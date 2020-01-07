from scripts.system.palladium_performance_master import *

S1 = FunPlatform.S1

ALLOC_SPEED_TEST_TAG_S1 = "qa_alloc_speed_test_s1"
NUCLEUS_SET_2_S1 = "qa_nucleus_set_2_s1"
NUCLEUS_SET_3_S1 = "qa_nucleus_set_3_s1"


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        self.lsf_status_server = LsfStatusServer()
        tags = [ALLOC_SPEED_TEST_TAG_S1]
        self.lsf_status_server.workaround(tags=tags)
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        invalidate_goodness_cache()

class WuDispatchTestPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "WuDispatchTestPerformance"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=1,
                              summary="Wu Dispatch Test performance on S1",
                              steps="Steps 1")

class WuSendSpeedTestPerformanceS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_2_S1
    model = "WuSendSpeedTestPerformance"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=2,
                              summary="Wu Send Speed Test performance on S1",
                              steps="Steps 1")

class FunMagentPerformanceTestS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_3_S1
    model = "FunMagentPerformanceTest"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=3,
                              summary="Fun Magent Performance Test on S1",
                              steps="Steps 1")

class WuStackSpeedTestPerformanceS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_2_S1
    model = "WuStackSpeedTestPerformance"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=4,
                              summary="Wu Send Speed Test performance on S1",
                              steps="Steps 1")

class SoakFunMallocPerformanceS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_3_S1
    model = "SoakFunMallocPerformance"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=5,
                              summary="Soak fun malloc Performance Test on S1",
                              steps="Steps 1")

class SoakClassicMallocPerformanceS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_3_S1
    model = "SoakClassicMallocPerformance"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=6,
                              summary="Soak classic malloc Performance Test on S1",
                              steps="Steps 1")

class BcopyFloodPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "BcopyFloodDmaPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=7,
                              summary="bcopy flood performance on S1",
                              steps="Steps 1")

class BcopyPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "BcopyPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=8,
                              summary="Bcopy performance",
                              steps="Steps 1")

class AllocSpeedPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "AllocSpeedPerformance"  # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=9,
                              summary="Alloc speed test on S1",
                              steps="Steps 1")

class WuLatencyUngatedPerformanceS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_2_S1
    model = "WuLatencyUngated"   # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=10,
                              summary="Wu Latency Ungated Performance Test on S1",
                              steps="Steps 1")

class WuLatencyAllocStackPerformanceS1Tc(PalladiumPerformanceTc):
    tag = NUCLEUS_SET_2_S1
    model = "WuLatencyAllocStack"   # Yes
    platform = S1

    def describe(self):
        self.set_test_details(id=11,
                              summary="Wu Latency Alloc Stack Test on S1",
                              steps="Steps 1")


class EcPerformanceS1Tc(PalladiumPerformanceTc):
    tag = TERAMARK_EC_S1
    model = "EcPerformance"
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=12,
                              summary="S1 EC performance teramark",
                              steps="Steps 1")


class TeraMarkJpegPerformanceS1Tc(TeraMarkJpegPerformanceTc):
    tag = TERAMARK_JPEG_S1
    model = "TeraMarkJpegPerformance"
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=13,
                              summary="S1 Jpeg performance teramark",
                              steps="Steps 1")


class TeraMarkZipDeflatePerformanceS1Tc(TeraMarkZipPerformanceTc):
    tag = TERAMARK_ZIP_DEFLATE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=14,
                              summary="S1 Zip defalte performance teramark",
                              steps="Steps 1")


class TeraMarkZipLzmaPerformanceS1Tc(TeraMarkZipPerformanceTc):
    tag = TERAMARK_ZIP_LZMA_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=15,
                              summary="S1 Zip lzma performance teramark",
                              steps="Steps 1")


class TeraMarkPkeRsaPerformanceS1Tc(TeraMarkPkeRsaPerformanceTc):
    tag = TERAMARK_PKE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=16,
                              summary="S1 teraMark PKE RSA Performance Test",
                              steps="Steps 1")


class TeraMarkPkeRsa4kPerformanceS1Tc(TeraMarkPkeRsa4kPerformanceTc):
    tag = TERAMARK_PKE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=17,
                              summary="S1 TeraMark PKE RSA 4K Performance Test",
                              steps="Steps 1")


class TeraMarkPkeEcdh256PerformanceS1Tc(TeraMarkPkeEcdh256PerformanceTc):
    tag = TERAMARK_PKE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=18,
                              summary="S1 TeraMark PKE ECDH P256 Performance Test",
                              steps="Steps 1")


class TeraMarkPkeEcdh25519PerformanceS1Tc(TeraMarkPkeEcdh25519PerformanceTc):
    tag = TERAMARK_PKE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=19,
                              summary="S1 TeraMark PKE ECDH 25519 Performance Test",
                              steps="Steps 1")


class PkeX25519TlsSoakPerformanceS1Tc(PkeX25519TlsSoakPerformanceTc):
    tag = TERAMARK_PKE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=20,
                              summary="S1 ECDHE_RSA X25519 RSA 2K TLS Soak Performance Test",
                              steps="Steps 1")


class PkeP256TlsSoakPerformanceS1Tc(PkeP256TlsSoakPerformanceTc):
    tag = TERAMARK_PKE_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=21,
                              summary="S1 ECDHE_RSA P256 RSA 2K TLS Soak Performance Test",
                              steps="Steps 1")


class TeraMarkDfaPerformanceS1Tc(TeraMarkDfaPerformanceTc):
    tag = TERAMARK_DFA_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=22,
                              summary="TeraMark DFA Performance Test on S1",
                              steps="Steps 1")


class TeraMarkNfaPerformanceS1Tc(TeraMarkNfaPerformanceTc):
    tag = TERAMARK_NFA_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=23,
                              summary="TeraMark NFA Performance Test on S1",
                              steps="Steps 1")


class TeraMarkMultiClusterCryptoPerformanceS1Tc(TeraMarkMultiClusterCryptoPerformanceTc):
    tag = TERAMARK_CRYPTO_RAW_S1
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=24,
                              summary="S1 TeraMark Multi Cluster Crypto Performance Test",
                              steps="Steps 1")

class SoakFlowsMemcpy1MbNonCohPerformanceS1Tc(SoakFlowsMemcpy1MbNonCohPerformanceTc):
    tag = SOAK_FLOWS_MEMCPY_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=25,
                              summary="S1 soak flows memcpy 1MB non coh performance",
                              steps="Steps 1")

class ChannelParallPerformanceS1Tc(ChannelParallPerformanceTc):
    tag = CHANNEL_PARALL_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=26,
                              summary="Channel parall Performance on S1",
                              steps="Steps 1")

class SoakFlowsBusyLoopPerformanceS1Tc(SoakFlowsBusyLoopPerformanceTc):
    tag = SOAK_FLOWS_BUSY_LOOP_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=27,
                              summary="soak flows busy loop 10 usecs performance on S1",
                              steps="Steps 1")

class SoakDmaMemcpyThresholdPerformanceS1Tc(SoakDmaMemcpyThresholdPerformanceTc):
    tag = SOAK_DMA_MEMCPY_THRESHOLD_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=28,
                              summary="Soak DMA memcpy vs VP memcpy threshold test on S1",
                              steps="Steps 1")

class SoakDmaMemcpyCohPerformanceS1Tc(SoakDmaMemcpyCohPerformanceTc):
    tag = SOAK_DMA_MEMCPY_COH_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=29,
                              summary="Soak DMA memcpy coherent Performance Test on S1",
                              steps="Steps 1")


class SoakDmaMemcpyNonCohPerformanceS1Tc(SoakDmaMemcpyNonCohPerformanceTc):
    tag = SOAK_DMA_MEMCPY_NON_COH_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=30,
                              summary="Soak DMA memcpy Non coherent Performance Test on S1",
                              steps="Steps 1")


class SoakDmaMemsetPerformanceS1Tc(SoakDmaMemsetPerformanceTc):
    tag = SOAK_DMA_MEMSET_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=31,
                              summary="Soak DMA memset Performance Test on S1",
                              steps="Steps 1")

class BootTimingPerformanceS1Tc(BootTimingPerformanceTc):
    tag = BOOT_TIMING_TEST_TAG_S1
    platform = S1

    def describe(self):
        self.set_test_details(id=32,
                              summary="Boot timing Performance Test on S1",
                              steps="Steps 1")


if __name__ == "__main__":
    myscript = MyScript()

    myscript.add_test_case(WuDispatchTestPerformanceS1Tc())
    myscript.add_test_case(WuSendSpeedTestPerformanceS1Tc())
    myscript.add_test_case(FunMagentPerformanceTestS1Tc())
    myscript.add_test_case(WuStackSpeedTestPerformanceS1Tc())
    myscript.add_test_case(SoakFunMallocPerformanceS1Tc())
    myscript.add_test_case(SoakClassicMallocPerformanceS1Tc())
    myscript.add_test_case(BcopyFloodPerformanceS1Tc())
    myscript.add_test_case(BcopyPerformanceS1Tc())
    myscript.add_test_case(AllocSpeedPerformanceS1Tc())
    myscript.add_test_case(WuLatencyUngatedPerformanceS1Tc())
    myscript.add_test_case(WuLatencyAllocStackPerformanceS1Tc())
    myscript.add_test_case(EcPerformanceS1Tc())
    myscript.add_test_case(TeraMarkJpegPerformanceS1Tc())
    myscript.add_test_case(TeraMarkZipDeflatePerformanceS1Tc())
    myscript.add_test_case(TeraMarkZipLzmaPerformanceS1Tc())
    myscript.add_test_case(TeraMarkPkeRsaPerformanceS1Tc())
    myscript.add_test_case(TeraMarkPkeRsa4kPerformanceS1Tc())
    myscript.add_test_case(TeraMarkPkeEcdh256PerformanceS1Tc())
    myscript.add_test_case(TeraMarkPkeEcdh25519PerformanceS1Tc())
    myscript.add_test_case(PkeX25519TlsSoakPerformanceS1Tc())
    myscript.add_test_case(PkeP256TlsSoakPerformanceS1Tc())
    myscript.add_test_case(TeraMarkDfaPerformanceS1Tc())
    myscript.add_test_case(TeraMarkNfaPerformanceS1Tc())
    myscript.add_test_case(TeraMarkMultiClusterCryptoPerformanceS1Tc())
    myscript.add_test_case(SoakFlowsMemcpy1MbNonCohPerformanceS1Tc())
    myscript.add_test_case(ChannelParallPerformanceS1Tc())
    myscript.add_test_case(SoakFlowsBusyLoopPerformanceS1Tc())
    myscript.add_test_case(SoakDmaMemcpyCohPerformanceS1Tc())

    myscript.add_test_case(SoakDmaMemcpyNonCohPerformanceS1Tc())

    myscript.add_test_case(SoakDmaMemsetPerformanceS1Tc())
    myscript.add_test_case(SoakDmaMemcpyThresholdPerformanceS1Tc())
    myscript.add_test_case(BootTimingPerformanceS1Tc())
    
    myscript.run()
