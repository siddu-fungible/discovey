dropdb fun_test
createdb fun_test
rm fun_test/migrations/0*py
python manage.py makemigrations
python manage.py migrate --database=default
python manage.py initialize
