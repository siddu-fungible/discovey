from lib.host.linux import *


def verify_host_pcie_link(hostname, username="localadmin", password="Precious1*", mode="x8"):
    linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
    lspci_out = linux_obj.lspci(grep_filter="LnkSta", verbose=True, device="1dad:")
    sections = ['LnkSta', 'Speed', 'Width', 'EqualizationComplete']
    for section in sections:
        fun_test.test_assert(section in lspci_out, "{} seen".format(section))
    if mode not in sections:
        fun_test.critical("PCIE link did not come up in %s mode" % mode)
