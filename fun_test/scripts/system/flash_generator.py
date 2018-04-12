'''
{
  "name": "flash_image",
  "size": "0xE0000",
  "page_size": "0x10000",
  "puf-rom": {
    "a": {
      "name": "esecure_puf_rom_packed_v1.bin",
      "version": "0x1",
      "start_certificate": "start_certificate.bin"
    },
    "b": {
      "name": ""
    }
  },
  "firmware": {
    "a": {
      "name": "esecure_firmware_packed_v1.bin",
      "key": "fpk3",
      "version": "0x1"
    },
    "b": {
      "name": ""
    }
  },
  "host": {
    "a": {
      "name": "host_firmware_packed_v1.bin",
      "key": "fpk5",
      "version": "0x2"
    },
    "b": ""
  },
  "enrollment_certificate": {
    "a": {
      "name": "",
      "reserve": 2000,
      "key": "fpk4"
    }
  },
  "start_certificate": {
    "serial_number": "0x00",
    "serial_number_mask": "00",
    "tamper_flags": "pufr",
    "debugger_flags": "000",
    "name": "start_certificate.bin",
    "public_key": "fpk2",
    "key": "fpk1"
  },
  "eeprom": {
    "a": {
      "name": "eeprom_packed_v1.bin",
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
    START_CERTIFICATE_NAME = "start_certificate.bin"
    PUF_ROM_NAME = "esecure_puf_rom_packed_{}.bin"
    FIRMWARE_NAME = "esecure_firmware_packed_{}.bin"
    HOST_NAME = "host_firmware_packed_{}.bin"
    ENROLLMENT_CERTIFICATE_NAME = "enroll_cert.bin"
    EEPROM_NAME = "eeprom_packed_{}.bin"

    def __init__(self):
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

    def set_image_size(self, size):
        self.image_size = size

    def set_page_size(self, size):
        self.page_size = size

    def get_config(self, qspi=False):
        return ""

    def set_puf_rom(self,
                    version,
                    start_certificate=START_CERTIFICATE_NAME,
                    bank="a"):
        d = self.puf_rom[bank]
        d["name"] = self.PUF_ROM_NAME.format(bank)
        d["version"] = version
        d["start_certificate"] = start_certificate

    def set_firmware(self, version, key, bank="a"):
        d = self.firmware[bank]
        d["name"] = self.FIRMWARE_NAME.format(bank)
        d["version"] = version
        d["key"] = key

    def set_host(self, version, key, bank="a"):
        d = self.host[bank]
        d["name"] = self.HOST_NAME.format(bank)
        d["version"] = version
        d["key"] = key

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

    def set_eeprom(self, key, version, bank="a"):
        d = self.eeprom[bank]
        d["name"] = self.EEPROM_NAME.format(bank)
        d["key"] = key
        d["version"] = version

    def get_flash_config(self):
        config = CONFIG_TEMPLATE.format(self.image_size,
                                        self.page_size,
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
        return config



if __name__ == "__main__":
    fg = FlashGenerator()

    image_size = "0xE0000"
    page_size = "0x10000"

    # Start-certificate

    serial_number = "00000000000000000000000000000000"
    serial_number_mask = "00000000000000000000000000000000"
    tamper_flags = "00000000"
    debugger_flags = "00000000"
    start_certificate_key = "fpk1"
    start_certificate_public_key = "fpk2"

    # PUF-ROM
    puf_rom_a_version = "0x1"
    puf_rom_b_version = "0x2"

    # Firmware
    firmware_a_version = "0x1"
    firmware_a_key = "fpk3"
    firmware_b_version = "0x2"
    firmware_b_key = "fpk3"


    # Enrollment certificate
    enrollment_certificate_key = "fpk4"

    # EEPROM
    eeprom_a_version = "0x1"
    eeprom_a_key = "fpk5"

    # Host
    host_a_version = "0x1"
    host_a_key = "fpk5"

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

    # Set PUF-ROM

    fg.set_puf_rom(version=puf_rom_a_version, bank="a")
    fg.set_puf_rom(version=puf_rom_b_version, bank="b")

    # Set Firmware

    fg.set_firmware(version=firmware_a_version, key=firmware_a_key)
    fg.set_firmware(version=firmware_b_version, key=firmware_b_key)

    # Set enrollment certificate
    reserve = 2000
    fg.set_enrollment_certificate(reserve=reserve, key=enrollment_certificate_key)

    # Set eeprom

    fg.set_eeprom(key=eeprom_a_key, version=eeprom_a_version)

    # Set host
    fg.set_host(version=host_a_version, key=host_a_key)

    print fg.get_flash_config()