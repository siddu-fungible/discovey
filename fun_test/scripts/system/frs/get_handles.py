from asset.asset_manager import AssetManager
from lib.fun.fs import ComE, Bmc


def get_come_handle(fs_name):
    fs = AssetManager().get_fs_spec(fs_name)
    come_handle = ComE(host_ip=fs['come']['mgmt_ip'],
                       ssh_username=fs['come']['mgmt_ssh_username'],
                       ssh_password=fs['come']['mgmt_ssh_password'])
    come_handle.command("pwd")
    return come_handle


def get_bmc_handle(fs_name):
    fs = AssetManager().get_fs_spec(fs_name)
    bmc_handle = Bmc(host_ip=fs['bmc']['mgmt_ip'],
                     ssh_username=fs['bmc']['mgmt_ssh_username'],
                     ssh_password=fs['bmc']['mgmt_ssh_password'],
                     set_term_settings=True,
                     disable_uart_logger=False)
    bmc_handle.set_prompt_terminator(r'# $')
    bmc_handle.command("pwd")
    return bmc_handle