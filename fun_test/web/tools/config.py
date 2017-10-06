offRacks = 0 
offLeafs = 0 
offSpines = 0 

flat_topo = False
network_only = False 

if network_only:
    leaf_container = 'frr:v2'
elif flat_topo:
    leaf_container = 'psim:v1'
else:
    leaf_container = 'demo:v4'
#leaf_container = 'text:latest'

vm_ips = ['10.138.0.3', '10.138.0.4', '10.138.0.5'] 
vm_user = 'amit.surana'
vm_passwd = 'fun123'

