from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import SpirentTrafficGeneratorTemplate


class SpirentEthernetTrafficTemplate(SpirentTrafficGeneratorTemplate):

    def __init__(self, session_name, chassis_type=SpirentManager.VIRTUAL_CHASSIS_TYPE):
        SpirentTrafficGeneratorTemplate.__init__(self, chassis_type=chassis_type)
        self.session_name = session_name
        self.chassis_type = chassis_type

    def setup(self, port_list, slot_no,
              physical_interface_type=SpirentManager.ETHERNET_COPPER_INTERFACE):
        result = {"result": False}
        try:

            fun_test.test_assert(expression=self.stc_manager.check_health(session_name=self.session_name)['result'],
                                 message="Health of Spirent Hosts")

            project_handle = self.stc_manager.create_project(project_name=self.session_name)
            fun_test.test_assert(project_handle, "Create %s Project" % self.session_name)

            for port_no in port_list:
                port_location = "//%s/%s/%s" % (self.stc_manager.chassis_ip, slot_no, port_no)
                port_handle = self.stc_manager.create_port(location=port_location)
                fun_test.test_assert(port_handle, "Create Port: %s" % port_location)
                result['port_%s' % port_no] = port_handle
                port_interface = self.stc_manager.configure_physical_interface(port_handle=port_handle,
                                                                               interface_type=physical_interface_type)
                fun_test.test_assert(port_interface, "Create %s Interface for Port %s" % (physical_interface_type,
                                                                                          port_handle))

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
        except Exception as ex:
            fun_test.critical(str(ex))
        return True

    def configure_stream_block(self, stream_block_obj, port_handle=None, update=False):
        result = False
        try:
            attributes = stream_block_obj.get_attributes_dict()
            if update:
                result = self.stc_manager.update_stream_block(stream_block_handle=stream_block_obj.spirent_handle,
                                                              update_attributes=attributes)
                fun_test.test_assert(result, message="Update Stream Block %s" % str(stream_block_obj.spirent_handle))
            else:
                if not port_handle:
                    raise FunTestLibException("Please provide port handle under which stream to be created")
                spirent_handle = self.stc_manager.create_streamblock(port=port_handle, attributes=attributes)
                fun_test.test_assert(spirent_handle, message="Create Stream Block: %s" % spirent_handle)
                self.StreamBlock.spirent_handle = spirent_handle  # Setting Spirent handle to our object
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def setup_existing_tcc_configuration(self, config_file_path, configure_ports=False, port_list=[]):
        result = False
        try:
            fun_test.test_assert(expression=self.stc_manager.check_health(session_name=self.session_name)['result'],
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
                deactivate_success = self.deactivate_stream_blocks(stream_block_handles=all_port_streams[key])
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
                                                                      port_no=port_no)

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
                        if stream_parameters['Name'] == stream_block_name:
                            stream_info = stream_parameters
                            stream_handle = child
                            stream_found = True
                            break
                if stream_found:
                    break
            if stream_found:
                stream_obj = self.StreamBlock()
                stream_info = self._intersect_writable_attributes(writable_attributes=stream_obj.get_attributes_dict(),
                                                                  all_attributes=stream_info)
                stream_obj.update_stream_block_object(**stream_info)
                self.StreamBlock._spirent_handle = stream_handle
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
                result = self.stc_manager.update_generator_config(generator_config_handle=generator_config_obj.spirent_handle,
                                                                  attributes=attributes)
                fun_test.test_assert(result, message="Update Generator Config: %s" % generator_config_obj.spirent_handle)
            else:
                fun_test.log("Getting new generator in port: %s with default values" % port_handle)
                generator = self.stc_manager.get_generator(port_handle=port_handle)
                fun_test.test_assert(generator, "Get Generator")
                generator_config_handle = self.stc_manager.get_generator_config(generator_handle=generator)
                fun_test.test_assert(generator_config_handle, "Get Generator Config for %s " % generator)
                self.stc_manager.stc.config(generator_config_handle, **attributes)
                self.GeneratorConfig._spirent_handle = generator
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def activate_stream_blocks(self, stream_block_handles):
        result = False
        try:
            result = self.stc_manager.run_stream_block_active_command(stream_block_handles=stream_block_handles)
            fun_test.test_assert(result, message="Activate Stream Blocks: %s" % stream_block_handles)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def deactivate_stream_blocks(self, stream_block_handles):
        result = False
        try:
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
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type)
            if op_handle:
                result_handle = op_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def subscribe_rx_results(self, parent, config_type="StreamBlock", result_type="RxStreamBlockResults"):
        result_handle = None
        try:
            op_handle = self.stc_manager.subscribe_results(parent=parent, config_type=config_type,
                                                           result_type=result_type)
            if op_handle:
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
            if query_handle:
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
            if attribute_name not in tx_results.keys():
                raise Exception("Attribute %s not found in tx_results" % attribute_name)
            if attribute_name not in rx_results.keys():
                raise Exception("Attribute %s not found in rx_results" % attribute_name)
            if tx_results[attribute_name] == rx_results[attribute_name]:
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def check_non_zero_error_count(self, rx_results):
        result = {}
        try:
            for key, val in rx_results.iteritems():
                if ('error' in key.lower())and ('count' in key.lower()) and (not int(val) == 0):
                    result[key] = val
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
