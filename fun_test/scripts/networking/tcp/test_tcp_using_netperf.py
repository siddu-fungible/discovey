from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import copy
import re

network_controller_obj = None
nu_lab_handle = None
app = "tcp_server"
host_name = "poc-server-06"
hosts_json_file = ASSET_DIR + "/hosts.json"
setup_fpg1_file = "setup_fpg1.sh"
setup_fpg1_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg1_file
TIMESTAMP = None
filename = "tcp_performance.json"
use_mpstat = True


def get_port_from_file(filepath):
    port_value = None
    try:
        read_op = fun_test.read_file(file_name=filepath)
        if read_op:
            read_op = read_op.split("\n")
            first_line = read_op[0]
            out = re.search(',[0-9]*', first_line)
            if out.group():
                port_value = int(out.group()[1:])
    except Exception as ex:
        fun_test.critical(str(ex))
    return port_value


class TcpPerformance(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup fpg on nu-lab-04
        2. set syslog 2
        3. Execute tcp_server in dpcsh""")

    def setup(self):
        global nu_lab_obj, network_controller_obj, nu_lab_ip, nu_lab_username, nu_lab_password, nu_lab_obj2, \
            mpstat_obj, mpstat_obj2, mode, TIMESTAMP

        TIMESTAMP = get_current_time()
        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        if not f1_index:
            f1_index = 0
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get(disable_f1_index=f1_index)
            fun_test.shared_variables['fs'] = fs
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        private_funos_branch = fun_test.get_build_parameter(parameter='BRANCH_FunOS')
        if private_funos_branch:
            fun_test.shared_variables['funos_branch'] = private_funos_branch

        job_inputs = fun_test.get_job_inputs()
        fun_test.shared_variables['inputs'] = job_inputs

        speed = nu_config_obj.get_speed()
        if speed:
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
        mpstat_obj = copy.deepcopy(nu_lab_obj)
        mpstat_obj2 = copy.deepcopy(nu_lab_obj)

    def cleanup(self):
        if 'fs' in fun_test.shared_variables:
            fs = fun_test.shared_variables['fs']
            fs.cleanup()


class TestTcpPerformance(FunTestCase):
    default_frame_size = 1500
    test_run_time = 10
    num_flows = 1
    output_file = None
    netperf_remote_port = 4555

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Tcp performance",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 1 or multi connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name)

    def setup(self):
        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=nu_lab_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)

        target_file_path = "/tmp/" + setup_fpg1_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg1_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))

        fun_test.sleep("Letting file be copied", seconds=1)

        # Execute sh file
        fun_test.log("Creating interface and applying routes")
        output = execute_shell_file(linux_obj=nu_lab_obj, target_file=target_file_path)
        fun_test.simple_assert(output['result'], "Ensure file %s is executed" % target_file_path)

        fun_test.log_section("Display applied routes")
        nu_lab_obj.get_ip_route()

    def run(self):
        inputs = fun_test.shared_variables['inputs']
        num_flows = 1
        publish_results = False
        branch_name = 'master'
        if inputs:
            if 'num_of_connections' in inputs:
                num_flows = inputs['num_of_connections']

            if 'publish_results' in inputs:
                publish_results = inputs['publish_results']

        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        fun_test.log_section("Test Parameters")
        fun_test.log("# of connections: %d" % num_flows)
        fun_test.log("Publish results to performance site: %s" % publish_results)
        fun_test.log("FunOS Branch: %s" % branch_name)
        fun_test.log("FunOS version: %s" % fun_test.get_version())

        test_parameters = {'dest_ip': '29.1.1.2', 'protocol': 'tcp', 'num_flows': num_flows, 'duration': 60,
                           'port1': 1000, 'port2': 4555, 'send_size': '128K'}

        checkpoint = "Capture netstat before traffic"
        netstat_1 = get_netstat_output(linux_obj=nu_lab_obj)
        fun_test.add_checkpoint(checkpoint)

        # Start mpstat
        version = fun_test.get_version()
        mpstat_temp_filename = str(version) + "_" + str(self.num_flows) + '_mpstat.txt'
        mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)
        if use_mpstat:
            fun_test.log("Starting to run mpstat command")
            mp_out = run_mpstat_command(linux_obj=mpstat_obj, interval=self.test_run_time,
                                        output_file=mpstat_output_file, bg=True, count=6)
            fun_test.log('mpstat cmd process id: %s' % mp_out)
            fun_test.add_checkpoint("Started mpstat command")

        checkpoint = "Peek stats resource pc 1 before"
        resource_pc_temp_filename = str(version) + "_" + str(self.num_flows) + '_resource_pc.txt'
        fun_test.simple_assert(populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                                                filename=resource_pc_temp_filename,
                                                                pc_id=1, count=1), checkpoint)
        checkpoint = "Peek stats resource pc 2 before"
        fun_test.simple_assert(populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                                                filename=resource_pc_temp_filename,
                                                                pc_id=2, count=1), checkpoint)

        fun_test.log_section("Starting netperf test")
        cmd_list = get_netperf_cmd_list(dip=test_parameters['dest_ip'],
                                        duration=test_parameters['duration'],
                                        num_flows=test_parameters['num_flows'],
                                        send_size=test_parameters['send_size'])
        fun_test.simple_assert(cmd_list, 'Ensure netperf command formed')

        netperf_result = run_netperf_concurrently(cmd_list=cmd_list, linux_obj=nu_lab_obj)
        fun_test.test_assert(netperf_result, 'Ensure result found')

        checkpoint = "Get Flow list during test"
        output = network_controller_obj.get_flow_list()
        flowlist_temp_filename = str(version) + "_" + str(self.num_flows) + '_flowlist.txt'
        fun_test.test_assert(populate_flow_list_output_file(result=output['data'], filename=flowlist_temp_filename),
                             checkpoint)

        checkpoint = "Peek stats resource pc 1 after"
        resource_pc_temp_filename = str(version) + "_" + str(self.num_flows) + '_resource_pc.txt'
        fun_test.test_assert(populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                                              filename=resource_pc_temp_filename,
                                                              pc_id=1, count=1), checkpoint)
        checkpoint = "Peek stats resource pc 2 after"
        fun_test.test_assert(populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                                              filename=resource_pc_temp_filename,
                                                              pc_id=2, count=1), checkpoint)

        total_throughput = netperf_result['total_throughput']
        fun_test.log("Total throughput seen is %s" % total_throughput)
        fun_test.test_assert(total_throughput > 0.0, "Ensure some throughput is seen. Actual %s" % total_throughput)

        pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
        fun_test.log("Total PPS value is %s" % round(pps, 2))

        create_performance_table(total_throughput=total_throughput, total_pps=round(pps, 2), num_flows=num_flows)

        # Scp mpstat json to LOGS dir
        if use_mpstat:
            populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=mpstat_obj,
                                        dump_filename=mpstat_temp_filename)

        fun_test.sleep("Letting file to be scp", seconds=2)

        fun_test.log("Capture netstat after traffic")
        netstat_2 = get_netstat_output(linux_obj=nu_lab_obj)

        # Get diff stats
        netstat_temp_filename = str(version) + "_" + str(self.num_flows) + '_netstat.txt'
        diff_netstat = get_diff_stats(old_stats=netstat_1, new_stats=netstat_2)
        populate = populate_netstat_output_file(diff_stats=diff_netstat, filename=netstat_temp_filename)
        fun_test.test_assert(populate, "Populate netstat into txt file")

        # Parse output to get json
        if not branch_name:
            if publish_results:
                output = populate_performance_json_file(mode=mode, flow_type="FunTCP_Server_Throughput",
                                                        frame_size=self.default_frame_size,
                                                        num_flows=self.num_flows,
                                                        throughput_n2t=total_throughput, pps_n2t=pps,
                                                        timestamp=TIMESTAMP,
                                                        filename=filename, model_name=TCP_PERFORMANCE_MODEL_NAME)
                fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        if self.output_file:
            nu_lab_obj.remove_file(self.output_file)

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=nu_lab_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)


if __name__ == '__main__':
    ts = TcpPerformance()
    ts.add_test_case(TestTcpPerformance())
    ts.run()