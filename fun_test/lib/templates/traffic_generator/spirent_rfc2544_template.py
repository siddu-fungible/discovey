"""
Author: Rushikesh Pendse

This template is for RFC-2544 Networking performance.
User needs to create .tcc spirent config with the test parameters and RFC-2544 wizard configured
"""
from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.host.linux import Linux
import sqlite3

FLOW_TYPE_NU_NU_NFCP = "NU_NU_NFCP"
FLOW_TYPE_HNU_HNU_NFCP = "HNU_HNU_NFCP"
FLOW_TYPE_HNU_HNU_FCP = "HNU_HNU_FCP"
FLOW_TYPE_HNU_NU_NFCP = "HNU_NU_NFCP"
FLOW_TYPE_NU_HNU_NFCP = "NU_HNU_NFCP"


class Rfc2544Template(SpirentTrafficGeneratorTemplate):
    USER_WORKING_DIR = "USER_WORKING_DIR"
    FRAME_SIZE_64 = "64.0"
    FRAME_SIZE_1500 = "1500.0"
    FRAME_SIZE_IMIX = "IMIX"
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
        result[self.FRAME_SIZE_IMIX] = []
        result[self.FRAME_SIZE_1000] = []
        result[self.FRAME_SIZE_9000] = []
        try:
            spirent_path = self.retrieve_database_file_name()
            # spirent_path = "/home/rushikesh/Spirent/TestCenter 4.81/Results/transit_bidirectional_palladium_2019-01-15_04-24-47/2544-Tput_2019-01-15_04-30-41/2544-Tput-Summary-2_2019-01-15_04-30-41.db"
            base_path = self._get_base_db_path(db_path=spirent_path)
            dbs = self._get_throughput_summary_db_list(base_path=base_path)
            for db in dbs:
                records = self.fetch_summary_result(db_name=db)
                for record in records:
                    data_dict = OrderedDict(record)
                    if 'AvgFrameSize' in data_dict and self.FRAME_SIZE_64 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_64].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_1500 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_1500].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_IMIX == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_IMIX].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_1000 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_1000].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_9000 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_9000].append(data_dict)
                    elif 'AvgFrameSize' in data_dict and self.FRAME_SIZE_8900 == data_dict['AvgFrameSize']:
                        result[self.FRAME_SIZE_9000].append(data_dict)
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
            throughput = float(forwarding_rate * (frame_size + 8) / 100000)
        except Exception as ex:
            fun_test.critical(str(ex))
        return throughput

    def _get_max_forwarding_rate(self, records, frame_size):
        max_rate_record = None
        try:
            forwarding_rates = []
            for record in records:
                if float(record['AvgFrameSize']) == frame_size:
                    forwarding_rates.append(record['ForwardingRate(fps)'])
            max_rate = max(forwarding_rates)
            for record in records:
                if max_rate == record['ForwardingRate(fps)']:
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

    def populate_performance_json_file(self, result_dict, timestamp, flow_direction, mode=DUT_MODE_25G):
        results = []
        try:
            for key in result_dict:
                records = result_dict[key]
                data_dict = OrderedDict()
                data_dict['mode'] = mode
                data_dict['version'] = fun_test.get_version()
                data_dict['timestamp'] = timestamp
                frame_size = float(records[0]['AvgFrameSize']) if records else None
                if frame_size == 8900.0:
                    frame_size = 9000.0
                if frame_size:
                    data_dict['flow_type'] = flow_direction
                    data_dict['frame_size'] = frame_size

                    max_rate_record = self._get_max_forwarding_rate(records=records, frame_size=frame_size)
                    data_dict['pps'] = float(max_rate_record['ForwardingRate(fps)'])
                    throughput = self._calculate_throughput_in_mbps(forwarding_rate=data_dict['pps'],
                                                                    frame_size=frame_size)
                    data_dict['throughput'] = round(throughput, 2)
                    data_dict['latency_min'] = round(float(max_rate_record['MinimumLatency(us)']), 2)
                    data_dict['latency_max'] = round(float(max_rate_record['MaximumLatency(us)']), 2)
                    data_dict['latency_avg'] = round(float(max_rate_record['AverageLatency(us)']), 2)

                    data_dict['jitter_min'] = round(float(max_rate_record['MinimumJitter(us)']), 2)
                    data_dict['jitter_max'] = round(float(max_rate_record['MaximumJitter(us)']), 2)
                    data_dict['jitter_avg'] = round(float(max_rate_record['AverageJitter(us)']), 2)

                    results.append(data_dict)
                    fun_test.debug(results)

            file_path = LOGS_DIR + "/%s" % self.OUTPUT_JSON_FILE_NAME
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
        except Exception as ex:
            fun_test.critical(str(ex))
        return results

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









