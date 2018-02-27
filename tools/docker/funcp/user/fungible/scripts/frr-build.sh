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

if [ ! -d "FunSDK" ]; then
   git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK
   echo "Download FunSDK source"
   cd FunSDK
   sudo scripts/bob --sdkup
fi

#
# Compile FunControl Plane
#
cd $WORKSPACE/FunControlPlane
make cleanall
make -j 2 
#
# Compile FRR
#
cd ../frr
./bootstrap.sh
./configure \
              --prefix=/opt/fungible \
              --enable-exampledir=/opt/fungible/share/doc/frr/examples/ \
              --localstatedir=/var/run/frr \
              --bindir=/opt/fungible/bin/frr \
              --sbindir=/opt/fungible/sbin/frr \
              --sysconfdir=/etc/frr \
              --enable-pimd \
              --enable-watchfrr \
              --enable-multipath=64 \
              --enable-user=frr \
              --enable-group=frr \
              --enable-vty-group=frrvty \
              --enable-configfile-mask=0640 \
              --enable-logfile-mask=0640 \
              --enable-rtadv \
              --enable-fpm \
              --enable-systemd=yes \
              --with-pkg-git-version \
              --disable-nhrpd \
              --with-pkg-extra-version=-MyOwnFRRVersion
make
sudo make install

sudo install -m 755 -o frr -g frr -d /var/log/frr
sudo install -m 775 -o frr -g frrvty -d /etc/frr
sudo install -m 755 -o frr -g frr /dev/null /var/log/frr/bgpd.log
sudo install -m 755 -o frr -g frr /dev/null /var/log/frr/isisd.log
sudo install -m 755 -o frr -g frr /dev/null /var/log/frr/zebra.log
sudo install -m 640 -o frr -g frr /dev/null /etc/frr/zebra.conf
sudo install -m 640 -o frr -g frr /dev/null /etc/frr/bgpd.conf
sudo install -m 640 -o frr -g frr /dev/null /etc/frr/isisd.conf
sudo install -m 640 -o frr -g frrvty /dev/null /etc/frr/vtysh.conf
sudo sed -i 's/#net.ipv4.ip_forward=./net.ipv4.ip_forward=1/g' /etc/sysctl.conf
sudo chown frr:frrvty /etc/frr/zebra.conf /etc/frr/bgpd.conf /etc/frr/isisd.conf
sudo cp $WORKSPACE/FunControlPlane/build/posix/lib/* /opt/fungible/lib/
sudo cp $WORKSPACE/FunControlPlane/build/posix/bin/* /opt/fungible/bin/funcp/
sudo cp /opt/fungible/scripts/frr /opt/fungible/sbin/frr/frr
sudo cp /opt/fungible/conf/* /etc/frr/
sudo cp /opt/fungible/conf/frr /etc/default/frr
sudo chown -R frr:frrvty /etc/frr
sudo chown frr:frrvty /etc/default/frr
sudo chown -R frr:frrvty /opt/fungible/sbin/frr
sudo /opt/fungible/sbin/frr/frr start

#
# Run Integration Test
#
#cd ../FunControlPlane
#sudo -E ./networking/test/integration/test_l3_integration.py -p 
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
