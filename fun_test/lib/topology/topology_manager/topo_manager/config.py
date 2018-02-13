import os

offRacks = 0 
offLeafs = 0 
offSpines = 0 

#If not flat_topo, setup standard spine/leaf topology. Else Flat topology.
flat_topo = False 

#If network_only, use FRR container. Else use PSIM container.
network_only = True 

if network_only:
    leaf_container = 'reg-nw-frr:v1' 
    startup = '/opt/fungible/scripts/frr-startup.sh'
else:
    leaf_container = 'reg-nw-full-build:v1'
    startup = "/workspace/Integration/tools/docker/funcp/dev/startup.sh"

tg_container = 'tgen:v3'
spine_container = 'frr:v1'

#IPs of compute engines on which docker containers will be launched
vm_ips = ['127.0.0.1']

#Uname/passwd of compute engines
vm_user = 'regress'
user = os.environ.get('USER')
workspace = '/home/'+user+'/fungible'
uid = str(os.getuid())
gid = str(os.getgid())
vm_passwd = 'fun123'
container_passwd = 'fun123'
