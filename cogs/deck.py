from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from deck import deck_manager
from utils.logger import setup_logger

logger = setup_logger("DeckCog")


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
            await interaction.response.send_message(
                f"[안내] {interaction.user.mention}님은 이미 덱을 보유하고 있습니다. (덱: {len(deck.cards)}/9장, 패: {len(deck.hand)}/9장)",
                ephemeral=True,
            )
            return

        deck_manager.create_deck(user_id)
        logger.info(f"덱 생성: {interaction.user.name} ({user_id})")
        await interaction.response.send_message(
            f"{interaction.user.mention}님의 새로운 덱이 생성되었습니다. '/카드추가' 명령어로 카드를 넣어보세요."
        )

    @app_commands.command(name="카드추가", description="덱에 새로운 카드를 추가합니다. (최대 9장)")
    @app_commands.describe(카드이름="추가할 카드의 이름")
    async def add_card(self, interaction: discord.Interaction, 카드이름: str):
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
            f"'{cleaned_card}' 카드가 덱에 추가되었습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장)"
        )

    @app_commands.command(name="카드뽑기", description="덱에서 카드를 뽑아 패로 가져옵니다. (패 최대 9장)")
    @app_commands.describe(장수="뽑을 카드의 장수 (기본값: 1)")
    async def draw_card(self, interaction: discord.Interaction, 장수: int = 1):
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

        if not deck.cards:
            await interaction.response.send_message(
                "[안내] 덱에 남은 카드가 없습니다. '/카드추가'로 카드를 넣거나 '/덱초기화'를 이용해주세요.",
                ephemeral=True,
            )
            return

        drawn = deck.draw_card(장수)
        drawn_str = ", ".join(f"[{c}]" for c in drawn)
        logger.info(f"카드 드로우: {interaction.user.name} -> {len(drawn)}장")

        msg = f"{interaction.user.mention}님이 카드를 {len(drawn)}장 뽑았습니다.\n"
        msg += f"- 뽑은 카드: {drawn_str}\n"
        msg += f"- 남은 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장 | 현재 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장"

        if len(drawn) < 장수:
            msg += f"\n(제한으로 인해 {len(drawn)}장만 뽑혔습니다.)"

        await interaction.response.send_message(msg)

    @app_commands.command(name="패확인", description="현재 내 손(패)에 있는 카드 목록을 확인합니다.")
    async def check_hand(self, interaction: discord.Interaction):
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
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="카드사용", description="패에서 카드를 1장 사용합니다.")
    @app_commands.describe(카드이름="사용할 카드의 이름 (자동완성 지원)")
    @app_commands.autocomplete(카드이름=hand_card_autocomplete)
    async def use_card(self, interaction: discord.Interaction, 카드이름: str):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck:
            await interaction.response.send_message(
                "[안내] 먼저 '/덱생성' 명령어로 덱을 생성해주세요.", ephemeral=True
            )
            return

        if deck.use_card(카드이름):
            logger.info(f"카드 사용: {interaction.user.name} -> '{카드이름}'")
            await interaction.response.send_message(
                f"{interaction.user.mention}님이 패에서 '{카드이름}' 카드를 사용했습니다. (남은 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장)"
            )
        else:
            await interaction.response.send_message(
                f"[오류] 패에 '{카드이름}' 카드가 없습니다. '/패확인'으로 현재 패를 확인해보세요.",
                ephemeral=True,
            )

    @app_commands.command(name="덱확인", description="현재 내 덱에 남은 카드 목록과 장수를 확인합니다.")
    async def check_deck(self, interaction: discord.Interaction):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.cards:
            await interaction.response.send_message(
                "[안내] 덱이 비어 있습니다. '/카드추가'로 카드를 넣어주세요.",
                ephemeral=True,
            )
            return

        cards = deck.current_deck()
        display_limit = 20
        deck_display = ", ".join(f"[{c}]" for c in cards[:display_limit])
        if len(cards) > display_limit:
            deck_display += f" 외 {len(cards) - display_limit}장..."

        embed = discord.Embed(
            title=f"{interaction.user.display_name}님의 덱 정보",
            color=discord.Color.green(),
        )
        embed.add_field(name="남은 카드 수", value=f"{len(cards)}/{deck.MAX_DECK_SIZE}장", inline=True)
        embed.add_field(name="현재 패 카드 수", value=f"{len(deck.hand)}/{deck.MAX_HAND_SIZE}장", inline=True)
        embed.add_field(name="덱 카드 목록", value=deck_display, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="덱셔플", description="현재 덱에 남아있는 카드를 무작위로 섞습니다.")
    async def shuffle_deck(self, interaction: discord.Interaction):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck or not deck.cards:
            await interaction.response.send_message(
                "[안내] 덱에 섞을 카드가 없습니다.", ephemeral=True
            )
            return

        deck.deck_shuffle()
        logger.info(f"덱 셔플: {interaction.user.name}")
        await interaction.response.send_message(
            f"덱을 무작위로 섞었습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장)"
        )

    @app_commands.command(name="덱초기화", description="패의 카드를 모두 덱으로 회수하고 섞습니다.")
    async def reset_deck(self, interaction: discord.Interaction):
        deck = deck_manager.get_deck(interaction.user.id)
        if not deck:
            await interaction.response.send_message(
                "[안내] 생성된 덱이 없습니다.", ephemeral=True
            )
            return

        deck.reset_deck()
        logger.info(f"덱 초기화: {interaction.user.name}")
        await interaction.response.send_message(
            f"패에 있던 카드를 모두 덱으로 회수하고 섞었습니다. (현재 덱: {len(deck.cards)}/{deck.MAX_DECK_SIZE}장, 패: {len(deck.hand)}/{deck.MAX_HAND_SIZE}장)"
        )


async def setup(bot: commands.Bot) -> None:
    """Cog를 봇에 등록합니다."""
    await bot.add_cog(DeckCog(bot))
