"""Measure the revenue that reaches NEAR's wallets, from the chain, where the thesis used to quote it.

  python3 -m pipeline.revenue                       # the summary of data/context/revenue.json (no network)
  python3 -m pipeline.revenue --balances            # read the three wallets' NEAR balance at every stored day's block
  python3 -m pipeline.revenue --transfers FIRST LAST  # list their transfers on those days from a public index

DefiLlama counts as NEAR Intents' revenue the NEAR received by three public accounts. Their balances are a view
call at any past block, so the money can be read directly: `view_account` at the day's block for each wallet.
The transfers between two readings come from FastNEAR's transfers index and are used the way pipeline/flows.py
uses it: only as far as they add up to the balances read from the chain.

A balance that could not be read is stored as null and the days around it are left out. It is never zero.
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

WALLETS = ["buybacks.multisignature.near", "fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"]
PATH = os.path.join(DATA, "context", "revenue.json")
RAW = os.path.join(DATA, "..", ".flows", "revenue")
INDEX = "https://transfers.main.fastnear.com/v0/transfers"
YOCTO = 10**24


def balance(account, height):
    """Native NEAR of an account at a height, in yoctoNEAR as text. None when it cannot be read."""
    try:
        got = rpc.call("query", {"request_type": "view_account", "block_id": height, "account_id": account})
    except rpc.UnknownBlock:
        raise
    except rpc.RpcError as e:
        if "UNKNOWN_ACCOUNT" in str(e) or "does not exist" in str(e):
            return "0"          # the account did not exist yet at that block: it held nothing, which is known
        return None
    return str(got["amount"])


def pull_balances(only_missing=True):
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    rec = load(PATH, None) or {"wallets": WALLETS, "balances": {}, "transfers": {}}
    done = 0
    for day in sorted(blocks):
        row = rec["balances"].setdefault(day, {})
        for w in WALLETS:
            if only_missing and row.get(w) is not None:
                continue
            row[w] = balance(w, blocks[day]["height"])
            done += 1
        if done and done % 60 == 0:
            save(PATH, rec)
    save(PATH, rec)
    print(f"{done} balances read; {len(rec['balances'])} days stored")
    return rec


def fetch(account, day, pause=1.5):
    d = dt.date.fromisoformat(day)
    a = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
    rows, token = [], None
    while True:
        body = {"account_id": account, "from_timestamp_ms": a, "to_timestamp_ms": a + 86_400_000, "limit": 100}
        if token:
            body["resume_token"] = token
        req = urllib.request.Request(INDEX, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "waterline/1"})
        for attempt in range(12):
            try:
                with urllib.request.urlopen(req, timeout=40) as res:
                    got = json.load(res)
                break
            except (OSError, ValueError):
                time.sleep(min(30, 3 + 3 * attempt))
        else:
            raise SystemExit(f"the index did not answer for {account} on {day}")
        rows += got["transfers"]
        token = got.get("resume_token")
        if not token or not got["transfers"]:
            return rows
        time.sleep(pause)


COUNTED = ("native:near", "nep141:wrap.near")   # DefiLlama counts NEAR and wNEAR received; so do we


def summarise_transfers(rows, blocks, days):
    """Per day and wallet, between the reading before the day and its own: NEAR and wNEAR received, native NEAR in
    and out (to set against the balance read from the chain), and who sent the most. Amounts are yoctoNEAR as text."""
    out = {}
    for day in days:
        before = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        if before not in blocks or day not in blocks:
            continue
        lo, hi = blocks[before], blocks[day]
        per = {}
        for w, listed in rows.items():
            seen, received, native_in, native_out, n, senders = set(), 0, 0, 0, 0, {}
            for t in listed:
                key = (t["receipt_id"], t.get("action_index"), t.get("transfer_index"), t.get("log_index"), t["asset_id"], t["amount"])
                if t["asset_id"] not in COUNTED or not lo < int(t["block_height"]) <= hi or key in seen:
                    continue
                if t["asset_id"] == "nep141:wrap.near" and t.get("transfer_type") not in (None, "FtTransfer"):
                    continue    # wNEAR also shows as the mint and burn of wrapping; only a transfer between accounts is income
                seen.add(key)
                amount = int(t["amount"])
                if t["asset_id"] == "native:near":
                    if amount > 0:
                        native_in += amount
                    else:
                        native_out -= amount
                if amount > 0:
                    received += amount
                    n += 1
                    s = t.get("other_account_id") or ""
                    senders[s] = senders.get(s, 0) + amount
            per[w] = {"received": str(received), "native_in": str(native_in), "native_out": str(native_out), "transfers_in": n,
                      "from": {k: str(v) for k, v in sorted(senders.items(), key=lambda kv: -kv[1])[:5]}}
        out[day] = per
    return out


def pull_transfers(first, last):
    os.makedirs(RAW, exist_ok=True)
    a, b = dt.date.fromisoformat(first), dt.date.fromisoformat(last)
    cal = [(a + dt.timedelta(days=k)).isoformat() for k in range(-1, (b - a).days + 1)]
    rows = {w: [] for w in WALLETS}
    for w in WALLETS:
        for day in cal:
            path = os.path.join(RAW, f"{w}.{day}.json")
            if not os.path.exists(path):
                got = fetch(w, day)
                with open(path, "w") as f:
                    json.dump(got, f)
                print(f"{w} {day}: {len(got)} transfers listed", flush=True)
            rows[w] += load(path, [])
    blocks = {d: v["height"] for d, v in load(os.path.join(DATA, "blocks.json"), {}).items()}
    rec = load(PATH, None) or {"wallets": WALLETS, "balances": {}, "transfers": {}}
    rec["transfers"].update(summarise_transfers(rows, blocks, cal[1:]))
    rec["source"] = INDEX + " (FastNEAR transfers index, no key) for the transfers; view_account on an archival node for the balances"
    save(PATH, rec)
    return rec


def window(rec, first, last):
    """Totals over the days from first to last (inclusive): NEAR and wNEAR received by the wallets, and a check that
    native NEAR in minus out equals the change in each wallet's balance read from the chain. None when a balance in
    the window is unknown or a day has no transfer list."""
    days = sorted(d for d in rec["balances"] if first <= d <= last)
    before = (dt.date.fromisoformat(first) - dt.timedelta(days=1)).isoformat()
    if before not in rec["balances"] or not days:
        return None
    out = {"first": days[0], "last": days[-1], "days": len(days), "received": 0, "by_wallet": {}, "adds_up": True}
    for w in rec["wallets"]:
        b0, b1 = rec["balances"][before].get(w), rec["balances"][days[-1]].get(w)
        if b0 is None or b1 is None:
            return None
        received = native_in = native_out = 0
        for d in days:
            t = rec["transfers"].get(d, {}).get(w)
            if t is None:
                return None
            received += int(t["received"])
            native_in += int(t["native_in"])
            native_out += int(t["native_out"])
        change = int(b1) - int(b0)
        ok = native_in - native_out == change
        out["by_wallet"][w] = {"received": received, "native_in": native_in, "native_out": native_out, "change": change, "adds_up": ok}
        out["received"] += received
        out["adds_up"] = out["adds_up"] and ok
    return out


def main():
    ap = argparse.ArgumentParser(description="Measure the revenue reaching NEAR's wallets from the chain.")
    ap.add_argument("--balances", action="store_true")
    ap.add_argument("--transfers", nargs=2, metavar=("FIRST", "LAST"))
    args = ap.parse_args()
    if args.balances:
        pull_balances()
        return 0
    if args.transfers:
        pull_transfers(*args.transfers)
        return 0
    rec = load(PATH, None)
    if not rec:
        raise SystemExit("data/context/revenue.json does not exist yet: run with --balances")
    days = sorted(rec["balances"])
    for w in rec["wallets"]:
        known = [(d, rec["balances"][d][w]) for d in days if rec["balances"][d].get(w) is not None]
        if known:
            print(f"{w:36} {known[0][0]} {int(known[0][1]) / YOCTO:12,.0f} NEAR  ->  {known[-1][0]} {int(known[-1][1]) / YOCTO:12,.0f} NEAR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
