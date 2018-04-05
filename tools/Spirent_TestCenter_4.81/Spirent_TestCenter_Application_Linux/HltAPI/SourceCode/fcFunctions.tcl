namespace eval ::sth::fc:: {
    proc ::sth::fc::fc_config_create { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {![info exists userArgsArray(port_handle)]} {
            set result "The -port_handle is required when \"-mode create\" is used."
            return -code 1 -errorcode -1 $result
        }
        set hltPort $userArgsArray(port_handle)
        
        if {![info exists userArgsArray(fc_topology)]} {
            set fcHostConfigParamList ""
            unset userArgsArray(optional_args)
            unset userArgsArray(mandatory_args)
            
            set IfStack "FcIf"
            set IfCount "1"
            
            array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle)]
            set host $DeviceCreateOutput(-ReturnList)

            set fcIf [::sth::sthCore::invoke stc::get $host -children-fcif]
            set fcHostConfig [::sth::sthCore::invoke stc::create fcHostConfig -under $host "-UseFcIfWorldWidePortName False"]
            set fcGlobalConfig [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) "-children-FcGlobalConfig"]
            set fcGlobalParams [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) "-children-FcGlobalParams"]
            ::sth::sthCore::invoke stc::config $fcHostConfig "-UsesIf-targets [::sth::sthCore::invoke stc::get $host -children-fcif]"

            lappend configHandleList $host $fcHostConfig $fcIf $fcGlobalConfig $fcGlobalParams
            if {[catch {::sth::fc::processCofigAttr $configHandleList returnKeyedList} err]} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                return $::sth::sthCore::FAILURE
            }
            
            keylset returnKeyedList handle $host;# will now be used for traffic    
            return $::sth::sthCore::SUCCESS
        } else {
            set topology $userArgsArray(fc_topology)
            if {$topology eq "N_PORT_TO_F_PORT" && [llength $hltPort] < 2} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: at least 2 ports"
                return $::sth::sthCore::FAILURE
            }
            
            set fcParams [::sth::sthCore::invoke stc::create FcTestGenParams -under project1 -Topology $topology]
            set fcParams_configList ""
            lappend fcParams_configList -edtov $userArgsArray(ed_tov)
            lappend fcParams_configList -ratov $userArgsArray(ra_tov_port)
            ::sth::sthCore::invoke stc::config $fcParams $fcParams_configList
            
            set fcLeftSideParams [::sth::sthCore::invoke stc::get $fcParams -children-FcLeftSideTestParams]
            ::sth::sthCore::invoke stc::config $fcLeftSideParams -HostType [lindex $userArgsArray(host_type) 0] -NportsPerEnode [lindex $userArgsArray(nport_count) 0] -HostsPerPortCount [lindex $userArgsArray(host_per_port) 0]
            
            set fcRightSideParams [::sth::sthCore::invoke stc::get $fcParams -children-FcRightSideTestParams]
            ::sth::sthCore::invoke stc::config $fcRightSideParams -DomainId [format "%i" $userArgsArray(domain_id)] -DomainIdStep $userArgsArray(domain_id_step)
            if {[llength $userArgsArray(host_type)] > 1} {
                ::sth::sthCore::invoke stc::config $fcRightSideParams -HostType [lindex $userArgsArray(host_type) 1]
            } else {
                ::sth::sthCore::invoke stc::config $fcRightSideParams -HostType $::sth::fc::fc_config_default(host_type)
            }
            if {[llength $userArgsArray(nport_count)] > 1} {
                ::sth::sthCore::invoke stc::config $fcRightSideParams -NportsPerEnode [lindex $userArgsArray(nport_count) 0]
            } else {
                ::sth::sthCore::invoke stc::config $fcRightSideParams -NportsPerEnode $::sth::fc::fc_config_default(nport_count)               
            }
            
            if {[llength $userArgsArray(host_per_port)] > 1} {
                ::sth::sthCore::invoke stc::config $fcRightSideParams -HostsPerPortCount [lindex $userArgsArray(host_per_port) 0]
            } else {
                ::sth::sthCore::invoke stc::config $fcRightSideParams -HostsPerPortCount $::sth::fc::fc_config_default(host_per_port)               
            }
            
            if {[info exist userArgsArray(wwnn)]} {
                set wwnn_len [llength $userArgsArray(wwnn)]
                if {$wwnn_len > 0} {
                    ::sth::sthCore::invoke stc::config $fcLeftSideParams -StartWorldWideNodeName [lindex $userArgsArray(wwnn) 0]
                }
                if {$wwnn_len > 1} {
                    ::sth::sthCore::invoke stc::config $fcRightSideParams -StartWorldWideNodeName [lindex $userArgsArray(wwnn) 1]
                }
            }
            if {[info exist userArgsArray(wwpn)]} {
                set wwpn_len [llength $userArgsArray(wwpn)]
                if {$wwpn_len > 0} {
                    ::sth::sthCore::invoke stc::config $fcLeftSideParams -StartWorldWidePortName [lindex $userArgsArray(wwpn) 0]
                }
                if {$wwpn_len > 1} {
                        ::sth::sthCore::invoke stc::config $fcRightSideParams -StartWorldWidePortName [lindex $userArgsArray(wwpn) 1]
                }
            }
            if {[info exist userArgsArray(wwnn_step)]} {
                set wwnn_step_len [llength $userArgsArray(wwnn_step)]
                if {$wwnn_step_len > 0} {
                    ::sth::sthCore::invoke stc::config $fcLeftSideParams -WorldWideNodeNameStep [lindex $userArgsArray(wwnn_step) 0]
                }
                if {$wwnn_step_len > 1} {
                    ::sth::sthCore::invoke stc::config $fcRightSideParams -WorldWideNodeNameStep [lindex $userArgsArray(wwnn_step) 1]
                }
            }
            
            if {[info exist userArgsArray(wwpn_step)]} {
                set wwpn_step_len [llength $userArgsArray(wwpn_step)]
                if {$wwpn_step_len > 0} {
                    ::sth::sthCore::invoke stc::config $fcLeftSideParams -WorldWidePortNameStep [lindex $userArgsArray(wwpn_step) 0]
                }
                if {$wwpn_step_len > 1} {
                    ::sth::sthCore::invoke stc::config $fcRightSideParams -WorldWidePortNameStep [lindex $userArgsArray(wwpn_step) 1]
                }
            }

            set fcLeftSidePortParams [::sth::sthCore::invoke stc::create FcLeftSidePortParams -under $fcParams]
            ::sth::sthCore::invoke stc::config $fcLeftSidePortParams -RxCredit $userArgsArray(rxcredit_host)
            ::sth::sthCore::invoke stc::config $fcLeftSidePortParams -AffiliationPort-targets [lindex $hltPort 0]
            
            set fcRightSidePortParams [::sth::sthCore::invoke stc::create FcRightSidePortParams -under $fcParams]
            ::sth::sthCore::invoke stc::config $fcRightSidePortParams -RxCredit $userArgsArray(rxcredit_port)
            ::sth::sthCore::invoke stc::config $fcRightSidePortParams -AffiliationPort-targets [lindex $hltPort 1]

            set fcTraffic [::sth::sthCore::invoke stc::create FcFcoeTrafficParams -under project1]
            ::sth::sthCore::invoke stc::config $fcTraffic -CreateTraffic $userArgsArray(create_traffic) -TrafficFlow $userArgsArray(traffic_flow) -StreamBlockGroupMethod $userArgsArray(group_method) \
                                        -TrafficFrameSize $userArgsArray(traffic_flow_size) -TrafficLoadPercentPorts $userArgsArray(traffic_percent_ports)
            
            set fcoeParams [::sth::sthCore::invoke stc::create FcoeTestGenParams -under project1 -Topology $topology]
            ::sth::sthCore::invoke stc::config $fcoeParams -ratov $userArgsArray(ra_tov_host)
            ::sth::sthCore::invoke stc::perform FcoeTestGenUpdateAvailablePortsCommand -GenParams $fcoeParams -RemoveUnusedPorts FALSE
            ::sth::sthCore::invoke stc::perform FcTestGenUpdateAvailablePortsCommand -GenParams $fcParams -RemoveUnusedPorts FALSE
            set ret [::sth::sthCore::invoke stc::perform FcFcoeTestGenConfigExpand -ClearPortConfig YES -UseEmulatedDeviceType TRUE -GenFcParams $fcParams -GenTrafficParams $fcTraffic -GenFcoeParams $fcoeParams]
        
            
            set streamid1 [::sth::sthCore::invoke stc::get [lindex $hltPort 0] -children-streamblock]
            set streamid2 [::sth::sthCore::invoke stc::get [lindex $hltPort 1] -children-streamblock]
            set streamids [concat $streamid1 $streamid2]
            ::sth::sthCore::invoke stc::perform StreamBlockUpdate -streamblock $streamids
            set ::sth::Session::fillTraffic "unset"  
            if {$streamids ne ""} {
                keylset returnKeyedList streamid $streamids
                # for stream blocks created by create_traffic, need to update some data structures for traffic APIs.
                set ::sth::Session::fillTraffic "set"    
            }
            
            set hosts [::sth::sthCore::invoke stc::get project1 -children-emulateddevice]
            keylset returnKeyedList handle $hosts

            foreach host $hosts {
                set hostConfig [::sth::sthCore::invoke stc::get $host -children-fcHostConfig]
                if {$hostConfig ne ""} {
                    ::sth::sthCore::invoke stc::config $hostConfig -ratov $userArgsArray(ra_tov_host)
                    ::sth::sthCore::invoke stc::config $hostConfig -UseFcIfWorldWidePortName [lindex $userArgsArray(use_interface) 0]
                }
                set fportConfig [::sth::sthCore::invoke stc::get $host -children-fcFPortConfig]
                if {$fportConfig ne ""} {
                    set len [llength $userArgsArray(use_interface)]
                    if {$len > 1} {
                        ::sth::sthCore::invoke stc::config $fportConfig -UseFcIfWorldWidePortName [lindex $userArgsArray(use_interface) 1]
                    } else {
                        ::sth::sthCore::invoke stc::config $fportConfig -UseFcIfWorldWidePortName $::sth::fc::fc_config_default(use_interface)  
                    }
                }
            }
            
            set fcGlobalParams [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) "-children-FcGlobalParams"]            
            if {[catch {::sth::fc::processCofigAttr $fcGlobalParams returnKeyedList} err]} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                return $::sth::sthCore::FAILURE
            }
            
            return $::sth::sthCore::SUCCESS
        }
    }
    
    proc ::sth::fc::fc_config_modify { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "The -handle is required when \"-mode modify\" is used."
            return $::sth::sthCore::FAILURE
        }
        
        #foreach param {rxcredit_host rxcredit_port fc_topology group_method create_traffic traffic_flow traffic_flow_size traffic_percent_ports} {
        #    if {[info exists userArgsArray($param)]} {
        #        append msg "$param "
        #    }
        #}
        #if {[info exists msg]} {
        #    ::sth::sthCore::processError returnKeyedList "$msg\cannot be edited when \"-mode modify\" is used."
        #    return $::sth::sthCore::FAILURE
        #}
        #
        foreach ele $sortedSwitchPriorityList {
            set switchName [lindex $ele 1]
            set newUserArgsArray($switchName) $userArgsArray($switchName)
        }
        unset userArgsArray
        array set userArgsArray [array get newUserArgsArray]
        
        foreach host $userArgsArray(handle) {
            if {[set fcIf [::sth::sthCore::invoke stc::get $host -children-fcif]] == ""} {
                ::sth::sthCore::processError returnKeyedList "$host is not a valid FC device"
                return $::sth::sthCore::FAILURE
            }
            
            set fcHostConfig [::sth::sthCore::invoke stc::get $host -children-fcHostConfig]
            set fcGlobalConfig [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) "-children-fcGlobalParams"]
            lappend configHandleList $fcHostConfig $fcIf $host $fcGlobalConfig
            set fcFPortConfig [::sth::sthCore::invoke stc::get $host -children-fcFPortConfig]
            if {$fcFPortConfig ne ""} {
                lappend configHandleList $fcFPortConfig 
            }
            
            if {[catch {::sth::fc::processCofigAttr $configHandleList returnKeyedList} err]} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                return $::sth::sthCore::FAILURE
            }
        }
        keylset returnKeyedList handle $userArgsArray(handle)
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fc::fc_config_reset { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {![info exists userArgsArray(handle)]} {
           ::sth::sthCore::processError returnKeyedList  "The -handle is required when \"-mode reset\" is used."
            return $::sth::sthCore::FAILURE
        }
        
        foreach host $userArgsArray(handle) {
            set handle [::sth::sthCore::invoke stc::get $host -affiliationport-targets]
            foreach streamblock [::sth::sthCore::invoke stc::get $handle -Children-StreamBlock ] {
                set sb_dstbding [::sth::sthCore::invoke stc::get $streamblock -DstBinding-targets]
                set sb_srcbding [::sth::sthCore::invoke stc::get $streamblock -SrcBinding-targets]
                if {($sb_dstbding == "" )|| ($sb_srcbding == "")} {
                    if {[catch {::sth::sthCore::invoke stc::delete $streamblock} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error: $err"
                        return $::sth::sthCore::FAILURE
                    }
                }
            }
        }
        if {[catch {::sth::sthCore::invoke stc::perform deleteCommand -ConfigList $userArgsArray(handle)} err]} {
            ::sth::sthCore::processError returnKeyedList "Error: $err"
            return $::sth::sthCore::FAILURE
        }

        return $::sth::sthCore::SUCCESS
    }
    


    
    proc ::sth::fc::processCofigAttr { configHandleList returnInfoVarName} {
        set procName [lindex [info level [info level]] 0]
        upvar 1 $returnInfoVarName returnKeyedList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        foreach key $sortedSwitchPriorityList {
            set switchName [lindex $key 1]
            set switchValue $userArgsArray($switchName)
            set stcObjs     [::sth::sthCore::getswitchprop ::sth::fc:: fc_config $switchName stcobj]
            set stcAttr     [::sth::sthCore::getswitchprop ::sth::fc:: fc_config $switchName stcattr]
            set procFunc [::sth::sthCore::getModeFunc ::sth::fc:: fc_config $switchName create]
            if {$stcAttr == "_none_"} { continue }
            foreach stcObj [split $stcObjs |] {
                if {[set index [lsearch -regexp [string tolower $configHandleList] $stcObj\\d+]] !=-1} {
                    if {$procFunc != ""} {
                        if {[catch {$procFunc $configHandleList switchName switchValue returnKeyedList} err]} {
                            ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                            return $::sth::sthCore::FAILURE
                        }
                    }
                    set configHandle [lindex $configHandleList $index]
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
}
