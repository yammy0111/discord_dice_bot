from __future__ import annotations

import json
import sqlite3
import os
from contextlib import closing
from pathlib import Path

from deck.model import Deck


DB_PATH = Path(os.getenv("DB_PATH", "data/decks.sqlite3"))


class DeckManager:
    """유저별 덱 인스턴스를 관리하는 매니저 클래스."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._decks: dict[int, Deck] = {}
        self._init_db()
        self._load_all()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS player_decks (
                        user_id INTEGER PRIMARY KEY,
                        payload TEXT NOT NULL,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

    def _load_all(self) -> None:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT user_id, payload FROM player_decks").fetchall()

        for user_id, payload in rows:
            try:
                data = json.loads(payload)
                data["owner_id"] = int(user_id)
                self._decks[int(user_id)] = Deck.from_dict(data)
            except (TypeError, ValueError, json.JSONDecodeError, KeyError):
                continue

    def save_deck(self, user_id: int) -> None:
        deck = self._decks.get(user_id)
        if not deck:
            return

        payload = json.dumps(deck.to_dict(), ensure_ascii=False)
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    INSERT INTO player_decks (user_id, payload, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        payload = excluded.payload,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id, payload),
                )

    def has_deck(self, user_id: int) -> bool:
        """해당 유저의 덱이 존재하는지 확인합니다."""
        return user_id in self._decks

    def get_deck(self, user_id: int) -> Deck | None:
        """해당 유저의 덱을 반환합니다. 없으면 None을 반환합니다."""
        return self._decks.get(user_id)

    def create_deck(self, user_id: int) -> Deck:
        """해당 유저의 새 덱을 생성합니다."""
        deck = Deck(owner_id=user_id)
        self._decks[user_id] = deck
        self.save_deck(user_id)
        return deck

    def get_or_create_deck(self, user_id: int) -> Deck:
        """해당 유저의 덱을 가져오거나, 없으면 새로 생성하여 반환합니다."""
        if user_id not in self._decks:
            return self.create_deck(user_id)
        return self._decks[user_id]

    def remove_deck(self, user_id: int) -> bool:
        """해당 유저의 덱을 삭제합니다."""
        if user_id in self._decks:
            del self._decks[user_id]
            with closing(self._connect()) as conn:
                with conn:
                    conn.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id,))
            return True
        return False


# 전역 싱글톤 매니저 인스턴스
deck_manager = DeckManager()
