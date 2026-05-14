import os
from dotenv import load_dotenv

load_dotenv()

# ── Обязательно заполни в файле .env ──────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "")                  # Токен от @BotFather
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))  # Твой Telegram ID

# Ссылка-приглашение в закрытый канал/группу с курсом (одноразовая или постоянная)
COURSE_INVITE_LINK = os.getenv("COURSE_INVITE_LINK", "https://t.me/+XXXXXXXXXX")
COURSE_CHANNEL_NAME = os.getenv("COURSE_CHANNEL_NAME", "курс по SQL")
# ──────────────────────────────────────────────────────────────────────────────
