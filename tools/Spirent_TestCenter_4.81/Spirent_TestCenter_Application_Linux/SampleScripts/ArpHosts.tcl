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

# File Name:                 ArpHosts.tcl
# Description:               This script demonstrates how to create hosts
#                            under the project and arp from them.                           
# 

set ENABLE_CAPTURE 1

if {[catch {   
# Load the API.
  package require SpirentTestCenter

# Retrieve and display the current API version.
  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.29
  set iTxSlot 10
  set iTxPort 1
  set iRxSlot 10
  set iRxPort 2


# Emulation Variables
  set txIpAddr "10.1.1.1"
  set rxIpAddr "10.1.1.10"
  
  set txMacAddr "00.00.11.00.00.11"
  set rxMacAddr "00.00.22.00.00.22"


# Create the root project object
  set hProject [stc::create project]

# Set up the ARP configuration
  set hArpNdConfig [stc::get $hProject -children-ArpNdConfig]

# Create ports.
  puts "\nCreating ports"
  set hPortTx [stc::create port -under $hProject -location //$szChassisAddr/$iTxSlot/$iTxPort \
          -useDefaultHost FALSE ]
  set hPortRx [stc::create port -under $hProject -location //$szChassisAddr/$iRxSlot/$iRxPort \
          -useDefaultHost FALSE ]

# Show port attributes.
  set lstPortInfo [stc::get $hPortTx]
  
  puts "\nTx port information"
  
  foreach {szAttribute szValue} $lstPortInfo {
    puts \t$szAttribute\t$szValue
  }

# METHOD 1.  Use commands to connect, reserve, and setup Port Mappings.
# Connect to a chassis
#  puts "Connecting $szChassisAddr"	
#  stc::connect $szChassisAddr
	
# Reserve
#  puts "Reserving $szChassisAddr/$iTxSlot/$iTxPort and $szChassisAddr/$iRxSlot/$iRxPort"
#  stc::reserve [list $szChassisAddr/$iTxSlot/$iTxPort $szChassisAddr/$iRxSlot/$iRxPort]
                                 
# Create the tx side host emulation
  set hHostTx [stc::create Host -under $hProject]
  
# Create an Ethernet/Ipv4 protocol stack.
  set hEthTxIf [stc::create "EthIIIf" \
          -under $hHostTx \
          -sourceMac $txMacAddr ]

  set hIPv4TxIf [stc::create "Ipv4If" \
  	-under $hHostTx \
  	-address $txIpAddr \
  	-gateway $rxIpAddr] \

# Specify the top of the stack.  
  stc::config $hHostTx -TopLevelIf-targets $hIPv4TxIf

# Order the remaining stack items.  
  stc::config $hIPv4TxIf -stackedOnEndpoint-targets $hEthTxIf

# Specify the top level interface facing the DUT.
  stc::config $hHostTx -PrimaryIf-targets $hIPv4TxIf
  
# Affiliate the host with a port.
  stc::config $hHostTx -AffiliationPort-targets $hPortTx
 
# Create the rx side host emulation.
  set hHostRx [stc::create Host -under $hProject]

  set hEthRxIf [stc::create "EthIIIf" \
          -under $hHostRx \
          -sourceMac $rxMacAddr ]
  
  set hIPv4RxIf [stc::create "Ipv4If" \
  	-under $hHostRx \
  	-address $rxIpAddr \
  	-gateway $txIpAddr \
  	-stackedOnEndpoint-targets $hEthRxIf]

  stc::config $hHostRx -TopLevelIf-targets $hIPv4RxIf -PrimaryIf-targets $hIPv4RxIf

# Affiliate the host with a port.
  stc::config $hHostRx -AffiliationPort-targets $hPortRx

# Configure Capture Settings.
  stc::config $hPortRx.capture -mode REGULAR_MODE -srcMode TX_RX_MODE

#
#
# Note location of the SetupPortMappings/attachPorts command.  It is located
#
#   AFTER configuring the hosts.  Move these commands before 1 or both
# 
#   of the hosts to see the location's effect on the test.
#
#

# METHOD 1.  Use commands to connect, reserve, and setup Port Mappings.
# Create the mapping between the physical ports and their logical 
#   representation in the test configuration.
#  puts "Set up port mappings"
#  stc::perform SetupPortMappings                                 

# METHOD 2.  Use a single command to attachPorts (connect, reserve, and setup Port Mappings)
# Attach ports.
  puts "\nAttaching Ports ..."
  stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE

  puts "Applying configuration"
  stc::apply

# Show Tx host attributes.
  puts "\nTx Host information"
  set lstHostInfo [stc::get $hHostTx]
  foreach {szAttribute szValue} $lstHostInfo {
    puts \t$szAttribute\t$szValue
  }

# Show Rx host attributes.
  puts "\nRx Host information"
  set lstHostInfo [stc::get $hHostRx]
  foreach {szAttribute szValue} $lstHostInfo {
    puts \t$szAttribute\t$szValue
  }
  
# Display some stats before the ArpNd command begins.
  puts "\nBefore Arp/Nd starts"
  puts "\t$hHostTx : EthIIIf.SourceMac [stc::get $hHostTx -EthIIIf.SourceMac ]"
  puts "\t$hHostTx : Ipv4If.Address [stc::get $hHostTx -Ipv4If.Address]"
  puts "\t$hHostTx : Ipv4If.GatewayIP [stc::get $hHostTx -Ipv4If.Gateway]"
  puts "\t$hHostTx : Ipv4If.GatewayMac [stc::get $hHostTx -Ipv4If.GatewayMac]"
  puts "\n\t$hHostRx : EthIIIf.SourceMac [stc::get $hHostRx -EthIIIf.SourceMac ]"
  puts "\t$hHostRx : Ipv4If.Address [stc::get $hHostRx -Ipv4If.Address]"
  puts "\t$hHostRx : Ipv4If.GatewayIP [stc::get $hHostRx -Ipv4If.Gateway]"
  puts "\t$hHostRx : Ipv4If.GatewayMac [stc::get $hHostRx -Ipv4If.GatewayMac]"


# Subscribe to realtime results.  
  stc::subscribe -Parent $hProject \
      -configType Port \
      -resultType ArpNdResults \
      -resultParent $hPortTx \
			-viewAttributeList [list RxArpReplyCount RxArpRequestCount TxArpReplyCount TxArpRequestCount] \
      -filenameprefix ArpNdResultsFile

# Configure Capture.
  if { $ENABLE_CAPTURE } {
     puts "\nStarting Capture..."
  
  # Create a capture object. Automatically created.
     set hCaptureRx [stc::get $::hPortRx -children-capture]
     stc::config $hCaptureRx -mode REGULAR_MODE -srcMode TX_RX_MODE  
     stc::perform CaptureStart -captureProxyId $hCaptureRx  
  }


# Start ArpNd
  puts "\nStart Arp"
  stc::perform ArpNdStart -HandleList [list $hPortRx $hPortTx]

# Wait for Arps to complete.
  puts "\nwaiting 5 seconds ..."
  after 5000

# Display some stats after the ArpNd command finishes.
  puts "\nAfter Arp/Nd "
  puts "\t$hHostTx : EthIIIf.SourceMac [stc::get $hHostTx -EthIIIf.SourceMac ]"
  puts "\t$hHostTx : Ipv4If.Address [stc::get $hHostTx -Ipv4If.Address]"
  puts "\t$hHostTx : Ipv4If.GatewayIP [stc::get $hHostTx -Ipv4If.Gateway]"
  puts "\t$hHostTx : Ipv4If.GatewayMac [stc::get $hHostTx -Ipv4If.GatewayMac]"
  puts "\n\t$hHostRx : EthIIIf.SourceMac [stc::get $hHostRx -EthIIIf.SourceMac ]"
  puts "\t$hHostRx : Ipv4If.Address [stc::get $hHostRx -Ipv4If.Address]"
  puts "\t$hHostRx : Ipv4If.GatewayIP [stc::get $hHostRx -Ipv4If.Gateway]"
  puts "\t$hHostRx : Ipv4If.GatewayMac [stc::get $hHostRx -Ipv4If.GatewayMac]"

# Display the resolved mac address on the Tx host.
  puts "\nTx side mac resolution information:"
  puts "\tresolved mac:[stc::get $hHostTx -Ipv4If.GatewayMac] "
  puts "\tresolved state:[stc::get $hHostTx -Ipv4If.GatewayMacResolveState] "

# Verify the results.

# Verify that the ARP worked.
  if { [stc::get $hHostTx -Ipv4If.GatewayMac] != [stc::get $hHostRx -EthIIIf.SourceMac ] } {
  	puts "Gateway [stc::get $hHostTx -Ipv4If.GatewayMac] does not match source MAC  [stc::get $hHostRx -EthIIIf.SourceMac ]"
  }

# Verify the resolved state.
  if { [stc::get $hHostTx -Ipv4If.GatewayMacResolveState] != "RESOLVE_DONE" } {
  	puts "Resolve state invalid: [stc::get $hHostTx -Ipv4If.GatewayMacResolveState]"
  } 

# Display the resolved mac address on the Rx host.
  puts "\nRx side mac resolution information:"
  puts "\tresolved mac:[stc::get $hHostRx -Ipv4If.GatewayMac] "
  puts "\tresolved state:[stc::get $hHostRx -Ipv4If.GatewayMacResolveState] "

# Verify the results.

# Verify that the ARP worked.
  if { [stc::get $hHostRx -Ipv4If.GatewayMac] != [stc::get $hHostTx -EthIIIf.SourceMac ] } {
  	puts "Gateway [stc::get $hHostRx -Ipv4If.GatewayMac] does not match source MAC  [stc::get $hHostTx -EthIIIf.SourceMac ]"
  }

# Verify the resolved state.
  if { [stc::get $hHostRx -Ipv4If.GatewayMacResolveState] != "RESOLVE_DONE" } {
  	puts "Resolve state invalid: [stc::get $hHostRx -Ipv4If.GatewayMacResolveState]"
  } 

# Update ArpCache
  puts "\nUpdating ArpCache tables on the ports"
  stc::perform ArpNdUpdateArpCache -HandleList [list $hPortTx $hPortRx]

# View the ARP cache table for each port.
  set txArpCacheHandle [stc::get $hPortTx -children-arpcache]
  set rxArpCacheHandle [stc::get $hPortRx -children-arpcache]

  puts "\nRetrieving arp cache table information"
  puts "\tTx arp cache table [stc::get $txArpCacheHandle -ArpCacheData]"
  puts "\tRx arp cache table [stc::get $rxArpCacheHandle -ArpCacheData]"

# Save the capture.
  if { $ENABLE_CAPTURE } {
    puts "\nRetrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCaptureRx
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCaptureRx -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCaptureRx -PktCount]"
  } 

  stc::perform detachPorts -portList [list $hPortTx $hPortRx]
  
# Delete configuration
  puts "\nDeleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}