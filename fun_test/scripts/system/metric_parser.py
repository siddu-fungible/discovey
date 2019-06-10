from django.apps import apps
from web.fun_test.metrics_models import MetricChart
from web.fun_test.analytics_models_helper import MetricHelper
import re
import json
import collections
from fun_global import RESULTS
from dateutil.parser import parse
from fun_global import FunPlatform

app_config = apps.get_app_config(app_label='fun_test')


class MetricParser():
    def parse_it(self, logs, metric_id=None, model_name=None, auto_add_to_db=False, date_time=None, platform=FunPlatform.F1):
        result = {}
        if model_name:
            result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time, platform=platform)
        else:
            if metric_id:
                chart = MetricChart.objects.get(metric_id=metric_id)
                model_name = chart.metric_model_name
                result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time, platform=platform)

        if auto_add_to_db:
            if result["data"]:
                metric_model = app_config.get_metric_models()[model_name]
                for entry in result["data"]:
                    MetricHelper(model=metric_model).add_entry(**entry)
        return result

    def regex_by_model(self, model_name, logs, date_time, platform):
        if "FlowTest" in model_name:
            return self.flow_test(logs=logs, date_time=date_time)
        elif "Dfa" in model_name or "Nfa" in model_name:
            return self.dfa_nfa(logs=logs, date_time=date_time)
        elif "Rcnvme" in model_name:
            return self.rcnvme(logs=logs, date_time=date_time, model_name=model_name)
        elif "HuLatency" in model_name or "HuThroughput" in model_name:
            return self.hu_networking(logs=logs, date_time=date_time)
        elif "JuniperCryptoTunnel" in model_name or "JuniperIpsec" in model_name:
            return self.crypto_tunnel(logs=logs, date_time=date_time)
        elif "LookupEngine" in model_name:
            return self.lookup_engine(logs=logs, date_time=date_time)
        elif "JuniperTlsTunnel" in model_name:
            return self.crypto_tunnel(logs=logs, date_time=date_time)
        elif "MemcpyThreshold" in model_name:
            return self.memcpy_threshold(logs=logs, date_time=date_time)
        elif "WuDispatchTest" in model_name:
            return self.wu_dispatch(logs=logs, date_time=date_time, platform=platform)
        elif "WuSendSpeedTest" in model_name:
            return self.wu_send_speed(logs=logs, date_time=date_time, platform=platform)
        elif "FunMagent" in model_name:
            return self.fun_magent(logs=logs, date_time=date_time, platform=platform)
        elif "WuStackSpeed" in model_name:
            return self.wu_stack_speed(logs=logs, date_time=date_time, platform=platform)
        elif "SoakFunMalloc" in model_name:
            return self.soak_fun_malloc(logs=logs, date_time=date_time, platform=platform)
        elif "SoakClassicMalloc" in model_name:
            return self.soak_classic_malloc(logs=logs, date_time=date_time, platform=platform)
        elif "AllocSpeed" in model_name:
            return self.alloc_speed(logs=logs, date_time=date_time, platform=platform)
        elif "WuLatencyUngated" in model_name:
            return self.wu_latency_ungated(logs=logs, date_time=date_time, platform=platform)
        elif "WuLatencyAllocStack" in model_name:
            return self.wu_latency_alloc_stack(logs=logs, date_time=date_time, platform=platform)
        elif "BcopyPerformance" in model_name:
            return self.bcopy(logs=logs, date_time=date_time, platform=platform)
        elif "BcopyFloodDmaPerformance" in model_name:
            return self.bcopy_flood(logs=logs, date_time=date_time, platform=platform)
        elif "VoltestLsv" in model_name:
            return self.voltest_lsv(logs=logs, date_time=date_time, platform=platform)
        elif "ChannelParallPerformance" in model_name:
            return self.channel_parall(logs=logs, date_time=date_time, platform=platform)
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
            if "PASS testflow_test" in line:
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

    def rcnvme(self, logs, date_time, model_name):
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
                    # metrics["input_total_numios"] = json_value["total_numios"]
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
                if model_name == "TeraMarkRcnvmeReadWriteAllPerformance":
                    o = re.search(
                        r'rcnvme_consolidated_(?P<operation>\S+)\s+(\S+\s+)?(?P<value>{.*})\s+\[(?P<metric_name>\S+)\]',
                        line)
                else:
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

    def lookup_engine(self, logs, date_time):
        match_found = False
        result = {}
        result["data"] = []
        teramark_begin = False
        self.status = RESULTS["FAILED"]
        metrics = collections.OrderedDict()
        for line in logs:
            if "TeraMark Begin" in line:
                teramark_begin = True
                continue
            if "TeraMark End" in line:
                teramark_begin = False
            if teramark_begin:
                m = re.search(
                    r'(?P<value_json>{.*})',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    match_found = True
                    metrics["input_test"] = "le_test_perf"
                    metrics["input_memory"] = value_json["memory"]
                    metrics["input_operation"] = value_json["operation"]
                    self.set_metrics(value_json=value_json, metrics=metrics, key="output_lookup_per_sec", default=-1)
                    self.status = RESULTS["PASSED"]
                    d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                    result["data"].append(d)
        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]
        return result

    def set_metrics(self, value_json, metrics, key, default):
        metrics[key + "_min"] = value_json.get("min", default)
        metrics[key + "_max"] = value_json.get("max", default)
        if "avg" in value_json:
            metrics[key + "_avg"] = value_json.get("avg", default)
        else:
            metrics[key + "_avg"] = value_json.get("value", default)
        if "unit" in value_json:
            metrics[key + "_min_unit"] = value_json.get("unit", default)
            metrics[key + "_max_unit"] = value_json.get("unit", default)
            metrics[key + "_avg_unit"] = value_json.get("unit", default)

    def set_value_metrics(self, value_json, key, default):
        self.metrics[key] = value_json.get("value", default)
        self.metrics[key + '_unit'] = value_json["unit"]

    def memcpy_threshold(self, logs, date_time):
        self.initialize()
        for line in logs:
            m = re.search(r'DMA\s+memcpy\s+threshold\s+VP\s+vs.\s+DMA:\s+(?P<threshold_json>{.*})\s+\[(?P<metric_name>.*)\]', line)
            if m:
                self.match_found = True
                threshold_json = json.loads(m.group("threshold_json"))
                self.metrics["input_metric_name"] = m.group("metric_name")
                self.set_value_metrics(value_json=threshold_json, key="output_threshold", default=-1)
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def initialize(self):
        self.metrics = collections.OrderedDict()
        self.match_found = False
        self.result = {}
        self.result["data"] = []
        self.status = RESULTS["FAILED"]

    def wu_dispatch(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(r'Average\s+dispatch\s+WU\s+(?P<average_json>{.*})\s+\[(?P<metric_name>wu_dispatch_latency_cycles)\]', line)
            if m:
                self.match_found = True
                average_json = json.loads(m.group("average_json"))
                output_average = int(average_json["value"])
                unit = average_json["unit"]
                input_app = "dispatch_speed_test"
                input_metric_name = m.group("metric_name")
                self.metrics["input_app"] = input_app
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["output_average"] = output_average
                self.metrics["output_average_unit"] = unit
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def wu_send_speed(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'Average\s+WU\s+send\s+ungated\s+(?P<average_json>{.*})\s+\[(?P<metric_name>wu_send_ungated_latency_cycles)\]',
                line)
            if m:
                self.match_found = True
                average_json = json.loads(m.group("average_json"))
                output_average = int(average_json["value"])
                unit = average_json["unit"]
                input_app = "wu_send_speed_test"
                input_metric_name = m.group("metric_name")
                self.metrics["input_app"] = input_app
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["output_average"] = output_average
                self.metrics["output_average_unit"] = unit
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def fun_magent(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            with open("/tmp/a.txt", "a+") as f:
                f.write(line)
            m = re.search(
                r'fun_magent.*=>\s+(?P<latency_json>{.*})\s+\[(?P<metric_name>fun_magent_rate_malloc_free_per_sec)\]',
                line)
            if m:
                self.match_found = True
                latency_json = json.loads(m.group("latency_json"))
                unit = latency_json["unit"]
                output_latency = int(latency_json["value"])
                input_app = "fun_magent_perf_test"
                input_metric_name = m.group("metric_name")
                self.metrics["input_app"] = input_app
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["output_latency"] = output_latency
                self.metrics["output_latency_unit"] = unit
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def wu_stack_speed(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'Average\s+wustack\s+alloc/+free\s+cycles:\s+(?P<average_json>{.*})\[(?P<metric_name>wustack_alloc_free_cycles)\]',
                line)
            if m:
                self.match_found = True
                average_json = json.loads(m.group("average_json"))
                output_average = int(average_json["value"])
                unit = average_json["unit"]
                input_app = "wustack_speed_test"
                input_metric_name = m.group("metric_name")
                self.metrics["output_average"] = output_average
                self.metrics["output_average_unit"] = unit
                self.metrics["input_app"] = input_app
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def soak_fun_malloc(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>soak_two_fun_malloc_fun_free)\]',
                line)
            if m:
                self.match_found = True
                value_json = json.loads(m.group("value_json"))
                output_ops_per_sec = float(value_json["value"])
                unit = value_json["unit"]
                input_app = "soak_malloc_fun_malloc"
                input_metric_name = m.group("metric_name")
                self.metrics["output_ops_per_sec"] = output_ops_per_sec
                self.metrics["output_ops_per_sec_unit"] = unit
                self.metrics["input_app"] = input_app
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def soak_classic_malloc(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>soak_two_classic_malloc_free)\]',
                line)
            if m:
                self.match_found = True
                value_json = json.loads(m.group("value_json"))
                output_ops_per_sec = float(value_json["value"])
                unit = value_json["unit"]
                input_app = "soak_malloc_classic"
                input_metric_name = m.group("metric_name")
                self.metrics["output_ops_per_sec"] = output_ops_per_sec
                self.metrics["output_ops_per_sec_unit"] = unit
                self.metrics["input_app"] = input_app
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def alloc_speed(self, logs, date_time, platform):
        self.initialize()
        m = None
        n = None
        o = None
        output_one_malloc_free_wu = -1
        output_one_malloc_free_threaded = -1
        output_one_malloc_free_classic_min = output_one_malloc_free_classic_avg = output_one_malloc_free_classic_max = -1
        for line in logs:
            if not m:
                m = re.search(r'Time for one fun_malloc\+fun_free \(WU\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]',
                              line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_wu = int(d["avg"])
                    output_one_malloc_free_wu_unit = d["unit"]
            if not n:
                n = re.search(
                    r'Time for one fun_malloc\+fun_free \(threaded\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_threaded_ns\]',
                    line)
                if n:
                    d = json.loads(n.group(1))
                    output_one_malloc_free_threaded = int(d['avg'])
                    output_one_malloc_free_threaded_unit = d["unit"]
            if not o:
                o = re.search(
                    r'Time for one malloc\+free \(classic\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_classic_ns\]', line)
                if o:
                    d = json.loads(o.group(1))
                    output_one_malloc_free_classic_avg = int(d['avg'])
                    output_one_malloc_free_classic_min = int(d['min'])
                    output_one_malloc_free_classic_max = int(d['max'])
                    output_one_malloc_free_classic_avg_unit = d["unit"]
                    output_one_malloc_free_classic_min_unit = d["unit"]
                    output_one_malloc_free_classic_max_unit = d["unit"]
            if m and n and o:
                self.match_found = True
                self.metrics["input_app"] = "alloc_speed_test"
                self.metrics["output_one_malloc_free_wu"] = output_one_malloc_free_wu
                self.metrics["output_one_malloc_free_threaded"] = output_one_malloc_free_threaded
                self.metrics["output_one_malloc_free_classic_min"] = output_one_malloc_free_classic_min
                self.metrics["output_one_malloc_free_classic_avg"] = output_one_malloc_free_classic_avg
                self.metrics["output_one_malloc_free_classic_max"] = output_one_malloc_free_classic_max
                self.metrics["output_one_malloc_free_wu_unit"] = output_one_malloc_free_wu_unit
                self.metrics["output_one_malloc_free_threaded_unit"] = output_one_malloc_free_threaded_unit
                self.metrics["output_one_malloc_free_classic_min_unit"] = output_one_malloc_free_classic_min_unit
                self.metrics["output_one_malloc_free_classic_avg_unit"] = output_one_malloc_free_classic_avg_unit
                self.metrics["output_one_malloc_free_classic_max_unit"] = output_one_malloc_free_classic_max_unit
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)
                m = None
                n = None
                o = None

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def wu_latency_ungated(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r' wu_latency_test.*({.*}).*perf_wu_ungated_ns',
                line)
            if m:
                self.match_found = True
                d = json.loads(m.group(1))
                wu_ungated_ns_min = int(d["min"])
                wu_ungated_ns_avg = int(d["avg"])
                wu_ungated_ns_max = int(d["max"])
                wu_ungated_ns_min_unit = d["unit"]
                wu_ungated_ns_avg_unit = d["unit"]
                wu_ungated_ns_max_unit = d["unit"]

                self.metrics["input_app"] = "wu_latency_test"
                self.metrics["output_min"] = wu_ungated_ns_min
                self.metrics["output_max"] = wu_ungated_ns_max
                self.metrics["output_avg"] = wu_ungated_ns_avg
                self.metrics["output_min_unit"] = wu_ungated_ns_min_unit
                self.metrics["output_max_unit"] = wu_ungated_ns_max_unit
                self.metrics["output_avg_unit"] = wu_ungated_ns_avg_unit
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def wu_latency_alloc_stack(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'wu_latency_test.*({.*}).*perf_wu_alloc_stack_ns',
                line)
            if m:
                self.match_found = True
                d = json.loads(m.group(1))
                wu_alloc_stack_ns_min = int(d["min"])
                wu_alloc_stack_ns_avg = int(d["avg"])
                wu_alloc_stack_ns_max = int(d["max"])
                wu_alloc_stack_ns_min_unit = d["unit"]
                wu_alloc_stack_ns_avg_unit = d["unit"]
                wu_alloc_stack_ns_max_unit = d["unit"]

                self.metrics["input_app"] = "wu_latency_test"
                self.metrics["output_min"] = wu_alloc_stack_ns_min
                self.metrics["output_max"] = wu_alloc_stack_ns_max
                self.metrics["output_avg"] = wu_alloc_stack_ns_avg
                self.metrics["output_min_unit"] = wu_alloc_stack_ns_min_unit
                self.metrics["output_max_unit"] = wu_alloc_stack_ns_max_unit
                self.metrics["output_avg_unit"] = wu_alloc_stack_ns_avg_unit
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def bcopy(self, logs, date_time, platform):
        self.initialize()
        m = None
        n = None
        for line in logs:
            if not m:
                m = re.search(
                    r'bcopy \((?P<coherent>\S+),\s+(?P<plain>\S+)\) (?P<size>\S+) (?P<iterations>\d+) times;\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>.*)\]',
                    line)
            if not n:
                n = re.search(
                    r'bcopy \((?P<coherent>\S+),\s+(?P<plain>\S+)\) (?P<size>\S+) (?P<iterations>\d+) times;\s+average bandwidth: (?P<bandwidth_json>{.*})\s+\[(?P<average_bandwidth_perf_name>.*)\]',
                    line)
            if m and n:
                self.match_found = True
                coherent = "Coherent"
                if m.group("coherent") != "coherent":
                    coherent = "Non-coherent"
                plain = "Plain"
                if m.group("plain") != "plain":
                    plain = "DMA"
                size = m.group("size")
                size = int(size.replace("KB", ""))
                latency_json_raw = m.group("latency_json")
                latency_json = json.loads(latency_json_raw)
                bandwidth_json = json.loads(n.group("bandwidth_json"))
                average_bandwidth = int(bandwidth_json["value"])

                self.metrics["input_plain"] = plain
                self.metrics["input_coherent"] = coherent
                self.metrics["input_size"] = size
                self.metrics["input_iterations"] = int(m.group("iterations"))
                self.metrics["output_latency_units"] = m.group("latency_units")
                self.metrics["output_latency_min"] = latency_json["min"]
                self.metrics["output_latency_max"] = latency_json["max"]
                self.metrics["output_latency_avg"] = latency_json["avg"]
                self.metrics["output_latency_min_unit"] = latency_json["unit"]
                self.metrics["output_latency_max_unit"] = latency_json["unit"]
                self.metrics["output_latency_avg_unit"] = latency_json["unit"]
                self.metrics["input_latency_perf_name"] = m.group("latency_perf_name")
                self.metrics["output_average_bandwith"] = average_bandwidth
                self.metrics["output_average_bandwith_unit"] = bandwidth_json["unit"]
                self.metrics["input_average_bandwith_perf_name"] = n.group("average_bandwidth_perf_name")
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)
                m = None
                n = None

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def bcopy_flood(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'bcopy flood with dma \((?P<N>\d+)\)\s+(?P<size>\S+);\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>\S+)\];\s+average bandwidth: (?P<bandwidth_json>{.*})\s+\[(?P<average_bandwidth_perf_name>\S+)\]',
                line)
            if m:
                self.match_found = True
                latency_json_raw = m.group("latency_json")
                latency_json = json.loads(latency_json_raw)
                bandwidth_json = json.loads(m.group("bandwidth_json"))
                average_bandwidth = int(bandwidth_json["value"])
                size = m.group("size")
                size = int(size.replace("KB", ""))

                self.metrics["input_n"] = m.group("N")
                self.metrics["input_size"] = size
                self.metrics["output_latency_units"] = m.group("latency_units")
                self.metrics["output_latency_min"] = latency_json["min"]
                self.metrics["output_latency_max"] = latency_json["max"]
                self.metrics["output_latency_avg"] = latency_json["avg"]
                self.metrics["output_latency_min_unit"] = latency_json["unit"]
                self.metrics["output_latency_max_unit"] = latency_json["unit"]
                self.metrics["output_latency_avg_unit"] = latency_json["unit"]
                self.metrics["input_latency_perf_name"] = m.group("latency_perf_name")
                self.metrics["output_average_bandwith"] = average_bandwidth
                self.metrics["output_average_bandwith_unit"] = bandwidth_json["unit"]
                self.metrics["input_average_bandwith_perf_name"] = m.group("average_bandwidth_perf_name")
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def voltest_lsv(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'loadgen_tot\S+\s+(?P<metric>\S+):\s+(?P<value_json>{.*})\s+\[(?P<metric_name>\S+)\]',
                line)
            if m:
                metric = m.group("metric")
                if metric == "Bandwidth" or metric == "IOPS":
                    self.match_found = True
                    value_json = json.loads(m.group("value_json"))
                    metric_name = m.group("metric_name")
                    if "read" in metric_name:
                        operation = "read"
                    else:
                        operation = "write"
                    if metric == "Bandwidth":
                        key = "output_" + operation + "_bandwidth"
                    else:
                        key = "output_" + operation + "_iops"
                    self.set_value_metrics(value_json=value_json, key=key, default=-1)
                    self.metrics["input_platform"] = platform
                    self.status = RESULTS["PASSED"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def channel_parall(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'Channel\s+parall\s+speed\s+test\s+(?P<value_json>{.*})\s+\[(?P<metric_name>\S+)\]',
                line)
            if m:
                self.match_found = True
                value_json = json.loads(m.group("value_json"))
                output_channel_parall_speed = int(value_json["value"])
                unit = value_json["unit"]
                input_metric_name = m.group("metric_name")
                self.metrics["output_channel_parall_speed"] = output_channel_parall_speed
                self.metrics["output_channel_parall_speed_unit"] = unit
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result
