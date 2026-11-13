# Waterline

**NEAR Intents' swaps went private. The money behind them did not.** Waterline reads that money every day from
public NEAR. It is an investment thesis for NEAR whose own measurements anyone can recompute, and which labels
every number it only quotes. Run over past blocks, the same reading shows one token almost wholly unbacked on
2 October 2026, which matches a published exploit.

Built at NEAR HACKATHON 2026. Track: Investment Thesis (`thesis`).

Live dashboard: <https://nuel-osas.github.io/waterline/>

## The problem

NEAR's investment case leans on NEAR Intents. On 27 October 2026, NEAR Intents' 1Click swaps began to settle on
a private chain. The docs describe it as "a permissioned instance of the NEAR protocol operated by a small
validator set with no public networking", where a swap is "invisible to public indexers".

The volume and fee figures that investors quote have come from NEAR-run sources since 2025. Until 27 October an
outsider could in principle cross-check them against public settlement in `intents.near` (we did not). Since
then the swap leg is private. A thesis "judged on the evidence" needs evidence that does not depend on the party being valued.

## What this is

One thing about the private chain is still fully public: the tokens that back it sit in one account inside the
`intents.near` contract. Waterline reads that account at one block per day since it was created, asks each
token's contract how much `intents.near` holds in total, and builds:

- a daily history of the money behind the private chain (the float), in tokens and in dollars at fixed prices;
- the share of everything NEAR Intents holds that is now private;
- a check, on every reading that has totals, that the treasury is never credited with more of a token than
  `intents.near` holds. It fails on two readings in October, which match a published exploit by token, size
  and day;
- the float read against NEAR's own reward programme for confidential balances;
- an investment thesis on NEAR that states which of its inputs are observed and which are reported, and the
  readings that would change it: [`THESIS.md`](THESIS.md);
- forward tests written before their readings exist, scored by code: [`PREREG.md`](PREREG.md);
- a seeded model anyone can re-run, which replays the float's past daily changes forward and counts how often
  the thesis's long-dated readings hold: `make model`;
- a dashboard that shows all of it: `make serve`.

No key, no account, no package to install. Python 3.9 or newer.

## Findings

As of NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). This table is written by `pipeline/claims.py` from
the raw readings. `make check` rebuilds it in memory and fails if it differs, and fails if any dollar amount,
percentage, multiple or NEAR amount in the prose of this file, `THESIS.md` or `PREREG.md` is neither one of
these rows nor a constant declared in `data/constants.json`. It does not check plain counts such as "205 token
types", and it cannot tell that a valid number was put in the wrong sentence.

<!-- claims:start -->
| # | Number | What it is |
| --- | --- | --- |
| C1 | **$136.4M** | Value locked behind the private chain on 2026-11-13, at pinned prices |
| C2 | **205 token types** | Different tokens the private chain held on 2026-11-13 (30 of them have no price and are left out of every dollar figure) |
| C3 | **2026-02-19** | First reading (00:00 UTC) on which the treasury held anything; the account was created the day before |
| C4 | **61.0%** | Share of everything intents.near holds that sits behind the private chain on 2026-11-13: every token in NEAR Intents' token list that has a price and a balance inside intents.near (180 tokens, $223.8M in total; 27 listed ids are not balances inside intents.near or could not be read, and are left out) |
| C6-NEAR | **69.9%** | The same share for NEAR alone on 2026-11-13 ($62.3M held in total) |
| C6-Stablecoins | **68.2%** | The same share for stablecoins alone on 2026-11-13 ($72.3M held in total) |
| C6-ZEC | **60.3%** | The same share for ZEC alone on 2026-11-13 ($23.7M held in total) |
| C6-ETH | **57.5%** | The same share for ETH alone on 2026-11-13 ($7.7M held in total) |
| C6-BTC | **28.8%** | The same share for bitcoin alone on 2026-11-13 ($27.5M held in total) |
| C23 | **62.3%** | The same share on 2026-11-13 for the 20 tokens tracked through time (the largest by total held) |
| C18 | **89%** | Part of everything intents.near holds that the tracked tokens cover |
| C19 | **6%** | Tracked-token share on 2026-04-02, the first reading of April |
| C20 | **$83.5M** | Public side of intents.near on 2026-04-02, tracked tokens ($75.0M on 2026-11-13) |
| C24 | **$75.0M** | Public side of intents.near on 2026-11-13, tracked tokens |
| C5 | **36.2%** | Tracked-token share on 2026-07-16, the first reading after the B2B launch of 2026-07-13 |
| C21 | **56.2%** | Tracked-token share on 2026-10-26, the day before the switch |
| C7 | **2.8x** | Growth of the private float since the B2B launch on 2026-07-13 ($49.3M then) |
| C8 | **$75.5M** | Added on the 10 best days out of 268 (the float on 2026-11-13 is $136.4M) |
| C17 | **55%** | The ten best days as a share of the float on 2026-11-13 (the concentration reading) |
| C25 | **$4.7M** | The tenth-largest one-day rise in the float so far (the bar for 'one more lump' in PREREG.md) |
| B1 | **63%** | Days on which the float did not fall, out of 268 (the base rate of test E1) |
| B2 | **58%** | Four-day windows since the B2B launch in which the float did not fall (the base rate of test F1) |
| B3 | **79%** | Four-day windows since the B2B launch with no day above the tenth-largest rise (the base rate of test F2) |
| C9 | **$14.6M** | Largest one-day fall in the float, between the readings of 2026-09-29 and 2026-09-30 |
| C10 | **2.8%** | Change in the float across the day 1Click swaps began to settle on the private chain (2026-10-26 to 2026-10-28) |
| C11 | **$20.7M** | Added to the float between 2026-10-27 and 2026-11-13 |
| C12 | **Stablecoins: $49.3M** | Largest asset group in the float on 2026-11-13 |
| C13 | **NEAR: $43.5M** | NEAR's own token in the float on 2026-11-13 |
| C22 | **68%** | Part of the float that is not NEAR's own token on 2026-11-13 |
| C14 | **12.6M NEAR** | wNEAR that entered the float between the readings of 2026-09-15 and 2026-09-28 |
| C15 | **3.9M NEAR** | wNEAR that left the float in one day, between the readings of 2026-09-29 and 2026-09-30 |
| C16 | **12.4M NEAR** | wNEAR in the float on 2026-11-13 |
| C27 | **8.5M NEAR** | wNEAR in the float on the 2026-09-17 reading, the day NEAR announced the reward's snapshot had been triggered |
| P1 | **$7.9M per 30 days** | Float growth before the reward programme (2026-02-19 to 2026-06-11) |
| P2 | **$14.3M per 30 days** | Float growth while the first reward was open (2026-06-11 to 2026-09-17) |
| P3 | **$31.8M per 30 days** | Float growth after the first reward's snapshot was triggered (2026-09-17 to 2026-11-13) |
| P9 | **$76.0M** | The float on the 2026-09-17 reading, the day NEAR announced confidential balances had passed $70M (at that day's prices) |
| P4 | **$92.9M** | Float without NEAR's own token on 2026-11-13 ($46.1M on 2026-09-17) |
| P5 | **$46.1M** | Float without NEAR's own token on 2026-09-17 |
| P6 | **$2.7M** | Largest one-day fall in the float without NEAR's own token |
| P7 | **69%** | Part of the wNEAR that arrived between 2026-09-15 and 2026-09-28 that had left again by the pinned day |
| S1 | **2 readings** | Readings where the treasury was credited with more of a token than intents.near held: 2026-10-01, 2026-10-02 |
| S2 | **$3.3M** | Largest such shortfall, on the 2026-10-02 reading: USDT(DEPRECATED) on bsc, 67,669 held against 3,373,849 credited |
| S3 | **98%** | Part of the treasury's credit in that token that had nothing behind it on that reading |
| S5 | **25%** | Part of the treasury's credit in that token with nothing behind it on the earlier reading, 2026-10-01 |
| S4 | **2026-10-03** | First reading on which that token was fully held again |
| X1 | **$3.73B** | Reported swap volume, 30 days to 2026-11-11 (DefiLlama, from a table uploaded to Dune under the near team's name) |
| X2 | **$6.0M** | Reported gross fees, 30 days to 2026-11-11 (same kind of source) |
| X3 | **$1.8M** | Revenue that reached NEAR's public revenue wallets, 30 days to 2026-11-11 (DefiLlama, from chain tables, in dollars at each day's price) |
| T1 | **-22%** | Change in reported volume, 30 days to 2026-11-11 against the 30 days before |
| T2 | **-26%** | Change in reported fees, 30 days to 2026-11-11 against the 30 days before |
| T3 | **-20%** | Change in revenue reaching NEAR's wallets, 30 days to 2026-11-11 against the 30 days before |
| X4 | **0.56x a day** | Reported daily volume divided by everything intents.near holds |
| V1 | **$4.48B** | Value of NEAR's total supply on 2026-11-13: supply in the block header times CoinGecko's price of $3.42 |
| V2 | **88,704 NEAR a day** | Net new NEAR supply, average of the 30 days to the pinned day |
| V3 | **$110.7M a year** | The same, in dollars at that price |
| V4 | **15%** | Revenue reaching NEAR's wallets as a share of net new supply, NEAR against NEAR, 30 days to 2026-11-11 |
| V5 | **265x** | NEAR's total supply divided by that revenue, annualised, NEAR against NEAR |
| M1 | **4.8 basis points** | Revenue reaching NEAR's wallets per dollar of reported volume, 30 days to 2026-11-11 |
| M2 | **6.5x** | How many times revenue would have to grow for buybacks to match net new supply |
| H1 | **4.2x** | How many times revenue would have to grow if net new supply ran at the 1.6% a year that HSP-029 proposes |
| M3 | **$297B a year** | Reported volume that would take at today's rate of revenue per dollar of volume |
| T4 | **$136.4M** | Highest the float has been, on the 2026-11-13 reading |
| P8 | **3.5x** | Growth of the float without NEAR's own token since the B2B launch ($26.8M then) |
| K2 | **1 of 1** | Access keys of the treasury account on NEAR itself that have never signed a transaction (the nonce is still the value set at creation) |
| K1 | **1 key** | Keys registered inside intents.near for the treasury account at the pinned block (the account itself has no contract code) |
| O1 | **53%** | Replayed paths on which R1 holds (the float is at least $200M on 2027-03-31), drawing from every day since the first deposit (267 daily changes): 138 days to 2027-03-31 built from runs of 7 consecutive past days, 10,000 paths, seed 20261113. A base rate, not a forecast |
| O2 | **under 1%** | The same, drawing only from days before the reward programme was announced (2026-02-19 to 2026-06-11, 112 daily changes) |
| O3 | **82%** | The same, drawing only from days since the first reward's snapshot was triggered (2026-09-17 to 2026-11-13, 57 daily changes) |
| O4 | **72%** | Replayed paths on which R5 holds (the float without NEAR's own token is at least $130M), drawing from every day since the first deposit (267 daily changes) |
| O5 | **under 1%** | The same, drawing only from days before the reward programme was announced |
| O6 | **over 99%** | The same, drawing only from days since the first reward's snapshot was triggered |
| O7 | **67%** | Replayed paths on which R2 holds (the ten best days are under 45% of the float), drawing from every day since the first deposit |
| O8 | **$202.6M** | Median float on 2027-03-31 across the replayed paths, drawing from every day since the first deposit (one path in ten ends below $164.8M, one in ten above $252.7M) |
| O9 | **$170.0M** | Median float on 2027-03-31 across the replayed paths, drawing only from days before the reward programme was announced (one path in ten ends below $159.5M, one in ten above $181.5M) |
| O10 | **$258.7M** | Median float on 2027-03-31 across the replayed paths, drawing only from days since the first reward's snapshot was triggered (one path in ten ends below $176.1M, one in ten above $353.0M) |
| O11 | **51% to 60%** | How far O1 moves when the runs are 1, 3, 7, 14 or 30 days long |
| O12 | **38% to 96%** | How far O3 moves when the runs are 1, 3, 7, 14 or 30 days long |
<!-- claims:end -->

C, P, S and K rows are measured here from chain state (P: around NEAR's reward programme; S: shortfalls; K:
custody). V and M rows combine a block-header reading with quoted figures. X and T rows are quoted from
DefiLlama and labelled with their origin; this project does not vouch for them. O rows are not measurements: they
are the output of `make model`, a base rate drawn from the float's own past, and they say so.

## Try it

| Do | See |
| --- | --- |
| `make test` | `OK` after the unit tests. No network. Under a second. |
| `make check` | Every derived file, the table above and the numbers in the page are rebuilt in memory and compared with what is committed; every number in the prose is checked. Ends with `RESULT: PASS`. No network, writes nothing. |
| `make verify` | First re-reads 8 days from a public NEAR archival node (balances, the largest totals, the supply headers, the treasury's keys), then does everything `make check` does. One to three minutes. |
| `make score` | The forward tests in [`PREREG.md`](PREREG.md), each `PASS`, `FAIL`, `UNKNOWN` or `PENDING` until its reading exists. |
| `make model` | How often the long-dated readings R1, R2 and R5 hold when the float's past daily changes are replayed forward to 2027-03-31, for three windows of past days. Seeded: the same numbers on any machine. `python3 -m pipeline.model --help` lists the settings (`--since`, `--until`, `--block`, `--paths`, `--seed`). |
| `make pull` then `make build` | Adds the days since the last committed reading (about 30 requests a day added) and rebuilds, so `make score` can resolve tests whose day has come. |
| `make serve` | The dashboard at <http://localhost:8080>. The command keeps running; stop it with Ctrl-C. |
| `python3 -m pipeline.verify --all` | Re-reads every day. Slow: public nodes allow under one request a second. |

Settings, all optional: `ARCHIVAL_RPC` (another archival node), `RPC_RATE` (requests a second, default 0.7),
`FIRST_DAY` and `OLD_ANCHOR` (where a pull from scratch starts; defaults cover the whole history).

What `make verify` prints, shortened:

```
re-reading 8 days from https://archival-rpc.mainnet.fastnear.com
ok   2026-02-18  block 186012275  0 balances and 0 totals match the chain
ok   2026-10-02  block 218126936  172 balances and 1 totals match the chain
ok   2026-11-13  block 224285109  205 balances and 20 totals match the chain
...
ok   total supply in 5 block headers matches data/context/supply.json
ok   1 key registered for the treasury in intents.near, as in data/context/custody.json
ok   data/derived/series.json is exactly what the data produces
ok   README.md is exactly what the data produces
ok   THESIS.md: all 79 numbers in the prose are computed claims or declared constants
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

1. NEAR's price needs growth: the value of its supply is 265x the revenue that reaches NEAR's wallets, that
   revenue covers 15% of net new supply, and it would have to grow 6.5x to match it.
2. The product that has to grow went private on 27 October. The float is an adoption measure that cannot be
   restated afterwards, and it is up 2.8x since July.
3. It can be inflated while it is read, though. NEAR pays a reward for confidential balances, and 69% of the
   NEAR that arrived in the days after the reward's snapshot was announced has left. Without NEAR's own token
   the float is $92.9M and steadier.
4. The same float is an unpriced risk. For 2 readings in October one token in it was 98% unbacked, which
   matches a published exploit. That was visible because it was on the public ledger; nothing public proves
   the private chain owes what the treasury holds, and 1 key is registered for the treasury, with nothing
   published on whether that key is split.
5. Position: a small holding, an option on private settlement, conditional on dated readings. Replaying the
   float's own past, the main reading (float at least $200M by 2027-03-31) holds on 53% of paths, on under 1% at
   the pace before the reward, and on 82% at the pace since September. See [`THESIS.md`](THESIS.md).

## What the track's example prompt asks for, and where it is

| The prompt asks for | Here |
| --- | --- |
| "Onchain analytics, live dashboards and models anyone can re-run" (the track's description) | The readings are contract calls at pinned blocks (`make verify` repeats them). The hosted dashboard is rebuilt every morning from the new day's reading. `make model` is seeded and prints the same numbers on any machine |
| "One command that rebuilds every chart from raw data" | `make build` rebuilds every series, every quoted number and the dashboard's data from `data/` |
| "A static dashboard page: each chart, the query behind it, and one plain sentence on what it shows" | [`site/`](site/), hosted at the link above. Each chart has a note saying what it shows and a "query behind this chart" block with the contract calls |
| "THESIS.md with the claim, the evidence for it, the evidence against it, and what result would change my mind" | [`THESIS.md`](THESIS.md), sections 1, 3, 4 and 6 |
| "If a metric can't be computed from these sources, write that in THESIS.md" | [`THESIS.md`](THESIS.md), section 7 |
| "Never invent numbers" | `make check` fails on any dollar amount, percentage, multiple or NEAR amount in the prose that the data does not produce |
| SQL against the NEAR BigQuery public dataset | Not used. The thesis is about what sits behind the private chain, which activity tables do not show, and BigQuery needs a billing account, which would end "no key, no account" |
| A pull from the NEAR Intents Explorer API | Not used. It needs a partner key and returns the operator's own figures. Volume and fees are quoted from DefiLlama and labelled as reported |

The prompt's own working hypothesis, that Intents volume leads network usage, is tested by several other entries
in this track. This one asks a different question: what can still be checked now that the volume is private.

## How it works

```
public NEAR archival node
   |  block header at ~00:00 UTC each day            -> data/blocks.json
   |  intents.near.mt_batch_balance_of(treasury)     -> data/float/<day>.json
   |  <token>.ft_balance_of(intents.near)            -> data/held/<day>.json
   v
pipeline/build.py    exact integer and fraction arithmetic -> data/derived/series.json, site/data.js
pipeline/context.py  token list, quoted figures, supply headers, custody -> data/tokens.json, data/context/
pipeline/claims.py   every quoted number                   -> data/derived/claims.json, the table above,
                                                             the numbers written into site/index.html
pipeline/score.py    forward tests written in PREREG.md     -> data/derived/forward.json
pipeline/model.py    replays past daily changes forward     -> the O rows of the table above; prints, writes nothing
pipeline/verify.py   re-read from the chain, rebuild in memory, compare; writes nothing
```

- A reading is tied to a block height, so it never changes: anyone who reads the recorded heights gets the same
  bytes. From 2026-11-14 the day's block is the first one stamped at or after 00:00:00 UTC, so a pull from
  scratch also chooses the same block; earlier days were taken as some block in the first 15 seconds.
- A read that fails is stored as `null` and left out. It is never counted as zero.
- If the treasury is credited with more of a token than the token's contract says `intents.near` holds, that
  reading is left out of the share and listed in `data/derived/anomalies.json` with its size. It is never
  turned into a share above 100%. Two such readings exist, 2026-10-01 and 2026-10-02, for one token.
- Constants and how each was checked: [`docs/SOURCES.md`](docs/SOURCES.md).
- A scheduled workflow (`.github/workflows/daily.yml`) reads the new days every morning, scores the forward
  tests and republishes the dashboard. It commits nothing: main changes only through pull requests, and the
  numbers quoted in the text stay pinned to the block above. Two limits: readings it takes are kept in a build
  cache, not in the repository, until someone merges them; and GitHub pauses scheduled workflows after 60 days
  without repository activity.

## How NEAR fits

The subject is NEAR, and the method only works because of how NEAR is built: `intents.near` is a public
multi-token ledger (NEP-245) with view methods, token contracts follow NEP-141, and archival nodes answer view
calls at any past block. That is what lets a private chain's backing be audited from outside without anyone's
permission.

## Limits

The full list is in [`THESIS.md`](THESIS.md#7-what-could-not-be-computed-and-other-limits). The main ones: dollar figures use one fixed price list;
30 token types have no price and are left out; the 61.0% counts every listed token with a price on the pinned
day, while the history follows the 20 largest and is weekly before 23 October; one reading a day cannot see
money that enters and leaves within the day; the treasury shows assets, not what the private chain owes; the
October shortfall is matched to the published exploit by token, size and time, not by transaction; volume, fees
and revenue are quoted from DefiLlama, not recomputed here.

## What was built for this hackathon

Everything in this repository was written during the hackathon window: all of it on 13 November 2026, which is
why the history is short. No earlier code. Libraries: none beyond the Python standard library; the dashboard is
plain HTML, CSS and JavaScript with no framework. GitHub Actions used: `actions/checkout`,
`actions/setup-python`, `actions/cache`, `actions/configure-pages`, `actions/upload-pages-artifact`,
`actions/deploy-pages`. Fonts: Geist and Geist Mono (SIL Open Font License), in `site/fonts/`. Data sources:
NEAR mainnet through a public archival node, NEAR Intents' public token list, DefiLlama's public API. The code
and text were written with an AI coding assistant (Claude Code) under the author's direction. Before
submission the repository was reviewed twice by independent AI reviewers, and their findings were fixed in
pull request 2.

## Errata

- `PREREG.md` dates its two amendments "about 13:30 UTC" and "about 15:00 UTC" on 2026-11-13. Both times are
  wrong. The commit that contains them was made at 13:07 UTC, and the price list was completed at 12:57 UTC
  (`data/tokens.json`). The file is left byte for byte as it was, because its hash is recorded and timestamped:
  `data/derived/prereg.sha256.ots` is an OpenTimestamps proof that is now confirmed in a Bitcoin block.
- The first version of this README said the October shortfall was found "before its author knew there had been
  a hack" and matched "to the hour". Both overstated it. Every reading was taken on 13 November, five weeks
  after the event; the first data commit flagged the 1 October reading as unexplained, and the match to the
  published incident was made afterwards, by token, size and day.

## Licence

MIT. See [`LICENSE`](LICENSE). The licence holder, Veltri Labs, is the author's team; the repository is under
the author's GitHub account.
