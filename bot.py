# bot.py

import os
import sys
import asyncio
import discord
from discord.ext import commands

import config
from utils.logger import setup_logger

logger = setup_logger("DiceBot")


class DiceBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        """봇 시작 시 Cog 로드 및 Slash Command 동기화"""
        logger.info("Cog 로드 중...")
        await self.load_extension("cogs.dice")

        logger.info("슬래시 커맨드 동기화 중...")
        if config.GUILD_ID:
            guild = discord.Object(id=int(config.GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"테스트 길드({config.GUILD_ID})에 {len(synced)}개 커맨드 동기화 완료.")
        else:
            synced = await self.tree.sync()
            logger.info(f"글로벌 {len(synced)}개 커맨드 동기화 완료.")

    async def on_ready(self) -> None:
        logger.info(f"로그인 성공: {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Game(name="/roll 또는 /주사위")
        )


def main() -> None:
    token = config.DISCORD_BOT_TOKEN
    if not token:
        logger.error(
            "DISCORD_BOT_TOKEN 환경변수가 설정되지 않았습니다.\n"
            ".env 파일에 DISCORD_BOT_TOKEN=YOUR_TOKEN 형식으로 입력해주세요."
        )
        return

    bot = DiceBot()
    bot.run(token)


if __name__ == "__main__":
    main()