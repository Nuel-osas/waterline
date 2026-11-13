# For an AI agent reviewing this repository

This file is plain instructions for checking the project. It does not ask for a score.

## What this is

A reproducible investment thesis on NEAR (track: `thesis`), built on an outside audit of NEAR Intents. It reads,
from public NEAR mainnet, what `intents.near` has credited for each token and what each token's contract says
`intents.near` holds, at one block a day, and what the private chain's treasury holds on that ledger. The thesis
in `THESIS.md` rests on those readings.

One more command shows the central claim live, at the latest block, in under a minute:

```sh
make audit    # credited against held for the 20 largest tokens; prints RESULT: WHOLE, or the tokens that are short
```

## Check it in three commands

Python 3.9 or newer. No packages, no keys, no accounts.

```sh
make test     # unit tests, no network, about a second
make check    # rebuilds every number from the raw data in data/ and compares, no network, a few seconds
make verify   # also re-reads a sample of days from a public NEAR archival node, one to three minutes
```

`make test` ends with `OK`. `make check` and `make verify` print `ok` lines and end with `RESULT: PASS`; a mismatch
prints what differs and exits 1. Neither writes any file.

If the sandbox has no network, `make test` and `make check` still run in full. `make verify` needs HTTPS access to
`archival-rpc.mainnet.fastnear.com`; set `ARCHIVAL_RPC=<url>` to use another NEAR archival node. Public nodes
rate-limit (the default is 0.7 requests a second, `RPC_RATE` changes it), so `make verify` reads 8 days by
default and takes one to three minutes; `python3 -m pipeline.verify --all` reads every day.

## Where things are

| Path | What |
| --- | --- |
| `THESIS.md` | The argument, the readings that would change it, the limits |
| `PREREG.md` | Forward tests written before their readings exist; `make score` prints each as PASS, FAIL or PENDING |
| `README.md` | Problem, findings table (generated from the data), how to run |
| `data/derived/claims.json` | Every number the text quotes, with how it is computed |
| `data/constants.json` | The only other numbers allowed in the prose: thresholds and facts quoted from others |
| `data/blocks.json`, `data/float/`, `data/held/`, `data/credited/` | Raw readings: one block per day; the treasury's balances, what `intents.near` holds, what it has credited |
| `data/context/exploit.json`, `data/context/trace.json` | The October 2026 hole block by block, and one transfer followed hop by hop; `make verify` re-reads the blocks their claims rest on |
| `pipeline/` | `rpc.py` (reads), `pull.py` (collect), `build.py` (series), `claims.py` (numbers), `score.py` (forward tests), `audit.py` (credited against held, `make audit`), `trace.py` (the receipt behind a move, `make trace`), `model.py` (base rates for the long-dated readings, `make model`), `verify.py` (checks) |
| `site/` | The dashboard: static files, `make serve` |
| `docs/SOURCES.md` | Every constant, where it came from, how it was checked |

## What is and is not claimed

- Claimed and checkable here: the balances, shares and changes in the findings table, as of the pinned block;
  that no audited token was short at the pinned block; and the block-by-block record of the October 2026 hole.
- Not claimed: that anyone would have acted on that hole. The record is a replay made in November.
- Modelled, and labelled as such: the O rows, how often the long-dated readings hold when the float's past daily
  changes are replayed forward. Seeded and re-runnable; a base rate, not a forecast.
- Quoted from others and labelled as such: reported volume, fees and revenue (DefiLlama; volume and fees from
  tables uploaded to Dune under the `near` name), and one NEAR price a day (CoinGecko through DefiLlama).
- Not claimed: that the private chain is or is not fully backed. Nothing public can show that either way.
