import random


class Deck:
    """사용자별 덱과 패(Hand)를 관리하는 클래스."""

    def __init__(self, owner_id: int):
        self.owner_id = owner_id
        self.cards: list[str] = []
        self.hand: list[str] = []

    def add_card(self, card: str) -> None:
        """덱에 카드를 추가합니다."""
        self.cards.append(card)

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
        """덱에서 지정한 장수만큼 카드를 뽑아 패(Hand)로 가져옵니다.

        덱의 카드 수가 요청한 수보다 적으면 남은 카드만 모두 뽑습니다.
        """
        drawn_cards = []
        for _ in range(num_cards):
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
