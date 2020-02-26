from lib.system.fun_test import fun_test
from lib.host.linux import Linux
from fun_settings import DOCHUB_BASE_URL
from lib.utilities.http import fetch_text_file


class FungibleController(Linux):
    BUILD_SCRIPT_DOWNLOAD_DIRECTORY = "/tmp/remove_me_build_script"
    def __init__(self, **kwargs):
        super(FungibleController, self).__init__(**kwargs)
        self.initialized = False

    def initialize(self, reset=False):
        fun_test.log("Fungible controller: {} initialize".format(self))
        self.initialized = True

    def is_ready_for_deploy(self):
        result = False
        if not self.initialized:
            self.initialize()
        return result

    def health(self, only_reachability=False):
        base_health = super(FungibleController, self).health(only_reachability=only_reachability)
        result = base_health
        return result

    def deploy(self, dut_instances, already_deployed=False):
        if not self.initialized:
            self.initialize()
        fs_objs = dut_instances
        return True

    def get_build_number_for_latest(self, release_train):
        url = "{}/{}/fc/latest/build_info.txt".format(DOCHUB_BASE_URL, release_train)

        result = None
        build_info_file_contents = fetch_text_file(url=url)
        if build_info_file_contents:
            try:
                result = int(build_info_file_contents)
            except Exception as ex:
                print("Error getting build number: {}".format(str(ex)))
        return result

    def install_bundle(self, release_train="master", build_number="latest"):
        if build_number == "latest":
            build_number = self.get_build_number_for_latest(release_train=release_train)
            fun_test.test_assert(build_number, "Build number for latest")
        script_file_name = "setup_fc-bld-{}.sh".format(build_number)
        script_url = "{}/{}/fc/{}/{}".format(DOCHUB_BASE_URL, release_train, build_number, script_file_name)
        target_directory = self._setup_build_script_directory()
        target_file_name = "{}/{}".format(target_directory, script_file_name)
        self.curl(output_file=target_file_name, url=script_url, timeout=180)
        fun_test.simple_assert(self.list_files(target_file_name), "Install script downloaded")
        self.sudo_command("chmod 777 {}".format(target_file_name))

    def _setup_build_script_directory(self):
        """
        Sets up the directory location where the build script such as setup_fc-bld-14.sh will be saved for the installation
        process. Remove the directory and Create the directory
        :return:
        """
        path = self.BUILD_SCRIPT_DOWNLOAD_DIRECTORY
        self.command("rm -rf {}".format(path))
        self.command("mkdir -p {}".format(path))
        return path

if __name__ == "__main__":
    fc = FungibleController(host_ip="server17", ssh_username="root", ssh_password="fun123")
    # fc.command("date")
    fc.install_bundle()