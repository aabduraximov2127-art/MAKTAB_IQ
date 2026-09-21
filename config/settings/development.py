import os

from .base import *  # noqa: F401,F403

DEBUG = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# Redis (Celery broker + Channels layer) is optional in local dev. Set USE_REDIS=1
# in .env once Redis is actually running to get real background tasks / cross-process
# real-time delivery; otherwise everything runs in-process so `runserver` alone works.
if os.getenv("USE_REDIS", "0") != "1":
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    # NOT LocMemCache here: it's per-process memory, so the runserver process and the
    # separate `python -m bot.bot` process would each see their own empty cache and
    # the Telegram /link <code> flow (code written by the web process, read by the
    # bot process) would always miss. A DB-backed cache is shared by both processes
    # without needing Redis. Run `manage.py createcachetable` once to create it.
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache",
        }
    }

# Antivirus HTTPS scanning (Avast etc.) breaks certifi-based TLS to api.telegram.org; use the OS trust store.
from common.system_certs import use_system_trust_store  # noqa: E402

use_system_trust_store()
