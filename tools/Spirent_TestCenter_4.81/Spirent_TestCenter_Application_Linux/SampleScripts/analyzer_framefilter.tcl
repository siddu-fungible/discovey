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

# File Name:                 analyzer_framefilter.tcl
# Description:               This script demonstrates how to configure 
#                            an analyzer frame filter. There are two methods
#                            to configure the analyzer config filter.  The
#                            first uses the the -FrameConfig attribute.  The
#                            xml format is not documented.  However, you can
#                            create a filter using the GUI, export it to a
#                            script, and extract it from the script.
#                            The second method uses PDU objects, similar to
#                            the way they are used with the StreamBlock object.
#                            Create the PDU headers under the 
#                            AnalyzerFrameConfigFilter.  Set the filter values
#                            on the particular fields using the format 
#                            illustrated below.    
#

set ENABLE_CAPTURE 0


if {[catch {
  package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Physical topology
  set szChassisIp 10.100.33.137
  set iSlotA 1
  set iPortA 9
  set iSlotB 1
  set iPortB 11

# Create the root project object
  puts "Creating project ..."
  set hProject [stc::create project]

# Create ports
  puts "Creating ports ..."
  set hPortA [stc::create port -under $hProject -location //$szChassisIp/$iSlotA/$iPortA \
  				-useDefaultHost False ]
  set hPortB [stc::create port -under $hProject -location //$szChassisIp/$iSlotB/$iPortB \
  				-useDefaultHost False ]

# Attach ports.  
  puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Attaching Ports ..."
  stc::perform attachPorts -portList [list $hPortA $hPortB] -autoConnect TRUE

# Initialize generator/analyzer.
  set hGenerator [stc::get $hPortA -children-Generator]
  set hAnalyzer [stc::get $hPortB -children-Analyzer]

# Create the AnalyzerFrameConfigFilter filter. Clear the -FrameConfig attribute value. 
  puts "Configuring analyzer frame config filter ..."
  set hAnalyzerFrameConfigFilter [stc::create AnalyzerFrameConfigFilter -under $hAnalyzer -FrameConfig ""]

# Select the method to generate the frame config filter.  The same filter is configured in both methods.
set USE_METHOD_A 0

if {$USE_METHOD_A} {
# Use method A.  Create the XML formatted -FrameConfig attribute string.  
#
# This method will generate the PDU objects based on the -FrameConfig attribute.
#
  set szFrameConfig \
   "<frame> \
      <config> \
        <pdus> \
          <pdu name=\"eth1\" \
            pdu=\"ethernet:EthernetII\"> \
              <dstMac filterMinValue=\"00:00:00:00:00:00\" filterMaxValue=\"FF:FF:FF:FF:FF:FF\">FF:FF:FF:FF:FF:FF</dstMac>
            </pdu> \
          <pdu name=\"ip1\" \
            pdu=\"ipv4:IPv4\"> \
              <destAddr filterMinValue=\"192.168.1.1\" filterMaxValue=\"192.168.1.3\">255.255.255.255</destAddr> \
            </pdu> \
        </pdus> \
      </config> \
    </frame>"

# Adding this would exhaust the available filters.  Remove this and insert one of the other filters to try.
#              <sourceAddr filterMinValue=\"10.0.0.0\" filterMaxValue=\"10.0.0.10\">255.255.255.255</sourceAddr> \

  stc::config $hAnalyzerFrameConfigFilter -FrameConfig $szFrameConfig -Summary "Any IPv4 frame"  
} else {
# Method B.  Use the familiar PDU objects.  Instead of creating under the StreamBlock, create under the 
#   AnalyzerFrameConfig object.  Set the attribute to filter on using the following syntax:
#
#       "min_filter_value/max_filter_value#mask"
#
#   Use the NATIVE format (use delimiters such as : or .) where applicable; i.e. for MAC or IP source/dest values.
#
#
# This method will generate the xml formatted string for the -FrameConfig attribute.
#
  stc::create ethernet:EthernetII -under $hAnalyzerFrameConfigFilter -name af1_eth \
    -srcMac "00:00:00:00:00:00/FF:FF:FF:FF:FF:FF#FF:FF:FF:FF:FF:FF"
   
  stc::create ipv4:IPv4 -under $hAnalyzerFrameConfigFilter -name af1_ip \
    -destAddr "192.168.1.1/192.168.1.3#255.255.255.255"  
}

# Apply this and show the children of the AnalyzerFrameConfigFilter object.  Note that the PDU objects appear.
  stc::apply

  puts "FrameConfig attribute"
  puts \t[stc::get $hAnalyzerFrameConfigFilter -FrameConfig]
  
  puts "\nAnalyzerFrameConfigFilter children"
  foreach hChild [stc::get $hAnalyzerFrameConfigFilter -children] {
    puts \n\t$hChild

  # Display the attributes for each child.    
    foreach {szAttribute szName} [stc::get $hChild] {
      puts \t\t$szAttribute\t$szName
    }
  }
  puts \n\n
  
# Create a stream block.
  puts "Configuring stream block ..."
  set hStreamBlock [stc::create streamBlock -under $hPortA -insertSig TRUE \
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
          -Mask "000000FF" \
          -StepValue "0A000001" \
          -Data "0A000002" \
          -RecycleCount 100 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream true \
          -Offset 0 \
          -OffsetReference "sb1_ip.sourceAddr"]

  set hRangeModifer2 [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask FFFFFFFF \
          -StepValue 1 \
          -Data C0A80101 \
          -RecycleCount 10 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream true \
          -Offset 0 \
          -OffsetReference "sb1_ip.destAddr"]
  
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
              -Duration 10000 \
  	          -LoadMode FIXED \
  	          -FixedLoad 100 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode PORT_BASED

# Subscribe to realtime results
  puts "Subscribe to realtime results"

  stc::subscribe -Parent $hProject \
                -configType Analyzer \
                -resultParent $hPortB \
                -resultType FilteredStreamResults  \
                -filenamePrefix "FilteredStreamResults" \
                -interval 1
                       
# Apply configuration.  
  puts "Apply configuration" 
  stc::apply

  if { $ENABLE_CAPTURE } {
     puts "[clock format [clock seconds] -format %m-%d-%Y%l:%M:%S%p] Starting Capture..."
  
  # Get the capture object. (Automatically created)
     set hCapture [stc::get $::hPortB -children-capture]
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
    
# Retrieve the resultChild objects. There will be one handle for each filtered stream entry.
  puts "\n\nFiltered Frame Results:"

# Using the -children method to obtain results object handles.  
  foreach hResults [stc::get $hPortB.Analyzer -children-FilteredStreamResults] {
    array set aResults [stc::get $hResults]
    
  # Get the filtered Names and Values.  This is a nice way to display what unique elements
  #   were tracked.
    set szResults ""
    
    for {set i 1} {$i <= 10} {incr i} {
      if {![string equal $aResults(-FilteredName_$i) ""]} {
        append szResults $aResults(-FilteredName_$i) ":$aResults(-FilteredValue_$i) "
      } else {
        break
      }
    }
    
    append szResults \t$aResults(-FrameCount)
    puts \t$szResults
  }
  puts \n\n

  if { $ENABLE_CAPTURE } {
    puts "[clock format [clock seconds] -format %m-%d-%Y_%l:%M:%S%p] Retrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
  }

# Write results to a database.
  puts "Writing results to a db file ..."
  stc::perform SaveResult -DatabaseConnectionString frame_filter.db -OverwriteIfExist TRUE

# Detach ports.
  stc::perform detachPorts -portList [list $hPortA $hPortB]

# Delete configuration
  puts "Deleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}
