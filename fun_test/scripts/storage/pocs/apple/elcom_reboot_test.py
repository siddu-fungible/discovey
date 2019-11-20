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

    def collect_bmc_logs(self):
        self.bmc_handle.set_prompt_terminator(r'# $')
        # Capture the UART logs also
        artifact_file_name_f1_0 = self.bmc_handle.get_uart_log_file(0, "Iteration_{}".format(self.pc_no))
        artifact_file_name_f1_1 = self.bmc_handle.get_uart_log_file(1, "Iteration_{}".format(self.pc_no))
        fun_test.add_auxillary_file(description="Iteration {}:  DUT_0_fs-65_F1_0 UART Log".format(self.pc_no), filename=artifact_file_name_f1_0)
        fun_test.add_auxillary_file(description="Iteration {}:  DUT_0_fs-65_F1_1 UART Log".format(self.pc_no), filename=artifact_file_name_f1_1)

    def data_integrity_check(self):
        pass

    def apc_pdu_reboot(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))
        fun_test.log("Checking if COMe is UP")
        come_up = come_handle.ensure_host_is_up()
        fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                self.to_str(come_up), True, come_up)
        come_handle.destroy()

        switch = ElcomPowerSwitch(self.apc_info['host_ip'], self.apc_info['username'], self.apc_info['password'])
        fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)
        outlet_off_msg = switch.off(str(self.outlet_no))
        fun_test.log("PDU outlet off mesg {}".format(outlet_off_msg))
        outlet_off = self.match_success(outlet_off_msg)
        fun_test.test_assert(outlet_off, "Power down FS")

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

        fun_test.log("Checking if COMe is down")
        come_down = not (come_handle.ensure_host_is_up(max_wait_time=15))
        fun_test.test_assert(come_down, "COMe is Down")
        come_handle.destroy()

        outlet_on_msg = switch.on(str(self.outlet_no))
        fun_test.log("APC PDU outlet on message {}".format(outlet_on_msg))
        outlet_on = self.match_success(outlet_on_msg)
        fun_test.test_assert(outlet_on, "Power on FS")
        switch.close()
        come_handle.destroy()
        come_handle.destroy()
        return




    def cleanup(self):
        pass

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