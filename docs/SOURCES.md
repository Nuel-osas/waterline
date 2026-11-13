# Sources and constants

Every constant this project depends on, with where it came from and how it was checked.

| Constant | Value | Source | How it was checked |
| --- | --- | --- | --- |
| Public ledger | `intents.near` | NEAR Intents docs, "Confidential Intents": "`intents.near` is the smart-contract ledger that credits deposited balances" | View calls `mt_tokens_for_owner` and `mt_batch_balance_of` answer on mainnet |
| Private-chain treasury | `51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe` | Same page: the example asset id `imt:51e8f94d...7cbe:nep141:wrap.near`, with "This account ID (`PRIVATE_TREASURY_ACCOUNT_ID` in solver configs) is a production constant shared by all participants." The solver example page lists the same id among "production constants shared by all solver operators" | The account was created on 2026-02-18 (NEAR Blocks, transaction `5BfpVdVufdZD3xim5JYWkBFa1e69DfqLLadk3HGZLdLX`); this project's first non-zero reading is 2026-02-19 |
| What the treasury means | "Each IMT is backed 1:1 by the corresponding tokens locked in the Treasury smart-contract account on the public chain." | Same page, "Asset identifiers" | Quoted, not verified: nothing public proves the private ledger's total equals the treasury. That gap is one of the thesis's risks |
| Private chain | "FAR is a permissioned instance of the NEAR protocol operated by a small validator set with no public networking. Balances and swap details on FAR are not visible to the public" | Same page, "How it works" | Quoted |
| Switch date | 2026-10-27 | NEAR Intents changelog: "From October 27, 2026, 1Click swaps settle confidentially. The API is unchanged. As an integrator, you don't need to change anything. Swap data stays on the NEAR Intents Explorer, so this does not mean that 1Click is only Confidential Intents. The swap settles on the NEAR Private Shard, so `nearTxHashes` has no hash for the swap. It has the hashes for the shield and the unshield instead." | Quoted in full. The entry does not name the treasury account; that 1Click uses the same one is our inference |
| B2B launch | 2026-07-13 | NEAR Intents changelog: "Confidential Intents B2B launch" | Quoted |
| Token prices and decimals | `data/tokens.json` | `https://1click.chaindefuser.com/v0/tokens` (NEAR Intents' own token list), fetched once at the time recorded in the file | Pinned. Used for dollar figures. A single token's share needs no price; combined shares weight tokens by these prices. The list changed during the day: `pipeline.context tokens` adds ids that appear later and never changes a pinned price |
| Reported volume, fees, revenue | `data/context/defillama.json` | DefiLlama API, `summary/dexs/near-intents` and `summary/fees/near-intents` | See "Where the reported numbers come from" below |
| Archival node | `https://archival-rpc.mainnet.fastnear.com` | FastNEAR public archival RPC | One historical read was repeated against `https://archival-rpc.mainnet.near.org` and returned the same bytes; the call and both answers are in `data/context/cross_check.json` |

Docs pages: <https://docs.near-intents.org/integration/market-makers/confidential-intents> and
<https://docs.near-intents.org/changelog/overview>.

## NEAR's reward for confidential balances

- Rules: NEAR's blog post, <https://near.org/blog/milestone-incentive-program> (announced 2026-06-11). As read on
  2026-11-13: a first pool of 333,333 locked tokens; snapshot when confidential balances reach $70M; a wallet
  qualifies by keeping more than $100 in a confidential balance and making at least one confidential swap; no
  wallet receives more than 2%; the tokens convert 1:1 to NEAR once NEAR's volume-weighted price holds at or
  above $3.33 for three days; later rounds are promised.
- The trigger: NEAR's press release of 2026-09-17, "near.com's Confidential TVL Reaches $70 Million, Triggering
  the NEAR@3.33 Snapshot",
  <https://www.prnewswire.com/news-releases/nearcoms-confidential-tvl-reaches-70-million-triggering-the-near3-33-snapshot-amid-industry-wide-privacy-wave-302881903.html>.
- Both are paraphrased, not quoted. The two dates are the constants `REWARD_ANNOUNCED` and `REWARD_TRIGGER` in
  `pipeline/build.py`.

## The audit: credited against held

- Credited: `intents.near.mt_batch_supply({"token_ids": [...]})` returns, for each token id, the total the ledger
  has credited to all accounts together (`mt_supply` is the same for one id). Stored per day in
  `data/credited/<day>.json`, read at the day's block. How it was checked: on the pinned day the answer equals,
  to the last unit, what the token's own contract reports for 184 of 214 tokens, and is slightly below it for
  the other 30, which is what a sum of credits should do; it is above it only for one token on three readings,
  all inside a published exploit.
- Held: `ft_balance_of(intents.near)` on the token's contract for `nep141:` ids, `mt_balance_of(intents.near, id)`
  for `nep245:` ids. Stored per day in `data/held/<day>.json`.
- Live: `make audit` and the dashboard's button ask the same two questions at the latest final block. The button
  uses `rpc.mainnet.fastnear.com`, `free.rpc.fastnear.com` and `rpc.mainnet.near.org`, in that order, from the
  visitor's browser; all three were checked on 2026-11-13 to answer cross-origin requests.
- What it does not cover: most tokens on the ledger are issued on NEAR by a bridge for tokens that live on
  another chain. Whether the bridge holds those is not asked here.

## The October hole, block by block

- The token: `nep245:v2_1.omni.hot.tg:56_2CMMyVTGZkeyNZTSvS5sarzfir6g`, a dollar token bridged from BNB Chain by
  HOT, listed by NEAR Intents as `USDT(DEPRECATED)` with 18 decimals.
- Our record: `data/context/exploit.json`. Every block between the readings of 2026-09-29 and 2026-10-03 at which
  credited minus held was found to change, with both totals before and after and the block time. Found by
  halving (`python3 -m pipeline.audit --steps 2026-09-29 2026-10-03`, about 1,200 reads, slow on a public
  node). The scan starts from a grid of readings two hours apart, so two changes that cancel between two blocks
  that were read are not in it. `make verify` re-reads the three blocks the claims rest on, each with the block
  before it: where the hole opens (217799506), its peak, and where it closes (218251129).
- The published incident: CertiK, "HOT Bridge / NEAR Intents", 2026-10-08,
  <https://www.certik.com/blog/hot-bridge-near-intents>. As read on 2026-11-13 it lists five payouts of USDT
  from the bridge's BNB Chain treasury (2026-09-30 23:54:30 UTC 800,000; 2026-10-01 00:24:02 1,200,000;
  00:50:42 1,500,000; 01:46:20 330,000; 06:08:26 35,000; 3,865,000 in all), describes the cause as a refund that
  returned the tokens backing a deposit while the credit inside NEAR Intents remained, records an upgrade of
  `intents.near` on 2026-10-02 at 20:31:41 UTC, and reports NEAR Intents' general manager saying the money was
  returned in full, which CertiK does not itself verify. The first payout and upgrade times in
  `data/context/exploit.json` are these.
- How the two line up: the hole opens at 16:14:22 UTC on 29 September at 10 of the token, grows by doubling to
  1,299,979 at 23:41:28 on 30 September, thirteen minutes before the first payout, peaks at 3,848,795 at 01:29:28
  on 1 October, and closes in seven steps between 19:26:35 and 20:22:09 on 2 October while the credited total
  stays at 3,869,502. So the chain record supports "returned in full". We matched by token, size and time; we
  did not trace the attacker's transactions or follow the tokens on BNB Chain.
- All of it was read on 2026-11-13, five weeks after the event. The first data commit of this repository lists
  the 2026-10-01 reading as an unexplained anomaly, measured then only against the private chain's own credit
  (the S rows); the match to CertiK's report and the audit against every holder's credit came afterwards.

## Where the reported numbers come from

DefiLlama's adapters are public code
(<https://github.com/DefiLlama/dimension-adapters>, read on 2026-11-13 at commits
[`d40b4ef1fe`](https://github.com/DefiLlama/dimension-adapters/blob/d40b4ef1fe/dexs/near-intents/index.ts) for `dexs/near-intents/index.ts` and
[`acd40121e8`](https://github.com/DefiLlama/dimension-adapters/blob/acd40121e8/fees/near-intents/index.ts) for `fees/near-intents/index.ts`):

- **Volume** sums `volume_amount_usd` from `dune.near.dataset_near_intents_metrics` (our paraphrase of the query).
  The file's history shows a NEAR-run source since 2025-05-26 (commit `fa31506463`, "switched to official data
  source") and this Dune table since April 2026 (commits `953fc3fe11`, `890310b5dc`).
- **Gross fees** come from `dune.near.dataset_near_intents_protocol_fees` and `dune.near.dataset_near_intents_fees`.
- **Revenue** is computed differently: NEAR and wNEAR received by three public wallets
  (`fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near`, `buybacks.multisignature.near`), read from Dune's
  decoded chain tables (`near.actions`, `near.ft_transfers`). The adapter says this revenue has been used to buy
  back NEAR since 2026-02-23.

On Dune, a table named `dune.<team>.dataset_<name>` is one uploaded by the account or team with that handle
(<https://docs.dune.com/api-reference/tables/endpoint/overview>). So the volume and gross-fee figures are
tables uploaded under the `near` handle, while the revenue figure is derived from the chain. We take the `near`
handle to be NEAR's own because DefiLlama's adapter comments call the related queries "NEAR's own" and tie them
to revenue.near.org; we did not verify who controls the handle.

## The proposal to lower issuance

HSP-029, "Establish a 24-Month Issuance Ramp to a 1.6% Target Rate Of NEAR Token Emissions", posted on NEAR's
governance forum on 2026-10-07: it would lower maximum issuance from 2.5% a year to 1.6% over 24 months.
<https://gov.near.org/t/hsp-029-establish-a-24-month-issuance-ramp-to-a-1-6-target-rate-of-near-token-emissions/42644>.
The two rates are declared in `data/constants.json`. We read the proposal's text, not its status on chain.

## Custody

`data/context/custody.json`: at the pinned block, `intents.near.public_keys_of(treasury)` returns one ed25519 key,
`view_account(treasury)` shows an account with no contract code, and `view_access_key_list(treasury)` shows one
full-access key whose nonce is still the value set when the account was created, so the account has never
signed a transaction on NEAR itself: its balances inside `intents.near` move by signed messages that the
contract checks against the registered key. For an implicit account, a single key equal
to the account id is the default. Nothing public that we found says who holds the key or how. `make verify`
re-reads both.

## The transfer followed from the chain

`data/context/trace.json`, written with `pipeline/trace.py`. Each account below was read from a receipt or a
balance at the block given, not taken from a label. None of them is named in NEAR Intents' documentation that
we found, so each is described by what it did, not by who runs it.

| Account | What it did | Block | How it was checked |
| --- | --- | --- | --- |
| `51e8f94d...7cbe` (the treasury) | Paid out 1,730,851.324698195834932526948583 NEAR by a transfer intent signed with the one key registered for it | 216973662, 2026-09-23 23:35:58 UTC | `EXPERIMENTAL_receipt` of `9tF9HZnUkAMEW78Ez4dCnZEQkJYmJepcpJ1T8pnZfU3e`; treasury balance one block before and at that block |
| `bf20691c...c5f9` | Received it on the public ledger, held it nine hours, then withdrew it as plain NEAR | 217029847, 2026-09-24 08:52:21 UTC | `EXPERIMENTAL_receipt` of `5WtU7FG6E27HuCTnDopXK42on49dVaj9kVtY1sseuYZy` |
| `6ec9de2f...fbfd` | A NEAR account that received the plain NEAR and passed it on eight seconds later | 217029864 | FastNEAR transfers index only (transaction `B4nXBFdnofcrUKNmwwxL7awiff8yj57CaMdgH5fQ6gsY`); not re-read from the chain |
| `bridge-mng.near` | Wrapped it and deposited it into `intents.near`, crediting the next account | 217029871 | `EXPERIMENTAL_receipt` of `3pAwqgD3BitCtrb7LKANSmUvJJbEKeU9SMtqxkojrFEZ` |
| `7bb16411...3f2f` | Received the deposit and sent it to the treasury four seconds later. It has no other transfer | 217029878, 2026-09-24 08:52:40 UTC | `EXPERIMENTAL_receipt` of `CZ6jeGYpCZtESVcoDgT9xHSiQyVPmQrVrrs9MqgX5zvi`; treasury balance one block before and at that block |

How the block was found: the treasury's wNEAR balance is a view call at any past height, so the day between the
readings of 24 and 25 September was halved 17 times, each time keeping the half whose balance changed more,
down to one block (19 balance reads). `EXPERIMENTAL_changes` then names the receipts that changed
`intents.near` in that block. `make trace` repeats this. `make verify` re-reads the four receipts and the four
balances. Full account ids are in the file.

## Who moved the NEAR in September

- Source: FastNEAR's transfers index, `POST https://transfers.main.fastnear.com/v0/transfers` with
  `{"account_id": <treasury>, "asset_id": "nep245:intents.near:nep141:wrap.near", "from_timestamp_ms", "to_timestamp_ms", "limit": 100, "resume_token"}`.
  No key. 100 rows a page; it answers HTTP 429 when asked faster than about once every two seconds.
- It is an indexer's list, not a chain read, so it is tested before use: for each day, the transfers between the
  two daily readings (by block height) must add up, to the last unit, to the change in the wNEAR balance stored
  in `data/float/`. All 20 days from 2026-09-12 to 2026-10-01 do. `make check` repeats that test from the files.
- Stored: `data/context/flows.json`, one entry a day: gross in and out, each account that moved 1,000 NEAR or
  more that day, the rest added up, and the largest single transfer each way with its receipt id. The raw pages
  (about 2 MB a day) are not committed; `python3 -m pipeline.flows --pull 2026-09-12 2026-10-01` fetches them
  again, in about an hour and a half.
- `solver-priv-liq.near` is a named account with no contract code (checked with `view_account` at the pinned
  block). It is not named in NEAR Intents' documentation that we found. We describe it by what the list shows.

## How a reading is taken

For each day, one block stamped just after 00:00 UTC. From 2026-11-14 it is the first block stamped at or after
00:00:00 UTC, and `make verify` checks that. For earlier days it is some block in the first 15 seconds, so the
heights in `data/blocks.json` are the record: re-pulling such a day from scratch can choose a neighbouring
block. At that exact height:

1. `intents.near.mt_tokens_for_owner(treasury)` lists the token ids, then `mt_batch_balance_of` returns the balances
   (`data/float/<day>.json`).
2. For each tracked token, the token's own contract is asked how much `intents.near` holds:
   `ft_balance_of(intents.near)` for `nep141:` ids, `mt_balance_of(intents.near, id)` for `nep245:` ids
   (`data/held/<day>.json`). The tracked tokens are the 20 largest by total held on the pinned day
   (`data/tracked.json`). On the pinned day itself the same question is asked for every token in NEAR Intents'
   token list (`python3 -m pipeline.held_all <day>`), and the headline share is computed over all of them, so it
   does not depend on which tokens were picked.

A read that fails is stored as `null` and left out of every sum. It is never treated as zero.
