from scripts.system.palladium_performance_master import *

S1 = FunPlatform.S1

ALLOC_SPEED_TEST_TAG_S1 = "qa_alloc_speed_test_s1"

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
    model = "WuDispatchTestPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=1,
                              summary="Wu Dispatch Test performance on S1",
                              steps="Steps 1")

class WuSendSpeedTestPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "WuSendSpeedTestPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=2,
                              summary="Wu Send Speed Test performance on S1",
                              steps="Steps 1")

class FunMagentPerformanceTestS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "FunMagentPerformanceTest"
    platform = S1

    def describe(self):
        self.set_test_details(id=3,
                              summary="Fun Magent Performance Test on S1",
                              steps="Steps 1")

class WuStackSpeedTestPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "WuStackSpeedTestPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=4,
                              summary="Wu Send Speed Test performance on S1",
                              steps="Steps 1")

class SoakFunMallocPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "SoakFunMallocPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=5,
                              summary="Soak fun malloc Performance Test on S1",
                              steps="Steps 1")

class SoakClassicMallocPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "SoakClassicMallocPerformance"
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
    model = "AllocSpeedPerformance"
    platform = S1

    def describe(self):
        self.set_test_details(id=9,
                              summary="Alloc speed test on S1",
                              steps="Steps 1")

class WuLatencyUngatedPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "WuLatencyUngated"
    platform = S1

    def describe(self):
        self.set_test_details(id=10,
                              summary="Wu Latency Ungated Performance Test on S1",
                              steps="Steps 1")

class WuLatencyAllocStackPerformanceS1Tc(PalladiumPerformanceTc):
    tag = ALLOC_SPEED_TEST_TAG_S1
    model = "WuLatencyAllocStack"
    platform = S1

    def describe(self):
        self.set_test_details(id=11,
                              summary="Wu Latency Alloc Stack Test on S1",
                              steps="Steps 1")

class PrepareDbTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=100,
                              summary="Prepare Status Db on S1",
                              steps="Steps 1")

    def setup(self):
        pass

    def run(self):
        chart_names = [FunPlatform.S1, "All metrics"]
        prepare_status_db(chart_names=chart_names)
        TimeKeeper.set_time(name=LAST_ANALYTICS_DB_STATUS_UPDATE, time=get_current_time())

    def cleanup(self):
        pass


class S1EcPerformanceTc(PalladiumPerformanceTc):
    tag = TERAMARK_EC_S1
    model = "EcPerformance"
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=12,
                              summary="S1 EC performance teramark",
                              steps="Steps 1")


class S1TeraMarkJpegPerformanceTc(TeraMarkJpegPerformanceTc):
    tag = TERAMARK_JPEG_S1
    model = "TeraMarkZipDeflatePerformance"
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=13,
                              summary="S1 Jpeg performance teramark",
                              steps="Steps 1")


class S1TeraMarkZipPerformanceTc(TeraMarkZipPerformanceTc):
    tag = TERAMARK_ZIP_S1
    model = "TeraMarkJpegPerformance"
    platform = FunPlatform.S1

    def describe(self):
        self.set_test_details(id=14,
                              summary="S1 Zip performance teramark",
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
    # myscript.add_test_case(PrepareDbTc())
    myscript.add_test_case(S1EcPerformanceTc())
    myscript.add_test_case(S1TeraMarkJpegPerformanceTc())
    # myscript.add_test_case(S1TeraMarkZipPerformanceTc())


    myscript.run()
