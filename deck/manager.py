from deck.model import Deck


class DeckManager:
    """유저별 덱 인스턴스를 관리하는 매니저 클래스."""

    def __init__(self):
        self._decks: dict[int, Deck] = {}

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
            return True
        return False


# 전역 싱글톤 매니저 인스턴스
deck_manager = DeckManager()
