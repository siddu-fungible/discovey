from lib.system.fun_test import *
from fun_settings import *
from lib.system.utils import parse_file_to_json
from lib.utilities.StcPython import StcPython
import re


class SpirentManager(object):
    SPIRENT_HOSTS_SPEC = ASSET_DIR + "/traffic_generator_hosts.json"
    SYSTEM_OBJECT = "system1"
    ETHERNET_COPPER_INTERFACE = "EthernetCopper"
    ETHERNET_10GIG_FIBER = "Ethernet10GigFiber"
    ETHERNET_100GIG_FIBER = "Ethernet100GigFiber"
    LOCAL_EXPERIMENTAL_ETHERTYPE = "88B5"
    ETHERNETII_FRAME = "ethernet:EthernetII"
    ETHERNET_PAUSE_FRAME = "ethernetpause:EthernetPause"
    IP_VERSION_4 = "ipv4:IPv4"
    IP_VERSION_6 = "ipv6:IPv6"
    FIXED_FRAME_LENGTH = "FIXED"
    PHYSICAL_CHASSIS_TYPE = "physical"
    VIRTUAL_CHASSIS_TYPE = "virtual"
    DUT_TYPE_QFX = "qfx"
    DUT_TYPE_F1 = "f1"
    DUT_TYPE_PALLADIUM = "palladium"
    MODULE_STATUS_UP = "MODULE_STATUS_UP"
    MODULE_SYNC_STATUS = "MODULE_IN_SYNC"
    OWNERSHIP_STATE_AVAILABLE = "OWNERSHIP_STATE_AVAILABLE"
    LINK_STATUS_UP = "LINK_STATUS_UP"

    def __init__(self, chassis_type=VIRTUAL_CHASSIS_TYPE, dut_type=DUT_TYPE_PALLADIUM):
        try:
            self.stc = StcPython()
        except Exception as ex:
            raise FunTestLibException("Unable to initialized Spirent Manager: %s" % str(ex))
        self.project_handle = None
        self.host_config = {}
        self.dut_config = {}
        self.chassis_type = chassis_type
        self.dut_type = dut_type
        if fun_test.local_settings:
            self.chassis_type = fun_test.get_local_setting("spirent_chassis_type")
            self.dut_type = fun_test.get_local_setting("dut_type")
            self.host_config['test_module'] = fun_test.get_local_setting(self.chassis_type)
            self.dut_config = fun_test.get_local_setting(self.dut_type)
        self.chassis_ip = self._get_chassis_ip_by_chassis_type()

    def health(self, session_name="TestSession"):
        health_result = {"result": False, "error_message": None}
        fun_test.debug("Determining health of Spirent Application and Lab Server. Checking availability of ports")
        try:
            fun_test.test_assert(self.get_api_version(), "Get STC API Version")
            fun_test.test_assert(self.connect_lab_server(session_name=session_name), "Connect to Lab Server")
            fun_test.test_assert(self.connect_license_manager(), "Connect to License Server")
            health_result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return health_result

    def get_test_module_info(self):
        module_list = []
        chassis_info = {}
        port_group_list = []
        port_list = []
        try:
            if not self.connect_chassis():
                raise FunTestLibException("Unable to connect chassis: %s" % self.chassis_ip)
            chassis_mgr = self.get_chassis_manager()
            manager_handles = self.stc.get(chassis_mgr, "children-PhysicalChassis").split()
            for handle in manager_handles:
                modules = self.stc.get(handle, "children-PhysicalTestModule").split()
                for module in modules:
                    info = self.stc.get(module)
                    module_list.append(info)

                    # Getting Port Group handles
                    portgroups = self.stc.get(module, "children-physicalportgroup").split()
                    for group in portgroups:
                        info = self.stc.get(group)
                        port_group_list.append(info)

                        # Getting Port handles for each group
                        ports = self.stc.get(group, "children-physicalport").split()
                        for port in ports:
                            info = self.stc.get(port)
                            port_list.append(info)

            chassis_info['module_info'] = module_list
            chassis_info['port_group_info'] = port_group_list
            chassis_info['port_info'] = port_list

        except Exception as ex:
            fun_test.critical(str(ex))
        return chassis_info

    def ensure_modules_status_up(self, module_list):
        result = False
        try:
            for module in module_list:
                fun_test.debug("Determining status of slot no: %d " % module['Index'])
                if not module['Status'] == self.MODULE_STATUS_UP:
                    raise FunTestLibException("Test Module Status is not UP. Found: %s" % module['Status'])

                if not module['SyncStatus'] == self.MODULE_SYNC_STATUS:
                    raise FunTestLibException("Test Module")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def ensure_port_groups_status(self, port_group_list):
        result = False
        try:
            fun_test.simple_assert(port_group_list, "Port Group List is empty")

            for port_group in port_group_list:
                fun_test.debug("Determining status of port group no: %d " % int(port_group['Index']))
                if not port_group['OwnershipState'] == self.OWNERSHIP_STATE_AVAILABLE:
                    raise FunTestLibException("Port Group Reserved by %s@%s" % (port_group['OwnerUserId'],
                                                                                port_group['OwnerHostname']))

                if not port_group['Status'] == self.MODULE_STATUS_UP:
                    raise FunTestLibException("Port Group Status is not Up")

            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def is_port_group_free(self, port_group):
        result = True
        try:
            if port_group['OwnerUserId'] and port_group['OwnerHostname']:
                fun_test.debug("Port Group Reserved by %s@%s" % (port_group['OwnerUserId'],
                                                                 port_group['OwnerHostname']))
                result = False
            fun_test.simple_assert(result, "Port Group is not free")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def ensure_ports_status(self, port_list):
        result = False
        try:
            for port in port_list:
                fun_test.debug("Determining status of port no: %d " % port['Index'])
                if not port['LinkStatus'] == self.LINK_STATUS_UP:
                    raise FunTestLibException("Port is not UP. Found: %s" % (port['LinkStatus']))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_chassis_ip_by_chassis_type(self):
        ip_address = None
        try:
            self._read_spirent_config()
            if self.chassis_type == self.PHYSICAL_CHASSIS_TYPE:
                ip_address = self.host_config['hosts']['physical_chassis_ip']
            else:
                ip_address = self.host_config['hosts']['virtual_chassis_ip']
        except Exception as ex:
            fun_test.critical(str(ex))
        return ip_address

    def connect_chassis(self):
        result = False
        try:
            self.stc.connect(str(self.chassis_ip))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def disconnect_chassis(self):
        result = False
        try:
            self.stc.disconnect(str(self.chassis_ip))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _read_spirent_config(self):
        spirent_config = {}
        try:
            configs = parse_file_to_json(file_name=self.SPIRENT_HOSTS_SPEC)
            fun_test.simple_assert(expression=configs, message="Read Config File")
            for config in configs:
                if config['name'] == "spirent_test_center":
                    spirent_config = config
                    break
            fun_test.debug("Found: %s" % spirent_config)
            self.host_config['hosts'] = spirent_config
        except Exception as ex:
            fun_test.critical(str(ex))
        return self.host_config

    def get_chassis_manager(self):
        handle = None
        try:
            handle = self.stc.get(self.SYSTEM_OBJECT, "children-PhysicalChassisManager")
        except Exception as ex:
            fun_test.critical(str(ex))
        return handle

    def get_api_version(self):
        fun_test.debug("Getting STC API version")
        version = None
        try:
            version = self.stc.get(self.SYSTEM_OBJECT, 'version')
            fun_test.debug("Version: %s" % version)
        except Exception as ex:
            fun_test.critical(str(ex))
        return version

    def connect_lab_server(self, session_name):
        result = False
        try:
            self.stc.perform("CSTestSessionConnect", host=self.host_config['hosts']['lab_server_ip'],
                             TestSessionName=session_name,
                             CreateNewTestSession=True)
            self.stc.perform("TerminateBll", TerminateType="ON_LAST_DISCONNECT")
            fun_test.debug("Connected to Lab Server: %s" % self.host_config['hosts']['lab_server_ip'])
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def connect_license_manager(self):
        result = False
        try:
            license_manager = self.stc.get(self.SYSTEM_OBJECT, "children-licenseservermanager")
            output = self.stc.create("LicenseServer", under=license_manager, server=self.host_config['hosts']['license_server_ip'])
            fun_test.simple_assert(output, "Connect to License Server: %s" % self.host_config['hosts']['license_server_ip'])
            fun_test.debug("Connected to License Server: %s" % self.host_config['hosts']['license_server_ip'])
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_project(self, project_name):
        try:
            project_handle = self.stc.create("project")
            self.project_handle = project_handle
        except Exception as ex:
            fun_test.critical(str(ex))
        return self.project_handle

    def create_port(self, location, use_default_host=False):
        port = None
        try:
            if not self.project_handle:
                raise Exception("Please Create Project First")
            port = self.stc.create('port', under=self.project_handle, location=location,
                                   useDefaultHost=use_default_host)
            self.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return port

    def apply_configuration(self):
        result = False
        try:
            fun_test.debug("Applying Configuration")
            self.stc.apply()
            result = True
        except Exception as ex:
            fun_test.critical("Unable to apply configuration. ERROR: %s" % str(ex))
        return result

    def configure_physical_interface(self, port_handle, interface_type=ETHERNET_COPPER_INTERFACE):
        result = None
        try:
            result = self.stc.create(interface_type, under=port_handle)
            self.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def attach_ports(self):
        result = False
        try:
            output = self.stc.perform("AttachPorts")
            print output
            # if re.search(r'ERROR', output):
            #    raise FunTestLibException("Failed to Attach Ports: %s" % output)
            if self.apply_configuration():
                for port in self.get_port_list():
                    if self.get_port_details(port=port)['Online'] == "false":
                        raise FunTestLibException("Ports are not online. Please check")
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_port_details(self, port):
        port_info = {}
        try:
            port_info = self.stc.get(port)
        except Exception as ex:
            fun_test.critical(str(ex))
        return port_info

    def create_stream_block(self, port, attributes):
        result = None
        try:
            result = self.stc.create("StreamBlock", under=port, **attributes)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_mac_address(self, streamblock, source_mac, destination_mac, ethernet_type,
                              frame_type=ETHERNETII_FRAME):
        result = False
        try:
            fun_test.debug("Adding Mac Address for %s Stream" % str(streamblock))
            self.stc.create(frame_type, under=streamblock, srcMac=source_mac, dstMac=destination_mac,
                            etherType=ethernet_type)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_ip_address(self, streamblock, source, destination, gateway, ip_version=IP_VERSION_4):
        result = False
        try:
            self.stc.create(ip_version, under=streamblock, sourceAddr=source, destAddr=destination,
                            gateway=gateway)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_frame_stack(self, stream_block_handle, header_obj):
        result = False
        try:
            attributes = header_obj.get_attributes_dict()
            fun_test.debug("Configuring %s header under %s" % (header_obj.HEADER_TYPE, stream_block_handle))
            handle = self.stc.create(header_obj.HEADER_TYPE, under=stream_block_handle,  **attributes)
            if handle:
                header_obj.spirent_handle = handle
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_traffic_stream(self, stream_blocks_list):
        result = False
        try:
            stream_blocks = stream_blocks_list
            if type(stream_blocks_list) == list:
                stream_blocks = ' '.join(stream_blocks_list)
            self.stc.perform("StreamBlockStartCommand", StreamBlockList=stream_blocks)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def stop_traffic_stream(self, stream_blocks_list):
        result = False
        try:
            stream_blocks = stream_blocks_list
            if type(stream_blocks_list) == list:
                stream_blocks = ' '.join(stream_blocks_list)
            self.stc.perform("StreamBlockStopCommand", StreamBlockList=stream_blocks)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_results(self, config_type, result_type):
        pass

    def get_stream_results(self):
        pass

    def get_diffserv_results(self):
        pass

    def refresh_results(self, result_data_set):
        try:
            self.stc.perform("RefreshResultView", ResultDataSet=result_data_set)
        except Exception as ex:
            fun_test.critical(str(ex))
        return True

    def save_tcc_configuration(self, tcc_config_file_path):
        result = False
        try:
            self.stc.perform("SaveToTcc", config=self.SYSTEM_OBJECT, filename=(tcc_config_file_path))
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def unsubsribe_results(self, result_data_set):
        result = False
        try:
            self.stc.unsubscribe(result_data_set)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def disconnect_session(self, terminate=True):
        result = False
        try:
            self.stc.perform("CSTestSessionDisconnect", Terminate=terminate)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def disconnect_lab_server(self):
        result = False
        try:
            self.stc.perform("CSServerDisconnect")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def load_tcc_configuration(self, tcc_config_file_path):
        result = False
        try:
            fun_test.debug("Loading TCC configuration %s" % tcc_config_file_path)
            result = self.stc.perform("LoadFromDatabaseCommand", DatabaseConnectionString=tcc_config_file_path)
            self.apply_configuration()
            if result['State'] != "COMPLETED":
                raise FunTestLibException("Unable to load TCC Config ")
            result = True
        except Exception as ex:
            fun_test.critical("Error while loading TCC config: %s" % str(ex))
        return result

    def get_project_handle(self):
        try:
            if not self.project_handle:
                self.project_handle = self.stc.get(self.SYSTEM_OBJECT, "children-project")
            fun_test.debug("Spirent Project: %s" % self.project_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return self.project_handle

    def get_port_list(self):
        ports = None
        try:
            ports = self.stc.get(self.project_handle, "children-port").split()
            fun_test.debug("List of ports: %s" % ports)
        except Exception as ex:
            fun_test.critical(str(ex))
        return ports

    def get_stream_parameters(self, stream_block_handle):
        stream_dict = {}
        try:
            stream_dict = self.stc.get(stream_block_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return stream_dict

    def update_stream_block(self, stream_block_handle, update_attributes):
        result = False
        try:
            fun_test.debug("Updating %s stream parameters: %s " % (stream_block_handle, update_attributes))
            self.stc.config(stream_block_handle, **update_attributes)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_port_location(self, port_handle, chassis_type, slot_no=2, port_no=1):
        result = False
        try:
            location = "//%s/%s/%s" % (self.chassis_ip, slot_no, port_no)
            self.stc.config(port_handle, Location=location)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_object_children(self, handle):
        children = None
        try:
            result = self.stc.get(handle, "children")
            if result:
                children = result.split()
        except Exception as ex:
            fun_test.critical(str(ex))
        return children

    def get_generator(self, port_handle):
        # Generator object is a child of Port object
        generator_handle = None
        try:
            generator_handle = self.stc.get(port_handle, "children-Generator")
        except Exception as ex:
            fun_test.critical(str(ex))
        return generator_handle

    def get_generator_config(self, generator_handle):
        generator_config = None
        try:
            generator_config = self.stc.get(generator_handle, "children-GeneratorConfig")
        except Exception as ex:
            fun_test.critical(str(ex))
        return generator_config

    def update_generator_config(self, generator_config_handle, attributes):
        result = False
        try:
            fun_test.debug("updating %s generator config %s" % (generator_config_handle, attributes))
            self.stc.config(generator_config_handle, **attributes)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def run_stream_block_active_command(self, stream_block_handles, activate=True):
        result = False
        try:
            if type(stream_block_handles) == list:
                stream_block_handles = ' '.join(stream_block_handles)
            output = self.stc.perform("StreamBlockActivateCommand", Activate=activate,
                                      StreamBlockList=stream_block_handles)
            if self.apply_configuration() and output['State'] == "COMPLETED":
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_generator_command(self, generator_handles):
        result = False
        try:
            output = self.stc.perform("GeneratorStartCommand", GeneratorList=generator_handles)
            if output['State'] == "COMPLETED":
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def stop_generator_command(self, generator_handles):
        result = False
        try:
            output = self.stc.perform("GeneratorStopCommand", GeneratorList=generator_handles)
            if output['State'] == "COMPLETED":
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_object_parent(self, handle):
        parent = None
        try:
            result = self.stc.get(handle, "parent")
            fun_test.simple_assert(result, "Fetch parents of object handle %s" % handle)
            parent = result.split()
        except Exception as ex:
            fun_test.critical(str(ex))
        return parent

    def get_generator_port_results(self, generator_handle):
        result = {}
        port_result_handle = None
        try:
            port_result_handle = self.stc.get(generator_handle, "children-GeneratorPortResults")
            fun_test.simple_assert(port_result_handle, "Get generator port results handle")
            result = self.stc.get(port_result_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def refresh_result_view(self, view_handle):
        result = False
        try:
            output = self.stc.perform("RefreshResultView", resultDataSet=view_handle)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Check state of Refresh View command")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def subscribe_results(self, parent, config_type, result_type):
        result_handle = None
        try:
            result_handle = self.stc.subscribe(Parent=parent, ConfigType=config_type, resulttype=result_type)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def unsubscribe_results(self, result_handle):
        result = False
        try:
            output = self.stc.unsubscribe(result_handle)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Unsubscribe results")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_result_query(self, subscribe_handle, result_root_list, config_class_id="StreamBlock",
                            result_class_id="RxStreamBlockResults"):
        result = False
        try:
            output = self.stc.create("ResultQuery", under=subscribe_handle, ResultRootList=result_root_list,
                                     ConfigClassId=config_class_id, ResultClassId=result_class_id)
            fun_test.simple_assert(output, "Result query handle")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_tx_stream_block_results(self, stream_block_handle, subscribe_handle):
        result = {}
        try:
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile("txstreamblockresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == stream_block_handle:
                        result = self.stc.get(output)
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_rx_stream_block_results(self, stream_block_handle, subscribe_handle):
        result = {}
        try:
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile("rxstreamblockresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == stream_block_handle:
                        result = self.stc.get(output)
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_rx_port_analyzer_results(self, port_handle, subscribe_handle):
        result = {}
        try:
            analyzer_handle = self.stc.get(port_handle, "children-Analyzer")
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile("analyzerportresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == analyzer_handle:
                        result = self.stc.get(output)
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def clear_all_port_results(self, port_list):
        result = False
        try:
            output = self.stc.perform("ResultsClearAllCommand", PortList=port_list)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Check status of clear port results command")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def clear_results_view_command(self, result_dataset=None, result_list=None):
        result = False
        output = {}
        output['State'] = None
        try:
            if result_dataset:
                output = self.stc.perform("ResultsClearViewCommand", ResultDataSet=result_dataset)
            else:
                output = self.stc.perform("ResultsClearViewCommand", ResultList=result_list)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Check Clear Result view command status")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def delete_objects(self, object_handle_list):
        result = False
        try:
            output = self.stc.perform("DeleteCommand", ConfigList=object_handle_list)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Delete objects")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


if __name__ == "__main__":
    stc_manager = SpirentManager()
    # stc_manager.connect_lab_server()
    stc_manager.connect_license_manager()