import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from database import Database
from config import BOT_TOKEN, ADMIN_IDS, COURSE_INVITE_LINK, CHANNEL_USERNAME

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

db = Database()


async def check_subscription(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_subscribed = await check_subscription(context.bot, user.id)

    if not is_subscribed:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "📢 Подписаться на канал",
                url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
            )],
            [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")],
        ])
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Чтобы получить доступ к курсу, сначала подпишись на наш канал Поступашки 👇",
            reply_markup=keyboard,
        )
        return

    await give_access(update.message, user)


async def give_access(message, user):
    is_new = db.add_user(user.id, user.username, user.full_name)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Получить доступ к курсу", url=COURSE_INVITE_LINK)],
    ])

    if is_new:
        text = (
            f"Отлично! \n\n"
            "Даем тебе полностью *бесплатный доступ к нашему курсу по SQL*.\n"
            "Это один из главных инструментов работы с данными для любого аналитика.\n\n"
            "Также напоминаем, что 17 мая в 17:30 мы проведем вебинар по A/B-тестам, "
            "напоминание и ссылку пришлем сюда, не забудь включить уведомления.\n\n"
            "Нажми кнопку ниже, чтобы вступить в закрытый канал с курсом 👇"
        )
    else:
        text = (
            f"С возвращением, {user.first_name}! 👋\n\n"
            "Твой доступ к курсу по SQL всё ещё активен 👇"
        )

    await message.reply_text(text, reply_markup=keyboard)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "check_subscription":
        is_subscribed = await check_subscription(context.bot, user.id)

        if is_subscribed:
            await query.message.delete()
            await give_access(query.message, user)
        else:
            await query.answer(
                "Ты ещё не подписался 😊 Подпишись и нажми кнопку снова!",
                show_alert=True,
            )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast текст сообщения\n\n"
            "Например:\n"
            "/broadcast Вебинар сегодня в 17:30! Ссылка: https://..."
        )
        return

    message_text = " ".join(context.args)
    users = db.get_all_users()
    sent = 0
    failed = 0
    status_msg = await update.message.reply_text(f"Рассылка начата... (0/{len(users)})")

    for i, (chat_id,) in enumerate(users):
        try:
            await context.bot.send_message(chat_id=chat_id, text=message_text)
            sent += 1
        except Exception as e:
            logger.warning(f"Не удалось отправить {chat_id}: {e}")
            failed += 1
        if (i + 1) % 20 == 0:
            await status_msg.edit_text(f"Рассылка... ({i+1}/{len(users)})")
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"Рассылка завершена!\n\n"
        f"Отправлено: {sent}\n"
        f"Не доставлено: {failed}"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("У тебя нет доступа к этой команде.")
        return
    count = db.get_user_count()
    await update.message.reply_text(f"Всего пользователей: {count}")


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Бот запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
