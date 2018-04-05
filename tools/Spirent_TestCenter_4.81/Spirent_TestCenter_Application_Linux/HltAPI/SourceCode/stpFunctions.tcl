
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Stp {
    # a global variable indicating whether to subscribe stp result objects
    variable stp_subscription_state 0
    set applyFlag 1
}

proc ::sth::Stp::emulation_stp_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_stp_config_create"

    variable ::sth::Stp::userArgsArray
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
         
        
        # set the default value for stp_type
        if {![info exists userArgsArray(stp_type)]} {
            set userArgsArray(stp_type) "stp"
        }
        # create encapsulation stack by -protocol and -encap 
        if {[regexp -nocase "ipv4" $userArgsArray(ip_version)]} {
            set ipVersion "ipv4"
            set topif "Ipv4If"
            set ifCount "1"
        } elseif {[regexp -nocase "ipv6" $userArgsArray(ip_version)]} {
            set ipVersion "ipv6"
            set topif "Ipv6If"
            set ifCount "1"
        } else {
            # the interface does not have the L3 layer encapsulation
            set ipVersion "none"
            set topif ""
            set ifCount ""
        }
        
        
        # create encapsulation stack by -encap 
        set encap $userArgsArray(encap)
        
        switch -- $encap {
            "ethernet_ii" {
                set IfStack "$topif EthIIIf"
                set IfCount "$ifCount 1"
            }
            "ethernet_ii_vlan" {
                set IfStack "$topif VlanIf EthIIIf"
                set IfCount "$ifCount 1 1"
            }
            "ethernet_ii_qinq" {
                set IfStack "$topif VlanIf VlanIf EthIIIf"
                set IfCount "$ifCount 1 1 1"
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -encap $encap" {}
                return -code error $returnKeyedList  
            }
        }
        
        # create device
        set createdDeviceList ""
        
        for {set i 0} {$i < $userArgsArray(count)} {incr i} {
            array set DeviceCreateOutput [::sth::sthCore::invoke "stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) \
	    						-DeviceType Host \
							-IfStack \"$IfStack\" \
							-IfCount \"$IfCount\" \
							-Port $portHandle"]
            set createdHost $DeviceCreateOutput(-ReturnList)
            
            lappend createdDeviceList $createdHost
            
            # adjust link local interface for ipv6 case
            if {[string match -nocase "ipv6" $ipVersion]} {
                         
                #### ipv6 encap stack map ####
                #
                #            'toplevelIf'           UsesIf
                #         emulateddevice1 -----> ipv6if1  <------- BridgeportConfig
                #              |                    |
                # 'toplevelIf' |                    |
                # 'PrimaryIf'  |                    |
                #              |                    |
                #   ipv6if2(linklocal)--------> vlanIf1 ---> vlanIf2 ---> ethIIIf1
                #
                #
                ####
                #  link local ipv6 interface faces to the DUT
                #  global ipv6 interface faces to BridgeportConfig
                ####

                set ipv6If [::sth::sthCore::invoke stc::get $createdHost -children-ipv6if]
                set lowerIf [::sth::sthCore::invoke stc::get $ipv6If -StackedOnEndpoint-targets]
            
                # create new ipv6if
                set cfglist "-Address fe80::1 -AddrStep ::1 -PrefixLength 64"
                set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $createdHost "$cfglist -toplevelIf-sources $createdHost -StackedOnEndpoint-targets $lowerIf"]
                ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
                ::sth::sthCore::invoke stc::config $createdHost "-primaryif-targets $linkLocalIf"
            }
            
            
            
            set ipStack [::sth::sthCore::invoke stc::get $createdHost -children-$topif]
            
            set ipStack [lindex $ipStack 0]
            # Create BridgePortConfig
            set BridgePortConfig [::sth::sthCore::invoke stc::create BridgeportConfig -under $createdHost "-UsesIf-targets $ipStack"]
            
            #### Config input switches ####
            ::sth::Stp::processConfigSwitches emulation_stp_config $createdHost create $ipVersion returnKeyedList
            
	    #updaet the value using the step
	    ::sth::Stp::processParamsStep $ipVersion
	    
            # adjuct the default config if multi devices created on one port
            if { $i > 0} {
                ::sth::Stp::adjuctDefaultCfg $BridgePortConfig $i
            }
            
        }
        
        
        # create the result dataset if the stp type is not mstp, or else do this after creating the regions
        if {![string match -nocase $userArgsArray(stp_type) "mstp"]} {
            if {$::sth::Stp::stp_subscription_state == 0} {
                # Create the stp result dataset
                set stpResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            } else {
                set stpResultDataSet [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]
            }
            if {$::sth::Stp::stp_subscription_state == 0} {
                set stpResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $stpResultDataSet \
								"-ResultRootList $::sth::GBLHNDMAP(project) \
								-ConfigClassId BridgePortConfig \
								-ResultClassId BridgePortResults "]
                
                set stpResultQuery(2) [::sth::sthCore::invoke stc::create "ResultQuery" -under $stpResultDataSet \
								"-ResultRootList $::sth::GBLHNDMAP(project) \
								-ConfigClassId MstiConfig \
								-ResultClassId BridgePortResults"]
            }
                        
            #apply all configurations
            if {[catch {::sth::sthCore::doStcApply} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying Stp configuration: $err"
                return $returnKeyedList
            }
            
            if {$::sth::Stp::stp_subscription_state == 0} {
                ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $stpResultDataSet
                set ::sth::Stp::stp_subscription_state 1
            }
        }
        
        
    
    } returnedString]
    
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any device created if error occurs
        if {[info exists createdDeviceList]} {
            foreach device $createdDeviceList {
                ::sth::sthCore::invoke stc::delete $device
            }
        }
    } else {
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList handle $createdDeviceList 
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}

proc ::sth::Stp::emulation_stp_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_stp_config_modify"

    variable ::sth::Stp::userArgsArray
    variable ::sth::Stp::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set hostHandleList $userArgsArray(handle)
            foreach hostHandle $hostHandleList {
                if {![IsStpHandleValid $hostHandle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not valid STP handle" {}
                    return -code error $returnKeyedList 
                }
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        
        # checking unsupported switches under "modify" mode
        set unsupportedModifyOptions {port_handle ip_version encap count}
        
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
            set port [::sth::sthCore::invoke stc::get $hostHandle "-AffiliationPort-targets"]
            
            set childList [::sth::sthCore::invoke stc::get $hostHandle -children]
            if {[regexp -- "ipv4if" $childList]} {
                set ipVersion "ipv4"
            } elseif {[regexp -- "ipv6if" $childList]} {
                set ipVersion "ipv6"
            } else {
                set ipVersion "none"
            }  
            
            ::sth::Stp::processConfigSwitches emulation_stp_config $hostHandle modify $ipVersion returnKeyedList  
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

proc ::sth::Stp::emulation_stp_config_delete { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_stp_config_delete"
    
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
            if {![IsStpHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid stp handle" {}
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


proc ::sth::Stp::emulation_stp_config_enable {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_stp_config_enable"

    variable ::sth::Stp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch { 
        foreach deviceHandle $userArgsArray(handle) {  
            if {![IsStpHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not a valid STP device handle" {}
                return -code error $returnKeyedList 
            }
        
            #get BridgePortConfig
            set BridgePortCfgHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BridgePortConfig ]
            #active stp
            ::sth::sthCore::invoke stc::config $BridgePortCfgHdl "-Active TRUE"
        }
        
        keylset returnKeyedList handle $userArgsArray(handle)

    } returnedString]
    
    return -code $retVal $returnedString
}


proc ::sth::Stp::emulation_stp_config_disable {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_stp_config_disable"

    variable ::sth::Stp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch {
        foreach deviceHandle $userArgsArray(handle) {        
            if {![IsStpHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not a valid STP device handle" {}
                return -code error $returnKeyedList 
            }
        
            set BridgePortCfgHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BridgePortConfig ]
         
            ::sth::sthCore::invoke stc::config $BridgePortCfgHdl "-Active FALSE"
        }
        keylset returnKeyedList handle $userArgsArray(handle)
        
    } returnedString]
    
    return -code $retVal $returnedString
}



proc ::sth::Stp::emulation_mstp_region_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_mstp_region_config_create"

    variable ::sth::Stp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        # port_handle is mandatory for the -mode create
        if {[info exists userArgsArray(port_handle)]} {
            set portHdlList $userArgsArray(port_handle)
            set stpPortHdlList ""
            foreach portHdl $portHdlList {
                if {![::sth::sthCore::IsPortValid $portHdl Msg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid value of \"-port_handle\" $portHdl"
                    return $returnKeyedList
                }
                
                #check if the port is already specified as running mstp
                set stpPortCfg [::sth::sthCore::invoke stc::get $portHdl -children-StpPortConfig]
                set stpTyp [::sth::sthCore::invoke stc::get $stpPortCfg -StpType]
                if {![string match -nocase "mstp" $stpTyp]} {
                    ::sth::sthCore::processError returnKeyedList "Error: The emulation_mstp_region_config Can only be configured on those ports already specified as running MSTP."
                    return $returnKeyedList
                } else {
                    lappend stpPortHdlList $stpPortCfg
                }
            }
            
            #check if the elements number of mstp_instance_vlan_list and mstp_instance_num_list is equal
            if {!([info exists userArgsArray(mstp_instance_vlan_list)] && [info exists userArgsArray(mstp_instance_num_list)])} {
                ::sth::sthCore::processError returnKeyedList "Error: Options \"mstp_instance_vlan_list\" and \"mstp_instance_num_list\" should be specified in the create mode of emulation_mstp_region_config."
                return $returnKeyedList
            } elseif {[llength $userArgsArray(mstp_instance_vlan_list)] != [llength $userArgsArray(mstp_instance_num_list)] || [llength $userArgsArray(mstp_instance_vlan_list)] != $userArgsArray(mstp_instance_count)} {
                    ::sth::sthCore::processError returnKeyedList "Error: The element number of \"mstp_instance_vlan_list\" , \"mstp_instance_num_list\"  and \"mstp_instance_count\" should be equal."
                    return $returnKeyedList
            }
            
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -port_handle is required when \"-mode create\" is used."
            return $returnKeyedList
        }
        
        set mstiDefaultCnfList {}
        lappend mstiDefaultCnfList -MstInstanceCount $userArgsArray(mstp_instance_count) -InstanceNumList $userArgsArray(mstp_instance_num_list) -InstanceVlanList $userArgsArray(mstp_instance_vlan_list)
        # create region and create relations of port
        set mstpRegionHdl [::sth::sthCore::invoke stc::create MstpRegionConfig -under $::sth::GBLHNDMAP(project) "-memberof-targets {$stpPortHdlList} $mstiDefaultCnfList"]
        
        #### create the default msti configuration ####
         set mstiHdlList [::sth::Stp::processConfigMsti create $portHdlList port returnKeyedList]
        
        #### Config input switches ####
        ::sth::Stp::processConfigSwitches emulation_mstp_region_config $mstpRegionHdl create null returnKeyedList
        
        
        #need to check if all the ports created with mstp type have configured mstp region related by "memberof-targets", apply after meeting this requirements. 
        #get all the port under this project
        
        set portHdlList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-port]
        foreach portHdl $portHdlList {
            set stpPortCfg [::sth::sthCore::invoke stc::get $portHdl -children-StpPortConfig]
            set stpTyp [::sth::sthCore::invoke stc::get $stpPortCfg -StpType]
            if {![string match -nocase "mstp" $stpTyp]} {
                continue
            } else {
                #check if the mstp region has been created
                set regionHdl [::sth::sthCore::invoke stc::get $stpPortCfg -memberof-Sources]
                if {$regionHdl == ""} {
                    set ::sth::Stp::applyFlag 0
                }
            }
        }
        
        
        
        if { $::sth::Stp::applyFlag == 1 }  {
            if {$::sth::Stp::stp_subscription_state == 0} {
                # Create the stp result dataset
                set stpResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            } else {
                set stpResultDataSet [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]
            }
            if {$::sth::Stp::stp_subscription_state == 0} {
                set stpResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $stpResultDataSet \
								"-ResultRootList $::sth::GBLHNDMAP(project) \
								-ConfigClassId BridgePortConfig \
								-ResultClassId BridgePortResults "]
                
                set stpResultQuery(2) [::sth::sthCore::invoke stc::create "ResultQuery" -under $stpResultDataSet \
								"-ResultRootList $::sth::GBLHNDMAP(project) \
								-ConfigClassId MstiConfig \
								-ResultClassId BridgePortResults"]
            }
                        
            #apply all configurations
            if {[catch {::sth::sthCore::doStcApply} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying Stp configuration: $err"
                return $returnKeyedList
            }
        
            if {$::sth::Stp::stp_subscription_state == 0} {
                ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $stpResultDataSet
                set ::sth::Stp::stp_subscription_state 1
            }
         
        }
    } returnedString]
    
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any device created if error occurs
        if {[info exists mstpRegionHdl]} {
            foreach region $mstpRegionHdl {
                #need to check again
                ::sth::sthCore::invoke stc::delete $mstpRegionHdl
            }
        }
    } else {
        keylset returnKeyedList port_handle $portHdlList
        keylset returnKeyedList reg_handle $mstpRegionHdl
        keylset returnKeyedList msti_handle $mstiHdlList
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}



proc ::sth::Stp::emulation_mstp_region_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_mstp_region_config_modify"

    variable ::sth::Stp::userArgsArray
    variable ::sth::Stp::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set regionHandle $userArgsArray(handle)
            if {![IsMstpRegionHandleValid $regionHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $regionHandle is not valid mstp region handle" {}
                return -code error $returnKeyedList 
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList
        }
        
        # modify input arguments
        ::sth::Stp::processConfigSwitches emulation_mstp_region_config $regionHandle modify null returnKeyedList  
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList handle $regionHandle   
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}



proc ::sth::Stp::emulation_mstp_region_config_delete { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_mstp_region_config_delete"

    variable userArgsArray
    variable sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }
        
        set regionHandleList $userArgsArray(handle)
        
        foreach regionHandle $regionHandleList {
            if {![IsMstpRegionHandleValid $regionHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $regionHandle is not valid mstp region handle" {}
                return -code error $returnKeyedList 
            }
            
            ::sth::sthCore::invoke stc::delete $regionHandle
        }
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}


proc ::sth::Stp::emulation_msti_config {returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_msti_config"

    variable ::sth::Stp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            # if handle is specified, use the handle directly, then the port handle and instance number are not workable;
            # if not, get the msti handle by the port and instance number
            set mstiHdlList $userArgsArray(handle)
        } elseif {[info exists userArgsArray(port_handle)]} {
            set portHdlList $userArgsArray(port_handle)
            set stpPortHdlList ""
            foreach portHdl $portHdlList {
                if {![::sth::sthCore::IsPortValid $portHdl Msg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid value of \"-port_handle\" $portHdl"
                    return $returnKeyedList
                }
                
                #check if the port is already specified as running mstp
                set stpPortCfg [::sth::sthCore::invoke stc::get $portHdl -children-StpPortConfig]
                set stpTyp [::sth::sthCore::invoke stc::get $stpPortCfg -StpType]
                if {![string match -nocase "mstp" $stpTyp]} {
                    ::sth::sthCore::processError returnKeyedList "Error: The emulation_mstp_region_config Can only be configured on those ports already specified as running MSTP."
                    return $returnKeyedList
                } else {
                    lappend stpPortHdlList $stpPortCfg
                }
            }
            
            # get the msti handles under the specified port
            set mstiHdlList [ ::sth::Stp::processConfigMsti get $portHdlList port returnKeyedList ]
            
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -port_handle or handle is required."
            return $returnKeyedList
        }
        
        
        #### Config input switches ####
        ::sth::Stp::processConfigSwitches emulation_msti_config $mstiHdlList modify null returnKeyedList
        
        
    } returnedString]
    
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList handle $mstiHdlList 
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}


proc ::sth::Stp::processConfigSwitches {userfunName handleList mode ipVersion returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    upvar $returnList returnKeyedList

    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Stp:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Stp:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Stp:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    #### used for msti modify ####
    if {[info exists userArgsArray(msti_instance_num)]} {
        set userInstanceNum $userArgsArray(msti_instance_num)
    } else {
        #set the default value 1 for msti_instance_num, although the defaut value provided by stc is 0
        set userInstanceNum 1
    }
    ###############################
    
    foreach deviceHandle $handleList {
        #actually, only msti hanlde is a list, others are one handle
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    set ethiiIf [::sth::sthCore::invoke stc::get $deviceHandle -children-EthIIIf]
                    if {[string length $ethiiIf] != 0} {
                        configEthIIIntf $ethiiIf $mode
                    }
                }
                configVlanIfInner {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 0]
                        }
                        configVlanIfInner $vlanIf $mode
                    }
                }
                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] < 2} {continue}            
                        set vlanIf [lindex $vlanIf 1]
                        configVlanIfOuter $vlanIf $mode
                    }
                }
                configIpIntf {
                    set ipIf [::sth::sthCore::invoke stc::get $deviceHandle -children-${ipVersion}if]
                    if {[llength $ipIf] != 0} {
                        if {[llength $ipIf] > 1} {
                            # get global ipv6if 
                            set ipIf [lindex $ipIf 0] 
                        }
                        configIpIntf $ipIf $mode
                    }
                }
                configStpPortConfig {
                    #get the port handle from the device handle
                    set portHdl [::sth::sthCore::invoke stc::get $deviceHandle -AffiliationPort-targets]
                    set stpPortHdl [::sth::sthCore::invoke stc::get $portHdl -children-StpPortConfig]
                    if {[string length $stpPortHdl] != 0} {
                        StpCommonConfig emulation_stp_config configStpPortConfig $stpPortHdl $mode returnKeyedList
                    }
                }
                configBridgePortConfig {
                    set bridgePortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BridgeportConfig]
                    if {[string length $bridgePortHdl] != 0} {
                        StpCommonConfig emulation_stp_config configBridgePortConfig $bridgePortHdl $mode returnKeyedList
                    }
                }
                configVlanBlockConfig {
                    set bridgePortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BridgePortConfig]
                    set stpBridgePortHdl [::sth::sthCore::invoke stc::get $bridgePortHdl -children-StpBridgePortConfig]
                    set vlanBlockHdl [::sth::sthCore::invoke stc::get $stpBridgePortHdl -children-VlanBlock]
                    if {[string length $vlanBlockHdl] != 0} {
                        StpCommonConfig emulation_stp_config configVlanBlockConfig $vlanBlockHdl $mode returnKeyedList
                    }
                }
                configMstpBridgePortConfig {
                    set bridgePortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BridgePortConfig]
                    set mstpBridgePortHdl [::sth::sthCore::invoke stc::get $bridgePortHdl -children-MstpBridgePortConfig]
                    if {[string length $mstpBridgePortHdl] != 0} {
                        StpCommonConfig emulation_stp_config configMstpBridgePortConfig $mstpBridgePortHdl $mode returnKeyedList
                    }
                }
                configMstpRegionConfig {
                    # the element in the $handleList is the region handle for emulation_mstp_region_config
                    if {[string length $deviceHandle] != 0} {
                        StpCommonConfig emulation_mstp_region_config configMstpRegionConfig $deviceHandle $mode returnKeyedList
                    }
                }
                configMstiConfig {
                    # the element in the $handleList is the msti handle for emulation_msti_config
                    # get the msti instance handle which has the same instance number as the specified value from user input
                    set instanceNum [::sth::sthCore::invoke stc::get $deviceHandle -InstanceNum]

                    if { $instanceNum == $userInstanceNum  || [info exists userArgsArray(handle)]} {
                        StpCommonConfig emulation_msti_config configMstiConfig $deviceHandle $mode returnKeyedList
                        break
                    }
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
}


# internal functions for emulation_stp_config
proc ::sth::Stp::StpCommonConfig { userFunc func cfghdl mode returnList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    upvar $returnList returnKeyedList
    
    if {[string length $cfghdl] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    
    set optionValueList [getStcOptionValueList $userFunc $func $mode $cfghdl]
    
    #specially handling for configStpPortConfig part
    if {[string match -nocase "configStpPortConfig" $func]} {
        #add some mandatory value for enable_pt2pt_link
        #for stp type: false, for pvst, rpvst, mstp: true, for rstp it can be configured and default value is false
        switch -- $userArgsArray(stp_type) {
            "stp" {
                lappend optionValueList -EnablePt2PtLink false
            }
            "pvst" -
            "rpvst" -
            "mstp" {
                lappend optionValueList -EnablePt2PtLink true
            }
            "rstp" {
            }
        }
        #need to check the port type for pvst and rpvst if native vlan is configured
        if {[info exists userArgsArray(native_vlan)]} {
            if {[info exists userArgsArray(port_type)] && ![string match -nocase "trunk" $userArgsArray(port_type)]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: native vlan is workable only when the port type is set to trunk" {}
                return -code error $returnKeyedList
            }
        }
    }
    
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $cfghdl $optionValueList
    }
}



#for mode create: to create the msti handle under current port handle or device handle
#for mode get: to get the msti handle under current port handle or device handle
#type is port or device: to determine the handle is port handle or device handle
proc ::sth::Stp::processConfigMsti {mode HandleList type returnList} {
    
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    upvar $returnList returnKeyedList
    
    set deviceHdlList ""
    set mstiHdlList ""
    
    
    #1.get the device handles under the port or from the parameters
    if {[string match -nocase "port" $type]} {
        foreach portHdl $HandleList {
            set deviceHdl [::sth::sthCore::invoke stc::get $portHdl -affiliationport-Sources]
            lappend deviceHdlList $deviceHdl
        }
    } else {
            set deviceHdlList $HandleList
    }
    
    # update the device handle list to get the mstp handle only
    foreach deviceHdl [join $deviceHdlList] {
        if {![::sth::Stp::IsStpHandleValid $deviceHdl]} {continue}
        lappend stpDeviceHdlList $deviceHdl
    }

    foreach deviceHdl $stpDeviceHdlList {
        set bridgePortHdl [::sth::sthCore::invoke stc::get $deviceHdl -children-BridgeportConfig]
        set mstpBridgePortHdl [::sth::sthCore::invoke stc::get $bridgePortHdl -children-MstpBridgePortConfig]
        
        switch -- $mode {
            create {
                #creat the msti by the mstp_instance_num_list
                for {set i 0} {$i < $userArgsArray(mstp_instance_count)} {incr i} {
                    set mstiHdl [::sth::sthCore::invoke stc::create msticonfig -under $mstpBridgePortHdl]
                    lappend mstiHdlList $mstiHdl
                }
            }
            get {
                set mstiHdl [::sth::sthCore::invoke stc::get $mstpBridgePortHdl -children-Msticonfig]
                lappend mstiHdlList $mstiHdl
            }
            default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown mode: $mode" {}
                    return -code error $returnKeyedList 
            }
        }
    }
    return [join $mstiHdlList]
}



#configEthIIIntf, configVlanIfInner, configVlanIfOuter, configIpIntf is common config for different protocols, to create the protcol stack
proc ::sth::Stp::configEthIIIntf { ethHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $ethHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_stp_config configEthIIIntf $mode $ethHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::Stp::configVlanIfInner { vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    
    if {[string length $deviceHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_stp_config configVlanIfInner $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Stp::configVlanIfOuter { vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    
    if {[string length $vlanHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_stp_config configVlanIfOuter $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Stp::configIpIntf { ipIfHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    if {[string length $ipIfHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_stp_config configIpIntf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}


proc ::sth::Stp::processConfigFwdCmd { myswitch value } {

    # get forward map for "constant" property 
    set fwdValue [::sth::sthCore::getFwdmap ::sth::Stp:: emulation_stp_config $myswitch $value]
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Stp:: emulation_stp_config $myswitch stcattr]
    
    return "-$stcAttr $fwdValue"
}


proc ::sth::Stp::processConfigCmd_vlanId { myswitch value } {
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
        if {$userArgsArray(encap) == "ethernet_ii_qinq"} {
            switch -exact -- $qinqIncrMode {
                "inner" {
                    lappend vlanCfg -IfRecycleCount $count
                }
                "outer" {
                    if {[expr $outer_count-1] > 0} {
                        lappend vlanCfg -IdRepeatCount [expr $outer_count-1] -IfRecycleCount $count
                    } else {
                        lappend vlanCfg  -IfRecycleCount $count
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
        
        switch -exact -- $qinqIncrMode {
            "inner" {
                if {[expr $count-1] > 0} {
                    lappend vlanCfg -IdRepeatCount [expr $count-1] -IfRecycleCount $outer_count
                } else {
                    lappend vlanCfg  -IfRecycleCount $outer_count
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


###################################### emulation_stp_control ####################################
#start and stop bridge_port, cist and msti
proc ::sth::Stp::emulation_stp_control { returnKeyedListVarName } {
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    set procName [lindex [info level [info level]] 0]
    
    # has checked if the action is configured by user in stp.tcl file
    set action $userArgsArray(action)
    
    set retVal [catch {
        #get the device handle by the port_handle or handle to start
        set deviceHandleList ""
        if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
            if {![::sth::Stp::IsStpHandleValid $userArgsArray(handle)]} {
                ::sth::sthCore::processError returnKeyedList "Error: $userArgsArray(handle) is not valid Stp handle" {}
                return -code error $returnKeyedList
            }
            set deviceHandleList $userArgsArray(handle)         
                    
        } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
            foreach port $userArgsArray(port_handle) {
                if {[::sth::sthCore::IsPortValid $port err]} {
                    set deviceHdlList [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                    return -code error $returnKeyedList
                }
                foreach deviceHandle $deviceHdlList {
                    if {![::sth::Stp::IsStpHandleValid $deviceHandle]} { continue }
                    lappend deviceHandleList $deviceHandle
                }
            }
        }
        
        #different commands for different types
        switch -- $userArgsArray(type) {
            bridge_port {
                set bridgePortList ""
                #get the command
                switch -- $action {
                    start {
                        set command "DeviceStart"
                    }
                    stop {
                        set command "DeviceStop"
                    }
                    init_topo_change {
                        set command "StpInitTopoChangeBridgePort"
                    }
                    default {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -action $action" {}
                        return -code error $returnKeyedList  
                    }
                }
                if {[string match -nocase "start" $action] || [string match -nocase "stop" $action]} {
                    ::sth::sthCore::invoke stc::perform $command -DeviceList $deviceHandleList
                } else {
                    #sepcially handling for StpInitTopoChangeBridgePortCommand
                    #get bridge port handle
                    foreach deviceHdl $deviceHandleList {
                        set bridgePortCfg [::sth::sthCore::invoke stc::get $deviceHdl -children-BridgePortConfig]
                        lappend bridgePortList $bridgePortCfg
                    }
                    
                    ::sth::sthCore::invoke stc::perform $command -BridgePortConfigList $bridgePortList
                }
                
               
                
            }
            cist {
                # get the bridge port config handle
                set bridgePortList ""
                #get the command
                switch -- $action {
                    start {
                        set command "StpStartCist"
                    }
                    stop {
                        set command "StpStopCist"
                    }
                    init_topo_change {
                        set command "StpInitTopoChangeCist"
                    }
                    default {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -action $action" {}
                        return -code error $returnKeyedList  
                    }
                }
                foreach deviceHdl $deviceHandleList {
                    set bridgePortCfg [::sth::sthCore::invoke stc::get $deviceHdl -children-BridgePortConfig]
                    lappend bridgePortList $bridgePortCfg
                }
                #start the command
                ::sth::sthCore::invoke stc::perform $command -MstpBridgePortConfigList $bridgePortList
                
            }
            msti {
                #get the command
                switch -- $action {
                    start {
                        set command "StpStartMsti"
                    }
                    stop {
                        set command "StpStopMsti"
                    }
                    init_topo_change {
                        set command "StpInitTopoChangeMsti"
                    }
                    default {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -action $action" {}
                        return -code error $returnKeyedList  
                    }
                }
                # get the msti handle
                set mstiHdlList [ ::sth::Stp::processConfigMsti get $deviceHandleList device returnKeyedList ]
                
                #start the command
                ::sth::sthCore::invoke stc::perform $command -MstiConfigList $mstiHdlList
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -type $userArgsArray(type)" {}
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




proc ::sth::Stp::emulation_stp_stats { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Stp::userArgsArray

    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        
        set deviceHandleList ""
            
        if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
            foreach handle $userArgsArray(handle) {
                if {![::sth::Stp::IsStpHandleValid $handle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $handle is not valid stp handle" {}
                    return -code error $returnKeyedList
                }
                lappend deviceHandleList $handle
            }
                    
        } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
            foreach port $userArgsArray(port_handle) {
                if {[::sth::sthCore::IsPortValid $port err]} {
                    set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                    foreach device $deviceHandle {
                        if {![::sth::Stp::IsStpHandleValid $device]} {
                            continue
                        } else {
                            lappend deviceHandleList $device
                        }
                    }
                }
            }
        }
        
        foreach device $deviceHandleList {
            set bridgePortCfg [::sth::sthCore::invoke stc::get $device -children-BridgePortConfig]
            
            #get bridgePort result
            set bridgePortResults [::sth::sthCore::invoke stc::get $bridgePortCfg -children-BridgePortResults]
            
            
            set mstpBridgePortCfg ""
            set mstiResultsList ""
            set mstpBridgePortCfg [::sth::sthCore::invoke stc::get $bridgePortCfg -children-MstpBridgePortConfig]
            
            if { $mstpBridgePortCfg != "" } {
                set mstiCfgList [::sth::sthCore::invoke stc::get $mstpBridgePortCfg -children-MstiConfig]
                
                #get msti config results for mstp type
                foreach mstiCfg $mstiCfgList {
                    set mstiResults [::sth::sthCore::invoke stc::get $mstiCfg -children-BridgePortResults]
                    lappend mstiResultsList $mstiResults
                }
            }
           
            
            # create an array mapping between stcObj and stcHandle
            set hdlArray1(BridgePortResults) $bridgePortResults
            set hdlArray2(BridgePortResults) $mstiResultsList
            
            set mode $userArgsArray(mode)
            
            
            foreach key [array names ::sth::Stp::emulation_stp_stats_mode] {
                foreach {tblMode tblProc} $::sth::Stp::emulation_stp_stats_mode($key) {
                    if {[string match $tblMode $mode]} {
                        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Stp:: emulation_stp_stats $key supported] "false"]} {
                            continue
                        }
                        if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::Stp:: emulation_stp_stats $key stcattr]] "_none_"]} {
                            continue
                        }
                            
                        if {$tblMode == "stp" || $tblMode == "both"} {
                            if {[catch {set stcObj [::sth::sthCore::getswitchprop ::sth::Stp:: emulation_stp_stats $key stcobj]} err]} {
                                ::sth::sthCore::processError returnKeyedList "emulation_stp_stats $key Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set obj $hdlArray1($stcObj)
                            if { $obj != "" } {
                                set val [::sth::sthCore::invoke stc::get $obj -$stcAttr]
                                
                                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "stp.$device.$key" $val]
                            }
                        }
                        
                        if {$tblMode == "msti" || $tblMode == "both"} {
                            if {[catch {set stcObj [::sth::sthCore::getswitchprop ::sth::Stp:: emulation_stp_stats $key stcobj]} err]} {
                                ::sth::sthCore::processError returnKeyedList "emulation_stp_stats $key Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set objList $hdlArray2($stcObj)
                            if { $objList != ""} {
                                foreach obj $objList {
                                    set val [::sth::sthCore::invoke stc::get $obj -$stcAttr]
                                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "msti.$device.$obj.$key" $val]
                                }
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

      
#put the options with the same ModeFunc in the same list
proc ::sth::Stp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    set procName [lindex [info level [info level]] 0]
    set optionValueList {}
    
    foreach item $::sth::Stp::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Stp:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Stp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Stp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::Stp::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::Stp::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Stp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Stp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Stp:: $cmdType $opt $::sth::Stp::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::Stp::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $opt $::sth::Stp::userArgsArray($opt)]
                }
            }
    }
    
    return $optionValueList
}


proc ::sth::Stp::IsMstpRegionHandleValid { handle } {
    set procName [lindex [info level [info level]] 0]
    set cmdStatus 0
    
    if {[catch {set mstpRegionCfgList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-MstpRegionConfig]} err]} {
        ::sth::sthCore::processError returnKeyedList "No device exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return -code error $returnKeyedList 
    } else {
	foreach regionHandle $mstpRegionCfgList {
	    if {[string equal $regionHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}

	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid stp handle"
	    return $::sth::sthCore::FAILURE
	}		
    }
}
proc ::sth::Stp::IsStpHandleValid { handle } {
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
        if {$cmdStatus == 0} {
            return $::sth::sthCore::FAILURE
        }
        
	if {[catch {set BridgePortConfig [::sth::sthCore::invoke stc::get $handle -children-BridgePortConfig]} err]} {
	    set cmdStatus 0
	}
        if {[string length $BridgePortConfig] == 0} {
            set cmdStatus 0
        }
	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    return $::sth::sthCore::FAILURE		
	}		
    }
}

proc ::sth::Stp::checkDependency {cmdType switchName modeFunc mode} {
    set procName [lindex [info level [info level]] 0]
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::Stp:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            # unlock the specified dependency relation when modify
            if {[string match "modify" $mode]} {
                if {[lsearch -exact "stp_type root_bridge_type region_root_bridge_type" $dependSwitch] >= 0} {
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
                #add warning for dependency error
                
                unset userArgsArray($switchName)
            }
        }
    }
}

# adjuct the default config if multi devices created on one port

#1. stp: devices on one port should not have duplicate port number and bridge mac
#2. rstp: if enable_pt2pt_link is true, then count only can be 1; devices on one port should not have duplicate port number and bridge mac
#3. pvst/rpvst: devices on one port should not have duplicate vlan id
#4. mstp: only one cist can be configured on one port, so count only can be 1
      
proc ::sth::Stp::adjuctDefaultCfg {bridgePortCfgHdl i } {
    
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Stp::userArgsArray
    variable sortedSwitchPriorityList
     
    set cfgHdl ""
    set specialCfgList ""
    switch -- $userArgsArray(stp_type) {
        "stp" {
            set portNum [expr $userArgsArray(port_number) + $i]
            set bridgeMac [::sth::sthCore::macStep $userArgsArray(bridge_mac_address) "00:00:00:00:00:01" 1]
            #handle BridgePortConfig
            set specialCfgList "-PortNum $portNum -BridgeMacAddr $bridgeMac"
            set cfgHdl $bridgePortCfgHdl
        }
        "rstp" {
            if {$userArgsArray(enable_pt2pt_link) == 1} {
                # change the count value to 1
                sth::sthCore::processError returnKeyedList "Error in $procName: :: only one device can be created under one port if enable_pt2pt_link is set to true,so change the count value to 1" {}
                set $userArgsArray(count) 1
            } else {
                set portNum [expr $userArgsArray(port_number)+$i]
                set bridgeMac [::sth::sthCore::macStep $userArgsArray(bridge_mac_address) 1 1]
                #handle BridgePortConfig
                set specialCfgList "-PortNum $portNum -BridgeMacAddr $bridgeMac"
                set cfgHdl $bridgePortCfgHdl
            }
        }
        "pvst" -
        "rpvst" {
            set vlanId [expr $userArgsArray(vlan_start)+$i]
            #handle BridgePortConfig
            set specialCfgList "-StartVlanList $vlanId"
            if {[catch {set stpbridgeportconfig [::sth::sthCore::invoke stc::get $bridgePortCfgHdl -children-StpBridgePortConfig]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::doStcGetNew Failed: $err" {}
                return -code error $returnKeyedList 
            } else {
                if {[info exists stpbridgeportconfig]} {
                    set cfgHdl [stc::get $stpbridgeportconfig -children-VlanBlock]
                }
            }
        }
        "mstp" {
            #put the info into the log file, doesn't handle as a error returned.?
            sth::sthCore::processError returnKeyedList "Error in $procName: :: only one device can be created under one port for mstp type" {}
            set $userArgsArray(count) 1
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown stp type: $userArgsArray(stp_type)" {}
            return -code error $returnKeyedList 
        }
    }
    
    # config
    ::sth::sthCore::invoke stc::config $cfgHdl $specialCfgList
        
}

            

proc ::sth::Stp::processParamsStep {ipversion} {
    variable ::sth::Stp::userArgsArray
    
    set paramslist_ipv4 "local_ip_addr gateway_ip_addr"
    set paramslist_ipv6 "local_ipv6_addr gateway_ipv6_addr"
    set paramslist_vlan "vlan_id vlan_id_outer"
    
    if {[regexp -nocase 4 $ipversion]} {
	set paramslist $paramslist_ipv4
    } elseif {[regexp -nocase 6 $ipversion]} {
	set paramslist $paramslist_ipv6
    } else {
	set paramslist ""
    }
    regsub {ipv} $ipversion "" ipversion
    
    foreach params $paramslist {
	if {[info exists userArgsArray($params)] && [info exists userArgsArray($params\_step)]} {
	    set userArgsArray($params) [::sth::sthCore::updateIpAddress $ipversion $userArgsArray($params) $userArgsArray($params\_step) 1]
	}
    }
    
    foreach params $paramslist_vlan {
	if {[info exists userArgsArray($params)] && [info exists userArgsArray($params\_step)]} {
	    set userArgsArray($params) [expr {$userArgsArray($params) + $userArgsArray($params\_step)}]
	}
    }
    
    if {[info exists userArgsArray(mac_addr)] && [info exists userArgsArray(mac_addr_step)]} {
        set userArgsArray(mac_addr) [::sth::sthCore::macStep $userArgsArray(mac_addr) $userArgsArray(mac_addr_step) 1]
    }
}