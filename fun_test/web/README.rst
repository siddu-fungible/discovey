DB Backup:
./backup_db.sh 


DB restore:

Drop the database

John-Abrahams-MacBook-Pro:backup johnabraham$ psql postgres
psql (10.4)
Type "help" for help.

postgres=# DROP DATABASE fun_test;
DROP DATABASE
postgres=# CREATE DATABASE fun_test;
CREATE DATABASE


Untar the backup:
tar -xvzf perf_db_backup.json.bkp.tgz 

python manage.py migrate --database=default
python manage.py loaddata perf_db_backup.json  --exclude contenttypes 

