offRacks = 0 
offLeafs = 0 
offSpines = 0 

#If not flat_topo, setup standard spine/leaf topology. Else Flat topology.
flat_topo = False 

#If network_only, use FRR container. Else use PSIM container.
network_only = True 

if network_only:
    leaf_container = 'frr:v4'
else:
    leaf_container = 'demo:v6'

tg_container = 'tgen:v3'
spine_container = 'frr:v4'

#IPs of compute engines on which docker containers will be launched
vm_ips = ['192.168.56.107']
#Uname/passwd of compute engines
vm_user = 'asurana'
vm_passwd = 'fun123'
