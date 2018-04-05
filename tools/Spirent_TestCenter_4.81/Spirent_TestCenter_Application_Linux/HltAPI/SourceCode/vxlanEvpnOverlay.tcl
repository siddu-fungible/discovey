namespace eval ::sth::vxlanEvpnOverlay:: {
}

proc ::sth::emulation_vxlan_evpn_overlay_control {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_evpn_overlay_control" $args
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    variable ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList
    array unset ::sth::vxlanEvpnOverlay::userArgsArray
    array set ::sth::vxlanEvpnOverlay::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_evpn_overlay_control"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlanEvpnOverlay::vxlanEvpnOverlayTable $args \
                                                            ::sth::vxlanEvpnOverlay:: \
                                                            emulation_vxlan_evpn_overlay_control \
                                                            ::sth::vxlanEvpnOverlay::userArgsArray \
                                                            ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {!([info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)] || 
        [info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error : The command $_hltCmdName requires -port_handle or -handle."
        return $returnKeyedList
    }
        
    if {[info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)] &&
        [info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_hanlde)]} {
            ::sth::sthCore::processError returnKeyedList "The options -port_handle or -handle are mutually exclusive."
            return $returnKeyedList
    }
    
    
    set retVal [catch {
        set action $::sth::vxlanEvpnOverlay::userArgsArray(action)
        set device_list ""
        if {[info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)]} {
            set device_list $::sth::vxlanEvpnOverlay::userArgsArray(handle)
        } else {
            set port_list $::sth::vxlanEvpnOverlay::userArgsArray(port_handle)
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
            ::sth::sthCore::invoke stc::perform VxlanEvpnStart -handlelist $device_list
        } else {
            ::sth::sthCore::invoke stc::perform VxlanEvpnStop -handlelist $device_list
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList "Error in $action\ing vxlan device : $returnedString"
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $returnKeyedList
}

proc ::sth::emulation_vxlan_evpn_overlay_stats {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_evpn_overlay_stats" $args
    #get the result under the VxlanVtepConfig
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    variable ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList
    array unset ::sth::vxlanEvpnOverlay::userArgsArray
    array set ::sth::vxlanEvpnOverlay::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_evpn_overlay_stats"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlanEvpnOverlay::vxlanEvpnOverlayTable $args \
                                                            ::sth::vxlanEvpnOverlay:: \
                                                            emulation_vxlan_evpn_overlay_stats \
                                                            ::sth::vxlanEvpnOverlay::userArgsArray \
                                                            ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {!([info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)] || 
        [info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error : The command $_hltCmdName requires -port_handle or -handle."
        return $returnKeyedList
    }
        
    if {[info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)] &&
        [info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_hanlde)]} {
            ::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires: the options -port_handle or -handle are mutually exclusive."
            return $returnKeyedList
    }
    if {[catch {::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get vxlan stats : $err"
    }
    return $returnKeyedList
}
########################VXLAN EVPN Overlay Wizard APIs#####################################
proc ::sth::emulation_vxlan_evpn_overlay_port_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_evpn_overlay_port_config" $args
    
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    variable ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList
    array unset ::sth::vxlanEvpnOverlay::userArgsArray
    array set ::sth::vxlanEvpnOverlay::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_evpn_overlay_port_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlanEvpnOverlay::vxlanEvpnOverlayTable $args \
                                                            ::sth::vxlanEvpnOverlay:: \
                                                            emulation_vxlan_evpn_overlay_port_config \
                                                            ::sth::vxlanEvpnOverlay::userArgsArray \
                                                            ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    
	if {![info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_handle)]} {
        return  -code 1 -errorcode -1 "Error : The command emulation_vxlan_evpn_overlay_port_config requires -port_handle."
    }  
    set mode $::sth::vxlanEvpnOverlay::userArgsArray(mode)   
    if {[catch {::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_port_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_vxlan_evpn_overlay_port_config : $err"
    }
    return $returnKeyedList
}

proc ::sth::emulation_nonvxlan_evpn_overlay_port_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_nonvxlan_evpn_overlay_port_config" $args
    
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    variable ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList
    array unset ::sth::vxlanEvpnOverlay::userArgsArray
    array set ::sth::vxlanEvpnOverlay::userArgsArray {}
    
    set _hltCmdName "emulation_nonvxlan_evpn_overlay_port_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlanEvpnOverlay::vxlanEvpnOverlayTable $args \
                                                            ::sth::vxlanEvpnOverlay:: \
                                                            emulation_nonvxlan_evpn_overlay_port_config \
                                                            ::sth::vxlanEvpnOverlay::userArgsArray \
                                                            ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
	if {![info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_handle)]} {
        return  -code 1 -errorcode -1 "Error : The command emulation_nonvxlan_evpn_overlay_port_config requires -port_handle."
    }
        
    set mode $::sth::vxlanEvpnOverlay::userArgsArray(mode)   
    if {[catch {::sth::vxlanEvpnOverlay::emulation_nonvxlan_evpn_overlay_port_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_nonvxlan_evpn_overlay_port_config : $err"
    }
    return $returnKeyedList
}

proc ::sth::emulation_vxlan_evpn_overlay_wizard_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_vxlan_evpn_overlay_wizard_config" $args
    
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    variable ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList
    array unset ::sth::vxlanEvpnOverlay::userArgsArray
    array set ::sth::vxlanEvpnOverlay::userArgsArray {}
    
    set _hltCmdName "emulation_vxlan_evpn_overlay_wizard_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::vxlanEvpnOverlay::vxlanEvpnOverlayTable $args \
                                                            ::sth::vxlanEvpnOverlay:: \
                                                            emulation_vxlan_evpn_overlay_wizard_config \
                                                            ::sth::vxlanEvpnOverlay::userArgsArray \
                                                            ::sth::vxlanEvpnOverlay::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    
    # for stream blocks created by VXLAN "auto" mode, need to update some data structures for traffic APIs.
    set ::sth::Session::fillTraffic "unset"
    if {[string match -nocase $::sth::vxlanEvpnOverlay::userArgsArray(create_traffic) "true"] && 
        [string match -nocase $::sth::vxlanEvpnOverlay::userArgsArray(traffic_config) "auto"] } {
        set ::sth::Session::fillTraffic "set"
    }
    
    set mode $::sth::vxlanEvpnOverlay::userArgsArray(mode)   
    if {[catch {::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_wizard_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_vxlan_evpn_overlay_wizard_config : $err"
    }
    if {[catch {::sth::sthCore::doStcApply } retHandle]} {
           ::sth::sthCore::processError trafficKeyedList "Apply failed. $retHandle" {}
    }
    return $returnKeyedList
}

