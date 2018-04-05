
namespace eval ::sth::bfd {
    variable bfd_subscription_state 0
}

proc ::sth::bfd::emulation_bfd_config_create {returnKeyedListVarName {level 1}} {

    variable userArgsArray
    variable bfd_subscription_state
    set mode create

    if {![info exists userArgsArray(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle." {}
        return -code error $returnKeyedList
    }

    if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
        return -code error $returnKeyedList
    }
    upvar $level $returnKeyedListVarName returnKeyedList

    if {[info exists userArgsArray(bfd_cc_channel_type)] || [info exists userArgsArray(bfd_cv_channel_type)] } {
        set bfdGlobHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-BfdGlobalConfig]
        if {$bfdGlobHdl == ""} {
            set bfdGlobHdl [::sth::sthCore::invoke stc::create BfdGlobalConfig -under $::sth::GBLHNDMAP(project)]
        }
        if {[info exists userArgsArray(bfd_cc_channel_type)]} {
            ::sth::sthCore::invoke stc::config $bfdGlobHdl -BfdCcChannelType $userArgsArray(bfd_cc_channel_type)
        }
        if {[info exists userArgsArray(bfd_cv_channel_type)]} {
            ::sth::sthCore::invoke stc::config $bfdGlobHdl -BfdCvChannelType $userArgsArray(bfd_cv_channel_type)
        }
    }

    set retVal [catch {

    # set default values for non-user defined switches
    foreach key [array names ::sth::bfd::emulation_bfd_config_default] {
        if {![info exists ::sth::bfd::userArgsArray($key)]} {
            set defaultValue [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $key default]
            if {![string match -nocase $defaultValue "_none_"]} {
                set ::sth::bfd::userArgsArray($key) $defaultValue
            }
        }
    }

    if {[string match -nocase $userArgsArray(count) 0]} {
            ::sth::sthCore::processError returnKeyedList "Invalid \"-count\" value $userArgsArray(count)" {}
            return -code error $returnKeyedList
    }

        set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]

        set routerList [list]
        set ipv4SessionList [list]
        set ipv6SessionList [list]
        for {set j 1} {$j <= $userArgsArray(count)} {incr j} {

            switch -exact -- $userArgsArray(ip_version) {
                "IPv4" {
                    set ipVersion 4
                }
                "IPv6" {
                    set ipVersion 6
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error: Unknown ip_version $userArgsArray(ip_version)." {}
                    return -code error $returnKeyedList
                }
            }

            # create the router
            set router($j) [::sth::sthCore::invoke stc::create "Router" -under $::sth::GBLHNDMAP(project)]

            configRouter $router($j) $mode $j

            # if ATM option is provided, configure ATM stack for BFD router,
            # otherwise, configure the ethernet stack for BFD router
            if {[info exists userArgsArray(vci)]||[info exists userArgsArray(vpi)]} {
                set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $router($j)]
                configAtmIf $atmResultIf $mode $j
            } else {
                set ethiiIf [::sth::sthCore::invoke stc::create EthIIIf -under $router($j)]
                configEthIIIntf $ethiiIf $mode $j
            }

            # create & configure vlan if option is provided
            # if there is aal5if, vlan is not allowed
            if {$vlanOptFound && ![info exists atmResultIf]} {
                set ethernetii_vlan 0
                set ethernetii_qinq 0

                if {([info exists userArgsArray(vlan_id1)]&&(![info exists userArgsArray(vlan_id2)]))
                    || ([info exists userArgsArray(vlan_id2]&&(![info exists userArgsArray(vlan_id1]))} {
                    set ethernetii_vlan 1
                }
                if {([info exist userArgsArray(vlan_id1)]&&[info exists userArgsArray(vlan_id2)])} {
                    set ethernetii_qinq 1
                }
                if {$ethernetii_vlan} {
                    set vlanIf [::sth::sthCore::invoke stc::create VlanIf -under $router($j)]
                    if {[info exists userArgsArray(vlan_id1)]} {
                        configVlanIfInner $vlanIf $mode $j
                    } elseif {[info exists userArgsArray(vlan_id2)]} {
                        configVlanIfOuter $vlanIf $mode $j
                    }
                }
                if {$ethernetii_qinq} {
                    #vlan_id_inner
                    set vlanIf_inner [::sth::sthCore::invoke stc::create VlanIf -under $router($j)]
                    configVlanIfInner $vlanIf_inner $mode $j

                    #vlan_id_outer
                    set vlanIf_outer [::sth::sthCore::invoke stc::create VlanIf -under $router($j)]
                    configVlanIfOuter $vlanIf_outer $mode $j
                }
            }

            # configure ip stack for BFD router
            set ipIf [::sth::sthCore::invoke stc::create Ipv[string trim $ipVersion]If -under $router($j)]

            configIpInterface $ipIf $mode $j

            #configure a link local stack in case of ipv6
            if {$ipVersion == 6} {
                set linkLocalHandle [::sth::sthCore::invoke stc::create Ipv[string trim $ipVersion]If -under $router($j)]

                configLinkLocal $linkLocalHandle $mode $j
            }

            #create BFD router and config BFD router settings
            set bfdRtrCfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $router($j)]

            configBfdRouter $bfdRtrCfg $mode $j

            if {[string match -nocase $ipVersion 4]} {
                #create & configure BFD IPv4 CPI Session
                set bfdIpv4CpiSession [::sth::sthCore::invoke stc::create "BfdIpv4ControlPlaneIndependentSession" -under $bfdRtrCfg]
                configBFDCpiSession $bfdIpv4CpiSession $mode $j
                lappend ipv4SessionList $bfdIpv4CpiSession
                set Ipv4NetworkBlock [lindex [::sth::sthCore::invoke stc::get $bfdIpv4CpiSession -children-Ipv4NetworkBlock] 0]

                configIpNetworkBlock $Ipv4NetworkBlock $mode $j


            } elseif {[string match -nocase $ipVersion 6]} {
                #create & configure BFD IPv6 CPI Session
                set bfdIpv6CpiSession [::sth::sthCore::invoke stc::create "BfdIpv6ControlPlaneIndependentSession" -under $bfdRtrCfg]

                configBFDCpiSession $bfdIpv6CpiSession $mode $j
                lappend ipv6SessionList $bfdIpv6CpiSession
                set Ipv6NetworkBlock [lindex [::sth::sthCore::invoke stc::get $bfdIpv6CpiSession -children-Ipv6NetworkBlock] 0]

                configIpNetworkBlock $Ipv6NetworkBlock $mode $j
            }
            #setup relations
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $router($j) "-AffiliationPort-targets $userArgsArray(port_handle)"]
            #adjust the stack for vlan relation
            if {[info exists atmResultIf]} {
                lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $atmResultIf" ]
            } else {
                if {$vlanOptFound} {
                    if {$ethernetii_vlan} {
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $vlanIf"]
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $vlanIf "-StackedOnEndpoint-targets $ethiiIf"]
                    }
                    if {$ethernetii_qinq} {
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $vlanIf_inner"]
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $vlanIf_inner "-StackedOnEndpoint-targets $vlanIf_outer"]
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $vlanIf_outer "-StackedOnEndpoint-targets $ethiiIf"]
                    }
                } else {
                    lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $ethiiIf" ]
                }
            }

            #adjust the stack for link local stack relation
            if {$ipVersion == 6} {
                set ipstacking "$ipIf $linkLocalHandle"
                lappend cmd_list [list ::sth::sthCore::invoke stc::config $linkLocalHandle "-StackedOnEndpoint-targets $ethiiIf" ]
            } else {
                set ipstacking "$ipIf"
            }

            lappend cmd_list [list ::sth::sthCore::invoke stc::config $router($j) "-TopLevelIf-targets {$ipstacking}"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $router($j) "-PrimaryIf-targets {$ipstacking}"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets {$ipstacking}"]

            foreach cmd $cmd_list {
                if {[catch {eval $cmd} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
                    return -code error $returnKeyedList
                }
            }

            #build router handle into keyed list
            lappend routerList $router($j)
        }

        if {$bfd_subscription_state == 0} {
            # Create the BFD result dataset
            set bfdResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set bfdResultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $bfdResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId BfdRouterConfig -ResultClassId BfdRouterResults"]
            if {[string match -nocase $ipVersion 4]} {
                set bfdResultQuery2 [::sth::sthCore::invoke stc::create "ResultQuery" -under $bfdResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId BfdIpv4SessionResults"]
            } elseif {[string match -nocase $ipVersion 6]} {
                set bfdResultQuery2 [::sth::sthCore::invoke stc::create "ResultQuery" -under $bfdResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId BfdIpv6SessionResults"]
            }
        }


        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying BFD configuration: $err"
            return -code error $returnKeyedList
        }

        if {$bfd_subscription_state == 0} {
        # Subscribe to the datasets
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $bfdResultDataSet
            set bfd_subscription_state 1
        }

        keylset returnKeyedList handle $routerList
        keylset returnKeyedList handles $routerList
        if {$ipv4SessionList != ""} {
            keylset returnKeyedList ipv4_session_handle $ipv4SessionList
        }
        if {$ipv6SessionList != ""} {
            keylset returnKeyedList ipv6_session_handle $ipv6SessionList
        }

    } returnedString]
    ::sth::sthCore::invoke stc::apply
    return -code $retVal $returnedString
}

proc ::sth::bfd::emulation_bfd_config_modify {returnKeyedListVarName {level 1}} {

    variable userArgsArray
    variable sortedSwitchPriorityList
    set mode modify

    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return -code error $returnKeyedList
    }

    upvar $level $returnKeyedListVarName returnKeyedList

    set unsupportedModifyOptions {port_handle count}

    set retVal [catch {
        set routerHandle $userArgsArray(handle)

        #check if the handle is a valid Bfd handle or not
        if {![IsBfdRouterHandleValid $routerHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error: $routerHandle is not a valid BFD router handle" {}
            return -code error $returnKeyedList
        }

        set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
        if {$vlanOptFound} {
            set ethernetii_vlan 0
            set ethernetii_qinq 0
            if {([info exists userArgsArray(vlan_id1)]&&(![info exists userArgsArray(vlan_id2)]))
                || ([info exists userArgsArray(vlan_id2]&&(![info exists userArgsArray(vlan_id1]))} {
                    set ethernetii_vlan 1
            }
            if {([info exist userArgsArray(vlan_id1)]&&[info exists userArgsArray(vlan_id2)])} {
                set ethernetii_qinq 1
            }
        }

        set functionsToRun {}
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                # make sure the option is supported
                if {![::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $switchname supported]} {
                    ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                    return -code error $returnKeyedList
                }
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                ::sth::sthCore::processError returnKeyedList "unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList
                }

                if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $switchname mode] "_none_"]} { continue }
                set func [::sth::sthCore::getModeFunc ::sth::bfd:: emulation_bfd_config $switchname modify]
                if {[lsearch $functionsToRun $func] == -1} {
                    lappend functionsToRun $func
                }
            }
        }

        foreach func $functionsToRun {
        # these functions are mapped to switches in bfdTable.tcl
            switch -- $func {
                configEthIIIntf {
                    set EthiiIf [::sth::sthCore::invoke stc::get $routerHandle -children-ethiiif]
                    configEthIIIntf $EthiiIf $mode 1
                }
                configRouter {
                    configRouter $routerHandle $mode 1
                }
                configVlanIfInner {
                    set vlanIf [::sth::sthCore::invoke stc::get $routerHandle -children-vlanif ]
                    if {$ethernetii_vlan} {
                        configVlanIfInner $vlanIf $mode 1
                    } elseif {$ethernetii_qinq} {
                        configVlanIfInner [lindex $vlanIf 0] $mode 1
                    }
                }
                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $routerHandle -children-vlanif]
                    if {$ethernetii_vlan} {
                        configVlanIfOuter $vlanIf $mode 1
                    } elseif {$ethernetii_qinq} {
                        configVlanIfOuter [lindex $vlanIf 1] $mode 1
                    }

                }
                configIpInterface {
                    set rtrChild [::sth::sthCore::invoke stc::get $routerHandle -children]
                    foreach ipResultIf $rtrChild {
                        if {[string match -nocase "ipv4if*" $ipResultIf]} {
                            set ipVersion 4
                            set ipIf $ipResultIf
                            break
                        } elseif {[string match -nocase "ipv6if*" $ipResultIf]} {
                            set ipVersion 6
                            set ipIf $ipResultIf
                            break
                        }
                    }
                        configIpInterface $ipIf $mode 1
                }
                configAtmIf {
                    set atmIf [::sth::sthCore::invoke stc::get $routerHandle -children-aal5if]
                    configAtmIf $atmIf $mode 1
                }
                configBfdRouter {
                     set bfdRtrCfg [::sth::sthCore::invoke stc::get $routerHandle -children-bfdrouterconfig]
                    configBfdRouter $bfdRtrCfg $mode 1
                }
                configBFDCpiSession {
                    set bfdRtrCfg [::sth::sthCore::invoke stc::get $routerHandle -children-bfdrouterconfig]
                    set bfdChild [::sth::sthCore::invoke stc::get $bfdRtrCfg -children]

                    foreach bfd $bfdChild {
                        if {[string match -nocase "bfdipv4controlplaneindependentsession*" $bfd]} {
                            set bfdCpiSession $bfd
                            break
                        } elseif {[string match -nocase "bfdipv6controlplaneindependentsession*" $bfd]} {
                            set bfdCpiSession $bfd
                            break
                        }
                    }

                    configBFDCpiSession $bfdCpiSession $mode 1
                }
                configIpNetworkBlock
                {
                    set bfdRtrCfg [::sth::sthCore::invoke stc::get $routerHandle -children-bfdrouterconfig]

                    set bfdChild [::sth::sthCore::invoke stc::get $bfdRtrCfg -children]

                    foreach bfd $bfdChild {
                        if {[string match -nocase "bfdipv4controlplaneindependentsession*" $bfd]} {
                            set ipVersion 4
                            set bfdCpiSession $bfd
                            break
                        } elseif {[string match -nocase "bfdipv6controlplaneindependentsession*" $bfd]} {
                            set ipVersion 6
                            set bfdCpiSession $bfd
                            break
                        }
                    }

                    set ipNetworkBlock [lindex [::sth::sthCore::invoke stc::get $bfdCpiSession -children-Ipv$ipVersion\NetworkBlock] 0]

                    configIpNetworkBlock $ipNetworkBlock $mode 1
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "unknown function: $func" {}
                    return -code error $returnKeyedList
                }
            }
        }

        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying BFD configuration: $err"
            return -code error $returnKeyedList
        }

        keylset returnKeyedList handle $userArgsArray(handle)
        keylset returnKeyedList handles $userArgsArray(handle)

    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::bfd::emulation_bfd_config_delete {returnKeyedListVarName {level 1}} {

    variable userArgsArray
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
        return -code error $returnKeyedList
    }

    upvar $level $returnKeyedListVarName returnKeyedList
    set retVal [catch {
        set routerHandle $userArgsArray(handle)

        foreach rtr $userArgsArray(handle) {
            if {![IsBfdRouterHandleValid $rtr]} {
                ::sth::sthCore::processError returnKeyedList "Error: $routerHandle is not a valid BFD router handle" {}
                return -code error $returnKeyedList
            }

            ::sth::sthCore::invoke stc::delete $routerHandle
        }

        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying Bfd configuration: $err"
            return -code error $returnKeyedList
        }
    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::bfd::configBfdRouter {bfdRtrCfgHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configBfdRouter $mode $bfdRtrCfgHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bfdRtrCfgHandle $optionValueList
    }
}

proc ::sth::bfd::configBfdSessionResults  {bfdSsnRstHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configBfdSessionResults $mode $bfdSsnRstHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bfdSsnRstHandle $optionValueList
    }
}

proc ::sth::bfd::configBFDCpiSession {bfdCpiHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configBFDCpiSession $mode $bfdCpiHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bfdCpiHandle $optionValueList
    }
}

proc ::sth::bfd::configEthIIIntf {ethIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configEthIIIntf $mode $ethIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethIfHandle $optionValueList
    }
}

proc ::sth::bfd::configVlanIfInner {vlanIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configVlanIfInner $mode $vlanIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}
proc ::sth::bfd::configVlanIfOuter {vlanIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configVlanIfOuter $mode $vlanIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}

proc ::sth::bfd::configRouter {routerHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configRouter $mode $routerHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $routerHandle $optionValueList
    }
}


proc ::sth::bfd::configIpInterface {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configIpInterface $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::bfd::configLinkLocal {ipIfHandle mode routerIdx} {
    set defaultAddr "fe80::"
    set defaultAddrStep "::1"
    set defaultPrefix "-PrefixLength 128"
    if {[catch {set newipaddr [::sth::sthCore::updateIpAddress 6 $defaultAddr $defaultAddrStep [expr {$routerIdx-1}]]} err]} {
        ::sth::sthCore::processError returnKeyedList "updateIpAddress Failed: $err" {}
        return -code error $returnKeyedList
    }

    set linkLocalsettings "-Address $newipaddr -AddrStep $defaultAddrStep $defaultPrefix"
    ::sth::sthCore::invoke stc::config $ipIfHandle $linkLocalsettings
}

proc ::sth::bfd::configAtmIf {atmHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configAtmIf $mode $atmHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $atmHandle $optionValueList
    }
}

proc ::sth::bfd::configIpNetworkBlock {ipNetBlockHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_config configIpNetworkBlock $mode $ipNetBlockHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipNetBlockHandle $optionValueList
    }
}

proc ::sth::bfd::processEmulation_bfd_configMacAddr {ethIfHandle myswitch value routerIdx} {
    variable userArgsArray

    if {[info exists userArgsArray(local_mac_addr_step)]} {
        set newmacaddr [::sth::sthCore::macStep $userArgsArray(local_mac_addr) \
                        $userArgsArray(local_mac_addr_step) [expr {$routerIdx-1}]]
    } else {
        set newmacaddr $value
    }
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }

    return "-$stcattr $newmacaddr"
}

proc ::sth::bfd::processEmulation_bfd_configVlanId {vlanIfHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }

    if {[string match -nocase $myswitch "vlan_id1"]} {
        if {[info exists userArgsArray(vlan_id_mode1)] && \
            [string match -nocase $userArgsArray(vlan_id_mode1) "increment"]} {
            if {![info exists userArgsArray(vlan_id_step1)]} {
                ::sth::sthCore::processError returnKeyedList "missing \"-vlan_id_step1\" switch" {}
                return -code error $returnKeyedList
            }
            set newvlanId [expr {$value + ($userArgsArray(vlan_id_step1) * [expr {$routerIdx-1}])}]
        } else {
            set newvlanId $value
        }
    } elseif {[string match -nocase $myswitch "vlan_id2"]} {
        if {[info exists userArgsArray(vlan_id_mode2)] && \
            [string match -nocase $userArgsArray(vlan_id_mode2) "increment"]} {
            if {![info exists userArgsArray(vlan_id_step2)]} {
                ::sth::sthCore::processError returnKeyedList "missing \"-vlan_id_step2\" switch" {}
                return -code error $returnKeyedList
            }
            set newvlanId [expr {$value + ($userArgsArray(vlan_id_step2) * [expr {$routerIdx-1}])}]
        } else {
            set newvlanId $value
        }
    }
    return "-$stcattr $newvlanId"
}


proc ::sth::bfd::processEmulation_bfd_configvlanType { vlanIfHandle myswitch value routerIdx} {

    variable userArgsArray

    set vlantype ""
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }

    if {[string match -nocase $myswitch "vlan_ether_type1"]} {
        if {![info exists userArgsArray(vlan_id1)]} {
            ::sth::sthCore::processError returnKeyedList "switch -vlan_id1 is required when \"-vlan_ether_type1\" is used" {}
            return -code error $returnKeyedList
        }
        if {[string match -nocase $value "vlan_tag_0x8100"]} {
            set vlantype "0x8100"
        } elseif {[string match -nocase $value "vlan_tag_0x88a8"]} {
            set vlantype "0x88a8"
        } elseif {[string match -nocase $value "vlan_tag_0x9100"]} {
            set vlantype "0x9100"
        }
        #convert HEX to decimal
        set decVlantype [format "%i" $vlantype]
    } elseif {[string match -nocase $myswitch "vlan_ether_type2"]} {
        if {![info exists userArgsArray(vlan_id2)]} {
            ::sth::sthCore::processError returnKeyedList "switch -vlan_id2 is required when \"-vlan_ether_type2\" is used" {}
            return -code error $returnKeyedList
        }
        if {[string match -nocase $value "vlan_tag_0x8100"]} {
            set vlantype "0x8100"
        } elseif {[string match -nocase $value "vlan_tag_0x88a8"]} {
            set vlantype "0x88a8"
        } elseif {[string match -nocase $value "vlan_tag_0x9100"]} {
            set vlantype "0x9100"
        }
        #convert HEX to decimal
        set decVlantype [format "%i" $vlantype]
    }
    return "-$stcattr $decVlantype"
}


proc ::sth::bfd::processEmulation_bfd_configIp {ipIfHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1

    if {[string match -nocase "ipv4if*" $ipIfHandle]} {
        set ipVersion 4
        if {[info exist userArgsArray(intf_ip_addr_step)]} {
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $value $userArgsArray(intf_ip_addr_step) [expr {$routerIdx-1}]]
        } else {
            set newipaddr $value
        }
    } elseif {[string match -nocase "ipv6if*" $ipIfHandle]} {
        set ipVersion 6
        if {[info exist userArgsArray(intf_ipv6_addr_step)]} {
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $value $userArgsArray(intf_ipv6_addr_step) [expr {$routerIdx-1}]]
        } else {
            set newipaddr $value
        }
    }

    set rtrHandle [::sth::sthCore::invoke stc::get $ipIfHandle -parent]
    ##validate BFD having different ipaddr on different interfaces
    #if {![::sth::sthCore::IsBfdIpAddrValid $rtrHandle $newipaddr]} {
    #    ::sth::sthCore::processError returnKeyedList "unable to enable BFD under different interfaces with the same IP address" {}
    #    return -code error $returnKeyedList
    #}

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }

    return "-$stcattr $newipaddr"
}


proc ::sth::bfd::processEmulation_bfd_configGateWay {ipIfHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1

    if {[string match -nocase "ipv4if*" $ipIfHandle]} {
        set ipVersion 4
        if {[info exist userArgsArray(gateway_ip_addr_step)]} {
            set newgateway [::sth::sthCore::updateIpAddress $ipVersion $value $userArgsArray(gateway_ip_addr_step) [expr {$routerIdx-1}]]
        } else {
            set newgateway $value
        }
    } elseif {[string match -nocase "ipv6if*" $ipIfHandle]} {
        set ipVersion 6
        if {[info exist userArgsArray(gateway_ipv6_addr_step)]} {
            set newgateway [::sth::sthCore::updateIpAddress $ipVersion $value $userArgsArray(gateway_ipv6_addr_step) [expr {$routerIdx-1}]]
        } else {
            set newgateway $value
        }
    }

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }

    return "-$stcattr $newgateway"
}

proc ::sth::bfd::processEmulation_bfd_configVci {atmHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1


        if {[info exist userArgsArray(vci_step)]} {
            set vci [expr {$value + ($userArgsArray(vci_step) * [expr {$routerIdx-1}])}]
        } else {
            set vci $value
        }

        if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
            return -code error $returnKeyedList
        }

    return "-$stcattr $vci"
}

proc ::sth::bfd::processEmulation_bfd_configVpi {atmHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1


        if {[info exist userArgsArray(vpi_step)]} {
            set vpi [expr {$value + ($userArgsArray(vpi_step) * [expr {$routerIdx-1}])}]
        } else {
            set vpi $value
        }

        if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
            return -code error $returnKeyedList
        }

    return "-$stcattr $vpi"
}

proc ::sth::bfd::processEmulation_bfd_configSessionDiscriminator {bfdCpiHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1

        #set "Enable My Discriminator" to be TRUE when configuring "session_discriminator"
        set enableMydis "-EnableMyDiscriminator TRUE"

        if {[info exist userArgsArray(session_discriminator_step)]} {
            set discriminator [expr {$value + ($userArgsArray(session_discriminator_step) * [expr {$routerIdx-1}])}]
        } else {
            set discriminator $value
        }

        if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
            return -code error $returnKeyedList
        }

    return "$enableMydis -$stcattr $discriminator"
}

proc ::sth::bfd::processEmulation_bfd_configIpVersion {bfdRtrHandle myswitch value routerIdx} {

    set rtrHandle [::sth::sthCore::invoke stc::get $bfdRtrHandle -parent]
    set newIpVersion $value
    set oldIpVersion [getIpVersionFromStack $rtrHandle]
    if {![string equal -nocase $oldIpVersion $newIpVersion]} {
       #remove old IF stack
        set hasVlan 0
        if {[catch {
            set vlanResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-VlanIf]
        } err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList
        } else {
            if {[llength $vlanResultIf]} {
                set hasVlan 1
            }
            if {!$hasVlan} {
                # There is no vlan configuration
                switch -- $newIpVersion {
                "IPv4" {
                    set IfStack "Ipv4If EthIIIf"
                }
                "IPv6" {
                    set IfStack "Ipv6If EthIIIf"
                }
            }
            set IfCount "1 1"
            } else {
                # There is vlan configuration
                switch -- $newIpVersion {
                    "IPv4" {
                        set IfStack "Ipv4If VlanIf EthIIIf"
                    }
                    "IPv6" {
                        set IfStack "Ipv6If VlanIf EthIIIf"
                    }
                }
                set IfCount "1 1 1"
            }
        }

        switch -- $oldIpVersion {
            "IPv4" {
                set ipv4ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv4If]
                if {[llength $ipv4ResultIf]} {
                    set performStatus [::sth::sthCore::invoke stc::perform IfStackRemove -DeviceList $rtrHandle -TopIf $ipv4ResultIf]
                }
            }
            "IPv6" {
                set ipv6ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv6If]
                foreach ipv6If $ipv6ResultIf {
                    set performStatus [::sth::sthCore::invoke stc::perform IfStackRemove -DeviceList $rtrHandle -TopIf $ipv6If]
                }
            }
        }

        #add new IF stack
        switch -- $newIpVersion {
            "IPv4" {
                set performStatus [::sth::sthCore::invoke stc::perform IfStackAdd -DeviceList $rtrHandle -IfStack $IfStack -IfCount $IfCount]
            }
            "IPv6" {
                set performStatus [::sth::sthCore::invoke stc::perform IfStackAdd -DeviceList $rtrHandle -IfStack $IfStack -IfCount $IfCount]
                if {[catch {set vlanResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                    return -code error $returnKeyedList
                } else {
                    if {!$hasVlan} {
                        set ethiiResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
                        set AttachToIf $ethiiResultIf
                    } else {
                        set AttachToIf $vlanResultIf
                    }
                }
                set performStatus [::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $rtrHandle -IfStack "Ipv6If" -IfCount "1" -AttachToIf $AttachToIf]
                set ipv6ResultIfList [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv6if]
                set ipv6ifLocal [lindex $ipv6ResultIfList 1]
    #           set link64BitAddr [::sth::sthCore::getNext64BitNumber]
    #           set linkLocalIp "FE80:0:0:0"
    #           foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
    #               append linkLocalIp ":$num1$num2$num3$num4"
    #           }
                set configStatus [::sth::sthCore::invoke stc::config $ipv6ifLocal -Address fe80::2]
                ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true

            }
        }
    } elseif {[string equal -nocase $newIpVersion "IPv6"] &&[string equal -nocase $oldIpVersion $newIpVersion]} {
        set ipv6ResultIfList [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv6if]
        foreach ipv6address $ipv6ResultIfList {
            set address [::sth::sthCore::invoke stc::get $ipv6address -Address]
            if {[regexp -nocase "fe80::" $address]} {
                ::sth::sthCore::invoke stc::config $ipv6address -Address fe80::2
                ::sth::sthCore::invoke stc::config $ipv6address -AllocateEui64LinkLocalAddress true

                break
            }
        }

    }
}


proc ::sth::bfd::processEmulation_bfd_configRemoteAddr {ipNetBlockHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1

    if {[string match -nocase "ipv4networkblock*" $ipNetBlockHandle]} {
        set ipVersion 4
        if {[info exist userArgsArray(remote_ip_addr_step)]} {
            set remoteipaddr [::sth::sthCore::updateIpAddress $ipVersion $value $userArgsArray(remote_ip_addr_step) [expr {$routerIdx-1}]]
        } else {
            set remoteipaddr $value
        }
    } elseif {[string match -nocase "ipv6networkblock*" $ipNetBlockHandle]} {
        set ipVersion 6
        if {[info exist userArgsArray(remote_ipv6_addr_step)]} {
            set remoteipaddr [::sth::sthCore::updateIpAddress $ipVersion $value $userArgsArray(remote_ipv6_addr_step) [expr {$routerIdx-1}]]
        } else {
            set remoteipaddr $value
        }
    }

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }

    return "-$stcattr $remoteipaddr"
}

proc ::sth::bfd::processEmulation_bfd_configRemoteAddrStep {ipNetBlockHandle myswitch value routerIdx} {
    variable userArgsArray
    # check for any dependencies
    checkDependency "emulation_bfd_config" $myswitch 1

    if {[string match -nocase "ipv4networkblock*" $ipNetBlockHandle]} {
        #convert the step ip address to decimal
        set stepValue $value
        set octets [split $stepValue .]
        if {[llength $octets] != 4} {
            set octets [lrange [concat 0 0 0 $octets] 0 3]
        }
        set binStepIpAddress ""
        foreach oct $octets {
            binary scan [binary format c $oct] B* bin
            set binStepIpAddress "$binStepIpAddress$bin"
        }
        binary scan [binary format B32 [format %032s $binStepIpAddress]] I stepIpAddress
        set prefixLength ""
    } elseif {[string match -nocase "ipv6networkblock*" $ipNetBlockHandle]} {
        set stepValue $value
        set myStepValue $stepValue
        if {[string first "::" $stepValue] <0} {
            if {[string length $stepValue] > 4} {
                set stepValue [string range $stepValue 0 3]
            }
            set stepValue "0::$stepValue"
        }

        set count 0
        for {set i 0} {$i<[string length $myStepValue]} {incr i} {
            if {[string equal : [string range $myStepValue $i $i]]} {
                incr count
            }
        }
        if {[string equal 7 $count]} {
            set starIndex [expr [string last ":" $myStepValue] + 1]
            set endIndex [expr [string length $myStepValue] - 1]
            set stepValue [string range $myStepValue $starIndex $endIndex]
            set stepValue "0::$stepValue"
        }

        set normalizedStepValue [::sth::sthCore::normalizeIPv6Addr $stepValue];
        if {$normalizedStepValue == 0} {
            return 0;
        } else {
            set stepValue $normalizedStepValue
        }

        #converting the step to binary
        set octets [split $stepValue :]
        set binStepIpAddress ""
        foreach oct $octets {
            binary scan [binary format H4 $oct] B* bin
            set binStepIpAddress "$binStepIpAddress$bin"
        }

        set firstLength [string first "1" $binStepIpAddress]
        set lastLength [string last "1" $binStepIpAddress]
        if {($firstLength > 0) && ($lastLength > 0)} {
            if {$firstLength <= $lastLength} {
                if {[expr $lastLength-$firstLength] <= 32} {
                    set ipaddrBin [string range $binStepIpAddress $firstLength $lastLength]
                    binary scan [binary format B32 [format %032s $ipaddrBin]] I stepIpAddress
                } else {
                    set val [catch {
                        set num 0
                        set len [expr $lastLength-$firstLength]
                        set ipaddrBin [string range $binStepIpAddress $firstLength $lastLength]
                        for {set x [expr $len-15]; set y $len} {$y >= 0} {} {
                            set oct [string range $ipaddrBin $x $y]
                            binary scan [binary format B32 [format %032s $oct]] I* val
                            if {$val != 0} {
                                set num [expr $num+double([expr $val*int(pow(2,[expr $len-$y]))])]
                            }

                            set x [expr {$x-16}]
                            set y [expr {$y-16}]
                            if {$x < 0 && $y > 0} {
                                set x 0
                                set y 0
                            }
                            set num [expr int($num)]
                        }
                    set stepIpAddress $num
                    } err]
                    if {$val} {
                       ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
                       return -code error $returnKeyedList
                    }

                }
            }
        }
        set lastLength [expr $lastLength+1]
        set prefixLength "-PrefixLength $lastLength"
    }

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList
    }
    return "$prefixLength -$stcattr $stepIpAddress"
}

#to check if the handle is valid BFD router Handle or not
proc ::sth::bfd::IsBfdRouterHandleValid { handle } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set cmdStatus 0

    if {[catch {set routerHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]} err]} {        ::sth::sthCore::processError returnKeyedList "No router exists under Project Handle:$::sth::GBLHNDMAP(project)"        return $FAILURE    } else {
        foreach routerHandle $routerHandleList {
            if {[string equal $routerHandle $handle]} {
                set cmdStatus 1
                break
            }
        }
        if {[catch {set bfdRouterConfigHandle [::sth::sthCore::invoke stc::get $routerHandle -children-bfdrouterconfig]} err]} {            set cmdStatus 0
        }

        if {$cmdStatus == 1} {
            return $SUCCESS
        } else {
            set errorMsg "Value ($handle) is not a valid Bfd router handle"
            return $FAILURE
        }
    }
}

proc ::sth::bfd::emulation_bfd_flap {returnKeyedListVarName rtrList {level 1}} {
    variable userArgsArray
    upvar $level $returnKeyedListVarName returnKeyedList

    set bfdRtrConfigHandle [::sth::sthCore::invoke stc::get $rtrList -children-bfdrouterconfig]

    set retVal [catch {
        if {![info exists userArgsArray(flap_count)]} {
            ::sth::sthCore::processError returnKeyedList "missing \"-flap_count\" switch" {}
            return -code error $returnKeyedList
        }
        if {![info exists userArgsArray(flap_interval)]} {
            ::sth::sthCore::processError returnKeyedList "missing \"-flap_interval\" switch" {}
            return -code error $returnKeyedList
        }
        for {set i 1} {$i <= $userArgsArray(flap_count)} {incr i} {
            ::sth::sthCore::invoke stc::perform BfdStopPdus -ObjectList  $bfdRtrConfigHandle
            after [expr 1000 * {$userArgsArray(flap_interval)}]
            ::sth::sthCore::invoke stc::perform BfdResumePdus -ObjectList $bfdRtrConfigHandle
        }
    } returnedString]
    return -code $retVal $returnedString
}

proc ::sth::bfd::emulation_bfd_common_control {returnKeyedListVarName rtrList {level 1}} {
    variable userArgsArray
    set mode $userArgsArray(mode)
    array set cmdNameArr {stop_pdus BfdStopPdus resume_pdus BfdResumePdus admin_up BfdAdminUpCommand admin_down BfdAdminDownCommand enable_demand BfdEnableDemandModeCommand disable_demand BfdDisableDemandModeCommand initiate_poll BfdInitiatePollCommand}
    set cmdName $cmdNameArr($mode)
    set bfdRtrConfigHandleList ""
    set retVal [catch {
        foreach rtr $rtrList {
            lappend bfdRtrConfigHandleList [::sth::sthCore::invoke stc::get $rtr -children-bfdrouterconfig]
        }
        ::sth::sthCore::invoke stc::perform $cmdName -ObjectList $bfdRtrConfigHandleList
    } returnedString]
    return -code $retVal $returnedString
}

proc ::sth::bfd::checkDependency {cmdType myswitch dependentValue} {
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::bfd:: $cmdType $myswitch dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists ::sth::bfd::userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the existence of \"-$dependency\"."
        } elseif {![string match -nocase $dependentValue $::sth::bfd::userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}


proc ::sth::bfd::getIpVersionFromStack {deviceHandle} {
    set ipv4IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv4if]
    set ipv6IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv6if]
    if {[llength $ipv4IfHandle] > 0 && [llength $ipv6IfHandle] == 0} {
        return "IPv4"
    } elseif {[llength $ipv6IfHandle] > 0 && [llength $ipv4IfHandle] == 0} {
        return "IPv6"
    } else {
        return "IPV4andIPv6"
    }
}

proc ::sth::bfd::getAssociatedItem {ipVersion attribute} {
    #return value assocated to the atrribute based on desired sesssion (version) type.
    foreach {key keyVal} $attribute {
        if {$key == $ipVersion} {
            return $keyVal
        }
    }
    return $attribute
}

proc ::sth::bfd::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in bfdTable.tcl
    foreach item $::sth::bfd::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::bfd:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::bfd:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::bfd:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::bfd:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::bfd:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::bfd:: $cmdType $opt $::sth::bfd::userArgsArray($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::bfd::userArgsArray($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::bfd::userArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}


proc ::sth::bfd::emulation_bfd_session_config_create {returnKeyedListVarName {level 1}} {

    variable userArgsArray
    set mode create

    if {![info exists userArgsArray(bfd_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -bfd_handle." {}
        return -code error $returnKeyedList
    } else {
        set bfdRouter $userArgsArray(bfd_handle)
        set bfdHandle [::sth::sthCore::invoke stc::get $bfdRouter -children-BfdRouterConfig]
    }
    set ipVersion "IPv4"
    upvar $level $returnKeyedListVarName returnKeyedList
    if {[info exists userArgsArray(ip_version)]} {
        set ipVersion $userArgsArray(ip_version)
    }
    if {[string match -nocase $ipVersion IPv46]} {
        set bfdIpv4CpiSession [::sth::sthCore::invoke stc::create "BfdIpv4ControlPlaneIndependentSession" -under $bfdHandle]
        configBfdsession $bfdIpv4CpiSession $mode 0
        set bfdIpv4NB [::sth::sthCore::invoke stc::get $bfdIpv4CpiSession -children-Ipv4NetworkBlock]
        configIpNetworkBlock4 $bfdIpv4NB $mode 0
        set bfdIpv6CpiSession [::sth::sthCore::invoke stc::create "BfdIpv6ControlPlaneIndependentSession" -under $bfdHandle]
        configBfdsession6 $bfdIpv6CpiSession $mode 0
        set bfdIpv6NB [::sth::sthCore::invoke stc::get $bfdIpv6CpiSession -children-Ipv6NetworkBlock]
        configIpNetworkBlock6 $bfdIpv6NB $mode 0
        keylset returnKeyedList ipv4_session_handle $bfdIpv4CpiSession
        keylset returnKeyedList ipv6_session_handle $bfdIpv6CpiSession
    } elseif {[string match -nocase $ipVersion IPv6]} {
        set bfdIpv6CpiSession [::sth::sthCore::invoke stc::create "BfdIpv6ControlPlaneIndependentSession" -under $bfdHandle]
        configBfdsession6 $bfdIpv6CpiSession $mode 0
        set bfdIpv6NB [::sth::sthCore::invoke stc::get $bfdIpv6CpiSession -children-Ipv6NetworkBlock]
        configIpNetworkBlock6 $bfdIpv6NB $mode 0
        keylset returnKeyedList ipv6_session_handle $bfdIpv6CpiSession
    } else {
        set bfdIpv4CpiSession [::sth::sthCore::invoke stc::create "BfdIpv4ControlPlaneIndependentSession" -under $bfdHandle]
        configBfdsession $bfdIpv4CpiSession $mode 0
        set bfdIpv4NB [::sth::sthCore::invoke stc::get $bfdIpv4CpiSession -children-Ipv4NetworkBlock]
        configIpNetworkBlock4 $bfdIpv4NB $mode 0
        keylset returnKeyedList ipv4_session_handle $bfdIpv4CpiSession
    }

    #apply all configurations
    if {[catch {::sth::sthCore::doStcApply} err]} {
        ::sth::sthCore::processError returnKeyedList "Error applying Bfd configuration: $err"
        return -code error $returnKeyedList
    }
}

proc ::sth::bfd::emulation_bfd_session_config_modify {returnKeyedListVarName {level 1}} {

    variable userArgsArray
    variable sortedSwitchPriorityList
    set mode modify

    if {![info exists userArgsArray(ipv4_handle)] && ![info exists userArgsArray(ipv6_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -ipv4_handle or -ipv6_handle." {}
        return -code error $returnKeyedList
    }
    if {[info exists userArgsArray(ipv4_handle)] && [info exists userArgsArray(ipv6_handle)]} {
        set bfdIpv6CpiSession $userArgsArray(ipv6_handle)
        configBfdsession6 $bfdIpv6CpiSession $mode 0
        set bfdIpv6NB [::sth::sthCore::invoke stc::get $bfdIpv6CpiSession -children-Ipv6NetworkBlock]
        configIpNetworkBlock6 $bfdIpv6NB $mode 0
        set bfdIpv4CpiSession $userArgsArray(ipv4_handle)
        configBfdsession $bfdIpv4CpiSession $mode 0
        set bfdIpv4NB [::sth::sthCore::invoke stc::get $bfdIpv4CpiSession -children-Ipv4NetworkBlock]
        configIpNetworkBlock4 $bfdIpv4NB $mode 0
    } elseif {[info exists userArgsArray(ipv6_handle)]} {
        set bfdIpv6CpiSession $userArgsArray(ipv6_handle)
        configBfdsession6 $bfdIpv6CpiSession $mode 0
        set bfdIpv6NB [::sth::sthCore::invoke stc::get $bfdIpv6CpiSession -children-Ipv6NetworkBlock]
        configIpNetworkBlock6 $bfdIpv6NB $mode 0
    } elseif {[info exists userArgsArray(ipv4_handle)]} {
        set bfdIpv4CpiSession $userArgsArray(ipv4_handle)
        configBfdsession $bfdIpv4CpiSession $mode 0
        set bfdIpv4NB [::sth::sthCore::invoke stc::get $bfdIpv4CpiSession -children-Ipv4NetworkBlock]
        configIpNetworkBlock4 $bfdIpv4NB $mode 0
    }

    #apply all configurations
    if {[catch {::sth::sthCore::doStcApply} err]} {
        ::sth::sthCore::processError returnKeyedList "Error applying BFD configuration: $err"
        return -code error $returnKeyedList
    }
}

proc ::sth::bfd::emulation_bfd_session_config_delete {returnKeyedListVarName {level 1}} {

    variable userArgsArray
    if {![info exists userArgsArray(ipv4_handle)] && ![info exists userArgsArray(ipv6_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -ipv4_handle -ipv6_handle."
        return -code error $returnKeyedList
    }

    upvar $level $returnKeyedListVarName returnKeyedList
    set retVal [catch {
        if {[info exists userArgsArray(ipv4_handle)]} {
            ::sth::sthCore::invoke stc::delete $userArgsArray(ipv4_handle)
        }
        if {[info exists userArgsArray(ipv6_handle)]} {
            ::sth::sthCore::invoke stc::delete $userArgsArray(ipv6_handle)
        }

        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying Bfd configuration: $err"
            return -code error $returnKeyedList
        }
    } returnedString]

    return  $returnedString
}

proc ::sth::bfd::configBfdsession {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_session_config configBfdsession $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::bfd::configIpNetworkBlock4 {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_session_config configIpNetworkBlock4 $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::bfd::configBfdsession6 {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_session_config configBfdsession6 $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::bfd::configIpNetworkBlock6 {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bfd_session_config configIpNetworkBlock6 $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}
