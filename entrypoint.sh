#!/bin/sh
set -e

# Only the service the RUN_MIGRATIONS env var is set on applies migrations on startup
# (avoids every service racing to migrate the same database at once).
if [ "$RUN_MIGRATIONS" = "1" ]; then
    python manage.py migrate --noinput
fi

exec "$@"
