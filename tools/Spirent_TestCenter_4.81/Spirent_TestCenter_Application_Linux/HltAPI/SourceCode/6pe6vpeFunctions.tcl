namespace eval ::sth::6pe6vpe:: {
    variable switchHandleArray
    variable keyedList
    set createResultQuery 0
    set resultDataSetHandleList {}
}
# provider side port config functions
proc ::sth::6pe6vpe::emulation_6pe_6vpe_provider_port_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $userArgsArray(port_handle)
    } else {
        return -code 1 -errorcode -1 "port_handle needed for create mode."
    }
    if {[catch {set vpn6PeGenParamsHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Vpn6PeGenParams ]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get Vpn6PeGenParams Handle. Error: $errMsg"  {}

    }
    if {[string equal "" $vpn6PeGenParamsHnd]} {
        if {[catch {set vpn6PeGenParamsHnd [::sth::sthCore::invoke stc::create "Vpn6PeGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            return -code 1 -errorcode -1 "Unable to create Vpn6PeGenParams Handle. Error: $errMsg"  {}
        }
    }
    set Vpn6PeGenCorePortParamsHndList [::sth::sthCore::invoke stc::get $vpn6PeGenParamsHnd -Children-Vpn6PeGenCorePortParams]
    set Vpn6PeGenCorePortParamsHnd ""
    foreach CorePortParamsHnd $Vpn6PeGenCorePortParamsHndList {
        if {$CorePortParamsHnd ne ""} {
            set CorePortHnd [::sth::sthCore::invoke stc::get $CorePortParamsHnd -AffiliationPort-Targets]
            if {[string equal $portHandle $CorePortHnd]} {
                set Vpn6PeGenCorePortParamsHnd $corePortParamsHnd
            }
        }
    }
    if {[string equal "" $Vpn6PeGenCorePortParamsHnd]} {
        if {[catch {set Vpn6PeGenCorePortParamsHnd [::sth::sthCore::invoke stc::create "Vpn6PeGenCorePortParams" -under $vpn6PeGenParamsHnd]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create Vpn6PeGenCorePortParams under $vpn6PeGenParamsHnd. Error: $errMsg"  {}
        }
        if {[catch {::sth::sthCore::invoke stc::config $Vpn6PeGenCorePortParamsHnd "-AffiliationPort-Targets $portHandle -Active true"} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config -AffiliationPort-Targets to $Vpn6PeGenCorePortParamsHnd. Error: $errMsg"  {}
        }
    }
    
    set functionsToRun [getFunctionToRun emulation_6pe_6vpe_provider_port_config create] 
    foreach func $functionsToRun {
        $func $Vpn6PeGenCorePortParamsHnd create
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_provider_port_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    if { ![::info exists ::sth::6pe6vpe::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for delete mode."
    } else {
        set routerHndList $::sth::6pe6vpe::userArgsArray(handle)
        foreach router $routerHndList {
            if {[catch {::sth::sthCore::invoke ::sth::sthCore::invoke stc::delete $router} errMsg]} {
                return -code 1 -errorcode -1  "Unable to delete $router. Error: $errMsg"  {}
            }
        }
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
        return $myReturnKeyedList
    }
}

proc ::sth::6pe6vpe::coreport_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_provider_port_config coreport_config $mode $handle]
    lappend optionValueList -Active true
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $handle. Error: $errMsg"  {}
        }
    }
}

# customer side port config functions
proc ::sth::6pe6vpe::emulation_6pe_6vpe_cust_port_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $userArgsArray(port_handle)
    } else {
        return -code 1 -errorcode -1 "port_handle needed for create mode."
    }
    if {[catch {set vpn6PeGenParamsHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Vpn6PeGenParams ]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get Vpn6PeGenParams Handle. Error: $errMsg"  {}
    }
    if {[string equal "" $vpn6PeGenParamsHnd]} {
        if {[catch {set vpn6PeGenParamsHnd [::sth::sthCore::invoke stc::create "Vpn6PeGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create Vpn6PeGenParams Handle. Error: $errMsg"  {}
        }
    }
    set Vpn6PeGenCustPortParamsHndList [::sth::sthCore::invoke stc::get $vpn6PeGenParamsHnd -Children-Vpn6PeGenCustPortParams]
    set Vpn6PeGenCustPortParamsHnd ""
    foreach CustPortParamsHnd $Vpn6PeGenCustPortParamsHndList {
        if {$CustPortParamsHnd ne ""} {
            set CustPortHnd [::sth::sthCore::invoke stc::get $CustPortParamsHnd -AffiliationPort-Targets]
            if {[string equal $portHandle $CustPortHnd]} {
                set Vpn6PeGenCustPortParamsHnd $custPortParamsHnd
            }
        }
    }
    if {[string equal "" $Vpn6PeGenCustPortParamsHnd]} {
        if {[catch {set Vpn6PeGenCustPortParamsHnd [::sth::sthCore::invoke stc::create "Vpn6PeGenCustPortParams" -under $vpn6PeGenParamsHnd]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create Vpn6PeGenCustPortParams under $vpn6PeGenParamsHnd. Error: $errMsg"  {}
        }
        if {[catch {::sth::sthCore::invoke stc::config $Vpn6PeGenCustPortParamsHnd "-AffiliationPort-Targets $portHandle"} errMsg]} {
            return -code 1 -errorcode -1   "Unable to config -AffiliationPort-Targets to $Vpn6PeGenCustPortParamsHnd. Error: $errMsg"  {}
        }
    }
    
    set functionsToRun [getFunctionToRun emulation_6pe_6vpe_cust_port_config create] 
    foreach func $functionsToRun {
        $func $Vpn6PeGenCustPortParamsHnd create
    }
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_cust_port_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    if { ![::info exists ::sth::6pe6vpe::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for delete mode."
        keylset myReturnKeyedList status $::sth::sthCore::FAILURE
        return $myReturnKeyedList
    } else {
        set routerHndList $::sth::6pe6vpe::userArgsArray(handle)
        foreach router $routerHndList {
            if {[catch {::sth::sthCore::invoke ::sth::sthCore::invoke stc::delete $router} errMsg]} {
                return -code 1 -errorcode -1   "Unable to delete $router. Error: $errMsg"  {}
            }
        }
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
        return $myReturnKeyedList
    }
}

proc ::sth::6pe6vpe::custport_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_cust_port_config custport_config $mode $handle]
    lappend optionValueList -Active true
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $handle. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

# 6pe 6vpe network topology config function

proc ::sth::6pe6vpe::emulation_6pe_6vpe_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set vpn6PeGenParamsHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Vpn6PeGenParams]

    if {[string equal "" $vpn6PeGenParamsHnd]} {
        if {[catch {set vpn6PeGenParamsHnd [::sth::sthCore::invoke stc::create "Vpn6PeGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to create Vpn6PeGenParams Handle. Error: $errMsg"  {}
        }
    }
    
    set functionsToRun [getFunctionToRun emulation_6pe_6vpe_config create]
    foreach func $functionsToRun {
        $func $vpn6PeGenParamsHnd create
    }
    set hdlKeyList [expand_config $vpn6PeGenParamsHnd]

    # get the existing resultDataSet handle
    if {[catch {set perResultDataSetHandles [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get ResultDataSet Handle. Error: $errMsg"  {}
    }

    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: IsisRouterConfig IsisRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe IsisRouterResults. Error: $errMsg"  
    }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: BgpRouterConfig BgpRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe BgpRouterResults. Error: $errMsg"  
    }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: LdpRouterConfig LdpRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe LdpRouterResults. Error: $errMsg"  
    }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: RsvpRouterConfig RsvpRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe RsvpRouterResults. Error: $errMsg"  
        }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: Ospfv2RouterConfig Ospfv2RouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe Ospfv2RouterResults.  Error: $errMsg"  
    }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: Ospfv3RouterConfig Ospfv3RouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe Ospfv3RouterResults.  Error: $errMsg"  
    }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: RipRouterConfig RipRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe RipRouterResults. Error: $errMsg"  

    }
    set ::sth::6pe6vpe::createResultQuery 0
    if {[catch {::sth::sthCore::ResultDataSetSubscribe ::sth::6pe6vpe:: BfdRouterConfig BfdRouterResults myreturnKeyedList} errMsg]} {
        return -code 1 -errorcode -1  "Unable to subscribe BfdRouterResults.  Error: $errMsg"  
    }
    set ::sth::6pe6vpe::createResultQuery 0
    
    set resultTypeList {ldp ripv4 isis rsvp bgp bfd ospfv2 ospfv3}
    foreach resultType $resultTypeList {
        summaryResultsDataSetSubscribe $resultType myreturnKeyedList
    }
    if {[catch {set resultDataSetHandles [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get ResultDataSet Handle. Error: $errMsg"  {}
    }

    #get new created resultdataset handles within 6pe 6vpe config 
    foreach dataSetHandle $perResultDataSetHandles {
        set x [lsearch $resultDataSetHandles $dataSetHandle]
        if { $x > -1 } {
            set resultDataSetHandles [lreplace $resultDataSetHandles $x $x]
        }
    }
    set ::sth::6pe6vpe::resultDataSetHandleList $resultDataSetHandles

    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    keylset myReturnKeyedList handle $hdlKeyList
    
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""

    array set objArr {
        vpn "VpnIdGroup"
        ce_router "Router"
        rr_router "Router"
        p_router "Router"
        pe_router "Router"
    }

    # delete the streamblock firstly
    set handles [keylget ::sth::6pe6vpe::userArgsArray(handle) stream_id]
    foreach handle $handles {
        ::sth::sthCore::isHandleValid $handle streamblock
        if {[catch {::sth::sthCore::invoke stc::delete $handle} eMsg]} {
            return -code 1 -errorcode -1 "Internal Command Error while deleting $handle. Error: $eMsg"
        }
    }

    # delete the resultdataset for every protocol 
    
    if {[llength $::sth::6pe6vpe::resultDataSetHandleList] > 0 } {
        foreach dataSetHandle $::sth::6pe6vpe::resultDataSetHandleList {
            if {[catch {::sth::sthCore::invoke stc::delete $dataSetHandle} eMsg]} {
                return -code 1 -errorcode -1 "Internal Command Error while deleting $dataSetHandle. Error: $eMsg"
            }
        }
    }

    # delete routers

    foreach obj [array names objArr] {
        set handles [keylget ::sth::6pe6vpe::userArgsArray(handle) $obj]
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            if {[catch {::sth::sthCore::invoke stc::delete $handle} eMsg]} {
                return -code 1 -errorcode -1 "Internal Command Error while deleting $handle. Error: $eMsg"
            }
        }
    }
    if {[catch {set Vpn6PeGenHandle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Vpn6PeGenParams]} errMsg]} {
        return -code 1 -errorcode -1  "Internal Command Error while geting Vpn6PeGenParams.Error: $errMsg"
    } else {
        if {[catch {::sth::sthCore::invoke stc::delete $Vpn6PeGenHandle} errMsg]} {
            return -code 1 -errorcode -1  "Internal Command Error while deleting $Vpn6PeGenHandle.Error: $errMsg"
        }
    }

    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
}

proc ::sth::6pe6vpe::vpn6pe_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList
    
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config vpn6pe_config $mode $handle]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $handle. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::ospfv2session_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnIgpOspfv2SessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnIgpOspfv2SessionParams]} errMsg]} {
        return -code 1 -errorcode -1  "Unable to get VpnIgpOspfv2SessionParams Handle.Error: $errMsg" 
    }
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config ospfv2session_config $mode $vpnIgpOspfv2SessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnIgpOspfv2SessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnIgpOspfv2SessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::ospfv2auth_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnIgpOspfv2SessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnIgpOspfv2SessionParams]} errMsg ]} {
        return -code 1 -errorcode -1  "Unable to get VpnIgpOspfv2SessionParams Handle.Error :$errMsg" 
    }
    if {[string length $vpnIgpOspfv2SessionParamsHnd] > 0} {
        if {[catch {set ospfv2AuthenticationParamsHnd [::sth::sthCore::invoke stc::get $vpnIgpOspfv2SessionParamsHnd -children-Ospfv2AuthenticationParams]} errMsg]} {
            return -code 1 -errorcode -1  "Unable to get Ospfv2AuthenticationParams Handle .Error :$errMsg" 
        }
    } 
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config ospfv2auth_config $mode $ospfv2AuthenticationParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ospfv2AuthenticationParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $ospfv2AuthenticationParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::isissession_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnIgpIsisSessionParamsHnd [::sth::sthCore::invoke stc::get $handle -children-VpnIgpIsisSessionParams]} errMsg]} {
        return -code 1 -errorcode -1 "Unable to get VpnIgpIsisSessionParams Handle.Error: $errMsg " 
    }
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config isissession_config $mode $vpnIgpIsisSessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnIgpIsisSessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnIgpIsisSessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::isisauth_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnIgpIsisSessionParamsHnd [::sth::sthCore::invoke stc::get $handle -children-VpnIgpIsisSessionParams]} ]} {
        return -code 1 -errorcode -1 "Unable to get VpnIgpIsisSessionParams Handle." 
    }
    if {[string length $vpnIgpIsisSessionParamsHnd] > 0} {
        if {[catch {set isisAuthenticationParamsHnd [::sth::sthCore::invoke stc::get $vpnIgpIsisSessionParamsHnd -children-IsisAuthenticationParams]} ]} {
        return -code 1 -errorcode -1 "Unable to get IsisAuthenticationParams Handle. " 
        }
    } 
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config isisauth_config $mode $isisAuthenticationParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $isisAuthenticationParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $isisAuthenticationParamsHnd. Error: $errMsg"  {}
        }
        ::sth::sthCore::invoke stc::config $isisAuthenticationParamsHnd $optionValueList
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::rsvpsession_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnMplsRsvpSessionParamsHnd [::sth::sthCore::invoke stc::get $handle -children-VpnMplsRsvpSessionParams ]} ]} {
        return -code 1 -errorcode -1  "Unable to get VpnMplsRsvpSessionParams Handle." {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config rsvpsession_config $mode $vpnMplsRsvpSessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnMplsRsvpSessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnMplsRsvpSessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::ldpsession_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnMplsLdpSessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnMplsLdpSessionParams]} ]} {
        return -code 1 -errorcode -1 "Unable to get VpnMplsLdpSessionParams Handle." 
        }
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config ldpsession_config $mode $vpnMplsLdpSessionParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vpnMplsLdpSessionParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $vpnMplsLdpSessionParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::ldpauth_config {handle mode} {

    variable ::sth::6pe6vpe::keyedList

    if {[catch {set vpnMplsLdpSessionParamsHnd  [::sth::sthCore::invoke stc::get $handle -children-VpnMplsLdpSessionParams]} ]} {
        return -code 1 -errorcode -1  "Unable to get VpnMplsLdpSessionParams Handle." 
        }
    if {[string length $vpnMplsLdpSessionParamsHnd] > 0} {
        if {[catch {set ldpAuthenticationParamsHnd [::sth::sthCore::invoke stc::get $vpnMplsLdpSessionParamsHnd -children-LdpAuthenticationParams]} ]} {
            return -code 1 -errorcode -1  "Unable to get LdpAuthenticationParams Handle. " {}
        }
    } 
    set optionValueList [getStcOptionValueList emulation_6pe_6vpe_config ldpauth_config $mode $ldpAuthenticationParamsHnd]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ldpAuthenticationParamsHnd $optionValueList} errMsg]} {
            return -code 1 -errorcode -1  "Unable to config $ldpAuthenticationParamsHnd. Error: $errMsg"  {}
        }
    }
    keylset ::sth::6pe6vpe::keyedList handle $handle
}

proc ::sth::6pe6vpe::expand_config { Vpn6PeGenHandle } {
    
    variable ::sth::6pe6vpe::keyedList

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
    if {[catch {::sth::sthCore::invoke stc::perform RtgTestGenConfigExpandAndRunCommand -clearportconfig no -genparams $Vpn6PeGenHandle} errMsg] } {
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
    
    #get new created devices handles within 6pe 6vpe config 
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

# 6pe 6vpe control functions

proc ::sth::6pe6vpe::emulation_6pe_6vpe_control_start {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""

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

proc ::sth::6pe6vpe::emulation_6pe_6vpe_control_stop {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
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

# 6pe 6vpe info functions

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_isis {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList isis_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList

}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_ospfv2 {returnKeyedList} {

    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList ospfv2_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_ospfv3 {returnKeyedList} {

    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList ospfv3_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_rsvp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList rsvp_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_bfd {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList bfd_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}
proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_bgp {returnKeyedList} {

    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList bgp_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}
proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_rip {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList rip_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_ldp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set resultsType $::sth::6pe6vpe::userArgsArray(mode)
    set routerHndList [getRouterHandles]
    set resultsData [getResults $routerHndList $resultsType]

    keylset myReturnKeyedList ldp_results $resultsData
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}


proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_summary {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::keyedList
    set ::sth::6pe6vpe::keyedList ""
    
    set portHndList ""
    if {[info exists ::sth::6pe6vpe::userArgsArray(port_handle)]} {
        set portHndList $::sth::6pe6vpe::userArgsArray(port_handle)
    } elseif {[info exists ::sth::6pe6vpe::userArgsArray(handle)]} {
        set deviceHndList $::sth::6pe6vpe::userArgsArray(handle) 
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

# 6pe 6vpe common functions
proc ::sth::6pe6vpe::getFunctionToRun {mycmd mode} {

    variable sortedSwitchPriorityList
    set functionsToRun {}
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {

            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::6pe6vpe:: $mycmd $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::6pe6vpe:: $mycmd $switchname mode] "_none_"]} { 
                continue 
            }
            set func [::sth::sthCore::getModeFunc ::sth::6pe6vpe:: $mycmd $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    return $functionsToRun
}

proc ::sth::6pe6vpe::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::6pe6vpe::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::6pe6vpe:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::6pe6vpe:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::6pe6vpe:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                #check dependency
                #::sth::6pe6vpe::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::6pe6vpe::userArgsArray($opt)]} { continue }
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::6pe6vpe:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::6pe6vpe:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::6pe6vpe:: $cmdType $opt $::sth::6pe6vpe::userArgsArray($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::6pe6vpe::userArgsArray($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::6pe6vpe::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}

proc ::sth::6pe6vpe::getRouterHandles {} {

    variable ::sth::6pe6vpe::userArgsArray
    
    set handleList ""
    if {[info exists ::sth::6pe6vpe::userArgsArray(handle)]} {
        set handleList $::sth::6pe6vpe::userArgsArray(handle)
        foreach handle $handleList {
            if {[string first "emulateddevice" "$handle"] == 0 || [string first "router" "$handle"] == 0} {
                lappend handleList $handle
            }
        }
    } elseif {[info exists ::sth::6pe6vpe::userArgsArray(port_handle)]} {
        set portList $::sth::6pe6vpe::userArgsArray(port_handle)
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

proc ::sth::6pe6vpe::getResults {handles mode} {
    
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

proc ::sth::6pe6vpe::getSummaryResults {handle type} {
    
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

proc ::sth::6pe6vpe::summaryResultsDataSetSubscribe {summaryType returnKeyedList} {
    
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

proc ::sth::6pe6vpe::processResultsValue {input} {
    
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

