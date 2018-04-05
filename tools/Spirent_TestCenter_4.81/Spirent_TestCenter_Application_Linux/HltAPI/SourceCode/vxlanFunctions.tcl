namespace eval ::sth::vxlan:: {
}


proc ::sth::vxlan::emulation_vxlan_config_create {returnKeyedList} {
    #create vxlan device
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
        set ip_version $::sth::vxlan::userArgsArray(ip_version)
        switch -- $ip_version {
            "ipv4"  {
                set topif "Ipv4If"
                set ifCount "1"
            }
            "ipv6"  {
                set topif "Ipv6If"
                set ifCount "1"
            }
            "ipv46" {
                set topif "Ipv6If Ipv4If"
                set ifCount "1 1"
            }
            "none" {
                # the interface does not have the L3 layer encapsulation
                set topif ""
                set ifCount ""
            }
        }
        
        set encap $::sth::vxlan::userArgsArray(encapsulation)
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
                ::sth::sthCore::processError returnKeyedList "Error in emulation_vxlan_config: Invalid -encap $encap" {}
                return -code error $returnKeyedList  
            }
            
        }
        
        set deviceList ""
        set portHandle $::sth::vxlan::userArgsArray(port_handle)
        set count $::sth::vxlan::userArgsArray(count)
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle -CreateCount $count]
        set devices $DeviceCreateOutput(-ReturnList)
        set i 0
        foreach device $devices {
            configDevice $device create $i
            set ethIfHandle [::sth::sthCore::invoke stc::get $device -children-EthIIIf]
            configEthIIIntf $ethIfHandle create $i
            set lowerIf ""
            if {$encap == "ethernet_ii"} {
                set lowerIf [::sth::sthCore::invoke stc::get $device -children-EthIIIf]
            } else {
                set lowerIf [lindex [::sth::sthCore::invoke stc::get $device -children-VlanIf] 0]
            }
            
            #need to split the linklocal and the global ipv6
            set topLevelIf ""
            if {[regexp "6" $ip_version]} {            
                set ipv6If [::sth::sthCore::invoke stc::get $device -children-ipv6if]
                ::sth::sthCore::invoke stc::config $device "-primaryif-targets $ipv6If"
                # create new ipv6if
                set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $device -StackedOnEndpoint-targets $lowerIf]
                set topLevelIf [concat $topLevelIf $ipv6If $linkLocalIf]
                configIpv6LinkLocalIntf $linkLocalIf create $i
                configIpv6Intf $ipv6If create $i
                
            }
            set ipv4If ""
            if {[regexp "v4" $ip_version]} {
                set ipv4If [::sth::sthCore::invoke stc::get $device -children-Ipv4If]
                set topLevelIf [concat $ipv4If $topLevelIf]
                configIpv4Intf $ipv4If create $i
            }
            ::sth::sthCore::invoke stc::config $device "-TopLevelIf-targets \"$topLevelIf\""
            
            if {[regexp "ethernet_ii_vlan" $encap]} {
                set vlanIntf [::sth::sthCore::invoke stc::get $device -children-VlanIf]
                configVlanIfInner $vlanIntf create $i
            } elseif {[regexp "ethernet_ii_qinq" $encap]} {
                set vlanIntf [::sth::sthCore::invoke stc::get $device -children-VlanIf]
                configVlanIfInner [lindex $vlanIntf 0] create $i
                configVlanIfOuter [lindex $vlanIntf 1] create $i
            }
            
            #create and config the vtep
            set vtepConfig [::sth::sthCore::invoke stc::create VxlanVtepConfig -under $device]
            set vxlanIf [::sth::sthCore::invoke stc::create VxlanIf -under $device]
            configVxlan $vtepConfig create $i
            ::sth::sthCore::invoke stc::config $vtepConfig -UsesIf-targets $ipv4If
            ::sth::sthCore::invoke stc::config $vxlanIf -StackedOnEndpoint-targets $ipv4If
            
            set vxlanPortConfig [::sth::sthCore::invoke stc::get $portHandle -children-VxlanPortConfig]
            configVxlanPort $vxlanPortConfig create $i
            
            set vxlanSegmentConfigList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-VxlanSegmentConfig]
            set vxlanSegmentConfig ""
    
            set optionValueList [getStcOptionValueList emulation_vxlan_config configVxlanSegment create $vxlanSegmentConfigList $i]
            if {![regexp "^$" $optionValueList]} {
                #when one of the vni communication_type multicast_group vm_hosts has been configured,
                #will configure the vxlansegment, else will not process it
                set vxlanSegmentConfig [configVxlanSegment $vxlanSegmentConfigList $device create $i]
            }
            incr i
        }
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
        # delete any host created if error occurs
        foreach device $devices {
            ::sth::sthCore::invoke stc::delete $device
        }
    } else {
        keylset myreturnKeyedList handle $devices
	keylset myreturnKeyedList  vxlansegmenthandle $vxlanSegmentConfig
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList                                                                                                                                                                          
}


proc ::sth::vxlan::emulation_vxlan_config_modify {returnKeyedList} {
    #only modify the VTEP device and VxlanVtepConfig attributes, need to process the vxlansegmentconfig and vxlan vxlanvmtovteplink
    
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
        set device $::sth::vxlan::userArgsArray(handle)
        configDevice $device modify 0
        set ethIfHandle [::sth::sthCore::invoke stc::get $device -children-EthIIIf]
        if {$ethIfHandle != ""} {
            configEthIIIntf $ethIfHandle modify 0
        }
        set vlanIntf [::sth::sthCore::invoke stc::get $device -children-VlanIf]
        if {$vlanIntf != ""} {
            if {[llength $vlanIntf] > 1} {
                foreach vlan $vlanIntf {
                    set vlanLowerIntf [::sth::sthCore::invoke stc::get $vlan -StackedOnEndpoint-targets]
                    if {[regexp "vlan" $vlanLowerIntf]} {
                        #this is inner vlan
                        configVlanIfInner $vlan modify 0
                    } else {
                        configVlanIfOuter $vlan modify 0
                    }
                }
            } else {
                configVlanIfInner $vlanIntf modify 0
            }
        }
        set ipv6If [::sth::sthCore::invoke stc::get $device -children-ipv6If]
        if {$ipv6If != ""} {
            #check the linklocal addr
            foreach ipv6 $ipv6If {
                set addr [::sth::sthCore::invoke stc::get $ipv6 -address]
                if {[regexp -nocase "fe80::" $addr]} {
                    configIpv6LinkLocalIntf $ipv6 modify 0
                } else {
                    configIpv6Intf $ipv6 modify 0
                }
            }
        }
        set ipv4If [::sth::sthCore::invoke stc::get $device -children-ipv4If]
        
        if {$ipv4If != ""} {
            configIpv4Intf $ipv4If modify 0
        }
	
	set vtepConfig [::sth::sthCore::invoke stc::get $device -children-VxlanVtepConfig]
        #set vxlanIf [::sth::sthCore::invoke stc::create VxlanIf -under $device]
        configVxlan $vtepConfig modify 0
        #stc::config $vtepConfig -UsesIf-targets $ipv4If
        #stc::config $vxlanIf -StackedOnEndpoint-targets $ipv4If
        set portHandle [::sth::sthCore::invoke stc::get $device -affiliationport-Targets]
        set vxlanPortConfig [::sth::sthCore::invoke stc::get $portHandle -children-VxlanPortConfig]
        configVxlanPort $vxlanPortConfig modify 0

	if {[info exists ::sth::vxlan::userArgsArray(vxlansegmenthandle)]} {
	    set vxlanSegmentConfig $::sth::vxlan::userArgsArray(vxlansegmenthandle)
	    configVxlanSegment $vxlanSegmentConfig $device modify 0
	}
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList

}

proc ::sth::vxlan::emulation_vxlan_config_delete {returnKeyedList} {
    #delete the specified the device
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
        set devices $::sth::vxlan::userArgsArray(handle)
        foreach device $devices {
            ::sth::sthCore::invoke stc::delete $device
        }
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList
}

proc ::sth::vxlan::configDevice {deviceHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_vxlan_config configDevice $mode $deviceHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $deviceHandle $optionValueList
    }
}
proc ::sth::vxlan::configEthIIIntf { ethIfHandle mode routerIdx} {
    
    set optionValueList [getStcOptionValueList emulation_vxlan_config configEthIIIntf $mode $ethIfHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethIfHandle $optionValueList
    }
}

proc ::sth::vxlan::configIpv4Intf { ipIfHandle mode routerIdx} {
    
    set optionValueList [getStcOptionValueList emulation_vxlan_config configIpv4Intf $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::vxlan::configIpv6Intf { ipIfHandle mode routerIdx} {
    
    set optionValueList [getStcOptionValueList emulation_vxlan_config configIpv6Intf $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}



proc ::sth::vxlan::configIpv6LinkLocalIntf { ipIfHandle mode routerIdx} {
    
    set optionValueList [getStcOptionValueList emulation_vxlan_config configIpv6LinkLocalIntf $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}


###
#  Name:    configVlanIfInner 
#  Inputs:  vlanIfHandle - VlanIf handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description:  This procedure configures VlanIf with vlan_id and vlan_ethertype
###
proc ::sth::vxlan::configVlanIfInner { vlanIfHandle mode routerIdx} {
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanIfHandle -parent]
    set optionValueList [getStcOptionValueList emulation_vxlan_config configVlanIfInner $mode $deviceHandle $routerIdx]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}


proc ::sth::vxlan::configVlanIfOuter {vlanIfHandle mode routerIdx} {
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanIfHandle -parent]
    set optionValueList [getStcOptionValueList emulation_vxlan_config configVlanIfOuter $mode $deviceHandle $routerIdx]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}

proc ::sth::vxlan::getStcOptionValueList {cmdType modeFunc mode procFuncHandle routerIdx} {
    
    set optionValueList {}
    
    foreach item $::sth::vxlan::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::vxlan:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::vxlan:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::vxlan:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                #::sth::vxlan::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::vxlan::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::vxlan:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::vxlan:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::vxlan:: $cmdType $opt $::sth::vxlan::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::vxlan::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::vxlan::userArgsArray($opt) $routerIdx]
                }
            }
    }
    return $optionValueList
}

proc ::sth::vxlan::configVxlan {vtepConfig mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_vxlan_config configVxlan $mode $vtepConfig $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vtepConfig $optionValueList
    }
}

proc ::sth::vxlan::configVxlanPort {vxlanPortConfig mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_vxlan_config configVxlanPort $mode $vxlanPortConfig $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vxlanPortConfig $optionValueList
    }
}



proc ::sth::vxlan::configVxlanSegment {vxlanSegmentConfig device mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_vxlan_config configVxlanSegment $mode $vxlanSegmentConfig $routerIdx]
    set vxlanvminfo_list ""
    if {$mode == "create"} {
        set segmentflag 0
        
        if {$vxlanSegmentConfig == ""} {
            set vxlanSegmentConfig [::sth::sthCore::invoke stc::create VxlanSegmentConfig -under $::sth::GBLHNDMAP(project)]
            if {[info exists ::sth::vxlan::userArgsArray(vni)]} {
                ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -Vni $::sth::vxlan::userArgsArray(vni)
            }
            if {[info exists ::sth::vxlan::userArgsArray(communication_type)]} {
                ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -CommunicationType $::sth::vxlan::userArgsArray(communication_type)
            }
	    set segmentflag 1
        } else {
            foreach vxlanSegment $vxlanSegmentConfig {
                set vni [::sth::sthCore::invoke stc::get $vxlanSegment -Vni]
                if {[info exists ::sth::vxlan::userArgsArray(vni)] && $vni == $::sth::vxlan::userArgsArray(vni)} {
                    set segmentflag 1
                    set vxlanSegmentConfig $vxlanSegment
                    break
                } else {
                    set segmentflag 0
                }
            }
        }
        if {$segmentflag == 0} {
            set vxlanSegmentConfig [::sth::sthCore::invoke stc::create VxlanSegmentConfig -under $::sth::GBLHNDMAP(project)]
            if {[info exists ::sth::vxlan::userArgsArray(vni)]} {
                ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -Vni $::sth::vxlan::userArgsArray(vni)
            }
            if {[info exists ::sth::vxlan::userArgsArray(communication_type)]} {
                ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -CommunicationType $::sth::vxlan::userArgsArray(communication_type)
            }
        } else {
            set vxlanvminfo_list [::sth::sthCore::invoke stc::get $vxlanSegmentConfig -MemberOfVxlanSegment-targets]
        }
        #need to also process the vm_hosts and the multicast_group
        if {[info exists ::sth::vxlan::userArgsArray(multicast_group)]} {
            #the communication_type need to be multicast
            set com_type [::sth::sthCore::invoke stc::get $vxlanSegmentConfig -CommunicationType]
            if {[regexp -nocase "MULTICAST" $com_type]} {
                foreach mgroup $::sth::vxlan::userArgsArray(multicast_group) {
                    ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -UsesIpv4MulticastGroupForOverlay-targets $mgroup
                }
            }
        }
    } else {
        #modify mode
	#modify the info in on the given vxlanSegmentConfig handle
	if {[info exists ::sth::vxlan::userArgsArray(vni)]} {
	    ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -Vni $::sth::vxlan::userArgsArray(vni)
	}
	if {[info exists ::sth::vxlan::userArgsArray(communication_type)]} {
            ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -CommunicationType $::sth::vxlan::userArgsArray(communication_type)
        }

	#need to also process the vm_hosts and the multicast_group
        if {[info exists ::sth::vxlan::userArgsArray(multicast_group)]} {
            #the communication_type need to be multicast
            set com_type [::sth::sthCore::invoke stc::get $vxlanSegmentConfig -CommunicationType]
            if {[regexp -nocase "MULTICAST" $com_type]} {
                foreach mgroup $::sth::vxlan::userArgsArray(multicast_group) {
                    ::sth::sthCore::invoke stc::config $vxlanSegmentConfig -UsesIpv4MulticastGroupForOverlay-targets $mgroup
                }
            }
        }
	
	if {[info exists ::sth::vxlan::userArgsArray(vm_hosts)]} {
	    #delete the all the exists vxlanvminfo
	    set vxlanvminfo_list_old [::sth::sthCore::invoke stc::get $vxlanSegmentConfig -MemberOfVxlanSegment-targets]
	    foreach vxlanvminfo $vxlanvminfo_list_old {
		#get the related vmhost and delete the link on this host
		set vm_host_old [::sth::sthCore::invoke stc::get $vxlanvminfo -UsesVxlanVmInfo-sources]
		set vxlan_link [::sth::sthCore::invoke stc::get $vm_host_old -children-VxlanVmToVtepLink]
                set vtep [::sth::sthCore::invoke stc::get $vxlan_link -linkdstdevice-Targets]
                if {[regexp $device $vtep]} {
                    ::sth::sthCore::invoke stc::config $vxlan_link -linkdst-Targets ""
                    ::sth::sthCore::invoke stc::delete $vxlan_link
                    ::sth::sthCore::invoke stc::delete $vxlanvminfo
                } else {
                    set vxlanvminfo_list [concat $vxlanvminfo_list $vxlanvminfo]
                }
	    }
	}
	
    }
    if {[info exists ::sth::vxlan::userArgsArray(vm_hosts)]} {
	#create new vxlanvminfo
	foreach vmhost $::sth::vxlan::userArgsArray(vm_hosts) {
	    set vxlanvminfo [::sth::sthCore::invoke stc::create VxlanVmInfo -under $::sth::GBLHNDMAP(project)]
	    ::sth::sthCore::invoke stc::config $vmhost -UsesVxlanVmInfo-targets $vxlanvminfo
            set ethif [::sth::sthCore::invoke stc::get $vmhost -children-EthIIIf]
	    set vxlanif [::sth::sthCore::invoke stc::get $device -children-VxlanIf]
            array set LinkCreatArray [::sth::sthCore::invoke stc::perform LinkCreate -SrcDev $vmhost -DstDev $device -LinkType "VXLAN VM to VTEP Device Link"]
            set vxlanVmToVtepLink $LinkCreatArray(-Link)
            ::sth::sthCore::invoke stc::config $vmhost -ContainedLink-targets $vxlanVmToVtepLink
            ::sth::sthCore::invoke stc::config $vxlanVmToVtepLink -LinkSrc-targets $ethif
            ::sth::sthCore::invoke stc::config $vxlanVmToVtepLink -LinkDst-targets $vxlanif
            ::sth::sthCore::invoke stc::config $vxlanvminfo -MemberOfVxlanSegment-Sources $vxlanSegmentConfig
	}

    }
    return $vxlanSegmentConfig
}

proc ::sth::vxlan::emulation_vxlan_stats_func {returnKeyedList} {
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set device_list ""
    set retVal [catch {
        if {[info exists ::sth::vxlan::userArgsArray(handle)]} {
            set device_list $::sth::vxlan::userArgsArray(handle)
        } else {
            set port_list $::sth::vxlan::userArgsArray(port_handle)
            foreach port $port_list {
                #get the vxlan device
                set devices [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
                foreach device $devices {
                    set vtep [::sth::sthCore::invoke stc::get $device -children-VxlanVtepConfig]
                    if {![regexp "^$" $vtep]} {
                        set device_list [concat $device_list $device]
                    }
                }
            }
        }
        foreach device $device_list {
            set retVal {}
            set stcobj [::sth::sthCore::invoke stc::get $device -children-VxlanVtepConfig]
            if {[regexp "^$" $stcobj]} {
                continue
            }
            foreach key [array names ::sth::vxlan::emulation_vxlan_stats_stcobj] {
                if {[regexp -nocase "VxlanVtepConfig" $::sth::vxlan::emulation_vxlan_stats_stcobj($key)]} {
                    set stcattr $::sth::vxlan::emulation_vxlan_stats_stcattr($key)
                    set stcvalue [::sth::sthCore::invoke stc::get $stcobj -$stcattr]
                    keylset retVal $key $stcvalue
                }
            }
            keylset myreturnKeyedList $device $retVal
        }
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList "Error in get vxlan device stats: $returnedString"
    } else {
        keylset myreturnKeyedList status 1
    }
    
}

proc ::sth::vxlan::processEmulation_vxlan_configVlanId {vlanIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    set encap $::sth::vxlan::userArgsArray(encapsulation)
    set qinq_incr_mode $::sth::vxlan::userArgsArray(qinq_incr_mode)
    set vlan_count $::sth::vxlan::userArgsArray(vlan_id_count)
    if {$vlan_count == 1} {
        set vlan $::sth::vxlan::userArgsArray(vlan_id)
    } else {
        if {$encap == "ethernet_ii_qinq"} {
            switch -exact -- $qinq_incr_mode {
                "inner" -
                "both" {
                     set vlan [expr $value + (($routerIdx%$vlan_count) * $::sth::vxlan::userArgsArray(vlan_id_step))]
                }
                "outer" {
                    set repeat_count ""
                    if {[expr $::sth::vxlan::userArgsArray(vlan_id_count)-1] > 0} {
                        set repeat_count [expr $::sth::vxlan::userArgsArray(vlan_id_count)-1]
                    } else {
                        set repeat_count $::sth::vxlan::userArgsArray(vlan_id_count)
                    }
                    set vlan [expr $value + ((($routerIdx/$repeat_count)%$vlan_count) * $::sth::vxlan::userArgsArray(vlan_id_step))]
                }
            }
        } else {
            set vlan [expr $value + (($routerIdx%$vlan_count) * $::sth::vxlan::userArgsArray(vlan_id_step))]
        }
    }
    return "-[::sth::sthCore::getswitchprop ::sth::vxlan:: emulation_vxlan_config $option stcattr] $vlan"
}
proc ::sth::vxlan::processEmulation_vxlan_configOuterVlanId {vlanIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    set qinq_incr_mode $::sth::vxlan::userArgsArray(qinq_incr_mode)
    set vlan_count $::sth::vxlan::userArgsArray(vlan_outer_id_count)
    if {$vlan_count == 1} {
        set vlan $::sth::vxlan::userArgsArray(vlan_outer_id)
    } else {
        switch -exact -- $qinq_incr_mode {
            "outer" -
            "both" {
                 set vlan [expr $value + (($routerIdx%$vlan_count) * $::sth::vxlan::userArgsArray(vlan_outer_id_step))]
            }
            "inner" {
                set repeat_count ""
                if {[expr $::sth::vxlan::userArgsArray(vlan_outer_id_count)-1] > 0} {
                    set repeat_count [expr $::sth::vxlan::userArgsArray(vlan_outer_id_count)-1]
                } else {
                    set repeat_count $::sth::vxlan::userArgsArray(vlan_outer_id_count)
                }
                set vlan [expr $value + ((($routerIdx/$repeat_count)%$vlan_count) * $::sth::vxlan::userArgsArray(vlan_outer_id_step))]
            }
        }
    }
    return "-[::sth::sthCore::getswitchprop ::sth::vxlan:: emulation_vxlan_config $option stcattr] $vlan"
}
proc ::sth::vxlan::processEmulation_vxlan_configSrcMacAddr {ethIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    # mac step is not defined in HltApi spec so we'll just step by 1
    if {[info exists ::sth::vxlan::userArgsArray(mac_addr_step)]} {
        set step $::sth::vxlan::userArgsArray(mac_addr_step)
    } else {
        set step "00:00:00:00:00:01"
    }
    set srcMac [::sth::sthCore::macStep $value $step $routerIdx]
        
    if {$routerIdx == [expr $::sth::vxlan::userArgsArray(count) -1]} {
        set nextMac [::sth::sthCore::macStep $srcMac "00:00:00:00:00:01" 1]
        set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
        ::sth::sthCore::invoke stc::config $addrOption "-NextMac $nextMac"
    }
    
    return "-[::sth::sthCore::getswitchprop ::sth::vxlan:: emulation_vxlan_config $option stcattr] $srcMac"
}
proc ::sth::vxlan::processEmulation_vxlan_configIp {ipIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    set ipVersion 4
    if {[string match -nocase "ipv6if*" $ipIfHandle]} {
	set ipVersion 6
    }
    if {$ipVersion == 4} {
        if {[regexp "gateway" $option]} {
            if {[info exists ::sth::vxlan::userArgsArray(gateway_ip_addr_step)]} {
                set step $::sth::vxlan::userArgsArray(gateway_ip_addr_step)
                set ip [::sth::sthCore::updateIpAddress $ipVersion $value $step $routerIdx]
            } else {
                set ip $value
            }
        } else {
            if {[info exists ::sth::vxlan::userArgsArray(intf_ip_addr_step)]} {
                set step $::sth::vxlan::userArgsArray(intf_ip_addr_step)
                set ip [::sth::sthCore::updateIpAddress $ipVersion $value $step $routerIdx]
            } else {
                set ip $value
            }
        }
    } else {
        if {[regexp "gateway" $option]} {
            if {[info exists ::sth::vxlan::userArgsArray(gateway_ipv6_addr_step)]} {
                set step $::sth::vxlan::userArgsArray(gateway_ipv6_addr_step)
                set ip [::sth::sthCore::updateIpAddress $ipVersion $value $step $routerIdx]
            } else {
                set ip $value
            }
        } elseif {[regexp "link_local" $option]} {
            if {[info exists ::sth::vxlan::userArgsArray(link_local_ipv6_addr_step)]} {
                set step $::sth::vxlan::userArgsArray(link_local_ipv6_addr_step)
                set ip [::sth::sthCore::updateIpAddress $ipVersion $value $step $routerIdx]
            } else {
                set ip $value
            }
        } else {
            if {[info exists ::sth::vxlan::userArgsArray(intf_ipv6_addr_step)]} {
                set step $::sth::vxlan::userArgsArray(intf_ipv6_addr_step)
                set ip [::sth::sthCore::updateIpAddress $ipVersion $value $step $routerIdx]
            } else {
                set ip $value
            }
        }
    }
    return "-[::sth::sthCore::getswitchprop ::sth::vxlan:: emulation_vxlan_config $option stcattr] $ip"
}

##############################Functions for vxlan wizard#######################

##########LOGIC############
#created VxlanConfigGenParams?
#   1)create VxlanGenVtepPortParams 
#   2)set affiliationport-Targets  
#   3)set other config values
#   4)set return value
#if VxlanConfigGenParams not already created
#   5)create VxlanConfigGenParams under project 
#   6)follow step 1 to 4 
###########LOGIC ENDS####

proc ::sth::vxlan::emulation_vxlan_port_config_create {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
	
	#port_handle is mandatory 
    set portHandle $::sth::vxlan::userArgsArray(port_handle)   
	if { ![::info exists ::sth::vxlan::userArgsArray(port_handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "port_handle needed when adding port to vxlan configuration." {}
	    return $returnKeyedList
    }
    
	set VxlanConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanConfigGenParams]
	if { $VxlanConfigGenParamsHdl == ""} {
	    set VxlanConfigGenParamsHdl [::sth::sthCore::invoke stc::create "VxlanConfigGenParams" -under $::sth::GBLHNDMAP(project)]
	}
	
	# 1)create VxlanGenVtepPortParams 
	set VxlanGenVtepPortParamsHdl [::sth::sthCore::invoke stc::create "VxlanGenVtepPortParams" -under $VxlanConfigGenParamsHdl]
	
	# 2)set affiliationport-Targets 
	::sth::sthCore::invoke stc::config $VxlanGenVtepPortParamsHdl "-AffiliationPort-Targets $portHandle"	
	
	# 3)set other config
	set optionValueList [getStcOptionValueList emulation_vxlan_port_config processConfigCmd create $VxlanGenVtepPortParamsHdl 0]
	::sth::sthCore::invoke stc::config $VxlanGenVtepPortParamsHdl $optionValueList
	
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        # 4)set return value
        keylset myreturnKeyedList handle $VxlanGenVtepPortParamsHdl
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList

}

proc ::sth::vxlan::emulation_vxlan_port_config_delete {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
    #handle needed for delete mode
	if { ![::info exists ::sth::vxlan::userArgsArray(handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "handle needed for delete mode " {}
	    return $returnKeyedList
    }
    #Delete the handle
    ::sth::sthCore::invoke stc::delete $::sth::vxlan::userArgsArray(handle)	
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList

}

#################END OF emulation_vxlan_port_config APIs#############################

##########LOGIC for emulation_nonvxlan_port_config_create############
#created VxlanConfigGenParams?
#   1)create VxlanGenHostPortParams 
#   2)set affiliationport-Targets  
#   3)set other config
#   4)set return value
#if VxlanConfigGenParams not already created
#   5)create VxlanConfigGenParams under project 
#   6)follow step 1 to 4 
###########################LOGIC ENDS###############################

proc ::sth::vxlan::emulation_nonvxlan_port_config_create {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
        
    #port_handle is mandatory 
    set portHandle $::sth::vxlan::userArgsArray(port_handle)   
	if { ![::info exists ::sth::vxlan::userArgsArray(port_handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "port_handle needed when adding port to vxlan configuration." {}
	    return $returnKeyedList
    }

	set VxlanConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanConfigGenParams]
	if { $VxlanConfigGenParamsHdl == ""} {
	    set VxlanConfigGenParamsHdl [::sth::sthCore::invoke stc::create "VxlanConfigGenParams" -under $::sth::GBLHNDMAP(project)]
	}
	
	# 1)create VxlanGenHostPortParams 
	set VxlanGenHostPortParamsHdl [::sth::sthCore::invoke stc::create "VxlanGenHostPortParams" -under $VxlanConfigGenParamsHdl]
	
	# 2)set affiliationport-Targets 
	::sth::sthCore::invoke stc::config $VxlanGenHostPortParamsHdl "-AffiliationPort-Targets $portHandle"	
	
	# 3)set other config
	set optionValueList [getStcOptionValueList emulation_nonvxlan_port_config processConfigCmd create $VxlanGenHostPortParamsHdl 0]
	::sth::sthCore::invoke stc::config $VxlanGenHostPortParamsHdl $optionValueList    
		
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        # 4)set return value
        keylset myreturnKeyedList handle $VxlanGenHostPortParamsHdl
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList

}

proc ::sth::vxlan::emulation_nonvxlan_port_config_delete {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
    #handle needed for delete mode
	if { ![::info exists ::sth::vxlan::userArgsArray(handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "handle needed for delete mode " {}
	    return $returnKeyedList
    }
    #Delete the handle
    ::sth::sthCore::invoke stc::delete $::sth::vxlan::userArgsArray(handle)	
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $myreturnKeyedList

}
########Logic for emulation_vxlan_wizard_config_create############
#created VxlanConfigGenParams?
#   1)config values for VxlanConfigGenParams
#   2)config values for VxlanGenHostParams
#   3)config values for VxlanGenVtepParams
#   4)config values for BgpEvpnRouteParams
#   5)config values for VxlanTrafficParams
#   6)get vtep_handle,vm_handle and host_handle           
#   7)set return value
#if VxlanConfigGenParams not already created
#   8)create VxlanConfigGenParams under project 
#   9)follow step 1 to 7 
###################################################################
proc ::sth::vxlan::emulation_vxlan_wizard_config_create {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
        
    set VxlanConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanConfigGenParams]
	if { $VxlanConfigGenParamsHdl == ""} {
	    set VxlanConfigGenParamsHdl [::sth::sthCore::invoke stc::create "VxlanConfigGenParams" -under $::sth::GBLHNDMAP(project)]
	}
    
	#1)config values for VxlanConfigGenParams
    set optionValueList [getStcOptionValueList emulation_vxlan_wizard_config VxlanConfigGenParams create $VxlanConfigGenParamsHdl 0]
	::sth::sthCore::invoke stc::config $VxlanConfigGenParamsHdl $optionValueList  
		
	#2)config values for VxlanGenHostParams
    set VxlanGenHostParamsHdl [::sth::sthCore::invoke stc::get $VxlanConfigGenParamsHdl -Children-VxlanGenHostParams]
    if {$VxlanGenHostParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_wizard_config VxlanGenHostParams create $VxlanGenHostParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanGenHostParamsHdl $optionValueList
    }
    
    #3)config values for VxlanGenVtepParams
    set VxlanGenVtepParamsHdl [::sth::sthCore::invoke stc::get $VxlanConfigGenParamsHdl -Children-VxlanGenVtepParams]
    if {$VxlanGenVtepParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_wizard_config VxlanGenVtepParams create $VxlanGenVtepParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanGenVtepParamsHdl $optionValueList
    }
    
    #4)config values for BgpEvpnRouteParams
    set BgpEvpnRouteParamsHdl [::sth::sthCore::invoke stc::get $VxlanConfigGenParamsHdl -Children-BgpEvpnRouteParams]
    if {$BgpEvpnRouteParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_wizard_config BgpEvpnRouteParams create $BgpEvpnRouteParamsHdl 0]
        ::sth::sthCore::invoke stc::config $BgpEvpnRouteParamsHdl $optionValueList
    }
    
    #5)config values for VxlanTrafficParams
    set VxlanTrafficParamsHdl [::sth::sthCore::invoke stc::get $VxlanConfigGenParamsHdl -Children-VxlanTrafficParams]
    if {$VxlanTrafficParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_wizard_config VxlanTrafficParams create $VxlanTrafficParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanTrafficParamsHdl $optionValueList
    }
    
	#6)config values for VxlanL3VniParams
    set VxlanL3VniParamsHdl [::sth::sthCore::invoke stc::get $VxlanConfigGenParamsHdl -Children-VxlanL3VniParams]
    if {$VxlanL3VniParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_wizard_config VxlanL3VniParams create $VxlanL3VniParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanL3VniParamsHdl $optionValueList
    }
	
    #Expand and 6) get vtep_handle,vm_handle and host_handle  
    set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]
    stc::perform VxlanConfigGenConfigExpandCommand -GenParams $VxlanConfigGenParamsHdl -ClearExisting no
    set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]
    set childrenList [split $childrenStr]
    foreach child $pre_childrenStr {
        set x [lsearch $childrenList $child]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    set emulatedDeviceHdl ""
    set host_handle ""
    set vtep_handle ""
    set vm_handle ""
    set device_children ""
    set AffPortList ""
    set index 1
    foreach child $childrenList {
        if { [string first "emulateddevice" [string tolower $child]] > -1} {
            lappend emulatedDeviceHdl $child
        }
    }
    foreach device $emulatedDeviceHdl {
        set bgpevpn_handle ""
        if {[catch {set deviceName [::sth::sthCore::invoke stc::get $device -Name]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Name from $device. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { [string first "VTEP Device" $deviceName] > -1 } {
            set bgp_handle [::sth::sthCore::invoke stc::get $device -children-bgprouterconfig]
            if { $bgp_handle != "" } {
                set bgpevpn_handles [stc::get $bgp_handle -children]
                foreach bgpevpn_hdl $bgpevpn_handles {
                    if {[regexp "^bgpevpn" $bgpevpn_hdl]} {
                        lappend bgpevpn_handle $bgpevpn_hdl
                    }
                }
                set AffPort [::sth::sthCore::invoke stc::get $device -AffiliationPort-Targets]
                if {[lsearch $AffPortList $AffPort] == -1} {
                    set index 1
                }
                lappend AffPortList $AffPort
                keylset vtep_handle $AffPort.$index.device_handle $device 
                keylset vtep_handle $AffPort.$index.bgp_handle $bgp_handle
                keylset vtep_handle $AffPort.$index.bgpevpn_handle $bgpevpn_handle
                incr index
            } else {
                lappend vtep_handle $device
            }
        } elseif { [string first "VM Device" $deviceName] > -1 } {
            lappend vm_handle $device
        } else {
            lappend host_handle $device
        }
    }
    
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        #7)set return value
        if { $vtep_handle != "" } {
            keylset myreturnKeyedList vtep_handle $vtep_handle
        }
        if { $vm_handle != "" } {
            keylset myreturnKeyedList vm_handle $vm_handle
        }
        if { $host_handle != "" } {
            keylset myreturnKeyedList host_handle $host_handle
        }
        keylset myreturnKeyedList handle $VxlanConfigGenParamsHdl
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList

}

proc ::sth::vxlan::emulation_vxlan_wizard_config_delete {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlan::userArgsArray
    set retVal [catch {
    #handle needed for delete mode
	if { ![::info exists ::sth::vxlan::userArgsArray(handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "handle needed for delete mode " {}
	    return $returnKeyedList
    }
    #Delete the handle
    ::sth::sthCore::invoke stc::delete $::sth::vxlan::userArgsArray(handle)	
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $myreturnKeyedList

}


##############################End Functions for vxlan wizard#######################


