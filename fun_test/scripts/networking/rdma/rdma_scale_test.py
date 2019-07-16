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

        if scenario_type in [RdmaHelper.SCENARIO_TYPE_1_1, RdmaHelper.SCENARIO_TYPE_N_1, RdmaHelper.SCENARIO_TYPE_N_N]:
            if 'test_case_ids' in inputs:
                fun_test.selected_test_case_ids = inputs['test_case_ids']
            else:
                fun_test.selected_test_case_ids = [1, 2]
        elif scenario_type == RdmaHelper.SCENARIO_TYPE_LATENCY_UNDER_LOAD:
            fun_test.selected_test_case_ids = [3]

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
        run_infinetly = self.rdma_helper.get_run_infinetly()
        iterations = self.rdma_helper.get_iterations()
        self.rdma_template = RdmaTemplate(test_type=self.test_type, is_parallel=is_parallel,
                                          size=size_in_bytes, duration=duration, inline_size=inline_size,
                                          iterations=iterations, run_infinitely=run_infinetly,
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


class RdmaLatencyUnderLoadTest(FunTestCase):
    lat_test_type = IB_WRITE_LATENCY_TEST
    bw_test_type = IB_WRITE_BANDWIDTH_TEST
    rdma_helper = None
    rdma_template = None
    setup_test = True
    iterations = True

    def describe(self):
        self.set_test_details(id=3, summary="Test RDMA latency under load",
                              steps="""
                              1. Fetch Client/Server Map 
                              2. Setup clients and servers and load modules
                              3. Connect to each client and initiate RDMA BW traffic towards each server and run latency 
                              test in parallel
                              4. Collect all results from each client and display it  
                              """)

    def setup(self):
        scenario_type = fun_test.shared_variables['scenario']
        self.rdma_helper = RdmaHelper(scenario_type=scenario_type)

        checkpoint = "Fetch Client/Server Map Objects"
        client_server_objs = self.rdma_helper.create_lat_under_load_topology()
        fun_test.test_assert(client_server_objs, checkpoint)

        checkpoint = "Setup clients/servers and load modules"
        bw_test_size_in_bytes = self.rdma_helper.get_traffic_size_in_bytes(key_name='bw_test_size_in_bytes')
        lat_test_size_in_bytes = self.rdma_helper.get_traffic_size_in_bytes(key_name='lat_test_size_in_bytes')
        duration = self.rdma_helper.get_traffic_duration_in_secs()
        inline_size = self.rdma_helper.get_inline_size()
        run_infinetly = self.rdma_helper.get_run_infinetly()
        iterations = self.rdma_helper.get_iterations()
        rate_limit = self.rdma_helper.get_rate_limit()
        rate_units = self.rdma_helper.get_rate_units()

        self.rdma_template = RdmaLatencyUnderLoadTemplate(lat_test_type=self.lat_test_type,
                                                          bw_test_type=self.bw_test_type,
                                                          lat_client_server_objs=client_server_objs['lat'],
                                                          bw_client_server_objs=client_server_objs['bw'],
                                                          bw_test_size=bw_test_size_in_bytes,
                                                          lat_test_size=lat_test_size_in_bytes, inline_size=inline_size,
                                                          duration=duration, iterations=iterations,
                                                          run_infinitely=run_infinetly, rate_limit=rate_limit,
                                                          rate_units=rate_units, hosts=self.rdma_helper.host_objs)

        if self.setup_test:
            result = self.rdma_template.setup_test()
            fun_test.test_assert(result, checkpoint)

    def run(self):
        scenario_type = fun_test.shared_variables['scenario']
        if 'cmd_args' in fun_test.shared_variables:
            cmd_args = fun_test.shared_variables['cmd_args']
        else:
            cmd_args = {}

        checkpoint = "Connect to each client and initiate RDMA BW traffic towards each server and run latency test " \
                     "in parallel"
        records = self.rdma_template.run(**cmd_args)
        fun_test.test_assert(records, checkpoint)

        checkpoint = "Result table for %s scenario" % scenario_type
        self.rdma_template.create_table(records=records)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = BasicSetup()
    ts.add_test_case(RdmaWriteBandwidthTest())
    ts.add_test_case(RdmaWriteLatencyTest())
    ts.add_test_case(RdmaLatencyUnderLoadTest())
    ts.run()
