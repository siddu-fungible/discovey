from lib.system.fun_test import *
from lib.templates.security.libkcapi_speed_template import LibkcapiSpeedTemplate
from lib.host.linux import Linux


class LibkcapiSpeedScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Speed test kcapi
                              """)

    def setup(self):
        host = Linux(host_ip="10.1.20.67", ssh_username="root", ssh_port="22")
        libkcapi_speed_template = LibkcapiSpeedTemplate(host)
        fun_test.shared_variables["host"] = host
        fun_test.shared_variables["libkcapi_speed_template"] = libkcapi_speed_template

    def cleanup(self):
        pass


class SpeedCbc(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="CBC speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
        3. Driver for Ciphers can be funcrypto or aesni.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.CBC_AES, driver="aesni", test_time="5",
                                           block_size="64",
                                           aux_param=None)


class SpeedEcb(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="ECB speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.ECB_AES, driver="aesni", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedCtr(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="CTR speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.CTR_AES, driver="aesni", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedXts(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="XTS speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.XTS_AES, driver="aesni", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedGcm(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="GCM speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.GCM_AES, driver="aesni", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedCcm(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="CCM speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.CCM_AES, driver="aesni", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedSha1(FunTestCase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="SHA1 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
        3. Driver for digest(not hmac) can be generic or funcrypto.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.SHA1, driver="generic", test_time=None,
                                           block_size="256",
                                           aux_param=None)


class SpeedSha224(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="SHA224 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.SHA224, driver="generic", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedSha256(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="SHA256 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.SHA256, driver="generic", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedSha384(FunTestCase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="SHA384 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.SHA384, driver="generic", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedSha512(FunTestCase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="SHA512 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.SHA512, driver="generic", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedHmacSha1(FunTestCase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="HMAC-SHA1 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.HMAC_SHA1, driver="funcrypto", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedHmacSha224(FunTestCase):
    def describe(self):
        self.set_test_details(id=13,
                              summary="HMAC-SHA224 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.HMAC_SHA224, driver="funcrypto", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedHmacSha256(FunTestCase):
    def describe(self):
        self.set_test_details(id=14,
                              summary="HMAC-SHA256 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.HMAC_SHA256, driver="funcrypto", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedHmacSha384(FunTestCase):
    def describe(self):
        self.set_test_details(id=15,
                              summary="HMAC-SHA384 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.HMAC_SHA384, driver="funcrypto", test_time=None,
                                           block_size=None,
                                           aux_param=None)


class SpeedHmacSha512(FunTestCase):
    def describe(self):
        self.set_test_details(id=16,
                              summary="HMAC-SHA512 speed test with kcapi",
                              steps="""
        1. Login to host.
        2. Run kcapi-speed test.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_speed_template = fun_test.shared_variables["libkcapi_speed_template"]
        libkcapi_speed_template.kcapi_cmnd(LibkcapiSpeedTemplate.HMAC_SHA512, driver="funcrypto", test_time=None,
                                           block_size=None,
                                           aux_param=None)


if __name__ == "__main__":
    libkcapi_script = LibkcapiSpeedScript()

    libkcapi_script.add_test_case(SpeedCbc())
    libkcapi_script.add_test_case(SpeedEcb())
    libkcapi_script.add_test_case(SpeedCtr())
    libkcapi_script.add_test_case(SpeedXts())
    libkcapi_script.add_test_case(SpeedGcm())
    libkcapi_script.add_test_case(SpeedCcm())
    libkcapi_script.add_test_case(SpeedSha1())
    libkcapi_script.add_test_case(SpeedSha224())
    libkcapi_script.add_test_case(SpeedSha256())
    libkcapi_script.add_test_case(SpeedSha384())
    libkcapi_script.add_test_case(SpeedSha512())
    libkcapi_script.add_test_case(SpeedHmacSha1())
    libkcapi_script.add_test_case(SpeedHmacSha224())
    libkcapi_script.add_test_case(SpeedHmacSha256())
    libkcapi_script.add_test_case(SpeedHmacSha384())
    libkcapi_script.add_test_case(SpeedHmacSha512())

    libkcapi_script.run()
