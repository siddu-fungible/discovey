from lib.system.fun_test import *
from lib.system.utils import MultiProcessingTasks
from lib.host.linux import Linux
from lib.host.frr import Frr
import re


NUM_OF_RACKS = 3
NUM_OF_NODES_PER_RACK = 4
NUM_OF_SPINES = 8


def baseline_verifications(tb, check_traffic=False, traffic_dut_node='1-1'):
    """Verify all nodes' BGP neighbors, ISIS neighbors, ip route sum, FRR RIB vs FIB, FRR FIB vs Linux FIB, traffic

    :param
        tb: testbed.TestBed() obj
        check_traffic: bool, whether to check traffic or not
        traffic_dut_node: str, if check_traffic, send bi-directional traffic from this node to all other nodes
    :return:
    """
    verify_bgp_state(tb)
    verify_isis_neigh_state(tb)
    verify_ip_route_sum(tb)
    verify_frr_rib_vs_fib(tb)
    verify_frr_fib_vs_linux_fib(tb)
    if check_traffic:
        verify_traffic(tb, traffic_dut_node)


def verify_bgp_state(tb, check_all_nodes=True):
    """Verify all nodes' BGP neighbor IP, ASN, and state or number of prefixes received

    :param
        tb: testbed.TestBed() obj
        check_all_node: bool
    :return:
    """
    mp_task_obj = MultiProcessingTasks()
    expected_dict = {}
    node_list = tb.get_nodes()
    if not check_all_nodes:
        node_list = node_list[:1]

    node_num_of_ebgp_prefixes = tb.get_node_num_of_ebgp_prefixes()
    node_num_of_ibgp_prefixes = tb.get_node_num_of_ibgp_prefixes()
    for node in node_list:
        frr_obj = Frr(host_ip=node.host_ip,
                      ssh_username=node.ssh_username,
                      ssh_password=node.ssh_password,
                      ssh_port=node.ssh_port)
        mp_task_obj.add_task(func=frr_obj.get_ip_bgp_sum, task_key=node.name)
        bgp_neigh_expected = {'local_ASN': node.asn, 'neighbors': []}
        for peer in node.interfaces:
            if tb.down_links and (node.name in tb.down_links and peer in tb.down_links[node.name] or
                                  peer in tb.down_links and node.name in tb.down_links[peer]):
                num_of_prefixes = r'[Idle|Connect|Active]'
            elif node.interfaces[peer]['peer_type'] == 'spine':
                num_of_prefixes = node_num_of_ebgp_prefixes[node.name][peer]
            elif node.interfaces[peer]['peer_type'] == 'leaf':
                num_of_prefixes = node_num_of_ibgp_prefixes[node.name][peer]
            else:  # peer_type might be 'traffic_gen', too
                continue
            bgp_neigh_expected['neighbors'].append({'ip_addr': node.interfaces[peer]['peer_ip'],
                                                    'ASN': node.interfaces[peer]['peer_asn'],
                                                    'state_prefixes': num_of_prefixes})
        bgp_neigh_expected['neighbors'].sort()
        expected_dict[node.name] = bgp_neigh_expected
    if check_all_nodes:
        msg = "Get BGP neighbor summary from all the nodes"
    else:
        msg = "Get BGP neighbor summary from node %s" % node_list[0].name
    fun_test.test_assert(mp_task_obj.run(), msg)
    for node_name in sorted(expected_dict):
        msg = 'Node %s' % node_name
        if tb.down_links and (node_name in tb.down_links or node_name in sum(tb.down_links.values(), [])):
            bgp_neigh_expected = expected_dict[node_name]
            bgp_neigh_actual = mp_task_obj.get_result(node_name)
            for neigh_expected, neigh_actual in zip(bgp_neigh_expected['neighbors'], bgp_neigh_actual['neighbors']):
                if isinstance(neigh_expected['state_prefixes'], str):
                    msg += 'BGP neighbor %s, %s is not established' % (neigh_expected['ip_addr'], neigh_expected['ASN'])
                    fun_test.test_assert(
                        neigh_expected['ip_addr'] == neigh_actual['ip_addr'] and
                        neigh_expected['ASN'] == neigh_actual['ASN'] and
                        re.search(neigh_expected['state_prefixes'], neigh_actual['state_prefixes']),
                        msg)
        else:
            fun_test.test_assert_expected(
                expected=expected_dict[node_name], actual=mp_task_obj.get_result(node_name), message=msg)


def verify_isis_neigh_state(tb):
    """Verify all nodes' ISIS neighbors' system id, interface, and state is up

    :param tb: testbed.TestBed() obj
    :return:
    """
    mp_task_obj = MultiProcessingTasks()
    expected_dict = {}
    node_list = tb.get_nodes()
    for node in node_list:
        frr_obj = Frr(host_ip=node.host_ip,
                      ssh_username=node.ssh_username,
                      ssh_password=node.ssh_password,
                      ssh_port=node.ssh_port)
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


def verify_ip_route_sum(tb):
    """Verify all F1s' number of Routes/FIB learnt from all the protocols

    :param
        tb: testbed.TestBed() obj
    :return:
    """
    node_list = tb.get_nodes()
    # number of connected routes = connected to spines + connected to all F1 peers + local SVI connected to HU + eth0
    node_num_of_spine_links = tb.get_node_num_of_spine_links()
    node_num_of_connected_routes = {}
    for node in node_list:
        num_of_connected_routes = node_num_of_spine_links[node.name] + (tb.num_of_nodes_per_rack - 1) + 2
        node_num_of_connected_routes.update({node.name: num_of_connected_routes})

    # the connected routes are installed as connected FIB, not ISIS
    num_of_isis_routes = tb.num_of_nodes_per_rack * (tb.num_of_nodes_per_rack - 1) / 2
    num_of_isis_fibs = num_of_isis_routes - (tb.num_of_nodes_per_rack - 1)
    node_num_of_ebgp_routes = tb.get_node_num_of_ebgp_prefixes()
    num_of_ibgp_routes = tb.num_of_nodes_per_rack - 1

    mp_task_obj = MultiProcessingTasks()
    expected_dict = {}
    for node in node_list:
        frr_obj = Frr(host_ip=node.host_ip,
                      ssh_username=node.ssh_username,
                      ssh_password=node.ssh_password,
                      ssh_port=node.ssh_port)
        mp_task_obj.add_task(func=frr_obj.get_ip_route_sum, task_key=node.name)

        n_connected_routes = node_num_of_connected_routes[node.name]
        n_isis_routes = num_of_isis_routes
        n_isis_fibs = num_of_isis_fibs
        n_ebgp_routes = max(node_num_of_ebgp_routes[node.name].values())
        n_ibgp_routes = num_of_ibgp_routes

        ip_route_sum_expected = {
            'connected': {'Routes': n_connected_routes,
                          'FIB': n_connected_routes},
            'isis': {'Routes': n_isis_routes,
                     'FIB': n_isis_fibs},
            'ebgp': {'Routes': n_ebgp_routes,
                     'FIB': n_ebgp_routes},
            'ibgp': {'Routes': n_ibgp_routes,
                     'FIB': n_ibgp_routes}}
        expected_dict[node.name] = ip_route_sum_expected
    fun_test.test_assert(mp_task_obj.run(), "Get ip route summary from all the nodes")
    for node_name in sorted(expected_dict):
        msg = 'Node %s' % node_name
        fun_test.test_assert_expected(
            expected=expected_dict[node_name], actual=mp_task_obj.get_result(node_name), message=msg)


def verify_frr_rib_vs_fib(tb):
    """Verify all nodes' FRR RIB and FIB are consistent

    :param tb: testbed.TestBed() obj
    :return:
    """
    mp_task_rib_obj = MultiProcessingTasks()
    mp_task_fib_obj = MultiProcessingTasks()
    node_list = tb.get_nodes()
    for node in node_list:
        frr_obj = Frr(host_ip=node.host_ip,
                      ssh_username=node.ssh_username,
                      ssh_password=node.ssh_password,
                      ssh_port=node.ssh_port)
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
        msg = 'Node %s: RIB vs. FIB consistency\n' % node.name
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


def verify_frr_fib_vs_linux_fib(tb):
    """Verify all nodes' FRR FIB and Linux kernel FIB are consistent

    :param tb: testbed.TestBed() obj
    :return:
    """
    mp_task_frr_obj = MultiProcessingTasks()
    mp_task_lnx_obj = MultiProcessingTasks()
    node_list = tb.get_nodes()
    for node in node_list:
        frr_obj = Frr(host_ip=node.host_ip,
                      ssh_username=node.ssh_username,
                      ssh_password=node.ssh_password,
                      ssh_port=node.ssh_port)
        lnx_obj = Linux(host_ip=node.host_ip, ssh_username=node.ssh_username, ssh_password=node.ssh_password)
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
        for k, v in frr_prefixes_only.items():
            if v == {'directly connected': 'lo'}:  # Exclude loopback interface
                frr_prefixes_only.pop(k)
        lnx_prefixes_only = {k: v for k, v in lnx.items() if k not in frr}
        nhp_diff_frr = {k: v for k, v in frr.items() if k in lnx and v != lnx[k]}
        nhp_diff_lnx = {k: v for k, v in lnx.items() if k in frr and v != frr[k]}
        msg = 'Node %s: FRR FIB vs. Linux FIB consistency\n' % node.name
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


def verify_traffic(tb, dut_node='1-1'):
    """Verify bi-directional traffic from one node to all other nodes

    :param
        tb: testbed.TestBed() obj
        dut_node: str
    :return:
    """
    node_list = tb.get_nodes()

    # Attach traffic generator to all nodes
    mp_task_obj = MultiProcessingTasks()
    tg_dict = {}
    for node in node_list:
        tg_dict[node.name] = tb.topo.attachTG(node.name)
        # TODO: mp_task doesn't work because of tg id conflict, after Amit fixes it, change to mp_task
        # mp_task_obj.add_task(func=self.script_obj.topo.attachTG, func_args=(node.name,), task_key=node.name)
        # fun_test.test_assert(mp_task_obj.run(), "Attach traffic generator to all F1 nodes")

        # for node in node_list:
        # tg_dict.update({node.name: mp_task_obj.get_result(node.name)})

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