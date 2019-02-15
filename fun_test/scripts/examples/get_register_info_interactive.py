from scripts.examples.register_controller import RegisterController
import sys

rc = RegisterController(dpc_server_ip='10.1.40.22', dpc_server_port=40221, verbose=False)
while True:
    name = raw_input("\nRegister name: ")
    if name == "exit":
        sys.exit()
    rinst = raw_input("Rinst: ")
    field = raw_input("Field: ")

    rc.peek_register(register_name=name,rinst=rinst, field=field)
    enable_counter_execute = 0