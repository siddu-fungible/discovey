from lib.system.fun_test import fun_test


class CryptoTemplate:

    # common variables used
    FUNCRYPTO = "funcrypto"
    AESNI_INTEL = "aesni_intel"
    VERSION = "version"
    ENGINE = "engine"
    AF_ALG = "af_alg"
    DIGEST_HMAC_SHA3 = "digest_hmac_sha3"
    CREATE_FILE = "mygendata_big"
    FILE_128MB = "134217728"
    TOOLS_PATH = "/bin/"
    TOOLS = ["mygendata_big"]

    def __init__(self, host):
        self.host = host

    def copy_tools(self):
        tool_path = fun_test.get_script_parent_directory() + self.TOOLS_PATH + self.TOOLS[0]
        fun_test.scp(source_file_path=tool_path,
                     target_file_path="/tmp/",
                     target_ip=self.host.host_ip,
                     target_port=self.host.ssh_port,
                     target_username=self.host.ssh_username,
                     target_password=self.host.ssh_password,
                     recursive=True)

    def create_huge_file(self):
        # tool_path = fun_test.get_script_parent_directory() + self.TOOLS_PATH + CryptoTemplate.CREATE_FILE
        tool_path = "/tmp/" + CryptoTemplate.CREATE_FILE
        create_file_command = tool_path + " " + self.FILE_128MB + " > " + "/home/root/" + self.FILE_128MB + ".txt"
        print "command: ", create_file_command
        command_output = self.host.command(create_file_command)

    def load_funcrypto(self):
        self.host.modprobe(self.FUNCRYPTO)

    def unload_funcrypto(self):
        self.host.rmmod(self.FUNCRYPTO)

    def load_aesni(self):
        self.host.modprobe(self.AESNI_INTEL)

    def unload_aesni(self):
        self.host.rmmod(self.AESNI_INTEL)

    def verify_funcrypto(self):
        # check if funcrypto module is loaded
        fun_test.test_assert((self.host.lsmod(self.FUNCRYPTO)), message="funcrypto loaded")
        return True

    def parse_input(self, file_path):
        plaintext_list = []
        digest_list = []
        input_dict = {}
        for line in open(file_path, 'r').read().split(','):
            line_list = line.split("=")
            if len(line_list) > 1:
                if ".plaintext" in line_list[0]:
                    plaintext_list.append((line_list[1].replace('"', '').replace('\n', '')).strip())
                elif ".digest" in line_list[0]:
                    digest_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())

        for plain_text, digest in zip(plaintext_list, digest_list):
            input_dict[plain_text] = digest

        return input_dict

    def parse_input_huge(self, file_path):
        size_list = []
        digest_list = []
        input_dict = {}
        for line in open(file_path, 'r').read().split(','):
            line_list = line.split("=")
            if len(line_list) > 1:
                if ".size" in line_list[0]:
                    size_list.append((line_list[1].replace('"', '').replace('\n', '')).strip())
                elif ".digest" in line_list[0]:
                    digest_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())

        for size, digest in zip(size_list, digest_list):
            input_dict[size] = digest

        return input_dict

    def parse_input_hmac(self, file_path):
        plaintext_list = []
        key_list = []
        digest_list = []
        plaintext_key_dict={}
        input_dict = {}

        for line in open(file_path, 'r').read().split(','):
            line_list = line.split("=")
            if len(line_list) > 1:
                if ".key" in line_list[0]:
                    key_list.append((line_list[1].replace('"', '').replace('\n', '')).strip())
                elif ".plaintext" in line_list[0]:
                    plaintext_list.append((line_list[1].replace('"', '').replace('\n', '')).strip())
                elif ".digest" in line_list[0]:
                    digest_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())

        for plain_text, key, hmac in zip(plaintext_list, key_list, digest_list):
            plaintext_key_dict[key] = plain_text
            input_dict[hmac] = plaintext_key_dict

        return input_dict

    def compute_digest(self, algorithm, digest_input, engine=None):
        return True

    """
    example commands:   ./digest_hmac_sha3 "hmac(sha3-224-generic)" file.txt key_text_imm "Jefe"
                        ./digest_hmac_sha3 "hmac(sha3-256-generic)" file.txt key_hex_imm "\x0b\x0b\x0b\x0b\x0b"
                        ./digest_hmac_sha3 "hmac(sha3-224-generic)" file.txt key_hex_esc_imm "0b0b0b0b0b"
                        ./openssl dgst -sha1 -hmac "Jefe" test.bin
                        ./openssl dgst -sha1 -mac HMAC -macopt hexkey:4a656665  test.bin
    """
    def compute_hmac(self, algorithm, hmac_input, key_type=None, key=None, engine=None):
        return True

    def encrypt(self, algorithm,  encrypt_input_file, encrypt_output_file, key):
        return True

    def decrypt(self, algorithm, decrypt_input_file, encrypt_output_file, key):
        return True