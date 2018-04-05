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

# File Name:                 PduLibraryGRE.tcl
# Description:               This script demonstrates the use of
#                            the Protocol Data Unit libraries. See
#                            the section "Protocol Data Unit Objects
#                            Index" in the Spirent_TestCenter_Automation
#                            _Obj_Ref.pdf file for more information.
#                            In particular, a GRE PDU is generated. 

set ENABLE_CAPTURE 1

if {[catch {
# Load the API.
  package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.29
  set iTxSlot 10
  set iTxPort 5
  set iRxSlot 10
  set iRxPort 7

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
  
# Get generator and analyzer.  
  set hGeneratorTx [stc::get $hPortTx -children-Generator]
  set hAnalyzerRx [stc::get $hPortRx -children-Analyzer]
  
# Configure streams
  puts "Configuring streams"

# Note that the default frame configuration, which contains both an ethernet and 
#   an ipv4 header must be cleared for the GRE packet. 
#
# Note that the attribute, -frameLengthMode is set to AUTO.  This will determine the
#   appropriate frame length once the packet is created. 
  set hStreamBlock [stc::create streamBlock -under $hPortTx -frameConfig "" \
  			-frameLengthMode AUTO -maxFrameLength 1200 -FixedFrameLength 128]

# Terminology will follow RFC 2784, Generic Routing Encapsulation (GRE).

# Create the ethernetII header.
  stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
  				-dstMac 00:00:00:00:00:40 

# Create a deliver header (IPv4).
  puts "Adding delivery header"
  stc::create ipv4:IPv4 -under $hStreamBlock -name sb1_ip -sourceAddr 10.0.0.2 -destAddr 192.168.1.1 -protocol 47

# Create the GRE header using the GRE PDU library. 
#
#   Refer to the "Protocol Data Unit Objects Index" section in the 
#   Spirent_TestCenter_Automation_Obj_Ref.pdf file.  
#
# The PDU libraries have the following format:
#
#   <PDU library name>:<library object>     
#
#       e.g. ipv4:IPv4
#            ethernet:EthernetII
#
#       - where ipv4 is the PDU library name, which has a library object named IPv4
# 
#       - some PDU library names have more than one library object
#
#   This script will use a GRE PDU.  The Gre object is part of the gre PDU library.  
#     Therefore, we will use the gre:GRE syntax.  This gives us access to the 
#     attributes defined for this object.
#
  puts "Adding GRE header"
  set hGre [stc::create gre:Gre -under $hStreamBlock -name gre1 -ckPresent 1 -keyPresent 1 -routingPresent 1 -protocolType 86DD]

# We also want to set some of the other objects available in the gre PDU library, namely:
#
#       checksums, keys, and seqNums library objects
#
#     (The GRE object lists these as Children objects)

# First, lets modify the checksums.
#   Get the container object which can hold multiple checksum objects.
#
# Think -->  gre:Gre -
#                     checksums container -
#                                         GreChecksum object 

  set hChecksumContainer [stc::create checksums -under $hGre]

# Add one checksum object and modify its -value attribute.  In the documentation, the GreChecksum 
#   object is listed under the Children descriptor for the checksums object.
  stc::create GreChecksum -under $hChecksumContainer -value 16

# Add the payload packet (IPv6).
  puts "Adding payload packet"
  stc::create ipv6:IPv6 -under $hStreamBlock -name sb1_ipv6
  
# Display stream block information.
  puts "\n\nStreamBlock information"
  set lstStreamBlockInfo [stc::perform StreamBlockGetInfo -StreamBlock $hStreamBlock] 

  foreach {szName szValue} $lstStreamBlockInfo {
    puts \t$szName\t$szValue
  }
  puts \n\n
     
# Configure generator
  puts "Configuring Generator"
  set hGeneratorConfig [stc::get $hGeneratorTx -children-GeneratorConfig]
  
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
  set hAnalyzerConfig [stc::get $hAnalyzerRx -children-AnalyzerConfig]
  
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
    
# Start the analyzer and generator
  puts "Start Analyzer"
  stc::perform AnalyzerStart -AnalyzerList $hAnalyzerRx
  puts "Current analyzer state [stc::get $hAnalyzerRx -state]"
  
  puts "Start Generator"
  stc::perform GeneratorStart -GeneratorList $hGeneratorTx
  puts "Current generator state [stc::get $hGeneratorTx -state]"
      
  puts "Running for 10 seconds ..."
  after 10000
    
  puts "Current analyzer state [stc::get $hAnalyzerRx -state]"
  puts "Current generator state [stc::get $hGeneratorTx -state]"
  
  puts "Stop Analyzer"
  stc::perform AnalyzerStop -AnalyzerList $hAnalyzerRx
  
  set hAnalyzerResults [ stc::get $hAnalyzerRx -children-AnalyzerPortResults ]

  puts "Final frame statistics"
  puts "\tSignature frames:\t[stc::get $hAnalyzerResults -sigFrameCount]"
  puts "\tTotal Frame Count:\t[stc::get $hAnalyzerResults -totalFrameCount]"
  puts \n\n\n
    
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
