set STC_LIB_PATH [info script]

set STC_LIB_PATH [file dirname $STC_LIB_PATH]
set STC_LIB_PATH [file join $STC_LIB_PATH stclib]

source [file join $STC_LIB_PATH gdbg.tcl]
source [file join $STC_LIB_PATH gtrace.tcl]
source [file join $STC_LIB_PATH bw.tcl]
source [file join $STC_LIB_PATH bll.tcl]


package provide stclib 4.81
