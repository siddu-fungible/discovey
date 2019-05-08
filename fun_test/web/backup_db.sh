# This is intended to be run only on the main regression server
NOW=$(date +"%m-%d-%Y-%H-%M")
./manage.py dumpdata > /tmp/perf_db_backup.json
tar -cvzf /tmp/perf_db_backup.json.$NOW.bkp.tgz -C /tmp/perf_db_backup.json
