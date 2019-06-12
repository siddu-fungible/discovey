from lib.system.fun_test import fun_test
import telnetlib
import re


class ApcPdu():
    PROMPT = "apc>"
    def __init__(self, host_ip, username, password, port=23, context=None):
        self.host_ip = host_ip
        self.username = username
        self.password = password
        self.logged_in = None
        self.port = port
        self.handle = None
        self.context = context

    def _login(self):
        if not self.handle:
            self._connect()
        output = self.handle.read_until("User Name :")
        fun_test.log(message=output, context=self.context, no_timestamp=True)
        self.handle.write(self.username + "\r\n")
        output = self.handle.read_until("Password  :")
        fun_test.log(message=output, context=self.context, no_timestamp=True)

        self.handle.write(self.password + "\r\n")
        output = self.handle.read_until(self.PROMPT)
        fun_test.log(message=output, context=self.context, no_timestamp=True)

        if self.PROMPT in output:
            self.logged_in = True
        else:
            raise Exception("Unable to login to APC using: {} {}".format(self.username, self.password))
        return True

    def _connect(self):
        if not self.handle:
            self.handle = telnetlib.Telnet(host=self.host_ip, port=self.port)

    def command(self, command):
        if not self.logged_in:
            self._login()
        self.handle.write(command + "\r\n")
        output = self.handle.read_until(self.PROMPT)
        fun_test.log(message=output, context=self.context, no_timestamp=True)
        return output

    def read_until(self, until_string):
        if not self.logged_in:
            self._login()
        output = self.handle.read_until(until_string)
        return output

    def disconnect(self):
        self.handle.close()

    def outlet_status(self, outlet_number):
        return self.command("olStatus {}".format(outlet_number))

    def outlet_on(self, outlet_number):
        return self.command("olOn {}".format(outlet_number))

    def outlet_off(self, outlet_number):
        return self.command("olOff {}".format(outlet_number))

    def power_cycle(self, outlet_number):
        result = None
        try:
            self.outlet_on(outlet_number=outlet_number)
        except Exception as ex:
            fun_test.critical(message=str(ex), context=self.context)
        try:
            self.outlet_off(outlet_number=outlet_number)
        except Exception as ex:
            fun_test.critical(message=str(ex), context=self.context)
        status = self.outlet_status(outlet_number=outlet_number)
        if re.search(r'Outlet\s+' + outlet_number + r'.*On', status):
            result = True
        return result