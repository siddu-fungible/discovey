from lib.system.fun_test import *
from lib.templates.networking.rdma_template import *


class BasicSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Bringup FS1600 
        2. Configure Hosts nad bringup topo
        """)

    def setup(self):
        inputs = fun_test.get_job_inputs()
        scenario_type = inputs['scenario']
        fun_test.shared_variables['scenario'] = scenario_type

    def cleanup(self):
        pass


class RdmaWriteBandwidthTest(FunTestCase):
    rdma_helper = None
    rdma_template = None

    def describe(self):
        scenario_type = fun_test.shared_variables['scenario']
        self.set_test_details(id=1, summary="Test RDMA Write Bandwidth Scenario: %s" % scenario_type,
                              steps="""
                              1. Fetch Client/Server Map 
                              2. Setup clients and servers and load modules
                              3. Connect to each client and initiate RDMA traffic towards each server
                              4. Collect all results from each client and display it  
                              """)

    def setup(self):
        scenario_type = fun_test.shared_variables['scenario']
        self.rdma_helper = RdmaHelper(scenario_type=scenario_type)
        client_server_map = self.rdma_helper.get_client_server_map()
        fun_test.simple_assert(client_server_map, "Fetch client-server map in json for %s scenario" % scenario_type)

        checkpoint = "Fetch Client/Server Map Objects"
        client_server_objs = self.rdma_helper.create_client_server_objects(client_server_map=client_server_map)
        fun_test.test_assert(client_server_objs, checkpoint)

        checkpoint = "Setup clients/servers and load modules"
        size_in_bytes = self.rdma_helper.get_traffic_size_in_bytes()
        duration = self.rdma_helper.get_traffic_duration_in_secs()
        is_parallel = self.rdma_helper.is_parallel()
        inline_size = self.rdma_helper.get_inline_size()
        self.rdma_template = RdmaTemplate(servers=client_server_objs.values(), clients=client_server_objs.keys(),
                                          test_type=IB_WRITE_BANDWIDTH_TEST, is_parallel=is_parallel,
                                          size=size_in_bytes, duration=duration, inline_size=inline_size)
        result = self.rdma_template.setup_test()
        fun_test.test_assert(result, checkpoint)

    def run(self):
        scenario_type = fun_test.shared_variables['scenario']
        checkpoint = "Connect to each client and initiate RDMA write bandwidth traffic towards each server"
        records = self.rdma_template.run()
        fun_test.test_assert(records, checkpoint)

        checkpoint = "Result table for %s scenario" % scenario_type
        self.rdma_template.create_table(records=records, scenario_type=scenario_type)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        pass
