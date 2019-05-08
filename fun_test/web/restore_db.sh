set -e

dropdb fun_test
echo "Dropped fun_test"
createdb fun_test
echo "Created fun_test"
rm fun_test/migrations/0*py
git checkout origin/master -- 'fun_test/migrations/*.py'
python manage.py migrate --database=default
echo "Completed migrate"
python manage.py loaddata perf_db_backup.json  --exclude contenttypes 
echo "Restore complete"

