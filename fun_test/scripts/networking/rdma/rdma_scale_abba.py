from lib.system.fun_test import *
from lib.templates.networking.rdma_template_abba import *
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
        if 'combined_log' in inputs:
            fun_test.shared_variables['combined_log'] = inputs['combined_log']
        else:
            fun_test.shared_variables['combined_log'] = 0
        if 'already_deployed' in inputs:
            fun_test.shared_variables['already_deployed'] = inputs['already_deployed']
        else:
            fun_test.shared_variables['already_deployed'] = True
        fun_test.shared_variables['scenario'] = scenario_type

        if scenario_type in [RdmaHelper.SCENARIO_TYPE_1_1, RdmaHelper.SCENARIO_TYPE_N_1, RdmaHelper.SCENARIO_TYPE_N_N]:
            if 'test_case_ids' in inputs:
                fun_test.selected_test_case_ids = inputs['test_case_ids']
            else:
                fun_test.selected_test_case_ids = [1, 2]
        elif scenario_type == RdmaHelper.SCENARIO_TYPE_LATENCY_UNDER_LOAD:
            fun_test.selected_test_case_ids = [3]
        elif scenario_type == RdmaHelper.SCENARIO_TYPE_ABBA_LATENCY_UNDER_LOAD:
            fun_test.selected_test_case_ids = [4]
        elif scenario_type == RdmaHelper.SCENARIO_TYPE_N_2:
            fun_test.selected_test_case_ids = [5]

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
        run_infinitely = self.rdma_helper.get_run_infinitely()
        iterations = self.rdma_helper.get_iterations()
        qpairs = self.rdma_helper.get_qpairs()
        ib_device = self.rdma_helper.get_ibdev()

        if fun_test.shared_variables["combined_log"]:
            self.combined_log = fun_test.shared_variables["combined_log"]
        else:
            self.combined_log = self.rdma_helper.get_combined_log()

        if (self.combined_log and scenario_type == "N_1") and self.test_type == "ib_write_bw":
            self.rdma_template = RdmaTemplate(test_type=self.test_type, is_parallel=is_parallel,
                                              size=size_in_bytes, duration=duration, inline_size=inline_size,
                                              iterations=iterations, qpairs=qpairs, run_infinitely=run_infinitely,
                                              client_server_objs=client_server_objs, hosts=self.rdma_helper.host_objs,
                                              combined_log=self.combined_log, ib_device=ib_device)
        else:
            self.rdma_template = RdmaTemplate(test_type=self.test_type, is_parallel=is_parallel,
                                              size=size_in_bytes, duration=duration, inline_size=inline_size,
                                              iterations=iterations, qpairs=qpairs, run_infinitely=run_infinitely,
                                              client_server_objs=client_server_objs, hosts=self.rdma_helper.host_objs,
                                              ib_device=ib_device)
        if not fun_test.shared_variables['already_deployed']:
            result = self.rdma_template.setup_test()
            fun_test.test_assert(result, checkpoint)

    def run(self):
        scenario_type = fun_test.shared_variables['scenario']
        if 'cmd_args' in fun_test.shared_variables:
            cmd_args = fun_test.shared_variables['cmd_args']
        else:
            cmd_args = {}

        checkpoint = "Connect to each client and initiate RDMA traffic towards each server"
        output_record = self.rdma_template.run(**cmd_args)
        if (scenario_type == "N_1" and self.combined_log) and self.test_type == "ib_write_bw":
            records = output_record[0]
            output_record.pop(0)
            for index, i in enumerate(records):
                for j in output_record:
                    i.update(j[index])
        else:
            records = output_record

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
        self.set_test_details(id=3, summary="Test RDMA latency under load : N->1 BW & Lat",
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
        iterations = self.rdma_helper.get_iterations()
        run_infinitely = self.rdma_helper.get_run_infinitely()
        qpairs = self.rdma_helper.get_qpairs()
        ib_device = self.rdma_helper.get_ibdev()

        self.rdma_template = RdmaLatencyUnderLoadTemplate(lat_test_type=self.lat_test_type,
                                                          bw_test_type=self.bw_test_type,
                                                          lat_client_server_objs=client_server_objs['lat'],
                                                          bw_client_server_objs=client_server_objs['bw'],
                                                          bw_test_size=bw_test_size_in_bytes,
                                                          lat_test_size=lat_test_size_in_bytes, inline_size=inline_size,
                                                          duration=duration, iterations=iterations,
                                                          run_infinitely=run_infinitely,
                                                          qpairs=qpairs,
                                                          hosts=self.rdma_helper.host_objs,
                                                          connection_type=None,
                                                          ib_device=ib_device)

        if not fun_test.shared_variables['already_deployed']:
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
        self.rdma_template.cleanup()


class AbbaLatencyUnderLoadTest(FunTestCase):
    lat_test_type = IB_WRITE_LATENCY_TEST
    bw_test_type = IB_WRITE_BANDWIDTH_TEST
    rdma_helper = None
    rdma_template = None
    setup_test = True
    iterations = True

    def describe(self):
        self.set_test_details(id=4, summary="ABBA : Test RDMA latency under load : N<->N BW & Lat",
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
        iterations = self.rdma_helper.get_iterations()
        run_infinitely = self.rdma_helper.get_run_infinitely()
        qpairs = self.rdma_helper.get_qpairs()
        ib_device = self.rdma_helper.get_ibdev()

        self.rdma_template = RdmaLatencyUnderLoadTemplate(lat_test_type=self.lat_test_type,
                                                          bw_test_type=self.bw_test_type,
                                                          lat_client_server_objs=client_server_objs['lat'],
                                                          bw_client_server_objs=client_server_objs['bw'],
                                                          bw_test_size=bw_test_size_in_bytes,
                                                          lat_test_size=lat_test_size_in_bytes, inline_size=inline_size,
                                                          duration=duration, iterations=iterations,
                                                          run_infinitely=run_infinitely,
                                                          qpairs=qpairs,
                                                          hosts=self.rdma_helper.host_objs,
                                                          connection_type=None,
                                                          ib_device=ib_device)

        if not fun_test.shared_variables['already_deployed']:
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
        self.rdma_template.cleanup()


class RdmaLatencyUnderLoadN2(FunTestCase):
    lat_test_type = IB_WRITE_LATENCY_TEST
    bw_test_type = IB_WRITE_BANDWIDTH_TEST
    rdma_helper = None
    rdma_template = None
    setup_test = True
    iterations = True

    def describe(self):
        self.set_test_details(id=5, summary="Test RDMA latency under load : N->2 BW & Lat",
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
        iterations = self.rdma_helper.get_iterations()
        run_infinitely = self.rdma_helper.get_run_infinitely()
        qpairs = self.rdma_helper.get_qpairs()
        ib_device = self.rdma_helper.get_ibdev()

        self.rdma_template = RdmaLatencyUnderLoadTemplate(lat_test_type=self.lat_test_type,
                                                          bw_test_type=self.bw_test_type,
                                                          lat_client_server_objs=client_server_objs['lat'],
                                                          bw_client_server_objs=client_server_objs['bw'],
                                                          bw_test_size=bw_test_size_in_bytes,
                                                          lat_test_size=lat_test_size_in_bytes, inline_size=inline_size,
                                                          duration=duration, iterations=iterations,
                                                          run_infinitely=run_infinitely,
                                                          qpairs=qpairs,
                                                          hosts=self.rdma_helper.host_objs,
                                                          connection_type=None,
                                                          ib_device=ib_device)

        if not fun_test.shared_variables['already_deployed']:
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
        self.rdma_template.cleanup()


if __name__ == '__main__':
    ts = BasicSetup()
    ts.add_test_case(RdmaWriteBandwidthTest())
    # ts.add_test_case(RdmaWriteLatencyTest())
    ts.add_test_case(RdmaLatencyUnderLoadTest())
    ts.add_test_case(AbbaLatencyUnderLoadTest())
    ts.add_test_case(RdmaLatencyUnderLoadN2())
    ts.run()
