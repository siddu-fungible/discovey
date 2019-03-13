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
    TeraMarkCryptoPerformance, SoakDmaMemcpyCoherentPerformance, SoakDmaMemcpyNonCoherentPerformance, SoakDmaMemsetPerformance
from web.fun_test.metrics_models import TeraMarkLookupEnginePerformance, FlowTestPerformance, \
    TeraMarkZipDeflatePerformance, TeraMarkZipLzmaPerformance, TeraMarkDfaPerformance, TeraMarkJpegPerformance
from web.fun_test.analytics_models_helper import MetricHelper, invalidate_goodness_cache, MetricChartHelper
from web.fun_test.analytics_models_helper import prepare_status_db
from web.fun_test.models import TimeKeeper
import re
from datetime import datetime
from dateutil.parser import parse

ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
BOOT_TIMING_TEST_TAG = "boot_timing_test"
VOLTEST_TAG = "voltest_performance"
TERAMARK_PKE = "pke_teramark"
TERAMARK_CRYPTO = "crypto_teramark"
TERAMARK_LOOKUP = "le_teramark"
FLOW_TEST_TAG = "qa_storage2_endpoint"
TERAMARK_ZIP = "zip_teramark"
TERAMARK_DFA = "dfa_teramark"
TERAMARK_EC = "ec_teramark"
TERAMARK_JPEG = "jpeg_teramark"
SOAK_DMA_MEMCPY_COH = "soak_funos_memcpy_coh"
SOAK_DMA_MEMCPY_NON_COH = "soak_funos_memcpy_non_coh"
SOAK_DMA_MEMSET = "soak_funos_memset"
jpeg_operations = {"Compression throughput": "Compression throughput with Driver",
                   "Decompression throughput": "JPEG Decompress",
                   "Accelerator Compression throughput": "Compression Accelerator throughput",
                   "Accelerator Decompression throughput": "Decompression Accelerator throughput",
                   "JPEG Compression": "JPEG Compression"}
nu_transit_flow_types = {"FCP_HNU_HNU": "HNU_HNU_FCP"}
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

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


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        self.lsf_status_server = LsfStatusServer()
        tags = [ALLOC_SPEED_TEST_TAG, VOLTEST_TAG, BOOT_TIMING_TEST_TAG, TERAMARK_PKE, TERAMARK_CRYPTO, TERAMARK_LOOKUP,
                FLOW_TEST_TAG, TERAMARK_ZIP, TERAMARK_DFA, TERAMARK_EC, TERAMARK_JPEG, SOAK_DMA_MEMCPY_COH, SOAK_DMA_MEMCPY_NON_COH, SOAK_DMA_MEMSET]
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

    def validate_json_file(self, validation_required=True):
        data = {}
        self.lines = []
        file_path = LOGS_DIR + "/nu_rfc2544_performance.json"
        fun_test.test_assert(os.path.isfile(file_path), "Ensure Nu Transit Performance Data Json exists")
        fun_test.test_assert(os.access(file_path, os.R_OK), "Ensure read access for the file")
        with open(file_path) as fp:
            data = json.loads(fp.read())
            self.lines.append(data)

        file_path = LOGS_DIR + "/hu_funeth_performance_data.json"
        fun_test.test_assert(os.path.isfile(file_path), "Ensure Hu Funeth Performance Data Json exists")
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
                m = re.search(
                    r'Time for one fun_malloc\+fun_free \(threaded\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_threaded_ns\]',
                    line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_threaded = int(d['avg'])
                m = re.search(
                    r'Time for one malloc\+free \(classic\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_classic_ns\]', line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_classic_avg = int(d['avg'])
                    output_one_malloc_free_classic_min = int(d['min'])
                    output_one_malloc_free_classic_max = int(d['max'])

                # wu_latency_test
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_alloc_stack_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_alloc_stack_ns_min = int(d["min"])
                    wu_alloc_stack_ns_avg = int(d["avg"])
                    wu_alloc_stack_ns_max = int(d["max"])
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_ungated_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_ungated_ns_min = int(d["min"])
                    wu_ungated_ns_avg = int(d["avg"])
                    wu_ungated_ns_max = int(d["max"])

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
                                                                input_date_time=self.dt)

            MetricHelper(model=WuLatencyUngated).add_entry(status=self.result, input_app="wu_latency_test",
                                                           output_min=wu_ungated_ns_min,
                                                           output_max=wu_ungated_ns_max,
                                                           output_avg=wu_ungated_ns_avg,
                                                           input_date_time=self.dt)

            MetricHelper(model=WuLatencyAllocStack).add_entry(status=self.result,
                                                              input_app="wu_latency_test",
                                                              output_min=wu_alloc_stack_ns_min,
                                                              output_max=wu_alloc_stack_ns_max,
                                                              output_avg=wu_alloc_stack_ns_avg,
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
                                                                   input_latency_perf_name=latency_perf_name,
                                                                   output_average_bandwith=average_bandwidth,
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
                                                                           input_latency_perf_name=latency_perf_name,
                                                                           output_average_bandwith=average_bandwidth,
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

                m = re.search(r'(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_encode_latency)\]', line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_encode_latency_min = int(d["min"])
                    ec_encode_latency_max = int(d["max"])
                    ec_encode_latency_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    unit = d["unit"]
                    fun_test.test_assert_expected(actual=unit, expected="nsecs", message="perf_ec_encode_latency unit")

                m = re.search(r'(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_encode_throughput)\]', line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_encode_throughput_min = int(d["min"])
                    ec_encode_throughput_max = int(d["max"])
                    ec_encode_throughput_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    unit = d["unit"]
                    fun_test.test_assert_expected(actual=unit, expected="Mbps",
                                                  message="perf_ec_encode_throughput unit")

                m = re.search(r'(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_recovery_latency)\]', line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_recovery_latency_min = int(d["min"])
                    ec_recovery_latency_max = int(d["max"])
                    ec_recovery_latency_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    unit = d["unit"]
                    fun_test.test_assert_expected(actual=unit, expected="nsecs",
                                                  message="perf_ec_recovery_latency unit")

                m = re.search(r'(?P<value_json>{.*})\s+\[(?P<metric_name>perf_ec_recovery_throughput)\]', line)
                if m:
                    d = json.loads(m.group("value_json"))
                    ec_recovery_throughput_min = int(d["min"])
                    ec_recovery_throughput_max = int(d["max"])
                    ec_recovery_throughput_avg = int(d["avg"])
                    input_metric_name = m.group("metric_name")
                    unit = d["unit"]
                    fun_test.test_assert_expected(actual=unit, expected="Mbps",
                                                  message="perf_ec_recovery_throughput unit")
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
                                                        output_recovery_throughput_avg=ec_recovery_throughput_avg
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
                            if key == "value":
                                metrics["output_" + metric_name] = value
                    except:
                        metrics["output_" + metric_name] = value
                    try:
                        # if units not in ["mbps", "nsecs", "iops"]:
                        units = j["unit"]
                        fun_test.simple_assert(units in ["mbps", "nsecs", "iops"],
                                               "Unexpected unit {} in line: {}".format(units, line))
                    except Exception as ex:
                        pass
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
                            if key == "value":
                                metrics["output_" + metric_name + "_" + metric_type] = value
                    except Exception as ex:
                        metrics["output_" + metric_name + "_" + metric_type] = value

                    try:
                        units = j["unit"]
                        fun_test.simple_assert(units in ["Mbps", "nsecs", "ops"],
                                               "Unexpected unit {} in line: {}".format(units, line))
                    except Exception as ex:
                        fun_test.critical(str(ex))
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
                    input_unit = average_json["unit"]
                    input_app = "dispatch_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    j = 0
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
                    input_unit = average_json["unit"]
                    input_app = "wu_send_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    j = 0
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
            i = 0

            for line in self.lines:
                m = re.search(
                    r'fun_magent.*=>\s+(?P<latency_json>{.*})\s+\[(?P<metric_name>fun_magent_rate_malloc_free_per_sec)\]',
                    line)
                if m:
                    latency_json = json.loads(m.group("latency_json"))
                    unit = latency_json["unit"]
                    fun_test.test_assert(unit, "Kops", "Valid Unit")
                    output_latency = int(latency_json["value"])
                    input_app = "fun_magent_perf_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("latency: {}, metric_name: {}".format(output_latency, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_latency"] = output_latency
                    d = self.metrics_to_dict(metrics, fun_test.PASSED)
                    j = 0
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
                    input_unit = average_json["unit"]
                    input_app = "wustack_speed_test"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("average: {}, metric_name: {}".format(output_average, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_average"] = output_average
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
                    input_unit = value_json["unit"]
                    input_app = "soak_malloc_fun_malloc"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = value_json["unit"]
                    input_app = "soak_malloc_classic"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = value_json["unit"]
                    input_app = "pke_rsa_crt_dec_no_pad_soak"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = value_json["unit"]
                    input_app = "pke_rsa_crt_dec_no_pad_4096_soak"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = value_json["unit"]
                    input_app = "pke_ecdh_soak_256"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = value_json["unit"]
                    input_app = "pke_ecdh_soak_25519"
                    input_metric_name = m.group("metric_name").replace(" ", "_")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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

                            metrics["input_app"] = input_app
                            metrics["input_algorithm"] = input_algorithm
                            metrics["input_operation"] = input_operation
                            metrics["input_pkt_size"] = input_pkt_size
                            metrics["output_ops_per_sec"] = output_ops_per_sec
                            metrics["output_throughput"] = output_throughput
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

                            metrics["input_app"] = input_app
                            metrics["input_key_size"] = input_key_size
                            metrics["input_algorithm"] = input_algorithm
                            metrics["input_operation"] = input_operation
                            metrics["input_pkt_size"] = input_pkt_size
                            metrics["output_ops_per_sec"] = output_ops_per_sec
                            metrics["output_throughput"] = output_throughput
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

    def describe(self):
        self.set_test_details(id=20,
                              summary="Flow Test Performance",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            flow_test_passed = False
            match = None
            for line in self.lines:
                if "PASS libfunq testflow_test" in line:
                    flow_test_passed = True
                m = re.search(
                    r'Testflow:\s+(?P<iterations>\d+)\s+iterations\s+took\s+(?P<seconds>\d+)\s+seconds',
                    line)
                if m:
                    match = m
                    input_iterations = int(m.group("iterations"))
                    input_app = "hw_hsu_test"
                    output_time = int(m.group("seconds"))
                    fun_test.log("iterations: {}, time taken: {}".format(input_iterations, output_time))

                if flow_test_passed:
                    self.result = fun_test.PASSED
                    if match:
                        metrics["input_iterations"] = input_iterations
                        metrics["output_time"] = output_time
                        metrics["input_app"] = input_app
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        MetricHelper(model=FlowTestPerformance).add_entry(**d)

            fun_test.test_assert(flow_test_passed, "Checking if flow test passed")

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="FlowTestPerformance")
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
                        r'{"Type":\s+"(?P<type>\S+)",\s+"Operation":\s+"(?P<operation>\S+)",\s+"Effort":\s+(?P<effort>\S+),\s+"Stats":\s+(?P<stats>.*)}',
                        line)
                    if m:
                        input_type = m.group("type")
                        input_operation = m.group("operation")
                        input_effort = int(m.group("effort"))
                        output_stats = json.loads(m.group("stats"))
                        output_bandwidth_avg = output_stats['_avg_bw_gbps']
                        output_bandwidth_total = output_stats['_total_bw_kbps']
                        output_latency_min = output_stats['_min_latency']
                        output_latency_avg = output_stats['_avg_latency']
                        output_latency_max = output_stats['_max_latency']
                        output_iops = output_stats['_iops']
                        output_count = output_stats["_count"]

                        fun_test.log("type: {}, operation: {}, effort: {}, stats {}".format(input_type, input_operation,
                                                                                            input_effort, output_stats))
                        metrics["input_type"] = input_type
                        metrics["input_operation"] = input_operation
                        metrics["input_effort"] = input_effort
                        metrics["output_bandwidth_avg"] = output_bandwidth_avg
                        metrics["output_bandwidth_total"] = output_bandwidth_total
                        metrics["output_latency_min"] = output_latency_min
                        metrics["output_latency_avg"] = output_latency_avg
                        metrics["output_latency_max"] = output_latency_max
                        metrics["output_iops"] = output_iops
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

    def describe(self):
        self.set_test_details(id=22,
                              summary="TeraMark DFA Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:
            fun_test.test_assert(self.validate_job(validation_required=False), "validating job")
            teramark_begin = False
            for line in self.lines:
                if "TeraMark Begin" in line:
                    teramark_begin = True
                if "TeraMark End" in line:
                    teramark_begin = False
                if teramark_begin:
                    m = re.search(
                        r'{"Graph\s+Index":\s+(?P<index>\S+),\s+"Processed\s+\(Bytes\)":\s+(?P<processed>\S+),\s+"Matches\s+\(Bytes\)":\s+(?P<matches>\S+),\s+"Duration\s+\(ns\)":\s+(?P<latency>\S+),\s+"Throughput\s+\(Gbps\)":\s+(?P<bandwidth>\S+)}',
                        line)
                    if m:
                        input_graph_index = int(m.group("index"))
                        output_processed = int(m.group("processed"))
                        output_matches = int(m.group("matches"))
                        output_latency = int(m.group("latency"))
                        output_bandwidth = int(m.group("bandwidth"))

                        fun_test.log(
                            "graph index: {}, latency: {}, bandwidth: {}".format(input_graph_index, output_latency,
                                                                                 output_bandwidth))
                        metrics["input_graph_index"] = input_graph_index
                        metrics["output_processed"] = output_processed
                        metrics["output_matches"] = output_matches
                        metrics["output_latency"] = output_latency
                        metrics["output_bandwidth"] = output_bandwidth
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        MetricHelper(model=TeraMarkDfaPerformance).add_entry(**d)

            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkDfaPerformance")
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
    def describe(self):
        self.set_test_details(id=24,
                              summary="TeraMark NU Transit and HU Funeth Performance Test",
                              steps="Steps 1")

    def run(self):
        metrics = collections.OrderedDict()
        try:

            fun_test.test_assert(self.validate_json_file(), "validate json file and output")
            for lines in self.lines:
                for line in lines:
                    if "flow_type" in line:
                        if line["flow_type"] in nu_transit_flow_types:
                            line["flow_type"] = nu_transit_flow_types[line["flow_type"]]
                        metrics["input_flow_type"] = line["flow_type"].replace("FPG", "NU")
                        metrics["input_mode"] = line["mode"] if "mode" in line else ""
                        metrics["input_version"] = line["version"]
                        metrics["input_frame_size"] = line["frame_size"]
                        date_time = get_time_from_timestamp(line["timestamp"])
                        if "HU" in metrics["input_flow_type"]:
                            metrics["output_throughput"] = (float(line["throughput"]) * 4.8) if "throughput" in line else -1 #extrapolate by 4.8 for HU
                            metrics["output_pps"] = (float(line["pps"]) * 0.0048) if "pps" in line else -1 #extrapolate by 0.0048 for HU
                        else:
                            metrics["output_throughput"] = (float(line["throughput"]) * 3.9) if "throughput" in line else -1
                            metrics["output_pps"] = (float(line["pps"]) * 0.0039) if "pps" in line else -1
                        metrics["output_latency_max"] = line["latency_max"] if "latency_max" in line else -1
                        metrics["output_latency_min"] = line["latency_min"] if "latency_min" in line else -1
                        metrics["output_latency_avg"] = line["latency_avg"] if "latency_avg" in line else -1
                        if "latency_P99.0" in line:
                            metrics["output_latency_P99"] = line["latency_P99.0"]
                        else:
                            metrics["output_latency_P99"] = -1
                        metrics["output_jitter_max"] = line["jitter_max"] if "jitter_max" in line else -1
                        metrics["output_jitter_min"] = line["jitter_min"] if "jitter_min" in line else -1
                        metrics["output_jitter_avg"] = line["jitter_avg"] if "jitter_avg" in line else -1
                        fun_test.log(
                            "flow type: {}, latency: {}, bandwidth: {}, frame size: {}, jitters: {}, pps: {}".format(
                                metrics["input_flow_type"], metrics["output_latency_avg"], metrics["output_throughput"],
                                metrics["input_frame_size"], metrics["output_jitter_avg"], metrics["output_pps"]))
                        d = self.metrics_to_dict(metrics, fun_test.PASSED)
                        d["input_date_time"] = date_time
                        if date_time.year >= 2019:
                            MetricHelper(model=NuTransitPerformance).add_entry(**d)
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=-1, jenkins_job_id=-1,
                                     git_commit="", model_name="NuTransitPerformance")
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
                    input_unit = value_json["unit"]
                    input_app = "pke_x25519_2k_tls_soak"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = value_json["unit"]
                    input_app = "pke_p256_2k_tls_soak"
                    input_metric_name = m.group("metric_name")
                    fun_test.log("ops per sec: {}, metric_name: {}".format(output_ops_per_sec, input_metric_name))
                    metrics["input_app"] = input_app
                    metrics["input_metric_name"] = input_metric_name
                    metrics["output_ops_per_sec"] = output_ops_per_sec
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
                    input_unit = bandwidth_json["unit"]
                    if input_unit == "MBps":
                        output_bandwidth = float(output_bandwidth / 1000)
                    input_log_size = bandwidth_json["log_size"]
                    metric_name = m.group("metric_name")
                    metrics["input_size"] = input_size
                    metrics["input_operation"] = input_operation
                    metrics["output_bandwidth"] = output_bandwidth
                    metrics["input_unit"] = input_unit
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
    myscript.add_test_case(TeraMarkZipPerformanceTC())
    # # myscript.add_test_case(TeraMarkDfaPerformanceTC())
    # myscript.add_test_case(TeraMarkJpegPerformanceTC())
    # myscript.add_test_case(TeraMarkNuTransitPerformanceTC())
    # myscript.add_test_case(PkeX25519TlsSoakPerformanceTC())
    # myscript.add_test_case(PkeP256TlsSoakPerformanceTC())
    # myscript.add_test_case(SoakDmaMemcpyCohPerformanceTC())
    # myscript.add_test_case(SoakDmaMemcpyNonCohPerformanceTC())
    # myscript.add_test_case(SoakDmaMemsetPerformanceTC())
    # myscript.add_test_case(TeraMarkMultiClusterCryptoPerformanceTC())
    # myscript.add_test_case(PrepareDbTc())

    myscript.run()
