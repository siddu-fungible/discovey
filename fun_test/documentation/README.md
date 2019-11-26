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
### Setup without the web-server
~~~~
cd /project/users/QA/regression/Integration/fun_test
export PYTHONPATH=`pwd`
pip install -r requirements.txt --user
python scripts/examples/sanity.py
~~~~


### Setup with the web-server and databases
#### Web-server and Postgres setup
Documentation: https://github.com/fungible-inc/Integration/blob/master/fun_test/web/documentation/README.md


## Data-store

A place to store test-input files that are large.
Currently, it is set to 'data_store' in the parent directory of the Integration repo.
Ex: /project/users/QA/regression/data_store

The data-store directory can be accessed using
```
from fun_settings import DATA_STORE_DIR
```
### Suggestions for the data-store directories layout

```
data_store/storage
data_store/networking
data_store/web_backup (Location of the regression/performance Db backup)
data_store/job_backup (Location of the regression jobs log that are archived via web/fun_test/management/archiver.py)
```
