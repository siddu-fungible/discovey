from lib.system.fun_test import *
from scripts.networking.lib_nw import testbed, verifications


NUM_OF_RACKS = 3
NUM_OF_NODES_PER_RACK = 4
NUM_OF_SPINES = 8

CONVERGE_TIME = 30


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
        7. Step 7: Verify bi-directional traffic between one F1 and all other F1s
        """)

    def setup(self):
        self.tb = testbed.TestBed(NUM_OF_RACKS, NUM_OF_NODES_PER_RACK, NUM_OF_SPINES)
        msg = 'Call topo_manager to create virtual test bed'
        fun_test.test_assert(self.tb.create_topo(), msg)
        fun_test.sleep("Wait for BGP/ISIS/RIB/FIB to converge", seconds=CONVERGE_TIME)

    def cleanup(self):
        self.tb.cleanup()


class VerifyBgpNeighborState(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Verify all F1s' BGP neighbor IP, ASN, and state or number of prefixes received",
                              steps="""
        1. Step 1: Go through every node(F1) in every rack, get each BGP neighbor's ip addr, ASN, and state or # of 
                    prefixes received in 'show ip bgp sum'
        2. Step 2: Verify BGP neighbor ip addr and ASN match what are configured, and # of prefixes received match below
                    2.1 # of prefixes from spine == (# of racks - 1) * # of F1 per rack
                    2.2 # of prefixes from F1 == # of prefixes from spine * (# of spines / # of F1 per rack) + 1
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        verifications.verify_bgp_state(self.script_obj.tb)


class VerifyBgpNeighborStateQuick(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Verify one F1s' BGP neighbor IP, ASN, and state or number of prefixes received",
                              steps="""
        1. Step 1: From one F1 (e.g. rack 1 node 1), get each BGP neighbor's ip addr, ASN, and state or # of prefixes 
                    received in 'show ip bgp sum'
        2. Step 2: Verify BGP neighbor ip addr and ASN match what are configured, and # of prefixes received match below
                    2.1 # of prefixes from spine == (# of racks - 1) * # of F1 per rack
                    2.2 # of prefixes from F1 == # of prefixes from spine * (# of spines / # of F1 per rack) + 1
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        verifications.verify_bgp_state(self.script_obj.tb, check_all_node=False)


class VerifyIsisNeighborState(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Verify all F1s' ISIS neighbors' system id, interface, and state is up",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get each ISIS neighbor's state in 'show isis neighbor'
        2. Step 2: Verify neighbor's system id, interface, and state is 'Up'
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        verifications.verify_isis_neigh_state(self.script_obj.tb)


class VerifyIpRouteSum(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Verify all F1s' number of Routes/FIB learnt from all the protocols",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get 'show ip route summary'
        2. Step 2: Verify number of Routes and FIB learnt from connected/isis/ebgp/ibgp
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        verifications.verify_ip_route_sum(self.script_obj.tb)


class VerifyIpRibAndFib(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Verify all F1s' FRR RIB and FIB are consistent",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get FRR RIB info ('show ip route') and FIB info ('show ip fib')
        2. Step 2: Verify prefixes/nexthops/interfaces are consistent
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        verifications.verify_frr_rib_vs_fib(self.script_obj.tb)


class VerifyIpFibAndLinuxFib(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Verify all F1s' FRR FIB and Linux kernel FIB are consistent",
                              steps="""
        1. Step 1: Go through every F1 in every rack, get FRR FIB ('show ip fib') and Linux kernel FIB ('ip -n <netns> 
                    route show')
        2. Step 2: Verify prefixes/nexthops/interfaces are consistent
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        verifications.verify_frr_fib_vs_linux_fib(self.script_obj.tb)


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
        verifications.verify_traffic(self.script_obj.tb, dut_node='1-1')


if __name__ == "__main__":
    ts = BringUpTestBed()
    for tc in (VerifyBgpNeighborState,
               VerifyIsisNeighborState,
               VerifyBgpNeighborStateQuick,
               VerifyIpRouteSum,
               VerifyIpRibAndFib,
               VerifyIpFibAndLinuxFib,
               VerifyTraffic,
               ):
        ts.add_test_case(tc(ts))
    ts.run()
