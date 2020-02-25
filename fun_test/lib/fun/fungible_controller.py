from lib.system.fun_test import *
from lib.host.linux import Linux
COME_FC_CONNECT_FILE_CONTENTS = """
#!/bin/bash
set -e

#comma separated list of controller IPs
CONTROLLER_IPS={}
ETCD_PORT=2379
F1_0_APISVR_PORT=6000
F1_1_APISVR_PORT=6001

echo "Hello storage world!"


exit 0
"""


class FungibleController(Linux):
    EXPECTED_DOCKER_IMAGES = ["docker.fungible.com/sns-controller",
                              "docker.fungible.com/cfgmgr-controller",
                              "docker.fungible.com/run_apigateway",
                              "docker.fungible.com/storage-services",
                              "confluentinc/cp-kafka",
                              "confluentinc/cp-zookeeper",
                              "cassandra"]
    EXPECTED_CONTAINERS = ["run_sc",
                           "apigateway",
                           "cfgmgr",
                           "sns",
                           "kafka",
                           "zookeeper",
                           "cassandra-seed1",
                           "etcd"]
    CONTAINERS_BRING_UP_TIME_MAX = 30

    def __init__(self, **kwargs):
        super(FungibleController, self).__init__(**kwargs)
        self.initialized = False

    def initialize(self, reset=False, ws="/opt/fungible/fc/"):

        fun_test.log("Fungible controller: {} initialize".format(self))

        # WORKAROUND
        docker_images_output = self.sudo_command("docker images")
        for docker_image in self.EXPECTED_DOCKER_IMAGES:
            fun_test.simple_assert(docker_image in docker_images_output,
                                   "Docker image: {} should exist".format(docker_image))

        self.command("export WORKSPACE={}".format(ws))

        self.install_fc_bundle()
        self.command("rm -fr FunAPIGateway")
        self.command("cd {}".format(ws))
        self.command("git clone -o StrictHostKeyChecking=no"
                     " -o UserKnownHostsFile=/dev/null git@github.com:fungible-inc/FunAPIGateway.git")
        self.command("cd FunAPIGateway/docker/containers/; ./fun_containers.sh start")

        self.initialized = True

    def install_fc_bundle(self, ws="/opt/fungible/fc/"):
        self.command("cd {}".format(ws))
        docker_image_ids = self.command("docker images -q").split("\n")
        for docker_image_id in docker_image_ids:
            delete_docker_image = self.command("docker rmi {}".format(docker_image_id))
            fun_test.add_checkpoint(expected=True, actual="Deleted" in delete_docker_image,
                                    checkpoint="Deleted docker image: ".format({docker_image_id}))

        self.command("wget https://dochub.fungible.local/doc/jenkins/master/fc/12/setup_fc-bld-12.sh")
        #  TODO: Enable once bundle is available without versions
        self.sudo_command("chmod 777 setup_fc-bld-12.sh", timeout=300)
        self.sudo_command("./setup_fc-bld-12.sh")

    def is_ready_for_deploy(self):
        if not self.initialized:
            self.initialize()
        result = self.ensure_expected_containers_running()
        return result

    def health(self, only_reachability=False):
        base_health = super(FungibleController, self).health(only_reachability=only_reachability)
        result = base_health
        return result

    def deploy(self, dut_instances, already_deployed=False):
        if not self.initialized:
            self.initialize()
        fs_objs = dut_instances
        for fs_obj in fs_objs:
            bmc_handle = fs_obj.get_bmc()
            ifconfig = bmc_handle.ifconfig()
            mac = ifconfig[0]['HWaddr'].lower()
            self.create_oc_file(mac=mac, fs_name=fs_obj.asset_name)
            come_handle = fs_obj.get_come()
            file_name = self.create_come_fc_connect_file(come_handle=come_handle)

            come_handle.sudo_command(
                "cd /usr/local/bin; sudo ztp_dpu_discovery.py -i enp3s0f0 -s -b {}".format(file_name))

        return True

    def create_oc_file(self, mac, fs_name):
        file_name = "DPU_" + mac + "_oc.cfg"
        fun_test.test_assert(expression=fun_test.scp(
            source_file_path=ASSET_DIR + "/open_configs/{}_oc.json".format(fs_name),
            target_file_path="/opt/fungible/day1_configfiles/{}".format(file_name), target_ip=self.host_ip,
            target_username=self.ssh_username, target_password=self.ssh_password),
            message="Create Open Config file on Fungible Controller")

    def create_come_fc_connect_file(self, host_handle, file_name="connect_to_fc.sh", file_location="~/"):

        host_handle.sudo_command("rm {}".format(file_location + file_name))
        contents = COME_FC_CONNECT_FILE_CONTENTS.format(self.host_ip)
        host_handle.create_file(file_name=file_location + file_name, contents=contents)
        return file_name

    def ensure_expected_containers_running(self, max_time=CONTAINERS_BRING_UP_TIME_MAX):
        fun_test.sleep(seconds=10, message="Waiting for expected containers")
        expected_containers_running = self.is_expected_containers_running()
        expected_containers_running_timer = FunTimer(max_time=max_time)

        while not expected_containers_running and not expected_containers_running_timer.is_expired(
                print_remaining_time=True):
            fun_test.sleep(seconds=10, message="Waiting for expected containers", context=self.fs.context)
            expected_containers_running = self.is_expected_containers_running()
        return expected_containers_running

    def is_expected_containers_running(self):

        result = True
        containers = self.docker(sudo=True)
        for expected_container in self.EXPECTED_CONTAINERS:
            found = False
            if containers:
                for container in containers:
                    container_name = container["Names"]
                    if container_name == expected_container:
                        found = True
                        container_is_up = "Up" in container["Status"]
                        if not container_is_up:
                            result = False
                            fun_test.critical("Container {} is not up".format(container_name), context=self.fs.context)
                            break
                if not found:
                    fun_test.critical("Container {} was not found".format(expected_container), context=self.fs.context)
                    result = False
                break
            else:
                fun_test.critical("No containers are running")
                result = False
        return result

    def kill_fc_containers(self, ws="/opt/fungible/fc"):
        self.command("cd {}/FunAPIGateway/docker/containers/; ./fun_containers.sh stop".format(ws), timeout=300)
        self.command("docker network rm fcnet")  # Check if this should be part of cleanup
