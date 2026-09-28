#!/bin/sh
set -e
python manage.py migrate --noinput
python manage.py seed_demo_users
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
