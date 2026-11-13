# Written down before the result

Written on 2026-11-13, when the last reading the authors had seen was block 224285109 (2026-11-13, 00:00 UTC).
Every test below is scored by `python3 -m pipeline.score` from block-pinned readings taken later, at the fixed
prices in `data/tokens.json`. The thresholds are written here and are constants in `pipeline/score.py`. The
hashes of both files are in `data/derived/prereg.sha256` and are checked by `make check`, so neither can change
without it showing.

A test is `PASS` or `FAIL` once its reading exists, `PENDING` before that, and `UNKNOWN` if the reading exists
but not every tracked total could be read: a share over only some of the tracked tokens is not the share that
was written down.

## Scored on the 2026-11-14 reading (before the submission deadline)

| # | Test | Why it matters | How often it held before |
| --- | --- | --- | --- |
| E1 | The float on the 2026-11-14 reading is at least what it was on 2026-11-13 ($136.4M). | It keeps growing. | 63% of single days |
| E2 | The day between the two readings does not add more than the tenth-largest rise so far ($4.7M). | Growth, if any, is not one more lump. | |
| E3 | The private share of the tracked tokens on the 2026-11-14 reading is at least 60.0% (62.3% on 2026-11-13). | Money is not moving back to the public side. | |

One day is noise as much as signal. These are here so that at least one result exists, written before it was
known, when the project is judged.

## Scored on the 2026-11-17 reading (during judging)

| # | Test | How often it held before |
| --- | --- | --- |
| F1 | The float on the 2026-11-17 reading is at least what it was on 2026-11-13 ($136.4M). | 58% of four-day windows since the July launch |
| F2 | No single day between the two readings adds more than the tenth-largest rise so far ($4.7M). | 79% of four-day windows since the July launch |
| F3 | The private share of the tracked tokens on the 2026-11-17 reading is at least 60.0%. | |

These are close to coin flips on their base rates, and we say so. A fail will be reported as a fail.

## Long-dated: scored on the 2027-03-31 reading

| # | Test |
| --- | --- |
| R1 | The float is at least $200M. |
| R2 | The ten best days are less than 45% of the float. |
| R3 | The private share of the tracked tokens is at least 50%. |
| R5 | The float without NEAR's own token is at least $130M. |

R4 in `THESIS.md` uses a figure this repository does not compute itself (revenue reaching NEAR's wallets, from
DefiLlama), so it is scored by hand and is not in the table above.

## Amendments

Both were made on 2026-11-13, the same day the file was first written and before any later reading existed.
The first version is in the repository's history (commit `f572586`). No threshold was changed.

1. About 13:30 UTC: added E1 to E3 (an earlier checkpoint with the same thresholds as F1 to F3) and R5 (the
   float without NEAR's own token), after we learned that NEAR pays a reward for confidential balances.
2. About 15:00 UTC: the price list was completed (NEAR Intents' own list showed more ids later in the day), which
   moved the pinned day's float from $132.3M to $136.4M and the tracked share from 61.8% to 62.3%. The tests
   compare later readings with the pinned day's at the same prices, so the tests themselves are unchanged; the
   figures quoted in them were updated. Base rates were added.

## How the date of this file can be checked

- `data/derived/prereg.sha256` holds the SHA-256 of this file and of `pipeline/score.py`.
- The repository's public history on GitHub shows when each version was pushed.
- `data/derived/prereg.sha256.ots` is an OpenTimestamps proof for that hash file: it commits the hashes to the
  Bitcoin blockchain through public calendar servers, with no account of ours involved. `ots verify` checks it
  once the calendar has been included in a block, a few hours after stamping.
- Not done: an anchor on NEAR itself. That needs a signed transaction from an account the authors control.
