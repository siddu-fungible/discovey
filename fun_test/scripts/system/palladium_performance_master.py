from lib.system.fun_test import *
from django.apps import apps
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.metrics_models import AllocSpeedPerformance, BcopyPerformance, LAST_ANALYTICS_DB_STATUS_UPDATE
from web.fun_test.metrics_models import BcopyFloodDmaPerformance, PkeX25519TlsSoakPerformance, PkeP256TlsSoakPerformance
from web.fun_test.metrics_models import EcPerformance, EcVolPerformance, VoltestPerformance
from web.fun_test.metrics_models import WuSendSpeedTestPerformance, WuDispatchTestPerformance, FunMagentPerformanceTest
from web.fun_test.metrics_models import WuStackSpeedTestPerformance, SoakFunMallocPerformance, \
    SoakClassicMallocPerformance, TeraMarkMultiClusterCryptoPerformance
from web.fun_test.metrics_models import WuLatencyAllocStack, WuLatencyUngated, BootTimePerformance, NuTransitPerformance
from web.fun_test.metrics_models import TeraMarkPkeEcdh256Performance, TeraMarkPkeEcdh25519Performance
from web.fun_test.metrics_models import TeraMarkPkeRsa4kPerformance, TeraMarkPkeRsaPerformance, \
    TeraMarkCryptoPerformance, SoakDmaMemcpyCoherentPerformance, SoakDmaMemcpyNonCoherentPerformance, \
    SoakDmaMemsetPerformance, MetricChart, F1FlowTestPerformance
from web.fun_test.metrics_models import TeraMarkLookupEnginePerformance, FlowTestPerformance, \
    TeraMarkZipDeflatePerformance, TeraMarkZipLzmaPerformance, TeraMarkDfaPerformance, TeraMarkJpegPerformance
from web.fun_test.analytics_models_helper import MetricHelper, invalidate_goodness_cache, MetricChartHelper
from web.fun_test.analytics_models_helper import prepare_status_db
from web.fun_test.models import TimeKeeper
import re
from datetime import datetime
from dateutil.parser import parse
from scripts.system.metric_parser import MetricParser

ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
BOOT_TIMING_TEST_TAG = "boot_timing_test"
VOLTEST_TAG = "voltest_performance"
TERAMARK_PKE = "pke_teramark"
TERAMARK_CRYPTO = "crypto_teramark"
TERAMARK_LOOKUP = "le_teramark"
FLOW_TEST_TAG = "qa_storage2_endpoint"
F1_FLOW_TEST_TAG = "qa_f1_flowtest"
TERAMARK_ZIP = "zip_teramark"
TERAMARK_DFA = "dfa_teramark"
TERAMARK_NFA = "nfa_teramark"
TERAMARK_EC = "ec_teramark"
TERAMARK_JPEG = "jpeg_teramark"
SOAK_DMA_MEMCPY_COH = "soak_funos_memcpy_coh"
SOAK_DMA_MEMCPY_NON_COH = "soak_funos_memcpy_non_coh"
SOAK_DMA_MEMSET = "soak_funos_memset"
RCNVME_READ = "qa_rcnvme_read"
RCNVME_RANDOM_READ = "qa_rcnvme_random_read"
RCNVME_WRITE = "qa_rcnvme_write"
RCNVME_RANDOM_WRITE = "qa_rcnvme_random_write"

jpeg_operations = {"Compression throughput": "Compression throughput with Driver",
                   "Decompression throughput": "JPEG Decompress",
                   "Accelerator Compression throughput": "Compression Accelerator throughput",
                   "Accelerator Decompression throughput": "Decompression Accelerator throughput",
                   "JPEG Compression": "JPEG Compression"}
nu_transit_flow_types = {"FCP_HNU_HNU": "HNU_HNU_FCP"}
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

internal_chart_names_for_flows = {
    "NU_HNU_NFCP": ["NU_HNU_output_throughput", "NU_HNU_output_pps", "NU_HNU_output_latency_avg"],
    "HNU_HNU_FCP": ["HNU_HNU_FCP_output_throughput", "HNU_HNU_FCP_output_pps", "HNU_HNU_FCP_output_latency_avg"],
    "HNU_HNU_NFCP": ["HNU_HNU_output_throughput", "HNU_HNU_output_pps", "HNU_HNU_output_latency_avg"],
    "NU_NU_NFCP": ["NU_NU_output_throughput", "NU_NU_output_pps", "NU_NU_output_latency_avg"],
    "HNU_NU_NFCP": ["HNU_NU_output_throughput", "HNU_NU_output_pps", "HNU_NU_output_latency_avg"],
    "HU_NU_NFCP": ["HU_NU_NFCP_output_throughput", "HU_NU_NFCP_output_pps", "HU_NU_NFCP_output_latency_avg"],
    "HU_HU_NFCP": ["HU_HU_NFCP_output_throughput", "HU_HU_NFCP_output_pps", "HU_HU_NFCP_output_latency_avg"],
    "HU_HU_FCP": ["HU_HU_FCP_output_throughput", "HU_HU_FCP_output_pps", "HU_HU_FCP_output_latency_avg"],
    "NU_HU_NFCP": ["NU_HU_NFCP_output_throughput", "NU_HU_NFCP_output_pps", "NU_HU_NFCP_output_latency_avg"],
    "NU_VP_NU_FWD_NFCP": ["juniper_NU_VP_NU_FWD_NFCP_output_throughput", "juniper_NU_VP_NU_FWD_NFCP_output_pps",
                          "juniper_NU_VP_NU_FWD_NFCP_output_latency_avg"],
    "NU_LE_VP_NU_FW": ["juniper_NU_LE_VP_NU_FW_output_throughput", "juniper_NU_LE_VP_NU_FW_output_pps",
                       "juniper_NU_LE_VP_NU_FW_output_latency_avg"]
}

networking_models = ["HuThroughputPerformance", "HuLatencyPerformance"]


def get_rounded_time():
    dt = get_current_time()
    dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=23, minute=59, second=59)
    dt = get_localized_time(dt)
    return dt


def get_time_from_timestamp(timestamp):
    time_obj = parse(timestamp)
    return time_obj


def is_job_from_today(job_dt):
    today = get_rounded_time()
    return True  # TODO:
    return (job_dt.year == today.year) and (job_dt.month == today.month) and (job_dt.day == today.day)


def set_build_details_for_charts(result, suite_execution_id, test_case_id, jenkins_job_id, job_id, git_commit,
                                 model_name):
    charts = MetricChartHelper.get_charts_by_model_name(metric_model_name=model_name)
    for chart in charts:
        chart.last_build_status = result
        chart.last_build_date = get_current_time()
        chart.last_suite_execution_id = suite_execution_id
        chart.last_test_case_id = test_case_id
        chart.last_lsf_job_id = job_id
        chart.last_jenkins_job_id = jenkins_job_id
        chart.last_git_commit = git_commit
        chart.save()


def set_chart_status(result, suite_execution_id, test_case_id, jenkins_job_id, job_id, git_commit,
                     internal_chart_name):
    charts = MetricChart.objects.filter(internal_chart_name=internal_chart_name)
    for chart in charts:
        chart.last_build_status = result
        chart.last_build_date = get_current_time()
        chart.last_suite_execution_id = suite_execution_id
        chart.last_test_case_id = test_case_id
        chart.last_lsf_job_id = job_id
        chart.last_jenkins_job_id = jenkins_job_id
        chart.last_git_commit = git_commit
        chart.save()

def set_networking_chart_status():
    for model in networking_models:
        metric_model = app_config.get_metric_models()[model]
        charts = MetricChart.objects.filter(metric_model_name=model)
        for chart in charts:
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                order_by = "input_date_time"
                inputs = data_set["inputs"]
                output = data_set["output"]["name"]
                d = {}
                for input_name, input_value in inputs.iteritems():
                    d[input_name] = input_value
                entries = metric_model.objects.filter(**d).order_by(order_by)
                if len(entries):
                    entry = entries.first()
                    value = getattr(entry, output)
                    if value == -1:
                        chart.last_build_status = fun_test.FAILED
                        chart.last_build_date = get_current_time()
                        chart.save()
                        break


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        self.lsf_status_server = LsfStatusServer()
        tags = [ALLOC_SPEED_TEST_TAG, VOLTEST_TAG, BOOT_TIMING_TEST_TAG, TERAMARK_PKE, TERAMARK_CRYPTO, TERAMARK_LOOKUP,
                FLOW_TEST_TAG, F1_FLOW_TEST_TAG, TERAMARK_ZIP, TERAMARK_DFA, TERAMARK_NFA, TERAMARK_EC, TERAMARK_JPEG,
                SOAK_DMA_MEMCPY_COH,
                SOAK_DMA_MEMCPY_NON_COH, SOAK_DMA_MEMSET, RCNVME_READ, RCNVME_RANDOM_READ, RCNVME_WRITE,
                RCNVME_RANDOM_WRITE]
        self.lsf_status_server.workaround(tags=tags)
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        invalidate_goodness_cache()


class PalladiumPerformanceTc(FunTestCase):
    tag = ALLOC_SPEED_TEST_TAG
    model = None
    result = fun_test.FAILED
    dt = get_rounded_time()

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def cleanup(self):
        pass

    def validate_job(self, validation_required=True):
        job_info = self.lsf_status_server.get_last_job(tag=self.tag)
        fun_test.test_assert(job_info, "Ensure Job Info exists")
        self.jenkins_job_id = job_info["jenkins_build_number"]
        self.job_id = job_info["job_id"]
        self.git_commit = job_info["git_commit"]
        self.git_commit = self.git_commit.replace("https://github.com/fungible-inc/FunOS/commit/", "")
        if validation_required:
            fun_test.test_assert(not job_info["return_code"], "Valid return code")
            fun_test.test_assert("output_text" in job_info, "output_text found in job info: {}".format(self.job_id))
        lines = job_info["output_text"].split("\n")
        dt = job_info["date_time"]

        fun_test.test_assert(is_job_from_today(dt), "Last job is from today")
        self.job_info = job_info
        self.lines = lines
        self.dt = dt

        return True

    def metrics_to_dict(self, metrics, result):
        d = {}
        d["input_date_time"] = self.dt
        d["status"] = result
        for key, value in metrics.iteritems():
            d[key] = value
        return d

    def validate_json_file(self, file_paths, validation_required=True):
        self.lines = []
        for names in file_paths:
            file_path = LOGS_DIR + "/" + names
            fun_test.test_assert(os.path.isfile(file_path), "Ensure Json exists")
            fun_test.test_assert(os.access(file_path, os.R_OK), "Ensure read access for the file")
            with open(file_path) as fp:
                data = json.loads(fp.read())
                self.lines.append(data)
        return True


class AllocSpeedPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Alloc speed test",
                              steps="Steps 1")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):

        output_one_malloc_free_wu = 0
        output_one_malloc_free_threaded = 0
        output_one_malloc_free_classic_min = output_one_malloc_free_classic_avg = output_one_malloc_free_classic_max = -1
        wu_alloc_stack_ns_min = wu_alloc_stack_ns_max = wu_alloc_stack_ns_avg = -1
        wu_ungated_ns_min = wu_ungated_ns_max = wu_ungated_ns_avg = -1
        try:

            alloc_speed_test_found = False
            wu_latency_test_found = False

            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(r'Time for one fun_malloc\+fun_free \(WU\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]',
                              line)
                if m:
                    alloc_speed_test_found = True
                    d = json.loads(m.group(1))
                    output_one_malloc_free_wu = int(d["avg"])
                    output_one_malloc_free_wu_unit = d["unit"]
                m = re.search(
                    r'Time for one fun_malloc\+fun_free \(threaded\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_threaded_ns\]',
                    line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_threaded = int(d['avg'])
                    output_one_malloc_free_threaded_unit = d["unit"]
                m = re.search(
                    r'Time for one malloc\+free \(classic\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_classic_ns\]', line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_classic_avg = int(d['avg'])
                    output_one_malloc_free_classic_min = int(d['min'])
                    output_one_malloc_free_classic_max = int(d['max'])
                    output_one_malloc_free_classic_avg_unit = d["unit"]
                    output_one_malloc_free_classic_min_unit = d["unit"]
                    output_one_malloc_free_classic_max_unit = d["unit"]

                # wu_latency_test
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_alloc_stack_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_alloc_stack_ns_min = int(d["min"])
                    wu_alloc_stack_ns_avg = int(d["avg"])
                    wu_alloc_stack_ns_max = int(d["max"])
                    wu_alloc_stack_ns_min_unit = d["unit"]
                    wu_alloc_stack_ns_avg_unit = d["unit"]
                    wu_alloc_stack_ns_max_unit = d["unit"]
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_ungated_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_ungated_ns_min = int(d["min"])
                    wu_ungated_ns_avg = int(d["avg"])
                    wu_ungated_ns_max = int(d["max"])
                    wu_ungated_ns_min_unit = d["unit"]
                    wu_ungated_ns_avg_unit = d["unit"]
                    wu_ungated_ns_max_unit = d["unit"]

            fun_test.log("Malloc Free threaded: {}".format(output_one_malloc_free_threaded))
            fun_test.log("Malloc Free WU: {}".format(output_one_malloc_free_wu))
            fun_test.log("Malloc Free classic: min: {}, avg: {}, max: {}".format(output_one_malloc_free_classic_min,
                                                                                 output_one_malloc_free_classic_avg,
                                                                                 output_one_malloc_free_classic_max))
            fun_test.log("wu_latency_test: wu_alloc_stack_ns: min: {}, avg: {}, max: {}".format(wu_alloc_stack_ns_min,
                                                                                                wu_alloc_stack_ns_avg,
                                                                                                wu_alloc_stack_ns_max))
            fun_test.log("wu_latency_test: wu_ungated_ns: min: {}, avg: {}, max: {}".format(wu_ungated_ns_min,
                                                                                            wu_ungated_ns_avg,
                                                                                            wu_ungated_ns_max))
            self.result = RESULTS["PASSED"]
        except Exception as ex:
            fun_test.critical(str(ex))
        if self.result == fun_test.PASSED:
            MetricHelper(model=AllocSpeedPerformance).add_entry(status=self.result,
                                                                input_app="alloc_speed_test",
                                                                output_one_malloc_free_wu=output_one_malloc_free_wu,
                                                                output_one_malloc_free_threaded=output_one_malloc_free_threaded,
                                                                output_one_malloc_free_classic_min=output_one_malloc_free_classic_min,
                                                                output_one_malloc_free_classic_avg=output_one_malloc_free_classic_avg,
                                                                output_one_malloc_free_classic_max=output_one_malloc_free_classic_max,
                                                                output_one_malloc_free_wu_unit=output_one_malloc_free_wu_unit,
                                                                output_one_malloc_free_threaded_unit=output_one_malloc_free_threaded_unit,
                                                                output_one_malloc_free_classic_min_unit=output_one_malloc_free_classic_min_unit,
                                                                output_one_malloc_free_classic_avg_unit=output_one_malloc_free_classic_avg_unit,
                                                                output_one_malloc_free_classic_max_unit=output_one_malloc_free_classic_max_unit,
                                                                input_date_time=self.dt)

            MetricHelper(model=WuLatencyUngated).add_entry(status=self.result, input_app="wu_latency_test",
                                                           output_min=wu_ungated_ns_min,
                                                           output_max=wu_ungated_ns_max,
                                                           output_avg=wu_ungated_ns_avg,
                                                           output_min_unit=wu_ungated_ns_min_unit,
                                                           output_max_unit=wu_ungated_ns_max_unit,
                                                           output_avg_unit=wu_ungated_ns_avg_unit,
                                                           input_date_time=self.dt)

            MetricHelper(model=WuLatencyAllocStack).add_entry(status=self.result,
                                                              input_app="wu_latency_test",
                                                              output_min=wu_alloc_stack_ns_min,
                                                              output_max=wu_alloc_stack_ns_max,
                                                              output_avg=wu_alloc_stack_ns_avg,
                                                              output_min_unit=wu_alloc_stack_ns_min_unit,
                                                              output_max_unit=wu_alloc_stack_ns_max_unit,
                                                              output_avg_unit=wu_alloc_stack_ns_avg_unit,
                                                              input_date_time=self.dt)

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="AllocSpeedPerformance")
        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="WuLatencyUngated")
        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="WuLatencyAllocStack")

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class BcopyPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Bcopy performance",
                              steps="Steps 1")

    def run(self):
        plain = ""
        coherent = ""
        size = -1
        iterations = -1
        latency_units = ""
        latency_min = -1
        latency_max = -1
        latency_avg = -1
        latency_perf_name = ""
        average_bandwidth = -1
        average_bandwidth_perf_name = ""
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            m = None
            n = None

            for line in self.lines:
                if not m:
                    m = re.search(
                        r'bcopy \((?P<coherent>\S+),\s+(?P<plain>\S+)\) (?P<size>\S+) (?P<iterations>\d+) times;\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>.*)\]',
                        line)
                if not n:
                    n = re.search(
                        r'bcopy \((?P<coherent>\S+),\s+(?P<plain>\S+)\) (?P<size>\S+) (?P<iterations>\d+) times;\s+average bandwidth: (?P<bandwidth_json>{.*})\s+\[(?P<average_bandwidth_perf_name>.*)\]',
                        line)
                if m and n:
                    stats_found = True
                    coherent = "Coherent"
                    if m.group("coherent") != "coherent":
                        coherent = "Non-coherent"
                    plain = "Plain"
                    if m.group("plain") != "plain":
                        plain = "DMA"
                    size = m.group("size")
                    fun_test.test_assert(size.endswith("KB"), "Size should be in KB")
                    size = int(size.replace("KB", ""))

                    iterations = int(m.group("iterations"))
                    latency_units = m.group("latency_units")
                    try:
                        fun_test.test_assert_expected(expected="nsecs", actual=latency_units,
                                                      message="Latency in nsecs")
                    except:
                        pass
                    latency_json_raw = m.group("latency_json")
                    latency_json = json.loads(latency_json_raw)
                    latency_min = latency_json["min"]
                    latency_max = latency_json["max"]
                    latency_avg = latency_json["avg"]
                    latency_unit = latency_json["unit"]
                    latency_perf_name = m.group("latency_perf_name")
                    bandwidth_json = json.loads(n.group("bandwidth_json"))
                    average_bandwidth_unit = bandwidth_json["unit"]
                    try:
                        fun_test.test_assert(average_bandwidth_unit.endswith("Gbps"), "Avg bw should be Gbps")
                        average_bandwidth = int(bandwidth_json["value"])
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    average_bandwidth_perf_name = n.group("average_bandwidth_perf_name")
                    MetricHelper(model=BcopyPerformance).add_entry(status=self.result,
                                                                   input_date_time=self.dt,
                                                                   input_plain=plain,
                                                                   input_coherent=coherent,
                                                                   input_size=size,
                                                                   input_iterations=iterations,
                                                                   output_latency_units=latency_units,
                                                                   output_latency_min=latency_min,
                                                                   output_latency_max=latency_max,
                                                                   output_latency_avg=latency_avg,
                                                                   output_latency_min_unit=latency_unit,
                                                                   output_latency_max_unit=latency_unit,
                                                                   output_latency_avg_unit=latency_unit,
                                                                   input_latency_perf_name=latency_perf_name,
                                                                   output_average_bandwith=average_bandwidth,
                                                                   output_average_bandwith_unit=average_bandwidth_unit,
                                                                   input_average_bandwith_perf_name=average_bandwidth_perf_name)
                    m = None
                    n = None
            self.result = fun_test.PASSED
            # if self.result == fun_test.PASSED:


        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="BcopyPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class BcopyFloodPerformanceTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=3,
                              summary="bcopy flood performance",
                              steps="Steps 1")

    def run(self):
        latency_units = latency_perf_name = average_bandwidth_perf_name = ""
        size = n = latency_min = latency_max = latency_avg = average_bandwidth = -1
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'bcopy flood with dma \((?P<N>\d+)\)\s+(?P<size>\S+);\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>\S+)\];\s+average bandwidth: (?P<bandwidth_json>{.*})\s+\[(?P<average_bandwidth_perf_name>\S+)\]',
                    line)
                if m:
                    n = m.group("N")
                    size = m.group("size")
                    fun_test.test_assert(size.endswith("KB"), "Size should be in KB")
                    size = int(size.replace("KB", ""))
                    latency_units = m.group("latency_units")
                    try:
                        fun_test.test_assert_expected(expected="nsecs", actual=latency_units,
                                                      message="Latency in nsecs")
                    except:
                        pass
                    latency_json_raw = m.group("latency_json")
                    latency_json = json.loads(latency_json_raw)
                    latency_min = latency_json["min"]
                    latency_max = latency_json["max"]
                    latency_avg = latency_json["avg"]
                    latency_unit = latency_json["unit"]
                    latency_perf_name = m.group("latency_perf_name")
                    bandwidth_json = json.loads(m.group("bandwidth_json"))
                    average_bandwidth_unit = bandwidth_json["unit"]
                    try:
                        fun_test.test_assert(average_bandwidth_unit.endswith("Gbps"), "Avg bw should be Gbps")
                        average_bandwidth = int(bandwidth_json["value"])
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    average_bandwidth_perf_name = m.group("average_bandwidth_perf_name")

                    MetricHelper(model=BcopyFloodDmaPerformance).add_entry(status=self.result,
                                                                           input_date_time=self.dt,
                                                                           input_n=n,
                                                                           input_size=size,
                                                                           output_latency_units=latency_units,
                                                                           output_latency_min=latency_min,
                                                                           output_latency_max=latency_max,
                                                                           output_latency_avg=latency_avg,
                                                                           output_latency_min_unit=latency_unit,
                                                                           output_latency_max_unit=latency_unit,
                                                                           output_latency_avg_unit=latency_unit,
                                                                           input_latency_perf_name=latency_perf_name,
                                                                           output_average_bandwith=average_bandwidth,
                                                                           output_average_bandwith_unit=average_bandwidth_unit,
                                                                           input_average_bandwith_perf_name=average_bandwidth_perf_name
                                                                           )
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="BcopyFloodDmaPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class EcPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_EC

    def describe(self):
        self.set_test_details(id=4,
                              summary="EC performance",
                              steps="Steps 1")

    def run(self):
        ec_encode_latency_min = ec_encode_latency_max = ec_encode_latency_avg = -1
        ec_encode_throughput_min = ec_encode_throughput_max = ec_encode_throughput_avg = -1
        ec_recovery_latency_min = ec_recovery_latency_max = ec_recovery_latency_avg = -1
        ec_recovery_throughput_min = ec_recovery_throughput_max = ec_recovery_throughput_avg = -1

        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:

                m = re.search(r'Aggregated.*\s+(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_encode_latency)\]',
                              line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_encode_latency_min = int(d["min"])
                    ec_encode_latency_max = int(d["max"])
                    ec_encode_latency_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    encode_latency_unit = d["unit"]

                m = re.search(r'Aggregated.*\s+(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_encode_throughput)\]',
                              line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_encode_throughput_min = int(d["min"])
                    ec_encode_throughput_max = int(d["max"])
                    ec_encode_throughput_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    encode_throughput_unit = d["unit"]

                m = re.search(r'Aggregated.*\s+(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_recovery_latency)\]',
                              line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_recovery_latency_min = int(d["min"])
                    ec_recovery_latency_max = int(d["max"])
                    ec_recovery_latency_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    recovery_latency_unit = d["unit"]

                m = re.search(r'Aggregated.*\s+(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_recovery_throughput)\]',
                              line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_recovery_throughput_min = int(d["min"])
                    ec_recovery_throughput_max = int(d["max"])
                    ec_recovery_throughput_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    recovery_throughput_unit = d["unit"]
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))
        if self.result == fun_test.PASSED:
            MetricHelper(model=EcPerformance).add_entry(status=self.result,
                                                        input_date_time=self.dt,
                                                        output_encode_latency_min=ec_encode_latency_min,
                                                        output_encode_latency_max=ec_encode_latency_max,
                                                        output_encode_latency_avg=ec_encode_latency_avg,
                                                        output_encode_throughput_min=ec_encode_throughput_min,
                                                        output_encode_throughput_max=ec_encode_throughput_max,
                                                        output_encode_throughput_avg=ec_encode_throughput_avg,
                                                        output_recovery_latency_min=ec_recovery_latency_min,
                                                        output_recovery_latency_max=ec_recovery_latency_max,
                                                        output_recovery_latency_avg=ec_recovery_latency_avg,
                                                        output_recovery_throughput_min=ec_recovery_throughput_min,
                                                        output_recovery_throughput_max=ec_recovery_throughput_max,
                                                        output_recovery_throughput_avg=ec_recovery_throughput_avg,
                                                        output_encode_latency_min_unit=encode_latency_unit,
                                                        output_encode_latency_max_unit=encode_latency_unit,
                                                        output_encode_latency_avg_unit=encode_latency_unit,
                                                        output_encode_throughput_min_unit=encode_throughput_unit,
                                                        output_encode_throughput_max_unit=encode_throughput_unit,
                                                        output_encode_throughput_avg_unit=encode_throughput_unit,
                                                        output_recovery_latency_min_unit=recovery_latency_unit,
                                                        output_recovery_latency_max_unit=recovery_latency_unit,
                                                        output_recovery_latency_avg_unit=recovery_latency_unit,
                                                        output_recovery_throughput_min_unit=recovery_throughput_unit,
                                                        output_recovery_throughput_max_unit=recovery_throughput_unit,
                                                        output_recovery_throughput_avg_unit=recovery_throughput_unit
                                                        )
        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="EcPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class EcVolPerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_TAG

    def describe(self):
        self.set_test_details(id=5,
                              summary="EC Vol performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'(?:\s+\d+:\s+)?(?P<metric_type>\S+):\s+(?P<value>{.*})\s+\[\S+:(?P<metric_name>\S+)\]',
                    line)
                if m:
                    metric_type = m.group("metric_type")
                    value = m.group("value")
                    j = json.loads(value)
                    metric_name = m.group("metric_name").lower()
                    if not (
                            "ECVOL_EC_STATS_latency_ns".lower() in metric_name or "ECVOL_EC_STATS_iops".lower() in metric_name):
                        continue

                    try:  # Either a raw value or json value
                        for key, value in j.iteritems():
                            if key != "unit" and key != "value":
                                metrics["output_" + metric_name + "_" + key] = value
                                metrics["output_" + metric_name + "_" + key + "_unit"] = j["unit"]
                            if key == "value":
                                metrics["output_" + metric_name] = value
                                metrics["output_" + metric_name + "_unit"] = j["unit"]
                    except:
                        metrics["output_" + metric_name] = value
                        metrics["output_" + metric_name + "_unit"] = j["unit"]
                    d = self.metrics_to_dict(metrics, self.result)
                    MetricHelper(model=EcVolPerformance).add_entry(**d)
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="EcVolPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class VoltestPerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_TAG

    def describe(self):
        self.set_test_details(id=6,
                              summary="Voltest performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'"(?P<metric_name>\S+)\s+(?:\S+\s+\d+:\s+)?(?P<metric_type>\S+):\s+(?P<value>{.*})\s+\[(?P<metric_id>\S+)\]',
                    line)
                if m:
                    stats_found = True
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

                    if "andwidth" in metric_type.lower():
                        if "avg_op_bw_mbps" in line:
                            metric_type += "_avg"
                        elif "total_op_bw_mbps":
                            metric_type += "_total"

                    try:  # Either a raw value or json value
                        for key, value in j.iteritems():
                            if key != "unit" and key != "value":
                                metrics["output_" + metric_name + "_" + metric_type + "_" + key] = value
                                metrics["output_" + metric_name + "_" + metric_type + "_" + key + "_unit"] = j["unit"]
                            if key == "value":
                                metrics["output_" + metric_name + "_" + metric_type] = value
                                metrics["output_" + metric_name + "_" + metric_type + "_unit"] = j["unit"]
                    except Exception as ex:
                        metrics["output_" + metric_name + "_" + metric_type] = value
                        metrics["output_" + metric_name + "_" + metric_type + "_unit"] = j["unit"]
                    d = self.metrics_to_dict(metrics, self.result)
                    MetricHelper(model=VoltestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="VoltestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class WuDispatchTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=7,
                              summary="Wu Dispatch Test performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            i = 0

            for line in self.lines:
                m = re.search(
                    r'Average\s+dispatch\s+WU\s+(?P<average_json>{.*})\s+\[(?P<metric_name>wu_dispatch_latency_cycles)\]',
                    line)
                if m:
                    average_json = json.loads(m.group("average_json"))
                    output_average = int(average_json["value"])
                    unit = average_json["unit"]
                    input_app = "dispatch_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    metrics["output_average_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=WuDispatchTestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="WuDispatchTestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class WuSendSpeedTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=8,
                              summary="Wu Send Speed Test performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            i = 0

            for line in self.lines:
                m = re.search(
                    r'Average\s+WU\s+send\s+ungated\s+(?P<average_json>{.*})\s+\[(?P<metric_name>wu_send_ungated_latency_cycles)\]',
                    line)
                if m:
                    average_json = json.loads(m.group("average_json"))
                    output_average = int(average_json["value"])
                    unit = average_json["unit"]
                    input_app = "wu_send_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    metrics["output_average_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=WuSendSpeedTestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="WuSendSpeedTestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class FunMagentPerformanceTestTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=9,
                              summary="Fun Magent Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'fun_magent.*=>\s+(?P<latency_json>{.*})\s+\[(?P<metric_name>fun_magent_rate_malloc_free_per_sec)\]',
                    line)
                if m:
                    latency_json = json.loads(m.group("latency_json"))
                    unit = latency_json["unit"]
                    output_latency = int(latency_json["value"])
                    input_app = "fun_magent_perf_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("latency: {}, metric_name: {}".format(output_latency, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_latency"] = output_latency
                    metrics["output_latency_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=FunMagentPerformanceTest).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="FunMagentPerformanceTest")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class WuStackSpeedTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=10,
                              summary="Wu Send Speed Test performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'Average\s+wustack\s+alloc/+free\s+cycles:\s+(?P<average_json>{.*})\[(?P<metric_name>wustack_alloc_free_cycles)\]',
                    line)
                if m:
                    average_json = json.loads(m.group("average_json"))
                    output_average = int(average_json["value"])
                    unit = average_json["unit"]
                    input_app = "wustack_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    metrics["output_average_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=WuStackSpeedTestPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="WuStackSpeedTestPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class SoakFunMallocPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=11,
                              summary="Soak fun malloc Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>soak_two_fun_malloc_fun_free)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "soak_malloc_fun_malloc"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=SoakFunMallocPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="SoakFunMallocPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class SoakClassicMallocPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG

    def describe(self):
        self.set_test_details(id=12,
                              summary="Soak classic malloc Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>soak_two_classic_malloc_free)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "soak_malloc_classic"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=SoakClassicMallocPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="SoakClassicMallocPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class BootTimingPerformanceTc(PalladiumPerformanceTc):
    tag = BOOT_TIMING_TEST_TAG

    def describe(self):
        self.set_test_details(id=13,
                              summary="Boot Timing Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        reset_cut_done = False
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            log = self.lsf_status_server.get_raw_file(job_id=self.job_id, file_name="cdn_uartout1.txt")
            fun_test.test_assert(log, "fetched boot time uart log")
            log = log.split("\n")
            for line in log:
                if "Reset CUT done!" in line:
                    reset_cut_done = True
                if reset_cut_done:
                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Firmware',
                        line)
                    if m:
                        output_firmware_boot_time = int(m.group("time")) / 1000.0
                        output_firmware_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: Firmware, boot time: {}, boot cycles: {}".format(output_firmware_boot_time,
                                                                                         output_firmware_boot_cycles))
                        metrics["output_firmware_boot_time"] = output_firmware_boot_time
                        metrics["output_firmware_boot_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Flash\s+type\s+detection',
                        line)
                    if m:
                        output_flash_type_boot_time = int(m.group("time")) / 1000.0
                        output_flash_type_boot_cycles = int(m.group("cycle"))
                        fun_test.log("boot type: Flash type detection, boot time: {}, boot cycles: {}".format(
                            output_flash_type_boot_time,
                            output_flash_type_boot_cycles))
                        metrics["output_flash_type_boot_time"] = output_flash_type_boot_time
                        metrics["output_flash_type_boot_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+EEPROM\s+Loading',
                        line)
                    if m:
                        output_eeprom_boot_time = int(m.group("time")) / 1000.0
                        output_eeprom_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: EEPROM Loading, boot time: {}, boot cycles: {}".format(output_eeprom_boot_time,
                                                                                               output_eeprom_boot_cycles))
                        metrics["output_eeprom_boot_time"] = output_eeprom_boot_time
                        metrics["output_eeprom_boot_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+SBUS\s+Loading',
                        line)
                    if m:
                        output_sbus_boot_time = int(m.group("time")) / 1000.0
                        output_sbus_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: SBUS Loading, boot time: {}, boot cycles: {}".format(output_sbus_boot_time,
                                                                                             output_sbus_boot_cycles))
                        metrics["output_sbus_boot_time"] = output_sbus_boot_time
                        metrics["output_sbus_boot_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Host\s+BOOT',
                        line)
                    if m:
                        output_host_boot_time = int(m.group("time")) / 1000.0
                        output_host_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: Host BOOT, boot time: {}, boot cycles: {}".format(output_host_boot_time,
                                                                                          output_host_boot_cycles))
                        metrics["output_host_boot_time"] = output_host_boot_time
                        metrics["output_host_boot_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Main\s+Loop',
                        line)
                    if m:
                        output_main_loop_boot_time = int(m.group("time")) / 1000.0
                        output_main_loop_boot_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "boot type: Main Loop, boot time: {}, boot cycles: {}".format(output_main_loop_boot_time,
                                                                                          output_main_loop_boot_cycles))
                        metrics["output_main_loop_boot_time"] = output_main_loop_boot_time
                        metrics["output_main_loop_boot_time_unit"] = "msecs"

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
                        metrics["output_boot_success_boot_time"] = output_boot_success_boot_time
                        metrics["output_boot_success_boot_time_unit"] = "msecs"

            log = self.lsf_status_server.get_raw_file(job_id=self.job_id, file_name="cdn_uartout0.txt")
            fun_test.test_assert(log, "fetched mmc time uart log")
            log = log.split("\n")
            for line in log:
                if "Welcome to FunOS" in line:
                    break
                else:
                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+MMC\s+INIT',
                        line)
                    if m:
                        output_init_mmc_time = int(m.group("time")) / 1000.0
                        output_init_mmc_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "MMC INIT Time: {}, cycles: {}".format(output_init_mmc_time,
                                                                   output_init_mmc_cycles))
                        metrics["output_init_mmc_time"] = output_init_mmc_time
                        metrics["output_init_mmc_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+MMC\s+load\s+dest=(?P<dest>ffffffff90000000)\s+size=(?P<size>\d+)',
                        line)
                    if m:
                        output_boot_read_mmc_time = int(m.group("time")) / 1000.0
                        output_boot_read_mmc_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "MMC Boot Read Time: {}, cycles: {}".format(output_boot_read_mmc_time,
                                                                        output_boot_read_mmc_cycles))
                        metrics["output_boot_read_mmc_time"] = output_boot_read_mmc_time
                        metrics["output_boot_read_mmc_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+MMC\s+load\s+dest=(?P<dest>ffffffff91000000)\s+size=(?P<size>\d+)',
                        line)
                    if m:
                        output_funos_read_mmc_time = int(m.group("time")) / 1000.0
                        output_funos_read_mmc_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "MMC FunOS Read Time: {}, cycles: {}".format(output_funos_read_mmc_time,
                                                                         output_funos_read_mmc_cycles))
                        metrics["output_funos_read_mmc_time"] = output_funos_read_mmc_time
                        metrics["output_funos_read_mmc_time_unit"] = "msecs"

                    m = re.search(
                        r'\[(?P<time>\d+)\s+microseconds\]:\s+\((?P<cycle>\d+)\s+cycles\)\s+Start\s+ELF',
                        line)
                    if m:
                        output_funos_load_elf_time = int(m.group("time")) / 1000.0
                        output_funos_load_elf_cycles = int(m.group("cycle"))
                        fun_test.log(
                            "ELF FunOS Load Time: {}, cycles: {}".format(output_funos_load_elf_time,
                                                                         output_funos_load_elf_cycles))
                        metrics["output_funos_load_elf_time"] = output_funos_load_elf_time
                        metrics["output_funos_load_elf_time_unit"] = "msecs"

            d = self.metrics_to_dict(metrics, fun_test.PASSED)
            MetricHelper(model=BootTimePerformance).add_entry(**d)
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="BootTimePerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeRsaPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=14,
                              summary="TeraMark PKE RSA Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>RSA\s+CRT\s+2048\s+decryptions)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "pke_rsa_crt_dec_no_pad_soak"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeRsaPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkPkeRsaPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeRsa4kPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=15,
                              summary="TeraMark PKE RSA 4K Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>RSA\s+CRT\s+4096\s+decryptions)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "pke_rsa_crt_dec_no_pad_4096_soak"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeRsa4kPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkPkeRsa4kPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeEcdh256PerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=16,
                              summary="TeraMark PKE ECDH P256 Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>ECDH\s+P256)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "pke_ecdh_soak_256"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeEcdh256Performance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkPkeEcdh256Performance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeEcdh25519PerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=17,
                              summary="TeraMark PKE ECDH 25519 Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[(?P<metric_name>ECDH\s+25519)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "pke_ecdh_soak_25519"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=TeraMarkPkeEcdh25519Performance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkPkeEcdh25519Performance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkCryptoPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_CRYPTO
    model = "TeraMarkCryptoPerformance"

    def describe(self):
        self.set_test_details(id=18,
                              summary="TeraMark Crypto Performance Test",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'(?P<crypto_json>{"test".*})',
                    line)
                if m:
                    metrics = collections.OrderedDict()
                    crypto_json = json.loads(m.group("crypto_json"))
                    input_test = crypto_json["test"]
                    if self.model == "TeraMarkCryptoPerformance":
                        if "api" in input_test:
                            input_app = "crypto_api_perf"
                            input_algorithm = crypto_json["alg"]
                            input_operation = crypto_json["operation"]
                            pkt_size_json = crypto_json["pktsize"]
                            ops_json = crypto_json["ops"] if "ops" in crypto_json else None
                            bandwidth_json = crypto_json["throughput"]

                            input_pkt_size = int(pkt_size_json["value"])
                            output_ops_per_sec = int(ops_json["value"]) if ops_json else -1
                            output_throughput = float(bandwidth_json["value"])
                            unit = bandwidth_json["units"]

                            metrics["input_app"] = input_app
                            metrics["input_algorithm"] = input_algorithm
                            metrics["input_operation"] = input_operation
                            metrics["input_pkt_size"] = input_pkt_size
                            metrics["output_ops_per_sec"] = output_ops_per_sec
                            metrics["output_throughput"] = output_throughput
                            metrics["output_ops_per_sec_unit"] = "ops"
                            metrics["output_throughput_unit"] = unit
                            # metrics["output_latency_min"] = output_latency_min
                            # metrics["output_latency_avg"] = output_latency_avg
                            # metrics["output_latency_max"] = output_latency_max
                            d = self.metrics_to_dict(metrics, fun_test.PASSED)
                            metric_model = app_config.get_metric_models()[self.model]
                            MetricHelper(model=metric_model).add_entry(**d)
                    elif self.model == "TeraMarkMultiClusterCryptoPerformance":
                        if "raw" in input_test:
                            input_app = "crypto_raw_speed"
                            input_algorithm = crypto_json["alg"]
                            input_operation = crypto_json["operation"]
                            input_key_size = int(crypto_json["key_size"]) if "key_size" in crypto_json else -1
                            pkt_size_json = crypto_json["pktsize"]
                            ops_json = crypto_json["ops"] if "ops" in crypto_json else None
                            bandwidth_json = crypto_json["throughput"]

                            input_pkt_size = int(pkt_size_json["value"])
                            output_ops_per_sec = int(ops_json["value"]) if ops_json else -1
                            output_throughput = float(bandwidth_json["value"])
                            unit = bandwidth_json["units"]

                            metrics["input_app"] = input_app
                            metrics["input_key_size"] = input_key_size
                            metrics["input_algorithm"] = input_algorithm
                            metrics["input_operation"] = input_operation
                            metrics["input_pkt_size"] = input_pkt_size
                            metrics["output_ops_per_sec"] = output_ops_per_sec
                            metrics["output_throughput"] = output_throughput
                            metrics["output_ops_per_sec_unit"] = "ops"
                            metrics["output_throughput_unit"] = unit
                            # metrics["output_latency_min"] = output_latency_min
                            # metrics["output_latency_avg"] = output_latency_avg
                            # metrics["output_latency_max"] = output_latency_max
                            d = self.metrics_to_dict(metrics, fun_test.PASSED)
                            metric_model = app_config.get_metric_models()[self.model]
                            MetricHelper(model=metric_model).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkLookupEnginePerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_LOOKUP

    def describe(self):
        self.set_test_details(id=19,
                              summary="TeraMark Lookup Engine Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            teramark_begin = False
            for line in self.lines:
                if "TeraMark Begin" in line:
                    teramark_begin = True
                if teramark_begin:
                    m = re.search(
                        r'{\s+"memory":\s+"(?P<memory>.*)",\s+"unit":\s+"(?P<unit>\S+)",\s+"min":\s+(?P<minimum>\d+),\s+"avg":\s+(?P<average>\d+),\s+"max":\s+(?P<maximum>\d+)\s+}',
                        line)
                    if m:
                        input_memory = m.group("memory")
                        output_lookup_per_sec_min = int(m.group("minimum"))
                        output_lookup_per_sec_avg = int(m.group("average"))
                        output_lookup_per_sec_max = int(m.group("maximum"))
                        output_lookup_per_sec_min_unit = m.group("unit")
                        output_lookup_per_sec_avg_unit = m.group("unit")
                        output_lookup_per_sec_max_unit = m.group("unit")
                        input_test = "le_test_perf"
                        fun_test.log("memory: {}, lookup per sec: min {}, avg {}, max {}".format(input_memory,
                                                                                                 output_lookup_per_sec_min,
                                                                                                 output_lookup_per_sec_avg,
                                                                                                 output_lookup_per_sec_max))
                        metrics["input_test"] = input_test
                        metrics["input_memory"] = input_memory
                        metrics["output_lookup_per_sec_min"] = output_lookup_per_sec_min
                        metrics["output_lookup_per_sec_avg"] = output_lookup_per_sec_avg
                        metrics["output_lookup_per_sec_max"] = output_lookup_per_sec_max
                        metrics["output_lookup_per_sec_min_unit"] = output_lookup_per_sec_min_unit
                        metrics["output_lookup_per_sec_avg_unit"] = output_lookup_per_sec_avg_unit
                        metrics["output_lookup_per_sec_max_unit"] = output_lookup_per_sec_max_unit
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        MetricHelper(model=TeraMarkLookupEnginePerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkLookupEnginePerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class FlowTestPerformanceTC(PalladiumPerformanceTc):
    tag = FLOW_TEST_TAG
    model = "FlowTestPerformance"

    def describe(self):
        self.set_test_details(id=20,
                              summary="Flow Test Performance",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, date_time=self.dt)

            fun_test.test_assert(result["status"], "Checking if flow test passed")
            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkZipPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_ZIP

    def describe(self):
        self.set_test_details(id=21,
                              summary="TeraMark Zip Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            teramark_begin = False
            for line in self.lines:
                if "TeraMark Begin" in line:
                    teramark_begin = True
                if "TeraMark End" in line:
                    teramark_begin = False
                if teramark_begin:
                    m = re.search(
                        r'{"Type":\s+"(?P<type>\S+)",\s+"Operation":\s+(?P<operation>\S+),\s+"Effort":\s+(?P<effort>\S+),.*\s+"Duration"\s+:\s+(?P<latency_json>{.*}),\s+"Throughput":\s+(?P<throughput_json>{.*})}',
                        line)
                    if m:
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
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        if input_type == "Deflate":
                            MetricHelper(model=TeraMarkZipDeflatePerformance).add_entry(**d)
                        else:
                            MetricHelper(model=TeraMarkZipLzmaPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkZipDeflatePerformance")
        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkZipLzmaPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkDfaPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_DFA
    model = "TeraMarkDfaPerformance"

    def describe(self):
        self.set_test_details(id=22,
                              summary="TeraMark DFA Performance Test on F1",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, date_time=self.dt)

            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkJpegPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_JPEG

    def describe(self):
        self.set_test_details(id=23,
                              summary="TeraMark Jpeg Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        current_file_name = None
        final_file_name = None
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            teramark_begin = False

            for line in self.lines:
                compression_ratio_found = False
                if "Compression-ratio to 1" in line:
                    compression_ratio_found = True
                m = re.search(r'JPEG Compression/Decompression performance stats (?P<current_file_name>\S+?)(?=#)',
                              line)
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
                    pass
                    m = re.search(r'({.*})', line)
                    if m:
                        j = m.group(1)
                        try:
                            d = json.loads(j)
                        except Exception as ex:
                            message = "Invalid json for : {}".format(j)
                            fun_test.critical(message)
                            raise Exception(message)

                        try:
                            metrics = {}
                            if not compression_ratio_found:
                                if d["Operation"] in jpeg_operations:
                                    metrics["input_operation"] = jpeg_operations[d["Operation"]]
                                else:
                                    metrics["input_operation"] = d["Operation"]
                                metrics["input_count"] = d['Stats']['_count']
                                metrics["input_image"] = final_file_name
                                # metrics["output_iops"] = d['Stats']['_iops']
                                # metrics["output_max_latency"] = d['Stats']['_max_latency']
                                # metrics["output_min_latency"] = d['Stats']['_min_latency']
                                # metrics["output_average_latency"] = d['Stats']['_avg_latency']
                                metrics["output_average_bandwidth"] = d['Stats']['_avg_bw_gbps']
                            else:
                                if d["Operation"] in jpeg_operations:
                                    metrics["input_operation"] = jpeg_operations[d["Operation"]]
                                else:
                                    metrics["input_operation"] = d["Operation"]
                                metrics["input_image"] = final_file_name
                                metrics["output_compression_ratio"] = d['Stats']["Compression-ratio to 1"]
                                metrics["output_percentage_savings"] = d['Stats']["PercentageSpaceSaving"]
                            d = self.metrics_to_dict(metrics, fun_test.PASSED)
                            MetricHelper(model=TeraMarkJpegPerformance).add_entry(**d)

                        except Exception as ex:
                            message = "Unable to add metric : {}".format(str(ex))
                            fun_test.critical(message)
                            raise Exception(message)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkJpegPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkNuTransitPerformanceTC(PalladiumPerformanceTc):
    model = "NuTransitPerformance"
    file_paths = ["nu_rfc2544_performance.json"]

    def describe(self):
        self.set_test_details(id=24,
                              summary="TeraMark HNU Transit Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_json_file(file_paths=self.file_paths), "validate json file and output")
            for file in self.lines:
                for line in file:
                    if "flow_type" in line:
                        if line["flow_type"] in nu_transit_flow_types:
                            line["flow_type"] = nu_transit_flow_types[line["flow_type"]]
                        metrics["input_flow_type"] = line["flow_type"].replace("FPG", "NU")
                        metrics["input_mode"] = line.get("mode", "")
                        metrics["input_version"] = line["version"]
                        metrics["input_frame_size"] = line["frame_size"]
                        date_time = get_time_from_timestamp(line["timestamp"])
                        metrics["output_throughput"] = (float(
                            line["throughput"]) / 1000) if "throughput" in line and line[
                            "throughput"] != -1 else -1
                        metrics["output_pps"] = (float(
                            line["pps"]) / 1000000) if "pps" in line and line[
                            "pps"] != -1 else -1
                        metrics["output_latency_max"] = line.get("latency_max", -1)
                        metrics["output_latency_min"] = line.get("latency_min", -1)
                        metrics["output_latency_avg"] = line.get("latency_avg", -1)
                        if self.model == "NuTransitPerformance":
                            metrics["output_latency_P99"] = line.get("latency_P99", -1)
                            metrics["output_latency_P90"] = line.get("latency_P90", -1)
                            metrics["output_latency_P50"] = line.get("latency_P50", -1)
                        metrics["input_number_flows"] = line.get("num_flows", 512000)
                        metrics["input_offloads"] = line.get("offloads", False)
                        metrics["input_protocol"] = line.get("protocol", "UDP")
                        metrics["output_jitter_max"] = line.get("jitter_max", -1)
                        metrics["output_jitter_min"] = line.get("jitter_min", -1)
                        metrics["output_jitter_avg"] = line.get("jitter_avg", -1)
                        fun_test.log(
                            "flow type: {}, latency: {}, bandwidth: {}, frame size: {}, jitters: {}, pps: {}".format(
                                metrics["input_flow_type"], metrics["output_latency_avg"], metrics["output_throughput"],
                                metrics["input_frame_size"], metrics["output_jitter_avg"], metrics["output_pps"]))
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        d["input_date_time"] = date_time
                        if date_time.year >= 2019:
                            metric_model = app_config.get_metric_models()[self.model]
                            MetricHelper(model=metric_model).add_entry(**d)
                        if metrics["input_flow_type"] in internal_chart_names_for_flows:
                            chart_names = internal_chart_names_for_flows[metrics["input_flow_type"]]
                            for names in chart_names:
                                if "throughput" in names:
                                    if metrics["output_throughput"] == -1 and metrics["input_frame_size"] == 800:
                                        set_chart_status(result=fun_test.FAILED,
                                                         suite_execution_id=fun_test.get_suite_execution_id(),
                                                         test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                                         git_commit="", internal_chart_name=names)
                                    else:
                                        set_chart_status(result=fun_test.PASSED,
                                                         suite_execution_id=fun_test.get_suite_execution_id(),
                                                         test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                                         git_commit="", internal_chart_name=names)
                                if "pps" in names:
                                    if metrics["output_pps"] == -1 and metrics["input_frame_size"] == 800:
                                        set_chart_status(result=fun_test.FAILED,
                                                         suite_execution_id=fun_test.get_suite_execution_id(),
                                                         test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                                         git_commit="", internal_chart_name=names)
                                    else:
                                        set_chart_status(result=fun_test.PASSED,
                                                         suite_execution_id=fun_test.get_suite_execution_id(),
                                                         test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                                         git_commit="", internal_chart_name=names)
                                if "latency" in names:
                                    if metrics["output_latency_avg"] == -1 and metrics["input_frame_size"] == 800:
                                        set_chart_status(result=fun_test.FAILED,
                                                         suite_execution_id=fun_test.get_suite_execution_id(),
                                                         test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                                         git_commit="", internal_chart_name=names)
                                    else:
                                        set_chart_status(result=fun_test.PASSED,
                                                         suite_execution_id=fun_test.get_suite_execution_id(),
                                                         test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                                         git_commit="", internal_chart_name=names)

            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class PkeX25519TlsSoakPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=25,
                              summary="ECDHE_RSA X25519 RSA 2K TLS Soak Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")

            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[TLS\s+1.2\s+SERVER\s+PKE\s+OPS\s+\((?P<metric_name>ECDHE_RSA\s+X25519\s+RSA\s+2K)\)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "pke_x25519_2k_tls_soak"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=PkeX25519TlsSoakPerformance).add_entry(**d)
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="PkeX25519TlsSoakPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class PkeP256TlsSoakPerformanceTC(PalladiumPerformanceTc):
    tag = TERAMARK_PKE

    def describe(self):
        self.set_test_details(id=26,
                              summary="ECDHE_RSA P256 RSA 2K TLS Soak Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'soak_bench\s+result\s+(?P<value_json>{.*})\s+\[TLS\s+1.2\s+SERVER\s+PKE\s+OPS\s+\((?P<metric_name>ECDHE_RSA\s+P256\s+RSA\s+2K)\)\]',
                    line)
                if m:
                    value_json = json.loads(m.group("value_json"))
                    output_ops_per_sec = float(value_json["value"])
                    unit = value_json["unit"]
                    input_app = "pke_p256_2k_tls_soak"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
                    metrics["output_ops_per_sec_unit"] = unit
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    MetricHelper(model=PkeP256TlsSoakPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="PkeP256TlsSoakPerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class SoakDmaMemcpyCohPerformanceTC(PalladiumPerformanceTc):
    tag = SOAK_DMA_MEMCPY_COH
    model = "SoakDmaMemcpyCoherentPerformance"

    def describe(self):
        self.set_test_details(id=27,
                              summary="Soak DMA memcpy coherent Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            for line in self.lines:
                m = re.search(
                    r'Bandwidth\s+for\s+DMA\s+(?P<operation>\S+)\s+for\s+size\s+(?P<size>\S+):\s+(?P<bandwidth_json>.*)\s+\[(?P<metric_name>\S+)\]',
                    line)
                if m:
                    input_operation = m.group("operation")
                    input_size = m.group("size")
                    bandwidth_json = json.loads(m.group("bandwidth_json"))
                    output_bandwidth = float(bandwidth_json["value"])
                    unit = bandwidth_json["unit"]
                    input_log_size = bandwidth_json["log_size"]
                    if self.model == "SoakDmaMemsetPerformance":
                        if "non_coh" in bandwidth_json:
                            input_non_coherent = bandwidth_json["non_coh"]
                            metrics["input_coherent"] = False if input_non_coherent == 1 else True
                        elif "bm" in bandwidth_json:
                            input_bm = bandwidth_json["bm"]
                            metrics["input_buffer_memory"] = True if input_bm == 1 else False
                    metric_name = m.group("metric_name")
                    metrics["input_size"] = input_size
                    metrics["input_operation"] = input_operation
                    metrics["output_bandwidth"] = output_bandwidth
                    metrics["output_bandwidth_unit"] = unit
                    metrics["input_log_size"] = input_log_size
                    metrics["input_metric_name"] = metric_name
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    metric_model = app_config.get_metric_models()[self.model]
                    MetricHelper(model=metric_model).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class SoakDmaMemcpyNonCohPerformanceTC(SoakDmaMemcpyCohPerformanceTC):
    tag = SOAK_DMA_MEMCPY_NON_COH
    model = "SoakDmaMemcpyNonCoherentPerformance"

    def describe(self):
        self.set_test_details(id=28,
                              summary="Soak DMA memcpy Non coherent Performance Test",
                              steps="Steps 1")


class SoakDmaMemsetPerformanceTC(SoakDmaMemcpyCohPerformanceTC):
    tag = SOAK_DMA_MEMSET
    model = "SoakDmaMemsetPerformance"

    def describe(self):
        self.set_test_details(id=29,
                              summary="Soak DMA memset Performance Test",
                              steps="Steps 1")


class TeraMarkMultiClusterCryptoPerformanceTC(TeraMarkCryptoPerformanceTC):
    tag = TERAMARK_CRYPTO
    model = "TeraMarkMultiClusterCryptoPerformance"

    def describe(self):
        self.set_test_details(id=30,
                              summary="TeraMark Multi Cluster Crypto Performance Test",
                              steps="Steps 1")


class F1FlowTestPerformanceTC(FlowTestPerformanceTC):
    tag = F1_FLOW_TEST_TAG
    model = "F1FlowTestPerformance"

    def describe(self):
        self.set_test_details(id=31,
                              summary="Flow Test Performance on F1",
                              steps="Steps 1")


class TeraMarkNfaPerformanceTC(TeraMarkDfaPerformanceTC):
    tag = TERAMARK_NFA
    model = "TeraMarkNfaPerformance"

    def describe(self):
        self.set_test_details(id=32,
                              summary="TeraMark NFA Performance Test on F1",
                              steps="Steps 1")


class TeraMarkJuniperNetworkingPerformanceTC(TeraMarkNuTransitPerformanceTC):
    file_paths = ["nu_rfc2544_fwd_performance.json"]
    model = "TeraMarkJuniperNetworkingPerformance"

    def describe(self):
        self.set_test_details(id=33,
                              summary="TeraMark Juniper Networking Performance Test",
                              steps="Steps 1")


class TeraMarkRcnvmeReadPerformanceTC(PalladiumPerformanceTc):
    tag = RCNVME_READ
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=34,
                              summary="TeraMark rcnvme read Performance Test on F1",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, date_time=self.dt)

            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkRcnvmeRandomReadPerformanceTC(TeraMarkRcnvmeReadPerformanceTC):
    tag = RCNVME_RANDOM_READ
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=35,
                              summary="TeraMark rcnvme random read Performance Test on F1",
                              steps="Steps 1")


class TeraMarkRcnvmeWritePerformanceTC(TeraMarkRcnvmeReadPerformanceTC):
    tag = RCNVME_WRITE
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=36,
                              summary="TeraMark rcnvme write Performance Test on F1",
                              steps="Steps 1")


class TeraMarkRcnvmeRandomWritePerformanceTC(TeraMarkRcnvmeReadPerformanceTC):
    tag = RCNVME_RANDOM_WRITE
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=37,
                              summary="TeraMark rcnvme random write Performance Test on F1",
                              steps="Steps 1")


class TeraMarkHuPerformanceTC(PalladiumPerformanceTc):
    file_paths = ["hu_funeth_performance_data.json"]

    def describe(self):
        self.set_test_details(id=38,
                              summary="TeraMark HU Funeth Performance Test",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_json_file(file_paths=self.file_paths), "validate json file and output")
            for file in self.lines:
                for line in file:
                    if "flow_type" in line:
                        metrics = collections.OrderedDict()
                        metrics["input_flow_type"] = line["flow_type"]
                        metrics["input_frame_size"] = line["frame_size"]
                        metrics["input_number_flows"] = line.get("num_flows", 1)
                        metrics["input_offloads"] = line.get("offloads", False)
                        metrics["input_protocol"] = line.get("protocol", "TCP")
                        metrics["input_version"] = line.get("version", "")
                        date_time = get_time_from_timestamp(line["timestamp"])
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
                        else:
                            self.add_entries_into_dual_table(default_metrics=metrics, line=line, date_time=date_time)
                            continue
                        fun_test.log(
                            "flow type: {}, frame size: {}, date time: {}".format(
                                metrics["input_flow_type"], metrics["input_frame_size"], date_time))
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        d["input_date_time"] = date_time
                        metric_model = app_config.get_metric_models()[self.model]
                        MetricHelper(model=metric_model).add_entry(**d)

            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        set_networking_chart_status()
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")

    def add_entries_into_dual_table(self, default_metrics, line, date_time):
        metrics = dict(default_metrics)
        self.model = "HuThroughputPerformance"
        if metrics["input_flow_type"] == "HU_NU_NFCP":
            metrics["output_throughput_h2n"] = (float(
                line["throughput"]) / 1000) if line["throughput"] != -1 else -1
            metrics["output_pps_h2n"] = (float(
                line["pps"]) / 1000000) if line["pps"] != -1 else -1
        else:
            metrics["output_throughput_n2h"] = (float(
                line["throughput"]) / 1000) if line["throughput"] != -1 else -1
            metrics["output_pps_n2h"] = (float(
                line["pps"]) / 1000000) if line["pps"] != -1 else -1
        d = self.metrics_to_dict(metrics, fun_test.PASSED)
        d["input_date_time"] = date_time
        metric_model = app_config.get_metric_models()[self.model]
        MetricHelper(model=metric_model).add_entry(**d)
        metrics = dict(default_metrics)
        self.model = "HuLatencyPerformance"
        if metrics["input_flow_type"] == "HU_NU_NFCP":
            metrics["output_latency_max_h2n"] = line.get("latency_max", -1)
            metrics["output_latency_min_h2n"] = line.get("latency_min", -1)
            metrics["output_latency_avg_h2n"] = line.get("latency_avg", -1)
            metrics["output_latency_P99_h2n"] = line.get("latency_P99", -1)
            metrics["output_latency_P90_h2n"] = line.get("latency_P90", -1)
            metrics["output_latency_P50_h2n"] = line.get("latency_P50", -1)
        else:
            metrics["output_latency_max_n2h"] = line.get("latency_max", -1)
            metrics["output_latency_min_n2h"] = line.get("latency_min", -1)
            metrics["output_latency_avg_n2h"] = line.get("latency_avg", -1)
            metrics["output_latency_P99_n2h"] = line.get("latency_P99", -1)
            metrics["output_latency_P90_n2h"] = line.get("latency_P90", -1)
            metrics["output_latency_P50_n2h"] = line.get("latency_P50", -1)
        d = self.metrics_to_dict(metrics, fun_test.PASSED)
        d["input_date_time"] = date_time
        metric_model = app_config.get_metric_models()[self.model]
        MetricHelper(model=metric_model).add_entry(**d)


class PrepareDbTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=100,
                              summary="Prepare Status Db",
                              steps="Steps 1")

    def setup(self):
        pass

    def run(self):
        prepare_status_db()
        TimeKeeper.set_time(name=LAST_ANALYTICS_DB_STATUS_UPDATE, time=get_current_time())

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()

    # myscript.add_test_case(AllocSpeedPerformanceTc())
    # myscript.add_test_case(BcopyPerformanceTc())
    # myscript.add_test_case(BcopyFloodPerformanceTc())
    # myscript.add_test_case(EcPerformanceTc())
    # myscript.add_test_case(EcVolPerformanceTc())
    # myscript.add_test_case(VoltestPerformanceTc())
    # myscript.add_test_case(WuDispatchTestPerformanceTc())
    # myscript.add_test_case(WuSendSpeedTestPerformanceTc())
    # myscript.add_test_case(FunMagentPerformanceTestTc())
    # myscript.add_test_case(WuStackSpeedTestPerformanceTc())
    # myscript.add_test_case(SoakFunMallocPerformanceTc())
    # myscript.add_test_case(SoakClassicMallocPerformanceTc())
    # myscript.add_test_case(BootTimingPerformanceTc())
    # myscript.add_test_case(TeraMarkPkeRsaPerformanceTC())
    # myscript.add_test_case(TeraMarkPkeRsa4kPerformanceTC())
    # myscript.add_test_case(TeraMarkPkeEcdh256PerformanceTC())
    # myscript.add_test_case(TeraMarkPkeEcdh25519PerformanceTC())
    # myscript.add_test_case(TeraMarkCryptoPerformanceTC())
    # myscript.add_test_case(TeraMarkLookupEnginePerformanceTC())
    # myscript.add_test_case(FlowTestPerformanceTC())
    # myscript.add_test_case(TeraMarkZipPerformanceTC())
    # myscript.add_test_case(TeraMarkDfaPerformanceTC())
    # myscript.add_test_case(TeraMarkJpegPerformanceTC())
    # myscript.add_test_case(TeraMarkNuTransitPerformanceTC())
    # myscript.add_test_case(PkeX25519TlsSoakPerformanceTC())
    # myscript.add_test_case(PkeP256TlsSoakPerformanceTC())
    # myscript.add_test_case(SoakDmaMemcpyCohPerformanceTC())
    # myscript.add_test_case(SoakDmaMemcpyNonCohPerformanceTC())
    # myscript.add_test_case(SoakDmaMemsetPerformanceTC())
    # myscript.add_test_case(TeraMarkMultiClusterCryptoPerformanceTC())
    # myscript.add_test_case(F1FlowTestPerformanceTC())
    # myscript.add_test_case(TeraMarkNfaPerformanceTC())
    # myscript.add_test_case(TeraMarkJuniperNetworkingPerformanceTC())
    # myscript.add_test_case(TeraMarkRcnvmeReadPerformanceTC())
    # myscript.add_test_case(TeraMarkRcnvmeRandomReadPerformanceTC())
    # myscript.add_test_case(TeraMarkRcnvmeWritePerformanceTC())
    # myscript.add_test_case(TeraMarkRcnvmeRandomWritePerformanceTC())
    myscript.add_test_case(TeraMarkHuPerformanceTC())
    # myscript.add_test_case(PrepareDbTc())

    myscript.run()
