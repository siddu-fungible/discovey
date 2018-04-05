namespace eval ::sth::fcoetraffic:: {
    proc ::sth::fcoetraffic::fcoe_traffic_config_create { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        set _OrigHltCmdName "fcoe_traffic_config"
        set _hltCmdName "fcoe_traffic_config_create"
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        set pl_id $::sth::fcoetraffic::userArgsArray(pl_id)
        regsub -all {/} $userArgsArray(pl_id) " " userArgsArray(pl_id)
        
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        array set arrayHandleConfigList {}
        
        set sb $userArgsArray(handle)
		set fcFcoe [::sth::sthCore::invoke stc::create fc:FCoE -under $sb]
		set fc [::sth::sthCore::invoke stc::create fc -under $fcFcoe]
		set fcHeader [::sth::sthCore::invoke stc::create fcHeader -under $fc]
		set fcPayloads [::sth::sthCore::invoke stc::create fcPayloads -under $fc]
        lappend configHandleList $fcFcoe $fcHeader
        
        foreach id [split $userArgsArray(pl_id)] {
			set fHnd [::sth::sthCore::invoke stc::create FCPayload-Choice -under $fcPayloads]
            set cHnd ""
            foreach cHndId [split $id -] {
			set cHnd [::sth::sthCore::invoke stc::create $cHndId -under $fHnd]
                set fHnd $cHnd
                lappend configHandleList $cHnd
            }
        }
        processCofigFCPayLoadAttr fcoe  $configHandleList returnKeyedList
        processCofigNonFCPayLoadAttr fcoe $configHandleList returnKeyedList
        
        foreach handle [split $configHandleList] {
            #STC limitation: have to increase the index of pdu
            regexp {(.*\D)(\d+)} $handle match obj i
            incr i
            regsub "$handle" $configHandleList $obj$i configHandleList 
        }
        
        set ::sth::fcoetraffic::arrayFCoESbBlockHandle($sb) $configHandleList
        return $::sth::sthCore::SUCCESS
    }

    proc ::sth::fcoetraffic::fcoe_traffic_config_modify { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        set _OrigHltCmdName "fcoe_traffic_config"
        set _hltCmdName "fcoe_traffic_config_modify"
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        
        set sb $userArgsArray(handle)
        if {(![info exists ::sth::fcoetraffic::arrayFCoESbBlockHandle($sb)]) || ($::sth::fcoetraffic::arrayFCoESbBlockHandle($sb) == "")} {
            ::sth::sthCore::processError returnKeyedList "modify $sb Error: $sb is not a valide FCoE traffic, please use fcoe_traffic_config -mode create to create one first"
            return $::sth::sthCore::FAILURE
        }
        set configHandleList $::sth::fcoetraffic::arrayFCoESbBlockHandle($sb)
        set fcFcoe [::sth::sthCore::invoke stc::get $sb "-children-fc:Fcoe"]
        set fc [::sth::sthCore::invoke stc::get $fcFcoe "-children-fc"]
        set fcHeader [::sth::sthCore::invoke stc::get $fc "-children-fcHeader"]
        set fcPayload [::sth::sthCore::invoke stc::get $fc "-children-fcPayloads"]
        set fcPayloadChoice [::sth::sthCore::invoke stc::get $fcPayload "-children-FCPayload-Choice"]
        set id $userArgsArray(pl_id)
        set fHndId  [lindex [split $id -] 0]
        if {[lsearch -regexp [string tolower $configHandleList] $fHndId\\d+]== -1} {
            set index [lsearch -regexp [string tolower $configHandleList] fcheader\\d+]
            ::sth::sthCore::invoke stc::delete $fcPayloadChoice
            set configHandleList [lrange $configHandleList 0 $index]
			set fHnd [::sth::sthCore::invoke stc::create FCPayload-Choice -under $fcPayload]
            set cHnd ""
            foreach cHndId [split $id -] {
				set cHnd [::sth::sthCore::invoke stc::create $cHndId -under $fHnd]
                set fHnd $cHnd
                lappend configHandleList $cHnd
            }
        } elseif {$fHndId == "fcpcmnd" && ([lsearch -regexp [string tolower $configHandleList] [string tolower $userArgsArray(pl_cdbtype)]\\d+] == -1)} {
            set fcpcmnd [::sth::sthCore::invoke stc::get $fcPayloadChoice "-children-fcpcmnd"]
            set fcpcdb [::sth::sthCore::invoke stc::get $fcpcmnd "-children-fcpcdb"]
            ::sth::sthCore::invoke stc::delete $fcpcdb
			set fcpcdb [::sth::sthCore::invoke stc::create fcpcdb -under $fcpcmnd]
            set index [lsearch -regexp [string tolower $configHandleList] fcpcdb\\d]
			set configHandleList [lreplace $configHandleList [expr $index+1] [expr $index+1] [::sth::sthCore::invoke stc::create $userArgsArray(pl_cdbtype) -under $fcpcdb]]
        } else {
            set fHnd [::sth::sthCore::invoke stc::get $fcPayloadChoice "-children-$fHndId"]
            set cHnd ""
            foreach cHndId [lrange [split $id -] 1 [expr [llength [split $id -]] -1]] {
                set cHnd [::sth::sthCore::invoke stc::get $fHnd "-children-$cHndId"]
                set fHnd $cHnd
            }
        }
        
        processCofigFCPayLoadAttr fcoe $configHandleList returnKeyedList
        processCofigNonFCPayLoadAttr fcoe $configHandleList returnKeyedList
        
        set ::sth::fcoetraffic::arrayFCoESbBlockHandle($sb) $configHandleList
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fcoetraffic::fcoe_traffic_config_reset { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        set _OrigHltCmdName "fcoe_traffic_config"
        set _hltCmdName "fcoe_traffic_config_reset"
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        set sb $userArgsArray(handle)
        if {(![info exists ::sth::fcoetraffic::arrayFCoESbBlockHandle($sb)]) || ($::sth::fcoetraffic::arrayFCoESbBlockHandle($sb) == "")} {
            ::sth::sthCore::processError returnKeyedList "config $sb Error: $sb is not a valide FCoE traffic, please use fcoe_traffic_config -mode create to create one first"
            return $::sth::sthCore::FAILURE
        }
        set configHandleList $::sth::fcoetraffic::arrayFCoESbBlockHandle($sb)
        set fcFcoe [::sth::sthCore::invoke stc::get $sb "-children-fc:Fcoe"]
        set fc [::sth::sthCore::invoke stc::get $fcFcoe "-children-fc"]
        if {[info exists userArgsArray(pl_id)]} {
            set id [split $userArgsArray(pl_id)] 
            set fHndId  [lindex [split $id -] 0]
            if {[lsearch -regexp [string tolower $configHandleList] $fHndId\\d+] !=  -1} {
                set fcPayload [::sth::sthCore::invoke stc::get $fc "-children-FCPayloads"]
                set fcPayloadChoice [::sth::sthCore::invoke stc::get $fcPayload "-children-FCPayload-Choice"]
                if {[set fHnd [::sth::sthCore::invoke stc::get $fcPayloadChoice "-children-$fHndId"]] != ""} {
                    set cHnd ""
                    foreach cHndId [lrange [split $id -] 1 [expr [llength [split $id -]] -1]] {
                        set cHnd [::sth::sthCore::invoke stc::get $fHnd "-children-$cHndId"]
                        set fHnd $cHnd
                    }
                }
            }
        }
        if {[::sth::fcoetraffic::processDeleteHnd fcoe configHandleList returnKeyedList]} {
            ::sth::sthCore::processError returnKeyedList "$procName Error"
            return $::sth::sthCore::FAILURE
        }
        set ::sth::fcoetraffic::arrayFCoESbBlockHandle($sb) $configHandleList
        return $::sth::sthCore::SUCCESS
    }
    proc ::sth::fcoetraffic::fip_traffic_config_create { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        set _OrigHltCmdName "fip_traffic_config"
        set _hltCmdName "fip_traffic_config_create"
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        array set arrayHandleConfigList {}
        
        set sb $userArgsArray(handle)
set fcFip [::sth::sthCore::invoke stc::create fc:FIP -under $sb]
set dl [::sth::sthCore::invoke stc::create dl -under $fcFip]
        lappend configHandleList $fcFip 
        foreach id [split $userArgsArray(dl_id)] {
set fHnd [::sth::sthCore::invoke stc::create DL-Choice -under $dl]
            set cHnd ""
            foreach cHndId [split $id -] {
set cHnd [::sth::sthCore::invoke stc::create $cHndId -under $fHnd]
                set fHnd $cHnd
                lappend configHandleList $cHnd
            }
        }
        
        processCofigFCPayLoadAttr fip $configHandleList returnKeyedList
        processCofigNonFCPayLoadAttr fip $configHandleList returnKeyedList
        
        foreach handle [split $configHandleList] {
            #STC limitation: have to increase the index of pdu
            regexp {(.*\D)(\d+)} $handle match obj i
            incr i
            regsub "$handle" $configHandleList $obj$i configHandleList
        }
        set ::sth::fcoetraffic::arrayFIPSbBlockHandle($sb) $configHandleList
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fcoetraffic::fip_traffic_config_modify { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        set _OrigHltCmdName "fip_traffic_config"
        set _hltCmdName "fip_traffic_config_modify"
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        
        set sb $userArgsArray(handle)
        if {(![info exists ::sth::fcoetraffic::arrayFIPSbBlockHandle($sb)]) || ($::sth::fcoetraffic::arrayFIPSbBlockHandle($sb) == "") } {
            ::sth::sthCore::processError returnKeyedList "modify $sb Error: $sb is not a valide FIP traffic, please use fip_traffic_config -mode create to create one first"
            return $::sth::sthCore::FAILURE
        }
        
        set configHandleList $::sth::fcoetraffic::arrayFIPSbBlockHandle($sb)
        set fcFip [::sth::sthCore::invoke stc::get $sb "-children-fc:Fip"]
        set dl [::sth::sthCore::invoke stc::get $fcFip "-children-dl"]
        foreach id [split $userArgsArray(dl_id)] {
            set fHndId  [lindex [split $id -] 0]
            if {[lsearch -regexp [string tolower $configHandleList] $fHndId\\d+]== -1} {
				set fHnd [::sth::sthCore::invoke stc::create DL-Choice -under $dl]
                set cHnd ""
                foreach cHndId [split $id -] {
					set cHnd [::sth::sthCore::invoke stc::create $cHndId -under $fHnd]
                    set fHnd $cHnd
                    lappend configHandleList $cHnd
                }
            } else {
                foreach dlChoice [split [::sth::sthCore::invoke stc::get $dl "-children-DL-Choice"]] {
                    if {[set fHnd [::sth::sthCore::invoke stc::get $dlChoice "-children-$fHndId"]] != ""} {
                        set cHnd ""
                        foreach cHndId [lrange [split $id -] 1 [expr [llength [split $id -]] -1]] {
                            set cHnd [::sth::sthCore::invoke stc::get $fHnd "-children-$cHndId"]
                            set fHnd $cHnd
                        }
                    }
                }
            }
        }
        
        processCofigFCPayLoadAttr fip $configHandleList returnKeyedList
        processCofigNonFCPayLoadAttr fip $configHandleList returnKeyedList
        
        foreach handle [split $configHandleList] {
            #STC limitation: have to increase the index of pdu
            regexp {(.*\D)(\d+)} $handle match obj i
            incr i
            regsub "$handle" $configHandleList $obj$i configHandleList 
        }
        
        set ::sth::fcoetraffic::arrayFCoESbBlockHandle($sb) $configHandleList
        return $::sth::sthCore::SUCCESS
    }
    
    
    proc ::sth::fcoetraffic::fip_traffic_config_reset { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        set _OrigHltCmdName "fip_traffic_config"
        set _hltCmdName "fip_traffic_config_reset"
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        set sb $userArgsArray(handle)
        if {(![info exists ::sth::fcoetraffic::arrayFIPSbBlockHandle($sb)]) ||  ($::sth::fcoetraffic::arrayFIPSbBlockHandle($sb) == "")} {
            ::sth::sthCore::processError returnKeyedList "config $sb Error: $sb is not a valide FIP traffic, please use fip_traffic_config -mode create to create one first"
            return $::sth::sthCore::FAILURE
        }
        set configHandleList $::sth::fcoetraffic::arrayFIPSbBlockHandle($sb)
        set fcFip [::sth::sthCore::invoke stc::get $sb "-children-fc:Fip"]
        set dl [::sth::sthCore::invoke stc::get $fcFip "-children-dl"]
        if {[info exists userArgsArray(dl_id)]} {
            foreach id [split $userArgsArray(dl_id)] {
                set fHndId  [lindex [split $id -] 0]
                if {[lsearch -regexp [string tolower $configHandleList] $fHndId\\d+] !=  -1} {
                    foreach dlChoice [split [::sth::sthCore::invoke stc::get $dl "-children-DL-Choice"]] {
                        if {[set fHnd [::sth::sthCore::invoke stc::get $dlChoice "-children-$fHndId"]] != ""} {
                            set cHnd ""
                            foreach cHndId [lrange [split $id -] 1 [expr [llength [split $id -]] -1]] {
                                set cHnd [::sth::sthCore::invoke stc::get $fHnd "-children-$cHndId"]
                                set fHnd $cHnd
                            }
                        }
                    }
                }
            }
        }
        if {[::sth::fcoetraffic::processDeleteHnd fip configHandleList returnKeyedList]} {
            ::sth::sthCore::processError returnKeyedList "$procName Error"
            return $::sth::sthCore::FAILURE
        }
        set ::sth::fcoetraffic::arrayFIPSbBlockHandle($sb) $configHandleList
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fcoetraffic::processCofigFCPayLoadAttr {type configHandleList returnInfoVarName} {
        set procName [lindex [info level [info level]] 0]
        upvar 1 $returnInfoVarName returnKeyedList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray

        foreach listname  $::sth::fcoetraffic::validList {
            if {[info exists userArgsArray(pl_$listname)]} {
                set stcObj     [::sth::sthCore::getswitchprop ::sth::fcoetraffic:: $type\_traffic_config pl_$listname stcobj]
                set fHndIds [lindex [split $stcObj -] 0]
                #set cHndIds [lrange [split $stcObj -] 1 [expr [llength $[split $stcObj -]] -1]]
                set cHndIds [split [lrange [split $stcObj -] 1 [expr [llength [split $stcObj -]] -1]]]
                foreach fHndId [split $fHndIds /] {
                    if {$fHndId == ""} {continue}
                    foreach pos [lsearch -regexp -all $configHandleList $fHndId\\d] {
                        set fHnd [lindex $configHandleList $pos]
                        if {$fHnd == ""} {continue}
                        set cHnd ""
                        if {[set cHnd [::sth::sthCore::invoke stc::get $fHnd "-children-[lindex $cHndIds 0]"]] == ""} {
                            foreach cHndId $cHndIds {
								set cHnd [::sth::sthCore::invoke stc::create $cHndId -under $fHnd]
                                set fHnd $cHnd
                            }
                        }
                        lappend configHandleList $cHnd
                        regsub -all {\s+} $userArgsArray(pl_$listname) " " user_list
                        regsub -all {^\s*|\s*$} $user_list "" user_list
                        array unset arruserlist
                        if {[catch {array set  arruserlist [split $user_list]} err]} {
                            ::sth::sthCore::processError returnKeyedList "$procName Error: $err\nPlease check your input userArgsArray($id\_$listname): $user_list"
                            return $::sth::sthCore::FAILURE
                        }
                        foreach attr [array names arruserlist] {
                            if {[lsearch -regexp [set ::sth::fcoetraffic::$listname] [string tolower $attr]]} {
                                lappend ${cHnd}_configList $attr $arruserlist($attr)
                            } else {
                                ::sth::sthCore::processError returnKeyedList "$procName Error: Invalid option $attr"
                                return $::sth::sthCore::FAILURE
                            }
                        }
                    }
                }
            }
        }
        foreach handle [split $configHandleList] {
            if {[info exists ${handle}_configList]  && ([set ${handle}_configList] != "")} {
                if {[catch {::sth::sthCore::invoke stc::config  $handle "[set ${handle}_configList]"} err]} {
                    ::sth::sthCore::processError returnKeyedList "config $handle Error: $err"
                    return $::sth::sthCore::FAILURE
                }
            }
        }
        return $::sth::sthCore::SUCCESS
        
    }
    
    proc ::sth::fcoetraffic::processCofigNonFCPayLoadAttr {type configHandleList returnInfoVarName} {
        set procName [lindex [info level [info level]] 0]
        upvar 1 $returnInfoVarName returnKeyedList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        foreach key $sortedSwitchPriorityList {
            set switchName [lindex $key 1]
            set switchValue $userArgsArray($switchName)
            set stcObj     [::sth::sthCore::getswitchprop ::sth::fcoetraffic:: $type\_traffic_config $switchName stcobj]
            set stcAttr     [::sth::sthCore::getswitchprop ::sth::fcoetraffic:: $type\_traffic_config $switchName stcattr]
            if {$stcAttr == "_none_"} { continue }
            if {[regexp / $stcObj]} {
                foreach stcobj [split $stcObj /] {
                    if {$stcobj == ""} {continue}
                    if {([set index [lsearch -regexp -all [string tolower $configHandleList] $stcobj\\d+]] != -1) } {
                        foreach pos $index {
                            set configHandle [lindex $configHandleList $pos]
                            lappend ${configHandle}_configList -$stcAttr $switchValue
                        }
                    }
                }
            } elseif {[set index [lsearch -regexp -all [string tolower $configHandleList] $stcObj\\d+]] !=-1} {
                foreach pos $index {
                    set configHandle [lindex $configHandleList $pos]
                    lappend ${configHandle}_configList -$stcAttr $switchValue
                }
            }
        }
        
        foreach handle [split $configHandleList] {
            if {[info exists ${handle}_configList] && ([set ${handle}_configList] != "")} {
                if {[catch {::sth::sthCore::invoke stc::config  $handle "[set ${handle}_configList]"} err]} {
                    ::sth::sthCore::processError returnKeyedList "config $handle Error: $err"
                    return $::sth::sthCore::FAILURE
                }
            }
        }
        return $::sth::sthCore::SUCCESS
    }
    proc ::sth::fcoetraffic::processDeleteHnd {type configHandleListVarName returnInfoVarName} {
        set procName [lindex [info level [info level]] 0]
        upvar 1 $returnInfoVarName returnKeyedList
        upvar 1 $configHandleListVarName configHandleList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        
        if {$type == "fcoe"} {
            set idList pl_id
        } else {
            set idList dl_id
        }
        
        if {[info exists userArgsArray($idList)]} {
            foreach id $userArgsArray($idList) {
                set fHndId  [lindex [split $id /] 0]
                set offset [llength [lindex [split $id /]]]
                if {([set index [lsearch -regexp [string tolower $configHandleList] $fHndId]] != -1) } {
                    set fHnd [lindex $configHandleList $index]
                    ::sth::sthCore::invoke stc::delete [::sth::sthCore::invoke stc::get $fHnd -parent]
                    set configHandleList [lreplace $configHandleList $index [expr $index+$offset] ""]
                }
            }
            foreach ele $configHandleList {
                if {$ele == ""} {continue}
                lappend newConfigHandleList $ele
            }
            set configHandleList {}
            set configHandleList $newConfigHandleList
        } else {
            set handList [split $configHandleList] 
            if {[catch {::sth::sthCore::invoke stc::delete [lindex $handList 0]} err]} {
                ::sth::sthCore::processError returnKeyedList "delete [lindex $handList 0] Error: $err"
                return $::sth::sthCore::FAILURE
            }
            set configHandleList {}
        }
        return $::sth::sthCore::SUCCESS
    }
}
