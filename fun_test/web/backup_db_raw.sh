# This is intended to be run only on the main regression server
NOW=$(date +"%m-%d-%Y-%H-%M")
BACKUP_FILE=fun_test
BACKUP_LOCATION=/project/users/QA/regression/data_store/web_backup
BACKUP_FILE_TGZ=$BACKUP_FILE.$NOW.bkp.tgz
sudo -u postgres pg_dump fun_test | gzip > $BACKUP_LOCATION/$BACKUP_FILE_TGZ
echo "Backup moved to: $BACKUP_LOCATION/$BACKUP_FILE_TGZ"
