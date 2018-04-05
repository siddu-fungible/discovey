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

# File Name:                 AnatomyUsingAttach.tcl
# Description:               This script demonstrates basic features 
#                            such as creating streams, generating traffic,
#                            enabling capture, saving realtime results
#                            to files, and retrieving results.
#                            This script uses the attachPorts command. 

set ENABLE_CAPTURE 1

if {[catch {
  package require SpirentTestCenter
  
# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Physical topology
  set szChassisIp 192.168.1.1
  set iTxSlot 1
  set iTxPort 11
  set iRxSlot 1
  set iRxPort 12

# Create the root project object
  puts "Creating project ..."
  set hProject [stc::create project]

# Create ports
  puts "Creating ports ..."
  set hPortTx [stc::create port -under $hProject -location //$szChassisIp/$iTxSlot/$iTxPort \
  				-useDefaultHost False ]
  set hPortRx [stc::create port -under $hProject -location //$szChassisIp/$iRxSlot/$iRxPort \
  				-useDefaultHost False ]

# Attach ports. (One command takes care of three) 
# Connect to a chassis, reserve ports, and create the mapping between the 
#   physical ports and their logical representation in the test configuration.
  puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Attaching Ports ..."
  stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE

# Initialize generator/analyzer.
  set hGenerator [stc::get $hPortTx -children-Generator]
  puts "Stopping Generator -current state [stc::get $hGenerator -state]"
  
  set hAnalyzer [stc::get $hPortRx -children-Analyzer]
  puts "Stopping Analyzer -current state [stc::get $hAnalyzer -state]"
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzer

# Create a stream block.
  puts "Configuring stream block ..."
  set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true \
  			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]

# Add an EthernetII Protocol Data Unit (PDU).
  puts "Adding headers"
  stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
  				-dstMac 00:00:00:00:00:40 

# Use modifier to generate multiple streams.
  puts "Creating Modifier on Stream Block ..."
  set hRangeModifier [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode DECR \
          -Mask "00:00:FF:FF:FF:FF" \
          -StepValue "00:00:00:00:00:01" \
          -Data "00:00:10:10:00:01" \
          -RecycleCount 20 \
          -RepeatCount 0 \
          -DataType NATIVE \
          -EnableStream true \
          -Offset 2 \
          -OffsetReference "sb1_eth.dstMac"]

# Update just the streamblock.
  stc::perform StreamBlockUpdate -StreamBlock "$hStreamBlock"

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

  puts "Current analyzer state [stc::get $hAnalyzer -state]"
  puts "Current generator state [stc::get $hGenerator -state]"

# Stop the generator.
  puts "Stop Generator"
  stc::perform GeneratorStop -GeneratorList $hGenerator 

# Stop the analyzer.  
  puts "Stop Analyzer"
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzer

# Display some statistics.
  set hAnalyzerResults [ stc::get $hAnalyzer -children-AnalyzerPortResults]
  
  puts "Frames Counts:"
  puts "\tSignature frames: [stc::get $hAnalyzerResults -sigFrameCount]"
  puts "\tTotal frames: [stc::get $hAnalyzerResults -totalFrameCount]"


  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
  }

# Detach ports. (One command takes care of two) 
# Release ports and disconnect from a chassis. 
  stc::perform DetachPorts -portList [list $hPortTx $hPortRx]

# Delete configuration
  puts "Deleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}
