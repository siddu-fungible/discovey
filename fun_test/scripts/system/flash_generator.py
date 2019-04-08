import json
import argparse
import fnmatch
import os
import subprocess
from shutil import copyfile

# Sample spec file:
'''
{
  "name": "flash_image",
  "size": "0x40000",
  "puf_rom": {
    "a": {
      "version": "0x1"
    }
  },
  "firmware": {
    "a": {
      "key": "fpk3",
      "version": "0x1"
    }
  },
  "host": {
    "a": {
      "key": "fpk5",
      "version": "0x2"
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
      "version": "0x1",
      "key": "fpk5"
    }
  }
}
'''

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
    START_CERTIFICATE_NAME = "start_certificate_{}.bin"
    PUF_ROM_NAME = "esecure_puf_rom_packed_{}.bin"
    FIRMWARE_NAME = "esecure_firmware_packed_{}.bin"
    HOST_NAME = "host_firmware_packed_{}.bin"
    ENROLLMENT_TBS_NAME = "enroll_tbs.bin"
    ENROLLMENT_CERTIFICATE_NAME = "enroll_cert.bin"
    EEPROM_NAME = "eeprom_packed_{}.bin"
    FIRMWARE_IMAGE_PY_PATH = "../devtools/firmware/generate_firmware_image.py"
    GEN_FLASH2_PY_PATH = "../devtools/firmware/generate_flash2.py"
    FLASH_CONFIG_FILE = "flash_config"
    DEFAULT_PUF_ROM_BIN = "puf_rom_m5150.bin"
    DEFAULT_FIRMWARE_BIN = "firmware_m5150.bin"
    DEFAULT_FLASH_IMAGE_BASENAME = "flash_image"
    DEFAULT_EEPROM_BIN = "../../software/eeprom/eeprom_zync6"
    DEFAULT_HOST_BIN = "../../build_dir/software/host/crosscc_host_bmetal_v0-prefix/src/crosscc_host_bmetal_v0-build/firmware/host_bmetal.bin"

    def __init__(self,
                 artifacts_dir,
                 tbs,
                 spec,
                 output_dir):
        self.artifacts_dir = artifacts_dir
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

        self.start_certificate = {}
        self.start_certificate["a"] = {"name": ""}
        self.start_certificate["b"] = {"name": ""}

        self.eeprom = {}
        self.eeprom["a"] = {"name": ""}
        self.eeprom["b"] = {"name": ""}

        self.tbs = tbs
        if not self.tbs:
            self.tbs = self.artifacts_dir + "/" + self.ENROLLMENT_TBS_NAME
        self.output_dir = output_dir
        self.spec = spec

    def set_image_size(self, size):
        self.image_size = size

    def set_page_size(self, size):
        self.page_size = size

    def get_config(self, qspi=False):
        return ""

    def set_puf_rom(self,
                    version,
                    binary,
                    bank="a",
                    type="pufr"):
        d = self.puf_rom[bank]
        d["name"] = self.PUF_ROM_NAME.format(bank)
        d["version"] = version
        d["start_certificate"] = self.START_CERTIFICATE_NAME.format(bank)
        d["type"] = type
        d["binary"] = binary

    def set_firmware(self, version, binary, key, bank="a", type="frmw"):
        d = self.firmware[bank]
        d["name"] = self.FIRMWARE_NAME.format(bank)
        d["binary"] = binary
        d["version"] = version
        d["key"] = key
        d["type"] = type

    def set_host(self, version, binary, key, bank="a", type="host"):
        d = self.host[bank]
        d["name"] = self.HOST_NAME.format(bank)
        d["binary"] = binary
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
                              bank="a"):
        d = self.start_certificate[bank]
        d["name"] = self.START_CERTIFICATE_NAME.format(bank)
        d["serial_number"] = serial_number
        d["serial_number_mask"] = serial_number_mask
        d["tamper_flags"] = tamper_flags
        d["debugger_flags"] = debugger_flags
        d["public_key"] = public_key
        d["key"] = key

    def set_enrollment_certificate(self, reserve, key):
        self.enrollment_certificate["name"] = self.ENROLLMENT_CERTIFICATE_NAME
        self.enrollment_certificate["reserve"] = reserve
        self.enrollment_certificate["key"] = key

    def set_eeprom(self, key, binary, version, bank="a", type="eepr"):
        d = self.eeprom[bank]
        d["name"] = self.EEPROM_NAME.format(bank)
        d["binary"] = binary
        d["key"] = key
        d["version"] = version
        d["type"] = type

    def write_flash_config(self):
        config = CONFIG_TEMPLATE.format(self.image_size,
                                        self.DEFAULT_FLASH_IMAGE_BASENAME,
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
        poll_status, stdout, stderr = 0, "", ""
        for bank, info in self.puf_rom.iteritems():
            if self.start_certificate[bank]["name"]:
                s = "python3 {} certificate --tamper_flags {} --debugger_flags {} --serial_number {} --serial_number_mask {} --public {} --key {} --output {}".format(
                    self.FIRMWARE_IMAGE_PY_PATH,
                    self.start_certificate[bank]["tamper_flags"],
                    self.start_certificate[bank]["debugger_flags"],
                    self.start_certificate[bank]["serial_number"],
                    self.start_certificate[bank]["serial_number_mask"],
                    self.start_certificate[bank]["public_key"],
                    self.start_certificate[bank]["key"],
                    self.start_certificate[bank]["name"])
                poll_status, stdout, stderr = self.execute_command(s)
                if poll_status:
                    break
        return poll_status, stdout, stderr

    def generate_puf_rom(self):
        poll_status, stdout, stderr = 0, "", ""
        for bank, info in self.puf_rom.iteritems():
            if self.puf_rom[bank]["name"]:
                s = "python3 {} image --fwpath {} --fwver {} --fwtype {} --certificate {} --output {}".format(
                    self.FIRMWARE_IMAGE_PY_PATH,
                    self.puf_rom[bank]["binary"],
                    self.puf_rom[bank]["version"],
                    self.puf_rom[bank]["type"],
                    self.start_certificate[bank]["name"],
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
                    self.firmware[bank]["binary"],
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
                    self.eeprom[bank]["binary"],
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
                    self.host[bank]["binary"],
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
        s = "python {} {} ./{}".format(self.GEN_FLASH2_PY_PATH, self.FLASH_CONFIG_FILE,
                                       self.ENROLLMENT_CERTIFICATE_NAME)
        output = self.execute_command(s)
        images_to_copy = [self.DEFAULT_FLASH_IMAGE_BASENAME + "." + x for x in ["map", "bin", "byte"]]
        for image_to_copy in images_to_copy:
            copyfile(image_to_copy, self.output_dir + "/" + image_to_copy)
        return output

    def generate(self):
        image_size = self.spec["size"]

        # Enrollment certificate
        enrollment_certificate_key = self.spec["enrollment_certificate"]["a"]["key"]

        banks = ["a", "b"]
        for bank in banks:
            # Start-certificate:
            start_certificate_spec = self.spec["start_certificate"]
            if bank in start_certificate_spec:
                spec = self.spec["start_certificate"][bank]
                serial_number = spec["serial_number"]
                serial_number_mask = spec["serial_number_mask"]
                tamper_flags = spec["tamper_flags"]
                debugger_flags = spec["debugger_flags"]
                start_certificate_key = spec["key"]
                start_certificate_public_key = spec["public_key"]
                fg.set_start_certificate(serial_number=serial_number,
                                         serial_number_mask=serial_number_mask,
                                         tamper_flags=tamper_flags,
                                         debugger_flags=debugger_flags,
                                         key=start_certificate_key,
                                         public_key=start_certificate_public_key, bank=bank)

            # PUF-ROM
            puf_rom_spec = self.spec["puf_rom"]
            if bank in puf_rom_spec:
                puf_rom_version = self.spec["puf_rom"][bank]["version"]
                puf_rom_type = self.spec["puf_rom"][bank].get("type", "pufr")
                puf_rom_binary = self.spec["puf_rom"][bank].get("binary", os.path.join(self.artifacts_dir,
                                                                                       self.DEFAULT_PUF_ROM_BIN))
                fg.set_puf_rom(version=puf_rom_version, bank=bank, type=puf_rom_type, binary=puf_rom_binary)

            # Firmware
            firmware_spec = self.spec["firmware"]
            if bank in firmware_spec:
                firmware_version = self.spec["firmware"][bank]["version"]
                firmware_key = self.spec["firmware"][bank]["key"]
                firmware_type = self.spec["firmware"][bank].get("type", "frmw")
                firmware_binary = self.spec["firmware"][bank].get("binary", os.path.join(self.artifacts_dir,
                                                                                         self.DEFAULT_FIRMWARE_BIN))
                fg.set_firmware(version=firmware_version, key=firmware_key, type=firmware_type, binary=firmware_binary)

            # EEPROM
            eeprom_spec = self.spec["eeprom"]
            if bank in eeprom_spec:
                eeprom_version = eeprom_spec[bank]["version"]
                eeprom_key = eeprom_spec[bank]["key"]
                eeprom_type = eeprom_spec[bank].get("type", "eepr")
                eeprom_binary = eeprom_spec[bank].get("binary", self.DEFAULT_EEPROM_BIN)
                fg.set_eeprom(key=eeprom_key, version=eeprom_version, type=eeprom_type, binary=eeprom_binary)

            # Host
            host_spec = self.spec["host"]
            if bank in host_spec:
                host_version = host_spec[bank]["version"]
                host_key = host_spec[bank]["key"]
                host_type = host_spec[bank].get("type", "host")
                host_binary = host_spec[bank].get("binary", self.DEFAULT_HOST_BIN)
                fg.set_host(version=host_version, key=host_key, type=host_type, binary=host_binary)

        # General settings
        fg.set_image_size(size=image_size)
        if "page_size" in self.spec:
            page_size = self.spec["page_size"]
            fg.set_page_size(size=page_size)

        # Set enrollment certificate
        reserve = 2000
        fg.set_enrollment_certificate(reserve=reserve, key=enrollment_certificate_key)
        fg.write_flash_config()
        stages = ["GEN_ENROLLMENT_CERT", "GEN_START_CERT", "GEN_PUF_ROM", "GEN_EEPROM", "GEN_HOST", "GEN_FIRMWARE",
                  "GEN_FLASH"]

        for stage in stages:
            print("\n***** Stage: {} ***** \n\n".format(stage))
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
        result = self.DEFAULT_HOST_BIN
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
    # Usage: python custom_flash_generator.py --artifacts_dir ../../artifacts_secure_eeprom_zync6/ --spec flash_config.json --output_dir ../../artifacts_secure_eeprom_zync6
    parser = argparse.ArgumentParser(description="custom_flash_generator")
    parser.add_argument('--spec',
                        dest="spec",
                        required=True,
                        help="Specification of the flash contents")
    parser.add_argument('--artifacts_dir',
                        dest="artifacts_dir",
                        required=True,
                        help="Location of the pre-built artifacts")
    parser.add_argument('--tbs',
                        dest="tbs",
                        help="Path to TBS",
                        default=None)
    parser.add_argument('--output_dir',
                        dest="output_dir",
                        help="Directory where flash_image.bin should be placed")
    args = parser.parse_args()

    with open(args.spec, "r") as fp:
        spec = json.load(fp)
        fg = FlashGenerator(artifacts_dir=args.artifacts_dir,
                            tbs=args.tbs, spec=spec,
                            output_dir=args.output_dir)

        fg.generate()
