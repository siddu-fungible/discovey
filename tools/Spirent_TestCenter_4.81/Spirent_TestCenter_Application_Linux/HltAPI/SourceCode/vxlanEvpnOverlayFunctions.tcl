namespace eval ::sth::vxlanEvpnOverlay:: {
    set new_handles ""
}

proc ::sth::vxlanEvpnOverlay::getDependValueList {cmdType modeFunc valueList} {
    upvar $valueList myValueList
    
    if {[string match -nocase $modeFunc VxlanConfigGenParams]} {
        # when in ibgp, as values need to be the same as dut_as values.
        if {[info exists ::sth::vxlanEvpnOverlay::userArgsArray(bgp_mode)] && [string match -nocase $::sth::vxlanEvpnOverlay::userArgsArray(bgp_mode) "ibgp"]} {
            set as_map {{dut_as as} {dut_as_step_device as_step_device} {dut_as_step_port as_step_port}}
            foreach item $as_map {
                set src [lindex $item 0]
                set des [lindex $item 1]
                set stcAttr [::sth::sthCore::getswitchprop ::sth::vxlanEvpnOverlay:: $cmdType $des stcattr]
                if {[info exists ::sth::vxlanEvpnOverlay::userArgsArray($src)]} {
                    lappend myValueList -$stcAttr $::sth::vxlanEvpnOverlay::userArgsArray($src)
                }
            }
        }
    }
}

proc ::sth::vxlanEvpnOverlay::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 1
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::vxlanEvpnOverlay:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            if { $switchName == "multi_homed_vtep_type" && [string match -nocase $userArgsArray($switchName) "across_port"]} {
                set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanEvpnOverlayConfigGenParams ]
                set VxlanEvpnOverlayGenVtepPortParamsHdls [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -children-VxlanEvpnOverlayGenVtepPortParams]
                set active_count 0
                foreach hd $VxlanEvpnOverlayGenVtepPortParamsHdls {
                    if {[regexp -nocase "true" [::sth::sthCore::invoke stc::get $hd -active]]} {
                        set active_count [expr $active_count+1]
                    }
                }
                if {$active_count < 2} {
                    ::sth::sthCore::outputConsoleLog "warning" "\"-$switchName $userArgsArray($switchName)\" takes effect when there are two or more VXLAN ports."
                    unset userArgsArray($switchName)
                    break
                }
            } elseif {$switchName == "ippr_gw_type" } {
                if {[regexp -nocase "v6" $userArgsArray(ippr_mode)] && [string match -nocase $userArgsArray($switchName) "VTEP"]} {
                    ::sth::sthCore::outputConsoleLog "warning" "\"-$switchName $userArgsArray($switchName)\" takes effect if \"-$dependSwitch ipv4\"."
                    unset userArgsArray($switchName)
                    break
                }
            }
            
            if {![string match "-" $dependValue] && !([info exists userArgsArray($dependSwitch)] && [string match -nocase $dependValue $userArgsArray($dependSwitch)]) } {
                set validFlag 0
                break
            } 
        }
        
        if {$validFlag == 0} { 
            if {[info exists userArgsArray($switchName)]} {
                ::sth::sthCore::outputConsoleLog "warning" "\"-$switchName\" takes effect if \"-$dependSwitch $dependValue\"."
                unset userArgsArray($switchName)
            }
        }
    }
}
proc ::sth::vxlanEvpnOverlay::getStcOptionValueList {cmdType modeFunc mode procFuncHandle routerIdx} {
    set optionValueList {}
    
    foreach item $::sth::vxlanEvpnOverlay::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::vxlanEvpnOverlay:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::vxlanEvpnOverlay:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::vxlanEvpnOverlay:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                #check dependency
                ::sth::vxlanEvpnOverlay::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::vxlanEvpnOverlay::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::vxlanEvpnOverlay:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::vxlanEvpnOverlay:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::vxlanEvpnOverlay:: $cmdType $opt $::sth::vxlanEvpnOverlay::userArgsArray($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::vxlanEvpnOverlay::userArgsArray($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::vxlanEvpnOverlay::userArgsArray($opt) $routerIdx]
                }
            }
    }
    # Some attributes need to have the same values under certain circumstances
    if {[string match -nocase $modeFunc VxlanConfigGenParams]} {
        getDependValueList $cmdType $modeFunc optionValueList
    }
    return $optionValueList
}

proc ::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_stats_func {returnKeyedList} {
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    set device_list ""
    
        if {[info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)]} {
            set device_list $::sth::vxlanEvpnOverlay::userArgsArray(handle)
        } else {
            set port_list $::sth::vxlanEvpnOverlay::userArgsArray(port_handle)
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
            foreach key [array names ::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_stats_stcobj] {
                if {[regexp -nocase "VxlanVtepConfig" $::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_stats_stcobj($key)]} {
                    set stcattr $::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_stats_stcattr($key)
                    set stcvalue [::sth::sthCore::invoke stc::get $stcobj -$stcattr]
                    keylset retVal $key $stcvalue
                }
            }
            keylset myreturnKeyedList $device $retVal
        }
        keylset myreturnKeyedList status 1
    
}

##############################Functions for vxlan wizard#######################

##########LOGIC############
#created VxlanEvpnOverlayConfigGenParams?
#   1)create VxlanGenVtepPortParams 
#   2)set affiliationport-Targets  
#   3)set other config values
#   4)set return value
#if VxlanEvpnOverlayConfigGenParams not already created
#   5)create VxlanEvpnOverlayConfigGenParams under project 
#   6)follow step 1 to 4 
###########LOGIC ENDS####

proc ::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_port_config_create {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlanEvpnOverlay::userArgsArray
	
	#port_handle is mandatory 
    set portHandle $::sth::vxlanEvpnOverlay::userArgsArray(port_handle)   
	if { ![::info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "port_handle needed when adding port to vxlanEvpnOverlay configuration." {}
	    return $returnKeyedList
    }
    
	set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanEvpnOverlayConfigGenParams ]
	if { $VxlanEvpnOverlayConfigGenParamsHdl == ""} {
	    set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::create "VxlanEvpnOverlayConfigGenParams" -under $::sth::GBLHNDMAP(project)]
	}
	
	# 1)create VxlanGenEvpnOverlayVtepPortParams 
	set VxlanGenEvpnOverlayVtepPortParamsHdl [::sth::sthCore::invoke stc::create "VxlanEvpnOverlayGenVtepPortParams" -under $VxlanEvpnOverlayConfigGenParamsHdl]
	
	# 2)set affiliationport-Targets 
	::sth::sthCore::invoke stc::config $VxlanGenEvpnOverlayVtepPortParamsHdl "-AffiliationPort-Targets $portHandle"	
	
	# 3)set other config
	set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_port_config processConfigCmd create $VxlanGenEvpnOverlayVtepPortParamsHdl 0]
	::sth::sthCore::invoke stc::config $VxlanGenEvpnOverlayVtepPortParamsHdl $optionValueList
	
    keylset myreturnKeyedList handle $VxlanGenEvpnOverlayVtepPortParamsHdl
    keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    
    return $myreturnKeyedList

}

#################END OF emulation_vxlan_port_config APIs#############################

##########LOGIC for emulation_nonvxlan_evpn_overlay_port_config_create############
#created VxlanEvpnOverlayConfigGenParams?
#   1)create VxlanEvpnOverlayGenL2VniHostPortParams 
#   2)set affiliationport-Targets  
#   3)set other configuration
#   4)create VxlanEvpnOverlayGenL3VniHostPortParams 
#   5)set affiliationport-Targets  
#   6)set other config
#   7)set return value
#if VxlanEvpnOverlayConfigGenParams not already created
#   8)create VxlanEvpnOverlayConfigGenParams under project 
#   9)follow step 1 to 7
###########################LOGIC ENDS###############################

proc ::sth::vxlanEvpnOverlay::emulation_nonvxlan_evpn_overlay_port_config_create {returnKeyedList} {
   
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlanEvpnOverlay::userArgsArray
        
    #port_handle is mandatory 
    set portHandle $::sth::vxlanEvpnOverlay::userArgsArray(port_handle)   
	if { ![::info exists ::sth::vxlanEvpnOverlay::userArgsArray(port_handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "port_handle needed when adding port to vxlan configuration." {}
	    return $returnKeyedList
    }

	set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanEvpnOverlayConfigGenParams]
	if { $VxlanEvpnOverlayConfigGenParamsHdl == ""} {
	    set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::create "VxlanEvpnOverlayConfigGenParams" -under $::sth::GBLHNDMAP(project)]
	}
	set VxlanEvpnOverlayGenHostPortParamsHandles ""
    if {[regexp -nocase "L2" $::sth::vxlanEvpnOverlay::userArgsArray(type)]} {
        # 1)create VxlanEvpnOverlayGenL2VniHostPortParams
        set VxlanEvpnOverlayGenL2VniHostPortParamsHdl [::sth::sthCore::invoke stc::create "VxlanEvpnOverlayGenL2VniHostPortParams" -under $VxlanEvpnOverlayConfigGenParamsHdl]
        # 2)set affiliationport-Targets 
        ::sth::sthCore::invoke stc::config $VxlanEvpnOverlayGenL2VniHostPortParamsHdl "-AffiliationPort-Targets $portHandle"	
        # 3)set other config
        set optionValueList [getStcOptionValueList emulation_nonvxlan_evpn_overlay_port_config processL2ConfigCmd create $VxlanEvpnOverlayGenL2VniHostPortParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanEvpnOverlayGenL2VniHostPortParamsHdl $optionValueList 
        
        lappend VxlanEvpnOverlayGenHostPortParamsHandles $VxlanEvpnOverlayGenL2VniHostPortParamsHdl
        keylset myreturnKeyedList l2_handle $VxlanEvpnOverlayGenL2VniHostPortParamsHdl
    }
   
    if {[regexp -nocase "L3" $::sth::vxlanEvpnOverlay::userArgsArray(type)]} {
        # 4)create VxlanEvpnOverlayGenL3VniHostPortParams
        set VxlanEvpnOverlayGenL3VniHostPortParamsHdl [::sth::sthCore::invoke stc::create "VxlanEvpnOverlayGenL3VniHostPortParams" -under $VxlanEvpnOverlayConfigGenParamsHdl]
        # 5)set affiliationport-Targets 
        ::sth::sthCore::invoke stc::config $VxlanEvpnOverlayGenL3VniHostPortParamsHdl "-AffiliationPort-Targets $portHandle"
        # 6)set other config
        set optionValueList [getStcOptionValueList emulation_nonvxlan_evpn_overlay_port_config processL3ConfigCmd create $VxlanEvpnOverlayGenL3VniHostPortParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanEvpnOverlayGenL3VniHostPortParamsHdl $optionValueList 
        
        lappend VxlanEvpnOverlayGenHostPortParamsHandles $VxlanEvpnOverlayGenL3VniHostPortParamsHdl
        keylset myreturnKeyedList l3_handle $VxlanEvpnOverlayGenL3VniHostPortParamsHdl
    }
    keylset myreturnKeyedList handle $VxlanEvpnOverlayGenHostPortParamsHandles
    keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    
    return $myreturnKeyedList
}

########Logic for emulation_vxlan_evpn_overlay_wizard_config_create############
#created VxlanEvpnOverlayConfigGenParams?
#   1)config values for VxlanEvpnOverlayConfigGenParams
#   2)config values for VxlanEvpnOverlayL2VniDeviceConfigParams and VxlanEvpnOverlayL3VniDeviceConfigParams
#   3)config values for VxlanEvpnOverlayGenVtepParams
#   4)config values for BgpVxlanEvpnOverlayRouteParams
#   5)config values for VxlanEvpnOverlayTrafficParams
#   6)config values for VxlanEvpnOverlayL2L3SegmentConfigParams
#   7)config values for VxlanIpPrefixRouteParams
#   8)get vtep_handle,vm_handle and host_handle           
#   9)set return value
#if VxlanEvpnOverlayConfigGenParams not already created
#   10)create VxlanEvpnOverlayConfigGenParams under project 
#   11)follow step 1 to 9 
###################################################################
proc ::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_wizard_config_create {returnKeyedList} {
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlanEvpnOverlay::userArgsArray
        
    set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VxlanEvpnOverlayConfigGenParams]
	if { $VxlanEvpnOverlayConfigGenParamsHdl == ""} {
	    set VxlanEvpnOverlayConfigGenParamsHdl [::sth::sthCore::invoke stc::create "VxlanEvpnOverlayConfigGenParams" -under $::sth::GBLHNDMAP(project)]
	}
    
	#1)config values for VxlanEvpnOverlayConfigGenParams
    set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config VxlanConfigGenParams create $VxlanEvpnOverlayConfigGenParamsHdl 0]
	::sth::sthCore::invoke stc::config $VxlanEvpnOverlayConfigGenParamsHdl $optionValueList  
		
	#2)config values for VxlanGenHostParams
    if {[regexp -nocase "L2" $::sth::vxlanEvpnOverlay::userArgsArray(traffic_endpoint_mode)]} {
        set VxlanGenHostParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-VxlanEvpnOverlayL2VniDeviceConfigParams]
        if {$VxlanGenHostParamsHdl != "" } {
            set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config VxlanGenHostParams create $VxlanGenHostParamsHdl 0]
            ::sth::sthCore::invoke stc::config $VxlanGenHostParamsHdl $optionValueList
        }
    } 
    if {[regexp -nocase "L3" $::sth::vxlanEvpnOverlay::userArgsArray(traffic_endpoint_mode)]} {
        set VxlanGenHostParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-VxlanEvpnOverlayL3VniDeviceConfigParams]
        if {$VxlanGenHostParamsHdl != "" } {
            set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config VxlanGenL3HostParams create $VxlanGenHostParamsHdl 0]
            ::sth::sthCore::invoke stc::config $VxlanGenHostParamsHdl $optionValueList
        }
    }
    
    #3)config values for VxlanGenVtepParams
    set VxlanGenVtepParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-VxlanEvpnOverlayGenVtepParams]
    if {$VxlanGenVtepParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config VxlanGenVtepParams create $VxlanGenVtepParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanGenVtepParamsHdl $optionValueList
    }
    
    #4)config values for BgpEvpnRouteParams
    set BgpEvpnRouteParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-BgpVxlanEvpnOverlayRouteParams]
    if {$BgpEvpnRouteParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config BgpEvpnRouteParams create $BgpEvpnRouteParamsHdl 0]
        ::sth::sthCore::invoke stc::config $BgpEvpnRouteParamsHdl $optionValueList
    }
    
    #5)config values for VxlanTrafficParams
    set VxlanTrafficParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-VxlanEvpnOverlayTrafficParams]
    if {$VxlanTrafficParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config VxlanTrafficParams create $VxlanTrafficParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanTrafficParamsHdl $optionValueList
    }
    
    #6)config values for VxlanEvpnOverlayL2L3SegmentConfigParams
    set VxlanL2L3VniParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-VxlanEvpnOverlayL2L3SegmentConfigParams]
    if {$VxlanL2L3VniParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config VxlanConfigL2L3Params create $VxlanL2L3VniParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanL2L3VniParamsHdl $optionValueList
    }
    
    #7)config values for VxlanIpPrefixRouteParams
    set VxlanIpPrefixRouteParamsHdl [::sth::sthCore::invoke stc::get $VxlanEvpnOverlayConfigGenParamsHdl -Children-VxlanEvpnOverlayIpPrefixRouteParams]
    if {$VxlanIpPrefixRouteParamsHdl != "" } {
        set optionValueList [getStcOptionValueList emulation_vxlan_evpn_overlay_wizard_config IpPrefixRouteParams create $VxlanIpPrefixRouteParamsHdl 0]
        ::sth::sthCore::invoke stc::config $VxlanIpPrefixRouteParamsHdl $optionValueList
    }
	
    #Expand and 8) get vtep_handle,vm_handle and host_handle  
    set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]
    set pre_streamblocks [sth::get_handles -type streamblock]
    if {[keylget pre_streamblocks status] == 1} {
        set pre_streamblockStr [keylget pre_streamblocks handles]
    } else {
        set pre_streamblockStr ""
    }
    stc::perform VxlanEvpnOverlayConfigGenConfigExpandCommand -GenParams $VxlanEvpnOverlayConfigGenParamsHdl -ClearExisting no
    # get handles after expanding
    set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]
    set childrenList [split $childrenStr]
    foreach child $pre_childrenStr {
        set x [lsearch $childrenList $child]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    # save new handles created by expanding vxlan, for future deletion
    set ::sth::vxlanEvpnOverlay::new_handles $childrenList
    # get streamblock handles after expanding
    set streamblockList ""
    set streamblocks [sth::get_handles -type streamblock]
    if {[keylget streamblocks status] == 1} {
        set streamblockStr [keylget streamblocks handles]
        set streamblockList [split $streamblockStr]
        foreach child $pre_streamblocks {
            set x [lsearch $streamblockList $child]
            if { $x > -1 } {
                set streamblockList [lreplace $streamblockList $x $x]
            }
        }
    } 
    
    set emulatedDeviceHdl ""
    set host_handle ""
    set vtep_handle ""
    set vm_handle ""
    set ip_prefix_handle ""
    set device_children ""
    set AffPortList ""
    set index 1
    foreach child $childrenList {
        if { [string first "emulateddevice" [string tolower $child]] > -1} {
            lappend emulatedDeviceHdl $child
        }
    }
    foreach device $emulatedDeviceHdl {
        set bgpevpnmacadv_handle ""
        set bgpevpnippr_handle ""
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
                    if {[regexp "^bgpevpnmacadv" $bgpevpn_hdl]} {
                        lappend bgpevpnmacadv_handle $bgpevpn_hdl
                    } elseif {[regexp "^bgpevpnipprefix" $bgpevpn_hdl]} {
                        lappend bgpevpnippr_handle $bgpevpn_hdl
                    }
                }
                set AffPort [::sth::sthCore::invoke stc::get $device -AffiliationPort-Targets]
                if {[lsearch $AffPortList $AffPort] == -1} {
                    set index 1
                }
                lappend AffPortList $AffPort
                keylset vtep_handle $AffPort.$index.device_handle $device 
                keylset vtep_handle $AffPort.$index.bgp_handle $bgp_handle
                if { $bgpevpnmacadv_handle != "" } {
                    keylset vtep_handle $AffPort.$index.bgpevpnmacadv_handle $bgpevpnmacadv_handle
                }
                if { $bgpevpnippr_handle != "" } {
                    keylset vtep_handle $AffPort.$index.bgpevpnippr_handle $bgpevpnippr_handle
                }
                # also return VM and IP prefix handles by vtep
                set vmlink_list ""
                set ipprlink_list ""
                set vmlinks [::sth::sthCore::invoke stc::get $device -linkdstdevice-Sources]
                if { $vmlinks != "" } {
                    foreach link $vmlinks {
                        set linksrc [::sth::sthCore::invoke stc::get $link -containedlink-Sources]
                        set device_name [::sth::sthCore::invoke stc::get $linksrc -Name]
                        if {[string first "VM Device" $device_name] > -1} {
                            lappend vmlink_list $linksrc
                        } elseif { [string first "IP Prefix Device" $device_name] > -1 } {
                            lappend ipprlink_list $linksrc
                        }
                    }
                    if { $vmlink_list != "" } {
                        keylset vtep_handle $AffPort.$index.vm_handle $vmlink_list
                    }
                    if { $ipprlink_list != "" } {
                        keylset vtep_handle $AffPort.$index.ip_prefix_handle $ipprlink_list
                    }
                }
                incr index
            } else {
                lappend vtep_handle $device
            }
        } elseif { [string first "VM Device" $deviceName] > -1 } {
            lappend vm_handle $device
        } elseif { [string first "IP Prefix Device" $deviceName] > -1 } {
            lappend ip_prefix_handle $device
        } else {
            lappend host_handle $device
        }
    }
    
    if { $vtep_handle != "" } {
        keylset myreturnKeyedList vtep_handle $vtep_handle
    }
    if { $vm_handle != "" } {
        keylset myreturnKeyedList vm_handle $vm_handle
    }
    if { $host_handle != "" } {
        keylset myreturnKeyedList host_handle $host_handle
    }
    if { $ip_prefix_handle != "" } {
        keylset myreturnKeyedList ip_prefix_handle $ip_prefix_handle
    }
    if { $streamblockList != "" } {
        keylset myreturnKeyedList streamblock_handle $streamblockList
    }
    keylset myreturnKeyedList handle $VxlanEvpnOverlayConfigGenParamsHdl
    keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    
    return $myreturnKeyedList

}

proc ::sth::vxlanEvpnOverlay::emulation_vxlan_evpn_overlay_wizard_config_delete {returnKeyedList} {
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::vxlanEvpnOverlay::userArgsArray
    
    #handle needed for delete mode
	if { ![::info exists ::sth::vxlanEvpnOverlay::userArgsArray(handle)]} {
    	::sth::sthCore::processError myreturnKeyedList "handles needed for delete mode " {}
	    return $returnKeyedList
    }
    
    #Delete the handles
    set delete_list ""
    set handles_in_list [::sth::sthCore::keylvalues $::sth::vxlanEvpnOverlay::userArgsArray(handle) "status"]
    # remove duplicate handles
    foreach hd "$handles_in_list $::sth::vxlanEvpnOverlay::new_handles" {
        if {[lsearch $delete_list $hd] == -1} {
            lappend delete_list $hd
        }
    }
    
    ::sth::sthCore::invoke stc::perform Delete -ConfigList $delete_list
    
    keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    return $myreturnKeyedList
}


##############################End Functions for vxlan wizard#######################


