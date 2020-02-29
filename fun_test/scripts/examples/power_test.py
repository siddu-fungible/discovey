from lib.utilities.board_helper import board_helper
## -----------------------------------------------------
A = board_helper("fs-174") ## given board name or FS spec
SPEC = A.find_asset("fs-174")
B = board_helper(SPEC)
B.bmc_test(0)
# B.power_cycle() ## power cycle the power plug of the board
B.power_cycle( 8 ) # unused port 8 of fs-174 (is off, used for testing)
B.power_on( 8 )
B.power_cycle( 8 )
B.power_off( 8 )



