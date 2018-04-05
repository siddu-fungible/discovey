# Copyright (c) 2007 by Spirent Communications, Inc.
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

# File Name:                 VlanTaggedFrames.tcl
# Description:               This script demonstrates the creation of
#                            Vlan tagged frames. Use the capture feature
#                            to verify the vlan tagged frames were
#                            created.                          
# 

set ENABLE_CAPTURE 1

if {[catch {   
# Load the API.  
  package require SpirentTestCenter

  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Physical topology
  set szChassisAddr 10.100.33.137
  set iSlotA 1
  set iPortA 9
  set iSlotB 1
  set iPortB 11
  
# MAC addresses
  set szMacAddrPortA "11.11.11.11.11.11"
  set szMacAddrPortB "22.22.22.22.22.22"

# Create the root project object
  set hProject [stc::create project]

# Create ports.
  puts "\nCreating ports"
  set hPortA [stc::create port -under $hProject -location //$szChassisAddr/$iSlotA/$iPortA \
          -useDefaultHost FALSE ]
  set hPortB [stc::create port -under $hProject -location //$szChassisAddr/$iSlotB/$iPortB \
          -useDefaultHost FALSE ]

# Show port attributes.
  set lstPortInfo [stc::get $hPortA]
  
  puts "\nTx port information"
  
  foreach {szAttribute szValue} $lstPortInfo {
    puts \t$szAttribute\t$szValue
  }

# Configure Capture Settings.
  stc::config $hPortB.capture -mode REGULAR_MODE -srcMode TX_RX_MODE

# Use a single command to attachPorts (connect, reserve, and setup Port Mappings)
# Attach ports.
  puts "\nAttaching Ports ..."
  stc::perform attachPorts -portList [list $hPortA $hPortB] -autoConnect TRUE

# Subscribe to realtime results.  
  set hResultDataSetRxStreamSummaryResults [stc::subscribe -Parent $hProject \
      -configType StreamBlock \
      -resultType RxStreamSummaryResults \
      -filenameprefix RxStreamSummaryResults \
      -viewAttributeList [list MinLatency MaxLatency AvgLatency BitRate DroppedFrameCount FrameCount FrameRate]]

# Configure Capture.
  if { $ENABLE_CAPTURE } {
     puts "\nStarting Capture..."
  
  # Create a capture object. Automatically created.
     set hCaptureRx [stc::get $::hPortB -children-capture]
     stc::config $hCaptureRx -mode REGULAR_MODE -srcMode TX_RX_MODE  
     stc::perform CaptureStart -captureProxyId $hCaptureRx  
  }
  
# Create traffic.  
  set hStreamBlockPort [stc::create streamBlock -under $hPortA -insertSig true \
        -frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128 \
        -loadUnit BITS_PER_SECOND -load 100 -name StreamBlockPortA]
     
# Add the EthernetII header.
  set hEthernet [stc::create ethernet:EthernetII -under $hStreamBlockPort -name sb1_eth -srcMac $szMacAddrPortA \
          -dstMac $szMacAddrPortA]

# Add a Vlan container object.
  set hVlanContainer [stc::create vlans -under $hEthernet]
  
# Add a Vlan header.
  stc::create Vlan -under $hVlanContainer -pri 000 -cfi 0 -id 101
    
# Configure generator
  puts "\nConfiguring Generator"
  
  set hGenerator [stc::get $hPortA -children-Generator]
  
  set hGeneratorConfig [stc::get $hGenerator -children-GeneratorConfig]
  
  stc::config $hGeneratorConfig \
              -DurationMode BURSTS \
  	          -BurstSize 1 \
              -Duration 100 \
  	          -LoadMode FIXED \
  	          -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode PORT_BASED
  
  puts "\nApplying configuration"
  stc::apply

  puts "\nStart Generator"
  stc::perform GeneratorStart -GeneratorList $hGenerator

# Poll the generator until it has stopped.
  while {![string equal [stc::get $hGenerator -state] "STOPPED"]} {
    after 1000
  }

  puts "\nStop Generators"
  stc::perform GeneratorStop -GeneratorList $hGenerator
  
  puts "\n\nTest Results"
  
  foreach hResults [stc::get $hResultDataSetRxStreamSummaryResults -resultchild-Targets] {
    array set aResults [stc::get $hResults]
    
  # Retrieve the streamBlock name.
    set szName [stc::get [lindex $aResults(-resultchild-Sources) 0] -Name]  
        
    puts "\t$szName\tMin: $aResults(-MinLatency)\tMax: $aResults(-MaxLatency)\tAvg: $aResults(-AvgLatency)"
  }
  
# Save the capture.
  if { $ENABLE_CAPTURE } {
    puts "\nRetrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCaptureRx
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCaptureRx -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCaptureRx -PktCount]"
  } 

  stc::perform detachPorts -portList [list $hPortA $hPortB]
  
# Delete configuration
  puts "\nDeleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}