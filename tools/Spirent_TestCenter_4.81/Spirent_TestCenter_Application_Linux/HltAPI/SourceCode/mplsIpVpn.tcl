namespace eval ::sth:: {
}

namespace eval ::sth::mplsIpVpn:: {
}

proc ::sth::emulation_mpls_ip_vpn_provider_port_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_mpls_ip_vpn_provider_port_config" $args

    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::sortedSwitchPriorityList
    array unset ::sth::mplsIpVpn::userArgsArray
    array set ::sth::mplsIpVpn::userArgsArray {}

    set _hltCmdName "emulation_mpls_ip_vpn_provider_port_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::mplsIpVpn::mplsIpVpnTable $args \
                                                            ::sth::mplsIpVpn:: \
                                                            emulation_mpls_ip_vpn_provider_port_config \
                                                            ::sth::mplsIpVpn::userArgsArray \
                                                            ::sth::mplsIpVpn::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::mplsIpVpn::emulation_mpls_ip_vpn_provider_port_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing mpls provider side port config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_provider_port_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::mplsIpVpn::userArgsArray(mode)
    
    ::sth::mplsIpVpn::emulation_mpls_ip_vpn_provider_port_config_$mode myReturnKeyedList
}

proc ::sth::emulation_mpls_ip_vpn_cust_port_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_mpls_ip_vpn_cust_port_config" $args

    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::sortedSwitchPriorityList
    array unset ::sth::mplsIpVpn::userArgsArray
    array set ::sth::mplsIpVpn::userArgsArray {}

    set _hltCmdName "emulation_mpls_ip_vpn_cust_port_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::mplsIpVpn::mplsIpVpnTable $args \
                                                            ::sth::mplsIpVpn:: \
                                                            emulation_mpls_ip_vpn_cust_port_config \
                                                            ::sth::mplsIpVpn::userArgsArray \
                                                            ::sth::mplsIpVpn::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::mplsIpVpn::emulation_mpls_ip_vpn_cust_port_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing mpls customer side port config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_cust_port_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::mplsIpVpn::userArgsArray(mode)
    
    ::sth::mplsIpVpn::emulation_mpls_ip_vpn_cust_port_config_$mode myReturnKeyedList
}


proc ::sth::emulation_mpls_ip_vpn_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_mpls_ip_vpn_config" $args

    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::sortedSwitchPriorityList
    array unset ::sth::mplsIpVpn::userArgsArray
    array set ::sth::mplsIpVpn::userArgsArray {}

    set _hltCmdName "emulation_mpls_ip_vpn_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::mplsIpVpn::mplsIpVpnTable $args \
                                                            ::sth::mplsIpVpn:: \
                                                            emulation_mpls_ip_vpn_config \
                                                            ::sth::mplsIpVpn::userArgsArray \
                                                            ::sth::mplsIpVpn::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::mplsIpVpn::emulation_mpls_ip_vpn_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList " : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::mplsIpVpn::userArgsArray(mode)
    
    ::sth::mplsIpVpn::emulation_mpls_ip_vpn_config_$mode myReturnKeyedList
}

proc ::sth::emulation_mpls_ip_vpn_control { args } {

    ::sth::sthCore::Tracker "::sth::emulation_mpls_ip_vpn_control" $args

    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::sortedSwitchPriorityList
    array unset ::sth::mplsIpVpn::userArgsArray
    array set ::sth::mplsIpVpn::userArgsArray {}

    set _hltCmdName "emulation_mpls_ip_vpn_control"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::mplsIpVpn::mplsIpVpnTable $args \
                                                            ::sth::mplsIpVpn:: \
                                                            emulation_mpls_ip_vpn_control \
                                                            ::sth::mplsIpVpn::userArgsArray \
                                                            ::sth::mplsIpVpn::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::mplsIpVpn::emulation_mpls_ip_vpn_control_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing mpls network control : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_control_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set action $::sth::mplsIpVpn::userArgsArray(action)
    
    if {![info exists ::sth::mplsIpVpn::userArgsArray(handle)] && ![info exists ::sth::mplsIpVpn::userArgsArray(port_handle)]} {
        return -code 1 -errorcode -1 "Either handle or port_handle need to be specified"
    }
    ::sth::mplsIpVpn::emulation_mpls_ip_vpn_control_$action myReturnKeyedList
}

proc ::sth::emulation_mpls_ip_vpn_info { args } {

    ::sth::sthCore::Tracker "::sth::emulation_mpls_ip_vpn_info" $args

    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::sortedSwitchPriorityList
    array unset ::sth::mplsIpVpn::userArgsArray
    array set ::sth::mplsIpVpn::userArgsArray {}

    set _hltCmdName "emulation_mpls_ip_vpn_info"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::mplsIpVpn::mplsIpVpnTable $args \
                                                            ::sth::mplsIpVpn:: \
                                                            emulation_mpls_ip_vpn_info \
                                                            ::sth::mplsIpVpn::userArgsArray \
                                                            ::sth::mplsIpVpn::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing mpls info : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::mplsIpVpn::userArgsArray(mode)

    ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_$mode myReturnKeyedList
}
