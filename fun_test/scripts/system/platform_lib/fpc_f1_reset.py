from scripts.system.platform_lib.platform_test_cases import *

# --environment={\"test_bed_type\":\"fs-104\",\"bundle_image_parameters\":{\"release_train\":\"master\",\"build_number\":\"176\"}}


class MultipleF1Reset(PlatformGeneralTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.iterations = 10
        self.initialize_job_inputs()

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(fs_parameters={"already_deployed": False})
        self.topology = topology_helper.deploy()
        fun_test.test_assert(self.topology, "Topology deployed")

        self.fs_obj = self.topology.get_dut_instance(index=0)
        self.dpc_f1_0 = self.fs_obj.get_dpc_client(0)
        self.dpc_f1_1 = self.fs_obj.get_dpc_client(1)
        self.come_handle = self.fs_obj.get_come()
        self.bmc_handle = self.fs_obj.get_bmc()

    def run(self):

        for iteration in range(self.iterations):
            fun_test.add_checkpoint("Iteration : {} of {}".format(iteration+1, self.iterations))

            self.stop_cc_linux_n_health()
            self.run_fpc_stress_test()
            self.check_i2c_error_in_funos_logs()

            self.bmc_handle.reset_f1(0)
            self.bmc_handle.reset_f1(1)
            fun_test.sleep("F1's to reset", seconds=50)

            self.check_i2c_error_in_funos_logs()
            self.come_handle.reboot()
            if iteration != (self.iterations - 1):
                come = self.fs_obj.get_come()
                come.initialize()
                come.setup_dpc()
                fun_test.test_assert(expression=come.ensure_dpc_running(),
                                     message="Ensure dpc is running")
                self.dpc_f1_0 = self.fs_obj.get_dpc_client(0)
                self.dpc_f1_1 = self.fs_obj.get_dpc_client(1)
                self.come_handle = self.fs_obj.get_come()
                self.bmc_handle = self.fs_obj.get_bmc()

    def initialize_job_inputs(self):
        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Input: {}".format(job_inputs))
        if job_inputs:
            for k, v in job_inputs.iteritems():
                setattr(self, k, v)

    def stop_cc_linux_n_health(self):
        try:
            self.come_handle.stop_health_monitors()
        except Exception as e:
            fun_test.critical(e)
        try:
            self.come_handle.stop_cc_health_check()
        except Exception as e:
            fun_test.critical(e)
        try:
            self.come_handle.stop_cclinux_service()
        except Exception as e:
            fun_test.critical(e)

    def run_fpc_stress_test(self):
        self.get_dpcsh_data_for_cmds("async fpc_stresstest", f1=0)
        self.get_dpcsh_data_for_cmds("async fpc_stresstest", f1=1)
        fun_test.sleep("For tests to run")

    def check_i2c_error_in_funos_logs(self):
        f1_0_log = self.fs_obj.get_uart_log_file(0)
        f1_1_log = self.fs_obj.get_uart_log_file(1)

        result = self.parse_uart_log_for_i2c_error(f1_0_log)
        fun_test.test_assert(result, "I2C error not seen on F1_0")
        result = self.parse_uart_log_for_i2c_error(f1_1_log)
        fun_test.test_assert(result, "I2C error not seen on F1_1")

    def parse_uart_log_for_i2c_error(self, uart_log):
        result = True
        with open(uart_log, "r") as f:
            lines = f.readlines()
            for line in lines:
                match_i2c = re.search(r"smbus read cmd write failed\(-\w+\)! master:\s?2", line)
                if match_i2c:
                    result = False
                    break
        return result

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(MultipleF1Reset())
    myscript.run()