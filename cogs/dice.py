# cogs/dice.py

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from dice.engine import DiceEngine
from dice.errors import DiceError
from utils.embeds import build_dice_embed, build_error_embed


class DiceCog(commands.Cog):
    """주사위 명령어 Cog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.engine = DiceEngine()

    @app_commands.command(
        name="roll",
        description="주사위 표현식을 평가하여 결과를 굴립니다. 쉼표(,)로 구분해 여러 개 작성 가능합니다. (예: 1d20+5, 2d6+3)",
    )
    @app_commands.describe(
        expression="굴릴 주사위 수식 (예: 1d20+5, 2d6+3, 1d100)",
        secret="나에게만 결과를 표시할지 여부 (기본값: False)",
    )
    async def roll(
        self,
        interaction: discord.Interaction,
        expression: str,
        secret: bool = False,
    ) -> None:
        """주사위 굴리기 슬래시 커맨드 (쉼표 구분 다중 주사위 지원)"""
        try:
            results = self.engine.roll_multiple(expression)
            embed = build_dice_embed(results, interaction.user)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=secret,
            )
        except DiceError as e:
            embed = build_error_embed(str(e), expression=expression)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        except Exception as e:
            embed = build_error_embed(
                f"알 수 없는 오류가 발생했습니다: {e}",
                expression=expression,
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )

    @app_commands.command(
        name="주사위",
        description="주사위 표현식을 평가하여 결과를 굴립니다. 쉼표(,)로 구분해 여러 개 작성 가능합니다.",
    )
    @app_commands.describe(
        수식="굴릴 주사위 수식 (예: 1d20+5, 2d6+3, 1d100)",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False)",
    )
    async def roll_kr(
        self,
        interaction: discord.Interaction,
        수식: str,
        비밀: bool = False,
    ) -> None:
        """한글 주사위 굴리기 슬래시 커맨드"""
        await self.roll(interaction, expression=수식, secret=비밀)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiceCog(bot))
