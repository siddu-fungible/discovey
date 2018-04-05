proc ::sth::hunderdGig::config_pcs_error_insertion {pcs_error_insertion_handle} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    set configList ""
    set TableName ::sth::hunderdGig::pcs_error_config_stcattr
    foreach key $sortedSwitchPriorityList {
        set arg [lindex $key 1]
        if {$arg != "handle" && $arg != "port_handle"} {
            set stcattr [set $TableName\($arg)]
            set value $userArgsArray($arg)
            if {[regexp "lane" $arg]} {
                set configList [concat $configList "-$stcattr \"$value\""]
            } else {
                set configList [concat $configList "-$stcattr $value"]
            }
        }
    }
    ::sth::sthCore::invoke stc::config $pcs_error_insertion_handle $configList
}
proc ::sth::hunderdGig::config_random_error_insertion {random_error_insertion_handle} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    set configList ""
    set TableName ::sth::hunderdGig::random_error_config_stcattr
    foreach key $sortedSwitchPriorityList {
        set arg [lindex $key 1]
        if {$arg != "handle" && $arg != "port_handle"} {
            set stcattr [set $TableName\($arg)]
            set value $userArgsArray($arg)
            if {[regexp "lane" $arg]} {
                set configList [concat $configList "-$stcattr \"$value\""]
            } else {
                set configList [concat $configList "-$stcattr $value"]
            }
        }
    }
    ::sth::sthCore::invoke stc::config $random_error_insertion_handle $configList
}


proc ::sth::hunderdGig::forty_hundred_gig_l1_results_pcs {object_list} {
    variable userArgsArray
    set returnKeyedList ""
    set properties "Port.Name
                    Port.PCS.BIP8ErrorRate
                    Port.PCS.BIP8Errors
                    Port.PCS.BIP8ErrorsErr
                    Port.PCS.BIP8ErrorsLastSec
                    Port.PCS.ConsecErrorRate
                    Port.PCS.ConsecErrors
                    Port.PCS.ConsecErrorsErr
                    Port.PCS.ConsecErrorsLastSec
                    Port.PCS.LengthErrorRate
                    Port.PCS.LengthErrors
                    Port.PCS.LengthErrorsErr
                    Port.PCS.LengthErrorsLastSec
                    Port.PCS.MarkerErrorRate
                    Port.PCS.MarkerErrors
                    Port.PCS.MarkerErrorsErr
                    Port.PCS.MarkerErrorsLastSec
                    Port.PCS.SHErrorRate
                    Port.PCS.SHErrors
                    Port.PCS.SHErrorsErr
                    Port.PCS.SHErrorsLastSec
                    Port.PCS.SyncErrorRate
                    Port.PCS.SyncErrors
                    Port.PCS.SyncErrorsErr
                    Port.PCS.SyncErrorsLastSec"
    set drv [sth::sthCore::invoke "stc::create DynamicResultView -under $::sth::sthCore::GBLHNDMAP(project) -Name \"Port PCS Results\""]
    set drvResultQ [sth::sthCore::invoke "stc::create PresentationResultQuery -under $drv -Name \"Port PCS Results\" "]
    
    sth::sthCore::invoke "stc::config $drvResultQ -SelectProperties \"$properties\"\
                                          -FromObjects \"$object_list\"\
                                          -LimitSize 2000\
                                          -SortBy \"\"\
                                          -WhereConditions \"\"\
                                          -GroupByProperties \"\""
    sth::sthCore::invoke "stc::perform SubscribeDynamicResultViewCommand -DynamicResultView $drv"
    ::sth::sthCore::invoke stc::sleep 3;
    
    process_ret_value pcs $properties $drvResultQ returnKeyedList
    return $returnKeyedList
}

proc ::sth::hunderdGig::forty_hundred_gig_l1_results_pcs_lane {object_list} {
    variable userArgsArray
    set returnKeyedList ""
    set properties "Port.Name
                    Port.PCS.Lane.Index
                    Port.PCS.Lane.BIP8ErrorRate
                    Port.PCS.Lane.BIP8Errors
                    Port.PCS.Lane.BIP8ErrorsErr
                    Port.PCS.Lane.BIP8ErrorsLastSec
                    Port.PCS.Lane.ConsecErrorRate
                    Port.PCS.Lane.ConsecErrors
                    Port.PCS.Lane.ConsecErrorsErr
                    Port.PCS.Lane.ConsecErrorsLastSec
                    Port.PCS.Lane.LengthErrorRate
                    Port.PCS.Lane.LengthErrors
                    Port.PCS.Lane.LengthErrorsErr
                    Port.PCS.Lane.LengthErrorsLastSec
                    Port.PCS.Lane.MarkerErrorRate
                    Port.PCS.Lane.MarkerErrors
                    Port.PCS.Lane.MarkerErrorsErr
                    Port.PCS.Lane.MarkerErrorsLastSec
                    Port.PCS.Lane.SHErrorRate
                    Port.PCS.Lane.SHErrors
                    Port.PCS.Lane.SHErrorsErr
                    Port.PCS.Lane.SHErrorsLastSec
                    Port.PCS.Lane.SyncErrorRate
                    Port.PCS.Lane.SyncErrors
                    Port.PCS.Lane.SyncErrorsErr
                    Port.PCS.Lane.SyncErrorsLastSec"
    set drv [sth::sthCore::invoke "stc::create DynamicResultView -under $::sth::sthCore::GBLHNDMAP(project) -Name \"Port PCS Lane Results\""]
    set drvResultQ [sth::sthCore::invoke "stc::create PresentationResultQuery -under $drv -Name \"Port PCS Lane Results\" "]
    
    sth::sthCore::invoke "stc::config $drvResultQ -SelectProperties \"$properties\"\
                                          -FromObjects \"$object_list\"\
                                          -LimitSize 2000\
                                          -SortBy \"\"\
                                          -WhereConditions \"\"\
                                          -GroupByProperties \"Port.Name\""
    
    sth::sthCore::invoke "stc::perform SubscribeDynamicResultViewCommand -DynamicResultView $drv"
    ::sth::sthCore::invoke stc::sleep 3;
    
    process_ret_value pcs_lane $properties $drvResultQ returnKeyedList
    return $returnKeyedList
}

proc ::sth::hunderdGig::forty_hundred_gig_l1_results_pma_lane {object_list} {
    variable userArgsArray
    set returnKeyedList ""
    set properties "Port.Name
                    Port.PMA.Lane.Lane
                    Port.PMA.Lane.BerErrorRate
                    Port.PMA.Lane.BerErrors
                    Port.PMA.Lane.BerSync
                    Port.PMA.Lane.BerUnsync
                    Port.PMA.Lane.RxPrbsPattern"
    set drv [sth::sthCore::invoke "stc::create DynamicResultView -under $::sth::sthCore::GBLHNDMAP(project) -Name \"Port PMA Lane Results\""]
    set drvResultQ [sth::sthCore::invoke "stc::create PresentationResultQuery -under $drv -Name \"Port PMA Lane Results\" "]
    
    sth::sthCore::invoke "stc::config $drvResultQ -SelectProperties \"$properties\"\
                                          -FromObjects \"$object_list\"\
                                          -LimitSize 2000\
                                          -SortBy \"\"\
                                          -WhereConditions \"\"\
                                          -GroupByProperties \"Port.Name\""
    sth::sthCore::invoke "stc::perform SubscribeDynamicResultViewCommand -DynamicResultView $drv"
    ::sth::sthCore::invoke stc::sleep 3;
    process_ret_value pma_lane $properties $drvResultQ returnKeyedList
    return $returnKeyedList
}


proc ::sth::hunderdGig::process_ret_value {type properties drvResultQ returnKeyedList} {
    variable userArgsArray
    upvar $returnKeyedList myreturnKeyedList
    set resultViewDataList [sth::sthCore::invoke "stc::get $drvResultQ -children-ResultViewData"]
    keylset myreturnKeyedList result_count [llength $resultViewDataList]
    set property_num [llength $properties]
    set i 0
    foreach resultViewData $resultViewDataList {
        set resultDataList [lrange [sth::sthCore::invoke "stc::get $resultViewData -ResultData"] 0 [expr $property_num - 1]]
        #get the port handle
        set port_name [lindex $resultDataList 0]
        set obj_list [stc::perform GetObjects -rootlist $::sth::sthCore::GBLHNDMAP(project) -classname port -condition "name = $port_name"]
        set obj_index [expr [lsearch $obj_list "-ObjectList"] + 1]
        set port_handle [lindex $obj_list $obj_index]
        if {![regexp "lane" $type] || ![regexp "lanes" $userArgsArray(mode)]} {
            set item_value ""
            set j 0
            foreach property $properties {
                set property [string tolower [regsub -all {\.} $property {_}]]
                set value [lindex $resultDataList $j]
                keylset item_value $property $value
                incr j
            }
            keylset myreturnKeyedList $port_handle.port $item_value
        }
        if {[regexp "lane" $type] && [regexp "lanes|all" $userArgsArray(mode)]} {
            #when the type is pcs_lane and pma_lane and the mode is port or all need to get the results for every lane
            sth::sthCore::invoke "stc::perform ExpandResultViewDataCommand  -ResultViewData $resultViewData"
            set resultViewDataListChildren [sth::sthCore::invoke "stc::get $resultViewData -children"]
            set resultViewDataListSubList [sth::sthCore::invoke "stc::get $resultViewDataListChildren -children"]
            foreach resultViewDataListSub $resultViewDataListSubList {
                set resultDataList [lrange [sth::sthCore::invoke "stc::get $resultViewDataListSub -ResultData"] 1 [expr $property_num - 1]]
                set j 1
                set properties_lane [lrange $properties 2 end]
                set lane_id [lindex $resultDataList 0]
                set item_value ""
                foreach property $properties_lane {
                    set property [string tolower [regsub -all {\.} $property {_}]]
                    set value [lindex $resultDataList $j]
                    keylset item_value $property $value
                    incr j
                }
                keylset myreturnKeyedList $port_handle.lane.$lane_id $item_value
            }
        }
    }
}