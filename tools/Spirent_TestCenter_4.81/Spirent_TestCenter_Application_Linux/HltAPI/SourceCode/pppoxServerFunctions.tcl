# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/pppoxServerFunctions.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#
namespace eval ::sth::PppoxServer {
    #
    # PPPOXSERVEROBJTYPE is used to distinguish different stc pppox server objects: "pppoe" or "pppoa"
    # config obj:     PppoeServerBlockConfig   PppoaServerBlockConfig
    # result obj:     PppoeServerBlockResults  PppoaServerBlockResults
    # pool addr obj:  PppoeServerIpv4PeerPool  PppoxServerIpv4PeerPool (note, prefix is pppox)
    array set PPPOXSERVEROBJTYPE {}
}


proc ::sth::PppoxServer::pppox_server_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "pppox_server_config_create"

    variable ::sth::PppoxServer::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {  
        # port_handle is mandatory for the -mode create
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
                ::sth::sthCore::processError returnKeyedList "Error: Invalid value of \"-port_handle\" $portHandle"
                return $returnKeyedList
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -port_handle is required when \"-mode create\" is used."
            return $returnKeyedList
        }
        
        if {[regexp -nocase "v4" $userArgsArray(ip_cp)]} {
            set ipVersion "ipv4"
            set topif "Ipv4If"
            set IfCount "1"
        } else {
            set ipVersion "ipv6"
            set topif "Ipv6If"
            set IfCount "1"
        }
        
        # create encapsulation stack by -protocol and -encap
           # For pppoeoa, we can use the combination of "ethernet_ii|ethernet_ii_vlan|ethernet_ii_qinq" and "vc_mux|llcsnap" for -encap
        set encap $userArgsArray(encap)
        set protocol $userArgsArray(protocol)
        switch -exact -- $protocol {
            "pppoe" {
                if {[regexp "ethernet_ii_vlan" $encap]} {
                    set IfStack "$topif PppIf PppoeIf VlanIf EthIIIf"
                    set IfCount "$IfCount 1 1 1 1"
                } elseif {[regexp "ethernet_ii_qinq" $encap]} {
                    set IfStack "$topif PppIf PppoeIf VlanIf VlanIf EthIIIf"
                    set IfCount "$IfCount 1 1 1 1 1"
                } elseif {[regexp "ethernet_ii" $encap]} {
                    # ethernet_ii
                    set IfStack "$topif PppIf PppoeIf EthIIIf"
                    set IfCount "$IfCount 1 1 1"
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid -encap $encap for -protocol $protocol" {}
                    return -code error $returnKeyedList  
                }
                set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($portHandle) "pppoe"
            }
            "pppoa" {
                if {[regexp "vc_mux" $encap] || [regexp "llcsnap" $encap]} {
                    set IfStack "$topif PppIf Aal5If"
                    set IfCount "$IfCount 1 1"
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid -encap $encap for -protocol $protocol" {}
                    return -code error $returnKeyedList  
                }
                set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($portHandle) "pppoa"
            }
            "pppoeoa" {
                if {[regexp "ethernet_ii_vlan" $encap] } {
                    set IfStack "$topif PppIf PppoeIf VlanIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1 1"
                } elseif {[regexp "ethernet_ii_qinq" $encap] } {
                    set IfStack "$topif PppIf PppoeIf VlanIf VlanIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1 1 1"
                } elseif {[regexp "ethernet_ii" $encap]} {
                    set IfStack "$topif PppIf PppoeIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1"
                } else {
                    set IfStack "$topif PppIf PppoeIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1"
                }
                set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($portHandle) "pppoe"
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error: Unknown value $protocol for argument -protocol" {}
                return -code error $returnKeyedList  
            }
        }
    
        # create pppox server host block
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
        set createdHost $DeviceCreateOutput(-ReturnList)
        
        if {[info exists userArgsArray(num_sessions)]} {
            if {[catch {::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $userArgsArray(num_sessions)"} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                return -code error $returnKeyedList 
            }
        }
        
        # adjust link local interface for ipv6
        if {$ipVersion == "ipv6"} {
            if {[catch {set linkLocalIf [::sth::sthCore::invoke stc::get $createdHost -children-ipv6if]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            }
            
            if {[catch {
                ::sth::sthCore::invoke stc::config $linkLocalIf "-Address fe80::1 -AddrStep ::1 -PrefixLength 64"
                ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
            } err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                return -code error $returnKeyedList 
            }
            
            # create new ipv6if
            if {[catch {set ipv6If [::sth::sthCore::invoke stc::create ipv6if -under $createdHost "-primaryif-sources $createdHost"]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                return -code error $returnKeyedList 
            }
            
            if {[catch {::sth::sthCore::invoke stc::config $createdHost "-TopLevelIf-targets {$linkLocalIf $ipv6If}"} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            } 
            
            if {$protocol == "pppoeoa" || $protocol == "pppoe"} {
                if {[catch {set lowIf [::sth::sthCore::invoke stc::get $createdHost -children-PppoeIf]} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                    return -code error $returnKeyedList 
                }
            } elseif {$protocol == "pppoa"} {
                if {[catch {set lowIf [::sth::sthCore::invoke stc::get $createdHost -children-Aal5If]} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                    return -code error $returnKeyedList 
                }
            }
            #### ipv6 encap stack map ####
            #
            #               'PrimaryIf toplevelIf'      UsesIf
            #         emulateddevice ----->  ipv6if2  <------- PppoeServerBlockConfig
            #              |                    |
            # 'toplevelIf' |                  pppif2
            #              |                    |
            #   ipv6if1(linklocal)-->pppIf1--->pppoeIf--->vlanIf--->ethIIIf
            #
            #
            ####
            #
            # ipv6if-->PppIf-->PppoeIf   pppoe or pppoeoa
            # ipv6if-->PppIf-->Aal5If    pppoa
            #
            # create new pppif stack between the new ipv6if and pppoeif 
            if {[catch {::sth::sthCore::invoke stc::create PppIf -under $createdHost "-StackedOnEndpoint-sources $ipv6If -StackedOnEndpoint-targets $lowIf"} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                return -code error $returnKeyedList 
            }
        }
        
        # config atm encapsulation type
        if {$protocol == "pppoa" || $protocol == "pppoeoa"} {
            if {[catch {set atmHandle [::sth::sthCore::invoke stc::get $createdHost -children-Aal5If]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            }
            if {[regexp "vc_mux" $encap]} {
                if {[catch {::sth::sthCore::invoke stc::config $atmHandle "-VcEncapsulation VC_MULTIPLEXED"} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                    return -code error $returnKeyedList 
                } 
            } elseif {[regexp "llcsnap" $encap]} {
                if {[catch {::sth::sthCore::invoke stc::config $atmHandle "-VcEncapsulation LLC_ENCAPSULATED"} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                    return -code error $returnKeyedList 
                } 
            }
        }
        
        if {[catch {set ipStack [::sth::sthCore::invoke stc::get $createdHost -children-$topif]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
            return -code error $returnKeyedList 
        }
        
        # Create the pppox server session block
        set pppoxServerBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($portHandle)]ServerBlockConfig
        set ipStack [lindex $ipStack 0]
        if {[catch {set pppoxBlockSession [::sth::sthCore::invoke stc::create $pppoxServerBlock -under $createdHost "-IpcpEncap $ipVersion -UsesIf-targets $ipStack"]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::create Failed $err" {}
            return -code error $returnKeyedList 
        }
        
        ### Config input switches
        ::sth::PppoxServer::processConfigSwitches $createdHost create $ipVersion returnKeyedList
        
        if {[catch {set pppoxPort [::sth::sthCore::invoke stc::get $portHandle -children-PppoxPortConfig]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
            return -code error $returnKeyedList 
        }
        # set pppox emulation Type - server
        if {[catch {::sth::sthCore::invoke stc::config $pppoxPort "-EmulationType SERVER"} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
            return -code error $returnKeyedList 
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any host created if error occurs
        if {[info exists createdHost]} {
            if {[catch {::sth::sthCore::invoke stc::delete $createdHost} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::delete Failed $err" {}
                return -code error $returnKeyedList   
            }
        }
    } else {
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList pppox_port $pppoxPort
        keylset returnKeyedList handle $createdHost   
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}

proc ::sth::PppoxServer::pppox_server_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "pppox_server_config_modify"

    variable ::sth::PppoxServer::userArgsArray
    variable ::sth::PppoxServer::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set hostHandleList $userArgsArray(handle)
            if {![IsPppoxServerHandleValid $hostHandleList]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandleList is not valid Pppox Server handle" {}
                return -code error $returnKeyedList 
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        
        # checking unsupported switches under "modify" mode
        set unsupportedModifyOptions {port_handle ip_cp encap protocol}
        
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                    ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        # modify input arguments
        foreach hostHandle $hostHandleList {
            if {[catch {set port [::sth::sthCore::invoke stc::get $hostHandle "-AffiliationPort-targets"]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            }
            set pppoxServerBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)]ServerBlockConfig
            if {[catch {set pppoxBlock [::sth::sthCore::invoke stc::get $hostHandle -children-$pppoxServerBlock]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            }
            if {[catch {set ipVersion [::sth::sthCore::invoke stc::get $pppoxBlock -IpcpEncap]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            }
            
            if {[info exists userArgsArray(num_sessions)]} {
                if {[catch {::sth::sthCore::invoke stc::config $hostHandle "-DeviceCount $userArgsArray(num_sessions)"} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                    return -code error $returnKeyedList 
                }
            }
            
            ::sth::PppoxServer::processConfigSwitches $hostHandle modify $ipVersion returnKeyedList  
        }
        
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList handle $hostHandleList   
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}

proc ::sth::PppoxServer::pppox_server_config_reset { returnKeyedListVarName } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }
        
        set hostHandleList $userArgsArray(handle)
        
        foreach hostHandle $hostHandleList {
            if {![IsPppoxServerHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandleList is not valid Pppox Server handle" {}
                return -code error $returnKeyedList 
            }
            
            if {[catch {::sth::sthCore::invoke stc::delete $hostHandle} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
                return -code error $returnKeyedList 
            }  
        }
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}

proc ::sth::PppoxServer::processConfigSwitches {handleList mode ipVersion returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::PppoxServer::sortedSwitchPriorityList
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::PppoxServer:: pppox_server_config $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::PppoxServer:: pppox_server_config $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::PppoxServer:: pppox_server_config $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    foreach hostHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    if {[catch {set ethiiIf [::sth::sthCore::invoke stc::get $hostHandle -children-EthIIIf]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[string length $ethiiIf] != 0} {
                        configEthIIIntf $ethiiIf $mode
                    }
                }
                configVlanIfInner {
                    if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $hostHandle -children-VlanIf]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 0]
                        }
                        configVlanIfInner $vlanIf $mode
                    }
                }
                configVlanIfOuter {
                    if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $hostHandle -children-VlanIf]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] < 2} {continue}            
                        set vlanIf [lindex $vlanIf 1]
                        configVlanIfOuter $vlanIf $mode
                    }

                }
                configIpIntf {
                    if {[catch {set ipIf [::sth::sthCore::invoke stc::get $hostHandle -children-${ipVersion}if]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[llength $ipIf] != 0} {
                        if {[llength $ipIf] > 1} {
                            set ipIf [lindex $ipIf 1] 
                        }
                        configIpIntf $ipIf $mode
                    }
                }
                configAtmIntf {
                    if {[catch {set atmIf [::sth::sthCore::invoke stc::get $hostHandle -children-Aal5If]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[string length $atmIf] != 0} {
                        configAtmIntf $atmIf $mode
                    }
                }
                configPortConfig {
                    if {[catch {set port [::sth::sthCore::invoke stc::get $hostHandle -AffiliationPort-targets]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[catch {set portConfig [::sth::sthCore::invoke stc::get $port -children-PppoxPortConfig]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    configPortConfig $portConfig $mode
                }
                configSessionBlock {
                    if {[catch {set port [::sth::sthCore::invoke stc::get $hostHandle -AffiliationPort-targets]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    set pppoxServerBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)]ServerBlockConfig
                    if {[catch {set pppoxBlockSession [::sth::sthCore::invoke stc::get $hostHandle -children-$pppoxServerBlock]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    configSessionBlock $pppoxBlockSession $mode
                }
                configIpAddressPool {
                    if {[catch {set port [::sth::sthCore::invoke stc::get $hostHandle -AffiliationPort-targets]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    set pppoxServerBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)]ServerBlockConfig
                    if {[catch {set pppoxBlockSession [::sth::sthCore::invoke stc::get $hostHandle -children-$pppoxServerBlock]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    # For Pppoa, address pool obj is "PppoxServerIpv4PeerPool"; for Pppoe, it is "PppoeServerIpv4PeerPool"
                    # For ipv6, address pool obj is "pppoxserveripv6peerpool", both for over Ethernet and over ATM
                    if {[string match -nocase "ipv4" $ipVersion]} {
                        if {[regexp -nocase "pppoa" $pppoxBlockSession]} {
                            set pppoxPool PppoxServer${ipVersion}PeerPool
                        } elseif {[regexp -nocase "pppoe" $pppoxBlockSession]} {
                            set pppoxPool PppoeServer${ipVersion}PeerPool
                        }
                    } elseif {[string match -nocase "ipv6" $ipVersion]} {
                        set pppoxPool "pppoxserveripv6peerpool"
                    }
                    
                    if {[catch {set pppoxIpPool [::sth::sthCore::invoke stc::get $pppoxBlockSession "-children-$pppoxPool"]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    
                    if {[llength $pppoxIpPool] == 0} {
                        # Note: in the case of IPv6 over ATM, stc 3.50 bll can not create ipv6 pool address obj (pppoxserveripv6peerpool)
                        # automatically from PppoaServerBlockConfig, we need to create the obj here
                        if {[catch {set pppoxIpPool [::sth::sthCore::invoke stc::create $pppoxPool -under $pppoxBlockSession]} err]} {
                            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                            return -code error $returnKeyedList 
                        }
                    }
                    
                    configIpAddressPool $pppoxIpPool $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
}


# Configure PPPox server port level configuration
proc ::sth::PppoxServer::configPortConfig { portConfigHdl mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $portConfigHdl] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    
    set optionValueList [getStcOptionValueList pppox_server_config configPortConfig $mode $portConfigHdl]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $portConfigHdl $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configSessionBlock { blockSessionHdl mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $blockSessionHdl] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    
    set optionValueList [getStcOptionValueList pppox_server_config configSessionBlock $mode $blockSessionHdl]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $blockSessionHdl $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configIpAddressPool { ipPoolHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $ipPoolHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList pppox_server_config configIpAddressPool $mode $ipPoolHandle]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ipPoolHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configEthIIIntf { ethHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $ethHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList pppox_server_config configEthIIIntf $mode $ethHandle]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ethHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configVlanIfInner { vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $vlanHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList pppox_server_config configVlanIfInner $mode $vlanHandle]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configVlanIfOuter { vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $vlanHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList pppox_server_config configVlanIfOuter $mode $vlanHandle]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configIpIntf { ipIfHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $ipIfHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList pppox_server_config configIpIntf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::PppoxServer::configAtmIntf { atmHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $atmHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList pppox_server_config configAtmIntf $mode $atmHandle]

    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $atmHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}
proc ::sth::PppoxServer::processConfigAddrPool { myswitch value } {

    set poolCfg ""
    
    if {$myswitch == "ipv4_pool_addr_start"} {
        set poolCfg "-Ipv4PeerPoolAddr $value -StartIpList $value"
    }
    
    return "$poolCfg"
}

proc ::sth::PppoxServer::processConfigFwdCmd { myswitch value } {

    # get forward map for "constant" property 
    set fwdValue [::sth::sthCore::getFwdmap ::sth::PppoxServer:: pppox_server_config $myswitch $value]
    set stcAttr [::sth::sthCore::getswitchprop ::sth::PppoxServer:: pppox_server_config $myswitch stcattr]
    
    return "-$stcAttr $fwdValue"
}
    
# Handle the username/password wildcards
proc ::sth::PppoxServer::processConfigCmd_wildcard { myswitch value } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    set _OrigHltCmdName "pppox_server_config"
 
    set configList ""
    if {![info exists userArgsArray(${myswitch}_wildcard)] || !$userArgsArray(${myswitch}_wildcard)} {
        lappend configList -$myswitch $value
        return $configList
    } 

    # Calculate the start/end for 4 marker characters
    foreach marker {question pound bang dollar} {
        set ${marker}_start  1
        set ${marker}_count  1
        set ${marker}_step   1
        set ${marker}_fill   0
        set ${marker}_repeat 0
        set ${marker}_end    1

        foreach type {start fill end} {
            if {[info exists userArgsArray(wildcard_${marker}_$type)]} {
                set ${marker}_${type} $userArgsArray(wildcard_${marker}_$type)
            }
        }

        if {[set ${marker}_end] < [set ${marker}_start]} {
            set result "Error: wildcard_${marker}_end ([set ${marker}_end]) must not be less than wildcard_${marker}_start ([set ${marker}_start])"
            return -code 1 -errorcode -1 $result
        }

        set ${marker}_count [expr "([set ${marker}_end] - [set ${marker}_start]) + 1"]
        set ${marker}_string "@x([set ${marker}_start],[set ${marker}_count],[set ${marker}_step],[set ${marker}_fill],[set ${marker}_repeat])"
    }

    if {[info exists userArgsArray(${myswitch}_wildcard)]} {
        # username/password default - spirent/spirent
        set attrValue "spirent"
        if {[info exists userArgsArray($myswitch)]} {
            set attrValue $userArgsArray($myswitch)
        }
        foreach pair {{# pound} {? question} {! bang} {$ dollar}} {
            foreach {symbol marker} $pair {};
            regsub -all \\$symbol $attrValue [set ${marker}_string] attrValue
        }
        lappend configList -$myswitch $attrValue
    }

    return $configList
}


proc ::sth::PppoxServer::processConfigCmd_vlanId { myswitch value } {
    variable userArgsArray
    
    set qinqIncrMode "inner"
    if {[info exists userArgsArray(qinq_incr_mode)]} {
        set qinqIncrMode $userArgsArray(qinq_incr_mode)
    }
    
    foreach item {{vlan_id_step 0} {vlan_id_count 1} {vlan_id_mode increment} {vlan_id_outer_step 0} {vlan_id_outer_count 1} {vlan_id_outer_mode increment}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
        set [string trim $opt "vlan_id_"] $userArgsArray($opt)
    }
    
    if {$myswitch == "vlan_id"} {
        if {[expr $userArgsArray(num_sessions)%$count] != 0} {
            ::sth::sthCore::processError returnKeyedList "Error: The value of -num_sessions should be devided by -$myswitch\_count" {}
            return -code error $returnKeyedList 
        }
        if {$userArgsArray(encap) == "ethernet_ii_qinq"} {
            switch -exact -- $qinqIncrMode {
                "inner" {
                    lappend vlanCfg -IfRecycleCount $count
                }
                "outer" {
                    if {[expr $outer_count-1] > 0} {
                        lappend vlanCfg -IdRepeatCount [expr $outer_count-1] -IfRecycleCount $count
                    } else {
                        lappend vlanCfg -IdRepeatCount 0 -IfRecycleCount $count
                    }
                }
                "both" {
                    lappend vlanCfg -IfRecycleCount $count
                }
            }
        } elseif {$userArgsArray(encap) == "ethernet_ii_vlan"} {
            lappend vlanCfg -IfRecycleCount $count
        }
        if {$mode == "increment"} {
            lappend vlanCfg -IdStep $step
        } elseif {$mode == "fixed"} {
            lappend vlanCfg -IdStep 0
        }
        
        lappend vlanCfg -VlanId $value
        
    } elseif {$myswitch == "vlan_id_outer"} {
        
        if {$userArgsArray(encap) != "ethernet_ii_qinq"} { return }
        
        if {[expr $userArgsArray(num_sessions)%$outer_count] != 0} {
            ::sth::sthCore::processError returnKeyedList "Error: The value of -num_sessions should be devided by -$myswitch\_count" {}
            return -code error $returnKeyedList 
        }
        switch -exact -- $qinqIncrMode {
            "inner" {
                if {[expr $count-1] > 0} {
                    lappend vlanCfg -IdRepeatCount [expr $count-1] -IfRecycleCount $outer_count
                } else {
                    lappend vlanCfg -IdRepeatCount 0 -IfRecycleCount $outer_count
                } 
            }
            "outer" {
               lappend vlanCfg -IfRecycleCount $outer_count
            }
            "both" {
                lappend vlanCfg -IfRecycleCount $outer_count
            }
        }
        if {$mode == "increment"} {
            lappend vlanCfg -IdStep $outer_step
        } elseif {$mode == "fixed"} {
            lappend vlanCfg -IdStep 0
        }
        lappend vlanCfg -VlanId $value
    }

    return $vlanCfg
}

proc ::sth::PppoxServer::processConfigCmd_atmSettings { myswitch value } {
    variable userArgsArray
    
    foreach item {{vci 100} {vci_step 1} {vci_count 1} {vpi 100} {vpi_step 1} {vpi_count 1} {pvc_incr_mode vci}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
        set $opt $userArgsArray($opt)
    }
    
    #validate vci_count and vpi_count
    if {[expr $userArgsArray(num_sessions) % $vci_count != 0]} {
        ::sth::sthCore::processError returnKeyedList "The value $vci_count is not valid for -vci_count, it SHOULD divide -num_sessions $userArgsArray(num_sessions)."
        return -code error $returnKeyedList
    }
    
    if {[expr $userArgsArray(num_sessions) % $vpi_count != 0]} {
        ::sth::sthCore::processError returnKeyedList "The value $vpi_count is not valid for -vpi_count, it SHOULD divide -num_sessions $userArgsArray(num_sessions)."
        return -code error $returnKeyedList
    }
    
    set atmConfig ""
    switch -exact -- $pvc_incr_mode {
        "vci" {
            if {$myswitch == "vci"} {
                set atmConfig "-Vci $value -VciStep $vci_step -VciRecycleCount $vci_count"   
            } elseif {$myswitch == "vpi"} {
                if {[expr $vci_count-1] >= 0} {
                    set vpiRepeat [expr $vci_count-1]
                } else {
                    set vpiRepeat 0
                }
                set atmConfig "-Vpi $value -VpiStep $vpi_step -VpiRepeatCount $vpiRepeat -IfRecycleCount $vpi_count"
            }
        }
        "vpi" {
            if {$myswitch == "vci"} {
                if {[expr $vpi_count-1] >= 0} {
                    set vciRepeat [expr $vpi_count-1]
                } else {
                    set vciRepeat 0
                }
                set atmConfig "-Vci $value -VciStep $vci_step -VciRepeatCount $vciRepeat -VciRecycleCount $vci_count"   
            } elseif {$myswitch == "vpi"} {
                set atmConfig "-Vpi $value -VpiStep $vpi_step -IfRecycleCount $vpi_count"
            }
        }
        "both" {
            if {$myswitch == "vci"} {
                set atmConfig "-Vci $value -VciStep $vci_step -VciRecycleCount $vci_count"                 
            } elseif {$myswitch == "vpi"} {
                set atmConfig "-Vpi $value -VpiStep $vpi_step -IfRecycleCount $vpi_count"              
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Error: Unknown -pvc_incr_mode $pvc_incr_mode." {}
            return -code error $returnKeyedList
        }
    }
    
    return "$atmConfig"
}


proc ::sth::PppoxServer::pppox_server_stats { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {      
        set hostHandleList ""
        if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
            
            foreach hostHandle $userArgsArray(handle) {
                if {![::sth::PppoxServer::IsPppoxServerHandleValid $hostHandle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not valid PPPox Server handle" {}
                    return -code error $returnKeyedList
                }
            }
            set hostHandleList $userArgsArray(handle)         
                    
        } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
            foreach port_handle $userArgsArray(port_handle) {
                if {[::sth::sthCore::IsPortValid $port_handle err]} {
                    if {[catch {set hostHandle [::sth::sthCore::invoke stc::get $port_handle -affiliationport-sources]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList   
                    }
                    set portAgg($port_handle) 0
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                    return -code error $returnKeyedList
                }
                foreach host $hostHandle {
                    set host_name [::sth::sthCore::invoke stc::get $host -name]
                    if {[regexp {^port_address$} $host_name]} {
                        continue
                    }
                    if {![::sth::PppoxServer::IsPppoxServerHandleValid $host]} {
                        continue
                    }
                    lappend hostHandleList $host
                }
            }       
        }
        
        foreach host $hostHandleList {
            if {[catch {set portHdl [::sth::sthCore::invoke stc::get $host -affiliationport-targets]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            # get pppox server port aggregate results
            if {[catch {set pppoxPortHandle [::sth::sthCore::invoke stc::get $portHdl -children-PppoxPortConfig]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                return -code error $returnKeyedList   
            }
            
            if {[catch {set pppoxPortResult [::sth::sthCore::invoke stc::get $pppoxPortHandle -children-PppoePortResults]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                return -code error $returnKeyedList   
            }
            
            set pppoxServerBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($portHdl)]ServerBlockConfig
            set pppoxServerResults [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($portHdl)]ServerBlockResults
            
            # get pppox server block results
            if {[catch {set pppoxBlockHandle [::sth::sthCore::invoke stc::get $host -children-$pppoxServerBlock]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                return -code error $returnKeyedList   
            }
            if {[catch {set pppoxBlockResult [::sth::sthCore::invoke stc::get $pppoxBlockHandle -children-$pppoxServerResults]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                return -code error $returnKeyedList   
            }
            
            #if {[catch {::sth::sthCore::invoke stc::perform PppoxSessionInfo -BlockList $pppoxBlockHandle -saveToFile FALSE} err]} {
            #    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::perform PppoxSessionInfo Failed: $err" {}
            #    return -code error $returnKeyedList   
            #}
            #if {[catch {set pppoxSessionResult [stc::get $pppoxBlockHandle -children-PppoeSessionResults]} err]} {
            #    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
            #    return -code error $returnKeyedList   
            #}
            
            # create an array mapping between stcObj and stcHandle
            set hdlArray(PppoePortResults) $pppoxPortResult
            set hdlArray(PppoeServerBlockResults) $pppoxBlockResult
            #set hdlArray(PppoeSessionResults) $pppoxSessionResult
            
            set mode $userArgsArray(mode)
            
            if {$mode == "aggregate"} {
                if {[info exists portAgg($portHdl)] && $portAgg($portHdl) == 1} {
                    continue
                } else {
                    set portAgg($portHdl) 1
                    keylset returnKeyedList port_handle $portHdl
                    # set port state
                    if {[catch {processPppoxGetCmd_state $mode [::sth::sthCore::invoke stc::get $hdlArray(PppoePortResults) -parent] returnKeyedList} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while fetching portState" $err" {}
                        return -code error $returnKeyedList
                    }
                }
            }
            
            if {$mode == "session"} {
                # set port state
                if {[catch {processPppoxGetCmd_state $mode [::sth::sthCore::invoke stc::get $hdlArray(PppoeServerBlockResults) -parent] returnKeyedList} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while fetching portState" $err" {}
                    return -code error $returnKeyedList
                }
            }
            
            # get the interface stack
            if {[catch {set stack [::sth::sthCore::invoke stc::get $host -children]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            
            set atm 0
            if {[lsearch -regexp $stack "aal5if*"] >= 0} {
                set atm 1
                if {$mode == "aggregate"} {
                    keylset returnKeyedList ${mode}.atm_mode 1
                } elseif {$mode == "session"} {
                    keylset returnKeyedList ${mode}.$host.atm_mode 1
                }
            } else {
                if {$mode == "aggregate"} {
                    keylset returnKeyedList ${mode}.atm_mode 0
                } elseif {$mode == "session"} {
                    keylset returnKeyedList ${mode}.$host.atm_mode 0
                }
            }
            
            foreach key [array names ::sth::PppoxServer::pppox_server_stats_mode] {
                foreach {tblMode tblProc} $::sth::PppoxServer::pppox_server_stats_mode($key) {
                    if {[string match $tblMode $mode]} {
                        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::PppoxServer:: pppox_server_stats $key supported] "false"]} {
                            continue
                        }
                        if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::PppoxServer:: pppox_server_stats $key stcattr]] "_none_"]} {
                            continue
                        }
                        # not in PppoaServerBlockResults 
                        if {$atm && [lsearch "padi_rx padr_rx padt_rx pads_tx padt_tx padi_tx padr_tx pado_rx pads_rx pado_tx" $key] >= 0} {
                            continue
                        }
                        if {$tblMode == "aggregate"} {
                            set stcObj $hdlArray(PppoePortResults)
                            if {[catch {set val [::sth::sthCore::invoke stc::get $stcObj -$stcAttr]} err]} {
                                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "aggregate.$key" $val]
                        } elseif {$tblMode == "session"} {
                            set stcObj $hdlArray(PppoeServerBlockResults)
                            if {[catch {set val [::sth::sthCore::invoke stc::get $stcObj -$stcAttr]} err]} {
                                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "session.$host.$key" $val]
                        } 
                    }
                }
            }
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $returnKeyedList
}


proc ::sth::PppoxServer::processPppoxGetCmd_state { keyName handle returnInfoVarName} {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $returnInfoVarName returnKeyedList

    if {[string match -nocase "session" $keyName]} {
        if {[catch {set host [::sth::sthCore::invoke stc::get $handle -parent]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Error Occured while fetching value of state. Error: $getStatus"
            return -code error $returnKeyedList
        }   
        if {[catch {set stateVal [::sth::sthCore::invoke stc::get $handle -blockState]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Error Occured while fetching value of state. Error: $getStatus"
            return -code error $returnKeyedList
        }
    } elseif {[string match -nocase "aggregate" $keyName]} {
        if {[catch {set stateVal [::sth::sthCore::invoke stc::get $handle -portState]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Error Occured while fetching value of state. Error: $getStatus"
            return -code error $returnKeyedList
        } 
    }

    set connecting 0
    set connected 0
    set disconnecting 0
    set abort 0
    set idle 0
    switch -glob -- $stateVal {
        "CONNECTING*" {
            set connecting 1
        }
        "CONNECTED*" {
            set connected 1
        }
        "DISCONNECTING*" {
            set disconnecting 1
        }
        "TERMINATING*" {
            set abort 1
        }
        "IDLE*" {
            set idle 1
        }
        "NONE" {
            # Do nothing - No host blocks are configured for PPPoX
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Could not resolve state: $stateVal"
            return -code error $returnKeyedList
        }
    }

    if {[string match -nocase "aggregate" $keyName]} {
        keylset returnKeyedList ${keyName}.connecting $connecting
        keylset returnKeyedList ${keyName}.connected $connected
        keylset returnKeyedList ${keyName}.disconnecting $disconnecting
        keylset returnKeyedList ${keyName}.abort $abort
        keylset returnKeyedList ${keyName}.idle $idle
    } elseif {[string match -nocase "session" $keyName]} {
        keylset returnKeyedList ${keyName}.$host.connecting $connecting
        keylset returnKeyedList ${keyName}.$host.connected $connected
        keylset returnKeyedList ${keyName}.$host.disconnecting $disconnecting
        keylset returnKeyedList ${keyName}.$host.abort $abort
        keylset returnKeyedList ${keyName}.$host.idle $idle
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::PppoxServer::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::PppoxServer::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::PppoxServer:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::PppoxServer:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::PppoxServer:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::PppoxServer::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::PppoxServer::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::PppoxServer:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::PppoxServer:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::PppoxServer:: $cmdType $opt $::sth::PppoxServer::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::PppoxServer::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $opt $::sth::PppoxServer::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}

proc ::sth::PppoxServer::IsPppoxServerHandleValid { handle } {
    
    set cmdStatus 0
    if {[catch {set port [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
        return -code error $returnKeyedList 
    }
    
    if {[catch {set hostHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} err]} {
        ::sth::sthCore::processError returnKeyedList "No emulateddevice exists under Project Handle:$::sth::GBLHNDMAP(project)"
        return -code error $returnKeyedList 
    } else {
        foreach hostHandle $hostHandleList {
            if {[string equal $hostHandle $handle]} {
                set cmdStatus 1
                break
            }
        }
        # for cases such as load_xml()
        if {![info exists ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)]} {
            set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port) ""
            regexp {(pppo.)serverblockconfig[0-9]*} [::sth::sthCore::invoke stc::get $handle -children] "" ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)
        }        
        set pppoxBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)]ServerBlockConfig
        if { "" == $::sth::PppoxServer::PPPOXSERVEROBJTYPE($port) || 
        [catch {set pppServerHandle [::sth::sthCore::invoke stc::get $hostHandle -children-$pppoxBlock]} err] || 
        0 == [string length $pppServerHandle] } {
            set cmdStatus 0
        }
        # if {[string length $pppServerHandle] == 0} {
            # set cmdStatus 0
        # }
        if {$cmdStatus == 1} {
            return $::sth::sthCore::SUCCESS
        } else {
            ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid PPPoX Server handle"
            return $::sth::sthCore::FAILURE		
        }		
    }
}

proc ::sth::PppoxServer::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::PppoxServer:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            # unlock the specified dependency relation when modify 
            if {[string match "modify" $mode]} {
                if {[lsearch -exact "ip_cp protocol encap" $dependSwitch] >= 0} {
                    set validFlag 1
                    break
                }
            }
            
            if {[info exists userArgsArray($dependSwitch)] && [string match -nocase $dependValue $userArgsArray($dependSwitch)]} {
                set validFlag 1
                break
            }    
        }
        
        if {$validFlag == 0} { 
            if {[info exists userArgsArray($switchName)]} {
                unset userArgsArray($switchName)
            }
        }
    }
}
