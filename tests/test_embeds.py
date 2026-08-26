# tests/test_embeds.py

import unittest
from unittest.mock import MagicMock
from dice.engine import DiceEngine
from utils.embeds import build_dice_embed, build_error_embed


class TestEmbeds(unittest.TestCase):

    def test_build_dice_embed_default(self):
        engine = DiceEngine()
        result = engine.roll("2d6 + 3")

        mock_user = MagicMock()
        mock_user.display_name = "Tester"
        mock_user.display_avatar.url = "http://example.com/avatar.png"

        # show_detail=False (기본)
        embed = build_dice_embed(result, mock_user, show_detail=False)
        self.assertEqual(embed.title, "주사위 굴림 결과")
        self.assertEqual(len(embed.fields), 2)  # 요청 수식, 최종 결과만 표시

    def test_build_dice_embed_detailed(self):
        engine = DiceEngine()
        result = engine.roll("2d6 + 3")

        mock_user = MagicMock()
        mock_user.display_name = "Tester"
        mock_user.display_avatar.url = "http://example.com/avatar.png"

        # show_detail=True (상세)
        embed = build_dice_embed(result, mock_user, show_detail=True)
        self.assertEqual(embed.title, "주사위 굴림 결과")
        self.assertGreater(len(embed.fields), 2)  # 개별 주사위, 치환 수식 등 추가 표시

    def test_build_error_embed(self):
        embed = build_error_embed("테스트 에러 메시지", expression="1000d100")
        self.assertEqual(embed.title, "주사위 굴림 오류")
        self.assertEqual(embed.description, "**테스트 에러 메시지**")


if __name__ == "__main__":
    unittest.main()
