#!/bin/bash

sudo /etc/init.d/ssh restart

export WORKSPACE=`pwd`
export TEST=$WORKSPACE/Integration/tools/docker/funcp
export LC_ALL=C

echo "Workspace : $WORKSPACE"

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -f|--funcp)
    FUNCPBR="$2"
    shift # past argument
    shift # past value
    ;;
    -o|--funos)
    FUNOSBR="$2"
    shift # past argument
    shift # past value
    ;;
    -n|--nutest)
    NUTEST="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

sudo rm -rf FunSDK-cache funnel-as sonic-swss-common qemu_image FunOS FunControlPlane FunSDK psim* nv* tra*

git clone -b $FUNCPBR git@github.com:fungible-inc/FunControlPlane.git
git clone -b $FUNOSBR git@github.com:fungible-inc/FunOS.git
git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK

if [ "$NUTEST" != "default" ]; then
    echo "came here"
    cp $NUTEST $WORKSPACE/FunControlPlane/networking/asicd/libnu/test/
fi

cd $WORKSPACE/FunSDK
scripts/bob --sdkup
cd $WORKSPACE/FunSDK/integration_test
lib/build_setup.py

echo "Container UP. Idling now"
while [ 1 ]
    do
        sleep 1
    done
