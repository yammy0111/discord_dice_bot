from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from deck.model import Deck


DB_PATH = Path(os.getenv("DB_PATH", "data/decks.sqlite3"))


class DeckManager:
    """유저별 다중 덱 및 활성 덱을 관리하는 매니저 클래스."""

    MAX_USER_DECKS: int = 5

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._user_decks: dict[int, dict[str, Deck]] = {}  # user_id -> {deck_name: Deck}
        self._active_deck: dict[int, str] = {}             # user_id -> active_deck_name
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
                uid = int(user_id)
                if "decks" in data and isinstance(data["decks"], dict):
                    # Multi-deck format
                    decks_map: dict[str, Deck] = {}
                    for d_name, d_data in data["decks"].items():
                        if isinstance(d_data, dict):
                            d_data["owner_id"] = uid
                            d_data.setdefault("name", d_name)
                            decks_map[d_name] = Deck.from_dict(d_data)
                    active_name = str(data.get("active_deck_name", ""))
                    if not active_name or active_name not in decks_map:
                        active_name = list(decks_map.keys())[0] if decks_map else "기본"
                    self._user_decks[uid] = decks_map
                    self._active_deck[uid] = active_name
                else:
                    # Legacy single-deck format
                    data["owner_id"] = uid
                    deck = Deck.from_dict(data)
                    d_name = deck.name or "기본"
                    self._user_decks[uid] = {d_name: deck}
                    self._active_deck[uid] = d_name
            except (TypeError, ValueError, json.JSONDecodeError, KeyError):
                continue

    def save_deck(self, user_id: int) -> None:
        decks_map = self._user_decks.get(user_id)
        if not decks_map:
            return

        active_name = self._active_deck.get(user_id, list(decks_map.keys())[0])
        payload = json.dumps(
            {
                "active_deck_name": active_name,
                "decks": {
                    d_name: deck.to_dict()
                    for d_name, deck in decks_map.items()
                },
            },
            ensure_ascii=False,
        )
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
        return bool(self._user_decks.get(user_id))

    def get_deck(self, user_id: int) -> Deck | None:
        """해당 유저의 현재 활성(선택된) 덱을 반환합니다. 없으면 None을 반환합니다."""
        decks_map = self._user_decks.get(user_id)
        if not decks_map:
            return None
        active_name = self._active_deck.get(user_id)
        if active_name and active_name in decks_map:
            return decks_map[active_name]
        # 활성 덱이 지정되지 않았거나 없는 경우 첫 번째 덱 반환 및 활성화
        first_name = list(decks_map.keys())[0]
        self._active_deck[user_id] = first_name
        return decks_map[first_name]

    def get_active_deck_name(self, user_id: int) -> str:
        """현재 활성화된 덱의 이름을 반환합니다."""
        return self._active_deck.get(user_id, "기본")

    def get_all_decks(self, user_id: int) -> dict[str, Deck]:
        """해당 유저가 보유한 모든 덱 맵 {덱이름: Deck}을 반환합니다."""
        return dict(self._user_decks.get(user_id, {}))

    def get_deck_by_name(self, user_id: int, name: str) -> Deck | None:
        """특정 이름의 덱을 반환합니다."""
        return self._user_decks.get(user_id, {}).get(name.strip())

    def create_deck(self, user_id: int, name: str = "기본") -> Deck:
        """새로운 덱을 생성하고 활성화합니다."""
        clean_name = name.strip() if name and name.strip() else "기본"
        deck = Deck(owner_id=user_id, name=clean_name)
        if user_id not in self._user_decks:
            self._user_decks[user_id] = {}
        self._user_decks[user_id][clean_name] = deck
        self._active_deck[user_id] = clean_name
        self.save_deck(user_id)
        return deck

    def add_new_deck(
        self, user_id: int, name: str, set_active: bool = True
    ) -> tuple[bool, str, Deck | None]:
        """새로운 덱을 추가합니다."""
        clean_name = name.strip()
        if not clean_name:
            return False, "덱 이름을 입력해주세요.", None

        decks_map = self._user_decks.setdefault(user_id, {})
        if len(decks_map) >= self.MAX_USER_DECKS:
            return (
                False,
                f"덱은 최대 {self.MAX_USER_DECKS}개까지만 보유할 수 있습니다.",
                None,
            )

        if clean_name in decks_map:
            return False, f"이미 '{clean_name}' 이름의 덱이 존재합니다.", None

        deck = Deck(owner_id=user_id, name=clean_name)
        decks_map[clean_name] = deck
        if set_active or user_id not in self._active_deck:
            self._active_deck[user_id] = clean_name
        self.save_deck(user_id)
        return True, "덱 생성 완료", deck

    def switch_deck(self, user_id: int, name: str) -> tuple[bool, str, Deck | None]:
        """활성 덱을 전환합니다."""
        clean_name = name.strip()
        decks_map = self._user_decks.get(user_id)
        if not decks_map or clean_name not in decks_map:
            return False, f"'{clean_name}' 덱을 찾을 수 없습니다.", None

        self._active_deck[user_id] = clean_name
        self.save_deck(user_id)
        return True, "덱 전환 완료", decks_map[clean_name]

    def delete_deck(self, user_id: int, name: str) -> tuple[bool, str, str | None]:
        """특정 덱을 삭제합니다. (반환값: (성공여부, 메시지, 새로 활성화된 덱 이름))"""
        clean_name = name.strip()
        decks_map = self._user_decks.get(user_id)
        if not decks_map or clean_name not in decks_map:
            return False, f"'{clean_name}' 덱이 존재하지 않습니다.", None

        if len(decks_map) <= 1:
            return False, "보유 중인 덱이 1개뿐이므로 삭제할 수 없습니다. (최소 1개 유지)", None

        del decks_map[clean_name]
        new_active: str | None = None
        if self._active_deck.get(user_id) == clean_name:
            new_active = list(decks_map.keys())[0]
            self._active_deck[user_id] = new_active

        self.save_deck(user_id)
        return True, f"'{clean_name}' 덱을 삭제했습니다.", new_active

    def rename_deck(
        self, user_id: int, old_name: str, new_name: str
    ) -> tuple[bool, str]:
        """덱 이름을 변경합니다."""
        c_old = old_name.strip()
        c_new = new_name.strip()
        if not c_new:
            return False, "새로운 덱 이름을 입력해주세요."

        decks_map = self._user_decks.get(user_id)
        if not decks_map or c_old not in decks_map:
            return False, f"'{c_old}' 덱이 존재하지 않습니다."

        if c_old != c_new and c_new in decks_map:
            return False, f"'{c_new}' 덱이 이미 존재합니다."

        deck = decks_map.pop(c_old)
        deck.name = c_new
        decks_map[c_new] = deck

        if self._active_deck.get(user_id) == c_old:
            self._active_deck[user_id] = c_new

        self.save_deck(user_id)
        return True, f"덱 이름이 '{c_old}'에서 '{c_new}'(으)로 변경되었습니다."

    def get_or_create_deck(self, user_id: int) -> Deck:
        """해당 유저의 활성 덱을 가져오거나, 없으면 새로 생성하여 반환합니다."""
        deck = self.get_deck(user_id)
        if not deck:
            return self.create_deck(user_id)
        return deck

    def remove_deck(self, user_id: int) -> bool:
        """해당 유저의 모든 덱을 삭제합니다."""
        if user_id in self._user_decks:
            del self._user_decks[user_id]
            self._active_deck.pop(user_id, None)
            with closing(self._connect()) as conn:
                with conn:
                    conn.execute("DELETE FROM player_decks WHERE user_id = ?", (user_id,))
            return True
        return False


# 전역 싱글톤 매니저 인스턴스
deck_manager = DeckManager()
