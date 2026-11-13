"""Read what intents.near holds of EVERY token in NEAR Intents' own token list, at one day's block.

  python3 -m pipeline.held_all 2026-11-13

The daily series asks this only for a tracked set of tokens (public nodes rate-limit). This fills in the
rest for one day, so the headline share can be computed over everything with a price, not over a selection.
Results are added to data/held/<day>.json.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from .pull import DATA, load, read_held, save


def main(day):
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    height = blocks[day]["height"]
    listed = [t["assetId"] for t in load(os.path.join(DATA, "tokens.json"), None)["tokens"]]
    treasury = list(load(os.path.join(DATA, "float", day + ".json"), None)["balances"])
    path = os.path.join(DATA, "held", day + ".json")
    have = load(path, {"day": day, "height": height, "held": {}})
    todo = [t for t in dict.fromkeys(listed + treasury) if t not in have["held"]]
    print(f"{day} block {height}: {len(todo)} tokens to read", flush=True)

    def one(t):
        try:
            return t, read_held(height, t)
        except Exception as e:  # a token whose contract cannot answer is unknown, not zero
            print("unreadable", t, str(e)[:80], flush=True)
            return t, None

    with ThreadPoolExecutor(2) as ex:
        for n, (t, v) in enumerate(ex.map(one, todo), 1):
            have["held"][t] = v
            if n % 25 == 0:
                save(path, have)
                print(n, "read", flush=True)
    save(path, have)
    print("done:", len(have["held"]), "tokens in", path, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
