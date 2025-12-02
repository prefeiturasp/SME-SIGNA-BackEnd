#!/usr/bin/env bash
set -e

# esperar Postgres (ajustar depois)
# until pg_isready -h "${DATABASE_HOST:-db}" -p "${POSTGRES_PORT:-5432}" >/dev/null 2>&1; do
#   echo "Waiting for Postgres..."
#   sleep 1
# done

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers ${GUNICORN_WORKERS:-4} \
  --threads ${GUNICORN_THREADS:-2} \
  --timeout ${GUNICORN_TIMEOUT:-120}



