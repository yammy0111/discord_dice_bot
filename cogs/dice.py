# cogs/dice.py

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from dice.engine import DiceEngine
from dice.errors import DiceError
from dice.mackerel import roll_mackerel_dice
from utils.embeds import (
    build_dice_embed,
    build_derived_dice_embed,
    build_error_embed,
    build_mackerel_dice_embed,
)



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
            if ">" in expression:
                results = self.engine.roll_derived(expression)
                embed = build_derived_dice_embed(
                    results,
                    interaction.user,
                    show_detail=detail,
                )
            else:
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


    @app_commands.command(
        name="간고등어주사위",
        description="높은 수나 낮은 수가 더 잘 나오도록 확률이 곡선 형태로 보정된 주사위 표현식을 굴립니다.",
    )
    @app_commands.describe(
        보정="확률을 높일 방향 선택 (기본값: 높은 수)",
        수식="굴릴 주사위 수식 (예: 1d20+5, 2d6, 1d20 > +5)",
        상세="상세 정보(개별 주사위 눈금, 치환 수식, 풀이 과정) 표시 여부 (기본값: False)",
        비밀="나에게만 결과를 표시할지 여부 (기본값: False)",
    )
    @app_commands.choices(
        보정=[
            app_commands.Choice(name="높은 수 (큰 눈금일수록 확률 증가)", value="높은 수"),
            app_commands.Choice(name="낮은 수 (작은 눈금일수록 확률 증가)", value="낮은 수"),
        ]
    )
    async def mackerel_roll(
        self,
        interaction: discord.Interaction,
        보정: app_commands.Choice[str],
        수식: str = "1d20",
        상세: bool = False,
        비밀: bool = False,
    ) -> None:
        """간고등어 주사위 굴리기 슬래시 커맨드 (표현식 파싱 지원)"""
        try:
            bias_val = 보정.value
            extra_field = ("보정 방향", f"`{bias_val}` (곡선 보정)")

            if ">" in 수식:
                results = self.engine.roll_derived(수식, bias=bias_val)
                embed = build_derived_dice_embed(
                    results,
                    interaction.user,
                    show_detail=상세,
                    title="간고등어 주사위 파생 굴림 결과",
                )
                embed.insert_field_at(1, name=extra_field[0], value=extra_field[1], inline=False)
            else:
                results = self.engine.roll_multiple(수식, bias=bias_val)
                embed = build_dice_embed(
                    results,
                    interaction.user,
                    show_detail=상세,
                    title="간고등어 주사위 굴림 결과" if len(results) == 1 else f"간고등어 주사위 굴림 결과 (총 {len(results)}개)",
                    extra_field=extra_field if len(results) == 1 else None,
                )
                if len(results) > 1:
                    embed.insert_field_at(0, name=extra_field[0], value=extra_field[1], inline=False)

            await interaction.response.send_message(
                embed=embed,
                ephemeral=비밀,
            )
        except DiceError as e:
            embed = build_error_embed(str(e), expression=수식)
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        except Exception as e:
            embed = build_error_embed(
                f"간고등어 주사위 굴림 중 오류가 발생했습니다: {e}",
                expression=수식,
            )
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True,
            )



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DiceCog(bot))

