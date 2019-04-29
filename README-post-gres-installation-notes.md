# Post-gres installation notes:

## Ubuntu:
```
sudo apt-get install postgresql
update-rc.d postgresql enable
service postgresql start
sudo -u postgres -i

psql
psql (9.5.14)
Type "help" for help.

postgres=# CREATE USER fun_test_user WITH PASSWORD 'fun123';
CREATE ROLE
postgres=# CREATE DATABASE fun_test;
CREATE DATABASE
postgres-# \q
```
