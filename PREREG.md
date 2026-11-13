# Written down before the result

Written on 2026-11-13, when the last reading the authors had seen was block 224285109 (2026-11-13, 00:00 UTC).
Every test below is scored by `python3 -m pipeline.score` from block-pinned readings taken later, at the fixed
prices in `data/tokens.json`. The thresholds are constants in `pipeline/score.py`; changing one changes this
file's hash.

## Near-term: scored on the 2026-11-17 reading

| # | Test | Why it matters |
| --- | --- | --- |
| F1 | The float on the 2026-11-17 reading is at least what it was on 2026-11-13 ($132.3M). | "It compounds." |
| F2 | No single day between the two readings adds more than the tenth-largest rise so far ($4.7M). | Growth, if any, is not one more lump. |
| F3 | The private share of the tracked tokens on the 2026-11-17 reading is at least 60.0% (61.8% on 2026-11-13). | Money is not moving back to the public side. |

Four days is a short window and these can fail on noise. A fail will be reported as a fail.

## Long-dated: scored on the 2027-03-31 reading

| # | Test |
| --- | --- |
| R1 | The float is at least $200M. |
| R2 | The ten best days are less than 45% of the float. |
| R3 | The private share of the tracked tokens is at least 50%. |

A fourth long-dated reading, R4 in `THESIS.md`, uses a figure this repository does not compute itself (revenue
reaching NEAR's wallets, from DefiLlama), so it is scored by hand and is not in the table above.

## How the date of this file can be checked

- The file's SHA-256 is in `data/derived/prereg.sha256` and is checked by `make check`.
- The same hash is in the first commit that contains this file, and in the public demo post for the
  hackathon, which carries its own timestamp.
- Not done: an on-chain anchor. Writing the hash to NEAR mainnet needs a signed transaction from an account
  the authors control; if it is added later, the transaction hash goes here.
