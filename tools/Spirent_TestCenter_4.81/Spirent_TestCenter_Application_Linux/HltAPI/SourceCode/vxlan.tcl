namespace eval ::sth::vxlan:: {

}

proc ::sth::emulation_vxlan_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_config" $args
    
    variable ::sth::vxlan::userArgsArray
    variable ::sth::vxlan::sortedSwitchPriorityList
    array unset ::sth::vxlan::userArgsArray
    array set ::sth::vxlan::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlan::vxlanTable $args \
                                                            ::sth::vxlan:: \
                                                            emulation_vxlan_config \
                                                            ::sth::vxlan::userArgsArray \
                                                            ::sth::vxlan::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::vxlan::emulation_vxlan_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_vxlan_config : $err"
    }
    return $returnKeyedList
}
proc ::sth::vxlan::emulation_vxlan_config_imp {returnKeyedList} {
    variable userArgsArray
    upvar 1 $returnKeyedList myreturnKeyedList
    if {!([info exists ::sth::vxlan::userArgsArray(handle)] || [info exists ::sth::vxlan::userArgsArray(port_handle)])} {
        return  -code 1 -errorcode -1 "Error : The command emulation_vxlan_config requires -port_handle or -handle."
    }
        
    if {[info exists ::sth::vxlan::userArgsArray(handle)] && [info exists ::sth::vxlan::userArgsArray(port_hanlde)]} {
        return -code 1 -errorcode -1 "The options -port_handle or -handle are mutually exclusive."
    }
        
    set mode $::sth::vxlan::userArgsArray(mode)   
    ::sth::vxlan::emulation_vxlan_config_$mode myreturnKeyedList
    return $myreturnKeyedList
}
proc ::sth::emulation_vxlan_control {args} {
    variable ::sth::vxlan::userArgsArray
    variable ::sth::vxlan::sortedSwitchPriorityList
    array unset ::sth::vxlan::userArgsArray
    array set ::sth::vxlan::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_control"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlan::vxlanTable $args \
                                                            ::sth::vxlan:: \
                                                            emulation_vxlan_control \
                                                            ::sth::vxlan::userArgsArray \
                                                            ::sth::vxlan::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {!([info exists ::sth::vxlan::userArgsArray(handle)] || 
        [info exists ::sth::vxlan::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error : The command $_hltCmdName requires -port_handle or -handle."
        return $returnKeyedList
    }
        
    if {[info exists ::sth::vxlan::userArgsArray(handle)] &&
        [info exists ::sth::vxlan::userArgsArray(port_hanlde)]} {
            ::sth::sthCore::processError returnKeyedList "The options -port_handle or -handle are mutually exclusive."
            return $returnKeyedList
    }
    
    
    set retVal [catch {
        set action $::sth::vxlan::userArgsArray(action)
        set device_list ""
        if {[info exists ::sth::vxlan::userArgsArray(handle)]} {
            set device_list $::sth::vxlan::userArgsArray(handle)
        } else {
            set port_list $::sth::vxlan::userArgsArray(port_handle)
            foreach port $port_list {
                #get the vxlan device
                set devices [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
                foreach device $devices {
                    set vtep [::sth::sthCore::invoke stc::get $device -children-VxlanVtepConfig]
                    if {![regexp "^$" $vtep]} {
                        set device_list [concat $device_list $device]
                    }
                }
            }
        }
        if {[regexp "start" $action]} {
            ::sth::sthCore::invoke stc::perform devicestart -devicelist $device_list
        } else {
            ::sth::sthCore::invoke stc::perform devicestop -devicelist $device_list
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList "Error in $action\ing vxlan device : $returnedString"
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $returnKeyedList
}

proc ::sth::emulation_vxlan_stats {args} {
    #get the result under the VxlanVtepConfig
    variable ::sth::vxlan::userArgsArray
    variable ::sth::vxlan::sortedSwitchPriorityList
    array unset ::sth::vxlan::userArgsArray
    array set ::sth::vxlan::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_stats"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlan::vxlanTable $args \
                                                            ::sth::vxlan:: \
                                                            emulation_vxlan_stats \
                                                            ::sth::vxlan::userArgsArray \
                                                            ::sth::vxlan::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {!([info exists ::sth::vxlan::userArgsArray(handle)] || 
        [info exists ::sth::vxlan::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error : The command $_hltCmdName requires -port_handle or -handle."
        return $returnKeyedList
    }
        
    if {[info exists ::sth::vxlan::userArgsArray(handle)] &&
        [info exists ::sth::vxlan::userArgsArray(port_hanlde)]} {
            ::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires: the options -port_handle or -handle are mutually exclusive."
            return $returnKeyedList
    }
    if {[catch {::sth::vxlan::emulation_vxlan_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get vxlan stats : $err"
    }
    return $returnKeyedList
}
########################VXLAN Wizard APIs#####################################
proc ::sth::emulation_vxlan_port_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_port_config" $args
    
    variable ::sth::vxlan::userArgsArray
    variable ::sth::vxlan::sortedSwitchPriorityList
    array unset ::sth::vxlan::userArgsArray
    array set ::sth::vxlan::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_port_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlan::vxlanTable $args \
                                                            ::sth::vxlan:: \
                                                            emulation_vxlan_port_config \
                                                            ::sth::vxlan::userArgsArray \
                                                            ::sth::vxlan::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
	if {!([info exists ::sth::vxlan::userArgsArray(handle)] || [info exists ::sth::vxlan::userArgsArray(port_handle)])} {
        return  -code 1 -errorcode -1 "Error : The command emulation_vxlan_port_config requires -port_handle or -handle."
    }  
    set mode $::sth::vxlan::userArgsArray(mode)   
    if {[catch {::sth::vxlan::emulation_vxlan_port_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_vxlan_port_config : $err"
    }
    return $returnKeyedList
}

proc ::sth::emulation_nonvxlan_port_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_nonvxlan_port_config" $args
    
    variable ::sth::vxlan::userArgsArray
    variable ::sth::vxlan::sortedSwitchPriorityList
    array unset ::sth::vxlan::userArgsArray
    array set ::sth::vxlan::userArgsArray {}
    
    set _hltCmdName "emulation_nonvxlan_port_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlan::vxlanTable $args \
                                                            ::sth::vxlan:: \
                                                            emulation_nonvxlan_port_config \
                                                            ::sth::vxlan::userArgsArray \
                                                            ::sth::vxlan::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
	if {!([info exists ::sth::vxlan::userArgsArray(handle)] || [info exists ::sth::vxlan::userArgsArray(port_handle)])} {
        return  -code 1 -errorcode -1 "Error : The command emulation_nonvxlan_port_config requires -port_handle or -handle."
    }
        
    set mode $::sth::vxlan::userArgsArray(mode)   
    if {[catch {::sth::vxlan::emulation_nonvxlan_port_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_nonvxlan_port_config : $err"
    }
    return $returnKeyedList
}

proc ::sth::emulation_vxlan_wizard_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_wizard_config" $args
    
    variable ::sth::vxlan::userArgsArray
    variable ::sth::vxlan::sortedSwitchPriorityList
    array unset ::sth::vxlan::userArgsArray
    array set ::sth::vxlan::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_wizard_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlan::vxlanTable $args \
                                                            ::sth::vxlan:: \
                                                            emulation_vxlan_wizard_config \
                                                            ::sth::vxlan::userArgsArray \
                                                            ::sth::vxlan::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
	
    set mode $::sth::vxlan::userArgsArray(mode)   
    if {[catch {::sth::vxlan::emulation_vxlan_wizard_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_vxlan_wizard_config : $err"
    }
    return $returnKeyedList
}

