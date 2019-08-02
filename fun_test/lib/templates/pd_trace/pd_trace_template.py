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
FUNOS_F1_NAME = "funos-f1.gz"


class PdTraceTemplate():
    def __init__(self, perf_collector_host_name):
        self.perf_collector_host_name = perf_collector_host_name
        self.perf_host = None
        self.perf_listener_process_id = None
        self.job_directory = None

    def prepare(self, prefix="", remove=True):
        if not self.perf_host:
            am = fun_test.get_asset_manager()
            self.perf_host = am.get_linux_host(name=self.perf_collector_host_name)
        fun_test.simple_assert(self.perf_host, "Get perf host handle")
        s = "s_{}_{}".format(fun_test.get_suite_execution_id(), fun_test.get_test_case_execution_id())
        if prefix:
            s += "_{}".format(prefix)
        s = "{}/{}".format(BASE_JOB_DIRECTORY, s)
        if self.perf_host.check_file_directory_exists(s):
            if remove:
                self.perf_host.remove_directory_contents(s)
                self.perf_host.command("mkdir -p {}".format(s))
        self.job_directory = s
        self._prepare_directory_structure(job_directory=self.job_directory)

        return True

    def _prepare_directory_structure(self, job_directory):
        self.perf_host.command("mkdir -p {}/odp".format(job_directory))
        self.perf_host.command("mkdir -p {}/odp/trace_dumps".format(job_directory))

    def start(self, listener_ip):
        # ensure perf listener is not running
        process_ids = self.perf_host.get_process_id_by_pattern(process_pat=PERF_LISTENER, multiple=True)
        if process_ids:
            for process_id in process_ids:
                self.perf_host.kill_process(signal=9, process_id=process_id, kill_seconds=2)
        self.perf_host.command("mv trace_cluster* /tmp")
        command = "python " + PERF_LISTENER_PATH + " --perf-ip={}".format(listener_ip)
        self.perf_listener_process_id = self.perf_host.start_bg_process(command, output_file="/tmp/perf_listener.log")

    def stop(self):
        self.move_trace_files(source_directory=TOOLS_DIRECTORY, job_directory=self.job_directory)
        uart_log_path = "/Users/johnabraham/PycharmProjects/fun_test/Integration/fun_test/web/static/logs/test_fs_nu.py_3829_100_DUT_0_fs-21_f1_0_uart_log.txt"
        self.move_uart_log(uart_log_path=uart_log_path)
        self.move_f1_binary(tftp_image_path="s_21048_funos-f1.stripped.gz")

    def move_trace_files(self, source_directory, job_directory):
        self.perf_host.command("mv {}/trace_cluster* {}/odp/trace_dumps/".format(source_directory, job_directory))

    def move_uart_log(self, uart_log_path):
        target_file_path = "{}/odp/uartout0.0.txt".format(self.job_directory)
        fun_test.scp(source_file_path=uart_log_path,
                     target_file_path=target_file_path,
                     target_ip=self.perf_host.host_ip,
                     target_username=self.perf_host.ssh_username, target_password=self.perf_host.ssh_password)
        fun_test.test_assert(self.perf_host.check_file_directory_exists(target_file_path), "trace files in the right location")

    def move_f1_binary(self, tftp_image_path):
        fun_test.get_asset_manager().get_regression_service_host_spec()
        target_file_path = "{}/{}".format(self.job_directory, FUNOS_F1_NAME)
        tftp_server = Linux(host_ip=TFTP_SERVER_IP,
                            ssh_username=TFTP_SERVER_SSH_USERNAME,
                            ssh_password=TFTP_SERVER_SSH_PASSWORD)
        tftp_server.scp(source_file_path="{}/{}".format(TFTP_DIRECTORY,
                                                        tftp_image_path),
                        target_ip=self.perf_host.host_ip,
                        target_username=self.perf_host.ssh_username,
                        target_password=self.perf_host.ssh_password,
                        target_file_path=target_file_path)
        fun_test.test_assert(self.perf_host.check_file_directory_exists(target_file_path), "funos-f1 in the right location")


    def setup_networking(self):
        pass




if __name__ == "__main__":
    p = PdTraceTemplate(perf_collector_host_name="poc-server-04")
    p.prepare()
    p.start(listener_ip="20.1.1.1")
    p.stop()
