## fun_test
This page is under construction. 
fun_test has the following layout
1. assets
2. system
3. scripts
4. scheduler
5. web
6. stash (A place to store git repositories)

## Setup
### Quick-start (without the web-server)
~~~~
cd /project/users/QA/regression/Integration/fun_test
export PYTHONPATH=`pwd`
pip install -r requirements.txt --user
python scripts/examples/sanity.py
~~~~


### Setup with the web-server and databases
The infrastructure uses the following:

1. PostgreSQL as the SQL RDBMS
2. Angular 6 for the web framework
3. Django as the REST API server
4. MongDB as the NoSQL database


#### 1. Postgres setup
##### Ubuntu installation:
```
# sudo apt-get install postgresql
# update-rc.d postgresql enable
# service postgresql start


# sudo -u postgres -i
# psql

psql (9.5.14)
Type "help" for help.

postgres=# CREATE USER fun_test_user WITH PASSWORD 'fun123';
CREATE ROLE
postgres=# CREATE DATABASE fun_test;
CREATE DATABASE
postgres-# \q

```

##### Mac installation:
```
Install Xcode via the Appstore

In a terminal execute the below:
# brew install postgres
# brew services start postgresql


# psql postgres

psql (9.5.14)
Type "help" for help.

postgres=# CREATE USER fun_test_user WITH PASSWORD 'fun123';
CREATE ROLE
postgres=# CREATE DATABASE fun_test;
CREATE DATABASE
postgres-# \q

```


#### 2. Angular 6 installation
```
# cd Integration/fun_test/web/angular/qadashboard
# brew install npm (For Mac only)
# npm install -g @angular/cli
# npm install

```



#### 3. Django installation
Django will be installed via the instructions mentioned in the Quick-start section
````
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# cd web
# export DEVELOPMENT_MODE=1; python start_development_server
# python web/manage.py migrate --database=default
````

