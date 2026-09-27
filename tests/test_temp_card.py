from __future__ import annotations

import unittest

from deck.model import Card, Deck


class TestTemporaryCard(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(owner_id=12345)
        self.deck.add_card("불꽃", 1, "화염 피해")
        self.deck.add_card("얼음", 2, "빙결 피해")

    def test_add_temp_card(self):
        self.assertEqual(len(self.deck.original_cards), 2)
        self.assertEqual(len(self.deck.cards), 2)
        self.assertEqual(len(self.deck.hand), 0)

        temp_card = self.deck.add_temp_card("포션", 0, "체력 5 회복")
        self.assertIsNotNone(temp_card)
        if temp_card:
            self.assertTrue(temp_card.is_temporary)
        self.assertEqual(len(self.deck.hand), 1)
        self.assertEqual(self.deck.hand[0].name, "포션")

        self.assertEqual(len(self.deck.original_cards), 2)
        self.assertEqual(len(self.deck.cards), 2)
        self.assertNotIn("포션", [c.name for c in self.deck.original_cards])
        self.assertNotIn("포션", [c.name for c in self.deck.cards])

    def test_use_temp_card(self):
        self.deck.add_temp_card("포션", 0, "체력 5 회복")
        self.assertEqual(len(self.deck.hand), 1)

        succ, reason, card = self.deck.use_card("포션")
        self.assertTrue(succ)
        self.assertIsNotNone(card)
        if card:
            self.assertEqual(card.name, "포션")
        self.assertEqual(len(self.deck.hand), 0)
        self.assertEqual(len(self.deck.cards), 2)
        self.assertEqual(len(self.deck.original_cards), 2)

    def test_reset_deck_clears_temp_card(self):
        self.deck.draw_card(1)
        self.deck.add_temp_card("임시타격", 1, "추가 피해")
        self.assertEqual(len(self.deck.hand), 2)

        self.deck.reset_deck_and_hand()
        self.assertEqual(len(self.deck.hand), 0)
        self.assertEqual(len(self.deck.cards), 2)
        self.assertEqual(len(self.deck.original_cards), 2)
        for c in self.deck.cards:
            self.assertFalse(c.is_temporary)
            self.assertNotEqual(c.name, "임시타격")

    def test_refill_deck_keeps_temp_card_in_hand(self):
        self.deck.add_temp_card("임시타격", 1, "추가 피해")
        self.assertEqual(len(self.deck.hand), 1)

        self.deck.refill_deck()
        self.assertEqual(len(self.deck.hand), 1)
        self.assertEqual(self.deck.hand[0].name, "임시타격")
        self.assertEqual(len(self.deck.cards), 2)

    def test_hand_limit(self):
        for i in range(9):
            self.deck.add_temp_card(f"임시{i}", 0, "")
        self.assertEqual(len(self.deck.hand), 9)
        self.assertTrue(self.deck.is_hand_full())

        extra = self.deck.add_temp_card("초과카드", 0, "")
        self.assertIsNone(extra)
        self.assertEqual(len(self.deck.hand), 9)


if __name__ == "__main__":
    unittest.main()
