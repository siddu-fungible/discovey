from lib.system.fun_test import *
from lib.topology.topology_manager.topo_manager.topo import Topology
from lib.system.utils import MultiProcessingTasks
from lib.host.linux import Linux
from lib.host.frr import Frr
import math
import re


NUM_OF_RACKS = 5
NUM_OF_F1_PER_RACK = 8
NUM_OF_SPINES = 8

SSH_USERNAME = 'root'
SSH_PASSWORD = 'fun123'

# number of BGP prefixes from spine, which is eBGP
NUM_OF_EBGP_PREFIXES = (NUM_OF_RACKS - 1) * NUM_OF_F1_PER_RACK
# number of BGP prefixes from peer F1, which is iBGP
NUM_OF_SPINE_LINKS = int(math.ceil(float(NUM_OF_SPINES) / NUM_OF_F1_PER_RACK))
NUM_OF_IBGP_PREFIXES = NUM_OF_EBGP_PREFIXES * NUM_OF_SPINE_LINKS + 1

# number of connected routes == connected to spines + connected to all F1 peers + local SVI connected to HU + eth0
NUM_OF_CONNECTED_ROUTES = NUM_OF_SPINE_LINKS + (NUM_OF_F1_PER_RACK - 1) + 2
NUM_OF_CONNECTED_FIB = NUM_OF_CONNECTED_ROUTES

# the connected routes are installed as connected FIB, not ISIS
NUM_OF_ISIS_ROUTES = NUM_OF_F1_PER_RACK * (NUM_OF_F1_PER_RACK - 1) / 2
NUM_OF_ISIS_FIB = NUM_OF_ISIS_ROUTES - (NUM_OF_F1_PER_RACK - 1)

NUM_OF_EBGP_ROUTES = NUM_OF_EBGP_PREFIXES
NUM_OF_EBGP_FIB = NUM_OF_EBGP_ROUTES

NUM_OF_IBGP_ROUTES = NUM_OF_F1_PER_RACK - 1
NUM_OF_IBGP_FIB = NUM_OF_IBGP_ROUTES

CONVERGE_TIME = 90


class BringUpTestBed(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Step 1: Call topo_manager to create test bed, R * F * S - 
                    R: number of racks, F: number of F1s per rack, S: number of spines
        2. Step 2: Verify all F1s' BGP neighbor IP, ASNs match what are configured, and prefixes received match what is
                    expected (state is up) in 'show ip bgp sum'
        3. Step 3: Verify all F1s' ISIS neighbors' system id, interface match what are configured, and state is up in 
                    'show isis neighbor'
        4. Step 4: Verify all F1s' number of Routes/FIB learnt from connected/isis/ebgp/ibgp in 'show ip route summary' 
        5. Step 5: Verify all F1s' FRR RIB and FIB are consistent in 'show ip route' and 'show ip fib'
        6. Step 6: Verify all F1s' FRR FIB and Linux kernel FIB are consistent in 'show ip fib' and 'ip -n <netns> route
                    show'
        7. Step 7: Verify bi-directional traffic from one F1 to all other F1s
        """)

    def setup(self):
        self.topo = Topology()
        self.topo.create(NUM_OF_RACKS, NUM_OF_F1_PER_RACK, NUM_OF_SPINES)  # TODO: put testbed parameters in json/yml
        fun_test.sleep("Wait for BGP/ISIS to converge", seconds=CONVERGE_TIME)

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
            frr_obj = Frr(host_ip=node.vm_ip, ssh_username=SSH_USERNAME, ssh_password=SSH_PASSWORD, ssh_port=node.host_ssh_port)
            mp_task_obj.add_task(func=frr_obj.get_ip_bgp_sum, task_key=node.name)
            bgp_neigh_expected = {'local_ASN': node.asn, 'neighbors': []}
            for p in node.interfaces:
                if node.interfaces[p]['peer_type'] == 'spine':
                    num_of_prefixes = NUM_OF_EBGP_PREFIXES
                elif node.interfaces[p]['peer_type'] == 'leaf':
                    num_of_prefixes = NUM_OF_IBGP_PREFIXES
                bgp_neigh_expected['neighbors'].append({'ip_addr': node.interfaces[p]['peer_ip'],
                                                        'ASN': node.interfaces[p]['peer_asn'],
                                                        'state_prefixes': num_of_prefixes})
            bgp_neigh_expected['neighbors'].sort()
            expected_dict[node.name] = bgp_neigh_expected
        if check_all_node:
            msg = "Get BGP neighbor summary from all the nodes"
        else:
            msg = "Get BGP neighbor summary from node %s" % node_list[0].name
        fun_test.test_assert(mp_task_obj.run(), msg)
        for node_name in sorted(expected_dict):
            msg = 'Node %s' % node_name
            fun_test.test_assert_expected(
                expected=expected_dict[node_name], actual=mp_task_obj.get_result(node_name), message=msg)


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
        1. Step 1: Go through every F1 in every rack, get each ISIS neighbor's state
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
            frr_obj = Frr(
                host_ip=node.vm_ip, ssh_username=SSH_USERNAME, ssh_password=SSH_PASSWORD, ssh_port=node.host_ssh_port)
            mp_task_obj.add_task(func=frr_obj.get_isis_neighbor, task_key=node.name)
            isis_neigh_expected = {}
            for p in node.interfaces:
                if node.interfaces[p]['peer_type'] == 'leaf':
                    isis_neigh_expected.update({'System_Id': 'node-%s' % p,
                                                'Interface': node.interfaces[p]['my_intf_name'],
                                                'State': 'Up'})
            expected_dict[node.name] = isis_neigh_expected
        fun_test.test_assert(mp_task_obj.run(), "Get ISIS neighbor info from all the nodes")
        for node_name in sorted(expected_dict):
            msg = 'Node %s' % node_name
            fun_test.test_assert_expected(
                expected=expected_dict[node_name], actual=mp_task_obj.get_result(node_name), message=msg)


class VerifyIpRouteSum(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Verify all F1s' number of Routes/FIB learnt from all the protocols",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get ip route summary
        2. Step 2: Verify number of Routes and FIB learnt from connected/isis/ebgp/ibgp
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
            frr_obj = Frr(
                host_ip=node.vm_ip, ssh_username=SSH_USERNAME, ssh_password=SSH_PASSWORD, ssh_port=node.host_ssh_port)
            mp_task_obj.add_task(func=frr_obj.get_ip_route_sum, task_key=node.name)
            ip_route_sum_expected = {'connected': {'Routes': NUM_OF_CONNECTED_ROUTES, 'FIB': NUM_OF_CONNECTED_FIB},
                                     'isis': {'Routes': NUM_OF_ISIS_ROUTES, 'FIB': NUM_OF_ISIS_FIB},
                                     'ebgp': {'Routes': NUM_OF_EBGP_ROUTES, 'FIB': NUM_OF_EBGP_FIB},
                                     'ibgp': {'Routes': NUM_OF_IBGP_ROUTES, 'FIB': NUM_OF_IBGP_FIB}}
            expected_dict[node.name] = ip_route_sum_expected
        fun_test.test_assert(mp_task_obj.run(), "Get ip route summary from all the nodes")
        for node_name in sorted(expected_dict):
            msg = 'Node %s' % node_name
            fun_test.test_assert_expected(
                expected=expected_dict[node_name], actual=mp_task_obj.get_result(node_name), message=msg)


class VerifyIpRibAndFib(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Verify all F1s' FRR RIB and FIB are consistent",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get FRR RIB info and FIB info
        2. Step 2: Verify prefixes/nexthops/interfaces are consistent
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        mp_task_rib_obj = MultiProcessingTasks()
        mp_task_fib_obj = MultiProcessingTasks()
        node_list = []
        for vm in self.script_obj.topo.leaf_vm_objs:
            for rack in vm.racks:
                for node in rack.nodes:
                    node_list.append(node)
        for node in node_list:
            frr_obj = Frr(
                host_ip=node.vm_ip, ssh_username=SSH_USERNAME, ssh_password=SSH_PASSWORD, ssh_port=node.host_ssh_port)
            mp_task_rib_obj.add_task(func=frr_obj.get_ip_route, task_key=node.name)
            mp_task_fib_obj.add_task(func=frr_obj.get_ip_fib, task_key=node.name)
        fun_test.test_assert(mp_task_rib_obj.run(), "Get ip RIB of FRR from all the nodes")
        fun_test.test_assert(mp_task_fib_obj.run(), "Get ip FIB of FRR from all the nodes")
        for node in node_list:
            rib = mp_task_rib_obj.get_result(node.name)
            fun_test.log('Node %s - RIB: %s' % (node.name, rib))
            fib = mp_task_rib_obj.get_result(node.name)
            fun_test.log('Node %s - FIB: %s' % (node.name, fib))
            rib_prefixes_only = {k: v for k, v in rib.items() if k not in fib}
            fib_prefixes_only = {k: v for k, v in fib.items() if k not in rib}
            nhp_diff_rib = {k: v for k, v in rib.items() if k in fib and v != fib[k]}
            nhp_diff_fib = {k: v for k, v in fib.items() if k in fib and v != rib[k]}
            msg = 'Node %s\n' % node.name
            if rib_prefixes_only:
                msg += 'Prefixes in FRR RIB but not in FRR FIB: %s\n' % rib_prefixes_only
            if fib_prefixes_only:
                msg += 'Pefixes in FRR FIB but not in FRR RIB: %s\n' % fib_prefixes_only
            if nhp_diff_rib or nhp_diff_fib:
                msg += """Prefixes in FRR RIB and FRR FIB, but with different next-hop
                            - RIB: %s
                            - FIB: %s
                            """ % (nhp_diff_rib, nhp_diff_fib)
            fun_test.test_assert(
                not rib_prefixes_only and not fib_prefixes_only and not nhp_diff_rib and not nhp_diff_rib, message=msg)


class VerifyIpFibAndLinuxFib(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Verify all F1s' FRR FIB and Linux kernel FIB are consistent",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get FRR FIB and Linux kernel FIB
        2. Step 2: Verify prefixes/nexthops/interfaces are consistent
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        mp_task_frr_obj = MultiProcessingTasks()
        mp_task_lnx_obj = MultiProcessingTasks()
        node_list = []
        for vm in self.script_obj.topo.leaf_vm_objs:
            for rack in vm.racks:
                for node in rack.nodes:
                    node_list.append(node)
        for node in node_list:
            frr_obj = Frr(
                host_ip=node.vm_ip, ssh_username=SSH_USERNAME, ssh_password=SSH_PASSWORD, ssh_port=node.host_ssh_port)
            lnx_obj = Linux(host_ip=node.vm_ip, ssh_username=SSH_USERNAME, ssh_password=SSH_PASSWORD)
            mp_task_frr_obj.add_task(func=frr_obj.get_ip_fib, task_key=node.name)
            mp_task_lnx_obj.add_task(func=lnx_obj.get_ip_route, func_args=(node.name,), task_key=node.name)
        fun_test.test_assert(mp_task_frr_obj.run(), "Get ip FIB of FRR from all the nodes")
        fun_test.test_assert(mp_task_lnx_obj.run(), "Get ip FIB of Linux kernel from all the nodes")
        for node in node_list:
            frr = mp_task_frr_obj.get_result(node.name)
            fun_test.log('Node %s - FRR FIB: %s' % (node.name, frr))
            lnx = mp_task_lnx_obj.get_result(node.name)
            fun_test.log('Node %s - Linux FIB: %s' % (node.name, lnx))
            frr_prefixes_only = {k: v for k, v in frr.items() if k not in lnx}
            for k,v in frr_prefixes_only.items():
                if v == {'directly connected': 'lo'}:  # Exclude loopback interface
                    frr_prefixes_only.pop(k)
            lnx_prefixes_only = {k: v for k, v in lnx.items() if k not in frr}
            nhp_diff_frr = {k: v for k, v in frr.items() if k in lnx and v != lnx[k]}
            nhp_diff_lnx = {k: v for k, v in lnx.items() if k in frr and v != frr[k]}
            msg = 'Node %s\n' % node.name
            if frr_prefixes_only:
                msg += 'Prefixes in FRR FIB but not in Linux kernel FIB: %s\n' % frr_prefixes_only
            if lnx_prefixes_only:
                msg += 'Prefixes in Linux kernel FIB but not in FRR FIB: %s\n' % lnx_prefixes_only
            if nhp_diff_frr or nhp_diff_lnx:
                msg += """Prefixes in FRR FIB and Linux kernel FIB, but with different next-hop
                            - FRR: %s
                            - Linux: %s
                            """ % (nhp_diff_frr, nhp_diff_lnx)
            fun_test.test_assert(
                not frr_prefixes_only and not lnx_prefixes_only and not nhp_diff_frr and not nhp_diff_lnx, message=msg)


class VerifyTraffic(FunTestCase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Verify traffic from one F1 to all other F1s",
                              steps="""
        1. Step 1: From one F1 (e.g. rack 1 node 1), use iperf to send TCP traffic (1.25MB) to all other F1
        2. Step 2: Verify the traffic sent and received
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        dut_node = '1-1'
        expected_dict = {}
        node_list = []
        for vm in self.script_obj.topo.leaf_vm_objs:
            for rack in vm.racks:
                for node in rack.nodes:
                    node_list.append(node)

        # Attach traffic generator to all nodes
        mp_task_obj = MultiProcessingTasks()
        tg_dict = {}
        for node in node_list:
            tg_dict[node.name] = self.script_obj.topo.attachTG(node.name)
            # TODO: mp_task doesn't work because of tg id conflict, after Amit fixes it, change to mp_task
            #mp_task_obj.add_task(func=self.script_obj.topo.attachTG, func_args=(node.name,), task_key=node.name)
        #fun_test.test_assert(mp_task_obj.run(), "Attach traffic generator to all F1 nodes")

        #for node in node_list:
            #tg_dict.update({node.name: mp_task_obj.get_result(node.name)})

        # Send traffic from DUT node to all other nodes
        mp_task_obj2 = MultiProcessingTasks()
        output_dict = {}
        for node in node_list:
            if node.name == dut_node:
                continue
            mp_task_obj2.add_task(
                func=tg_dict[dut_node].start_iperf, func_args=(tg_dict[node.name],), task_key=node.name)
        fun_test.test_assert(mp_task_obj2.run(), "Send traffic from %s to all other F1" % dut_node)

        for node in node_list:
            if node.name == dut_node:
                continue
            output = mp_task_obj2.get_result(node.name)
            fun_test.log('%s: %s' % (node.name, output))
            output_dict.update({node.name: output})

        pat = re.compile(r'1.25 MBytes.*\s+0\s+sender.*1.25 MBytes.*receiver', re.DOTALL)
        for node_name in sorted(output_dict):
            msg = 'Traffic between Node %s and Node %s' % (dut_node, node_name)
            fun_test.test_assert(pat.search(output_dict[node_name]) is not None, message=msg)


if __name__ == "__main__":
    tb = BringUpTestBed()
    for tc in (VerifyBgpNeighborState,
               VerifyIsisNeighborState,
               VerifyBgpNeighborStateQuick,
               VerifyIpRouteSum,
               VerifyIpRibAndFib,
               VerifyIpFibAndLinuxFib,
               VerifyTraffic,):
        tb.add_test_case(tc(tb))
    tb.run()
