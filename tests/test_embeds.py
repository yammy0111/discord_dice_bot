# tests/test_embeds.py

import unittest
from unittest.mock import MagicMock
from dice.engine import DiceEngine
from utils.embeds import build_dice_embed, build_error_embed


class TestEmbeds(unittest.TestCase):

    def test_build_dice_embed(self):
        engine = DiceEngine()
        result = engine.roll("2d6 + 3")

        mock_user = MagicMock()
        mock_user.display_name = "Tester"
        mock_user.display_avatar.url = "http://example.com/avatar.png"

        embed = build_dice_embed(result, mock_user)
        self.assertEqual(embed.title, "🎲 주사위 굴림 결과")
        field_val = embed.fields[0].value
        self.assertIsNotNone(field_val)
        if field_val:
            self.assertIn("2d6 + 3", field_val)

    def test_build_error_embed(self):
        embed = build_error_embed("테스트 에러 메시지", expression="1000d100")
        self.assertEqual(embed.title, "⚠️ 주사위 굴림 오류")
        self.assertEqual(embed.description, "**테스트 에러 메시지**")


if __name__ == "__main__":
    unittest.main()
