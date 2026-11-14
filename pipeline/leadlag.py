"""Test the track's working hypothesis: does NEAR Intents' volume lead network usage, or NEAR's price?

  python3 -m pipeline.leadlag                 # prints the test; no network
  python3 -m pipeline.leadlag --shifts 20000 --seed 7

Weekly series, Monday to Sunday, over the complete weeks that both sources cover up to the pinned day: volume is
DefiLlama's reported NEAR Intents volume (data/context/defillama.json), usage is NearBlocks' daily transactions and
active accounts (data/context/activity.json), price is NearBlocks' daily NEAR price. Each series becomes its weekly
change in logarithms. For leads of 1 to 8 weeks, the correlation of this week's volume change with the usage or
price change that many weeks later is compared with what the same correlation gives when one series is shifted
round in time by a random amount (a circular shift keeps each series' own pattern and breaks only the link
between them). The p-value is for the largest of the eight correlations, so trying eight leads is paid for.

Seeded: the same arguments give the same numbers on any machine.
"""
import argparse
import datetime as dt
import math
import os
import random
import sys

from .pull import DATA, load

SEED = 20261114
SHIFTS = 10000
LEADS = range(1, 9)


def weekly(daily, how):
    """{monday: value} for complete Monday-to-Sunday weeks. `how` is 'sum' or 'mean'."""
    weeks = {}
    for day, v in daily.items():
        d = dt.date.fromisoformat(day)
        weeks.setdefault(d - dt.timedelta(days=d.weekday()), []).append(v)
    out = {}
    for monday, vals in weeks.items():
        if len(vals) == 7:
            out[monday] = sum(vals) if how == "sum" else sum(vals) / 7
    return out


def changes(series, mondays):
    return [math.log(series[mondays[k]] / series[mondays[k - 1]]) for k in range(1, len(mondays))]


def corr(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy) if sx and sy else 0.0


def lagged(x, y, k):
    """Correlation of x now with y k steps later."""
    return corr(x[:len(x) - k], y[k:]) if k else corr(x, y)


def test(x, y, shifts=SHIFTS, seed=SEED):
    """The largest correlation over the leads, the lead it occurs at, and how often a circular shift of y does as well."""
    observed = {k: lagged(x, y, k) for k in LEADS}
    best_k = max(observed, key=lambda k: abs(observed[k]))
    best = abs(observed[best_k])
    rng = random.Random(seed)
    n, beat = len(y), 0
    for _ in range(shifts):
        s = rng.randrange(1, n)
        z = y[s:] + y[:s]
        if max(abs(lagged(x, z, k)) for k in LEADS) >= best:
            beat += 1
    return {"lead_weeks": best_k, "r": observed[best_k], "p": (beat + 1) / (shifts + 1), "same_week": lagged(x, y, 0),
            "by_lead": observed}


def series(pin):
    vol = {d: float(v) for d, v in dict(load(os.path.join(DATA, "context", "defillama.json"), {})["series"]["volume"]["daily"]).items()}
    act = load(os.path.join(DATA, "context", "activity.json"), {})["days"]
    end = dt.date.fromisoformat(pin)
    vol = {d: v for d, v in vol.items() if d <= pin and v > 0}
    act = {d: a for d, a in act.items() if d <= pin and d in vol}
    v_w = weekly({d: vol[d] for d in act}, "sum")
    t_w = weekly({d: a["txns"] for d, a in act.items()}, "sum")
    a_w = weekly({d: a["active_accounts"] for d, a in act.items()}, "mean")
    p_w = weekly({d: float(a["near_price"]) for d, a in act.items() if float(a["near_price"]) > 0}, "mean")
    mondays = sorted(m for m in v_w if m in t_w and m in a_w and m in p_w and m + dt.timedelta(days=6) <= end)
    return mondays, {"volume": changes(v_w, mondays), "transactions": changes(t_w, mondays),
                     "active accounts": changes(a_w, mondays), "price": changes(p_w, mondays)}


def run(pin, shifts=SHIFTS, seed=SEED):
    mondays, ch = series(pin)
    out = {"first_week": mondays[0].isoformat(), "last_week": mondays[-1].isoformat(), "weeks": len(mondays),
           "changes": len(ch["volume"]), "shifts": shifts, "seed": seed, "tests": {}}
    for target in ("transactions", "active accounts", "price"):
        out["tests"][target] = test(ch["volume"], ch[target], shifts, seed)
    return out


def main():
    ap = argparse.ArgumentParser(description="Does NEAR Intents' volume lead network usage or NEAR's price?")
    ap.add_argument("--shifts", type=int, default=SHIFTS)
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    pin = load(os.path.join(DATA, "pin.json"), {})["pin_day"]
    got = run(pin, args.shifts, args.seed)
    print(f"weekly changes from the week of {got['first_week']} to the week of {got['last_week']}: {got['changes']} changes; "
          f"{got['shifts']} circular shifts, seed {got['seed']}")
    for target, t in got["tests"].items():
        print(f"  volume leading {target:15}  strongest at {t['lead_weeks']} week(s): r = {t['r']:+.2f}, p = {t['p']:.2f}   "
              f"(same week: r = {t['same_week']:+.2f})")
    print("A p-value is the share of shifted series that do at least as well at their best lead. Small means a lead is unlikely to be chance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
