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
CREATE USER fun_test_user WITH PASSWORD 'fun123';


Untar the backup:
tar -xvzf perf_db_backup.json.bkp.tgz 

export PERFORMANCE_SERVER=1;
python manage.py migrate --database=default
python manage.py loaddata perf_db_backup.json  --exclude contenttypes 



Postgres Installation on Mac

brew install postgres
brew service start postgres


