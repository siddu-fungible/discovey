namespace eval ::sth::alarms {
    
    variable alarms_subscription_state 0
    
    #alarm types for OC3 interface
    array set ALARMSTYPEOC3 {
        line_ais    LINE_AIS
        line_bip24  LINE_B2
        line_rdi    LINE_RDI
        line_rei    LINE_REI
        path_ais    PATH_AIS
        path_bip8   PATH_B3
        path_rdi    PATH_RDI
        path_rei    PATH_REI
        sec_bip8    SECTION_B1
        unequip     PATH_UNEQUIPPED
    }
    
    #alarm types for OC12 interface
    array set ALARMSTYPEOC12 {
        line_ais    LINE_AIS
        line_bip96  LINE_B2
        line_rdi    LINE_RDI
        line_rei    LINE_REI
        path_ais    PATH_AIS
        path_bip8   PATH_B3
        path_rdi    PATH_RDI
        path_rei    PATH_REI
        sec_bip8    SECTION_B1
        unequip     PATH_UNEQUIPPED
    }
    
    #alarm types for OC48 interface
    array set ALARMSTYPEOC48 {
        line_ais    LINE_AIS
        line_bip384 LINE_B2
        line_rdi    LINE_RDI
        line_rei    LINE_REI
        path_ais    PATH_AIS
        path_bip8   PATH_B3
        path_rdi    PATH_RDI
        path_rei    PATH_REI
        sec_bip8    SECTION_B1
        unequip     PATH_UNEQUIPPED
    }
    #alarm types other interfaces except OC3, OC12 and OC48
    array set ALARMSTYPEOTHER {
        line_ais    LINE_AIS
        line_rdi    LINE_RDI
        line_rei    LINE_REI
        path_ais    PATH_AIS
        path_bip8   PATH_B3
        path_rdi    PATH_RDI
        path_rei    PATH_REI
        sec_bip8    SECTION_B1
        unequip     PATH_UNEQUIPPED
    }
}

proc ::sth::alarms::alarms_control_start {returnKeyedListVarName} {
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(alarm_type)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory switch -alarm_type" {}
            return -code error $returnKeyedList
        }
        
        set activePhy [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -ActivePhy-targets]
        
        #get lineSpeed
        set lineSpeed [::sth::sthCore::invoke stc::get $activePhy.SonetConfig -LineSpeed]
        
        set alarmType $userArgsArray(alarm_type)
        set injectorProperty ""
        switch -- $lineSpeed {
            "OC3" {
                if {[info exists ::sth::alarms::ALARMSTYPEOC3($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOC3($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
            "OC12" {
                if {[info exists ::sth::alarms::ALARMSTYPEOC12($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOC12($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
            "OC48" {
                if {[info exists ::sth::alarms::ALARMSTYPEOC48($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOC48($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
            default {
                if {[info exists ::sth::alarms::ALARMSTYPEOTHER($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOTHER($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        if {$userArgsArray(mode) == "momentary"} {
            for {set i 1} {$i <= $userArgsArray(count)} {incr i} {
                
                ::sth::sthCore::invoke stc::perform SonetInjectOne -InjectorCommand MOMENTARY -InjectorProperty  $injectorProperty -Port $userArgsArray(port_handle)
                
                after [expr 1000 * {$userArgsArray(interval)}]
            }
        } elseif {$userArgsArray(mode) == "continuous"} {
            ::sth::sthCore::invoke stc::perform SonetInjectOne -InjectorCommand START -InjectorProperty  $injectorProperty -Port $userArgsArray(port_handle)
        }
    } returnedString]
    
    return -code $retVal $returnedString
}


proc ::sth::alarms::alarms_control_stop {returnKeyedListVarName} {
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(alarm_type)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory switch -alarm_type" {}
            return -code error $returnKeyedList
        }
        
        set activePhy [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -ActivePhy-targets]
        
        #get lineSpeed
        set lineSpeed [::sth::sthCore::invoke stc::get $activePhy.SonetConfig -LineSpeed]
        
        set alarmType $userArgsArray(alarm_type)
        set injectorProperty ""
        switch -- $lineSpeed {
            "OC3" {
                if {[info exists ::sth::alarms::ALARMSTYPEOC3($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOC3($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
            "OC12" {
                if {[info exists ::sth::alarms::ALARMSTYPEOC12($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOC12($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
            "OC48" {
                if {[info exists ::sth::alarms::ALARMSTYPEOC48($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOC48($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
            default {
                if {[info exists ::sth::alarms::ALARMSTYPEOTHER($alarmType)]} {
                    set injectorProperty $::sth::alarms::ALARMSTYPEOTHER($alarmType)
                } else {
                    ::sth::sthCore::processError returnKeyedList "The alarm type $alarmType is not valid for $lineSpeed interface" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        ::sth::sthCore::invoke stc::perform SonetInjectOne -InjectorCommand OFF -InjectorProperty  $injectorProperty -Port $userArgsArray(port_handle)
    
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::alarms::alarms_control_reset {returnKeyedListVarName} {
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList      

    ::sth::sthCore::invoke stc::perform SonetResetAlarms -Port $userArgsArray(port_handle)
    ::sth::sthCore::invoke stc::perform ResultsClearAll -PortList $userArgsArray(port_handle)
    return $returnKeyedList
}


proc ::sth::alarms::alarms_stats_collect {returnKeyedListVarName} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch { 
        set portHandle $userArgsArray(port_handle)
        
        # get required handles
        set sonetResults [::sth::sthCore::invoke stc::get $portHandle -children-SonetResults]
            
        set sonetAlarmsResults [::sth::sthCore::invoke stc::get $portHandle -children-SonetAlarmsResults]
        
        keylset returnKeyedList port_handle $portHandle
        
        set hdlArray(SonetResults) $sonetResults
        set hdlArray(SonetAlarmsResults) $sonetAlarmsResults
              
        foreach key [array names ::sth::alarms::alarms_stats_mode] {
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::alarms:: alarms_stats $key supported] "false"]} {
                continue
            }
            if {[string match [set Obj [::sth::sthCore::getswitchprop ::sth::alarms:: alarms_stats $key stcobj]] "_none_"]} {
                continue
            }

            if {$Obj == "SonetResults"} {
                if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::alarms:: alarms_stats $key stcattr]] "_none_"]} {
                    continue
                }
                set val [::sth::sthCore::invoke stc::get $hdlArray($Obj) -$stcAttr]
                keylset returnKeyedList $key $val
            } elseif {$Obj == "SonetAlarmsResults"} {
                array set alarmResults [::sth::sthCore::invoke stc::get $hdlArray($Obj) "-Aisl -Aisp -J0unst -J1unst -Kchg -Kunst -Lof -Lopp -Los -Oof -Plmp -Rdil -Rdip -Timp -Uneqp"]
                
                set alarmDetected ""
                foreach attr [array names alarmResults] {
                    if {$alarmResults($attr) != 0} {
                        set attr [string trimleft $attr "-"]
                        lappend alarmDetected $attr
                    }
                }
                if {[string length $alarmDetected] == 0} {
                    set alarmDetected "--"
                }
                keylset returnKeyedList $key $alarmDetected
            }
        } 
    } returnedString]
    
    return -code $retVal $returnedString
}
