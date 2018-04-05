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

# File Name:                 TableModifierCustom.tcl
# Description:               This script demonstrates the use of
#                            TableModifiers to create unique streams.
#                            A custom PDU is used to demonstrate the 
#                            maximum table list entry size of 16 bytes.

set ENABLE_CAPTURE 1

# Load the Spirent TestCenter API.
	package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.29
  set iTxSlot 11
  set iTxPort 1
  set iRxSlot 11
  set iRxPort 2

if {[catch {
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
  
  puts "Apply configuration"
  stc::apply

# Get the generator and analyzer.  
  set hGeneratorTx [stc::get $hPortTx -children-Generator]  
  set hAnalyzerRx [stc::get $hPortRx -children-Analyzer]
    
# Create streams. Note that the attribute, -frameConfig, was left at its default value.
#   The default value contains an ethernet and an IPv4 PDU. To remove the defaults, set
#   the attribute -frameConfig to "".
  puts "Configuring stream blocks"
  set hStreamBlock [stc::create streamBlock -under $hPortTx \
  			-frameLengthMode AUTO -maxFrameLength 1200 -FixedFrameLength 128]
  
# Create PDUs.  
  puts "Adding headers"
  stc::create custom:Custom -under $hStreamBlock -name custom -pattern EE00000000000000000000000000000000EE

# Create 5 list entries of repeated patterns.  The length is 16 bytes (the maximum size).   
  lappend lstData [string repeat AA 16]  
  lappend lstData [string repeat BB 16]  
  lappend lstData [string repeat CC 16]  
  lappend lstData [string repeat DD 16]  
  lappend lstData [string repeat EE 16]  

# The table modifier will insert the entries from the list into the custom
#   pattern between the delimiting EE bytes.  
  puts "Creating TableModifier on Stream Block"
  set hTableModifier [stc::create TableModifier \
          -under $hStreamBlock \
          -Data $lstData \
          -RepeatCount 0 \
          -DataType NATIVE \
          -EnableStream true \
          -Offset 1 \
          -OffsetReference "custom.pattern"]

  puts "\n\nStreamBlock information"
  # Display stream block information.
    set lstStreamBlockInfo [stc::perform StreamBlockGetInfo -StreamBlock $hStreamBlock] 
  
    foreach {szName szValue} $lstStreamBlockInfo {
      puts \t$szName\t$szValue
    }
    puts \n\n
  
  
  puts "\n\nTableModifier information"
  # Display stream block information.
    set lstTableModifierInfo [stc::get $hTableModifier]
  
    foreach {szName szValue} $lstTableModifierInfo {
      puts \t$szName\t$szValue
    }
    puts \n\n
  
    
# Configure generator
  puts "Configuring Generator"
  set hGeneratorConfig [stc::get $hGeneratorTx -children-GeneratorConfig]

# For verifying capture packets, use a smaller duration with the BURSTS mode.
#   Disable the capture feature, set ENABLE_CAPTURE to 0, and change the -DurationMode
#   attribute to SECONDS, while changing the -Duration attribute.  Monitor other
#   port attributes. Also adjust the time loop below for longer test time. 
  stc::config $hGeneratorConfig \
              -DurationMode BURSTS \
              -BurstSize 1 \
              -Duration 100 \
              -LoadMode FIXED \
              -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
              -SchedulingMode RATE_BASED
  
# Subscribe to realtime results
  puts "Subscribe to results"
  
  stc::subscribe -Parent [lindex [stc::get system1 -children-Project] 0] \
                -ConfigType Analyzer \
                -resulttype AnalyzerPortResults  \
                -filenameprefix "Analyzer_Port_Results"
  
  stc::subscribe -Parent [lindex [stc::get system1 -children-Project] 0] \
                 -ConfigType Generator \
                 -resulttype GeneratorPortResults  \
                 -filenameprefix "Generator_Port_Counter" \
                 -Interval 2
            
  puts "Apply configuration" 
  stc::apply
  
  
  if { $ENABLE_CAPTURE } {
     puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Starting Capture..."
  
  # Create a capture object. Automatically created.
     set hCapture [stc::get $::hPortRx -children-capture]
     stc::config $hCapture -mode REGULAR_MODE -srcMode TX_RX_MODE  
     stc::perform CaptureStart -captureProxyId $hCapture
  }
  
# Get the handle to the results information, so we can monitor receive side realtime port results.
  set hAnalyzerResults [ stc::get $hAnalyzerRx -children-AnalyzerPortResults ]
  
# Start the analyzer and generator.  
  puts "Start Analyzer"
  stc::perform AnalyzerStart -AnalyzerList $hAnalyzerRx
  
  puts "Start Generator"
  stc::perform GeneratorStart -GeneratorList $hGeneratorTx
  
  puts "Current generator state [stc::get $hGeneratorTx -state]"
  puts "Current analyzer state [stc::get $hAnalyzerRx -state]"
    
  set iTime 0
  
  puts "Received signature tagged frames"
  
  # Display runtime results:
    while {$iTime < 10} {
      puts "\t[stc::get $hAnalyzerResults -sigFrameCount]"
      
      incr iTime
      after 1000
    }
  
  puts "Current analyzer state [stc::get $hAnalyzerRx -state]"
  puts "Current generator state [stc::get $hGeneratorTx -state]"

# Stop the analyzer.  
  puts "Stop Analyzer"
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzerRx
  
  puts "Final frame statistics"
  puts "\tJumbo frames:\t[stc::get $hAnalyzerResults -JumboFrameCount]"
  puts "\tSignature frames:\t[stc::get $hAnalyzerResults -sigFrameCount]"
  puts "\tMax Frame Length:\t[stc::get $hAnalyzerResults -MaxFrameLength]"
  puts "\tTotal Frame Count:\t[stc::get $hAnalyzerResults -totalFrameCount]"
  puts \n\n\n

# Verify that the table entries were inserted in the correct position in the frame.    
  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
    puts "Saved Captured frames:\t[stc::get $hCapture -PktSavedCount]"  
  }
    
# Detach ports.
  puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Attaching Ports ..."
  stc::perform DetachPorts -portList [list $hPortTx $hPortRx]
  
# Delete configuration
  puts "Deleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}
