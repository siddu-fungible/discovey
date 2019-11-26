# Additional notes regarding the regression/production environment

## Initial setup
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

## SSH settings
~~~~
qa-admin@qa-ubuntu-01:~$ grep Client /etc/ssh/sshd_config
ClientAliveInterval 1200
ClientAliveCountMax 3
~~~~


## Postgres settings for the main regression server (Ubuntu only)
### Prepare the data-directory
~~~~

# mkdir /project/users/QA/regression/database

qa-admin@qa-ubuntu-01:/project/users/QA/regression/Integration/fun_test$ grep "data_dir"   /etc/postgresql/9.5/main/postgresql.conf
#data_directory = '/var/lib/postgresql/9.5/main'		# use data in another directory
data_directory = '/project/users/QA/regression/database/postgresql’
~~~~

### Start the Postgres service
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


## Starting the scheduler
- Ensure the web-server was started successfully
- Ensure that 'ps -ef | grep scheduler_main' does not show any entry
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export PRODUCTION_MODE=1
# scheduler/restart_scheduler.sh
~~~~

## Re-starting the web-server
~~~~
# cd /project/users/QA/regression/Integration/fun_test
# export PYTHONPATH=`pwd`
# export PRODUCTION_MODE=1
# ./web/restart_production_server.sh
~~~~

## Debugging Postgres
1. Check /var/log/syslog
2. Run without daemon mode:
    ~~~~
    /usr/lib/postgresql/9.5/bin/postgres -d 3 -D /project/users/QA/regression/database/postgresql/9.5/main  -c config_file=/etc/postgresql/9.5/main/postgresql.conf
    ~~~~
3. Ensure postgres is running. Refer notes above
4. Enable query logging on Postgres

    a. Determine the location where the HBA file is.
        John-Abrahams-MacBook-Pro:fun_test johnabraham$ psql postgres
        psql (10.4)
        Type "help" for help.

        postgres=# SHOW hba_file;
                      hba_file
        -------------------------------------
         /usr/local/var/postgres/pg_hba.conf
        (1 row)
    b. postgresql.conf will be in the same directory determined above. Set log_ variables in postgresql.conf
    ~~~~
    John-Abrahams-MacBook-Pro:fun_test johnabraham$ grep log_ /usr/local/var/postgres/postgresql.conf
    # "postgres -c log_connections=on".  Some parameters can be changed at run time
    #wal_log_hints = off			# also do full page writes of non-critical updates
    #log_destination = 'stderr'		# Valid values are combinations of
    log_directory = 'log'			# directory where log files are written,
    log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'	# log file name pattern,
    #log_file_mode = 0600			# creation mode for log files,
    #log_truncate_on_rotation = off		# If on, an existing log file with the
    #log_rotation_age = 1d			# Automatic rotation of logfiles will
    #log_rotation_size = 10MB		# Automatic rotation of logfiles will
    #syslog_facility = 'LOCAL0'
    #syslog_ident = 'postgres'
    #syslog_sequence_numbers = on
    #syslog_split_messages = on
    #log_min_messages = warning		# values in order of decreasing detail:
    #log_min_error_statement = error	# values in order of decreasing detail:
    #log_min_duration_statement = -1	# -1 is disabled, 0 logs all statements
    #log_checkpoints = off
    #log_connections = off
    #log_disconnections = off
    #log_duration = off
    #log_error_verbosity = default		# terse, default, or verbose messages
    #log_hostname = off
    #log_line_prefix = '%m [%p] '		# special values:
    #log_lock_waits = off			# log lock waits >= deadlock_timeout
    log_statement = 'all'			# none, ddl, mod, all
    #log_replication_commands = off
    #log_temp_files = -1			# log temporary files equal or larger
    log_timezone = 'US/Pacific'
    #log_parser_stats = off
    #log_planner_stats = off
    #log_executor_stats = off
    #log_statement_stats = off
    #log_autovacuum_min_duration = -1	# -1 disables, 0 logs all actions and
    ~~~~
    c. Restart Postgres

       On Ubuntu:
       sudo systemctl stop postgresql
       sudo systemctl start postgresql


## Errors in Angular

If you encounter EBUSY: resource busy or locked, unlink, too often
~~~~
npm cache clean --force"
npm install
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

