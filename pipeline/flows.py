"""Who moved NEAR in and out of the private chain's treasury: every transfer, taken from a public index and
accepted only where it adds up to the balances this repository read from the chain.

  python3 -m pipeline.flows                               # the summary of data/context/flows.json
  python3 -m pipeline.flows --pull 2026-09-11 2026-10-03  # refetch those days from the index and rebuild the file (slow)

Source: FastNEAR's transfers index, no key. It is an indexer's list, not a chain read, so it is tested before it is
used: for each day, the transfers between the two daily readings must add up, to the last unit, to the change in the
balance read from the chain at those two blocks. A day that does not add up is marked and left out of every figure.

What it shows and what it does not. A transfer names the account on the other side inside intents.near. Many of
those are one-time deposit addresses, so an account is not a person, and the money's origin outside NEAR Intents is
a further step that this file does not take. `pipeline.trace` finds the largest moves from the chain alone.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.request

from . import rpc
from .pull import DATA, load, save

INDEX = "https://transfers.main.fastnear.com/v0/transfers"
TOKEN = "nep141:wrap.near"
ASSET = "nep245:intents.near:" + TOKEN
PATH = os.path.join(DATA, "context", "flows.json")
RAW = os.path.join(DATA, "..", ".flows")        # raw pages, not committed: about 2 MB a day
FLOOR = 1000 * 10**24                           # accounts that moved less than 1,000 NEAR in a day are added up as "rest"


def fetch_day(day, pause=1.5):
    """Every wNEAR transfer of the treasury stamped on one UTC day, as the index lists them."""
    d = dt.date.fromisoformat(day)
    a = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
    rows, token = [], None
    while True:
        body = {"account_id": rpc.TREASURY, "asset_id": ASSET, "from_timestamp_ms": a, "to_timestamp_ms": a + 86_400_000, "limit": 100}
        if token:
            body["resume_token"] = token
        req = urllib.request.Request(INDEX, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": "waterline/1"})
        for attempt in range(12):
            try:
                with urllib.request.urlopen(req, timeout=40) as res:
                    got = json.load(res)
                break
            except (OSError, ValueError):
                time.sleep(min(30, 3 + 3 * attempt))
        else:
            raise SystemExit(f"the index did not answer for {day}")
        rows += got["transfers"]
        token = got.get("resume_token")
        if not token or not got["transfers"]:
            return rows
        time.sleep(pause)


def summarise(transfers, blocks, balances, days):
    """One entry per day in `days`: the transfers between the reading before it and its own, by counterparty.

    `transfers` are index rows, `blocks` maps a day to its reading's height, `balances` maps a day to the balance
    read from the chain at that height. Amounts stay whole units, as text."""
    out = {}
    for day in days:
        before = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        if before not in blocks or day not in blocks or balances.get(before) is None or balances.get(day) is None:
            continue
        lo, hi = blocks[before], blocks[day]
        seen, by, biggest = set(), {}, {True: None, False: None}
        for t in transfers:
            key = (t["receipt_id"], t["log_index"], t["transfer_index"], t["other_account_id"], t["amount"])
            if not lo < int(t["block_height"]) <= hi or key in seen:
                continue
            seen.add(key)
            row = by.setdefault(t["other_account_id"] or "", [0, 0, 0])
            amount = int(t["amount"])
            row[0 if amount > 0 else 1] += abs(amount)
            row[2] += 1
            top = biggest[amount > 0]
            if top is None or abs(amount) > int(top["amount"]):
                biggest[amount > 0] = {"amount": str(abs(amount)), "account": t["other_account_id"] or "", "height": int(t["block_height"]),
                                       "receipt_id": t["receipt_id"]}
        total_in, total_out = sum(r[0] for r in by.values()), sum(r[1] for r in by.values())
        change = balances[day] - balances[before]
        named = {a: r for a, r in by.items() if r[0] + r[1] >= FLOOR}
        rest = [r for a, r in by.items() if a not in named]
        out[day] = {
            "from_height": lo, "to_height": hi, "transfers": len(seen), "accounts": len(by),
            "in": str(total_in), "out": str(total_out), "chain_change": str(change),
            "adds_up": total_in - total_out == change,
            "largest_in": biggest[True], "largest_out": biggest[False],
            "by_account": {a: [str(r[0]), str(r[1]), r[2]] for a, r in sorted(named.items(), key=lambda kv: (-(kv[1][0] + kv[1][1]), kv[0]))},
            "rest": [str(sum(r[0] for r in rest)), str(sum(r[1] for r in rest)), sum(r[2] for r in rest), len(rest)],
        }
    return out


def span(flows, first, last):
    """Totals over the days from `first` to `last` that add up: {in, out, accounts: {id: [in, out, n]}, rest, days, skipped}."""
    acc, rest, days, skipped = {}, [0, 0, 0], [], []
    for day in sorted(flows["days"]):
        if not first <= day <= last:
            continue
        d = flows["days"][day]
        if not d["adds_up"]:
            skipped.append(day)
            continue
        days.append(day)
        for a, (i, o, n) in d["by_account"].items():
            row = acc.setdefault(a, [0, 0, 0])
            row[0] += int(i)
            row[1] += int(o)
            row[2] += n
        rest[0] += int(d["rest"][0])
        rest[1] += int(d["rest"][1])
        rest[2] += d["rest"][2]
    return {"in": sum(r[0] for r in acc.values()) + rest[0], "out": sum(r[1] for r in acc.values()) + rest[1],
            "accounts": acc, "rest": rest, "days": days, "skipped": skipped}


def chain_balances(days):
    out = {}
    for day in days:
        got = load(os.path.join(DATA, "float", day + ".json"), None)
        bal = (got or {}).get("balances", got or {})
        out[day] = int(bal[TOKEN]) if bal and TOKEN in bal else None
    return out


def pull(first, last):
    os.makedirs(RAW, exist_ok=True)
    a, b = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    cal = [(a + dt.timedelta(days=k)).isoformat() for k in range(-1, (b - a).days + 1)]
    rows = []
    for day in cal:
        path = os.path.join(RAW, day + ".json")
        if not os.path.exists(path):
            got = fetch_day(day)
            with open(path, "w") as f:
                json.dump(got, f)
            print(f"{day}: {len(got)} transfers listed", flush=True)
        rows += load(path, [])
    blocks = {d: v["height"] for d, v in load(os.path.join(DATA, "blocks.json"), {}).items()}
    days = cal[1:]
    out = {"source": INDEX + " (FastNEAR transfers index, no key). An indexer's list: used only where it adds up to the chain.",
           "account": rpc.TREASURY, "token": TOKEN, "floor": str(FLOOR),
           "days": summarise(rows, blocks, chain_balances(cal), days)}
    save(PATH, out)
    return out


def main():
    ap = argparse.ArgumentParser(description="Who moved NEAR in and out of the private chain's treasury.")
    ap.add_argument("--pull", nargs=2, metavar=("FIRST", "LAST"), help="refetch these days from the index and rebuild the file")
    args = ap.parse_args()
    flows = pull(*args.pull) if args.pull else load(PATH, None)
    if not flows:
        raise SystemExit("data/context/flows.json does not exist yet: run with --pull FIRST LAST")
    unit = 10**24
    for day in sorted(flows["days"]):
        d = flows["days"][day]
        top = next(iter(d["by_account"].items()), None)
        print(f"{day}  in {int(d['in']) / unit:12,.0f}  out {int(d['out']) / unit:12,.0f}  {d['transfers']:6d} transfers  {d['accounts']:5d} accounts  "
              + ("adds up to the chain" if d["adds_up"] else "DOES NOT ADD UP, left out")
              + (f"  largest: {top[0][:24]} in {int(top[1][0]) / unit:,.0f}" if top else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
