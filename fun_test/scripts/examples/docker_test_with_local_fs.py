from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.host.linux import Linux
import time
import pprint
import os

# This example illustrates a case where we could mount a directory found on the docker host (/root/my-build)
# onto the container's /my-build directory
# /root/my-build should typically contain the funos-posix executable and dpcsh
# This example also shows how to use the Linux class to do commands like "ls -l /"

if __name__ == "__main__":
    os.environ["DOCKER_HOSTS_SPEC_FILE"] = "my_docker_hosts.json"
    num_f1 = 2
    topology_helper = TopologyHelper()
    host_directory = "/root/my-build"
    container_mount_directory = "/my-build"

    # Ensure funos-posix and dpcsh are found in host_directory
    paths_to_validate = ["{}/funos-posix".format(host_directory), "{}/dpcsh".format(host_directory)]
    for path_to_validate in paths_to_validate:
        if not os.path.exists(path_to_validate):
            raise Exception ("{} does not exist".format(path_to_validate))

    deployed_assets = topology_helper.quick_docker_deploy(num_f1=num_f1,
                                                          num_tg=1,
                                                          funos_command="'{0}/funos-posix app=mdt_test nvfile=nvfile; {0}/funos-posix app=load_mods --dpc-server'".format(container_mount_directory), 
                                                          pre_dpcsh_sleep=120, # Required to ensure dpcsh proxy is started only after load_mods above completes
                                                          dpcsh_directory=container_mount_directory,
                                                          mount="{}:{}".format(host_directory, container_mount_directory))
    pprint.pprint(deployed_assets)
    time.sleep(15)

    for index in range(num_f1):
        f1_asset = deployed_assets['f1_assets'][index]
        f1_external_ip = f1_asset["host_ip"]
        f1_external_dpcsh_proxy_port = f1_asset["dpcsh_proxy_port"]["external"]
        f1_ssh_username = f1_asset["mgmt_ssh_username"]
        f1_ssh_password = f1_asset["mgmt_ssh_password"]
        f1_external_ssh_port = f1_asset["mgmt_ssh_port"]

        count = 100
        while count > 0:
            try:
                storage_controller = StorageController(target_ip=f1_external_ip, target_port=f1_external_dpcsh_proxy_port)
                storage_controller.command("peek stats", expected_command_duration=4)
                linux_obj = Linux(host_ip=f1_external_ip, ssh_username=f1_ssh_username, ssh_password=f1_ssh_password, ssh_port=f1_external_ssh_port)
                linux_obj.command("ls -l /")
                break
            except:
                time.sleep(5)
                count -= 1

    print("Cleaning up")
    topology_helper.quick_docker_deploy(cleanup=True)
    
