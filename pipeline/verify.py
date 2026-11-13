"""Check the published numbers against the chain and against the raw data. It never writes a file.

  python3 -m pipeline.verify            # re-read a sample of days from a public node, then everything below
  python3 -m pipeline.verify --all      # re-read every day (slow: public nodes rate-limit)
  python3 -m pipeline.verify --offline  # no network

What the offline part checks:
  1. Rebuilding the series, the claims and the forward-test scores from data/ in memory gives exactly the
     committed files, including the findings table in README.md and the numbers written into site/index.html.
  2. Every dollar amount, percentage, multiple and NEAR amount in the prose of README.md, THESIS.md and
     PREREG.md is either a computed claim or a constant declared, with its reason, in data/constants.json.
     A number typed by hand that the data does not produce fails here.
  3. PREREG.md and pipeline/score.py still match the hashes recorded when the forward tests were written.

Exit code 0 means every check passed. A failure prints what differs and exits 1.
"""
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys

from . import audit, rpc
from .build import build, site_js, token_meta, usd
from .claims import write_claims
from .pull import DATA, FIRST_BLOCK_FROM, ROOT, header_at, load, read_float, read_held
from .score import score
from .score_audit import score as score_audit

PROSE = ("README.md", "THESIS.md", "PREREG.md", "PREREG-AUDIT.md")
NUMBER = re.compile(r"[+-]?\$\d[\d,]*(?:\.\d+)?[MBK]?|[+-]?\d[\d,]*(?:\.\d+)?%|\b\d[\d,]*(?:\.\d+)?x\b|\b\d[\d,]*(?:\.\d+)?M NEAR\b|\b\d{1,3}(?:,\d{3})+ NEAR\b"
                    r"|(?<![-\d,.])\b\d[\d,]* (?:checks|tokens|readings)\b|(?<![-\d,.:])\b\d+ hours(?: \d+ minutes)?\b")


def read(path):
    with open(path) as f:
        return f.read()


def sample_days(blocks, k):
    days = sorted(d for d in blocks if os.path.exists(os.path.join(DATA, "float", d + ".json")))
    pin = load(os.path.join(DATA, "pin.json"), {}).get("pin_day")
    must = {days[0], days[-1]} | {d for d in ("2026-07-13", "2026-10-02", "2026-10-27", pin) if d in days}
    # the sample is fixed by the data itself, so two people running this check the same days
    seed = int(hashlib.sha256(json.dumps(blocks, sort_keys=True).encode()).hexdigest(), 16)
    rest = [d for d in days if d not in must]
    random.Random(seed).shuffle(rest)
    return sorted(must | set(rest[:max(0, k - len(must))]))


def totals_to_probe(day, held, tracked, meta, pin):
    """Which stored totals to re-read for a day: all tracked ones on the pinned day (they make the headline),
    otherwise the three largest by value plus two picked by a seed fixed by the day."""
    readable = [t for t in held if held[t] is not None and t.split(":")[0] in ("nep141", "nep245")]
    if day == pin:
        return [t for t in tracked if t in readable]
    ranked = sorted(readable, key=lambda t: -(usd(int(held[t]), meta.get(t)) or 0))
    extra = ranked[3:]
    random.Random(day).shuffle(extra)
    return ranked[:3] + extra[:2]


def check_chain(days, blocks):
    bad = 0
    meta, _ = token_meta()
    tracked = load(os.path.join(DATA, "tracked.json"), [])
    pin = load(os.path.join(DATA, "pin.json"), {}).get("pin_day")
    for day in days:
        bad_day = 0
        height = blocks[day]["height"]
        head = rpc.header(height)
        if head["timestamp"] != blocks[day]["timestamp"]:
            print(f"FAIL {day}: block {height} is stamped {head['timestamp']}, file says {blocks[day]['timestamp']}")
            bad_day += 1
        if day >= FIRST_BLOCK_FROM:
            # from this day on the block must be the first one stamped at or after 00:00:00 UTC
            y, m, d = map(int, day.split("-"))
            midnight = int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp()) * 10**9
            below, h = None, height - 1
            while below is None and h > height - 40:
                below, h = header_at(h), h - 1
            if head["timestamp"] < midnight or below is None or below["timestamp"] >= midnight:
                print(f"FAIL {day}: block {height} is not the first block stamped at or after 00:00:00 UTC")
                bad_day += 1
        stored = load(os.path.join(DATA, "float", day + ".json"), None)["balances"]
        live = read_float(height)
        if live != stored:
            bad_day += 1
            keys = sorted(set(live or {}) | set(stored or {}))
            diff = [(k, (stored or {}).get(k), (live or {}).get(k)) for k in keys if (stored or {}).get(k) != (live or {}).get(k)]
            print(f"FAIL {day} @ {height}: {len(diff)} balances differ, first: {diff[:2]}")
        held = load(os.path.join(DATA, "held", day + ".json"), {"held": {}})["held"]
        probe = totals_to_probe(day, held, tracked, meta, pin)
        for t in probe:
            got = read_held(height, t)
            if got != held[t]:
                bad_day += 1
                print(f"FAIL {day} @ {height}: intents.near holds {got} of {t}, file says {held[t]}")
        cred = load(os.path.join(DATA, "credited", day + ".json"), None)
        n_cred = 0
        if cred and cred.get("height") == height:
            ids = sorted(cred["credited"])
            live_cred = audit.read_credited(height, ids)
            n_cred = len(ids)
            wrong = [t for t in ids if live_cred.get(t) != cred["credited"][t]]
            if wrong:
                bad_day += 1
                print(f"FAIL {day} @ {height}: intents.near credits {live_cred.get(wrong[0])} of {wrong[0]}, file says {cred['credited'][wrong[0]]}"
                      + (f" (and {len(wrong) - 1} more)" if len(wrong) > 1 else ""))
        if not bad_day:
            print(f"ok   {day}  block {height}  {len(stored)} balances, {len(probe)} totals and {n_cred} credited totals match the chain")
        bad += bad_day

    supply = load(os.path.join(DATA, "context", "supply.json"), {"days": {}})["days"]
    for day, s in sorted(supply.items()):
        got = rpc.header(s["height"])["total_supply"]
        if got != s["total_supply"]:
            print(f"FAIL supply on {day}: header says {got}, file says {s['total_supply']}")
            bad += 1
    if supply:
        print(f"ok   total supply in {len(supply)} block headers matches data/context/supply.json")
    cus = load(os.path.join(DATA, "context", "custody.json"), None)
    if cus:
        keys = rpc.view(cus["height"], rpc.LEDGER, "public_keys_of", {"account_id": rpc.TREASURY})
        if keys != cus["keys_registered_in_intents_near"]:
            print(f"FAIL custody: intents.near lists {keys} for the treasury, file says {cus['keys_registered_in_intents_near']}")
            bad += 1
        else:
            print(f"ok   {len(keys)} key registered for the treasury in intents.near, as in data/context/custody.json")
        if cus.get("account_access_keys") is not None:
            live = rpc.call("query", {"request_type": "view_access_key_list", "block_id": cus["height"], "account_id": rpc.TREASURY})["keys"]
            got = [(k["public_key"], k["access_key"]["nonce"]) for k in live]
            if got != [(k["public_key"], k["nonce"]) for k in cus["account_access_keys"]]:
                print("FAIL custody: the treasury account's access keys on NEAR differ from data/context/custody.json")
                bad += 1
            else:
                print("ok   the treasury account's access keys and their nonces match data/context/custody.json")
    bad += check_trace_chain()
    bad += check_exploit_chain()
    return bad


def exploit_marks(ex):
    """The steps of the recorded exploit that carry the claims: where the hole opens, its peak, where it closes."""
    hole = lambda st: int(st["credited"]) - int(st["held"])   # noqa: E731
    steps = ex["steps"]
    first = next(st for st in steps if hole(st) > 0)
    peak = max(steps, key=hole)
    whole = next((st for st in steps if st["height"] > peak["height"] and hole(st) <= 0), None)
    return [st for st in (first, peak, whole) if st]


def check_exploit_chain():
    """Re-read from the chain the blocks on which the exploit's claims rest: the state at the block and one before."""
    ex = load(audit.EXPLOIT, None)
    if not ex:
        return 0
    bad = 0
    marks = exploit_marks(ex)
    for st in marks:
        seen = {}
        before, after = audit.hole_at(ex["token"], st["height"] - 1, seen), audit.hole_at(ex["token"], st["height"], seen)
        want_before, want_after = (int(st["credited_before"]), int(st["held_before"])), (int(st["credited"]), int(st["held"]))
        head = rpc.header(st["height"])
        if before != want_before or after != want_after or head["timestamp"] // 10**9 != st["timestamp"] // 10**9:
            print(f"FAIL exploit: block {st['height']} does not show the credited and held totals, or the time, in data/context/exploit.json")
            bad += 1
    if not bad:
        print(f"ok   exploit replay: credited and held at {len(marks)} blocks, each with the block before it, match the chain "
              f"(the hole opens at block {marks[0]['height']})")
    return bad


def check_trace_chain():
    """Re-read from the chain every hop of a traced case that was read from the chain, and the balances around it."""
    from . import trace
    rec = load(trace.PATH, None)
    bad = 0
    for case in (rec or {}).get("cases", []):
        hops = [h for h in case["hops"] if h["seen"] == "chain"]
        for hop in hops:
            receipt = rpc.call("EXPERIMENTAL_receipt", {"receipt_id": hop["receipt_id"]})
            want = {"from": hop["from"], "to": hop["to"], "amount": int(case["amount"]), "how": hop["how"]}
            if want not in trace.legs(receipt, case["token"]):
                print(f"FAIL trace: receipt {hop['receipt_id']} does not carry {hop['how']} of {case['amount']} from {hop['from']} to {hop['to']}")
                bad += 1
            if hop.get("signed_by") and trace.signers(receipt).get(hop["from"]) != hop["signed_by"]:
                print(f"FAIL trace: receipt {hop['receipt_id']} was not signed for {hop['from']} by {hop['signed_by']}")
                bad += 1
        seen = {}
        for height, stored in case["treasury_balance"].items():
            if trace.balance(rpc.TREASURY, case["token"], int(height), seen) != int(stored):
                print(f"FAIL trace: treasury balance at block {height} differs from data/context/trace.json")
                bad += 1
        if not bad:
            print(f"ok   traced case: {len(hops)} receipts and {len(case['treasury_balance'])} balances match the chain "
                  f"({int(case['amount']) // 10**24:,} NEAR out of the treasury and back)")
    return bad


def check_flows():
    """The indexed transfer list is used only where it adds up to the balances read from the chain. Recheck that."""
    from . import flows, trace
    bad = 0
    rec = load(flows.PATH, None)
    if rec:
        days = sorted(rec["days"])
        cal = sorted(set(days) | {(dt.date.fromisoformat(d) - dt.timedelta(days=1)).isoformat() for d in days})
        chain = flows.chain_balances(cal)
        good = 0
        for day in days:
            d = rec["days"][day]
            before = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
            parts_in = sum(int(v[0]) for v in d["by_account"].values()) + int(d["rest"][0])
            parts_out = sum(int(v[1]) for v in d["by_account"].values()) + int(d["rest"][1])
            change = None if chain[day] is None or chain[before] is None else chain[day] - chain[before]
            if parts_in != int(d["in"]) or parts_out != int(d["out"]) or change is None or int(d["chain_change"]) != change:
                print(f"FAIL flows {day}: the stored totals do not match their parts or the chain balances in data/float/")
                bad += 1
            elif d["adds_up"] != (parts_in - parts_out == change):
                print(f"FAIL flows {day}: marked {'as adding up' if d['adds_up'] else 'as not adding up'}, and the opposite is true")
                bad += 1
            else:
                good += d["adds_up"]
        if not bad:
            print(f"ok   data/context/flows.json: on {good} of {len(days)} days the listed transfers add up exactly to the change in the chain balance")
    return bad


def check_exploit_stored():
    """The exploit's steps as stored: in order, inside the window, and each one starting where the last one ended
    unless blocks in between were not read."""
    ex = load(audit.EXPLOIT, None)
    if not ex:
        return 0
    steps = ex["steps"]
    ordered = all(a["height"] < b["height"] and a["timestamp"] <= b["timestamp"] for a, b in zip(steps, steps[1:]))
    inside = all(ex["from_height"] < st["height"] <= ex["to_height"] for st in steps)
    joined = all((b["credited_before"], b["held_before"]) == (a["credited"], a["held"])
                 for a, b in zip(steps, steps[1:]) if b["height"] == a["height"] + 1)
    moved = all((st["credited_before"], st["held_before"]) != (st["credited"], st["held"]) for st in steps)
    if not (ordered and inside and joined and moved):
        print("FAIL data/context/exploit.json: the steps are out of order, outside the window, or do not join up")
        return 1
    print(f"ok   data/context/exploit.json: {len(steps)} steps in order, inside the window, each a real change")
    return 0


def check_trace_stored():
    """The traced case as stored: the same amount leaves the treasury and comes back, signed by the registered key."""
    from . import trace
    bad = 0
    registered = (load(os.path.join(DATA, "context", "custody.json"), None) or {}).get("keys_registered_in_intents_near", [])
    for case in (load(trace.PATH, None) or {}).get("cases", []):
        for hop in case["hops"]:
            if hop.get("signed_by") and hop["from"] == rpc.TREASURY and hop["signed_by"] not in registered:
                print("FAIL trace: the key recorded as signing the treasury's payout is not the key in data/context/custody.json")
                bad += 1
        b = {int(h): int(v) for h, v in case["treasury_balance"].items()}
        hs = sorted(b)
        steps = [b[hs[1]] - b[hs[0]], b[hs[3]] - b[hs[2]]]
        if steps != [-int(case["amount"]), int(case["amount"])]:
            print("FAIL trace: the stored balances do not show the amount leaving and coming back")
            bad += 1
        else:
            print("ok   data/context/trace.json: the stored balances show the same amount leaving the treasury and coming back")
    return bad


def same(name, want, path, as_json=False):
    """Compare what the data produces with the committed file. Returns the number of problems (0 or 1)."""
    if not os.path.exists(path):
        print(f"FAIL {name}: {os.path.relpath(path, ROOT)} is missing")
        return 1
    have = load(path, None) if as_json else read(path)
    if as_json:
        want = json.loads(json.dumps(want))
    if have != want:
        print(f"FAIL {name}: {os.path.relpath(path, ROOT)} is not what the data produces. Run `make build` and look at the diff.")
        return 1
    print(f"ok   {os.path.relpath(path, ROOT)} is exactly what the data produces")
    return 0


def prose_only(text):
    """The hand-written part of a markdown file: no code blocks, no inline code, no generated findings table, no links."""
    text = re.sub(r"<!-- claims:start -->.*?<!-- claims:end -->", "", text, flags=re.S)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"\]\([^)]*\)|<https?://[^>]*>", "]", text)


def allowed_numbers(claims):
    ok = {}
    for c in claims["claims"]:
        for m in NUMBER.findall(c["shown"]) + NUMBER.findall(c["what"]):
            ok.setdefault(m, "claim " + c["id"])
    for entry in load(os.path.join(DATA, "constants.json"), {"constants": []})["constants"]:
        ok.setdefault(entry["value"], "declared constant")
    return ok


def check_prose(claims):
    ok = allowed_numbers(claims)
    bad = 0
    for name in PROSE:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        misses = []
        for n, line in enumerate(prose_only(read(path)).split("\n"), 1):
            misses += [(n, m) for m in NUMBER.findall(line) if m not in ok]
        if misses:
            bad += len(misses)
            for n, m in misses[:12]:
                print(f"FAIL {name}: the number {m} is neither a computed claim nor a declared constant")
        else:
            found = sum(len(NUMBER.findall(l)) for l in prose_only(read(path)).split("\n"))
            print(f"ok   {name}: all {found} numbers in the prose are computed claims or declared constants")
    # every claim that must be quoted is quoted somewhere
    text = "".join(read(os.path.join(ROOT, n)) for n in PROSE if os.path.exists(os.path.join(ROOT, n)))
    for c in claims["claims"]:
        if c.get("must_appear", True) and c["shown"] not in text:
            print(f"FAIL claim {c['id']}: '{c['shown']}' appears in none of {', '.join(PROSE)}")
            bad += 1
    return bad


def check_hashes():
    bad = 0
    lines = []
    for name in ("prereg.sha256", "prereg_audit.sha256"):
        hash_file = os.path.join(DATA, "derived", name)
        if os.path.exists(hash_file):
            lines += read(hash_file).split("\n")
    for line in lines:
        if not line.strip():
            continue
        want, name = line.split(None, 1)
        got = hashlib.sha256(open(os.path.join(ROOT, name.strip()), "rb").read()).hexdigest()
        if got != want:
            print(f"FAIL {name.strip()} no longer matches the hash recorded when the forward tests were written")
            bad += 1
        else:
            print(f"ok   {name.strip()} matches its recorded hash {want[:16]}...")
    return bad


def check_derived():
    write_claims(write=False)
    score(write=False)
    b, c, f = build.last, write_claims.last, score.last
    bad = 0
    bad += same("series", b["series"], os.path.join(DATA, "derived", "series.json"), as_json=True)
    bad += same("anomalies", b["anomalies"], os.path.join(DATA, "derived", "anomalies.json"), as_json=True)
    bad += same("claims", c["claims"], os.path.join(DATA, "derived", "claims.json"), as_json=True)
    bad += same("forward tests", f["forward"], os.path.join(DATA, "derived", "forward.json"), as_json=True)
    g = score_audit(write=False)
    bad += same("audit forward tests", g, os.path.join(DATA, "derived", "forward_audit.json"), as_json=True)
    bad += same("dashboard audit tests", score_audit.last["forward_audit_js"], os.path.join(ROOT, "site", "forward_audit.js"))
    bad += same("dashboard data", site_js("WATERLINE", b["series"]), os.path.join(ROOT, "site", "data.js"))
    bad += same("dashboard claims", c["claims_js"], os.path.join(ROOT, "site", "claims.js"))
    bad += same("dashboard forward tests", f["forward_js"], os.path.join(ROOT, "site", "forward.js"))
    bad += same("findings table", c["readme"], os.path.join(ROOT, "README.md"))
    bad += same("numbers in the page", c["index"], os.path.join(ROOT, "site", "index.html"))
    bad += check_flows()
    bad += check_exploit_stored()
    bad += check_trace_stored()
    bad += check_prose(c["claims"])
    bad += check_hashes()
    for t in f["forward"]["tests"] + g["tests"]:
        print(f"     {t['status']:8} {t['id']} due {t['due']}" + (f": {t['value']}" if t["value"] else ""))
    return bad


def main(argv):
    bad = 0
    if "--offline" not in argv:
        blocks = load(os.path.join(DATA, "blocks.json"), {})
        days = sorted(blocks) if "--all" in argv else sample_days(blocks, 8)
        print(f"re-reading {len(days)} days from {rpc.ENDPOINTS[0]}")
        bad += check_chain(days, blocks)
    bad += check_derived()
    print("\nRESULT:", "PASS" if not bad else f"FAIL ({bad} problems)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
