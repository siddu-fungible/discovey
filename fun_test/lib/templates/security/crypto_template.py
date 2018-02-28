from lib.system.fun_test import fun_test


class CryptoTemplate:

    # common variables used
    FUNCRYPTO = "funcrypto"
    VERSION = "version"
    ENGINE = "engine"
    AF_ALG = "af_alg"

    def __init__(self, host):
        self.host = host

    def load_funcrypto(self):
        self.host.modprobe(self.FUNCRYPTO)

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

    def compute_hmac(self, algorithm, key, hmac_input, engine=None):
        return True

    def encrypt(self, algorithm,  encrypt_input_file, encrypt_output_file, key):
        return True

    def decrypt(self, algorithm, decrypt_input_file, encrypt_output_file, key):
        return True