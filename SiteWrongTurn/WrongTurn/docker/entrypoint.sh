#!/bin/sh
set -e

DB_PATH="${DJANGO_DB_PATH:-/data/db.sqlite3}"
DB_DIR="$(dirname "$DB_PATH")"
mkdir -p "$DB_DIR" /app/staticfiles /app/media/images_for_pages /app/media/questions

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Копирует exam.jpg, ordinary.jpg и т.д. из media/questions в media/images_for_pages
python manage.py setup_mode_images || true

exec gunicorn WrongTurn.wsgi:application \
    --bind 0.0.0.0:8090 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout 120
