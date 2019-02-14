import requests  
from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, TCP, UDP, Ipv4Header, RangeModifier, ARP, CustomBytePatternHeader, Capture
from lib.host.network_controller import NetworkController
from lib.utilities.pcap_parser import PcapParser
from lib.host.linux import *
from scripts.networking.helper import *
from scripts.networking.nu_config_manager import NuConfigManager
from scripts.networking.fwd.helper import BaseSetup

num_ports = 3
FCP_Custom_Header='FCP_CUSTOM_HEADER'
FSF_Custom_Header='FSF_CUSTOM_HEADER'
#custom_headers = {FCP_Custom_Header: ['0000002030400E5','0000000000000003'],
#                  FSF_Custom_Header: ['11010010' , '11010011']
#                  }
custom_headers = {FCP_Custom_Header: ['0008002030400E5','0000000000000003', '0000000000000004'],
                  FSF_Custom_Header: ['11010010' , '11010011','01:80:C2:00:00:01'],
                  }

# GLobal Packet tolerange value
TOLERANCE=10

class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, lab server and license server
                3. Attach Ports
                """)

    
    def setup(self):
        global template_obj, port_1, port_2, port_3, gen_obj, \
            gen_config_obj, network_controller_obj, dut_port_1, dut_port_2, dut_port_3, dut_config, spirent_config, chassis_type, \
            next_hop_intf_list, nu_obj, routes_config
 
        nu_config_obj = NuConfigManager()
        nu_obj = nu_config_obj
        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type,flow_type=NuConfigManager.ECMP_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_ECMP)

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="nh-testing", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports, flow_type=NuConfigManager.ECMP_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_ECMP)
        fun_test.test_assert(result['result'], "Configure setup")

        # Create network controller object
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

 
        # Setting QoS profile for FCP traffic
        buffer = network_controller_obj.set_qos_egress_buffer_pool(mode='hnu', df_thr=2000, dx_thr=1000, fcp_thr=1000, 
                                                                    fcp_xoff_thr=900, nonfcp_thr=4000, nonfcp_xoff_thr=3500,
                                                                    sample_copy_thr=255, sf_thr=2000, sf_xoff_thr=1900,
                                                                    sx_thr=250 )
        fun_test.test_assert(buffer, "Set hnu egress buffer pool")

        buffer = network_controller_obj.set_qos_egress_buffer_pool(df_thr=4000, dx_thr=4000, fcp_thr=8000, fcp_xoff_thr=7000, 
                                                                   nonfcp_thr=8000, nonfcp_xoff_thr=7000, sample_copy_thr=255,
                                                                   sf_thr=4000, sf_xoff_thr=3500, sx_thr=4000)
        fun_test.test_assert(buffer, "Set egress buffer pool")

        # DUT port receving traffic from traffic generator    
        dut_port_1 = dut_config["ports"][0]  
        dut_port_2 = dut_config['ports'][1] 
        dut_port_3 = dut_config['ports'][2] 
        
        
        # Traffic generaotr port conencted to HNU 
        port_1 = result['port_list'][0]
        
        # Traffic generaotr port conencted to Spine
        port_2 = result['port_list'][1]  

        # Traffic generaotr port conencted to Fab
        port_3 = result['port_list'][2] 

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.Duration = 30
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.AdvancedInterleaving = True
      


    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")   

class InterRackNFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface = None
    down_interface_name = None

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack NFCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab 
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure 
                        """)

    def test_mode(self, ch_enable, gph_enable, fabric_down, spine_down, flow_type='multi', source='host'):
        self.ch_enable=ch_enable
        self.gph_enable=gph_enable
        self.fabric_down=fabric_down
        self.spine_down=spine_down
        self.flow_type=flow_type 
        self.source=source
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)


    def setup(self):
        #self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj) 
        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
             
        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        gen_config_obj.Duration = self.duration_seconds
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
        ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip5'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        if self.flow_type =='multi':
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

        if self.flow_type=='multi': 
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

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.down_interface_name is not None: 
            # Enable the interface back 
            self.enable_disable_intf(intf_name=self.down_interface_name, status=True)
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        dut_port_3_results = None
        dut_port_2_results = None
        dut_port_1_transmit = None

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3
      
            
        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
            self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
            self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)
             
        # Only valid when source is host 
        if self.fabric_down: 
    
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test 
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)     
            else:
                # Clear Rx port 
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port) 

            # Get all fabric interface 
            fabric_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='fabric')
            self.down_interface = fabric_intf_list[0]
            self.down_interface_name = 'fpg'+str(self.down_interface)
          
            # Disable one fabric link 
            self.enable_disable_intf(intf_name=self.down_interface_name, status=False)

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
            fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
            message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except the interface is down")

            result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix recieved from traffic generator is sent out via FPG")

            # Ensure traffic distribution is as per the weight 
            intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='interrack1',ex_intf=fabric_intf_list[0])
            unit_weight  = self.get_pkt_weight_unit_post_link_failure(type='interracks',id='interrack1', total_pkt=dut_port_1_rx,intf_type='fabric', intf_list=[self.down_interface])
            result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix transmited from each nexthop as per wieght")
            fun_test.log("Further test will enable the link back and validate")
    
        if self.spine_down:
           
            if self.source == 'host': 
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port) 

            # Get all spine interface
            spine_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
            self.down_interface = spine_intf_list[0]
            self.down_interface_name = 'fpg'+str(self.down_interface)

            # Disable one spine link
            self.enable_disable_intf(intf_name=self.down_interface_name, status=False)

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
         
            # Rx packet on DUT
            if self.source == 'host':
                dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
                dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
            else:
                dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
                dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            # Tx packet on DUT intf_weight_list
            tx_result_dict = {}
            for item in next_hop_intf_list:
                dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
                tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
                if tx_packet == None:
                    tx_result_dict[item] = 0
                else:
                    tx_result_dict[item] = tx_packet
            fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
            message="Ensure as multiple flow, traffic should egress out via all diffrent nextho except the down interfacep")

            result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix recieved from traffic generator is sent out via FPG")

            # Ensure traffic distribution is as per the weight
            if self.source == 'host':
                intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='interrack1',ex_intf=spine_intf_list[0])
                unit_weight  = self.get_pkt_weight_unit_post_link_failure(type='interracks',id='interrack1', total_pkt=dut_port_1_rx,intf_type='spine', intf_list=[self.down_interface])
                result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                fun_test.test_assert_expected(expected=True, actual=result,
                message="Ensure traffix transmited from each nexthop as per wieght")
            else:

                intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='interrack1', link='spine', ex_intf=spine_intf_list[0])    
                unit_weight  = self.get_spine_pkt_weight_unit_post_link_failure(type='interracks',id='interrack1', total_pkt=dut_port_1_rx, intf_list=[self.down_interface])
                result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                fun_test.test_assert_expected(expected=True, actual=result,
                message="Ensure traffix transmited fro Test Case fromm each nexthop as per wieght")           

        # Enable the link back
        if self.down_interface_name is not None:
            self.enable_disable_intf(intf_name=self.down_interface_name, status=True) 
            if self.source == 'host':
                next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
                self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
            else:
                next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
                self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)


class InterRackFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 120
    down_interface = None
    down_interface_name = None

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack FCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, ch_enable, gph_enable, fabric_down, spine_down, flow_type='single', source='host'):
        self.ch_enable=ch_enable
        self.gph_enable=gph_enable
        self.fabric_down=fabric_down
        self.spine_down=spine_down
        self.source=source
        self.flow_type=flow_type
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)  


    def setup(self):
        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')


        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        load = 20
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 82
        self.streamblock_obj.MaxFrameLength = 900

        # Change generator config parameters
        gen_obj = template_obj.stc_manager.get_generator(port_handle=port)
        gen_config_obj.Duration = self.duration_seconds
        config_obj = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")
        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

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

        if self.source == 'host':

            # Crafting FCP packet for Sf cases
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip9'],
                                   source_address=l3_config['source_ip1'])
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

        else:

            # Crafting FCP packet for Sx /Dx cases 
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip6'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)
 
            checkpoint = "Add UDP header"
            udp_header_obj = UDP(destination_port=7085)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=udp_header_obj, update=False)
            fun_test.simple_assert(result, "Added UDP header with dest port 7085")

            checkpoint = "Add Custom FCP header"
            custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][0])
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_1)
            fun_test.simple_assert(custom_header_1, checkpoint)

            #custom_header_2 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][1])
            #configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            #    stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_2)
            #fun_test.test_assert(configure_cust_header, "Configure custom header")
            #fun_test.simple_assert(custom_header_2, checkpoint)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.down_interface_name is not None:
            # Enable the interface back
            self.enable_disable_intf(intf_name=self.down_interface_name, status=True)
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        dut_port_3_results = None
        dut_port_2_results = None
        dut_port_1_transmit = None

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
            self.verify_hnu_fcp_traffic(dut_port, port, next_hop_intf_list)
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
            self.verify_nu_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        # Only valid when source is host
        if self.fabric_down:

            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)

            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            # Get all fabric interface
            fabric_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='fabric')
            self.down_interface = fabric_intf_list[0]
            self.down_interface_name = 'fpg'+str(self.down_interface)

            # Disable one fabric link
            self.enable_disable_intf(intf_name=self.down_interface_name, status=False)

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

            # Rx packet on DUT
            if self.source == 'host':
                dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
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
                tx_packet = get_dut_output_stats_value(dut_results, OCTETS_TRANSMITTED_OK)
                if tx_packet == None:
                    tx_result_dict[item] = 0
                else:
                    tx_result_dict[item] = tx_packet
            fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
            message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except the interface is down")

            result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix recieved from traffic generator is sent out via FPG")

            # Ensure traffic distribution is as per the weight
            intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='fcp_interrack1',ex_intf=fabric_intf_list[0])
            unit_weight  = self.get_pkt_weight_unit_post_link_failure(type='interracks',id='fcp_interrack1', total_pkt=dut_port_1_rx,intf_type='fabric', intf_list=[self.down_interface])
            result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix transmited from each nexthop as per wieght")
            fun_test.log("Further test will enable the link back and validate")

        if self.spine_down:

            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)

            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port) 

            # Get all fabric interface
            spine_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
            self.down_interface = spine_intf_list[0]
            self.down_interface_name = 'fpg'+str(self.down_interface)

            # Disable one fabric link
            self.enable_disable_intf(intf_name=self.down_interface_name, status=False)

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

            # Rx packet on DUT
            if self.source == 'host':
                dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)
                dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx
            else:
                dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
                dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)

            # Tx packet on DUT intf_weight_list
            tx_result_dict = {}
            for item in next_hop_intf_list:
                dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
                tx_packet = get_dut_output_stats_value(dut_results, OCTETS_TRANSMITTED_OK)
                if tx_packet == None:
                    tx_result_dict[item] = 0
                else:
                    tx_result_dict[item] = tx_packet
            fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
            message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop")

            result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
            fun_test.test_assert_expected(expected=True, actual=result,
            message="Ensure traffix recieved from traffic generator is sent out via FPG")

            # Ensure traffic distribution is as per the weight
            if self.source == 'host':
                intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='int',ex_intf=spine_intf_list[0])
                unit_weight  = self.get_pkt_weight_unit_post_link_failure(type='interracks',id='fcp_interrack1', total_pkt=sum(tx_result_dict.values()),intf_type='spine', intf_list=[self.down_interface])
                result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                fun_test.test_assert_expected(expected=True, actual=result,
                message="Ensure traffix transmited from each nexthop as per wieght")
            else:

                intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='fcp_interrack1', link='spine', ex_intf=spine_intf_list[0])
                unit_weight  = self.get_spine_pkt_weight_unit_post_link_failure(type='interracks',id='fcp_interrack1', total_pkt=sum(tx_result_dict.values()), intf_list=[self.down_interface])
                result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
                fun_test.test_assert_expected(expected=True, actual=result,
                message="Ensure traffix transmited fro Test Case fromm each nexthop as per wieght")

        # Enable the link back
        if self.down_interface_name is not None:
            self.enable_disable_intf(intf_name=self.down_interface_name, status=True)
            if self.source == 'host':
                next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
                self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
            else:
                next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
                self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list)


class IntraRackNFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60

    def describe(self):
        self.set_test_details(id=998,
                        summary="Base Test Case from Intra Rack NFCP traffic",
                        steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab / spine
                        2. Direct link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and DL status
                        """)

    def test_mode(self, source, dl_status):
        self.source=source
        self.dl_status=dl_status
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='intrarack1')

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80
       
        if  self.source == 'host': 
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else: 
            port = port_3
            dut_port = dut_port_3
            

        # Change generator config parameters
        gen_config_obj.Duration = self.duration_seconds
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
        ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip7'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Configure IP range modifier"
        modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, recycle_count=200,
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

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")
        if  not self.dl_status:
            self.enable_disable_intf(intf_name=self.spf_intf, status=True)

    def run(self):
        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3  
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='intrarack1')
        self.spf_intf= 'fpg'+str(self.get_direct_link(type='intraracks',id='intrarack1'))
        if  not self.dl_status:
            # Disable the direct link interface 
            self.enable_disable_intf(intf_name=self.spf_intf, status=False)
       
        if self.source == 'host':    
            self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=self.dl_status) 
        else:
            self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=self.dl_status) 
           
class IntraRackFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60

    def describe(self):
        self.set_test_details(id=997,
                              summary="Base Test Case from Intra Rack FCP traffic",
                               steps="""
                               1. Base test case will be caled by diffrent test cases based on Traffic source.
                                   Traffic source can be host /fab / spine
                               2. Direct link failure will be handled based on input from original test case
                               3. Traffic validation will be based on traffic source and DL status

                               """)

    def test_mode(self, source, dl_status):
        self.source=source
        self.dl_status=dl_status
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='fcp_intrarack1')

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 20
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 82
        self.streamblock_obj.MaxFrameLength = 900

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3


        # Change generator config parameters
        gen_config_obj.Duration = self.duration_seconds
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

        if self.source == 'host':

            ## TODO Des IP need to change
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip13'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Add UDP header"
            udp_header_obj = UDP(destination_port=10101)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
            fun_test.simple_assert(result, "Added UDP header with dest port 10101")
            fun_test.simple_assert(udp_header_obj, checkpoint)
        else: 
            
            # Crafting FCP header for Sx 
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip8'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)
      
            checkpoint = "Add UDP header"
            udp_header_obj = UDP(destination_port=7085)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
            fun_test.simple_assert(result, "Added UDP header with dest port 7085")
            fun_test.simple_assert(udp_header_obj, checkpoint)

            checkpoint = "Add Custom FCP header"
            custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][0])
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_1)
            fun_test.simple_assert(configure_cust_header, checkpoint)

            custom_header_2 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][1])
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_2)
            fun_test.test_assert(configure_cust_header, "Configure custom header")
            fun_test.simple_assert(configure_cust_header, checkpoint)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")
        if  not self.dl_status:
            # Disable the direct link interface
            self.enable_disable_intf(intf_name=self.spf_intf, status=True)

    def run(self):
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='fcp_intrarack1')
        self.spf_intf= 'fpg'+str(self.get_direct_link(type='intraracks',id='fcp_intrarack1'))
        if  not self.dl_status:
            # Disable the direct link interface
            self.enable_disable_intf(intf_name=self.spf_intf, status=False)
        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        if self.source == 'host':
            self.verify_hnu_fcp_traffic(dut_port, port, next_hop_intf_list, flow='single', traffic_type='intra', spf_up=self.dl_status)
        else:
            self.verify_nu_fcp_traffic(dut_port, port, next_hop_intf_list, flow='single', traffic_type='intra', spf_up=self.dl_status) 

#####- Start here 
class FFRInterRackNFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface_list = []
    down_interface_name_list = []

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack NFCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, ch_enable, gph_enable, fabric_down, spine_down, flow_type='multi', source='host'):
        self.ch_enable=ch_enable
        self.gph_enable=gph_enable
        self.fabric_down=fabric_down
        self.spine_down=spine_down
        self.flow_type=flow_type
        self.source=source
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')


        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        gen_config_obj.Duration = self.duration_seconds
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
        ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip5'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        if self.flow_type =='multi':
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

        if self.flow_type=='multi':
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

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        for item in self.down_interface_name_list:
            # Enable the interface back
            self.enable_disable_intf(intf_name=item, status=True)
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        dut_port_3_results = None
        dut_port_2_results = None
        dut_port_1_transmit = None

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3


        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
        #     # self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
        #     self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
        spine_intf_list=self.get_all_nexthop(type='interracks',id='interrack1',link='spine')  
        fabric_intf_list=self.get_all_nexthop(type='interracks',id='interrack1',link='fabric')  

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)
     
        # Only valid when source is host
        if self.fabric_down:

            ##
            # Sub Test-1: 2 Interface down  
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 1: Bring down 2 fabric interface and validate traffic")
            for item in fabric_intf_list[0:2]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, fabric_intf_list[0:2])
            checkpoint = "Subtest1:Bring down 2 fabric interface and validate traffic"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-2: 4 Interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 2: Bring down further 2 fabric interface and validate traffi.Total 4 interface down")
            for item in fabric_intf_list[2:5]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)


            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, fabric_intf_list[0:5])
            checkpoint = "Subtest2:Bring down further 2 fabric interface and validate traffi.Total 4 interface down"
            fun_test.simple_assert(result, checkpoint) 

            ##
            # Sub Test-3: All fabric interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 3: Bring down all fabric interface and validate traffc")
            for item in fabric_intf_list[5:]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            fun_test.log("Subtest 3: Bring down all fabric interface and validate traffic leaving via spine only")

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, fabric_intf_list)
            checkpoint = "Subtest 3: Bring down all fabric interface and validate traffic leaving via spine only"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-4: Bring up 2 fabric down interface
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 4: Bring up 2 fabric interface and validate traffc")
            for item in fabric_intf_list[0:2]:
                name = 'fpg'+str(item)
                # Enable one fabric link
                self.enable_disable_intf(intf_name=name, status=True)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)

            fun_test.log("Subtest 4: Bring up 2 fabric interface and validate traffic resumed on them")

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, fabric_intf_list[2:])
            checkpoint = "Subtest 4: Bring up 2 fabric interface and validate traffic resumed on them"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-5: Bring up all interface and traffic should resume normaly
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 5: Bring up all fabric interface and validate traffc")
            for item in fabric_intf_list[2:]:
                name = 'fpg'+str(item)
                # Enable one fabric link
                self.enable_disable_intf(intf_name=name, status=True)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
            if self.source == 'host':
                self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi')
            else:
                self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi')    


            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            checkpoint = "Subtest 5: Bring up all fabric interface and validate traffic resumed nomraly"
            fun_test.simple_assert(result, checkpoint)

        if self.spine_down:   
            ##
            # Sub Test-1: 2 Interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 1: Bring down 2 spine interface and validate traffic")
            for item in spine_intf_list[0:2]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, spine_intf_list[0:2])
            checkpoint = "Subtest1:Bring down 2 spine interface and validate traffic"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-2: 4 Interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 2: Bring down further 2 spine interface and validate traffi.Total 4 interface down")
            for item in spine_intf_list[2:5]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)


            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, spine_intf_list[0:5])
            checkpoint = "Subtest2:Bring down further 2 spine interface and validate traffi.Total 4 interface down"
            fun_test.simple_assert(result, checkpoint) 

            ##
            # Sub Test-3: All spine interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 3: Bring down all spine interface and validate traffc")
            for item in spine_intf_list[5:]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            fun_test.log("Subtest 3: Bring down all spine interface and validate traffic leaving via spine only")

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, spine_intf_list)
            checkpoint = "Subtest 3: Bring down all spine interface and validate traffic leaving via spine only"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-4: Bring up 2 spine down interface
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 4: Bring up 2 spine interface and validate traffc")
            for item in spine_intf_list[0:2]:
                name = 'fpg'+str(item)
                # Enable one fabric link
                self.enable_disable_intf(intf_name=name, status=True)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)

            fun_test.log("Subtest 4: Bring up 2 spine interface and validate traffic resumed on them")

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, spine_intf_list[2:])
            checkpoint = "Subtest 4: Bring up 2 spine interface and validate traffic resumed on them"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-5: Bring up all interface and traffic should resume normaly
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 5: Bring up all spine interface and validate traffc")
            for item in spine_intf_list[2:]:
                name = 'fpg'+str(item)
                # Enable one fabric link
                self.enable_disable_intf(intf_name=name, status=True)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
            if self.source == 'host':
                self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi')
            else:
                self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi')


            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            checkpoint = "Subtest 5: Bring up all fabric interface and validate traffic resumed nomraly"
            fun_test.simple_assert(result, checkpoint)

class FFRInterRackFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface_list = []
    down_interface_name_list = []

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack FCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, ch_enable, gph_enable, fabric_down, spine_down, flow_type='multi', source='host'):
        self.ch_enable=ch_enable
        self.gph_enable=gph_enable
        self.fabric_down=fabric_down
        self.spine_down=spine_down
        self.flow_type=flow_type
        self.source=source
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')


        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        gen_config_obj.Duration = self.duration_seconds
        config_obj = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")

        l3_config = routes_config['l3_config']
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        if self.source == 'host':

            # Crafting FCP packet for Sf cases
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip9'],
                                   source_address=l3_config['source_ip1'])
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

        else:

            # Crafting FCP packet for Sx /Dx cases
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip6'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Add UDP header"
            udp_header_obj = UDP(destination_port=7085)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=udp_header_obj, update=False)
            fun_test.simple_assert(result, "Added UDP header with dest port 7085")

            checkpoint = "Add Custom FCP header"
            custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][0])
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_1)
            fun_test.simple_assert(custom_header_1, checkpoint)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        for item in self.down_interface_name_list:
            # Enable the interface back
            self.enable_disable_intf(intf_name=item, status=True)
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")   

    def run(self):
        dut_port_3_results = None
        dut_port_2_results = None
        dut_port_1_transmit = None

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3


        if self.source == 'host':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
            self.verify_hnu_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
            self.verify_nu_fcp_traffic(dut_port, port, next_hop_intf_list, flow=self.flow_type)
        spine_intf_list=self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
        fabric_intf_list=self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='fabric')

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item) 

        # Only valid when source is host
        if self.fabric_down:

            ##
            # Sub Test-1: 2 Interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 1: Bring down 2 fabric interface and validate traffic")
            for item in fabric_intf_list[0:2]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            result=self.verify_ffr_interrack_fcp(dut_port, port, self.source, fabric_intf_list[0:2])
            checkpoint = "Subtest1:Bring down 2 fabric interface and validate traffic"
            fun_test.simple_assert(result, checkpoint) 

            ##
            # Sub Test-2: All fabric interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 2: Bring down all fabric interface and validate traffc")
            for item in fabric_intf_list[2:]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            # Execute traffic
            self.start_traffic(port)

            # Sleep until traffic is executed
            fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)
            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, fabric_intf_list)
            checkpoint = "Subtest 2: Bring down all fabric interface and validate traffic leaving via spine only"
            fun_test.simple_assert(result, checkpoint)

    
        if self.spine_down:
            ##
            # Sub Test-1: 2 Interface down
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            fun_test.log("Subtest 1: Bring down 2 spine interface and validate traffic")
            for item in spine_intf_list[0:2]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)

            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, spine_intf_list[0:2])
            checkpoint = "Subtest1:Bring down 2 spine interface and validate traffic"
            fun_test.simple_assert(result, checkpoint)

            ##
            # Sub Test-2: Bring down all fabric interface traffic should leave via spine
            ##
            if self.source == 'host':
                # Get HNU port traffic status again before starting further test
                dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
                dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, OCTETS_RECEIVED_OK, tx=False)
            else:
                # Clear Rx port
                clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
                fun_test.sleep("Sleeping  1 sec", seconds=1)
                fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

            for item in spine_intf_list[2:]:
                name = 'fpg'+str(item)
                # Disable one fabric link
                self.enable_disable_intf(intf_name=name, status=False)
                fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
                self.down_interface_name_list.append(name)


            result=self.verify_ffr_interrack_non_fcp(dut_port, port, self.source, spine_intf_list)
            checkpoint = "Subtest2:Bring down all spine interface. Traffic should leave via fabric only "
            fun_test.simple_assert(result, checkpoint)

class FFRIntraRackNFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface_list = []
    down_interface_name_list = []

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack NFCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, ch_enable=False, gph_enable=False, flow_type='multi', source='host'):
        self.ch_enable=ch_enable
        self.gph_enable=gph_enable
        self.flow_type=flow_type
        self.source=source
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='intrarack1')

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3


        # Change generator config parameters
        gen_config_obj.Duration = self.duration_seconds
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
        ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip7'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Configure IP range modifier"
        modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, recycle_count=200,
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

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")
        if  not self.dl_status:
            self.enable_disable_intf(intf_name=self.spf_intf, status=True)

    def run(self):
        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='intrarack1')
        self.spf_intf= self.get_direct_link(type='intraracks',id='intrarack1')
        self.spf_intf_name= 'fpg'+str(self.get_direct_link(type='intraracks',id='intrarack1'))
        self.non_dl_link_list=next_hop_intf_list.remove(self.get_direct_link(type='intraracks',id='intrarack1'))

        fun_test.log("Disable Direct Link first for traffic to take non direct link")
        # Disable the direct link interface
        self.enable_disable_intf(intf_name=self.spf_intf_name, status=False)
        down_interface_name_list.append(self.spf_intf_name)

        if self.source == 'host':
            self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=False)
        else:
            self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=False) 


        ##
        # Sub Test-1: 2 Interface down
        ##
        if self.source == 'host':
            # Get HNU port traffic status again before starting further test
            dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
            dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
        else:
            # Clear Rx port
            clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
            fun_test.sleep("Sleeping  1 sec", seconds=1)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        fun_test.log("Subtest 1: Bring down 2 non DL interface and validate traffic")
        for item in self.non_dl_link[0:2]:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=False)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
            self.down_interface_name_list.append(name)
        result=self.verify_ffr_intrarack_non_fcp(dut_port, port, self.source, self.non_dl_link_list, self.spf_intf,  self.non_dl_link[0:2])
        checkpoint = "Subtest1:Bring down 2 spine interface and validate traffic"
        fun_test.simple_assert(result, checkpoint)

        ##
        # Sub Test-2: 4 Interface down
        ##
        if self.source == 'host':
            # Get HNU port traffic status again before starting further test
            dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
            dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
        else:
            # Clear Rx port
            clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
            fun_test.sleep("Sleeping  1 sec", seconds=1)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        fun_test.log("Subtest 2: Bring down 4 non DL interface and validate traffic")
        for item in self.non_dl_link[2:4]:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=False)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
            self.down_interface_name_list.append(name)

        result=self.verify_ffr_intrarack_non_fcp(dut_port, port, self.source, self.non_dl_link_list, self.spf_intf,  self.non_dl_link[0:4]) 
        checkpoint = "Subtest 2: Bring down 4 non DL interface and validate traffic"
        fun_test.simple_assert(result, checkpoint)

        ##
        # Sub Test-3: Bring up all interface and validate traffic
        ##
        if self.source == 'host':
            # Get HNU port traffic status again before starting further test
            dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
            dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
        else:
            # Clear Rx port
            clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
            fun_test.sleep("Sleeping  1 sec", seconds=1)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        fun_test.log("sub Test-3: Bring up all interface and validate traffic")
        for item in down_interface_name_list:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=True)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)

        if self.source == 'host':
            self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=False)
        else:
            self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=False) 


class FFRIntraRackFCPBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface_list = []
    down_interface_name_list = []

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack NFCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, ch_enable=False, gph_enable=False, flow_type='multi', source='host'):
        self.ch_enable=ch_enable
        self.gph_enable=gph_enable
        self.flow_type=flow_type
        self.source=source
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='intrarack1')


        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)


        load = 100
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_FIXED
        self.streamblock_obj.FixedFrameLength = 80

        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3

        # Change generator config parameters
        gen_config_obj.Duration = self.duration_seconds
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

        if self.source == 'host':

            ## TODO Des IP need to change
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip9'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Add UDP header"
            udp_header_obj = UDP(destination_port=10101)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
            fun_test.simple_assert(result, "Added UDP header with dest port 10101")
            fun_test.simple_assert(udp_header_obj, checkpoint)
        else:

            # Crafting FCP header for Sx
            checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
            ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip8'],
                                   source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Add UDP header"
            udp_header_obj = UDP(destination_port=7085)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
            fun_test.simple_assert(result, "Added UDP header with dest port 7085")
            fun_test.simple_assert(udp_header_obj, checkpoint)

            checkpoint = "Add Custom FCP header"
            custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][0])
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_1)
            fun_test.simple_assert(configure_cust_header, checkpoint)

            custom_header_2 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][1])
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_2)
            fun_test.test_assert(configure_cust_header, "Configure custom header")
            fun_test.simple_assert(configure_cust_header, checkpoint) 

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")
        if  not self.dl_status:
            self.enable_disable_intf(intf_name=self.spf_intf, status=True)

    def run(self):
        if  self.source == 'host':
            port = port_1
            dut_port = dut_port_1
        elif self.source == 'spine':
            port = port_2
            dut_port = dut_port_2
        else:
            port = port_3
            dut_port = dut_port_3
        next_hop_intf_list = self.get_all_nexthop(type='intraracks',id='fcp_intrarack1')
        self.spf_intf= self.get_direct_link(type='intraracks',id='fcp_intrarack1')
        self.spf_intf_name= 'fpg'+str(self.get_direct_link(type='intraracks',id='fcp_intrarack1'))
        self.non_dl_link_list=next_hop_intf_list.remove(self.get_direct_link(type='intraracks',id='fcp_intrarack1'))

        fun_test.log("Disable Direct Link first for traffic to take non direct link")
        # Disable the direct link interface
        self.enable_disable_intf(intf_name=self.spf_intf_name, status=False)
        down_interface_name_list.append(self.spf_intf_name)

        if self.source == 'host':
           self.verify_hnu_fcp_traffic(dut_port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=False)
        else:
            self.verify_nu_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=False)

        #
        # Sub Test-1: 2 Interface down
        ##
        fun_test.log("Subtest 1: Bring down 2 non DL interface and validate traffic")
        for item in self.non_dl_link[0:2]:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=False)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
            self.down_interface_name_list.append(name)
        result=self.verify_ffr_intrarack_fcp(dut_port, port, self.source, self.non_dl_link_list, self.spf_intf,  self.non_dl_link[0:2])
        checkpoint = "Subtest1:Bring down 2 spine interface and validate traffic"
        fun_test.simple_assert(result, checkpoint)

        #
        # Sub Test-2: 4 Interface down
        ##
        fun_test.log("Subtest 1: Bring down 4 non DL interface and validate traffic")
        for item in self.non_dl_link[0:4]:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=False)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
            self.down_interface_name_list.append(name)
        result=self.verify_ffr_intrarack_fcp(dut_port, port, self.source, self.non_dl_link_list, self.spf_intf,  self.non_dl_link[0:4])
        checkpoint = "Subtest1:Bring down 2 spine interface and validate traffic"
        fun_test.simple_assert(result, checkpoint)  

        #
        # Sub Test-3: Bring 2 non DL down link back traffic should distribute
        ##
        fun_test.log("Subtest 3: Bring 2 non DL down link back traffic should distribute")
        for item in self.non_dl_link[0:2]:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=True)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)
        result=self.verify_ffr_intrarack_fcp(dut_port, port, self.source, self.non_dl_link_list, self.spf_intf,  self.non_dl_link[2:4])
        checkpoint = "Subtest 3: Bring 2 non DL down link back traffic should distribute"
        fun_test.simple_assert(result, checkpoint)

        #
        # Sub Test-4: Bring alllink all  
        ##
        if self.source == 'host':
            # Get HNU port traffic status again before starting further test
            dut_port_1_pre_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
            dut_port_1_pre_rx = get_dut_output_stats_value(dut_port_1_pre_results, FRAMES_RECEIVED_OK, tx=False)
        else:
            # Clear Rx port
            clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
            fun_test.sleep("Sleeping  1 sec", seconds=1)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        fun_test.log("sub Test-4: Bring up all interface and validate traffic")
        for item in down_interface_name_list:
            name = 'fpg'+str(item)
            # Disable one fabric link
            self.enable_disable_intf(intf_name=name, status=True)
            fun_test.sleep("Sleeping  5 sec between shutting down interface", seconds=5)

        if self.source == 'host':
            self.verify_hnu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=True)
        else:
            self.verify_nu_non_fcp_traffic(dut_port, port, next_hop_intf_list, flow='multi', traffic_type='intra', spf_up=True)


class InjectFSFBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface = None
    down_interface_name = None

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack NFCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, spine_failure='peer', traffic_type='nfcp'):

        self.spine_failure=spine_failure
        self.traffic_type=traffic_type 
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj) 


    def setup(self):
        if self.traffic_type == 'nfcp':
            self.next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
        else:
            self.next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1') 

        if self.spine_failure == 'peer':
            self.port = port_3
            self.dut_port = dut_port_3
        else: 
            self.port = port_2
            self.dut_port = dut_port_2
        
        self.source_port=port_1
        self.source_dut_port=dut_port_1

    def run(self):

        # Send Interrack traffic
        streamblock_obj=self.create_hnu_interrack_frame(duration=60, port=self.source_port, traffic_type=self.traffic_type)
     
        if self.traffic_type == 'nfcp':
            self.verify_hnu_non_fcp_traffic(self.source_dut_port, self.source_port, self.next_hop_intf_list, flow='multi')
        else:
            self.verify_hnu_fcp_traffic(self.dut_port, self.port, self.next_hop_intf_list, flow='multi')
        self.delete_stream(streamblock_obj)

        # Send FSF Frame to Indicate Spine Port FPG 2 is down
        streamblock_obj=self.create_fsf_frame(duration=1, port=self.port)
        self.start_traffic(self.port)
        fun_test.sleep("Sleeping for executing traffic", seconds=2) 
        self.delete_stream(streamblock_obj)
  
        # Send Interrack traffic
        streamblock_obj=self.create_hnu_interrack_frame(duration=60, port=self.source_port, traffic_type='multi')
        self.start_traffic(self.source_port)

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=60)

        # Rx packet on DUT
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port,hnu=True)
        dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_1_rx = dut_port_1_rx - dut_port_1_pre_rx

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
 
        # Ensure traffic distribution is as per the weight
        if self.traffic_type == 'nfcp':
            intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='interrack1')
        else:
            intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='fcp_interrack')

        fun_test.log("Re-adjusting the interface weight expectation as FSF frame arrived")
        intf_wight_list[self.dut_port]= intf_wight_list[self.dut_port] -1

        unit_weight  = self.get_pkt_weight_unit(type='interracks',id='interrack1', total_pkt=sum(tx_result_dict.values()))
        result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix transmited from each nexthop as per wieght")
        # WRite CSR to enable the link back 
        # TODO 

class ValidateFSFBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    down_interface = None
    down_interface_name = None

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case for validating FSF frame",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def test_mode(self, nexthop_type='nfcp'):
        self.nexthop_type=nexthop_type
        self.get_network_handle(nc_obj=nu_obj, nu_con_obj=network_controller_obj, temp_obj=template_obj)

    def setup(self):
        if self.nexthop_type == 'nfcp':
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1')
            spine_next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
        else:
            next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
            spine_next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')

        # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.sleep("Sleeping  1 sec", seconds=1)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        if self.down_interface_name is not None:
            # Enable the interface back
            self.enable_disable_intf(intf_name=self.down_interface_name, status=True)   

        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):

        # Start capture
        capture_obj = Capture()
        start_capture = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj, port_handle=port_3)
        fun_test.test_assert(start_capture, "Started capture on port %s" % port_3)

        fun_test.sleep("Letting capture to start", seconds=5)

        # Get all spine interface
        if self.nexthop_type == 'nfcp':
            spine_next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='spine')
            fabric_next_hop_intf_list = self.get_all_nexthop(type='interracks',id='interrack1',link='fabric')
        else:
            spine_next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='spine')
            fabric_next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1',link='fabric')

        # Disable one spine link
        self.down_interface = spine_next_hop_intf_list[0]
        self.down_interface_name = 'fpg'+str(self.down_interface) 
        self.enable_disable_intf(intf_name=self.down_interface_name, status=False)

        # Stop capture
        stop_capture = template_obj.stc_manager.stop_capture_command(capture_obj._spirent_handle)
        fun_test.test_assert(stop_capture, "Stopped capture on port %s" % port_3)

        tx_result_dict = {}
        for item in fabric_next_hop_intf_list:
            dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
            tx_packet = get_dut_output_stats_value(dut_results, FRAMES_TRANSMITTED_OK)
            if tx_packet == None:
                tx_result_dict[item] = 0
            else:
                tx_result_dict[item] = tx_packet


        # Validate atleast one FSF should egress via each fabric interface 
        # TODO Change this validation to Octet size of the FSF packet  
        for item in tx_result_dict:
            if tx_result_dict[item] != 1:
                fun_test.test_assert_expected(expected=1, actual=tx_result_dict[item],
                      message="Ensure one FSF packer egress via fabric interface")    
        
        # Save capture   
        file = fun_test.get_temp_file_name()
        file_name_1 = file + '.pcap'
        file_path = SYSTEM_TMP_DIR
        self.pcap_file_path_1 = file_path + "/" + file_name_1

        saved = template_obj.stc_manager.save_capture_data_command(capture_handle=capture_obj._spirent_handle,
                                                                   file_name=file_name_1,
                                                                   file_name_path=file_path)
        fun_test.test_assert(saved, "Saved pcap %s to local machine" % self.pcap_file_path_1)

        fun_test.test_assert(os.path.exists(self.pcap_file_path_1), message="Check pcap file exists locally")        

        pcap_parser_1 = PcapParser(self.pcap_file_path_1)
        # Check if atleast one packet exists for each priority with quanta value specified and 0
        compare_dict = {}
        all_captures = pcap_parser_1.get_captures_from_file()
        #for capture in all_captures:
        #    output_dict = pcap_parser_1.get_all_packet_fields(capture)

        # TODO Add Spine index is correct


### NEWTC

class RemoteSpineFailureBaseTestCase(FunTestCase, BaseSetup):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 60
    down_interface = None
    down_interface_name = None

    def describe(self):
        self.set_test_details(id=999,
                              summary="Base Test Case from Inter Rack FCP traffic",
                              steps="""
                        1. Base test case will be caled by diffrent test cases based on Traffic source.
                           Traffic source can be host /fab
                        2. Spine and Fab link failure will be handled based on input from original test case
                        3. Traffic validation will be based on traffic source and link failure
                        """)

    def setup(self):
        next_hop_intf_list = self.get_all_nexthop(type='interracks',id='fcp_interrack1')
     
         # Clear port results on DUT
        for item in next_hop_intf_list:
            clear_id = network_controller_obj.clear_port_stats(port_num=item)
            fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % item)

        # Set Spirent source port as Spine
        port = port_2
        dut_port = dut_port_2

        load = 30
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 82
        self.streamblock_obj.MaxFrameLength = 900

        # Change generator config parameters
        gen_obj = template_obj.stc_manager.get_generator(port_handle=port)
        gen_config_obj.Duration = self.duration_seconds
        config_obj = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")
        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

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

        # Crafting FCP packet for Sx /Dx cases
        checkpoint = "Configure IP address for %s " % self.streamblock_obj.spirent_handle
        ip_header_obj = Ipv4Header(destination_address=l3_config['destination_ip6'],
                               source_address=l3_config['source_ip1'], protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add UDP header"
        udp_header_obj = UDP(destination_port=7085)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with dest port 7085")

        checkpoint = "Add Custom FCP header"
        custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][0])
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_1)
        fun_test.simple_assert(custom_header_1, checkpoint)

        custom_header_2 = CustomBytePatternHeader(byte_pattern=custom_headers[FCP_Custom_Header][1])
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                                stream_block_handle=self.streamblock_obj.spirent_handle, header_obj=custom_header_2)
        fun_test.test_assert(configure_cust_header, "Configure custom header")
        fun_test.simple_assert(custom_header_2, checkpoint)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2, port_3])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        dut_port_3_results = None
        dut_port_2_results = None
        dut_port_1_transmit = None

        # Sending FCP Custom header field with remote spine index 4 as down. 
        self.down_interface=17
        

        port = port_2
        dut_port = dut_port_2

        # Execute traffic
        self.start_traffic(port)

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Clear Rx port
        clear_id = network_controller_obj.clear_port_stats(port_num=dut_port)
        fun_test.test_assert(clear_id, message="Clear stats on port num %s of dut" % dut_port)

        # Rx packet on DUT
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port)
        dut_port_1_rx = get_dut_output_stats_value(dut_port_1_results, OCTETS_RECEIVED_OK, tx=False)

        # Tx packet on DUT intf_weight_list
        tx_result_dict = {}
        for item in next_hop_intf_list:
            dut_results = network_controller_obj.peek_fpg_port_stats(item,hnu=False)
            tx_packet = get_dut_output_stats_value(dut_results, OCTETS_TRANSMITTED_OK)
            if tx_packet == None:
                tx_result_dict[item] = 0
            else:
                tx_result_dict[item] = tx_packet
        fun_test.test_assert_expected(expected=1, actual=int(tx_result_dict.values().count(0)),
        message="Ensure as multiple flow, traffic should egress out via all diffrent nexthop except Spine Interface")

        result=self.validate_received_pkt_count(dut_port_1_rx, sum(tx_result_dict.values()), TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix recieved from traffic generator is sent out via FPG")

        # Ensure traffic distribution is as per the weight
        intf_weight_list  = self.get_all_nexthop_weight(type='interracks',id='fcp_interrack1', link='spine', ex_intf=self.down_interface)
        unit_weight  = self.get_spine_pkt_weight_unit_post_link_failure(type='interracks',id='fcp_interrack1', total_pkt=sum(tx_result_dict.values()), intf_list=[self.down_interface])
        result=self.validate_received_pkt_count_weight(tx_result_dict, intf_weight_list, sum(tx_result_dict.values()), unit_weight, TOLERANCE)
        fun_test.test_assert_expected(expected=True, actual=result,
        message="Ensure traffix transmited fro Test Case fromm each nexthop as per wieght")

 

     
class NFCPInterrackHostSingleFlowNoFailureTC1(InterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=1,summary="Test NFCP Interrack Traffic From Host with Single Flow and No Failure",
            steps="""
            1. Test single flow fixed length NFCP traffic 
            2. Traffic source is host, destined for Interrack 
            4. Traffic should leave via any of the Fabric/Spine port
            """)

    def test_mode(self):
        super(NFCPInterrackHostSingleFlowNoFailureTC1, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=False, flow_type='single', source='host')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostSingleFlowNoFailureTC1, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackHostSingleFlowNoFailureTC1, self).run()

    def cleanup(self):
        super(NFCPInterrackHostSingleFlowNoFailureTC1, self).cleanup()

class NFCPInterrackHostMultipleFlowNoFailureTC2(InterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=2,summary="Test NFCP Interrack Traffic From Host with Multiple Flow and No Failure",
            steps="""
            1. Test multiple flow (Diffrent ) NFCP traffic
            2. Traffic source is host, destined for Interrack
            3. Traffic should leave via all the Fabric and Spine interface

            """)

    def test_mode(self):
        super(NFCPInterrackHostMultipleFlowNoFailureTC2, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=False, flow_type='multi', source='host')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowNoFailureTC2, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowNoFailureTC2, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowNoFailureTC2, self).cleanup()

class NFCPInterrackFabMultipleFlowNoFailureTC3(InterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=3,summary="Test NFCP Interrack Traffic From Fab with Multiple Flow and No Failure",
            steps="""
            1. Test multiple flow (Diffrent ) NFCP traffic
            2. Traffic source is fab, destined for Interrack
            3. Traffic should leave via all the Spine interface

            """)

    def test_mode(self):
        super(NFCPInterrackFabMultipleFlowNoFailureTC3, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=False, flow_type='multi', source='fabric')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleFlowNoFailureTC3, self).setup()


    def run(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleFlowNoFailureTC3, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleFlowNoFailureTC3, self).cleanup()

class NFCPIntrarackHostMultipleFlowNoFailureTC4(IntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=4,summary="Test NFCP Intrarack Traffic From Host with Multiple Flow and No Failure DL Up",
            steps="""
            1. Test NFCP Inrtraffic coming from host, destined for Intrarack.
            2. Validate traffic is leaving via all the Fabric port
            3. As DL is up should receive 2x traffic than other interface

            """)
    def test_mode(self):
        super(NFCPIntrarackHostMultipleFlowNoFailureTC4, self).test_mode(source='host', dl_status=True)

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackHostMultipleFlowNoFailureTC4, self).setup()

    def run(self):
        super(NFCPIntrarackHostMultipleFlowNoFailureTC4, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackHostMultipleFlowNoFailureTC4, self).cleanup()

class NFCPIntrarackFabMultipleFlowNoFailureTC5(IntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=5,summary="Test NFCP Intrarack Traffic From Fab with Multiple Flow and No Failure DL Up",
            steps="""
            1. Test NFCP Inrtraffic coming from fab, destine Intrarack.
            2. Validate traffic is leaving only via DL port

            """)

    def test_mode(self):
        super(NFCPIntrarackFabMultipleFlowNoFailureTC5, self).test_mode(source='fab', dl_status=True)

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultipleFlowNoFailureTC5, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackFabMultipleFlowNoFailureTC5, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultipleFlowNoFailureTC5, self).cleanup()

class NFCPIntrarackSpineMultipleFlowNoFailureTC6(IntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=6,summary="Test NFCP Intrarack Traffic From Spine with Multiple Flow and No Failure DL Up",
            steps="""
            1. Test NFCP Inrtraffic coming from spine port, destined Intrarack.
            2. Validate traffic is leaving only via DL port

            """)

    def test_mode(self):
        super(NFCPIntrarackSpineMultipleFlowNoFailureTC6, self).test_mode(source='spine', dl_status=True)

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackSpineMultipleFlowNoFailureTC6, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackSpineMultipleFlowNoFailureTC6, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackSpineMultipleFlowNoFailureTC6, self).cleanup()

## NFCP Forwarding Type Cases End Here

class FCPInterrackHostSingleFlowNoFailureTC7(InterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=7,summary="Test FCP Interrack Traffic From Host with Single Flow No failure",
            steps="""
            1. Test FCP traffic coming from Host (Sf) , destined Interrack.
            2. Traffic should spray to  all the Fabric and Spine interface

            """)

    def test_mode(self):
        super(FCPInterrackHostSingleFlowNoFailureTC7, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=False, source='host')

    def setup(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowNoFailureTC7, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowNoFailureTC7, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowNoFailureTC7, self).cleanup()

class FCPInterrackFabSingleFlowNoFailureTC8(InterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=8,summary="Test FCP Interrack Traffic From Fab with Single Flow No failure",
            steps="""
            1. Test FCP traffic coming from Fab (Sx). Traffic is destined to Interrack.
            2. Traffic should spray to all Spine interface

            """)

    def test_mode(self):
        super(FCPInterrackFabSingleFlowNoFailureTC8, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=False, source='fabric')

    def setup(self):
        self.test_mode()
        super(FCPInterrackFabSingleFlowNoFailureTC8, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackFabSingleFlowNoFailureTC8, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackFabSingleFlowNoFailureTC8, self).cleanup()


class FCPIntrarackHostSingleFlowNoFailureTC9(IntraRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=9,summary="Test FCP Intrarack Traffic From Host with Single Flow No Failure DL Up",
            steps="""
            1. Test FCP Inrtraffic coming from host (Sf), destined to Intrarack
            3. Traffic should egress only via DL
            """)

    def test_mode(self):
        super(FCPIntrarackHostSingleFlowNoFailureTC9, self).test_mode(source='host', dl_status=True)

    def setup(self):
        self.test_mode()
        super(FCPIntrarackHostSingleFlowNoFailureTC9, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackHostSingleFlowNoFailureTC9, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackHostSingleFlowNoFailureTC9, self).cleanup()


class FCPIntrarackFabSingleFlowNoFailureTC10(IntraRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=10,summary="Test FCP Intrarack Traffic From fab with Single Flow No Failure DL Up",
            steps="""
            1. Test FCP Inrtraffic coming from fab port (Sx), destined to Intrarack
            3. Traffic should exis only via DL
            """)

    def test_mode(self):
        super(FCPIntrarackFabSingleFlowNoFailureTC10, self).test_mode(source='fab', dl_status=True)

    def setup(self):
        self.test_mode()
        super(FCPIntrarackFabSingleFlowNoFailureTC10, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackFabSingleFlowNoFailureTC10, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackFabSingleFlowNoFailureTC10, self).cleanup()


class FCPIntrarackSpineSingleFlowNoFailureTC11(IntraRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=11,summary="Test FCP Intrarack Traffic From spine with Single Flow No Failure DL Up",
            steps="""
            1. Test FCP Inrtraffic coming from spine port (Dx),destined to Intrarack  
            3. Traffic should exis only via DL
            """)

    def test_mode(self):
        super(FCPIntrarackSpineSingleFlowNoFailureTC11, self).test_mode(source='spine', dl_status=True)

    def setup(self):
        self.test_mode()
        super(FCPIntrarackSpineSingleFlowNoFailureTC11, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackSpineSingleFlowNoFailureTC11, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackSpineSingleFlowNoFailureTC11, self).cleanup()

# FCP Forwarding Type Test Case end here
# Non Failure related cases end here


class NFCPInterrackHostMultipleFlowFabricFailureTC12(InterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=12,summary="Test NFCP Interrack Traffic From Host with Multiple Flow and Local Single Fabric Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(NFCPInterrackHostMultipleFlowFabricFailureTC12, self).test_mode(source='host', ch_enable=False, gph_enable=False, fabric_down=True, spine_down=False, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowFabricFailureTC12, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowFabricFailureTC12, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowFabricFailureTC12, self).cleanup()


class NFCPInterrackHostMultipleFlowSpineFailureTC13(InterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=13,summary="Test NFCP Interrack Traffic From Host with Multiple Flow and Local Spine Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the Spine link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)
    def test_mode(self):
        super(NFCPInterrackHostMultipleFlowSpineFailureTC13, self).test_mode(source='host', ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, flow_type='multi')


    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowSpineFailureTC13, self).setup()


    def run(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowSpineFailureTC13, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFlowSpineFailureTC13, self).cleanup()

class NFCPInterrackFabMultipleFlowSpineFailureTC14(InterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=14,summary="Test NFCP Interrack Traffic From Fab with Multiple Flow and Local Spine link Failure",
            steps="""
            1. Test NFCP traffic coming from fab port
            2. Validate traffic is leaving via all the Spine port
            3. Disable one of the Spine link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)
    def test_mode(self):
        super(NFCPInterrackFabMultipleFlowSpineFailureTC14, self).test_mode(source='fabric', ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, flow_type='multi')


    def setup(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleFlowSpineFailureTC14, self).setup()


    def run(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleFlowSpineFailureTC14, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleFlowSpineFailureTC14, self).cleanup()


class NFCPIntrarackHostMultiipleFlowDLDownTC15(IntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=15,summary="Test NFCP Intrarack Traffic coming from host with Multiple Flow  and DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic should egress via all the fabric port DL should get 2x.
            3. Disable the DL link
            4. Traffic should ECMP over all the non DL link

            """)

    def test_mode(self):
        super(NFCPIntrarackHostMultiipleFlowDLDownTC15, self).test_mode(source='host', dl_status=False)

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackHostMultiipleFlowDLDownTC15, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackHostMultiipleFlowDLDownTC15, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackHostMultiipleFlowDLDownTC15, self).cleanup()


class NFCPIntrarackFabMultiipleFlowDLDownTC16(IntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=16,summary="Test NFCP Intrarack Traffic coming from fab with Multiple Flow  and DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from fab port, destined Intrarack.
            2. Traffic should egress only via DL.
            3. Bring the DL down.
            4. Traffic should ECMP over all non DL link

            """)

    def test_mode(self):
        super(NFCPIntrarackFabMultiipleFlowDLDownTC16, self).test_mode(source='fab', dl_status=False)

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowDLDownTC16, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowDLDownTC16, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowDLDownTC16, self).cleanup()

class NFCPIntrarackSpineMultiipleFlowDLDownTC17(IntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=17,summary="Test NFCP Intrarack Traffic coming from spine with Multiple Flow  and DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from spine port, destined Intrarack.
            2. Traffic should egress only via DL.
            3. Bring the DL down.
            4. Traffic should ECMP over all non DL link

            """)

    def test_mode(self):
        super(NFCPIntrarackSpineMultiipleFlowDLDownTC17, self).test_mode(source='spine', dl_status=False)

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackSpineMultiipleFlowDLDownTC17, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackSpineMultiipleFlowDLDownTC17, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackSpineMultiipleFlowDLDownTC17, self).cleanup()

# Non FCP Single Link Failure Ends here

class FCPInterrackHostSingleFlowFabricFailureTC18(InterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=18,summary="Test FCP Interrack Traffic From Host with Single Flow and Local Fabric Link Failure",
            steps="""
            1. Test FCP traffic coming from host, destined Interrack
            2. Bring one fabric link down. 
            3. Traffic should spray over all remaning fabric and spine link.

            """)

    def test_mode(self):
        super(FCPInterrackHostSingleFlowFabricFailureTC18, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=True, spine_down=False, source='host')

    def setup(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowFabricFailureTC18, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowFabricFailureTC18, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowFabricFailureTC18, self).cleanup()

class FCPInterrackHostSingleFlowSpineFailureTC19(InterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=19,summary="Test FCP Interrack Traffic From Host with Single Flow and Local Spine Link Failure",
            steps="""
            1. Test FCP traffic coming from host, destined Interrack
            2. Bring one spine link down.
            3. Traffic should spray over all ramanining fabric and spine link.
            

            """)

    def test_mode(self):
        super(FCPInterrackHostSingleFlowSpineFailureTC19, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, source='host')

    def setup(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowSpineFailureTC19, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowSpineFailureTC19, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackHostSingleFlowSpineFailureTC19, self).cleanup()

class FCPInterrackFabSingleFlowSpineFailureTC20(InterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=20,summary="Test FCP Interrack Traffic From Fab with Single Flow and Local Spine Link Failure",
            steps="""
            1. Test FCP traffic coming from fab, destined Interrack
            2. Bring one spine link down.
            3. Traffic should spray over all ramanining spine link.
            """)

    def test_mode(self):
        super(FCPInterrackFabSingleFlowSpineFailureTC20, self).test_mode(ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, source='fab')

    def setup(self):
        self.test_mode()
        super(FCPInterrackFabSingleFlowSpineFailureTC20, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackFabSingleFlowSpineFailureTC20, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackFabSingleFlowSpineFailureTC20, self).cleanup()

class FCPIntrarackHostSingleFlowDlDownTC21(IntraRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=21,summary="Test FCP Intrarack Traffic From Host with Single Single  Failure DL Down",
            steps="""
            1. Test FCP Inrtraffic coming from host, destined Intrarack
            3. When DL is down traffic spar to all non DL link
            """)

    def test_mode(self):
        super(FCPIntrarackHostSingleFlowDlDownTC21, self).test_mode(source='host', dl_status=False)

    def setup(self):
        self.test_mode()
        super(FCPIntrarackHostSingleFlowDlDownTC21, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackHostSingleFlowDlDownTC21, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackHostSingleFlowDlDownTC21, self).cleanup()

class FCPIntrarackFabSingleFlowDLDownTC22(IntraRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=22,summary="Test FCP Intrarack Traffic From fab with Single Flow Single Failure DL down",
            steps="""
            1. Test FCP Inrtraffic coming from fab port, destined Intrarack
            2. When DL is down traffic will pick single non DL link 
            """)

    def test_mode(self):
        super(FCPIntrarackFabSingleFlowDLDownTC22, self).test_mode(source='fab', dl_status=False)

    def setup(self):
        self.test_mode()
        super(FCPIntrarackFabSingleFlowDLDownTC22, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackFabSingleFlowDLDownTC22, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackFabSingleFlowDLDownTC22, self).cleanup()

class FCPIntrarackSpineSingleFlowDLDownTC23(IntraRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=23,summary="Test FCP Intrarack Traffic From spine with Single Flow No Failure DL Up",
            steps="""
            1. Test FCP Inrtraffic coming from spine port, destined Intrarack
            2. When DL is down traffic will pick single non DL link
            """)

    def test_mode(self):
        super(FCPIntrarackSpineSingleFlowDLDownTC23, self).test_mode(source='spine', dl_status=False)

    def setup(self):
        self.test_mode()
        super(FCPIntrarackSpineSingleFlowDLDownTC23, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackSpineSingleFlowDLDownTC23, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackSpineSingleFlowDLDownTC23, self).cleanup()


###
# FFR Start Here
class NFCPInterrackHostMultipleFabricFailureTC24(FFRInterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=24,summary="Test NFCP Interrack Traffic From Host with Multiple Flow and Local Multiple Fabric Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(NFCPInterrackHostMultipleFabricFailureTC24, self).test_mode(source='host', ch_enable=False, gph_enable=False, fabric_down=True, spine_down=False, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFabricFailureTC24, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFabricFailureTC24, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleFabricFailureTC24, self).cleanup()

class NFCPInterrackHostMultipleSpineFailureTC25(FFRInterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=25,summary="Test NFCP Interrack Traffic From Host with Multiple Flow and Local Multiple Spine Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(NFCPInterrackHostMultipleSpineFailureTC25, self).test_mode(source='host', ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleSpineFailureTC25, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleSpineFailureTC25, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackHostMultipleSpineFailureTC25, self).cleanup()

class NFCPInterrackFabMultipleSpineFailureTC26(FFRInterRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=26,summary="Test NFCP Interrack Traffic From Fab with Multiple Flow and Local Multiple Spine Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(NFCPInterrackFabMultipleSpineFailureTC26, self).test_mode(source='fab', ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleSpineFailureTC26, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleSpineFailureTC26, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackFabMultipleSpineFailureTC26, self).cleanup()

class FCPInterrackHostMultipleFabricFailureTC27(FFRInterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=24,summary="Test FCP Interrack Traffic From Host with Multiple Flow and Local Multiple Fabric Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(FCPInterrackHostMultipleFabricFailureTC27, self).test_mode(source='host', ch_enable=False, gph_enable=False, fabric_down=True, spine_down=False, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(FCPInterrackHostMultipleFabricFailureTC27, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackHostMultipleFabricFailureTC27, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackHostMultipleFabricFailureTC27, self).cleanup()

class FCPInterrackHostMultipleSpineFailureTC28(FFRInterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=24,summary="Test FCP Interrack Traffic From Host with Multiple Flow and Local Multiple Fabric Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(FCPInterrackHostMultipleSpineFailureTC28, self).test_mode(source='host', ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(FCPInterrackHostMultipleSpineFailureTC28, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackHostMultipleSpineFailureTC28, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackHostMultipleSpineFailureTC28, self).cleanup()

class FCPInterrackFabMultipleSpineFailureTC29(FFRInterRackFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=24,summary="Test FCP Interrack Traffic From Host with Multiple Flow and Local Multiple Fabric Link Failure",
            steps="""
            1. Test NFCP traffic coming from host port
            2. Validate traffic is leaving via all the Spine and Fabric port
            3. Disable one of the fabric link . Traffic weight should change accodrngly
            3. Enable the interface back. It should start receiving traffic as per weight.

            """)

    def test_mode(self):
        super(FCPInterrackFabMultipleSpineFailureTC29, self).test_mode(source='fab', ch_enable=False, gph_enable=False, fabric_down=False, spine_down=True, flow_type='multi')

    def setup(self):
        self.test_mode()
        super(FCPInterrackFabMultipleSpineFailureTC29, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackFabMultipleSpineFailureTC29, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackFabMultipleSpineFailureTC29, self).cleanup()

class NFCPIntrarackHostMultiipleFlowMultipleLinkDownTC30(FFRIntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=30,summary="Test NFCP Intrarack Traffic coming from host with Multiple Flow  and DL Dow and Multiple Non DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(NFCPIntrarackHostMultiipleFlowMultipleLinkDownTC30, self).test_mode(source='host')

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackHostMultiipleFlowMultipleLinkDownTC30, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackHostMultiipleFlowMultipleLinkDownTC30, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackHostMultiipleFlowMultipleLinkDownTC30, self).cleanup()

class NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC31(FFRIntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=31,summary="Test NFCP Intrarack Traffic coming from host with Multiple Flow  and DL Dow and Multiple Non DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        supee(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC31, self).test_mode(source='fab')

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC31, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC31, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC31, self).cleanup()

class NFCPIntrarackSpineMultiipleFlowMultipleLinkDownTC32(FFRIntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=32,summary="Test NFCP Intrarack Traffic coming from host with Multiple Flow  and DL Dow and Multiple Non DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC32, self).test_mode(source='fab')

    def setup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC32, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC32, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC32, self).cleanup()

class FCPIntrarackHostMultiipleFlowMultipleLinkDownTC33(FFRIntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=31,summary="Test FCP Intrarack Traffic coming from host with Multiple Flow  and DL Dow and Multiple Non DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(FCPIntrarackHostMultiipleFlowMultipleLinkDownTC33, self).test_mode(source='host')

    def setup(self):
        self.test_mode()
        super(FCPIntrarackHostMultiipleFlowMultipleLinkDownTC33, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackHostMultiipleFlowMultipleLinkDownTC33, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackHostMultiipleFlowMultipleLinkDownTC33, self).cleanup()

class FCPIntrarackFabMultiipleFlowMultipleLinkDownTC34(FFRIntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=34,summary="Test FCP Intrarack Traffic coming from host with Multiple Flow  and DL Dow and Multiple Non DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(FCPIntrarackFabMultiipleFlowMultipleLinkDownTC34, self).test_mode(source='fab')

    def setup(self):
        self.test_mode()
        super(FCPIntrarackFabMultiipleFlowMultipleLinkDownTC34, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackFabMultiipleFlowMultipleLinkDownTC34, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackFabMultiipleFlowMultipleLinkDownTC34, self).cleanup()

class FCPIntrarackSpineMultiipleFlowMultipleLinkDownTC35(FFRIntraRackNFCPBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=35,summary="Test FCP Intrarack Traffic coming from host with Multiple Flow  and DL Dow and Multiple Non DL Down",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(FCPIntrarackSpineMultiipleFlowMultipleLinkDownTC35, self).test_mode(source='spine')

    def setup(self):
        self.test_mode()
        super(FCPIntrarackSpineMultiipleFlowMultipleLinkDownTC35, self).setup()

    def run(self):
        self.test_mode()
        super(FCPIntrarackSpineMultiipleFlowMultipleLinkDownTC35, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPIntrarackSpineMultiipleFlowMultipleLinkDownTC35, self).cleanup()

class NFCPInterrackHostSinglePeerSpineLinkFailureTC36(InjectFSFBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=36,summary="Test NFCP Interrack Traffic coming from host with Multiple Flow  and Peer Spine Link Failure",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(NFCPInterrackHostSinglePeerSpineLinkFailureTC36, self).test_mode(spine_failure='peer', traffic_type='nfcp')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackHostSinglePeerSpineLinkFailureTC36, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackHostSinglePeerSpineLinkFailureTC36, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackHostSinglePeerSpineLinkFailureTC36, self).cleanup()

class FCPInterrackHostSinglePeerSpineLinkFailureTC37(InjectFSFBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=37,summary="Test FCP Interrack Traffic coming from host with Multiple Flow  and Peer Spine Link Failure",
            steps="""
            1. Test NFCP Inrtraffic coming from host port
            2. Validate traffic is leaving via all the Fabric port

            """)

    def test_mode(self):
        super(FCPInterrackHostSinglePeerSpineLinkFailureTC37, self).test_mode(spine_failure='peer', traffic_type='fcp')

    def setup(self):
        self.test_mode()
        super(FCPInterrackHostSinglePeerSpineLinkFailureTC37, self).setup()

    def run(self):
        self.test_mode()
        super(FCPInterrackHostSinglePeerSpineLinkFailureTC37, self).run()

    def cleanup(self):
        self.test_mode()
        super(FCPInterrackHostSinglePeerSpineLinkFailureTC37, self).cleanup()

class NFCPInterrackFSFSpineLinkFailureTC38(ValidateFSFBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=38,summary="Test FSF frame generation for local Spine Link Failure for Non FCP Interrack",
            steps="""
            1. Bring local spine link down failure fro Non FCP interrack
            2. Validate FSF is getting generated for fabric link 

            """)

    def test_mode(self):
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).test_mode(nexthop_type='nfcp')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).cleanup()

class FCPInterrackFSFSpineLinkFailureTC39(ValidateFSFBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=39,summary="Test FSF frame generation for local Spine Link Failure for FCP Interrack",
            steps="""
            1. Bring local spine link down failure fro FCP interrack
            2. Validate FSF is getting generated for fabric link

            """)

    def test_mode(self):
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).test_mode(nexthop_type='fcp')

    def setup(self):
        self.test_mode()
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).setup()

    def run(self):
        self.test_mode()
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).run()

    def cleanup(self):
        self.test_mode()
        super(NFCPInterrackFSFSpineLinkFailureTC38, self).cleanup()

class FCPRemoteSpineLinkFailureTC40(RemoteSpineFailureBaseTestCase):

    def describe(self):
        self.set_test_details(
            id=40,summary="Test Remote Spine Link Failure for FCP Interrack",
            steps="""
            1. Bring local spine link down failure fro FCP interrack
            2. Validate FSF is getting generated for fabric link

            """)

    def setup(self):
        super(FCPRemoteSpineLinkFailureTC40, self).setup()

    def run(self):
        super(FCPRemoteSpineLinkFailureTC40, self).run()

    def cleanup(self):
        super(FCPRemoteSpineLinkFailureTC40, self).cleanup()
###

if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(NFCPInterrackHostSingleFlowNoFailureTC1())
    #ts.add_test_case(NFCPInterrackHostMultipleFlowNoFailureTC2())
    #ts.add_test_case(NFCPInterrackFabMultipleFlowNoFailureTC3())
    #ts.add_test_case(NFCPIntrarackHostMultipleFlowNoFailureTC4())
    #ts.add_test_case(NFCPIntrarackFabMultipleFlowNoFailureTC5())
    #ts.add_test_case(NFCPIntrarackSpineMultipleFlowNoFailureTC6())
    #ts.add_test_case(FCPInterrackHostSingleFlowNoFailureTC7())
    #ts.add_test_case(FCPInterrackFabSingleFlowNoFailureTC8())
    #ts.add_test_case(FCPIntrarackHostSingleFlowNoFailureTC9())
    #ts.add_test_case(FCPIntrarackFabSingleFlowNoFailureTC10())
    #ts.add_test_case(FCPIntrarackSpineSingleFlowNoFailureTC11())
    #ts.add_test_case(NFCPInterrackHostMultipleFlowFabricFailureTC12())
    #ts.add_test_case(NFCPInterrackHostMultipleFlowSpineFailureTC13())
    #ts.add_test_case(NFCPInterrackFabMultipleFlowSpineFailureTC14())
    #ts.add_test_case(NFCPIntrarackHostMultiipleFlowDLDownTC15())
    #ts.add_test_case(NFCPIntrarackFabMultiipleFlowDLDownTC16())
    #ts.add_test_case(NFCPIntrarackSpineMultiipleFlowDLDownTC17())
    #ts.add_test_case(FCPInterrackHostSingleFlowFabricFailureTC18())
    #ts.add_test_case(FCPInterrackHostSingleFlowSpineFailureTC19())
    #ts.add_test_case(FCPInterrackFabSingleFlowSpineFailureTC20())
    #ts.add_test_case(FCPIntrarackHostSingleFlowDlDownTC21())
    #ts.add_test_case(FCPIntrarackFabSingleFlowDLDownTC22())
    #ts.add_test_case(FCPIntrarackSpineSingleFlowDLDownTC23())
    #ts.add_test_case(NFCPInterrackHostMultipleFabricFailureTC24())  
    #ts.add_test_case(NFCPInterrackHostMultipleSpineFailureTC25())  
    #ts.add_test_case(NFCPInterrackFabMultipleSpineFailureTC26())  
    #ts.add_test_case(FCPInterrackHostMultipleFabricFailureTC27())  
    #ts.add_test_case(FCPInterrackHostMultipleSpineFailureTC28())  
    #ts.add_test_case(FCPInterrackFabMultipleSpineFailureTC29())  
    #ts.add_test_case(NFCPIntrarackHostMultiipleFlowMultipleLinkDownTC30())  
    #ts.add_test_case(NFCPIntrarackFabMultiipleFlowMultipleLinkDownTC31())  
    #ts.add_test_case(NFCPIntrarackSpineMultiipleFlowMultipleLinkDownTC32())  
    # ts.add_test_case(FCPIntrarackHostMultiipleFlowMultipleLinkDownTC33())  
    #ts.add_test_case(FCPIntrarackFabMultiipleFlowMultipleLinkDownTC34())  
    #ts.add_test_case(FCPIntrarackSpineMultiipleFlowMultipleLinkDownTC35())  
    #ts.add_test_case(NFCPInterrackHostSinglePeerSpineLinkFailureTC36())  
    #ts.add_test_case(FCPInterrackHostSinglePeerSpineLinkFailureTC37())  
    #ts.add_test_case(NFCPInterrackFSFSpineLinkFailureTC38())  
    # ts.add_test_case(FCPInterrackFSFSpineLinkFailureTC39())  
    #ts.add_test_case(FCPRemoteSpineLinkFailureTC40())  
    ts.run()
