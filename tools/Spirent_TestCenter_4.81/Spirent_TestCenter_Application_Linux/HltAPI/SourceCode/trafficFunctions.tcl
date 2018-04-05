# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Traffic:: {
    ## processElapsedTime: a flag enabling the code block which especially processes elapsed_time
    ## if in the future STC bll provides elapsed_time directly, set the processElapsedTime to 0 to disable the codes
    variable processElapsedTime 1
    ## streamTxFrameRate: store the frame rate before EOT on stream basis
    array set streamTxEOTFrameRate {}
    ## portTxFrameRate: store the frame rate before EOT for the port
    array set portTxEOTFrameRate {}
    ## pastElapsedTime: store all the elapsed times on stream basis
    array set pastStreamElapTime {}
    array set curStreamElapTime {}
    
    array set generatorMode ""
    # the results are clear/reset or not
    set isClear 0
    set ::sth::Traffic::sbTxIndex {}
    set ::sth::Traffic::sbRxIndex {}
}

namespace eval ::sth::sthCore:: {}
#namespace eval ::sth::Session:: {}


proc ::sth::Traffic::processTraffic_controlPort_handle {} {
    
    upvar trafficControlKeyedList trafficControlKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::Session::PORTHNDLIST
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    if {[info exist userArray(port_handle)]} {
        set listOfpHandles $userArray(port_handle)
        if {$listOfpHandles == "all"} {
            return $::sth::sthCore::SUCCESS;
        }
        foreach portHnd $listOfpHandles {
            if {[info exists ::sth::Session::PORTHNDLIST($portHnd)]} {
            } else {
                set errMsg "Internal Command Error: port_handle $portHnd is not valid"
                return -code 1 -errorcode -1 $errMsg;
            }
        }
    } elseif {[info exist userArray(stream_handle)]} {
        if {$userArray(stream_handle) ne "all"} {
            set streamHandleList $userArray(stream_handle)
        } else {
                set ports [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
                foreach port $ports {
                   foreach strmblk [sth::sthCore::invoke ::sth::sthCore::invoke stc::get $port -children-streamblock] {
                      lappend streamHandleList $strmblk
                   }
                }
        }
        set streamExistList ""
        if {[info exists ::sth::Traffic::arrayPortHnd]}  {
            foreach port [array names ::sth::Traffic::arrayPortHnd] {
                set streamExistList "$streamExistList $::sth::Traffic::arrayPortHnd($port)"
            }
            foreach stream $streamHandleList {
                if {[lsearch -exact $streamExistList $stream] < 0} {
                    return -code error "stream $stream not existed" 
                }
            }
        } else {
            return -code error "streams $streamHandleList not existed" 
        }
    }
    return $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::createviewlist {type} {
    
    set TableName ::sth::Traffic::traffic_stats\_$type\_results_stcattr
    set aggregateList [array names $TableName]
    
    foreach ele $aggregateList {
        set myVar "::sth::Traffic::traffic_stats\_$type\_results_stcattr"
        set stcName [set $myVar\($ele)];
        if {($stcName == "_none_") || ($stcName == "hlt" )} {
        } else {
            lappend viewTrafficList $stcName;
        }
    }
    
    return $viewTrafficList
}

# Analyzer filter names/values depend on what has been specified. Create dynamically.
proc ::sth::Traffic::createFilterViewlist {} {
    
    set filterNameQuery "select FilteredName_1, FilteredName_2, FilteredName_3, FilteredName_4,\
    FilteredName_5, FilteredName_6, FilteredName_7, FilteredName_8, FilteredName_9, FilteredName_10\
    from RxEotAnalyzerFilterNamesTable where id=1"
    
    set viewTrafficList ""
    set filterNameList [db eval $filterNameQuery]
    if {$filterNameList != ""} {
        # mapping: FilteredValue_* -> vlan_id, tos, ...
        array set ::sth::Traffic::filterValueIdToName {}
        
        for {set i 0} {$i < 10} {incr i}  {
            set filterName [lindex $filterNameList $i]
            if {$filterName != ""} {
                foreach filter $::sth::Traffic::FilterType {
                    if {$filterName == $::sth::Traffic::filter_key_column($filter)} {
                        set j [expr $i + 1]
                        lappend viewTrafficList FilteredValue_$j
                        set ::sth::Traffic::filterValueIdToName(FilteredValue_$j) $filter
                        break
                    }
                }
            } else {
                break
            }
        }
    }
    return $viewTrafficList
}

proc ::sth::Traffic::createPropertyViewlist {type properties} {

    set aggregateList $properties
    set viewTrafficList ""
    
    foreach ele $aggregateList {
        set myVar "::sth::Traffic::traffic_stats\_$type\_results_stcattr"
        set stcName [set $myVar\($ele)];
        if {($stcName == "_none_") || ($stcName == "hlt" )} {
        } else {
            lappend viewTrafficList $stcName;
        }
    }
    
    return $viewTrafficList
}


proc ::sth::Traffic::processTrafficStatsSubscribeProjectLevelCounters {type ConfigType resulttype} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    
    set TableName ::sth::Traffic::traffic_stats\_$type\_results_stcattr
    set aggregateList [array names $TableName]
    
    foreach ele $aggregateList {
        set hltname $ele
        set myVar "::sth::Traffic::traffic_stats\_$type\_results_stcattr"
        set stcName [set $myVar\($ele)];
        if {($stcName == "_none_") || ($stcName == "hlt" )} {
        } else {
            lappend viewTrafficList $stcName;
        }
    }
    
    ::sth::sthCore::log debug "Subscribe $type Results..."

    set subscribeCommand "-Parent $::sth::sthCore::GBLHNDMAP(project) \
                                -ConfigType $ConfigType \
                                -resulttype $resulttype \
                                -viewAttributeList {$viewTrafficList}"
    if {[catch {sth::sthCore::invoke "stc::subscribe $subscribeCommand"} subscribeResultDataStatus]} {
        ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::invoke subscribe Failed: Error subscribing GeneatorPortResults" {}
        return $::sth::sthCore::FAILURE
    } 
           
    # MGJ: Don't sleep for all result types.
    #      Anything that requires the command "RefreshResultView" doesn't need a delay.
    set nodelayresulttypes [string tolower "RxStreamBlockResults TxStreamBlockResults"]
    if { [lsearch -exact $nodelayresulttypes [string tolower $resulttype]] == -1 } {
        #::sth::sthCore::invoke stc::sleep 15
        ::sth::sthCore::invoke stc::sleep 3
    } else {
        sth::sthCore::invoke "stc::perform RefreshResultView -ResultDataSet $subscribeResultDataStatus"
    }
    
    return $subscribeResultDataStatus 
}

# Subscribe FilteredStreamResults for ports.
#Arguments:
#   type        Result type. For example, "stream_rx".
#   properties  Requested result attributes.
#   portlist    The ports under which FilteredStreamResults will be subscribed. Empty means all ports.
proc ::sth::Traffic::processTrafficStatsSubscribeFilteredCounters {type properties {portlist ""}} {
    upvar trafficStatsKeyedList trafficStatsKeyedList
    upvar 1 userArgsArray userArray
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project)
    # resultdataset object -> subscribed port. mapping example: resultdataset2 -> port1
    array unset ::sth::Traffic::filteredResultDataSetToPort
    array set ::sth::Traffic::filteredResultDataSetToPort {}
    if {$properties == "_none_"} {
        return;
    }
    
    if {$type == "stream_rx"} {
        set ::sth::Traffic::viewRxlist [::sth::Traffic::createviewlist $type]
        set viewTrafficList $::sth::Traffic::viewRxlist
    }
    
    if {$properties != "" } {
        set viewTrafficList [::sth::Traffic::createPropertyViewlist $type $properties]
    }
    # FilteredStreamResults has no -RxPort attribute, remove RxPort here, will 
    # construct rx_port and add it to final output in later functions.
    regsub -nocase {rxport} $viewTrafficList "" viewTrafficList
    ::sth::sthCore::log debug "Subscribe $type FilteredStreamResults..."

    if {$portlist == ""} {
        set port_list [sth::sthCore::invoke "stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port"]
    } else {
        set port_list $portlist
    }
    
    # TODO: Can subscribe FilteredStreamResults with one subscription as follows:
    # But it will need 2 stc::get for each stream to get rxport. Use multiple subscription for now.
    # Subscribe FilteredStreamResults once.
    # set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under $ProjHnd]
    # foreach port $portlist {
        # sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList $port -ConfigClassId Analyzer -ResultClassId FilteredStreamResults"
    # }
    # sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
    
    # Subscribe FilteredStreamResults one port at a time.
    foreach port $port_list {
        set subscribeCommand "-Parent $::sth::sthCore::GBLHNDMAP(project) \
                              -ResultParent {$port} \
                              -ConfigType Analyzer \
                              -resulttype FilteredStreamResults \
                              -viewAttributeList {$viewTrafficList}"
        if {[info exists userArray(records_per_page)]} {
            append subscribeCommand " -RecordsPerPage $userArray(records_per_page)"
        }
        if {[catch {sth::sthCore::invoke "stc::subscribe $subscribeCommand"} subscribeResultDataStatus]} {
            ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::invoke subscribe Failed: Error subscribing FilteredStreamResults" {}
            return $::sth::sthCore::FAILURE
        }
        set ::sth::Traffic::filteredResultDataSetToPort($subscribeResultDataStatus) $port
    }
    return [array names ::sth::Traffic::filteredResultDataSetToPort]
}

proc ::sth::Traffic::processTrafficStatsSubscribeCounters {type ConfigType resulttype level parent properties} {
    
    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTrafficStatsSubscribeCounters}"
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    
    if {$properties == "_none_"} {
        return;
    }

    if {($type == "stream_tx") && ($::sth::Traffic::viewListTxStreamBlock == 0)} {
        set ::sth::Traffic::viewTxlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListTxStreamBlock 1
    }
    if {($type == "stream_rx") && ($::sth::Traffic::viewListRxStreamBlock == 0)} {
        set ::sth::Traffic::viewRxlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListRxStreamBlock 1
    }
    
    if {($type == "aggregate_txjoin") && ($::sth::Traffic::viewListAggTx == 0)} {
        set ::sth::Traffic::viewAggTxlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListAggTx 1
    }
    if {($type == "aggregate_rxjoin") && ($::sth::Traffic::viewListAggRx == 0)} {
        set ::sth::Traffic::viewAggRxlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListAggRx 1
    }
    
    if {($type == "out_of_filter") && ($::sth::Traffic::viewListoof == 0)} {
        set ::sth::Traffic::viewooflist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListoof 1
    }
    if {($type == "diffserv") && ($::sth::Traffic::viewListqos == 0)} {
        set ::sth::Traffic::viewqoslist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListqos 1
    }
    
    if {($type == "userdefined") && ($::sth::Traffic::viewListcustomized == 0)} {
        set ::sth::Traffic::viewcustomizedlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListcustomized 1
    }
    
    if {($type == "fc_port") && ($::sth::Traffic::viewListfcresult == 0)} {
        set ::sth::Traffic::viewfcresultlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListfcresult 1
    }
    
    if {($type == "system_monitor") && ($::sth::Traffic::viewListsysmonitorresult == 0)} {
        set ::sth::Traffic::viewsysmonitorresultlist [::sth::Traffic::createviewlist $type]
        set ::sth::Traffic::viewListsysmonitorresult 1
    }

    if {$type == "stream_tx"} {
        set viewTrafficList $::sth::Traffic::viewTxlist
    } elseif {$type == "stream_rx"} {
        set viewTrafficList $::sth::Traffic::viewRxlist
    } elseif {$type == "aggregate_txjoin"} {
        set viewTrafficList $::sth::Traffic::viewAggTxlist
    } elseif {$type == "aggregate_rxjoin"} {
        set viewTrafficList $::sth::Traffic::viewAggRxlist
    } elseif {$type == "out_of_filter"} {
        set viewTrafficList $::sth::Traffic::viewooflist
    } elseif {$type == "diffserv"} {
        set viewTrafficList $::sth::Traffic::viewqoslist
    } elseif {$type == "userdefined"} {
        set viewTrafficList $::sth::Traffic::viewcustomizedlist
    } elseif {$type == "fc_port"} {
        set viewTrafficList $::sth::Traffic::viewfcresultlist
    } elseif {$type == "system_monitor"} {
        set viewTrafficList $::sth::Traffic::viewsysmonitorresultlist
    }

    if {$properties != "" } {
        set viewTrafficList [::sth::Traffic::createPropertyViewlist $type $properties]
    }

    ::sth::sthCore::log debug "Subscribe $type Results..."

    #add by cf. Once set analyzer filters, FilteredValue_[1-10] are returned anyways. No need to specify them. 
    if {$resulttype =="FilteredStreamResults"} {
        set viewTrafficList "SigFrameCount FrameRate BitRate"
    }
    #end

    set subscribeCommand "-Parent $::sth::sthCore::GBLHNDMAP(project) \
                                -ResultParent {$parent} \
                                -ConfigType $ConfigType \
                                -resulttype $resulttype \
                                -viewAttributeList {$viewTrafficList}"
    if {[info exists userArray(records_per_page)]} {
        append subscribeCommand " -RecordsPerPage $userArray(records_per_page)"
    }
    if {[catch {sth::sthCore::invoke "stc::subscribe $subscribeCommand"} subscribeResultDataStatus]} {
        ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::invoke subscribe Failed: Error subscribing GeneatorPortResults" {}
        return $::sth::sthCore::FAILURE
    }
    # MGJ: Don't sleep for all result types.
    #      Anything that requires the command "RefreshResultView" doesn't need a delay.
    set nodelayresulttypes [string tolower "RxStreamBlockResults TxStreamBlockResults"]
    if { [lsearch -exact $nodelayresulttypes [string tolower $resulttype]] == 0 } {
        sth::sthCore::invoke "stc::perform RefreshResultView -ResultDataSet $subscribeResultDataStatus"
    }
    
    return $subscribeResultDataStatus 
}


proc ::sth::Traffic::delay {resultTypeList} {

    set nodelayresulttypes [string tolower "RxStreamBlockResults TxStreamBlockResults"]
    if { [lsearch -exact $nodelayresulttypes [string tolower $resultTypeList]] == -1 } {
        ::sth::sthCore::invoke stc::sleep 3
    }

}


proc ::sth::Traffic::processUnSubscribeProjectLevelCounters {ResultDataList} {
    
    upvar cleanUpSessionKeyList cleanUpSessionKeyList;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    if {[llength $ResultDataList] != 0} {
        foreach ele $ResultDataList {
            sth::sthCore::invoke "stc::unsubscribe $ele"
            sth::sthCore::invoke "stc::delete $ele"
        }
    }
}

proc ::sth::Traffic::getTypeProperties {type properties} {
    set propertiesValues ""
    
    foreach key $properties {
        if {[regsub -all "^$type\." $key "" key]} {
            lappend propertiesValues $key
        }
    }
    return $propertiesValues;
}

proc ::sth::Traffic::processTrafficStatsGetAggTxCounters {porthandlevalues properties} {
    
    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTrafficStatsGetAggTxCounters}"
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set currPort $porthandlevalues;
    
    if {$properties == "_none_"} {
        return;
    }
    
    foreach currPort $porthandlevalues {
            #set generatorResult $::sth::Traffic::arrayGeneratorResult($currPort);
            if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-generator"} generatorhndl]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Generator children" {}
                return $::sth::sthCore::FAILURE
            } 
            if {[catch {::sth::sthCore::invoke stc::get $generatorhndl "-children-generatorportresults"} generatorResult]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Generatorportresults children" {}
                return $::sth::sthCore::FAILURE
            }
            set TableName ::sth::Traffic::traffic_stats_aggregate_tx_results_stcattr
            if {$properties == ""} {
                set aggregateList [array names $TableName]
            } else {
                set aggregateList $properties
            }
            if {[string equal $generatorResult ""]} {
                foreach hltName $aggregateList {
                    set stcName $::sth::Traffic::traffic_stats_aggregate_tx_results_stcattr($hltName)
                    if {$stcName == "_none_"} {
                    } else { 
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.tx.$hltName "0"]
                    }
                }
            } else {
                # if result object is subscribered for two times, it will return 2 result handles. Just add here in case.  
                set generatorResult [lindex $generatorResult 0]
                set stcReturnList [::sth::sthCore::invoke stc::get $generatorResult];
                set ipPktscount 0
                set lengthcount 0
                array set stcArray $stcReturnList;
                set listlength [llength $aggregateList]
                foreach hltName $aggregateList {
                    incr lengthcount
                    set stcName $::sth::Traffic::traffic_stats_aggregate_tx_results_stcattr($hltName)
                        #puts "--> $stcName"
                    if {$stcName == "_none_" || $stcName == "hlt"} {
                    } else {
                        set stcName -$stcName
                        set stcValue $stcArray($stcName);
                        #if {$hltName == "pkt_bit_rate"} {
                        #    set stcValue [expr {$stcValue * 8}]
                        #}
                        
                        if {($stcName == "-GeneratorIpv4FrameCount") || ($stcName == "-GeneratorIpv6FrameCount")} {
                            set ipPktscount [expr {$ipPktscount + $stcValue}]
                        } else {
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.tx.$hltName "$stcValue"]
                        }
                    }
                    if {$lengthcount == $listlength && $properties == ""} {
                        set hltName "ip_pkts"
                        set stcValue $ipPktscount
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.tx.$hltName "$stcValue"]
                        set ipPktscount 0
                        set lengthcount 0
                    }
                }
                
                ## process elapsed_time (added by xiaozhi)
                if {$::sth::Traffic::processElapsedTime && $properties == ""} {
                    set hltName "elapsed_time"
                    set frameCount [keylget trafficStatsKeyedList $currPort.aggregate.tx.total_pkts]
                    set frameRate [keylget trafficStatsKeyedList $currPort.aggregate.tx.total_pkt_rate]
                    set stcValue [::sth::Traffic::processTrafficTxElapsedTime $currPort $frameCount $frameRate]
                    keylset trafficStatsKeyedList $currPort.aggregate.tx.$hltName $stcValue
                }
            } 
        }
}

proc ::sth::Traffic::processTrafficStatsGetCustomizedCounters {porthandlevalues properties} {
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    variable ::sth::sthCore::analyzerResultlist;
    set currPort $porthandlevalues;
    set resultDataSetList $::sth::Traffic::userDefinedDataset
    
    foreach currPort $porthandlevalues {
        if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-analyzer"} analyzerhndl]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting analyzer children" {}
            return $::sth::sthCore::FAILURE
        } 
        if {[catch {::sth::sthCore::invoke stc::get $analyzerhndl "-children-analyzerportresults"} analyzerhndlResult]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting analyzerhndlResult children" {}
            return $::sth::sthCore::FAILURE
        }

        set TableName ::sth::Traffic::traffic_stats_userdefined_results_stcattr
        if {$properties == ""} {
            set aggregateList [array names $TableName]
        } else {
            set aggregateList $properties
        }
        
        if {[string equal $analyzerhndlResult ""]} {
            foreach hltName $aggregateList {
                set stcName $::sth::Traffic::traffic_stats_userdefined_results_stcattr($hltName)
                if {$stcName == "_none_"} {
                } else { 
                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.userdefined.$hltName "0"]
                }
            }
        } else {
            set analyzerResult [lindex $analyzerhndlResult 0]
            set stcReturnList [::sth::sthCore::invoke stc::get $analyzerResult];
            array set stcArray $stcReturnList;
            
            foreach hltName $aggregateList {
                set stcName $::sth::Traffic::traffic_stats_userdefined_results_stcattr($hltName)
                #puts "--> $stcName"
                if {$stcName == "_none_" || $stcName == "hlt"} {
                } else {
                    set stcName -$stcName 
                    set stcValue $stcArray($stcName);
                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.userdefined.$hltName "$stcValue"]
                }
            }
        }
    }
}

proc ::sth::Traffic::processTrafficStatsGetAggRxCounters {porthandlevalues properties} {
    
    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTrafficStatsGetAggRxCounters}"
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    variable ::sth::sthCore::analyzerResultlist;
    set currPort $porthandlevalues;
    
    if {$properties == "_none_"} {
        return;
    }
    set captureAnaFil [::sth::sthCore::invoke stc::get \
                                            [::sth::sthCore::invoke stc::get \
                                                [::sth::sthCore::invoke stc::get $currPort "-children-capture"]\
                                            "-children-CaptureFilter"]\
                                      "-children-CaptureAnalyzerFilter"]
    
    set resultDataSetList $::sth::Traffic::aggRxjoinDataset
    if {[info exists ::sth::Traffic::aggRxQoSDataset] && ($::sth::Traffic::aggRxQoSDataset != "")} {
        # get FilteredValue_* column names before looping
        if {[catch {::sth::sthCore::invoke stc::get $::sth::Traffic::aggRxQoSDataset -ResultHandleList} resultHdlList]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting ResultDataSet -ResultHandleList" {}
            return $::sth::sthCore::FAILURE;
        }
        if {[llength $resultHdlList] > 0} {
            # filter name -> FilteredValue_* (attribute name in object)
            # mapping example: vlan_id -> FilteredValue_1, tos -> FilteredValue_3, ...
            array unset ::sth::Traffic::filter_value_column
            array set ::sth::Traffic::filter_value_column {}
            
            set stcReturnList [::sth::sthCore::invoke stc::get [lindex $resultHdlList 0]]
            array set stcArray $stcReturnList
            foreach filter $::sth::Traffic::FilterType {
                for {set i 1} {$i <= 10} {incr i}  {
                    if {$stcArray(-FilteredName_$i) == $::sth::Traffic::filter_key_column($filter)} {
                        set ::sth::Traffic::filter_value_column($filter) FilteredValue_$i
                        break
                    }
                }
            }
            # Add for looping
            append resultDataSetList " $::sth::Traffic::aggRxQoSDataset"
        }
    } else {
        set ::sth::Traffic::aggRxQoSDataset ""
    }
    
    # changed by Yulin Chen for paged results
    foreach resultDataSet $resultDataSetList {
        if {[catch {::sth::sthCore::invoke stc::get $resultDataSet "-TotalPageCount"} resultPageCount]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting ResultDataSet -TotalPageCount" {}
            return $::sth::sthCore::FAILURE;
        }

        for {set i 1} {$i<= $resultPageCount} {incr i} {
            if {$i > 1} {
                if {[catch {::sth::sthCore::invoke stc::config $resultDataSet "-PageNumber $i"} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                if {[catch {::sth::sthCore::doStcApply} $err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
            }
            
            if {[catch {::sth::sthCore::invoke stc::get $resultDataSet "-ResultHandleList"} resultHdlList]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting ResultDataSet -ResultHandleList" {}
                return $::sth::sthCore::FAILURE;
            }
            
            if {$resultDataSet == $::sth::Traffic::aggRxjoinDataset} {
                set TableName ::sth::Traffic::traffic_stats_aggregate_rx_results_stcattr
                if {$properties == ""} {
                    set aggregateList [array names $TableName]
                } else {
                    set aggregateList $properties
                }
                
                if {$captureAnaFil != ""} {
                    set TableName ::sth::Traffic::traffic_stats_aggregate_rxjoin_results_stcattr
                    set aggregateList [array names $TableName]
                }
                
                if {[string equal $resultHdlList ""]} {
                    if {$i == 1} {
                        foreach currPort $porthandlevalues {
                            
                            
                            foreach hltName $aggregateList {
                                if {$captureAnaFil != ""} {
                                    set stcName $::sth::Traffic::traffic_stats_aggregate_rxjoin_results_stcattr($hltName)
                                } else {
                                    set stcName $::sth::Traffic::traffic_stats_aggregate_rx_results_stcattr($hltName)
                                }
                                if {$stcName == "_none_"} {
                                } else {
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$hltName "0"]
                                }
                            }
                        }
                    }
                } else {
                    # if result object is subscribered for two times, it will return 2 result handles. Just add here in case.  
                    set analyzerResult [lindex $resultHdlList 0]
                    set stcReturnList [::sth::sthCore::invoke stc::get $analyzerResult];
                    set ipPktscount 0
                    set lengthcount 0
                    set analyzerResultParent [::sth::sthCore::invoke stc::get $analyzerResult -parent];
                    array set stcArray $stcReturnList;
                    set listlength [llength $aggregateList]
                    
                    foreach hltName $aggregateList {
                        incr lengthcount
                        if {$captureAnaFil != ""} {
                            set stcName $::sth::Traffic::traffic_stats_aggregate_rxjoin_results_stcattr($hltName)
                        } else {
                            set stcName $::sth::Traffic::traffic_stats_aggregate_rx_results_stcattr($hltName)
                        }
                        #puts "--> $stcName"
                        if {$stcName == "_none_" || $stcName == "hlt"} {
                        } else {
                            set stcName -$stcName 
                            set stcValue $stcArray($stcName);
                            #if {$hltName == "pkt_bit_rate"} {
                            #    set stcValue [expr {$stcValue * 8}]
                            #}
                            if {($stcName == "-Ipv4FrameCount") || ($stcName == "-Ipv6FrameCount")} {
                                set ipPktscount [expr {$ipPktscount + $stcValue}]
                            } else {
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$hltName "$stcValue"]
                                
                            }
                        }
                        if {$lengthcount == $listlength && $properties == ""} {
                            set hltName "ip_pkts"
                            set stcValue $ipPktscount
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$hltName "$stcValue"]
                            set ipPktscount 0
                            set lengthcount 0
                        }
                    }
                }
            }
            
            #add by cf. if the filterResults is not empty, we will get the value we want in each filterResult
            if {$resultDataSet == $::sth::Traffic::aggRxQoSDataset} {                   
                foreach filterResult $resultHdlList {
                    set stcReturnList [::sth::sthCore::invoke stc::get $filterResult]
                    array set stcArray $stcReturnList
                    foreach filter $::sth::Traffic::FilterType {
                        set keyFilteredValue $::sth::Traffic::filter_value_column($filter)
                    
                        if {$filter == "tos"} {
                            set bin $stcArray(-$keyFilteredValue)
                            #translate the tos bin to decimal value     
                            set tosbin [string range $bin 3 6]
                            set precbin [string range $bin 0 2]
                            set tosValue [::sth::sthCore::binToInt $tosbin]
                            set precValue [::sth::sthCore::binToInt $precbin]
                            
                            set stcValue $stcArray(-FrameCount)
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.count "$stcValue" add]
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.count "$stcValue" add]
                            set stcValue $stcArray(-FrameRate)
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_pps "$stcValue" add]
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.rate_pps "$stcValue" add]
                            set stcValue $stcArray(-BitRate)
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_bps "$stcValue" add]
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.rate_bps "$stcValue" add]
                         } else {
                            set id $stcArray(-$keyFilteredValue)
                            if {$filter == "vlan_pri" || $filter == "vlan_pri_inner" || $filter == "dscp"} {
                                if {$filter != "dscp"} {
                                    set id [::sth::sthCore::binToInt $stcArray(-$keyFilteredValue)]
                                }
                                if { [regexp -all {vlan_pri|dscp} $::sth::Traffic::FilterType] == 1 } {
                                    # For backward compatiblity, output 'qos' if only one of "vlan_pri", "vlan_pri_inner" and "dscp" is specified.
                                    set filter "qos"
                                }
                            } else {
                                # For backward compatiblity, when outputting, "vlan_id", "vlan_id_inner" -> "vlan", "vlan_inner"
                                regsub vlan_id $filter vlan filter
                            }
                            set stcValue $stcArray(-FrameCount)
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$filter.$id.count "$stcValue" add]
                            set stcValue $stcArray(-FrameRate)
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$filter.$id.rate_pps "$stcValue" add]
                            set stcValue $stcArray(-BitRate)
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$filter.$id.rate_bps "$stcValue" add]
                        }
                    }
                }
            }
        }
    }
}

proc ::sth::Traffic::processTrafficStatsGetEOTAggCounters {portlistname resulttype properties} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set TableName ::sth::Traffic::traffic_stats_aggregate\_$resulttype\_results_stcattr
    if {$properties == ""} {
        set aggregateList [array names $TableName]
    } else {
        set aggregateList $properties
    }
    foreach currPort $portlistname {
        set ipPktscount 0
        set lengthcount 0
        set listlength [llength $aggregateList]
        set captureAnaFil [::sth::sthCore::invoke stc::get \
                                            [::sth::sthCore::invoke stc::get \
                                                [::sth::sthCore::invoke stc::get $currPort "-children-capture"]\
                                            "-children-CaptureFilter"]\
                                      "-children-CaptureAnalyzerFilter"]
        if {$resulttype == "rx"} {
                if {$captureAnaFil != ""} {
                    set TableName ::sth::Traffic::traffic_stats_aggregate_rxjoin_results_stcattr
                    set aggregateList [array names $TableName]
                }
        }
        foreach hltName $aggregateList {
        incr lengthcount
            if {$resulttype == "rx"} {
                if {$captureAnaFil != ""} {
                    set stcName $::sth::Traffic::traffic_stats_aggregate_rxjoin_results_stcattr($hltName)
                } else {
                    set stcName $::sth::Traffic::traffic_stats_aggregate_rx_results_stcattr($hltName)
                }
                if {$stcName != "_none_"} {
                    set stcValue $::sth::Traffic::arraySTCArray($stcName);
                    #if {$hltName == "pkt_bit_rate"} {
                    #    set stcValue [expr {$stcValue * 8}]
                    #}
                    if {($stcName == "Ipv4FrameCount") || ($stcName == "Ipv6FrameCount")} {
                        set ipPktscount [expr {$ipPktscount + $stcValue}]
                    } else {
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$hltName "$stcValue"]
                        
                    }
                }
                if {$lengthcount == $listlength && $properties == ""} {
                    set hltName "ip_pkts"
                    set stcValue $ipPktscount
                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$hltName "$stcValue"]
                    set ipPktscount 0
                    set lengthcount 0
                }
            } else {
                set stcName $::sth::Traffic::traffic_stats_aggregate_tx_results_stcattr($hltName)
                if {$stcName == "_none_"} {
                } else {
                    if {$stcName != "hlt"} {
                        set stcValue $::sth::Traffic::arraySTCArray($stcName)
                        #if {$hltName == "pkt_bit_rate"} {
                        #    set stcValue [expr {$stcValue * 8}]
                        #}
                    }
                    ## process elapsed_time (added by xiaozhi)
                    if {$hltName == "elapsed_time"} {
                        if {$::sth::Traffic::processElapsedTime == 0} { continue }
                        set stcValue [::sth::Traffic::processTrafficTxElapsedTime $currPort $::sth::Traffic::arraySTCArray(TotalFrameCount) ""]
                    }
                    ## end
                    if {($stcName == "GeneratorIpv4FrameCount") || ($stcName == "GeneratorIpv6FrameCount")} {
                        set ipPktscount [expr {$ipPktscount + $stcValue}]
                    } else {
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.tx.$hltName "$stcValue"]
                    }
                }
                if {$lengthcount == $listlength && $properties == ""} {
                    set hltName "ip_pkts"
                    set stcValue $ipPktscount
                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.tx.$hltName "$stcValue"]
                    set ipPktscount 0
                    set lengthcount 0
                }
            } 
        }
        if {$::sth::Traffic::FilterType != "" && $resulttype == "rx" && [info exists ::sth::Traffic::arrayFilterResult($currPort)]} {
            set countIndex [lsearch $::sth::Traffic::selectedDbColumns "SigFrameCount"]
            set len [llength $::sth::Traffic::arrayFilterResult($currPort)]
            foreach filter $::sth::Traffic::FilterType {
                set filterIndex [lsearch $::sth::Traffic::selectedDbColumns $::sth::Traffic::filterValueNameToId($filter)]                
                set filterToCountDiff [expr $countIndex - $filterIndex]
                set columnCount [llength $::sth::Traffic::selectedDbColumns]
                set filterName $filter
                for {set i $filterIndex} {$i < $len} {set i [expr $i + $columnCount]} {
                        set index [lindex $::sth::Traffic::arrayFilterResult($currPort) $i]
                        set value [lindex $::sth::Traffic::arrayFilterResult($currPort) [expr $i+$filterToCountDiff]]
                        if {$filter == "tos"} {
                            set bin $index
                            #translate the tos bin to decimal value     
                            set tosbin [string range $bin 3 6]     
                            set tosValue [::sth::sthCore::binToInt $tosbin]
                            
                            set precbin [string range $bin 0 2]     
                            set precValue [::sth::sthCore::binToInt $precbin]
                            
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.count "$value" add]
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.count "$value" add]
                            
                            if {![info exists rateArray($currPort\_tos_$tosValue)]} {
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_pps "0"]
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_bps "0"]
                                set rateArray($currPort\_tos_$tosValue) 1
                            }
                            if {![info exists rateArray($currPort\_prec_$precValue)]} {
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.rate_pps "0"]
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.rate_bps "0"]
                                set rateArray($currPort\_prec_$precValue) 1
                            }
                        } else {
                            if {$filter == "vlan_pri" || $filter == "vlan_pri_inner" || $filter == "dscp"} {
                                if {$filter != "dscp"} {
                                    set index [::sth::sthCore::binToInt $index]
                                }
                                if { [regexp -all {vlan_pri|dscp} $::sth::Traffic::FilterType] == 1 } {
                                    # For backward compatiblity, output 'qos' if only one of "vlan_pri", "vlan_pri_inner" and "dscp" is specified.
                                    set filterName "qos"
                                } 
                            } else {
                                # For backward compatiblity, when outputting, "vlan_id", "vlan_id_inner" -> "vlan", "vlan_inner"
                                regsub vlan_id $filter vlan filterName
                            }
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$filterName.$index.count "$value" add]
                            if {![info exists rateArray($currPort\_$filterName\_$index)]} {
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$filterName.$index.rate_pps "0" ]
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.aggregate.rx.$filterName.$index.rate_bps "0" ]
                                set rateArray($currPort\_$filterName\_$index) 1
                            }
                        }
                }
            }
        }
    }
}

proc ::sth::Traffic::processTrafficStatsGetEOTDiffservCounters {portname resulttype attrlist} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    
    set len [llength $::sth::Traffic::arrayDiffServResult]
    
    set attrlist [list "qos_binary" "ip_precedence" "Ecn" "diffserv" "ipv4_pkts" "ipv6_pkts" "rx_ipv4_frame_rate" "rx_ipv6_frame_rate"]

    if {$len != 0} {
           set count [expr $len/7]
           for {set i 0} {$i<$count} {incr i} {
               set index [expr $i*7]
               set qosVlaue  [lindex $::sth::Traffic::arrayDiffServResult $index]
               foreach stcName $attrlist {
                if {[regexp rate $stcName]} {
                    set stcValue 0
                } else {
                    set index [expr $index + 1]
                    set stcValue [lindex $::sth::Traffic::arrayDiffServResult $index]
                }
                keylset trafficStatsKeyedList $portname.aggregate.rx.qos.$qosVlaue.$stcName $stcValue  
               }
            }
    }
    
    
}

proc ::sth::Traffic::processTrafficStatsGetEOTStreamCounters {handlenames resulttype isStreamBlk properties detail_streams} {
    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTrafficStatsGetEOTStreamCounters}"
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 3 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP;
    variable detailedRxStats;
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    
    set TableName ::sth::Traffic::traffic_stats_streameot\_$resulttype\_results_stcattr
    
    if {$detail_streams && $::sth::Traffic::FilterType != ""} {
        set allFilterNames "tos prec qos dscp vlan vlan_inner vlan_id vlan_id_inner vlan_pri vlan_pri_inner"
        # Update the table
        foreach filter $::sth::Traffic::FilterType {
            if {$filter == "tos"} {
                #set $TableName\(prec) prec
                if {$properties != ""} {
                    lappend properties prec
                }
            } elseif {$filter == "vlan_pri" || $filter == "vlan_pri_inner" || $filter == "dscp"} {
                if { [regexp -all {vlan_pri|dscp} $::sth::Traffic::FilterType] == 1 } {
                    # For backward compatiblity, output 'qos' if only one of "vlan_pri", "vlan_pri_inner" and "dscp" is specified.
                    #set $TableName\(qos) qos
                    if {$properties != ""} {
                        lappend properties qos
                    }
                    continue
                }
            } 
            #set $TableName\($filter) $filter
            if {$properties != ""} {
                lappend properties $filter
            }
        }
    }
    
    if {$properties == ""} {
        set hltStreamList [array names $TableName]
    } else {
        set hltStreamList $properties
    }
    
    set streamblkHndl $isStreamBlk
    if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl "-parent"} currPort]} {
               ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting parent of streamBlock: $currPort" {}
               return $::sth::sthCore::FAILURE;
    }
    
    ::sth::Traffic::processRxPortResultFilter $streamblkHndl 1 enableRxPortFilter rxPortHdl
    
    foreach hltName $hltStreamList {
        if {$resulttype == "rx"} {
            #get the rx port for each streamblock
            if {$detailedRxStats == 1} {
                if {[info exists ::sth::Traffic::arraySTCArray_per_port(PortName)]} {
                    set rx_port_name_list $::sth::Traffic::arraySTCArray_per_port(PortName)
                    set rxPort ""
                    foreach rx_port_name $rx_port_name_list {
                        set objList [::sth::sthCore::invoke stc::perform GetObjects -rootlist project1 -classname port -condition "name = $rx_port_name"]
                        set obj_index [expr [lsearch $objList "-ObjectList"] + 1]
                        set PortHdl [lindex $objList $obj_index]
                        if {$PortHdl != ""} {
                            lappend rxPort $PortHdl
                        }
                    }
                } elseif {[info exists ::sth::Traffic::arraySTCArray(PortName)]} {
                    set rx_port_name $::sth::Traffic::arraySTCArray(PortName)
                    if {$rx_port_name != ""} {
                        set objList [::sth::sthCore::invoke stc::perform GetObjects -rootlist project1 -classname port -condition "name = $rx_port_name"]
                        set obj_index [expr [lsearch $objList "-ObjectList"] + 1]
                        set rxPort [lindex $objList $obj_index]
                    }
                }
            }
            
            if {$detail_streams && ($::sth::Traffic::FilterType != "") && ([lsearch $allFilterNames $hltName] != -1)} {
                set stcName $hltName
            } else {
                set stcName $::sth::Traffic::traffic_stats_streameot_rx_results_stcattr($hltName)
            }
            
            if {!$detail_streams} {
                if {$hltName == "total_pkt_rate" || $hltName == "total_pkt_bit_rate" || $hltName == "rx_sig_rate"} {
                    if {$enableRxPortFilter} {
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                        }
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "0"]
                    } else {
                        if {[info exists rxPort] && $rxPort != ""} {
                            foreach eachRxPort $rxPort {
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                                }
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $eachRxPort.stream.$streamblkHndl.rx.$hltName "0"]
                            }
                        } else {
                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                            }
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "0"]
                        }
                    }
                }
            }
            if {$stcName != "_none_"} {
                if {$::sth::Traffic::isLatencyConfig == 1} {
                    if {[regexp Hist $stcName]} {
                        set binnumber [::sth::Traffic::processGetBinNumber $stcName]
                        if {$detail_streams} {
                            if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                                set stcValue $::sth::Traffic::arraySTCArray($stcName);
                                if {($hltName == "rx_port") && ($detail_streams == 1)} {
                                    set temp [regsub -all {\}} $stcValue {}]
                                    set stcValue [split $temp {\s*(?=\{)}]
                                    set stcValue [regsub -all {\{\}} $stcValue {}]
                                }
                            } else {
                                set stcValue ""
                            }
                        } else {
                            if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                                set stcValue $::sth::Traffic::arraySTCArray($stcName);
                            } else {
                                set stcValue -1
                            }
                        }
                        #for detailed streams
                        for {set i 0} {$i < [llength $stcValue]} {incr i} {
                            if {[regexp total_pkts $hltName]} {
                                set hltName "total_pkts"
                            } elseif {[regexp pkt_frame_rate $hltName]} {
                                set hltName "pkt_frame_rate"
                            }
                            if {$enableRxPortFilter} {
                                if {$detail_streams} {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$i.latency_bin.$binnumber.$hltName [lindex $stcValue $i]]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$i.latency_bin.$binnumber.$hltName [lindex $stcValue $i]]
                                } else {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                }
                            } else {
                                if {[info exists rxPort] && $rxPort != ""} {
                                    if {[llength $rxPort] == 1} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                    } else {
                                        set num 0
                                        foreach eachRxPort $rxPort {
                                            if {$eachRxPort == $currPort} {
                                                continue
                                            }
                                            if {[info exist ::sth::Traffic::arraySTCArray_per_port($stcName)]} {
                                                set stcValue [lindex $::sth::Traffic::arraySTCArray_per_port($stcName) $num];
                                            } else {
                                                set stcValue -1
                                            }
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                            }
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $eachRxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                            incr num
                                        }
                                    }
                                } else {
                                    if {$detail_streams} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$i.latency_bin.$binnumber.$hltName [lindex $stcValue $i]]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.latency_bin.$binnumber.$hltName [lindex $stcValue $i]]
                                    } else {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                    }
                                }
                            }
                        }
                    } else {
                        if {$detail_streams} {
                            if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                                set stcValue $::sth::Traffic::arraySTCArray($stcName);
                                if {($hltName == "rx_port") && ($detail_streams == 1)} {
                                    set temp [regsub -all {\}} $stcValue {}]
                                    set stcValue [split $temp {\s*(?=\{)}]
                                    set stcValue [regsub -all {\{\}} $stcValue {}]
                                }
                            } else {
                                set stcValue ""
                            }
                        } else {
                            if {$stcName == "hlt"} {
                                set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                            } else {
                                if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                                    set stcValue $::sth::Traffic::arraySTCArray($stcName);
                                } else {
                                    set stcValue -1
                                }
                                if {[regexp #QNANO $stcValue]} {
                                    set stcValue -1
                                }
                            }
                        }
                        for {set i 0} {$i < [llength $stcValue]} {incr i} {
                            if {$enableRxPortFilter} {
                                if {$detail_streams} {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                } else {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                }
                            } else {
                                if {[info exists rxPort] && $rxPort != ""} {
                                    if {[llength $rxPort] == 1} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                    } else {
                                        set num 0
                                        foreach eachRxPort $rxPort {
                                            if {$eachRxPort == $currPort} {
                                                continue
                                            }
                                            if {[info exist ::sth::Traffic::arraySTCArray_per_port($stcName)]} {
                                                set stcValue [lindex $::sth::Traffic::arraySTCArray_per_port($stcName) $num];
                                            } else {
                                                set stcValue -1
                                            }
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                            }
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $eachRxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                            incr num
                                        }
                                    }
                                } else {
                                    if {$detail_streams} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                    } else {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                    }
                                }
                            }
                        }
                    }
                } else {
                    if {![regexp Hist $stcName]} {
                        if {$detail_streams} {
                            if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                                set stcValue $::sth::Traffic::arraySTCArray($stcName);
                                if {($hltName == "rx_port") && ($detail_streams == 1)} {
                                    set temp [regsub -all {\}} $stcValue {}]
                                    set stcValue [split $temp {\s*(?=\{)}]
                                    set stcValue [regsub -all {\{\}} $stcValue {}]
                                }
                            } else {
                                set stcValue ""
                            }
                        } else {
                            if {$stcName == "hlt"} {
                                set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                            } else {
                                if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                                    set stcValue $::sth::Traffic::arraySTCArray($stcName);
                                } else {
                                    set stcValue -1
                                }
                                if {[regexp #QNANO $stcValue]} {
                                    set stcValue -1
                                }
                            }
                        }
                        
                        for {set i 0} {$i < [llength $stcValue]} {incr i} {
                            if {$enableRxPortFilter} {
                                if {$detail_streams} {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                    } 
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                } else {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                    } 
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                }
                            } else {
                                if {[info exists rxPort] && $rxPort != ""} {
                                    if {[llength $rxPort] == 1} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                        } 
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                    } else {
                                        set num 0
                                        foreach eachRxPort $rxPort {
                                            if {$eachRxPort == $currPort} {
                                                continue
                                            }
                                            if {[info exist ::sth::Traffic::arraySTCArray_per_port($stcName)]} {
                                                set stcValue [lindex $::sth::Traffic::arraySTCArray_per_port($stcName) $num];
                                            } else {
                                                set stcValue -1
                                            }
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                            } 
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $eachRxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                            incr num
                                        }
                                    }
                                } else {
                                    if {$detail_streams} {
                                        # set values
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                        } 
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$i.$hltName [lindex $stcValue $i]]
                                    } else {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                        } 
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else {
            #TX
            if {!$detail_streams} {
                if {$hltName == "total_pkt_rate" || $hltName == "total_pkt_bit_rate" || $hltName == "rx_sig_rate"} {
                    if { $::sth::Traffic::dict_skip_port == 1 } {
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.tx.$hltName "0"]
                    }
                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName "0"]
                }
            }
            set stcName $::sth::Traffic::traffic_stats_streameot_tx_results_stcattr($hltName)
            if {$stcName != "_none_"} {
                if {$detail_streams} {
                    if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                        set stcValue $::sth::Traffic::arraySTCArray($stcName);
                        if {($hltName == "rx_port") && ($detail_streams == 1)} {
                            set temp [regsub -all {\}} $stcValue {}]
                            set stcValue [split $temp {\s*(?=\{)}]
                            set stcValue [regsub -all {\{\}} $stcValue {}]
                        }
                    } else {
                        set stcValue ""
                    }
                } else {
                    if {$stcName == "hlt"} {
                         set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                    } else {
                        if {[info exist ::sth::Traffic::arraySTCArray($stcName)]} {
                            set stcValue $::sth::Traffic::arraySTCArray($stcName);
                        } else {
                            set stcValue -1
                        }
                        if {[regexp #QNANO $stcValue]} {
                            set stcValue -1
                        }
                    }
                
                    ## process elapsed_time (added by xiaozhi)
                    if {$hltName == "elapsed_time"} {
                        if {$::sth::Traffic::processElapsedTime == 0} { continue }
                        if {[info exist ::sth::Traffic::arraySTCArray(FrameCount)]} {
                            set stcValue [::sth::Traffic::processTrafficTxElapsedTime $streamblkHndl $::sth::Traffic::arraySTCArray(FrameCount) ""]
                        } else {
                            set stcValue 0
                        }
                        
                    }
                    ## end
                }
                for {set i 0} {$i < [llength $stcValue]} {incr i} {
                    if {$detail_streams} {
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.tx.$i.$hltName [lindex $stcValue $i]]
                        }
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$i.$hltName [lindex $stcValue $i]]
                    } else {
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.tx.$hltName "$stcValue"]
                        }
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName "$stcValue"]
                    }
                }
            }
        }
    }
    
    #get the percentage of line rate of generator
    if {[info exists rxPort] && $rxPort != "" && $properties == ""} {
        set generatorHdl [::sth::sthCore::invoke stc::get $currPort -children-generator]
        set generatorCfgHdl [::sth::sthCore::invoke stc::get $generatorHdl -children-GeneratorConfig]
        set line_rate_percentage [::sth::sthCore::invoke stc::get $generatorCfgHdl -PercentageLoad]
        foreach eachRxPort $rxPort {
            if { $::sth::Traffic::dict_skip_port == 1 } {
                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.line_rate_percentage $line_rate_percentage]
            }
            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $eachRxPort.stream.$streamblkHndl.rx.line_rate_percentage $line_rate_percentage]
        }
    }
}

proc ::sth::Traffic::processCheckHeaderPresent {streamblkHndl hltName} {
    
    set stcValue 0;
    set layerType ""
    
    if { ![info exists ::sth::Traffic::arraystreamHnd($streamblkHndl)]} {
        if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl "-frameconfig"} frameStr]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting -frameconfig children $frameStr" {}
            #keylset trafficStatsKeyedList status $::sth::sthCore::FAILURE;
            return $::sth::sthCore::FAILURE;
        }
        #puts $frameStr
        if {$hltName == "ipv4_present"} {
            if { [regexp -all -nocase {ipv4:IPv4} $frameStr] > 0} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0
                } else {
                    set stcValue 1
                }
            } else {
                set stcValue 0
            }
        } elseif {$hltName == "ipv6_present"} {
            if { [regexp -all -nocase {ipv6:IPv6} $frameStr] > 0} {
                 if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0
                } else {
                    set stcValue 1
                }
            } else {
                set stcValue 0
            }
        } elseif {$hltName == "ipv4_outer_present"} {
            if { [regexp -all -nocase {ipv4:IPv4} $frameStr] == 2} {
                 if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0
                } else {
                    set stcValue 1
                }
            } else {
                set stcValue 0
            }
        } elseif {$hltName == "ipv6_outer_present"} {
            if { [regexp -all -nocase {ipv6:IPv6} $frameStr] == 2} {
                 if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0
                } else {
                    set stcValue 1
                }
            } else {
                set stcValue 0
            }
        } else {
            set stcValue 0;
        }
        return $stcValue
    }
    
    set headerSet [set ::sth::Traffic::arraystreamHnd($streamblkHndl)];
    array set arrayHeadersPresent $headerSet
    
    if {($hltName == "ipv4_present") || ($hltName == "ipv6_present")} {
        if {[info exists arrayHeadersPresent(l3_header)]} {
            set layerType $arrayHeadersPresent(l3_header)
        } 
    } elseif {($hltName == "tcp_present") || ($hltName == "udp_present")} {
        if {[info exists arrayHeadersPresent(l4_header)]} {
            set layerType $arrayHeadersPresent(l4_header)
        }  
    } elseif {($hltName == "ipv4_outer_present") || ($hltName == "ipv6_outer_present")} {
        if {[info exists arrayHeadersPresent(l3_header_outer)]} {
            set layerType $arrayHeadersPresent(l3_header_outer)
        } 
    }
    set stcValue 0
    if {[llength $layerType] != 0} {
        if {($hltName == "ipv4_present")} {
            if {[regexp ipv4 $layerType]} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0;
                } else {
                    set stcValue 1;
                }
            }
        }
        if {($hltName == "ipv6_present")} {
            if {[regexp ipv6 $layerType]} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0;
                } else {
                    set stcValue 1;
                }
            }
        }
        if {($hltName == "ipv4_outer_present")} {
            if {[regexp ipv4 $layerType]} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0;
                } else {
                    set stcValue 1;
                }
            }
        }
        if {($hltName == "ipv6_outer_present")} {
            if {[regexp ipv6 $layerType]} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0;
                } else {
                    set stcValue 1;
                }
            }
        }
        if {($hltName == "tcp_present")} {
            if {[regexp tcp $layerType]} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0;
                } else {
                    set stcValue 1;
                }
            }
        }
        if {($hltName == "udp_present")} {
            if {[regexp udp $layerType]} {
                if {$::sth::Traffic::isClear && $::sth::Traffic::isEOTResults} {
                    set stcValue 0;
                } else {
                    set stcValue 1;
                }
            }
        }
    }
    
    return $stcValue
}

proc ::sth::Traffic::processPagingForStreams {resultDataSet type properties detail_streams {isFilteredStreamResult 0}} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    variable detailedRxStats;
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set detailTrafficStatsKeyedList $trafficStatsKeyedList
    
    set TableName ::sth::Traffic::traffic_stats_stream\_$type\_results_stcattr
    if {$properties == ""} {
        set streamList [array names $TableName]
    } else {
        set streamList $properties
    }

    set totalPage [::sth::sthCore::invoke stc::get $resultDataSet -totalPageCount]
    set resultobjlist ""
    set streamblkHndl ""
    set currPort ""
    # FIXME: (MGJ) The rxPortList variable should be initialized early.
    set rxPortList ""
    #set streamIndex 0
    set lastStreamblkHndl ""
    array set streamParentHash {}
    array set analyzerParentHash {}
    set streamTrafficStatsKeyedList ""
    
    if {$isFilteredStreamResult} {
        set rxportName [sth::sthCore::invoke "stc::get $::sth::Traffic::filteredResultDataSetToPort($resultDataSet) -name"]
        # Remove rx_port here because FilteredStreamResults has no -RxPort. 
        regsub {rx_port} $streamList "" streamList
    }
    
    for { set pageNumber 1 } { $pageNumber <= $totalPage } { incr pageNumber } {
        #Mod by West, since pageNumber is 1 by default
        if {$pageNumber > 1} {
            ::sth::sthCore::invoke stc::config $resultDataSet -pageNumber $pageNumber
            ::sth::sthCore::invoke stc::apply
            ::sth::sthCore::invoke stc::perform RefreshResultView -ResultDataSet $resultDataSet -ExecuteSynchronous TRUE
            ::sth::sthCore::invoke stc::sleep 2
        }
        set resultobjlist [::sth::sthCore::invoke stc::get $resultDataSet -resultChild-targets]
        
        foreach streamResult $resultobjlist {
            set stcReturnList [::sth::sthCore::invoke stc::get $streamResult]
            array set stcArray $stcReturnList
            set streamblkHndl $stcArray(-parent)
            
            if {$isFilteredStreamResult} {
                # 32-bit filter for stream ID, which is enabled by default.
                set streamID $stcArray(-Comp32)
                if {[info exists ::sth::Traffic::streamToStreamBlock($streamID)]} {
                    set streamblkHndl $::sth::Traffic::streamToStreamBlock($streamID)
                } else {
                    # this stream is not belonging to processing streamblocks 
                    continue
                }
                
                if {[info exists ::sth::Traffic::streamIdToIndex($streamID)]} {
                    # This stream has been processed and thus its ID has gotten $streamIndex in output.
                    set streamIndexInList $::sth::Traffic::streamIdToIndex($streamID)
                } else {
                    set streamIndexInList ""
                }
                # Filter values of a stream are the same across ports, 
                # one checking of a port is enough.
                if { ![info exists ::sth::Traffic::filterValuesForStreams($streamID)] } {
                    set ::sth::Traffic::filterValuesForStreams($streamID) ""
                    foreach filter $::sth::Traffic::FilterType {
                        set filteredValue_N $::sth::Traffic::filter_value_column($filter)
                        set filterValue $stcArray(-$filteredValue_N)
                        if {$filter == "tos"} {
                            set bin $filterValue
                            #translate the tos bin to decimal value     
                            set tosbin [string range $bin 3 6]
                            set precbin [string range $bin 0 2]
                            set tosValue [::sth::sthCore::binToInt $tosbin]
                            set precValue [::sth::sthCore::binToInt $precbin]
                            append ::sth::Traffic::filterValuesForStreams($streamID) " tos \{$tosValue\} prec \{$precValue\}"
                        } elseif {$filter == "vlan_pri" || $filter == "vlan_pri_inner" || $filter == "dscp"} {
                            if {$filter != "dscp"} {
                                set filterValue [::sth::sthCore::binToInt $filterValue]
                            }
                            if { [regexp -all {vlan_pri|dscp} $::sth::Traffic::FilterType] == 1 } {
                                # For backward compatiblity, output 'qos' if only one of "vlan_pri", "vlan_pri_inner" and "dscp" is specified.
                                append ::sth::Traffic::filterValuesForStreams($streamID) " qos \{$filterValue\}"
                            } else {
                                append ::sth::Traffic::filterValuesForStreams($streamID) " $filter \{$filterValue\}"
                            }
                        } else {
                            # For backward compatiblity, when outputting, "vlan_id", "vlan_id_inner" -> "vlan", "vlan_inner"
                            regsub vlan_id $filter vlan filter
                            append ::sth::Traffic::filterValuesForStreams($streamID) " $filter \{$filterValue\}"
                        }
                    }
                }
            } 
            
            if { $streamblkHndl != $lastStreamblkHndl } {
                set streamIndex 0
                set lastStreamblkHndl $streamblkHndl
            }
            #puts "Parent of result object: $mystrmblkhndl"
            if {[info exists streamParentHash($streamblkHndl)]} {
                set currPort $streamParentHash($streamblkHndl)
            } else {
                set currPort [::sth::sthCore::invoke stc::get $streamblkHndl -parent]
                set streamParentHash($streamblkHndl) $currPort
            }
            #puts "Result for: $currPort $streamblkHndl\n"
            
            #get rx port handle to add return info
            if {$type == "rx"} {
                set rxPortList ""
                if {$detailedRxStats == 1} {
                    array unset stcArray_per_port
                    array set stcArray_per_port {}
                    if { [info exists stcArray(-summaryresultchild-Targets)] } {
                        foreach rxStreamResult $stcArray(-summaryresultchild-Targets) {                            
                            #to get each stream's rx attribute per port, need to get "rxstreamresult" object instead of "rxstreamsummaryresult" object
                            set attrCurrStream [sth::sthCore::invoke stc::get $rxStreamResult]
                            array set attrCurrStreamArray $attrCurrStream
                            set analyzer $attrCurrStreamArray(-parent)
                            if {[info exists analyzerParentHash($analyzer)]} {
                                set rxPort $analyzerParentHash($analyzer)
                            } else {
                                set rxPort [sth::sthCore::invoke stc::get $analyzer -parent]
                                set analyzerParentHash($analyzer) $rxPort
                            }
                            lappend rxPortList $rxPort
                                
                            set keys [array names stcArray_per_port]
                            if {$keys == ""} {
                                array set stcArray_per_port $attrCurrStream
                            } else {
                                foreach key $keys {
                                    set attrLastStream $stcArray_per_port($key)
                                    set stcArray_per_port($key) "$attrLastStream $attrCurrStreamArray($key)"
                                }
                            }
                        }
                    }
                }
            }
            foreach hltName $streamList {
                if {$type == "rx"} {
                    set stcName $::sth::Traffic::traffic_stats_stream_rx_results_stcattr($hltName)
                } else {
                    set stcName $::sth::Traffic::traffic_stats_stream_tx_results_stcattr($hltName)
                }
                #set stcName $TableName($hltName)
                #puts "--> $stcName"
                
                
                if {$type == "tx"} {
                    if {$stcName != "_none_"} {
                        if {$stcName == "hlt"} {
                            set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                        } else {
                            set stcName -$stcName
                            set stcValue $stcArray($stcName);
                            if {[regexp #QNANO $stcValue]} {
                                set stcValue -1
                            }
                        }
                        
                        if {!$detail_streams} {
                            if {[regexp -nocase {count|rate} $stcName] } {
                                if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName]}]} {
                                    set value 0
                                }
                                set stcValue [expr $value + $stcValue]
                            }
                        }
                        
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            keylset trafficStatsKeyedList $streamblkHndl.tx.$hltName "$stcValue"
                        }
                        
                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName "$stcValue"
                        #set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName "$stcValue"]
                    }
                } else {
                    ####For RX
                    if {$stcName != "_none_"} {
                        if {$::sth::Traffic::isLatencyConfig == 1} {
                            if {[regexp Hist $stcName]} {
                                set binnumber [::sth::Traffic::processGetBinNumber $stcName]
                                set stcName -$stcName
                                set stcValue $stcArray($stcName);
                                if {[regexp #QNANO $stcValue]} {
                                    set stcValue -1
                                }
                                #<port handle>.stream.<id>.rx.latency_bin.<bin number>.pkt_bit_rate
                                if {[regexp total_pkts $hltName]} {
                                    set hltName "total_pkts"
                                } elseif {[regexp pkt_frame_rate $hltName]} {
                                    set hltName "pkt_frame_rate"
                                }
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                }
                                
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                
                                set i 0
                                foreach rxPort $rxPortList {
                                    if {[info exists stcArray_per_port($stcName)]} {
                                        set stcValue [lindex $stcArray_per_port($stcName) $i]
                                    }
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"]
                                    incr i
                                }
                            } else {
                                if {$stcName == "hlt"} {
                                    set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                } else {
                                    set stcName -$stcName
                                    set stcValue $stcArray($stcName);
                                    if {[regexp #QNANO $stcValue]} {
                                        set stcValue -1
                                    }
                                }
                                
                                set i 0
                                foreach rxPort $rxPortList {
                                    if {[info exists stcArray_per_port($stcName)]} {
                                        set stcValue [lindex $stcArray_per_port($stcName) $i]
                                    }
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                                    incr i
                                }
                            }
                        } else {
                            if {![regexp Hist $stcName]} {
                                if {$stcName == "hlt"} {
                                    set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                } else {
                                    set stcName -$stcName
                                    set stcValue $stcArray($stcName);
                                    if {[regexp #QNANO $stcValue]} {
                                        set stcValue -1
                                    }
                                }
                                if {!$detail_streams} {
                                    if {[regexp -nocase {count|rate} $stcName] } {
                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                            set value 0
                                        }
                                        set stcValue [expr $value + $stcValue]
                                    }
                                } elseif {$isFilteredStreamResult && ($detail_streams || $::sth::Traffic::statsMode) && $streamIndexInList != ""} {
                                    if {[regexp -nocase {count|rate} $stcName] } {
                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamIndexInList.$hltName]}]} {
                                            set value 0
                                        }
                                        set stcValue [expr $value + $stcValue]
                                    } elseif {[regexp -nocase {min|first} $stcName]} {
                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamIndexInList.$hltName]}]} {
                                            
                                        } elseif {$stcValue > $value} {
                                            set stcValue $value
                                        }
                                    } elseif {[regexp -nocase {max|last} $stcName]} {
                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamIndexInList.$hltName]}]} {
                                            
                                        } elseif {$stcValue < $value} {
                                            set stcValue $value
                                        }
                                    } elseif {[regexp -nocase {Avg} $stcName]} {
                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamIndexInList.$hltName]}]} {
                                            
                                        } else {
                                            set stcValue "$value $stcValue"
                                        }
                                        # Average values need to be re-calculated
                                        if {[lsearch $::sth::Traffic::reCalcuList $hltName] == -1} {
                                            lappend ::sth::Traffic::reCalcuList $hltName
                                        }
                                    }
                                }
                                if {!$isFilteredStreamResult && [regexp -nocase {rxport} $stcName]} {
                                    if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                       set value ""
                                    }
                                    if {$value != "" && $value != $stcValue} {
                                        set stcValue "$value $stcValue"
                                    }
                                }
                                # set values
                                if {$isFilteredStreamResult && ($detail_streams || $::sth::Traffic::statsMode)} {
                                    if {$detailedRxStats == 0} {
                                        keylset streamTrafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamID.$hltName "$stcValue"
                                    }
                                } else {
                                    if {$detailedRxStats == 0} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                        }
                                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                    }
                                }
                                set i 0
                                foreach rxPort $rxPortList {
                                    if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0)} {
                                        if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                            set value 0
                                        }
                                        set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                    } elseif {[regexp -nocase {rxport} $stcName]} {
                                        set stcValue $stcArray($stcName)
                                    } elseif {[info exists stcArray_per_port($stcName)]} {
                                        set stcValue [lindex $stcArray_per_port($stcName) $i]
                                    }
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                    } 
                                    keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                    incr i
                                }
                                
                               # set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"]
                            } 
                        }
                    }
                }
            }
            ## process elapsed_time (added by xiaozhi)
            if {$::sth::Traffic::processElapsedTime && $type == "tx" && $properties == ""} {
                set hltName "elapsed_time"
                set frameCount [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts]
                set frameRate [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkt_rate]
                set stcValue [::sth::Traffic::processTrafficTxElapsedTime $streamblkHndl $frameCount $frameRate]
                
                if { $::sth::Traffic::dict_skip_port == 1 } {
                    keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                } 
                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName $stcValue
            }
            ## end
            if {$detail_streams || $::sth::Traffic::statsMode} {
                if {$isFilteredStreamResult} {
                    # For FilteredStreamResults in detailed_streams, need to know $streamID -> $streamIndex mapping.
                    # Because the output is based upon $streamIndex, which is starting from 0, not 
                    # $streamID, which is real stream ID (for example, starting from 65536).
                    if {![info exists ::sth::Traffic::streamIdToIndex($streamID)]} {
                        set ::sth::Traffic::streamIdToIndex($streamID) $streamIndex
                        set streamIndexInUse $streamIndex
                    } else {
                        set streamIndexInUse $::sth::Traffic::streamIdToIndex($streamID)
                    }
                    # Construct rx_port 
                    if {($properties == "") || ([lsearch $properties rx_port] != -1)} {
                        if {[catch {set rx_ports [keylget detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamIndexInUse.rx_port]}]} {
                           set rx_ports ""
                        }
                        if {$rx_ports == ""} {
                            set rx_ports $rxportName
                        } elseif {![regexp $rxportName $rx_ports]} {
                            append rx_ports ", $rxportName"
                        }
                    }
                    
                    if {[catch {set temp [keylget streamTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamID]}]} {
                    } else {
                        #set temp [keylget streamTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamID]
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            keylset detailTrafficStatsKeyedList $streamblkHndl.$type.$streamIndexInUse $temp
                        } 
                        keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamIndexInUse $temp
                    }
                    # Add rx_port 
                    if {($properties == "") || ([lsearch $properties rx_port] != -1)} {
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            keylset detailTrafficStatsKeyedList $streamblkHndl.$type.$streamIndexInUse.rx_port $rx_ports
                        } 
                        keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamIndexInUse.rx_port $rx_ports
                    }
                    
                    # Add filter values
                    array set filterArray $::sth::Traffic::filterValuesForStreams($streamID)
                    foreach filter [array names filterArray] {
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            keylset detailTrafficStatsKeyedList $streamblkHndl.$type.$streamIndexInUse.$filter $filterArray($filter)
                        } 
                        keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamIndexInUse.$filter $filterArray($filter)
                    }
                } else {
                    set temp [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.$type]
                    if { $::sth::Traffic::dict_skip_port == 1 } {
                        keylset detailTrafficStatsKeyedList $streamblkHndl.$type.$streamIndex $temp
                    } 
                    keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.$type.$streamIndex $temp
                }
            }
            
            incr streamIndex
        }
    }
    
    if {$detail_streams == 1} {
        set trafficStatsKeyedList $detailTrafficStatsKeyedList
    }
                                
    return $::sth::sthCore::SUCCESS; 
}



#<port handle>.stream.<id>.<rx|tx>.total_pkts
#<port handle>.stream.<id>.<rx|tx>.total_pkt_bytes
proc ::sth::Traffic::processTrafficStatsGetTxStreamCounters {handlevalues isStreamBlk properties detail_streams} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set detailTrafficStatsKeyedList $trafficStatsKeyedList
    
    if {$properties == "_none_"} {
        return;
    }
    
    #check it is eot or not
    if {($sth::Traffic::isEOTResults ==1) &&
        ($detail_streams == 0)} {
        set resulttype TxStreamBlockResults
    } else {
        set resulttype txstreamresults
    }
    
    if {$isStreamBlk} {
        set paging 0        
        set totalPage [::sth::sthCore::invoke stc::get $::sth::Traffic::txStreamDataset -totalPageCount]
        if {$totalPage > 1} {
            set paging 1
        }
        if {$paging ==0} {
            foreach streamblkHndl $handlevalues {
                set currPort [::sth::sthCore::invoke stc::get $streamblkHndl -parent]
                set TableName ::sth::Traffic::traffic_stats_stream_tx_results_stcattr
                if {$properties == ""} {
                    set txstreamList [array names $TableName]
                } else {
                    set txstreamList $properties
                }
                if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl -children-$resulttype} txStreamData]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting txStreamresults children $txStreamData" {}
                    return $::sth::sthCore::FAILURE;
                }
                
                if {[string equal $txStreamData ""]} {
                                foreach hltName $txstreamList {
                                    set stcName $::sth::Traffic::traffic_stats_stream_tx_results_stcattr($hltName)
                                    if {$stcName != "_none_"} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.tx.$hltName "0"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName "0"]
                                    }
                                }
                } else {
                    set num [llength $txStreamData]
                    set streamIndex 0
                    foreach result $txStreamData {
                        set stcReturnList [::sth::sthCore::invoke stc::get $result];
                   
                        array set stcArray $stcReturnList;
                        
                        foreach hltName $txstreamList {
                            set stcName $::sth::Traffic::traffic_stats_stream_tx_results_stcattr($hltName)
                            if {$stcName != "_none_"} {
                               if {$stcName == "hlt"} {
                                   set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]                         
                                } else {
                                    set stcName -$stcName
                                    set stcValue $stcArray($stcName);
                                    if {[regexp #QNANO $stcValue]} {
                                        set stcValue -1
                                    }
                                }
                                if {!$detail_streams} {
                                    if {[regexp -nocase {count|rate} $stcName] } {
                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName]} ]} {
                                            set value 0
                                        }
                                        set stcValue [expr $value + $stcValue] 
                                       
                                    }
                                }
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                    keylset trafficStatsKeyedList $streamblkHndl.tx.$hltName $stcValue
                                }
                                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName $stcValue
                            }
                        }
                        if {$detail_streams == 1} {
                            set temp [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx]
                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                keylset detailTrafficStatsKeyedList $streamblkHndl.tx.$streamIndex $temp
                            }             
                            keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$streamIndex $temp
                        }
                        incr streamIndex
                    }
                    ## process elapsed_time (added by xiaozhi)
                    if {$::sth::Traffic::processElapsedTime && $properties == ""} {
                        set hltName "elapsed_time"
                        set frameCount [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts]
                        set frameRate [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkt_rate]
                        set stcValue [::sth::Traffic::processTrafficTxElapsedTime $streamblkHndl $frameCount $frameRate]
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            keylset trafficStatsKeyedList $streamblkHndl.tx.$hltName $stcValue
                        } 
                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName $stcValue
                    }
                    ## end
                }  
            }
        } else {
            set returnVal [::sth::Traffic::processPagingForStreams $::sth::Traffic::txStreamDataset tx $properties $detail_streams]
        }
        
    } else {
        if {$::sth::Traffic::statsMode == 1} {
            set returnVal [::sth::Traffic::processPagingForStreams $::sth::Traffic::txStreamDataset tx $properties $detail_streams]
        } else {
            set lengthstreamblkHndlList ""
            set paging 0
            foreach currPort $handlevalues {
                if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-streamblock"} streamblkHndlList]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting streamBlock children $streamblkHndlList" {}
                    return $::sth::sthCore::FAILURE;
                }
                set lengthstreamblkHndlList [llength $streamblkHndlList]
                if {$lengthstreamblkHndlList > 100} {
                    set paging 1
                } else {
                    set totalPage [::sth::sthCore::invoke stc::get $::sth::Traffic::txStreamDataset -totalPageCount]
                    if {$totalPage > 1} {
                        set paging 1
                    }
                }
                set TableName ::sth::Traffic::traffic_stats_stream_tx_results_stcattr
                if {$properties == ""} {
                    set txstreamList [array names $TableName]
                } else {
                    set txstreamList $properties
                }
                if {$paging == 0} {
                    foreach streamblkHndl $streamblkHndlList {
                        if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl -children-$resulttype} txStreamResult]} {
                            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting txstreamresults children $txStreamResult" {}
                            return $::sth::sthCore::FAILURE;
                        }
                        if {[string equal $txStreamResult ""]} {
                            foreach hltName $txstreamList {
                                set stcName $::sth::Traffic::traffic_stats_stream_tx_results_stcattr($hltName)
                                if {$stcName != "_none_"} {
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.tx.$hltName "0"]
                                    }
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName "0"]
                                }
                            }
                        } else {
                            set num [llength $txStreamResult]
                            set streamIndex 0
                            foreach result $txStreamResult {
                                set stcReturnList [::sth::sthCore::invoke stc::get $result];
                                array set stcArray $stcReturnList;
                                foreach hltName $txstreamList {
                                    set stcName $::sth::Traffic::traffic_stats_stream_tx_results_stcattr($hltName)
                                    #puts "--> $stcName"
                                    if {$stcName != "_none_"} {
                                        if {$stcName == "hlt"} {
                                            set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                        } else {
                                            set stcName -$stcName
                                            set stcValue $stcArray($stcName);
                                            if {[regexp #QNANO $stcValue]} {
                                                set stcValue -1
                                            }
                                        }
                                        if {!$detail_streams} {
                                            if {[regexp -nocase {count|rate} $stcName] } {
                                                if { [catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName]}] } {
                                                    set value 0
                                                }
                                                set stcValue [expr $value + $stcValue]
                                            }
                                        }
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            keylset trafficStatsKeyedList $streamblkHndl.tx.$hltName $stcValue
                                        }
                                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName $stcValue
                                    }
                                }
                                if {$detail_streams == 1} {
                                    set temp [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx]
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        keylset detailTrafficStatsKeyedList $streamblkHndl.tx.$streamIndex $temp
                                    }     
                                    keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$streamIndex $temp
                                }
                                incr streamIndex
                            }
                            ## process elapsed_time (added by xiaozhi)
                            if {$::sth::Traffic::processElapsedTime && $properties == ""} {
                                set hltName "elapsed_time"
                                set frameCount [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts]
                                set frameRate [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkt_rate]
                                set stcValue [::sth::Traffic::processTrafficTxElapsedTime $streamblkHndl $frameCount $frameRate]
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                    keylset trafficStatsKeyedList $streamblkHndl.tx.$hltName $stcValue
                                }
                                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.$hltName $stcValue
                            }
                            ## end
                        }
                    }
                } else {
                    set returnVal [::sth::Traffic::processPagingForStreams $::sth::Traffic::txStreamDataset tx $properties $detail_streams]
                }
            }
        }
    }

    if {($detail_streams == 1) && ($paging == 0)} {
        set trafficStatsKeyedList $detailTrafficStatsKeyedList
    }
}



proc ::sth::Traffic::processGetBinNumber {element} {
    
    set binnumber 0
    set myval [string range $element 7 7]
    
    if {$myval == 1} {
        set binNo [string range $element 7 8]
        if {($binNo == "1C") || ($binNo == "1R")} {
            set binNo 1;
        }
    } else {
        set binNo $myval;
    }

    return $binNo;
}

# Some values in the return list need to be re-calculated. For example, average values.
# Arguments:
#   reCalcuList     the fields to be re-calculated
#   streamblockHndlList     streamblock handles 
#   txPort          the tx port of $streamblockHndlList
# Example:
#   Return list is {port1 {{stream {{streamblock1 {{rx {{0 {{avg_delay {147.572303819 143.21770877}}}}}}}}}}}} 
#   set avg_delay to the arithmetic average of the values.
proc ::sth::Traffic::reCalcuValues {reCalcuList streamblockHndlList txPort} {

    ::sth::sthCore::log debug "{Calling ::sth::Traffic::reCalcuValues}"
    upvar trafficStatsKeyedList trafficStatsKeyedList
    
    foreach hltName $reCalcuList {
        foreach streamblkHndl $streamblockHndlList {
            if {[catch {set streamIndexList [keylkeys trafficStatsKeyedList $txPort.stream.$streamblkHndl.rx]}]} {
                
            } else {
                foreach streamIndex $streamIndexList {
                    set total 0
                    set avg_values [keylget trafficStatsKeyedList $txPort.stream.$streamblkHndl.rx.$streamIndex.$hltName]
                    if {[llength $avg_values] > 1} {
                        foreach avg_value $avg_values {
                            set total [expr $total + $avg_value]
                        }
                        
                        set new_avg_value [expr $total / [llength $avg_values]]
                        # round the value to three digits after decimal point
                        set new_avg_value [expr {double(round(1000*$new_avg_value))/1000}]
                        if {![catch {set temp [keylget trafficStatsKeyedList $streamblkHndl.rx.$streamIndex.$hltName]}]} {
                            keylset trafficStatsKeyedList $streamblkHndl.rx.$streamIndex.$hltName $new_avg_value
                        }
                        keylset trafficStatsKeyedList $txPort.stream.$streamblkHndl.rx.$streamIndex.$hltName $new_avg_value
                    }
                }
            }
        }
    }
}

#Arguments:
#   handlevalues    a list of streamblock handles, or a list of port handles.
#   isStreamBlk     1 indicates handlevalues is a list of streamblock handles; 0 indicates handlevalues is a list of port handles.
#   properties      1) "_none_", do nothing 2) specified properties 3) "" stands for all properties
#   detail_streams  1 means '-mode detailed_streams' is specified, 0 means other modes.
proc ::sth::Traffic::processTrafficStatsGetRxStreamFilteredCounters {handlevalues isStreamBlk properties detail_streams} {

    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTrafficStatsGetRxStreamFilteredCounters}"
    upvar trafficStatsKeyedList trafficStatsKeyedList
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    if {$properties == "_none_"} {
        return;
    }
    
    # stream ID -> belonging streamblock
    array unset ::sth::Traffic::streamToStreamBlock
    array set ::sth::Traffic::streamToStreamBlock {}
    # streamblock -> tx port
    array unset streamBlockToPort
    array set streamBlockToPort {}
    # stream ID -> "vlan_id 1000 tos 4 pri 0 ..."
    array unset ::sth::Traffic::filterValuesForStreams 
    array set ::sth::Traffic::filterValuesForStreams {}
    # filter name -> FilteredValue_* (attribute name in object)
    array unset ::sth::Traffic::filter_value_column
    array set ::sth::Traffic::filter_value_column {}
    # real stream ID -> output streamIndex (for example, 65536 -> 0)
    array unset ::sth::Traffic::streamIdToIndex
    array set ::sth::Traffic::streamIdToIndex {}
    # Some values need to be calculated after all stream values on different ports are collected.
    set ::sth::Traffic::reCalcuList ""
    set streamblockHndlList ""
    if {$isStreamBlk} {
        set streamblockHndlList $handlevalues
    } else {
        foreach port $handlevalues {
            set streamblocks [::sth::sthCore::invoke stc::get $port -children-streamblock]
            if {$streamblocks != ""} {
                append streamblockHndlList " $streamblocks"
            }
        }
    }
    # No streamblocks under ports
    if {$streamblockHndlList == ""} {
        return 
    }
    
        # Get all the stream IDs of a streamblock from TxStreamResults because there is no streamblock info
        # in FilteredStreamResults, just stream info. We need to know which streams belong to which streamblock,
        # so that we can group stream info for a streamblock. Also, TxStreamResults should be already 
        # subscribed in this case.
        set needTxStreamBlocks ""
        set forFilterTxResultDataSet ""
        set txStreamResultsForFiltered ""
        foreach streamblkHndl $streamblockHndlList {
            set streamBlockToPort($streamblkHndl) [::sth::sthCore::invoke stc::get $streamblkHndl "-parent"]
            set txStreamResults [::sth::sthCore::invoke stc::get $streamblkHndl -children-txstreamresults]
            if {$txStreamResults == ""} {
                lappend needTxStreamBlocks $streamblkHndl                
            } else {
                append txStreamResultsForFiltered " $txStreamResults"
            }
        }
        # Need to subscribe by myself if no TxStreamResults was subscribed for these streamblocks.
        if {$needTxStreamBlocks != ""} {
            set forFilterTxResultDataSet [::sth::Traffic::processTrafficStatsSubscribeCounters stream_tx StreamBlock TxStreamResults streamblocklevel $needTxStreamBlocks "total_pkt_bytes"]
            set totalPage [::sth::sthCore::invoke stc::get $forFilterTxResultDataSet -totalPageCount]
            for { set pageNumber 1 } { $pageNumber <= $totalPage } { incr pageNumber } {
                if {$pageNumber > 1} {
                    ::sth::sthCore::invoke stc::config $forFilterTxResultDataSet -pageNumber $pageNumber
                    ::sth::sthCore::invoke stc::apply
                    #::sth::sthCore::invoke stc::perform RefreshResultView -ResultDataSet $resultDataSet -ExecuteSynchronous TRUE
                    #::sth::sthCore::invoke stc::sleep 1
                }
                set resultobjlist [::sth::sthCore::invoke stc::get $forFilterTxResultDataSet -resultChild-targets]
                append txStreamResultsForFiltered " $resultobjlist"
            }
        }
        
        foreach streamResult $txStreamResultsForFiltered {
            set streamId [::sth::sthCore::invoke stc::get $streamResult -StreamId]
            set streamblkHndl [::sth::sthCore::invoke stc::get $streamResult -parent]
            set ::sth::Traffic::streamToStreamBlock($streamId) $streamblkHndl
        }
        # For FilteredStreamResults, ::sth::Traffic::rxStreamDataset is a list of resultdataset objects,
        # each resultdataset object is for a port. 
        foreach dataset $::sth::Traffic::rxStreamDataset {
            if {[array size ::sth::Traffic::filter_value_column] == 0} {
                # Only need to get one filteredstreamresults of one port to know filter -> FilteredValue_* mappings.
                # Because we set the same analyzer filters for all ports.
                set filteredResultList [sth::sthCore::invoke "stc::get $dataset -resultchild-Targets"]
                if {$filteredResultList != ""} {
                    set filteredResult [lindex $filteredResultList 0]
                    set stcReturnList [::sth::sthCore::invoke "stc::get $filteredResult"]
                    array set stcArray $stcReturnList
                    
                    foreach filter $::sth::Traffic::FilterType {
                        for {set i 1} {$i <= 10} {incr i}  {
                            # -FilteredValue_N is the value of -FilteredName_N, N is from 1 to 10 in STC.
                            # Find which -FilteredName_N is the requested filter name.
                            if {$stcArray(-FilteredName_$i) == $::sth::Traffic::filter_key_column($filter)} {
                                set ::sth::Traffic::filter_value_column($filter) FilteredValue_$i
                                break
                            }
                        }
                    }
                } 
            }
            
            if {[::sth::sthCore::invoke stc::get $dataset -totalPageCount]} {
                set returnVal [::sth::Traffic::processPagingForStreams $dataset rx $properties $detail_streams 1]
            }
        }
        
    # Re-calculate values
    if {$::sth::Traffic::reCalcuList != ""} {
        ::sth::Traffic::reCalcuValues $::sth::Traffic::reCalcuList $streamblockHndlList $streamBlockToPort($streamblkHndl)
    }
    # Unsubscribe TxStreamResults subscribed by this function.
    if {$forFilterTxResultDataSet != ""} {
        ::sth::Traffic::processUnSubscribeProjectLevelCounters $forFilterTxResultDataSet
    }
}

#<port handle>.stream.<id>.<rx|tx>.total_pkts
#<port handle>.stream.<id>.<rx|tx>.total_pkt_bytes
#Arguments:
#   handlevalues    a list of streamblock handles, or a list of port handles (current use is only a port handle)
#   isStreamBlk     1 indicates handlevalues is a list of streamblock handles; 0 indicates handlevalues is a list of port handles
#   properties      1) "_none_", do nothing 2) specified properties 3) "" stands for all properties
#   detail_streams  1 means '-mode detailed_streams' is specified, 0 means other modes.
proc ::sth::Traffic::processTrafficStatsGetRxStreamCounters {handlevalues isStreamBlk properties detail_streams} {
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    variable detailedRxStats;
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set detailTrafficStatsKeyedList $trafficStatsKeyedList
    
    if {$properties == "_none_"} {
        return;
    }
    
    # FIXME: (MGJ) The rxPortList variable should be initialized early.
    set rxPortList ""
    #check it is eot or not
    if {($sth::Traffic::isEOTResults ==1) &&
        ($detail_streams == 0) } {
        if {$::sth::Traffic::FilterType != ""} {
            set resulttype RxStreamBlockResults
        } else {
            set resulttype rxstreamsummaryresults
        }
        set eot 1
    } else {
        #   If analyzer filters are used, no RxStreamSummaryResults can be obtained.  Only
        #   FilteredStreamResults will be obtained.
        if {($::sth::Traffic::FilterType != "") &&
            ($detail_streams == 0)} {
            set resulttype RxStreamBlockResults
        } else {
            set resulttype rxstreamsummaryresults
        }
        set eot 0
    }
    if {$isStreamBlk} {
        set paging 0
        set totalPage [::sth::sthCore::invoke stc::get $::sth::Traffic::rxStreamDataset -totalPageCount]
        if {$totalPage > 1} {
            set paging 1
        }
        if {$paging == 0} {
            foreach streamblkHndl $handlevalues {
                if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl "-parent"} currPort]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting parent of streamBlock: $currPort" {}
                    return $::sth::sthCore::FAILURE;
                }
                
                #add Rx port filter
                ::sth::Traffic::processRxPortResultFilter $streamblkHndl $eot enableRxPortFilter rxPortHdl
                
                set TableName ::sth::Traffic::traffic_stats_stream_rx_results_stcattr
                if {$properties == ""} {
                    set rxstreamList [array names $TableName]
                } else {
                    set rxstreamList $properties
                }
                if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl -children-$resulttype} rxStreamData]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting children of rxstreamresults: $rxStreamData" {}
                    return $::sth::sthCore::FAILURE;
                }
                
                if {[string equal $rxStreamData ""]} {
                    foreach hltName $rxstreamList {
                        set stcName $::sth::Traffic::traffic_stats_stream_rx_results_stcattr($hltName)
                        if {$stcName != "_none_"} {
                            if {$enableRxPortFilter} {
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                                }
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "0"]
                            } else {
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                                }
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "0"]
                            }
                        }
                    }
                } else {
                    set num [llength $rxStreamData]
                    set streamIndex 0
                    foreach result $rxStreamData {
                        set stcReturnList [::sth::sthCore::invoke stc::get $result];
                        array set stcArray $stcReturnList;
                        set frameRateValue $stcArray(-FrameRate)
                        if {$frameRateValue == 0} {
                            if {[info exists stcArray(-resultchild-Targets)]} {
                                set rxStreamHndList $stcArray(-resultchild-Targets)
                                foreach rxStreamHnd $rxStreamHndList {
                                    set frameRateValue [::sth::sthCore::invoke stc::get $rxStreamHnd -FrameRate]
                                    if {$frameRateValue != 0} {
                                        set stcArray(-FrameRate) $frameRateValue
                                        break
                                    }
                                }
                            }
                        }
                        set rxPortList ""
                        if {$detailedRxStats == 1} {
                            array unset stcArray_per_port
                            array set stcArray_per_port {}
                            if { [info exists stcArray(-summaryresultchild-Targets)] } {
                                foreach rxStreamResult $stcArray(-summaryresultchild-Targets) {
                                    set analyzer [sth::sthCore::invoke stc::get $rxStreamResult -parent]
                                    set rxPort   [sth::sthCore::invoke stc::get $analyzer       -parent]
                                    lappend rxPortList $rxPort
                                    
                                    #to get each stream's rx attribute per port, need to get "rxstreamresult" object instead of "rxstreamsummaryresult" object
                                    set attrCurrStream [sth::sthCore::invoke stc::get $rxStreamResult]
                                    array set attrCurrStreamArray $attrCurrStream
                    
                                    set keys [array names stcArray_per_port]
                                    if {$keys == ""} {
                                        array set stcArray_per_port $attrCurrStream
                                    } else {
                                        foreach key $keys {
                                            set attrLastStream $stcArray_per_port($key)
                                            set stcArray_per_port($key) "$attrLastStream $attrCurrStreamArray($key)"
                                        }
                                    }
                                }
                            }
                        }
                        foreach hltName $rxstreamList {
                            set stcName $::sth::Traffic::traffic_stats_stream_rx_results_stcattr($hltName)
                            if {$stcName != "_none_"} {
                                if {$::sth::Traffic::isLatencyConfig == 1} {
                                    if {[regexp Hist $stcName]} {
                                        set binnumber [::sth::Traffic::processGetBinNumber $stcName]
                                        set stcName -$stcName
                                        set stcValue $stcArray($stcName);
                                        if {[regexp #QNANO $stcValue]} {
                                            set stcValue -1
                                        }
                                        #<port handle>.stream.<id>.rx.latency_bin.<bin number>.pkt_bit_rate
                                        if {[regexp total_pkts $hltName]} {
                                            set hltName "total_pkts"
                                        } elseif {[regexp pkt_frame_rate $hltName]} {
                                            set hltName "pkt_frame_rate"
                                        }
                                        if {!$detail_streams} {
                                            if {[regexp -nocase {count|rate} $stcName] } {
                                                if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName]}]} {
                                                    set value 0
                                                }
                                                    set stcValue [expr $value + $stcValue]
                                            }
                                        }

                                        if {$enableRxPortFilter} {
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                                keylset trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName $stcValue
                                            }
                                            keylset trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName $stcValue
                                        } else {
                                            if {$detailedRxStats == 0} {
                                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                                    keylset trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName $stcValue
                                                }
                                                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName $stcValue
                                            }
                                            set i 0
                                            if {[info exists rxPortList]} {
                                                foreach rxPort $rxPortList {
                                                    if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0)} {
                                                        if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName]}]} {
                                                            set value 0
                                                        }
                                                        set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                                    } elseif {[info exists stcArray_per_port($stcName)]} {
                                                        set stcValue [lindex $stcArray_per_port($stcName) $i]
                                                    }
                                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                                        keylset trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName $stcValue
                                                    }
                                                    keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName $stcValue
                                                    incr i
                                                }
                                            }
                                        }
                                        
                                    } else {
                                        if {$stcName == "hlt"} {
                                            set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                        } else {
                                            set stcName -$stcName
                                            set stcValue $stcArray($stcName);
                                            if {[regexp #QNANO $stcValue]} {
                                                set stcValue -1
                                            }
                                        }
                                        if {!$detail_streams} {
                                            if {[regexp -nocase {count|rate} $stcName] } {
                                                if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                   set value 0
                                                }
                                                    set stcValue [expr $value + $stcValue]
                                            }
                                        }
                                        if {[regexp -nocase {rxport} $stcName]} {
                                            if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                               set value ""
                                            }
                                            if {$value != "" && $value != $stcValue} {
                                                set stcValue "$value $stcValue"
                                            }
                                        }
                                        if {$enableRxPortFilter} {
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                                keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                            }
                                            keylset trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                        } else {
                                            if {$detailedRxStats == 0} {
                                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                                    keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                }
                                                keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                            }
                                            set i 0
                                            if {[info exists rxPortList]} {
                                            foreach rxPort $rxPortList {
                                                if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0) } {
                                                    if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                       set value 0
                                                    }
                                                    set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                                } elseif {[regexp -nocase {rxport} $stcName] } {
                                                    set stcValue $stcArray($stcName)
                                                } elseif {[info exists stcArray_per_port($stcName)]} {
                                                    set stcValue [lindex $stcArray_per_port($stcName) $i]
                                                }
                                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                                    keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                }
                                                keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                incr i
                                            }
                                            }
                                        }
                                    }
                                } else {
                                    if {![regexp Hist $stcName]} {
                                        if {$stcName == "hlt"} {
                                            set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                        } else {
                                            set stcName -$stcName
                                            set stcValue $stcArray($stcName);
                                            if {[regexp #QNANO $stcValue]} {
                                                set stcValue -1
                                            }
                                        }
                                        if {!$detail_streams} {
                                            if {[regexp -nocase {count|rate} $stcName] } {
                                                if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                    set value 0
                                                }
                                                    set stcValue [expr $value + $stcValue]
                                            }
                                        }
                                        if {[regexp -nocase {rxport} $stcName]} {
                                            if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                               set value ""
                                            }
                                            if {$value != "" && $value != $stcValue} {
                                                set stcValue "$value $stcValue"
                                            }
                                        }
                                        if {$enableRxPortFilter} {
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                                keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                            }
                                            keylset trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                        } else {
                                            if {$detailedRxStats == 0} {
                                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                                    keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                }
                                                    keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                            }
                                            set i 0
                                            if {[info exists rxPortList]} {
                                            foreach rxPort $rxPortList {
                                                if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0)} {
                                                    if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                        set value 0
                                                    }
                                                    set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                                } elseif {[regexp -nocase {rxport} $stcName]} {
                                                    set stcValue $stcArray($stcName)
                                                } elseif {[info exists stcArray_per_port($stcName)]} {
                                                    set stcValue [lindex $stcArray_per_port($stcName) $i]
                                                }
                                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                                    keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                }
                                                keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                incr i
                                            }
                                            }
                                        }
                                    } 
                                }
                            }
                        }
                        if {$detail_streams == 1} {
                            set temp [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx]
                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                keylset detailTrafficStatsKeyedList $streamblkHndl.rx.$streamIndex $temp
                            }
                            keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamIndex $temp
                            incr streamIndex
                        }
                    }
                }
                
                #get the percentage of line rate of generator
                if {[info exists rxPortList]} {
                    foreach rxPort $rxPortList {
                        set generatorHdl         [::sth::sthCore::invoke stc::get $currPort -children-generator]
                        set generatorCfgHdl      [::sth::sthCore::invoke stc::get $generatorHdl -children-GeneratorConfig]
                        set line_rate_percentage [::sth::sthCore::invoke stc::get $generatorCfgHdl -PercentageLoad]
                        if { $::sth::Traffic::dict_skip_port == 1 } {
                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.line_rate_percentage $line_rate_percentage]
                        }
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.line_rate_percentage $line_rate_percentage]  
                    }
                }
            }
        }  else {
            set returnVal [::sth::Traffic::processPagingForStreams $::sth::Traffic::rxStreamDataset rx $properties $detail_streams]
        }
    } else {
        if {$::sth::Traffic::statsMode == 1} {
                set returnVal [::sth::Traffic::processPagingForStreams $::sth::Traffic::rxStreamDataset rx $properties $detail_streams]
        } else {
        foreach currPort $handlevalues {
                set paging 0
                set lengthstreamblkHndlList ""
                if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-streamblock"} streamblkHndlList]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting streamblock children: $streamblkHndlList" {}
                    return $::sth::sthCore::FAILURE;
                }
                set lengthstreamblkHndlList [llength $streamblkHndlList]
                if {$lengthstreamblkHndlList > 100} {
                    set paging 1
                } else {
                    set totalPage [::sth::sthCore::invoke stc::get $::sth::Traffic::rxStreamDataset -totalPageCount]
                    if {$totalPage > 1} {
                        set paging 1
                    }
                }
                #add Rx port filter
                ::sth::Traffic::processRxPortResultFilter $streamblkHndlList $eot enableRxPortFilter rxPortHdl
                
                set TableName ::sth::Traffic::traffic_stats_stream_rx_results_stcattr
                if {$properties == ""} {
                    set rxstreamList [array names $TableName]
                } else {
                    set rxstreamList $properties
                }
                if {$paging == 0} {
                    foreach streamblkHndl $streamblkHndlList {

                            if {[catch {::sth::sthCore::invoke stc::get $streamblkHndl -children-$resulttype} rxStreamData]} {
                                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting children of rxstreamresults: $rxStreamData" {}
                                return $::sth::sthCore::FAILURE;
                            }
                        
                        if {[string equal $rxStreamData ""]} {
                            foreach hltName $rxstreamList {
                                set stcName $::sth::Traffic::traffic_stats_stream_rx_results_stcattr($hltName)
                                if {$stcName != "_none_"} {
                                    if {$enableRxPortFilter} {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "0"]
                                    } else {
                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                                        }
                                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "0"]
                                        if {[info exists rxPort] && $rxPort != ""} {
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.$hltName "0"]
                                            }
                                            set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "0"]
                                        }
                                    }
                                }
                            }
                        } else {
                            set num [llength $rxStreamData]
                            set streamIndex 0
                            foreach result $rxStreamData {
                                set stcReturnList [::sth::sthCore::invoke stc::get $result]
                                array set stcArray $stcReturnList;
                                set frameRateValue $stcArray(-FrameRate)
                                if {$frameRateValue == 0} {
                                    if {[info exists stcArray(-resultchild-Targets)]} {
                                        set rxStreamHndList $stcArray(-resultchild-Targets)
                                        foreach rxStreamHnd $rxStreamHndList {
                                            set frameRateValue [::sth::sthCore::invoke stc::get $rxStreamHnd -FrameRate]
                                            if {$frameRateValue != 0} {
                                                set stcArray(-FrameRate) $frameRateValue
                                                break
                                            }
                                        }
                                    }
                                }
                                set rxPortList ""
                                if {$detailedRxStats == 1} {
                                    array unset stcArray_per_port
                                    array set stcArray_per_port {}
                                    if { [info exists stcArray(-summaryresultchild-Targets)]} {
                                        foreach rxStreamResult $stcArray(-summaryresultchild-Targets) {
                                            set analyzer [sth::sthCore::invoke stc::get $rxStreamResult -parent]
                                            set rxPort   [sth::sthCore::invoke stc::get $analyzer       -parent]
                                            lappend rxPortList $rxPort
                                            
                                            #to get each stream's rx attribute per port, need to get "rxstreamresult" object instead of "rxstreamsummaryresult" object
                                            set attrCurrStream [sth::sthCore::invoke stc::get $rxStreamResult]
                                            array set attrCurrStreamArray $attrCurrStream
                                            set keys [array names stcArray_per_port]
                                            if {$keys == ""} {
                                                array set stcArray_per_port $attrCurrStream
                                            } else {
                                                foreach key $keys {
                                                    set attrLastStream $stcArray_per_port($key)
                                                    set stcArray_per_port($key) "$attrLastStream $attrCurrStreamArray($key)"
                                                }
                                            }
                                        }
                                    }
                                }
                                foreach hltName $rxstreamList {
                                    set stcName $::sth::Traffic::traffic_stats_stream_rx_results_stcattr($hltName)
                                    if {$stcName != "_none_"} {
                                        if {$::sth::Traffic::isLatencyConfig == 1} {
                                            if {[regexp Hist $stcName]} {
                                                set binnumber [::sth::Traffic::processGetBinNumber $stcName]
                                                set stcName -$stcName
                                                set stcValue $stcArray($stcName);
                                                if {[regexp #QNANO $stcValue]} {
                                                    set stcValue -1
                                                }
                                                #<port handle>.stream.<id>.rx.latency_bin.<bin number>.pkt_bit_rate
                                                if {[regexp total_pkts $hltName]} {
                                                    set hltName "total_pkts"
                                                } elseif {[regexp pkt_frame_rate $hltName]} {
                                                    set hltName "pkt_frame_rate"
                                                }
                                                if {!$detail_streams} {
                                                    if {[regexp -nocase {count|rate} $stcName] } {
                                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName]}]} {
                                                           set value 0
                                                        }
                                                        set stcValue [expr $value + $stcValue]
                                                    }
                                                }
                                                if {$enableRxPortFilter} {
                                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                                        keylset trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"
                                                    }
                                                    keylset trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"
                                                } else {
                                                    if {$detailedRxStats == 0} {
                                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                                            keylset trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"
                                                        }
                                                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"
                                                    }
                                                    set i 0
                                                    if {[info exists rxPortList]} {
                                                    foreach rxPort $rxPortList {
                                                        if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0)} {
                                                            if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName]}]} {
                                                               set value 0
                                                            }
                                                            set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                                        } elseif {[info exists stcArray_per_port($stcName)]} {
                                                            set stcValue [lindex $stcArray_per_port($stcName) $i]
                                                        }
                                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                                            keylset trafficStatsKeyedList $streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"
                                                        }
                                                        keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.latency_bin.$binnumber.$hltName "$stcValue"
                                                        incr i
                                                    }
                                                    }
                                                }                                               
                                            } else {
                                                if {$stcName == "hlt"} {
                                                    set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                                } else {
                                                    set stcName -$stcName
                                                    set stcValue $stcArray($stcName);
                                                    if {[regexp #QNANO $stcValue]} {
                                                        set stcValue -1
                                                    }
                                                }
                                                if {!$detail_streams} {
                                                    if {[regexp -nocase {count|rate} $stcName] } {
                                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                            set value 0
                                                        }
                                                        set stcValue [expr $value + $stcValue]
                                                    }
                                                }
                                                if {[regexp -nocase {rxport} $stcName]} {
                                                    if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                       set value ""
                                                    }
                                                    if {$value != "" && $value != $stcValue} {
                                                        set stcValue "$value $stcValue"
                                                    }
                                                }
                                                if {$enableRxPortFilter} {
                                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                                        keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                    }
                                                    keylset trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                } else {
                                                    if {$detailedRxStats == 0} {
                                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                                            keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                        }
                                                            keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                    }
                                                    set i 0
                                                    if {[info exists rxPortList]} {
                                                    foreach rxPort $rxPortList {
                                                        if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0)} {
                                                            if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                                set value 0
                                                            }
                                                            set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                                        } elseif {[regexp -nocase {rxport} $stcName]} {
                                                            set stcValue $stcArray($stcName)
                                                        } elseif {[info exists stcArray_per_port($stcName)]} {
                                                            set stcValue [lindex $stcArray_per_port($stcName) $i]
                                                        }
                                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                                            keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                        }
                                                        keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                        incr i
                                                    }
                                                    }
                                                }
                                            }
                                        } else {
                                            if {![regexp Hist $stcName]} {
                                                if {$stcName == "hlt"} {
                                                    set stcValue [::sth::Traffic::processCheckHeaderPresent $streamblkHndl $hltName]
                                                } else {
                                                    set stcName -$stcName
                                                    set stcValue $stcArray($stcName);
                                                    if {[regexp #QNANO $stcValue]} {
                                                        set stcValue -1
                                                    }
                                                }
                                                if {!$detail_streams} {
                                                    if {[regexp -nocase {count|rate} $stcName] } {
                                                        if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                            set value 0
                                                        }
                                                        set stcValue [expr $value + $stcValue]
                                                    }
                                                }
                                                if {[regexp -nocase {rxport} $stcName]} {
                                                    if {[catch {set value [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                       set value ""
                                                    }
                                                    if {$value != "" && $value != $stcValue} {
                                                        set stcValue "$value $stcValue"
                                                    }
                                                }
                                                if {$enableRxPortFilter} {
                                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                                        keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                    }
                                                    keylset trafficStatsKeyedList $rxPortHdl.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                } else {
                                                    if {$detailedRxStats == 0} {
                                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                                            keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                        }
                                                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                    }
                                                    set i 0
                                                    if {[info exists rxPortList]} {
                                                    foreach rxPort $rxPortList {
                                                        if {[regexp -nocase {count|rate} $stcName] && ($detail_streams == 0)} {
                                                            if {[catch {set value [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName]}]} {
                                                                set value 0
                                                            }
                                                            set stcValue [expr $value + [lindex $stcArray_per_port($stcName) $i]]
                                                        } elseif {[regexp -nocase {rxport} $stcName]} {
                                                            set stcValue $stcArray($stcName)
                                                        } elseif {[info exists stcArray_per_port($stcName)]} {
                                                            set stcValue [lindex $stcArray_per_port($stcName) $i]
                                                        }
                                                        if { $::sth::Traffic::dict_skip_port == 1 } {
                                                            keylset trafficStatsKeyedList $streamblkHndl.rx.$hltName "$stcValue"
                                                        }
                                                        keylset trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$hltName "$stcValue"
                                                        incr i
                                                    }
                                                    }
                                                }
                                            } 
                                        }
                                    }
                                }
                                if {$detail_streams == 1 && $detailedRxStats == 0} {
                                    set temp [keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx]
                                    if { $::sth::Traffic::dict_skip_port == 1 } {
                                        keylset trafficStatsKeyedList $streamblkHndl.rx.$streamIndex $temp
                                    }
                                    keylset detailTrafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.$streamIndex $temp
                                } elseif {$detail_streams == 1 && $detailedRxStats == 1} {
                                    if {[info exists rxPortList]} {
                                        foreach rxPort $rxPortList {
                                            set temp [keylget trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx]
                                            if { $::sth::Traffic::dict_skip_port == 1 } {
                                                keylset trafficStatsKeyedList $streamblkHndl.rx.$streamIndex $temp
                                            }
                                            keylset detailTrafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.$streamIndex $temp
                                        }
                                    }
                                }
                                incr streamIndex
                            }
                        }

                        #get the percentage of line rate of generator
                        if {[info exists rxPortList]} {
                            foreach rxPort $rxPortList {
                                set generatorHdl [::sth::sthCore::invoke stc::get $currPort -children-generator]
                                set generatorCfgHdl [::sth::sthCore::invoke stc::get $generatorHdl -children-GeneratorConfig]
                                set line_rate_percentage [::sth::sthCore::invoke stc::get $generatorCfgHdl -PercentageLoad]
                                if { $::sth::Traffic::dict_skip_port == 1 } {
                                    set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $streamblkHndl.rx.line_rate_percentage $line_rate_percentage]
                                }
                                set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $rxPort.stream.$streamblkHndl.rx.line_rate_percentage $line_rate_percentage]
                            }
                        }
                    }
                } else {
                    set returnVal [::sth::Traffic::processPagingForStreams $::sth::Traffic::rxStreamDataset rx $properties $detail_streams]
                }
            }
        }
    }
    
    if {($detail_streams == 1) && ($paging == 0)} {
        set trafficStatsKeyedList $detailTrafficStatsKeyedList
    }
}

## CR299119706 add Rx port filter for real time and EOT traffic results (by xiaozhi)
proc ::sth::Traffic::processRxPortResultFilter { streamHdlList isEOT enableRxPortFilter rxPortHdl} {
    variable userArgsArray
    upvar trafficStatsKeyedList trafficStatsKeyedList
    upvar $enableRxPortFilter enablePortFilter
    upvar $rxPortHdl rxPortList
    
    if {$isEOT} {
        # EOT results
        if {[info exists userArgsArray(rx_port_handle)]} {
            set rxPortList $userArgsArray(rx_port_handle)
            if {[llength $rxPortList] > 1 || [regexp "^all$" $rxPortList]} {
                set enablePortFilter 0
                set rxPortList ""
            } else {
                set enablePortFilter 1
            }
        } else {
            set enablePortFilter 0
            set rxPortList ""
        }
    } else {
        # retrieve real-time results from specific rx port
        if {[info exists userArgsArray(rx_port_handle)]} {
            set rxPortList $userArgsArray(rx_port_handle)
            if {[llength $rxPortList] > 1 || [regexp "^all$" $rxPortList]} {
                set enablePortFilter 0
                return
            } else {
                set enablePortFilter 1
            }
            if {[catch {set rxportfilter [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-RxPortResultFilter"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE;
            }
            
            set dataqueryList ""
            foreach streamHdl $streamHdlList {  
                if {[catch {set rstTarget [::sth::sthCore::invoke stc::get $streamHdl "-resultchild-Targets"]} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                foreach rst $rstTarget {
                    if {[string match -nocase "rxstreamsummaryresults*" $rst]} {
                        if {[catch {set rstSource [::sth::sthCore::invoke stc::get $rst "-resultchild-Sources"]} err]} {
                            ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                            return $::sth::sthCore::FAILURE;
                        }
                        
                        foreach src $rstSource {
                            if {[string match -nocase "resultdataset*" $src]} {
                                if {[catch {set query [::sth::sthCore::invoke stc::get $src "-children-resultquery"]} err]} {
                                    ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                                    return $::sth::sthCore::FAILURE;
                                }
                                if {[string length $query] != 0 && ![string match $query $dataqueryList]} {
                                    lappend dataqueryList $query
                                }
                            }
                        }
                    }
                }
            }
                
            if {[string length $rxportfilter] == 0} {
                if {[catch {set rxportfilter [::sth::sthCore::invoke stc::create RxPortResultFilter -under $::sth::sthCore::GBLHNDMAP(project) "-RxPortList $rxPortList"]} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::create Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                
                if {[catch {::sth::sthCore::invoke stc::config $rxportfilter "-ResultQuery {$dataqueryList}"} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                
            } else {
                if {[catch {::sth::sthCore::invoke stc::config $rxportfilter "-RxPortList $rxPortList"} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::create Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                if {[catch {set query [::sth::sthCore::invoke stc::get $rxportfilter "-ResultQuery"]} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                if {![string match -nocase $query $dataqueryList]} {
                    if {[catch {::sth::sthCore::invoke stc::config $rxportfilter "-ResultQuery {$dataqueryList}"} err]} {
                        ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                        return $::sth::sthCore::FAILURE;
                    }
                }
            }
            
            ::sth::sthCore::invoke stc::apply
            #Config rxportfilter need to sleep
            ::sth::sthCore::invoke stc::sleep 2
            
        } else {
            # retrieve real-time results from all rx ports
            set enablePortFilter 0
            set rxPortList ""
            
            if {[catch {set rxportfilter [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-RxPortResultFilter"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE;
            }
            
            if {[string length $rxportfilter] != 0} {
                if {[catch {set rxPortList [::sth::sthCore::invoke stc::get $rxportfilter "-RxPortList"]} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                    return $::sth::sthCore::FAILURE;
                }
                if {[llength $rxPortList] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $rxportfilter "-RxPortList {}"} err]} {
                        ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                        return $::sth::sthCore::FAILURE; 
                    }
                    ::sth::sthCore::invoke stc::apply
                }
                #Config rxportfilter need to sleep
                ::sth::sthCore::invoke stc::sleep 2
            }
        }
    }
}

#<port handle>.stream.unknown.<rx|tx>.total_pkts
#<port handle>.stream.unknown.<rx|tx>.total_pkt_bytes
proc ::sth::Traffic::processTrafficStatsGetUnknownOofTxCounters {porthandlevalues} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set currPort $porthandlevalues;
    
    foreach currPort $porthandlevalues {
            #set overflowResult $::sth::Traffic::arrayRxOverflowResult($currPort);
            if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-analyzer"} analyzerhndl]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Analyzer children: $analyzerhndl" {}
                #keylset trafficStatsKeyedList status $::sth::sthCore::FAILURE;
                return $::sth::sthCore::FAILURE
            } 
            if {[catch {::sth::sthCore::invoke stc::get $analyzerhndl "-children-overflowresults"} overflowResult]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Overflowresults children: $overflowResult" {}
                #keylset trafficStatsKeyedList status $::sth::sthCore::FAILURE;
                return $::sth::sthCore::FAILURE
            }
            set TableName ::sth::Traffic::traffic_stats_out_of_filter_results_stcattr
            set oofList [array names $TableName]
            
            if {[string equal $overflowResult ""]} {
                foreach hltName $oofList {
                    set stcName $::sth::Traffic::traffic_stats_out_of_filter_results_stcattr($hltName)
                    #puts "--> $stcName"
                    if {$stcName == "_none_"} {
                    } else {
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.unknown.rx.$hltName "0"]
                    }
                }
            } else {
                set stcReturnList [::sth::sthCore::invoke stc::get [lindex $overflowResult 0]];
                array set stcArray $stcReturnList;
                foreach hltName $oofList {
                    set stcName $::sth::Traffic::traffic_stats_out_of_filter_results_stcattr($hltName)
                    #puts "--> $stcName"
                    if {$stcName == "_none_"} {
                    } else {
                        set stcName -$stcName 
                        set stcValue $stcArray($stcName);
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.unknown.rx.$hltName "$stcValue"]
                    }
                }
            } 
        }
}


proc ::sth::Traffic::processTrafficStatsDiffservCounters {porthandlevalues} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set currPort $porthandlevalues;
    
    foreach currPort $porthandlevalues {
            #set overflowResult $::sth::Traffic::arrayRxOverflowResult($currPort);
            if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-analyzer"} analyzerhndl]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Analyzer children: $analyzerhndl" {}
                #keylset trafficStatsKeyedList status $::sth::sthCore::FAILURE;
                return $::sth::sthCore::FAILURE
            } 
            if {[catch {::sth::sthCore::invoke stc::get $analyzerhndl "-children-diffservresults"} diffservResults]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Overflowresults children: $overflowResult" {}
                #keylset trafficStatsKeyedList status $::sth::sthCore::FAILURE;
                return $::sth::sthCore::FAILURE
            }
            set TableName ::sth::Traffic::traffic_stats_diffserv_results_stcattr
                                         
            set qosList [array names $TableName]
            
            if {[string equal $diffservResults ""]} {
                foreach hltName $qosList {
                    set stcName $::sth::Traffic::traffic_stats_diffserv_results_stcattr($hltName)
                    #puts "--> $stcName"
                    if {$stcName == "_none_"} {
                    } else {
                        set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.qos.rx.$hltName "0"]
                    }
                }
            } else {
                foreach diffservResult $diffservResults {
                   set stcReturnList [::sth::sthCore::invoke stc::get $diffservResult];
                   puts "$stcReturnList \n"
                   puts "*****************************************************"
                   array set stcArray $stcReturnList;
                   set qosValue $stcArray(-Qos);
                   foreach hltName $qosList {
                        set stcName $::sth::Traffic::traffic_stats_diffserv_results_stcattr($hltName)
                        #puts "--> $stcName"
                        if {$stcName == "_none_"} {
                        } else {
                            set stcName2 -$stcName 
                            set stcValue $stcArray($stcName2);
                            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.$hltName $stcValue
                            #set trafficStatsKeyedList [::sth::sthCore::updateReturnInfo $trafficStatsKeyedList $currPort.stream.qos.rx.$hltName "$stcValue"]
                        }
                    }
                }
            } 
        }
}



proc ::sth::Traffic::processTraffic_controlDuration {} {
    upvar trafficControlKeyedList trafficControlKeyedList;
    upvar 1 userArgsArray userArgsArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    
    # get the port handles entered by the user here.
    
    if {[info exist userArgsArray(port_handle)]} {
        set listOfPortHandles $userArgsArray(port_handle);
        if {$listOfPortHandles == "all"} {
            if {[catch {::sth::sthCore::invoke stc::get $ProjHnd "-children-port"} returnedList]} {
                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting ports: $listOfpHandles" {};
                return -code 1 -errorcode -1 $returnedList;
            } else {
                set listOfPortHandles [::sth::sthCore::invoke stc::get $ProjHnd "-children-port"];
            }
        }
    
        foreach portHandle $listOfPortHandles {
            # for each of the port Handles, set the generator transmit mode to fixed seconds.
            set stcAttr [set ::sth::Traffic::traffic_control_stcattr(duration)];
            set durationValue $userArgsArray(duration);
            set stcAttributeList "-DurationMode SECONDS -$stcAttr $durationValue";
             
            if {[catch {set handleGenerator [::sth::sthCore::invoke stc::get $portHandle -children-generator]
        set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
        ::sth::sthCore::invoke stc::config $handleGeneratorConfig $stcAttributeList    
                } retStatus]} {
                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while configuring duration for port $portHandle" {};
                return -code 1 -errorcode -1 $retStatus;
            } else {
            ::sth::sthCore::log info "port $portHandle configured to $stcAttributeList";
            }
        }
    } elseif {[info exist userArgsArray(stream_handle)]} {
        set streamList $userArgsArray(stream_handle)
        set listOfpHandles ""
        foreach stream $streamList {
            if {[catch {set portHandle [::sth::sthCore::invoke stc::get $stream -parent]} err]} {
                ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
                return -code error $trafficControlKeyedList
            }
            if {[lsearch -exact $listOfpHandles $portHandle] < 0} {
                lappend listOfpHandles $portHandle
            }
        }
        
        foreach portHandle $listOfpHandles {
            # for each of the port Handles, set the generator transmit mode to fixed seconds.
            set stcAttr [set ::sth::Traffic::traffic_control_stcattr(duration)];
            set durationValue $userArgsArray(duration);
            set stcAttributeList "-DurationMode SECONDS -$stcAttr $durationValue";
            
            if {[catch {
            set handleGenerator [::sth::sthCore::invoke stc::get $portHandle -children-generator]
        set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
                ::sth::sthCore::invoke stc::config $handleGeneratorConfig $stcAttributeList } retStatus]} {
                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while configuring duration for port $portHandle" {};
                return -code 1 -errorcode -1 $retStatus;
            } else {
            ::sth::sthCore::log info " port $portHandle configured to $stcAttributeList";
            }
        }
        
    }

    return ::sth::sthCore::SUCCESS;
}


#add for qos
proc ::sth::Traffic::processTraffic_setFilter {} {

    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTraffic_setFilter}"
    upvar trafficControlKeyedList trafficControlKeyedList;
    upvar 1 userArgsArray userArgsArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    set ether_vlan_outer "vlan_pri vlan_id"
    set ether_vlan_inner "vlan_pri_inner vlan_id_inner"
    set ipv4_header "tos dscp"
    set valid_filters "$ether_vlan_outer $ether_vlan_inner $ipv4_header"
    # maximum number of 16-bit filters that can be used
    set max_num_filter 4
    # number of 16-bit filters each will use
    set num_of_filters_list "vlan_pri 1 vlan_pri_inner 1 vlan_id 1 vlan_id_inner 1 tos 1 dscp 2"
    array set num_of_filters $num_of_filters_list
    
    set requested_filters ""
    # check if filters are valid
    foreach filter [string tolower $userArgsArray(get)] {
        if {[lsearch -exact $valid_filters $filter] == -1} {
            ::sth::sthCore::processError trafficControlKeyedList "$filter is invalid, should be one of the following:$valid_filters" {}
            return $::sth::sthCore::FAILURE
        } elseif {[lsearch -exact $requested_filters $filter] == -1} {
            lappend requested_filters $filter
        }
    }
    # check if filters are in conflict
    if {[lsearch -exact $requested_filters tos] != -1 && [lsearch -exact $requested_filters dscp] != -1} {
        ::sth::sthCore::processError trafficControlKeyedList "tos and dscp cannot be specified together, please specify one of them." {}
        return $::sth::sthCore::FAILURE
    }
    # check the number of 16-bit filters 
    set total 0
    foreach filter $requested_filters {
        set total [expr $total + $num_of_filters($filter)]
    }
    if {$total > $max_num_filter} {
        ::sth::sthCore::processError trafficControlKeyedList "The number of 16-bit filters exceeds maximum. At most $max_num_filter 16-bit filters can be used.\
        Number of 16-bit filters each value uses: $num_of_filters_list" {}
        return $::sth::sthCore::FAILURE
    }
    
    # The number of FilteredValue_* columns each filter will take, for traffic_stats to use
    array set filter_columns {
            vlan_pri        1
            vlan_pri_inner  1
            vlan_id         1
            vlan_id_inner   1
            tos             2
            dscp            4
    }
    
    set ::sth::Traffic::FilterType $requested_filters
    
    array set filter_statement {
        vlan_pri        {::sth::sthCore::invoke stc::create "Analyzer16BitFilter" \
                                              -under $AnalyzerFrameConfigFilter \
                                              -Mask "57344" \
                                              -EndOfRange "57344" \
                                              -LocationType "VLAN_TAG" \
                                              -Offset "2" \
                                              -FilterName "Vlan 0 - Priority"}
        vlan_pri_inner  {::sth::sthCore::invoke stc::create "Analyzer16BitFilter" \
                                              -under $AnalyzerFrameConfigFilter \
                                              -Mask "57344" \
                                              -EndOfRange "57344" \
                                              -LocationType "VLAN_TAG" \
                                              -Offset "2" \
                                              -FilterName "Vlan 1 - Priority"}
        dscp            {::sth::sthCore::invoke stc::create "Analyzer16BitFilter" \
                                              -under $AnalyzerFrameConfigFilter \
                                              -Mask "65280" \
                                              -EndOfRange "65280" \
                                              -LocationType "START_OF_IPV4_HDR" \
                                              -Offset "1" \
                                              -FilterName "dscp Byte"}
    }
    # Of multiple columns, specify a key column
    # tos             "IP Precedence" "ToS Byte (bits)" 
    # dscp            "DSCP (int)" "DiffServ" "ECN" "ECN (bits)"
    array set ::sth::Traffic::filter_key_column {
        vlan_pri        "Vlan 0 - Priority (bits)"
        vlan_pri_inner  "Vlan 1 - Priority (bits)"
        vlan_id         "Vlan 0 - ID (int)"
        vlan_id_inner   "Vlan 1 - ID (int)"
        tos             "ToS Byte (bits)" 
        dscp            "DSCP (int)"
    }
        
    array set filter_strs {
        vlan_pri        "<pri filterMinValue=\"0\" filterMaxValue=\"111\">111</pri>"
        vlan_pri_inner  "<pri filterMinValue=\"0\" filterMaxValue=\"111\">111</pri>"
        vlan_id         "<id filterMinValue=\"0\" filterMaxValue=\"4095\">4095</id>"
        vlan_id_inner   "<id filterMinValue=\"0\" filterMaxValue=\"4095\">4095</id>"
        tos             "<tosDiffserv>
                        <tos>
                        <precedence filterMinValue=\"0\" filterMaxValue=\"7\">7</precedence>
                        <dBit filterMinValue=\"0\" filterMaxValue=\"1\">1</dBit>
                        <tBit filterMinValue=\"0\" filterMaxValue=\"1\">1</tBit>
                        <rBit filterMinValue=\"0\" filterMaxValue=\"1\">1</rBit>
                        <mBit filterMinValue=\"0\" filterMaxValue=\"1\">1</mBit>
                        <reserved filterMinValue=\"0\" filterMaxValue=\"1\">1</reserved>
                        </tos>
                        </tosDiffserv>"
        dscp            "<tosDiffserv>
                        <diffServ>
                        <dscpHigh filterMinValue=\"0\" filterMaxValue=\"7\">7</dscpHigh>
                        <dscpLow filterMinValue=\"0\" filterMaxValue=\"7\">7</dscpLow>
                        <reserved filterMinValue=\"0\" filterMaxValue=\"11\">11</reserved>
                        </diffServ>
                        </tosDiffserv>"
    }

    set ethernet_pdu_start "<pdu name=\"eth1\" pdu=\"ethernet:EthernetII\">"
    set ipv4_pdu_start "<pdu name=\"ipv4\" pdu=\"ipv4:IPv4\">"
    set vlan_str "<vlans><Vlan name=\"Vlan\">INSERT_OUTER_VLAN</Vlan><Vlan name=\"iVlan\">INSERT_INNER_VLAN</Vlan></vlans>"
    set ipv4_str ""
    
    set frameconfig "<frame><config><pdus>"
        
        ### start of Ethernet pdu
        set outer_vlan ""
        set inner_vlan ""
        # outer vlan
        foreach filter $ether_vlan_outer {
            if {[lsearch -exact $requested_filters $filter] != -1} {
                append outer_vlan $filter_strs($filter)
            }
        }

        # inner vlan
        foreach filter $ether_vlan_inner {
            if {[lsearch -exact $requested_filters $filter] != -1} {
                append inner_vlan $filter_strs($filter)
            }
        }

        if {$inner_vlan != ""} {
            regsub "INSERT_OUTER_VLAN" $vlan_str $outer_vlan vlan_str
            regsub "INSERT_INNER_VLAN" $vlan_str $inner_vlan vlan_str
        } elseif {$outer_vlan != ""} {
            regsub "INSERT_OUTER_VLAN" $vlan_str $outer_vlan vlan_str
            regsub "<Vlan name=\"iVlan\">INSERT_INNER_VLAN</Vlan>" $vlan_str $inner_vlan vlan_str
        } else {
            set vlan_str ""
        }

        if {$vlan_str != ""} {
            append frameconfig $ethernet_pdu_start $vlan_str "</pdu>"
        }
        ### end of Ethernet pdu
        ### start of IPv4 pdu
        # tos or dscp
        foreach filter $ipv4_header {
            if {[lsearch -exact $requested_filters $filter] != -1} {
                append ipv4_str $filter_strs($filter)
            }
        }
        
        if {$ipv4_str != ""} {
            append frameconfig $ipv4_pdu_start $ipv4_str "</pdu>"
        }
        ### end of IPv4 pdu
        
        append frameconfig "</pdus></config></frame>"
        ### end of analyzer frame config
    
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set portlist [::sth::sthCore::invoke stc::get $ProjHnd -children-Port]    
    foreach port $portlist {
        set analyzer [::sth::sthCore::invoke stc::get $port -children-Analyzer]
        set AnalyzerFrameConfigFilter [::sth::sthCore::invoke stc::get $analyzer -children-AnalyzerFrameConfigFilter]
        #if the AnalyzerFrameConfigFilter already exist, delete it and recreate
        if {$AnalyzerFrameConfigFilter != ""} {
             if {[catch {::sth::sthCore::invoke stc::delete $AnalyzerFrameConfigFilter} deleteStatus ]} {
                return -code 1 -errorcode -1 $deleteStatus
             }
            ::sth::sthCore::invoke stc::apply 
        }
        
        # create frame config
        set AnalyzerFrameConfigFilter [::sth::sthCore::invoke stc::create AnalyzerFrameConfigFilter \
                                               -under $analyzer \
                                               -FrameConfig "$frameconfig"]
       
        foreach filter $requested_filters {
            if {[info exists filter_statement($filter)]} {
                eval $filter_statement($filter)
            }
        }
    }
}


proc ::sth::sthCore::getObjectIndex { object } {
    set index -1
    set len [string length $object]
    for { set i $len } { $i > 0 } { set i [expr {$i - 1}] } {
    if { ![string is integer [string range $object $i $i]] } {
       set index [string range $object  [expr {$i + 1}] [ expr {$len - 1} ] ]
       break
    }
    }
    return $index
}

proc ::sth::Traffic::processGetDiffservQuery {type len userlist attrList formattedList formattedqueryList } {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    
    regexp {([^:]*),(\s*?$)}  $formattedList match formattedList
    
    if {$::sth::Traffic::EOTResultsFileName != ""} {
    set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
    } else {
    ::sth::sthCore::processError trafficStatsKeyedList "EOTResults db file name is null, EOTResults db file has not been created" {}
        return $::sth::sthCore::FAILURE;
    }
    
    if {[file exists $hltfile]} {
        if {[file size $hltfile] == 0} {
            set sth::Traffic::eotPortQueryEmpty 1
        } else {
            set query "select IntHandle from handlemap where StringHandle = $formattedList"
            set value [db eval $query ]
            set query "select Qos, QosBinary, IpPrecedence, Ecn, DiffServ, Ipv4FrameCount, Ipv6FrameCount from diffservresults where ParentHnd = '$value'" 
            set values [db eval $query ]
            list $values
            set ::sth::Traffic::arrayDiffServResult $values
            
        }
    } else {
        set sth::Traffic::eotPortQueryEmpty 1
    }
    
    if {$::sth::Session::isEotIntStats == 1} {
        set ::sth::Session::isEotIntStats 0
        #return $userlist
    } else {
        ::sth::Traffic::processTrafficStatsGetEOTDiffservCounters $userlist "rx" $attrList   
    }

}


proc ::sth::Traffic::processGetAggQuery {type len userlist attrList formattedList formattedqueryList properties} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    
    regexp {([^:]*),(\s*?$)}  $formattedList match formattedList
             
    if {$type == "aggregate_rxjoin"} {
        #puts "GETTING EOT AnayzerPortResults\n"
        set query "select stringhandle,analyzerportresults.datasetid, $formattedqueryList \
                    from  port, analyzer, analyzerportresults, handlemap \
                    where port.handle = handlemap.inthandle AND \
                          handlemap.stringhandle in ($formattedList) AND\
                          port.handle = analyzer.parenthnd  AND \
                          analyzerportresults.datasetid = '1' AND \
                          analyzer.handle = analyzerportresults.parenthnd " 
    } else {
        #puts "GETTING EOT GeneratorPortResults\n"
        set query "select stringhandle, generatorportresults.datasetid, $formattedqueryList \
            from   port, generator, generatorportresults, handlemap \
            where  inthandle = port.handle AND \
                   port.handle = generator.parenthnd AND \
                   generator.handle = generatorportresults.parenthnd AND \
                   generatorportresults.datasetid = '1' AND \
                   stringhandle in ($formattedList)"
    }
    
    #add for qos
   if {$::sth::Traffic::FilterType != "" && $type == "aggregate_rxjoin"} {
        set filterNameQuery "select FilteredName_1, FilteredName_2, FilteredName_3, FilteredName_4,\
        FilteredName_5, FilteredName_6, FilteredName_7, FilteredName_8, FilteredName_9, FilteredName_10\
        from RxEotAnalyzerFilterNamesTable where id=1"
        set filterNameList [db eval $filterNameQuery]
        
        # mapping example: vlan_id -> FilteredValue_1, tos -> FilteredValue_3, ...
        array unset ::sth::Traffic::filterValueNameToId
        array set ::sth::Traffic::filterValueNameToId {}
        
        set ::sth::Traffic::selectedDbColumns ""
        
        array unset ::sth::Traffic::arrayFilterResult
        
        for {set i 0} {$i < 10} {incr i}  {
            set filterName [lindex $filterNameList $i]
            if {$filterName == ""} {break}
            foreach filter $::sth::Traffic::FilterType { 
                if {$filterName == $::sth::Traffic::filter_key_column($filter)} {
                    set j [expr $i + 1]
                    set ::sth::Traffic::filterValueNameToId($filter) FilteredValue_$j
                    lappend ::sth::Traffic::selectedDbColumns FilteredValue_$j
                    break
                }
            }            
        }  
        lappend ::sth::Traffic::selectedDbColumns "SigFrameCount"

        array unset filterQuery
        foreach port $userlist {
            set portName [::sth::sthCore::invoke stc::get $port -name]
            set filterQuery($port) "select [join $::sth::Traffic::selectedDbColumns ,] \
                  from RxEotStreamResults, RxEotAnalyzerFilterValuesTable \ 
                  where RxEotStreamResults.Comp32 = RxEotAnalyzerFilterValuesTable.Comp32 AND \
                  RxEotStreamResults.Comp16_1 = RxEotAnalyzerFilterValuesTable.Comp16_1 AND \
                  RxEotStreamResults.Comp16_2 = RxEotAnalyzerFilterValuesTable.Comp16_2 AND \
                  RxEotStreamResults.Comp16_3 = RxEotAnalyzerFilterValuesTable.Comp16_3 AND \
                  RxEotStreamResults.Comp16_4 = RxEotAnalyzerFilterValuesTable.Comp16_4 AND \
                  RxEotStreamResults.PortName = RxEotAnalyzerFilterValuesTable.PortName AND \
                  RxEotStreamResults.PortName = '$portName'"
        }
    }
  
    
    #set hltfile [file join $::sth::Traffic::hltDir eotResultsHltApi.db]
    if {$::sth::Traffic::EOTResultsFileName != ""} {
        set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
    } else {
        ::sth::sthCore::processError trafficStatsKeyedList "EOTResults db file name is null, EOTResults db file has not been created" {}
        return $::sth::sthCore::FAILURE;
    }
    
    if {[file exists $hltfile]} {
        if {[file size $hltfile] == 0} {
            set sth::Traffic::eotPortQueryEmpty 1
        } else {
            set values [db eval $query ]
        }
        #add for qos
        if { [info exists filterQuery] } {
            foreach port [array names filterQuery] {
                set filterValues [db eval $filterQuery($port)]
                if {$filterValues != ""} {
                    list $filterValues
                    set ::sth::Traffic::arrayFilterResult($port) $filterValues
                }
            }
        }
           
        if {([llength $values] == 0) || ([llength $values] == 2)} {
            set sth::Traffic::eotPortQueryEmpty 1
        }
    } else {
        set sth::Traffic::eotPortQueryEmpty 1
    }
    
    if {($::sth::Traffic::eotPortQueryEmpty == 1) && ($::sth::Session::intStats == 1)} {
        set ::sth::Session::intStats 0
        return
    }
    set j 2
    
    for {set i 0} {$i < $len} {incr i} {
        if {$::sth::Traffic::isClear} {
            # if clear_stats is done
            set ::sth::Traffic::arraySTCArray([lindex $attrList $i]) 0
        } else {
            set ::sth::Traffic::arraySTCArray([lindex $attrList $i]) [lindex $values $j]
        }
        incr j
    }
    if {$::sth::Session::isEotIntStats == 1} {
        set ::sth::Session::isEotIntStats 0
        #return $userlist
    } else {
        if {$type == "aggregate_rxjoin"} {
            ::sth::Traffic::processTrafficStatsGetEOTAggCounters $userlist "rx" $properties
        } else {
            ::sth::Traffic::processTrafficStatsGetEOTAggCounters $userlist "tx" $properties
        }
    }
}

proc ::sth::Traffic::processGetStreamsQuery {type attrList userlist len streamBlk formattedqueryList formattedList properties detail_streams} {

    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processGetStreamsQuery}"
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    set level [info level]
    #upvar [expr $level-2] userArgsArray userArray;
    #with the hltapiwrapper, the upvar should not be [expr $level-2]
    upvar 2 userArgsArray userArray
    variable detailedRxStats

    regexp {([^:]*),(\s*?$)}  $formattedList match formattedList

    set FLAG_detail_stream  0
    set FLAG_per_port       0
    if {1 == $detail_streams} {
        set FLAG_detail_stream 1
    } elseif {1 == $detailedRxStats} {
        set FLAG_per_port 1
    }

    # Remove if (0 == $FLAG_detail_stream) to let detailed_streams can also use SQL 
    # aggregate functions.
        set querylist ""
        foreach entry $formattedqueryList {
            # Strip off any training comma. We'll add it back later.
            regsub {,\s*$} $entry {} entry
            
            # Strip away the prefix from the formattedquery. This should leave
            # us with the name of the statistic.
            # eg: rxeotstreamresults.HistBin12Count -> HistBin12Count
            set stat [lindex [split $entry .] 1]
            if {$stat eq ""} {
                set stat $entry
            }

            if { [regexp "Count" $entry] } {
                append querylist ", SUM($entry) AS $stat"
            } elseif { [regexp "DroppedFramePercent" $entry] } {
            # Because of we cannot get DroppedFramePercent from DB table, we have to calculate it in traffic.tcl.
            # To avoid raising error msg, we will ignore dropped_pkts_percent of traffic_stats_streameot_rx_results.
            } elseif { [regexp "Max" $entry] } {
                append querylist ", MAX($entry) AS $stat"
            } elseif { [regexp "LastArrival" $entry] } {
                append querylist ", MAX($entry) AS $stat"
            } elseif { [regexp "Min" $entry] } {
                append querylist ", MIN($entry) AS $stat"
            } elseif { [regexp "FirstArrival" $entry] } {
                append querylist ", MIN($entry) AS $stat"
            } elseif { [regexp "AvgLatency" $entry] } {
                append querylist ", sum(TotalLatency) / sum(SigFrameCount) / 100 AS $stat"
            } elseif { [regexp "Avg" $entry] } {
                append querylist ", AVG($entry) AS $stat"
            } else {
                append querylist ", $entry AS $stat"
            }
        }
    
    if {$FLAG_detail_stream || $FLAG_per_port} {
        set querylist_detail ""
        foreach entry $formattedqueryList {
            # Strip off any training comma. We'll add it back later.
            regsub {,\s*$} $entry {} entry
            if { [regexp "DroppedFramePercent" $entry] } {
                # Because of we cannot get DroppedFramePercent from DB table, we have to calculate it in traffic.tcl.
                # To avoid raising error msg, we will ignore dropped_pkts_percent of traffic_stats_streameot_rx_results.
            } else {
                append querylist_detail ", $entry"
            }
        }
    }
    foreach stream [split $formattedList ","] {
        set stream [string trim $stream]
        if {$type == "streameot_rx"} {

            set query_PortName "
                    SELECT 
                        DISTINCT(PortName),
                        porthandlemap.stringhandle AS 'PortHandle',
                        handlemap.stringhandle AS 'StreamBlockHandle',
                        rxeotstreamresults.datasetid
                    FROM
                        port,
                        streamblock,
                        rxeotstreamresults,
                        handlemap,
                        handlemap porthandlemap
                    WHERE
                        handlemap.inthandle = streamblock.handle AND
                        porthandlemap.inthandle = port.handle AND
                        port.handle = streamblock.parenthnd AND
                        streamblock.handle = rxeotstreamresults.parentstreamblock AND
                        handlemap.stringhandle in ($stream)
                    ORDER BY
                        PortHandle,
                        StreamBlockHandle"

            if {![info exists userArray(rx_port_handle)]} {
                if {[info exists querylist]} {
                    set query "
                            SELECT
                                porthandlemap.stringhandle AS 'PortHandle',
                                handlemap.stringhandle AS 'StreamBlockHandle',
                                rxeotstreamresults.datasetid
                                $querylist
                            FROM
                                port,
                                streamblock,
                                rxeotstreamresults,
                                handlemap,
                                handlemap porthandlemap
                            WHERE
                                handlemap.inthandle = streamblock.handle AND
                                porthandlemap.inthandle = port.handle AND
                                port.handle = streamblock.parenthnd AND
                                streamblock.handle = rxeotstreamresults.parentstreamblock AND
                                handlemap.stringhandle in ($stream)
                            ORDER BY
                                PortHandle,
                                StreamBlockHandle"
                }
                if {[info exists querylist_detail]} {
                    # Use SQL aggregate functions to get resutls. In cases like 1 tx and multiple rx ports,
                    # this can keep the number of streams correct, besides getting the values.
                    set select_clause "porthandlemap.stringhandle AS 'PortHandle',
                                rxeotstreamresults.PortName AS 'hltPortName',
                                handlemap.stringhandle AS 'StreamBlockHandle',
                                rxeotstreamresults.datasetid,
                                rxeotstreamresults.Comp32
                                $querylist"
                    set from_clause "port,
                                streamblock,
                                rxeotstreamresults,
                                handlemap,
                                handlemap porthandlemap"
                    set where_clause "handlemap.inthandle = streamblock.handle AND
                                porthandlemap.inthandle = port.handle AND
                                port.handle = streamblock.parenthnd AND
                                streamblock.handle = rxeotstreamresults.parentstreamblock AND
                                handlemap.stringhandle in ($stream)"
                    
                    if {$::sth::Traffic::FilterType != ""} {
                        append from_clause ", RxEotAnalyzerFilterValuesTable"
                        append where_clause " AND
                                rxeotstreamresults.Comp32 = RxEotAnalyzerFilterValuesTable.Comp32 AND 
                                rxeotstreamresults.portname = RxEotAnalyzerFilterValuesTable.portname"           
                    }
                    set query_detail "
                            SELECT
                                $select_clause
                            FROM
                                $from_clause
                            WHERE
                                $where_clause
                            GROUP BY 
                                rxeotstreamresults.Comp32
                            ORDER BY
                                PortHandle,
                                StreamBlockHandle"
                                
                    regsub {FROM}  $query_PortName ",rxeotstreamresults.Comp32 FROM" query_PortName
                }
            } else {
                set rxPortHdl $userArray(rx_port_handle)
                if {[regexp "^all$" $rxPortHdl]} {
                    set str_len [string length $stream]
                    set streamblock [string range $stream 1 [expr $str_len-2]]
                    set stream_parent [::sth::sthCore::invoke stc::get $streamblock -parent]
                    set port_list [::sth::sthCore::invoke stc::get project1 -children-port]
                    set port_list_new ""
                    foreach port $port_list {
                        if {![regexp "^$port$" $stream_parent]} {
                            set port_list_new [concat $port_list_new $port]
                        }
                    }
                    set rxPortHdl $port_list_new
                }
                set port_match_sq ""
                set index 0
                foreach rxPort $rxPortHdl {
                    if {$index > 0} {
                        set port_match_sq [concat $port_match_sq "OR"]
                    }
                    set port_match_sq [concat $port_match_sq "handlemap.stringhandle = \'$rxPort\'"]
                    incr index
                }
                if {[info exists querylist]} {
                    set query "
                            SELECT
                                handlemap.stringhandle AS 'PortHandle',
                                RxEotStreamResults.parentstreamblock AS 'StreamBlockHandle',
                                rxeotstreamresults.datasetid
                                $querylist
                            FROM
                                rxeotstreamresults,
                                handlemap,
                                handlemap porthandlemap
                            WHERE
                                handlemap.inthandle = rxeotstreamresults.parenthnd AND
                                porthandlemap.inthandle = rxeotstreamresults.parentstreamblock AND
                                ($port_match_sq) AND
                                porthandlemap.stringhandle = $stream"
                    
                }
                if {[info exists querylist_detail]} {
                    set query_detail "
                            SELECT
                                handlemap.stringhandle AS 'PortHandle',
                                RxEotStreamResults.parentstreamblock AS 'StreamBlockHandle',
                                rxeotstreamresults.datasetid
                                $querylist_detail
                            FROM
                                rxeotstreamresults,
                                handlemap,
                                handlemap porthandlemap
                            WHERE
                                handlemap.inthandle = rxeotstreamresults.parenthnd AND
                                porthandlemap.inthandle = rxeotstreamresults.parentstreamblock AND
                                ($port_match_sq) AND
                                porthandlemap.stringhandle = $stream"
                }
            }
        } elseif {$type == "streameot_tx"} {

            # Keep old logic consistency. Maybe streameot_tx can also use querylist, but not testing yet.
            if {(1 == $FLAG_detail_stream) && [info exists querylist]} {
                unset querylist
            }
            set query_PortName "
                    SELECT
                        DISTINCT(PortName),
                        porthandlemap.stringhandle AS 'PortHandle',
                        handlemap.stringhandle AS 'StreamBlockHandle',
                        txeotstreamresults.datasetid
                    FROM
                        port,
                        streamblock,
                        txeotstreamresults,
                        handlemap,
                        handlemap porthandlemap
                    WHERE
                        handlemap.inthandle = streamblock.handle AND
                        porthandlemap.inthandle = port.handle AND
                        port.handle = streamblock.parenthnd AND
                        streamblock.handle = txeotstreamresults.parentstreamblock AND
                        handlemap.stringhandle in ($stream) AND
                        streamblock.handle = txeotstreamresults.parentstreamblock
                    ORDER BY
                        PortHandle,
                        StreamBlockHandle"

            if {[info exists querylist]} {
                set query "
                        SELECT
                            porthandlemap.stringhandle AS 'PortHandle',
                            handlemap.stringhandle AS 'StreamBlockHandle',
                            txeotstreamresults.datasetid
                            $querylist
                        FROM
                            port,
                            streamblock,
                            txeotstreamresults,
                            handlemap,
                            handlemap porthandlemap
                        WHERE
                            handlemap.inthandle = streamblock.handle AND
                            porthandlemap.inthandle = port.handle AND
                            port.handle = streamblock.parenthnd AND
                            streamblock.handle = txeotstreamresults.parentstreamblock AND
                            handlemap.stringhandle in ($stream) AND
                            streamblock.handle = txeotstreamresults.parentstreamblock
                        ORDER BY
                            PortHandle,
                            StreamBlockHandle"
            }
            if {[info exists querylist_detail]} {
                set query_detail "
                        SELECT
                            porthandlemap.stringhandle AS 'PortHandle',
                            handlemap.stringhandle AS 'StreamBlockHandle',
                            txeotstreamresults.datasetid
                            $querylist_detail
                        FROM
                            port,
                            streamblock,
                            txeotstreamresults,
                            handlemap,
                            handlemap porthandlemap
                        WHERE
                            handlemap.inthandle = streamblock.handle AND
                            porthandlemap.inthandle = port.handle AND
                            port.handle = streamblock.parenthnd AND
                            streamblock.handle = txeotstreamresults.parentstreamblock AND
                            handlemap.stringhandle in ($stream) AND
                            streamblock.handle = txeotstreamresults.parentstreamblock
                        ORDER BY
                            PortHandle,
                            StreamBlockHandle"
            }
        }

        array unset ::sth::Traffic::arraySTCArray
        array unset ::sth::Traffic::arraySTCArray_per_port
        array set   ::sth::Traffic::arraySTCArray {}
        array set   ::sth::Traffic::arraySTCArray_per_port {}

        # Comp32 is stream ID, we need this value to group streams into streamblock.
        if {(1 == $FLAG_detail_stream) && [lsearch -exact $attrList "Comp32"] == -1} {
            lappend attrList "Comp32"    
        }
        
        
        if {1 == $FLAG_detail_stream} {
            set rxPortList ""
            if {$type == "streameot_rx"} {
                db eval $query_PortName results {
                    set rxPortList [::sth::sthCore::updateReturnInfo $rxPortList $results(Comp32) "$results(PortName), "]
                }
            }
            db eval $query_detail results {
                foreach stat $attrList {
                    if { [info exists results($stat)] && !($results($stat) eq "")} {
                        set value $results($stat)
                        if {$type == "streameot_rx" } {
                            if {[string equal -nocase "portname" $stat]} {
                                continue
                            } elseif {[string equal -nocase "Comp32" $stat]} {
                                set rxPorts [string trim [keylget rxPortList $value] ", "]
                                lappend ::sth::Traffic::arraySTCArray(PortName) $rxPorts
                            }
                        }
                        
                        if {[regexp {FilteredValue_\d+} $stat]} {
                            set filter $::sth::Traffic::filterValueIdToName($stat)
                            if {$filter == "tos"} {
                                set tosbin [string range $value 3 6]
                                set precbin [string range $value 0 2]
                                set tosValue [::sth::sthCore::binToInt $tosbin]
                                set precValue [::sth::sthCore::binToInt $precbin]
                                lappend ::sth::Traffic::arraySTCArray(tos) $tosValue
                                lappend ::sth::Traffic::arraySTCArray(prec) $precValue
                            } else {
                                if {$filter == "vlan_pri" || $filter == "vlan_pri_inner" || $filter == "dscp"} {
                                    if {$filter != "dscp"} {
                                        set value [::sth::sthCore::binToInt $value]
                                    } 
                                    if { [regexp -all {vlan_pri|dscp} $::sth::Traffic::FilterType] == 1 } {
                                        # For backward compatiblity, output 'qos' if only one of "vlan_pri", "vlan_pri_inner" and "dscp" is specified.
                                        set filter "qos"
                                    }
                                } else {
                                    # For backward compatiblity, when outputting, "vlan_id", "vlan_id_inner" -> "vlan", "vlan_inner"
                                    regsub vlan_id $filter vlan filter
                                }
                                lappend ::sth::Traffic::arraySTCArray($filter) $value
                            }
                        } else {
                            lappend ::sth::Traffic::arraySTCArray($stat) $value
                        }
                    } else {
                        lappend ::sth::Traffic::arraySTCArray($stat) 0
                    }
                }
            }
        } else {
            db eval $query_PortName results {
                append ::sth::Traffic::arraySTCArray(PortName) "$results(PortName) "
            }
            if {![info exists ::sth::Traffic::arraySTCArray(PortName)]} {
                set ::sth::Traffic::arraySTCArray(PortName) 0
            }
            db eval $query results {
                foreach stat $attrList {
                    if {[regexp "PortName" $stat]} {
                        continue
                    }
                    if { [info exists results($stat)] && !($results($stat) eq "")} {
                        set ::sth::Traffic::arraySTCArray($stat) $results($stat)
                    } else {
                        set ::sth::Traffic::arraySTCArray($stat) 0
                    }
                }
            }

            if {1 == $FLAG_per_port} {
                set ::sth::Traffic::arraySTCArray_per_port(PortName) $::sth::Traffic::arraySTCArray(PortName)
                db eval $query_detail results {
                    foreach stat $attrList {
                        if {[regexp "PortName" $stat]} {
                            continue
                        }
                        if { [info exists results($stat)] && !($results($stat) eq "")} {
                            lappend ::sth::Traffic::arraySTCArray_per_port($stat) $results($stat)
                        } else {
                            lappend ::sth::Traffic::arraySTCArray_per_port($stat) 0
                        }
                    }
                }
            }
        }

        regexp {'([^']*)'} $stream match stream
        if {$type == "streameot_rx"} {
            set cmd [::sth::Traffic::processTrafficStatsGetEOTStreamCounters $userlist "rx" $stream $properties $detail_streams]
        } else {
            set cmd [::sth::Traffic::processTrafficStatsGetEOTStreamCounters $userlist "tx" $stream $properties $detail_streams]
        }
    }
}

# Arguments:
# statHnd   a port handle or a list of streamblock handles
proc ::sth::Traffic::processTrafficStats_GetEOTResults {type streamBlk {statHnd ""} properties detail_streams} {
    
    ::sth::sthCore::log debug "{Calling ::sth::Traffic::processTrafficStats_GetEOTResults}"
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    
    if {$properties == "_none_"} {
        return;
    }
    #if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
    #    load tclsqlite3
    #} else {
    #    load libtclsqlite3.so
    #}
    
#    sqlite3 db [file join $::sth::Traffic::hltDir eotResultsHltApi.db]
    if {$::sth::Traffic::EOTResultsFileName != ""} {
        sqlite3 db [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
    } else {
        ::sth::sthCore::processError trafficStatsKeyedList "EOTResults db file name is null, can not open EOTResults DataBase" {}
        return $::sth::sthCore::FAILURE;
    }
    # FIXME: (MGJ) We need to catch all exceptions so that the DB file
    #              can be closed properly.
    set errorHasOccurred [catch {
    if {$userArray(mode) == "aggregate"} {
        set userlist $statHnd
        if {$type == "aggregate_rxjoin"} {
            set viewEotAgglist [::sth::Traffic::createviewlist $type]
        } elseif {$type == "aggregate_txjoin"} {
            set viewEotAgglist [::sth::Traffic::createviewlist $type]
        }
        set attrList $viewEotAgglist
    } elseif {$userArray(mode) == "diffserv"} {
        set userlist $userArray(port_handle)
        set viewEotAgglist [::sth::Traffic::createviewlist $type]
        set attrList $viewEotAgglist
    } elseif {($userArray(mode) == "streams") ||
            ($userArray(mode) == "detailed_streams")} {
        set userlist $statHnd
        set viewEotStreamlist ""
        if {$type == "streameot_rx"} {
            set viewEotStreamlist [::sth::Traffic::createviewlist $type]
        } elseif {$type == "streameot_tx"} {
            set viewEotStreamlist [::sth::Traffic::createviewlist $type]
        }
        set attrList $viewEotStreamlist
    } elseif {$userArray(mode) == "all"} {
        set userlist $statHnd
        if {$type == "aggregate_rxjoin"} {
            set viewEotAgglist [::sth::Traffic::createviewlist $type]
        } elseif {$type == "aggregate_txjoin"} {
            set viewEotAgglist [::sth::Traffic::createviewlist $type]
        }
        set viewEotStreamlist ""
        if {$type == "streameot_rx"} {
            set viewEotStreamlist [::sth::Traffic::createviewlist $type]
        } elseif {$type == "streameot_tx"} {
            set viewEotStreamlist [::sth::Traffic::createviewlist $type]
        }
        if {($type == "streameot_rx") || ($type == "streameot_tx")} {
            set attrList $viewEotStreamlist
        } elseif {($type == "aggregate_rxjoin") || ($type == "aggregate_txjoin")} {
            set attrList $viewEotAgglist
        }
        if {$type == "diffserv"} {
            set viewEotAgglist [::sth::Traffic::createviewlist $type]
            set attrList $viewEotAgglist
        }
    }
    
    if {$properties != "" } {
        set attrList [::sth::Traffic::createPropertyViewlist $type $properties]
    }
    
    # Analyzer filter results added into DB detailed_streams rx 
    if {$detail_streams && $type == "streameot_rx" && $::sth::Traffic::FilterType != ""} {
        append attrList " [::sth::Traffic::createFilterViewlist]"
    }
            
    set formattedList ""
    foreach userInout $userlist {
        #TODO: is it a bug?
        set formattedList '$userInout',
            #lappend formattedList '$userInout',
    
        set formattedqueryList ""
        set len [llength $attrList]
        set i 0
        foreach attr $attrList {
            incr i
            if {$i == $len} {
                if {$type == "streameot_rx"} {
                    if {[regexp "FilteredValue_" $attr]} {
                        lappend formattedqueryList RxEotAnalyzerFilterValuesTable.$attr
                    } else {
                        lappend formattedqueryList rxeotstreamresults.$attr
                    }
                } elseif {$type == "diffserv"} {
                    if {![regexp Rate $attr]} {
                        lappend formattedqueryList $attr
                    }
                } else {
                    lappend formattedqueryList $attr
                }
            } else {
                if {$type == "streameot_rx"} {
                    if {[regexp "FilteredValue_" $attr]} {
                        lappend formattedqueryList RxEotAnalyzerFilterValuesTable.$attr,
                    } else {
                        lappend formattedqueryList rxeotstreamresults.$attr,
                    }
                } elseif {$type == "diffserv"} {
                    if {![regexp Rate $attr]} {
                        lappend formattedqueryList $attr
                    }
                } else {
                    lappend formattedqueryList $attr,
                }
            }
        }
        if {$userArray(mode) == "aggregate"} {
            ::sth::Traffic::processGetAggQuery $type $len $userInout $attrList $formattedList $formattedqueryList $properties
        }  elseif {$userArray(mode) == "diffserv"} {
            ::sth::Traffic::processGetDiffservQuery $type $len $userInout $attrList $formattedList $formattedqueryList
        } elseif {($userArray(mode) == "streams") ||
            ($userArray(mode) == "detailed_streams")} {
            if {$streamBlk == 1} {
                ::sth::Traffic::processGetStreamsQuery $type $attrList $userInout  $len $streamBlk $formattedqueryList $formattedList $properties $detail_streams
            } else {
                set formattedList ""
                if {[catch {::sth::sthCore::invoke stc::get $userInout "-children-streamblock"} streamblkHndlList]} {
                        # FIXME: (MGJ)
                        db close
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting streamblock children: $streamblkHndlList" {}
                    return $::sth::sthCore::FAILURE;
                }
                foreach strmblk $streamblkHndlList {
                    lappend formattedList '$strmblk',
                }
                ::sth::Traffic::processGetStreamsQuery $type $attrList $userInout  $len $streamBlk $formattedqueryList $formattedList $properties $detail_streams
            }
        } elseif {$userArray(mode) == "all"} {
            if {($type == "aggregate_rxjoin") || ($type == "aggregate_txjoin")} {
                ::sth::Traffic::processGetAggQuery $type $len $userInout  $attrList $formattedList $formattedqueryList $properties
            } elseif {$type == "diffserv"} {
                ::sth::Traffic::processGetAggQuery $type $len $userInout  $attrList $formattedList $formattedqueryList $properties
            } elseif {($type == "streameot_rx") || ($type == "streameot_tx")} {
                if {$streamBlk == 1} {
                ::sth::Traffic::processGetStreamsQuery $type $attrList $userInout  $len $streamBlk $formattedqueryList $formattedList $properties $detail_streams
                } else {
                    set formattedList ""
                    if {[catch {::sth::sthCore::invoke stc::get $userInout "-children-streamblock"} streamblkHndlList]} {
                            # FIXME: (MGJ)
                            db close
                        ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting streamblock children: $streamblkHndlList" {}
                        return $::sth::sthCore::FAILURE;
                    }
                    foreach strmblk $streamblkHndlList {
                        lappend formattedList '$strmblk',
                    }
                    ::sth::Traffic::processGetStreamsQuery $type $attrList $userInout  $len $streamBlk $formattedqueryList $formattedList $properties $detail_streams
                }
            }
        }
    }
    } errmsg]
    
    #close the db file
    #db close [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
    db close
    # FIXME: (MGJ) Report any exceptions.          
    if { $errorHasOccurred } {    
        ::sth::sthCore::processError trafficStatsKeyedList "Internal Error while gathering EoT results: $errmsg" {}
        return $::sth::sthCore::FAILURE;
    }    
}


proc ::sth::Traffic::processTraffic_controlAction {} {
    
    upvar trafficControlKeyedList trafficControlKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set errMsg "";
    
    set action_reqd $userArray(action);
    if {$action_reqd == "run" || $action_reqd == "stop" || $action_reqd == "clear_stats" || $action_reqd == "destroy" || $action_reqd == "reset" || $action_reqd == "poll"} {
    } else {
        set errMsg "Action entered is either not a valid action or is not supported at this time: $action_reqd"
        return -code 1 -errorcode -1 $errMsg;
    }
    
    if {[info exists userArray(port_handle)]} {
        set listOfpHandles $userArray(port_handle)
    } elseif {[info exist userArray(stream_handle)]} {
        set listOfpHandles $userArray(stream_handle)
    } else {
        set listOfpHandles [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"]
      }

    foreach portHnd $listOfpHandles {
        switch -exact $action_reqd {
        "run" {
                #### Fix CR 282062551, set duration mode "non_blocking" - 4.14.2011 #####
                set port_list [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"]
                foreach port $port_list {
                    set gen [::sth::sthCore::invoke ::stc::get $port -children-generator]
                    set duration_mode [::sth::sthCore::invoke ::stc::get $gen.GeneratorConfig -DurationMode]
                    if {($duration_mode != $::sth::Traffic::generatorMode($port)) && ($duration_mode == "SECONDS") && ![info exists userArray(duration)]} {
                        ::sth::sthCore::invoke ::stc::config $gen.GeneratorConfig -DurationMode $::sth::Traffic::generatorMode($port)
                    }
                }
                #### end
                    
                # not clear_stats
                set ::sth::Traffic::isClear 0
                    
                if {$portHnd == "all"} {
                    if {[catch {::sth::sthCore::invoke stc::get $ProjHnd "-children-port"} listOfpHandles]} {
                        ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting ports: $listOfpHandles" {}
                        return -code 1 -errorcode -1 $listOfpHandles;
                    }
                    # US32951- TrafficStartMode -Controls how the ports start sending traffic.
                    set trafficOpt [::sth::sthCore::invoke stc::get $ProjHnd "-children-trafficoptions"]
                    if {[info exists userArray(traffic_start_mode)] && [string match -nocase "async" $userArray(traffic_start_mode)]} {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "asynchronous"
                    } else {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "synchronous"
                    }
                } else {
                    # US32951- TrafficStartMode -Controls how the ports start sending traffic.
                    set trafficOpt [::sth::sthCore::invoke stc::get $ProjHnd "-children-trafficoptions"]
                    if {[info exists userArray(traffic_start_mode)] && [string match -nocase "sync" $userArray(traffic_start_mode)]} {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "synchronous"
                    } else {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "asynchronous"
                    }
                }
                    
                if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
                    ::sth::sthCore::processError trafficControlKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $applyStatus" {}
                    return -code 1 -errorcode -1 $applyStatus;
                }
                    
                # A boolen flag indicating starting the specified streamblock(controlStreamblock = 1)
                # or all the streamblocks on the port (controlStreamblock = 0)
                set controlStreamblock 0
                if {[string match -nocase "streamblock*" $portHnd]} {
                    set controlStreamblock 1
                }
                    
                #Need to get the below from traffic_config
                if {[info exists ::sth::Traffic::arrayPortHnd]} {
                    if {$controlStreamblock == 0} {
                        ##### get all the streamblocks in the traffic generator #####
                        set Generatorlist {}
                        set Analyzerlist {}
                        foreach portHnd $listOfpHandles {
                            if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-Analyzer"} analyzerhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting analyzer handle: $analyzerhndl" {}
                                return -code 1 -errorcode -1 $analyzerhndl;
                            }
                            if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-generator"} generatorhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                                return -code 1 -errorcode -1 $generatorhndl;
                            } 
                            lappend Analyzerlist $analyzerhndl
                            lappend Generatorlist $generatorhndl
                        }
                        
                        if {[catch {::sth::sthCore::invoke stc::perform analyzerstart -AnalyzerList $Analyzerlist} configStatus]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while starting traffic on Analyer(receiving): $configStatus" {}
                            return -code 1 -errorcode -1 $configStatus;
                        }
                    } else {
                        ##### get the port handle on which the specified streamblock was created (added by xiaozhi)######
                        set streamList $listOfpHandles
                        unset listOfpHandles
                        set listOfpHandles ""
                        foreach stream $streamList {
                            if {[catch {set portHandle [::sth::sthCore::invoke stc::get $stream -parent]} err]} {
                                ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
                                return -code error $trafficControlKeyedList
                            }
                            if {[lsearch -exact $listOfpHandles $portHandle] < 0} {
                                lappend listOfpHandles $portHandle
                            }
                        }
                        #####end
                    }
                        
                    variable ::sth::Session::PORTLEVELARPSENDREQUEST
                    variable ::sth::Session::PORTLEVELARPDONE
                    foreach portHnd $listOfpHandles {
                        if {$::sth::Session::PORTLEVELARPSENDREQUEST($portHnd) > 0 && $::sth::Session::PORTLEVELARPDONE($portHnd) == 0} {
                            ########## ARP all hosts except PPPoX hosts ############
                            set hosts [::sth::sthCore::invoke ::stc::get $portHnd -affiliationport-Sources]
                            set hostList ""
                            set ripRouterList ""
                            set portIndex [::sth::sthCore::getObjectIndex $portHnd]
                                
                                #special case for MVPN
                                while { [set mpvnIndex [lsearch $hosts mvpngencustportparams*]] > -1} {
                                    set hosts [lreplace $hosts $mpvnIndex $mpvnIndex]
                                }
                                while { [set mpvnIndex [lsearch $hostList mvpngencoreportparams*]] > -1} {
                                    set hosts [lreplace $hosts $mpvnIndex $mpvnIndex]
                                }
                                #end special case for MVPN

                                foreach host $hosts {
                                    set hostIndex [::sth::sthCore::getObjectIndex $host]
                                    set pppoeClients [::sth::sthCore::invoke ::stc::get $host -children-PppoeClientBlockConfig]
                                    set pppoeServers [::sth::sthCore::invoke ::stc::get $host -children-PppoeServerBlockConfig]
                    

                                    #special case for rip
                                    set ripRouterCfgList [::sth::sthCore::invoke stc::get $host -children-riprouterconfig]
                                    if {$ripRouterCfgList != ""} {
                                        lappend ripRouterList $host
                                    }   
                                    #end special case for rip
                    
                                    if {[llength $pppoeClients] == 0 && [llength $pppoeServers] == 0 && ![regexp -nocase {^vpn} $host]
                                        && $hostIndex != $portIndex} {
                                        lappend hostList $host
                                    }
                                    incr hostIndex
                                }

                                if {$userArray(enable_arp)} {
                                    #special case for rip
                                    if {[llength $ripRouterList] > 0} {
                                        if {[catch {::sth::sthCore::invoke ::stc::perform ArpNdStart -HandleList $ripRouterList} errMsg]} {
                                            ::sth::sthCore::processError trafficControlKeyedList "stc::perform ArpNdStart Failed: $ripRouterList $errMsg " {}
                                            return -code error $errMsg
                                        }
                                    }
                                    #end special case for rip

                                    if { [llength $hostList] > 0} {
                                        if {[catch {::sth::sthCore::invoke ::stc::perform ArpNdStart -HandleList $hostList} errMsg]} {
                                          ::sth::sthCore::processError trafficControlKeyedList "stc::perform ArpNdStart Failed: $hostList $errMsg" {}
                                          return -code error $errMsg
                                        }
                                    }
                                    
                                    ########## ARP all stream blocks #################
                                    set streamblocks [::sth::sthCore::invoke ::stc::get $portHnd -children-streamblock]
                                    if { [llength $streamblocks] > 0} {
                                        if {[catch {::sth::sthCore::invoke ::stc::perform ArpNdStart -HandleList $streamblocks} errMsg]} {
                                            ::sth::sthCore::processError trafficControlKeyedList "stc::perform ArpNdStart Failed:$streamblocks $errMsg " {}
                                            return -code error $errMsg
                                        }
                                    }

                                    ::sth::sthCore::log debug "::stc::perform ArpNdStart -HandleList $portHnd"
                                }
                                
                                set ::sth::Session::PORTLEVELARPDONE($portHnd) 1
                            }
                    }
                        
                    if {$controlStreamblock == 0} {
                        #### start all the streamblocks in the traffic generator ####
                        if {[catch {::sth::sthCore::invoke stc::perform generatorstart -GeneratorList $Generatorlist} configStatus]} {
                            ::sth::sthCore::processError trafficControlKeyedList "stc::perform Failed: Error while starting traffic on Generator(transmitting): $configStatus" {}
                            return -code 1 -errorcode -1 $configStatus;
                        }
                    } else {
                        #### start the specified streamblocks (xiaozhi, 6/15/09) ####
                        
                        # traffic for duration time
                        if {[info exist userArray(duration)] && [info exists userArray(port_handle)] } {
                            #only enable the $streamlist, make others disable
                            ::sth::Traffic::processOnlyEnableStreamblock $streamList 0
                            #get generator
                            foreach port $listOfpHandles {
                                if {[catch {set generator [::sth::sthCore::invoke stc::get $port -children-generator]} err]} {
                                    ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
                                    return -code error $trafficControlKeyedList
                                }
                                lappend Generatorlist $generator
                            }
                           
                            if {[catch {::sth::sthCore::invoke stc::perform generatorstart -GeneratorList $Generatorlist} configStatus]} {
                                ::sth::sthCore::processError trafficControlKeyedList "stc::perform Failed: Error while starting traffic on Generator(transmitting): $configStatus" {}
                                return -code 1 -errorcode -1 $configStatus;
                            }
                            
                            #sleep before changing back the active status of streamblock
                            ::sth::sthCore::invoke "stc::sleep $userArray(duration)"

                            ## there is no need to process elapsed time if duration is configured.
                            
                            #make all the streamblocks are enable
                            ::sth::Traffic::processOnlyEnableStreamblock $streamList 1
                            
                        } else {
                            if {[catch {::sth::sthCore::invoke stc::perform StreamBlockStart -StreamBlockList $streamList} configStatus]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while starting traffic on $portHnd: $configStatus" {}
                                return -code error $trafficControlKeyedList
                            }
                            if {[info exist userArray(duration)]} {
                                ::sth::sthCore::invoke "stc::sleep $userArray(duration)"
                                if {[catch {::sth::sthCore::invoke stc::perform streamblockstop -StreamBlockList $streamList} configStatus]} {
                                    ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while stopping traffic on $portHnd: $configStatus" {}
                                    return -code error $trafficControlKeyedList
                                }
                            }
                        }
                    }       
                } else {
                    ::sth::sthCore::processError trafficControlKeyedList "no streams under port $portHnd" {}
                    return $::sth::sthCore::FAILURE
                }
                    
                set sth::Traffic::isEOTResults 0
                set EOTResultsFileNameCurrent 0
                if {[info exist userArray(duration)]} {
                   
                    set sth::Traffic::isEOTResults 1
                }
                return $::sth::sthCore::SUCCESS;
        }
        "stop" {
                # not clear_stats
                if {$::sth::Traffic::isEOTResults && $::sth::Traffic::isClear} {
                    set ::sth::Traffic::isClear 1
                } else {
                    set ::sth::Traffic::isClear 0
                }

                if {$portHnd != "all"} {
                    # US32951- TrafficStartMode -Controls how the ports start sending traffic.
                    set trafficOpt [::sth::sthCore::invoke stc::get $ProjHnd "-children-trafficoptions"]
                    if {[info exists userArray(traffic_start_mode)] && [string match -nocase "sync" $userArray(traffic_start_mode)]} {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "synchronous"
                    } else {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "asynchronous"
                    }
                }

                if {$portHnd == "all"} {
                    #Need to check if we need to change the traffic options for stop to synchronous
                    if {[catch {::sth::sthCore::invoke stc::get $ProjHnd "-children-port"} listOfpHandles]} {
                        ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting port handles: $listOfpHandles" {}
                        return -code 1 -errorcode -1 $listOfpHandles;
                    }
                    
                    # US32951- TrafficStartMode -Controls how the ports start sending traffic.
                    set trafficOpt [::sth::sthCore::invoke stc::get $ProjHnd "-children-trafficoptions"]
                    if {[info exists userArray(traffic_start_mode)] && [string match -nocase "async" $userArray(traffic_start_mode)]} {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "asynchronous"
                    } else {
                        ::sth::sthCore::invoke stc::config $trafficOpt TrafficStartMode "synchronous"
                    }

                    set Generatorlist {}
                    set Analyzerlist {}
                    foreach portHnd $listOfpHandles {
                        if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-Analyzer"} analyzerhndl]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting analyzer handle: $analyzerhndl" {}
                            return -code 1 -errorcode -1 $analyzerhndl;
                        }
                        if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-generator"} generatorhndl]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                            return -code 1 -errorcode -1 $generatorhndl;
                        } 
                        lappend Analyzerlist $analyzerhndl
                        lappend Generatorlist $generatorhndl
                    }
                    
                    if {$::sth::Traffic::processElapsedTime} {
                        ::sth::Traffic::getPortTrafficTxFrameRate $listOfpHandles
                    }
            
                    if {[catch {::sth::sthCore::invoke stc::perform generatorstop -GeneratorList $Generatorlist} configStatus]} {
                        ::sth::sthCore::processError trafficControlKeyedList "stc::perform Failed: Error while stopping on Generator(transmitting): $configStatus" {}
                        return -code 1 -errorcode -1 $configStatus; 
                    }
                    
                    ::sth::sthCore::invoke "stc::sleep 3"
                    if {[string length $::sth::sthCore::custom_path]} {
                        set ::sth::Traffic::hltDir $::sth::sthCore::custom_path
                    } else {
                        if {[file isdirectory [file join [pwd] [info script]]]} {
                            set ::sth::Traffic::hltDir [file join [pwd] [info script]]
                        } else {
                            set ::sth::Traffic::hltDir [file dirname [file join [pwd] [info script]]]
                        }
                    }
                    #if two user scripts run in same dir, it will conflict with the same db file name "eotResultsHltApi.db"
                    #add clock value %hour%minus%second to file name to avoid different user scripts use a same db file name
                    if {$::sth::Traffic::db_file == 1} {
                        if {$::sth::Traffic::EOTResultsFileName == ""} {
                            if {[string length $::sth::sthCore::custom_path]} {
                                set ::sth::Traffic::hltDir $::sth::sthCore::custom_path
                            } else {
                                if {[file isdirectory [file join [pwd] [info script]]]} {
                                    set ::sth::Traffic::hltDir [file join [pwd] [info script]]
                                } else {
                                    set ::sth::Traffic::hltDir [file dirname [file join [pwd] [info script]]]
                                }
                            }
                            set ::sth::Traffic::EOTResultsFileName [concat "eotResultsHltApi" [clock format [clock seconds] -format %H%M%S] ".db"]
                            set ::sth::Traffic::EOTResultsFileName [join $::sth::Traffic::EOTResultsFileName ""]
                            
                        }
                        #rxu
                        set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
                        while {[file exists $hltfile]} {
                            file delete $hltfile
                            set ::sth::Traffic::EOTResultsFileName [concat "eotResultsHltApi" [clock format [clock seconds] -format %H%M%S] ".db"]
                            set ::sth::Traffic::EOTResultsFileName [join $::sth::Traffic::EOTResultsFileName ""]
                            set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]            
                        }
                        ::sth::sthCore::invoke ::stc::perform SaveResult -SaveDetailedResults true -SaveToDatabase true -OverwriteIfExist true -DatabaseConnectionString [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
                        set sth::Traffic::EOTResultsFileNameCurrent 1
                    }  else {
                        set sth::Traffic::EOTResultsFileNameCurrent 0
                    }
                    set sth::Traffic::isEOTResults 1
                    return $::sth::sthCore::SUCCESS;

                } else {
                    # $portHnd != "all"
                                        
                        #### stop the specified streamblock (xiaozhi) ####
                    if {[string match -nocase "streamblock*" $portHnd]} {
                        
                        if {$::sth::Traffic::processElapsedTime} {
                            set portHandleList ""
                            foreach handle $listOfpHandles {
                                if {[catch {set portHandle [::sth::sthCore::invoke stc::get $handle -parent]} err]} {
                                    ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
                                    return -code error $trafficControlKeyedList
                                }
                                if {[lsearch $portHandleList $portHandle] < 0} {
                                   set portHandleList "$portHandle $portHandleList" 
                                }
                            }
                            ::sth::Traffic::getPortTrafficTxFrameRate $portHandleList
                        }
                        if {[catch {::sth::sthCore::invoke stc::perform StreamBlockStop -StreamBlockList $listOfpHandles} configStatus]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while starting traffic on $portHnd: $configStatus" {}
                            return -code 1 -errorcode -1 $configStatus;
                        }                        
                        if {[catch {::sth::sthCore::StreamblockWaitForStop $listOfpHandles -1} configStatus]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while waiting for traffic to stop on $listOfpHandles: $configStatus" {}
                            return -code error $trafficControlKeyedList
                        }                        
                    } else {
                        #### stop all the streambloks on the port ####
                        set Generatorlist {}
                        set Analyzerlist {}
                        # retrieve the running tx_frame_rate of the traffic 
                        if {$::sth::Traffic::processElapsedTime} {
                            ::sth::Traffic::getPortTrafficTxFrameRate $listOfpHandles
                        }
                        foreach portHnd $listOfpHandles {
                            if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-Analyzer"} analyzerhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting analyzer handle: $analyzerhndl" {}
                                return -code 1 -errorcode -1 $analyzerhndl;
                            }
                            if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-generator"} generatorhndl]} {
                                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                                return -code 1 -errorcode -1 $generatorhndl;
                            } 
                            lappend Analyzerlist $analyzerhndl
                            lappend Generatorlist $generatorhndl
                        }
            
                        if {[catch {::sth::sthCore::invoke stc::perform generatorstop -GeneratorList $Generatorlist} configStatus]} {
                            ::sth::sthCore::processError trafficControlKeyedList "stc::perform Failed: Error while stopping on Generator(transmitting): $configStatus" {}
                            return -code 1 -errorcode -1 $configStatus; 
                        }
                        if {[catch {::sth::sthCore::invoke stc::perform GeneratorWaitForStop -GeneratorList $Generatorlist -WaitTimeout 60} configStatus]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while waiting for traffic to stop on $portHnd: $configStatus" {}
                            return -code error $trafficControlKeyedList
                        }                        
                    }
#                    ::sth::sthCore::invoke "stc::sleep 3"
                    #if two user scripts run in same dir, it will conflict with the same db file name "eotResultsHltApi.db"
                    #add clock value %hour%minus%second to file name to avoid different user scripts use a same db file name
                    if {$::sth::Traffic::db_file == 1} {
                        if {$::sth::Traffic::EOTResultsFileName == ""} {
                            if {[string length $::sth::sthCore::custom_path]} {
                                set ::sth::Traffic::hltDir $::sth::sthCore::custom_path
                            } else {
                                if {[file isdirectory [file join [pwd] [info script]]]} {
                                    set ::sth::Traffic::hltDir [file join [pwd] [info script]]
                                } else {
                                    set ::sth::Traffic::hltDir [file dirname [file join [pwd] [info script]]]
                                }
                            }
                            set ::sth::Traffic::EOTResultsFileName [concat "eotResultsHltApi" [clock format [clock seconds] -format %H%M%S] ".db"]
                            set ::sth::Traffic::EOTResultsFileName [join $::sth::Traffic::EOTResultsFileName ""]
                        }
                        set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
                        while {[file exists $hltfile]} {
                            file delete $hltfile
                            set ::sth::Traffic::EOTResultsFileName [concat "eotResultsHltApi" [clock format [clock seconds] -format %H%M%S] ".db"]
                            set ::sth::Traffic::EOTResultsFileName [join $::sth::Traffic::EOTResultsFileName ""]
                            set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]            
                        }
                        ::sth::sthCore::invoke ::stc::perform SaveResult -SaveDetailedResults true -SaveToDatabase true -OverwriteIfExist true -DatabaseConnectionString [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
                        set sth::Traffic::EOTResultsFileNameCurrent 1
                    } else {
                        set sth::Traffic::EOTResultsFileNameCurrent 0
                    }
                    set sth::Traffic::isEOTResults 1
                    return $::sth::sthCore::SUCCESS;
                }
            }
        "poll" {
                set trafficControlKeyedList {}
                if {$portHnd == "all"} {
                    if {[catch {::sth::sthCore::invoke stc::get $ProjHnd "-children-port"} listOfpHandles]} {
                        ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting port handles: $listOfpHandles" {}
                        return -code 1 -errorcode -1 $listOfpHandles;
                    }
                }
                keylset trafficControlKeyedList stopped 1
                foreach portHnd $listOfpHandles {
                   if {[catch {::sth::sthCore::invoke stc::get $portHnd "-children-generator"} generatorhndl]} {
                            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting generator handle: $generatorhndl" {}
                            return -code 1 -errorcode -1 $generatorhndl;
                        }
                    set status [::sth::sthCore::invoke stc::get $generatorhndl -State]
                    if {$status != "STOPPED"} {
                    keylset trafficControlKeyedList stopped 0
                    }
                    keylset trafficControlKeyedList $portHnd-$generatorhndl $status
                }
                return $::sth::sthCore::SUCCESS;
            }
        "clear_stats" {
                # clear_stats
                set ::sth::Traffic::isClear 1
                #us34052 stats not getting cleared to '0' while using HLTAPI 4.62 GA
                # retrieve real-time stat  instead of EOT result after clear_stats
                set ::sth::Traffic::EOTResultsFileNameCurrent 0           
                if {$listOfpHandles == "all"} {
                    set listOfpHandles [::sth::sthCore::invoke stc::get $ProjHnd "-children-port"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAll -PortList $listOfpHandles} configStatus]} {
                    ::sth::sthCore::processError trafficControlKeyedList "stc::perform Failed: Error while clearinf results: $configStatus" {}
                    return -code 1 -errorcode -1 $configStatus;
                }
                    
                foreach hnd $listOfpHandles {
                    if {[info exists ::sth::Traffic::curStreamElapTime($hnd)]} {
                        set ::sth::Traffic::curStreamElapTime($hnd) 0
                    }
                    if {[info exists ::sth::Traffic::pastStreamElapTime($hnd)]} {
                        set ::sth::Traffic::pastStreamElapTime($hnd) 0
                    }
                }
                break
        }
        "destroy" {
                set streamblockGet [sth::get_handles -type streamblock]
                set streamblockIdList [keylget streamblockGet handles]
                foreach streamblockID $streamblockIdList {
                    if {[catch {::sth::sthCore::invoke stc::delete $streamblockID} deleteStatus ]} {
                        ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while deleting stream block ID: $deleteStatus" {}
                        return -code 1 -errorcode -1 $deleteStatus;
                    }
                }
                set errMsg "";
                if {[catch {array unset ::sth::Traffic::arraystreamHnd} errMsg]} {
                    ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while cleaning streamHndArray: $errMsg" {}
                    return -code 1 -errorcode -1 $errMsg;
                }
            
                # reset the arrayPortHnd here.
                set portHndlList [array names ::sth::Traffic::arrayPortHnd];
                foreach portHndl $portHndlList {
                    set ::sth::Traffic::arrayPortHnd($portHndl) {};
                }
                return $::sth::sthCore::SUCCESS;
        }
        "reset" {
        # 1. clear the stats
        # 2. delete the streams
                set streamblockGet [sth::get_handles -type streamblock]
                set listOfStreams [keylget streamblockGet handles]
                if {$listOfpHandles == "all"} {
                    set listOfpHandles [concat [::sth::sthCore::invoke stc::get $ProjHnd "-children-port"] listOfStreams]
                }
                foreach hnd $listOfpHandles {
                    if {[info exists ::sth::Traffic::curStreamElapTime($hnd)]} {
                        set ::sth::Traffic::curStreamElapTime($hnd) 0
                    }
                    if {[info exists ::sth::Traffic::pastStreamElapTime($hnd)]} {
                        set ::sth::Traffic::pastStreamElapTime($hnd) 0
                    }
                }
                if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAll -Project $ProjHnd} configStatus]} {
                    ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while cleaning streamHndArray: $configStatus" {}
                    return -code 1 -errorcode -1 $configStatus;
                }
                ::sth::sthCore::invoke "stc::sleep 5"
                
                foreach streamBlockId $listOfStreams {
                    if {[catch {::sth::sthCore::invoke stc::delete $streamBlockId} deleteStatus]} {
                        ::sth::sthCore::processError trafficControlKeyedList "stc::delete Failed: Internal Command Error while deleting stream block Id's: $deleteStatus" {}
                        return -code 1 -errorcode -1 $deleteStatus;
                    }
                }
                break
            }
        }
    }
    return $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::start_test_imp { args } {   
    set startTestKeyedList ""
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {};
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::GBLHNDMAP
    variable sortedSwitchPriorityList {};
    set wait 1
    set ::sth::Traffic::isClear 1
    
    set sth::Traffic::isEOTResults 0
    set EOTResultsFileNameCurrent 0
    
    ::sth::sthCore::log debug "{Calling sth::start_test}"
    ::sth::sthCore::log info "{Generating traffic table}"
     
    if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args \
                                  ::sth::Traffic:: \
                                  start_test \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError startTestKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $startTestKeyedList
     }
    
    if {[info exists userArgsArray(duration)]} {
        set duration $userArgsArray(duration)
    }
    if {[info exists userArgsArray(wait)]} {
        set wait $userArgsArray(wait)
    } 
    if {[info exists userArgsArray(clear_stats)]} {
        set ::sth::Traffic::isClear $userArgsArray(clear_stats)
    } 

    set port_list [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"]
    set unwait_Generatorlist {}
    set wait_Generatorlist {}
    set Analyzerlist {}

    foreach port $port_list {
        set  duration_mode [::sth::sthCore::invoke ::stc::get $port.generator.generatorconfig -DurationMode]
        set gen [::sth::sthCore::invoke ::stc::get $port -children-generator]
        set ana [::sth::sthCore::invoke ::stc::get $port -children-analyzer]
        lappend Analyzerlist $ana
        if {[info exists userArgsArray(duration)]} {
            if {[string match -nocase "bursts" $duration_mode]} {
                ::sth::sthCore::log info "LOG $port was burst mode previously, will not change its mode here"
            } else {
                sth::sthCore::invoke stc::config $port.generator.generatorconfig -duration $duration -DurationMode seconds
                set duration_mode "seconds"
            }
        } else {
            if {[string match -nocase "seconds" $duration_mode]} {
                sth::sthCore::invoke stc::config $port.generator.generatorconfig -DurationMode continuous
                set duration_mode "continuous"
            }
        }
    
        set tmpWait 0
        if {[string match -nocase "continuous" $duration_mode]} {
            set tmpWait 0
            lappend unwait_Generatorlist $gen
        } elseif {[string match -nocase "bursts" $duration_mode]} {
            set tmpWait 1
            lappend wait_Generatorlist $gen
        } else {
            if {$wait == 0} {
                lappend unwait_Generatorlist $gen
            } else {
                set tmpWait 1
                lappend wait_Generatorlist $gen
            }
        }
        ::sth::sthCore::log info "For $port the Durationmode mode is $duration_mode. Wait flag is $wait"
    }

    ::sth::sthCore::doStcApply
    
    # clear_stats
    if {$::sth::Traffic::isClear} {
        ::sth::sthCore::invoke stc::perform resultclearalltraffic -portlist $port_list
    }
    
    # start the specified streamblock or a stack of streamblocks by specifying the stream_handle
    if {[info exist userArgsArray(stream_handle)]} {
        set streamHandleList $userArgsArray(stream_handle)
        foreach stream $streamHandleList {
        lappend listOfsTreams $stream
        }
        ::sth::sthCore::log info "Starting streamblock $listOfsTreams"
        ::sth::sthCore::invoke stc::perform streamblockstart -streamblockList $listOfsTreams
        
        if {[info exists userArgsArray(duration)]} {
            ::sth::sthCore::invoke stc::sleep $duration
            ::sth::sthCore::invoke stc::perform streamblockstop -streamblockList $listOfsTreams
            ::sth::sthCore::log info "Stopping traffic"
        }
    } else {
        # start all analyzers and generators 
        ::sth::sthCore::log info "Start all analyzers and generators"
        ::sth::sthCore::invoke stc::perform analyzerstart -analyzerlist $Analyzerlist
        ::sth::sthCore::invoke stc::perform generatorstart -generatorlist "$wait_Generatorlist $unwait_Generatorlist"
        ::sth::sthCore::invoke stc::sleep 4
    }
    
    # keep checking status...if wait is provided # can't just sleep for the duration ..keep polling for state
    if {$wait && $wait_Generatorlist != ""} {
        set tmp_gens ""
        set dur 20
        if {[info exists userArgsArray(duration)]} {
            set dur $duration
        }
        for {set i 0} {$i<=$dur} {incr i} {
            ::sth::sthCore::invoke stc::sleep 1
            set cmdResult 0
            foreach genlist $wait_Generatorlist {
                set genstate  "[sth::sthCore::invoke stc::get $genlist -state]"
                if {[string match -nocase "stopped" $genstate]} {
                    continue
                }
                lappend tmp_gens $genlist
            }
            set wait_Generatorlist $tmp_gens
            set tmp_gens ""
            if { $wait_Generatorlist == ""&& [info exist userArgsArray(stream_handle)]} {
                set cmdResult 1
                break
            }
            if { $wait_Generatorlist == "" && ![info exist userArgsArray(stream_handle)]} {
                set cmdResult 1
                break
            }
        }
        #if the burst run duration is greater than specified argument passed duration generator handles wont become empty.
        if { $wait_Generatorlist != "" && [string match -nocase "bursts" $duration_mode]} {
            set cmdResult 1             
        }
        if {$cmdResult == 0} {  
            set startTestKeyedList [::sth::sthCore::updateReturnInfo $startTestKeyedList status 0]
            ::sth::sthCore::processError startTestKeyedList "{start_test failed: $startTestKeyedList}"
            return $startTestKeyedList
        }
    }
    ::sth::sthCore::invoke stc::sleep 5                                 ;# sleep ...let packets get through test
    set startTestKeyedList [::sth::sthCore::updateReturnInfo $startTestKeyedList status 1]
    return $startTestKeyedList      
}

proc ::sth::Traffic::processTraffic_configlatency_bins {} {

    upvar 1 userArgsArray userArray;
    upvar trafficControlKeyedList trafficControlKeyedList;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    if {[info exists userArray(latency_values)]} {
    return $::sth::sthCore::SUCCESS;
    } else {
    return $::sth::sthCore::FAILURE;
    }
}
    
proc ::sth::Traffic::processTraffic_configlatency_values {} {

    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::GBLHNDMAP
    upvar trafficControlKeyedList trafficControlKeyedList;
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);
    set MaxStcList 15;
    set latencyValueList $userArray(latency_values);
    set newlatencyvaluelist {};
    set latencyValueLen [llength $latencyValueList]
    if {$latencyValueLen < $MaxStcList} {
        foreach val $latencyValueList {
			#Fractional values are not supporting for NANOSECONDS; so multiplying with 100; Remaining all supports.
			if {(([string equal $userArray(bucket_size_unit) ten_nanoseconds]) && ([regexp {\.} $val match]))} {
				lappend newlatencyvaluelist [expr round($val * 100)]
			} else {
				lappend newlatencyvaluelist $val
			}
        }
        set listlength [llength $newlatencyvaluelist]
        set lastplusonelength [expr $listlength + 1]
		# Values supporting Limit must be within -536870912 and 3758096383 nano seconds.3758096.383 Micro seconds. 3758.096383 Milli second. 3.758096383 seconds.
		if {([string equal $userArray(bucket_size_unit) ten_nanoseconds]) || ([string equal $userArray(bucket_size_unit) microseconds])} {
			set MaxValue 65535;
		}
		if {([string equal $userArray(bucket_size_unit) milliseconds])} {
			set MaxValue 3742;
		}   
		if {([string equal $userArray(bucket_size_unit) seconds])} {
			set MaxValue 3;
		}   
        

        if {$listlength < $MaxStcList} {
            set newlatencyvaluelist [linsert  $newlatencyvaluelist $lastplusonelength $MaxValue]
            set newlength [llength $newlatencyvaluelist]
                
            if {$newlength < $MaxStcList} {
                set length [expr $newlength +1]
                for {set i $length} {$i <= $MaxStcList} {incr i 1} {
					if {([string equal $userArray(bucket_size_unit) seconds])} { 
							set MaxValue "[expr {$MaxValue+0.01}]"
						} else {
							incr MaxValue
						}   
						set  newlatencyvaluelist [linsert  $newlatencyvaluelist $i $MaxValue]
					}
            }
        }
    }
    
    if {[info exists userArray(latency_bins)]} {
    set latBinValue $userArray(latency_bins);
    } else {
        ::sth::sthCore::processError trafficControlKeyedList "Latency Bin Values are not defined and are required" {}
		return 0;
    }
    
    if {[info exist userArray(port_handle)]} {
        if {[string equal $userArray(port_handle) "all"]} {
            if {[catch {::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"} porthandlelistnew]} {
                ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting ports: $porthandlelistnew" {}
                return -code 1 -errorcode -1 $porthandlelistnew;
            } 
        } else {
                set porthandlelistnew $userArray(port_handle)
        }
    } elseif {[info exist userArray(stream_handle)]} {
        set streamList $userArray(stream_handle)
        set porthandlelistnew ""
        foreach steam $streamList {
            if {[catch {set portHandle [::sth::sthCore::invoke stc::get $steam -parent]} err]} {
                ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
                return -code error $trafficControlKeyedList
            }
            if {[lsearch -exact $porthandlelistnew $portHandle] < 0} {
                lappend porthandlelistnew $portHandle
            }
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-ResultOptions"} resOptions]} {
    ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting result options: $resOptions" {}
    return -code 1 -errorcode -1 $resOptions;
    }
    if {[catch {::sth::sthCore::invoke stc::config $resOptions "-ResultViewMode HISTOGRAM"} configStatus]} {
        ::sth::sthCore::processError trafficControlKeyedList "stc::config Failed: Internal Command Error while configuring histogram: $configStatus" {}
        return -code 1 -errorcode -1 $configStatus;
    }
    
    set listOfports $porthandlelistnew
    set portCount [llength $listOfports]
    
    foreach currPort $listOfports {
        if {[catch {::sth::sthCore::invoke stc::get $currPort "-children-Analyzer"} analyzerCurrent]} {
            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting analyzer: $analyzerCurrent" {}
            return -code 1 -errorcode -1 $analyzerCurrent;
        }
        if {[catch {::sth::sthCore::invoke stc::get $analyzerCurrent "-children-AnalyzerConfig"} analyzerConfig]} {
            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting analyzerConfig: $analyzerConfig" {}
            return -code 1 -errorcode -1 $analyzerConfig;
        }
        set configlist "-HistogramMode LATENCY"
        if {[catch {::sth::sthCore::invoke stc::config $analyzerConfig $configlist} configStatus]} {
            ::sth::sthCore::processError trafficControlKeyedList "stc::config Failed: Internal Command Error while configuring histogram mode: $configStatus" {}
            return -code 1 -errorcode -1 $configStatus;
		}
        if {[catch {::sth::sthCore::invoke stc::get $analyzerConfig -children-latencyHistogram} histogram]} {
            ::sth::sthCore::processError trafficControlKeyedList "Internal Command Error while getting latencyHistogram: $histogram" {}
            return -code 1 -errorcode -1 $histogram;
        }
        if {[catch {::sth::sthCore::invoke stc::config $histogram "-ConfigMode CONFIG_LIMIT_MODE -LimitList {$newlatencyvaluelist} -BucketSizeUnit $userArray(bucket_size_unit) -Active TRUE"} configStatus]} {
			::sth::sthCore::processError trafficControlKeyedList "stc::config Failed: Internal Command Error while configuring histogram: $configStatus" {}
			return -code 1 -errorcode -1 $configStatus;
		}
    }
    set ::sth::Traffic::isLatencyConfig 1;
    # Apply
    if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
    ::sth::sthCore::processError trafficControlKeyedList "stc::config Failed: Unable to apply configuration for histograms: $applyStatus" {}
        return -code 1 -errorcode -1 $applyStatus;
    } 
    
                         
    return $::sth::sthCore::SUCCESS;
    
}


# get the frame rate both on port basis and streamblock basis
# by xiaozhi, liu
proc ::sth::Traffic::getPortTrafficTxFrameRate { portHandle } {
    #set txResultsData ""
    
    foreach handle $portHandle {
        if {[catch {::sth::sthCore::invoke stc::get $handle "-children-generator"} generatorhdl]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Generator children" {}
            return $::sth::sthCore::FAILURE
        }
        
        ## validate generator state, get the "running" rate
        if {[catch {set state [::sth::sthCore::invoke stc::get $generatorhdl "-state"]} err]} {
            ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        
        if {$state == "STOPPED"} {
            if {![info exists ::sth::Traffic::portTxEOTFrameRate($handle)]} {
                set ::sth::Traffic::portTxEOTFrameRate($handle) 0
            }
            return
        }
        
        if {[catch {set streamHandle [::sth::sthCore::invoke stc::get $handle "-children-streamblock"]} err]} {
            ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }  
        ## get generatorportresults to retrieve FrameRate
        if {[catch {::sth::sthCore::invoke stc::get $generatorhdl "-children-generatorportresults"} generatorResult]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting Generatorportresults children" {}
            return $::sth::sthCore::FAILURE
        }
        
        set txFrameRate ""
        set txFrameCount 0
        if {[llength $generatorResult] == 0} {
            set subscribeCommand "-Parent $::sth::sthCore::GBLHNDMAP(project) -ResultParent {$handle} \
                                -ConfigType Generator  \
                                -resulttype GeneratorPortResults \
                                -viewAttributeList {TotalFrameRate TotalFrameCount}"
            if {[catch {sth::sthCore::invoke "stc::subscribe $subscribeCommand"} txPortResultsData]} {
                ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::invoke subscribe Failed" {}
                return $::sth::sthCore::FAILURE
            }         
            
            set subscribeCommand "-Parent $::sth::sthCore::GBLHNDMAP(project) -ResultParent {$streamHandle} \
                                -ConfigType StreamBlock \
                                -resulttype TxStreamBlockResults \
                                -viewAttributeList {FrameRate FrameCount}"
            if {[catch {sth::sthCore::invoke "stc::subscribe $subscribeCommand"} txStreamResultsData]} {
                ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::invoke subscribe Failed" {}
                return $::sth::sthCore::FAILURE
            }

#            ::sth::sthCore::invoke stc::sleep 2
            if {[catch {::sth::sthCore::invoke stc::get $generatorhdl "-children-generatorportresults"} newGeneratorResult]} {
                ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting TxStreamResults children" {}
                return $::sth::sthCore::FAILURE
            }
            set newGeneratorResult [lindex $newGeneratorResult 0]
            if {[catch {set txFrameRate [::sth::sthCore::invoke stc::get $newGeneratorResult "-TotalFrameRate"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }                                  
            if {[catch {set txFrameCount [::sth::sthCore::invoke stc::get $newGeneratorResult "-TotalFrameCount"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
            set ::sth::Traffic::portTxEOTFrameRate($handle) $txFrameRate
            
            ::sth::Traffic::processUnSubscribeProjectLevelCounters $txPortResultsData
                                                   
        } else {
            set generatorResult [lindex $generatorResult 0]
            if {[catch {set txFrameRate [::sth::sthCore::invoke stc::get $generatorResult "-TotalFrameRate"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }                                                                                      
            if {[catch {set txFrameCount [::sth::sthCore::invoke stc::get $generatorResult "-TotalFrameCount"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
            set ::sth::Traffic::portTxEOTFrameRate($handle) $txFrameRate
        }
        
        # store the elapsed time on port level
        if {$txFrameRate != 0} {
            set elapsedTime [expr $txFrameCount/$txFrameRate]
        } else {
            set elapsedTime 0
        }
        
        if {[info exists ::sth::Traffic::curStreamElapTime($handle)]} {
            set ::sth::Traffic::pastStreamElapTime($handle) $::sth::Traffic::curStreamElapTime($handle)
        }
        set ::sth::Traffic::curStreamElapTime($handle) $elapsedTime 
        
        ### get the frame rate and elapsed time on streamblock basis
        if {[info exists txStreamResultsData]} {
            ::sth::Traffic::getStreamTxFrameRate $streamHandle $txStreamResultsData
        } else {
            ::sth::Traffic::getStreamTxFrameRate $streamHandle ""
        }
    }

}

# get the frame rate both on streamblock basis
# by xiaozhi, liu
proc ::sth::Traffic::getStreamTxFrameRate { handle {txResultsData ""}} {
    
    #set txResultsData ""
    
    foreach streamHandle $handle {
        ## validate stream states
        if {[catch {set state [::sth::sthCore::invoke stc::get $streamHandle "-RunningState"]} err]} {
            ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        if {$state == "STOPPED"} {
            if {![info exists ::sth::Traffic::streamTxEOTFrameRate($handle)]} {
                set ::sth::Traffic::streamTxEOTFrameRate($handle) 0
            }
            if {$txResultsData != ""} {
               ::sth::Traffic::processUnSubscribeProjectLevelCounters $txResultsData
            }
            return  
        }
        
        ## get txStreamResults to retrieve FrameRate
        if {[catch {::sth::sthCore::invoke stc::get $streamHandle "-children-TxStreamBlockResults"} txStreamResults]} {
            ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting TxStreamResults children" {}
            return $::sth::sthCore::FAILURE
        }
        
        set allFrameRate 0
        set allFrameCount 0
        if {[llength $txStreamResults] == 0 && $txResultsData != ""} {
            if {[catch {set totalPageCount [::sth::sthCore::invoke stc::get $txResultsData "-totalPageCount"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
            if {[catch {set currentPage [::sth::sthCore::invoke stc::get $txResultsData "-pageNumber"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
            while {$currentPage  < $totalPageCount} {
                set currentPage [expr $currentPage  + 1]
                if {[catch {::sth::sthCore::invoke stc::config $txResultsData pageNumber $currentPage} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
                if {[catch {::sth::sthCore::doStcApply} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
                    return $::sth::sthCore::FAILURE
        }
                if {[catch {::sth::sthCore::invoke stc::perform RefreshResultView -ResultDataSet $txResultsData -ExecuteSynchronous TRUE} err]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "stc::perform Failed: $err" {}
                    return $::sth::sthCore::FAILURE
        }
                
                if {[catch {::sth::sthCore::invoke stc::get $streamHandle "-children-TxStreamBlockResults"} txStreamResults]} {
                    ::sth::sthCore::processError trafficStatsKeyedList "Internal Command Error while getting TxStreamResults children" {}
                    return $::sth::sthCore::FAILURE
                }
                if {[llength $txStreamResults] != 0} {
                    break
                }
            }
        }
        
        foreach streamResult $txStreamResults {
            if {[catch {set frameRate [::sth::sthCore::invoke stc::get $streamResult "-FrameRate"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
            if {[catch {set frameCount [::sth::sthCore::invoke stc::get $streamResult "-FrameCount"]} err]} {
                ::sth::sthCore::processError trafficStatsKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
                
            set allFrameRate [expr $frameRate+$allFrameRate]
            set allFrameCount [expr $frameCount+$allFrameCount]
        }
       
        set ::sth::Traffic::streamTxEOTFrameRate($streamHandle) $allFrameRate
        
        if {$allFrameRate != 0} {
            set elapsedTime [expr $allFrameCount/$allFrameRate]
        } else {
            set elapsedTime 0
        }
        
        if {[info exists ::sth::Traffic::curStreamElapTime($streamHandle)]} {
            set ::sth::Traffic::pastStreamElapTime($streamHandle) $::sth::Traffic::curStreamElapTime($streamHandle)
        }
        set ::sth::Traffic::curStreamElapTime($streamHandle) $elapsedTime
    }
    if {$txResultsData != ""} {
       ::sth::Traffic::processUnSubscribeProjectLevelCounters $txResultsData
    }
}

# calculate the traffic elapsed time by dividing txFrameCount by txFrameRate
# by xiaozhi, liu
proc ::sth::Traffic::processTrafficTxElapsedTime { handle txFrameCount txFrameRate} {
    
    set elapsedTime 0
    if {[string match -nocase "port*" $handle]} {

        if {$::sth::Traffic::isEOTResults} {
            if {[info exists ::sth::Traffic::portTxEOTFrameRate($handle) ]} {
                set txFrameRate $::sth::Traffic::portTxEOTFrameRate($handle)  
            } else {
                ::sth::Traffic::getPortTrafficTxFrameRate $handle
                set txFrameRate $::sth::Traffic::portTxEOTFrameRate($handle)  
            }
        }
        
        if {$txFrameRate != 0} {
            set elapsedTime [expr $txFrameCount/$txFrameRate]
        }
        
        # elapsed from the last traffic connection
        if {$::sth::Traffic::isEOTResults == 0} {
            if {![info exists ::sth::Traffic::curStreamElapTime($handle)]} {
                set ::sth::Traffic::curStreamElapTime($handle) 0
            }
            set newElapsedTime [expr $elapsedTime - $::sth::Traffic::curStreamElapTime($handle)]
        } else {
            if {![info exists ::sth::Traffic::pastStreamElapTime($handle)]} {
                set ::sth::Traffic::pastStreamElapTime($handle) 0
            }
            set newElapsedTime [expr $elapsedTime - $::sth::Traffic::pastStreamElapTime($handle)]
        }
    } elseif {[string match -nocase "streamblock*" $handle]} {
        
        if {$::sth::Traffic::isEOTResults} {
            if {[info exists ::sth::Traffic::streamTxEOTFrameRate($handle)]} {
                set txFrameRate $::sth::Traffic::streamTxEOTFrameRate($handle)
            } else {
                ::sth::Traffic::getStreamTxFrameRate $handle
                set txFrameRate $::sth::Traffic::streamTxEOTFrameRate($handle)
            }
        }
        
        if {$txFrameRate != 0} {
            set elapsedTime [expr $txFrameCount/$txFrameRate]
        }
        # elapsed from the last streamblock connection
        if {$::sth::Traffic::isEOTResults == 0} {
            if {![info exists ::sth::Traffic::curStreamElapTime($handle)]} {
                set ::sth::Traffic::curStreamElapTime($handle) 0
            }
            set newElapsedTime [expr $elapsedTime - $::sth::Traffic::curStreamElapTime($handle)]
        } else {
            if {![info exists ::sth::Traffic::pastStreamElapTime($handle)]} {
                set ::sth::Traffic::pastStreamElapTime($handle) 0
            }
            set newElapsedTime [expr $elapsedTime - $::sth::Traffic::pastStreamElapTime($handle)]
        }
    }
    return $newElapsedTime
}


proc ::sth::Traffic::processOnlyEnableStreamblock {strBlkList all} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar userArgsArray userArray;
    set portList ""
    
    foreach strBlk $strBlkList {
        if {[catch {set port [::sth::sthCore::invoke stc::get $strBlk -parent]} err]} {
            ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
            return -code error $trafficControlKeyedList
        }
        if {[lsearch -exact $portList $port] < 0} {
            lappend portList $port
        }
    }
    
    foreach port $portList {
        if {[catch {set streamblocks [::sth::sthCore::invoke stc::get $port -children-streamblock]} err]} {
            ::sth::sthCore::processError trafficControlKeyedList "stc::get Failed: $err" {}
            return -code error $trafficControlKeyedList
        }
        foreach streamblock $streamblocks {
            if {$all == 0} {
                #only enable the strblk in the given streamblock list
                if {[lsearch -exact $strBlkList $streamblock] < 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $streamblock "-Active false"} err]} {
                        ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                        return $::sth::sthCore::FAILURE;
                    }
                } else {
                    if {[catch {::sth::sthCore::invoke stc::config $streamblock "-Active true"} err]} {
                        ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                        return $::sth::sthCore::FAILURE;
                    }
                }
            } else {
                if {[catch {::sth::sthCore::invoke stc::config $streamblock "-Active true"} err]} {
                        ::sth::sthCore::processError trafficStatsKeyedList "stc::config Failed: $err" {}
                        return $::sth::sthCore::FAILURE;
                }
            }
            
        }
    }
    
    if {[catch {::sth::sthCore::doStcApply} err]} {
        ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
        return $::sth::sthCore::FAILURE;
    }
}

proc ::sth::Traffic::getResults {} {
    
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    upvar userArgsArray userArgsArray;
    set properties ""

    if {[info exists userArgsArray(properties)]} {
        if {[regexp -nocase {all} $userArgsArray(mode)]} {
            #Ignore properties option for mode -all, and flag warning info.
            set properties ""
            ::sth::sthCore::log info "traffic_stats \"properties\" option INVALID for mode ALL"
            puts "[info] traffic_stats \"properties\" option INVALID for mode ALL"
        } else {
            set properties $userArgsArray(properties)
        }
    }

    #Subscribing to result object
    set resultDataSetHndList [sth::Traffic::subscribeTrafficObject $userArgsArray(mode) $properties]
    #Getting stats
    foreach resultDataSetHnd $resultDataSetHndList {
        sth::Traffic::getStats $resultDataSetHnd $properties
        #Un-Subscribing and deleting result objects
        sth::Traffic::unsubscribeTrafficObject $resultDataSetHnd
    }

    ##########################################
    #dropped_pkts updating by performing tx-rx, if result view mode is changed to Histogram
    if {($userArgsArray(mode) eq "streams") ||
        ($userArgsArray(mode) eq "all")} {
        if {$::sth::Traffic::isLatencyConfig} {
            set portList [::sth::Traffic::getPortList]
            foreach currPort $portList {
                set streamblockHndlList [::sth::sthCore::invoke stc::get $currPort -children-streamblock]
                foreach streamblkHndl $streamblockHndlList {
                    keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.total_pkts rx_count
                    keylget trafficStatsKeyedList $currPort.stream.$streamblkHndl.tx.total_pkts tx_count
                    if {[info exists rx_count] && [info exists tx_count]} {
                        keylset trafficStatsKeyedList $currPort.stream.$streamblkHndl.rx.dropped_pkts [expr $tx_count - $rx_count]
                        keylset trafficStatsKeyedList $streamblkHndl.rx.dropped_pkts [expr $tx_count - $rx_count]
                    }
                }
            }
        }
    }
  ##########################################
    
    keylset trafficStatsKeyedList status $::sth::sthCore::SUCCESS
    return $trafficStatsKeyedList
}

proc ::sth::Traffic::subscribeTrafficObject {mode properties} {
    upvar userArgsArray userArgsArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    set streamBlockList ""
    set resultDataSetHndList ""

    #Create differet result queries based on different modes
    switch -exact $mode { 
        streams {
            #get streamblock list 
            set streamBlockList [::sth::Traffic::getStreamblockList]
            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createStreamblockResultQuery $resultDataSet $streamBlockList $properties
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet
        }
        detailed_streams {
            #get streamblock list 
            set streamBlockList [::sth::Traffic::getStreamblockList]
            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createStreamResultQuery $resultDataSet $streamBlockList $properties
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::sleep 3
        }
        aggregate {
            #get port list 
            set portList [::sth::Traffic::getPortList]
            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createPortResultQuery $resultDataSet $portList $properties 
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            if {$::sth::Traffic::FilterType ne "" } {
                set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
                lappend resultDataSetHndList $resultDataSet
                sth::Traffic::createFilteredStreamResultQuery $resultDataSet $portList
                sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            }
            sth::sthCore::invoke stc::sleep 3
        }
        out_of_filter {
            #get port list 
            set portList [::sth::Traffic::getPortList]
            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createOofResultQuery $resultDataSet $portList $properties
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::sleep 3
        }
        all {
            #get port list  and streamblock list 
            set portList [::sth::Traffic::getPortList]
            if {[info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) ne ""} {
                set streamBlockList ""
                foreach port $portList {
                    set streamHandle [sth::sthCore::invoke "stc::get $port -children-streamblock"]
                    append streamBlockList " $streamHandle"
                }
            } elseif {[info exists userArgsArray(streams)] && $userArgsArray(streams) ne "" && $userArgsArray(streams) ne "all"} {
                set streamBlockList $userArgsArray(streams)
            } else {
                set streamBlockList ""
                foreach port $portList {
                    set streamHandle [sth::sthCore::invoke "stc::get $port -children-streamblock"]
                    append streamBlockList " $streamHandle"
                }
            }
            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createStreamblockResultQuery $resultDataSet $streamBlockList $properties
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet

            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createPortResultQuery $resultDataSet $portList $properties
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet
            
            set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
            lappend resultDataSetHndList $resultDataSet
            sth::Traffic::createOofResultQuery $resultDataSet $portList $properties
            sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet

            if {$::sth::Traffic::FilterType ne "" } {
                set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]
                lappend resultDataSetHndList $resultDataSet
                sth::Traffic::createFilteredStreamResultQuery $resultDataSet $portList
                sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
                sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet
            }
            sth::sthCore::invoke stc::sleep 3
        }
    }

    return $resultDataSetHndList
}

proc ::sth::Traffic::createPortResultQuery { resultDataSet portList properties } {

    ::sth::Traffic::createPortLevelResultQuery $resultDataSet $portList $properties tx Generator GeneratorPortResults 
    ::sth::Traffic::createPortLevelResultQuery $resultDataSet $portList $properties rx Analyzer AnalyzerPortResults 
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::createStreamblockResultQuery { resultDataSet streamBlockList properties } {

    ::sth::Traffic::createStreamblockLevelResultQuery $resultDataSet $streamBlockList $properties tx TxStreamBlockResults 
    ::sth::Traffic::createStreamblockLevelResultQuery $resultDataSet $streamBlockList $properties rx RxStreamBlockResults 
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::createStreamResultQuery { resultDataSet streamBlockList properties } {

    ::sth::Traffic::createStreamblockLevelResultQuery $resultDataSet $streamBlockList $properties tx TxStreamResults
    ::sth::Traffic::createStreamblockLevelResultQuery $resultDataSet $streamBlockList $properties rx RxStreamSummaryResults

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::createStreamblockLevelResultQuery { resultDataSet streamBlockList properties type object} {

    if {$properties ne ""} {
        #Tx/Rx Streamblock Result Query with properties
        set resultKeys [sth::Traffic::getTypeProperties $type $properties]
        set keys ""
        
        foreach item $resultKeys {
            set stcAttr [set ::sth::Traffic::traffic_stats_stream_[set type]_results_stcattr($item)]
            if {($stcAttr ne "hlt") && ($stcAttr ne "_none_")} {
                append keys " $object.$stcAttr"
            }
        }

        if {$keys ne ""} {
            sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$streamBlockList\} -ConfigClassId StreamBlock -ResultClassId $object -PropertyIdArray \{$keys\}"
        }
    } else {
        #Tx/Rx Streamblock Result Query without properties
        sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$streamBlockList\} -ConfigClassId StreamBlock -ResultClassId $object"
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::createPortLevelResultQuery { resultDataSet portList properties type classId object} {

    if {$properties ne ""} {
        #Tx/Rx Gen/Ana Result Query with properties
        set resultKeys [sth::Traffic::getTypeProperties $type $properties]
        set keys ""
        
        foreach item $resultKeys {
            set stcAttr [set ::sth::Traffic::traffic_stats_aggregate_[set type]_results_stcattr($item)]
            if {($stcAttr ne "hlt") && ($stcAttr ne "_none_")} {
                append keys " $object.$stcAttr"
            }
        }

        if {$keys ne ""} {
            sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$portList\} -ConfigClassId $classId -ResultClassId $object -PropertyIdArray \{$keys\}"
        }
    } else {
        #Tx/Rx Streamblock Result Query without properties
        sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$portList\} -ConfigClassId $classId -ResultClassId $object"
    }

    return $::sth::sthCore::SUCCESS
}


proc ::sth::Traffic::createOofResultQuery { resultDataSet portList properties } {

    set keys ""

    if {$properties eq ""} {
       set properties [array names ::sth::Traffic::traffic_stats_out_of_filter_results_stcattr]
    }
    foreach item $properties {
        set stcAttr [set ::sth::Traffic::traffic_stats_out_of_filter_results_stcattr($item)]
        if {$stcAttr ne "_none_"} {
            append keys " OverflowResults.$stcAttr"
        }
    }

    sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$portList\} -ConfigClassId Analyzer -ResultClassId OverflowResults -PropertyIdArray \{$keys\}"

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::createFilteredStreamResultQuery { resultDataSet portList} {
    
    foreach port $portList {
        sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList $port -ConfigClassId Analyzer -ResultClassId FilteredStreamResults"
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::getStats {resultDataSet properties} {
    upvar userArgsArray userArgsArray;
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    set prevSb ""
    set portHnd ""
    set ::sth::Traffic::sbTxIndex {}
    set ::sth::Traffic::sbRxIndex {}

    set totalPage [sth::sthCore::invoke stc::get $resultDataSet -TotalPageCount]
    if {$totalPage == 0} {
        incr totalPage 
    }
    
    #Getting mapping the native and hlt return keys/values
    for {set pageNumber 1} { $pageNumber <= $totalPage} {incr pageNumber} {
        
        if {$pageNumber > 1} {
            sth::sthCore::invoke stc::config $resultDataSet -pageNumber $pageNumber
            sth::sthCore::invoke stc::apply
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::sleep 2
        }

        set resultHndLists [sth::sthCore::invoke stc::get $resultDataSet -ResultHandleList]

        foreach resultHnd $resultHndLists {
            array set hnd [sth::sthCore::invoke stc::get $resultHnd]
            if {($prevSb ne $hnd(-parent)) || ($prevSb eq "")} {
                set portHnd [sth::sthCore::invoke stc::get $hnd(-parent) -parent]
            }
            if {[regexp -nocase "RxStreamBlockResults" $resultHnd]} {
                ::sth::Traffic::updateStreamblockLevelCounters [array get hnd] $properties rx $portHnd
            } elseif {[regexp -nocase "TxStreamBlockResults" $resultHnd]} {
                ::sth::Traffic::updateStreamblockLevelCounters [array get hnd] $properties tx $portHnd
            } elseif {[regexp -nocase "TxStreamResults" $resultHnd]} {
                set txIndex [::sth::Traffic::getStreamIndex $hnd(-parent) tx]
                ::sth::Traffic::updateStreamLevelCounters [array get hnd] $properties $txIndex tx $portHnd
            } elseif {[regexp -nocase "RxStreamSummaryResults" $resultHnd]} {
                set rxIndex [::sth::Traffic::getStreamIndex $hnd(-parent) rx]
                ::sth::Traffic::updateStreamLevelCounters [array get hnd] $properties $rxIndex rx $portHnd
            } elseif {[regexp -nocase "GeneratorPortResults" $resultHnd]} {
                ::sth::Traffic::updatePortLevelCounters [array get hnd] $properties tx $portHnd
            } elseif {[regexp -nocase "AnalyzerPortResults" $resultHnd]} {
                ::sth::Traffic::updatePortLevelCounters [array get hnd] $properties rx $portHnd
            } elseif {[regexp -nocase "OverflowResults" $resultHnd]} {
                ::sth::Traffic::updateOofCounters [array get hnd] $properties $portHnd
            } elseif {[regexp -nocase "FilteredStreamResults" $resultHnd]} {
                ::sth::Traffic::updateFilteredStreamCounters [array get hnd] $properties $portHnd
            }
            set prevSb $hnd(-parent)
        }
    }
    return $trafficStatsKeyedList
}

proc ::sth::Traffic::getStreamIndex {streamBlock type} {
    variable ::sth::Traffic::sbTxIndex
    variable ::sth::Traffic::sbRxIndex
    set retIndex 0

    if {$type eq "tx"} {
        keylget ::sth::Traffic::sbTxIndex $streamBlock index
        if {[info exists index]} {
            set retIndex $index
            keylset ::sth::Traffic::sbTxIndex $streamBlock [incr index]
        } else {
            keylset ::sth::Traffic::sbTxIndex $streamBlock 1
        }
    } elseif {$type eq "rx"} {
        keylget ::sth::Traffic::sbRxIndex $streamBlock index
        if {[info exists index]} {
            set retIndex $index
            keylset ::sth::Traffic::sbRxIndex $streamBlock [incr index]
        } else {
            keylset ::sth::Traffic::sbRxIndex $streamBlock 1
        }
    }
    
    return $retIndex
}

proc ::sth::Traffic::updatePortLevelCounters {resultVal properties type portHnd} {
    upvar userArgsArray userArgsArray;
    upvar trafficStatsKeyedList trafficStatsKeyedList;

    array set hnd $resultVal
    set key "$portHnd.aggregate"

    #GeneratorPortResults/AnalyzerPortResults - Getting mapping the native and hlt return keys/values
    set TableName ::sth::Traffic::traffic_stats_aggregate_$type\_results_stcattr
    if {$properties eq ""} {
        set hltOptionList [array names $TableName]
    } else {
        set hltOptionList [sth::Traffic::getTypeProperties $type $properties]
    }
    foreach hltName $hltOptionList {
        if {[info exists ::sth::Traffic::traffic_stats_aggregate_[set type]_results_stcattr($hltName)]} {
            set stcName [set ::sth::Traffic::traffic_stats_aggregate_[set type]_results_stcattr($hltName)]
            if {($stcName ne "_none_") && ($stcName ne "hlt")} {
                set stcValue $hnd(-$stcName)
                keylset trafficStatsKeyedList $key.$type.$hltName $stcValue
            } elseif {$stcName eq "hlt"} {
                keylset trafficStatsKeyedList $key.$type.$hltName "0"
            } elseif {$hltName eq "ip_pkts"} {
                keylset trafficStatsKeyedList $key.$type.$hltName "0"
            }
        }
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::updateStreamblockLevelCounters {resultVal properties type portHnd} {
    upvar userArgsArray userArgsArray;
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    set portHndFlag 0
    
    if {([info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) ne "") && ![info exists userArgsArray(streams)]} {
        set portHndFlag 1
    } 
    array set hnd $resultVal
    set streamblockHnd $hnd(-parent)
    set key "$streamblockHnd"
    if {$portHndFlag} {
        set key "$portHnd.stream.$streamblockHnd"
    }

    #RxStreamBlockResults - Getting mapping the native and hlt return keys/values
    set TableName ::sth::Traffic::traffic_stats_stream_$type\_results_stcattr
    if {$properties eq ""} {
        set hltOptionList [array names $TableName]
    } else {
        set hltOptionList [sth::Traffic::getTypeProperties $type $properties]
    }
    foreach hltName $hltOptionList {
        if {[info exists ::sth::Traffic::traffic_stats_stream_[set type]_results_stcattr($hltName)]} {
            set stcName [set ::sth::Traffic::traffic_stats_stream_[set type]_results_stcattr($hltName)]
            if {![regexp -nocase "Hist" $stcName]} {
                if {($stcName ne "_none_") && ($stcName ne "hlt")} {
                    set stcValue $hnd(-$stcName)
                    keylset trafficStatsKeyedList $key.$type.$hltName $stcValue
                } elseif {$stcName eq "hlt"} {
                    keylset trafficStatsKeyedList $key.$type.$hltName "0"
                }
            } elseif {[regexp -nocase "Hist" $stcName]} {
                #add latency counters
                if {$::sth::Traffic::isLatencyConfig == 1} {
                    if {[regexp total_pkts $hltName]} {
                        set hltName "total_pkts"
                    } elseif {[regexp pkt_frame_rate $hltName]} {
                        set hltName "pkt_frame_rate"
                    }
                    set binnumber [::sth::Traffic::processGetBinNumber $stcName]
                    set stcValue $hnd(-$stcName)
                    if {$type eq "rx"} {
                        keylset trafficStatsKeyedList $key.$type.latency_bin.$binnumber.$hltName "$stcValue"
                    }
                }
            }
        }
    }
    if {$portHndFlag == 0} {
        set key "$portHnd.stream.$streamblockHnd.$type"
        set stcvalue [keylget trafficStatsKeyedList $streamblockHnd.$type]
        keylset trafficStatsKeyedList $key "$stcvalue"
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::updateStreamLevelCounters {resultVal properties index type portHnd} {
    upvar userArgsArray userArgsArray;
    upvar trafficStatsKeyedList trafficStatsKeyedList;
    set portHndFlag 0

    if {([info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) ne "") && ![info exists userArgsArray(streams)]} {
        set portHndFlag 1
    } 

    array set hnd $resultVal
    set streamblockHnd $hnd(-parent)
    set key "$streamblockHnd"
    if {$portHndFlag} {
        set key "$portHnd.stream.$streamblockHnd"
    }
    #RxStreamSummaryResults - Getting mapping the native and hlt return keys/values
    set TableName ::sth::Traffic::traffic_stats_stream_$type\_results_stcattr
    if {$properties == ""} {
        set hltOptionList [array names $TableName]
    } else {
        set hltOptionList [sth::Traffic::getTypeProperties $type $properties]
    }
    foreach hltName $hltOptionList {
        if {[info exists ::sth::Traffic::traffic_stats_stream_[set type]_results_stcattr($hltName)]} {
            set stcName [set ::sth::Traffic::traffic_stats_stream_[set type]_results_stcattr($hltName)]
            if {![regexp -nocase "Hist" $stcName]} {
                if {($stcName ne "_none_") && ($stcName ne "hlt")} {
                    set stcValue $hnd(-$stcName)
                    keylset trafficStatsKeyedList $key.$type.$index.$hltName $stcValue
                } elseif {$stcName eq "hlt"} {
                    keylset trafficStatsKeyedList $key.$type.$index.$hltName "0"
                }
            }
        }
    }
    if {$portHndFlag == 0} {
        set key "$portHnd.stream.$streamblockHnd.$type"
        set stcvalue [keylget trafficStatsKeyedList $streamblockHnd.$type.$index]
        keylset trafficStatsKeyedList $key.$index "$stcvalue"
    }

    return $::sth::sthCore::SUCCESS
}


proc ::sth::Traffic::updateFilteredStreamCounters {resultVal properties portHnd} {
    upvar userArgsArray userArgsArray;
    upvar trafficStatsKeyedList trafficStatsKeyedList;

    set currPort $portHnd
    #FilteredStreamResults - Getting mapping the native and hlt return keys/values
    array set stcArray $resultVal;
    
    # TODO: this is a temporary fix for scale_mode 1. 'scale_mode 1' is in old fashion: 
    # only supports one filter in 'traffic_control -get' and maps both 'vlan_pri' and 'vlan_pri_inner'
    # to 'qos' in ::sth::Traffic::FilterType. 'scale_mode 0' has already supported multiple filters, 
    # please remove this line when supporting multiple filters in 'scale_mode 1'.
    #  Save original value and restore when leaving scale_mode 1. This is to avoid mismatch for scale_mode 0.
    set ::sth::Traffic::oriFilterType  $::sth::Traffic::FilterType 
    regsub {vlan_pri|vlan_pri_inner} $::sth::Traffic::FilterType "qos" ::sth::Traffic::FilterType
    
    switch $::sth::Traffic::FilterType {
        "qos" {
            #FilteredValue_1 is for the qos results
            set qosValue [::sth::sthCore::binToInt $stcArray(-FilteredValue_1)]
            #the values for one qos may exist in different filterResult, if this is the case, we will add them
            set aggregateCount $stcArray(-FrameCount)
            set aggregateRate_pps $stcArray(-FrameRate)
            set aggregateRate_bps $stcArray(-BitRate)
            
            keylget trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.count count
            keylget trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.rate_pps rate_pps
            keylget trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.rate_bps rate_bps
            if {[info exists count] && [info exists rate_pps] && [info exists rate_bps]} {
                set aggregateCount [expr $count + $aggregateCount]
                set aggregateRate_pps [expr $rate_pps + $aggregateRate_pps]
                set aggregateRate_bps [expr $rate_bps + $aggregateRate_bps]
            }
            
            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.count $aggregateCount
            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.rate_pps $aggregateRate_pps
            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$qosValue.rate_bps $aggregateRate_bps

        }
        "vlan_id" {
            #FilteredValue_1 is for the VLAN ID results
            set vlanValue $stcArray(-FilteredValue_1)

            set aggregateCount $stcArray(-FrameCount)
            set aggregateRate_pps $stcArray(-FrameRate)
            set aggregateRate_bps $stcArray(-BitRate)
        
            keylget trafficStatsKeyedList $currPort.aggregate.rx.vlan.$vlanValue.count count
            keylget trafficStatsKeyedList $currPort.aggregate.rx.vlan.$vlanValue.rate_pps rate_pps
            keylget trafficStatsKeyedList $currPort.aggregate.rx.vlan.$vlanValue.rate_bps rate_bps
            if {[info exists count] && [info exists rate_pps] && [info exists rate_bps]} {
                set aggregateCount "$aggregateCount $count"
                set aggregateRate_pps "$aggregateRate_pps $rate_pps"
                set aggregateRate_bps "$aggregateRate_bps $rate_bps"
            }

            keylset trafficStatsKeyedList $currPort.aggregate.rx.vlan.$vlanValue.count $aggregateCount
            keylset trafficStatsKeyedList $currPort.aggregate.rx.vlan.$vlanValue.rate_pps $aggregateRate_pps
            keylset trafficStatsKeyedList $currPort.aggregate.rx.vlan.$vlanValue.rate_bps $aggregateRate_bps
        }
        "vlan_id_inner" {
            #FilteredValue_1 is for the VLAN ID results
            set vlanValue $stcArray(-FilteredValue_1)
            
            set aggregateCount $stcArray(-FrameCount)
            set aggregateRate_pps $stcArray(-FrameRate)
            set aggregateRate_bps $stcArray(-BitRate)
        
            keylget trafficStatsKeyedList $currPort.aggregate.rx.vlan_inner.$vlanValue.count count
            keylget trafficStatsKeyedList $currPort.aggregate.rx.vlan_inner.$vlanValue.rate_pps rate_pps
            keylget trafficStatsKeyedList $currPort.aggregate.rx.vlan_inner.$vlanValue.rate_bps rate_bps
            if {[info exists count] && [info exists rate_pps] && [info exists rate_bps]} {
                set aggregateCount "$aggregateCount $count"
                set aggregateRate_pps "$aggregateRate_pps $rate_pps"
                set aggregateRate_bps "$aggregateRate_bps $rate_bps"
            }
            
            keylset trafficStatsKeyedList $currPort.aggregate.rx.vlan_inner.$vlanValue.count $aggregateCount
            keylset trafficStatsKeyedList $currPort.aggregate.rx.vlan_inner.$vlanValue.rate_pps $aggregateRate_pps
            keylset trafficStatsKeyedList $currPort.aggregate.rx.vlan_inner.$vlanValue.rate_bps $aggregateRate_bps
        }
        "dscp" {
            #FilteredValue_2 is for tos stats  
            set tosValue $stcArray(-FilteredValue_1)
            #translate the tos bin to decimal value     
            #set tosbin [string range $bin 3 6]     
            set aggregateCount $stcArray(-FrameCount)
            set aggregateRate_pps $stcArray(-FrameRate)
            set aggregateRate_bps $stcArray(-BitRate)
        
            keylget trafficStatsKeyedList $currPort.aggregate.rx.qos.$tosValue.count count
            keylget trafficStatsKeyedList $currPort.aggregate.rx.qos.$tosValue.rate_pps rate_pps
            keylget trafficStatsKeyedList $currPort.aggregate.rx.qos.$tosValue.rate_bps rate_bps
            if {[info exists count] && [info exists rate_pps] && [info exists rate_bps]} {
                set aggregateCount [expr $count + $aggregateCount]
                set aggregateRate_pps [expr $rate_pps + $aggregateRate_pps]
                set aggregateRate_bps [expr $rate_bps + $aggregateRate_bps]
            }
            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$tosValue.count $aggregateCount
            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$tosValue.rate_pps $aggregateRate_pps
            keylset trafficStatsKeyedList $currPort.aggregate.rx.qos.$tosValue.rate_bps $aggregateRate_bps
        } 
        "tos" {
            #FilteredValue_2 is for tos stats  
            set bin $stcArray(-FilteredValue_2)
            #translate the tos bin to decimal value     
            set tosbin [string range $bin 3 6]
            set precbin [string range $bin 0 2]
            set tosValue [::sth::sthCore::binToInt $tosbin]
            set precValue [::sth::sthCore::binToInt $precbin]
            
            set aggregateCount $stcArray(-FrameCount)
            set aggregateRate_pps $stcArray(-FrameRate)
            set aggregateRate_bps $stcArray(-BitRate)
            keylget trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.count count
            keylget trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_pps rate_pps
            keylget trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_bps rate_bps
            if {[info exists count] && [info exists rate_pps] && [info exists rate_bps]} {
                set aggregateCount [expr $count + $aggregateCount]
                set aggregateRate_pps [expr $rate_pps + $aggregateRate_pps]
                set aggregateRate_bps [expr $rate_bps + $aggregateRate_bps]
            }
            keylset trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.count $aggregateCount
            keylset trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_pps $aggregateRate_pps
            keylset trafficStatsKeyedList $currPort.aggregate.rx.tos.$tosValue.rate_bps $aggregateRate_bps

            keylset trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.count $aggregateCount
            keylset trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.rate_pps $aggregateRate_pps
            keylset trafficStatsKeyedList $currPort.aggregate.rx.prec.$precValue.rate_bps $aggregateRate_bps
        } 
    }

    # restore
    set ::sth::Traffic::FilterType  $::sth::Traffic::oriFilterType
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::updateOofCounters {resultVal properties portHnd} {
    upvar userArgsArray userArgsArray;
    upvar trafficStatsKeyedList trafficStatsKeyedList;

    array set hnd $resultVal
    set key "$portHnd.stream.unknown.rx"

    #OverflowResults - Getting mapping the native and hlt return keys/values
    set TableName ::sth::Traffic::traffic_stats_out_of_filter_results_stcattr
    if {$properties eq ""} {
        set hltOptionList [array names $TableName]
    } else {
        set hltOptionList $properties
    }
    foreach hltName $hltOptionList {
        if {[info exists ::sth::Traffic::traffic_stats_out_of_filter_results_stcattr($hltName)]} {
            set stcName [set ::sth::Traffic::traffic_stats_out_of_filter_results_stcattr($hltName)]
            if {($stcName ne "_none_")} {
                set stcValue $hnd(-$stcName)
                keylset trafficStatsKeyedList $key.$hltName $stcValue
            }
        }
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Traffic::getStreamblockList {} {
    upvar userArgsArray userArgsArray
    
    #port_handle/streams handle check
    if {[info exists userArgsArray(streams)] && $userArgsArray(streams) ne "" && $userArgsArray(streams) ne "all"} {
        set streamBlockList $userArgsArray(streams)
    } elseif {[info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) ne "" && $userArgsArray(port_handle) ne "all"} {
        foreach port $userArgsArray(port_handle) {
            set streamHandle [sth::sthCore::invoke "stc::get $port -children-streamblock"]
            append streamBlockList " $streamHandle"
        }
    } else {
        #if no port_handle/handle passed, then gets all streamblocks
        set portList [sth::sthCore::invoke "stc::get project1 -children-port"]
        foreach port $portList {
            set streamHandle [sth::sthCore::invoke "stc::get $port -children-streamblock"]
            append streamBlockList " $streamHandle"
        }
    }
    
    return $streamBlockList
}

proc ::sth::Traffic::getPortList {} {
    upvar userArgsArray userArgsArray
    
    #port_handle/streams handle check
    if {[info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) ne "" && $userArgsArray(port_handle) ne "all"} {
        set portList $userArgsArray(port_handle)
    } elseif {[info exists userArgsArray(streams)] && $userArgsArray(streams) ne "" && $userArgsArray(streams) ne "all"} {
        foreach streamblock $userArgsArray(streams) {
            set portHandle [sth::sthCore::invoke "stc::get $streamblock -parent"]
            append portList " $portHandle"
        }
    } else {
        #if no port_handle/handle passed, then gets all ports
        set portList [sth::sthCore::invoke "stc::get project1 -children-port"]
    }
    
    return $portList
}



proc ::sth::Traffic::unsubscribeTrafficObject {resultDataSet} {

    #Unsubscribing and deleting resultdataset object
    sth::sthCore::invoke stc::perform ResultDataSetUnsubscribeCommand -ResultDataSet $resultDataSet
    sth::sthCore::invoke stc::perform DeleteCommand -ConfigList $resultDataSet
    
    return $::sth::sthCore::SUCCESS
}
