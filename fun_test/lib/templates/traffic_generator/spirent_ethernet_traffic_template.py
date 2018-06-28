from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from prettytable import PrettyTable


class SpirentEthernetTrafficTemplate(SpirentTrafficGeneratorTemplate):
    ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP = 1
    ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP = 2
    ETH_IPV4_UDP_VXLAN_ETH_IPV6_TCP = 3
    ETH_IPV4_UDP_VXLAN_ETH_IPV6_UDP = 4
    ETH_IPV6_UDP_VXLAN_ETH_IPV4_TCP = 5
    ETH_IPV6_UDP_VXLAN_ETH_IPV4_UDP = 6
    ETH_IPV6_UDP_VXLAN_ETH_IPV6_TCP = 7
    ETH_IPV6_UDP_VXLAN_ETH_IPV6_UDP = 8

    def __init__(self, session_name, spirent_config, chassis_type=SpirentManager.VIRTUAL_CHASSIS_TYPE):
        SpirentTrafficGeneratorTemplate.__init__(self, spirent_config=spirent_config, chassis_type=chassis_type)
        self.session_name = session_name
        self.stc_connected = False

    def setup(self, no_of_ports_needed=2, port_mapper_dict={}):
        result = {"result": False, 'port_list': [], 'interface_obj_list': []}

        project_handle = self.stc_manager.create_project(project_name=self.session_name)
        fun_test.test_assert(project_handle, "Create %s Project" % self.session_name)
        physical_interface_type = str(self.spirent_config[self.chassis_type]['interface_type'])

        if not self.stc_connected:
            fun_test.test_assert(expression=self.stc_manager.health(session_name=self.session_name)['result'],
                                 message="Health of Spirent Test Center")
            self.stc_connected = True

        try:
            if port_mapper_dict:
                for key, val in port_mapper_dict.iteritems():
                    #port_location = "//%s/%s" % (self.stc_manager.chassis_ip, key)
                    port_handle = self.stc_manager.create_port(location=key)
                    fun_test.test_assert(port_handle, "Create Port: %s" % key)
                    result['port_list'].append(port_handle)
                    interface_obj = self.create_physical_interface(interface_type=physical_interface_type,
                                                                   port_handle=port_handle)
                    fun_test.test_assert(interface_obj, "Create %s Interface for Port %s" % (physical_interface_type,
                                                                                             port_handle))
                    result['interface_obj_list'].append(interface_obj)
            else:
                no_of_ports_in_config = len(self.spirent_config[self.chassis_type]["ports"])
                fun_test.debug("Ports Needed: %d    Ports found in nu config: %d" % (no_of_ports_needed,
                                                                                     no_of_ports_in_config))
                fun_test.test_assert(no_of_ports_needed <= no_of_ports_in_config,
                                     message="Ensure no of ports needed to run script exists in nu config.")

                chassis_info = self.stc_manager.get_test_module_info()
                slot_found = False
                for module in chassis_info['module_info']:
                    if int(module['Index']) == self.spirent_config[self.chassis_type]['slot_no'] and \
                            int(module['PortCount']) >= no_of_ports_needed:
                        slot_found = True
                        #status = self.stc_manager.ensure_port_groups_status(port_group_list=chassis_info['port_group_info'])
                        #fun_test.simple_assert(status, "Ports are not free. Please check")

                fun_test.simple_assert(slot_found, "Ensure slot num mentioned in config exists on STC")

                for port_no in self.spirent_config[self.chassis_type]['ports'][:no_of_ports_needed]:
                    port_location = "//%s/%s/%s" % (self.stc_manager.chassis_ip,
                                                    self.spirent_config[self.chassis_type]['slot_no'], port_no)
                    port_handle = self.stc_manager.create_port(location=port_location)
                    fun_test.test_assert(port_handle, "Create Port: %s" % port_location)
                    result['port_list'].append(port_handle)
                    interface_obj = self.create_physical_interface(interface_type=physical_interface_type,
                                                                   port_handle=port_handle)
                    fun_test.test_assert(interface_obj, "Create %s Interface for Port %s" % (physical_interface_type,
                                                                                             port_handle))
                    result['interface_obj_list'].append(interface_obj)

            # Attach ports method take care of applying configuration
            fun_test.test_assert(self.stc_manager.attach_ports(), message="Attach Ports")
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def cleanup(self):
        try:
            self.stc_manager.disconnect_session()
            self.stc_manager.disconnect_lab_server()
            # self.stc_manager.disconnect_chassis()
        except Exception as ex:
            fun_test.critical(str(ex))
        return True

    def create_physical_interface(self, interface_type, port_handle):
        result = None
        try:
            interface_class = None
            if interface_type == self.stc_manager.ETHERNET_COPPER_INTERFACE:
                interface_class = EthernetCopperInterface
            elif interface_type == self.stc_manager.ETHERNET_10GIG_FIBER_INTERFACE:
                interface_class = Ethernnet10GigFiberInterface

            interface_obj = interface_class()
            attributes = interface_obj.get_attributes_dict()
            spirent_handle = self.stc_manager.create_physical_interface(port_handle=port_handle,
                                                                        interface_type=str(interface_obj),
                                                                        attributes=attributes)
            fun_test.test_assert(spirent_handle, "Create Physical Interface: %s" % spirent_handle)
            interface_obj._spirent_handle = spirent_handle
            result = interface_obj
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_physical_interface(self, interface_obj):
        result = False
        try:
            attributes = interface_obj.get_attributes_dict()
            result = self.stc_manager.update_physical_interface(interface_handle=interface_obj._spirent_handle,
                                                                update_attributes=attributes)
            fun_test.test_assert(result, "Update %s physical interface" % interface_obj._spirent_handle)
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

    def setup_existing_tcc_configuration(self, config_file_path, configure_ports=False, port_list=[]):
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

    def activate_stream_blocks(self, stream_obj_list=None):
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

            result = self.stc_manager.run_stream_block_active_command(stream_block_handles=stream_block_handles)
            fun_test.test_assert(result, message="Activate Stream Blocks: %s" % stream_block_handles)
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
            pass
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list)
            fun_test.simple_assert(op_handle, "Getting analyzer subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_diff_serv_results(self,  parent, config_type="Analyzer", result_type="DiffServResults",
                                    view_attribute_list=None):
        result_handle = None
        try:
            fun_test.log("Subscribing to diff serv results on %s" % parent)
            pass
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type,
                                                           view_attribute_list=view_attribute_list)
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

    def subscribe_to_all_results(self, parent, diff_serv=False, pfc=False):
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
                fun_test.debug("Subscribing to diff serv results")
                diff_serv_subscribe = self.subscribe_diff_serv_results(parent=parent)
                fun_test.simple_assert(diff_serv_subscribe, "Check diff serv subscribe")
                result['diff_serv_subscribe'] = diff_serv_subscribe

            if pfc:
                fun_test.debug("Subscribing to pfc results")
                pfc_subscribe = self.subscribe_pfc_results(parent=parent)
                fun_test.simple_assert(pfc_subscribe, "Check pfc subscribe")
                result['pfc_subscribe'] = pfc_subscribe

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

    def validate_traffic_rate_results(self, rx_summary_subscribe_handle, tx_summary_subscribe_handle, stream_objects,
                                      wait_before_fetching_results=True, validate_throughput=True):
        result = {'result': False, 'pps_count': {}, 'throughput_count': {}}
        try:
            if wait_before_fetching_results:
                fun_test.sleep("Waiting for traffic to reach full throughput", seconds=5)

            for stream_obj in stream_objects:
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
                fun_test.simple_assert(expression=int(tx_result['FrameRate']) != 0, message="Tx FrameRate is zero")
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
                    fun_test.simple_assert(expression=int(tx_result['L1BitRate']) != 0, message="Tx L1 Rate is zero")
                    rx_bit_rate = self._manipulate_rate_counters(tx_rate_count=tx_l1_bit_rate_in_mbps,
                                                                 rx_rate_count=rx_l1_bit_rate_in_mbps)
                    fun_test.test_assert_expected(expected=tx_l1_bit_rate_in_mbps,
                                                  actual=rx_bit_rate,
                                                  message=checkpoint)

                result['pps_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): int(rx_result['FrameRate'])}
                if validate_throughput:
                    result['throughput_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): rx_bit_rate}
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
            if not expected_latency_count:
                # TODO: Later on we need to integrate RFC 2544 standards for benchmarking
                # If existing record not found for given frame size dump the result as it is for now
                result['frame_%s' % stream_obj.FixedFrameLength] = {'avg': float(rx_result['AvgLatency']),
                                                                    'min': float(rx_result['MinLatency']),
                                                                    'max': float(rx_result['MaxLatency'])}
            else:
                # For performance benchmarking we are comparing existing benchmarking results
                frame_size = str(stream_obj.FixedFrameLength)
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
                fun_test.test_assert(expression=float(rx_result['AvgLatency']) <= float(expected_threshold_latency),
                                     message=checkpoint)

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
                fun_test.test_assert(expression=float(rx_result['MinLatency']) <= float(expected_threshold_latency),
                                     message=checkpoint)

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
                fun_test.test_assert(expression=float(rx_result['MaxLatency']) <= float(expected_threshold_latency),
                                     message=checkpoint)
                result['frame_%s' % frame_size] = {'avg': float(rx_result['AvgLatency']),
                                                   'min': float(rx_result['MinLatency']),
                                                   'max': float(rx_result['MaxLatency'])}
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
            if not expected_jitter_count:
                # TODO: Later on we need to integrate RFC 2544 standards for benchmarking
                result['frame_%s' % stream_obj.FixedFrameLength] = {'avg': float(rx_result['AvgJitter']),
                                                                    'min': float(rx_result['MinJitter']),
                                                                    'max': float(rx_result['MaxJitter'])}
            else:
                # For performance benchmarking we are comparing existing benchmarking results
                frame_size = str(stream_obj.FixedFrameLength)
                checkpoint = "Validate Avg. jitter for %s Frame Size with Load %s " \
                             "Actual jitter <= Expected Threshold jitter (%s)" % \
                             (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                expected_threshold_jitter = self._calculate_threshold_count(
                    count=expected_jitter_count['jitter_avg'], tolerance_percent=tolerance_percent)
                fun_test.log("Expected Avg jitter: %s us Frame Size: %s" % (str(expected_threshold_jitter),
                                                                            frame_size))
                fun_test.log("Avg Jitter for %s Frame Size %s B: %s " % (stream_obj.spirent_handle,
                                                                         frame_size, str(rx_result['AvgJitter'])))
                fun_test.test_assert(expression=float(rx_result['AvgJitter']) <= float(expected_threshold_jitter),
                                     message=checkpoint)

                checkpoint = "Validate Min. jitter for %s Frame Size with Load %s " \
                             "Actual jitter <= Expected Threshold jitter (%s)" % \
                             (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                expected_threshold_jitter = self._calculate_threshold_count(
                    count=expected_jitter_count['jitter_min'], tolerance_percent=tolerance_percent)
                fun_test.log("Expected Min jitter: %s us Frame Size: %s" % (str(expected_threshold_jitter),
                                                                            frame_size))
                fun_test.log("Min Jitter for %s Frame Size %s B: %s " % (stream_obj.spirent_handle,
                                                                         frame_size, str(rx_result['MinJitter'])))
                fun_test.test_assert(expression=float(rx_result['MinJitter']) <= float(expected_threshold_jitter),
                                     message=checkpoint)

                checkpoint = "Validate Max. jitter for %s Frame Size with Load %s " \
                             "Actual jitter <= Expected Threshold jitter (%s)" % \
                             (frame_size, str(stream_obj.Load), stream_obj.spirent_handle)
                expected_threshold_jitter = self._calculate_threshold_count(
                    count=expected_jitter_count['jitter_max'], tolerance_percent=tolerance_percent)
                fun_test.log("Expected Max jitter: %s us Frame Size: %s" % (str(expected_threshold_jitter),
                                                                            frame_size))
                fun_test.log("Max Jitter for %s Frame Size %s B: %s " % (stream_obj.spirent_handle,
                                                                         frame_size, str(rx_result['MaxJitter'])))
                fun_test.test_assert(expression=float(rx_result['MaxJitter']) <= float(expected_threshold_jitter),
                                     message=checkpoint)
                result['frame_%s' % frame_size] = {'avg': float(rx_result['AvgJitter']),
                                                   'min': float(rx_result['MinJitter']),
                                                   'max': float(rx_result['MaxJitter'])}

            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_performance_result(self, tx_subscribe_handle, rx_subscribe_handle, stream_objects,
                                    jitter=False, expected_performance_data=[],
                                    tolerance_percent=10):
        result = {'result': False}
        try:

            key = "frame_%s" % str(stream_objects[0].FixedFrameLength)
            result[key] = []
            for stream_obj in stream_objects:
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
                fun_test.test_assert_expected(expected=int(tx_result['FrameCount']),
                                              actual=int(rx_result['FrameCount']),
                                              message=checkpoint)
                if jitter:
                    expected_jitter_dict = {}
                    for record in expected_performance_data:
                        if "_name" in record:
                            continue
                        if record['frame_size'] == stream_obj.FixedFrameLength:
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
            fun_test.log_disable_timestamps()
            fun_test.log_section("Nu Transit Performance Latency Counters")
            table_obj = PrettyTable(['Frame Size', 'PPS', 'Throughput (Mbps)', 'Avg. Latency (us)', 'Min Latency (us)',
                                     'Max Latency (us)'])
            for key in result:
                pps_count = result[key]['pps_count']
                throughput_count = result[key]['throughput_count']
                if len(result[key]['latency_count']) > 1:
                    avg_latency1 = result[key]['latency_count'][0]['avg']
                    avg_latency2 = result[key]['latency_count'][1]['avg']
                    min_latency1 = result[key]['latency_count'][0]['min']
                    min_latency2 = result[key]['latency_count'][1]['min']
                    max_latency1 = result[key]['latency_count'][0]['max']
                    max_latency2 = result[key]['latency_count'][1]['max']
                    table_obj.add_row([key, pps_count, throughput_count, avg_latency1, min_latency1, max_latency1])
                    table_obj.add_row([key, pps_count, throughput_count, avg_latency2, min_latency2, max_latency2])
                else:
                    avg_latency1 = result[key]['latency_count'][0]['avg']
                    min_latency1 = result[key]['latency_count'][0]['min']
                    max_latency1 = result[key]['latency_count'][0]['max']

                    table_obj.add_row([key, pps_count, throughput_count, avg_latency1, min_latency1, max_latency1])
            fun_test.log(str(table_obj))
            fun_test.log_enable_timestamps()
        except Exception as ex:
            fun_test.critical(str(ex))

    def display_jitter_counters(self, result):
        try:
            fun_test.log_disable_timestamps()
            fun_test.log_section("Nu Transit Performance Jitter Counters")
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

    def configure_pause_mac_control_header(self, stream_obj, source_mac, destination_mac, length="8808", pause_time=0,
                                           op_code="0001", preamble="55555555555555d5"):
        result = {}
        result['result'] = False
        try:
            ethernet_header_obj = Ethernet8023MacControlHeader(destination_mac=destination_mac,
                                                               source_mac=source_mac, length=length, preamble=preamble)
            pause_header_obj = PauseMacControlHeader(op_code=op_code, pause_time=pause_time)
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
                                               reserved=''):
        result = {}
        result['result'] = False
        try:
            ethernet_header_obj = MacControlHeader(destination_mac=destination_mac,
                                                               source_mac=source_mac, length=length, preamble=preamble)
            pfc_header_obj = PriorityFlowControlHeader(op_code=op_code, time0=time0, time1=time1, time2=time2,
                                                       time3=time3, time4=time4, time5=time5, time6=time6, time7=time7,
                                                       reserved=reserved)
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

    def configure_diffserv(self, ip_header_obj, streamblock_obj, dscp_high='0',
                           dscp_low='0', name=None, reserved='00'):
        result = False
        try:
            fun_test.log("Creating tos_diffServ obj")
            # Get latest ip handle
            child_type = 'children-' + ip_header_obj.HEADER_TYPE.lower()
            new_ip_handle = self.stc_manager.get_object_children(handle=streamblock_obj._spirent_handle,
                                                                 child_type=child_type)[0]
            ip_header_obj._spirent_handle = new_ip_handle
            tos_diffserv_obj = TosDiffServ()
            tosdiffserv_handle = self.stc_manager.stc.create(tos_diffserv_obj.HEADER_TYPE.lower(),
                                                             under=new_ip_handle)

            fun_test.simple_assert(tosdiffserv_handle, "Created tosdiffServ under ip header")
            tos_diffserv_obj._spirent_handle = tosdiffserv_handle
            fun_test.log("Adding diff serv under tosdiffServ")
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
            # TODO: Delete IPv4 Header
            attributes = header_obj.get_attributes_dict()
            if create_header:
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

    def create_overlay_frame_stack(self, streamblock_obj, header_list=[], headers_created=False):
        result = OrderedDict()
        result['result'] = False
        try:
            fun_test.simple_assert(header_list, "Headers are not provided to be created in streamblock")
            header_obj_list = []
            underlay_list = header_list[0:header_list.index(VxLAN)]
            overlay_list = header_list[header_list.index(VxLAN):]
            spirent_configs = self.spirent_config

            # Clear streamblock
            self.stc_manager.stc.config(streamblock_obj._spirent_handle, FrameConfig='')

            if headers_created:
                header_obj_list = header_list
            else:
                for header in underlay_list:
                    if header == Ethernet2Header:
                        eth_obj = Ethernet2Header(destination_mac=spirent_configs['l2_config']['destination_mac'])
                        header_obj_list.append(eth_obj)
                    if header == Ipv4Header:
                        ipv4_obj = Ipv4Header(destination_address=spirent_configs['l3_config']['ipv4']['destination_ip1'])
                        header_obj_list.append(ipv4_obj)
                    if header == Ipv6Header:
                        ipv6_obj = Ipv6Header(destination_address=spirent_configs['l3_config']['ipv6']['destination_ip1'])
                        header_obj_list.append(ipv6_obj)
                    if header == UDP:
                        udp_obj = UDP()
                        header_obj_list.append(udp_obj)
                for header in overlay_list:
                    if header == VxLAN:
                        vxlan_obj = VxLAN()
                        header_obj_list.append(vxlan_obj)
                    if header == Ipv4Header:
                        ipv4_obj = Ipv4Header(destination_address=spirent_configs['l3_overlay_config']['ipv4']['destination_ip1'])
                        header_obj_list.append(ipv4_obj)
                    if header == Ipv6Header:
                        ipv6_obj = Ipv6Header(destination_address=spirent_configs['l3_overlay_config']['ipv6']['destination_ip1'])
                        header_obj_list.append(ipv6_obj)
                    if header == UDP:
                        udp_obj = UDP()
                        header_obj_list.append(udp_obj)
                    if header == TCP:
                        tcp_obj = TCP()
                        header_obj_list.append(tcp_obj)

            for header_obj in header_obj_list:
                output = self.stc_manager.configure_frame_stack(stream_block_handle=streamblock_obj._spirent_handle,
                                                                header_obj=header_obj)
                fun_test.test_assert(output['result'], "Added header %s to framestack" % header_obj.HEADER_TYPE)
                result[header_obj] = header_obj
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_overlay_frame_stack(self, streamblock_obj, overlay_type=ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP):
        try:
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

            result = self.create_overlay_frame_stack(header_list=header_list, streamblock_obj=streamblock_obj)

        except Exception as ex:
            fun_test.critical(str(ex))
        return result

