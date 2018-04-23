from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *


class SpirentEthernetTrafficTemplate(SpirentTrafficGeneratorTemplate):

    def __init__(self, session_name):
        SpirentTrafficGeneratorTemplate.__init__(self)
        self.session_name = session_name

    def setup(self, no_of_ports_needed):
        result = {"result": False, 'port_list': [], 'interface_obj_list': []}

        try:
            fun_test.test_assert(expression=self.stc_manager.health(session_name=self.session_name)['result'],
                                 message="Health of Spirent Test Center")

            if fun_test.local_settings:
                fun_test.log("%s Config: %s" % (self.stc_manager.dut_type, self.stc_manager.dut_config))
                no_of_ports_in_config = len(self.stc_manager.host_config['test_module']["port_nos"])
                fun_test.debug("Ports Needed: %d    Ports found in local config: %d" % (no_of_ports_needed,
                                                                                        no_of_ports_in_config))
                fun_test.test_assert(no_of_ports_needed <= no_of_ports_in_config,
                                     message="Ensure no of ports needed to run script exists in local config.")

                chassis_info = self.stc_manager.get_test_module_info()
                slot_found = False
                for module in chassis_info['module_info']:
                    if int(module['Index']) == self.stc_manager.host_config['test_module']['slot_no'] and \
                            int(module['PortCount']) >= no_of_ports_needed:
                        slot_found = True
                        #status = self.stc_manager.ensure_port_groups_status(port_group_list=chassis_info['port_group_info'])
                        #fun_test.simple_assert(status, "Ports are not free. Please check")

                fun_test.test_assert(slot_found, "Ensure slot num mentioned in config exists on STC")

                project_handle = self.stc_manager.create_project(project_name=self.session_name)
                fun_test.test_assert(project_handle, "Create %s Project" % self.session_name)
                physical_interface_type = str(self.stc_manager.host_config['test_module']['interface_type'])

                for port_no in self.stc_manager.host_config['test_module']['port_nos']:
                    port_location = "//%s/%s/%s" % (self.stc_manager.chassis_ip,
                                                    self.stc_manager.host_config['test_module']['slot_no'], port_no)
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
            else:
                pass
            # TODO: Currently we are using local settings to get slot/port no based on chassis_type and also
            # TODO: reading dut_config such as source_mac, dest_mac etc.
            # TODO: This will get changed later on once we finalized the topology that we need to run our script with
            # TODO: exact script input
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
                interface_class = EthernnetCopperInterface
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

    def configure_stream_block(self, stream_block_obj, port_handle=None, update=False):
        result = False
        try:
            attributes = stream_block_obj.get_attributes_dict()
            if update:
                result = self.stc_manager.update_stream_block(stream_block_handle=stream_block_obj._spirent_handle,
                                                              update_attributes=attributes)
                fun_test.test_assert(result, message="Update Stream Block %s" % str(stream_block_obj._spirent_handle))
            else:
                if not port_handle:
                    raise Exception("Please provide port handle under which stream to be created")
                spirent_handle = self.stc_manager.create_stream_block(port=port_handle, attributes=attributes)
                fun_test.test_assert(spirent_handle, message="Create Stream Block: %s" % spirent_handle)
                stream_block_obj._spirent_handle = spirent_handle  # Setting Spirent handle to our object
                result = True
        except Exception as ex:
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
                generator_config_obj.spirent_handle = generator
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

    def activate_stream_blocks(self, stream_obj_list):
        result = False
        try:
            stream_block_handles = []
            for stream_obj in stream_obj_list:
                stream_block_handles.append(stream_obj._spirent_handle)

            result = self.stc_manager.run_stream_block_active_command(stream_block_handles=stream_block_handles)
            fun_test.test_assert(result, message="Activate Stream Blocks: %s" % stream_block_handles)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def deactivate_stream_blocks(self, stream_obj_list):
        result = False
        try:
            stream_block_handles = []
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

    def subscribe_tx_results(self, parent, config_type="StreamBlock", result_type="TxStreamBlockResults"):
        result_handle = None
        try:
            fun_test.log("Subscribing to %s for %s config to get %s result" % (parent, config_type, result_type))
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type)
            fun_test.simple_assert(op_handle, "Getting tx subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_rx_results(self, parent, config_type="StreamBlock", result_type="RxStreamBlockResults"):
        result_handle = None
        try:
            fun_test.log("Subscribing to %s for %s config to get %s result" % (parent, config_type, result_type))
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type)
            fun_test.simple_assert(op_handle, "Getting rx subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_analyzer_results(self,  parent, config_type="Analyzer", result_type="AnalyzerPortResults"):
        result_handle = None
        try:
            fun_test.log("Subscribing to port analyzer results on port %s" % parent)
            pass
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type)
            fun_test.simple_assert(op_handle, "Getting analyzer subscribe handle")
            result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_generator_results(self,  parent, config_type="Generator", result_type="GeneratorPortResults"):
        result_handle = None
        try:
            fun_test.log("Subscribing to port generator results on port %s" % parent)
            pass
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type)
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
                fun_test.test_assert(output, message="Clear results for handle %s" % handle)
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
            if len(result) == 1:
                result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def delete_streamblocks(self, streamblock_handle_list):
        result = False
        try:
            fun_test.debug("Deleting list of objects %s" % streamblock_handle_list)
            result = self.stc_manager.delete_objects(streamblock_handle_list)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def subscribe_to_all_results(self, parent):
        result = {'result': 'False'}
        try:
            fun_test.debug("Subscribing to tx results")
            tx_subscribe = self.subscribe_tx_results(parent=parent)
            fun_test.simple_assert(tx_subscribe, "Check tx subscribed")
            result['tx_subscribe'] = tx_subscribe

            fun_test.debug("Subscribing to rx results")
            rx_subscribe = self.subscribe_rx_results(parent=parent)
            fun_test.simple_assert(rx_subscribe, "Check rx subscribed")
            result['rx_subscribe'] = rx_subscribe

            fun_test.debug("Subscribing to generator results")
            generator_subscribe = self.subscribe_generator_results(parent=parent)
            fun_test.simple_assert(generator_subscribe, "Check generator subscribed")
            result['generator_subscribe'] = generator_subscribe

            fun_test.debug("Subscribing to analyzer results")
            analyzer_subscribe = self.subscribe_analyzer_results(parent=parent)
            fun_test.simple_assert(analyzer_subscribe, "Check analyzer subscribed")
            result['analyzer_subscribe'] = analyzer_subscribe

            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_traffic_rate_results(self, rx_subscribe_handle, tx_subscribe_handle, stream_objects):
        result = {'result': False, 'pps_count': {}, 'throughput_count': {}}
        try:
            fun_test.sleep("wait", seconds=2)
            for stream_obj in stream_objects:
                checkpoint = "Fetch Tx Results for %s" % stream_obj.spirent_handle
                tx_result = self.stc_manager.get_tx_stream_block_results(stream_block_handle=stream_obj.spirent_handle,
                                                                         subscribe_handle=tx_subscribe_handle)
                fun_test.simple_assert(expression=tx_result, message=checkpoint)

                checkpoint = "Fetch Rx Results for %s" % stream_obj.spirent_handle
                rx_result = self.stc_manager.get_rx_stream_block_results(stream_block_handle=stream_obj.spirent_handle,
                                                                         subscribe_handle=rx_subscribe_handle)
                fun_test.simple_assert(expression=rx_result, message=checkpoint)

                checkpoint = "Ensure Tx FrameRate(PPS) is equal to Rx FrameRate(PPS) for %d Frame Size" % \
                             stream_obj.FixedFrameLength
                fun_test.log("FrameRate (PPS) Results for %s : Tx --> %d fps and Rx --> %d fps" % (
                    stream_obj.spirent_handle, int(tx_result['FrameRate']), int(rx_result['FrameRate'])))
                fun_test.simple_assert(expression=int(tx_result['FrameRate']) != 0, message="Tx FrameRate is zero")
                fun_test.test_assert_expected(expected=int(tx_result['FrameRate']),
                                              actual=int(rx_result['FrameRate']),
                                              message=checkpoint)

                checkpoint = "Ensure Throughput Tx Rate is equal to Rx Rate for %d Frame Size" % \
                             stream_obj.FixedFrameLength
                fun_test.log("Throughput (L1 Rate) Results for %s : Tx --> %d bps and Rx --> %d bps " % (
                    stream_obj.spirent_handle, int(tx_result['L1BitRate']), int(rx_result['L1BitRate'])
                ))
                fun_test.simple_assert(expression=int(tx_result['L1BitRate']) != 0, message="Tx L1 Rate is zero")
                fun_test.test_assert_expected(expected=int(tx_result['L1BitRate']),
                                              actual=int(rx_result['L1BitRate']),
                                              message=checkpoint)
                result['pps_count'] = {'frame_%s' % str(stream_obj.FixedFrameLength): {'tx': tx_result['FrameRate'],
                                                                                       'rx': rx_result['FrameRate']}}

                result['throughput_count'] = {'frame_%s' %
                                              str(stream_obj.FixedFrameLength): {'tx': tx_result['L1BitRate'],
                                                                                 'rx': rx_result['L1BitRate']}}
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _calculate_threshold_count(self, count, tolerance_percent=10):
        return (float(count) * tolerance_percent/100) + count

    def validate_latency_results(self, rx_result, stream_objects,
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
                pass
            else:
                # For performance benchmarking we are comparing existing benchmarking results
                for stream_obj in stream_objects:
                    frame_size = str(stream_obj.FixedFrameLength)
                    checkpoint = "Validate Avg. latency for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency" % \
                                 (frame_size, str(stream_obj.Load))
                    expected_threshold_latency = self._calculate_threshold_count(
                        count=expected_latency_count['frame_%s' % frame_size]['avg'],
                        tolerance_percent=tolerance_percent)
                    fun_test.test_assert(expression=float(rx_result['AvgLatency']) <= float(expected_threshold_latency),
                                         message=checkpoint)

                    checkpoint = "Validate Min. latency for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency" % \
                                 (frame_size, str(stream_obj.Load))
                    expected_threshold_latency = self._calculate_threshold_count(
                        count=expected_latency_count['frame_%s' % frame_size]['min'],
                        tolerance_percent=tolerance_percent)
                    fun_test.test_assert(expression=float(rx_result['MinLatency']) <= float(expected_threshold_latency),
                                         message=checkpoint)

                    checkpoint = "Validate Max. latency for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency" % \
                                 (frame_size, str(stream_obj.Load))
                    expected_threshold_latency = self._calculate_threshold_count(
                        count=expected_latency_count['frame_%s' % frame_size]['max'],
                        tolerance_percent=tolerance_percent)
                    fun_test.test_assert(expression=float(rx_result['MaxLatency']) <= float(expected_threshold_latency),
                                         message=checkpoint)
                    result['frame_%s' % frame_size] = {'avg': rx_result['AvgLatency'],
                                                       'min': rx_result['MinLatency'],
                                                       'max': rx_result['MaxLatency']}
            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_jitter_results(self, rx_result, stream_objects,
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
                pass
            else:
                # For performance benchmarking we are comparing existing benchmarking results
                for stream_obj in stream_objects:
                    frame_size = str(stream_obj.FixedFrameLength)
                    checkpoint = "Validate Avg. jitter for %s Frame Size with Load %s " \
                                 "Actual jitter <= Expected Threshold jitter" % \
                                 (frame_size, str(stream_obj.Load))
                    expected_threshold_jitter = self._calculate_threshold_count(
                        count=expected_jitter_count['frame_%s' % frame_size]['avg'], tolerance_percent=tolerance_percent)
                    fun_test.test_assert(expression=float(rx_result['AvgJitter']) <= float(expected_threshold_jitter),
                                         message=checkpoint)

                    checkpoint = "Validate Min. jitter for %s Frame Size with Load %s " \
                                 "Actual jitter <= Expected Threshold jitter" % \
                                 (frame_size, str(stream_obj.Load))
                    expected_threshold_jitter = self._calculate_threshold_count(
                        count=expected_jitter_count['frame_%s' % frame_size]['min'], tolerance_percent=tolerance_percent)
                    fun_test.test_assert(expression=float(rx_result['MinJitter']) <= float(expected_threshold_jitter),
                                         message=checkpoint)

                    checkpoint = "Validate Max. jitter for %s Frame Size with Load %s " \
                                 "Actual latency <= Expected Threshold latency" % \
                                 (frame_size, str(stream_obj.Load))
                    expected_threshold_jitter = self._calculate_threshold_count(
                        count=expected_jitter_count['frame_%s' % frame_size]['max'], tolerance_percent=tolerance_percent)
                    fun_test.test_assert(expression=float(rx_result['MaxJitter']) <= float(expected_threshold_jitter),
                                         message=checkpoint)
                    result['frame_%s' % frame_size] = {'avg': rx_result['AvgJitter'],
                                                       'min': rx_result['MinJitter'],
                                                       'max': rx_result['MaxJitter']}

            result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def validate_performance_result(self, tx_subscribe_handle, rx_subscribe_handle, stream_objects,
                                    jitter=False, expected_latency_count={}, expected_jitter_count={},
                                    tolerance_percent=10):
        result = False
        try:
            rx_result = {}
            for stream_obj in stream_objects:
                checkpoint = "Fetch Rx Results for %s" % stream_obj.spirent_handle
                rx_result = self.stc_manager.get_rx_stream_block_results(
                    stream_block_handle=stream_obj.spirent_handle,
                    subscribe_handle=rx_subscribe_handle)
                fun_test.simple_assert(expression=rx_result, message=checkpoint)

                checkpoint = "Fetch Tx Results for %s" % stream_obj.spirent_handle
                tx_result = self.stc_manager.get_tx_stream_block_results(
                    stream_block_handle=stream_obj.spirent_handle,
                    subscribe_handle=tx_subscribe_handle)
                fun_test.simple_assert(expression=tx_result, message=checkpoint)

                checkpoint = "Ensure Tx FrameCount is equal to Rx FrameCount for %d frame size" % (
                    stream_obj.FixedFrameLength
                )
                fun_test.log("Frame Count Results for %d B: \n Tx Frame Count: %d \n Rx Frame Count: %d " % (
                    stream_obj.FixedFrameLength, int(tx_result['FrameCount']), int(rx_result['FrameCount'])
                ))
                fun_test.test_assert_expected(expected=int(tx_result['FrameCount']),
                                              actual=int(rx_result['FrameCount']),
                                              message=checkpoint)
            if jitter:
                checkpoint = "Validate Jitter Counters"
                jitter_result = self.validate_jitter_results(rx_result=rx_result,
                                                             stream_objects=stream_objects,
                                                             expected_jitter_count=expected_jitter_count,
                                                             tolerance_percent=tolerance_percent)
                fun_test.simple_assert(expression=jitter_result['result'], message=checkpoint)

                #TODO: Add Logging
            else:
                checkpoint = "Validate Latency Counters"
                latency_result = self.validate_latency_results(rx_result=rx_result,
                                                               stream_objects=stream_objects,
                                                               expected_latency_count=expected_latency_count,
                                                               tolerance_percent=tolerance_percent)
                fun_test.simple_assert(expression=latency_result['result'], message=checkpoint)

            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result













