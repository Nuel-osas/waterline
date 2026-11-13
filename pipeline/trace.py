"""Trace the largest single moves of a token in or out of an account inside intents.near to the receipt behind each.

  python3 -m pipeline.trace 2026-09-25                  # wNEAR in the treasury, between the readings of 24 and 25 September
  python3 -m pipeline.trace 2026-09-25 --top 5
  python3 -m pipeline.trace 2026-09-25 --account <id>   # the same for another account's balance inside intents.near
  python3 -m pipeline.trace --record                    # redo every window recorded in data/context/trace.json (slow)

How. A balance at any past block is one view call, so the block in which it changed can be found by halving: read
the balance in the middle of the interval, keep going into whichever part changed more, repeat. About 17 reads
isolate one block in a day of blocks. For that block, EXPERIMENTAL_changes names the receipts that changed
intents.near's state and EXPERIMENTAL_receipt returns each one: who signed it and what it asked for.

Limits. Halving follows the larger net change, so two moves that cancel inside one interval are not seen, and a
day made of many small moves has no largest move worth the name: each window records how much of its change the
moves found explain. A receipt names an account, not a person.
"""
import argparse
import base64
import datetime as dt
import heapq
import json
import os

from . import rpc
from .pull import DATA, load, save

WNEAR = "nep141:wrap.near"
OUTSIDE = " (outside intents.near)"
PATH = os.path.join(DATA, "context", "trace.json")


def balance(account, token, height, seen):
    """Balance as of `height`: read at that height, or at the last one below it that exists (some are skipped)."""
    if height not in seen:
        for h in range(height, height - 30, -1):
            try:
                got = rpc.view(h, rpc.LEDGER, "mt_batch_balance_of", {"account_id": account, "token_ids": [token]})
            except rpc.UnknownBlock:
                continue
            if got is None:
                raise rpc.RpcError(f"balance of {token} at {h} could not be read")
            seen[height] = int(got[0])
            break
        else:
            raise rpc.RpcError(f"no block near {height}")
    return seen[height]


def largest_moves(read, lo, hi, top, enough=None):
    """The largest single-block changes of `read(height)` between two heights, largest first: [(height, change)].

    Stops after `top` moves, or sooner once the moves found add up to `enough` of the interval's net change."""
    whole = read(hi) - read(lo)
    heap, found = [(-abs(whole), lo, hi)], []
    while heap and len(found) < top:
        size, a, b = heapq.heappop(heap)
        if size == 0:
            break
        if b - a == 1:
            found.append((b, read(b) - read(a)))
            if enough is not None and whole and abs(sum(c for _, c in found)) >= abs(whole) * enough:
                break
            continue
        mid = (a + b) // 2
        for x, y in ((a, mid), (mid, b)):
            heapq.heappush(heap, (-abs(read(y) - read(x)), x, y))
    return found


def message_of(signed):
    """The signed message inside one entry of execute_intents, whatever standard wrapped it. None if unreadable."""
    payload = signed.get("payload") if isinstance(signed, dict) else None
    text = payload.get("message") or payload.get("text") if isinstance(payload, dict) else payload
    try:
        msg = json.loads(text) if isinstance(text, str) else None
    except ValueError:
        return None
    return msg if isinstance(msg, dict) else None


def signers(receipt):
    """Which public key signed for which account in a receipt's execute_intents call: {signer_id: public_key}."""
    out = {}
    for action in receipt.get("receipt", {}).get("Action", {}).get("actions", []):
        call = action.get("FunctionCall") if isinstance(action, dict) else None
        if not call or call["method_name"] != "execute_intents":
            continue
        try:
            args = json.loads(base64.b64decode(call["args"]))
        except ValueError:
            continue
        for signed in args.get("signed", []) if isinstance(args, dict) else []:
            msg = message_of(signed)
            if msg and msg.get("signer_id") and isinstance(signed.get("public_key"), str):
                out[msg["signer_id"]] = signed["public_key"]
    return out


def legs(receipt, token):
    """What one receipt asks intents.near to do with `token`: [{from, to, amount, how}]. Amounts are whole units."""
    out = []
    sender = receipt.get("predecessor_id")
    for action in receipt.get("receipt", {}).get("Action", {}).get("actions", []):
        call = action.get("FunctionCall") if isinstance(action, dict) else None
        if not call:
            continue
        try:
            args = json.loads(base64.b64decode(call["args"]))
        except ValueError:
            continue
        if not isinstance(args, dict):
            continue
        method = call["method_name"]
        if method == "execute_intents":
            for signed in args.get("signed", []):
                msg = message_of(signed) or {}
                signer = msg.get("signer_id")
                for intent in msg.get("intents", []):
                    kind = intent.get("intent")
                    if kind == "transfer" and token in intent.get("tokens", {}):
                        out.append({"from": signer, "to": intent.get("receiver_id"), "amount": int(intent["tokens"][token]),
                                    "how": "transfer intent"})
                    elif kind == "token_diff" and token in intent.get("diff", {}):
                        change = int(intent["diff"][token])
                        out.append({"from": signer if change < 0 else None, "to": signer if change > 0 else None,
                                    "amount": abs(change), "how": "swap leg"})
                    elif kind == "ft_withdraw" and "nep141:" + str(intent.get("token")) == token:
                        out.append({"from": signer, "to": str(intent.get("receiver_id")) + OUTSIDE, "amount": int(intent["amount"]),
                                    "how": "withdrawal intent"})
                    elif kind == "native_withdraw" and token == WNEAR:
                        out.append({"from": signer, "to": str(intent.get("receiver_id")) + OUTSIDE, "amount": int(intent["amount"]),
                                    "how": "withdrawal intent, unwrapped"})
        elif method == "ft_on_transfer" and "nep141:" + str(sender) == token:
            note = args.get("msg") or ""
            try:
                named = json.loads(note)
                to = named.get("receiver_id") if isinstance(named, dict) else None
            except ValueError:
                to = note or None
            out.append({"from": str(args.get("sender_id")) + OUTSIDE, "to": to or args.get("sender_id"),
                        "amount": int(args["amount"]), "how": "deposit"})
        elif method in ("mt_transfer", "mt_transfer_call") and args.get("token_id") == token:
            out.append({"from": sender, "to": args.get("receiver_id"), "amount": int(args["amount"]), "how": method})
        elif method in ("mt_batch_transfer", "mt_batch_transfer_call"):
            for tid, amount in zip(args.get("token_ids", []), args.get("amounts", [])):
                if tid == token:
                    out.append({"from": sender, "to": args.get("receiver_id"), "amount": int(amount), "how": method})
        elif method == "ft_withdraw" and "nep141:" + str(args.get("token")) == token:
            out.append({"from": sender, "to": str(args.get("receiver_id")) + OUTSIDE, "amount": int(args["amount"]), "how": method})
    return out


def receipts_in(height):
    """The receipts that changed intents.near's state in the block at `height`."""
    got = rpc.call("EXPERIMENTAL_changes", {"changes_type": "data_changes", "account_ids": [rpc.LEDGER],
                                            "key_prefix_base64": "", "block_id": height})
    ids = []
    for change in got["changes"]:
        rid = change["cause"].get("receipt_hash")
        if rid and rid not in ids:
            ids.append(rid)
    return [rpc.call("EXPERIMENTAL_receipt", {"receipt_id": rid}) for rid in ids]


def explain(height, change, account, token):
    """The legs, among the receipts of that block, that move `token` in or out of `account`."""
    out = []
    for receipt in receipts_in(height):
        for leg in legs(receipt, token):
            if account in (leg["from"], leg["to"]):
                out.append({"receipt_id": receipt["receipt_id"], "from": leg["from"], "to": leg["to"],
                            "amount": str(leg["amount"]), "how": leg["how"]})
    signed = sum(int(l["amount"]) * (1 if l["to"] == account else -1) for l in out)
    return out, signed == change


def trace_window(account, token, lo, hi, top, enough=None, say=None):
    seen = {}
    read = lambda h: balance(account, token, h, seen)   # noqa: E731
    change = read(hi) - read(lo)
    moves = []
    for height, delta in largest_moves(read, lo, hi, top, enough):
        found, exact = explain(height, delta, account, token)
        moves.append({"height": height, "change": str(delta), "legs": found, "legs_add_up": exact})
        if say:
            say(moves[-1])
    return {"from_height": lo, "to_height": hi, "change": str(change), "moves": moves,
            "explained": str(sum(int(m["change"]) for m in moves)), "balance_reads": len(seen)}


def show(move, decimals=24):
    print(f"  block {move['height']}  {int(move['change']) / 10**decimals:+16,.0f}" + ("" if move["legs_add_up"] else "   (legs below do not add up to it)"))
    for leg in move["legs"]:
        print(f"      {int(leg['amount']) / 10**decimals:14,.0f}  {leg['how']}: {leg['from']} -> {leg['to']}   receipt {leg['receipt_id']}")
    if not move["legs"]:
        print("      no receipt in that block names this account for this token")


def main():
    ap = argparse.ArgumentParser(description="Trace the largest single moves of a token to the receipt behind each.")
    ap.add_argument("day", nargs="?", help="a day in data/blocks.json; the window runs from the reading before it to its own")
    ap.add_argument("--account", default=rpc.TREASURY, help="account inside intents.near (default: the private chain's treasury)")
    ap.add_argument("--token", default=WNEAR)
    ap.add_argument("--top", type=int, default=3, help="how many moves to find (default 3)")
    ap.add_argument("--record", action="store_true", help="redo every window in data/context/trace.json and rewrite it")
    args = ap.parse_args()
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    if args.record:
        rec = load(PATH, None)
        if not rec:
            raise SystemExit("nothing recorded yet")
        for w in rec["windows"]:
            print(f"{w['from_day']} -> {w['to_day']}  {w['account'][:12]}  {w['token']}")
            got = trace_window(w["account"], w["token"], blocks[w["from_day"]]["height"], blocks[w["to_day"]]["height"],
                               w["top"], say=show)
            w.update(got)
        save(PATH, rec)
        return
    if not args.day or args.day not in blocks:
        raise SystemExit("give a day that is in data/blocks.json, for example 2026-09-25")
    before = (dt.date.fromisoformat(args.day) - dt.timedelta(days=1)).isoformat()
    if before not in blocks:
        raise SystemExit(f"no reading for {before}")
    print(f"{args.token} of {args.account} inside intents.near, between the readings of {before} and {args.day}")
    listed = load(os.path.join(DATA, "tokens.json"), {}).get("tokens", [])
    decimals = next((int(t["decimals"]) for t in listed if t.get("assetId") == args.token), 0)
    got = trace_window(args.account, args.token, blocks[before]["height"], blocks[args.day]["height"], args.top,
                       say=lambda move: show(move, decimals))
    unit = 10**decimals
    print(f"net change {int(got['change']) / unit:+,.0f}; the moves above explain {int(got['explained']) / unit:+,.0f}; "
          f"{got['balance_reads']} balance reads" + ("" if decimals else " (amounts in the token's smallest unit)"))


if __name__ == "__main__":
    main()
