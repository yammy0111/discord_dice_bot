# config.py

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
GUILD_ID = os.getenv("GUILD_ID", None)  # 특정 길드 즉시 동기화용 (테스트용)
