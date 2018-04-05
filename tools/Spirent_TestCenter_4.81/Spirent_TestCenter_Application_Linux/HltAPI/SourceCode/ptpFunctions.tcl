# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/ptpFunctions.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#
namespace eval ::sth::Ptp {
    variable ptp_subscription_state 0
    array set processedTosDiff ""
}


proc ::sth::Ptp::emulation_ptp_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config_create"

    variable ::sth::Ptp::userArgsArray
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
        
        # -transport_type will determine the encapsulation used by PTP protocol as well as determine what address fields wil be presented.
        # If "ethernet_ii" is selected, the IP address configuration will not take effect.
        #
        #####
        #       encapsulation                    transport_type         STC Applicable
        #     ETHERNETII (Ethernet/Ipv4)           UDP_IPV4              yes  (ip multicast)
        #     ETHERNETII (Ethernet/Vlan/IPv4)      UDP_IPV4              yes
        #     ETHERNETII (Ethernet)                ethernet_ii           yes  (mac multicast)
        #     ETHERNETII (Ethernet/Vlan/Vlan)      ethernet_ii           yes
        #     ATM (AAl5/IPv4)                      UDP_IPV4              yes
        #     ATM (AAl5/IPv4)                      ethernet_ii           no (bll encap error)
        #     ETHERNETII_VC_MUX (AAl5/Ethernet/IPv4) UDP_IPV4            yes
        #     ETHERNETII_VC_MUX (AAl5/Ethernet/IPv4) ethernet_ii         no (bll encap error)
        #     ETHERNETII_VC_MUX (AAl5/Ethernet)      ethernet_ii         no (bll encap error)
        #####
        if {[regexp -nocase "ipv4" $userArgsArray(transport_type)]} {
            set ipVersion "ipv4"
            set topif "Ipv4If"
            set IfCount "1"
        } elseif {[regexp -nocase "ipv6" $userArgsArray(transport_type)]} {
            set ipVersion "ipv6"
            set topif "Ipv6If"
            set IfCount "1"
        } elseif {[regexp -nocase "ethernet_ii" $userArgsArray(transport_type)]} {
            set ipVersion "none"
            set topif ""
            set IfCount ""
        }
        
        # create encapsulation stack by -encapsulation
        set encap $userArgsArray(encapsulation)
        
        set vlanFlag 0
        set qinqFlag 0
        
        if {[regexp -- {vlan_id1} $userArgsArray(optional_args)]} {
            if {[regexp -- {vlan_id2} $userArgsArray(optional_args)]} {
                set qinqFlag 1
            } else {
                set vlanFlag 1
            }
        }
        
        switch -- $encap {
            "ETHERNETII" {
                # ptp-oe
                # transport_type can be "ipv4", "ipv6" or "ethernet_ii"
                if {$vlanFlag} {
                    set IfStack "$topif VlanIf EthIIIf"
                    set IfCount "$IfCount 1 1"
                    if {[string length $topif] == 0} {
                        set topif "VlanIf"
                    }
                } elseif {$qinqFlag} {
                    set IfStack "$topif VlanIf VlanIf EthIIIf"
                    set IfCount "$IfCount 1 1 1"
                    if {[string length $topif] == 0} {
                        set topif "VlanIf"
                    }
                } else {
                    set IfStack "$topif EthIIIf"
                    set IfCount "$IfCount 1"
                    if {[string length $topif] == 0} {
                        set topif "EthIIIf"
                    }
                }
            }
            "LLC_SNAP" -
            "VC_MUX" {
                # ptp-oa
                # transport_type can be "ipv4" or "ipv6"; "ethernet_ii" is not allowed under atm encapsulton
                set IfStack "$topif Aal5If"
                set IfCount "$IfCount 1"
                if {[string length $topif] == 0} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -transport_type $userArgsArray(transport_type)" {}
                    return -code error $returnKeyedList  
                }
            }
            "ETHERNETII_LLC_SNAP" -
            "ETHERNETII_VC_MUX" {
                # ptp-oeoa
                # transport_type can be "ipv4", "ipv6" or "ethernet_ii"
                if {$vlanFlag} {
                    set IfStack "$topif VlanIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1"
                    if {[string length $topif] == 0} {
                        set topif "VlanIf"
                    }
                } elseif {$qinqFlag} {
                    set IfStack "$topif VlanIf VlanIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1"
                    if {[string length $topif] == 0} {
                        set topif "VlanIf"
                    }
                } else {
                    set IfStack "$topif EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1"
                    if {[string length $topif] == 0} {
                        set topif "EthIIIf"
                    }
                }
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -encap $encap" {}
                return -code error $returnKeyedList  
            }
            
        }
    
        set createdDeviceList ""
        for {set i 1} {$i <= $userArgsArray(count)} {incr i} {
            
            # create PTP device
            array set DeviceCreateOutput [::sth::sthCore::invoke "stc::perform DeviceCreate \
	    						-ParentList $::sth::GBLHNDMAP(project) \
							-DeviceType Router \
							-IfStack \"$IfStack\" \
							-IfCount \"$IfCount\" \
							-Port $portHandle"]
            set createdDevice $DeviceCreateOutput(-ReturnList)
            
            lappend createdDeviceList $createdDevice
            # adjust link local interface for ipv6 case
            if {[string match -nocase "ipv6" $ipVersion]} {
                         
                #### ipv6 encap stack map ####
                #
                #                    'toplevelIf'           UsesIf
                #         emulateddevice1 -----> ipv6if1  <------- Ieee1588v2ClockConfig
                #              |                    |
                # 'toplevelIf' |                    |
                # 'PrimaryIf'  |                    |
                #              |                    |
                #   ipv6if2(linklocal)--------> vlanIf1 ---> vlanIf2 ---> ethIIIf1
                #
                #
                ####
                #  link local ipv6 interface faces to the DUT
                #  global ipv6 interface faces to Ieee1588v2ClockConfig
                ####
                
                set ipv6If [::sth::sthCore::invoke stc::get $createdDevice -children-ipv6if]
                set lowerIf [::sth::sthCore::invoke stc::get $ipv6If -StackedOnEndpoint-targets]
            
                # create new ipv6if
                set cfglist "-Address fe80::1 -AddrStep ::1 -PrefixLength 64"
                set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $createdDevice "$cfglist -toplevelIf-sources $createdDevice -StackedOnEndpoint-targets $lowerIf"]
                ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
                ::sth::sthCore::invoke stc::config $createdDevice "-primaryif-targets $linkLocalIf"
            }
                    
            # config atm encapsulation type for ATM interface
            if {[regexp "VC_MUX" $encap] || [regexp "LLC_SNAP" $encap]} {
                set atmHandle [::sth::sthCore::invoke stc::get $createdDevice -children-Aal5If]
                if {[regexp "VC_MUX" $encap]} {
                    ::sth::sthCore::invoke stc::config $atmHandle "-VcEncapsulation VC_MULTIPLEXED"
                } elseif {[regexp "LLC_SNAP" $encap]} {
                    ::sth::sthCore::invoke stc::config $atmHandle "-VcEncapsulation LLC_ENCAPSULATED"
                }
            }
            
            # config device name
            if {[info exists userArgsArray(name)]} {
                ::sth::sthCore::invoke stc::config $createdDevice "-Name $userArgsArray(name)"
            }
            
            set ipStack [::sth::sthCore::invoke stc::get $createdDevice -children-$topif]
            
            # lindex to get the gloal ipv6 interface in case of ipv6
            set ipStack [lindex $ipStack 0] 
            
            # Create Ieee1588v2ClockConfig block
            set ptpConfig [::sth::sthCore::invoke stc::create Ieee1588v2ClockConfig -under $createdDevice "-UsesIf-targets $ipStack"]
                    
            ### Config input switches
            ::sth::Ptp::processConfigSwitches $createdDevice create $ipVersion $i returnKeyedList
        }
        
        # create ptp result dataset
        if {$::sth::Ptp::ptp_subscription_state == 0} {
            set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set ptpResultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet \
	    					"-ResultRootList $::sth::GBLHNDMAP(project) \
						-ConfigClassId Ieee1588v2ClockConfig \
						-ResultClassId Ieee1588v2ClockResult"]
            set ptpResultQuery2 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet \
	    					"-ResultRootList $::sth::GBLHNDMAP(project) \
						-ConfigClassId Ieee1588v2ClockConfig \
						-ResultClassId ParentClockInfoResult"]
            set ptpResultQuery3 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet \
	    					"-ResultRootList $::sth::GBLHNDMAP(project) \
						-ConfigClassId Ieee1588v2ClockConfig \
						-ResultClassId ClockSynchronizationResult"]
            set ptpResultQuery4 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet \
	    					"-ResultRootList $::sth::GBLHNDMAP(project) \
						-ConfigClassId Ieee1588v2ClockConfig \
						-ResultClassId TimePropertiesResult"]
        }
        
        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying PTP configuration: $err"
            return $returnKeyedList
        }
        
        if {$::sth::Ptp::ptp_subscription_state == 0} {
            # Subscribe to the datasets
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            set ::sth::Ptp::ptp_subscription_state 1
        }
        
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any device created if error occurs
        if {[info exists createdDevice]} {
            ::sth::sthCore::invoke stc::delete $createdDevice
        }
    } else {
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList handle $createdDeviceList   
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}

proc ::sth::Ptp::emulation_ptp_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config_modify"

    variable ::sth::Ptp::userArgsArray
    variable ::sth::Ptp::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set deviceHandleList $userArgsArray(handle)
            if {![IsPtpHandleValid $deviceHandleList]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandleList is not valid ptp device handle" {}
                return -code error $returnKeyedList 
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        
        # checking unsupported switches under "modify" mode
        set unsupportedModifyOptions {port_handle encapsulation count transport_type}
        
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                    ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        # modify device name
        if {[info exists userArgsArray(name)]} {
            ::sth::sthCore::invoke stc::config $deviceHandleList "-Name $userArgsArray(name)"
        }
        
        # modify input arguments
        foreach deviceHandle $deviceHandleList {
            set childList [::sth::sthCore::invoke stc::get $deviceHandle -children]
            if {[regexp -- "ipv4if" $childList]} {
                set ipVersion "ipv4"
                set ipIf [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv4if]
                if {[info exists ::sth::Ptp::processedTosDiff($ipIf)]} {
                    set ::sth::Ptp::processedTosDiff($ipIf) 0
                }
            } elseif {[regexp -- "ipv6if" $childList]} {
                set ipVersion "ipv6"
            } else {
                set ipVersion "none"
            }
            ::sth::Ptp::processConfigSwitches $deviceHandle modify $ipVersion 1 returnKeyedList  
        }
        
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList handle $deviceHandleList   
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList

}


proc ::sth::Ptp::emulation_ptp_config_enable {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config_enable"

    variable ::sth::Ptp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch { 
        foreach deviceHandle $userArgsArray(handle) {
            
            if {![IsPtpHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not a valid PTP device handle" {}
                return -code error $returnKeyedList 
            }
        
            #get Ieee1588v2ClockConfig
            set ptpClockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Ieee1588v2ClockConfig ]
            #active ptp
            ::sth::sthCore::invoke stc::config $ptpClockCfg "-Active TRUE"
        }
        
        keylset returnKeyedList handle $userArgsArray(handle)

    } returnedString]
    
    return -code $retVal $returnedString
}


proc ::sth::Ptp::emulation_ptp_config_disable {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config_disable"

    variable ::sth::Ptp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch {
        foreach deviceHandle $userArgsArray(handle) {
        
            if {![IsPtpHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not a valid PTP device handle" {}
                return -code error $returnKeyedList 
            }
        
            set ptpClockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Ieee1588v2ClockConfig ]
         
            ::sth::sthCore::invoke stc::config $ptpClockCfg "-Active FALSE"
        }
        keylset returnKeyedList handle $userArgsArray(handle)
        
    } returnedString]
    
    return -code $retVal $returnedString
}


proc ::sth::Ptp::emulation_ptp_config_enable_all {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config_enable_all"

    variable ::sth::Ptp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {    
        if {![info exists userArgsArray(port_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle." {}
            return $returnKeyedList
        }
    
        foreach portHandle $userArgsArray(port_handle) {
            if {![::sth::sthCore::IsPortValid $portHandle eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                return $returnKeyedList
            }
        
            set handleList [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
            
            foreach handle $handleList {
                if {![string match -nocase "router*" $handle]} {
                    continue
                }
                if {[IsPtpHandleValid $handle]} {
                    
                    set ptpClockCfg [::sth::sthCore::invoke stc::get $handle -children-Ieee1588v2ClockConfig ]
                   
                    ::sth::sthCore::invoke stc::config $ptpClockCfg "-Active TRUE"
                    lappend ptpHandleList $handle
                }  
            }  
        }
        
        keylset returnKeyedList handle $ptpHandleList
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::Ptp::emulation_ptp_config_disable_all {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config_disable_all"

    variable ::sth::Ptp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle." {}
        return $returnKeyedList
        }
        
        foreach portHandle $userArgsArray(port_handle) {
            if {![::sth::sthCore::IsPortValid $portHandle eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                return $returnKeyedList
            }
         
            set handleList [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
        
            foreach handle $handleList {
                if {![string match -nocase "router*" $handle]} {
                    continue
                }
                if {[IsPtpHandleValid $handle]} {
                    set ptpClockCfg [::sth::sthCore::invoke stc::get $handle -children-Ieee1588v2ClockConfig ]
    
                    ::sth::sthCore::invoke stc::config $ptpClockCfg "-Active FALSE"
                    lappend ptpHandleList $handle
                }  
            }
        }
        
        keylset returnKeyedList handle $ptpHandleList
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::Ptp::emulation_ptp_config_delete { returnKeyedListVarName } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }
        
        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![IsPtpHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid PTP handle" {}
                return -code error $returnKeyedList 
            }
            
            ::sth::sthCore::invoke stc::delete $deviceHandle
        }
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}

proc ::sth::Ptp::processConfigSwitches {handleList mode ipVersion index returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Ptp::sortedSwitchPriorityList
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_config $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_config $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Ptp:: emulation_ptp_config $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    foreach deviceHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    set ethiiIf [::sth::sthCore::invoke stc::get $deviceHandle -children-EthIIIf]
                    if {[string length $ethiiIf] != 0} {
                        configEthIIIntf $ethiiIf $index $mode
                    }
                }
                configVlanIfInner {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    
                    # for vlan encapsulation, config "-vlan_id1" as vlan id
                    # for qinq encapsulation, config "-vlan_id1" as "outer vlan"
                    # here, the function name is a bit different with the feature implemented.
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 1]
                        }
                        configVlanIfInner $vlanIf $index $mode
                    }
                }
                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] < 2} {continue}
                        # for qinq encapsulation, config "-vlan_id2" as "inner vlan"
                        set vlanIf [lindex $vlanIf 0]
                        configVlanIfOuter $vlanIf $index $mode
                    }

                }
                configIpIntf {
                    if {![regexp -nocase "ipv4" $ipVersion] && ![regexp -nocase "ipv6" $ipVersion]} {
                        continue
                    }
                    set ipIf [::sth::sthCore::invoke stc::get $deviceHandle -children-${ipVersion}if]
                    if {[llength $ipIf] != 0} {
                        if {[llength $ipIf] > 1} {
                            # get global ipv6if 
                            set ipIf [lindex $ipIf 0] 
                        }
                        configIpIntf $ipIf $index $mode
                    }
                }
                configAtmIntf {
                    set atmIf [::sth::sthCore::invoke stc::get $deviceHandle -children-Aal5If]
                    if {[string length $atmIf] != 0} {
                        configAtmIntf $atmIf $index $mode
                    }
                }
                configIeee1588v2Config {
                    set port [::sth::sthCore::invoke stc::get $deviceHandle -AffiliationPort-targets]
                    set ptpClockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Ieee1588v2ClockConfig]
                    configIeee1588v2Config $ptpClockCfg $index $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
}

proc ::sth::Ptp::configIeee1588v2Config { ptpClockCfg index mode } {
    
    set optionValueList [getStcOptionValueList emulation_ptp_config configIeee1588v2Config $mode $ptpClockCfg $index]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ptpClockCfg $optionValueList
    }
}

proc ::sth::Ptp::configEthIIIntf { ethHandle index mode } {

    set optionValueList [getStcOptionValueList emulation_ptp_config configEthIIIntf $mode $ethHandle $index]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::Ptp::configVlanIfInner { vlanHandle index mode } {

    set optionValueList [getStcOptionValueList emulation_ptp_config configVlanIfInner $mode $vlanHandle $index]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Ptp::configVlanIfOuter { vlanHandle index mode } {

    set optionValueList [getStcOptionValueList emulation_ptp_config configVlanIfOuter $mode $vlanHandle $index]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Ptp::configIpIntf { ipIfHandle index mode } {

    set optionValueList [getStcOptionValueList emulation_ptp_config configIpIntf $mode $ipIfHandle $index]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::Ptp::configAtmIntf { atmHandle index mode } {

    set optionValueList [getStcOptionValueList emulation_ptp_config configAtmIntf $mode $atmHandle $index]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $atmHandle $optionValueList
    }
}

proc ::sth::Ptp::processConfigFwdCmd { handle myswitch value index } {

    # get forward map for "constant" property 
    set fwdValue [::sth::sthCore::getFwdmap ::sth::Ptp:: emulation_ptp_config $myswitch $value]
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_config $myswitch stcattr]
    
    return "-$stcAttr $fwdValue"
}

proc ::sth::Ptp::processConfigCmd_macAddr { handle myswitch value index } {
    variable userArgsArray
    
    if {![regexp -- "ETHERNETII" $userArgsArray(encapsulation)]} { return }
    
    foreach item {{local_mac_addr_step "00:00:00:00:00:01"} {local_mac_addr_repeat 0}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
    }
    
    set newmacaddr [::sth::sthCore::macStep $userArgsArray(local_mac_addr) $userArgsArray(local_mac_addr_step) [expr ($index-1)/($userArgsArray(local_mac_addr_repeat)+1)]]    
        
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
  
    return "-$stcattr $newmacaddr"
}


# When multiple vlans are configured, -vlan_id1 is used to specify outer vlan id for Ethernet filed, -vlan_id2 is used to specify inner vlan id
# When only -vlan_id1 is specified, Ethernet vlan encapsulation is configured
proc ::sth::Ptp::processConfigCmd_vlanId { handle myswitch value index } {
    variable userArgsArray

    foreach item {{vlan_id_step1 1} {vlan_id_repeat1 0} {vlan_id_mode1 increment} {vlan_id_step2 1} {vlan_id_repeat2 0} {vlan_id_mode2 increment}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
        set [string trim $opt "vlan_id_"] $userArgsArray($opt)
    }
    
    if {$myswitch == "vlan_id1"} {
        if {![regexp -- "ETHERNETII" $userArgsArray(encapsulation)]} { return }
        
        if {$mode1 == "increment"} {
            set vlanId [expr $value+$step1*(($index-1)/($repeat1+1))]   
        } elseif {$mode1 == "fixed"} {
            set vlanId $value
        }
        lappend vlanCfg -VlanId $vlanId
        
    } elseif {$myswitch == "vlan_id2"} {
        if {![regexp -- "ETHERNETII" $userArgsArray(encapsulation)]} { return }
        
        # vlan_id1 is to be specified when config qinq mode
        if {![regexp -- "vlan_id1" $userArgsArray(optional_args)]} { return}
        
        if {$mode2 == "increment"} {
            set vlanId [expr $value+$step2*(($index-1)/($repeat2+1))]
        } elseif {$mode1 == "fixed"} {
            set vlanId $value
        }
        lappend vlanCfg -VlanId $vlanId
    }

    return $vlanCfg
}

proc ::sth::Ptp::processConfigCmd_atmSettings { handle myswitch value index } {
    variable userArgsArray
    
    if {![regexp -- "LLC_SNAP" $userArgsArray(encapsulation)] && ![regexp -- "VC_MUX" $userArgsArray(encapsulation)]} { return }

    foreach item {{vci 100} {vci_step 1} {vpi 100} {vpi_step 1}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
        set $opt $userArgsArray($opt)
    }
    
    set atmConfig ""
    if {$myswitch == "vci"} {
        set vci [expr $value+$vci_step*($index-1)]
        lappend atmConfig -vci $vci
    } elseif {$myswitch == "vpi"} {
        set vpi [expr $value+$vpi_step*($index-1)]
        lappend atmConfig -vpi $vpi
    }
    
    return $atmConfig
}


proc ::sth::Ptp::processConfigCmd_ipSettings { handle myswitch value index } {
	variable userArgsArray
        
        foreach item {{local_ip_addr_step "0.0.0.1"} {local_ip_addr_repeat 0} {}} {
            foreach {opt default} $item {}
            if {![info exists userArgsArray($opt)]} {
                set userArgsArray($opt) $default
            }
        }
        
        if {$myswitch == "local_ip_addr"} {
            if {![info exist userArgsArray(local_ip_addr_step)]} { set userArgsArray(local_ip_addr_step) "0.0.0.1" }
            if {![info exist userArgsArray(local_ip_addr_repeat)]} { set userArgsArray(local_ip_addr_repeat) 0 }
            set newipaddr [::sth::sthCore::updateIpAddress 4 $value $userArgsArray(local_ip_addr_step) [expr ($index-1)/($userArgsArray(local_ip_addr_repeat)+1)]]
        } elseif {$myswitch == "local_ipv6_addr"} {
            if {![info exist userArgsArray(local_ipv6_addr_step)]} { set userArgsArray(local_ipv6_addr_step) "::1" }
            if {![info exist userArgsArray(local_ipv6_addr_repeat)]} { set userArgsArray(local_ipv6_addr_repeat) 0 }
            set newipaddr [::sth::sthCore::updateIpAddress 6 $value $userArgsArray(local_ipv6_addr_step) [expr ($index-1)/($userArgsArray(local_ipv6_addr_repeat)+1)]]
        } elseif {$myswitch == "remote_ip_addr"} {
            if {![info exist userArgsArray(remote_ip_addr_step)]} { set userArgsArray(remote_ip_addr_step) "0.0.0.0" }
            set newipaddr [::sth::sthCore::updateIpAddress 4 $value $userArgsArray(remote_ip_addr_step) [expr $index-1]]
        } elseif {$myswitch == "remote_ipv6_addr"} {
            if {![info exist userArgsArray(remote_ipv6_addr_step)]} { set userArgsArray(remote_ipv6_addr_step) "::" }
            set newipaddr [::sth::sthCore::updateIpAddress 6 $value $userArgsArray(remote_ipv6_addr_step) [expr $index-1]]
        }
        
        if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_config $myswitch stcattr]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
            return -code error $returnKeyedList 
        }
  
    return "-$stcattr $newipaddr"
}


proc ::sth::Ptp::processConfigCmd_clockId { handle myswitch value index} {
    variable userArgsArray
    
    if {[info exists userArgsArray(ptp_clock_id)] } {
        foreach clock_id [split $userArgsArray(ptp_clock_id)] {
            if {[regexp -- "0x" $clock_id]} {
                set clockId [string trimleft $clock_id "0x"]
                if {[string length $clockId] > 16} {
                    ::sth::sthCore::processError returnKeyedList "The length of -ptp_clock_id should be LESS than 16" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
    
    foreach item {{ptp_clock_id_step 0000000000000000} {ptp_clock_id_mode increment} {ptp_clock_id_repeat 0}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
        set $opt $userArgsArray($opt)
    }
    
    if {$ptp_clock_id_mode == "increment"} {

        if {[regexp -- "0x" $value]} { set value [string trimleft $value "0x"] }
        if {[regexp -- "0x" $ptp_clock_id_step]} { set ptp_clock_id_step [string trimleft $ptp_clock_id_step "0x"] }
    
        # change hex string to binary format
                # use parameter count to replace default count for "B" format which is a multiple of 8
        set count [expr 4*[string length $value]]
        binary scan [binary format H* $value] B$count clockId_bin
        set count [expr 4*[string length $ptp_clock_id_step]]
        binary scan [binary format H* $ptp_clock_id_step] B$count clockStep_bin
        
        if {![expr ($index-1)%($ptp_clock_id_repeat+1)] && [expr ($index-1)/($ptp_clock_id_repeat+1)]} {
            ::sth::sthCore::binaryAddition $clockId_bin $clockStep_bin newClock_bin
            set newClockId [::sth::sthCore::binToHex $newClock_bin]
            set newClockId "0x$newClockId"
            set userArgsArray(ptp_clock_id) $newClockId
        } else {
            set newClockId $userArgsArray(ptp_clock_id) 
        }
    } elseif {$ptp_clock_id_mode == "list"} {
        set len [llength $value]
        set newClockId [lindex $value [expr ($index-1)%$len]]
    }
        
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
  
    return "-$stcattr $newClockId"
}

proc ::sth::Ptp::processConfigCmd_tos { handle myswitch value index} {
    variable userArgsArray
        
    set tosCfg ""
    
    # ipv4 tos or diff_ser is configurable when -transport_type is ipv4
    if {$userArgsArray(transport_type) == "ipv6" || $userArgsArray(transport_type) == "ethernet_ii"} { return }
    if {[string match -nocase "diff-serv" $userArgsArray(ipv4_priority)]} { return }
    
    if {$myswitch == "ip_tos_field"} {
        # -ip_tos_field takes higher priorty if any -tos_** and -ip_tos_field are configured both
        set ::sth::Ptp::processedTosDiff($handle) 1
        # convert hex to interger
        if {[regexp -- "0x" $value]} { set value [string trimleft $value "0x"] }
        set count [expr 4*[string length $value]]
        binary scan [binary format H* $value] B$count tos
        set tosValue [::sth::sthCore::binToInt $tos]
        set tosCfg "-Tos $tosValue"
    } else {
        if {[info exists ::sth::Ptp::processedTosDiff($handle)] && $::sth::Ptp::processedTosDiff($handle) == 1} { return }
        set ::sth::Ptp::processedTosDiff($handle) 1
        ####
        # IP precedence (3-bit) + Tos (4-bit) + unused
        #
        # tos_precedence: The first 3 bits of 8-bit Tos value, routine-000(default), priority-001 .. network-control-111(better)
        # tos_delay: The 4th bit of 8-bit Tos, 0 - normal, 1 - low
        # tos_throughput: The 5th bit of  8-bit Tos, 0 - normal, 1 - high
        # tos_reliability: The 6th bit of  8-bit Tos, 0 - normal, 1 - high
        # tos_monetary_cost: The 7th bit of  8-bit Tos, 0 - normal, 1 - minimize
        # tos_unused The 8th bit of 8-bit Tos
        ####
        foreach item {{tos_precedence internet-control} {tos_delay normal} {tos_throughput normal} {tos_reliability normal} {tos_monetary_cost normal} {tos_unused 0x0}} {
            foreach {opt default} $item {}
            if {![info exists userArgsArray($opt)]} {
                set userArgsArray($opt) $default
            }
            set $opt [lindex [::sth::Ptp::processConfigFwdCmd $handle $opt $userArgsArray($opt) $index] 1]
        }
        set tos $tos_precedence$tos_delay$tos_throughput$tos_reliability$tos_monetary_cost$tos_unused
        set tosValue [::sth::sthCore::binToInt $tos]
        set tosCfg "-Tos $tosValue"
    }
    return $tosCfg
}

proc ::sth::Ptp::processConfigCmd_diffserv { handle myswitch value index} {
    variable userArgsArray
    
    # ipv4 tos or diff_ser is configurable when -transport_type is ipv4
    if {$userArgsArray(transport_type) == "ipv6" || $userArgsArray(transport_type) == "ethernet_ii"} { return }
    if {[string match -nocase "tos" $userArgsArray(ipv4_priority)]} { return }
    ####
    # The first 6-bit of Differentiated Services 
    # diff_default  (default PHB)
    # diff_assured_forwarding  (AF PHB)
    # diff_explicit_forwarding (EF PHB)
    # diff_class  
    # The last 2 bit of 8-bit DiffServ
    # diff_ecn: 
    ####
    
    # Note: 1 diff_default takes higher priority than diff_assured_forwarding, diff_explicit_forwarding, -diff_class
    # 2, diff_assured_forwarding, diff_explicit_forwarding take higher priority than -diff_class
    # 3, it makes sence to use "drop precedece" (low|mediate|high) with AF PHB to assure traffic bandwidth -> from AF11 to AF43.
    #  For EF or default PHB, do not use drop precedence field ???
    set diffCfg ""
    if {$myswitch == "diff_default"} {
        
        if {[info exists ::sth::Ptp::processedTosDiff($handle)] && $::sth::Ptp::processedTosDiff($handle) == 1} { return }
        set ::sth::Ptp::processedTosDiff($handle) 1
        
        if {[string compare $value "0"] < 0 || [string compare $value "255"] > 0} {
            ::sth::sthCore::processError returnKeyedList " Invalid diff_default $value: should be between 0 and 255" {}
            return -code error $returnKeyedList
        } 
        set diffCfg "-Tos $value"
        
    } else {
        if {$myswitch == "diff_assured_forwarding"} {
            if {[info exists userArgsArray(diff_default)]} { return }
            if {[info exists ::sth::Ptp::processedTosDiff($handle)] && $::sth::Ptp::processedTosDiff($handle) == 1} { return }
            set ::sth::Ptp::processedTosDiff($handle) 1
            
            set dscp [lindex [::sth::Ptp::processConfigFwdCmd $handle $myswitch $value $index] 1]
            
        }
        if {$myswitch == "diff_explicit_forwarding"} {
            if {[info exists userArgsArray(diff_default)]} { return }
            # Codepoint '101110' is recommended for the EF PHB
            if {[info exists ::sth::Ptp::processedTosDiff($handle)] && $::sth::Ptp::processedTosDiff($handle) == 1} { return }
            set ::sth::Ptp::processedTosDiff($handle) 1
            
            if {[string compare $value "0"] < 0 || [string compare $value "63"] > 0} {
                ::sth::sthCore::processError returnKeyedList " Invalid diff_explicit_forwarding $value: should be between 0 and 63" {}
                return -code error $returnKeyedList
            } 
            
            binary scan [binary format c* $value] B* dscp
            set dscp [string trimleft $dscp "00"]
        }
        if {$myswitch == "diff_class"} {
            if {[info exists userArgsArray(diff_default)]} { return }
            if {[info exists userArgsArray(diff_assured_forwarding)]} { return }
            if {[info exists userArgsArray(diff_explicit_forwarding)]} { return }
            
            if {[string compare $value "0"] < 0 || [string compare $value "7"] > 0} {
                ::sth::sthCore::processError returnKeyedList " Invalid diff_class $value: should be between 0 and 7" {}
                return -code error $returnKeyedList
            } 
            
            binary scan [binary format c* $value] B* dscp
            set dscp [string trimleft $dscp "00000"]
        }
        
        if {![info exists userArgsArray(diff_ecn)]} {
            set userArgsArray(diff_ecn) "non-ecn-capable-transport"
        }
        
        set ecn [lindex [::sth::Ptp::processConfigFwdCmd $handle diff_ecn $userArgsArray(diff_ecn) $index] 1]
        set diffValue [::sth::sthCore::binToInt $dscp$ecn]
        set diffCfg "-Tos $diffValue"
    }

    
    return $diffCfg
}

proc ::sth::Ptp::emulation_ptp_stats { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {      
        set deviceHandleList ""
        if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
            foreach handle $userArgsArray(handle) {
                if {![::sth::Ptp::IsPtpHandleValid $handle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $handle is not valid PTP handle" {}
                    return -code error $returnKeyedList
                }
                lappend deviceHandleList $handle
            }
                    
        } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
            foreach port $userArgsArray(port_handle) {
                if {[::sth::sthCore::IsPortValid $port err]} {
                    set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                foreach device $deviceHandle {
                    if {![::sth::Ptp::IsPtpHandleValid $device]} { continue }
                    lappend deviceHandleList $device
                }
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                    return -code error $returnKeyedList
                }
            }
        }
        
        foreach device $deviceHandleList {
            set ptpClockCfg [::sth::sthCore::invoke stc::get $device -children-Ieee1588v2ClockConfig]
            
            # get ptp result obj
            set ptpClockResult [::sth::sthCore::invoke stc::get $ptpClockCfg -children-Ieee1588v2ClockResult]
            set parentInfoResult [::sth::sthCore::invoke stc::get $ptpClockCfg -children-ParentClockInfoResult]
            set ptpSyncResult [::sth::sthCore::invoke stc::get $ptpClockCfg -children-ClockSynchronizationResult]
            set timePropResult [::sth::sthCore::invoke stc::get $ptpClockCfg -children-TimePropertiesResult]

            # create an array mapping between stcObj and stcHandle
            set hdlArray(Ieee1588v2ClockResult) $ptpClockResult
            set hdlArray(ParentClockInfoResult) $parentInfoResult
            set hdlArray(ClockSynchronizationResult) $ptpSyncResult
            set hdlArray(TimePropertiesResult) $timePropResult
            
            set mode $userArgsArray(mode)
            
            set clock_state [::sth::Ptp::processPtpGetCmd_state $device]
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$device.clock_state" $clock_state]

            
            foreach key [array names ::sth::Ptp::emulation_ptp_stats_mode] {
                foreach {tblMode tblProc} $::sth::Ptp::emulation_ptp_stats_mode($key) {
                    if {[string match $tblMode $mode]} {
                        
                        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_stats $key supported] "false"]} {
                            continue
                        }
                        if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_stats $key stcattr]] "_none_"]} {
                            continue
                        }
                            
                        if {$tblMode == "device"} {
                            # convert clock accuracy display name
                            if {$key == "bmc_clock_accuracy"} {
                                ::sth::Ptp::processPtpGet_ClockAccuracy $device returnKeyedList
                                continue
                            }
                            
                            set depend [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_stats $key dependency]
                            if {$depend == "slave" && $clock_state != "slave"} {
                                continue
                            }
                            
                            if {[catch {set stcObj [::sth::sthCore::getswitchprop ::sth::Ptp:: emulation_ptp_stats $key stcobj]} err]} {
                                ::sth::sthCore::processError returnKeyedList "emulation_ptp_stats $key Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set obj $hdlArray($stcObj)
                            set val [::sth::sthCore::invoke stc::get $obj -$stcAttr]
                            
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$device.$key" $val]
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


proc ::sth::Ptp::processPtpGetCmd_state { handle} {
    variable userArgsArray

    set ptpConfig [::sth::sthCore::invoke stc::get $handle -children-Ieee1588v2ClockConfig]
    set stateVal [::sth::sthCore::invoke stc::get $ptpConfig -ClockState]

    switch -glob -- $stateVal {
        "IEEE1588_STATE_INITIALIZING*" {
            set state "initializing"
        }
        "IEEE1588_STATE_FAULTY*" {
            set state "faulty"
        }
        "IEEE1588_STATE_DISABLED*" {
            set state "disabled"
        }
        "IEEE1588_STATE_LISTENING*" {
            set state "listening"
        }
        "IEEE1588_STATE_PRE_MASTER*" {
            set state "pre_master"
        }
        "IEEE1588_STATE_MASTER*" {
            set state "master"
        }
        "IEEE1588_STATE_PASSIVE*" {
            set state "passive"
        }
        "IEEE1588_STATE_UNCALIBRATED*" {
            set state "uncalibrated"
        }
        "IEEE1588_STATE_SLAVE*" {
            set state "slave"
        }
        "IEEE1588_STATE_NONE" {
            set state "none"
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Could not resolve state: $stateVal"
            return -code error $returnKeyedList
        }
    }

    return $state
}
      
      
proc ::sth::Ptp::processPtpGet_ClockAccuracy { handle returnInfoVarName } {
    variable userArgsArray

    upvar 1 $returnInfoVarName returnKeyedList

    set ptpConfig [::sth::sthCore::invoke stc::get $handle -children-Ieee1588v2ClockConfig]
    set parentClock [::sth::sthCore::invoke stc::get $ptpConfig -children-ParentClockInfoResult]
    set clockAccur [::sth::sthCore::invoke stc::get $parentClock -GrandmasterClockAccuracy]
    switch -regexp -- $clockAccur {
        "LESS_025_0NS" {
            set accurancy "25ns"
        }
        
        "LESS_100_0NS" {
            set accurancy "100ns"
        }
        
        "LESS_250_0NS" {
            set accurancy "250ns"
        }
        "LESS_001_0US" {
            set accurancy "1us"
        }
        "LESS_002_5US" {
            set accurancy "2.5us"
        }
        "LESS_010_0US" {
            set accurancy "10us"
        }
        "LESS_025_0US" {
            set accurancy "25us"
        }
        "LESS_100_0US" {
            set accurancy "100us"
        }
        "LESS_250_0US" {
            set accurancy "250us"
        }
        "LESS_001_0MS" {
            set accurancy "1ms"
        }
        "LESS_002_5MS" {
            set accurancy "2.5ms"
        }
        "LESS_010_0MS" {
            set accurancy "10ms"
        }
        "LESS_025_0MS" {
            set accurancy "25ms"
        }
        "LESS_100_0MS" {
            set accurancy "100ms"
        }
        "LESS_250_0MS" {
            set accurancy "250ms"
        }
        "LESS_001_0S" {
            set accurancy "1s"
        }
        "LESS_010_0S" {
            set accurancy "10s"
        }
        "GREATER_010_0S" {
            set accurancy ">10s"
        }
        default {
            set accurancy $clockAccur
        }
    }

    keylset returnKeyedList $handle.bmc_clock_accuracy $accurancy

}



proc ::sth::Ptp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    
    set optionValueList {}
    
    foreach item $::sth::Ptp::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Ptp:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ptp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Ptp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::Ptp::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::Ptp::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Ptp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Ptp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Ptp:: $cmdType $opt $::sth::Ptp::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::Ptp::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Ptp::userArgsArray($opt) $index]
                }
            }
    }
    return $optionValueList
}

proc ::sth::Ptp::IsPtpHandleValid { handle } {
    
    set cmdStatus 0
    set port [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
    
    if {[catch {set deviceHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]} err]} {
        ::sth::sthCore::processError returnKeyedList "No device exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return -code error $returnKeyedList 
    } else {
	foreach deviceHandle $deviceHandleList {
	    if {[string equal $deviceHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}

	if {[catch {set ptpClockConfig [::sth::sthCore::invoke stc::get $deviceHandle -children-Ieee1588v2ClockConfig]} err]} {
	    set cmdStatus 0
	}
        if {[string length $ptpClockConfig] == 0} {
            set cmdStatus 0
        }
	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    #::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid Dhcp Server handle"
	    return $::sth::sthCore::FAILURE		
	}		
    }
}

proc ::sth::Ptp::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::Ptp:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            # unlock the specified dependency relation when modify 
            if {[string match "modify" $mode]} {
                if {[lsearch -exact "transport_type device_type" $dependSwitch] >= 0} {
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
