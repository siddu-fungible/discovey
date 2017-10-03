offRacks = 0 
offLeafs = 0 
offSpines = 0 

flat_topo = False

#leaf_container = 'frr:v2'
if flat_topo:
    leaf_container = 'psim:v1'
else:
    leaf_container = 'demo:v2'
#leaf_container = 'text:latest'

vm_ips = ['10.138.0.3', '10.138.0.4', '10.138.0.5'] 
vm_user = 'amit.surana'
vm_passwd = 'fun123'

