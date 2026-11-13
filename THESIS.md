# Waterline: a NEAR thesis built on what anyone can check

Pinned to NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). Every number in this file is either computed
from the data (`data/derived/claims.json`) or a declared constant (`data/constants.json`), and `make check`
fails if one is not.

## The thesis in six sentences

NEAR's investment case leans on one product, NEAR Intents, whose revenue funds the NEAR buyback. On 27 October
2026 its 1Click swaps began to settle on a private chain, so the swap itself can no longer be checked by an
outsider. One thing still can: the money locked behind that chain, which sits in a public contract. That money,
the float, went from zero in February to $136.4M and is now 61.0% of everything NEAR Intents holds. But NEAR
pays a reward for keeping money there, the largest inflow has mostly left again, and for two days in October
one token in it had almost nothing behind it. We would hold NEAR as a small bet on private settlement, and we
name the readings that would change our mind.

## 1. What changed on 27 October

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
the `near` name since November 2025. What 27 October removed is the cross-check: until then an outsider could
compare those figures with public settlement in `intents.near`.

| Number | Latest value | Where it comes from | Can an outsider recompute it from the chain? |
| --- | --- | --- | --- |
| Swap volume, 30 days | $3.73B | A table uploaded to Dune under the `near` name, read by DefiLlama; also NEAR's own Explorer | Not the swap leg. Shield and unshield flows yes, with an indexer; not done here |
| Gross fees, 30 days | $6.0M | Tables uploaded to Dune under the `near` name | No |
| Revenue reaching NEAR's wallets, 30 days | $1.8M | NEAR received by three public wallets | Yes, with an indexer; quoted here |
| Net new NEAR supply | 88,704 NEAR a day | Block headers | Yes, this repository |
| Private float | $136.4M | Balances of one account in `intents.near` | Yes, this repository |

We are not saying the uploaded numbers are wrong. They are reported, not observed, and a thesis should say which
of its inputs are which. Sources for every row: `docs/SOURCES.md`.

## 2. What the float shows

The float is every token held in `intents.near` by the treasury account that backs the private chain. We read it
at one block a day since the account was created. Dollar figures use one fixed price list, so a change in the
series is a change in tokens, not in prices.

**It is large and it grew.** First reading with a balance: 2026-02-19. $49.3M at the B2B launch on 13 July.
$136.4M on the pinned day, 2.8x in four months, across 205 token types. That is also the highest it has been.

**Most of NEAR Intents is already behind it.** On the pinned day we asked the contract of every token in NEAR
Intents' own token list how much `intents.near` holds: 180 tokens with a price, $223.8M in total. The private
side is 61.0% of that. It is not even across assets: NEAR 69.9%, stablecoins 68.2%, ZEC 60.3%, ETH 57.5%, and
bitcoin only 28.8%.

Through time we follow the 20 largest tokens by total held, which cover 89% of that total. Their private share
was 6% at the start of April, 36.2% just after the July launch, 56.2% the day before the switch and 62.3% on the
pinned day. Over the same months the public side did not grow: $83.5M in April, $75.0M now. The growth was on
the private side.

**It is not only NEAR's own token.** Stablecoins are the largest group (Stablecoins: $49.3M) ahead of NEAR's own
token (NEAR: $43.5M). 68% of the float is not NEAR's own token. We do not know who the depositors are.

**Part of it is paid for.** On 11 June 2026 NEAR announced a reward for holding a confidential balance: a pool
of locked tokens that convert to NEAR, shared among wallets that keep more than $100 there and make at least
one confidential swap, with the snapshot taken once confidential balances reach $70M and no wallet receiving
more than 2%. On 17 September NEAR announced that the $70M had been reached and the snapshot triggered. A second
round is promised. The float grew by $7.9M per 30 days before the programme, $14.3M per 30 days while the first
reward was open, and $31.8M per 30 days since its snapshot was triggered. So growth did not stop when the first
reward closed. But with another round promised, nobody outside can separate use from reward-seeking, and we do
not claim to.

**The NEAR in it is hot money.** The ten best days add up to $75.5M, which is 55% of the float. Between the
readings of 15 and 28 September, the days around the snapshot announcement, 12.6M NEAR entered. In one day at
the end of that month 3.9M NEAR left, the largest one-day fall in the series ($14.6M), and 69% of that inflow
has now gone. Without NEAR's own token the float is steadier: $46.1M at the snapshot, $92.9M now, 3.5x since the
July launch, and its worst day ever is a fall of $2.7M.

**The switch itself moved little.** Across 27 October the float changed by 2.8%. Swaps pass through the private
chain and leave. What stays is inventory and balances people choose to keep there. So the float is not a
measure of activity. It is a measure of commitment: how much money is willing to rest behind a chain nobody
outside can read. In the 17 days since the switch it has added $20.7M.

**The reading caught a real shortfall.** The pipeline refuses to compute a share when the ledger credits the
treasury with more of a token than `intents.near` holds. That happened on 2 readings, 1 and 2 October, for one
token: the old BNB Chain USDT id, which is bridged by HOT. On the 2 October reading `intents.near` held 67,669
of it while the treasury alone was credited 3,373,849. That is $3.3M, 98% of the treasury's claim on that
token, with nothing behind it. On the 2026-10-03 reading it was whole again.

We found this before we knew what it was. It matches a published incident: CertiK reports five payouts from the
bridge's BNB Chain treasury between 30 September 23:54 UTC and 1 October 06:08 UTC, $3.86M in all, caused by a
refund bug that left credit inside NEAR Intents after the backing tokens were returned; an upgrade of
`intents.near` on 2 October at 20:31 UTC; and NEAR Intents' general manager saying the money was returned in
full. Our readings bracket each of those times.

Two things follow. The backing of the float can break, and has. And when it broke on the public ledger, an
outsider could see it within a day by asking two contracts one question each. Nothing like that question can be
asked of the private chain.

## 3. What that means for a NEAR holder

**The price needs growth, and the recent trend is down.** The value of NEAR's total supply is $4.48B. Net new
supply runs at 88,704 NEAR a day, $110.7M a year. Counted NEAR against NEAR, the revenue that reaches NEAR's
wallets covers 15% of that, and the supply is worth 265x that revenue. Over the latest 30 days against the 30
before, reported volume is -22%, reported fees -26% and that revenue -20%.

**A simple model of what is needed.** NEAR's wallets receive 4.8 basis points per dollar of reported volume.
For buybacks to match net new supply, revenue has to grow 6.5x. At today's rate per dollar of volume that means
about $297B a year of volume, against $3.73B in the last 30 days. A holder is buying that growth, or a higher
take, or lower issuance.

**After 27 October, the float is the adoption measure that cannot be misreported. It can be rented.** A table
can be restated by whoever keeps it. A token balance in a public contract cannot. But a reward, or an
interested party, can put balances there for a while. So we read two things: the float without NEAR's own
token, which doubled in the eight weeks since the first snapshot with no large falls, and what remains once
rewards have been paid.

**The same float is an unpriced risk, and one key holds it.** $136.4M is described as "backed 1:1" by the
treasury. The treasury is public. What the private chain owes is not, and nothing published proves the two
match. October showed the failure is not hypothetical: a single bug left one token 98% unbacked for two
readings, on the public side, where it could be seen and was repaired in two days. And the treasury is not a
contract: it is an ordinary account with 1 key registered for it inside `intents.near`. Nothing public says who
holds that key or how.

**Our position.** Hold NEAR as a small position, an option on private settlement, not as a cash-flow asset. The
case for holding any: the private side keeps taking a larger share of what NEAR Intents holds, in assets other
than NEAR's own, and it kept growing after the first reward closed. The case against holding much: revenue is
15% of dilution and falling, a reward is still in force, the largest inflow was transient, the backing has
already failed once, and one key holds it. We would add if the readings below hold, and cut if R3 or R5 breaks.
We do not give a price target: nothing we can check supports one.

## 4. The readings that would change our mind

Written on 2026-11-13. R1, R2, R3 and R5 are produced by this repository's pipeline at the pinned prices and
scored by `python3 -m pipeline.score` once their reading exists.

| # | Reading | Now | Thesis holds if, on 2027-03-31 | Thesis breaks if |
| --- | --- | --- | --- | --- |
| R1 | Private float | $136.4M | at least $200M | below the pinned day's level |
| R2 | Ten best days as a share of the float | 55% | below 45%: new money arrives on many days | still above 55% |
| R3 | Private share, the 20 tracked tokens | 62.3% | at least 50% | below 40%: money is moving back to the public side |
| R4 | Revenue reaching NEAR's wallets as a share of net new supply, NEAR against NEAR | 15% | at least 25% | below 10% |
| R5 | Float without NEAR's own token | $92.9M | at least $130M | below the pinned day's level: the rest was rented too |

Between "holds" and "breaks" a reading is undecided. R2 depends on R1: if the float does not grow, R2 can only
improve when lumps leave. R4 is the last 30 complete days of DefiLlama's revenue, each day turned back into NEAR
at that day's price, over 30 days of net new supply from block headers. It uses a quoted figure, so it is
scored by hand. R5 was added on the same day as the others, after we learned of the reward programme;
`PREREG.md` records the amendment.

Shorter tests resolve on the 2026-11-14 and 2026-11-17 readings: the float does not fall, no single day adds
another lump, and the tracked share stays at 60% or more. They are written, with their thresholds and their
base rates, in [`PREREG.md`](PREREG.md). A fail will be reported as a fail.

One more item has no threshold. If NEAR publishes a proof that the private chain's balances add up to the
treasury, the risk in section 3 mostly goes away and we would hold more.

## 5. Limits

- **One price list.** Dollar history is in the prices NEAR Intents' own list showed on 2026-11-13. It shows
  tokens moving, not what the float was worth on each past day. NEAR's "$70M" in September was measured at that
  day's prices, not ours. The list changed during the day: ids that appeared later were added at the price
  first seen, and an id already pinned kept its price.
- **Unpriced tokens.** 30 of the 205 token types have no price in that list. They are counted and left out of
  every dollar figure, so the float is understated by an unknown amount.
- **Coverage of the share.** The 61.0% counts every token in NEAR Intents' token list that has a price and a
  balance inside `intents.near`. 27 listed ids are of another kind (`1cs_v1:`), are not balances inside
  `intents.near`, and are not counted. A token that `intents.near` holds but NEAR Intents does not list would
  not be counted at all. The history follows 20 tokens chosen by their size on the pinned day, read once a week
  before 23 October and daily after. DefiLlama shows a smaller total for NEAR Intents than ours; we did not
  reconcile the two.
- **The treasury account.** The docs name this account for the confidential flow used by market makers. That
  1Click's private settlement since 27 October uses the same account is our inference from the docs and from
  the account's daily movements. We did not trace a 1Click swap's shield transaction to it.
- **The shortfall is matched by token, size and time, not by transaction.** We did not trace the attacker's
  transactions. The shortfall we measure is a lower bound: it compares what `intents.near` held with the
  treasury's credit alone, not with every other holder's credit.
- **The reward programme.** Its rules are taken from NEAR's blog post and press release (`docs/SOURCES.md`). We
  did not measure how many wallets qualified, and we did not trace who deposited the NEAR that arrived in
  September.
- **One reading a day.** Money that enters and leaves between two midnights is not seen. That is why this is a
  float series and not a volume series. Shield and unshield flows could be counted with an indexer; we did not.
- **Assets, not liabilities.** The treasury shows what backs the private chain. It cannot show what the private
  chain owes. If the private chain is also backed somewhere other than this one account, we do not see it.
- **Quoted figures.** Volume, fees and revenue come from DefiLlama, and one NEAR price a day from CoinGecko
  through DefiLlama. We did not recompute them. The last day before the pin is left out because its fee figure
  was incomplete. The valuation figures in section 3 and R4 depend on them.
- **One provider.** Readings come from one public archival node. One historical read was repeated on a second
  node and matched (`data/context/cross_check.json`). Set `ARCHIVAL_RPC` to repeat the whole check elsewhere.
- **Readings written the same day.** R1 to R5 were written on the day the data was first assembled, not before.
  Only the tests in `PREREG.md` are scored on readings taken after they were written.
- **Not covered.** Competitors, regulation of private settlement, and who the private chain's validators are.

This is research, not investment advice.
