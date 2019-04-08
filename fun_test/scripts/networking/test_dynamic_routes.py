from lib.system.fun_test import *
from lib.host.linux import *
from helper import *

from lib.host.network_controller import NetworkController
start_counter = 0
end_counter = 15
sleep_time = 120

json_file = "dynamic_routes.json"
file_path = fun_test.get_script_parent_directory() + "/" + json_file
output = fun_test.parse_file_to_json(file_path)
docker_host = output['docker_host']
docker_user = output['docker_user']
docker_password = output['docker_password']
ifname = output['ifname']
mac_address = output['mac_address']
ip_address = output['ip_address']
dpcsh_machine_ip = output['dpc_cli_machine_ip']
dpcsh_port = output['dpc_cli_port']
custom_prompt = {'prompt1': r'$ '}
fcp_csr_monitor_script_path = "FunControlPlane/scripts/palladium_test/csr_monitor.py"


def start_csr_monitor(ssh_handle, dpc_cli_machine_ip):
    process_id = None
    try:
        workspace = ssh_handle.command("env | grep 'WORKSPACE'")
        if workspace:
            workspace_path = workspace.split('=')[1].strip()
            csr_monitor_script_path = str(workspace_path) + '/' + str(fcp_csr_monitor_script_path)
            fun_test.log("csr monitor script is %s" % csr_monitor_script_path)
            process_id = ssh_handle.start_bg_process(nohup=False, command="python %s -H %s" % (csr_monitor_script_path, dpc_cli_machine_ip))
    except Exception as ex:
        fun_test.critical(str(ex))
    return process_id


def get_fpg_stats():
    stats_output = None
    try:
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_machine_ip, dpc_server_port=dpcsh_port)
        fun_test.log("Clear stats on port %s" % ifname)
        clear_stats_output = network_controller_obj.clear_port_stats(port_num=int(ifname))
        fun_test.simple_assert(clear_stats_output, "stats cleared")
        stats_output = network_controller_obj.peek_fpg_port_stats(port_num=int(ifname))
        fun_test.log("Disconnecting from dpcsh")
        network_controller_obj.disconnect()
    except Exception as ex:
        fun_test.critical(str(ex))
    return stats_output


add_cmd = ["curl -s -k -H 'Content-Type: application/json' -X POST http://127.0.0.1:8000/v1/cfg/FIBNH/300 -d '{\"nhip\": \"200.1.0.5\", \"mac\": \"%s\", \"ifname\": \"fpg%s\"}'" % (mac_address, ifname),
"curl -s -k -H 'Content-Type: application/json' -X POST http://127.0.0.1:8000/v1/cfg/FIBPREFIX/600 -d '{\"vrfid\": 1, \"pfx\": \"%s/32\", \"outgoingnh\": 300}'" % ip_address]

del_cmd = ["curl -s -k -X DELETE http://127.0.0.1:8000/v1/delete/FIBPREFIX/600",
"curl -s -k -X DELETE http://127.0.0.1:8000/v1/delete/FIBNH/300"]

ssh_obj_1 = None
ssh_obj_2 = None
ssh_obj_1 = Linux(docker_host,ssh_username=docker_user, ssh_password=docker_password)
out = ssh_obj_1.command("docker exec -it frr-img bash")

while start_counter <= end_counter:
    start_counter += 1

    fun_test.log("Starting csr monitor for adding routes")
    ssh_obj_2 = Linux(docker_host, ssh_username=docker_user, ssh_password=docker_password)
    pid = start_csr_monitor(ssh_handle=ssh_obj_2, dpc_cli_machine_ip=dpcsh_machine_ip)
    fun_test.simple_assert(pid, "csr_monitor script started in background")

    for cmd in add_cmd:
        ssh_obj_1.command(cmd, custom_prompts=custom_prompt)
        fun_test.sleep("sleeping 1 sec", seconds=1)

    fun_test.log("Added rules")
    fun_test.sleep("After adding rules", seconds=sleep_time)

    fun_test.log("Killing csr monitor to get fpg mac stats")
    ssh_obj_2.kill_process(process_id=pid)
    ssh_obj_2.disconnect()
    stats_1 = get_fpg_stats()
    dut_port_transmit = get_dut_output_stats_value(stats_1, FRAMES_TRANSMITTED_OK)
    fun_test.test_assert(dut_port_transmit, message="Tx stats seen on fpg %s after adding routes" % ifname)

    fun_test.log("Starting csr monitor for deleting routes")
    ssh_obj_2 = Linux(docker_host, ssh_username=docker_user, ssh_password=docker_password)
    pid = start_csr_monitor(ssh_handle=ssh_obj_2, dpc_cli_machine_ip=dpcsh_machine_ip)
    fun_test.simple_assert(pid, "csr_monitor script started in background")

    for cmd in del_cmd:
        ssh_obj_1.command(cmd, custom_prompts=custom_prompt)
        fun_test.sleep("Sleeping 1 sec for curl call", seconds=1)

    fun_test.log("Delete rules")
    fun_test.sleep("After rules are deleted", seconds=sleep_time)

    fun_test.log("Killing csr monitor to get fpg mac stats")
    ssh_obj_2.kill_process(process_id=pid)
    stats_2 = get_fpg_stats()
    dut_port_transmit = get_dut_output_stats_value(stats_2, FRAMES_TRANSMITTED_OK)
    fun_test.test_assert(not dut_port_transmit, message="Tx stats are not seen on fpg %s after deleting routes" % ifname)

fun_test.log("Script execution done")