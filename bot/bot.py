"""MaktabIQ Telegram Bot.

Foydalanuvchi web/app orqali `/api/v1/users/me/telegram-link-code/` dan bir martalik
kod oladi, so'ng botga `/link <code>` yuboradi. Bot kodni tekshirib, uning
telegram_chat_id'sini User'ga bog'laydi — shundan keyin absent, grade, homework,
announcement va emergency xabarlari shu chat'ga yuboriladi (apps/notifications/tasks.py).

Ishga tushirish: `python -m bot.bot` (loyiha ildizidan, .env'da TELEGRAM_BOT_TOKEN bilan).
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import logging  # noqa: E402

from asgiref.sync import sync_to_async  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from telegram import Update  # noqa: E402
from telegram.ext import (  # noqa: E402
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! MaktabIQ botiga xush kelibsiz.\n\n"
        "Hisobingizni bog'lash uchun MaktabIQ profilingizdan kod oling, so'ng:\n"
        "/link <kod>"
    )


@sync_to_async
def _mark_linked(user_id, chat_id):
    from apps.users.models import User

    updated = User.objects.filter(id=user_id).update(telegram_chat_id=chat_id)
    if not updated:
        return None
    return User.objects.get(id=user_id)


@sync_to_async
def _notify_linked(user):
    from apps.notifications.models import Notification, NotificationType
    from common.realtime import push_notification_to_user

    notification = Notification.objects.create(
        user=user,
        title="Telegram ulandi",
        message="Hisobingiz Telegram botiga muvaffaqiyatli ulandi. Endi bildirishnomalarni shu yerda ham olasiz.",
        type=NotificationType.ANNOUNCEMENT,
    )
    push_notification_to_user(
        user.id,
        {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type,
            "created_at": notification.created_at.isoformat(),
        },
    )


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /link <kod>")
        return

    code = context.args[0]
    user_id = cache.get(f"telegram_link:{code}")
    if not user_id:
        await update.message.reply_text("Kod noto'g'ri yoki muddati o'tgan. Qaytadan urinib ko'ring.")
        return

    chat_id = str(update.effective_chat.id)
    user = await _mark_linked(user_id, chat_id)
    cache.delete(f"telegram_link:{code}")

    if user is None:
        await update.message.reply_text("Xatolik yuz berdi, hisob topilmadi. Qaytadan urinib ko'ring.")
        return

    await _notify_linked(user)
    await update.message.reply_text("Hisobingiz muvaffaqiyatli bog'landi! Endi bildirishnomalarni shu yerda olasiz.")


async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from apps.users.models import User

    chat_id = str(update.effective_chat.id)
    await sync_to_async(User.objects.filter(telegram_chat_id=chat_id).update)(telegram_chat_id=None)
    await update.message.reply_text("Hisobingiz botdan uzildi.")


def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN sozlanmagan (.env)")

    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link))
    application.add_handler(CommandHandler("unlink", unlink))

    logger.info("MaktabIQ bot polling boshlandi...")
    application.run_polling()


if __name__ == "__main__":
    main()
