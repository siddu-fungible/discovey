#!/bin/bash

export WORKDIR=~/fungible
export FRR=$WORKDIR/frr
export DOCKER=$WORKDIR/Integration/tools/docker/frr

if [ $1 == 'init' ]
then
  sudo apt-get update
  sudo apt-get install -y git autoconf automake libtool make gawk libreadline-dev \
	                  texinfo dejagnu pkg-config libpam0g-dev libjson-c-dev \
			  bison flex python-pytest libc-ares-dev python3-dev
   sudo groupadd -g 92 frr
   sudo groupadd -r -g 85 frrvty
   sudo adduser --system --ingroup frr --home /var/run/frr/ \
	        --gecos "FRR suite" --shell /sbin/nologin frr
   sudo usermod -a -G frrvty frr
   docker_image=$2
else
   docker_image=$1
fi

echo "Building FRR...."

cd $FRR 
sudo ./bootstrap.sh
sudo ./configure \
	 --prefix=/usr \
	 --localstatedir=/var/run/frr \
	 --sbindir=/usr/lib/frr \
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
	 --enable-ldpd \
	 --with-pkg-git-version \
	 --with-pkg-extra-version=-MyOwnFRRVersion   

sudo make
sudo make install

echo "Done building FRR. Creating FRR Docker image"

cp -r /usr/lib/frr/* $DOCKER/bin/
cp /usr/bin/vtysh $DOCKER/bin/
cp -r /usr/lib/libfrr* $DOCKER/frr_lib/
cp -r /lib/x86_64-linux-gnu/* $DOCKER/libs/

cd $DOCKER
sudo docker build -t $docker_image .

echo "Docker image $docker_image built" 
