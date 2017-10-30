**Topology Manager**

The Topology Manager automates the build out of a data center network. What this means is that given a high level specification of the DC topology - which is typically the number of Racks, number of F1s/Rack and number of Spines, the topology_manager builds out the DC network by spinning up F1/Spine routers inside docker containers and connecting them via virtual p2p ethernet links. Additionally, it also configures the relevant routing protocols by applying the necessary configurations on the F1/Spine routers.

The topo_manager supports the following modes:

1. **Hierarchical:** this is the standard spine/leaf topology and is the default.
2. **Flat:** for cases where the application does not really care about the underlay topology, this is a useful mode. In this mode, Spine count is set to 0. Only F1 containers are launched and they all have a single interface into the same network.


Topo_manager can be run on standalone (single) physical server/VM or on a cluster of servers/VMs.

**Usage:**

```
1. Clone this repo.
2. Make changes to config.py to suit your environment.
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
   (d) sudo pip install -y paramiko zmq netaddr
   (e) Pull relevant docker images
   (f) Start ZMQ agent on all the VM.
       (i) screen -d -S cmd_agent -m /usr/bin/python2.7 topology_manager/topolib/recv_zmq.py
```
To run the example scripts in topology_manager/examples, do the following (from topology_manager directory):

```
    python -m topology_manager.examples.hier
```
To execute your own script, set PYTHONPATH to include topology_manager and import topolib: "from topolib import *"
