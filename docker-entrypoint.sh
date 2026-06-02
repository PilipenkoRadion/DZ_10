#!/bin/bash
set -e
echo "Начало ура ..."
python manage.py collectstatic --noinput

echo "Миграций к базе данных ..."

python manage.py migrate --noinput

echo "Запускаем ваш проект ..."
exec python manage.py runserver 0.0.0.0:8000