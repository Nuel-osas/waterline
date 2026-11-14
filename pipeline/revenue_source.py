"""Where the revenue that funds NEAR's buyback comes from, one step back inside intents.near.

  python3 -m pipeline.revenue_source            # the stored result: the share paid out of the private chain's treasury
  python3 -m pipeline.revenue_source --pull     # trace every payment of the latest 30 days again (no key; over an hour)

It covers the 30 days to the pinned reading, the window the rating's coverage uses. The index refuses about
half of its calls at one a second, so tracing a second window would take hours more; it is not traced.

Every payment of NEAR or wNEAR from intents.near into the three revenue wallets is a withdrawal signed by an account
on intents.near's own ledger: a native_withdraw or ft_withdraw intent. For each payment this reads the transaction
from FastNEAR's transactions index and finds the intent that paid it, matched by wallet and amount, and so the
account that signed it. It then reads that account's ledger transfers in the ten minutes before the payment from
FastNEAR's transfers index (six hours if the ten minutes show nothing) to see where its wNEAR came from: the private
chain's treasury, or any other account. A payment counts as paid out of the treasury in the proportion of the payer's
wNEAR that came from the treasury in that time. A payment whose intent cannot be found, or whose payer received no
wNEAR in that time, is untraced and counts as neither.

`make check` recomputes every share from data/context/revenue_source.json and checks that its payments add up to the
transfers from intents.near that data/context/revenue.json counts; `make verify` re-reads a sample of payments, and
the transfer into each payer, from a NEAR archival node.
"""
import argparse
import base64
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from . import rpc
from .pull import DATA, load, save
from .revenue import COUNTED, WALLETS, fetch

OUT = os.path.join(DATA, "context", "revenue_source.json")
RAW = os.path.join(DATA, "..", ".flows", "revenue_source")   # the index's pages for each wallet and day, not committed
TXS = "https://tx.main.fastnear.com/v0/transactions"
INDEX = "https://transfers.main.fastnear.com/v0/transfers"
WNEAR = "nep245:intents.near:nep141:wrap.near"           # wNEAR as a balance on intents.near's own ledger
LOOKBACK_MS = (10 * 60 * 1000, 6 * 3600 * 1000)          # ten minutes before the payment; six hours if those show nothing
WITHDRAW = {"native:near": ("native_withdraw", None), "nep141:wrap.near": ("ft_withdraw", "wrap.near")}


INDEX_GAP = 5.0      # seconds between calls to the transfers index: at one a second it refuses half, at three a third, at five none
_last_call = [0.0]


def _post(url, body, tries=10):
    if url == INDEX:                                        # pace the transfers index; the transactions index is not limited this way
        wait = _last_call[0] + INDEX_GAP - time.time()
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "waterline/1"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                return json.load(res)
        except urllib.error.HTTPError as e:                  # 429: the index is rate-limiting; wait it out
            time.sleep(min(90, 10 + 10 * attempt) if e.code == 429 else min(30, 2 + 3 * attempt))
        except (OSError, ValueError):
            time.sleep(min(30, 2 + 3 * attempt))
    raise SystemExit(f"no answer from {url}")


def payments(utc_days):
    """Every NEAR or wNEAR transfer from intents.near into the three wallets on the given UTC days, from the index."""
    out, seen = [], set()
    for wallet in WALLETS:
        for day in utc_days:
            path = os.path.join(RAW, wallet, day + ".json")
            rows = load(path, None)
            if rows is None:
                rows = fetch(wallet, day, pause=2.0)
                save(path, rows)
                time.sleep(1.0)
            for r in rows:
                key = (r["receipt_id"], r.get("transfer_index"), wallet)
                if r["other_account_id"] != rpc.LEDGER or r["asset_id"] not in COUNTED or int(r["amount"]) <= 0 or key in seen:
                    continue
                seen.add(key)
                out.append({"wallet": wallet, "tx": r["transaction_id"], "height": int(r["block_height"]),
                            "ts_ms": int(r["block_timestamp"]) // 10**6, "asset": r["asset_id"], "amount": r["amount"]})
    return sorted(out, key=lambda p: (p["height"], p["tx"], p["wallet"]))


def withdrawals(tx):
    """[(signer, intent, receiver, amount)] for every withdrawal intent in an execute_intents transaction."""
    out = []
    for action in tx["actions"]:
        call = action.get("FunctionCall") if isinstance(action, dict) else None
        if not call or call["method_name"] != "execute_intents":
            continue
        for signed in json.loads(base64.b64decode(call["args"])).get("signed", []):
            msg = signed.get("payload")
            if isinstance(msg, dict) and ("message" in msg or "text" in msg):   # NEP-413 and TON Connect wrap the intent
                msg = msg.get("message") or msg.get("text")
            for _ in range(2):                                    # other standards carry it as JSON text, sometimes twice
                if isinstance(msg, str):
                    try:
                        msg = json.loads(msg)
                    except ValueError:
                        msg = None
            if not isinstance(msg, dict):
                continue
            for it in msg.get("intents", []):
                if it.get("intent") in ("native_withdraw", "ft_withdraw"):
                    out.append((msg.get("signer_id"), it["intent"], it.get("receiver_id"), str(it.get("amount")), it.get("token")))
    return out


def match_payers(pays, txs):
    """Set each payment's payer: the signer of the withdrawal intent with its wallet and amount, used once each."""
    pool = {}
    for p in pays:
        if p["tx"] not in pool and p["tx"] in txs:
            pool[p["tx"]] = withdrawals(txs[p["tx"]])
    for p in pays:
        want_intent, want_token = WITHDRAW[p["asset"]]
        cands = pool.get(p["tx"], [])
        hit = next((c for c in cands if c[1] == want_intent and c[2] == p["wallet"] and c[3] == p["amount"]
                    and (want_token is None or c[4] == want_token)), None)
        if hit:
            cands.remove(hit)
            p["payer"], p["intent"] = hit[0], hit[1]
        else:
            p["payer"], p["intent"] = None, None
    return pays


def read_txs(hashes):
    """Transactions by hash from the index, kept in a local cache so an interrupted trace does not read them twice."""
    cache = os.path.join(RAW, "transactions.json")
    got = load(cache, None) or {}
    todo = sorted(set(hashes) - set(got))
    for k, i in enumerate(range(0, len(todo), 20), 1):
        for t in _post(TXS, {"tx_hashes": todo[i:i + 20]}).get("transactions", []):
            got[t["transaction"]["hash"]] = t["transaction"]
        if k % 10 == 0:
            save(cache, got)
        time.sleep(0.4)
    save(cache, got)
    return got


def inflows(p):
    """The payer's wNEAR arriving on the ledger before the payment, ten minutes back, or six hours if none."""
    for back in LOOKBACK_MS:
        got = _post(INDEX, {"account_id": p["payer"], "from_timestamp_ms": p["ts_ms"] - back, "to_timestamp_ms": p["ts_ms"] + 1000, "limit": 100})
        rows = [{"tx": r["transaction_id"], "height": int(r["block_height"]), "from": r["other_account_id"], "amount": r["amount"]}
                for r in got.get("transfers", [])
                if r["asset_id"] == WNEAR and int(r["amount"]) > 0 and int(r["block_height"]) <= p["height"]]
        if rows:
            return back, rows
    return LOOKBACK_MS[-1], []


def allocate(pays, treasury=rpc.TREASURY):
    """Each payer's wNEAR inflows fund its payments in time order, oldest first, each inflow used once and never beyond
    its amount. Returns {id(payment): (through the treasury, from other accounts, not explained)} in yoctoNEAR. The
    part of a payment that the inflows seen before it do not cover was paid from a balance the payer already held,
    whose source the windows read here do not show; it is counted as neither."""
    out, by_payer = {}, {}
    for p in pays:
        if p.get("payer") and "in" in p:
            by_payer.setdefault(p["payer"], []).append(p)
        else:
            out[id(p)] = (0, 0, int(p["amount"]))
    for ps in by_payer.values():
        seen, pool = set(), []
        for p in ps:
            for r in p["in"]:
                key = (r["tx"], r["height"], r["from"], r["amount"])
                if key not in seen:
                    seen.add(key)
                    pool.append([r["height"], r["from"] == treasury, int(r["amount"])])
        pool.sort(key=lambda x: x[0])
        for p in sorted(ps, key=lambda p: (p["height"], p["tx"])):
            need, t, o = int(p["amount"]), 0, 0
            for item in pool:
                if need == 0:
                    break
                if item[0] > p["height"] or item[2] == 0:
                    continue
                use = min(need, item[2])
                item[2] -= use
                need -= use
                if item[1]:
                    t += use
                else:
                    o += use
            out[id(p)] = (t, o, need)
    return out


def in_window(rec, blocks, first, last):
    """Payments that fall in the readings window first..last: after the block of the reading before `first`, up to the
    block of `last`, the same days pipeline/revenue.py counts."""
    before = (dt.date.fromisoformat(first) - dt.timedelta(days=1)).isoformat()
    if before not in blocks or last not in blocks:
        return None
    lo, hi = blocks[before]["height"], blocks[last]["height"]
    return [p for p in rec["payments"] if lo < p["height"] <= hi]


SWITCH_MS = int(dt.datetime(2026, 10, 27, tzinfo=dt.timezone.utc).timestamp() * 1000)   # 1Click settles privately from this day


def summarise(rec, blocks, first, last):
    """Totals for the readings window first..last: paid, and how much arrived through the treasury, came from other
    accounts, or is not explained; also by wallet, and before and from 27 October 2026. None without the readings."""
    pays = in_window(rec, blocks, first, last)
    if pays is None:
        return None
    parts = allocate(pays, rec.get("treasury", rpc.TREASURY))
    def tally(ps):   # noqa: E306
        t = sum(parts[id(p)][0] for p in ps)
        o = sum(parts[id(p)][1] for p in ps)
        u = sum(parts[id(p)][2] for p in ps)
        return {"payments": len(ps), "paid": sum(int(p["amount"]) for p in ps), "treasury": t, "other": o, "untraced": u}
    out = tally(pays)
    out.update({"first": first, "last": last, "payers": len({p["payer"] for p in pays if p.get("payer")}),
                "untraced_payments": sum(1 for p in pays if parts[id(p)][2] > 0),
                "by_wallet": {w: tally([p for p in pays if p["wallet"] == w]) for w in sorted({p["wallet"] for p in pays})},
                "before_switch": tally([p for p in pays if p["ts_ms"] < SWITCH_MS]),
                "from_switch": tally([p for p in pays if p["ts_ms"] >= SWITCH_MS])})
    return out


def counted_by_revenue(rv, first, last):
    """NEAR and wNEAR the revenue wallets received from intents.near over first..last, as data/context/revenue.json counts it."""
    d, end, total = dt.date.fromisoformat(first), dt.date.fromisoformat(last), 0
    while d <= end:
        day = rv["transfers"].get(d.isoformat())
        if day is None:
            return None
        total += sum(int(w["from"].get(rpc.LEDGER, "0")) for w in day.values())
        d += dt.timedelta(days=1)
    return total


def logged_transfer(status, sender, receiver, token, amount):
    """Whether a transaction's receipts log a NEP-245 transfer of `amount` of `token` from `sender` to `receiver`."""
    for outcome in status.get("receipts_outcome", []):
        for line in outcome["outcome"]["logs"]:
            if not line.startswith("EVENT_JSON:"):
                continue
            ev = json.loads(line[len("EVENT_JSON:"):])
            if ev.get("standard") != "nep245" or ev.get("event") != "mt_transfer":
                continue
            for d in ev.get("data", []):
                if d.get("old_owner_id") == sender and d.get("new_owner_id") == receiver and \
                        any(t == token and str(a) == amount for t, a in zip(d.get("token_ids", []), d.get("amounts", []))):
                    return True
    return False


def sample(rec, k=3, seed=20261114):
    """A seeded sample of payments that arrived wholly through the treasury, for re-reading from the chain."""
    import random
    parts = allocate(rec["payments"], rec["treasury"])
    pool = [p for p in rec["payments"] if p.get("in") and parts[id(p)][0] == int(p["amount"])]
    return random.Random(seed).sample(pool, min(k, len(pool)))


def pull(first_utc, last_utc, workers=1):
    """Trace every payment on the UTC days first..last. Saves as it goes and resumes a trace of the same days; the
    record is marked complete only when every payment has been looked at."""
    old = load(OUT, None)
    if old and old.get("utc_days") == [first_utc, last_utc] and old.get("payments"):
        rec = old
        print(f"resuming the trace of {first_utc} to {last_utc}: {len(rec['payments'])} payments", flush=True)
    else:
        days, d = [], dt.date.fromisoformat(first_utc)
        while d <= dt.date.fromisoformat(last_utc):
            days.append(d.isoformat())
            d += dt.timedelta(days=1)
        print(f"payments into the three wallets from intents.near, {first_utc} to {last_utc} (UTC days)...", flush=True)
        pays = payments(days)
        print(f"  {len(pays)} payments; reading their transactions...", flush=True)
        match_payers(pays, read_txs([p["tx"] for p in pays]))
        rec = {"source": "FastNEAR's transactions index (tx.main.fastnear.com) and transfers index (transfers.main.fastnear.com); no key",
               "treasury": rpc.TREASURY, "utc_days": [first_utc, last_utc], "complete": False, "payments": pays}
        save(OUT, rec)
    todo = sorted((p for p in rec["payments"] if p.get("payer") and "in" not in p), key=lambda p: -p["height"])   # latest first
    print(f"  payer found for {sum(1 for p in rec['payments'] if p.get('payer'))}; {len(todo)} still to read...", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for k, (p, (back, rows)) in enumerate(zip(todo, pool.map(inflows, todo)), 1):
            p["lookback_ms"], p["in"] = back, rows
            if k % 50 == 0:
                save(OUT, rec)
                print(f"  {k} of {len(todo)}", flush=True)
    rec["complete"] = all("in" in p for p in rec["payments"] if p.get("payer"))
    save(OUT, rec)
    return rec


def main():
    ap = argparse.ArgumentParser(description="Where the revenue that funds NEAR's buyback comes from, one step back.")
    ap.add_argument("--pull", action="store_true", help="trace every payment of the latest 30-day window again (network)")
    args = ap.parse_args()
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    pin = load(os.path.join(DATA, "pin.json"), {})["pin_day"]
    shift = lambda n: (dt.date.fromisoformat(pin) + dt.timedelta(days=n)).isoformat()   # noqa: E731
    if args.pull:
        pull(shift(-30), shift(-1))
    rec = load(OUT, None)
    if not rec:
        print("no stored trace: run with --pull")
        return 1
    rv = load(os.path.join(DATA, "context", "revenue.json"), None)
    for first, last in ((shift(-29), pin),):
        s = summarise(rec, blocks, first, last)
        if s is None:
            print(f"{first} to {last}: not covered by the stored trace")
            continue
        theirs = counted_by_revenue(rv, first, last) if rv else None
        n = lambda x: f"{float(x) / 1e24:,.0f} NEAR"   # noqa: E731
        print(f"{first} to {last}: {s['payments']} payments by {s['payers']} accounts, {n(s['paid'])}"
              + ("" if theirs is None else f" ({'equal to' if theirs == s['paid'] else 'NOT equal to'} the {n(theirs)} revenue.json counts from intents.near)"))
        share = lambda t: f"{t['treasury'] / t['paid'] * 100:.1f}%" if t["paid"] else "none"   # noqa: E731
        print(f"  arrived through the private chain's treasury: {n(s['treasury'])} ({share(s)}); from other accounts: {n(s['other'])}; "
              f"not explained by the payer's inflows (paid from a balance it already held): {n(s['untraced'])}, in {s['untraced_payments']} payments")
        print(f"  before 27 October: {share(s['before_switch'])} of {n(s['before_switch']['paid'])}; from 27 October: "
              f"{share(s['from_switch'])} of {n(s['from_switch']['paid'])}")
        for w, t in s["by_wallet"].items():
            print(f"  {w}: {share(t)} of {n(t['paid'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
