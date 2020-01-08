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
entry_count = 0
for suite_directory_path in suite_directory_paths:
    entry_count += 1

    uart_log_files = glob.glob(suite_directory_path + "/*uart*txt")
    for uart_log_file in uart_log_files:
        fp = open(uart_log_file, "r")
        if fp:
            contents = fp.read()
            m2 = re.search(r'i2c write: final NACK check failure|i2c write error|fpc_i2c_read err', contents)
            if m2:
                new_entry = Entry(uart_log_file_path=uart_log_file, found_string=m2.group(0))
                entries.append(new_entry)
                print str(new_entry)

print "Searched count: {}".format(entry_count)
print "All entries"
for entry in entries:
    print str(entry)