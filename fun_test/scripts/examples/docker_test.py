from lib.topology.topology_helper import TopologyHelper
import time
import pprint

if __name__ == "__main__":
    topology_helper = TopologyHelper()
    deployed_assets = topology_helper.quick_docker_deploy(num_f1=1, num_tg=1)
    pprint.pprint(deployed_assets)
    time.sleep(15)
    topology_helper.quick_docker_deploy(cleanup=True)


