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

# File Name:    ProcessingRealtimeResults.tcl
# Description:  This script demonstrates special realtime results
#               processing considerations.

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

# Create 250 stream blocks.
puts "Configuring stream blocks 1 - 250 ..."
for {set i 0} {$i < 250} {incr i} {
    set hStreamBlock [stc::create streamBlock -under $hPortTx -insertSig true -frameConfig "" -frameLengthMode FIXED -FixedFrameLength 128]

    stc::create ethernet:EthernetII -under $hStreamBlock -name sb1_eth -srcMac 00:00:20:00:00:00 \
                                  -dstMac 01:00:5e:01:01:01
    
    stc::create ipv4:IPv4 -under $hStreamBlock -name sb1_ipv4 -destAddr 225.0.0.1 -sourceAddr 30.0.0.2
}

# Apply configuration.
puts "Applying configuration ..."
stc::apply

# Subscribe ...
puts "Create and subscribe a ResultDataSet ..."
set hResultDataSetTxStreamResults [stc::subscribe -Parent $hProject \
           -configType streamblock \
           -resulttype txstreamresults \
           -viewAttributeList "bitrate" ]

stc::config $hResultDataSetTxStreamResults -Name "My ResultDataSet"

# The subscribe command can optionally write results to a CSV file at a specified interval.
# This is good for post processing of results.
# For in memory processing, you don't need need this.
# This example writes results every second to a CSV file named my_results.csv
set hResultDataSetLogToCSV [stc::subscribe -Parent $hProject \
           -configType streamblock \
           -resulttype txstreamresults \
           -viewAttributeList "bitrate" \
           -filenamePrefix "my_results" \
           -interval 1]

stc::config $hResultDataSetLogToCSV -Name "My ResultDataSet Logging to CSV"


# Start Traffic
puts "Starting Traffic ..."
set hGenerator [stc::get $hPortTx -children-Generator]
stc::perform GeneratorStart -GeneratorList $hGenerator

after 5000

proc processResults {hResultDataSet} {
    puts "ResultDataSet: [ stc::get $hResultDataSet -name ]"
    set bitrate 0
    set threshold 999999
    set hCurResult ""

    # Looking for a streamblock bitrate matching the given threshold.
    while {$bitrate <= $threshold} {
                
        # Get the total number of pages ...
        set totalPage [stc::get $hResultDataSet -TotalPageCount]

        # And iterate all the pages.
        for {set pageNum 1} {$pageNum <= $totalPage} {incr pageNum} {

            # Move to the next page ...
            stc::config $hResultDataSet -PageNumber $pageNum

            # Don't forget to apply
            stc::apply

            # Give the BLL a chance to create Result objects for the current page ...
            # If rates are zero, consider increasing this time to 3 seconds.
            after 2500

            puts "---------- Page number [stc::get $hResultDataSet -PageNumber] ----------"

            # Iterate all the results for the current page ...
            set lstResults [stc::get $hResultDataSet -ResultHandleList]
            foreach hResult $lstResults {

                set hCurResult $hResult
                set bitrate [ stc::get $hResult -bitrate ]
                
                puts "BitRate: [stc::get $hResult -PortUiName] $hResult $bitrate"
                                
                if {$bitrate > $threshold} {
                    break
                }                
            }
        }

        update
    }

    # And the threshold was found ...
    # To get the associated Streamblock use the ResultChild relationship ...
    set hStreamblock [lindex [ stc::get $hCurResult -ResultChild-sources] 0]
    puts "Threshold $threshold reached - txstreamresults $hStreamblock - bitrate $bitrate"
}

after 10000 { 
    # Change the FixedFrameLength of the last stream block ...    
    set hlastStreamBlock [lindex [stc::get $hPortTx -children-streamblock] end]
    stc::config $hlastStreamBlock -FixedFrameLength 2048    
}

# Begin in memory result processing ...
puts "Begin result processing ..."
processResults $hResultDataSetTxStreamResults

# Stop Traffic
puts "Stopping Traffic ..."
stc::perform GeneratorStop -GeneratorList $hGenerator

# Detach ports.
puts "Detaching Ports ..."
stc::perform DetachPorts -portList [list $hPortTx $hPortRx]

# Post process results that were written to CSV.
# Form the absolute path for the CSV file. See TestResultSetting.tcl for more details.
array set lstTrs [stc::perform GetTestResultSettingPaths]
set csvFile "$lstTrs(-OutputBasePath)my_results.csv"
puts "CSV file written to: $csvFile"

# Process the results file ...

# Delete configuration
puts "Deleting project"
stc::delete $hProject




