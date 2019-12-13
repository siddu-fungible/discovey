from fun_settings import LOGS_DIR
import glob
import re

class Entry:
    def __init__(self, uart_log_file_path, found_string):
        self.uart_log_file_path = uart_log_file_path
        self.fs = "unknown"
        m = re.search("fs-(\d+)", self.uart_log_file_path)
        if m:
            self.fs = "FS-{}".format(m.group(1))
        self.found_string = found_string

    def __str__(self):
        return "{}: {}: {}".format(self.fs, self.found_string, self.uart_log_file_path)

suite_directory_paths = glob.glob(LOGS_DIR + "/s_*")
entries = []
for suite_directory_path in suite_directory_paths:
    uart_log_files = glob.glob(suite_directory_path + "/*uart*txt")
    for uart_log_file in uart_log_files:
        fp = open(uart_log_file, "r")
        if fp:
            contents = fp.read()
            m2 = re.search(r'CSR:MUH_MCI_NON_FATAL_INTR_STAT|CSR:FEP_.*_FATAL_INTR ', contents)
            if m2:
                entries.append(Entry(uart_log_file_path=uart_log_file, found_string=m.group(0)))


for entry in entries:
    print str(entry)