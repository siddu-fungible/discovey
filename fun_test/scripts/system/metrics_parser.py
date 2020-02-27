from django.apps import apps
from web.fun_test.metrics_models import MetricChart
from web.fun_test.analytics_models_helper import MetricHelper
import re
import json
import collections
from fun_global import RESULTS
from dateutil.parser import parse
from fun_global import FunPlatform, PerfUnit
from lib.system.fun_test import *
from web.fun_test.models_helper import add_jenkins_job_id_map
from web.fun_test.metrics_models import *

app_config = apps.get_app_config(app_label='fun_test')


class MetricParser():
    def parse_it(self, logs, metric_id=None, model_name=None, auto_add_to_db=False, date_time=None,
                 platform=FunPlatform.F1, run_time=None):
        result = {}
        if model_name:
            result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time, platform=platform,
                                         run_time=run_time)
        else:
            if metric_id:
                chart = MetricChart.objects.get(metric_id=metric_id)
                model_name = chart.metric_model_name
                result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time,
                                             platform=platform, run_time=run_time)

        if auto_add_to_db:
            if result["data"]:
                metric_model = app_config.get_metric_models()[model_name]
                for entry in result["data"]:
                    MetricHelper(model=metric_model).add_entry(run_time=run_time, **entry)
        return result

    def regex_by_model(self, model_name, logs, date_time, platform, run_time):
        if "FlowTest" in model_name:
            return self.flow_test(logs=logs, date_time=date_time)
        elif "Dfa" in model_name or "Nfa" in model_name:
            return self.dfa_nfa(logs=logs, date_time=date_time, platform=platform)
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
        elif "TeraMarkPkeRsaPerformance" in model_name:
            return self.pke_rsa(logs=logs, date_time=date_time, platform=platform)
        elif "TeraMarkPkeRsa4kPerformance" in model_name:
            return self.pke_rsa_4k(logs=logs, date_time=date_time, platform=platform)
        elif "TeraMarkPkeEcdh256Performance" in model_name:
            return self.pke_ecdh_256(logs=logs, date_time=date_time, platform=platform)
        elif "TeraMarkPkeEcdh25519Performance" in model_name:
            return self.pke_ecdh_25519(logs=logs, date_time=date_time, platform=platform)
        elif "PkeX25519TlsSoakPerformance" in model_name:
            return self.pke_x25519_tls(logs=logs, date_time=date_time, platform=platform)
        elif "PkeP256TlsSoakPerformance" in model_name:
            return self.pke_p256_tls(logs=logs, date_time=date_time, platform=platform)
        elif "SoakDmaMem" in model_name:
            return self.soak_dma_memcpy_memset(logs=logs, date_time=date_time, platform=platform, model_name=model_name)
        elif "SoakFlows" in model_name:
            return self.soak_flows(logs=logs, date_time=date_time, platform=platform, model_name=model_name)
        elif "VoltestBlt" in model_name:
            return self.voltest_blt(logs=logs, date_time=date_time, platform=platform, model_name=model_name)
        elif "EcPerformance" in model_name:
            return self.ec_performance(logs=logs, date_time=date_time, platform=platform)
        elif "EcVolPerformance" in model_name:
            return self.ec_vol_performance(logs=logs, date_time=date_time, platform=platform)
        elif "VoltestPerformance" in model_name:
            return self.voltest_performance(logs=logs, date_time=date_time, platform=platform)
        elif "TeraMarkCrypto" in model_name or "TeraMarkMultiClusterCrypto" in model_name or "CryptoFastPath" in \
                model_name:
            return self.teramark_crypto(logs=logs, date_time=date_time, platform=platform, model_name=model_name)
        elif "TeraMarkJpeg" in model_name:
            return self.teramark_jpeg(logs=logs, date_time=date_time, platform=platform)
        elif "BootTime" in model_name:
            return self.boot_time(logs=logs, date_time=date_time, platform=platform)
        elif "NuTransit" in model_name:
            return self.teramark_nu_transit(logs=logs, platform=platform, model_name=model_name)
        elif "TeraMarkZip" in model_name:
            return self.teramark_zip(logs=logs, date_time=date_time, platform=platform, run_time=run_time)
        elif "DataPlaneOperationsPerformance" in model_name:
            return self.data_plane_operations(logs=logs, platform=platform)
        else:
            return {}

    def metrics_to_dict(self, metrics, result, date_time):
        d = {}
        d["input_date_time"] = date_time
        d["status"] = result
        for key, value in metrics.iteritems():
            d[key] = value
        return d

    def add_version_to_jenkins_job_id_map(self, date_time, version):
        suite_execution_id = fun_test.get_suite_execution_id()
        add_jenkins_job_id_map(jenkins_job_id=0,
                               fun_sdk_branch="",
                               git_commit="",
                               software_date=0,
                               hardware_version="",
                               build_properties="", lsf_job_id="",
                               sdk_version=version, build_date=date_time, suite_execution_id=suite_execution_id,
                               add_associated_suites=False)

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

    def dfa_nfa(self, logs, date_time, platform):
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
                    metrics["input_platform"] = platform
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
            m = re.search(
                r'DMA\s+memcpy\s+threshold\s+VP\s+vs.\s+DMA:\s+(?P<threshold_json>{.*})\s+\[(?P<metric_name>.*)\]',
                line)
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
            m = re.search(
                r'Average\s+dispatch\s+WU\s+(?P<average_json>{.*})\s+\[(?P<metric_name>wu_dispatch_latency_cycles)\]',
                line)
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
            m = re.search(r'loadgen_aggregate\s+(?P<metric>\w+).*(?P<value_json>{.*})\s+\[(?P<metric_name>.*)\]', line)
            if m:
                metric = m.group("metric")
                if metric == "Bandwidth" or metric == "IOPS":
                    self.match_found = True
                    value_json = json.loads(m.group("value_json"))
                    key = "output_read_write_" + metric.lower()
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
                key = "output_channel_parall_speed"
                self.set_value_metrics(value_json=value_json, key=key, default=-1)
                input_metric_name = m.group("metric_name")
                self.metrics["input_metric_name"] = input_metric_name
                self.metrics["input_platform"] = platform
                self.metrics["input_busy_loop_usecs"] = value_json["busy_loop_usecs"]
                self.metrics["input_data_pool_count"] = value_json["data_pool_count"]
                self.metrics["input_number_channels"] = value_json["N"]
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def set_pke_metrics(self, m, input_app, platform, date_time):
        self.match_found = True
        value_json = json.loads(m.group("value_json"))
        output_ops_per_sec = float(value_json["value"])
        unit = value_json["unit"]
        input_metric_name = m.group("metric_name").replace(" ", "_")
        self.metrics["input_app"] = input_app
        self.metrics["input_metric_name"] = input_metric_name
        self.metrics["output_ops_per_sec"] = output_ops_per_sec
        self.metrics["output_ops_per_sec_unit"] = unit
        self.metrics["input_platform"] = platform
        self.status = RESULTS["PASSED"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)

    def pke_rsa(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>RSA\s+CRT\s+2048\s+decryptions)\]',
                line)
            if m:
                self.set_pke_metrics(m=m, input_app="pke_rsa_crt_dec_no_pad_soak", platform=platform,
                                     date_time=date_time)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def pke_rsa_4k(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>RSA\s+CRT\s+4096\s+decryptions)\]',
                line)
            if m:
                self.set_pke_metrics(m=m, input_app="pke_rsa_crt_dec_no_pad_4096_soak", platform=platform,
                                     date_time=date_time)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def pke_ecdh_256(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>ECDH\s+P256)\]',
                line)
            if m:
                self.set_pke_metrics(m=m, input_app="pke_ecdh_soak_256", platform=platform,
                                     date_time=date_time)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def pke_ecdh_25519(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>ECDH\s+25519)\]',
                line)
            if m:
                self.set_pke_metrics(m=m, input_app="pke_ecdh_soak_25519", platform=platform,
                                     date_time=date_time)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def pke_x25519_tls(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[TLS\s+1.2\s+SERVER\s+PKE\s+OPS\s+\((?P<metric_name>ECDHE_RSA\s+X25519\s+RSA\s+2K)\)\]',
                line)
            if m:
                self.set_pke_metrics(m=m, input_app="pke_x25519_2k_tls_soak", platform=platform,
                                     date_time=date_time)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def pke_p256_tls(self, logs, date_time, platform):
        self.initialize()
        for line in logs:
            m = re.search(
                r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[TLS\s+1.2\s+SERVER\s+PKE\s+OPS\s+\((?P<metric_name>ECDHE_RSA\s+P256\s+RSA\s+2K)\)\]',
                line)
            if m:
                self.set_pke_metrics(m=m, input_app="pke_p256_2k_tls_soak", platform=platform,
                                     date_time=date_time)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def soak_dma_memcpy_memset(self, logs, date_time, platform, model_name):
        self.initialize()
        for line in logs:
            m = re.search(
                r'Bandwidth\s+for\s+DMA\s+(?P<operation>\S+)\s+for\s+size\s+(?P<size>\S+):\s+(?P<bandwidth_json>.*)\s+\[(?P<metric_name>\S+)\]',
                line)
            if m:
                self.match_found = True
                bandwidth_json = json.loads(m.group("bandwidth_json"))
                output_bandwidth = float(bandwidth_json["value"])
                unit = bandwidth_json["unit"]
                if model_name == "SoakDmaMemsetPerformance":
                    if "non_coh" in bandwidth_json:
                        input_non_coherent = bandwidth_json["non_coh"]
                        self.metrics["input_coherent"] = False if input_non_coherent == 1 else True
                    elif "bm" in bandwidth_json:
                        input_bm = bandwidth_json["bm"]
                        self.metrics["input_buffer_memory"] = True if input_bm == 1 else False
                self.metrics["input_size"] = m.group("size")
                self.metrics["input_operation"] = m.group("operation")
                self.metrics["output_bandwidth"] = output_bandwidth
                self.metrics["output_bandwidth_unit"] = unit
                self.metrics["input_log_size"] = bandwidth_json["log_size"]
                self.metrics["input_metric_name"] = m.group("metric_name")
                self.metrics["input_platform"] = platform
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def soak_flows(self, logs, date_time, platform, model_name):
        self.initialize()
        for line in logs:
            m = re.search(r'CRIT\s+nucleus\s+"Experiment completed:\s+(?P<exp_value>[0-9.]+)'
                          r'(?P<exp_unit>\w+)\s+(?P<value_json>{.*})\s+\[(?P<metric_name>\w+)\]', line)
            if m:
                self.match_found = True
                value_json = json.loads(m.group("value_json"))
                self.metrics['input_name'] = value_json['name']
                self.metrics['input_metric_name'] = m.group('metric_name')
                self.metrics["input_platform"] = platform
                self.metrics['input_variation'] = value_json.get('variation', -1)
                self.metrics['input_max_variation'] = value_json.get('max_variation', -1)
                self.metrics['input_min_duration'] = value_json.get('min_duration', -1)
                self.metrics['input_max_duration'] = value_json.get('max_duration', -1)
                self.metrics['input_duration'] = value_json.get('duration', -1)
                self.metrics['input_num_flows'] = value_json.get('num_flows', -1)
                self.metrics['input_num_ops'] = value_json.get('num_ops', -1)
                self.metrics['input_warm_up'] = value_json.get('warm_up', -1)

                if model_name == "SoakFlowsBusyLoop10usecs":
                    key = 'output_busy_loops_value'
                elif model_name == "SoakFlowsMemcpy1MBNonCoh":
                    key = 'output_dma_memcpy_value'

                self.set_value_metrics(value_json=value_json, key=key, default=-1)
                self.status = RESULTS["PASSED"]
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def voltest_blt(self, logs, date_time, platform, model_name):
        self.initialize()
        blt_instance = int(re.search(r'\d+', model_name).group())
        self.metrics['input_blt_instance'] = blt_instance
        for line in logs:
            m = re.search(r'loadgen_aggregate\s+(\w+:\s+)?(?P<value_json>{.*})\s+\[(?P<metric_name>.*)\]', line)
            if m:
                self.match_found = True
                metric_name = m.group('metric_name')
                value_json = json.loads(m.group("value_json"))
                if metric_name == 'loadgen_aggregate_latency_ns':
                    self.metrics["output_min_latency"] = value_json["latency"]["min"]
                    self.metrics["output_max_latency"] = value_json["latency"]["max"]
                    self.metrics["output_avg_latency"] = value_json["latency"]["avg"]
                    self.metrics["output_min_latency"] = value_json["latency"]["min"]
                    self.metrics["output_max_latency"] = value_json["latency"]["max"]
                    self.metrics["output_min_latency_unit"] = self.metrics["output_max_latency_unit"] = \
                        self.metrics["output_avg_latency_unit"] = value_json["latency"]["unit"]
                elif metric_name == "loadgen_aggregate_iops":
                    key = 'output_iops'
                    self.set_value_metrics(value_json=value_json, key=key, default=-1)
                elif metric_name == "loadgen_aggregate_avg_op_bw_mbps":
                    key = 'output_bandwidth'
                    self.set_value_metrics(value_json=value_json, key=key, default=-1)
        if self.match_found:
            self.status = RESULTS["PASSED"]
            d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
            self.result["data"].append(d)
            self.result["match_found"] = self.match_found
            self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result

    def ec_performance(self, logs, date_time, platform):
        self.initialize()
        self.metrics["input_platform"] = platform
        str_logs = '\n'.join(logs)
        match_agg = re.search(r"Aggregated", str_logs)
        if match_agg:
            regex = "Aggregated EC\s+\w+\s+\w+:?\s+(?P<value_json>{.*})\s+\[(?P<metric_name>\w+)\]"
        else:
            regex = "EC config\s+\w+\s+\w+:?\s+(?P<value_json>{.*})\s+\[(?P<metric_name>\w+)\]"

        for line in logs:
            m = re.search(r'{}'.format(regex), line)
            if m:
                fun_test.log(line)
                self.match_found = True
                value_json = json.loads(m.group("value_json"))
                metric_name = m.group("metric_name")
                if metric_name == 'perf_ec_encode_latency':
                    self.metrics['output_encode_latency_min'] = value_json.get('min', -1)
                    self.metrics['output_encode_latency_max'] = value_json.get('max', -1)
                    self.metrics['output_encode_latency_avg'] = value_json.get('avg', -1)
                    self.metrics['output_encode_latency_min_unit'] = \
                        self.metrics['output_encode_latency_max_unit'] = \
                        self.metrics['output_encode_latency_avg_unit'] = value_json.get('unit', PerfUnit.UNIT_NSECS)

                elif metric_name == 'perf_ec_encode_throughput':
                    self.metrics['output_encode_throughput_min'] = value_json.get('min', -1)
                    self.metrics['output_encode_throughput_max'] = value_json.get('max', -1)
                    self.metrics['output_encode_throughput_avg'] = value_json.get('avg', -1)
                    self.metrics['output_encode_throughput_min_unit'] = \
                        self.metrics['output_encode_throughput_max_unit'] = \
                        self.metrics['output_encode_throughput_avg_unit'] = value_json.get('unit',
                                                                                           PerfUnit.UNIT_GBITS_PER_SEC)

                elif metric_name == 'perf_ec_recovery_latency':
                    self.metrics['output_recovery_latency_min'] = value_json.get('min', -1)
                    self.metrics['output_recovery_latency_max'] = value_json.get('max', -1)
                    self.metrics['output_recovery_latency_avg'] = value_json.get('avg', -1)
                    self.metrics['output_recovery_latency_min_unit'] = \
                        self.metrics['output_recovery_latency_max_unit'] = \
                        self.metrics['output_recovery_latency_avg_unit'] = value_json.get('unit', PerfUnit.UNIT_NSECS)

                elif metric_name == 'perf_ec_recovery_throughput':
                    self.metrics['output_recovery_throughput_min'] = value_json.get('min', -1)
                    self.metrics['output_recovery_throughput_max'] = value_json.get('max', -1)
                    self.metrics['output_recovery_throughput_avg'] = value_json.get('avg', -1)
                    self.metrics['output_recovery_throughput_min_unit'] = \
                        self.metrics['output_recovery_throughput_max_unit'] = \
                        self.metrics['output_recovery_throughput_avg_unit'] = value_json.get('unit',
                                                                                             PerfUnit.UNIT_GBITS_PER_SEC)

        self.status = RESULTS["PASSED"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result))
        return self.result

    def ec_vol_performance(self, logs, date_time, platform):
        self.initialize()
        self.metrics["input_platform"] = platform
        for line in logs:
            m = re.search(r'(?P<value>{.*})\s+\[\S+:(?P<metric_name>\S+)\]', line)
            if m:
                fun_test.log(line)
                self.match_found = True
                value = m.group("value")
                j = json.loads(value)
                metric_name = m.group("metric_name").lower()
                if not ("ECVOL_EC_STATS_latency_ns".lower() in metric_name or
                        "ECVOL_EC_STATS_iops".lower() in metric_name):
                    continue

                try:  # Either a raw value or json value
                    if "latency" in j:
                        j = j["latency"]
                    for key, value in j.iteritems():
                        if key != "unit" and key != "value":
                            self.metrics["output_" + metric_name + "_" + key] = value
                            self.metrics["output_" + metric_name + "_" + key + "_unit"] = j["unit"]
                        if key == "value":
                            self.metrics["output_" + metric_name] = value
                            self.metrics["output_" + metric_name + "_unit"] = j["unit"]
                except:
                    self.metrics["output_" + metric_name] = value
                    self.metrics["output_" + metric_name + "_unit"] = j["unit"]

        self.status = RESULTS["PASSED"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result))
        return self.result

    def voltest_performance(self, logs, date_time, platform):
        self.initialize()
        self.metrics["input_platform"] = platform
        for line in logs:
            m = re.search(r'"(?P<metric_name>\S+)\s+(?:\S+\s+\d+:\s+)?(?P<metric_type>\S+)?(:\s+)?'
                          r'(?P<value>{.*})\s+\[(?P<metric_id>\S+)\]', line)
            if m:
                fun_test.log(line)
                self.match_found = True
                metric_name = m.group("metric_name")
                metric_type = m.group("metric_type")
                value = m.group("value")
                j = json.loads(value)
                metric_id = m.group("metric_id").lower()
                allowed_metric_names = ["VOL_TYPE_BLK_LSV_write",
                                        "VOL_TYPE_BLK_LSV_read",
                                        "FILTER_TYPE_XTS_ENCRYPT",
                                        "FILTER_TYPE_XTS_DECRYPT",
                                        "FILTER_TYPE_DEFLATE",
                                        "FILTER_TYPE_INFLATE",
                                        "VOL_TYPE_BLK_EC_write",
                                        "VOL_TYPE_BLK_EC_read"]
                if metric_name not in allowed_metric_names:
                    continue

                if metric_type == None:
                    metric_type = "latency"
                    j = j["latency"]

                if "andwidth" in metric_type.lower():
                    if "avg_op_bw_mbps" in line:
                        metric_type += "_avg"
                    elif "total_op_bw_mbps":
                        metric_type += "_total"

                try:  # Either a raw value or json value
                    for key, value in j.iteritems():
                        if key != "unit" and key != "value":
                            self.metrics["output_" + metric_name + "_" + metric_type + "_" + key] = value
                            self.metrics["output_" + metric_name + "_" + metric_type + "_" + key + "_unit"] = j["unit"]
                        if key == "value":
                            self.metrics["output_" + metric_name + "_" + metric_type] = value
                            self.metrics["output_" + metric_name + "_" + metric_type + "_unit"] = j["unit"]
                except Exception as ex:
                    self.metrics["output_" + metric_name + "_" + metric_type] = value
                    self.metrics["output_" + metric_name + "_" + metric_type + "_unit"] = j["unit"]

        self.status = RESULTS["PASSED"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result))
        return self.result

    def boot_time(self, logs, date_time, platform):
        self.initialize()
        self.metrics["input_platform"] = platform
        for line in logs:
            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Firmware',
                line)
            if m:
                self.match_found = True
                output_firmware_boot_time = int(m.group("time")) / 1000.0
                output_firmware_boot_cycles = int(m.group("cycle"))
                fun_test.log(
                    "boot type: Firmware, boot time: {}, boot cycles: {}".format(output_firmware_boot_time,
                                                                                 output_firmware_boot_cycles))
                self.metrics["output_firmware_boot_time"] = output_firmware_boot_time
                self.metrics["output_firmware_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Flash\s+type\s+detection',
                line)
            if m:
                output_flash_type_boot_time = int(m.group("time")) / 1000.0
                output_flash_type_boot_cycles = int(m.group("cycle"))
                fun_test.log("boot type: Flash type detection, boot time: {}, boot cycles: {}".format(
                    output_flash_type_boot_time,
                    output_flash_type_boot_cycles))
                self.metrics["output_flash_type_boot_time"] = output_flash_type_boot_time
                self.metrics["output_flash_type_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+EEPROM\s+Loading',
                line)
            if m:
                output_eeprom_boot_time = int(m.group("time")) / 1000.0
                output_eeprom_boot_cycles = int(m.group("cycle"))
                fun_test.log(
                    "boot type: EEPROM Loading, boot time: {}, boot cycles: {}".format(output_eeprom_boot_time,
                                                                                       output_eeprom_boot_cycles))
                self.metrics["output_eeprom_boot_time"] = output_eeprom_boot_time
                self.metrics["output_eeprom_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+SBUS\s+Loading',
                line)
            if m:
                output_sbus_boot_time = int(m.group("time")) / 1000.0
                output_sbus_boot_cycles = int(m.group("cycle"))
                fun_test.log(
                    "boot type: SBUS Loading, boot time: {}, boot cycles: {}".format(output_sbus_boot_time,
                                                                                     output_sbus_boot_cycles))
                self.metrics["output_sbus_boot_time"] = output_sbus_boot_time
                self.metrics["output_sbus_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Host\s+BOOT',
                line)
            if m:
                output_host_boot_time = int(m.group("time")) / 1000.0
                output_host_boot_cycles = int(m.group("cycle"))
                fun_test.log(
                    "boot type: Host BOOT, boot time: {}, boot cycles: {}".format(output_host_boot_time,
                                                                                  output_host_boot_cycles))
                self.metrics["output_host_boot_time"] = output_host_boot_time
                self.metrics["output_host_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Main\s+Loop',
                line)
            if m:
                output_main_loop_boot_time = int(m.group("time")) / 1000.0
                output_main_loop_boot_cycles = int(m.group("cycle"))
                fun_test.log(
                    "boot type: Main Loop, boot time: {}, boot cycles: {}".format(output_main_loop_boot_time,
                                                                                  output_main_loop_boot_cycles))
                self.metrics["output_main_loop_boot_time"] = output_main_loop_boot_time
                self.metrics["output_main_loop_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Boot\s+success',
                line)
            if m:
                output_boot_success_boot_time = int(m.group("time")) / 1000.0
                output_boot_success_boot_cycles = int(m.group("cycle"))
                fun_test.log(
                    "boot type: Boot success, boot time: {}, boot cycles: {}".format(
                        output_boot_success_boot_time,
                        output_boot_success_boot_cycles))
                self.metrics["output_boot_success_boot_time"] = output_boot_success_boot_time
                self.metrics["output_boot_success_boot_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<timestamp>.*)\s+\S+\]\s+\[\S+\]\s+all\s+VPs\s+online,\s+sending\s+bootstrap\s+WU',
                line)
            if m:
                self.metrics["output_all_vps_online"] = float(m.group("timestamp"))
                self.metrics["output_all_vps_online_unit"] = PerfUnit.UNIT_SECS
                fun_test.log(
                    "All VPs online: {}".format(self.metrics["output_all_vps_online"]))
            m = re.search(
                r'\[(?P<timestamp>.*)\s+\S+\]\s+\[\S+\]\s+Parsing\s+config\s+took\s+(?P<parsing_time>\S+)('
                r'?P<parsing_unit>msecs)',
                line)
            if m:
                self.metrics["output_parsing_config_end"] = float(m.group("timestamp"))
                self.metrics["output_parsing_config_end_unit"] = PerfUnit.UNIT_SECS
                self.metrics["output_parsing_config"] = float(m.group("parsing_time"))
                self.metrics["output_parsing_config_unit"] = m.group("parsing_unit")
                fun_test.log(
                    "Parsing config: {}, {}".format(self.metrics["output_parsing_config"],
                                                    self.metrics["output_parsing_config_end"]))
            m = re.search(
                r'\[(?P<timestamp>.*)\s+\S+\]\s+\[\S+\]\s+SKU\s+has\s+SBP,\s+sending\s+a\s+HOST_BOOTED\s+message',
                line)
            if m:
                self.metrics["output_sending_host_booted_message"] = float(m.group("timestamp"))
                self.metrics["output_sending_host_booted_message_unit"] = PerfUnit.UNIT_SECS
                fun_test.log(
                    "Sending host booted message: {}".format(self.metrics["output_sending_host_booted_message"]))

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+MMC\s+INIT',
                line)
            if m:
                output_init_mmc_time = int(m.group("time")) / 1000.0
                output_init_mmc_cycles = int(m.group("cycle"))
                fun_test.log(
                    "MMC INIT Time: {}, cycles: {}".format(output_init_mmc_time,
                                                           output_init_mmc_cycles))
                self.metrics["output_init_mmc_time"] = output_init_mmc_time
                self.metrics["output_init_mmc_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+MMC\s+load\s+dest=(?P<dest>ffffffff90000000)\s+size=(?P<size>\d+)',
                line)
            if m:
                output_boot_read_mmc_time = int(m.group("time")) / 1000.0
                output_boot_read_mmc_cycles = int(m.group("cycle"))
                fun_test.log(
                    "MMC Boot Read Time: {}, cycles: {}".format(output_boot_read_mmc_time,
                                                                output_boot_read_mmc_cycles))
                self.metrics["output_boot_read_mmc_time"] = output_boot_read_mmc_time
                self.metrics["output_boot_read_mmc_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+MMC\s+load\s+dest=(?P<dest>ffffffff91000000)\s+size=(?P<size>\d+)',
                line)
            if m:
                output_funos_read_mmc_time = int(m.group("time")) / 1000.0
                output_funos_read_mmc_cycles = int(m.group("cycle"))
                fun_test.log(
                    "MMC FunOS Read Time: {}, cycles: {}".format(output_funos_read_mmc_time,
                                                                 output_funos_read_mmc_cycles))
                self.metrics["output_funos_read_mmc_time"] = output_funos_read_mmc_time
                self.metrics["output_funos_read_mmc_time_unit"] = "msecs"

            m = re.search(
                r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Start\s+ELF',
                line)
            if m:
                output_funos_load_elf_time = int(m.group("time")) / 1000.0
                output_funos_load_elf_cycles = int(m.group("cycle"))
                fun_test.log(
                    "ELF FunOS Load Time: {}, cycles: {}".format(output_funos_load_elf_time,
                                                                 output_funos_load_elf_cycles))
                self.metrics["output_funos_load_elf_time"] = output_funos_load_elf_time
                self.metrics["output_funos_load_elf_time_unit"] = "msecs"

        self.status = RESULTS["PASSED"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result))
        return self.result


    def set_crypto_metrics_dict(self, crypto_json, input_app, date_time):
        pkt_size_json = crypto_json["pktsize"]
        ops_json = crypto_json["ops"] if "ops" in crypto_json else None
        bandwidth_json = crypto_json["throughput"]

        output_ops_per_sec = int(ops_json["value"]) if ops_json else -1
        output_throughput = float(bandwidth_json["value"])

        self.metrics["input_app"] = input_app
        self.metrics["input_algorithm"] = crypto_json["alg"]
        self.metrics["input_operation"] = crypto_json["operation"]
        self.metrics["input_pkt_size"] = int(pkt_size_json["value"])
        self.metrics["output_ops_per_sec"] = output_ops_per_sec
        self.metrics["output_throughput"] = output_throughput
        self.metrics["output_ops_per_sec_unit"] = PerfUnit.UNIT_OPS
        self.metrics["output_throughput_unit"] = bandwidth_json["units"]
        d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
        self.result["data"].append(d)


    def teramark_crypto(self, logs, date_time, platform, model_name):
        self.initialize()
        self.metrics["input_platform"] = platform
        for line in logs:
            m = re.search(r'(?P<crypto_json>{"test".*})', line)
            if m:
                fun_test.log(line)
                self.match_found = True
                self.status = RESULTS["PASSED"]
                crypto_json = json.loads(m.group("crypto_json"))
                input_test = crypto_json["test"]
                if model_name == "TeraMarkCryptoPerformance":
                    if "api" in input_test:
                        input_app = "crypto_api_perf"
                        self.set_crypto_metrics_dict(crypto_json=crypto_json, input_app=input_app, date_time=date_time)
                elif model_name == "TeraMarkMultiClusterCryptoPerformance":
                    if "raw" in input_test:
                        input_app = "crypto_raw_speed"
                        input_key_size = int(crypto_json["key_size"]) if "key_size" in crypto_json else -1
                        self.metrics["input_key_size"] = input_key_size
                        self.set_crypto_metrics_dict(crypto_json=crypto_json, input_app=input_app, date_time=date_time)
                elif model_name == "CryptoFastPathPerformance":
                    if "fastpath" in input_test:
                        input_app = "crypto_fast_path"
                        input_key_size = int(crypto_json["key_size"]) if "key_size" in crypto_json else -1
                        self.metrics["input_key_size"] = input_key_size
                        self.set_crypto_metrics_dict(crypto_json=crypto_json, input_app=input_app, date_time=date_time)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result))
        return self.result


    def teramark_jpeg(self, logs, date_time, platform):
        self.initialize()
        jpeg_operations = {"Compression throughput": "Compression throughput with Driver",
                           "Decompression throughput": "JPEG Decompress",
                           "Accelerator Compression throughput": "Compression Accelerator throughput",
                           "Accelerator Decompression throughput": "Decompression Accelerator throughput",
                           "JPEG Compression": "JPEG Compression"}

        self.metrics["input_platform"] = platform
        current_file_name = None
        final_file_name = None
        teramark_begin = False
        for line in logs:
            compression_ratio_found = False
            if "Compression-ratio to 1" in line:
                compression_ratio_found = True
            m = re.search(r'JPEG Compression/Decompression performance stats (?P<current_file_name>\S+?)(?=#)', line)
            if m:
                current_file_name = m.group("current_file_name")
                final_file_name = current_file_name
            if "TeraMark Begin" in line:
                teramark_begin = True
                continue
            if "TeraMark End" in line:
                teramark_begin = False
                fun_test.test_assert(current_file_name, "Filename detected")

                current_file_name = None
            if teramark_begin:
                m = re.search(r'({.*})', line)
                if m:
                    fun_test.log(line)
                    self.match_found = True
                    j = m.group(1)
                    try:
                        d = json.loads(j)
                    except Exception as ex:
                        message = "Invalid json for : {}".format(j)
                        fun_test.critical(message)
                        raise Exception(message)
                    self.metrics = {}
                    self.metrics["input_platform"] = platform
                    if not compression_ratio_found:
                        if d["Operation"] in jpeg_operations:
                            self.metrics["input_operation"] = jpeg_operations[d["Operation"]]
                        else:
                            self.metrics["input_operation"] = d["Operation"]
                        self.metrics["input_count"] = d['Stats']['_count']
                        self.metrics["input_image"] = final_file_name
                        # metrics["output_iops"] = d['Stats']['_iops']
                        # metrics["output_max_latency"] = d['Stats']['_max_latency']
                        # metrics["output_min_latency"] = d['Stats']['_min_latency']
                        # metrics["output_average_latency"] = d['Stats']['_avg_latency']
                        self.metrics["output_average_bandwidth"] = d['Stats']['_avg_bw_gbps']
                    else:
                        if d["Operation"] in jpeg_operations:
                            self.metrics["input_operation"] = jpeg_operations[d["Operation"]]
                        else:
                            self.metrics["input_operation"] = d["Operation"]
                        self.metrics["input_image"] = final_file_name
                        self.metrics["output_compression_ratio"] = d['Stats']["Compression-ratio to 1"]
                        self.metrics["output_percentage_savings"] = d['Stats']["PercentageSpaceSaving"]

                    self.status = RESULTS["PASSED"]
                    d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                    print("data", d)
                    self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result, indent=4))
        return self.result


    def teramark_nu_transit(self, logs, platform, model_name):
        self.initialize()
        self.metrics["input_platform"] = platform
        nu_transit_flow_types = {"FCP_HNU_HNU": "HNU_HNU_FCP"}

        for file in logs:
            for line in file:
                if "flow_type" in line:
                    if line["flow_type"] in nu_transit_flow_types:
                        line["flow_type"] = nu_transit_flow_types[line["flow_type"]]
                        self.match_found = True
                    self.metrics["input_flow_type"] = line["flow_type"].replace("FPG", "NU")
                    self.metrics["input_mode"] = line.get("mode", "")
                    self.metrics["input_version"] = line["version"]
                    self.metrics["input_frame_size"] = line["frame_size"]
                    date_time = self.get_time_from_timestamp(line["timestamp"])
                    self.metrics["output_throughput"] = (float(
                        line["throughput"]) / 1000) if "throughput" in line and line[
                        "throughput"] != -1 else -1
                    self.metrics["output_pps"] = (float(
                        line["pps"]) / 1000000) if "pps" in line and line[
                        "pps"] != -1 else -1
                    self.metrics["output_latency_max"] = line.get("latency_max", -1)
                    self.metrics["output_latency_min"] = line.get("latency_min", -1)
                    self.metrics["output_latency_avg"] = line.get("latency_avg", -1)
                    if model_name == "NuTransitPerformance":
                        self.metrics["output_latency_P99"] = line.get("latency_P99", -1)
                        self.metrics["output_latency_P90"] = line.get("latency_P90", -1)
                        self.metrics["output_latency_P50"] = line.get("latency_P50", -1)
                    else:
                        self.metrics["input_half_load_latency"] = line.get("half_load_latency", False)
                    self.metrics["input_num_flows"] = line.get("num_flows", 512000)
                    self.metrics["input_offloads"] = line.get("offloads", False)
                    self.metrics["input_protocol"] = line.get("protocol", "UDP")
                    self.metrics["output_jitter_max"] = line.get("jitter_max", -1)
                    self.metrics["output_jitter_min"] = line.get("jitter_min", -1)
                    self.metrics["output_jitter_avg"] = line.get("jitter_avg", -1)
                    fun_test.log(
                        "flow type: {}, latency: {}, bandwidth: {}, frame size: {}, jitters: {}, pps: {}".format(
                            self.metrics["input_flow_type"], self.metrics["output_latency_avg"],
                            self.metrics["output_throughput"],
                            self.metrics["input_frame_size"], self.metrics["output_jitter_avg"],
                            self.metrics["output_pps"]))
                    self.status = RESULTS["PASSED"]
                    d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                    self.result["data"].append(d)
                    if date_time.year >= 2019:
                        metric_model = app_config.get_metric_models()[model_name]
                        run_time_props = {}
                        run_time_props["lsf_job_id"] = None
                        run_time_props["suite_execution_id"] = fun_test.get_suite_execution_id()
                        run_time_props["jenkins_build_number"] = None
                        run_time_props["build_properties"] = None
                        run_time_props["version"] = self.metrics["input_version"]
                        run_time_props["associated_suites"] = None
                        MetricHelper(model=metric_model).add_entry(run_time=run_time_props, **d)

            self.result["match_found"] = self.match_found
            self.result["status"] = self.status == RESULTS["PASSED"]
            fun_test.log("Result :{}".format(self.result))
            return self.result


    def teramark_zip(self, logs, date_time, platform, run_time):
        self.initialize()
        metrics = collections.OrderedDict()
        metrics['input_platform'] = platform
        teramark_begin = False
        for line in logs:
            if "TeraMark Begin" in line:
                teramark_begin = True
            if "TeraMark End" in line:
                teramark_begin = False
            if teramark_begin:
                m = re.search(
                    r'{"Type":\s+"(?P<type>\S+)",.*?\s+"Operation":\s+(?P<operation>\S+),\s+"Effort":\s+(?P<effort>\S+),'
                    r'.*\s+"Duration"\s+:\s+(?P<latency_json>{.*}),\s+"Throughput":\s+(?P<throughput_json>{.*})}', line)
                if m:
                    self.match_found = True
                    input_type = m.group("type")
                    input_operation = m.group("operation")
                    input_effort = int(m.group("effort"))
                    bandwidth_json = json.loads(m.group("throughput_json"))
                    output_bandwidth_avg = bandwidth_json['value']
                    output_bandwidth_avg_unit = bandwidth_json["unit"]
                    latency_json = json.loads(m.group("latency_json"))
                    output_latency_avg = latency_json['value']
                    output_latency_unit = latency_json["unit"]

                    fun_test.log("type: {}, operation: {}, effort: {}, stats {}".format(input_type, input_operation,
                                                                                        input_effort,
                                                                                        bandwidth_json))
                    metrics["input_type"] = input_type
                    metrics["input_operation"] = input_operation
                    metrics["input_effort"] = input_effort
                    metrics["output_bandwidth_avg"] = output_bandwidth_avg
                    metrics["output_bandwidth_avg_unit"] = output_bandwidth_avg_unit
                    metrics["output_latency_avg"] = output_latency_avg
                    metrics["output_latency_avg_unit"] = output_latency_unit
                    self.status = RESULTS["PASSED"]
                    d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                    if input_type == "Deflate":
                        MetricHelper(model=eval("TeraMarkZipDeflatePerformance")).add_entry(run_time=run_time, **d)
                    else:
                        MetricHelper(model=eval("TeraMarkZipLzmaPerformance")).add_entry(run_time=run_time, **d)
                    self.result["data"].append(d)
        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        return self.result


    def data_plane_operations(self, logs, platform):
        self.initialize()
        self.metrics["input_platform"] = platform

        for file in logs:
            for line in file:
                self.match_found = True
                self.metrics["output_total_time"] = line["total_time"]
                self.metrics["output_total_time_unit"] = line["total_time_unit"]
                if line["total_time_unit"] == "seconds":
                    self.metrics["output_total_time_unit"] = PerfUnit.UNIT_SECS
                self.metrics["output_avg_time"] = line["avg_time_per_volume"]
                if line["avg_time_per_volume_unit"] == "seconds":
                    self.metrics["output_avg_time_unit"] = PerfUnit.UNIT_SECS

                self.metrics["input_volume_size"] = line["volume_size"]
                self.metrics["input_volume_size_unit"] = line["volume_size_unit"]
                if line["volume_size_unit"] == "MB":
                    self.metrics["input_volume_size_unit"] = PerfUnit.UNIT_MB
                self.metrics["input_volume_type"] = line["volume_type"]
                self.metrics["input_total_volumes"] = line["total_volumes"]
                self.metrics["input_concurrent"] = line["concurrent"]
                self.metrics["input_action_type"] = line["action_type"]
                self.metrics["input_split_performance_data"] = line["split_performance_data"] if \
                    "split_performance_data" in line else "{}"
                self.metrics["input_real_f1"] = line["real_f1"] if "real_f1" in line else False

                self.status = RESULTS["PASSED"]
                date_time = self.get_time_from_timestamp(line["date_time"])
                d = self.metrics_to_dict(metrics=self.metrics, result=self.status, date_time=date_time)
                self.result["data"].append(d)

        self.result["match_found"] = self.match_found
        self.result["status"] = self.status == RESULTS["PASSED"]
        fun_test.log("Result :{}".format(self.result))
        return self.result
