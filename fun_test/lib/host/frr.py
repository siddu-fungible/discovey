from lib.system.fun_test import fun_test
from lib.host.linux import Linux
import re


PAT_IP_ADDR = r'(?:\d{1,3}\.){3}\d{1,3}'

PAT_IP_BGP_LOCAL_AS = re.compile(r'local AS number (\d+)')
PAT_IP_BGP_NEIGH = re.compile(
    r'(%s)\s+4\s+(\d+).*?(?:(?:\d{2}:){2}\d{2}|[a-zA-Z]+)\s+(\d+|[a-zA-Z]+)' % PAT_IP_ADDR)
PAT_ISIS_NEIGH = re.compile(r'(node\S+)\s+(\S+)\s+.*1\s+(\w+)')
PAT_IP_ROUTE_SUM = re.compile(r'(connected|isis|ebgp|ibgp)\s+(\d+)\s+(\d+)')
PAT_IP_ROUTE = re.compile(r'\* (%s/\d{1,2}|).*?(%s|directly connected),\s+(\S+)' % (PAT_IP_ADDR, PAT_IP_ADDR))


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
                result['neighbors'].append(
                    {'ip_addr': ip_addr,
                     'ASN': asn,
                     'state_prefixes': int(state_prefixes) if state_prefixes.isdigit() else state_prefixes})
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

    def get_ip_route_sum(self):
        """Do 'show ip route sum' and get number of routes from each protocol

        root@node-1-1:~# vtysh -c 'show ip route sum'
        Route Source         Routes               FIB  (vrf Default-IP-Routing-Table)
        kernel               1                    1
        connected            7                    7
        isis                 6                    3
        ebgp                 16                   16
        ibgp                 3                    3
        ------
        Totals               33                   30

        root@node-1-1:~# 

        :return: dict {'connected': {'Routes': 1, 'FIB': 1}, 'isis': {'Routes': 7, 'FIB': 3}}, ..}
        """
        output = self.vtysh_command('show ip route sum')
        result = {}

        m = PAT_IP_ROUTE_SUM.findall(output)
        if m:
            for protocol, rib, fib in m:
                result.update({protocol: {'Routes': int(rib), 'FIB': int(fib)}})
        return result

    def get_ip_route(self, fib=False):
        """Do 'show ip route' and get RIB info, excluding inactive routes

        root@node-1-1:~# vtysh -c 'show ip route'
        Codes: K - kernel route, C - connected, S - static, R - RIP,
               O - OSPF, I - IS-IS, B - BGP, P - PIM, E - EIGRP, N - NHRP,
               T - Table, v - VNC, V - VNC-Direct, A - Babel,
               > - selected route, * - FIB route

        K>* 0.0.0.0/0 [0/0] via 172.17.0.1, eth0
        C>* 10.0.0.1/32 is directly connected, lo
        B>* 10.0.0.16/28 [200/0] via 192.168.0.2, p-65, 00:03:45
        B>* 10.0.0.32/28 [200/0] via 192.168.0.6, p-67, 00:03:45
        B>* 10.0.0.48/28 [200/0] via 192.168.0.10, p-69, 00:03:45
        B>* 10.0.1.0/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                    via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.1.16/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                     via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.1.32/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                     via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.1.48/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                     via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.2.0/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                    via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.2.16/28 [20/0] via 192.96.0.6, p-3, 00:03:44
          *                     via 192.96.0.2, p-1, 00:03:44
        B>* 10.0.2.32/28 [20/0] via 192.96.0.6, p-3, 00:03:44
          *                     via 192.96.0.2, p-1, 00:03:44
        B>* 10.0.2.48/28 [20/0] via 192.96.0.6, p-3, 00:03:44
          *                     via 192.96.0.2, p-1, 00:03:44
        B>* 10.0.3.0/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                    via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.3.16/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                     via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.3.32/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                     via 192.96.0.6, p-3, 00:03:44
        B>* 10.0.3.48/28 [20/0] via 192.96.0.2, p-1, 00:03:44
          *                     via 192.96.0.6, p-3, 00:03:44
        C>* 172.17.0.0/16 is directly connected, eth0
        C>* 192.96.0.0/30 is directly connected, p-1
        C>* 192.96.0.4/30 is directly connected, p-3
        I   192.168.0.0/30 [115/2] via 192.168.0.2, p-65 inactive, 00:03:17
        C>* 192.168.0.0/30 is directly connected, p-65
        I   192.168.0.4/30 [115/2] via 192.168.0.6, p-67 inactive, 00:03:16
        C>* 192.168.0.4/30 is directly connected, p-67
        I   192.168.0.8/30 [115/2] via 192.168.0.10, p-69 inactive, 00:03:16
        C>* 192.168.0.8/30 is directly connected, p-69
        I>* 192.168.0.12/30 [115/2] via 192.168.0.6, p-67, 00:03:16
          *                         via 192.168.0.2, p-65, 00:03:16
        I>* 192.168.0.16/30 [115/2] via 192.168.0.2, p-65, 00:03:16
          *                         via 192.168.0.10, p-69, 00:03:16
        I>* 192.168.0.20/30 [115/2] via 192.168.0.6, p-67, 00:03:16
          *                         via 192.168.0.10, p-69, 00:03:16
        root@node-1-1:~#


        :return: dict {'10.0.0.1/32': {'directly connected': 'p-114'},
                       '10.0.1.0/28': {'192.96.0.2': 'p-1', '192.96.0.6': 'p-3'},
                        ..}
        """
        cmd = 'show ip %s' % ('fib' if fib else 'route')
        output = self.vtysh_command(cmd)
        result = {}

        m = PAT_IP_ROUTE.findall(output)
        if m:
            for prefix, nhp, interface in m:
                if prefix:
                    prefix_cache = prefix
                else:
                    prefix = prefix_cache
                result.setdefault(prefix, {}).update({nhp: interface.rstrip(',')})
        return result

    def get_ip_fib(self):
        """Do 'show ip fib' and get FIB info

        root@node-1-1:~# vtysh -c 'show ip fib'
        Codes: K - kernel route, C - connected, S - static, R - RIP,
               O - OSPF, I - IS-IS, B - BGP, P - PIM, E - EIGRP, N - NHRP,
               T - Table, v - VNC, V - VNC-Direct, A - Babel,
               > - selected route, * - FIB route

        K>* 0.0.0.0/0 [0/0] via 172.17.0.1, eth0
        C>* 10.0.0.1/32 is directly connected, lo
        B>* 10.0.0.16/28 [200/0] via 192.168.0.2, p-65, 00:10:49
        B>* 10.0.0.32/28 [200/0] via 192.168.0.6, p-67, 00:10:49
        B>* 10.0.0.48/28 [200/0] via 192.168.0.10, p-69, 00:10:49
        B>* 10.0.1.0/28 [20/0] via 192.96.0.2, p-1, 00:10:48
          *                    via 192.96.0.6, p-3, 00:10:48
        ..

        :return: same as self.get_ip_route()
        """
        return self.get_ip_route(fib=True)

    def get_bgp_timers(self):
        """ Do 'show run bgpd' | grep 'timers bgp' to get BGP keepalive/hold time.

        root@node-1-1:~# vtysh -c 'show run bgpd' | grep 'timers bgp'
         timers bgp 5 15
        root@node-1-1:~#

        :return: tuple, (5, 15)
        """
        output = self.command("vtysh -c 'show run bgpd' | grep 'timers bgp'")
        result = ()

        m = re.search(r'timers bgp (\d+) (\d+)', output)
        if m:
            result = (int(m.group(1)), int(m.group(2)))
        return result



if __name__ == "__main__":
    node = '1-1'
    frr_obj = Frr(host_ip=node,
                  ssh_username="root",
                  ssh_password="fun123",
                  ssh_port=None)

    for cmd in ('show ip bgp sum',
                'show isis neighbor',
                'show ip route sum'):
        output = frr_obj.vtysh_command(cmd)
        fun_test.log("\nOutput:" + output)

    import pprint
    for func in (frr_obj.get_ip_bgp_sum,
                 frr_obj.get_isis_neighbor,
                 frr_obj.get_ip_route_sum,
                 frr_obj.get_ip_route,
                 frr_obj.get_ip_fib):
        pprint.pprint(func())

    linux_obj = Linux(host_ip='192.168.162.128',
                      ssh_username="root",
                      ssh_password="fun123")
    pprint.pprint(linux_obj.get_ip_route(netns=node))