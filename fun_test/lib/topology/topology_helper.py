from lib.system.fun_test import fun_test, FunTestLibException
from lib.topology.posix_qemu_topology import PosixQemuTopology
from lib.topology.posix_docker_topology import PosixDockerTopology
from asset.asset_manager import *
from lib.system.utils import ToDictMixin
import json

class ExpandedTopology(ToDictMixin):
    TO_DICT_VARS = ["duts"]
    def __init__(self):
        self.duts = {}

    def get_dut(self, index):
        result = None
        if index in self.duts:
            result = self.duts[index]
        return result

    def get_dut_instance(self, index):
        result = None
        dut = self.get_dut(index=index)
        if dut:
            result = dut.get_instance()
        return result

    def get_host_instance(self, dut_index, interface_index, host_index):
        dut = self.get_dut(index=dut_index)
        return dut.get_host_on_interface(interface_index=interface_index, host_index=host_index)

class EndPoint(object, ToDictMixin):
    end_point_type = "Unknown end-point type"
    END_POINT_TYPE_BARE_METAL = "END_POINT_TYPE_BARE_METAL"
    END_POINT_TYPE_VM = "END_POINT_TYPE_VM"
    END_POINT_TYPE_SSD = "END_POINT_TYPE_SSD"
    END_POINT_TYPE_HYPERVISOR = "END_POINT_TYPE_HYPERVISOR"
    END_POINT_TYPE_QEMU_HYPERVISOR = "END_POINT_TYPE_QEMU_HYPERVISOR"
    MODE_SIMULATION = "MODE_SIMULATION"

    TO_DICT_VARS = ["mode", "type", "instance"]
    def __init__(self):
        self.type = self.end_point_type
        self.instance = None
        self.mode = self.MODE_SIMULATION

    def __repr__(self):
        return str(self.type)

    def get_instance(self):
        return self.instance

class VmEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_VM

    def __init__(self, centos7=0, ubuntu14=0):
        super(VmEndPoint, self).__init__()
        self.centos7 = centos7
        self.ubuntu14 = ubuntu14

        if (not centos7) and (not ubuntu14):
            self.centos7 = 1


class BareMetalEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_BARE_METAL

    def __init__(self):
        super(BareMetalEndPoint, self).__init__()
        self.mode = self.MODE_SIMULATION


class HypervisorEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_HYPERVISOR

    def __init__(self, num_vms=None):
        super(HypervisorEndPoint, self).__init__()
        self.num_vms = num_vms
        self.mode = self.MODE_SIMULATION

class QemuHypervisorEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_QEMU_HYPERVISOR

    def __init__(self, num_vms=None):
        super(QemuHypervisorEndPoint, self).__init__()
        self.num_vms = num_vms
        self.mode = self.MODE_SIMULATION
        self.TO_DICT_VARS.extend(["mode", "num_vms", "end_point_type", "instances", "orchestrator"])

    def get_host_instance(self, host_index):
        return self.instances[host_index]

class SsdEndPoint(EndPoint):
    end_point_type = EndPoint.END_POINT_TYPE_SSD


class Dut(ToDictMixin):
    DUT_TYPE_FSU = "DUT_TYPE_FSU"
    DUT_TYPE_FM8 = "DUT_TYPE_FM8"

    SIMULATION_START_MODE_NORMAL = "SIMULATION_START_MODE_NORMAL"
    SIMULATION_START_MODE_DPCSH_ONLY = "SIMULATION_START_MODE_DPCSH_ONLY"

    MODE_SIMULATION = "MODE_SIMULATION"
    MODE_EMULATION = "MODE_EMULATION"
    MODE_REAL = "MODE_REAL"

    TO_DICT_VARS = ["type", "index", "interfaces", "simulation_start_mode", "instance"]

    class DutInterface(ToDictMixin):
        INTERFACE_TYPE_PCIE = "INTERFACE_TYPE_PCIE"
        INTERFACE_TYPE_ETHERNET = "INTERFACE_TYPE_ETHERNET"

        TO_DICT_VARS = ["index", "type", "peer_info"]
        def __init__(self, index):
            self.index = index  # interface index
            self.peer_info = None
            self.type = self.INTERFACE_TYPE_PCIE  # pcie, ethernet

        def get_peer_instance(self):
            return self.peer_info

    def __init__(self, type, index, mode=MODE_SIMULATION, simulation_start_mode=SIMULATION_START_MODE_NORMAL):
        self.type = type
        self.index = index
        self.interfaces = {}
        self.simulation_start_mode = simulation_start_mode
        self.mode = mode
        self.instance = None

    def __repr__(self):
        return str(self.index) + " : " + str(self.type)

    def add_hosts_to_interface(self, interface_index, num_hosts=0):
        dut_interface_obj = self.DutInterface(index=interface_index)
        self.interfaces[interface_index] = dut_interface_obj
        # fun_test.simple_assert(num_hosts or num_vms, "num hosts or num vms")

        if num_hosts:
            fun_test.debug("User intended baremetal for Interface: {}".format(interface_index))
            dut_interface_obj.peer_info = BareMetalEndPoint()

    def add_qemu_hypervisor_to_interface(self,
                                         interface_index,
                                         num_vms=0,
                                        ):
        dut_interface_obj = self.DutInterface(index=interface_index)
        self.interfaces[interface_index] = dut_interface_obj
        if num_vms:
            dut_interface_obj.peer_info = QemuHypervisorEndPoint(num_vms=num_vms)
            fun_test.debug("User intended hypervisor for Interface: {}".format(interface_index))

    def add_hypervisor_to_interface(self,
                                    interface_index,
                                    num_vms=0,
                                    interface_type=DutInterface.INTERFACE_TYPE_PCIE):
        dut_interface_obj = self.DutInterface(index=interface_index)
        self.interfaces[interface_index] = dut_interface_obj
        if num_vms:
            if interface_type == Dut.DutInterface.INTERFACE_TYPE_ETHERNET:
                dut_interface_obj.peer_info = HypervisorEndPoint(num_vms=num_vms)
                fun_test.debug("User intended hypervisor for Interface: {}".format(interface_index))

    def add_drives_to_interface(self, interface_index, num_ssds=0):
        dut_interface_obj = self.DutInterface(index=interface_index)
        self.interfaces[interface_index] = dut_interface_obj
        fun_test.simple_assert(num_ssds, "Num ssds")

    def start(self):
        pass

    def get_instance(self):
        return self.instance

    def get_interface(self, interface_index):
        return self.interfaces[interface_index]

    def get_host_on_interface(self, interface_index, host_index):
        return self.interfaces[interface_index].get_peer_instance().get_host_instance(host_index=host_index)

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
                if "hosts" in interface_info:
                    dut_obj.add_hosts_to_interface(interface_index=interface_index, num_hosts=interface_info["hosts"])
                elif 'vms' in interface_info:
                    if not 'type' in interface_info:
                        raise FunTestLibException("We must define an interface type")
                    if interface_info["type"] == Dut.DutInterface.INTERFACE_TYPE_PCIE:
                        dut_obj.add_qemu_hypervisor_to_interface(interface_index=interface_index,
                                                                 num_vms=interface_info["vms"])
                    elif interface_info['type'] == Dut.DutInterface.INTERFACE_TYPE_ETHERNET:
                        dut_obj.add_hypervisor_to_interface(interface_index=interface_index,
                                                                num_vms=interface_info["vms"])


                elif 'ssds' in interface_info:
                    dut_obj.add_drives_to_interface(interface_index=interface_index, num_ssds=interface_info["ssds"])

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
                        elif peer_info.type == peer_info.END_POINT_TYPE_QEMU_HYPERVISOR:
                            self.allocate_qemu_hypervisor(hypervisor_end_point=peer_info,
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
        '''
        if bare_metal_end_point.mode == bare_metal_end_point.MODE_SIMULATION:
            qemu_ssh_ports = orchestrator_obj.qemu_ssh_ports
            if not orchestrator_obj:
                orchestrator_obj = asset_manager.get_orchestrator(asset_manager.ORCHESTRATOR_TYPE_DOCKER_SIMULATION)
            fun_test.simple_assert(orchestrator_obj, "orchestrator")
            for i in range(bare_metal_end_point.num_vms):

                internal_ssh_port = qemu_ssh_ports[i]["internal"]
                external_ssh_port = qemu_ssh_ports[i]["external"]
                instance = orchestrator_obj.launch_instance(SimulationOrchestrator.INSTANCE_TYPE_QEMU,
                                                            internal_ssh_port=internal_ssh_port,
                                                            external_ssh_port=external_ssh_port)
                fun_test.test_assert(instance, "allocate_bare_metal: Launched host instance")
            bare_metal_end_point.instance = instance
            bare_metal_end_point.orchestrator = orchestrator_obj
        '''


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
            dut_instance.orchestrator = orchestrator_obj

    @fun_test.safe
    def allocate_hypervisor(self, hypervisor_end_point, orchestrator_obj=None):  # TODO
        raise FunTestLibException("Not implemented")

    @fun_test.safe
    def allocate_qemu_hypervisor(self, hypervisor_end_point, orchestrator_obj=None):  # TODO
        if hypervisor_end_point.mode == hypervisor_end_point.MODE_SIMULATION:
            if not orchestrator_obj:
                orchestrator_obj = asset_manager.get_orchestrator(asset_manager.ORCHESTRATOR_TYPE_DOCKER_SIMULATION)
            fun_test.simple_assert(orchestrator_obj, "orchestrator")

            instances = []
            if hypervisor_end_point.num_vms:
                qemu_ssh_ports = orchestrator_obj.qemu_ssh_ports
                for i in range(hypervisor_end_point.num_vms):
                    # ssh_redir_port = orchestrator_obj.get_redir_port()
                    # orchestrator_obj.add_port_redir(port=ssh_redir_port, internal_ip=orchestrator_obj.internal_ip)
                    internal_ssh_port = qemu_ssh_ports[i]["internal"]
                    external_ssh_port = qemu_ssh_ports[i]["external"]
                    instance = orchestrator_obj.launch_instance(SimulationOrchestrator.INSTANCE_TYPE_QEMU,
                                                                external_ssh_port=external_ssh_port,
                                                                internal_ssh_port=internal_ssh_port)
                    fun_test.test_assert(instance, "allocate_hypervisor: Launched host instance {}".format(i))
                    instances.append(instance)
                    fun_test.counter += 1
            hypervisor_end_point.instances = instances
            hypervisor_end_point.orchestrator = orchestrator_obj


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