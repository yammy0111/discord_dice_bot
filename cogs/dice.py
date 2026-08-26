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

    async def _execute_roll(
        self,
        interaction: discord.Interaction,
        expression: str,
        detail: bool = False,
        secret: bool = False,
    ) -> None:
        """주사위 굴리기 내부 헬퍼 메서드"""
        try:
            results = self.engine.roll_multiple(expression)
            embed = build_dice_embed(results, interaction.user, show_detail=detail)
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
        name="roll",
        description="주사위 표현식을 평가하여 결과를 굴립니다. (예: 1d20+5, 2d6+3)",
    )
    @app_commands.describe(
        expression="굴릴 주사위 수식 (예: 1d20+5, 2d6+3, 1d100)",
        detail="상세 정보(개별 주사위 눈금, 치환 수식, 풀이 과정) 표시 여부 (기본값: False)",
        secret="나에게만 결과를 표시할지 여부 (기본값: False)",
    )
    async def roll(
        self,
        interaction: discord.Interaction,
        expression: str,
        detail: bool = False,
        secret: bool = False,
    ) -> None:
        """영문 주사위 굴리기 슬래시 커맨드"""
        await self._execute_roll(
            interaction,
            expression=expression,
            detail=detail,
            secret=secret,
        )

    @app_commands.command(
        name="주사위",
        description="주사위 표현식을 평가하여 결과를 굴립니다. (한글 명령어)",
    )
    @app_commands.describe(
        수식="굴릴 주사위 수식 (예: 1d20+5, 2d6+3, 1d100)",
        상세="상세 정보(개별 주사위 눈금, 치환 수식, 풀이 과정) 표시 여부 (기본값: False)",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False)",
    )
    async def roll_kr(
        self,
        interaction: discord.Interaction,
        수식: str,
        상세: bool = False,
        비밀: bool = False,
    ) -> None:
        """한글 주사위 굴리기 슬래시 커맨드"""
        await self._execute_roll(
            interaction,
            expression=수식,
            detail=상세,
            secret=비밀,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiceCog(bot))
