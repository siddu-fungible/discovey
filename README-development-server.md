## Setup need for a development environment

### Install Python modules
```
# cd /project/users/QA/regression/Integration/fun_test
# pip install -r requirements.txt --user
```


### Install Postgres database
Refer: https://github.com/fungible-inc/Integration/blob/master/README-postgres-installation-notes.md


### Starting the web-server
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export DEVELOPMENT_MODE=1
# python web/manage.py migrate --database=default
# cd web/angular/qadashboard/
# npm install
# ng build
# nohup python web/start_development_server.py &> server.out  &
~~~~

### Starting/Re-starting the scheduler
- Ensure the web-server was started successfully
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export PRODUCTION_MODE=1
# scheduler/restart_scheduler.sh
~~~~
- Ensure that ps -ef | grep scheduler_main does not show any entry
