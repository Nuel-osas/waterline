"""Run with: python3 -m unittest discover -s tests -v   (no network)"""
import os
import sys
import unittest
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import build, pull, rpc  # noqa: E402

META = {
    "nep141:wrap.near": {"symbol": "wNEAR", "chain": "near", "decimals": 24, "price": Fraction("3.5")},
    "nep141:usdc": {"symbol": "USDC", "chain": "eth", "decimals": 6, "price": Fraction("1")},
    "nep141:mystery": {"symbol": "???", "chain": "?", "decimals": 18, "price": None},
}


def day(bal, held, name="2026-10-27"):
    return {"day": name, "height": 1, "timestamp": 0, "balances": bal, "held": held}


class Shares(unittest.TestCase):
    def test_share_is_units_over_units(self):
        r = build.day_row(day({"nep141:usdc": 600_000_000}, {"nep141:usdc": 1_000_000_000}), META, ["nep141:usdc"])
        self.assertEqual(r["shares"]["nep141:usdc"], Fraction(3, 5))
        self.assertEqual(r["share_usd"], Fraction(3, 5))

    def test_combined_share_weights_by_value_not_by_token_count(self):
        # 10% of $1,000 of USDC is private, 90% of $35 of wNEAR is private: by value that is 12.7%, not 50%
        bal = {"nep141:usdc": 100_000_000, "nep141:wrap.near": 9 * 10**24}
        held = {"nep141:usdc": 1_000_000_000, "nep141:wrap.near": 10 * 10**24}
        r = build.day_row(day(bal, held), META, sorted(bal))
        self.assertEqual(r["share_usd"], Fraction("131.5") / Fraction(1035))
        self.assertNotEqual(r["share_usd"], Fraction(1, 2))

    def test_an_unread_total_is_unknown_and_left_out_never_zero(self):
        bal = {"nep141:usdc": 500_000_000, "nep141:wrap.near": 10**24}
        held = {"nep141:usdc": 1_000_000_000, "nep141:wrap.near": None}
        r = build.day_row(day(bal, held), META, sorted(bal))
        self.assertNotIn("nep141:wrap.near", r["shares"])
        self.assertEqual(r["share_cover"]["tokens"], 1)
        self.assertEqual(r["share_usd"], Fraction(1, 2))

    def test_no_totals_at_all_gives_no_share(self):
        r = build.day_row(day({"nep141:usdc": 5}, {}), META, ["nep141:usdc"])
        self.assertIsNone(r["share_usd"])

    def test_treasury_above_the_contract_total_is_listed_and_left_out_never_a_share(self):
        bal = {"nep141:usdc": 11, "nep141:wrap.near": 10**24}
        held = {"nep141:usdc": 10, "nep141:wrap.near": 4 * 10**24}
        r = build.day_row(day(bal, held), META, sorted(bal))
        self.assertNotIn("nep141:usdc", r["shares"])
        self.assertEqual(r["share_usd"], Fraction(1, 4))
        self.assertEqual(r["anomalies"], [{"day": "2026-10-27", "height": 1, "token": "nep141:usdc", "treasury": "11", "held": "10"}])

    def test_unpriced_tokens_are_counted_not_valued_at_zero(self):
        r = build.day_row(day({"nep141:mystery": 10**18, "nep141:usdc": 2_000_000}, {}), META, [])
        self.assertEqual(r["unpriced_types"], 1)
        self.assertEqual(r["float_usd"], Fraction(2))
        self.assertEqual(r["types"], 2)

    def test_money_is_exact(self):
        self.assertEqual(build.usd(1, META["nep141:wrap.near"]), Fraction(35, 10**25))
        self.assertIsNone(build.usd(None, META["nep141:usdc"]))
        self.assertIsNone(build.usd(5, META["nep141:mystery"]))


class Scope(unittest.TestCase):
    """The headline is over every token with a total; the history is over the tracked ones only."""

    def setUp(self):
        # usdc is tracked and 90% private; wnear is not tracked and only 10% private, with far more value
        self.bal = {"nep141:usdc": 90_000_000, "nep141:wrap.near": 100 * 10**24}
        self.held = {"nep141:usdc": 100_000_000, "nep141:wrap.near": 1000 * 10**24}
        self.row = build.day_row(day(self.bal, self.held), META, ["nep141:usdc"])

    def test_tracked_share_ignores_untracked_tokens(self):
        self.assertEqual(self.row["share_usd"], Fraction(9, 10))
        self.assertEqual(list(self.row["shares"]), ["nep141:usdc"])

    def test_headline_counts_every_token_so_a_selection_cannot_flatter_it(self):
        want = (Fraction(90) + Fraction(350)) / (Fraction(100) + Fraction(3500))
        self.assertEqual(self.row["all"]["share"], want)
        self.assertLess(self.row["all"]["share"], self.row["share_usd"])
        self.assertEqual(self.row["all"]["tokens"], 2)

    def test_group_shares(self):
        g = self.row["all"]["group_share"]
        self.assertEqual(g["Stablecoins"], Fraction(9, 10))
        self.assertEqual(g["NEAR"], Fraction(1, 10))
        self.assertIsNone(g["BTC"])

    def test_unknown_totals_are_counted(self):
        r = build.day_row(day({"nep141:usdc": 1}, {"nep141:usdc": None, "nep141:wrap.near": 10**24}), META, [])
        self.assertEqual(r["all"]["unknown"], 1)
        self.assertEqual(r["all"]["share"], Fraction(0))


class Forward(unittest.TestCase):
    """The forward tests: pending until the reading exists, then pass or fail on the written thresholds."""

    def rows(self, extra):
        from pipeline import score
        days = ["2026-11-%02d" % d for d in range(1, 14)]
        rows = [{"day": d, "float_usd": Fraction(100_000_000 + 1_000_000 * i), "share_usd": Fraction(62, 100)} for i, d in enumerate(days)]
        rows[5]["float_usd"] += 0  # ten rises of exactly $1M each among the first twelve steps
        return score, rows + extra

    def test_pending_until_the_reading_exists(self):
        score, rows = self.rows([])
        self.assertEqual({t["status"] for t in score.tests(rows)}, {"PENDING"})

    def test_pass_and_fail(self):
        score, rows = self.rows([
            {"day": "2026-11-14", "float_usd": Fraction(112_500_000), "share_usd": Fraction(62, 100)},
            {"day": "2026-11-15", "float_usd": Fraction(113_000_000), "share_usd": Fraction(62, 100)},
            {"day": "2026-11-16", "float_usd": Fraction(113_500_000), "share_usd": Fraction(61, 100)},
            {"day": "2026-11-17", "float_usd": Fraction(114_000_000), "share_usd": Fraction(59, 100)},
        ])
        got = {t["id"]: t["status"] for t in score.tests(rows)}
        self.assertEqual(got["F1"], "PASS")   # 114.0M >= 112.0M on the 13th
        self.assertEqual(got["F2"], "PASS")   # largest later rise 0.5M < tenth-largest so far 1.0M
        self.assertEqual(got["F3"], "FAIL")   # 59% is below the 60% floor
        self.assertEqual(got["R1"], "PENDING")

    def test_a_lump_fails_the_breadth_test_and_a_fall_fails_growth(self):
        score, rows = self.rows([
            {"day": "2026-11-14", "float_usd": Fraction(120_000_000), "share_usd": Fraction(62, 100)},
            {"day": "2026-11-17", "float_usd": Fraction(111_000_000), "share_usd": None},
        ])
        got = {t["id"]: t["status"] for t in score.tests(rows)}
        self.assertEqual(got["F2"], "FAIL")
        self.assertEqual(got["F1"], "FAIL")
        self.assertEqual(got["F3"], "FAIL")   # an unknown share is not a pass


class Sample(unittest.TestCase):
    def test_the_verify_sample_is_fixed_by_the_data_and_always_has_the_key_days(self):
        from pipeline import verify
        blocks = pull.load(os.path.join(pull.DATA, "blocks.json"), {})
        if not blocks:
            self.skipTest("no data")
        a, b = verify.sample_days(blocks, 8), verify.sample_days(blocks, 8)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 8)
        for d in (min(blocks), max(blocks), "2026-07-13", "2026-10-27"):
            self.assertIn(d, a)


class Claims(unittest.TestCase):
    def test_formats(self):
        from pipeline import claims
        self.assertEqual(claims.money(Fraction(132_280_481)), "$132.3M")
        self.assertEqual(claims.money(3_774_153_452), "$3.77B")
        self.assertEqual(claims.money(807), "$807")
        self.assertEqual(claims.pct(Fraction(705, 1000)), "70.5%")
        self.assertEqual(claims.pct(Fraction(2, 3), 0), "67%")

    def test_every_claim_in_the_repository_is_quoted_in_the_text(self):
        import json
        path = os.path.join(pull.DATA, "derived", "claims.json")
        if not os.path.exists(path):
            self.skipTest("no claims built yet")
        text = ""
        for name in ("README.md", "THESIS.md"):
            with open(os.path.join(pull.ROOT, name)) as f:
                text += f.read()
        with open(path) as f:
            claims = json.load(f)["claims"]
        for c in claims:
            self.assertIn(c["shown"], text, c["id"])


class Groups(unittest.TestCase):
    def test_groups(self):
        for sym, g in (("wNEAR", "NEAR"), ("USDT(DEPRECATED)", "Stablecoins"), ("nBTC", "BTC"), ("ZEC", "ZEC"),
                       ("ETH", "ETH"), ("TLO", "Other"), ("cNEAR", "Other")):
            self.assertEqual(build.group_of(sym), g, sym)


class BlockSearch(unittest.TestCase):
    """block_at against a fake chain: heights 0..N, uneven block times, some heights skipped."""

    def setUp(self):
        self.times = {}
        t = 1_000_000_000_000
        for h in range(0, 400_000):
            t += 550_000_000 + (h * 7919 % 13) * 10_000_000
            if h % 97 != 5:
                self.times[h] = t
        self.calls = 0
        self._orig = rpc.header

        def fake(height):
            self.calls += 1
            if height not in self.times:
                raise rpc.UnknownBlock(str(height))
            return {"height": height, "timestamp": self.times[height]}
        rpc.header = fake

    def tearDown(self):
        rpc.header = self._orig

    def test_finds_a_block_inside_the_window_in_few_calls(self):
        anchors = [(0, self.times[0]), (399_999, self.times[399_999])]
        for target_h in (1_234, 200_000, 398_000):
            target = self.times[target_h] - 100
            h, ns = pull.block_at(target, anchors)
            self.assertGreaterEqual(ns, target)
            self.assertLess(ns, target + pull.WINDOW_NS)
        self.assertLess(self.calls, 60)

    def test_target_outside_known_range_is_refused(self):
        with self.assertRaises(rpc.RpcError):
            pull.block_at(5, [(10, self.times[10]), (20, self.times[20])])


class CommittedData(unittest.TestCase):
    """Sanity checks on whatever raw data is in the repository."""

    def setUp(self):
        self.blocks = pull.load(os.path.join(pull.DATA, "blocks.json"), {})

    def test_each_day_block_is_stamped_just_after_midnight_utc(self):
        import datetime as dt
        for d, b in self.blocks.items():
            y, m, dd = map(int, d.split("-"))
            midnight = int(dt.datetime(y, m, dd, tzinfo=dt.timezone.utc).timestamp()) * 10**9
            self.assertGreaterEqual(b["timestamp"], midnight, d)
            self.assertLess(b["timestamp"], midnight + pull.WINDOW_NS, d)

    def test_heights_rise_with_the_days(self):
        hs = [self.blocks[d]["height"] for d in sorted(self.blocks)]
        self.assertEqual(hs, sorted(hs))
        self.assertEqual(len(hs), len(set(hs)))

    def test_every_float_file_matches_its_block(self):
        for d, b in self.blocks.items():
            f = pull.load(os.path.join(pull.DATA, "float", d + ".json"), None)
            if f is None:
                continue
            self.assertEqual(f["height"], b["height"], d)
            for k, v in f["balances"].items():
                self.assertTrue(v.isdigit(), (d, k, v))


if __name__ == "__main__":
    unittest.main()
