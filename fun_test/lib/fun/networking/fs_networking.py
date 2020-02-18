class InterfaceTypes:
    INTERFACE_TYPE_ETHERNET = "INTERFACE_TYPE_ETHERNET"
    INTERFACE_TYPE_ETHERNET_BOND = "INTERFACE_TYPE_ETHERNET_BOND"

class Route:
    def __init__(self, network, gateway):
        self.network = network
        self.gateway = gateway

class FpgInterface():
    def __init__(self, f1_index, interface_index, type=InterfaceTypes.INTERFACE_TYPE_ETHERNET):
        self.switch_info = None
        self.f1_index = f1_index
        self.interface_index = interface_index

    def set_switch_info(self, switch_info):
        self.switch_info = switch_info


class BondInterface():
    def __init__(self, f1_index, interface_index, type=InterfaceTypes.INTERFACE_TYPE_ETHERNET_BOND):
        self.f1_index = f1_index
        self.interface_index = interface_index
        self.ip = None
        self.routes = []   # List of type Route
        self.fpg_slaves = None

    def set_ip(self, ip):
        self.ip = ip

    def add_route(self, route):
        self.routes.append(route)

    def set_fpg_slaves(self, slave_indexes):
        self.fpg_slaves = slave_indexes


class FsNetworking():
    fpg_interfaces = {0: {}, 1: {}}   # One for each f1-index
    bond_interfaces = {0: {}, 1: {}}

    def __init__(self, fs_obj):
        self.fs_obj = fs_obj

    def add_fpg_interface(self, f1_index, interface_index):
        fpg_interface = FpgInterface(f1_index=f1_index, interface_index=interface_index)
        self.fpg_interfaces[f1_index][interface_index] = fpg_interface
        return fpg_interface

    def get_fpg_interface(self, f1_index, interface_index):
        return self.fpg_interfaces[f1_index].get(interface_index, None)

    def get_fpg_interfaces(self, f1_index):
        return self.fpg_interfaces[f1_index]

    def add_bond_interface(self, f1_index, interface_index):
        bond_interface = BondInterface(f1_index=f1_index, interface_index=interface_index)
        self.bond_interfaces[f1_index][interface_index] = bond_interface
        return bond_interface

    def get_bond_interface(self, f1_index, interface_index):
        return self.bond_interfaces[f1_index].get(interface_index, None)

    def get_bond_interfaces(self, f1_index):
        return self.bond_interfaces[f1_index]