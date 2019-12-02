from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient


try:
    job_environment = fun_test.get_job_environment()
    DPC_PROXY_IP = str(job_environment['UART_HOST'])
    DPC_PROXY_PORT = int(job_environment['UART_TCP_PORT_0'])
    emulation_target = str(job_environment['EMULATION_TARGET']).lower()
except (KeyError, ValueError):
    #DPC_PROXY_IP = '10.1.40.24'
    #DPC_PROXY_PORT = 42221
    # DPC_PROXY_IP = '10.1.20.129'
    # DPC_PROXY_PORT = 42220
    pass


class AppRun(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Bring up FS1600
        2. Execute run crypto_raw_speed
        3. Execute run qa_ec_stress
        4. Execute run soak_jpg_zip
        5. Execute run le_perf
        6. Async run crypto_raw_speed
        7. Async run qa_ec_stress
        8. Async run soak_jpg_zip
        9. Async run le_perf
        10. Async run crypto_raw_speed, qa_ec_stress, soak_jpg_zip, and le_perf together
        """)

    def setup(self):
        # Fun on demand will bring up FS1600, so no need to do it in script

        dpcsh_client_obj = DpcshClient(target_ip=DPC_PROXY_IP, target_port=DPC_PROXY_PORT)
        fun_test.shared_variables['dpcsh_client_obj'] = dpcsh_client_obj

    def cleanup(self):
        pass


class RunAppBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        pass

    def _run(self, app, arg=None, run='execute'):
        dpcsh_client_obj = fun_test.shared_variables['dpcsh_client_obj']
        if arg:
            cmd = '{} {} {}'.format(run, app, arg)
        else:
            cmd = '{} {}'.format(run, app)
        result = dpcsh_client_obj.command(cmd, legacy=True)
        fun_test.test_assert(result['status'], '{}'.format(cmd))


class ExecuteCrypto(RunAppBase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Execute run crypto_raw_speed",
                              steps="""
        1. Execute run crypto_raw_speed
        """)

    def run(self):
        RunAppBase._run(self, app='crypto_raw_speed', arg='{src:bm, dst:hbm, vp_iters:5000, cr_test_mute:True}')


class ExecuteEc(RunAppBase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Execute run qa_ec_stress",
                              steps="""
        1. Execute run qa_ec_stress
        """)

    def run(self):
        RunAppBase._run(self, app='qa_ec_stress',
                        arg="""{min_ndata:2, max_ndata:4, min_nparity:1, max_nparity:8, min_stridelen:640,
                         max_stridelen:640, syslog:1, seq_fail:True, enable_multi_pcs: True, num_pcs:8}""")


class ExecuteSoakJpgZip(RunAppBase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Execute run soak_jpg_zip",
                              steps="""
        1. Execute run crypto_raw_speed
        """)

    def run(self):
        RunAppBase._run(self, app='soak_jpg_zip', arg='{num_flows:4096, run_time.sec:240, log_level:1}')


class ExecuteLe(RunAppBase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Execute run le_perf",
                              steps="""
        1. Execute run le_perf
        """)

    def run(self):
        RunAppBase._run(self, app='le_perf', arg='{per_vp:20000, repeat=50}')


class AsyncCrypto(RunAppBase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="Execute run crypto_raw_speed",
                              steps="""
        1. Async run crypto_raw_speed
        """)

    def run(self):
        RunAppBase._run(self, app='crypto_raw_speed', arg='{src:bm, dst:hbm, vp_iters:5000, cr_test_mute:True}',
                        run='async')


class AsyncEc(RunAppBase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="Execute run qa_ec_stress",
                              steps="""
        1. Async run qa_ec_stress
        """)

    def run(self):
        RunAppBase._run(self, app='qa_ec_stress',
                        arg="""{min_ndata:2, max_ndata:4, min_nparity:1, max_nparity:8, min_stridelen:640,
                         max_stridelen:640, syslog:1, seq_fail:True, enable_multi_pcs: True, num_pcs:8}""",
                        run='async')


class AsyncSoakJpgZip(RunAppBase):
    def describe(self):
        self.set_test_details(id=13,
                              summary="Execute run soak_jpg_zip",
                              steps="""
        1. Async run crypto_raw_speed
        """)

    def run(self):
        RunAppBase._run(self, app='soak_jpg_zip', arg='{num_flows:4096, run_time.sec:240, log_level:1}', run='async')


class AsyncLe(RunAppBase):
    def describe(self):
        self.set_test_details(id=14,
                              summary="Execute run le_perf",
                              steps="""
        1. Async run le_perf
        """)

    def run(self):
        RunAppBase._run(self, app='le_perf', arg='{per_vp:20000, repeat=50}', run='async')


if __name__ == "__main__":
    ts = AppRun()
    for tc in (
            ExecuteCrypto,
            ExecuteEc,
            ExecuteSoakJpgZip,
            ExecuteLe,
            AsyncCrypto,
            AsyncEc,
            AsyncSoakJpgZip,
            AsyncLe,
    ):
        ts.add_test_case(tc())
    ts.run()
