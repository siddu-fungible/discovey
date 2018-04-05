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

# File Name:                 StreamBlock_Preview.tcl
# Description:               This script demonstrates the Preview feature
#                            available to the API.  This feature is used
#                            to display the streams that will be generated
#                            using the StreamBlock modifiers.  This is 
#                            equivalent to the Preview tab in the GUI. This
#                            is a nice feature to verify your configuration.                          
# 

set ENABLE_CAPTURE 1

if {[catch {   
  package require SpirentTestCenter

  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Physical topology
  set szChassisAddr 10.100.33.137
  set iSlotA 1
  set iPortA 9
  set iSlotB 1
  set iPortB 11

#
# Test parameters.
#

  set iLoad 10240 
    
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

# Use a single command to attachPorts (connect, reserve, and setup Port Mappings)
# Attach ports.
  puts "\nAttaching Ports ..."
  stc::perform attachPorts -portList [list $hPortA $hPortB] -autoConnect TRUE

# Subscribe to realtime results.  
  set hResultDataSet [stc::subscribe -Parent $hProject \
      -configType StreamBlock \
      -resultType RxStreamSummaryResults \
      -filenameprefix RxStreamSummaryResults \
      -viewAttributeList [list MinLatency MaxLatency AvgLatency BitRate DroppedFrameCount FrameCount FrameRate]]

# Configure Capture.
  if { $ENABLE_CAPTURE } {
    puts "\nStarting Capture..."
  
  # Create a capture object. Automatically created.
    set hCaptureRx [stc::get $::hPortB -children-capture]
  
  # Configure Capture Settings.
    stc::config $hCaptureRx -mode REGULAR_MODE -srcMode TX_RX_MODE  
    stc::perform CaptureStart -captureProxyId $hCaptureRx  
  }
  
# Create traffic.  
  set hStreamBlock [stc::create streamBlock -under $hPortA -insertSig true \
        -frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128 \
        -loadUnit BITS_PER_SECOND -load $iLoad -name StreamBlockPortA]
     
# Add the EthernetII header.
  set hEthernet [stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac $szMacAddrPortA \
          -dstMac $szMacAddrPortA]

# Use modifiers to generate multiple streams.
  puts "Creating Modifier on Stream Block ..."
  set hRangeModifier [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "FFFF" \
          -StepValue "0001" \
          -Data "0000" \
          -RecycleCount 10 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream TRUE \
          -Offset 0 \
          -OffsetReference sb1_eth.dstMac]

  set hRangeModifier2 [stc::create RangeModifier \
          -under $hStreamBlock \
          -ModifierMode INCR \
          -Mask "FFFF" \
          -StepValue "0010" \
          -Data "0000" \
          -RecycleCount 10 \
          -RepeatCount 0 \
          -DataType BYTE \
          -EnableStream TRUE \
          -Offset 0 \
          -OffsetReference sb1_eth.srcMac]
    
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
  	          -SchedulingMode RATE_BASED
  
  puts "\nApplying configuration"
  stc::apply

# Display the number of streams created.  Only the modified fields will]
#   be shown.
  puts "Get StreamBlock Preview Data"
  stc::perform GetPreviewData -StreamBlock $hStreamBlock
  set hStreamPreviewData [stc::get $hStreamBlock -children-PreviewData]  

  set lstStreamPreviewData [stc::get $hStreamPreviewData -Data]

# Find the first stream entry.  Always begins with "0@".
  set iIndex [lsearch -glob $lstStreamPreviewData "0@*"]
  
  set lstColumnData [lrange $lstStreamPreviewData 0 [expr $iIndex - 1]]
  set lstStreamData [lrange $lstStreamPreviewData $iIndex end]
    
  puts "\nStream Preview Information\n"
  
  puts [join [split $lstColumnData @] ,]
  
  foreach szStreamData $lstStreamData {
    puts [join [split $szStreamData @] ,]
  }  

  puts "\nStart Generator and wait for it to complete"
  stc::perform GeneratorStart -GeneratorList $hGenerator
  
  set lstCommandInfo [stc::perform GeneratorWaitForStop -GeneratorList $hGenerator -WaitTimeout 20]
  
  puts "\nGeneratorWaitForStop command information"
  
  foreach {szAttribute szValue} $lstCommandInfo {
    puts \t$szAttribute\t$szValue
  }  
  
  set lstResults {}

  puts "\n\nTest Results"
  
  foreach hResults [stc::get $hResultDataSet -ResultHandleList] {
  # Place the results into an array for easy access.  
    array set aResults [stc::get $hResults]        
  
  # Use the -Comp32 (32 bit filter used to identify the string identifier). Same number as String Id. in Preview information.  
    puts "\t$hResults\tStream Id: $aResults(-Comp32)\tMin: $aResults(-MinLatency)\tMax: $aResults(-MaxLatency)\tAvg: $aResults(-AvgLatency)"
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