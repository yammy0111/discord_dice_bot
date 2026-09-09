from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from deck import deck_manager
from utils.logger import setup_logger

logger = setup_logger("DeckCog")


class ConfirmView(discord.ui.View):
    """실행 전 사용자 확인을 받기 위한 버튼 View."""

    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value: bool | None = None

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
        for item in self.children:
            item.disabled = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        for item in self.children:
            item.disabled = True
        self.stop()
        await interaction.response.edit_message(
            content="[안내] 작업이 취소되었습니다.", view=self
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True


class DeckCog(commands.Cog, name="카드 덱"):
    """카드 덱 및 패 관리를 위한 디스코드 슬래시 명령어 모음."""

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

        unique_cards = sorted(list(set(deck.hand)))
        matching_cards = [
            card for card in unique_cards if current.lower() in card.lower()
        ]

        return [
            app_commands.Choice(name=card, value=card)
            for card in matching_cards[:25]
        ]

    # --- 슬래시 명령어 ---

    @app_commands.command(name="덱생성", description="새로운 카드 덱을 생성합니다.")
    async def create_deck(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if deck_manager.has_deck(user_id):
            deck = deck_manager.get_deck(user_id)
            prompt = (
                f"[확인] {interaction.user.mention}님은 이미 덱을 보유하고 있습니다. "
                f"(현재 덱: {len(deck.cards)}/9장, 패: {len(deck.hand)}/9장)\n"
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

    @app_commands.command(name="카드추가", description="덱에 새로운 카드를 추가합니다. (최대 9장)")
    @app_commands.describe(
        카드이름="추가할 카드의 이름",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False, 공개)",
    )
    async def add_card(
        self, interaction: discord.Interaction, 카드이름: str, 비밀: bool = False
    ):
        deck = deck_manager.get_or_create_deck(interaction.user.id)
        cleaned_card = 카드이름.strip()

        if deck.is_deck_full():
            await interaction.response.send_message(
                f"[오류] 덱이 가득 찼습니다. (최대 {deck.MAX_DECK_SIZE}장) 더 이상 카드를 추가할 수 없습니다.",
                ephemeral=True,
            )
            return

        deck.add_card(cleaned_card)
        logger.info(f"카드 추가: {interaction.user.name} -> '{cleaned_card}'")
        await interaction.response.send_message(
            f"'{cleaned_card}' 카드가 덱에 추가되었습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장)",
            ephemeral=비밀,
        )

    @app_commands.command(name="카드뽑기", description="덱에서 카드를 뽑아 패로 가져옵니다. (패 최대 9장)")
    @app_commands.describe(
        장수="뽑을 카드의 장수 (기본값: 1)",
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
        drawn_str = ", ".join(f"[{c}]" for c in drawn)
        logger.info(f"카드 드로우: {interaction.user.name} -> {len(drawn)}장 (초기화 여부: {refilled})")

        msg = f"{interaction.user.mention}님이 카드를 {len(drawn)}장 뽑았습니다.\n"
        msg += f"- 뽑은 카드: {drawn_str}\n"
        msg += f"- 남은 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장 | 현재 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장"

        if refilled:
            msg += "\n[안내] 덱이 고갈되어 패는 그대로 두고 덱을 초기화하여 다시 뽑았습니다."

        if len(drawn) < 장수:
            msg += f"\n(패 제한으로 인해 {len(drawn)}장만 뽑혔습니다.)"

        await interaction.response.send_message(msg)

    @app_commands.command(name="패확인", description="현재 내 손(패)에 있는 카드 목록을 확인합니다.")
    @app_commands.describe(비밀="나에게만 패를 표시할지 여부 (기본값: False, 공개)")
    async def check_hand(
        self, interaction: discord.Interaction, 비밀: bool = False
    ):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.hand:
            await interaction.response.send_message(
                "[안내] 현재 패가 비어 있습니다. '/카드뽑기'로 카드를 뽑아보세요.",
                ephemeral=True,
            )
            return

        hand_cards = deck.current_hand()
        hand_display = "\n".join(
            f"{i + 1}. [{card}]" for i, card in enumerate(hand_cards)
        )

        embed = discord.Embed(
            title=f"{interaction.user.display_name}님의 패 ({len(hand_cards)}/{deck.MAX_HAND_SIZE}장)",
            description=hand_display,
            color=discord.Color.blue(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=비밀)

    @app_commands.command(name="카드사용", description="패에서 카드를 1장 사용합니다.")
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

        if deck.use_card(카드이름):
            logger.info(f"카드 사용: {interaction.user.name} -> '{카드이름}'")
            await interaction.response.send_message(
                f"{interaction.user.mention}님이 패에서 '{카드이름}' 카드를 사용했습니다. (남은 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장)",
                ephemeral=False,
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
        deck_display = ", ".join(f"[{c}]" for c in cards[:display_limit]) if cards else "(고갈됨 - 뽑기 시 자동 초기화)"
        if len(cards) > display_limit:
            deck_display += f" 외 {len(cards) - display_limit}장..."

        orig_display = ", ".join(f"[{c}]" for c in orig_cards[:display_limit])
        if len(orig_cards) > display_limit:
            orig_display += f" 외 {len(orig_cards) - display_limit}장..."

        embed = discord.Embed(
            title=f"{interaction.user.display_name}님의 덱 정보",
            color=discord.Color.green(),
        )
        embed.add_field(name="남은 덱 카드 수", value=f"{len(cards)}/{deck.MAX_DECK_SIZE}장", inline=True)
        embed.add_field(name="현재 패 카드 수", value=f"{len(deck.hand)}/{deck.MAX_HAND_SIZE}장", inline=True)
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

    @app_commands.command(name="덱초기화", description="내 패를 모두 비우고 덱을 처음 상태로 되돌립니다.")
    async def reset_deck(self, interaction: discord.Interaction):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.original_cards:
            await interaction.response.send_message(
                "[안내] 생성되거나 등록된 덱이 없습니다.", ephemeral=True
            )
            return

        prompt = (
            f"[확인] 정말 덱과 패를 초기화하시겠습니까?\n"
            f"현재 패({len(deck.hand)}장)를 모두 비우고 덱({len(deck.original_cards)}장)을 처음 상태로 되돌립니다."
        )
        view = ConfirmView(author_id=interaction.user.id)
        await interaction.response.send_message(prompt, view=view, ephemeral=True)
        await view.wait()

        if view.value is True:
            deck.reset_deck_and_hand()
            logger.info(f"덱과 패 초기화: {interaction.user.name}")
            # 버튼이 달린 확인 메시지는 비활성화 후 갱신
            await interaction.edit_original_response(
                content="[안내] 덱과 패 초기화가 완료되었습니다.",
                view=view,
            )
            # 모두가 볼 수 있도록 채널에 공개 알림 전송!
            public_msg = (
                f"{interaction.user.mention}님이 덱과 패를 초기화했습니다. "
                f"패를 모두 비우고 덱을 처음 상태로 되돌렸습니다. "
                f"(현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장, 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장)"
            )
            if interaction.channel:
                await interaction.channel.send(public_msg)
            else:
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


async def setup(bot: commands.Bot) -> None:
    """Cog를 봇에 등록합니다."""
    await bot.add_cog(DeckCog(bot))
