# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx

namespace eval ::sth::Lldp:: {
    set createResultQuery 0
    array set ResultQueryCreateTable {
        lldp 0
        basic 0
        feature_basic 0
        prio_alloc 0
        bw_alloc 0
        pfc 0
        fcoe_prio 0
        logic_link 0
        bcn_parameter 0
        bcn_mode 0
    }
    set TRUE 1
    set FALSE 0
    set FALSE_MINUS_ONE -1
}

proc ::sth::Lldp::emulation_lldp_config_create { inputs returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "emulation_lldp_config_create"
    set myNameSpace "::sth::Lldp::"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -port_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set portHandle $switchToValue(port_handle)
    
    array set commonConfigTable {}
    array set stepConfigTable {}
    array set otherConfigTable {}
    
    if { [catch {::sth::Lldp::FormConfigParameter $inputs \
            $myNameSpace $_OrigHltCmdName  commonConfigTable stepConfigTable otherConfigTable} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured when running function FormConfigParameter.$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {![info exists switchToValue(intf_ip_addr)] && [info exists commonConfigTable(Router-Ipv4If)]} {
        unset commonConfigTable(Router-Ipv4If)
    }
    if {![info exists switchToValue(intf_ipv6_addr)] && [info exists commonConfigTable(Router-Ipv6If)]} {
        unset commonConfigTable(Router-Ipv6If)
    }
    if {![info exists switchToValue(vlan_id)] && [info exists commonConfigTable(Router-VlanIf)]} {
        unset commonConfigTable(Router-VlanIf)
    }
    
    set returnHandleList ""
    set count 1
    if { [info exists switchToValue(count)] } {
        set count $switchToValue(count)
    }
    
    for {set i 0} { $i < $count} {incr i} {
        set handleList ""
        array set objectHandleArr {}
        if { [catch {::sth::Lldp::CreateDeviceAndCommonConfig $portHandle commonConfigTable objectHandleArr handleList returnKeyedList cmdState} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured when running function CreateDeviceAndCommonConfig.$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        set lldpTlvConfigHandle [lindex $handleList 1]
        foreach funcName [array names otherConfigTable] {
            set procFuncName [lindex [split $funcName "-"] 1]
            #if { ($procFuncName == "ConfigOptionalTlvs") || ($procFuncName == "ConfigDcbxTlvs")} {
            #    set parameterList [lindex [lindex $otherConfigTable($funcName) 1] 2]
            #}
            
            set cmd "$myNameSpace$procFuncName \{$otherConfigTable($funcName)\} $lldpTlvConfigHandle returnKeyedList cmdState"
            if {[catch $cmd errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when running function $cmd.$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
        
        foreach objectType [array names stepConfigTable] {
            foreach {switchName switchValue} $stepConfigTable($objectType) {
                if { ![info exists commonConfigTable($objectType)]} {
                    continue
                }
                set index [lsearch $commonConfigTable($objectType) $switchName ]
                incr index
                set parameter ""
                lappend parameter [lindex $commonConfigTable($objectType) $index] $switchValue 1
                set cmdName ""
                if { $objectType == "Router-EthIIIf"} {
                    set cmdName "::sth::sthCore::macStep $parameter"
                } elseif { ($objectType == "Router-Ipv4If") || ($objectType == "Router")} {
                    set cmdName "::sth::sthCore::updateIpAddress 4 $parameter"
                } elseif { $objectType == "Router-Ipv6If"} {
                    set cmdName "::sth::sthCore::updateIpAddress 6 $parameter"
                } elseif { $objectType == "Router-VlanIf"} {
                    set cmdName "expr [lindex $commonConfigTable($objectType) $index] + $switchValue"
                }
                
                
                set commonConfigTable($objectType) [lreplace $commonConfigTable($objectType) $index $index [eval $cmdName]]

            }
        }
        
        lappend returnHandleList [lindex $handleList 0]
    }
    
    keylset returnKeyedList handle $returnHandleList
    
    return $SUCCESS
}

proc ::sth::Lldp::emulation_lldp_config_modify { inputs returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "emulation_lldp_config_modify"
    set myNameSpace "::sth::Lldp::"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    set handle $switchToValue(handle)
    if { ![::sth::Lldp::IsLldpHandleValid $handle errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    set lldpNodeConfigHandle $errMsg
    
    array set commonConfigTable {}
    array set stepConfigTable {}
    array set otherConfigTable {}
    
    if { [catch {::sth::Lldp::FormConfigParameter $inputs \
            $myNameSpace $_OrigHltCmdName  commonConfigTable stepConfigTable otherConfigTable} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured when running function FormConfigParameter.$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    array set objectHandleArr {}
    
    if {[catch {::sth::Lldp::ConfigCommonParameters $handle commonConfigTable objectHandleArr returnKeyedListVarName cmdStatusVarName} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {set lldpTlvConfigHdl [::sth::sthCore::invoke stc::get $lldpNodeConfigHandle -Children-LldpTlvConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LldpTlvConfig from port:$lldpNodeConfigHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {array set tlvAttrArr [::sth::sthCore::invoke stc::get $lldpTlvConfigHdl ]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get info from port:$lldpTlvConfigHdl." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { [info exists switchToValue(lldp_optional_tlvs)]} {
        foreach tlvHdl $tlvHdlList {
            if {[regexp "(lldp:systemnametlv|lldp:systemdescriptiontlv|lldp:portdescriptiontlv|lldp:systemcapabilitiestlv|\
                          lldp:managementaddrtlv|lldp:endtlv|lldp:customtlv|lldp:macphyconfigstatustlv|lldp:powerviamditlv|\
                          lldp:linkaggregationtlv|lldp:maxframesizetlv|lldp:portvlanidtlv|lldp:vlannametlv|\
                          lldp:portandprotocolvlanidtlv|lldp:protocolidentitytlv|lldp:organizationallyspecifictlv)" $tlvHdl]} {
                if {[catch {::sth::sthCore::invoke stc::delete $tlvHdl } errMsg]} {
                    ::sth::sthCore::processError returnKeyedList $errMsg {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
        
    }
    if { [info exists switchToValue(dcbx_tlvs)]} {
        foreach tlvHdl $tlvHdlList {
            if {[regexp "(lldp:DcbxTlvt1|lldp:DcbxTlvt2)" $tlvHdl]} {
                if {[catch {::sth::sthCore::invoke stc::delete $tlvHdl } errMsg]} {
                    ::sth::sthCore::processError returnKeyedList $errMsg {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
    }
    
    foreach funcName [array names otherConfigTable] {
        set procFuncName [lindex [split $funcName "-"] 1]
        #if { ($procFuncName == "ConfigOptionalTlvs") || ($procFuncName == "ConfigDcbxTlvs")} {
        #    set parameterList [lindex [lindex $otherConfigTable($funcName) 1] 2]
        #}
        
        set cmd "$myNameSpace$procFuncName \{$otherConfigTable($funcName)\} $lldpTlvConfigHdl returnKeyedList cmdState"
        if {[catch $cmd errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured when running function $cmd.$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    keylset returnKeyedList handle $switchToValue(handle)
    return $SUCCESS
}

proc ::sth::Lldp::emulation_lldp_config_delete { inputs returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "emulation_lldp_config_delete"
    set myNameSpace "::sth::Lldp::"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach handle $switchToValue(handle) {
        if { ![::sth::Lldp::IsLldpHandleValid $handle errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::delete $handle } errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::emulation_lldp_config_reset_tlv { inputs returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "emulation_lldp_config_reset_tlv"
    set myNameSpace "::sth::Lldp::"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach handle $switchToValue(handle) {
        if { ![::sth::Lldp::IsLldpHandleValid $handle errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        set lldpNodeConfigHandle $errMsg
        
        if {[catch {set lldpTlvConfigHdl [::sth::sthCore::invoke stc::get $lldpNodeConfigHandle -Children-LldpTlvConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-LldpTlvConfig from port:$lldpNodeConfigHandle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {array set tlvAttrArr [::sth::sthCore::invoke stc::get $lldpTlvConfigHdl ]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get info from port:$lldpTlvConfigHdl." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        set tlvHdlList $tlvAttrArr(-children)
        
        set resetTlvType $switchToValue(reset_tlv_type)
        if { $resetTlvType == "both"} {
            set $resetTlvType "lldp | dcbx"
        }
        
        set deleteTlvHdlList ""
        if {[string first "lldp" $resetTlvType] > -1} {
            foreach tlvHdl $tlvHdlList {
                if {[regexp "(lldp:systemnametlv|lldp:systemdescriptiontlv|lldp:portdescriptiontlv|lldp:systemcapabilitiestlv|\
                              lldp:managementaddrtlv|lldp:endtlv|lldp:customtlv|lldp:macphyconfigstatustlv|lldp:powerviamditlv|\
                              lldp:linkaggregationtlv|lldp:maxframesizetlv|lldp:portvlanidtlv|lldp:vlannametlv|\
                              lldp:portandprotocolvlanidtlv|lldp:protocolidentitytlv|lldp:organizationallyspecifictlv)" $tlvHdl]} {
                    if {[catch {::sth::sthCore::invoke stc::delete $tlvHdl } errMsg]} {
                        ::sth::sthCore::processError returnKeyedList $errMsg {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
        } elseif {[string first "dcbx" $resetTlvType] > -1} {
            foreach tlvHdl $tlvHdlList {
                if {[regexp "(lldp:DcbxTlvt1|lldp:DcbxTlvt2)" $tlvHdl]} {
                    if {[catch {::sth::sthCore::invoke stc::delete $tlvHdl } errMsg]} {
                        ::sth::sthCore::processError returnKeyedList $errMsg {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
        }
    }
    keylset returnKeyedList handle $switchToValue(handle)
    return $SUCCESS
}

proc ::sth::Lldp::emulation_lldp_optional_tlv_config_img { inputs returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_optional_tlv_config"
    set _hltCmdName "emulation_lldp_optional_tlv_config_img"
    set myNameSpace "::sth::Lldp::"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    array set commonConfigTable {}
    array set stepConfigTable {}
    array set otherConfigTable {}
    
    if { [catch {::sth::Lldp::FormConfigParameter $inputs \
            $myNameSpace $_OrigHltCmdName  commonConfigTable stepConfigTable otherConfigTable} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured when running function FormConfigParameter.$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    keylset returnKeyedList handle [array get otherConfigTable]
    
    return $SUCCESS
}

proc ::sth::Lldp::emulation_lldp_dcbx_tlv_config_img { inputs returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_dcbx_tlv_config"
    set _hltCmdName "emulation_lldp_dcbx_tlv_config_img"
    set myNameSpace "::sth::Lldp::"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    #array set commonConfigTable {}
    #array set stepConfigTable {}
    #array set otherConfigTable {}
    
    #if { [catch {::sth::Lldp::FormConfigParameter $inputs \
    #        $myNameSpace $_OrigHltCmdName  commonConfigTable stepConfigTable otherConfigTable} errMsg]} {
    #    ::sth::sthCore::processError returnKeyedList "Error occured when running function FormConfigParameter.$errMsg" {}
    #    set cmdState $FAILURE
    #    return $returnKeyedList
    #}
    
    #keylset returnKeyedList handle [array get otherConfigTable]
    
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigOptionalTlvs { parameterList lldpTlvConfigHandle returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "ConfigOptionalTlvs"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName  "
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    #set Handle $lldpTlvConfigHandle
    
    set parameterList [lindex [lindex $parameterList 1] 2]
    
    array set procFuncTable $parameterList
    
    foreach procFuncName [array names procFuncTable] {
        array unset parameterArr
        array set parameterArr $procFuncTable($procFuncName)
    
        set procFunc [lindex [split $procFuncName "-"] 1]
        
        if { $procFunc == "PortDescription" } {
            if { [info exists parameterArr(tlv_port_description_enable)] } {
                if { [lindex $parameterArr(tlv_port_description_enable) 2] == 1 } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:PortDescriptionTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:PortDescriptionTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {::sth::Lldp::SetTlvFieldValue "tlv_port_description_value" $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValue, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
        } elseif { $procFunc == "SystemName" } {
            if { [info exists parameterArr(tlv_system_name_enable)] } {
                if { [lindex $parameterArr(tlv_system_name_enable) 2] == "1" } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:SystemNameTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:SystemNameTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {::sth::Lldp::SetTlvFieldValue "tlv_system_name_value" $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValue, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
        } elseif { $procFunc == "SystemDescription" } {
            if { [info exists parameterArr(tlv_system_description_enable)] } {
                if { [lindex $parameterArr(tlv_system_description_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:SystemDescriptionTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:SystemDescriptionTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {::sth::Lldp::SetTlvFieldValue "tlv_system_description_value" $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValue, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
        } elseif { $procFunc == "SystemCapabilities" } {
            if { [info exists parameterArr(tlv_system_capabilities_enable)] } {
                if { [lindex $parameterArr(tlv_system_capabilities_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:SystemCapabilitiesTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:SystemCapabilitiesTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {set c1Handle [::sth::sthCore::invoke stc::create "enabledCapabilities" -under $pHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create enabledCapabilities on object:$pHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {set c2Handle [::sth::sthCore::invoke stc::create "systemCapabilities" -under $pHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create systemCapabilities on object:$pHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    foreach switchName [array names parameterArr] {
                        if { ($switchName == "tlv_system_capabilities_value") } {
                            set attrList ""
                            set index 0
                            foreach attr "-other -repeater -bridge -wlanAccessPoint -router -telephone -docsisCableDevice  -stationOnly" {
                                lappend attrList $attr [lindex [split [lindex $parameterArr($switchName) 2] ""] $index]
                                incr index
                            }
                            if {[catch {::sth::sthCore::invoke stc::config $c2Handle $attrList} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Can not config $attrList to object: $c2Handle, errMsg:$errMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        } elseif { ($switchName == "tlv_enabled_capabilities_value") } {
                            set attrList ""
                            set index 0
                            foreach attr "-other -repeater -bridge -wlanAccessPoint -router -telephone -docsisCableDevice  -stationOnly" {
                                lappend attrList $attr [lindex [split [lindex $parameterArr($switchName) 2] ""] $index]
                                incr index
                            }
                            if {[catch {::sth::sthCore::invoke stc::config $c1Handle $attrList} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Can not config $attrList to object: $c1Handle, errMsg:$errMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        }
                    }
                }
            }
        } elseif { $procFunc == "ManagementAddress" } {
            if { [info exists parameterArr(tlv_management_addr_enable)] } {
                if { [lindex $parameterArr(tlv_management_addr_enable) 2] } {
                    set count 1
                    if { [info exists parameterArr(tlv_management_addr_count)]} {
                        set count [lindex $parameterArr(tlv_management_addr_count) 2]
                    }
                    
                    for {set i 0} {$i < $count} {incr i} {
                        if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:ManagementAddrTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create lldp:ManagementAddrTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        if {[catch {set cHandle [::sth::sthCore::invoke stc::create "managementAddr" -under $pHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create managementAddr on object:$pHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        if {[catch {set ccHandle [::sth::sthCore::invoke stc::create "customAddr" -under $cHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create customAddr on object:$cHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        
                        foreach {switchName value} [array get parameterArr] {
                            set stcObj [lindex $value 0]
                            set stcAttr [lindex $value 1]
                            set stcValue [lindex [lindex $value 2] $i]
                            if { ($switchName == "tlv_management_addr_enable") || ($switchName == "tlv_management_addr_count")} {
                                continue
                            }
                            if { $switchName == "tlv_management_addr_subtype_list"} {
                                array set mapTable {
                                                    other 00 ipv4 01 ipv6 02 nsap 03 hdlc 04 bbn1822 05 all_802 06 e163 \
                                                    07 e164 08 f69 09 x121 0A ipx 0B apple_talk 0C dec_net_iv 0D banyan_vines 0E \
                                                    e164_with_nsap 0F dns 10 distinguished_name 11 as_number 12 xtp_over_ipv4 13 \
                                                    xtp_over_ipv6 14 xtp_native_mode_xtp 15 fibre_channel_wwpn 16 \
                                                    fibre_channel_wwnn 17 gateway_identifier 18 afi 19
                                                    }
                                if { [info exists mapTable($stcValue)]} {
                                    set stcValue $mapTable($stcValue)
                                } else {
                                    set errMsg "Error! The value \"$stcValue\" of switch -$switchName is wrong, should be \
                                        \{other|ipv4|ipv6|nsap|hdlc|bbn1822|all_802|e163|e164|f69|x121|ipx|apple_talk|\
                                        dec_net_iv|banyan_vines|e164_with_nsap|dns|distinguished_name|as_number|xtp_over_ipv4\
                                        |xtp_over_ipv6|xtp_native_mode_xtp|fibre_channel_wwpn|fibre_channel_wwnn|gateway_identifier|afi\}"
                                    
                                    puts $errMsg
                                    ::sth::sthCore::processError returnKeyedList "$errMsg" {}
                                    set cmdState $FAILURE
                                    return $returnKeyedList
                                }
                            }
                            #ip4v addr to hex
                            if { [string first "." $stcValue] > -1} {
                                set hex ""
                                foreach integer [split $stcValue "."] {
                                    binary scan [binary format i* $integer] H2 var
                                    append hex $var
                                }
                                set stcValue $hex
                            }
                            if { [string first ":" $stcValue] > -1} {
                                set nIp [::sth::sthCore::normalizeIPv6Addr $stcValue]
                                set stcValue [join [split $nIp ":"] ""]
                            }
                            #ipv6 addr to hex
                            if { $stcObj == "lldp:ManagementAddrTlv"} {
                                set handle $pHandle
                            } elseif { $stcObj == "lldp:ManagementAddrTlv-managementAddr-customAddr"} {
                                set handle $ccHandle
                            } else {
                                continue
                            }
                            if {[catch {::sth::sthCore::invoke stc::config $handle "-$stcAttr $stcValue"} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Can not config  -$stcAttr $stcValue to object: $handle, errMsg:$errMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        }
                    }
                }
            }
        } elseif { $procFunc == "PortVlanId" } {
            if { [info exists parameterArr(tlv_port_vlanid_enable)] } {
                if { [lindex $parameterArr(tlv_port_vlanid_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:PortVlanIdTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:PortVlanIdTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {::sth::Lldp::SetTlvFieldValue "tlv_port_vlanid_value" $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValue, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
        } elseif { $procFunc == "PortAndProtocolVlanId" } {
            if { [info exists parameterArr(tlv_port_and_protocol_vlanid_enable)] } {
                if { [lindex $parameterArr(tlv_port_and_protocol_vlanid_enable) 2] } {
                    set count 1
                    if {[info exists parameterArr(tlv_port_and_protocol_vlanid_count)] } {
                        set count [lindex $parameterArr(tlv_port_and_protocol_vlanid_count) 2]
                    }
                    for {set i 0} {$i < $count} {incr i} {
                        if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:PortAndProtocolVlanIdTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create lldp:PortAndProtocolVlanIdTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        
                        if {[catch {set cHandle [::sth::sthCore::invoke stc::create "flags" -under $pHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create lldp:PortAndProtocolVlanIdTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        
                        foreach switchName [array names parameterArr] {
                            if { ($switchName == "tlv_port_and_protocol_vlanid_enable") || ($switchName == "tlv_port_and_protocol_vlanid_count")} {
                                continue
                            }
                            if { [llength [lindex $parameterArr($switchName) 2]] != $count } {
                                ::sth::sthCore::processError returnKeyedList "Error: value number of -$switchName is not equal to value of -tlv_port_and_protocol_vlanid_count" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                            if {[catch {::sth::Lldp::SetTlvFieldValueCount $switchName $lldpTlvConfigHandle parameterArr $i returnKeyedList cmdState} errMsg ]} {
                                ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValueCount, errMsg:$errMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        }
                    }
                }
            }
        } elseif { $procFunc == "VlanName" } {
            if { [info exists parameterArr(tlv_vlan_name_enable)] } {
                if { [lindex $parameterArr(tlv_vlan_name_enable) 2] } {
                    set count 1
                    if {[info exists parameterArr(tlv_vlan_name_count)] } {
                        set count [lindex $parameterArr(tlv_vlan_name_count) 2]
                    }
                    for {set i 0} {$i < $count} {incr i} {
                        if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:VlanNameTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create lldp:VlanNameTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        
                        foreach switchName [array names parameterArr] {
                            if { ($switchName == "tlv_vlan_name_enable") || ($switchName == "tlv_vlan_name_count")} {
                                continue
                            }
                            if { [llength [lindex $parameterArr($switchName) 2]] != $count } {
                                ::sth::sthCore::processError returnKeyedList "Error: value number of -$switchName is not equal to value of -tlv_vlan_name_count" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                            if {[catch {::sth::Lldp::SetTlvFieldValueCount $switchName $lldpTlvConfigHandle parameterArr $i returnKeyedList cmdState} errMsg ]} {
                                ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValueCount, errMsg:$errMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        }
                    }
                }
            }
        } elseif { $procFunc == "ProtocolIdentity" } {
            if { [info exists parameterArr(tlv_protocol_identity_enable)] } {
                if { [lindex $parameterArr(tlv_protocol_identity_enable) 2] } {
                    set count 1
                    if {[info exists parameterArr(tlv_protocol_identity_count)] } {
                        set count [lindex $parameterArr(tlv_protocol_identity_count) 2]
                    }
                    for {set i 0} {$i < $count} {incr i} {
                        if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:ProtocolIdentityTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not create lldp:ProtocolIdentityTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        
                        foreach switchName [array names parameterArr] {
                            if { ($switchName == "tlv_protocol_identity_enable") || ($switchName == "tlv_protocol_identity_count")} {
                                continue
                            }
                            if { [llength [lindex $parameterArr($switchName) 2]] != $count } {
                                ::sth::sthCore::processError returnKeyedList "Error: value number of -$switchName is not equal to value of -tlv_vlan_name_count" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                            if {[catch {::sth::Lldp::SetTlvFieldValueCount $switchName $lldpTlvConfigHandle parameterArr $i returnKeyedList cmdState} errMsg ]} {
                                ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValueCount, errMsg:$errMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        }
                    }
                }
            }
        } elseif { $procFunc == "MacPhyConfigStatus" } {
            if { [info exists parameterArr(tlv_mac_phy_config_status_enable)] } {
                if { [lindex $parameterArr(tlv_mac_phy_config_status_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:MacPhyConfigStatusTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:MacPhyConfigStatusTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {set c1Handle [::sth::sthCore::invoke stc::create "autoNegotiationSupportAndStatus" -under $pHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create autoNegotiationSupportAndStatus on object:$pHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {set c2Handle [::sth::sthCore::invoke stc::create "autoNegotiationAdvertisedCapability" -under $pHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create autoNegotiationAdvertisedCapability on object:$pHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    foreach switchName [array names parameterArr] {
                        set switchValue [lindex $parameterArr($switchName) 2]
                        set attrList ""
                        set handle ""
                        if { $switchName == "tlv_mac_phy_config_status_auto_negotiation_supported_flag" } {
                            append attrList " -autoNegotiationSupported $switchValue"
                            set handle $c1Handle
                        } elseif { $switchName == "tlv_mac_phy_config_status_auto_negotiation_status_flag" } {
                            append attrList " -autoNegotiationEnabled $switchValue"
                            set handle $c1Handle
                        } elseif { $switchName == "tlv_mac_phy_config_status_auto_negotiation_advertised_capability" } {
                            set bin ""
                            foreach hex [split $switchValue ""] {
                                append bin [::sth::Lldp::OneDigitHexTobit $hex]
                            }
                            
                            set attrTypeList "other b10baseT b10baseTFD b100baseT4 b100baseTX b100baseTXFD b100baseT2 b100baseT2FD \
                                              bFdxPause bFdxAPause bFdxSPause bFdxBPause  b1000baseX b1000baseXFD b1000baseT b1000baseTFD"
                            foreach attrType $attrTypeList value [split $bin ""] {
                                append attrList " -$attrType $value"
                                set handle $c2Handle
                            }
                        } elseif { $switchName == "tlv_mac_phy_config_status_operational_mau_type" } {
                            append attrList " -operationalMauType $switchValue"
                            set handle $pHandle
                        } else {
                            continue
                        }
                        
                        if {[catch {::sth::sthCore::invoke stc::config $handle $attrList} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not config  $attrList to object: $handle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                    }
                }
            }
        } elseif { $procFunc == "PowerViaMdi" } {
            if { [info exists parameterArr(tlv_power_via_mdi_enable)]  } {
                if { [lindex $parameterArr(tlv_power_via_mdi_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:PowerViaMdiTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:PowerViaMdiTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {set c1Handle [::sth::sthCore::invoke stc::create "mdiPowerSupport" -under $pHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create mdiPowerSupport on object:$pHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    foreach switchName [array names parameterArr] {
                        set switchValue [lindex $parameterArr($switchName) 2]
                        set attrList ""
                        set handle ""
                        if { $switchName == "tlv_power_via_mdi_pse_power_pair" } {
                            append attrList " -psePowerPairs $switchValue"
                            set handle $pHandle
                        } elseif { $switchName == "tlv_power_via_mdi_pse_power_class" } {
                            append attrList " -psePowerClass $switchValue"
                            set handle $pHandle
                        } elseif { $switchName == "tlv_power_via_mdi_power_support_bits" } {
                            set attrTypeList "portClass pseMdiPowerSupport pseMdiPowerState psePairsControlAbility"
                            foreach attrType $attrTypeList value [split $switchValue ""] {
                                append attrList " -$attrType $value"
                                set handle $c1Handle
                            }
                        } else {
                            continue
                        }
                        
                        if {[catch {::sth::sthCore::invoke stc::config $handle $attrList} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not config  $attrList to object: $handle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                    }
                }
            }
        } elseif { $procFunc == "LinkAggregation" } {
            #puts [array get parameterArr]
            if { [info exists parameterArr(tlv_link_aggregation_enable)] } {
                if { [lindex $parameterArr(tlv_link_aggregation_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:LinkAggregationTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:LinkAggregationTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    if {[catch {set c1Handle [::sth::sthCore::invoke stc::create "aggregationStatus" -under $pHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create aggregationStatus on object:$pHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    foreach switchName [array names parameterArr] {
                        set switchValue [lindex $parameterArr($switchName) 2]
                        set attrList ""
                        set handle ""
                        if { $switchName == "tlv_link_aggregation_aggregated_port_id" } {
                            append attrList " -aggregatedPortid $switchValue"
                            set handle $pHandle
                        } elseif { $switchName == "tlv_link_aggregation_status_flag" } {
                            append attrList " -aggregationStatus $switchValue"
                            set handle $c1Handle
                        } elseif { $switchName == "tlv_link_aggregation_capability_flag" } {
                            append attrList " -aggregationCapability $switchValue"
                            set handle $c1Handle
                        } else {
                            continue
                        }
                        
                        if {[catch {::sth::sthCore::invoke stc::config $handle $attrList} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not config  $attrList to object: $handle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                    }
                }
            }
        } elseif { $procFunc == "MaxFrameSize" } {
            if { [info exists parameterArr(tlv_maximum_frame_size_enable)] } {
                if { [lindex $parameterArr(tlv_maximum_frame_size_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:MaxFrameSizeTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:MaxFrameSizeTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    foreach switchName [array names parameterArr] {
                        set switchValue [lindex $parameterArr($switchName) 2]
                        set attrList ""
                        set handle ""
                        if { $switchName == "tlv_maximum_frame_size_value" } {
                            append attrList " -frameSize $switchValue"
                            set handle $pHandle
                        }  else {
                            continue
                        }
                        
                        if {[catch {::sth::sthCore::invoke stc::config $handle $attrList} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not config  $attrList to object: $handle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                    }
                }
            }
        } elseif { $procFunc == "Custom" } {
            if { [info exists parameterArr(tlv_customized_enable)] } {
                if { [lindex $parameterArr(tlv_customized_enable) 2] } {
                    if {[catch {set pHandle [::sth::sthCore::invoke stc::create "lldp:CustomTlv" -under $lldpTlvConfigHandle]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not create lldp:CustomTlv on object:$lldpTlvConfigHandle, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    foreach switchName [array names parameterArr] {
                        set switchValue [lindex $parameterArr($switchName) 2]
                        set attrList ""
                        set handle ""
                        if { $switchName == "tlv_customized_type" } {
                            append attrList " -type $switchValue"
                            set handle $pHandle
                        } elseif { $switchName == "tlv_customized_value" } {
                            append attrList " -value $switchValue"
                            set handle $pHandle
                        } else {
                            continue
                        }
                        
                        if {[catch {::sth::sthCore::invoke stc::config $handle $attrList} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Can not config  $attrList to object: $handle, errMsg:$errMsg" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                    }
                }
            }
        }
        
    }
    
    
    return $SUCCESS
}

proc ::sth::Lldp::OneDigitHexTobit { hexDig} {
    
    if { $hexDig == "1" } {
        return "0001"
    } elseif { $hexDig == "2" } {
                return "0010"
    } elseif { $hexDig == "3" } {
                return "0011"
    } elseif { $hexDig == "4" } {
                return "0100"
    } elseif { $hexDig == "5" } {
                return "0101"
    } elseif { $hexDig == "6" } {
                return "0110"
    } elseif { $hexDig == "7" } {
                return "0111"
    } elseif { $hexDig == "8" } {
                return "1000"
    } elseif { $hexDig == "9" } {
                return "1001"
    } elseif { [string tolower $hexDig] == "a" } {
                return "1010"
    } elseif { [string tolower $hexDig] == "b" } {
                return "1011"
    } elseif { [string tolower $hexDig] == "c" } {
                return "1100"
    } elseif { [string tolower $hexDig] == "d" } {
                return "1101"
    } elseif { [string tolower $hexDig] == "e" } {
                return "1110"
    } elseif { [string tolower $hexDig] == "f" } {
                return "1111"
    }
}

proc ::sth::Lldp::ConfigMandatoryTlvs { parameterList lldpTlvConfigHandle returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    
    set _OrigHltCmdName "ConfigMandatoryTlvs"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName  "
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    array set parameterArr $parameterList
    foreach switchName [array names parameterArr] {
        if { ($switchName == "tlv_chassis_id_subtype") || ($switchName == "tlv_port_id_subtype") } {
            if {[catch {::sth::Lldp::SetTlvSubtype $switchName $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvSubtype, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        } elseif { ($switchName == "tlv_chassis_id_value") || ($switchName == "tlv_port_id_value") } {
            if {[catch {::sth::Lldp::SetTlvSubtypeFieldValue $switchName $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvSubtypeFieldValue, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        } elseif { $switchName == "tlv_ttl_value" } {
            if {[catch {::sth::Lldp::SetTlvFieldValue $switchName $lldpTlvConfigHandle parameterArr returnKeyedList cmdState} errMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when running function ::sth::Lldp::SetTlvFieldValue, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    
    return $SUCCESS
}

proc ::sth::Lldp::SetTlvSubtypeFieldValue { argName parentHandle parameterList returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set Handle $parentHandle
    
    upvar 1 $parameterList parameterArr
    
    set stcObject [lindex $parameterArr($argName) 0]
    set stcAttr [lindex $parameterArr($argName) 1]
    set stcValue [lindex $parameterArr($argName) 2]
        
    foreach objectType [split $stcObject "-"] {
        if {[catch {set Handle [::sth::sthCore::invoke stc::get $Handle -Children-$objectType]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-$objectType from object:$Handle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set subtypeHandle [::sth::sthCore::invoke stc::get $Handle -Children]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children from object:$Handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[regexp {^pidmacaddress\d+$} $subtypeHandle] && $stcValue eq "00:00:00:00:00:00"} {
        return $SUCCESS
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $subtypeHandle "-$stcAttr \{$stcValue\}"} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not config -$stcAttr $stcValue to object: $subtypeHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
       
    return $SUCCESS
}

proc ::sth::Lldp::SetTlvFieldValue { argName parentHandle parameterList returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set Handle $parentHandle
    
    upvar 1 $parameterList parameterArr
    
    set stcObject [lindex $parameterArr($argName) 0]
    set stcAttr [lindex $parameterArr($argName) 1]
    set stcValue [lindex $parameterArr($argName) 2]
    
    foreach objectType [split $stcObject "-"] {
        if {[catch {set Handle [::sth::sthCore::invoke stc::get $Handle -Children-$objectType]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-$objectType from object:$Handle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $Handle "-$stcAttr \{$stcValue\}"} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not config -$stcAttr $stcValue to object: $subtypeHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::SetTlvFieldValueCount { argName parentHandle parameterList count returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set Handle $parentHandle
    
    upvar 1 $parameterList parameterArr
    
    set stcObject [lindex $parameterArr($argName) 0]
    set stcAttr [lindex $parameterArr($argName) 1]
    set stcValue [lindex [lindex $parameterArr($argName) 2] $count]
    
    foreach objectType [split $stcObject "-"] {
        if {[catch {set Handle [::sth::sthCore::invoke stc::get $Handle -Children-$objectType]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-$objectType from object:$Handle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { [llength $Handle] >1 } {
            set Handle [lindex $Handle $count]
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $Handle "-$stcAttr \{$stcValue\}"} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not config -$stcAttr $stcValue to object: $Handle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::SetTlvSubtype { argName parentHandle parameterList returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set Handle $parentHandle
    
    upvar 1 $parameterList parameterArr
    
    set stcObject [lindex $parameterArr($argName) 0]
    set stcAttr [lindex $parameterArr($argName) 1]
    set stcValue [lindex $parameterArr($argName) 2]
        
    foreach objectType [split $stcObject "-"] {
        if {[catch {set Handle [::sth::sthCore::invoke stc::get $Handle -Children-$objectType]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-$objectType from object:$Handle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set subtypeHandle [::sth::sthCore::invoke stc::get $Handle -Children-$stcValue]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-$stcValue from object:$Handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { $subtypeHandle == "" } {
        if {[catch {set subtypeHandle [::sth::sthCore::invoke stc::get $Handle -Children]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children from object:$Handle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::delete $subtypeHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not delete object:$subtypeHandle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {set subtypeHandle [::sth::sthCore::invoke stc::create $stcValue -under $Handle]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not create $stcValue on object:$Handle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::CreateDeviceAndCommonConfig { portHandle commonConfigTable objectHandleArrName msg returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "CreateDevice"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: CreateDevice "
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $msg returnMsg
    upvar 1 $commonConfigTable commonTable
    upvar 1 $objectHandleArrName objectHandleArr
    
    set IfStack "EthIIIf"
    set IfCount "1"
    
    if { [info exists commonTable(Router-VlanIf)]} {
        set IfStack [linsert $IfStack 0 "VlanIf"]
        set IfCount [linsert $IfCount 0 "1"]
    }
    if { [info exists commonTable(Router-Ipv4If)]} {
        set IfStack [linsert $IfStack 0 "Ipv4If"]
        set IfCount [linsert $IfCount 0 "1"]
    } elseif { [info exists commonTable(Router-Ipv6If)]} {
        set IfStack [linsert $IfStack 0 "Ipv6If"]
        set IfCount [linsert $IfCount 0 "1"]
    }
    
    #by now, the IfStack may be "EthIIIf {VlanIf}" or "EthIIIf {VlanIf} Ipv4If" or "EthIIIf {VlanIf} Ipv6If"
    if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set routerHandle $DeviceCreateOutput(-ReturnList)} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Interal command error while creating LLDP router. Error: $errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router) $routerHandle
    }
    
    if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-EthIIIf]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-EthIIIf from port:$routerHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router-EthIIIf) $EthIIIfHandle
    }
    
    if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-VlanIf]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-VlanIf from port:$routerHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router-VlanIf) $VlanIfHandle
    }
    
    if {[catch {set Ipv4IfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-Ipv4If]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv4If from port:$routerHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router-Ipv4If) $Ipv4IfHandle
    }
    
    if { [info exists commonTable(Router-Ipv6If)] } {
        set attachIf $VlanIfHandle
        if { $VlanIfHandle == "" } {
            set attachIf $EthIIIfHandle
        }
        
        #ipv4 & ipv6 dual stack
        if { [info exists commonTable(Router-Ipv4If)] } {
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -AttachToIf $attachIf -DeviceList $routerHandle -IfStack Ipv6If -IfCount 1 -IsPrimaryIf TRUE} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not do StcPerform IfStackAttach :$errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
        
        if {[catch {set Ipv6IfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-Ipv6If]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv6If from object:$routerHandle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        } else {
            set objectHandleArr(Router-Ipv6If) $Ipv6IfHandle
        }
        
        #link local ipv6 intf
        if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -AttachToIf $attachIf -DeviceList $routerHandle -IfStack Ipv6If -IfCount 1 -IsPrimaryIf TRUE} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not do StcPerform IfStackAttach :$errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        } else {
            if {[catch {set handleList [::sth::sthCore::invoke stc::get $routerHandle -Children-Ipv6If]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv6If from object:$routerHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            
            set objectHandleArr(Router-LinkLocalIpv6If) [lindex $handleList 1]
            if { ![info exists commonTable(Router-LinkLocalIpv6If) ]} {
                set commonTable(Router-LinkLocalIpv6If) "-Address fe80::1"
            }
        }
    }
    
    if {[catch {set lldpNodeHandle [::sth::sthCore::invoke stc::create LldpNodeConfig -under $routerHandle "-UsesIf-Targets $objectHandleArr(Router-EthIIIf)"]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not create LldpNodeConfig on router:$routerHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router-LldpNodeConfig) $lldpNodeHandle
    }
    
    if { [catch {::sth::Lldp::ConfigToStc objectHandleArr commonTable returnKeyedList cmdState} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error! errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }

    if {[catch {::sth::sthCore::invoke stc::get $lldpNodeHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get info from object:$lldpNodeHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {set lldpTlvConfigHandle [::sth::sthCore::invoke stc::get $lldpNodeHandle -Children-LldpTlvConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LldpTlvConfig from object:$lldpNodeHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::get $lldpTlvConfigHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get info from object:$lldpNodeHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set returnMsg "$routerHandle $lldpTlvConfigHandle"
    
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigCommonParameters { deviceHandle commonConfigTable objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "ConfigCommonParameters"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: ConfigCommonParameters "
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $commonConfigTable commonTable
    upvar 1 $objectHandleArrName objectHandleArr
    
    set objectHandleArr(Router) $deviceHandle
    
    if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-EthIIIf]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-EthIIIf from object:$deviceHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router-EthIIIf) $EthIIIfHandle
    }
    
    if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-VlanIf]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-VlanIf from port:$routerHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        if { ($VlanIfHandle == "") && [info exists commonTable(Router-VlanIf)]} {
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -AttachToIf $EthIIIfHandle -DeviceList $deviceHandle -IfStack VlanIf -IfCount 1 -IsPrimaryIf TRUE} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not do StcPerform IfStackAttach :$errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-VlanIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not get -Children-VlanIf from object:$deviceHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {[catch {set handleList [::sth::sthCore::invoke stc::get $EthIIIfHandle -stackedonendpoint-Sources]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not get -stackedonendpoint-Sources from object:$EthIIIfHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            foreach handle $handleList {
                if {[catch {::sth::sthCore::invoke stc::config $handle "-stackedonendpoint-Targets $VlanIfHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not config -stackedonendpoint-Targets $handle to $objectHandleArr($objecType), errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
        set objectHandleArr(Router-VlanIf) $VlanIfHandle
    }
    
    if {[catch {set Ipv4IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-Ipv4If]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv4If from port:$routerHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        if { ($Ipv4IfHandle == "") && [info exists commonTable(Router-Ipv4If)]} {
            if { $objectHandleArr(Router-VlanIf) != ""} {
                set attchIf $objectHandleArr(Router-VlanIf)
            } else {
                set attchIf $objectHandleArr(Router-EthIIIf)
            }
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -AttachToIf $attchIf -DeviceList $deviceHandle -IfStack Ipv4If -IfCount 1 -IsPrimaryIf TRUE} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not do StcPerform IfStackAttach :$errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {[catch {set Ipv4IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-Ipv4If]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not get -Children-VlanIf from object:$deviceHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
        set objectHandleArr(Router-Ipv4If) $Ipv4IfHandle
    }
    
    if {[catch {set Ipv6IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-Ipv6If]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv6If from object:$deviceHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        if { ($Ipv6IfHandle == "") && [info exists commonTable(Router-Ipv6If)]} {
            if { $objectHandleArr(Router-VlanIf) != ""} {
                set attchIf $objectHandleArr(Router-VlanIf)
            } else {
                set attchIf $objectHandleArr(Router-EthIIIf)
            }
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -AttachToIf $attchIf -DeviceList $deviceHandle -IfStack Ipv6If -IfCount 1 -IsPrimaryIf TRUE} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not do StcPerform IfStackAttach :$errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {[catch {set Ipv6IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-Ipv6If]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv6If from object:$deviceHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            } else {
                set objectHandleArr(Router-Ipv6If) $Ipv6IfHandle
            }
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -AttachToIf $attachIf -DeviceList $deviceHandle -IfStack Ipv6If -IfCount 1 -IsPrimaryIf TRUE} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not do StcPerform IfStackAttach :$errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            } else {
                if {[catch {set handleList [::sth::sthCore::invoke stc::get $deviceHandle -Children-Ipv6If]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not get -Children-Ipv6If from object:$deviceHandle." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                
                set objectHandleArr(Router-LinkLocalIpv6If) [lindex $handleList 1]
                if { ![info exists commonTable(Router-LinkLocalIpv6If) ]} {
                    set commonTable(Router-LinkLocalIpv6If) "-Address fe80::1"
                }
            }
        } else {
            set objectHandleArr(Router-Ipv6If) [lindex $Ipv6IfHandle 0]
            set objectHandleArr(Router-LinkLocalIpv6If) [lindex $Ipv6IfHandle 1]
        }
        
    }
    
    if {[catch {set lldpNodeHandle [::sth::sthCore::invoke stc::get $deviceHandle -Children-LldpNodeConfig ]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not create LldpNodeConfig on router:$deviceHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set objectHandleArr(Router-LldpNodeConfig) $lldpNodeHandle
    }
    
    if { [catch {::sth::Lldp::ConfigToStc objectHandleArr commonTable returnKeyedList cmdState} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error! errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigToStc { handleArr attrArr returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _hltCmdName "ConfigToStc"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $handleArr objectHandleArr
    upvar 1 $attrArr commonTable
    
    foreach objecType [array names objectHandleArr] {
        if {[info exists commonTable($objecType)]} {
            if {[catch {::sth::sthCore::invoke stc::config $objectHandleArr($objecType) $commonTable($objecType)} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not config $commonTable($objecType) to $objectHandleArr($objecType), errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    
    return $SUCCESS
}

proc ::sth::Lldp::FormConfigParameter { inputs myNameSpace configTableName commonConfigTable stepConfigTable otherConfigTable  } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    set _OrigHltCmdName "emulation_lldp_config"
    set _hltCmdName "FormConfigParameter"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: FormConfigParameter "
    
    upvar 1 $commonConfigTable commonTable
    upvar 1 $stepConfigTable stepTable
    upvar 1 $otherConfigTable otherTable
    
    set configSwitchNameValueList ""
    
    #eliminate the switches which have default value but need not to be configured.(cause re-configuring, a waste of time)
    set eliminateDefault 0
    if { $configTableName == $_OrigHltCmdName} {
        if { $switchToValue(mode) == "modify"} {
            set eliminateDefault 1
        }
    }
    if { $eliminateDefault } {
        foreach {switchName switchValue} $inputs {
            set name [string range $switchName 1 end ]
            
            if { [lsearch [array names switchToValue] $name] >-1 } {
                lappend configSwitchNameValueList $name $switchToValue($name)
            }
        }
    } else {
        set configSwitchNameValueList [array get switchToValue]
    }
    
    
    foreach {switchName switchValue} $configSwitchNameValueList {
        if { ($switchName == "mandatory_args") || ($switchName == "optional_args") } {
            continue
        }
        
        if { $configTableName == "emulation_lldp_dcbx_tlv_config" } {
            set dcbxVersion $switchToValue(version_num)
            if { $dcbxVersion == "ver_100" } {
                if {[string first "tlv2" $switchName ] > -1} {
                    puts "Warning: the swith -$switchName is not support in DCBX version 1.00, will be ignored."
                    continue
                }
            } elseif { $dcbxVersion == "ver_103" } {
                if {[string first "tlv1" $switchName ] > -1} {
                    puts "Warning: the swith -$switchName is not support in DCBX version 1.03, will be ignored."
                    continue
                }
            }
        }
        
        set procFuncName [set $myNameSpace$configTableName\_procfunc($switchName)]
        set stcobj [set $myNameSpace$configTableName\_stcobj($switchName)]
        set stcattr [set $myNameSpace$configTableName\_stcattr($switchName)]
        
        if {![catch {set attrValue [::sth::sthCore::getFwdmap $myNameSpace $configTableName $switchName $switchValue]} getStatus]} {
            set switchValue $attrValue
        }
        
        if { $procFuncName == "CommonConfigProcess" } {
            if { [info exists commonTable($stcobj)] } {
                lappend commonTable($stcobj) "-$stcattr" $switchValue
            } else {
                set commonTable($stcobj) "-$stcattr $switchValue"
            }
            
        } elseif { $procFuncName == "StepConfigProcess" } {
            if { [info exists stepTable($stcobj)] } {
                lappend stepTable($stcobj) "-$stcattr" $switchValue
            } else {
                set stepTable($stcobj) "-$stcattr $switchValue"
            }
        } elseif { [string first "OtherConfigProcess" $procFuncName] >-1 } {
            if { [info exists otherTable($procFuncName)] } {
                lappend otherTable($procFuncName) $switchName "$stcobj $stcattr \{$switchValue\}"
            } else {
                set otherTable($procFuncName) [list $switchName "$stcobj $stcattr \{$switchValue\}"]
            }
        }
    }
    
    foreach objectType [array names stepConfigTable] {
        foreach {switchName switchValue} $stepConfigTable($objectType) {
            if { [set index [lsearch $commonConfigTable($objectType) "switchName" ]] == -1} {
                set stepConfigTable($objectType) [lreplace $stepConfigTable($objectType) $index [expr $index + 1]]
            }
            if { $stepConfigTable($objectType) == "" } {
                unset stepConfigTable($objectType)
            }
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::emulation_lldp_control_start { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_control"
    set _hltCmdName "emulation_lldp_control_start"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach lldpHandle $switchToValue(handle) {
        if { ![::sth::Lldp::IsLldpHandleValid $lldpHandle errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $lldpHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not perform DeviceStart on $lldpHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS     
}

proc ::sth::Lldp::emulation_lldp_control_stop { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_control"
    set _hltCmdName "emulation_lldp_control_stop"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach lldpHandle $switchToValue(handle) {
        if { ![::sth::Lldp::IsLldpHandleValid $lldpHandle errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $lldpHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not perform DeviceStop on $lldpHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS     
}

proc ::sth::Lldp::emulation_lldp_control_pause { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_control"
    set _hltCmdName "emulation_lldp_control_pause"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach lldpHandle $switchToValue(handle) {
        if { ![::sth::Lldp::IsLldpHandleValid $lldpHandle errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        set lldpNodeConfigHandle $errMsg
        
        if {[catch {::sth::sthCore::invoke stc::perform LldpPause -NodeList $lldpNodeConfigHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not perform LldpPause on $lldpNodeConfigHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS     
}

proc ::sth::Lldp::emulation_lldp_control_resume { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lldp_control"
    set _hltCmdName "emulation_lldp_control_resume"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach lldpHandle $switchToValue(handle) {
        if { ![::sth::Lldp::IsLldpHandleValid $lldpHandle errMsg]} {
            ::sth::sthCore::processError returnKeyedList $errMsg {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        set lldpNodeConfigHandle $errMsg
        
        if {[catch {::sth::sthCore::invoke stc::perform LldpResume -NodeList $lldpNodeConfigHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not perform LldpResume on $lldpNodeConfigHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS     
}

proc ::sth::Lldp::emulation_lldp_info_img { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lldp::switchToValue
    variable ::sth::GBLHNDMAP
    set myNameSpace "::sth::Lldp::"

    set _OrigHltCmdName "emulation_lldp_info"
    set _hltCmdName "emulation_lldp_info_img"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { ![::sth::Lldp::IsLldpHandleValid $switchToValue(handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    set lldpNodeHandle $errMsg
    
    #set lldpHandle $switchToValue(handle)
    
    set mode $switchToValue(mode)
    
    if { $mode == "both"} {
        set mode "lldp | dcbx"
    }
    
    #set resultTypeList ""
    
    set lldpResultTypeList "LldpNodeResults LldpNeighborResults"
    set lldpResultTableList "emulation_lldp_node_results emulation_lldp_neighbor_results"
    
    array set dcbxResultTypeArr {
        basic LldpDcbxResult
        feature_basic LldpDcbxFeatureResult
        prio_alloc DcbxPriorityAllocationResult
        bw_alloc DcbxBandwidthAllocationResult
        pfc DcbxPriorityFlowControlResult
        fcoe_prio DcbxFcoePriorityResult
        logic_link DcbxLogicalLinkResult
        bcn_parameter DcbxBcnParameterResult
        bcn_mode DcbxBcnModeResult
    }
    array set dcbxResultTableArr {
        basic emulation_lldp_dcbx_result
        feature_basic emulation_lldp_dcbx_feature_result
        prio_alloc emulation_dcbx_priority_allocation_result
        bw_alloc emulation_dcbx_bandwidth_allocaton_result
        pfc emulation_dcbx_priority_flow_control_result
        fcoe_prio emulatiion_dcbx_fcoe_priority_result
        logic_link emulation_dcbx_logic_link_result
        bcn_parameter emulation_dcbx_bcn_parameter_result
        bcn_mode emulation_dcbx_bcn_mode_result
    }
    
    set resultObjectTypeList ""
    set returnTableNameList ""
    set subscribeObjTypeList ""
    if { [string first "lldp" $mode] > -1 } {
        set returnTableNameList $lldpResultTableList
        set resultObjectTypeList $lldpResultTypeList
        if { !$::sth::Lldp::ResultQueryCreateTable(lldp)} {
            set subscribeObjTypeList $lldpResultTypeList
            set ::sth::Lldp::ResultQueryCreateTable(lldp) 1
        }
    }
    if { [string first "dcbx" $mode] > -1 } {
        set dcbxInfoType $switchToValue(dcbx_info_type)
        
        foreach subtype [split $dcbxInfoType "|"] {
        lappend returnTableNameList $dcbxResultTableArr($subtype)
        lappend resultObjectTypeList $dcbxResultTypeArr($subtype)
            if { !$::sth::Lldp::ResultQueryCreateTable($subtype)} {
            lappend subscribeObjTypeList $dcbxResultTypeArr($subtype)
            set ::sth::Lldp::ResultQueryCreateTable($subtype) 1
            }
        }
    }
    
    foreach resultType $subscribeObjTypeList {
        set $myNameSpace\createResultQuery 0
        if {[catch {::sth::sthCore::ResultDataSetSubscribe $myNameSpace LldpNodeConfig $resultType returnKeyedList} errMsg]} {
            ::sth::sthCore::processError "Internal Command Error while subscribing results. Error: $errMsg" {}
            return $FAILURE
        }
        
    }
    
    if {[catch {::sth::Lldp::FormResult $myNameSpace $returnTableNameList $lldpNodeHandle $resultObjectTypeList returnKeyedList $cmdState} errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    #if { [string first "lldp" $mode] > -1 } {
    #    if {[catch {::sth::Lldp::GetLldpResults $lldpNodeHandle "lldp" returnKeyedList cmdState} errMsg]} {
    #        ::sth::sthCore::processError returnKeyedList $errMsg {}
    #        set cmdState $FAILURE
    #        return $returnKeyedList
    #    }
    #}
    #if { [string first "dcbx" $mode] > -1} {
    #    if {[catch {::sth::Lldp::GetLldpResults $lldpNodeHandle "dcbx" returnKeyedList cmdState} errMsg]} {
    #        ::sth::sthCore::processError returnKeyedList $errMsg {}
    #        set cmdState $FAILURE
    #        return $returnKeyedList
    #    }
    #}
    
    
    return $SUCCESS
}

proc ::sth::Lldp::FormResult { myNameSpace returnTableNameList resultParentHandle resultObjectTypeList returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: FormResult "
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    #form result table
    array set resultObjectHandleArr "
        LldpNodeConfig $resultParentHandle
    "
    
    array set resultTable {}
    
    if {[catch {set resultAttrValueList [::sth::sthCore::invoke stc::get $resultParentHandle -DeviceState]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -DeviceState from result object: $resultParentHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set resultTable($resultParentHandle,DeviceState) $resultAttrValueList
    }
    
    foreach resultObjectType "$resultObjectTypeList" {
        if {[catch {set resultObjectHandleArr($resultObjectType) [::sth::sthCore::invoke stc::get $resultParentHandle -Children-$resultObjectType]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-$resultObjectType from $resultParentHandle." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        foreach resultObjectHandle $resultObjectHandleArr($resultObjectType) {
            if {[catch {set resultAttrValueList [::sth::sthCore::invoke stc::get $resultObjectHandle]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not get attributes from result object: $resultObjectHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            foreach {attrName attrValue} $resultAttrValueList {
                set name [string range $attrName 1 end]
                set resultTable($resultObjectHandle,$name) $attrValue
            }
        }
    }
    
    #form return keyed list
    foreach returnTableName $returnTableNameList {
        set returnKeyList [array names $myNameSpace$returnTableName\_mode]
        
        foreach returnKey $returnKeyList {
            set stcobj [set $myNameSpace$returnTableName\_stcobj($returnKey)]
            set stcattr [set $myNameSpace$returnTableName\_stcattr($returnKey)]
            
            if {[string equal $stcobj "_none_"]} {
                    #do nothing, present for further update
            } else {
                set index 1
                
                if { (![info exists resultObjectHandleArr($stcobj)]) || ($resultObjectHandleArr($stcobj) == "")} {
                    #set namePrefix [concat [set $myNameSpace$returnTableName\_mode($returnKey)] "."]
                    #puts $namePrefix
                    #keylset returnKeyedList [concat $namePrefix [regsub {xxx} $returnKey $index] ""] "N/A"
                    keylset returnKeyedList [regsub {xxx} $returnKey $index] "N/A"
                } else {
                    foreach resultObjectHandle $resultObjectHandleArr($stcobj) {
                        #special: deal with prefix of return key name
                        #set namePrefix [concat [set $myNameSpace$returnTableName\_mode($returnKey)] "."]
                        #puts $namePrefix
                        #keylset returnKeyedList [concat $namePrefix [regsub {xxx} $returnKey $index] ""] $resultTable($resultObjectHandle,$stcattr)
                        keylset returnKeyedList [regsub {xxx} $returnKey $index] $resultTable($resultObjectHandle,$stcattr)
                    }
                }
                incr index
            }
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::IsLldpHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set cmdStatus $::sth::Lldp::FALSE
    
    upvar 1 $msgName errorMsg

    if {[catch {set deviceHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Router]} getStatus]} {
        ::sth::sthCore::log error "No router exists under Project Handle:$::sth::GBLHNDMAP(project)"
        return $FAILURE
    } else {
        foreach deviceHandle $deviceHandleList {
            if {[string equal $deviceHandle $handle]} {
                set cmdStatus $::sth::Lldp::TRUE
                break
            }
        }
        
        if {[catch {set lldpNodeConfigHandle [::sth::sthCore::invoke stc::get $deviceHandle -children-LldpNodeConfig]} getStatus]} {
            set cmdStatus $::sth::Lldp::FALSE
        }

        if {$cmdStatus == $::sth::Lldp::TRUE} {
            set errorMsg $lldpNodeConfigHandle
            return $SUCCESS
        } else {
            set errorMsg "Value ($handle) is not a valid Lldp handle"
            return $FAILURE        
        }        
    }
}

proc ::sth::Lldp::CreateObject { originHandle cObjectType objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $objectHandleArrName objectHandleArr
    
    foreach { pType cType } $cObjectType {
        if {[catch {set pHandle [::sth::sthCore::invoke stc::create $pType -under $originHandle]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        } else {
            if { $pType == "dcbxCtlTlv" } {
                if {[catch {::sth::sthCore::invoke stc::config $pHandle "-ackNo 0 -seqNo 0"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not config -ackNo 0 -seqNo 0 to object: $pHandle, errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            
            lappend objectHandleArr($pType) $pHandle
        }
        
        if {[catch {::sth::Lldp::CreateObject $pHandle $cType objectHandleArr returnKeyedListVarName cmdStatusVarName} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigObjectDuplicateParameter { objectTypeList attrName attrValue objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $objectHandleArrName objectHandleArr
    
    foreach objectType $objectTypeList {
        foreach objectHandle $objectHandleArr($objectType) {
            if { ($objectType == "bwg_percentage") || ( $objectType == "prioAllocation") || ( $objectType == "pgAllocation")} {
                set attrList ""
                foreach attr $attrName value $attrValue {
                    append attrList " -$attr $value"
                }
                if {[catch {::sth::sthCore::invoke stc::config $objectHandle $attrList} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not config $attrList to object: $objectHandle, errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            } elseif {$objectType == "pfcTlv"} {
                set attrList ""
                foreach attr $attrName value [split $attrValue ""] {
                    append attrList " -$attr $value"
                }
                if {[catch {::sth::sthCore::invoke stc::config $objectHandle $attrList} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not config $attrList to object: $objectHandle, errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            } else {
                if {[catch {::sth::sthCore::invoke stc::config $objectHandle "-$attrName \{$attrValue\}"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not config -$attrName $attrValue to object: $objectHandle, errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigMultiAttributesVaryParameters { objectTypeList attrName attrValue objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $objectHandleArrName objectHandleArr
    
    foreach objectType $objectTypeList {
        foreach objectHandle $objectHandleArr($objectType) {
            set attrList ""
            set ValueList $attrValue
            if {$objectType == "pfcTlv"} {
                set ValueList [split $attrValue ""]
            }
            foreach attr $attrName value $ValueList {
                append attrList " -$attr $value"
            }
            if {[catch {::sth::sthCore::invoke stc::config $objectHandle $attrList} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not config $attrList to object: $objectHandle, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigMultiObjectTypesVaryParameters { objectTypeList attrName attrValue objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $objectHandleArrName objectHandleArr
    
    foreach objectType $objectTypeList value $attrValue {
        if {[catch {::sth::sthCore::invoke stc::config $objectHandleArr($objectType) "-$attrName \{$value\}"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config -$attrName $value to object: $objectHandle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigMultiObjectsVaryParameters { objectTypeList attrName attrValue objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    upvar 1 $objectHandleArrName objectHandleArr
    
    foreach objectType $objectTypeList  {
        foreach objectHandl $objectHandleArr($objectType) value $attrValue {
            if {[catch {::sth::sthCore::invoke stc::config $objectHandl "-$attrName \{$value\}"} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not config -$attrName $value to object: $objectHandle, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::CreateMultiObjects { pObjHandle cObjType count objectHandleArrName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set myNameSpace "::sth::Lldp::"
    
    upvar 1 $objectHandleArrName objectHandleArr
    
    for {set i 0} { $i < $count } {incr i} {
            if {[catch {set handle [::sth::sthCore::invoke stc::create $cObjType -under $pObjHandle]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            } else {
                lappend objectHandleArr($cObjType) $handle
            }
        
    }
    
    return $SUCCESS
}

proc ::sth::Lldp::ConfigDcbxTlvs { parameterList lldpTlvConfigHdl returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "ConfigDcbxTlvs"
    set _hltCmdName "FormConfigParameter"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: ConfigDcbxTlvs "
    
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    variable ::sth::Lldp::switchToValueDcbx
    set myNameSpace "::sth::Lldp::"
    set configTableName "emulation_lldp_dcbx_tlv_config"
    
    
    set argList [lindex [lindex $parameterList 1] 2]
    if {[catch {::sth::sthCore::commandInit ::sth::Lldp::lldpTable $argList $myNameSpace $configTableName ::sth::Lldp::switchToValueDcbx slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList
    }
    
    array set CommonHdlArr " LldpTlvConfig $lldpTlvConfigHdl"
    array set T1_PGTlvHdlArr {}
    array set T1_PFCTlvHdlArr {}
    array set T1_BCNTlvHdlArr {}
    array set T1_AppTlvHdlArr {}
    array set T1_LLDTlvHdlArr {}
    array set T1_CustomTlvHdlArr {}
    array set T2_PGTlvHdlArr {}
    array set T2_PFCTlvHdlArr {}
    array set T2_AppProTlvHdlArr {}
    array set T2_CustomTlvHdlArr {}
    
    array set objectHdlIndexArr {
        Common CommonHdlArr
        PDU_DcbxType1 CommonHdlArr
        PDU_DcbxType2 CommonHdlArr
        TLV_DcbxPG_Type1 T1_PGTlvHdlArr
        TLV_DcbxPFC_Type1 T1_PFCTlvHdlArr
        TLV_DcbxBCN_Type1 T1_BCNTlvHdlArr
        TLV_DcbxApp_Type1 T1_AppTlvHdlArr
        TLV_DcbxLLD_Type1 T1_LLDTlvHdlArr
        TLV_DcbxCustom_Type1 T1_CustomTlvHdlArr
        TLV_DcbxPG_Type2 T2_PGTlvHdlArr
        TLV_DcbxPFC_Type2 T2_PFCTlvHdlArr
        TLV_DcbxAppPro_Type2 T2_AppProTlvHdlArr
        TLV_DcbxCustom_Type2 T2_CustomTlvHdlArr
    }

    #array set CommonParArr {}
    #array set T1_PGTlvParArr {}
    #array set T1_PFCTlvParArr {}
    #array set T1_BCNTlvParArr {}
    #array set T1_AppTlvParArr {}
    #array set T1_LLDTlvParArr {}
    #array set T1_CustomTlvParArr {}
    #array set T2_PGTlvParArr {}
    #array set T2_PFCTlvParArr {}
    #array set T2_AppProTlvParArr {}
    #array set T2_CustomTlvParArr {}
    #
    #array set objectParIndexArr {
    #    Common CommonParArr
    #    PDU_DcbxType1 CommonParArr
    #    PDU_DcbxType2 CommonParArr
    #    TLV_DcbxPG_Type1 T1_PGTlvParArr
    #    TLV_DcbxPFC_Type1 T1_PFCTlvParArr
    #    TLV_DcbxBCN_Type1 T1_BCNTlvParArr
    #    TLV_DcbxApp_Type1 T1_AppTlvParArr
    #    TLV_DcbxLLD_Type1 T1_LLDTlvParArr
    #    TLV_DcbxCustom_Type1 T1_CustomTlvParArr
    #    TLV_DcbxPG_Type2 T2_PGTlvParArr
    #    TLV_DcbxPFC_Type2 T2_PFCTlvParArr
    #    TLV_DcbxAppPro_Type2 T2_AppProTlvParArr
    #    TLV_DcbxCustom_Type2 T2_CustomTlvParArr
    #}
    
    foreach prio_switch $slist {
        set switchName [lindex $prio_switch 1]
        if { ($switchName == "mandatory_args") || ($switchName == "optional_args") } {
            continue
        }
        set dependSwitch [lindex [set $myNameSpace$configTableName\_dependency($switchName)] 0]
        set dependValue [lindex [set $myNameSpace$configTableName\_dependency($switchName)] 1]
        if { $dependSwitch != "_none_"} {
            if { $::sth::Lldp::switchToValueDcbx($dependSwitch) != $dependValue} {
                continue
            }
        }
        
        set procFuncName [set $myNameSpace$configTableName\_procfunc($switchName)]
        set stcattr [set $myNameSpace$configTableName\_stcattr($switchName)]
        set switchValue $switchToValueDcbx($switchName)
        
        set stcobj [set $myNameSpace$configTableName\_stcobj($switchName)]
        set originHdlArrIndex [lindex [split $stcobj "-"] 0]
        set stcObj [lindex [split $stcobj "-"] 1]
        set originObjHdlArrName $objectHdlIndexArr($originHdlArrIndex)
        
        if {![catch {set attrValue [::sth::sthCore::getFwdmap $myNameSpace $configTableName $switchName $switchValue]} getStatus]} {
            set switchValue $attrValue
        }
        
        if { $switchValue == ""} {
            continue
        }
        
        switch $procFuncName {
            CreateObject {
                set originObjHandle [set $originObjHdlArrName\($stcObj)]
                set targetObjectType [set $myNameSpace$switchValue]
                set targetObjHdlArrName $objectHdlIndexArr($switchValue)
                if {[catch {::sth::Lldp::CreateObject $originObjHandle $targetObjectType $targetObjHdlArrName returnKeyedList cmdState} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            ConfigParameter {
                if {[catch {::sth::Lldp::ConfigObjectDuplicateParameter $stcObj $stcattr $switchValue $originObjHdlArrName returnKeyedList cmdState} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            ConfigMultiObjectsVaryParameters -
            ConfigMultiAttributesVaryParameters {
                set cmd "::sth::Lldp::$procFuncName \{$stcObj\} \{$stcattr\} \{$switchValue\} $originObjHdlArrName returnKeyedList cmdState"
                if {[catch {eval $cmd} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            CreateMultiObjects {
                set count [expr $switchValue - 1]
                set originObjHandle [set $originObjHdlArrName\($stcObj)]
                if {[catch {::sth::Lldp::CreateMultiObjects $originObjHandle $stcattr $count $originObjHdlArrName returnKeyedList cmdState} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
    }
    
    return $SUCCESS
}
