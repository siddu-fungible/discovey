#!/bin/bash

PREFIX=$1
SOCKET=$2
OUTLOG=$3
ERRLOG=$4
LAUNCHERDBG=$5

PROJDIR=$(dirname $(readlink -f "$0"))
PIDFILE="launcher.pid"

cd $PROJDIR

# Stop the service if it is running. 
starting=1
. ./stop_sl.sh $PREFIX $SOCKET $OUTLOG $ERRLOG

export REST_STC_HOME=${PROJDIR%/*}
export LD_LIBRARY_PATH=${REST_STC_HOME}/Python/lib:${REST_STC_HOME}:${HOME}/stcweb
export PYTHON=${REST_STC_HOME}/Python/bin/python

. ${HOME}/pyenv/bin/activate
if [ -f sessionlauncher.py ]
then
    LAUNCHER='sessionlauncher.py'
else
    LAUNCHER='sessionlauncher.pyc'
fi


# Use this for local sessions (no TestCenter server)
LAUNCHERARGS="--prefix $PREFIX --channel $SOCKET --pidfile $PIDFILE "
if [ $LAUNCHERDBG == "--debug" ]
then
    LAUNCHERARGS+=" $LAUNCHERDBG"
fi

exec $PYTHON $LAUNCHER $LAUNCHERARGS 1>"${OUTLOG}" 2>"${ERRLOG}"  &

PIDPATH="/tmp/stcweb_${PREFIX}/${PIDFILE}"

sleep 2
try=0
limit=30

while [ $try -lt $limit ]
do
    sleep 1
    if [ -f $PIDPATH ]
    then
        pid=$(cat -- $PIDPATH)
        kill -0 $pid >/dev/null 2>&1
        if [ $? -eq 0 ]
        then
            break
        fi
    fi
    echo -n '.'
    try=$(expr $try + 1)
done

dt=$(date)
if [ $try -ge $limit ]
then
    echo "${dt} ALERT: session service did not start"  >> ${ERRLOG}
    exit 1
fi

echo "${dt} started stcapi session service" >> "${OUTLOG}"
