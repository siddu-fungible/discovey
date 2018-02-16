#!/bin/bash

sudo /etc/init.d/ssh restart

export WORKSPACE=`pwd`
export TEST=$WORKSPACE/Integration/tools/docker/funcp
export LC_ALL=C

echo "Workspace : $WORKSPACE"

echo "Clone FunControlPlane and FunSDK Repo"
sudo rm -rf funnel-as sonic-swss-common qemu_image FunControlPlane FunSDK
git clone git@github.com:fungible-inc/FunControlPlane.git
git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK
cd $WORKSPACE/FunSDK
scripts/bob --sdkup

#cd $WORKSPACE/FunControlPlane
#./scripts/nutest/test_l3_traffic -l
#sudo -E python scripts/nutest/test_l3_traffic.py -n 12 -p -b -s > $WORKSPACE/nutest.log 2>&1
#./scripts/nutest/test_l3_traffic.py --traffic -n12 --testcase prv.PrvTest_fpg_simple_tcp 
#./scripts/nutest/test_l3_traffic.py --traffic -n12 --testcase prv  > $WORKSPACE/parser.log 2>&1
#sudo -E python scripts/nutest/test_l3_traffic.py -n 12 --kill

echo "Container UP. Idling now"
while [ 1 ]
    do
        sleep 1
    done
