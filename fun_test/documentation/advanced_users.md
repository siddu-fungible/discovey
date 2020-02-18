# Installation notes for advanced users
The following installation notes are meant for users who develop the web front-end or want to run the scheduler locally

### Angular 6 installation
```
# cd Integration/fun_test/web/angular/qadashboard
# brew install npm (For Mac only)
# npm install -g @angular/cli
# npm install
```

### MongoDB installation
```
# sudo apt-get update
# echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.0.list
# sudo apt-get install -y mongodb-org
# sudo apt-get install -y mongodb-org=4.0.13 mongodb-org-server=4.0.13 mongodb-org-shell=4.0.13 mongodb-org-mongos=4.0.13 mongodb-org-tools=4.0.13
# qa-admin@qa-ubuntu-01:/etc/apt$ grep bind /etc/mongod.conf

  bindIp: 0.0.0.0
# sudo systemctl restart mongodb
# ulimit -n 4096 (For Mac users only)
```

#### Starting/Re-starting the scheduler
- Ensure the web-server was started successfully
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export DEVELOPMENT_MODE=1 (export PRODUCTION_MODE=1 for production/regression server)
# scheduler/restart_scheduler.sh
~~~~
- Ensure that ps -ef | grep scheduler_main does not show any entry

### Additional notes regarding the development environment
#### Backing up the database from qa-ubuntu-01
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

#### Restore database locally
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


## Additional notes regarding the regression/production environment
All configuration steps below need to be performed with "qa-admin" as the user

### Account settings
~~~~
# sudo adduser qa-admin sudo
# echo $PRODUCTION_MODE
1
# cat ~/.bash_profile
if [ -f $HOME/.bashrc ]; then
        source $HOME/.bashrc
fi

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
qa-admin@qa-ubuntu-01:~$ cat ~/.bashrc
# export PRODUCTION_MODE=1
# export PYTHONPATH=/project/users/QA/regression/Integration/fun_test
~~~~

### iptables
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$  sudo iptables -i enp3s0f0 -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000
~~~~

### SSH settings
~~~~
qa-admin@qa-ubuntu-01:~$ grep Client /etc/ssh/sshd_config
ClientAliveInterval 1200
ClientAliveCountMax 3
~~~~


### Postgres settings for the main regression server (Ubuntu only)
#### Prepare the data-directory
~~~~

# mkdir /project/users/QA/regression/database

qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ grep "data_dir"   /etc/postgresql/9.5/main/postgresql.conf
#data_directory = '/var/lib/postgresql/9.5/main'		# use data in another directory
data_directory = '/project/users/QA/regression/database/postgresql’
~~~~

#### Prepare logging
~~~~
qa-admin@qa-ubuntu-01:~$ grep log /etc/postgresql/9.5/main/postgresql.conf | egrep "(log_statement|log_directory|log_filename|logging_collector|log_min_error)"
					# requires logging_collector to be on.
logging_collector = on		# Enable capturing of stderr and csvlog
# These are only used if logging_collector is on:
log_directory = 'pg_log'		# directory where log files are written,
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'	# log file name pattern,
log_min_error_statement = error	# values in order of decreasing detail:
log_statement = 'all'			# none, ddl, mod, all
#log_statement_stats = off
~~~~

#### Start the Postgres service
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ sudo systemctl stop postgresql
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ sudo systemctl start postgresql
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ sudo systemctl status postgresql
● postgresql.service - PostgreSQL RDBMS
   Loaded: loaded (/lib/systemd/system/postgresql.service; enabled; vendor preset: enabled)
   Active: active (exited) since Sat 2019-02-23 07:20:42 PST; 2s ago
  Process: 27461 ExecStart=/bin/true (code=exited, status=0/SUCCESS)
 Main PID: 27461 (code=exited, status=0/SUCCESS)

Feb 23 07:20:42 qa-ubuntu-01 systemd[1]: Starting PostgreSQL RDBMS...
Feb 23 07:20:42 qa-ubuntu-01 systemd[1]: Started PostgreSQL RDBMS.
~~~~




### Re-starting the web-server
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export PRODUCTION_MODE=1
# ./web/restart_production_server.sh
~~~~


#### Docker setup
Enable Docker remote API
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ grep ExecStart /lib/systemd/system/docker.service
ExecStart=/usr/bin/dockerd -H fd:// -H=tcp://0.0.0.0:4243 $DOCKER_OPTS

systemctl daemon-reload
sudo service docker restart
~~~~
Verify Docker remote API
~~~~
qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ curl http://127.0.0.1:4243/version
{"Version":"1.13.1","ApiVersion":"1.26","MinAPIVersion":"1.12","GitCommit":"092cba3","GoVersion":"go1.6.2","Os":"linux","Arch":"amd64","KernelVersion":"4.4.0-87-generic","BuildTime":"2017-11-02T20:40:23.484070968+00:00"}
~~~~


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
### On restarting the server, the following services should be started
```
/project/users/QA/regression/Integration/fun_test$ ./web/restart_production_server.sh
/project/users/QA/regression/Integration/fun_test$ scheduler/restart_scheduler.sh
/project/users/QA/regression/Integration/fun_test$ nohup python catalog_execution_service.py &

/project/users/QA/regression/Integration/fun_test/web/fun_test$ cd tests/
/project/users/QA/regression/Integration/fun_test/web/fun_test/tests$ nohup python test_triaging.py &

/project/users/QA/regression/Integration/fun_test/services$ nohup python asset_health_monitor.py &
sudo systemctl restart mongodb
sudo systemctl status mongodb
```

