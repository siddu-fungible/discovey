from lib.templates.security.crypto_template import CryptoTemplate


class XtsOpenssl(CryptoTemplate):

    ssl_path = "/tmp/xts_ssl/openssl-1.0.1e/apps/openssl"

    def install_ssl(self):
        self.host.command("wget https://ftp.openssl.org/source/old/1.0.1/openssl-1.0.1e.tar.gz -P /tmp/xts_ssl",
                          timeout=80)
        self.host.command("cd /tmp/xts_ssl && tar xf openssl-1.0.1e.tar.gz", timeout=80)
        self.host.command("cd /tmp/xts_ssl/openssl-1.0.1e && ./config &> /dev/null && make &> /dev/null && cd",
                          timeout=180)
        check_ssl = self.host.command("ls /tmp/xts_ssl/openssl-1.0.1e/apps/openssl")
        if "cannot access" in check_ssl:
            return False
        else:
            return True

    def compute_cipher(self, key, iv, input_file, output_file, encrypt=True):
        key_len = len(key)
        if key_len == 64:
            cipher = " -aes-128-xts "
        elif key_len == 96:
            cipher = " -aes-192-xts "
        elif key_len == 128:
            cipher = " -aes-256-xts "
        if encrypt:
            cmd_str = self.ssl_path + " enc " + cipher + " -in " + input_file + " -out " + output_file + " -e " + \
                      " -K " + key + " -iv " + iv
        else:
            cmd_str = self.ssl_path + " enc " + cipher + " -in " + input_file + " -out " + output_file + " -d " + \
                      " -K " + key + " -iv " + iv
        cmd_result = self.host.command(cmd_str)
        if "error" in cmd_result:
            return False
        else:
            return True
