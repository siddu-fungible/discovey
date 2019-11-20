from lib.system.fun_test import *
from scripts.networking.nu_config_manager import NuConfigManager
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import NetworkController
from get_handles import *


def run_nu_transit(run_time=180, load=99.9, f1=0):
    flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU_POWER_F1_0
    if f1 == 1:
        flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU_POWER_F1_1

    flow_type = NuConfigManager.TRANSIT_FLOW_TYPE
    num_ports = 2

    nu_config_obj = NuConfigManager()
    fun_test.shared_variables['nu_config_obj'] = nu_config_obj
    spirent_config = nu_config_obj.read_traffic_generator_config()

    routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
    fun_test.simple_assert(routes_config, "Ensure routes config fetched")
    l3_config = routes_config['l3_config']

    destination_mac1 = routes_config['routermac']
    destination_ip20 = l3_config['destination_ip20']
    destination_ip0 = l3_config['destination_ip0']

    session_name = "f1-power-{}".format(f1)
    template_obj = SpirentEthernetTrafficTemplate(session_name=session_name, spirent_config=spirent_config,
                                                  chassis_type=SpirentManager.PHYSICAL_CHASSIS_TYPE)

    project_handle = template_obj.stc_manager.create_project(project_name=session_name)
    fun_test.simple_assert(project_handle, "Create power Project")

    result = template_obj.setup_ports_using_command(no_of_ports_needed=num_ports,
                                                    flow_type=flow_type, flow_direction=flow_direction)
    fun_test.test_assert(result['result'], "Configure setup")

    port_obj_list = []
    port_1 = result['port_list'][0]
    port_obj_list.append(port_1)
    port_2 = result['port_list'][1]
    port_obj_list.append(port_2)

    gen_objs = []
    streamblock_handles_list = []
    for port_obj in port_obj_list:
        destination_ip = destination_ip20
        if port_obj == port_2:
            destination_ip = destination_ip0
        gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                         duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                         advanced_interleaving=True)

        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_obj)
        gen_objs.append(gen_obj_1)
        config_obj = template_obj.configure_generator_config(port_handle=port_obj,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_obj)

        create_streamblock_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_PERCENT_LINE_RATE, fill_type=StreamBlock.FILL_TYPE_PRBS,
                                           frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED, load=load, fixed_frame_length=1500)
        streamblock_1 = template_obj.configure_stream_block(create_streamblock_1,
                                                            port_handle=port_obj)
        fun_test.test_assert(streamblock_1, "Creating streamblock on port %s" % port_obj)

        # Configure mac and ip on the stream
        ethernet = Ethernet2Header(destination_mac=destination_mac1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ethernet,
            delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(frame_stack,
                             "Added ethernet header to stream %s" % create_streamblock_1._spirent_handle)

        ipv4 = Ipv4Header(destination_address=destination_ip)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ipv4)
        fun_test.test_assert(frame_stack,
                             "Added ipv4 header to stream %s" % create_streamblock_1._spirent_handle)
        streamblock_handles_list.append(create_streamblock_1._spirent_handle)

    # Subscribe to results
    project = template_obj.stc_manager.get_project_handle()
    subscribe_results = template_obj.subscribe_to_all_results(parent=project)
    del subscribe_results['result']

    start = template_obj.enable_generator_configs(generator_configs=gen_objs)
    fun_test.test_assert(start, "Starting generators config")

    time_delta = 10
    time_interval = run_time / time_delta
    current_time = 0
    keep_running = True

    while keep_running:
        fun_test.sleep("Letting traffic run", seconds=time_interval)
        current_time += time_delta

        # Fetch Rx L1 rate
        output = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                    streamblock_handle_list=streamblock_handles_list,
                                                                    rx_summary_result=True, tx_stream_result=True)

        # rx_summary_subscribe_handle = subscribe_results['rx_summary_subscribe'],
        # tx_summary_subscribe_handle = subscribe_results['tx_subscribe']

        # for port_obj in port_obj_list:
        #     tx_port = port_1
        #     rx_port = port_2
        #     if port_obj == port_2:
        #         tx_port = port_1
        #         rx_port = port_2
        #     tx_port_result = template_obj.stc_manager.get_generator_port_results(
        #         port_handle=tx_port, subscribe_handle=tx_summary_subscribe_handle)
        #     rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
        #         port_handle=rx_port, subscribe_handle=rx_summary_subscribe_handle)
        #
        #     tx_l1_bit_rate_in_kbps = template_obj._convert_bps_to_kbps(
        #         count_in_bps=int(tx_port_result['L1BitRate']))
        #     rx_l1_bit_rate_in_kbps = template_obj._convert_bps_to_kbps(
        #         count_in_bps=int(rx_port_result['L1BitRate']))
        #     fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d kbps and Rx --> %d kbps " % (
        #         port_obj, tx_l1_bit_rate_in_kbps, rx_l1_bit_rate_in_kbps))

        for current_streamblock in streamblock_handles_list:
            rx_l1_bps = int(output[current_streamblock]['rx_summary_result']['L1BitRate'])
            rx_l1_rate = rx_l1_bps / float(1000000000)

            tx_l1_bps = int(output[current_streamblock]['tx_stream_result']['L1BitRate'])
            tx_l1_rate = tx_l1_bps / float(1000000000)

            fun_test.log("Tx and Rx rate for %s is %s and %s" % (current_streamblock, rx_l1_rate, tx_l1_rate))

        if current_time == run_time:
            keep_running = False

    stop = template_obj.disable_generator_configs(generator_configs=gen_objs)


def setup_nu_firewall(come_handle, f1=0):
    if f1 == 0:
        target_port = 42220
    elif f1 == 1:
        target_port = 42221
    network_controller_obj = NetworkController(dpc_server_ip=come_handle.host_ip, dpc_server_port=target_port)

    mode = 3
    num_flows = 134217728
    benchmark_ports = [0, 20]

    result = network_controller_obj.set_etp(pkt_adj_size=8)
    fun_test.simple_assert(result['status'], "Reset pkt_adj_size to 8")

    output_1 = network_controller_obj.set_nu_benchmark_1(mode=mode, num_flows=num_flows, flow_le_ddr=True,
                                                         flow_state_ddr=True)
    for fpg in benchmark_ports:
        result = network_controller_obj.set_nu_benchmark_1(mode=mode, fpg=fpg)
        fun_test.simple_assert(result['status'], 'Enable Firewall benchmark')

    output_2 = network_controller_obj.set_nu_benchmark_1(mode=mode, sport="10-2058", dport="10000-42768", protocol=17,
                                                         ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=0,
                                                         flow_inport=0, flow_outport=20)

    # output_3 = network_controller_obj.set_nu_benchmark_1(mode=mode, sport="10-2058", dport="10000-42768", protocol=17,
    #                                                      ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=67108864,
    #                                                      flow_inport=20, flow_outport=0)


def run_nu_firewall(come_handle, run_time=120, load=12, setup_dpc=True, f1=0):
    if setup_dpc:
        setup_nu_firewall(come_handle=come_handle, f1=f1)

    flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU_POWER_F1_0
    if f1 == 1:
        flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU_POWER_F1_1
    flow_type = NuConfigManager.TRANSIT_FLOW_TYPE
    num_ports = 2

    nu_config_obj = NuConfigManager()
    fun_test.shared_variables['nu_config_obj'] = nu_config_obj
    spirent_config = nu_config_obj.read_traffic_generator_config()

    routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
    fun_test.simple_assert(routes_config, "Ensure routes config fetched")
    l3_config = routes_config['l3_config']

    destination_mac1 = routes_config['routermac']
    src_ip = "29.1.1.1"
    dest_ip = "29.1.1.2"

    session_name = "f1-power-{}".format(f1)
    template_obj = SpirentEthernetTrafficTemplate(session_name=session_name, spirent_config=spirent_config,
                                                  chassis_type=SpirentManager.PHYSICAL_CHASSIS_TYPE)

    project_handle = template_obj.stc_manager.create_project(project_name=session_name)
    fun_test.simple_assert(project_handle, "Create power Project")

    result = template_obj.setup_ports_using_command(no_of_ports_needed=num_ports,
                                                    flow_type=flow_type, flow_direction=flow_direction)
    fun_test.test_assert(result['result'], "Configure setup")

    port_obj_list = []
    port_1 = result['port_list'][0]
    port_obj_list.append(port_1)
    port_2 = result['port_list'][1]
    port_obj_list.append(port_2)

    gen_objs = []
    streamblock_handles_list = []
    port_obj = port_1
    gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                     duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                     advanced_interleaving=True)

    gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_obj)
    gen_objs.append(gen_obj_1)
    config_obj = template_obj.configure_generator_config(port_handle=port_obj,
                                                         generator_config_obj=gen_config_obj)
    fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_obj)

    create_streamblock_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_PERCENT_LINE_RATE,
                                       fill_type=StreamBlock.FILL_TYPE_PRBS,
                                       frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED, load=load,
                                       fixed_frame_length=66)
    streamblock_1 = template_obj.configure_stream_block(create_streamblock_1,
                                                        port_handle=port_obj)
    fun_test.test_assert(streamblock_1, "Creating streamblock on port %s" % port_obj)

    # Configure mac and ip on the stream
    ethernet = Ethernet2Header(destination_mac=destination_mac1)
    frame_stack = template_obj.stc_manager.configure_frame_stack(
        stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ethernet,
        delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
    fun_test.test_assert(frame_stack,
                         "Added ethernet header to stream %s" % create_streamblock_1._spirent_handle)

    ipv4 = Ipv4Header(source_address=src_ip, destination_address=dest_ip, protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
    frame_stack = template_obj.stc_manager.configure_frame_stack(
        stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ipv4)
    fun_test.test_assert(frame_stack,
                         "Added ipv4 header to stream %s" % create_streamblock_1._spirent_handle)
    streamblock_handles_list.append(create_streamblock_1._spirent_handle)

    udp = UDP()
    add_udp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                             create_streamblock_1._spirent_handle,
                                                             header_obj=udp)
    fun_test.test_assert(add_udp, "Adding udp header to frame")

    range_obj = RangeModifier(recycle_count=512, step_value=1, data=10)
    modify_attribute = 'sourcePort'
    create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                     streamblock_obj=create_streamblock_1,
                                                                     header_obj=udp,
                                                                     header_attribute=modify_attribute)
    fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                         % (udp._spirent_handle, modify_attribute))

    range_obj_1 = RangeModifier(recycle_count=32768, step_value=1, data=10000)
    modify_attribute = 'destPort'
    create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj_1,
                                                                     streamblock_obj=create_streamblock_1,
                                                                     header_obj=udp,
                                                                     header_attribute=modify_attribute)
    fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                         % (udp._spirent_handle, modify_attribute))

    # Subscribe to results
    project = template_obj.stc_manager.get_project_handle()
    subscribe_results = template_obj.subscribe_to_all_results(parent=project)
    del subscribe_results['result']

    start = template_obj.enable_generator_configs(generator_configs=gen_objs)
    fun_test.test_assert(start, "Starting generators config")

    time_delta = 10
    time_interval = run_time / time_delta
    current_time = 0
    keep_running = True

    while keep_running:
        fun_test.sleep("Letting traffic run", seconds=time_interval)
        current_time += time_delta

        # Fetch Rx L1 rate
        output = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                    streamblock_handle_list=streamblock_handles_list,
                                                                    rx_summary_result=True, tx_stream_result=True)

        # rx_summary_subscribe_handle = subscribe_results['rx_summary_subscribe'],
        # tx_summary_subscribe_handle = subscribe_results['tx_subscribe']

        # for port_obj in port_obj_list:
        #     tx_port = port_1
        #     rx_port = port_2
        #     if port_obj == port_2:
        #         tx_port = port_1
        #         rx_port = port_2
        #     tx_port_result = template_obj.stc_manager.get_generator_port_results(
        #         port_handle=tx_port, subscribe_handle=tx_summary_subscribe_handle)
        #     rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
        #         port_handle=rx_port, subscribe_handle=rx_summary_subscribe_handle)
        #
        #     tx_l1_bit_rate_in_kbps = template_obj._convert_bps_to_kbps(
        #         count_in_bps=int(tx_port_result['L1BitRate']))
        #     rx_l1_bit_rate_in_kbps = template_obj._convert_bps_to_kbps(
        #         count_in_bps=int(rx_port_result['L1BitRate']))
        #     fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d kbps and Rx --> %d kbps " % (
        #         port_obj, tx_l1_bit_rate_in_kbps, rx_l1_bit_rate_in_kbps))

        for current_streamblock in streamblock_handles_list:
            rx_l1_bps = int(output[current_streamblock]['rx_summary_result']['L1BitRate'])
            rx_l1_rate = rx_l1_bps / float(1000000000)

            tx_l1_bps = int(output[current_streamblock]['tx_stream_result']['L1BitRate'])
            tx_l1_rate = tx_l1_bps / float(1000000000)

            fun_test.log("Rx and Tx rate for %s is %s and %s" % (current_streamblock, rx_l1_rate, tx_l1_rate))

        if current_time == run_time:
            keep_running = False

    stop = template_obj.disable_generator_configs(generator_configs=gen_objs)


if __name__ == "__main__":
    come_handle = get_come_handle("fs-65")
    #run_time = input("Run time :")
    #load = input("Load :")
    run_time = 120
    initiate = False
    f1 = 0
    load = 99.99
    job_inputs = fun_test.get_job_inputs()
    if job_inputs:
        if "run_time" in job_inputs:
            run_time = job_inputs["run_time"]
        if "initiate" in job_inputs:
            initiate = job_inputs["initiate"]
        if "f1" in job_inputs:
            f1 = job_inputs["f1"]
        if "load" in job_inputs:
            load = job_inputs["load"]
    run_nu_firewall(come_handle, run_time, load, initiate, f1)