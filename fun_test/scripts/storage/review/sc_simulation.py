from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from collections import OrderedDict
from lib.host.linux import Linux
from lib.system import utils

# --environment={\"test_bed_type\":\"fs-116\"} --inputs={\"fs_count\":4,\"host_name\":\"mktg-server-11\"}


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)

        self.initialize_json_data()
        self.initialize_job_inputs()

        host_handle = self.get_host_handle(self.host_name)
        host_handle.enter_sudo()
        output = host_handle.command("docker images | grep run_fs | grep latest")
        if "run_fs" not in output:
            host_handle.command("mkdir /home/localadmin/dpu_scale_test")
            host_handle.command("wget --output-document=/home/localadmin/dpu_scale_test/run_fs-100319.tar.gz http://dochub.fungible.local/doc/cloudistics/composer/run_fs-100319.tar.gz", timeout=300)
            host_handle.command("docker load -i /home/localadmin/dpu_scale_test/run_fs-100319.tar.gz")
            host_handle.command("docker tag run_fs:100319 run_fs:latest")
            host_handle.command("docker images")
        else:
            pass
        output = host_handle.command("docker images | grep run_sc | grep latest")
        if "run_sc" not in output:
            host_handle.command(
                "wget --output-document=/home/localadmin/dpu_scale_test/run_sc-100319.tar.gz http://dochub.fungible.local/doc/cloudistics/composer/run_sc-100319.tar.gz",
                timeout=300)
            host_handle.command("docker load -i /home/localadmin/dpu_scale_test/run_sc-100319.tar.gz")
            host_handle.command("docker tag run_sc:100319 run_sc:latest")
            host_handle.command("docker images")
        else:
            pass
        host_handle.command("rm -rf /home/localadmin/dpu_scale_test/storage_controller.tar.gz"
                            " /home/localadmin/dpu_scale_test/storage_controller_gui.tar.gz")
        host_handle.command("wget --output-document=/home/localadmin/dpu_scale_test/storage_controller.tar.gz http://dochub.fungible.local/doc/jenkins/master/sc/latest/storage_controller.tar.gz", timeout=300)
        host_handle.command("wget --output-document=/home/localadmin/dpu_scale_test/storage_controller_gui.tar.gz http://dochub.fungible.local/doc/jenkins/master/sc/latest/storage_controller_gui.tar.gz", timeout=300)

        # unzipping
        host_handle.command("cd /home/localadmin/dpu_scale_test")
        host_handle.command("tar -zxvf storage_controller.tar.gz")
        host_handle.command("tar -zxvf storage_controller_gui.tar.gz")

        # keying
        host_handle.command("mv SB-Admin-BS4-Angular-6/scripts/fungible_come.crt SB-Admin-BS4-Angular-6/scripts/fun_sc.crt")
        host_handle.command("mv SB-Admin-BS4-Angular-6/scripts/fungible_come.key SB-Admin-BS4-Angular-6/scripts/fun_sc.key")

        # test
        host_handle.command("cd /home/localadmin/dpu_scale_test/StorageController/test")

        cmd_orginal = "sudo WORKSPACE=/home/localadmin/dpu_scale_test ./fs_sc_launcher.py"
        cmd = cmd_orginal + " --cleanup"
        host_handle.command(cmd, timeout=300)
        cmd = cmd_orginal + " --fs_count={}".format(self.fs_count)
        host_handle.command(cmd, timeout=300)

    def get_host_handle(self, host_name):
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        return host_handle

    def initialize_json_data(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)

    def initialize_job_inputs(self):
        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Input: {}".format(job_inputs))
        if job_inputs:
            for k, v in job_inputs.iteritems():
                setattr(self, k, v)

    def cleanup(self):
        pass

    def run(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
