#! /bin/bash

GREPUSER=${1:-abc}
MINUTES=${2:-5}
EMAIL=${3:-parag.manjrekar@fungible.com}

echo "filter: $GREPUSER, $MINUTES, $EMAIL"

TIMES=$(/project/tools/cadence/installs/VXE18.50.009/tools.lnx86/bin/test_server | grep $GREPUSER | awk '{print $7}' | sort | uniq)

for T in $TIMES; do
    IFS=":"; read H M S <<< "$T";
    SPENT=$(((H)*60 + M))
    echo "$GREPUSER spent ($H:$M) or $SPENT minutes uptill now ..."
    if [ "$SPENT" -gt "$MINUTES" ]; then
        SUBJECT="ALERT !! $GREPUSER !! You have spend $SPENT minutes on palladium (limit=$MINUTES). Please kill session !!"
        echo "$GREPUSER spent $SPENT minutes on palladium setups. (limit=$MINUTES)..." | mailx -s "$SUBJECT" $EMAIL && echo "Sending email... Done."
    fi
done
