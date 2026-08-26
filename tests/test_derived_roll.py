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
        formulas = ", ".join("+1" for _ in range(4))
        with self.assertRaises(LimitExceededError):
            engine.roll_derived(f"1d1 > {formulas} > {formulas}")

    def test_derived_roll_requires_separator(self):
        engine = DiceEngine()
        with self.assertRaises(DiceError):
            engine.roll_derived("1d1 + 5")

    def test_derived_roll_limits_formula_count(self):
        engine = DiceEngine()
        formulas = ", ".join("+1" for _ in range(11))
        with self.assertRaises(LimitExceededError):
            engine.roll_derived(f"1d1 > {formulas}")


if __name__ == "__main__":
    unittest.main()
