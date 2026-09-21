"""MaktabIQ Telegram Bot.

Foydalanuvchi saytdagi «Yordam» bo'limidan (`/api/v1/users/me/telegram-link-code/`) bir martalik
kod oladi, so'ng botga `/link <code>` (yoki shunchaki kodni) yuboradi. Bot kodni sayt saqlagan
kod bilan tekshirib (`apps/users/telegram_link.py`), telegram_chat_id'ni User'ga bog'laydi — shundan keyin absent, grade, homework,
announcement va emergency xabarlari shu chat'ga yuboriladi (apps/notifications/tasks.py).

Ishga tushirish: `python -m bot.bot` (loyiha ildizidan, .env'da TELEGRAM_BOT_TOKEN bilan).
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from common.system_certs import use_system_trust_store  # noqa: E402

use_system_trust_store()

import logging  # noqa: E402

from asgiref.sync import sync_to_async  # noqa: E402
from django.conf import settings  # noqa: E402
from telegram import Update  # noqa: E402
from telegram.ext import (  # noqa: E402
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


LINK_HELP = (
    "Hisobingizni bog'lash uchun MaktabIQ saytida «Yordam» bo'limidan Telegram kodini oling, "
    "so'ng shu yerga yuboring:\n/link <kod>\n(yoki kodning o'zini yozing)"
)


@sync_to_async
def _try_link(code, chat_id):
    from apps.users.telegram_link import link_with_code, notify_linked

    status, user = link_with_code(code, chat_id)
    if user is not None:
        notify_linked(user)
    return status, user


async def _link_and_reply(update: Update, code: str):
    from apps.users.telegram_link import LINK_BLOCKED, LINK_OK

    status, user = await _try_link(code, update.effective_chat.id)
    if status == LINK_OK:
        await update.message.reply_text(
            f"✅ Hisobingiz muvaffaqiyatli bog'landi, {user.get_full_name() or user.username}!\n"
            "Endi bildirishnomalarni shu yerda olasiz."
        )
    elif status == LINK_BLOCKED:
        await update.message.reply_text("Juda ko'p noto'g'ri urinish. 10 daqiqadan keyin qayta urinib ko'ring.")
    else:
        await update.message.reply_text("❌ Kod noto'g'ri yoki muddati o'tgan. Saytdan yangi kod oling.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Deep link: https://t.me/<bot>?start=<code>
    if context.args:
        await _link_and_reply(update, context.args[0].strip())
        return
    await update.message.reply_text("Assalomu alaykum! MaktabIQ botiga xush kelibsiz.\n\n" + LINK_HELP)


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Foydalanish: /link <kod>\n\n" + LINK_HELP)
        return
    await _link_and_reply(update, context.args[0].strip())


async def plain_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """A bare 6-digit message is treated as a link code."""
    text = (update.message.text or "").strip()
    if text.isdigit() and len(text) == 6:
        await _link_and_reply(update, text)
    else:
        await update.message.reply_text(LINK_HELP)


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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_code))

    logger.info("MaktabIQ bot polling boshlandi...")
    application.run_polling()


if __name__ == "__main__":
    main()
