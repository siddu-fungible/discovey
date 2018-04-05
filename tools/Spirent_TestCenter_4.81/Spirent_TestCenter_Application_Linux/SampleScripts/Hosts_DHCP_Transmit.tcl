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

# File Name:                 Hosts_DHCP_Transmit.tcl
# Description:               This script demonstrates the use of hosts with the DHCP
#                            protocol.  One side uses DHCP, the other does not.  The
#                            script will then transmit traffic between the hosts.
# 

set ENABLE_CAPTURE 1
set SEND_TRAFFIC 1

if {[catch {   
# Load the API.
  package require SpirentTestCenter

  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Equipment variables
  set szChassisAddr 10.100.33.137
  set iTxSlot 1
  set iTxPort 1
  set iRxSlot 1
  set iRxPort 2

# Emulation Variables
  set txGatewayIpAddr "20.0.0.1"
  set rxIpAddr "30.0.0.2"
  set rxGatewayIpAddr "30.0.0.1"
  
  set txMacAddr "00.00.11.00.00.11"
  set rxMacAddr "00.00.22.00.00.22"

# Create the root project object
  set hProject [stc::create project]

# Create ports.
  puts "\nCreating ports"
  set hPortTx [stc::create port -under $hProject -location //$szChassisAddr/$iTxSlot/$iTxPort]
  set hPortRx [stc::create port -under $hProject -location //$szChassisAddr/$iRxSlot/$iRxPort]

# Configure Ethernet Copper interface.
  set hPortTxCopperInterface [stc::create EthernetCopper -under $hPortTx]
  set hPortRxCopperInterface [stc::create EthernetCopper -under $hPortRx]

# Configure DHCP port settings.
  set hDhcpv4PortConfig [stc::get $hPortTx -children-Dhcpv4PortConfig]
  stc::config $hDhcpv4PortConfig \
          -MaxMsgSize "576" \
          -LeaseTime "60" \
          -MsgTimeout "60" \
          -RetryCount "4" \
          -RequestRate "100.000000" \
          -ReleaseRate "100.000000" \
          -StartingXid "0" \
          -OutstandingSessionCount "1000" \
          -Active "TRUE" \
          -Name "Dhcpv4PortConfig 1"

# Show port attributes.
  set lstPortInfo [stc::get $hPortTx]
  
  puts "\nTx port information"
  
  foreach {szAttribute szValue} $lstPortInfo {
    puts \t$szAttribute\t$szValue
  }
                                 
# Create the tx side host emulation
  set hHostTx [stc::create Host -under $hProject -DeviceCount 10]
  
# Create an Ethernet/Ipv4 protocol stack.
  set hEthTxIf [stc::create "EthIIIf" \
          -under $hHostTx \
          -sourceMac $txMacAddr ]

  set hIPv4TxIf [stc::create "Ipv4If" \
  	-under $hHostTx \
  	-gateway $txGatewayIpAddr \
    -AddrResolver "Dhcpv4" \
    -ResolveGatewayMac TRUE \
    -GatewayMacResolver default]

# Configure the DHCP settings. (Use the defaults for now)  
  set hDhcpv4BlockConfig [stc::create Dhcpv4BlockConfig -under $hHostTx]

# Affiliate the host with the protocol stack.
  stc::config $hHostTx -AffiliationPort-targets $hPortTx

# Specify the top of the stack.  
  stc::config $hHostTx -TopLevelIf-targets $hIPv4TxIf

# Specify the top level interface facing the DUT.
  stc::config $hHostTx -PrimaryIf-targets $hIPv4TxIf
  
# Order the remaining stack items.  
  stc::config $hIPv4TxIf -stackedOnEndpoint-targets $hEthTxIf

  stc::config $hDhcpv4BlockConfig -UsesIf-targets $hIPv4TxIf

  puts "\nApplying configuration"
  stc::apply

                
  puts "\nDHCP IPv4 block configuration information"
  set lstDhcpv4BlockConfig [stc::get $hDhcpv4BlockConfig]  
  
  foreach {szAttribute szValue} $lstDhcpv4BlockConfig {
    puts \t$szAttribute\t$szValue
  }
 
# Create the rx side host emulation
  set hHostRx [stc::create Host -under $hProject -DeviceCount 1]

  set hEthRxIf [stc::create "EthIIIf" \
          -under $hHostRx \
          -sourceMac $rxMacAddr ]
  
  set hIPv4RxIf [stc::create "Ipv4If" \
  	-under $hHostRx \
  	-address $rxIpAddr \
  	-gateway $rxGatewayIpAddr \
  	-stackedOnEndpoint-targets $hEthRxIf]

# Specify the top of the stack and the top level interface facing the DUT.  
  stc::config $hHostRx -TopLevelIf-targets $hIPv4RxIf -PrimaryIf-targets $hIPv4RxIf

# Affiliate the host with a port.
  stc::config $hHostRx -AffiliationPort-targets $hPortRx

  puts "\nApplying configuration"
  stc::apply

                
# Attach ports.
  puts "\nAttaching Ports ..."
  stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE


# Check the link status.
  puts "Checking link status\n"
  
  for {set i 0} {$i < 5} {incr i} {
    set szTxStatus [stc::get $hPortTxCopperInterface -LinkStatus]
    set szRxStatus [stc::get $hPortRxCopperInterface -LinkStatus]
    puts "\nTx Status\t$szTxStatus\tRx Status\t$szRxStatus"
    if {[string equal $szTxStatus UP] && [string equal $szRxStatus UP]} { break }
    after 1000
  }

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

# Subscribe to realtime results.  
  stc::subscribe -Parent $hProject \
      -configType Analyzer \
      -resultType AnalyzerPortResults \
      -filenameprefix AnalyzerPortResults

  stc::subscribe -Parent $hProject \
      -configType Generator \
      -resultType GeneratorPortResults \
      -filenameprefix GeneratorPortResults

  stc::subscribe -Parent $hProject \
      -configType StreamBlock \
      -resultType RxStreamSummaryResults \
      -viewAttributeList [list FrameRate FrameCount] \
      -filenameprefix RxStreamSummaryResults

  stc::subscribe -Parent $hProject \
      -configType Dhcpv4BlockConfig \
      -resultType Dhcpv4BlockResults \
      -filenameprefix Dhcpv4BlockResults

  stc::subscribe -Parent $hProject \
      -configType Port \
      -resultType Dhcpv4PortResults \
      -filenameprefix Dhcpv4PortResults

# Configure Capture.
  if { $ENABLE_CAPTURE } {
    puts "\nStarting Capture..."
  
  # Create a capture object. Automatically created.
    set hCapture [stc::get $::hPortRx -children-capture]
    stc::config $hCapture -mode REGULAR_MODE -srcMode TX_RX_MODE  
    stc::perform CaptureStart -captureProxyId $hCapture  
  }

# Start the DHCP binding.
  puts "\nApplying configuration"
  stc::apply


  if {[catch {   
    puts "Start DHCP bindings ..."
    puts "Wait 10 seconds for binding to complete."
    stc::perform Dhcpv4Bind -BlockList $hDhcpv4BlockConfig
    after 10000
    
  # Display the DCHP Port Results information.     
    puts "\nDHCP Port Results information"
    set hDhcpv4PortResults [stc::get $hDhcpv4PortConfig -children-dhcpv4portresults]
    set lstDhcpPortInfo [stc::get $hDhcpv4PortResults]  
      
    foreach {szAttribute szValue} $lstDhcpPortInfo {
      puts \t$szAttribute\t$szValue
    }
  
  # Check the success rate.
    if {[stc::get $hDhcpv4PortResults -SuccessPercent] == 100.0} {
    # Display the DCHP Block Results information.
      puts "\nDHCP Block Results information"
      set hDhcpv4BlockResults [stc::get $hDhcpv4BlockConfig -children-dhcpv4blockresults]
      set lstDhcpBlockInfo [stc::get $hDhcpv4BlockResults]  
        
      foreach {szAttribute szValue} $lstDhcpBlockInfo {
        puts \t$szAttribute\t$szValue
      }
    
    # Display the DCHP session information.
      puts "\nDHCP Session information"
    
    # This will automatically generate a file named sessions.csv containing the session information.
      stc::perform Dhcpv4SessionInfo -BlockList $hDhcpv4BlockConfig
      
    # There will be a session result object for each DHCP host created. See the -DeviceCount 
    #   attribute when the Hosts were created.  
      set lstDhcpv4SessionResults [stc::get $hDhcpv4BlockConfig -children-dhcpv4sessionresults]
      
      foreach hDhcpv4SessionResult $lstDhcpv4SessionResults {
        set lstDhcpSessionInfo [stc::get $hDhcpv4SessionResult]  
          
        foreach {szAttribute szValue} $lstDhcpSessionInfo {
          puts \t$szAttribute\t$szValue
        }
        puts \n
      }

    # Start ArpNd
      puts "\nStart Arp"
      stc::perform ArpNdStart -HandleList [list $hPortRx $hPortTx]
    
    # Wait for Arps to complete.
      puts "\nwaiting 5 seconds ..."
      after 5000
  
        
      if {$SEND_TRAFFIC} {
      # Create traffic.
        puts "\nConfiguring stream blocks ..."
        set hStreamBlockTx [stc::create streamBlock -under $hPortTx -insertSig true \
        			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]
      
        set hStreamBlockRx [stc::create streamBlock -under $hPortRx -insertSig true \
        			-frameConfig "" -frameLengthMode FIXED -maxFrameLength 1200 -FixedFrameLength 128]
      
      # Bind the streamBlocks with their interface targets.
        stc::config $hStreamBlockTx -SrcBinding-targets $hIPv4TxIf -DstBinding-targets $hIPv4RxIf
        stc::config $hStreamBlockRx -SrcBinding-targets $hIPv4RxIf -DstBinding-targets $hIPv4TxIf
        
      # Configure generator
        puts "\nConfiguring Generators"
        
        set hGenerator [stc::get $hPortTx -children-Generator]
        lappend lstGenerators $hGenerator
        
        set hGeneratorConfig [stc::get $hGenerator -children-GeneratorConfig]
        
        stc::config $hGeneratorConfig \
                    -DurationMode BURSTS \
        	          -BurstSize 1 \
                    -Duration 100 \
        	          -LoadMode FIXED \
        	          -FixedLoad 15 \
                    -LoadUnit PERCENT_LINE_RATE \
        	          -SchedulingMode RATE_BASED
      
        set hGenerator [stc::get $hPortRx -children-Generator]
        lappend lstGenerators $hGenerator
        
        set hGeneratorConfig [stc::get $hGenerator -children-GeneratorConfig]
        
        stc::config $hGeneratorConfig \
                    -DurationMode BURSTS \
        	          -BurstSize 1 \
                    -Duration 100 \
        	          -LoadMode FIXED \
        	          -FixedLoad 10 \
                    -LoadUnit PERCENT_LINE_RATE \
        	          -SchedulingMode RATE_BASED
            
        puts "\nApplying configuration"
        stc::apply
      
      # Here is a neat trick to verify the contents of the packets being transmitted.  Recall, that the
      # firmware cannot capture transmitted data plane packets.  By configuring the interface to loopback,
      # we are capturing what we are sending out.  Be aware that these packets will not be transmitted to a
      # device, since they are being loopbacked to the firmware.
      
      # Switch to the loopback mode to capture transmitted packets.
      #  stc::config $hPortRxCopperInterface -DataPathMode LOCAL_LOOPBACK
        
        stc::apply
                      
        puts "\nStart Generators"
        stc::perform GeneratorStart -GeneratorList $lstGenerators
      
        puts "\nTransmit for 10 seconds ..."
        after 10000
      
        puts "\nStop Generators"
        stc::perform GeneratorStop -GeneratorList $lstGenerators
      }
      
    } else {
      puts "Failed to bind DHCP sessions."
    }
  } szError] } {
	  puts "Error occurred:\n\t$szError"
  
  # Display the DCHP session information.
    puts "\nDHCP Session information"
  
    stc::perform Dhcpv4SessionInfo -BlockList $hDhcpv4BlockConfig
    
  # There will be a session result object for each DHCP host created. See the -DeviceCount 
  #   attribute when the Hosts were created.  
    set lstDhcpv4SessionResults [stc::get $hDhcpv4BlockConfig -children-dhcpv4sessionresults]
    
    foreach hDhcpv4SessionResult $lstDhcpv4SessionResults {
      set lstDhcpSessionInfo [stc::get $hDhcpv4SessionResult]  
        
      foreach {szAttribute szValue} $lstDhcpSessionInfo {
        puts \t$szAttribute\t$szValue
      }
      puts \n
    }
  }
  
# Save the capture.
  if { $ENABLE_CAPTURE } {
    puts "\nRetrieving Captured frames..."
    
    stc::perform CaptureStop -captureProxyId $hCapture
    
  # Save captured frames to a file.
    stc::perform CaptureDataSave -captureProxyId $hCapture -FileName "capture.pcap" -FileNameFormat PCAP -IsScap FALSE
    
    puts "Captured frames:\t[stc::get $hCapture -PktCount]"
  } 

# Detach ports.
  stc::perform detachPorts -portList [list $hPortTx $hPortRx]
  
# Delete configuration
  puts "\nDeleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}