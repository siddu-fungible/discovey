from lib.system.fun_test import fun_test
from lib.host.linux import Linux
import re


PAT_IP_BGP_LOCAL_AS = re.compile(r'local AS number (\d+)')
PAT_IP_BGP_NEIGH = re.compile(
    r'((?:\d{1,3}\.){3}\d{1,3})\s+4\s+(\d+).*?(?:(?:\d{2}:){2}\d{2}|[a-zA-Z]+)\s+(\d+|[a-zA-Z]+)')
PAT_ISIS_NEIGH = re.compile(r'(node\S+)\s+(\S+)\s+.*1\s+(\w+)')


class Frr(Linux):
    """class for FRR/Quagga"""

    def vtysh_command(self, cmd):
        """Do vtysh -c 'cmd' under Linux shell to execute FRR/Quagga cmd."""
        return self.command("vtysh -c '%s'" % cmd)

    def get_ip_bgp_sum(self):
        """Do 'show ip bgp sum' and get local ASN, neighbor ip addr, ASN, state/prefixes

        node-1-1# show ip bgp sum

        IPv4 Unicast Summary:
        BGP router identifier 10.0.0.1, local AS number 64513 vrf-id 0
        BGP table version 25
        RIB entries 27, using 4104 bytes of memory
        Peers 5, using 97 KiB of memory

        Neighbor        V         AS MsgRcvd MsgSent   TblVer  InQ OutQ  Up/Down State/PfxRcd
        192.96.0.2      4      64512      35      39        0    0    0 00:01:57           10
        192.96.0.6      4      64512      34      39        0    0    0 00:01:57           10
        192.168.0.2     4      64513      39      41        0    0    0 00:01:55           21
        192.168.0.6     4      64513      39      41        0    0    0 00:01:55           23
        192.168.0.10    4      64513       0       1        0    0    0    never       Active

        Total number of neighbors 5


        :return: dict {'local_ASN': '64513', 
                       'neighbors': [{'ip_addr': '192.168.0.2', 'ASN': '64513', 'prefixes': '10'}, ..]}
        """
        output = self.vtysh_command('show ip bgp sum')
        result = {}

        m = PAT_IP_BGP_LOCAL_AS.search(output)
        if m:
            result.update({'local_ASN': m.group(1)})

        m = PAT_IP_BGP_NEIGH.findall(output)
        if m:
            result.update({'neighbors': []})
            for ip_addr, asn, state_prefixes in m:
                result['neighbors'].append({'ip_addr': ip_addr, 'ASN': asn, 'state_prefixes': state_prefixes})
        result['neighbors'].sort()
        return result

    def get_isis_neighbor(self):
        """Do 'show isis neighbor' and get neighbor state

        root@node-1-1:~# vtysh -c 'show isis neighbor'
        Area rack1:
          System Id           Interface   L  State        Holdtime SNPA
          node-1-3            p-67        1  Up           8        2020.2020.2020
          node-1-2            p-65        1  Up           8        2020.2020.2020
          node-1-4            p-69        1  Up           8        2020.2020.2020
        root@node-1-1:~#

        :return: dict {{'System_Id': 'node-1-3', 'Interface': 'p-67', 'State': 'Up'}, ..}
        """
        output = self.vtysh_command('show isis neighbor')
        result = {}

        m = PAT_ISIS_NEIGH.findall(output)
        if m:
            for system_id, interface, state in m:
                result.update({'System_Id': system_id, 'Interface': interface, 'State': state})
        return result


if __name__ == "__main__":
    frr_obj = Frr(host_ip="1-1",
                  ssh_username="root",
                  ssh_password="fun123",
                  ssh_port=None)
    output = frr_obj.vtysh_command('show ip bgp sum')
    fun_test.log("\nOutput:" + output)
    output = frr_obj.vtysh_command('show isis neighbor')
    fun_test.log("\nOutput:" + output)

    import pprint
    result = frr_obj.get_ip_bgp_sum()
    pprint.pprint(result)
    result = frr_obj.get_isis_neighbor()
    pprint.pprint(result)

