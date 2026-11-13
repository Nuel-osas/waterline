"""Check the published numbers against the chain and against the raw data.

  python3 -m pipeline.verify            # re-read a sample of days from a public node, then recompute
  python3 -m pipeline.verify --all      # re-read every day (slow: public nodes rate-limit)
  python3 -m pipeline.verify --offline  # no network: recompute from data/ and compare

Exit code 0 means every check passed. Any mismatch prints the day, the token and both values, and exits 1.
"""
import hashlib
import json
import os
import random
import sys

from . import rpc
from .build import build
from .pull import DATA, ROOT, load, read_float, read_held


def sample_days(blocks, k):
    days = sorted(d for d in blocks if os.path.exists(os.path.join(DATA, "float", d + ".json")))
    must = {days[0], days[-1]} | {d for d in ("2026-07-13", "2026-10-27") if d in days}
    # the sample is fixed by the data itself, so two people running this check the same days
    seed = int(hashlib.sha256(json.dumps(blocks, sort_keys=True).encode()).hexdigest(), 16)
    rest = [d for d in days if d not in must]
    random.Random(seed).shuffle(rest)
    return sorted(must | set(rest[:max(0, k - len(must))]))


def check_chain(days, blocks):
    bad = 0
    for day in days:
        height = blocks[day]["height"]
        head = rpc.header(height)
        if head["timestamp"] != blocks[day]["timestamp"]:
            print(f"FAIL {day}: block {height} is stamped {head['timestamp']}, file says {blocks[day]['timestamp']}")
            bad += 1
        stored = load(os.path.join(DATA, "float", day + ".json"), None)["balances"]
        live = read_float(height)
        if live != stored:
            bad += 1
            keys = sorted(set(live or {}) | set(stored or {}))
            diff = [(k, (stored or {}).get(k), (live or {}).get(k)) for k in keys if (stored or {}).get(k) != (live or {}).get(k)]
            print(f"FAIL {day} @ {height}: {len(diff)} balances differ, first: {diff[:2]}")
        held = load(os.path.join(DATA, "held", day + ".json"), {"held": {}})["held"]
        probe = sorted(held)[:3]
        for t in probe:
            got = read_held(height, t)
            if got != held[t]:
                bad += 1
                print(f"FAIL {day} @ {height}: intents.near holds {got} of {t}, file says {held[t]}")
        if not bad:
            print(f"ok   {day}  block {height}  {len(stored)} balances and {len(probe)} totals match the chain")
    return bad


def check_derived():
    before = load(os.path.join(DATA, "derived", "series.json"), None)
    claims_before = load(os.path.join(DATA, "derived", "claims.json"), None)
    bad = 0
    build()
    try:
        from .claims import write_claims
        write_claims()
    except ImportError:
        pass
    import hashlib
    want = open(os.path.join(DATA, "derived", "prereg.sha256")).read().strip() if os.path.exists(os.path.join(DATA, "derived", "prereg.sha256")) else None
    if want:
        got = hashlib.sha256(open(os.path.join(ROOT, "PREREG.md"), "rb").read()).hexdigest()
        if got != want:
            print("FAIL PREREG.md no longer matches the hash recorded when it was written")
            bad += 1
        else:
            print(f"ok   PREREG.md matches its recorded hash {want[:16]}...")
    after = load(os.path.join(DATA, "derived", "series.json"), None)
    if before != after:
        print("FAIL derived series changed when rebuilt from the raw data")
        bad += 1
    else:
        print(f"ok   series rebuilt from raw data is identical ({len(after['days'])} days)")
    claims_after = load(os.path.join(DATA, "derived", "claims.json"), None)
    if claims_before != claims_after:
        print("FAIL claims changed when rebuilt from the raw data")
        bad += 1
    elif claims_after:
        readme = open(os.path.join(ROOT, "README.md")).read() if os.path.exists(os.path.join(ROOT, "README.md")) else ""
        thesis = open(os.path.join(ROOT, "THESIS.md")).read() if os.path.exists(os.path.join(ROOT, "THESIS.md")) else ""
        for c in claims_after["claims"]:
            where = [n for n, text in (("README.md", readme), ("THESIS.md", thesis)) if c["shown"] in text]
            if c.get("must_appear", True) and not where:
                print(f"FAIL claim {c['id']}: the text '{c['shown']}' is in neither README.md nor THESIS.md")
                bad += 1
            else:
                print(f"ok   {c['id']}: {c['shown']}  ({c['what']})")
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
