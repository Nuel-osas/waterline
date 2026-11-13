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
        need = (per_day * 30) / rev_near
        add("M1", f"{float(rev / vol * 10000):.1f} basis points", f"Revenue reaching NEAR's wallets per dollar of reported volume, {span}", "X3 over X1", grade="reported")
        add("M2", f"{float(need):.1f}x", "How many times revenue would have to grow for buybacks to match net new supply", "one over V4", grade="chain, via an indexer")
        add("M3", f"${float(vol * Fraction(365, 30) * need) / 1e9:.0f}B a year", "Reported volume that would take at today's rate of revenue per dollar of volume",
            "annualised X1 times M2", grade="reported")

    peak = max(rows, key=lambda r: r["float_usd"])
    add("T4", money(peak["float_usd"]), f"Highest the float has been, on the {peak['day']} reading", "largest daily value, pinned prices")
    add("P8", f"{float(ex_near(last) / ex_near(launch)):.1f}x", f"Growth of the float without NEAR's own token since the B2B launch ({money(ex_near(launch))} then)", "as C7, without the NEAR group")

    cus = load(os.path.join(DATA, "context", "custody.json"), None)
    if cus:
        add("K1", f"{len(cus['keys_registered_in_intents_near'])} key",
            "Keys registered inside intents.near for the treasury account at the pinned block "
            + ("(the account has contract code)" if cus["account_has_contract_code"] else "(the account itself has no contract code)"),
            "intents.near.public_keys_of(treasury) and view_account(treasury)", grade="chain")

    out = {"pin_day": pin, "pin_height": last["height"], "priced_at": series["priced_at"], "claims": C}
    site = {"pin_day": pin, "pin_height": last["height"], "priced_at": series["priced_at"], "by_id": {c["id"]: c for c in C}}
    lines = ["| # | Number | What it is |", "| --- | --- | --- |"]
    lines += [f"| {c['id']} | **{c['shown']}** | {c['what']} |" for c in C]
    readme_path, index_path = os.path.join(ROOT, "README.md"), os.path.join(ROOT, "site", "index.html")
    readme = open(readme_path).read() if os.path.exists(readme_path) else ""
    a, b = "<!-- claims:start -->", "<!-- claims:end -->"
    if a in readme and b in readme:
        readme = readme[:readme.index(a) + len(a)] + "\n" + "\n".join(lines) + "\n" + readme[readme.index(b):]
    index = fill_page(open(index_path).read(), site) if os.path.exists(index_path) else ""
    write_claims.last = {"claims": out, "claims_js": site_js("WATERLINE_CLAIMS", site), "readme": readme, "index": index}
    if write:
        save(os.path.join(DATA, "derived", "claims.json"), out)
        with open(os.path.join(ROOT, "site", "claims.js"), "w") as f:
            f.write(write_claims.last["claims_js"])
        if readme:
            open(readme_path, "w").write(readme)
        if index:
            open(index_path, "w").write(index)
    return out


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
