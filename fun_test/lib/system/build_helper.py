from lib.system.fun_test import fun_test, FunTimer
from lib.utilities.jenkins_manager import JenkinsManager
from fun_settings import TFTP_SERVER_IP, TFTP_SERVER_SSH_USERNAME, TFTP_SERVER_SSH_PASSWORD, TFTP_DIRECTORY
from lib.host.linux import Linux
from lib.utilities.http import fetch_binary_file
import os
from random import randint

class BuildHelper():
    FUN_OS_STRIPPED_IMAGE_NAME = "funos-f1.stripped"
    DOCHUB_LATEST_PATH = "http://dochub.fungible.local/doc/jenkins/funsdk/latest"
    STABLE_MASTER_DOCHUB_PATH = "{}/Linux/funos.mips64-extra.tgz".format(DOCHUB_LATEST_PATH)
    STABLE_MASTER_DOCHUB_FLASH_TOOLS_PATH = "{}/Linux/flash_tools.tgz".format(DOCHUB_LATEST_PATH)

    def __init__(self,
                 parameters,
                 max_build_time=60 * 25,
                 job_name="emulation/fun_on_demand",
                 pre_built_artifacts=None):
        self.parameters = parameters
        self.max_build_time = max_build_time
        self.jenkins_manager = JenkinsManager(job_name=job_name)
        self.pre_built_artifacts = pre_built_artifacts

    def get_tftp_server(self):
        return Linux(host_ip=TFTP_SERVER_IP, ssh_username=TFTP_SERVER_SSH_USERNAME, ssh_password=TFTP_SERVER_SSH_PASSWORD)

    def position_pre_built_artifacts(self, pre_built_artifacts):
        filename = pre_built_artifacts["funos_binary"]
        gz_filename = filename + ".gz"
        new_gz_filename = "s_{}.gz".format(fun_test.get_suite_execution_id())

        tftp_server = self.get_tftp_server()
        tftp_server.command("cd {}".format(TFTP_DIRECTORY))
        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + filename), "Image {} copied to TFTP server".format(filename))
        tftp_server.command("gzip {}".format(filename))
        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + gz_filename), "Gz Image ready on TFTP server".format(filename))
        tftp_server.command("mv {} {}".format(gz_filename, new_gz_filename))
        return new_gz_filename

    def build_emulation_image(self, submitter_email=None):
        result = None
        parameters = self.parameters

        build_number = None
        max_tries = 3
        while not build_number and max_tries:
            max_tries -= 1
            queue_item = self.jenkins_manager.build(params=parameters, extra_emails=[submitter_email])
            max_wait_for_build_start = 60 * 20
            build_start_timer = FunTimer(max_time=max_wait_for_build_start)
            fun_test.sleep("Before polling Jenkins", seconds=15)
            while not build_start_timer.is_expired():
                build_number = self.jenkins_manager.get_build_number(queue_item=queue_item)
                if build_number:
                    break
                fun_test.sleep("Waiting for build start trigger")
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
        fun_test.set_suite_run_time_environment_variable("bld_props", bld_props)

        image_path = self.jenkins_manager.get_image_path(build_number=build_number)
        fun_test.log("Image path: {}".format(image_path))
        fun_test.test_assert(image_path, "Image path retrieved")

        tftp_server = self.get_tftp_server()
        file_output = tftp_server.file(path="{}/{}".format(image_path, self.FUN_OS_STRIPPED_IMAGE_NAME), mime_type=True)
        filename = "s_{}_{}".format(fun_test.get_suite_execution_id(), self.FUN_OS_STRIPPED_IMAGE_NAME)
        if file_output and "mime_type" in file_output and "application/octet-stream" in file_output["mime_type"]:
            filename += ".signed"

        tftp_server.command("cd {}".format(TFTP_DIRECTORY))
        tftp_server.command("rm -f {}".format(filename))
        tftp_server.command("cp {}/{} {}".format(image_path, self.FUN_OS_STRIPPED_IMAGE_NAME, filename))
        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + filename), "Image {} copied to TFTP server".format(filename))

        gz_filename = filename + ".gz"
        tftp_server.command("rm -f {}".format(gz_filename))
        tftp_server.command("gzip {}".format(filename))
        fun_test.simple_assert(tftp_server.list_files(TFTP_DIRECTORY + "/" + gz_filename), "Gz Image ready on TFTP server".format(filename))
        return gz_filename

    def fetch_stable_master(self, debug=False, stripped=True, generate_signed_image=True):
        result = False
        tftp_filename = "{}/s_{}_{}.gz".format(TFTP_DIRECTORY, fun_test.get_suite_execution_id(), self.FUN_OS_STRIPPED_IMAGE_NAME)
        if generate_signed_image:
            tftp_filename = "{}/s_{}_{}.signed.gz".format(TFTP_DIRECTORY, fun_test.get_suite_execution_id(),
                                                   self.FUN_OS_STRIPPED_IMAGE_NAME)

        base_temp_directory = "/tmp/stable_master/s_{}".format(fun_test.get_suite_execution_id())
        tftp_server = self.get_tftp_server()
        try:
            tmp_tgz_file_name = "{}/extra_remove_me.tgz".format(base_temp_directory)
            tmp_untar_directory = "{}/untar_extra_remove_me".format(base_temp_directory)
            tftp_server.command("cd /tmp; mkdir -p {}".format(tmp_untar_directory))
            tftp_server.curl(url=self.DOCHUB_LATEST_PATH + "/bld_props.json")
            tftp_server.curl(url=self.STABLE_MASTER_DOCHUB_PATH, output_file=tmp_tgz_file_name)
            fun_test.log(tmp_tgz_file_name)
            tftp_server.untar(file_name=tmp_tgz_file_name, dest=tmp_untar_directory, sudo=False)

            funos_binary_name = "funos-f1"

            if not debug:
                funos_binary_name += "-release"
            if stripped:
                funos_binary_name += ".stripped"

            fun_os_binary_full_path = "{}/bin/{}".format(tmp_untar_directory, funos_binary_name)
            if not debug:
                modified_release_path = fun_os_binary_full_path.replace("-release", "")
                tftp_server.command("mv {} {}".format(fun_os_binary_full_path, modified_release_path))
                fun_os_binary_full_path = modified_release_path

            f1_stripped_directory = "{}/bin/".format(tmp_untar_directory)
            fun_test.simple_assert(tftp_server.list_files("{}".format(fun_os_binary_full_path)), "FunOS binary path found")


            tmp_flash_tools_tgz_file_name = "{}/flash_tools_remove_me.tgz".format(base_temp_directory)
            tftp_server.curl(url=self.STABLE_MASTER_DOCHUB_FLASH_TOOLS_PATH, output_file=tmp_flash_tools_tgz_file_name)
            flash_tools_dir = "{}/flash_tools".format(tmp_untar_directory)
            tftp_server.command("mkdir -p {}".format(flash_tools_dir))
            tftp_server.untar(file_name=tmp_flash_tools_tgz_file_name, dest=flash_tools_dir, sudo=False)
            tftp_server.list_files(tmp_untar_directory + "/*")


            gz_filename = fun_os_binary_full_path + ".gz"
            tftp_server.command("rm {}".format(gz_filename))
            # tftp_server.command("gzip {}".format(fun_os_binary_full_path))


            if generate_signed_image:
                flash_tools_dir = "{}/bin/flash_tools".format(flash_tools_dir)
                tftp_server.command("cd {}".format(flash_tools_dir))

                # tftp_server.command("ls -l {}".format(f1_stripped_path))
                tftp_server.command(
                    "python3 {}/generate_flash.py --action sign --source-dir {} {}/mmc_config_fungible.json {}/key_bag_config.json".format(
                        flash_tools_dir,
                        f1_stripped_directory,
                        flash_tools_dir,
                        flash_tools_dir))

                signed_file = "{}/funos.signed.bin".format(flash_tools_dir)
                fun_test.simple_assert(tftp_server.list_files(signed_file), "signed image created")
                gz_filename = "{}".format(signed_file) + ".gz"
                tftp_server.command("rm {}".format(gz_filename))
                tftp_server.command("gzip {}".format(signed_file))

            fun_test.simple_assert(tftp_server.list_files(gz_filename), "GZ file created")
            tftp_server.command("mv {} {}".format(gz_filename, tftp_filename))
            fun_test.simple_assert(tftp_server.list_files(tftp_filename), "File moved to tftpboot directory")
            result = os.path.basename(tftp_filename)
            # fun_test.log("Result is: {}".format(result))
        except Exception as ex:
            fun_test.critical(str(ex))
        finally:
            tftp_server.command("rm -rf {}".format(base_temp_directory))
            tftp_server.disconnect()
        return result


if __name__ == "__main2__":
    boot_args = "app=jpeg_perf_test --test-exit-fast"
    fun_os_make_flags = "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list"

    build_helper = BuildHelper(boot_args=boot_args, fun_os_make_flags=fun_os_make_flags)
    build_helper.build_emulation_image()


if __name__ == "__main__":
    bh = BuildHelper(parameters=None)
    bh.fetch_stable_master()