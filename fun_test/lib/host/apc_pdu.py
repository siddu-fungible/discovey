from lib.system.fun_test import fun_test
import telnetlib
import re


class ApcPdu():
    PROMPT = "apc>"

    def __init__(self, host_ip, username, password, port=23, context=None, **kwargs):
        self.host_ip = host_ip
        self.username = str(username)
        self.password = str(password)
        self.logged_in = None
        self.port = int(port)
        self.handle = None
        self.context = context
        self.outlet_number = None
        if "outlet_number" in kwargs:
            self.outlet_number = kwargs.get("outlet_number", None)

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
        if not outlet_number:
            outlet_number = self.outlet_number
        result = None
        try:
            self.outlet_off(outlet_number=outlet_number)
        except Exception as ex:
            fun_test.critical(message=str(ex), context=self.context)
        fun_test.sleep("After APC off")
        try:
            self.outlet_on(outlet_number=outlet_number)
        except Exception as ex:
            fun_test.critical(message=str(ex), context=self.context)
        fun_test.sleep("After APC on")

        status = self.outlet_status(outlet_number=outlet_number)
        if re.search(r'Outlet\s+' + str(outlet_number) + r'.*On', status):
            result = True
        return result

if __name__ == "__main__":
    import json
    d = {"host_ip":"cab04-pdu1", "username": "localadmin", "password":"Precious1*"}
    a = ApcPdu(**json.loads(json.dumps(d)))
    a.outlet_status("7")
    a.power_cycle(7)
    a.outlet_status("7")