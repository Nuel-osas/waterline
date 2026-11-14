# Errata

Corrections made since the first version of this repository, newest last. A correction is listed here and made in
place; nothing is removed silently.

- `PREREG.md` dates its two amendments "about 13:30 UTC" and "about 15:00 UTC" on 2026-11-13. Both times are
  wrong. The commit that contains them was made at 13:07 UTC, and the price list was completed at 12:57 UTC
  (`data/tokens.json`). The file is left byte for byte as it was, because its hash is recorded and timestamped:
  `data/derived/prereg.sha256.ots` is an OpenTimestamps proof that is now confirmed in a Bitcoin block.
- The first version of this README said the October shortfall was found "before its author knew there had been
  a hack" and matched "to the hour". Both overstated it. Every reading was taken on 13 November, six weeks
  after the event; the first data commit flagged the 1 October reading as unexplained, and the match to the
  published incident was made afterwards, by token, size and day.

- `THESIS.md` called HSP-029 a proposal that "would" lower issuance. It had been approved by NEAR's House of Stake
  on 2 November 2026, before the thesis was written; it is not yet in force. Corrected in pull request 20.
- `THESIS.md` said that 1Click's settlement through the treasury was "our inference". It is now shown from
  1Click's own records for 9 swaps, each transfer read back from the chain (pull request 20).
- Until pull request 8 this project measured the October hole only against the private chain's own credit and
  reported it as 2 readings, 25% and then 98% of that credit, $3.3M. Against everything `intents.near` had
  credited in that token it is three readings and $3.8M at the largest daily reading. Both are in the table (the
  S rows and the A rows); the text now uses the second. The project was also first published as a reading of
  the private chain's balance. A review pointed out that NEAR already publishes that balance as a metric; the
  audit of the whole ledger was added on the same day and the thesis rebuilt around it.

- Until pull request 15 the history of the 20 tracked tokens had one reading a week before 23 October, and three
  figures were taken from the nearest weekly reading. With a reading for every day they are read on the day
  itself: the tracked share is 5% on 1 April (was 6%, from 2 April) and 36.0% on 13 July (was 36.2%, from
  16 July), and the public side on 1 April is $86.0M (was $83.5M). The audit's count rose from 1,090 checks on
  70 readings to 4,806 on 269, with the same three short.

- `make score` prints the result of E2 as "largest one-day rise $-1.2M". The largest change that day was a fall of
  $1.2M, so the test passed. The wording comes from `pipeline/score.py`, which is hashed and is not edited; the
  README's results table and the dashboard say it plainly.
- The position rule in `THESIS.md` first said to hold none if the float without NEAR's own token fell below its
  pinned level. One day later it had ($91.1M against $92.9M). A reviewer pointed out that the rule did not say
  when it was read. The trigger was removed in pull request 16, with the reason given in section 5.
- Pull request 22 said that the revenue funding the buyback had grown about 107% a year in NEAR since February,
  with a resampled range and odds of clearing the pace 2029 needs, and called that the reason to hold rather than
  exit. The rate depends on the week the fit starts from: from -91% to +1,160% a year over the starts that leave
  at least twelve weeks. The first complete week paid 25,228 NEAR a day and the latest 12,969 NEAR a day. The
  figure, its range and the odds are withdrawn (pull request 23). The rule that sets the rating never used them.
- `THESIS.md` and the README said "9 of 9 completed" 1Click swaps; 8 completed and 1 was refunded. They also did
  not say that the nine were found among accounts paying into the treasury, so they show the route and not a
  share of swaps. Corrected in pull request 24.
- `THESIS.md` section 5 gave the multiple revenue must grow by (6.5x), the volume it implies and the 1.6% case on
  DefiLlama's revenue, while the rating uses the chain's. They are now on the chain's basis: 6.2x, $283B a year
  and 4.0x (pull request 24). Section 4 set DefiLlama's revenue change beside reported volume and fees; it now
  gives the chain's, -17% (pull request 24).
- `THESIS.md` section 2 said volume "says little" about activity without giving the same-week correlation with
  transactions, r = +0.27. It is now stated (pull request 24).
