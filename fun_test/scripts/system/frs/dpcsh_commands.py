import dpcsh_nocli
import get_handles


def debug_memory(come_handle, f1=0):
    cmd = "debug memory"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    print(dpcsh_output)
    return dpcsh_output


def ddr(come_handle, f1=0):
    cmd = "peek stats/ddr"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


def hbm(come_handle, f1=0):
    cmd = "peek stats/hbm"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


def cdu(come_handle, f1=0):
    cmd = "peek stats/cdu"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


def eqm(come_handle, f1=0):
    cmd = "peek stats/eqm"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


def bam(come_handle, f1=0):
    cmd = "peek stats/resource/bam"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


def debug_vp_utils(come_handle, f1=0):
    cmd = "debug vp_util"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


def le(come_handle, f1=0):
    cmd = "peek stats/le/counters"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1)
    # print dpcsh_output
    return dpcsh_output


if __name__ == "__main__":
    come_handle = get_handles.get_come_handle("fs-65")
    output = ddr(come_handle, f1=0)
