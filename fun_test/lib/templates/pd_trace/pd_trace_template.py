from lib.system.fun_test import fun_test
# Connect to tracing server
# Setup networking
# Setup job directory
# move uart log
# move funos-binary


BASE_JOB_DIRECTORY = "/tmp/trace_jobs"
TOOLS_DIRECTORY = "/home/localadmin"
PERF_LISTENER = "perf_listener.py"
PERF_LISTENER_PATH = TOOLS_DIRECTORY + "/" + PERF_LISTENER


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

    def move_trace_files(self, source_directory, job_directory):
        self.perf_host.command("mv {}/trace_cluster* {}/odp/trace_dumps/", )

    def setup_networking(self):
        pass

    def setup_job_directory(self):
        pass


if __name__ == "__main__":
    p = PdTraceTemplate(perf_collector_host_name="poc-server-04")
    p.prepare()
    p.start(listener_ip="20.1.1.1")
