# Web
This is the location of the web-server, regression logs and database control modules.
The web-server operates in two modes, development-mode and production-mode (only used on the main regression server: integration.fungible.local)

## Setup
### Web-server in production-mode
Refer: https://github.com/fungible-inc/Integration/blob/master/fun_test/web/documentation/readme_production_server.md

### Web-server in development-mode
Refer: https://github.com/fungible-inc/Integration/blob/master/fun_test/web/documentation/readme_development_server.md

## Debugging
### Location of the logs

The web-server's logs are located under LOGS_DIR/web.log

## Backups
The Db (regression and performance) will be stored at /project/users/QA/regression/data_store/web_backup.
The backup script is located https://github.com/fungible-inc/Integration/blob/master/fun_test/web/backup_db.sh

## Errors
If you encounter EBUSY: resource busy or locked, unlink, too often
~~~~ 
npm cache clean --force"
npm install
~~~~
