from lib.system.fun_test import *
from lib.host.linux import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.fun.fs import *
from lib.host.trex_manager import TrexManager, TREX_CONFIG_FILE
import copy

network_controller_obj = None
nu_lab_handle = None
app = "tcp_server"
host_name = "nu-lab-04"
hosts_json_file = ASSET_DIR + "/hosts.json"
setup_fpg1_file = "setup_trex_fpg.sh"
setup_fpg1_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg1_file
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
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get(disable_f1_index=f1_index)
            fun_test.shared_variables['fs'] = fs
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

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
        if 'fs' in fun_test.shared_variables:
            fs = fun_test.shared_variables['fs']
            fs.cleanup()


class TestCloseResetCps(FunTestCase):
    default_frame_size = 1500
    test_run_time = 60
    duration = 60
    astf_profile = 'astf/close_reset_cps.py'

    def describe(self):
        self.set_test_details(id=1,
                              summary="Get Max CPS TCP with profile astf/close_reset_cps.py and measure latency",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run TRex command to measure max cps and latency in a loop starting from max 
                              3. Update tcp_cps_performance.json with the max cps and latency numbers for cps type 
                              close_reset_cps
                              """ % host_name)

    def setup(self):
        trex_manager = fun_test.shared_variables['trex_manager']

        port_info = [{'dest_mac': '00:de:ad:be:ef:00', 'src_mac': 'fe:dc:ba:44:55:99'},
                     {'dest_mac': 'fe:dc:ba:44:55:99', 'src_mac': '00:de:ad:be:ef:00'}]

        checkpoint = "Ensure %s config file is correct" % TREX_CONFIG_FILE
        trex_manager.ensure_trex_config_correct(port_info=port_info)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        # TODO: If config file is not present or macs are wrong edit the file

        fun_test.log("Display applied routes")
        nu_lab_obj.get_ip_route()

    def run(self):
        trex_manager = fun_test.shared_variables['trex_manager']
        inputs = fun_test.shared_variables['inputs']
        base_cps = inputs['base_cps']
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
                                         cpu=1, duration=60)
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
            output = populate_cps_performance_json_file(mode=mode, flow_type="FunTCP_Server_CPS",
                                                        frame_size=self.default_frame_size,
                                                        cps_type=profile_name,
                                                        max_cps=result['max_cps'],
                                                        max_latency=result['max_latency'],
                                                        avg_latency=result['avg_latency'],
                                                        timestamp=TIMESTAMP,
                                                        filename=filename, model_name=TCP_PERFORMANCE_MODEL_NAME)
            fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = TcpPerformance()
    ts.add_test_case(TestCloseResetCps())
    ts.run()
