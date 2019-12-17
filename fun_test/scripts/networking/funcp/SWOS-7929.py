import sys
import os
#sys.path.append('/workspace/Integration/fun_test')
#/usr/bin/python
from lib.system.fun_test import *
from lib.host.linux import Linux
from StringIO import StringIO
import random
from lib.system.fun_test import *
from lib.system import utils
from lib.fun.fs import Fs
import re
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from collections import OrderedDict, Counter
from scripts.networking.helper import *
import ipaddress
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform

fs = 'fs-39'
f1 = 'f11'
host = 'mpoc-server06'
host_intf = 'enp216s0'
num_vols = 2
ipconfig = 1
ipcfg_port = 1099
command_timeout = 5
blt_capacity = 107374182400
blt_blk_size = 4096
fabric_transport = "tcp"
nvme_io_queues = 16



# Connect to FS-come
fs_come = fs.replace("-", "") + "-come"
fs_come_handle = Linux(host_ip=fs_come, ssh_username="fun", ssh_password="123")
if f1 == 'f10':
    f1_handle = StorageController(target_ip=fs_come, target_port=42220)
    docker = 'F1-0'
else:
    f1_handle = StorageController(target_ip=fs_come, target_port=42221)
    docker = 'F1-1'
f1_loopback_ip = fs_come_handle.command("docker exec -it %s ifconfig vlan1 | "
                                                              "grep -e 'inet ' | awk -F ' ' '{print $2}'" %(docker))
f1_loopback_ip = f1_loopback_ip.strip()
ipaddress.ip_address(unicode(f1_loopback_ip))

params = {
    'drives' : [],
    'volumes' : {
        'device': [],
        'uuid' : [],
    },
    'controllers': {
        'nqn' : [],
        'uuid':  [],
    },
    'host_ips' : [],
    'nsid' : {}
}
# Connect to the host
host_handle = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
host_ip = host_handle.command(
                "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".format(
                    host_intf)).strip()

params['host_ips'].append(host_ip)
# Create storage listener

#if ipconfig:
#    command_result = f1_handle.ip_cfg(ip=f1_loopback_ip, port=ipcfg_port)
#    fun_test.simple_assert(command_result["status"], "IPCFG on F1")

# Get drive info
drive_dict = f1_handle.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/drives",
                                                     command_duration=command_timeout)
params['drives'] = sorted(drive_dict["data"].keys())

# Create 2 BLT volumes
for x in range(0,num_vols):
    vol_id = utils.generate_uuid()
    drive = params['drives'][x]
    vol_name = 'blt' + str(x)
    params['volumes']['uuid'].append(vol_id)
    params['volumes']['device'].append(params['drives'][x])

    command_result = f1_handle.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                      capacity=blt_capacity,
                                                                      block_size=blt_blk_size,
                                                                      name=vol_name,
                                                                      uuid=vol_id,
                                                                      drive_uuid=drive,
                                                                      command_duration=command_timeout)
    fun_test.test_assert(command_result["status"], "Creation of BLT_{} on F1".format(x))


# Create 1 NVME/TCP controller
ctrl_uuid = utils.generate_uuid()
nqn_name = 'nqn01'
params['controllers']['uuid'].append(ctrl_uuid)
params['controllers']['nqn'].append(nqn_name)
command_result = f1_handle.create_controller(
    ctrlr_uuid=ctrl_uuid,
    transport=fabric_transport.upper(),
    remote_ip=params['host_ips'][0],
    port=ipcfg_port,
    nqn=nqn_name,
    command_duration=command_timeout)
fun_test.test_assert(command_result["status"], "F1 Create of fabric controller {} to remote {}".
                     format(str(nqn_name), params['host_ips'][0]))

# Attach the first volume to the NVME/TCP controller
ns_id = 9
command_result = f1_handle.attach_volume_to_controller(
    ctrlr_uuid=params['controllers']['uuid'][0],
    ns_id=ns_id,
    vol_uuid=params['volumes']['uuid'][0],
    command_duration=command_timeout)
fun_test.test_assert(command_result["status"], "Attach vol_{}".format(str(ns_id)))

# Do nvme connect from the host
# NMVe connect from x86 server to FS
host_handle.modprobe("nvme_tcp")
check_nvmetcp = host_handle.lsmod("nvme_tcp")
fun_test.sleep("Waiting for load to complete", 2)
if not check_nvmetcp:
    fun_test.critical("nvme_tcp load failed on host")

host_handle.sudo_command("nvme connect -t {} -n {} -a {} -q {} -i {} -s {}".
                                        format(fabric_transport.lower(),
                                               params['controllers']['nqn'][0],
                                               f1_loopback_ip,
                                               host_ip,
                                               nvme_io_queues,
                                               ipcfg_port),
                                        timeout=90)

# Attach the second volume to the first controller
ns_id = 10
command_result = f1_handle.attach_volume_to_controller(
    ctrlr_uuid=params['controllers']['uuid'][0],
    ns_id=ns_id,
    vol_uuid=params['volumes']['uuid'][1],
    command_duration=command_timeout)
fun_test.test_assert(command_result["status"], "Attach vol_{}".format(str(ns_id)))



