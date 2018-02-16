from lib.system.fun_test import fun_test


class CryptoTemplate:

    # common variabes used

    openssl = "openssl"
    sha1 = "sha1"
    dgst = "dgst"
    funcrypto = "funcrypto"
    version = "version"
    openssl_version = "1.0.2k"
    engine = "engine"
    af_alg = "af_alg"

    def __init__(self, host):
        self.host = host

    def verify_openssl_version(self):
        # validate existence of OpenSSL
        version_output = (self.host.command(self.openssl + " " + self.version)).split(" ")
        fun_test.debug("OpenSSL version output: {}".format(version_output))
        version = version_output[1]
        fun_test.test_assert_expected(expected=self.openssl_version,
                                      actual=version,
                                      message="OpenSSL version as expected")
        return True

    def load_funcrypto(self):
        self.host.modprobe(CryptoTemplate.funcrypto)

    def verify_funcrypto(self):
        # check if funcrypto module is loaded
        fun_test.test_assert((self.host.lsmod(CryptoTemplate.funcrypto)), message="funcrypto loaded")
        return True

    def parse_input(self, file_path):
        plaintext_list = []
        digest_list = []
        input_dict = {}

        for line in open(file_path, 'r').read().split(','):
            line_list = line.split("=")
            if len(line_list) > 1:
                if ".plaintext" in line_list[0]:
                    plaintext_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())
                elif ".digest" in line_list[0]:
                    digest_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())

        for plain_text, digest in zip(plaintext_list, digest_list):
            input_dict[plain_text] = digest

        return input_dict

    def compute_digest(self, openssl_type, algorithm, digest_input, engine=None):
        return True

    def encrypt(self, algorithm, encrypt_input, key):
        return True

    def decrypt(self, algorithm, decrypt_input, key):
        return True