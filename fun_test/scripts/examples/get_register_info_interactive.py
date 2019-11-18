from scripts.examples.register_controller import RegisterController
import sys

rc = RegisterController(dpc_server_ip='10.1.40.22', dpc_server_port=42221, verbose=False)
while True:
    inst = None
    index = None
    name = raw_input("\nRegister name: ") or None
    if name == "exit":
        sys.exit()
    rinst = raw_input("Rinst: ") or None
    field = raw_input("Field: ") or None
    if name == rc.hsu_pwp_core0_csr_apb or name == 'hsu_pwp_core0_csr_pmlut':
        inst = raw_input("inst: ") or None
        index = raw_input("index: ") or None

    rc.peek_register(register_name=name,rinst=rinst, field=field, inst=inst, index=index)