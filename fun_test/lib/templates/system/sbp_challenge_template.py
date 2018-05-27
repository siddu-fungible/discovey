from lib.system.fun_test import fun_test
from lib.host.linux import Linux
import sys
import struct
import binascii

WRITE32_PATH = "/home/root/write32/write32.elf"
CODESCAPE_DIR = "/home/john/.local/opt/imgtec/Codescape-8.6"
CODESCAPE_LIB_RELATIVE_PATHS = [".",
                                "lib/python2.7/site-packages/sitepackages.zip",
                                'lib/python2.7/site-packages/sitepackages.zip',
                                'Codescape-Console',
                                'lib/python27.zip',
                                'lib/python2.7',
                                'lib/python2.7/plat-linux2',
                                'lib/python2.7/lib-tk',
                                'lib/python2.7/lib-old',
                                'lib/python2.7/lib-dynload']
map(lambda x: sys.path.append(CODESCAPE_DIR + "/" + x), CODESCAPE_LIB_RELATIVE_PATHS)


class Allocate(object):
    "Used as 'malloc' in host memory"

    def __init__(self, stop=0xFFFF, start=0xc000):
        self.addr = start
        self.stop = stop
        self.start = start

    def malloc(self, size, align=True):
        if align:
            # Align at word boundary
            self.addr += -self.addr % 4
        addr = self.addr
        self.addr = addr + size
        if self.addr > self.stop:
            # Wrap around
            addr = self.start
            self.addr = addr + size
        return addr


_allocate = Allocate(start=0, stop=4192)


class Buffer(object):
    "Describe a byte string in memory"

    def __init__(self, data="", fw_name=None, addr=None, size=None, metadata=None, cmt=""):
        assert cmt
        assert (not (data and fw_name))
        self.size = size or len(data) / 2
        self.addr = addr or _allocate.malloc(self.size)
        self.metadata = metadata
        self.cmt = cmt
        if self.metadata:
            self.param = (self.metadata, "Metadata for %s" % self.cmt)
        else:
            self.param = (self.size, "Size of %s" % self.cmt)
        if data:
            wrmem_(self.addr, data, self.cmt)
        if fw_name:
            wrfile(self.addr, fw_name, self.cmt)

    def print_words(self):
        print ("\n{}:\n".format(self.cmt))
        num_words = self.size * 8 / 32
        words = list(struct.unpack('{}I'.format(num_words), self.addr))
        for word in words:
            print "%08x" % word
        i = 0


COMMANDS = {
    # Functional commands
    "WrapKey": 0x01000000,
    "LoadARTable": 0x01010000,
    "UnwrapKey": 0x01020000,
    "ReadARTable": 0x01030000,
    "CommitARTable": 0x01040000,
    "DeleteKey": 0x01050000,
    "TransferKey": 0x01060000,
    "CreateKey": 0x02000000,
    "ReadPubKey": 0x02010000,
    "DeriveKey": 0x02020000,
    "Hash": 0x03000000,
    "HashUpdate": 0x03010000,
    "HMAC": 0x03020000,
    "AES_Encrypt": 0x04000000,
    "AES_Decrypt": 0x04010000,
    "AES_GCM_Encrypt": 0x04020000,
    "AES_GCM_Decrypt": 0x04030000,
    "AES_CMAC": 0x04040000,
    "AES_CCM_Encrypt": 0x04050000,
    "AES_CCM_Decrypt": 0x04060000,
    "RSA_Encrypt": 0x05000000,
    "RSA_Decrypt": 0x05010000,
    "Sign": 0x06000000,
    "Verify": 0x06010000,
    "EdDSA_Sign": 0x06020000,
    "EdDSA_Verify": 0x06030000,
    "GetRandom": 0x07000000,
    "ReadClock": 0x07020000,
    "GenPrime": 0x07030000,
    "BootSuccess": 0x07040000,
    "RevokePubKeyBoot": 0x07050000,
    "WriteOTP": 0x08000000,
    "ReadOTP": 0x08010000,
    "IntegrityConfigure": 0x09000000,
    "IntegrityUpdate": 0x09010000,
    "IntegrityVerify": 0x09020000,
    "CertifyKey": 0x0A000000,
    "CertifyTime": 0x0A010000,
    "ReadChipCert": 0x0A020000,
    "JPAKE_Round1": 0x0B000000,
    "JPAKE_Round2": 0x0B010000,
    "JPAKE_GenSessionKey": 0x0B020000,
    "ChaChaPoly_Aead_Encrypt": 0x0C000000,
    "ChaChaPoly_Aead_Decrypt": 0x0C010000,
    "ChaCha20_Encrypt": 0x0C020000,
    "ChaCha20_Decrypt": 0x0C030000,
    "Poly1305_KeyGen_MAC": 0x0C040000,
    "SRP_GenVerifier": 0x0D010000,
    "SRP_UserGenPub": 0x0D020000,
    "SRP_HostGenPub": 0x0D030000,
    "SRP_UserGenKey": 0x0D040000,
    "SRP_HostGenKey": 0x0D050000,
    "DiffieHellman": 0x0E000000,
    "DRBG_Hash_Instantiate": 0x0F000000,
    "DRBG_Hash_Reseed": 0x0F010000,
    "DRBG_Hash_Get_Random": 0x0F020000,
    "DRBG_Hash_Uninstantiate": 0x0F030000,
    "DES_Encrypt": 0x10000000,
    "DES_Decrypt": 0x10010000,
    "DES_CBC_MAC": 0x10020000,
    "FlashEraseSection": 0xFC000000,
    "FlashProgram": 0xFC010000,
    "FlashRead": 0xFC020000,
    "GetChallenge": 0xFD000000,
    "DebugAccess": 0xFD010000,
    "DisableTamper": 0xFD020000,
    "ReadSerialNumber": 0xFE000000,
    "GetStatus": 0xFE010000,
    "ReadPubKeyBoot": 0xFE020000,
    "SetUpgradeFlag": 0xFE030000,
    "SetStartCertificate": 0xFE0A0000,
    "DiagReadOTP": 0xFE0B0000,
    "InitOTP": 0xFF000000,
    "CreateEKPair": 0xFF010000,
    "CreateSRK": 0xFF020000,
    "EnrollPUF": 0xFF030000,
    "ReadPubEK": 0xFF040000,
    "GeneratePUF": 0xFF050000,
    "SavePUFCert": 0xFF060000,
    "SecureUpgrade": 0x43100000,
    # Test commands
    "Multiply": 0x43000000,

    "TEST_BYPASS": 0x54000000,
    "TEST_CRYPTOWRAP": 0x54020000,
    "TEST_RTC": 0x54030000,
    "TEST_TIMER": 0x54040000,
    "TEST_WATCHDOG": 0x54050000,
    "TEST_EXTDMA": 0x54060000,
    "TEST_EXTDMA_RST": 0x54070000,
    "TEST_DBGACCES": 0x54080000,
    "TEST_TAMPER": 0x54090000,
    "TEST_RESET_DONE": 0x540A0000,
    "TEST_BATTREGS_WRITE": 0x540B0000,
    "TEST_BATTREGS_ERASED": 0x540C0000,
    "TEST_EXTDMA_ERROR": 0x540D0000,
    "TEST_EXTDMA_PROT": 0x540E0000,
    "TEST_DBGGRANT": 0x540F0000,
    "TEST_OTP_ERASE": 0x54100000,
    "TEST_TAMPERIRQ": 0x54110000,
    "TEST_INITSECSTOR": 0x54120000,
    "TEST_SMTAMPEROFF": 0x54130000,
    "TEST_APBM_CORE": 0x54140000,
    "TEST_STACK_PROT": 0x54150000,
    "TEST_AHBM": 0x54190000,
    "TEST_APBM_PDON": 0x541A0000,
    "TEST_EVENT": 0x541B0000,
    "TEST_AUTH_FW_SIZE": 0x541C0000,
    "TEST_INIT_SRK": 0x541D0000,
    "TEST_CRYPTOLIB": 0x54200000,
    "TEST_OTP_DESTROYED": 0x54210000,
    "TEST_SET_WD_LVL2": 0x54220000,
    "TEST_BLOCK_MAIN_LOOP": 0x54230000,
    "TEST_DISABLE_WD_INT": 0x54240000,
    "TEST_CHECK_WD_ENABLE": 0x54250000,
    "TEST_RNG_ERROR": 0x54260000,
    "TEST_RAM_ERASE": 0x54270000,
    "TEST_SYSREGS": 0x54280000,
    "TEST_MEM_ACCESS": 0x54290000,
    "TEST_QSPI": 0x542A0000,
    "TEST_PKE": 0x542D0000,
    "TEST_GPIO_READ": 0x542E0000,
    "TEST_PKE_RSA2K": 0x542F0000,
    "TEST_AXIM": 0x54310000,
    "TEST_GPIO_WRITE": 0x54320000,
    "TEST_GPIO_IRQ": 0x54330000,
    "TEST_FIXED_ACCESS_CHALLENGE": 0x54340000,
    "TEST_WRITE_MK_HW_OTP": 0x54350000,
    "TEST_EXTDMA_SG": 0x54360000,
    "TEST_SBPPUF_SIGN": 0x54370000,
    "TEST_SBPPUF_ECCMUL_USER": 0x54380000,
    "TEST_WRITE_MK_SELECTOR": 0x54390000,
    "TEST_SBPPUF_READ_PUBEK": 0x543A0000,
    "TEST_SBPPUF_INVALID_CMD": 0x543B0000,
    "TEST_WD_LVL2_OFF": 0x543C0000,
    "TEST_SBPPUF_SOFTRST": 0x543D0000,
    "TEST_PKE_SOFTRST": 0x543E0000,
    "TEST_TRIGGER_BOOT_EXCEPTION": 0x54400000,

    # Fungible tests
    "TEST_READ_EEPROM": 0x54A00000,
    "TEST_VERIFY_CERTIFICATE": 0x54B00000,

    # Tamper source - for use in tamper tests
    "TAMP0": 0x00000000,
    "TAMP1": 0x00000100,
    "TAMP2": 0x00000200,
    "TAMP3": 0x00000300,
    "TAMP4": 0x00000400,
    "TAMP5": 0x00000500,
    "TAMP6": 0x00000600,
    "TAMP7": 0x00000700,
    "TAMP8": 0x00000800,
    "TAMP9": 0x00000900,
    "TAMP10": 0x00000a00,
    "TAMP11": 0x00000b00,
    "TAMP12": 0x00000c00,
    "TAMP13": 0x00000d00,
    "TAMP14": 0x00000e00,
    "TAMP15": 0x00000f00,

    # Hash
    "MD5": 0x00000100,
    "SHA1": 0x00000200,
    "SHA224": 0x00000300,
    "SHA256": 0x00000400,
    "SHA384": 0x00000500,
    "SHA512": 0x00000600,
    # AES modes
    "ECB": 0x00000100,
    "CBC": 0x00000200,
    "CTR": 0x00000300,
    "CFB": 0x00000400,
    "OFB": 0x00000500,
    "XTS": 0x00000800,
    # JPAKE
    "Gen": 0x00000000,
    "Ver": 0x00000100,
    # KDF
    "PBKDF2": 0x00000002,
    "HKDF": 0x00000003,
    # Context
    "Start": 0x00000001,
    "End": 0x00000002,
    "Middle": 0x00000003,
    # RSA padding
    "OAEP": 0x00000001,
    "EME": 0x00000002,  # EME-PKCS
    "EMSA": 0x00000003,  # EMSA-PKCS
    "PKCS": 0x00000000,  # Combined with EME- or EMSA-
    "PSS": 0x00000004,
    # Manufacturer
    "CM": 0x00000000,
    "SM": 0x00000001,
    # Image type
    "FW": 0x00000000,
    "HOST": 0x00000001,
    "CONF": 0x00000002,
    # SRP
    "6": 0x00000000,
    "6a": 0x00000001,
    # LE/BE
    "BE": 0x00000000,
    "LE": 0x00000001,
}

import secure_debug as sd


def messag(msg):
    print msg


class SbpChallengeTemplate():
    def __init__(self, board_ip=None, probe_ip=None, probe_name=None):
        self.board_ip = board_ip
        self.probe_ip = probe_ip
        self.probe_name = probe_name

    def setup_board(self):
        board = Linux(host_ip=self.board_ip, ssh_username="root", ssh_password="password")
        command = "{} 0x40074 1".format(WRITE32_PATH)
        board.command(command)

    def test(self):
        sd.probe(self.probe_name, self.probe_ip, force_disconnect=True)
        # output = sd.esecure_print_status()
        # sd.dump_status()
        # self.chal_cmd(command=0xFD000000)
        tamper_status = Buffer(size=16, cmt="Tamper Status")
        boot_status = Buffer(size=12, cmt="Boot Status")
        self.chal_cmd("GetStatus", outputs=[tamper_status, boot_status])
        tamper_status.print_words()
        boot_status.print_words()
        # print binascii.hexlify(tamper_status.addr)
        # print binascii.hexlify(boot_status.addr)

        sd.esecure_print_status()

        # sd.esecure_write(0x8)
        # sd.esecure_write(0xFE010000)
        # print "\nStatus:"
        # sd.dump_status_data()

    def parse_command_word(self, name):
        s = name.split(":")
        if s[0] == "RAW_ARG":
            return int(s[1], 0)
        raise Exception("Unhandled command type: %s" % name)

    def get_command_word(self, name):
        "Convert command name to command word (if applicable)"
        if not isinstance(name, str):
            return name
        word = 0
        for x in name.split("-"):
            if x in COMMANDS:
                word |= COMMANDS[x]
            else:
                word |= parse_command_word(x)

        return word

    def chaltx(self, data, cmt):
        print ("chaltx: {}".format(cmt))
        sd.esecure_write(data)

    def chalrx(self, size, cmt):
        print "chalrx: {}".format(cmt)
        result = ""
        data = sd.esecure_read()
        # result += struct.pack('<I', data)

        for i in range(size - 1):
            read_data = sd.esecure_read()
            result += struct.pack('<I', read_data)
        return result

    def chal_tx(self, cmd, params=[], inputs=[], outputs=[], cmd_len=0):
        "Send command to challenge interface"
        messag("    Send message")
        # Header
        size = 8 + 4 * len(params)
        for input in inputs:
            size += input.size
        if cmd_len:
            self.chaltx(cmd_len, "Header (%d bytes)" % cmd_len)
        else:
            self.chaltx(size, "Header (%d bytes)" % size)
        # Command
        self.chaltx(self.get_command_word(cmd), "Command: %s" % cmd)
        # Parameters
        for param, cmt in params:
            self.chaltx(param, "Parameter: %s" % cmt)
        # Inputs
        for input in inputs:
            word_size = (input.size + 3) / 4
            mem2ch(input.addr, word_size * 32, input.cmt)
        # Append zero words if requested
        if cmd_len:
            for word in range((cmd_len - size + 3) / 4):
                self.chaltx(0, "Appending zeroes")

    def chal_cmd(self, cmd, params=[], inputs=[], outputs=[], status=0, cmd_len=0):
        "Execute command through challenge interface"
        self.chal_tx(cmd, params, inputs, outputs, cmd_len)
        self.chal_rx(status, outputs)

    def chal_rx(self, status, outputs=[]):
        "Receive response from challenge interface"
        messag("    Receive response")
        # Header
        size = 4 * 8 / 32  # convert to bits, then divide by size of word
        if status == 0:
            for output in outputs:
                size += output.size * 8 / 32  # convert to bits, then divide by size of word
        data = self.chalrx(size | (status << 16), "Header (%d bytes, status = %d)" % (size, status))
        # Outputs
        if status == 0:
            # all_outputs = list(struct.unpack('<{}I'.format(size), data))
            f = "<"
            for output in outputs:
                num = output.size * 8 / 32
                f += "{}I".format(num)
            unpacked_outputs = list(struct.unpack(f, data))
            #for unpacked_output in unpacked_outputs:
            #    print hex(unpacked_output)
            unpacked_index = 0
            for index, output in enumerate(outputs):
                num = output.size * 8 / 32
                temp = ""
                for i in range(num):
                    temp += struct.pack('<I', unpacked_outputs[unpacked_index])
                    unpacked_index += 1
                output.addr = temp #struct.unpack('<{}I'.format(num), temp)

            # for output in outputs:
            #     # ch2mem(output.addr, output.size * 8, output.cmt)
            #     for i in (output.size * 8)/32:
            #         output.addr += struct.pack('<I')
            #     pass
