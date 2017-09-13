#!/bin/bash
set -e

startup_log_file="startup_log_file.log"
funos_log_file="funos.log"
qemu_log_file="qemu.log"

log()
{
    message=$1
    echo "STARTUP: $message"
}
startup_sleep()
{
    sleep_time=$1
    log "Sleeping $sleep_time"
    sleep $sleep_time

}

##### Start FunOS
log "Starting FunOS"
nohup ./funos-posix app=prem_test nvfile=nvfile &> $funos_log_file &
startup_sleep 60


##### Start QEMU
log "List sockets"
ls /tmp/*sock &> $startup_log_file || true
log "List funos process"
ps -ef | grep fun &> $startup_log_file || true
log "Starting QEMU"
nohup ./qemu-system-x86_64 ubuntu_min.img -machine q35 -smp 1 -m 2048 -device nvme-rem-fe,sim_id=0 -redir tcp:2220::22 -nographic -enable-kvm &> $qemu_log_file &
startup_sleep 60


##### Shutdown tap interface
log "Shutting down tap interface, to remove 10.x routes"
ifconfig tap down &> $funos_log_file || true


##### Idle
log "Idling"
startup_sleep 3600