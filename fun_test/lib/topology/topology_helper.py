import json
import dill

from asset.asset_manager import *
from dut import Dut, DutInterface
from lib.host.traffic_generator import Fio, LinuxHost
from lib.system.fun_test import FunTestLibException
from topology import ExpandedTopology
from end_points import EndPoint, FioEndPoint, LinuxHostEndPoint
from lib.system.utils import parse_file_to_json

class TopologyHelper:
    def __init__(self, spec=None, spec_file=None):
        self.spec = spec
        if spec_file:
            self.spec = parse_file_to_json(file_name=spec_file)
        self.expanded_topology = None

    def get_resource_requirements(self):
        pass

    def save(self, file_name):
        dill.dump(self.expanded_topology, open(file_name, "wb"))

    def load(self, file_name):
        return dill.load(open(file_name, "rb"))

    @fun_test.safe
    def get_expanded_topology(self):
        spec = self.spec

        self.expanded_topology = ExpandedTopology()
        # fun_test.simple_assert("dut_info" in spec, "dut_info in spec")  #TODO
        if "dut_repeat" in spec:
            repeat_count = spec["dut_repeat"]["count"]
            spec["dut_info"] = {}
            spec_dut_info = spec["dut_info"]
            repeat_dut_info = spec["dut_repeat"]["info"]
            for index in range(repeat_count):
                spec_dut_info[index] = repeat_dut_info

        if "dut_info" in spec:
            duts = spec["dut_info"]
            for dut_index, dut_info in duts.items():
                dut_index = int(dut_index)
                dut_type = dut_info["type"]
                start_mode = F1.START_MODE_NORMAL
                if "start_mode" in dut_info:
                    start_mode = dut_info["start_mode"]

                # Create DUT object
                dut_obj = Dut(type=dut_type, index=dut_index, spec=dut_info)
                interfaces = dut_info["interface_info"]

                # Assign endpoints on interfaces
                for interface_index, interface_info in interfaces.items():
                    interface_index = int(interface_index)
                    dut_interface_obj = dut_obj.add_interface(index=interface_index, type=interface_info['type'])
                    if "hosts" in interface_info:
                        dut_interface_obj.add_hosts(num_hosts=interface_info["hosts"])
                    elif 'vms' in interface_info:
                        if not 'type' in interface_info:
                            raise FunTestLibException("We must define an interface type")
                        if dut_interface_obj.type == DutInterface.INTERFACE_TYPE_PCIE:
                            dut_interface_obj.add_qemu_colocated_hypervisor(num_vms=interface_info["vms"])
                        elif dut_interface_obj.type == DutInterface.INTERFACE_TYPE_ETHERNET:
                            dut_interface_obj.add_hypervisor(num_vms=interface_info["vms"])
                    elif 'ssds' in interface_info:
                        dut_interface_obj.add_drives_to_interface(num_ssds=interface_info["ssds"])
                self.expanded_topology.duts[dut_index] = dut_obj

        if "tg_info" in spec:
            tgs = spec["tg_info"]
            for tg_index, tg_info in tgs.items():
                tg_index = int(tg_index)
                tg_type = tg_info["type"]
                if tg_type == Fio.TRAFFIC_GENERATOR_TYPE_FIO:
                    self.expanded_topology.tgs[tg_index] = FioEndPoint()
                if tg_type == LinuxHost.TRAFFIC_GENERATOR_TYPE_LINUX_HOST:
                    self.expanded_topology.tgs[tg_index] = LinuxHostEndPoint()

        fun_test.debug("got expanded topology")
        return self.expanded_topology


    @fun_test.safe
    def deploy(self):
        expanded_topology = self.get_expanded_topology()
        fun_test.test_assert(self.allocate_topology(topology=expanded_topology), "Allocate Topology")
        return expanded_topology

    @fun_test.safe
    def allocate_topology(self, topology):

        if True: # Storage style where each container has F1 and Host in it

            duts = topology.duts

            # Determine the number of storage containers you need
            # Today we need only one container

            # Fetch storage container orchestrator

            for dut_index, dut_obj in duts.items():
                dut_type = dut_obj.type
                fun_test.debug("Setting up DUT {}".format(dut_index))

                storage_container_orchestrator = asset_manager.get_orchestrator(index=dut_index)
                fun_test.simple_assert(storage_container_orchestrator, "Topology retrieved container orchestrator")

                fun_test.debug("Allocating the DUT")
                self.allocate_dut(dut_obj=dut_obj, orchestrator_obj=storage_container_orchestrator)

                fun_test.debug("Setting up peers on the interfaces")

                for interface_index, interface_info in dut_obj.interfaces.items():
                    fun_test.debug("Setting up DUT interface {}".format(interface_index))
                    peer_info = interface_info.peer_info
                    # fun_test.simple_assert(peer_info, "Peer info")
                    if peer_info:

                        if peer_info.type == peer_info.END_POINT_TYPE_BARE_METAL:
                            self.allocate_bare_metal(bare_metal_end_point=peer_info,
                                                     orchestrator_obj=storage_container_orchestrator)
                        elif peer_info.type == peer_info.END_POINT_TYPE_HYPERVISOR:
                            self.allocate_hypervisor(hypervisor_end_point=peer_info,
                                                     orchestrator_obj=storage_container_orchestrator)
                        elif peer_info.type == peer_info.END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED:
                            self.allocate_hypervisor(hypervisor_end_point=peer_info,
                                                     orchestrator_obj=storage_container_orchestrator)

            tgs = topology.tgs

            for tg_index, tg in tgs.items():
                fun_test.debug("Setting up Tg {}".format(str(tg)))
                if (tg.type == EndPoint.END_POINT_TYPE_FIO or tg.type == EndPoint.END_POINT_TYPE_LINUX_HOST):
                    self.allocate_traffic_generator(index=tg_index, end_point=tg)
        else:
            pass  # Networking style,

        fun_test.log("Completed allocating topology")
        ##### Let us print out the topology
        asset_manager.describe()  #TODO Just for debugging

        d = topology.to_dict()
        topology_json_artifact = fun_test.create_test_case_artifact_file(post_fix_name="topology.json",
                                                                         contents=json.dumps(d, indent=4))
        fun_test.set_topology_json_filename(filename=topology_json_artifact)
        return True  # TODO


    @fun_test.safe
    def allocate_bare_metal(self, bare_metal_end_point, orchestrator_obj=None):
        raise Exception("Not Implemented")

    @fun_test.safe
    def allocate_dut(self, dut_obj, orchestrator_obj=None):
        if dut_obj.mode == dut_obj.MODE_SIMULATION:
            if not orchestrator_obj:
                orchestrator_obj = asset_manager.get_orchestrator(asset_manager.ORCHESTRATOR_TYPE_DOCKER_SIMULATION)
            fun_test.simple_assert(orchestrator_obj, "orchestrator")
            dut_instance = orchestrator_obj.launch_dut_instance(spec=dut_obj.spec,
                                                                external_dpcsh_port=orchestrator_obj.dpcsh_port)
            fun_test.test_assert(dut_instance, "allocate_dut: Launch DUT instance")
            dut_obj.set_instance(dut_instance)

    @fun_test.safe
    def allocate_hypervisor(self, hypervisor_end_point, orchestrator_obj=None):  # TODO
        if hypervisor_end_point.mode == hypervisor_end_point.MODE_SIMULATION:
            # if not orchestrator_obj:
            #    orchestrator_obj = asset_manager.get_orchestrator(asset_manager.ORCHESTRATOR_TYPE_DOCKER_SIMULATION)
            fun_test.simple_assert(orchestrator_obj, "orchestrator")

            if hypervisor_end_point.num_vms:
                qemu_ssh_ports = orchestrator_obj.qemu_ssh_ports
                for i in range(hypervisor_end_point.num_vms):
                    internal_ssh_port = qemu_ssh_ports[i]["internal"]
                    external_ssh_port = qemu_ssh_ports[i]["external"]
                    instance = orchestrator_obj.launch_host_instance(instance_type=SimulationOrchestrator.INSTANCE_TYPE_QEMU,
                                                                external_ssh_port=external_ssh_port,
                                                                internal_ssh_port=internal_ssh_port)
                    fun_test.test_assert(instance, "allocate_hypervisor: Launched host instance {}".format(i))
                    hypervisor_end_point.add_instance(instance=instance)
                    fun_test.counter += 1

    @fun_test.safe
    def allocate_traffic_generator(self, index, end_point):
        orchestrator_obj = asset_manager.get_orchestrator(OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST)
        if end_point.end_point_type == EndPoint.END_POINT_TYPE_FIO:
            instance = orchestrator_obj.launch_fio_instance(index)
            fun_test.test_assert(instance, "allocate_traffic_generator: Launched fio instance")
            end_point.set_instance(instance=instance)
        if end_point.end_point_type == EndPoint.END_POINT_TYPE_LINUX_HOST:
            instance = orchestrator_obj.launch_linux_instance(index)
            fun_test.test_assert(instance, "allocate_traffic_generator: Launched Linux instance")
            end_point.set_instance(instance=instance)

    @fun_test.safe
    def cleanup(self):
        asset_manager.cleanup()


    def quick_docker_deploy(self,
                            num_f1=0,
                            build_url=None,
                            f1_base_name="quick_deploy_f1",
                            num_tg=0,
                            tg_base_name="quick_deploy_tg",
                            cleanup=False,
                            funos_command=None,
                            pre_dpcsh_sleep=None,
                            dpcsh_directory=None,
                            mount=None):

        docker_host = AssetManager().get_any_docker_host()
        docker_host.connect()
        if not cleanup:
            self.f1_assets = []
            self.tg_assets = []

            for index in range(num_f1):
                container_name = "{}_{}".format(f1_base_name, index)
                ssh_internal_ports = [22]
                qemu_internal_ports = [50001, 50002, 50004]
                dpcsh_internal_ports = [5000]

                container_asset = docker_host.setup_storage_container(container_name,
                                                                       build_url,
                                                                       ssh_internal_ports,
                                                                       qemu_internal_ports,
                                                                       dpcsh_internal_ports,
                                                                       funos_command=funos_command,
                                                                       dpc_server=True, pre_dpcsh_sleep=pre_dpcsh_sleep,
                                                                       dpcsh_directory=dpcsh_directory,
                                                                       mounts=[mount])
                docker_host.describe_storage_container(container_asset)
                container_asset["container_name"] = container_asset["name"]
                container_asset["qemu_ports"] = container_asset["pool1_ports"]
                container_asset["dpcsh_proxy_port"] = container_asset["pool2_ports"][0]
                del container_asset["name"]
                del container_asset["pool1_ports"]
                del container_asset["pool2_ports"]
                self.f1_assets.append(container_asset)

            for index in range(num_tg):
                container_name = "{}_{}".format(tg_base_name, index)
                ssh_internal_ports = [22]
                container_asset = docker_host.setup_fio_container(container_name, ssh_internal_ports)
                container_asset["container_name"] = container_asset["name"]
                del container_asset["name"]
                del container_asset["pool1_ports"]
                del container_asset["pool2_ports"]
                self.tg_assets.append(container_asset)
        else:
            for asset in self.f1_assets + self.tg_assets:
                docker_host.destroy_container(asset["container_name"])

        return {"f1_assets": self.f1_assets, "tg_assets": self.tg_assets}


if __name__ == "__main__":
    topology_dict = {
        "name": "Basic Storage",
        "dut_info": {
            0: {
                "mode": Dut.MODE_SIMULATION,
                "type": Dut.DUT_TYPE_FSU,
                "interface_info": {
                    1: {
                        "hosts": 1
                    }
                },
                "start_mode": F1.START_MODE_NORMAL
            }

        }
    }

    topology_dict = {
        "name": "Basic Storage",
        "dut_info": {
            0: {
                "mode": Dut.MODE_SIMULATION,
                "type": Dut.DUT_TYPE_FSU,
                "interface_info": {
                    1: {
                        "hosts": 0
                    }
                },
                "start_mode": F1.START_MODE_DPCSH_ONLY
            }

        }
    }

    topology_dict = {
        "name": "Basic Storage",
        "dut_info": {
            0: {
                "mode": Dut.MODE_SIMULATION,
                "type": Dut.DUT_TYPE_FSU,
                "interface_info": {
                    1: {
                        "vms": 1
                    }
                },
                "start_mode": F1.START_MODE_DPCSH_ONLY
            }

        }
    }

    TopologyHelper(spec=topology_dict).deploy()
