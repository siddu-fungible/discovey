#!/bin/bash
set -e

funos_url=$1
action=$2
resource_name="funos-posix"
echo "Fetching $resource_name from $funos_url"

curl_output=`curl -w 'httpcode=%{http_code}\n' $funos_url -O`
if [[ $curl_output == *"httpcode=200"* ]]; then
    echo "Fetched $resource_name"
    chmod 777 $resource_name
else
    echo "Fetch failed for $funos_url"
    exit 1
fi

echo "Starting SSH server"
/etc/init.d/ssh restart
echo "Started SSH Server"

echo "Adding QEMU to PATH"
export PATH=$PATH:./qemu

if [[ $action == *test* ]]; then
    echo "Testing: dd"
    dd if=/dev/zero of=nvfile bs=4096 count=256
    echo "Testing ulimit"
    ulimit -Sc unlimited
    echo "mdt_test"
    ./funos-posix app=mdt_test nvfile=nvfile
    echo "prem_test"
    nohup //funos-posix app=prem_test nvfile=nvfile &>/dev/null &
    sleep 60
    echo "start_qemu"
    cd qemu
    ./qemu-system-x86_64 -L pc-bios -daemonize -machine q35 -m 256  -device nvme-rem-fe,sim_id=0   -redir tcp:2220::22  -drive file=core-image-full-cmdline-qemux86-64.ext4,if=virtio,format=raw -kernel bzImage -append 'root=/dev/vda rw ip=:::255.255.255.0:qemu-yocto:eth0:on mem=256M oprofile.timer=1'

fi


echo "Idling forever"
while [ 1 ]
	do
		sleep 1
	done
