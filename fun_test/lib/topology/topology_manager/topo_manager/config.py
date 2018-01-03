offRacks = 0 
offLeafs = 0 
offSpines = 0 

#If not flat_topo, setup standard spine/leaf topology. Else Flat topology.
flat_topo = False 

#If network_only, use FRR container. Else use PSIM container.
network_only = False

if network_only:
    leaf_container = 'frr:v6'
else:
    leaf_container = 'testdemo:latest'

tg_container = 'tgen:v3'
spine_container = 'frr:v4'

#IPs of compute engines on which docker containers will be launched
#vm_ips = ['192.168.56.107']
vm_ips = ['192.168.56.101']

#Uname/passwd of compute engines
<<<<<<< HEAD
vm_user = 'ptf'
=======
vm_user = 'jabraham'
>>>>>>> 1a5e0d121eee2b79929ae3bbd90a64eff4f84442
vm_passwd = 'fun123'
