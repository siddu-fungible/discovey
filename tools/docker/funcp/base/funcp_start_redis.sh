#!/bin/bash

#
# This script is run inside the docker as a startup script to start
# redis server
#
export WORKSPACE=`pwd`
echo "Workspace : $WORKSPACE"
SUDO=''
if (( $EUID != 0 )); then
    SUDO='sudo'
fi

# TODO check if binary is changed. if so, update the prebuilt version
# $SUDO cp $WORKSPACE/build/posix/lib/libfunjson_redis.so /usr/local/lib/
#

DOCKER_REDIS_LOC=/fun_external/redis
if [ -f /var/run/redis_6379.pid ]; then
    $SUDO rm -rf /var/run/redis_6379.pid
fi

## Start redis server when entering docker
if (( $EUID != 0 )); then
$SUDO   REDIS_PORT=6379 \
    REDIS_CONFIG_FILE=/etc/redis/redis.conf \
    REDIS_LOG_FILE=/var/log/redis.log \
    REDIS_DATA_DIR=/var/lib/redis/6379 \
    REDIS_EXECUTABLE=`command -v redis-server` $DOCKER_REDIS_LOC/utils/install_server.sh
else
    REDIS_PORT=6379 \
    REDIS_CONFIG_FILE=/etc/redis/redis.conf \
    REDIS_LOG_FILE=/var/log/redis.log \
    REDIS_DATA_DIR=/var/lib/redis/6379 \
    REDIS_EXECUTABLE=`command -v redis-server` $DOCKER_REDIS_LOC/utils/install_server.sh
fi

/bin/bash
