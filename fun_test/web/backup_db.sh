
./manage.py dumpdata > perf_db_backup.json
tar -cvzf perf_db_backup.json.bkp.tgz perf_db_backup.json
