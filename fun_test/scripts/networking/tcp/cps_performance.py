"""
Inputs to the script as follows

--inputs
{\"speed\":\"SPEED_100G\",\"disable_f1_index\":0,\"base_cps\":50,\"duration\":60,\"incremental_count\":100}

speed = SPEED_100G (Interface speed)
disable_f1_index = 0 ( Boot only F1_1 of FS-7)
base_cps = 50 (Initial value of CPS to start the test)
duration = 60 (Test Duration)
incremental_count = 100 (Counter value at which cps value will be incremental starting from base_cps)
end_cps = 500 (Max CPS value)  <-- This parameter is optional and can be use for debug purpose.
                                   If not given test will find the max value.
publish_result = False/True  -<- Optional By default True
"""
from lib.system.fun_test import *
from lib.host.linux import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.fun.fs import *
from lib.host.trex_manager import TrexManager, TREX_CONFIG_FILE
import copy
from lib.topology.topology_helper import TopologyHelper

network_controller_obj = None
nu_lab_handle = None
app = "tcp_server"
host_name = "nu-lab-04"
hosts_json_file = ASSET_DIR + "/hosts.json"
setup_fpg0_file = "fpg0.sh"
setup_fpg0_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg0_file
TIMESTAMP = None
filename = "tcp_cps_performance.json"
use_mpstat = False


class TcpPerformance(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup fpg on nu-lab-04
        2. set syslog 2
        3. Execute tcp_server in dpcsh""")

    def setup(self):
        global nu_lab_obj, network_controller_obj, nu_lab_ip, nu_lab_username, nu_lab_password, nu_lab_obj2, mode, \
            TIMESTAMP

        TIMESTAMP = get_current_time()
        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        inputs = fun_test.get_job_inputs()
        fun_test.shared_variables['inputs'] = inputs
        #if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
        #    fs = Fs.get(disable_f1_index=f1_index)
        #    fun_test.shared_variables['fs'] = fs
        #    fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')
        f1_1_boot_args = "app=hw_hsu_test cc_huid=2 --dpc-server --dpc-uart --csr-replay --all_100g"

        topology_t_bed_type = fun_test.get_job_environment_variable('test_bed_type')

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={1: {"boot_args": f1_1_boot_args}}, disable_f1_index=0)

        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        private_funos_branch = fun_test.get_build_parameter(parameter='BRANCH_FunOS')
        if private_funos_branch:
            fun_test.shared_variables['funos_branch'] = private_funos_branch

        speed = nu_config_obj.get_speed()
        mode = str(speed / 1000) + "G"
        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        dut_config = nu_config_obj.read_dut_config()

        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=16383,
                                                                            nonfcp_xoff_thr=16383,
                                                                            df_thr=16383,
                                                                            dx_thr=16383,
                                                                            fcp_thr=12287,
                                                                            nonfcp_thr=256,
                                                                            sample_copy_thr=255,
                                                                            sf_thr=16383,
                                                                            sf_xoff_thr=4095,
                                                                            sx_thr=16383)
        fun_test.test_assert(buffer_pool_set, "Configure psw buffer")

        syslog = network_controller_obj.set_syslog_level(level=2)
        fun_test.simple_assert(syslog, "Set syslog level to 2")

        exec_app = network_controller_obj.execute_app(name=app)
        fun_test.test_assert(expression=exec_app['status'], message="Ensure TCP server App started")

        # Setup fpg1
        host_info = get_nu_lab_host(file_path=hosts_json_file, host_name=host_name)
        fun_test.simple_assert(host_info, 'Host info fetched')
        nu_lab_username = host_info['ssh_username']
        nu_lab_ip = host_info['host_ip']
        nu_lab_password = host_info['ssh_password']
        nu_lab_obj = Linux(host_ip=nu_lab_ip, ssh_username=nu_lab_username,
                           ssh_password=nu_lab_password)

        nu_lab_obj2 = copy.deepcopy(nu_lab_obj)

        trex_manager = TrexManager(host_ip=nu_lab_ip, ssh_username=nu_lab_username, ssh_password=nu_lab_password)
        fun_test.shared_variables['trex_manager'] = trex_manager

    def cleanup(self):
        #if 'fs' in fun_test.shared_variables:
        #    fs = fun_test.shared_variables['fs']
        #    fs.cleanup()
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()


class TestCloseResetCps(FunTestCase):
    default_frame_size = 1500
    test_run_time = 60
    astf_profile = 'astf/close_reset_cps.py'

    def describe(self):
        self.set_test_details(id=1,
                              summary="Get Max CPS TCP with profile astf/close_reset_cps and measure latency",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run TRex command to measure max cps and latency in a loop starting from max 
                              3. Update tcp_cps_performance.json with the max cps and latency numbers for cps type 
                              close_reset_cps
                              """ % host_name)

    def setup(self):
        trex_manager = fun_test.shared_variables['trex_manager']

        port_info = [{'dest_mac': '00:de:ad:be:ef:00', 'src_mac': 'fe:dc:ba:44:66:30'},
                     {'dest_mac': '98:03:9b:7f:c7:1c', 'src_mac': '98:03:9b:7f:b8:8c'}]

        checkpoint = "Ensure %s config file is correct" % TREX_CONFIG_FILE
        trex_manager.ensure_trex_config_correct(port_info=port_info)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        # TODO: If config file is not present or macs are wrong edit the file

        checkpoint = "Copy setup file %s to %s" % (setup_fpg0_file, host_name)
        target_file_path = "/tmp/" + setup_fpg0_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg0_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, checkpoint)

        fun_test.sleep("Letting file be copied", seconds=1)

        # Execute setup file on host2
        checkpoint = "Execute setup file %s on %s" % (target_file_path, host_name)
        output = execute_shell_file(linux_obj=nu_lab_obj, target_file=target_file_path, sudo=True)
        fun_test.simple_assert(output['result'], checkpoint)

        fun_test.log("Display applied routes")
        nu_lab_obj.get_ip_route()

    def run(self):
        trex_manager = fun_test.shared_variables['trex_manager']
        inputs = fun_test.shared_variables['inputs']
        base_cps = inputs['base_cps']
        test_duration = inputs['duration']
        increment_count = inputs['increment_count']
        publish_result = True
        if 'publish_result' in inputs:
            publish_result = inputs['publish_result']

        end_cps = None
        if 'end_cps' in inputs:
            end_cps = inputs['end_cps']

        profile_name = self.astf_profile.split('/')[1].split('.')[0]
        version = fun_test.get_version()

        branch_name = None
        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        checkpoint = "Capture netstat before traffic"
        netstat_1 = get_netstat_output(linux_obj=nu_lab_obj)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Find max cps for profile %s" % self.astf_profile
        result = find_max_cps_using_trex(network_controller_obj=network_controller_obj, trex_obj=trex_manager,
                                         astf_profile=self.astf_profile, base_cps=base_cps,
                                         cpu=1, duration=test_duration, end_cps=end_cps,
                                         increment_count=increment_count)
        fun_test.test_assert(result['status'], checkpoint)

        checkpoint = "Capture netstat after traffic"
        netstat_2 = get_netstat_output(linux_obj=nu_lab_obj)
        fun_test.add_checkpoint(checkpoint)

        # Get diff stats
        netstat_temp_filename = str(version) + "_" + profile_name + '_netstat.txt'
        diff_netstat = get_diff_stats(old_stats=netstat_1, new_stats=netstat_2)
        populate = populate_netstat_output_file(diff_stats=diff_netstat, filename=netstat_temp_filename)
        fun_test.test_assert(populate, "Populate netstat into txt file")

        # Parse output to get json
        if not branch_name:
            if publish_result:
                output = populate_cps_performance_json_file(mode=mode, flow_type="FunTCP_Server_CPS",
                                                            frame_size=self.default_frame_size,
                                                            cps_type=profile_name,
                                                            max_cps=result['max_cps'],
                                                            max_latency=result['max_latency'],
                                                            avg_latency=result['avg_latency'],
                                                            timestamp=TIMESTAMP,
                                                            filename=filename,
                                                            model_name=TCP_CPS_PERFORMANCE_MODEL_NAME)
                fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        if 'tcpdump_pid' in fun_test.shared_variables:
            nu_lab_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid']), sudo=True)


class TestCloseFinCps(TestCloseResetCps):
    astf_profile = "astf/close_fin_cps.py"

    def describe(self):
        self.set_test_details(id=2,
                              summary="Get Max CPS TCP with profile astf/close_fin_cps and measure latency",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run TRex command to measure max cps and latency in a loop starting from max 
                              3. Update tcp_cps_performance.json with the max cps and latency numbers for cps type 
                              close_reset_cps
                              """ % host_name)


if __name__ == '__main__':
    ts = TcpPerformance()
    ts.add_test_case(TestCloseResetCps())
    ts.add_test_case(TestCloseFinCps())
    ts.run()
