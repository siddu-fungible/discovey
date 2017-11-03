from lib.system.utils import ToDictMixin

class EndPoint(object, ToDictMixin):
    end_point_type = "Unknown end-point type"
    END_POINT_TYPE_BARE_METAL = "END_POINT_TYPE_BARE_METAL"
    END_POINT_TYPE_VM = "END_POINT_TYPE_VM"
    END_POINT_TYPE_SSD = "END_POINT_TYPE_SSD"

    # Hypervisor Endpoint types indicate Containers capable of carrying multiple hosts
    END_POINT_TYPE_HYPERVISOR = "END_POINT_TYPE_HYPERVISOR"
    END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED = "END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED"  # A container where the DUT and multiple QEMU instances are colocated
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

class QemuColocatedHypervisorEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED

    def __init__(self, num_vms=None):
        super(QemuColocatedHypervisorEndPoint, self).__init__()
        self.num_vms = num_vms
        self.mode = self.MODE_SIMULATION
        self.instances = []
        self.TO_DICT_VARS.extend(["mode", "num_vms", "end_point_type", "instances", "orchestrator"])


    def get_host_instance(self, host_index):
        return self.instances[host_index]

class SsdEndPoint(EndPoint):
    end_point_type = EndPoint.END_POINT_TYPE_SSD
