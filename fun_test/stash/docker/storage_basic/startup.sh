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
    curl_output=`curl -w 'httpcode=%{http_code}\n' $url -O`
    if [[ $curl_output == *"httpcode=200"* ]]; then
        echo "Fetched $resource_name"
    else
        echo "Fetch failed for $url"
        exit 1
    fi
}

if [ $# -ne 1 ]; then
    usage
    exit 1
fi
base_url=$1
dpcsh_name=dpcsh
dpcsh_url=$base_url/$dpcsh_name
funos_tgz_name=funos.tgz
funos_tgz_url=$base_url/$funos_tgz_name
qemu_name=qemu-system-x86_64
qemu_tgz_name=qemu.tgz
qemu_url=$base_url/$qemu_tgz_name
pcbios_tgz_name=pc-bios.tgz
pcbios_tgz_url=$base_url/$pcbios_tgz_name

echo "Base URL: $base_url"
echo "Dpsch URL: $dpcsh_url"
echo "FunOS Tgz URL: $funos_tgz_url"
echo "Qemu Tgz URL: $qemu_url"
echo "PC Bios URL: $pcbios_tgz_url"


arr=($dpcsh_url $funos_tgz_url $qemu_url $pcbios_tgz_url)
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
