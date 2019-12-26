from apc_pdu_auto import *


class ElcomRebootTest(ApcPduTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Reboot test",
                              steps="""""")

    def setup(self):
        super(ElcomRebootTest, self).setup()

    def run(self):
        super(ElcomRebootTest, self).run()

    def basic_checks(self):
        super(ElcomRebootTest, self).basic_checks()
        self.collect_bmc_logs()
        self.collect_fpga_logs()

    def data_integrity_check(self):
        pass

    def check_nu_ports(self,
                       expected_ports_up=None,
                       f1=0):
        self.get_dpcsh_data_for_cmds("port enableall", f1)
        fun_test.sleep("Before issuing the command 2nd time", seconds=5)
        self.get_dpcsh_data_for_cmds("port enableall", f1)
        fun_test.sleep("Before checking port status", seconds=40)
        super(ElcomRebootTest, self).check_nu_ports(expected_ports_up, f1)

    def validate_link_status_out(self, link_status_out, expected_port_up, f1=0):
        result = True
        link_status = self.parse_link_status_out(link_status_out, f1=f1, iteration=self.pc_no + 1)
        if link_status:
            for port_type, ports_list in expected_port_up.iteritems():
                for each_port in ports_list:
                    port_details = self.get_dict_for_port(port_type, each_port, link_status)
                    if not (port_details["xcvr"] == "PRESENT" and port_details["SW"] == 1 and port_details["HW"] == 1):
                        result = False
                        break
                if not result:
                    break
        else:
            result = False
        return result

    def apc_pdu_reboot(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        elcom_info = self.fs.get("elcom_info")
        outlet_list = elcom_info.get("outlet_list")
        fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))
        fun_test.log("Checking if COMe is UP")
        come_up = come_handle.ensure_host_is_up()
        fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                self.to_str(come_up), True, come_up)
        come_handle.destroy()

        switch = ElcomPowerSwitch(elcom_info['host_ip'], elcom_info['username'], elcom_info['password'])
        fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)
        for outlet_no in outlet_list:
            outlet_off_msg = switch.off(str(outlet_no))
            fun_test.log("PDU outlet off message {} for outlet: {}".format(outlet_off_msg, outlet_no))
            outlet_off = self.match_success(outlet_off_msg)
            fun_test.test_assert(outlet_off, "Power down outlet: {}".format(outlet_no))

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

        fun_test.log("Checking if COMe is down")
        come_down = not (come_handle.ensure_host_is_up(max_wait_time=15))
        fun_test.test_assert(come_down, "COMe is Down")
        come_handle.destroy()

        for outlet_no in outlet_list:
            outlet_on_msg = switch.on(str(outlet_no))
            fun_test.log("APC PDU outlet on message {} outlet: {}".format(outlet_on_msg, outlet_no))
            outlet_on = self.match_success(outlet_on_msg)
            fun_test.test_assert(outlet_on, "Power on outlet: {}".format(outlet_no))
        switch.close()
        come_handle.destroy()
        come_handle.destroy()
        return

    def collect_bmc_logs(self):
        bmc_logs = {}
        bmc_logs_file_name = fun_test.get_test_case_artifact_file_name(
            post_fix_name="important_bmc_logs_iteration_{}.txt".format(self.pc_no + 1))
        fun_test.add_auxillary_file(description="BMC logs Iteration: {}".format(self.pc_no + 1),
                                    filename=bmc_logs_file_name)
        bmc_logs['lanplus_sdr_logs'] = self.lanplus_sdr()
        bmc_logs['lanplus_sensor_log'] = self.lanplus_sensor()
        bmc_logs['f1_power_log'] = self.f1_power()
        bmc_logs['var_logs'] = self.bmc_var_logs()
        bmc_logs['FS_Details'] = self.fs_details()
        self.add_logs_to_file(bmc_logs_file_name, bmc_logs)

    def collect_fpga_logs(self):
        self.fpga_handle = Fpga(host_ip=self.fs['fpga']['mgmt_ip'],
                                ssh_username=self.fs['fpga']['mgmt_ssh_username'],
                                ssh_password=self.fs['fpga']['mgmt_ssh_password'])
        fpga_logs = {}
        fpga_logs_file_name = fun_test.get_test_case_artifact_file_name(
            post_fix_name="important_fpga_logs_iteration_{}.txt".format(self.pc_no + 1))
        fun_test.add_auxillary_file(description="FPGA logs Iteration: {}".format(self.pc_no + 1),
                                    filename=fpga_logs_file_name)
        fpga_logs["BootUpLog.txt"] = self.boot_up_log_txt()
        fpga_logs["boot-up.log"] = self.boot_up_log()
        fpga_logs["messages"] = self.messages_log()
        self.add_logs_to_file(fpga_logs_file_name, fpga_logs)
        self.fpga_handle.destroy()

    def boot_up_log_txt(self):
        output = self.fpga_handle.command("cat /home/root/BootUpLog.txt")
        return output

    def boot_up_log(self):
        output = self.fpga_handle.command("cat /var/log/boot-up.log")
        return output

    def messages_log(self):
        output = self.fpga_handle.command("cat /var/log/messages")
        return output

    def add_logs_to_file(self, file_name, logs_dict):
        f = open(file_name, "a+")
        for log_name, data in  logs_dict.iteritems():
            f.write("\n\n"+"--"*10 + log_name + "--"*10 + "\n\n")
            f.write(data)
        f.close()

    def lanplus_sdr(self):
        output = self.bmc_handle.command("ipmitool -I lanplus -H 127.0.0.1 -U admin -P admin sdr")
        return output

    def lanplus_sensor(self):
        output = self.bmc_handle.command("ipmitool -I lanplus -H 127.0.0.1 -U admin -P admin sensor")
        return output

    def f1_power(self):
        output = self.bmc_handle.command("/mnt/sdmmc0p1/scripts/f1_power.sh")
        return output

    def fs_details(self):
        output = self.bmc_handle.command("/mnt/sdmmc0p1/scripts/FS_Detail.sh", timeout=300)
        return output

    def bmc_var_logs(self):
        result = ""
        var_logs_list = ["alert.log", "btmp", "debug.log", "err.log", "messages", "redis-server.log", "syslog", "wtmp",
                         "audit.log", "info.log", "notice.log", "slpd.log", "warning.log"]
        for var_log in var_logs_list:
            result += "\n\n" + "--"*10 + var_log + "--"*10 + "\n\n"
            output = self.bmc_handle.command("cat /var/log/{}".format(var_log))
            result += "\n\n{}".format(output)
        return result

    def collect_uart_logs(self):
        self.bmc_handle.set_prompt_terminator(r'# $')
        # Capture the UART logs also
        artifact_file_name_f1_0 = self.bmc_handle.get_uart_log_file(0, "Iteration_{}".format(self.pc_no + 1))
        artifact_file_name_f1_1 = self.bmc_handle.get_uart_log_file(1, "Iteration_{}".format(self.pc_no + 1))
        fun_test.add_auxillary_file(description="Iteration {}:  DUT_0_fs-65_F1_0 UART Log".format(self.pc_no + 1),
                                    filename=artifact_file_name_f1_0)
        fun_test.add_auxillary_file(description="Iteration {}:  DUT_0_fs-65_F1_1 UART Log".format(self.pc_no + 1),
                                    filename=artifact_file_name_f1_1)

    def collect_fun_os_logs(self):
        bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                         ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                         ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                         set_term_settings=True,
                         disable_uart_logger=False,
                         bundle_compatible=True)
        artifact_file_name_f1_0 = bmc_handle.get_uart_log_file(0)
        artifact_file_name_f1_1 = bmc_handle.get_uart_log_file(1)
        fun_test.add_auxillary_file(description="DUT_0_F1_0 UART Log", filename=artifact_file_name_f1_0)
        fun_test.add_auxillary_file(description="DUT_0_F1_1 UART Log", filename=artifact_file_name_f1_1)

    def cleanup(self):
        try:
            self.collect_fun_os_logs()
            self.collect_bmc_logs()
            self.collect_fpga_logs()
        except:
            fun_test.log("Unable to collect the logs")


class ElcomPowerSwitch:
    """
    ELCOM power outlet class
    """
    def __init__(self, hostname, userid, password):
        #Init Elcom Prompt
        self.prompt = "Elcom"
        #Connect to the PDU
        self.pducon = self.connect(hostname, userid, password)
        if self.pducon is None:
            print 'Connection to ELCOM PDU:%s Failed'%(hostname)
        else:
            print 'PDU Connection Success'

    def connect(self, ip, user, passwd):
        child = pexpect.spawn('telnet '+ip, timeout=500)
        child.expect('Username')
        child.sendline(user + "\r")
        child.expect('Password')
        child.sendline(passwd + "\r")
        child.expect(self.prompt)
        print "Login To ELCOM PDU succesfull"
        return child

    def switch(self, outlet, op):
        #Prepend a "0" in case it is not present
        if len(outlet) == 1:
            outlet= "0"+outlet
        else:
            if outlet.startswith("0") is False:
                outlet= "0"+outlet
        # It is assumed that now the prompt is at elcom CLI.
        # try:
        #     i = self.pducon.expect([self.prompt, pexpect.TIMEOUT])
        # except:
        #     print ('Did not Connect to PDU. Prompt not seen')
        #     print (self.pducon.before)
        # if i == 0:
        #We reach here and connection is still up
        if op == "off":
            cmd = "outlet " + outlet + " " + "0"
        if op == "on":
            cmd = "outlet " + outlet + " " + "1"
        # if i == 1:
        #     print 'Timeout at PDU Con Prompt'
        #     print self.pducon.before
        #     return
        #Execute command
        self.pducon.sendline(cmd + "\r")
        try:
            i = self.pducon.expect([self.prompt, pexpect.TIMEOUT])
        except:
            print 'Exception tryin outlet command'
            print self.pducon.before
            return
        #It seems that we have completed command.
        output =  self.pducon.before
        if output.rfind("OFF") >= 0:
            return 'Outlet OFF Success'
        if output.rfind("ON") >= 0:
            return 'Outlet ON Success'

    def off(self, outlet):
        """ Turn the outlet off """
        return self.switch(outlet, "off")

    def on(self, outlet):
        """ Turn the outlet on """
        return self.switch(outlet, "on")

    def close(self):
        """ Close connection """
        self.pducon.sendline("bye\r")
        self.pducon.expect("Connection closed")


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(ElcomRebootTest())
    obj.run()