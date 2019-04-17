from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import copy


network_controller_obj = None
nu_lab_handle = None
app = "tcp_server"
nu_lab_json = "nu_lab_info.json"
nu_lab_info_file = SCRIPTS_DIR + "/networking/tcp/configs/" + nu_lab_json
setup_fpg1_file = "setup_fpg1.sh"
setup_fpg1_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg1_file
TIMESTAMP = None
filename = "tcp_performance.json"


class TcpPerformance(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup fpg on nu-lab-04
        2. set syslog 2
        3. Execute tcp_server in dpcsh""")

    def setup(self):
        global nu_lab_obj, network_controller_obj, nu_lab_ip, nu_lab_username, nu_lab_password, nu_lab_obj2

        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get()
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        nu_config_obj = NuConfigManager()
        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        dut_config = nu_config_obj.read_dut_config()
        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

        syslog = network_controller_obj.set_syslog_level(level=2)
        fun_test.simple_assert(syslog, "Set syslog level to 2")

        exec_app = network_controller_obj.execute_app(name=app)
        #fun_test.simple_assert(exec_app, "Execute %s on dpcsh" % app)

        # Setup fpg1
        file_json = fun_test.parse_file_to_json(nu_lab_info_file)
        nu_lab_username = file_json['username']
        nu_lab_ip = file_json['ip']
        nu_lab_password = file_json['password']
        nu_lab_obj = Linux(host_ip=nu_lab_ip, ssh_username=nu_lab_username,
                           ssh_password=nu_lab_password)

        nu_lab_obj2 = copy.deepcopy(nu_lab_obj)

    def cleanup(self):
        pass


class TcpPerformance_1_Conn(FunTestCase):
    default_frame_size = 1500
    perf_filename = "perf_1_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    test_run_time = 30
    num_flows = 1
    output_file = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Tcp performance for 1 connection for 1500B stream",
                              steps="""
                              1. Setup fpg1 on nu-lab-04
                              2. Run netperf file with 1 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """)

    def setup(self):
        target_file_path = "/tmp/" + setup_fpg1_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg1_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))

        # Execute sh file
        fun_test.log("Creating interface and applying routes")
        output = execute_shell_file(linux_obj=nu_lab_obj, target_file=target_file_path)
        fun_test.simple_assert(output['output'], "Ensure file %s is executed" % target_file_path)

        fun_test.log("Display applied routes")
        nu_lab_obj.get_ip_route()

    def run(self):

        TIMESTAMP = get_current_time()

        fun_test.log("SCP file %s to %s" % (self.perf_filename, nu_lab_obj.host_ip))

        target_file_path = "/tmp/" + self.perf_filename
        file_transfer = fun_test.scp(source_file_path=self.perf_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))
        
        # Execute sh file
        temp_filename = fun_test.get_temp_file_name() + '.txt'
        output_file = fun_test.get_temp_file_path(file_name=temp_filename)
        
        fun_test.log("Starting netperf test")
        output = execute_shell_file(linux_obj=nu_lab_obj2, target_file=target_file_path, output_file=output_file)
        fun_test.simple_assert(output['output'], "Ensure file %s is executed" % target_file_path)

        fun_test.sleep("Letting traffic be run", seconds=self.test_run_time + 10)

        netperf_output = nu_lab_obj.command("cat %s" % output_file)

        total_throughput = get_total_throughput(output=netperf_output)
        fun_test.log("Total throughput seen is %s" % total_throughput)

        pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
        fun_test.log("PPS value is %s" % pps)

        # Parse output to get json
        output = populate_performance_json_file(flow_type="TCP_Server", frame_size=self.default_frame_size,
                                                num_flows=self.num_flows,
                                                throughput_n2t=total_throughput, pps_n2t=pps, timestamp=TIMESTAMP,
                                                filename=filename)
        fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        if self.output_file:
            nu_lab_obj.remove_file(self.output_file)


class TcpPerformance_4_Conn(TcpPerformance_1_Conn):
    num_flows = 4
    perf_filename = "perf_4_tcp_connection.sh"

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test Tcp performance for 4 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on nu-lab-04
                              2. Run netperf file with 4 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """)


if __name__ == '__main__':
    ts = TcpPerformance()

    ts.add_test_case(TcpPerformance_1_Conn())
    ts.add_test_case(TcpPerformance_4_Conn())
    ts.run()