from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from lib.templates.system.sbp_template import SbpZynqSetupTemplate

BIT_STREAM = "SilexBitfiles/esecure_top_fpga_sbppuf_20180322.bit"
ZYNC_BOARD_IP = "10.1.23.106"


class ContainerSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Bring up the container
        """)

    def setup(self):
        self.docker_host = AssetManager().get_any_docker_host()
        self.container_asset = SbpZynqSetupTemplate(host=None, zynq_board_ip=None).setup_container(git_pull=False)

    def cleanup(self):
        container_asset = fun_test.shared_variables["container_asset"]
        self.docker_host.destroy_container(container_name=container_asset["name"], ignore_error=True)


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="puf-rom with higher version",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config_template_path = fun_test.get_script_parent_directory() + "/flash_config.json"
        with open(config_template_path, "r") as f:
            contents = f.read()
            config = json.loads(contents)
            config["puf_rom"]["a"]["version"] = "0x3"
            # config["puf_rom"]["b"]["version"] = "0x5"
            sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
            sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
            sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

            stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
            stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
            stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

            fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                       stimuli_file=stimuli_file,
                                                       artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

            stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
            fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                       stimuli_file=stimuli_file,
                                                       artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="puf-rom A invalid but fw, host on A are valid",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk4"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="puf-rom A invalid but fw, puf-rom B invalid",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk4"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk4"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="puf-rom A valid but B is higher version and invalid",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk4"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)

class TestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="FW A invalid, choose all B",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk1",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)

class TestCase6(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="FW A invalid, Host B invalid, choose Host A",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk1",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk1",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)

class TestCase7(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="FW A invalid, Host B invalid, Host A invalid",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk1",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk2",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk1",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase8(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="puf-rom A valid, PUFR-B invalid but higher version, bad serial",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "F0000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase9(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="puf-rom A invalid higher version, B valid",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "b": {
                    "version": "0xa11"
                },
                "a": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "b": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "a": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "b": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "a": {
                    "key": "fpk1",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk4"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase10(FunTestCase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="puf-rom A invalid start-certificate public key incorrect, B valid",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk5",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)

class TestCase11(FunTestCase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="puf-rom B invalid start-certificate public key incorrect but of higher version",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        sbp_setup.artifacts_setup(enroll=True)

        config = {
            "name": "flash_image",
            "size": "0x50000",
            "puf_rom": {
                "a": {
                    "version": "0xa11"
                },
                "b": {
                    "version": "0xa22"
                }
            },
            "firmware": {
                "a": {
                    "key": "fpk3",
                    "version": "0xb11"
                },
                "b": {
                    "key": "fpk3",
                    "version": "0xb22"
                }
            },
            "host": {
                "a": {
                    "key": "fpk5",
                    "version": "0xc11"
                },
                "b": {
                    "key": "fpk5",
                    "version": "0xc22"
                }
            },
            "enrollment_certificate": {
                "a": {
                    "reserve": 2000,
                    "key": "fpk4"
                }
            },
            "start_certificate": {
                "a": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk2",
                    "key": "fpk1"
                },
                "b": {
                    "serial_number": "00000000000000000000000000000000",
                    "serial_number_mask": "00000000000000000000000000000000",
                    "tamper_flags": "00000000",
                    "debugger_flags": "00000000",
                    "public_key": "fpk5",
                    "key": "fpk1"
                }
            },
            "eeprom": {
                "a": {
                    "version": "0xd11",
                    "key": "fpk5"
                },
                "b": {
                    "version": "0xd22",
                    "key": "fpk5"
                }

            }
        }

        sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
        sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
        sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir())

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "run_test")

        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                                   stimuli_file=stimuli_file,
                                                   artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)

if __name__ == "__main__":
    ts = ContainerSetup()
    # ts.add_test_case(TestCase1())
    # ts.add_test_case(TestCase2())
    # ts.add_test_case(TestCase3())
    # ts.add_test_case(TestCase4())
    # ts.add_test_case(TestCase5())
    # ts.add_test_case(TestCase6())
    # ts.add_test_case(TestCase7())
    # ts.add_test_case(TestCase8())
    # ts.add_test_case(TestCase9())
    # ts.add_test_case(TestCase10())
    ts.add_test_case(TestCase11())

    ts.run()
