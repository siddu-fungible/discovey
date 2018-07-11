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

#sudo rm -rf FunSDK-cache funnel-as sonic-swss-common qemu_image FunOS FunControlPlane FunSDK psim* nv* tra*
sudo rm -rf psim* nv* tra*

if [ $FUNCPBR ]; then
    echo ">>>> Cloning FunCP branch: $FUNCPBR"
    sudo rm -rf $WORKSPACE/FunControlPlane
    git clone -b $FUNCPBR git@github.com:fungible-inc/FunControlPlane.git
else
    if [ ! -d $WORKSPACE/FunControlPlane ]; then
        echo ">>>> Cloning FunCP Master"
        git clone git@github.com:fungible-inc/FunControlPlane.git
    else
        echo ">>>> Updating FunCP from Master: $FUNCPBR"
        cd $WORKSPACE/FunControlPlane
        git stash
        git pull
        cd $WORKSPACE
    fi
fi
if [ $FUNOSBR ]; then
    echo ">>>> Cloning FunOS branch: $FUNOSBR"
    sudo rm -rf $WORKSPACE/FunOS
    git clone -b $FUNOSBR git@github.com:fungible-inc/FunOS.git
else
    if [ ! -d $WORKSPACE/FunOS ]; then
        echo ">>>> Cloning FunOS Master"
        git clone git@github.com:fungible-inc/FunOS.git
    else
        echo ">>>> Updating FunOS from Master"
        cd $WORKSPACE/FunOS
        git stash
        git pull
        cd $WORKSPACE
    fi
fi

if [ ! -d $WORKSPACE/FunSDK ]; then
    echo ">>>> Cloning FunSDK Master"
    git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK
else
    echo ">>>> Updating FunSDK from Master"
    cd $WORKSPACE/FunSDK
    git stash
    git pull
    cd $WORKSPACE
fi

if [ ! -d $WORKSPACE/fungible-host-drivers ]; then
    echo ">>>> Cloning FunHostDrivers Master"
    git clone git@github.com:fungible-inc/fungible-host-drivers.git
else
    echo ">>>> Updating FunHostDrivers from Master"
    cd $WORKSPACE/fungible-host-drivers
    git stash
    git pull
    cd $WORKSPACE
fi

if [ "$NUTEST" ]; then
    echo ">>>>>>>>>>>>copying nutest.json"
    echo "cp $NUTEST $WORKSPACE/FunControlPlane/networking/asicd/libnu/test/"
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
