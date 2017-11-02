import math
import sys
import re
import os
import telnetlib
from util import *
import threading
import paramiko
import time
from send_zmq import *
import pickle
import logging


class Topology(object):
    def __init__(self):

        self.vm_ips = vm_ips 
        self.leaf_vm_ips = []
        self.spine_vm_ips = []
        self.leaf_vm_objs = []
        self.spine_vm_objs = []

        self.nRacks = 0
        self.nLeafs = 0
        self.nSpines = 0

        self.offRacks = 0
        self.offLeafs = 0
        self.offSpines = 0

        self.leaf_vms = 0
        self.spine_vms = 0
        self.total_vms = 0
        self.available_vms = 0

        self.max_racks_per_vm = 0
        self.max_spines_per_vm = 0
        self.max_leafs_per_vm = 0

        self.leaf_leaf_ovs =  0
        self.leaf_leaf_ovs_ports = 0

        self.max_leaf_spine_ports_per_ovs = 0
        self.max_spine_spine_ports_per_ovs = 0

        self.link_objs = []
        self.all_spines = []

        self.iid = 1

        self.logger = logging.getLogger(__name__)

        self.name = '%d_Racks__%d_Leafs/rack__%d_Spines' % \
                    (self.nRacks, self.nLeafs, self.nSpines)
        self.state = 'init'

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        d['logger'] = logging.getLogger(__name__)
        self.__dict__.update(d) 

    def get_next_id(self):
        res = self.iid
        self.iid += 1
        return res
 
    def getAccessInfo(self):
        access_info = {}
        leafs_dict = dict()
        for leaf_vm in self.leaf_vm_objs:
            leaf_nodes = leaf_vm.get_nodes()
            for leaf_node in leaf_nodes:
                leaf_dict = dict()
                leaf_dict['mgmt_ip'] = leaf_node.vm_ip
                leaf_dict['mgmt_ssh_port'] = leaf_node.host_ssh_port
                leaf_dict['dpcsh_port'] = leaf_node.dpcsh_port
                leaf_dict['dataplane_ip'] = leaf_node.ip
                if leaf_node.tgs:
                    tgs_dict = dict()
                    for tg in leaf_node.tgs:
                        tg_dict = dict()
                        tg_dict['mgmt_ip'] = tg.vm_ip
                        tg_dict['mgmt_ssh_port'] = tg.host_ssh_port
                        tg_dict['dataplane_ip'] = tg.ip
                        tgs_dict[tg.name] = tg_dict
                    leaf_dict['tgs'] = tgs_dict
                leafs_dict[leaf_node.name] = leaf_dict
        access_info['F1'] = leafs_dict

        racks_dict = dict()
        for leaf_vm in self.leaf_vm_objs:
            for rack in leaf_vm.racks:
                rack_dict = dict()
                for node in rack.nodes:
                    rack_dict[node.name] = []
                    for k,v in node.interfaces.items():
                        if v['peer_type'] == 'spine':
                            rack_dict[node.name].append(k)
                racks_dict[str(rack.rack_id)] = rack_dict
        access_info['Racks'] = racks_dict
 
        spines_dict = dict()
        for spine_vm in self.spine_vm_objs:
            spine_nodes = spine_vm.get_nodes()
            for spine_node in spine_nodes:
                spine_dict = dict()
                spine_dict['mgmt_ip'] = spine_node.vm_ip
                spine_dict['mgmt_ssh_port'] = spine_node.host_ssh_port
                spine_dict['dataplane_ip'] = spine_node.ip
                spines_dict[spine_node.name] = spine_dict
        access_info['CX'] = spines_dict

        self.logger.debug('Access Info: %s' % pretty(access_info))
        return json.dumps(access_info)

    def save(self, filename='topology.pkl'):
        
        topo_state = {'leaf_vm_ips': self.leaf_vm_ips,\
                      'spine_vm_ips': self.spine_vm_ips,\
                      'leaf_vm_objs': self.leaf_vm_objs,\
                      'spine_vm_objs': self.spine_vm_objs,\
                      'nRacks': self.nRacks,\
                      'nLeafs': self.nLeafs,\
                      'nSpines': self.nSpines,\
                      'leaf_vms': self.leaf_vms,\
                      'spine_vms': self.spine_vms,\
                      'all_spines': self.all_spines,\
                      'max_racks_per_vm': self.max_racks_per_vm,\
                      'max_spines_per_vm': self.max_spines_per_vm,\
                      'max_leafs_per_vm': self.max_leafs_per_vm,\
                      'iid': self.iid,\
                      'state': self.state,\
                      'f1_mgmt_ips': f1_mgmt_ips,\
                      'flat_topo': flat_topo
                      }
        self.logger.info('Saved topology to %s' % filename)
        pickle.dump(topo_state, open(filename,'wb'))

    def load(self, filename='topology.pkl'):

        global f1_mgmt_ips, flat_topo

        self.logger.info('Loaded topology from %s' % filename)
        topo_state = pickle.load(open(filename, 'rb'))
        
        self.leaf_vm_ips = topo_state['leaf_vm_ips']
        self.spine_vm_ips = topo_state['spine_vm_ips']
        self.leaf_vm_objs = topo_state['leaf_vm_objs']
        self.spine_vm_objs = topo_state['spine_vm_objs']
        self.nRacks = topo_state['nRacks']
        self.nLeafs = topo_state['nLeafs']
        self.nSpines = topo_state['nSpines']
        self.leaf_vms = topo_state['leaf_vms']
        self.spine_vms = topo_state['spine_vms']
        self.all_spines = topo_state['all_spines']
        self.max_racks_per_vm = topo_state['max_racks_per_vm']  
        self.max_spines_per_vm = topo_state['max_spines_per_vm']
        self.max_leafs_per_vm = topo_state['max_leafs_per_vm']
        self.iid = topo_state['iid']
        self.state = topo_state['state']
        f1_mgmt_ips = topo_state['f1_mgmt_ips']
        flat_topo = topo_state['flat_topo'] 
 
    def sizeUp(self):

        if self.nRacks == 0 or self.nLeafs == 0:
            self.logger.error('Number of Racks and/or Leafs/Racks cannot be 0. Exiting.')
            sys.exit(1)

        if self.nSpines % self.nLeafs:
            self.logger.error('Number of Spines should be a multiple of number of F1s/Rack. Exiting.')
            sys.exit(1)

        if len(self.vm_ips) == 1:
            self.logger.info('All-in-one')
            self.total_vms = 1
            self.leaf_vm_ips = self.spine_vm_ips = self.vm_ips
            self.max_racks_per_vm = self.nRacks
            self.max_spines_per_vm = self.nSpines
            self.max_leafs_per_vm = self.nLeafs
            self.leaf_leaf_ovs = 1
            self.leaf_leaf_ovs_ports = (self.nLeafs * (self.nLeafs-1))*self.nRacks + self.nRacks*self.nSpines*2
            if (self.nRacks*self.nLeafs+self.nSpines) > max_containers_per_leaf_vm:
                self.logger.info('Cannot fit requested topology in 1 VM')
                sys.exit(1)
            else:
                self.logger.info('Topology fits in 1 VM')
                return
        if not flat_topo:
            max_racks_per_vm = math.floor(max_containers_per_leaf_vm / self.nLeafs)
            self.leaf_vms = int(max(1, math.ceil(self.nRacks / max_racks_per_vm)))
        else:
            self.leaf_vms = int(max(1, math.ceil(self.nLeafs / max_containers_per_leaf_vm)))
        temp_spine_vms = math.ceil(self.nRacks * self.nSpines / max_links_per_spine_vm)
        self.spine_vms = int(temp_spine_vms) if not temp_spine_vms else int(max(1, temp_spine_vms)) 
        self.total_vms = self.leaf_vms + self.spine_vms

        if self.total_vms > self.available_vms:
            self.logger.error('Insufficient resources. Required VMs: %d' % (self.total_vms))
            sys.exit(1)

        self.leaf_vm_ips = self.vm_ips[:self.leaf_vms]
        self.spine_vm_ips = self.vm_ips[self.leaf_vms:self.total_vms]

        self.logger.info('Sufficient Resources to fulfil current requirement. Creating Topology with specs:')
        self.logger.info('\tTopology: %dx%dx%d' % (self.nRacks, self.nLeafs, self.nSpines))
        self.logger.info('\tTotal VMs used: %d' % self.total_vms)
        self.logger.info('\tNumber of Leaf VMs: %d. On each Leaf VM:' % self.leaf_vms)

        if not flat_topo:
            if self.leaf_vms == 1:
                self.max_racks_per_vm = self.nRacks
            else:
                self.max_racks_per_vm = int(math.floor(max_containers_per_leaf_vm / self.nLeafs))
            self.logger.info('\t\tMax Num of Racks: %d' % self.max_racks_per_vm)

            self.logger.info('\tNumber of Spine VMs: %d. On Each Spine VM:' % self.spine_vms)
            if self.spine_vms == 1:
                self.max_spines_per_vm = self.nSpines
            else:
                self.max_spines_per_vm = int(math.floor(max_links_per_spine_vm/self.nRacks))
            self.logger.info('\t\tMax Num of Spines: %d' % self.max_spines_per_vm)

            num_leaf_leaf_ports = (self.nLeafs * (self.nLeafs -1)) * self.max_racks_per_vm
            self.leaf_leaf_ovs = int(max(1, math.ceil(num_leaf_leaf_ports/max_ports_per_ovs)))
            self.leaf_leaf_ovs_ports = int(math.ceil(num_leaf_leaf_ports/self.leaf_leaf_ovs))

            leaf_spine_ports = float(self.max_racks_per_vm * self.nSpines)
            if leaf_spine_ports:
                leaf_spine_ovs = self.spine_vms
                self.max_leaf_spine_ports_per_ovs = int(math.ceil(leaf_spine_ports/leaf_spine_ovs))

                spine_spine_ports = float(self.max_spines_per_vm * self.nRacks)
                spine_spine_ovs = self.leaf_vms
                self.max_spine_spine_ports_per_ovs = int(math.ceil(spine_spine_ports/spine_spine_ovs))
        else:
            if self.leaf_vms == 1:
                self.max_leafs_per_vm = self.nLeafs
            else:
                self.max_leafs_per_vm = int(max_containers_per_leaf_vm)
            self.logger.info('\t\tMax Num of F1s: %d' % self.max_leafs_per_vm)            
            self.logger.info('\tNumber of Spine VMs: %d. On Each Spine VM:' % self.spine_vms)

    def configureTopoSubnets(self):

        global f1_public_subnet, rack_subnets, spine_subnets, f1_mgmt_ips, spine_lo_subnets

        if flat_topo:
            all_ips= IPNetwork(f1_mgmt_net).iter_hosts()
            #*4 to accomodate for 4 TGs/Leaf. Also adjust for docker0 IP
            num_ips = self.nRacks*self.nLeafs + self.nLeafs*4 + 2 
            for i in range(1,num_ips):
                f1_mgmt_ips.append(all_ips.next())
            return

        all_subnets = IPNetwork(public_net).subnet(24)
        for i in range(1,self.nRacks+1):
            rack_subnets.append(all_subnets.next())
        for rack_subnet in rack_subnets:
            f1_public_subnet.extend(list(rack_subnet.subnet(28))[:self.nLeafs])
        del all_subnets

        all_subnets = IPNetwork(f1_spine_net).subnet(30)
        for i in range(0,self.nRacks*self.nSpines):
            spine_subnets.append(all_subnets.next())
        del all_subnets

        all_subnets = IPNetwork(spine_lo_net).subnet(30)
        for i in range(0,128):
            spine_lo_subnets.append(all_subnets.next())
        f1_mgmt_ips = []


    def initialize(self):

        threads = [] 
        for vm_ip in self.vm_ips:
            t = threading.Thread(target=self.linuxSettings, args=(vm_ip,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def linuxSettings(self, vm_ip):

        out = exec_remote_commands([(vm_ip, [mkdir_netns_cmd,
                                             rp_filter_all_cmd,
                                             rp_filter_default_cmd,
                                             arp_ignore_all_cmd,
                                             arp_ignore_default_cmd,
                                             vxlan_del_cmd,
                                             docker_restart_cmd])],
                                   [], logger=self.logger)

        
    @timeit
    def create(self, nRacks, nLeafs, nSpines):

        self.nRacks = nRacks
        self.nLeafs = nLeafs
        self.nSpines = nSpines

        if self.state == 'running':
            self.logger.warning('Topology already up and running. Cannot call create() again')
            return

        self.logger.info('Creating Topology: %sx%sx%s' % (self.nRacks, self.nLeafs, self.nSpines))

        self.available_vms = len(vm_ips)
        self.sizeUp()
        self.initialize()
        self.configureTopoSubnets()

        if flat_topo:
            self.createMgmtOverlay()
            for vm_id,vm_ip in enumerate(self.leaf_vm_ips):
                vm_obj = VM(self, vm_id+1, vm_ip, role='leaf')
                self.leaf_vm_objs.append(vm_obj)
                vm_obj.createLeafs()
        else:
            for vm_id,vm_ip in enumerate(self.leaf_vm_ips):
                vm_obj = VM(self, vm_id+1, vm_ip, role='leaf')
                self.leaf_vm_objs.append(vm_obj)
                vm_obj.configureBridges()
                vm_obj.createRacks()

            for vm_id,vm_ip in enumerate(self.spine_vm_ips):
                vm_obj = VM(self, vm_id+1, vm_ip, role='spine')
                self.spine_vm_objs.append(vm_obj)
                if not flat_topo:
                    vm_obj.configureBridges()
                vm_obj.createSpines()

            self.configureSpineLinks()
        
            for vm in self.leaf_vm_objs:
                vm.configureLeafLinks()
      
        if self.available_vms == 1:
            if not flat_topo:
                self.spine_vm_objs[0].run()
            self.leaf_vm_objs[0].run()
        else:         
            all_vms = self.leaf_vm_objs + self.spine_vm_objs
      
            threads = []
            for vm in all_vms:
                t = threading.Thread(target=vm.run)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
        
        self.populate_ssh_config()
        self.deactivate_partial_topo(offRacks, offLeafs, offSpines)
        self.state = 'running'

    def deactivate_partial_topo(self, offRacks, offLeafs, offSpines):

        self.offRacks = offRacks
        self.offLeafs = offLeafs
        self.offSpines = offSpines

        if offLeafs == self.nLeafs:
            rack_list = []
            for rack in range(self.nRacks-offRacks+1, self.nRacks+1):
                rack_list.append(rack)
            self.pauseRacks(rack_list)
        elif offLeafs < self.nLeafs:
            node_list = []
            for rack in range(1, self.nRacks+1):
                for node in range(self.nLeafs-offLeafs+1, self.nLeafs+1):
                    node_list.append(str(rack)+'-'+str(node))
            self.pauseNodes(node_list)
        else:
            self.logger.warning('OffLeafs cant be greater than total Leafs')
        if offSpines > 0:
            spine_list = []
            for spine in range(self.nSpines-offSpines+1, self.nSpines+1):
                spine_list.append('0-'+str(spine))
            self.pauseNodes(spine_list)

        self.logger.info('Deactivating: %sx%sx%s' % (self.offRacks, self.offLeafs, self.offSpines))

    def configureSpineLinks(self):
        for leaf_vm in self.leaf_vm_objs:
            for rack in leaf_vm.racks:
                index = 1
                for src in rack.nodes:
                    for spine in range(1, self.nSpines/self.nLeafs+1):
                        spine_name = self.convert_index_to_name(index)
                        dst = self.get_node(spine_name)
                        dst_vm = self.get_node_vm(spine_name)
                        if dst.name not in src.interfaces:
                            if self.available_vms == 1:
                                src_bridge = leaf_vm.leaf_bridges[0]
                                link_obj = Link(src, dst, spine_subnets.pop(0), src_bridge)
                            else:
                                src_bridge = leaf_vm.spine_bridges[dst_vm.id-1]
                                dst_bridge = dst_vm.spine_bridges[leaf_vm.id-1]
                                link_obj = Link(src, dst, spine_subnets.pop(0), src_bridge, dst_bridge)
                            self.link_objs.append(link_obj)
                        index += 1

    def createMgmtOverlay(self):
        worker_cmd = ''
        if self.available_vms == 1:
            out = run_commands(commands=[docker_del_mgmt_net_cmd])
            time.sleep(0.5)
            out = run_commands(commands=[docker_mgmt_net_cmd])
            return

        for vm_ip in self.vm_ips[1:]:
            out = exec_remote_commands([(vm_ip, [docker_swarm_leave_cmd])], [], logger=self.logger)

        tries = 0
        while True:
            try: 
                out = run_commands(commands=[docker_swarm_leave_force_cmd]) 
                time.sleep(2)
                out = run_commands(commands=[docker_swarm_init_cmd])
                worker_cmd = out['results'][0]['output'].split('\n')[4].strip()
            except:
                time.sleep(1)
                tries += 1
                if tries == 5:
                    self.logger.error('Unable to form Swarm. Exiting..') 
                    sys.exit(1)
            if worker_cmd:
                break

        for vm_ip in self.vm_ips[1:]:
            out = exec_remote_commands([(vm_ip, [worker_cmd])], [], logger=self.logger)

        tries = 0
        mgmt_driver = ''
        while True:
            try:
                out = run_commands(commands=[docker_del_mgmt_net_cmd])
                time.sleep(2)
                out = run_commands(commands=[ docker_swarm_net_cmd])
                time.sleep(1)
                out = run_commands(commands=[docker_net_list_cmd])
                mgmt_driver = out['results'][0]['output'].split('\n')[1].strip()
            except:
                time.sleep(1)
                tries += 1
                if tries == 5:
                    self.logger.error('Unable to create Overlay MGMT n/w. Exiting..')
                    sys.exit(1)
            if mgmt_driver:
                break    

    def pauseRacks(self, rack_ids):
        vms = {}
        invalids = []
        self.logger.info('pauseRacks called for %s' % rack_ids)
        for rack_id in rack_ids:
            if rack_id == 0 or rack_id > self.nRacks:
                self.logger.warning('Invalid rack_id:%s. Skipping over' % rack_id)
                invalids.append(rack_id)
                continue
            vm = self.get_node_vm(str(rack_id)+'-'+str(1))
            vms.setdefault(vm, []).append(rack_id)

        self.logger.info('Pausing Racks: %s' % list(set(rack_ids)-set(invalids))) 
        
        threads = []
        for vm, rack_ids in vms.items():
            t = threading.Thread(target=vm.pauseRacks, args=(rack_ids,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def pauseNodes(self, node_names):
        vms = {}
        invalids = []
        self.logger.info('pauseNodes called for %s' % node_names)
        for node_name in node_names:
            if not self.isNodeValid(node_name):
                invalids.append(node_name)
                continue
            vm = self.get_node_vm(node_name)
            vms.setdefault(vm, []).append(node_name)

        self.logger.info('Pausing Nodes: %s' % list(set(node_names)-set(invalids)))

        threads = []
        for vm, node_name in vms.items():
            t = threading.Thread(target=vm.pauseNodes, args=(node_name,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def unpauseRacks(self, rack_ids):
        vms = {}
        invalids = []
        self.logger.info('unpauseRacks called for %s' % rack_ids)
        for rack_id in rack_ids:
            if rack_id == 0 or rack_id > self.nRacks:
                self.logger.warning('Invalid rack_id: %s. Skipping over' % rack_id)
                invalids.append(rack_id)
                continue
            vm = self.get_node_vm(str(rack_id)+'-'+str(1))
            vms.setdefault(vm, []).append(rack_id)

        self.logger.info('Unpausing Racks: %s' % list(set(rack_ids)-set(invalids)))

        threads = []
        for vm, rack_ids in vms.items():
            t = threading.Thread(target=vm.unpauseRacks, args=(rack_ids,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def unpauseNodes(self, node_names):
        vms = {}
        invalids = []
        self.logger.info('unpauseNodes called for %s' % node_names)
        for node_name in node_names:
            if not self.isNodeValid(node_name):
                invalids.append(node_name)
                continue
            vm = self.get_node_vm(node_name)
            vms.setdefault(vm, []).append(node_name)

        self.logger.info('Unpausing Nodes: %s' % list(set(node_names)-set(invalids)))

        threads = []
        for vm, node_name in vms.items():
            t = threading.Thread(target=vm.unpauseNodes, args=(node_name,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def linkImpair(self, src, dsts, oper='loss', param1='100%', param2=None, param3=None):
        """ Flap link that connects src node to nodes in dsts.
            dsts supports wild cards:
            all spine links:  flap links from src F1 to all its spines
            all inter-f1 links: flap links from src F1 to all its peer F1s
            all f1 links: flap links from src spine to all its peer F1s
            dsts: can also be a list of nodes
        """

        invalids = []

        self.logger.info('LinkImpair called for: %s %s %s %s %s %s' % (src, dsts, oper, param1, param2, param3))

        if not self.isNodeValid(src):
            return

        if flat_topo:
            if not isinstance(dsts, list):
                self.logger.warning('For flat_topo, destinations must be list of nodes')
                return
            dst_nodes = []
            node_vm = self.get_node_vm(src)
            for dst in dsts:
                if not self.isNodeValid(dst):
                    invalids.append(dst)
                else:
                    dst_node = self.get_node(dst)
                    dst_nodes.append(dst_node)

            self.logger.info('Flat Topo, LinkImpair: links from %s to %s' %(src, list(set(dsts)-set(invalids))))
            node_vm.flatLinkImpair(src, dst_nodes)
        else:
            node_vm = self.get_node_vm(src)
            node_vm.linksImpair(src, dsts, oper, param1, param2, param3)

    def linkRepair(self, src, dsts, oper='loss'):
        """ Flap link that connects src node to nodes in dsts.
            dsts supports wild cards:
            all spine links:  flap links from src F1 to all its spines
            all inter-f1 links: flap links from src F1 to all its peer F1s
            all f1 links: flap links from src spine to all its peer F1s
            dsts: can also be a list of nodes
        """

        invalids = []

        self.logger.info('LinkRepair called for: %s %s %s' % (src, dsts, oper))

        if not self.isNodeValid(src):
            return

        if flat_topo:
            if not isinstance(dsts, list):
                self.logger.warning('For flat_topo, destinations must be list of nodes')
                return
            dst_nodes = []
            node_vm = self.get_node_vm(src)
            for dst in dsts:
                if not self.isNodeValid(dst):
                    invalids.append(dst)
                else:
                    dst_node = self.get_node(dst)
                    dst_nodes.append(dst_node)

            self.logger.info('Flat Topo, LinkRepair: Links from %s to %s' %(src, list(set(dsts)-set(invalids))))
            node_vm.flatLinkRepair(src, dst_nodes)
        else:
            node_vm = self.get_node_vm(src)
            node_vm.linksRepair(src, dsts, oper)
 
    def attachTG(self, node_name):

        self.logger.info('Attaching TG to node: %s' % node_name)

        if not self.isNodeValid(node_name):
            return
        node = self.get_node(node_name)
        if node.type == 'spine':
            self.logger.warning('Cant attach TG to spine router')
            return 
        tg_id = node.get_next_tg_id()
        if tg_id > 4:
            self.logger.warning('Reached limit of 4 TGs/Node. Cannot attach this TG')
            return None
        else:
            tg = node.attachTG(tg_id)
            return tg

    def get_tgs(self, node_name):

        if not self.isNodeValid(node_name):
            return []
        node = self.get_node(node_name)
        return node.tgs

    def get_tg(self, tg_name):

        node_name = '-'.join(tg_name.split('-')[1:])
        if not self.isNodeValid(node_name):
            self.logger.warning('Invalid TG name: %s' % tg_name)
            return
        tgs = self.get_tgs(node_name)
        if tgs:
            for tg in tgs:
                if tg.name == tg_name:
                    return tg
            else:
                self.logger.warning('Invalid TG name: %s' % tg_name)
                return None
        else:
            self.logger.warning('No TGs attached to Node: %s' % node_name)
            return None

    def isNodeValid(self, node_name):
        rack_id, node_id = node_name.split('-')
        if flat_topo:
            if (int(rack_id) > 0 or int(node_id) > self.nLeafs):
                self.logger.warning('Node %s does not exist' % node_name)
                return False
            else:
                return True
        if (int(rack_id) > self.nRacks) \
                or (rack_id == '0' and int(node_id) > self.nSpines) \
                or (int(node_id) > self.nLeafs):
            self.logger.warning('Node %s does not exist' % node_name)
            return False
        else:
            return True

    def get_node_vm(self, node_name):
        rack_id, node_id = node_name.split('-')
        if rack_id != '0':
            return self.leaf_vm_objs[(int(rack_id)-1)/self.max_racks_per_vm]
        else:
            if flat_topo:
                return self.leaf_vm_objs[(int(node_id)-1)/self.max_leafs_per_vm]
            else:
                return self.spine_vm_objs[(int(node_id)-1)/self.max_spines_per_vm]

    def get_node(self, node_name):
        node_vm = self.get_node_vm(node_name)
        return node_vm.get_node(node_name)

    def convert_index_to_name(self, index):
        return '0-'+str(index)

    def populate_ssh_config(self):
        ssh_config = ''
        for vm_obj in self.leaf_vm_objs:
            if flat_topo:
                for node in vm_obj.leafs:
                    node_ssh = 'Host %s \n\tHostName %s \n\tUser root\n\tPort %s\n' %\
                               (node.name, node.vm_ip, node.host_ssh_port)
                    ssh_config += node_ssh
                    if node.tgs:
                        for tg in node.tgs:
                            node_ssh = 'Host %s \n\tHostName %s \n\tUser root\n\tPort %s\n' %\
                                       (tg.name, tg.vm_ip, tg.host_ssh_port)
                            ssh_config += node_ssh
            else:
                for rack in vm_obj.racks:
                    for node in rack.nodes:
                        node_ssh = 'Host %s \n\tHostName %s \n\tUser root\n\tPort %s\n' %\
                                   (node.name, node.vm_ip, node.host_ssh_port)
                        ssh_config += node_ssh
                        if node.tgs:
                            for tg in node.tgs:
                                node_ssh = 'Host %s \n\tHostName %s \n\tUser root\n\tPort %s\n' %\
                                           (tg.name, tg.vm_ip, tg.host_ssh_port)
                                ssh_config += node_ssh

        for vm_obj in self.spine_vm_objs:
            for node in vm_obj.spines:
                node_ssh = 'Host %s \n\tHostName %s \n\tUser root\n\tPort %s\n' %\
                           (node.name, node.vm_ip, node.host_ssh_port)
                ssh_config += node_ssh

        create_ssh_config(ssh_config)


    def cleanup(self):

        self.logger.info('cleaning up topology')
        all_vms = self.leaf_vm_objs + self.spine_vm_objs
        threads = []
        for vm in all_vms:
            t = threading.Thread(target=vm.cleanup)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        if flat_topo and self.total_vms > 1:
            time.sleep(2)
            out = run_commands(commands=[docker_swarm_leave_force_cmd])

        self.state = ''

    def printRacks(self, rack_ids):
        output = 'Topology Summary:\n\tFull: %s Racks, %s Leafs/Rack, %s Spines \n' % \
                   (self.nRacks, self.nLeafs, self.nSpines)

        output += '\tInactive: %s Racks, %s Leafs, %s Spines\n' % (self.offRacks, self.offLeafs, self.offSpines)

        if flat_topo:
            self.logger.warning('Cannot print Racks for flat_topo')
            return

        if '0' in rack_ids:
            self.logger.warning('Cannot print Rack 0 as it does not exist')
            rack_ids.remove('0')

        if rack_ids:
            vms = {} 
            for rack_id in rack_ids:
                if rack_id == '0' or int(rack_id) > self.nRacks:
                    self.logger.warning('Invalid Rack-id: %s. Skipping over.' % rack_id)
                    continue
                vm = self.get_node_vm(str(rack_id)+'-'+str(1))
                vms.setdefault(vm, []).append(rack_id)

            for vm, rack_ids in sorted(vms.items()): 
                for rack_id in rack_ids:
                    rack = vm.get_rack_from_id(rack_id)
                    if rack:
                        output += rack.__str__()

            print output


    def __str__(self, rack_ids=None):
        output = 'Topology Summary:\n\tFull: %s Racks, %s Leafs/Rack, %s Spines \n' % \
                   (self.nRacks, self.nLeafs, self.nSpines)

        output += '\tInactive: %s Racks, %s Leafs, %s Spines\n' % (self.offRacks, self.offLeafs, self.offSpines)

        for vm in self.leaf_vm_objs:
            for rack in vm.racks:
                output += rack.__str__()

        return output


class VM(object):

    def __init__(self, topo, vm_id, vm_ip, role=''):

        self.id = vm_id
        self.role = role
        self.ip = vm_ip 
        self.topo = topo
        self.nLeafs = topo.nLeafs

        self.racks =  []
        self.spines = []
        self.links = {}
        self.link_objs = []

        self.leaf_bridges = []
        self.spine_bridges = []
        self.port_id = 1

        self.logger = logging.getLogger(__name__)

        if self.role == 'leaf':
            if not flat_topo:
                self.nRacks = self.get_rack_count()
                self.nLeafs = topo.nLeafs
                self.num_leafOVS = topo.leaf_leaf_ovs
                self.num_leafOVS_ports = topo.leaf_leaf_ovs_ports
                self.num_spineOVS = topo.spine_vms
                self.start_rack_id, self.end_rack_id = self.get_rack_range()
                self.start_vxlan_id, self.end_vxlan_id = self.get_vxlan_range()
            else:
                self.leafs = []
                self.nLeafs = self.get_leaf_count()
                self.start_leaf_id, self.end_leaf_id = self.get_leaf_range()
        else:
            self.nSpines = self.get_spine_count()
            self.num_spineOVS = topo.leaf_vms
            self.start_vxlan_id = self.id
            self.start_spine_id, self.end_spine_id = self.get_spine_range()

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        d['logger'] = logging.getLogger(__name__)
        self.__dict__.update(d)

    def createRacks(self):
        for rack in range(self.start_rack_id, self.end_rack_id):
            rack_obj = Rack(self, rack)
            rack_obj.addNodes(self.nLeafs)
            self.racks.append(rack_obj)

    def createSpines(self):
        for spine in range(self.start_spine_id, self.end_spine_id):
            spine_obj = Node(self, node_id=spine)
            self.spines.append(spine_obj)

    def createLeafs(self):
        for leaf in range(self.start_leaf_id, self.end_leaf_id):
            leaf_obj = Node(self, node_id=leaf)
            self.leafs.append(leaf_obj)

    def configureLeafLinks(self):
        vlan = 3 
        flag = False
        for rack in self.racks:
            for node in range(0, self.nLeafs):
                src = rack.getNode(node)
                for leaf in range(0, self.nLeafs):
                    if leaf > node:
                        dst = rack.getNode(leaf)
                        if dst.name not in src.interfaces:
                            if (vlan-2) <= self.num_leafOVS_ports/2 and not flag:
                                bridge = self.leaf_bridges[0]
                            else:
                                vlan = 3 
                                flag = True
                                bridge = self.leaf_bridges[1]
                            src.bridge = dst.bridge = bridge
                            link_obj = Link(src, dst, rack.inter_f1_subnets.pop(0), bridge)
                            self.link_objs.append(link_obj)
                            vlan += 1
                        else:
                            continue

    def configureBridges(self):
        if self.role == 'leaf':
            self.configureLeafBridges()
            if self.topo.available_vms != 1:
                self.configureLeafSpineBridges()
        elif self.role == 'spine':
            if self.topo.available_vms != 1:
                self.configureSpineBridges()

    def configureLeafBridges(self):
        for bridge_id in range(1, self.num_leafOVS+1):
            bridge_obj = Bridge(self, bridge_id, 'leaf')
            # Add room for TG connection
            bridge_obj.addLeafPorts(self.num_leafOVS_ports+1024)
            self.leaf_bridges.append(bridge_obj)

    def configureLeafSpineBridges(self):
        dummy,remaining_spines = divmod(self.topo.nSpines,self.topo.max_spines_per_vm)
        for bridge_id in range(1, self.num_spineOVS+1):
            vxlan_id = self.start_vxlan_id + bridge_id - 1
            remote_ip = self.topo.spine_vm_ips[bridge_id - 1]
            bridge_obj = Bridge(self, bridge_id, 'spine', vxlan_id, remote_ip)
            if bridge_id == self.num_spineOVS:
                if remaining_spines:
                    ports = self.nRacks * remaining_spines
                else:
                    ports = self.nRacks * self.topo.max_spines_per_vm 
            else:
                ports = self.nRacks * self.topo.max_spines_per_vm
            bridge_obj.addSpinePorts(ports)
            self.spine_bridges.append(bridge_obj)

    def configureSpineBridges(self):
        dummy,remaining_racks = divmod(self.topo.nRacks,self.topo.max_racks_per_vm)
        for bridge_id in range(1, self.num_spineOVS+1):
            vxlan_id = self.start_vxlan_id + (bridge_id-1) * self.topo.spine_vms
            remote_ip = self.topo.leaf_vm_ips[bridge_id - 1]
            bridge_obj = Bridge(self, bridge_id, 'spine', vxlan_id, remote_ip)
            if bridge_id == self.num_spineOVS:
                if remaining_racks:
                    ports = self.nSpines * remaining_racks
                else:
                    ports = self.nSpines * self.topo.max_racks_per_vm
            else:
                ports = self.nSpines * self.topo.max_racks_per_vm
            bridge_obj.addSpinePorts(ports)
            self.spine_bridges.append(bridge_obj)


    def configureRacks(self):
        for rack in self.racks:
            rack.configureNodes()

    def configureSpines(self):
        for spine in self.spines:
            spine.configure()

    def run(self):
        vm_docker_run = ''
        vm_links = ''
        up_links = ''
        if flat_topo:
            for leaf in  self.leafs:
                leaf.run()
                vm_docker_run += leaf.docker_run
                vm_links += leaf.link_config
            params = {'role': self.role,
                    'start_leaf_id': self.start_leaf_id,
                    'end_leaf_id': self.end_leaf_id}
            self.logger.info('creating F1 containers')
        else:
            if self.role == 'leaf':
                for rack in self.racks:
                    rack_docker_run, rack_links = rack.run()
                    vm_docker_run += rack_docker_run
                    vm_links += rack_links
                params = {'role': self.role,
                          'start_rack_id': self.start_rack_id,
                          'end_rack_id': self.end_rack_id,
                          'nLeafs': self.nLeafs}
                self.logger.info('creating F1 containers')
            else:
                for spine in  self.spines:
                    spine.run()
                    vm_docker_run += spine.docker_run
                    vm_links += spine.link_config
                params = {'role': self.role,
                          'start_spine_id': self.start_spine_id,
                          'end_spine_id': self.end_spine_id}
                self.logger.info('creating Spine containers')
        
        if not vm_docker_run:
            self.logger.warning('No containers to launch')
            return

        out = exec_send_file([(self.ip, vm_docker_run)], [], logger=self.logger)
        out = exec_remote_commands([(self.ip, [docker_run_sh])], [], timeout=300, logger=self.logger)
        out = exec_send_file([(self.ip, params)], [], logger=self.logger)

        if self.role == 'leaf' and not network_only:
            self.logger.info('Waiting for PSIMs to be ready')
            self.waitOnPsim()
        if not flat_topo:
            if self.role == 'leaf':
                time.sleep(10)
                for rack in self.racks:
                    rack.configureNodes()
                self.pauseRacks([rack.rack_id for rack in self.racks])
            else:
                time.sleep(10)
                for spine in self.spines:
                    spine.configure()
                self.pauseNodes([spine.name for spine in self.spines])

            if self.topo.available_vms > 1:
                for bridge in self.spine_bridges:
                    bridge.run()

            if self.role == 'leaf':
                self.logger.info('connecting F1/spine containers')

            if (self.role == 'leaf' and self.topo.available_vms == 1) or self.topo.available_vms > 1:
                out = exec_send_file([(self.ip, vm_links)], [], logger=self.logger)
                out = exec_remote_commands([(self.ip, [links_sh])], [], timeout=1200, logger=self.logger)

            if self.role == 'leaf':
                self.unpauseRacks([rack.rack_id for rack in self.racks])
            else:
                self.unpauseNodes([spine.name for spine in self.spines])

    def pauseRacks(self, *racks):
        pause_list = ' '
        for rack_id in racks[0]:
            rack_obj = self.get_rack_from_id(rack_id)
            if rack_obj:
                for node in rack_obj.nodes:
                    node.state = 'paused'
                    pause_list += node.name
                    pause_list += ' '

        docker_pause = docker_pause_cmd + pause_list
        out = exec_remote_commands([(self.ip, [docker_pause])], [], logger=self.logger)

    def pauseNodes(self, *nodes):
        pause_list = ''
        for node in nodes[0]:
            node_obj = self.get_node(node)
            if node_obj:
                node_obj.state = 'paused'
                pause_list += node_obj.name
                pause_list += ' '

        docker_pause = docker_pause_cmd + pause_list
        out = exec_remote_commands([(self.ip, [docker_pause])], [], logger=self.logger)

    def unpauseRacks(self, *racks):
        unpause_list = ' '
        for rack_id in racks[0]:
            rack_obj = self.get_rack_from_id(rack_id)
            if rack_obj:
                for node in rack_obj.nodes:
                    node.state = 'running'
                    unpause_list += node.name
                    unpause_list += ' '

        docker_unpause = docker_unpause_cmd + unpause_list
        out = exec_remote_commands([(self.ip, [docker_unpause])], [], logger=self.logger)

    def unpauseNodes(self, *nodes):
        unpause_list = ''
        for node in nodes[0]:
            node_obj = self.get_node(node)
            if node_obj:
                node_obj.state = 'paused'
                unpause_list += node_obj.name
                unpause_list += ' '

        docker_unpause = docker_unpause_cmd + unpause_list
        out = exec_remote_commands([(self.ip, [docker_unpause])], [], logger=self.logger)

    def get_dst_list(self, src_node, dsts):

        dst_list = []
        rack_id = src_node.rack_id
        if dsts == 'all spine links':
            for intf,value in src_node.interfaces.items():
                if value['peer_type'] == 'spine':
                    dst_list.append(intf)
        elif dsts == 'all inter-f1 links':
            for intf,value in src_node.interfaces.items():
                if value['peer_type'] == 'leaf':
                    dst_list.append(intf)
        elif 'all f1 links' and rack_id == '0':
            for intf,value in src_node.interfaces.items():
                if value['peer_type'] == 'leaf':
                    dst_list.append(intf)
        elif isinstance(dsts, list):
            dst_list = dsts
        else:
            self.logger.warning('Invalid input %s for linkImpair/Repair' % dst_list)
      
        return dst_list 

    def linksRepair(self, src, dsts, oper):

        src_node = self.get_node(src)
        if src_node:
            dst_list = self.get_dst_list(src_node, dsts)
            for dst in dst_list:
                self.linkRepair(src_node, dst, oper)

    def linkRepair(self, src_node, dst, oper):

        if dst not in src_node.interfaces:
            self.logger.warning('Invalid destination %s for linkRepair from %s. Skipping over' % (dst, src_node.name))
            return

        my_intf_name = src_node.interfaces[dst]['my_intf_name']
        peer_intf_name = src_node.interfaces[dst]['peer_intf_name']
        peer_type = src_node.interfaces[dst]['peer_type']
        netem_repair_cmd = 'ip netns exec %s tc qdisc del dev %s root \n' % (src_node.name, my_intf_name) 
        if peer_type == 'leaf':
            netem_repair_cmd += 'ip netns exec %s tc qdisc del dev %s root \n' % (dst, peer_intf_name)

        out = exec_remote_commands([(self.ip, [netem_repair_cmd])], [], logger=self.logger)
        src_node.interfaces[dst]['state'] = 'up'

      
    def linksImpair(self, src, dsts, oper, param1, param2, param3):

        src_node = self.get_node(src)
        if src_node:
            dst_list = self.get_dst_list(src_node, dsts)
            for dst in dst_list:
                self.linkImpair(src_node, dst, oper, param1, param2, param3)

    def linkImpair(self, src_node, dst, oper, param1, param2, param3):

        if dst not in src_node.interfaces:
            self.logger.warning('Invalid destination %s for linkImpair from %s. Skipping over' % (dst, src_node.name))
            return

        my_intf_name = src_node.interfaces[dst]['my_intf_name']
        peer_intf_name = src_node.interfaces[dst]['peer_intf_name']
        peer_type = src_node.interfaces[dst]['peer_type']
        if oper == 'rate':
            netem_impair_cmd = 'ip netns exec %s tc qdisc add dev %s root tbf %s %s ' % \
                               (src_node.name, my_intf_name, oper, param1)
        elif oper == 'loss' and param1 == '100%' and peer_type == 'leaf':
            netem_impair_cmd = 'ip netns exec %s tc qdisc add dev %s root netem %s %s ' % \
                               (src_node.name, my_intf_name, oper, param1)
            netem_impair_cmd += '\nip netns exec %s tc qdisc add dev %s root netem %s %s \n' % \
                               (dst, peer_intf_name, oper, param1)
        else:
            netem_impair_cmd = 'ip netns exec %s tc qdisc add dev %s root netem %s %s ' % \
                               (src_node.name, my_intf_name, oper, param1)

        src_node.interfaces[dst]['state'] = 'Impaired: %s %s ' % (oper, param1)

        if param2:
            if oper == 'rate':
                netem_impair_cmd += 'burst %s ' % param2
                src_node.interfaces[dst]['state'] += 'burst %s ' % param2
            else:
                netem_impair_cmd += '%s ' % param2
                src_node.interfaces[dst]['state'] += '%s ' % param2
        if param3:
            if oper == 'loss':
                netem_impair_cmd += 'distribution %s' % param3
                src_node.interfaces[dst]['state'] += 'distribution %s ' % param3        
            elif oper == 'rate':
                netem_impair_cmd += 'latency %s' % param3
                src_node.interfaces[dst]['state'] += 'latency %s ' % param3
            elif oper == 'reorder':
                netem_impair_cmd += 'delay %s' % param3
                src_node.interfaces[dst]['state'] += 'delay %s ' % param3
            else:
                pass
        out = exec_remote_commands([(self.ip, [netem_impair_cmd])], [], logger=self.logger)

    def flatLinkImpair(self, src, dsts):
        src_node = self.get_node(src) 
        iptables_impair_cmd = ''
        if src_node:
            for dst in dsts:
                iptables_impair_cmd += 'ip netns exec %s iptables -I INPUT -i eth0 -s %s -j DROP \n' % \
                                       (src_node.name, dst.ip)
                iptables_impair_cmd += 'ip netns exec %s iptables -I OUTPUT -o eth0 -d %s -j DROP \n' % \
                                       (src_node.name, dst.ip)

            out = exec_remote_commands([(self.ip, [iptables_impair_cmd])], [], logger=self.logger)

    def flatLinkRepair(self, src, dsts):
        src_node = self.get_node(src)
        iptables_repair_cmd = ''
        if src_node: 
            for dst in dsts:
                iptables_repair_cmd += 'ip netns exec %s iptables -D INPUT -i eth0 -s %s -j DROP \n' % \
                                       (src_node.name, dst.ip)
                iptables_repair_cmd += 'ip netns exec %s iptables -D OUTPUT -o eth0 -d %s -j DROP \n' % \
                                       (src_node.name, dst.ip)

            out = exec_remote_commands([(self.ip, [iptables_repair_cmd])], [], logger=self.logger)

    @retry(tries=100, delay=20)
    def waitOnPsim(self):
        out = exec_remote_commands([(self.ip, [psim_process_count])], [], logger=self.logger)
        if int(out[0]['results'][0]['output']) == self.nRacks*self.nLeafs:
            return True
        else:
            return False

    def get_rack_from_id(self, rack_id):
        if int(rack_id) > self.end_rack_id: 
            self.logger.warning('Rack %s does not exist' % rack_id)
            return None
        index = int(rack_id) - ((self.id-1)*self.topo.max_racks_per_vm) -1
        return self.racks[index]

    def get_rack_from_node(self, node_name):
        rack_id, node_id = node_name.split('-')
        if int(rack_id) > self.end_rack_id or int(node_id) > self.nLeafs: 
            self.logger.warning('Node %s does not exist' % node_name)
            return None
        index = int(rack_id) - ((self.id-1)*self.topo.max_racks_per_vm) -1
        return self.racks[index]

    def get_node(self, node_name):
        rack_id, node_id = node_name.split('-')
        if rack_id == '0':
            if flat_topo:
                index = int(node_id) - ((self.id-1)*self.topo.max_leafs_per_vm) - 1
                return self.leafs[index]
            else:
                index = int(node_id) - ((self.id-1)*self.topo.max_spines_per_vm) - 1
                return self.spines[index]
        else:
            rack_obj = self.get_rack_from_node(node_name)
            return rack_obj.nodes[int(node_id)-1]

    def get_nodes(self):
        nodes = []
        if self.role == 'leaf':
            if flat_topo:
                nodes.extend(self.leafs)
            else:
                for rack in self.racks:
                    nodes.extend(rack.getNodes())
        else:
            nodes.extend(self.spines)
        return nodes
  
    def get_vxlan_range(self):
        return self.get_id_range(self.id, self.num_spineOVS, self.num_spineOVS)

    def get_spine_range(self):
        return self.get_id_range(self.id, self.nSpines, self.topo.max_spines_per_vm)

    def get_rack_range(self):
        return self.get_id_range(self.id, self.nRacks, self.topo.max_racks_per_vm)

    def get_rack_count(self):
        return self.get_count(self.id, self.topo.max_racks_per_vm, self.topo.nRacks)

    def get_spine_count(self):
        return self.get_count(self.id, self.topo.max_spines_per_vm, self.topo.nSpines)

    def get_leaf_range(self):
        return self.get_id_range(self.id, self.nLeafs, self.topo.max_leafs_per_vm)

    def get_leaf_count(self):
        return self.get_count(self.id, self.topo.max_leafs_per_vm, self.topo.nLeafs)

    def get_id_range(self, x, y, z):
        start = x * z - z + 1
        end = start + y 
        return start, end

    def get_count(self, x, y, z):
        if x * y <= z:
            return y
        else:
            return (z - ((x - 1) * y))

    def get_port_id(self):
        res = self.port_id
        self.port_id += 1
        return res

    def cleanup(self):
        self.cleanupNodes()
        self.cleanupBridge()

    def cleanupBridge(self):
        all_bridges = self.leaf_bridges + self.spine_bridges
        bridge_cmd = []
        for bridge in all_bridges:
            if not 'leaf' in bridge.name:
                bridge_cmd.append(ovs_del_br_cmd + bridge.name)
        for cmd in bridge_cmd:
           output = exec_remote_commands([(self.ip, [cmd])], [], timeout=300, logger=self.logger)

    def cleanupNodes(self):
            bridge_names = ''
            node_names = ''
            tgs = ''
            netns_cmd = []
            if self.role == 'leaf':
                if flat_topo:
                    for leaf in self.leafs:
                        node_names += leaf.name
                        node_names += ' '
                        if leaf.tgs:
                            for tg in leaf.tgs:
                                node_names += tg.name
                                node_names += ' '
                else:
                    for rack in self.racks:
                        for node in rack.nodes: 
                            node_names += node.name
                            node_names += ' '
                            if node.tgs:
                                for tg in node.tgs:
                                    node_names += tg.name
                                    node_names += ' '
            else:
                for node in self.spines:
                    node_names += node.name
                    node_names += ' '

            if not node_names:
                return

            unpause_cmd = docker_unpause_cmd + node_names
            kill_cmd = docker_kill_cmd + node_names
            for netns in node_names.split():
                netns_cmd.append(netns_del_cmd + netns)
            final_cleanup = [unpause_cmd] + [kill_cmd] + netns_cmd + docker_mnt_clean_cmd
            if flat_topo and self.topo.total_vms > 1:
                final_cleanup += [docker_swarm_leave_cmd]
            for cmd in final_cleanup:
                output = exec_remote_commands([(self.ip, [cmd])], [], timeout=300, logger=self.logger)


class Rack(object):

    def __init__(self, vm_obj, rack_id):
        """ Rack object. All nodes are created in the context
            of a Rack. Rack 0 is the spine rack.
            Every F1 rack has a unique rack_subnet. Each F1
            further subnets the rack subnet. Spines are given
            a lo address from the spine_lo_subnet. Not really
            used/advertised, but done to set deterministic
            router-id on spines. Inter F1 links subnets are
            the same in each rack
        """

        self.rack_id = rack_id
        self.asn = 64512 + rack_id

        if not flat_topo:
            self.rack_subnet = str(rack_subnets.pop(0))
            # At most 120 inter-F1 subnets
            self.inter_f1_subnets = list(IPNetwork(inter_f1_net).subnet(30))[:121]

        self.nNodes = 0
        self.nodes = []
        self.links = {}
        self.vm_obj = vm_obj
        self.vm_ip = vm_obj.ip
     

    def addNodes(self, nNodes):

        self.nNodes = nNodes
        for node in range(1, nNodes+1):
            self.nodes.append(Node(self.vm_obj, self.rack_id, self.asn, node))

    def configureNodes(self):
        #"Configure nodes for Rack %d" % self.rack_id
        for node in self.nodes:
            node.configure()

    def run(self):
        "Run docker container for all the rack nodes"
        links = ''
        docker_run = ''
        up_link = ''
        for node in self.nodes:
            node.run()
            docker_run += node.docker_run
            links += node.link_config

        return docker_run, links

    def pause(self):
        "Pause docker container for all the rack nodes"
        for node in self.nodes:
            node.pause()

    def unpause(self):
        "Pause docker container for all the rack nodes"
        for node in self.nodes:
            node.unpause()

    def getNode(self, index):
        return self.nodes[index]

    def getNodes(self):
        return self.nodes
        
    def cleanup(self):
        for node in self.nodes:
            node.cleanup()

    def __str__(self):
        "Returns string representation of Rack and all the nodes in it"

        rack_str = 'Rack-id: %s, Rack-ASN: %s, nNodes: %s, Rack-net: %s\n' % \
                   (self.rack_id, self.asn, self.nNodes, str(self.rack_subnet))

        for node in self.nodes:
            rack_str += node.__str__()
            rack_str += '\n'
        return rack_str


class Node(object):

    def __init__(self, vm_obj, rack_id=0, rack_asn=64512, node_id=1):
        """ F1(Leaf)/Spine object

            :param rack_id: 0 for Spine rack. 1..1k for F1 racks.
            :param rack_asn: 64512 for Spine routers. 64513..XXXXX for F1 routers.
            :param node_id: 1..16
            :param public_network: F1 public network or Spine Loopback network.

            Calls add_loopback_ips() to set lo IP address.
        """

        self.vm_obj = vm_obj
        self.node_id = str(node_id)
        self.rack_id = str(rack_id)
        self.asn = str(rack_asn)
        self.tn = None
        self.state = 'init'
        self.zebra_port = self.get_host_port()
        self.bgp_port = self.get_host_port()
        self.isis_port = self.get_host_port()
        self.host_ssh_port = self.get_host_port()
        self.dpcsh_port = self.get_host_port()
        self.ip = ''
        self.vm_ip = self.vm_obj.ip
        self.vm_id = vm_obj.id
        self.container_conn = None
        self.interfaces = {}
        self.tg_interfaces = {}
        self.config = ''
        self.link_config = ''
        self.up_link = ''
        self.zebra_config = ''
        self.bgp_config = ''
        self.isis_config = ''
        self.tgs = []
        self.logger = logging.getLogger(__name__)

        self.name = '%s-%s' % (self.rack_id, self.node_id)

        if flat_topo:
            self.rack_id = '0' 
            self.type = 'leaf'
            self.public_network = ''
            return

        if self.rack_id == '0':
            self.type = 'spine'
            self.public_network = spine_lo_subnets.pop(0)
        else:
            self.type = 'leaf'
            self.public_network = f1_public_subnet.pop(0)

        self.loopback_ips = self.add_loopback_ips()
    

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        d['logger'] = logging.getLogger(__name__)
        self.__dict__.update(d)
    
    def add_interface(self, dst=None, my_intf_name='', my_ip='',
                      prefixlen='', peer_intf_name='', peer_ip='', bridge_name='', vlan='' ):
        """ Update interfaces dictionary that keeps track of
            all the interfaces that this Node connects to. This
            dictionary is used to generate routing configurations
            for both Spine and F1 routers. The interfaces dictionary
            is also used for linkFlap tests.

            :param dst: Destination node
            :param my_intf_name: local node interface
            :param my_ip: local interface IP
            :param prefixlen: netmask of link subnet
            :param peer_intf_name: remote/peer interface name
            :param peer_ip: peer IP
        """

        self.interfaces[dst.name] = {'my_intf_name': my_intf_name,
                                     'my_ip': my_ip,
                                     'prefixlen': prefixlen,
                                     'peer_intf_name': peer_intf_name,
                                     'peer_ip': peer_ip,
                                     'peer_asn': dst.asn,
                                     'peer_type': dst.type,
                                     'state': 'up'
                                     }

        #Links to TG are made from the TG node
        if dst.type == 'traffic_gen':
            return
        #If using VETH on leaf nodes and OVS on spine
        if self.type == dst.type:
            if int(self.node_id) < int(dst.node_id):
                self.link_config += 'ip link add name %s type veth peer name %s\n' % \
                                    (my_intf_name, peer_intf_name)
                self.link_config += 'ip link set %s netns %s\n' % \
                                    (my_intf_name, self.name)
                self.link_config += 'ip netns exec %s ip addr add %s/%s dev %s\n' % \
                                    (self.name, my_ip, prefixlen, my_intf_name)
                self.link_config += 'ip netns exec %s ip link set dev %s up\n' % \
                                    (self.name, my_intf_name)
            else:
                self.link_config += 'ip link set %s netns %s\n' % \
                                    (my_intf_name, self.name)
                self.link_config += 'ip netns exec %s ip addr add %s/%s dev %s\n' % \
                                    (self.name, my_ip, prefixlen, my_intf_name)
                self.link_config += 'ip netns exec %s ip link set dev %s up\n' % \
                                    (self.name, my_intf_name)
        elif self.vm_obj.topo.available_vms == 1:
                self.link_config += 'ip link add name %s type veth peer name %s\n' % \
                                    (my_intf_name, peer_intf_name)
                self.link_config += 'ip link set %s netns %s\n' % \
                                    (my_intf_name, self.name)
                self.link_config += 'ip netns exec %s ip addr add %s/%s dev %s\n' % \
                                    (self.name, my_ip, prefixlen, my_intf_name)
                self.link_config += 'ip netns exec %s ip link set dev %s up\n' % \
                                    (self.name, my_intf_name)
                self.link_config += 'ip link set %s netns %s\n' % \
                                    (peer_intf_name, dst.name)
                self.link_config += 'ip netns exec %s ip addr add %s/%s dev %s\n' % \
                                    (dst.name, peer_ip, prefixlen, peer_intf_name)
                self.link_config += 'ip netns exec %s ip link set dev %s up\n' % \
                                    (dst.name, peer_intf_name)
        else:
            self.link_config += 'ip link set %s netns %s\n' % \
                                (my_intf_name, self.name)
            self.link_config += 'ip netns exec %s ip addr add %s/%s dev %s\n' % \
                                (self.name, my_ip, prefixlen, my_intf_name)
            self.link_config += 'ip netns exec %s ip link set %s up\n' % \
                                (self.name, my_intf_name)
        '''

        #If using OVS for leaf-leaf links
        self.link_config += 'ip link set %s netns %s\n' % (my_intf_name, self.name)
        self.link_config += 'ip netns exec %s ip addr add %s/%s dev %s\n' % (self.name, my_ip, prefixlen, my_intf_name)
        self.link_config += 'ip netns exec %s ip link set %s up\n' % (self.name, my_intf_name)
      
        #Can do ovs-docker directly instead of explicitly linking container namespaces
        self.link_config += 'ovs-docker add-port %s %s %s --ipaddress=%s/%s\n' % (bridge_name, my_intf_name, self.name, my_ip, prefixlen)
        self.link_config += 'ovs-docker set-vlan %s %s %s %d\n' % (bridge_name, my_intf_name, self.name, vlan) 
        ''' 

    def run(self):
        """ Start router by running docker container
            Also setup netns softlink based on returned
            container instance-id
        """
        router_image = docker_images[self.type]
        if flat_topo:
            self.ip = str(f1_mgmt_ips.pop())
            self.public_network = self.ip
            self.docker_run = '%s ' \
                              '--name %s ' \
                              '--hostname ' \
                              'node-%s ' \
                              '--network=mgmt ' \
                              '--ip=%s ' \
                              '-p %s:22 ' \
                              '-p %s:5001 ' \
                              '%s &\n' % \
                      (docker_run_cmd, self.name, self.name, self.ip,
                      self.host_ssh_port, self.dpcsh_port, router_image) 
        else:
            self.ip = self.loopback_ips[0]
            self.docker_run = '%s ' \
                              '--name %s ' \
                              '--hostname ' \
                              'node-%s ' \
                              '-p %s:22 ' \
                              '-p %s:2601 ' \
                              '-p %s:2605 ' \
                              '-p %s:2608 ' \
                              '-p %s:5001 ' \
                              '%s &\n' % \
                     (docker_run_cmd, self.name, self.name,
                      self.host_ssh_port, self.zebra_port, self.bgp_port,
                      self.isis_port, self.dpcsh_port, router_image)

        self.logger.info('Docker command: %s' % self.docker_run)

    def configure(self):
        "Generate routing configuration"
        self.do_zebra_config()
        self.do_bgp_config()
        self.do_isis_config()
        self.state = 'running'

    def do_zebra_config(self):
        if self.state != 'init':
            return
        else:
            zebra_config = 'hostname node-%s\npassword zebra \nservice integrated-vtysh-config\nline vty\n' % self.name
            lo_ip = self.get_loopback_ips()[0]
            zebra_config += 'interface lo \n\t ip address %s%s\n' % (lo_ip, '/32')
            for item in self.interfaces.values():
                zebra_config += 'interface %s \n ip address %s\n' % \
                                (item['my_intf_name'], item['my_ip'])
            self.zebra_config = 'en\n conf t\n' + zebra_config + 'do wr mem\n'
        res = self.exec_command_telnet(self.zebra_port, self.zebra_config.split('\n'))

    def do_bgp_config(self):
        bgp_config = 'hostname node-%s\npassword zebra \nline vty\n' % self.name
        bgp_config += 'router bgp %s \n' % self.asn
        bgp_config += '  bgp router-id %s \n' % self.loopback_ips[0]
        bgp_config += '  bgp bestpath as-path multipath-relax \n'
        bgp_config += '  timers bgp 5 15 \n'
        for intf in self.interfaces:
            if self.type != 'traffi_gen':
                neighbor = self.interfaces[intf]['peer_ip']
                bgp_config += '  neighbor %s remote-as %s \n' % (neighbor, self.interfaces[intf]['peer_asn'])
                if self.type == 'leaf':
                    #if self.interfaces[intf]['peer_type'] == 'leaf':
                    #    bgp_config += '  neighbor %s route-map REMOTE_RACK_RMAP_IBGP_OUT out \n' % neighbor
                    #else:
                    #    bgp_config += '  neighbor %s route-map REMOTE_RACK_RMAP_IN in \n' % neighbor
                    #    bgp_config += '  neighbor %s route-map REMOTE_RACK_RMAP_OUT out \n' % neighbor
                    bgp_config += '  address-family ipv4 unicast \n'
                    bgp_config += '    network %s \n' % str(self.public_network)
                    bgp_config += '    maximum-paths 8 \n'
                    bgp_config += '    maximum-paths ibgp 16 \n'
                    if self.interfaces[intf]['peer_type'] == 'leaf':
                        bgp_config += '    neighbor %s addpath-tx-all-paths \n' % neighbor
                    else:
                        bgp_config += '    neighbor %s next-hop-self \n' % neighbor
        if self.type == 'leaf':
            bgp_config += create_ip_prefix_list('REMOTE_RACK_PREFIX_MATCH_ALL', 'permit', '0.0.0.0/0')
            bgp_config += create_ip_community_list('FILTER_E_I', 'permit', self.asn + ':1')
            bgp_config += create_ip_community_list('FILTER_E_I_E', 'permit', self.asn + ':2')
            bgp_config += create_route_map('REMOTE_RACK_RMAP_IN', self.asn + ':1')
            bgp_config += create_route_map('REMOTE_RACK_RMAP_IBGP_OUT', self.asn + ':2')
            bgp_config += create_route_map('REMOTE_RACK_RMAP_OUT', 'None')
        self.bgp_config = 'en\n conf t\n' + bgp_config + 'do wr mem\n'

        res = self.exec_command_telnet(self.bgp_port, self.bgp_config.split('\n'))

    def do_isis_config(self):

        if self.type != 'leaf':
            return

        ip = convert_ip_to_48bits(self.loopback_ips[0])
        area_id = self.rack_id.zfill(4)
        net = '49.%s.%s.00' % (area_id, ip)
        isis_config = 'hostname node-%s\npassword zebra \nline vty\n' % self.name
        isis_config += 'router isis rack%s\n' % self.rack_id
        isis_config += 'net %s\n' % net
        isis_config += 'is-type level-1\n'
        isis_config += 'metric-style wide\n'
        for intf in self.interfaces:
            if self.interfaces[intf]['peer_type'] == 'leaf':
                isis_config += 'interface %s\n' % self.interfaces[intf]['my_intf_name']
                isis_config += 'ip router isis rack%s\n' % self.rack_id
                isis_config += 'isis circuit-type level-1 \n'
                isis_config += 'isis network point-to-point\n'
                isis_config += 'isis csnp-interval 5 level-1 \n'
                isis_config += 'isis hello-interval 5\n'
                isis_config += 'isis hello-multiplier 2 level-1 \n'
                isis_config += 'isis metric 1 level-1\n'
        self.isis_config = 'en\n conf t\n' + isis_config + 'do wr mem \n'

        if self.type == 'leaf':
            res = self.exec_command_telnet(self.isis_port, self.isis_config.split('\n'))

    def add_loopback_ips(self, count=1):
        """ Generate loopback IPs. Spine loopback IPs
            are not really used. F1 loopback IP comes out of
            F1 public subnet.
        """
        loop_ips = []
        ip_iterator = self.public_network.iter_hosts()
        for i in range(count):
            loop_ips.append(str(ip_iterator.next()))
        return loop_ips

    def get_loopback_ips(self):
        return self.loopback_ips

    def add_ns(self, instance_id):
        """ Add netns symlink for easy
            reference to docker netns
        """
        docker_pid = '%s %s' % (docker_pid_cmd, instance_id)
        out = run_commands(self.vm_conn_handle, [docker_pid])
        pid = out['results'][0]['output']
        ns_ln = 'ln -s /proc/%s/ns/net /var/run/netns/%s' % (pid, self.name)
        output = run_commands(self.vm_conn_handle, [ns_ln])

    def attachTG(self, tg_id):
        tg_obj = TrafficGenerator(self, tg_id)
        self.tgs.append(tg_obj)
        if not flat_topo:
            bridge_obj = self.bridge
            link_obj = Link(tg_obj, self, self.public_network, bridge_obj)
        tg_obj.run()
        self.vm_obj.topo.populate_ssh_config()
        return tg_obj

    def get_host_port(self):
        return (base_port + self.vm_obj.topo.get_next_id()) 

    # Given name of peer node, return local interface details
    def get_interface(self, node_name):
        return self.interfaces[node_name]

    def get_next_tg_id(self):
        return len(self.tgs)+1
 
    def cleanup(self):
        commands = []
        docker_stop = '%s %s' % (docker_kill_cmd, self.name)
        netns_del = '%s %s' % (netns_del_cmd, self.name)
        commands.append(docker_stop)
        commands.append(netns_del)
        for cmds in commands:
            out = exec_remote_commands([(self.vm_ip, [cmds])], [], timeout=300, logger=self.logger)

    def show_route(self):
        show_bgp_summ = ['show ip bgp summ']
        show_ip_route_bgp = ['show ip route ']
        bgp_summ = self.exec_command(self.bgp_port, show_bgp_summ)
        bgp_route = self.exec_command(self.zebra_port, show_ip_route_bgp)
        for i in bgp_summ[0].split('\n'):
            print i
        for i in bgp_route[0].split('\n'):
            print i
        print '**** \n'

    def exec_command(self, cmd, background=True):
        self.container_conn = self.set_container_conn()
        if background:
            cmd = 'nohup ' + cmd + ' > /var/tmp/output 2>&1 &'
            out = run_commands(self.container_conn, [cmd])
            del self.container_conn
            return out

    def set_container_conn(self):
        client = paramiko.SSHClient()
        client.host_ip = self.vm_ip
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.vm_ip, self.host_ssh_port, username='root', password=vm_passwd)
        return client

    def exec_command_telnet(self, port, commandlist):
        """ Telnet into FRR router and execute commandlist
            :returns console output as a list of 1 new line
            separated string.
        """
        if self.tn is None:
            self.tn = telnetlib.Telnet()
        try:
            result = False
            try:
                linesout = list()
                self.tn.open(self.vm_ip, port)
                self.tn.read_until("Password: ")
                self.tn.write(frr_password + '\n')
                self.tn.read_until('> ')
                self.tn.write('enable' + '\n')
                self.tn.read_until('# ')
                for command in commandlist:
                    self.tn.write(command.encode('ascii') + '\n')
                    linesout.append(self.tn.read_until('# ').replace('\r', ' '))
                result = linesout
            except:
                self.logger.warning('Failed to configure node %s. Telnet Failed' % self.name)
                result = None
        finally:
            self.tn.close()

        return result

    def __str__(self):
        "Returns string representation of Node data"
        node_str = '\t node_id: %s, node_name: %s, node_state: %s, node_network: %s \n' % \
                   (self.node_id, self.name, self.state, str(self.public_network))
        node_str += '\t\tLinks to:\n'
        for dst in sorted(self.interfaces):
            node_str = node_str + '\t\t\t -->' + dst + ' '
            for key in sorted(self.interfaces[dst]):
                for item in self.interfaces[dst][key]:
                    node_str += str(item)
                node_str += ' '
            node_str += '\n'
        return node_str

class Link(object):
    _link_id = 0

    def __init__(self, left, right, subnet, left_bridge, right_bridge=None):
        Link._link_id += 1
        self.link_id = Link._link_id
        self.left = left
        self.right = right
        self.subnet = subnet
        self.prefixlen = str(subnet.prefixlen)
        self.left_bridge = left_bridge
        self.right_bridge = right_bridge
        self.interfaces = {}
        if left.type == 'traffic_gen':
            self.configure_TG_link()
        else:
            self.configure()

    def configure(self):
        ip_generator = self.subnet.iter_hosts()
        left_ip = str(ip_generator.next())
        right_ip = str(ip_generator.next())
        if not self.right_bridge:
            left_intf, right_intf, vlan = self.left_bridge.get_leaf_port_pair()
            self.left.add_interface(self.right, left_intf,
                                    left_ip, self.prefixlen,
                                    right_intf, right_ip,
                                    self.left_bridge.name, vlan)
            self.right.add_interface(self.left, right_intf,
                                     right_ip, self.prefixlen, left_intf,
                                     left_ip, self.left_bridge.name, vlan)
        else:
            left_vlan, left_intf = self.left_bridge.get_spine_port()
            right_vlan, right_intf = self.right_bridge.get_spine_port()
            if left_vlan != right_vlan:
                import pdb; pdb.set_trace()
            self.left.add_interface(self.right, left_intf,
                                    left_ip, self.prefixlen,
                                    right_intf, right_ip,
                                    self.left_bridge.name, left_vlan)
            self.right.add_interface(self.left, right_intf,
                                     right_ip, self.prefixlen,
                                     left_intf, left_ip,
                                     self.right_bridge.name, right_vlan)

    def configure_TG_link(self):
        used_ips = len(self.right.loopback_ips) + int(self.left.id) 
        subnet_ips = list(self.subnet.iter_hosts())[used_ips:]

        if len(subnet_ips) < 2:
            self.logger.warning("Can't create TG due to IP exhaustion")
            return
        left_ip = str(subnet_ips.pop(0))
        right_ip = str(subnet_ips.pop(1))
        left_intf, right_intf, vlan = self.left_bridge.get_leaf_port_pair()

        self.left.add_interface(self.right,
                                left_intf, left_ip,
                                self.prefixlen, right_intf,
                                right_ip)
        self.right.add_interface(self.left,
                                 right_intf, right_ip,
                                 self.prefixlen, left_intf,
                                 left_ip)

        self.interfaces[(self.left.name, self.right.name)] = {'left_intf_name': left_intf,
                                                              'left_ip': left_ip,
                                                              'right_intf_name': right_intf,
                                                              'right_ip': right_ip,
                                                              'prefixlen': self.prefixlen,
                                                              'state': 'up'
                                                              }

class Bridge(object):

    def __init__(self, vm_obj, bridge_id, bridge_type, vxlan_id=0, remote_ip=''):
        self.vm_obj = vm_obj
        self.vm_ip = vm_obj.ip
        self.id = bridge_id
        self.type = bridge_type
        self.name = bridge_type + '-' + str(self.id)
        if self.type == 'spine':
            self.vxlan_id = vxlan_id
            self.remote_ip = remote_ip
        self.commands = 'ovs-vsctl add-br %s\novs-vsctl set bridge %s other-config:forward-bpdu=true\n' % \
                        (self.name,self.name)
        self.leaf_vlan_ports = []
        self.spine_vlan_ports = []
        self.logger = logging.getLogger(__name__)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        d['logger'] = logging.getLogger(__name__)
        self.__dict__.update(d)

    def addLeafPorts(self, nPorts):
        port_cmd = ''
        intf_cmd = ''
        vlan = 3 
        self.leaf_ports = nPorts
        port_tuple = tuple()
        for i in range(1, nPorts+1):
            port_id = 'p-' + str(self.get_next_port_id())
            port_cmd += '-- add-port %s %s tag=%d ' % (self.name, port_id , vlan)
            intf_cmd += '-- set interface %s type=internal ' % (port_id)
            port_tuple += (port_id,)
            if not i%2:
                port_tuple += (vlan,)
                self.leaf_vlan_ports.append(port_tuple)
                port_tuple = tuple()
                vlan += 1

        add_port_command = 'ovs-vsctl ' + port_cmd + '\n'
        add_intf_command = 'ovs-vsctl ' + intf_cmd + '\n'

        self.commands += add_port_command
        self.commands += add_intf_command

    def addSpinePorts(self, nPorts):
        self.spine_ports = nPorts
        port_cmd = ''
        intf_cmd = ''
        vxlan_cmd = ''
        trunks = ''
        vlan = 3 
        for i in range(1, nPorts+1):
            port_id = 'p-' + str(self.get_next_port_id())
            port_cmd += '-- add-port %s %s tag=%d ' % (self.name, port_id , vlan)
            intf_cmd += '-- set interface %s type=internal ' % (port_id)
            temp = str(vlan) + ','
            trunks += temp
            self.spine_vlan_ports.append((vlan, port_id))
            vlan += 1
        trunks = trunks.strip(',')

        if not flat_topo:
            vxlan_cmd =  'add-port %s vxlan-%d trunks=%s ' \
                         '-- set interface vxlan-%s type=vxlan ' \
                         'options:remote_ip=%s options:key=%s' % (self.name, self.vxlan_id,
                                                                trunks, self.vxlan_id, self.remote_ip,
                                                                self.vxlan_id)
        else:
            #Flat-topo needs swarm which only supports vxlan.
            vxlan_cmd =  'add-port %s ' \
                         'vxlan-%d trunks=%s ' \
                         '-- set interface ' \
                         'vxlan-%s type=geneve ' \
                         'options:remote_ip=%s' \
                         ' options:key=%s' % (self.name, self.vxlan_id,
                                              trunks, self.vxlan_id, self.remote_ip,
                                              self.vxlan_id)

        #GRE not supported on GCP
        #vxlan_cmd =  'add-port %s gre-%d trunks=%s ' \
        #             '-- set interface gre-%s type=gre ' \
        #             'options:remote_ip=%s options:key=%s' % (self.name, self.vxlan_id,
        #                                                      trunks, self.vxlan_id, self.remote_ip,
        #                                                      self.vxlan_id)


        add_port_command = 'ovs-vsctl ' + port_cmd + '\n'
        add_intf_command = 'ovs-vsctl ' + intf_cmd + '\n'
        add_vxlan_command = 'ovs-vsctl ' + vxlan_cmd + '\n'

        self.commands += add_port_command
        self.commands += add_intf_command
        self.commands += add_vxlan_command

    def run(self): 
        for cmd in self.commands.split('\n'):
           output = exec_remote_commands([(self.vm_ip, [cmd])], [], timeout=300, logger=self.logger)

    def get_leaf_port_pair(self):
        try:
            return self.leaf_vlan_ports.pop(0)
        except:
            import pdb; pdb.set_trace()

    def get_spine_port(self):
        try:
            return self.spine_vlan_ports.pop(0)
        except:
            import pdb; pdb.set_trace()

    def get_next_port_id(self):
        return (self.vm_obj.get_port_id())

    def __str__(self):
        return self.commands

class TrafficGenerator(object):

    def __init__(self, node, tg_id):
        self.id = str(tg_id)
        self.name = 'TG%s-%s' % (self.id, node.name)
        self.node = node
        self.asn = node.asn
        self.type = 'traffic_gen'
        self.vm_ip = node.vm_ip
        self.host_ssh_port = self.get_host_port()
        self.container_conn = None
        self.ip = ''
        self.interfaces = {}
        self.commands = ''
        self.route_command = 'ip route del 10.0.0.0/8\n'
        self.logger = logging.getLogger(__name__)

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d

    def __setstate__(self, d):
        d['logger'] = logging.getLogger(__name__)
        self.__dict__.update(d)

    def run(self):
        """ Start TG by running docker container
            Also setup netns softlink based on returned
            container instance-id
        """
        
        router_image = docker_images[self.type]
        
        if flat_topo:
            self.ip = str(f1_mgmt_ips.pop())
            docker_run = '%s --name %s --hostname %s --network mgmt --ip=%s -p %d:22 %s' % \
                     (docker_run_cmd, self.name, self.name, self.ip, self.host_ssh_port, router_image)
        else:
            docker_run = '%s --name %s --hostname %s -p %d:22 %s' % \
                     (docker_run_cmd, self.name, self.name, self.host_ssh_port, router_image)

        self.logger.info('Docker command: %s' % docker_run)

        out = exec_remote_commands([(self.vm_ip, [docker_run])], [], logger=self.logger)
        
        self.state = 'init'
        self.add_ns()

        #if flat_topo:
        #    self.state = 'running'
        #    return

        command_list = self.commands.split('\n')
        for command in command_list:
            if command:
                out = exec_remote_commands([(self.vm_ip, [command])], [], logger=self.logger)

        self.state = 'running'
 
        for i in range(ssh_retries):
            try:
                self.container_conn = self.set_container_conn()
                break
            except Exception, e:
                time.sleep(2)
        
        self.tg_config(self.route_command)
        #delete connection so that pickling doesnt error out
        self.container_conn = None


    def add_interface(self, dst=None, my_intf_name='', my_ip='',
                      prefixlen='', peer_intf_name='', peer_ip=''):
        """ Update interfaces dictionary that keeps track of
            all the interfaces that this Node connects to. This
            dictionary is used to generate routing configurations
            for both Spine and F1 routers. The interfaces dictionary
            is also used for linkFlap tests.

            :param dst: Destination node
            :param my_intf_name: local node interface
            :param my_ip: local interface IP
            :param prefixlen: netmask of link subnet
            :param peer_intf_name: remote/peer interface name
            :param peer_ip: peer IP
        """

        self.interfaces[dst.name] = {'my_intf_name': my_intf_name,
                                     'my_ip': my_ip,
                                     'prefixlen': prefixlen,
                                     'peer_intf_name': peer_intf_name,
                                     'peer_ip': peer_ip,
                                     'peer_asn': dst.asn,
                                     'peer_type': dst.type,
                                     'state': 'up'
                                     }

        if not flat_topo:

            self.ip = my_ip

            self.commands += 'ip link add name %s type veth peer name %s\n' % \
                             (my_intf_name, peer_intf_name)
            self.commands += 'ip link set %s netns %s\n' % \
                             (my_intf_name, self.name)
            self.commands += 'ip netns exec %s ip addr add %s/%s dev %s\n' %\
                             (self.name, my_ip, prefixlen, my_intf_name)
            self.commands += 'ip netns exec %s ip link set dev %s up\n' % \
                             (self.name, my_intf_name)
            self.commands += 'ip netns exec %s ip link set dev %s mtu 1200\n' % \
                             (self.name, my_intf_name)

            self.commands += 'ip link set %s netns %s\n' % \
                             (peer_intf_name, dst.name)
            self.commands += 'ip netns exec %s ip addr add %s/%s dev %s\n' % \
                             (dst.name, peer_ip, prefixlen, peer_intf_name)
            self.commands += 'ip netns exec %s ip link set %s up\n' % \
                             (dst.name, peer_intf_name)

            route = 'ip route add 10.0.0.0/14 via %s\n' % peer_ip
            self.route_command += route 


    def start_iperf(self, dst, duration=5, background=False):
        if not dst:
            self.logger.warning('TG called with None destination')
            return
        iperf_cmd = 'iperf3 -P 1  -b 200M -t %s -c %s ' % (duration, dst.ip)
        self.logger.info('Starting iperf traffic %s' % iperf_cmd)
        out = self.exec_command(iperf_cmd, background)
        self.state = 'running'
        return out['results'][0]['output'] 

    def start_ab(self, dst, duration=5, background=False):
        if not dst:
            self.logger.warning('TG called with None destination')
            return
        ab_cmd = 'ab -n 1000 -c 100 http://%s:80/1mb' % dst.ip
        self.logger.info('Starting ab traffic %s' % ab_cmd)
        out = self.exec_command(ab_cmd, background)
        self.state = 'running'
        return out['results'][0]['output']

    def stop_iperf(self):
        iperf_cmd = 'kill `pgrep iperf3`'
        out = self.exec_command(iperf_cmd, background=False)
        self.state = 'stopped'
        return out['results'][0]['output']

    def stop_ab(self):
        ab_cmd = 'kill `pgrep ab`'
        out = self.exec_command(ab_cmd, background=False)
        self.state = 'stopped'
        return out['results'][0]['output']

    def exec_command(self, cmd, background=True):
        self.container_conn = self.set_container_conn()
        if background:
            cmd = 'nohup ' + cmd + ' > /var/tmp/output 2>&1 &'
            #cmd = 'echo $$ && exec ' + cmd + ' &> /var/tmp/output &'
        out = run_commands(self.container_conn, [cmd])
        del self.container_conn
        return out

    def set_container_conn(self):
        client = paramiko.SSHClient()
        client.vm_ip = self.vm_ip
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.vm_ip, self.host_ssh_port, username='root', password='fun123')
        return client

    def tg_config(self, commands):
        command_list = commands.split('\n')
        for command in command_list:
            if command:
                out = run_commands(self.container_conn, [command])

    def add_ns(self):
        """ Add netns symlink for easy
            reference to docker netns
        """
        docker_pid = '%s %s' % (docker_pid_cmd, self.name)
        out = exec_remote_commands([(self.vm_ip, [docker_pid])], [], logger=self.logger)
        try:
            pid = out[0]['results'][0]['output'].strip()
        except:
            self.logger.warning('Could not find TG container %s' % self.name)
            return

        ns_ln = 'ln -s /proc/%s/ns/net /var/run/netns/%s' % (pid, self.name)
        out = exec_remote_commands([(self.vm_ip, [ns_ln])], [], logger=self.logger)

    def get_host_port(self):
        return (base_port+self.node.vm_obj.topo.get_next_id())

def main():
    topo = Topology()
    topo.create(2,2,4)
    topo.save()
    pretty(json.loads(getAccessInfo()))
    topo.cleanup()

if __name__ == "__main__":
    main()
