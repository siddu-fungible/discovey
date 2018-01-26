from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.host.linux import Linux
import time
import pprint
import os
import pdb


if __name__ == "__main__":
    os.environ["DOCKER_HOSTS_SPEC_FILE"] = "my-docker-hosts.json"
    num_f1 = 2
    topology_helper = TopologyHelper()
    deployed_assets = topology_helper.quick_docker_deploy(num_f1=num_f1,
                                                          num_tg=1,
                                                          funos_command="'/my-build/funos-posix app=mdt_test nvfile=nvfile; /my-build/funos-posix app=load_mods --dpc-server'", 
                                                          pre_dpcsh_sleep=120,
                                                          dpcsh_directory="/my-build",
                                                          mount="/root/my-build:/my-build")
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
                linux_obj.command("ls /")
                break
            except:
                time.sleep(5)
                count -= 1

    pdb.set_trace()
    topology_helper.quick_docker_deploy(cleanup=True)


