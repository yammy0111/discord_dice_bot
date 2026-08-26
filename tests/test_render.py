# tests/test_render.py

import unittest
from dice.engine import DiceEngine


class TestRendererAndEngine(unittest.TestCase):

    def test_engine_roll(self):
        engine = DiceEngine()
        result = engine.roll("1d1 + 2 * 3")

        self.assertEqual(result.expression, "1d1 + 2 * 3")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.substituted_expression, "(1+(2*3))")
        self.assertGreaterEqual(len(result.calculation_steps), 0)


if __name__ == "__main__":
    unittest.main()
