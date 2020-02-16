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


### Basic setup with the web-server and databases
Please ensure the steps in the Quick-start section have been completed

#### 1. Postgres setup
##### Installation on Ubuntu:
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

##### Installation on the Mac:
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


#### 2. Starting the web-server
Django will be installed via the instructions mentioned in the Quick-start section
````
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# cd web
# export DEVELOPMENT_MODE=1;
# python web/manage.py migrate --database=default
# python start_development_server
# python scripts/examples/sanity.py (this will generate a link to the report on the web-server)
````

#### 3. Running tests
The preferred approach is to run tests using PyCharm
https://github.com/fungible-inc/Integration/blob/master/fun_test/documentation/running_tests.md


## Notes for advanced users
https://github.com/fungible-inc/Integration/blob/master/fun_test/documentation/advanced_users.md
