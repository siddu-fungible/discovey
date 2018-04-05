#
# util.tcl --
#
#   Miscellaneous TCL utilities.
#
# Copyright (c) 2006 by Spirent Communications, Inc.
# All Rights Reserved
#
# By accessing or executing this software, you agree to be bound 
# by the terms of this agreement.
# 
# Redistribution and use of this software in source and binary
# forms, with or without modification, are permitted provided
# that the following conditions are met: 
#
#   1. Redistribution of source code must contain the above 
#	   copyright notice, this list of conditions, and the
#	   following disclaimer.
#
#   2. Redistribution in binary form must reproduce the above
#	   copyright notice, this list of conditions and the
#	   following disclaimer in the documentation and/or other
#	   materials provided with the distribution.
#
#   3. Neither the name Spirent Communications nor the names of 
#	   its contributors may be used to endorse or promote 
#      products derived from this software without specific 
#      prior written permission.
#
# This software is provided by the copyright holders and
# contributors [as is] and any express or implied warranties, 
# limited to, the implied warranties of merchantability and 
# fitness for a particular purpose are disclaimed.  In no event 
# shall Spirent Communications, Inc. or its contributors be 
# liable for any direct, indirect, incidental, special, 
# exemplary, or consequential damages  (including, but not 
# limited to: procurement of substitute goods or services; loss 
# of use, data, or profits; or business interruption) however 
# caused and on any theory of liability, whether in contract, 
# strict liability, or tort (including negligence or otherwise) 
# arising in any way out of the use of this software, even if 
# advised of the possibility of such damage.
#

namespace eval ::stclib::util {}

#
# sleep --
#
#   Delay execution without stalling the event loop. This is especially useful for
#   Tk applications, as it allows the user interface to remain responsive while
#   the logic is pausing.
#
# Arguments:
#
#   seconds The length of the pause.
#
# Results:
#
#   Returns only after the specified interval has elapsed.
#
# Issues:
#
#   An invalid prameter will be reported by the embedded expr command, not by
#   the proc itself. Probably not worth fixing.
#
# History:
#
#   This functionality exists in the ::stc:: API, but is being deprecated, as
#   it does not actually interact with the hardware. Make it available here
#   as an alternative.
#
#   2006-08-23 John Morris - initial version. Modified from ::stc:: original
#   to use a namespace variable instaead of a global.

proc ::stclib::util::sleep {seconds} {
	variable sleepFlag 0
	after [expr {$seconds * 1000}] [namespace code [list set sleepFlag 1]]
	vwait [namespace current]::sleepFlag 
}

#####################################################################

package provide stclib::util 0.0.1
