from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin

class ExpandedTopology(ToDictMixin):
    TO_DICT_VARS = ["duts", "tgs"]

    def __init__(self, spec):
        self.duts = {}
        self.tgs = {}
        self.active_orchestrators = []
        self.switches = {}
        self.hosts = {}
        self.spec = spec
        self.cleaned_up = False

    def is_cleaned_up(self):
        return self.cleaned_up

    def add_active_orchestrator(self, orchestrator):
        self.active_orchestrators.append(orchestrator)

    def get_dut(self, index):
        result = None
        if index in self.duts:
            result = self.duts[index]
        else:
            fun_test.log("Dut Index: {} not found".format(index))
        return result

    def get_duts(self):
        return self.duts

    def get_switch(self, name):
        result = None
        if name in self.switches:
            result = self.switches[name]
        else:
            fun_test.log("Switch: {} not found".format(name))
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

    def get_switch_instance(self, name):
        result = None
        result = self.get_switch(name=name)
        return result

    def get_host_instances(self):
        result = {}
        for host_name, host in self.hosts.iteritems():
            result[host_name] = host.get_instance()
        return result

    def get_hosts(self):
        return self.hosts

    def get_host(self, name):
        host = self.hosts.get(name, None)
        return host

    def get_host_instance(self,
                          dut_index,
                          name=None,
                          host_index=None,
                          interface_index=None,
                          ssd_interface_index=None,
                          pcie_interface_index=None,
                          fpg_interface_index=None,
                          f1_index=0):
        host = None

        if (interface_index is not None or ssd_interface_index is not None or pcie_interface_index is not None or fpg_interface_index is not None) and host_index is not None:
            dut = self.get_dut(index=dut_index)
            if ssd_interface_index is not None:  # Backward compatibility
                interface_index = ssd_interface_index
            if pcie_interface_index is not None:  # Backward compatibility
                interface_index = pcie_interface_index
            host = None
            fun_test.simple_assert(interface_index is not None or fpg_interface_index is not None, "Provide SSD interface or FPG interface")
            if interface_index is not None:
                host = dut.get_host_on_interface(interface_index=interface_index, host_index=host_index)
            elif fpg_interface_index is not None:
                host = dut.get_host_on_fpg_interface(interface_index=fpg_interface_index, host_index=host_index, f1_index=f1_index)
        elif name is not None:
            host_instances = self.get_host_instances()
            if name not in host_instances:
                fun_test.critical("Host name: {} not found".format(name))
            host = host_instances[name]
        return host

    def _get_host_instances_on_interfaces(self, dut, interfaces):
        hosts = {}
        for interface_index, interface_obj in interfaces.iteritems():
            host = dut.get_host_on_interface_obj(interface_obj=interface_obj, host_index=0)
            if host:
                if host.host_ip not in hosts:
                    hosts[host.host_ip] = {"interfaces": [interface_obj], "host_obj": host}
                else:
                    hosts[host.host_ip]["interfaces"].append(interface_obj)
        return hosts

    def _get_dut_instances_on_interfaces(self, dut, interfaces):
        duts = []
        for interface_index, interface_obj in interfaces.iteritems():
            dut_on_interface = dut.get_dut_on_interface_obj(interface_obj=interface_obj)
            if dut_on_interface:
                duts.append({"dut_obj": dut_on_interface, "interface_obj": interface_obj})
        return duts

    def get_host_instances_on_ssd_interfaces(self, dut_index):
        dut = self.get_dut(index=dut_index)
        return self._get_host_instances_on_interfaces(dut=dut, interfaces=dut.get_ssd_interfaces())

    def get_host_instances_on_fpg_interfaces(self, dut_index, f1_index=0):
        dut = self.get_dut(index=dut_index)
        return self._get_host_instances_on_interfaces(dut=dut, interfaces=dut.get_fpg_interfaces(f1_index=f1_index))

    def get_dut_instances_on_fpg_interfaces(self, dut_index, f1_index=0):
        dut = self.get_dut(index=dut_index)
        return self._get_dut_instances_on_interfaces(dut=dut, interfaces=dut.get_fpg_interfaces(f1_index=f1_index))

    def get_tg_instance(self, tg_index):
        tg = self.get_tg(index=tg_index)
        return tg.get_instance()

    def cleanup(self):
        for active_orchestrator in self.active_orchestrators:
            active_orchestrator.cleanup()
        self.cleaned_up = True

