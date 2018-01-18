from lib.system.fun_test import fun_test
from lib.fun.f1 import F1
from lib.system.utils import ToDictMixin
from lib.topology.end_points import BareMetalEndPoint, QemuColocatedHypervisorEndPoint, HypervisorEndPoint


class DutInterface(ToDictMixin):
    INTERFACE_TYPE_PCIE = "INTERFACE_TYPE_PCIE"
    INTERFACE_TYPE_ETHERNET = "INTERFACE_TYPE_ETHERNET"

    TO_DICT_VARS = ["index", "type", "peer_info"]

    def __init__(self, index, type):
        self.index = index  # interface index
        self.peer_info = None
        self.type = type  # pcie, ethernet

    def get_peer_instance(self):
        return self.peer_info

    def add_hosts(self, num_hosts=0):
        # fun_test.simple_assert(num_hosts or num_vms, "num hosts or num vms")

        if num_hosts:
            fun_test.debug("User intended baremetal for Interface: {}".format(self.index))
            self.peer_info = BareMetalEndPoint()

    def add_qemu_colocated_hypervisor(self, num_vms=0):
        if num_vms:
            self.peer_info = QemuColocatedHypervisorEndPoint(num_vms=num_vms)
            fun_test.debug("User intended hypervisor for Interface: {}".format(self.index))

    def add_hypervisor(self, num_vms=0):
        if num_vms:
            if self.type == DutInterface.INTERFACE_TYPE_ETHERNET:
                self.peer_info = HypervisorEndPoint(num_vms=num_vms)
                fun_test.debug("User intended hypervisor for Interface: {}".format(self.index))

    def add_drives_to_interface(self, num_ssds=0):
        fun_test.simple_assert(num_ssds, "Num ssds")


class Dut(ToDictMixin):
    DUT_TYPE_FSU = "DUT_TYPE_FSU"
    DUT_TYPE_FM8 = "DUT_TYPE_FM8"



    MODE_SIMULATION = "MODE_SIMULATION"
    MODE_EMULATION = "MODE_EMULATION"
    MODE_REAL = "MODE_REAL"

    TO_DICT_VARS = ["type", "index", "interfaces", "start_mode", "instance"]



    def __init__(self, type, index, mode=MODE_SIMULATION, spec=None):
        self.type = type
        self.index = index
        self.interfaces = {}
        self.spec = spec
        self.mode = mode
        self.instance = None

    def __repr__(self):
        return str(self.index) + " : " + str(self.type)

    def set_instance(self, instance):
        self.instance = instance

    def add_interface(self, index, type):
        dut_interface_obj = DutInterface(index=index, type=type)
        self.interfaces[index] = dut_interface_obj
        return dut_interface_obj

    def start(self):
        pass

    def get_instance(self):
        return self.instance

    def get_interface(self, interface_index):
        return self.interfaces[interface_index]

    def get_host_on_interface(self, interface_index, host_index):
        return self.interfaces[interface_index].get_peer_instance().get_host_instance(host_index=host_index)
