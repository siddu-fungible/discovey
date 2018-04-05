# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Traffic:: {
    array set arrayAnalyzerResult {};
    array set arrayGeneratorResult {};
    array set arrayTxStreamResult {};
    array set arrayRxStreamResult {};
    array set arrayRxOverflowResult {};
    array set arraySTCArray {};
    array set arraySTCArray_per_port {};
    #Add this array for CR 205767430. Used to save the generator mode so we can config it back later
    array set generatorMode {};
    ##end
    array set arrayFilterResult {}
    set arrayDiffServResult {};
    set control_Action "";
    set statsMode 0;
    set isLatencyConfig 0;
    set isEOTResults 0;
    set hltDir "";
    set EOTResultsFileName "";
    set EOTResultsFileNameCurrent 0
    set db_file 1;
    set detailedRxStats 0;
    #add by cf,this flag is used for qos stat
    set FilterType ""
    set dict_skip_port 0
    #end
    # For scale_mode 1, save FilterType and restore when leaving scale_mode 1.
    set oriFilterType ""

    # A filter may have multiple FilteredValue_* columns in results, need to specify a key column.
    array set filter_key_column {}
    set subscribeProjectLevelCounters 0;
    set subscribeProjectLevelRxStreamCounters 0;
    set aggTxjoinDataset "";
    set aggRxjoinDataset "";
    set txStreamDataset "";
    set rxStreamDataset "";
    set oofDataset "";
    
    set subscribeRxStreamSummaryResults "";
    set subscribeTxStreamResults "";
    set subscribeAnalyzerPortResults "";
    set subscribeGeneratorPortResults "";
    set subscribeOverflowResults "";
    set subscribeEnable "";
    set viewListRxStreamBlock 0;
    set viewListTxStreamBlock 0;
    set viewListAggTx 0;
    set viewListAggRx 0;
    set viewListoof 0;
    set viewListqos 0;
    set viewListcustomized 0;
    set viewListfcresult 0;
    set viewListsysmonitorresult 0;
    set viewAggTxlist ""
    set viewAggRxlist ""
    set viewooflist ""
    set viewqoslist ""
    set viewRxlist ""
    set viewTxlist ""
    set eotPortQueryEmpty 0
    set eotStreamQueryEmpty 0
    set drv_all_handle ""
}
namespace eval ::sth:: {
}

##Procedure Header
#
# Name:
#    sth::traffic_control
#
# Purpose:
#    Controls traffic generation on the specified test ports.
#
# Synopsis:
#    sth::traffic_control
#         -port_handle <list of port handles>
#         -action {run|stop|reset|destroy|clear_stats}
#         [-latency_bins {} ]
#         [-latency_values {} ]
#         [-duration <seconds>]
# Arguments:
#    -action
#                   Specifies the action to take on the specified port handles.
#                   Possible values are:
#
#                   run       - Starts traffic on all specified test ports.
#
#                   stop      - Stops traffic generation on all specified test
#                               ports.
#
#                   reset     - Clears all statistics and deletes all streams.
#
#                   destroy   - Deletes all streams. (Same as using
#                               -traffic_configure -mode remove.)
#
#                   clear_stats - Clears all statistics (transmitted and
#                                 received counters) related to streams.
#
#    -duration
#                   Amount of time in seconds for a continuous test to run.
#                   Tests run continuously for the number of seconds
#                   specified. You must set "sth::traffic_config -transmit_mode"
#                   to "continuous".
#
#    -port_handle
#                   Specifies the handle(s) of the port(s) on which to control
#                   traffic. A port_handle is a value that uniquely identifies a
#                   port on a chassis. This argument is required.
#
#    -latency_bins
#                   Specifies the number of latency bins. Always choose the
#                   first n number of preset buckets.
#
#    -latency_values
#                   Specifies the latency bucket values. You can enter a maximum 
#                   of 15 values.
#
#                   For example, if you specify the following arguments:
#                   sth::traffic_control -latency_bins 3 \
#                                       -latency_values 0.1 0.2 0.3 0.4 0.5 0.6
#
#                   Then the following values are sent to Spirent TestCenter:
#                   0.1 0.2 0.3 0.4
#
# Return Values:
#    The sth::traffic_control function returns a keyed list using
#    the following keys (with corresponding data):
#
#    stopped        Stopped (1) or Running (0)
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
# Description:
#    The traffic_control function manages streams of traffic on the
#    specified test ports. You use this function to perform the following
#    actions:
#
#    - Start and stop traffic
#
#    - Synchronize traffic generation
#
#    - Determine status
#
#    - Reset the traffic generators and result counters
#
# When you are running interactive tests, note that if you configure one port
# and start traffic on that port, and then wait a while before configuring
# another port and starting traffic on it, all of the port counters will be
# reset at the moment you start traffic on the second port.
#
# Examples: Please see Sample Input and Sample Output below.
#
# Sample Input:
#    set returnCtrlKlist [sth::traffic_control -action run -port_handle 84];
#
#    keylget returnCtrlKlist status iStatus;
#    if {$iStatus == 0} {
#         keylget returnCtrlKlist log result;
#         puts $result;
#    }
#
# Sample Output:
#    On success:
#    {status 1} {log {}}
#
#    On failure:
#    {status 0} {log {<errorMsg>}}
#
# Notes:
#    1)   The traffic_control function is non-blocking; it starts the action and
#         then returns control to the Tcl shell environment immediately. To
#         determine if an action has completed, use the "poll" action.
#
#
# End of Procedure Header
#
proc ::sth::traffic_control {args} {
    ::sth::sthCore::Tracker ::sth::traffic_control $args
 
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set returnKeyedList ""

    set cmdName "::sth::Traffic::traffic_control_imp $args"
      
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error message is raised."
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}


proc ::sth::Traffic::traffic_control_imp { args } {
    #::sth::sthCore::Tracker ::sth::traffic_control $args
    
     set trafficControlKeyedList ""
     variable userArgsArray
     array unset userArgsArray
     array set userArgsArray {};
     variable sortedSwitchPriorityList {};
     variable ::sth::sthCore::SUCCESS
     variable ::sth::sthCore::FAILURE
     
     ::sth::sthCore::log debug "{Calling sth::traffic_control}"
     ::sth::sthCore::log info "{Generating traffic table}"
     if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args \
                                  ::sth::Traffic:: \
                                  traffic_control \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError trafficControlKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $trafficControlKeyedList
     }

    ::sth::fill_global_variables

    #add "stream_handle" to control the specified streamblock  (xiaozhi 6/12/09)
    #if {(![info exists userArgsArray(port_handle)]) && (![info exists userArgsArray(stream_handle)])} {
    #    ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -stream_handle." {}
    #    return -code error $returnKeyedList
    #}
    #if "port_handle" and "stream_handle" are both given, pick port_handle as higher priority
    if {[info exists userArgsArray(port_handle)] && [info exists userArgsArray(stream_handle)]} {
        unset userArgsArray(stream_handle)
    }
    if {[info exists userArgsArray(elapsed_time)]} {
        set ::sth::Traffic::processElapsedTime $userArgsArray(elapsed_time)
    }

    set funcCall 0;
    if {$userArgsArray(action) == "run"} {
        set portlist [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"]
        
        # Fix for CR 205767430. save the generator mode so we can config it back later
        foreach port $portlist {
            if (![info exists ::sth::Traffic::generatorMode($port)]) {
                set gen [::sth::sthCore::invoke ::stc::get $port -children-generator]
                set ::sth::Traffic::generatorMode($port) [::sth::sthCore::invoke ::stc::get $gen.GeneratorConfig -DurationMode]
            }
        }
        
        set ::sth::Traffic::FilterType ""
        set sth::Traffic::control_Action $userArgsArray(action)
        
        #Saps need to change the unsubscribe values
        set sth::Traffic::subscribeEnable 1;
        if {[info exists userArgsArray(latency_bins)]} {
            set ret [::sth::Traffic::processTraffic_configlatency_values]
            set funcCall 1;
        } 
    } elseif {$userArgsArray(action) == "stop"} {
        set sth::Traffic::control_Action $userArgsArray(action)
        if {[info exists userArgsArray(db_file)]} {
            set sth::Traffic::db_file $userArgsArray(db_file)
        }
    }
        
    foreach key $sortedSwitchPriorityList {
        set switchName [lindex $key 1]
        if {(([string equal $switchName "latency_values"]) && ($funcCall == 1))} {
        } else {
            set myFunc $::sth::Traffic::traffic_control_procfunc($switchName)
            if {$myFunc != "_none_"} {
                ::sth::sthCore::log info "{Calling: $myFunc}"
                set cmdResult [eval $myFunc]
                if {$cmdResult == 0} {
                    set cmdFailed 0
                    break
                }
            }
        }
    }
    
    if {[::info exists cmdFailed]} {
                set trafficControlKeyedList [::sth::sthCore::updateReturnInfo $trafficControlKeyedList status 0]
                ::sth::sthCore::processError trafficControlKeyedList "{Error: Connect: $trafficControlKeyedList}";    
                return $trafficControlKeyedList
        } else {
                set trafficControlKeyedList [::sth::sthCore::updateReturnInfo $trafficControlKeyedList status 1]
                ::sth::sthCore::log info "{SUCCESS: Connect: $trafficControlKeyedList}"
                return $trafficControlKeyedList
    }

}

proc ::sth::start_test {args} {
    ::sth::sthCore::Tracker ::sth::start_test $args
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    set returnKeyedList ""
    set cmdName "::sth::Traffic::start_test_imp $args"
    
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error message is raised."
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::traffic_stats
#
# Purpose:
#    Retrieves statistical information about traffic streams.
#
# Synopsis:
#    sth::traffic_stats
#         -port_handle <integer>
#       { [-mode {aggregate|stream|all}] |
#         [-mode streams [-streams <list of stream IDs>]]
#       }
#
# Arguments:
#    -port_handle
#                   Specifies one or more ports from which to gather transmitted
#                   (tx) and received (rx) statistics. This argument is
#                   required.
#
#    -mode
#                   Specifies the type of statistics to collect:
#
#                   aggregate -         Collect all transmitted (tx) and
#                                       received (rx) packets.
#
#                   stream -            Collect detailed test stream statistics.
#
#                   all -               Collect all statistics.
#
#                   This argument is required.
#
#    -streams
#                   Specifies a stream ID for which to gather statistics.
#                   Retrieves statistics for the specified streams when the
#                   -mode is set to "stream." If you do not list one or more
#                   stream IDs, then this function retrieves statistics for all
#                   streams under the specified port(s).
#
# Return Values:
#    The traffic_stats function returns a keyed list using the
#    following keys (with corresponding data):
#
#    <port_handle>  The handle(s) of the port(s) on which to retrieve
#                   statistics.
#    <mode>         The type of statistics to collect.
#    <tx|rx>        Indicates if the value refers to a transmitted (tx) or
#                   received (rx) statistic.
#    <attribute>    The name of the attribute to which the statistic applies.
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
# Following is a keyed list showing the types of keys returned based on the mode
# you specified.
#
#    Note:  With EOT results, after you stop the traffic, all rates are set to
#           0; therefore, they are not returned in the keyed list.
#
#    *** aggregate statistics ***
#
#    <port handle>.aggregate.<tx|rx>.pkt_count
#    <port handle>.aggregate.<tx|rx>.pkt_byte_count
#    <port handle>.aggregate.<tx|rx>.pkt_rate
#    <port handle>.aggregate.<tx|rx>.total_pkts
#    <port handle>.aggregate.<tx|rx>.total_pkt_bytes
#    <port handle>.aggregate.<tx|rx>.total_pkt_rate
#    <port handle>.aggregate.<tx|rx>.tcp_pkts
#    <port handle>.aggregate.<tx|rx>.tcp_checksum_errors
#    <port handle>.aggregate.<tx|rx>.udp_pkts
#    <port handle>.aggregate.<tx|rx>.ip_pkts
#
#  *** stream statistics ***
#
#    <port handle>.stream.<id>.ipv4_present
#    <port handle>.stream.<id>.ipv6_present
#    <port handle>.stream.<id>.ipv4_outer_present
#    <port handle>.stream.<id>.ipv6_outer_present
#    <port handle>.stream.<id>.tcp_present
#    <port handle>.stream.<id>.udp_present
#    <port handle>.stream.<id>.<rx|tx>.total_pkts
#    <port handle>.stream.<id>.<rx|tx>.total_pkt_bytes
#    <port handle>.stream.<id>.<rx|tx>.total_pkt_rate
#    <port handle>.stream.<id>.<rx|tx>.total_pkt_bit_rate
#    <port handle>.stream.<id>.<rx|tx>.min_pkt_length
#    <port handle>.stream.<id>.<rx|tx>.max_pkt_length
#    <port handle>.stream.<id>.<rx|tx>.avg_delay
#    <port handle>.stream.<id>.<rx|tx>.min_delay
#    <port handle>.stream.<id>.<rx|tx>.max_delay
#    <port handle>.stream.<id>.<rx|tx>.misinserted_pkts
#    <port handle>.stream.<id>.<rx|tx>.out_of_sequence_pkts
#    <port handle>.stream.<id>.<rx|tx>.misinserted_pkt_rate
#    <port handle>.stream.<id>.<rx|tx>.prbs_bit_error_rate
#    <port handle>.stream.<id>.<rx|tx>.prbs_bit_errors
#    <port handle>.stream.<id>.<rx|tx>.first_tstamp
#    <port handle>.stream.<id>.<rx|tx>.last_tstamp
#    <port handle>.stream.<id>.<rx|tx>.Max
#    <port handle>.stream.<id>.<rx|tx>.Min
#    <port handle>.stream.<id>.<rx|tx>.pkt_byte_rate
#    <port handle>.stream.<id>.rx.latency_bin.<bin number>.pkt_byte_rate
#    <port handle>.stream.<id>.rx.latency_bin.<bin number>.total_pkts
#
# Description:
#    The traffic_stats function provides detailed information about
#    the traffic transmitted and received at the specified port(s). You can
#    direct Spirent HLTAPI analyzer to retrieve various combinations of
#    statistics:
#
#    - All transmitted and received packets, identified by port.
#    - Statistics organized by stream.
#    - All statistics.
#
#    The function returns the requested type of data and a status value (1 for
#    success). If there is an error, the function returns the status value (0)
#    and an error message. Function return values are formatted as a keyed list
#    (supported by the Tcl extension software - TclX). Use the TclX function
#    keylget to retrieve data from the keyed list.
#
#    The key values to access the data returned from the traffic_stats function
#    are:
#
#    <port_handle>.<mode>.<tx|rx>.<attribute>
#
#    <port_handle> identifies a port on the chassis, specified as an integer.
#    <mode> indicates the type of statistics to collect.
#    <tx | rx> specifies whether the statistic was transmitted or received.
#    <attribute> specifies the name of the attribute to which the statistic
#    applies such as avg_pkt_length, pkt_count, and pkt_rate,
#
#    status
#
#    The key "status" retrieves a value indicating the success (1) or failure
#    (0) of the operation.
#
#    log
#
#    The key "log" retrieves a message describing the last error that occurred
#    during the operation. If the operation was successful - {status 1} - the
#    log value is null.
#
#
# Examples: See Sample Input and Sample Output.
#
# Sample Input:
#    set statsKeyList [sth::traffic_stats -mode aggregate -port_handle 60];
#
#    keylget statsKeyList status iStatus;
#    if {$iStatus == 0} {
#         keylget statsKeyList log result;
#         puts $result;
#    }
#
# Sample Output:
#
#    On success:
#    {status 1} {log {}}
#
#    On failure:
#    {status 0} {log {<errorMsg>}}
#
# Notes:
#    1)   The keyed list that is returned will contain only the relevant
#         parameters. For example, if the generator is running on port 2 and
#         analyzer is running on port 1, a call to traffic_stats passing port 2
#         will only return the generator statistics. A call to traffic_stats for
#         port 2 with the mode set as stream will return only the tx-side
#         parameter that will be returned in the total_pkts field. None of the
#         rx-side parameters will be returned.
#
#    2)   Do not reset the analyzer (if the stream statistics are required)
#         because this will clear the filters.
#
#    3)   Elapsed time is returned only if the analyzer is receiving any data.
#
# End of Procedure Header
#
proc ::sth::traffic_stats {args} {
    ::sth::sthCore::Tracker ::sth::traffic_stats $args
 
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set returnKeyedList ""

    set cmdName "::sth::Traffic::traffic_stats_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error message is raised."
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::Traffic::traffic_stats_imp { args } {
    ::sth::sthCore::Tracker ::sth::traffic_stats_imp $args
        
        set trafficStatsKeyedList ""
        variable userArgsArray
        array unset userArgsArray
        array set userArgsArray {};
        variable sortedSwitchPriorityList {};
        variable detailedRxStats;
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        set cmdName "traffic_stats"
        set properties ""
        set txResultKeys ""
        set rxResultKeys ""
        set detail_streams 0
        set detailedRxStats 0
        
        ::sth::sthCore::log debug "{Calling sth::traffic_stats}"
        ::sth::sthCore::log info "{Generating traffic table}"
    
        if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args \
                                     ::sth::Traffic:: \
                                     traffic_stats \
                                     userArgsArray \
                                     sortedSwitchPriorityList} eMsg]} {
           ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
           return $trafficStatsKeyedList
        }
        if {[info exists userArgsArray(scale_mode)]} {
            if {$userArgsArray(scale_mode) == 1} {
                set trafficStatsKeyedList [sth::Traffic::getResults]
                return $trafficStatsKeyedList
            }
        }

        if {$userArgsArray(mode) == "detailed_streams"} {
            set detail_streams 1
        }
        
        if {[info exists userArgsArray(properties)]} {
            set txResultKeys [sth::Traffic::getTypeProperties tx $userArgsArray(properties)]
            set rxResultKeys [sth::Traffic::getTypeProperties rx $userArgsArray(properties)]
            if {$txResultKeys == ""} {
                set txResultKeys "_none_"
            } elseif {$rxResultKeys == ""} {
                set rxResultKeys "_none_"
            }
        }
        if {$userArgsArray(mode) == "all"} {
            if {![info exists userArgsArray(port_handle)]} {
                set userArgsArray(mode) "streams"
            }
        }
        if {[info exists userArgsArray(detailed_rx_stats)] && $userArgsArray(detailed_rx_stats) == 1} {
            set detailedRxStats 1
        }
        if {($sth::Traffic::isEOTResults == 0)||
            ($detail_streams == 1)} {
                set rxStreamTyp RxStreamSummaryResults
                set txStreamTyp TxStreamResults
            } else {
                if {$sth::Traffic::EOTResultsFileNameCurrent == 1} {
                } else {
                   set rxStreamTyp RxStreamBlockResults
                   set txStreamTyp TxStreamBlockResults 
                }
            }
        if {$userArgsArray(mode) == "aggregate"} {
                if {[info exists userArgsArray(streams)]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Aggregate mode does not support streams" {}
                    return $trafficStatsKeyedList
                }
                if {![info exists userArgsArray(port_handle)] || $userArgsArray(port_handle) eq "all"} {
                    set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                } else {
                    set portlist $userArgsArray(port_handle)
                }
                foreach port $portlist {
                    if {[catch {::sth::sthCore::invoke stc::get $port "-children-generator"} generatorhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                                return -code 1 -errorcode -1 $generatorhndl;
                    }
                    set status [::sth::sthCore::invoke stc::get $generatorhndl -State]
                    if {$status == "RUNNING" || $sth::Traffic::isEOTResults == 0} {
                        set ::sth::Traffic::aggTxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_txjoin Generator GeneratorPortResults portlevel $port $txResultKeys]
                        set ::sth::Traffic::aggRxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer AnalyzerPortResults portlevel $port $rxResultKeys]
                                      
                        #add by cf
                        variable ::sth::Traffic::FilterType 
                        if {$::sth::Traffic::FilterType != ""} {
                            set ::sth::Traffic::aggRxQoSDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer FilteredStreamResults portlevel $port $rxResultKeys]
                        } else {
                            set ::sth::Traffic::aggRxQoSDataset ""
                        }
                        #end
                        ::sth::Traffic::delay "GeneratorPortResults AnalyzerPortResults FilteredStreamResults"
                        set cmdResult [::sth::Traffic::processTrafficStatsGetAggRxCounters $port $rxResultKeys]
                        set cmdResult [::sth::Traffic::processTrafficStatsGetAggTxCounters $port $txResultKeys]
                        ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggTxjoinDataset
                        ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxjoinDataset
                        if {$::sth::Traffic::FilterType != ""} {
                           ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxQoSDataset
                        }
                    } else {
                        if {$sth::Traffic::EOTResultsFileNameCurrent == 1} {
                            set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults "aggregate_rxjoin" "0" $port $rxResultKeys $detail_streams]
                            set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults "aggregate_txjoin" "0" $port $txResultKeys $detail_streams]
                        } else {
                            ::sth::sthCore::log warn "No DB File is saved after traffic stopped, so the real time results return";
                            set ::sth::Traffic::aggTxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_txjoin Generator GeneratorPortResults portlevel $port $txResultKeys]
                            set ::sth::Traffic::aggRxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer AnalyzerPortResults portlevel $port $rxResultKeys]
                                      
                            #add by cf
                            variable ::sth::Traffic::FilterType 
                            if {$::sth::Traffic::FilterType != ""} {
                                set ::sth::Traffic::aggRxQoSDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer FilteredStreamResults portlevel $port $rxResultKeys]
                            } else {
                                set ::sth::Traffic::aggRxQoSDataset ""
                            }
                            #end
                            ::sth::Traffic::delay "GeneratorPortResults AnalyzerPortResults FilteredStreamResults"
                            set cmdResult [::sth::Traffic::processTrafficStatsGetAggRxCounters $port $rxResultKeys]
                            set cmdResult [::sth::Traffic::processTrafficStatsGetAggTxCounters $port $txResultKeys]
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggTxjoinDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxjoinDataset
                            if {$::sth::Traffic::FilterType != ""} {
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxQoSDataset
                            }
                        }
                    }
                }
        } elseif {$userArgsArray(mode) == "streams" ||
                  $userArgsArray(mode) == "detailed_streams" } {
                    
                set streamBlk 0;
                # fix an error: can't read "paging" :no such variable;
                # continue run " sth::traffic_stats -mode all " and " sth::traffic_stats -mode detailed_streams " will throw this error message; 
                set ::sth::Traffic::statsMode 0
                #added for US32329 
                if {[info exists userArgsArray(streams)] || ![info exists userArgsArray(port_handle)] } {
                    # specified streamblocks or all streamblocks under project
                    
                    # For processTrafficStatsGet(Rx|Tx)StreamCounters use, to indicate if the first argument is a list of 
                    # streamblock handles(1) or a list of port handles (0)
                    set streamBlk 1
                    
                    if {![info exists userArgsArray(port_handle)] && ![info exists userArgsArray(rx_port_handle)] } {
                        set ::sth::Traffic::dict_skip_port 1
                    }
                    if {[info exists userArgsArray(streams)] && $userArgsArray(streams) ne "all"} {
                        set streamblkHndlist $userArgsArray(streams)
                    } else {
                        set ports [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-port]
                        set streamBlockList ""
                        foreach portVar $ports {
                            set streamBlockTemp [::sth::sthCore::invoke stc::get $portVar -children-streamblock]
                            if {$streamBlockTemp != ""} {
                                append streamBlockList "$streamBlockTemp "
                            }
                        }
                        if { $streamBlockList != "" } {
                            set streamblkHndlist $streamBlockList
                        }
                    }
                    foreach streamblkhndl $streamblkHndlist {
                        set status [::sth::sthCore::invoke stc::get $streamblkhndl -RunningState]
                        if {$status == "RUNNING" || $sth::Traffic::isEOTResults == 0 || $detail_streams == 1} {
                            # rtStreamList: get results from result objects
                            # eotStreamList: get results from db file
                            lappend rtStreamList $streamblkhndl
                            set rxStreamTyp RxStreamSummaryResults
                            set txStreamTyp TxStreamResults
                            ::sth::sthCore::log debug "status $status isEOTResults $sth::Traffic::isEOTResults detail_streams $detail_streams"
                        } else {
                            ::sth::sthCore::log debug "status $status isEOTResults $sth::Traffic::isEOTResults detail_streams $detail_streams"
                            if {$sth::Traffic::EOTResultsFileNameCurrent == 1} {
                                lappend eotStreamList $streamblkhndl
                            } else {
                                lappend rtStreamList $streamblkhndl
                                if {$::sth::Traffic::FilterType != ""} {
                                    set rxStreamTyp RxStreamBlockResults
                                } else {
                                    set rxStreamTyp rxstreamsummaryresults
                                } 
                                #set rxStreamTyp RxStreamBlockResults
                                set txStreamTyp TxStreamBlockResults 
                            }
                        }
                    }
                    # retrieve stats from result objects for Tx and Rx
                    if {[info exists rtStreamList]} {
                        set ::sth::Traffic::txStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_tx StreamBlock $txStreamTyp streamblocklevel $rtStreamList $txResultKeys]
                        
                        if {$::sth::Traffic::FilterType != ""} {
                            if {$detail_streams == 1} {
                                # When analyzer filters exist, RxStreamSummaryResults can be subscribed but store nothing. 
                                # Use FilteredStreamResults instead.
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeFilteredCounters stream_rx $rxResultKeys]
                            } else {
                                # subscribe RxStreamBlockResults
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_rx StreamBlock RxStreamBlockResults streamblocklevel $rtStreamList $rxResultKeys]    
                            }
                        } else {
                            # subscribe RxStreamSummaryResults
                            set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_rx StreamBlock $rxStreamTyp streamblocklevel $rtStreamList $rxResultKeys]
                        }
                        ::sth::Traffic::delay "$txStreamTyp $rxStreamTyp"
                        
                        if {$detail_streams == 1 && $::sth::Traffic::FilterType != ""} {
                            set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamFilteredCounters $rtStreamList $streamBlk $rxResultKeys $detail_streams]
                        } else {
                            set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamCounters $rtStreamList $streamBlk $rxResultKeys $detail_streams]
                        }
                        set cmdResult [::sth::Traffic::processTrafficStatsGetTxStreamCounters $rtStreamList $streamBlk $txResultKeys $detail_streams]
                        ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::txStreamDataset
                        ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::rxStreamDataset
                    }
                    # retrieve stats from DB for Tx and Rx
                    if {[info exists eotStreamList]} {
                        set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults "streameot_rx" $streamBlk $eotStreamList $rxResultKeys $detail_streams]
                        set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults "streameot_tx" $streamBlk $eotStreamList $txResultKeys $detail_streams]
                    }
                }  elseif {[info exists userArgsArray(port_handle)]} {
                    # All streamblocks under specified ports
                    if {$userArgsArray(port_handle) eq "all"} {
                       set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                    } else {
                        set portlist $userArgsArray(port_handle)
                     }
                    foreach port $portlist {
                        set ana [::sth::sthCore::invoke stc::get $port -children-Analyzer]
                        set anaconfig [::sth::sthCore::invoke stc::get $ana -children-Analyzer16BitFilter]
                        if {$anaconfig != "" && $::sth::Traffic::FilterType == ""} {
                            set ::sth::Traffic::FilterType wrapper
                        }
                    }
                    if {($::sth::Traffic::FilterType != "") &&
                        ($detail_streams == 0)} {
                        set rxStreamTyp RxStreamBlockResults
                    } else {
                        set rxStreamTyp rxstreamsummaryresults
                    }
                    foreach port $portlist {
                        if {[catch {::sth::sthCore::invoke stc::get $port "-children-generator"} generatorhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                                return -code 1 -errorcode -1 $generatorhndl;
                        }
                        set status [::sth::sthCore::invoke stc::get $generatorhndl -State]
                        
                        # retrieve real-time stats for Tx and Rx
                        if {$status == "RUNNING" || $sth::Traffic::isEOTResults == 0} {
                            set ::sth::Traffic::txStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_tx StreamBlock $txStreamTyp portlevel $port $txResultKeys]
                            
                            if {$detail_streams == 1 && $::sth::Traffic::FilterType != ""} {
                                # When analyzer filters exist, RxStreamSummaryResults can be subscribed but store nothing. 
                                # Use FilteredStreamResults instead.
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeFilteredCounters stream_rx $rxResultKeys]
                            } else {
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_rx StreamBlock $rxStreamTyp portlevel $port $rxResultKeys]
                            }
                            
                            ::sth::Traffic::delay "$txStreamTyp $rxStreamTyp"
                            
                            if {$detail_streams == 1 && $::sth::Traffic::FilterType != ""} {
                                set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamFilteredCounters $port $streamBlk $rxResultKeys $detail_streams]
                            } else {
                                set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamCounters $port $streamBlk $rxResultKeys $detail_streams]
                            }
                            set cmdResult [::sth::Traffic::processTrafficStatsGetTxStreamCounters $port $streamBlk $txResultKeys $detail_streams]
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::txStreamDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::rxStreamDataset
                        } else {
                            # retrieve EOT stats for Tx and Rx
                            if {$sth::Traffic::EOTResultsFileNameCurrent == 1} {
                                set streamlist "streameot_rx streameot_tx"
                                set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults "streameot_rx" $streamBlk $port $rxResultKeys $detail_streams]
                                set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults "streameot_tx" $streamBlk $port $txResultKeys $detail_streams]
                            } else {
                                ::sth::sthCore::log warn "No DB File is saved after traffic stopped, so the real time results return";
                                set ::sth::Traffic::txStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_tx StreamBlock $txStreamTyp portlevel $port $txResultKeys]
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_rx StreamBlock $rxStreamTyp portlevel $port $rxResultKeys]
                                ::sth::Traffic::delay "$txStreamTyp $rxStreamTyp"
                                set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamCounters $port $streamBlk $rxResultKeys $detail_streams]
                                set cmdResult [::sth::Traffic::processTrafficStatsGetTxStreamCounters $port $streamBlk $txResultKeys $detail_streams]
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::txStreamDataset
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::rxStreamDataset
                            }
                        }
                    }
                }

                if {$::sth::Traffic::isLatencyConfig} {
                    if {[info exists streamblkHndlist]} {
                        foreach streamblkHndl $streamblkHndlist {
                            set currPort [::sth::sthCore::invoke stc::get $streamblkHndl -parent]
                            keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.total_pkts rx_count
                            keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts tx_count
                            if {[info exists rx_count] && [info exists tx_count] && $tx_count != 0 } {
                                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts [expr $tx_count - $rx_count]
                                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts_percent [expr ($tx_count - $rx_count) * 100.0/$tx_count]
                            }
                        }
                    } else {
                        foreach currPort $portlist {
                            set streamblockHndlList [::sth::sthCore::invoke stc::get $currPort -children-streamblock]
                            foreach streamblkHndl $streamblockHndlList {
                                keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.total_pkts rx_count
                                keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts tx_count
                                if {[info exists rx_count] && [info exists tx_count] && $tx_count != 0 } {
                                    keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts [expr $tx_count - $rx_count]
                                    keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts_percent [expr ($tx_count - $rx_count) * 100.0/$tx_count]
                                }
                            }
                        }
                    }
                }
                
                if {$::sth::Traffic::FilterType  == "wrapper"} {
                    set ::sth::Traffic::FilterType ""
                }
        }  elseif {$userArgsArray(mode) == "out_of_filter"} {
            if {![info exists userArgsArray(port_handle)] || $userArgsArray(port_handle) eq "all"} {
                  set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
            } else {
                set portlist $userArgsArray(port_handle)
              }
                foreach port $portlist {
                    set ::sth::Traffic::oofDataset [::sth::Traffic::processTrafficStatsSubscribeCounters out_of_filter Analyzer OverflowResults portlevel $port $properties]
                    ::sth::Traffic::delay "OverflowResults"
                    set cmdResult [::sth::Traffic::processTrafficStatsGetUnknownOofTxCounters $port]
                    ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::oofDataset
                }
            
        } elseif {$userArgsArray(mode) == "all"} {
                set ::sth::Traffic::statsMode 1
             
                if {![info exists userArgsArray(port_handle)]} {
                    ::sth::sthCore::processError trafficStatsKeyedList " mode requires port handles to be specified" {}
                    return $trafficStatsKeyedList
                } else {
                    if {$userArgsArray(port_handle) ne "all" } {
                        set portlist $userArgsArray(port_handle)
                    } else {
                        set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                    }
                    foreach port $portlist {
                        if {[catch {::sth::sthCore::invoke stc::get $port "-children-generator"} generatorhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                                return -code 1 -errorcode -1 $generatorhndl;
                        }
                        set status [::sth::sthCore::invoke stc::get $generatorhndl -State]
                        if {$status == "RUNNING" || $sth::Traffic::isEOTResults == 0} {
                            set ::sth::Traffic::userDefinedDataset [::sth::Traffic::processTrafficStatsSubscribeCounters userdefined Analyzer AnalyzerPortResults portlevel $port $properties]
                            set ::sth::Traffic::aggRxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer AnalyzerPortResults portlevel $port $properties]
                            set ::sth::Traffic::aggTxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_txjoin Generator GeneratorPortResults portlevel $port $properties]
                            #add by cf. for qos stat
                            variable ::sth::Traffic::FilterType 
                            if {$::sth::Traffic::FilterType != ""} {
                                set ::sth::Traffic::aggRxQoSDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer FilteredStreamResults portlevel $port $properties]
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeFilteredCounters stream_rx $properties]
                            } else {
                                set ::sth::Traffic::aggRxQoSDataset ""
                                set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_rx StreamBlock $rxStreamTyp portlevel $port $properties]
                            }
                            #end
                            set ::sth::Traffic::oofDataset [::sth::Traffic::processTrafficStatsSubscribeCounters out_of_filter Analyzer OverflowResults portlevel $port $properties]
                            
                            set ::sth::Traffic::txStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_tx StreamBlock $txStreamTyp portlevel $port $properties]
                            
                            ::sth::Traffic::delay "AnalyzerPortResults GeneratorPortResults FilteredStreamResults OverflowResults $rxStreamTyp $txStreamTyp"
                            set cmdResult [::sth::Traffic::processTrafficStatsGetAggRxCounters $port $properties]
                            set cmdResult [::sth::Traffic::processTrafficStatsGetCustomizedCounters $port $properties]
                            set cmdResult [::sth::Traffic::processTrafficStatsGetAggTxCounters $port $properties]
                            set cmdResult [::sth::Traffic::processTrafficStatsGetUnknownOofTxCounters $port]
                            if {$::sth::Traffic::FilterType != ""} {
                                set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamFilteredCounters $port 0 $properties $detail_streams]
                            } else {
                                set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamCounters $port 0 $properties $detail_streams]
                            }
                            set cmdResult [::sth::Traffic::processTrafficStatsGetTxStreamCounters $port 0 $properties $detail_streams]
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::userDefinedDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggTxjoinDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxjoinDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::oofDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::txStreamDataset
                            ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::rxStreamDataset
                            if {$::sth::Traffic::FilterType != ""} {
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxQoSDataset
                            }
                        } else {
                             ##EOT result
                            if {$sth::Traffic::EOTResultsFileNameCurrent == 1} {
                                set agglist "aggregate_rxjoin aggregate_txjoin streameot_rx streameot_tx"
                                foreach listitem $agglist {
                                   set cmdResult [::sth::Traffic::processTrafficStats_GetEOTResults $listitem "0" $port $properties $detail_streams]
                                }
                            } else {
                                ::sth::sthCore::log warn "No DB File is saved after traffic stopped, so the real time results return";
                                set ::sth::Traffic::aggRxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer AnalyzerPortResults portlevel $port $properties]
                                set ::sth::Traffic::aggTxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_txjoin Generator GeneratorPortResults portlevel $port $properties]
                                #add by cf. for qos stat
                                if {$::sth::Traffic::FilterType != ""} {
                                    set ::sth::Traffic::aggRxQoSDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer FilteredStreamResults portlevel $port $properties]
                                    set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeFilteredCounters stream_rx $properties]
                                } else {
                                    set ::sth::Traffic::aggRxQoSDataset ""
                                    set ::sth::Traffic::rxStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_rx StreamBlock $rxStreamTyp portlevel $port $properties]
                                }
                                #end
                                set ::sth::Traffic::oofDataset [::sth::Traffic::processTrafficStatsSubscribeCounters out_of_filter Analyzer OverflowResults portlevel $port $properties]
                                set ::sth::Traffic::txStreamDataset [::sth::Traffic::processTrafficStatsSubscribeCounters stream_tx StreamBlock $txStreamTyp portlevel $port $properties]

                                ::sth::Traffic::delay "AnalyzerPortResults GeneratorPortResults FilteredStreamResults OverflowResults $rxStreamTyp $txStreamTyp"
                                set cmdResult [::sth::Traffic::processTrafficStatsGetAggRxCounters $port $properties]
                                set cmdResult [::sth::Traffic::processTrafficStatsGetAggTxCounters $port $properties]
                                set cmdResult [::sth::Traffic::processTrafficStatsGetUnknownOofTxCounters $port]
                                if {$::sth::Traffic::FilterType != ""} {
                                    set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamFilteredCounters $port 0 $properties $detail_streams]
                                } else {
                                    set cmdResult [::sth::Traffic::processTrafficStatsGetRxStreamCounters $port 0 $properties $detail_streams]
                                }
                                set cmdResult [::sth::Traffic::processTrafficStatsGetTxStreamCounters $port 0 $properties $detail_streams]
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggTxjoinDataset
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxjoinDataset
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::oofDataset
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::txStreamDataset
                                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::rxStreamDataset
                                if {$::sth::Traffic::FilterType != ""} {
                                    ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxQoSDataset
                                }    
                            }
                        }
                    }
                }
        } elseif {$userArgsArray(mode) == "get_name"} {
            #add arguments "get_name" to get streamblock's name
            set streamblockNameList ""
            set streamblockHandleList ""
            if {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(streams)] } {
                if {$userArgsArray(port_handle) eq "all" } {
                    set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                } else {
                     set portlist $userArgsArray(port_handle)
                 }
                foreach port $portlist {
                    set streamblockHandleList [concat $streamblockHandleList [::sth::sthCore::invoke stc::get $port -children-streamblock]]                  
                }
                foreach streamblockHandle $streamblockHandleList {
                    set streamblockNameList [concat $streamblockNameList [::sth::sthCore::invoke stc::get $streamblockHandle -name]]
                }
                set cmdResult [llength $streamblockNameList]
            } elseif {[info exists userArgsArray(streams)] } {
                if {$userArgsArray(streams) eq "all"} {
                           set ports [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                           foreach port $ports {
                              foreach streamblk [sth::sthCore::invoke ::sth::sthCore::invoke stc::get $port -children-streamblock] {
                                 lappend streamblockHandleList $streamblk
                              }
                           }
                       } else {
                            set streamblockHandleList $userArgsArray(streams)
                         }
                foreach streamblockHandle $streamblockHandleList {
                    set streamblockNameList [concat $streamblockNameList [::sth::sthCore::invoke stc::get $streamblockHandle -name]]
                }
                set cmdResult [llength $streamblockNameList]
            } else {
                #::sth::sthCore::processError trafficStatsKeyedList "get_name mode requires port handles or streamblock handles to be specified" {}
                #return $trafficStatsKeyedList

                set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                foreach port $portlist {
                    set streamblockHandleList [concat $streamblockHandleList [::sth::sthCore::invoke stc::get $port -children-streamblock]]                  
                }
                foreach streamblockHandle $streamblockHandleList {
                    set streamblockNameList [concat $streamblockNameList [::sth::sthCore::invoke stc::get $streamblockHandle -name]]
                }
                set cmdResult [llength $streamblockNameList]
            }
        } else {
            ::sth::sthCore::processError trafficStatsKeyedList "Invalid mode for traffic_Stats, should be: aggregate, streams, out_of_filter, all, get_name \n" {}
            set cmdResult 0
        }
        
        if {$cmdResult == 0} {
            set cmdFailed 0
        } 
        if {[::info exists cmdFailed]} {
            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList status 0]
            set ::sth::Traffic::dict_skip_port 0
            return $trafficStatsKeyedList
        } else {
            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList status 1]
            if {[info exists streamblockNameList] && [llength $streamblockNameList]>0} {
                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList stream_name $streamblockNameList]
            }
            # calculate dropped_pkts_percent for each stream
            if {$detailedRxStats == 0} {
                if {[info exists userArgsArray(streams)] || ![info exists userArgsArray(port_handle)] } {
                    if {[info exists userArgsArray(streams)]} {
                        if {$userArgsArray(streams) eq "all"} {
                           set ports [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                           foreach port $ports {
                              foreach streamblk [sth::sthCore::invoke ::sth::sthCore::invoke stc::get $port -children-streamblock] { 
                                 lappend streamblkHndlist $streamblk
                              }
                           }
                       } else {
                            set streamblkHndlist $userArgsArray(streams)
                         }
                    } elseif { [info exists streamBlockList] && $streamBlockList != "" } {
                        # when mode is 'streams' or 'detailed_streams'
                        set streamblkHndlist $streamBlockList
                    } else {
                        set ports [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                        foreach port $ports {
                            foreach streamblk [sth::sthCore::invoke ::sth::sthCore::invoke stc::get $port -children-streamblock] {
                           #lappend streamblkHndlist [sth::sthCore::invoke ::sth::sthCore::invoke stc::get $port -children-streamblock]
                               lappend streamblkHndlist $streamblk
                            }
                        }
                      }
                    foreach streamblkHndl $streamblkHndlist {
                        set status [::sth::sthCore::invoke stc::get $streamblkHndl -RunningState]
                        if {$status == "RUNNING"} {
                            # Get dropped_pkts and dropped_pkts_percent from dataset
                        } else {
                            # EOT result, need to calculate dropped_pkts_percent
                            set currPort [::sth::sthCore::invoke stc::get $streamblkHndl -parent]
                            if {$detail_streams == 1} {
                                if {[catch {set stcValue [keylkeys trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx]}]} {
                                    set stcValue ""
                                }
                                for {set i 0} {$i < [llength $stcValue]} {incr i} {
                                    keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.total_pkts rx_count
                                    keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$i.total_pkts tx_count
                                    if {[info exists rx_count] && [info exists tx_count] && $tx_count != 0 } {
                                        set dropped_pkts_percent [expr ($tx_count - $rx_count) * 100.0/$tx_count]
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            keylset trafficStatsKeyedList $streamblkHndl.rx.$i.dropped_pkts_percent $dropped_pkts_percent
                                        }
                                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.dropped_pkts_percent $dropped_pkts_percent
                                    }
                                }
                            } else {
                                keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.total_pkts rx_count
                                keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts tx_count
                                if {[info exists rx_count] && [info exists tx_count] && $tx_count != 0 } {
                                    set dropped_pkts_percent [expr ($tx_count - $rx_count) * 100.0/$tx_count]
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        keylset trafficStatsKeyedList $streamblkHndl.rx.dropped_pkts_percent $dropped_pkts_percent
                                    }
                                    keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts_percent $dropped_pkts_percent
                                }
                            }
                        }
                    }
                }  elseif {[info exists userArgsArray(port_handle)]} {
                    if {$userArgsArray(port_handle) ne "all" } {
                       set portlist $userArgsArray(port_handle)
                    } else {
                        set portlist [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                    }
                    foreach currPort $portlist {
                        if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-generator"} generatorhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                                return -code 1 -errorcode -1 $generatorhndl;
                        }
                        set status [::sth::sthCore::invoke stc::get $generatorhndl -State]
                        if {$status == "RUNNING" || $sth::Traffic::isEOTResults == 0} {
                            # Get dropped_pkts and dropped_pkts_percent from dataset
                        } else {
                            # EOT result, need to calculate dropped_pkts_percent
                            set streamblockHndlList [::sth::sthCore::invoke stc::get $currPort -children-streamblock]
                            foreach streamblkHndl $streamblockHndlList {
                                if {$detail_streams == 1} {
                                    if {[catch {set stcValue [keylkeys trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx]}]} {
                                        set stcValue ""
                                    }
                                    for {set i 0} {$i < [llength $stcValue]} {incr i} {
                                        keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.total_pkts rx_count
                                        keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$i.total_pkts tx_count
                                        if {[info exists rx_count] && [info exists tx_count] && $tx_count != 0 } {
                                            set dropped_pkts_percent [expr ($tx_count - $rx_count) * 100.0/$tx_count]
                                            keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.dropped_pkts_percent $dropped_pkts_percent
                                        }
                                    }
                                } else {
                                    keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.total_pkts rx_count
                                    keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts tx_count
                                    if {[info exists rx_count] && [info exists tx_count] && $tx_count != 0 } {
                                        set dropped_pkts_percent [expr ($tx_count - $rx_count) * 100.0/$tx_count]
                                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts_percent $dropped_pkts_percent
                                    }
                                }
                            }
                        }
                    }
                }
            }
            set ::sth::Traffic::dict_skip_port 0
            return $trafficStatsKeyedList
        }
}

proc ::sth::drv_stats {args} {
    ::sth::sthCore::Tracker ::sth::drv_stats $args
 
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set returnKeyedList ""

    set cmdName "::sth::Traffic::drv_stats_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error message is raised."
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";
        return $returnKeyedList
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
            return $returnKeyedList
        }
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}

proc ::sth::Traffic::drv_stats_imp {args} {
    ::sth::sthCore::Tracker ::sth::drv_stats_imp $args
 
    set drvStatsKeyedList ""
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {};
    variable sortedSwitchPriorityList {};
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
     
    ::sth::sthCore::log debug "{Calling sth::drv_stats}"    
    if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args \
                                 ::sth::Traffic:: \
                                 drv_stats \
                                 userArgsArray \
                                 sortedSwitchPriorityList} eMsg]} {
       ::sth::sthCore::processError drvStatsKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
       return $drvStatsKeyedList
    }
    
    set drv_handle ""
    
    if {[info exists userArgsArray(handle)]} {
        set drv_handle $userArgsArray(handle)
    }
    set drv_name $userArgsArray(drv_name)
    if {[regexp -nocase "true" $userArgsArray(force_load)] && ![regexp -nocase "^$" $drv_handle]} {
        set drv_name [sth::sthCore::invoke "stc::get $drv_handle -name"]
        sth::sthCore::invoke "stc::perform UnSubscribeDynamicResultViewCommand -DynamicResultView $drv_handle"
        ::sth::sthCore::invoke stc::sleep 3;
        sth::sthCore::invoke "stc::delete $drv_handle"
        set drv_handle ""
    }
    if {$drv_handle == ""} {
        if {[info exists userArgsArray(drv_xml)]} {
            set drv_xml $userArgsArray(drv_xml)
            array set ret_arr [sth::sthCore::invoke "stc::perform loadfromxml -filename $drv_xml -parentconfig $::sth::sthCore::GBLHNDMAP(project)"]
            set drv_handle $ret_arr(-Config)
            set drvResultQ [sth::sthCore::invoke "stc::get $drv_handle -children-PresentationResultQuery"]
        } else {
            set drv [sth::sthCore::invoke "stc::create DynamicResultView -under $::sth::sthCore::GBLHNDMAP(project) -Name $drv_name"]
            set drvResultQ [sth::sthCore::invoke "stc::create PresentationResultQuery -under $drv -Name $drv_name "]
            if {[regexp "^$" $userArgsArray(where)]} {
                set mywhere $userArgsArray(where)
            } else {
                set mywhere "\{$userArgsArray(where)\}"
            }
            
            if {[regexp "\{" $userArgsArray(sort_by)] || [regexp "^$" $userArgsArray(sort_by)]} {
                set mysort_by $userArgsArray(sort_by)
            } else {
                set mysort_by "\{$userArgsArray(sort_by)\}"
            }
            sth::sthCore::invoke "stc::config $drvResultQ -SelectProperties \"$userArgsArray(properties)\"\
                                                  -FromObjects \"$userArgsArray(query_from)\"\
                                                  -LimitSize $userArgsArray(size)\
                                                  -SortBy \"$mysort_by\"\
                                                  -WhereConditions \"$mywhere\"\
												  -DisableAutoGrouping \"$userArgsArray(disable_autogroup)\"\
                                                  -GroupByProperties \"$userArgsArray(group_by)\""
            set drv_handle $drv;
        }
        sth::sthCore::invoke "stc::perform SubscribeDynamicResultViewCommand -DynamicResultView $drv_handle"
        sth::sthCore::invoke "stc::perform UpdateDynamicResultViewCommand -DynamicResultView $drv_handle"
        ::sth::sthCore::invoke stc::sleep 3;
    } else {
        sth::sthCore::invoke "stc::perform UpdateDynamicResultViewCommand -DynamicResultView $drv_handle"
        ::sth::sthCore::invoke stc::sleep 3;
        set drvResultQ [sth::sthCore::invoke "stc::get $drv_handle -children-PresentationResultQuery"]
    }
    
    set resultViewDataList [sth::sthCore::invoke "stc::get $drvResultQ -children-ResultViewData"]
    keylset drvStatsKeyedList result_count [llength $resultViewDataList]
    set properties [sth::sthCore::invoke "stc::get $drvResultQ -SelectProperties"]
    set property_num [llength $properties]
    set i 0
    foreach resultViewData $resultViewDataList {
        set resultDataList [sth::sthCore::invoke "stc::get $resultViewData -ResultData"]
        set raw_value ""
        set j 0
        foreach property $properties {
            set key [join [split $property "\."] {}]
            set value [lindex $resultDataList $j]
            if {$value != ""} {
                keylset raw_value $key $value 
            }
            incr j
        }
        
        ##handle sub results
        # sth::sthCore::invoke "stc::perform ExpandResultViewDataCommand  -ResultViewData $resultViewData"
        # if {[sth::sthCore::invoke "stc::get $resultViewData -children-ResultViewData"] != ""} {
            # set resultViewDataListtemp [sth::sthCore::invoke "stc::get $resultViewData -children-ResultViewData"]
            # set resultViewDataListsub [sth::sthCore::invoke "stc::get $resultViewDataListtemp -children-ResultViewData"]
            # keylset raw_value result_count [llength $resultViewDataListsub]
            # set propertiessub [sth::sthCore::invoke "stc::get $drvResultQ -SelectProperties"]
            # set property_numsub [llength $propertiessub]
            # set subi 0
            # foreach resultViewDatasub $resultViewDataListsub {
                # set resultDataListsub [sth::sthCore::invoke "stc::get $resultViewDatasub -ResultData"]
                # set raw_valuesub ""
                # set subj 0
                # foreach propertysub $propertiessub {
                    # set key [join [split $propertysub "\."] {}]
                    # set value [lindex $resultDataListsub $subj]
                    # if {$value != ""} {
                        # keylset raw_valuesub $key $value
                    # }
                    # incr subj
                # }
                # keylset raw_value item$subi $raw_valuesub
                # incr subi
            # }
        # } else {
            # keylset raw_value result_count 0    
        # }
		keylset raw_value result_count 0
        keylset drvStatsKeyedList item$i $raw_value
        incr i
    }
    keylset drvStatsKeyedList handle $drv_handle
    return $drvStatsKeyedList
}

proc ::sth::Traffic::drv_stats_all {args} {
    ::sth::sthCore::Tracker ::sth::drv_stats_imp $args
 
    set drvStatsKeyedList ""
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {};
    variable sortedSwitchPriorityList {};
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    keylset drvStatsKeyedList result_count 0
    if {[catch {
        ::sth::sthCore::log debug "{Calling sth::drv_stats_all}"    
        if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args \
                                     ::sth::Traffic:: \
                                     drv_stats \
                                     userArgsArray \
                                     sortedSwitchPriorityList} eMsg]} {
           ::sth::sthCore::processError drvStatsKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
           return $drvStatsKeyedList
        }
        set drv_name $userArgsArray(drv_name)
        ##set resultviewmode into BASIC
        set resultoptions [sth::sthCore::invoke "stc::get project1 -children-resultoptions"]
        sth::sthCore::invoke "stc::config $resultoptions -resultviewmode BASIC"
        if {$::sth::Traffic::drv_all_handle == ""} {
            set drv [sth::sthCore::invoke "stc::create DynamicResultView -under $::sth::sthCore::GBLHNDMAP(project) -Name $drv_name"]
            set drvResultQ [sth::sthCore::invoke "stc::create PresentationResultQuery -under $drv -Name $drv_name "]
            
            sth::sthCore::invoke "stc::config $drvResultQ -SelectProperties \"$userArgsArray(properties)\"\
                                                  -FromObjects \"$userArgsArray(query_from)\"\
                                                  -LimitSize $userArgsArray(size)\
                                                  -DisableAutoGrouping \"$userArgsArray(disable_autogroup)\"\
                                                  -GroupByProperties \"$userArgsArray(group_by)\""
            set ::sth::Traffic::drv_all_handle $drv;
            sth::sthCore::invoke "stc::perform SubscribeDynamicResultViewCommand -DynamicResultView $::sth::Traffic::drv_all_handle"
            sth::sthCore::invoke "stc::perform UpdateDynamicResultViewCommand -DynamicResultView $::sth::Traffic::drv_all_handle"
            ::sth::sthCore::invoke stc::sleep 3
        } else {
            sth::sthCore::invoke "stc::perform UpdateDynamicResultViewCommand -DynamicResultView $::sth::Traffic::drv_all_handle"
            ::sth::sthCore::invoke stc::sleep 3
            set drvResultQ [sth::sthCore::invoke "stc::get $::sth::Traffic::drv_all_handle -children-PresentationResultQuery"]
        }
        
        set resultViewDataList [sth::sthCore::invoke "stc::get $drvResultQ -children-ResultViewData"]
        keylset drvStatsKeyedList result_count [llength $resultViewDataList]
        set properties [sth::sthCore::invoke "stc::get $drvResultQ -SelectProperties"]
        set property_num [llength $properties]
        set i 0
        foreach resultViewData $resultViewDataList {
            set resultDataList [sth::sthCore::invoke "stc::get $resultViewData -ResultData"]
            set raw_value ""
            set j 0
            foreach property $properties {
                set key [join [split $property "\."] {}]
                set value [lindex $resultDataList $j]
                if {$value != ""} {
                    keylset raw_value $key $value 
                }
                incr j
            }
            
            ##handle sub results
            sth::sthCore::invoke "stc::perform ExpandResultViewDataCommand  -ResultViewData $resultViewData"
            if {[sth::sthCore::invoke "stc::get $resultViewData -children-ResultViewData"] != ""} {
                set resultViewDataListtemp [sth::sthCore::invoke "stc::get $resultViewData -children-ResultViewData"]
                set resultViewDataListsub [sth::sthCore::invoke "stc::get $resultViewDataListtemp -children-ResultViewData"]
                keylset raw_value result_count [llength $resultViewDataListsub]
                set propertiessub [sth::sthCore::invoke "stc::get $drvResultQ -SelectProperties"]
                set property_numsub [llength $propertiessub]
                set subi 0
                foreach resultViewDatasub $resultViewDataListsub {
                    set resultDataListsub [sth::sthCore::invoke "stc::get $resultViewDatasub -ResultData"]
                    set raw_valuesub ""
                    set subj 0
                    foreach propertysub $propertiessub {
                        set key [join [split $propertysub "\."] {}]
                        set value [lindex $resultDataListsub $subj]
                        if {$value != ""} {
                            keylset raw_valuesub $key $value
                        }
                        incr subj
                    }
                    keylset raw_value item$subi $raw_valuesub
                    incr subi
                }
            } else {
                keylset raw_value result_count 0    
            }
            keylset drvStatsKeyedList item$i $raw_value
            incr i
        }
    } ErrMsg]} {
        ::sth::sthCore::processError drvStatsKeyedList "Warning: ::sth::Traffic::drv_stats_all:$ErrMsg"; 
    }
    keylset drvStatsKeyedList handle $::sth::Traffic::drv_all_handle
    return $drvStatsKeyedList
}


proc ::sth::create_csv_file {args} {
    ::sth::sthCore::Tracker ::sth::create_csv_file $args
    set csvKeyedList ""
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {};
    variable sortedSwitchPriorityList {};
    ::sth::sthCore::log debug "{Calling sth::drv_stats}"

    if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args \
                                 ::sth::Traffic:: \
                                 create_csv_file \
                                 userArgsArray \
                                 sortedSwitchPriorityList} eMsg]} {
       ::sth::sthCore::processError csvKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
       return $csvKeyedList
    }
    set result_view_handles $userArgsArray(result_view_handle)
    
    if {[info exists ::sth::sthCore::custom_path]} {
       set TestResultSettingObject [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) -children-TestResultSetting]
       ::sth::sthCore::invoke stc::config $TestResultSettingObject -ResultsDirectory "$::sth::sthCore::custom_path" -SaveResultsRelativeTo "NONE"
    }
    
    if {[catch {
        foreach result_view_handle $result_view_handles {
            puts $result_view_handle
            set i 0
            set write_mode $userArgsArray(write_mode)
            if {$i > 0} {
                set write_mode "append"
            }
            sth::sthCore::invoke "stc::perform ExportResults \
                            -ColumnHeaderStyle $userArgsArray(column_style)\
                            -filenameprefix $userArgsArray(file_name) \
                            -resultview $result_view_handle \
                            -WriteMode $write_mode"
            incr i
        }
    } eMsg]} {
       ::sth::sthCore::processError csvKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
       return $csvKeyedList
    }
    keylset csvKeyedList status 1
    return $csvKeyedList
}
