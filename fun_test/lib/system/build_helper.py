from lib.system.fun_test import fun_test, FunTimer
from lib.utilities.jenkins_manager import JenkinsManager
from fun_settings import TFTP_SERVER_IP, TFTP_SERVER_SSH_USERNAME, TFTP_SERVER_SSH_PASSWORD, TFTP_DIRECTORY
from lib.host.linux import Linux


class BuildHelper():
    FUN_OS_STRIPPED_IMAGE_NAME = "funos-f1.stripped"

    def __init__(self,
                 parameters,
                 max_build_time=60 * 25,
                 job_name="emulation/fun_on_demand",
                 disable_assertions=None):
        self.parameters = parameters
        self.max_build_time = max_build_time
        self.disable_assertions = disable_assertions
        self.jenkins_manager = JenkinsManager(job_name=job_name)

    def build_emulation_image(self, submitter_email=None):
        result = None
        parameters = self.parameters

        build_number = None
        max_tries = 3
        while not build_number and max_tries:
            max_tries -= 1
            queue_item = self.jenkins_manager.build(params=parameters, extra_emails=[submitter_email])
            max_wait_for_build_start = 60
            build_start_timer = FunTimer(max_time=max_wait_for_build_start)
            fun_test.sleep("Before polling Jenkins", seconds=15)
            while not build_start_timer.is_expired():
                build_number = self.jenkins_manager.get_build_number(queue_item=queue_item)
                if build_number:
                    break
                fun_test.sleep("Build start trigger")
            if not build_number:
                fun_test.log("")
                fun_test.sleep(seconds=10 * 60, message="Retry Jenkins build. Remaining tries: {}".format(max_tries))

        fun_test.test_assert(build_number, "Jenkins build number is {}".format(build_number))
        fun_test.log("Jenkins build-URL: {}".format(self.jenkins_manager.get_build_url(build_number)))
        job_info = self.jenkins_manager.get_job_info(build_number=build_number)

        build_timer = FunTimer(max_time=self.max_build_time)
        while job_info["building"] and not build_timer.is_expired():
            job_info = self.jenkins_manager.get_job_info(build_number=build_number)
            fun_test.sleep("Re-checking Jenkins build info. Remaining time: {}".format(build_timer.remaining_time()), seconds=30)

        fun_test.test_assert_expected(actual=job_info["result"], expected="SUCCESS", message="Jenkins build: {} success".format(build_number))

        bld_props_path = self.jenkins_manager.get_bld_props_path(build_number=build_number)
        fun_test.simple_assert(bld_props_path, "Bld props path")
        bld_props = self.jenkins_manager.get_bld_props(build_number=build_number, bld_props_path=bld_props_path)
        fun_test.test_assert(bld_props, "Bld props retrieved")

        image_path = self.jenkins_manager.get_image_path(build_number=build_number)
        fun_test.log("Image path: {}".format(image_path))
        fun_test.test_assert(image_path, "Image path retrieved")

        tftp_server = Linux(host_ip=TFTP_SERVER_IP,
                            ssh_username=TFTP_SERVER_SSH_USERNAME,
                            ssh_password=TFTP_SERVER_SSH_PASSWORD)
        filename = "s_{}_{}".format(fun_test.get_suite_execution_id(), self.FUN_OS_STRIPPED_IMAGE_NAME)
        gz_filename = filename + ".gz"
        tftp_server.command("cd {}".format(TFTP_DIRECTORY))
        tftp_server.command("rm -f {}".format(filename))
        tftp_server.command("rm -f {}".format(gz_filename))
        tftp_server.command("cp {}/{} {}".format(image_path, self.FUN_OS_STRIPPED_IMAGE_NAME, filename))
        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + filename), "Image {} copied to TFTP server".format(filename))
        tftp_server.command("gzip {}".format(filename))

        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + gz_filename), "Gz Image ready on TFTP server".format(filename))

        return gz_filename

if __name__ == "__main__":
    boot_args = "app=jpeg_perf_test --test-exit-fast"
    fun_os_make_flags = "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list"

    build_helper = BuildHelper(boot_args=boot_args, fun_os_make_flags=fun_os_make_flags)
    build_helper.build_emulation_image()
