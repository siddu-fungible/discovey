from StcIntPythonPL import *
import json
import copy
import xml.etree.ElementTree as etree
import spirent.methodology.utils.pdu_utils as pdu_utils
import spirent.methodology.utils.json_utils as json_utils
from spirent.methodology.utils.rest_client import send_http_request
import spirent.methodology.utils.tag_utils as tag_utils
import spirent.methodology.utils.sql_utils as sql_utils
import spirent.methodology.utils.dyn_obj_utils as dyn_obj_utils
import spirent.core.utils.IfUtils as if_utils
import spirent.methodology.InitRealTimeResultsCommand as InitRtrCmd
import spirent.methodology.utils.data_model_utils as dm_utils
import cmd_json_input

PKG = "spirent.methodology"

# Global values for the Orchestrator IP address and port number for the REST URL
orchestrator_ip = "1.1.1.1"
# Don't specify the port number in the send_http_request; use the default
# url_port = 443
base_url = "gms/rest/"
# Save the session ID after logging in
login_cookie = {}

# West and East config
# TODO This should really be stored in some class structure instead of globals
# Documentation on config:
# app_ip: 10.29.0.61    IPv4 adddress of the appliance so we know what appliace this port is
#                       connected to
# app_if: lan0          Interface name the port is connect to. We assume its a LAN interface
# app_info: {...}       Dict with info on appliance the orchestrator returns to us
# app_if_addr:          Dict with interface addressing info on LAN interface we're connect to
# {
#  "ip": "191.0.0.1",           Use this IP as the device Gateway
#  "mask": 24,
#  "wanNexthop": "191.0.0.2",   Use this IP as the device address
#  "dhcp": false,
#  "lanSide": true,
#  "wanSide": false,
#  "label": "6",
#  "harden": 0,
#  "behindNAT": "none",
#  "maxBW": {}
# }
# active_map_name: map1         I think in SP map name = route policy name
# app_route_policies: [...]     List of route policy objects
# Example route policy object:
# {
#  "priority": "65535",
#  "match": {
#   "acl" : "",
#   "vlan" : "any",
#   "application" : "any",
#   "dscp" : "any",
#   "protocol" : "ip",
#   "src_ip" : "0.0.0.0/0",
#   "dst_ip" : "0.0.0.0/0",
#   "src_port" : "0",
#   "dst_port" : "0"
#  },
#  "actions": {
#   "auto_mod" : "default",
#   "peer" : "",
#   "auto_overlay" : 0,
#   "auto_ena" : false,
#   "drop_ena" : true,
#   "auto_prefif" : "none",
#   "down_action" : "",             Fallback action
#   "tun_pri" : "",
#   "passthru_ena" : false,
#   "passthru_shape_ena" : true
#  },
#  "dest_action": Overlay Name | Drop | Auto Optimized | Pass-Through Unshaped
#                                   The dest_action is parse of the "actions"
#  "expected_rx": True | False      Might want to change this to a port/if name/side at some point
#  "acl_rules": [...]               List of rules in ACL if one is specified in match criteria
# }
# Example acl rule object:
# {
#  "permit": false,         True = permit; False = deny
#  "self": 60,              Priority of rule
#  "comment": "",
#  "application": "http",
#  "protocol": "ip",
#  ...
# }
#
# device_addressing:
# We'll use this dict to store addressing information for devices we create on the port
# After using an address for a device, we'll increment the address if required for the next device
# The ip, prefix and gateway will be taken from the appliance configuration
west_config = {
    "app_ip": "",
    "app_if": "",
    "app_info": {},
    "app_if_addr": {},
    "active_map_name": "",
    "app_route_policies": [],
    "device_addressing": {
        "router_id": "",
        "mac": "00:10:94:00:00:01",
        "ip": "",
        "prefix": "",
        "gateway": ""
    }
}
east_config = {
    "app_ip": "",
    "app_if": "",
    "app_info": {},
    "app_if_addr": {},
    "active_map_name": "",
    "app_route_policies": [],
    "device_addressing": {
        "router_id": "",
        "mac": "00:10:95:00:00:01",
        "ip": "",
        "prefix": "",
        "gateway": ""
    }
}


def send_request(url, headers={}, data=None):
    # Make the HTTP request
    err, response = send_http_request(host=orchestrator_ip,
                                      data_obj=data,
                                      base_url=base_url+url,
                                      delete=False,
                                      entity=url,
                                      use_https=True,
                                      headers=headers)
    if err:
        return err, {}

    # For Testing
    logger = PLLogger.GetLogger('methodology')
    logger.LogInfo(url + " response: " + str(response))

    # We'll assume a non-200 response code is an error
    code = response["code"]
    if code != 200:
        err = "Expecting status code 200 while calling " + entity + \
              ". Instead got " + str(code) + ": " + str(response["body"])
        return err, {}

    return "", response


def send_get(url):
    # Send GET request
    err, response = send_request(url, login_cookie)
    if err:
        return err, {}

    # Load the body as JSON and return it if succesful
    err, body = json_utils.load_json(response["body"])
    if err:
        return err, {}

    return "", body


def orchestrator_login(user_name, password):
    # Initialize parameters
    url = 'authentication/login'
    headers = {'Content-Type': 'application/json'}
    login_json = {
        "user": user_name,
        "password": password,
        "token": ""
    }

    # Send POST request
    err, response = send_request(url, headers, login_json)
    if err:
        return err

    # Save the session ID cookie if one was returned
    set_cookie = response["headers"].get("set-cookie", None)
    if set_cookie:
        global login_cookie
        login_cookie = {"Cookie": set_cookie}

    return ""


def orchestrator_verify_logged_in():
    # Send GET request
    err, body = send_get('authentication/loginStatus')
    if err:
        return err

    # Verify logged in
    logged_in = body.get("isLoggedIn", None)
    if not logged_in:
        return "Not logged in. Status of isLoggedIn: " + str(logged_in)

    return ""


def orchestrator_logout():
    # Send GET request
    # If logout not successful, we'll get back a non-200 error code
    err, response = send_request('authentication/logout', login_cookie)
    return err


def get_user_appliance_config():
    # Get the input from the tagged PDC (these values will be exposed to the user)
    err, cmd = get_tagged_command(PKG + ".ProcessDataCommand", "WestApplianceConfig")
    if err:
        return err
    err, pdc_input = json_utils.load_json(cmd.Get("InputJson"))
    if err:
        return err
    west_app = pdc_input["operation_list"][0]["transfer_data"]["src"]["static_value"]["data"]

    # Save the values in the global west_config object
    global west_config
    west_config["app_ip"] = west_app["west_appliance_ip"]
    west_config["app_if"] = west_app["west_appliance_if_name"]

    # Do the same for the East side...
    err, cmd = get_tagged_command(PKG + ".ProcessDataCommand", "EastApplianceConfig")
    if err:
        return err
    err, pdc_input = json_utils.load_json(cmd.Get("InputJson"))
    if err:
        return err
    east_app = pdc_input["operation_list"][0]["transfer_data"]["src"]["static_value"]["data"]

    global east_config
    east_config["app_ip"] = east_app["east_appliance_ip"]
    east_config["app_if"] = east_app["east_appliance_if_name"]

    # Check values are not empty
    if not west_config["app_ip"] or not east_config["app_ip"] or \
       not west_config["app_if"] or not east_config["app_if"]:
        return "Error: Found empty IP or interface name in East/West appliance configuration"

    # Check if West and East config are the same
    # For now, we'll accept the West and East IPs to be the same
    if west_config["app_ip"] == east_config["app_ip"] and \
       west_config["app_if"] == east_config["app_if"]:
        return "Error: The West and East are both configured with IP " + \
               west_config["app_ip"] + " and interface name " + west_config["app_if"]

    return ""


def orchestrator_get_appliance_info():
    # Get Appliance info
    err, body = send_get('appliance')
    if err:
        return err

    # Look for the appliances in the list
    for appliance in body:
        ip = appliance["ip"]
        key = appliance["nePk"]

        # West
        if ip == west_config["app_ip"]:
            if west_config["app_info"]:
                return "Found more than one appliance with West IP address " + \
                       west_config["app_ip"] + ". Found appliances with primary keys " + \
                       west_config["app_info"]["nePk"] + " and " + key
            global west_config
            # west_config["app_info"]["nePk"] = key
            west_config["app_info"] = appliance
        # East
        if ip == east_config["app_ip"]:
            if east_config["app_info"]:
                return "Found more than one appliance with East IP address " + \
                       east_config["app_ip"] + ". Found appliances with primary keys " + \
                       east_config["app_info"]["nePk"] + " and " + key
            global east_config
            # east_config["app_info"]["nePk"] = key
            east_config["app_info"] = appliance

    # Verify that we found the appliances
    if not west_config["app_info"]:
        return "Error: West appliance with IP " + west_config["app_ip"] + \
               " not found in appliance list"
    if not east_config["app_info"]:
        return "Error: East appliance with IP " + east_config["app_ip"] + \
               " not found in appliance list"

    return ""


def orchestrator_get_appliance_if_addr(config):
    # Get the deployment info for the appliance
    err, body = send_get('deployment/' + config["app_info"]["nePk"])
    if err:
        return err, {}

    # Get interfaces for appliance
    interfaces = body.get("modeIfs", [])
    int_addr_list = []

    # Go through each interface and check if its the one the user configured
    for interface in interfaces:
        if config["app_if"] == interface["ifName"]:
            int_addr_list = interface.get("applianceIPs", [])
            break

    # For now we only handle the one address case
    # TODO Can there be more? Maybe for non-Inline-Router deployments
    if len(int_addr_list) != 1:
        return "For West appliance interface " + config["app_if"] + \
               " found 0 or more than one IP addresses. This case it not handled yet. " + \
               "Expecting only one interface address on LAN side", {}

    return "", int_addr_list[0]


def get_appliance_if_addrs():
    # For each side, get the if addressing info and save it...
    err, if_addr = orchestrator_get_appliance_if_addr(west_config)
    if err:
        return err
    global west_config
    west_config["app_if_addr"] = if_addr

    # Source IP address of Spirent devices/endpoints
    # TODO: Make this configurable so the user can specify to use:
    # - Wan Next Hop (like it currently does)
    # - Automatically determine the IP based on the lan interface address
    # - Manually configure it (using start, step, etc)
    # For now just return an error if the wan next hop is not configured
    west_next_hop = west_config["app_if_addr"]["wanNexthop"]
    if west_next_hop == "" or west_next_hop == "0.0.0.0":
        return "West Wan next hop IP is " + west_next_hop + \
               ". It must be configured to a valid IP address " + \
               "so it can be used for the Spirent endpoint"

    # Fill in addressing info we'll use to create devices
    west_config["device_addressing"]["router_id"] = west_next_hop
    west_config["device_addressing"]["ip"] = west_next_hop
    west_config["device_addressing"]["prefix"] = "24"
    west_config["device_addressing"]["gateway"] = west_config["app_if_addr"]["ip"]

    err, if_addr = orchestrator_get_appliance_if_addr(east_config)
    if err:
        return err
    global east_config
    east_config["app_if_addr"] = if_addr

    # Source IP address of Spirent devices/endpoints
    east_next_hop = east_config["app_if_addr"]["wanNexthop"]
    if east_next_hop == "" or east_next_hop == "0.0.0.0":
        return "East Wan next hop IP is " + east_next_hop + \
               ". It must be configured to a valid IP address " + \
               "so it can be used for the Spirent endpoint"

    # Fill in addressing info we'll use to create devices
    east_config["device_addressing"]["router_id"] = east_next_hop
    east_config["device_addressing"]["ip"] = east_next_hop
    east_config["device_addressing"]["prefix"] = "24"
    east_config["device_addressing"]["gateway"] = east_config["app_if_addr"]["ip"]

    return ""


def verify_acl_rule_match_criteria_is_supported(acl):
    # Supported ACL Match Critera:
    # IP Intelligence
    #   either_service, src_service, dst_service
    # Domain
    #   either_dns, src_dns, dst_dns
    # Geo Location
    #   either_geo, src_geo, dst_geo
    # Application (can be any)
    #   application
    # Interface (can be any)
    #   vlan
    # Protocol
    #   protocol
    # DSCP (can be any)
    #   dscp
    # IP/Subnet
    #   src_ip, dst_ip
    # Port (only when protocol=tcp|udp; can be 0)
    #   either_port, src_port, dst_port

    # For now we'll support
    # protocol = ip | tcp | udp
    # either_port, src_port, dst_port > 0

    unsupported_names = ["IP Intelligence", "IP Intelligence", "IP Intelligence",
                         "Domain", "Domain", "Domain",
                         "Geo Location", "Geo Location", "Geo Location",
                         "IP/Subnet", "IP/Subnet"]
    unsupported_keys = ["either_service", "src_service", "dst_service",
                        "either_dns", "src_dns", "dst_dns",
                        "either_geo", "src_geo", "dst_geo",
                        "src_ip", "dst_ip"]

    for i, unsupported in enumerate(unsupported_keys):
        if acl.get(unsupported, "") != "":
            return unsupported_names[i] + " match criteria currently not supported"

    application = acl.get("application", "")
    if application != "" and application != "any" and application != "http":
        return "Application match criteria " + application + " currently not supported"

    interface = acl.get("vlan", "")
    if interface != "" and interface != "any":
        return "Interface match criteria " + interface + " currently not supported"

    protocol = acl.get("protocol", "")
    if protocol != "" and protocol != "ip" and protocol != "tcp" and protocol != "udp":
        return "Supported Protocol match criteria are ip, tcp and udp. " + \
               "All others currently not supported"

    dscp = acl.get("dscp", "")
    if dscp != "" and dscp != "any":
        return "DSCP match criteria " + dscp + " currently not supported"

    return ""


def orchestrator_get_appliance_acl(config, acl_name):
    # Return the specified ACL from an appliance or error if not found
    # TODO for now we get the cached data; might want to make this user configurable
    err, body = send_get('acls/' + config["app_info"]["nePk"] + '?cached=true')
    if err:
        return err, []

    if acl_name not in body:
        return "ACL " + acl_name + " does not exist in list of appliance ACL's. " + \
               "Please check that it exists and has at least one rule", []

    acl_rules = []
    for priority in body[acl_name]["entry"].keys():
        # Note that priority value is in the "self" key in the acl rule
        acl_rule = body[acl_name]["entry"][priority]

        # Verify ACL has match criteria that we support
        # Return an error if we find critera that we don't support/parse
        err = verify_acl_rule_match_criteria_is_supported(acl_rule)
        if err:
            return err, []

        acl_rules.append(acl_rule)

    return "", acl_rules


def orchestrator_get_appliance_route_policies(config):
    # Get the route maps/policies for the appliance
    # TODO for now we get the cached data; might want to make this user configurable
    err, body = send_get('routeMaps/' + config["app_info"]["nePk"] + '?cached=true')
    if err:
        return err, "", []

    # Get the active map
    active_map = body["options"]["activeMap"]

    # Find the active map in the data section
    map = body["data"].get(active_map, None)
    if map is None:
        return "Error: did not find active map " + active_map + " in routeMaps data object", "", []

    # Go through list of route maps/policies and save the info
    route_policies = []
    for priority in map["prio"].keys():
        route_policy = {}
        route_policy["priority"] = priority
        # In the match and set dicts, there's a "0" key; Is there situations with other values?
        route_policy["match"] = map["prio"][priority]["match"]["0"]
        route_policy["actions"] = map["prio"][priority]["set"]["0"]
        # Is there an ACL specified in the match criteria?
        acl_name = route_policy["match"].get("acl", "")
        if acl_name:
            # Get and save rules for specified ACL
            err, acl_rules = orchestrator_get_appliance_acl(config, acl_name)
            if err:
                return err, "", []
            route_policy["acl_rules"] = acl_rules

        # Each policy will have some actions (Destination, Path, Fallback)
        # Destination actions include:
        # auto optimized, pass-through, pass-through-unshaped and overlay
        # For now to determine if the traffic is expected to be received,
        # we'll only consider the "drop_ena" key
        policy_dest = "Unknown"
        expected_rx = "True"
        if route_policy["actions"]["auto_mod"] == "overlay":
            policy_dest = "Overlay " + str(route_policy["actions"]["auto_overlay"])
        elif route_policy["actions"]["drop_ena"]:
            policy_dest = "Drop"
            # For now we'll only consider the Drop destination to not rx the traffic
            expected_rx = "False"
        elif route_policy["actions"]["auto_ena"]:
            policy_dest = "Auto Optimized"
        elif route_policy["actions"]["passthru_ena"] and \
                route_policy["actions"]["passthru_shape_ena"]:
            policy_dest = "Pass-Through"
        elif route_policy["actions"]["passthru_ena"] and \
                not route_policy["actions"]["passthru_shape_ena"]:
            policy_dest = "Pass-Through Unshaped"
        route_policy["dest_action"] = policy_dest
        route_policy["expected_rx"] = expected_rx

        # Append the policy to the route policies list
        route_policies.append(route_policy)

    return "", active_map, route_policies


def get_appliance_route_policies():
    # For each side, get through the route maps/policies and save the match/actions/acls
    err, map_name, route_policies = orchestrator_get_appliance_route_policies(west_config)
    if err:
        return err
    global west_config
    west_config["active_map_name"] = map_name
    west_config["app_route_policies"] = route_policies

    err, map_name, route_policies = orchestrator_get_appliance_route_policies(east_config)
    if err:
        return err
    global east_config
    east_config["active_map_name"] = map_name
    east_config["app_route_policies"] = route_policies

    return ""


def run(tagname, b, params):
    logger = PLLogger.GetLogger('methodology')
    logger.LogInfo("Running configure_traffic script")

    # Load input params as JSON
    err, input = json_utils.load_json(params)
    if err != '':
        return "Failed parsing script JSON input: " + str(err)

    # Get input params
    global orchestrator_ip
    orchestrator_ip = input["orchestrator_ip"]
    user_name = input["user_name"]
    password = input["password"]
    traffic_load = input["traffic_load"]

    # Login to orchestrator
    err = orchestrator_login(user_name, password)
    if err:
        return err

    # Verify logged in
    err = orchestrator_verify_logged_in()
    if err:
        return err

    # Get user configuration for connected appliances
    err = get_user_appliance_config()
    if err:
        return err

    # Get appliances information from the orchestrator
    err = orchestrator_get_appliance_info()
    if err:
        return err
    # logger.LogError("West appliance key: " + west_config["app_info"]["nePk"])
    # logger.LogError("East appliance key: " + east_config["app_info"]["nePk"])

    # Update the RT Policy table titles
    err = set_rt_table_titles()
    if err:
        return err

    # Get addressing info for appliance interfaces
    err = get_appliance_if_addrs()
    if err:
        return err
    # logger.LogError("West int addr: " + str(west_config["app_if_addr"]))
    # logger.LogError("East int addr: " + str(east_config["app_if_addr"]))

    # Get appliance route maps/policies and acl's that are used in match criteria
    err = get_appliance_route_policies()
    if err:
        return err
    # logger.LogError("West route policies: " + str(west_config["app_route_policies"]))
    # logger.LogError("East route policies: " + str(east_config["app_route_policies"]))

    # Logout of orchestrator
    err = orchestrator_logout()
    if err:
        return err

    # Create Devices
    err = create_devices_for_traffic()
    if err:
        return err

    # Create Traffic Stream Blocks
    # err = create_stream_blocks(traffic_load)
    # if err:
    #     return err

    # First determine if we should create traffic for the default route policies
    err, traffic_default_policies = dyn_obj_utils.get_variable("TrafficDefaultPolicies")
    traffic_default_policies = True if err else traffic_default_policies.get("data", True)

    err, west_sb_name_list = create_traffic_from_route_policies(west_config, "West",
                                                                "East", traffic_load,
                                                                traffic_default_policies)
    if err:
        return err
    err, east_sb_name_list = create_traffic_from_route_policies(east_config, "East",
                                                                "West", traffic_load,
                                                                traffic_default_policies)
    if err:
        return err

    # Kind of a HACK here...
    # We need to do this because tables are not created if no data is created/sourced
    # Should look into fixing dst db_table in PDC to create empty tables if src data is empty
    err, traffic_west_east_enabled = dyn_obj_utils.get_variable("EnableCreateTrafficWestEast")
    if err:
        return err
    traffic_west_east_enabled = traffic_west_east_enabled["data"]
    err, traffic_east_west_enabled = dyn_obj_utils.get_variable("EnableCreateTrafficEastWest")
    if err:
        return err
    traffic_east_west_enabled = traffic_east_west_enabled["data"]
    # Set the flag so we know if traffic was created or not
    # Will be used later when we verify traffic and create tables
    enable_create_traffic = True
    if not traffic_west_east_enabled and not traffic_east_west_enabled:
        enable_create_traffic = False
    dyn_obj_utils.set_variable("EnableCreateTraffic",
                               {"format": "scalar", "data": enable_create_traffic})

    # Update the Init RT traffic tags list
    err = set_rt_traffic_tags(east_sb_name_list, west_sb_name_list)
    if err:
        return err

    # Create Protocol Devices
    # TODO: This is kinda of a hack; this should combined with traffic/stream blocks above
    #       and made into one function to process all policies and create what's needed

    # First set the HttpEnabled flag to False
    dyn_obj_utils.set_variable("HttpEnabled", {"format": "scalar", "data": False})

    err = create_protocols_from_route_policies()
    if err:
        return err

    # Another HACK...
    # Policies tables will be empty if no traffic and no HTTP
    # Should fix the table creation so it creates the empty dst table if src tables are empty
    err, http_enabled = dyn_obj_utils.get_variable("HttpEnabled")
    if err:
        return err
    http_enabled = http_enabled["data"]
    create_policies_table = bool(enable_create_traffic or http_enabled)
    dyn_obj_utils.set_variable("CreatePoliciesTable",
                               {"format": "scalar", "data": create_policies_table})

    return ""


# Increment the addressing in the device_addressing structure
# so it can be assigned to the next device created
# This is also part of the hack to create protocol devices
def increment_device_addressing():
    # Update the West side...
    global west_config
    west = west_config["device_addressing"]

    # Increment the source IP address and router id
    ip = if_utils.GetNextIPAddress(west["ip"], "0.0.0.1", 1, west["prefix"])
    if ip == "":
        return "An error occured while incrementing the source IPv4 device address"
    west["router_id"] = ip
    west["ip"] = ip

    # Increment the source MAC
    west["mac"] = if_utils.GetNextMacAddress(west["mac"], 48, 1, 1)

    # Update the East side...
    global east_config
    east = east_config["device_addressing"]

    # Increment the source IP address and router id
    ip = if_utils.GetNextIPAddress(east["ip"], "0.0.0.1", 1, east["prefix"])
    if ip == "":
        return "An error occured while incrementing the source IPv4 device address"
    east["router_id"] = ip
    east["ip"] = ip

    # Increment the source MAC
    east["mac"] = if_utils.GetNextMacAddress(east["mac"], 48, 1, 1)

    return ""


# After expanding StreamBlock's, the name gets appended with '-1'
# We'll remove it so it matches the names we configured
def run_fix_streamblock_names(tagname, b, params):
    # Get list of ports under project
    project = CStcSystem.Instance().GetObject('Project')
    port_list = project.GetObjects("Port")
    if len(port_list) == 0:
        return ""

    # Get all StreamBlocks
    sb_list = []
    for port in port_list:
        sb_list += port.GetObjects("StreamBlock")

    # Remove the "-1" if it exists
    for sb in sb_list:
        name = sb.Get("Name")
        if name[len(name)-2:] == "-1":
            name = name[:len(name)-2]
            sb.Set("Name", name)

    return ""


def get_tagged_command(cmd_class, tag_name):
    cmd_list = tag_utils.get_tagged_objects_from_string_names(tag_name,
                                                              class_name=cmd_class)
    if len(cmd_list) != 1:
        return "Found " + str(len(cmd_list)) + " commands matching tag " + tag_name + \
               ". Expecting exactly one command to be found"

    return "", cmd_list[0]


def set_rt_table_titles():
    # Get the current InitRT cmd json input
    err, cmd = get_tagged_command(PKG + ".InitRealTimeResultsCommand", "InitRtTableResults")
    if err:
        return err
    err, init_input = json_utils.load_json(cmd.Get("InputJson"))
    if err:
        return err

    # First list item is East to West
    host_name = east_config["app_info"]["hostName"]
    if host_name:
        host_name = " (" + host_name + ")"
    title = "Policies on " + east_config["app_ip"] + host_name + ": East to West"
    init_input[0]["definition"]["title"] = title

    # Second list item is West to East
    host_name = west_config["app_info"]["hostName"]
    if host_name:
        host_name = " (" + host_name + ")"
    title = "Policies on " + west_config["app_ip"] + host_name + ": West to East"
    init_input[1]["definition"]["title"] = title

    # Set the json input with the correct titles
    cmd.Set('InputJson', json.dumps(init_input))
    return ""


def set_rt_traffic_tags(east_sb_names, west_sb_names):
    # Get the current InitRT cmd json input
    err, cmd = get_tagged_command(PKG + ".InitRealTimeResultsCommand", "InitRtTrafficResults")
    if err:
        return err

    # Initialize empty init rt input list
    init_input = []

    # East side chart
    east_init_traffic = cmd_json_input.get_init_rt_traffic()
    east_init_traffic["result_id"] = "chart_traffic_east_west"
    east_init_traffic["definition"]["title"]["text"] = "East to West Traffic Streams"
    for i, name in enumerate(east_sb_names):
        east_sb_names[i] = name + "_ttStreamBlock"
    east_init_traffic["subscribe"][0]["result_parent_tags"] = east_sb_names
    east_init_traffic["subscribe"][1]["result_parent_tags"] = east_sb_names
    init_input.append(east_init_traffic)

    # West side chart
    west_init_traffic = cmd_json_input.get_init_rt_traffic()
    west_init_traffic["result_id"] = "chart_traffic_west_east"
    west_init_traffic["definition"]["title"]["text"] = "West to East Traffic Streams"
    for i, name in enumerate(west_sb_names):
        west_sb_names[i] = name + "_ttStreamBlock"
    west_init_traffic["subscribe"][0]["result_parent_tags"] = west_sb_names
    west_init_traffic["subscribe"][1]["result_parent_tags"] = west_sb_names
    init_input.append(west_init_traffic)

    # Set the json input in the command
    cmd.Set('InputJson', json.dumps(init_input))
    return ""


def create_devices_for_traffic():
    # Configure West Device JSON
    west = cmd_json_input.get_device_template_config()
    west["tagPrefix"] = "West_"
    west_ipv4_oplist = west["modifyList"][1]["operationList"]
    # RouterId
    # west_ipv4_oplist[1]["stmPropertyModifier"]["propertyValueList"]["Start"] = "192.0.0.1"
    west_ipv4_oplist[1]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
        west_config["device_addressing"]["router_id"]
    # Gateway
    # west_ipv4_oplist[3]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
    #     west_config["app_if_addr"]["ip"]
    west_ipv4_oplist[3]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
        west_config["device_addressing"]["gateway"]
    # IP Source Address
    # west_next_hop = west_config["app_if_addr"]["wanNexthop"]
    # west_ipv4_oplist[4]["stmPropertyModifier"]["propertyValueList"]["Start"] = west_next_hop
    west_ipv4_oplist[4]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
        west_config["device_addressing"]["ip"]
    # Netmask
    west_ipv4_oplist[5]["propertyValue"]["propertyValueList"]["PrefixLength"] = \
        west_config["device_addressing"]["prefix"]
    # MAC
    west_source_mac_modifier = west["modifyList"][2]["operationList"][0]["stmPropertyModifier"]
    # west_source_mac_modifier["propertyValueList"]["Start"] = "00:10:94:00:00:01"
    west_source_mac_modifier["propertyValueList"]["Start"] = \
        west_config["device_addressing"]["mac"]

    # Configure East Device JSON
    east = cmd_json_input.get_device_template_config()
    east["tagPrefix"] = "East_"
    east_ipv4_oplist = east["modifyList"][1]["operationList"]
    # RouterId
    # east_ipv4_oplist[1]["stmPropertyModifier"]["propertyValueList"]["Start"] = "193.0.0.1"
    east_ipv4_oplist[1]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
        east_config["device_addressing"]["router_id"]
    # Gateway
    # east_ipv4_oplist[3]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
    #     east_config["app_if_addr"]["ip"]
    east_ipv4_oplist[3]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
        east_config["device_addressing"]["gateway"]
    # IP Source Address
    # east_next_hop = east_config["app_if_addr"]["wanNexthop"]
    # east_ipv4_oplist[4]["stmPropertyModifier"]["propertyValueList"]["Start"] = east_next_hop
    east_ipv4_oplist[4]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
        east_config["device_addressing"]["ip"]
    # Netmask
    east_ipv4_oplist[5]["propertyValue"]["propertyValueList"]["PrefixLength"] = \
        east_config["device_addressing"]["prefix"]
    # MAC
    east_source_mac_modifier = east["modifyList"][2]["operationList"][0]["stmPropertyModifier"]
    # east_source_mac_modifier["propertyValueList"]["Start"] = "00:10:95:00:00:01"
    east_source_mac_modifier["propertyValueList"]["Start"] = \
        east_config["device_addressing"]["mac"]

    # Increment device addressing so its ready for next device
    err = increment_device_addressing()
    if err:
        return err

    # Configure the InputJson in CreateTemplateConfigCommand for the West endpoint
    err, cmd = get_tagged_command(PKG + ".CreateTemplateConfigCommand", "CreateWestEndpoint")
    if err:
        return err
    cmd.Set('InputJson', json.dumps(west))

    # Configure the InputJson in CreateTemplateConfigCommand for the East endpoint
    err, cmd = get_tagged_command(PKG + ".CreateTemplateConfigCommand", "CreateEastEndpoint")
    if err:
        return err
    cmd.Set('InputJson', json.dumps(east))

    return ""


# This was initially used for testing. Currently not used
# Instead, create_traffic_from_route_policies() is used to configure traffic on each side
def create_stream_blocks(traffic_load=10):
    # Get Traffic Mix input JSON
    traffic_mix = cmd_json_input.get_traffic_mix_config()

    # Update the load
    traffic_mix["load"] = traffic_load

    # Set the CreateTrafficMixCommand MixInfo property
    err, cmd = get_tagged_command(PKG + ".traffic.CreateTrafficMixCommand", "CreateTrafficMixCmd")
    if err:
        return err
    cmd.Set('MixInfo', json.dumps(traffic_mix))

    return ""


def create_traffic_from_route_policies(config, src_side="West", dst_side="East",
                                       traffic_load=10, traffic_default_policies=True):

    # TODO verify src_side and dst_side is "West" or "East"

    # Create new table in DB for route policies
    table_name = "Policies" + src_side + "To" + dst_side
    create_table = "CREATE TABLE IF NOT EXISTS " + table_name + \
        " (ID INTEGER PRIMARY KEY, " + \
        "SbName TEXT, " + \
        "MapName TEXT, " + \
        "PolicyPriority INTEGER, " + \
        "AclName TEXT, " + \
        "AclPriority INTEGER, " + \
        "AclPermit TEXT, " + \
        "PolicyDest TEXT, " + \
        "ExpectedRx TEXT)"
    err_str, data = sql_utils.run_sql_on_db_name("SUMMARY", create_table)
    if err_str:
        return "Error creating DB table for route policies: " + err_str, []

    # Base traffic mix config
    traffic_mix = {
        "load": traffic_load,
        "loadUnits": "PERCENT_LINE_RATE",
        "table": []
    }
    streamblock_name_list = []

    for policy in config["app_route_policies"]:
        priority = policy["priority"]
        acl_name = policy["match"].get("acl", "")

        # If the default route policy
        if priority == "65535":
            # Ignore if we're not creating traffic for the default policy
            if not traffic_default_policies:
                continue

            # Verify acl is empty
            if acl_name:
                return "Expecting the default policy with priority 65535 to have no ACL. " + \
                       "Instead, got ACL " + acl_name, []

            # Create traffix mix component
            name = src_side + "_Default_Policy"
            err_str, component = create_traffic_mix_component(name, src_side, dst_side, None)
            if err_str:
                    return "TODO: " + err_str, []
            traffic_mix["table"].append(component)
            streamblock_name_list.append(name)

            # Insert the policy into the table
            err_str = insert_policy_into_db_table(name, table_name, config["active_map_name"],
                                                  policy, None)
            if err_str:
                return err_str, []
        else:
            # If not default, verify an acl is specified
            if not acl_name:
                return "Currently only route policies with match " + \
                       "criteria using an ACL are supported", []

            # Go through list of rules in ACL
            for acl_rule in policy["acl_rules"]:
                # TODO Support case where permit=False (deny)
                #      Does that mean traffic on this ACL is not expected to be received?
                # if acl_rule["permit"] != True:
                #     return "Policy with priority " + priority + " and ACL " + acl_name + \
                #            " has rule with priority " + str(acl_rule["self"]) + \
                #            " with permit set to " + str(acl_rule["permit"]) + \
                #            ". Currently only permit = True supported"

                # Ignore all ACL's with application (this is only for traffic creation)
                application = acl_rule.get("application", "")
                if application != "" and application != "any":
                    continue

                # Create traffix mix component
                name = src_side + "_ACL_" + str(acl_rule["self"])
                err_str, component = create_traffic_mix_component(name, src_side,
                                                                  dst_side, acl_rule)
                if err_str:
                    return "TODO: " + err_str, []
                traffic_mix["table"].append(component)
                streamblock_name_list.append(name)

                # Insert the policy into the table
                err_str = insert_policy_into_db_table(name, table_name, config["active_map_name"],
                                                      policy, acl_rule)
                if err_str:
                    return err_str, []

    # Update weights in traffic mix to all be equal
    num_components = len(traffic_mix["table"])
    if num_components > 0:
        weight = truncate(100.0/num_components, 1) + " %"
        for component in traffic_mix["table"]:
            component["weight"] = weight

    # We need to surround the CreateTrafficMix in an if as enable=false and 0 table elements
    # doens't actually work. The command errors out
    variable_name = "EnableCreateTraffic" + src_side + dst_side
    dyn_obj_utils.set_variable(variable_name, {"format": "scalar", "data": bool(num_components)})

    # Set the CreateTrafficMixCommand MixInfo property
    traffic_mix_cmd_tag = "CreateTrafficMix" + src_side + dst_side
    err, cmd = get_tagged_command(PKG + ".traffic.CreateTrafficMixCommand", traffic_mix_cmd_tag)
    if err:
        return err, []
    cmd.Set('MixInfo', json.dumps(traffic_mix))

    return "", streamblock_name_list


def create_traffic_mix_component(streamblock_name, src_side, dst_side, acl):
    component = copy.deepcopy(cmd_json_input.get_traffic_mix_component())

    # Add tag prefix
    component["tagPrefix"] = streamblock_name + "_"
    # Set the StreamBlock name
    oper_list = component["modifyList"][0]["operationList"]
    oper_list[0]["propertyValue"]["propertyValueList"]["Name"] = streamblock_name

    # Process the ACL if one was specified
    if acl:
        # Create the frame config string
        err, frame_config = create_streamblock_frame_config_from_acl(acl)
        if err:
            return err, {}

        # Create the modify operation and append it to the modifyList
        modify_frame_config = {
            "propertyValue": {
                "className": "StreamBlock",
                "tagName": "ttStreamBlock",
                "propertyValueList": {
                    "FrameConfig": frame_config
                }
            }
        }
        oper_list.append(modify_frame_config)

    tag = src_side + "_ttIpv4If"
    endpoint = component["postExpandModify"][0]["streamBlockExpand"]["endpointMapping"]
    endpoint["srcBindingTagList"].append(tag)
    tag = dst_side + "_ttIpv4If"
    endpoint["dstBindingTagList"].append(tag)
    return "", component


# TODO This function is not written that well. Refactor it so it doesn't duplicate code
def create_streamblock_frame_config_from_acl(acl):
    if not acl:
        return "Error creating frame config. Must pass in valid ACL object to process", ""

    # Get the IP frame config and convert to JSON
    root = etree.fromstring(get_ipv4_stream_frame_config())
    err, pdu_json = pdu_utils.pdu_xml_to_json(root)
    if err:
        return err, ""

    # Get the port number if its specified
    src_port = 0
    dst_port = 0
    either_port = acl.get("either_port", "")
    if either_port and either_port != "0":
        # First use either_port key if its specified
        src_port = either_port
        dst_port = either_port
    else:
        # Else look for src_port and dst_port keys
        port = acl.get("src_port", "")
        if port and port != "0":
            src_port = port
        port = acl.get("dst_port", "")
        if port and port != "0":
            dst_port = port

    protocol = acl.get("protocol", "")
    # For protocol ip don't need to do anything
    if protocol == "udp":
        udp = get_pdu_obj()
        udp["pdu"] = "udp:Udp"
        udp["name"] = "udp1"
        if src_port:
            udp["property_data"]["sourcePort"] = {"sourcePort": src_port, "override": "true"}
        if dst_port:
            udp["property_data"]["destPort"] = {"destPort": dst_port, "override": "true"}
        pdu_json["pdu_list"].append(udp)
    elif protocol == "tcp":
        tcp = get_pdu_obj()
        tcp["pdu"] = "tcp:Tcp"
        tcp["name"] = "tcp1"
        # TODO Refactor this code with udp protocol so there's no duplicate code
        if src_port:
            tcp["property_data"]["sourcePort"] = {"sourcePort": src_port, "override": "true"}
        if dst_port:
            tcp["property_data"]["destPort"] = {"destPort": dst_port, "override": "true"}
        pdu_json["pdu_list"].append(tcp)

    return "", etree.tostring(pdu_utils.json_to_pdu_xml(pdu_json))


def insert_policy_into_db_table(sb_name, table_name, map_name, policy, acl_rule):
    # If it exists get ACL info
    if acl_rule:
        acl_name = policy["match"].get("acl")
        acl_permit = str(acl_rule["permit"])
        acl_priority = str(acl_rule["self"])
    else:
        acl_name = "N/A"
        acl_permit = "N/A"
        acl_priority = "N/A"

    # Create INSERT statement and run on SQL DB
    insert = "INSERT INTO " + table_name + \
             "(SbName, MapName, PolicyPriority, AclName, AclPriority, AclPermit, " + \
             "PolicyDest, ExpectedRx) VALUES ('" + \
             sb_name + "', '" + map_name + "', " + policy["priority"] + ", '" + \
             acl_name + "', '" + \
             acl_priority + "', '" + acl_permit + \
             "', '" + policy["dest_action"] + "', '" + policy["expected_rx"] + "')"
    err_str, data = sql_utils.run_sql_on_db_name("SUMMARY", insert)
    if err_str:
        return "Error inserting into DB table: " + err_str

    return ""


def create_protocols_from_route_policies():
    # Base protocol mix config's
    west_proto_mix = {
        "deviceCount": 0,
        "table": []
    }
    east_proto_mix = {
        "deviceCount": 0,
        "table": []
    }

    # Go through West side policies
    err, west_mixes, east_mixes = create_proto_mix_components_from_route_policies(
        west_config, east_config, src_side="West", dst_side="East")
    # Append proto mix components to master list for West and East sides
    west_proto_mix["deviceCount"] = west_proto_mix["deviceCount"] + len(west_mixes)
    west_proto_mix["table"].extend(west_mixes)
    east_proto_mix["deviceCount"] = east_proto_mix["deviceCount"] + len(east_mixes)
    east_proto_mix["table"].extend(east_mixes)

    # Go through East side policies
    err, east_mixes, west_mixes = create_proto_mix_components_from_route_policies(
        east_config, west_config, src_side="East", dst_side="West")
    # Append proto mix components to master list for West and East sides
    west_proto_mix["deviceCount"] = west_proto_mix["deviceCount"] + len(west_mixes)
    west_proto_mix["table"].extend(west_mixes)
    east_proto_mix["deviceCount"] = east_proto_mix["deviceCount"] + len(east_mixes)
    east_proto_mix["table"].extend(east_mixes)

    # Configure West side protocol mix
    if len(west_proto_mix["table"]) > 0:
        err, cmd = get_tagged_command(PKG + ".CreateProtocolMixCommand",
                                      "CreateWestProtocolMix")
        if err:
            return err
        cmd.Set('MixInfo', json.dumps(west_proto_mix))

    # Configure East side protocol mix
    if len(east_proto_mix["table"]) > 0:
        err, cmd = get_tagged_command(PKG + ".CreateProtocolMixCommand",
                                      "CreateEastProtocolMix")
        if err:
            return err
        cmd.Set('MixInfo', json.dumps(east_proto_mix))

    return ""


def create_proto_mix_components_from_route_policies(src_config, dst_config,
                                                    src_side="West", dst_side="East"):
    # Protocol mix config components
    src_proto_mix_list = []
    dst_proto_mix_list = []

    # Add policy to Policies table (we assumed table was already created)
    table_name = "Policies" + src_side + "To" + dst_side

    for policy in src_config["app_route_policies"]:
        # priority = policy["priority"]
        acl_name = policy["match"].get("acl", "")

        if not acl_name:
            continue

        # Go through list of rules in ACL
        for acl_rule in policy["acl_rules"]:
            # TODO Support case where permit=False (deny)
            #      Does that mean traffic on this ACL is not expected to be received?
            # if acl_rule["permit"] != True:
            #     return "Policy with priority " + priority + " and ACL " + acl_name + \
            #            " has rule with priority " + str(acl_rule["self"]) + \
            #            " with permit set to " + str(acl_rule["permit"]) + \
            #            ". Currently only permit = True supported", [], []

            application = acl_rule.get("application", "")
            if application == "" or application == "any":
                continue

            # For now we're only doing HTTP...
            if application == "http":
                # Create an HTTP device...
                name = src_side + "_ACL_" + str(acl_rule["self"]) + "_HTTP"

                # Enable the HTTP flag so relations are created (later on in the sequencer)
                dyn_obj_utils.set_variable("HttpEnabled", {"format": "scalar", "data": True})

                # Client side...

                client = copy.deepcopy(cmd_json_input.get_proto_mix_component())
                # client["tagPrefix"] = src_side + "_HTTP_"
                client["tagPrefix"] = "HTTP_Client_"

                client_ipv4 = client["modifyList"][1]["operationList"]
                # RouterId
                client_ipv4[1]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
                    src_config["device_addressing"]["router_id"]
                # Gateway
                client_ipv4[3]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
                    src_config["device_addressing"]["gateway"]
                # IP Source Address
                client_ipv4[4]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
                    src_config["device_addressing"]["ip"]
                # Netmask
                client_ipv4[5]["propertyValue"]["propertyValueList"]["PrefixLength"] = \
                    src_config["device_addressing"]["prefix"]
                # MAC
                client_mac = client["modifyList"][2]["operationList"][0]["stmPropertyModifier"]
                client_mac["propertyValueList"]["Start"] = src_config["device_addressing"]["mac"]
                # Device Name
                client_name = client["modifyList"][5]["operationList"][0]
                client_name["propertyValue"]["propertyValueList"]["Name"] = name

                http_client = {
                    "enable": True,
                    "description": "Add HTTP Client",
                    "operationList": [
                        {
                            "merge": {
                                "mergeSourceTag": "ttHttpClientProtocolConfig",
                                "mergeSourceTemplateFile": "Http_Protocol.xml",
                                "mergeTargetTag": "ttEmulatedDevice"
                            }
                        }
                    ]
                }
                client["modifyList"].append(http_client)

                # src_proto_mix["table"].append(client)
                # src_proto_mix["deviceCount"] = src_proto_mix["deviceCount"] + 1
                src_proto_mix_list.append(client)

                # Server side...

                server = copy.deepcopy(cmd_json_input.get_proto_mix_component())
                # server["tagPrefix"] = dst_side + "_HTTP_"
                server["tagPrefix"] = "HTTP_Server_"

                server_ipv4 = server["modifyList"][1]["operationList"]
                # RouterId
                server_ipv4[1]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
                    dst_config["device_addressing"]["router_id"]
                # Gateway
                server_ipv4[3]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
                    dst_config["device_addressing"]["gateway"]
                # IP Source Address
                server_ipv4[4]["stmPropertyModifier"]["propertyValueList"]["Start"] = \
                    dst_config["device_addressing"]["ip"]
                # Netmask
                server_ipv4[5]["propertyValue"]["propertyValueList"]["PrefixLength"] = \
                    dst_config["device_addressing"]["prefix"]
                # MAC
                server_mac = server["modifyList"][2]["operationList"][0]["stmPropertyModifier"]
                server_mac["propertyValueList"]["Start"] = dst_config["device_addressing"]["mac"]
                # Device Name
                server_name = server["modifyList"][5]["operationList"][0]
                server_name["propertyValue"]["propertyValueList"]["Name"] = name

                http_server = {
                    "enable": True,
                    "description": "Add HTTP Server",
                    "operationList": [
                        {
                            "merge": {
                                "mergeSourceTag": "ttHttpServerProtocolConfig",
                                "mergeSourceTemplateFile": "Http_Protocol.xml",
                                "mergeTargetTag": "ttEmulatedDevice"
                            }
                        }
                    ]
                }

                server["modifyList"].append(http_server)

                # dst_proto_mix["table"].append(server)
                # dst_proto_mix["deviceCount"] = dst_proto_mix["deviceCount"] + 1
                dst_proto_mix_list.append(server)

                # Increment device addressing so its ready for next device
                err = increment_device_addressing()
                if err:
                    return err, [], []

                # Insert the policy into the table
                err_str = insert_policy_into_db_table(name, table_name,
                                                      src_config["active_map_name"],
                                                      policy, acl_rule)
                if err_str:
                    return err_str, [], []
            else:
                # Unsupported application type
                logger.LogWarn("Unsupported application found: " + application)

    return "", src_proto_mix_list, dst_proto_mix_list


# When multiple client and server devices are created, the ConfigRelationCommand
# doesn't work in Pair mode because it seems to config relations based on the order
# of creation. We'll manually do it here for the ConnectionDestination relation
def configure_http_client_server_relation(tagname, b, params):
    # Get list of http client and server devices
    client_list = tag_utils.get_tagged_objects_from_string_names(["HTTP_Client_ttEmulatedDevice"])
    server_list = tag_utils.get_tagged_objects_from_string_names(["HTTP_Server_ttEmulatedDevice"])

    # There's probably a better/more effient way of doing this but for now it works
    for client in client_list:
        client_name = client.Get("Name")
        for server in server_list:
            if client_name == server.Get("Name"):
                # Create the "Connected Server" relation between the client and server
                http_client = client.GetObject("HttpClientProtocolConfig",
                                               RelationType("ParentChild"))
                http_server = server.GetObject("HttpServerProtocolConfig",
                                               RelationType("ParentChild"))
                http_client.AddObject(http_server, RelationType("ConnectionDestination"))

    return ""


# Find the HttpClientResults under the HTTP Emulated Devices
# and name the objects with the same name as the device
# so the results have a unique name, used to identify them
def add_names_to_http_results(tagname, b, params):
    # Subscribe to HTTP results
    result_subscribe_list = [
        {
            "config_type": "HttpClientProtocolConfig",
            "result_type": "HttpClientResults",
            "view_attribute_list": ["AbortedTransactions"],
            "result_parent_tags": ["HTTP_Client_ttHttpClientProtocolConfig"],
            "interval": "3"
        }
    ]
    err = InitRtrCmd.Subscribe(result_subscribe_list)
    if err:
        return err

    # Go through HTTP client devices
    devices = tag_utils.get_tagged_objects_from_string_names(["HTTP_Client_ttEmulatedDevice"])
    for device in devices:
        # Get the HttpClientResults object under the client device
        err, obj_list = dm_utils.get_class_objects([device.GetObjectHandle()], [],
                                                   ["HttpClientResults"])
        if err:
            return err

        # There should only be one HttpClientResults
        # Set the name of the result object with the same name as the client device
        for client_result in obj_list:
            client_result.Set("Name", device.Get("Name"))

    return ""


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])


# Not used. Only for testing purposes
def get_traffic_mix_component_test():
    return {
        "baseTemplateFile": "Ipv4_Stream.xml",
        "modifyList": [
            {
                "enable": True,
                "description": "Modify the IPv4If",
                "operationList": [
                    {
                        "propertyValue":
                        {
                            "className": "StreamBlock",
                            "tagName": "ttStreamBlock",
                            "propertyValueList":
                            {
                                "Name": "StreamBlock"
                            }
                        }
                    }
                ]
            }
        ],
        "postExpandModify": [
            {
                "streamBlockExpand":
                {
                    "endpointMapping":
                    {
                        "srcBindingTagList": [],
                        "dstBindingTagList": [],
                        "bidirectional": False
                    }
                }
            }
        ]
    }


def get_ipv4_stream_frame_config():
    return '''
        <frame><config><pdus>
          <pdu name="eth1" pdu="ethernet:EthernetII"></pdu>
          <pdu name="ip_1" pdu="ipv4:IPv4">
            <tosDiffserv name="anon_2117">
              <tos name="anon_2118"></tos>
            </tosDiffserv>
          </pdu>
        </pdus></config></frame>
    '''


def get_pdu_obj():
    return {
        "enable": True,
        "element_type": "pdu",
        "pdu": "",
        "name": "",
        "property_data": {}
    }
