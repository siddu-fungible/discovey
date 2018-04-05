
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dot1x {
    # a global variable indicating whether to subscribe dot1x result objects
    variable dot1x_subscription_state 0
    array set ENCAP ""
    array set NUM_SESSIONS ""
    array set VLAN_INNER_TO_HANDLE_MAP ""
    array set VLAN_OUTER_TO_HANDLE_MAP ""
    array set HANDLE_TO_QINQ_MODE_MAP ""
    array set VLANS ""
}


proc ::sth::Dot1x::emulation_dot1x_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dot1x_config_create"

    variable ::sth::Dot1x::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ENCAP
    variable VLAN_INNER_TO_HANDLE_MAP
    variable VLAN_OUTER_TO_HANDLE_MAP
    variable NUM_SESSIONS
    
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
        
		switch $userArgsArray(ip_version) {
		    "ipv4" {
                set ipVersion "ipv4"
                set topif "Ipv4If"
                set ifCount "1"
			}
		    "ipv6" {
                set ipVersion "ipv6"
                set topif "Ipv6If"
                set ifCount "1"
			}		
		    "ipv4_6" {
                set ipVersion "ipv4_6"
                set topif "Ipv4If Ipv6If"
                set ifCount "1 1"
			}		
		    "none" {
                set ipVersion ""
                set topif ""
                set ifCount ""
			}		
		}
        
        #####
        # Note:
        # Current stc 802.1x emulation could not send out vlan/qinq tagged packages even you configure vlan/qinq encapsulation.
        # To conquer this issue, we shall use DBD (device behind device) mechanism by creating an additional device between the 802.1x emulation and the DUT.
        # Topology:
        #     [802.1x device]---[tagged device w/ vlan/qinq encap]---[DUT]
        #            (vlan switch link)
        #####
        
        # create encapsulation stack by -encapsulation
        set encap $userArgsArray(encapsulation)
        
        switch -- $encap {
            "ethernet_ii" {
                set l2If "EthIIIf"
                set IfStack "$topif EthIIIf"
                set IfCount "$ifCount 1"
            }
            "ethernet_ii_vlan" -
            "ethernet_ii_qinq" {
                set l2If "vlanIf"
                set IfStack "$topif VlanIf EthIIIf"
                set IfCount "$ifCount 1 1"
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -encap $encap" {}
                return -code error $returnKeyedList  
            }
            
        }
        
        set deviceList ""
        
        # create dot1x device, the L2 layer is fixed to be "ethernet"
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack "$topif EthIIIf" -IfCount "$ifCount 1" -Port $portHandle]
                            set dot1xDevice $DeviceCreateOutput(-ReturnList)
        set ENCAP($dot1xDevice) $encap
        lappend deviceList $dot1xDevice
        
        # config device count
        set NUM_SESSIONS($dot1xDevice) $userArgsArray(num_sessions)
        ::sth::sthCore::invoke stc::config $dot1xDevice "-DeviceCount $NUM_SESSIONS($dot1xDevice)"
        
        set taggedDevice ""
        set thirdDevice ""
        # create an second device and use DBD mechanism for 802.1x vlan
        if {$encap == "ethernet_ii_vlan" || $encap == "ethernet_ii_qinq"} {
            # create the vlan/qinq tagged device for vlan or qinq encapsulation
            array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set taggedDevice $DeviceCreateOutput(-ReturnList)
            
            lappend deviceList $taggedDevice
            set ENCAP($taggedDevice) $encap
            set VLAN_INNER_TO_HANDLE_MAP($encap) $taggedDevice 
            
            # config device count for the extral device
            set NUM_SESSIONS($taggedDevice) $userArgsArray(num_sessions)
            ::sth::sthCore::invoke stc::config $taggedDevice "-DeviceCount $NUM_SESSIONS($taggedDevice)"
            
            ################################
            # establish "Vlan Switch Link" #
            ################################
                            
            set vlanLink [::sth::sthCore::invoke stc::create VlanSwitchLink -under $dot1xDevice]
            #VlanSwitchLink  "-LinkType {VLAN Switch Link}" (read-only)
            
            ::sth::sthCore::invoke stc::config $dot1xDevice "-ContainedLink-targets $vlanLink"
            
            ::sth::sthCore::invoke stc::config $vlanLink "-LinkDstDevice-targets $taggedDevice"
            
            set ethIf [::sth::sthCore::invoke stc::get $dot1xDevice -children-ethiiif]
            set vlanIf [::sth::sthCore::invoke stc::get $taggedDevice -children-vlanif]
            if {[llength $vlanIf] > 1} {
                set vlanIf [lindex $vlanIf 1]
            }
            ::sth::sthCore::invoke stc::config $vlanLink "-LinkSrc-targets $ethIf -LinkDst-targets $vlanIf"
        }
        
        # create the third device and use DBD mechanism twice for 802.1x qinq
        if {$encap == "ethernet_ii_qinq"} {
            # create the vlan tagged for the third device
            array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set thirdDevice $DeviceCreateOutput(-ReturnList)
            
            lappend deviceList $thirdDevice
            set ENCAP($thirdDevice) $encap
            set VLAN_OUTER_TO_HANDLE_MAP($encap) $thirdDevice 

            # config device count for the extral device
            set NUM_SESSIONS($thirdDevice) $userArgsArray(num_sessions)
            ::sth::sthCore::invoke stc::config $thirdDevice "-DeviceCount $NUM_SESSIONS($thirdDevice)"
            
            ################################
            # establish "Vlan Switch Link" #
            ################################
                            
            set vlanLink [::sth::sthCore::invoke stc::create VlanSwitchLink -under $taggedDevice]
            
            ::sth::sthCore::invoke stc::config $taggedDevice "-ContainedLink-targets $vlanLink"
            
            ::sth::sthCore::invoke stc::config $vlanLink "-LinkDstDevice-targets $thirdDevice"
            
            set ethIf [::sth::sthCore::invoke stc::get $taggedDevice -children-ethiiif]
            set vlanIf [::sth::sthCore::invoke stc::get $thirdDevice -children-vlanif]
            if {[llength $vlanIf] > 1} {
                set vlanIf [lindex $vlanIf 1]
            }
            ::sth::sthCore::invoke stc::config $vlanLink "-LinkSrc-targets $ethIf -LinkDst-targets $vlanIf"
        }
        
        
        # adjust link local interface for ipv6 case
        if {[string match -nocase "ipv6" $ipVersion]} {
                     
            #### ipv6 encap stack map ####
            #
            #            'toplevelIf'           UsesIf
            #         emulateddevice1 -----> ipv6if1  <------- Dot1xSupplicantBlockConfig
            #              |                    |
            # 'toplevelIf' |                    |
            # 'PrimaryIf'  |                    |
            #              |                    |
            #   ipv6if2(linklocal)--------> vlanIf1 ---> vlanIf2 ---> ethIIIf1
            #
            #
            ####
            #  link local ipv6 interface faces to the DUT
            #  global ipv6 interface faces to Dot1xSupplicantBlockConfig
            ####
            
            foreach device $deviceList {
                set ipv6If [::sth::sthCore::invoke stc::get $device -children-ipv6if]
                set lowerIf [::sth::sthCore::invoke stc::get $ipv6If -StackedOnEndpoint-targets]

                # create new ipv6if
                set cfglist "-Address fe80::1 -AddrStep ::1 -PrefixLength 64"
                set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $device "$cfglist -toplevelIf-sources $dot1xDevice -StackedOnEndpoint-targets $lowerIf"]
                ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
                ::sth::sthCore::invoke stc::config $device "-primaryif-targets $linkLocalIf"
            }
        }
        if {[string match -nocase "ipv4_6" $ipVersion]} {

            foreach device $deviceList {
                set toplevelIf ""
                set linkLocalIf ""
                set ipv6If [::sth::sthCore::invoke stc::get $device -children-ipv6if]
                set ipv4If [::sth::sthCore::invoke stc::get $device -children-ipv4if]
                set lowerIf [::sth::sthCore::invoke stc::get $ipv6If -StackedOnEndpoint-targets]

                # create new ipv6if
                set cfglist "-Address fe80::1 -AddrStep ::1 -PrefixLength 64"
                set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $device "$cfglist -toplevelIf-sources $dot1xDevice -StackedOnEndpoint-targets $lowerIf"]
                set toplevelIf [concat $toplevelIf $ipv6If $linkLocalIf]
                set toplevelIf [concat $ipv4If $toplevelIf]
                ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
                ::sth::sthCore::invoke stc::config $device "-primaryif-targets $linkLocalIf"
                ::sth::sthCore::invoke stc::config $device -toplevelIf-targets $toplevelIf
            }
        }
        # config device name
        if {[info exists userArgsArray(name)]} {
            ::sth::sthCore::invoke stc::config $dot1xDevice "-Name $userArgsArray(name)"
        }
        
        ####
        # A fixed "UsesIf" relation between Dot1xSupplicantBlockConfig and EthernetII should be established because 802.1x is an ethernet access control
        # and authentication protocol. (this relation is designed to be fixed by stc bll)
        ####
        
        set ipStack [::sth::sthCore::invoke stc::get $dot1xDevice -children-ethiiif]
        
        # Create Dot1xSupplicantBlockConfig
        set dot1xConfig [::sth::sthCore::invoke stc::create Dot1xSupplicantBlockConfig -under $dot1xDevice "-UsesIf-targets $ipStack"]
                
        #### Config input switches ####
        ::sth::Dot1x::processConfigSwitches $dot1xDevice create $ipVersion returnKeyedList
        
        # create result dataset and resultquery for subscribing dot1x result objects
        if {$::sth::Dot1x::dot1x_subscription_state == 0} {
            set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            # device level results - Dot1xSupplicantBlockConfig result children
            set resultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xSupplicantBlockConfig -ResultClassId Dot1xSupplicantAuthResults"]
            set resultQuery2 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xSupplicantBlockConfig -ResultClassId Dot1xEapolResults"]
            set resultQuery3 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xSupplicantBlockConfig -ResultClassId Dot1xEapPktResults"]
            set resultQuery4 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xSupplicantBlockConfig -ResultClassId Dot1xEapMethodResults"]
            
            # port level results - Dot1xPortConfig result children
            set resultQuery5 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xPortConfig -ResultClassId Dot1xSupplicantAuthResults"]
            set resultQuery6 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xPortConfig -ResultClassId Dot1xEapolResults"]
            set resultQuery7 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xPortConfig -ResultClassId Dot1xEapPktResults"]
            set resultQuery8 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dot1xPortConfig -ResultClassId Dot1xEapMethodResults"]
        }
        
        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying Dot1x configuration: $err"
            return $returnKeyedList
        }
        
        if {$::sth::Dot1x::dot1x_subscription_state == 0} {
            #Subscribe to the datasets
            #result obj like Dot1xSupplicantAuthResults will be activated and be the children of Dot1xSupplicantBlockConfig/Dot1xPortConfig
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            set ::sth::Dot1x::dot1x_subscription_state 1
        }
        
        
    } returnedString]
    
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any device created if error occurs
        if {[info exists deviceList]} {
            foreach device $deviceList {
                ::sth::sthCore::invoke stc::delete $device
            }
        }
    } else {
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList handle $dot1xDevice 
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}

proc ::sth::Dot1x::emulation_dot1x_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dot1x_config_modify"

    variable ::sth::Dot1x::userArgsArray
    variable ::sth::Dot1x::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ENCAP
    variable VLAN_INNER_TO_HANDLE_MAP
    variable VLAN_OUTER_TO_HANDLE_MAP
    
    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set deviceHandleList $userArgsArray(handle)
            if {![IsDot1xHandleValid $deviceHandleList]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandleList is not valid dot1x device handle" {}
                return -code error $returnKeyedList 
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        array set newArgsArray ""
        # checking unsupported switches under "modify" mode
        set unsupportedModifyOptions {port_handle encapsulation ip_version}
        
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                    ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
                }
                set newArgsArray($switchname) $userArgsArray($switchname)
            }
        }
        array unset ::sth::Dot1x::userArgsArray
        array set ::sth::Dot1x::userArgsArray {}
        #foreach arr [array names newArgsArray] {
        #    set userArgsArray($arr) $newArgsArray($arr)
        #}
        array set userArgsArray [array get newArgsArray]
  
        # modify input arguments
        foreach deviceHandle $deviceHandleList {
            
            # modify device name
            if {[info exists userArgsArray(name)]} {
                ::sth::sthCore::invoke stc::config $deviceHandle "-Name $userArgsArray(name)"
            }
            
            # modify device count
            if {[info exists userArgsArray(num_sessions)]} {
                set NUM_SESSIONS($deviceHandle) $userArgsArray(num_sessions)
                ::sth::sthCore::invoke stc::config $deviceHandle "-DeviceCount $userArgsArray(num_sessions)"
                
                set encap $ENCAP($deviceHandle)
                if {$encap == "ethernet_ii_vlan"} {
                    set NUM_SESSIONS($VLAN_INNER_TO_HANDLE_MAP($encap)) $userArgsArray(num_sessions)
                    ::sth::sthCore::invoke stc::config $VLAN_INNER_TO_HANDLE_MAP($encap) "-DeviceCount $userArgsArray(num_sessions)"
                } elseif {$encap == "ethernet_ii_qinq"} {
                    set NUM_SESSIONS($VLAN_INNER_TO_HANDLE_MAP($encap)) $userArgsArray(num_sessions)
                    set NUM_SESSIONS($VLAN_OUTER_TO_HANDLE_MAP($encap)) $userArgsArray(num_sessions)
                    ::sth::sthCore::invoke stc::config $VLAN_INNER_TO_HANDLE_MAP($encap) "-DeviceCount $userArgsArray(num_sessions)"
                    ::sth::sthCore::invoke stc::config $VLAN_OUTER_TO_HANDLE_MAP($encap) "-DeviceCount $userArgsArray(num_sessions)"
                }
            }
            
            set childList [::sth::sthCore::invoke stc::get $deviceHandle -children]

            if {[regexp -- "ipv4if" $childList] && [regexp -- "ipv6if" $childList]} {
                set ipVersion "ipv4_6"
            } elseif {[regexp -- "ipv4f" $childList]} {
                set ipVersion "ipv4"
            } elseif {[regexp -- "ipv6if" $childList]} {
                set ipVersion "ipv6"
            } else {
                set ipVersion "none"
            }
            ::sth::Dot1x::processConfigSwitches $deviceHandle modify $ipVersion returnKeyedList  
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

proc ::sth::Dot1x::emulation_dot1x_config_delete { returnKeyedListVarName } {
    
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
            if {![IsDot1xHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid Dot1x handle" {}
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

proc ::sth::Dot1x::processConfigSwitches {handleList mode ipVersion returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Dot1x::sortedSwitchPriorityList
    variable ::sth::Dot1x::userArgsArray
    upvar $returnList returnKeyedList
    variable ENCAP
    variable VLAN_INNER_TO_HANDLE_MAP
    variable VLAN_OUTER_TO_HANDLE_MAP
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_config $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_config $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Dot1x:: emulation_dot1x_config $switchname $mode]
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
                        configEthIIIntf $ethiiIf $mode
                    }
                }
                configVlanIfInner {
                    set encap $ENCAP($deviceHandle)
                    if {$encap == "ethernet_ii_vlan" || $encap == "ethernet_ii_qinq"} {
                        
                        set handle $VLAN_INNER_TO_HANDLE_MAP($encap)
                        
                        set vlanIf [::sth::sthCore::invoke stc::get $handle -children-VlanIf]
                        #
                        #if {[llength $vlanIf] != 0} {
                        #    if {[llength $vlanIf] > 1} {
                        #        set vlanIf [lindex $vlanIf 0]
                        #    }
                        #    configVlanIfInner $vlanIf $mode
                        #}
                        configVlanIfInner $vlanIf $mode
                    }
                }
                configVlanIfOuter {
                    set encap $ENCAP($deviceHandle)
                    if {$encap == "ethernet_ii_qinq"} {
                        
                        set handle $VLAN_OUTER_TO_HANDLE_MAP($encap)
                        
                        set vlanIf [::sth::sthCore::invoke stc::get $handle -children-VlanIf]
                        #if {[llength $vlanIf] != 0} {
                        #    if {[llength $vlanIf] < 2} {continue}
                        #    set vlanIf [lindex $vlanIf 1]
                        #    configVlanIfOuter $vlanIf $mode
                        #}
                        configVlanIfOuter $vlanIf $mode
                    }
                }

                configIpv4Intf {
 
                    set ipIf [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv4if]
                    if {[llength $ipIf] != 0} {
                        set ipIf [lindex $ipIf 0]
                    }
                    configIpv4Intf $ipIf $mode
                }
                configIpv6Intf {

                    set ipIf [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv6if]
                    if {[llength $ipIf] != 0} {
                        set ipIf [lindex $ipIf 0]
                    }
                    configIpv6Intf $ipIf $mode
                }

                configDot1xPortConfig {
                    set port [::sth::sthCore::invoke stc::get $deviceHandle -AffiliationPort-targets]
                    set dot1xPortCfg [::sth::sthCore::invoke stc::get $port -children-Dot1xPortConfig]
                    configDot1xPortConfig $dot1xPortCfg $mode
                }
                configDot1xSupplicantConfig {
                    set port [::sth::sthCore::invoke stc::get $deviceHandle -AffiliationPort-targets]
                    set dot1xClockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dot1xSupplicantBlockConfig]
                    configDot1xSupplicantConfig $dot1xClockCfg $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
}

proc ::sth::Dot1x::configDot1xSupplicantConfig { dot1xCfg mode } {
    
    set optionValueList [getStcOptionValueList emulation_dot1x_config configDot1xSupplicantConfig $mode $dot1xCfg]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dot1xCfg $optionValueList
    }
}

proc ::sth::Dot1x::configDot1xPortConfig { dot1xPortCfg mode } {
    
    set optionValueList [getStcOptionValueList emulation_dot1x_config configDot1xPortConfig $mode $dot1xPortCfg]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dot1xPortCfg $optionValueList
    }
}

proc ::sth::Dot1x::configEthIIIntf { ethHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dot1x_config configEthIIIntf $mode $ethHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::Dot1x::configVlanIfInner { vlanHandle mode } {
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    set optionValueList [getStcOptionValueList emulation_dot1x_config configVlanIfInner $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Dot1x::configVlanIfOuter { vlanHandle mode } {
        
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    set optionValueList [getStcOptionValueList emulation_dot1x_config configVlanIfOuter $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Dot1x::configIpv4Intf { ipIfHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dot1x_config configIpv4Intf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}
proc ::sth::Dot1x::configIpv6Intf { ipIfHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dot1x_config configIpv6Intf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}



proc ::sth::Dot1x::processConfigFwdCmd { handle myswitch value } {

    # get forward map for "constant" property 
    set fwdValue [::sth::sthCore::getFwdmap ::sth::Dot1x:: emulation_dot1x_config $myswitch $value]
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_config $myswitch stcattr]
    
    return "-$stcAttr $fwdValue"
}

proc ::sth::Dot1x::processConfigCmd_qinqIncrMode { handle myswitch value } {
    variable sortedSwitchPriorityList
    variable VLANS
    variable ENCAP
    variable HANDLE_TO_QINQ_MODE_MAP
    variable VLAN_INNER_TO_HANDLE_MAP
    variable VLAN_OUTER_TO_HANDLE_MAP
    
    set HANDLE_TO_QINQ_MODE_MAP($handle) $value
    set target_handle [::sth::sthCore::invoke stc::get [stc::get $handle -linkdstdevice-Sources] -containedlink-Sources]
    set HANDLE_TO_QINQ_MODE_MAP($target_handle) $value
    set encap $ENCAP($handle)
    
    foreach opt {vlan_id_step vlan_id_count vlan_outer_id_step vlan_outer_id_count} {
        if {![info exists VLANS($opt)] && [info exists userArgsArray($opt)] } {
            #set [string trim $opt "vlan_"] $userArgsArray($opt)
            set VLANS($opt) $userArgsArray($opt)
        } 
    }
    
    # inner vlan
    if {![info exists userArgsArray(vlan_id)]} {
        set vlanIf [::sth::sthCore::invoke stc::get $VLAN_INNER_TO_HANDLE_MAP($encap) -children-vlanif]
        set vlan_id [::sth::sthCore::invoke stc::get $vlanIf -vlanId]
        set vlanInnerCfg [processConfigCmd_vlanId $VLAN_INNER_TO_HANDLE_MAP($encap) vlan_id $vlan_id]
        ::sth::sthCore::invoke stc::config $vlanIf "$vlanInnerCfg"
    }
    if {![info exists userArgsArray(vlan_outer_id)]} {
        # outer vlan
        set outerVlanIf [::sth::sthCore::invoke stc::get $VLAN_OUTER_TO_HANDLE_MAP($encap) -children-vlanif]
        set outer_vlan_id [::sth::sthCore::invoke stc::get $outerVlanIf -vlanId]
        set vlanOuterCfg [processConfigCmd_vlanId $VLAN_OUTER_TO_HANDLE_MAP($encap) vlan_outer_id $outer_vlan_id]
        ::sth::sthCore::invoke stc::config $outerVlanIf "$vlanOuterCfg"
    }
}

proc ::sth::Dot1x::processConfigCmd_vlanId { handle myswitch value } {
    variable userArgsArray
    variable ENCAP
    variable VLANS
    variable HANDLE_TO_QINQ_MODE_MAP
    variable NUM_SESSIONS

    if {![info exists HANDLE_TO_QINQ_MODE_MAP($handle)]} {
        if {[info exists userArgsArray(qinq_incr_mode)]} {
            set HANDLE_TO_QINQ_MODE_MAP($handle) $userArgsArray(qinq_incr_mode)
        } else {
            set HANDLE_TO_QINQ_MODE_MAP($handle) "both"
        }
    }
    
    foreach opt {vlan_id_step vlan_id_count vlan_outer_id_step vlan_outer_id_count} {
        if {![info exists VLANS($opt)] && [info exists userArgsArray($opt)] } {
            set VLANS($opt) $userArgsArray($opt)
        } 
    }
    
    set encap $ENCAP($handle)
    if {$myswitch == "vlan_id"} {
        if {[expr $NUM_SESSIONS($handle)%$VLANS(vlan_id_count)] != 0} {
            ::sth::sthCore::processError returnKeyedList "Error: The value of -num_sessions should be devided by -vlan_id_count" {}
            return -code error $returnKeyedList 
        }
        # fix the bug: Interface VlanIf has invalid effective block size for current value of Interface Count and IdRepeatCount
        # set -IdRepeatCount to 0
        if {$encap == "ethernet_ii_qinq"} {
            switch -exact -- $HANDLE_TO_QINQ_MODE_MAP($handle) {
                "inner" {
                    lappend vlanCfg -IdRepeatCount 0 -IfRecycleCount $VLANS(vlan_id_count)
                }
                "outer" {
                    set repeat_count ""
                    set repeat_count [expr $VLANS(vlan_outer_id_count)-1]
                    lappend vlanCfg -IdRepeatCount $repeat_count -IfRecycleCount 0
                }
                "both" {
                    lappend vlanCfg -IdRepeatCount 0 -IfRecycleCount $VLANS(vlan_id_count)
                }
            }
        } elseif {$encap == "ethernet_ii_vlan"} {
            lappend vlanCfg -IfRecycleCount $VLANS(vlan_id_count)
        }
        
        lappend vlanCfg -VlanId $value
        
    } elseif {$myswitch == "vlan_outer_id"} {
        
        if {$encap != "ethernet_ii_qinq"} { return }
        
        if {[expr $NUM_SESSIONS($handle)%$VLANS(vlan_outer_id_count)] != 0} {
            ::sth::sthCore::processError returnKeyedList "Error: The value of -num_sessions should be devided by -vlan_outer_id_count" {}
            return -code error $returnKeyedList 
        }
        if {[expr $NUM_SESSIONS($handle)%$VLANS(vlan_id_count)] != 0} {
            ::sth::sthCore::processError returnKeyedList "Error: The value of -num_sessions should be devided by -vlan_id_count" {}
            return -code error $returnKeyedList 
        }
        switch -exact -- $HANDLE_TO_QINQ_MODE_MAP($handle) {
            "inner" {
                set repeat_count ""
                set repeat_count [expr $VLANS(vlan_id_count)-1]
                lappend vlanCfg -IdRepeatCount $repeat_count -IfRecycleCount 0
            }
            "outer" {
               lappend vlanCfg -IdRepeatCount 0 -IfRecycleCount $VLANS(vlan_outer_id_count)
            }
            "both" {
                lappend vlanCfg -IdRepeatCount 0 -IfRecycleCount $VLANS(vlan_outer_id_count)
            }
        }

        lappend vlanCfg -VlanId $value
    }

    return $vlanCfg
}

proc ::sth::Dot1x::processConfigCmd_auth { handle myswitch value } {
    
    variable userArgsArray
    
    if {[info exists userArgsArray(eap_auth_method)]} {
        set eap $userArgsArray(eap_auth_method)
        set eapObj "Dot1xEap${eap}Config"
        
        set eapCfg [::sth::sthCore::invoke stc::get $handle -children]
        set eapCfgList ""
        foreach eap $eapCfg {
            if {![regexp -nocase "results" $eap]} {
                lappend eapCfgList $eap
            }
        }
        set eapConfig [::sth::sthCore::invoke stc::get $handle -children-$eapObj]
        if {[llength $eapConfig] == 0} {
            set eapConfig [::sth::sthCore::invoke stc::create $eapObj -under $handle]
            lappend eapCfgList $eapConfig
        }
    } else {
	     set eapCfgList ""
	     set eap [::sth::sthCore::invoke stc::get $handle -EapAuthMethod]
	     set eapObj "Dot1xEap${eap}Config"
         set eapConfig [::sth::sthCore::invoke stc::get $handle -children-$eapObj]
         lappend eapCfgList $eapConfig    
	}

    # config certificate/key file
    if {$myswitch == "eap_auth_method"} {
        if {[regexp -- "fast" $userArgsArray(eap_auth_method)]} {
            ::sth::sthCore::invoke stc::config $handle "-EapAuthMethod $userArgsArray(eap_auth_method)"
            if {[info exists userArgsArray(pac_key_file)]} {
                set config [processConfigCmd_wildcard pac_key_file]
                ::sth::sthCore::invoke stc::config $eapConfig "-PacKeyFileName $config"
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: PAC file name -pac_key_file shall NOT be empty" {}
                return -code error $returnKeyedList  
            }
        } elseif {[regexp -- "tls" $userArgsArray(eap_auth_method)]} {
            ::sth::sthCore::invoke stc::config $handle "-EapAuthMethod $userArgsArray(eap_auth_method)"
            if {[info exists userArgsArray(certificate)]} {
                set config [processConfigCmd_wildcard certificate]
                ::sth::sthCore::invoke stc::config $eapConfig "-Certificate $config"
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: certificate file name -certificate shall NOT be empty" {}
                return -code error $returnKeyedList  
            }
        }
    } elseif {$myswitch == "username"} {
        set config [processConfigCmd_wildcard $myswitch]
        foreach authCfg $eapCfgList {
            ::sth::sthCore::invoke stc::config $authCfg "-UserId $config"
        }
    } elseif {$myswitch == "password"} {
        set config [processConfigCmd_wildcard $myswitch]
        foreach authCfg $eapCfgList {
            ::sth::sthCore::invoke stc::config $authCfg "-Password $config"
        }
    }
    
    set null ""
    return $null
}

# Handle the username/password/certificate/pac_key_file wildcards
proc ::sth::Dot1x::processConfigCmd_wildcard { myswitch } {
    variable userArgsArray
    
    #password_wildcard
    #username_wildcard
    #pac_key_wildcard
    #certificate_wildcard
    #wildcard_question_start
    #wildcard_question_end
    #wildcard_question_fill
    #wildcard_pound_start
    #wildcard_pound_end
    #wildcard_pound_fill

    set configList ""
    if {![info exists userArgsArray(${myswitch}_wildcard)] || !$userArgsArray(${myswitch}_wildcard)} {
        lappend configList $userArgsArray($myswitch)
        return $configList
    } 

    # Calculate the start/end for 4 marker characters
    foreach marker {question pound} {
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
        if {[info exists userArgsArray($myswitch)]} {
            set attrValue $userArgsArray($myswitch)
        }
        foreach pair {{# pound} {? question}} {
            foreach {symbol marker} $pair {};
            regsub -all \\$symbol $attrValue [set ${marker}_string] attrValue
        }
        lappend configList $attrValue
    }

    return $configList
}

##
#  common errors for certificate file
#    1, "Bad TLS client certificates", reason1 - bad format of the certificate file, reason2 - bad password for the certificate file
#    2, "TLS client certificates not exist", reason - certificate file is not downloaded to the port
##

proc ::sth::Dot1x::emulation_dot1x_control_download { returnKeyedListVarName } {
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(certificate_dir)]} {
            ::sth::sthCore::processError returnKeyedList "Error: switch -certificate_dir is necessary for -action download." {}
            return -code error $returnKeyedList  
        }

        set certDir $userArgsArray(certificate_dir)
        set portHndList $userArgsArray(port_handle)

        ::sth::sthCore::invoke stc::perform Dot1xDownloadCertificate -CertificateDir $certDir -ObjectList $portHndList
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $returnKeyedList
}


proc ::sth::Dot1x::emulation_dot1x_control_delete_all { returnKeyedListVarName } {
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {

        set portHndList $userArgsArray(port_handle)

        ::sth::sthCore::invoke stc::perform Dot1xDeleteAllCertificate -ObjectList $portHndList
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $returnKeyedList
}


proc ::sth::Dot1x::emulation_dot1x_stats { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        
        set deviceHandleList ""
        array set portAgg ""
            
        if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
            foreach handle $userArgsArray(handle) {
                if {![::sth::Dot1x::IsDot1xHandleValid $handle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $handle is not valid Dot1x handle" {}
                    return -code error $returnKeyedList
                }
                lappend deviceHandleList $handle
            }
                    
        } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
            foreach port $userArgsArray(port_handle) {
                set portAgg($port) 0
                if {[::sth::sthCore::IsPortValid $port err]} {
                    set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                foreach device $deviceHandle {
                    if {![::sth::Dot1x::IsDot1xHandleValid $device]} { continue }
                    lappend deviceHandleList $device
                }
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                    return -code error $returnKeyedList
                }
            }
        }
        
        foreach device $deviceHandleList {
            set dot1xClockCfg [::sth::sthCore::invoke stc::get $device -children-Dot1xSupplicantBlockConfig]
            
            # get 802.1x device level result obj
            set authResult1 [::sth::sthCore::invoke stc::get $dot1xClockCfg -children-Dot1xSupplicantAuthResults]
            set eapolResult1 [::sth::sthCore::invoke stc::get $dot1xClockCfg -children-Dot1xEapolResults]
            set eapPktResult1 [::sth::sthCore::invoke stc::get $dot1xClockCfg -children-Dot1xEapPktResults]
            set methodResult1 [::sth::sthCore::invoke stc::get $dot1xClockCfg -children-Dot1xEapMethodResults]
            
            # get 802.1x port level result obj
            set port [::sth::sthCore::invoke stc::get $device -AffiliationPort-targets]
            
            set dot1xPortCfg [::sth::sthCore::invoke stc::get $port -children-Dot1xPortConfig]

            set authResult2 [::sth::sthCore::invoke stc::get $dot1xPortCfg -children-Dot1xSupplicantAuthResults]
            set eapolResult2 [::sth::sthCore::invoke stc::get $dot1xPortCfg -children-Dot1xEapolResults]
            set eapPktResult2 [::sth::sthCore::invoke stc::get $dot1xPortCfg -children-Dot1xEapPktResults]
            set methodResult2 [::sth::sthCore::invoke stc::get $dot1xPortCfg -children-Dot1xEapMethodResults]
    
            # create an array mapping between stcObj and stcHandle
            set hdlArray1(Dot1xSupplicantAuthResults) $authResult1
            set hdlArray1(Dot1xEapolResults) $eapolResult1
            set hdlArray1(Dot1xEapPktResults) $eapPktResult1
            set hdlArray1(Dot1xEapMethodResults) $methodResult1
            
            set hdlArray2(Dot1xSupplicantAuthResults) $authResult2
            set hdlArray2(Dot1xEapolResults) $eapolResult2
            set hdlArray2(Dot1xEapPktResults) $eapPktResult2
            set hdlArray2(Dot1xEapMethodResults) $methodResult2
            
            set mode $userArgsArray(mode)
            
            if {$mode == "aggregate"} {
                if {[info exists portAgg($port)] && $portAgg($port) == 1} {
                    continue
                } else {
                    set portAgg($port) 1
                }
            }
            
            if {$mode == "session"} {
                set state [eval processDot1xGetCmd_state $device $mode]
                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "session.$device.authentication_state" $state]
            }
            #else {
            #    set state [eval processDot1xGetCmd_state $port $mode]
            #    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "aggregate.$port.authentication_state" $state]
            #}
            
            foreach key [array names ::sth::Dot1x::emulation_dot1x_stats_mode] {
                foreach {tblMode tblProc} $::sth::Dot1x::emulation_dot1x_stats_mode($key) {
                    if {[string match $tblMode $mode]} {
                        
                        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_stats $key supported] "false"]} {
                            continue
                        }
                        if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_stats $key stcattr]] "_none_"]} {
                            continue
                        }
                            
                        if {$tblMode == "session"} {
                            
                            if {[catch {set stcObj [::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_stats $key stcobj]} err]} {
                                ::sth::sthCore::processError returnKeyedList "emulation_dot1x_stats $key Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set obj $hdlArray1($stcObj)
                            set val [::sth::sthCore::invoke stc::get $obj -$stcAttr]
                            
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "session.$device.$key" $val]
                            
                        } elseif {$tblMode == "aggregate"} {
                            
                            if {[catch {set stcObj [::sth::sthCore::getswitchprop ::sth::Dot1x:: emulation_dot1x_stats $key stcobj]} err]} {
                                ::sth::sthCore::processError returnKeyedList "emulation_dot1x_stats $key Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set obj $hdlArray2($stcObj)
                            if {![regexp "^$" $obj]} {
                                set val [::sth::sthCore::invoke stc::get $obj -$stcAttr]
                                
                                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "aggregate.$port.$key" $val]
                            }
                            
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

#####
# Note:
# STC 802.1x does not provide aggregate port state directly, hltapi determines the aggregate state based on the session state
#####
proc ::sth::Dot1x::processDot1xGetCmd_state { handle mode} {
    
    if {$mode == "aggregate"} {
        set deviceHandle [::sth::sthCore::invoke stc::get $handle -affiliationport-sources]
        foreach device $deviceHandle {
            if {![::sth::Dot1x::IsDot1xHandleValid $device]} { continue }
            lappend deviceHandleList $device
        }
    } else {
        set deviceHandleList $handle
    }
    
    set state ""
    foreach hdl $deviceHandleList {
        set ptpConfig [::sth::sthCore::invoke stc::get $hdl -children-Dot1xSupplicantBlockConfig]
        set stateVal [::sth::sthCore::invoke stc::get $ptpConfig -AuthState]

        switch -glob -- $stateVal {
            "UNAUTHORIZED*" {
                lappend state unauthorized
            }
            "AUTHENTICATING*" {
                lappend state authenticating
            }
            "REAUTHENTICATING*" {
                lappend state reauthenticating
            }
            "AUTH_SUCCESS*" {
                lappend state authenticated
            }
            "AUTH_FAILED*" {
                lappend state authentication_failed
            }
            "LOGGING_OFF*" {
                lappend state logging_off
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Could not resolve state: $stateVal"
                return -code error $returnKeyedList
            }
        }
    }
    
    #if {$mode == "aggregate"} {
    #    # unauthorized: 
    #    # authenticating:    At least one host block is in the process of authenticating
    #    # reauthenticating:  At least one host block is in the process of reauthenticating
    #    # authenticated:     All host blocks are authenticated. 
    #    # authentication_failed:  At least Supplicants were not authenticated successfully
    #    # logging_off:      
    #
    #    if {[lsearch $state ]} {
    #        
    #    }
    #}

    return $state
}
      

proc ::sth::Dot1x::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::Dot1x::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Dot1x:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dot1x:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Dot1x:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::Dot1x::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::Dot1x::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Dot1x:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dot1x:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Dot1x:: $cmdType $opt $::sth::Dot1x::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::Dot1x::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Dot1x::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}

proc ::sth::Dot1x::IsDot1xHandleValid { handle } {
    
    set cmdStatus 0
    set port [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
    
    if {[catch {set deviceHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} err]} {
        ::sth::sthCore::processError returnKeyedList "No device exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return -code error $returnKeyedList 
    } else {
	foreach deviceHandle $deviceHandleList {
	    if {[string equal $deviceHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}

	if {[catch {set ptpClockConfig [::sth::sthCore::invoke stc::get $deviceHandle -children-Dot1xSupplicantBlockConfig]} err]} {
	    set cmdStatus 0
	}
        if {[string length $ptpClockConfig] == 0} {
            set cmdStatus 0
        }
	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid dot1x handle"
	    return $::sth::sthCore::FAILURE		
	}		
    }
}

proc ::sth::Dot1x::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::Dot1x:: $cmdType $switchName dependency]] "_none_"]} {
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
