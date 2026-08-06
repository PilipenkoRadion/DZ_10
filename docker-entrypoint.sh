set -e
echo "Начало запуска, немного подождите"
python manage.py collectstatic --noinput

echo "Миграций к базе данных"

python manage.py migrate --noinput

echo "Запускаем ваш проект, почти уже готово ..."
exec python manage.py runserver 0.0.0.0:8000