from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux

"""
      "0": {
        "name": "enp216s0",
        "ip": "15.1.11.2/24",
        "switch_info": {
          "name": "qfx-1",
          "port": "et-0/0/10"
        }
      }
"""

class HostType:
    HOST_TYPE_BARE_METAL = "HOST_TYPE_BARE_METAL"
    HOST_TYPE_VM = "HOST_TYPE_VM"

class HostInterface():
    def __init__(self, name, ip, spec):
        self.name = name
        self.ip = ip
        self.spec = spec
        self.peer_info = spec.get("switch_info", None)

class Host(ToDictMixin):
    def __init__(self, name, spec):
        self.name = name
        self.spec = spec
        self.instance = None
        self.test_interfaces = {}

        if self.spec:
            if "test_interface_info" in self.spec:
                self.set_test_interfaces(self.spec["test_interface_info"])

    def set_test_interfaces(self, info):
        for interface_index, interface_info in info.iteritems():
            self.test_interfaces[int(interface_index)] = HostInterface(name=interface_info["name"],
                                                                       ip=interface_info["ip"],
                                                                       spec=interface_info)
        pass

    def set_spec(self, spec):
        self.spec = spec

    def get_spec(self):
        return self.spec

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

    def get_test_interfaces(self):
        return self.test_interfaces

    def get_test_interface(self, index):
        result = None
        if index in self.test_interfaces:
            result = self.test_interfaces[index]
        else:
            fun_test.critical("Host interface index: {} not found".format(index))
        return result