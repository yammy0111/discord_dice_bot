# tests/test_percent.py

import unittest
from dice.engine import DiceEngine


class TestPercent(unittest.TestCase):

    def setUp(self):
        self.engine = DiceEngine()

    def test_percentage_standalone(self):
        result = self.engine.roll("50%")
        self.assertEqual(result.value, 0.5)

    def test_percentage_in_multiplication(self):
        result = self.engine.roll("100 * 20%")
        self.assertEqual(result.value, 20)

    def test_percentage_with_dice(self):
        result = self.engine.roll("1d1 * 50%")
        self.assertEqual(result.value, 0.5)

    def test_percentile_dice_d_percent(self):
        result = self.engine.roll("1d%")
        self.assertGreaterEqual(result.value, 1)
        self.assertLessEqual(result.value, 100)
        self.assertEqual(result.roll_logs[0].expression, "1d100")

    def test_multiple_percentile_dice(self):
        result = self.engine.roll("2d%")
        self.assertGreaterEqual(result.value, 2)
        self.assertLessEqual(result.value, 200)
        self.assertEqual(result.roll_logs[0].expression, "2d100")


if __name__ == "__main__":
    unittest.main()
