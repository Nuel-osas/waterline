"""A base-rate model for the long-dated readings: how often the float's own past, replayed, meets them.

  python3 -m pipeline.model                                  # the three windows the thesis quotes
  python3 -m pipeline.model --since 2026-10-01               # another window of past days
  python3 -m pipeline.model --block 1 --paths 50000 --seed 7 # other settings

Method: a moving-block bootstrap. Take the float's daily changes over a window of past days, in dollars at the
pinned prices. Build each future path by drawing a run of `block` consecutive days at random from the window,
again and again, laying the runs end to end until the path reaches the day the readings are scored. Drawing whole
runs keeps a lump together with the days after it. The float and the float without NEAR's own token are drawn
from the same days, so the two stay tied. Each path is then scored with the thresholds of R1, R2 and R5.

What it is not. It is a base rate, not a forecast: it answers "if the days to come are drawn from this window,
how often does the reading hold?". It knows nothing about why the float moved, so a window with a reward open in
it assumes the reward goes on, and one without assumes none. Changes are in dollars, not in percent, so growth
does not compound. R3 and R4 are not modelled: they need the public side and the revenue, which the float's
history does not contain.

Same arguments, same numbers on any machine: the paths are drawn from Python's seeded generator and added up in
whole cents.
"""
import argparse
import datetime as dt
import os
import random
from fractions import Fraction

from .build import REWARD_ANNOUNCED, REWARD_TRIGGER, build
from .score import LONG_DATED

SEED = 20261113
PATHS = 10000
BLOCK = 7
CENTS = 100
R1_HOLDS = 200_000_000 * CENTS      # R1: the float is at least $200M
R5_HOLDS = 130_000_000 * CENTS      # R5: the float without NEAR's own token is at least $130M
R2_HOLDS, R2_BREAKS = 45, 55        # R2: the ten best days as a percentage of the float


def cents(x):
    return int(Fraction(x) * CENTS)


def ex_near(r):
    return r["float_usd"] - r["groups"]["NEAR"]


def simulate(rows, pin, since=None, until=None, block=BLOCK, paths=PATHS, seed=SEED, target=LONG_DATED):
    """Share of paths on which each reading holds, and breaks, on the target day. `rows` is the daily series."""
    seen = [r for r in rows if r["day"] <= pin]
    since, until = since or seen[0]["day"], until or pin
    window = [r for r in seen if since <= r["day"] <= until]
    if block < 1 or paths < 1 or len(window) < block + 1:
        raise SystemExit(f"{len(window)} readings between {since} and {until} are too few for runs of {block} days")
    moves = [(cents(window[k]["float_usd"]) - cents(window[k - 1]["float_usd"]),
              cents(ex_near(window[k])) - cents(ex_near(window[k - 1]))) for k in range(1, len(window))]
    start = seen[-1]
    if start["day"] != pin:
        raise SystemExit(f"no reading for the pinned day {pin}")
    f0, e0 = cents(start["float_usd"]), cents(ex_near(start))
    horizon = (dt.date.fromisoformat(target) - dt.date.fromisoformat(pin)).days
    # R2 counts the ten largest one-day rises over the whole history, past and drawn
    past_top = sorted((cents(seen[k]["float_usd"]) - cents(seen[k - 1]["float_usd"]) for k in range(1, len(seen))),
                      reverse=True)[:10]
    starts = len(moves) - block + 1
    rng = random.Random(seed)
    n = {"r1_holds": 0, "r1_breaks": 0, "r2_holds": 0, "r2_breaks": 0, "r5_holds": 0, "r5_breaks": 0}
    ends = []
    for _ in range(paths):
        f, e, day, rises = f0, e0, 0, []
        while day < horizon:
            at = int(rng.random() * starts)
            for df, de in moves[at:at + block]:
                if day == horizon:
                    break
                df, de = max(df, -f), max(de, -e)   # a balance cannot go below nothing
                f, e, day = f + df, e + de, day + 1
                if df > past_top[-1]:
                    rises.append(df)
        top = sum(sorted(past_top + rises, reverse=True)[:10])
        ends.append(f)
        n["r1_holds"] += f >= R1_HOLDS
        n["r1_breaks"] += f < f0
        n["r2_holds"] += top * 100 < R2_HOLDS * f
        n["r2_breaks"] += top * 100 > R2_BREAKS * f
        n["r5_holds"] += e >= R5_HOLDS
        n["r5_breaks"] += e < e0
    ends.sort()
    out = {k: Fraction(v, paths) for k, v in n.items()}
    out.update({"since": since, "until": until, "pin": pin, "target": target, "horizon_days": horizon,
                "changes": len(moves), "block": block, "paths": paths, "seed": seed,
                "p10_usd": ends[paths // 10] // CENTS, "median_usd": ends[paths // 2] // CENTS,
                "p90_usd": ends[paths * 9 // 10] // CENTS})
    return out


def windows(rows, pin):
    """The three windows the thesis quotes, cut at the reward programme's two public dates, not chosen by result."""
    first = next(r["day"] for r in rows if r["types"] > 0)
    return [
        ("whole", "every day since the first deposit", first, pin),
        ("before", "before the reward programme was announced", first, REWARD_ANNOUNCED),
        ("after", "since the first reward's snapshot was triggered", REWARD_TRIGGER, pin),
    ]


def scenarios(rows, pin, **settings):
    return [(key, label, simulate(rows, pin, since, until, **settings)) for key, label, since, until in windows(rows, pin)]


def share(x):
    """A share of paths as text. Nothing is rounded to 'never' or 'always' unless it is exactly that."""
    if x == 0:
        return "none"
    if x == 1:
        return "all"
    p = float(x) * 100
    return "under 1%" if p < 1 else "over 99%" if p > 99 else f"{p:.0f}%"


def main():
    ap = argparse.ArgumentParser(description="How often the float's own past, replayed, meets the long-dated readings.")
    ap.add_argument("--since", help="first past day to draw from (default: the three windows the thesis quotes)")
    ap.add_argument("--until", help="last past day to draw from (default: the pinned day)")
    ap.add_argument("--block", type=int, default=BLOCK, help=f"days in each run drawn (default {BLOCK})")
    ap.add_argument("--paths", type=int, default=PATHS, help=f"paths drawn (default {PATHS})")
    ap.add_argument("--seed", type=int, default=SEED, help=f"seed (default {SEED})")
    args = ap.parse_args()
    from .pull import DATA, load
    rows, _, _, _ = build(write=False)
    pin = load(os.path.join(DATA, "pin.json"), None)["pin_day"]
    settings = {"block": args.block, "paths": args.paths, "seed": args.seed}
    if args.since or args.until:
        runs = [("custom", "the window asked for", simulate(rows, pin, args.since, args.until, **settings))]
    else:
        runs = scenarios(rows, pin, **settings)
    m = runs[0][2]
    print(f"{m['paths']} paths of {m['horizon_days']} days, from the {m['pin']} reading to {m['target']}; "
          f"runs of {m['block']} days; seed {m['seed']}")
    print(f"{'days drawn from':50} {'changes':>7}  {'R1 holds':>9} {'breaks':>9}  {'R2 holds':>9} {'breaks':>9}  "
          f"{'R5 holds':>9} {'breaks':>9}  float on the day: 10th, median, 90th")
    for _, label, m in runs:
        print(f"{label[:50]:50} {m['changes']:>7}  {share(m['r1_holds']):>9} {share(m['r1_breaks']):>9}  "
              f"{share(m['r2_holds']):>9} {share(m['r2_breaks']):>9}  {share(m['r5_holds']):>9} {share(m['r5_breaks']):>9}  "
              f"${m['p10_usd'] / 1e6:.0f}M, ${m['median_usd'] / 1e6:.0f}M, ${m['p90_usd'] / 1e6:.0f}M")
    print("R1: float at least $200M (breaks: below the pinned day's). R2: ten best days under 45% of the float "
          "(breaks: above 55%). R5: float without NEAR's own token at least $130M (breaks: below the pinned day's).")
    print("A base rate, not a forecast: it assumes the days to come are drawn from the window named.")


if __name__ == "__main__":
    main()
