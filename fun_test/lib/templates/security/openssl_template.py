from lib.system.fun_test import fun_test
import re
from lib.templates.security.crypto_template import CryptoTemplate


class OpenSslTemplate(CryptoTemplate):

    def __init__(self, host):
        self.host = host

    def setup(self):
        crypto_template = CryptoTemplate(self.host)
        crypto_template.load_funcrypto()
        crypto_template.verify_openssl_version()
        crypto_template.verify_funcrypto()
        return True

    def compute_digest(self, openssl_type, algorithm, digest_input, engine=None):
        #openssl_command = CryptoTemplate.openssl + " " + openssl_type + +" -"+ CryptoTemplate.engine + " " + CryptoTemplate.af_alg + " -" ++ algorithm + " " + digest_input
        openssl_command = CryptoTemplate.openssl + " " + openssl_type + " -" + algorithm + " " + digest_input
        digest_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return digest_output

    def get_error_logs(self):
        print "error logs"
