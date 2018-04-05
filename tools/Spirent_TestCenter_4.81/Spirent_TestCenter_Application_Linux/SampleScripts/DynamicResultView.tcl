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

# File Name:    DynamicResultView.tcl
# Description:  This script demonstrates the various ways to create
#               and subscribe a Dynamic Result View and how to get to the results
#               for processing.    

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

# Method 1 - Create DynamicResultView using PresentationResultQuery
#------------------------------------------------------------------------------
# Create the DynamicResultView
set hdrv [stc::create DynamicResultView -under project1 -ResultSourceClass Port \
            -Name "DRV created by method 1"]

# Create the PresentationResultQuery
# Specify the SelectProperties for the result properties you are 
# interested in and optionally WhereConditions and SortBy clauses.
# In this example, there will not be any result data until the
# TxBitRate is greater than or equal to 90,000,000
set hprq [stc::create PresentationResultQuery -under $hdrv \
                -SelectProperties {Port.Name StreamBlock.TxBitRate StreamBlock.RxBitRate} \
                -FromObjects project1 \
                -WhereConditions {{StreamBlock.TxBitRate >= 90000000}} \
                -LimitSize 20]

# Subscribe the DynamicResultView to begin updating the data model.
stc::perform SubscribeDynamicResultView -DynamicResultView $hdrv

# Method 2 - Create DynamicResultView using an SQL query.
#------------------------------------------------------------------------------
# To create the same DynamicResultView as above, use the following SQL query.
# The results will be returned in the select order, filtered using the specified
# WHERE clause with a size limit of 20.
set hdrv2 [stc::create DynamicResultView -under project1 -ResultSourceClass Port \
            -Name "DRV created by method 2" ]
stc::perform DefineDynamicResultViewCommand \
        -Query "SELECT Port.Name, StreamBlock.TxBitRate, StreamBlock.RxBitRate FROM project1 WHERE StreamBlock.TxBitRate >= 90000000 LIMIT 20" \
        -Target $hdrv2

# Subscribe the DynamicResultView to begin updating the data model.
stc::perform SubscribeDynamicResultView -DynamicResultView $hdrv2

# Start Traffic
puts "Starting Traffic ..."
set hGenerator [stc::get $hPortTx -children-Generator]
stc::perform GeneratorStart -GeneratorList $hGenerator

after 5000

proc expandAndPrintResultData {resultViewData nlevel} {

    if {[ string length $resultViewData ] != 0 } {
        puts "ResultData Nested Level $nlevel [string repeat \t $nlevel] [ stc::get $resultViewData -ResultData ]"
        stc::perform ExpandResultViewDataCommand -ResultViewData $resultViewData
        foreach childrvd [stc::get $resultViewData -children-ResultViewData] {
            incr nlevel
            expandAndPrintResultData $childrvd $nlevel            
        }
    }       
}

proc showResultData {hdrv expand} {
    puts "DynamicResultView: [ stc::get $hdrv -name ]\n--------------------\n"

    set hprq [lindex [stc::get $hdrv -children-PresentationResultQuery] 0]

    for { set i 0 } { $i < 5 } { incr i } {        

        # Since these are not realtime results, the view has to be manually updated.
        stc::perform UpdateDynamicResultViewCommand -DynamicResultView $hdrv

        # Wait a bit to allow time for the update to complete.
        after 2000

        if {$expand == 1} {
            # Expand all nested ResultViewData and print it to the console.
            set hrvdata [lindex [stc::get $hprq -children-ResultViewData] 0 ]
            expandAndPrintResultData $hrvdata 0
        } else {
            # Just print the top level ResultViewData       
            set hrvdata [lindex [stc::get $hprq -children-ResultViewData] 0 ]
            if {[ string length $hrvdata ] != 0 } {
                puts "ResultData: [ stc::get $hrvdata -ResultData ]"               
            }                
        }       
    }
}

# Show the result data. There will be no result data yet since
# the where clause specified is "StreamBlock.TxBitRate >= 90000000"
puts "No result data yet. Where clause is [ stc::get $hprq -WhereConditions ]"
showResultData $hdrv 0

# Change the FixedFrameLength to 2048
stc::config $hStreamBlock -FixedFrameLength 2048
stc::apply

# Now we should get result data.
puts "Result data now meets the where clause condition in the PresentationResultQuery"
showResultData $hdrv 0

# Show result data from DynamicResultView created from the SQL query.
showResultData $hdrv2 0

# Show the fully expanded result data tree.
puts "Fully expanded result data tree"
showResultData $hdrv 1

# Stop Traffic
puts "Stopping Traffic ..."
stc::perform GeneratorStop -GeneratorList $hGenerator

# Detach ports.
puts "Detaching Ports ..."
stc::perform DetachPorts -portList [list $hPortTx $hPortRx]

# Delete configuration
puts "Deleting project"
stc::delete $hProject

