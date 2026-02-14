#!/bin/sh

set -e

ls -la /vol/
ls -la /vol/web

whoami

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py collect_statistics

exec gunicorn portfolio.asgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120
