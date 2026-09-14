from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from deck import Card, deck_manager, format_cost, parse_card_input
from utils.logger import setup_logger

logger = setup_logger("DeckCog")


class ConfirmView(discord.ui.View):
    """실행 전 사용자 확인을 받기 위한 버튼 View."""

    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value: bool | None = None

    def disable_buttons(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "[오류] 명령어를 입력한 사용자만 선택할 수 있습니다.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="확인", style=discord.ButtonStyle.primary)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.disable_buttons()
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.disable_buttons()
        self.stop()
        await interaction.response.edit_message(
            content="[안내] 작업이 취소되었습니다.", view=self
        )

    async def on_timeout(self):
        self.disable_buttons()


class DeckCog(commands.Cog, name="카드 덱"):
    """카드 덱 및 패, 코스트 관리를 위한 디스코드 슬래시 명령어 모음."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- 자동완성 (Autocomplete) ---
    async def hand_card_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """사용자의 현재 패에 있는 카드를 자동완성 목록으로 제공합니다."""
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.hand:
            return []

        unique_cards: dict[str, int] = {}
        for card in deck.hand:
            if card.name not in unique_cards:
                unique_cards[card.name] = card.cost

        choices = []
        for name, cost in unique_cards.items():
            if current.lower() in name.lower():
                choices.append(
                    app_commands.Choice(name=f"{name} (코스트 {cost})", value=name)
                )

        return choices[:25]

    async def all_deck_cards_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """사용자의 등록된 원본 덱에 있는 모든 카드를 자동완성 목록으로 제공합니다."""
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.original_cards:
            return []

        unique_names: list[str] = []
        for card in deck.original_cards:
            if card.name not in unique_names:
                unique_names.append(card.name)

        choices = []
        for name in unique_names:
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=name))

        return choices[:25]

    # --- 슬래시 명령어 ---

    @app_commands.command(name="덱생성", description="새로운 카드 덱을 생성합니다.")
    async def create_deck(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        deck = deck_manager.get_deck(user_id)
        if deck:
            prompt = (
                f"[확인] {interaction.user.mention}님은 이미 덱을 보유하고 있습니다. "
                f"(현재 덱: {len(deck.cards)}/9장, 패: {len(deck.hand)}/9장, 코스트: {format_cost(deck.current_cost)}/{deck.max_cost})\n"
                "기존 덱을 삭제하고 새로운 덱을 생성하시겠습니까?"
            )
        else:
            prompt = f"[확인] {interaction.user.mention}님의 새로운 카드 덱을 생성하시겠습니까?"

        view = ConfirmView(author_id=user_id)
        await interaction.response.send_message(prompt, view=view, ephemeral=True)
        await view.wait()

        if view.value is True:
            deck_manager.create_deck(user_id)
            logger.info(f"덱 생성: {interaction.user.name} ({user_id})")
            await interaction.edit_original_response(
                content=f"{interaction.user.mention}님의 새로운 덱이 생성되었습니다. '/카드추가' 명령어로 카드를 넣어보세요.",
                view=view,
            )
        elif view.value is None:
            await interaction.edit_original_response(
                content="[안내] 응답 시간이 초과되어 덱 생성이 취소되었습니다.",
                view=view,
            )

    @app_commands.command(
        name="카드추가",
        description="덱에 새로운 카드를 추가합니다. (쉼표로 여러 개 매칭 가능, 최대 9장)",
    )
    @app_commands.describe(
        이름="추가할 카드 이름 목록 (쉼표 구분, 예: 불꽃, 얼음, 번개)",
        코스트="각 카드의 소모 코스트 목록 (쉼표 구분, 예: 1, 2, 3 / 생략 시 0)",
        설명="각 카드의 설명 목록 (쉼표 구분, 예: 불꽃 발사, 얼림 / 생략 시 없음)",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False, 공개)",
    )
    async def add_card(
        self,
        interaction: discord.Interaction,
        이름: str,
        코스트: str = "",
        설명: str = "",
        비밀: bool = False,
    ):
        deck = deck_manager.get_or_create_deck(interaction.user.id)
        raw_names = [n.strip() for n in 이름.split(",") if n.strip()]

        if not raw_names:
            await interaction.response.send_message(
                "[오류] 추가할 카드 이름을 최소 1개 이상 입력해주세요.",
                ephemeral=True,
            )
            return

        available_slots = deck.MAX_DECK_SIZE - len(deck.original_cards)
        if available_slots <= 0:
            await interaction.response.send_message(
                f"[오류] 덱이 가득 찼습니다. (최대 {deck.MAX_DECK_SIZE}장) 더 이상 카드를 추가할 수 없습니다.",
                ephemeral=True,
            )
            return

        raw_costs = [c.strip() for c in 코스트.split(",") if c.strip()] if 코스트 else []
        raw_descs = [d.strip() for d in 설명.split(",") if d.strip()] if 설명 else []

        # 이름 개수 N을 기준으로 코스트와 설명 정렬 및 보정
        n_cards = len(raw_names)
        parsed_costs: list[int] = []
        for i in range(n_cards):
            if i < len(raw_costs):
                try:
                    c_val = int(raw_costs[i])
                    parsed_costs.append(max(0, c_val))
                except ValueError:
                    parsed_costs.append(0)
            else:
                parsed_costs.append(0)

        parsed_descs: list[str] = []
        for i in range(n_cards):
            if i < len(raw_descs):
                parsed_descs.append(raw_descs[i])
            else:
                parsed_descs.append("")

        added_cards: list[Card] = []
        for i in range(min(n_cards, available_slots)):
            c_name = raw_names[i]
            c_cost = parsed_costs[i]
            c_desc = parsed_descs[i]
            deck.add_card(c_name, c_cost, c_desc)
            added_cards.append(Card(c_name, c_cost, c_desc))

        logger.info(f"카드 추가: {interaction.user.name} -> {added_cards}")

        if len(raw_names) == 1 and len(added_cards) == 1:
            c = added_cards[0]
            desc_info = f" | 설명: {c.description}" if c.description else ""
            msg = f"'{c.name}' (코스트 {c.cost}{desc_info}) 카드가 덱에 추가되었습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장)"
        else:
            lines = []
            for c in added_cards:
                desc_info = f" (설명: {c.description})" if c.description else ""
                lines.append(f"[{c.name}] 코스트 {c.cost}{desc_info}")
            added_str = ", ".join(lines)
            msg = f"카드 {len(added_cards)}장이 덱에 추가되었습니다:\n{added_str}\n- 현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장"
            if len(added_cards) < len(raw_names):
                msg += f"\n(덱 최대 매수 {deck.MAX_DECK_SIZE}장 제한으로 인해 {len(raw_names) - len(added_cards)}장은 추가되지 않았습니다.)"

        await interaction.response.send_message(msg, ephemeral=비밀)

    @app_commands.command(name="카드뽑기", description="덱에서 카드를 뽑아 패로 가져옵니다. (패 최대 9장)")
    @app_commands.describe(
        장수="뽑을 카드의 장수 (기본값: 1)",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False, 공개)",
    )
    async def draw_card(
        self, interaction: discord.Interaction, 장수: int = 1, 비밀: bool = False
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck:
            await interaction.response.send_message(
                "[안내] 먼저 '/덱생성' 명령어로 덱을 생성해주세요.", ephemeral=True
            )
            return

        if 장수 <= 0:
            await interaction.response.send_message(
                "[오류] 카드는 1장 이상 뽑아야 합니다.", ephemeral=True
            )
            return

        if deck.is_hand_full():
            await interaction.response.send_message(
                f"[오류] 패가 가득 찼습니다. (최대 {deck.MAX_HAND_SIZE}장) 더 이상 카드를 뽑을 수 없습니다.",
                ephemeral=True,
            )
            return

        if not deck.cards and not deck.original_cards:
            await interaction.response.send_message(
                "[안내] 덱에 등록된 카드가 없습니다. 먼저 '/카드추가'로 카드를 등록해주세요.",
                ephemeral=True,
            )
            return

        drawn, refilled = deck.draw_card(장수)
        drawn_str = ", ".join(f"[{c.name}] (코스트 {c.cost})" for c in drawn)
        logger.info(f"카드 드로우: {interaction.user.name} -> {len(drawn)}장 (초기화 여부: {refilled})")

        msg = f"{interaction.user.mention}님이 카드를 {len(drawn)}장 뽑았습니다.\n"
        msg += f"- 뽑은 카드: {drawn_str}\n"
        msg += (
            f"- 남은 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장 | "
            f"현재 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장 | "
            f"보유 코스트: {format_cost(deck.current_cost)}/{deck.max_cost}"
        )

        if refilled:
            msg += "\n[안내] 덱이 고갈되어 패는 그대로 두고 덱을 초기화하여 다시 뽑았습니다."

        if len(drawn) < 장수:
            msg += f"\n(패 제한으로 인해 {len(drawn)}장만 뽑혔습니다.)"

        await interaction.response.send_message(msg, ephemeral=비밀)

    @app_commands.command(name="패확인", description="현재 내 손(패)에 있는 카드 목록과 코스트를 확인합니다.")
    @app_commands.describe(비밀="나에게만 패를 표시할지 여부 (기본값: False, 공개)")
    async def check_hand(
        self, interaction: discord.Interaction, 비밀: bool = False
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck:
            await interaction.response.send_message(
                "[안내] 먼저 '/덱생성' 명령어로 덱을 생성해주세요.", ephemeral=True
            )
            return

        hand_cards = deck.current_hand()
        if not hand_cards:
            hand_display = "(패가 비어 있습니다. '/카드뽑기'로 카드를 뽑아보세요.)"
        else:
            hand_display = "\n".join(
                f"{i + 1}. [{card.name}] (코스트 {card.cost})"
                for i, card in enumerate(hand_cards)
            )

        embed = discord.Embed(
            title=f"{interaction.user.display_name}님의 패 정보 ({len(hand_cards)}/{deck.MAX_HAND_SIZE}장)",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="보유 코스트",
            value=f"{format_cost(deck.current_cost)} / {deck.max_cost}",
            inline=False,
        )
        embed.add_field(
            name="패 목록",
            value=hand_display,
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=비밀)

    @app_commands.command(name="카드사용", description="패에서 카드를 1장 사용합니다. (코스트 자동 차감)")
    @app_commands.describe(카드이름="사용할 카드의 이름 (자동완성 지원)")
    @app_commands.autocomplete(카드이름=hand_card_autocomplete)
    async def use_card(
        self, interaction: discord.Interaction, 카드이름: str
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck:
            await interaction.response.send_message(
                "[안내] 먼저 '/덱생성' 명령어로 덱을 생성해주세요.", ephemeral=True
            )
            return

        success, reason, card = deck.use_card(카드이름)
        if success and card:
            logger.info(f"카드 사용: {interaction.user.name} -> '{card.name}' (코스트 {card.cost})")
            await interaction.response.send_message(
                f"{interaction.user.mention}님이 패에서 '[{card.name}]' 카드를 사용했습니다. "
                f"(소모 코스트: {card.cost}, 잔여 코스트: {format_cost(deck.current_cost)}/{deck.max_cost}, 남은 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장)",
                ephemeral=False,
            )
        else:
            if reason == "코스트가 부족합니다." and card:
                await interaction.response.send_message(
                    f"[오류] 코스트가 부족합니다. (필요: {card.cost}, 보유: {format_cost(deck.current_cost)}/{deck.max_cost})",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    f"[오류] 패에 '{카드이름}' 카드가 없습니다. '/패확인'으로 현재 패를 확인해보세요.",
                    ephemeral=True,
                )

    @app_commands.command(name="덱확인", description="현재 내 덱에 남은 카드 목록과 장수를 확인합니다.")
    @app_commands.describe(비밀="나에게만 덱 정보를 표시할지 여부 (기본값: False, 공개)")
    async def check_deck(
        self, interaction: discord.Interaction, 비밀: bool = False
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.original_cards:
            await interaction.response.send_message(
                "[안내] 덱이 비어 있습니다. 먼저 '/카드추가'로 카드를 넣어주세요.",
                ephemeral=True,
            )
            return

        cards = deck.current_deck()
        orig_cards = deck.registered_deck()
        display_limit = 20
        deck_display = (
            ", ".join(f"[{c.name}] (코스트 {c.cost})" for c in cards[:display_limit])
            if cards
            else "(고갈됨 - 뽑기 시 자동 초기화)"
        )
        if len(cards) > display_limit:
            deck_display += f" 외 {len(cards) - display_limit}장..."

        orig_display = ", ".join(
            f"[{c.name}] (코스트 {c.base_cost})" for c in orig_cards[:display_limit]
        )
        if len(orig_cards) > display_limit:
            orig_display += f" 외 {len(orig_cards) - display_limit}장..."

        embed = discord.Embed(
            title=f"{interaction.user.display_name}님의 덱 정보",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="보유 코스트",
            value=f"{format_cost(deck.current_cost)} / {deck.max_cost}",
            inline=True,
        )
        embed.add_field(
            name="남은 덱 카드 수", value=f"{len(cards)}/{deck.MAX_DECK_SIZE}장", inline=True
        )
        embed.add_field(
            name="현재 패 카드 수", value=f"{len(deck.hand)}/{deck.MAX_HAND_SIZE}장", inline=True
        )
        embed.add_field(name="등록된 원본 덱", value=f"{orig_display} (총 {len(orig_cards)}장)", inline=False)
        embed.add_field(name="현재 남은 덱 카드", value=deck_display, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=비밀)

    @app_commands.command(name="덱셔플", description="현재 덱에 남아있는 카드를 무작위로 섞습니다.")
    @app_commands.describe(비밀="나에게만 결과를 표시할지 여부 (기본값: False, 공개)")
    async def shuffle_deck(
        self, interaction: discord.Interaction, 비밀: bool = False
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.cards:
            await interaction.response.send_message(
                "[안내] 덱에 섞을 카드가 없습니다.", ephemeral=True
            )
            return

        deck.deck_shuffle()
        logger.info(f"덱 셔플: {interaction.user.name}")
        await interaction.response.send_message(
            f"덱을 무작위로 섞었습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장)",
            ephemeral=비밀,
        )

    @app_commands.command(name="덱초기화", description="내 패를 모두 비우고 덱과 코스트를 처음 상태로 되돌립니다.")
    async def reset_deck(self, interaction: discord.Interaction):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.original_cards:
            await interaction.response.send_message(
                "[안내] 생성되거나 등록된 덱이 없습니다.", ephemeral=True
            )
            return

        prompt = (
            f"[확인] 정말 덱과 패를 초기화하시겠습니까?\n"
            f"- 현재 패({len(deck.hand)}장)를 모두 비우고 덱({len(deck.original_cards)}장)을 원상복구합니다.\n"
            f"- 코스트가 기본 최대치({deck.base_max_cost})로 충전되며 전투 중 증가분이 초기화됩니다."
        )
        view = ConfirmView(author_id=interaction.user.id)
        await interaction.response.send_message(prompt, view=view, ephemeral=True)
        await view.wait()

        if view.value is True:
            deck.reset_deck_and_hand()
            logger.info(f"덱과 패 초기화: {interaction.user.name}")
            await interaction.edit_original_response(
                content="[안내] 덱과 패 초기화가 완료되었습니다.",
                view=view,
            )
            public_msg = (
                f"{interaction.user.mention}님이 덱과 패를 초기화했습니다. "
                f"패를 모두 비우고 덱을 처음 상태로 되돌렸습니다. "
                f"(현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장, 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장, 코스트: {format_cost(deck.current_cost)}/{deck.max_cost})"
            )
            await interaction.followup.send(public_msg, ephemeral=False)
        elif view.value is None:
            await interaction.edit_original_response(
                content="[안내] 응답 시간이 초과되어 초기화가 취소되었습니다.",
                view=view,
            )

    @app_commands.command(name="덱리필", description="패는 그대로 유지하고 덱만 원래 등록된 카드로 다시 채웁니다.")
    async def refill_deck(self, interaction: discord.Interaction):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.original_cards:
            await interaction.response.send_message(
                "[안내] 생성되거나 등록된 덱이 없습니다.", ephemeral=True
            )
            return

        deck.refill_deck()
        logger.info(f"덱 리필: {interaction.user.name}")
        await interaction.response.send_message(
            f"{interaction.user.mention}님이 패는 그대로 두고 덱만 원래 등록된 카드로 다시 채웠습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장, 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장)",
            ephemeral=False,
        )

    # --- 코스트 관리 슬래시 명령어 ---

    @app_commands.command(name="코스트설정", description="기본 최대 코스트를 설정합니다. (자연수, 1 이상)")
    @app_commands.describe(최댓값="설정할 기본 최대 코스트 (자연수, 1 이상)")
    async def set_cost(self, interaction: discord.Interaction, 최댓값: int):
        deck = deck_manager.get_or_create_deck(interaction.user.id)
        if 최댓값 < 1:
            await interaction.response.send_message(
                "[오류] 최대 코스트는 1 이상의 자연수여야 합니다.", ephemeral=True
            )
            return

        deck.set_base_max_cost(최댓값)
        logger.info(f"기본 최대 코스트 설정: {interaction.user.name} -> {최댓값}")
        await interaction.response.send_message(
            f"{interaction.user.mention}님의 기본 최대 코스트가 {최댓값}(으)로 설정되었습니다. (현재 코스트: {format_cost(deck.current_cost)}/{deck.max_cost})",
            ephemeral=False,
        )

    @app_commands.command(name="코스트회복", description="코스트를 지정한 수치만큼 회복합니다. (음이 아닌 유리수)")
    @app_commands.describe(
        수치="회복할 코스트 수치 (양의 유리수/소수 가능, 기본값: 1.0)",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False, 공개)",
    )
    async def restore_cost(
        self, interaction: discord.Interaction, 수치: float = 1.0, 비밀: bool = False
    ):
        deck = deck_manager.get_or_create_deck(interaction.user.id)
        if 수치 <= 0:
            await interaction.response.send_message(
                "[오류] 회복 수치는 0보다 커야 합니다.", ephemeral=True
            )
            return

        restored = deck.restore_cost(수치)
        logger.info(f"코스트 회복: {interaction.user.name} -> {수치}")
        await interaction.response.send_message(
            f"{interaction.user.mention}님의 코스트가 {format_cost(restored)} 회복되었습니다. (현재 코스트: {format_cost(deck.current_cost)}/{deck.max_cost})",
            ephemeral=비밀,
        )

    @app_commands.command(name="최대코스트증가", description="이번 전투 동안 최대 코스트를 추가로 증가시킵니다. (자연수)")
    @app_commands.describe(증가량="이번 전투 동안 추가할 최대 코스트 (자연수, 1 이상)")
    async def add_max_cost(self, interaction: discord.Interaction, 증가량: int = 1):
        deck = deck_manager.get_or_create_deck(interaction.user.id)
        if 증가량 < 1:
            await interaction.response.send_message(
                "[오류] 증가량은 1 이상의 자연수여야 합니다.", ephemeral=True
            )
            return

        deck.add_max_cost(증가량)
        logger.info(f"전투 중 최대 코스트 증가: {interaction.user.name} -> +{증가량}")
        await interaction.response.send_message(
            f"{interaction.user.mention}님의 이번 전투 최대 코스트가 {증가량} 증가했습니다. (현재 최대 코스트: {deck.max_cost}, 보유 코스트: {format_cost(deck.current_cost)})",
            ephemeral=False,
        )

    @app_commands.command(name="카드코스트변경", description="패에 머무는 동안 패에 있는 특정 카드의 소모 코스트를 변경합니다.")
    @app_commands.describe(
        카드이름="패에서 변경할 카드의 이름",
        변경할코스트="새로 지정할 소모 코스트 (음이 아닌 정수, 0 이상)",
    )
    @app_commands.autocomplete(카드이름=hand_card_autocomplete)
    async def change_card_cost(
        self, interaction: discord.Interaction, 카드이름: str, 변경할코스트: int
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.hand:
            await interaction.response.send_message(
                "[안내] 현재 패가 비어 있습니다.", ephemeral=True
            )
            return

        if 변경할코스트 < 0:
            await interaction.response.send_message(
                "[오류] 카드 소모 코스트는 0 이상의 정수여야 합니다.", ephemeral=True
            )
            return

        if deck.modify_hand_card_cost(카드이름, 변경할코스트):
            logger.info(f"패 카드 코스트 변경: {interaction.user.name} -> {카드이름} : {변경할코스트}")
            await interaction.response.send_message(
                f"{interaction.user.mention}님의 패에 있는 '[{카드이름}]' 카드의 코스트가 이번 패에 머무는 동안 {변경할코스트}(으)로 변경되었습니다.",
                ephemeral=False,
            )
        else:
            await interaction.response.send_message(
                f"[오류] 패에 '{카드이름}' 카드가 없습니다. '/패확인'으로 현재 패를 확인해보세요.",
                ephemeral=True,
            )

    @app_commands.command(name="카드정보", description="특정 카드의 소모 코스트와 상세 설명을 확인합니다.")
    @app_commands.describe(
        카드이름="정보를 확인할 카드의 이름",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False, 공개)",
    )
    @app_commands.autocomplete(카드이름=all_deck_cards_autocomplete)
    async def view_card_info(
        self, interaction: discord.Interaction, 카드이름: str, 비밀: bool = False
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck:
            await interaction.response.send_message(
                "[안내] 먼저 '/덱생성' 명령어로 덱을 생성해주세요.", ephemeral=True
            )
            return

        card = deck.get_card(카드이름)
        if not card:
            await interaction.response.send_message(
                f"[오류] 덱에 '{카드이름}' 카드가 등록되어 있지 않습니다.", ephemeral=True
            )
            return

        desc_text = card.description if card.description else "(등록된 설명이 없습니다.)"
        embed = discord.Embed(
            title=f"카드 정보: [{card.name}]",
            color=discord.Color.purple(),
        )
        embed.add_field(name="소모 코스트", value=f"{card.cost} (기본: {card.base_cost})", inline=True)
        embed.add_field(name="카드 설명", value=desc_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=비밀)

    @app_commands.command(name="카드정보설정", description="이미 등록된 카드의 설명이나 코스트를 추가/수정합니다.")
    @app_commands.describe(
        카드이름="정보를 수정할 카드의 이름",
        설명="새로 지정할 카드 설명 (생략 시 기존 설명 유지)",
        코스트="새로 지정할 기본 소모 코스트 (음이 아닌 정수, 생략 시 기존 코스트 유지)",
    )
    @app_commands.autocomplete(카드이름=all_deck_cards_autocomplete)
    async def update_card_info(
        self,
        interaction: discord.Interaction,
        카드이름: str,
        설명: str | None = None,
        코스트: int | None = None,
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.original_cards:
            await interaction.response.send_message(
                "[안내] 등록된 덱 카드가 없습니다. 먼저 '/카드추가'로 카드를 넣어주세요.",
                ephemeral=True,
            )
            return

        if 설명 is None and 코스트 is None:
            await interaction.response.send_message(
                "[오류] 설명이나 코스트 중 최소 하나는 입력해야 합니다.", ephemeral=True
            )
            return

        if 코스트 is not None and 코스트 < 0:
            await interaction.response.send_message(
                "[오류] 코스트는 0 이상의 정수여야 합니다.", ephemeral=True
            )
            return

        updated = deck.update_card_info(카드이름, cost=코스트, description=설명)
        if updated:
            card = deck.get_card(카드이름)
            logger.info(f"카드 정보 수정: {interaction.user.name} -> {카드이름}")
            desc_str = f" | 설명: {card.description}" if card and card.description else ""
            cost_str = f" | 코스트: {card.cost}" if card else ""
            await interaction.response.send_message(
                f"{interaction.user.mention}님의 '[{카드이름}]' 카드 정보가 수정되었습니다.{cost_str}{desc_str}",
                ephemeral=False,
            )
        else:
            await interaction.response.send_message(
                f"[오류] 덱에 '{카드이름}' 카드가 등록되어 있지 않습니다.", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """Cog를 봇에 등록합니다."""
    await bot.add_cog(DeckCog(bot))


