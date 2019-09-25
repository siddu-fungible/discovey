from lib.system.fun_test import *
from fun_settings import SCRIPTS_DIR
import yaml


def get_tb_name_vm(tb, ul_or_ol):
    "Get TB (test bed) config file name for VM underlay or overlay."
    if ul_or_ol.lower() in ('ul', 'underlay'):
        return '{}_UL_VM'.format(tb)
    elif ul_or_ol.lower() in ('ol', 'overlay'):
        return '{}_OL_VM'.format(tb)


class TBConfigs:
    """Class for Test Bed configs. The test bed examples are 'SN2', 'SB5'.
    """
    def __init__(self, tb_name):
        with open('{}/networking/tb_configs/{}.yml'.format(SCRIPTS_DIR, tb_name.upper())) as f:
            self.configs = yaml.load(f)

    def get_router_mac(self):
        return self.configs['router_mac']

    def get_hostname(self, nu_or_hu):
        return self.configs[nu_or_hu]['hostname']

    def get_username(self, nu_or_hu):
        return self.configs[nu_or_hu]['username']

    def get_password(self, nu_or_hu):
        return self.configs[nu_or_hu]['password']

    def get_mgmt_interface(self, nu_or_hu):
        return self.configs[nu_or_hu]['mgmt_interface']

    def get_an_interface(self, nu_or_hu, type=None):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                for intf in intf_dict.keys():
                    if intf_dict[intf].get('type', None) == type:
                        return intf

    def get_a_nu_interface(self, nu='nu'):
        namespaces = self.get_namespaces(nu)
        for ns in namespaces:
            if ns is None:
                ns = 'default'
            interfaces = self.configs[nu]['namespaces'][ns]['interfaces']
            if interfaces:
                return interfaces[0].keys()[0]

    def get_hu_pcie_width(self, hu='hu'):
        return self.configs[hu]['pcie_width']

    def get_hu_pf_interface(self, hu='hu'):
        return self.configs[hu]['pf_interface']

    def get_hu_vf_interface(self, hu='hu'):
        return self.configs[hu]['vf_interface']

    def get_hu_pf_interface_fcp(self, hu='hu'):
        return self.configs[hu]['pf_interface_fcp']

    def get_hu_vf_interface_fcp(self, hu='hu'):
        return self.configs[hu]['vf_interface_fcp']

    def get_namespaces(self, nu_or_hu):
        return [n if n != 'default' else None for n in self.configs[nu_or_hu]['namespaces'].keys()]

    def get_hu_pf_namespace(self, hu='hu'):
        for ns in self.get_namespaces(hu):
            if self.get_hu_pf_interface(hu) in self.get_interfaces(hu, ns):
                return ns

    def get_hu_vf_namespace(self, hu='hu'):
        for ns in self.get_namespaces(hu):
            if self.get_hu_vf_interface(hu) in self.get_interfaces(hu, ns):
                return ns

    def get_interface_dicts(self, nu_or_hu, ns):
        if ns is None:
            ns = 'default'
        return self.configs[nu_or_hu]['namespaces'][ns]['interfaces']

    def get_interfaces(self, nu_or_hu, ns):
        if ns is None:
            ns = 'default'
        return [i.keys()[0] for i in self.configs[nu_or_hu]['namespaces'][ns]['interfaces']]

    def get_all_interfaces(self, nu_or_hu):
        interfaces = []
        for namespace in self.get_namespaces(nu_or_hu):
            interfaces.extend(self.get_interfaces(nu_or_hu, namespace))
        return interfaces

    def get_interface_mac_addr(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get('mac_addr', None)

    def get_interface_addr(self, nu_or_hu, intf, address_family='ipv4'):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get(address_family, None)

    def get_interface_netmask(self, nu_or_hu, intf, address_family='ipv4'):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    if address_family == 'ipv4':
                        return intf_dict[intf].get('ipv4_netmask', None)
                    elif address_family == 'ipv6':
                        return intf_dict[intf].get('ipv6_prefix_length', None)

    def get_interface_ipv4_addr(self, nu_or_hu, intf):
        return self.get_interface_addr(nu_or_hu, intf, address_family='ipv4')

    def get_interface_ipv4_netmask(self, nu_or_hu, intf):
        return self.get_interface_netmask(nu_or_hu, intf, address_family='ipv4')

    def get_interface_ipv6_addr(self, nu_or_hu, intf):
        return self.get_interface_addr(nu_or_hu, intf, address_family='ipv6')

    def get_interface_ipv6_prefix_length(self, nu_or_hu, intf):
        return self.get_interface_netmask(nu_or_hu, intf, address_family='ipv6')

    def get_interface_mtu(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get('mtu', 1500)

    def is_macvlan(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get('type', None) == 'macvlan'

    def is_alias(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get('type', None) == 'alias'

    def get_ipv4_routes(self, nu_or_hu, ns):
        """Get route configs.

        :param ns: str
        :return:
            list of dict, e.g. [{'prefix': 53.1.9.0/24, 'nexthop': 53.1.1.1},]
        """
        if ns is None:
            ns = 'default'
        return self.configs[nu_or_hu]['namespaces'][ns].get('routes', [])

    def get_ipv6_routes(self, nu_or_hu, ns):
        """Get IPv6 route configs."""
        if ns is None:
            ns = 'default'
        return self.configs[nu_or_hu]['namespaces'][ns].get('ipv6_routes', [])

    def get_arps(self, nu_or_hu, ns):
        """Get arp entries.

        :param ns: str
        :return:
            list of dict, e.g. [{'ipv4_addr': 53.1.1.4, 'mac_addr': 00:de:ad:be:ef:11},]
        """
        if ns is None:
            ns = 'default'
        return self.configs[nu_or_hu]['namespaces'][ns].get('arps', [])

    def get_vm_host(self, vm):
        return self.configs[vm].get('host')

    def get_vm_host_pci_info(self, vm):
        return self.configs[vm].get('pci_info')