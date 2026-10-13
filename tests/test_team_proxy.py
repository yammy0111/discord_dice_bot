from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from deck.manager import DeckManager


class TestTeamAndProxy(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_decks.sqlite3"
        self.manager = DeckManager(db_path=self.db_path)
        self.guild_id = 123456

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_team_setting_and_membership(self):
        u1 = 1001
        u2 = 1002
        u3 = 1003

        self.manager.set_user_team(self.guild_id, u1, "레드팀")
        self.manager.set_user_team(self.guild_id, u2, "레드팀")
        self.manager.set_user_team(self.guild_id, u3, "블루팀")

        self.assertEqual(self.manager.get_user_team(self.guild_id, u1), "레드팀")
        self.assertTrue(self.manager.are_teammates(self.guild_id, u1, u2))
        self.assertFalse(self.manager.are_teammates(self.guild_id, u1, u3))

        members = self.manager.get_team_members(self.guild_id, "레드팀")
        self.assertEqual(set(members), {u1, u2})

        # Leave team
        self.assertTrue(self.manager.leave_user_team(self.guild_id, u1))
        self.assertIsNone(self.manager.get_user_team(self.guild_id, u1))
        self.assertFalse(self.manager.are_teammates(self.guild_id, u1, u2))

    def test_proxy_play_setting(self):
        u1 = 2001
        self.assertFalse(self.manager.is_proxy_play_enabled(self.guild_id, u1))

        self.manager.set_proxy_play(self.guild_id, u1, True)
        self.assertTrue(self.manager.is_proxy_play_enabled(self.guild_id, u1))

        self.manager.set_proxy_play(self.guild_id, u1, False)
        self.assertFalse(self.manager.is_proxy_play_enabled(self.guild_id, u1))

    def test_persistence_of_team_and_proxy(self):
        u1 = 3001
        self.manager.set_user_team(self.guild_id, u1, "드래곤팀")
        self.manager.set_proxy_play(self.guild_id, u1, True)

        # Reload new manager instance
        new_mgr = DeckManager(db_path=self.db_path)
        self.assertEqual(new_mgr.get_user_team(self.guild_id, u1), "드래곤팀")
        self.assertTrue(new_mgr.is_proxy_play_enabled(self.guild_id, u1))


if __name__ == "__main__":
    unittest.main()
