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

#/fun_external/funcp_start_redis.sh
#sudo cp $WORKSPACE/FunControlPlane/build/posix/lib/* /opt/fungible/lib/
#sudo cp $WORKSPACE/FunControlPlane/build/posix/bin/* /opt/fungible/bin/funcp/
#sudo /opt/fungible/sbin/frr/frr start

#
# Run Integration Test
#
cd ../FunControlPlane
sudo -E ./networking/test/integration/test_l3_integration.py -p -l 
# ./scripts/nutest/test_l3_traffic -p
# Run Parser Tests
#

#cd $WORKSPACE/FunControlPlane
#sudo -E python scripts/nutest/test_l3_traffic.py -n 12 --setuponly
#./scripts/nutest/test_l3_traffic.py --traffic -n12 --testcase prv
#sudo -E python scripts/nutest/test_l3_traffic.py -n 12 --kill

echo "Testing Completed"
while [ 1 ]
    do
        sleep 1
    done
