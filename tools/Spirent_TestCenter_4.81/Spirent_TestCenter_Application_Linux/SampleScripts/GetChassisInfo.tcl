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

# File Name:    GetChassisInfo.tcl
# Description:  This script demonstrates how to query basic information
#               about a chassis and the test module(s) that reside in it.


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

# Display basic info about a chassis
proc displayChassisInfo {hChassis} {
    set szChassisIp [stc::get $hChassis -Hostname]
    array set chassisProps [stc::get $hChassis]
    puts "\nDisplaying info for chassis $szChassisIp...\n"
    puts "Part number: $chassisProps(-PartNum)"
    puts "Serial number: $chassisProps(-SerialNum)"
    puts "Firmware version: $chassisProps(-FirmwareVersion)"
    puts "Controller version: $chassisProps(-ControllerHwVersion)"
    puts "Number of slots: $chassisProps(-SlotCount)"
    puts "Sync status: $chassisProps(-SyncStatus)"
    puts "Sync source: $chassisProps(-SyncSrc)"

    displayChassisTopologyInfo $hChassis
    displayChassisTempInfo $hChassis
    displayChassisPowerSupplyInfo $hChassis
    displayChassisFanInfo $hChassis

    # Display info for each test module
    displayTestModuleInfo $hChassis
}

# Display sync topology for a chassis
proc displayChassisTopologyInfo {hChassis} {
    set szChassisIp [stc::get $hChassis -Hostname]
    set hTopList [stc::get $hChassis -children-PhysicalChassisSyncTopology]
    set iTopSize [llength $hTopList]

    # Not connected to any other chassis
    if {!$iTopSize} {
	return
    }

    puts "\nTopology... \n"
    for {set i 0} {$i < $iTopSize} {incr i} {
	array set topProps [stc::get [lindex $hTopList $i]]

	# Determine which address type to display
	set szAddr ""
	if {$topProps(-Hostname) != ""} {
	    set szAddr $topProps(-Hostname)
	} elseif {$topProps(-Ipv6Addr) != ""\
		  && $topProps(-Ipv6Addr) != "::"} {
	    set szAddr $topProps(-Ipv6Addr)
	} else {
	    set szAddr $topProps(-Ipv4Addr)
	}

	puts "Chassis $szAddr relationship is $topProps(-Relation)"
    }
}

# Display temperature sensor info for a chassis
proc displayChassisTempInfo {hChassis} {
    set szChassisIp [stc::get $hChassis -Hostname]
    set hTemp [stc::get $hChassis -children-PhysicalChassisTempStatus]
    array set tempProps [stc::get $hTemp]

    puts "\nTemperature sensor info...\n"

    for {set i 0} {$i < [llength $tempProps(-SensorList)]} {incr i} {
	set szName [lindex $tempProps(-SensorList) $i]
	set iTemp [lindex $tempProps(-SensorTempList) $i]
	set szStatus [lindex $tempProps(-SensorStatusList) $i]
	puts "\"$szName\" sensor temperature is $iTemp\(Celsius\), status is $szStatus"
    }
}

# Display power supply info for a chassis
proc displayChassisPowerSupplyInfo {hChassis} {
    set szChassisIp [stc::get $hChassis -Hostname]
    set hPower [stc::get $hChassis -children-PhysicalChassisPowerSupplyStatus]
    array set powerProps [stc::get $hPower]

    puts "\nPower supply info...\n"

    for {set i 0} {$i < [llength $powerProps(-PowerSupplyList)]} {incr i} {
	set szName [lindex $powerProps(-PowerSupplyList) $i]
	set iVoltage [lindex $powerProps(-PowerSupplyVoltageList) $i]
	set iCurrent [lindex $powerProps(-PowerSupplyCurrentList) $i]
	set iStatus [lindex $powerProps(-PowerSupplyStatusList) $i]
	puts "\"$szName\" power supply voltage is $iVoltage\(volts\), current is $iCurrent\(amps\), status is $iStatus"
    }
}

# Display fan info for a chassis
proc displayChassisFanInfo {hChassis} {
    set szChassisIp [stc::get $hChassis -Hostname]
    set hFanList [stc::get $hChassis -children-PhysicalChassisFan]

    puts "\nFan info...\n"

    foreach hFan $hFanList {
	array set fanProps [stc::get $hFan]
	puts "\"$fanProps(-FanName)\" fan status is $fanProps(-FanState)"
    }
}

# Display info about test module(s) in a chassis
proc displayTestModuleInfo {hChassis} {
    set szChassisIp [stc::get $hChassis -Hostname]

    # Display info for each test module
    set hTmList [getTestModules $hChassis]
    foreach hTm $hTmList {
	array set tmProps [stc::get $hTm]

	# Empty slot
	if {$tmProps(-PartNum) == ""} {
	    continue
	}

	puts "\n\tTest module $szChassisIp/$tmProps(-Index)...\n"
	puts "\tPart number: $tmProps(-PartNum)"
	puts "\tDescription: $tmProps(-Description)"
	puts "\tProduct id: $tmProps(-ProductId)"
	puts "\tSerial number: $tmProps(-SerialNum)"
	puts "\tFirmware version: $tmProps(-FirmwareVersion)"
	puts "\tPort count: $tmProps(-PortCount)"
	puts "\tPort group count: $tmProps(-PortGroupCount)"
	puts "\tStatus: $tmProps(-Status)"
	puts "\tStatus change: $tmProps(-StatusChanged)"
	puts "\tSync status: $tmProps(-SyncStatus)"
	puts -nonewline "\tSupported test package(s):"
	foreach sztestPkg $tmProps(-TestPackages) {
	    puts -nonewline " $sztestPkg"
	}
	puts ""

	set hPgList [getPortGroups $hTm]
	foreach hPg $hPgList {
	    array set pgProps [stc::get $hPg]
	    puts "\n\t\tPort group $szChassisIp/$tmProps(-Index)/$pgProps(-Index)...\n"
	    puts "\t\tTest package: $pgProps(-TestPackage)"
	    puts "\t\tTest package version: $pgProps(-TestPackageVersion)"
	    puts "\t\tStatus: $pgProps(-Status)"
	    puts "\t\tStatus change: $pgProps(-StatusChanged)"
	    puts "\t\tSync Status: $pgProps(-SyncStatus)"
	    
	    # Display ownership status
	    set status $pgProps(-OwnershipState)
	    if {$pgProps(-OwnershipState) == "OWNERSHIP_STATE_RESERVED"} {
		set status "Reserved by $pgProps(-OwnerUserId)@$pgProps(-OwnerHostname)"
	    }
	    puts "\t\tOwnership status: $status" 

	    # Display port(s)
	    puts ""
	    set hPortList [getPorts $hPg]
	    foreach hPort $hPortList {
		array set portProps [stc::get $hPort]
		puts "\t\t\tPort $portProps(-Location)"

	    }
	}
    }    
}


########
# Main
########

# Get command line args
if {$argc != 1} {
    puts "Usage: GetChassisInfo.tcl {chassis ip or hostname}"
    puts "Ex: tclsh GetChassisInfo.tcl 10.2.1.1"
    return -1
}
set szChassisIp [lindex $argv 0]

#package require SpirentTestCenter
source SpirentTestCenter.tcl

# Connect to chassis
puts "Connecting to chassis $szChassisIp..."
stc::connect $szChassisIp
set hChassis [getChassis]

# Display chassis info
displayChassisInfo $hChassis

# Disconnect from chassis
puts "\nDisconnecting from chassis $szChassisIp...\n"
stc::disconnect $szChassisIp

puts "Complete."

