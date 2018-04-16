from lib.system.fun_test import *
from lib.templates.traffic_generator.traffic_generator_template import TrafficGeneratorTemplate
from lib.host.spirent_manager import SpirentManager


class SpirentTrafficGeneratorTemplate(TrafficGeneratorTemplate):
    def __init__(self, chassis_type=SpirentManager.VIRTUAL_CHASSIS_TYPE, dut_type=SpirentManager.DUT_TYPE_PALLADIUM):
        TrafficGeneratorTemplate.__init__(self)
        self.chassis_type = chassis_type
        self.dut_type = dut_type
        try:
            self.stc_manager = SpirentManager(chassis_type=self.chassis_type, dut_type=self.dut_type)
        except Exception as ex:
            fun_test.critical(str(ex))


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
        return vars(self)

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)

    @property
    def spirent_handle(self):
        return self._spirent_handle

    @spirent_handle.setter
    def spirent_handle(self, handle):
        self._spirent_handle = handle


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
        return vars(self)

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

    def __init__(self, destination_mac="00:00:01:00:00:01", ether_type=LOCAL_EXPERIMENTAL_ETHERTYPE,
                 preamble="55555555555555d5", source_mac="00:10:94:00:00:02"):
        self.dstMac = destination_mac
        self.etherType = ether_type
        self.preamble = preamble
        self.srcMac = source_mac

    def get_attributes_dict(self):
        return vars(self)

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class EthernetPauseHeader(object):
    HEADER_TYPE = "ethernet:EthernetPause"

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
        return vars(self)

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)


class Ipv4Header(object):
    PROTOCOL_TYPE_EXPERIMENTAL = "Experimental"
    HEADER_TYPE = "ipv4:IPv4"

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
        return vars(self)

    def update_stream_block_object(self, **kwargs):
        self.__dict__.update(**kwargs)











