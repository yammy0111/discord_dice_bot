import random


class Deck:
    """사용자별 덱과 패(Hand)를 관리하는 클래스 (최대 9장 제한)."""

    MAX_DECK_SIZE: int = 9
    MAX_HAND_SIZE: int = 9

    def __init__(self, owner_id: int):
        self.owner_id = owner_id
        self.original_cards: list[str] = []  # 등록된 원본 덱 카드 목록
        self.cards: list[str] = []           # 현재 덱에 남아있는 카드 목록
        self.hand: list[str] = []            # 현재 손에 든 패

    def is_deck_full(self) -> bool:
        """등록된 덱 카드가 최대치(9장)인지 확인합니다."""
        return len(self.original_cards) >= self.MAX_DECK_SIZE

    def is_hand_full(self) -> bool:
        """패가 최대치(9장)인지 확인합니다."""
        return len(self.hand) >= self.MAX_HAND_SIZE

    def add_card(self, card: str) -> bool:
        """덱에 카드를 추가(등록)합니다. 최대치 도달 시 추가되지 않고 False를 반환합니다."""
        if self.is_deck_full():
            return False
        self.original_cards.append(card)
        self.cards.append(card)
        return True

    def remove_card(self, card: str) -> bool:
        """덱에서 특정 카드를 등록 해제합니다."""
        removed = False
        if card in self.original_cards:
            self.original_cards.remove(card)
            removed = True
        if card in self.cards:
            self.cards.remove(card)
        return removed

    def deck_shuffle(self) -> None:
        """현재 덱에 남아있는 카드를 무작위로 섞습니다."""
        random.shuffle(self.cards)

    def refill_deck(self) -> None:
        """패는 그대로 유지하고, 덱만 원래 등록된 카드들로 다시 채운 뒤 섞습니다."""
        self.cards = list(self.original_cards)
        self.deck_shuffle()

    def reset_game(self) -> None:
        """게임을 재시작합니다. 패를 모두 비우고 덱을 등록된 카드로 가득 채워 섞습니다."""
        self.hand.clear()
        self.cards = list(self.original_cards)
        self.deck_shuffle()

    def reset_deck(self) -> None:
        """기존 덱 초기화: 게임 재시작(패 비우기 + 덱 원상복구)을 수행합니다."""
        self.reset_game()

    def draw_card(self, num_cards: int = 1) -> tuple[list[str], bool]:
        """덱에서 카드를 뽑아 패로 가져옵니다.

        덱 고갈 시 패는 그대로 두고 덱을 원래 등록된 카드로 초기화(리필)하여 계속해서 뽑습니다.
        반환값: (뽑힌 카드 리스트, 덱 고갈로 인한 초기화 발생 여부)
        """
        available_hand_space = max(0, self.MAX_HAND_SIZE - len(self.hand))
        if available_hand_space == 0:
            return [], False

        draw_limit = min(num_cards, available_hand_space)
        drawn_cards = []
        refilled = False

        for _ in range(draw_limit):
            # 덱이 고갈된 경우: 패는 그대로 두고 덱을 리필
            if not self.cards:
                if not self.original_cards:
                    break
                self.refill_deck()
                refilled = True

            if not self.cards:
                break

            card = self.cards.pop(0)
            self.hand.append(card)
            drawn_cards.append(card)

        return drawn_cards, refilled

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

    def registered_deck(self) -> list[str]:
        """원래 등록된 덱 카드 목록을 반환합니다."""
        return list(self.original_cards)

    def clear(self) -> None:
        """덱과 패를 모두 비웁니다."""
        self.original_cards.clear()
        self.cards.clear()
        self.hand.clear()


