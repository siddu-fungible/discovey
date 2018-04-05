#!/bin/bash

if [ -z "$PREFIX" ]; then
  PREFIX=$1;
fi

if [ -z "$SOCKET" ]; then 
  SOCKET=$2;
fi

if [ -z "$OUTLOG" ]; then
  OUTLOG=$3;
fi

if [ -z "$ERRLOG" ]; then
  ERRLOG=$4;
fi

PROJDIR=$(dirname $(readlink -f "$0"))
SOCKETPATH="/tmp/stcweb_${PREFIX}/${SOCKET}"
PIDFILE="launcher.pid"
PIDPATH="/tmp/stcweb_${PREFIX}/${PIDFILE}"

cd $PROJDIR

name="sessionlauncher"
killwait=15

if [ -S ${SOCKETPATH} ]
then
    if [ -x "$(command -v nc)" ]
    then
        echo "SENDING EXIT MESSAGE" >> $OUTLOG
        printf "[\"___EXIT___\",\"GOODBYE\"]\0" | nc -U ${SOCKETPATH}
        sleep 1
        printf "\nExit command sent.\n" >> $OUTLOG
    fi
fi

if [ -f $PIDPATH ]
then
    pid=$(cat -- $PIDPATH)
    kill -0 $pid
    if [ $? -eq 0 ]
    then
        echo "killing ${name} (pid=$pid)"  >> "${OUTLOG}"
        # TERM first, then KILL if not dead
        kill -TERM $pid 
        try=0
        while [ $try -lt $killwait ]
        do
            sleep 1
            kill -0 $pid >/dev/null 2>&1 || break
            echo -n '.' >> "${OUTLOG}"
            try=$(expr $try + 1)
        done
        if [ $try -eq $killwait ]
        then
            echo " still running..."  >> "${OUTLOG}" 
            # Forcefully kill all processes in process group.
            kill -KILL -$(ps -o pgid= $pid | grep -o '[0-9]*') >/dev/null 2>&1
        fi
        dt=$(date)
        echo "${dt} stopped stcapi session service" >> "${OUTLOG}"
	    else
        echo "pidfile exists but ${name} not running"  >> "${OUTLOG}" 
    fi 
    rm -f -- $PIDPATH
elif [ ! ${starting+x} ]
then
    echo "${name} no longer running"  >> "${OUTLOG}"
fi


