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

# File Name:                 TableModifiers.tcl
# Description:               This script demonstrates the use of
#                            TableModifiers to create unique streams.

set ENABLE_CAPTURE 0

if {[catch {
  package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.29
  set iTxSlot 11
  set iTxPort 1
  set iRxSlot 11
  set iRxPort 2

  # Create the root project object
  set hProject [stc::create project]
  
  # Create ports
  puts "Create ports"
  set hPortTx [stc::create port -under $hProject -location //$szChassisAddr/$iTxSlot/$iTxPort \
  				-useDefaultHost False ]
  set hPortRx [stc::create port -under $hProject -location //$szChassisAddr/$iRxSlot/$iRxPort \
  				-useDefaultHost False ]
  
# Attach ports.
  puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Attaching Ports ..."
  stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE

# Initialize generators/analyzers.
  set hGeneratorTx [stc::get $hPortTx -children-Generator]      
  set hAnalyzerRx [stc::get $hPortRx -children-Analyzer]
  
# Create traffic.
  puts "Configuring stream block"
  set hStreamBlockTx [stc::create streamBlock -under $hPortTx -insertSig true \
  			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]
    
# Create Ethernet PDUs.
  puts "Adding headers"
  stc::create ethernet:EthernetII -under $hStreamBlockTx -name sb1_eth -srcMac 10:00:00:00:00:00 \
  				-dstMac 10:00:00:00:00:00     

# Generate 100 streams per streamBlock.   
  set iMaxCount 100

# Some code to create list of iMaxCount entries, each containing last 4 bytes of MAC address.  
  for {set iIndex 0} {$iIndex <= 4} {incr iIndex} {
    set aBytes($iIndex) 0
  }
    
  for {set i 1} {$i <= $iMaxCount} {incr i} {
    set iRemainder $iMaxCount
    set szTempData ""
    incr aBytes(0)
    
    for {set iIndex 0} {$iIndex < 4} {incr iIndex} {
      
      if {$aBytes($iIndex) > 255} {
        set aBytes($iIndex) 0
        incr aBytes([expr $iIndex + 1])
      }
    }
    
    for {set iIndex 3} {$iIndex > -1} {incr iIndex -1} {
      append szTempData [format %02X $aBytes($iIndex)]
    }
  
  # Build a list with data to be used in the TableModifier.    
    lappend lstData $szTempData
  }
  
# Have a look at the data created by setting the value from 0 to 1.
  if {0} {
    foreach szEntry $lstData {
      puts \t>$szEntry<
    }
    puts \n\n
  }
  
# Use TableModifiers to generate the streams. Each stream will
#     use an entry from the list. Note that the -DataType is "BYTE".
#   This allows the attribute, -Offset, to move the modifer 2 bytes
#     relative to the offset reference.
#   The OffsetReference is the name of the ethernet PDU, sb1_eth,
#     dotted-with the reference attribute, dstMac.  Hence, 
#     sb1_eth.dstMac.
  puts "Creating TableModifier on Stream Block Tx"
  set hTableModifierTx [stc::create TableModifier \
          -under $hStreamBlockTx \
          -Data $lstData \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream true \
          -OffsetReference "sb1_eth.dstMac" \
          -Offset 2]
      
# Display stream block information.
  puts "\n\nStreamBlock information"
  set lstStreamBlockInfo [stc::perform StreamBlockGetInfo -StreamBlock $hStreamBlockTx] 

  foreach {szName szValue} $lstStreamBlockInfo {
    puts \t$szName\t$szValue
  }
  puts \n\n
    
# Display stream block information.
  puts "\n\nTableModifier information"
  set lstTableModifierInfo [stc::get $hTableModifierTx]

  foreach {szName szValue} $lstTableModifierInfo {
    puts \t$szName\t$szValue
  }
  puts \n\n
  
    
# Configure generator
  puts "Configuring Generator"
  set hGeneratorConfigTx [stc::get $hGeneratorTx -children-GeneratorConfig]
  
  stc::config $hGeneratorConfigTx \
              -DurationMode BURSTS \
              -BurstSize 1 \
              -Duration [expr $iMaxCount * 2] \
              -LoadMode FIXED \
              -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
              -SchedulingMode RATE_BASED
    
# Subscribe to realtime results
  puts "Subscribe to realtime results"
  
# Save the handle to this result subscription.  
  set hRxStreamSummaryResult [ stc::subscribe -parent $hProject \
       -resultParent $hProject \
       -configType streamblock \
       -resultType rxstreamsummaryresults -interval 1 -filenamePrefix "rxstreamsummaryresults"]
      
# Retrieve the resultChild objects. There will be one handle for each stream.
  set lstResultChildTargets [stc::get $hRxStreamSummaryResult -resultchild-Targets]
  
# Save the handle to the first stream's result.
  set hStreamResults [lindex $lstResultChildTargets 0]  
    
  puts "Apply configuration" 
  stc::apply
              
  if { $ENABLE_CAPTURE } {
     puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Starting Capture..."
  
  # Create a capture object. Automatically created.
     set hCaptureRx [stc::get $::hPortRx -children-capture]
     stc::config $hCaptureRx -mode REGULAR_MODE -srcMode TX_RX_MODE  
     stc::perform CaptureStart -captureProxyId $hCaptureRx  
  }
  
# Start the analyzer and generator.
  puts "Start Analyzer"
  stc::perform AnalyzerStart -AnalyzerList $hAnalyzerRx
  puts "Current analyzer state [stc::get $hAnalyzerRx -state]"
    
  puts "Start Generator"
  stc::perform GeneratorStart -GeneratorList $hGeneratorTx
  puts "Current generator state [stc::get $hGeneratorTx -state]"

  puts "Wait 10 seconds ..."
  
  set iTime 0
    
# Display realtime results from one of the streams.
  while {$iTime < 10} {
    puts "\tStream frame count:\t[stc::get $hStreamResults -FrameCount]"
    incr iTime
    after 1000
  }
  
  puts "Current analyzer state [stc::get $hAnalyzerRx -state]"
  puts "Current generator state [stc::get $hGeneratorTx -state]"

# Stop the analyzers.  
  puts "Stop Analyzer"  
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzerRx
  
  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCaptureRx
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCaptureRx -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCaptureRx -PktCount]"
  } 
  
# Detach ports.
  puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Detaching Ports ..."
  stc::perform DetachPorts -portList [list $hPortTx $hPortRx]
  
# Delete configuration
  puts "Deleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}
