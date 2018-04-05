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

# File Name:                 analyzer_filters_Ipv4src_Ipv4dst_tos.tcl
# Description:               This script uses multiple analyzer filters
#                            to track IPv4 Source, IPv4 Destination, and
#                            TOS values.  Use both the capture and 
#                            filtered stream results to analyze the
#                            results. 
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

# Retrieve the generator and analyzer objects.
  set hGenerator [stc::get $hPortTx -children-Generator]
  set hAnalyzer [stc::get $hPortRx -children-Analyzer]

# Create three Analyzer16Bit filters.  
  set hAnalyzer16BitFilter1 [stc::create Analyzer16BitFilter -under $hAnalyzer]
  set hAnalyzer16BitFilter2 [stc::create Analyzer16BitFilter -under $hAnalyzer]
  set hAnalyzer16BitFilter3 [stc::create Analyzer16BitFilter -under $hAnalyzer]

# Create one Analyzer32Bit filter.  
  set hAnalyzer32BitFilter1 [stc::create Analyzer32BitFilter -under $hAnalyzer]

# Configure the filters.  The filters are using the default StartOfRange and EndOfRange
#   values.  Every unique combination of the filters will be tracked.

# Track IPv4 src addresses. (Use two 16-bit filters to track the 32-bit source field)
  stc::config $hAnalyzer16BitFilter1 -FilterName JohnB1 -Offset 26  
  stc::config $hAnalyzer16BitFilter2 -FilterName JohnB2 -Offset 28
  
# Track IPv4 dst addresses. (Use one 32-bit filter) 
  stc::config $hAnalyzer32BitFilter1 -FilterName JohnB3 -Offset 30 -LocationType START_OF_FRAME

# Track the TOS bits.  
  stc::config $hAnalyzer16BitFilter3 -FilterName JohnB4 -Offset 14 -Mask 0x00E0

# foreach hFilter [list $hAnalyzer16BitFilter1 $hAnalyzer16BitFilter2 $hAnalyzer16BitFilter3 $hAnalyzer16BitFilter4] {
#   puts \n\n$hFilter\n
# 
# # Display analyzer 16 bit attributes.
#   foreach {szAttribute szValue} [stc::get $hFilter] {
#     puts \t$szAttribute\t$szValue
#   }
# }
  
# Create stream blocks.
  set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true \
        -frameConfig "" -frameLengthMode FIXED -FixedFrameLength 64 -Load 0.18 \
        -fillType PRBS]

# Code the length in the destination MAC for easy viewing
  puts "Adding headers"
  stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth \
    -srcMac 00:00:20:00:00:00 -dstMac 00:00:00:00:00:40 

  set hIpv4Object [stc::create ipv4:IPv4 -under $hStreamBlock -name sb1_ip -sourceAddr 10.0.0.2 -destAddr 192.168.1.1]

# Create the TOS header.
 	set hTosDiffserv [stc::create tosDiffserv -under $hIpv4Object]
 	set hTos [stc::create tos -under $hTosDiffserv]
 	stc::config $hTos -name sb1_tos -precedence 8
    
  set hRangeModifer1 [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "FF" \
          -StepValue "01" \
          -Data "00" \
          -RecycleCount 256 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream false \
          -Offset 3 \
          -OffsetReference "sb1_ip.sourceAddr"]

  set hRangeModifer2 [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "FF" \
          -StepValue "01" \
          -Data "00" \
          -RecycleCount 256 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream false \
          -Offset 3 \
          -OffsetReference "sb1_ip.destAddr"]

  set hRangeModifer3 [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "F" \
          -StepValue "1" \
          -Data "0" \
          -RecycleCount 8 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream false \
          -Offset 0 \
          -OffsetReference "sb1_ip.tosDiffserv.tos.precedence"]
  
       
# Configure generator
  puts "Configuring Generator"
  set hGeneratorConfig [stc::get $hGenerator -children-GeneratorConfig]
  
  stc::config $hGeneratorConfig \
              -DurationMode BURSTS \
  	          -BurstSize 1 \
              -Duration 300 \
  	          -LoadMode FIXED \
  	          -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode PRIORITY_BASED
  
# Subscribe to runtime results
  puts "Subscribe to results"

# FilteredStreamResults REQUIRES the -ResultParent attribute be set to a port
#   value.  The default value, the project, will not work.
  stc::subscribe -Parent $hProject \
                  -ResultParent $hPortRx \
                  -ConfigType Analyzer \
                  -resulttype FilteredStreamResults  \
                  -filenameprefix FilteredStreamResults
  
# Apply configuration.  
  puts "Applying configuration ... (this may take a few minutes)" 
  stc::apply

  if { $ENABLE_CAPTURE } {
     puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Starting Capture..."
  
  # Create a capture object. Automatically created.
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

  puts "Transmitting for 5 seconds ..."
  after 5000

  puts "Current analyzer state [stc::get $hAnalyzer -state]"
  puts "Current generator state [stc::get $hGenerator -state]"
  puts "Stop Analyzer"

# Stop the analyzer.  
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzer

  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
    puts "Saved Captured frames:\t[stc::get $hCapture -PktSavedCount]"    
  }

# Write results to a database.
  puts "Writing results to a db file ..."
  stc::perform SaveResult -DatabaseConnectionString results.db -OverwriteIfExist TRUE

# Detach ports.
  stc::perform detachPorts -portList [list $hPortTx $hPortRx]

# Delete configuration
  puts "Deleting project"
  stc::delete $hProject

} err] } {
	puts "Error caught: $err"
}
