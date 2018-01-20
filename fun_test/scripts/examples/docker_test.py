from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
import time
import pprint
import os


if __name__ == "__main__":
    os.environ["DOCKER_HOSTS_SPEC_FILE"] = "my-docker-hosts.json"
    topology_helper = TopologyHelper()
    deployed_assets = topology_helper.quick_docker_deploy(num_f1=1,
                                                          num_tg=1,
                                                          build_url="http://10.1.20.99/doc/jenkins/funos/latest/",
                                                          funos_command="'/funos-posix app=load_mods --dpc-server'")
    pprint.pprint(deployed_assets)
    time.sleep(15)

    f1_asset_0 = deployed_assets['f1_assets'][0]
    f1_external_ip = f1_asset_0["host_ip"]
    f1_external_dpcsh_proxy_port = f1_asset_0["dpcsh_proxy_port"]["external"]


    count = 100
    while count > 0:
        try:
            storage_controller = StorageController(target_ip=f1_external_ip, target_port=f1_external_dpcsh_proxy_port)
            storage_controller.command("peek /stats")
            break
        except:
            time.sleep(5)




    topology_helper.quick_docker_deploy(cleanup=True)


