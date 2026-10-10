from __future__ import annotations

import unittest

from deck.model import Deck, Card


class TestDiscardCard(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(owner_id=12345)
        self.deck.set_base_max_cost(3)
        self.deck.restore_cost(3.0)
        self.deck.add_card("타격", cost=2, description="타격 설명")
        self.deck.add_card("수비", cost=1, description="수비 설명")
        self.deck.draw_card(2)

    def test_discard_card_by_name(self):
        self.assertEqual(len(self.deck.hand), 2)
        self.assertEqual(self.deck.current_cost, 3.0)

        succ, reason, card = self.deck.discard_card("타격")
        self.assertTrue(succ)
        self.assertIsNotNone(card)
        self.assertEqual(card.name, "타격")
        self.assertEqual(len(self.deck.hand), 1)
        self.assertEqual(self.deck.hand[0].name, "수비")
        # Cost should NOT be consumed
        self.assertEqual(self.deck.current_cost, 3.0)

    def test_discard_card_at_index(self):
        self.assertEqual(len(self.deck.hand), 2)
        succ, reason, card = self.deck.discard_card_at(0)
        self.assertTrue(succ)
        self.assertEqual(len(self.deck.hand), 1)
        self.assertEqual(self.deck.current_cost, 3.0)

    def test_discard_nonexistent_card(self):
        succ, reason, card = self.deck.discard_card("없는카드")
        self.assertFalse(succ)
        self.assertIsNone(card)
        self.assertEqual(len(self.deck.hand), 2)


if __name__ == "__main__":
    unittest.main()
