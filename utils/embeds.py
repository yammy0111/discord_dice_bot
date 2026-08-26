# utils/embeds.py

from __future__ import annotations

import discord
from typing import TYPE_CHECKING, Union, List

if TYPE_CHECKING:
    from dice.engine import EngineResult


def build_dice_embed(
    results: Union[EngineResult, List[EngineResult]],
    user: discord.User | discord.Member,
) -> discord.Embed:
    """주사위 굴림 성공 결과를 시각화하는 Discord Embed 생성 (단일 및 다중 수식 지원)"""
    if not isinstance(results, list):
        results_list = [results]
    else:
        results_list = results

    if len(results_list) == 1:
        res = results_list[0]
        embed = discord.Embed(
            title="🎲 주사위 굴림 결과",
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="📝 요청 수식",
            value=f"`{res.expression}`",
            inline=False,
        )

        embed.add_field(
            name="🎯 최종 결과",
            value=f"**`{res.value}`**",
            inline=False,
        )

        # 개별 주사위 굴림 로그
        if res.roll_logs:
            log_lines = []
            for entry in res.roll_logs:
                rolls_str = ", ".join(map(str, entry.rolls))
                if len(rolls_str) > 100:
                    rolls_str = rolls_str[:97] + "..."
                log_lines.append(f"• `{entry.expression}`: [{rolls_str}] (합: {entry.total})")

            logs_text = "\n".join(log_lines)
            if len(logs_text) > 1000:
                logs_text = logs_text[:997] + "..."

            embed.add_field(
                name="📊 개별 주사위 결과",
                value=logs_text,
                inline=False,
            )

        # 치환된 수식
        if res.substituted_expression != res.expression:
            embed.add_field(
                name="🔢 치환 수식",
                value=f"`{res.substituted_expression}`",
                inline=False,
            )

        # 단계별 풀이과정
        if res.calculation_steps:
            steps_text = " → ".join(f"`{s}`" for s in res.calculation_steps)
            if len(steps_text) > 1000:
                steps_text = steps_text[:997] + "..."
            embed.add_field(
                name="🔍 풀이 과정",
                value=steps_text,
                inline=False,
            )

    else:
        embed = discord.Embed(
            title=f"🎲 주사위 굴림 결과 (총 {len(results_list)}개)",
            color=discord.Color.blurple(),
        )

        for idx, res in enumerate(results_list, 1):
            detail_parts = []
            if res.roll_logs:
                rolls_summary = "; ".join(
                    f"{entry.expression}: [{', '.join(map(str, entry.rolls))}]"
                    for entry in res.roll_logs
                )
                if len(rolls_summary) > 200:
                    rolls_summary = rolls_summary[:197] + "..."
                detail_parts.append(f"🎲 {rolls_summary}")

            if res.substituted_expression != res.expression:
                detail_parts.append(f"🔢 치환: `{res.substituted_expression}`")

            detail_parts.append(f"🎯 **결과: `{res.value}`**")

            field_val = "\n".join(detail_parts)
            embed.add_field(
                name=f"#{idx}  `{res.expression}`",
                value=field_val,
                inline=False,
            )

    embed.set_footer(
        text=f"요청자: {user.display_name}",
        icon_url=user.display_avatar.url if user.display_avatar else None,
    )
    return embed


def build_error_embed(
    error_message: str,
    expression: str | None = None,
) -> discord.Embed:
    """오류 발생시 디스코드 엠베드 생성"""
    embed = discord.Embed(
        title="⚠️ 주사위 굴림 오류",
        description=f"**{error_message}**",
        color=discord.Color.red(),
    )
    if expression:
        embed.add_field(
            name="입력된 수식",
            value=f"`{expression}`",
            inline=False,
        )
    return embed
