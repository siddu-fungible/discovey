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

# File Name:                 analyzer_filters_easy.tcl
# Description:               This script demonstrates how to configure 
#                            a single analyzer filter.   
#

set ENABLE_CAPTURE 1


if {[catch {
  package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Physical topology
  set szChassisIp 10.100.33.137
  set iTxSlot 1
  set iTxPort 9
  set iRxSlot 1
  set iRxPort 11

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
  puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Attaching Ports ..."
  stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE

# Initialize generator/analyzer.
  set hGenerator [stc::get $hPortTx -children-Generator]
  set hAnalyzer [stc::get $hPortRx -children-Analyzer]

# Create four Analyzer16Bit filters.  
  set hAnalyzer16BitFilter1 [stc::create Analyzer16BitFilter -under $hAnalyzer]

  stc::config $hAnalyzer16BitFilter1 -FilterName DstMacFilter -Offset 4  

# Create a stream block.
  puts "Configuring stream block ..."
  set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true \
  			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]

# Add an EthernetII Protocol Data Unit (PDU).
  puts "\nAdding headers"
  stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
  				-dstMac 00:00:00:00:00:40 

  stc::create ipv4:IPv4 -under $hStreamBlock -name sb1_ip -sourceAddr 10.0.0.2 -destAddr 192.168.1.1

# Use modifier to generate multiple streams.
  puts "\nCreating Modifiers on Stream Block"
  set hRangeModifer1 [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "00FF" \
          -StepValue "0001" \
          -Data "0000" \
          -RecycleCount 5 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream false \
          -Offset 4 \
          -OffsetReference "sb1_eth.dstMac"]
  
# Display stream block information.
  puts "\n\nStreamBlock information"
  set lstStreamBlockInfo [stc::perform StreamBlockGetInfo -StreamBlock $hStreamBlock] 

  foreach {szName szValue} $lstStreamBlockInfo {
    puts \t$szName\t$szValue
  }
  puts \n\n
  

# Configure generator
  puts "Configuring Generator"
  set hGeneratorConfig [stc::get $hGenerator -children-GeneratorConfig]
  
  stc::config $hGeneratorConfig \
              -DurationMode BURSTS \
  	          -BurstSize 1 \
              -Duration 100 \
  	          -LoadMode FIXED \
  	          -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode RATE_BASED

# Subscribe to realtime results
  puts "Subscribe to realtime results"
  stc::subscribe -Parent $hProject \
                -configType Analyzer \
                -resultType AnalyzerPortResults  \
                -filenameprefix "Analyzer_Port_Results"
 
  stc::subscribe -Parent $hProject \
                -configType Generator \
                -resultType GeneratorPortResults  \
                -filenameprefix "Generator_Port_Counter" \
                -Interval 2
                
# Note: If analyzer filters are used, no RxStreamSummaryResults can be obtained.  Only
#   FilteredStreamResults will be obtained.  I.e., no file will be created.
  stc::subscribe -Parent $hProject \
                -configType StreamBlock \
                -resultType RxStreamSummaryResults  \
                -filenameprefix RxStreamSummaryResults

  stc::subscribe -Parent $hProject \
                -resultParent $hPortRx \
                -configType Analyzer \
                -resultType FilteredStreamResults  \
                -filenameprefix FilteredStreamResults

# Apply configuration.  
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
  puts "Current analyzer state [stc::get $hAnalyzer -state]"
    
  puts "Start Generator"
  stc::perform GeneratorStart -GeneratorList $hGenerator
  puts "Current generator state [stc::get $hGenerator -state]"

  puts "Wait 10 seconds ..."
  after 10000

# Stop the analyzer.  
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzer

  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
  }

# Write results to a database.
  puts "Writing results to a db file ..."
  stc::perform SaveResult -DatabaseConnectionString analyzer_filters.db -OverwriteIfExist TRUE

# Detach ports.
  stc::perform detachPorts -portList [list $hPortTx $hPortRx]

# Delete configuration
  puts "Deleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}
