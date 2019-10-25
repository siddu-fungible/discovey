from lib.system.fun_test import *
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer
from fun_global import FunPlatform


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""

        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")
        self.lsf_status_server = LsfStatusServer()
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class PalladiumTc(FunTestCase):
    boot_args = ""
    tags = ""
    note = ""
    fun_os_make_flags = ""
    hw_model = "S1_Compute"
    max_duration = 900
    release_build = "true"
    hw_version = "rel_10082019"
    run_target = "protium_s"
    extra_emails = []

    def describe(self):
        self.set_test_details(id=0,
                              summary="",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        if not ("ranga.gowda@fungible.com" in self.extra_emails):
            self.extra_emails.append("ranga.gowda@fungible.com")
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Starting the jenkins build")
        jenkins_manager = JenkinsManager()
        params = {"BOOTARGS": self.boot_args,
                  "MAX_DURATION": self.max_duration,
                  "RUN_MODE": "Batch",
                  "TAGS": self.tags,
                  "NOTE": self.note,
                  "RELEASE_BUILD": self.release_build,
                  "FUNOS_MAKEFLAGS": self.fun_os_make_flags,
                  "HW_VERSION": self.hw_version,
                  "RUN_TARGET": self.run_target,
                  "HW_MODEL": self.hw_model}

        build_result = jenkins_manager.build(params=params, extra_emails=self.extra_emails)
        fun_test.test_assert(build_result, "Build completed normally")


class CryptoTeramarkTc(PalladiumTc):
    #boot_args = "app=crypto_test,crypto_tunnel_perf,crypto_api_perf,crypto_raw_speed --test-exit-fast --serial"
    boot_args = "app=crypto_test,crypto_raw_speed  nvps=24 vp_iters=5000 pcs_to_use=1 --test-exit-fast --serial"
    tags = "qa_s1_crypto_teramark"
    max_duration = 2700
    note = "Crypto SEC Regression & TeraMark apps (PC0 Throughput) on S1"
    fun_os_make_flags = "NDEBUG=1"
    extra_emails = ["jitendra.lulla@fungible.com"]

    def describe(self):
        self.set_test_details(id=1,
                              summary="Schedule crypto (SEC) s1 Feature Regression and TeraMark apps on Jenkins",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)


class PkeTeramarkTc(PalladiumTc):
    boot_args = "app=pke_rsa_crt_dec_no_pad_soak,pke_rsa_crt_dec_no_pad_4096_soak,pke_ecdh_soak_256,pke_ecdh_soak_25519,pke_x25519_2k_tls_soak,pke_p256_2k_tls_soak --serial"
    tags = "qa_s1_pke_teramark"
    hw_model = "S1_CUT"
    note = "PKE teramark app on S1"

    def describe(self):
        self.set_test_details(id=2,
                              summary="Schedule PKE teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class EcTeramarkTc(PalladiumTc):
    boot_args = "app=qa_ec_stress min_ndata=8 max_ndata=8 min_nparity=4 max_nparity=4 min_stridelen=4096 max_stridelen=4096 --seq_fail syslog=2 num_pcs=1 --noload --test-exit-fast"
    tags = "qa_s1_ec_teramark"
    note = "EC teramark app on S1"
    hw_model = "S1_Compute"
    max_duration = 1800

    def describe(self):
        self.set_test_details(id=3,
                              summary="Schedule EC teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class DfaTeramarkTc(PalladiumTc):
    boot_args = "app=dfa_perf_bootstrap rbm-size=1m dfa_perf.pc_mask=1 --bm-profile-regex dfa_perf.nflows=24 dfa_perf.niterations=100 syslog=2"
    tags = "qa_s1_dfa_teramark"
    note = "DFA teramark app on S1"
    fun_os_make_flags = "PM_TESTS=1"
    extra_emails = ["jitendra.lulla@fungible.com", "mahesh.kumar@fungible.com", " indrani.p@fungible.com"]

    def describe(self):
        self.set_test_details(id=4,
                              summary="Schedule DFA teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class NfaTeramarkTc(PalladiumTc):
    boot_args = "app=nfa_perf_bootstrap rbm-size=1m --bm-profile-regex nfa_perf.pc_mask=1 nfa_perf.nflows=140 nfa_perf.niterations=1024 syslog=2 nfa_perf.name=perf0"
    tags = "qa_s1_nfa_teramark"
    note = "NFA teramark app on S1"
    fun_os_make_flags = "PM_TESTS=1"
    extra_emails = ["jitendra.lulla@fungible.com", "mahesh.kumar@fungible.com", " indrani.p@fungible.com"]

    def describe(self):
        self.set_test_details(id=5,
                              summary="Schedule NFA teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class JpegTeramarkTc(PalladiumTc):
    boot_args = "app=jpeg_perf_test"
    tags = "qa_s1_jpeg_teramark"
    note = "JPEG teramark app on S1"
    fun_os_make_flags = "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/jpeg_perf_inputs/perf_input.list"
    extra_emails = ["jitendra.lulla@fungible.com", "abhishek.dikshit@fungible.com", "hara.bandhakavi@fungible.com"]

    def describe(self):
        self.set_test_details(id=6,
                              summary="Schedule JPEG teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class ZipDeflateTeramarkTc(PalladiumTc):
    boot_args = "app=deflate_perf_multi nflows=30 niterations=30 npcs=1 --platforms1"
    tags = "qa_s1_zip_deflate_teramark"
    note = "ZIP deflate teramark app on S1"
    fun_os_make_flags = "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/zip_inputs/compress_perf_input.list"
    max_duration = 9000
    extra_emails = ["jitendra.lulla@fungible.com"]

    def describe(self):
        self.set_test_details(id=7,
                              summary="Schedule Zip Deflate teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class ZipLzmaTeramarkTc(PalladiumTc):
    boot_args = "app=lzma_perf_multi nflows=30 niterations=10 npcs=1 --platforms1"
    tags = "qa_s1_zip_lzma_teramark"
    note = "ZIP lzma teramark app on S1"
    fun_os_make_flags = "XDATA_LISTS=/project/users/ashaikh/qa_test_inputs/zip_inputs/compress_perf_input.list"
    max_duration = 9000
    extra_emails = ["jitendra.lulla@fungible.com"]

    def describe(self):
        self.set_test_details(id=8,
                              summary="Schedule Zip Lzma teramark app on Jenkins",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


class CryptoCCPSanityTc(PalladiumTc):
    boot_args = "app=crypto_ccp_test"
    tags = "qa_s1_ccp_sanity"
    note = "Crypto ccp accelerator sanity test app"
    max_duration = 9000
    extra_emails = ["jitendra.lulla@fungible.com"]

    def describe(self):
        self.set_test_details(id=9,
                              summary="Schedule Crypto ccp sanity test app on S1",
                              steps="""
            1. Steps 1
            2. Steps 2
            3. Steps 3
                                  """)


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(CryptoTeramarkTc())
    # myscript.add_test_case(PkeTeramarkTc())
    myscript.add_test_case(EcTeramarkTc())
    myscript.add_test_case(DfaTeramarkTc())
    myscript.add_test_case(NfaTeramarkTc())
    myscript.add_test_case(JpegTeramarkTc())
    myscript.add_test_case(ZipDeflateTeramarkTc())
    myscript.add_test_case(ZipLzmaTeramarkTc())
    myscript.add_test_case(CryptoCCPSanityTc())
    myscript.run()
