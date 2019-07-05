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

        diff_netstat = None
        netstat_1 = None

        # Start mpstat
        version = fun_test.get_version()
        mpstat_temp_filename = str(version) + "_" + str(num_flows) + '_mpstat.txt'
        mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)
        tcpdump_temp_filename = str(version) + "_" + str(num_flows) + '_tcpdump.pcap'
        tcpdump_output_file = fun_test.get_temp_file_path(file_name=tcpdump_temp_filename)

        fun_test.log_section("Starting netperf test")
        cmd_list = get_netperf_cmd_list(dip=test_parameters['dest_ip'],
                                        duration=test_parameters['duration'],
                                        num_flows=test_parameters['num_flows'],
                                        send_size=test_parameters['send_size'])
        fun_test.simple_assert(cmd_list, 'Ensure netperf command formed')

        network_controller_obj.disconnect()
        cmd_dict = {nu_lab_obj: cmd_list}
        throughput_list = []
        for iteration in range(0, 5):
            fun_test.add_checkpoint("<=====> Start iteration: %d  <=====>" % iteration)
            fun_test.log_section("Start iteration: %d" % iteration)
            collect_dpc_stats = False if iteration > 0 else True
            if iteration == 0:
                fun_test.add_checkpoint("Capture netstat before traffic for iteration %d" % iteration)
                netstat_1 = get_netstat_output(linux_obj=nu_lab_obj)

                # Start mpstat
                if use_mpstat:
                    fun_test.log("Starting to run mpstat command")
                    mp_out = run_mpstat_command(linux_obj=mpstat_obj, interval=self.test_run_time,
                                                output_file=mpstat_output_file, bg=True, count=6)
                    fun_test.log('mpstat cmd process id: %s' % mp_out)
                    fun_test.add_checkpoint("Started mpstat command")

                checkpoint = "Start tcpdump capture in background before starting traffic"
                interface_name = get_interface_name(file_path=setup_fpg1_filepath)
                result = run_tcpdump_command(linux_obj=nu_lab_obj, interface=interface_name,
                                             tcp_dump_file=tcpdump_output_file,
                                             count=100000, filecount=1)
                fun_test.simple_assert(result, checkpoint)
                fun_test.shared_variables['tcpdump_pid'] = result

            netperf_result = run_netperf_concurrently(cmd_dict=cmd_dict,
                                                      network_controller_obj=network_controller_obj,
                                                      display_output=False,
                                                      num_flows=num_flows, collect_dpc_stats=collect_dpc_stats)
            fun_test.simple_assert(netperf_result, 'Ensure result found')

            fun_test.sleep("Wait after traffic", seconds=self.test_run_time)

            if 'tcpdump_pid' in fun_test.shared_variables and iteration == 0:
                nu_lab_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid']), sudo=True)

            if iteration == 0:
                fun_test.add_checkpoint("Capture netstat after traffic for iteration %d" % iteration)
                netstat_2 = get_netstat_output(linux_obj=nu_lab_obj)
                diff_netstat = get_diff_stats(old_stats=netstat_1, new_stats=netstat_2)

            total_throughput = netperf_result['total_throughput']
            fun_test.add_checkpoint("ITERATION: %d Total throughput seen is %s" % (iteration, total_throughput))
            # TODO: We don't need to fail the case if total_throughput <= 0 instead put -1 in JSON and
            # TODO: Model so that it gets reflected on dashboard
            # fun_test.test_assert(total_throughput > 0.0, "Ensure some throughput is seen. Actual %s" %
            # total_throughput)

            throughput_list.append(total_throughput)

            pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
            fun_test.add_checkpoint("ITERATION: %d Total PPS value is %s" % (iteration, round(pps, 2)))

            fun_test.add_checkpoint("<=====> End iteration: %d  <=====>" % iteration)

        avg_throughput = sum(throughput_list) / len(throughput_list)
        avg_pps = get_pps_from_mbps(mbps=avg_throughput, byte_frame_size=self.default_frame_size)
        if avg_throughput <= 0.0 and avg_pps <= 0.0:
            avg_throughput = -1
            avg_pps = -1

        create_performance_table(total_throughput=avg_throughput, total_pps=round(avg_pps, 2),
                                 num_flows=num_flows)

        # Scp mpstat json to LOGS dir
        if use_mpstat:
            populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=mpstat_obj,
                                        dump_filename=mpstat_temp_filename)

        fun_test.sleep("Letting file to be scp", seconds=2)

        populate_tcpdump_redirect_file(dump_filename=tcpdump_temp_filename, version=version, num_flows=num_flows,
                                       host_name=host_name, host_obj=nu_lab_obj, source_file_path=tcpdump_output_file)

        # Get diff stats
        netstat_temp_filename = str(version) + "_" + str(num_flows) + '_netstat.txt'
        populate = populate_netstat_output_file(diff_stats=diff_netstat, filename=netstat_temp_filename)
        fun_test.test_assert(populate, "Populate netstat into txt file")

        # Parse output to get json
        if not branch_name:
            if publish_results:
                output = populate_performance_json_file(mode=mode, flow_type="FunTCP_Server_Throughput",
                                                        frame_size=self.default_frame_size,
                                                        num_flows=num_flows,
                                                        throughput_n2t=avg_throughput, pps_n2t=avg_pps,
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
