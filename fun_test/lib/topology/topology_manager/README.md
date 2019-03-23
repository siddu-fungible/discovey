**Topology Manager**

The Topology Manager automates the build out of a data center network. What this means is that given a high level specification of the DC topology - which is typically the number of Racks, number of F1s/Rack and number of Spines, the Topology Manager builds out the DC network by spinning up F1/Spine routers inside docker containers and connecting them via virtual p2p ethernet links. Additionally, it also configures the relevant routing protocols by applying the necessary configurations on the F1/Spine routers.

The topo_manager supports the following modes:

1. **Hierarchical:** this is the standard spine/leaf topology and is the default.
2. **Flat:** for usecases where the underlay topology doesnt matter (eg: storage), this is a useful mode. In this mode, Spine count is set to 0. Only F1 containers are launched and they all have a single interface into the same network.

Topology manager can be run on standalone (single) physical server/VM or on a cluster of servers/VMs. Furthermore, F1/spine containers can be launched on the server where the topology manager itself is running (All-in-one mode). The vm_ips list in config.py governs this. 

**Usage:**

```
1. Clone Integration repo. 
2. Make changes to topo_manager/config.py to suit your environment. Defaults should usually work; the only needed change would    be the IP(s) of the compute VMs and their access credentials.
3. On all the compute engines, do the following:
   (a) Install Docker:
         (i) curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        (ii) sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
       (iii) sudo apt-get update
        (iv) apt-cache policy docker-ce
         (v) sudo apt-get install -y docker-ce
   (b) Install OVS:
         (i) sudo apt-get install -qy openvswitch-switch openvswitch-common
   (c) sudo apt-get install -y python-pip
   (d) sudo pip install paramiko zmq netaddr
   (e) Either build or copy relevant docker images from root@10.1.20.67:/home/asurana/docker_images/ (pwd: fun123)
         Leaf FRR: reg-nw-frr:v1
         spine FRR: frr:v1
       Once these images are copied, they can be loaded by doing:
         sudo docker load < image_name
   (f) Start ZMQ agent on all the VM (recv_zmq.py should be copied to each VM).
       (i) sudo screen -d -S cmd_agent -m /usr/bin/python2.7 topology_manager/topo_manager/recv_zmq.py
```

To run the example scripts in topology_manager/examples, do either of the following: 

```
    From topology directory:

    python -m topology_manager.examples.hier
```

or, set PYTHONPATH appropriately and import topo_manager (from topo_manager import *)
