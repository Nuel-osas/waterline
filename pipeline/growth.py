"""The upside case: how fast has the revenue that funds NEAR's buyback grown, counted in NEAR, and how sure is that?

  python3 -m pipeline.growth                       # the trend, its range, and the odds of clearing a given pace
  python3 -m pipeline.growth --at 0.84 --seed 7

Revenue is DefiLlama's daily revenue for NEAR Intents (data/context/defillama.json), which agrees with the chain to
within a percent over the window this repository reads (claim U3), turned into NEAR at NearBlocks' price for each
day (data/context/activity.json). Before the buyback began on 2026-02-23 the revenue arrived in occasional lumps,
with weeks of zeros between them, so the trend starts there: complete Monday-to-Sunday weeks from that day to the
last complete week before the pinned day.

The trend is a straight line through the logarithm of the weekly totals, annualised. Its range comes from
resampling the residuals in runs of four weeks (a moving-block bootstrap, so a run of good or bad weeks stays
together) and refitting. Seeded: the same arguments give the same numbers on any machine.
"""
import argparse
import datetime as dt
import math
import os
import random
import sys

from .pull import DATA, load

START = "2026-02-23"    # the first day of the buyback, per DefiLlama's adapter; revenue is daily from here
SEED = 20261114
RESAMPLES = 4000
RUN = 4


def weekly_near(pin, start=START):
    """Weekly revenue in NEAR for complete Monday-to-Sunday weeks from `start` to the last one ending before `pin`."""
    rev = dict(load(os.path.join(DATA, "context", "defillama.json"), {})["series"]["revenue"]["daily"])
    act = load(os.path.join(DATA, "context", "activity.json"), {})["days"]
    d = dt.date.fromisoformat(start)
    while d.weekday() != 0:
        d += dt.timedelta(days=1)
    last = dt.date.fromisoformat(pin) - dt.timedelta(days=1)
    weeks = []
    while d + dt.timedelta(days=6) <= last:
        days = [(d + dt.timedelta(days=k)).isoformat() for k in range(7)]
        if any(x not in rev or x not in act or float(act[x]["near_price"]) <= 0 for x in days):
            break
        weeks.append((d.isoformat(), sum(float(rev[x]) / float(act[x]["near_price"]) for x in days)))
        d += dt.timedelta(days=7)
    return weeks


def fit(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - b * mx, b


def annual(slope_per_week):
    return math.exp(slope_per_week * 365.25 / 7) - 1


def trend(pin, resamples=RESAMPLES, seed=SEED, run=RUN):
    weeks = weekly_near(pin)
    if len(weeks) < 3 * run or any(v <= 0 for _, v in weeks):
        raise SystemExit("not enough complete weeks of revenue to fit a trend")
    xs = list(range(len(weeks)))
    ys = [math.log(v) for _, v in weeks]
    a, b = fit(xs, ys)
    res = [y - (a + b * x) for x, y in zip(xs, ys)]
    rng = random.Random(seed)
    slopes = []
    for _ in range(resamples):
        drawn = []
        while len(drawn) < len(res):
            i = rng.randrange(0, len(res) - run + 1)
            drawn += res[i:i + run]
        slopes.append(fit(xs, [a + b * x + e for x, e in zip(xs, drawn[:len(res)])])[1])
    slopes.sort()
    return {"first_week": weeks[0][0], "last_week": weeks[-1][0], "weeks": len(weeks), "growth": annual(b),
            "low": annual(slopes[int(0.05 * resamples)]), "high": annual(slopes[int(0.95 * resamples) - 1]),
            "slopes": slopes, "resamples": resamples, "seed": seed, "run": run,
            "first_total": weeks[0][1], "last_total": weeks[-1][1]}


def share_at_least(t, rate):
    """Share of resampled trends whose annual growth is at least `rate` (a fraction, 0.84 for 84%)."""
    return sum(1 for s in t["slopes"] if annual(s) >= rate) / len(t["slopes"])


def main():
    ap = argparse.ArgumentParser(description="How fast has the revenue that funds NEAR's buyback grown, counted in NEAR?")
    ap.add_argument("--at", type=float, action="append", help="a growth rate to test, as a fraction (0.84 for 84%%); may be repeated")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    args = ap.parse_args()
    pin = load(os.path.join(DATA, "pin.json"), {})["pin_day"]
    t = trend(pin, args.resamples, args.seed)
    print(f"{t['weeks']} weekly totals from the week of {t['first_week']} to the week of {t['last_week']}; "
          f"{t['resamples']} resamples in runs of {t['run']} weeks, seed {t['seed']}")
    print(f"  trend: {t['growth'] * 100:.0f}% a year, counted in NEAR; 90% range {t['low'] * 100:.0f}% to {t['high'] * 100:.0f}%")
    for rate in args.at or [0.84, 0.46]:
        print(f"  share of resamples growing at least {rate * 100:.0f}% a year: {share_at_least(t, rate) * 100:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
