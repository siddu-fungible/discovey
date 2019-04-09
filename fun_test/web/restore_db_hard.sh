dropdb fun_test
createdb fun_test
rm fun_test/migrations/0*py
python manage.py makemigrations
python manage.py migrate --database=default
tar -xvzf perf_db_backup.json.bkp.tgz
python manage.py loaddata perf_db_backup.json  --exclude contenttypes
python manage.py initialize
