from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate

#TOOLS_PATH = "/bin"

class Sha3Template(CryptoTemplate):

    # variables
    sha3_digests = ["sha3-224-generic", "sha3-256-generic", "sha3-384-generic", "sha3-512-generic"]

    def __init__(self, host):
        self.host = host

    def setup_verify(self):
        tool_path = fun_test.get_script_parent_directory() + CryptoTemplate.TOOLS_PATH + CryptoTemplate.DIGEST_HMAC_SHA3
        fun_test.scp(source_file_path=tool_path,
                     target_file_path="/tmp/",
                     target_ip=self.host.host_ip,
                     target_port=self.host.ssh_port,
                     target_username=self.host.ssh_username,
                     target_password=self.host.ssh_password,
                     recursive=False)
        CryptoTemplate.copy_tools(self)
        CryptoTemplate.load_funcrypto(self)
        CryptoTemplate.verify_funcrypto(self)

    def parse_input_sha3(self, file_path):
        plaintext_list = []
        digest_list = []
        input_dict = {}
        key_list = []
        key_type_list = []
        print "file: ", file_path
        for line in open(file_path, 'r').read().split(','):
            line_list = line.split("=")
            if len(line_list) > 1:
                if ".plaintext" in line_list[0]:
                    plaintext_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())
                elif ".digest" in line_list[0]:
                    digest_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())
                elif ".key" in line_list[0]:
                    if (line_list[1].find("\\x") == -1):
                        key_type_list.append("key_text_imm")
                    else:
                        key_type_list.append("key_hex_esc_imm")
                    key_list.append((line_list[1].replace('"', '').replace('\\x', '').replace('\n', '')).strip())
        for plain_text, digest in zip(plaintext_list, digest_list):
            input_dict[plain_text] = digest
        if (file_path.find("hmac") == -1):
            return input_dict
        else:
            zipped = zip(plaintext_list, digest_list, key_list, key_type_list)
            return zipped



    def compute_digest(self, algorithm, digest_input, engine=None):
        digest_sha3_command = "/tmp/" + CryptoTemplate.DIGEST_HMAC_SHA3 + " " + algorithm + " " + digest_input
        digest_output = ((self.host.command(digest_sha3_command)).strip())
        return digest_output

    def compute_hmac(self, algorithm, digest_input, keytype=None, key=None, engine=None):
        hmac_sha3_command = "/tmp/" + CryptoTemplate.DIGEST_HMAC_SHA3 + " " + algorithm + " " + \
                            digest_input + " " + keytype + " " + key
        hmac_output = ((self.host.command(hmac_sha3_command)).strip())
        return hmac_output

    def get_error_logs(self):
        print "error logs"
