from lib.system.fun_test import *
from fun_global import get_current_time
from lib.templates.traffic_generator.traffic_generator_template import TrafficGeneratorTemplate
from lib.host.spirent_manager import SpirentManager
import json
from collections import OrderedDict
from uuid import uuid4
import os


class SpirentTrafficGeneratorTemplate(TrafficGeneratorTemplate):
    diff_serv_dscp_values = {
        'best_effort': {'dscp_value': '000000', 'decimal_value': '0', 'dscp_high': '0', 'dscp_low': '0'},
        '1': {'dscp_value': '000001', 'decimal_value': '1', 'dscp_high': '0', 'dscp_low': '1'},
        '2': {'dscp_value': '000010', 'decimal_value': '2', 'dscp_high': '0', 'dscp_low': '2'},
        '3': {'dscp_value': '000011', 'decimal_value': '3', 'dscp_high': '0', 'dscp_low': '3'},
        '4': {'dscp_value': '000100', 'decimal_value': '4', 'dscp_high': '0', 'dscp_low': '4'},
        '5': {'dscp_value': '000101', 'decimal_value': '5', 'dscp_high': '0', 'dscp_low': '5'},
        '6': {'dscp_value': '000110', 'decimal_value': '6', 'dscp_high': '0', 'dscp_low': '6'},
        '7': {'dscp_value': '000111', 'decimal_value': '7', 'dscp_high': '0', 'dscp_low': '7'},
        '8': {'dscp_value': '001000', 'decimal_value': '8', 'dscp_high': '1', 'dscp_low': '0'},
        '9': {'dscp_value': '001001', 'decimal_value': '9', 'dscp_high': '1', 'dscp_low': '1'},
        'AF11': {'dscp_value': '001010', 'decimal_value': '10', 'dscp_high': '1', 'dscp_low': '2'},
        '11': {'dscp_value': '001011', 'decimal_value': '11', 'dscp_high': '1', 'dscp_low': '3'},
        'AF12': {'dscp_value': '001100', 'decimal_value': '12', 'dscp_high': '1', 'dscp_low': '4'},
        '13': {'dscp_value': '001101', 'decimal_value': '13', 'dscp_high': '1', 'dscp_low': '5'},
        'AF13': {'dscp_value': '001110', 'decimal_value': '14', 'dscp_high': '1', 'dscp_low': '6'},
        '15': {'dscp_value': '001111', 'decimal_value': '15', 'dscp_high': '1', 'dscp_low': '7'},
        '16': {'dscp_value': '010000', 'decimal_value': '16', 'dscp_high': '2', 'dscp_low': '0'},
        'AF21': {'dscp_value': '010010', 'decimal_value': '18', 'dscp_high': '2', 'dscp_low': '2'},
        'AF22': {'dscp_value': '010100', 'decimal_value': '20', 'dscp_high': '2', 'dscp_low': '4'},
        'AF23': {'dscp_value': '010110', 'decimal_value': '22', 'dscp_high': '2', 'dscp_low': '6'},
        'AF31': {'dscp_value': '011010', 'decimal_value': '26', 'dscp_high': '3', 'dscp_low': '2'},
        'AF32': {'dscp_value': '011100', 'decimal_value': '28', 'dscp_high': '3', 'dscp_low': '4'},
        'AF33': {'dscp_value': '011110', 'decimal_value': '30', 'dscp_high': '3', 'dscp_low': '6'},
        'AF41': {'dscp_value': '100010', 'decimal_value': '34', 'dscp_high': '4', 'dscp_low': '2'},
        'AF42': {'dscp_value': '100100', 'decimal_value': '36', 'dscp_high': '4', 'dscp_low': '4'},
        'AF43': {'dscp_value': '100110', 'decimal_value': '38', 'dscp_high': '4', 'dscp_low': '6'},
        'EF': {'dscp_value': '101110', 'decimal_value': '46', 'dscp_high': '5', 'dscp_low': '6'},
        'CS6': {'dscp_value': '110000', 'decimal_value': '48', 'dscp_high': '6', 'dscp_low': '0'},
        'CS7': {'dscp_value': '111000', 'decimal_value': '56', 'dscp_high': '7', 'dscp_low': '0'}}

    def __init__(self, spirent_config, chassis_type=SpirentManager.VIRTUAL_CHASSIS_TYPE):
        TrafficGeneratorTemplate.__init__(self)
        if not chassis_type:
            self.chassis_type = SpirentManager.VIRTUAL_CHASSIS_TYPE
        else:
            self.chassis_type = chassis_type
        self.spirent_config = spirent_config
        try:
            self.stc_manager = SpirentManager(chassis_type=self.chassis_type, spirent_config=self.spirent_config)
        except Exception as ex:
            fun_test.critical(str(ex))

    def get_diff_serv_dscp_value(self, input_type, input_list=[], meaning=False, dscp_value=False, decimal_value=False,
                                 dscp_high=False, dscp_low=False):
        output = {}
        MEANING = "meaning"
        DSCP_VALUE = "dscp_value"
        DECIMAL_VALUE = "decimal_value"
        DSCP_HIGH = "dscp_high"
        DSCP_LOW = "dscp_low"

        try:
            def get_other_values(input_type, input_list):
                result = {}
                for item in input_list:
                    result[item] = {}
                    for key, val in self.diff_serv_dscp_values.iteritems():
                        if str(val[input_type]) == str(item):
                            result[item][MEANING] = key
                            result[item].update(val)
                            del result[item][input_type]
                            break
                return result

            if input_type == MEANING:
                for item in input_list:
                    output[item] = self.diff_serv_dscp_values[item]
            elif input_type == DSCP_VALUE or input_type == DECIMAL_VALUE:
                output = get_other_values(input_type=input_type, input_list=input_list)

            for key, val in output.iteritems():
                if not meaning:
                    if val.has_key(MEANING):
                        del val[MEANING]
                if not dscp_value:
                    if val.has_key(DSCP_VALUE):
                        del val[DSCP_VALUE]
                if not decimal_value:
                    if val.has_key(DECIMAL_VALUE):
                        del val[DECIMAL_VALUE]
                if not dscp_high:
                    if val.has_key(DSCP_HIGH):
                        del val[DSCP_HIGH]
                if not dscp_low:
                    if val.has_key(DSCP_LOW):
                        del val[DSCP_LOW]
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def get_diff_serv_dscp_value_from_meaning(self, meaning_list, dscp_value=False, decimal_value=False, dscp_high=False, dscp_low=False):
        result = {}
        try:
            result = self.get_diff_serv_dscp_value(input_type='meaning', input_list=meaning_list, dscp_low=dscp_low,
                                                   dscp_value=dscp_value, decimal_value=decimal_value,
                                                   dscp_high=dscp_high)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_diff_serv_dscp_value_from_dscp_value(self,  dscp_value_list, meaning=False, decimal_value=False, dscp_high=False, dscp_low=False):
        result = {}
        try:
            result = self.get_diff_serv_dscp_value(input_type='dscp_value', input_list=dscp_value_list, dscp_low=dscp_low,
                                                   meaning=meaning, decimal_value=decimal_value,
                                                   dscp_high=dscp_high)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_diff_serv_dscp_value_from_decimal_value(self, decimal_value_list, meaning=False, dscp_value=False, dscp_high=False, dscp_low=False):
        result = {}
        try:
            result = self.get_diff_serv_dscp_value(input_type='decimal_value', input_list=decimal_value_list, dscp_low=dscp_low,
                                                   meaning=meaning, dscp_value=dscp_value,
                                                   dscp_high=dscp_high)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def read_json_file_contents(self, file_path):
        contents = {}
        try:
            if os.path.exists(file_path):
                contents = fun_test.parse_file_to_json(file_name=file_path)
                fun_test.simple_assert(expression=contents, message="Read %s File" % file_path)
                fun_test.debug("Found: %s" % contents)
        except Exception as ex:
            fun_test.critical(str(ex))
        return contents

    def create_counters_file(self, json_file_name, counter_dict):
        result = False
        try:
            with open(json_file_name, "w") as f:
                json.dump(counter_dict, f, indent=4, default=str)

            fun_test.add_auxillary_file(description="Counters file", filename=json_file_name)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def populate_performance_counters_json(self, mode, file_name, results=None, flow_type=None, timestamp=None):
        file_created = False
        records = []
        try:
            if not timestamp:
                timestamp = get_current_time()
            for key in results:
                record = OrderedDict()
                record['mode'] = mode.upper()
                record['version'] = fun_test.get_version()
                record['timestamp'] = timestamp
                frame_size = int(key.split('_')[1])
                record['frame_size'] = frame_size
                if flow_type:
                    record['flow_type'] = flow_type
                record['throughput'] = float(results[key]['throughput_count'])
                record['pps'] = results[key]['pps_count']

                record['latency_avg'] = results[key]['latency_count'][0]['avg']
                record['latency_max'] = results[key]['latency_count'][0]['max']
                record['latency_min'] = results[key]['latency_count'][0]['min']

                record['jitter_avg'] = results[key]['jitter_count'][0]['avg']
                record['jitter_max'] = results[key]['jitter_count'][0]['max']
                record['jitter_min'] = results[key]['jitter_count'][0]['min']
                records.append(record)
            fun_test.debug(records)
            previous_run_records = self.read_json_file_contents(file_path=file_name)
            if previous_run_records:
                new_records = previous_run_records + records
                file_created = self.create_counters_file(json_file_name=file_name, counter_dict=new_records)
                fun_test.simple_assert(file_created, "Create Performance JSON File")
            else:
                file_created = self.create_counters_file(json_file_name=file_name, counter_dict=records)
                fun_test.simple_assert(file_created, "Create Performance JSON File")
        except Exception as ex:
            fun_test.critical(str(ex))
        return file_created

    def start_default_capture_save_locally(self, port_handle, sleep_time=5):
        result = {}
        result['result'] = False
        result['capture_obj'] = None
        result['pcap_file_path'] = None
        try:
            capture_obj = Capture()
            start_capture = self.stc_manager.start_capture_command(capture_obj=capture_obj, port_handle=port_handle)
            fun_test.test_assert(start_capture, "Started capture on port %s" % port_handle)
            result['capture_obj'] = capture_obj

            fun_test.sleep("Letting captures to happen", seconds=sleep_time)

            stop_capture = self.stc_manager.stop_capture_command(capture_obj._spirent_handle)
            fun_test.test_assert(stop_capture, "Stopped capture on port %s" % port_handle)

            file = fun_test.get_temp_file_name()
            file_name = file + '.pcap'
            file_path = SYSTEM_TMP_DIR
            pcap_file_path = file_path + "/" + file_name

            saved = self.stc_manager.save_capture_data_command(capture_handle=capture_obj._spirent_handle,
                                                               file_name=file_name, file_name_path=file_path)
            fun_test.test_assert(saved, "Saved pcap %s to local machine" % pcap_file_path)

            fun_test.simple_assert(os.path.exists(pcap_file_path), message="Check pcap file exists locally")
            result['pcap_file_path'] = pcap_file_path
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


class StreamBlock(object):
    ENDPOINT_MAPPING_ONE_TO_ONE = "ONE_TO_ONE"
    ENDPOINT_MAPPING_ONE_TO_MANY = "ONE_TO_MANY"
    FILL_TYPE_CONSTANT = "CONSTANT"
    FILL_TYPE_INCR = "INCR"
    FILL_TYPE_DECR = "DECR"
    FILL_TYPE_PRBS = "PRBS"
    FRAME_LENGTH_MODE_FIXED = "FIXED"
    FRAME_LENGTH_MODE_INCR = "INCR"
    FRAME_LENGTH_MODE_DECR = "DECR"
    FRAME_LENGTH_MODE_IMIX = "IMIX"
    FRAME_LENGTH_MODE_RANDOM = "RANDOM"
    FRAME_LENGTH_MODE_AUTO = "AUTO"
    LOAD_UNIT_PERCENT_LINE_RATE = "PERCENT_LINE_RATE"
    LOAD_UNIT_FRAMES_PER_SECOND = "FRAMES_PER_SECOND"
    LOAD_UNIT_INTER_BURST_PER_GAP = "INTER_BURST_GAP"
    LOAD_UNIT_BITS_PER_SECOND = "BITS_PER_SECOND"
    LOAD_UNIT_KILOBITS_PER_SECOND = "KILOBITS_PER_SECOND"
    LOAD_UNIT_MEGABITS_PER_SECOND = "MEGABITS_PER_SECOND"
    LOAD_UNIT_INTER_BURST_GAP_IN_MILLISECONDS = "INTER_BURST_GAP_IN_MILLISECONDS"
    LOAD_UNIT_INTER_BURST_GAP_IN_NANOSECONDS = "INTER_BURST_GAP_IN_NANOSECONDS"
    LOAD_UNIT_L2_RATE = "L2_RATE"
    TIME_STAMP_TYPE_MIN = "MIN"
    TIME_STAMP_TYPE_IEEE_1588 = "IEEE_1588"
    TIME_STAMP_TYPE_GM = "GM"
    TIME_STAMP_TYPE_AVTP = "AVTP"
    TIME_STAMP_TYPE_MAX = "MAX"
    TRAFFIC_PATTERN_PAIR = "PAIR"
    TRAFFIC_PATTERN_MESH = "MESH"
    TRAFFIC_PATTERN_BACKBONE = "BACKBONE"
    _spirent_handle = None

    def __init__(self, advanced_inter_leaving_group=0, allow_invalid_headers=False, burst_size=1,
                 by_pass_simple_ip_subnet_checking=False, constant_fill_pattern=0, custom_pfc_priority=0,
                 enable_backbone_traffic_send_to_self=True, enable_bidirectoional_traffic=False,
                 enable_control_plane=False, enable_custom_pfc=False, enable_fcs_error_insertion=False,
                 enable_high_speen_result_analysis=False, enable_resolve_dest_mac_address=True,
                 enable_stream_only_generation=True, enable_tx_port_sending_traffic_to_self=False,
                 endpoint_mapping=ENDPOINT_MAPPING_ONE_TO_ONE, fill_type=FILL_TYPE_CONSTANT, fixed_frame_length=128,
                 frame_config="", frame_length_mode=FRAME_LENGTH_MODE_FIXED, insert_signature=True, inter_frame_gap=12,
                 load=10, load_unit=LOAD_UNIT_PERCENT_LINE_RATE, max_frame_length=256, min_frame_length=128,
                 priority=0, show_all_headers=False, start_delay=0, step_frame_length=1, time_stamp_offset=0,
                 time_stamp_type=TIME_STAMP_TYPE_MIN, traffic_pattern=TRAFFIC_PATTERN_PAIR):
        self.AdvancedInterleavingGroup = advanced_inter_leaving_group
        self.AllowInvalidHeaders = allow_invalid_headers
        self.BurstSize = burst_size
        self.ByPassSimpleIpSubnetChecking = by_pass_simple_ip_subnet_checking
        self.ConstantFillPattern = constant_fill_pattern
        self.CustomPfcPriority = custom_pfc_priority
        self.EnableBackBoneTrafficSendToSelf = enable_backbone_traffic_send_to_self
        self.EnableBidirectionalTraffic = enable_bidirectoional_traffic
        self.EnableControlPlane = enable_control_plane
        self.EnableCustomPfc = enable_custom_pfc
        self.EnableFcsErrorInsertion = enable_fcs_error_insertion
        self.EnableHighSpeedResultAnalysis = enable_high_speen_result_analysis
        self.EnableResolveDestMacAddress = enable_resolve_dest_mac_address
        self.EnableStreamOnlyGeneration = enable_stream_only_generation
        self.EnableTxPortSendingTrafficToSelf = enable_tx_port_sending_traffic_to_self
        self.EndpointMapping = endpoint_mapping
        self.FillType = fill_type
        self.FixedFrameLength = fixed_frame_length
        self.FrameConfig = frame_config
        self.FrameLengthMode = frame_length_mode
        self.InsertSig = insert_signature
        self.InterFrameGap = inter_frame_gap
        self.Load = load
        self.LoadUnit = load_unit
        self.MaxFrameLength = max_frame_length
        self.MinFrameLength = min_frame_length
        self.Priority = priority
        self.ShowAllHeaders = show_all_headers
        self.StartDelay = start_delay
        self.StepFrameLength = step_frame_length
        self.TimeStampOffset = time_stamp_offset
        self.TimeStampType = time_stamp_type
        self.TrafficPattern = traffic_pattern

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle



class FrameLengthDistributor(object):
    HEADER_TYPE = "ethernetpause:PauseMacControl"
    _spirent_handle = None

    def __init__(self, op_code="0001", pause_time=0, reserved=""):
        self.opCode = op_code
        self.pauseTime = pause_time
        self.reserved = reserved

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class GeneratorConfig(object):
    INTER_FRAME_GAP_UNIT_PERCENT_LINE_RATE = "PERCENT_LINE_RATE"
    INTER_FRAME_GAP_UNIT_FRAMES_PER_SECOND = "FRAMES_PER_SECOND"
    INTER_FRAME_GAP_UNIT_BYTES = "BYTES"
    INTER_FRAME_GAP_UNIT_BITS_PER_SECOND = "BITS_PER_SECOND"
    INTER_FRAME_GAP_UNIT_KILOBITS_PER_SECOND = "KILOBITS_PER_SECOND"
    INTER_FRAME_GAP_UNIT_MEGABITS_PER_SECOND = "MEGABITS_PER_SECOND"
    INTER_FRAME_GAP_UNIT_MILLISECONDS = "INTER_BURST_GAP_IN_MILLISECONDS"
    INTER_FRAME_GAP_UNIT_NANOSECONDS = "INTER_BURST_GAP_IN_NANOSECONDS"
    LOAD_UNIT_PERCENT_LINE_RATE = "PERCENT_LINE_RATE"
    LOAD_UNIT_FRAMES_PER_SECOND = "FRAMES_PER_SECOND"
    LOAD_UNIT_INTER_BURST_PER_GAP = "INTER_BURST_GAP"
    LOAD_UNIT_BITS_PER_SECOND = "BITS_PER_SECOND"
    LOAD_UNIT_KILOBITS_PER_SECOND = "KILOBITS_PER_SECOND"
    LOAD_UNIT_MEGABITS_PER_SECOND = "MEGABITS_PER_SECOND"
    LOAD_UNIT_INTER_BURST_GAP_IN_MILLISECONDS = "INTER_BURST_GAP_IN_MILLISECONDS"
    LOAD_UNIT_INTER_BURST_GAP_IN_NANOSECONDS = "INTER_BURST_GAP_IN_NANOSECONDS"
    LOAD_UNIT_L2_RATE = "L2_RATE"
    DURATION_MODE_CONTINOUS = "CONTINUOUS"
    DURATION_MODE_BURSTS = "BURSTS"
    DURATION_MODE_SECONDS = "SECONDS"
    DURATION_MODE_TABLE_REPETITIONS = "TABLE_REPETITIONS"
    DURATION_MODE_STEP = "STEP"
    LOAD_MODE_FIXED = "FIXED"
    LOAD_MODE_RANDOM = "RANDOM"
    SCHEDULING_MODE_PORT_BASED = "PORT_BASED"
    SCHEDULING_MODE_RATE_BASED = "RATE_BASED"
    SCHEDULING_MODE_PRIORITY_BASED = "PRIORITY_BASED"
    SCHEDULING_MODE_MANUAL_BASED = "MANUAL_BASED"
    TIME_STAMP_LATCH_MDOE_START_OF_FRAME = "START_OF_FRAME"
    TIME_STAMP_LATCH_MODE_END_OF_FRAME = "END_OF_FRAME"
    _spirent_handle = None

    def __init__(self, advanced_interleaving=False, burst_size=1, duration=10, duration_mode=DURATION_MODE_CONTINOUS,
                 fixed_laod=10, inter_frame_gap_unit=INTER_FRAME_GAP_UNIT_BYTES, jumbo_frame_threshold=1518,
                 oversize_frame_threshold=9018, random_length_seed=10900842, random_max_load=100, random_min_load=10,
                 scheduling_mode=SCHEDULING_MODE_PORT_BASED, smoothen_random_length=False, step_size=1,
                 time_stamp_latch_mode=TIME_STAMP_LATCH_MDOE_START_OF_FRAME, undersize_frame_threshold=64,
                 inter_frame_gap=12, load_mode=LOAD_MODE_FIXED, load_unit=LOAD_UNIT_PERCENT_LINE_RATE):
        self.AdvancedInterleaving = advanced_interleaving
        self.BurstSize = burst_size
        self.Duration = duration
        self.DurationMode = duration_mode
        self.FixedLoad = fixed_laod
        self.InterFrameGapUnit = inter_frame_gap_unit
        self.JumboFrameThreshold = jumbo_frame_threshold
        self.OversizeFrameThreshold = oversize_frame_threshold
        self.RandomLengthSeed = random_length_seed
        self.RandomMaxLoad = random_max_load
        self.RandomMinLoad = random_min_load
        self.SchedulingMode = scheduling_mode
        self.SmoothenRandomLength = smoothen_random_length
        self.StepSize = step_size
        self.TimeStampLatchMode = time_stamp_latch_mode
        self.UndersizeFrameThreshold = undersize_frame_threshold
        self.InterFrameGap = inter_frame_gap
        self.LoadMode = load_mode
        self.LoadUnit = load_unit

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Ethernet2Header(object):
    HEADER_TYPE = "ethernet:EthernetII"
    LOCAL_EXPERIMENTAL_ETHERTYPE = "88B5"
    INTERNET_IP_ETHERTYPE = "0800"
    ARP_ETHERTYPE = "0806"
    RARP_ETHERTYPE = "8035"
    LLDP_ETHERTYPE = "88CC"
    PTP_ETHERTYPE = "88F7"
    X25_LEVEL_3_ETHERTYPE = "0805"
    BROADCAST_MAC = "FF:FF:FF:FF:FF:FF"
    OSPF_MULTICAST_MAC_1 = "01:00:5E:00:00:05"
    OSPF_MULTICAST_MAC_2 = "01:00:5E:00:00:06"
    PIM_MULTICAST_MAC = "01:00:5E:00:00:0D"
    LLDP_MULTICAST_MAC = "01:80:C2:00:00:0E"
    ETHERNET_FLOW_CONTROL_MAC = "01:80:C2:00:00:01"
    PTP_MULTICAST_MAC = "01:1B:19:00:00:00"
    INTERNET_IPV6_ETHERTYPE = "86DD"
    ETHERNET_FLOW_CONTROL_ETHERTYPE = "8808"
    ISIS_MULTICAST_MAC_1 = "01:80:C2:00:00:14"
    ISIS_MULTICAST_MAC_2 = "01:80:C2:00:00:15"

    def __init__(self, destination_mac="00:00:01:00:00:01", ether_type=INTERNET_IP_ETHERTYPE,
                 preamble="55555555555555d5", source_mac="00:10:94:00:00:02"):
        self.dstMac = destination_mac
        self.etherType = ether_type
        self.preamble = preamble
        self.srcMac = source_mac

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class PtpFollowUpHeader(object):
    HEADER_TYPE = "ptp:FollowUp"
    CONTROL_FIELD_FOLLOW_UP = "02"
    CONTROL_FIELD_SYNC = "00"
    MESSAGE_TYPE_FOLLOW_UP = 8
    MESSAGE_TYPE_SYNC = 0

    def __init__(self, control_field="", domain_number=0, log_message_interval=127, message_length=0,
                 message_type=MESSAGE_TYPE_SYNC, name=None, sequence_id=0, transport_specific="0000",
                 version_ptp=2):
        self.ControlField = control_field
        self.DomainNumber = domain_number
        self.LogMsgInt = log_message_interval
        self.MessageLength = message_length
        self.MessageType = message_type
        self.Name = name
        self.SeqId = sequence_id
        self.TransportSpecific = transport_specific
        self.VersionPtp = version_ptp

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class PtpTimeStampHeader(object):
    HEADER_TYPE = "ptp:Timestamp"
    CONTROL_FIELD_FOLLOW_UP = "02"
    CONTROL_FIELD_SYNC = "00"
    MESSAGE_TYPE_FOLLOW_UP = 8
    MESSAGE_TYPE_SYNC = 0

    def __init__(self, control_field="", domain_number=0, log_message_interval=127, message_length=0,
                 message_type=MESSAGE_TYPE_SYNC, name=None, sequence_id=0, transport_specific="0000",
                 version_ptp=2):
        self.ControlField = control_field
        self.DomainNumber = domain_number
        self.LogMsgInt = log_message_interval
        self.MessageLength = message_length
        self.MessageType = message_type
        self.Name = name
        self.SeqId = sequence_id
        self.TransportSpecific = transport_specific
        self.VersionPtp = version_ptp

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class PtpSyncHeader(object):
    HEADER_TYPE = "ptp:Sync"
    CONTROL_FIELD_FOLLOW_UP = "02"
    CONTROL_FIELD_SYNC = "00"
    MESSAGE_TYPE_FOLLOW_UP = 8
    MESSAGE_TYPE_SYNC = 0

    def __init__(self, control_field="", domain_number=0, log_message_interval=127, message_length=0,
                 message_type=MESSAGE_TYPE_SYNC, name=None, sequence_id=0, transport_specific="0000",
                 version_ptp=2):
        self.ControlField = control_field
        self.DomainNumber = domain_number
        self.LogMsgInt = log_message_interval
        self.MessageLength = message_length
        self.MessageType = message_type
        self.Name = name
        self.SeqId = sequence_id
        self.TransportSpecific = transport_specific
        self.VersionPtp = version_ptp

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class PtpDelayReqHeader(object):
    HEADER_TYPE = "ptp:DelayReq"
    CONTROL_FIELD_FOLLOW_UP = "02"
    CONTROL_FIELD_SYNC = "00"
    MESSAGE_TYPE_FOLLOW_UP = 8
    MESSAGE_TYPE_SYNC = 0

    def __init__(self, control_field="", domain_number=0, log_message_interval=127, message_length=0,
                 message_type=MESSAGE_TYPE_SYNC, name=None, sequence_id=0, transport_specific="0000",
                 version_ptp=2):
        self.ControlField = control_field
        self.DomainNumber = domain_number
        self.LogMsgInt = log_message_interval
        self.MessageLength = message_length
        self.MessageType = message_type
        self.Name = name
        self.SeqId = sequence_id
        self.TransportSpecific = transport_specific
        self.VersionPtp = version_ptp

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class EthernetPauseHeader(object):
    HEADER_TYPE = "ethernetpause:EthernetPause"

    def __init__(self, destination_mac="01:80:C2:00:00:01", length_type="8808", op_code="0001",
                 preamble="55555555555555d5", source_mac="00:00:01:00:00:03", parameters="0000", reserved=""):
        self.dstMac = destination_mac
        self.lengthType = length_type
        self.Opcode = op_code
        self.srcMac = source_mac
        self.preamble = preamble
        self.Parameters = parameters
        self.Reserved = reserved

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class Ipv4Header(object):
    PROTOCOL_TYPE_EXPERIMENTAL = 253
    PROTOCOL_TYPE_ICMP = 1
    PROTOCOL_TYPE_OSPFIGP = 89
    PROTOCOL_TYPE_PIM = 103
    PROTOCOL_TYPE_TCP = 6
    PROTOCOL_TYPE_IGMP = 2
    PROTOCOL_TYPE_UDP = 17
    HEADER_TYPE = "ipv4:IPv4"
    CHECKSUM_ERROR = '65535'
    TOTAL_HEADER_LENGTH_ERROR = '65535'
    OSPF_MULTICAST_IP_1 = "224.0.0.5"
    OSPF_MULTICAST_IP_2 = "224.0.0.6"
    PIM_MULTICAST_IP = "224.0.0.13"
    DHCP_RELAY_AGENT_MULTICAST_IP = "224.0.0.12"
    PTP_SYNC_MULTICAST_IP = "224.0.1.129"
    PTP_DELAY_MULTICAST_IP = "224.0.0.107"

    def __init__(self, checksum=0, destination_address="192.0.0.1", dest_prefix_length=24,
                 frag_offset=0, gateway="192.85.0.1", identification=0, ihl=5, prefix_length=24,
                 protocol=PROTOCOL_TYPE_EXPERIMENTAL, source_address="192.85.1.2", total_length=20,
                 ttl=255, version=4):
        self.checksum = checksum
        self.destAddr = destination_address
        self.destPrefixLength = dest_prefix_length
        self.fragOffset = frag_offset
        self.gateway = gateway
        self.identification = identification
        self.ihl = ihl
        self.prefixLength = prefix_length
        self.protocol = protocol
        self.sourceAddr = source_address
        self.totalLength = total_length
        self.ttl = ttl
        self.version = version

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class Ipv6Header(object):
    HEADER_TYPE = "ipv6:IPv6"
    NEXT_HEADER_TCP = 6
    NEXT_HEADER_UDP = 17
    NO_NEXT_HEADER = 59
    PAYLOAD_LENGTH_ERROR = '65535'
    _spirent_handle = None

    def __init__(self, destination_address="2000::1", destination_prefix_length=64, flow_label=0, gateway="::0",
                 hop_limit=255, name="", next_header=NO_NEXT_HEADER, payload_length=0,
                 prefix_length=64,source_address="2000::2", traffic_class=0, version=6):
        self.destAddr = destination_address
        self.destPrefixLength = destination_prefix_length
        self.flowLabel = flow_label
        self.gateway = gateway
        self.hopLimit = hop_limit
        self.nextHeader = next_header
        self.payloadLength = payload_length
        self.prefixLength = prefix_length
        self.sourceAddr = source_address
        self.trafficClass = traffic_class
        self.version = version

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class EthernetCopperInterface(object):
    SPEED_UNKNOWN = "SPEED_UNKNOWN"
    SPEED_1G = "SPEED_1G"
    CUSTOM_FEC_MODE_KR = "KR_FEC"
    CUSTOM_FEC_MODE_RS = "RS_FEC"
    CUSTOM_FEC_MODE_KP4 = "KP4_FEC"
    CUSTOM_FEC_MODE_NONE = "NONE"
    DATA_PATH_MODE_NORMAL = "NORMAL"
    DATA_PATH_MODE_LOCAL_LOOPBACK = "LOCAL_LOOPBACK"
    DATA_PATH_MODE_LINE_MONITOR = "LINE_MONITOR"
    FULL_DUPLEX = "FULL"
    HALF_DUPLEX = "HALF"
    _spirent_handle = None

    def __init__(self, advertise_ieee=True, advertise_nbaset=True, alternate_speeds=SPEED_UNKNOWN,
                 auto_mdix=False, auto_negotiation=True, auto_negotiation_master_slave="MASTER",
                 auto_negotiation_master_slave_enable=True, collision_exponent=10, custom_fec_mode=CUSTOM_FEC_MODE_KR,
                 data_path_mode=DATA_PATH_MODE_NORMAL, down_shift_enable=False, duplex=FULL_DUPLEX, flow_control=False,
                 forward_error_correction=True, ignore_link_status=False, internal_ppm_adjust=0, line_speed=SPEED_1G,
                 mtu=1500, optimize_xon="DISABLE", performance_mode="STC_DEFAULT", port_setup_mode="PORTCONFIG_ONLY",
                 test_mode="NORMAL_OPERATION", transmit_clock_source="INTERNAL"):
        self.AdvertiseIEEE = advertise_ieee
        self.AdvertiseNBASET = advertise_nbaset
        self.AlternateSpeeds = alternate_speeds
        self.AutoMdix = auto_mdix
        self.AutoNegotiation = auto_negotiation
        self.AutoNegotiationMasterSlave = auto_negotiation_master_slave
        self.AutoNegotiationMasterSlaveEnable = auto_negotiation_master_slave_enable
        self.CollisionExponent = collision_exponent
        self.CustomFecMode = custom_fec_mode
        self.DataPathMode = data_path_mode
        self.DownshiftEnable = down_shift_enable
        self.Duplex = duplex
        self.FlowControl = flow_control
        self.ForwardErrorCorrection = forward_error_correction
        self.IgnoreLinkStatus = ignore_link_status
        self.InternalPpmAdjust = internal_ppm_adjust
        self.LineSpeed = line_speed
        self.Mtu = mtu
        self.OptimizedXon = optimize_xon
        self.PerformanceMode = performance_mode
        self.PortSetupMode = port_setup_mode
        self.TestMode = test_mode
        self.TransmitClockSource = transmit_clock_source

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle

    def __str__(self):
        return "EthernetCopper"


class Ethernet10GigFiberInterface(object):
    SPEED_UNKNOWN = "SPEED_UNKNOWN"
    SPEED_1G = "SPEED_1G"
    CUSTOM_FEC_MODE_KR = "KR_FEC"
    CUSTOM_FEC_MODE_RS = "RS_FEC"
    CUSTOM_FEC_MODE_KP4 = "KP4_FEC"
    CUSTOM_FEC_MODE_NONE = "NONE"
    DATA_PATH_MODE_NORMAL = "NORMAL"
    DATA_PATH_MODE_LOCAL_LOOPBACK = "LOCAL_LOOPBACK"
    DATA_PATH_MODE_LINE_MONITOR = "LINE_MONITOR"
    FULL_DUPLEX = "FULL"
    HALF_DUPLEX = "HALF"
    _spirent_handle = None

    def __init__(self, advertise_ieee=True, advertise_nbaset=True, alternate_speeds=SPEED_UNKNOWN,
                 auto_negotiation=True, auto_negotiation_master_slave="MASTER",
                 auto_negotiation_master_slave_enable=True, cable_type_length="OPTICAL", cfp_interface="ACC_6068A",
                 collision_exponent=10, custom_fec_mode=CUSTOM_FEC_MODE_KR,
                 data_path_mode=DATA_PATH_MODE_NORMAL, deficit_idle_count=False, detection_mode="AUTO_DETECT",
                 down_shift_enable=False, duplex=FULL_DUPLEX, flow_control=False,
                 forward_error_correction=True, ignore_link_status=False, internal_ppm_adjust=0,
                 is_pfc_negotiated=False, line_speed=SPEED_1G, port_mode="LAN",
                 mtu=1500, optimize_xon="DISABLE", performance_mode="STC_DEFAULT", port_setup_mode="PORTCONFIG_ONLY",
                 test_mode="NORMAL_OPERATION", transmit_clock_source="INTERNAL"):
        self.AdvertiseIEEE = advertise_ieee
        self.AdvertiseNBASET = advertise_nbaset
        self.AlternateSpeeds = alternate_speeds
        self.CableTypeLength = cable_type_length
        self.CfpInterface = cfp_interface
        self.AutoNegotiation = auto_negotiation
        self.AutoNegotiationMasterSlave = auto_negotiation_master_slave
        self.AutoNegotiationMasterSlaveEnable = auto_negotiation_master_slave_enable
        self.CollisionExponent = collision_exponent
        self.CustomFecMode = custom_fec_mode
        self.DataPathMode = data_path_mode
        self.DeficitIdleCount = deficit_idle_count
        self.DetectionMode = detection_mode
        self.DownshiftEnable = down_shift_enable
        self.Duplex = duplex
        self.FlowControl = flow_control
        self.ForwardErrorCorrection = forward_error_correction
        self.IgnoreLinkStatus = ignore_link_status
        self.InternalPpmAdjust = internal_ppm_adjust
        self.IsPfcNegotiated = is_pfc_negotiated
        self.LineSpeed = line_speed
        self.Mtu = mtu
        self.OptimizedXon = optimize_xon
        self.PortMode = port_mode
        self.PerformanceMode = performance_mode
        self.PortSetupMode = port_setup_mode
        self.TestMode = test_mode
        self.TransmitClockSource = transmit_clock_source

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle

    def __str__(self):
        return "Ethernet10GigFiber"


class Ethernet100GigFiberInterface(object):
    SPEED_UNKNOWN = "SPEED_UNKNOWN"
    SPEED_1G = "SPEED_1G"
    SPEED_100G = "SPEED_100G"
    SPEED_25G = "SPEED_25G"
    CUSTOM_FEC_MODE_KR = "KR_FEC"
    CUSTOM_FEC_MODE_RS = "RS_FEC"
    CUSTOM_FEC_MODE_KP4 = "KP4_FEC"
    CUSTOM_FEC_MODE_NONE = "NONE"
    DATA_PATH_MODE_NORMAL = "NORMAL"
    DATA_PATH_MODE_LOCAL_LOOPBACK = "LOCAL_LOOPBACK"
    DATA_PATH_MODE_LINE_MONITOR = "LINE_MONITOR"
    FULL_DUPLEX = "FULL"
    HALF_DUPLEX = "HALF"
    _spirent_handle = None

    def __init__(self, advertise_ieee=True, advertise_nbaset=True, alternate_speeds=SPEED_UNKNOWN,
                 auto_negotiation=True, auto_negotiation_master_slave="MASTER",
                 auto_negotiation_master_slave_enable=True, cable_type_length="OPTICAL", cfp_interface="ACC_6068A",
                 collision_exponent=10, custom_fec_mode=CUSTOM_FEC_MODE_KR,
                 data_path_mode=DATA_PATH_MODE_NORMAL, deficit_idle_count=True, detection_mode="AUTO_DETECT",
                 down_shift_enable=False, duplex=FULL_DUPLEX, flow_control=False,
                 forward_error_correction=True, ignore_link_status=False, internal_ppm_adjust=0,
                 is_pfc_negotiated=False, line_speed=SPEED_1G, priority_flow_control_array=False,
                 mtu=1500, optimize_xon="DISABLE", performance_mode="STC_DEFAULT", port_setup_mode="PORTCONFIG_ONLY",
                 test_mode="NORMAL_OPERATION", transmit_clock_source="INTERNAL"):
        self.AdvertiseIEEE = advertise_ieee
        self.AdvertiseNBASET = advertise_nbaset
        self.AlternateSpeeds = alternate_speeds
        self.CableTypeLength = cable_type_length
        self.CfpInterface = cfp_interface
        self.AutoNegotiation = auto_negotiation
        self.AutoNegotiationMasterSlave = auto_negotiation_master_slave
        self.AutoNegotiationMasterSlaveEnable = auto_negotiation_master_slave_enable
        self.CollisionExponent = collision_exponent
        self.CustomFecMode = custom_fec_mode
        self.DataPathMode = data_path_mode
        self.DeficitIdleCount = deficit_idle_count
        self.DetectionMode = detection_mode
        self.DownshiftEnable = down_shift_enable
        self.Duplex = duplex
        self.FlowControl = flow_control
        self.ForwardErrorCorrection = forward_error_correction
        self.IgnoreLinkStatus = ignore_link_status
        self.InternalPpmAdjust = internal_ppm_adjust
        self.IsPfcNegotiated = is_pfc_negotiated
        self.LineSpeed = line_speed
        self.Mtu = mtu
        self.OptimizedXon = optimize_xon
        self.PerformanceMode = performance_mode
        self.PortSetupMode = port_setup_mode
        self.PriorityFlowControlArray = priority_flow_control_array
        self.TestMode = test_mode
        self.TransmitClockSource = transmit_clock_source

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle

    def __str__(self):
        return "Ethernet100GigFiber"


class Ethernet25GigFiberInterface(object):
    SPEED_UNKNOWN = "SPEED_UNKNOWN"
    SPEED_1G = "SPEED_1G"
    SPEED_100G = "SPEED_100G"
    SPEED_25G = "SPEED_25G"
    CUSTOM_FEC_MODE_KR = "KR_FEC"
    CUSTOM_FEC_MODE_RS = "RS_FEC"
    CUSTOM_FEC_MODE_KP4 = "KP4_FEC"
    CUSTOM_FEC_MODE_NONE = "NONE"
    DATA_PATH_MODE_NORMAL = "NORMAL"
    DATA_PATH_MODE_LOCAL_LOOPBACK = "LOCAL_LOOPBACK"
    DATA_PATH_MODE_LINE_MONITOR = "LINE_MONITOR"
    FULL_DUPLEX = "FULL"
    HALF_DUPLEX = "HALF"
    _spirent_handle = None

    def __init__(self, advertise_ieee=True, advertise_nbaset=True, alternate_speeds=SPEED_UNKNOWN,
                 auto_negotiation=True, auto_negotiation_master_slave="MASTER",
                 auto_negotiation_master_slave_enable=True, cable_type_length="OPTICAL", cfp_interface="ACC_6068A",
                 collision_exponent=10, custom_fec_mode=CUSTOM_FEC_MODE_KR,
                 data_path_mode=DATA_PATH_MODE_NORMAL, deficit_idle_count=False, detection_mode="AUTO_DETECT",
                 down_shift_enable=False, duplex=FULL_DUPLEX, flow_control=False,
                 forward_error_correction=True, ignore_link_status=False, internal_ppm_adjust=0,
                 is_pfc_negotiated=False, line_speed=SPEED_1G, priority_flow_control_array=False,
                 mtu=1500, optimize_xon="DISABLE", performance_mode="STC_DEFAULT", port_setup_mode="PORTCONFIG_ONLY",
                 test_mode="NORMAL_OPERATION", transmit_clock_source="INTERNAL"):
        self.AdvertiseIEEE = advertise_ieee
        self.AdvertiseNBASET = advertise_nbaset
        self.AlternateSpeeds = alternate_speeds
        self.CableTypeLength = cable_type_length
        self.CfpInterface = cfp_interface
        self.AutoNegotiation = auto_negotiation
        self.AutoNegotiationMasterSlave = auto_negotiation_master_slave
        self.AutoNegotiationMasterSlaveEnable = auto_negotiation_master_slave_enable
        self.CollisionExponent = collision_exponent
        self.CustomFecMode = custom_fec_mode
        self.DataPathMode = data_path_mode
        self.DeficitIdleCount = deficit_idle_count
        self.DetectionMode = detection_mode
        self.DownshiftEnable = down_shift_enable
        self.Duplex = duplex
        self.FlowControl = flow_control
        self.ForwardErrorCorrection = forward_error_correction
        self.IgnoreLinkStatus = ignore_link_status
        self.InternalPpmAdjust = internal_ppm_adjust
        self.IsPfcNegotiated = is_pfc_negotiated
        self.LineSpeed = line_speed
        self.Mtu = mtu
        self.OptimizedXon = optimize_xon
        self.PerformanceMode = performance_mode
        self.PortSetupMode = port_setup_mode
        self.PriorityFlowControlArray = priority_flow_control_array
        self.TestMode = test_mode
        self.TransmitClockSource = transmit_clock_source

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle

    def __str__(self):
        return "Ethernet25GigFiber"


class AnalyzerConfig(object):
    HISTOGRAM_MODE_INTERARRIVAL_TIME = "INTERARRIVAL_TIME"
    HISTOGRAM_MODE_LATENCY = "LATENCY"
    HISTOGRAM_MODE_FRAME_LENGTH = "FRAME_LENGTH"
    HISTOGRAM_MODE_SEQ_RUN_LENGTH = "SEQ_RUN_LENGTH"
    HISTOGRAM_MODE_SEQ_DIFF_CHECK = "SEQ_DIFF_CHECK"
    HISTOGRAM_MODE_JITTER = "JITTER"
    LATENCY_MODE_PER_STREAM_RX_LATENCY_OFF = "PER_STREAM_RX_LATENCY_OFF"
    LATENCY_MODE_PER_STREAM_RX_LATENCY_ON = "PER_STREAM_RX_LATENCY_ON"
    LATENCY_MODE_LATENCY_MODE_OFF_4096_RX_STREAMS = "LATENCY_MODE_OFF_4096_RX_STREAMS"
    LATENCY_MODE_LATENCY_MODE_OFF_1024_RX_STREAMS = "LATENCY_MODE_OFF_1024_RX_STREAMS"
    SIG_MODE_LONG_SEQ_NUM = "LONG_SEQ_NUM"
    SIG_MODE_ENHANCED_DETECTION = "ENHANCED_DETECTION"
    TIME_STAMP_LATCH_MDOE_START_OF_FRAME = "START_OF_FRAME"
    TIME_STAMP_LATCH_MODE_END_OF_FRAME = "END_OF_FRAME"
    _spirent_handle = None

    def __init__(self, adv_seq_checker_late_threshold="1000", alternate_sig_offset="0",
                 histogram_mode=HISTOGRAM_MODE_LATENCY,
                 jumbo_frame_threshold="1518", latency_mode=LATENCY_MODE_PER_STREAM_RX_LATENCY_ON,
                 oversize_frame_threshold="9018",
                 sig_mode=SIG_MODE_ENHANCED_DETECTION, timestamp_latch_mode=TIME_STAMP_LATCH_MDOE_START_OF_FRAME,
                 undersize_frame_threshold="64",
                 vlan_alternate_tpid="34984"):
        self.AdvSeqCheckerLateThreshold = adv_seq_checker_late_threshold
        self.AlternateSigOffset = alternate_sig_offset
        self.HistogramMode = histogram_mode
        self.JumboFrameThreshold = jumbo_frame_threshold
        self.LatencyMode = latency_mode
        self.OversizeFrameThreshold = oversize_frame_threshold
        self.SigMode = sig_mode
        self.TimestampLatchMode = timestamp_latch_mode
        self.UndersizeFrameThreshold = undersize_frame_threshold
        self.VlanAlternateTpid = vlan_alternate_tpid

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Ethernet8023MacControlHeader(object):
    HEADER_TYPE = "ethernet:Ethernet8023Raw"
    _spirent_handle = None

    def __init__(self, destination_mac="00:00:01:00:00:01", source_mac="00:10:94:00:00:02", length="",
                 preamble="55555555555555d5"):
        self.dstMac = destination_mac
        self.srcMac = source_mac
        self.Length = length
        self.preamble = preamble

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class MacControlHeader(object):
    HEADER_TYPE = "ethernetpause:MacControl"
    _spirent_handle = None

    def __init__(self, destination_mac="00:00:01:00:00:01", source_mac="00:10:94:00:00:02", length="8808",
                 preamble="55555555555555d5"):
        self.dstMac = destination_mac
        self.srcMac = source_mac
        self.lengthType = length
        self.preamble = preamble

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class PauseMacControlHeader(object):
    HEADER_TYPE = "ethernetpause:PauseMacControl"
    _spirent_handle = None

    def __init__(self, op_code="0001", pause_time=0, reserved=""):
        self.opCode = op_code
        self.pauseTime = pause_time
        self.reserved = reserved

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class PriorityFlowControlHeader(object):
    HEADER_TYPE = "ethernetpause:PFC"
    _spirent_handle = None

    def __init__(self, op_code="0101", time0="", time1="", time2="", time3="", time4="", time5="", time6="", time7="",
                 reserved=""):
        self.opCode = op_code
        self.time0 = time0
        self.time1 = time1
        self.time2 = time2
        self.time3 = time3
        self.time4 = time4
        self.time5 = time5
        self.time6 = time6
        self.time7 = time7
        self.reserved = reserved

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class CustomBytePatternHeader(object):
    HEADER_TYPE = "custom:Custom"
    _spirent_handle = None

    def __init__(self, byte_pattern=""):
        self.pattern = byte_pattern

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class Capture(object):
    WRAP = 'WRAP'
    STOP_ON_FULL = 'STOP_ON_FULL'
    FRAMECONTENT = 'FRAMECONTENT'
    BYTEOFFSETANDRANGE = 'BYTEOFFSETANDRANGE'
    IEEE80211FRAMECONTENT = 'IEEE80211FRAMECONTENT'
    IDLE = 'IDLE'
    SAVING = 'SAVING'
    RETRIEVING = 'RETRIEVING'
    REGULAR_FLAG_MODE = 'REGULAR_FLAG_MODE'
    ADV_SEQ_FLAG_MODE = 'ADV_SEQ_FLAG_MODE'
    REGULAR_MODE = 'REGULAR_MODE'
    SIG_MODE = 'SIG_MODE'
    IEEE80211_MODE = 'IEEE80211_REGULAR_MODE'
    REALTIME_DISABLE = 'REALTIME_DISABLE'
    REALTIME_ENABLE = 'REALTIME_ENABLE'
    DISABLE = 'DISABLE'
    ENABLE = 'ENABLE'
    PREAMBLE = 'PREAMBLE'
    FRAME = 'FRAME'
    IP = 'IP'
    IP_PAYLOAD = 'IP_PAYLOAD'
    TX_MODE = 'TX_MODE'
    RX_MODE = 'RX_MODE'
    TX_RX_MODE = 'TX_RX_MODE'
    _spirent_handle = None

    def __init__(self, abort_save_task=False, buffer_mode=WRAP, capture_filter_mode=FRAMECONTENT,
                 current_filter_bytes_used=0, current_filters_used=0, current_task=IDLE, elapsed_time='0:00:00',
                 flag_mode=REGULAR_FLAG_MODE, ieee80211_filter_string="", increased_memory_support=False,
                 mode=REGULAR_MODE, real_time_buffer_status=False, real_time_frames_buffer=0,
                 real_time_mode=REALTIME_DISABLE, slice_capture_size=128, slice_mode=DISABLE, slice_offset=0,
                 slice_offset_ref=PREAMBLE, src_mode=TX_RX_MODE, start='0x00004000', stop='0x00000000', tab_index=0):
        self.AbortSaveTask = abort_save_task
        self.BufferMode = buffer_mode
        self.CaptureFilterMode = capture_filter_mode
        self.CurrentFilterBytesUsed = current_filter_bytes_used
        self.CurrentFiltersUsed = current_filters_used
        self.CurrentTask = current_task
        self.ElapsedTime = elapsed_time
        self.FlagMode = flag_mode
        self.Ieee80211FilterString = ieee80211_filter_string
        self.IncreasedMemorySupport = increased_memory_support
        self.Mode = mode
        self.RealTimeBufferStatus = real_time_buffer_status
        self.RealTimeFramesBuffer = real_time_frames_buffer
        self.RealTimeMode = real_time_mode
        self.SliceCaptureSize = slice_capture_size
        self.SliceMode = slice_mode
        self.SliceOffset = slice_offset
        self.SliceOffsetRef = slice_offset_ref
        self.srcMode = src_mode
        self.Start = start
        self.Stop = stop
        self.TabIndex = tab_index

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class ARP(object):
    HEADER_TYPE = "arp:ARP"
    ETHERNET = '0001'
    ARP_OPERATION_UNKNOWN = 0
    ARP_OPERATION_REQUEST = 1
    ARP_OPERATION_REPLY = 2
    INTERNET_IP = '0800'
    _spirent_handle = None

    def __init__(self, hardware=ETHERNET, hardware_address_length=6, protocol_address_length=4, name=None,
                 operation=ARP_OPERATION_REQUEST, protocol=INTERNET_IP, sender_hw_address='00:00:01:00:00:02',
                 sender_ip_address='192.85.1.2', target_hw_address='00:00:00:00:00:00', target_ip_address='0.0.0.0'):
        self.hardware = hardware
        self.ihAddr = hardware_address_length
        self.ipAddr = protocol_address_length
        self.Name = name
        self.operation = operation
        self.protocol = protocol
        self.senderHwAddr = sender_hw_address
        self.senderPAddr = sender_ip_address
        self.targetHwAddr = target_hw_address
        self.targetPAddr = target_ip_address

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class RARP(object):
    HEADER_TYPE = "arp:RARP"
    ETHERNET = "0001"
    RARP_OPERATION_UNKNOWN = 0
    RARP_OPERATION_REQUEST = 3
    RARP_OPERATION_REPLY = 4
    INTERNET_IP = '0800'
    _spirent_handle = None

    def __init__(self, hardware=ETHERNET, hardware_address_length=6, protocol_address_length=4, name=None,
                 operation=RARP_OPERATION_REQUEST, protocol=INTERNET_IP, sender_hw_address='00:00:01:00:00:02',
                 sender_ip_address='192.85.1.2', target_hw_address='00:00:00:00:00:00', target_ip_address='0.0.0.0'):
        self.hardware = hardware
        self.ihAddr = hardware_address_length
        self.ipAddr = protocol_address_length
        self.Name = name
        self.operation = operation
        self.protocol = protocol
        self.senderHwAddr = sender_hw_address
        self.senderPAddr = sender_ip_address
        self.targetHwAddr = target_hw_address
        self.targetPAddr = target_ip_address

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class TosDiffServ(object):
    HEADER_TYPE = "tosDiffServ"
    _spirent_handle = None

    def __init__(self, name=None):
        self.name = name

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class DiffServ(object):
    HEADER_TYPE = "diffServ"
    _spirent_handle = None

    def __init__(self, dscp_high=0, dscp_low=0, name=None, reserved='00'):
        self.dscpHigh = dscp_high
        self.dscpLow = dscp_low
        self.Name = name
        self.reserved = reserved

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Tos(object):
    HEADER_TYPE = "tos"
    NETWORK_CONTROL = 7
    INTERNETWORK_CONTROL = 6
    CRITIC_ECP = 5
    FLASH_OVERRIDE = 4
    FLASH = 3
    IMEEDIATE = 2
    PRIORITY = 1
    ROUTINE = 0
    _spirent_handle = None

    def __init__(self, d_bit=0, m_bit=0, name=None, precedence=ROUTINE, r_bit=0, reserved=0, t_bit=0):
        self.dBit = d_bit
        self.mBit = m_bit
        self.Name = name
        self.precedence = precedence
        self.rBit = r_bit
        self.reserved = reserved
        self.tBit = t_bit

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class UDP(object):
    HEADER_TYPE = "udp:UDP"
    TCPMUX = 1
    CHECKSUM_ERROR = '65535'
    _spirent_handle = None

    def __init__(self, checksum='', destination_port=1024, length=0, source_port=1024, name=None):
        self.checksum = checksum
        self.destPort = destination_port
        self.length = length
        self.sourcePort = source_port
        if not name:
            name = 'anon_' + str(uuid4()).split('-')[0]
        self.Name = name

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class TCP(object):
    HEADER_TYPE = "tcp:TCP"
    TCPMUX = 1
    DESTINATION_PORT_BGP = 179
    CHECKSUM_ERROR = '65535'
    _spirent_handle = None

    def __init__(self, ack_bit='1', ack_num=234567, checksum='', cwr_bit='0', destination_port=1024, ecn_bit='0',
                 finish_bit='0', offset=5, push_bit='0', reserved='0000', reset_bit='0', seq_num=123456,
                 source_port=1024, sync_bit='0', urgent_bit='0', urgent_pointer=0, window=4096,
                 name=None):
        self.window = window
        self.urgentPtr = urgent_pointer
        self.urgBit = urgent_bit
        self.synBit = sync_bit
        self.sourcePort = source_port
        self.seqNum = seq_num
        self.rstBit = reset_bit
        self.reserved = reserved
        self.pshBit = push_bit
        self.offset = offset
        self.finBit = finish_bit
        self.ecnBit = ecn_bit
        self.destPort = destination_port
        self.cwrBit = cwr_bit
        self.checksum = checksum
        self.ackNum = ack_num
        self.ackBit = ack_bit
        if not name:
            name = 'anon_' + str(uuid4()).split('-')[0]
        self.Name = name

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class VxLAN(object):
    HEADER_TYPE = "vxlan:VxLAN"
    _spirent_handle = None

    def __init__(self, auto_select_udp_src_port=1, enable_vm_arp_sending_for_evpn_learning=0, evpn_learning_enabled=0,
                 flags=8, multicast_group_address='255.0.0.1', reserve_done=0, reserved_two=0,
                 resolved_ipv4_address='0.0.0.0', source_vtep_interface_address='0.0.0.0', source_vtep_router_id='0.0.0.0',
                 traffic_control_flags=0, use_target_ip_for_vm_arp=0, vni=0, vxlanIpAddressMode=0):
        self.vxlanIpAddressMode = vxlanIpAddressMode
        self.vni = vni
        self.useTargetIpForVmArp = use_target_ip_for_vm_arp
        self.trafficControlFlags = traffic_control_flags
        self.srcVtepRouterId = source_vtep_router_id
        self.srcVtepinterfaceAddr = source_vtep_interface_address
        self.resolvedIpv4Addr = resolved_ipv4_address
        self.reservedtwo = reserved_two
        self.reservedone = reserve_done
        self.multicastGroupAddr = multicast_group_address
        self.flags = flags
        self.evpnLearningEnabled = evpn_learning_enabled
        self.enableVmArpSendingForEvpnLearning = enable_vm_arp_sending_for_evpn_learning
        self.autoSelectUdpSrcPort = auto_select_udp_src_port

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class RangeModifier(object):
    HEADER_TYPE = 'RangeModifier'
    NATIVE = 'NATIVE'
    BYTE = 'BYTE'
    INCR = 'INCR'
    DECR = 'DECR'
    SHUFFLE = 'SHUFFLE'

    def __init__(self, data='00', data_type=NATIVE, enable_stream=False, mask='65535', modifier_mode=INCR, offset='0',
                 offset_reference='', recycle_count='0', repeat_count='0', step_value='01'):
        self.StepValue = step_value
        self.RepeatCount = repeat_count
        self.RecycleCount = recycle_count
        self.OffsetReference = offset_reference
        self.Offset = offset
        self.ModifierMode = modifier_mode
        self.Mask = mask
        self.EnableStream = enable_stream
        self.DataType = data_type
        self.Data = data

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class IcmpEchoRequestHeader(object):
    HEADER_TYPE = "icmp:IcmpEchoRequest"
    ECHO_REQUEST_TYPE = 8

    def __init__(self, checksum='', code=0, echo_data="0000", identifier=0, name=None, sequence_num=0,
                 icmp_type=ECHO_REQUEST_TYPE):
        self.checksum = checksum
        self.code = code
        self.data = echo_data
        self.identifier = identifier
        self.name = name
        self.seqNum = sequence_num
        self.type = icmp_type

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Ospfv2HelloHeader(object):
    HEADER_TYPE = "ospfv2:Ospfv2Hello"

    def __init__(self, backup_designated_router="2.2.2.2", designated_router='1.1.1.1', hello_interval=10, name=None,
                 network_mask="255.255.255.0", router_dead_priority=0, router_dead_interval=40):
        self.backupDesignatedRouter = backup_designated_router
        self.designatedRouter = designated_router
        self.helloInterval = hello_interval
        self.Name = name
        self.networkMask = network_mask
        self.routerDeadInterval = router_dead_interval
        self.routerPriority = router_dead_priority

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Ospfv2LinkStateUpdateHeader(object):
    HEADER_TYPE = "ospfv2:Ospfv2LinkStateUpdate"

    def __init__(self, name=None, number_of_lsas=0):
        self.Name = name
        self.numberOfLsas = number_of_lsas

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Pimv4HelloHeader(object):
    HEADER_TYPE = "pim:Pimv4Hello"

    def __init__(self, name=None):
        self.Name = name

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Igmpv1Header(object):
    HEADER_TYPE = "igmp:igmpv1"
    MESSAGE_TYPE_V1_QUERY = 1
    MESSAGE_TYPE_V1_REPORT = 2

    def __init__(self, checksum='', group_address="225.0.0.1", name=None, message_type=MESSAGE_TYPE_V1_REPORT,
                 unused=0, version=1):
        self.checksum = checksum
        self.groupAddress = group_address
        self.Name = name
        self.type = message_type
        self.unused = unused
        self.version = version

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class IPv4HeaderOptionTimestamp(object):
    PARENT_HEADER_OPTION = "IPv4HeaderOption"
    OPTION_TYPE = "timestamp"
    OPTION_TYPE_TIMESTAMP = 68

    def __init__(self, flag=0, length=5, name=None, overflow=0, pointer=0, timestamp="",
                 option_type=OPTION_TYPE_TIMESTAMP):
        self.flag = flag
        self.length = length
        self.Name = name
        self.overflow = overflow
        self.pointer = pointer
        self.timestamp = timestamp
        self.type = option_type

    def get_attributes_dict(self):
        return vars(self)


class IPv4HeaderOptionLooseSourceRoute(object):
    PARENT_HEADER_OPTION = "IPv4HeaderOption"
    OPTION_TYPE = "looseSrcRoute"
    OPTION_TYPE_LOOSE_SRC_ROUTE = 131

    def __init__(self, length=0, name=None, pointer=4, option_type=OPTION_TYPE_LOOSE_SRC_ROUTE):
        self.length = length
        self.Name = name
        self.pointer = pointer
        self.type = option_type

    def get_attributes_dict(self):
        return vars(self)


class DhcpClientMessageHeader(object):
    HEADER_TYPE = "dhcp:Dhcpclientmsg"

    def __init__(self, boot_file_name='', boot_p_flag='8000', client_address='192.85.1.2',
                 client_hw_pad='', client_mac='00:00:01:00:00:02', elapsed=0, haddrlen=6, hardware_type=1, hops=0,
                 magic_cookie=63825363, message_type=1, name=None, next_server_address='0.0.0.0',
                 relay_agent_address='0.0.0.0', server_host_name='', xid=1, your_address='0.0.0.0'):
        self.bootfilename = boot_file_name
        self.bootpflags = boot_p_flag
        self.clientAddr = client_address
        self.clientHWPad = client_hw_pad
        self.elapsed = elapsed
        self.haddrLen = haddrlen
        self.hardwareType = hardware_type
        self.hops = hops
        self.magiccookie = magic_cookie
        self.messageType = message_type
        self.Name = name
        self.nextservAddr = next_server_address
        self.relayagentAddr = relay_agent_address
        self.serverhostname = server_host_name
        self.xid = xid
        self.yourAddr = your_address

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class Rfc2544ThroughputConfig(object):
    ASYMMETRIC_TRAFFIC_BACK_OFF_MODE_ALL_RATES = "ALL_RATES"
    ASYMMETRIC_TRAFFIC_BACK_OFF_MODE_FAILED_RATES = "FAILED_RATES"
    LOAD_UNIT_PERCENT_LINE_RATE = "PERCENT_LINE_RATE"
    LOAD_UNIT_FRAMES_PER_SECOND = "FRAMES_PER_SECOND"
    LOAD_UNIT_INTER_BURST_PER_GAP = "INTER_BURST_GAP"
    LOAD_UNIT_BITS_PER_SECOND = "BITS_PER_SECOND"
    LOAD_UNIT_KILOBITS_PER_SECOND = "KILOBITS_PER_SECOND"
    LOAD_UNIT_MEGABITS_PER_SECOND = "MEGABITS_PER_SECOND"
    FRAME_SIZE_ITERATION_MODE_CUSTOM = "CUSTOM"
    FRAME_SIZE_ITERATION_MODE_RANDOM = "RANDOM"
    FRAME_SIZE_ITERATION_MODE_STEP = "STEP"
    FRAME_SIZE_ITERATION_MODE_IMIX = "IMIX"
    FRAME_SIZE_ITERATION_MODE_NONE = "NONE"
    LATENCY_TYPE_LILO = "LILO"
    LATENCY_TYPE_LIFO = "LIFO"
    LATENCY_TYPE_FIFO = "FIFO"
    LEARNING_FREQUENCY_MODE_ONCE = "LEARN_ONCE"
    LEARNING_FREQUENCY_MODE_EVERY_TRIAL = "LEARN_EVERY_TRIAL"
    LEARNING_FREQUENCY_MODE_EVERY_FRAME_SIZE = "LEARN_EVERY_FRAME_SIZE"
    LEARNING_FREQUENCY_MODE_EVERY_ITERATION = "LEARN_EVERY_ITERATION"
    LEARNING_MODE_L2 = "L2_LEARNING"
    LEARNING_MODE_L3 = "L3_LEARNING"
    PROFILE_CONFIG_MODE_MANUAL = "MANUAL"
    PROFILE_CONFIG_MODE_PER_PORT = "PER_PORT"
    PROFILE_CONFIG_MODE_PER_SIDE = "PER_SIDE"
    PROFILE_CONFIG_MODE_PER_GROUP = "PER_GROUP"
    SEARCH_MODE_BINARY = "BINARY"
    SEARCH_MODE_STEP = "STEP"
    SEARCH_MODE_COMBO = "COMBO"
    TRAFFIC_START_DELAY_MODE_AFTER_TEST = "AFTER_TEST"
    TRAFFIC_START_DELAY_MODE_AFTER_USER_RESPONSE = "AFTER_USER_RESPONSE"
    TRAFFIC_VERIFICATION_FEQ_MODE_TRIAL = "VERIFY_EVERY_TRIAL"
    TRAFFIC_VERIFICATION_FEQ_MODE_FRAME_SIZE = "VERIFY_EVERY_FRAME_SIZE"
    TRAFFIC_VERIFICATION_FEQ_MODE_ITERATION = "VERIFY_EVERY_ITERATION"
    DURATION_MODE_SECONDS = "SECONDS"
    DURATION_MODE_BURSTS = "BURSTS"

    def __init__(self, acceptable_frame_loss=0, back_off=50, custom_frame_size_list=0,
                 delay_after_transmission=2, display_laod_unit=LOAD_UNIT_PERCENT_LINE_RATE,
                 display_traffic_group_load_unit=LOAD_UNIT_PERCENT_LINE_RATE, duration_bursts=1000, duration_seconds=10,
                 enable_detailed_results_collection=False, enable_exposedf_internal_commands=False,
                 enable_frame_size_on_test=True, enable_jitter_measurement=True, enable_learning=False,
                 enable_max_latency_threshold=False, enable_out_of_seq_threshold=False,
                 enable_pause_before_traffic=False, enable_traffic_verification=False, frame_size_end=256,
                 frame_size_iteration_mode=FRAME_SIZE_ITERATION_MODE_CUSTOM, frame_size_start=128, frame_size_step=128,
                 ignore_min_max_limits=False, imix_distribution_list=0, imix_distribution_string="",
                 l2_delay_before_learning=2, l2_learning_frame_rate=1000, l2_learning_repeat_count=5,
                 l3_delay_before_learning=2, l3_enable_cyclic_addr_resolution=True, l3_rate=1000, l3_retry_count=5,
                 latency_type=LATENCY_TYPE_LILO, learning_frequency_mode=LEARNING_FREQUENCY_MODE_ONCE,
                 learning_mode=LEARNING_MODE_L3, max_latency_threshold=30, num_of_trials=2, out_of_seq_threshold=0,
                 profile_config_group_type="", profile_config_mode=PROFILE_CONFIG_MODE_MANUAL, random_max_frame_size=256,
                 random_min_frame_size=128, rate_initial=10, rate_lower_limit=1, rate_upper_limit=100, rate_step=10,
                 resolution=1, search_mode=SEARCH_MODE_BINARY, stagger_start_delay=0, traffic_start_delay=2,
                 traffic_start_delay_mode=TRAFFIC_START_DELAY_MODE_AFTER_TEST, traffic_verfication_abort_on_fail=True,
                 traffic_verification_feq_mode=TRAFFIC_VERIFICATION_FEQ_MODE_ITERATION,
                 traffic_verfication_tx_frame_count=100, traffic_verification_tx_frame_rate=1000,
                 use_existing_stream_blocks=True, duration_mode=DURATION_MODE_SECONDS,
                 asymmetric_traffic_back_off_mode=ASYMMETRIC_TRAFFIC_BACK_OFF_MODE_FAILED_RATES):
        self.Name = ""
        self.Active = True
        self.ProfileConfigMode = profile_config_mode
        self.L3Rate = l3_rate
        self.LearningMode = learning_mode
        self.RateStep = rate_step
        self.L2DelayBeforeLearning = l2_delay_before_learning
        self.MaxLatencyThreshold = max_latency_threshold
        self.FrameSizeEnd = frame_size_end
        self.EnablePauseBeforeTraffic = enable_pause_before_traffic
        self.OutOfSeqThreshold = out_of_seq_threshold
        self.TrafficStartDelayMode = traffic_start_delay_mode
        self.L3DelayBeforeLearning = l3_delay_before_learning
        self.L3RetryCount = l3_retry_count
        self.LearningFreqMode = learning_frequency_mode
        self.RateInitial = rate_initial
        self.L2LearningRepeatCount = l2_learning_repeat_count
        self.AcceptableFrameLoss = acceptable_frame_loss
        self.AsymmetricTrafficBackoffMode = asymmetric_traffic_back_off_mode
        self.TrafficStartDelay = traffic_start_delay
        self.CustomFrameSizeList = custom_frame_size_list
        self.RandomMaxFrameSize = random_max_frame_size
        self.DelayAfterTransmission = delay_after_transmission
        self.RateUpperLimit = rate_upper_limit
        self.FrameSizeIterationMode = frame_size_iteration_mode
        self.L3EnableCyclicAddrResolution = l3_enable_cyclic_addr_resolution
        self.UseExistingStreamBlocks = use_existing_stream_blocks
        self.EnableJitterMeasurement = enable_jitter_measurement
        self.TrafficVerificationAbortOnFail = traffic_verfication_abort_on_fail
        self.DisplayTrafficGroupLoadUnit = display_traffic_group_load_unit
        self.LatencyType = latency_type
        self.EnableMaxLatencyThreshold = enable_max_latency_threshold
        self.RateLowerLimit = rate_lower_limit
        self.EnableFrameSizeOnTest = enable_frame_size_on_test
        self.TrafficVerificationTxFrameCount = traffic_verfication_tx_frame_count
        self.IgnoreMinMaxLimits = ignore_min_max_limits
        self.RandomMinFrameSize = random_min_frame_size
        self.DurationMode = duration_mode
        self.SearchMode = search_mode
        self.L2LearningFrameRate = l2_learning_frame_rate
        self.TrafficVerificationFreqMode = traffic_verification_feq_mode
        self.DisplayLoadUnit = display_laod_unit
        self.StaggerStartDelay = stagger_start_delay
        self.NumOfTrials = num_of_trials
        self.Resolution = resolution
        self.EnableExposedInternalCommands = enable_exposedf_internal_commands
        self.TrafficVerificationTxFrameRate = traffic_verification_tx_frame_rate
        self.EnableDetailedResultsCollection = enable_detailed_results_collection
        self.DurationBursts = duration_bursts
        self.ProfileConfigGroupType = profile_config_group_type
        self.EnableOutOfSeqThreshold = enable_out_of_seq_threshold
        self.ImixDistributionString = imix_distribution_string
        self.Backoff = back_off
        self.DurationSeconds = duration_seconds
        self.EnableLearning = enable_learning
        self.EnableTrafficVerification = enable_traffic_verification
        self.FrameSizeStart = frame_size_start
        self.ImixDistributionList = imix_distribution_list
        self.FrameSizeStep = frame_size_step

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key or 'children' in key or 'parent' in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_object_attributes(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


class FecModeObject(object):

    FEC_MODE_NONE = "NONE"
    FEC_MODE_FORCE = "FORCE"
    FEC_MODE_IEEE = "IEEE"
    FEC_PHY_TYPE_NONE = "NONE"
    FEC_TYPE_NONE = "NONE"
    FEC_TYPE_CLAUSE108 = "CLAUSE_108_RS"
    FEC_TYPE_CLAUSE74 = "CLAUSE_74_BASE_R"
    FEC_TYPE_CLAUSE91 = "CLAUSE_91_RS"

    def __init__(self, fecaction="DISABLE", fecmode=FEC_MODE_NONE, fecphytype=FEC_PHY_TYPE_NONE, fectype=FEC_TYPE_NONE):
        self.FecAction = fecaction
        self.FecMode = fecmode
        self.FecPhyType = fecphytype
        self.FecType = fectype

    def get_attributes_dict(self):
        attributes = {}
        for key in vars(self):
            if "_spirent" in key:
                continue
            attributes[key] = getattr(self, key)
        return attributes

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle

    def __str__(self):
        return "FecModeObject"








