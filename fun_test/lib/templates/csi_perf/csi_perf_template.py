from lib.system.fun_test import fun_test
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER_IP, TFTP_DIRECTORY, TFTP_SERVER_SSH_PASSWORD, TFTP_SERVER_SSH_USERNAME
from fun_settings import STASH_DIR
import os
# Connect to tracing server
# Setup networking
# Setup job directory
# move uart log
# move funos-binary


TRACE_JOBS_DIRECTORY = "trace_jobs"
BASE_JOB_DIRECTORY = "/home/localadmin/{}".format(TRACE_JOBS_DIRECTORY)
TOOLS_DIRECTORY = "/home/localadmin"
PERF_LISTENER = "perf_listener.py"
PERF_LISTENER_PATH = TOOLS_DIRECTORY + "/" + PERF_LISTENER
FUNOS_F1_NAME = "funos-f1"
MAX_TRACE_JOB_DIRECTORIES = 50
EXPECTED_TOOLS = ["process_perf.sh", "view_perf.sh", "listener_lib.py", "perf_listener.py"]
EXPECTED_DOCKER_IMAGES = ["docker.fungible.com/perf_processing",
                          "docker.fungible.com/perf_server",
                          "docker.fungible.com/cm_processing"]
EXPECTED_TOOL_LOCATIONS = {"PalladiumOnDemand": [
    {"source_file_path": "docker/process_perf.sh", "target_file_path": "process_perf.sh"},
    {"source_file_path": "docker/process_cm.sh", "target_file_path": "process_cm.sh"},
    {"source_file_path": "docker/view_perf.sh", "target_file_path": "view_perf.sh"}],
    "FunTools": [{"source_file_path": "csi_listeners/perf_listener.py", "target_file_path": "perf_listener.py"},
                 {"source_file_path": "csi_listeners/listener_lib.py", "target_file_path": "listener_lib.py"}]}


class CsiPerfOperation:
    PREPARE = "reinit"
    START = "start"
    STOP = "stop"
    OFFLOAD = "offload"


class CsiPerfTemplate():
    def __init__(self, perf_collector_host_name, listener_ip, fs, setup_docker=False, listener_port=None):
        self.perf_collector_host_name = perf_collector_host_name
        self.perf_host = None
        self.perf_listener_process_id = None
        self.job_directory = None
        self.listener_ip = listener_ip
        self.fs = fs
        self.instance = 0
        self.tools_directory = TOOLS_DIRECTORY
        self.base_job_directory = TOOLS_DIRECTORY + "/trace_jobs"
        self.setup_docker = setup_docker
        self.prepare_complete = False
        self.listener_port = listener_port

    def ensure_docker_images_exist(self):
        docker_images_output = self.perf_host.sudo_command("docker images")
        for docker_image in EXPECTED_DOCKER_IMAGES:
            fun_test.simple_assert(docker_image in docker_images_output, "Docker image: {} should exist".format(docker_image))
        return True

    def ensure_tools_exists(self):
        for tool in EXPECTED_TOOLS:
            fun_test.simple_assert(self.perf_host.list_files("{}/{}".format(self.tools_directory, tool)), "{} should exist".format(tool))
        return True

    def ensure_space_is_available(self, num_allowed_trace_job_directories=MAX_TRACE_JOB_DIRECTORIES):
        """
        We need to ensure the server has enough space.
        For now we ensure only num_allowed_trace_directories can exist
        :return True if number of current trace directories is < num_allowed_trace_job_directories
        """
        pass
        self.perf_host = self.get_perf_host()
        files = self.perf_host.list_files(self.base_job_directory + "/s_*")
        if len(files) >= num_allowed_trace_job_directories:
            # remove the oldest directory
            fun_test.log("Removing oldest directory: {}".format(files[0]["filename"]))
            self.perf_host.remove_directory(files[0]["filename"])
            files = self.perf_host.list_files(self.base_job_directory + "/s_*")
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
                self.base_job_directory = self.tools_directory + "/" + TRACE_JOBS_DIRECTORY

        if self.setup_docker:
            fun_test.simple_assert(self.do_setup_docker(), "Docker setup")
        fun_test.simple_assert(self.position_files(), "Position tools")
        fun_test.simple_assert(self.ensure_space_is_available(), "Ensure space exists on. Please clear trace files/directories from {}. max dirs: {}".format(self.base_job_directory, MAX_TRACE_JOB_DIRECTORIES))
        fun_test.simple_assert(self.ensure_tools_exists(), "Ensure necessary tools exists")
        fun_test.simple_assert(self.ensure_docker_images_exist(), "Ensure docker images exist")

        s = "s_{}_{}_f1_{}".format(fun_test.get_suite_execution_id(), fun_test.get_test_case_execution_id(), f1_index)
        if prefix:
            s += "_{}".format(prefix)
        s = "{}/{}".format(self.base_job_directory, s)
        if self.perf_host.check_file_directory_exists(s):
            if remove_old_job_directory:
                self.perf_host.remove_directory_contents(s)
                self.perf_host.command("mkdir -p {}".format(s))
        self.job_directory = s
        self._prepare_directory_structure(job_directory=self.job_directory)
        tftp_image_path = self.fs.get_tftp_image_path()
        self.move_f1_binary(tftp_image_path=tftp_image_path)
        fun_test.add_checkpoint("Perf host: {} Job directory: {}".format(self.perf_host, self.job_directory))
        self.prepare_complete = True
        return True

    def _prepare_directory_structure(self, job_directory):
        self.perf_host.command("mkdir -p {}/odp".format(job_directory))
        self.perf_host.command("mkdir -p {}/odp/trace_dumps".format(job_directory))

    def start(self, f1_index=0, dpc_client=None):
        fun_test.simple_assert(self.prepare_complete, "Please call prepare() before calling start")
        fun_test.add_checkpoint("CSI perf before start")
        self.instance += 1
        # ensure perf listener is not running
        process_ids = self.perf_host.get_process_id_by_pattern(process_pat=PERF_LISTENER, multiple=True)
        if process_ids:
            for process_id in process_ids:
                self.perf_host.kill_process(signal=9, process_id=process_id, kill_seconds=2)
        process_ids = self.perf_host.get_process_id_by_pattern(process_pat=PERF_LISTENER, multiple=True)

        self.perf_host.command("mv trace_cluster* /tmp")
        command = "python " + PERF_LISTENER_PATH + " --perf-ip={}".format(self.listener_ip)
        if self.listener_port:
            command += " --perf-port={}".format(self.listener_port)
        self.perf_listener_process_id = self.perf_host.start_bg_process(command, output_file="/tmp/perf_listener_f1_{}.log".format(f1_index))

        if not dpc_client:
            dpc_client = self.fs.get_dpc_client(f1_index=f1_index, auto_disconnect=True)
        dpc_client.json_execute(verb="csi", data="reinit", command_duration=4)
        dpc_client.json_execute(verb="csi", data="start", command_duration=4)
        fun_test.add_checkpoint("CSI perf started")

    def stop(self, f1_index=0, dpc_client=None):
        fun_test.add_checkpoint("CSI perf before stop")
        if not dpc_client:
            dpc_client = self.fs.get_dpc_client(f1_index=f1_index, auto_disconnect=True)
        dpc_client.json_execute(verb="csi", data="stop", command_duration=4)
        # dpc_client.json_execute(verb="csi", data="offload", command_duration=4)
        fun_test.sleep("Wait for offload to complete", seconds=120)
        self.move_trace_files(source_directory=self.tools_directory, job_directory=self.job_directory)
        uart_log_path = self.fs.get_uart_log_file(f1_index=f1_index, post_fix=self.instance)
        self.move_uart_log(uart_log_path=uart_log_path, f1_index=f1_index)
        fun_test.add_checkpoint("CSI perf after stop")
        fun_test.report_message("CSI perf traces are at trace job directory: {}".format(self.job_directory))
        fun_test.report_message("CSI perf host: {} username: {} password: {}".format(self.perf_host.host_ip,
                                                                                     self.perf_host.ssh_username,
                                                                                     self.perf_host.ssh_password))
        fun_test.report_message("CSI perf base job directory: {}".format(self.base_job_directory))
        fun_test.report_message("CSI perf: to process perf: #./process_perf.sh {}".format(self.job_directory))
        fun_test.report_message("CSI perf: to view perf: #./view_perf.sh {}".format(self.base_job_directory))

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

    def repo_exists(self, name):
        result = None
        path = STASH_DIR + "/" + name
        if os.path.exists(path):
            result = True
        return result

    def position_files(self):
        to_position = EXPECTED_TOOL_LOCATIONS
        for repo_name, values in to_position.iteritems():
            fun_test.simple_assert(self.repo_exists(name=repo_name), "Repo: {} exists".format(repo_name))
            for value in values:
                repo_path = STASH_DIR + "/" + repo_name
                source_path = repo_path + "/" + value["source_file_path"]
                os.system("cd {}; git pull".format(repo_path))
                fun_test.simple_assert(os.path.exists(source_path), "Source: {} exists".format(source_path))
                target_file_path = TOOLS_DIRECTORY + "/" + value["target_file_path"]
                fun_test.scp(source_file_path=source_path,
                             target_file_path=target_file_path,
                             target_ip=self.perf_host.host_ip,
                             target_username=self.perf_host.ssh_username,
                             target_password=self.perf_host.ssh_password)
        result = True
        return result

    def do_setup_docker(self):
        user = self.perf_host.command("echo $USER")
        user = user.strip()
        # fun_test.simple_assert(self.perf_host.command_exists("docker"), "Docker installed")
        self.perf_host.sudo_command("usermod -aG docker {}".format(user))
        self.perf_host.sudo_command("setfacl -m user:{}:rw /var/run/docker.sock".format(user))

        commands = ["timeout 5 openssl s_client -showcerts -connect docker.fungible.com:443 | tee /tmp/cert.log",
                    "cat /tmp/cert.log | sed -n '/-----BEGIN CERTIFICATE-----/,/-----END CERTIFICATE-----/p' > /tmp/cert.pem"]
        for command in commands:
            self.perf_host.command(command)

        sudo_commands = ["mkdir /usr/share/ca-certificates/extra",
                         "cp /tmp/cert.pem /usr/share/ca-certificates/fun_cert.crt",
                         "dpkg-reconfigure ca-certificates",
                         ]
        self.perf_host.enter_sudo()
        for sudo_command in sudo_commands:
            self.perf_host.command(sudo_command, custom_prompts={'Trust new certificates from certificate authorities?': 'yes', "Certificates to activate:": "fun_cert.crt"})
        self.perf_host.command("apt-get update")
        self.perf_host.command("apt install -y docker.io")
        self.perf_host.exit_sudo()
        self.perf_host.command("service docker stop", custom_prompts={"Password:": self.perf_host.ssh_password})
        self.perf_host.command("service docker start", custom_prompts={"Password:": self.perf_host.ssh_password})
        docker_commands = ["docker pull docker.fungible.com/perf_processing",
                           "docker pull docker.fungible.com/perf_server",
                           "docker pull docker.fungible.com/cm_processing"]
        for docker_command in docker_commands:
            self.perf_host.command(docker_command)
        return True

if __name__ == "__main__":
    p = CsiPerfTemplate(perf_collector_host_name="mktg-server-14", listener_ip="123", fs=None, setup_docker=True)
    p.prepare(f1_index=0)