## fun_test
fun_test has the following layout
1. assets
2. system
3. scripts
4. scheduler
5. web

### web
Documentation: https://github.com/fungible-inc/Integration/blob/master/fun_test/web/documentation/README.md

## Data-store

A place to store test-input files that are large.
Currently it is set to 'data_store' in the parent directory of the Integration repo.
Ex: /project/users/QA/regression/data_store

The data-store directory can be accessed using
```
from fun_settings import DATA_STORE_DIR
```
### Suggestions for the data-store directories layout

```
data-store/storage
data-store/networking
```
