# Waterline: a NEAR thesis built on what anyone can check

Pinned to NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). Every number below is in
`data/derived/claims.json` and is rebuilt and compared by `make check`.

## The thesis in five sentences

NEAR's value rests on one product, NEAR Intents. On 27 October 2026 that product moved its 1Click swaps to a
private chain, so the activity numbers the market quotes can no longer be recomputed by an outsider. One thing still
can: the money locked behind that chain, which sits in a public contract. That money, the float, went from zero
in February to $132.3M, and it is now 60.2% of everything NEAR Intents holds. We are constructive on NEAR as a
growth bet on private settlement, and we name the four readings that would change our mind.

## 1. What changed on 27 October

NEAR Intents runs two ledgers. `intents.near` is public. FAR is, in the docs' words, "a permissioned instance of
the NEAR protocol operated by a small validator set with no public networking". The changelog entry for the day:

> From October 27, 2026, 1Click swaps settle confidentially. [...] The swap settles on the NEAR Private Shard,
> so `nearTxHashes` has no hash for the swap. It has the hashes for the shield and the unshield instead.

A swap on FAR is "invisible to public indexers" (same docs). What the public chain still shows is money going in
(shield) and coming out (unshield), and the account that holds it in between.

That changes what each headline number is worth as evidence:

| Number | Latest value | Where it comes from | Can an outsider recompute it from the chain? |
| --- | --- | --- | --- |
| Swap volume, 30 days | $3.77B | A table NEAR's team uploads to Dune, read by DefiLlama | No |
| Gross fees, 30 days | $5.8M | Tables NEAR's team uploads to Dune | No |
| Revenue reaching NEAR's wallets, 30 days | $1.8M | NEAR received by three public wallets | Yes, with an indexer |
| Net new NEAR supply | 88,704 NEAR a day | Block headers | Yes, this repository |
| Private float | $132.3M | Balances of one account in `intents.near` | Yes, this repository |

We are not saying the uploaded numbers are wrong. We are saying they are now reported, not observed, and a
thesis should say which of its inputs are which. Sources for every row: `docs/SOURCES.md`.

## 2. What the float shows

The float is every token held in `intents.near` by the treasury account that backs the private chain. We read it
at one block a day since the account was created. Dollar figures use one fixed price list, so a change in the
series is a change in tokens, not in prices.

**It is large and it compounds.** First balance on 2026-02-19. $49.3M at the B2B launch on 13 July. $132.3M
today, 2.7x in four months, across 205 token types.

**Most of NEAR Intents is already behind it.** On the pinned day we asked the contract of every token in NEAR
Intents' own token list how much `intents.near` holds: 158 tokens with a price, $219.6M in total. The private
side is 60.2% of that. It is not even across assets: NEAR 69.9%, stablecoins 67.5%, ZEC 60.3%, ETH 57.5%, and
bitcoin only 28.8%.

Through time we follow the 20 largest tokens by total held, which cover 90% of that total. Their private share
was 6% at the start of April, 36.2% just after the July launch, 56.2% the day before the switch and 61.8% on the
pinned day. Over the same months the public side did not grow: $83.5M in April, $75.7M now. Everything new went
to the private side.

**It is not NEAR parked in NEAR.** Stablecoins are the largest group (Stablecoins: $47.6M) ahead of NEAR's own
token (NEAR: $43.5M). Two thirds of the float is other people's assets.

**It arrived in lumps.** The ten best days add up to $75.0M, which is 57% of today's float. Between 15 and 28
September, 12.6M NEAR entered. In one day at the end of that month, 3.9M NEAR left. The largest one-day fall in
the whole series is $14.6M. A float built this way belongs to a small number of large holders, and it can leave
the way it came.

**The switch itself moved nothing.** Across 27 October the float changed by 2.6%. Swaps pass through the
private chain and leave. What stays is inventory and balances people choose to keep there. So the float does
not measure activity. It measures how much money is willing to rest behind a chain nobody outside can read.
Since the switch it has added $18.0M.

## 3. What that means for a NEAR holder

**The price is a growth price.** NEAR's market value is $4.62B. Net new supply runs at 88,704 NEAR a day,
$114.0M a year. Revenue that reaches NEAR's wallets covers 20% of that, and the market value is 207x that
revenue. Nobody holds NEAR at this price for today's cash flow. They hold it because they expect Intents to grow
several times over.

**After 27 October, the float is the growth signal that cannot be reported into existence.** Volume can be
restated by whoever keeps the table. A token balance in a public contract cannot. If Intents is growing the way the reported volume says, the float and the
revenue wallets will show it. If they stall while reported volume climbs, believe the chain.

**The same float is NEAR's largest unpriced risk.** $132.3M is described as "backed 1:1" by the treasury. The
treasury is public. What the private chain owes is not, and nothing published proves the two match. A shortfall
would stay invisible until a withdrawal failed. For a token whose value depends on this one product, that is a
tail risk no dashboard shows today.

**Our position.** Constructive on NEAR over a multi-year horizon, sized as a bet on one product. Private
settlement has found real demand, and the demand is in assets (stablecoins, bitcoin, ZEC) that had no reason to
come to NEAR before. The position is conditional on the four readings below.

## 4. The readings that would change our mind

Written on 2026-11-13. R1 to R3 are produced by this repository's pipeline at the pinned prices and scored by
`python3 -m pipeline.score`; the dashboard keeps them current.

| # | Reading | Now | Thesis holds if, on 2027-03-31 | Thesis breaks if |
| --- | --- | --- | --- | --- |
| R1 | Private float | $132.3M | at least $200M | below today's level |
| R2 | Ten best days as a share of the float | 57% | below 45%: new money arrives on many days | above 57%: growth is still a few large moves |
| R3 | Private share, the 20 tracked tokens | 61.8% | at least 50% | below 40%: money is moving back to the public side |
| R4 | Revenue reaching NEAR's wallets as a share of net new supply | 20% | at least 30% | below 15% |

R4 uses a quoted revenue figure, so it is scored by hand.

Three shorter tests resolve on the 2026-11-17 reading: the float does not fall, no single day adds another lump,
and the tracked share stays at 60% or more. They are written, with their thresholds, in [`PREREG.md`](PREREG.md),
whose hash is checked by `make check`. A fail will be reported as a fail.

A fifth long-dated item has no threshold. If NEAR publishes a proof that the private chain's balances add up to
the treasury, the risk in section 3 mostly goes away and we would hold more.

## 5. Limits

- **One price list.** Dollar history is in the prices of 2026-11-13. It shows tokens moving, not what the float
  was worth on each past day.
- **Unpriced tokens.** 52 of the 205 token types have no price in NEAR Intents' own list. They are counted and
  left out of every dollar figure, so the float is understated by an unknown amount.
- **Coverage of the share.** The 60.2% counts every token in NEAR Intents' token list that has a price and a
  readable total on the pinned day. 27 listed tokens could not be read and are left out, and a token that
  `intents.near` holds but NEAR Intents does not list would not be counted at all. The history follows 20 tokens
  chosen by their size on the pinned day, read once a week before 23 October and daily after.
- **One impossible reading.** On 2026-10-01 the ledger credits the treasury with more of one token (the old BNB
  Chain USDT id) than that token's contract says `intents.near` held at the same block. We do not know why. The
  reading is left out of that day's share and listed in `data/derived/anomalies.json`.
- **One reading a day.** Money that enters and leaves between two midnights is not seen. That is why this is a
  float series and not a volume series.
- **Assets, not liabilities.** The treasury shows what backs the private chain. It cannot show what the private
  chain owes.
- **Quoted figures.** Volume, fees and revenue come from DefiLlama as fetched on the pinned day. We did not
  recompute them, and R4 and the valuation figures in section 3 depend on the revenue one. Revenue could be recomputed from chain data with an indexer; volume and fees could not.
- **One provider.** Readings come from one public archival node. One historical read was repeated on a second
  node and matched (`data/context/cross_check.json`). Set `ARCHIVAL_RPC` to repeat the whole check elsewhere.
- **Who the holders are.** The lumps suggest few holders. This version does not name them.
- **Readings written the same day.** R1 to R4 were written on the day the data was first assembled, not before.
  Only the tests in `PREREG.md` are scored on readings taken after they were written.

This is research, not investment advice.
