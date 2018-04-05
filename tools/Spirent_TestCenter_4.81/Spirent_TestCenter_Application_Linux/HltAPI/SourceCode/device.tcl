namespace eval ::sth:: {

}

proc ::sth::emulation_device_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_device_config" $args
    
    variable ::sth::device::userArgsArray
    variable ::sth::device::sortedSwitchPriorityList
    array unset ::sth::device::userArgsArray
    array set ::sth::device::userArgsArray {}
    
    set _hltCmdName "emulation_device_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::device::deviceTable $args \
                                                            ::sth::device:: \
                                                            emulation_device_config \
                                                            ::sth::device::userArgsArray \
                                                            ::sth::device::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {!([info exists ::sth::device::userArgsArray(handle)] || 
        [info exists ::sth::device::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error : The command $_hltCmdName requires -port_handle or -handle."
        return $returnKeyedList
    }
        
    if {[info exists ::sth::device::userArgsArray(handle)] &&
        [info exists ::sth::device::userArgsArray(port_hanlde)]} {
        ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, The options -port_handle or -handle are mutually exclusive."
        return $returnKeyedList
    }
        
    set mode $::sth::device::userArgsArray(mode)
    # US37595 --TA144698 fix backward compatability issue
    if {[string equal $mode "modify"]} {
        if {[lsearch $args "-encapsulation"] == -1} {
            set ::sth::device::userArgsArray(encapsulation) ""
        }
        if {[lsearch $args "-vlan_id_list"] == -1} {
            set ::sth::device::userArgsArray(vlan_id_list) ""
        }
    }
    if {[catch {::sth::device::emulation_device_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing raw device : $err"
        return $returnKeyedList
    }
    
    return $returnKeyedList
}