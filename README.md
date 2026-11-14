# Waterline

**NEAR Intents can be audited from outside, to the last unit, at any block. Its private chain cannot.**
Waterline is that audit, and an investment thesis for NEAR built on it: **Hold, small, to the end of 2029**. Two
questions to two contracts show whether NEAR Intents holds what it has credited. Asked at the pinned block: 214
tokens, $223.8M, none short. Asked over past blocks: the October 2026 exploit is in the public books from ten
dollars, 31 hours 40 minutes before the first payout. The audit stops at one account, the private chain's treasury:
1Click's own records show its swaps settling through it, and it now holds 61.0% of everything.

![The audit run on the latest block from a browser: 20 of 20 tokens whole](docs/audit.png)

**Dated tests, results so far.** Every test was written and hashed before its reading existed. This table is
written by the scoring code, not typed:

<!-- results:start -->
| Test | Reading | Result |
| --- | --- | --- |
| G1: no tracked token is short | 2026-11-14 | **PASS** |
| E1: the float is at least what it was on 2026-11-13 ($136.4M) | 2026-11-14 | **FAIL**: it was $135.2M |
| E2: no single day adds another lump | 2026-11-14 | **PASS** |
| E3: the private share of the tracked tokens is at least 60.0% | 2026-11-14 | **PASS**: 61.9% |

Scored by code and still pending: 4 on the 2026-11-17 reading, 6 on the 2027-03-31 reading. Two more, R4 and D1, are scored by hand on 2027-03-31. `make score` prints every test.
<!-- results:end -->

## The thesis in short

**Rating: Hold, small, to the end of 2029.** Up to 1% of a liquid portfolio, moved by a rule whose inputs this
repository reads from the chain ([`THESIS.md`](THESIS.md), section 5).

1. NEAR Intents' public books can be proven whole by anyone, at any block, in two calls per token. Today they
   are: 214 tokens, $223.8M, none short.
2. The one time they were not, it showed: the October hole was in the books from ten dollars 31 hours 40 minutes before the
   first payout, and above $10,000 1 hour 9 minutes before it. A replay run in November, not live detection; the start time
   is also CertiK's.
3. The swaps now settle through the one account the audit cannot see into: for 9 of 9 completed 1Click swaps we
   found, the swap's own record lists the transaction that moved its tokens into it. That account holds 61.0% of
   everything NEAR Intents holds.
4. NEAR's buyback is funded by revenue we read from the chain: 426,685 NEAR in the last 30 days, 16% of net new supply.
   For buybacks to match new supply by the end of 2029 that revenue, counted in NEAR, has to grow 84% a year, or 59% a year
   if HSP-029 takes effect. Since the buyback began in February it has grown about 107% a year in NEAR, but the
   range is wide: 59% of resamples clear the 2029 pace. Over the latest 30 days against the 30 before it was -17%.
5. What sits behind the private chain is partly paid for and moves in lumps: NEAR pays a reward for confidential
   balances, 94% of the net NEAR that arrived in late September came from one account, and half of the float's
   best day was money the treasury had paid out the evening before.
6. The rule: add, up to 3%, if coverage reaches 25% in two 30-day windows in a row or NEAR publishes the private
   chain's totals; exit if a hole in the public books stays open beyond 3 readings, the audit stops working, or
   coverage falls below 10% in two windows in a row. Dated tests are hashed and scored by code:
   [`PREREG-AUDIT.md`](PREREG-AUDIT.md) for the audit, and [`PREREG.md`](PREREG.md) for this project's first
   question, the growth of the private side.

## Try it

| Do | See |
| --- | --- |
| `make test` | `OK` after the unit tests. No network. Under a second. |
| `make check` | Every derived file, the findings table in `docs/FINDINGS.md` and the numbers in the page are rebuilt in memory and compared with what is committed; every number in the prose is checked. Ends with `RESULT: PASS`. No network, writes nothing. |
| `make verify` | First re-reads 8 days from a public NEAR archival node (balances, the largest totals, the supply headers, the treasury's keys), then does everything `make check` does. Three to fifteen minutes, depending on how hard the public node is rate-limiting. |
| `make tomorrow` | Adds a made-up next day to a temporary copy of the repository and runs the checks there. Prints one `ok` line if no quoted number depends on days after the pinned one. No network, about seven seconds. It is what the daily dashboard job relies on. |
| `make score` | The forward tests in [`PREREG.md`](PREREG.md) and [`PREREG-AUDIT.md`](PREREG-AUDIT.md), each `PASS`, `FAIL`, `UNKNOWN` or `PENDING` until its reading exists. |
| `make audit` | Audits the 20 largest tokens at the latest final block: what `intents.near` has credited against what each token's contract says it holds. Prints one line per token and `RESULT: WHOLE`; exit code 1 and the tokens concerned if any is short; `RESULT: INCOMPLETE` and exit code 2 if any total could not be read. About 25 requests: under a minute on a quiet node, a few minutes when it rate-limits. `python3 -m pipeline.audit` prints the audit of every stored day with no network. |
| `make trace` | Halves the day before the 25 September reading down to the one block where the treasury's NEAR balance jumped, then prints the receipt behind it: who signed it, for how much. About 25 requests to a public archival node, about a minute. `python3 -m pipeline.trace --help` lists the settings (`--account`, `--token`, `--top`). |
| `python3 -m pipeline.revenue` | The three revenue wallets' NEAR balances at the first and last stored day. `--balances` and `--transfers FIRST LAST` read them again from the chain and a public index. No network without a flag. |
| `python3 -m pipeline.oneclick` | The 1Click swaps found whose own records list the transaction into the private chain's treasury. `--scan` looks again (slow). No network without a flag. |
| `python3 -m pipeline.growth` | The upside case: how fast the revenue that funds the buyback has grown since February, counted in NEAR, its 90% range, and the share of resamples that clear the paces needed by 2029 and 2031. Seeded, no network, under a second. |
| `python3 -m pipeline.leadlag` | The test of the track's hypothesis that Intents volume leads network usage: the strongest lead for transactions, active accounts and price, with its p-value. Seeded, no network, a few seconds. |
| `make model` | How often the long-dated readings R1, R2 and R5 hold when the float's past daily changes are replayed forward to 2027-03-31, for three windows of past days. Seeded: the same numbers on any machine. `python3 -m pipeline.model --help` lists the settings (`--since`, `--until`, `--block`, `--paths`, `--seed`). |
| `make pull` then `make build` | Adds the days since the last committed reading (about 30 requests a day added) and rebuilds, so `make score` can resolve tests whose day has come. |
| `make serve` | The dashboard at <http://localhost:8080>. The command keeps running; stop it with Ctrl-C. |
| `python3 -m pipeline.verify --all` | Re-reads every day. Slow: public nodes allow under one request a second. |

Settings, all optional: `ARCHIVAL_RPC` (another archival node), `RPC_RATE` (requests a second, default 0.7),
`FIRST_DAY` and `OLD_ANCHOR` (where a pull from scratch starts; defaults cover the whole history).

The free public archival node answers HTTP 429 when asked for more than about one request a second, and it
counts by address. The code waits and retries, so a busy node makes a command slow, not wrong. Running
`make audit` and `make verify` back to back, or from a shared address, is what makes them slow; `RPC_RATE=0.3`
is gentler. `make test`, `make check` and `make model` use no network.

What `make verify` prints, shortened (from the CI run on 14 November):

```
re-reading 8 days from https://archival-rpc.mainnet.fastnear.com
ok   2026-02-18  block 186012275  0 balances, 5 totals and 17 credited totals match the chain
ok   2026-10-02  block 218126936  172 balances, 5 totals and 20 credited totals match the chain
ok   2026-11-13  block 224285109  205 balances, 20 totals and 214 credited totals match the chain
ok   2026-11-14  block 224435951  205 balances, 5 totals and 20 credited totals match the chain
...
ok   total supply in 5 block headers matches data/context/supply.json
ok   1 key registered for the treasury in intents.near, as in data/context/custody.json
ok   traced case: 4 receipts and 4 balances match the chain (1,730,851 NEAR out of the treasury and back)
ok   exploit replay: credited and held at 3 blocks, each with the block before it, match the chain (the hole opens at block 217799506)
ok   data/derived/series.json is exactly what the data produces
ok   data/context/flows.json: on 20 of 20 days the listed transfers add up exactly to the change in the chain balance
ok   THESIS.md: all the numbers in the prose are computed claims or declared constants
ok   PREREG-AUDIT.md matches its recorded hash
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

It prints the private chain's wNEAR balance at that block, in yoctoNEAR. If it prints a `KeyError`, the node
rate-limited the call: wait a few seconds and run it again. The same value is in
`data/float/2026-11-13.json`.

## The problem

NEAR's investment case leans on NEAR Intents. On 27 October 2026, NEAR Intents' 1Click swaps began to settle on
a private chain. The docs describe it as "a permissioned instance of the NEAR protocol operated by a small
validator set with no public networking", where a swap is "invisible to public indexers".

The volume and fee figures that investors quote have come from NEAR-run sources since 2025. Until 27 October an
outsider could in principle cross-check them against public settlement in `intents.near` (we did not). Since
then the swap leg is private. A thesis "judged on the evidence" needs evidence that does not depend on the party being valued.

## What this is

Two things about NEAR Intents are still fully public. Its ledger, `intents.near`, says what it has credited for
each token. Each token's own contract says what that ledger holds. And the tokens that back the private chain
sit in one account on that ledger. Waterline reads all three at one block per day and builds:

- the revenue that funds NEAR's buyback, read from the chain: 426,685 NEAR in the last 30 days, every wallet reconciled
  against its balance, and a rating computed from it by a stated rule;
- a record, from 1Click's own status records and the chain, that its swaps settle through the private chain's
  treasury (9 of 9);
- a test of the track's hypothesis that Intents volume leads network usage: it does not, in this data;
- an audit of the public books: credited against held, token by token, at the pinned block, on every stored
  reading, and at the latest block on demand (`make audit`, or the button on the dashboard);
- a second, stricter test in the same audit: whether what a token holds over its credit fell below every
  earlier reading. It fires on the three readings of the exploit and on no other;
- a block-by-block replay of the one time the books were short, the October 2026 exploit, from ten dollars to
  $3.8M and back to whole;
- a daily history of the money behind the private chain (the float), in tokens and in dollars at fixed prices,
  and the share of everything NEAR Intents holds that is now private;
- the float read against NEAR's own reward programme for confidential balances;
- a tracer that finds, from balances alone, the block and the receipt behind the largest move of a day:
  `make trace`. It shows that half of the float's best day was money the treasury had paid out the evening before;
- a list of who moved NEAR in and out of the treasury in September, taken from a public index and used only on
  days where it adds up to the chain: `python3 -m pipeline.flows`;
- an investment thesis on NEAR that states which of its inputs are observed and which are reported, and the
  readings that would change it: [`THESIS.md`](THESIS.md);
- forward tests written before their readings exist, scored by code: [`PREREG.md`](PREREG.md);
- a seeded model anyone can re-run, which replays the float's past daily changes forward and counts how often
  the thesis's long-dated readings hold: `make model`;
- a dashboard that shows all of it: `make serve`.

No key, no account, no package to install. Python 3.9 or newer: the tests and the offline check were run under
3.9.6 and 3.15 locally, and CI uses 3.12.

## Findings

Every number the README, the thesis and the dashboard quote is one row of a table, written by
`pipeline/claims.py` from the raw readings and rebuilt and compared by `make check`: [`docs/FINDINGS.md`](docs/FINDINGS.md).
Each row says what the number is and how it is computed, and which numbers are measured, quoted or modelled.

## What the track's example prompt asks for, and where it is

| The prompt asks for | Here |
| --- | --- |
| "Onchain analytics, live dashboards and models anyone can re-run" (the track's description) | The readings are contract calls at pinned blocks (`make verify` repeats them). The hosted dashboard is rebuilt every morning from the new day's reading, and its audit button reads the latest block from the visitor's browser. `make model` is seeded and prints the same numbers on any machine |
| "One command that rebuilds every chart from raw data" | `make build` rebuilds every series, every quoted number and the dashboard's data from `data/` |
| "A static dashboard page: each chart, the query behind it, and one plain sentence on what it shows" | [`site/`](site/), hosted at the link above. Each chart has a note saying what it shows and a "query behind this chart" block with the contract calls |
| "THESIS.md with the claim, the evidence for it, the evidence against it, and what result would change my mind" | [`THESIS.md`](THESIS.md), sections 1, 3, 4 and 6 |
| "If a metric can't be computed from these sources, write that in THESIS.md" | [`THESIS.md`](THESIS.md), section 7 |
| "Never invent numbers" | `make check` fails on any dollar amount, percentage, multiple or NEAR amount in the prose that the data does not produce |
| The prompt's working hypothesis, that NEAR Intents' volume leads network usage | Tested, and not supported in this data: `python3 -m pipeline.leadlag`, [`THESIS.md`](THESIS.md) section 2 (r = -0.11, p = 0.96 for transactions, r = +0.09, p = 0.88 for active accounts, r = -0.12, p = 0.74 for price, over 98 weekly changes) |
| SQL against the NEAR BigQuery public dataset | Not used. It needs a Google Cloud account (the free sandbox needs no card), which would end "no key, no account". NearBlocks' public daily counts give the same activity series without one, and the lead-lag test uses them |
| A pull from the NEAR Intents Explorer API | Not used. It needs a partner key and returns the operator's own figures. Volume and fees are quoted from DefiLlama and labelled as reported |

## How it works

```
public NEAR archival node
   |  block header at ~00:00 UTC each day            -> data/blocks.json
   |  intents.near.mt_batch_balance_of(treasury)     -> data/float/<day>.json
   |  <token>.ft_balance_of(intents.near)            -> data/held/<day>.json
   |  intents.near.mt_batch_supply(token_ids)        -> data/credited/<day>.json
   v
pipeline/build.py    exact integer and fraction arithmetic -> data/derived/series.json, site/data.js
pipeline/context.py  token list, quoted figures, supply headers, custody -> data/tokens.json, data/context/
pipeline/claims.py   every quoted number                   -> data/derived/claims.json, docs/FINDINGS.md,
                                                             the numbers written into site/index.html
pipeline/score.py    forward tests written in PREREG.md     -> data/derived/forward.json
pipeline/audit.py    credited (mt_batch_supply) against held  -> data/credited/<day>.json, data/context/exploit.json, the A rows
pipeline/flows.py    an index's transfer list, kept where it adds up -> data/context/flows.json, the N rows
pipeline/revenue.py  the revenue wallets: balances and transfers   -> data/context/revenue.json, the U rows and the rating
pipeline/oneclick.py 1Click swaps that settle through the treasury -> data/context/oneclick.json, W5
pipeline/leadlag.py  does Intents volume lead usage or price?      -> the L rows; prints, writes nothing
pipeline/growth.py   the revenue's trend in NEAR since February   -> the GR rows; prints, writes nothing
pipeline/model.py    replays past daily changes forward     -> the O rows of the findings table; prints, writes nothing
pipeline/trace.py    halves a day to the block of a move, reads its receipts -> data/context/trace.json (one case, re-read by make verify)
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
- A scheduled workflow (`.github/workflows/daily.yml`) reads the new days, audits them, scores the forward
  tests and republishes the dashboard. GitHub's schedules are best effort, and here they run late.
  On the first night, 14 November, nothing started at 00:20 UTC or, after the job was given four schedules a
  day, at 02:47 UTC; by 03:36 UTC no scheduled run had ever started. The first one began at 06:25 UTC and
  passed. GitHub reported no incident. So expect the page to gain a new day some hours after midnight UTC, not
  minutes after. Runs started by a push to `main` or by hand also pass, and anyone with write access can start
  one from the Actions tab ("dashboard", "Run workflow") or with `gh workflow run dashboard`. It commits nothing: main changes only through pull requests, and the
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
day, while the history follows the 20 largest, one reading a day; one reading a day cannot see
money that enters and leaves within the day; the treasury shows assets, not what the private chain owes; the
October shortfall is matched to the published exploit by token, size and time, not by transaction; volume and fees are quoted from DefiLlama; revenue is read from the chain for the last two
30-day windows.

## What was built for this hackathon

Everything in this repository was written during the hackathon window, on 13 and 14 November 2026, which is why
the history is short. No earlier code. Libraries: none beyond the Python standard library; the dashboard is
plain HTML, CSS and JavaScript with no framework. GitHub Actions used: `actions/checkout`,
`actions/setup-python`, `actions/cache`, `actions/configure-pages`, `actions/upload-pages-artifact`,
`actions/deploy-pages`. Fonts: Geist and Geist Mono (SIL Open Font License), in `site/fonts/`. Data sources:
NEAR mainnet through a public archival node, NEAR Intents' public token list, DefiLlama's public API, CertiK's
published incident report (three quoted times), and FastNEAR's transfers index for the list of September NEAR
transfers and one hop of the transfer that was followed. The dashboard's audit button asks three public NEAR nodes from the visitor's browser. The code
and text were written with an AI coding assistant (Claude Code) under the author's direction. Before
submission the repository was reviewed several times by independent AI reviewers. Their findings were fixed in
pull requests 2, 4, 5, 10, 11, 13, 14 and 16, and one review's proposal, to audit the whole ledger and not one
account, is pull request 8.

## Errata

Every correction made since the first version is listed in [`docs/ERRATA.md`](docs/ERRATA.md).

## Another project by the same author

The author is also entering one other, independent project in this hackathon: CopyLaunch, in the Memecoins and
DeFi tracks. The two share no code and no data. (Rule Q-015 asks each project's README to name the other.)

## Licence

MIT. See [`LICENSE`](LICENSE). The licence holder, Veltri Labs, is the author's team; the repository is under
the author's GitHub account.
