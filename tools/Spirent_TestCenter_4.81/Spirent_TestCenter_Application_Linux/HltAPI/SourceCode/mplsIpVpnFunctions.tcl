namespace eval ::sth::mplsIpVpn {
    variable switchHandleArray
    variable keyedList
    set createResultQuery 0
    set resultDataSetHandleList {}
}
# provider side port config functions
proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_provider_port_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $userArgsArray(port_handle)
    } else {
        return -code 1 -errorcode -1 "port_handle needed for create mode."
    }
    if {[catch {set VpnRfc2547GenParamsHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnRfc2547GenParams ]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get VpnRfc2547GenParams Handle. Error: $errMsg"  {}

    }
    if {[string equal "" $VpnRfc2547GenParamsHnd]} {
        if {[catch {set VpnRfc2547GenParamsHnd [::sth::sthCore::invoke stc::create "VpnRfc2547GenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            return -code 1 -errorcode -1 "Unable to create VpnRfc2547GenParams Handle. Error: $errMsg"  {}
        }
    }
    set VpnRfc2547GenCorePortParamsHndList [::sth::sthCore::invoke stc::get $VpnRfc2547GenParamsHnd -Children-VpnRfc2547GenCorePortParams]
    set VpnRfc2547GenCorePortParamsHnd ""
    foreach CorePortParamsHnd $VpnRfc2547GenCorePortParamsHndList {
        if {$CorePortParamsHnd ne ""} {
            set CorePortHnd [::sth::sthCore::invoke stc::get $CorePortParamsHnd -AffiliationPort-Targets]
            if {[string equal $portHandle $CorePortHnd]} {
                set VpnRfc2547GenCorePortParamsHnd $corePortParamsHnd
            }
        }
    }
    if {[string equal "" $VpnRfc2547GenCorePortParamsHnd]} {
        if {[catch {set VpnRfc2547GenCorePortParamsHnd [::sth::sthCore::invoke stc::create "VpnRfc2547GenCorePortParams" -under $VpnRfc2547GenParamsHnd]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create VpnRfc2547GenCorePortParams under $VpnRfc2547GenParamsHnd. Error: $errMsg"  {}
        }
        if {[catch {::sth::sthCore::invoke stc::config $VpnRfc2547GenCorePortParamsHnd "-AffiliationPort-Targets $portHandle -Active true"} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config -AffiliationPort-Targets to $VpnRfc2547GenCorePortParamsHnd. Error: $errMsg"  {}
        }
    }
    
    set functionsToRun [getFunctionToRun emulation_mpls_ip_vpn_provider_port_config create] 
    foreach func $functionsToRun {
        $func $VpnRfc2547GenCorePortParamsHnd create
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_provider_port_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    if { ![::info exists ::sth::mplsIpVpn::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for delete mode."
    } else {
        set routerHndList $::sth::mplsIpVpn::userArgsArray(handle)
        foreach router $routerHndList {
            if {[catch {::sth::sthCore::invoke ::sth::sthCore::invoke stc::delete $router} errMsg]} {
                return -code 1 -errorcode -1  "Unable to delete $router. Error: $errMsg"  {}
            }
        }
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
        return $myReturnKeyedList
    }
}

proc ::sth::mplsIpVpn::coreport_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_provider_port_config coreport_config $mode $handle]
    lappend optionValueList -Active true
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $handle. Error: $errMsg"  {}
        }
    }
}

# customer side port config functions
proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_cust_port_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $userArgsArray(port_handle)
    } else {
        return -code 1 -errorcode -1 "port_handle needed for create mode."
    }
    if {[catch {set VpnRfc2547GenParamsHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnRfc2547GenParams ]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get VpnRfc2547GenParams Handle. Error: $errMsg"  {}
    }
    if {[string equal "" $VpnRfc2547GenParamsHnd]} {
        if {[catch {set VpnRfc2547GenParamsHnd [::sth::sthCore::invoke stc::create "VpnRfc2547GenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create VpnRfc2547GenParams Handle. Error: $errMsg"  {}
        }
    }
    set VpnRfc2547GenCustPortParamsHndList [::sth::sthCore::invoke stc::get $VpnRfc2547GenParamsHnd -Children-VpnRfc2547GenCustPortParams]
    set VpnRfc2547GenCustPortParamsHnd ""
    foreach CustPortParamsHnd $VpnRfc2547GenCustPortParamsHndList {
        if {$CustPortParamsHnd ne ""} {
            set CustPortHnd [::sth::sthCore::invoke stc::get $CustPortParamsHnd -AffiliationPort-Targets]
            if {[string equal $portHandle $CustPortHnd]} {
                set VpnRfc2547GenCustPortParamsHnd $custPortParamsHnd
            }
        }
    }
    if {[string equal "" $VpnRfc2547GenCustPortParamsHnd]} {
        if {[catch {set VpnRfc2547GenCustPortParamsHnd [::sth::sthCore::invoke stc::create "VpnRfc2547GenCustPortParams" -under $VpnRfc2547GenParamsHnd]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create VpnRfc2547GenCustPortParams under $VpnRfc2547GenParamsHnd. Error: $errMsg"  {}
        }
        if {[catch {::sth::sthCore::invoke stc::config $VpnRfc2547GenCustPortParamsHnd "-AffiliationPort-Targets $portHandle"} errMsg]} {
            return -code 1 -errorcode -1   "Unable to config -AffiliationPort-Targets to $VpnRfc2547GenCustPortParamsHnd. Error: $errMsg"  {}
        }
    }
    
    set functionsToRun [getFunctionToRun emulation_mpls_ip_vpn_cust_port_config create] 
    foreach func $functionsToRun {
        $func $VpnRfc2547GenCustPortParamsHnd create
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_cust_port_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    if { ![::info exists ::sth::mplsIpVpn::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for delete mode."
        keylset myReturnKeyedList status $::sth::sthCore::FAILURE
        return $myReturnKeyedList
    } else {
        set routerHndList $::sth::mplsIpVpn::userArgsArray(handle)
        foreach router $routerHndList {
            if {[catch {::sth::sthCore::invoke ::sth::sthCore::invoke stc::delete $router} errMsg]} {
                return -code 1 -errorcode -1   "Unable to delete $router. Error: $errMsg"  {}
            }
        }
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
        return $myReturnKeyedList
    }
}

proc ::sth::mplsIpVpn::custport_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_cust_port_config custport_config $mode $handle]
    lappend optionValueList -Active true
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $handle. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

# MPLS network topology config function

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set VpnRfc2547GenParamsHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnRfc2547GenParams]

    if {[string equal "" $VpnRfc2547GenParamsHnd]} {
        if {[catch {set VpnRfc2547GenParamsHnd [::sth::sthCore::invoke stc::create "VpnRfc2547GenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create VpnRfc2547GenParams Handle. Error: $errMsg"  {}
        }
    }
    
    set functionsToRun [getFunctionToRun emulation_mpls_ip_vpn_config create]
    foreach func $functionsToRun {
        $func $VpnRfc2547GenParamsHnd create
    }
    set hdlKeyList [expand_config $VpnRfc2547GenParamsHnd]

    # get the existing resultDataSet handle
    if {[catch {set perResultDataSetHandles [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get ResultDataSet Handle. Error: $errMsg"  {}
    }

    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: IsisRouterConfig IsisRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe IsisRouterResults. Error: $errMsg"  
    }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: BgpRouterConfig BgpRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe BgpRouterResults. Error: $errMsg"  
    }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: LdpRouterConfig LdpRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe LdpRouterResults. Error: $errMsg"  
    }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: RsvpRouterConfig RsvpRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe RsvpRouterResults. Error: $errMsg"  
        }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: Ospfv2RouterConfig Ospfv2RouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe Ospfv2RouterResults.  Error: $errMsg"  
    }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: Ospfv3RouterConfig Ospfv3RouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe Ospfv3RouterResults.  Error: $errMsg"  
    }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: RipRouterConfig RipRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe RipRouterResults. Error: $errMsg"  

    }
    set ::sth::mplsIpVpn::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::mplsIpVpn:: BfdRouterConfig BfdRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe BfdRouterResults.  Error: $errMsg"  
    }
    set ::sth::mplsIpVpn::createResultQuery 0
    
    set resultTypeList {ldp ripv4 isis rsvp bgp bfd ospfv2 ospfv3}
    foreach resultType $resultTypeList {
        summaryResultsDataSetSubscribe $resultType myreturnKeyedList
    }
    if {[catch {set resultDataSetHandles [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get ResultDataSet Handle. Error: $errMsg"  {}
    }

    #get new created resultdataset handles within mpls config 
    foreach dataSetHandle $perResultDataSetHandles {
        set index [lsearch $resultDataSetHandles $dataSetHandle]
        if { $index > -1 } {
            set resultDataSetHandles [lreplace $resultDataSetHandles $index $index]
        }
    }
    set ::sth::mplsIpVpn::resultDataSetHandleList $resultDataSetHandles

    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    keylset myReturnKeyedList handle $hdlKeyList
    
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""

    array set objArr {
        vpn "VpnIdGroup"
        ce_router "Router"
        rr_router "Router"
        p_router "Router"
        pe_router "Router"
    }

    # delete the streamblock firstly
    set handles [keylget ::sth::mplsIpVpn::userArgsArray(handle) stream_id]
    foreach handle $handles {
        ::sth::sthCore::isHandleValid $handle streamblock
        if {[catch {::sth::sthCore::invoke stc::delete $handle} eMsg]} {
            return -code 1 -errorcode -1 "Internal Command Error while deleting $handle. Error: $eMsg"
        }
    }

    # delete the resultdataset for every protocol 
    
    if {[llength $::sth::mplsIpVpn::resultDataSetHandleList] > 0 } {
        foreach dataSetHandle $::sth::mplsIpVpn::resultDataSetHandleList {
            if {[catch {::sth::sthCore::invoke stc::delete $dataSetHandle} eMsg]} {
                return -code 1 -errorcode -1 "Internal Command Error while deleting $dataSetHandle. Error: $eMsg"
            }
        }
    }

    # delete routers

    foreach obj [array names objArr] {
        set handles [keylget ::sth::mplsIpVpn::userArgsArray(handle) $obj]
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            if {[catch {::sth::sthCore::invoke stc::delete $handle} eMsg]} {
                return -code 1 -errorcode -1 "Internal Command Error while deleting $handle. Error: $eMsg"
            }
        }
    }
    if {[catch {set VpnMplsGenHandle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnRfc2547GenParams]} errMsg]} {
        return -code 1 -errorcode -1  "Internal Command Error while geting VpnRfc2547GenParams.Error: $errMsg"
    } else {
        if {[catch {::sth::sthCore::invoke stc::delete $VpnMplsGenHandle} errMsg]} {
            return -code 1 -errorcode -1  "Internal Command Error while deleting $VpnMplsGenHandle.Error: $errMsg"
        }
    }

    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
}

proc ::sth::mplsIpVpn::mpls_ip_vpn_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList
    
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config mpls_ip_vpn_config $mode $handle]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $handle. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::ospfv2session_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnIgpOspfv2SessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnIgpOspfv2SessionParams]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get VpnIgpOspfv2SessionParams Handle.Error: $errMsg" 
    }
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config ospfv2session_config $mode $vpnIgpOspfv2SessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnIgpOspfv2SessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnIgpOspfv2SessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::ospfv2auth_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnIgpOspfv2SessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnIgpOspfv2SessionParams]} errMsg ]} {
        return -code 1 -errorcode -1  "Unable to get VpnIgpOspfv2SessionParams Handle.Error :$errMsg" 
    }
    if {[string length $vpnIgpOspfv2SessionParamsHnd] > 0} {
        if {[catch {set ospfv2AuthenticationParamsHnd [::sth::sthCore::invoke stc::get $vpnIgpOspfv2SessionParamsHnd -children-Ospfv2AuthenticationParams]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to get Ospfv2AuthenticationParams Handle .Error :$errMsg" 
        }
    } 
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config ospfv2auth_config $mode $ospfv2AuthenticationParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ospfv2AuthenticationParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $ospfv2AuthenticationParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::isissession_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnIgpIsisSessionParamsHnd [::sth::sthCore::invoke stc::get $handle -children-VpnIgpIsisSessionParams]} errMsg]} {
        return -code 1 -errorcode -1 "Unable to get VpnIgpIsisSessionParams Handle.Error: $errMsg " 
    }
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config isissession_config $mode $vpnIgpIsisSessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnIgpIsisSessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnIgpIsisSessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::isisauth_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnIgpIsisSessionParamsHnd [::sth::sthCore::invoke stc::get $handle -children-VpnIgpIsisSessionParams]} ]} {
        return -code 1 -errorcode -1 "Unable to get VpnIgpIsisSessionParams Handle." 
    }
    if {[string length $vpnIgpIsisSessionParamsHnd] > 0} {
        if {[catch {set isisAuthenticationParamsHnd [::sth::sthCore::invoke stc::get $vpnIgpIsisSessionParamsHnd -children-IsisAuthenticationParams]} ]} {
        return -code 1 -errorcode -1 "Unable to get IsisAuthenticationParams Handle. " 
        }
    } 
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config isisauth_config $mode $isisAuthenticationParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $isisAuthenticationParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $isisAuthenticationParamsHnd. Error: $errMsg"  {}
        }
        ::sth::sthCore::invoke stc::config $isisAuthenticationParamsHnd $optionValueList
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::rsvpsession_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnmplsRsvpSessionParamsHnd [::sth::sthCore::invoke stc::get $handle -children-VpnmplsRsvpSessionParams ]} ]} {
        return -code 1 -errorcode -1  "Unable to get VpnmplsRsvpSessionParams Handle." {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config rsvpsession_config $mode $vpnmplsRsvpSessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnmplsRsvpSessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnmplsRsvpSessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::ldpsession_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnmplsLdpSessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnmplsLdpSessionParams]} ]} {
        return -code 1 -errorcode -1 "Unable to get VpnmplsLdpSessionParams Handle." 
        }
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config ldpsession_config $mode $vpnmplsLdpSessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnmplsLdpSessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnmplsLdpSessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::ldpauth_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnmplsLdpSessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnmplsLdpSessionParams]} ]} {
        return -code 1 -errorcode -1  "Unable to get VpnmplsLdpSessionParams Handle." 
        }
    if {[string length $vpnmplsLdpSessionParamsHnd] > 0} {
        if {[catch {set ldpAuthenticationParamsHnd [::sth::sthCore::invoke stc::get $vpnmplsLdpSessionParamsHnd -children-LdpAuthenticationParams]} ]} {
            return -code 1 -errorcode -1  "Unable to get LdpAuthenticationParams Handle. " {}
        }
    } 
    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config ldpauth_config $mode $ldpAuthenticationParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ldpAuthenticationParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $ldpAuthenticationParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::expand_config { VpnMplsGenHandle } {
    
    variable ::sth::mplsIpVpn::keyedList

    set preStreamList ""
    if {[catch {set portHndList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
        return -code 1 -errorcode -1 "Unable to fetch -Children-Port from project. Error: $errMsg"
    }
    foreach portHnd $portHndList {
        if {[catch {set streamHnd [::sth::sthCore::invoke stc::get $portHnd -Children-StreamBlock]} errMsg]} {
            return -code 1 -errorcode -1 "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg"
        }
        if { $streamHnd != "" } {
            set preStreamList [concat $preStreamList $streamHnd]
        }
    }
    if {[catch {set preChildrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to fetch -Children from project. Error: $errMsg"
    }
    if {[catch {::sth::sthCore::invoke stc::perform RtgTestGenConfigExpandAndRunCommand -clearportconfig no -genparams $VpnMplsGenHandle} errMsg] } {
        return -code 1 -errorcode -1  "Unable to expand 6PV or 6VPE configuration .Error: $errMsg"
    }
    if {[catch {::sth::sthCore::invoke stc::apply} errMsg] } {
        return -code 1 -errorcode -1  "Unable to apply.Error: $errMsg"
    }

    
    set streamList ""
    if {[catch {set portHndList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to fetch -Children-Port from project.Error: $errMsg" 
    }
    foreach portHnd $portHndList {
        if {[catch {set streamHnd [::sth::sthCore::invoke stc::get $portHnd -Children-StreamBlock]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to fetch -Children-StreamBlock from $portHnd.Error: $errMsg" 
        }
        if { $streamHnd != "" } {
            set streamList [concat $streamList $streamHnd]
        }
    }
    if {[catch {set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
        return -code 1 -errorcode -1   "Unable to fetch -Children from project.Error: $errMsg "
    }
    
    #get new created devices handles within mpls config 
    foreach stream $preStreamList {
        set x [lsearch $streamList $stream]
        if { $x > -1 } {
            set streamList [lreplace $streamList $x $x]
        }
    }
    set childrenList [split $childrenStr]
    foreach childHnd $preChildrenStr {
        set x [lsearch $childrenList $childHnd]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    set vpnIdGroupHnd ""
    set emulatedDeviceHnd ""
    set ipv4GroupHnd ""
    set vpnSiteInfoHnd ""
    set ceRouter ""
    set pRouter ""
    set rrRouter ""
    set peRouter ""
    set ospfv2Session ""
    set ospfv3Session ""
    set isisSession ""
    set ldpSession ""
    set rsvpSession ""
    set bgpSession ""
    set bfdSession ""
    set ripSession ""

    foreach child $childrenList {
        switch -glob -- $child {
            vpnidgroup* {lappend vpnIdGroupHnd $child}
            emulateddevice* {lappend emulatedDeviceHnd $child}
            router* {lappend emulatedDeviceHnd $child}
            vpnsiteinfo6pe* {lappend vpnSiteInfoHnd $child}
        }
    }
    foreach deviceHnd $emulatedDeviceHnd {
        if {$deviceHnd ne ""} {
            if {[catch {set deviceName [::sth::sthCore::invoke stc::get $deviceHnd -Name]} errMsg]} {
                return -code 1 -errorcode -1 "Unable to fetch -Name from $device.  " {}
            }
        
            if {$deviceName ne ""} {
                set ospfv2Session [concat $ospfv2Session [::sth::sthCore::invoke stc::get $deviceHnd -Children-Ospfv2RouterConfig]]
                set ospfv3Session [concat $ospfv3Session [::sth::sthCore::invoke stc::get $deviceHnd -Children-Ospfv3RouterConfig]]
                set isisSession [concat $isisSession [::sth::sthCore::invoke stc::get $deviceHnd -Children-IsisRouterConfig]]
                set ldpSession [concat $ldpSession [::sth::sthCore::invoke stc::get $deviceHnd -Children-LdpRouterConfig]]
                set rsvpSession [concat $rsvpSession [::sth::sthCore::invoke stc::get $deviceHnd -Children-RsvpRouterConfig]]
                set bgpSession [concat $bgpSession [::sth::sthCore::invoke stc::get $deviceHnd -Children-BgpRouterConfig]]
                set bfdSession [concat $bfdSession [::sth::sthCore::invoke stc::get $deviceHnd -Children-BfdRouterConfig]]
                set ripSession [concat $ripSession [::sth::sthCore::invoke stc::get $deviceHnd -Children-RipRouterConfig]]
            }
        }
        
        switch -glob -- $deviceName {
            PE* {lappend peRouter $deviceHnd}
            P* {lappend pRouter $deviceHnd}
            CE* {lappend ceRouter $deviceHnd}
            RR* {lappend rrRouter $deviceHnd}
        }
    }
    set handleKeyList ""
    
    keylset handleKeyList  vpn $vpnIdGroupHnd
    #keylset handleKeyList  vpnsite $vpnSiteInfoHnd
    keylset handleKeyList  ce_router $ceRouter
    keylset handleKeyList  p_router $pRouter
    keylset handleKeyList  rr_router $rrRouter
    keylset handleKeyList  pe_router $peRouter
    keylset handleKeyList  ospfv2 $ospfv2Session
    keylset handleKeyList  ospfv3 $ospfv3Session
    keylset handleKeyList  isis $isisSession
    keylset handleKeyList  ldp $ldpSession
    keylset handleKeyList  rsvp $rsvpSession
    keylset handleKeyList  bgp $bgpSession
    keylset handleKeyList  bfd $bfdSession
    keylset handleKeyList  rip $ripSession
    keylset handleKeyList  stream_id $streamList
    return $handleKeyList
}

#LSP ping functions

proc ::sth::mplsIpVpn::lsp_ping_core_tunnel_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnLspPingGenIpv4CoreParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnLspPingGenIpv4CoreParams]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get VpnLspPingGenIpv4CoreParams Handle.Error: $errMsg" 
    }
    if {$vpnLspPingGenIpv4CoreParamsHnd == ""} {
        set vpnLspPingGenIpv4CoreParamsHnd [::sth::sthCore::invoke stc::create VpnLspPingGenIpv4CoreParams -under $handle]}

    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config lsp_ping_core_tunnel_config $mode $vpnLspPingGenIpv4CoreParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnLspPingGenIpv4CoreParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnLspPingGenIpv4CoreParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

proc ::sth::mplsIpVpn::lsp_ping_vpn_tunnel_config {handle mode} {

    variable ::sth::mplsIpVpn::keyedList

    if {[catch {set vpnLspPingGenIpv4VpnParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnLspPingGenIpv4VpnParams]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get VpnLspPingGenIpv4VpnParams Handle.Error: $errMsg" 
    }

    if {$vpnLspPingGenIpv4VpnParamsHnd == ""} {
        set vpnLspPingGenIpv4VpnParamsHnd [::sth::sthCore::invoke stc::create VpnLspPingGenIpv4VpnParams -under $handle]}

    set optionValueList [getStcOptionValueList emulation_mpls_ip_vpn_config lsp_ping_vpn_tunnel_config $mode $vpnLspPingGenIpv4VpnParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnLspPingGenIpv4VpnParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnLspPingGenIpv4VpnParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::mplsIpVpn::keyedList handle $handle
}

# MPLS control functions

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_control_start {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""

    set routerHandles [getRouterHandles]
    if {[llength $routerHandles] < 0 } {
        return -code 1 -errorcode -1 "Unable to get router Handle."
        }
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStartCommand -DeviceList $routerHandles} eMsg]} {
        return -code 1 -errorcode -1  "Internal Command Error while Start $routerHandles. Error: $eMsg"
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_control_stop {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    set routerHandles [getRouterHandles]
    if {[llength $routerHandles] < 0 } {
        return -code 1 -errorcode -1 "Unable to get router Handle."
        }
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStopCommand  -DeviceList $routerHandles} eMsg]} {
        return -code 1 -errorcode -1  "Internal Command Error while Start $routerHandles. Error: $eMsg"
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

# MPLS info functions

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_isis {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList isis_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList

}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_ospfv2 {returnKeyedList} {

    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList ospfv2_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_ospfv3 {returnKeyedList} {

    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList ospfv3_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_rsvp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList rsvp_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_bfd {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList bfd_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}
proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_bgp {returnKeyedList} {

    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList bgp_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}
proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_rip {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList rip_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_ldp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set resultsType $::sth::mplsIpVpn::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList ldp_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}


proc ::sth::mplsIpVpn::emulation_mpls_ip_vpn_info_summary {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::mplsIpVpn::userArgsArray
    variable ::sth::mplsIpVpn::keyedList
    set ::sth::mplsIpVpn::keyedList ""
    
    set portHndList ""
    if {[info exists ::sth::mplsIpVpn::userArgsArray(port_handle)]} {
        set portHndList $::sth::mplsIpVpn::userArgsArray(port_handle)
    } elseif {[info exists ::sth::mplsIpVpn::userArgsArray(handle)]} {
        set deviceHndList $::sth::mplsIpVpn::userArgsArray(handle) 
        foreach deviceHnd $deviceHndList {
            if {[catch {set portHnnd [::sth::sthCore::invoke stc::get $deviceHnd -AffiliationPort-Targets]} eMsg]} {
                return -code 1 -errorcode -1  "Unable to get port handle .Error: $eMsg"
            }
            if {[string length $portHnnd]} {
                set portHndList [concat $portHndList $portHnnd]
            }
        }
    }
    set summaryResults ""
    foreach portHnd $portHndList {
        keylset summaryResults ldp_summary.$portHnd [getSummaryResults $portHnd ldp]
        keylset summaryResults bgp_summary.$portHnd [getSummaryResults $portHnd bgp]
        keylset summaryResults bfd_summary.$portHnd [getSummaryResults $portHnd bfd]
        keylset summaryResults ospfv2_summary.$portHnd [getSummaryResults $portHnd ospfv2]
        keylset summaryResults ospfv3_summary.$portHnd [getSummaryResults $portHnd ospfv3]
        keylset summaryResults rsvp_summary.$portHnd [getSummaryResults $portHnd rsvp]
        keylset summaryResults rip_summary.$portHnd [getSummaryResults $portHnd ripv4]
        keylset summaryResults isis_summary.$portHnd [getSummaryResults $portHnd isis]
        keylset myReturnKeyedList summary $summaryResults
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

# mpls common functions
proc ::sth::mplsIpVpn::getFunctionToRun {mycmd mode} {

    variable sortedSwitchPriorityList
    set functionsToRun {}
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {

            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::mplsIpVpn:: $mycmd $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::mplsIpVpn:: $mycmd $switchname mode] "_none_"]} { 
                continue 
            }
            set func [::sth::sthCore::getModeFunc ::sth::mplsIpVpn:: $mycmd $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    return $functionsToRun
}

proc ::sth::mplsIpVpn::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::mplsIpVpn::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::mplsIpVpn:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::mplsIpVpn:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::mplsIpVpn:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                #check dependency
                #::sth::mplsIpVpn::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::mplsIpVpn::userArgsArray($opt)]} { continue }
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::mplsIpVpn:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::mplsIpVpn:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::mplsIpVpn:: $cmdType $opt $::sth::mplsIpVpn::userArgsArray($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::mplsIpVpn::userArgsArray($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::mplsIpVpn::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}

proc ::sth::mplsIpVpn::getRouterHandles {} {

    variable ::sth::mplsIpVpn::userArgsArray
    
    set handleList ""
    if {[info exists ::sth::mplsIpVpn::userArgsArray(handle)]} {
        set handleList $::sth::mplsIpVpn::userArgsArray(handle)
        foreach handle $handleList {
            if {[string first "emulateddevice" "$handle"] == 0 || [string first "router" "$handle"] == 0} {
                lappend handleList $handle
            }
        }
    } elseif {[info exists ::sth::mplsIpVpn::userArgsArray(port_handle)]} {
        set portList $::sth::mplsIpVpn::userArgsArray(port_handle)
        foreach portHandle $portList {
            if {[catch {set devices [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-Sources]} eMsg]} {
                return -code 1 -errorcode -1  "Unable to get router handles .Error: $eMsg"
            }
            foreach deviceHandle $devices {
                if {[string first "emulateddevice" "$deviceHandle"] == 0 || [string first "router" "$deviceHandle"] == 0} {
                    lappend handleList $deviceHandle
                }
            }
        }
    }
    
    return $handleList
}

proc ::sth::mplsIpVpn::getResults {handles mode} {
    
    set deviceHndList $handles
    set resultsType $mode
    set resultsPerPort ""
    set resultsPerDevice ""
    foreach deviceHnd $deviceHndList {
        if {[catch {set portHnd [::sth::sthCore::invoke stc::get $deviceHnd -AffiliationPort-Targets]} eMsg]} {
            return -code 1 -errorcode -1  "Unable to get port handles .Error: $eMsg"
        }
        if {[catch {set protocolHnd [::sth::sthCore::invoke stc::get $deviceHnd -Children-$resultsType\RouterConfig]} eMsg]} {
            return -code 1 -errorcode -1  "Unable to get $resultsType\RouterConfig .Error: $eMsg"
        }
        if {[string length $protocolHnd] > 0} {

            if {[catch {set resultsHnd [::sth::sthCore::invoke stc::get $protocolHnd -Children-$resultsType\RouterResults] } eMsg]} {
                return -code 1 -errorcode -1  "Unable to get $resultsType\RouterResults .Error: $eMsg"
            }

            if {[string length $resultsHnd]} {
                if {[catch {set resultsData [::sth::sthCore::invoke stc::get $resultsHnd] } eMsg]} {
                    return -code 1 -errorcode -1  "Unable to get $resultsHnd .Error: $eMsg"
                }
                if {[llength $resultsData] > 0} {
                    set resultsData [processResultsValue $resultsData]
                    keylset resultsPerPort $portHnd.$deviceHnd $resultsData
                }
            }
        }
    }
    return $resultsPerPort
}

proc ::sth::mplsIpVpn::getSummaryResults {handle type} {
    
    set resultsData ""
    if {[catch {set summaryResults [::sth::sthCore::invoke stc::get $handle -Children-$type\statesummary]} eMsg]} {
        return -code 1 -errorcode -1 "Unable to get $type summary results handle . Error: $eMsg"
    }
    if {[string length $summaryResults]} {
        if {[catch {set resultsData [::sth::sthCore::invoke stc::get $summaryResults]} eMsg]} {
            return -code 1 -errorcode -1  "Unable to get $type summary results data. Error: $eMsg"
        }
        set resultsData [processResultsValue $resultsData]
    }
    return $resultsData
}

proc ::sth::mplsIpVpn::summaryResultsDataSetSubscribe {summaryType returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    
    if {[catch {set resultDataSet [::sth::sthCore::invoke stc::create ResultDataSet -under $::sth::GBLHNDMAP(project)]} createStatus]} {
        return -code 1 -errorcode -1 "Internal Command Error while creating the resultDataSet under $::sth::GBLHNDMAP(project), Error:$createStatus" {}
        keylset myReturnKeyedList status $::sth::sthCore::FAILURE
        return $myReturnKeyedList
    }

    if {[catch {set ResultQuery [::sth::sthCore::invoke stc::create ResultQuery -under $resultDataSet -ConfigClassId "port" -ResultClassId $summaryType\statesummary ]} createStatus]} {
                return -code 1 -errorcode -1 "Internal Command Error while creating the ResultQuery under $resultDataSet, Error:$createStatus" {}
    }
}

proc ::sth::mplsIpVpn::processResultsValue {input} {
    
    set retVal ""
    foreach {attr val} $input {
        set attr [string range $attr 1 end]
        if {[string match -nocase $attr "parent"] || [string match -nocase $attr "resultchild-Sources"] || [string match -nocase $attr "Name"] || [string match -nocase $attr "Active"] } {
            continue
        }
        keylset retVal $attr $val
    }
    return $retVal
}

