set -e

dropdb fun_test
echo "Dropped fun_test"
createdb fun_test
echo "Created fun_test"
BACKUP_FILE=perf_db_backup.json
rm $BACKUP_FILE || true
tar -xvzf $1
rm fun_test/migrations/0*py || true
rm fun_test/migrations/0*pyc || true
echo "Removed migrations"
git checkout origin/master -- 'fun_test/migrations/*.py'
python manage.py migrate --database=default
echo "Completed migrate"
python manage.py loaddata $BACKUP_FILE  --exclude contenttypes 
echo "Restore complete"

