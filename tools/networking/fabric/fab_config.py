#from lib.system.fun_test import *
import os
import json
from netaddr import IPNetwork
import argparse


PUBLIC_NET = '10.0.0.0/14'
F1_LO_NET = '192.0.0.0/8'
F1_SPINE_NET = '193.0.0.0/13'
SPINE_LO_NET = '194.0.0.0/16'

F1_PUBLIC_SUBNETS = []
F1_LO_SUBNETS = []
SPINE_SUBNETS = []
SPINE_LO_SUBNETS = []

F1_AS = 64512
SPINE_AS = 64513

TOPO_DATA = {}
F1_CONFIG = {}
CX_CONFIG = {}


def readTopoDefinition(filename):

    topo_def_data = None
    try:
        topo_def_data = json.loads(open(filename).read())
    except Exception as ex:
        print str(ex)
    return topo_def_data

def writeCxConfig():

    for k,v in CX_CONFIG.items():
        v += "commit\n"
        abs_path = os.path.join(OUTPUT_DIR, 'Cx-' + str(k) + ".txt")
        with open(abs_path, 'w') as outfile:
            outfile.write(v)

def getCxConfig(cx_id):

    spine_subnet = SPINE_LO_SUBNETS.pop(0)
    spine_lo_ips = spine_subnet.iter_hosts()
    spine_lo_ip = spine_lo_ips.next()

    cx_name = "Cx"+str(cx_id)
    config = "set routing-instances %s instance-type virtual-router\n" % cx_name
    config += "set routing-instanaces %s routing-options router-id %s\n" % (cx_name, str(spine_lo_ip))
    config += "set routing-instances %s routing-options autonomous-system %s\n" % (cx_name, SPINE_AS)
    config += "set routing-instances %s protocols bgp group external-peers type external\n" % cx_name
    config += "set routing-instances %s protocols bgp group external-peers advertise-peer-as\n" % cx_name
    config += "set routing-instances %s protocols bgp group external-peers peer-as %s\n" % (cx_name, F1_AS)

    return config

def pretty(d, indent=0):

    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))


def configureTopoSubnets():

    nRacks = TOPO_DATA["Size"]["Racks"]
    nF1s = TOPO_DATA["Size"]["FSs"] * 2
    nSpines = TOPO_DATA["Size"]["Cx"]["Physical"] \
        if TOPO_DATA["Size"]["Cx"]["Virtual"] == 0 \
        else TOPO_DATA["Size"]["Cx"]["Virtual"]

    # F1 Subnet
    rack_subnets = []
    all_subnets = IPNetwork(PUBLIC_NET).subnet(24)
    all_subnets.next()
    for i in range(1, nRacks + 1):
        rack_subnets.append(all_subnets.next())
    for rack_subnet in rack_subnets:
        F1_PUBLIC_SUBNETS.extend(list(rack_subnet.subnet(28))[:nF1s])
    del all_subnets, rack_subnets

    # F1 Lo0
    all_subnets_lo = IPNetwork(F1_LO_NET).subnet(24)
    all_subnets_f1 = IPNetwork(all_subnets_lo.next()).subnet(32)
    all_subnets_f1.next()
    for i in range(0, nRacks):
        all_subnets_f1 = IPNetwork(all_subnets_lo.next()).subnet(32)
        all_subnets_f1.next()
        for j in range(0, nF1s):
            F1_LO_SUBNETS.append(all_subnets_f1.next())
    del all_subnets_lo, all_subnets_f1

    # Spine Links
    all_subnets = IPNetwork(F1_SPINE_NET).subnet(30)
    for i in range(0, nRacks * nSpines):
        SPINE_SUBNETS.append(all_subnets.next())
    del all_subnets

    # Spine Lo0
    all_subnets = IPNetwork(SPINE_LO_NET).subnet(32)
    all_subnets.next()
    for i in range(0, nSpines):
        SPINE_LO_SUBNETS.append(all_subnets.next())

def generateAllF1Configs():

    num_of_cx = TOPO_DATA["Size"]["Cx"]["Physical"] \
        if TOPO_DATA["Size"]["Cx"]["Virtual"] == 0 \
        else TOPO_DATA["Size"]["Cx"]["Virtual"]
    spine_per_f1 = num_of_cx / (TOPO_DATA["Size"]["FSs"]*2)

    for rack in TOPO_DATA["Racks"]:
        if TOPO_DATA["Size"]["Cx"]["Physical"] > 0:
            cx_id = 1
        for fs in rack["FS1600"]:
            for f1 in fs["F1s"]:
                generateF1Config(rack["id"], fs["id"], f1, cx_id)
                cx_id += spine_per_f1

def generateF1Config(rack_id, fs_id, f1, cx_id):

    f1_interfaces = []

    f1_bgp_config = {
        "as": F1_AS,
        "neighbors": []
    }

    num_of_cx = TOPO_DATA["Size"]["Cx"]["Physical"] \
        if TOPO_DATA["Size"]["Cx"]["Virtual"] == 0 \
        else TOPO_DATA["Size"]["Cx"]["Virtual"]
    spine_per_f1 = num_of_cx / (TOPO_DATA["Size"]["FSs"]*2)

    # Spine facing links
    for idx, Cxlink in enumerate(f1["CxLinks"]):
        fport, cxport = Cxlink["INTERFACES"].items()[0]
        spine_index = (fs_id-1)*(spine_per_f1 * 2) + f1["id"]*spine_per_f1 + idx
        spine_subnet = SPINE_SUBNETS.pop(0)
        spine_prefixlen = str(spine_subnet.prefixlen)
        host_ips = spine_subnet.iter_hosts()
        my_ip = str(host_ips.next())
        peer_ip = str(host_ips.next())
        f1_interface = {
            "id": fport,
            "description": "spine link from FS %s f1 %s port %s to Cx %s port %s" % (
                fs_id, f1["id"], fport, Cxlink["MGMT_IP"], cxport),
            "bandwidth": 100,
            "mtu": 9000,
            "vrf": 1,
            "type": "spine_facing",
            "spine_index": spine_index,
            "gph_index": [
                {"index": spine_index}
            ],
            "ip": {
                "address": my_ip,
                "netmask": spine_prefixlen
            }
        }
        f1_interfaces.append(f1_interface)

        # BGP Config for Spine Links
        bgp_n = {
            "ip": peer_ip,
            "as": SPINE_AS,
            "next-hop-self": True,
            "allowas-in": 1
        }
        f1_bgp_config["neighbors"].append(bgp_n)

        # Cx Config
        if rack_id == 1:
            CX_CONFIG[str(cx_id)] = getCxConfig(cx_id)

        CX_CONFIG[str(cx_id)] += "set routing-instance %s interface %s\n" % ("Cx"+str(cx_id), cxport)
        CX_CONFIG[str(cx_id)] += "set routing-instance %s protocols bgp group external-peers neighbor %s\n" % ("Cx" + str(cx_id), my_ip)
        CX_CONFIG[str(cx_id)] += "set interfaces %s unit 0 family inet addess %s/%s\n" % (cxport, peer_ip, spine_prefixlen)
        cx_id += 1


    # Fabric facing links
    for intf in sorted(f1["FabLinks"]):
        f1_interface = {}
        peer_fs_id, peer_f1_id = f1["FabLinks"][intf].split('_')
        remote_f1_id = (int(peer_fs_id) -1)*2 + int(peer_f1_id)
        gph_index = []
        for i in range(spine_per_f1):
            temp = {}
            temp["index"] = remote_f1_id * spine_per_f1 + i
            gph_index.append(temp)

        f1_interface = {
            "id": intf,
            "description": "fab link from FS %s F1 %s port %s to FS %s F1 %s" % (
                fs_id, f1["id"], intf, peer_fs_id, peer_f1_id),
            "bandwidth": 100 if TOPO_DATA["Size"]["FSs"] <= 2 else 50,
            "mtu": 9000,
            "vrf": 1,
            "type": "fabric_facing",
            "remote_f1_id": remote_f1_id,
            "gph_index": gph_index
        }

        f1_interfaces.append(f1_interface)


    # VLAN config
    vlan_subnet = F1_PUBLIC_SUBNETS.pop(0)
    vlan_prefixlen = str(vlan_subnet.prefixlen)
    host_ips = vlan_subnet.iter_hosts()
    f1_vlan_interface = {
        "id": "vlan2",
        "ip": str(host_ips.next()),
        "netmask": vlan_prefixlen
    }
    f1_interfaces.append(f1_vlan_interface)
    f1_bgp_config["network"] = str(vlan_subnet)

    # Lo0 config
    loopback_subnet = F1_LO_SUBNETS.pop(0)
    loopback_prefixlen = str(loopback_subnet.prefixlen)
    host_ips = loopback_subnet.iter_hosts()
    lo_ip = str(host_ips.next())
    f1_loopback_interface = {
        "id": "lo0",
        "ip": lo_ip,
        "netmask": loopback_prefixlen
    }
    f1_interfaces.append(f1_loopback_interface)

    # F1 BGP Config
    f1_bgp_config["router_id"] = lo_ip

    # F1 Global Config
    f1_global_config = {
        "f1_num": (int(fs_id) - 1) * 2 + f1["id"],
        "f1_ftep": lo_ip,
        "fcp_config": {
            "fcp_hdr_udp_sport": 1,
            "fcp_hdr_udp_dport": 7085,
            "fcp_hdr_v4_etype": 2048,
            "fcp_hdr_ipv4_id": 0,
            "fcp_hdr_ver": 0,
            "fcp_nq_per_tunnel_2power": 3,
            "fcp_blk_size_2power": 7,
            "fcp_req_dscp_ecn": 252,
            "fcp_gnt_dscp_ecn": 248,
            "fcp_data_dscp_ecn": 244
        }
    }

    # Final F1 Config
    F1_CONFIG["global"] = f1_global_config
    F1_CONFIG["intfs"] = f1_interfaces
    F1_CONFIG["bgp"] = f1_bgp_config

    #pretty(F1_CONFIG)
    #import pdb; pdb.set_trace()

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    abs_path =  os.path.join(OUTPUT_DIR, str(rack_id) + '_' + str(fs_id) + '_' + str(f1["id"]) + ".json")

    with open(abs_path, 'w') as outfile:
        json.dump(F1_CONFIG, outfile, indent=4)

def writeCxConfig():
    for k,v in CX_CONFIG.items():
        v += "commit\n"
        abs_path = os.path.join(OUTPUT_DIR, 'Cx-' + str(k) + ".txt")
        with open(abs_path, 'w') as outfile:
            outfile.write(v)

def getCxConfig(cx_id):

    spine_subnet = SPINE_LO_SUBNETS.pop(0)
    spine_lo_ips = spine_subnet.iter_hosts()
    spine_lo_ip = spine_lo_ips.next()

    cx_name = "Cx"+str(cx_id)
    config = "set routing-instances %s instance-type virtual-router\n" % cx_name
    config += "set routing-instanaces %s routing-options router-id %s\n" % (cx_name, str(spine_lo_ip))
    config += "set routing-instances %s routing-options autonomous-system %s\n" % (cx_name, SPINE_AS)
    config += "set routing-instances %s protocols bgp group external-peers type external\n" % cx_name
    config += "set routing-instances %s protocols bgp group external-peers advertise-peer-as\n" % cx_name
    config += "set routing-instances %s protocols bgp group external-peers peer-as %s\n" % (cx_name, F1_AS)

    return config

def pretty(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))

def main():
    global TOPO_DATA, OUTPUT_DIR

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-f', '--file',
                 type=str,
                 help='Topology Definition Json',
                 default='2r1fs4cx.json')
    arg_parser.add_argument('-o', '--output',
                 help='Directory to place config json',
                 default='output')

    args = arg_parser.parse_args()
    OUTPUT_DIR = args.output

    TOPO_DATA = readTopoDefinition(args.file)
    configureTopoSubnets()
    generateAllF1Configs()
    writeCxConfig()


if __name__ == "__main__":
    main()
