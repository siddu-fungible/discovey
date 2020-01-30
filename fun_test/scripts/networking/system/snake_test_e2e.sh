#! /bin/bash
set -x
#
# This script is for setting up a snake test env.
# Move this file to /opt/fungible/cclinux/snake_test.sh

FUNGIBLE_ROOT=${FUNGIBLE_ROOT:-/opt/fungible}

#
# Assume bundle image just unpacked and control plane dockers are started
#

cd ${FUNGIBLE_ROOT}/cclinux
SUDO=""
if [ $(id -u) != 0 ]; then
    SUDO="sudo"
fi

#
# Step 1: Stop all control plane dockers for snake test.
#
./cclinux_service.sh --stop

#
# Step 2: start funeth and libfunq
# Assume udev rules are installed during bundling init
#
./handle_funeth_driver_on_fs1600.sh --bind $FUNGIBLE_ROOT/drivers
if [ $? -ne 0 ]; then
    echo "Failed to install funeth driver"
    exit 1
fi
./handle_libfunq_on_fs1600.sh --bind $FUNGIBLE_ROOT/FunControlPlane/bin
if [ $? -ne 0 ]; then
    echo "Failed to bind libfunq"
    exit 1
fi

#
# Step 3: Start 4 dockers for snake test
# Four dockers are F1-0-fgp0, F1-0-fpg20, F1-1-fpg0, F1-1-fpg20
#
./start_f1_docker.py  -s snake_test_startup.sh --name F1-0-fpg0
./start_f1_docker.py  -s snake_test_startup.sh --name F1-0-fpg20
./start_f1_docker.py  -s snake_test_startup.sh --name F1-1-fpg0
./start_f1_docker.py  -s snake_test_startup.sh --name F1-1-fpg20


#
# Step 4: Move interfaces into dockers
#
#$SUDO ./move_interface_to_docker.sh F1-0-fpg0 f0fpg0 $FUNGIBLE_ROOT/logs/snake_test_F1-0-fpg0.log "skipirb"
#$SUDO ./move_interface_to_docker.sh F1-0-fpg20 f0fpg20 $FUNGIBLE_ROOT/logs/snake_test_F1-0-fpg20.log "skipirb"
#$SUDO ./move_interface_to_docker.sh F1-1-fpg0 f1fpg0 $FUNGIBLE_ROOT/logs/snake_test_F1-1-fpg0.log "skipirb"
#$SUDO ./move_interface_to_docker.sh F1-1-fpg20 f1fpg20 $FUNGIBLE_ROOT/logs/snake_test_F1-1-fpg20.log "skipirb"

