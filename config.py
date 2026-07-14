import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))
COURSE_INVITE_LINK = os.getenv("COURSE_INVITE_LINK", "https://t.me/+XXXXXXXXXX")
ALGO_INVITE_LINK = os.getenv("ALGO_INVITE_LINK", "https://t.me/+uETpfryOXOI4MTU0")
