"""Every number the README and the thesis quote, computed from the raw data as of the pinned day.

  python3 -m pipeline.claims        # writes data/derived/claims.json and the table in README.md

`pipeline.verify` rebuilds this file and fails if a quoted number is missing from the text, so the
prose cannot drift away from the data.
"""
import os
from fractions import Fraction

from .build import ALL_PRIVATE, B2B_LAUNCH, GROUPS, REWARD_ANNOUNCED, REWARD_TRIGGER, build, group_of, site_js, usd
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


def write_claims(write=True):
    rows, series, meta, tracked = build(write)
    from .build import load_days
    days_raw = load_days()
    pin = load(os.path.join(DATA, "pin.json"), None)["pin_day"]
    rows_all = rows   # every stored day, for the results of tests that are about days after the pinned one
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
    add("C3", first["day"], "First reading (00:00 UTC) on which the treasury held anything; the account was created the day before",
        "first day with a non-zero balance")

    allp = last["all"]
    if allp["share"] is not None:
        add("C4", pct(allp["share"]),
            f"Share of everything intents.near holds that sits behind the private chain on {pin}: every token in "
            f"NEAR Intents' token list that has a price and a balance inside intents.near ({allp['tokens']} tokens, "
            f"{money(allp['held_usd'])} in total; {allp['unknown']} listed ids are not balances inside intents.near "
            f"or could not be read, and are left out)",
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
        f"Added on the 10 best days out of {len(net)} (the float on {pin} is {money(last['float_usd'])})",
        "sum of the ten largest one-day changes in the float, pinned prices")
    add("C17", pct(sum(n for n, _ in best) / last["float_usd"], 0),
        f"The ten best days as a share of the float on {pin} (the concentration reading)", "C8 divided by C1")
    add("C25", money(best[9][0]), "The tenth-largest one-day rise in the float so far (the bar for 'one more lump' in PREREG.md)",
        "tenth of the one-day changes, largest first")
    ups = sum(1 for n, _ in net if n >= 0)
    add("B1", pct(Fraction(ups, len(net)), 0), f"Days on which the float did not fall, out of {len(net)} (the base rate of test E1)", "count of non-negative one-day changes")
    since = [k for k in range(len(rows)) if rows[k]["day"] >= B2B_LAUNCH]
    four = [(rows[k + 4]["float_usd"] >= rows[k]["float_usd"],
             max(rows[j + 1]["float_usd"] - rows[j]["float_usd"] for j in range(k, k + 4)) < best[9][0])
            for k in since if k + 4 < len(rows)]
    add("B2", pct(Fraction(sum(1 for a, _ in four if a), len(four)), 0),
        f"Four-day windows since the B2B launch in which the float did not fall (the base rate of test F1)", "share of four-day windows")
    add("B3", pct(Fraction(sum(1 for _, b in four if b), len(four)), 0),
        "Four-day windows since the B2B launch with no day above the tenth-largest rise (the base rate of test F2)", "share of four-day windows")
    worst = min(net)
    prev = rows[[r["day"] for r in rows].index(worst[1]) - 1]["day"]
    add("C9", money(-worst[0]), f"Largest one-day fall in the float, between the readings of {prev} and {worst[1]}",
        "smallest one-day change")

    before, after = on_or_after(rows, "2026-10-26"), on_or_after(rows, "2026-10-28")
    add("C10", pct(after["float_usd"] / before["float_usd"] - 1),
        f"Change in the float across the day 1Click swaps began to settle on the private chain ({before['day']} to {after['day']})",
        "float two days apart, pinned prices")
    switch = on_or_after(rows, ALL_PRIVATE)
    add("C11", money(last["float_usd"] - switch["float_usd"]),
        f"Added to the float between {ALL_PRIVATE} and {pin}, {len([r for r in rows if r['day'] > ALL_PRIVATE])} days", "difference of the two days")

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
    if REWARD_TRIGGER in units:
        add("C27", f"{units[REWARD_TRIGGER] / 10**24 / 1e6:.1f}M NEAR",
            f"wNEAR in the float on the {REWARD_TRIGGER} reading, the day NEAR announced the reward's snapshot had been triggered",
            "balance in tokens")

    # --- the reward programme: growth before it, during it, and after its snapshot was triggered
    def ex_near(r):
        return r["float_usd"] - r["groups"]["NEAR"]

    def per30(a, b, f):
        n = [r["day"] for r in rows].index(b["day"]) - [r["day"] for r in rows].index(a["day"])
        return (f(b) - f(a)) * 30 / n

    ann, trig = on_or_after(rows, REWARD_ANNOUNCED), on_or_after(rows, REWARD_TRIGGER)
    whole = lambda r: r["float_usd"]
    add("P1", money(per30(first, ann, whole)) + " per 30 days",
        f"Float growth before the reward programme ({first['day']} to {REWARD_ANNOUNCED})", "change in float over the days, times 30")
    add("P2", money(per30(ann, trig, whole)) + " per 30 days",
        f"Float growth while the first reward was open ({REWARD_ANNOUNCED} to {REWARD_TRIGGER})", "as P1")
    add("P3", money(per30(trig, last, whole)) + " per 30 days",
        f"Float growth after the first reward's snapshot was triggered ({REWARD_TRIGGER} to {pin})", "as P1")
    add("P9", money(trig["float_usd"]),
        f"The float on the {REWARD_TRIGGER} reading, the day NEAR announced confidential balances had passed $70M (at that day's prices)",
        "float at the pinned prices")
    px_day = load(os.path.join(DATA, "context", "near_price.json"), None)
    if px_day and REWARD_TRIGGER in units:
        nxt = rows[[r["day"] for r in rows].index(trig["day"]) + 1]
        def at_day_price(r):
            p = Fraction(str(px_day["daily"][r["day"]]))
            return r["float_usd"] + Fraction(units[r["day"]], 10**24) * (p - meta["nep141:wrap.near"]["price"])
        if trig["day"] in px_day["daily"] and nxt["day"] in px_day["daily"] and nxt["day"] in units:
            add("P10", money(at_day_price(trig)),
                f"The float on the {REWARD_TRIGGER} reading with wNEAR at that day's CoinGecko price and every other token at the pinned price "
                f"({money(at_day_price(nxt))} on the next reading): it crosses the $70M of NEAR's announcement between the two",
                "P9 with the wNEAR balance repriced at data/context/near_price.json", grade="chain, one quoted price")
    pool = Fraction(333_333) * Fraction("3.33")
    add("P11", money(pool),
        "The first reward pool at its conversion price: 333,333 locked tokens that convert 1:1 to NEAR at $3.33 (NEAR's blog post, quoted). "
        f"No wallet receives more than 2% of it: {money(pool * Fraction(2, 100))}", "333,333 times 3.33", grade="quoted")
    if px_day and "2026-09-15" in px_day["daily"] and "2026-09-28" in px_day["daily"]:
        p0, p1 = Fraction(str(px_day["daily"]["2026-09-15"])), Fraction(str(px_day["daily"]["2026-09-28"]))
        add("P12", f"{float(p1 / p0):.1f}x",
            f"NEAR's price on CoinGecko over the days of the September inflow: ${float(p0):.2f} on 2026-09-15, ${float(p1):.2f} on 2026-09-28",
            "data/context/near_price.json", grade="quoted")
    add("P4", money(ex_near(last)), f"Float without NEAR's own token on {pin} ({money(ex_near(trig))} on {REWARD_TRIGGER})",
        "float minus the NEAR group, pinned prices")
    add("P5", money(ex_near(trig)), f"Float without NEAR's own token on {REWARD_TRIGGER}", "as P4")
    ex_net = [ex_near(rows[k]) - ex_near(rows[k - 1]) for k in range(1, len(rows))]
    add("P6", money(-min(ex_net)), "Largest one-day fall in the float without NEAR's own token", "smallest one-day change of P4's series")
    if "2026-09-15" in units and "2026-09-28" in units:
        came, left = units["2026-09-28"] - units["2026-09-15"], units["2026-09-28"] - units[pin]
        add("P7", pct(Fraction(left, came), 0),
            "Part of the wNEAR that arrived between 2026-09-15 and 2026-09-28 that had left again by the pinned day",
            "wNEAR balance at the peak minus today, over the inflow")

    # --- readings where the ledger credited the treasury with more of a token than intents.near held
    shorts = [a for r in rows for a in r["anomalies"]]
    if shorts:
        worst_s = max(shorts, key=lambda a: a["short_usd"] or 0)
        m = meta[worst_s["token"]]
        add("S1", f"{len(shorts)} readings",
            "Readings where the treasury was credited with more of a token than intents.near held: "
            + ", ".join(sorted(a["day"] for a in shorts)), "treasury balance above the token contract's balance for intents.near")
        add("S2", money(worst_s["short_usd"]),
            f"Largest such shortfall, on the {worst_s['day']} reading: {m['symbol']} on {m['chain']}, "
            f"{int(worst_s['held']) // 10**m['decimals']:,} held against {int(worst_s['treasury']) // 10**m['decimals']:,} credited",
            "treasury minus held, at the pinned price")
        add("S3", pct(Fraction(str(worst_s["short_share"])) / 100, 0),
            "Part of the treasury's credit in that token that had nothing behind it on that reading", "shortfall over treasury credit")
        first_s = min(shorts, key=lambda a: a["day"])
        add("S5", pct(Fraction(str(first_s["short_share"])) / 100, 0),
            f"Part of the treasury's credit in that token with nothing behind it on the earlier reading, {first_s['day']}",
            "shortfall over treasury credit")
        days_all = [r["day"] for r in rows]
        after = days_all[days_all.index(max(a["day"] for a in shorts)) + 1]
        add("S4", after, "First reading on which that token was fully held again", "next reading with treasury at or below held")

    # --- quoted figures. The last day before the pin is left out: its fee figure was still incomplete when fetched.
    import datetime as _dt
    ctx = load(os.path.join(DATA, "context", "defillama.json"), None)
    px = load(os.path.join(DATA, "context", "near_price.json"), None)
    sup = load(os.path.join(DATA, "context", "supply.json"), None)
    if ctx and px and sup:
        end = _dt.date.fromisoformat(pin) - _dt.timedelta(days=2)
        win = [(end - _dt.timedelta(days=n)).isoformat() for n in range(29, -1, -1)]
        prev = [(end - _dt.timedelta(days=n)).isoformat() for n in range(59, 29, -1)]
        S = {k: dict(ctx["series"][k]["daily"]) for k in ("volume", "fees", "revenue")}

        def total(name, days_):
            return sum(Fraction(str(S[name][d])) for d in days_)
        vol, fees, rev = total("volume", win), total("fees", win), total("revenue", win)
        span = f"30 days to {win[-1]}"
        add("X1", money(vol), f"Reported swap volume, {span} (DefiLlama, from a table uploaded to Dune under the near team's name)",
            "sum of 30 daily values in data/context/defillama.json", grade="reported")
        add("X2", money(fees), f"Reported gross fees, {span} (same kind of source)", "as X1", grade="reported")
        add("X3", money(rev), f"Revenue that reached NEAR's public revenue wallets, {span} (DefiLlama, from chain tables, in dollars at each day's price)",
            "as X1", grade="chain, via an indexer")
        for cid, name, label in (("T1", "volume", "reported volume"), ("T2", "fees", "reported fees"), ("T3", "revenue", "revenue reaching NEAR's wallets")):
            change = total(name, win) / total(name, prev) - 1
            add(cid, ("+" if change >= 0 else "") + pct(change, 0), f"Change in {label}, {span} against the 30 days before", "ratio of two 30-day sums")
        if last["all"]["held_usd"]:
            add("X4", f"{float(vol / 30 / last['all']['held_usd']):.2f}x a day",
                "Reported daily volume divided by everything intents.near holds", "X1 / 30 / total held", grade="reported", must_appear=False)

        # like for like: NEAR against NEAR. DefiLlama's revenue is NEAR valued at each day's price, so each day is
        # turned back into NEAR at that day's price before it is compared with the NEAR added to the supply.
        price = {d: Fraction(str(v)) for d, v in px["daily"].items()}
        rev_near = sum(Fraction(str(S["revenue"][d])) / price[d] for d in win)
        s1 = int(sup["days"][pin]["total_supply"])
        s0_day = (_dt.date.fromisoformat(pin) - _dt.timedelta(days=30)).isoformat()
        per_day = Fraction(s1 - int(sup["days"][s0_day]["total_supply"]), 10**24) / 30
        near_usd = price[pin]
        cap = Fraction(s1, 10**24) * near_usd
        add("V1", money(cap), f"Value of NEAR's total supply on {pin}: supply in the block header times CoinGecko's price of ${float(near_usd):.2f}",
            "total_supply at the pinned block, times the price in data/context/near_price.json", grade="chain, one quoted price")
        add("V2", f"{float(per_day):,.0f} NEAR a day", "Net new NEAR supply, average of the 30 days to the pinned day",
            "difference of total_supply in two block headers, divided by 30", grade="chain")
        add("V3", money(per_day * near_usd * 365) + " a year", "The same, in dollars at that price", "V2 times price times 365", grade="chain, one quoted price")
        add("V4", pct(rev_near / (per_day * 30), 0), f"Revenue reaching NEAR's wallets as a share of net new supply, NEAR against NEAR, {span}",
            "each day's quoted revenue divided by that day's price, summed, over 30 days of V2", grade="chain, via an indexer")
        add("V5", f"{float(Fraction(s1, 10**24) / (rev_near * Fraction(365, 30))):.0f}x", "NEAR's total supply divided by that revenue, annualised, NEAR against NEAR",
            "supply over (30-day revenue in NEAR times 365/30)", grade="chain, via an indexer")
        # the same three figures with both sides in dollars: revenue at each day's price, supply at the pinned price
        usd_share = rev / (per_day * 30 * near_usd)
        add("V6", pct(usd_share, 0), "V4 with both sides in dollars: revenue as DefiLlama counts it, at each day's price, against net new supply at the "
            f"price of the pinned block. It is higher than V4 because NEAR averaged ${float(rev / rev_near):.2f} over those 30 days and was ${float(near_usd):.2f} on the pinned day",
            "X3 over (30 days of V2 times the pinned price)", grade="chain, via an indexer")
        add("V7", f"{float(cap / (rev * Fraction(365, 30))):.0f}x", "V5 on the same dollar basis", "V1 over (X3 times 365/30)", grade="chain, via an indexer")
        add("V8", f"{float(1 / usd_share):.1f}x", "M2 on the same dollar basis", "one over V6", grade="chain, via an indexer")
        need = (per_day * 30) / rev_near
        add("M1", f"{float(rev / vol * 10000):.1f} basis points", f"Revenue reaching NEAR's wallets per dollar of reported volume, {span}", "X3 over X1", grade="reported")
        # HSP-029's issuance target; M2 and H1 are added below, on the basis the rating uses
        target = Fraction(16, 1000)
        # scale: the money beyond the audit, and the one hole that was measured, against the revenue that funds the buyback
        month = rev  # 30 days of revenue reaching NEAR's wallets, in dollars at each day's price
        year = month * Fraction(365, 30)
        add("Q1", f"{float(last['float_usd'] / year):.1f} years",
            f"The float on {pin} as years of the revenue that reaches NEAR's wallets, at the rate of the {span}",
            "C1 over (X3 times 365/30)", grade="chain, via an indexer")
        add("Q2", pct(year / last["float_usd"], 0),
            "Part of the float whose loss would equal a full year of that revenue", "X3 times 365/30, over C1", grade="chain, via an indexer")
        ex0 = (build.last.get("audit") or {}).get("exploit")
        if ex0:
            m0 = meta[ex0["token"]]
            peak_usd = max(Fraction(int(st["credited"]) - int(st["held"]), 10 ** m0["decimals"]) for st in ex0["steps"]) * m0["price"]
            add("Q3", f"{float(peak_usd / month):.1f} months",
                "The October hole at its largest as months of that revenue", "A10 over X3", grade="chain, via an indexer")
        # --- revenue measured on chain: NEAR and wNEAR received by the three wallets (pipeline/revenue.py). Our day D is the
        # 24 hours before the reading at 00:00 on D; DefiLlama's day D is the calendar day, so its window is one day earlier.
        from .revenue import window as rev_window
        rv = load(os.path.join(DATA, "context", "revenue.json"), None)
        shift = lambda d, n=1: (_dt.date.fromisoformat(d) + _dt.timedelta(days=n)).isoformat()   # noqa: E731
        coverage, coverage_label = rev_near / (per_day * 30), "V4"
        rev30 = rev_near                                         # 30 days of revenue in NEAR: DefiLlama's, until the chain's is read
        sday = lambda d: int(sup["days"][d]["total_supply"])   # noqa: E731
        win_b = (shift(pin, -29), pin)                            # the 30 readings to the pinned one
        win_a = (shift(pin, -59), shift(pin, -30))                # the 30 before
        rb = rev_window(rv, *win_b) if rv else None
        ra = rev_window(rv, *win_a) if rv else None
        rx = rev_window(rv, shift(win[0]), shift(win[-1])) if rv else None
        if rb and shift(pin, -30) in sup["days"] and shift(pin, -60) in sup["days"]:
            got_b = Fraction(rb["received"], 10**24)
            new_b = Fraction(sday(pin) - sday(shift(pin, -30)), 10**24)
            add("U1", f"{float(got_b):,.0f} NEAR",
                f"NEAR and wNEAR received by the three revenue wallets in the 30 days to the reading of {pin}, counted from the chain: "
                f"transfers listed by a public index, and every wallet's native NEAR in minus out "
                + ("equal, to the last unit, to the change in its balance read at each day's block" if rb["adds_up"] else "NOT equal to the change in its balance"),
                "pipeline/revenue.py; data/context/revenue.json", grade="chain")
            add("U2", f"{float(got_b / 30):,.0f} NEAR a day", "The same, a day", "U1 over 30", grade="chain")
            coverage, coverage_label, rev30 = got_b / new_b, "U4", got_b
            add("U4", pct(coverage, 0), f"Revenue reaching NEAR's wallets as a share of net new supply, both read from the chain, in the 30 days to the reading of {pin}: "
                "U1 over the change in total supply between two block headers 30 days apart. The rating in THESIS.md section 5 uses it", "U1 over 30 days of supply growth", grade="chain")
            if ra and shift(pin, -60) in sup["days"]:
                got_a = Fraction(ra["received"], 10**24)
                new_a = Fraction(sday(shift(pin, -30)) - sday(shift(pin, -60)), 10**24)
                add("U5", pct(got_a / new_a, 0), f"The same coverage in the 30 days before, to the reading of {shift(pin, -30)} ({float(got_a):,.0f} NEAR received)",
                    "as U4, one window earlier", grade="chain")
                ch = got_b / got_a - 1
                add("U6", ("+" if ch >= 0 else "") + pct(ch, 0), "Change in the NEAR reaching the revenue wallets, the latest 30 days against the 30 before, read from the chain",
                    "U1 over the window before, minus one", grade="chain")
                cov_a = got_a / new_a
                # --- one step back: who paid those wallets on intents.near's ledger, and where their wNEAR came from (pipeline/revenue_source.py)
                rsrc = load(os.path.join(DATA, "context", "revenue_source.json"), None)
                if rsrc and rsrc.get("complete"):
                    from .revenue_source import counted_by_revenue, summarise as src_summary
                    blk = load(os.path.join(DATA, "blocks.json"), {})
                    sb = src_summary(rsrc, blk, *win_b)
                    if sb:
                        adds = sb["paid"] == counted_by_revenue(rv, sb["first"], sb["last"])
                        wal = sb["by_wallet"]
                        fe = wal.get("fefundsadmin.sputnik-dao.near")
                        add("U7", pct(sb["treasury"] / rb["received"], 0),
                            f"Share of U1 that arrived through the private chain's treasury. Each payment into the three wallets from intents.near is a "
                            f"withdrawal signed by an account on its ledger; that account's wNEAR inflows in the ten minutes (or, failing that, six hours) "
                            f"before it paid fund its payments oldest first, each inflow used once and never beyond its amount, and the part funded by "
                            f"transfers from the treasury counts here. {sb['payments']:,} payments by {sb['payers']:,} accounts, each looked up; the payments "
                            + ("add up exactly to" if adds else "do NOT add up to") + " the transfers from intents.near that U1 counts. This is the route the "
                            "money took, not where it was earned. The 30 days before are not traced",
                            "pipeline/revenue_source.py; data/context/revenue_source.json", grade="index, sampled against the chain")
                        add("U10", pct(sb["untraced"] / rb["received"], 0),
                            f"Share of U1 that the payers' inflows before each payment do not explain: paid from balances the payers already held, whose "
                            f"source the windows read do not show ({sb['untraced_payments']:,} payments, mostly by accounts that pay many times)",
                            "as U7", grade="index")
                        if sb["before_switch"]["paid"] and sb["from_switch"]["paid"]:
                            add("U11", pct(Fraction(sb["from_switch"]["treasury"], sb["from_switch"]["paid"]), 0),
                                "Share of the payments from intents.near made on or after 27 October 2026, the day 1Click swaps began to settle privately, "
                                "that arrived through the treasury", "as U7, for payments from that day", grade="index")
                            add("U12", pct(Fraction(sb["before_switch"]["treasury"], sb["before_switch"]["paid"]), 0),
                                "The same for the payments in the window made before 27 October 2026", "as U7, for payments before that day", grade="index")
                        if fe and fe["paid"]:
                            add("U13", pct(Fraction(fe["treasury"], fe["paid"]), 0), "Share of the payments to fefundsadmin.sputnik-dao.near that arrived "
                                "through the treasury, in the same window", "as U7, for one wallet", grade="index")
                        add("U9", pct(Fraction(sb["paid"], rb["received"]), 1),
                            "Share of U1 that came from intents.near at all, by any payer; the rest was sent to the wallets from outside it",
                            "payments from intents.near over U1", grade="index")
            else:
                cov_a = None
        if rx:
            got_x = Fraction(rx["received"], 10**24)
            add("U3", pct(got_x / rev_near, 1),
                f"NEAR the chain shows reaching the wallets over the 30 days of X3, as a share of DefiLlama's revenue for those days turned into NEAR "
                f"at each day's price ({float(got_x):,.0f} NEAR against {float(rev_near):,.0f} NEAR): how far the quoted figure agrees with the chain",
                "pipeline/revenue.py against data/context/defillama.json", grade="chain")
        # the multiples on the same basis as the rating: the chain's revenue when it was read (U4), DefiLlama's otherwise (V4)
        need = 1 / coverage
        need_target = (Fraction(s1, 10**24) * target * Fraction(30, 365)) / rev30
        on_chain = coverage_label == "U4"
        add("M2", f"{float(need):.1f}x", "How many times revenue would have to grow for buybacks to match net new supply", f"one over {coverage_label}",
            grade="chain" if on_chain else "chain, via an indexer")
        add("H1", f"{float(need_target):.1f}x", "How many times revenue would have to grow if net new supply ran at the 1.6% a year that HSP-029 would bring about",
            f"supply times 1.6%, over a year, against 30 days of revenue in NEAR ({'U1' if on_chain else 'DefiLlama'})", grade="chain" if on_chain else "chain, via an indexer")
        # --- the rating, from the rule in THESIS.md section 5: computed, not typed
        last_audit = (build.last.get("audit") or {}).get("history") or []
        audited = [d for d in last_audit if d["day"] <= pin]
        books_whole = bool(audited) and audited[-1]["counts"]["short"] == 0
        if "U4" in [c["id"] for c in C] and "U5" in [c["id"] for c in C]:
            lo, hi = Fraction(10, 100), Fraction(25, 100)
            if not books_whole or (coverage < lo and cov_a < lo):
                rating = "Exit"
            elif (coverage >= hi and cov_a >= hi) or D1_MET:
                rating = "Add"
            else:
                rating = "Hold"
            add("RT", rating, f"The rating the rule in THESIS.md section 5 gives on {pin}: the public books are "
                + ("whole" if books_whole else "short") + f" on the latest reading; coverage is {pct(coverage, 0)} and {pct(cov_a, 0)} in the last two 30-day windows; "
                "NEAR has " + ("" if D1_MET else "not ") + "published the private chain's totals", "the rule, applied by pipeline/claims.py", grade="rule")
        # --- what has to be true by 2029 and 2031: coverage of net new supply if revenue, counted in NEAR, grows at g a year
        i_now = per_day * 365 / Fraction(s1, 10**24)
        sc = scenarios(coverage, i_now, pin)
        scenario_block = sc["table"]
        add("Z1", pct(sc["need"][("as now", "2029")], 0) + " a year",
            "How fast the revenue reaching NEAR's wallets, counted in NEAR, must grow for buybacks to match net new supply by the end of 2029, "
            f"with issuance as it is ({pct(i_now, 2)} of supply a year)", f"(1 + issuance) times (1 / {coverage_label}) to the power 1/years, minus 1", grade="model")
        add("Z2", pct(sc["need"][("at 1.6%", "2029")], 0) + " a year",
            "The same, if net new supply runs at 1.6% of supply by then, as HSP-029 would bring about", "as Z1", grade="model")
        add("Z3", pct(sc["need"][("as now", "2031")], 0) + " a year", "The same by the end of 2031, issuance as it is", "as Z1", grade="model")
        add("Z4", pct(sc["need"][("at 1.6%", "2031")], 0) + " a year", "The same by the end of 2031, at 1.6%", "as Z1", grade="model")
        flat = next(r for r in sc["rows"] if r["g"] == 0)
        add("Z5", pct(flat[("as now", "2029")], 0), "Coverage at the end of 2029 if revenue in NEAR stays where it is and issuance does too", "as Z1", grade="model")
        add("Z6", pct(flat[("at 1.6%", "2029")], 0), "Coverage at the end of 2029 if revenue in NEAR stays where it is and issuance falls to 1.6%", "as Z1", grade="model")
        # --- can a growth rate be read from the revenue in NEAR? How far the fitted rate moves with its start (pipeline/growth.py)
        if os.path.exists(os.path.join(DATA, "context", "activity.json")):
            from .growth import summary
            gs = summary(pin)
            spct = lambda x: f"{round(x * 100):+,d}%"   # noqa: E731
            add("GR1", f"{spct(gs['lowest'][2])} to {spct(gs['highest'][2])} a year",
                f"Growth of the revenue reaching NEAR's wallets, counted in NEAR at each day's price, from a straight line through the logarithm of "
                f"the weekly totals, fitted from every start week from {gs['first_week']} that leaves at least {gs['min_weeks']} weeks to the week of "
                f"{gs['last_week']}: lowest from the week of {gs['lowest'][0]}, highest from the week of {gs['highest'][0]}. "
                f"A rate that moves this far with its start is not used",
                "python3 -m pipeline.growth; DefiLlama's daily revenue over NearBlocks' daily price", grade="model, on quoted revenue")
            add("GR2", f"{gs['first_per_day']:,.0f} NEAR a day",
                f"Revenue reaching NEAR's wallets in the first complete week of the buyback (week of {gs['first_week']}), counted in NEAR at each "
                f"day's price, per day", "weekly total over 7", grade="quoted revenue, NearBlocks price")
            add("GR3", f"{gs['last_per_day']:,.0f} NEAR a day", f"The same for the latest complete week (week of {gs['last_week']})",
                "as GR2", grade="quoted revenue, NearBlocks price")
            add("GR4", f"{round(gs['from_first'][2] * 100)}% a year",
                f"The same line fitted from the first week only, over {gs['from_first'][1]} weeks: the figure pull request 22 reported, withdrawn "
                f"because the start chosen decides it", "as GR1", grade="model, withdrawn")
        add("M3", f"${float(vol * Fraction(365, 30) * need) / 1e9:.0f}B a year", "Reported volume that would take at today's rate of revenue per dollar of volume",
            "annualised X1 times M2", grade="reported")
        # --- a holder's view: what staking pays against what new supply takes (data/context/staking.json, read at the pinned block)
        stk = load(os.path.join(DATA, "context", "staking.json"), None)
        if stk and stk.get("day") == pin and stk["protocol_reward_rate"][0] == 0:
            stake = Fraction(int(stk["total_stake"]), 10**24)
            supply_now = Fraction(s1, 10**24)
            y = per_day * 365 / stake                                   # every new NEAR is paid to stake when the protocol keeps none
            y_low = target * supply_now / stake                         # the same at HSP-029's 1.6%, with the stake unchanged
            yrs = Fraction((_dt.date(2030, 1, 1) - _dt.date.fromisoformat(pin)).days * 100, 36525)
            signed = lambda x: ("+" if x >= 0 else "") + pct(x, 1)     # noqa: E731
            staker, idle = (1 + y) / (1 + i_now) - 1, 1 / (1 + i_now) - 1
            add("ST1", pct(stake / supply_now, 1), f"Share of NEAR's total supply staked with the {stk['validators']} validators of the epoch of the pinned "
                f"block ({float(stake):,.0f} NEAR)", "validators RPC by epoch, over the pinned block's total supply", grade="chain")
            add("ST2", pct(y, 1) + " a year", "What stake earns before the validator's fee: net new supply over a year, over the total stake. The protocol "
                "keeps none of the new supply (protocol_reward_rate 0 at the pinned block), so all of it is paid to stake; net new supply is what is "
                "minted less the fees burned, so this slightly understates it", "V2 times 365, over the stake in ST1", grade="chain")
            add("ST3", signed(staker) + " a year", "Change in a staker's share of NEAR's total supply over a year, before the validator's fee",
                "(1 + ST2) / (1 + issuance) - 1", grade="chain")
            add("ST4", signed(idle) + " a year", "Change in the share of a holder who does not stake: new supply goes to stakers", "1 / (1 + issuance) - 1", grade="chain")
            to_2030 = lambda r: (1 + float(r)) ** float(yrs) - 1   # noqa: E731
            add("ST5", f"{signed(to_2030(staker))} against {signed(to_2030(idle))}",
                "Change in a holder's share of total supply from the pinned day to the end of 2029, staked (before the validator's fee) against not "
                "staked, with issuance and stake as they are now", "ST3 and ST4 compounded to 2030-01-01", grade="model")
            add("ST6", pct(y_low, 1) + " a year", "What stake would earn before the validator's fee if new supply ran at 1.6% of supply, as HSP-029 would "
                "bring about, with the stake as it is", "1.6% of supply over the stake in ST1", grade="model")

    peak = max(rows, key=lambda r: r["float_usd"])
    add("T4", money(peak["float_usd"]), f"Highest the float has been, on the {peak['day']} reading", "largest daily value, pinned prices")
    add("P8", f"{float(ex_near(last) / ex_near(launch)):.1f}x", f"Growth of the float without NEAR's own token since the B2B launch ({money(ex_near(launch))} then)", "as C7, without the NEAR group")

    cus = load(os.path.join(DATA, "context", "custody.json"), None)
    if cus and cus.get("account_access_keys"):
        unused = [k for k in cus["account_access_keys"] if k["nonce"] % 1_000_000 == 0]
        add("K2", f"{len(unused)} of {len(cus['account_access_keys'])}",
            "Access keys of the treasury account on NEAR itself that have never signed a transaction (the nonce is still the value set at creation)",
            "view_access_key_list(treasury) at the pinned block", grade="chain", must_appear=False)
    if cus:
        add("K1", f"{len(cus['keys_registered_in_intents_near'])} key",
            "Keys registered inside intents.near for the treasury account at the pinned block "
            + ("(the account has contract code)" if cus["account_has_contract_code"] else "(the account itself has no contract code)"),
            "intents.near.public_keys_of(treasury) and view_account(treasury)", grade="chain")

    # --- the audit: what intents.near has credited in total against what each token's contract says it holds
    aud = build.last.get("audit") or {}
    if aud.get("pin") and aud.get("history"):
        # like every quoted number, the audit's counts stop at the pinned day: a reading added later must not change the text
        ap, hist = aud["pin"], [d for d in aud["history"] if d["day"] <= pin]
        listed = {t["assetId"] for t in load(os.path.join(DATA, "tokens.json"), {"tokens": []})["tokens"]}
        pin_held = load(os.path.join(DATA, "held", pin + ".json"), {"held": {}})["held"]
        unlisted = sum(1 for t, v in pin_held.items() if v is not None and t not in listed)
        add("A1", f"{ap['checked']} tokens",
            f"Tokens audited on {pin}: every token with a balance to read that was in NEAR Intents' list when the day's totals were taken, "
            f"and {unlisted} unlisted ones the treasury holds. For each, the credited total (intents.near.mt_batch_supply) is set "
            f"against what the token's own contract says intents.near holds. {ap['counts']['equal']} are equal to the last unit, "
            f"{ap['counts']['surplus']} hold more than is credited ({money(ap['surplus_usd'])} in all), {ap['counts']['short']} are short",
            "pipeline/audit.py: mt_batch_supply on intents.near, ft_balance_of or mt_balance_of on each token contract, same block", grade="chain")
        add("A2", money(ap["held_usd"]), f"Value of the tokens audited on {pin}, at pinned prices", "sum of held, priced tokens", grade="chain")
        token_days = sum(d["checked"] for d in hist)
        short_days = [d for d in hist if d["counts"]["short"]]
        thin = sum(1 for d in hist if d["checked"] < 10)
        add("A3", f"{token_days:,} checks",
            f"Token-by-token checks of the {len(tracked)} tracked tokens on {len(hist)} stored readings from {hist[0]['day']} to {hist[-1]['day']}. "
            + (f"{len(hist) - thin} readings cover every tracked token that had a balance; {thin} readings around the October exploit cover only the token involved"
               if thin else "Every reading covers every tracked token that had a balance that day"),
            "one audit per stored day", grade="chain")
        shorts = [(d["day"], r) for d in short_days for r in d["not_equal"] if r["status"] == "short"]
        tokens_short = sorted({r["token"] for _, r in shorts})
        add("A4", f"{len(shorts)} of them short",
            "Checks in which more was credited than held: " + ", ".join(f"{day} ({money(r['usd'])})" for day, r in shorts)
            + (f", all one token: {meta[tokens_short[0]]['symbol']} on {meta[tokens_short[0]]['chain']}" if len(tokens_short) == 1 else ""),
            "credited above held", grade="chain")
        lows_ = aud.get("new_lows") or []
        same_days = sorted({d for d, _, _ in lows_}) == sorted({d for d, _ in shorts})
        add("A15", f"{len(lows_)} new lows",
            f"Checks, out of those {token_days:,}, on which a token's held-minus-credited fell below every earlier reading of that token"
            + (": the same readings as A4 and no others" if same_days else ": " + ", ".join(sorted({d for d, _, _ in lows_})))
            + ". This test also sees a hole smaller than the surplus a token already carries",
            "pipeline/audit.py, new_lows: the running minimum of held minus credited, per token", grade="chain")
        if shorts:
            day, worst_r = max(shorts, key=lambda x: x[1]["usd"] or 0)
            m = meta[worst_r["token"]]
            add("A5", money(worst_r["usd"]),
                f"Largest hole on a daily reading, {day}: {int(worst_r['held']) // 10**m['decimals']:,} held against "
                f"{int(worst_r['credited']) // 10**m['decimals']:,} credited to everyone", "credited minus held, at the pinned price", grade="chain")
            add("A6", pct(Fraction(int(worst_r["hole"]), int(worst_r["credited"])), 0),
                "Part of everything credited in that token that had nothing behind it on that reading", "hole over credited", grade="chain")
            owed = next((int(d["balances"].get(worst_r["token"], 0)) for d in days_raw if d["day"] == day), None)
            if owed is not None:
                add("A7", pct(Fraction(owed, int(worst_r["credited"])), 0),
                    "Part of that token's credit that belonged to the private chain's treasury on that reading", "treasury balance over credited", grade="chain")
    ex = aud.get("exploit")
    if ex:
        m = meta[ex["token"]]
        unit = 10 ** m["decimals"]
        hole = lambda st: int(st["credited"]) - int(st["held"])   # noqa: E731
        stamp = lambda text: int(_dt2.datetime.strptime(text + " +0000", "%Y-%m-%d %H:%M:%S %z").timestamp())   # noqa: E731
        import datetime as _dt2
        steps_ = ex["steps"]
        first = next(st for st in steps_ if hole(st) > 0)
        peak = max(steps_, key=hole)
        whole = next((st for st in steps_ if st["height"] > peak["height"] and hole(st) <= 0), None)
        paid = stamp(ex["quoted"]["first_payout_utc"])
        lead = paid - first["timestamp"] // 10**9
        before = [st for st in steps_ if st["timestamp"] // 10**9 < paid][-1]
        add("A8", f"{lead // 3600} hours {lead % 3600 // 60} minutes",
            f"How long before the first payout CertiK reports ({ex['quoted']['first_payout_utc']} UTC) the hole was already in the public books: "
            f"it opens at block {first['height']}, {first['time_utc']} UTC, at {hole(first) // unit:,} {m['symbol'].split('(')[0]}",
            "pipeline/audit.py --steps: halve the days between two readings down to each block where credited minus held changed; data/context/exploit.json",
            grade="chain, one quoted time")
        add("A9", money(Fraction(hole(before), unit) * m["price"]),
            f"The hole in the public books at {before['time_utc']} UTC, the last change before that first payout", "credited minus held, at the pinned price", grade="chain")
        add("A10", money(Fraction(hole(peak), unit) * m["price"]), f"The hole at its largest, {peak['time_utc']} UTC", "as A9", grade="chain")
        if whole:
            shut = whole["timestamp"] // 10**9 - first["timestamp"] // 10**9
            up = stamp(ex["quoted"]["upgrade_utc"]) - whole["timestamp"] // 10**9
            add("A11", f"{shut // 3600} hours",
                f"How long the books stayed short: whole again at block {whole['height']}, {whole['time_utc']} UTC, "
                + (f"{up // 60} minutes before" if up >= 0 else f"{-up // 60} minutes after")
                + f" the contract upgrade CertiK records ({ex['quoted']['upgrade_utc']} UTC)"
                + (". The credited total did not fall while the hole closed, so the tokens came back"
                   if int(whole["credited"]) >= max(int(st["credited"]) for st in steps_ if peak["height"] < st["height"] < whole["height"] and st["timestamp"] > whole["timestamp"] - 4 * 3600 * 10**9) else
                   ". Part of the hole closed because credit was removed, not because tokens came back"),
                "first block after the peak with held at or above credited", grade="chain, one quoted time")

    if ex:
        def ago(seconds):
            h, m_ = seconds // 3600, seconds % 3600 // 60
            return (f"{h} hour{'s' if h != 1 else ''} " if h else "") + f"{m_} minute{'s' if m_ != 1 else ''}"
        rungs = []
        for level in (100, 1_000, 10_000, 100_000, 1_000_000):
            hit = next((st for st in steps_ if hole(st) >= level * unit and st["timestamp"] // 10**9 < paid), None)
            if hit:
                rungs.append((level, paid - hit["timestamp"] // 10**9))
        small = next((st for st in steps_ if hole(st) >= 3_000 * unit), None)
        if small and rungs:
            quiet = small["timestamp"] // 10**9 - first["timestamp"] // 10**9
            add("A12", f"{quiet // 3600} hours",
                f"Of those {lead // 3600} hours {lead % 3600 // 60} minutes, the time the hole stayed under $3,000 ({ago(quiet)}). "
                "How long before the first payout each size was first reached: " + ", ".join(f"{money(level)} at {ago(t)}" for level, t in rungs),
                "first step at or above each size, against the quoted payout time", grade="chain, one quoted time")
            add("A13", ago(rungs[-1][1]), f"How long before the first payout the hole first passed {money(rungs[-1][0])}", "as A12", grade="chain, one quoted time")
            ten_k = next((t for level, t in rungs if level == 10_000), None)
            if ten_k is not None:
                add("A16", ago(ten_k), "How long before the first payout the hole first passed $10,000", "as A12", grade="chain, one quoted time")
    late = load(os.path.join(DATA, "context", "late_tokens.json"), None)
    if late and last["all"]["share"] is not None:
        extra = sum((usd(int(v["held"]), meta[t]) or 0) for t, v in late["tokens"].items() if v["held"] is not None and t in meta)
        extra_private = sum((usd(int(v["treasury"]), meta[t]) or 0) for t, v in late["tokens"].items() if v["treasury"] is not None and t in meta)
        whole_late = all(v["held"] is not None and v["credited"] is not None and int(v["credited"]) <= int(v["held"]) for v in late["tokens"].values())
        add("A14", pct((last["all"]["private_usd"] + extra_private) / (last["all"]["held_usd"] + extra)),
            f"What C4 would be with the {len(late['tokens'])} tokens that joined NEAR Intents' list later on the pinned day. They were read once, at the "
            f"pinned block: {money(extra)} held, " + ("none short" if whole_late else "not all whole") + f", {money(extra_private)} of it in the treasury. "
            "They are left out of every pinned figure", "data/context/late_tokens.json added to both sides of C4", grade="chain")

    # --- results of the dated tests whose reading exists. They are about days after the pinned one, and never change again
    from .score import FIRST_CHECK, tests as float_tests
    from .score_audit import tests as audit_tests
    from . import audit as _audit2
    all_rows = rows_all
    after = next((r for r in all_rows if r["day"] == FIRST_CHECK), None)
    if after:
        got = {t["id"]: t for t in float_tests(all_rows)}
        got.update({t["id"]: t for t in audit_tests(_audit2.stored_days(), [t for t in tracked if t in meta])})
        word = {"PASS": "PASS", "FAIL": "FAIL", "UNKNOWN": "UNKNOWN"}
        change = after["float_usd"] - last["float_usd"]
        add("E1", money(after["float_usd"]),
            f"{word[got['E1']['status']]}. Test E1: the float on the {FIRST_CHECK} reading had to be at least what it was on {pin} "
            f"({money(last['float_usd'])}). It " + (f"fell by {money(-change)}" if change < 0 else f"rose by {money(change)}"),
            "pipeline/score.py on the reading of that day", grade="chain, a reading taken after the test was written")
        add("E2", money(abs(change)),
            f"{word[got['E2']['status']]}. Test E2: the largest one-day change between the two readings ("
            + ("a fall" if change < 0 else "a rise") + f"). To pass it had to stay under the tenth-largest rise so far, {shown_tenth(got['E2']['text'])}",
            "as E1", grade="chain, a reading taken after the test was written", must_appear=False)
        if after["share_usd"] is not None:
            add("E3", pct(after["share_usd"]),
                f"{word[got['E3']['status']]}. Test E3: the private share of the tracked tokens on the {FIRST_CHECK} reading had to be at least 60.0%",
                "as E1", grade="chain, a reading taken after the test was written")
        d_ex = ex_near(after) - ex_near(last)
        earlier = [ex_near(rows[k]) - ex_near(rows[k - 1]) for k in range(1, len(rows))]
        near_part = after["groups"]["NEAR"] - last["groups"]["NEAR"]
        add("Y1", money(ex_near(after)),
            f"The float without NEAR's own token on the {FIRST_CHECK} reading, " + (f"down {money(-d_ex)}" if d_ex < 0 else f"up {money(d_ex)}")
            + f" from the pinned day. {sum(1 for x in earlier if x <= d_ex)} of that series' {len(earlier)} earlier one-day changes were falls at least as large. "
            + f"NEAR's own part of the float {'rose' if near_part >= 0 else 'fell'} by {money(abs(near_part))} over the same day",
            "as P4, on the later reading", grade="chain, a reading taken after the test was written")
        whole_moves = [rows[k]["float_usd"] - rows[k - 1]["float_usd"] for k in range(1, len(rows))]
        add("Y2", pct(Fraction(sum(1 for x in whole_moves if x < 0), len(whole_moves)), 0),
            f"Days up to the pinned one on which the float fell, out of {len(whole_moves)}: a single fall is ordinary", "count of negative one-day changes")
        add("G1", got["G1"]["value"] or got["G1"]["status"],
            f"{word[got['G1']['status']]}. Test G1 of PREREG-AUDIT.md: no tracked token short on the {FIRST_CHECK} reading",
            "pipeline/score_audit.py on the reading of that day", grade="chain, a reading taken after the test was written", must_appear=False)

    # --- one traced case: the largest single transfer of NEAR into the treasury in September
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    traced = load(os.path.join(DATA, "context", "trace.json"), None)
    for case in (traced or {}).get("cases", [])[:1]:
        amount = int(case["amount"])
        value = usd(amount, meta[case["token"]])
        left, back = case["hops"][0], case["hops"][-1]
        k = next(j for j in range(1, len(rows)) if rows[j]["height"] >= back["height"])      # the first reading that includes the return
        cut = next(r for r in rows if r["height"] >= left["height"])                           # the reading it left just before
        rise = rows[k]["float_usd"] - rows[k - 1]["float_usd"]
        best = max(rows[j]["float_usd"] - rows[j - 1]["float_usd"] for j in range(1, len(rows)))
        away = (back["timestamp"] - left["timestamp"]) // 10**9
        early = (blocks[cut["day"]]["timestamp"] - left["timestamp"]) // 10**9
        add("W1", f"{amount / 10**24 / 1e6:.1f}M NEAR",
            f"The largest single transfer of NEAR into the treasury in September, at {back['time_utc']} UTC. The treasury had paid out "
            f"the same amount, to the last unit, at {left['time_utc']} UTC: {away // 3600} hours {away % 3600 // 60} minutes earlier, "
            f"and {early // 60} minutes before the {cut['day']} reading. It was back {back['height'] - case['hops'][1]['height']} blocks after it was withdrawn from the public ledger",
            "pipeline/trace.py: halve the day to the block where the balance moved, then read that block's receipts; data/context/trace.json",
            grade="chain")
        add("W2", money(value), "That transfer at the pinned price", "amount times the pinned price", grade="chain")
        add("W3", money(rise), f"The float's rise on the {rows[k]['day']} reading, which includes that transfer"
            + (". It is the largest one-day rise in the series" if rise == best else ""), "one-day change, pinned prices")
        add("W4", pct(value / rise, 0), "Part of that day's rise that is money the treasury had paid out the evening before", "W2 over W3", grade="chain")

    # --- who moved the NEAR in September: an indexer's transfer list, used only on days that add up to the chain
    fl = load(os.path.join(DATA, "context", "flows.json"), None)
    if fl and fl.get("days"):
        from .flows import span
        fdays = sorted(fl["days"])
        good = [d for d in fdays if fl["days"][d]["adds_up"]]
        add("N1", f"{len(good)} of {len(fdays)} days",
            f"Days from {fdays[0]} to {fdays[-1]} on which the treasury's NEAR transfers listed by FastNEAR's index "
            f"({sum(fl['days'][d]['transfers'] for d in fdays):,} in all) add up, to the last unit, to the change in the balance read from the chain",
            "pipeline/flows.py: sum of listed transfers between two daily readings against the change in data/float/", grade="index, checked against the chain")
        win = span(fl, "2026-09-16", "2026-09-28")
        net = win["in"] - win["out"]
        if win["days"] and not win["skipped"] and net > 0:
            top_id, top = max(win["accounts"].items(), key=lambda kv: kv[1][0] - kv[1][1])
            add("N2", f"{win['in'] / 10**24 / 1e6:.1f}M NEAR",
                f"NEAR transferred into the treasury between the readings of 2026-09-15 and 2026-09-28, gross "
                f"({win['out'] / 10**24 / 1e6:.1f}M NEAR went out over the same days, which leaves the net inflow of C14)",
                "sum of incoming transfers on days that add up", grade="index, checked against the chain")
            add("N3", pct(Fraction(top[0] - top[1], net), 0),
                f"Part of that net inflow that came from one account, {top_id}: {top[0] / 10**24 / 1e6:.1f}M NEAR in and "
                f"{top[1] / 10**24 / 1e6:.1f}M NEAR out, in {top[2]:,} transfers", "the account's in minus out, over the net inflow",
                grade="index, checked against the chain")
            add("N4", pct(Fraction(top[0], win["in"]), 0), "The same account's part of the gross inflow over those days", "the account's in over all in",
                grade="index, checked against the chain")
        ex_day = fl["days"].get("2026-09-30")
        if ex_day and ex_day["adds_up"]:
            biggest = sorted((int(v[1]) for v in ex_day["by_account"].values()), reverse=True)[:3]
            add("N5", pct(Fraction(sum(biggest), int(ex_day["out"])), 0),
                f"Part of the NEAR that left the treasury before the 2026-09-30 reading ({int(ex_day['out']) / 10**24 / 1e6:.1f}M NEAR gross, "
                f"to {ex_day['accounts']:,} accounts) that went to the three largest receivers, each in a single transfer",
                "three largest outgoing totals over all out", grade="index, checked against the chain")

    # --- does the alarm cry wolf? Blocks drawn at random, audited (pipeline/audit.py --sample)
    rs = load(os.path.join(DATA, "context", "random_audit.json"), None)
    ex3 = load(os.path.join(DATA, "context", "exploit.json"), None)
    if rs and ex3 and rs.get("blocks") and rs.get("complete"):     # a sample still being read says nothing yet
        hole = lambda st: int(st["credited"]) - int(st["held"])   # noqa: E731
        steps3 = sorted(ex3["steps"], key=lambda st: st["height"])
        h_open = next(st["height"] for st in steps3 if hole(st) > 0)
        h_peak = max(steps3, key=hole)["height"]
        h_shut = next(st["height"] for st in steps3 if st["height"] > h_peak and hole(st) <= 0)
        done = [r for r in rs["blocks"].values() if r]
        inside = [r for r in done if h_open <= r["height"] < h_shut]
        outside = [r for r in done if not h_open <= r["height"] < h_shut]
        out_short = sum(1 for r in outside if r["short"])
        out_low = sum(1 for r in outside if r["low"])
        in_short = sum(1 for r in inside if r["short"])
        unread = sum(r["unread"] for r in done)
        # An unread check is accounted for when the daily reading before that block lacks the same number of tracked
        # tokens: tokens not yet on the books then. Anything beyond that is a read that failed, and is said so.
        from .audit import stored_days
        bl = load(os.path.join(DATA, "blocks.json"), {})
        tracked = rs["tokens"]
        lacking = sorted((bl[d]["height"], sum(1 for t in tracked if held.get(t) is None or cred.get(t) is None))
                         for d, held, cred in stored_days() if d in bl)
        def absent(h):   # noqa: E306
            before = [n for hh, n in lacking if hh <= h]
            return before[-1] if before else len(tracked)
        failed = sum(max(0, r["unread"] - absent(r["height"])) for r in done)
        why = ("each one a token that the daily reading before that block also lacks, because it was not yet on the books"
               if not failed else f"{unread - failed} of them tokens the daily reading before that block also lacks, and {failed} reads that failed")
        add("J1", f"{len(done)} random blocks",
            f"Blocks drawn at random (seed {rs['seed']}) between the first reading and the pinned one and audited for the {len(tracked)} tracked tokens: "
            f"{len(inside)} fell inside the {h_shut - h_open:,} blocks the October hole was open and {in_short} of those showed it; "
            f"{unread} token checks returned nothing and count as unknown, {why}",
            "python3 -m pipeline.audit --sample 200; data/context/random_audit.json", grade="chain")
        add("J2", f"{out_short} of {len(outside)}",
            "Random blocks outside the October hole on which any tracked token was short: how often the sign test would cry wolf", "count", grade="chain")
        add("J3", f"{out_low} of {len(outside)}",
            "Random blocks outside the October hole on which a tracked token held less over its credit than on every earlier daily reading", "count", grade="chain")
        if outside and out_short == 0:
            add("J4", pct(Fraction(3, len(outside)), 1), "With no false alarm in the sample, the highest false-alarm rate per block that the sample "
                "does not rule out, at about 95% confidence: three over the number of blocks (the rule of three)", "3 over J2's denominator", grade="model")

    # --- the track's working hypothesis: does NEAR Intents' volume lead network usage or NEAR's price? (pipeline/leadlag.py)
    if os.path.exists(os.path.join(DATA, "context", "activity.json")):
        from .leadlag import run as leadlag_run
        ll = leadlag_run(pin)
        for cid, target in (("L1", "transactions"), ("L2", "active accounts"), ("L3", "price")):
            t = ll["tests"][target]
            add(cid, f"r = {t['r']:+.2f}, p = {t['p']:.2f}",
                f"Weekly change in NEAR Intents' reported volume against the change in NEAR's {target if target != 'price' else 'price'} "
                f"{t['lead_weeks']} week{'s' if t['lead_weeks'] != 1 else ''} later, the strongest of leads of 1 to 8 weeks. p is the share of "
                f"{ll['shifts']:,} circularly shifted series that do as well at their best lead (seed {ll['seed']})",
                "python3 -m pipeline.leadlag", grade="model, on quoted volume and NearBlocks activity")
        add("L4", f"{ll['changes']} weekly changes", f"Weeks in the lead-lag test, from the week of {ll['first_week']} to the week of {ll['last_week']}",
            "complete Monday-to-Sunday weeks both sources cover", grade="model")
        add("L5", f"r = {ll['tests']['transactions']['same_week']:+.2f}",
            "Weekly change in NEAR Intents' reported volume against the change in NEAR's transactions in the same week, with no lead: they move "
            "a little together, which a chart of the two would show. No p-value is given for it; the test is for a lead",
            "python3 -m pipeline.leadlag", grade="model, on quoted volume and NearBlocks activity")
    # --- 1Click's own records: its swaps settle through the private chain's treasury (pipeline/oneclick.py)
    oc = load(os.path.join(DATA, "context", "oneclick.json"), None)
    if oc and oc.get("swaps"):
        listed = [x for x in oc["swaps"] if x["treasury_transfers"]]
        onchain = sum(1 for x in listed for t in x["treasury_transfers"] if t.get("on_chain"))
        dates = sorted({x["updated_at"][:10] for x in oc["swaps"]})
        add("W5", f"{len(listed)} of {len(oc['swaps'])}",
            f"Completed or refunded 1Click swaps, found among {oc['senders']} accounts that paid into the treasury on six days after "
            f"2026-10-27, whose own status record lists the NEAR transaction that moved their tokens into the treasury "
            f"(swaps dated {dates[0]} to {dates[-1]}; {onchain} of those transfers read back from the chain as stated)",
            "pipeline/oneclick.py; data/context/oneclick.json", grade="chain, found through 1Click's public status records")
    # --- the September exit, ordered against the block where the hole in the public books opened
    fl2 = load(os.path.join(DATA, "context", "flows.json"), None)
    eo = (fl2 or {}).get("exit_order")
    if eo:
        before_net = (int(eo["before"]["in"]) - int(eo["before"]["out"])) / 10**24
        after_net = (int(eo["after"]["in"]) - int(eo["after"]["out"])) / 10**24
        big = eo["largest_out"]
        hole_ts = next(int(st["timestamp"]) for st in load(os.path.join(DATA, "context", "exploit.json"), {"steps": []})["steps"]
                       if int(st["height"]) == eo["mark_height"])
        lead_h = (hole_ts - max(int(b["timestamp"]) for b in big)) // (3600 * 10**9)
        add("N6", f"{-before_net / 1e6:.1f}M NEAR",
            f"Net NEAR that left the treasury between the reading of 2026-09-29 and block {eo['mark_height']}, where the hole in the public books opened. "
            f"From that block to the next reading the treasury gained {after_net / 1e6:.1f}M NEAR",
            "data/context/flows.json, exit_order", grade="index, checked against the chain")
        add("N7", f"{sum(int(b['amount']) for b in big) / 10**24 / 1e6:.1f}M NEAR",
            f"The three largest transfers out of the treasury that day, all between "
            + _dt2_fmt(min(int(b['timestamp']) for b in big)) + " and " + _dt2_fmt(max(int(b['timestamp']) for b in big)) + " UTC on 29 September",
            "as N6", grade="index, checked against the chain")
        add("N8", f"{lead_h} hours", "How long before the hole opened the last of those three transfers left", "block times", grade="index, checked against the chain")

    # --- the base-rate model: how often the float's own past, replayed, meets the long-dated readings
    from .model import BLOCK, PATHS, SEED, share, simulate, windows
    cut = {key: (label, since, until) for key, label, since, until in windows(rows, pin)}
    run = {key: simulate(rows, pin, since, until) for key, (_, since, until) in cut.items()}
    whole, before, after = run["whole"], run["before"], run["after"]
    setup = (f"{whole['horizon_days']} days to {whole['target']} built from runs of {BLOCK} consecutive past days, "
             f"{PATHS:,} paths, seed {SEED}")
    drawn = {"whole": f"from every day since the first deposit ({whole['changes']} daily changes)",
             "before": f"only from days before the reward programme was announced ({before['since']} to {before['until']}, {before['changes']} daily changes)",
             "after": f"only from days since the first reward's snapshot was triggered ({after['since']} to {after['until']}, {after['changes']} daily changes)"}
    add("O1", share(whole["r1_holds"]),
        f"Replayed paths on which R1 holds (the float is at least $200M on {whole['target']}), drawing {drawn['whole']}: "
        f"{setup}. A base rate, not a forecast", "python3 -m pipeline.model", grade="model")
    add("O2", share(before["r1_holds"]), f"The same, drawing {drawn['before']}", "as O1", grade="model")
    add("O3", share(after["r1_holds"]), f"The same, drawing {drawn['after']}", "as O1", grade="model")
    add("O4", share(whole["r5_holds"]),
        f"Replayed paths on which R5 holds (the float without NEAR's own token is at least $130M), drawing {drawn['whole']}",
        "as O1", grade="model")
    add("O5", share(before["r5_holds"]), "The same, drawing only from days before the reward programme was announced", "as O1", grade="model")
    add("O6", share(after["r5_holds"]), "The same, drawing only from days since the first reward's snapshot was triggered", "as O1", grade="model")
    add("O7", share(whole["r2_holds"]),
        "Replayed paths on which R2 holds (the ten best days are under 45% of the float), drawing from every day since the first deposit",
        "as O1", grade="model")
    for cid, key in (("O8", "whole"), ("O9", "before"), ("O10", "after")):
        m = run[key]
        add(cid, money(m["median_usd"]),
            f"Median float on {m['target']} across the replayed paths, drawing {drawn[key].split(' (')[0]} "
            f"(one path in ten ends below {money(m['p10_usd'])}, one in ten above {money(m['p90_usd'])})", "as O1", grade="model")
    add("O13", share(simulate(rows, pin, cut["after"][1], cut["after"][2], wrap=True)["r1_holds"]),
        f"O3 when a run may wrap from the end of the window to its start. Without wrapping, a run of {BLOCK} days cannot start in the last "
        f"{BLOCK - 1} days of a window, so its first and last days are drawn less often",
        "as O3, with wrap", grade="model")
    lengths = (1, 3, BLOCK, 14, 30)
    for cid, key in (("O11", "whole"), ("O12", "after")):
        got = [run[key]["r1_holds"] if b == BLOCK else simulate(rows, pin, cut[key][1], cut[key][2], block=b)["r1_holds"] for b in lengths]
        add(cid, f"{share(min(got))} to {share(max(got))}",
            f"How far O{'1' if key == 'whole' else '3'} moves when the runs are {', '.join(str(b) for b in lengths[:-1])} or {lengths[-1]} days long",
            "as O1, five run lengths", grade="model")

    out = {"pin_day": pin, "pin_height": last["height"], "priced_at": series["priced_at"], "claims": C}
    site = {"pin_day": pin, "pin_height": last["height"], "priced_at": series["priced_at"], "by_id": {c["id"]: c for c in C}}
    lines = ["| # | Number | What it is |", "| --- | --- | --- |"]
    lines += [f"| {c['id']} | **{c['shown']}** | {c['what']} |" for c in C]
    readme_path, index_path = os.path.join(ROOT, "README.md"), os.path.join(ROOT, "site", "index.html")
    readme = open(readme_path).read() if os.path.exists(readme_path) else ""
    findings_path = os.path.join(ROOT, "docs", "FINDINGS.md")
    findings = open(findings_path).read() if os.path.exists(findings_path) else ""
    a, b = "<!-- claims:start -->", "<!-- claims:end -->"
    if a in findings and b in findings:
        findings = findings[:findings.index(a) + len(a)] + "\n" + "\n".join(lines) + "\n" + findings[findings.index(b):]
    ra, rb = "<!-- results:start -->", "<!-- results:end -->"
    if ra in readme and rb in readme:
        readme = readme[:readme.index(ra) + len(ra)] + "\n" + "\n".join(results_table(rows_all, last, pin, tracked, meta)) + "\n" + readme[readme.index(rb):]
    thesis_path = os.path.join(ROOT, "THESIS.md")
    thesis = open(thesis_path).read() if os.path.exists(thesis_path) else ""
    gen = {}
    if "scenario_block" in dir() or True:
        try:
            gen["scenarios"] = scenario_block
        except NameError:
            pass
    ex_rec = load(os.path.join(DATA, "context", "exploit.json"), None)
    if ex_rec:
        gen["alarm"] = alarm_table(ex_rec, meta)
    thesis = fill_blocks(thesis, gen)
    index = fill_page(open(index_path).read(), site) if os.path.exists(index_path) else ""
    write_claims.last = {"claims": out, "claims_js": site_js("WATERLINE_CLAIMS", site), "readme": readme, "index": index, "thesis": thesis,
                         "findings": findings}
    if write:
        save(os.path.join(DATA, "derived", "claims.json"), out)
        with open(os.path.join(ROOT, "site", "claims.js"), "w") as f:
            f.write(write_claims.last["claims_js"])
        if readme:
            open(readme_path, "w").write(readme)
        if index:
            open(index_path, "w").write(index)
        if thesis:
            open(thesis_path, "w").write(thesis)
        if findings:
            open(findings_path, "w").write(findings)
    return out


# D1 in PREREG-AUDIT.md: has NEAR published the private chain's totals per token against a block height? Scored by hand.
D1_MET = False


def _dt2_fmt(ns):
    import datetime as _d
    return _d.datetime.fromtimestamp(ns / 1e9, _d.timezone.utc).strftime("%H:%M")


def scenarios(coverage, issuance, pin, low=Fraction(16, 1000), growth=(-0.2, 0.0, 0.25, 0.5, 1.0)):
    """Share of net new supply that revenue would cover at the end of 2029 and 2031, and the years to cover all of it,
    for revenue counted in NEAR growing at g a year; with issuance as now, or at `low` (HSP-029's target). A model:
    revenue and supply both compound at constant rates, and the lower issuance is taken as fully in force by the
    horizon. Returns rows, the growth needed for each case and horizon, and the markdown table."""
    import datetime as _d
    import math
    t0 = _d.date.fromisoformat(pin)
    horizons = {"2029": (_d.date(2029, 12, 31) - t0).days / 365.25, "2031": (_d.date(2031, 12, 31) - t0).days / 365.25}
    cases = {"as now": (float(coverage), float(issuance)), "at 1.6%": (float(coverage * issuance / low), float(low))}
    rows = []
    for g in growth:
        row = {"g": g}
        for name, (c, i) in cases.items():
            for h, years in horizons.items():
                row[(name, h)] = c * ((1 + g) / (1 + i)) ** years
            ratio = (1 + g) / (1 + i)
            row[(name, "years")] = math.log(1 / c) / math.log(ratio) if ratio > 1 and c < 1 else None
        rows.append(row)
    need = {(name, h): (1 + i) * (1 / c) ** (1 / years) - 1 for name, (c, i) in cases.items() for h, years in horizons.items()}

    def cell(x):
        return "over 100%" if x >= 1 else f"{x * 100:.0f}%"

    def yrs(x):
        return "never" if x is None else f"{x:.1f}"
    lines = ["| Revenue in NEAR grows, a year | Covered at end-2029, issuance as now | At end-2031 | Years to cover it all "
             "| Covered at end-2029, issuance at 1.6% | At end-2031 | Years to cover it all |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['g'] * 100:+.0f}% | {cell(r[('as now', '2029')])} | {cell(r[('as now', '2031')])} | {yrs(r[('as now', 'years')])} "
                     f"| {cell(r[('at 1.6%', '2029')])} | {cell(r[('at 1.6%', '2031')])} | {yrs(r[('at 1.6%', 'years')])} |")
    lines.append(f"| needed to cover it all | {need[('as now', '2029')] * 100:.0f}% a year by end-2029 | {need[('as now', '2031')] * 100:.0f}% a year by end-2031 | "
                 f"| {need[('at 1.6%', '2029')] * 100:.0f}% a year by end-2029 | {need[('at 1.6%', '2031')] * 100:.0f}% a year by end-2031 | |")
    return {"rows": rows, "need": need, "table": lines, "horizons": horizons}


def alarm_table(ex, meta):
    """From the replay of the October hole: when a reader at each interval, or an alarm at each size, first sees it,
    and how long that is before the first payout CertiK reports."""
    import datetime as _d
    m = meta[ex["token"]]
    unit = 10 ** m["decimals"]
    steps = sorted(ex["steps"], key=lambda st: st["timestamp"])
    paid = int(_d.datetime.strptime(ex["quoted"]["first_payout_utc"] + " +0000", "%Y-%m-%d %H:%M:%S %z").timestamp())

    def hole_at(t):
        h = None
        for st in steps:
            if st["timestamp"] // 10**9 <= t:
                h = int(st["credited"]) - int(st["held"])
            else:
                break
        if h is None:
            h = int(steps[0]["credited_before"]) - int(steps[0]["held_before"])
        return h

    def span(seconds):
        h, mm = seconds // 3600, seconds % 3600 // 60
        return f"{h}h {mm}m"

    def usd_of(units):
        return money(Fraction(units, unit) * m["price"])
    first = next(st for st in steps if int(st["credited"]) > int(st["held"]))
    t_open = first["timestamp"] // 10**9
    rows = ["| A reader who checks | First sees the hole at (UTC) | Hole then | Before the first payout |", "| --- | --- | --- | --- |"]
    for label, every in (("every block", 1), ("every 10 minutes", 600), ("every hour", 3600), ("once a day, at 00:00 UTC", 86400)):
        t = t_open if every == 1 else ((t_open + every - 1) // every) * every
        while t < paid and hole_at(t) <= 0:
            t += every
        if t >= paid:
            rows.append(f"| {label} | not before the payout | | |")
            continue
        when = _d.datetime.fromtimestamp(t, _d.timezone.utc).strftime("%d %b %H:%M:%S")
        rows.append(f"| {label} | {when} | {usd_of(hole_at(t))} | {span(paid - t)} |")
    rows += ["", "| An alarm set at a hole of | First reached at (UTC) | Before the first payout |", "| --- | --- | --- |"]
    for level in (10, 1_000, 10_000, 100_000, 1_000_000):
        hit = next((st for st in steps if int(st["credited"]) - int(st["held"]) >= level * unit and st["timestamp"] // 10**9 < paid), None)
        if hit:
            when = _d.datetime.fromtimestamp(hit["timestamp"] // 10**9, _d.timezone.utc).strftime("%d %b %H:%M:%S")
            rows.append(f"| {money(level)} | {when} | {span(paid - hit['timestamp'] // 10**9)} |")
    return rows


def fill_blocks(text, blocks):
    """Replace each <!-- name:start --> ... <!-- name:end --> block with generated lines."""
    for name, lines in blocks.items():
        a, b = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
        if a in text and b in text:
            text = text[:text.index(a) + len(a)] + "\n" + "\n".join(lines) + "\n" + text[text.index(b):]
    return text


def results_table(rows_all, last, pin, tracked, meta):
    """The table of dated tests that opens the README, written from the scorers' own output so a verdict cannot be mistyped."""
    from . import audit as _audit
    from .score import tests as float_tests
    from .score_audit import tests as audit_tests
    got = float_tests(rows_all) + audit_tests(_audit.stored_days(), [t for t in tracked if t in meta])
    by_id = {t["id"]: t for t in got}
    by_day = {r["day"]: r for r in rows_all}
    said = {"G1": "no tracked token is short", "G2": "no tracked token is short",
            "E1": f"the float is at least what it was on {pin} ({money(last['float_usd'])})", "F1": f"the float is at least what it was on {pin} ({money(last['float_usd'])})",
            "E2": "no single day adds another lump", "F2": "no single day adds another lump",
            "E3": "the private share of the tracked tokens is at least 60.0%", "F3": "the private share of the tracked tokens is at least 60.0%"}
    done = [t for t in got if t["status"] != "PENDING" and t["id"] in said]
    lines = []
    if done:
        lines += ["| Test | Reading | Result |", "| --- | --- | --- |"]
        for t in sorted(done, key=lambda t: (t["due"], t["id"][0] != "G", t["id"])):
            r = by_day.get(t["due"])
            detail = ""
            if t["id"][1] == "1" and t["id"][0] in "EF" and r:
                detail = f": it was {money(r['float_usd'])}"
            if t["id"][1] == "3" and r and r.get("share_usd") is not None:
                detail = f": {pct(r['share_usd'])}"
            lines.append(f"| {t['id']}: {said[t['id']]} | {t['due']} | **{t['status']}**{detail} |")
        lines.append("")
    pending = [t for t in got if t["status"] == "PENDING"]
    dues = sorted({t["due"] for t in pending})
    parts = [f"{sum(1 for t in pending if t['due'] == d)} on the {d} reading" for d in dues]
    lines.append(f"Scored by code and still pending: {', '.join(parts)}. Two more, R4 and D1, are scored by hand on 2027-03-31. "
                 "`make score` prints every test.")
    return lines


def shown_tenth(text):
    """The tenth-largest rise as score.py printed it in a test's text."""
    import re
    m = re.search(r"\((\$[\d.]+M)\)", text)
    return m.group(1) if m else "the stated limit"


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def long_day(day):
    return f"{int(day[8:10])} {MONTHS[int(day[5:7]) - 1]} {day[:4]}"


def shown_for(claim, part=None, fmt=None):
    """The text a page element shows for a claim. site/app.js applies the same three rules in the browser."""
    import re
    text = claim["shown"]
    if part == "then":
        m = re.search(r"\(([^)]+) then\)", claim["what"])
        text = m.group(1) if m else text
    if part == "unpriced":
        m = re.search(r"\((\d+) of them", claim["what"])
        text = m.group(1) if m else text
    if fmt == "date":
        text = long_day(text)
    if fmt == "lead":
        text = text.split(" ")[0]
    if fmt == "hm":
        m = re.fullmatch(r"(\d+) hours? (\d+) minutes?", text)
        text = f"{m.group(1)}h {m.group(2)}m" if m else text
    return text


def fill_page(html, site):
    """Write every claim into the static page, so the numbers are in the HTML itself and not only filled by script."""
    import re

    def claim(m):
        attrs = m.group(2)
        cid = re.search(r'data-claim="([^"]+)"', attrs).group(1)
        part = re.search(r'data-part="([^"]+)"', attrs)
        fmt = re.search(r'data-fmt="([^"]+)"', attrs)
        c = site["by_id"].get(cid)
        text = shown_for(c, part and part.group(1), fmt and fmt.group(1)) if c else "n/a"
        return f"<{m.group(1)}{attrs}>{text}</{m.group(1)}>"

    html = re.sub(r'<(span|td|dd|p)(\b[^>]*\bdata-claim="[^"]+"[^>]*)>[^<]*</\1>', claim, html)
    pins = {"height": f"{site['pin_height']:,}", "day": long_day(site["pin_day"]),
            "priced": site["priced_at"].replace("T", " ").replace("Z", " UTC")}
    return re.sub(r'<(b|span)(\b[^>]*\bdata-pin="(\w+)"[^>]*)>[^<]*</\1>',
                  lambda m: f"<{m.group(1)}{m.group(2)}>{pins.get(m.group(3), '')}</{m.group(1)}>", html)


if __name__ == "__main__":
    out = write_claims()
    for c in out["claims"]:
        print(f"{c['id']:10} {c['shown']:22} {c['what']}")
