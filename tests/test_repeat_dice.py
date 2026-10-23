# tests/test_repeat_dice.py

import unittest
from dice.engine import DiceEngine
from dice.errors import ParserError, LimitExceededError
from dice.limits import MAX_REPEAT_COUNT


class TestRepeatDice(unittest.TestCase):
    def setUp(self):
        self.engine = DiceEngine()

    def test_repeat_simple_dice(self):
        # 1d1^5는 항상 5 (1d1이 5번 굴려짐)
        result = self.engine.roll("1d1^5")
        self.assertEqual(result.value, 5)
        self.assertEqual(len(result.roll_logs), 5)
        for entry in result.roll_logs:
            self.assertEqual(entry.expression, "1d1")
            self.assertEqual(entry.total, 1)

    def test_repeat_3d6_5_times(self):
        # 3d6^5
        result = self.engine.roll("3d6^5")
        self.assertEqual(len(result.roll_logs), 5)
        for entry in result.roll_logs:
            self.assertEqual(entry.expression, "3d6")
            self.assertEqual(len(entry.rolls), 3)
            self.assertEqual(sum(entry.rolls), entry.total)
        self.assertEqual(result.value, sum(e.total for e in result.roll_logs))

    def test_repeat_with_other_operators(self):
        # 덧셈 및 곱셈과 혼합: 1d1^3 + 10 * 2 -> 3 + 20 = 23
        result = self.engine.roll("1d1^3 + 10 * 2")
        self.assertEqual(result.value, 23)
        self.assertEqual(len(result.roll_logs), 3)

    def test_repeat_parenthesized_expression(self):
        # (1d1 + 2)^4 -> (1 + 2) * 4 = 12
        result = self.engine.roll("(1d1 + 2)^4")
        self.assertEqual(result.value, 12)
        self.assertEqual(len(result.roll_logs), 4)

    def test_repeat_limit_exceeded(self):
        with self.assertRaises(LimitExceededError):
            self.engine.roll(f"1d1^{MAX_REPEAT_COUNT + 1}")

    def test_repeat_invalid_count(self):
        with self.assertRaises(ParserError):
            self.engine.roll("3d6^0")

        with self.assertRaises(ParserError):
            self.engine.roll("3d6^2.5")

    def test_repeat_with_mackerel(self):
        # 간고등어 주사위와도 함께 동작
        result = self.engine.roll("1d20^3", bias="높은 수")
        self.assertEqual(len(result.roll_logs), 3)
        self.assertEqual(result.value, sum(e.total for e in result.roll_logs))


if __name__ == "__main__":
    unittest.main()
