import unittest

from dice.engine import DiceEngine
from dice.errors import DiceError, LimitExceededError


class TestDerivedRoll(unittest.TestCase):

    def test_derived_roll_reuses_base_value(self):
        engine = DiceEngine()
        result = engine.roll_derived("1d1 > +5, *2+3, -1")

        self.assertEqual(result.base.value, 1)
        self.assertEqual([item.value for item in result.derived], [6, 5, 0])
        self.assertEqual(result.derived[0].full_expression, "1+5")
        self.assertEqual(result.derived[1].full_expression, "1*2+3")
        self.assertEqual(result.derived[2].full_expression, "1-1")


    def test_multi_derived_roll_applies_next_level_to_previous_results(self):
        engine = DiceEngine()
        result = engine.roll_derived("1d1 > +5, *2+3 > -1")

        self.assertEqual([item.value for item in result.derived], [6, 5, 5, 4])
        self.assertEqual([item.level for item in result.derived], [1, 1, 2, 2])
        self.assertEqual(result.derived[2].source_label, "1차 #1")
        self.assertEqual(result.derived[2].source_value, 6)
        self.assertEqual(result.derived[2].full_expression, "6-1")
        self.assertEqual(result.derived[3].source_label, "1차 #2")
        self.assertEqual(result.derived[3].source_value, 5)
        self.assertEqual(result.derived[3].full_expression, "5-1")

    def test_multi_derived_roll_limits_branching_results(self):
        engine = DiceEngine()
        formulas = ", ".join("+1" for _ in range(5))
        with self.assertRaises(LimitExceededError):
            engine.roll_derived(f"1d1 > {formulas} > {formulas}")

    def test_derived_roll_requires_separator(self):
        engine = DiceEngine()
        with self.assertRaises(DiceError):
            engine.roll_derived("1d1 + 5")

    def test_derived_roll_limits_formula_count(self):
        from dice.limits import MAX_EXPRESSIONS_COUNT
        engine = DiceEngine()
        formulas = ", ".join("+1" for _ in range(MAX_EXPRESSIONS_COUNT + 1))
        with self.assertRaises(LimitExceededError):
            engine.roll_derived(f"1d1 > {formulas}")


    def test_derived_roll_with_percent_base(self):
        engine = DiceEngine()
        result = engine.roll_derived("100% > +5")
        self.assertEqual(result.base.value, 1)
        self.assertEqual(result.derived[0].value, 6)

        result_half = engine.roll_derived("50% > +5")
        self.assertEqual(result_half.base.value, 0.5)
        self.assertEqual(result_half.derived[0].value, 5.5)

    def test_derived_roll_with_percentile_dice(self):
        engine = DiceEngine()
        result = engine.roll_derived("1d% > +5")
        self.assertGreaterEqual(result.base.value, 1)
        self.assertLessEqual(result.base.value, 100)
        self.assertEqual(result.derived[0].value, result.base.value + 5)

    def test_multi_level_derived_roll_with_percent(self):
        engine = DiceEngine()
        result = engine.roll_derived("100 > *50% > +5")
        self.assertEqual(result.base.value, 100)
        self.assertEqual(result.derived[0].value, 50)
        self.assertEqual(result.derived[1].value, 55)

    def test_derived_formula_percent_shorthand(self):
        engine = DiceEngine()
        # 50% 단독 표기
        res1 = engine.roll_derived("100 > 50%")
        self.assertEqual(res1.derived[0].value, 50)

        # %50 단독 표기
        res2 = engine.roll_derived("100 > %50")
        self.assertEqual(res2.derived[0].value, 50)


if __name__ == "__main__":
    unittest.main()
