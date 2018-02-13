from lib.system.fun_test import fun_test
import re
from lib.templates.security.crypto_template import CryptoTemplate


class OpenSslTemplate(CryptoTemplate):

    def __init__(self, host):
        self.host = host

    def setup_verify(self):
        # validate existence of OpenSSL
        version_output = (self.host.command(CryptoTemplate.openssl+" "+CryptoTemplate.version)).split(" ")
        fun_test.debug("OpenSSL version output: {}".format(version_output))
        version = version_output[1]
        fun_test.test_assert_expected(expected=CryptoTemplate.openssl_version,
                                      actual=version,
                                      message="OpenSSL version as expected")

        # Insert and check if funcrypto module is loaded
        self.host.modprobe(CryptoTemplate.funcrypto)
        lsmod_output_dict = self.host.lsmod(CryptoTemplate.funcrypto)
        fun_test.test_assert((lsmod_output_dict["size"] > 10000), message="funcrypto size as expected")

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
        openssl_command = CryptoTemplate.openssl + " " + openssl_type + " -" + algorithm + " " + digest_input
        digest_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return digest_output

    def get_error_logs(self):
        print "error logs"
