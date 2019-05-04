from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin

class ExpandedTopology(ToDictMixin):
    TO_DICT_VARS = ["duts", "tgs"]

    def __init__(self):
        self.duts = {}
        self.tgs = {}
        self.active_orchestrators = []

    def add_active_orchestrator(self, orchestrator):
        self.active_orchestrators.append(orchestrator)

    def get_dut(self, index):
        result = None
        if index in self.duts:
            result = self.duts[index]
        return result

    def get_tg(self, index):
        result = None
        if index in self.tgs:
            result = self.tgs[index]
        return result

    def get_dut_instance(self, index):
        result = None
        dut = self.get_dut(index=index)
        if dut:
            result = dut.get_instance()
        return result

    def get_host_instance(self, dut_index, host_index, interface_index=None, ssd_interface_index=None, fpg_interface_index=None):
        dut = self.get_dut(index=dut_index)
        if ssd_interface_index is not None:  # Backward compatibility
            interface_index = ssd_interface_index
        host = None
        fun_test.simple_assert(interface_index is not None or fpg_interface_index is not None, "Provide SSD interface or FPG interface")
        if interface_index is not None:
            host = dut.get_host_on_interface(interface_index=interface_index, host_index=host_index)
        elif fpg_interface_index is not None:
            host = dut.get_host_on_fpg_interface(interface_index=fpg_interface_index, host_index=host_index)
        return host

    def _get_host_instances_on_interfaces(self, dut, interfaces):
        hosts = {}
        for interface_index, interface_obj in interfaces.iteritems():
            host = dut.get_host_on_interface_obj(interface_obj=interface_obj, host_index=0)
            if host.host_ip not in hosts:
                hosts[host.host_ip] = {"interfaces": [interface_obj], "host_obj": host}
            else:
                hosts[host.host_ip]["interfaces"].append(interface_obj)
        return hosts

    def get_host_instances_on_ssd_interfaces(self, dut_index):
        dut = self.get_dut(index=dut_index)
        return self._get_host_instances_on_interfaces(dut=dut, interfaces=dut.get_ssd_interfaces())

    def get_host_instances_on_fpg_interfaces(self, dut_index):
        dut = self.get_dut(index=dut_index)
        return self._get_host_instances_on_interfaces(dut=dut, interfaces=dut.get_fpg_interfaces())

    def get_tg_instance(self, tg_index):
        tg = self.get_tg(index=tg_index)
        return tg.get_instance()

    def cleanup(self):
        for active_orchestrator in self.active_orchestrators:
            active_orchestrator.cleanup()

