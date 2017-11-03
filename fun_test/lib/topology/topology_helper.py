from lib.system.fun_test import fun_test, FunTestLibException
from asset.asset_manager import *
import json
from topology import ExpandedTopology
from dut import Dut

class TopologyHelper:
    def __init__(self, spec):
        self.spec = spec

    def get_resource_requirements(self):
        pass

    @fun_test.safe
    def get_expanded_topology(self):
        spec = self.spec

        expanded_topology = ExpandedTopology()
        fun_test.simple_assert("dut_info" in spec, "dut_info in spec")
        duts = spec["dut_info"]
        for dut_index, dut_info in duts.items():
            dut_type = dut_info["type"]
            simulation_start_mode = Dut.SIMULATION_START_MODE_NORMAL
            if "simulation_start_mode" in dut_info:
                simulation_start_mode = dut_info["simulation_start_mode"]
            dut_obj = Dut(type=dut_type, index=dut_index, simulation_start_mode=simulation_start_mode)
            interfaces = dut_info["interface_info"]
            for interface_index, interface_info in interfaces.items():
                dut_interface_obj = dut_obj.add_interface(index=interface_index, type=interface_info['type'])
                if "hosts" in interface_info:
                    dut_interface_obj.add_hosts(num_hosts=interface_info["hosts"])
                elif 'vms' in interface_info:
                    if not 'type' in interface_info:
                        raise FunTestLibException("We must define an interface type")
                    if dut_interface_obj.type == Dut.DutInterface.INTERFACE_TYPE_PCIE:
                        dut_interface_obj.add_qemu_colocated_hypervisor(num_vms=interface_info["vms"])
                    elif dut_interface_obj.type == Dut.DutInterface.INTERFACE_TYPE_ETHERNET:
                        dut_interface_obj.add_hypervisor(num_vms=interface_info["vms"])
                elif 'ssds' in interface_info:
                    dut_interface_obj.add_drives_to_interface(num_ssds=interface_info["ssds"])
            expanded_topology.duts[dut_index] = dut_obj

        return expanded_topology


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

                fun_test.debug("Setup peers on the interfaces")

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
        else:
            pass  # Networking style, where hosts can be separate containers

        fun_test.log("Completed allocating topology")
        ##### Let us print out the topology
        asset_manager.describe()

        d = topology.to_dict()
        topology_json_artifact = fun_test.create_test_case_artifact_file(post_fix_name="topology.json",
                                                                         contents=json.dumps(d))
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
            dut_instance = orchestrator_obj.launch_dut_instance(
                dpcsh_only=(dut_obj.simulation_start_mode == dut_obj.SIMULATION_START_MODE_DPCSH_ONLY),
            external_dpcsh_port=orchestrator_obj.dpcsh_port)
            fun_test.test_assert(dut_instance, "allocate_dut: Launch DUT instance")
            dut_obj.instance = dut_instance

    @fun_test.safe
    def allocate_hypervisor(self, hypervisor_end_point, orchestrator_obj=None):  # TODO
        if hypervisor_end_point.mode == hypervisor_end_point.MODE_SIMULATION:
            if not orchestrator_obj:
                orchestrator_obj = asset_manager.get_orchestrator(asset_manager.ORCHESTRATOR_TYPE_DOCKER_SIMULATION)
            fun_test.simple_assert(orchestrator_obj, "orchestrator")

            instances = []
            if hypervisor_end_point.num_vms:
                qemu_ssh_ports = orchestrator_obj.qemu_ssh_ports
                for i in range(hypervisor_end_point.num_vms):
                    internal_ssh_port = qemu_ssh_ports[i]["internal"]
                    external_ssh_port = qemu_ssh_ports[i]["external"]
                    instance = orchestrator_obj.launch_instance(instance_type=SimulationOrchestrator.INSTANCE_TYPE_QEMU,
                                                                external_ssh_port=external_ssh_port,
                                                                internal_ssh_port=internal_ssh_port)
                    fun_test.test_assert(instance, "allocate_hypervisor: Launched host instance {}".format(i))
                    instances.append(instance)
                    fun_test.counter += 1
            hypervisor_end_point.instances = instances
            # hypervisor_end_point.orchestrator = orchestrator_obj


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
                "simulation_start_mode": Dut.SIMULATION_START_MODE_NORMAL
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
                "simulation_start_mode": Dut.SIMULATION_START_MODE_DPCSH_ONLY
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
                "simulation_start_mode": Dut.SIMULATION_START_MODE_DPCSH_ONLY
            }

        }
    }

    TopologyHelper(spec=topology_dict).deploy()