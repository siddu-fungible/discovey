#!/bin/bash
set -e

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

dochub_fungible_local=10.1.20.99
dpcsh_tgz_url=
funos_tgz_url=
qemu_tgz_url=
modules_tgz_url=http://$dochub_fungible_local/doc/jenkins/fungible-host-drivers/latest/x86_64/modules.tgz
functrlp_tgz_url=http://$dochub_fungible_local/doc/jenkins/funcontrolplane/latest/functrlp_posix.tgz
sdk_url=
kernel_url=
host_os_tgz=host_os.tgz    
regex_tgz_url=

QEMU_TGZ_NAME=qemu.tgz
DPCSH_TGZ_NAME=dpcsh.tgz
FUNOS_TGZ_NAME=funos.posix-base.tgz
DPCSH_NAME=dpcsh
FUNOS_POSIX_NAME=funos-posix
QEMU_DIRECTORY=qemu
KERNEL_NAME=bzImage
REGEX_TGZ_NAME=Regex.re.tgz

while getopts d:f:q:m:c:s:h:k:r: name
do
    case $name in
    d)    dpcsh_tgz_url="$OPTARG";;
    f)    funos_tgz_url="$OPTARG";;
    q)    qemu_tgz_url="$OPTARG";;
    m)    modules_tgz_url="$OPTARG";;
    c)    functrlp_tgz_url="$OPTARG";;
    h)    dochub_fungible_local="$OPTARG";;
    s)    sdk_url="$OPTARG";;
    r)    regex_tgz_url="$OPTARG";;
    ?)    printf "Usage: %s: [-d dpcsh tgz url] [-f funos tgz url] [-q qemu tgz url] [-m modules tgz url] [-c functrlp tgz url] [-h dochub ip] [-s sdk url] [-r regex tgz url]\n" $0
          exit 2;;
    esac
done

if [ -z "$sdk_url" ]; then
    sdk_url=http://$dochub_fungible_local/doc/jenkins/funsdk/latest/Linux
    printf "SDK url: $sdk_url\n"
fi

if [ -z "$funos_tgz_url" ]; then
    funos_tgz_url=$sdk_url/$FUNOS_TGZ_NAME
fi

if [ -z "$qemu_tgz_url" ]; then
    qemu_tgz_url=$sdk_url/$QEMU_TGZ_NAME
fi

if [ -z "$dcpsh_tgz_url" ]; then
    dpcsh_tgz_url=$sdk_url/$DPCSH_TGZ_NAME
fi

if [ -z "$regex_tgz_url" ]; then
    regex_tgz_url=$sdk_url/$REGEX_TGZ_NAME
fi

if [ ! -z "$dpcsh_tgz_url" ]; then
    printf "DPCSH tgz url: $dpcsh_tgz_url\n"
    echo "----------------------"
    echo "Setting up dpcsh files"
    echo "----------------------"
    curl_fetch $dpcsh_tgz_url
    tar -xf $DPCSH_TGZ_NAME -C /tmp
    mv /tmp/bin/Linux/$DPCSH_NAME $DPCSH_NAME
    rm -rf /tmp/bin
    chmod 777 $DPCSH_NAME
fi

if [ ! -z "$funos_tgz_url" ]; then
    printf "FunOS tgz url: $funos_tgz_url\n"
    echo "----------------------"
    echo "Setting up funos files"
    echo "----------------------"
    curl_fetch $funos_tgz_url
    if [[ $fun_os_tgz_url =~ tgz ]]; then
        tar -xf $FUNOS_TGZ_NAME -C /tmp
        mv /tmp/bin/$FUNOS_POSIX_NAME $FUNOS_POSIX_NAME
        rm -rf /tmp/bin
    fi
    chmod 777 $FUNOS_POSIX_NAME
fi

if [ ! -z "$qemu_tgz_url" ]; then
    printf "QEMU tgz url: $qemu_tgz_url\n"
    echo "---------------------"
    echo "Setting up qemu files"
    echo "---------------------"
    curl_fetch $qemu_tgz_url
    tar -xvzf $QEMU_TGZ_NAME -C $QEMU_DIRECTORY
    qemu_linux_directory=$QEMU_DIRECTORY/qemu-Linux
    qemu_bin_directory=$qemu_linux_directory/bin
    QEMU_NAME=qemu-system-x86_64
    chmod 777 $qemu_bin_directory/$QEMU_NAME
    export PATH=$PATH:$qemu_bin_directory
fi

if [ ! -z "$regex_tgz_url" ]; then
    printf "Regex tgz url: $regex_tgz_url\n"
    curl_fetch $regex_tgz_url
    TMP_REGEX=/tmp/regex
    mkdir -p /tmp/regex
    tar -xvzf $REGEX_TGZ_NAME -C $TMP_REGEX
    cp $TMP_REGEX/bin/Linux/ffac `pwd`
    rm -rf $TMP_REGEX
    echo PATH=$PATH:`pwd` >> ~/.bashrc
fi

if [ ! -z "$host_os_tgz" ]; then
    printf "Host OS tgz: $host_os_tgz\n"
    echo "-------------------------"
    echo "Setting up Host OS"
    echo "-------------------------"
    tar -xvzf $host_os_tgz -C $QEMU_DIRECTORY
    rm $host_os_tgz
    echo "Done setting up Host OS"
fi


if [ ! -z "$modules_tgz_url" ]; then
    printf "Modules tgz url: $modules_tgz_url\n"
    curl_fetch $modules_tgz_url
fi

if [ ! -z "$functrlp_tgz_url" ]; then
    printf "Fun Ctrl plane tgz url: $functrlp_tgz_url\n"
    curl_fetch $functrlp_tgz_url
fi



echo "-------------------"
echo "Starting SSH server"
echo "-------------------"
/etc/init.d/ssh restart
echo "Started SSH Server"

echo "-----------------"
echo "Setup is complete"
echo "-----------------"

echo "Idling forever"
while [ 1 ]
    do
        sleep 1
    done

