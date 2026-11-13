# Waterline

**What NEAR Intents' private chain holds, read every day from public NEAR. An investment thesis for NEAR built
only on numbers anyone can recompute.**

Built at NEAR HACKATHON 2026. Track: Investment Thesis (`thesis`).

Live dashboard: <https://nuel-osas.github.io/waterline/>

## The problem

NEAR's investment case rests on NEAR Intents. On 27 October 2026, NEAR Intents moved its 1Click swaps to a
private chain. The docs describe it as "a permissioned instance of the NEAR protocol operated by a small validator set
with no public networking", where a swap is "invisible to public indexers".

Since that day, the volume and fee figures that investors quote come from tables NEAR's own team uploads. An
outsider can read them but cannot recompute them. A thesis "judged on the evidence" needs evidence that does not
depend on the party being valued.

## What this is

One thing about the private chain is still fully public: the tokens that back it sit in one account inside the
`intents.near` contract. Waterline reads that account at one block per day since it was created, asks each
token's contract how much `intents.near` holds in total, and builds:

- a daily history of the money behind the private chain (the float), in tokens and in dollars at fixed prices;
- the share of everything NEAR Intents holds that is now private;
- an investment thesis on NEAR that states which of its inputs are observed and which are reported, and the
  four readings that would change it: [`THESIS.md`](THESIS.md);
- a dashboard that shows all of it: `make serve`.

No key, no account, no package to install. Python 3.9 or newer.

## Findings

As of NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). This table is written by `pipeline/claims.py` from
the raw readings; `make check` rebuilds it and fails if any number in this file or in `THESIS.md` differs.

<!-- claims:start -->
| # | Number | What it is |
| --- | --- | --- |
| C1 | **$132.3M** | Value locked behind the private chain on 2026-11-13, at pinned prices |
| C2 | **205 token types** | Different tokens the private chain held on 2026-11-13 (52 of them have no price and are left out of every dollar figure) |
| C3 | **2026-02-19** | First day the treasury held anything |
| C4 | **60.2%** | Share of everything intents.near holds that sits behind the private chain on 2026-11-13: every token in NEAR Intents' token list that has a price and a readable total (158 tokens, $219.6M in total; 27 listed tokens could not be read and are left out) |
| C6-NEAR | **69.9%** | The same share for NEAR alone on 2026-11-13 ($62.3M held in total) |
| C6-Stablecoins | **67.5%** | The same share for stablecoins alone on 2026-11-13 ($70.6M held in total) |
| C6-ZEC | **60.3%** | The same share for ZEC alone on 2026-11-13 ($23.7M held in total) |
| C6-ETH | **57.5%** | The same share for ETH alone on 2026-11-13 ($7.7M held in total) |
| C6-BTC | **28.8%** | The same share for bitcoin alone on 2026-11-13 ($27.5M held in total) |
| C23 | **61.8%** | The same share on 2026-11-13 for the 20 tokens tracked through time (the largest by total held) |
| C18 | **90%** | Part of everything intents.near holds that the tracked tokens cover |
| C19 | **6%** | Tracked-token share on 2026-04-02, the first reading of April |
| C20 | **$83.5M** | Public side of intents.near on 2026-04-02, tracked tokens ($75.7M on 2026-11-13) |
| C24 | **$75.7M** | Public side of intents.near on 2026-11-13, tracked tokens |
| C5 | **36.2%** | Tracked-token share on 2026-07-16, the first reading after the B2B launch of 2026-07-13 |
| C21 | **56.2%** | Tracked-token share on 2026-10-26, the day before the switch |
| C7 | **2.7x** | Growth of the private float since the B2B launch on 2026-07-13 ($49.3M then) |
| C8 | **$75.0M** | Added on the 10 best days out of 268 (the float today is $132.3M) |
| C17 | **57%** | The ten best days as a share of today's float (the concentration reading) |
| C9 | **$14.6M** | Largest one-day fall in the float, between the readings of 2026-09-29 and 2026-09-30 |
| C10 | **2.6%** | Change in the float across the day every 1Click swap moved to the private chain (2026-10-26 to 2026-10-28) |
| C11 | **$18.0M** | Added to the float between 2026-10-27 and 2026-11-13 |
| C12 | **Stablecoins: $47.6M** | Largest asset group in the float on 2026-11-13 |
| C13 | **NEAR: $43.5M** | NEAR's own token in the float on 2026-11-13 |
| C22 | **67%** | Part of the float that is not NEAR's own token on 2026-11-13 |
| C14 | **12.6M NEAR** | wNEAR that entered the float between the readings of 2026-09-15 and 2026-09-28 |
| C15 | **3.9M NEAR** | wNEAR that left the float in one day, between the readings of 2026-09-29 and 2026-09-30 |
| C16 | **12.4M NEAR** | wNEAR in the float on 2026-11-13 |
| X1 | **$3.77B** | Reported 30-day swap volume (DefiLlama, from a table NEAR uploads to Dune) |
| X2 | **$5.8M** | Reported 30-day gross fees (same kind of source) |
| X3 | **$1.8M** | 30-day revenue that reached NEAR's public revenue wallets (DefiLlama, from chain tables) |
| X4 | **0.57x a day** | Reported daily volume divided by everything intents.near holds |
| V1 | **$4.62B** | NEAR market value on 2026-11-13: supply in the block header times the pinned price of $3.52 |
| V2 | **88,704 NEAR a day** | Net new NEAR supply, average of the 30 days to the pinned day |
| V3 | **$114.0M a year** | The same, in dollars at the pinned price |
| V4 | **20%** | Revenue reaching NEAR's wallets as a share of net new supply (30 days) |
| V5 | **207x** | NEAR market value divided by that revenue, annualised |
<!-- claims:end -->

C rows are measured here from chain state. V rows combine a block-header reading with one quoted figure. X rows
are quoted from DefiLlama and labelled with their origin; this project does not vouch for them.

## Try it

| Do | See |
| --- | --- |
| `make test` | The unit tests pass. No network. About a second. |
| `make check` | Every number above is rebuilt from `data/` and compared. Ends with `RESULT: PASS`. No network. |
| `make verify` | First re-reads 8 days from a public NEAR archival node and compares them with the stored readings, then does everything `make check` does. About a minute. |
| `make score` | The forward tests in [`PREREG.md`](PREREG.md), each `PASS`, `FAIL` or `PENDING` until its reading exists. |
| `make serve` | The dashboard at <http://localhost:8080>. |
| `python3 -m pipeline.verify --all` | Re-reads every day. Slow: public nodes allow under one request a second. |

What `make verify` prints, shortened:

```
re-reading 8 days from https://archival-rpc.mainnet.fastnear.com
ok   2026-02-18  block 186012275  0 balances and 0 totals match the chain
ok   2026-10-27  block 221760250  180 balances and 3 totals match the chain
ok   2026-11-13  block 224285109  205 balances and 3 totals match the chain
...
ok   series rebuilt from raw data is identical (269 days)
ok   C1: $132.3M  (Value locked behind the private chain on 2026-11-13, at pinned prices)
ok   C4: 60.2%  (Share of everything intents.near holds that sits behind the private chain ...)
...
RESULT: PASS
```

To check one number by hand, with nothing from this repository:

```sh
curl -s https://archival-rpc.mainnet.fastnear.com -H 'Content-Type: application/json' -d '{
  "jsonrpc":"2.0","id":1,"method":"query","params":{
    "request_type":"call_function","block_id":224285109,"account_id":"intents.near",
    "method_name":"mt_batch_balance_of",
    "args_base64":"'$(printf '{"account_id":"51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe","token_ids":["nep141:wrap.near"]}' | base64 | tr -d '\n')'"}}' \
  | python3 -c 'import sys,json; print(bytes(json.load(sys.stdin)["result"]["result"]).decode())'
```

It prints the private chain's wNEAR balance at that block, in yoctoNEAR. The same value is in
`data/float/2026-11-13.json`.

## The thesis in short

1. NEAR's price is a growth price: its market value is 207x the revenue that reaches NEAR's wallets, and that
   revenue covers 20% of net new supply.
2. The growth is in a product whose activity went private on 27 October. The float is the growth signal that
   cannot be reported into existence, and it is up 2.7x since July.
3. The same float is the largest unpriced risk: nothing public proves the private chain owes what the treasury
   holds.
4. Position: constructive, conditional on four dated readings. See [`THESIS.md`](THESIS.md).

## How it works

```
public NEAR archival node
   |  block header at ~00:00 UTC each day            -> data/blocks.json
   |  intents.near.mt_batch_balance_of(treasury)     -> data/float/<day>.json
   |  <token>.ft_balance_of(intents.near)            -> data/held/<day>.json
   v
pipeline/build.py    exact integer and fraction arithmetic -> data/derived/series.json, site/data.js
pipeline/claims.py   every quoted number                   -> data/derived/claims.json, the table above
pipeline/score.py    forward tests written in PREREG.md     -> data/derived/forward.json
pipeline/verify.py   re-read from the chain, rebuild, compare
```

- A reading is tied to a block height, so it never changes and anyone gets the same bytes.
- A read that fails is stored as `null` and left out. It is never counted as zero.
- If the treasury shows more of a token than the token's contract says `intents.near` holds, that reading is
  left out of the share and listed in `data/derived/anomalies.json`. It is never turned into a share above
  100%. One such reading exists so far: 2026-10-01, the old BNB Chain USDT id.
- Constants and how each was checked: [`docs/SOURCES.md`](docs/SOURCES.md).
- A scheduled workflow (`.github/workflows/daily.yml`) reads the new days every morning, scores the forward
  tests and republishes the dashboard, so the gauge outlives the hackathon. It commits nothing: the numbers
  quoted in the text stay pinned to the block above.

## How NEAR fits

The subject is NEAR, and the method only works because of how NEAR is built: `intents.near` is a public
multi-token ledger (NEP-245) with view methods, token contracts follow NEP-141, and archival nodes answer view
calls at any past block. That is what lets a private chain's backing be audited from outside without anyone's
permission.

## Limits

The full list is in [`THESIS.md`](THESIS.md#5-limits). The main ones: dollar figures use one fixed price list;
52 token types have no price and are left out; the 60.2% counts every listed token with a price on the pinned
day, while the history follows the 20 largest and is weekly before 23 October; one reading a day cannot see
money that enters and leaves within the day; the treasury shows assets, not what the private chain owes; volume,
fees and revenue are quoted from DefiLlama, not recomputed here.

## What was built for this hackathon

Everything in this repository was written during the hackathon window (after 2026-10-19). No earlier code.
Libraries: none beyond the Python standard library; the dashboard is plain HTML, CSS and JavaScript with no
framework. Fonts: Geist and Geist Mono (SIL Open Font License), in `site/fonts/`. Data sources: NEAR mainnet
through a public archival node, NEAR Intents' public token list, DefiLlama's public API. The code and text were
written with an AI coding assistant (Claude Code) under the author's direction, and every number was checked
against the chain by the commands above.

## Licence

MIT. See [`LICENSE`](LICENSE).
