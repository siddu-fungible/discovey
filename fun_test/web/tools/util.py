import os
import time
import subprocess
from netaddr import IPNetwork
from config import *

#docker_images = {'leaf': 'frr:v2', 'spine': 'frr:v2' , 'traffic_gen': 'tgen:v1'}
docker_images = {'leaf': leaf_container, 'spine': 'frr:v2' , 'traffic_gen': 'tgen:v2'}
docker_run_cmd = "docker run --privileged=true --rm -d"
docker_stop_cmd = "docker stop "
docker_kill_cmd ='docker kill '
docker_remove_cmd = 'docker rm '
docker_pause_cmd = 'docker pause '
docker_unpause_cmd = 'docker unpause '
docker_pid_cmd = "docker inspect -f '{{.State.Pid}}'"
docker_network_cmd = "docker inspect bridge"
docker_mnt_clean_cmd = ['rm -rf /var/lib/docker/aufs/diff/*/nvfile', 'rm -rf /var/lib/docker/aufs/mnt/*/nvfile', 'rm -rf /var/lib/docker/aufs/diff/*/nvme_disk*', 'rm -rf /var/lib/docker/aufs/mnt/*/nvme_disk*']
docker_swarm_init_cmd = 'docker swarm init'
docker_swarm_leave_cmd = 'docker swarm leave'
docker_swarm_leave_force_cmd = 'docker swarm leave --force'
docker_mgmt_net_cmd = 'docker network create --driver overlay --attachable --subnet=172.16.0.0/16 mgmt'
netns_del_cmd = "ip netns del "
ovs_del_br_cmd = 'ovs-vsctl del-br '
frr_password = 'zebra'
storage_create_file_cmd = 'dd if=/dev/zero of=nvfile bs=1024k count=1k'
storage_mdt_test_cmd = 'funos-posix app=mdt_test nvfile=nvfile'
storage_nvmeof_cmd = 'nohup funos-posix app=nvmeof_target localaddr=0x0A000104 remoteaddr=0x0A000102  --dpc-server > /dev/null 2>&1 &'
storage_fio_verify = 'fio --name=fun_nvmeof --ioengine=fun --rw=write --bs=4k --size=12m --numjobs=1  --iodepth=8 --do_verify=1 --verify=md5 --verify_fatal=1 --group_reporting -source_ip=10.0.1.2 --dest_ip=10.0.1.4 --io_queues=4 --nrfiles=1 --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=FULL_TEST'
storage_fio_noverify = 'fio --name=fun_nvmeof --ioengine=fun --rw=randrw --bs=4k --size=1m --numjobs=1  --iodepth=8 --group_reporting -source_ip=172.16.0.5 --dest_ip=172.16.0.13 --io_queues=4 --nrfiles=1 --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=FULL_TEST'
etc_orig = '/etc/hosts-orig'
etc_curr = '/etc/hosts'
base_port = 10000
iid = 1
ssh_retries = 10

max_containers_per_leaf_vm = 32.0 
max_links_per_spine_vm = 128.0 
max_ports_per_ovs = 1850.0

spine_lo_net = '192.170.0.0/16'
public_net = '10.0.0.0/14'
f1_spine_net= '192.100.0.0/13'
inter_f1_net = '192.168.0.0/16'
f1_mgmt_net= IPNetwork('172.16.0.0/16')

spine_lo_subnets = [] 
f1_public_subnet = []
rack_subnets = []
spine_subnets = []
f1_mgmt_ips = []

def get_next_id():
    global iid
    res = iid
    iid += 1
    return res

def create_ip_prefix_list(name, action, prefix):
    ip_prefix_list = 'ip prefix-list ' + name + ' ' + action + ' ' + prefix + '\n'
    return ip_prefix_list

def create_ip_community_list(name, action, community):
    ip_community_list = 'ip community-list expanded ' + name + ' ' + action + ' ' + community + '\n'
    return ip_community_list

def create_route_map(name, community):
    if name == 'REMOTE_RACK_RMAP_IN':
        route_map = 'route-map ' + name + ' permit 10 \n'
        route_map += '   match ip address prefix-list REMOTE_RACK_PREFIX_MATCH_ALL \n'
        route_map += '      set community ' + community + '\n'
    elif name == 'REMOTE_RACK_RMAP_IBGP_OUT':
        route_map = 'route-map ' + name + ' permit 10 \n'
        route_map += '   match community FILTER_E_I \n'
        route_map += '      set community ' + community + '\n'
        route_map += 'route-map ' + name + ' permit 20 \n'
        route_map += ' match ip address prefix-list REMOTE_RACK_PREFIX_MATCH_ALL \n'
    elif name == 'REMOTE_RACK_RMAP_OUT':
        route_map = 'route-map ' + name + ' deny 10 \n'
        route_map += '   match community FILTER_E_I_E \n'
        route_map += ' route-map REMOTE_RACK_RMAP_OUT permit 20 \n'
        route_map += '   match ip address prefix-list REMOTE_RACK_PREFIX_MATCH_ALL \n'
    else:
        return ''

    return route_map


def create_ssh_config(config_str):

    homefolder = os.path.expanduser('~')
    ssh_config_file = os.path.abspath('%s/.ssh/config' % homefolder)

    fp = open(ssh_config_file, 'w')

    fp.write(config_str)
    fp.close()

def convert_ip_to_48bits(ip_addr):
    ip = ''.join([ip.zfill(3) for ip in ip_addr.split('.')])
    chunks, chunk_size = len(ip), len(ip)/3 
    return '.'.join([ ip[i:i+chunk_size] for i in range(0, chunks, chunk_size) ])
    
def run_commands(host_linux=None, commands=None, sleep=0):

    start_time = time.time()
    processes = []
    results = []

    if host_linux:
        for command in commands:
            if command:
                #res = host_linux.command(command, timeout=180, wait_until_timeout=180)
                stdin,stdout,stderr = host_linux.exec_command(command)
                res = stdout.readlines()
                if res:
                    if len(res) == 1:
                        res = res[0].strip() 
                    else:
                        res = '\n'.join(res) 
                results.append(dict(output=res, command=command))
                time.sleep(sleep)

        return dict(start=start_time, end=time.time(), results=results)
    else:
        for command in commands:
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            processes.append((proc, command))


        for proc, command in processes:
            out, error = proc.communicate()
            results.append(dict(output=out, error=error, command=command))
            time.sleep(sleep)

        return dict(start=start_time, end=time.time(), results=results)

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result
    return timed
