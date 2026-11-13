# Forward tests for the audit

Written on 2026-11-13 at 20:50 UTC, before the 2026-11-14 reading existed. The hashes of this file and of
`pipeline/score_audit.py` are in `data/derived/prereg_audit.sha256`, with an OpenTimestamps proof beside it, and
the pull request that added them was opened on GitHub before 00:00 UTC on 14 November. Neither file is edited
after that. `make score` prints each test as `PASS`, `FAIL`, `UNKNOWN` or `PENDING`.

## Why a second file

[`PREREG.md`](PREREG.md), written and hashed earlier the same day, asks whether the money behind the private
chain keeps growing. That was this project's first question. The thesis now leads with a different claim: the
public books of NEAR Intents can be proven whole from outside, and when they are not, it shows and it is closed.
A review pointed out that no dated test covered that claim. These do.

## The tests

A token is short on a reading when `intents.near` has credited more of it than the token's own contract says
`intents.near` holds, at the day's block. The tokens are the tracked ones in `data/tracked.json`.

| # | Test | Scored on |
| --- | --- | --- |
| G1 | No tracked token is short on the 2026-11-14 reading | that reading |
| G2 | No tracked token is short on the 2026-11-17 reading | that reading |
| G3 | From 2026-11-14 to 2027-03-31, any tracked token found short on a reading is whole again within 3 readings | 2027-03-31, or earlier: it fails on the first reading that breaks it |
| G4 | On the 2027-03-31 reading both questions can still be asked for every tracked token | that reading |

One more item is scored by hand, because no contract can answer it:

| # | Test | Scored on |
| --- | --- | --- |
| D1 | NEAR has published what the private chain owes, per token, in a form that can be set against the treasury's balance at a block height | 2027-03-31 |

D1 is the disclosure that would extend the audit to everything. If it is met we would hold more. If it is not,
the claim about the public books stands and the position stays small.

## Rules

- A reading on which a tracked token's credited or held total could not be read is `UNKNOWN`. It is never a pass.
- The thresholds are constants in `pipeline/score_audit.py`: the three dates above and the 3 readings of G3.
- A fail is reported as a fail, in the README and on the dashboard, on the day it is scored.

## Base rates, said plainly

G1 and G2 are likely to pass. On the readings stored when this was written, a hole was found on three, all in
one token during one exploit, and every other reading was whole. They are written down anyway, because a fail
would be the most important thing this project could report.

G3's threshold is the October precedent: short on three daily readings, whole on the fourth.

G4 fails if the ledger stops answering `mt_batch_supply`, or a tracked token's contract stops answering for
`intents.near`. Either would end the audit, and with it the reason this thesis gives for holding.

## What these tests cannot see

A hole smaller than the surplus a token already carries. A hole that opens and closes between two daily
readings. Anything on the private chain.
