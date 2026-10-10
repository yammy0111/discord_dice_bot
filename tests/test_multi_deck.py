from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deck.manager import DeckManager
from deck.model import Deck, Card


class TestMultiDeck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_decks.sqlite3"
        self.manager = DeckManager(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_and_switch_decks(self):
        user_id = 999
        # Default creation
        deck1 = self.manager.create_deck(user_id, name="기본")
        deck1.add_card("불꽃", cost=1)
        self.manager.save_deck(user_id)

        # Add second deck
        succ, msg, deck2 = self.manager.add_new_deck(user_id, name="얼음덱", set_active=True)
        self.assertTrue(succ)
        self.assertIsNotNone(deck2)
        deck2.add_card("눈보라", cost=2)
        self.manager.save_deck(user_id)

        # Active deck should be "얼음덱"
        self.assertEqual(self.manager.get_active_deck_name(user_id), "얼음덱")
        active = self.manager.get_deck(user_id)
        self.assertIsNotNone(active)
        self.assertEqual(active.name, "얼음덱")
        self.assertEqual(len(active.original_cards), 1)
        self.assertEqual(active.original_cards[0].name, "눈보라")

        # Switch back to "기본"
        succ, msg, switched = self.manager.switch_deck(user_id, "기본")
        self.assertTrue(succ)
        self.assertEqual(self.manager.get_active_deck_name(user_id), "기본")
        active = self.manager.get_deck(user_id)
        self.assertEqual(active.name, "기본")
        self.assertEqual(active.original_cards[0].name, "불꽃")

    def test_duplicate_deck_name(self):
        user_id = 888
        self.manager.create_deck(user_id, name="화염")
        succ, msg, _ = self.manager.add_new_deck(user_id, name="화염")
        self.assertFalse(succ)
        self.assertIn("이미", msg)

    def test_rename_deck(self):
        user_id = 777
        self.manager.create_deck(user_id, name="구이름")
        succ, msg = self.manager.rename_deck(user_id, "구이름", "신이름")
        self.assertTrue(succ)
        self.assertEqual(self.manager.get_active_deck_name(user_id), "신이름")
        self.assertIsNotNone(self.manager.get_deck_by_name(user_id, "신이름"))
        self.assertIsNone(self.manager.get_deck_by_name(user_id, "구이름"))

    def test_delete_deck(self):
        user_id = 666
        self.manager.create_deck(user_id, name="덱1")
        # Cannot delete the only deck
        succ, msg, _ = self.manager.delete_deck(user_id, "덱1")
        self.assertFalse(succ)

        # Add second deck and delete active deck
        self.manager.add_new_deck(user_id, "덱2", set_active=True)
        self.assertEqual(self.manager.get_active_deck_name(user_id), "덱2")

        succ, msg, new_active = self.manager.delete_deck(user_id, "덱2")
        self.assertTrue(succ)
        self.assertEqual(new_active, "덱1")
        self.assertEqual(self.manager.get_active_deck_name(user_id), "덱1")
        self.assertEqual(len(self.manager.get_all_decks(user_id)), 1)

    def test_persistence_and_reload(self):
        user_id = 555
        d1 = self.manager.create_deck(user_id, name="A덱")
        d1.add_card("카드A", cost=1)
        d2 = self.manager.add_new_deck(user_id, "B덱", set_active=True)[2]
        d2.add_card("카드B", cost=2)
        self.manager.save_deck(user_id)

        # Reload new manager from same db
        new_manager = DeckManager(db_path=self.db_path)
        self.assertEqual(new_manager.get_active_deck_name(user_id), "B덱")
        decks = new_manager.get_all_decks(user_id)
        self.assertEqual(len(decks), 2)
        self.assertIn("A덱", decks)
        self.assertIn("B덱", decks)
        self.assertEqual(decks["A덱"].original_cards[0].name, "카드A")
        self.assertEqual(decks["B덱"].original_cards[0].name, "카드B")

    def test_max_decks_limit(self):
        user_id = 444
        self.manager.create_deck(user_id, name="덱1")
        for i in range(2, 6):
            succ, msg, _ = self.manager.add_new_deck(user_id, name=f"덱{i}")
            self.assertTrue(succ)

        self.assertEqual(len(self.manager.get_all_decks(user_id)), 5)

        # 6th deck should fail
        succ, msg, _ = self.manager.add_new_deck(user_id, name="덱6")
        self.assertFalse(succ)
        self.assertIn("최대 5개", msg)


if __name__ == "__main__":
    unittest.main()
