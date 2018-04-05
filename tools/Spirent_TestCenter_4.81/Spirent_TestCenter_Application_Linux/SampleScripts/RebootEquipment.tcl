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

# File Name:    RebootEquipment.tcl
# Description:  This script demonstrates how to reboot a chassis,
#               module or port group.


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


###########
# MAIN
###########

# Get command line args
if {$argc < 2} {
    puts "Usage: RebootEquipment.tcl \[-csp\] {chassis ip/hostname list} \[{slot index list}\] \[{port group index list}\]"
    puts "Ex(for chassis reboot): tclsh RebootEquipment.tcl -c 10.2.1.1"
    puts "Ex(for module reboot): tclsh RebootEquipment.tcl -s 10.2.1.1 \"1 2\""
    puts "Ex(for port group reboot): tclsh RebootEquipment.tcl -p 10.2.1.1 1 \"1 2\""
    return -1
}
set option [lindex $argv 0]

set szChassisIpList ""
set iTmList ""
set iPgList ""
switch -- $option \
    "-c" { set szChassisIpList [lindex $argv 1] } \
    "-s" { set szChassisIpList [lindex $argv 1]; set iTmList [lindex $argv 2] } \
    "-p" { set szChassisIpList [lindex $argv 1]; set iTmList [lindex $argv 2]; set iPgList [lindex $argv 3] } \
    default { puts "** ERROR ** Unknown option $option"; return } \

#package require SpirentTestCenter
source SpirentTestCenter.tcl

# Connect to each chassis
puts ""
foreach szChassisIp $szChassisIpList {
    puts "Connecting to chassis $szChassisIp..."
    stc::connect $szChassisIp
}
puts ""
set hChassisList [getChassis]

# Reboot the specified chassis
if { $option == "-c" } {
    # Reboot each chassis and wait for them to come back online
    puts "\nRebooting chassis..."
    stc::perform RebootEquipment -EquipmentList $hChassisList
    puts "Chassis reboot complete.\n"
}

# Reboot the specified module(s)
if { $option == "-s" } {
    # Locate module(s) in each chassis
    set rebootList {}
    foreach hChassis $hChassisList {
	set hTmList [getTestModules $hChassis]
	foreach hTm $hTmList {
	    set iSlot [stc::get $hTm -Index]

	    # Module not specified for reboot
	    if {[lsearch $iTmList $iSlot] < 0} {
		continue
	    }
	    
	    # Add to reboot list
	    puts "Adding module [stc::get $hChassis -Hostname]/$iSlot to the reboot list"
	    lappend rebootList $hTm
	}
    }

    # Reboot each module and wait for them to come back online
    puts "\nRebooting module(s)..."
    stc::perform RebootEquipment -EquipmentList $rebootList
    puts "Module reboot complete.\n"
}

# Reboot the specified port group(s)
if { $option == "-p" } {
    # Locate port group(s) in each chassis and module
    set rebootList {}
    foreach hChassis $hChassisList {
	set hTmList [getTestModules $hChassis]
	foreach hTm $hTmList {
	    set iSlot [stc::get $hTm -Index]
	    
	    # None of the module's port groups have been specified for reboot
	    if {[lsearch $iTmList $iSlot] < 0} {
		continue
	    }
	    
	    set hPgList [getPortGroups $hTm]
	    foreach hPg $hPgList {
		set iPgIndex [stc::get $hPg -Index]

		# Port group not specified for reboot
		if {[lsearch $iPgList $iSlot] < 0} {
		    continue
		}

		# Add to reboot list
		puts "Adding port group [stc::get $hChassis -Hostname]/$iSlot/$iPgIndex to the reboot list"
		lappend rebootList $hPg
	    }

	}
    }

    # Reboot each port group and wait for them to come back online
    puts "\nRebooting port group(s)..."
    stc::perform RebootEquipment -EquipmentList $rebootList
    puts "Port group reboot complete.\n"
}

puts "Disconnecting from chassis..."
stc::perform chassisDisconnectAll

puts "\nComplete."

