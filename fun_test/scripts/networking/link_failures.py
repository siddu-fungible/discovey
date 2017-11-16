from lib.system.fun_test import *
from scripts.networking.lib_nw import testbed, verifications, failures
import testbed_bringup


fun_test.enable_pause_on_failure()


class LinkFailures(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Step 1: One Node to one Spine - single link failure
        2. Step 2: One Node to all peer Spines - all links failure
        3. Step 3: One Node to one peer Node - single link failure
        4. Step 4: One Node to all peer Nodes - all links failure, causing isolation
        5. Step 5: One Rack, multiple Nodes -  multiple links failure, causing half-half isolation
        6. Step 6: Multiple Racks, multiple Nodes - multiple links failure, causing M topo
        7. Step 7: Multiple Racks, multiple Nodes - multiple links failure, causing M topo + half-half isolation
        8. Step 8: Multiple Racks, multiple Nodes - multiple links failure, causing X-circle topo
        """)

    def setup(self):
        self.tb = testbed.TestBed(testbed_bringup.NUM_OF_RACKS,
                                  testbed_bringup.NUM_OF_NODES_PER_RACK,
                                  testbed_bringup.NUM_OF_SPINES)
        msg = 'Call topo_manager to create virtual test bed'
        fun_test.test_assert(self.tb.create_topo(), msg)
        fun_test.sleep("Wait for BGP/ISIS/RIB/FIB to converge", seconds=testbed_bringup.CONVERGE_TIME)
        verifications.baseline_verifications(self.tb)

    def cleanup(self):
        self.tb.cleanup()


class NodeSpineSingleLinkFailure(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Shutdown one link between Node and Spine and verify BGP/ISIS/RIB/FIB/traffic",
                              steps="""
        1. Step 1: Shutdown one link between one Node and one Spine
        2. Step 2: Verify below on all the nodes,
                    - BGP neighbors, 
                    - ISIS neighbors, 
                    - ip route sum, 
                    - FRR RIB vs FIB, 
                    - FRR FIB vs Linux FIB, 
                    - traffic between one node and all other nodes
        3. Step 3: No shutdown the link
        4. Step 4: Verify the same in step 2
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        failures.link_failures(self.script_obj.tb, src_node_name='1-1', dst_node_names='0-1')


class NodeAllSpineLinksFailure(FunTestCase):
    def describe(self):
        self.set_test_details(id=2  ,
                              summary="Shutdown all the spine links of a Node and verify BGP/ISIS/RIB/FIB/traffic",
                              steps="""
        1. Step 1: Shutdown all the spine links of of a Node
        2. Step 2: Verify below on all the nodes,
                    - BGP neighbors, 
                    - ISIS neighbors, 
                    - ip route sum, 
                    - FRR RIB vs FIB, 
                    - FRR FIB vs Linux FIB, 
                    - traffic between one node and all other nodes
        3. Step 3: No shutdown the link
        4. Step 4: Verify the same in step 2
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        failures.link_failures(self.script_obj.tb, src_node_name='1-1', dst_node_names='all spine links')


class NodeNodeSingleLinkFailure(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Shutdown one link between Node and peer Node and verify BGP/ISIS/RIB/FIB/traffic",
                              steps="""
        1. Step 1: Shutdown one link between one Node and its peer Node
        2. Step 2: Verify below on all the nodes,
                    - BGP neighbors, 
                    - ISIS neighbors, 
                    - ip route sum, 
                    - FRR RIB vs FIB, 
                    - FRR FIB vs Linux FIB, 
                    - traffic between one node and all other nodes
        3. Step 3: No shutdown the link
        4. Step 4: Verify the same in step 2
        """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        failures.link_failures(self.script_obj.tb, src_node_name='1-1', dst_node_names='1-2')


if __name__ == "__main__":
    ts = LinkFailures()
    for tc in (NodeSpineSingleLinkFailure,
               NodeAllSpineLinksFailure,
               NodeNodeSingleLinkFailure,
               ):
        ts.add_test_case(tc(ts))
    ts.run()
