from lib.system.fun_test import *
from fun_settings import SCRIPTS_DIR
import yaml


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

    def get_a_nu_interface(self):
        namespaces = self.get_namespaces('nu')
        for ns in namespaces:
            if ns is None:
                ns = 'default'
            interfaces = self.configs['nu']['namespaces'][ns]['interfaces']
            if interfaces:
                return interfaces[0].keys()[0]

    def get_hu_pf_interface(self):
        return self.configs['hu']['pf_interface']

    def get_hu_vf_interface(self):
        return self.configs['hu']['vf_interface']

    def get_hu_pf_interface_fcp(self):
        return self.configs['hu']['pf_interface_fcp']

    def get_hu_vf_interface_fcp(self):
        return self.configs['hu']['vf_interface_fcp']

    def get_namespaces(self, nu_or_hu):
        return [n if n != 'default' else None for n in self.configs[nu_or_hu]['namespaces'].keys()]

    def get_hu_pf_namespace(self):
        for ns in self.get_namespaces('hu'):
            if self.get_hu_pf_interface() in self.get_interfaces('hu', ns):
                if ns != 'default':
                    return ns
                else:
                    return None

    def get_hu_vf_namespace(self):
        for ns in self.get_namespaces('hu'):
            if self.get_hu_vf_interface() in self.get_interfaces('hu', ns):
                if ns != 'default':
                    return ns
                else:
                    return None

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

    def get_interface_ipv4_addr(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get('ipv4_addr', None)

    def get_interface_ipv4_netmask(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for intf_dict in self.get_interface_dicts(nu_or_hu, namespace):
                if intf_dict.keys()[0] == intf:
                    return intf_dict[intf].get('ipv4_netmask', None)

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
        return self.configs[nu_or_hu]['namespaces'][ns]['routes']