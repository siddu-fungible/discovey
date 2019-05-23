import json
import dill

from asset.asset_manager import *
from fun_settings import REGRESSION_SERVICE_HOST
from lib.topology.dut import Dut, DutInterface
from lib.topology.switch import Switch
from lib.host.traffic_generator import Fio, LinuxHost
from lib.system.fun_test import FunTestLibException, FunTimer
from topology import ExpandedTopology
from end_points import EndPoint, FioEndPoint, LinuxHostEndPoint, SwitchEndPoint
from lib.system.utils import parse_file_to_json
from lib.host.linux import Linux
from lib.host.router import Router
from lib.fun.fs import ComE


class TopologyHelper:
    def __init__(self, expanded_topology=None, spec=None, spec_file=None):
        self.spec = spec
        if spec_file:
            self.spec = parse_file_to_json(file_name=spec_file)
        self.expanded_topology = expanded_topology

    def get_resource_requirements(self):
        pass

    def save(self, file_name):
        dill.dump(self.expanded_topology, open(file_name, "wb"))

    def load(self, file_name):
        return dill.load(open(file_name, "rb"))

    @fun_test.safe
    def get_expanded_topology(self):
        spec = self.spec

        if not self.spec:
            test_bed_name = fun_test.get_job_environment_variable(variable="test_bed_type")
            am = fun_test.get_asset_manager()
            spec = am.get_test_bed_spec(name=test_bed_name)

            fun_test.simple_assert(spec, "topology spec available for {}".format(test_bed_name))

        self.expanded_topology = ExpandedTopology()

        if "switch_info" in spec:
            switches = spec["switch_info"]
            for switch_name, switch_spec in switches.items():
                self.expanded_topology.switches[switch_name] = Switch(name=switch_name, spec=switch_spec)

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
                dut_obj = Dut(type=dut_type, index=dut_index, spec=dut_info, start_mode=start_mode)

                interfaces = {}  # TODO Actually SSD interfaces, will need to rename it
                if "interface_info" in dut_info:
                    interfaces = dut_info["interface_info"]
                elif "pcie_interface_info" in dut_info:
                    interfaces = dut_info["pcie_interface_info"]
                elif "ssd_interface_info" in dut_info:
                    interfaces = dut_info["ssd_interface_info"]

                fpg_interfaces = {}
                if "fpg_interface_info" in dut_info:
                    fpg_interfaces = dut_info["fpg_interface_info"]

                bond_interfaces = {}
                if "bond_interface_info" in dut_info:
                    bond_interfaces = dut_info["bond_interface_info"]

                # Assign endpoints on interfaces
                for interface_index, interface_info in interfaces.items():
                    interface_index = int(interface_index)
                    dut_interface_obj = dut_obj.add_interface(index=interface_index, type=interface_info['type'])
                    if "hosts" in interface_info:
                        dut_interface_obj.add_hosts(num_hosts=interface_info["hosts"], host_info=interface_info["host_info"])
                    elif 'vms' in interface_info:
                        if 'type' not in interface_info:
                            raise FunTestLibException("We must define an interface type")
                        if dut_interface_obj.type == DutInterface.INTERFACE_TYPE_PCIE:
                            vm_start_mode = None
                            if "vm_start_mode" in interface_info:
                                vm_start_mode = interface_info["vm_start_mode"]
                            dut_interface_obj.add_qemu_colocated_hypervisor(num_vms=interface_info["vms"],
                                                                            vm_start_mode=vm_start_mode,
                                                                            vm_host_os=interface_info.get("vm_host_os", None))
                        elif dut_interface_obj.type == DutInterface.INTERFACE_TYPE_ETHERNET:
                            dut_interface_obj.add_hypervisor(num_vms=interface_info["vms"])
                    elif 'ssds' in interface_info:
                        dut_interface_obj.add_drives_to_interface(num_ssds=interface_info["ssds"])
                    elif 'dual' in interface_info:
                        dut_interface_obj.set_dual_interface(interface_index=interface_info["dual"])
                self.expanded_topology.duts[dut_index] = dut_obj

                for f1_index, interfaces_info in fpg_interfaces.items():
                    for interface_index, interface_info in interfaces_info.items():
                        interface_index = int(interface_index)
                        dut_interface_obj = dut_obj.add_fpg_interface(index=interface_index,
                                                                      type=interface_info['type'],
                                                                      f1_index=int(f1_index))
                        if "hosts" in interface_info:
                            dut_interface_obj.add_hosts(num_hosts=interface_info["hosts"], host_info=interface_info["host_info"])
                        elif "dut_info" in interface_info:
                            this_dut_info = interface_info["dut_info"]
                            dut_index = this_dut_info["dut_index"]
                            fun_test.simple_assert("fpg_interface_info" in this_dut_info, "fpg_interface_info is expected")
                            peer_fpg_interface_info = this_dut_info["fpg_interface_info"]
                            dut_interface_obj.add_peer_dut_interface(dut_index=dut_index, peer_fpg_interface_info=peer_fpg_interface_info)
                        elif "switch_info" in interface_info:
                            switch_spec = interface_info["switch_info"]
                            dut_interface_obj.add_peer_switch_interface(switch_spec=switch_spec)

                for f1_index, interfaces_info in bond_interfaces.items():
                    for interface_index, interface_info in interfaces_info.items():
                        interface_index = int(interface_index)
                        dut_obj.add_bond_interface(index=interface_index,
                                                   type=interface_info['type'],
                                                   f1_index=int(f1_index),
                                                   fpg_slaves=interface_info["fpg_slaves"],
                                                   ip=interface_info["ip"])

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
        if not self.expanded_topology:
            self.expanded_topology = self.get_expanded_topology()
        fun_test.test_assert(self.allocate_topology(topology=self.expanded_topology), "Allocate topology")
        if not fun_test.is_simulation():
            fun_test.test_assert(self.validate_topology(), "Validate topology")
        return self.expanded_topology


    @fun_test.safe
    def set_dut_parameters(self, dut_index, **kwargs):
        if not self.expanded_topology:
            self.expanded_topology = self.get_expanded_topology()
            fun_test.simple_assert(self.expanded_topology, "Expanded Topology")
        dut = self.expanded_topology.get_dut(index=dut_index)
        fun_test.simple_assert(dut, "Dut index: {}".format(dut_index))
        for key, value in kwargs.iteritems():
            dut.spec[key] = value
        pass

    @fun_test.safe
    def validate_topology(self):
        topology = self.expanded_topology
        duts = topology.duts

        for dut_index, dut_obj in duts.items():
            fun_test.debug("Validating DUT readiness {}".format(dut_index))
            fun_test.test_assert(dut_obj.get_instance().is_ready(), "DUT: {} ready".format(dut_index))

            for interface_index, interface_info in dut_obj.interfaces.items():
                fun_test.debug("Validating peer on DUT interface {}".format(interface_index))
                peer_info = interface_info.peer_info
                if peer_info:
                    if peer_info.type == peer_info.END_POINT_TYPE_BARE_METAL:
                        host_instance = peer_info.get_host_instance()
                        ipmi_details = None
                        if host_instance.extra_attributes:
                            if "ipmi_info" in host_instance.extra_attributes:
                                ipmi_details = host_instance.extra_attributes["ipmi_info"]
                        instance_ready = host_instance.ensure_host_is_up(max_wait_time=240, ipmi_details=ipmi_details)
                        fun_test.test_assert(instance_ready, "Instance: {} ready".format(str(host_instance)))
                        host_instance.lspci(grep_filter="1dad")
        return True

    @fun_test.safe
    def allocate_topology(self, topology):

        if True:  # Storage style where each container has F1 and Host in it


            duts = topology.duts

            # Determine the number of storage containers you need
            # Today we need only one container

            # Fetch storage container orchestrator

            for dut_index, dut_obj in duts.items():
                fun_test.debug("Setting up DUT {}".format(dut_index))

                orchestrator = asset_manager.get_orchestrator(is_simulation=fun_test.is_simulation(), dut_index=dut_index)
                topology.add_active_orchestrator(orchestrator)
                fun_test.simple_assert(orchestrator, "Topology retrieved container orchestrator")

                fun_test.debug("Allocating the DUT")
                self.allocate_dut(dut_index=dut_index, dut_obj=dut_obj, orchestrator_obj=orchestrator)

                fun_test.debug("Setting up peers on the interfaces")

                for interface_index, interface_info in dut_obj.interfaces.items():
                    fun_test.debug("Setting up DUT interface {}".format(interface_index))
                    peer_info = interface_info.peer_info
                    # fun_test.simple_assert(peer_info, "Peer info")
                    if peer_info:

                        if peer_info.type == peer_info.END_POINT_TYPE_BARE_METAL:
                            instance = self.allocate_bare_metal(bare_metal_end_point=peer_info,
                                                                orchestrator_obj=orchestrator)
                            fun_test.simple_assert(instance, "Bare-metal instance")

                            if interface_info.type == DutInterface.INTERFACE_TYPE_PCIE:
                                fun_test.test_assert(instance.reboot(non_blocking=True), "Host instance: {} rebooted issued".format(str(instance)))

                        elif peer_info.type == peer_info.END_POINT_TYPE_HYPERVISOR:
                            self.allocate_hypervisor(hypervisor_end_point=peer_info,
                                                     orchestrator_obj=orchestrator)
                        elif peer_info.type == peer_info.END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED:
                            self.allocate_hypervisor(hypervisor_end_point=peer_info,
                                                     orchestrator_obj=orchestrator)

            for dut_index, dut_obj in duts.items():
                for f1_index, interface_info in dut_obj.fpg_interfaces.iteritems():
                    for interface_index, interface_obj in interface_info.items():
                        fun_test.debug("Setting up DUT F1: {} FPG interface {}".format(f1_index, interface_index))
                        peer_info = interface_obj.peer_info
                        # fun_test.simple_assert(peer_info, "Peer info")
                        if peer_info:

                            if peer_info.type == peer_info.END_POINT_TYPE_BARE_METAL:
                                instance = self.allocate_bare_metal(bare_metal_end_point=peer_info,
                                                                    orchestrator_obj=orchestrator)
                                fun_test.simple_assert(instance, "Bare-metal instance")

                            elif peer_info.type == peer_info.END_POINT_TYPE_HYPERVISOR:
                                self.allocate_hypervisor(hypervisor_end_point=peer_info,
                                                         orchestrator_obj=orchestrator)

                            elif peer_info.type == peer_info.END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED:
                                self.allocate_hypervisor(hypervisor_end_point=peer_info,
                                                         orchestrator_obj=orchestrator)
                            elif peer_info.type == peer_info.END_POINT_TYPE_DUT:
                                peer_dut_end_point = peer_info
                                peer_dut_instance = self.expanded_topology.get_dut_instance(peer_dut_end_point.dut_index)  # Should be changed to allocate_dut
                                peer_info.set_instance(peer_dut_instance)

                            elif peer_info.type == peer_info.END_POINT_TYPE_SWITCH:
                                peer_instance = self.expanded_topology.get_switch_instance(peer_info.name)
                                peer_info.set_instance(peer_instance)

            for dut_index, dut_obj in duts.items():
                for f1_index, interface_info in dut_obj.bond_interfaces.iteritems():
                    for interface_index, interface_obj in interface_info.items():
                        pass #Optionally work on peer endpoint

            tgs = topology.tgs

            for tg_index, tg in tgs.items():
                fun_test.debug("Setting up Tg {}".format(str(tg)))
                if tg.type in [EndPoint.END_POINT_TYPE_FIO, EndPoint.END_POINT_TYPE_LINUX_HOST]:
                    self.allocate_traffic_generator(index=tg_index, end_point=tg)
        else:
            pass  # Networking style,

        fun_test.log("Completed allocating topology")
        ##### Let us print out the topology
        asset_manager.describe()  # TODO Just for debugging

        d = topology.to_dict()
        topology_json_artifact = fun_test.create_test_case_artifact_file(post_fix_name="topology.json",
                                                                         contents=json.dumps(d, indent=4))
        fun_test.set_topology_json_filename(filename=topology_json_artifact)
        return True  # TODO

    @fun_test.safe
    def allocate_bare_metal(self, bare_metal_end_point, orchestrator_obj=None):
        host_info = bare_metal_end_point.host_info
        host_spec = fun_test.get_asset_manager().get_host_spec(name=host_info["name"])
        fun_test.simple_assert(host_spec, "Retrieve host-spec for {}".format(host_info["name"]))
        linux_obj = Linux(**host_spec)
        bare_metal_end_point.add_instance(linux_obj)
        return linux_obj

    @fun_test.safe
    def allocate_dut(self, dut_index, dut_obj, orchestrator_obj=None):
        fun_test.simple_assert(orchestrator_obj, "orchestrator")
        dut_instance = orchestrator_obj.launch_dut_instance(dut_index=dut_index, dut_obj=dut_obj)
        fun_test.test_assert(dut_instance, "allocate_dut: Launch DUT instance")
        dut_obj.set_instance(dut_instance)

    @fun_test.safe
    def allocate_switch(self, switch_name, switch_obj):
        switch_instance = None #TODO: Not implemented Router(host_ip="127.0.0.1", ssh_username="fun", ssh_password="123")
        switch_obj.set_instance(switch_instance)

    @fun_test.safe
    def allocate_hypervisor(self, hypervisor_end_point, orchestrator_obj=None):  # TODO
        if hypervisor_end_point.mode == hypervisor_end_point.MODE_SIMULATION:
            # if not orchestrator_obj:
            #    orchestrator_obj = asset_manager.get_orchestrator(asset_manager.ORCHESTRATOR_TYPE_DOCKER_SIMULATION)
            fun_test.simple_assert(orchestrator_obj, "orchestrator")

            if hypervisor_end_point.num_vms:
                host_ssh_ports = orchestrator_obj.get_host_ssh_ports()
                for host_index in range(hypervisor_end_point.num_vms):
                    internal_ssh_port = host_ssh_ports[host_index]["internal"]
                    external_ssh_port = host_ssh_ports[host_index]["external"]
                    vm_host_os = getattr(hypervisor_end_point, "vm_host_os", None)

                    instance = orchestrator_obj.launch_host_instance(
                        external_ssh_port=external_ssh_port,
                        internal_ssh_port=internal_ssh_port,
                        vm_host_os=vm_host_os,
                    )
                    fun_test.test_assert(instance, "allocate_hypervisor: Launched host instance {}".format(host_index))
                    hypervisor_end_point.add_instance(instance=instance)

    @fun_test.safe
    def allocate_traffic_generator(self, index, end_point):
        orchestrator_obj = asset_manager.get_orchestrator(is_simulation=fun_test.is_simulation(), type=OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST)
        self.expanded_topology.add_active_orchestrator(orchestrator_obj)
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
        return self.expanded_topology.cleanup()

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

        docker_host = fun_test.get_asset_manager().get_any_docker_host()
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
                fun_test.simple_assert(docker_host.wait_for_handoff(container_name=container_name,
                                                                    handoff_string="Idling"), message="Container handoff")

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
