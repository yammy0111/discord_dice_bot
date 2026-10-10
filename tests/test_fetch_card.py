from __future__ import annotations

import unittest

from deck.model import Deck, Card


class TestFetchCard(unittest.TestCase):
    def setUp(self):
        self.deck = Deck(owner_id=12345)
        self.deck.set_base_max_cost(5)
        self.deck.restore_cost(5.0)

    def test_fetch_card_by_name(self):
        self.deck.add_card("타격", cost=1, description="기본 타격")
        self.deck.add_card("수비", cost=1, description="기본 수비")
        self.deck.add_card("강타", cost=2, description="강한 타격")

        self.assertEqual(len(self.deck.cards), 3)
        self.assertEqual(len(self.deck.hand), 0)

        succ, reason, card, refilled = self.deck.fetch_card_from_deck("수비")
        self.assertTrue(succ)
        self.assertIsNotNone(card)
        self.assertEqual(card.name, "수비")
        self.assertEqual(len(self.deck.hand), 1)
        self.assertEqual(len(self.deck.cards), 2)
        self.assertEqual(self.deck.hand[0].name, "수비")
        self.assertFalse(refilled)

    def test_fetch_card_at_index(self):
        self.deck.add_card("카드1", cost=1)
        self.deck.add_card("카드2", cost=2)

        succ, reason, card, refilled = self.deck.fetch_card_from_deck_at(1)
        self.assertTrue(succ)
        self.assertEqual(card.name, "카드2")
        self.assertEqual(len(self.deck.hand), 1)
        self.assertEqual(len(self.deck.cards), 1)
        self.assertEqual(self.deck.cards[0].name, "카드1")

    def test_fetch_card_when_hand_full(self):
        for i in range(Deck.MAX_HAND_SIZE):
            self.deck.add_temp_card(f"패{i}")

        self.deck.add_card("타격", cost=1)
        self.assertTrue(self.deck.is_hand_full())

        succ, reason, card, refilled = self.deck.fetch_card_from_deck("타격")
        self.assertFalse(succ)
        self.assertIn("패가 가득 찼습니다", reason)

    def test_fetch_card_not_in_remaining_deck(self):
        self.deck.add_card("유일카드", cost=1)
        # Draw the only card
        self.deck.draw_card(1)
        self.assertEqual(len(self.deck.cards), 0)
        self.assertEqual(len(self.deck.hand), 1)

        # Since cards is empty and original_cards exists, fetching will refill the deck
        succ, reason, card, refilled = self.deck.fetch_card_from_deck("유일카드")
        self.assertTrue(succ)
        self.assertTrue(refilled)
        self.assertEqual(len(self.deck.hand), 2)

    def test_fetch_unregistered_card(self):
        self.deck.add_card("타격", cost=1)
        succ, reason, card, refilled = self.deck.fetch_card_from_deck("없는카드")
        self.assertFalse(succ)
        self.assertIn("등록되어 있지 않습니다", reason)


if __name__ == "__main__":
    unittest.main()
