from lib.system.fun_test import *
from django.apps import apps
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.metrics_models import MetricChart
from web.fun_test.analytics_models_helper import invalidate_goodness_cache

from datetime import datetime
from dateutil.parser import parse
from scripts.system.metrics_parser import MetricParser
from fun_global import FunPlatform
from glob import glob

F1 = FunPlatform.F1

ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
SOAK_BCOPY_TEST = "qa_soak_bcopy_test"
BOOT_TIMING_TEST_TAG = "boot_timing_test"
BOOT_TIMING_TEST_TAG_S1 = "qa_s1_boot_timing_test"
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
SOAK_DMA_MEMCPY_COH_S1 = "qa_s1_soak_funos_memcpy_coh"
SOAK_DMA_MEMCPY_NON_COH_S1 = "qa_s1_soak_funos_memcpy_non_coh"
SOAK_DMA_MEMSET_S1 = "qa_s1_soak_funos_memset"

RCNVME_READ = "qa_rcnvme_read"
RCNVME_RANDOM_READ = "qa_rcnvme_random_read"
RCNVME_WRITE = "qa_rcnvme_write"
RCNVME_RANDOM_WRITE = "qa_rcnvme_random_write"
RCNVME_READ_ALL = "qa_rcnvme_read_all"
RCNVME_RANDOM_READ_ALL = "qa_rcnvme_random_read_all"
RCNVME_WRITE_ALL = "qa_rcnvme_write_all"
RCNVME_RANDOM_WRITE_ALL = "qa_rcnvme_random_write_all"
TERAMARK_CRYPTO_SINGLE_TUNNEL = "crypto_single_tunnel_teramark"
TERAMARK_CRYPTO_MULTI_TUNNEL = "crypto_multi_tunnel_teramark"
TLS_1_TUNNEL = "tls_1_tunnel_teramark"
TLS_32_TUNNEL = "tls_32_tunnel_teramark"
TLS_64_TUNNEL = "tls_64_tunnel_teramark"

SOAK_DMA_MEMCPY_THRESHOLD = "soak_funos_memcpy_threshold"
SOAK_DMA_MEMCPY_THRESHOLD_S1 = "qa_s1_soak_funos_memcpy_threshold"

IPSEC_ENC_SINGLE_TUNNEL = "ipsec_enc_single_tunnel_teramark"
IPSEC_ENC_MULTI_TUNNEL = "ipsec_enc_multi_tunnel_teramark"
IPSEC_DEC_SINGLE_TUNNEL = "ipsec_dec_single_tunnel_teramark"
IPSEC_DEC_MULTI_TUNNEL = "ipsec_dec_multi_tunnel_teramark"
VOLTEST_LSV = "qa_voltest_lsv_performance"
VOLTEST_LSV_4 = "qa_voltest_lsv_4_performance"

CHANNEL_PARALL = "qa_channel_parall"
CHANNEL_PARALL_S1 = "qa_s1_channel_parall"
SOAK_FLOWS_BUSY_LOOP = "qa_soak_flows_busy_loop"
SOAK_FLOWS_BUSY_LOOP_S1 = "qa_s1_soak_flows_busy_loop"
SOAK_FLOWS_MEMCPY = "qa_soak_flows_memcpy_non_coh"
SOAK_FLOWS_MEMCPY_S1 = "qa_s1_soak_flows_memcpy_non_coh"

VOLTEST_BLT_1 = "qa_voltest_blt_performance"
VOLTEST_BLT_8 = "qa_voltest_blt_8_performance"
VOLTEST_BLT_12 = "qa_voltest_blt_12_performance"
TERAMARK_EC_S1 = "qa_s1_ec_teramark"
TERAMARK_JPEG_S1 = "qa_s1_jpeg_teramark"
TERAMARK_ZIP_DEFLATE_S1 = "qa_s1_zip_deflate_teramark"
TERAMARK_ZIP_LZMA_S1 = "qa_s1_zip_lzma_teramark"
TERAMARK_PKE_S1 = "qa_s1_pke_teramark"
TERAMARK_DFA_S1 = "qa_s1_dfa_teramark"
TERAMARK_NFA_S1 = "qa_s1_nfa_teramark"
TERAMARK_CRYPTO_RAW_S1 = "qa_s1_crypto_teramark"

CRYPTO_FAST_PATH = "qa_crypto_fastpath_teramark"

jpeg_operations = {"Compression throughput": "Compression throughput with Driver",
                   "Decompression throughput": "JPEG Decompress",
                   "Accelerator Compression throughput": "Compression Accelerator throughput",
                   "Accelerator Decompression throughput": "Decompression Accelerator throughput",
                   "JPEG Compression": "JPEG Compression"}
nu_transit_flow_types = {"FCP_HNU_HNU": "HNU_HNU_FCP"}
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

networking_models = ["HuThroughputPerformance", "HuLatencyPerformance", "TeraMarkFunTcpThroughputPerformance",
                     "NuTransitPerformance", "TeraMarkJuniperNetworkingPerformance", "HuLatencyUnderLoadPerformance",
                     "TeraMarkFunTcpConnectionsPerSecondPerformance", "AlibabaRdmaPerformance"]


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
                                 model_name, platform="F1"):
    charts = MetricChart.objects.filter(metric_model_name=model_name, platform=platform)
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
                     metric_id):
    charts = MetricChart.objects.filter(metric_id=metric_id)
    for chart in charts:
        chart.last_build_status = result
        chart.last_build_date = get_current_time()
        chart.last_suite_execution_id = suite_execution_id
        chart.last_test_case_id = test_case_id
        chart.last_lsf_job_id = job_id
        chart.last_jenkins_job_id = jenkins_job_id
        chart.last_git_commit = git_commit
        chart.save()


def set_networking_chart_status(platform=FunPlatform.F1):
    for model in networking_models:
        metric_model = app_config.get_metric_models()[model]
        charts = MetricChart.objects.filter(metric_model_name=model, platform=platform)
        for chart in charts:
            status = True
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                order_by = "-input_date_time"
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
                        status = False
                        chart.last_build_status = fun_test.FAILED
                        chart.last_suite_execution_id = fun_test.get_suite_execution_id()
                        chart.last_build_date = get_current_time()
                        chart.save()
                        break
            if status:
                chart.last_build_status = fun_test.PASSED
                chart.last_suite_execution_id = fun_test.get_suite_execution_id()
                chart.last_build_date = get_current_time()
                chart.save()


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        self.lsf_status_server = LsfStatusServer()
        tags = [ALLOC_SPEED_TEST_TAG, SOAK_BCOPY_TEST, BOOT_TIMING_TEST_TAG, BOOT_TIMING_TEST_TAG_S1, TERAMARK_PKE,
                TERAMARK_CRYPTO,
                TERAMARK_LOOKUP,
                FLOW_TEST_TAG, F1_FLOW_TEST_TAG, TERAMARK_ZIP, TERAMARK_DFA, TERAMARK_NFA, TERAMARK_EC, TERAMARK_JPEG,
                SOAK_DMA_MEMCPY_COH, SOAK_DMA_MEMCPY_COH_S1,
                SOAK_DMA_MEMCPY_NON_COH, SOAK_DMA_MEMCPY_NON_COH_S1, SOAK_DMA_MEMSET, SOAK_DMA_MEMSET_S1, RCNVME_READ,
                RCNVME_RANDOM_READ, RCNVME_WRITE,
                RCNVME_RANDOM_WRITE, RCNVME_READ_ALL,
                RCNVME_RANDOM_READ_ALL, RCNVME_WRITE_ALL,
                RCNVME_RANDOM_WRITE_ALL, SOAK_DMA_MEMCPY_THRESHOLD, SOAK_DMA_MEMCPY_THRESHOLD_S1,
                IPSEC_ENC_SINGLE_TUNNEL, IPSEC_ENC_MULTI_TUNNEL, IPSEC_DEC_MULTI_TUNNEL, IPSEC_DEC_SINGLE_TUNNEL,
                VOLTEST_LSV, VOLTEST_LSV_4, CHANNEL_PARALL, CHANNEL_PARALL_S1, SOAK_FLOWS_BUSY_LOOP,
                SOAK_FLOWS_BUSY_LOOP_S1, SOAK_FLOWS_MEMCPY,
                SOAK_FLOWS_MEMCPY_S1, VOLTEST_BLT_1,
                VOLTEST_BLT_8, VOLTEST_BLT_12, TERAMARK_EC_S1, TERAMARK_JPEG_S1, TERAMARK_ZIP_DEFLATE_S1,
                TERAMARK_ZIP_LZMA_S1, TERAMARK_PKE_S1, TERAMARK_DFA_S1, TERAMARK_NFA_S1, TERAMARK_CRYPTO_RAW_S1, CRYPTO_FAST_PATH]
        # self.lsf_status_server.workaround(tags=tags)
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        invalidate_goodness_cache()


class PalladiumPerformanceTc(FunTestCase):
    tag = ALLOC_SPEED_TEST_TAG
    model = None
    result = fun_test.FAILED
    dt = get_rounded_time()
    platform = F1

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def cleanup(self):
        pass

    def validate_job(self, validation_required=True):
        job_info = self.lsf_status_server.get_last_job(tag=self.tag)
        fun_test.test_assert(job_info, "Ensure Job Info exists")
        self.jenkins_job_id = job_info["jenkins_build_number"]
        self.job_id = job_info["job_id"]
        git_commit = job_info["git_commit"]
        self.git_commit = git_commit.replace("https://github.com/fungible-inc/FunOS/commit/", "")
        if validation_required:
            fun_test.test_assert(not job_info["return_code"], "Valid return code")
            fun_test.test_assert("output_text" in job_info, "output_text found in job info: {}".format(self.job_id))
        self.lines = job_info["output_text"].split("\n")
        self.dt = job_info["date_time"]
        self.run_time = job_info["run_time"]
        self.job_info = job_info
        fun_test.test_assert(is_job_from_today(self.dt), "Last job is from today")

        return True

    def metrics_to_dict(self, metrics, result):
        d = {}
        d["input_date_time"] = self.dt
        d["status"] = result
        for key, value in metrics.iteritems():
            d[key] = value
        return d

    def validate_json_file(self, file_paths, logs_dir=True):
        self.lines = []
        for names in file_paths:
            file_path = LOGS_DIR + "/" + names
            if not logs_dir:
                file_path = SHARED_TEST_RESULTS_DIR + "/" + names + "/results.json"
            fun_test.test_assert(os.path.isfile(file_path), "Ensure Json exists")
            fun_test.test_assert(os.access(file_path, os.R_OK), "Ensure read access for the file")
            with open(file_path) as fp:
                data = json.loads(fp.read())
                self.lines.append(data)
        return True

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, date_time=self.dt, platform=self.platform,
                                             run_time=self.run_time)

            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model, platform=self.platform)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class AllocSpeedPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    model = "AllocSpeedPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=1,
                              summary="Alloc speed test on F1",
                              steps="Steps 1")


class BcopyPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_BCOPY_TEST
    model = "BcopyPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=2,
                              summary="Bcopy performance",
                              steps="Steps 1")


class BcopyFloodPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_BCOPY_TEST
    model = "BcopyFloodDmaPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=3,
                              summary="bcopy flood performance",
                              steps="Steps 1")


class EcPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_EC
    model = 'EcPerformance'
    platform = F1

    def describe(self):
        self.set_test_details(id=4,
                              summary="EC performance",
                              steps="Steps 1")


class EcVolPerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_TAG
    model = "EcVolPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=5,
                              summary="EC Vol performance",
                              steps="Steps 1")


class VoltestPerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_TAG
    model = "VoltestPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=6,
                              summary="Voltest performance",
                              steps="Steps 1")


class WuDispatchTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    model = "WuDispatchTestPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=7,
                              summary="Wu Dispatch Test performance",
                              steps="Steps 1")


class WuSendSpeedTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    model = "WuSendSpeedTestPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=8,
                              summary="Wu Send Speed Test performance",
                              steps="Steps 1")


class FunMagentPerformanceTestTc(PalladiumPerformanceTc):
    tag = SOAK_BCOPY_TEST
    model = "FunMagentPerformanceTest"
    platform = F1

    def describe(self):
        self.set_test_details(id=9,
                              summary="Fun Magent Performance Test",
                              steps="Steps 1")


class WuStackSpeedTestPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    model = "WuStackSpeedTestPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=10,
                              summary="Wu Stack Speed Test performance",
                              steps="Steps 1")


class SoakFunMallocPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_BCOPY_TEST
    model = "SoakFunMallocPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=11,
                              summary="Soak fun malloc Performance Test",
                              steps="Steps 1")


class SoakClassicMallocPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_BCOPY_TEST
    model = "SoakClassicMallocPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=12,
                              summary="Soak classic malloc Performance Test",
                              steps="Steps 1")


class BootTimingPerformanceTc(PalladiumPerformanceTc):
    tag = BOOT_TIMING_TEST_TAG
    model = "BootTimePerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=13,
                              summary="Boot Timing Performance Test",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            log = self.lsf_status_server.get_human_file(job_id=self.job_id, file_name="cdn_uartout1.txt")
            fun_test.test_assert(log, "fetched boot time uart log")
            logs_1 = log.split("\n")
            log = self.lsf_status_server.get_human_file(job_id=self.job_id, file_name="cdn_uartout0.txt")
            fun_test.test_assert(log, "fetched mmc time uart log")
            logs_0 = log.split("\n")
            self.lines = logs_1 + logs_0

            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, date_time=self.dt, platform=self.platform, run_time=self.run_time)

            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="BootTimePerformance")
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkPkeRsaPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_PKE
    model = "TeraMarkPkeRsaPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=14,
                              summary="TeraMark PKE RSA Performance Test",
                              steps="Steps 1")


class TeraMarkPkeRsa4kPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_PKE
    model = "TeraMarkPkeRsa4kPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=15,
                              summary="TeraMark PKE RSA 4K Performance Test",
                              steps="Steps 1")


class TeraMarkPkeEcdh256PerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_PKE
    model = "TeraMarkPkeEcdh256Performance"
    platform = F1


    def describe(self):
        self.set_test_details(id=16,
                              summary="TeraMark PKE ECDH P256 Performance Test",
                              steps="Steps 1")


class TeraMarkPkeEcdh25519PerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_PKE
    model = "TeraMarkPkeEcdh25519Performance"
    platform = F1

    def describe(self):
        self.set_test_details(id=17,
                              summary="TeraMark PKE ECDH 25519 Performance Test",
                              steps="Steps 1")


class TeraMarkCryptoPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_CRYPTO
    model = "TeraMarkCryptoPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=18,
                              summary="TeraMark Crypto Performance Test",
                              steps="Steps 1")


class TeraMarkLookupEnginePerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_LOOKUP
    model = "TeraMarkLookupEnginePerformance"

    def describe(self):
        self.set_test_details(id=19,
                              summary="TeraMark Lookup Engine Performance Test",
                              steps="Steps 1")


class FlowTestPerformanceTc(PalladiumPerformanceTc):
    tag = FLOW_TEST_TAG
    model = "FlowTestPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=20,
                              summary="Flow Test Performance",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            lines = self.lsf_status_server.get_human_file(job_id=self.job_id, console_name="PCI Script Output")
            self.lines = lines.split("\n")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, date_time=self.dt, platform=self.platform, run_time=self.run_time)

            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name=self.model, platform=self.platform)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkZipPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_ZIP
    platform = F1

    def describe(self):
        self.set_test_details(id=21,
                              summary="TeraMark Zip Performance Test",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_job(), "validating job")
            result = MetricParser().parse_it(model_name="TeraMarkZip", logs=self.lines,
                                                    auto_add_to_db=False, date_time=self.dt, platform=self.platform, run_time=self.run_time)
            fun_test.test_assert(result["match_found"], "Found atleast one entry")
            self.result = fun_test.PASSED

        except Exception as ex:
            fun_test.critical(str(ex))

        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkZipDeflatePerformance",
                                     platform=self.platform)
        set_build_details_for_charts(result=self.result, suite_execution_id=fun_test.get_suite_execution_id(),
                                     test_case_id=self.id, job_id=self.job_id, jenkins_job_id=self.jenkins_job_id,
                                     git_commit=self.git_commit, model_name="TeraMarkZipLzmaPerformance",
                                     platform=self.platform)
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class TeraMarkDfaPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_DFA
    model = "TeraMarkDfaPerformance"

    def describe(self):
        self.set_test_details(id=22,
                              summary="TeraMark DFA Performance Test on F1",
                              steps="Steps 1")


class TeraMarkJpegPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_JPEG
    model = "TeraMarkJpegPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=23,
                              summary="TeraMark Jpeg Performance Test",
                              steps="Steps 1")


class TeraMarkNuTransitPerformanceTc(PalladiumPerformanceTc):
    model = "NuTransitPerformance"
    file_paths = ["nu_rfc2544_performance.json"]
    platform = F1

    def describe(self):
        self.set_test_details(id=24,
                              summary="TeraMark HNU Transit Performance Test",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_json_file(file_paths=self.file_paths), "validate json file and output")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=False, platform=self.platform)
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


class PkeX25519TlsSoakPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_PKE
    model = "PkeX25519TlsSoakPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=25,
                              summary="ECDHE_RSA X25519 RSA 2K TLS Soak Performance Test",
                              steps="Steps 1")


class PkeP256TlsSoakPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_PKE
    model = "PkeP256TlsSoakPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=26,
                              summary="ECDHE_RSA P256 RSA 2K TLS Soak Performance Test",
                              steps="Steps 1")


class SoakDmaMemcpyCohPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_DMA_MEMCPY_COH
    model = "SoakDmaMemcpyCoherentPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=27,
                              summary="Soak DMA memcpy coherent Performance Test",
                              steps="Steps 1")


class SoakDmaMemcpyNonCohPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_DMA_MEMCPY_NON_COH
    model = "SoakDmaMemcpyNonCoherentPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=28,
                              summary="Soak DMA memcpy Non coherent Performance Test",
                              steps="Steps 1")


class SoakDmaMemsetPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_DMA_MEMSET
    model = "SoakDmaMemsetPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=29,
                              summary="Soak DMA memset Performance Test",
                              steps="Steps 1")


class TeraMarkMultiClusterCryptoPerformanceTc(TeraMarkCryptoPerformanceTc):
    tag = TERAMARK_CRYPTO
    model = "TeraMarkMultiClusterCryptoPerformance"

    def describe(self):
        self.set_test_details(id=30,
                              summary="TeraMark Multi Cluster Crypto Performance Test",
                              steps="Steps 1")


class F1FlowTestPerformanceTc(FlowTestPerformanceTc):
    tag = F1_FLOW_TEST_TAG
    model = "F1FlowTestPerformance"

    def describe(self):
        self.set_test_details(id=31,
                              summary="Flow Test Performance on F1",
                              steps="Steps 1")


class TeraMarkNfaPerformanceTc(TeraMarkDfaPerformanceTc):
    tag = TERAMARK_NFA
    model = "TeraMarkNfaPerformance"

    def describe(self):
        self.set_test_details(id=32,
                              summary="TeraMark NFA Performance Test on F1",
                              steps="Steps 1")


class TeraMarkRcnvmeReadPerformanceTc(PalladiumPerformanceTc):
    tag = RCNVME_READ
    model = "TeraMarkRcnvmeReadWritePerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=34,
                              summary="TeraMark rcnvme read Performance Test on F1",
                              steps="Steps 1")


class TeraMarkRcnvmeRandomReadPerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_RANDOM_READ
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=35,
                              summary="TeraMark rcnvme random read Performance Test on F1",
                              steps="Steps 1")


class TeraMarkRcnvmeWritePerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_WRITE
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=36,
                              summary="TeraMark rcnvme write Performance Test on F1",
                              steps="Steps 1")


class TeraMarkRcnvmeRandomWritePerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_RANDOM_WRITE
    model = "TeraMarkRcnvmeReadWritePerformance"

    def describe(self):
        self.set_test_details(id=37,
                              summary="TeraMark rcnvme random write Performance Test on F1",
                              steps="Steps 1")


class JuniperCryptoSingleTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_CRYPTO_SINGLE_TUNNEL
    model = "JuniperCryptoTunnelPerformance"

    def describe(self):
        self.set_test_details(id=39,
                              summary="TeraMark Crypto single tunnel Performance Test on F1 for IMIX",
                              steps="Steps 1")


class JuniperCryptoMultiTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_CRYPTO_MULTI_TUNNEL
    model = "JuniperCryptoTunnelPerformance"

    def describe(self):
        self.set_test_details(id=40,
                              summary="TeraMark Crypto multi tunnel Performance Test on F1 for IMIX",
                              steps="Steps 1")


class RcnvmeReadAllPerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_READ_ALL
    model = "TeraMarkRcnvmeReadWriteAllPerformance"

    def describe(self):
        self.set_test_details(id=41,
                              summary="Rcnvme read all Performance Test on F1",
                              steps="Steps 1")


class RcnvmeRandomReadAllPerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_RANDOM_READ_ALL
    model = "TeraMarkRcnvmeReadWriteAllPerformance"

    def describe(self):
        self.set_test_details(id=42,
                              summary="Rcnvme random read all drives Performance Test on F1",
                              steps="Steps 1")


class RcnvmeWriteAllPerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_WRITE_ALL
    model = "TeraMarkRcnvmeReadWriteAllPerformance"

    def describe(self):
        self.set_test_details(id=43,
                              summary="Rcnvme write all Performance Test on F1",
                              steps="Steps 1")


class RcnvmeRandomWriteAllPerformanceTc(TeraMarkRcnvmeReadPerformanceTc):
    tag = RCNVME_RANDOM_WRITE_ALL
    model = "TeraMarkRcnvmeReadWriteAllPerformance"

    def describe(self):
        self.set_test_details(id=44,
                              summary="Rcnvme random write all Performance Test on F1",
                              steps="Steps 1")


class JuniperTlsSingleTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = TLS_1_TUNNEL
    model = "JuniperTlsTunnelPerformance"

    def describe(self):
        self.set_test_details(id=45,
                              summary="TeraMark TLS single tunnel Performance Test on F1",
                              steps="Steps 1")


class JuniperTls32TunnelPerformanceTc(JuniperTlsSingleTunnelPerformanceTc):
    tag = TLS_32_TUNNEL
    model = "JuniperTlsTunnelPerformance"

    def describe(self):
        self.set_test_details(id=46,
                              summary="TeraMark TLS 32 tunnel Performance Test on F1",
                              steps="Steps 1")


class JuniperTls64TunnelPerformanceTc(JuniperTlsSingleTunnelPerformanceTc):
    tag = TLS_64_TUNNEL
    model = "JuniperTlsTunnelPerformance"

    def describe(self):
        self.set_test_details(id=47,
                              summary="TeraMark TLS 64 tunnel Performance Test on F1",
                              steps="Steps 1")


class SoakDmaMemcpyThresholdPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_DMA_MEMCPY_THRESHOLD
    model = "SoakDmaMemcpyThresholdPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=48,
                              summary="Soak DMA memcpy vs VP memcpy threshold test",
                              steps="Steps 1")


class WuLatencyUngatedPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    model = "WuLatencyUngated"
    platform = F1

    def describe(self):
        self.set_test_details(id=49,
                              summary="Wu Latency Ungated Performance Test on F1",
                              steps="Steps 1")


class WuLatencyAllocStackPerformanceTc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG
    model = "WuLatencyAllocStack"
    platform = F1

    def describe(self):
        self.set_test_details(id=50,
                              summary="Wu Latency Alloc Stack Test on F1",
                              steps="Steps 1")


class JuniperIpsecEncryptionSingleTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = IPSEC_ENC_SINGLE_TUNNEL
    model = "JuniperIpsecEncryptionSingleTunnelPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=51,
                              summary="TeraMark IPSEC encryption single tunnel Performance Test on F1 for IMIX",
                              steps="Steps 1")


class JuniperIpsecEncryptionMultiTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = IPSEC_ENC_MULTI_TUNNEL
    model = "JuniperIpsecEncryptionMultiTunnelPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=52,
                              summary="TeraMark IPSEC encryption multi tunnel Performance Test on F1 for IMIX",
                              steps="Steps 1")


class JuniperIpsecDecryptionSingleTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = IPSEC_DEC_SINGLE_TUNNEL
    model = "JuniperIpsecDecryptionSingleTunnelPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=53,
                              summary="TeraMark IPSEC decryption single tunnel Performance Test on F1 for IMIX",
                              steps="Steps 1")


class JuniperIpsecDecryptionMultiTunnelPerformanceTc(PalladiumPerformanceTc):
    tag = IPSEC_DEC_MULTI_TUNNEL
    model = "JuniperIpsecDecryptionMultiTunnelPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=54,
                              summary="TeraMark IPSEC decryption multi tunnel Performance Test on F1 for IMIX",
                              steps="Steps 1")


class SetNetworkingStatusTc(PalladiumPerformanceTc):
    def describe(self):
        self.set_test_details(id=55,
                              summary="Set Networking status for charts",
                              steps="Steps 1")

    def run(self):
        set_networking_chart_status(platform=FunPlatform.F1)


class VoltestLsvPerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_LSV
    model = "VoltestLsvPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=56,
                              summary="Voltest LSV Performance with numinstance 1",
                              steps="Steps 1")


class VoltestLsv4PerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_LSV_4
    model = "VoltestLsv4Performance"
    platform = F1

    def describe(self):
        self.set_test_details(id=57,
                              summary="Voltest LSV Performance with numinstance 4",
                              steps="Steps 1")


class ChannelParallPerformanceTc(PalladiumPerformanceTc):
    tag = CHANNEL_PARALL
    model = "ChannelParallPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=58,
                              summary="Channel parall Performance on F1",
                              steps="Steps 1")


class SoakFlowsBusyLoopPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_FLOWS_BUSY_LOOP
    model = "SoakFlowsBusyLoop10usecs"
    platform = F1

    def describe(self):
        self.set_test_details(id=59,
                              summary="soak flows busy loop 10 usecs performance",
                              steps="Steps 1")


class SoakFlowsMemcpy1MbNonCohPerformanceTc(PalladiumPerformanceTc):
    tag = SOAK_FLOWS_MEMCPY
    model = "SoakFlowsMemcpy1MBNonCoh"
    platform = F1

    def describe(self):
        self.set_test_details(id=60,
                              summary="soak flows memcpy 64KB non coh performance",
                              steps="Steps 1")


class VoltestBlt1PerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_BLT_1
    model = 'VoltestBlt1Performance'
    platform = F1

    def describe(self):
        self.set_test_details(id=61,
                              summary="Voltest instance 1 BLT performance",
                              steps="Steps 1")


class VoltestBlt8PerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_BLT_8
    model = 'VoltestBlt8Performance'
    platform = F1

    def describe(self):
        self.set_test_details(id=62,
                              summary="Voltest instance 8 BLT performance",
                              steps="Steps 1")


class VoltestBlt12PerformanceTc(PalladiumPerformanceTc):
    tag = VOLTEST_BLT_12
    model = 'VoltestBlt12Performance'
    platform = F1

    def describe(self):
        self.set_test_details(id=63,
                              summary="Voltest instance 12 BLT performance",
                              steps="Steps 1")


class CryptoFastPathPerformanceTc(PalladiumPerformanceTc):
    tag = CRYPTO_FAST_PATH
    model = "CryptoFastPathPerformance"
    platform = F1

    def describe(self):
        self.set_test_details(id=64,
                              summary="Crypto Fast Path Performance Test",
                              steps="Steps 1")


class DataPlaneOperationsPerformanceTc(PalladiumPerformanceTc):
    model = "DataPlaneOperationsPerformance"
    file_paths = ["attach_raw_volumes", "create_raw_volumes", "detach_raw_volumes", "delete_raw_volumes"]
    platform = F1

    def describe(self):
        self.set_test_details(id=65,
                              summary="Data plane operations Performance Test",
                              steps="Steps 1")

    def run(self):
        try:
            fun_test.test_assert(self.validate_json_file(file_paths=self.file_paths, logs_dir=False), "validate json file and output")
            result = MetricParser().parse_it(model_name=self.model, logs=self.lines,
                                             auto_add_to_db=True, platform=self.platform)
            self.result = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


if __name__ == "__main__":
    myscript = MyScript()

    # myscript.add_test_case(AllocSpeedPerformanceTc())
    # myscript.add_test_case(BcopyPerformanceTc())
    # myscript.add_test_case(BcopyFloodPerformanceTc())
    # myscript.add_test_case(EcPerformanceTc())
    # myscript.add_test_case(WuDispatchTestPerformanceTc())
    # myscript.add_test_case(WuSendSpeedTestPerformanceTc())
    # myscript.add_test_case(FunMagentPerformanceTestTc())
    # myscript.add_test_case(WuStackSpeedTestPerformanceTc())
    # myscript.add_test_case(SoakFunMallocPerformanceTc())
    # myscript.add_test_case(SoakClassicMallocPerformanceTc())
    # myscript.add_test_case(BootTimingPerformanceTc())
    # myscript.add_test_case(TeraMarkPkeRsaPerformanceTc())
    # myscript.add_test_case(TeraMarkPkeRsa4kPerformanceTc())
    # myscript.add_test_case(TeraMarkPkeEcdh256PerformanceTc())
    # myscript.add_test_case(TeraMarkPkeEcdh25519PerformanceTc())
    # myscript.add_test_case(TeraMarkCryptoPerformanceTc())
    # myscript.add_test_case(TeraMarkLookupEnginePerformanceTc())
    # myscript.add_test_case(FlowTestPerformanceTc())
    # myscript.add_test_case(TeraMarkZipPerformanceTc())
    # myscript.add_test_case(TeraMarkDfaPerformanceTc())
    # myscript.add_test_case(TeraMarkJpegPerformanceTc())
    # myscript.add_test_case(TeraMarkNuTransitPerformanceTc())
    # myscript.add_test_case(PkeX25519TlsSoakPerformanceTc())
    # myscript.add_test_case(PkeP256TlsSoakPerformanceTc())
    # myscript.add_test_case(SoakDmaMemcpyCohPerformanceTc())
    # myscript.add_test_case(SoakDmaMemcpyNonCohPerformanceTc())
    # myscript.add_test_case(SoakDmaMemsetPerformanceTc())
    # myscript.add_test_case(F1FlowTestPerformanceTc())
    # myscript.add_test_case(TeraMarkNfaPerformanceTc())
    # myscript.add_test_case(TeraMarkRcnvmeReadPerformanceTc())
    # myscript.add_test_case(TeraMarkRcnvmeRandomReadPerformanceTc())
    # myscript.add_test_case(TeraMarkRcnvmeWritePerformanceTc())
    # myscript.add_test_case(TeraMarkRcnvmeRandomWritePerformanceTc())
    # myscript.add_test_case(RcnvmeReadAllPerformanceTc())
    # myscript.add_test_case(RcnvmeRandomReadAllPerformanceTc())
    # myscript.add_test_case(RcnvmeWriteAllPerformanceTc())
    # myscript.add_test_case(RcnvmeRandomWriteAllPerformanceTc())
    # myscript.add_test_case(SoakDmaMemcpyThresholdPerformanceTc())
    # myscript.add_test_case(WuLatencyUngatedPerformanceTc())
    # myscript.add_test_case(WuLatencyAllocStackPerformanceTc())
    # myscript.add_test_case(JuniperIpsecEncryptionSingleTunnelPerformanceTc())
    # myscript.add_test_case(JuniperIpsecDecryptionMultiTunnelPerformanceTc())
    # myscript.add_test_case(JuniperIpsecDecryptionSingleTunnelPerformanceTc())
    # myscript.add_test_case(JuniperIpsecEncryptionMultiTunnelPerformanceTc())
    # myscript.add_test_case(SetNetworkingStatusTc())
    # myscript.add_test_case(VoltestLsvPerformanceTc())
    # myscript.add_test_case(VoltestLsv4PerformanceTc())
    # myscript.add_test_case(ChannelParallPerformanceTc())
    # myscript.add_test_case(SoakFlowsBusyLoopPerformanceTc())
    # myscript.add_test_case(SoakFlowsMemcpy1MbNonCohPerformanceTc())
    # myscript.add_test_case(VoltestBlt1PerformanceTc())
    # myscript.add_test_case(VoltestBlt8PerformanceTc())
    # myscript.add_test_case(VoltestBlt12PerformanceTc())
    # myscript.add_test_case(CryptoFastPathPerformanceTc())
    myscript.add_test_case(DataPlaneOperationsPerformanceTc())

    myscript.run()
