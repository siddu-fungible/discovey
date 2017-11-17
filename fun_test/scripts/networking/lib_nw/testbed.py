from lib.host.linux import Linux
from lib.host.frr import Frr
from lib.topology.topology_manager.topo_manager.topo import Topology
import math


class TestBed:
    """Testbed consists of Nodes."""
    def __init__(self, num_of_racks, num_of_nodes_per_rack, num_of_spines, virtual=True):
        self.num_of_racks = num_of_racks
        self.num_of_nodes_per_rack = num_of_nodes_per_rack
        self.num_of_spines = num_of_spines
        self.virtual = True
        if self.virtual:
            self.topo = Topology()
        else:  # TODO: handle physical test bed
            pass
        self.node_list = []
        self.down_links = {}  # dict of links - {<src node>: [dst nodes]}, e.g. {'1-1': ['0-1', '0-2']}
        self.node_num_of_spine_links = {}  # dict, e.g. {'1-1': 2, ..}
        self.node_num_of_ebgp_prefixes = {}  # dict, e.g. {'1-1': {'0-1': 8}, '0-2': 8, ..}, ..}
        self.node_num_of_ibgp_prefixes = {}  # dict, e.g. {'1-1': {'1-2': 17, '1-3': 17, ..}, ..}

    def create_topo(self):
        if self.virtual:
            self.topo.create(self.num_of_racks, self.num_of_nodes_per_rack, self.num_of_spines)
        else:  # TODO: create topo for physical test bed
            pass
        return True

    def cleanup(self):
        if self.virtual:
            self.topo.cleanup()

    def get_nodes(self):
        """Get list of Node objs"""
        if self.node_list:
            return self.node_list
        elif self.virtual:
            for vm in self.topo.leaf_vm_objs:
                for rack in vm.racks:
                    for node in rack.nodes:
                        node_obj = Node(name=node.name,
                                        host_ip=node.vm_ip,
                                        ssh_port=node.host_ssh_port,
                                        interfaces=node.interfaces,
                                        asn=node.asn)
                        self.node_list.append(node_obj)
        else:  # TODO: get nodes from physical test bed
            pass
        return self.node_list

    def get_node_from_name(self, node_name):
        """Get Node obj from node's name"""
        if not self.node_list:
            self.node_list = self.get_nodes()
        for node in self.node_list:
            if node.name == node_name:
                return node

    def get_node_num_of_spine_links(self):
        """Calculate number of spine links of all nodes.

        :return: dict, {<node1>: <num_of_spine_links>, ..}
        """
        if self.node_num_of_spine_links:
            return self.node_num_of_spine_links
        self.node_num_of_spine_links = {}
        node_list = self.get_nodes()
        base_num_of_spine_links = int(math.ceil(float(self.num_of_spines) / self.num_of_nodes_per_rack))
        for node in node_list:
            self.node_num_of_spine_links.update({node.name: base_num_of_spine_links})
            if self.down_links and node.name in self.down_links:
                for peer in node.interfaces:
                    if peer in self.down_links[node.name]:
                        if node.interfaces[peer]['peer_type'] == 'spine':
                            self.node_num_of_spine_links[node.name] -= 1
        return self.node_num_of_spine_links

    def get_node_num_of_ebgp_prefixes(self):
        """Calculate number of ebgp prefixes of all nodes' spine link interfaces.

        :return: dict, {<node1>: {<peer1>: <num_of_ebgp_prefixes>}, ..}, ..}
        """
        if self.node_num_of_ebgp_prefixes:
            return self.node_num_of_ebgp_prefixes
        self.node_num_of_ebgp_prefixes = {}
        node_list = self.get_nodes()
        base_num_of_ebgp_prefixes = (self.num_of_racks - 1) * self.num_of_nodes_per_rack
        for node in node_list:
            self.node_num_of_ebgp_prefixes.update({node.name: {}})
            for peer in node.interfaces:
                if node.interfaces[peer]['peer_type'] == 'spine':
                    if self.down_links:
                        if node.name in self.down_links:
                            if peer in self.down_links[node.name]:
                                num_of_ebgp_prefixes = 0
                            else:
                                num_of_ebgp_prefixes = base_num_of_ebgp_prefixes
                        else:
                            if peer in sum(self.down_links.values(), []):
                                num_of_ebgp_prefixes = base_num_of_ebgp_prefixes - self.num_of_nodes_per_rack
                            else:
                                num_of_ebgp_prefixes = base_num_of_ebgp_prefixes
                    else:
                        num_of_ebgp_prefixes = base_num_of_ebgp_prefixes
                    self.node_num_of_ebgp_prefixes[node.name].update({peer: num_of_ebgp_prefixes})
        return self.node_num_of_ebgp_prefixes

    def get_node_num_of_ibgp_prefixes(self):
        """Calculate number of ibgp prefixes of all nodes' inter-nodes interfaces.

        :return: dict, {<node1>: {<peer1>: <num_of_ibgp_prefixes>}, ..}, ..}
        """
        if self.node_num_of_ibgp_prefixes:
            return self.node_num_of_ibgp_prefixes
        self.node_num_of_ibgp_prefixes = {}
        node_num_of_ebgp_prefixes = self.get_node_num_of_ebgp_prefixes()
        node_list = self.get_nodes()
        for node in node_list:
            self.node_num_of_ibgp_prefixes.update({node.name: {}})
            for peer in node.interfaces:
                if node.interfaces[peer]['peer_type'] == 'leaf':
                    self.node_num_of_ibgp_prefixes[node.name].update(
                        {peer: sum(node_num_of_ebgp_prefixes[peer].values()) + 1})
        return self.node_num_of_ibgp_prefixes

    def shutdown_links(self, src_node_name, dst_node_names, no_shut=False):
        """Shutdown links between sr_node and dst_nodes

        :param
            src_node_name: str, e.g. '1-1'
            dst_node_names: list of str, e.g. ['1-3', '0-2', '0-3']
            no_shut: bool
        :return: bool
        """
        if self.virtual:
            if no_shut:
                func = self.topo.linkRepair
                op = 'no_shut'
            else:
                func = self.topo.linkImpair
                op = 'shut'
            func(src_node_name, dst_node_names, op)
        else:  # TODO: do it for physical test bed
            pass

        # update self.down_links
        if no_shut:
            if src_node_name in self.down_links:
                self.down_links[src_node_name] = [n for n in self.down_links[src_node_name] if n not in dst_node_names]
        else:
            self.down_links.setdefault(src_node_name, []).extend(dst_node_names)

        # re-initialize below to trigger re-calculation
        self.node_num_of_spine_links = {}
        self.node_num_of_ebgp_prefixes = {}
        self.node_num_of_ibgp_prefixes = {}

        return True

    def no_shutdown_links(self, src_node_name, dst_node_names):
        return self.shutdown_links(src_node_name, dst_node_names, no_shut=True)


class Node(Frr):
    """Node class for F1, physical test bed and virtual one should have uniformed Node class."""
    def __init__(self,
                 name,
                 host_ip,
                 ssh_username='root', ssh_password='fun123', ssh_port=Linux.SSH_PORT_DEFAULT,
                 interfaces=None,
                 asn=None):
        Frr.__init__(self, host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password, ssh_port=ssh_port)
        self.name = name
        self.interfaces = interfaces
        self.asn = asn

    def get_peers(self, type):
        """Get all the peer spine or leaf nodes.

        :param type: str, 'spine' or 'leaf'
        :return:
        """
        result = []
        for peer in self.interfaces:
            if self.interfaces[peer]['peer_type'] == type:
                result.append(peer)
        return result

    def get_peer_spines(self):
        """Get all the peer spines."""
        return self.get_peers(type='spine')

    def get_peer_nodes(self):
        """Get all the peer  nodes."""
        return self.get_peers(type='leaf')