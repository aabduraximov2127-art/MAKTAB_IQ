import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id, text):
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.info("Telegram not configured or chat_id missing, skipping message to %s", chat_id)
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Failed to send Telegram message to %s", chat_id)
        return False
