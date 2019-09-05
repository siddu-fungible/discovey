from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_rfc2544_template import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *


network_controller_obj = None
spirent_config = None
TIMESTAMP = None


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Connect to DPCSH and configure egress NU/HNU buffer_pool and enable global PFC
        """)

    def _setup_fcp_external_routes(self):
        username = 'root'
        pc_3_password = 'Precious1*'
        pc_4_password = "fun123"
        cadence_pc_3 = "cadence-pc-3"
        cadence_pc_4 = "cadence-pc-4"
        pc_3_config_dir = fun_test.get_helper_dir_path() + "/pc_3_fcp_configs"
        pc_4_config_dir = fun_test.get_helper_dir_path() + "/pc_4_fcp_configs"

        # Copy req files to cadence pc 3
        target_file_path = "/tmp"
        pc_3_obj = Linux(host_ip=cadence_pc_3, ssh_username=username, ssh_password=pc_3_password)
        for file_name in ['nh_fcp.sh']:
            fun_test.log("Coping %s file to cadence pc 3 in /tmp dir" % file_name)
            transfer_success = fun_test.scp(source_file_path=pc_3_config_dir + "/%s" % file_name,
                                            target_file_path=target_file_path, target_ip=cadence_pc_3,
                                            target_username=username, target_password=pc_3_password)
            fun_test.simple_assert(transfer_success, "Ensure file is transferred")

            # Configure cadence pc 3 for FCP traffic
            fun_test.log("Executing %s on cadence pc 3" % file_name)
            cmd = "sh /tmp/%s" % file_name
            pc_3_obj.command(command=cmd)

        fun_test.log("========= IP Routes on cadence-pc-3 =========")
        pc_3_obj.get_ip_route()

        # Copy req files to cadence pc 4
        pc_4_obj = Linux(host_ip=cadence_pc_4, ssh_username=username, ssh_password=pc_4_password)
        for file_name in ['nh_fcp.sh']:
            fun_test.log("Coping %s file to cadence pc 4 in /tmp dir" % file_name)
            transfer_success = fun_test.scp(source_file_path=pc_4_config_dir + "/%s" % file_name,
                                            target_file_path=target_file_path, target_ip=cadence_pc_4,
                                            target_username=username, target_password=pc_4_password)
            fun_test.simple_assert(transfer_success, "Ensure file is transferred")

            # Configure cadence pc 4 for FCP traffic
            fun_test.log("Executing %s cadence pc 4" % file_name)
            cmd = "sh /tmp/%s" % file_name
            pc_4_obj.command(command=cmd)
        fun_test.log("========= IP Routes on cadence-pc-4 =========")
        pc_4_obj.get_ip_route()

    def setup(self):
        global dut_config, network_controller_obj, spirent_config, TIMESTAMP

        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get(disable_f1_index=f1_index)
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')
            
        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        spirent_config = nu_config_obj.read_traffic_generator_config()
        dut_config = nu_config_obj.read_dut_config()
        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

        # fun_test.simple_assert(ensure_dpcsh_ready(network_controller_obj=network_controller_obj),
        #                        "Ensure DPCsh ready to process commands")

        checkpoint = "Configure QoS settings"
        enable_pfc = network_controller_obj.enable_qos_pfc()
        fun_test.simple_assert(enable_pfc, "Enable QoS PFC")
        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=7000,
                                                                            nonfcp_xoff_thr=7000,
                                                                            df_thr=4000,
                                                                            dx_thr=4000,
                                                                            fcp_thr=8000,
                                                                            nonfcp_thr=8000,
                                                                            sample_copy_thr=255,
                                                                            sf_thr=4000,
                                                                            sf_xoff_thr=3500,
                                                                            sx_thr=4000)
        fun_test.test_assert(buffer_pool_set, checkpoint)

        checkpoint = "Configure HNU QoS settings"
        enable_pfc = network_controller_obj.enable_qos_pfc(hnu=True)
        fun_test.simple_assert(enable_pfc, "Enable QoS PFC")
        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=900,
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
        fun_test.test_assert(buffer_pool_set, checkpoint)

        nu_port_list = [8,12]
        hnu_port_list = [0, 4]
        shape = 0
        for port in nu_port_list:
            result = network_controller_obj.set_port_mtu(port_num=port, shape=shape, mtu_value=9000)
            fun_test.simple_assert(result, "Set MTU to 9000 on all interfaces")

        for port in hnu_port_list:
            shape = 1
            result = network_controller_obj.set_port_mtu(port_num=port, shape=shape, mtu_value=9000)
            fun_test.simple_assert(result, "Set MTU to 9000 on all interfaces")

        # self._setup_fcp_external_routes()

        TIMESTAMP = get_current_time()

    def cleanup(self):
        pass


class TestTransitPerformance(FunTestCase):
    tc_id = 1
    template_obj = None
    flow_direction = FLOW_TYPE_NU_NU_NFCP
    tcc_file_name = "transit_single_flow_rfc.tcc"  # Uni-directional
    spray = False

    def _get_tcc_config_file_path(self, flow_direction):
        dir_name = None
        if flow_direction == FLOW_TYPE_NU_NU_NFCP:
            dir_name = "nu_nu_flow"
        elif flow_direction == FLOW_TYPE_HNU_HNU_NFCP:
            dir_name = "hnu_hnu_nfcp_flow"
        elif flow_direction == FLOW_TYPE_HNU_NU_NFCP:
            dir_name = "hnu_nu_flow"
        elif flow_direction == FLOW_TYPE_NU_HNU_NFCP:
            dir_name = "nu_hnu_flow"
        elif flow_direction == FLOW_TYPE_HNU_HNU_FCP:
            dir_name = "hnu_hnu_fcp_flow"

        config_type = "palladium_configs"
        dut_type = fun_test.shared_variables['dut_type']
        if dut_type == NuConfigManager.DUT_TYPE_F1:
            config_type = "f1_configs"

        tcc_config_path = fun_test.get_helper_dir_path() + '/%s/%s/%s' % (
            config_type, dir_name, self.tcc_file_name)
        fun_test.debug("Dir Name: %s" % dir_name)
        return tcc_config_path

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="%s RFC-2544 Spray: %s Frames: [64B, 800B, 1500B, 9000B, IMIX]" % (
                                  self.flow_direction, self.spray),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)

    def setup(self):
        dut_type = fun_test.shared_variables['dut_type']
        checkpoint = "Initialize RFC-2544 template"
        self.template_obj = Rfc2544Template(spirent_config=spirent_config)
        fun_test.test_assert(self.template_obj, checkpoint)

        tcc_config_path = self._get_tcc_config_file_path(flow_direction=self.flow_direction)

        checkpoint = "Load existing tcc configuration"
        result = self.template_obj.setup(tcc_config_path=tcc_config_path)
        fun_test.test_assert(result['result'], checkpoint)

        if dut_type == NuConfigManager.DUT_TYPE_F1:
            checkpoint = "Enable per-port latency compensation adjustments"
            result = self.template_obj.enable_per_port_latency_adjustments()
            fun_test.test_assert(result, checkpoint)

            checkpoint = "Set compensation mode to REMOVED for each port"
            result = self.template_obj.set_ports_compensation_mode()
            fun_test.test_assert(result, checkpoint)

    def run(self):
        fun_test.log("----------------> Start RFC-2544 test using %s <----------------" % self.tcc_file_name)

        fun_test.log("Fetching per VP stats before traffic")
        network_controller_obj.peek_per_vp_stats()

        fun_test.log("Fetching PSW NU Global stats before test")
        network_controller_obj.peek_psw_global_stats()

        if self.flow_direction != NuConfigManager.FLOW_DIRECTION_NU_NU:
            fun_test.log("Fetching PSW HNU Global stats before test")
            network_controller_obj.peek_psw_global_stats(hnu=True)

        fun_test.log("Fetching VP packets before test")
        network_controller_obj.peek_vp_packets()

        fun_test.log("Fetching BAM stats before test")
        network_controller_obj.peek_resource_bam_stats()

        checkpoint = "Start Sequencer"
        result = self.template_obj.start_sequencer()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Wait until test is finish"
        result = self.template_obj.wait_until_complete()
        fun_test.test_assert(result, checkpoint)

        fun_test.log("Fetching PSW NU Global stats after test")
        network_controller_obj.peek_psw_global_stats()

        if self.flow_direction != NuConfigManager.FLOW_DIRECTION_NU_NU:
            fun_test.log("Fetching PSW HNU Global stats after test")
            network_controller_obj.peek_psw_global_stats(hnu=True)

        fun_test.log("Fetching VP packets after test")
        network_controller_obj.peek_vp_packets()

        fun_test.log("Fetching BAM stats after test")
        network_controller_obj.peek_resource_bam_stats()

        fun_test.log("Fetching per VP stats after traffic")
        network_controller_obj.peek_per_vp_stats()

        checkpoint = "Fetch summary result for latency and throughput for all frames and all iterations"
        result_dict = self.template_obj.get_throughput_summary_results_by_frame_size()
        fun_test.test_assert(result_dict['status'], checkpoint)

        # TODO: We need to validate script later on once we know numbers for palladium and F1
        # checkpoint = "Validate results of current run"
        # result = self.template_obj.validate_result(result_dict=result_dict['summary_result'])
        # fun_test.test_assert(result, checkpoint)

        checkpoint = "Display Performance Table"
        table_name = "Performance Numbers for %s flow " % self.flow_direction
        if self.spray:
            table_name += " Spray Enable"
        result = self.template_obj.create_performance_table(result=result_dict['summary_result'],
                                                            table_name=table_name)
        fun_test.simple_assert(result, checkpoint)
        if self.spray or self.flow_direction == FLOW_TYPE_NU_NU_NFCP:
            mode = self.template_obj.get_interface_mode_input_speed()
            result = self.template_obj.populate_performance_json_file(result_dict=result_dict['summary_result'],
                                                                      timestamp=TIMESTAMP,
                                                                      mode=mode,
                                                                      flow_direction=self.flow_direction,
                                                                      model_name=HNU_PERFORMANCE_MODEL_NAME,
                                                                      update_charts=False,
                                                                      update_json=True)
            if not result:
                fun_test.log("===================== Trying another trial for failed flow with extra debug logs %s "
                             "=====================" % self.flow_direction)
                checkpoint = "Clear FPG stats"
                for port in [13, 15, 18, 1, 2]:
                    shape = 0
                    if port == 1 or port == 2:
                        shape = 1
                    network_controller_obj.clear_port_stats(port, shape)
                fun_test.add_checkpoint(checkpoint)

                checkpoint = "Start Sequencer"
                result = self.template_obj.start_sequencer()
                fun_test.test_assert(result, checkpoint)

                fun_test.sleep("Waiting for sequencer to run", seconds=60)

                checkpoint = "Stop Sequencer"
                result = self.template_obj.stc_manager.stop_sequencer()
                fun_test.test_assert(result, checkpoint)

                fun_test.log("============== Mac stats for FPG13 ==============")
                network_controller_obj.peek_fpg_port_stats(port_num=13)
                fun_test.log("============== Mac stats for FPG15 ==============")
                network_controller_obj.peek_fpg_port_stats(port_num=15)
                fun_test.log("============== Mac stats for FPG18 ==============")
                network_controller_obj.peek_fpg_port_stats(port_num=18)
                fun_test.log("============== Mac stats for HNU FPG1 ==============")
                network_controller_obj.peek_fpg_port_stats(port_num=1, hnu=True)
                fun_test.log("============== Mac stats for HNU FPG2 ==============")
                network_controller_obj.peek_fpg_port_stats(port_num=2, hnu=True)

                fun_test.log("Fetching PSW Global stats re-run test")
                network_controller_obj.peek_psw_global_stats()

                if self.flow_direction != NuConfigManager.FLOW_DIRECTION_NU_NU:
                    fun_test.log("Fetching PSW HNU Global stats re-run test")
                    network_controller_obj.peek_psw_global_stats(hnu=True)

                fun_test.simple_assert(False, '%s Flow Failed as all iterations in RFC2544 run failed. '
                                              'Added -1 in JSON output for this flow' % self.flow_direction)

        fun_test.log("----------------> End RFC-2544 test using %s  <----------------" % self.tcc_file_name)

    def cleanup(self):
        self.template_obj.cleanup()


class TestNuHnuPerformance(TestTransitPerformance):
    tc_id = 2
    flow_direction = FLOW_TYPE_NU_HNU_NFCP
    tcc_file_name = "nu_hnu_fs1600_2ports_100g.tcc"  # 2 Ports with Spray Enable
    spray = True


class TestHnuNuPerformance(TestTransitPerformance):
    tc_id = 3
    flow_direction = FLOW_TYPE_HNU_NU_NFCP
    tcc_file_name = "hnu_nu_fs1600_2ports_100g.tcc"  # 2 Ports with Spray Enable
    spray = True


class TestHnuHnuNonFcpPerformance(TestTransitPerformance):
    tc_id = 4
    flow_direction = FLOW_TYPE_HNU_HNU_NFCP
    tcc_file_name = "hnu_hnu_fs1600_2ports_nfcp.tcc"  # Bi-directional with Spray Enable
    spray = True


class TestNuHnuPerformanceSingleFlow(TestTransitPerformance):
    tc_id = 5
    flow_direction = FLOW_TYPE_NU_HNU_NFCP
    tcc_file_name = "nu_hnu_fs1600_single.tcc"  # Single Port with Spray Disable
    spray = False


class TestHnuNuPerformanceSingleFlow(TestTransitPerformance):
    tc_id = 6
    flow_direction = FLOW_TYPE_HNU_NU_NFCP
    tcc_file_name = "hnu_nu_fs1600_single.tcc"  # Single Port with Spray Disable
    spray = False


class TestHnuHnuNonFcpPerformanceSingleFlow(TestTransitPerformance):
    tc_id = 7
    flow_direction = FLOW_TYPE_HNU_HNU_NFCP
    tcc_file_name = "hnu_hnu_fs1600_single_nfcp.tcc"  # Single Port with Spray Disable
    spray = False


class TestHnuHnuFcpPerformance(TestTransitPerformance):
    tc_id = 8
    flow_direction = FLOW_TYPE_HNU_HNU_FCP
    tcc_file_name = "hnu_hnu_fcp_spray.tcc"
    spray = True


class TestHnuHnuFcpPerformanceSingleFlow(TestTransitPerformance):
    tc_id = 9
    flow_direction = FLOW_TYPE_HNU_HNU_FCP
    tcc_file_name = "hnu_hnu_fcp_single_flow.tcc"
    spray = False


if __name__ == '__main__':
    ts = ScriptSetup()

    # Multi flows
    #ts.add_test_case(TestTransitPerformance())
    ts.add_test_case(TestNuHnuPerformance())
    ts.add_test_case(TestHnuNuPerformance())
    #ts.add_test_case(TestHnuHnuNonFcpPerformance())

    # Single flow
    #ts.add_test_case(TestNuHnuPerformanceSingleFlow())
    #ts.add_test_case(TestHnuNuPerformanceSingleFlow())
    #ts.add_test_case(TestHnuHnuNonFcpPerformanceSingleFlow())

    # FCP cases
    # ts.add_test_case(TestHnuHnuFcpPerformance())
    # ts.add_test_case(TestHnuHnuFcpPerformanceSingleFlow())
    ts.run()
