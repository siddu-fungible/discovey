from lib.system.fun_test import *
from lib.host.network_controller import NetworkController
import random, time
from helper import *

FPGs = [6, 8, 12, 18]
SPEEDs = ["brk_4x10g", "brk_4x25g", "brk_2x50g"]

nw_obj = NetworkController('10.1.21.120', 42221)

def run_speed_test():
    while True:
        need_break = False
        temp_speed = random.choice(SPEEDs)
        fun_test.log("Setting speed to %s" % temp_speed)
        nw_obj.set_fpg_speed(port_num=random.choice([8, 12]), brk_mode=temp_speed)
        for fpg in FPGs:
            clear_stats = nw_obj.clear_port_stats(port_num=int(fpg))
            fun_test.sleep("Sleeping 60 seconds", seconds=60)
            fun_test.log("Check psw stats")
            psw = nw_obj.peek_psw_global_stats()
            fun_test.log("Check stats on %s" % fpg)
            dut_1 = nw_obj.peek_fpg_port_stats(fpg)
            dut_port_2_transmit = get_dut_output_stats_value(dut_1, FRAMES_TRANSMITTED_OK)
            fun_test.log("Transmit value for fpg %s is %s " % (fpg, dut_port_2_transmit))
            if dut_port_2_transmit is None:
                need_break = True
                break
        if need_break:
            break

if __name__ == "__main__":
    run_speed_test()