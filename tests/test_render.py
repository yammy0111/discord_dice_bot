# tests/test_render.py

import unittest
from dice.engine import DiceEngine


class TestRendererAndEngine(unittest.TestCase):

    def test_engine_roll(self):
        engine = DiceEngine()
        result = engine.roll("1d1 + 2 * 3")

        self.assertEqual(result.expression, "1d1 + 2 * 3")
        self.assertEqual(result.value, 7)
        self.assertEqual(result.substituted_expression, "1+2*3")
        self.assertGreaterEqual(len(result.calculation_steps), 0)

    def test_large_dice_clean_parentheses(self):
        engine = DiceEngine()
        result = engine.roll("10d6")

        # 10d6 굴렸을 때 겉에 불필요한 괄호 ( ... ) 가 생기지 않아야 함
        self.assertFalse(result.substituted_expression.startswith("("))
        self.assertFalse(result.substituted_expression.endswith(")"))


if __name__ == "__main__":
    unittest.main()
