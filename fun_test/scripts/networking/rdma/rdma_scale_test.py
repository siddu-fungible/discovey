from lib.system.fun_test import *
from lib.templates.networking.rdma_template import *
import argparse


class BasicSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Bringup FS1600
        2. Bringup FunCP
        3. Apply abstract configs  
        4. Configure Hosts and bringup topo
        """)

    def setup(self):
        inputs = fun_test.get_job_inputs()
        scenario_type = inputs['scenario']
        if 'cmd_args' in inputs:
            cmd_args = inputs['cmd_args']
            fun_test.shared_variables['cmd_args'] = cmd_args
        fun_test.shared_variables['scenario'] = scenario_type

        # TODO: Add Bringup Logic

    def cleanup(self):
        pass


class RdmaWriteBandwidthTest(FunTestCase):
    rdma_helper = None
    rdma_template = None
    test_type = IB_WRITE_BANDWIDTH_TEST
    setup_test = True
    iterations = False

    def describe(self):
        self.set_test_details(id=1, summary="Test RDMA Write Bandwidth",
                              steps="""
                              1. Fetch Client/Server Map 
                              2. Setup clients and servers and load modules
                              3. Connect to each client and initiate RDMA traffic towards each server
                              4. Collect all results from each client and display it  
                              """)

    def setup(self):
        scenario_type = fun_test.shared_variables['scenario']
        self.rdma_helper = RdmaHelper(scenario_type=scenario_type)

        checkpoint = "Fetch Client/Server Map Objects"
        client_server_objs = self.rdma_helper.create_client_server_objects()
        fun_test.test_assert(client_server_objs, checkpoint)

        checkpoint = "Setup clients/servers and load modules"
        size_in_bytes = self.rdma_helper.get_traffic_size_in_bytes()
        duration = self.rdma_helper.get_traffic_duration_in_secs()
        is_parallel = self.rdma_helper.is_parallel()
        inline_size = self.rdma_helper.get_inline_size()
        self.rdma_template = RdmaTemplate(test_type=self.test_type, is_parallel=is_parallel,
                                          size=size_in_bytes, duration=duration, inline_size=inline_size,
                                          client_server_objs=client_server_objs, hosts=self.rdma_helper.host_objs)
        if self.setup_test:
            result = self.rdma_template.setup_test()
            fun_test.test_assert(result, checkpoint)

    def run(self):
        scenario_type = fun_test.shared_variables['scenario']
        if 'cmd_args' in fun_test.shared_variables:
            cmd_args = fun_test.shared_variables['cmd_args']
        else:
            cmd_args = {}

        checkpoint = "Connect to each client and initiate RDMA traffic towards each server"
        records = self.rdma_template.run(**cmd_args)
        fun_test.test_assert(records, checkpoint)

        checkpoint = "Result table for %s scenario" % scenario_type
        self.rdma_template.create_table(records=records, scenario_type=scenario_type)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        self.rdma_template.cleanup()


class RdmaWriteLatencyTest(RdmaWriteBandwidthTest):
    test_type = IB_WRITE_LATENCY_TEST
    rdma_helper = None
    rdma_template = None
    setup_test = False
    iterations = True

    def describe(self):
        self.set_test_details(id=2, summary="Test RDMA Write Latency",
                              steps="""
                              1. Fetch Client/Server Map 
                              2. Setup clients and servers and load modules
                              3. Connect to each client and initiate RDMA traffic towards each server
                              4. Collect all results from each client and display it  
                              """)


if __name__ == '__main__':
    ts = BasicSetup()
    ts.add_test_case(RdmaWriteBandwidthTest())
    ts.add_test_case(RdmaWriteLatencyTest())
    ts.run()
