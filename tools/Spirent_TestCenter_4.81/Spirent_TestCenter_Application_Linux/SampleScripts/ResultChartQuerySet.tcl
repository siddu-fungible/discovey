# Copyright (c) 2010 by Spirent Communications, Inc.
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

# File Name:    ResultChartQuerySet.tcl
# Description:  This script demonstrates how to create a ResultChartQuerySet,
#               subscribe to it get to the results for processing.

#package require SpirentTestCenter
source SpirentTestCenter.tcl

# Physical topology
set szChassisIp 10.21.0.16
set iTxSlot 2
set iTxPort 1
set iRxSlot 2
set iRxPort 2

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
puts "Attaching Ports ..."
stc::perform attachPorts -portList [list $hPortTx $hPortRx] -autoConnect TRUE

# Create 1 stream block.
puts "Configuring stream block ..."
set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true -frameConfig "" -frameLengthMode FIXED -FixedFrameLength 128]

stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
                              -dstMac 01:00:5e:01:01:01

stc::create ipv4:IPv4 -under $hStreamBlock -name sb1_ipv4 -destAddr 225.0.0.1 -sourceAddr 30.0.0.2

# Apply configuration.
puts "Applying configuration ..."
stc::apply

# Create the ResultChartQuery
set hResultChart [stc::create ResultChartQuerySet -under project1 -name "My Chart"]

# Create and configure it's ResultQuery objects.
stc::create ResultQuery -under $hResultChart \
        -ConfigClassId Generator \
        -ResultClassId GeneratorPortResults \
        -PropertyIdArray GeneratorPortResults.TotalBitRate \
        -ResultRootList $hPortTx        

stc::create ResultQuery -under $hResultChart \
        -ConfigClassId Analyzer \
        -ResultClassId AnalyzerPortResults \
        -PropertyIdArray AnalyzerPortResults.TotalBitRate \
        -ResultRootList $hPortRx

# Subscribe the ResultChartQuery to begin updating the data model.
stc::perform ResultDataSetSubscribe -ResultDataSet $hResultChart 

# Start Traffic
puts "Starting Traffic ..."
set hGenerator [stc::get $hPortTx -children-Generator]
stc::perform GeneratorStart -GeneratorList $hGenerator

after 5000

proc showBitRate {hResultChart} {
    puts "ResultChartQuerySet: [ stc::get $hResultChart -name ]"
    for { set i 0 } { $i < 50 } { incr i } {

        # Iterate Results ...
        set lstResults [stc::get $hResultChart -ResultHandleList]
        foreach hResult $lstResults {
            # Get the RealtimeChartSeries ...
            set hChartSeries [lindex [stc::get $hResult -children-RealtimeChartSeries] 0]
            
            set dstream [stc::get $hChartSeries -DataStream]
            # RealtimeChartSeries will have 0-n DataStreams
            if {[llength $dstream] != 0} {

                puts "[stc::get $hResult -PortUiName] [stc::get $hChartSeries -DataSourcePropertyId]"

                # Iterate the DataStreams which contains the x,y data pairs. x = timestamp, y = data value.
                foreach dstream [stc::get $hChartSeries -DataStream] {

                    # Convert the raw timestamp to a display time for easier viewing ...
                    set secs [lindex [ split $dstream , ] 0 ]
                    puts "[string repeat \t 6][clock format [expr {round($secs)}] -format {%H:%M:%S}], [lindex [ split $dstream , ] 1 ]"
                }
            }
        }
        
        after 1000
    }
}

showBitRate $hResultChart

# Stop Traffic
puts "Stopping Traffic ..."
stc::perform GeneratorStop -GeneratorList $hGenerator

# Detach ports.
puts "Detaching Ports ..."
stc::perform DetachPorts -portList [list $hPortTx $hPortRx]

# Delete configuration
puts "Deleting project"
stc::delete $hProject

