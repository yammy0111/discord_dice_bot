from __future__ import annotations

import unittest

from deck.model import Deck, SpecialCard, format_special_card_display


class TestSpecialCards(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(owner_id=12345)
        self.deck.set_base_max_cost(5)
        self.deck.restore_cost(5.0)

    def test_add_and_format_special_card(self):
        card = self.deck.add_special_card("푸리오소", cost=4, description="모든 적에게 9회 공격")
        self.assertEqual(len(self.deck.special_cards), 1)
        self.assertEqual(len(self.deck.hand), 0)
        self.assertEqual(len(self.deck.cards), 0)
        self.assertEqual(len(self.deck.original_cards), 0)

        disp = format_special_card_display(card)
        expected = '[푸리오소]\n(4)\n"모든 적에게 9회 공격"'
        self.assertEqual(disp, expected)

    def test_use_special_card(self):
        card = self.deck.add_special_card("푸리오소", cost=4, description="강력한 공격")
        self.assertEqual(self.deck.current_cost, 5.0)

        # 1st use: success, deducts cost, card remains in special_cards
        succ, reason, used_card = self.deck.use_special_card("푸리오소")
        self.assertTrue(succ)
        self.assertEqual(self.deck.current_cost, 1.0)
        self.assertEqual(len(self.deck.special_cards), 1)

        # 2nd use: fails because current_cost (1.0) < cost (4)
        succ2, reason2, _ = self.deck.use_special_card("푸리오소")
        self.assertFalse(succ2)
        self.assertIn("코스트가 부족합니다", reason2)

    def test_reset_deck_preserves_special_cards(self):
        self.deck.add_special_card("스페셜", cost=2)
        self.deck.use_special_card("스페셜")
        self.assertEqual(self.deck.current_cost, 3.0)

        # Battle reset: restores cost to base_max_cost, special_cards remain intact
        self.deck.reset_deck_and_hand()
        self.assertEqual(self.deck.current_cost, 5.0)
        self.assertEqual(len(self.deck.special_cards), 1)

    def test_remove_special_card(self):
        self.deck.add_special_card("카드A", cost=1)
        self.deck.add_special_card("카드B", cost=2)
        self.assertEqual(len(self.deck.special_cards), 2)

        self.assertTrue(self.deck.remove_special_card("카드A"))
        self.assertEqual(len(self.deck.special_cards), 1)
        self.assertEqual(self.deck.special_cards[0].name, "카드B")
        self.assertFalse(self.deck.remove_special_card("없는카드"))

    def test_update_special_card_info(self):
        card = self.deck.add_special_card("스킬", cost=2, description="구설명")
        self.deck.update_special_card_info("스킬", cost=3, description="신설명")
        self.assertEqual(card.cost, 3)
        self.assertEqual(card.description, "신설명")

    def test_serialization(self):
        self.deck.add_special_card("EGO", cost=3, description="강력")
        self.deck.use_special_card("EGO")
        data = self.deck.to_dict()

        restored = Deck.from_dict(data)
        self.assertEqual(len(restored.special_cards), 1)
        restored_card = restored.special_cards[0]
        self.assertEqual(restored_card.name, "EGO")
        self.assertEqual(restored_card.cost, 3)
        self.assertEqual(restored_card.description, "강력")


if __name__ == "__main__":
    unittest.main()
