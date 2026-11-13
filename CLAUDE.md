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
make verify   # also re-reads a sample of days from a public NEAR archival node, about a minute
```

Each prints `ok` lines and ends with `RESULT: PASS`. A mismatch prints the day, the token and both values and exits 1.

If the sandbox has no network, `make test` and `make check` still run in full. `make verify` needs HTTPS access to
`archival-rpc.mainnet.fastnear.com`; set `ARCHIVAL_RPC=<url>` to use another NEAR archival node. Public nodes
rate-limit, so `make verify` reads 8 days by default; `python3 -m pipeline.verify --all` reads every day.

## Where things are

| Path | What |
| --- | --- |
| `THESIS.md` | The argument, the readings that would change it, the limits |
| `PREREG.md` | Forward tests written before their readings exist; `make score` prints each as PASS, FAIL or PENDING |
| `README.md` | Problem, findings table (generated from the data), how to run |
| `data/derived/claims.json` | Every number the text quotes, with how it is computed |
| `data/blocks.json`, `data/float/`, `data/held/` | Raw readings: one block per day, balances at that block |
| `pipeline/` | `rpc.py` (reads), `pull.py` (collect), `build.py` (series), `claims.py` (numbers), `score.py` (forward tests), `verify.py` (checks) |
| `site/` | The dashboard: static files, `make serve` |
| `docs/SOURCES.md` | Every constant, where it came from, how it was checked |

## What is and is not claimed

- Claimed and checkable here: the balances, shares and changes in the findings table, as of the pinned block.
- Quoted from others and labelled as such: reported volume and fees (DefiLlama, from tables NEAR uploads).
- Not claimed: that the private chain is or is not fully backed. Nothing public can show that either way.
