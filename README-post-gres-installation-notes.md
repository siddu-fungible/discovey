# Post-gres installation notes:

## Ubuntu installation:
```
sudo apt-get install postgresql
update-rc.d postgresql enable
service postgresql start
sudo -u postgres -i

psql (9.5.14)
Type "help" for help.

postgres=# CREATE USER fun_test_user WITH PASSWORD 'fun123';
CREATE ROLE
postgres=# CREATE DATABASE fun_test;
CREATE DATABASE
postgres-# \q

```

## Mac installation:
```
brew install postgres
brew services start postgresql
psql postgres

psql (9.5.14)
Type "help" for help.

postgres=# CREATE USER fun_test_user WITH PASSWORD 'fun123';
CREATE ROLE
postgres=# CREATE DATABASE fun_test;
CREATE DATABASE
postgres-# \q

```
