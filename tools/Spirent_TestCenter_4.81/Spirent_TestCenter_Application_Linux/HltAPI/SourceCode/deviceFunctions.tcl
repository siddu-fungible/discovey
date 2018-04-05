namespace eval ::sth::device:: {
    
}

proc ::sth::device::emulation_device_config_create {returnKeyedList} {
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::device::userArgsArray
    if {[::sth::sthCore::IsInputOpt block_mode] || [::sth::sthCore::IsInputOpt expand]} {
            set portHandle $::sth::device::userArgsArray(port_handle)
            ::sth::device::configureDeviceWizard $portHandle
            return $myreturnKeyedList
        }   

    set retVal [catch {
        set ip_version $::sth::device::userArgsArray(ip_version)
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
        
        set encap $::sth::device::userArgsArray(encapsulation)
        switch -- $encap {
            "ethernet_ii" {
                set IfStack "$topif EthIIIf"
                set IfCount "$ifCount 1"
            }
            "ethernet_ii_vlan" {
                set IfStack "$topif VlanIf EthIIIf"
                set IfCount "$ifCount 1 1"
            }
            "ethernet_ii_qinq"  -
            "ethernet_ii_mvlan" {
                set IfStack "$topif VlanIf VlanIf EthIIIf"
                set IfCount "$ifCount 1 1 1"
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error in emulation_device_config: Invalid -encap $encap" {}
                return -code error $returnKeyedList  
            }
        }
        set IfStack [string trim $IfStack]
        set IfCount [string trim $IfCount]
        set deviceList ""
        set portHandle $::sth::device::userArgsArray(port_handle)
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
        set device $DeviceCreateOutput(-ReturnList)
        configDevice $device create
        set ethIfHandle [::sth::sthCore::invoke stc::get $device -children-EthIIIf]
        configEthIIIntf $ethIfHandle create
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
            ::sth::sthCore::invoke stc::config $ipv6If -StackedOnEndpoint-targets $lowerIf
            #For US38176,add link local default address
            set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $device -StackedOnEndpoint-targets $lowerIf -Address "fe80::1"]
            set topLevelIf [concat $topLevelIf $ipv6If $linkLocalIf]
            configIpv6LinkLocalIntf $linkLocalIf create
            configIpv6Intf $ipv6If create
        }
        
        if {[regexp "v4" $ip_version]} {
            set ipv4If [::sth::sthCore::invoke stc::get $device -children-Ipv4If]
           
            set topLevelIf [concat $ipv4If $topLevelIf]
            configIpv4Intf $ipv4If create
        }
        
		if {$topLevelIf != "" } {
	        ::sth::sthCore::invoke stc::config $device "-TopLevelIf-targets \"$topLevelIf\""
		}
        
        set vlanIntf [::sth::sthCore::invoke stc::get $device -children-VlanIf]
        if {[regexp "ethernet_ii_vlan" $encap]} {
            configVlanIfInner $vlanIntf create
        } elseif {[regexp "ethernet_ii_qinq" $encap]} {
            configVlanIfInner [lindex $vlanIntf 0] create
            configVlanIfOuter [lindex $vlanIntf 1] create
        } elseif {[regexp "ethernet_ii_mvlan" $encap]} {
            configVlanIfInner [lindex $vlanIntf 0] create
            configVlanIfOuter [lindex $vlanIntf 1] create
            configVlanIfMultiple $device create
        }
        
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
        # delete any host created if error occurs
        ::sth::sthCore::invoke stc::delete $device
    } else {
        keylset myreturnKeyedList handle $device
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList
}

proc ::sth::device::emulation_device_config_modify {returnKeyedList} {
    #modify the device config, the interface configure, will not change the stack.
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::device::userArgsArray
    set retVal [catch {
        set device $::sth::device::userArgsArray(handle)
        set vlanHandleCount 0
        set children [::sth::sthCore::invoke stc::get $device -children]
        foreach child  $children {
            if {[regexp "vlanif" $child]} {
                incr vlanHandleCount
            }
        }
        # compare with current encapsulation type and modification encapsulation type 
        switch -- $vlanHandleCount {
            "0" {set currentEncapsulation "ethernet_ii"}
            "1" {set currentEncapsulation "ethernet_ii_vlan"}
            "2" {set currentEncapsulation "ethernet_ii_qinq"}
            default {set currentEncapsulation "ethernet_ii_mvlan"}
        }

        configDevice $device modify
        set ethIfHandle [::sth::sthCore::invoke stc::get $device -children-EthIIIf]
        if {$ethIfHandle != ""} {
            configEthIIIntf $ethIfHandle modify
        }
        
       ::sth::device::emulation_device_config_modify_encapsulation returnKeyedList $currentEncapsulation
        
        set ipv6If [::sth::sthCore::invoke stc::get $device -children-ipv6If]
        if {$ipv6If != ""} {
            #check the linklocal addr
            foreach ipv6 $ipv6If {
                set addr [::sth::sthCore::invoke stc::get $ipv6 -address]
                if {[regexp -nocase "fe80::" $addr]} {
                    configIpv6LinkLocalIntf $ipv6 modify
                } else {
                    configIpv6Intf $ipv6 modify
                }
            }
        }
        set ipv4If [::sth::sthCore::invoke stc::get $device -children-ipv4If]
        
        if {$ipv4If != ""} {
            configIpv4Intf $ipv4If modify
        }
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $myreturnKeyedList
}

# US37595 [CR22811][P1]Issue in modfication of emulation_device_config
# US37595 --TA144698 fix backward compatability issue 
proc ::sth::device::emulation_device_config_modify_encapsulation {returnKeyedList currentEncapsulation} {
    #modify the encapsulation, will change the stack.
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::device::userArgsArray
    
    # following var is used for save current stack info
    set tagNum 1
    array set stackSource {}
    array set stackTargets {}
    array set sortedStack {}
    
    #set tagLayer ""

    set device $::sth::device::userArgsArray(handle)

    set ethIfHandle [::sth::sthCore::invoke stc::get $device -children-EthIIIf]
    set vlanIntfs [::sth::sthCore::invoke stc::get $device -children-VlanIf]

    if {[string eq $::sth::device::userArgsArray(encapsulation) ""]} {
        set encap $currentEncapsulation
    } else {
        set encap $::sth::device::userArgsArray(encapsulation)
    }

    set sortedStack(stackUnderVlan) $ethIfHandle
    # get and save current interface handle info,
    set tagNum [::sth::device::getCurrentStackInfo $ethIfHandle $tagNum stackSource stackTargets]

    ::sth::device::sortStack $currentEncapsulation stackSource sortedStack

    switch -- $encap {
        "ethernet_ii" {
            if { $currentEncapsulation ne "ethernet_ii" } {
                configStackRelations $sortedStack(stackUnderVlan) $sortedStack(stackUpperVlan)
                foreach vlan $vlanIntfs {
                    ::sth::sthCore::invoke stc::delete $vlan
                }
            }
        }
        "ethernet_ii_vlan" {
            switch -- $currentEncapsulation {
                "ethernet_ii" {
                    set vlanInnerIntf [::sth::sthCore::invoke stc::create vlanIf -under $device]
                    configStackRelations $sortedStack(stackUnderVlan) $vlanInnerIntf
                    configStackRelations $vlanInnerIntf $sortedStack(stackUpperVlan)
                }
                "ethernet_ii_vlan" {
                    set vlanInnerIntf $sortedStack(firstVlan)
                }
                "ethernet_ii_qinq" {
                    configStackRelations $sortedStack(stackUnderVlan) $sortedStack(secondVlan)
                    set vlanInnerIntf $sortedStack(secondVlan)
                    ::sth::sthCore::invoke stc::delete $sortedStack(firstVlan)
                }
                "ethernet_ii_mvlan" {
                    configStackRelations $sortedStack(stackUnderVlan) $sortedStack(secondVlan)
                    configStackRelations $sortedStack(secondVlan) $sortedStack(stackUpperVlan)
                    set vlanInnerIntf $sortedStack(secondVlan)
                    foreach vlan $vlanIntfs {
                        if {![string equal $sortedStack(secondVlan) $vlan]} {
                            ::sth::sthCore::invoke stc::delete $vlan
                        }
                    }
                }
            }
            configVlanIfInner $vlanInnerIntf modify
        }
        "ethernet_ii_qinq" -
        "ethernet_ii_mvlan" {
            switch -- $currentEncapsulation {
                "ethernet_ii" {
                    set vlanInnerIntf [::sth::sthCore::invoke stc::create vlanIf -under $device]
                    set vlanOuterIntf [::sth::sthCore::invoke stc::create vlanIf -under $device]
                    configStackRelations $sortedStack(stackUnderVlan) $vlanOuterIntf
                    configStackRelations $vlanOuterIntf $vlanInnerIntf
                    configStackRelations $vlanInnerIntf $sortedStack(stackUpperVlan)
                }
                "ethernet_ii_vlan" {
                    set vlanOuterIntf [::sth::sthCore::invoke stc::create vlanIf -under $device]
                    configStackRelations $sortedStack(stackUnderVlan) $vlanOuterIntf
                    configStackRelations $vlanOuterIntf $sortedStack(firstVlan)
                    configStackRelations $sortedStack(firstVlan) $sortedStack(stackUpperVlan)
                    set vlanInnerIntf $sortedStack(firstVlan)
                }
                default {
                    set vlanOuterIntf  $sortedStack(firstVlan)
                    set vlanInnerIntf  $sortedStack(secondVlan)
                }
            }
            configVlanIfInner $vlanInnerIntf modify
            configVlanIfOuter $vlanOuterIntf modify
            # from mvlan to qinq
            if {[string equal $encap "ethernet_ii_qinq"]} {
                configStackRelations $vlanInnerIntf $sortedStack(stackUpperVlan)
                foreach vlan $vlanIntfs {
                    if {[string equal $vlanInnerIntf $vlan] || [string equal $vlanOuterIntf $vlan]} {
                        continue
                    }
                    ::sth::sthCore::invoke stc::delete $vlan
                }
            } elseif {[string equal $encap "ethernet_ii_mvlan"] } {
                if {[info exists ::sth::device::userArgsArray(vlan_id_list)] && $::sth::device::userArgsArray(vlan_id_list) ne ""} {
                    # modify mvlan tags, according to the prev version,the follow two condition will modify the mvlan tags.
                    # 1, set -vlan_id_list and set -encapsulation as ethernet_ii_mvlan in modify mode
                    # 2, current encapsulation type is "ethernet_ii_mvlan" ,pass -vlan_id_list to emulation_device_config in modify mode
                    # if only set -encapsulation as "ethernet_ii_mvlan", will not modify the vlan tags
                    configStackRelations $vlanInnerIntf $sortedStack(stackUpperVlan)
                    foreach vlan $vlanIntfs {
                        if {[string equal $vlanInnerIntf $vlan] || [string equal $vlanOuterIntf $vlan]} {
                            continue
                        }
                        ::sth::sthCore::invoke stc::delete $vlan
                    }
                    configVlanIfMultiple $device modify
                }
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Error in emulation_device_config: Invalid -encap $encap" {}
            return -code error $returnKeyedList  
        }
    }
}


proc ::sth::device::emulation_device_config_delete {returnKeyedList} {
    #delete the specified the device
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::device::userArgsArray
    set retVal [catch {
        set devices $::sth::device::userArgsArray(handle)
        
        if { $devices == "all"} {
            set portList [::sth::sthCore::invoke stc::get project1 -children-port]
            foreach port $portList {
                set deviceHnd [stc::get $port -AffiliatedPortSource]
                ::sth::sthCore::invoke stc::perform delete -ConfigList $deviceHnd
            }
        } else {
            ::sth::sthCore::invoke stc::perform delete -ConfigList $devices
        }
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    ::sth::sthCore::invoke stc::apply
    return $myreturnKeyedList
}



proc ::sth::device::configureDeviceWizard {porthandlevalue} {
    variable ::sth::device::userArgsArray
    variable ::sth::device::sortedSwitchPriorityList
    upvar myreturnKeyedList myreturnKeyedList;
    
    if {[info exists ::sth::device::userArgsArray(count)]} {
        ##wizard way
        set blockMode ONE_DEVICE_PER_BLOCK
        if {[::sth::sthCore::IsInputOpt block_mode]} {
            set blockMode $::sth::device::userArgsArray(block_mode)
        }
                        
        set interfaceGen [::sth::sthCore::invoke stc::create EmulatedDeviceGenParams -under project1\
            -SelectedPort-targets $porthandlevalue -BlockMode $blockMode -Count $::sth::device::userArgsArray(count)]
        
        set ethGen [::sth::sthCore::invoke stc::create DeviceGenEthIIIfParams -under $interfaceGen]
        if {[::sth::sthCore::IsInputOpt mac_addr]} {
            ::sth::sthCore::invoke stc::config $ethGen -SrcMac $::sth::device::userArgsArray(mac_addr)]
        }
        set Lowif $ethGen
        
        if {[::sth::sthCore::IsInputOpt vlan_id]} {
            set vlan1Gen [::sth::sthCore::invoke stc::create DeviceGenVlanIfParams -under $interfaceGen]
            ::sth::sthCore::invoke stc::config $vlan1Gen -vlanId $::sth::device::userArgsArray(vlan_id) -DeviceGenStackedOnIf-targets $ethGen
            if {[::sth::sthCore::IsInputOpt vlan_id_count]} {
                ::sth::sthCore::invoke stc::config $vlan1Gen -Count $::sth::device::userArgsArray(vlan_id_count)
            }
            if {[::sth::sthCore::IsInputOpt vlan_id_step]} {
                ::sth::sthCore::invoke stc::config $vlan1Gen -IdStep $::sth::device::userArgsArray(vlan_id_step)
            }
            if {[::sth::sthCore::IsInputOpt vlan_user_pri]} {
                ::sth::sthCore::invoke stc::config $vlan1Gen -Priority $::sth::device::userArgsArray(vlan_user_pri)
            }
            set Lowif $vlan1Gen
        }
        
        if {[::sth::sthCore::IsInputOpt vlan_outer_id] && [info exists vlan1Gen]} {
            set vlan2Gen [::sth::sthCore::invoke stc::create DeviceGenVlanIfParams -under $interfaceGen]
            ::sth::sthCore::invoke stc::config $vlan2Gen -vlanId $::sth::device::userArgsArray(vlan_outer_id) -DeviceGenStackedOnIf-targets $ethGen
            ::sth::sthCore::invoke stc::config $vlan1Gen -DeviceGenStackedOnIf-targets $vlan2Gen
            if {[::sth::sthCore::IsInputOpt vlan_outer_id_count]} {
                ::sth::sthCore::invoke stc::config $vlan2Gen -Count $::sth::device::userArgsArray(vlan_outer_id_count)
            }
            if {[::sth::sthCore::IsInputOpt vlan_outer_id_step]} {
                ::sth::sthCore::invoke stc::config $vlan2Gen -IdStep $::sth::device::userArgsArray(vlan_outer_id_step)
            }
            if {[::sth::sthCore::IsInputOpt vlan_outer_user_pri]} {
                ::sth::sthCore::invoke stc::config $vlan2Gen -Priority $::sth::device::userArgsArray(vlan_outer_user_pri)
            }
        }
        
        if {[::sth::sthCore::IsInputOpt intf_ip_addr]} {
            set ipv4Gen [::sth::sthCore::invoke stc::create DeviceGenIpv4IfParams -under $interfaceGen\
                -Addr $::sth::device::userArgsArray(intf_ip_addr) -DeviceGenStackedOnIf-targets $Lowif \
                -DeviceGenTopLevelIf-sources $interfaceGen]
            if {[::sth::sthCore::IsInputOpt intf_ip_addr_step]} {
                ::sth::sthCore::invoke stc::config $ipv4Gen -AddrStep $::sth::device::userArgsArray(intf_ip_addr_step)
            }
            if {[::sth::sthCore::IsInputOpt gateway_ip_addr]} {
                ::sth::sthCore::invoke stc::config $ipv4Gen -Gateway $::sth::device::userArgsArray(gateway_ip_addr)
            }
            if {[::sth::sthCore::IsInputOpt gateway_ip_addr_step ]} {
                ::sth::sthCore::invoke stc::config $ipv4Gen -GatewayStep $::sth::device::userArgsArray(gateway_ip_addr_step)
            }
        }
        if {[::sth::sthCore::IsInputOpt ipv6_intf_addr]} {
            set ipv6Gen1 [::sth::sthCore::invoke stc::create DeviceGenIpv6IfParams -under $interfaceGen -AddrType NON_LINK_LOCAL \
                -Addr $::sth::device::userArgsArray(ipv6_intf_addr) -DeviceGenStackedOnIf-targets $Lowif \
                -DeviceGenTopLevelIf-sources $interfaceGen]
            if {[::sth::sthCore::IsInputOpt intf_ipv6_addr_step]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -AddrStep $::sth::device::userArgsArray(intf_ipv6_addr_step)
            }
            if {[::sth::sthCore::IsInputOpt gateway_ipv6_addr]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -Gateway $::sth::device::userArgsArray(gateway_ipv6_addr)
            }
            if {[::sth::sthCore::IsInputOpt gateway_ipv6_addr_step]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -GatewayStep $::sth::device::userArgsArray(gateway_ipv6_addr_step)
            }
            if {[::sth::sthCore::IsInputOpt intf_ipv6_prefix_len]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -PrefixLength $::sth::device::userArgsArray(intf_ipv6_prefix_len)
            }
            set ipv6Gen2 [::sth::sthCore::invoke stc::create DeviceGenIpv6IfParams -under $interfaceGen -AddrType LINK_LOCAL \
                -AutoAddrEnable TRUE -UseEui64LinkLocalAddress TRUE -DeviceGenStackedOnIf-targets $Lowif \
                -DeviceGenTopLevelIf-sources $interfaceGen]
        }
        
        if {[::sth::sthCore::IsInputOpt expand] && $::sth::device::userArgsArray(expand) == "false"} {
            keylset myreturnKeyedList handle_list ""
            keylset myreturnKeyedList param_handle $interfaceGen
        } else {
            array set myreturn [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $interfaceGen]
            keylset myreturnKeyedList handle_list $myreturn(-ReturnList)
            keylset myreturnKeyedList param_handle ""
        }
    }
    keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    return $::sth::sthCore::SUCCESS
}

proc ::sth::device::configDevice {deviceHandle mode} {
    set optionValueList [getStcOptionValueList emulation_device_config configDevice $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $deviceHandle $optionValueList
    }
}
proc ::sth::device::configEthIIIntf { ethIfHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_device_config configEthIIIntf $mode $ethIfHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethIfHandle $optionValueList
    }
}

proc ::sth::device::configIpv4Intf { ipIfHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_device_config configIpv4Intf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::device::configIpv6Intf { ipIfHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_device_config configIpv6Intf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::device::configIpv6LinkLocalIntf { ipIfHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_device_config configIpv6LinkLocalIntf $mode $ipIfHandle]

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
proc ::sth::device::configVlanIfInner { vlanIfHandle mode } {
    variable ::sth::device::userArgsArray
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanIfHandle -parent]
    set optionValueList [getStcOptionValueList emulation_device_config configVlanIfInner $mode $deviceHandle]
    set encap $::sth::device::userArgsArray(encapsulation)
    set qinq_incr_mode ::sth::device::userArgsArray(qinq_incr_mode)
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        switch -exact -- $qinq_incr_mode {
            "inner" -
            "both" {
                lappend optionValueList -IdRepeatCount 0
            }
            "outer" {
                set repeat_count ""
                if {[expr $::sth::device::userArgsArray(vlan_outer_id_count)-1] > 0} {
                    set repeat_count [expr $::sth::device::userArgsArray(vlan_outer_id_count)-1]
                } else {
                    set repeat_count $::sth::device::userArgsArray(vlan_outer_id_count)
                }
                lappend optionValueList -IdRepeatCount $repeat_count
            }
        }
    }
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}

proc ::sth::device::configVlanIfOuter {vlanIfHandle mode} {
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanIfHandle -parent]
    set optionValueList [getStcOptionValueList emulation_device_config configVlanIfOuter $mode $deviceHandle]
    set encap $::sth::device::userArgsArray(encapsulation)
    set qinq_incr_mode ::sth::device::userArgsArray(qinq_incr_mode)
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        switch -exact -- $qinq_incr_mode {
            "outer" -
            "both" {
                lappend optionValueList -IdRepeatCount 0
            }
            "inner" {
                set repeat_count ""
                if {[expr $::sth::device::userArgsArray(vlan_id_count)-1] > 0} {
                    set repeat_count [expr $::sth::device::userArgsArray(vlan_id_count)-1]
                } else {
                    set repeat_count $::sth::device::userArgsArray(vlan_id_count)
                }
                lappend optionValueList -IdRepeatCount $repeat_count
            }
        }
    }
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}

proc ::sth::device::configVlanIfMultiple {deviceHandle mode} {
    variable ::sth::device::userArgsArray
              
    if {[info exists ::sth::device::userArgsArray(vlan_id_list)] && $::sth::device::userArgsArray(vlan_id_list) ne ""} {
        set vlanid_list $::sth::device::userArgsArray(vlan_id_list)
        set tpid_list $::sth::device::userArgsArray(vlan_tpid_list)
        set idcount_list $::sth::device::userArgsArray(vlan_id_count_list)
        set cfi_list $::sth::device::userArgsArray(vlan_cfi_list)
        set userprio_list $::sth::device::userArgsArray(vlan_user_pri_list)
        set idstep_list $::sth::device::userArgsArray(vlan_id_step_list)
        set repeatcount_list $::sth::device::userArgsArray(vlan_id_repeat_count_list)
        
        set vlanlist [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
        set index [expr [llength $vlanlist] -1]
        set vlanHandle [lindex $vlanlist $index]
        set stack_src ""
        set k 0
        foreach hnd $vlanlist {
            incr k
            if {$k > 2} {
                set stackedHandle [::sth::sthCore::invoke stc::get $hnd "-stackedonendpoint-Sources"]
                set stack_src_tmp [regsub -all {vlanif\d+} $stackedHandle ""]
                if {$stack_src_tmp ne ""} {
                    set stack_src $stack_src_tmp
                }
                
                catch {::sth::sthCore::invoke stc::delete $hnd}
            } else {
                set stackedHandle [::sth::sthCore::invoke stc::get $hnd "-stackedonendpoint-Targets"]
                set stack_target [regsub -all {vlanif\d+} $stackedHandle ""]
                if {$stack_target eq ""} {
                    set vlanHandle $hnd
                }
                
                set stackedHandle [::sth::sthCore::invoke stc::get $hnd "-stackedonendpoint-Sources"]
                set stack_src_tmp [regsub -all {vlanif\d+} $stackedHandle ""]
                if {$stack_src_tmp ne ""} {
                    set stack_src $stack_src_tmp
                }
            }
        }

        set i 0
        foreach vlanid $vlanid_list {
            set myvlanid $vlanid 
            set stackedHandle [::sth::sthCore::invoke stc::create VlanIf -under $deviceHandle "-StackedOnEndpoint-targets $vlanHandle"]
            
            set tpid [lindex $tpid_list $i]
            if {$tpid == ""} {
                set tpid $::sth::device::emulation_device_config_default(vlan_tpid_list)
            }
            set idcount [lindex $idcount_list $i]
            if {$idcount == ""} {
                set idcount $::sth::device::emulation_device_config_default(vlan_id_count_list)
            }
            set usrprio [lindex $userprio_list $i]
            if {$usrprio == ""} {
                set usrprio $::sth::device::emulation_device_config_default(vlan_user_pri_list)
            }
            set idstep [lindex $idstep_list $i]
            if {$idstep == ""} {
                set idstep $::sth::device::emulation_device_config_default(vlan_id_step_list)
            }
            set repeatcount [lindex $repeatcount_list $i]
            if {$repeatcount == ""} {
                set repeatcount $::sth::device::emulation_device_config_default(vlan_id_repeat_count_list)
            }
            if {[catch {::sth::sthCore::invoke stc::config $stackedHandle "-VlanId $myvlanid -IdStep $idstep -IdRepeatCount $repeatcount -IfRecycleCount $idcount -Priority $usrprio -Tpid $tpid"} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal error configuring device: $eMsg"
                return $::sth::sthCore::FAILURE
            }

            set vlanHandle $stackedHandle
            incr i
        }

        if {$stack_src ne ""} {
            # fix an issue for Dual stack
            foreach stack_src_hnd $stack_src {
                ::sth::sthCore::invoke stc::config $stack_src_hnd "-stackedonendpoint-Targets $vlanHandle"
            }
        } else {
            return -code error "cannot find object to set its stackedonendpoint-targets for multiple vlans"
        }
    }
    
}

# us37595 [CR22811][P1]Issue in modfication of emulation_device_config
# add following 2 API ::sth::device::configStackRelations and ::sth::device::configVlanStackRelations
# here del ::sth::device::configVlanStackRelations function, and modify configStackRelations function 
# configStackRelations is used for config the stack relationship between the upper stack and lower stack.
proc ::sth::device::configStackRelations {lowerStack upperStack} {

    if {$lowerStack != "" && $upperStack != ""} {
        foreach stack $upperStack {
            ::sth::sthCore::invoke stc::config $stack -stackedonendpoint-Targets $lowerStack
        }
        ::sth::sthCore::invoke stc::config $lowerStack stackedonendpoint-Sources $upperStack
    }
}

proc ::sth::device::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::device::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::device:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::device:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::device:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                #::sth::device::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::device::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::device:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::device:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::device:: $cmdType $opt $::sth::device::userArgsArray($opt)} value]} {
                lappend optionValueList -$stcAttr $value
                } else {
                        lappend optionValueList -$stcAttr $::sth::device::userArgsArray($opt)
                }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::device::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}

proc ::sth::device::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::device:: $cmdType $switchName dependency]] "_none_"]} {
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

proc ::sth::device::getCurrentStackInfo {handle tagNum stackSource stackTargets} {
    # this function is used for get and record current stack info
    upvar $tagNum $stackSource myStackSource
    upvar $tagNum $stackTargets myStackTargets

    set myStackSource($handle) [::sth::sthCore::invoke stc::get $handle -stackedonendpoint-Sources]
    set myStackTargets($handle) [::sth::sthCore::invoke stc::get $handle -stackedonendpoint-Targets]
    
    set nextLayerStacks $myStackSource($handle)
    if {[llength $nextLayerStacks] > 0 } {
        incr tagNum
        foreach intfHandle $nextLayerStacks {
            ::sth::device::getCurrentStackInfo $intfHandle $tagNum stackSource stackTargets
        }
    } else {
        return $tagNum
    }
}


proc ::sth::device::sortStack {currentEncapsulation stackSource sortedStack} {
    
    upvar 1 $sortedStack mySortedStack
    upvar 1 $stackSource myStackSource

    switch -- $currentEncapsulation {
        "ethernet_ii" {
            set mySortedStack(stackUpperVlan) $myStackSource($mySortedStack(stackUnderVlan))
        }
        "ethernet_ii_vlan" {
            set mySortedStack(firstVlan) $myStackSource($mySortedStack(stackUnderVlan))
            set mySortedStack(stackUpperVlan) $myStackSource($mySortedStack(firstVlan))
        }
        "ethernet_ii_qinq" {
            set mySortedStack(firstVlan) $myStackSource($mySortedStack(stackUnderVlan))
            set mySortedStack(secondVlan) $myStackSource($mySortedStack(firstVlan))
            set mySortedStack(stackUpperVlan) $myStackSource($mySortedStack(secondVlan))
        }
        "ethernet_ii_mvlan" {
            set mySortedStack(firstVlan) $myStackSource($mySortedStack(stackUnderVlan))
            set mySortedStack(secondVlan) $myStackSource($mySortedStack(firstVlan))
            set mySortedStack(lastVlan) [::sth::device::searchLastVlanif $mySortedStack(secondVlan) myStackSource]
            set mySortedStack(stackUpperVlan) $myStackSource($mySortedStack(lastVlan))
        }
    }
}

proc ::sth::device::searchLastVlanif {handle stackSource} {
    # this funcion is used for get the last vlanif handle
    upvar 1 $stackSource myStackSource

    if {[regexp -nocase "vlanif" $myStackSource($handle)]} {
        ::sth::device::searchLastVlanif $myStackSource($handle) myStackSource
    } else {
        return $handle
    }
}
