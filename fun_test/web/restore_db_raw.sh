set -e

dropdb fun_test
echo "Dropped fun_test"
createdb fun_test
echo "Created fun_test"
rm fun_test/migrations/0*py || true
rm fun_test/migrations/0*pyc || true
echo "Removed migrations"
git checkout origin/master -- 'fun_test/migrations/*.py'
python manage.py migrate --database=default
echo "Completed migrate"
gunzip -c $1 | psql fun_test
echo "Restore complete"

