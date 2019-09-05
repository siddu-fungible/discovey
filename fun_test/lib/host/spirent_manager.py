from lib.system.fun_test import *
from fun_settings import *
from lib.system.utils import parse_file_to_json
from lib.utilities.StcPython import StcPython
import re
import inspect


class SpirentManager(object):
    SPIRENT_HOSTS_SPEC = ASSET_DIR + "/traffic_generator_hosts.json"
    SYSTEM_OBJECT = "system1"
    ETHERNET_COPPER_INTERFACE = "EthernetCopper"
    ETHERNET_10GIG_FIBER_INTERFACE = "Ethernet10GigFiber"
    ETHERNET_100GIG_FIBER_INTERFACE = "Ethernet100GigFiber"
    ETHERNET_25GIG_FIBER_INTERFACE = "Ethernet25GigFiber"
    ETHERNET_40GIG_FIBER_INTERFACE = "Ethernet40GigFiber"
    SPEED_100G = "SPEED_100G"
    SPEED_25G = "SPEED_25G"
    SPEED_40G = "SPEED_40G"
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
    DUT_INTERFACE_MODE = "interface_mode"
    MODULE_STATUS_UP = "MODULE_STATUS_UP"
    MODULE_SYNC_STATUS = "MODULE_IN_SYNC"
    OWNERSHIP_STATE_AVAILABLE = "OWNERSHIP_STATE_AVAILABLE"
    LINK_STATUS_UP = "LINK_STATUS_UP"
    RESULT_VIEW_MODE_JITTER = "JITTER"
    RESULT_VIEW_MODE_BASIC = "BASIC"
    TIMED_REFRESH_RESULT_VIEW_MODE = "PERIODIC"
    HOST_CONFIG = {}

    def __init__(self, spirent_config, chassis_type=VIRTUAL_CHASSIS_TYPE):
        self._read_spirent_config()
        try:
            stc_private_install_dir = fun_test.get_environment_variable(variable="STC_PRIVATE_INSTALL_DIR")
            if not stc_private_install_dir:
                # raise FunTestLibException("STC install directory not found. Please export STC_PRIVATE_INSTALL_DIR.")
                os.environ['STC_PRIVATE_INSTALL_DIR'] = self.HOST_CONFIG['hosts']['spirent_private_install_dir']
                os.environ['SPIRENTD_LICENSE_FILE'] = self.HOST_CONFIG['hosts']['license_server_ip']
            self.stc = StcPython()
        except Exception as ex:
            raise FunTestLibException("Unable to initialized Spirent Manager: %s" % str(ex))
        self.project_handle = None
        self.chassis_type = chassis_type
        self.spirent_config = spirent_config
        # self.chassis_ip = self._get_chassis_ip_by_chassis_type()
        self.chassis_ip = None  # After dut_spirent_map change we don't need to use this

    def health(self, session_name="TestSession"):
        health_result = {"result": False, "error_message": None}
        fun_test.debug("Determining health of Spirent Application and Lab Server. Checking availability of ports")
        try:
            if self.spirent_config['connect_via_lab_server']:
                fun_test.test_assert(self.get_api_version(), "Get STC API Version")
                fun_test.test_assert(self.connect_lab_server(session_name=session_name), "Connect to Lab Server")
                fun_test.test_assert(self.connect_license_manager(), "Connect to License Server")
            health_result['result'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return health_result

    def get_test_module_info(self, chassis_ip):
        module_list = []
        chassis_info = {}
        port_group_list = []
        port_list = []
        try:
            if not self.connect_chassis(chassis_ip=chassis_ip):
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
                ip_address = self.HOST_CONFIG['hosts']['physical_chassis_ip']
            else:
                ip_address = self.HOST_CONFIG['hosts']['virtual_chassis_ip']
        except Exception as ex:
            fun_test.critical(str(ex))
        return ip_address

    def connect_chassis(self, chassis_ip):
        result = False
        try:
            self.stc.connect(str(chassis_ip))
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
            self.HOST_CONFIG['hosts'] = spirent_config
        except Exception as ex:
            fun_test.critical(str(ex))
        return self.HOST_CONFIG

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
            self.stc.perform("CSTestSessionConnect", host=self.HOST_CONFIG['hosts']['lab_server_ip'],
                             TestSessionName=session_name,
                             CreateNewTestSession=True)
            self.stc.perform("TerminateBll", TerminateType="ON_LAST_DISCONNECT")
            fun_test.debug("Connected to Lab Server: %s" % self.HOST_CONFIG['hosts']['lab_server_ip'])
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def connect_license_manager(self):
        result = False
        try:
            license_manager = self.stc.get(self.SYSTEM_OBJECT, "children-licenseservermanager")
            output = self.stc.create("LicenseServer", under=license_manager, server=self.HOST_CONFIG['hosts']['license_server_ip'])
            fun_test.simple_assert(output, "Connect to License Server: %s" % self.HOST_CONFIG['hosts']['license_server_ip'])
            fun_test.debug("Connected to License Server: %s" % self.HOST_CONFIG['hosts']['license_server_ip'])
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

    def create_frame_length_distribution(self):
        frame_length_dist_handle = None
        try:
            under = self.project_handle
            frame_length_dist_handle = self.stc.create("FrameLengthDistribution", under=under)
        except Exception as ex:
            fun_test.critical(str(ex))
        return frame_length_dist_handle

    def create_port(self, location, use_default_host=False, apply_config=False):
        port = None
        try:
            if not self.project_handle:
                raise Exception("Please Create Project First")
            port = self.stc.create('port', under=self.project_handle, location=location,
                                   useDefaultHost=use_default_host)
            if apply_config:
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

    def create_physical_interface(self, port_handle, interface_type, attributes):
        result = None
        try:
            fun_test.debug("Creating %s Interface on %s port" % (interface_type, port_handle))
            result = self.stc.create(interface_type, under=port_handle, **attributes)
            fun_test.simple_assert(result, "Create Physical Interface")
            self.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def update_physical_interface(self, interface_handle, update_attributes):
        result = False
        try:
            fun_test.debug("Updating %s interface parameters: %s " % (interface_handle, update_attributes))
            self.stc.config(interface_handle, **update_attributes)

            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def attach_ports(self, port_list, auto_connect=True, revoke_user=True):
        result = False
        try:
            self.stc.perform("attachPorts", portList=port_list, autoConnect=auto_connect, RevokeOwner=revoke_user)
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

    def configure_mac_address(self, streamblock, destination_mac, source_mac=None,  ethernet_type='0800',
                              frame_type=ETHERNETII_FRAME):
        result = False
        try:
            fun_test.debug("Adding Mac Address for %s Stream" % str(streamblock))
            handles = self.get_object_children(streamblock)
            ethernet_handle = None
            for handle in handles:
                if re.search(r'ethernet.*', handle, re.IGNORECASE):
                    fun_test.log("Handle Fetched: %s" % handle)
                    ethernet_handle = handle
                    break
            if source_mac:
                self.stc.config(ethernet_handle, srcMac=source_mac, dstMac=destination_mac, etherType=ethernet_type)
            else:
                self.stc.config(ethernet_handle, dstMac=destination_mac, etherType=ethernet_type)
            # self.stc.create(frame_type, under=streamblock, srcMac=source_mac, dstMac=destination_mac,
            #                etherType=ethernet_type)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_ip_address(self, streamblock, destination, source=None, gateway=None, ip_version=IP_VERSION_4):
        result = False
        try:
            handles = self.get_object_children(handle=streamblock)
            ip_handle = None
            for handle in handles:
                if re.search(r'ip.*', handle, re.IGNORECASE):
                    fun_test.log("Handle Fetched: %s" % handle)
                    ip_handle = handle
                    break
            if gateway:
                self.stc.config(ip_handle, sourceAddr=source, destAddr=destination, gateway=gateway)
            else:
                if source:
                    self.stc.config(ip_handle, sourceAddr=source, destAddr=destination)
                else:
                    self.stc.config(ip_handle, destAddr=destination)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_frame_stack(self, stream_block_handle, header_obj, update=False, delete_header=[]):
        result = False
        try:
            attributes = header_obj.get_attributes_dict()
            fun_test.debug("Configuring %s header under %s" % (header_obj.HEADER_TYPE, stream_block_handle))
            if not update:
                if delete_header:
                    existing_headers = self.get_object_children(handle=stream_block_handle)
                    fun_test.log("Headers found in %s: %s" % (stream_block_handle, existing_headers))
                    for header in delete_header:
                        for handle in existing_headers:
                            if header.lower() in handle:
                                fun_test.log("Deleting Header: %s" % handle)
                                self.delete_handle(handle=handle)
                handle = self.stc.create(header_obj.HEADER_TYPE, under=stream_block_handle, **attributes)
            else:
                child = header_obj.HEADER_TYPE.lower()
                child_type = 'children-' + child
                new_handle = self.get_object_children(stream_block_handle, child_type=child_type)[0]
                handle = self.stc.config(new_handle, **attributes)
            if handle:
                header_obj._spirent_handle = handle
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def delete_frame_headers(self, header_types, stream_block_handle):
        result = False
        try:
            headers = self.get_object_children(handle=stream_block_handle)
            fun_test.debug("Headers found in %s: %s" % (stream_block_handle, headers))
            for header in header_types:
                for handle in headers:
                    if header.lower() in handle:
                        fun_test.log("Deleting Header: %s" % handle)
                        self.delete_handle(handle=handle)
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
            self.apply_configuration()
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

    def get_stream_handle_list(self, port_handle):
        stream_handles = []
        try:
            stream_handles = self.stc.get(port_handle, "children-streamblock")
            stream_handles = stream_handles.split(' ')
        except Exception as ex:
            fun_test.critical(str(ex))
        return stream_handles

    def update_object_attributes(self, object_handle, update_attributes):
        result = False
        try:
            fun_test.debug("Updating %s stream parameters: %s " % (object_handle, update_attributes))
            self.stc.config(object_handle, **update_attributes)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

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

    def get_streamblock_frame_config(self, streamblock_handle):
        result = None
        try:
            output = self.stc.get(streamblock_handle)
            if output:
                result = output['FrameConfig']
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

    def get_object_children(self, handle, child_type=None):
        children = None
        try:
            if not child_type:
                child_type = "children"
            result = self.stc.get(handle, child_type)
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

    def get_analyzer(self, port_handle):
        # Generator object is a child of Port object
        analyzer_handle = None
        try:
            analyzer_handle = self.stc.get(port_handle, "children-Analyzer")
        except Exception as ex:
            fun_test.critical(str(ex))
        return analyzer_handle

    def get_generator_config(self, generator_handle):
        generator_config = None
        try:
            generator_config = self.stc.get(generator_handle, "children-GeneratorConfig")
        except Exception as ex:
            fun_test.critical(str(ex))
        return generator_config

    def get_analyzer_config(self, analyzer_handle):
        analyzer_config = None
        try:
            analyzer_config = self.stc.get(analyzer_handle, "children-AnalyzerConfig")
        except Exception as ex:
            fun_test.critical(str(ex))
        return analyzer_config

    def update_handle_config(self, config_handle, attributes):
        result = False
        try:
            fun_test.debug("updating %s generator config %s" % (config_handle, attributes))
            self.stc.config(config_handle, **attributes)
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
            self.apply_configuration()
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

    def get_generator_port_results(self, port_handle, subscribe_handle):
        result = {}
        try:
            generator_handle = self.stc.get(port_handle, "children-Generator")
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile("generatorportresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == generator_handle:
                        self.refresh_result_view(output)
                        result = self.stc.get(output)
                        break
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

    def subscribe_results(self, parent, config_type, result_type, change_mode=False,
                          result_view_mode=RESULT_VIEW_MODE_JITTER,
                          timed_refresh_result_view_mode=TIMED_REFRESH_RESULT_VIEW_MODE,
                          view_attribute_list=None, result_parent=None):
        result_handle = None
        try:
            if change_mode:
                result_options_handle = self.stc.get(parent, "children-ResultOptions")
                self.stc.config(result_options_handle, ResultViewMode=result_view_mode,
                                TimedRefreshResultViewMode=timed_refresh_result_view_mode, TimedRefreshInterval="1")
            if view_attribute_list:
                attributes = ' '.join(view_attribute_list)
                if result_parent:
                    result_handle = self.stc.subscribe(Parent=parent, ResultParent=result_parent,
                                                       ConfigType=config_type, resulttype=result_type,
                                                       viewAttributeList=attributes)
                else:
                    result_handle = self.stc.subscribe(Parent=parent, ConfigType=config_type, resulttype=result_type,
                                                       viewAttributeList=attributes)
            else:
                if result_parent:
                    result_handle = self.stc.subscribe(Parent=parent, ConfigType=config_type, resulttype=result_type,
                                                       ResultParent=result_parent)
                else:
                    result_handle = self.stc.subscribe(Parent=parent, ConfigType=config_type, resulttype=result_type)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_handle

    def unsubscribe_results(self, result_handle):
        result = False
        try:
            self.stc.unsubscribe(result_handle)
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

    def get_tx_stream_block_results(self, stream_block_handle, subscribe_handle, summary=False, refresh=True):
        result = {}
        try:
            tx_stream_str = "txstreamblockresults."
            if summary:
                tx_stream_str = "txstreamresults."
            if refresh:
                fun_test.debug("Refresh result view for handle %s" % subscribe_handle)
                refresh_view = self.refresh_result_view(subscribe_handle)
                fun_test.simple_assert(refresh_view, "Refresh result view")
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile(tx_stream_str)
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == stream_block_handle:
                        result = self.stc.get(output)
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_rx_stream_block_results(self, stream_block_handle, subscribe_handle, summary=False, refresh=True):
        result = {}
        try:
            rx_stream_str = "rxstreamblockresults."
            if summary:
                rx_stream_str = "rxstreamsummaryresults."
            if refresh:
                fun_test.debug("Refresh result view for handle %s" % subscribe_handle)
                refresh_view = self.refresh_result_view(subscribe_handle)
                fun_test.simple_assert(refresh_view, "Refresh result view")
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile(rx_stream_str)
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
                        self.refresh_result_view(output)
                        result = self.stc.get(output)
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_port_pfc_results(self, port_handle, subscribe_handle):
        result = {}
        try:
            analyzer_handle = self.stc.get(port_handle, "children-Analyzer")
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile("pfcportresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == analyzer_handle:
                        result = self.stc.get(output)
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_port_diffserv_results(self, port_handle, subscribe_handle):
        result = {}
        try:
            analyzer_handle = self.stc.get(port_handle, "children-Analyzer")
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            fun_test.simple_assert(res_handle_list is not None, "Result handle list is found ofr diff serv result on port %s" % port_handle)
            for output in res_handle_list:
                regex = re.compile("diffservresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == analyzer_handle:
                        qos_val = self.stc.get(output)['QosBinary']
                        result[qos_val] = self.stc.get(output)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_port_filtered_results(self, port_handle, subscribe_handle):
        result = []
        try:
            analyzer_handle = self.stc.get(port_handle, "children-Analyzer")
            self.stc.perform("RefreshResultView", ResultDataSet=subscribe_handle)
            res_handle_list = self.stc.get(subscribe_handle, "ResultHandleList").split()
            for output in res_handle_list:
                regex = re.compile("filteredstreamresults.")
                if re.match(regex, output):
                    parent = self.stc.get(output, "parent")
                    if parent == analyzer_handle:
                        result.append(self.stc.get(output))
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

    def delete_handle(self, handle):
        result = False
        try:
            self.stc.delete(handle=handle)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_pfc_header(self, header_obj, stream_block_handle, class_enable_vector=False,
                             ls_octet="00000000", ms_octet="00000000", update=False):
        result = None
        try:
            attributes = header_obj.get_attributes_dict()
            fun_test.debug("Configuring %s header under %s" % (header_obj.HEADER_TYPE, stream_block_handle))
            if not update:
                header_created = self.stc.create(header_obj.HEADER_TYPE, under=stream_block_handle, **attributes)
                fun_test.simple_assert(header_created, "header created")
                handle = self.stc.get(header_created, "Handle")
                header_obj._spirent_handle = handle
                if class_enable_vector and handle:
                    output = self.stc.create("classEnableVector", under=handle, lsOctet=ls_octet, msOctet=ms_octet)
                    fun_test.simple_assert(output, "Configure Class Enable Vector for %s" % header_obj._spirent_handle)
            else:
                header_type = header_obj.HEADER_TYPE.lower()
                child_type = 'children-' + header_type
                header_handle = self.get_object_children(stream_block_handle, child_type=child_type)[0]
                self.stc.config(header_handle, **attributes)
                fun_test.log('Updated pfc header attributes on streamblock %s' % stream_block_handle)
                if class_enable_vector:
                    new_header_handle = self.get_object_children(stream_block_handle, child_type=child_type)[0]
                    header_child_handle = self.get_object_children(new_header_handle)[0]
                    self.stc.config(header_child_handle, msOctet=ms_octet, lsOctet=ls_octet)
                    fun_test.log('Updated class enabled vector attributes on streamblock %s' % stream_block_handle)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def fetch_streamblock_results(self, subscribe_result, streamblock_handle_list=[], tx_result=False, rx_result=False,
                                  tx_stream_result=False, rx_summary_result=False):
        result = {}
        try:
            for streamblock_handle in streamblock_handle_list:
                result[streamblock_handle] = {}

                if tx_result:
                    output = self.get_tx_stream_block_results(streamblock_handle, subscribe_result['tx_subscribe'])
                    result[streamblock_handle]['tx_result'] = output
                    fun_test.log("Fetched tx_result for stream %s" % streamblock_handle)
                if tx_stream_result:
                    output = self.get_tx_stream_block_results(streamblock_handle,
                                                              subscribe_result['tx_stream_subscribe'],
                                                              summary=True)
                    result[streamblock_handle]['tx_stream_result'] = output
                    fun_test.log("Fetched tx_stream_result for stream %s" % streamblock_handle)
                if rx_result:
                    output = self.get_rx_stream_block_results(streamblock_handle, subscribe_result['rx_subscribe'])
                    result[streamblock_handle]['rx_result'] = output
                    fun_test.log("Fetched rx_result for stream %s" % streamblock_handle)
                if rx_summary_result:
                    output = self.get_rx_stream_block_results(streamblock_handle,
                                                              subscribe_result['rx_summary_subscribe'], summary=True)
                    result[streamblock_handle]['rx_summary_result'] = output
                    fun_test.log("Fetched rx_summary_result for stream %s" % streamblock_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def fetch_port_results(self, subscribe_result, port_handle_list=[], generator_result=False, analyzer_result=False,
                           pfc_result=False, diff_serv_result=False):
        result = {}
        try:
            for port_handle in port_handle_list:
                result[port_handle] = {}
                if generator_result:
                    output = self.get_generator_port_results(port_handle, subscribe_result['generator_subscribe'])
                    result[port_handle]['generator_result'] = output
                    fun_test.log("Fetched generator_result for port %s" % port_handle)
                if analyzer_result:
                    output = self.get_rx_port_analyzer_results(port_handle, subscribe_result['analyzer_subscribe'])
                    result[port_handle]['analyzer_result'] = output
                    fun_test.log("Fetched analyzer_result for port %s" % port_handle)
                if pfc_result:
                    output = self.get_port_pfc_results(port_handle, subscribe_result['pfc_subscribe'])
                    result[port_handle]['pfc_result'] = output
                    fun_test.log("Fetched pfc_result for port %s" % port_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_capture(self, capture_obj, port_handle):
        result = False
        try:
            capture_handle = self.get_object_children(port_handle,child_type='children-capture')
            capture_obj._spirent_handle = capture_handle[0]
            update_attributes = capture_obj.get_attributes_dict()
            self.stc.config(capture_obj._spirent_handle, **update_attributes)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_capture_command(self, capture_obj, port_handle, real_time_decoder_location="", real_time_host_name='127.0.0.1',
                              real_time_tcp_port='2006'):
        result = False
        try:
            output = self.configure_capture(capture_obj, port_handle)
            fun_test.simple_assert(output, "Configuring capture on port %s" % port_handle)
            fun_test.log("Starting capture start command")
            output = self.stc.perform("CaptureStartCommand", CaptureProxyId=capture_obj._spirent_handle,
                                      RealTimeDecoderLocation=real_time_decoder_location,
                                      RealTimeHostName=real_time_host_name,
                                      RealTimeTcpPort=real_time_tcp_port)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Start capture")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def stop_capture_command(self, capture_handle):
        result = False
        try:
            output = self.stc.perform("CaptureStopCommand", CaptureProxyId=capture_handle)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Stop capture")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def save_capture_data_command(self, capture_handle, file_name, file_name_path, append_suffix_to_file_name=False,
                                  end_frame_index='0', file_name_format='PCAP', start_frame_index='0'):

        result = False
        try:
            output = self.stc.perform("CaptureDataSaveCommand", CaptureProxyId=capture_handle,
                                      AppendSuffixToFileName=append_suffix_to_file_name, EndFrameIndex=end_frame_index,
                                      FileName=file_name, FileNamePath=file_name_path, FileNameFormat=file_name_format,
                                      StartFrameIndex=start_frame_index)
            fun_test.simple_assert(output['State'] == "COMPLETED", "Saved capture %s at path %s" %
                                   (file_name, file_name_path))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_range_modifier(self, range_modifier_obj, streamblock_obj, header_obj, header_attribute, overlay=False,
                                 custom_header=False):
        result = False
        header_handle = None
        assigned_header_name = None
        try:
            attributes = header_obj.__dict__.keys()
            fun_test.simple_assert(header_attribute in attributes, "Attribute %s not found in header obj %s. "
                                                                   "Available values are %s" % (header_attribute,
                                                                                                header_obj, attributes))
            header_type = header_obj.HEADER_TYPE.lower()
            header_type = 'children-' + header_type
            header_list = self.get_object_children(handle=streamblock_obj._spirent_handle, child_type=header_type)
            header_handle = header_list[0]
            if overlay and len(header_list) > 1:
                header_handle = header_list[1]
            elif custom_header:
                header_handle = header_list[-1]
            fun_test.simple_assert(header_handle, "Header handle not found for header %s in streamblock %s"
                                   % (header_obj.HEADER_TYPE, streamblock_obj._spirent_handle))
            range_attributes = range_modifier_obj.get_attributes_dict()
            assigned_header_name = self.stc.get(header_handle, "name")
            fun_test.simple_assert(assigned_header_name, "Header name not found for %s" % header_handle)
            range_attributes['OffsetReference'] = assigned_header_name + '.' + header_attribute
            output = self.stc.create(range_modifier_obj.HEADER_TYPE, under=streamblock_obj._spirent_handle,
                                     **range_attributes)
            fun_test.simple_assert(output, "range modifier not created")
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def update_header_options(self, header_obj, option_obj, stream_block_handle):
        result = False
        try:
            header_handles = self.get_object_children(handle=stream_block_handle)
            for header_handle in header_handles:
                if re.search(header_obj.HEADER_TYPE, header_handle, re.IGNORECASE):
                    attributes = option_obj.get_attributes_dict()
                    options_handle = self.get_object_children(handle=header_handle)[2]
                    new_options_handle = self.stc.create(option_obj.PARENT_HEADER_OPTION, under=options_handle)
                    self.stc.create(option_obj.OPTION_TYPE, under=new_options_handle, **attributes)
                    break
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def update_control_flags(self, stream_block_obj, header_obj, df_bit=0, mf_bit=0, reserved=0):
        result = False
        try:
            header_handles = self.get_object_children(handle=stream_block_obj.spirent_handle)
            for header_handle in header_handles:
                if re.search(header_obj.HEADER_TYPE, header_handle, re.IGNORECASE):
                    flags_handle = self.get_object_children(handle=header_handle)[1]
                    handle = self.stc.config(flags_handle, dfBit=df_bit, mfBit=mf_bit, reserved=reserved)
                    break
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def detach_ports_by_command(self, port_handles):
        result = False
        try:
            if type(port_handles) == list:
                port_handles = ' '.join(port_handles)
            fun_test.debug("Releasing %s from project" % port_handles)
            output = self.stc.perform("DetachPortsCommand", PortList=port_handles)
            fun_test.simple_assert(output['State'] == 'COMPLETED', "%s detached" % port_handles)
            if re.search(r'Successfully\s+detached.*', output['Status'], re.IGNORECASE):
                fun_test.log("%s released successfully" % port_handles)
                if self.apply_configuration():
                    result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def attach_ports_by_command(self, port_handles, auto_connect_chassis=True, revoke_user=True):
        result = False
        try:
            if type(port_handles) == list:
                port_handles = ' '.join(port_handles)
            fun_test.debug("Releasing %s from project" % port_handles)
            output = self.stc.perform("AttachPortsCommand", PortList=port_handles, AutoConnect=auto_connect_chassis,
                                      RevokeOwner=revoke_user)
            fun_test.simple_assert(output['State'] == 'COMPLETED', "%s attached" % port_handles)
            if re.search(r'Reserving.*.*', output['Status'], re.IGNORECASE):
                if self.apply_configuration():
                    result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_sequencer(self):
        is_started = False
        try:
            fun_test.debug("Starting Sequencer...")
            result = self.stc.perform("SequencerStart")
            if result['State'] == 'COMPLETED':
                is_started = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return is_started

    def stop_sequencer(self):
        is_stopped = False
        try:
            fun_test.debug("Stopping Sequencer...")
            result = self.stc.perform("SequencerStop")
            if result['State'] == 'COMPLETED':
                is_stopped = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return is_stopped

    def wait_until_complete(self):
        return self.stc.waitUntilComplete()

    def get_sequencer_handles(self):
        handles= None
        try:
            fun_test.debug("Fetching Sequencer Handle")
            handles = self.get_object_children(handle=self.SYSTEM_OBJECT, child_type="children-sequencer")
            fun_test.simple_assert(handles, "Fetch Sequencer Handle")
        except Exception as ex:
            fun_test.critical(str(ex))
        return handles

    def get_sequencer_config(self, handle):
        config = None
        try:
            fun_test.debug("Fetching Sequencer Config")
            config = self.stc.get(handle)
            fun_test.simple_assert(config, "Fetch Sequencer Config")
        except Exception as ex:
            fun_test.critical(str(ex))
        return config

    def get_test_result_setting_handles(self):
        handles = None
        try:
            fun_test.debug("Fetching TestResultSetting handle")
            handles = self.get_object_children(handle=self.project_handle, child_type="children-TestResultSetting")
            fun_test.simple_assert(handles, "Fetch TestResultSetting Handle")
        except Exception as ex:
            fun_test.critical(str(ex))
        return handles

    def get_test_result_setting_config(self, test_result_handle):
        config = None
        try:
            fun_test.debug("Fetching TestResultSetting Config")
            config = self.stc.get(test_result_handle)
            fun_test.simple_assert(config, "Fetch TestResultSetting Config")
        except Exception as ex:
            fun_test.critical(str(ex))
        return config

    def perform_query_result_command(self, result_db_name, result_path):
        result = None
        try:
            fun_test.debug("Fetching Query Result")
            result = self.stc.perform("QueryResult", DatabaseConnectionString=result_db_name, ResultPath=result_path)
            fun_test.simple_assert(result, "Fetch Query Result")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def update_test_result_directory(self, test_result_handle, dir_name):
        result = False
        try:
            fun_test.debug("Changing TestResult directory to %s" % dir_name)
            self.stc.config(test_result_handle, SaveResultsRelativeTo=dir_name)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_rfc2544_group_commands(self, sequencer_handle, command_type):
        group_commands = []
        try:
            group_commands = self.get_object_children(handle=sequencer_handle,
                                                      child_type=command_type)
            fun_test.debug("RFC-2544 Group Commands: %s" % group_commands)
        except Exception as ex:
            fun_test.critical(str(ex))
        return group_commands

    def get_rfc2544_throughput_config(self, handle):
        config = {}
        try:
            config = self.stc.get(handle)
            fun_test.debug(config)
        except Exception as ex:
            fun_test.critical(str(ex))
        return config

    def configure_rfc2544_throughput_config(self, handle, attributes):
        result = False
        try:
            self.stc.config(handle, **attributes)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def configure_speed_config(self, interface_handle, line_speed, auto_negotiation=False,
                               forward_error_correction=False):
        result = False
        try:
            self.stc.config(interface_handle, linespeed=line_speed, AutoNegotiation=auto_negotiation,
                            ForwardErrorCorrection=forward_error_correction)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_interface_handle(self, port_handle, interface_type):
        handle = None
        try:
            children = self.get_object_children(handle=port_handle)
            for child in children:
                if interface_type.lower() in child:
                    fun_test.debug(child)
                    handle = child
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return handle

    def get_interface_details(self, interface_handle):
        result = {}
        try:
            result = self.stc.get(interface_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_activephy_targets_under_port(self, port_handle):
        result = None
        try:
            result = self.stc.get(port_handle, 'activephy-Targets')
            fun_test.debug(result)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_fec_status(self, handle):
        status = None
        try:
            status = self.stc.get(handle, 'ForwardErrorCorrection')
        except Exception as ex:
            fun_test.critical(str(ex))
        return status

    def get_auto_negotiation_status(self, handle):
        status = None
        try:
            status = self.stc.get(handle, 'AutoNegotiation')
        except Exception as ex:
            fun_test.critical(str(ex))
        return status

    def get_interface_link_status(self, handle):
        status = None
        try:
            status = self.stc.get(handle, 'LinkStatus')
        except Exception as ex:
            fun_test.critical(str(ex))
        return status

    def create_phy_compensation_option(self, interface_handle, compensation_mode):
        result = None
        try:
            result = self.stc.create('PhyCompensationOptions', under=interface_handle,
                                     CompensationMode=compensation_mode)
            fun_test.simple_assert(result, "Create Phy compensation mode under %s" % interface_handle)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_physical_options_under_project(self):
        options = []
        try:
            options = self.stc.get(self.project_handle, 'children-PhyOptions').split()
            fun_test.simple_assert(options, "Ensure Physical options are fetched")
        except Exception as ex:
            fun_test.critical(str(ex))
        return options

    def enable_per_port_latency_compensation_adjustments(self, phy_option, enable_compensation_mode=True):
        result = False
        try:
            self.stc.config(phy_option, EnableCompensationMode=enable_compensation_mode)
            if self.apply_configuration():
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def applyfec(self, port_handle, fec_obj, attributes):
        result = None
        try:
            fun_test.debug("Adding %s FEC on %s port" % (fec_obj, port_handle))
            result = self.stc.create(fec_obj, under=port_handle, **attributes)
            fun_test.simple_assert(result, "Applying FEC settings")
            self.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def update_range_modifier_object(self, streamblock_handle, attributes):
        result = None
        try:
            child = self.get_object_children(streamblock_handle)
            for child_type in child:
                if 'rangemodifier' in child_type:
                    range_modfier_handle = child_type
                    break
            self.stc.config(range_modfier_handle, **attributes)
            self.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


if __name__ == "__main__":
    stc_manager = SpirentManager()
    # stc_manager.connect_lab_server()
    stc_manager.connect_license_manager()