"""Pull the raw history from public NEAR mainnet.

  python3 -m pipeline.pull            # add any missing days up to today
  python3 -m pipeline.pull --held     # also read what all of intents.near holds for the tracked tokens

For each day it finds one block just after 00:00 UTC, then at that exact height reads
  - every token balance the private-chain treasury holds inside `intents.near`  (data/float/<day>.json)
  - how much of the same token `intents.near` holds in total, from the token's own contract
    (data/held/<day>.json)
Heights are written to data/blocks.json. Anyone can re-read the same heights and must get the same bytes.
"""
import datetime as dt
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from . import rpc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UTC = dt.timezone.utc
WINDOW_NS = 15 * 10**9  # the day's block is any block stamped in the first 15 s after midnight UTC


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def header_near(height):
    """Header at `height`, or at the next height that exists (some heights are skipped)."""
    for h in range(height, height + 30):
        try:
            return rpc.header(h)
        except rpc.UnknownBlock:
            continue
    raise rpc.RpcError(f"no block near {height}")


def block_at(target_ns, anchors):
    """Find a block stamped in [target, target + WINDOW). `anchors` is a list of known (height, ns)."""
    lo = max((a for a in anchors if a[1] < target_ns), key=lambda a: a[1], default=None)
    hi = min((a for a in anchors if a[1] >= target_ns), key=lambda a: a[1], default=None)
    if lo is None or hi is None:
        raise rpc.RpcError("target time is outside the known block range")
    for _ in range(60):
        if target_ns <= hi[1] < target_ns + WINDOW_NS:
            return hi
        span_h, span_t = hi[0] - lo[0], hi[1] - lo[1]
        if span_h <= 1:
            return hi
        guess = lo[0] + max(1, min(span_h - 1, round(span_h * (target_ns - lo[1] + WINDOW_NS // 3) / span_t)))
        head = header_near(guess)
        got = (head["height"], head["timestamp"])
        if got[0] >= hi[0]:
            got = (guess, None)
            head = header_near(lo[0] + span_h // 2)
            got = (head["height"], head["timestamp"])
            if got[0] >= hi[0]:
                return hi
        if got[1] < target_ns:
            lo = got
        else:
            hi = got
    return hi


def read_float(height):
    ids = []
    start = 0
    while True:
        page = rpc.view(height, rpc.LEDGER, "mt_tokens_for_owner",
                        {"account_id": rpc.TREASURY, "from_index": str(start), "limit": 200})
        if page is None:
            return None
        ids += [t["token_id"] for t in page]
        if len(page) < 200:
            break
        start += 200
    out = {}
    for i in range(0, len(ids), 100):
        part = ids[i:i + 100]
        bal = rpc.view(height, rpc.LEDGER, "mt_batch_balance_of", {"account_id": rpc.TREASURY, "token_ids": part})
        if bal is None:
            return None
        out.update(dict(zip(part, bal)))
    return out


def read_held(height, token_id):
    """Units of `token_id` that intents.near holds for everyone, read from the token's own contract."""
    kind, _, rest = token_id.partition(":")
    if kind == "nep141":
        return rpc.view(height, rest, "ft_balance_of", {"account_id": rpc.LEDGER})
    if kind == "nep245":
        contract, _, inner = rest.partition(":")
        return rpc.view(height, contract, "mt_balance_of", {"account_id": rpc.LEDGER, "token_id": inner})
    return None


def days(first, last):
    d = first
    while d <= last:
        yield d
        d += dt.timedelta(days=1)


def main(argv):
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    head = rpc.header(None)
    today = dt.datetime.fromtimestamp(head["timestamp"] / 1e9, UTC).date()
    first = dt.date.fromisoformat(os.environ.get("FIRST_DAY", "2026-06-01"))
    anchors = [(b["height"], b["timestamp"]) for b in blocks.values()] + [(head["height"], head["timestamp"])]
    # one old anchor so every target day is bracketed
    old = header_near(int(os.environ.get("OLD_ANCHOR", "195000000")))
    anchors.append((old["height"], old["timestamp"]))

    want = [] if "--no-new-days" in argv else [d for d in days(first, today) if d.isoformat() not in blocks]

    def find(d):
        target = int(dt.datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp()) * 10**9
        if target < old["timestamp"] or target > head["timestamp"]:
            return
        h, ns = block_at(target, list(anchors))
        anchors.append((h, ns))
        blocks[d.isoformat()] = {"height": h, "timestamp": ns}

    # coarse pass first (every 16th day) so the fine pass starts from close anchors
    for part in (want[::16], want):
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(find, [d for d in part if d.isoformat() not in blocks]))
        save(os.path.join(DATA, "blocks.json"), dict(blocks))
    print("days with a block:", len(blocks), flush=True)

    def do_float(day):
        path = os.path.join(DATA, "float", day + ".json")
        if os.path.exists(path):
            return
        bal = read_float(blocks[day]["height"])
        save(path, {"day": day, "height": blocks[day]["height"], "balances": bal})

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(do_float, sorted(blocks)))
    print("float days:", len(os.listdir(os.path.join(DATA, "float"))), flush=True)

    if "--held" in argv:
        tracked = load(os.path.join(DATA, "tracked.json"), [])
        # Totals are read for every day from HELD_FROM on, and for every HELD_EVERY-th day before it.
        held_from = os.environ.get("HELD_FROM", "2026-10-23")
        every = int(os.environ.get("HELD_EVERY", "7"))
        only = os.environ.get("HELD_ONLY", "")  # "recent" or "early": lets two nodes share the work
        ordered = sorted(blocks)
        early = [d for d in ordered if d < held_from][::-1][::every]
        recent = [d for d in ordered if d >= held_from]
        chosen = recent if only == "recent" else early if only == "early" else early + recent

        def do_held(day):
            path = os.path.join(DATA, "held", day + ".json")
            have = load(path, {"day": day, "height": blocks[day]["height"], "held": {}})
            todo = [t for t in tracked if t not in have["held"]]
            if not todo:
                return
            for t in todo:
                have["held"][t] = read_held(blocks[day]["height"], t)
            save(path, have)

        with ThreadPoolExecutor(2) as ex:
            list(ex.map(do_held, sorted(chosen, reverse=True)))
        print("held days:", len(os.listdir(os.path.join(DATA, "held"))), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
