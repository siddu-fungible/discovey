## fun_test
This page is under construction. 
fun_test has the following layout
1. assets
2. system
3. scripts
4. scheduler
5. web

### Setup without the web-server
TBD

### Setup with the web-server and database
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
```
