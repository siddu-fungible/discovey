# Debugging
## Location of the logs
The web-server's logs are located under LOGS_DIR/web.log

## Errors in Angular

If you encounter EBUSY: resource busy or locked, unlink, too often
~~~~
npm cache clean --force"
npm install
~~~~


### Debugging Postgres
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
    c. Check number of active connections. It should be around 23
    ~~~~
    sudo -u postgres -i
    postgres@qa-ubuntu-01:~$ psql
    psql (9.5.13)
    Type "help" for help.

    postgres=# select count(*) from pg_stat_activity;
     count 
    -------
        20
    (1 row)


    ~~~~
    d. Restart Postgres

       On Ubuntu:
       sudo systemctl stop postgresql
       sudo systemctl start postgresql
