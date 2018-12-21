#!/bin/bash

sudo /etc/init.d/ssh restart

export WORKSPACE=`pwd`
export TEST=$WORKSPACE/Integration/tools/docker/funcp
export LC_ALL=C

echo "Workspace : $WORKSPACE"

echo "Clone FunControlPlane, FunOS and FunSDK Repos"
sudo rm -rf FunSDK-cache funnel-as sonic-swss-common qemu_image FunOS FunControlPlane FunSDK
git clone git@github.com:fungible-inc/FunControlPlane.git
git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK
git clone git@github.com:fungible-inc/FunOS.git
cd $WORKSPACE/FunSDK
scripts/bob --sdkup
cd $WORKSPACE/FunSDK/integration_test
lib/build_setup.py

echo "Container UP. Idling now"
while [ 1 ]
    do
        sleep 1
    done
