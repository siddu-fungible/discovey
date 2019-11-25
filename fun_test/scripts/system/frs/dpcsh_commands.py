import dpcsh_nocli


def debug_memory(come_handle, f1=0):
    cmd = "debug memory"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    print(dpcsh_output)
    return dpcsh_output


def ddr(come_handle, f1=0):
    cmd = "peek stats/ddr"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def hbm(come_handle, f1=0):
    cmd = "peek stats/hbm"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def cdu(come_handle, f1=0):
    cmd = "peek stats/cdu"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def eqm(come_handle, f1=0):
    cmd = "peek stats/eqm"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def bam(come_handle, f1=0):
    cmd = "peek stats/resource/bam"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def debug_vp_utils(come_handle, f1=0):
    cmd = "debug vp_util"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def le(come_handle, f1=0):
    cmd = "peek stats/le/counters"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def execute_leaks(come_handle, f1=0):
    cmd = "execute leaks"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def pc_dma(come_handle, f1=0):
    cmd = "peek stats/pc_dma"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def busy_loop(come_handle, f1=0):
    cmd = "async soak_flows_busy_loop_10usecs"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def memcpy_1MB(come_handle, f1=0):
    cmd = "async soak_flows_memcpy_1MB_non_coh"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output


def storage_iops(come_handle, f1=0):
    cmd = "peek storage/devices/nvme/ssds"
    dpcsh_output = dpcsh_nocli.get_dpcsh_output(come_handle, cmd, f1, env_set=True)
    # print dpcsh_output
    return dpcsh_output
