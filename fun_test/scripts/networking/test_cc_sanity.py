from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import NetworkController
from nu_config_manager import *

dut_config = {}
spirent_config = {}
network_controller_obj = None
port1 = None
port2 = None
TRAFFIC_DURATION = 30
cc_path_config = {}
LOAD = 81
LOAD_UNIT = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
FRAME_SIZE = 128
FRAME_LENGTH_MODE = StreamBlock.FRAME_LENGTH_MODE_FIXED
INTERFACE_LOADS_SPEC = SCRIPTS_DIR + "/networking" + "/interface_loads.json"
NUM_PORTS = 2


class SetupSpirent(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Check health of Spirent. Connect to Lab server
        2. Create ports and attach ports
        3. Read configs 
        4. In cleanup, disconnect session 
        """)

    def setup(self):
        fun_test.log("In script setup")
        global template_obj, dut_config, spirent_config, network_controller_obj, port1, port2, cc_path_config, \
            interface_obj1, interface_obj2
        global LOAD, LOAD_UNIT, FRAME_SIZE, FRAME_LENGTH_MODE

        dut_type = fun_test.get_local_setting('dut_type')
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type)

        chassis_type = fun_test.get_local_setting('chassis_type')
        spirent_config = nu_config_obj.read_traffic_generator_config()

        template_obj = SpirentEthernetTrafficTemplate(session_name="cc_path", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                    cc_flow_direction=NuConfigManager.FLOW_DIRECTION_FPG_CC)
        fun_test.test_assert(result['result'], "Ensure Spirent Setup done")

        port1 = result['port_list'][0]
        port2 = result['port_list'][1]

        interface_obj1 = result['interface_obj_list'][0]
        interface_obj2 = result['interface_obj_list'][1]

        dpc_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpc_server_port = dut_config['dpcsh_tcp_proxy_port']
        network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

        configs = fun_test.parse_file_to_json(INTERFACE_LOADS_SPEC)
        fun_test.simple_assert(configs, "Read Interface loads file")
        cc_path_config = configs['cc_path']
        LOAD = cc_path_config['load']
        LOAD_UNIT = cc_path_config['load_unit']
        FRAME_SIZE = cc_path_config['frame_size']
        FRAME_LENGTH_MODE = cc_path_config['frame_length_mode']

    def cleanup(self):
        fun_test.log("In script cleanup")
        template_obj.cleanup()


class TestCcEthernetArpRequest(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test CC Ethernet ARP Request",
                              steps="""
                              1. Create a stream with EthernetII and ARP headers under port %s
                                 a. Frame Size Mode: %s Frame Size %d
                                 b. Load: %d Load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Validate Tx == Rx on spirent and ensure no errors are seen.
                              7. Validate Tx == Rx on DUT and ensure no errors are seen 
                              8. From VP stats, validate CC OUT and Control T2C counters are UP
                              9. From VP stats, validate VP total IN == VP total OUT
                              10. Ensure BAM pools are 0 before and after running traffic
                              11. From ERP NU stats, validate count for all non FCP packets are UP
                              12. From PSW NU stats, validate    
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):

        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=40, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)
        arp_obj = ARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetArpResponse(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test CC Ethernet ARP Response",
                              steps="""
                              1. Create a stream with EthernetII and ARP headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=41, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)
        arp_obj = ARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetRarp(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=3, summary="Test CC Ethernet RARP (Reverse-ARP)",
                              steps="""
                              1. Create a stream with EthernetII and RARP headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Configure stream with EthernetII and RARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.RARP_ETHERTYPE)
        rarp_obj = RARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=rarp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetLLDP(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=4, summary="Test CC Ethernet LLDP (Link Layer Discovery Protocol)",
                              steps="""
                              1. Create a stream with EthernetII (EtherType - 88CC)under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Configure stream with EthernetII under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.LLDP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.LLDP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.delete_frame_headers(stream_block_handle=self.stream_obj.spirent_handle,
                                                               header_types=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetPTP(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=5, summary="Test CC Ethernet PTP (Precision Time Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and PTP headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']

        checkpoint = "Configure stream with EthernetII under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.PTP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ptp_header_obj = PtpFollowUpHeader(control_field=PtpFollowUpHeader.CONTROL_FIELD_FOLLOW_UP,
                                           message_type=PtpFollowUpHeader.MESSAGE_TYPE_FOLLOW_UP)

        result = template_obj.configure_ptp_header(stream_block_handle=self.stream_obj.spirent_handle,
                                                   header_obj=ptp_header_obj, create_header=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4ICMP(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=6, summary="Test CC IPv4 ICMP (Internet Control Message Protocol)",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 and ICMP Echo Request 
                                     headers under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']

        checkpoint = "Configure stream with EthernetII, IPv4 and ICMP Echo Request under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_ICMP, destination_address="20.1.1.2")
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        icmp_echo_req_obj = IcmpEchoRequestHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=icmp_echo_req_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ospfv2Hello(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=7, summary="Test CC IPv4 OSPF V2 Hello (Open Shortest Path First)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and OSPFv2 Hello headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and IPv4 and OSPFv2 Hello headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.OSPF_MULTICAST_MAC_1,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_OSPFIGP,
                                     destination_address=Ipv4Header.OSPF_MULTICAST_IP_1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        ospf_header_obj = Ospfv2HelloHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ospf_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ospfv2LinkStateUpdate(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=8, summary="Test CC IPv4 OSPF V2 Link State Update (Open Shortest Path First)",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 and OSPFv2 Link State Update 
                                     headers under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and IPv4 and OSPFv2 Link State Update headers under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.OSPF_MULTICAST_MAC_2,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_OSPFIGP,
                                     destination_address=Ipv4Header.OSPF_MULTICAST_IP_2)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        ospf_header_obj = Ospfv2LinkStateUpdateHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ospf_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Pim(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=9, summary="Test CC IPv4 PIM (Protocol Independent Multicast)",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 and PIMv4Hello
                                     headers under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and IPv4 and PIMv4Hello headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.PIM_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_PIM,
                                     destination_address=Ipv4Header.PIM_MULTICAST_IP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        pim_header_obj = Pimv4HelloHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=pim_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4BGP(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=10, summary="Test CC IPv4 BGP (Border Gateway Protocol)",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 and TCP headers under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 and TCP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_TCP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        tcp_header_obj = TCP(source_port=1024, destination_port=TCP.DESTINATION_PORT_BGP, checksum=20047)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Igmp(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=11, summary="Test CC IPv4 IGMP (Internet Group Management Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and IGMP headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 and IGMP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_IGMP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        igmp_header_obj = Igmpv1Header()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=igmp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4ForUs(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=12, summary="Test CC IPv4 FOR US",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 headers under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP1(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=13, summary="Test CC IPv4 PTP with Destination port 319 with PTP sync",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (dest port 319) PTP sync 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with dest port 319")
        ptp_sync_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP2(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=14, summary="Test CC IPv4 PTP with Destination port 320 with PTP sync",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (dest port 320) PTP sync 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=320)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with destination port 320")
        ptp_sync_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP3(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=15, summary="Test CC IPv4 PTP Sync with UDP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (PTP Sync) headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and IPv4 and UDP (PTP Sync) headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.LLDP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.PTP_SYNC_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Add UDP header")

        ptp_sync_header_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_header_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP4(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=16, summary="Test CC IPv4 PTP Delay Request with UDP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (PTP Delay Request) 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and IPv4 and UDP (PTP Delay Request) headers under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.PTP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.PTP_DELAY_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Add UDP header")

        ptp_delay_header_obj = PtpDelayReqHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_delay_header_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4TtlError1(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 27

    def describe(self):
        self.set_test_details(id=17, summary="Test CC IPv4 TTL Error (TTL = 1)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 1" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], ttl=1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4TtlError2(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 27

    def describe(self):
        self.set_test_details(id=18, summary="Test CC IPv4 TTL Error (TTL = 0)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 0" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], ttl=0)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4TtlError3(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 27

    def describe(self):
        self.set_test_details(id=19, summary="Test CC IPv4 TTL Error (TTL = 1)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 1" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'], ttl=1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4ErrorTrapIpOpts1(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 40

    def describe(self):
        self.set_test_details(id=20, summary="Test CC IPv4 OPTS Error (Header Option: timestamp)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with timestamp header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with timestamp header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure Ipv4 Header")
        timestamp_header_option_obj = IPv4HeaderOptionTimestamp()
        result = template_obj.stc_manager.update_header_options(header_obj=ipv4_header_obj,
                                                                option_obj=timestamp_header_option_obj,
                                                                stream_block_handle=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4ErrorTrapIpOpts2(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 41

    def describe(self):
        self.set_test_details(id=21, summary="Test CC IPv4 OPTS Error (Header Option: Loose Src Route)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with Loose Src Route header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with Loose Src Route header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure Ipv4 Header")
        lsr_header_option_obj = IPv4HeaderOptionLooseSourceRoute()
        result = template_obj.stc_manager.update_header_options(header_obj=ipv4_header_obj,
                                                                option_obj=lsr_header_option_obj,
                                                                stream_block_handle=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthArpRequestUnicast(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 40

    def describe(self):
        self.set_test_details(id=22, summary="Test CC Ethernet ARP Request Unicast ",
                              steps="""
                              1. Create a stream with EthernetII and ARP header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and ARP header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        arp_header_obj = ARP(target_ip_address=l3_config['cc_destination_ip1'], operation=ARP.ARP_OPERATION_REQUEST)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpChecksumError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 41

    def describe(self):
        self.set_test_details(id=23, summary="Test CC IP checksum Error ",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and Ipv4 header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'],
                                     checksum=Ipv4Header.CHECKSUM_ERROR)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Dhcp(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=24, summary="Test CC IPv4 DHCP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and DHCp header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and IPv4 and DHCp header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.DHCP_RELAY_AGENT_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure IPv4 Header with DHCP Relay Agent Multicast IP")

        udp_header_obj = UDP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header")

        dhcp_client_message_header = DhcpClientMessageHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=dhcp_client_message_header,
                                                                update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcFSFError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=25, summary="Test CC FSF Error",
                              steps="""
                              1. Create a stream with EthernetII and Custom header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Start traffic   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        checkpoint = "Create a stream with EthernetII and Custom header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ETHERNET_FLOW_CONTROL_MAC,
                                    ether_type=Ethernet2Header.ETHERNET_FLOW_CONTROL_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        custom_header_obj = CustomBytePatternHeader(byte_pattern="11010000")
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=custom_header_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4VersionError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=32, summary="Test CC IPv4 Version Error",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 with version = 0  under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with version = 0  under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], version=0)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4InternetHeaderLengthError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=33, summary="Test CC IPv4 Internet Header Length Error",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 with Header Length = 4  under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Header Length = 4  under port %s " % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], ihl=4)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4FlagZeroError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=34, summary="Test CC IPv4 Control Flags Reserved = 1 Error",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error 
                                     under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Updated IPv4 Header")
        result = template_obj.stc_manager.update_control_flags(stream_block_obj=self.stream_obj,
                                                               header_obj=ipv4_header_obj, reserved=1)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4MTUCase(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    mtu = 10000
    frame_size = mtu
    load = 1

    def describe(self):
        self.set_test_details(id=34, summary="Test CC IPv4 10K MTU Case",
                              steps="""
                                  1. Create a stream with EthernetII and IPv4 under port %s
                                     a. Frame Size Mode: %s Frame Size: %d 
                                     b. load: %d load Unit: %s
                                     c. Include signature field
                                     d. Payload Fill type: Constant
                                     c. MTU on ports: %d
                                  2. Configure %s generator with following settings
                                     a. Set Duration %d secs 
                                     b. Scheduling mode to Rate based
                                  3. Subscribe to all results
                                  4. Start traffic   
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, self.mtu,
                                         port1, TRAFFIC_DURATION))
        # TODO: Add validation steps

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update ports MTU on spirent ports. MTU: %d" % self.mtu
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=[interface_obj1, interface_obj2],
                                                               mtu_value=self.mtu)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        checkpoint = "Update MTU on DUT ports. MTU: %d" % self.mtu
        for port in dut_config['ports']
        mtu_changed_on_dut = network_controller_obj.

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        pass

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

if __name__ == '__main__':
    ts = SetupSpirent()
    '''
    ts.add_test_case(TestCcEthernetArpRequest())
    ts.add_test_case(TestCcEthernetArpResponse())
    ts.add_test_case(TestCcEthernetRarp())
    ts.add_test_case(TestCcEthernetLLDP())
    ts.add_test_case(TestCcEthernetPTP())
    ts.add_test_case(TestCcIPv4ICMP())
    
    ts.add_test_case(TestCcIPv4Ospfv2Hello())
    ts.add_test_case(TestCcIPv4Ospfv2LinkStateUpdate())
    ts.add_test_case(TestCcIpv4Pim())
    ts.add_test_case(TestCcIpv4BGP())
    ts.add_test_case(TestCcIpv4Igmp())
    ts.add_test_case(TestCcIPv4ForUs())
    ts.add_test_case(TestCcIPv4PTP1())
    ts.add_test_case(TestCcIPv4PTP2())
    ts.add_test_case(TestCcIPv4PTP3())
    ts.add_test_case(TestCcIPv4PTP4())
    ts.add_test_case(TestCcIPv4TtlError1())
    ts.add_test_case(TestCcIPv4TtlError2())
    
    ts.add_test_case(TestCcIPv4TtlError3())
    ts.add_test_case(TestCcIpv4ErrorTrapIpOpts1())
    ts.add_test_case(TestCcIpv4ErrorTrapIpOpts2())
    ts.add_test_case(TestCcEthArpRequestUnicast())
    
    ts.add_test_case(TestCcIpChecksumError())
    ts.add_test_case(TestCcIpv4Dhcp())
    '''
    ts.add_test_case(TestCcFSFError())
    ts.add_test_case(TestCcIPv4VersionError())
    ts.add_test_case(TestCcIPv4InternetHeaderLengthError())
    ts.add_test_case(TestCcIPv4FlagZeroError())

    ts.run()