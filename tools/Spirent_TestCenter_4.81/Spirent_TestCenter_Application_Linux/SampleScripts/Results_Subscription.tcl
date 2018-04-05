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

# File Name:                 Results_Subscription.tcl
# Description:               This script demonstrates multiple ways to 
#                            retrieve subscribed results.  
#                              One method uses the stc::subscribe function to obtain
#                            a data set handle. Then, either the 
#                            -ResultHandleList attribute or the -resultchild-Targets
#                            relation, can be used to obtain the result objects.
#                              Another way uses the -children relation.
#                            Both methods achieve the same goal: obtain the handle
#                            to the subscribed result object.  Once this is
#                            obtained, you can easily retrieve the object's
#                            attributes (statistics) with the stc::get function.
#

set ENABLE_CAPTURE 1


if {[catch {
  package require SpirentTestCenter

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

# Apply the configuration.
  puts "Apply configuration"
  stc::apply

# Retrieve handles to the generator and analyzer.
  set hGenerator [stc::get $hPortTx -children-Generator]  
  set hAnalyzer [stc::get $hPortRx -children-Analyzer]

# Create a stream block.
  puts "Configuring stream block ..."
  set iStreamBlockLoad 100
  
  set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true \
  			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 256 \
        -Load $iStreamBlockLoad -LoadUnit FRAMES_PER_SECOND]

# Add an EthernetII Protocol Data Unit (PDU).
  puts "Adding headers"
  stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
  				-dstMac 00:00:00:00:00:00 

# Use modifier to generate multiple streams.
  puts "Creating Modifier on Stream Block ..."
  set hRangeModifier [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "0000FFFFFFFF" \
          -StepValue "000000000001" \
          -Data "000000000000" \
          -RecycleCount 4294967295 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream FALSE \
          -Offset 0 \
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
              -DurationMode SECONDS \
  	          -BurstSize 1 \
              -Duration 100 \
  	          -LoadMode FIXED \
  	          -FixedLoad 25 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode RATE_BASED

# Analyzer Configuration
  puts "Configuring Analyzer"
  set hAnalyzerConfig [stc::get $hAnalyzer -children-AnalyzerConfig]

# Subscribe to realtime results

# Method #1.  Retrieve the result data set handle.
  set hResultDataSetAnalyzerPortResults [stc::subscribe -Parent $hProject \
                -ConfigType Analyzer \
                -resulttype AnalyzerPortResults  \
                -filenameprefix "Analyzer_Port_Results"]

# Configure Capture.
  if { $ENABLE_CAPTURE } {
    puts "\nStarting Capture..."
  
  # Create a capture object. Automatically created.
    set hCapture [stc::get $::hPortTx -children-capture]
    stc::config $hCapture -mode REGULAR_MODE -srcMode TX_RX_MODE  
    stc::perform CaptureStart -captureProxyId $hCapture  
  }

# Apply configuration.  
  puts "Apply configuration" 
  stc::apply

# Save the configuration as an XML file for later import into the GUI.
  puts "\nSave configuration as an XML file."
  stc::perform SaveAsXml

# Start the analyzer and generator.
  puts "Start Analyzer"
  stc::perform AnalyzerStart -AnalyzerList $hAnalyzer
  puts "Current analyzer state [stc::get $hAnalyzer -state]"
    
  puts "Start Generator"
  stc::perform GeneratorStart -GeneratorList $hGenerator
  puts "Current generator state [stc::get $hGenerator -state]"

  set iTransmitTime 10
  
  puts "\nRun test for $iTransmitTime seconds ..."
        
# Get the result handle list from the result data set. This can be achieved in two ways.
#   Note that both ways retrieve the identical list.  

# First way uses the -ResultHandleList attribute.
  set lstAnalyzerPortResults [stc::get $hResultDataSetAnalyzerPortResults -ResultHandleList]

  puts "\nList results for -ResultHandleList attribute"
  foreach szItem $lstAnalyzerPortResults {
    puts \t$szItem
  }

# Second way uses the -childresult-Targets relation.
  set lstAnalyzerPortResults [stc::get $hResultDataSetAnalyzerPortResults -resultchild-Targets]
  
  puts "\nList results for -resultchild-Targets relation"
  foreach szItem $lstAnalyzerPortResults {
    puts \t$szItem
  }

# In this example, there is only one Analyzer object created, so there will be only one
#   AnalyzerPortResults object.  
  set hAnalyzerPortResults [lindex $lstAnalyzerPortResults 0]
    

# Method #2.  Retrieve the Analyzer Port handle using the -children relation.  Note the
#   string after the "-children-" is the name of the result object to retrieve.
#
# This method is nice if multiple Analyzer objects were created. You can specify which
#   object to retrieve results for as opposed to retrieving them from a list using the
#   lindex operation.
#
# This is the same handle as above.
#
  set hAnalyzerPortResults [ stc::get $hAnalyzer -children-AnalyzerPortResults]

  puts "\n\nAnalyzer Port Results"
  
  for {set i 0} {$i < $iTransmitTime} {incr i} {      
  # Update on 1-second intervals.  
    after 1000
    puts "\t\nInterval [expr $i + 1]"            
    puts \tJumbo:\t[stc::get $hAnalyzerPortResults -JumboFrameCount]
    puts \tSig:\t[stc::get $hAnalyzerPortResults -sigFrameCount]
    puts \tUnder:\t[stc::get $hAnalyzerPortResults -UndersizeFrameCount]
    puts \tOver:\t[stc::get $hAnalyzerPortResults -oversizeFrameCount]
    puts "\tMax Len:\t[stc::get $hAnalyzerPortResults -MaxFrameLength]"
    puts \tTotal:\t[stc::get $hAnalyzerPortResults -totalFrameCount] 
  }
  puts \n\n
  
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
