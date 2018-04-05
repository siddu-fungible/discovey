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

# File Name:    Apply.tcl
# Description:  This script demonstrates the apply command and how
#               any change to a configuration must be applied to the IL
#               for it to have any affect.

#package require SpirentTestCenter
source SpirentTestCenter.tcl

# Physical topology
set szChassisIp 10.21.0.16
set iTxSlot 2
set iTxPort 1
set iRxSlot 2
set iRxPort 2

# Create the root project object
puts "Creating project ..."
set hProject [stc::create project]

# Create ports
puts "Creating ports ..."
set hPortTx [stc::create port -under $hProject -location //$szChassisIp/$iTxSlot/$iTxPort \
                            -useDefaultHost False ]
set hPortRx [stc::create port -under $hProject -location //$szChassisIp/$iRxSlot/$iRxPort \
                            -useDefaultHost False ]
# Attach ports.
puts "Attaching Ports ..."
stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE

# Create 1 stream block.
puts "Configuring stream block ..."
set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true -frameConfig "" -frameLengthMode FIXED -FixedFrameLength 128]

stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
                              -dstMac 01:00:5e:01:01:01

stc::create ipv4:IPv4 -under $hStreamBlock -name sb1_ipv4 -destAddr 225.0.0.1 -sourceAddr 30.0.0.2

# Apply configuration.
puts "Applying configuration ..."
stc::apply

# Subscribe to realtime results
puts "Subscribing to realtime results ..."
set hResultDataSetTxStreamResults [stc::subscribe -Parent $hProject \
           -configType streamblock \
           -resulttype txstreamresults \
           -viewAttributeList "framecount framerate bitrate expectedrxframecount l1bitcount l1bitrate bitcount " ]

# Start Traffic
puts "Starting Traffic ..."
set hGenerator [stc::get $hPortTx -children-Generator]
stc::perform GeneratorStart -GeneratorList $hGenerator

after 5000

proc showBitRate {hResultDataSet} {
    for { set i 0 } { $i < 10 } { incr i } {
        set lstResults [stc::get $hResultDataSet -ResultHandleList]
        foreach hResult $lstResults {
            puts "BitRate: [ stc::get $hResult -bitrate ]"    
        }
        after 1000
    }
}

showBitRate $hResultDataSetTxStreamResults

# Change the frame length to 2048
stc::config $hStreamBlock -FixedFrameLength 2048
puts "Frame Length now changed to [ stc::get $hStreamBlock -FixedFrameLength ]"

# See that the bit rate has not yet changed.
puts "However, the bit rate has not yet changed."
showBitRate $hResultDataSetTxStreamResults

# Apply the configuration change to the IL.
puts "Applying configuration ..."
stc::apply

# Now the frame rate has changed.
puts "Now the bit rate has changed since the configuration has been applied."
showBitRate $hResultDataSetTxStreamResults

# Stop Traffic
puts "Stopping Traffic ..."
stc::perform GeneratorStop -GeneratorList $hGenerator

# Detach ports.
puts "Detaching Ports ..."
stc::perform DetachPorts -portList [list $hPortTx $hPortRx]

# Delete configuration
puts "Deleting project"
stc::delete $hProject

