from scripts.examples.register_controller import RegisterController

rc = RegisterController(dpc_server_ip='10.1.40.22', dpc_server_port=42221, verbose=False)
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_test_in, rinst=0, field="test_in")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_tl_pm_event0, rinst=0, field="tl_pm_event")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_tl_pm_event1, rinst=0, field="tl_pm_event")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_tl_pm_event2, rinst=0, field="tl_pm_event")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_tl_pm_event3, rinst=0, field="tl_pm_event")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_l1ss_sup")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_asl11_sup")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_asl12_sup")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_pml11_sup")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_pml12_sup")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_link_aspml1")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_k_pexconf, rinst=0, field="kpexconf_link_aspml0s")
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_test_outl, rinst=0, field="csr_test_outl")

# rinst is 0 and inst is 0-3
rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=0, inst=0, index=63)
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=0, inst=1, index=63)
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=0, inst=2, index=63)
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=0, inst=3, index=63)

# rinst is 3 and inst is 0-3
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=3, inst=0, index=63)
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=3, inst=1, index=63)
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=3, inst=2, index=63)
#rc.peek_register(register_name=rc.hsu_pwp_core0_csr_apb, rinst=3, inst=3, index=63)
