from lib.system.board_helper import board_helper
## -----------------------------------------------------
B = board_helper("fs-174")
B.bmc_test(0)
# B.power_cycle() ## power cycle the power plug of the board
B.power_cycle( 8 ) # unused port 8 of fs-174 (is off, used for testing)
B.power_on( 8 )
B.power_cycle( 8 )
B.power_off( 8 )



