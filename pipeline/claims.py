"""Every number the README and the thesis quote, computed from the raw data as of the pinned day.

  python3 -m pipeline.claims        # writes data/derived/claims.json and the table in README.md

`pipeline.verify` rebuilds this file and fails if a quoted number is missing from the text, so the
prose cannot drift away from the data.
"""
import os
from fractions import Fraction

from .build import ALL_PRIVATE, B2B_LAUNCH, GROUPS, build, group_of, usd
from .pull import DATA, ROOT, load, save


def money(x):
    x = float(x)
    if abs(x) >= 1e9:
        return f"${x / 1e9:.2f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.1f}M"
    return f"${x:,.0f}"


def pct(x, nd=1):
    return f"{float(x) * 100:.{nd}f}%"


def on_or_after(rows, day):
    return next(r for r in rows if r["day"] >= day)


def write_claims():
    rows, series, meta, tracked = build()
    pin = load(os.path.join(DATA, "pin.json"), None)["pin_day"]
    rows = [r for r in rows if r["day"] <= pin]
    last = rows[-1]
    if last["day"] != pin:
        raise SystemExit(f"no data for the pinned day {pin}")
    live = [r for r in rows if r["types"] > 0]
    first = live[0]
    C = []

    def add(cid, shown, what, how, **extra):
        C.append({"id": cid, "shown": shown, "what": what, "how": how, **extra})

    add("C1", money(last["float_usd"]),
        f"Value locked behind the private chain on {pin}, at pinned prices",
        "sum over the treasury's balances in intents.near at the pinned block, times data/tokens.json prices")
    add("C2", f"{last['types']} token types",
        f"Different tokens the private chain held on {pin} ({last['unpriced_types']} of them have no price and are left out of every dollar figure)",
        "count of non-zero balances")
    add("C3", first["day"], "First day the treasury held anything", "first day with a non-zero balance")

    allp = last["all"]
    if allp["share"] is not None:
        add("C4", pct(allp["share"]),
            f"Share of everything intents.near holds that sits behind the private chain on {pin}: every token in "
            f"NEAR Intents' token list that has a price and a readable total ({allp['tokens']} tokens, "
            f"{money(allp['held_usd'])} in total; {allp['unknown']} listed tokens could not be read and are left out)",
            "treasury balance divided by the token contract's balance for intents.near, value-weighted, all tokens")
        for g, label in (("NEAR", "NEAR"), ("Stablecoins", "stablecoins"), ("ZEC", "ZEC"), ("ETH", "ETH"), ("BTC", "bitcoin")):
            if allp["group_share"][g] is not None:
                add("C6-" + g, pct(allp["group_share"][g]),
                    f"The same share for {label} alone on {pin} ({money(allp['group_held'][g])} held in total)",
                    "as C4, one asset group")
    if last["share_usd"] is not None:
        cov = last["share_cover"]
        add("C23", pct(last["share_usd"]),
            f"The same share on {pin} for the {cov['tokens']} tokens tracked through time (the largest by total held)",
            "as C4, tracked tokens only")
        if allp["held_usd"]:
            add("C18", pct(cov["held_usd"] / allp["held_usd"], 0),
                "Part of everything intents.near holds that the tracked tokens cover", "tracked total over all-token total")
        early = next((r for r in rows if r["day"] >= "2026-04-01" and r["share_usd"] is not None), None)
        if early:
            add("C19", pct(early["share_usd"], 0), f"Tracked-token share on {early['day']}, the first reading of April", "as C23")
            add("C20", money(early["share_cover"]["held_usd"] - early["share_cover"]["private_usd"]),
                f"Public side of intents.near on {early['day']}, tracked tokens "
                f"({money(cov['held_usd'] - cov['private_usd'])} on {pin})", "held minus treasury, pinned prices")
            add("C24", money(cov["held_usd"] - cov["private_usd"]), f"Public side of intents.near on {pin}, tracked tokens", "as C20")
        base = next((r for r in rows if B2B_LAUNCH <= r["day"] <= "2026-07-20" and r["share_usd"] is not None), None)
        if base:
            add("C5", pct(base["share_usd"]),
                f"Tracked-token share on {base['day']}, the first reading after the B2B launch of {B2B_LAUNCH}", "as C23")
        before_switch = next((r for r in rows if r["day"] == "2026-10-26" and r["share_usd"] is not None), None)
        if before_switch:
            add("C21", pct(before_switch["share_usd"]), "Tracked-token share on 2026-10-26, the day before the switch", "as C23")

    launch = on_or_after(rows, B2B_LAUNCH)
    add("C7", f"{float(last['float_usd'] / launch['float_usd']):.1f}x",
        f"Growth of the private float since the B2B launch on {B2B_LAUNCH} ({money(launch['float_usd'])} then)",
        "float on the pinned day divided by float at launch, same prices")

    net = [(rows[k]["float_usd"] - rows[k - 1]["float_usd"], rows[k]["day"]) for k in range(1, len(rows))]
    best = sorted(net, reverse=True)[:10]
    add("C8", money(sum(n for n, _ in best)),
        f"Added on the 10 best days out of {len(net)} (the float today is {money(last['float_usd'])})",
        "sum of the ten largest one-day changes in the float, pinned prices")
    add("C17", pct(sum(n for n, _ in best) / last["float_usd"], 0),
        "The ten best days as a share of today's float (the concentration reading)", "C8 divided by C1")
    worst = min(net)
    prev = rows[[r["day"] for r in rows].index(worst[1]) - 1]["day"]
    add("C9", money(-worst[0]), f"Largest one-day fall in the float, between the readings of {prev} and {worst[1]}",
        "smallest one-day change")

    before, after = on_or_after(rows, "2026-10-26"), on_or_after(rows, "2026-10-28")
    add("C10", pct(after["float_usd"] / before["float_usd"] - 1),
        f"Change in the float across the day every 1Click swap moved to the private chain ({before['day']} to {after['day']})",
        "float two days apart, pinned prices")
    switch = on_or_after(rows, ALL_PRIVATE)
    add("C11", money(last["float_usd"] - switch["float_usd"]),
        f"Added to the float between {ALL_PRIVATE} and {pin}", "difference of the two days")

    g = {name: last["groups"][name] for name in GROUPS}
    top = max(g, key=g.get)
    add("C12", f"{top}: {money(g[top])}", f"Largest asset group in the float on {pin}", "group totals at pinned prices")
    add("C13", f"NEAR: {money(g['NEAR'])}", f"NEAR's own token in the float on {pin}", "as C12")
    add("C22", pct(1 - g["NEAR"] / last["float_usd"], 0), f"Part of the float that is not NEAR's own token on {pin}",
        "one minus C13 over C1", must_appear=False)
    wnear = "nep141:wrap.near"
    units = {r["day"]: r["wnear"] for r in rows}
    if "2026-09-15" in units and "2026-09-28" in units:
        add("C14", f"{(units['2026-09-28'] - units['2026-09-15']) / 10**24 / 1e6:.1f}M NEAR",
            "wNEAR that entered the float between the readings of 2026-09-15 and 2026-09-28",
            "difference of two balances, in tokens, no price involved")
        add("C15", f"{(units['2026-09-29'] - units['2026-09-30']) / 10**24 / 1e6:.1f}M NEAR",
            "wNEAR that left the float in one day, between the readings of 2026-09-29 and 2026-09-30", "as C14")
    add("C16", f"{units[pin] / 10**24 / 1e6:.1f}M NEAR", f"wNEAR in the float on {pin}", "balance in tokens", must_appear=False)

    ctx = load(os.path.join(DATA, "context", "defillama.json"), None)
    if ctx:
        def last30(name):
            daily = [v for d, v in ctx["series"][name]["daily"] if d <= pin][-30:]
            return sum(daily)
        vol, fees, rev = last30("volume"), last30("fees"), last30("revenue")
        add("X1", money(vol), "Reported 30-day swap volume (DefiLlama, from a table NEAR uploads to Dune)",
            "sum of the last 30 daily values in data/context/defillama.json", grade="reported")
        add("X2", money(fees), "Reported 30-day gross fees (same kind of source)", "as X1", grade="reported")
        add("X3", money(rev), "30-day revenue that reached NEAR's public revenue wallets (DefiLlama, from chain tables)",
            "as X1", grade="chain, via an indexer")
        if last["all"]["held_usd"]:
            held = last["all"]["held_usd"]
            add("X4", f"{vol / 30 / float(held):.2f}x a day",
                "Reported daily volume divided by everything intents.near holds", "X1 / 30 / total held", grade="reported", must_appear=False)

    sup = load(os.path.join(DATA, "context", "supply.json"), None)
    if sup and ctx and pin in sup["days"] and "2026-10-14" in sup["days"]:
        price = meta[wnear]["price"]
        s1, s0 = int(sup["days"][pin]["total_supply"]), int(sup["days"]["2026-10-14"]["total_supply"])
        per_day = Fraction(s1 - s0, 10**24) / 30
        cap = Fraction(s1, 10**24) * price
        add("V1", money(cap), f"NEAR market value on {pin}: supply in the block header times the pinned price of ${float(price):.2f}",
            "total_supply at the pinned block, times the wNEAR price in data/tokens.json", grade="chain")
        add("V2", f"{float(per_day):,.0f} NEAR a day", "Net new NEAR supply, average of the 30 days to the pinned day",
            "difference of total_supply in two block headers, divided by 30", grade="chain")
        add("V3", money(per_day * price * 365) + " a year", "The same, in dollars at the pinned price", "V2 times price times 365", grade="chain")
        add("V4", pct(Fraction(rev) / 30 / (per_day * price), 0), "Revenue reaching NEAR's wallets as a share of net new supply (30 days)",
            "X3 divided by 30 days of V2 at the pinned price", grade="chain, via an indexer")
        add("V5", f"{float(cap / (Fraction(rev) * Fraction(365, 30))):.0f}x", "NEAR market value divided by that revenue, annualised",
            "V1 divided by (X3 times 365/30)", grade="chain, via an indexer")

    out = {"pin_day": pin, "pin_height": last["height"], "priced_at": series["priced_at"], "claims": C}
    save(os.path.join(DATA, "derived", "claims.json"), out)

    import json
    with open(os.path.join(ROOT, "site", "claims.js"), "w") as f:
        f.write("window.WATERLINE_CLAIMS = " + json.dumps(
            {"pin_day": pin, "pin_height": last["height"], "priced_at": series["priced_at"],
             "by_id": {c["id"]: c for c in C}}, separators=(",", ":")) + ";\n")

    lines = ["| # | Number | What it is |", "| --- | --- | --- |"]
    lines += [f"| {c['id']} | **{c['shown']}** | {c['what']} |" for c in C]
    table = "\n".join(lines)
    path = os.path.join(ROOT, "README.md")
    if os.path.exists(path):
        text = open(path).read()
        a, b = "<!-- claims:start -->", "<!-- claims:end -->"
        if a in text and b in text:
            text = text[:text.index(a) + len(a)] + "\n" + table + "\n" + text[text.index(b):]
            open(path, "w").write(text)
    return out


if __name__ == "__main__":
    out = write_claims()
    for c in out["claims"]:
        print(f"{c['id']:10} {c['shown']:22} {c['what']}")
