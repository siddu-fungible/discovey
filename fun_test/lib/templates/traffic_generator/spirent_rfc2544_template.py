"""
Author: Rushikesh Pendse

This template is for RFC-2544 Networking performance.
User needs to create .tcc spirent config with the test parameters and RFC-2544 wizard configured
"""
from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from scripts.networking.nu_config_manager import *
import sqlite3
from web.fun_test.analytics_models_helper import ModelHelper
from fun_global import PerfUnit

FLOW_TYPE_NU_NU_NFCP = "NU_NU_NFCP"
FLOW_TYPE_HNU_HNU_NFCP = "HNU_HNU_NFCP"
FLOW_TYPE_HNU_HNU_FCP = "HNU_HNU_FCP"
FLOW_TYPE_HNU_NU_NFCP = "HNU_NU_NFCP"
FLOW_TYPE_NU_HNU_NFCP = "NU_HNU_NFCP"
FLOW_TYPE_NU_VP_NU_FWD_NFCP = "NU_VP_NU_FWD_NFCP"
FLOW_TYPE_NU_LE_VP_NU_FW = "NU_LE_VP_NU_FW"
FLOW_TYPE_NU_LE_VP_NU_L4_FW = "NU_LE_VP_NU_L4_FW"
JUNIPER_PERFORMANCE_MODEL_NAME = "TeraMarkJuniperNetworkingPerformance"
HNU_PERFORMANCE_MODEL_NAME = "NuTransitPerformance"
MEMORY_TYPE_HBM = "HBM"
MEMORY_TYPE_DDR = "DDR"
FLOW_TYPE_FWD = "FWD"
IPSEC_ENCRYPT_MULTI_TUNNEL = "IPSEC_ENCRYPT_MULTI_TUNNEL"
IPSEC_DECRYPT_MULTI_TUNNEL = "IPSEC_DECRYPT_MULTI_TUNNEL"
IPSEC_ENCRYPT_SINGLE_TUNNEL = "IPSEC_ENCRYPT_SINGLE_TUNNEL"
IPSEC_DECRYPT_SINGLE_TUNNEL = "IPSEC_DECRYPT_SINGLE_TUNNEL"


class Rfc2544Template(SpirentEthernetTrafficTemplate):
    USER_WORKING_DIR = "USER_WORKING_DIR"
    FRAME_SIZE_64 = "64.0"
    FRAME_SIZE_66 = "66.0"
    FRAME_SIZE_1500 = "1500.0"
    FRAME_SIZE_800 = "800.0"
    FRAME_SIZE_IMIX = None
    FRAME_SIZE_1000 = "1000.0"
    FRAME_SIZE_9000 = "9000.0"
    FRAME_SIZE_8900 = "8900.0"
    PASSED = "Passed"
    FAILED = "Failed"
    PERFORMANCE_DATA_JSON_FILE = "rfc2544_performance_results.json"
    DUT_MODE_25G = "25G"
    DUT_MODE_50G = "50G"
    DUT_MODE_100G = "100G"
    OUTPUT_JSON_FILE_NAME = "nu_rfc2544_performance.json"

    def __init__(self, spirent_config, session_name="RFC-2544", chassis_type=SpirentManager.PHYSICAL_CHASSIS_TYPE):
        SpirentTrafficGeneratorTemplate.__init__(self, spirent_config=spirent_config,chassis_type=chassis_type)
        self.session_name = session_name
        self.project_handle = None
        self.result_setting_handle = None
        self.result_db_name = None

    def setup(self, tcc_config_path):
        result = {"result": False, "port_list": None}
        try:
            if not self.project_handle:
                self.project_handle = self.stc_manager.create_project(project_name=self.session_name)
                fun_test.test_assert(self.project_handle, "Create %s project" % self.session_name)

            fun_test.test_assert(expression=self.stc_manager.health(session_name=self.session_name)['result'],
                                 message="Check Health of Spirent Application")

            config_file_exists = os.path.exists(tcc_config_path)
            fun_test.test_assert(config_file_exists, "%s config exists" % tcc_config_path)

            config_file_name = os.path.basename(tcc_config_path)

            fun_test.log("Loading %s configuration..." % config_file_name)
            tcc_loaded = self.stc_manager.load_tcc_configuration(tcc_config_file_path=tcc_config_path)
            fun_test.test_assert(tcc_loaded, "%s config loaded" % config_file_name)

            checkpoint = "Get list of ports"
            ports = self.stc_manager.get_port_list()
            fun_test.test_assert(ports, checkpoint)
            result['port_list'] = ports

            # TODO: Create map dict in nuconfigs and check if chassis ip is correct. There will be separate map for RFC-2544
            for port in ports:
                info = self.stc_manager.get_port_details(port=port)
                fun_test.log("Port: %s Spirent Handle: %s" % (info['Location'], port))

            checkpoint = "Connect to Chassis and attached ports"
            port_attached = self.stc_manager.attach_ports_by_command(port_handles=ports)
            fun_test.test_assert(port_attached, checkpoint)

            checkpoint = "Fetch TestResultSetting handle and configure results directory"
            self.result_setting_handle = self.stc_manager.get_test_result_setting_handles()[0]
            result_dir_changed = self.stc_manager.update_test_result_directory(
                test_result_handle=self.result_setting_handle, dir_name=self.USER_WORKING_DIR)
            fun_test.test_assert(result_dir_changed, checkpoint)

            result['result'] = True

        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_sequencer(self):
        is_started = False
        try:
            fun_test.log("Starting Sequencer...")
            is_started = self.stc_manager.start_sequencer()
            fun_test.test_assert(is_started, "Sequencer started")
        except Exception as ex:
            fun_test.critical(str(ex))
        return is_started

    def wait_until_complete(self):
        result = False
        try:
            fun_test.log("Sequencer running... This might take little while")
            status = self.stc_manager.wait_until_complete()
            fun_test.simple_assert(status == 'PASSED', message="Ensure Sequencer stopped")
            fun_test.log("Sequencer Stopped...")
            result = True
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

    def get_interface_mode_input_speed(self):
        interface_mode = None
        try:
            inputs = fun_test.get_job_inputs()
            if 'speed' in inputs:
                speed = inputs['speed']
            else:
                speed = SpirentManager.SPEED_25G
            if speed == SpirentManager.SPEED_100G:
                interface_mode = self.DUT_MODE_100G
            elif speed == SpirentManager.SPEED_25G:
                interface_mode = self.DUT_MODE_25G
        except Exception as ex:
            fun_test.critical(str(ex))
        return interface_mode

    def get_parameters_for_each_stream(self):
        streams_info = {}
        try:
            stream_handles = self.get_throughput_command_handle()
            for stream_handle in stream_handles:
                stream_dict = self.stc_manager.get_stream_parameters(stream_block_handle=stream_handle)
                fun_test.log("----------------------> Stream Info for %s <----------------------" % stream_handle)
                for key, val in stream_dict.items():
                    fun_test.log("%s : %s" % (key, val))
                streams_info[stream_handle] = stream_dict
        except Exception as ex:
            fun_test.critical(str(ex))
        return streams_info

    def _fetch_sequencer_handles(self):
        handles = []
        try:
            handles = self.stc_manager.get_sequencer_handles()
            fun_test.debug(handles)
        except Exception as ex:
            fun_test.critical(str(ex))
        return handles

    def get_sequencer_configuration(self):
        sequencer_config = None
        try:
            sequencer_handle = self._fetch_sequencer_handles()[0]
            sequencer_config = self.stc_manager.get_sequencer_config(handle=sequencer_handle)
            for key, val in sequencer_config.items():
                fun_test.debug("%s : %s" % (key, val))
        except Exception as ex:
            fun_test.critical(str(ex))
        return sequencer_config

    def retrieve_database_file_name(self):
        try:
            config = self.stc_manager.get_test_result_setting_config(test_result_handle=self.result_setting_handle)
            self.result_db_name = config['CurrentResultFileName']
        except Exception as ex:
            fun_test.critical(str(ex))
        return self.result_db_name

    def fetch_summary_result(self, db_name, result_path="RFC2544ThroughputTestResultDetailedSummaryView"):
        records = []
        try:
            summary_result = self.stc_manager.perform_query_result_command(result_db_name=db_name,
                                                                           result_path=result_path)
            fun_test.simple_assert(summary_result, "Ensure Throughput detailed summary fetched")
            records = self._get_list_of_records(summary_result)
            fun_test.debug(records)
        except Exception as ex:
            fun_test.critical(str(ex))
        return records

    def _get_base_db_path(self, db_path):
        base_path = None
        try:
            base_path = '/'.join(db_path.split('/')[:7])
        except Exception as ex:
            fun_test.critical(str(ex))
        return base_path

    def _get_throughput_summary_db_list(self, base_path):
        db_list = []
        try:
            run_dirs = os.listdir(base_path)
            for run_dir in run_dirs:
                if re.search(r'2544-Tput', run_dir.strip()):
                    path = base_path + "/%s" % run_dir
                    dbs = glob.glob(path + "/*.db")
                    for db in dbs:
                        if re.search(r'2544-Tput-Summary', db.strip()):
                            db_list.append(db)
        except Exception as ex:
            fun_test.critical(str(ex))
        return db_list

    def get_throughput_summary_results_by_frame_size(self):
        output = {"status": False}
        result = OrderedDict()
        result[self.FRAME_SIZE_64] = []
        result[self.FRAME_SIZE_1500] = []
        result[self.FRAME_SIZE_800] = []
        result['IMIX'] = []
        result[self.FRAME_SIZE_1000] = []
        result[self.FRAME_SIZE_9000] = []
        try:
            spirent_path = self.retrieve_database_file_name()
            # spirent_path = "/home/rushikesh/Spirent/TestCenter 4.81/Results/nu_hnu_palladium_2ports_2019-01-23_07-08-45/2544-Tput_2019-01-23_07-13-54/2544-Tput-Summary-6_2019-01-23_07-13-54.db"
            base_path = self._get_base_db_path(db_path=spirent_path)
            dbs = self._get_throughput_summary_db_list(base_path=base_path)
            for db in dbs:
                records = self.fetch_summary_result(db_name=db)
                for record in records:
                    data_dict = OrderedDict(record)
                    if 'AvgFrameSize' in data_dict and self.FRAME_SIZE_64 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_64].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_66 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_64].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_1500 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_1500].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_800 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_800].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_1000 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_1000].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_9000 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_9000].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_8900 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_9000].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and data_dict['iMIXDistribution'] == 'Default':
                        result['IMIX'].append(data_dict)
            output['status'] = True
            output['summary_result'] = result
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def validate_result(self, result_dict):
        result = False
        try:
            if self.FRAME_SIZE_64 in result_dict:
                for record in result_dict[self.FRAME_SIZE_64]:
                    fun_test.test_assert_expected(expected=self.PASSED, actual=record['Result'],
                                                  message="Ensure Result for %s frame size trial num: %s" % (
                                                      self.FRAME_SIZE_64, record['TrialNumber']))
            if self.FRAME_SIZE_1500 in result_dict:
                for record in result_dict[self.FRAME_SIZE_1500]:
                    fun_test.test_assert_expected(expected=self.PASSED, actual=record['Result'],
                                                  message="Ensure Result for %s frame size trial num: %s" % (
                                                      self.FRAME_SIZE_1500, record['TrialNumber']))
            if self.FRAME_SIZE_IMIX in result_dict:
                for record in result_dict[self.FRAME_SIZE_IMIX]:
                    fun_test.test_assert_expected(expected=self.PASSED, actual=record['Result'],
                                                  message="Ensure Result for %s frame size trial num: %s" % (
                                                      self.FRAME_SIZE_IMIX, record['TrialNumber']))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_table_data(self, result_dict):
        table_data = {'headers': [], 'rows': []}
        try:
            headers = []
            exclude_header_list = ['UnexpectedRxSignatureFrames', 'MaxLatencyThresholdExceeded', 'FrameLoss',
                                   'FloodFrameCount', 'ConfiguredFrameSize', 'OfferedLoad(fps)', 'FrameSizeType',
                                   'OutOfSeqThresholdExceeded', 'IntendedLoad(Mbps)', 'iMIXDistribution']
            for key in result_dict:
                if result_dict[key]:
                    all_headers = result_dict[key][0].keys()
                    headers = [val for val in all_headers if val not in exclude_header_list]
                    break
            rows = []
            for key in result_dict:
                for record in result_dict[key]:
                    row = []
                    for _key in record.keys():
                        if _key in headers:
                            row.append(record[_key])
                    rows.append(row)
            table_data = {'headers': headers, 'rows': rows}
        except Exception as ex:
            fun_test.critical(str(ex))
        return table_data

    def create_performance_table(self, result_dict, table_name):
        result = False
        try:
            table_data = self._get_table_data(result_dict=result_dict)
            fun_test.add_table(panel_header="RFC-2544 Performance Detailed Summary",
                               table_name=table_name,
                               table_data=table_data)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_list_of_records(self, summary_result):
        records = []
        try:
            columns = summary_result['Columns'].split()
            outputs = re.split(r'}', summary_result['Output'])

            for output in outputs:
                data_list = output.lstrip(' {').split()
                records.append(zip(columns, data_list))
        except Exception as ex:
            fun_test.critical(str(ex))
        return records

    def _calculate_throughput_in_mbps(self, forwarding_rate, frame_size):
        throughput = None
        try:
            throughput = float((forwarding_rate * (frame_size + 8)) * 8 / 1000000)
        except Exception as ex:
            fun_test.critical(str(ex))
        return throughput

    def _get_max_forwarding_rate(self, records, frame_size):
        max_rate_record = None
        try:
            forwarding_rates = []
            for record in records:
                if float(record['AvgFrameSize']) == frame_size:
                    if record['Result'] == self.PASSED:
                        forwarding_rates.append(float(record['ForwardingRate(fps)']))
            if not forwarding_rates:
                fun_test.log("All results failed for %s frame size" % (frame_size))
                return max_rate_record
            else:
                max_rate = max(forwarding_rates)
                for record in records:
                    if max_rate == float(record['ForwardingRate(fps)']):
                        max_rate_record = record
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return max_rate_record

    def _parse_file_to_json_in_order(self, file_name):
        result = None
        try:
            with open(file_name, "r") as infile:
                contents = infile.read()
                result = json.loads(contents, object_pairs_hook=OrderedDict)
        except Exception as ex:
            scheduler_logger.critical(str(ex))
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

    def populate_performance_json_file(self, result_dict, model_name, timestamp, flow_direction, mode=DUT_MODE_25G,
                                       file_name=OUTPUT_JSON_FILE_NAME, protocol="UDP", offloads=False, num_flows=None,
                                       half_load_latency=False, memory=None, update_charts=True, update_json=False,
                                       display_negative_results=False):
        results = []
        output = True
        any_result_failed = False
        try:
            for key in result_dict:
                failed_result_found = False
                records = result_dict[key]
                data_dict = OrderedDict()
                data_dict['mode'] = mode
                data_dict['version'] = fun_test.get_version()
                data_dict['timestamp'] = str(timestamp)
                data_dict['half_load_latency'] = half_load_latency

                if memory:
                    data_dict['memory'] = memory

                frame_size = float(records[0]['AvgFrameSize']) if records else None
                actual_frame_size = frame_size
                if frame_size == 8900.0:
                    frame_size = 9000.0
                elif frame_size == 66.0:
                    frame_size = 64.0
                elif frame_size == 354.94:
                    frame_size = 362.94
                if frame_size:
                    data_dict['flow_type'] = flow_direction
                    data_dict['frame_size'] = frame_size

                    max_rate_record = self._get_max_forwarding_rate(records=records, frame_size=actual_frame_size)
                    if display_negative_results:
                        fun_test.log("Display of negative results flag set to True")
                        data_dict['pps'] = -1
                        data_dict['throughput'] = -1
                        data_dict['latency_min'] = -1
                        data_dict['latency_max'] = -1
                        data_dict['latency_avg'] = -1

                        data_dict['jitter_min'] = -1
                        data_dict['jitter_max'] = -1
                        data_dict['jitter_avg'] = -1
                        failed_result_found = True
                        any_result_failed = True
                    elif max_rate_record:
                        fun_test.log("Max result seen for frame %s" % frame_size)
                        data_dict['pps'] = float(max_rate_record['ForwardingRate(fps)'])
                        #throughput = self._calculate_throughput_in_mbps(forwarding_rate=data_dict['pps'],
                        #                                                frame_size=frame_size)
                        #data_dict['throughput'] = round(throughput, 2)
                        data_dict['throughput'] = round(float(max_rate_record['OfferedLoad(Mbps)']), 2)
                        data_dict['latency_min'] = round(float(max_rate_record['MinimumLatency(us)']), 2)
                        data_dict['latency_max'] = round(float(max_rate_record['MaximumLatency(us)']), 2)
                        data_dict['latency_avg'] = round(float(max_rate_record['AverageLatency(us)']), 2)

                        data_dict['jitter_min'] = round(float(max_rate_record['MinimumJitter(us)']), 2)
                        data_dict['jitter_max'] = round(float(max_rate_record['MaximumJitter(us)']), 2)
                        data_dict['jitter_avg'] = round(float(max_rate_record['AverageJitter(us)']), 2)
                    else:
                        fun_test.log("No entry as PASSED seen for frame size %s" % frame_size)
                        data_dict['pps'] = -1
                        data_dict['throughput'] = -1
                        data_dict['latency_min'] = -1
                        data_dict['latency_max'] = -1
                        data_dict['latency_avg'] = -1

                        data_dict['jitter_min'] = -1
                        data_dict['jitter_max'] = -1
                        data_dict['jitter_avg'] = -1
                        failed_result_found = True
                        any_result_failed = True

                    if num_flows:
                        data_dict['num_flows'] = num_flows
                        data_dict['offloads'] = offloads
                        data_dict['protocol'] = protocol

                    results.append(data_dict)
                    fun_test.debug(results)

                    if update_charts:
                        if model_name == JUNIPER_PERFORMANCE_MODEL_NAME:
                            unit_dict = {}
                            unit_dict["pps_unit"] = PerfUnit.UNIT_PPS
                            unit_dict["throughput_unit"] = PerfUnit.UNIT_MBITS_PER_SEC
                            unit_dict["latency_min_unit"] = PerfUnit.UNIT_USECS
                            unit_dict["latency_max_unit"] = PerfUnit.UNIT_USECS
                            unit_dict["latency_avg_unit"] = PerfUnit.UNIT_USECS
                            unit_dict["jitter_min_unit"] = PerfUnit.UNIT_USECS
                            unit_dict["jitter_max_unit"] = PerfUnit.UNIT_USECS
                            unit_dict["jitter_avg_unit"] = PerfUnit.UNIT_USECS
                            add_entry = self.use_model_helper(model_name=model_name, data_dict=data_dict,
                                                              unit_dict=unit_dict)
                            fun_test.add_checkpoint("Entry added for frame size %s to model %s" % (frame_size, model_name))
            if update_json:
                file_path = fun_test.get_test_case_artifact_file_name(post_fix_name=file_name)
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
            if any_result_failed:
                fun_test.log("Failed result found")
                output = False
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

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
            unit_dict["latency_min_unit"] = PerfUnit.UNIT_USECS
            unit_dict["latency_max_unit"] = PerfUnit.UNIT_USECS
            unit_dict["latency_avg_unit"] = PerfUnit.UNIT_USECS
            unit_dict["jitter_min_unit"] = PerfUnit.UNIT_USECS
            unit_dict["jitter_max_unit"] = PerfUnit.UNIT_USECS
            unit_dict["jitter_avg_unit"] = PerfUnit.UNIT_USECS
            add_entry = self.use_model_helper(model_name=model_name, data_dict=output_dict, unit_dict=unit_dict)
            fun_test.simple_assert(add_entry, "Entry added to model %s" % model_name)
            fun_test.add_checkpoint("Entry added to model %s" % model_name)

            output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def get_throughput_config(self):
        configs = []
        try:
            handle = self._fetch_sequencer_handles()[0]
            fun_test.simple_assert(handle, "Get Sequencer configuration")

            group_commands = self.stc_manager.get_rfc2544_group_commands(
                sequencer_handle=handle, command_type="children-Rfc2544ThroughputSequencerGroupCommand")
            for command in group_commands:
                throughput_command = self.get_throughput_command_handle(group_command_handle=command)
                config_command = self.get_rfc2544_throughput_config_command(handle=throughput_command)
                existing_config = self.stc_manager.get_rfc2544_throughput_config(handle=config_command)
                config_obj = Rfc2544ThroughputConfig()
                config_obj.spirent_handle = config_command
                config_obj.update_object_attributes(**existing_config)
                configs.append(config_obj)
        except Exception as ex:
            fun_test.critical(str(ex))
        return configs

    def get_throughput_command_handle(self, group_command_handle):
        handle = None
        try:
            handles = self.stc_manager.get_object_children(handle=group_command_handle)
            for handle in handles:
                if re.search(r'rfc2544throughput.*', handle):
                    handle = handle
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return handle

    def get_rfc2544_throughput_config_command(self, handle):
        command = None
        try:
            commands = self.stc_manager.get_object_children(handle)
            for command in commands:
                if re.search(r'rfc2544throughput.*', command):
                    command = command
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return command

    def update_throughput_config(self, config_obj):
        result = False
        try:
            result = self.stc_manager.configure_rfc2544_throughput_config(handle=config_obj.spirent_handle,
                                                                          attributes=config_obj.get_attributes_dict())
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_interface_type_by_speed(self, speed):
        interface_type = None
        if speed == SpirentManager.SPEED_25G:
            interface_type = str(Ethernet25GigFiberInterface())
        elif speed == SpirentManager.SPEED_100G:
            interface_type = str(Ethernet100GigFiberInterface())
        return interface_type

    # We need to enable per-port latency compensation adjustments
    # Settings --> PHY --> enable per-port latency compensation adjustments
    def enable_per_port_latency_adjustments(self):
        result = False
        try:
            phy_options = self.stc_manager.get_physical_options_under_project()
            for phy_option in phy_options:
                result = self.stc_manager.enable_per_port_latency_compensation_adjustments(
                    phy_option=phy_option, enable_compensation_mode=True)
                fun_test.simple_assert(result, "Ensure per-port latency adjustments are enabled")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    # All ports --> Port config --> compensation_mode = 'Removed'
    def set_ports_compensation_mode(self, port_list=None, compensation_mode="REMOVED"):
        result = False
        try:
            if not port_list:
                port_list = self.stc_manager.get_port_list()
            for port in port_list:
                interface_obj = self.create_physical_interface(port_handle=port)
                phy_compensation_option = self.stc_manager.create_phy_compensation_option(
                    interface_handle=interface_obj.spirent_handle, compensation_mode=compensation_mode)
                fun_test.simple_assert(phy_compensation_option,
                                       "Ensure physical compensation option updated for %s under interface %s" % (
                                           port, interface_obj.spirent_handle))
                kwargs = {"ActivePhy-targets": interface_obj.spirent_handle}
                result = self.stc_manager.update_handle_config(config_handle=port, attributes=kwargs)
                fun_test.simple_assert(result, "Ensure %s updated successfully" % port)
                self.stc_manager.apply_configuration()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_physical_interface(self, port_handle):
        result = None
        try:
            interface_obj = None
            job_inputs = fun_test.get_job_inputs()
            fun_test.simple_assert(job_inputs, "Job inputs are not found")
            if job_inputs['speed'] == SpirentManager.SPEED_100G:
                # To avoid latency spikes at 100% rate we need to adjust internal clock source to -10
                interface_obj = Ethernet100GigFiberInterface(line_speed=Ethernet100GigFiberInterface.SPEED_100G,
                                                             auto_negotiation=False,
                                                             forward_error_correction=False,
                                                             internal_ppm_adjust=-10,
                                                             transmit_clock_source="INTERNAL_PPM_ADJ")
            elif job_inputs['speed'] == SpirentManager.SPEED_25G:
                # To avoid latency spikes at 100% rate we need to adjust internal clock source to -10
                interface_obj = Ethernet25GigFiberInterface(auto_negotiation=False,
                                                            line_speed=Ethernet25GigFiberInterface.SPEED_25G,
                                                            internal_ppm_adjust=-10,
                                                            transmit_clock_source="INTERNAL_PPM_ADJ")
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

    def get_sequencer_handle(self):
        return self._fetch_sequencer_handles()[0]

    def get_sequencer_state(self, sequencer_handle):
        try:
            state = self.stc_manager.stc.get(sequencer_handle, 'testState')
        except Exception as ex:
            fun_test.critical(str(ex))
        return state

# TODO: We might need this sqlite wrapper later on to fetch more detail test data


class SqliteWrapper(object):

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self._connect()
        self.cursor = None
        self._get_cursor()

    def _connect(self):
        try:
            if not self.conn:
                self.conn = sqlite3.connect(self.db_path)
        except Exception as ex:
            fun_test.critical(str(ex))

    def _get_cursor(self):
        try:
            if not self.cursor:
                self.cursor = self.conn.cursor()
        except Exception as ex:
            fun_test.critical(str(ex))

    def get_max_fps(self):
        pass

    def _create_query(self, column_list, table_name):
        query = None
        try:
            columns = ', '.join(column_list)
            query = "select %s from %s" % (columns, table_name)
            fun_test.log("Running query: %s" % query)
        except Exception as ex:
            fun_test.critical(str(ex))
        return query

    def fetch_throughput_results(self):
        results = []
        try:
            columns = ['TrialNum', 'IterationNum', 'FrameSize', 'FrameSizeType', 'Result',
                       'IntendedFPSLoad', 'IntendedMbpsLoad', 'OfferedFPSLoad', 'OfferedMbpsLoad', 'LoadSize',
                       'LoadSizeType', 'TxFrameCount', 'RxFrameCount', 'ExpectedFrameCount',
                       'FrameLoss', 'PercentLoss', 'TxFrameRate', 'ForwardingRate', 'ThroughputRate', 'Throughput',
                       'MinLatency', 'AvgLatency', 'MaxLatency', 'MinJitter', 'AvgJitter', 'MaxJitter', 'DurationinSec']

            query = self._create_query(column_list=columns, table_name="Rfc2544ThroughputPerFrameSizeResult")

            for row in self.cursor.execute(query):
                index = 0
                data_dict = OrderedDict()
                for col in columns:
                    data_dict[col] = row[index]
                    index += 1
                results.append(data_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return results









