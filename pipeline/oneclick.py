"""Show from 1Click's own records that its swaps settle through the private chain's treasury.

  python3 -m pipeline.oneclick                 # the summary of data/context/oneclick.json (no network)
  python3 -m pipeline.oneclick --scan          # look again: accounts that paid into the treasury, asked of 1Click (slow)

NEAR's changelog says that from 27 October 2026 1Click swaps settle on the private chain, and that a swap's
`nearTxHashes` then lists the shield and unshield transactions instead of the swap. This takes accounts that paid
into the treasury after that date, asks 1Click's public status endpoint whether each is one of its deposit
addresses, and for every completed swap checks whether the swap's own record lists the transaction that moved its
tokens into the treasury. Each such receipt is then read from the chain: it must carry a transfer, signed for the
deposit address, of that amount, to the treasury.

The status endpoint is 1Click's, not the chain's: it is used to find the swaps and to show that the operator's own
record names the transaction. The transfer itself is read from the chain, and `make verify` reads it again.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request

from . import rpc, trace
from .pull import DATA, load, save

PATH = os.path.join(DATA, "context", "oneclick.json")
STATUS = "https://1click.chaindefuser.com/v0/status?depositAddress="
INDEX = "https://transfers.main.fastnear.com/v0/transfers"
SWITCH = "2026-10-27"


def _get(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "User-Agent": "waterline/1"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=40) as res:
                return res.status, json.load(res)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, None
            time.sleep(3 + 2 * attempt)
        except (OSError, ValueError):
            time.sleep(3 + 2 * attempt)
    return None, None


def is_implicit(account):
    return len(account) == 64 and all(c in "0123456789abcdef" for c in account)


def scan(days, hours=2):
    """Accounts that paid into the treasury in `hours` from noon UTC on each day, asked of 1Click. Completed or
    refunded swaps are kept with the treasury transfers seen for their deposit address."""
    senders = {}
    for day in days:
        d = dt.date.fromisoformat(day)
        a = int(dt.datetime(d.year, d.month, d.day, 12, tzinfo=dt.timezone.utc).timestamp() * 1000)
        _, got = _get(INDEX, {"account_id": rpc.TREASURY, "from_timestamp_ms": a, "to_timestamp_ms": a + hours * 3_600_000, "limit": 100})
        time.sleep(1.6)
        for t in (got or {}).get("transfers", []):
            other = t.get("other_account_id") or ""
            if int(t["amount"]) > 0 and is_implicit(other):
                senders.setdefault(other, []).append({"tx": t["transaction_id"], "receipt_id": t["receipt_id"], "height": int(t["block_height"]),
                                                      "asset": t["asset_id"].replace("nep245:intents.near:", ""), "amount": t["amount"]})
    found, asked = [], 0
    for address, transfers in senders.items():
        code, body = _get(STATUS + address)
        asked += 1
        time.sleep(1.0)
        if not body or body.get("status") in (None, "PENDING_DEPOSIT"):
            continue
        details = body.get("swapDetails") or {}
        listed = set(details.get("nearTxHashes") or [])
        quote = (body.get("quoteResponse") or {}).get("quoteRequest") or {}
        found.append({"deposit_address": address, "status": body["status"], "updated_at": body.get("updatedAt"),
                      "origin_asset": quote.get("originAsset"), "destination_asset": quote.get("destinationAsset"),
                      "confidentiality": quote.get("confidentiality"), "deposit_type": quote.get("depositType"),
                      "amount_in_usd": details.get("amountInUsd"), "near_tx_hashes": sorted(listed),
                      "treasury_transfers": [t for t in transfers if t["tx"] in listed]})
    return {"days": days, "senders": len(senders), "asked": asked, "swaps": found}


def confirm(rec):
    """Read each recorded treasury receipt from the chain. Returns the number that carry the stated transfer."""
    good = 0
    for swap in rec["swaps"]:
        for t in swap["treasury_transfers"]:
            receipt = rpc.call("EXPERIMENTAL_receipt", {"receipt_id": t["receipt_id"]})
            want = {"from": swap["deposit_address"], "to": rpc.TREASURY, "amount": int(t["amount"]), "how": "transfer intent"}
            t["on_chain"] = want in trace.legs(receipt, t["asset"])
            good += t["on_chain"]
    return good


def main():
    ap = argparse.ArgumentParser(description="Show from 1Click's own records that its swaps settle through the treasury.")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--from-file", help="build the record from an earlier scan's output instead of scanning again")
    args = ap.parse_args()
    if args.scan or args.from_file:
        if args.from_file:
            raw = load(args.from_file, [])
            rec = {"days": ["2026-10-29", "2026-11-02", "2026-11-06", "2026-11-09", "2026-11-11", "2026-11-13"], "senders": None, "asked": None, "swaps": []}
            for h in raw:
                details = h.get("swapDetails") or {}
                listed = set(details.get("nearTxHashes") or [])
                q = h.get("quote") or {}
                rec["swaps"].append({"deposit_address": h["deposit_address"], "status": h["status"], "updated_at": h.get("updatedAt"),
                                     "origin_asset": q.get("originAsset"), "destination_asset": q.get("destinationAsset"),
                                     "confidentiality": q.get("confidentiality"), "deposit_type": q.get("depositType"),
                                     "amount_in_usd": details.get("amountInUsd"), "near_tx_hashes": sorted(listed),
                                     "treasury_transfers": [{"tx": t["tx"], "receipt_id": t["receipt"], "height": int(t["block"]),
                                                             "asset": t["asset"].replace("nep245:intents.near:", ""), "amount": t["amount"]}
                                                            for t in h["treasury_transfers"] if t["tx"] in listed]})
        else:
            rec = scan(["2026-10-29", "2026-11-02", "2026-11-06", "2026-11-09", "2026-11-11", "2026-11-13"])
        rec["checked_on_chain"] = confirm(rec)
        rec["source"] = "1Click status endpoint (" + STATUS + "<address>, public) to find swaps; EXPERIMENTAL_receipt on an archival node for each transfer"
        save(PATH, rec)
    rec = load(PATH, None)
    if not rec:
        raise SystemExit("data/context/oneclick.json does not exist yet: run with --scan")
    n = len(rec["swaps"])
    listed = sum(1 for s in rec["swaps"] if s["treasury_transfers"])
    onchain = sum(1 for s in rec["swaps"] for t in s["treasury_transfers"] if t.get("on_chain"))
    print(f"{n} completed or refunded 1Click swaps found; {listed} list, among their own NEAR transactions, the one that moved "
          f"their tokens into the treasury; {onchain} of those transfers read back from the chain as stated")
    for s in rec["swaps"]:
        print(f"  {s['updated_at'][:10]}  {s['status']:9} {s['confidentiality'] or '?':7}  {(s['origin_asset'] or '')[:30]:30} -> {(s['destination_asset'] or '')[:30]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
