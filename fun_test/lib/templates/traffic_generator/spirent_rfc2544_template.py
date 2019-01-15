"""
Author: Rushikesh Pendse

This template is for RFC-2544 Networking performance.
User needs to create .tcc spirent config with the test parameters and RFC-2544 wizard configured
"""
from lib.system.fun_test import *
from lib.host.spirent_manager import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *


class Rfc2544Template(SpirentTrafficGeneratorTemplate):
    USER_WORKING_DIR = "USER_WORKING_DIR"
    FRAME_SIZE_64 = "64"
    FRAME_SIZE_1500 = "1500"
    FRAME_SIZE_IMIX = "IMIX"
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
            fun_test.test_assert(config_file_exists, "%s tcc config exists" % tcc_config_path)

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
            fun_test.log("Sequencer running...")
            result_dict = self.stc_manager.wait_until_complete()
            # TODO: check the status of it if finish
            fun_test.log("Sequencer Stopped...")
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

    def get_stream_handles(self):
        stream_handles = []
        try:
            stream_handles = self.stc_manager.get_stream_handle_list()
        except Exception as ex:
            fun_test.critical(str(ex))
        return stream_handles

    def get_parameters_for_each_stream(self):
        streams_info = {}
        try:
            stream_handles = self.get_stream_handles()
            for stream_handle in stream_handles:
                stream_dict = self.stc_manager.get_stream_parameters(stream_block_handle=stream_handle)
                fun_test.log("----------------------> Stream Info for %s <----------------------" % stream_handle)
                for key, val in stream_dict.items():
                    fun_test.log("%s : %s" % (key, val))
                streams_info[stream_handle] = stream_dict
        except Exception as ex:
            fun_test.critical(str(ex))
        return streams_info

    def get_sequencer_configuration(self):
        sequencer_config = None
        try:
            sequencer_handle = self.stc_manager.get_sequencer_handles()[0]
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

    def validate_performance_result(self, records):
        result = False
        try:
            checkpoint = "Verify RFC-2544 Result for each trial"
            for record in records:
                data_dict = dict(record)
                trial_num = data_dict['TrialNumber']
                frame_size = data_dict['AvgFrameSize']
                fun_test.test_assert_expected(expected=self.PASSED, actual=data_dict['Result'],
                                              message="Ensure test result PASSED for trial %d and "
                                                      "frame size %s B" % (trial_num, frame_size))
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Verify TxFrameCount == RxFrameCount and FrameLoss is 0 for each trial"
            for record in records:
                data_dict = dict(record)
                trial_num = data_dict['TrialNumber']
                frame_size = data_dict['AvgFrameSize']
                frame_loss = data_dict['FrameLoss']
                tx_frame_count = data_dict['TxFrameCount']
                rx_frame_count = data_dict['RxFrameCount']
                fun_test.test_assert_expected(expected=tx_frame_count, actual=rx_frame_count,
                                              message="Ensure TxFrameCount == RxFrameCount for trial %d and"
                                                      "frame size %s B" % (trial_num, frame_size))
                fun_test.test_assert_expected(expected=0, actual=frame_loss,
                                              message="Ensure FrameLoss is 0 for trial %d and frame size %s B" % (
                                                  trial_num, frame_size))
            fun_test.add_checkpoint(checkpoint)
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

    def create_performance_table(self, records, table_name):
        result = False
        try:
            table_headers = []
            for record in records:
                for data in record:
                    table_headers.append(data[0])

            table_rows = []
            for record in records:
                row = []
                for data in record:
                    row.append(data[1])
                table_rows.append(row)

            table_data = {'headers': table_headers, 'rows': table_rows}
            fun_test.add_table(panel_header="RFC-2544 Performance Detailed Summary",
                               table_name=table_name,
                               table_data=table_data)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _is_frame_size_found(self, result_list, frame_size):
        frame_size_found = False
        try:
            for result in result_list:
                if 'frame_size' in result:
                    if result['frame_size'] == frame_size:
                        frame_size_found = True
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return frame_size_found

    def populate_performance_json_file(self, records, timestamp, flow_direction, mode=DUT_MODE_25G):
        results = []
        try:
            for record in records:
                record_dict = dict(record)
                data_dict = OrderedDict()
                data_dict['mode'] = mode
                data_dict['version'] = fun_test.get_version()
                data_dict['timestamp'] = timestamp
                frame_size = int(record_dict['AvgFrameSize'])
                if self._is_frame_size_found(result_list=results, frame_size=frame_size):
                    pass
                else:
                    data_dict['flow_type'] = flow_direction
                    data_dict['frame_size'] = frame_size
                    data_dict['pps'] = record_dict['Forwarding Rate (fps)']
                    data_dict['throughput'] = record_dict['Throughput (Mbps)']
                    data_dict['latency_min'] = record_dict['Minimum Latency (us)']
                    data_dict['latency_max'] = record_dict['Maximum Latency (us)']
                    data_dict['latency_avg'] = record_dict['Average Latency (us)']

                    data_dict['jitter_min'] = record_dict['Minimum Jitter (us)']
                    data_dict['jitter_max'] = record_dict['Maximum Jitter (us)']
                    data_dict['jitter_avg'] = record_dict['Average Jitter (us)']

                    results.append(data_dict)
                    fun_test.debug(results)

            file_path = LOGS_DIR + "/%s" % self.OUTPUT_JSON_FILE_NAME
            contents = self.read_json_file_contents(file_path=file_path)
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



