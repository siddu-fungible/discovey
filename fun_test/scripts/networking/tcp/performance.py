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
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get(disable_f1_index=f1_index)
            fun_test.shared_variables['fs'] = fs
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        speed = nu_config_obj.get_speed()
        mode = str(speed/1000) + "G"
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


class TcpPerformance1Conn(FunTestCase):
    default_frame_size = 1500
    perf_filename = "perf_1_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    test_run_time = 10
    num_flows = 1
    output_file = None
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Tcp performance for 1 connection for 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 1 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name)

    def setup(self):
        self.netperf_remote_port = get_port_from_file(self.perf_filepath)
        fun_test.simple_assert(self.netperf_remote_port, "Value of server port is %s" % self.netperf_remote_port)

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

        fun_test.log("Display applied routes")
        nu_lab_obj.get_ip_route()

    def run(self):
        fun_test.log("SCP file %s to %s" % (self.perf_filename, nu_lab_obj.host_ip))

        target_file_path = "/tmp/" + self.perf_filename
        file_transfer = fun_test.scp(source_file_path=self.perf_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))

        fun_test.sleep("Letting file be copied", seconds=1)

        fun_test.log("Capture netstat before traffic")
        netstat_1 = get_netstat_output(linux_obj=nu_lab_obj)

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
        
        # Execute sh file
        temp_filename = fun_test.get_temp_file_name() + '.txt'
        output_file = fun_test.get_temp_file_path(file_name=temp_filename)
        
        fun_test.log("Starting netperf test")
        output = execute_shell_file(linux_obj=nu_lab_obj2, target_file=target_file_path, output_file=output_file)
        fun_test.simple_assert(output['result'], "Ensure file %s is executed" % target_file_path)

        checkpoint = "Get Flow list during test"
        output = network_controller_obj.get_flow_list()
        flowlist_temp_filename = str(version) + "_" + str(self.num_flows) + '_flowlist.txt'
        fun_test.simple_assert(populate_flow_list_output_file(result=output['data'], filename=flowlist_temp_filename),
                               checkpoint)

        checkpoint = "Peek stats resource pc 1"
        resource_pc_temp_filename = str(version) + "_" + str(self.num_flows) + '_resource_pc.txt'
        fun_test.simple_assert(populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                                                filename=resource_pc_temp_filename,
                                                                pc_id=1), checkpoint)
        fun_test.simple_assert(populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                                                filename=resource_pc_temp_filename,
                                                                pc_id=2), checkpoint)
        fun_test.sleep("Letting traffic be run", seconds=60)

        netperf_output = nu_lab_obj.command("cat %s" % output_file)
        fun_test.test_assert(netperf_output, "Ensure throughput value is seen")

        output = get_total_throughput(output=netperf_output, num_conns=self.num_flows)
        total_throughput = output['throughput']
        fun_test.log("Total throughput seen is %s" % total_throughput)
        fun_test.test_assert(total_throughput > 0.0, "Ensure some throughput is seen. Actual %s" % total_throughput)

        pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
        fun_test.log("PPS value is %s" % pps)

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
        output = populate_performance_json_file(mode=mode, flow_type="FunTCP_Server_Throughput",
                                                frame_size=self.default_frame_size,
                                                num_flows=self.num_flows,
                                                throughput_n2t=total_throughput, pps_n2t=pps, timestamp=TIMESTAMP,
                                                filename=filename, model_name=TCP_PERFORMANCE_MODEL_NAME)
        fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        if self.output_file:
            nu_lab_obj.remove_file(self.output_file)

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=nu_lab_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)


class TcpPerformance2Conn(TcpPerformance1Conn):
    num_flows = 2
    perf_filename = "perf_2_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test Tcp performance for 2 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 2 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name)


class TcpPerformance4Conn(TcpPerformance1Conn):
    num_flows = 4
    perf_filename = "perf_4_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Tcp performance for 4 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 4 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name)


class TcpPerformance8Conn(TcpPerformance1Conn):
    num_flows = 8
    perf_filename = "perf_8_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test Tcp performance for 8 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 8 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name)


if __name__ == '__main__':
    ts = TcpPerformance()

    ts.add_test_case(TcpPerformance1Conn())
    # ts.add_test_case(TcpPerformance_2_Conn())
    ts.add_test_case(TcpPerformance4Conn())
    ts.add_test_case(TcpPerformance8Conn())
    ts.run()