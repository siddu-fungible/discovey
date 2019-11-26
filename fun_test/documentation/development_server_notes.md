## Additional notes regarding the development environment

### Backing up the database from qa-ubuntu-01
~~~~
# ssh qa-admin@qa-ubuntu-01
# cd /project/users/QA/regression/Integration/fun_test/web
# ./backup_db_raw.sh
# exit
~~~~
The output should look like:
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test/web$ ./backup_db_raw.sh
Backup moved to: /project/users/QA/regression/data_store/web_backup/fun_test.11-25-2019-20-15.bkp.tgz
~~~~

### Restore database locally
Please ensure that the web-server and scheduler are stopped before restoring the database.
~~~~
# cd /Desktop/Integration/fun_test (your local directory)
# export PYTHONPATH=`pwd`
# export DEVELOPMENT_MODE=1
# cd web
# scp qa-admin@qa-ubuntu-01:/project/users/QA/regression/data_store/web_backup/'file name' . (file name from the previous step)
# ./restore_db_raw.sh 'file name' (In the example output shown above, the file name is fun_test.11-25-2019-20-15.bkp.tgz)
~~~~
Example:
~~~~
# Ashwins-MacBook-Pro-2:web ash$ ./restore_db_raw.sh perf_db_backup.json.06-17-2019-13-13.bkp.tgz
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

