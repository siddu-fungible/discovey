from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from prettytable import PrettyTable
# Currently Nu Config manager is in scripts dir we will move it later to proper place
from scripts.networking.nu_config_manager import NuConfigManager
from fun_global import PerfUnit
from web.fun_test.analytics_models_helper import ModelHelper


class SpirentEthernetTrafficTemplate(SpirentTrafficGeneratorTemplate):
    ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP = 1
    ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP = 2
    ETH_IPV4_UDP_VXLAN_ETH_IPV6_TCP = 3
    ETH_IPV4_UDP_VXLAN_ETH_IPV6_UDP = 4
    ETH_IPV6_UDP_VXLAN_ETH_IPV4_TCP = 5
    ETH_IPV6_UDP_VXLAN_ETH_IPV4_UDP = 6
    ETH_IPV6_UDP_VXLAN_ETH_IPV6_TCP = 7
    ETH_IPV6_UDP_VXLAN_ETH_IPV6_UDP = 8
    MPLS_ETH_IPV4_UDP_CUST_IPV4_TCP = 9
    MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP = 10
    JUNIPER_PERFORMANCE_MODEL_NAME = "TeraMarkJuniperNetworkingPerformance"

    def __init__(self, session_name, spirent_config, chassis_type=SpirentManager.VIRTUAL_CHASSIS_TYPE):
        SpirentTrafficGeneratorTemplate.__init__(self, spirent_config=spirent_config, chassis_type=chassis_type)
        self.session_name = session_name
        self.stc_connected = False
        self.nu_config_obj = NuConfigManager()

    def setup(self, no_of_ports_needed, flow_type=NuConfigManager.TRANSIT_FLOW_TYPE,
              flow_direction=NuConfigManager.FLOW_DIRECTION_NU_NU, ports_map={}, imix_distribution=False):
        result = {"result": False, 'port_list': [], 'interface_obj_list': []}

        project_handle = self.stc_manager.create_project(project_name=self.session_name)
        fun_test.test_assert(project_handle, "Create %s Project" % self.session_name)

        if imix_distribution:
            out = self.stc_manager.create_frame_length_distribution()
        if not self.stc_connected:
            fun_test.test_assert(expression=self.stc_manager.health(session_name=self.session_name)['result'],
                                 message="Health of Spirent Test Center")
            self.stc_connected = True

        try:
            if not ports_map:
                ports_map = self.nu_config_obj.get_spirent_dut_port_mapper(no_of_ports_needed=no_of_ports_needed,
                                                                      flow_type=flow_type,
                                                                      flow_direction=flow_direction)
            else:
                fun_test.simple_assert(int(no_of_ports_needed) == len(ports_map),
                                       message="Number of ports needed is %s and provided in ports_map is %s "
                                               % (no_of_ports_needed, len(ports_map)))
            for key, val in ports_map.iteritems():
                fun_test.log("Using %s -----> %s" % (key, val))
                port_handle = self.stc_manager.create_port(location=val)
                fun_test.test_assert(port_handle, "Create Port: %s" % val)
                result['port_list'].append(port_handle)

                interface_obj = self.create_physical_interface(port_handle=port_handle)
                # self.stc_manager.stc.config(child="")
                fun_test.simple_assert(interface_obj, "Create Physical Interface: %s" % str(interface_obj))
                result['interface_obj_list'].append(interface_obj)

            self.stc_manager.apply_configuration()

            # Attach ports method take care of applying configuration
            fun_test.test_assert(self.stc_manager.attach_ports(port_list=result['port_list']), message="Attach Ports")

            # fec_disable = self._ensure_fec_disabled(port_list=result['port_list'])
            # fun_test.test_assert(fec_disable, "Ensure FEC disable on interfaces")

            # Update Spirent handle for each interface
            count = 0
            for port_handle in result['port_list']:
                handle = self.stc_manager.get_activephy_targets_under_port(port_handle=port_handle)
                fun_test.log("Chassis Type: %s Link Status: %s Interface: %s Port: %s" % (
                    self.chassis_type, self.stc_manager.get_interface_link_status(handle=handle), handle, port_handle))
                fun_test.log("Chassis Type: %s Auto Negotiation Status: %s Interface: %s Port: %s" % (
                    self.chassis_type, self.stc_manager.get_auto_negotiation_status(handle=handle), handle,
                    port_handle))
                fun_test.log("Chassis Type: %s FEC Status: %s Interface: %s Port: %s" % (
                    self.chassis_type, self.stc_manager.get_fec_status(handle=handle), handle, port_handle))
                result['interface_obj_list'][count].spirent_handle = handle
                count += 1
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def cleanup(self):
        try:
            if self.spirent_config['connect_via_lab_server']:
                self.stc_manager.disconnect_session()
                self.stc_manager.disconnect_lab_server()
            # self.stc_manager.disconnect_chassis()
        except Exception as ex:
            fun_test.critical(str(ex))
        return True

    def create_physical_interface(self, port_handle):
        result = None
        try:
            interface_obj = None
            fec_obj = None
            if self.chassis_type == SpirentManager.PHYSICAL_CHASSIS_TYPE:
                job_inputs = fun_test.get_job_inputs()
                fun_test.simple_assert(job_inputs, "Job inputs are not found")
                if job_inputs['speed'] == SpirentManager.SPEED_100G:
                    interface_obj = Ethernet100GigFiberInterface(line_speed=Ethernet100GigFiberInterface.SPEED_100G,
                                                                 auto_negotiation=False,
                                                                 forward_error_correction=False)
                elif job_inputs['speed'] == SpirentManager.SPEED_25G:
                    interface_obj = Ethernet25GigFiberInterface(auto_negotiation=False,
                                                                line_speed=Ethernet25GigFiberInterface.SPEED_25G)
                    fec_obj = FecModeObject(fectype="CLAUSE_108_RS")

                attributes = interface_obj.get_attributes_dict()
                spirent_handle = self.stc_manager.create_physical_interface(port_handle=port_handle,
                                                                            interface_type=str(interface_obj),
                                                                            attributes=attributes)

                fun_test.test_assert(spirent_handle, "Create Physical Interface: %s" % spirent_handle)
                interface_obj.spirent_handle = spirent_handle

                if job_inputs['speed'] == SpirentManager.SPEED_25G:
                    fec_attributes = fec_obj.get_attributes_dict()
                    spirent_handle = self.stc_manager.applyfec(port_handle=port_handle, fec_obj=str(fec_obj),
                                                               attributes=fec_attributes)
                    fun_test.test_assert(spirent_handle, "Apply FEC settings: %s" % spirent_handle)
                    fec_obj.spirent_handle = spirent_handle

            else:
                interface_obj = EthernetCopperInterface()
                attributes = interface_obj.get_attributes_dict()
                spirent_handle = self.stc_manager.create_physical_interface(port_handle=port_handle,
                                                                            interface_type=str(interface_obj),
                                                                            attributes=attributes)
                fun_test.test_assert(spirent_handle, "Create Physical Interface: %s" % spirent_handle)
                interface_obj.spirent_handle = spirent_handle
            result = interface_obj
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _ensure_fec_disabled(self, port_list):
        result = False
        try:
            if self.chassis_type == SpirentManager.PHYSICAL_CHASSIS_TYPE:
                for port_handle in port_list:
                    handle = self.stc_manager.get_activephy_targets_under_port(port_handle=port_handle)
                    fec_status = self.stc_manager.get_fec_status(handle=handle)
                    if fec_status == 'true':
                        fun_test.log("Disabling FEC on %s" % handle)
                        status_updated = self.stc_manager.update_physical_interface(
                            interface_handle=handle, update_attributes={"ForwardErrorCorrection": False})
                        fun_test.simple_assert(status_updated, "Ensure Interface config updated")
                        handle = self.stc_manager.get_activephy_targets_under_port(port_handle=port_handle)
                        fec_status = self.stc_manager.get_fec_status(handle=handle)
                        fun_test.simple_assert(fec_status == 'false', "Ensure FEC disable for %s under %s" % (
                            handle, port_handle))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_physical_interface(self, interface_obj):
        result = False
        try:
            attributes = interface_obj.get_attributes_dict()
            result = self.stc_manager.update_physical_interface(interface_handle=interface_obj.spirent_handle,
                                                                update_attributes=attributes)
            fun_test.test_assert(result, "Update %s physical interface" % interface_obj.spirent_handle)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def change_ports_mtu(self, interface_obj_list, mtu_value):
        result = False
        try:
            for interface_obj in interface_obj_list:
                checkpoint = "Change MTU for interface %s to %d" % (str(interface_obj), mtu_value)
                interface_obj.Mtu = mtu_value
                mtu_update_result = self.configure_physical_interface(interface_obj=interface_obj)
                fun_test.simple_assert(mtu_update_result, checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_stream_block(self, stream_block_obj, port_handle=None, update=False, frame_stack_obj_list=[],
                               ip_header_version=4):
        result = {}
        try:
            attributes = stream_block_obj.get_attributes_dict()
            if update:
                frame_config = self.stc_manager.get_streamblock_frame_config(stream_block_obj._spirent_handle)
                if frame_config:
                    stream_block_obj.FrameConfig = frame_config
                    attributes['FrameConfig'] = frame_config
                result = self.stc_manager.update_stream_block(stream_block_handle=stream_block_obj._spirent_handle,
                                                              update_attributes=attributes)
                fun_test.test_assert(result, message="Update Stream Block %s" % str(stream_block_obj._spirent_handle))

                if frame_stack_obj_list:
                    for obj in frame_stack_obj_list:
                        frame_update = self.stc_manager.configure_frame_stack(
                            stream_block_handle=stream_block_obj._spirent_handle, header_obj=obj, update=update)
                        fun_test.simple_assert(frame_update, message="Update frame_stack %s" % obj._spirent_handle)
            else:
                if not port_handle:
                    raise Exception("Please provide port handle under which stream to be created")
                spirent_handle = self.stc_manager.create_stream_block(port=port_handle, attributes=attributes)
                fun_test.test_assert(spirent_handle, message="Create Stream Block: %s" % spirent_handle)
                stream_block_obj._spirent_handle = spirent_handle  # Setting Spirent handle to our object
                fun_test.simple_assert(self.stc_manager.apply_configuration(),
                                       "Apply Configuration after creating %s" % stream_block_obj._spirent_handle)
                ethernet_header_obj = Ethernet2Header()
                if ip_header_version == 4:
                    ipv4_header_obj = Ipv4Header()
                    result["status"] = True
                    result["ethernet_header_obj"] = ethernet_header_obj
                    result["ip_header_obj"] = ipv4_header_obj
                else:
                    ipv6_header_obj = Ipv6Header()
                    header = self.stc_manager.stc.get(spirent_handle, "children").split()[1]
                    fun_test.debug("Default IPv4 Handle: %s" % header)

                    fun_test.simple_assert(self.stc_manager.delete_handle(handle=header),
                                           "Delete Default IPv4 header: %s" % header)

                    v6_header_created = self.stc_manager.configure_frame_stack(stream_block_handle=
                                                                               stream_block_obj._spirent_handle,
                                                                               header_obj=ipv6_header_obj)
                    fun_test.simple_assert(v6_header_created, "Append IPv6 header under %s" %
                                           stream_block_obj._spirent_handle)
                    result["status"] = True
                    result["ethernet_header_obj"] = ethernet_header_obj
                    result["ip_header_obj"] = ipv6_header_obj
        except Exception as ex:
            result = False
            fun_test.critical(str(ex))
        return result

    def setup_existing_tcc_configuration(self, config_file_path, configure_ports=False, port_list=[],
                                         deactivate_streams=True):
        result = False
        try:
            fun_test.test_assert(expression=self.stc_manager.health(session_name=self.session_name)['result'],
                                 message="Connect to Lab Server")
            tcc_config = self.stc_manager.load_tcc_configuration(tcc_config_file_path=config_file_path)
            fun_test.test_assert(expression=tcc_config, message="Load TCC configuration")

            self.stc_manager.get_project_handle()
            fun_test.add_checkpoint(checkpoint="Get Project")

            if configure_ports:
                if not port_list:
                    raise FunTestLibException("Please Provide Port list require to configure")
                fun_test.test_assert(expression=self.configure_ports(port_list), message="Configure Ports")

            checkpoint = "Attach ports and apply configuration"
            fun_test.test_assert(expression=self.stc_manager.attach_ports(), message=checkpoint)

            if deactivate_streams:
                checkpoint = "Deactivate all streams from all ports"
                all_port_streams = self.get_streams_all_ports()
                for key in all_port_streams.keys():
                    if not all_port_streams[key]:
                        continue
                    deactivate_success = self.deactivate_stream_blocks(stream_obj_list=all_port_streams[key])
                    fun_test.test_assert(deactivate_success, message="Deactivate Streams %s " % all_port_streams[key],
                                         ignore_on_success=True)
                fun_test.add_checkpoint(checkpoint)

            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_ports(self, port_list):
        result = False
        try:
            ports = self.stc_manager.get_port_list()
            for port in ports:
                if port in port_list:
                    checkpoint = "Update %s Location" % port
                    result = self.stc_manager.configure_port_location(port_handle=port, chassis_type=self.chassis_type,
                                                                      slot_no=self.stc_manager.config['free_slots'][0],
                                                                      port_no=port)

                    fun_test.test_assert(result, message=checkpoint, ignore_on_success=True)

        except Exception as ex:
            result = False
            fun_test.critical(str(ex))
        return result

    def ensure_stream_exists_in_config(self, stream_block_name):
        stream_obj = None
        stream_info = {}
        stream_handle = None
        stream_found = False
        try:
            ports = self.stc_manager.get_port_list()
            for port in ports:
                port_children = self.stc_manager.get_object_children(handle=port)
                for child in port_children:
                    if child.startswith('streamblock'):
                        stream_parameters = self.stc_manager.get_stream_parameters(stream_block_handle=child)
                        if re.search(stream_block_name, stream_parameters['Name']):
                            stream_info = stream_parameters
                            stream_handle = child
                            stream_found = True
                            break
                if stream_found:
                    break
            if stream_found:
                stream_obj = StreamBlock()
                stream_info = self._intersect_writable_attributes(writable_attributes=stream_obj.get_attributes_dict(),
                                                                  all_attributes=stream_info)
                stream_obj.update_stream_block_object(**stream_info)
                StreamBlock._spirent_handle = stream_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return stream_obj

    def _intersect_writable_attributes(self, writable_attributes, all_attributes):
        intersect = {}
        for key in writable_attributes.keys():
            if key in all_attributes:
                intersect[key] = all_attributes[key]
        return intersect

    def get_streams_by_port(self, port_handle):
        result = []
        try:
            children = self.stc_manager.get_object_children(handle=port_handle)
            for child in children:
                if child.startswith('streamblock'):
                    result.append(child)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_streams_all_ports(self):
        result = {}
        try:
            ports = self.stc_manager.get_port_list()
            for port in ports:
                port_name = self.stc_manager.get_port_details(port=port)['Name']
                streams = self.get_streams_by_port(port_handle=port)
                result[port_name] = streams
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_generator_config(self, port_handle, generator_config_obj, update=False):
        result = False
        try:
            attributes = generator_config_obj.get_attributes_dict()
            if update:
                result = self.stc_manager.update_handle_config(config_handle=generator_config_obj.spirent_handle,
                                                               attributes=attributes)
                fun_test.test_assert(result, message="Update Generator Config: %s" % generator_config_obj.spirent_handle)
            else:
                fun_test.log("Getting new generator in port: %s with default values" % port_handle)
                generator = self.stc_manager.get_generator(port_handle=port_handle)
                fun_test.simple_assert(generator, "Get Generator")
                generator_config_handle = self.stc_manager.get_generator_config(generator_handle=generator)
                fun_test.test_assert(generator_config_handle, "Get Generator Config for %s " % generator)
                self.stc_manager.stc.config(generator_config_handle, **attributes)
                generator_config_obj.spirent_handle = generator_config_handle
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_analyzer_config(self, port_handle, analyzer_config_obj, update=False):
        result = False
        try:
            attributes = analyzer_config_obj.get_attributes_dict()
            if update:
                result = self.stc_manager.update_handle_config(config_handle=analyzer_config_obj.spirent_handle,
                                                               attributes=attributes)
                fun_test.test_assert(result, message="Update Generator Config: %s" % analyzer_config_obj.spirent_handle)
            else:
                fun_test.log("Getting new analyzer in port: %s with default values" % port_handle)
                analyzer = self.stc_manager.get_analyzer(port_handle=port_handle)
                fun_test.simple_assert(analyzer, "Get Analyzer")
                analyzer_config_handle = self.stc_manager.get_analyzer_config(analyzer_handle=analyzer)
                fun_test.test_assert(analyzer_config_handle, "Get Analyzer Config for %s " % analyzer)
                self.stc_manager.stc.config(analyzer_config_handle, **attributes)
                analyzer_config_obj.spirent_handle = analyzer
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def activate_stream_blocks(self, stream_obj_list=None, stream_handles=False):
        result = False
        try:
            stream_block_handles = []
            if not stream_obj_list:
                project = self.stc_manager.get_project_handle()
                ports = self.stc_manager.get_object_children(project, child_type="children-port")
                for port in ports:
                    streamblocks = self.stc_manager.get_object_children(port, "children-streamblock")
                    if streamblocks:
                        for stream_obj in streamblocks:
                            stream_block_handles.append(stream_obj)
            else:
                for stream_obj in stream_obj_list:
                    if stream_handles:
                        stream_block_handles.append(stream_obj)
                    else:
                        stream_block_handles.append(stream_obj._spirent_handle)

            result = self.stc_manager.run_stream_block_active_command(stream_block_handles=stream_block_handles)
            fun_test.test_assert(result, message="Activate Stream Blocks: %s" % stream_block_handles)
            self.stc_manager.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def deactivate_stream_blocks(self, stream_obj_list=None):
        result = False
        try:
            stream_block_handles = []
            if not stream_obj_list:
                project = self.stc_manager.get_project_handle()
                ports = self.stc_manager.get_object_children(project, child_type="children-port")
                for port in ports:
                    streamblocks = self.stc_manager.get_object_children(port, "children-streamblock")
                    if streamblocks:
                        for stream_obj in streamblocks:
                            stream_block_handles.append(stream_obj)
            else:
                for stream_obj in stream_obj_list:
                    stream_block_handles.append(stream_obj._spirent_handle)

            result = self.stc_manager.run_stream_block_active_command(stream_block_handles=stream_block_handles,
                                                                      activate=False)
            fun_test.test_assert(result, message="Deactivate Stream Blocks: %s" % stream_block_handles)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def enable_generator_configs(self, generator_configs):
        result = False
        try:
            result = self.stc_manager.start_generator_command(generator_handles=generator_configs)
            fun_test.test_assert(result, message="Start Generator Configs: %s" % generator_configs)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def disable_generator_configs(self, generator_configs):
        result = False
        try:
            result = self.stc_manager.stop_generator_command(generator_handles=generator_configs)
            fun_test.test_assert(result, message="Stop Generator Configs: %s" % generator_configs)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def subscribe_tx_results(self, parent, config_type="StreamBlock", result_type="TxStreamBlockResults",
                             view_attribute_list=None, change_mode=False,
                             result_view_mode=SpirentManager.RESULT_VIEW_MODE_JITTER,
                             timed_refresh_result_view_mode=SpirentManager.TIMED_REFRESH_RESULT_VIEW_MODE):
        result_handle = None
        try:
            fun_test.log("Subscribing to %s for %s config to get %s result" % (parent, config_type, result_type))
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list,
                                                           change_mode=change_mode,
                                                           result_view_mode=result_view_mode,
                                                           timed_refresh_result_view_mode=timed_refresh_result_view_mode)
            fun_test.simple_assert(op_handle, "Getting tx subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_rx_results(self, parent, config_type="StreamBlock", result_type="RxStreamBlockResults",
                             view_attribute_list=None, change_mode=False,
                             result_view_mode=SpirentManager.RESULT_VIEW_MODE_JITTER,
                             timed_refresh_result_view_mode=SpirentManager.TIMED_REFRESH_RESULT_VIEW_MODE):
        result_handle = None
        try:
            fun_test.log("Subscribing to %s for %s config to get %s result" % (parent, config_type, result_type))
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list,
                                                           change_mode=change_mode,
                                                           result_view_mode=result_view_mode,
                                                           timed_refresh_result_view_mode=timed_refresh_result_view_mode)
            fun_test.simple_assert(op_handle, "Getting rx subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_analyzer_results(self,  parent, config_type="Analyzer", result_type="AnalyzerPortResults",
                                   view_attribute_list=None):
        result_handle = None
        try:
            fun_test.log("Subscribing to port analyzer results on port %s" % parent)
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list)
            fun_test.simple_assert(op_handle, "Getting analyzer subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_diff_serv_results(self,  parent, result_parent, config_type="Analyzer", result_type="DiffServResults",
                                    view_attribute_list=None):
        result_handle = None
        try:
            fun_test.log("Subscribing to diff serv results on %s" % parent)
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list, result_parent=result_parent)
            fun_test.simple_assert(op_handle, "Getting diffServ subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_pfc_results(self,  parent, config_type="Port", result_type="PfcResults",
                              view_attribute_list=None):
        result_handle = None
        try:
            fun_test.log("Subscribing to pfc results on %s" % parent)
            pass
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list)
            fun_test.simple_assert(op_handle, "Getting pfc subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_filtered_stream_results(self, parent, result_parent, config_type="Analyzer", result_type="FilteredStreamResults"):
        result_handle = None
        try:
            analyzer_handle = self.stc_manager.stc.get(result_parent, "children-Analyzer")

            bit_analyzer = self.stc_manager.stc.create("Analyzer16BitFilter", under=analyzer_handle)

            # Track Tos bits
            self.stc_manager.stc.config(bit_analyzer, FilterName="HEX", Offset=14, Mask="0x00FF")
            self.stc_manager.stc.apply()

            fun_test.log("Subscribing to filtered stream results on %s" % parent)
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           result_parent=result_parent)
            fun_test.simple_assert(op_handle, "Getting filtered stream subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle


    def subscribe_generator_results(self,  parent, config_type="Generator", result_type="GeneratorPortResults",
                                    view_attribute_list=None):
        result_handle = None
        try:
            fun_test.log("Subscribing to port generator results on port %s" % parent)
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list)
            fun_test.simple_assert(op_handle, "Getting generator subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def create_result_query(self, tx_subscribe_handle, parent, config_class_id="StreamBlock",
                            result_class_id="RxStreamBlockResults"):
        result = False
        try:
            query_handle = self.stc_manager.create_result_query(subscribe_handle=tx_subscribe_handle,
                                                                result_root_list=parent,
                                                                config_class_id=config_class_id,
                                                                result_class_id=result_class_id)
            fun_test.simple_assert(query_handle, "Getting result query handle")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def clear_subscribed_results(self, subscribe_handle_list):
        result = False
        try:
            for handle in subscribe_handle_list:
                if type(handle) == bool:
                    continue
                output = self.stc_manager.clear_results_view_command(result_dataset=handle)
                fun_test.simple_assert(output, message="Clear results for handle %s" % handle)
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def compare_result_attribute(self, tx_results, rx_results, attribute_name="FrameCount"):
        result = False
        try:
            fun_test.simple_assert(expression=attribute_name in tx_results.keys(),
                                   message="Attribute %s not found in tx_results" % attribute_name)
            fun_test.simple_assert(expression=attribute_name in rx_results.keys(),
                                   message="Attribute %s not found in rx_results" % attribute_name)
            fun_test.log("Atrribute %s has a value %s in tx_results" % (attribute_name, tx_results[attribute_name]))
            fun_test.log("Atrribute %s has a value %s in rx_results" % (attribute_name, rx_results[attribute_name]))
            if tx_results[attribute_name] == rx_results[attribute_name]:
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def check_non_zero_error_count(self, rx_results):
        result = {'result': False}
        try:
            error_counters_list = ["FcsErrorFrameCount", "Ipv4ChecksumErrorCount", "PrbsErrorFrameCount",
                                   "TcpChecksumErrorCount", "UdpChecksumErrorCount", "DroppedFrameCount",
                                   "DuplicateFrameCount", "OutSeqFrameCount", "LateFrameCount", "ReorderedFrameCount"]
            for counter in error_counters_list:
                if counter in rx_results:
                    if not rx_results[counter] == '0':
                        result[counter] = rx_results[counter]
                        fun_test.log("Error counter seen for %s with value %s" % (counter, rx_results[counter]))
            if len(result) == 1:
                result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def delete_streamblocks(self, streamblock_handle_list=None, stream_obj_list=None):
        result = False
        try:
            handles = []
            if stream_obj_list:
                for stream_obj in stream_obj_list:
                    handles.append(stream_obj.spirent_handle)
            elif streamblock_handle_list:
                handles = streamblock_handle_list
            else:
                raise FunTestLibException("Please provide either streamblock handle list or stream block obj list")
            fun_test.debug("Deleting list of objects %s" % handles)
            result = self.stc_manager.delete_objects(handles)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def subscribe_to_all_results(self, parent, diff_serv=False, pfc=False, filtered_stream=False, port=None):
        result = {'result': False}
        try:
            fun_test.debug("Subscribing to tx results")
            tx_subscribe = self.subscribe_tx_results(parent=parent)
            fun_test.simple_assert(tx_subscribe, "Check tx subscribed")
            result['tx_subscribe'] = tx_subscribe

            fun_test.debug("Subscribing to tx stream results")
            tx_stream_subscribe = self.subscribe_tx_results(parent=parent, result_type="TxStreamResults")
            fun_test.simple_assert(tx_stream_subscribe, "Check tx summary subscribe")
            result['tx_stream_subscribe'] = tx_stream_subscribe

            fun_test.debug("Subscribing to rx results")
            rx_subscribe = self.subscribe_rx_results(parent=parent)
            fun_test.simple_assert(rx_subscribe, "Check rx subscribed")
            result['rx_subscribe'] = rx_subscribe

            fun_test.debug("Subscribing to rx summary results")
            rx_summary_subscribe = self.subscribe_rx_results(parent=parent, result_type="RxStreamSummaryResults")
            fun_test.simple_assert(rx_summary_subscribe, "Check rx summary subscribe")
            result['rx_summary_subscribe'] = rx_summary_subscribe

            fun_test.debug("Subscribing to generator results")
            generator_subscribe = self.subscribe_generator_results(parent=parent)
            fun_test.simple_assert(generator_subscribe, "Check generator subscribed")
            result['generator_subscribe'] = generator_subscribe

            fun_test.debug("Subscribing to analyzer results")
            analyzer_subscribe = self.subscribe_analyzer_results(parent=parent)
            fun_test.simple_assert(analyzer_subscribe, "Check analyzer subscribed")
            result['analyzer_subscribe'] = analyzer_subscribe

            if diff_serv:
                fun_test.simple_assert(port, "Port handle must be provided for diffserv results")
                fun_test.debug("Subscribing to diff serv results")
                diff_serv_subscribe = self.subscribe_diff_serv_results(parent=parent, result_parent=port, view_attribute_list=["qos", "Ipv4FrameCount"])
                fun_test.simple_assert(diff_serv_subscribe, "Check diff serv subscribe")
                result['diff_serv_subscribe'] = diff_serv_subscribe

            if pfc:
                fun_test.debug("Subscribing to pfc results")
                pfc_subscribe = self.subscribe_pfc_results(parent=parent)
                fun_test.simple_assert(pfc_subscribe, "Check pfc subscribe")
                result['pfc_subscribe'] = pfc_subscribe

            if filtered_stream:
                fun_test.simple_assert(port, "Port handle must be provided for filtered stream results")
                fun_test.debug("Subscribing to filtered stream results")
                filter_subscribe =self.subscribe_filtered_stream_results(parent=parent, result_parent=port)
                fun_test.simple_assert(filter_subscribe, "Check filter subscribe")
                result['filtered_stream_subscribe'] = filter_subscribe

            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def unsubscribe_to_all_results(self, subscribe_dict):
        result = False
        try:
            checkpoint = "Unsubscribe all results"
            fun_test.debug(checkpoint)
            for key in subscribe_dict:
                if key != 'result':
                    fun_test.simple_assert(self.stc_manager.unsubscribe_results(result_handle=subscribe_dict[key]),
                                           checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _manipulate_rate_counters(self, tx_rate_count, rx_rate_count, tolerance_count=5):
        if rx_rate_count == 0:
            return rx_rate_count
        pps_count_difference = tx_rate_count - rx_rate_count
        if pps_count_difference < tolerance_count:
            rx_rate_count += pps_count_difference
        return rx_rate_count

    def _convert_bps_to_mbps(self, count_in_bps):
        count_in_mbps = count_in_bps / 1000000
        return int(count_in_mbps)

    def _convert_bps_to_kbps(self, count_in_bps):
        count_in_kbps = count_in_bps / 1000
        return int(count_in_kbps)

    def validate_traffic_rate_results(self, rx_summary_subscribe_handle, tx_summary_subscribe_handle, stream_objects,
                                      wait_before_fetching_results=True, validate_throughput=True, tx_port=None,
                                      rx_port=None):
        result = {'result': False, 'pps_count': {}, 'throughput_count': {}}
        try:
            if wait_before_fetching_results:
                fun_test.sleep("Waiting for traffic to reach full throughput", seconds=25)

            for stream_obj in stream_objects:
                if stream_obj.FixedFrameLength == 64:
                    if not tx_port and not rx_port:
                        raise Exception("Please provide Spirent Tx Port and Rx Port handles")

                    checkpoint = "Fetch Tx Port Results for %s" % tx_port
                    tx_port_result = self.stc_manager.get_generator_port_results(
                        port_handle=tx_port, subscribe_handle=tx_summary_subscribe_handle)
                    fun_test.simple_assert(expression=tx_port_result, message=checkpoint)
                    checkpoint = "Fetch Rx Port Results for %s" % rx_port
                    rx_port_result = self.stc_manager.get_rx_port_analyzer_results(
                        port_handle=rx_port, subscribe_handle=rx_summary_subscribe_handle)
                    fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

                    checkpoint = "Ensure Tx GeneratorFrameRate(PPS) is equal to Rx TotalFrameRate(PPS) for %d " \
                                 "Frame Size (%s)" % (stream_obj.FixedFrameLength, stream_obj.spirent_handle)
                    fun_test.log("FrameRate (PPS) Results for %s : Tx --> %d fps and Rx --> %d fps" % (
                        stream_obj.spirent_handle, int(tx_port_result['GeneratorFrameRate']),
                        int(rx_port_result['TotalFrameRate'])))
                    rx_pps_count = self._manipulate_rate_counters(tx_rate_count=int(tx_port_result['GeneratorFrameRate']),
                                                                  rx_rate_count=int(rx_port_result['TotalFrameRate']))
                    fun_test.test_assert_expected(expected=int(tx_port_result['GeneratorFrameRate']),
                                                  actual=rx_pps_count,
                                                  message=checkpoint)
                    if validate_throughput:
                        checkpoint = "Ensure Throughput Tx Rate is equal to Rx Rate for %d Frame Size (%s)" % \
                                     (stream_obj.FixedFrameLength, stream_obj.spirent_handle)
                        tx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(tx_port_result['L1BitRate']))
                        rx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(rx_port_result['L1BitRate']))
                        fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d Mbps and Rx --> %d Mbps " % (
                            stream_obj.spirent_handle, tx_l1_bit_rate_in_mbps, rx_l1_bit_rate_in_mbps))
                        rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_mbps,
                                                                     rx_rate_count=rx_l1_bit_rate_in_mbps)
                        fun_test.test_assert_expected(expected=tx_l1_bit_rate_in_mbps,
                                                      actual=rx_bit_rate,
                                                      message=checkpoint)
                    result['pps_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength):
                                               int(rx_port_result['TotalFrameRate'])}
                else:

                    checkpoint = "Fetch Tx Results for %s" % stream_obj.spirent_handle
                    tx_result = self.stc_manager.get_tx_stream_block_results(stream_block_handle=stream_obj.spirent_handle,
                                                                             subscribe_handle=tx_summary_subscribe_handle,
                                                                             summary=True, refresh=False)
                    fun_test.simple_assert(expression=tx_result, message=checkpoint)

                    checkpoint = "Fetch Rx Results for %s" % stream_obj.spirent_handle
                    rx_result = self.stc_manager.get_rx_stream_block_results(stream_block_handle=stream_obj.spirent_handle,
                                                                             subscribe_handle=rx_summary_subscribe_handle,
                                                                             summary=True, refresh=False)
                    fun_test.simple_assert(expression=rx_result, message=checkpoint)

                    checkpoint = "Ensure Tx FrameRate(PPS) is equal to Rx FrameRate(PPS) for %d Frame Size (%s)" % \
                                 (stream_obj.FixedFrameLength, stream_obj.spirent_handle)
                    fun_test.log("FrameRate (PPS) Results for %s : Tx --> %d fps and Rx --> %d fps" % (
                        stream_obj.spirent_handle, int(tx_result['FrameRate']), int(rx_result['FrameRate'])))

                    rx_pps_count = self._manipulate_rate_counters(tx_rate_count=int(tx_result['FrameRate']),
                                                                  rx_rate_count=int(rx_result['FrameRate']))
                    fun_test.test_assert_expected(expected=int(tx_result['FrameRate']),
                                                  actual=rx_pps_count,
                                                  message=checkpoint)

                    if validate_throughput:
                        checkpoint = "Ensure Throughput Tx Rate is equal to Rx Rate for %d Frame Size (%s)" % \
                                     (stream_obj.FixedFrameLength, stream_obj.spirent_handle)
                        tx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(tx_result['L1BitRate']))
                        rx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(rx_result['L1BitRate']))
                        fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d Mbps and Rx --> %d Mbps " % (
                            stream_obj.spirent_handle, tx_l1_bit_rate_in_mbps, rx_l1_bit_rate_in_mbps))

                        rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_mbps,
                                                                     rx_rate_count=rx_l1_bit_rate_in_mbps)
                        fun_test.test_assert_expected(expected=tx_l1_bit_rate_in_mbps,
                                                      actual=rx_bit_rate,
                                                      message=checkpoint)

                    result['pps_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): int(rx_result['FrameRate'])}
                if validate_throughput:
                    result['throughput_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): float(rx_bit_rate)}
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _calculate_threshold_count(self, count, tolerance_percent=10):
        return (float(count) * tolerance_percent/100) + count

    def validate_latency_results(self, rx_result, stream_obj,
                                 expected_latency_count={}, tolerance_percent=10):
        """
        :param rx_result: Spirent Result Dict
        :param stream_objects: List of stream block objects
        :param expected_latency_count: Optional dict with expected avg, min, max counters for each stream
        for e.g expected_latency_count = {frame_64': {'avg': value, 'min': value, 'max': value}}
        :param tolerance_percent: Threshold for benchmarking results Default 10 %
        :return: bool
        """
        result = {'result': False}
        try:
            frame_size = str(stream_obj.FixedFrameLength)
            if not expected_latency_count:
                # TODO: Later on we need to integrate RFC 2544 standards for benchmarking
                # If existing record not found for given frame size dump the result as it is for now
                result['frame_%s' % frame_size] = {'avg': 0, 'min': 0, 'max': 0}
            else:
                # For performance benchmarking we are comparing existing benchmarking results
                if rx_result:
                    checkpoint = "Validate Avg. latency for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency (%s) " % \
                                 (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                    expected_threshold_latency = self._calculate_threshold_count(
                        count=expected_latency_count['latency_avg'],
                        tolerance_percent=tolerance_percent)
                    fun_test.log("Expected Avg latency: %s us Frame Size: %s" % (str(expected_threshold_latency),
                                                                                 frame_size))
                    fun_test.log("Avg Latency for %s Frame Size %s B: %s us" % (stream_obj.spirent_handle,
                                                                                frame_size, str(rx_result['AvgLatency'])))
                    # fun_test.test_assert(expression=float(rx_result['AvgLatency']) <= float(expected_threshold_latency),
                    #                      message=checkpoint)

                    checkpoint = "Validate Min. latency for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency (%s) " % \
                                 (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                    expected_threshold_latency = self._calculate_threshold_count(
                        count=expected_latency_count['latency_min'],
                        tolerance_percent=tolerance_percent)
                    fun_test.log("Expected Min latency: %s us Frame Size: %s" % (str(expected_threshold_latency),
                                                                                 frame_size))
                    fun_test.log("Min Latency for %s Frame Size %s B: %s us" % (stream_obj.spirent_handle,
                                                                                frame_size, str(rx_result['MinLatency'])))
                    # fun_test.test_assert(expression=float(rx_result['MinLatency']) <= float(expected_threshold_latency),
                    #                     message=checkpoint)

                    checkpoint = "Validate Max. latency for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency (%s)" % \
                                 (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                    expected_threshold_latency = self._calculate_threshold_count(
                        count=expected_latency_count['latency_max'],
                        tolerance_percent=tolerance_percent)
                    fun_test.log("Expected Max latency: %s us Frame Size: %s" % (str(expected_threshold_latency),
                                                                                 frame_size))
                    fun_test.log("Max Latency for %s Frame Size %s B: %s us" % (stream_obj.spirent_handle,
                                                                                frame_size, str(rx_result['MaxLatency'])))
                    # fun_test.test_assert(expression=float(rx_result['MaxLatency']) <= float(expected_threshold_latency),
                    #                     message=checkpoint)
                    result['frame_%s' % frame_size] = {'avg': float(rx_result['AvgLatency']),
                                                       'min': float(rx_result['MinLatency']),
                                                       'max': float(rx_result['MaxLatency'])}
                else:
                    result['frame_%s' % frame_size] = {'avg': 0, 'min': 0, 'max': 0}
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_jitter_results(self, rx_result, stream_obj,
                                expected_jitter_count={}, tolerance_percent=10):
        """
        :param rx_result: Spirent Result Dict
        :param stream_objects: List of stream block objects
        :param expected_jitter_count: Optional dict with expected avg, min, max counters for each stream
        for e.g expected_jitter_count = {frame_64: {'avg': value, 'min': value, 'max': value}}
        :param tolerance_percent: Threshold for benchmarking results Default 10 %
        :return: bool
        """
        result = {'result': False}
        try:
            frame_size = str(stream_obj.FixedFrameLength)
            if not expected_jitter_count:
                # TODO: Later on we need to integrate RFC 2544 standards for benchmarking
                result['frame_%s' % frame_size] = {'avg': 0, 'min': 0, 'max': 0}
            else:
                # For performance benchmarking we are comparing existing benchmarking results
                if rx_result:
                    checkpoint = "Validate Avg. jitter for %s Frame Size with Load %s " \
                                 "Actual jitter <= Expected Threshold jitter (%s)" % \
                                 (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                    expected_threshold_jitter = self._calculate_threshold_count(
                        count=expected_jitter_count['jitter_avg'], tolerance_percent=tolerance_percent)
                    fun_test.log("Expected Avg jitter: %s us Frame Size: %s" % (str(expected_threshold_jitter),
                                                                                frame_size))
                    fun_test.log("Avg Jitter for %s Frame Size %s B: %s " % (stream_obj.spirent_handle,
                                                                             frame_size, str(rx_result['AvgJitter'])))
                    # fun_test.test_assert(expression=float(rx_result['AvgJitter']) <= float(expected_threshold_jitter),
                    #                     message=checkpoint)

                    checkpoint = "Validate Min. jitter for %s Frame Size with Load %s " \
                                 "Actual jitter <= Expected Threshold jitter (%s)" % \
                                 (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                    expected_threshold_jitter = self._calculate_threshold_count(
                        count=expected_jitter_count['jitter_min'], tolerance_percent=tolerance_percent)
                    fun_test.log("Expected Min jitter: %s us Frame Size: %s" % (str(expected_threshold_jitter),
                                                                                frame_size))
                    fun_test.log("Min Jitter for %s Frame Size %s B: %s " % (stream_obj.spirent_handle,
                                                                             frame_size, str(rx_result['MinJitter'])))
                    # fun_test.test_assert(expression=float(rx_result['MinJitter']) <= float(expected_threshold_jitter),
                    #                     message=checkpoint)

                    checkpoint = "Validate Max. jitter for %s Frame Size with Load %s " \
                                 "Actual jitter <= Expected Threshold jitter (%s)" % \
                                 (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                    expected_threshold_jitter = self._calculate_threshold_count(
                        count=expected_jitter_count['jitter_max'], tolerance_percent=tolerance_percent)
                    fun_test.log("Expected Max jitter: %s us Frame Size: %s" % (str(expected_threshold_jitter),
                                                                                frame_size))
                    fun_test.log("Max Jitter for %s Frame Size %s B: %s " % (stream_obj.spirent_handle,
                                                                             frame_size, str(rx_result['MaxJitter'])))
                    # fun_test.test_assert(expression=float(rx_result['MaxJitter']) <= float(expected_threshold_jitter),
                    #                     message=checkpoint)
                    result['frame_%s' % frame_size] = {'avg': float(rx_result['AvgJitter']),
                                                       'min': float(rx_result['MinJitter']),
                                                       'max': float(rx_result['MaxJitter'])}
                else:
                    result['frame_%s' % frame_size] = {'avg': 0, 'min': 0, 'max': 0}
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_performance_result(self, tx_subscribe_handle, rx_subscribe_handle, stream_objects,
                                    jitter=False, expected_performance_data=[],
                                    tx_port=None, rx_port=None,
                                    tolerance_percent=10, flow_type=None, spray_enabled=False, dut_stats_success=False):
        result = {'result': False}
        try:
            expected_performance_data.reverse()
            key = "frame_%s" % str(stream_objects[0].FixedFrameLength)
            result[key] = []
            rx_result = None
            for stream_obj in stream_objects:
                if stream_obj.FixedFrameLength == 64:
                    checkpoint = "Fetch Tx Port Results for %s" % tx_port
                    tx_port_result = self.stc_manager.get_generator_port_results(
                        port_handle=tx_port, subscribe_handle=tx_subscribe_handle)
                    fun_test.simple_assert(expression=tx_port_result, message=checkpoint)
                    checkpoint = "Fetch Rx Port Results for %s" % rx_port
                    rx_port_result = self.stc_manager.get_rx_port_analyzer_results(
                        port_handle=rx_port, subscribe_handle=rx_subscribe_handle)
                    fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

                    checkpoint = "Ensure Tx FrameCount is equal to Rx FrameCount for %d frame size (%s)" % (
                        stream_obj.FixedFrameLength, stream_obj.spirent_handle
                    )
                    fun_test.log("Frame Count Results for %d B: \n Tx Frame Count: %d \n Rx Frame Count: %d " % (
                        stream_obj.FixedFrameLength, int(tx_port_result['GeneratorFrameCount']),
                        int(rx_port_result['TotalFrameCount'])
                    ))
                    if (int(tx_port_result['GeneratorFrameCount']) != int(rx_port_result['TotalFrameCount'])) and \
                            dut_stats_success:
                        fun_test.test_assert(dut_stats_success, checkpoint)
                    else:
                        fun_test.test_assert_expected(expected=int(tx_port_result['GeneratorFrameCount']),
                                                      actual=int(rx_port_result['TotalFrameCount']),
                                                      message=checkpoint)
                else:
                    checkpoint = "Fetch Rx Results for %s" % stream_obj.spirent_handle
                    rx_result = self.stc_manager.get_rx_stream_block_results(
                        stream_block_handle=stream_obj.spirent_handle,
                        subscribe_handle=rx_subscribe_handle, summary=True)
                    fun_test.log("TX Results: %s" % rx_result)
                    fun_test.simple_assert(expression=rx_result, message=checkpoint)

                    checkpoint = "Fetch Tx Results for %s" % stream_obj.spirent_handle
                    tx_result = self.stc_manager.get_tx_stream_block_results(
                        stream_block_handle=stream_obj.spirent_handle,
                        subscribe_handle=tx_subscribe_handle)
                    fun_test.log("RX Results: %s" % tx_result)
                    fun_test.simple_assert(expression=tx_result, message=checkpoint)

                    checkpoint = "Ensure Tx FrameCount is equal to Rx FrameCount for %d frame size (%s)" % (
                        stream_obj.FixedFrameLength, stream_obj.spirent_handle
                    )
                    fun_test.log("Frame Count Results for %d B: \n Tx Frame Count: %d \n Rx Frame Count: %d " % (
                        stream_obj.FixedFrameLength, int(tx_result['FrameCount']), int(rx_result['FrameCount'])
                    ))
                    if (flow_type == NuConfigManager.FLOW_DIRECTION_FPG_HNU or flow_type == NuConfigManager.FLOW_DIRECTION_HNU_FPG) \
                            and spray_enabled:
                        fun_test.log("Reordered Frame Count: %d for %d B frame." % (
                            int(rx_result['ReorderedFrameCount']), stream_obj.FixedFrameLength))
                    else:
                        fun_test.test_assert_expected(expected=int(tx_result['FrameCount']),
                                                      actual=int(rx_result['FrameCount']),
                                                      message=checkpoint)
                if jitter:
                    expected_jitter_dict = {}
                    for record in expected_performance_data:
                        if "_name" in record:
                            continue
                        if record['frame_size'] == stream_obj.FixedFrameLength:
                            if 'flow_type' in record:
                                if flow_type == record['flow_type']:
                                    expected_jitter_dict = record
                                    break
                            else:
                                if 'jitter_avg' in record:
                                    expected_jitter_dict = record
                                    break
                    checkpoint = "Validate Jitter Counters"
                    jitter_result = self.validate_jitter_results(rx_result=rx_result,
                                                                 stream_obj=stream_obj,
                                                                 expected_jitter_count=expected_jitter_dict,
                                                                 tolerance_percent=tolerance_percent)
                    fun_test.simple_assert(expression=jitter_result['result'], message=checkpoint)
                    result[key].append(jitter_result[key])
                else:
                    expected_latency_dict = {}
                    for record in expected_performance_data:
                        if '_name' in record:
                            continue
                        if record['frame_size'] == stream_obj.FixedFrameLength:
                            if "flow_type" in record:
                                if flow_type == record['flow_type']:
                                    expected_latency_dict = record
                                    break
                            else:
                                expected_latency_dict = record
                                break

                    checkpoint = "Validate Latency Counters"
                    latency_result = self.validate_latency_results(rx_result=rx_result,
                                                                   stream_obj=stream_obj,
                                                                   expected_latency_count=expected_latency_dict,
                                                                   tolerance_percent=tolerance_percent)
                    fun_test.simple_assert(expression=latency_result['result'], message=checkpoint)
                    result[key].append(latency_result[key])

            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def display_latency_counters(self, result):
        try:
            table_data_headers = ['Frame Size', 'PPS', 'Throughput (Mbps)', 'Avg. Latency (us)', 'Min Latency (us)',
                                  'Max Latency (us)', 'Avg. Jitter (us)', 'Min Jitter (us)', 'Max Jitter (us)']
            table_data_rows = []
            for key in result:
                table_data_rows.append([key, result[key]['pps_count'], result[key]['throughput_count'],
                                        result[key]['latency_count'][0]['avg'],
                                        result[key]['latency_count'][0]['min'],
                                        result[key]['latency_count'][0]['max'],
                                        result[key]['jitter_count'][0]['avg'],
                                        result[key]['jitter_count'][0]['min'],
                                        result[key]['jitter_count'][0]['max']])
            table_data = {'headers': table_data_headers, 'rows': table_data_rows}
            fun_test.add_table(panel_header="NU Performance Latency Counters", table_name="NU --> HNU",
                               table_data=table_data)
        except Exception as ex:
            fun_test.critical(str(ex))

    def display_jitter_counters(self, result):
        try:
            fun_test.log_disable_timestamps()
            fun_test.log_section("NU Performance Jitter Counters")
            if 'throughput_count' in result:
                column_list = ['Frame Size', 'PPS', 'Throughput (Mbps)', 'Avg. Jitter (us)', 'Min Jitter (us)',
                               'Max Jitter (us)']
            else:
                column_list = ['Frame Size', 'PPS', 'Avg. Jitter (us)', 'Min Jitter (us)', 'Max Jitter (us)']
            table_obj = PrettyTable(column_list)
            for key in result:
                pps_count = result[key]['pps_count']
                throughput_count = None
                if 'Throughput' in column_list:
                    throughput_count = result[key]['throughput_count']
                if len(result[key]['jitter_count']) > 1:
                    avg_jitter1 = result[key]['jitter_count'][0]['avg']
                    avg_jitter2 = result[key]['jitter_count'][1]['avg']
                    min_jitter1 = result[key]['jitter_count'][0]['min']
                    min_jitter2 = result[key]['jitter_count'][1]['min']
                    max_jitter1 = result[key]['jitter_count'][0]['max']
                    max_jitter2 = result[key]['jitter_count'][1]['max']
                    if throughput_count:
                        table_obj.add_row([key, pps_count, throughput_count, avg_jitter1, min_jitter1, max_jitter1])
                        table_obj.add_row([key, pps_count, throughput_count, avg_jitter2, min_jitter2, max_jitter2])
                    else:
                        table_obj.add_row([key, pps_count, avg_jitter1, min_jitter1, max_jitter1])
                        table_obj.add_row([key, pps_count, avg_jitter2, min_jitter2, max_jitter2])
                else:
                    avg_jitter1 = result[key]['jitter_count'][0]['avg']
                    min_jitter1 = result[key]['jitter_count'][0]['min']
                    max_jitter1 = result[key]['jitter_count'][0]['max']
                    if throughput_count:
                        table_obj.add_row([key, pps_count, throughput_count, avg_jitter1, min_jitter1, max_jitter1])
                    else:
                        table_obj.add_row([key, pps_count, avg_jitter1, min_jitter1, max_jitter1])
            fun_test.log(str(table_obj))
            fun_test.log_enable_timestamps()
        except Exception as ex:
            fun_test.critical(str(ex))

    def configure_pause_mac_control_header(self, stream_obj, source_mac="00:10:94:00:00:02",
                                           destination_mac="01:80:C2:00:00:01", length="8808", pause_time=0,
                                           op_code="0001", preamble="55555555555555d5"):
        result = {}
        result['result'] = False
        try:
            ethernet_header_obj = MacControlHeader(destination_mac=destination_mac,
                                                               source_mac=source_mac, length=length, preamble=preamble)
            pause_header_obj = PauseMacControlHeader(op_code=op_code, pause_time=pause_time)

            fun_test.log("Removing ethernet and ip header from streamblock")
            self.stc_manager.stc.config(stream_obj.spirent_handle, FrameConfig='')

            fun_test.log("Creating Pause Mac Control Frame with Ethernet 802.3 Mac Control header")
            header_created = self.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ethernet_header_obj)
            result['ethernet8023_mac_control_header_obj'] = ethernet_header_obj
            fun_test.test_assert(header_created, "Create Ethernet 802.3 Mac Control header for %s" %
                                 stream_obj.spirent_handle)
            header_created = self.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=pause_header_obj)
            fun_test.test_assert(header_created, "Create Pause Mac Control header for %s" % stream_obj.spirent_handle)
            result['pause_mac_control_header_obj'] = pause_header_obj
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_pause_header(self, stream_obj, destination_mac, source_mac, length_type="8808", op_code="0001",
                               preamble="55555555555555d5", parameters="0000"):
        result = False
        try:
            header_obj = EthernetPauseHeader(destination_mac=destination_mac, source_mac=source_mac,
                                             length_type=length_type, op_code=op_code, preamble=preamble,
                                             parameters=parameters)
            fun_test.log("Creating Ethernet Pause Frame ")
            result = self.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                            header_obj=header_obj)
            fun_test.test_assert(result, "Create Ethernet Pause Frame for %s" % stream_obj.spirent_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_priority_flow_control_header(self, stream_obj, destination_mac="01:80:c2:00:00:01",
                                               source_mac="00:10:94:00:00:02", length="8808",
                                               preamble="55555555555555d5", op_code="0101", time0="", time1="",
                                               time2="", time3="", time4="", time5="", time6="", time7="",
                                               class_enable_vector=False, ls_octet="00000000", ms_octet="00000000",
                                               reserved='', update=False):
        result = {}
        result['result'] = False
        try:
            ethernet_header_obj = MacControlHeader(destination_mac=destination_mac,
                                                               source_mac=source_mac, length=length, preamble=preamble)
            pfc_header_obj = PriorityFlowControlHeader(op_code=op_code, time0=time0, time1=time1, time2=time2,
                                                       time3=time3, time4=time4, time5=time5, time6=time6, time7=time7,
                                                       reserved=reserved)
            fun_test.log("Removing ethernet and ip header from streamblock")
            self.stc_manager.stc.config(stream_obj.spirent_handle, FrameConfig='')
            #self.stc_manager.apply_configuration()
            fun_test.log("Creating Priority Flow Control Frame with Mac Control header")
            header_created = self.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ethernet_header_obj)
            result['ethernet8023_mac_control_header_obj'] = ethernet_header_obj
            fun_test.test_assert(header_created, "Create Mac Control header for %s" %
                                 stream_obj.spirent_handle)
            header_created = self.stc_manager.configure_pfc_header(
                stream_block_handle=stream_obj.spirent_handle,
                header_obj=pfc_header_obj, class_enable_vector=class_enable_vector,
                ls_octet=ls_octet, ms_octet=ms_octet)
            fun_test.test_assert(header_created, "Create Priority Flow Control Header for %s" %
                                 stream_obj.spirent_handle)
            result['pfc_header_obj'] = pfc_header_obj
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_custom_header(self, stream_obj, source_mac, destination_mac,
                                ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE, byte_pattern="0001FFFF"):
        result = None
        try:
            ethernet_header_obj = Ethernet2Header(destination_mac=destination_mac,
                                                  source_mac=source_mac, ether_type=ether_type)
            custom_byte_pattern_obj = CustomBytePatternHeader(byte_pattern=byte_pattern)
            fun_test.log("Creating Pause Mac Control Frame with Ethernet 802.3 Mac Control header")
            header_created = self.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ethernet_header_obj)
            fun_test.test_assert(header_created, "Create Ethernet 802.3 Mac Control header for %s" %
                                 stream_obj.spirent_handle)
            header_created = self.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=custom_byte_pattern_obj)
            fun_test.test_assert(header_created, "Create Pause Mac Control header for %s" % stream_obj.spirent_handle)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_diffserv(self, streamblock_obj, dscp_high='0',
                           dscp_low='0', name=None, reserved='00', ip_header_obj=None, update=False):
        result = False
        try:
            fun_test.log("Creating tos_diffServ obj")
            # Get latest ip handle

            new_ip_handle = None
            if not ip_header_obj:
                ip_header_obj = Ipv4Header()
                child_type = 'children-' + ip_header_obj.HEADER_TYPE.lower()
                new_ip_handle = self.stc_manager.get_object_children(handle=streamblock_obj._spirent_handle,
                                                                     child_type=child_type)[0]
            if (not new_ip_handle) and (not ip_header_obj):
                ip_header_obj = Ipv6Header()
                child_type = 'children-' + ip_header_obj.HEADER_TYPE.lower()
                new_ip_handle = self.stc_manager.get_object_children(handle=streamblock_obj._spirent_handle,
                                                                     child_type=child_type)[0]
            else:
                child_type = 'children-' + ip_header_obj.HEADER_TYPE.lower()
                new_ip_handle = self.stc_manager.get_object_children(handle=streamblock_obj._spirent_handle,
                                                                     child_type=child_type)[0]

            ip_header_obj._spirent_handle = new_ip_handle
            tos_diffserv_obj = TosDiffServ()
            child_type = 'children-' + tos_diffserv_obj.HEADER_TYPE.lower()
            tosdiffserv_handle = self.stc_manager.get_object_children(handle=ip_header_obj._spirent_handle,
                                                                      child_type=child_type)[0]
            if not update:
                tosdiffserv_handle = self.stc_manager.stc.create(tos_diffserv_obj.HEADER_TYPE.lower(),
                                                                 under=new_ip_handle)

                fun_test.simple_assert(tosdiffserv_handle, "Created tosdiffServ under ip header")
            tos_diffserv_obj._spirent_handle = tosdiffserv_handle
            fun_test.log("Adding diff serv under tosdiffServ")

            if update:
                child_type = 'children-' + DiffServ.HEADER_TYPE.lower()
                old_diffserv_handle = self.stc_manager.get_object_children(handle=tosdiffserv_handle,
                                                                           child_type=child_type)
                if old_diffserv_handle:
                    old_diffserv_handle = old_diffserv_handle[0]
                    del_diff_serv = self.stc_manager.delete_handle(old_diffserv_handle)
                    fun_test.simple_assert(del_diff_serv, "Delete old diff serv handle")

            diff_serv_obj = DiffServ(dscp_high=dscp_high, dscp_low=dscp_low, name=name, reserved=reserved)
            diff_serv_handle = self.stc_manager.stc.create(diff_serv_obj.HEADER_TYPE, under=tosdiffserv_handle,
                                                           dscpHigh=dscp_high, dscpLow=dscp_low, reserved=reserved,
                                                           Name=name)
            fun_test.simple_assert(diff_serv_handle, "Diff serv handle created")
            diff_serv_obj._spirent_handle = diff_serv_handle
            self.stc_manager.stc.perform("StreamBlockUpdate", StreamBlock=streamblock_obj._spirent_handle)
            fun_test.simple_assert(self.stc_manager.apply_configuration(), "Apply configuration with dscp values")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_ptp_header(self, header_obj, stream_block_handle, create_header=False, delete_header_type="ipv4"):
        result = False
        try:
            attributes = header_obj.get_attributes_dict()
            if create_header:
                if delete_header_type:
                    existing_headers = self.stc_manager.get_object_children(stream_block_handle)
                    fun_test.debug("headers found in %s: %s" % (stream_block_handle, existing_headers))
                    for header in existing_headers:
                        if delete_header_type in header:
                            fun_test.log("Deleting Header: %s" % header)
                            self.stc_manager.delete_handle(header)
                            break
                fun_test.log("Creating %s Header under %s" % (header_obj.HEADER_TYPE, stream_block_handle))
                handle = self.stc_manager.stc.create(header_obj.HEADER_TYPE, under=stream_block_handle,
                                                     Name=attributes['Name'])
                fun_test.simple_assert(handle, "Handle Created")

            child = header_obj.HEADER_TYPE.lower()
            child_type = 'children-' + child
            parent_handle = self.stc_manager.get_object_children(stream_block_handle, child_type=child_type)[0]
            # child_handle = self.stc_manager.get_object_children(parent_handle)
            # print child_handle
            fun_test.log("Updating %s Header under %s" % (parent_handle, stream_block_handle))
            handle = self.stc_manager.stc.create("ptpHeader", under=parent_handle, **attributes)
            fun_test.simple_assert(handle, "Handle updated")

            if self.stc_manager.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_overlay_frame_stack(self, streamblock_obj, mpls, header_list=[], headers_created=False,
                                   byte_pattern="00012140"):
        result = {}
        result['result'] = False
        try:
            fun_test.simple_assert(header_list, "Headers are not provided to be created in streamblock")
            header_obj_list = []
            if not mpls:
                destination_port = 4789
                underlay_list = header_list[0:header_list.index(VxLAN)]
                overlay_list = header_list[header_list.index(VxLAN):]
            else:
                destination_port = 6635
                underlay_list = header_list[0:header_list.index(CustomBytePatternHeader)]
                overlay_list = header_list[header_list.index(CustomBytePatternHeader):]
            spirent_configs = self.spirent_config
            spirent_config = self.nu_config_obj.read_traffic_generator_config()
            ul_ipv4_routes_config = self.nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
            fun_test.simple_assert(ul_ipv4_routes_config, "Ensure routes config fetched")

            ol_ipv4_routes_config = self.nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config, overlay=True)
            fun_test.simple_assert(ol_ipv4_routes_config, "Ensure ipv4 overlay routes config fetched")

            ul_ipv6_routes_config = self.nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config, ip_version="ipv6")
            fun_test.simple_assert(ul_ipv6_routes_config, "Ensure ipv6 routes config fetched")

            ol_ipv6_routes_config = self.nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config, ip_version="ipv6", overlay=True)
            fun_test.simple_assert(ol_ipv6_routes_config, "Ensure routes config fetched")

            destination_mac1 = ul_ipv4_routes_config['routermac']

            if headers_created:
                header_obj_list = header_list
            else:
                for header in underlay_list:
                    if header == Ethernet2Header:
                        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE
                        if 'ipv6' in underlay_list[1].HEADER_TYPE.lower():
                            ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE
                        eth_obj = Ethernet2Header(destination_mac=destination_mac1,
                                                  ether_type=ether_type)
                        header_obj_list.append(eth_obj)
                    elif header == Ipv4Header:
                        ipv4_obj = Ipv4Header(destination_address=ul_ipv4_routes_config['l3_config']['destination_ip1'])
                        current_index = header_list.index(header)
                        ipv4_obj.protocol = ipv4_obj.PROTOCOL_TYPE_TCP if 'tcp' in header_list[
                            current_index + 1].HEADER_TYPE.lower() else ipv4_obj.PROTOCOL_TYPE_UDP
                        header_obj_list.append(ipv4_obj)
                    elif header == Ipv6Header:
                        ipv6_obj = Ipv6Header(destination_address=ul_ipv6_routes_config['l3_config']['destination_ip1'])
                        current_index = header_list.index(header)
                        ipv6_obj.nextHeader = ipv6_obj.NEXT_HEADER_TCP if 'tcp' in header_list[
                            current_index + 1].HEADER_TYPE.lower() else ipv6_obj.NEXT_HEADER_UDP
                        header_obj_list.append(ipv6_obj)
                    elif header == UDP:
                        udp_obj = UDP(destination_port=destination_port)
                        header_obj_list.append(udp_obj)
                for header in overlay_list:
                    if header == VxLAN:
                        vxlan_obj = VxLAN()
                        header_obj_list.append(vxlan_obj)
                    elif header == CustomBytePatternHeader:
                        custom_header_obj = CustomBytePatternHeader(byte_pattern=byte_pattern)
                        header_obj_list.append(custom_header_obj)
                    elif header == Ethernet2Header:
                        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE
                        if 'ipv6' in overlay_list[2].HEADER_TYPE.lower():
                            ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE
                        eth_obj = Ethernet2Header(destination_mac=destination_mac1,
                                                  ether_type=ether_type)
                        header_obj_list.append(eth_obj)
                    elif header == Ipv4Header:
                        ipv4_obj = Ipv4Header(destination_address=ol_ipv4_routes_config['l3_config']['destination_ip2'])
                        index_list = [i for i, n in enumerate(header_list) if n == header]
                        current_index = index_list[0]
                        if len(index_list) == 2:
                            current_index = index_list[1]
                        ipv4_obj.protocol = ipv4_obj.PROTOCOL_TYPE_TCP if 'tcp' in header_list[
                            current_index + 1].HEADER_TYPE.lower() else ipv4_obj.PROTOCOL_TYPE_UDP
                        header_obj_list.append(ipv4_obj)
                    elif header == Ipv6Header:
                        ipv6_obj = Ipv6Header(destination_address=ol_ipv6_routes_config['l3_config']['destination_ip2'])
                        index_list = [i for i, n in enumerate(header_list) if n == header]
                        current_index = index_list[0]
                        if len(index_list) == 2:
                            current_index = index_list[1]
                        ipv6_obj.nextHeader = ipv6_obj.NEXT_HEADER_TCP if 'tcp' in header_list[
                            current_index + 1].HEADER_TYPE.lower() else ipv6_obj.NEXT_HEADER_UDP
                        header_obj_list.append(ipv6_obj)
                    elif header == UDP:
                        udp_obj = UDP()
                        header_obj_list.append(udp_obj)
                    elif header == TCP:
                        tcp_obj = TCP()
                        header_obj_list.append(tcp_obj)
                    else:
                        raise Exception("Header %s not found in overlay options" % header.HEADER_TYPE)

            for header_obj in header_obj_list:
                delete_header = []
                if header_obj is header_obj_list[0]:
                    delete_header = [Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE]
                output = self.stc_manager.configure_frame_stack(stream_block_handle=streamblock_obj._spirent_handle,
                                                                header_obj=header_obj, delete_header=delete_header)
                fun_test.test_assert(output, "Added header %s to framestack" % header_obj.HEADER_TYPE)
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_overlay_frame_stack(self, port, overlay_type=ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP, streamblock_obj=None,
                                      mpls=False, byte_pattern="00012140", streamblock_frame_length=148):
        result = {}
        try:
            if mpls:
                if overlay_type == self.MPLS_ETH_IPV4_UDP_CUST_IPV4_TCP:
                    header_list = [Ethernet2Header, Ipv4Header, UDP, CustomBytePatternHeader, Ipv4Header, TCP]
                elif overlay_type == self.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP:
                    header_list = [Ethernet2Header, Ipv4Header, UDP, CustomBytePatternHeader, Ipv4Header, UDP]
            if not streamblock_obj:
                streamblock_obj = StreamBlock(fixed_frame_length=streamblock_frame_length)
                stream = self.configure_stream_block(stream_block_obj=streamblock_obj, port_handle=port)
                fun_test.simple_assert(stream, "Creating streamblock for overlay")
            if overlay_type == self.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP:
                header_list = [Ethernet2Header, Ipv4Header, UDP, VxLAN, Ethernet2Header, Ipv4Header, TCP]
            elif overlay_type == self.ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP:
                header_list = [Ethernet2Header, Ipv4Header, UDP, VxLAN, Ethernet2Header, Ipv4Header, UDP]
            elif overlay_type == self.ETH_IPV4_UDP_VXLAN_ETH_IPV6_TCP:
                header_list = [Ethernet2Header, Ipv4Header, UDP, VxLAN, Ethernet2Header, Ipv6Header, TCP]
            elif overlay_type == self.ETH_IPV4_UDP_VXLAN_ETH_IPV6_UDP:
                header_list = [Ethernet2Header, Ipv4Header, UDP, VxLAN, Ethernet2Header, Ipv6Header, UDP]
            elif overlay_type == self.ETH_IPV6_UDP_VXLAN_ETH_IPV4_TCP:
                header_list = [Ethernet2Header, Ipv6Header, UDP, VxLAN, Ethernet2Header, Ipv4Header, TCP]
            elif overlay_type == self.ETH_IPV6_UDP_VXLAN_ETH_IPV4_UDP:
                header_list = [Ethernet2Header, Ipv6Header, UDP, VxLAN, Ethernet2Header, Ipv4Header, UDP]
            elif overlay_type == self.ETH_IPV6_UDP_VXLAN_ETH_IPV6_TCP:
                header_list = [Ethernet2Header, Ipv6Header, UDP, VxLAN, Ethernet2Header, Ipv6Header, TCP]
            elif overlay_type == self.ETH_IPV6_UDP_VXLAN_ETH_IPV6_UDP:
                header_list = [Ethernet2Header, Ipv6Header, UDP, VxLAN, Ethernet2Header, Ipv6Header, UDP]

            result['streamblock_obj'] = streamblock_obj
            result.update(self.create_overlay_frame_stack(header_list=header_list, streamblock_obj=streamblock_obj,
                          mpls=mpls, byte_pattern=byte_pattern))

        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def update_overlay_frame_header(self, streamblock_obj, header_obj, updated_header_attributes_dict={}, overlay=True):
        result = False
        try:
            fun_test.simple_assert(updated_header_attributes_dict, "Empty attributes sent for update")
            child_type = 'children-' + header_obj.HEADER_TYPE.lower()
            child_handle_list = self.stc_manager.get_object_children(handle=streamblock_obj._spirent_handle,
                                                                     child_type=child_type)
            fun_test.simple_assert(child_handle_list, "Fetch all header handles")
            child_handle = child_handle_list[0]
            if overlay:
                if len(child_handle_list) > 1:
                    child_handle = child_handle_list[1]
            fun_test.log("Modifying atrributes on handle %s" % child_handle)
            self.stc_manager.stc.config(child_handle, **updated_header_attributes_dict)
            fun_test.simple_assert(self.stc_manager.apply_configuration(), message="Changed attributes of header")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def setup_ports_using_command(self, no_of_ports_needed, flow_type,
                                  flow_direction=NuConfigManager.FLOW_DIRECTION_NU_NU):
        result = {"result": False, 'port_list': [], 'interface_obj_list': []}
        try:
            if not self.stc_manager.project_handle:
                project_handle = self.stc_manager.create_project(project_name=self.session_name)
                fun_test.test_assert(project_handle, "Create %s Project" % self.session_name)

            if not self.stc_connected:
                fun_test.test_assert(expression=self.stc_manager.health(session_name=self.session_name)['result'],
                                     message="Health of Spirent Test Center")
                self.stc_connected = True

            offline_ports = {}
            ports_map = self.nu_config_obj.get_spirent_dut_port_mapper(no_of_ports_needed=no_of_ports_needed,
                                                                       flow_type=flow_type,
                                                                       flow_direction=flow_direction)
            existing_ports = self.stc_manager.get_port_list()
            for port_handle in existing_ports:
                port_info = self.stc_manager.get_port_details(port=port_handle)
                offline_ports[port_info['Location'].split('//')[1]] = port_handle

            for key, val in ports_map.iteritems():
                fun_test.log("Using %s -----> %s" % (key, val))
                if val in offline_ports:
                    result['port_list'].append(offline_ports[val])
                else:
                    port_handle = self.stc_manager.create_port(location=val)
                    fun_test.test_assert(port_handle, "Create Port: %s" % val)
                    result['port_list'].append(port_handle)
                    interface_obj = self.create_physical_interface(port_handle=port_handle)
                    fun_test.simple_assert(interface_obj, "Create %s Interface for Port %s" % (str(interface_obj),
                                                                                               port_handle))
                    result['interface_obj_list'].append(interface_obj)

            ports_attached = self.stc_manager.attach_ports_by_command(port_handles=result['port_list'],
                                                                      auto_connect_chassis=True)
            fun_test.test_assert(ports_attached, "%s ports attached successfully" % result['port_list'])

            fec_disable = self._ensure_fec_disabled(port_list=result['port_list'])
            fun_test.test_assert(fec_disable, "Ensure FEC disable on interfaces")

            # Update Spirent handle for each interface
            count = 0
            for port_handle in result['port_list']:
                handle = self.stc_manager.get_activephy_targets_under_port(port_handle=port_handle)
                fun_test.log("Chassis Type: %s Link Status: %s Interface: %s Port: %s" % (
                    self.chassis_type, self.stc_manager.get_interface_link_status(handle=handle), handle, port_handle))
                fun_test.log("Chassis Type: %s Auto Negotiation Status: %s Interface: %s Port: %s" % (
                    self.chassis_type, self.stc_manager.get_auto_negotiation_status(handle=handle), handle,
                    port_handle))
                fun_test.log("Chassis Type: %s FEC Status: %s Interface: %s Port: %s" % (
                    self.chassis_type, self.stc_manager.get_fec_status(handle=handle), handle, port_handle))
                count += 1
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_traffic_rate_comparison(self, rx_summary_subscribe_handle, tx_summary_subscribe_handle, stream_objects,
                                      wait_before_fetching_results=True, validate_throughput=True, tx_port=None,
                                      rx_port=None, time_for_throughput=25, kbps=False):
        result = {'result': False, 'pps_in': 0, 'pps_out': 0, 'throughput_count_in': 0, 'throughput_count_out': 0}
        try:
            if wait_before_fetching_results:
                fun_test.sleep("Waiting for traffic to reach full throughput", seconds=time_for_throughput)

            for stream_obj in stream_objects:
                if stream_obj.FixedFrameLength == 64:
                    if not tx_port and not rx_port:
                        raise Exception("Please provide Spirent Tx Port and Rx Port handles")

                    checkpoint = "Fetch Tx Port Results for %s" % tx_port
                    tx_port_result = self.stc_manager.get_generator_port_results(
                        port_handle=tx_port, subscribe_handle=tx_summary_subscribe_handle)
                    fun_test.simple_assert(expression=tx_port_result, message=checkpoint)
                    checkpoint = "Fetch Rx Port Results for %s" % rx_port
                    rx_port_result = self.stc_manager.get_rx_port_analyzer_results(
                        port_handle=rx_port, subscribe_handle=rx_summary_subscribe_handle)
                    fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

                    fun_test.log("FrameRate (PPS) Results for %s : Tx --> %d fps and Rx --> %d fps" % (
                        stream_obj.spirent_handle, int(tx_port_result['GeneratorFrameRate']),
                        int(rx_port_result['TotalFrameRate'])))
                    rx_pps_count = self._manipulate_rate_counters(tx_rate_count=int(tx_port_result['GeneratorFrameRate']),
                                                                  rx_rate_count=int(rx_port_result['TotalFrameRate']))

                    result['pps_in'] = int(tx_port_result['GeneratorFrameRate'])
                    result['pps_out'] = rx_pps_count
                    if validate_throughput:
                        if kbps:
                            tx_l1_bit_rate_in_kbps = self._convert_bps_to_kbps(
                                count_in_bps=int(tx_port_result['L1BitRate']))
                            rx_l1_bit_rate_in_kbps = self._convert_bps_to_kbps(
                                count_in_bps=int(rx_port_result['L1BitRate']))
                            fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d kbps and Rx --> %d kbps " % (
                                stream_obj.spirent_handle, tx_l1_bit_rate_in_kbps, rx_l1_bit_rate_in_kbps))
                            rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_kbps,
                                                                         rx_rate_count=rx_l1_bit_rate_in_kbps)
                            result['throughput_count_in'] = tx_l1_bit_rate_in_kbps
                            result['throughput_count_out'] = rx_bit_rate
                        else:
                            tx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(tx_port_result['L1BitRate']))
                            rx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(rx_port_result['L1BitRate']))
                            fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d Mbps and Rx --> %d Mbps " % (
                                stream_obj.spirent_handle, tx_l1_bit_rate_in_mbps, rx_l1_bit_rate_in_mbps))
                            rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_mbps,
                                                                         rx_rate_count=rx_l1_bit_rate_in_mbps)
                            result['throughput_count_in'] = tx_l1_bit_rate_in_mbps
                            result['throughput_count_out'] = rx_bit_rate
                else:

                    checkpoint = "Fetch Tx Results for %s" % stream_obj.spirent_handle
                    tx_result = self.stc_manager.get_tx_stream_block_results(stream_block_handle=stream_obj.spirent_handle,
                                                                             subscribe_handle=tx_summary_subscribe_handle,
                                                                             summary=True, refresh=False)
                    fun_test.simple_assert(expression=tx_result, message=checkpoint)

                    checkpoint = "Fetch Rx Results for %s" % stream_obj.spirent_handle
                    rx_result = self.stc_manager.get_rx_stream_block_results(stream_block_handle=stream_obj.spirent_handle,
                                                                             subscribe_handle=rx_summary_subscribe_handle,
                                                                             summary=True, refresh=False)
                    fun_test.simple_assert(expression=rx_result, message=checkpoint)

                    fun_test.log("FrameRate (PPS) Results for %s : Tx --> %d fps and Rx --> %d fps" % (
                        stream_obj.spirent_handle, int(tx_result['FrameRate']), int(rx_result['FrameRate'])))

                    rx_pps_count = self._manipulate_rate_counters(tx_rate_count=int(tx_result['FrameRate']),
                                                                  rx_rate_count=int(rx_result['FrameRate']))

                    result['pps_in'] = int(tx_result['FrameRate'])
                    result['pps_out'] = rx_pps_count
                    if validate_throughput:
                        if kbps:
                            tx_l1_bit_rate_in_kbps = self._convert_bps_to_kbps(count_in_bps=int(tx_result['L1BitRate']))
                            rx_l1_bit_rate_in_kbps = self._convert_bps_to_kbps(count_in_bps=int(rx_result['L1BitRate']))
                            fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d kbps and Rx --> %d kbps " % (
                                stream_obj.spirent_handle, tx_l1_bit_rate_in_kbps, rx_l1_bit_rate_in_kbps))

                            rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_kbps,
                                                                         rx_rate_count=rx_l1_bit_rate_in_kbps)
                            result['throughput_count_in'] = tx_l1_bit_rate_in_kbps
                            result['throughput_count_out'] = rx_bit_rate
                        else:
                            tx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(tx_result['L1BitRate']))
                            rx_l1_bit_rate_in_mbps = self._convert_bps_to_mbps(count_in_bps=int(rx_result['L1BitRate']))
                            fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d Mbps and Rx --> %d Mbps " % (
                                stream_obj.spirent_handle, tx_l1_bit_rate_in_mbps, rx_l1_bit_rate_in_mbps))

                            rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_mbps,
                                                                         rx_rate_count=rx_l1_bit_rate_in_mbps)
                            result['throughput_count_in'] = tx_l1_bit_rate_in_mbps
                            result['throughput_count_out'] = rx_bit_rate
                #     result['pps_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): int(rx_result['FrameRate'])}
                # if validate_throughput:
                #     result['throughput_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): float(rx_bit_rate)}
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_latency_values_for_streamblock(self, streamblock_handle, rx_streamblock_subscribe_handle):
        result = {}
        result['latency_min'] = 0.0
        result['latency_max'] = 0.0
        result['latency_avg'] = 0.0
        try:
            output = self.stc_manager.get_rx_stream_block_results(stream_block_handle=streamblock_handle,
                                                                  subscribe_handle=rx_streamblock_subscribe_handle,
                                                                  summary=True)
            if output:
                result['latency_min'] = output["MinLatency"]
                result['latency_max'] = output["MaxLatency"]
                result['latency_avg'] = output["AvgLatency"]
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_jitter_values_for_streamblock(self, streamblock_handle, rx_streamblock_subscribe_handle,
                                          change_mode_jitter=False):
        result = {}
        result['jitter_min'] = 0.0
        result['jitter_max'] = 0.0
        result['jitter_avg'] = 0.0
        try:
            view_attribute_list = ["AvgJitter", "MinJitter", "MaxJitter"]
            if change_mode_jitter:
                rx_summary_subscribe = self.subscribe_rx_results(
                    parent=self.stc_manager.project_handle, result_type="RxStreamSummaryResults",
                    change_mode=True, result_view_mode=SpirentManager.RESULT_VIEW_MODE_JITTER,
                    view_attribute_list=view_attribute_list)
                fun_test.simple_assert(rx_summary_subscribe, "Subscribe to jitter mode")
            output = self.stc_manager.get_rx_stream_block_results(stream_block_handle=streamblock_handle,
                                                                  subscribe_handle=rx_summary_subscribe,
                                                                  summary=True)
            if output:
                result['jitter_min'] = output["MinJitter"]
                result['jitter_max'] = output["MaxJitter"]
                result['jitter_avg'] = output["AvgJitter"]
            if change_mode_jitter:
                rx_summary_subscribe = self.subscribe_rx_results(
                    parent=self.stc_manager.project_handle, result_type="RxStreamSummaryResults",
                    change_mode=True, result_view_mode=SpirentManager.RESULT_VIEW_MODE_BASIC)
                fun_test.simple_assert(rx_summary_subscribe, "Subscribe back to basic mode")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


    def use_model_helper(self, model_name, data_dict, unit_dict):
        result = False
        try:
            generic_helper = ModelHelper(model_name=model_name)
            status = fun_test.PASSED
            generic_helper.set_units(**unit_dict)
            generic_helper.add_entry(**data_dict)
            generic_helper.set_status(status)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _parse_file_to_json_in_order(self, file_name):
        result = None
        try:
            with open(file_name, "r") as infile:
                contents = infile.read()
                result = json.loads(contents, object_pairs_hook=OrderedDict)
        except Exception as ex:
            scheduler_logger.critical(str(ex))
        return result

    def populate_non_rfc_performance_json_file(self, flow_type, frame_size, pps, filename, timestamp, num_flows=None, throughput=None,
                                               mode="100G", model_name=JUNIPER_PERFORMANCE_MODEL_NAME, offloads=False, protocol="UDP",
                                               latency_min=None, latency_max=None, latency_avg=None, jitter_min=None, jitter_max=None, jitter_avg=None,
                                               half_load_latency=False, num_tunnels=None):
        results = []
        output = False
        try:
            output_dict = OrderedDict()
            output_dict["mode"] = mode
            output_dict["version"] = fun_test.get_version()
            output_dict["timestamp"] = str(timestamp)
            output_dict["half_load_latency"] = half_load_latency
            output_dict["flow_type"] = flow_type
            output_dict["frame_size"] = frame_size
            output_dict["pps"] = pps
            if throughput:
                output_dict["throughput"] = throughput
            if latency_min:
                output_dict["latency_min"] = latency_min
            if latency_max:
                output_dict["latency_max"] = latency_max
            if latency_avg:
                output_dict["latency_avg"] = latency_avg
            if jitter_min:
                output_dict["jitter_min"] = jitter_min
            if jitter_max:
                output_dict["jitter_max"] = jitter_max
            if jitter_avg:
                output_dict["jitter_avg"] = jitter_avg
            if num_flows or num_tunnels:
                if num_flows:
                    output_dict["num_flows"] = num_flows
                if num_tunnels:
                    output_dict["num_tunnels"] = num_tunnels
                output_dict["offloads"] = offloads
                output_dict["protocol"] = protocol

            fun_test.log("FunOS version is %s" % output_dict['version'])
            results.append(output_dict)
            file_path = fun_test.get_test_case_artifact_file_name(post_fix_name=filename)
            contents = self._parse_file_to_json_in_order(file_name=file_path)
            if contents:
                append_new_results = contents + results
                file_created = self.create_counters_file(json_file_name=file_path,
                                                    counter_dict=append_new_results)
                fun_test.simple_assert(file_created, "Create Performance JSON file")
            else:
                file_created = self.create_counters_file(json_file_name=file_path,
                                                    counter_dict=results)
                fun_test.simple_assert(file_created, "Create Performance JSON file")
            unit_dict = {}
            unit_dict["pps_unit"] = PerfUnit.UNIT_PPS
            unit_dict["throughput_unit"] = PerfUnit.UNIT_MBITS_PER_SEC
            add_entry = self.use_model_helper(model_name=model_name, data_dict=output_dict, unit_dict=unit_dict)
            fun_test.simple_assert(add_entry, "Entry added to model %s" % model_name)
            fun_test.add_checkpoint("Entry added to model %s" % model_name)

            output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output