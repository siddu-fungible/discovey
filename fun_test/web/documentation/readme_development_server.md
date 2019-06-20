## Setup need for a development environment

### Install Python modules
```
# cd /project/users/QA/regression/Integration/fun_test
# pip install -r requirements.txt --user
```

### Install Postgres database
Refer: https://github.com/fungible-inc/Integration/blob/master/fun_test/web/documentation/postgres_notes.md

### Backing up database from qa-ubuntu-01
~~~~
# ssh qa-admin@qa-ubuntu-01
# cd /project/users/QA/regression/Integration/fun_test/web
# ./backup_db.sh
# exit
~~~~
The output should look like:
~~~~
qa-admin@qa-ubuntu-01:~$ cd /project/users/QA/regression/Integration/fun_test/web/
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test/web$ ./backup_db.sh
perf_db_backup.json 
Backup moved to: /project/users/QA/regression/data_store/web_backup/perf_db_backup.json.06-17-2019-13-13.bkp.tgz
~~~~

### Restore database locally
Please ensure that the web-server and scheduler are stopped before restoring the database.
~~~~
# cd /Desktop/Integration/fun_test (your local directory)
# export PYTHONPATH=`pwd`
# export DEVELOPMENT_MODE=1
# cd web
# scp qa-admin@qa-ubuntu-01:/project/users/QA/regression/data_store/web_backup/'file name' . (file name from the previous step)
# ./restore_db.sh 'file name' (In the example output shown above, the file name is perf_db_backup.json.06-17-2019-13-13.bkp.tgz)
~~~~
Example:
~~~~
# Ashwins-MacBook-Pro-2:web ash$ ./restore_db.sh perf_db_backup.json.06-17-2019-13-13.bkp.tgz
~~~~

### Starting the web-server
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export DEVELOPMENT_MODE=1
# python web/manage.py migrate --database=default
# cd web/angular/qadashboard/
# brew install npm (For Mac only)
# npm install -g @angular/cli
# npm install
# ng build
# nohup python web/start_development_server.py &> server.out  &
~~~~

### Starting/Re-starting the scheduler
- Ensure the web-server was started successfully
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export DEVELOPMENT_MODE=1
# scheduler/restart_scheduler.sh
~~~~
- Ensure that ps -ef | grep scheduler_main does not show any entry


### Keeping the integration/review branch up-to-date
~~~~
cd Integration/
git pull origin master
cd fun_test/
export PYTHONPATH=`pwd`
export DEVELOPMENT_MODE=1
python web/manage.py migrate --database=default
 ~~~~
