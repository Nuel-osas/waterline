# Findings: every number this repository computes


As of NEAR mainnet block 224285109 (2026-11-13, 00:00 UTC). This table is written by `pipeline/claims.py` from the
raw readings, and `make check` rebuilds it in memory and fails if it differs. It also fails if a number in the
prose of `README.md`, `THESIS.md`, `PREREG.md`, `PREREG-AUDIT.md`, this file or `docs/ERRATA.md`, or typed by hand
on the dashboard, is neither one of these rows nor a constant declared in `data/constants.json`. The kinds it
checks: dollar amounts, percentages, multiples, NEAR amounts, basis points, correlations and p-values, clock
times, block heights, spans of hours, minutes, days, months or years, and counts of tokens, checks, readings,
paths, transfers, accounts, blocks or steps. It does not check dates, numbers written as words, or counts with
other nouns such as "205 token types", and it cannot tell that a valid number was put in the wrong sentence.

What the letters mean: C, P, S and K rows are measured here from chain state (P: around NEAR's reward programme;
S: shortfalls as first measured, against the private chain's credit only; K: custody). A rows are the audit,
credited against held, and the October hole block by block. U rows are the revenue read from the chain, and RT
the rating the rule gives. W rows are transfers followed from the chain, and 1Click's own records. N rows come from
an indexer's list of transfers and count only days on which that list adds up, to the last unit, to the change in
the balance read from the chain. V and M rows combine a block-header reading with quoted figures; Q rows set the
float and the October hole against the revenue that funds the buyback. X and T rows are quoted from DefiLlama and
labelled with their origin; this project does not vouch for them. Z rows (what revenue growth would cover new
supply), L rows (the lead-lag test) and O rows (`make model`) are models, not measurements, and say so. E, G and Y
rows are results of dated tests on readings taken after the tests were written.

<!-- claims:start -->
| # | Number | What it is |
| --- | --- | --- |
| C1 | **$136.4M** | Value locked behind the private chain on 2026-11-13, at pinned prices |
| C2 | **205 token types** | Different tokens the private chain held on 2026-11-13 (30 of them have no price and are left out of every dollar figure) |
| C3 | **2026-02-19** | First reading (00:00 UTC) on which the treasury held anything; the account was created the day before |
| C4 | **61.0%** | Share of everything intents.near holds that sits behind the private chain on 2026-11-13: every token in NEAR Intents' token list that has a price and a balance inside intents.near (180 tokens, $223.8M in total; 27 listed ids are not balances inside intents.near or could not be read, and are left out) |
| C6-NEAR | **69.9%** | The same share for NEAR alone on 2026-11-13 ($62.3M held in total) |
| C6-Stablecoins | **68.2%** | The same share for stablecoins alone on 2026-11-13 ($72.3M held in total) |
| C6-ZEC | **60.3%** | The same share for ZEC alone on 2026-11-13 ($23.7M held in total) |
| C6-ETH | **57.5%** | The same share for ETH alone on 2026-11-13 ($7.7M held in total) |
| C6-BTC | **28.8%** | The same share for bitcoin alone on 2026-11-13 ($27.5M held in total) |
| C23 | **62.3%** | The same share on 2026-11-13 for the 20 tokens tracked through time (the largest by total held) |
| C18 | **89%** | Part of everything intents.near holds that the tracked tokens cover |
| C19 | **5%** | Tracked-token share on 2026-04-01, the first reading of April |
| C20 | **$86.0M** | Public side of intents.near on 2026-04-01, tracked tokens ($75.0M on 2026-11-13) |
| C24 | **$75.0M** | Public side of intents.near on 2026-11-13, tracked tokens |
| C5 | **36.0%** | Tracked-token share on 2026-07-13, the first reading after the B2B launch of 2026-07-13 |
| C21 | **56.2%** | Tracked-token share on 2026-10-26, the day before the switch |
| C7 | **2.8x** | Growth of the private float since the B2B launch on 2026-07-13 ($49.3M then) |
| C8 | **$75.5M** | Added on the 10 best days out of 268 (the float on 2026-11-13 is $136.4M) |
| C17 | **55%** | The ten best days as a share of the float on 2026-11-13 (the concentration reading) |
| C25 | **$4.7M** | The tenth-largest one-day rise in the float so far (the bar for 'one more lump' in PREREG.md) |
| B1 | **63%** | Days on which the float did not fall, out of 268 (the base rate of test E1) |
| B2 | **58%** | Four-day windows since the B2B launch in which the float did not fall (the base rate of test F1) |
| B3 | **79%** | Four-day windows since the B2B launch with no day above the tenth-largest rise (the base rate of test F2) |
| C9 | **$14.6M** | Largest one-day fall in the float, between the readings of 2026-09-29 and 2026-09-30 |
| C10 | **2.8%** | Change in the float across the day 1Click swaps began to settle on the private chain (2026-10-26 to 2026-10-28) |
| C11 | **$20.7M** | Added to the float between 2026-10-27 and 2026-11-13, 17 days |
| C12 | **Stablecoins: $49.3M** | Largest asset group in the float on 2026-11-13 |
| C13 | **NEAR: $43.5M** | NEAR's own token in the float on 2026-11-13 |
| C22 | **68%** | Part of the float that is not NEAR's own token on 2026-11-13 |
| C14 | **12.6M NEAR** | wNEAR that entered the float between the readings of 2026-09-15 and 2026-09-28 |
| C15 | **3.9M NEAR** | wNEAR that left the float in one day, between the readings of 2026-09-29 and 2026-09-30 |
| C16 | **12.4M NEAR** | wNEAR in the float on 2026-11-13 |
| C27 | **8.5M NEAR** | wNEAR in the float on the 2026-09-17 reading, the day NEAR announced the reward's snapshot had been triggered |
| P1 | **$7.9M per 30 days** | Float growth before the reward programme (2026-02-19 to 2026-06-11) |
| P2 | **$14.3M per 30 days** | Float growth while the first reward was open (2026-06-11 to 2026-09-17) |
| P3 | **$31.8M per 30 days** | Float growth after the first reward's snapshot was triggered (2026-09-17 to 2026-11-13) |
| P9 | **$76.0M** | The float on the 2026-09-17 reading, the day NEAR announced confidential balances had passed $70M (at that day's prices) |
| P10 | **$68.3M** | The float on the 2026-09-17 reading with wNEAR at that day's CoinGecko price and every other token at the pinned price ($74.1M on the next reading): it crosses the $70M of NEAR's announcement between the two |
| P11 | **$1.1M** | The first reward pool at its conversion price: 333,333 locked tokens that convert 1:1 to NEAR at $3.33 (NEAR's blog post, quoted). No wallet receives more than 2% of it: $22,200 |
| P12 | **2.2x** | NEAR's price on CoinGecko over the days of the September inflow: $2.47 on 2026-09-15, $5.39 on 2026-09-28 |
| P4 | **$92.9M** | Float without NEAR's own token on 2026-11-13 ($46.1M on 2026-09-17) |
| P5 | **$46.1M** | Float without NEAR's own token on 2026-09-17 |
| P6 | **$2.7M** | Largest one-day fall in the float without NEAR's own token |
| P7 | **69%** | Part of the wNEAR that arrived between 2026-09-15 and 2026-09-28 that had left again by the pinned day |
| S1 | **2 readings** | Readings where the treasury was credited with more of a token than intents.near held: 2026-10-01, 2026-10-02 |
| S2 | **$3.3M** | Largest such shortfall, on the 2026-10-02 reading: USDT(DEPRECATED) on bsc, 67,669 held against 3,373,849 credited |
| S3 | **98%** | Part of the treasury's credit in that token that had nothing behind it on that reading |
| S5 | **25%** | Part of the treasury's credit in that token with nothing behind it on the earlier reading, 2026-10-01 |
| S4 | **2026-10-03** | First reading on which that token was fully held again |
| X1 | **$3.73B** | Reported swap volume, 30 days to 2026-11-11 (DefiLlama, from a table uploaded to Dune under the near team's name) |
| X2 | **$6.0M** | Reported gross fees, 30 days to 2026-11-11 (same kind of source) |
| X3 | **$1.8M** | Revenue that reached NEAR's public revenue wallets, 30 days to 2026-11-11 (DefiLlama, from chain tables, in dollars at each day's price) |
| T1 | **-22%** | Change in reported volume, 30 days to 2026-11-11 against the 30 days before |
| T2 | **-26%** | Change in reported fees, 30 days to 2026-11-11 against the 30 days before |
| T3 | **-20%** | Change in revenue reaching NEAR's wallets, 30 days to 2026-11-11 against the 30 days before |
| X4 | **0.56x a day** | Reported daily volume divided by everything intents.near holds |
| V1 | **$4.48B** | Value of NEAR's total supply on 2026-11-13: supply in the block header times CoinGecko's price of $3.42 |
| V2 | **88,704 NEAR a day** | Net new NEAR supply, average of the 30 days to the pinned day |
| V3 | **$110.7M a year** | The same, in dollars at that price |
| V4 | **15%** | Revenue reaching NEAR's wallets as a share of net new supply, NEAR against NEAR, 30 days to 2026-11-11 |
| V5 | **265x** | NEAR's total supply divided by that revenue, annualised, NEAR against NEAR |
| V6 | **20%** | V4 with both sides in dollars: revenue as DefiLlama counts it, at each day's price, against net new supply at the price of the pinned block. It is higher than V4 because NEAR averaged $4.42 over those 30 days and was $3.42 on the pinned day |
| V7 | **205x** | V5 on the same dollar basis |
| V8 | **5.1x** | M2 on the same dollar basis |
| M1 | **4.8 basis points** | Revenue reaching NEAR's wallets per dollar of reported volume, 30 days to 2026-11-11 |
| M2 | **6.5x** | How many times revenue would have to grow for buybacks to match net new supply |
| H1 | **4.2x** | How many times revenue would have to grow if net new supply ran at the 1.6% a year that HSP-029 proposes |
| Q1 | **6.2 years** | The float on 2026-11-13 as years of the revenue that reaches NEAR's wallets, at the rate of the 30 days to 2026-11-11 |
| Q2 | **16%** | Part of the float whose loss would equal a full year of that revenue |
| Q3 | **2.1 months** | The October hole at its largest as months of that revenue |
| U1 | **426,685 NEAR** | NEAR and wNEAR received by the three revenue wallets in the 30 days to the reading of 2026-11-13, counted from the chain: transfers listed by a public index, and every wallet's native NEAR in minus out equal, to the last unit, to the change in its balance read at each day's block |
| U2 | **14,223 NEAR a day** | The same, a day |
| U4 | **16%** | Revenue reaching NEAR's wallets as a share of net new supply, both read from the chain, in the 30 days to the reading of 2026-11-13: U1 over the change in total supply between two block headers 30 days apart. The rating in THESIS.md section 5 uses it |
| U5 | **20%** | The same coverage in the 30 days before, to the reading of 2026-10-14 (517,163 NEAR received) |
| U6 | **-17%** | Change in the NEAR reaching the revenue wallets, the latest 30 days against the 30 before, read from the chain |
| U3 | **100.9%** | NEAR the chain shows reaching the wallets over the 30 days of X3, as a share of DefiLlama's revenue for those days turned into NEAR at each day's price (409,897 NEAR against 406,427 NEAR): how far the quoted figure agrees with the chain |
| RT | **Hold** | The rating the rule in THESIS.md section 5 gives on 2026-11-13: the public books are whole on the latest reading; coverage is 16% and 20% in the last two 30-day windows; NEAR has not published the private chain's totals |
| Z1 | **84% a year** | How fast the revenue reaching NEAR's wallets, counted in NEAR, must grow for buybacks to match net new supply by the end of 2029, with issuance as it is (2.47% of supply a year) |
| Z2 | **59% a year** | The same, if net new supply runs at 1.6% of supply by then, as HSP-029 would bring about |
| Z3 | **46% a year** | The same by the end of 2031, issuance as it is |
| Z4 | **33% a year** | The same by the end of 2031, at 1.6% |
| Z5 | **15%** | Coverage at the end of 2029 if revenue in NEAR stays where it is and issuance does too |
| Z6 | **24%** | Coverage at the end of 2029 if revenue in NEAR stays where it is and issuance falls to 1.6% |
| M3 | **$297B a year** | Reported volume that would take at today's rate of revenue per dollar of volume |
| T4 | **$136.4M** | Highest the float has been, on the 2026-11-13 reading |
| P8 | **3.5x** | Growth of the float without NEAR's own token since the B2B launch ($26.8M then) |
| K2 | **1 of 1** | Access keys of the treasury account on NEAR itself that have never signed a transaction (the nonce is still the value set at creation) |
| K1 | **1 key** | Keys registered inside intents.near for the treasury account at the pinned block (the account itself has no contract code) |
| A1 | **214 tokens** | Tokens audited on 2026-11-13: every token with a balance to read that was in NEAR Intents' list when the day's totals were taken, and 27 unlisted ones the treasury holds. For each, the credited total (intents.near.mt_batch_supply) is set against what the token's own contract says intents.near holds. 184 are equal to the last unit, 30 hold more than is credited ($6,321 in all), 0 are short |
| A2 | **$223.8M** | Value of the tokens audited on 2026-11-13, at pinned prices |
| A3 | **4,806 checks** | Token-by-token checks of the 20 tracked tokens on 269 stored readings from 2026-02-18 to 2026-11-13. Every reading covers every tracked token that had a balance that day |
| A4 | **3 of them short** | Checks in which more was credited than held: 2026-09-30 ($30), 2026-10-01 ($1.3M), 2026-10-02 ($3.8M), all one token: USDT(DEPRECATED) on bsc |
| A15 | **3 new lows** | Checks, out of those 4,806, on which a token's held-minus-credited fell below every earlier reading of that token: the same readings as A4 and no others. This test also sees a hole smaller than the surplus a token already carries |
| A5 | **$3.8M** | Largest hole on a daily reading, 2026-10-02: 67,669 held against 3,869,502 credited to everyone |
| A6 | **98%** | Part of everything credited in that token that had nothing behind it on that reading |
| A7 | **87%** | Part of that token's credit that belonged to the private chain's treasury on that reading |
| A8 | **31 hours 40 minutes** | How long before the first payout CertiK reports (2026-09-30 23:54:30 UTC) the hole was already in the public books: it opens at block 217799506, 2026-09-29 16:14:22 UTC, at 10 USDT |
| A9 | **$1.3M** | The hole in the public books at 2026-09-30 23:41:28 UTC, the last change before that first payout |
| A10 | **$3.8M** | The hole at its largest, 2026-10-01 01:29:28 UTC |
| A11 | **76 hours** | How long the books stayed short: whole again at block 218251129, 2026-10-02 20:22:09 UTC, 9 minutes before the contract upgrade CertiK records (2026-10-02 20:31:41 UTC). The credited total did not fall while the hole closed, so the tokens came back |
| A12 | **28 hours** | Of those 31 hours 40 minutes, the time the hole stayed under $3,000 (28 hours 1 minute). How long before the first payout each size was first reached: $100 at 23 hours 43 minutes, $1,000 at 23 hours 21 minutes, $10,000 at 1 hour 9 minutes, $100,000 at 32 minutes, $1.0M at 13 minutes |
| A13 | **13 minutes** | How long before the first payout the hole first passed $1.0M |
| A16 | **1 hour 9 minutes** | How long before the first payout the hole first passed $10,000 |
| A14 | **60.9%** | What C4 would be with the 15 tokens that joined NEAR Intents' list later on the pinned day. They were read once, at the pinned block: $291,069 held, none short, $0 of it in the treasury. They are left out of every pinned figure |
| E1 | **$135.2M** | FAIL. Test E1: the float on the 2026-11-14 reading had to be at least what it was on 2026-11-13 ($136.4M). It fell by $1.2M |
| E2 | **$1.2M** | PASS. Test E2: the largest one-day change between the two readings (a fall). To pass it had to stay under the tenth-largest rise so far, $4.7M |
| E3 | **61.9%** | PASS. Test E3: the private share of the tracked tokens on the 2026-11-14 reading had to be at least 60.0% |
| Y1 | **$91.1M** | The float without NEAR's own token on the 2026-11-14 reading, down $1.8M from the pinned day. 5 of that series' 268 earlier one-day changes were falls at least as large. NEAR's own part of the float rose by $568,746 over the same day |
| Y2 | **37%** | Days up to the pinned one on which the float fell, out of 268: a single fall is ordinary |
| G1 | **none short** | PASS. Test G1 of PREREG-AUDIT.md: no tracked token short on the 2026-11-14 reading |
| W1 | **1.7M NEAR** | The largest single transfer of NEAR into the treasury in September, at 2026-09-24 08:52:40 UTC. The treasury had paid out the same amount, to the last unit, at 2026-09-23 23:35:58 UTC: 9 hours 16 minutes earlier, and 24 minutes before the 2026-09-24 reading. It was back 31 blocks after it was withdrawn from the public ledger |
| W2 | **$6.1M** | That transfer at the pinned price |
| W3 | **$12.0M** | The float's rise on the 2026-09-25 reading, which includes that transfer. It is the largest one-day rise in the series |
| W4 | **51%** | Part of that day's rise that is money the treasury had paid out the evening before |
| N1 | **20 of 20 days** | Days from 2026-09-12 to 2026-10-01 on which the treasury's NEAR transfers listed by FastNEAR's index (78,360 in all) add up, to the last unit, to the change in the balance read from the chain |
| N2 | **33.8M NEAR** | NEAR transferred into the treasury between the readings of 2026-09-15 and 2026-09-28, gross (21.3M NEAR went out over the same days, which leaves the net inflow of C14) |
| N3 | **94%** | Part of that net inflow that came from one account, solver-priv-liq.near: 17.0M NEAR in and 5.2M NEAR out, in 40,748 transfers |
| N4 | **50%** | The same account's part of the gross inflow over those days |
| N5 | **38%** | Part of the NEAR that left the treasury before the 2026-09-30 reading (5.6M NEAR gross, to 1,083 accounts) that went to the three largest receivers, each in a single transfer |
| L1 | **r = -0.11, p = 0.96** | Weekly change in NEAR Intents' reported volume against the change in NEAR's transactions 2 weeks later, the strongest of leads of 1 to 8 weeks. p is the share of 10,000 circularly shifted series that do as well at their best lead (seed 20261114) |
| L2 | **r = +0.09, p = 0.88** | Weekly change in NEAR Intents' reported volume against the change in NEAR's active accounts 1 week later, the strongest of leads of 1 to 8 weeks. p is the share of 10,000 circularly shifted series that do as well at their best lead (seed 20261114) |
| L3 | **r = -0.12, p = 0.74** | Weekly change in NEAR Intents' reported volume against the change in NEAR's price 2 weeks later, the strongest of leads of 1 to 8 weeks. p is the share of 10,000 circularly shifted series that do as well at their best lead (seed 20261114) |
| L4 | **98 weekly changes** | Weeks in the lead-lag test, from the week of 2024-12-16 to the week of 2026-11-02 |
| W5 | **9 of 9** | Completed or refunded 1Click swaps, found among 188 accounts that paid into the treasury on six days after 2026-10-27, whose own status record lists the NEAR transaction that moved their tokens into the treasury (swaps dated 2026-11-02 to 2026-11-11; 9 of those transfers read back from the chain as stated) |
| N6 | **4.1M NEAR** | Net NEAR that left the treasury between the reading of 2026-09-29 and block 217799506, where the hole in the public books opened. From that block to the next reading the treasury gained 0.2M NEAR |
| N7 | **2.1M NEAR** | The three largest transfers out of the treasury that day, all between 06:06 and 06:09 UTC on 29 September |
| N8 | **10 hours** | How long before the hole opened the last of those three transfers left |
| O1 | **53%** | Replayed paths on which R1 holds (the float is at least $200M on 2027-03-31), drawing from every day since the first deposit (267 daily changes): 138 days to 2027-03-31 built from runs of 7 consecutive past days, 10,000 paths, seed 20261113. A base rate, not a forecast |
| O2 | **under 1%** | The same, drawing only from days before the reward programme was announced (2026-02-19 to 2026-06-11, 112 daily changes) |
| O3 | **82%** | The same, drawing only from days since the first reward's snapshot was triggered (2026-09-17 to 2026-11-13, 57 daily changes) |
| O4 | **72%** | Replayed paths on which R5 holds (the float without NEAR's own token is at least $130M), drawing from every day since the first deposit (267 daily changes) |
| O5 | **under 1%** | The same, drawing only from days before the reward programme was announced |
| O6 | **over 99%** | The same, drawing only from days since the first reward's snapshot was triggered |
| O7 | **67%** | Replayed paths on which R2 holds (the ten best days are under 45% of the float), drawing from every day since the first deposit |
| O8 | **$202.6M** | Median float on 2027-03-31 across the replayed paths, drawing from every day since the first deposit (one path in ten ends below $164.8M, one in ten above $252.7M) |
| O9 | **$170.0M** | Median float on 2027-03-31 across the replayed paths, drawing only from days before the reward programme was announced (one path in ten ends below $159.5M, one in ten above $181.5M) |
| O10 | **$258.7M** | Median float on 2027-03-31 across the replayed paths, drawing only from days since the first reward's snapshot was triggered (one path in ten ends below $176.1M, one in ten above $353.0M) |
| O13 | **89%** | O3 when a run may wrap from the end of the window to its start. Without wrapping, a run of 7 days cannot start in the last 6 days of a window, so its first and last days are drawn less often |
| O11 | **51% to 60%** | How far O1 moves when the runs are 1, 3, 7, 14 or 30 days long |
| O12 | **38% to 96%** | How far O3 moves when the runs are 1, 3, 7, 14 or 30 days long |
<!-- claims:end -->
