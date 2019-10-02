import re
from lib.system.fun_test import *


def docker_ps_a(output):
    # Just a basic function , will have to advance it using regex
    lines = output.split("\n")
    lines.pop(0)
    number_of_dockers = len(lines)
    print ("number_of_dockers: %s"%number_of_dockers)
    return number_of_dockers


def docker_get_num_dockers(output):
    # The docker_ps_a needs to be advanced
    num_doc = docker_ps_a(output)
    return num_doc


def ensure_io_running(device, output_iostat, host_name):
    fio_read = False
    fio_write = False
    result = False
    lines = output_iostat.split("\n")

    # Remove the initial iostat values
    lines_clean = lines[8:]

    iostat_sum = [0, 0, 0, 0, 0]
    for line in lines_clean:
        match_nvme = re.search(r'{}'.format(device), line)
        if match_nvme:
            match_numbers = re.findall(r'(?<= )[\d.]+', line)
            if len(match_numbers) == 5:
                numbers = map(float, match_numbers)
                iostat_sum = [sum(x) for x in zip(numbers, iostat_sum)]

    # read
    fun_test.log("IOstat sum: {}".format(iostat_sum))
    if iostat_sum[1] > 20 :
        fio_read = True
    # fun_test.test_assert(fio_read, "{} reads are resumed".format(host_name))

    # write
    if iostat_sum[2] > 20:
        fio_write = True
    # fun_test.test_assert(fio_write, "{} writes are resumed".format(host_name))

    if fio_read or fio_write:
        result = True
    fun_test.test_assert(result, "{} IO is running".format(host_name))


if __name__ == "__main__":
    pass