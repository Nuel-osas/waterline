"""Audit NEAR Intents' public books from outside: what it has credited against what it holds, token by token.

  python3 -m pipeline.audit                      # the audit of every stored day, from data/ (no network)
  python3 -m pipeline.audit --now                # the tracked tokens at the latest final block, live (about 25 requests)
  python3 -m pipeline.audit --pull               # read the credited totals for every day that has held totals (one call a day)
  python3 -m pipeline.audit --steps FROM TO      # every block between two readings where one token's hole changed (slow)

Two questions, asked of two different contracts at the same block:

  intents.near.mt_batch_supply(token_ids)        -> credited: what NEAR Intents says it owes, to all accounts together
  <token>.ft_balance_of("intents.near")          -> held: what the token's own contract says NEAR Intents has

Held at or above credited: the books are whole for that token. Credited above held: a hole, and its size is the
difference. A surplus (held above credited) is tokens that reached the contract without a credit; in the blocks
we looked at one by one it lasts a block or two around a deposit or a withdrawal, and it is not a risk to anyone
who is owed.

This audits the public ledger only. The largest account on that ledger is the private chain's treasury, and what
the private chain owes its own users cannot be asked of any contract.
"""
import argparse
import datetime as dt
import os
import sys
from fractions import Fraction

from . import rpc
from .pull import DATA, load, read_held, save

CREDITED = os.path.join(DATA, "credited")
EXPLOIT = os.path.join(DATA, "context", "exploit.json")
BATCH = 100


def read_credited(height, ids):
    """What intents.near has credited in total for each token id at a height: {id: units as text, or None}."""
    out = {}
    for k in range(0, len(ids), BATCH):
        part = ids[k:k + BATCH]
        got = rpc.view(height, rpc.LEDGER, "mt_batch_supply", {"token_ids": part})
        for i, tid in enumerate(part):
            out[tid] = str(got[i]) if got is not None and i < len(got) and got[i] is not None else None
    return out


def compare(credited, held):
    """One token at one block. Returns (status, hole): hole is credited minus held, None when either is unknown."""
    if credited is None or held is None:
        return "unknown", None
    hole = int(credited) - int(held)
    return ("short" if hole > 0 else "equal" if hole == 0 else "surplus"), hole


def audit_day(held, credited, meta):
    """Every token of one day. `meta` maps a token id to {decimals, price}. Dollar figures are exact fractions."""
    rows, counts = [], {"equal": 0, "surplus": 0, "short": 0, "unknown": 0}
    held_usd = short_usd = surplus_usd = Fraction(0)
    for tid in sorted(held):
        status, hole = compare(credited.get(tid), held[tid])
        counts[status] += 1
        if status == "unknown":
            continue
        m = meta.get(tid)
        price = m["price"] if m and m.get("price") is not None else None
        value = None if price is None else Fraction(abs(hole), 10 ** m["decimals"]) * price
        if price is not None:
            held_usd += Fraction(int(held[tid]), 10 ** m["decimals"]) * price
            if status == "short":
                short_usd += value
            if status == "surplus":
                surplus_usd += value
        if status != "equal":
            rows.append({"token": tid, "status": status, "credited": str(credited[tid]), "held": str(held[tid]),
                         "hole": str(hole), "usd": value})
    return {"counts": counts, "checked": counts["equal"] + counts["surplus"] + counts["short"],
            "held_usd": held_usd, "short_usd": short_usd, "surplus_usd": surplus_usd, "not_equal": rows}


def stored_days():
    """Days that have both a held file and a credited file, oldest first: [(day, held, credited)]."""
    out = []
    for name in sorted(os.listdir(CREDITED)) if os.path.isdir(CREDITED) else []:
        day = name[:-5]
        held = load(os.path.join(DATA, "held", name), None)
        cred = load(os.path.join(CREDITED, name), None)
        if held and cred and held.get("height") == cred.get("height"):
            out.append((day, {k: v for k, v in held["held"].items() if v is not None}, cred["credited"]))
    return out


def history(meta, tracked=None):
    """The audit of every stored day. With `tracked`, only those tokens (the same set on every day)."""
    out = []
    for day, held, credited in stored_days():
        if tracked is not None:
            held = {k: v for k, v in held.items() if k in tracked}
        got = audit_day(held, credited, meta)
        got["day"] = day
        out.append(got)
    return out


def pull(only=None):
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    done = 0
    for name in sorted(os.listdir(os.path.join(DATA, "held"))):
        day = name[:-5]
        if not name.endswith(".json") or (only and day not in only):
            continue
        held = load(os.path.join(DATA, "held", name), None)
        ids = sorted(k for k, v in (held or {}).get("held", {}).items() if v is not None)
        path = os.path.join(CREDITED, name)
        have = load(path, None)
        if not ids or (have and have.get("height") == held["height"] and all(have["credited"].get(i) is not None for i in ids)):
            continue
        save(path, {"day": day, "height": held["height"], "credited": read_credited(held["height"], ids)})
        done += 1
        print(f"{day}  block {held['height']}  credited totals for {len(ids)} tokens", flush=True)
    print(f"credited totals read for {done} days; {len(blocks)} days have a block")


def now(ids):
    """The same audit at the latest final block. Returns (height, timestamp, {id: (credited, held)})."""
    head = rpc.header(None)
    height = head["height"]
    credited = read_credited(height, ids)
    return height, head["timestamp"], {tid: (credited[tid], read_held(height, tid)) for tid in ids}


def hole_at(token, height, seen):
    """(credited, held) for one token as of a height, or the nearest height above it that exists."""
    if height not in seen:
        seen[height] = None
        for h in range(height, height + 4):
            try:
                c, held = rpc.view(h, rpc.LEDGER, "mt_supply", {"token_id": token}), read_held(h, token)
            except rpc.UnknownBlock:
                continue
            if c is not None and held is not None:
                seen[height] = (int(c), int(held))
                break
    return seen[height]


def steps(read, lo, hi, grid=12, limit=1500):
    """Every height in (lo, hi] at which credited minus held changed, found by halving. `read(height)` returns
    (credited, held) or None. Moves that cancel between two points that were read are not seen; reading a coarse
    grid first makes that less likely. Gives up splitting after `limit` reads."""
    found, reads = [], [0]

    def hole(h):
        reads[0] += 1
        got = read(h)
        return None if got is None else got[0] - got[1]

    def split(a, x, b, y):
        if x is None or y is None or x == y or reads[0] > limit:
            return
        if b - a <= 1:
            found.append(b)
            return
        mid = (a + b) // 2
        m = hole(mid)
        split(a, x, mid, m)
        split(mid, m, b, y)

    points = [lo + (hi - lo) * i // grid for i in range(grid + 1)]
    values = [hole(p) for p in points]
    for k in range(grid):
        split(points[k], values[k], points[k + 1], values[k + 1])
    return sorted(set(found))


def token_meta():
    from .build import token_meta as build_meta
    return build_meta()[0]


def main():
    ap = argparse.ArgumentParser(description="Audit NEAR Intents' public books: credited against held, token by token.")
    ap.add_argument("--now", action="store_true", help="audit the tracked tokens at the latest final block")
    ap.add_argument("--pull", action="store_true", help="read the credited totals for every day that has held totals")
    ap.add_argument("--steps", nargs=2, metavar=("FROM", "TO"), help="list the blocks between two readings where the hole changed")
    ap.add_argument("--token", help="token id for --steps (default: the token of the recorded exploit)")
    args = ap.parse_args()
    meta = token_meta()
    if args.pull:
        pull()
        return 0
    if args.now:
        tracked = load(os.path.join(DATA, "tracked.json"), [])
        height, stamp, got = now(tracked)
        when = dt.datetime.fromtimestamp(stamp / 1e9, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"block {height}, {when} UTC")
        short = 0
        for tid, (credited, held) in got.items():
            status, hole = compare(credited, held)
            m = meta.get(tid, {})
            unit = 10 ** m.get("decimals", 0)
            short += status == "short"
            print(f"  {status.upper() if status == 'short' else status:8} {m.get('symbol', '?'):8} {m.get('chain', '?'):6} "
                  + (f"credited {int(credited) / unit:18,.2f}  held {int(held) / unit:18,.2f}" if hole is not None else "could not be read"))
        print("RESULT:", "WHOLE: no token is credited above what is held" if not short else f"{short} token(s) SHORT")
        return 1 if short else 0
    if args.steps:
        blocks = load(os.path.join(DATA, "blocks.json"), {})
        token = args.token or (load(EXPLOIT, None) or {}).get("token")
        if not token or args.steps[0] not in blocks or args.steps[1] not in blocks:
            raise SystemExit("give two days that are in data/blocks.json, and --token if no exploit is recorded")
        seen = {}
        unit = 10 ** meta.get(token, {}).get("decimals", 0)
        for h in steps(lambda x: hole_at(token, x, seen), blocks[args.steps[0]]["height"], blocks[args.steps[1]]["height"]):
            before, after = hole_at(token, h - 1, seen), hole_at(token, h, seen)
            print(f"block {h}  hole {(before[0] - before[1]) / unit:16,.2f} -> {(after[0] - after[1]) / unit:16,.2f}")
        print(f"{len(seen)} states read, two calls each")
        return 0
    days = history(meta)
    if not days:
        raise SystemExit("no credited totals stored yet: run with --pull")
    for d in days:
        short = [r for r in d["not_equal"] if r["status"] == "short"]
        print(f"{d['day']}  {d['checked']:3d} tokens  ${float(d['held_usd']) / 1e6:7.1f}M held  {d['counts']['equal']:3d} equal  "
              f"{d['counts']['surplus']:3d} surplus  " + (f"SHORT {len(short)}: ${float(d['short_usd']):,.0f}" if short else "none short"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
