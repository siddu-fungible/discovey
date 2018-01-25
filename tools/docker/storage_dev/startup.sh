#!/bin/bash

set -e
usage()
{
    echo "Usage: startup.sh <build url> <funos command line> True <delay>" 
}

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

if [ $# -lt 2 ]; then
    usage
    exit 1
fi
dochub_fungible_local=10.1.20.99
base_url=$1
dpcsh_name=dpcsh
dpcsh_url=$base_url/$dpcsh_name
funos_tgz_name=funos.tgz
funos_tgz_url=$base_url/$funos_tgz_name
qemu_name=qemu-system-x86_64
qemu_tgz_name=qemu.tgz
qemu_tgz_url=$base_url/$qemu_tgz_name
pcbios_tgz_name=pc-bios.tgz
pcbios_tgz_url=$base_url/$pcbios_tgz_name
modules_tgz_name=modules.tgz
modules_tgz_url=http://$dochub_fungible_local/doc/jenkins/fungible-host-drivers/latest/x86_64/modules.tgz
dpcsh_tcp_proxy_default_internal_port=5000

echo "Base URL: $base_url"
echo "Dpsch URL: $dpcsh_url"
echo "FunOS Tgz URL: $funos_tgz_url"
echo "Qemu Tgz URL: $qemu_tgz_url"
echo "PC Bios URL: $pcbios_tgz_url"
echo "Modules URL: $modules_tgz_url"


arr=($dpcsh_url $funos_tgz_url $qemu_tgz_url $pcbios_tgz_url $modules_tgz_url)
for url in "${arr[@]}"
    do
        curl_fetch $url
    done

echo "Fetched all files"

echo "---------------------"
echo "Setting up qemu files"
echo "---------------------"
qemu_directory=qemu/x86_64-softmmu
tar -xvzf $qemu_tgz_name -C qemu 
tar -xvzf $pcbios_tgz_name -C $qemu_directory
chmod 777 $qemu_directory/$qemu_name
export PATH=$PATH:$qemu_directory


echo "----------------------"
echo "Setting up funos files"
echo "----------------------"
funos_posix_name=funos-posix
tar -xf $funos_tgz_name build/$funos_posix_name
mv build/$funos_posix_name $funos_posix_name
rm -rf build
chmod 777 $dpcsh_name

if [ "$2" != "" ]; then
    echo "-------------------"
    echo "funos-posix command"
    echo "-------------------"
    dd if=/dev/zero of=nvfile bs=4096 count=256
    /$funos_posix_name app=mdt_test nvfile=nvfile &> /tmp/f1mdt.log
    $2 &> /tmp/f1.log &
    if [ "$3" == "True" ]; then
        echo "------------------------"
        echo "Starting Dpcsh tcp proxy"
        echo "------------------------"
        if [ "$4" == "" ]; then
            sleep 20
        else
            sleep $4
        fi
        cd /; ./dpcsh  --tcp_proxy $dpcsh_tcp_proxy_default_internal_port &> /tmp/dpcsh.log &
        sleep 5
    fi
fi



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

