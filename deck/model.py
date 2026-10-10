from __future__ import annotations

import random
import re
from typing import Any


class Card:
    """단일 카드의 속성을 나타내는 클래스.

    소모 코스트는 '음이 아닌 정수' (cost >= 0) 입니다.
    """

    def __init__(
        self,
        name: str,
        cost: int = 0,
        description: str = "",
        is_temporary: bool = False,
    ):
        self.name = name.strip()
        self.cost: int = max(0, int(cost))
        self.base_cost: int = self.cost
        self.description: str = description.strip()
        self.is_temporary: bool = bool(is_temporary)

    def clone(self) -> Card:
        """기본 코스트와 설명을 유지한 새 카드 인스턴스를 복제합니다."""
        c = Card(self.name, self.base_cost, self.description, self.is_temporary)
        c.cost = self.cost
        return c

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cost": self.cost,
            "base_cost": self.base_cost,
            "description": self.description,
            "is_temporary": self.is_temporary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Card:
        card = cls(
            str(data.get("name", "")),
            int(data.get("base_cost", data.get("cost", 0))),
            str(data.get("description", "")),
            bool(data.get("is_temporary", False)),
        )
        card.cost = max(0, int(data.get("cost", card.base_cost)))
        return card

    def __repr__(self) -> str:
        temp_tag = ", temp=True" if self.is_temporary else ""
        return f"Card({self.name}, cost={self.cost}, desc='{self.description}'{temp_tag})"


def parse_card_input(card_str: str) -> tuple[str, int]:
    """'이름:코스트' 또는 '이름(코스트)' 형태의 문자열을 파싱합니다.

    코스트가 없으면 기본값 0을 반환합니다.
    """
    card_str = card_str.strip()

    # 1. 괄호 형식: 이름(코스트)
    paren_match = re.match(r"^(.+?)\s*\(\s*(\d+)\s*\)$", card_str)
    if paren_match:
        name = paren_match.group(1).strip()
        cost = int(paren_match.group(2))
        return name, cost

    # 2. 콜론 형식: 이름:코스트
    colon_match = re.match(r"^(.+?)\s*:\s*(\d+)$", card_str)
    if colon_match:
        name = colon_match.group(1).strip()
        cost = int(colon_match.group(2))
        return name, cost

    # 3. 코스트 없는 단일 이름
    return card_str, 0


def format_cost(val: float) -> str:
    """유리수 코스트를 보기 좋게 포맷합니다. (정수면 정수로, 소수면 소수점 표기)"""
    if val.is_integer():
        return str(int(val))
    # 소수점 아래 불필요한 0 제거
    return f"{val:.2f}".rstrip("0").rstrip(".")


def format_card_display(
    name: str, cost: int, description: str = "", show_detail: bool = True
) -> str:
    """요청된 양식대로 카드 정보를 포맷합니다:
    상세(show_detail=True):
    [카드 이름]
    (숫자)
    "카드 설명"

    비상세(show_detail=False):
    [카드 이름] (숫자)
    """
    if show_detail:
        desc = f'"{description}"' if description else '""'
        return f"[{name}]\n({cost})\n{desc}"
    return f"[{name}] ({cost})"


class SpecialCard:
    """패/덱과 별개로 보관되는 특수 카드 (E.G.O, 환상체 책장 등).

    - cost: 소모 코스트 (음이 아닌 정수 >= 0)
    - description: 카드 설명
    """

    def __init__(
        self,
        name: str,
        cost: int = 0,
        description: str = "",
    ):
        self.name = name.strip()
        self.cost: int = max(0, int(cost))
        self.base_cost: int = self.cost
        self.description: str = description.strip()

    def clone(self) -> SpecialCard:
        c = SpecialCard(self.name, self.base_cost, self.description)
        c.cost = self.cost
        return c

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cost": self.cost,
            "base_cost": self.base_cost,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SpecialCard:
        card = cls(
            name=str(data.get("name", "")),
            cost=int(data.get("base_cost", data.get("cost", 0))),
            description=str(data.get("description", "")),
        )
        card.cost = max(0, int(data.get("cost", card.base_cost)))
        return card

    def __repr__(self) -> str:
        return f"SpecialCard({self.name}, cost={self.cost}, desc='{self.description}')"


def format_special_card_display(card: SpecialCard, show_detail: bool = True) -> str:
    """특수 카드 정보를 포맷합니다:
    [카드 이름]
    (숫자)
    "카드 설명"
    """
    return format_card_display(card.name, card.cost, card.description, show_detail=show_detail)




class Deck:
    """사용자별 덱, 패(Hand), 코스트(Cost)를 관리하는 클래스.

    규칙:
    - 덱/패 최대 매수: 9장
    - 카드 소모 코스트: 음이 아닌 정수 (0, 1, 2, ...)
    - 코스트 보유량 (current_cost): 음이 아닌 유리수 (0, 0.5, 1.25, ...)
    - 최대 코스트 (max_cost): 자연수 (1, 2, 3, ...)
    - 전투 중 최대 코스트 보정값 (bonus_max_cost): 정수, 단 최종 최대 코스트는 1 이상
    """

    MAX_DECK_SIZE: int = 9
    MAX_HAND_SIZE: int = 9

    def __init__(self, owner_id: int, name: str = "기본"):
        self.owner_id = owner_id
        self.name = name.strip() if name and name.strip() else "기본"
        self.original_cards: list[Card] = []  # 등록된 원본 덱 카드 목록
        self.cards: list[Card] = []           # 현재 덱에 남아있는 카드 목록
        self.hand: list[Card] = []            # 현재 손에 든 패
        self.special_cards: list[SpecialCard] = []  # 패/덱과 분리된 특수 카드 목록

        # 코스트 시스템
        self.base_max_cost: int = 3           # 기본 최대 코스트 (자연수 >= 1)
        self.bonus_max_cost: int = 0          # 전투 중 최대 코스트 보정값
        self.current_cost: float = 3.0        # 현재 코스트 보유량 (음이 아닌 유리수)

    def clone_deck(self, new_name: str) -> Deck:
        """현재 덱을 복제하여 새로운 이름의 덱 인스턴스를 생성합니다."""
        d = Deck(owner_id=self.owner_id, name=new_name)
        d.original_cards = [c.clone() for c in self.original_cards]
        d.cards = [c.clone() for c in self.cards]
        d.hand = [c.clone() for c in self.hand]
        d.special_cards = [c.clone() for c in self.special_cards]
        d.base_max_cost = self.base_max_cost
        d.bonus_max_cost = self.bonus_max_cost
        d.current_cost = self.current_cost
        return d

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "name": self.name,
            "original_cards": [card.to_dict() for card in self.original_cards],
            "cards": [card.to_dict() for card in self.cards],
            "hand": [card.to_dict() for card in self.hand],
            "special_cards": [card.to_dict() for card in self.special_cards],
            "base_max_cost": self.base_max_cost,
            "bonus_max_cost": self.bonus_max_cost,
            "current_cost": self.current_cost,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Deck:
        deck = cls(
            owner_id=int(data["owner_id"]),
            name=str(data.get("name", "기본")),
        )
        deck.original_cards = [
            Card.from_dict(card)
            for card in data.get("original_cards", [])
            if isinstance(card, dict)
        ]
        deck.cards = [
            Card.from_dict(card)
            for card in data.get("cards", [])
            if isinstance(card, dict)
        ]
        deck.hand = [
            Card.from_dict(card)
            for card in data.get("hand", [])
            if isinstance(card, dict)
        ]
        deck.special_cards = [
            SpecialCard.from_dict(card)
            for card in data.get("special_cards", [])
            if isinstance(card, dict)
        ]
        deck.base_max_cost = max(1, int(data.get("base_max_cost", 3)))
        deck.bonus_max_cost = int(data.get("bonus_max_cost", 0))
        deck.current_cost = float(data.get("current_cost", deck.base_max_cost))
        deck.clamp_current_cost()
        return deck

    @property
    def max_cost(self) -> int:
        """현재 적용되는 최대 코스트 (기본 + 전투 중 증가분, 자연수)."""
        return max(1, self.base_max_cost + self.bonus_max_cost)

    def clamp_current_cost(self) -> None:
        """현재 코스트를 0 이상, 최대 코스트 이하로 보정합니다."""
        self.current_cost = max(0.0, min(float(self.max_cost), self.current_cost))

    def set_base_max_cost(self, value: int) -> bool:
        """기본 최대 코스트를 설정합니다. (자연수 >= 1 만 허용)"""
        if value < 1:
            return False
        self.base_max_cost = int(value)
        self.clamp_current_cost()
        return True

    def add_max_cost(self, amount: int) -> int:
        """이번 전투 동안 최대 코스트를 증감합니다.

        최대 코스트는 1 미만으로 내려가지 않으며, 반환값은 실제 증감량입니다.
        """
        old_max = self.max_cost
        self.bonus_max_cost += int(amount)
        if self.base_max_cost + self.bonus_max_cost < 1:
            self.bonus_max_cost = 1 - self.base_max_cost
        self.clamp_current_cost()
        return self.max_cost - old_max

    def restore_cost(self, amount: float) -> float:
        """코스트를 일정 수치만큼 증감합니다.

        반환값: 실제로 변동된 양. 음수 입력 시 감소량도 음수로 반환합니다.
        """
        old_cost = self.current_cost
        self.current_cost += float(amount)
        self.clamp_current_cost()
        return self.current_cost - old_cost

    def modify_hand_card_cost(
        self, card_name: str, new_cost: int, current_cost: int | None = None
    ) -> Card | None:
        """패에 있는 특정 카드의 소모 코스트를 이번 패에 머무는 동안 변경합니다.

        current_cost가 지정된 경우, 패에서 해당 코스트를 가진 동명 카드를 찾아 변경합니다.
        new_cost는 음이 아닌 정수 (>= 0) 여야 합니다.
        """
        if new_cost < 0:
            return None
        for card in self.hand:
            if card.name == card_name:
                if current_cost is not None and card.cost != current_cost:
                    continue
                card.cost = int(new_cost)
                return card
        return None

    def modify_hand_card_cost_at(self, hand_index: int, new_cost: int) -> Card | None:
        """패 위치를 지정해 카드 코스트를 변경하고 변경된 카드를 반환합니다."""
        if new_cost < 0 or hand_index < 0 or hand_index >= len(self.hand):
            return None

        card = self.hand[hand_index]
        card.cost = int(new_cost)
        return card


    def is_deck_full(self) -> bool:
        """등록된 덱 카드가 최대치(9장)인지 확인합니다."""
        return len(self.original_cards) >= self.MAX_DECK_SIZE

    def is_hand_full(self) -> bool:
        """패가 최대치(9장)인지 확인합니다."""
        return len(self.hand) >= self.MAX_HAND_SIZE

    def add_card(self, card_name: str, cost: int = 0, description: str = "") -> bool:
        """덱에 카드를 추가(등록)합니다. 최대치 도달 시 추가되지 않고 False를 반환합니다."""
        if self.is_deck_full():
            return False
        card = Card(card_name, cost, description)
        self.original_cards.append(card)
        self.cards.append(card.clone())
        return True

    def add_temp_card(
        self, card_name: str, cost: int = 0, description: str = ""
    ) -> Card | None:
        """패(Hand)에만 임시 카드를 1장 추가합니다.

        덱(original_cards, cards)에는 등록되지 않으며, 패가 가득 찬 경우 추가되지 않고 None을 반환합니다.
        """
        if self.is_hand_full():
            return None
        card = Card(card_name, cost, description, is_temporary=True)
        self.hand.append(card)
        return card

    def remove_card(self, card_name: str) -> bool:
        """덱에서 특정 카드를 등록 해제합니다."""
        removed = False
        for card in list(self.original_cards):
            if card.name == card_name:
                self.original_cards.remove(card)
                removed = True
                break
        for card in list(self.cards):
            if card.name == card_name:
                self.cards.remove(card)
                break
        return removed

    def remove_card_at(self, deck_index: int) -> Card | None:
        """등록된 원본 덱 위치를 지정해 카드 1장을 제거하고 제거된 카드를 반환합니다."""
        if deck_index < 0 or deck_index >= len(self.original_cards):
            return None

        removed_card = self.original_cards.pop(deck_index)
        for card in list(self.cards):
            if (
                card.name == removed_card.name
                and card.base_cost == removed_card.base_cost
                and card.description == removed_card.description
            ):
                self.cards.remove(card)
                break
        return removed_card

    def get_card(self, card_name: str) -> Card | None:
        """등록된 카드, 현재 덱, 패에서 일치하는 카드를 검색하여 반환합니다."""
        for card in self.original_cards:
            if card.name == card_name:
                return card
        for card in self.cards:
            if card.name == card_name:
                return card
        for card in self.hand:
            if card.name == card_name:
                return card
        return None

    def update_card_info(
        self,
        card_name: str,
        cost: int | None = None,
        description: str | None = None,
    ) -> bool:
        """이미 등록된 카드의 기본 코스트 및 설명을 수정합니다."""
        found = False
        # 원본 등록 카드 갱신
        for card in self.original_cards:
            if card.name == card_name:
                if cost is not None:
                    card.cost = max(0, int(cost))
                    card.base_cost = card.cost
                if description is not None:
                    card.description = description.strip()
                found = True

        # 현재 덱 카드 갱신
        for card in self.cards:
            if card.name == card_name:
                if cost is not None:
                    card.cost = max(0, int(cost))
                    card.base_cost = card.cost
                if description is not None:
                    card.description = description.strip()
                found = True

        # 현재 패 카드 갱신
        for card in self.hand:
            if card.name == card_name:
                if cost is not None:
                    card.cost = max(0, int(cost))
                    card.base_cost = card.cost
                if description is not None:
                    card.description = description.strip()
                found = True

        return found

    def deck_shuffle(self) -> None:
        """현재 덱에 남아있는 카드를 무작위로 섞습니다."""
        random.shuffle(self.cards)

    def refill_deck(self) -> None:
        """패는 그대로 유지하고, 덱만 원래 등록된 카드들로 다시 채운 뒤 섞습니다."""
        self.cards = [c.clone() for c in self.original_cards]
        self.deck_shuffle()

    def reset_deck_and_hand(self) -> None:
        """덱과 패 초기화: 패를 비우고 덱을 원상복구하며, 전투 중 증가 코스트를 초기화하고 코스트를 완충합니다."""
        self.hand.clear()
        self.cards = [c.clone() for c in self.original_cards]
        self.deck_shuffle()
        self.bonus_max_cost = 0
        self.current_cost = float(self.base_max_cost)

    def reset_deck(self) -> None:
        """덱과 패 초기화를 수행합니다."""
        self.reset_deck_and_hand()

    def draw_card(self, num_cards: int = 1) -> tuple[list[Card], bool]:
        """덱에서 카드를 뽑아 패로 가져옵니다.

        덱 고갈 시 패는 그대로 두고 덱을 원래 등록된 카드로 초기화(리필)하여 계속해서 뽑습니다.
        반환값: (뽑힌 카드 객체 리스트, 덱 고갈로 인한 리필 발생 여부)
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

    def fetch_card_from_deck(
        self, card_name: str, target_cost: int | None = None
    ) -> tuple[bool, str, Card | None, bool]:
        """남은 덱에서 특정 카드를 직접 패로 가져옵니다.

        덱이 고갈된 상태이면 패는 그대로 두고 덱을 리필한 후 검색합니다.
        반환값: (성공여부, 메시지/사유, 가져온 Card 객체, 리필 발생 여부)
        """
        if self.is_hand_full():
            return False, f"패가 가득 찼습니다. (최대 {self.MAX_HAND_SIZE}장)", None, False

        refilled = False
        if not self.cards:
            if not self.original_cards:
                return False, "덱에 등록된 카드가 없습니다.", None, False
            self.refill_deck()
            refilled = True

        target_card: Card | None = None
        target_idx: int = -1
        for idx, card in enumerate(self.cards):
            if card.name == card_name:
                if target_cost is not None and card.cost != target_cost:
                    continue
                target_card = card
                target_idx = idx
                break

        if target_card is None or target_idx == -1:
            in_orig = any(c.name == card_name for c in self.original_cards)
            if in_orig:
                return (
                    False,
                    f"현재 남은 덱에 '{card_name}' 카드가 없습니다. (이미 패에 있거나 소모되었습니다.)",
                    None,
                    refilled,
                )
            return False, f"덱에 '{card_name}' 카드가 등록되어 있지 않습니다.", None, refilled

        fetched = self.cards.pop(target_idx)
        self.hand.append(fetched)
        return True, "가져오기 성공", fetched, refilled

    def fetch_card_from_deck_at(
        self, deck_index: int
    ) -> tuple[bool, str, Card | None, bool]:
        """남은 덱의 특정 인덱스 위치 카드를 직접 패로 가져옵니다.

        반환값: (성공여부, 메시지/사유, 가져온 Card 객체, 리필 발생 여부)
        """
        if self.is_hand_full():
            return False, f"패가 가득 찼습니다. (최대 {self.MAX_HAND_SIZE}장)", None, False

        refilled = False
        if not self.cards:
            if not self.original_cards:
                return False, "덱에 등록된 카드가 없습니다.", None, False
            self.refill_deck()
            refilled = True

        if deck_index < 0 or deck_index >= len(self.cards):
            return False, "지정한 위치의 카드가 남은 덱에 없습니다.", None, refilled

        fetched = self.cards.pop(deck_index)
        self.hand.append(fetched)
        return True, "가져오기 성공", fetched, refilled

    def use_card(
        self, card_name: str, target_cost: int | None = None
    ) -> tuple[bool, str, Card | None]:
        """패(Hand)에서 카드를 1장 사용합니다.

        target_cost가 지정된 경우, 해당 코스트를 가진 카드를 우선적으로 찾아 사용합니다.
        반환값: (성공여부, 메시지/사유, 사용된 Card 객체)
        """
        target_card: Card | None = None
        for card in self.hand:
            if card.name == card_name:
                if target_cost is not None and card.cost != target_cost:
                    continue
                target_card = card
                break

        # target_cost를 지정했는데 못 찾은 경우, 일반 이름으로 fallback하지 않고 실패 처리
        if not target_card:
            if target_cost is not None:
                return False, f"패에 코스트 {target_cost}인 '{card_name}' 카드가 없습니다.", None
            return False, "패에 카드가 없습니다.", None

        # 코스트 검사 (소모 코스트 <= 보유 코스트)
        if self.current_cost < target_card.cost:
            return False, "코스트가 부족합니다.", target_card

        # 코스트 차감 및 패에서 제거
        self.current_cost -= float(target_card.cost)
        self.hand.remove(target_card)
        return True, "사용 성공", target_card

    def use_card_at(self, hand_index: int) -> tuple[bool, str, Card | None]:
        """패 위치를 지정해 카드를 1장 사용합니다."""
        if hand_index < 0 or hand_index >= len(self.hand):
            return False, "선택한 카드가 패에 없습니다.", None

        target_card = self.hand[hand_index]
        if self.current_cost < target_card.cost:
            return False, "코스트가 부족합니다.", target_card

        self.current_cost -= float(target_card.cost)
        self.hand.pop(hand_index)
        return True, "사용 성공", target_card

    def discard_card(
        self, card_name: str, target_cost: int | None = None
    ) -> tuple[bool, str, Card | None]:
        """패(Hand)에서 카드를 1장 버립니다. (코스트 소모 없음)

        target_cost가 지정된 경우, 해당 코스트를 가진 카드를 우선적으로 찾아 버립니다.
        반환값: (성공여부, 메시지/사유, 버려진 Card 객체)
        """
        target_card: Card | None = None
        for card in self.hand:
            if card.name == card_name:
                if target_cost is not None and card.cost != target_cost:
                    continue
                target_card = card
                break

        if not target_card:
            if target_cost is not None:
                return False, f"패에 코스트 {target_cost}인 '{card_name}' 카드가 없습니다.", None
            return False, f"패에 '{card_name}' 카드가 없습니다.", None

        self.hand.remove(target_card)
        return True, "버리기 성공", target_card

    def discard_card_at(self, hand_index: int) -> tuple[bool, str, Card | None]:
        """패 위치를 지정해 카드를 1장 버립니다. (코스트 소모 없음)"""
        if hand_index < 0 or hand_index >= len(self.hand):
            return False, "선택한 카드가 패에 없습니다.", None

        target_card = self.hand.pop(hand_index)
        return True, "버리기 성공", target_card

    def has_multiple_hand_variants(self, card_name: str) -> bool:
        """패에 같은 이름이면서 구분 가능한 카드가 여러 장 있는지 확인합니다."""
        variants = {
            (card.cost, card.base_cost, card.description)
            for card in self.hand
            if card.name == card_name
        }
        return len(variants) > 1

    def hand_variants_text(self, card_name: str) -> str:
        """동명 카드 선택 안내용 텍스트를 반환합니다."""
        lines = []
        for i, card in enumerate(self.hand):
            if card.name == card_name:
                lines.append(
                    f"{i + 1}. {format_card_display(card.name, card.cost, card.description)}"
                )
        return "\n".join(lines)


    def current_hand(self) -> list[Card]:
        """현재 패(Hand)에 있는 카드 목록을 반환합니다."""
        return list(self.hand)

    def current_deck(self) -> list[Card]:
        """현재 덱에 남아있는 카드 목록을 반환합니다."""
        return list(self.cards)

    def registered_deck(self) -> list[Card]:
        """원래 등록된 덱 카드 목록을 반환합니다."""
        return list(self.original_cards)

    def current_special_cards(self) -> list[SpecialCard]:
        """현재 보유 중인 특수 카드 목록을 반환합니다."""
        return list(self.special_cards)

    # --- 특수 카드 (Special Cards) 관리 ---

    def add_special_card(
        self,
        card_name: str,
        cost: int = 0,
        description: str = "",
    ) -> SpecialCard:
        """패/덱과 분리된 특수 카드를 추가합니다."""
        card = SpecialCard(card_name, cost, description)
        self.special_cards.append(card)
        return card

    def remove_special_card(self, card_name: str) -> bool:
        """특수 카드를 목록에서 제거합니다."""
        for card in list(self.special_cards):
            if card.name == card_name:
                self.special_cards.remove(card)
                return True
        return False

    def remove_special_card_at(self, index: int) -> SpecialCard | None:
        """인덱스 위치의 특수 카드를 제거합니다."""
        if index < 0 or index >= len(self.special_cards):
            return None
        return self.special_cards.pop(index)

    def get_special_card(self, card_name: str) -> SpecialCard | None:
        """이름으로 특수 카드를 검색합니다."""
        for card in self.special_cards:
            if card.name == card_name:
                return card
        return None

    def use_special_card(self, card_name: str) -> tuple[bool, str, SpecialCard | None]:
        """특수 카드를 사용합니다. (코스트 차감)

        반환값: (성공 여부, 메시지, 사용된 SpecialCard)
        """
        card = self.get_special_card(card_name)
        if not card:
            return False, f"보유 중인 특수 카드 '{card_name}'이(가) 없습니다.", None

        if self.current_cost < card.cost:
            return False, "코스트가 부족합니다.", card

        self.current_cost -= float(card.cost)
        return True, "사용 성공", card

    def use_special_card_at(self, index: int) -> tuple[bool, str, SpecialCard | None]:
        """인덱스 위치의 특수 카드를 사용합니다."""
        if index < 0 or index >= len(self.special_cards):
            return False, "지정한 특수 카드가 없습니다.", None
        card = self.special_cards[index]

        if self.current_cost < card.cost:
            return False, "코스트가 부족합니다.", card

        self.current_cost -= float(card.cost)
        return True, "사용 성공", card

    def update_special_card_info(
        self,
        card_name: str,
        cost: int | None = None,
        description: str | None = None,
    ) -> bool:
        """특수 카드의 정보(코스트, 설명)를 수정합니다."""
        card = self.get_special_card(card_name)
        if not card:
            return False

        if cost is not None:
            card.cost = max(0, int(cost))
            card.base_cost = card.cost
        if description is not None:
            card.description = description.strip()
        return True

    def clear(self) -> None:
        """덱과 패, 특수 카드를 모두 비웁니다."""
        self.original_cards.clear()
        self.cards.clear()
        self.hand.clear()
        self.special_cards.clear()

