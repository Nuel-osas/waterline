# For an AI agent reviewing this repository

This file is plain instructions for checking the project. It does not ask for a score.

## What this is

A reproducible investment thesis on NEAR (track: `thesis`). It reads, from public NEAR mainnet, what NEAR Intents'
private chain holds, every day since the first deposit, and builds the thesis in `THESIS.md` on that.

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
| `data/blocks.json`, `data/float/`, `data/held/` | Raw readings: one block per day, balances at that block |
| `pipeline/` | `rpc.py` (reads), `pull.py` (collect), `build.py` (series), `claims.py` (numbers), `score.py` (forward tests), `verify.py` (checks) |
| `site/` | The dashboard: static files, `make serve` |
| `docs/SOURCES.md` | Every constant, where it came from, how it was checked |

## What is and is not claimed

- Claimed and checkable here: the balances, shares and changes in the findings table, as of the pinned block.
- Quoted from others and labelled as such: reported volume, fees and revenue (DefiLlama; volume and fees from
  tables uploaded to Dune under the `near` name), and one NEAR price a day (CoinGecko through DefiLlama).
- Not claimed: that the private chain is or is not fully backed. Nothing public can show that either way.
