set -x

VERSION=${1:-7499}
DPU=${2:-0}
PCI=${3:-04:00.1}
DRYRUN=${4:-yes}

lspci -d1dad: | grep -F 1dad && echo "searching FUNGIBLE devices ..." || exit 1
lspci -d1dad: | grep -F "$PCI" && echo "searching FUNGIBLE device-and-function ..." ||  exit 1

PWD=$(pwd)

PID=$(basename $(mktemp))
DIR="$PWD/$PID"
VDIR="$PWD/$PID/$VERSION"

echo "Downloading images ..."

mkdir -p $VDIR
cd $DIR
wget -q http://vnc-shared-06.fungible.local:9669/my-github/FunSDK/integration_test/emulation/run_fwupgrade.py
wget -q http://dochub.fungible.local/doc/jenkins/funcontrolplane/latest/functrlp_palladium.tgz
tar xf functrlp_palladium.tgz

cd $VDIR
wget -q http://dochub.fungible.local/doc/jenkins/funsdk_flash_images/$VERSION/emmc_image.bin
wget -q http://dochub.fungible.local/doc/jenkins/funsdk_flash_images/$VERSION/eeprom_fs1600_0_packed.bin
wget -q http://dochub.fungible.local/doc/jenkins/funsdk_flash_images/$VERSION/eeprom_fs1600_1_packed.bin
wget -q http://dochub.fungible.local/doc/jenkins/funsdk_flash_images/$VERSION/host_firmware_packed.bin

cd $DIR
POSIXLIB="$DIR/build/posix-f1/lib"
POSIXBIN="$DIR/build/posix-f1/bin"

echo "bind library and utilities to pci function $PCI for DPU(index=$DPU) ..."
sudo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$POSIXLIB $POSIXBIN/funq-setup bind 'vfio' $PCI
echo "show current firmware images ..."
sudo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$POSIXLIB $POSIXBIN/fwupgrade -a -d $PCI

EEPR="$VDIR/eeprom_fs1600_${DPU}_packed.bin"
HOST="$VDIR/host_firmware_packed.bin"
EMMC="$VDIR/emmc_image.bin"

echo "upgrade EEPR image for ..."
[[ $DRYRUN == "yes" ]] || sudo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$POSIXLIB $POSIXBIN/fwupgrade --image $EEPR -f eepr -d $PCI

echo "upgrade HOST image for ..."
[[ $DRYRUN == "yes" ]] || sudo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$POSIXLIB $POSIXBIN/fwupgrade --image $HOST -f host -d $PCI

echo "upgrade EMMC image for ..."
[[ $DRYRUN == "yes" ]] || sudo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$POSIXLIB $POSIXBIN/fwupgrade --image $EMMC -f emmc -d $PCI

echo "UN bind library and utilities to pci function $PCI for DPU(index=$DPU) ..."
sudo LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:$POSIXLIB $POSIXBIN/funq-setup unbind 'vfio' $PCI
