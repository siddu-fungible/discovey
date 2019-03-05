from lib.host.network_controller import *
from lib.system.fun_test import *

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity Test 1",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)
        self.job_environment = fun_test.get_job_environment()
        fun_test.test_assert(self.job_environment, "Job environment provided")
        fun_test.print_key_value(title=None, data=self.job_environment)
        self.dpc_proxy_ip = str(self.job_environment['UART_HOST'])
        self.dpc_proxy_port = int(self.job_environment['UART_TCP_PORT_0'])

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.log("Running Dummy test")
        fun_test.log("Connecting to Remote DPC %s on port %d" % (self.dpc_proxy_ip, self.dpc_proxy_port))
        dpcsh_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port)

        port_list = [1, 2, 3, 4, 5, 15, 18, 13, 17, 20]
        k_list = [x for x in range(0, 16)]

        for i in xrange(0, 50):
            print "<=========================> Iteration: %d  <=========================>" % i
            for port in port_list:
                result = dpcsh_obj.clear_port_stats(port_num=port, shape=0)
                fun_test.simple_assert(result, "Cleat stats port: %d" % port)

            vp_stats = dpcsh_obj.peek_vp_packets()
            fun_test.simple_assert(vp_stats, "Fetch VP stats")
            enable_qos = dpcsh_obj.enable_qos_pfc()
            fun_test.simple_assert(enable_qos, "Enable QoS PFC")
            set_qos = dpcsh_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=7000,
                                                           nonfcp_xoff_thr=7000,
                                                           df_thr=4000,
                                                           dx_thr=4000,
                                                           fcp_thr=8000,
                                                           nonfcp_thr=8000,
                                                           sample_copy_thr=255,
                                                           sf_thr=4000,
                                                           sf_xoff_thr=3500,
                                                           sx_thr=4000)
            fun_test.simple_assert(set_qos, "Enable QoS Egress buffer pool")

            enable_qos_pfc = dpcsh_obj.enable_qos_pfc(hnu=True)
            fun_test.simple_assert(enable_qos_pfc, "Enable QoS PFC")
            set_qos = dpcsh_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=900,
                                                           nonfcp_xoff_thr=3500,
                                                           df_thr=2000,
                                                           dx_thr=1000,
                                                           fcp_thr=1000,
                                                           nonfcp_thr=4000,
                                                           sample_copy_thr=255,
                                                           sf_thr=2000,
                                                           sf_xoff_thr=1900,
                                                           sx_thr=250,
                                                           mode="hnu")
            fun_test.simple_assert(set_qos, "Enable QoS PFC")
            fpg_stats = dpcsh_obj.peek_fpg_port_stats(port_num=5)
            fun_test.simple_assert(fpg_stats, "Fetch FPG stats")
            psw_stats = dpcsh_obj.peek_psw_global_stats()
            fun_test.simple_assert(psw_stats, "Fetch PSW global stats")
            set_ingress_priority_map = dpcsh_obj.set_qos_priority_to_pg_map(port_num=5,
                                                                            map_list=k_list)
            fun_test.simple_assert(set_ingress_priority_map, message="Set priority to pg map")

        '''
        fun_test.log("Running Dummy test")
        fun_test.log("Connecting to Remote DPC %s on port %d" % (self.dpc_proxy_ip, self.dpc_proxy_port))
        network_controller_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port,
                                           verbose=True)

        #hello_output = network_controller_obj.json_execute(verb="echo", data=['frst hello'], command_duration=120)
        hello_output=str(network_controller_obj.echo_hello())
        fun_test.log(hello_output)

        #parser_stats = network_controller_obj.json_execute(verb='peek', data="stats/prsr/nu", command_duration=120)
        parser_stats = network_controller_obj.peek_parser_stats()
        fun_test.log("PSW Stats: %s \n" % parser_stats)

        #hello_output = network_controller_obj.json_execute(verb="echo", data=['2nd hello'], command_duration=120)
        hello_output=str(network_controller_obj.echo_hello())
        fun_test.log(hello_output)

        #network_controller_obj.dpc_shutdown()
        network_controller_obj.disconnect()
        del network_controller_obj

        network_controller_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port,
                                           verbose=True)
        #hello_output = network_controller_obj.json_execute(verb="echo", data=['last hello'], command_duration=120)
        hello_output=str(network_controller_obj.echo_hello())
        fun_test.log(hello_output)

        #del network_controller_obj

        #fun_test.log("sleeping 2 mins...\n")
        #time.sleep(120)
        #network_controller_obj = NetworkController(dpc_server_ip=self.dpc_proxy_ip, dpc_server_port=self.dpc_proxy_port, verbose=True)

        #hello_output=str(network_controller_obj.echo_hello())
        #fun_test.log(hello_output)
        #parser_stats = network_controller_obj.peek_parser_stats()
        #fun_test.log("PSW Stats: %s \n" % parser_stats)


        #network_controller_obj.dpc_shutdown()
        fun_test.test_assert_expected(expected=2, actual=2, message="Some message2")
        '''


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
