# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/pppoxFunctions.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

###/*! \file pppoxFunctions.tcl
###    \brief Sub Commands for PPPOX
###
###    This file contains the sub commands for Pppox Api which will execute the pppoe commands. This sub commands will be directly at the next level of the main command.
###*/


###/*! \namespace Pppox
###\brief Pppox Api
###
###This namespace contains the implementation for the Pppox Api

###*/
### namespace Pppoe {
namespace eval ::sth::Pppox:: {

###/*! \var PPPOEPORT2PORTHNDLMAP
### \brief Global List of PPPoE hltPortList
###
###This list holds the port handles
###
###*/
### array PPPOEPORT2PORTHNDLMAP;

        array set PPPOEPORT2PORTHNDLMAP {}

###/*! \var PPPOEPORT2SESSIONBLOCKHNDLMAP
### \brief Global Array for hltPortList and PppoeSessions
###
###This array holds the handles for the PPPOESessionBlock for a particular port
###
###*/
### array PPPOEPORT2SESSIONBLOCKHNDLMAP;

        array set PPPOEPORT2SESSIONBLOCKHNDLMAP {}

###/*! \var PPPOEPORTHNDL2PORTMAP
### \brief Global List of PPPoE hltPortList
###
###This list holds the port handles
###
###*/
### array PPPOEPORTHNDL2PORTMAP;

        array set PPPOEPORTHNDL2PORTMAP {}

###/*! \var PPPOESESSIONBLOCKHNDL2PORTMAP
### \brief Global Array for PPPOESessions
###
###This array holds the PPPOESessionHandle
###
###*/
###array PPPOESESSIONBLOCKHNDL2PORTMAP;
        array set PPPOESESSIONBLOCKHNDL2PORTMAP {}

       # For pppoe, session block handle/result is PppoeClientBlockConfig/PppoeClientBlockResults
       # For pppoa, session block handle/result is PppoaClientBlockConfig/PppoaClientBlockResults
       # added by xiaozhi
       array set PPPOXCLIENTROBJTYPE {}
###/*! \ingroup pppoeswitchprocfuncs
###\fn pppox_config_create (str args)
###\brief Process \em -mode switch with value \em enable for pppox_config cmd
###
###This procedure execute the pppox_config command when the mode is create. It will create pppoe sessions based on the \em -count switch.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with pppoe handles
###
###
###\author Alison Lee (all)
###*/
###
###pppox_config_create (str args);
###
proc ::sth::Pppox::pppox_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray

    set _OrigHltCmdName "pppox_config"
    set _hltCmdName "pppox_config_create"

    upvar 1 $returnKeyedListVarName returnKeyedList

    set validateStep 1
    set stepError 0

    # Port_handle is mandatory for the -mode create
    if {![info exists userArgsArray(port_handle)]} {
        set result "The -port_handle is required when \"-mode create\" is used."
        #puts "DEBUG:$result"
        return -code 1 -errorcode -1 $result
    }
    set hltPort $userArgsArray(port_handle)


    set portConfigParamList ""
    set sessionBlockConfigParamList ""
    set globalConfigParamList ""
    unset userArgsArray(optional_args)
    unset userArgsArray(mandatory_args)

    ##
    # Create the Host
    ##
    
    foreach param { mac_addr mac_addr_step protocol pvc_incr_mode vci vpi vci_step vpi_step vci_count vpi_count ip_cp encap qinq_oneblock vlan_id vlan_tpid vlan_id_step vlan_id_count vlan_user_priority vlan_cfi vlan_id_outer vlan_tpid_outer vlan_id_outer_step vlan_id_outer_count  vlan_outer_user_priority vlan_outer_cfi qinq_incr_mode num_sessions encap} {
           set $param $userArgsArray($param)
    }
    
    if {$ip_cp == "ipv4v6"} {
        set topif "Ipv6If"
        set IfCount "1"
    } elseif {$ip_cp == "ipv6"} {
        set topif "Ipv6If"
        set IfCount "1"
    } else {
        set topif "Ipv4If"
        set IfCount "1"
    }
    
    switch -exact -- $userArgsArray(protocol) {
            "pppoe" {
                if {$encap == "ethernet_ii_vlan"} {
                    set IfStack "$topif PppIf PppoeIf VlanIf EthIIIf"
                    set IfCount "$IfCount 1 1 1 1"
                } elseif {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
                    set IfStack "$topif PppIf PppoeIf VlanIf VlanIf EthIIIf"
                    set IfCount "$IfCount 1 1 1 1 1"
                } else {
                    set IfStack "$topif PppIf PppoeIf EthIIIf"
                    set IfCount "$IfCount 1 1 1"
                }
                set ::sth::Pppox::PPPOXCLIENTROBJTYPE($hltPort) "pppoe"
            }
            "pppoa" {
                set IfStack "$topif PppIf Aal5If"
                set IfCount "$IfCount 1 1"
                set ::sth::Pppox::PPPOXCLIENTROBJTYPE($hltPort) "pppoa"
            }
            "pppoeoa" {
                if {[regexp "ethernet_ii_vlan" $encap] } {
                    set IfStack "$topif PppIf PppoeIf VlanIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1 1"
                } elseif {[regexp "ethernet_ii_qinq" $encap] || [regexp "ethernet_ii_mvlan" $encap]} {
                    set IfStack "$topif PppIf PppoeIf VlanIf VlanIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1 1 1"
                } else {
                    set IfStack "$topif PppIf PppoeIf EthIIIf Aal5If"
                    set IfCount "$IfCount 1 1 1 1"
                }
                set ::sth::Pppox::PPPOXCLIENTROBJTYPE($hltPort) "pppoe"
            }
    }
    set PppoxClientBlockConfig [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($hltPort)]ClientBlockConfig
    set deviceCount $num_sessions


    if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host \
                                      -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle) -DeviceCount $deviceCount]
    } else {
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host \
                                      -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle) -CreateCount $deviceCount]
    }
    set createdHostList $DeviceCreateOutput(-ReturnList)
    #config IpIf
	set i 0
        set device_count [llength $createdHostList]
	foreach createdHost $createdHostList {
		array set ipv6Paramlist " intf_ipv6_addr address intf_ipv6_addr_step AddrStep gateway_ipv6_addr gateway gateway_ipv6_step GatewayStep"
		set ipv6Cfglist ""
		foreach param [array names ipv6Paramlist] {
			if {[info exists userArgsArray($param)]} {
                            set param_value $userArgsArray($param)
				if {$param == "intf_ipv6_addr"} {
					if {[info exists userArgsArray(intf_ipv6_addr_step)]} {
						set intf_ipv6_addr_step $userArgsArray(intf_ipv6_addr_step)
					} else {
						set intf_ipv6_addr_step ::1
					}
					set param_value [::sth::sthCore::updateIpAddress 6 $userArgsArray($param) $intf_ipv6_addr_step $i]
				}
				if {$param == "gateway_ipv6_addr"} {
					if {[info exists userArgsArray(gateway_ipv6_step)]} {
						set gateway_ipv6_step $userArgsArray(gateway_ipv6_step)
					} else {
						set gateway_ipv6_step ::1
					}
					set param_value [::sth::sthCore::updateIpAddress 6 $userArgsArray($param) $gateway_ipv6_step $i]
				}
				lappend ipv6Cfglist -$ipv6Paramlist($param) $param_value
			}
		}
		# US37424 Enhancement to support 8K devices in each of 4 vlans in HLTAPI
		array set ipv4Paramlist " intf_ip_addr address intf_ip_addr_step AddrStep gateway_ip_addr gateway gateway_ip_step GatewayStep stack_gateway_ip_recycle_count GatewayRecycleCount stack_gateway_ip_repeat_count GatewayRepeatCount"
		set ipv4Cfglist ""
		foreach param [array names ipv4Paramlist] {
			if {[info exists userArgsArray($param)]} {
                            set param_value $userArgsArray($param)
				if {$param == "intf_ip_addr"} {
					if {[info exists userArgsArray(intf_ip_addr_step)]} {
						set intf_ip_addr_step $userArgsArray(intf_ip_addr_step)
					} else {
						set intf_ip_addr_step 0.0.0.1
					}
					set param_value [::sth::sthCore::updateIpAddress 4 $userArgsArray($param) $intf_ip_addr_step $i]
				}
				if {$param == "gateway_ip_addr"} {
					if {[info exists userArgsArray(gateway_ip_step)]} {
						set gateway_ip_step $userArgsArray(gateway_ip_step)
					} else {
						set gateway_ip_step 0.0.0.1
					}
					set param_value [::sth::sthCore::updateIpAddress 4 $userArgsArray($param) $gateway_ip_step $i]
				}
				lappend ipv4Cfglist -$ipv4Paramlist($param) $param_value
			}
		}
		
		if {[set createdIpv6If [::sth::sthCore::invoke stc::get $createdHost "-children-ipv6if"]] != ""} {
			#Create and Config ipv6ifLocal
			set pppIf [::sth::sthCore::invoke stc::get $createdHost "-children-Pppif"]
			if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $createdHost -IfStack "Ipv6If" -IfCount "1" -AttachToIf $pppIf} err]} {
				::sth::sthCore::processError returnKeyedList "add locallink Ipv6If Failed: $err" {}
				return -code 1 -errorcode -1 $err
			}
			set ipv6ifList [::sth::sthCore::invoke stc::get $createdHost "-children-ipv6if"]
			set createdIpv6LocalIf [lindex $ipv6ifList 0]
			if {[info exists userArgsArray(local_ipv6_addr)]} {
				set addr $userArgsArray(local_ipv6_addr)
				::sth::sthCore::invoke stc::config $createdIpv6LocalIf "-Address $addr -Gateway ::"
			} else {
				set addr "FE80::0"
				::sth::sthCore::invoke stc::config $createdIpv6LocalIf "-Address $addr -Gateway ::"
				::sth::sthCore::invoke stc::config $createdIpv6LocalIf -AllocateEui64LinkLocalAddress true
			}

			if {[regexp -nocase $ip_cp "ipv4v6" ]} {
				if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $createdHost -IfStack "Ipv4If" -IfCount "1" -AttachToIf $pppIf} err]} {
					::sth::sthCore::processError returnKeyedList "add Ipv4If Ipv6If Failed: $err" {}
					return -code 1 -errorcode -1 $err
				}
				if {$ipv6Cfglist != ""} {
					::sth::sthCore::invoke stc::config [lindex $ipv6ifList 1] $ipv6Cfglist
				}
				
				set createdIpv4If [::sth::sthCore::invoke stc::get $createdHost "-children-ipv4if"]
				::sth::sthCore::invoke stc::config $createdHost "-TopLevelIf-targets {$ipv6ifList $createdIpv4If}"
				::sth::sthCore::invoke stc::config $createdHost "-PrimaryIf-targets $createdIpv4If"
				set createdIpIf $createdIpv4If
			} else {
				::sth::sthCore::invoke stc::config $createdHost "-TopLevelIf-targets {$ipv6ifList}"
				::sth::sthCore::invoke stc::config $createdHost "-PrimaryIf-targets $createdIpv6If"
				set createdIpIf [lindex $ipv6ifList 1]
			}
		} else {
                    set createdIpv4If [::sth::sthCore::invoke stc::get $createdHost "-children-ipv4if"]
                    ::sth::sthCore::invoke stc::config $createdHost "-TopLevelIf-targets $createdIpv4If"
                    ::sth::sthCore::invoke stc::config $createdHost "-PrimaryIf-targets $createdIpv4If"
                    set createdIpIf $createdIpv4If
		}
		if {[regexp -nocase "ipv4if" $createdIpIf]} {
                    if {$ipv4Cfglist != ""} {
                        ::sth::sthCore::invoke stc::config $createdIpIf $ipv4Cfglist
                    } 
			
		} elseif {[regexp -nocase "ipv6if" $createdIpIf]} {
                    if {$ipv6Cfglist != ""} {
                        ::sth::sthCore::invoke stc::config $createdIpIf $ipv6Cfglist
                    } 
		} 
		array unset ipv4Paramlist
		array unset ipv6Paramlist
		# set vlanConfigParamList and  vlanOuterConfigParamList if  QinQ is created
		if {[regexp "ethernet_ii_qinq" $encap] || [regexp "ethernet_ii_mvlan" $encap] } {
			if {[regexp "ethernet_ii_mvlan" $encap] } {
                set userArgsArray(qinq_incr_mode) both
            }
            switch -exact -- $userArgsArray(qinq_incr_mode) {
                "both" {
                    
                    set vlan_id_new [expr $vlan_id + ([expr $i % $vlan_id_count] * $vlan_id_step)]
                    set vlan_id_outer_new [expr $vlan_id_outer + ([expr $i % $vlan_id_outer_count] * $vlan_id_outer_step)]
                    if { $num_sessions < $vlan_id_count || $num_sessions < $vlan_id_outer_count } {return -code 1 -errorcode -1 "num_sessions should be bigger than vlan_id_count and vlan_id_outer_count when qinq_incr_mode is \"both\""}
                    if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
                        set vlanConfigParamList   \
                                [list \
                                                -VlanId $vlan_id \
                                                -IdStep $vlan_id_step \
                                                -IfRecycleCount $vlan_id_count\
                                                -Priority $vlan_user_priority \
                                                -Cfi $vlan_cfi \
                                                -Tpid $vlan_tpid \
                                ]
                        set vlanOuterConfigParamList   \
                                [list \
                                                -VlanId $vlan_id_outer \
                                                -IdStep $vlan_id_outer_step \
                                                -IfRecycleCount $vlan_id_outer_count \
                                                -Priority $vlan_outer_user_priority \
                                                -Cfi $vlan_outer_cfi \
                                                -Tpid $vlan_tpid_outer\
                                ]
                    } else {
                        set vlanConfigParamList   \
                                [list \
                                                -VlanId $vlan_id_new \
                                                -Priority $vlan_user_priority \
                                                -Cfi $vlan_cfi \
                                                -Tpid $vlan_tpid \
                                ]
                        set vlanOuterConfigParamList   \
                                [list \
                                                -VlanId $vlan_id_outer_new \
                                                -Priority $vlan_outer_user_priority \
                                                -Cfi $vlan_outer_cfi \
                                                -Tpid $vlan_tpid_outer \
                                ]
                    }
                }
                "inner" {
                    set vlan_id_new [expr $vlan_id + ([expr $i % $vlan_id_count] * $vlan_id_step)]
                    set vlan_id_outer_new [expr $vlan_id_outer + ([expr ($i / $vlan_id_count) % $vlan_id_outer_count] * $vlan_id_outer_step)]
                    if { $num_sessions < $vlan_id_count * $vlan_id_outer_count } {return -code 1 -errorcode -1 "num_sessions should be bigger than vlan_id_count  * vlan_id_outer_count when qinq_incr_mode is \"inner\""}
                    if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
                        set vlanConfigParamList   \
                                [list \
                                                -VlanId $vlan_id \
                                                -IdStep $vlan_id_step \
                                                -IfRecycleCount $vlan_id_count\
                                                -Priority $vlan_user_priority \
                                                -Cfi $vlan_cfi \
                                                -Tpid $vlan_tpid \
                                ]
                        set vlanOuterConfigParamList   \
                                [list \
                                                -VlanId $vlan_id_outer \
                                                -IdStep $vlan_id_outer_step \
                                                -IdRepeatCount [expr $vlan_id_count -1]\
                                                -IfRecycleCount $vlan_id_outer_count\
                                                -Priority $vlan_outer_user_priority \
                                                -Cfi $vlan_outer_cfi \
                                                -Tpid $vlan_tpid_outer \
                                ]
                    } else {
                        set vlanConfigParamList   \
                                [list \
                                                -VlanId $vlan_id_new \
                                                -Priority $vlan_user_priority \
                                                -Cfi $vlan_cfi \
                                                -Tpid $vlan_tpid \
                                ]
                        set vlanOuterConfigParamList   \
                                [list \
                                                -VlanId $vlan_id_outer_new \
                                                -Priority $vlan_outer_user_priority \
                                                -Cfi $vlan_outer_cfi \
                                                -Tpid $vlan_tpid_outer \
                                ]
                    }
                }
                "outer" {
                    set vlan_id_new [expr $vlan_id + ([expr $i / $vlan_id_outer_count % $vlan_id_count] * $vlan_id_step)]
                    set vlan_id_outer_new [expr $vlan_id_outer + ([expr $i % $vlan_id_outer_count] * $vlan_id_outer_step)]
                    if { $num_sessions < $vlan_id_count * $vlan_id_outer_count } {return -code 1 -errorcode -1 "num_sessions should be bigger than vlan_id_count  * vlan_id_outer_count when qinq_incr_mode is \"outer\""}
                    if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
                        set vlanConfigParamList   \
                                [list \
                                        -VlanId $vlan_id \
                                        -IdStep $vlan_id_step \
                                        -IdRepeatCount  [expr $vlan_id_outer_count -1]\
                                        -IfRecycleCount $vlan_id_count\
                                        -Priority $vlan_user_priority \
                                        -Cfi $vlan_cfi \
                                        -Tpid $vlan_tpid \
                                ]
                        set vlanOuterConfigParamList   \
                                [list \
                                        -VlanId $vlan_id_outer \
                                        -IdStep $vlan_id_outer_step \
                                        -IfRecycleCount $vlan_id_outer_count \
                                        -Priority $vlan_outer_user_priority \
                                        -Cfi $vlan_outer_cfi \
                                        -Tpid $vlan_tpid_outer \
                                ]
                    } else {
                        set vlanConfigParamList   \
                                [list \
                                        -VlanId $vlan_id_new \
                                        -Priority $vlan_user_priority \
                                        -Cfi $vlan_cfi \
                                        -Tpid $vlan_tpid \
                                ]
                        set vlanOuterConfigParamList   \
                                [list \
                                        -VlanId $vlan_id_outer_new \
                                        -Priority $vlan_outer_user_priority \
                                        -Cfi $vlan_outer_cfi \
                                        -Tpid $vlan_tpid_outer \
                                ]
                    }
                }
            }
		}
    
		# set atmConfigParamList Aal5If is created
		if {[regexp "oa" $protocol] } {
			
			if {[regexp "vc_mux" $encap] } {
				set vc_encap  "VC_MULTIPLEXED"
			} else {
				set vc_encap "LLC_ENCAPSULATED"
			}
			
			#set atmConfigParamList \
			#                [list \
			#                    -Vci $vci \
			#                    -VciStep $vci_step \
			#                    -VciRecycleCount $vci_count \
			#                    -Vpi $vpi \
			#                    -VpiStep $vpi_step \
			#                    -VpiRepeatCount [expr $num_sessions/$vpi_count -1] \
			#                    -VcEncapsulation $vc_encap \
			#                ]
			set vci_new [expr $vci + ($i * $vci_step)]
                        set vpi_new [expr $vpi + ($i * $vpi_step)]
			switch -exact -- $userArgsArray(pvc_incr_mode) {
				"both" {
						if { $num_sessions < $vci_count || $num_sessions < $vpi_count } {return -code 1 -errorcode -1 "num_sessions should be bigger than vci_count  and vpi_count when pvc_incr_mode is \"both\""}
						if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
                                                    set atmConfigParamList \
                                                            [list \
                                                                    -Vci $vci \
                                                                    -VciStep $vci_step \
                                                                    -VciRecycleCount $vci_count \
                                                                    -Vpi $vpi \
                                                                    -VpiStep $vpi_step \
                                                                    -IfRecycleCount $vpi_count \
                                                                    -VcEncapsulation $vc_encap \
                                                            ]
                                                } else {
                                                    set atmConfigParamList \
                                                            [list \
                                                                    -Vci $vci_new \
                                                                    -Vpi $vpi_new \
                                                                    -VcEncapsulation $vc_encap \
                                                            ]
                                                }
				}
				"vci" {
						if { $num_sessions < $vci_count * $vpi_count } {return -code 1 -errorcode -1 "num_sessions should be bigger than vci_count  * vpi_count when pvc_incr_mode is \"vpi\""}
						if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
                                                    set atmConfigParamList \
                                                            [list \
                                                                    -Vci $vci \
                                                                    -VciStep $vci_step \
                                                                    -VciRecycleCount $vci_count \
                                                                    -Vpi $vpi \
                                                                    -VpiStep $vpi_step \
                                                                    -VpiRepeatCount [expr $vci_count -1]\
                                                                    -IfRecycleCount $vpi_count \
                                                                    -VcEncapsulation $vc_encap \
                                                            ]
                                                } else {
                                                    set atmConfigParamList \
                                                            [list \
                                                                    -Vci $vci_new \
                                                                    -Vpi $vpi_new \
                                                                    -VcEncapsulation $vc_encap \
                                                            ]
                                                }
				}
				"vpi" {
						if { $num_sessions < $vci_count * $vpi_count } {return -code 1 -errorcode -1 "num_sessions should be bigger than vci_count  * vpi_count when pvc_incr_mode is \"vci\""}
						if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
                                                    set atmConfigParamList \
                                                            [list \
                                                                    -Vci $vci \
                                                                    -VciStep $vci_step \
                                                                    -VciRepeatCount [expr $vpi_count -1]\
                                                                    -VciRecycleCount $vci_count \
                                                                    -Vpi $vpi \
                                                                    -VpiStep $vpi_step \
                                                                    -IfRecycleCount $vpi_count \
                                                                    -VcEncapsulation $vc_encap \
                                                            ]
                                                } else {
                                                    set atmConfigParamList \
                                                            [list \
                                                                    -Vci $vci_new \
                                                                    -Vpi $vpi_new \
                                                                    -VcEncapsulation $vc_encap \
                                                            ]
                                                }
				}
			}
		}


		switch -exact -- $userArgsArray(protocol) {
				"pppoe" {
					set createdEthiiIf [::sth::sthCore::invoke stc::get $createdHost "-children-ethiiif"]
                    set mac_addr_new [::sth::sthCore::macStep $mac_addr $mac_addr_step $i]
					::sth::sthCore::invoke stc::config $createdEthiiIf [list -SourceMac $mac_addr_new -SrcMacStep $mac_addr_step ]
					if {$encap == "ethernet_ii_vlan"} {
						set createdVlanIf [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
                        ::sth::Pppox::processConfigVlan $createdVlanIf $i
					} elseif {$encap == "ethernet_ii_qinq"} {
						set createdVlanIfs [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
						::sth::sthCore::invoke stc::config [lindex $createdVlanIfs 0] $vlanConfigParamList
						::sth::sthCore::invoke stc::config [lindex $createdVlanIfs 1] $vlanOuterConfigParamList
					} elseif {$encap == "ethernet_ii_mvlan"} {
                        ::sth::Pppox::processConfigMVlan $createdHost $vlanConfigParamList $vlanOuterConfigParamList
                    }
				}
				"pppoa" {
					set createdAal5If [::sth::sthCore::invoke stc::get $createdHost "-children-aal5if"]
					::sth::sthCore::invoke stc::config $createdAal5If $atmConfigParamList
				}
				"pppoeoa" {
					set createdAal5If [::sth::sthCore::invoke stc::get $createdHost "-children-aal5if"]
					::sth::sthCore::invoke stc::config $createdAal5If $atmConfigParamList
					
					set createdEthiiIf [::sth::sthCore::invoke stc::get $createdHost "-children-ethiiif"]
                                        set mac_addr [::sth::sthCore::macStep $mac_addr $mac_addr_step $i]
					::sth::sthCore::invoke stc::config $createdEthiiIf [list -SourceMac $mac_addr -SrcMacStep $mac_addr_step ]
					if {[regexp "ethernet_ii_vlan" $encap] } {
						set createdVlanIf [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
                        ::sth::Pppox::processConfigVlan $createdVlanIf $i
					} elseif {[regexp "ethernet_ii_qinq" $encap] } {
						set createdVlanIfs [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
						::sth::sthCore::invoke stc::config [lindex $createdVlanIfs 0] $vlanConfigParamList
						::sth::sthCore::invoke stc::config [lindex $createdVlanIfs 1] $vlanOuterConfigParamList
					} elseif {$encap == "ethernet_ii_mvlan"} {
                        ::sth::Pppox::processConfigMVlan $createdHost $vlanConfigParamList $vlanOuterConfigParamList
                    }
				}
		}
    
    
		##
		# Create the port and session param lists
		##
		foreach switchName [array names userArgsArray ] {
			
			set switchValue $userArgsArray($switchName)
			set stcObj     [::sth::sthCore::getswitchprop ::sth::Pppox:: $_OrigHltCmdName $switchName stcobj]
			set stcAttr     [::sth::sthCore::getswitchprop ::sth::Pppox:: $_OrigHltCmdName $switchName stcattr]
			set procFunc [::sth::sthCore::getModeFunc ::sth::Pppox:: $_OrigHltCmdName $switchName create]
			if {$procFunc == ""} {
				continue
			}

			if {[regexp -nocase  "PppoxPortConfig"  $stcObj ] } {
				# Save the port param and value
				if {[catch {$procFunc portConfigParamList  $switchName $switchValue $stcAttr returnKeyedList} err]} {
					#puts "DEBUG:Hit if. Error in $procName. Unrecognized parameter:\"-$switchName $switchValue\". Msg: $err"
					return -code 1 -errorcode -1 $err
				}
			} elseif {[regexp -nocase "PppoeClientBlockConfig"  $stcObj ] } {
				# Save the session block param and value
				if {[catch {$procFunc sessionBlockConfigParamList $switchName $switchValue $stcAttr returnKeyedList} err]} {
					#puts "DEBUG:Hit elseIf. Error in $procName. Unrecognized parameter:\"-$switchName $switchValue\". Msg: $err"
					return -code 1 -errorcode -1 $err
				}
			} elseif {[regexp -nocase "PppoxOptions" $stcObj]} {
				if {[catch {$procFunc globalConfigParamList $switchName $switchValue $stcAttr returnKeyedList} err]} {
					::sth::sthCore::processError returnKeyedList "$err" {}
					return -code error $returnKeyedList
				}
			}
		}
		
		if {[catch {::sth::Pppox::processConfigCmd_wildcard sessionBlockConfigParamList returnKeyedList} err]} {
			#puts "DEBUG:Error in ::sth::Pppox::processConfigCmd_wildcard. Unrecognized parameter:\"-$switchName $switchValue\". Msg: $err"
			return -code 1 -errorcode -1 $err
		}

		# Create/Configure the PPPoE /PPPoA SessionBlock
		if {[catch {set createdPppoeClientBlockConfig [::sth::sthCore::invoke stc::create $PppoxClientBlockConfig -under $createdHost]} err]} {
			#puts "DEBUG:Error in $procName. Msg: $err"
			return -code 1 -errorcode -1 $err
		}
		
		#####
		#RXu: workaroud for PPPOX over IPV6 traffic error, MUST be removed once 3.40 STC inself fixs this
		if {[regexp -nocase "v6" $ip_cp] && [info exists userArgsArray(use_internal_dhcpv6)] && $userArgsArray(use_internal_dhcpv6) == 1} {
			if {[catch {set createdDhcpv6PdBlockConfig [::sth::sthCore::invoke stc::create Dhcpv6PdBlockConfig -under $createdHost "-ControlPlanePrefix ROUTERADVERTISEMENT"]} err]} {
				#puts "DEBUG:Error in $procName. Msg: $err"
				return -code 1 -errorcode -1 $err
			}
		}
		#RXu: End
		#####
		
		
		if {$sessionBlockConfigParamList != ""} {
			if {[catch {::sth::sthCore::invoke stc::config $createdPppoeClientBlockConfig "$sessionBlockConfigParamList"} configStatus]} {
				set result "Error in $procName while configuring the PPPoE object: $configStatus "
				return -code 1 -errorcode -1 $result
			}
		}
		#setup the relationship for PppoeClientBlockConfig
		#test debug
		
		::sth::sthCore::invoke stc::config $createdPppoeClientBlockConfig "-UsesIf-targets $createdIpIf"
		incr i
    }
	
	# configure PPPoE project options
	if {$globalConfigParamList != ""} {
		if {[catch {set pppoxOptions [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-PppoxOptions]} err]} {
			::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
			return -code error $returnKeyedList
		}
		if {[catch {::sth::sthCore::invoke stc::config $pppoxOptions "$globalConfigParamList"} err]} {
			::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
			return -code error $returnKeyedList
		}
	}

	# Create/Configure the PPPoE Port
	if {[catch {set pppoePort [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-PppoxPortConfig]} err]} {
		set result "Error: No PppoxPortConfig object exists on port $userArgsArray(port_handle). Msg: $err"
		#puts "DEBUG:$result"
		return -code 1 -errorcode -1 $result
	}
	if {$portConfigParamList != ""} {
		if {[catch {::sth::sthCore::invoke stc::config $pppoePort "$portConfigParamList"} configStatus]} {
			set err "Error in $procName while configuring the PPPoE port object \"$pppoePort\": $configStatus "
			return -code 1 -errorcode -1 $err
		}
	}
    if {[info exists userArgsArray(apply)] && $userArgsArray(apply) == "1"} {
        #::sth::sthCore::log debug "Attempting apply after creating pppoeSessionBlock:{$pppoeSessionBlockList}"
        if {[catch {::sth::sthCore::doStcApply } err ]} {
            set result "Internal Error while calling apply. Error: $err"
            return -code 1 -errorcode -1 $result
        }
    }

    keylset returnKeyedList port_handle $userArgsArray(port_handle)
    keylset returnKeyedList handle $createdHostList;# will now be used for traffic
    keylset returnKeyedList handles $createdHostList;# will now be used for traffic
    keylset returnKeyedList pppoe_port $pppoePort
    keylset returnKeyedList pppoe_session $createdPppoeClientBlockConfig; # used for traffic

    return $returnKeyedList
}

proc ::sth::Pppox::processConfigVlan {createdVlanIf hostNum} {
    variable userArgsArray
    foreach param {vlan_id vlan_tpid vlan_id_step vlan_id_count vlan_user_priority vlan_cfi num_sessions} {
        set $param $userArgsArray($param)   
    }
    # US37424 Enhancement to support 8K devices in each of 4 vlans in HLTAPI 
    if {[info exists userArgsArray(vlan_id_repeat_count)] || [info exists userArgsArray(vlan_id_stack_count)]} {
        if {[info exists userArgsArray(vlan_id_repeat_count)]} {
            set vlan_id_repeat_count $userArgsArray(vlan_id_repeat_count)
            if {[expr $num_sessions % ($vlan_id_repeat_count + 1) != 0]} {
                return -code 1 -errorcode -1 "-encap is set to ethernet_ii_vlan,then the value of -num_sessions must be divided evenly by value of (-vlan_id_repeat_count + 1)."
            }
        } else {
            set vlan_id_repeat_count 0
        }
        if {[info exists userArgsArray(vlan_id_stack_count)] } {
            set vlan_id_stack_count $userArgsArray(vlan_id_stack_count)
        } else {
            set vlan_id_stack_count 1
        }
        set vlan_id_new $vlan_id
    } else {
        if {[expr $num_sessions % $vlan_id_count ==0]} {
            set vlan_id_repeat_count [expr $num_sessions/$vlan_id_count - 1]
        } else {
            return -code 1 -errorcode -1 "-encap is set to ethernet_ii_vlan,then the value of -num_sessions must be divided evenly by value of -vlan_id_count."
        }
        set vlan_id_new [expr $vlan_id + ([expr $hostNum % $vlan_id_count] * $vlan_id_step)]
        set vlan_id_count 0
        set vlan_id_stack_count 1
    }
    if {[regexp -nocase "multi_device_per_block" $userArgsArray(device_block_mode)]} {
        if {[catch {::sth::sthCore::invoke stc::config $createdVlanIf [list -VlanId $vlan_id_new -IdStep $vlan_id_step -IfRecycleCount $vlan_id_count -IdRepeatCount $vlan_id_repeat_count -IfCountPerLowerIf $vlan_id_stack_count -Priority $vlan_user_priority -Cfi $vlan_cfi -Tpid $vlan_tpid]} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring pppox: $eMsg"
            return $::sth::sthCore::FAILURE
        }
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $createdVlanIf [list -VlanId $vlan_id_new -Priority $vlan_user_priority -Cfi $vlan_cfi -Tpid $vlan_tpid ]} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring pppox: $eMsg"
            return $::sth::sthCore::FAILURE
        }
    }
}


proc ::sth::Pppox::processConfigMVlan {createdHost vlanConfigParamList vlanOuterConfigParamList} {
    variable userArgsArray
        
    set createdVlanIfs [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
    if {$createdVlanIfs ne "" && [info exists ::sth::Pppox::userArgsArray(vlan_id_list)]} { 
        ::sth::sthCore::invoke stc::config [lindex $createdVlanIfs 0] $vlanConfigParamList
        ::sth::sthCore::invoke stc::config [lindex $createdVlanIfs 1] $vlanOuterConfigParamList
        set vlanid_list $userArgsArray(vlan_id_list)
        set tpid_list $userArgsArray(vlan_tpid_list)
        set idcount_list $userArgsArray(vlan_id_count_list)
        set userprio_list $userArgsArray(vlan_user_priority_list)
        set idstep_list $userArgsArray(vlan_id_step_list)
        set cfi_list $userArgsArray(vlan_cfi_list)
        
        set index [expr [llength $createdVlanIfs] -1]
        set vlanHandle [lindex $createdVlanIfs $index]
        set stack_target [::sth::sthCore::invoke stc::get $vlanHandle -stackedonendpoint-targets]
        set i 0    
        foreach vlanid $vlanid_list {
            set myvlanid $vlanid 
            set stackedHandle [::sth::sthCore::invoke stc::create VlanIf -under $createdHost]
            ::sth::sthCore::invoke stc::config $vlanHandle "-StackedOnEndpoint-targets $stackedHandle"
            
            set tpid [lindex $tpid_list $i]
            if {$tpid == ""} {
                set tpid $::sth::Pppox::pppox_config_default(vlan_tpid_list)
            }
            set idcount [lindex $idcount_list $i]
            if {$idcount == ""} {
                set idcount $::sth::Pppox::pppox_config_default(vlan_id_count_list)
            }
            set usrprio [lindex $userprio_list $i]
            if {$usrprio == ""} {
                set usrprio $::sth::Pppox::pppox_config_default(vlan_user_priority_list)
            }
            set idstep [lindex $idstep_list $i]
            if {$idstep == ""} {
                set idstep $::sth::Pppox::pppox_config_default(vlan_id_step_list)
            }
            set cfi [lindex $cfi_list $i]
            if {$cfi == ""} {
                set cfi $::sth::Pppox::pppox_config_default(vlan_cfi_list)
            }
            
            if {[catch {::sth::sthCore::invoke stc::config $stackedHandle "-VlanId $myvlanid -IdStep $idstep -Cfi $cfi -IfRecycleCount $idcount -Priority $usrprio -Tpid $tpid"} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal error configuring pppox: $eMsg"
                return $::sth::sthCore::FAILURE
            }
    
            set vlanHandle $stackedHandle
            incr i
        }
        
        
        if {$stack_target ne ""} {
            ::sth::sthCore::invoke stc::config $vlanHandle "-stackedonendpoint-targets $stack_target"
        } else {
            return -code error "cannot find object to set its stackedonendpoint-sources for multiple vlans"
        }
    }
}

#processConfigCmd1=(catch) 6299 microseconds
#processConfigCmd2=(set) 5753 microseconds
#time "processConfigCmd1 configList config_req_timeout 3 returnKeyedList"
#3521 microseconds per iteration
#time "processConfigCmd1 configList auth_mode pap returnKeyedList"
#2778 microseconds per iteration
#time "processConfigCmd2 configList config_req_timeout 3 returnKeyedList"
#2615 microseconds per iteration
#time "processConfigCmd2 configList auth_mode pap returnKeyedList"
#3138 microseconds per iteration
proc ::sth::Pppox::processConfigCmd { configListName  switchName switchValue switchStcAttr returnKeyedListVarName } {
    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    lappend configList -$switchStcAttr $switchValue

    return $returnKeyedList
}

proc ::sth::Pppox::processConfigFwdCmd { configListName  switchName switchValue switchStcAttr returnKeyedListVarName} {
    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList

    # get forward map for "constant" property 
    set fwdValue [::sth::sthCore::getFwdmap ::sth::Pppox:: pppox_config $switchName $switchValue]
    set switchStcAttr [::sth::sthCore::getswitchprop ::sth::Pppox:: pppox_config $switchName stcattr]
    
    lappend configList -$switchStcAttr $fwdValue
    
    return $returnKeyedList
}

proc ::sth::Pppox::processConfigCmd_wildcard { configListName returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    set _OrigHltCmdName "pppox_config"

    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList

    # Handle the wildcards

    #password_wildcard
    #username_wildcard
    #wildcard_question_start
    #wildcard_question_end
    #wildcard_question_fill
    #wildcard_pound_start
    #wildcard_pound_end
    #wildcard_pound_fill
    #wildcard_bang_start
    #wildcard_bang_end
    #wildcard_bang_fill
    #wildcard_dollar_start
    #wildcard_dollar_end
    #wildcard_dollar_fill

    if {! [info exists userArgsArray(username_wildcard)] && !  [info exists userArgsArray(password_wildcard)]} {
        # do nothing
        return $returnKeyedList
    }

    # Calculate the start/end for 4 marker characters

    foreach marker {question pound bang dollar} {
        set ${marker}_start 1
        set ${marker}_count 1
        set ${marker}_step 1
        set ${marker}_fill 0
        set ${marker}_repeat 0
        set ${marker}_end 1

        # testers
        #set ${marker}_start 0xFF
        #set ${marker}_count 0xFF
        #set ${marker}_step 0xFF
        #set ${marker}_fill 0xFF
        #set ${marker}_repeat 0xFF
        #set ${marker}_end 0xFF

        foreach type {start fill end} {
            if {[info exists userArgsArray(wildcard_[set marker]_[set type])]} {
                set ${marker}_${type} $userArgsArray(wildcard_[set marker]_[set type])
            }
        }

        if {[set [set marker]_end] < [set [set marker]_start]} {
            set result "Error: wildcard_${marker}_end ([set [set marker]_end]) must not be less than wildcard_${marker}_start ([set [set marker]_start])"
            #puts "DEBUG: Error in $procName. Msg: $result"
            return -code 1 -errorcode -1 $result
        }

        set ${marker}_count [expr "([set [set marker]_end] - [set [set marker]_start]) + 1"]
        set ${marker}_string "@x([set [set marker]_start],[set [set marker]_count],[set [set marker]_step],[set [set marker]_fill],[set [set marker]_repeat])"
        #puts "DEBUG:${marker}_string=[set [set marker]_string]"

    }

    # Reconfigure the actual username and/or password for wildcards
    foreach attr {{username anonymous} {password pass}} {
        foreach {attrName attrDefault} $attr {};
        if {[info exists userArgsArray(${attrName}_wildcard)]} {
            set $attrName $attrDefault
            if {[info exists userArgsArray($attrName)]} {
                set $attrName $userArgsArray($attrName)
            }
            foreach pair {{# pound} {? question} {! bang} {$ dollar}} {
                foreach {symbol marker} $pair {};
                #set cmd "regsub -all \{\\$symbol\} [set [set attrName]] [set [set marker]_string] $attrName"
                #eval $cmd
                regsub -all \\$symbol [set [set attrName]] [set [set marker]_string] $attrName

            }
            lappend configList -$attrName [set [set attrName]]
        }
    }

    return $returnKeyedList
}

proc ::sth::Pppox::processConfigCmd_PapChap { configListName switchName switchValue switchStcAttr returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList

    if {! [info exists userArgsArray(auth_mode)]} {
        # Do nothing
        return $returnKeyedList
    }
    # userArgsArray(auth_mode) has been mapped to new values in table file, we need to map here too
    foreach auth_mode_value {"pap" "chap" "pap_or_chap"} {
        set auth_mode_map($auth_mode_value)  [::sth::sthCore::getFwdmap      ::sth::Pppox::  pppox_config  auth_mode $auth_mode_value]
    }
    	
    set val $switchValue
    switch -- ${userArgsArray(auth_mode)},${switchName} $auth_mode_map(pap),auth_req_timeout {
            lappend configList -PapRequestTimeout $val
        } $auth_mode_map(chap),auth_req_timeout {
            lappend configList -ChapChalRequestTimeout $val
        } $auth_mode_map(pap_or_chap),auth_req_timeout {
            lappend configList -PapRequestTimeout $val -ChapChalRequestTimeout $val
        } $auth_mode_map(pap),max_auth_req {
            lappend configList -MaxPapRequestAttempts $val
        } $auth_mode_map(chap),max_auth_req {
            lappend configList -MaxChapRequestReplyAttempts $val
        } $auth_mode_map(pap_or_chap),max_auth_req {
            lappend configList -MaxPapRequestAttempts $val -MaxChapRequestReplyAttempts $val
        }
    

    return $returnKeyedList
}

proc ::sth::Pppox::processConfigCmd_EchoReq { configListName switchName switchValue switchStcAttr returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList

    if {$userArgsArray($switchName) < 1} {
        lappend configList -MaxEchoRequestAttempts 0
    } else {
        # Hack until the UI/BLL exposes a checkbox/field like on the AX
        if {![info exists userArgsArray(max_echo_acks)]} {
            lappend configList -MaxEchoRequestAttempts 3
        }
    }

    return $returnKeyedList
}
#PPPoX 3.00 enhancement
proc ::sth::Pppox::processConfigCmd_intermediateAgent_remoteSessionId { configListName switchName switchValue switchStcAttr returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList

    #2516 is session id & MAC, dsl is remote id & circuit ID

    if {![info exists userArgsArray(intermediate_agent)]} {
         return $returnKeyedList
    } else {
        if {$userArgsArray(intermediate_agent) == "0"} {
            return $returnKeyedList
        }
    }

    set agentType 2516
    if {[info exists userArgsArray(agent_type)]} {
        set agentType $userArgsArray(agent_type)
    }
    
    if {[regexp "dsl" $agentType] && $switchName == "agent_session_id"} {
        # Do nothing
        return $returnKeyedList
    } elseif {$agentType == "2516" && $switchName != "agent_session_id"} {
        # Do nothing
        return $returnKeyedList
    }
    
    set remoteName ""
    set remoteId ""
    if {[regexp "dsl" $agentType]} {
        if {[info exists userArgsArray(pppoe_remote_id)]} {
            set remoteName $userArgsArray(pppoe_remote_id)
        }
    
        if {$userArgsArray(remote_id_suffix_mode) == "none"} { 
            set remoteId $remoteName       
        } elseif {$userArgsArray(remote_id_suffix_mode) == "incr"} {
            if {$switchName == "remote_id_incr_start"} {
                set suffixStep 0
                set suffixCount 0
                set suffixStart $userArgsArray(remote_id_incr_start)
                if {[info exists userArgsArray(remote_id_incr_step)]} {
                    set suffixStep $userArgsArray(remote_id_incr_step)
                }
                if {[info exists userArgsArray(remote_id_incr_count)]} {
                    if {$userArgsArray(remote_id_incr_count) >= 1} {
                        set suffixCount [expr {$userArgsArray(remote_id_incr_count)-1}]
                    }
                }
                #convert decimal to HEX
                set hexsuffixStart [format "%x" $suffixStart]
                set remoteId "$remoteName @x($hexsuffixStart,0,$suffixStep,1,$suffixCount)"     
            } else {
                return $returnKeyedList
            }
        }
    }

    lappend configList -RemoteOrSessionId "$remoteId"

    return $returnKeyedList
}

#PPPoX 3.00 enhancement
proc ::sth::Pppox::processConfigCmd_intermediateAgent_cirentId { configListName switchName switchValue switchStcAttr returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $configListName configList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set circuitName ""
    set circuitId ""
    
    if {![info exists userArgsArray(intermediate_agent)]} {
         return $returnKeyedList
    } else {
        if {$userArgsArray(intermediate_agent) == "0"} {
            return $returnKeyedList
        }
    }
    #circuit_id can be configured only when agent_type is dsl
    set agentType 2516
    if {[info exists userArgsArray(agent_type)]} {
        set agentType $userArgsArray(agent_type)
    }
    if {![regexp "dsl" $agentType]} {
        return $returnKeyedList
    }
    if {[info exists userArgsArray(pppoe_circuit_id)]} {
        set circuitName $userArgsArray(pppoe_circuit_id)
    }
    
    if {$userArgsArray(circuit_id_suffix_mode) == "none"} { 
        set circuitId $circuitName
        
    } elseif {$userArgsArray(circuit_id_suffix_mode) == "incr"} {
        if {$switchName == "circuit_id_incr_start"} {
            set suffixStep 0
            set suffixCount 0
            set suffixStart $userArgsArray(circuit_id_incr_start)
            if {[info exists userArgsArray(circuit_id_incr_step)]} {
                set suffixStep $userArgsArray(circuit_id_incr_step)
            }
            if {[info exists userArgsArray(circuit_id_incr_count)]} {
                if {$userArgsArray(circuit_id_incr_count) >= 1} {
                    set suffixCount [expr {$userArgsArray(circuit_id_incr_count)-1}]
                }
            }
            #convert decimal to HEX
            set hexsuffixStart [format "%x" $suffixStart]
            set circuitId "$circuitName @x($hexsuffixStart,0,$suffixStep,1,$suffixCount)"     
        } else {
            return $returnKeyedList
        }
    }
    
    lappend configList -CircuitId "$circuitId"
    
    return $returnKeyedList
}
###/*! \ingroup pppoeswitchprocfuncs
###\fn pppox_config_modify (str args)
###\brief Process \em -mode switch with value \em modify for pppox_config cmd
###
###This procedure executes the pppox_config command when the mode is modify.  It will modify all pppoe sessions based on the port_handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList
###
###
###\author Alison Lee (all)
###*/
###
###pppox_config_modify (str args);
###

proc ::sth::Pppox::pppox_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray
    variable sortedSwitchPriorityList

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "pppox_config"
    set _hltCmdName "pppox_config_modify"

    upvar 1 $returnKeyedListVarName returnKeyedList

    if {![info exists userArgsArray(handle)]} {
        set result "The option -handle is mandatory."
        #keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }
    #unset the default value
    foreach ele $sortedSwitchPriorityList {
        set switchName [lindex $ele 1]
        set newUserArgsArray($switchName) $userArgsArray($switchName)
    }
    unset userArgsArray
    array set userArgsArray [array get newUserArgsArray]
    
    set ports ""
    set pppoePorts ""
    set createdPppoeClientBlockConfigs ""
    set portConfigParamList ""
    set sessionBlockConfigParamList ""
    set globalConfigParamList ""
    foreach switchName [array names userArgsArray ] {
        
        set switchValue $userArgsArray($switchName)
        set stcObj     [::sth::sthCore::getswitchprop ::sth::Pppox:: $_OrigHltCmdName $switchName stcobj]
        set stcAttr     [::sth::sthCore::getswitchprop ::sth::Pppox:: $_OrigHltCmdName $switchName stcattr]
        set procFunc [::sth::sthCore::getModeFunc ::sth::Pppox:: $_OrigHltCmdName $switchName create]
        if {$procFunc == ""} {
            continue
        }

        if {[regexp -nocase  "PppoxPortConfig"  $stcObj ] } {
            if {[catch {$procFunc portConfigParamList $switchName $switchValue $stcAttr returnKeyedList} err]} {
                return -code 1 -errorcode -1 $err
            }
        } elseif {[regexp -nocase  "PppoeClientBlockConfig"  $stcObj ] } {
            if {[catch {$procFunc sessionBlockConfigParamList $switchName $switchValue $stcAttr returnKeyedList} err]} {
                return -code 1 -errorcode -1 $err
            }
        } elseif {[regexp -nocase "PppoxOptions" $stcObj]} {
            if {[catch {$procFunc globalConfigParamList $switchName $switchValue $stcAttr returnKeyedList} err]} {
                ::sth::sthCore::processError returnKeyedList "$err" {}
                return -code error $returnKeyedList
            }
        }
    }
    
    
    if {[catch {::sth::Pppox::processConfigCmd_wildcard sessionBlockConfigParamList returnKeyedList} err]} {
        return -code 1 -errorcode -1 $err
    }
    
    if {$globalConfigParamList != ""} {
        if {[catch {set pppoxOptions [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-PppoxOptions]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $pppoxOptions "$globalConfigParamList"} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
    
    foreach host $userArgsArray(handle) {
        set port  [::sth::sthCore::invoke stc::get $host "-AffiliationPort-Targets"]
        set portConfig [::sth::sthCore::invoke stc::get $port "-children-PppoxPortConfig"]
        if {$portConfigParamList != ""} {
            if {[catch {::sth::sthCore::invoke stc::config $portConfig "$portConfigParamList"} configStatus]} {
                set err "Error in $procName while configuring $portConfig: $configStatus "
                return -code 1 -errorcode -1 $err
            }
        }
        set PppoxClientBlockConfig [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]ClientBlockConfig
        if {[set sessionBlockConfig [::sth::sthCore::invoke stc::get $host "-children-$PppoxClientBlockConfig"]] == ""} {
                set result "Error while fetching PppoxPortConfig of $host: $host is not a valid PPPox Host"
                keylset returnKeyedList log $result
                return -code 1 -errorcode -1 $result
        }
        if {$sessionBlockConfigParamList != ""} {
            if {[catch {::sth::sthCore::invoke stc::config $sessionBlockConfig "$sessionBlockConfigParamList"} configStatus]} {
                set result "Error in $procName while configuring the PPPoE object: $configStatus "
                return -code 1 -errorcode -1 $result
            }
        }
        
        ###exit here once caller is ixiangpf
        if {[regexp -nocase "ixiangpf" [info level 1]]} {
            keylset returnKeyedList port_handle $ports
            keylset returnKeyedList handle $userArgsArray(handle);# will now be used for traffic
            keylset returnKeyedList handles $userArgsArray(handle);# will now be used for traffic
            return $returnKeyedList
        }
        set Ipv6If [::sth::sthCore::invoke stc::get $host "-children-Ipv6If"]
        set Ipv4If [::sth::sthCore::invoke stc::get $host "-children-Ipv4If"]
        set CurrentIfStack "[lindex $Ipv6If 0] $Ipv4If"
        if {$Ipv6If != "" && $Ipv4If != ""} {set CurrentIfStack [lindex $Ipv6If 0]}
        set IpIf $CurrentIfStack
        if {[info exists userArgsArray(ip_cp)]} {
            if {$userArgsArray(ip_cp) == "ipv4v6" || $userArgsArray(ip_cp) == "ipv6"} {
                if {$Ipv6If == ""} {
                    set Ipv6If [::sth::sthCore::invoke stc::create Ipv6If -under $host]
                }
                set IpIf [lindex $Ipv6If 0]
            } else {
                if {$Ipv4If == ""} {
                    set Ipv4If [::sth::sthCore::invoke stc::create Ipv4If -under $host]
                }
                set IpIf $Ipv4If
            }
        }
        
        set PppoeIf [::sth::sthCore::invoke stc::get $host "-children-pppoeIf"]
        set PppIf [::sth::sthCore::invoke stc::get $host "-children-pppIf"]
        set CurrentIfStack "$CurrentIfStack $PppIf $PppoeIf"
        set IfStack "$IpIf $PppIf $PppoeIf"
        if {[info exists userArgsArray(protocol)]}  {
            switch -exact -- $userArgsArray(protocol) {
                "pppoe" {
                    set EthiiIf [::sth::sthCore::invoke stc::get $host "-children-EthiiIf"]
                    if {$userArgsArray(encap) == "ethernet_ii_vlan"} {
                        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] == ""} {
                            set VlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                        } else {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                        }
                        #in case the previously has dual vlan stack
                        set VlanIf  [lindex $VlanIf 0]
                        set IfStack "$IfStack $VlanIf"
                    } elseif {$userArgsArray(encap) == "ethernet_ii_qinq"} {
                        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] == ""} {
                            set VlanIf1 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf2 $VlanIf1"
                        } elseif {[llength $VlanIf]>1} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                            set IfStack "$IfStack $VlanIf"
                        } else {
                            #set CurrentIfStack "$CurrentIfStack $PppIf $PppoeIf $VlanIf $EthiiIf"
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf $VlanIf2"
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                        }
                    } elseif {$userArgsArray(encap) == "ethernet_ii_mvlan"} {
                        set len [llength $userArgsArray(vlan_id_list)]
                        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] == ""} {
                            set VlanIf1 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf2 $VlanIf1"

                            for {set idx 0} {$idx < $len} {incr idx} {
                                set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $myVlanIf"
                            }
                        } elseif {[llength $VlanIf] == 2} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"                            
                            set IfStack "$IfStack $VlanIf"
                            for {set idx } {$idx < $len} {incr idx} {
                                set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $myVlanIf"
                            }
                        } elseif {[llength $VlanIf] == 1} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"                            
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf $VlanIf2"
                            for {set idx 0} {$idx < $len} {incr idx} {
                                set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $myVlanIf"
                            }
                        } elseif {[llength $VlanIf] > 2} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                            set oldlen [expr [llength $VlanIf] - 2]
                            if {$len < $oldlen} {
                                set IfStack "$IfStack [lrange $VlanIf 0 [expr $len + 1]]"
                            } else {
                                set IfStack "$IfStack [lrange $VlanIf 0 [expr $oldlen + 1]]"
                                for {set idx $oldlen} {$idx < $len} {incr idx} {
                                    set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                    set IfStack "$IfStack $myVlanIf"
                                }
                            }
                        }
                    } else {
                        if {[set oldVlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] != ""} {
                            set CurrentIfStack "$CurrentIfStack $oldVlanIf"
                            set IfStack "$IfStack $oldVlanIf"
                        }
                    }
                    set IfStack "$IfStack $EthiiIf"
                    set CurrentIfStack "$CurrentIfStack $EthiiIf"
                    if {[set oldAal5If [::sth::sthCore::invoke stc::get $host "-children-Aal5If"]] != ""} {
                        set CurrentIfStack "$CurrentIfStack $oldAal5If"
                        set IfStack "$IfStack $$oldAal5If"
                    }
                }
                "pppoa" {
                    set Aal5If [::sth::sthCore::invoke stc::get $host "-children-Aal5If"]
                    if {[set oldVlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] != ""} {
                        set CurrentIfStack "$CurrentIfStack $oldVlanIf"
                    }
                    if {[set oldEthiiIf [::sth::sthCore::invoke stc::get $host "-children-EthiiIf"]] != ""} {
                        set CurrentIfStack "$CurrentIfStack $oldEthiiIf"
                    }
                    set CurrentIfStack "$CurrentIfStack $Aal5If"
                    set IfStack "$IfStack $Aal5If"
                }
                "pppoeoa" {
                    set Aal5If [::sth::sthCore::invoke stc::get $host "-children-Aal5If"]
                    if {[regexp "ethernet_ii_vlan" $userArgsArray(encap)] } {
                        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] == ""} {
                            set VlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf"
                        } else {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                            if {[llength $VlanIf]>1} {
                                set VlanIf [lindex $VlanIf 0]
                            }
                            set IfStack "$IfStack $VlanIf"
                        }
                    } elseif {[regexp "ethernet_ii_qinq" $userArgsArray(encap)] } {
                        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] == ""} {
                            set VlanIf1 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf2 $VlanIf1"
                        } else {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                            if {[llength $VlanIf]>1} {
                               set IfStack " $IfStack $VlanIf"
                            } else {
                                set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $VlanIf2 $VlanIf"
                            }
                        }
                    } elseif {$userArgsArray(encap) == "ethernet_ii_mvlan"} {
                        set len [llength $userArgsArray(vlan_id_list)]
                        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] == ""} {
                            set VlanIf1 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf2 $VlanIf1"

                            for {set idx 0} {$idx < $len} {incr idx} {
                                set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $myVlanIf"
                            }
                        } elseif {[llength $VlanIf] == 2} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"                            
                            set IfStack "$IfStack $VlanIf"
                            for {set idx } {$idx < $len} {incr idx} {
                                set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $myVlanIf"
                            }
                        } elseif {[llength $VlanIf] == 1} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"                            
                            set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack "$IfStack $VlanIf $VlanIf2"
                            for {set idx 0} {$idx < $len} {incr idx} {
                                set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                set IfStack "$IfStack $myVlanIf"
                            }
                        } elseif {[llength $VlanIf] > 2} {
                            set CurrentIfStack "$CurrentIfStack $VlanIf"
                            set oldlen [expr [llength $VlanIf] - 2]
                            if {$len < $oldlen} {
                                set IfStack "$IfStack [lrange $VlanIf 0 [expr $len + 1]]"
                            } else {
                                set IfStack "$IfStack [lrange $VlanIf 0 [expr $oldlen + 1]]"
                                for {set idx $oldlen} {$idx < $len} {incr idx} {
                                    set myVlanIf [::sth::sthCore::invoke stc::create VlanIf -under $host]
                                    set IfStack "$IfStack $myVlanIf"
                                }
                            }
                        }
                    } else {
                        if {[set oldVlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] != ""} {
                            set CurrentIfStack "$CurrentIfStack $oldVlanIf"
                            set IfStack "$IfStack $oldVlanIf"
                        }
                    }
                    if {[set EthiiIf [::sth::sthCore::invoke stc::get $host "-children-EthiiIf"]] == ""} {
                        set EthiiIf [::sth::sthCore::invoke stc::create EthiiIf -under $host]
                        set IfStack "$IfStack $EthiiIf"
                    } else {
                        set CurrentIfStack "$CurrentIfStack $EthiiIf"
                        set IfStack "$IfStack $EthiiIf"
                    }
                    set CurrentIfStack "$CurrentIfStack $Aal5If"
                    set IfStack "$IfStack $Aal5If"
                }
            }
        } else {
            if {[set oldVlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] != ""} {
                set CurrentIfStack "$CurrentIfStack $oldVlanIf"
                set IfStack "$IfStack $oldVlanIf"
            }
            if {[set oldEthiiIf [::sth::sthCore::invoke stc::get $host "-children-EthiiIf"]] != ""} {
                set CurrentIfStack "$CurrentIfStack $oldEthiiIf"
                set IfStack "$IfStack $oldEthiiIf"
            }
            if {[set oldAal5If [::sth::sthCore::invoke stc::get $host "-children-Aal5If"]] != ""} {
                set CurrentIfStack "$CurrentIfStack $oldAal5If"
                set IfStack "$IfStack $oldAal5If"
            }
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform IfStackReplace -DeviceList $host -NewIfStack $IfStack -CurrentIfStack $CurrentIfStack} configStatus]} {
            set result "Error in $procName while doStcPerform IfStackReplace: $configStatus "
            return -code 1 -errorcode -1 $result
        }
        # US37424 Enhancement to support 8K devices in each of 4 vlans in HLTAPI 
        foreach {stcattrgateway hnamegateway} {gateway gateway_ip_addr GatewayStep gateway_ip_step GatewayRecycleCount stack_gateway_ip_recycle_count GatewayRepeatCount stack_gateway_ip_repeat_count} {
            if {[info exists userArgsArray($hnamegateway)]} {
                lappend gatewayConfigParamList -$stcattrgateway $userArgsArray($hnamegateway)
            }
        }       
        if {[info exists userArgsArray(ip_cp)]} {
            set Ipv6If [::sth::sthCore::invoke stc::get $host "-children-ipv6if"]
            set Ipv4If [::sth::sthCore::invoke stc::get $host "-children-ipv4if"]
            
            if {$userArgsArray(ip_cp) == "ipv4v6"} {
                if {[llength $Ipv6If] == 1 } {
                    #Create and Config ipv6ifLocal
                    if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $host -IfStack "Ipv6If" -IfCount "1" -AttachToIf $PppIf} err]} {
                        ::sth::sthCore::processError returnKeyedList "add locallink Ipv6If Failed: $err" {}
                        return -code 1 -errorcode -1 $err
                    }
                    set Ipv6If [::sth::sthCore::invoke stc::get $host "-children-ipv6if"]
                    set Ipv6LocalIf [lindex $Ipv6If 0]
                    if {[info exists userArgsArray(local_ipv6_addr)]} {
                        set addr $userArgsArray(local_ipv6_addr)
                    } else {
                        set addr "FE80::0"
                    }
                    ::sth::sthCore::invoke stc::config $Ipv6LocalIf "-Address $addr -Gateway ::"
                }
                if {$Ipv4If == ""} {
                    if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $host -IfStack "Ipv4If" -IfCount "1" -AttachToIf $PppIf} err]} {
                        ::sth::sthCore::processError returnKeyedList "add Ipv4If Ipv6If Failed: $err" {}
                        return -code 1 -errorcode -1 $err
                    }
                    set Ipv4If [::sth::sthCore::invoke stc::get $host "-children-ipv4if"]
                }
                ::sth::sthCore::invoke stc::config $host "-TopLevelIf-targets {$Ipv6If $Ipv4If}"
                ::sth::sthCore::invoke stc::config $host "-PrimaryIf-targets $Ipv4If"
                set useIpIf $Ipv4If
                # US37424 Enhancement to support 8K devices in each of 4 vlans in HLTAPI 
                if {[llength $gatewayConfigParamList] > 0} {
                if {[catch {::sth::sthCore::invoke stc::config $useIpIf $gatewayConfigParamList} eMsg]} {
                    set err "Internal error configuring pppox: $eMsg"
                    return -code 1 -errorcode -1 $err
                    }
                } 
            } elseif {$userArgsArray(ip_cp) == "ipv6"} {
                if {[llength $Ipv6If] == 1 } {
                    #Create and Config ipv6ifLocal
                    if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $host -IfStack "Ipv6If" -IfCount "1" -AttachToIf $PppIf} err]} {
                        ::sth::sthCore::processError returnKeyedList "add locallink Ipv6If Failed: $err" {}
                        return -code 1 -errorcode -1 $err
                    }
                    set Ipv6If [::sth::sthCore::invoke stc::get $host "-children-ipv6if"]
                    set Ipv6LocalIf [lindex $Ipv6If 0]
                    if {[info exists userArgsArray(local_ipv6_addr)]} {
                        set addr $userArgsArray(local_ipv6_addr)
                    } else {
                        set addr "FE80::0"
                    }
                    ::sth::sthCore::invoke stc::config $Ipv6LocalIf "-Address $addr -Gateway ::"
                }
                if {$Ipv4If != ""} {
                    ::sth::sthCore::invoke stc::delete $Ipv4If
                }
                ::sth::sthCore::invoke stc::config $host "-TopLevelIf-targets {$Ipv6If}"
                ::sth::sthCore::invoke stc::config $host "-PrimaryIf-targets [lindex $Ipv6If 0]"
                set useIpIf $Ipv6If
            } else {
                if {$Ipv6If != ""} {
                    ::sth::sthCore::invoke stc::delete "$Ipv6If"
                }
                if {$Ipv4If == ""} {
                    if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $host -IfStack "Ipv4If" -IfCount "1" -AttachToIf $PppIf} err]} {
                        ::sth::sthCore::processError returnKeyedList "add Ipv4If Ipv6If Failed: $err" {}
                        return -code 1 -errorcode -1 $err
                    }
                    set Ipv4If [::sth::sthCore::invoke stc::get $host "-children-ipv4if"]
                    ::sth::sthCore::invoke stc::config $host "-TopLevelIf-targets {$Ipv4If}"
                    ::sth::sthCore::invoke stc::config $host "-PrimaryIf-targets $Ipv4If"
                }
                set useIpIf $Ipv4If
                # US37424 Enhancement to support 8K devices in each of 4 vlans in HLTAPI 
                if {[llength $gatewayConfigParamList] > 0} {
                if {[catch {::sth::sthCore::invoke stc::config $useIpIf $gatewayConfigParamList} eMsg]} {
                    set err "Internal error configuring pppox: $eMsg"
                    return -code 1 -errorcode -1 $err
                    }
                }                 
            }
            ::sth::sthCore::invoke stc::config $sessionBlockConfig "-UsesIf-targets {$useIpIf}"
        }
        
        if {[info exists userArgsArray(num_sessions)]} {
            set num_sessions $userArgsArray(num_sessions)
            if {[catch {::sth::sthCore::invoke stc::config $userArgsArray(handle) "-DeviceCount $userArgsArray(num_sessions)"} configStatus]} {
                set result "Error in $procName while configuring the host:  $configStatus"
                return -code 1 -errorcode -1 $result
            }
        } else {
            set num_sessions [::sth::sthCore::invoke stc::get $userArgsArray(handle)  -DeviceCount]
        }
        if {[set Aal5If [::sth::sthCore::invoke stc::get $host "-children-Aal5If"]] != ""} {
            set atmConfigParamList ""
            foreach {stcattr hname} {Vci vci VciStep VciRecycleCount vci_count Vpi vpi VpiRepeatCount vci_count} {
                if {[info exists userArgsArray($hname)]} {
                    lappend atmConfigParamList -$stcattr $userArgsArray($hname)
                }
            }
            if {[info exists userArgsArray(encap)]} {
                if {[regexp "vc_mux" $userArgsArray(encap)] } {
                    lappend atmConfigParamList  -VcEncapsulation VC_MULTIPLEXED
                } else {
                    lappend atmConfigParamList  -VcEncapsulation LLC_ENCAPSULATED
                }
            }
            if {[info exists userArgsArray(pvc_incr_mode)] && [info exists userArgsArray(vci_count)] && [info exists userArgsArray(vpi_count)] } {
                switch -exact -- $userArgsArray(pvc_incr_mode) {
                    "both" {
                       if { $num_sessions < $userArgsArray(vci_count) || $num_sessions < $userArgsArray(vpi_count) } {return -code 1 -errorcode -1 "num_sessions should be bigger than vci_count  and vpi_count when pvc_incr_mode is \"both\""}
                       lappend atmConfigParamList -VciRecycleCount $userArgsArray(vci_count) -IfRecycleCount $userArgsArray(vpi_count) 
                    }
                    "vci" {
                        if { $num_sessions < $userArgsArray(vci_count) * $userArgsArray(vpi_count) } {return -code 1 -errorcode -1 "num_sessions should be bigger than vci_count  * vpi_count when pvc_incr_mode is \"vci\""}
                        lappend atmConfigParamList -VciRecycleCount $userArgsArray(vci_count) -VpiRepeatCount [expr $userArgsArray(vci_count) - 1]
                    }
                    "vpi" {
                        if { $num_sessions < $userArgsArray(vci_count) * $userArgsArray(vpi_count) } {return -code 1 -errorcode -1 "num_sessions should be bigger than vci_count  * vpi_count when pvc_incr_mode is \"vpi\""}
                        lappend atmConfigParamList -VciRepeatCount [expr $userArgsArray(vpi_count) - 1](vci_count) -IfRecycleCount $userArgsArray(vpi_count)
                    }
                }
            }
            if {$atmConfigParamList != ""} {
                if {[catch {::sth::sthCore::invoke stc::config $Aal5If $atmConfigParamList} configStatus]} {
                    set result "Error in $procName while configuring the Aal5If object: $configStatus "
                    return -code 1 -errorcode -1 $result
                }
            }
        }
        
        if {[set EthiiIf [::sth::sthCore::invoke stc::get $host "-children-EthiiIf"]] != ""} {
            set ethConfigParamList ""
            foreach {stcattr hname} {SourceMac mac_addr SrcMacStep mac_addr_step } {
                if {[info exists userArgsArray($hname)]} {
                    lappend ethConfigParamList -$stcattr $userArgsArray($hname)
                }
            }
            if {$ethConfigParamList != ""} {
                if {[catch {::sth::sthCore::invoke stc::config $EthiiIf $ethConfigParamList} configStatus]} {
                    set result "Error in $procName while configuring the EthiiIf object: $configStatus "
                    return -code 1 -errorcode -1 $result
                }
            }
        }
        
        if {[set VlanIf [::sth::sthCore::invoke stc::get $host "-children-VlanIf"]] != ""} {
            if {[llength $VlanIf] == 1} {
                set vlanConfigParamList ""
                foreach {stcattr hname} {VlanId vlan_id IdStep vlan_id_step Priority vlan_user_priority Cfi vlan_cfi tpid vlan_tpid IfRecycleCount vlan_id_count IdRepeatCount vlan_id_repeat_count IfCountPerLowerIf vlan_id_stack_count} {
                    if {[info exists userArgsArray($hname)]} {
                        lappend vlanConfigParamList -$stcattr $userArgsArray($hname)
                    }
                }
                if {[info exists userArgsArray(vlan_id_repeat_count)]} {
                    if {[expr $num_sessions % ($userArgsArray(vlan_id_repeat_count) + 1) != 0]} {
                        return -code 1 -errorcode -1 "-encap is set to ethernet_ii_vlan,then the value of -num_sessions must be divided evenly by value of (-vlan_id_repeat_count + 1)."
                        }
                }
                if {$vlanConfigParamList != ""} {
                    if {[catch {::sth::sthCore::invoke stc::config $VlanIf $vlanConfigParamList} configStatus]} {
                        set result "Error in $procName while configuring the VlanIf object: $configStatus "
                        return -code 1 -errorcode -1 $result
                    }
                }
            } else {
                set vlanConfigParamList ""
                foreach {stcattr hname} {VlanId vlan_id IdStep vlan_id_step tpid vlan_tpid Priority vlan_user_priority Cfi vlan_cfi} {
                    if {[info exists userArgsArray($hname)]} {
                        lappend vlanConfigParamList -$stcattr $userArgsArray($hname)
                    }
                }
                set vlanOuterConfigParamList ""
                foreach {stcattr hname} {VlanId vlan_id_outer IdStep vlan_id_outer_step tpid vlan_tpid_outer Priority vlan_outer_user_priority Cfi vlan_outer_cfi} {
                    if {[info exists userArgsArray($hname)]} {
                        lappend vlanOuterConfigParamList -$stcattr $userArgsArray($hname)
                    }
                }
                if {[info exists userArgsArray(qinq_incr_mode)] && [info exists userArgsArray(vlan_id_outer_count)] && [info exists userArgsArray(vlan_id_count)] } {
                        switch -exact -- $userArgsArray(qinq_incr_mode) {
                            "both" {
                                if { $num_sessions < $userArgsArray(vlan_id_count) || $num_sessions < $userArgsArray(vlan_id_outer_count) } {return -code 1 -errorcode -1 "num_sessions should be bigger than vlan_id_count and vlan_id_outer_count when qinq_incr_mode is \"both\""}
                                lappend vlanConfigParamList  -IfRecycleCount $userArgsArray(vlan_id_count)
                                lappend vlanOuterConfigParamList  -IfRecycleCount $userArgsArray(vlan_id_outer_count)
                            }
                            "inner" {
                                    if { $num_sessions < $userArgsArray(vlan_id_count) * $userArgsArray(vlan_id_outer_count) } {return -code 1 -errorcode -1 "num_sessions should be bigger than vlan_id_count * vlan_id_outer_count when qinq_incr_mode is \"inner\""}
                                    lappend vlanConfigParamList -IfRecycleCount  $userArgsArray(vlan_id_count)
                                    lappend vlanOuterConfigParamList -IdRepeatCount [expr  $userArgsArray(vlan_id_count) -1]
                            }
                            "outer" {
                                    if { $num_sessions < $userArgsArray(vlan_id_count) * $userArgsArray(vlan_id_outer_count) } {return -code 1 -errorcode -1 "num_sessions should be bigger than vlan_id_count * vlan_id_outer_count when qinq_incr_mode is \"outer\""}
                                    lappend vlanConfigParamList -IdRepeatCount [expr $userArgsArray(vlan_id_outer_count) -1]
                                    lappend vlanOuterConfigParamList -IfRecycleCount $userArgsArray(vlan_id_outer_count)
                            }
                        }
                }
                if {$vlanConfigParamList != ""} {
                    if {[catch {::sth::sthCore::invoke stc::config [lindex $VlanIf 0] $vlanConfigParamList} configStatus]} {
                        set result "Error in $procName while configuring the VlanIf object: $configStatus "
                        return -code 1 -errorcode -1 $result
                    }
                }
                if {$vlanOuterConfigParamList != ""} {
                    if {[catch {::sth::sthCore::invoke stc::config [lindex $VlanIf 1] $vlanOuterConfigParamList} configStatus]} {
                        set result "Error in $procName while configuring the VlanIf object: $configStatus "
                        return -code 1 -errorcode -1 $result
                    }
                }
                
                if {$userArgsArray(encap) == "ethernet_ii_mvlan" && [info exists userArgsArray(vlan_id_list)]} {
                    set vlanListConfigParamList ""
                    set i 0
                    set vlanid_list $userArgsArray(vlan_id_list)
                    foreach vlanid $vlanid_list {
                        set subVlanListConfigParamList ""
                        foreach {stcattr hname} {VlanId vlan_id_list RecycleCount vlan_id_count IdStep vlan_id_step_list tpid vlan_tpid_list Priority vlan_user_priority_list Cfi vlan_cfi_list} {
                            if {[info exists userArgsArray($hname)]} {
                                set value [lindex $userArgsArray($hname) $i]
                                if {$value == ""} {
                                    set value $::sth::Pppox::pppox_config_default($hname)
                                }
                                lappend subVlanListConfigParamList -$stcattr $value
                            }
                        }
                        lappend vlanListConfigParamList $subVlanListConfigParamList
                        incr i
                    }
                    
                    set k 0
                    foreach hnd $VlanIf {
                        if {$k > 1} {
                            ::sth::sthCore::invoke stc::config [lindex $VlanIf $k] [lindex $vlanListConfigParamList [expr $k-2]]
                        }
                        incr k
                    }
                }
            }
        }
        
        lappend ports $port
        lappend pppoePorts  $portConfig
        lappend createdPppoeClientBlockConfigs $sessionBlockConfig
    }
    keylset returnKeyedList port_handle $ports
    keylset returnKeyedList handle $userArgsArray(handle);# will now be used for traffic
    keylset returnKeyedList handles $userArgsArray(handle);# will now be used for traffic
    keylset returnKeyedList pppoe_port $pppoePorts
    keylset returnKeyedList pppoe_session $createdPppoeClientBlockConfigs; # used for traffic
    return $returnKeyedList
}

###/*! \ingroup pppoeswitchprocfuncs
###\fn pppox_config_modify (str args)
###\brief Process \em -mode switch with value \em disable for pppox_config cmd
###
###This procedure execute the pppox_config command when the mode is modify. It will delete all pppoe sessions based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList
###
###
###\author Alison Lee (all)
###*/
###
###pppox_config_reset (str args);
###
proc ::sth::Pppox::pppox_config_reset { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    set _OrigHltCmdName "pppox_config"
    set _hltCmdName "pppox_config_modify"

    upvar 1 $returnKeyedListVarName returnKeyedList

    if {! [info exists userArgsArray(handle)]} {
        set result "Handle is a mandatory argument for the \"-mode reset\" option."
        return -code 1 -errorcode -1 $result
    }

    foreach createdHost $userArgsArray(handle) {
    if {[catch {::sth::sthCore::invoke stc::get $createdHost } err]} {
        set result "Error: handle $createdHost does not exist.  Msg: $err"
        #keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }

    # Before we delete the host, grab the associated project and port affiliation so we can delete the local HNDLMAP
    if {[catch {set hltPort [::sth::sthCore::invoke stc::get $createdHost -affiliationPort-targets]} err]} {
        set result "Error: affiliatedPort-target to host $createdHost does not exist.  Msg: $err"
        #keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }
    if {[catch {set hltProjectHandle [::sth::sthCore::invoke stc::get $createdHost -parent]} err]} {
        set result "Error: parent to host $createdHost does not exist.  Msg: $err"
        #keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }
    if {[catch {set PppoxPortConfig [::sth::sthCore::invoke stc::get $hltPort -children-pppoxportconfig]} err]} {
        set result "Error: children-pppoxportconfig to port $hltPort does not exist.  Msg: $err"
        #keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }

    # Delete AddStackIfCommand
    if {[catch { set IfStackAddCommandList [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $createdHost -parent] -parent] -children-IfStackAddCommand] } err]} {
        set result "$err"
        #puts "DEBUG:$result"
        return -code 1 -errorcode -1 $result
    }
    set aisc ""
    foreach aisc $IfStackAddCommandList {
        if {[regexp -nocase ^$createdHost [::sth::sthCore::invoke stc::get $aisc -DeviceList]]} { set createdIfStackAddCommand $aisc; break }
    }

    if {[catch {::sth::sthCore::invoke stc::delete $createdIfStackAddCommand} err ]} {
        ::sth::sthCore::log error "Error deleting previously created Host:$createdHost: $err"
        #puts "DEBUG:Error deleting previously created Host:$createdHost: $err"
    }

    # Host - this deletes things below it but not the IfStackAddCommand since that lives elsewhere
    if { [lsearch -glob [::sth::sthCore::invoke stc::get $createdHost -children] mld*] == -1 && [lsearch -glob [stc::get $createdHost -children] igmp*] == -1 } {
        if {[catch {::sth::sthCore::invoke stc::delete $createdHost} err ]} {
            ::sth::sthCore::log error "Error deleting previously created Host:$createdHost: $err"
            #puts "DEBUG:Error deleting previously created Host:$createdHost: $err"
        }
    }

    # If there now exist no hosts under the project, then delete the local HNDLMAP so that 
    # the pppoePort config will be defaulted on the next mode create
    # If we error out, we still need to complete the apply and remainder of proc
    if {[catch {set curHostList [::sth::sthCore::invoke stc::get $hltProjectHandle -children-host]} err]} {
        ::sth::sthCore::log error "Error deleting previously created Host:$createdHost: $err"
        #puts "DEBUG:Error deleting previously created Host:$createdHost: $err"
    } else {
        if {[llength $curHostList] == "0"} {
            catch {unset PPPOEPORT2PORTHNDLMAP($hltPort)}
            ::sth::Pppox::processPppox_config_defaults port $PppoxPortConfig "" returnKeyedList
        }
    }
    }

    # Make sure the IL is updated for this
    if {[catch {::sth::sthCore::doStcApply } err ]} {
        #::sth::sthCore::log error "Error applying configuration after deleting host \"$createdHost\" and IfStackAddCommand \"$createdIfStackAddCommand\". Msg: $err"
        set result "Error while calling apply: $err"
        #keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }

    if {[info exists userArgsArray(handle)]} {
        keylset returnKeyedList handle $userArgsArray(handle)
        keylset returnKeyedList handles $userArgsArray(handle)
    }

    return $returnKeyedList
}



proc ::sth::Pppox::convertMacHltapi2Stc {mac_value new_mac_value} {
    set procName [lindex [info level [info level]] 0]

    upvar 1 $new_mac_value newMac

    if {[llength [split $mac_value {[\-|.|\:]}]] != 6} {
        if {[llength [split $mac_value {.}]] != 3} {
            return -code 1 -errorcode -1 "Error: Invalid mac ($mac_value)"
        }
        regsub -all {[\:|.|\-]} $mac_value "" newMac
        if {[string length $newMac] != 12} {
            return -code 1 -errorcode -1 "Error: Invalid mac ($mac_value)"
        }
        set newMac_tmp ""
        for {set idx 0} {$idx <= 11} {incr idx 2} {
            set tmp [string range $newMac $idx [expr "$idx+1"]]
            set newMac_tmp "${newMac_tmp}:${tmp}"
        }
        set newMac [string trimleft $newMac_tmp ":"]
    } else {
        regsub -all {[\:|.|\-]} $mac_value ":" newMac
    }

    return $::sth::sthCore::SUCCESS

}
proc ::sth::Pppox::convertMacStc2Hltapi {mac_value new_mac_value} {
    set procName [lindex [info level [info level]] 0]

    upvar 1 $new_mac_value newMac

    if {[llength [split $mac_value {[\-|.|\:]}]] != 6} {
        if {[llength [split $mac_value {.}]] != 3} {
            return -code 1 -errorcode -1 "Error: Invalid mac ($mac_value)"
        }
        regsub -all {[\:|.|\-]} $mac_value "" newMac
        if {[string length $newMac] != 12} {
            return -code 1 -errorcode -1 "Error: Invalid mac ($mac_value)"
        }
        set newMac_tmp ""
        for {set idx 0} {$idx <= 11} {incr idx 2} {
            set tmp [string range $newMac $idx [expr "$idx+1"]]
            set newMac_tmp "$newMac_tmp.$tmp"
        }
        set newMac [string trimleft $newMac_tmp ":"]
    } else {
        regsub -all {[\:|.|\-]} $mac_value ":" newMac
    }

    return $::sth::sthCore::SUCCESS

}


proc ::sth::Pppox::processPppox_config_defaults { mode pppoePort pppoeSessionBlockHandle returnInfoVarName } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    variable PPPOEPORT2PORTHNDLMAP
    variable PPPOEPORT2SESSIONBLOCKHNDLMAP
    variable PPPOEPORTHNDL2PORTMAP
    variable PPPOESESSIONBLOCKHNDL2PORTMAP

    upvar 1 $returnInfoVarName returnKeyedList

    set argumentList_port {};
    set argumentList_sessionBlock {};

    lappend argumentList_port \
                  -Active                      "TRUE" \
                  -EmulationType               "Client" \
                  -ConnectRate                 "100" \
                  -DisconnectRate              "1000" \
                  -SessionOutstanding          "100"
    lappend argumentList_sessionBlock \
                  -Active                      "TRUE" \
                  -PapRequestTimeout           "3" \
                  -MaxPapRequestAttempts       "5" \
                  -ChapChalRequestTimeout      "3" \
                  -ChapAckTimeout              "3" \
                  -MaxChapRequestReplyAttempts "5" \
                  -AutoRetryCount              "65535" \
                  -EnableAutoRetry                   "FALSE" \
                  -PadiTimeout                 "3" \
                  -PadiMaxAttempts             "5" \
                  -PadrTimeout                 "3" \
                  -PadrMaxAttempts             "5" \
                  -TotalClients                "65535" \
                  -EnableRelayAgent            "FALSE" \
                  -RelayAgentType              "RFC_2516" \
                  -CircuitId                   "circuit @c@v@s" \
                  -RemoteOrSessionId           "remote @m@p@g" \
                  -RelayAgentMacAddr           "00:00:00:00:00:00" \
                  -IncludeRelayAgentInPadi             "TRUE" \
                  -IncludeRelayAgentInPadr             "TRUE" \
                  -IpcpEncap                   "IPV4" \
                  -Protocol                    "PPPOE" \
                  -EnableMruNegotiation        "TRUE" \
                  -EnableMagicNum           "TRUE" \
                  -Authentication              "NONE" \
                  -IncludeTxChapId             "TRUE" \
                  -EnableOsi                   "FALSE" \
                  -EnableMpls                 "FALSE" \
                  -MruSize                     "1492" \
                  -EchoRequestGenFreq          "10" \
                  -MaxEchoRequestAttempts      "0" \
                  -LcpConfigRequestTimeout     "3" \
                  -LcpConfigRequestMaxAttempts "5" \
                  -LcpTermRequestTimeout       "3" \
                  -LcpTermRequestMaxAttempts   "10" \
                  -NcpConfigRequestTimeout     "3" \
                  -NcpConfigRequestMaxAttempts "10" \
                  -MaxNaks                     "5" \
                  -UserName                    "anonymous" \
                  -Password                    "pass" \
                  -UsePartialBlockState        "FALSE"
                  #-ServiceName                 ""
                  #-BlockHandle                 "1"


    # Config the PPPoE Port
    # If the port has not already been configured, configure it now with its defaults
    if {($mode == "port" || $mode == "both") && $pppoePort != ""} {
        if {[catch {::sth::sthCore::invoke stc::config $pppoePort "$argumentList_port"} configStatus]} {
            set result "Internal Command Error while configuring PPPoEPort defaults on $pppoePort. Error: $configStatus "
            ::sth::sthCore::log error $result
            #keylset returnKeyedList log $result
            return -code 1 -errorcode -1 $result
        }
    }

    # Configure the PPPoE session block
    if {($mode == "session" || $mode == "both") && $pppoeSessionBlockHandle != ""} {
        if {[catch {::sth::sthCore::invoke stc::config $pppoeSessionBlockHandle "$argumentList_sessionBlock"} configStatus]} {
            set result "Internal Command Error while configuring PPPoESessionBlock defaults on $pppoePort. Error: $configStatus "
            ::sth::sthCore::log error $result
            #keylset returnKeyedList log $result
            return -code 1 -errorcode -1 $result
        }
    }

    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup pppoeswitchprocfuncs
###\fn processPPPOEClearCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic PPPOE Clear Processor
###
###This procedure implements the generic get command. This command is used by all the keys with one on one mapping with the STC attributes. In the args, wherever it says switch, it is supposed to mean key
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###
###\warning None
###\author Alison Lee (all)
###*/
###
###processPPPOEClearCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

# This command will not work as it was not added to the BLL.
proc ::sth::Pppox::processPPPOEClearCmd { modeVal } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    variable PPPOEPORT2PORTHNDLMAP
    variable PPPOEPORT2SESSIONBLOCKHNDLMAP
    variable PPPOEPORTHNDL2PORTMAP
    variable PPPOESESSIONBLOCKHNDL2PORTMAP

    set _OrigHltCmdName "pppox_control"
    set _hltCmdName "pppox_control_$modeVal"

    #::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"

    set returnKeyedList ""
    set grpName $modeVal

    set mode_idx [lsearch $args -mode]
    set args [lreplace $args $mode_idx [expr "$mode_idx+1"]]

    #initializing the cmd specific data, validating switches and user input for each switch
    ::sth::sthCore::cmdInit

    set handle $switchToValue(handle)

    # This needs to be filled in when PPPoE is added
    set cntList { advertisedRouteCnt\
                  lastRecvedUpdateRouteCnt\
                  outstandingRouteCnt\
                  recvedAdvertisedCnt\
                  recvedKeepAliveCnt\
                  recvedNotificationCnt\
                  recvedOpenCnt\
                  recvedUpdateCnt\
                  recvedWithdrawnCnt\
                  TxAdvertisedUpdateCount\
                  sentKeepAliveCnt\
                  sentNotificationCnt\
                  sentOpenCnt\
                  TxWithdrawnUpdateCount\
                  withdrawnRouteCnt\
    }

    #::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"

    if {[catch {::sth::sthCore::doStcClear $handle $cntList} clearStatus ]} {
        set result "Internal Command Error while clearing Stats. Error: $clearStatus"
        #::sth::sthCore::log error $result
        return -code 1 -errorcode -1 $result
    }
    if {[catch {::sth::sthCore::doStcApply } err ]} {
        set result "Internal Command Error while Error applying clear stats. Error: $clearStatus"
        #::sth::sthCore::log error $result
        return -code 1 -errorcode -1 $result
    }
    #::sth::sthCore::log debug "Successfully Cleared Stats."

    return $returnKeyedList
}




###/*! \ingroup pppoeswitchprocfuncs
###\fn processGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic PPPOE Get Processor
###
###This procedure implements the generic get command for PPPOE. This command is used by all the keys with one on one mapping with the STC attributes. In the args, wherever it says switch, it is supposed to mean key
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###
###\warning None
###\author Alison Lee (all)
###*/
###
###processGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Pppox::processPPPOXGetCmd { attr returnInfoVarName keyName handle } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $returnInfoVarName returnKeyedList

    set getValueVar ""
    set stcAttrName [set ::sth::Pppox::pppox_stats_${keyName}_stcattr($attr)]

    if {[catch {set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]} getStatus ]} {
        set result "Internal Command Error while fetching value of $attr. Error: $getStatus"
        #puts "DEBUG:$result"
        keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }

    #@TODO: Add the general encoding function as per requirement
    keylset returnKeyedList ${keyName}.$attr $val

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Pppox::processPPPOXSessionGetCmd { attr returnInfoVarName keyName pppoeSessionId handle } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList

    set getValueVar ""
    set stcAttrName [set ::sth::Pppox::pppox_stats_${keyName}_stcattr($attr)]

    if {[catch {set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]} getStatus ]} {
        set result "Internal Command Error while fetching value of $attr. Error: $getStatus"
        #puts "DEBUG:$result"
        keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }

    #@TODO: Add the general encoding function as per requirement
    keylset returnKeyedList ${keyName}.${pppoeSessionId}.$attr $val

    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup pppoeswitchprocfuncs
###\fn ::sth::Pppox::processPPPOXGetCmd_state(keyedListRef returnInfoVarName, str handle)
###\brief Processes RouteTarget related switches.
###
###This procedure implements the state related parameters. This command is used for multiple mapping with the STC attributes.
###
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] handle The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###
###\warning None
###\author Alison Lee (all)
###*/
###
###::sth::Pppox::processPPPOXGetCmd_state (keyedListRef returnInfoVarName, str handle);
###

proc ::sth::Pppox::processPPPOXGetCmd_state { attr returnInfoVarName keyName handle } {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray

    upvar 1 $returnInfoVarName returnKeyedList

    if {[catch {set stateVal [::sth::sthCore::invoke stc::get $handle -portState]} getStatus]} {
        set result "Internal Error Occured while fetching value of state. Error: $getStatus"
        keylset returnKeyedList log $result
        return -code 1 -errorcode -1 $result
    }

    set connecting 0
    set connected 0
    set disconnecting 0
    set abort 0
    set idle 0
    set server_up 0
    set server_down 0
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
            set aborting 1
        }
        "IDLE*" {
            set idle 1
        }
        "NONE" {
            # Do nothing - No host blocks are configured for PPPoX
        }
        default {
            #::sth::sthCore::log error "__INT_ERROR__: Could not resolve state :$stateVal"
            set result "Could not resolve state: $stateVal"
            keylset returnKeyedList log $result
            return -code 1 -errorcode -1 $result
        }
    }

    #keylset returnKeyedList ${keyName}.$_switchName $stcAttrValue
    keylset returnKeyedList ${keyName}.connecting $connecting
    keylset returnKeyedList ${keyName}.connected $connected
    keylset returnKeyedList ${keyName}.disconnecting $disconnecting
    keylset returnKeyedList ${keyName}.abort $abort
    keylset returnKeyedList ${keyName}.idle $idle
    #keylset returnKeyedList ${keyName}.state [string tolower $stateVal]; #undocumented
    #keylset returnKeyedList ${keyName}.server_up $server_up
    #keylset returnKeyedList ${keyName}.server_down $server_down

    return $::sth::sthCore::SUCCESS
}



###}; #ending for namespace comment for doc
proc ::sth::Pppox::int2bits {i {digits {} } } {
        #returns a bitslist, e.g. int2bits 10 => {1 0 1 0}
        # digits determines the length of the returned list (left truncated or added left 0 )
        # use of digits allows concatenation of bits sub-fields

        set res ""
        while {$i>0} {
                set res [expr {$i%2}]$res
                set i [expr {$i/2}]
        }
        if {$res==""} {set res 0}

        if {$digits != {} } {
                append d [string repeat 0 $digits ] $res
                set res [string range $d [string length $res ] end ]
        }
        #split $res ""
}

proc ::sth::Pppox::MACToDouble {mac} {
    set macDouble 0.0
    set shift 40
    
    if {[string match *:* $mac]} {
        set macaddr [split $mac :]
    } elseif {[string match *-* $mac]} {
        set macaddr [split $mac -]
    } else {
        set macaddr ""
        set macaddrTemp [split $mac .]
	set dot4Flag 0
        foreach w $macaddrTemp {
            if {[string length $w] == 4} {
                set w1 [string range $w 0 1]
                set w2 [string range $w 2 3]
                set macaddr [concat $macaddr $w1]
                set macaddr [concat $macaddr $w2]
		set dot4Flag 1
            }
        }
	if {$dot4Flag == 0} {
	    set macaddr $macaddrTemp
	}
    }
    
    foreach w $macaddr {
        set v [expr {"0x$w" * pow(2,$shift)}]
        set macDouble [format %f [expr {$macDouble + $v}]]
        incr shift -8
    }
    # default format is %g which looses precision
    return [format %f $macDouble]
}

proc ::sth::Pppox::DoubleToMAC {macDouble} {
    set macList ""
    for {set i 1} {$i <= 6} {incr i} {
        set modulus [expr {pow(2,(8*$i))}]
        set rem [expr {$macDouble - (floor($macDouble / $modulus)*$modulus)}]
        set macDouble [expr {$macDouble - $rem}]
        set word [expr {int($rem / pow(2,(8*($i-1))))}]
        set macList [concat [format %02x $word] $macList]
    }
    return [join $macList :]
}

proc ::sth::Pppox::MACIncr {start step {count 1}} {
   
    set maxD [MACToDouble FF.FF.FF.FF.FF.FF]
    set startD [MACToDouble $start]
    set stepD  [MACToDouble $step]
    set resD   [expr {$startD + ($stepD * $count)}]
    
    return [DoubleToMAC $resD]
}

proc ::sth::Pppox::IPv4ToInt { ipAddr } {
   set val 0
   foreach field [split $ipAddr .] {
      set val [expr "(wide($val)<<8) + $field"]
   }
   return $val
}

proc ::sth::Pppox::IntToIPv4 { val } {
   return "[expr ($val>>24)&0xff].[expr ($val>>16)&0xff].[expr ($val>>8)&0xff].[expr $val&0xff]"
}

proc ::sth::Pppox::IncrIPv4 { ipAddr ipAddrStep {count 1} } {
   set start [IPv4ToInt $ipAddr]
   set step [IPv4ToInt $ipAddrStep]

   set val [expr "$start+($step*$count)"]
   return [IntToIPv4 $val]
}



