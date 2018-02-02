offRacks = 0 
offLeafs = 0 
offSpines = 0 

#If not flat_topo, setup standard spine/leaf topology. Else Flat topology.
flat_topo = False 

#If network_only, use FRR container. Else use PSIM container.
network_only = True 

if network_only:
    leaf_container = 'frr:v2'
else:
    leaf_container = 'testdemo:latest'

tg_container = 'tgen:v3'
spine_container = 'frr:v1'

#IPs of compute engines on which docker containers will be launched
vm_ips = ['127.0.0.1']

#Uname/passwd of compute engines
vm_user = 'ptf'
vm_passwd = 'fun123'
container_passwd = 'fun123'
