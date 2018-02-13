#!/bin/bash

set -e
usage()
{
    echo "Usage: startup.sh <build url>"
}

curl_fetch()
{
    url=$1
    echo "Fetching $url"
    curl_output=`sudo curl -w 'httpcode=%{http_code}\n' $url -O`
    if [[ $curl_output == *"httpcode=200"* ]]; then
        echo "Fetched $url"
    else
        echo "Fetch failed for $url"
        exit 1
    fi
}

if [ $# -ne 1 ]; then
    usage
    exit 1
fi

cd /opt/fungible/downloads
dochub_fungible_local=10.1.20.99
base_url=$1
funos_url=$base_url/funos/latest/funos.tgz
funcp_url=$base_url/funcontrolplane/latest/functrlp.tgz
dpcsh_url=$base_url/funos/latest/dpcsh
qemu_url=$base_url/funos/latest/qemu.tgz
pcbios_url=$base_url/funos/latest/pc-bios.tgz
modules_url=$base_url/fungible-host-drivers/latest/x86_64/modules.tgz


echo "Base URL: $base_url"
echo "FunOS URL: $funos_url"
echo "Dpsch URL: $dpcsh_url"
echo "FunCP URL: $funcp_url"
echo "Qemu URL: $qemu_url"
echo "PC Bios URL: $pcbios_url"
echo "Modules URL: $modules_url"

arr=($dpcsh_url $funos_url $funcp_url $qemu_url $pcbios_url $modules_url)
for url in "${arr[@]}"
    do
        curl_fetch $url
    done

echo "Fetched all files"

echo "---------------------"
echo "Setting up qemu files"
echo "---------------------"
sudo tar -xvzf qemu.tgz  -C ../bin/qemu/
sudo tar -xvzf pc-bios.tgz -C ../bin/qemu/ 
sudo chmod -R 777 ../bin/qemu 

echo "----------------------"
echo "Setting up funos files"
echo "----------------------"
sudo tar -xvzf funos.tgz 
sudo mv build/funos-posix ../bin/funos/ 
sudo rm -rf build

echo "----------------------"
echo "Setting up dpcsh files"
echo "----------------------"
sudo chmod 777 dpcsh
sudo mv dpcsh ../bin/dpcsh

echo "----------------------"
echo "Setting up funcp files"
echo "----------------------" 
sudo tar -xvzf functrlp.tgz
sudo mv build/posix/bin/* ../bin/funcp
sudo mv build/posix/lib/* ../lib/
sudo rm -rf build

echo "------------------------"
echo "Cleanup Downloaded files"
echo "------------------------"
sudo rm -rf *

echo "Setup is complete"
echo "Idling forever"
while [ 1 ]
    do
        sleep 1
    done
