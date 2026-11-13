"""Turn the raw daily reads into the series and the findings. No network: it only reads data/.

  python3 -m pipeline.build

Money stays in integer base units until the last step. A balance that could not be read is None and
is left out of every sum and ratio; it is never treated as 0. Every ratio says how many tokens it covers.
"""
import datetime as dt
import json
import os
from fractions import Fraction

from .pull import DATA, ROOT, load, save

STABLE = {"USDC", "USDT", "DAI", "USD1", "USDT0", "USDE", "PYUSD", "FRAX", "USDS", "GTUSDCP", "USDF", "RLUSD"}
BTC = {"BTC", "NBTC", "WBTC", "CBBTC", "XBTC", "TBTC"}
ETH = {"ETH", "WETH"}
NEAR = {"WNEAR", "NEAR"}
ZEC = {"ZEC"}
GROUPS = ["NEAR", "Stablecoins", "ZEC", "BTC", "ETH", "Other"]

B2B_LAUNCH = "2026-07-13"   # docs.near-intents.org changelog: "Confidential Intents B2B launch"
ALL_PRIVATE = "2026-10-27"  # docs.near-intents.org changelog: "1Click swaps settle confidentially"


def group_of(symbol):
    s = symbol.upper().split("(")[0].strip()
    for name, members in (("NEAR", NEAR), ("Stablecoins", STABLE), ("ZEC", ZEC), ("BTC", BTC), ("ETH", ETH)):
        if s in members:
            return name
    return "Other"


def token_meta():
    snap = load(os.path.join(DATA, "tokens.json"), None)
    meta = {}
    for t in snap["tokens"]:
        price = t.get("price")
        meta[t["assetId"]] = {
            "symbol": t["symbol"], "chain": t.get("blockchain", "?"), "decimals": int(t["decimals"]),
            # the price list gives a float; keep it exact as a fraction of its printed digits
            "price": Fraction(str(price)) if price not in (None, 0, "0") else None,
        }
    return meta, snap["fetched_at"]


def usd(units, m):
    """Exact USD value of integer base units at the pinned price, or None when unpriced."""
    if units is None or m is None or m["price"] is None:
        return None
    return Fraction(int(units), 10 ** m["decimals"]) * m["price"]


def load_days():
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    days = []
    for day in sorted(blocks):
        f = load(os.path.join(DATA, "float", day + ".json"), None)
        if f is None or f["balances"] is None:
            continue
        h = load(os.path.join(DATA, "held", day + ".json"), {"held": {}})
        days.append({"day": day, "height": blocks[day]["height"], "timestamp": blocks[day]["timestamp"],
                     "balances": {k: int(v) for k, v in f["balances"].items()},
                     "held": {k: (int(v) if v is not None else None) for k, v in h["held"].items()}})
    return days


def pick_tracked(days, meta, floor=Fraction(1, 400), since="2026-07-01"):
    """Tokens worth reading a denominator for: at least 0.25% of the float on some day since `since`."""
    keep = set()
    for d in days:
        if d["day"] < since:
            continue
        vals = {t: usd(u, meta.get(t)) for t, u in d["balances"].items()}
        total = sum(v for v in vals.values() if v)
        if not total:
            continue
        keep |= {t for t, v in vals.items() if v and v / total >= floor}
    return sorted(keep)


def day_row(d, meta, tracked):
    bal = d["balances"]
    row = {"day": d["day"], "height": d["height"], "types": sum(1 for u in bal.values() if u > 0)}
    groups = {g: Fraction(0) for g in GROUPS}
    total = Fraction(0)
    unpriced = 0
    for t, u in bal.items():
        if u == 0:
            continue
        v = usd(u, meta.get(t))
        if v is None:
            unpriced += 1
            continue
        total += v
        groups[group_of(meta[t]["symbol"])] += v
    row["wnear"] = bal.get("nep141:wrap.near", 0)
    row["float_usd"] = total
    row["unpriced_types"] = unpriced
    row["groups"] = groups
    # Share of what intents.near holds, in base units per token (no price involved) and value-weighted.
    # Two scopes: the tracked tokens (read every sampled day, so they make the history), and every token
    # with a total read that day (only the pinned day has them all, so it makes the headline).
    tracked_set = set(tracked)
    num = den = num_all = den_all = Fraction(0)
    covered = covered_all = unknown = 0
    shares = {}
    anomalies = []
    g_num = {g: Fraction(0) for g in GROUPS}
    g_den = {g: Fraction(0) for g in GROUPS}
    for t in sorted(d["held"]):
        held = d["held"][t]
        mine = bal.get(t, 0)
        if held is None:
            unknown += 1
            continue
        if held == 0:
            continue
        if mine > held:
            # The ledger credits the treasury with more than the token's contract says intents.near holds.
            # That has no meaning as a share, so it is never turned into a number: the token is left out of
            # this day's share and the reading is listed in data/derived/anomalies.json.
            anomalies.append({"day": d["day"], "height": d["height"], "token": t, "treasury": str(mine), "held": str(held)})
            continue
        if t in tracked_set:
            shares[t] = Fraction(mine, held)
        m = meta.get(t)
        v_held = usd(held, m)
        if v_held is None:
            continue
        v_mine = usd(mine, m)
        num_all += v_mine
        den_all += v_held
        covered_all += 1
        g = group_of(m["symbol"])
        g_num[g] += v_mine
        g_den[g] += v_held
        if t in tracked_set:
            num += v_mine
            den += v_held
            covered += 1
    row["all"] = {"tokens": covered_all, "unknown": unknown, "private_usd": num_all, "held_usd": den_all,
                  "share": (num_all / den_all) if den_all else None,
                  "group_share": {g: (g_num[g] / g_den[g]) if g_den[g] else None for g in GROUPS},
                  "group_held": g_den, "group_private": g_num}
    row["anomalies"] = anomalies
    row["shares"] = shares
    row["share_usd"] = (num / den) if den else None
    row["share_cover"] = {"tokens": covered, "private_usd": num, "held_usd": den}
    return row


def at(rows, day):
    """The row for `day`, or the first row after it."""
    for r in rows:
        if r["day"] >= day:
            return r
    return rows[-1]


def f2(x, nd=2):
    return None if x is None else round(float(x), nd)


def build():
    meta, priced_at = token_meta()
    days = load_days()
    if not days:
        raise SystemExit("no data yet: run `python3 -m pipeline.pull` first")
    tracked = load(os.path.join(DATA, "tracked.json"), None)
    if tracked is None:
        tracked = pick_tracked(days, meta)
        save(os.path.join(DATA, "tracked.json"), tracked)
    rows = [day_row(d, meta, tracked) for d in days]
    last, first = rows[-1], rows[0]
    with_share = [r for r in rows if r["share_usd"] is not None]

    pin_day = load(os.path.join(DATA, "pin.json"), {"pin_day": last["day"]})["pin_day"]
    pin = next((r for r in rows if r["day"] == pin_day), last)
    series = {
        "priced_at": priced_at,
        "pin": {
            "day": pin["day"], "height": pin["height"],
            "share": f2(pin["all"]["share"] * 100, 1) if pin["all"]["share"] is not None else None,
            "private_usd": f2(pin["all"]["private_usd"], 0), "held_usd": f2(pin["all"]["held_usd"], 0),
            "tokens": pin["all"]["tokens"], "unknown": pin["all"]["unknown"],
            "groups": [{"name": g,
                        "share": f2(pin["all"]["group_share"][g] * 100, 1) if pin["all"]["group_share"][g] is not None else None,
                        "held_usd": f2(pin["all"]["group_held"][g], 0), "private_usd": f2(pin["all"]["group_private"][g], 0)}
                       for g in GROUPS],
        },
        "first_day": first["day"], "last_day": last["day"], "last_height": last["height"],
        "events": {"b2b_launch": B2B_LAUNCH, "all_private": ALL_PRIVATE},
        "groups": GROUPS,
        "days": [{
            "day": r["day"], "height": r["height"], "types": r["types"],
            "float_usd": f2(r["float_usd"], 0),
            "groups": [f2(r["groups"][g], 0) for g in GROUPS],
            "share": f2(r["share_usd"] * 100, 2) if r["share_usd"] is not None else None,
            "public_usd": f2(r["share_cover"]["held_usd"] - r["share_cover"]["private_usd"], 0) if r["share_usd"] is not None else None,
            "private_usd": f2(r["share_cover"]["private_usd"], 0) if r["share_usd"] is not None else None,
        } for r in rows],
        "tokens": [{
            "id": t, "symbol": meta[t]["symbol"], "chain": meta[t]["chain"],
            "private_usd": f2(usd(days[-1]["balances"].get(t, 0), meta[t]), 0),
            "held_usd": f2(usd(days[-1]["held"].get(t), meta[t]), 0),
            "share_now": f2(last["shares"][t] * 100, 1) if t in last["shares"] else None,
            "share": [f2(r["shares"][t] * 100, 1) if t in r["shares"] else None for r in rows],
        } for t in tracked if t in meta],
    }
    series["tokens"].sort(key=lambda t: -(t["held_usd"] or 0))
    save(os.path.join(DATA, "derived", "series.json"), series)
    save(os.path.join(DATA, "derived", "anomalies.json"), {
        "what": "Readings where the treasury's balance of a token is larger than the balance the token's own contract "
                "reports for intents.near at the same block. They are left out of the share, never forced to 100%.",
        "readings": [a for r in rows for a in r["anomalies"]]})
    with open(os.path.join(ROOT, "site", "data.js"), "w") as f:
        f.write("window.WATERLINE = " + json.dumps(series, separators=(",", ":")) + ";\n")
    return rows, series, meta, tracked


if __name__ == "__main__":
    rows, series, meta, tracked = build()
    last = series["days"][-1]
    print(f"{len(rows)} days, {series['first_day']} to {series['last_day']} (height {series['last_height']})")
    print(f"float at pinned prices: ${last['float_usd']:,.0f} in {last['types']} token types; tracked tokens: {len(tracked)}")
    print(f"private share of what intents.near holds: {last['share']}%")
