#!/bin/bash

set -e
curl_fetch()
{
    url=$1
    echo "Fetching $url"
    curl_output=`curl -w 'httpcode=%{http_code}\n' $url -O`
    if [[ $curl_output == *"httpcode=200"* ]]; then
        echo "Fetched $url"
    else
        echo "Fetch failed for $url"
        exit 1
    fi
}

aflag=
bflag=
while getopts ab: name
do
    case $name in
    a)    aflag=1;;
    b)    bflag=1
          bval="$OPTARG";;
    ?)    printf "Usage: %s: [-a] [-b value] args\n" $0
          exit 2;;
    esac
done
if [ ! -z "$aflag" ]; then
    printf "Option -a specified\n"
fi
if [ ! -z "$bflag" ]; then
    printf 'Option -b "%s" specified\n' "$bval"
fi
shift $(($OPTIND - 1))
printf "Remaining arguments are: %s\n" "$*"

echo "-------------------"
echo "Starting SSH server"
echo "-------------------"
/etc/init.d/ssh restart
echo "Started SSH Server"

echo "Setup is complete"
echo "Idling forever"
while [ 1 ]
    do
        sleep 1
    done


