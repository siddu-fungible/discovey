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

# File Name:                 Multicast.tcl
# Description:               This script demonstrates how to create
#                            multicast clients on one side and 
#                            multicast sources on the other.                           
# 

set ENABLE_CAPTURE 1

if {[catch {   
# Load the API.
  package require SpirentTestCenter

  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.137
  set iClientSlot 1
  set iClientPort 1
  set iSourceSlot 1
  set iSourcePort 2

# Create the root project object
  set hProject [stc::create project]

# Create ports.
  puts "\nCreating ports"
  set hPortClient [stc::create port -under $hProject -location //$szChassisAddr/$iClientSlot/$iClientPort \
          -useDefaultHost FALSE ]
  set hPortSource [stc::create port -under $hProject -location //$szChassisAddr/$iSourceSlot/$iSourcePort \
          -useDefaultHost FALSE ]

# Show port attributes.
  set lstPortInfo [stc::get $hPortClient]
  
  puts "\nClient port information"
  
  foreach {szAttribute szValue} $lstPortInfo {
    puts \t$szAttribute\t$szValue
  }

# Configure the port's IGMP settings.
  set hIgmpPort [stc::get $hPortClient -children-IgmpPortConfig]
  set lstIgmpPortInfo [stc::get $hIgmpPort]

  puts "\nIgmp port information"
  
  foreach {szAttribute szValue} $lstIgmpPortInfo {
    puts \t$szAttribute\t$szValue
  }
                                 
# Create the client side host emulation
  set hHostClient [stc::create Host -under $hProject -DeviceCount 1]
  
  puts \nhHostClient\t$hHostClient\n
    
# Create an Ethernet/Ipv4 protocol stack.
  set hEthClientIf [stc::create "EthIIIf" \
          -under $hHostClient]

  set hIPv4ClientIf [stc::create "Ipv4If" \
  	-under $hHostClient \
  	-address 20.0.0.2 \
  	-gateway 20.0.0.1]

# Configure the multicast implementation.
  set hIgmpHostConfig [stc::create IgmpHostConfig -under $hHostClient]
  stc::config $hIgmpHostConfig -Version IGMP_V2
  
# Configure the multicast group memberships.
  set hIgmpGroupMembership [stc::create "IgmpGroupMembership" -under $hIgmpHostConfig]

  set hIpv4NetworkBlock [stc::get $hIgmpGroupMembership -children-Ipv4NetworkBlock]
  
  stc::config $hIpv4NetworkBlock \
          -StartIpList "225.0.0.1" \
          -PrefixLength "24" \
          -NetworkCount "1" \
          -AddrIncrement "1"  

  set hIpv4Group [stc::create "Ipv4Group" -under $hProject]
  
  set hIpv4NetworkBlockGroup [stc::get $hIpv4Group -children-Ipv4NetworkBlock]
  
  stc::config $hIpv4NetworkBlockGroup \
          -StartIpList "225.0.0.1" \
          -PrefixLength "24" \
          -NetworkCount "1" \
          -AddrIncrement "1"  
  
# Specify the top of the stack.  
  stc::config $hHostClient -TopLevelIf-targets $hIPv4ClientIf -PrimaryIf-targets $hIPv4ClientIf

# Order the remaining stack items.  
  stc::config $hIPv4ClientIf -stackedOnEndpoint-targets $hEthClientIf
  
# Affiliate the host with a port.
  stc::config $hHostClient -AffiliationPort-targets $hPortClient

  stc::config $hIgmpHostConfig -UsesIf-targets [list $hIPv4ClientIf]

# IGMP Group Memberships do not use the network block created under the GroupMembership object.
#   Instead, a separate IPv4Group object's network block is required.  
  stc::config $hIgmpGroupMembership -SubscribedGroups-targets $hIpv4Group 
  
# Show Client host attributes.
  puts "\nClient Host information"
  set lstHostInfo [stc::get $hHostClient]
  foreach {szAttribute szValue} $lstHostInfo {
    puts \t$szAttribute\t$szValue
  }

  puts "\nIgmp Host Config information"
  set lstIgmpHostConfigInfo [stc::get $hIgmpHostConfig]
  foreach {szAttribute szValue} $lstIgmpHostConfigInfo {
    puts \t$szAttribute\t$szValue
  }

  puts "\nIgmp Group Membership information"
  set lstIgmpGroupMembershipInfo [stc::get $hIgmpGroupMembership]
  foreach {szAttribute szValue} $lstIgmpGroupMembershipInfo {
    puts \t$szAttribute\t$szValue
  }

  puts "\nNetwork Block information"
  set lstNetworkBlockInfo [stc::get $hIpv4NetworkBlock]
  foreach {szAttribute szValue} $lstNetworkBlockInfo {
    puts \t$szAttribute\t$szValue
  }

# Attach ports.
  puts "\nAttaching Ports ..."
  stc::perform attachPorts -portList [list $hPortClient $hPortSource] -autoConnect TRUE
  
  puts "\nApplying configuration"
  stc::apply


# Subscribe to realtime results.  
  stc::subscribe -Parent $hProject \
      -configType IgmpPortConfig \
      -resultType IgmpPortResults \
      -filenameprefix IgmpPortResults
  
  stc::subscribe -Parent $hProject \
      -configType IgmpHostConfig \
      -resultType IgmpHostResults \
      -filenameprefix IgmpHostResults

  stc::subscribe -Parent $hProject \
      -configType IgmpGroupMembership \
      -resultType IgmpGroupMembershipResults \
      -filenameprefix IgmpGroupMembershipResults

  stc::subscribe -Parent $hProject \
     -configType analyzer \
     -resultType AnalyzerPortResults \
     -filenameprefix AnalyzerPortResults
     
  stc::subscribe -parent [stc::get system1 -children-Project] \
     -configType generator \
     -resultType GeneratorPortResults \
     -filenameprefix GeneratorPortResults
  
# Configure Capture.
  if { $ENABLE_CAPTURE } {
    puts "\nStarting Capture..."

  # Retrieve the capture object.
    set hCaptureClient [stc::get $::hPortClient -children-capture]
    stc::config $hCaptureClient -mode REGULAR_MODE -srcMode TX_RX_MODE  
    stc::perform CaptureStart -captureProxyId $hCaptureClient  
  }

# Start IGMP joins.  
  puts "\nStart Joins"
  stc::perform IgmpMldJoinGroups -BlockList [list $hIgmpHostConfig]

# Wait for Joins to complete.
  puts "\nwaiting 5 seconds ..."
  after 5000

# Create multicast traffic from the source side.
  puts "\nConfiguring stream blocks ..."
  
  set hStreamBlockSource [stc::create streamBlock -under $hPortSource -insertSig true \
  			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]

  puts "Adding headers"
  stc::create ethernet:EthernetII -under $hStreamBlockSource -name sb1_eth -srcMac 00:00:20:00:00:00 \
				-dstMac 01:00:5e:01:01:01 

  stc::create ipv4:IPv4 -under $hStreamBlockSource -name sb1_ipv4 -destAddr 225.0.0.1 -sourceAddr 30.0.0.2 
  
# Configure generator
  puts "\nConfiguring Generators"
  
  set hGeneratorSource [stc::get $hPortSource -children-Generator]
  
  set hGeneratorConfig [stc::get $hGeneratorSource -children-GeneratorConfig]
  
  stc::config $hGeneratorConfig \
              -DurationMode BURSTS \
  	          -BurstSize 1 \
              -Duration 300 \
  	          -LoadMode FIXED \
  	          -FixedLoad 25 \
              -LoadUnit PERCENT_LINE_RATE \
  	          -SchedulingMode PORT_BASED

  puts "\nApplying configuration"
  stc::apply

  puts "\nStart Generators"
  stc::perform GeneratorStart -GeneratorList $hGeneratorSource

  puts "\nStop Generators after transmission completed."
  stc::perform GeneratorWaitForStop -GeneratorList $hGeneratorSource  -WaitTimeout 120


# Start IGMP leaves. 
  puts "\nStart Leaves"
  stc::perform IgmpMldLeaveGroups -BlockList [list $hIgmpHostConfig]

# Save the capture.
  if { $ENABLE_CAPTURE } {
    puts "\nRetrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCaptureClient
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCaptureClient -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hPortClient.capture -PktCount]"
  } 

  stc::perform detachPorts -portList [list $hPortClient $hPortSource]
  
# Delete configuration
  puts "\nDeleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}