"""Can a growth rate be read from the revenue that funds NEAR's buyback, counted in NEAR? This measures how much the
answer depends on the week the count starts from.

  python3 -m pipeline.growth                       # the weekly totals, and the trend fitted from every start week

Revenue is DefiLlama's daily revenue for NEAR Intents (data/context/defillama.json), which agrees with the chain to
within a percent over the window this repository reads (claim U3), turned into NEAR at NearBlocks' price for each
day (data/context/activity.json). Before the buyback began on 2026-02-23 the revenue arrived in occasional lumps,
with weeks of zeros between them, so the weeks start there: complete Monday-to-Sunday weeks from that day to the
last complete week before the pinned day.

A straight line through the logarithm of the weekly totals, annualised, is fitted from every start week that leaves
at least MIN_WEEKS weeks. When the rate moves a long way with the start week, the record does not support a growth
rate, and the thesis does not use one. Pull request 22 reported the fit from the first week alone, with a bootstrap
range around it; that range did not show how much the rate depends on the start, and it was withdrawn
(docs/ERRATA.md).
"""
import argparse
import datetime as dt
import math
import os
import sys

from .pull import DATA, load

START = "2026-02-23"    # the first day of the buyback, per DefiLlama's adapter; revenue is daily from here
MIN_WEEKS = 12          # the shortest run of weeks a trend is fitted to


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


def by_start(weeks, min_weeks=MIN_WEEKS):
    """[(start week, number of weeks, annual growth)] for a log-linear fit from every start that leaves `min_weeks`."""
    out = []
    for i in range(len(weeks) - min_weeks + 1):
        part = weeks[i:]
        xs = list(range(len(part)))
        out.append((part[0][0], len(part), annual(fit(xs, [math.log(v) for _, v in part])[1])))
    return out


def summary(pin, min_weeks=MIN_WEEKS):
    weeks = weekly_near(pin)
    if len(weeks) < min_weeks or any(v <= 0 for _, v in weeks):
        raise SystemExit("not enough complete weeks of revenue to fit a trend")
    fits = by_start(weeks, min_weeks)
    peak = max(weeks, key=lambda w: w[1])
    return {"first_week": weeks[0][0], "last_week": weeks[-1][0], "weeks": len(weeks), "min_weeks": min_weeks,
            "first_per_day": weeks[0][1] / 7, "last_per_day": weeks[-1][1] / 7,
            "peak_week": peak[0], "peak_per_day": peak[1] / 7, "fits": fits,
            "lowest": min(fits, key=lambda f: f[2]), "highest": max(fits, key=lambda f: f[2]),
            "from_first": fits[0], "latest": fits[-1]}


def main():
    argparse.ArgumentParser(description="Can a growth rate be read from the revenue that funds NEAR's buyback?").parse_args()
    pin = load(os.path.join(DATA, "pin.json"), {})["pin_day"]
    s = summary(pin)
    for d, v in weekly_near(pin):
        print(f"  week of {d}  {v / 7:>9,.0f} NEAR a day")
    print(f"{s['weeks']} complete weeks, {s['first_week']} to {s['last_week']}; a trend fitted from each start week that leaves "
          f"at least {s['min_weeks']} weeks:")
    for d, n, g in s["fits"]:
        print(f"  from {d} ({n} weeks): {g * 100:+.0f}% a year")
    print(f"  lowest {s['lowest'][2] * 100:+.0f}% (from {s['lowest'][0]}), highest {s['highest'][2] * 100:+.0f}% (from {s['highest'][0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
