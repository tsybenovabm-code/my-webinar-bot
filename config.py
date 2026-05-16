import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))
COURSE_INVITE_LINK = os.getenv("COURSE_INVITE_LINK", "https://t.me/+XXXXXXXXXX")
COURSE_CHANNEL_NAME = os.getenv("COURSE_CHANNEL_NAME", "курс по SQL")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@канал")
