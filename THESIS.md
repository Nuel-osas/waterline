# Waterline: a NEAR thesis built on an outside audit

Pinned to NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). Every number in this file is either computed
from the data (`data/derived/claims.json`) or a declared constant (`data/constants.json`). `make check` fails
if a dollar amount, a percentage, a multiple, a NEAR amount, a count of tokens, checks or readings, or a span of
hours here is neither. It does not check dates, clock times, block heights or numbers written as words.

The track's example prompt asks for four things in this file: the claim, the evidence for it, the evidence
against it, and what result would change our mind. They are sections 1, 3, 4 and 6. Section 7 says what could
not be computed.

## 1. The claim

NEAR's buyback is funded by the revenue of one product, NEAR Intents: $1.8M reached NEAR's wallets in the last
30 days. That product
keeps its books on a public ledger, `intents.near`, and anyone can audit them with two questions asked at the
same block: ask the ledger what it has credited for a token, and ask the token's own contract what the ledger
holds. We asked both for 214 tokens worth $223.8M at the pinned block. None is short. We asked both across the
history, and the books were short on three readings, for one token, during an exploit that was later
published. Replayed block by block, that hole was in the public books 31 hours 40 minutes before the first
payout.

On 27 October 2026, 1Click swaps began to settle on a private chain. By NEAR's docs, what backs that chain is
one account on the public ledger (that 1Click's settlement uses this same account is our inference; section 7). The audit sees that account's balance and nothing behind it, and it is now 61.0% of
everything NEAR Intents holds.

**Our claim: NEAR Intents' public books can be proven whole by anyone, at any block, and that is worth
something to a holder. The same proof does not reach the private chain, where most of the money now is. Until
it does, NEAR is worth holding as a small position, not as a cash-flow asset.**

We hold it loosely, because NEAR pays a reward for keeping money on the private side, the largest inflow there
has mostly left again, and the one time the backing broke, most of the broken credit belonged to the private
chain.

## 2. Why the usual numbers stopped being enough

NEAR Intents runs two ledgers. `intents.near` is public. FAR is, in the docs' words, "a permissioned instance of
the NEAR protocol operated by a small validator set with no public networking". The changelog entry for the
day, in full:

> From October 27, 2026, 1Click swaps settle confidentially. The API is unchanged. As an integrator, you don't
> need to change anything. Swap data stays on the NEAR Intents Explorer, so this does not mean that 1Click is
> only Confidential Intents. The swap settles on the NEAR Private Shard, so `nearTxHashes` has no hash for the
> swap. It has the hashes for the shield and the unshield instead.

So the swap is no longer a public transaction, but the money going in (shield) and coming out (unshield) still
is, and so is the account that holds it in between.

The volume and fee figures most people quote did not start coming from NEAR on that day. DefiLlama's adapter
history shows volume taken from a NEAR-run source since May 2025 and fees from tables uploaded to Dune under
the `near` name since November 2025. What 27 October removed is the possibility of a cross-check: until then an
outsider could in principle compare those figures with public settlement in `intents.near`. We did not do that,
and by our own reading 56.2% of what NEAR Intents held was already private the day before.

| Number | Latest value | Where it comes from | Can an outsider recompute it from the chain? |
| --- | --- | --- | --- |
| Swap volume, 30 days | $3.73B | A table uploaded to Dune under the `near` name, read by DefiLlama; also NEAR's own Explorer | Not the swap leg. Shield and unshield flows yes, with an indexer; not done here |
| Gross fees, 30 days | $6.0M | Tables uploaded to Dune under the `near` name | No |
| Revenue reaching NEAR's wallets, 30 days | $1.8M | NEAR received by three public wallets | Yes, with an indexer; quoted here |
| Net new NEAR supply | 88,704 NEAR a day | Block headers | Yes, this repository |
| Private float | $136.4M | Balances of one account in `intents.near` | Yes, this repository |
| Backing of the public books | $223.8M, none short | The ledger's credited totals against each token's own contract | Yes, this repository, and a button on the dashboard |

We are not saying the uploaded numbers are wrong. They are reported, not observed, and a thesis should say which
of its inputs are which. Sources for every row: `docs/SOURCES.md`.

The float is every token held in `intents.near` by the treasury account that backs the private chain. We read it
at one block a day since the account was created. Dollar figures use one fixed price list, so a change in the
series is a change in tokens, not in prices.

## 3. The evidence for the claim

**The public books can be audited, and they are whole.** `intents.near` answers `mt_batch_supply`: the total it
has credited for each token, to all accounts together. Each token's own contract answers how much
`intents.near` holds. At the pinned block we asked both for every token in NEAR Intents' list that has a balance
to read: 214 tokens, $223.8M. Most are equal to the last unit. The rest hold slightly more than is credited,
$6,321 in all. None is short. `python3 -m pipeline.audit --now` repeats this at the latest block, and so does a
button on the dashboard, from the reader's own browser.

**Across the history they were short once.** The same audit on every stored reading since February, for the 20
largest tokens, one reading a day: 4,806 checks, 3 of them short. All three are one token, a dollar token bridged from BNB Chain, on
30 September, 1 October and 2 October. On the last of them `intents.near` held 67,669 of it against 3,869,502
credited: a hole of $3.8M, 98% of everything credited in that token.

A stricter test gives the same answer. Many tokens hold a little more than is credited, and a hole smaller than
that surplus would not turn the sign. So we also ask whether held minus credited fell below every earlier
reading of the same token. Across the same checks that happened on 3 new lows: the same three readings, and no
others. Tokens that arrive without a credit only add to the surplus, so in ordinary running it does not make
new lows, and when it did, something owed had left.

**That hole showed before the money left.** We replayed those days block by block. The hole opens at block
217799506, stamped 16:14:22 UTC on 29 September, at ten dollars. CertiK dates the first exploit transaction to
16:14:19 that day, three seconds earlier, and places the fault in NEAR Intents' own deposit handling: a refund
that returned the tokens and left the credit. The first payout from the bridge's treasury on BNB Chain comes
31 hours 40 minutes after the hole opens. For 28 hours of that the hole is under $3,000. It passes $10,000 about
an hour before the first payout, $100,000 half an hour before, and $1.0M 13 minutes before. It peaks at $3.8M
and the books stay short for 76 hours. They are whole again on the evening of 2 October, minutes before the
contract upgrade CertiK records, and the credited total does not fall while the hole closes. That is consistent
with the statement, which CertiK reports and does not verify, that the money was returned in full. What we see
is the balance on NEAR being refilled, not the tokens on BNB Chain.

This is a replay, run on 13 November, five weeks after the event. It is not live detection, and we do not say
anyone would have acted. The start time is CertiK's finding too; what the replay adds is that the hole could be
seen and sized from outside, with two calls to two contracts, at every step: small for a day, large for the
last hour.

The rest of this section is about the one account the audit cannot see into: what it holds, read from outside.

**It is large and it grew.** First reading with a balance: 2026-02-19. $49.3M at the B2B launch on 13 July.
$136.4M on the pinned day, 2.8x in four months, across 205 token types. That is also the highest it has been.

**Most of NEAR Intents is already behind it.** On the pinned day we asked the contract of every token in NEAR
Intents' own token list how much `intents.near` holds: 180 tokens with a price, $223.8M in total. The private
side is 61.0% of that. It is not even across assets: NEAR 69.9%, stablecoins 68.2%, ZEC 60.3%, ETH 57.5%, and
bitcoin only 28.8%.

Through time we follow the 20 largest tokens by total held, which cover 89% of that total. Their private share
was 5% at the start of April, 36.0% at the July launch, 56.2% the day before the switch and 62.3% on the
pinned day. Over the same months the public side did not grow: $86.0M in April, $75.0M now. The growth was on
the private side.

**It is not only NEAR's own token.** Stablecoins are the largest group (Stablecoins: $49.3M) ahead of NEAR's own
token (NEAR: $43.5M). 68% of the float is not NEAR's own token. We do not know who the depositors are.

**Without NEAR's own token it is steadier, and it kept growing after the first reward closed.** That part was
$46.1M when the first reward's snapshot was announced and is $92.9M now, 3.5x since the July launch, and its
worst day ever is a fall of $2.7M. The whole float grew by $7.9M per 30 days before the reward programme,
$14.3M per 30 days while the first reward was open, and $31.8M per 30 days since.

**It is the account NEAR means.** NEAR announced on 17 September that confidential balances had passed $70M at
that day's prices. Our reading of this account that day, at our fixed prices, is $76.0M. With NEAR's own token
at each day's price it is $68.3M on the 17 September reading and $74.1M on the next: it crosses $70M on the day
of the announcement.

## 4. The evidence against the claim

**The audit stops at the private chain.** 61.0% of what NEAR Intents holds is credited to one account, the
private chain's treasury. The audit proves the tokens are there. It cannot say who they are owed to, or whether
the private chain has promised more than the treasury holds, because no contract answers that question. And
the October hole fell mostly on that side: 87% of the credit in the broken token belonged to the treasury.
Nothing public says how such a loss would have been shared among the private chain's users.

**Part of the float is paid for.** On 11 June 2026 NEAR announced a reward for holding a confidential balance: a
pool of locked tokens that convert to NEAR, shared among wallets that keep more than $100 there and make at
least one confidential swap, with the snapshot taken once confidential balances reach $70M and no wallet
receiving more than 2%. On 17 September NEAR announced that the $70M had been reached and the snapshot
triggered. A second round is promised. With another round promised, nobody outside can separate use from
reward-seeking, and we do not claim to.

**The NEAR in it came late and mostly left.** The ten best days add up to $75.5M, which is 55% of the float.
The treasury held 8.5M NEAR on the day NEAR announced that the snapshot had been triggered. Between the readings
of 15 and 28 September 12.6M NEAR entered, nearly all of it after that announcement, so it was not positioned
for the first reward. In one day at the end of that month 3.9M NEAR
left, the largest one-day fall in the series ($14.6M), and 69% of that inflow has now gone.

**Most of it came from one account.** A public index lists every transfer in and out of the treasury. We use
it only where it agrees with the chain: on 20 of 20 days tested, its list adds up, to the last unit, to the
change in the balance we read. Between the readings of 15 and 28 September 33.8M NEAR went in and 21.3M NEAR
came out. One account, `solver-priv-liq.near`, is 94% of the net: 17.0M NEAR in, 5.2M NEAR out. Its name
suggests a solver's own liquidity; nothing published says who runs it or why it moved. So the September lump
was not a crowd of depositors arriving for a reward. And when 5.6M NEAR left before the 30 September reading,
38% of it went to three accounts, each in a single transfer.

**The best day in the series is half a round trip.** We followed the largest single transfer behind it, from
the chain alone. The float's largest one-day rise is $12.0M, on the 2026-09-25 reading. $6.1M of it, 51%, is
one transfer of 1.7M NEAR that reached the treasury at 08:52:40 UTC on 24 September. The treasury itself had
paid out exactly that amount, to the last unit, at 23:35:58 UTC the evening before, 24 minutes before the daily
reading. It sat in an account on the public ledger for nine hours, was withdrawn as plain NEAR to a deposit
address, passed through the account that sweeps such addresses into NEAR Intents, and was back in the treasury
31 blocks after the withdrawal. So a daily series can count the same money leaving on one day and arriving on
the next. The ten-best-days figure above and reading R2 therefore overstate how much new money those days
brought. We do not know why it was moved. The five steps, with block heights and receipt ids, are in
`data/context/trace.json`; `make verify` re-reads four of them from the chain, and
`make trace` finds the transfer again from nothing but balances.

**The float is not activity.** Across 27 October, the day swaps moved to the private chain, the float changed by
2.8%. Swaps pass through and leave. What stays is inventory and balances people choose to keep there. So the
float measures commitment, how much money is willing to rest behind a chain nobody outside can read, and says
nothing direct about volume or fees. In the 17 days since the switch it has added $20.7M.

**The price needs growth, and the recent trend is down.** The value of NEAR's total supply is $4.48B. Net new
supply runs at 88,704 NEAR a day, $110.7M a year, and is paid to those who stake, so it dilutes holders who do
not. Counted NEAR against NEAR, the revenue that reaches NEAR's wallets covers 15% of it, and the supply is
worth 265x that revenue. With both sides in dollars instead, the revenue at each day's price and the new supply
at the pinned price, the same figures are 20% and 205x; they differ because NEAR's price averaged more over
those 30 days than on the pinned day. We use NEAR against NEAR because the buyback is paid in NEAR bought on the
day. Over the latest 30 days against the 30 before, reported volume is -22%, reported fees -26% and that
revenue -20%.

**The backing has already failed once, and one public key signs for it.** $136.4M is described as "backed 1:1"
by the treasury. The treasury is public. What the private chain owes is not, and nothing published proves the
two match. October showed the failure is not hypothetical, though that one was on the public side, where it
could be seen and was closed within 76 hours. And the treasury is not a contract: it is an ordinary account with
1 key registered for it inside `intents.near`. Its own access key on NEAR has never signed a transaction.
The payout in the transfer we followed above was signed by that registered key: one signature moved $6.1M out
of the treasury. NEAR's docs say that when tokens are unshielded "the PoA Bridge processes the burn request and
releases the backing tokens from the Treasury on NEAR". They do not say how the key that signs those releases
is held; one public key can stand for several parties signing together, and nothing published says whether
this one does.

## 5. What that means for a holder

**What the audit is worth.** A holder of NEAR is exposed to NEAR Intents whether they use it or not, because its
revenue is what funds the buyback. On the public side that exposure can be checked by anyone, at any block, for
two calls per token, and a hole shows in the block where it opens. We have not surveyed other venues, so we do not say how rare that is. We say it is the one part of NEAR's
investment case we could verify end to end without trusting the party being valued, and it held up: whole
today, and short only when something was in fact wrong. The same check is missing for the side that now holds
61.0%. Moving swaps to the private chain gave users confidentiality and took this check away, and nothing has
replaced it.

**What that is in money.** The revenue that funds the buyback is the only cash flow in NEAR's case, so it is the
right ruler. October's hole at its largest was 2.1 months of that revenue, and it was closed. The balance now
beyond the audit is 6.3 years of it. A loss of 16% of that balance would equal a full year of the revenue. We
do not say such a loss is likely. We say that the part nobody outside can check is large against the cash flow
a holder is counting on, and the part that can be checked has already shown a failure of two months' worth.
That gap, not a view on NEAR's technology, is why the position below is small.

**A simple model of what is needed.** NEAR's wallets receive 4.8 basis points per dollar of reported volume.
For buybacks to match net new supply, revenue has to grow 6.5x. At today's rate per dollar of volume that means
about $297B a year of volume, against $3.73B in the last 30 days. A governance proposal, HSP-029, would lower
the maximum issuance from 2.5% a year to 1.6%; if net new supply ran at 1.6%, the multiple would be 4.2x. On the dollar
basis of section 4 the first multiple is 5.1x. A holder is buying that growth, or a higher take, or lower
issuance.

**After 27 October, the float is an adoption measure that cannot be restated afterwards. It can be inflated
while it is read.** A table can be restated by whoever keeps it. A token balance at a past block cannot. But a
reward, or an interested party, can put balances there for a while. So we read two things: the float without
NEAR's own token, and what remains once rewards have been paid.

**Our position, with numbers.** We size NEAR by what can be checked. The rule below is a judgment, not a result
of the data, and it is the part of this file most open to argument.

- Hold no more than 1% of a liquid portfolio in NEAR while most of what NEAR Intents holds is beyond the audit.
- Hold up to 3% if NEAR publishes the private chain's totals per token against a block height (test D1). With
  those, the two-call audit covers everything.
- Hold none if a hole in the public books stays open beyond 3 readings (test G3), if the audit stops being
  possible (test G4), or if R5 breaks: the money behind the private chain, without NEAR's own token, falling
  below its pinned level would mean the product itself is being left.
- Review on 2027-03-31, when the dated tests resolve.

Growth of the float cuts both ways under this rule. It is use of the product, and it is money moving beyond the
audit. So R1 and R5 holding tells us the product is growing and does not raise the position; only the
disclosure does. The case against holding much is unchanged: revenue is 15% of net new supply and falling, a
reward is still in force, the largest inflow came from one account and half of the best day was a round trip,
the backing has already failed once, and one public key signs for the treasury. We do not give a price target:
nothing we can check supports one.

## 6. What would change our mind

Written on 2026-11-13. R1, R2, R3 and R5 are produced by this repository's pipeline at the pinned prices and
scored by `python3 -m pipeline.score` once their reading exists.

| # | Reading | Now | Thesis holds if, on 2027-03-31 | Thesis breaks if |
| --- | --- | --- | --- | --- |
| R1 | Private float | $136.4M | at least $200M | below the pinned day's level |
| R2 | Ten best days as a share of the float | 55% | below 45%: new money arrives on many days | still above 55% |
| R3 | Private share, the 20 tracked tokens | 62.3% | at least 50% | below 40%: money is moving back to the public side |
| R4 | Revenue reaching NEAR's wallets as a share of net new supply, NEAR against NEAR | 15% | at least 25% | below 10% |
| R5 | Float without NEAR's own token | $92.9M | at least $130M | below the pinned day's level |

Between "holds" and "breaks" a reading is undecided. The scoring code is stricter than this table: it prints
FAIL for anything short of "holds". R2 depends on R1: if the float does not grow, R2 can only improve when lumps
leave. R4 is the last 30 complete days of DefiLlama's revenue, each day turned back into NEAR at that day's
price, over 30 days of net new supply from block headers. It uses a quoted figure, so it is scored by hand. R5
was added on the same day as the others, after we learned of the reward programme; `PREREG.md` records the
amendment.

**First results, 14 November.** Four of the dated tests were scored on the 2026-11-14 reading, the first one
taken after they were written. E1 failed: the float had to be at least $136.4M and it was $135.2M. E2 and E3
passed: no single day added a lump, and the tracked share was 61.9%. G1 passed: none of the tracked tokens was
short. One day settles nothing about the long-dated readings; a fail is reported here because we said it would
be.

**Two sets of tests, and what each covers.** R1 to R5 above, and the E and F tests below, were written for this
project's first question: is the money behind the private chain growing. They are hashed and stay as written.
Read with the audit, R3 changes meaning: money moving back to the public side would be bad for the private
product and good for what can be checked, so we no longer treat a fall in R3 as breaking the thesis, and we say
so here instead of editing a hashed file. The claim the thesis now leads with has its own dated tests, written
on 13 November before the next reading existed, in [`PREREG-AUDIT.md`](PREREG-AUDIT.md):

| # | Test | Scored on |
| --- | --- | --- |
| G1, G2 | No tracked token is short on the 2026-11-14 reading, and none on the 2026-11-17 reading | those readings |
| G3 | Any tracked token found short on a reading is whole again within 3 readings | to 2027-03-31; fails on the day it is broken |
| G4 | Both questions can still be asked for every tracked token | 2027-03-31 |
| D1 | NEAR has published what the private chain owes, per token, against a block height | 2027-03-31, by hand |

G1 and G2 are likely to pass, and are written down because a fail would be the most important thing this
project could report.

Shorter tests resolve on the 2026-11-14 and 2026-11-17 readings: the float does not fall, no single day adds
another lump, and the tracked share stays at 60% or more. They are written, with their thresholds and their
base rates, in [`PREREG.md`](PREREG.md). A fail will be reported as a fail.

**How likely are they? A base rate from the float's own history.** `make model` replays the float's past daily
changes forward to 2027-03-31: 10,000 paths from one seed, each built from runs of 7 consecutive past days drawn at
random, each scored with the thresholds above. The readings were fixed and hashed before this model was
written, so it did not shape them.

| Days the paths are drawn from | R1 holds | R5 holds | Median float on the day |
| --- | --- | --- | --- |
| Every day since the first deposit | 53% | 72% | $202.6M |
| Only days before the reward programme was announced | under 1% | under 1% | $170.0M |
| Only days since the first reward's snapshot was triggered | 82% | over 99% | $258.7M |

On the whole history R1 is close to a coin flip, and R2 holds on 67% of paths. At the pace before the reward
neither R1 nor R5 holds: both need the pace of the last two months to continue, and that pace has a reward and
a promised second round behind it. So these readings do test the claim; they are not set where the float
already was heading without help. The result also moves with the length of the runs. From single days to runs
of 30 days, R1 on the whole history holds on 51% to 60% of paths, and on the last window on 38% to 96%, because
that window is short and contains the September exit. This is a base rate, not a forecast: changes are in
dollars, nothing compounds, and the model knows nothing about why money moved. R3 and R4 are not modelled.
`python3 -m pipeline.model --help` lists the settings.

Two more items have no threshold. If NEAR publishes what the private chain owes, per token, in a form that can
be set against the treasury at a block height, the largest risk in section 4 mostly goes away and we would hold
more. That disclosure does not have to reveal anyone's balance: committing to each balance and proving the
sums, a proof of liabilities, is a known technique that publishes totals and nothing else. And if the audit of
the public books, which the dashboard repeats every day, shows a hole that is not closed within days, we would
sell: the one thing we can check would have failed.

## 7. What could not be computed, and other limits

- **What the audit covers.** The public ledger, `intents.near`, against each token's contract on NEAR. Most of
  those tokens are themselves issued on NEAR by a bridge for tokens that live on another chain. Whether the
  bridge holds those is a further question that this audit does not ask. The audit takes `mt_batch_supply` as
  the sum of all credits and does not rebuild it from every account.
- **A standing surplus and a small hole.** Whether credited is above held would miss a hole smaller than the
  surplus a token already carries, as USDC on NEAR does. The second test, a new low of held minus credited,
  covers that case on the stored readings, and `make audit` and the dashboard's button compare a live reading
  with the lowest of the token's last 30 stored readings. That comparison is new and has no dated test of its
  own: the tests in `PREREG-AUDIT.md` were hashed before it was written and are about the sign only.
- **Which tokens.** On the pinned day: the tokens in NEAR Intents' list as first fetched that have a balance to
  read, and the unlisted ones the treasury holds. 15 tokens joined the list later that day and are left out of
  every pinned figure. Read once at the pinned block, they hold $291,069 in all. None is short and none is
  in the treasury. With them the private share would print as 60.9%.
- **A replay, not detection.** The block-by-block record of the October hole was made on 13 November. Its steps
  were found by halving the days between daily readings; two changes that cancel between two blocks that were
  read are not seen. Payout and upgrade times are CertiK's and are quoted.
- **How often.** One block a day since 18 February, for the 20 tracked tokens only; every listed token on the
  pinned day alone. A hole that opened and closed between two readings is not in it. The button on the dashboard reads the latest
  block only when someone presses it.
- **Swap volume and fees.** Not computable from the chain since 27 October for the swap leg. They are quoted
  from DefiLlama and labelled. The NEAR Intents Explorer API needs a partner key and returns the operator's own
  figures, so it would not change that.
- **Activity tables.** Daily active accounts and transaction counts from the BigQuery public dataset are not
  used: they say nothing about what sits behind the private chain, and querying them needs a billing account.
- **What the private chain owes.** Not computable by anyone outside it. The treasury shows assets, not
  liabilities. If the private chain is also backed somewhere other than this one account, we do not see it.
- **Who deposited.** A public index names the account on the other side of each NEAR transfer from 12 September
  to 1 October, and one account supplied most of the net inflow. An account is not a person: many of the others
  are one-time deposit addresses. We followed only one transfer back to where its money came from, and it was
  the treasury's own. We did not look at tokens other than NEAR, or at other months.
- **One price list.** Dollar history is in the prices NEAR Intents' own list showed on 2026-11-13. It shows
  tokens moving, not what the float was worth on each past day. NEAR's "$70M" in September was measured at that
  day's prices, not ours. The list changed during the day: ids that appeared later were added at the price
  first seen, and an id already pinned kept its price.
- **Unpriced tokens.** 30 of the 205 token types have no price in that list. They are counted and left out of
  every dollar figure, so the float is understated by an unknown amount.
- **Coverage of the share.** The 61.0% counts every token in NEAR Intents' token list that has a price and a
  balance inside `intents.near`. 27 listed ids are of another kind (`1cs_v1:`), are not balances inside
  `intents.near`, and are not counted. A token that `intents.near` holds but NEAR Intents does not list would
  not be counted at all. The history follows 20 tokens chosen by their size on the pinned day, read once a day. DefiLlama shows a smaller total for NEAR Intents than ours; we did not
  reconcile the two.
- **The treasury account.** The docs name this account for the confidential flow used by market makers. That
  1Click's private settlement since 27 October uses the same account is our inference from the docs, from the
  account's daily movements and from NEAR's September announcement. We did not trace a 1Click swap's shield
  transaction to it.
- **The exploit is matched by token, size and time, not by transaction.** We did not trace the attacker's
  transactions or follow the tokens on BNB Chain.
- **The reward programme.** Its rules are taken from NEAR's blog post and press release (`docs/SOURCES.md`). We
  did not measure how many wallets qualified.
- **HSP-029.** Its terms are taken from the proposal's text. We did not check its status on chain.
- **One reading a day.** Money that enters and leaves between two midnights is not seen. That is why this is a
  float series and not a volume series.
- **Quoted figures.** Volume, fees and revenue come from DefiLlama, and one NEAR price a day from CoinGecko
  through DefiLlama. Two NEAR prices are therefore in use: the float is valued at NEAR Intents' own list, and
  the supply at CoinGecko's price at the pinned block. We did not recompute the quoted figures. The last day
  before the pin is left out because its fee figure was incomplete. The valuation figures and R4 depend on them.
- **One provider.** Readings come from one public archival node. One historical read was repeated on a second
  node and matched (`data/context/cross_check.json`). Set `ARCHIVAL_RPC` to repeat the whole check elsewhere.
- **The model's runs do not wrap.** A run of 7 days cannot start in the last 6 days of a window, so those days
  and the first ones are drawn less often. When runs may wrap, R1 on the window since the snapshot holds on 89%
  of paths, not 82%. We kept the stricter version in the table.
- **Readings written the same day.** R1 to R5 were written on the day the data was first assembled, not before.
  Only the tests in `PREREG.md` are scored on readings taken after they were written.
- **Not covered.** Competitors, regulation of private settlement, and who the private chain's validators are.

This is research, not investment advice.
