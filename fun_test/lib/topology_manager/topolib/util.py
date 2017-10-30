import os
import time
import math
import subprocess
from netaddr import IPNetwork
from config import *

docker_images = {'leaf': leaf_container, 'spine': spine_container , 'traffic_gen': tg_container}
docker_restart_cmd = "service docker restart"
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
docker_swarm_net_cmd = 'docker network create --driver overlay --attachable --subnet=172.16.0.0/16 mgmt'
docker_mgmt_net_cmd = 'docker network create --subnet=172.16.0.0/16 mgmt' 
docker_del_mgmt_net_cmd = 'docker network rm mgmt'
docker_net_list_cmd = 'docker network ls -f name=mgmt'
netns_del_cmd = "ip netns del "
ovs_del_br_cmd = 'ovs-vsctl del-br '
psim_process_count = 'ps ax | grep load_mods | egrep -v grep | wc -l'
mkdir_netns_cmd = 'mkdir /var/run/netns'
rp_filter_all_cmd = 'echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter'
rp_filter_default_cmd = 'echo 0 > /proc/sys/net/ipv4/conf/default/rp_filter'
arp_ignore_all_cmd = 'echo 0 > /proc/sys/net/ipv4/conf/all/arp_ignore'
arp_ignore_default_cmd = 'echo 0 > /proc/sys/net/ipv4/conf/default/arp_ignore'
vxlan_del_cmd = "ip link del vxlan_sys_4789"

frr_password = 'zebra'
base_port = 10000
ssh_retries = 10

docker_run_sh = os.path.expanduser('~')+'/docker.sh'
links_sh = os.path.expanduser('~')+'/links.sh'

max_containers_per_leaf_vm = 24.0 
max_links_per_spine_vm = 8000.0 
max_ports_per_ovs = 3800.0

spine_lo_net = '192.170.0.0/16'
public_net = '10.0.0.0/14'
f1_spine_net= '192.100.0.0/13'
inter_f1_net = '192.168.0.0/16'
f1_mgmt_net= '172.16.0.0/16'

spine_lo_subnets = [] 
f1_public_subnet = []
rack_subnets = []
spine_subnets = []
f1_mgmt_ips = []

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

def pretty(d, indent=0):
   for key, value in d.items():
      print('\t' * indent + str(key))
      if isinstance(value, dict):
         pretty(value, indent+1)
      else:
         print('\t' * (indent+1) + str(value))

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts)
        return result
    return timed

def retry(tries=100, delay=20):
    '''Retries a function or method until it returns True.
    delay sets the initial delay in seconds.
    '''
    tries = tries * 1.0
    tries = math.floor(tries)
    if tries < 0:
        raise ValueError("tries must be 0 or greater")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay  # make mutable

            rv = f(*args, **kwargs)  # first attempt
            while mtries > 0:
                if rv is True:  # Done on success
                    return True
                mtries -= 1      # consume an attempt
                time.sleep(mdelay)  # wait...

                rv = f(*args, **kwargs)  # Try again
            return False  # Ran out of tries :-(

        return f_retry  # true decorator -> decorated function
    return deco_retry  # @retry(arg[, ...]) -> true decorator
