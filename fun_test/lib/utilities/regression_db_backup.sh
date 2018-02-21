NOW=$(date +"%m-%d-%Y")
REGRESSION_DB=regression.db.sqlite3
BACKUP_FILE=/tmp/$REGRESSION_DB.$NOW.tgz
REMOTE_BACKUP_SERVER=qa-ubuntu-02
SOURCE_PATH=../../web/$REGRESSION_DB
AUTO_ADMIN=auto_admin
tar -cvzf $BACKUP_FILE $SOURCE_PATH
ls -l $BACKUP_FILE
# Ensure passwordless SSH is setup
scp $BACKUP_FILE $AUTO_ADMIN@$REMOTE_BACKUP_SERVER:backups/
rm $BACKUP_FILE
