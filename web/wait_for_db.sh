#!/bin/bash

set -e

db="$1"
shift

while sleep 1; do
  if python -W ignore db-connect.py 2>&1 >/dev/null; then
    echo "Database is ready"
    break
  fi
  echo "Database is unavailable - sleeping"
done

cd gep
python manage.py collectstatic --noinput
python manage.py makemigrations gep_app
python manage.py migrate
gunicorn gep_project.wsgi:application -w 2 -b :8000
