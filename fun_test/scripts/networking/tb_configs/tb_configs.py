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

    def get_hu_pf_interface(self):
        return self.configs['hu']['pf_interface']

    def get_hu_vf_interface(self):
        return self.configs['hu']['vf_interface']

    def get_namespaces(self, nu_or_hu):
        return self.configs[nu_or_hu]['namespaces'].keys()

    def get_interfaces(self, nu_or_hu, ns):
        return self.configs[nu_or_hu]['namespaces'][ns]['interfaces'].keys()

    def get_interface_mac_addr(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for interface in self.get_interfaces(nu_or_hu, namespace):
                if interface == intf:
                    return self.configs[nu_or_hu]['namespaces'][namespace]['interfaces'][intf]['mac_addr']

    def get_interface_ipv4_addr(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for interface in self.get_interfaces(nu_or_hu, namespace):
                if interface == intf:
                    return self.configs[nu_or_hu]['namespaces'][namespace]['interfaces'][intf]['ipv4_addr']

    def get_interface_ipv4_netmask(self, nu_or_hu, intf):
        for namespace in self.get_namespaces(nu_or_hu):
            for interface in self.get_interfaces(nu_or_hu, namespace):
                if interface == intf:
                    return self.configs[nu_or_hu]['namespaces'][namespace]['interfaces'][intf]['ipv4_netmask']

    def get_ipv4_routes(self, nu_or_hu, namespace):
        """Get route configs.

        :param namespace: str
        :return:
            list of dict, e.g. [{'prefix': 53.1.9.0/24, 'nexthop': 53.1.1.1},]
        """
        return self.configs[nu_or_hu]['namespaces'][namespace]['routes']