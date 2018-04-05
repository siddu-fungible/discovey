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

# File Name:                 RangeModifiers.tcl
# Description:               This script demonstrates the use of a
#                            RangeModifier to create 20 unique streams.
#                            Realtime results are retrieved for one of
#                            the streams and displayed during test
#                            execution.

set ENABLE_CAPTURE 0
                 
if {[catch {
  package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.137
  set iTxSlot 1
  set iTxPort 9
  set iRxSlot 1
  set iRxPort 11

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
    
# Retrieve the generator and analyzer objects.
  set hGenerator [stc::get $hPortTx -children-Generator]
  set hAnalyzer [stc::get $hPortRx -children-Analyzer]

# Create a stream block.
  puts "Configuring stream block ..."
  set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true \
  			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]
    
# Add an EthernetII Protocol Data Unit (PDU).
  stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
  				-dstMac 00:00:00:00:00:40   

# Create 20 trackable streams (each stream has a unique stream identifier).  
  puts "Creating Range Modifier on Stream Block"
  set RangeModifier(1) [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Data "00:00:00:00:00:00" \
          -Mask "00:00:FF:FF:FF:FF" \
          -StepValue "00:00:00:00:00:01" \
          -RecycleCount 20 \
          -RepeatCount 0 \
          -DataType NATIVE \
          -EnableStream true \
          -OffsetReference "sb1_eth.dstMac" \
          -Active true]
    
# Display stream block information.
  set lstStreamBlockInfo [stc::perform StreamBlockGetInfo -StreamBlock $hStreamBlock] 

  foreach {szName szValue} $lstStreamBlockInfo {
    puts \t$szName\t$szValue
  }
  puts \n\n
    
# Configure generator
  puts "Configuring Generator"
  set hGeneratorConfig [stc::get $hGenerator -children-GeneratorConfig]
  
  stc::config $hGeneratorConfig \
              -DurationMode SECONDS \
  	          -BurstSize 1 \
              -Duration 20 \
  	          -LoadMode FIXED \
  	          -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode PORT_BASED
  
# Analyzer Configuration
  puts "Configuring Analyzer"
  set hAnalyzerConfig [stc::get $hAnalyzer -children-AnalyzerConfig]
  
# Subscribe to realtime results
  puts "Subscribe to results"
  stc::subscribe -Parent $hProject \
                -ConfigType Analyzer \
                -resulttype AnalyzerPortResults  \
                -filenameprefix "Analyzer_Port_Results"

  stc::subscribe -Parent $hProject \
                 -ConfigType Generator \
                 -resulttype GeneratorPortResults  \
                 -filenameprefix "Generator_Port_Counter" \
                 -Interval 2

# Save the handle to this result data set.  
  set hResultDataSetRxStreamSummaryResults [ stc::subscribe -parent $hProject \
       -resultParent $hProject \
       -configType streamblock \
       -resultType rxstreamsummaryresults -interval 1 -filenamePrefix "rxstreamsummaryresults"]

# Get the result handle list from the result data set.
  set lstRxStreamSummaryResults [stc::get $hResultDataSetRxStreamSummaryResults -ResultHandleList]
      
# Save the handle to the first stream's result.
  set hStreamResults [lindex $lstRxStreamSummaryResults 0]  

  puts hStreamResults\t$hStreamResults
      
  puts "Apply configuration" 
  stc::apply
    
  if { $ENABLE_CAPTURE } {
     puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Starting Capture..."
  
  # Get the capture object. (Automatically created)
     set hCapture [stc::get $::hPortRx -children-capture]
     stc::config $hCapture -mode REGULAR_MODE -srcMode TX_RX_MODE  
     stc::perform CaptureStart -captureProxyId $hCapture
  }
    
# Start the analyzer and generator.
  puts "Start Analyzer"
  stc::perform AnalyzerStart -AnalyzerList $hAnalyzer
  puts "Start Generator"
  stc::perform GeneratorStart -GeneratorList $hGenerator

  puts "Transmit for 10 seconds ..."
  
  set iTime 0
    
# Display realtime results.
  puts "Stream frame count:"
  
  while {$iTime < 10} {
    puts "\t\t[stc::get $hStreamResults -FrameCount]"
    incr iTime
    after 1000
  }
  
  puts "Current analyzer state [stc::get $hAnalyzer -state]"
  puts "Current generator state [stc::get $hGenerator -state]"

# Stop the analyzer.  
  puts "Stop Analyzer"
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzer
  
  set hAnalyzerResults [ stc::get $hAnalyzer -children-AnalyzerPortResults ]
  
  puts "\n\nAnalyzer Port Results"
  puts \tJumbo:\t[stc::get $hAnalyzerResults -JumboFrameCount]
  puts \tSig:\t[stc::get $hAnalyzerResults -sigFrameCount]
  puts \tUnder:\t[stc::get $hAnalyzerResults -UndersizeFrameCount]
  puts \tOver:\t[stc::get $hAnalyzerResults -oversizeFrameCount]
  puts "\tMax Len:\t[stc::get $hAnalyzerResults -MaxFrameLength]"
  puts \tTotal:\t[stc::get $hAnalyzerResults -totalFrameCount]\n\n
  
  
  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
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
