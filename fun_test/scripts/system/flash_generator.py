import json
import argparse
import fnmatch
import os
import subprocess

CONFIG_TEMPLATE = """
# Mandatory sections: All, PUF-ROM, START-CERT, FIRMWARE, HOST
[All]
size = {}
output = {}


[PUF-ROM]
A = {}
B = {}


[FIRMWARE]
A = {}
B = {}


[HOST]
A = {}
B = {}


# always reserve space for enroll certificate
[ENROLL_CERT]
A = reserve({}, 'nrol')
B =

[EEPROM]
A = {}
B = {}
optional:
"""


class FlashGenerator():
    START_CERTIFICATE_NAME = "start_certificate.bin"
    PUF_ROM_NAME = "esecure_puf_rom_packed_{}.bin"
    FIRMWARE_NAME = "esecure_firmware_packed_{}.bin"
    HOST_NAME = "host_firmware_packed_{}.bin"
    ENROLLMENT_CERTIFICATE_NAME = "enroll_cert.bin"
    EEPROM_NAME = "eeprom_packed_{}.bin"
    FIRMWARE_IMAGE_PY_PATH = "../devtools/firmware/generate_firmware_image.py"
    GEN_FLASH2_PY_PATH = "../devtools/firmware/generate_flash2.py"
    FLASH_CONFIG_FILE = "flash_config"

    def __init__(self,
                 puf_rom_binary,
                 firmware_binary,
                 eeprom_binary,
                 host_binary,
                 tbs,
                 spec):
        self.image_size = None
        self.page_size = None
        self.puf_rom = {}
        self.puf_rom["a"] = {"name": ""}
        self.puf_rom["b"] = {"name": ""}

        self.firmware = {}
        self.firmware["a"] = {"name": ""}
        self.firmware["b"] = {"name": ""}

        self.host = {}
        self.host["a"] = {"name": ""}
        self.host["b"] = {"name": ""}
        self.enrollment_certificate = {}

        self.start_cert_name = None
        self.start_cert_serial_number = None
        self.start_cert_serial_number_mask = None
        self.start_cert_tamper_flags = None
        self.start_cert_debugger_flags = None
        self.start_cert_public_key = None
        self.start_cert_key = None

        self.eeprom = {}
        self.eeprom["a"] = {"name": ""}
        self.eeprom["b"] = {"name": ""}

        self.puf_rom_binary = puf_rom_binary
        self.firmware_binary = firmware_binary
        self.eeprom_binary = eeprom_binary
        self.host_binary = host_binary
        self.tbs = tbs

        self.spec = spec

    def set_image_size(self, size):
        self.image_size = size

    def set_page_size(self, size):
        self.page_size = size

    def get_config(self, qspi=False):
        return ""

    def set_puf_rom(self,
                    version,
                    start_certificate=START_CERTIFICATE_NAME,
                    bank="a",
                    type="pufr"):
        d = self.puf_rom[bank]
        d["name"] = self.PUF_ROM_NAME.format(bank)
        d["version"] = version
        d["start_certificate"] = start_certificate
        d["type"] = type

    def set_firmware(self, version, key, bank="a", type="frmw"):
        d = self.firmware[bank]
        d["name"] = self.FIRMWARE_NAME.format(bank)
        d["version"] = version
        d["key"] = key
        d["type"] = type

    def set_host(self, version, key, bank="a", type="host"):
        d = self.host[bank]
        d["name"] = self.HOST_NAME.format(bank)
        d["version"] = version
        d["key"] = key
        d["type"] = type

    def set_start_certificate(self,
                              serial_number,
                              serial_number_mask,
                              tamper_flags,
                              debugger_flags,
                              public_key,
                              key,
                              name=START_CERTIFICATE_NAME):
        self.start_cert_name = name
        self.start_cert_serial_number = serial_number
        self.start_cert_serial_number_mask = serial_number_mask
        self.start_cert_tamper_flags = tamper_flags
        self.start_cert_debugger_flags = debugger_flags
        self.start_cert_public_key = public_key
        self.start_cert_key = key

    def set_enrollment_certificate(self, reserve, key):
        self.enrollment_certificate["name"] = self.ENROLLMENT_CERTIFICATE_NAME
        self.enrollment_certificate["reserve"] = reserve
        self.enrollment_certificate["key"] = key

    def set_eeprom(self, key, version, bank="a", type="eepr"):
        d = self.eeprom[bank]
        d["name"] = self.EEPROM_NAME.format(bank)
        d["key"] = key
        d["version"] = version
        d["type"] = type

    def write_flash_config(self):
        config = CONFIG_TEMPLATE.format(self.image_size,
                                        "flash_image",
                                        self.puf_rom["a"]["name"],
                                        self.puf_rom["b"]["name"],
                                        self.firmware["a"]["name"],
                                        self.firmware["b"]["name"],
                                        self.host["a"]["name"],
                                        self.host["b"]["name"],
                                        self.enrollment_certificate["reserve"],
                                        self.eeprom["a"]["name"],
                                        self.eeprom["b"]["name"]
                                        )
        with open(self.FLASH_CONFIG_FILE, "w") as f:
            f.write(config)

    def generate_start_certificate(self):
        s = "python3 {} certificate --tamper_flags {} --debugger_flags {} --serial_number {} --serial_number_mask {} --public {} --key {} --output {}".format(
            self.FIRMWARE_IMAGE_PY_PATH,
            self.start_cert_tamper_flags,
            self.start_cert_debugger_flags,
            self.start_cert_serial_number,
            self.start_cert_serial_number_mask, self.start_cert_public_key, self.start_cert_key, self.start_cert_name)
        return self.execute_command(s)

    def generate_puf_rom(self):
        poll_status, stdout, stderr = 0, "", ""
        for bank, info in self.puf_rom.iteritems():
            if self.puf_rom[bank]["name"]:
                s = "python3 {} image --fwpath {} --fwver {} --fwtype {} --certificate {} --output {}".format(
                    self.FIRMWARE_IMAGE_PY_PATH,
                    self.puf_rom_binary,
                    self.puf_rom[bank]["version"],
                    self.puf_rom[bank]["type"],
                    self.start_cert_name,
                    self.puf_rom[bank]["name"])
                poll_status, stdout, stderr = self.execute_command(s)
                if poll_status:
                    break
        return poll_status, stdout, stderr

    def generate_firmware(self):
        poll_status, stdout, stderr = 0, "", ""
        for bank, info in self.firmware.iteritems():
            if self.firmware[bank]["name"]:
                s = "python3 {} image --fwpath {} --fwver {} --fwtype {} --key {} --output {}".format(
                    self.FIRMWARE_IMAGE_PY_PATH,
                    self.firmware_binary,
                    self.firmware[bank]["version"],
                    self.firmware[bank]["type"],
                    self.firmware[bank]["key"],
                    self.firmware[bank]["name"])
                poll_status, stdout, stderr = self.execute_command(s)
                if poll_status:
                    break
        return poll_status, stdout, stderr

    def generate_eeprom(self):
        poll_status, stdout, stderr = 0, "", ""
        for bank, info in self.eeprom.iteritems():
            if self.eeprom[bank]["name"]:
                s = "python3 {} image --fwpath {} --fwver {} --fwtype {} --key {} --output {}".format(
                    self.FIRMWARE_IMAGE_PY_PATH,
                    self.eeprom_binary,
                    self.eeprom[bank]["version"],
                    self.eeprom[bank]["type"],
                    self.eeprom[bank]["key"],
                    self.eeprom[bank]["name"])
                poll_status, stdout, stderr = self.execute_command(s)
                if poll_status:
                    break
        return poll_status, stdout, stderr

    def generate_host(self):
        poll_status, stdout, stderr = 0, "", ""
        for bank, info in self.host.iteritems():
            if self.host[bank]["name"]:
                s = "python3 {} image --fwpath {} --fwver {} --fwtype {} --key {} --output {}".format(
                    self.FIRMWARE_IMAGE_PY_PATH,
                    self.host_binary,
                    self.host[bank]["version"],
                    self.host[bank]["type"],
                    self.host[bank]["key"],
                    self.host[bank]["name"])
                poll_status, stdout, stderr = self.execute_command(s)
                if poll_status:
                    break
        return poll_status, stdout, stderr

    def generate_enrollment_certificate(self):
        s = "python3 {} sign --fwpath {} --key {} --output {}".format(self.FIRMWARE_IMAGE_PY_PATH,
                                                                      self.tbs,
                                                                      self.enrollment_certificate["key"],
                                                                      self.enrollment_certificate["name"])
        return self.execute_command(s)

    def generate_flash(self):
        s = "python {} {}".format(self.GEN_FLASH2_PY_PATH, self.FLASH_CONFIG_FILE, self.ENROLLMENT_CERTIFICATE_NAME)
        return self.execute_command(s)

    def generate(self):
        image_size = self.spec["size"]
        page_size = self.spec["page_size"]

        # Start-certificate

        serial_number = self.spec["start_certificate"]["serial_number"]
        serial_number_mask = self.spec["start_certificate"]["serial_number_mask"]
        tamper_flags = self.spec["start_certificate"]["tamper_flags"]
        debugger_flags = self.spec["start_certificate"]["debugger_flags"]
        start_certificate_key = self.spec["start_certificate"]["key"]
        start_certificate_public_key = self.spec["start_certificate"]["public_key"]

        # PUF-ROM
        puf_rom_spec = self.spec["puf_rom"]
        if "a" in puf_rom_spec:
            puf_rom_a_version = self.spec["puf_rom"]["a"]["version"]
            puf_rom_a_type = self.spec["puf_rom"]["a"].get("type", "pufr")
            fg.set_puf_rom(version=puf_rom_a_version, bank="a", type=puf_rom_a_type)

        if "b" in puf_rom_spec:
            puf_rom_b_version = self.spec["puf_rom"]["b"]["version"]
            puf_rom_b_type = self.spec["puf_rom"]["b"].get("type", "pufr")
            fg.set_puf_rom(version=puf_rom_b_version, bank="b", type=puf_rom_b_type)

        # Firmware
        firmware_spec = self.spec["firmware"]
        if "a" in firmware_spec:
            firmware_a_version = self.spec["firmware"]["a"]["version"]
            firmware_a_key = self.spec["firmware"]["a"]["key"]
            firmware_a_type = self.spec["firmware"]["a"].get("type", "frmw")
            fg.set_firmware(version=firmware_a_version, key=firmware_a_key, type=firmware_a_type)

        if "b" in firmware_spec:
            firmware_b_version = self.spec["firmware"]["b"]["version"]
            firmware_b_key = self.spec["firmware"]["b"]["key"]
            firmware_b_type = self.spec["firmware"]["b"].get("type", "frmw")
            fg.set_firmware(version=firmware_b_version, key=firmware_b_key, type=firmware_b_type)

        # Enrollment certificate
        enrollment_certificate_key = self.spec["enrollment_certificate"]["a"]["key"]

        # EEPROM
        eeprom_spec = self.spec["eeprom"]
        if "a" in eeprom_spec:
            eeprom_a_version = eeprom_spec["a"]["version"]
            eeprom_a_key = eeprom_spec["a"]["key"]
            eeprom_a_type = eeprom_spec["a"].get("type", "eepr")
            fg.set_eeprom(key=eeprom_a_key, version=eeprom_a_version, type=eeprom_a_type)

        if "b" in eeprom_spec:
            eeprom_b_version = eeprom_spec["b"]["version"]
            eeprom_b_key = eeprom_spec["b"]["key"]
            eeprom_b_type = eeprom_spec["b"].get("type", "eepr")
            fg.set_eeprom(key=eeprom_b_key, version=eeprom_b_version, type=eeprom_b_type)

        # Host
        host_spec = self.spec["host"]
        if "a" in self.host:
            host_a_version = host_spec["a"]["version"]
            host_a_key = host_spec["a"]["key"]
            host_a_type = host_spec["a"].get("type", "host")
            fg.set_host(version=host_a_version, key=host_a_key, type=host_a_type)

        # General settings

        fg.set_image_size(size=image_size)
        fg.set_page_size(size=page_size)

        # Set start-certificate
        fg.set_start_certificate(serial_number=serial_number,
                                 serial_number_mask=serial_number_mask,
                                 tamper_flags=tamper_flags,
                                 debugger_flags=debugger_flags,
                                 key=start_certificate_key,
                                 public_key=start_certificate_public_key)

        # Set enrollment certificate
        reserve = 2000
        fg.set_enrollment_certificate(reserve=reserve, key=enrollment_certificate_key)
        fg.write_flash_config()
        stages = ["GEN_START_CERT", "GEN_PUF_ROM", "GEN_FIRMWARE", "GEN_EEPROM", "GEN_HOST", "GEN_ENROLLMENT_CERT",
                  "GEN_FLASH"]

        for stage in stages:
            print("***** Stage: {} ***** \n\n".format(stage))
            poll_status = None
            stdout = stderr = None
            if stage == "GEN_START_CERT":
                poll_status, stdout, stderr = fg.generate_start_certificate()

            if stage == "GEN_PUF_ROM":
                poll_status, stdout, stderr = fg.generate_puf_rom()

            if stage == "GEN_FIRMWARE":
                poll_status, stdout, stderr = fg.generate_firmware()

            if stage == "GEN_EEPROM":
                poll_status, stdout, stderr = fg.generate_eeprom()

            if stage == "GEN_HOST":
                poll_status, stdout, stderr = fg.generate_host()

            if stage == "GEN_ENROLLMENT_CERT":
                poll_status, stdout, stderr = fg.generate_enrollment_certificate()

            if stage == "GEN_FLASH":
                poll_status, stdout, stderr = fg.generate_flash()

            if poll_status:
                s = "{} Failed: stdout: {}, stderr: {}".format(stage, stdout, stderr)
                raise Exception(s)
            print("**** *****\n\n")
        return True

    @staticmethod
    def find_host_bin():
        result = None
        for root, dirnames, filenames in os.walk('../../'):
            for filename in fnmatch.filter(filenames, 'host_bmetal.bin'):
                result = os.path.join(root, filename)
                break
            if result:
                break
        return result

    def execute_command(self, command):
        print("Executing: {}".format(command))
        sp = subprocess.Popen(command.split(), close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        poll_status = None
        while poll_status is None:
            poll_status = sp.poll()
        stdout, stderr = sp.communicate()
        return poll_status, stdout, stderr


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="qa_flash_generator")
    parser.add_argument('--spec',
                        dest="spec",
                        required=True,
                        help="Specification of the flash contents")
    parser.add_argument('--puf_rom_binary',
                        dest="puf_rom_binary",
                        default="puf_rom_m5150.bin",
                        help="Path to PUF-ROM binary")
    parser.add_argument('--firmware_binary',
                        dest="firmware_binary",
                        default="firmware_m5150.bin",
                        help="Path to firmware binary")
    parser.add_argument('--eeprom_binary',
                        dest="eeprom_binary",
                        default="eeprom_zync6",
                        help="Path to EEPROM binary")
    parser.add_argument('--host_binary',
                        dest="host_binary",
                        help="Path to Host binary")
    parser.add_argument('--tbs',
                        dest="tbs",
                        help="Path to TBS",
                        default="enroll_cert.tbs")
    args = parser.parse_args()
    host_binary = args.host_binary
    if not host_binary:
        host_binary = FlashGenerator.find_host_bin()  # Find bin file

    assert host_binary, "Host Binary"
    with open(args.spec, "r") as fp:
        spec = json.load(fp)
        fg = FlashGenerator(puf_rom_binary=args.puf_rom_binary,
                            firmware_binary=args.firmware_binary,
                            eeprom_binary=args.eeprom_binary,
                            host_binary=host_binary,
                            tbs=args.tbs, spec=spec)

        fg.generate()