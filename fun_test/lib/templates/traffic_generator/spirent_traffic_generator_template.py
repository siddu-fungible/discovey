from lib.system.fun_test import *
from lib.templates.traffic_generator.traffic_generator_template import TrafficGeneratorTemplate
from lib.host.spirent_manager import SpirentManager


class SpirentTrafficGeneratorTemplate(TrafficGeneratorTemplate):
    def __init__(self, chassis_type):
        TrafficGeneratorTemplate.__init__(self)
        self.chassis_type = chassis_type
        try:
            self.stc_manager = SpirentManager(chassis_type=self.chassis_type)
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
        STREAM_BLOCK_READABLE_ATTRIBUTES = ["BpsLoad", "ControlledBy", "FlowCount", "FpsLoad", "IbgInMillisecondsLoad",
                                            "IbgInNanosecondsLoad", "IbgLoad", "IsArpResolved", "KbpsLoad", "L2Rate"]
        _spirent_handle = None

        def __init__(self):
            self.AdvancedInterleavingGroup = 0
            self.AllowInvalidHeaders = False
            self.BurstSize = 1
            self.ByPassSimpleIpSubnetChecking = False
            self.ConstantFillPattern = 0
            self.CustomPfcPriority = 0
            self.EnableBackBoneTrafficSendToSelf = True
            self.EnableBidirectionalTraffic = False
            self.EnableControlPlane = False
            self.EnableCustomPfc = False
            self.EnableFcsErrorInsertion = False
            self.EnableHighSpeedResultAnalysis = False
            self.EnableResolveDestMacAddress = True
            self.EnableStreamOnlyGeneration = True
            self.EnableTxPortSendingTrafficToSelf = False
            self.EndpointMapping = self.ENDPOINT_MAPPING_ONE_TO_ONE
            self.FillType = self.FILL_TYPE_CONSTANT
            self.FixedFrameLength = 128
            self.FrameConfig = ""
            self.FrameLengthMode = self.FRAME_LENGTH_MODE_FIXED
            self.InsertSig = True
            self.InterFrameGap = 12
            self.Load = 10
            self.LoadUnit = self.LOAD_UNIT_PERCENT_LINE_RATE
            self.MaxFrameLength = 256
            self.MinFrameLength = 128
            self.Priority = 0
            self.ShowAllHeaders = False
            self.StartDelay = 0
            self.StepFrameLength = 1
            self.TimeStampOffset = 0
            self.TimeStampType = self.TIME_STAMP_TYPE_MIN
            self.TrafficPattern = self.TRAFFIC_PATTERN_PAIR

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

        def __init__(self):
            self.AdvancedInterleaving = False
            self.BurstSize = 1
            self.Duration = 30
            self.DurationMode = self.DURATION_MODE_CONTINOUS
            self.FixedLoad = 10
            self.InterFrameGapUnit = self.INTER_FRAME_GAP_UNIT_BYTES
            self.JumboFrameThreshold = 1518
            self.OversizeFrameThreshold = 9018
            self.RandomLengthSeed = 10900842
            self.RandomMaxLoad = 100
            self.RandomMinLoad = 10
            self.SchedulingMode = self.SCHEDULING_MODE_PORT_BASED
            self.SmoothenRandomLength = False
            self.StepSize = 1
            self.TimeStampLatchMode = self.TIME_STAMP_LATCH_MDOE_START_OF_FRAME
            self.UndersizeFrameThreshold = 64
            self.InterFrameGap = 12
            self.LoadMode = self.LOAD_MODE_FIXED
            self.LoadUnit = self.LOAD_UNIT_PERCENT_LINE_RATE

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

    class EthernetIIHeader(object):
        HEADER_TYPE = "ethernet:EthernetII"
        LOCAL_EXPERIMENTAL_ETHERTYPE = "88B5"

        def __init__(self):
            self.dstMac = "00:00:01:00:00:01"
            self.etherType = self.LOCAL_EXPERIMENTAL_ETHERTYPE
            self.preamble = "55555555555555d5"
            self.srcMac = "00:10:94:00:00:02"

        def get_attributes_dict(self):
            return vars(self)

        def update_stream_block_object(self, **kwargs):
            self.__dict__.update(**kwargs)

    class EthernetPauseHeader(object):
        HEADER_TYPE = "ethernet:EthernetPause"

        def __init__(self):
            self.dstMac = "01:80:C2:00:00:01"
            self.lengthType = "8808"
            self.Opcode = "0001"
            self.srcMac = "00:00:01:00:00:03"
            self.preamble = "55555555555555d5"
            self.Parameters = "0000"
            self.Reserved = ""

        def get_attributes_dict(self):
            return vars(self)

        def update_stream_block_object(self, **kwargs):
            self.__dict__.update(**kwargs)

    class IPV4Header(object):
        PROTOCOL_TYPE_EXPERIMENTAL = "Experimental"
        HEADER_TYPE = "ipv4:IPv4"

        def __init__(self):
            self.checksum = 0
            self.destAddr = "192.0.0.1"
            self.destPrefixLength = 24
            self.fragOffset = 0
            self.gateway = "192.85.0.1"
            self.identification = 0
            self.ihl = 5
            self.prefixLength = 24
            self.protocol = self.PROTOCOL_TYPE_EXPERIMENTAL
            self.sourceAddr = "192.85.1.2"
            self.totalLength = 20
            self.ttl = 255
            self.version = 4

        def get_attributes_dict(self):
            return vars(self)

        def update_stream_block_object(self, **kwargs):
            self.__dict__.update(**kwargs)










