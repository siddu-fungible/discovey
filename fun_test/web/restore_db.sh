set -e
tar -xvzf perf_db_backup.json.bkp.tgz
echo "SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'fun_test'
  AND pid <> pg_backend_pid();

CREATE DATABASE fun_test;" > /tmp/restore.sql
# psql -U fun_test_user -c "DROP DATABASE fun_test";
dropdb fun_test
echo "Dropped fun_test"
createdb fun_test
echo "Created fun_test"
python manage.py makemigrations
echo "Completed makemigrations"
python manage.py migrate --database=default
echo "Completed migrate"
python manage.py loaddata perf_db_backup.json  --exclude contenttypes 
echo "Restore complete"
