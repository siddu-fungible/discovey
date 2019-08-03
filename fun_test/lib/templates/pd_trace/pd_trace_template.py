from lib.system.fun_test import fun_test
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER_IP, TFTP_DIRECTORY, TFTP_SERVER_SSH_PASSWORD, TFTP_SERVER_SSH_USERNAME
# Connect to tracing server
# Setup networking
# Setup job directory
# move uart log
# move funos-binary


BASE_JOB_DIRECTORY = "/tmp/trace_jobs"
TOOLS_DIRECTORY = "/home/localadmin"
PERF_LISTENER = "perf_listener.py"
PERF_LISTENER_PATH = TOOLS_DIRECTORY + "/" + PERF_LISTENER
FUNOS_F1_NAME = "funos-f1"
MAX_TRACE_JOB_DIRECTORIES = 5
EXPECTED_TOOLS = ["process_perf.sh", "view_perf.sh"]


class CsiPerfOperation:
    PREPARE = "reinit"
    START = "start"
    STOP = "stop"
    OFFLOAD = "offload"


class PdTraceTemplate():
    def __init__(self, perf_collector_host_name, listener_ip, fs):
        self.perf_collector_host_name = perf_collector_host_name
        self.perf_host = None
        self.perf_listener_process_id = None
        self.job_directory = None
        self.listener_ip = listener_ip
        self.fs = fs
        self.instance = 0
        self.tools_directory = TOOLS_DIRECTORY

    def ensure_space_exists(self, num_allowed_trace_job_directories=MAX_TRACE_JOB_DIRECTORIES):
        """
        We need to ensure the server has enough space.
        For now we ensure only num_allowed_trace_directories can exist
        :return True if number of current trace directories is < num_allowed_trace_job_directories
        """
        pass
        self.perf_host = self.get_perf_host()
        files = self.perf_host.list_files(BASE_JOB_DIRECTORY + "/s_*")
        return len(files) < num_allowed_trace_job_directories


    def get_perf_host(self):
        am = fun_test.get_asset_manager()
        self.perf_host = am.get_linux_host(name=self.perf_collector_host_name)
        return self.perf_host

    def prepare(self, f1_index=0, prefix="", remove_old_job_directory=True):
        if not self.perf_host:
            self.get_perf_host()
        fun_test.simple_assert(self.perf_host, "Get perf host handle")
        if "csi_perf" in self.perf_host.extra_attributes:
            if "tools_directory" in self.perf_host.extra_attributes["csi_perf"]:
                self.tools_directory = self.perf_host.extra_attributes["csi_perf"]["tools_directory"]
        fun_test.simple_assert(self.ensure_space_exists(), "Ensure space exists on. Please clear trace files/directories from {}. max dirs: {}".format(BASE_JOB_DIRECTORY, MAX_TRACE_JOB_DIRECTORIES))
        s = "s_{}_{}_f1_{}".format(fun_test.get_suite_execution_id(), fun_test.get_test_case_execution_id(), f1_index)
        if prefix:
            s += "_{}".format(prefix)
        s = "{}/{}".format(BASE_JOB_DIRECTORY, s)
        if self.perf_host.check_file_directory_exists(s):
            if remove_old_job_directory:
                self.perf_host.remove_directory_contents(s)
                self.perf_host.command("mkdir -p {}".format(s))
        self.job_directory = s
        self._prepare_directory_structure(job_directory=self.job_directory)
        tftp_image_path = self.fs.get_tftp_image_path()
        self.move_f1_binary(tftp_image_path=tftp_image_path)
        fun_test.add_checkpoint("Perf host: {} Job directory: {}".format(self.perf_host, self.job_directory))

        return True

    def _prepare_directory_structure(self, job_directory):
        self.perf_host.command("mkdir -p {}/odp".format(job_directory))
        self.perf_host.command("mkdir -p {}/odp/trace_dumps".format(job_directory))

    def start(self, f1_index=0):
        self.instance += 1
        # ensure perf listener is not running
        process_ids = self.perf_host.get_process_id_by_pattern(process_pat=PERF_LISTENER, multiple=True)
        if process_ids:
            for process_id in process_ids:
                self.perf_host.kill_process(signal=9, process_id=process_id, kill_seconds=2)
        self.perf_host.command("mv trace_cluster* /tmp")
        command = "python " + PERF_LISTENER_PATH + " --perf-ip={}".format(self.listener_ip)
        self.perf_listener_process_id = self.perf_host.start_bg_process(command, output_file="/tmp/perf_listener_f1_{}.log".format(f1_index))

        dpc_client = self.fs.get_dpc_client(f1_index=f1_index, auto_disconnect=True)
        dpc_client.json_execute(verb="perf", data="reinit", command_duration=4)
        dpc_client.json_execute(verb="perf", data="start", command_duration=4)

    def stop(self, f1_index=0):
        dpc_client = self.fs.get_dpc_client(f1_index=f1_index, auto_disconnect=True)
        dpc_client.json_execute(verb="perf", data="stop", command_duration=4)
        dpc_client.json_execute(verb="perf", data="offload", command_duration=4)
        fun_test.sleep("Wait for offload to complete", seconds=120)
        self.move_trace_files(source_directory=self.tools_directory, job_directory=self.job_directory)
        uart_log_path = self.fs.get_uart_log_file(f1_index=f1_index, post_fix=self.instance)
        self.move_uart_log(uart_log_path=uart_log_path, f1_index=f1_index)

    def move_trace_files(self, source_directory, job_directory):
        trace_files = self.perf_host.list_files("{}/trace_cluster*".format(source_directory))
        fun_test.test_assert(trace_files, "At least one perf trace file seen")
        self.perf_host.command("mv {}/trace_cluster* {}/odp/trace_dumps/".format(source_directory, job_directory))

    def move_uart_log(self, uart_log_path, f1_index=0):
        target_file_path = "{}/odp/uartout0.{}.txt".format(self.job_directory, f1_index)
        fun_test.scp(source_file_path=uart_log_path,
                     target_file_path=target_file_path,
                     target_ip=self.perf_host.host_ip,
                     target_username=self.perf_host.ssh_username, target_password=self.perf_host.ssh_password)
        fun_test.test_assert(self.perf_host.check_file_directory_exists(target_file_path), "UART log in the right location")

    def move_f1_binary(self, tftp_image_path):
        fun_test.get_asset_manager().get_regression_service_host_spec()
        target_file_path = "{}/{}".format(self.job_directory, FUNOS_F1_NAME)
        tftp_server = Linux(host_ip=TFTP_SERVER_IP,
                            ssh_username=TFTP_SERVER_SSH_USERNAME,
                            ssh_password=TFTP_SERVER_SSH_PASSWORD)
        jenkins_build_path = fun_test.get_job_environment_variable("jenkins_build_path")
        fun_test.test_assert(jenkins_build_path, "Jenkins build path: {}".format(jenkins_build_path))
        source_file_path = "{}/funos-f1".format(jenkins_build_path)
        tftp_server.scp(source_file_path=source_file_path,
                        target_ip=self.perf_host.host_ip,
                        target_username=self.perf_host.ssh_username,
                        target_password=self.perf_host.ssh_password,
                        target_file_path=target_file_path)
        fun_test.test_assert(self.perf_host.check_file_directory_exists(target_file_path), "funos-f1 in the right location")


    def setup_networking(self):
        pass




if __name__ == "__main__":
    p = PdTraceTemplate(perf_collector_host_name="poc-server-04", listener_ip="123", fs=None)
    p.prepare(f1_index=0)