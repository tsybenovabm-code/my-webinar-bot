import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from database import Database
from config import BOT_TOKEN, ADMIN_IDS, COURSE_INVITE_LINK, COURSE_CHANNEL_NAME

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

db = Database()


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat_id = user.id

    is_new = db.add_user(chat_id, user.username, user.full_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📚 Получить доступ к курсу", url=COURSE_INVITE_LINK)],
    ])

    if is_new:
        text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Из-за технических проблемам на платформе мы не смогли провести открытый вебинар."
            " Но это не беда - мы просто перенесем его на это воскресенье. Уведомление придёт прямо сюда!\n\n"
            "🎁 А чтобы ты не скучал, в качестве бонуса мы даем тебе полностью бесплатный доступ к нашему курсу по SQL.\n"
            "Это один из главных инструментов работы с данными для любого аналитика.\n\n"
            "Нажми кнопку ниже, чтобы вступить в закрытый канал с курсом 👇\n\n"
        )
    else:
        text = (
            f"С возвращением, {user.first_name}! 👋\n\n"
            "Твой доступ к курсу по SQL всё ещё активен 👇"
        )

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


# ─────────────────────────────────────────────
#  /broadcast — только для админов
# ─────────────────────────────────────────────
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У тебя нет доступа к этой команде.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast <текст сообщения>\n\n"
            "Например:\n"
            "/broadcast 🔔 Напоминаем: вебинар сегодня в 19:00! Ждём тебя 👉 [ссылка]"
        )
        return

    message_text = " ".join(context.args)
    users = db.get_all_users()

    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"📤 Рассылка начата... (0/{len(users)})")

    for i, (chat_id,) in enumerate(users):
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                parse_mode="Markdown",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить {chat_id}: {e}")
            failed += 1

        # Обновляем статус каждые 20 сообщений
        if (i + 1) % 20 == 0:
            await status_msg.edit_text(f"📤 Рассылка... ({i+1}/{len(users)})")

        await asyncio.sleep(0.05)  # Чтобы не словить rate limit

    await status_msg.edit_text(
        f"✅ Рассылка завершена!\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )


# ─────────────────────────────────────────────
#  /stats — только для админов
# ─────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ У тебя нет доступа к этой команде.")
        return

    count = db.get_user_count()
    await update.message.reply_text(
        f"📊 *Статистика бота*\n\n"
        f"👥 Всего пользователей: *{count}*",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
#  /help
# ─────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    is_admin = update.effective_user.id in ADMIN_IDS
    text = "ℹ️ *Доступные команды:*\n\n/start — получить доступ к курсу"
    if is_admin:
        text += (
            "\n\n*Админ-команды:*\n"
            "/broadcast <текст> — разослать сообщение всем пользователям\n"
            "/stats — статистика подключившихся"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────
#  Запуск
# ─────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("help", help_command))

    logger.info("Бот запущен ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
