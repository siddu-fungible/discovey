from lib.system.fun_test import *
from lib.templates.system.sbp_challenge_template import SbpChallengeTemplate

BOARD_IP = "10.1.23.106"
PROBE_IP = "10.1.23.108"
PROBE_NAME = "sp218"


if __name__ == "__main__":
    sbp_challenge_template = SbpChallengeTemplate(board_ip=BOARD_IP, probe_ip=PROBE_IP, probe_name=PROBE_NAME)
    sbp_challenge_template.setup_board()
    sbp_challenge_template.test()