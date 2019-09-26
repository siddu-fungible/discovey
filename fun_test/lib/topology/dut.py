from lib.system.fun_test import fun_test
from lib.fun.f1 import F1
from lib.system.utils import ToDictMixin
from lib.topology.end_points import BareMetalEndPoint, QemuColocatedHypervisorEndPoint, HypervisorEndPoint
from lib.topology.end_points import DutEndPoint, EndPoint, SwitchEndPoint


class DutInterface(object, ToDictMixin):
    INTERFACE_TYPE_PCIE = "INTERFACE_TYPE_PCIE"
    INTERFACE_TYPE_ETHERNET = "INTERFACE_TYPE_ETHERNET"
    INTERFACE_TYPE_ETHERNET_BOND = "INTERFACE_TYPE_ETHERNET_BOND"

    TO_DICT_VARS = ["index", "type", "peer_info"]

    def __init__(self, index, type, f1_index=0, **kwargs):
        self.index = index  # interface index
        self.peer_info = None
        self.type = type  # pcie, ethernet
        self.dual_interface_index = None
        self.f1_index = f1_index
        self.ip = None

    def get_peer_instance(self):
        return self.peer_info

    def add_hosts(self, num_hosts=0, host_info=None):
        # fun_test.simple_assert(num_hosts or num_vms, "num hosts or num vms")

        if num_hosts:
            fun_test.debug("User intended baremetal for Interface: {}".format(self.index))
            self.peer_info = BareMetalEndPoint(host_info=host_info)

    def add_peer_switch_interface(self, switch_spec):
        self.peer_info = SwitchEndPoint(name=switch_spec["name"], port=switch_spec["port"], spec=switch_spec)

    def add_peer_dut_interface(self, dut_index, peer_fpg_interface_info):  # Sometimes interfaces are just connected to another DUT
        self.peer_info = DutEndPoint(dut_index=dut_index, fpg_interface_info=peer_fpg_interface_info)

    def add_qemu_colocated_hypervisor(self, num_vms=0, vm_start_mode=None, vm_host_os=None):
        if num_vms:
            self.peer_info = QemuColocatedHypervisorEndPoint(num_vms=num_vms,
                                                             vm_start_mode=vm_start_mode,
                                                             vm_host_os=vm_host_os)
            fun_test.debug("User intended hypervisor for Interface: {}".format(self.index))

    def add_hypervisor(self, num_vms=0):
        if num_vms:
            if self.type == DutInterface.INTERFACE_TYPE_ETHERNET:
                self.peer_info = HypervisorEndPoint(num_vms=num_vms)
                fun_test.debug("User intended hypervisor for Interface: {}".format(self.index))

    def add_drives_to_interface(self, num_ssds=0):
        fun_test.simple_assert(num_ssds, "Num ssds")

    def set_dual_interface(self, interface_index):
        self.dual_interface_index = interface_index


class BondInterface(DutInterface):
    INTERFACE_TYPE_ETHERNET_BOND = "INTERFACE_TYPE_ETHERNET_BOND"

    def __init__(self, **kwargs):
        super(BondInterface, self).__init__(**kwargs)
        self.ip = kwargs.get("ip", None)
        self.fpg_slaves = kwargs.get("fpg_slaves", None)

class Dut(ToDictMixin):
    DUT_TYPE_FSU = "DUT_TYPE_FSU"
    DUT_TYPE_FM8 = "DUT_TYPE_FM8"

    POOL_MEMBER_TYPE_DEFAULT = "POOL_MEMBER_TYPE_DEFAULT"
    POOL_MEMBER_TYPE_WITH_SSDS = "POOL_MEMBER_TYPE_WITH_SSDS"
    POOL_MEMBER_TYPE_WITH_SERVERS = "POOL_MEMBER_TYPE_WITH_SERVERS"

    MODE_SIMULATION = "MODE_SIMULATION"
    MODE_EMULATION = "MODE_EMULATION"
    MODE_REAL = "MODE_REAL"

    TO_DICT_VARS = ["type", "index", "interfaces", "start_mode", "instance", "fpg_interfaces"]

    def __init__(self, type, index, mode=MODE_SIMULATION, spec=None, start_mode=None, name=None, pool_member_type=POOL_MEMBER_TYPE_DEFAULT):
        self.type = type
        self.index = index
        self.name = name
        self.interfaces = {}  # For PCIe interfaces
        self.fpg_interfaces = {0: {}, 1: {}}  # for each F1
        self.bond_interfaces = {0: {}, 1: {}}
        self.spec = spec
        self.mode = mode
        self.instance = None
        self.start_mode = start_mode
        self.pool_member_type = pool_member_type


    def __repr__(self):
        return str(self.index) + " : " + str(self.type) + " : " + self.name

    def get_pool_member_type(self):
        return self.pool_member_type

    def set_instance(self, instance):
        self.instance = instance

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_ssd_interfaces(self):
        return self.interfaces

    def get_pcie_interfaces(self):
        return self.interfaces

    def get_fpg_interfaces(self, f1_index=0):
        return self.fpg_interfaces[f1_index]

    def get_bond_interfaces(self, f1_index=0):
        return self.bond_interfaces[f1_index]

    def add_interface(self, index, type):
        dut_interface_obj = DutInterface(index=index, type=type)
        self.interfaces[index] = dut_interface_obj
        return dut_interface_obj

    def add_fpg_interface(self, index, type, f1_index):
        dut_interface_obj = DutInterface(index=index, type=type, f1_index=f1_index)
        self.fpg_interfaces[f1_index][index] = dut_interface_obj
        return dut_interface_obj

    def add_bond_interface(self, index, type, f1_index, fpg_slaves, ip):
        dut_interface_obj = BondInterface(index=index, type=type, f1_index=f1_index, fpg_slaves=fpg_slaves, ip=ip)
        self.bond_interfaces[f1_index][index] = dut_interface_obj
        return dut_interface_obj

    def get_spec(self):
        return self.spec

    def set_start_mode(self, mode):
        self.start_mode = mode

    def start(self):
        pass

    def get_instance(self):
        return self.instance

    def get_interface(self, interface_index):
        return self.interfaces.get(interface_index, None)

    def get_fpg_interface(self, interface_index, f1_index=0):
        return self.fpg_interfaces[f1_index].get(interface_index, None)

    def get_host_on_interface(self, interface_index, host_index):
        host_obj = None
        if interface_index in self.interfaces:
            interface_obj = self.interfaces[interface_index]
            host_obj = self.get_host_on_interface_obj(interface_obj=interface_obj, host_index=host_index)
        return host_obj

    def get_host_on_interface_obj(self, interface_obj, host_index=None):
        host = None
        if interface_obj.dual_interface_index is None:
            peer_instance = interface_obj.get_peer_instance()
            if peer_instance.type != EndPoint.END_POINT_TYPE_DUT:
                host = peer_instance.get_host_instance(host_index=host_index)
                if not host:
                    host = peer_instance.host_info # only used if deploy has not happened
        else:
            host = self.get_host_on_interface(interface_index=interface_obj.dual_interface_index, host_index=host_index)
        return host

    def get_dut_on_interface_obj(self, interface_obj, host_index=None):
        dut_obj = None
        peer_instance = interface_obj.get_peer_instance()
        if peer_instance and peer_instance.type == EndPoint.END_POINT_TYPE_DUT:
            dut_obj = peer_instance.get_instance()
        return dut_obj

    @fun_test.safe
    def get_host_on_fpg_interface(self, interface_index, host_index, f1_index=0):
        host = None
        interface_obj = self.fpg_interfaces[f1_index].get(interface_index, None)
        if interface_obj:
            peer_instance = interface_obj.get_peer_instance()
            if peer_instance:
                host = peer_instance.get_host_instance(host_index=host_index)
        return host

    @fun_test.safe
    def get_dut_on_fpg_interface(self, interface_index, f1_index):
        dut_obj = None
        interface_obj = self.fpg_interfaces[f1_index].get(interface_index, None)
        if interface_obj:
            peer_instance = interface_obj.get_peer_instance()
            if peer_instance:
                dut_obj = peer_instance.get_host_instance()
        return dut_obj