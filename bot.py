import logging
import asyncio
import csv
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from database import Database
from config import BOT_TOKEN, ADMIN_IDS, COURSE_INVITE_LINK, ALGO_INVITE_LINK

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

db = Database()

WAITING_BROADCAST = 1


# ─────────────────────────────────────────────
#  /start
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_new = db.add_user(user.id, user.username, user.full_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Курс по SQL (бесплатно)", url=COURSE_INVITE_LINK)],
        [InlineKeyboardButton("⚡️ Неделя алгоритмов (бесплатно)", url=ALGO_INVITE_LINK)],
    ])

    if is_new:
        text = (
            f"Привет, {user.first_name}! 👋\n\n"
            "Даем тебе полностью бесплатный доступ к нашему курсу по SQL.\n"
            "Это один из главных инструментов работы с данными для любого аналитика.\n\n"
           "А ещё у нас есть бесплатный курс «Python для алгоритмов» — для тех, кто хочет изучать алгоритмы, но пока не хватает базы программирования.\n\n"
        )
    else:
        text = (
            f"С возвращением, {user.first_name}! 👋\n\n"
            "У нас стартует Неделя алгоритмов — открытый бесплатный курс.\n"
            "Присоединяйся, пока не закрыли набор 👇"
        )

    await update.message.reply_text(text, reply_markup=keyboard)


# ─────────────────────────────────────────────
#  /broadcast — двухшаговая рассылка
# ─────────────────────────────────────────────
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return ConversationHandler.END

    count = db.get_user_count()
    await update.message.reply_text(
        f"Пришли сообщение для рассылки.\n\n"
        f"Можно: текст с абзацами, картинку с подписью, или просто картинку.\n"
        f"Получателей: {count} чел.\n\n"
        f"Для отмены напиши /cancel"
    )
    return WAITING_BROADCAST


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users = db.get_all_users()
    sent = 0
    failed = 0

    status_msg = await update.message.reply_text(f"📤 Рассылка начата... (0/{len(users)})")

    for i, (chat_id,) in enumerate(users):
        try:
            # Картинка с подписью или без
            if update.message.photo:
                photo = update.message.photo[-1].file_id
                caption = update.message.caption or ""
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                )
            # Просто текст (поддерживает абзацы и эмодзи)
            elif update.message.text:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=update.message.text,
                )
            sent += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить {chat_id}: {e}")
            failed += 1

        if (i + 1) % 20 == 0:
            await status_msg.edit_text(f"📤 Рассылка... ({i+1}/{len(users)})")
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"✅ Рассылка завершена!\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}"
    )
    return ConversationHandler.END


async def broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Рассылка отменена.")
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  /stats
# ─────────────────────────────────────────────
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return
    count = db.get_user_count()
    await update.message.reply_text(f"Всего пользователей: {count}")


# ─────────────────────────────────────────────
#  /export
# ─────────────────────────────────────────────
async def export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return

    rows = db.get_all_users_full()
    if not rows:
        await update.message.reply_text("Пока нет пользователей.")
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["chat_id", "username", "full_name", "joined_at"])
    for row in rows:
        writer.writerow(row)

    output.seek(0)
    file_bytes = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    file_bytes.name = "users.csv"

    await update.message.reply_document(
        document=InputFile(file_bytes, filename="users.csv"),
        caption=f"Всего пользователей: {len(rows)}",
    )


# ─────────────────────────────────────────────
#  Запуск
# ─────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            WAITING_BROADCAST: [
                MessageHandler(filters.TEXT | filters.PHOTO, broadcast_send),
            ],
        },
        fallbacks=[CommandHandler("cancel", broadcast_cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(broadcast_handler)
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("export", export))

    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
