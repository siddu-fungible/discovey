# from lib.system.fun_test import *
import os
import json
from netaddr import IPNetwork


TOPO_DEF_FILE = os.path.dirname(os.path.abspath(__file__)) + '/topo_def.json'

PUBLIC_NET = '10.0.0.0/14'
F1_LOOPBACK_NET = '192.0.0.0/8'
F1_SPINE_NET = '193.0.0.0/13'
SPINE_LO_NET = '194.0.0.0/16'

F1_PUBLIC_SUBNET = []
F1_LOOPBACK_SUBNET = []
SPINE_SUBNETS = []
SPINE_LO_SUBNETS = []

SPINE_AS = 64513
F1_AS = 64512

TOPO_DATA = {}
F1_CONFIG = {}


def readTopoDefinition():
    topo_def_data = None
    try:
        topo_def_data = json.loads(open(TOPO_DEF_FILE).read())
        # fun_test.log("TOPO_DEF: %s" % topo_def_data)
    except Exception as ex:
        # fun_test.log(str(ex))
        print ex

    return topo_def_data


def configureTopoSubnets():
    global TOPO_DATA, F1_PUBLIC_SUBNET, F1_LOOPBACK_SUBNET, SPINE_SUBNETS, SPINE_LO_SUBNETS

    nRacks = TOPO_DATA["Size"]["Racks"]
    nLeafs = TOPO_DATA["Size"]["FSs"] * 2
    nSpines = TOPO_DATA["Size"]["Cx"]["Virtual"]

    rack_subnets = []

    all_subnets = IPNetwork(PUBLIC_NET).subnet(24)
    all_subnets.next()
    for i in range(1, nRacks + 1):
        rack_subnets.append(all_subnets.next())
    for rack_subnet in rack_subnets:
        F1_PUBLIC_SUBNET.extend(list(rack_subnet.subnet(28))[:nLeafs])
    del all_subnets

    all_subnets_rack = IPNetwork(F1_LOOPBACK_NET).subnet(24)
    all_subnets_f1 = IPNetwork(all_subnets_rack.next()).subnet(32)
    all_subnets_f1.next()
    for i in range(0, nRacks):
        all_subnets_f1 = IPNetwork(all_subnets_rack.next()).subnet(32)
        all_subnets_f1.next()
        for j in range(0, nLeafs):
            F1_LOOPBACK_SUBNET.append(all_subnets_f1.next())
    del all_subnets_rack
    del all_subnets_f1

    all_subnets = IPNetwork(F1_SPINE_NET).subnet(30)
    for i in range(0, nRacks * nSpines):
        SPINE_SUBNETS.append(all_subnets.next())
    del all_subnets

    all_subnets = IPNetwork(SPINE_LO_NET).subnet(32)
    all_subnets.next()
    for i in range(0, nSpines):
        SPINE_LO_SUBNETS.append(all_subnets.next())


def generateAllF1Configs():
    for rack in TOPO_DATA["Racks"]:
        for fs in rack["FS1600"]:
            for f1 in fs["F1s"]:
                generateF1Config(rack["id"], fs["id"], f1)


def generateF1Config(rack_id, fs_id, f1):

    f1_interfaces = {}
    f1_bgp_config = {
        "as": F1_AS,
        "neighbors": []
    }

    num_of_cx = TOPO_DATA["Size"]["Cx"]["Physical"] if TOPO_DATA["Size"]["Cx"]["Virtual"] == 0 else \
        TOPO_DATA["Size"]["Cx"]["Virtual"]
    spine_per_f1 = num_of_cx / (TOPO_DATA["Size"]["FSs"]*2)

    # Spine facing links
    for idx, Cxlink in enumerate(f1["CxLinks"]):
        fport, cxport = Cxlink["INTERFACES"].items()[0]
        spine_index = (fs_id-1)*(spine_per_f1 * 2) + f1["id"]*spine_per_f1 + idx
        spine_subnet = SPINE_SUBNETS.pop(0)
        host_ips = spine_subnet.iter_hosts()
        my_ip = str(host_ips.next())
        peer_ip = str(host_ips.next())
        f1_interfaces[fport] = {
            "id": fport,
            "description": "spine link from FS %s f1 %s port %s to Cx %s port %s" % (
                fs_id, f1["id"], fport, Cxlink["MGMT_IP"], cxport),
            "bandwidth": "%d" % (100 if TOPO_DATA["Size"]["FSs"] <= 4 else 50),
            "type": "spine_facing",
            "spine_index": spine_index,
            "gph_index": [
                {"index": spine_index}
            ],
            "ip": {
                "my_ip": my_ip,
                "peer_ip": peer_ip
            }
        }
        # BGP Config for Spine Links
        bgp_n = {
            "ip": peer_ip,
            "as": SPINE_AS,
            "next-hop-self": True,
            "allowas-in": True
        }
        f1_bgp_config["neighbors"].append(bgp_n)


    # Fabric facing links
    for intf in sorted(f1["FabLinks"]):
        peer_fs_id, peer_f1_id = f1["FabLinks"][intf].split('_')
        remote_f1_id = (int(peer_fs_id) -1)*2 + int(peer_f1_id)
        gph_index = []
        for i in range(spine_per_f1):
            temp = {}
            temp["index"] = remote_f1_id * spine_per_f1 + i
            gph_index.append(temp)

        f1_interfaces[intf] = {
            "id": intf,
            "description": "fab link from FS %s F1 %s port %s to FS %s F1 %s" % (
                fs_id, f1["id"], intf, peer_fs_id, peer_f1_id),
            "bandwidth": 100 if TOPO_DATA["Size"]["FSs"] <= 4 else 50,
            "type": "fabric_facing",
            "remote_f1_id": remote_f1_id,
            "gph_index": gph_index
        }


    # VLAN config
    vlan_subnet = F1_PUBLIC_SUBNET.pop(0)
    host_ips = vlan_subnet.iter_hosts()
    f1_interfaces["VLAN"] = {
        "id": "vlan2",
        "ip": str(host_ips.next())
    }
    f1_bgp_config["network"] = str(vlan_subnet)

    # Lo0 config
    loopback_subnet = F1_LOOPBACK_SUBNET.pop(0)
    host_ips = loopback_subnet.iter_hosts()
    lo_ip = str(host_ips.next())
    f1_interfaces["lo0"] = {
        "id": "lo0",
        "ip": lo_ip
    }

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

    filename = str(rack_id) + '_' + str(fs_id) + '_' + str(f1["id"])+ ".json"

    with open(filename, 'w') as outfile:
        json.dump(F1_CONFIG, outfile)

def pretty(d, indent=0):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))

def main():

    global TOPO_DATA

    TOPO_DATA = readTopoDefinition()
    configureTopoSubnets()
    generateAllF1Configs()
    #generate_cx_config()



if __name__ == "__main__":
    main()
