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

    def test_treasury_above_the_contract_total_is_listed_with_its_size_and_left_out_never_a_share(self):
        bal = {"nep141:usdc": 11_000_000, "nep141:wrap.near": 10**24}
        held = {"nep141:usdc": 10_000_000, "nep141:wrap.near": 4 * 10**24}
        r = build.day_row(day(bal, held), META, sorted(bal))
        self.assertNotIn("nep141:usdc", r["shares"])
        self.assertEqual(r["share_usd"], Fraction(1, 4))
        self.assertEqual(r["anomalies"], [{"day": "2026-10-27", "height": 1, "token": "nep141:usdc",
                                           "treasury": "11000000", "held": "10000000", "short_usd": 1.0, "short_share": 9.1}])

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

    def test_a_day_with_only_some_tracked_tokens_read_makes_no_point_in_the_history(self):
        # usdc was read that day, wnear was never asked: the day has no tracked share, though usdc's own share stands
        r = build.day_row(day(self.bal, {"nep141:usdc": 100_000_000}), META, ["nep141:usdc", "nep141:wrap.near"])
        self.assertIsNone(r["share_usd"])
        self.assertEqual(r["shares"]["nep141:usdc"], Fraction(9, 10))

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
        rows = [{"day": d, "float_usd": Fraction(100_000_000 + 1_000_000 * i), "share_usd": Fraction(62, 100), "tracked_complete": True}
                for i, d in enumerate(days)]
        rows[5]["float_usd"] += 0  # ten rises of exactly $1M each among the first twelve steps
        return score, rows + extra

    def test_pending_until_the_reading_exists(self):
        score, rows = self.rows([])
        self.assertEqual({t["status"] for t in score.tests(rows)}, {"PENDING"})

    def test_pass_and_fail(self):
        score, rows = self.rows([
            {"day": "2026-11-14", "float_usd": Fraction(112_500_000), "share_usd": Fraction(62, 100), "tracked_complete": True},
            {"day": "2026-11-15", "float_usd": Fraction(113_000_000), "share_usd": Fraction(62, 100), "tracked_complete": True},
            {"day": "2026-11-16", "float_usd": Fraction(113_500_000), "share_usd": Fraction(61, 100), "tracked_complete": True},
            {"day": "2026-11-17", "float_usd": Fraction(114_000_000), "share_usd": Fraction(59, 100), "tracked_complete": True},
        ])
        got = {t["id"]: t["status"] for t in score.tests(rows)}
        self.assertEqual(got["F1"], "PASS")   # 114.0M >= 112.0M on the 13th
        self.assertEqual(got["F2"], "PASS")   # largest later rise 0.5M < tenth-largest so far 1.0M
        self.assertEqual(got["F3"], "FAIL")   # 59% is below the 60% floor
        self.assertEqual(got["E1"], "PASS")   # the 14 November checkpoint is scored on its own reading
        self.assertEqual(got["E3"], "PASS")   # 62% on the 14th
        self.assertEqual(got["R1"], "PENDING")

    def test_a_lump_fails_the_breadth_test_and_a_fall_fails_growth(self):
        score, rows = self.rows([
            {"day": "2026-11-14", "float_usd": Fraction(120_000_000), "share_usd": Fraction(62, 100), "tracked_complete": True},
            {"day": "2026-11-17", "float_usd": Fraction(111_000_000), "share_usd": Fraction(70, 100), "tracked_complete": False},
        ])
        got = {t["id"]: t["status"] for t in score.tests(rows)}
        self.assertEqual(got["F2"], "FAIL")
        self.assertEqual(got["F1"], "FAIL")
        # a share over only some of the tracked tokens is neither a pass nor a fail, even when it looks like a pass
        self.assertEqual(got["F3"], "UNKNOWN")
        self.assertEqual(got["E2"], "FAIL")   # the lump on the 14th is above the tenth-largest rise


class Prose(unittest.TestCase):
    """The check that the prose cannot carry a number the data does not produce."""

    def test_numbers_are_found_and_code_and_tables_are_not_prose(self):
        from pipeline import verify
        text = "It is $136.4M, 61.0% and 2.8x; 12.6M NEAR came in, 88,704 NEAR a day. In 2026 NEAR said so.\n`$9.9M`\n```\n$1.0M\n```\n<!-- claims:start -->\n| C1 | **$5.0M** |\n<!-- claims:end -->"
        found = verify.NUMBER.findall(verify.prose_only(text))
        self.assertEqual(found, ["$136.4M", "61.0%", "2.8x", "12.6M NEAR", "88,704 NEAR"])

    def test_a_typed_in_number_is_refused(self):
        from pipeline import verify
        claims = {"claims": [{"id": "C1", "shown": "$136.4M", "what": "the float ($49.3M then)"}]}
        ok = verify.allowed_numbers(claims)
        self.assertIn("$136.4M", ok)
        self.assertIn("$49.3M", ok)       # a number inside a claim's description is computed too
        self.assertIn("$200M", ok)        # a declared threshold
        self.assertNotIn("$200.0M", ok)
        self.assertNotIn("999x", ok)


    def test_the_kinds_of_number_the_check_sees_and_the_ones_it_leaves_alone(self):
        from pipeline.verify import NUMBER
        seen = NUMBER.findall("at 16:14:22 UTC, block 217799506, 24 minutes before, 4.8 basis points, 10,000 paths, "
                              "17 days, 3 of them short, 20 of 20 days, 31 hours 40 minutes, 214 tokens, $3.8M, 61.0%, 2.8x")
        self.assertEqual(seen, ["16:14:22", "217799506", "24 minutes", "4.8 basis points", "10,000 paths", "17 days",
                                "3 of them short", "20 of 20 days", "31 hours 40 minutes", "214 tokens", "$3.8M", "61.0%", "2.8x"])
        self.assertEqual(NUMBER.findall("a hole of $30, and then $1,299,979, and 98%, too"), ["$30", "$1,299,979", "98%"])
        # a date is not a count, and words are not numbers: both are stated limits of the check
        self.assertEqual(NUMBER.findall("the 2026-11-17 readings, on 29 September, ten dollars, four months"), [])

    def test_text_typed_on_the_page_is_checked_and_text_filled_from_the_data_is_not_checked_twice(self):
        from pipeline.verify import NUMBER, page_text
        html = '<p>It passes $9M <span data-claim="A13">13 minutes</span> before.</p><pre>$5</pre><script>var x = "$7M";</script>'
        self.assertEqual(NUMBER.findall(page_text(html)), ["$9M"])

class Sample(unittest.TestCase):
    def test_the_verify_sample_is_fixed_by_the_data_and_always_has_the_key_days(self):
        from pipeline import verify
        blocks = pull.load(os.path.join(pull.DATA, "blocks.json"), {})
        if not blocks:
            self.skipTest("no data")
        a, b = verify.sample_days(blocks, 8), verify.sample_days(blocks, 8)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 8)
        for d in (min(blocks), max(blocks), "2026-07-13", "2026-10-02", "2026-10-27"):
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
        for name in ("README.md", "THESIS.md", os.path.join("docs", "FINDINGS.md")):
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
        pull.rpc.header = fake

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

    def test_first_mode_returns_the_first_block_at_or_after_the_target_whatever_the_search_did(self):
        anchors = [(0, self.times[0]), (399_999, self.times[399_999])]
        for target_h in (1_234, 200_000, 398_000, 101, 103):   # 101 and 103 sit either side of a skipped height
            for back in (0, 1, 250_000_000, 9_000_000_000):     # target on the block, just before it, up to 9 s before
                target = self.times[target_h] - back
                h, ns = pull.block_at(target, anchors, first=True)
                want = min(x for x, t in self.times.items() if t >= target)
                self.assertEqual(h, want, (target_h, back))
                self.assertEqual(ns, self.times[want])

    def test_target_outside_known_range_is_refused(self):
        with self.assertRaises(rpc.RpcError):
            pull.block_at(5, [(10, self.times[10]), (20, self.times[20])])


class Model(unittest.TestCase):
    """The base-rate model: seeded, exact on series whose answer is known, and honest at the edges."""

    def rows(self, floats, near=10_000_000):
        import datetime as dt
        first = dt.date(2026, 10, 1)
        return [{"day": (first + dt.timedelta(days=i)).isoformat(), "float_usd": Fraction(f), "groups": {"NEAR": Fraction(near)}, "types": 1}
                for i, f in enumerate(floats)]

    def run_model(self, floats, **kw):
        import datetime as dt
        from pipeline import model
        rows = self.rows(floats)
        pin = rows[-1]["day"]
        target = (dt.date.fromisoformat(pin) + dt.timedelta(days=kw.pop("days", 100))).isoformat()
        return model.simulate(rows, pin, target=target, paths=kw.pop("paths", 200), **kw)

    def test_a_steady_rise_reaches_the_reading_on_every_path(self):
        m = self.run_model([100_000_000 + 1_000_000 * i for i in range(30)])
        self.assertEqual(m["median_usd"], 229_000_000)   # 129M on the pinned day plus 100 days of 1M
        self.assertEqual((m["r1_holds"], m["r1_breaks"]), (1, 0))
        self.assertEqual((m["r5_holds"], m["r5_breaks"]), (1, 0))   # 219M without the 10M of NEAR

    def test_a_steady_fall_breaks_it_and_a_balance_stops_at_nothing(self):
        m = self.run_model([100_000_000 - 2_000_000 * i for i in range(30)])
        self.assertEqual(m["median_usd"], 0)
        self.assertEqual((m["r1_holds"], m["r1_breaks"]), (0, 1))
        self.assertEqual((m["r5_holds"], m["r5_breaks"]), (0, 1))

    def test_the_same_seed_gives_the_same_paths_and_another_seed_does_not(self):
        steps = [5, -3, 1, -4, 8, 2, -6, 7, 0, -1] * 4
        floats = [100_000_000]
        for s in steps:
            floats.append(floats[-1] + s * 1_000_000)
        a, b, c = self.run_model(floats, seed=1), self.run_model(floats, seed=1), self.run_model(floats, seed=2)
        self.assertEqual(a, b)
        self.assertNotEqual((a["p10_usd"], a["median_usd"], a["p90_usd"]), (c["p10_usd"], c["median_usd"], c["p90_usd"]))

    def test_the_ten_best_days_count_the_past_as_well_as_the_days_drawn(self):
        # one lump of 100M and then nothing: drawing only from the quiet days cannot dilute the lump
        rows_floats = [0, 100_000_000] + [100_000_000] * 20
        from pipeline import model
        rows = self.rows(rows_floats, near=0)
        m = model.simulate(rows, rows[-1]["day"], since=rows[1]["day"], target="2027-03-31", paths=50)
        self.assertEqual((m["r2_holds"], m["r2_breaks"]), (0, 1))

    def test_a_window_too_short_for_one_run_is_refused(self):
        with self.assertRaises(SystemExit):
            self.run_model([100_000_000 + i for i in range(5)], block=7)

    def test_a_share_is_never_rounded_to_never_or_always(self):
        from pipeline.model import share
        self.assertEqual(share(Fraction(0)), "none")
        self.assertEqual(share(Fraction(1)), "all")
        self.assertEqual(share(Fraction(3, 10000)), "under 1%")
        self.assertEqual(share(Fraction(9998, 10000)), "over 99%")
        self.assertEqual(share(Fraction(53, 100)), "53%")


class Trace(unittest.TestCase):
    """Finding the block where a balance moved, and reading who moved it out of the receipt."""

    def steps(self, jumps, start=1000):
        def read(height):
            return start + sum(size for at, size in jumps.items() if at <= height)
        return read

    def receipt(self, method, args, sender="intents.near"):
        import base64
        import json
        packed = base64.b64encode(json.dumps(args).encode()).decode()
        return {"receipt_id": "R1", "predecessor_id": sender, "receiver_id": "intents.near",
                "receipt": {"Action": {"actions": [{"FunctionCall": {"method_name": method, "args": packed, "deposit": "0", "gas": 1}}]}}}

    def signed(self, signer, intents, standard="nep413"):
        import json
        message = json.dumps({"signer_id": signer, "intents": intents})
        return {"standard": standard, "payload": {"message": message, "nonce": "n", "recipient": "intents.near"} if standard == "nep413" else message}

    def test_halving_finds_each_block_where_the_balance_moved_largest_first(self):
        from pipeline import trace
        read = self.steps({150: 1000, 420: 300, 777: -500})
        self.assertEqual(trace.largest_moves(read, 100, 1000, 3), [(150, 1000), (777, -500), (420, 300)])
        self.assertEqual(trace.largest_moves(read, 100, 1000, 1), [(150, 1000)])

    def test_it_stops_once_enough_of_the_change_is_explained(self):
        from pipeline import trace
        read = self.steps({150: 1000, 420: 300, 777: 50})
        self.assertEqual(trace.largest_moves(read, 100, 1000, 3, enough=Fraction(7, 10)), [(150, 1000)])

    def test_moves_that_cancel_inside_the_window_are_not_seen(self):
        from pipeline import trace
        # in at 500, out again at 501: no net change over the window, so there is nothing to follow. A stated limit.
        self.assertEqual(trace.largest_moves(self.steps({500: 100, 501: -100}), 100, 1000, 3), [])

    def test_a_transfer_intent_names_the_signer_and_the_receiver(self):
        from pipeline import trace
        r = self.receipt("execute_intents", {"signed": [self.signed("alice", [{"intent": "transfer", "receiver_id": "treasury", "tokens": {"nep141:wrap.near": "1730", "nep141:usdc": "5"}}])]})
        self.assertEqual(trace.legs(r, "nep141:wrap.near"), [{"from": "alice", "to": "treasury", "amount": 1730, "how": "transfer intent"}])
        self.assertEqual(trace.legs(r, "nep141:other"), [])

    def test_a_message_signed_under_another_standard_is_read_the_same_way(self):
        from pipeline import trace
        r = self.receipt("execute_intents", {"signed": [self.signed("0xabc", [{"intent": "ft_withdraw", "token": "wrap.near", "receiver_id": "bob.near", "amount": "7"}], standard="erc191")]})
        self.assertEqual(trace.legs(r, "nep141:wrap.near"),
                         [{"from": "0xabc", "to": "bob.near (outside intents.near)", "amount": 7, "how": "withdrawal intent"}])

    def test_a_deposit_names_the_outside_sender_and_the_account_credited(self):
        from pipeline import trace
        named = self.receipt("ft_on_transfer", {"sender_id": "alice.near", "amount": "9", "msg": '{"receiver_id":"treasury"}'}, sender="wrap.near")
        plain = self.receipt("ft_on_transfer", {"sender_id": "alice.near", "amount": "9", "msg": ""}, sender="wrap.near")
        other = self.receipt("ft_on_transfer", {"sender_id": "alice.near", "amount": "9", "msg": ""}, sender="usdc.near")
        self.assertEqual(trace.legs(named, "nep141:wrap.near"), [{"from": "alice.near (outside intents.near)", "to": "treasury", "amount": 9, "how": "deposit"}])
        self.assertEqual(trace.legs(plain, "nep141:wrap.near")[0]["to"], "alice.near")
        self.assertEqual(trace.legs(other, "nep141:wrap.near"), [])   # a deposit of another token

    def test_the_key_that_signed_for_an_account_is_read_from_the_receipt(self):
        from pipeline import trace
        one = self.signed("treasury", [{"intent": "transfer", "receiver_id": "x", "tokens": {"nep141:wrap.near": "1"}}])
        one["public_key"] = "ed25519:KEY"
        self.assertEqual(trace.signers(self.receipt("execute_intents", {"signed": [one, {"standard": "weird"}]})), {"treasury": "ed25519:KEY"})
        self.assertEqual(trace.signers(self.receipt("ft_on_transfer", {"sender_id": "a", "amount": "1", "msg": ""})), {})

    def test_a_swap_leg_is_a_change_for_its_signer_and_an_unreadable_payload_is_skipped(self):
        from pipeline import trace
        r = self.receipt("execute_intents", {"signed": [
            {"standard": "nep413", "payload": {"message": "not json"}},
            {"standard": "weird"},
            self.signed("maker", [{"intent": "token_diff", "diff": {"nep141:wrap.near": "-40", "nep141:usdc": "120"}}]),
        ]})
        self.assertEqual(trace.legs(r, "nep141:wrap.near"), [{"from": "maker", "to": None, "amount": 40, "how": "swap leg"}])


class Audit(unittest.TestCase):
    """Credited against held: the books are whole, in surplus or short, and unknown is never whole."""

    def test_one_token_is_whole_in_surplus_short_or_unknown(self):
        from pipeline import audit
        self.assertEqual(audit.compare("100", "100"), ("equal", 0))
        self.assertEqual(audit.compare("100", "130"), ("surplus", -30))
        self.assertEqual(audit.compare("100", "70"), ("short", 30))
        self.assertEqual(audit.compare("100", None), ("unknown", None))   # a failed read is not a pass
        self.assertEqual(audit.compare(None, "100"), ("unknown", None))

    def test_a_day_counts_each_kind_and_values_the_hole_at_the_pinned_price(self):
        from pipeline import audit
        meta = {"a": {"decimals": 6, "price": Fraction(1)}, "b": {"decimals": 6, "price": Fraction(2)},
                "c": {"decimals": 0, "price": None}, "d": {"decimals": 6, "price": Fraction(1)}}
        held = {"a": "5000000", "b": "1000000", "c": "7", "d": "9000000"}
        credited = {"a": "5000000", "b": "4000000", "c": "9", "d": None}
        got = audit.audit_day(held, credited, meta)
        self.assertEqual(got["counts"], {"equal": 1, "surplus": 0, "short": 2, "unknown": 1})
        self.assertEqual(got["checked"], 3)
        self.assertEqual(got["short_usd"], 6)           # 3 units of b at 2 dollars; c is short too but has no price
        self.assertEqual(got["held_usd"], 7)            # a and b; d could not be compared and is left out
        self.assertEqual([(r["token"], r["status"], r["hole"]) for r in got["not_equal"]], [("b", "short", "3000000"), ("c", "short", "2")])

    def test_halving_finds_every_block_where_the_hole_changed(self):
        from pipeline import audit
        credit = {150: 10, 400: 20, 401: -20, 777: 40}     # a hole opens, a move in and straight out again, then it grows

        def read(height):
            return 1000 + sum(v for at, v in credit.items() if at <= height), 1000
        self.assertEqual(audit.steps(read, 100, 1000, grid=1), [150, 777])   # 400 and 401 cancel between two reads
        self.assertEqual(audit.steps(read, 399, 402, grid=3), [400, 401])    # read block by block, they show

    def test_the_blocks_the_exploit_claims_rest_on_are_where_it_opens_peaks_and_closes(self):
        from pipeline import verify

        def step(height, credited, held):
            return {"height": height, "credited": str(credited), "held": str(held)}
        ex = {"steps": [step(5, 100, 130), step(10, 100, 90), step(20, 100, 40), step(21, 100, 100), step(30, 100, 60), step(40, 100, 100)]}
        self.assertEqual([st["height"] for st in verify.exploit_marks(ex)], [10, 20, 21])   # a surplus at 5 is not a hole

    def test_a_new_low_of_the_surplus_is_seen_even_while_the_token_is_still_whole(self):
        from pipeline import audit
        # token a carries a surplus of 50; an attacker takes 10 while credit stays: still "whole", but a new low
        days = [("d1", {"a": "1050", "b": "500"}, {"a": "1000", "b": "500"}),
                ("d2", {"a": "1090", "b": "500"}, {"a": "1000", "b": "500"}),   # a deposit in flight: surplus up, no alarm
                ("d3", {"a": "1050", "b": "500"}, {"a": "1000", "b": "500"}),   # back to where it was: not a new low
                ("d4", {"a": "1040", "b": "500"}, {"a": "1000", "b": "500"}),   # 10 gone
                ("d5", {"a": "1040", "b": None}, {"a": "1000", "b": "500"})]    # an unread total is skipped, not a low
        lows, floor = audit.new_lows(days, ["a", "b"])
        self.assertEqual(lows, [("d4", "a", 10)])
        self.assertEqual(floor, {"a": 40, "b": 0})
        self.assertEqual(audit.compare("1000", "1040")[0], "surplus")   # the sign test alone would have passed it
        # the level a live reading is compared with looks only at recent readings, so an old hole does not become the floor
        old_hole = [("d0", {"a": "900"}, {"a": "1000"})] + [(d, {"a": h["a"]}, {"a": c["a"]}) for d, h, c in days]
        self.assertEqual(audit.recent_floor(old_hole, ["a"], n=3), {"a": 40})
        self.assertEqual(audit.recent_floor(old_hole, ["a"], n=30), {"a": -100})

    def test_an_unread_block_stops_the_search_there_instead_of_guessing(self):
        from pipeline import audit
        self.assertEqual(audit.steps(lambda h: None if h == 550 else (1000 + (10 if h >= 600 else 0), 1000), 100, 1000, grid=1), [])


class Flows(unittest.TestCase):
    """An indexer's transfer list is used only where it adds up to the balances read from the chain."""

    def transfer(self, height, other, amount, n=0):
        return {"block_height": str(height), "receipt_id": "R%d" % n, "log_index": 0, "transfer_index": n,
                "other_account_id": other, "amount": str(amount)}

    def setUp(self):
        from pipeline import flows
        self.flows = flows
        self.unit = 10**24
        self.blocks = {"2026-09-01": 100, "2026-09-02": 200, "2026-09-03": 300}
        self.rows = [self.transfer(100, "early", 5 * self.unit, 1),               # at the first reading's block: before the window
                     self.transfer(150, "solver.near", 4000 * self.unit, 2),
                     self.transfer(160, "solver.near", -1500 * self.unit, 3),
                     self.transfer(170, "small", 20 * self.unit, 4),
                     self.transfer(200, "whale", 9000 * self.unit, 5),            # at the reading's own block: inside the window
                     self.transfer(250, "whale", -9000 * self.unit, 6)]

    def test_a_day_that_adds_up_to_the_chain_is_kept_and_split_by_account(self):
        balances = {"2026-09-01": 0, "2026-09-02": 11520 * self.unit, "2026-09-03": 2520 * self.unit}
        got = self.flows.summarise(self.rows, self.blocks, balances, ["2026-09-02", "2026-09-03"])
        day = got["2026-09-02"]
        self.assertTrue(day["adds_up"])
        self.assertEqual((int(day["in"]) // self.unit, int(day["out"]) // self.unit, day["transfers"], day["accounts"]), (13020, 1500, 4, 3))
        self.assertEqual(list(day["by_account"]), ["whale", "solver.near"])          # largest first; under 1,000 NEAR goes to the rest
        self.assertEqual(day["rest"], [str(20 * self.unit), "0", 1, 1])
        self.assertEqual((day["largest_in"]["account"], day["largest_in"]["height"]), ("whale", 200))
        self.assertTrue(got["2026-09-03"]["adds_up"])

    def test_a_day_that_does_not_add_up_is_marked_and_left_out_of_every_total(self):
        balances = {"2026-09-01": 0, "2026-09-02": 11520 * self.unit, "2026-09-03": 0}   # the chain says more left than the list shows
        got = {"days": self.flows.summarise(self.rows, self.blocks, balances, ["2026-09-02", "2026-09-03"])}
        self.assertFalse(got["days"]["2026-09-03"]["adds_up"])
        total = self.flows.span(got, "2026-09-02", "2026-09-03")
        self.assertEqual((total["days"], total["skipped"]), (["2026-09-02"], ["2026-09-03"]))
        self.assertEqual(total["in"] // self.unit, 13020)
        self.assertEqual(total["accounts"]["solver.near"], [4000 * self.unit, 1500 * self.unit, 2])

    def test_a_row_listed_twice_is_counted_once_and_an_unread_balance_drops_the_day(self):
        balances = {"2026-09-01": 0, "2026-09-02": 11520 * self.unit, "2026-09-03": None}
        got = self.flows.summarise(self.rows + self.rows, self.blocks, balances, ["2026-09-02", "2026-09-03"])
        self.assertTrue(got["2026-09-02"]["adds_up"])
        self.assertNotIn("2026-09-03", got)   # unknown is not zero


class AuditForward(unittest.TestCase):
    """The audit's forward tests: a reading that could not be read is unknown, and an open hole fails in time."""

    def days(self, rows):
        # rows: [(day, {token: (credited, held)})]
        return [(d, {t: str(v[1]) if v[1] is not None else None for t, v in toks.items()},
                 {t: str(v[0]) if v[0] is not None else None for t, v in toks.items()}) for d, toks in rows]

    def run_tests(self, rows):
        from pipeline import score_audit
        return {t["id"]: t["status"] for t in score_audit.tests(self.days(rows), ["a", "b"])}

    def test_pending_until_the_reading_exists_then_pass_fail_or_unknown(self):
        whole = {"a": (10, 10), "b": (5, 9)}
        self.assertEqual(self.run_tests([("2026-11-13", whole)])["G1"], "PENDING")
        self.assertEqual(self.run_tests([("2026-11-14", whole)])["G1"], "PASS")
        self.assertEqual(self.run_tests([("2026-11-14", {"a": (10, 7), "b": (5, 9)})])["G1"], "FAIL")
        # a total that could not be read is never a pass, even when everything that was read is whole
        self.assertEqual(self.run_tests([("2026-11-14", {"a": (10, 10), "b": (5, None)})])["G1"], "UNKNOWN")

    def test_a_hole_must_close_within_three_readings(self):
        short, whole = {"a": (10, 7), "b": (5, 5)}, {"a": (10, 10), "b": (5, 5)}
        closed = [("2026-11-14", short), ("2026-11-15", short), ("2026-11-16", short), ("2026-11-17", whole)]
        self.assertEqual(self.run_tests(closed)["G3"], "PENDING")   # closed in time; the long test is not over yet
        stuck = closed[:3] + [("2026-11-17", short)]
        self.assertEqual(self.run_tests(stuck)["G3"], "FAIL")       # fails on the fourth short reading, not in March
        self.assertEqual(self.run_tests(stuck)["G2"], "FAIL")


class Revenue(unittest.TestCase):
    """Revenue read from the chain: NEAR and wNEAR received, reconciled against balances, never guessed."""

    def t(self, height, asset, amount, kind="NativeTransfer", other="intents.near", n=0):
        return {"block_height": str(height), "receipt_id": f"R{n}", "action_index": 0, "transfer_index": n, "log_index": None,
                "asset_id": asset, "amount": str(amount), "transfer_type": kind, "other_account_id": other}

    def test_a_day_counts_near_and_wnear_received_and_skips_wrapping(self):
        from pipeline import revenue
        rows = {"w": [self.t(150, "native:near", 5, n=1), self.t(160, "native:near", -2, other="x", n=2),
                      self.t(170, "nep141:wrap.near", 3, kind="FtTransfer", other="y", n=3),
                      self.t(175, "nep141:wrap.near", 4, kind="WrappedNear", other=None, n=4),     # wrapping is not income
                      self.t(180, "nep141:usdc", 9, kind="FtTransfer", n=5),                        # not NEAR
                      self.t(100, "native:near", 7, n=6)]}                                          # at the earlier reading: not in the day
        got = revenue.summarise_transfers(rows, {"2026-01-01": 100, "2026-01-02": 200}, ["2026-01-02"])["2026-01-02"]["w"]
        self.assertEqual((got["received"], got["native_in"], got["native_out"], got["transfers_in"]), ("8", "5", "2", 2))

    def test_a_window_reconciles_or_is_flagged_and_an_unknown_balance_gives_nothing(self):
        from pipeline import revenue
        day = {"received": "8", "native_in": "5", "native_out": "2", "transfers_in": 2, "from": {}}
        rec = {"wallets": ["w"], "balances": {"2026-01-01": {"w": "100"}, "2026-01-02": {"w": "103"}}, "transfers": {"2026-01-02": {"w": day}}}
        got = revenue.window(rec, "2026-01-02", "2026-01-02")
        self.assertEqual((got["received"], got["adds_up"]), (8, True))
        rec["balances"]["2026-01-02"]["w"] = "104"
        self.assertFalse(revenue.window(rec, "2026-01-02", "2026-01-02")["adds_up"])
        rec["balances"]["2026-01-02"]["w"] = None
        self.assertIsNone(revenue.window(rec, "2026-01-02", "2026-01-02"))   # unknown is not zero


class LeadLag(unittest.TestCase):
    def test_a_real_lead_is_found_and_noise_is_not(self):
        import random
        from pipeline import leadlag
        rng = random.Random(1)
        x = [rng.gauss(0, 1) for _ in range(120)]
        y = [0.0, 0.0] + [x[k] * 0.9 + rng.gauss(0, 0.3) for k in range(118)]      # y follows x two steps later
        got = leadlag.test(x, y, shifts=500, seed=3)
        self.assertEqual(got["lead_weeks"], 2)
        self.assertLess(got["p"], 0.01)
        z = [rng.gauss(0, 1) for _ in range(120)]
        self.assertGreater(leadlag.test(x, z, shifts=500, seed=3)["p"], 0.05)

    def test_weeks_are_monday_to_sunday_and_incomplete_weeks_are_dropped(self):
        from pipeline import leadlag
        days = {f"2026-11-{d:02d}": 1.0 for d in range(2, 13)}     # Monday 2 to Thursday 12 November
        weeks = leadlag.weekly(days, "sum")
        import datetime as dt
        self.assertEqual(weeks, {dt.date(2026, 11, 2): 7.0})


class Scenarios(unittest.TestCase):
    def test_coverage_compounds_and_the_needed_growth_reaches_full_coverage(self):
        from pipeline import claims
        sc = claims.scenarios(Fraction(1, 4), Fraction(1, 40), "2026-12-31", growth=(0.0, 1.0))
        flat = sc["rows"][0]
        years = sc["horizons"]["2029"]
        self.assertAlmostEqual(flat[("as now", "2029")], 0.25 / 1.025 ** years, places=9)
        self.assertIsNone(flat[("as now", "years")])                          # flat revenue never catches growing supply
        g = sc["need"][("as now", "2029")]
        self.assertAlmostEqual(0.25 * ((1 + g) / 1.025) ** years, 1.0, places=9)
        self.assertAlmostEqual(sc["rows"][1][("at 1.6%", "2029")], 0.25 * 0.025 / 0.016 * (2 / 1.016) ** years, places=9)


class ExitOrder(unittest.TestCase):
    def test_transfers_are_split_at_the_block_and_the_largest_outflows_kept(self):
        from pipeline import flows

        def t(h, amount, n):
            return {"block_height": str(h), "block_timestamp": str(h * 10**9), "receipt_id": f"R{n}", "log_index": 0, "transfer_index": n,
                    "other_account_id": f"a{n}", "amount": str(amount)}
        rows = [t(110, -50, 1), t(120, 10, 2), t(130, -5, 3), t(140, 7, 4), t(150, -9, 5), t(90, -99, 6)]
        got = flows.exit_order(rows, 100, 160, 130, top=2)
        self.assertEqual((got["before"], got["after"]), ({"in": "10", "out": "50"}, {"in": "7", "out": "14"}))
        self.assertEqual([x["amount"] for x in got["largest_out"]], ["50", "9"])


class Growth(unittest.TestCase):
    def test_a_steady_weekly_growth_is_annualised(self):
        import math
        from pipeline import growth
        weekly = math.log(2) / (365.25 / 7)            # doubling a year
        xs = list(range(20))
        a, b = growth.fit(xs, [5 + weekly * x for x in xs])
        self.assertAlmostEqual(growth.annual(b), 1.0, places=9)

    def test_the_fit_is_made_from_every_start_that_leaves_enough_weeks_and_shows_a_turn(self):
        import math
        from pipeline import growth
        up = [(f"w{k}", math.exp(0.1 * k)) for k in range(8)]               # rises for eight weeks
        down = [(f"w{8 + k}", math.exp(0.6 - 0.1 * k)) for k in range(5)]   # then falls for five
        fits = growth.by_start(up + down, min_weeks=4)
        self.assertEqual([f[0] for f in fits], [f"w{k}" for k in range(10)])  # starts w0..w9 each leave at least 4 weeks
        self.assertEqual([f[1] for f in fits], list(range(13, 3, -1)))
        self.assertLess(fits[-1][2], 0)                 # fitted over the fall alone, the trend is down
        self.assertGreater(max(f[2] for f in fits), 0)  # and some earlier start still shows growth


class RevenueSource(unittest.TestCase):
    """Who paid the revenue wallets, one step back on intents.near's ledger (pipeline/revenue_source.py)."""

    @staticmethod
    def _tx(*signed):
        import base64
        import json
        args = {"signed": [{"payload": {"message": json.dumps({"signer_id": s, "intents": its})}} for s, its in signed]}
        return {"actions": [{"FunctionCall": {"method_name": "execute_intents", "args": base64.b64encode(json.dumps(args).encode()).decode()}}]}

    def test_each_payment_is_matched_to_the_intent_with_its_wallet_and_amount_once(self):
        from pipeline import revenue_source as rs
        tx = self._tx(("alice", [{"intent": "native_withdraw", "receiver_id": "w1", "amount": "5"}]),
                      ("bob", [{"intent": "native_withdraw", "receiver_id": "w1", "amount": "5"},
                               {"intent": "ft_withdraw", "token": "wrap.near", "receiver_id": "w2", "amount": "7"}]),
                      ("carol", [{"intent": "transfer", "receiver_id": "w1", "amount": "5"}]))
        pays = [{"tx": "T", "wallet": "w1", "asset": "native:near", "amount": "5"},
                {"tx": "T", "wallet": "w1", "asset": "native:near", "amount": "5"},
                {"tx": "T", "wallet": "w1", "asset": "native:near", "amount": "5"},
                {"tx": "T", "wallet": "w2", "asset": "nep141:wrap.near", "amount": "7"},
                {"tx": "U", "wallet": "w2", "asset": "native:near", "amount": "1"}]
        rs.match_payers(pays, {"T": tx})
        self.assertEqual([p["payer"] for p in pays], ["alice", "bob", None, "bob", None])   # a transfer intent is not a withdrawal
        self.assertEqual(pays[3]["intent"], "ft_withdraw")

    def test_a_payload_given_as_json_text_is_read_like_one_given_as_an_object(self):
        import base64
        import json
        from pipeline import revenue_source as rs
        inner = {"signer_id": "dave", "intents": [{"intent": "native_withdraw", "receiver_id": "w1", "amount": "3"}]}
        args = {"signed": [{"payload": json.dumps(inner)}, {"payload": json.dumps(json.dumps(inner))}, {"payload": {"type": "text", "text": json.dumps(inner)}},
                           {"payload": "not json"}, {"payload": 7}]}
        tx = {"actions": [{"FunctionCall": {"method_name": "execute_intents", "args": base64.b64encode(json.dumps(args).encode()).decode()}}]}
        self.assertEqual([w[0] for w in rs.withdrawals(tx)], ["dave", "dave", "dave"])

    def test_a_payment_is_split_by_where_the_payers_wnear_came_from_and_untraced_counts_as_neither(self):
        from pipeline import revenue_source as rs
        T = "treasury"
        p = {"payer": "x", "amount": "100", "in": [{"from": T, "amount": "30"}, {"from": "solver", "amount": "10"}]}
        self.assertEqual(rs.split(p, T), (Fraction(75), Fraction(25)))
        self.assertEqual(rs.split({"payer": "x", "amount": "100", "in": []}, T), (None, None))
        self.assertEqual(rs.split({"payer": None, "amount": "100"}, T), (None, None))

    def test_the_window_uses_the_same_readings_as_the_revenue_count_and_fails_closed_without_them(self):
        from pipeline import revenue_source as rs
        blocks = {"2026-01-01": {"height": 100}, "2026-01-02": {"height": 200}, "2026-01-03": {"height": 300}}
        rec = {"treasury": "t", "payments": [
            {"height": 100, "amount": "1", "payer": "a", "in": [{"from": "t", "amount": "1"}]},     # at the reading before: out
            {"height": 150, "amount": "2", "payer": "a", "in": [{"from": "t", "amount": "1"}]},
            {"height": 300, "amount": "4", "payer": "b", "in": [{"from": "s", "amount": "1"}]},
            {"height": 250, "amount": "8", "payer": None}]}
        s = rs.summarise(rec, blocks, "2026-01-02", "2026-01-03")
        self.assertEqual((s["payments"], s["paid"], s["treasury"], s["other"], s["untraced"]), (3, 14, 2, 4, 8))
        self.assertIsNone(rs.summarise(rec, blocks, "2026-01-01", "2026-01-03"))   # no reading before the first day


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
            # normally within 15 seconds; never as late as ten minutes, even across a gap in block production
            self.assertLess(b["timestamp"], midnight + 600 * 10**9, d)

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
