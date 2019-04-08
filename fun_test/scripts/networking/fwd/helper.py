import requests
from lib.system.fun_test import *
from lib.utilities.pcap_parser import PcapParser
from lib.host.linux import *
from scripts.networking.helper import *
from scripts.networking.nu_config_manager import NuConfigManager
from lib.host.network_controller import NetworkController

FWD_CONFIGS_SPEC = fun_test.get_script_parent_directory() + "/forwarding_inputs.json"
json_file = "api_server_docker.json"
file_path = fun_test.get_script_parent_directory() + "/" + json_file
output = fun_test.parse_file_to_json(file_path)
docker_host = output['docker_host']
docker_user = output['docker_user']
docker_password = output['docker_password']
dpcsh_machine_ip = output['dpc_cli_machine_ip']
dpcsh_port = output['dpc_cli_port']
custom_prompt = {'prompt1': r'$ '}
fcp_csr_monitor_script_path = "FunControlPlane/scripts/palladium_test/csr_monitor.py"
TOLERANCE = 10

class BaseSetup (FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                Local Library
                """)
    def get_network_handle (self, nc_obj, nu_con_obj, temp_obj):
        global network_controller_obj,  nu_config_obj, template_obj
        nu_config_obj = nc_obj 
        network_controller_obj = nu_con_obj
        template_obj = temp_obj

    def _get_ecmp_configs(self):
        all_configs = []
        try:
            #all_configs = nu_config_obj._parse_file_to_json_in_order(file_name=FWD_CONFIGS_SPEC)
            all_configs = nu_config_obj.read_test_configs_by_dut_type(config_file=FWD_CONFIGS_SPEC)
            fun_test.simple_assert(all_configs, "Read Configs")
        except Exception as ex:
            fun_test.critical(str(ex))
        return all_configs

    def get_all_nexthop(self, type, id, link='all'):
        result = []
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            if type == 'interracks':
                if (link == 'all' or link == 'spine'):
                    for item in configs[type][id]['ecmpmember']['members']:
                        result.append(item['outgoingif'])
                if (link == 'all' or link == 'fabric'):
                    for item in configs[type][id]['onepathmembers']:
                        result.append(item['outgoingif'])
            else:
                for item in configs[type][id]['members']:
                    result.append(item['outgoingif'])
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_all_nexthop_weight(self, type, id, link='all', ex_intf=None):
        result = {}
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            spine_intf_weight = configs[type][id]['ecmpmember']['weight'] / len(configs[type][id]['ecmpmember']['members'])
            if (link == 'all' or link == 'spine'):
                for item in configs[type][id]['ecmpmember']['members']:
                    if ex_intf != item['outgoingif']:
                        result[item['outgoingif']] = spine_intf_weight
                    else:
                        result[item['outgoingif']] = 0
            if (link == 'all' or link == 'fabric'):
                for item in configs[type][id]['onepathmembers']:
                    if ex_intf != item['outgoingif']:
                        result[item['outgoingif']] = item['weight']
                    else:
                        result[item['outgoingif']] = 0
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_all_fcp_nexthop_weight(self, type, id, link='all', ex_intf=None):
        result = {}
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            spine_intf_weight = configs[type][id]['ecmpmember']['weight'] / len(configs[type][id]['ecmpmember']['members'])
            if (link == 'all' or link == 'spine'):
                for item in configs[type][id]['ecmpmember']['members']:
                    if ex_intf != item['outgoingif']:
                        result[item['outgoingif']] = spine_intf_weight
                    else:
                        result[item['outgoingif']] = 0
            if (link == 'all' or link == 'fabric'):
                for item in configs[type][id]['onepathmembers']:
                    if ex_intf != item['outgoingif']:
                        intf_name = 'fpg' + str(item['outgoingif'])
                        intf_config = self.get_intf_config(intf_name)
                        result[item['outgoingif']] = len(intf_config["gph_index"])
                    else:
                        result[item['outgoingif']] = 0
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_all_ffr_nexthop_weight(self, type, id, link='all', ex_intf_list=None):
        result = {}
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            spine_intf_weight = configs[type][id]['ecmpmember']['weight'] / len(configs[type][id]['ecmpmember']['members'])
            if (link == 'all' or link == 'spine'):
                for item in configs[type][id]['ecmpmember']['members']:
                    if item['outgoingif'] not in ex_intf_list:
                        result[item['outgoingif']] = spine_intf_weight
                    else:
                        result[item['outgoingif']] = 0
            if (link == 'all' or link == 'fabric'):
                for item in configs[type][id]['onepathmembers']:
                    if item['outgoingif'] not in ex_intf_list:
                        result[item['outgoingif']] = item['weight']
                    else:
                        result[item['outgoingif']] = 0
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


    def get_intrarack_netxt_hop__weight(self, type, id,spf_up):
        result = {}
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            intf_list= self.get_all_nexthop(type=type,id=id)
            dl_index=configs[type][id]['spf_intf']-1
            for item in intf_list:
                if item == intf_list[dl_index]:
                    if spf_up:
                        result[intf_list[dl_index]]= 2
                    else:
                        result[intf_list[dl_index]]= 0
                else:
                    result[item] = 1
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_intrarack_netxt_hop_ffr_weight(self, type, id,down_intf_list):
        result = {}
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            intf_list= self.get_all_nexthop(type=type,id=id)
            for item in intf_list:
                if item in down_intf_list:
                    result[item] = 0
                else:
                    result[item] = 1
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


    def get_pkt_weight_unit(self, type, id, total_pkt):
        result=0
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            total_weight=configs[type][id]['ecmpmember']['weight']
            for item in configs[type][id]['onepathmembers']:
                total_weight = total_weight + item['weight']
            result= total_pkt * 1.0 / total_weight
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_fcp_pkt_weight_unit(self, intf_weight_list, total_pkt):
        result=0
        try:
            total_weight=sum(intf_weight_list.values())
            result= total_pkt * 1.0 / total_weight
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_spine_pkt_weight_unit(self, type, id, total_pkt):
        result=0
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            total_weight=configs[type][id]['ecmpmember']['weight']
            result= total_pkt * 1.0 / total_weight
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_intrarack_pkt_weight_unit(self, type, id, spf_up, total_pkt):
        intf_weight_dict=self.get_intrarack_netxt_hop__weight(type, id, spf_up)
        result=total_pkt * 1.0 /sum(intf_weight_dict.values())
        return result

    def get_pkt_weight_unit_post_link_failure(self, type, id, total_pkt, intf_type, intf_list):
        result=0
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            total_weight=configs[type][id]['ecmpmember']['weight']
            if intf_type == 'spine':
                total_weight=configs[type][id]['ecmpmember']['weight'] - len (intf_list)
                for item in configs[type][id]['onepathmembers']:
                    total_weight = total_weight + item['weight']
            if intf_type == 'fabric':
                for item in configs[type][id]['onepathmembers']:
                    if item['outgoingif'] not in intf_list:
                        total_weight = total_weight + item['weight']
            result= total_pkt * 1.0 / total_weight
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_spine_pkt_weight_unit_post_link_failure(self, type, id, total_pkt, intf_list):
        result=0
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            total_weight=configs[type][id]['ecmpmember']['weight'] - len (intf_list)
            result= total_pkt * 1.0 / total_weight
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_pkt_weight_unit_post_link_failure_ffr(self, type, id, total_pkt, next_hop_type, down_intf_list):
        result=0
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            next_hop_list=[]
            total_weight=0

            # Calculate nexthop
            fabric_next_hop=self.get_all_nexthop(type, id, link='fabric')
            spine_next_hop=self.get_all_nexthop(type, id, link='spine')

            # Calculate total weight
            if next_hop_type == 'all' or next_hop_type == 'spine':
                total_weight=configs[type][id]['ecmpmember']['weight']

            if next_hop_type == 'all' or next_hop_type == 'fabric':
                for item in configs[type][id]['onepathmembers']:
                    total_weight = total_weight + item['weight']

            # Hanlde down interface list
            for item in down_intf_list:
                if item in spine_next_hop:
                    total_weight = total_weight -1
            for item in  configs[type][id]['onepathmembers']:
                if item['outgoingif'] in down_intf_list:
                    total_weight = total_weight - item['weight']

            result= total_pkt * 1.0 / total_weight
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_intrarack_netxt_hop_weight_ffr(self, type, id, down_intf_list):
        result = {}
        try:
            configs = self._get_ecmp_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            intf_list= self.get_all_nexthop(type=type,id=id)
            for item in intf_list:
                if item in down_intf_list:
                    result[item]= 0
                else:
                    result[item] = 1
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_intrarack_pkt_weight_unit_post_link_failure_ffr(self, type, id, total_pkt, down_intf_list):
         result=0
         try:
             configs = self._get_ecmp_configs()
             fun_test.simple_assert(configs, "Failed to read config spec")
             next_hop_list=[]
             total_weight=0

             # Calculate nexthop
             next_hop_list=self.get_all_nexthop(type, id)
             total_weight=len(next_hop_list) -len(down_intf_list)

             result=round( total_pkt * 1.0 / total_weight)
         except Exception as ex:
             fun_test.critical(str(ex))
         return result

    def validate_received_pkt_count_weight(self, recive_pkt_dict, intf_weight_dict, total_pkt, unit_weight, tolerance):

        result =0
        max= 1.0+tolerance/100.0
        min=1.0-tolerance/100.0

        for item in recive_pkt_dict:
            expected_pkt = intf_weight_dict[item] * unit_weight
            if (recive_pkt_dict[item] > round (expected_pkt * max)) or  (recive_pkt_dict[item] < round (expected_pkt * min)):
                fun_test.log("On Next hop interface %s Transmited packet count is not within range \
                              Expected packet count with range %d and %d . Actual count %d " \
                              % (item, round (expected_pkt * max) , round (expected_pkt * min), recive_pkt_dict[item]))
                result = result +1
            else:
                fun_test.log("On Next hop interface %s Transmited packet count is within range" % item)
            if (recive_pkt_dict[item] < round (expected_pkt * min)):
                fun_test.log("On Next hop interface %s Transmited packet count is not within range \
                              Expected packet count with range %d and %d . Actual count %d " \
                              % (item, round (expected_pkt * max) , round (expected_pkt * min), recive_pkt_dict[item]))
                result = result +1
            else:
                fun_test.log("On Next hop interface %s Transmited packet count is within range" % item)
        if result:
            return False
        else:
            return True

    def validate_received_pkt_count(self, expected, received, tolerance):

        result =True
        max= 1.0+tolerance/100.0
        min=1.0-tolerance/100.0

        if (received < (expected * min)):
            fun_test.log("Received Pkt count is less than sent beyond tollerance \
                              Expected packet count with range %d and %d . Actual count %d " \
                              % (round (expected * min) , round (expected * max), received))
            result = False

        if (received > round (expected * max)):
            fun_test.log("Received Pkt count is more than sent beyond tollerance \
                              Expected packet count with range %d and %d . Actual count %d " \
                              % (round (expected * min) , round (expected * max), received))
            result = False
        return result

    def validate_fcp_received_pkt_count(self, expected, received, tolerance):


        # TODO This verifciation need to be modified as FCP stats verification
        result =True
        max= 1.0+tolerance/100.0
        min=1.0-tolerance/100.0

        if (received < (expected * min)):
            fun_test.log("Received Pkt count is less than sent beyond tollerance \
                              Expected packet count with range %d and %d . Actual count %d " \
                              % (round (expected * min) , round (expected * max), received))
            result = False

        return result

    def start_csr_monitor(self, ssh_handle, dpc_cli_machine_ip):
         process_id = None
         try:
             workspace = ssh_handle.command("env | grep 'WORKSPACE'")
             if workspace:
                 workspace_path = workspace.split('=')[1].strip()
                 csr_monitor_script_path = str(workspace_path) + '/' + str(fcp_csr_monitor_script_path)
                 fun_test.log("csr monitor script is %s" % csr_monitor_script_path)
                 process_id = ssh_handle.start_bg_process(nohup=False, command="python %s -H %s -p %s" % (csr_monitor_script_path, dpc_cli_machine_ip, dpcsh_port))
         except Exception as ex:
             fun_test.critical(str(ex))
         return process_id

    def get_intf_config(self, id):
       result = []
       try:
           configs = self._get_ecmp_configs()
           fun_test.simple_assert(configs, "Failed to read config spec")
           result = configs["intfs"][id]
       except Exception as ex:
           fun_test.critical(str(ex))
       return result

    def get_direct_link(self, type, id):
        dl_link=None
        configs = self._get_ecmp_configs()
        fun_test.simple_assert(configs, "Failed to read config spec")
        spf_id= configs[type][id]['spf_intf']
        for item in configs[type][id]['members']:
            intf_name = 'fpg' + str(item['outgoingif'])
            intf_config = self.get_intf_config(intf_name)
            if spf_id == intf_config['remote_f1_id']:
                dl_link=item['outgoingif']
        return dl_link

    def get_non_dl_link_running_traffic(self,traffic_dict):
        non_dl_link=None
        for item in traffic_dict:
            if traffic_dict[item] != 0:
                non_dl_link=item
        return non_dl_link

    def start_traffic(self, port):
        gen_obj=None
        try:
            gen_obj = template_obj.stc_manager.get_generator(port_handle=port)
            start = template_obj.enable_generator_configs(generator_configs=gen_obj)
            fun_test.test_assert(start, "Starting generator config")
        except Exception as ex:
            fun_test.critical(str(ex))
        return gen_obj

    def enable_disable_intf(self, intf_name, status, api_server='127.0.0.1'):


         network_controller_obj.disconnect()
         fun_test.log("Starting csr monitor for adding routes")
         ssh_obj_2 = Linux(docker_host, ssh_username=docker_user, ssh_password=docker_password)
         pid = self.start_csr_monitor(ssh_handle=ssh_obj_2, dpc_cli_machine_ip=dpcsh_machine_ip)
         fun_test.simple_assert(pid, "csr_monitor script started in background")

         intf_config = self.get_intf_config(intf_name)
         headers = {
             'Content-Type': 'application/json',
         }
         data_dict={}

         link_speed = str('BW_'+ str(intf_config['bandwidth']) + 'G')
         intf_gphs_list=[]
         for item in intf_config["gph_index"]:
             intf_dict={}
             intf_dict["gph_index"] = item["index"]
             intf_dict["spine_index"] = item["index"]
             intf_gphs_list.append(intf_dict)

         if intf_config['Interface_type'] == 'fabric_facing':
             data_dict["status"] = status
             data_dict["vrfid"] = intf_config['vrf']
             data_dict["remote_f1_id"] = intf_config['remote_f1_id']
             data_dict["name"] = intf_name
             data_dict["Interface_type"] = 'Fabric_Facing'
             data_dict["bandwidth"] = link_speed
             data_dict["intf_gphs"] = intf_gphs_list
             data_dict["logicport"] = intf_config['logicport']
             data = json.dumps(data_dict)

         else:
             data_dict["status"] = status
             data_dict["vrfid"] = intf_config['vrf']
             data_dict["name"] = intf_name
             data_dict["Interface_type"] = intf_config['Interface_type']
             data_dict["bandwidth"] = link_speed
             data_dict["intf_gphs"] = intf_gphs_list
             data_dict["logicport"] = intf_config['logicport']
             data_dict["spine_index"] = intf_config['spine_index']
             data = json.dumps(data_dict)
         url = "http://%s:8000/v1/cfg/INTERFACE/%d" %(api_server,int(re.findall("\d+", intf_name)[0])+1)

         response = requests.post(url, headers=headers, data=data, verify=False)
         fun_test.sleep("Sleeping 30 sec for curl call", seconds=30)
         fun_test.log("Killing csr monitor ")
         ssh_obj_2.kill_process(process_id=pid)
         ssh_obj_2.disconnect()
         network_controller_obj._connect()
         fun_test.sleep("Sleeping  5 sec for config to program", seconds=5)

    def verify_hnu_non_fcp_traffic(self, dut_port_1, port, next_hop_intf_list, flow='multi', traffic_type='inter', spf_up=False):

         # Clear port results on DUT
         for item in next_hop_intf_list:
             clear_id = network_controller_obj.clear_port_stats(port_num=item)
             fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

         # Collecting HNU port traffic count before sending
         dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
         dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
         if dut_port_1_pre_rx is None: dut_port_1_pre_rx=0

         # Execute traffic
         self.start_traffic(port)

         # Sleep until traffic is executed
         fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

         # Rx packet on DUT
         dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
         dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
         dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
         fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

         # Tx packet on DUT intf_weight_list
         tx_result_dict = {}
         for item in next_hop_intf_list:
             dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
             tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
             if tx_packet == None:
                 tx_result_dict[item] = 0
             else:
                 tx_result_dict[item] = tx_packet
         result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
         fun_test.test_assert_expected(expected=True, actual=result,
         message="Ensure traffix recieved from traffic generator is sent out via FPG")

         if flow == 'multi':
             if traffic_type == 'inter':

                  fun_test.test_assert_expected(expected=0, actual=int(tx_result_dict.values().count(0)),
                  message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop")

                  # Ensure traffic distribution is as per the weight
                  intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='interrack1')
                  unit_weight  = self.get_pkt_weight_unit(type='interracks',id='interrack1', total_pkt=sum(tx_result_dict.values()))
                  result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                  fun_test.test_assert_expected(expected=True, actual=result,
                  message="Ensure traffix transmited from each nexthop as per wieght")
             else :
                  if spf_up:
                      fun_test.test_assert_expected(expected=0, actual=int(tx_result_dict.values().count(0)),
                      message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop")
                  else:
                      fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
                      message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except DL as down")

                  # Ensure traffic distribution is as per the weight
                  intf_weight_list  = self.get_intrarack_netxt_hop__weight(type='intraracks',id='intrarack1', spf_up=spf_up)
                  unit_weight  = self.get_intrarack_pkt_weight_unit(type='intraracks',id='intrarack1', spf_up=spf_up, total_pkt=sum(tx_result_dict.values()))
                  result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                  fun_test.test_assert_expected(expected=True, actual=result,
                  message="Ensure traffix transmited from each nexthop as per wieght")
         else:
             fun_test.test_assert_expected(expected=int(len(tx_result_dict)-1), actual=int(tx_result_dict.values().count(0)),
             message="Ensure as single flow, traffic should egress out of single interface")


    def verify_hnu_fcp_traffic(self, dut_port_1, port, next_hop_intf_list, flow='single', traffic_type='inter', spf_up=False):

         # Clear port results on DUT
         for item in next_hop_intf_list:
             clear_id = network_controller_obj.clear_port_stats(port_num=item)
             fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

         # Collecting HNU port traffic count before sending
         dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
         dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
         if dut_port_1_pre_rx is None: dut_port_1_pre_rx=0

         # Execute traffic
         self.start_traffic(port)

         # Sleep until traffic is executed
         fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

         # Rx packet on DUT
         dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
         dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)
         dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
         fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

         # Tx packet on DUT intf_weight_list
         tx_result_dict = {}
         for item in next_hop_intf_list:
             dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
             tx_packet = get_dut_output_stats_value(dut_results, OCTETS_TRANSMITTED_OK)
             if tx_packet == None:
                 tx_result_dict[item] = 0
             else:
                 tx_result_dict[item] = tx_packet

         result=self.validate_fcp_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
         fun_test.test_assert_expected(expected=True, actual=result,
         message="Ensure traffix recieved from traffic generator is sent out via FPG")


         if traffic_type == 'inter':
              fun_test.test_assert_expected(expected=0, actual=int(tx_result_dict.values().count(0)),
              message="Ensure FCP traffic should egress out via all diffrent nexthop")

              # Ensure traffic distribution is as per the weight
              #intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='fcp_interrack1')
              intf_weight_list  = self.get_all_fcp_nexthop_weight(type='interracks',id='fcp_interrack1')
              #unit_weight  = self.get_pkt_weight_unit(type='interracks',id='interrack1', total_pkt=sum(tx_result_dict.values()))
              unit_weight  = self.get_fcp_pkt_weight_unit(intf_weight_list=intf_weight_list, total_pkt=sum(tx_result_dict.values()))
              result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
              fun_test.test_assert_expected(expected=True, actual=result,
              message="Ensure traffix transmited from each nexthop as per wieght")
         else :

              # Ensure traffic distribution is as per the weight
              intf_weight_list  = self.get_intrarack_netxt_hop__weight(type='intraracks',id='fcp_intrarack1', spf_up=spf_up)
              unit_weight  = self.get_intrarack_pkt_weight_unit(type='intraracks',id='fcp_intrarack1', spf_up=spf_up, total_pkt=sum(tx_result_dict.values()))
              result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
              fun_test.test_assert_expected(expected=True, actual=result,
              message="Ensure traffix transmited from each nexthop as per wieght")



    def verify_nu_non_fcp_traffic(self, dut_port, port, next_hop_intf_list, flow='multi', traffic_type='inter', spf_up=False):

        # Clear port results on DUT
        for item in next_hop_intf_list:
           clear_id = network_controller_obj.clear_port_stats(port_num=item)
           fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
        fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        self.start_traffic(port)

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Rx packet on DUT
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
        dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

        # Tx packet on DUT intf_weight_list
        tx_result_dict = {}
        for item in next_hop_intf_list:
            dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
            tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
            if tx_packet == None:
                tx_result_dict[item] = 0
            else:
                tx_result_dict[item] = tx_packet

        result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="nsure traffix recieved from traffic generator is sent out via FPG")

        if flow == 'multi':
            if traffic_type == 'inter':
                 fun_test.test_assert_expected(expected=0, actual=int(tx_result_dict.values().count(0)),
                 message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop")

                 # Ensure traffic distribution is as per the weight
                 intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='interrack1', link='spine')
                 unit_weight  = self.get_spine_pkt_weight_unit(type='interracks',id='interrack1', total_pkt=sum(tx_result_dict.values()))
                 result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                 fun_test.test_assert_expected(expected=True, actual=result,
                 message="Ensure traffix transmited from each nexthop as per wieght")
            else :
                 if spf_up:
                     fun_test.test_assert_expected(expected=int(len(tx_result_dict)-1), actual=int(tx_result_dict.values().count(0)),
                     message="Ensure as single flow, traffic should egress out of DL interface")
                     # When packet is coming from Fab/Spine , Intra rack traffic will leave only via Direct link
                     self.spf_intf= self.get_direct_link(type='intraracks',id='intrarack1')
                     result=self.validate_received_pkt_count(dut_port_1_rx, tx_result_dict[self.spf_intf], TOLERANCE)
                     fun_test.test_assert_expected(expected=True, actual=result,
                     message="Ensure all traffic is going out via DL")
                 else:
                     fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
                     message="Ensure as multiple flow, traffic should egress out via all diffrent nextho except DL")
                     # Ensure traffic distribution is as per the weight
                     intf_weight_list  = self.get_intrarack_netxt_hop__weight(type='intraracks',id='intrarack1', spf_up=spf_up)
                     unit_weight  = self.get_intrarack_pkt_weight_unit(type='intraracks',id='intrarack1', spf_up=spf_up, total_pkt=sum(tx_result_dict.values()))
                     result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                     fun_test.test_assert_expected(expected=True, actual=result,
                     message="Ensure traffix transmited from each nexthop as per wieght")


    def verify_nu_fcp_traffic(self, dut_port, port, next_hop_intf_list, flow='multi', traffic_type='inter', spf_up=False):

        # Clear port results on DUT
        for item in next_hop_intf_list:
           clear_id = network_controller_obj.clear_port_stats(port_num=item)
           fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
        fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        self.start_traffic(port)

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Rx packet on DUT
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
        dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)
        fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

        # Tx packet on DUT intf_weight_list
        tx_result_dict = {}
        for item in next_hop_intf_list:
            dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
            tx_packet = get_dut_output_stats_value(dut_results, OCTETS_TRANSMITTED_OK)
            if tx_packet == None:
                tx_result_dict[item] = 0
            else:
                tx_result_dict[item] = tx_packet
        result=self.validate_fcp_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix recieved from traffic generator is sent out via FPG")


        if traffic_type == 'inter':
            # Ensure traffic distribution is as per the weight
            intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='fcp_interrack1', link='spine')
            unit_weight  = self.get_spine_pkt_weight_unit(type='interracks',id='fcp_interrack1', total_pkt=sum(tx_result_dict.values()))
            result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix transmited from each nexthop as per wieght")

        else :
            if spf_up:
                # When packet is coming from Fab/Spine , Intra rack traffic will leave only via Direct link
                self.spf_intf= self.get_direct_link(type='intraracks',id='fcp_intrarack1')
                result=self.validate_received_pkt_count(dut_port_1_rx, tx_result_dict[self.spf_intf], TOLERANCE)
                fun_test.test_assert_expected(expected=True, actual=result,
                message="Ensure traffix recieved from traffic generator is sent out via DL interface only")
            else:
                fun_test.log("For FCP Intrarack Direct Link down case traffic does not spray")
                # Ensure traffic distribution is as per the weight
                #intf_weight_list  = self.get_intrarack_netxt_hop__weight(type='intraracks',id='fcp_intrarack1', spf_up=spf_up)
                #unit_weight  = self.get_intrarack_pkt_weight_unit(type='intraracks',id='fcp_intrarack1', spf_up=spf_up, total_pkt=sum(tx_result_dict.values()))
                #result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                #fun_test.test_assert_expected(expected=True, actual=result,
                #message="Ensure traffix transmited from each nexthop as per wieght")

    def verify_ffr_interrack_non_fcp(self, dut_port, port, source, down_intf_list):


        down_interface_name=[]

        if source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
        down_intf_name_list=[]

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        if source == 'host':
            # Get HNU port traffic status again before starting further test
            dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
            dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            if dut_port_1_pre_rx is None: dut_port_1_pre_rx=0
        else:
            # Clear Rx port
            clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        # Execute traffic
        self.start_traffic(port)

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Rx packet on DUT
        if self.source == 'host':
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
            dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
            dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
        else:
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
            dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

        # Tx packet on DUT intf_weight_list
        tx_result_dict = {}
        for item in next_hop_intf_list:
            dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
            tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
            if tx_packet == None:
                tx_result_dict[item] = 0
            else:
                tx_result_dict[item] = tx_packet

        fun_test.test_assert_expected(expected=len(down_intf_list), actual=int(tx_result_dict.values().count(0)),
        message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except the interface is down")

        result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix recieved from traffic generator is sent out via FPG")

        # Ensure traffic distribution is as per the weight
        intf_weight_list  = self.get_all_ffr_nexthop_weight(type='interracks',id='interrack1',ex_intf_list=down_intf_list)
        if self.source == 'host':
            unit_weight  = self.get_pkt_weight_unit_post_link_failure_ffr(type='interracks',id='interrack1', total_pkt=dut_port_1_rx, next_hop_type='all', down_intf_list=down_intf_list)
        else:
            unit_weight  = self.get_pkt_weight_unit_post_link_failure_ffr(type='interracks',id='interrack1', total_pkt=dut_port_1_rx, next_hop_type='spine', down_intf_list=down_intf_list)
        result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix transmited from each nexthop as per wieght")
        fun_test.log("Further test will enable the link back and validate")

        return True

    def verify_ffr_interrack_fcp(self, dut_port, port, source, down_intf_list):


        down_interface_name=[]

        if source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
        down_intf_name_list=[]

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        if source == 'host':
            # Get HNU port traffic status again before starting further test
            dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
            dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
            if dut_port_1_pre_rx is None: dut_port_1_pre_rx=0
        else:
            # Clear Rx port
            clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        # Execute traffic
        self.start_traffic(port)

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Rx packet on DUT
        if self.source == 'host':
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
            dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)
            dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
        else:
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
            dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)

        fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

        # Tx packet on DUT intf_weight_list
        tx_result_dict = {}
        for item in next_hop_intf_list:
            dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
            tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
            if tx_packet == None:
                tx_result_dict[item] = 0
            else:
                tx_result_dict[item] = tx_packet

        fun_test.test_assert_expected(expected=len(down_intf_list), actual=int(tx_result_dict.values().count(0)),
        message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except the interface is down")

        result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix recieved from traffic generator is sent out via FPG")

        # Ensure traffic distribution is as per the weight
        intf_weight_list  = self.get_all_ffr_nexthop_weight(type='interracks',id='interrack1',ex_intf_list=down_intf_list)
        if self.source == 'host':
            unit_weight  = self.get_pkt_weight_unit_post_link_failure_ffr(type='interracks',id='fcp_interrack1', total_pkt=dut_port_1_rx, next_hop_type='all', down_intf_list=down_intf_list)
        else:
            unit_weight  = self.get_pkt_weight_unit_post_link_failure_ffr(type='interracks',id='fcp_interrack1', total_pkt=dut_port_1_rx, next_hop_type='spine', down_intf_list=down_intf_list)
        result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix transmited from each nexthop as per wieght")
        fun_test.log("Further test will enable the link back and validate")

    def verify_ffr_intrarack_non_fcp(self, dut_port, port, source, non_dl_list, dl_intf,  down_intf_list):

         down_intf_name_list=[]

         # Clear port results on DUT
         for item in next_hop_intf_list:
             clear_id = network_controller_obj.clear_port_stats(port_num=item)
             fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

         if source == 'host':
             # Get HNU port traffic status again before starting further test
             dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
             dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
             if dut_port_1_pre_rx is None: dut_port_1_pre_rx=0
         else:
             # Clear Rx port
             clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
             fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

         # Execute traffic
         self.start_traffic(port)

         # Sleep until traffic is executed
         fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

         # Rx packet on DUT/down_intf_list_with_dl
         if self.source == 'host':
             dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
             dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
             dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
         else:
             dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
             dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

         fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

         # Tx packet on DUT intf_weight_list
         tx_result_dict = {}
         for item in non_dl_list:
             dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
             tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
             if tx_packet == None:
                 tx_result_dict[item] = 0
             else:
                 tx_result_dict[item] = tx_packet

         fun_test.test_assert_expected(expected=len(down_intf_list), actual=int(tx_result_dict.values().count(0)),
         message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except the interface is down")

         result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
         fun_test.test_assert_expected(expected=True, actual=result,
         message="Ensure traffix recieved from traffic generator is sent out via FPG")

         down_intf_list_with_dl.append(down_intf_list)
         down_intf_list_with_dl.append(dl_intf)


         # Ensure traffic distribution is as per the weight
         intf_weight_list  = self.get_intrarack_netxt_hop_ffr_weight(type='intraracks',id='intrarack1', down_intf_list=down_intf_list_with_dl)
         unit_weight  =self.get_intrarack_pkt_weight_unit_post_link_failure_ffr(type='intraracks',id='intrarack1', total_pkt=dut_port_1_rx, down_intf_list=down_intf_list_with_dl)
         result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
         fun_test.test_assert_expected(expected=True, actual=result,
         message="Ensure traffix transmited from each nexthop as per wieght")
         fun_test.log("Further test will enable the link back and validate")

         return True

    def verify_ffr_intrarack_fcp(self, dut_port, port, source, non_dl_list, dl_intf,  down_intf_list):

         down_intf_name_list=[]

         # Clear port results on DUT
         for item in next_hop_intf_list:
             clear_id = network_controller_obj.clear_port_stats(port_num=item)
             fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

         if source == 'host':
             # Get HNU port traffic status again before starting further test
             dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
             dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
             if dut_port_1_pre_rx is None: dut_port_1_pre_rx=0
         else:
             # Clear Rx port
             clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
             fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

         # Execute traffic
         self.start_traffic(port)

         # Sleep until traffic is executed
         fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

         # Rx packet on DUT/down_intf_list_with_dl
         if self.source == 'host':
             dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1,hnu=True)
             dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)
             dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
         else:
             dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
             dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)

         fun_test.log("Packet Received from traffic generator : %d" % dut_port_1_rx)

         # Tx packet on DUT intf_weight_list
         tx_result_dict = {}
         for item in non_dl_list:
             dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
             tx_packet = get_dut_output_stats_value(dut_results, OCTETS_TRANSMITTED_OK)
             if tx_packet == None:
                 tx_result_dict[item] = 0
             else:
                 tx_result_dict[item] = tx_packet

         fun_test.test_assert_expected(expected=len(down_intf_list), actual=int(tx_result_dict.values().count(0)),
         message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except the interface is down")

         result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
         fun_test.test_assert_expected(expected=True, actual=result,
         message="Ensure traffix recieved from traffic generator is sent out via FPG")

         down_intf_list_with_dl.append(down_intf_list)
         down_intf_list_with_dl.append(dl_intf)


         # Ensure traffic distribution is as per the weight
         intf_weight_list  = self.get_intrarack_netxt_hop_ffr_weight(type='intraracks',id='fcp_intrarack1', down_intf_list=down_intf_list_with_dl)
         unit_weight  =self.get_intrarack_pkt_weight_unit_post_link_failure_ffr(type='intraracks',id='fcp_intrarack1', total_pkt=dut_port_1_rx, down_intf_list=down_intf_list_with_dl)
         result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
         fun_test.test_assert_expected(expected=True, actual=result,
         message="Ensure traffix transmited from each nexthop as per wieght")
         fun_test.log("Further test will enable the link back and validate")

         return True

    def create_hnu_interrack_frame(self, duration, port, traffic_type):

        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80
        if traffic_type == 'nfcp':
            dest_ip= 'destination_ip5'
        else:
            dest_ip= 'destination_ip9'


        gen_config_obj.Duration = duration
        config_obj = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")
        l3_config = routes_config['l3_config']
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE


        # Create streamblock
        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port)
        ethernet_obj = Ethernet2Header(destination_mac=routes_config['routermac'], ether_type=ether_type)
        checkpoint = "Configure Mac address for %s " % self.streamblock_obj.spirent_handle
        ether = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=ether, message=checkpoint)

        checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
        ip_header_obj = Ipv4Header(destination_address=l3_config[dest_ip],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Configure IP range modifier"
        modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, recycle_count=100,
                                     step_value="0.0.0.1", mask="255.255.255.255",
                                     data=l3_config['source_ip1'])
        result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=modifier_obj,
                                                                   header_obj=ip_header_obj,
                                                                   streamblock_obj=self.streamblock_obj,
                                                                   header_attribute="sourceAddr")
        fun_test.simple_assert(result, checkpoint)
        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        tcpHeader = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(tcpHeader, checkpoint)

        checkpoint = "Configure Port Modifier"
        port_modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, step_value=1, recycle_count=10000,
                                                  data=1024)
        result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=port_modifier_obj,
                                                                           header_obj=tcp_header_obj,
                                                                           streamblock_obj=self.streamblock_obj,
                                                                           header_attribute="destPort")
        fun_test.simple_assert(result, checkpoint)
        src_port_modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, step_value=1, recycle_count=10000,
                                                  data=10000)
        result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=src_port_modifier_obj,
                                                                           header_obj=tcp_header_obj,
                                                                           streamblock_obj=self.streamblock_obj,
                                                                           header_attribute="sourcePort")
        fun_test.simple_assert(result, checkpoint)

        return self.streamblock_obj

    def delete_stream(self, streamblock_obj):
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])

    def create_fsf_frame(self, duration, port):

        load = 1
        checkpoint = "Create a stream with EthernetII and Custom header option under port %s" % port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=80,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED,
                                      insert_signature=True,
                                      load=load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ETHERNET_FLOW_CONTROL_MAC, preamble="55555555555555d5",
                                    ether_type=Ethernet2Header.ETHERNET_FLOW_CONTROL_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        custom_header_obj = CustomBytePatternHeader(byte_pattern=custom_headers[FSF_Custom_Header][0])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=custom_header_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        return self.stream_obj
