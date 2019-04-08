set -e

dropdb fun_test
echo "Dropped fun_test"
createdb fun_test
echo "Created fun_test"

tar -xvzf perf_db_backup.json.bkp.tgz
python manage.py migrate --database=default
echo "Completed migrate"
python manage.py loaddata perf_db_backup.json  --exclude contenttypes 
echo "Restore complete"

