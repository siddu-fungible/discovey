from lib.system.fun_test import fun_test, FunTimer
from lib.utilities.jenkins_manager import JenkinsManager
from fun_settings import TFTP_SERVER_IP, TFTP_SERVER_SSH_USERNAME, TFTP_SERVER_SSH_PASSWORD, TFTP_DIRECTORY
from lib.host.linux import Linux


class BuildHelper():
    def __init__(self,
                 boot_args=None,
                 fun_os_make_flags=None,
                 max_build_time=60 * 15,
                 job_name="emulation/fun_on_demand",
                 disable_assertions=None):
        self.boot_args = boot_args
        self.fun_os_make_flags = fun_os_make_flags
        self.max_build_time = max_build_time
        self.disable_assertions = disable_assertions
        self.jenkins_manager = JenkinsManager(job_name=job_name)

    def build_emulation_image(self):
        result = None
        params = {"BOOTARGS": self.boot_args}
        if self.fun_os_make_flags:
            params["FUNOS_MAKEFLAGS"] = self.fun_os_make_flags

        if self.disable_assertions is not None:
            params["DISABLE_ASSERTIONS"] = self.disable_assertions

        queue_item = self.jenkins_manager.build(params=params)
        build_number = None
        max_wait_for_build_start = 60
        build_start_timer = FunTimer(max_time=max_wait_for_build_start)
        fun_test.sleep("Before polling", seconds=15)
        while not build_start_timer.is_expired():
            build_number = self.jenkins_manager.get_build_number(queue_item=queue_item)
            if build_number:
                break
            fun_test.sleep("Build start trigger")

        fun_test.test_assert(build_number, "Jenkins build number is {}".format(build_number))
        job_info = self.jenkins_manager.get_job_info(build_number=build_number)

        build_timer = FunTimer(max_time=self.max_build_time)
        while job_info["building"] and not build_timer.is_expired():
            job_info = self.jenkins_manager.get_job_info(build_number=build_number)
            fun_test.sleep("Re-checking build info. Remaining time: {}".format(build_timer.remaining_time()), seconds=30)

        fun_test.test_assert_expected(actual=job_info["result"], expected="SUCCESS", message="Jenkins build: {} success".format(build_number))
        node_number = self.jenkins_manager.get_node_number(build_number=build_number)
        filename = "s_{}_funos-f1.stripped".format(fun_test.get_suite_execution_id())
        local_file_path = '/tmp/{}'.format(filename)
        self.jenkins_manager.download_file(source_path=self.jenkins_manager.get_emulation_image_path(build_number=build_number,
                                                                                           node_number=node_number),
                                      target_path=local_file_path)
        fun_test.scp(source_file_path=local_file_path, target_ip=TFTP_SERVER_IP, target_username=TFTP_SERVER_SSH_USERNAME, target_password=TFTP_SERVER_SSH_PASSWORD, target_file_path=TFTP_DIRECTORY + "/")
        tftp_server = Linux(host_ip=TFTP_SERVER_IP, ssh_username=TFTP_SERVER_SSH_USERNAME, ssh_password=TFTP_SERVER_SSH_PASSWORD)
        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + filename), "Image {} copied to TFTP server".format(filename))
        tftp_server.command("cd {}".format(TFTP_DIRECTORY))
        gz_filename = filename + ".gz"
        tftp_server.command("rm -f {}".format(gz_filename))
        tftp_server.command("gzip {}".format(filename))
        fun_test.test_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + gz_filename), "Image gz for {} ready at TFTP server".format(filename))
        return gz_filename

if __name__ == "__main__":
    boot_args = "app=jpeg_perf_test --disable-wu-watchdog --test-exit-fast"
    fun_os_make_flags = "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list"

    build_helper = BuildHelper(boot_args=boot_args, fun_os_make_flags=fun_os_make_flags)
    build_helper.build_emulation_image()
