# Waterline: a NEAR thesis built on an outside audit

Pinned to NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). Every number in this file is either computed
from the data (`data/derived/claims.json`) or a declared constant (`data/constants.json`). `make check` fails
if a dollar amount, a percentage, a multiple, a NEAR amount, a clock time, a block height, a span of hours, days,
months or years, a correlation or p-value, or a count of tokens, checks or readings here is neither. It does not
check dates, numbers written as words, or a valid number put in the wrong sentence. The tables marked as
generated are written by the code and compared whole.

The track's example prompt asks for four things in this file: the claim, the evidence for it, the evidence
against it, and what result would change our mind. They are sections 1, 3, 4 and 6. Section 5 is the rating and
the rule that moves it. Section 7 says what could not be computed. Appendix A keeps this project's first
question, whether the money behind the private chain keeps growing, with its readings and tests as written.

## 1. The claim

**Rating: Hold, small and staked. Up to 1% of a liquid portfolio, to the end of 2029, checked every month by a rule
(section 5) whose inputs this repository reads from the chain.**

NEAR's buyback is funded by the revenue of one product, NEAR Intents. Read from the chain, 426,685 NEAR reached NEAR's
three revenue wallets in the 30 days to the pinned reading, 14,223 NEAR a day. That product keeps its books on a public
ledger, `intents.near`, and anyone can audit them with two questions asked at the same block: ask the ledger what
it has credited for a token, and ask the token's own contract what the ledger holds. We asked both for 214 tokens
worth $223.8M at the pinned block. None is short. Across the history the books were short on three readings, for
one token, during an exploit that was later published. Replayed block by block, that hole was in the public
books from ten dollars 31 hours 40 minutes before the first payout, and above $10,000 1 hour 9 minutes before it.

On 27 October 2026, 1Click swaps began to settle on a private chain. What backs that chain is one account on the
public ledger, and 1Click's own records show its swaps passing through it: for each of the 9 swaps we found
(8 completed, 1 refunded), the swap's status record lists the NEAR transaction that moved its tokens into that
account. They show the route a swap takes, not what share of swaps take it. The audit sees that
account's balance and nothing behind it, and it is now 61.0% of everything NEAR Intents holds. The revenue that
funds NEAR's buyback takes the same route: in the latest 30 days, 74% of it arrived through the treasury, paid by
accounts that had received that NEAR from the treasury minutes before.

**Our claim: NEAR Intents' public books can be proven whole by anyone, at any block, and the one failure showed
in them before the money left. The same proof does not reach the private chain, where the swaps now settle and
most of the money now sits. So NEAR is worth holding on what can be checked, and only a little of it: for
buybacks to match new supply by the end of 2029, the revenue that funds them has to grow about 84% a year in NEAR,
and over the latest 30 days against the 30 before it was -17%.**

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
and by our own reading 56.2% of what NEAR Intents held in its 20 largest tokens was already private the day
before.

| Number | Latest value | Where it comes from | Can an outsider recompute it from the chain? |
| --- | --- | --- | --- |
| Swap volume, 30 days | $3.73B | A table uploaded to Dune under the `near` name, read by DefiLlama; also NEAR's own Explorer | Not the swap leg. Shield and unshield flows yes, with an indexer; not done here |
| Gross fees, 30 days | $6.0M | Tables uploaded to Dune under the `near` name | No |
| Revenue reaching NEAR's wallets, 30 days | 426,685 NEAR read here; $1.8M quoted | NEAR and wNEAR received by three public wallets | Yes, this repository. Over the same days the chain shows 100.9% of the NEAR DefiLlama counts |
| Net new NEAR supply | 88,704 NEAR a day | Block headers | Yes, this repository |
| Private float | $136.4M | Balances of one account in `intents.near` | Yes, this repository |
| Backing of the public books | $223.8M, none short | The ledger's credited totals against each token's own contract | Yes, this repository, and a button on the dashboard |

We are not saying the uploaded numbers are wrong. They are reported, not observed, and a thesis should say which
of its inputs are which. Sources for every row: `docs/SOURCES.md`.

**The usual activity numbers do not move with it either.** The track's example prompt starts from a hypothesis:
NEAR Intents' volume leads network usage. We tested it over 98 weekly changes, with NearBlocks' public daily counts. A
week's change in reported volume does not foretell the change in transactions (r = -0.11, p = 0.96, at its strongest lead of
one to eight weeks), in active accounts (r = +0.09, p = 0.88) or in NEAR's price (r = -0.12, p = 0.74). p is the share of series shifted at
random in time that do as well, so a real lead would show a small p, and none does. Volume and transactions
do move a little together within the same week (r = +0.27), so a chart of the two shows some likeness; what the
data does not show is volume moving first. `python3 -m pipeline.leadlag` repeats the test.

The float is every token held in `intents.near` by the treasury account that backs the private chain. We read it
at one block a day since the account was created. Dollar figures use one fixed price list, so a change in the
series is a change in tokens, not in prices.

## 3. The evidence for the claim

**The public books can be audited, and they are whole.** `intents.near` answers `mt_batch_supply`: the total it
has credited for each token, to all accounts together. Each token's own contract answers how much
`intents.near` holds. At the pinned block we asked both for 214 tokens worth $223.8M: the listed tokens that have a
balance to read, and the unlisted ones the treasury holds. Most are equal to the last unit. The rest hold
slightly more than is credited, $6,321 in all. None is short. `python3 -m pipeline.audit --now` repeats it for
the 20 largest tokens at the latest block, and so does a button on the dashboard, from the reader's own browser.

**Across the history they were short once.** The same audit on every stored reading since February, for the 20
largest tokens, one reading a day: 4,806 checks, 3 of them short. All three are one token, a dollar token bridged from BNB Chain,
on 30 September, 1 October and 2 October. On the last of them `intents.near` held 67,669 of it against
3,869,502 credited: a hole of $3.8M, 98% of everything credited in that token.

A stricter test gives the same answer. Many tokens hold a little more than is credited, and a hole smaller than
that surplus would not turn the sign. So we also ask whether held minus credited fell below every earlier
reading of the same token. Across the same checks that happened on 3 new lows: the same three readings, and no
others. Tokens that arrive without a credit only add to the surplus, so in ordinary running it does not make
new lows, and when it did, something owed had left.

**That hole showed before the money left.** We replayed those days block by block. The hole opens at block
217799506, stamped 16:14:22 UTC on 29 September, at ten dollars. CertiK dates the first exploit transaction to
16:14:19 that day, three seconds earlier, and places the fault in NEAR Intents' own deposit handling: a refund
that returned the tokens and left the credit. The first payout from the bridge's treasury on BNB Chain comes
31 hours 40 minutes after the hole opens. For 28 hours of that the hole is under $3,000. It passes $10,000 1 hour 9 minutes before the first
payout and $1.0M 13 minutes before it. It peaks at $3.8M and the books stay short for 76 hours. They are whole again on
the evening of 2 October, minutes before the contract upgrade CertiK records, and the credited total does not
fall while the hole closes. That is consistent with the statement, which CertiK reports and does not verify,
that the money was returned in full. What we see is the balance on NEAR being refilled, not the tokens on BNB
Chain.

This is a replay, run on 13 November, six weeks after the event. It is not live detection, and we do not say
anyone would have acted. The start time is CertiK's finding too; what the replay adds is that the hole could be
seen and sized from outside, with two calls to two contracts, at every step.

**As an alarm.** How early an outside reader would have seen it depends on how often they read and how large a
hole they wait for. Generated from the replay in `data/context/exploit.json`; the payout time is CertiK's:

<!-- alarm:start -->
| A reader who checks | First sees the hole at (UTC) | Hole then | Before the first payout |
| --- | --- | --- | --- |
| every block | 29 Sep 16:14:22 | $10 | 31h 40m |
| every 10 minutes | 29 Sep 16:20:00 | $10 | 31h 34m |
| every hour | 29 Sep 17:00:00 | $10 | 30h 54m |
| once a day, at 00:00 UTC | 30 Sep 00:00:00 | $30 | 23h 54m |

| An alarm set at a hole of | First reached at (UTC) | Before the first payout |
| --- | --- | --- |
| $10 | 29 Sep 16:14:22 | 31h 40m |
| $1,000 | 30 Sep 00:32:34 | 23h 21m |
| $10,000 | 30 Sep 22:45:09 | 1h 9m |
| $100,000 | 30 Sep 23:22:01 | 0h 32m |
| $1.0M | 30 Sep 23:41:28 | 0h 13m |
<!-- alarm:end -->

A reader once a day, as this project is, would have seen a hole of $30 at the reading of 30 September, the
sign test firing almost a day before the first payout. Whether a test like that also fires when nothing is
wrong is the other half of an alarm. We audited 200 random blocks between the first reading and the pinned one,
so between the daily readings as well as on them. Outside the October hole the sign test fired on 0 of 199 and
the new-low test on 0 of 199. One block fell inside the 451,623 blocks the hole was open, and it showed the hole.
No false alarm in that many draws puts the rate per block below about 1.5%, at 95% confidence: a ceiling, not an
estimate. Section 7 says what that does not cover.

**The swaps now settle through the account the audit cannot see into.** NEAR's changelog says 1Click swaps settle
on the private chain from 27 October and that a swap's `nearTxHashes` then lists the shield and the unshield.
We took the accounts that paid into the treasury on six days after 27 October and asked 1Click's public status
endpoint about each. Among 188 accounts, 9 were deposit addresses of completed or refunded swaps, dated
2 to 11 November: 8 completed and 1 refunded. For each of them, the swap's own record lists the transaction
that moved its tokens into the treasury. We read each of those transfers back from the chain: a transfer signed for the deposit address, of
that amount, to the treasury. Every one of the 9 was marked `public` by the integrator, and every one went
through the private chain's treasury. Because they were found among accounts that paid into the treasury, they
show that the route exists and how it is recorded, not what share of 1Click's swaps take it; nothing public
lists all swaps without a key. `python3 -m pipeline.oneclick` lists them and `make verify` re-reads them.

The rest of this section is about that account, the one the audit cannot see into: what it holds, read from
outside.

**It is large and it grew.** First reading with a balance: 2026-02-19. $49.3M at the B2B launch on 13 July. $136.4M on
the pinned day, 2.8x in four months, across 205 token types. That is also the highest it has been.

**Most of NEAR Intents is already behind it.** On the pinned day we asked the contract of every token in NEAR
Intents' own token list how much `intents.near` holds: 180 tokens with a price, $223.8M in total. The private side
is 61.0% of that. It is not even across assets: NEAR 69.9%, stablecoins 68.2%, ZEC 60.3%, ETH
57.5%, and bitcoin only 28.8%.

Through time we follow the 20 largest tokens by total held, which cover 89% of that total. Their private share
was 5% at the start of April, 36.0% at the July launch, 56.2% the day before the switch and 62.3% on the pinned
day. Over the same months the public side did not grow: $86.0M in April, $75.0M now. The growth was on the private
side.

**It is not only NEAR's own token.** Stablecoins are the largest group (Stablecoins: $49.3M) ahead of NEAR's own token
(NEAR: $43.5M). 68% of the float is not NEAR's own token.

**Without NEAR's own token it is steadier, and it kept growing after the first reward closed.** That part was
$46.1M when the first reward's snapshot was announced and is $92.9M now, 3.5x since the July launch, and its worst
day ever is a fall of $2.7M. The whole float grew by $7.9M per 30 days before the reward programme, $14.3M per 30 days while the first reward
was open, and $31.8M per 30 days since.

**It is the account NEAR means.** NEAR announced on 17 September that confidential balances had passed $70M at
that day's prices. Our reading of this account that day, at our fixed prices, is $76.0M. With NEAR's own token at
each day's price it is $68.3M on the 17 September reading and $74.1M on the next: it crosses $70M on the day of
the announcement.

## 4. The evidence against the claim

**The audit stops at the private chain.** 61.0% of what NEAR Intents holds is credited to one account, the
private chain's treasury. The audit proves the tokens are there. It cannot say who they are owed to, or whether
the private chain has promised more than the treasury holds, because no contract answers that question. And
the October hole fell mostly on that side: 87% of the credit in the broken token belonged to the treasury.

**Who would bear a loss there.** The users who hold balances on the private chain, first. A NEAR holder would
bear it in two ways: through the revenue that funds the buyback, which depends on those users staying, and
through any decision by NEAR Intents' operators to make users whole, as the bridge operator did after October
by returning the backing, as CertiK reports. If a loss there were made good out of the revenue that funds the
buyback, a loss of 16% of the float would use up a full year of it. Nothing published says how such a loss
would be shared or who would pay it.

**Part of the float is paid for.** On 11 June 2026 NEAR announced a reward for holding a confidential balance: a
pool of locked tokens that convert to NEAR, shared among wallets that keep more than $100 there and make at
least one confidential swap, with the snapshot taken once confidential balances reach $70M and no wallet
receiving more than 2%. On 17 September NEAR announced that the $70M had been reached and the snapshot
triggered. A second round is promised. With another round promised, nobody outside can separate use from
reward-seeking, and we do not claim to. The reward is small against the float, though: the first pool is
333,333 locked tokens, $1.1M at its conversion price, and no wallet can receive more than $22,200.

**The NEAR in it came late and mostly left.** The ten best days add up to $75.5M, which is 55% of the float. The
treasury held 8.5M NEAR on the day NEAR announced that the snapshot had been triggered. Between the readings of 15
and 28 September 12.6M NEAR entered, nearly all of it after that announcement, so it was not positioned for the
first reward. In one day at the end of that month 3.9M NEAR left, the largest one-day fall in the series ($14.6M),
and 69% of that inflow has now gone. That fall lies between the readings of 29 and 30 September, the day the
hole in the public books opened, so we put the two in order. The money left first: 4.1M NEAR net between the
reading of 29 September and block 217799506, where the hole opened, including three transfers out of 2.1M NEAR
between 06:06 and 06:09 UTC, 10 hours before it. After that block the treasury gained NEAR. The exit was not a
reaction to the exploit.

**Most of it came from one account.** A public index lists every transfer in and out of the treasury. We use it
only where it agrees with the chain: on 20 of 20 days tested, its list adds up, to the last unit, to the change in the
balance we read. Between the readings of 15 and 28 September 33.8M NEAR went in and 21.3M NEAR came out. One account,
`solver-priv-liq.near`, is 94% of the net: 17.0M NEAR in, 5.2M NEAR out. Its name suggests a solver's own
liquidity; nothing published says who runs it or why it moved. So the September lump was not a crowd of
depositors arriving for a reward, and a reward of $1.1M could not be the reason one account moved that much.
Over the same two weeks NEAR's price on CoinGecko went from $2.47 to $5.39, 2.2x; we do not know which moved
which. And when 5.6M NEAR left before the 30 September reading, 38% of it went to three accounts, each in a
single transfer.

**The best day in the series is half a round trip.** We followed the largest single transfer behind it, from
the chain alone. The float's largest one-day rise is $12.0M, on the 2026-09-25 reading. $6.1M of it, 51%, is one
transfer of 1.7M NEAR that reached the treasury at 08:52:40 UTC on 24 September. The treasury itself had paid out
exactly that amount, to the last unit, at 23:35:58 UTC the evening before, 24 minutes before the daily reading.
It sat in an account on the public ledger for nine hours, was withdrawn as plain NEAR to a deposit address,
passed through the account that sweeps such addresses into NEAR Intents, and was back in the treasury 31 blocks
after the withdrawal. So a daily series can count the same money leaving on one day and arriving on the next.
The ten-best-days figure above therefore overstates how much new money those days brought. We do not know why
it was moved. The five steps, with block heights and receipt ids, are in `data/context/trace.json`; `make
verify` re-reads four of them from the chain, and `make trace` finds the transfer again from nothing but
balances.

**The float is not activity.** Across 27 October, the day swaps moved to the private chain, the float changed by
2.8%. Swaps pass through and leave. What stays is inventory and balances people choose to keep there. So the
float measures commitment, how much money is willing to rest behind a chain nobody outside can read, and says
nothing direct about volume or fees. In the 17 days since the switch it has added $20.7M.

**The price needs growth, and the recent trend is down.** The value of NEAR's total supply is $4.48B. Net new
supply runs at 88,704 NEAR a day, $110.7M a year, and is paid to those who stake, so it dilutes holders who do not. Read from the
chain, the revenue that reaches NEAR's wallets covered 16% of it in the 30 days to the pinned reading and 20%
in the 30 days before. Counted NEAR against NEAR from DefiLlama's figure the share is 15%, and the supply is
worth 265x that revenue; with both sides in dollars, the revenue at each day's price and the new supply at the
pinned price, the same figures are 20% and 205x. They differ because NEAR's price averaged more over those
30 days than on the pinned day. Over the latest 30 days against the 30 before, reported volume is -22% and
reported fees -26%; the revenue the chain shows reaching NEAR's wallets is -17%.

**The public ledger broke once, and one public key signs for the treasury.** $136.4M is described as "backed 1:1"
by the treasury. The treasury is public. What the private chain owes is not, and nothing published proves the
two match. In October the public ledger itself broke, through a fault in its own deposit handling: one token's
credit had nothing behind it for 76 hours, most of that credit was the private chain's, and it could be seen and
was closed. And the treasury is not a contract: it is an ordinary account with 1 key registered for it inside
`intents.near`. Its own access key on NEAR has never signed a transaction. The payout in the transfer we
followed above was signed by that registered key: one signature moved $6.1M out of the treasury. NEAR's docs say
that when tokens are unshielded "the PoA Bridge processes the burn request and releases the backing tokens from
the Treasury on NEAR". They do not say how the key that signs those releases is held; one public key can stand
for several parties signing together, and nothing published says whether this one does.

## 5. The rating

**Hold, small and staked: up to 1% of a liquid portfolio, to the end of 2029.**

**The rule.** Each input is computed by this repository's code from the chain, and the rating is too; the
dashboard shows the result.

| Rating | When | Position |
| --- | --- | --- |
| Add | The public books are whole, and either coverage is at least 25% in each of the last two 30-day windows, or NEAR has published the private chain's totals per token against a block height | up to 3% of a liquid portfolio |
| Hold | The public books are whole, and neither the Add nor the Exit condition on coverage holds | up to 1% |
| Exit | A hole in the public books stays open beyond 3 readings, or the audit can no longer be run, or coverage is below 10% in each of the last two 30-day windows | none |

Coverage is the NEAR and wNEAR that reach the three revenue wallets over 30 days, read from the chain, set
against the growth of NEAR's total supply over the same 30 days, read from two block headers: 16% in the
latest window and 20% in the one before. The public books are whole on the latest reading. So the rule gives
Hold.

**Where that revenue comes from.** One step back, the rating's only live input passes through the account the
audit cannot see into. Every payment from `intents.near` into the three wallets is a withdrawal signed by an
account on the ledger. We read each payment's transaction to find that account, then the account's ledger
transfers in the minutes before it paid, and let those inflows fund its payments oldest first, each used once:
1,116 payments by 835 accounts in the latest 30 days. 74% of the revenue arrived through the private chain's
treasury; 18% was paid from balances the payers already held, whose source the windows do not show; 99.9% of it
came from `intents.near` at all. The share was 72% before 27 October and 75% from that day, so the route is
older than 1Click's switch, and the foundation's wallet is paid almost entirely this way (99%). This is the route
the money took, not where it was earned: fees collected on the private chain reach NEAR's wallets by leaving
through the treasury. It does not change the rule. It means the revenue is measured on the chain as it arrives,
but whether the private chain earned it is not something anyone outside can check, which is a second reason the
Add rule accepts a disclosure of the private chain's totals. `python3 -m pipeline.revenue_source` prints the
trace, and `make verify` re-reads a sample from the chain.

Where the numbers come from: 25% and 10% are reading R4's thresholds, written on 13 November; 3 readings is the
October precedent, short on three readings and whole on the fourth; two windows in a row, because a rule that
one ordinary day can trip is not a rule. That last point was learned the hard way. An earlier version also
said to sell if the float without NEAR's own token fell below its pinned level; the very next reading tripped
it, on an ordinary day. A reader who holds us to that version would rate NEAR Exit. We withdrew it because the
float moves in lumps that say nothing about value (section 4), and we report the dated test it rested on as
failed (`make score`, E1) rather than drop it (errata). The 1% and the 3% are judgments, and the part of this
file most open to argument.

**The NEAR the revenue buys is held, not burned.** Coverage counts the NEAR that reaches the three wallets as if
it offset new supply. It does only while they keep it. Read from the chain, the three held 4,282,006 NEAR together
at the pinned reading, up from 1,040,604 NEAR on 18 February, and held less than at the reading before on only
2 of 268 days; since 14 September, when this repository starts reading their transfers, they have sent out 0 NEAR. None
of it is burned. The buyback wallet is a multisig that moves NEAR when 2 of 4 of its keys confirm, and the two DAOs
need 2 of 5 and 2 of 4 approvers. So coverage measures NEAR bought against NEAR issued: an upper bound on what
offsets new supply, which holds only while those signers keep what the revenue buys.

**Held staked, because new supply is paid to stake.** At the pinned block 44.4% of NEAR's supply was staked, and
the protocol kept none of the new supply for itself, so all of it is paid to stake: 5.6% a year before the
validator's fee, counted as net new supply over the total stake. A staker's share of the supply changes by +3.0% a
year and the share of a holder who does not stake by -2.4% a year; to the end of 2029, +9.8% against -7.4%, with
issuance and stake as they are now. If HSP-029 takes effect the reward falls with issuance, to 3.6% a year at the
same stake. So the dilution section 4 counts against NEAR is paid by holders who do not stake, and the rating
says to stake. A validator keeps a fee that varies by validator, and staked NEAR takes four epochs to withdraw.
`python3 -m pipeline.context staking` reads the stake again.

**What has to be true by 2029.** The rule says when to move. This says what a holder is betting on: the share of
net new supply that revenue would cover if revenue, counted in NEAR, grew at a steady rate from the latest 30
days. Generated by `pipeline/claims.py`:

<!-- scenarios:start -->
| Revenue in NEAR grows, a year | Covered at end-2029, issuance as now | At end-2031 | Years to cover it all | Covered at end-2029, issuance at 1.6% | At end-2031 | Years to cover it all |
| --- | --- | --- | --- | --- | --- | --- |
| -20% | 7% | 5% | never | 12% | 7% | never |
| +0% | 15% | 14% | never | 24% | 23% | never |
| +25% | 30% | 44% | 9.2 | 47% | 72% | 6.7 |
| +50% | 53% | over 100% | 4.8 | 84% | over 100% | 3.6 |
| +100% | over 100% | over 100% | 2.7 | over 100% | over 100% | 2.1 |
| needed to cover it all | 84% a year by end-2029 | 46% a year by end-2031 | | 59% a year by end-2029 | 33% a year by end-2031 | |
<!-- scenarios:end -->

With issuance as it is, revenue counted in NEAR has to grow 84% a year to cover new supply by the end of 2029, or
46% a year by the end of 2031. If HSP-029 takes effect, 59% a year or 33% a year. If revenue stays where it is, it covers 15%
at the end of 2029, or 24% at 1.6%. Read from the chain, the latest 30 days against the 30 before were -17%.
This is what the 265x multiple in section 4 prices in: a revenue line that grows by a third to a half every year
until 2031, or faster to get there by 2029.

**No growth rate can be read from the record yet.** The revenue has arrived every day since the buyback began on
23 February 2026. Counted in NEAR at each day's price, its first complete week paid 25,228 NEAR a day and its
latest 12,969 NEAR a day. In between it dropped after the first week, rose from April to September and has fallen
since. A straight line fitted to the weekly totals gives anything from -91% to +1,160% a year, depending on the
week it starts from. A rate that moves that far with its starting point is not a measurement, so this thesis
does not use one: the table above says what each rate would do, and the rule waits for coverage to move in two
windows in a row. The weekly figures are DefiLlama's, which agree with the chain to 100.9% over the window this
repository reads; `python3 -m pipeline.growth` prints every fit. (An earlier version of this section reported the
fit from the first week alone, 107% a year, as an upside case; it is withdrawn, see the errata.)

HSP-029 was approved by NEAR's House of Stake on 2 November 2026. As reported by The Block and Bitcoin.com, it
still needs the House of Stake's Security Council to ratify it, then a 90-day grace period and a validator
upgrade, after which it lowers the issuance cap from 2.5% to 1.6% over 24 months, taking daily issuance from
about 89,500 NEAR to 57,300 NEAR. The 1.6% columns assume all of that has happened by the horizon. Counting in
NEAR matters: revenue earned in dollars buys fewer NEAR when NEAR's price rises, so the same business needs
faster growth in dollars when the price goes up.

**A simple model of what is needed today.** NEAR's wallets receive 4.8 basis points per dollar of reported volume. For
buybacks to match net new supply now, revenue read from the chain would have to be 6.2x what it is. At today's
rate per dollar of volume that means about $283B a year of volume, against $3.73B in the last 30 days. If net new
supply ran at 1.6%, the multiple would be 4.0x; with DefiLlama's revenue in dollars, as in section 4, the first
multiple is 5.1x. A holder is buying that
growth, or a higher take, or lower issuance.

**What the audit is worth, in money.** A holder of NEAR is exposed to NEAR Intents whether they use it or not,
because its revenue is what funds the buyback. On the public side that exposure can be checked by anyone, at any
block, for two calls per token, and a hole shows in the block where it opens, to anyone reading that block. It
is the one part of NEAR's investment case we could verify end to end without trusting the party being valued,
and it held up: whole today, and short only when something was in fact wrong. Measured against the revenue
that funds the buyback, October's hole at its largest was 2.1 months of it, and it was closed. The balance now beyond
the audit is 6.2 years of it. That is a scale for what the audit cannot see, not an estimate of a loss: nothing
public says that balance is short, and nothing public can show that it is whole.

**Why 1% and not none.** The evidence argues for holding little, and a reader could fairly take it to none. We
do not, for three reasons we can point to. The part we could check held up. The growth a holder needs is large
but stated: 46% a year in NEAR to cover new supply by 2031, or 33% a year if HSP-029 takes effect, against a float
that grew 2.8x in four months. And the one thing that would let us hold more, a disclosure, is something NEAR can
do by itself. We give a horizon and the growth it needs; we do not give a price target or an expected return,
because nothing we can check supports one.

## 6. What would change our mind

The rating moves on four things, and only these. Each is read by code, and the first three are written down
with dates in [`PREREG-AUDIT.md`](PREREG-AUDIT.md), hashed on 13 November before the next reading existed:

| What | Moves the rating to | Read how | Dated test |
| --- | --- | --- | --- |
| A hole in the public books stays open beyond 3 readings | Exit | Credited against held for the tracked tokens, every reading | G3, to 2027-03-31 |
| The audit can no longer be run: either question stops answering | Exit | The same two calls | G4, on 2027-03-31 |
| NEAR publishes the private chain's totals per token against a block height | Add | By hand | D1, on 2027-03-31 |
| Coverage below 10%, or at least 25%, in two 30-day windows in a row | Exit, or Add | `pipeline/revenue.py` and two block headers | R4's thresholds, written on 13 November |

G1, that no tracked token is short on the 2026-11-14 reading, has passed; G2 is due on the 2026-11-17 reading.
The README's results table, written by the scoring code, shows each as it is scored, and a fail is reported as a
fail.

The disclosure does not have to reveal anyone's balance: committing to each balance and proving the sums, a
proof of liabilities, is a known technique that publishes totals and nothing else. With it, the two calls cover
everything, and the largest risk in section 4 mostly goes away.

The readings about the float, in Appendix A, do not move the rating in either direction. Growth there is use of
the product and money moving beyond the audit at once.

## 7. What could not be computed, and other limits

- **What the audit covers.** The public ledger, `intents.near`, against each token's contract on NEAR. Most of
  those tokens are themselves issued on NEAR by a bridge for tokens that live on another chain. Whether the
  bridge holds those is a further question that this audit does not ask. The audit takes `mt_batch_supply` as
  the sum of all credits and does not rebuild it from every account.
- **Whether the alarm cries wolf.** Whether a hole of any size, or a new low, also appears at times when nothing
  is wrong is measured by auditing blocks drawn at random between the first reading and the pinned one
  (`python3 -m pipeline.audit --sample 200`, seeded): outside the October hole, 0 of 199 short and 0 of 199 with
  a new low. Zero in that many draws bounds the false-alarm rate per block at about 1.5%; it does not show the
  rate is zero, and a reader who checks every block would need a far larger sample to promise a quiet alarm.
  Checks that returned nothing were all tokens not yet on the books at that block, the same tokens the daily
  readings lack then.
- **A standing surplus and a small hole.** Whether credited is above held would miss a hole smaller than the
  surplus a token already carries, as USDC on NEAR does. The second test, a new low of held minus credited,
  covers that case on the stored readings, and `make audit` and the dashboard's button compare a live reading
  with the lowest of the token's last 30 stored readings. That comparison is new and has no dated test of its
  own: the tests in `PREREG-AUDIT.md` were hashed before it was written and are about the sign only.
- **Tokens chosen with hindsight.** The history audits the 20 tokens that were largest on the pinned day. A
  token that broke and was delisted before then would not be in it, and a token is counted only from the day it
  has a balance, so the earliest checks of some tokens compare nothing with nothing.
- **Which tokens.** On the pinned day: the tokens in NEAR Intents' list as first fetched that have a balance to
  read, and the unlisted ones the treasury holds. 15 tokens joined the list later that day and are left out of
  every pinned figure. Read once at the pinned block, they hold $291,069 in all. None is short and none is in the
  treasury. With them the private share would print as 60.9%.
- **A replay, not detection.** The block-by-block record of the October hole was made on 13 November. Its steps
  were found by halving the days between daily readings; two changes that cancel between two blocks that were
  read are not seen. Payout and upgrade times are CertiK's and are quoted.
- **How often.** One block a day since 18 February, for the 20 tracked tokens only; every listed token on the
  pinned day alone. A hole that opened and closed between two readings is not in it. The button on the
  dashboard reads the latest block only when someone presses it.
- **Revenue read from the chain for two windows only.** The wallets' balances are read at every stored day, but
  the transfers behind them only from mid-September; earlier revenue figures are DefiLlama's. Revenue is NEAR
  and wNEAR received, as DefiLlama counts it; NEAR the wallets hold inside `intents.near` is not counted.
- **Swap volume and fees.** Not computable from the chain since 27 October for the swap leg. They are quoted
  from DefiLlama and labelled. The NEAR Intents Explorer API needs a partner key and returns the operator's own
  figures, so it would not change that.
- **Activity tables.** NEAR's BigQuery public dataset is not used: querying it needs a Google Cloud account (the
  free sandbox needs no card), which would break this repository's rule of no key and no account. NearBlocks'
  public daily counts give the same series without one, and the lead-lag test in section 2 uses them.
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
  not be counted at all. DefiLlama shows a smaller total for NEAR Intents than ours; we did not reconcile the two.
- **The treasury account and 1Click.** The docs name this account for the confidential flow. That 1Click's swaps
  go through it is shown for the 9 swaps we found, on six days after 27 October, not for every swap.
- **The exploit is matched by token, size and time, not by transaction.** We did not trace the attacker's
  transactions or follow the tokens on BNB Chain.
- **The reward programme.** Its rules are taken from NEAR's blog post and press release (`docs/SOURCES.md`). We
  did not measure how many wallets qualified.
- **HSP-029.** Its status is as reported by The Block and Bitcoin.com on 3 November 2026. We did not read the
  vote on chain.
- **No growth rate.** The weekly revenue since the buyback began gives a fitted rate anywhere from -91% to
  +1,160% a year depending on the start week, so none is used. The series is DefiLlama's, checked against the
  chain for two months only.
- **Where the revenue comes from.** Traced one step back, from two public indexes, with a sample re-read from the
  chain. Only the latest 30 days are traced; the index refuses about half its calls at one a second. Payments made
  from balances a payer already held are not explained and count as neither, so the share is a floor for money
  that came through the treasury. It says which way the money came, not what it was for.
- **The buyback NEAR.** The wallets' balances are read at each day's block, their transfers only from 14
  September. What their signers will do with the NEAR cannot be read from the chain.
- **Staking.** The reward is net new supply over the stake of one epoch, before any validator's fee. It moves with
  the stake and with issuance, and it is a share of supply, not a return in dollars.
- **The scenarios are arithmetic, not a forecast.** Revenue and supply compound at constant rates, the lower
  issuance is taken as fully in force at the horizon, and nothing is said about how likely any rate is.
- **Quoted figures.** Volume and fees come from DefiLlama, and one NEAR price a day from CoinGecko through
  DefiLlama. Two NEAR prices are therefore in use: the float is valued at NEAR Intents' own list, and the supply
  at CoinGecko's price at the pinned block. The last day before the pin is left out of the quoted windows
  because its fee figure was incomplete.
- **One provider.** Readings come from one public archival node. One historical read was repeated on a second
  node and matched (`data/context/cross_check.json`). Set `ARCHIVAL_RPC` to repeat the whole check elsewhere.
- **Not covered.** Competitors, regulation of private settlement, and who the private chain's validators are.

This is research, not investment advice.

## Appendix A. The private side's growth: this project's first question

This project began by asking whether the money behind the private chain keeps growing. Its readings and dated
tests stay as written on 13 November, and hashed where they are in `PREREG.md`. They do not move the rating.

After 27 October the float is an adoption measure that cannot be restated afterwards, and it can be inflated
while it is read: a table can be restated by whoever keeps it, a token balance at a past block cannot, but a
reward or an interested party can put balances there for a while. So these readings also look at the float
without NEAR's own token, and at how much of it arrived on a few days.

R1, R2, R3 and R5 are produced by this repository's pipeline at the pinned prices and scored by `python3 -m
pipeline.score` once their reading exists.

| # | Reading | Now | The private side is growing if, on 2027-03-31 | It is not if |
| --- | --- | --- | --- | --- |
| R1 | Private float | $136.4M | at least $200M | below the pinned day's level |
| R2 | Ten best days as a share of the float | 55% | below 45%: new money arrives on many days | still above 55% |
| R3 | Private share, the 20 tracked tokens | 62.3% | at least 50% | below 40%: money is moving back to the public side, where it can be audited |
| R4 | Revenue reaching NEAR's wallets as a share of net new supply | 16% read from the chain | at least 25% | below 10% |
| R5 | Float without NEAR's own token | $92.9M | at least $130M | below the pinned day's level |

Between the two a reading is undecided. The scoring code is stricter than this table: it prints FAIL for
anything short of the first column. R2 depends on R1: if the float does not grow, R2 can only improve when lumps
leave, and the round trip in section 4 shows it overstates new money. R4 was written as DefiLlama's revenue,
each day turned into NEAR at that day's price (15%); from 14 November it is read from the chain, and it is the
one reading the rating uses. R5 was added on the same day as the others, after we learned of the reward
programme; `PREREG.md` records the amendment.

**First results, 14 November.** The shorter tests on the float were scored on the 2026-11-14 reading, the first
one taken after they were written. E2 and E3 passed: no single day added a lump, and the tracked share was
61.9%. E1 failed: the float had to be at least $136.4M and it was $135.2M. The part without NEAR's own token was $91.1M,
down $1.8M in a day; 5 of that series' 268 earlier daily changes were falls at least that large. The whole float
fell on 37% of the days up to the pinned one, so one fall is ordinary and settles nothing about March. It is
reported because we said a fail would be.

**How likely are R1 and R5? A base rate from the float's own history.** `make model` replays the float's past
daily changes forward to 2027-03-31: 10,000 paths from one seed, each built from runs of 7 consecutive past days
drawn at random, each scored with the thresholds above. The readings were fixed and hashed before this model
was written, so it did not shape them.

| Days the paths are drawn from | R1 holds | R5 holds | Median float on the day |
| --- | --- | --- | --- |
| Every day since the first deposit | 53% | 72% | $202.6M |
| Only days before the reward programme was announced | under 1% | under 1% | $170.0M |
| Only days since the first reward's snapshot was triggered | 82% | over 99% | $258.7M |

On the whole history R1 is close to a coin flip, and R2 holds on 67% of paths. At the pace before the reward
neither R1 nor R5 holds: both need the pace of the last two months to continue, and that pace has a reward and
a promised second round behind it. The result also moves with the length of the runs. From single days to runs
of 30 days, R1 on the whole history holds on 51% to 60% of paths, and on the last window on 38% to 96%, because that
window is short and contains the September exit. A run of 7 days cannot start in the last 6 days of a window,
so those days and the first ones are drawn less often; when runs may wrap, R1 on the last window holds on 89%
of paths, not 82%. This is a base rate, not a forecast: changes are in dollars, nothing compounds, and the
model knows nothing about why money moved. `python3 -m pipeline.model --help` lists the settings.
