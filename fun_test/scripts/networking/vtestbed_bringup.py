from lib.system.fun_test import *
from lib.topology.topology_manager.topo_manager.topo import Topology
from lib.system.utils import MultiProcessingTasks
from lib.host.frr import Frr
import math


NUM_OF_RACKS = 5
NUM_OF_F1_PER_RACK = 4
NUM_OF_SPINES = 8


class BringUpTestBed(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Step 1: Call topo_manager to create test bed, R * F * S - 
                    R: number of racks, F: number of F1s per rack, S: number of spines
        2. Step 2: Verify BGP neighbors' ip addrs and ASNs match what are configured, and prefixes received match 
                    expected number
        3. Step 3: Verify ISIS neighbors' system id, interface match what are configured, and state is up
        4. Step 4: Verify number of routes learnt
        """)

    def setup(self):
        self.topo = Topology()
        self.topo.create(NUM_OF_RACKS, NUM_OF_F1_PER_RACK, NUM_OF_SPINES)  # TODO: put testbed parameters in json/yml
        fun_test.sleep("Wait for BGP/ISIS to converge", seconds=2)

    def cleanup(self):
        self.topo.cleanup()


class VerifyBgpNeighborState(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Verify all F1s' BGP neighbor IP, ASN, and state or number of prefixes received",
                              steps="""
        1. Step 1: Go through every node(F1) in every rack, get each BGP neighbor's ip addr, ASN, and state or # of 
                    prefixes received
        2. Step 2: Verify BGP neighbor ip addr and ASN match what are configured, and # of prefixes received match below
                    2.1 # of prefixes from spine == (# of racks - 1) * # of F1 per rack
                    2.2 # of prefixes from F1 == # of prefixes from spine * (# of spines / # of F1 per rack) + 1
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self, check_all_node=True):
        mp_task_obj = MultiProcessingTasks()
        expected_dict = {}
        node_list = []
        for vm in self.script_obj.topo.leaf_vm_objs:
            for rack in vm.racks:
                for node in rack.nodes:
                    node_list.append(node)
        if not check_all_node:
            node_list = node_list[:1]
        for node in node_list:
            key = (node.rack_id, node.node_id)
            frr_obj = Frr(host_ip=node.vm_ip, ssh_username="root", ssh_password="fun123", ssh_port=node.host_ssh_port)
            mp_task_obj.add_task(func=frr_obj.get_ip_bgp_sum, task_key=key)
            bgp_neigh_expected = {'local_ASN': node.asn, 'neighbors': []}
            for p in node.interfaces:
                if node.interfaces[p]['peer_type'] == 'spine':
                    num_of_prefixes = (NUM_OF_RACKS - 1) * NUM_OF_F1_PER_RACK
                elif node.interfaces[p]['peer_type'] == 'leaf':
                    num_of_prefixes = ((NUM_OF_RACKS - 1) * NUM_OF_F1_PER_RACK) * int(
                        math.ceil(float(NUM_OF_SPINES) / NUM_OF_F1_PER_RACK)) + 1
                bgp_neigh_expected['neighbors'].append({'ip_addr': node.interfaces[p]['peer_ip'],
                                                        'ASN': node.interfaces[p]['peer_asn'],
                                                        'state_prefixes': str(num_of_prefixes)})
            bgp_neigh_expected['neighbors'].sort()
            expected_dict[key] = bgp_neigh_expected
        fun_test.test_assert(mp_task_obj.run(), "Get BGP neighbor summary")
        for key in sorted(expected_dict):
            msg = 'Rack %s Node %s' % key
            fun_test.test_assert_expected(expected=expected_dict[key], actual=mp_task_obj.get_result(key), message=msg)


class VerifyBgpNeighborStateQuick(VerifyBgpNeighborState):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Verify one F1s' BGP neighbor IP, ASN, and state or number of prefixes received",
                              steps="""
        1. Step 1: From one F1 (e.g. rack 1 node 1), get each BGP neighbor's ip addr, ASN, and state or # of prefixes 
                    received
        2. Step 2: Verify BGP neighbor ip addr and ASN match what are configured, and # of prefixes received match below
                    2.1 # of prefixes from spine == (# of racks - 1) * # of F1 per rack
                    2.2 # of prefixes from F1 == # of prefixes from spine * (# of spines / # of F1 per rack) + 1
        """)

    def run(self):
        VerifyBgpNeighborState.run(self, check_all_node=False)


class VerifyIsisNeighborState(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Verify all F1s' ISIS neighbors' system id, interface, and state is up",
                              steps="""
        1. Step 1: Go through every node(F1) in every rack, get each ISIS neighbor's state
        2. Step 2: Verify neighbor's system id, interface, and state is 'Up'
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        mp_task_obj = MultiProcessingTasks()
        expected_dict = {}
        node_list = []
        for vm in self.script_obj.topo.leaf_vm_objs:
            for rack in vm.racks:
                for node in rack.nodes:
                    node_list.append(node)
        for node in node_list:
            key = (node.rack_id, node.node_id)
            frr_obj = Frr(
                host_ip=node.vm_ip, ssh_username="root", ssh_password="fun123", ssh_port=node.host_ssh_port)
            mp_task_obj.add_task(func=frr_obj.get_isis_neighbor, task_key=key)
            isis_neigh_expected = {}
            for p in node.interfaces:
                if node.interfaces[p]['peer_type'] == 'leaf':
                    isis_neigh_expected.update({'System_Id': 'node-%s' % p,
                                                'Interface': node.interfaces[p]['my_intf_name'],
                                                'State': 'Up'})
            expected_dict[key] = isis_neigh_expected
        fun_test.test_assert(mp_task_obj.run(), "Get ISIS neighbor info")
        for key in sorted(expected_dict):
            msg = 'Rack %s Node %s' % key
            fun_test.test_assert_expected(expected=expected_dict[key], actual=mp_task_obj.get_result(key), message=msg)


if __name__ == "__main__":
    tb = BringUpTestBed()
    tb.add_test_case(VerifyBgpNeighborState(tb))
    tb.add_test_case(VerifyIsisNeighborState(tb))
    tb.add_test_case(VerifyBgpNeighborStateQuick(tb))
    tb.run()