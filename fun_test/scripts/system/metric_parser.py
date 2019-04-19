from django.apps import apps
from web.fun_test.metrics_models import MetricChart
from web.fun_test.analytics_models_helper import MetricHelper
import re
import json
import collections
from fun_global import RESULTS
from dateutil.parser import parse

app_config = apps.get_app_config(app_label='fun_test')


class MetricParser():
    def parse_it(self, logs, metric_id=None, model_name=None, auto_add_to_db=False, date_time=None):
        result = {}
        if model_name:
            result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time)
        else:
            if metric_id:
                chart = MetricChart.objects.get(metric_id=metric_id)
                model_name = chart.metric_model_name
                result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time)

        if auto_add_to_db:
            if result["data"]:
                metric_model = app_config.get_metric_models()[model_name]
                for entry in result["data"]:
                    MetricHelper(model=metric_model).add_entry(**entry)
        return result

    def regex_by_model(self, model_name, logs, date_time):
        if "FlowTest" in model_name:
            return self.flow_test(logs=logs, date_time=date_time)
        elif "Dfa" in model_name or "Nfa" in model_name:
            return self.dfa_nfa(logs=logs, date_time=date_time)
        elif "Rcnvme" in model_name:
            return self.rcnvme(logs=logs, date_time=date_time)
        elif "HuLatency" in model_name or "HuThroughput" in model_name:
            return self.hu_networking(logs=logs, date_time=date_time)
        elif "JuniperCrypto" in model_name:
            return self.crypto_tunnel(logs=logs, date_time=date_time)
        else:
            return {}

    def metrics_to_dict(self, metrics, result, date_time):
        d = {}
        d["input_date_time"] = date_time
        d["status"] = result
        for key, value in metrics.iteritems():
            d[key] = value
        return d

    def flow_test(self, logs, date_time):
        match_found = False
        result = {}
        result["data"] = []
        d = {}
        metrics = collections.OrderedDict()
        flow_test_passed = False
        match = None
        self.status = RESULTS["FAILED"]
        for line in logs:
            if "PASS libfunq testflow_test" in line:
                flow_test_passed = True
            m = re.search(
                r'Testflow:\s+(?P<iterations>\d+)\s+iterations\s+took\s+(?P<seconds>\d+)\s+seconds',
                line)
            if m:
                match = m
                match_found = True

            if flow_test_passed:
                if match:
                    self.status = RESULTS["PASSED"]
                    input_iterations = int(match.group("iterations"))
                    input_app = "hw_hsu_test"
                    output_time = int(match.group("seconds"))
                    metrics["input_iterations"] = input_iterations
                    metrics["output_time"] = output_time
                    metrics["output_time_unit"] = "secs"
                    metrics["input_app"] = input_app
                    d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                    result["data"].append(d)
                    match = None

        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]
        return result

    def rcnvme(self, logs, date_time):
        match_found = False
        result = {}
        result["data"] = []
        d = {}
        metrics = collections.OrderedDict()
        start_rcnvme = False
        match = None
        self.status = RESULTS["FAILED"]
        input_dev_access = ""
        for line in logs:
            if not start_rcnvme:
                m = re.search(
                    r'RC NVMe test:\s+(?P<value>{.*})',
                    line)
                if m:
                    start_rcnvme = True
                    json_value = json.loads(m.group("value"))
                    metrics["input_io_type"] = json_value["io_type"]
                    input_dev_access = json_value["dev_access"]
                    metrics["input_dev_access"] = input_dev_access
                    metrics["input_num_ctrlrs"] = json_value["num_ctrlrs"]
                    metrics["input_num_threads"] = json_value["num_threads"]
                    metrics["input_qdepth"] = json_value["qdepth"]
                    metrics["input_total_numios"] = json_value["total_numios"]
                    metrics["input_io_size"] = json_value["io_size"]
            else:
                n = re.search(
                    r'rcnvme\s+(?P<value>{.*})',
                    line)
                if n:
                    json_value = json.loads(n.group("value"))
                    if "ctrlr_id" in json_value:
                        metrics["input_ctrlr_id"] = json_value["ctrlr_id"]
                        metrics["input_model"] = json_value["Model"]
                        metrics["input_fw_rev"] = json_value["fw_rev"]
                        metrics["input_serial"] = json_value["serial"]
                    else:
                        metrics["input_pci_vendor_id"] = json_value["pci_vendor_id"]
                        metrics["input_pci_device_id"] = json_value["pci_device_id"]
                o = re.search(
                    r'rcnvme_total_(?P<operation>\S+)\s+(\S+\s+)?(?P<value>{.*})\s+\[(?P<metric_name>\S+)\]',
                    line)
                if o:
                    match_found = True
                    json_value = json.loads(o.group("value"))
                    if "latency" in json_value:
                        metrics["input_count"] = json_value["count"]
                        metrics["output_latency_avg"] = json_value["latency"]["avg"]
                        metrics["output_latency_min"] = json_value["latency"]["min"]
                        metrics["output_latency_max"] = json_value["latency"]["max"]
                        metrics["output_latency_avg_unit"] = json_value["latency"]["unit"]
                        metrics["output_latency_min_unit"] = json_value["latency"]["unit"]
                        metrics["output_latency_max_unit"] = json_value["latency"]["unit"]
                    elif "IOPS" in line:
                        metrics["output_iops"] = json_value["value"]
                        metrics["output_iops_unit"] = json_value["unit"]
                    elif "Bandwidth" in line:
                        metrics["output_bandwidth"] = json_value["value"]
                        metrics["output_bandwidth_unit"] = json_value["unit"]
                    input_operation = str(o.group("operation"))
                    metrics["input_operation"] = input_dev_access + "_" + input_operation
                    metrics["input_metric_name"] = "rcnvme_total_" + input_dev_access + "_" + input_operation
                    self.status = RESULTS["PASSED"]
                    d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                    result["data"].append(d)
        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]
        return result

    def dfa_nfa(self, logs, date_time):
        metrics = collections.OrderedDict()
        teramark_begin = False
        match_found = False
        result = {}
        result["data"] = []
        d = {}
        self.status = RESULTS["FAILED"]
        for line in logs:
            if "TeraMark Begin" in line:
                teramark_begin = True
                continue
            if "TeraMark End" in line:
                teramark_begin = False
            if teramark_begin:
                m = re.search(r'({.*})', line)
                if m:
                    match_found = True
                    j = m.group(1)
                    d = json.loads(j)
                    latency_json = d["Duration"]
                    output_latency = int(latency_json["value"])
                    output_latency_unit = latency_json["unit"]
                    bandwidth_json = d["Throughput"]
                    output_bandwidth = float(bandwidth_json["value"])
                    output_bandwidth_unit = bandwidth_json["unit"]
                    metrics["output_latency"] = output_latency
                    metrics["output_bandwidth"] = output_bandwidth
                    metrics["output_latency_unit"] = output_latency_unit
                    metrics["output_bandwidth_unit"] = output_bandwidth_unit
                    self.status = RESULTS["PASSED"]
                    d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                    result["data"].append(d)
        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]
        return result

    def get_time_from_timestamp(self, timestamp):
        time_obj = parse(timestamp)
        return time_obj

    def hu_networking(self, logs, date_time):
        match_found = False
        result = {}
        result["data"] = []
        d = {}
        for line in logs:
            self.status = RESULTS["FAILED"]
            if "flow_type" in line:
                match_found = True
                metrics = collections.OrderedDict()
                metrics["input_flow_type"] = line["flow_type"]
                metrics["input_frame_size"] = line["frame_size"]
                metrics["input_number_flows"] = line.get("num_flows", 1)
                metrics["input_offloads"] = line.get("offloads", False)
                metrics["input_protocol"] = line.get("protocol", "TCP")
                metrics["input_version"] = line.get("version", "")
                date_time = self.get_time_from_timestamp(line["timestamp"])
                if "throughput_h2n" in line:
                    self.model = "HuThroughputPerformance"
                    metrics["output_throughput_h2n"] = (float(
                        line["throughput_h2n"]) / 1000) if line["throughput_h2n"] != -1 else -1
                    metrics["output_throughput_n2h"] = (float(
                        line["throughput_n2h"]) / 1000) if line["throughput_n2h"] != -1 else -1
                    metrics["output_pps_h2n"] = (float(
                        line["pps_h2n"]) / 1000000) if line["pps_h2n"] != -1 else -1
                    metrics["output_pps_n2h"] = (float(
                        line["pps_n2h"]) / 1000000) if line["pps_n2h"] != -1 else -1
                elif "latency_avg_h2n" in line:
                    self.model = "HuLatencyPerformance"
                    metrics["output_latency_max_h2n"] = line.get("latency_max_h2n", -1)
                    metrics["output_latency_min_h2n"] = line.get("latency_min_h2n", -1)
                    metrics["output_latency_avg_h2n"] = line.get("latency_avg_h2n", -1)
                    metrics["output_latency_P99_h2n"] = line.get("latency_P99_h2n", -1)
                    metrics["output_latency_P90_h2n"] = line.get("latency_P90_h2n", -1)
                    metrics["output_latency_P50_h2n"] = line.get("latency_P50_h2n", -1)

                    metrics["output_latency_max_n2h"] = line.get("latency_max_n2h", -1)
                    metrics["output_latency_min_n2h"] = line.get("latency_min_n2h", -1)
                    metrics["output_latency_avg_n2h"] = line.get("latency_avg_n2h", -1)
                    metrics["output_latency_P99_n2h"] = line.get("latency_P99_n2h", -1)
                    metrics["output_latency_P90_n2h"] = line.get("latency_P90_n2h", -1)
                    metrics["output_latency_P50_n2h"] = line.get("latency_P50_n2h", -1)
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                result["data"].append(d)
        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]
        return result

    def crypto_tunnel(self, logs, date_time):
        match_found = False
        result = {}
        result["data"] = []
        self.status = RESULTS["FAILED"]
        for line in logs:
            m = re.search(
                r'(?P<crypto_json>{"test".*})',
                line)
            if m:
                match_found = True
                metrics = collections.OrderedDict()
                crypto_json = json.loads(m.group("crypto_json"))
                input_test = crypto_json["test"]
                input_algorithm = crypto_json["alg"]
                input_num_tunnels = crypto_json["num_tunnels"]
                input_key_size = crypto_json["key_size"]
                input_operation = crypto_json["operation"]
                input_src_memory = crypto_json["src_mem"]
                input_dst_memory = crypto_json["dst_mem"]

                pkt_size_json = crypto_json["pktsize"]
                pps_json = crypto_json["PPS"] if "PPS" in crypto_json else None
                bandwidth_json = crypto_json["throughput"]

                input_pkt_size = float(pkt_size_json["value"])
                output_packets_per_sec = float(pps_json["value"]) if pps_json else -1
                output_packets_per_sec_unit = pps_json["unit"]
                output_throughput = float(bandwidth_json["value"])
                output_throughput_unit = bandwidth_json["unit"]

                metrics["input_test"] = input_test
                metrics["input_algorithm"] = input_algorithm
                metrics["input_num_tunnels"] = input_num_tunnels
                metrics["input_key_size"] = input_key_size
                metrics["input_operation"] = input_operation
                metrics["input_pkt_size"] = input_pkt_size
                metrics["input_src_memory"] = input_src_memory
                metrics["input_dst_memory"] = input_dst_memory
                metrics["output_packets_per_sec"] = output_packets_per_sec
                metrics["output_throughput"] = output_throughput
                metrics["output_packets_per_sec_unit"] = output_packets_per_sec_unit
                metrics["output_throughput_unit"] = output_throughput_unit
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                result["data"].append(d)
        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]
        return result
