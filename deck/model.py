import random


class Deck:
    """사용자별 덱과 패(Hand)를 관리하는 클래스 (최대 9장 제한)."""

    MAX_DECK_SIZE: int = 9
    MAX_HAND_SIZE: int = 9

    def __init__(self, owner_id: int):
        self.owner_id = owner_id
        self.cards: list[str] = []
        self.hand: list[str] = []

    def is_deck_full(self) -> bool:
        """덱이 최대치(9장)인지 확인합니다."""
        return len(self.cards) >= self.MAX_DECK_SIZE

    def is_hand_full(self) -> bool:
        """패가 최대치(9장)인지 확인합니다."""
        return len(self.hand) >= self.MAX_HAND_SIZE

    def add_card(self, card: str) -> bool:
        """덱에 카드를 추가합니다. 최대치 도달 시 추가되지 않고 False를 반환합니다."""
        if self.is_deck_full():
            return False
        self.cards.append(card)
        return True

    def remove_card(self, card: str) -> bool:
        """덱에서 특정 카드를 1장 제거합니다."""
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def deck_shuffle(self) -> None:
        """현재 덱에 남아있는 카드를 무작위로 섞습니다."""
        random.shuffle(self.cards)

    def draw_card(self, num_cards: int = 1) -> list[str]:
        """덱에서 카드를 뽑아 패로 가져옵니다.

        패의 최대치(9장) 또는 덱의 잔여 장수를 초과하여 뽑을 수 없습니다.
        """
        available_hand_space = max(0, self.MAX_HAND_SIZE - len(self.hand))
        if available_hand_space == 0:
            return []

        draw_limit = min(num_cards, available_hand_space)
        drawn_cards = []
        for _ in range(draw_limit):
            if not self.cards:
                break
            card = self.cards.pop(0)
            self.hand.append(card)
            drawn_cards.append(card)
        return drawn_cards

    def use_card(self, card: str) -> bool:
        """패(Hand)에서 카드를 1장 사용(제거)합니다."""
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False

    def current_hand(self) -> list[str]:
        """현재 패(Hand)에 있는 카드 목록을 반환합니다."""
        return list(self.hand)

    def current_deck(self) -> list[str]:
        """현재 덱에 남아있는 카드 목록을 반환합니다."""
        return list(self.cards)

    def reset_deck(self) -> None:
        """패에 든 카드를 모두 덱으로 되돌리고 덱을 섞습니다."""
        self.cards.extend(self.hand)
        self.hand.clear()
        self.deck_shuffle()

    def clear(self) -> None:
        """덱과 패를 모두 비웁니다."""
        self.cards.clear()
        self.hand.clear()

