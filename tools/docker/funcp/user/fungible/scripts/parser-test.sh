#!/bin/bash

sudo /etc/init.d/ssh restart

export WORKSPACE=`pwd`
export TEST=$WORKSPACE/Integration/tools/docker/funcp
echo "Workspace : $WORKSPACE"

if [ ! -d "frr" ]; then
    git clone --branch fungible/master git@github.com:fungible-inc/frr.git
    echo "Download FRR source"
fi

if [ ! -d "FunControlPlane" ]; then
    git clone git@github.com:fungible-inc/FunControlPlane.git
    echo "Download FunControlPlane source"
fi

#
# Compile FunControl Plane
#
cd FunControlPlane
make cleanall
make -j 2 

echo "#########"
echo "Run PARSER tests"
echo "#########"

cd $WORKSPACE/FunControlPlane
sudo -E python scripts/nutest/test_l3_traffic.py -n 12 -p --setuponly
#./scripts/nutest/test_l3_traffic.py --traffic -n12 --testcase prv.PrvTest_fpg_simple_tcp 
./scripts/nutest/test_l3_traffic.py --traffic -n12 --testcase prv
sudo -E python scripts/nutest/test_l3_traffic.py -n 12 --kill

echo "Testing Completed"
while [ 1 ]
    do
        sleep 1
    done
