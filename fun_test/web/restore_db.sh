set -e
read -n "This will delete old migration files" user_choice

if [ "$user_choice" = "y" ]
then
    echo "Removing old migrations"
    `find . -path "*/migrations/*.py" -not -name "__init__.py" -delete`
    `find . -path "*/migrations/*.pyc"  -delete`
else
    echo "Exiting now."
fi


tar -xvzf perf_db_backup.json.bkp.tgz


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
