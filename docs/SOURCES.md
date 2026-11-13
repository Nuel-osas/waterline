# Sources and constants

Every constant this project depends on, with where it came from and how it was checked.

| Constant | Value | Source | How it was checked |
| --- | --- | --- | --- |
| Public ledger | `intents.near` | NEAR Intents docs, "Confidential Intents": "`intents.near` is the smart-contract ledger that credits deposited balances" | View calls `mt_tokens_for_owner` and `mt_batch_balance_of` answer on mainnet |
| Private-chain treasury | `51e8f94d77b5e90dc9852ca6113771e11e8382ce69473a75e313e41665de7cbe` | Same page: `PRIVATE_TREASURY_ACCOUNT_ID`, described as one of the "production constants shared by all solver operators", and the example asset id `imt:51e8f94d...7cbe:nep141:wrap.near` | The account was created on 2026-02-18 (NEAR Blocks, transaction `5BfpVdVufdZD3xim5JYWkBFa1e69DfqLLadk3HGZLdLX`); this project's first non-zero reading is 2026-02-19 |
| What the treasury means | "Each IMT is backed 1:1 by the corresponding tokens locked in the Treasury smart-contract account on the public chain." | Same page, "Asset identifiers" | Quoted, not verified: nothing public proves the private ledger's total equals the treasury. That gap is one of the thesis's risks |
| Private chain | "FAR is a permissioned instance of the NEAR protocol operated by a small validator set with no public networking. Balances and swap details on FAR are not visible to the public" | Same page, "How it works" | Quoted |
| Switch date | 2026-10-27 | NEAR Intents changelog: "From October 27, 2026, 1Click swaps settle confidentially... The swap settles on the NEAR Private Shard, so `nearTxHashes` has no hash for the swap. It has the hashes for the shield and the unshield instead." | Quoted |
| B2B launch | 2026-07-13 | NEAR Intents changelog: "Confidential Intents B2B launch" | Quoted |
| Token prices and decimals | `data/tokens.json` | `https://1click.chaindefuser.com/v0/tokens` (NEAR Intents' own token list), fetched once at the time recorded in the file | Pinned. Used only for dollar figures; every share is computed in token units with no price |
| Reported volume, fees, revenue | `data/context/defillama.json` | DefiLlama API, `summary/dexs/near-intents` and `summary/fees/near-intents` | See "Where the reported numbers come from" below |
| Archival node | `https://archival-rpc.mainnet.fastnear.com` | FastNEAR public archival RPC | One historical read was repeated against `https://archival-rpc.mainnet.near.org` and returned the same bytes; the call and both answers are in `data/context/cross_check.json` |

Docs pages: <https://docs.near-intents.org/integration/market-makers/confidential-intents> and
<https://docs.near-intents.org/changelog/overview>.

## Where the reported numbers come from

DefiLlama's adapters are public code
(<https://github.com/DefiLlama/dimension-adapters>, `dexs/near-intents/index.ts` and `fees/near-intents/index.ts`, read on 2026-11-13):

- **Volume** is `SELECT sum(volume_amount_usd) FROM dune.near.dataset_near_intents_metrics`.
- **Gross fees** come from `dune.near.dataset_near_intents_protocol_fees` and `dune.near.dataset_near_intents_fees`.
- **Revenue** is computed differently: NEAR and wNEAR received by three public wallets
  (`fefundsadmin.sputnik-dao.near`, `1csfundsadmin.sputnik-dao.near`, `buybacks.multisignature.near`), read from Dune's
  decoded chain tables (`near.actions`, `near.ft_transfers`).

On Dune, a table named `dune.<team>.dataset_<name>` is one that the team uploaded
(<https://docs.dune.com/api-reference/tables/endpoint/overview>). So the volume and gross-fee figures are
tables supplied by the `near` team, while the revenue figure is derived from the chain.

## How a reading is taken

For each day, one block stamped in the first 15 seconds after 00:00 UTC (`data/blocks.json`). At that exact height:

1. `intents.near.mt_tokens_for_owner(treasury)` lists the token ids, then `mt_batch_balance_of` returns the balances
   (`data/float/<day>.json`).
2. For each tracked token, the token's own contract is asked how much `intents.near` holds:
   `ft_balance_of(intents.near)` for `nep141:` ids, `mt_balance_of(intents.near, id)` for `nep245:` ids
   (`data/held/<day>.json`). The tracked tokens are the 20 largest by total held on the pinned day
   (`data/tracked.json`). On the pinned day itself the same question is asked for every token in NEAR Intents'
   token list (`python3 -m pipeline.held_all <day>`), and the headline share is computed over all of them, so it
   does not depend on which tokens were picked.

A read that fails is stored as `null` and left out of every sum. It is never treated as zero.
