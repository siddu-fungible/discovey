# This is intended to be run only on the main regression server
NOW=$(date +"%m-%d-%Y-%H-%M")
TEMP_LOCATION=/tmp
BACKUP_FILE=perf_db_backup.json
BACKUP_LOCATION=/project/users/QA/regression/data_store/web_backup
BACKUP_FILE_TGZ=$BACKUP_FILE.$NOW.bkp.tgz
./manage.py dumpdata  --natural-foreign --natural-primary -e contenttypes -e auth.Permission > $TEMP_LOCATION/$BACKUP_FILE
tar -cvzf $TEMP_LOCATION/$BACKUP_FILE_TGZ -C $TEMP_LOCATION $BACKUP_FILE
mv $TEMP_LOCATION/$BACKUP_FILE_TGZ $BACKUP_LOCATION/
echo "Backup moved to: $BACKUP_LOCATION/$BACKUP_FILE_TGZ"
