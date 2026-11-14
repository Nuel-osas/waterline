"""Fetch the inputs that do not come from the daily chain readings, and write them under data/.

  python3 -m pipeline.context            # everything below
  python3 -m pipeline.context tokens     # one part: tokens | quoted | supply | custody | tracked

What each part is, and how far it can be re-checked:
  tokens   NEAR Intents' own token list (ids, decimals, prices). The list changes during a day, so new ids are
           ADDED to data/tokens.json and an id already there keeps its first price: the file is a pin, not a feed.
  quoted   DefiLlama's daily volume, fees and revenue for NEAR Intents, and CoinGecko's daily NEAR price through
           DefiLlama. These are other people's numbers. They are stored as fetched and labelled as quoted.
  supply   `total_supply` from the block header of chosen days. `make verify` re-reads these from the chain.
  custody  The keys registered for the treasury inside intents.near at the pinned block, and whether the
           account has contract code. `make verify` re-reads these too.
  tracked  The tokens followed through time: the 20 largest by total held on the pinned day.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

from . import rpc
from .pull import DATA, load, save

UTC = dt.timezone.utc
TOKENS_URL = "https://1click.chaindefuser.com/v0/tokens"
LLAMA = {
    "volume": "https://api.llama.fi/summary/dexs/near-intents?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true",
    "fees": "https://api.llama.fi/summary/fees/near-intents?dataType=dailyFees&excludeTotalDataChartBreakdown=true",
    "revenue": "https://api.llama.fi/summary/fees/near-intents?dataType=dailyRevenue&excludeTotalDataChartBreakdown=true",
    "holders_revenue": "https://api.llama.fi/summary/fees/near-intents?dataType=dailyHoldersRevenue&excludeTotalDataChartBreakdown=true",
}
TRACKED_COUNT = 20


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "waterline/1"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def now():
    return dt.datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def pin_day():
    return load(os.path.join(DATA, "pin.json"), None)["pin_day"]


def tokens():
    path = os.path.join(DATA, "tokens.json")
    have = load(path, {"source": TOKENS_URL, "fetched_at": now(), "fetches": [], "tokens": []})
    known = {t["assetId"] for t in have["tokens"]}
    fresh = [t for t in get(TOKENS_URL) if t["assetId"] not in known]
    have["tokens"] += fresh
    have.setdefault("fetches", [have["fetched_at"]])
    have["fetches"].append(now())
    save(path, have)
    print(f"tokens: {len(known)} already pinned, {len(fresh)} added, {len(have['tokens'])} in all")


def quoted():
    out = {"fetched_at": now(), "series": {}}
    for name, url in LLAMA.items():
        chart = get(url).get("totalDataChart") or []
        out["series"][name] = {"source": url, "daily": [
            [dt.datetime.fromtimestamp(t, UTC).strftime("%Y-%m-%d"), v] for t, v in chart]}
    save(os.path.join(DATA, "context", "defillama.json"), out)
    pin = dt.date.fromisoformat(pin_day())
    start = int(dt.datetime(pin.year, pin.month, pin.day, tzinfo=UTC).timestamp()) - 99 * 86400
    url = f"https://coins.llama.fi/chart/coingecko:near?start={start}&span=100&period=1d"
    prices = get(url)["coins"]["coingecko:near"]["prices"]
    save(os.path.join(DATA, "context", "near_price.json"), {
        "source": url, "fetched_at": now(),
        "what": "CoinGecko's NEAR price through DefiLlama, one value a day at 00:00 UTC. Used only to turn "
                "DefiLlama's dollar revenue back into NEAR and to value the supply; never for the float.",
        "daily": {dt.datetime.fromtimestamp(p["timestamp"], UTC).strftime("%Y-%m-%d"): p["price"] for p in prices}})
    print(f"quoted: {len(out['series'])} DefiLlama series, {len(prices)} daily NEAR prices")


def supply():
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    pin = dt.date.fromisoformat(pin_day())
    want = sorted({(pin - dt.timedelta(days=n)).isoformat() for n in (0, 30, 60, 90)} | {min(blocks)})
    out = {}
    for day in want:
        if day in blocks:
            head = rpc.header(blocks[day]["height"])
            out[day] = {"height": head["height"], "total_supply": head["total_supply"]}
    save(os.path.join(DATA, "context", "supply.json"), {
        "source": "block header field total_supply (yoctoNEAR) at the day's block in data/blocks.json", "days": out})
    print("supply:", ", ".join(out))


def custody():
    blocks = load(os.path.join(DATA, "blocks.json"), {})
    height = blocks[pin_day()]["height"]
    keys = rpc.view(height, rpc.LEDGER, "public_keys_of", {"account_id": rpc.TREASURY})
    account = rpc.call("query", {"request_type": "view_account", "block_id": height, "account_id": rpc.TREASURY})
    access = rpc.call("query", {"request_type": "view_access_key_list", "block_id": height, "account_id": rpc.TREASURY})["keys"]
    save(os.path.join(DATA, "context", "custody.json"), {
        "height": height, "treasury": rpc.TREASURY,
        "keys_registered_in_intents_near": keys,
        "account_code_hash": account["code_hash"],
        "account_has_contract_code": account["code_hash"] != "1" * 32,
        # A new access key's nonce is its creation block height times 1,000,000 and goes up by one with every
        # transaction it signs. A nonce that is still a whole multiple of 1,000,000 has never signed one.
        "account_access_keys": [{"public_key": k["public_key"], "nonce": k["access_key"]["nonce"],
                                 "permission": k["access_key"]["permission"] if isinstance(k["access_key"]["permission"], str) else "FunctionCall"}
                                for k in access],
        "what": "intents.near.public_keys_of(treasury) and view_account(treasury) at the pinned block. An implicit "
                "account's id is its own public key in hex, so one key equal to the id is the default."})
    print("custody:", len(keys), "key(s); contract code:", account["code_hash"] != "1" * 32)


def tracked():
    """The tokens followed through time: the largest by total held on the pinned day, at the pinned prices."""
    from .build import token_meta, usd
    meta, _ = token_meta()
    held = load(os.path.join(DATA, "held", pin_day() + ".json"), None)["held"]
    ranked = sorted(((usd(int(v), meta.get(t)) or 0, t) for t, v in held.items() if v), reverse=True)
    save(os.path.join(DATA, "tracked.json"), sorted(t for _, t in ranked[:TRACKED_COUNT]))
    print("tracked:", TRACKED_COUNT, "tokens")



def activity():
    """Daily network activity from NearBlocks' public charts (no key): transactions, active accounts and NEAR's price.
    Used only by the lead-lag test in pipeline/leadlag.py, which the track's example prompt asks for."""
    got = get("https://api.nearblocks.io/v1/charts")
    rows = got.get("charts", got) if isinstance(got, dict) else got
    days = {}
    for r in rows:
        day = r["date"][:10]
        days[day] = {"txns": int(r["txns"]), "active_accounts": int(r["active_accounts"]), "near_price": str(r["near_price"])}
    save(os.path.join(DATA, "context", "activity.json"), {
        "source": "https://api.nearblocks.io/v1/charts (NearBlocks, public, no key)", "fetched_at": now(),
        "days": dict(sorted(days.items()))})
    print(f"activity: {len(days)} days, {min(days)} to {max(days)}")


PARTS = {"tokens": tokens, "quoted": quoted, "supply": supply, "custody": custody, "tracked": tracked, "activity": activity}


if __name__ == "__main__":
    for name in (sys.argv[1:] or ["tokens", "quoted", "supply", "custody"]):
        PARTS[name]()
