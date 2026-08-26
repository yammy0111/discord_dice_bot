# tests/test_multiple_dice.py

import unittest
from unittest.mock import MagicMock
from dice.engine import DiceEngine
from dice.errors import DiceError, LimitExceededError
from utils.embeds import build_dice_embed


class TestMultipleDice(unittest.TestCase):

    def setUp(self):
        self.engine = DiceEngine()

    def test_roll_multiple_valid(self):
        results = self.engine.roll_multiple("1d1+5, 2d1*3, 10-2")
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].value, 6)
        self.assertEqual(results[1].value, 6)
        self.assertEqual(results[2].value, 8)

    def test_roll_multiple_with_spaces_and_trailing_comma(self):
        results = self.engine.roll_multiple("  1d1+1 , 2d1+2 , ")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].value, 2)
        self.assertEqual(results[1].value, 4)

    def test_roll_multiple_limit_exceeded(self):
        expr = ", ".join(["1d6"] * 11)
        with self.assertRaises(LimitExceededError):
            self.engine.roll_multiple(expr)

    def test_roll_multiple_empty_error(self):
        with self.assertRaises(DiceError):
            self.engine.roll_multiple(" ,  , ")

    def test_multiple_dice_embed_rendering(self):
        results = self.engine.roll_multiple("1d6, 2d6+3")
        mock_user = MagicMock()
        mock_user.display_name = "MultiTester"
        mock_user.display_avatar.url = "http://example.com/avatar.png"

        embed = build_dice_embed(results, mock_user)
        self.assertIsNotNone(embed.title)
        if embed.title:
            self.assertIn("총 2개", embed.title)
        self.assertEqual(len(embed.fields), 2)
        
        field0_name = embed.fields[0].name
        field1_name = embed.fields[1].name
        self.assertIsNotNone(field0_name)
        self.assertIsNotNone(field1_name)
        if field0_name and field1_name:
            self.assertIn("#1", field0_name)
            self.assertIn("#2", field1_name)


if __name__ == "__main__":
    unittest.main()
