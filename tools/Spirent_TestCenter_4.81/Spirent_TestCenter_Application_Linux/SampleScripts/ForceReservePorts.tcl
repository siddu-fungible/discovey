# Copyright (c) 2010 by Spirent Communications, Inc.
# All Rights Reserved
#
# By accessing or executing this software, you agree to be bound 
# by the terms of this agreement.
# 
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the 
# following conditions are met:
#   1.  Redistribution of source code must contain the above copyright 
#       notice, this list of conditions, and the following disclaimer.
#   2.  Redistribution in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer
#       in the documentation and/or other materials provided with the
#       distribution.
#   3.  Neither the name Spirent Communications nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# This software is provided by the copyright holders and contributors 
# [as is] and any express or implied warranties, including, but not 
# limited to, the implied warranties of merchantability and fitness for
# a particular purpose are disclaimed.  In no event shall Spirent
# Communications, Inc. or its contributors be liable for any direct, 
# indirect, incidental, special, exemplary, or consequential damages
# (including, but not limited to: procurement of substitute goods or
# services; loss of use, data, or profits; or business interruption)
# however caused and on any theory of liability, whether in contract, 
# strict liability, or tort (including negligence or otherwise) arising
# in any way out of the use of this software, even if advised of the
# possibility of such damage.

# File Name:    ForceReservePorts.tcl
# Description:  This script demonstrates how to reserve one or more
#               ports that are currently reserved by other user(s).


#################
# Utility Procs
#################

# Get chassis manager
proc getChassisManager {} {
    return [stc::get system1 -children-PhysicalChassisManager]
}

# Get list of chassis that STC is currently connected to
proc getChassis {} {
    set hMgr [getChassisManager]
    return [stc::get $hMgr -children-PhysicalChassis]
}

# Get list of test module(s) in a chassis
proc getTestModules {hChassis} {
    return [stc::get $hChassis -children-PhysicalTestmodule]
}

# Get list of port group(s) in a test module
proc getPortGroups {hTm} {
    return [stc::get $hTm -children-PhysicalPortgroup]
}

# Get list of ports in a port group
proc getPorts {hPg} {
    return [stc::get $hPg -children-PhysicalPort]
}


########
# Main
########

if {$argc != 3} {
    puts "Usage: ForceReservePorts.tcl {chassis ip/hostname list} {slot index list} {port index list}"
    puts "Ex: tclsh ForceReservePorts.tcl 10.2.1.1 \"1 2\" \"1 2 3 4\""
    return -1
}

#package require SpirentTestCenter
source SpirentTestCenter.tcl

# Get command line arguments
set szChassisIpList [lindex $argv 0]
set iSlotList [lindex $argv 1]
set iPortList [lindex $argv 2]

set cspList {}
foreach szChassisIp $szChassisIpList {
    # Connect to chassis
    puts "Connecting to chassis $szChassisIp...\n"
    stc::connect $szChassisIp
}

# Create a list of ports to reserve based upon the command line arguments
set hChassisList [getChassis]
foreach hChassis $hChassisList {
    set szChassisIp [stc::get $hChassis -Hostname]

    # Find ports matching slot and port indices provided from the command line
    set hTmList [getTestModules $hChassis]
    foreach hTm $hTmList {
	set iSlot [stc::get $hTm -Index]
	
	set hPgList [getPortGroups $hTm]
	foreach hPg $hPgList {
	    set hPortList [getPorts $hPg]
	    foreach hPort $hPortList {
		# Add to reserve list
		set iPort [stc::get $hPort -Index]
		if { ( [lsearch $iSlotList $iSlot] != -1 )\
			 && ( [lsearch $iPortList $iPort] != -1 ) } {
		    set csp "$szChassisIp/$iSlot/$iPort"
		    # Kick off current owner
		    array set pgProps [stc::get $hPg]
		    if {$pgProps(-OwnershipState) == "OWNERSHIP_STATE_RESERVED"} {
			puts "Kicking off owner $pgProps(-OwnerUserId)@$pgProps(-OwnerHostname) from port $csp..."
		    } else {
			puts "Port $csp is currently not reserved.  Adding to reserve list..."
		    }
		    lappend cspList $csp
		}   
	    }
	}
    }
}

# Reserve ports(kick off current owners if required)
puts "\nKicking off current owner(s) and reserving ports..."
stc::perform ReservePort -Location $cspList -RevokeOwner TRUE

# Release ports
puts "\nReleasing ports..."
stc::release $cspList

# Disconnect from each chassis
foreach szChassisIp $szChassisIpList {
    puts "\nDisconnecting from chassis $szChassisIp...\n"
    stc::disconnect $szChassisIp
}

puts "Complete."

