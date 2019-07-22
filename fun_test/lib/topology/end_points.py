from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from threading import Thread

class EndPoint(object, ToDictMixin):
    end_point_type = "Unknown end-point type"
    END_POINT_TYPE_BARE_METAL = "END_POINT_TYPE_BARE_METAL"
    END_POINT_TYPE_VM = "END_POINT_TYPE_VM"
    END_POINT_TYPE_SSD = "END_POINT_TYPE_SSD"
    END_POINT_TYPE_FIO = "END_POINT_TYPE_FIO"
    END_POINT_TYPE_LINUX_HOST = "END_POINT_TYPE_LINUX_HOST"
    END_POINT_TYPE_DUT = "END_POINT_TYPE_DUT"   # DUT is connected to DUT
    END_POINT_TYPE_SWITCH = "END_POINT_TYPE_SWITCH"

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

    class RebootWorker(Thread):
        def __init__(self, instance):
            super(BareMetalEndPoint.RebootWorker, self).__init__()
            self.instance = instance
            self.work_complete = False
            self.result = False

        def run(self):
            reboot_result = self.instance.reboot(non_blocking=True)
            if reboot_result:
                self.work_complete = True
                self.result = True


    def __init__(self, host_info):
        super(BareMetalEndPoint, self).__init__()
        self.mode = self.MODE_SIMULATION
        self.host_info = host_info
        self.instance = None
        self.reboot_worker = None

    def add_instance(self, instance):
        self.instance = instance

    def get_host_instance(self, host_index=None):
        return self.instance

    def reboot(self):
        self.reboot_worker = self.RebootWorker(instance=self.get_instance())
        self.reboot_worker.start()
        return True

    def is_ready(self, max_wait_time=300):
        instance_ready = False
        if self.reboot_worker and self.reboot_worker.work_complete:
            if self.reboot_worker.result:
                host_instance = self.get_host_instance()
                ipmi_details = None
                if host_instance.extra_attributes:
                    if "ipmi_info" in host_instance.extra_attributes:
                        ipmi_details = host_instance.extra_attributes["ipmi_info"]
                instance_ready = host_instance.ensure_host_is_up(max_wait_time=max_wait_time,
                                                                 ipmi_details=ipmi_details,
                                                                 power_cycle=True)
        return instance_ready


class SwitchEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_SWITCH

    def __init__(self, name, port, spec):
        super(SwitchEndPoint, self).__init__()
        self.spec = spec
        self.name = name
        self.port = port

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

class DutEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_DUT

    def __init__(self, dut_index, fpg_interface_info=None):
        super(DutEndPoint, self).__init__()
        self.dut_index = dut_index
        self.fpg_interface_info = fpg_interface_info
        self.instance = None

    def get_instance(self):
        return self.instance

    def set_instance(self, instance):
        self.instance = instance

class HypervisorEndPoint(EndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_HYPERVISOR

    def __init__(self, num_vms=None):
        super(HypervisorEndPoint, self).__init__()
        self.num_vms = num_vms
        self.mode = self.MODE_SIMULATION
        self.instances = []


class QemuColocatedHypervisorEndPoint(HypervisorEndPoint, ToDictMixin):
    end_point_type = EndPoint.END_POINT_TYPE_HYPERVISOR_QEMU_COLOCATED

    def __init__(self, num_vms=None, vm_start_mode=None, vm_host_os=None):
        super(QemuColocatedHypervisorEndPoint, self).__init__()
        self.num_vms = num_vms
        self.vm_start_mode = vm_start_mode
        self.vm_host_os = vm_host_os
        self.mode = self.MODE_SIMULATION
        self.TO_DICT_VARS.extend(["mode", "num_vms", "end_point_type", "instances", "orchestrator"])

    def add_instance(self, instance):
        self.instances.append(instance)

    def get_host_instance(self, host_index):
        return self.instances[host_index]

    def __getstate__(self):
        d = dict(self.__dict__)
        if 'handle' in d:
            del d['handle']
        if 'logger' in d:
            del d['logger']
        return d


class SsdEndPoint(EndPoint):
    end_point_type = EndPoint.END_POINT_TYPE_SSD


class FioEndPoint(EndPoint):
    end_point_type = EndPoint.END_POINT_TYPE_FIO

    def __init__(self):
        super(FioEndPoint, self).__init__()
        self.instance = None

    def __str__(self):
        return "Fio Endpoint"

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance


class LinuxHostEndPoint(EndPoint):
    end_point_type = EndPoint.END_POINT_TYPE_LINUX_HOST

    def __init__(self):
        super(LinuxHostEndPoint, self).__init__()
        self.instance = None

    def __str__(self):
        return "Linux Server Endpoint"

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance
