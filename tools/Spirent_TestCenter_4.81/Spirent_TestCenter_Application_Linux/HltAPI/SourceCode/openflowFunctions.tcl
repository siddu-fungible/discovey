namespace eval ::sth::openflow:: {
	variable switchHandleArray
	variable keyedList
}

proc ::sth::openflow::emulation_openflow_config_enable {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
	variable ::sth::openflow::keyedList
	set ::sth::openflow::keyedList ""
	
	set device $::sth::openflow::userArgsArray(handle)
	set functionsToRun [getFunctionToRun emulation_openflow_config enable]
	foreach func $functionsToRun {
		$func $device enable
	}
	
	set myreturnKeyedList $::sth::openflow::keyedList
    return $myreturnKeyedList
}

proc ::sth::openflow::emulation_openflow_config_modify {returnKeyedList} {

    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
	variable ::sth::openflow::keyedList
    set ::sth::openflow::keyedList ""
	
   	set device $::sth::openflow::userArgsArray(handle)
	set functionsToRun [getFunctionToRun emulation_openflow_config modify]
	foreach func $functionsToRun {
		$func $device modify
	}
	
	set myreturnKeyedList $::sth::openflow::keyedList
    return $myreturnKeyedList
}


proc ::sth::openflow::emulation_openflow_config_delete {returnKeyedList} {

    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
	variable ::sth::openflow::keyedList
    set ::sth::openflow::keyedList ""
	
	if {[info exists ::sth::openflow::userArgsArray(handle)]} {
        set handleList $::sth::openflow::userArgsArray(handle)
        if {[regexp -nocase {host} $handleList]} {
			set ofHndList ""
            foreach host $handleList {
                lappend ofHndList [::sth::sthCore::invoke stc::get $host -children-OpenflowControllerProtocolConfig]
            }
			set handleList $ofHndList
        }
		::sth::sthCore::invoke stc::perform delete -ConfigList $handleList
		keylset myreturnKeyedList status $::sth::sthCore::SUCCESS
	} else {
		::sth::sthCore::log error "Either handle or port_handle to be specified"
		keylset myreturnKeyedList status $::sth::sthCore::FAILURE
	}
	
    return $myreturnKeyedList
}


proc ::sth::openflow::getFunctionToRun {mycmd mode} {
	variable sortedSwitchPriorityList
	set functionsToRun {}
	foreach item $sortedSwitchPriorityList {
		foreach {priority switchname} $item {
			# make sure the option is supported
			if {![::sth::sthCore::getswitchprop ::sth::openflow:: $mycmd $switchname supported]} {
				::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
				return -code error $returnKeyedList 
			}
			if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::openflow:: $mycmd $switchname mode] "_none_"]} { 
				continue 
			}
			set func [::sth::sthCore::getModeFunc ::sth::openflow:: $mycmd $switchname $mode]
			if {[regexp {^switch_transport_} $func] || [regexp {^bound_traffic_} $func]
				|| [regexp {^meter_band_} $func] || [regexp {^group_action_set} $func]
                || [regexp {^rm_action} $func] || [regexp {^rm_match} $func]
                || [regexp {^custom_flowblock_match} $func] || [regexp {^custom_flowblock_action} $func]
                || [regexp {^custom_flowblock_goto_table} $func] || [regexp {^custom_flowblock_metadata} $func]
                || [regexp {^custom_flowblock_write_action} $func] || [regexp {^custom_flowblock_clear_action} $func]
                || [regexp {^custom_flowblock_meter} $func] || [regexp {^custom_flowblock_exp} $func]} {
				continue
			}
			if {[lsearch $functionsToRun $func] == -1} {
				lappend functionsToRun $func
			}
		}
	}
	
	return $functionsToRun
}


proc ::sth::openflow::group_entry_config {devhandle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]

	group_entry_common $openflow_handle $mode
}

proc ::sth::openflow::group_entry_modify {devhandle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]
	if {$openflow_handle eq ""} {
		set openflow_handle $devhandle
		set group_entry_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowGroupEntryConfig]
	} else {
		set group_entry_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowGroupEntryConfig]
	}
    sth::sthCore::invoke stc::perform delete -ConfigList "$group_entry_handles"
	group_entry_common $openflow_handle $mode
}

proc ::sth::openflow::group_entry_common {openflow_handle mode} {
	variable ::sth::openflow::switchHandleArray
	variable ::sth::openflow::keyedList
	
	set act $mode
	if {$mode eq "enable" || $mode eq "add"} {
		set act "config"
	}
	set optionValueList [getStcOptionValueList emulation_openflow_config group_entry_$act $mode ""]
	
	regexp {\-num\s?(\d+)} $optionValueList match num
	if {![info exists num]} {
		return -code 1 -errorcode -1 "the number of group_id should be more than 1."
	}

	set myvalueList [regsub -all {\-num\s?(\d+)} $optionValueList ""]
	set openflowParamList [processSplitList $num $myvalueList 0]
	array set openflowParamArray $openflowParamList

	set group_entry_handles ""
	for {set i 0} {$i<$num} {incr i} {
		set myOptionValues $openflowParamArray($i)
		if {[llength $myOptionValues]} {
			set myhandle $openflow_handle
			if {[regexp {^openflowcontrollerprotocolconfig\d+$} $openflow_handle]} {
				set myhandle [sth::sthCore::invoke stc::create OpenflowGroupEntryConfig -under $openflow_handle]
			}
			sth::sthCore::invoke stc::config $myhandle $myOptionValues
			
			set group_entry_handles [concat $group_entry_handles $myhandle]
		}
	}
	
	keylset ::sth::openflow::keyedList group_entry_handles $group_entry_handles
}


proc ::sth::openflow::rm_config {dev_handle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $dev_handle -children-OpenflowControllerProtocolConfig]
    
	rm_common $openflow_handle $mode
}

proc ::sth::openflow::rm_modify {dev_handle mode} {
	set rm_handle [::sth::sthCore::invoke stc::get $dev_handle -children-OpenflowReactiveModeRuleConfig]

    sth::sthCore::invoke stc::perform delete -ConfigList "$rm_handle"
	rm_common $dev_handle $mode
}


proc ::sth::openflow::rm_common {openflow_handle mode} {
	variable ::sth::openflow::switchHandleArray
	variable ::sth::openflow::keyedList

	set act $mode
	if {$mode eq "enable" || $mode eq "add"} {
		set act "config"
	}
    
	set optionValueList [getStcOptionValueList emulation_openflow_config rm_$act $mode ""]
	set actionValueList [getStcOptionValueList emulation_openflow_config rm_action_$act $mode ""]
	set matchValueList [getStcOptionValueList emulation_openflow_config rm_match_$act $mode ""]

    set rm_handle [::sth::sthCore::invoke stc::create OpenflowReactiveModeRuleConfig -under $openflow_handle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $rm_handle $optionValueList
    }

    if {[llength $actionValueList]} {    
        ::sth::openflow::process_rm_packet_out_action $rm_handle $actionValueList
    }

    if {[llength $matchValueList]} { 
        ::sth::openflow::process_rm_match $rm_handle $matchValueList
    }

	keylset ::sth::openflow::keyedList rm_handle $rm_handle
}


proc ::sth::openflow::process_rm_packet_out_action {rm_handle actionValueList} {

    set pkt_action_handle [::sth::sthCore::invoke stc::get $rm_handle -children-OpenflowReactivePacketOutActions]
    #delete default headers
    set childrenHnd [::sth::sthCore::invoke stc::get $pkt_action_handle -children]
    ::sth::sthCore::invoke stc::perform delete -ConfigList $childrenHnd
    
    set rm_action_hnd [::sth::sthCore::invoke stc::create openflow:ReactiveModeAction -under $pkt_action_handle]
    set action_hnd [::sth::sthCore::invoke stc::create Action -under $rm_action_hnd]

    #process user input
    set actionValue [regsub {^-FrameConfig\s} $actionValueList ""]
    set parrayValue [split $actionValue ","]
    foreach value $parrayValue {
        switch -regexp -- $value {
             "output" {
                set value [regsub {^output:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create output -under $rm_act_hnd -port_number $value]
             }
             "controller" {
                set value [regsub {^controller:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create controller -under $rm_act_hnd -max_length $value]
             }
             "all" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create all -under $rm_act_hnd]
             }
             "copy_ttl_in" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create copy_ttl_in -under $rm_act_hnd]
             }
             "copy_ttl_out" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create copy_ttl_out -under $rm_act_hnd]
             }
             "dec_mpls_ttl" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create dec_mpls_ttl -under $rm_act_hnd]
             }
             "dec_ttl" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create dec_ttl -under $rm_act_hnd]
             }
             "flood" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create flood -under $rm_act_hnd]
             }
             "local" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create local -under $rm_act_hnd]
             }
             "normal" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create normal -under $rm_act_hnd]
             }
             "pop_pbb" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create pop_pbb -under $rm_act_hnd]
             }
             "group" {
                set value [regsub {^group:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create group -under $rm_act_hnd -group_id $value]
             }
             "in_port" {
                set value [regsub {^in_port:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create in_port -under $rm_act_hnd]
             }
             "mod_sctp_dst" {
                set value [regsub {^mod_sctp_dst:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_sctp_dst -under $rm_act_hnd -port_number $value]
             }
             "mod_sctp_src" {
                set value [regsub {^mod_sctp_src:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_sctp_src -under $rm_act_hnd -port_number $value]
             }
             "mod_tcp_dst" {
                set value [regsub {^mod_tcp_dst:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_tcp_dst -under $rm_act_hnd -port_number $value]
             }
             "mod_tcp_src" {
                set value [regsub {^mod_tcp_src:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_tcp_src -under $rm_act_hnd -port_number $value]
             }
             "mod_udp_dst" {
                set value [regsub {^mod_udp_dst:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_udp_dst -under $rm_act_hnd -port_number $value]
             }
             "mod_udp_src" {
                set value [regsub {^in_port:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_udp_dst -under $rm_act_hnd -port_number $value]
             }
             "mod_dl_dst" {
                set value [regsub {^mod_dl_dst:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_dl_dst -under $rm_act_hnd -addr $value]
             }
             "mod_dl_src" {
                set value [regsub {^mod_dl_src:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_dl_src -under $rm_act_hnd -addr $value]
             }
             "mod_ipv6_dst" {
                set value [regsub {^mod_ipv6_dst:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_ipv6_dst -under $rm_act_hnd -addr $value]
             }
             "mod_ipv6_src" {
                set value [regsub {^mod_ipv6_src:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_ipv6_src -under $rm_act_hnd -addr $value]
             }
             "mod_nw_dst" {
                set value [regsub {^mod_nw_dst:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_nw_dst -under $rm_act_hnd -addr $value]
             }
             "mod_nw_src" {
                set value [regsub {^mod_nw_src:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_nw_src -under $rm_act_hnd -addr $value]
             }
             "pop_vlan" {
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create pop_vlan -under $rm_act_hnd]
             }
             "mod_icmpv6_code" {
                set value [regsub {^mod_icmpv6_code:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_icmpv6_code -under $rm_act_hnd -code $value]
             }
             "mod_icmpv6_type" {
                set value [regsub {^mod_icmpv6_type:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_icmpv6_type -under $rm_act_hnd -type $value]
             }
             "mod_ipv6_label" {
                set value [regsub {^mod_ipv6_label:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_ipv6_label -under $rm_act_hnd -label $value]
             }
             "mod_nd_sll" {
                set value [regsub {^mod_nd_sll:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_nd_sll -under $rm_act_hnd -source $value]
             }
             "mod_nd_tll" {
                set value [regsub {^mod_nd_tll:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_nd_tll -under $rm_act_hnd -source $value]
             }
             "mod_nd_target" {
                set value [regsub {^mod_nd_target:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_nd_target -under $rm_act_hnd -target $value]
             }
             "mod_nw_tos" {
                set value [regsub {^mod_nw_tos:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_nw_tos -under $rm_act_hnd -tos $value]
             }
             "mod_tun_id" {
                set value [regsub {^mod_tun_id:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_tun_id -under $rm_act_hnd -tunnel_id $value]
             }
             "mod_vlan_pcp" {
                set value [regsub {^mod_vlan_pcp:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_vlan_pcp -under $rm_act_hnd -pcp $value]
             }
             "mod_vlan_vid" {
                set value [regsub {^mod_vlan_vid:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create mod_vlan_vid -under $rm_act_hnd -id $value]
             }
             "pop_mpls" {
                set value [regsub {^pop_mpls:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create pop_mpls -under $rm_act_hnd -ethernet_type $value]
             }
             "push_mpls" {
                set value [regsub {^push_mpls:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create push_mpls -under $rm_act_hnd -ethernet_type $value]
             }
             "push_pbb" {
                set value [regsub {^push_pbb:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create push_pbb -under $rm_act_hnd -ethernet_type $value]
             }
             "push_vlan" {
                set value [regsub {^push_vlan:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create push_vlan -under $rm_act_hnd -ethernet_type $value]
             }
             "set_mpls_bos" {
                set value [regsub {^set_mpls_bos:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create set_mpls_bos -under $rm_act_hnd -bos $value]
             }
             "set_mpls_label" {
                set value [regsub {^set_mpls_label:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create set_mpls_label -under $rm_act_hnd -label $value]
             }
             "set_mpls_tc" {
                set value [regsub {^set_mpls_tc:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create set_mpls_tc -under $rm_act_hnd -traffic_class $value]
             }
             "set_mpls_ttl" {
                set value [regsub {^set_mpls_ttl:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create set_mpls_ttl -under $rm_act_hnd -ttl $value]
             }
             "set_queue" {
                set value [regsub {^set_queue:} $value ""]
                set rm_act_hnd [::sth::sthCore::invoke stc::create RmAction -under $action_hnd]
                set hnd [::sth::sthCore::invoke stc::create set_queue -under $rm_act_hnd -queue $value]
             }
             default {
                ::sth::sthCore::log error "Incorrect \"rm_action_field\" value: $value"
             }
         }
    }
}

proc ::sth::openflow::process_rm_match {rm_handle matchValueList} {

    set match_handle [::sth::sthCore::invoke stc::get $rm_handle -children-OpenflowReactiveMatchFields]
    #delete default headers
    set childrenHnd [::sth::sthCore::invoke stc::get $match_handle -children]
    ::sth::sthCore::invoke stc::perform delete -ConfigList $childrenHnd

    set rm_match_hnd [::sth::sthCore::invoke stc::create openflow:ReactiveModeMatch -under $match_handle]
    set match_hnd [::sth::sthCore::invoke stc::create Match -under $rm_match_hnd]
    
    #process user input
    set matchValue [regsub {^-FrameConfig\s} $matchValueList ""]
    set matchValue [regsub {^\{} $matchValue ""]
    set matchValue [regsub {\}$} $matchValue ""]
    set parrayValue [regexp -all -inline {\S+} $matchValue]
    #set parrayValue [split $matchValue " "]
    foreach value $parrayValue {
        switch -regexp -- $value {
             "dl_src" {
                set value [regsub {^dl_src=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                if {[regexp {/} $value]} {
                    regexp {(.*)/(.*)} $value val addr mask
                    ::sth::sthCore::invoke stc::create dl_src -under $rm_match_handle -useMask 1 -addr $addr -mask $mask
                } else {
                    ::sth::sthCore::invoke stc::create dl_src -under $rm_match_handle -addr $value
                }
             }
             "dl_dst" {
                set value [regsub {^dl_dst=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                if {[regexp {/} $value]} {
                    regexp {(.*)/(.*)} $value val addr mask
                    ::sth::sthCore::invoke stc::create dl_dst -under $rm_match_handle -useMask 1 -addr $addr -mask $mask
                } else {
                    ::sth::sthCore::invoke stc::create dl_dst -under $rm_match_handle -addr $value
                }
             }
			"dl_type" {
				set value [regsub {^dl_type=} $value ""]
				set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create dl_type -under $rm_match_handle -ethernet_type $value
			}
            "dl_vlan_pcp" {
                set value [regsub {^dl_vlan_pcp=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                ::sth::sthCore::invoke stc::create dl_vlan_pcp -under $rm_match_handle -priority $value
            }
            "dl_vlan" {
                set value [regsub {^dl_vlan=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                if {[regexp {/} $value]} {
                    regexp {(.*)/(.*)} $value val addr mask
                    ::sth::sthCore::invoke stc::create dl_vlan -under $rm_match_handle -useMask 1 -id $addr -mask $mask
                } else {
                    ::sth::sthCore::invoke stc::create dl_vlan -under $rm_match_handle -id $value
                }
            }
            "in_port" {
                set value [regsub {^in_port=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                ::sth::sthCore::invoke stc::create in_port -under $rm_match_handle -port_number $value
            }
            "nw_dst" {
                set value [regsub {^nw_dst=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                if {[regexp {/} $value]} {
                    regexp {(.*)/(.*)} $value val addr mask
                    ::sth::sthCore::invoke stc::create nw_dst -under $rm_match_handle -useMask 1 -addr $addr -mask $mask
                } else {
                    ::sth::sthCore::invoke stc::create nw_dst -under $rm_match_handle -addr $value
                }
            }
            "nw_ecn" {
                set value [regsub {^nw_ecn=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                ::sth::sthCore::invoke stc::create nw_ecn -under $rm_match_handle -tos $value
            }
            "nw_proto" {
                set value [regsub {^nw_proto=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                ::sth::sthCore::invoke stc::create nw_proto -under $rm_match_handle -protocol $value
            }
            "nw_src" {
                set value [regsub {^nw_src=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                if {[regexp {/} $value]} {
                    regexp {(.*)/(.*)} $value val addr mask
                    ::sth::sthCore::invoke stc::create nw_src -under $rm_match_handle -useMask 1 -addr $addr -mask $mask
                } else {
                    ::sth::sthCore::invoke stc::create nw_src -under $rm_match_handle -addr $value
                }
            }
            "nw_tos" {
                set value [regsub {^nw_tos=} $value ""]
                set rm_match_handle [::sth::sthCore::invoke stc::create RmMatch -under $match_hnd]
                ::sth::sthCore::invoke stc::create nw_tos -under $rm_match_handle -tos $value
            }
             default {
                ::sth::sthCore::log error "Incorrect \"rm_match_field\" value: $value"
             }
         }
    }
}


proc ::sth::openflow::process_custom_flowblock_match {handle matchValueList} {

	 set flowHandle [::sth::sthCore::invoke stc::get $handle -children-openflow:Flow]
	 if { $flowHandle == ""} {
		 set flowHandle [::sth::sthCore::invoke stc::create openflow:Flow -under $handle]
	 }
     set match_hnd [::sth::sthCore::invoke stc::create Match -under $flowHandle]
    
     #process user input
     set matchValue [regsub {^-FrameConfig\s} $matchValueList ""]
     set matchValue [regsub {^\{} $matchValue ""]
     set matchValue [regsub {\}$} $matchValue ""]
     set parrayValue [regexp -all -inline {\S+} $matchValue]

     foreach value $parrayValue {
         switch -regexp -- $value {
			"arp_op" {
				set value [regsub {^arp_op=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create arp_op -under $of_match_handle -type $value
			}
			"arp_sha" {
				 set value [regsub {^arp_sha=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create arp_sha -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create arp_sha -under $of_match_handle -addr $value
				 }
			}
			"arp_spa" {
				 set value [regsub {^arp_spa=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create arp_spa -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create arp_spa -under $of_match_handle -addr $value
				 }
			}
			"arp_tha" {
				 set value [regsub {^arp_tha=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create arp_tha -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create arp_tha -under $of_match_handle -addr $value
				 }
			}
			"arp_tpa" {
				 set value [regsub {^arp_tpa=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create arp_tpa -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create arp_tpa -under $of_match_handle -addr $value
				 }
			}
			"dl_dst" {
				 set value [regsub {^dl_dst=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create dl_dst -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create dl_dst -under $of_match_handle -addr $value
				 }
			}
			"dl_src" {
				 set value [regsub {^dl_src=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create dl_src -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create dl_src -under $of_match_handle -addr $value
				 }
			}
			"dl_type" {
				set value [regsub {^dl_type=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create dl_type -under $of_match_handle -ethernet_type $value
			}
			"dl_vlan" {
				 set value [regsub {^dl_vlan=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val id mask
					 ::sth::sthCore::invoke stc::create dl_vlan -under $of_match_handle -useMask 1 -id $id -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create dl_vlan -under $of_match_handle -id $value
				 }
			}
			"dl_vlan_pcp" {
				set value [regsub {^dl_vlan_pcp=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create dl_vlan_pcp -under $of_match_handle -priority $value
			}
			"exp" {
				 set value [regsub {^exp=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)/(.*)/(.*)} $value val expField expId expVal mask
					 ::sth::sthCore::invoke stc::create exp -under $of_match_handle -useMask 1 -experimenterField $expField -experimenterId $expId -experimenterValue $expVal -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create exp -under $of_match_handle -experimenterId $value
				 }
			}
			"ext_hdr" {
				 set value [regsub {^ext_hdr=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val id mask
					 ::sth::sthCore::invoke stc::create ext_hdr -under $of_match_handle -useMask 1 -header $id -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create ext_hdr -under $of_match_handle -header $value
				 }
			}
			"icmpv4_code" {
				set value [regsub {^icmpv4_code=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create icmpv4_code -under $of_match_handle -code $value
			}
			"icmpv4_type" {
				set value [regsub {^icmpv4_type=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create icmpv4_type -under $of_match_handle -type $value
			}
			"icmpv6_code" {
				set value [regsub {^icmpv6_code=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create icmpv6_code -under $of_match_handle -code $value
			}
			"icmpv6_type" {
				set value [regsub {^icmpv6_type=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create icmpv6_type -under $of_match_handle -type $value
			}
			"in_phy_port" {
				set value [regsub {^in_phy_port=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create in_phy_port -under $of_match_handle -port_number $value
			}
			"in_port" {
				set value [regsub {^in_port=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create in_port -under $of_match_handle -port_number $value
			}
			"ipv6_dst" {
				 set value [regsub {^ipv6_dst=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create ipv6_dst -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create ipv6_dst -under $of_match_handle -addr $value
				 }
			}
			"ipv6_label" {
				 set value [regsub {^ipv6_label=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val label mask
					 ::sth::sthCore::invoke stc::create ipv6_label -under $of_match_handle -useMask 1 -label $label -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create ipv6_label -under $of_match_handle -label $value
				 }
			}
			"ipv6_src" {
				 set value [regsub {^ipv6_src=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create ipv6_src -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create ipv6_src -under $of_match_handle -addr $value
				 }
			}
			"metadata" {
				 set value [regsub {^metadata=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val id mask
					 ::sth::sthCore::invoke stc::create metadata -under $of_match_handle -useMask 1 -id $id -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create metadata -under $of_match_handle -id $value
				 }
			}
			"mpls_bos" {
				set value [regsub {^mpls_bos=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create mpls_bos -under $of_match_handle -bos $value
			}
			"mpls_label" {
				set value [regsub {^mpls_label=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create mpls_label -under $of_match_handle -mpls_label $value
			}
			"mpls_tc" {
				set value [regsub {^mpls_tc=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create mpls_tc -under $of_match_handle -traffic_class $value
			}
			"nd_sll" {
				set value [regsub {^nd_sll=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create nd_sll -under $of_match_handle -source $value
			}
			"nd_target" {
				set value [regsub {^nd_target=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create nd_target -under $of_match_handle -target $value
			}
			"nd_tll" {
				set value [regsub {^nd_tll=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create nd_tll -under $of_match_handle -source $value
			}
			"nw_src" {
				 set value [regsub {^nw_src=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create nw_src -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create nw_src -under $of_match_handle -addr $value
				 }
			}
			"nw_dst" {
				 set value [regsub {^nw_dst=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val addr mask
					 ::sth::sthCore::invoke stc::create nw_dst -under $of_match_handle -useMask 1 -addr $addr -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create nw_dst -under $of_match_handle -addr $value
				 }
			}
			"nw_ecn" {
				set value [regsub {^nw_ecn=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create nw_ecn -under $of_match_handle -tos $value
			}
			"nw_proto" {
				set value [regsub {^nw_proto=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create nw_proto -under $of_match_handle -protocol $value
			}
			"nw_tos" {
				set value [regsub {^nw_tos=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create nw_tos -under $of_match_handle -tos $value
			}
			"pbb_isid" {
				 set value [regsub {^pbb_isid=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val id mask
					 ::sth::sthCore::invoke stc::create pbb_isid -under $of_match_handle -useMask 1 -id $id -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create pbb_isid -under $of_match_handle -id $value
				 }
			}
			"sctp_dst" {
				set value [regsub {^sctp_dst=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create sctp_dst -under $of_match_handle -port_number $value
			}
			"sctp_src" {
				set value [regsub {^sctp_src=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create sctp_src -under $of_match_handle -port_number $value
			}
			"tcp_dst" {
				set value [regsub {^tcp_dst=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create tcp_dst -under $of_match_handle -port_number $value
			}
			"tcp_src" {
				set value [regsub {^tcp_src=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create tcp_src -under $of_match_handle -port_number $value
			}
			"tp_dst" {
				set value [regsub {^tp_dst=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create tp_dst -under $of_match_handle -port_number $value
			}
			"tp_src" {
				set value [regsub {^tp_src=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create tp_src -under $of_match_handle -port_number $value
			}
			"tun_id" {
				 set value [regsub {^tun_id=} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*)/(.*)} $value val id mask
					 ::sth::sthCore::invoke stc::create tun_id -under $of_match_handle -useMask 1 -id $id -mask $mask
				 } else {
					 ::sth::sthCore::invoke stc::create tun_id -under $of_match_handle -id $value
				 }
			}
			"udp_dst" {
				set value [regsub {^udp_dst=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create udp_dst -under $of_match_handle -udp_dst $value
			}
			"udp_src" {
				set value [regsub {^udp_src=} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfMatch -under $match_hnd]
				::sth::sthCore::invoke stc::create udp_src -under $of_match_handle -port_number $value
			}
			default {
			 ::sth::sthCore::log error "Incorrect \"custom_match_field\" value: $value"
			}
          }
     }
}


proc ::sth::openflow::process_custom_flowblock_instruction {handle} {

	set flowHandle [::sth::sthCore::invoke stc::get $handle -children-openflow:Flow]
	if { $flowHandle == ""} {
	 set flowHandle [::sth::sthCore::invoke stc::create openflow:Flow -under $handle]
	}
	
	set instHandle [::sth::sthCore::invoke stc::get $flowHandle -children-Instructions]
	if { $instHandle == ""} {
		set instHandle [::sth::sthCore::invoke stc::create Instructions -under $flowHandle]
	}

	return $instHandle
}

proc ::sth::openflow::process_custom_flowblock_goto_table {handle gotoTableValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
	set gotoTableHnd [::sth::sthCore::invoke stc::create InstructionList.gotoTable -under $instHandle]
    
	#process user input
	set gotoValue [regsub {^-FrameConfig\s} $gotoTableValueList ""]
	set gotoValue [regsub {^\{} $gotoValue ""]
	set gotoValue [regsub {\}$} $gotoValue ""]
	set gotoValue [regsub {^goto_table=} $gotoValue ""]

	::sth::sthCore::invoke stc::config $gotoTableHnd -table $gotoValue
	
}

proc ::sth::openflow::process_custom_flowblock_metadata {handle metadataValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
	set metadataHnd [::sth::sthCore::invoke stc::create InstructionList.writeMetadata -under $instHandle]
    
	#process user input
	set metadataValue [regsub {^-FrameConfig\s} $metadataValueList ""]
	set metadataValue [regsub {^\{} $metadataValue ""]
	set metadataValue [regsub {\}$} $metadataValue ""]
	set metadataValue [regsub {^write_metadata=} $metadataValue ""]
    if {[regexp {:} $metadataValue]} {
        regexp {(.*):(.*)} $metadataValue val data mask
        ::sth::sthCore::invoke stc::config $metadataHnd -metadata $data -metadataMask $mask
    } else {
        ::sth::sthCore::log error "Incorrect \"custom_metadata_field\" - value: $metadataValue"
    }

}

proc ::sth::openflow::process_custom_flowblock_write_action {handle actionValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
    set writehnd [::sth::sthCore::invoke stc::create InstructionList.writeActions.writeActions -under $instHandle]
    
     #process user input
     set actionValue [regsub {^-FrameConfig\s} $actionValueList ""]
     set actionValue [regsub {^\{} $actionValue ""]
     set actionValue [regsub {\}$} $actionValue ""]
	 set parrayValue [split $actionValue ","]
     
     process_custom_flowblock_elements $writehnd $parrayValue
	
}

proc ::sth::openflow::process_custom_flowblock_clear_action {handle clearValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
	set gotoTableHnd [::sth::sthCore::invoke stc::create InstructionList.clearActions -under $instHandle]
}

proc ::sth::openflow::process_custom_flowblock_meter {handle meterValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
	set metersHnd [::sth::sthCore::invoke stc::create InstructionList.meters -under $instHandle]
    
	#process user input
	set meterValue [regsub {^-FrameConfig\s} $meterValueList ""]
	set meterValue [regsub {^\{} $meterValue ""]
	set meterValue [regsub {\}$} $meterValue ""]
	set meterValue [regsub {^meter=} $meterValue ""]

	::sth::sthCore::invoke stc::config $metersHnd -meter $meterValue
}

proc ::sth::openflow::process_custom_flowblock_exp {handle expValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
	set expHnd [::sth::sthCore::invoke stc::create InstructionList.experimenterInstructions -under $instHandle]
    
	#process user input
	set expValue [regsub {^-FrameConfig\s} $expValueList ""]
	set expValue [regsub {^\{} $expValue ""]
	set expValue [regsub {\}$} $expValue ""]
	set expValue [regsub {^exp_instruction=} $expValue ""]

    if {[regexp {:} $expValue]} {
        regexp {(.*):(.*)} $expValue val data id
        ::sth::sthCore::invoke stc::config $expHnd -exp_data $data -exp_id $id
    } else {
        ::sth::sthCore::log error "Incorrect \"custom_exp_field\" - value: $expValue"
    }
}

proc ::sth::openflow::process_custom_flowblock_action {handle actionValueList} {

	set instHandle [::sth::openflow::process_custom_flowblock_instruction $handle]
    set apply_hnd [::sth::sthCore::invoke stc::create InstructionList.applyActions.applyActions -under $instHandle]
    
     #process user input
     set actionValue [regsub {^-FrameConfig\s} $actionValueList ""]
     set actionValue [regsub {^\{} $actionValue ""]
     set actionValue [regsub {\}$} $actionValue ""]
	 set parrayValue [split $actionValue ","]
     
     process_custom_flowblock_elements $apply_hnd $parrayValue
}

proc ::sth::openflow::process_custom_flowblock_elements {apply_hnd parrayValue} {
    
    foreach value $parrayValue {
		switch -regexp -- $value {
			"output" {
				set value [regsub {^output:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create output -under $of_match_handle -port_number $value]
			}
			"controller" {
				set value [regsub {^controller:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create controller -under $of_match_handle -max_length $value]
			}
			"all" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				::sth::sthCore::invoke stc::create all -under $of_match_handle
			}
			"copy_ttl_in" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create copy_ttl_in -under $of_match_handle]
			}
			"copy_ttl_out" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create copy_ttl_out -under $of_match_handle]
			}
			"dec_mpls_ttl" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create dec_mpls_ttl -under $of_match_handle]
			}
			"dec_ttl" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create dec_ttl -under $of_match_handle]
			}
			"flood" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create flood -under $of_match_handle]
			}
			"local" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create local -under $of_match_handle]
			}
			"normal" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create normal -under $of_match_handle]
			}
			"pop_pbb" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create pop_pbb -under $of_match_handle]
			}
			"group" {
				set value [regsub {^group:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create group -under $of_match_handle -group_id $value]
			}
			"in_port" {
				set value [regsub {^in_port:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create in_port -under $of_match_handle]
			}
			"mod_sctp_dst" {
				set value [regsub {^mod_sctp_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_sctp_dst -under $of_match_handle -port_number $value]
			}
			"mod_sctp_src" {
				set value [regsub {^mod_sctp_src:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_sctp_src -under $of_match_handle -port_number $value]
			}
			"mod_tcp_dst" {
				set value [regsub {^mod_tcp_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_tcp_dst -under $of_match_handle -port_number $value]
			}
			"mod_tcp_src" {
				set value [regsub {^mod_tcp_src:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_tcp_src -under $of_match_handle -port_number $value]
			}
			"mod_udp_dst" {
				set value [regsub {^mod_udp_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_udp_dst -under $of_match_handle -port_number $value]
			}
			"mod_udp_src" {
				set value [regsub {^in_port:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_udp_dst -under $of_match_handle -port_number $value]
			}
			"mod_dl_dst" {
				set value [regsub {^mod_dl_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_dl_dst -under $of_match_handle -addr $value]
			}
			"mod_dl_src" {
				set value [regsub {^mod_dl_src:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_dl_src -under $of_match_handle -addr $value]
			}
			"mod_ipv6_dst" {
				set value [regsub {^mod_ipv6_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_ipv6_dst -under $of_match_handle -addr $value]
			}
			"mod_ipv6_src" {
				set value [regsub {^mod_ipv6_src:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_ipv6_src -under $of_match_handle -addr $value]
			}
			"mod_nw_dst" {
				set value [regsub {^mod_nw_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_nw_dst -under $of_match_handle -addr $value]
			}
			"mod_nw_src" {
				set value [regsub {^mod_nw_src:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_nw_src -under $of_match_handle -addr $value]
			}
			"pop_vlan" {
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create pop_vlan -under $of_match_handle]
			}
			"mod_icmpv6_code" {
				set value [regsub {^mod_icmpv6_code:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_icmpv6_code -under $of_match_handle -code $value]
			}
			"mod_icmpv6_type" {
				set value [regsub {^mod_icmpv6_type:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_icmpv6_type -under $of_match_handle -type $value]
			}
			"mod_ipv6_label" {
				set value [regsub {^mod_ipv6_label:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_ipv6_label -under $of_match_handle -label $value]
			}
			"mod_nd_sll" {
				set value [regsub {^mod_nd_sll:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_nd_sll -under $of_match_handle -source $value]
			}
			"mod_nd_tll" {
				set value [regsub {^mod_nd_tll:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_nd_tll -under $of_match_handle -source $value]
			}
			"mod_nd_target" {
				set value [regsub {^mod_nd_target:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_nd_target -under $of_match_handle -target $value]
			}
			"mod_nw_tos" {
				set value [regsub {^mod_nw_tos:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_nw_tos -under $of_match_handle -tos $value]
			}
			"mod_tun_id" {
				set value [regsub {^mod_tun_id:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_tun_id -under $of_match_handle -tunnel_id $value]
			}
			"mod_vlan_pcp" {
				set value [regsub {^mod_vlan_pcp:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_vlan_pcp -under $of_match_handle -pcp $value]
			}
			"mod_vlan_vid" {
				set value [regsub {^mod_vlan_vid:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_vlan_vid -under $of_match_handle -id $value]
			}
			"pop_mpls" {
				set value [regsub {^pop_mpls:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create pop_mpls -under $of_match_handle -ethernet_type $value]
			}
			"push_mpls" {
				set value [regsub {^push_mpls:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create push_mpls -under $of_match_handle -ethernet_type $value]
			}
			"push_pbb" {
				set value [regsub {^push_pbb:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create push_pbb -under $of_match_handle -ethernet_type $value]
			}
			"push_vlan" {
				set value [regsub {^push_vlan:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create push_vlan -under $of_match_handle -ethernet_type $value]
			}
			"set_mpls_bos" {
				set value [regsub {^set_mpls_bos:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create set_mpls_bos -under $of_match_handle -bos $value]
			}
			"set_mpls_label" {
				set value [regsub {^set_mpls_label:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create set_mpls_label -under $of_match_handle -label $value]
			}
			"set_mpls_tc" {
				set value [regsub {^set_mpls_tc:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create set_mpls_tc -under $of_match_handle -traffic_class $value]
			}
			"set_mpls_ttl" {
				set value [regsub {^set_mpls_ttl:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create set_mpls_ttl -under $of_match_handle -ttl $value]
			}
			"set_queue" {
				set value [regsub {^set_queue:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create set_queue -under $of_match_handle -queue $value]
			}
			"drop" {
				set value [regsub {^drop} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create drop -under $of_match_handle]
			}
			"enqueue" {
				 set value [regsub {^enqueue:} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*):(.*)} $value val port_num queueval
					 ::sth::sthCore::invoke stc::create enqueue -under $of_match_handle -port_number $port_num -queue $queueval 
				 } else {
					 ::sth::sthCore::log error "Incorrect \"custom_action_field\" - \"enqueue\" value: $value"
				 }
			}
			"exp_action" {
				 set value [regsub {^exp_action:} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				 if {[regexp {/} $value]} {
					 regexp {(.*):(.*)} $value val exp_data exp_id
					 ::sth::sthCore::invoke stc::create exp_action -under $of_match_handle -exp_data $exp_data -exp_id $exp_id 
				 } else {
					 ::sth::sthCore::log error "Incorrect \"custom_action_field\" - \"exp_action\" value: $value"
				 }
			}
			"goto_table" {
				set value [regsub {^goto_table:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create goto_table -under $of_match_handle -table $value]
			}
			"meter" {
				set value [regsub {^meter:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create meter -under $of_match_handle -meter $value]
			}
			"mod_tp_dst" {
				set value [regsub {^mod_tp_dst:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_tp_dst -under $of_match_handle -port_number $value]
			}
			"mod_tp_src" {
				set value [regsub {^mod_tp_src:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create mod_tp_src -under $of_match_handle -port_number $value]
			}
			"output" {
				set value [regsub {^output:} $value ""]
				set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				set hnd [::sth::sthCore::invoke stc::create output -under $of_match_handle -port_number $value]
			}
			"set_field_experimenter" {
				 set value [regsub {^set_field_experimenter:} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				 if {[regexp {:} $value]} {
					 regexp {(.*):(.*):(.*)} $value val exp_field exp_id exp_value
					 ::sth::sthCore::invoke stc::create set_field_experimenter -under $of_match_handle -experimenterField $exp_field -experimenterId $exp_id -experimenterValue $exp_value
				 } else {
					 ::sth::sthCore::log error "Incorrect \"custom_action_field\" - \"set_field_experimenter\" value: $value"
				 }
			}
			"set_field_experimenter_dec" {
				 set value [regsub {^set_field_experimenter_dec:} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				 if {[regexp {:} $value]} {
					 regexp {(.*):(.*):(.*)} $value val exp_field exp_id exp_value
					 ::sth::sthCore::invoke stc::create set_field_experimenter_dec -under $of_match_handle -experimenterField $exp_field -experimenterId $exp_id -expValueDecimal $exp_value
				 } else {
					 ::sth::sthCore::log error "Incorrect \"custom_action_field\" - \"set_field_experimenter_dec\" value: $value"
				 }
			}
			"set_field_experimenter_ip" {
				 set value [regsub {^set_field_experimenter_ip:} $value ""]
				 set of_match_handle [::sth::sthCore::invoke stc::create OfAction -under $apply_hnd]
				 if {[regexp {:} $value]} {
					 regexp {(.*):(.*):(.*)} $value val exp_field exp_id exp_value
					 ::sth::sthCore::invoke stc::create set_field_experimenter_ip -under $of_match_handle -experimenterField $exp_field -experimenterId $exp_id -ipAddr $exp_value
				 } else {
					 ::sth::sthCore::log error "Incorrect \"custom_action_field\" - \"set_field_experimenter_ip\" value: $value"
				 }
			}
			default {
				::sth::sthCore::log error "Incorrect \"custom_action_field\" value: $value"
			}
		}
     }
}


proc ::sth::openflow::group_action_bucket_config {group_entry_handle mode} {

	group_action_bucket_common $group_entry_handle $mode
}

proc ::sth::openflow::group_action_bucket_modify {group_entry_handle mode} {
	set action_bucket_handle [::sth::sthCore::invoke stc::get $group_entry_handle -children-OpenflowGroupActionBucketConfig]

    sth::sthCore::invoke stc::perform delete -ConfigList "$action_bucket_handle"
	group_action_bucket_common $group_entry_handle $mode
}

proc ::sth::openflow::group_action_bucket_common {group_entry_handle mode} {
	variable ::sth::openflow::switchHandleArray
	variable ::sth::openflow::keyedList
	
	set act $mode
	if {$mode eq "enable" || $mode eq "add"} {
		set act "config"
	}
	set optionValueList [getStcOptionValueList emulation_openflow_config group_action_bucket_$act $mode ""]
	
	regexp {\-num\s?(\d+)} $optionValueList match num
	if {![info exists num]} {
		return -code 1 -errorcode -1 "the number of watch_group should be more than 1."
	}
	
	set myvalueList [regsub -all {\-num\s?(\d+)} $optionValueList ""]
	set openflowParamList [processSplitList $num $myvalueList 0]
	array set openflowParamArray $openflowParamList

	set groupActionValueList [getStcOptionValueList emulation_openflow_config group_action_set_$act $mode ""]
	if {$groupActionValueList ne ""} {
		regexp {\-num\s?(\d+)} $groupActionValueList match num2
		if {![info exists num2]} {
			return -code 1 -errorcode -1 "the value of output_group_id should be set."
		}
		set mygroupActionValueList [regsub -all {\-num\s?(\d+)} $groupActionValueList ""]
		set mygroupActionValueList [processSplitList $num2 $mygroupActionValueList 0]
		array set groupActionParamArray $mygroupActionValueList
	}

	set action_bucket_handles ""
	for {set i 0} {$i<$num} {incr i} {
		set myOptionValues $openflowParamArray($i)
		if {[llength $myOptionValues]} {
			set myhandle $group_entry_handle
			if {[regexp {^openflowgroupentryconfig\d+$} $group_entry_handle]} {
				set myhandle [sth::sthCore::invoke stc::create OpenflowGroupActionBucketConfig -under $group_entry_handle]
			}
			sth::sthCore::invoke stc::config $myhandle $myOptionValues
			
			set action_bucket_handles [concat $action_bucket_handles $myhandle]
			
			if {[info exists groupActionParamArray]} {
                set handle [sth::sthCore::invoke stc::get $myhandle -children-OpenflowGroupActionSetConfig]
                sth::sthCore::invoke stc::config $handle $groupActionParamArray($i)
			}
		}
	}
	
	keylset ::sth::openflow::keyedList action_bucket_handles $action_bucket_handles
}


proc ::sth::openflow::meter_config {devhandle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]

	meter_common $openflow_handle $mode
}

proc ::sth::openflow::meter_modify {devhandle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]
	if {$openflow_handle eq ""} {
		set openflow_handle $devhandle
		set band_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowMeterBandConfig]
		foreach handle $band_handles {
			sth::sthCore::invoke stc::delete $handle
		}
	} else {
		set meter_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowMeterConfig]
		foreach handle $meter_handles {
			sth::sthCore::invoke stc::delete $handle
		}
	}
	meter_common $openflow_handle $mode
}

proc ::sth::openflow::meter_common {openflow_handle mode} {
	variable ::sth::openflow::switchHandleArray
	variable ::sth::openflow::keyedList
	
	set act $mode
	if {$mode eq "enable" || $mode eq "add"} {
		set act "config"
	}
	set optionValueList [getStcOptionValueList emulation_openflow_config meter_$act $mode ""]
	
	regexp {\-num\s?(\d+)} $optionValueList match num
	if {![info exists num]} {
		return -code 1 -errorcode -1 "the number of meter_id should be more than 1."
	}
	
	set myvalueList [regsub -all {\-num\s?(\d+)} $optionValueList ""]
	set openflowParamList [processSplitList $num $myvalueList 0]
	array set openflowParamArray $openflowParamList
		
	set bandValueList [getStcOptionValueList emulation_openflow_config meter_band_$act $mode ""]
	if {$bandValueList ne ""} {
		regexp {\-num\s?(\d+)} $bandValueList match num2
		if {![info exists num2]} {
			return -code 1 -errorcode -1 "the value of band_type should be set."
		}
		set mybandValueList [regsub -all {\-num\s?(\d+)} $bandValueList ""]
		set mybandValueList [processSplitList $num2 $mybandValueList 0]
		array set bandParamArray $mybandValueList
	}
	
	set meter_handles ""
	for {set i 0} {$i<$num} {incr i} {
		set myOptionValues $openflowParamArray($i)
		if {[llength $myOptionValues]} {
			if {[regexp {\-AffiliatedOpenflowSwitch-targets\sdpid(\d+)} $myOptionValues match index]} {
				set myOptionValues [regsub {dpid\d+} $myOptionValues $::sth::openflow::switchHandleArray($index)]
			}
			set myhandle $openflow_handle
			if {[regexp {^openflowcontrollerprotocolconfig\d+$} $openflow_handle]} {
				set myhandle [sth::sthCore::invoke stc::create OpenflowMeterConfig -under $openflow_handle]
			}
			sth::sthCore::invoke stc::config $myhandle $myOptionValues
			
			set meter_handles [concat $meter_handles $myhandle]
			
			if {[info exists bandParamArray]} {
				for {set j 0} {$j<$num2} {incr j} {
					set handle [sth::sthCore::invoke stc::create OpenflowMeterBandConfig -under $myhandle]
					sth::sthCore::invoke stc::config $handle $bandParamArray($j)
				}
			}
		}
	}
	
	keylset ::sth::openflow::keyedList meter_handles $meter_handles
}

proc ::sth::openflow::flowblock_config {devhandle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]

	flowblock_common $openflow_handle $mode
}

proc ::sth::openflow::flowblock_modify {devhandle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]
	if {$openflow_handle eq ""} {
		set openflow_handle $devhandle
	} else {
		set flowblock_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowFlowBlock]
		foreach handle $flowblock_handles {
			sth::sthCore::invoke stc::delete $handle
		}
	}
	flowblock_common $openflow_handle $mode
}

proc ::sth::openflow::flowblock_common {openflow_handle mode} {
	variable ::sth::openflow::switchHandleArray
	variable ::sth::openflow::keyedList
	
	set act $mode
	if {$mode eq "enable" || $mode eq "add"} {
		set act "config"
	}
	set optionValueList [getStcOptionValueList emulation_openflow_config flowblock_$act $mode ""]
	regexp {\-num\s?(\d+)} $optionValueList match num
	if {![info exists num]} {
		return -code 1 -errorcode -1 "the number of flow_cmd_type should be more than 1."
	} 
		
	set myvalueList [regsub -all {\-num\s?(\d+)} $optionValueList ""]
	set openflowParamList [processSplitList $num $myvalueList 0]
	array set openflowParamArray $openflowParamList
	
	set transportValueList [getStcOptionValueList emulation_openflow_config switch_transport_$act $mode ""]
	if {$transportValueList ne ""} {
		regexp {\-num\s?(\d+)} $transportValueList match num2
		
		if {![info exists num2]} {
			return -code 1 -errorcode -1 "the value of transport_type should be set."
		} elseif {$num ne $num2} {
			return -code 1 -errorcode -1 "the number of transport_type should be equal to the number of flow_cmd_type"
		} 
		
		set myTransvalueList [regsub -all {\-num\s?(\d+)} $transportValueList ""]
		set myTransvalueList [processSplitList $num2 $myTransvalueList 0]
		array set transParamArray $myTransvalueList
	}
	
	set trafficValueList [getStcOptionValueList emulation_openflow_config bound_traffic_$act $mode ""]
	if {$trafficValueList ne ""} {
		regexp {\-num\s?(\d+)} $trafficValueList match num3
	
		if {![info exists num3]} {
			return -code 1 -errorcode -1 "the value of action_type should be set."
		} elseif {$num ne $num3} {
			return -code 1 -errorcode -1 "the number of action_type should be equal to the number of flow_cmd_type"
		}
		set myTrafficValueList [regsub -all {\-num\s?(\d+)} $trafficValueList ""]
		set myTrafficValueList [processSplitList $num3 $myTrafficValueList 0]
		array set trafficParamArray $myTrafficValueList
	}

	set customMatchList [getStcOptionValueList emulation_openflow_config custom_flowblock_match_$act $mode ""]
	if {$customMatchList ne ""} {
		regexp {\-num\s?(\d+)} $customMatchList match num4
	
		if {![info exists num4]} {
			return -code 1 -errorcode -1 "the value of custom_match_field should be set."
		} elseif {$num ne $num4} {
			return -code 1 -errorcode -1 "the number of custom_match_field should be equal to the number of flow_cmd_type"
		}
		set myCustomMatchList [regsub -all {\-num\s?(\d+)} $customMatchList ""]
		set myCustomMatchList [processSplitList $num4 $myCustomMatchList 0]
		array set customMatchParamArray $myCustomMatchList
	}

	set customActionList [getStcOptionValueList emulation_openflow_config custom_flowblock_action_$act $mode ""]
	if {$customActionList ne ""} {
		regexp {\-num\s?(\d+)} $customActionList match num5
	
		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_action_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_action_field should be equal to the number of flow_cmd_type"
		}
		set myCustomActionList [regsub -all {\-num\s?(\d+)} $customActionList ""]
		set myCustomActionList [processSplitList $num5 $myCustomActionList 0]
		array set customActionParamArray $myCustomActionList
	}

	set customGotoTableList [getStcOptionValueList emulation_openflow_config custom_flowblock_goto_table_$act $mode ""]
	if {$customGotoTableList ne ""} {
		regexp {\-num\s?(\d+)} $customGotoTableList match num5

		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_goto_table_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_goto_table_field should be equal to the number of flow_cmd_type"
		}
		set myCustomGotoTableList [regsub -all {\-num\s?(\d+)} $customGotoTableList ""]
		set myCustomGotoTableList [processSplitList $num5 $myCustomGotoTableList 0]
		array set customGotoTableParamArray $myCustomGotoTableList
	}

	set customMetatdataList [getStcOptionValueList emulation_openflow_config custom_flowblock_metadata_$act $mode ""]
	if {$customMetatdataList ne ""} {
		regexp {\-num\s?(\d+)} $customMetatdataList match num5

		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_metadata_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_metadata_field should be equal to the number of flow_cmd_type"
		}
		set myCustomMetadataList [regsub -all {\-num\s?(\d+)} $customMetatdataList ""]
		set myCustomMetadataList [processSplitList $num5 $myCustomMetadataList 0]
		array set customMetadataParamArray $myCustomMetadataList
	}

	set customWriteActionList [getStcOptionValueList emulation_openflow_config custom_flowblock_write_action_$act $mode ""]
	if {$customWriteActionList ne ""} {
		regexp {\-num\s?(\d+)} $customWriteActionList match num5

		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_write_action_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_write_action_field should be equal to the number of flow_cmd_type"
		}
		set myCustomWriteActionList [regsub -all {\-num\s?(\d+)} $customWriteActionList ""]
		set myCustomWriteActionList [processSplitList $num5 $myCustomWriteActionList 0]
		array set customWriteActionParamArray $myCustomWriteActionList
	}

	set customClearActionList [getStcOptionValueList emulation_openflow_config custom_flowblock_clear_action_$act $mode ""]
	if {$customClearActionList ne ""} {
		regexp {\-num\s?(\d+)} $customClearActionList match num5

		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_clear_action_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_clear_action_field should be equal to the number of flow_cmd_type"
		}
		set myCustomClearActionList [regsub -all {\-num\s?(\d+)} $customClearActionList ""]
		set myCustomClearActionList [processSplitList $num5 $myCustomClearActionList 0]
		array set customClearActionParamArray $myCustomClearActionList
	}	

	set customMeterList [getStcOptionValueList emulation_openflow_config custom_flowblock_meter_$act $mode ""]
	if {$customMeterList ne ""} {
		regexp {\-num\s?(\d+)} $customMeterList match num5

		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_clear_action_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_clear_action_field should be equal to the number of flow_cmd_type"
		}
		set myCustomMeterList [regsub -all {\-num\s?(\d+)} $customMeterList ""]
		set myCustomMeterList [processSplitList $num5 $myCustomMeterList 0]
		array set customMeterParamArray $myCustomMeterList
	}	

	set customExpList [getStcOptionValueList emulation_openflow_config custom_flowblock_exp_$act $mode ""]
	if {$customExpList ne ""} {
		regexp {\-num\s?(\d+)} $customExpList match num5

		if {![info exists num5]} {
			return -code 1 -errorcode -1 "the value of custom_exp_field should be set."
		} elseif {$num ne $num5} {
			return -code 1 -errorcode -1 "the number of custom_exp_field should be equal to the number of flow_cmd_type"
		}
		set myExpList [regsub -all {\-num\s?(\d+)} $customExpList ""]
		set myExpList [processSplitList $num5 $myExpList 0]
		array set customExpParamArray $myExpList
	}

	set flow_handles ""
	for {set i 0} {$i<$num} {incr i} {
		set myOptionValues $openflowParamArray($i)
		if {[llength $myOptionValues]} {
			if {[regexp {\-AffiliatedOpenflowSwitch-targets\sdpid(\d+)} $myOptionValues match index]} {
				set myOptionValues [regsub {dpid\d+} $myOptionValues $::sth::openflow::switchHandleArray($index)]
			}
			
			set myhandle $openflow_handle
			if {[regexp {^openflowcontrollerprotocolconfig\d+$} $openflow_handle]} {
				set myhandle [sth::sthCore::invoke stc::create OpenflowFlowBlock -under $openflow_handle]
			}
			sth::sthCore::invoke stc::config $myhandle $myOptionValues
			set flow_handles [concat $flow_handles $myhandle]
			
			if {[info exists transParamArray] && $transParamArray($i) ne "-"} {
				set handle1 [sth::sthCore::invoke stc::get $myhandle -children-OpenflowSwitchTransportConfig]
				sth::sthCore::invoke stc::config $handle1 $transParamArray($i)
			}
			
			if {[info exists trafficParamArray] && $trafficParamArray($i) ne "-"} {
				set handle2 [sth::sthCore::invoke stc::get $myhandle -children-OpenflowFlowBoundTrafficAction]
				if {$handle2 eq ""} {
					sth::sthCore::invoke stc::create OpenflowFlowBoundTrafficAction -under $myhandle $trafficParamArray($i)
				} else {
					sth::sthCore::invoke stc::config $handle2 $trafficParamArray($i)
				}
			}
            
			if {[info exists customMatchParamArray] && $customMatchParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_match $myhandle $customMatchParamArray($i)
			}
            
			if {[info exists customActionParamArray] && $customActionParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_action $myhandle $customActionParamArray($i)
			}

			if {[info exists customGotoTableParamArray] && $customGotoTableParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_goto_table $myhandle $customGotoTableParamArray($i)
			}
			
			if {[info exists customMetadataParamArray] && $customMetadataParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_metadata $myhandle $customMetadataParamArray($i)
			}
			
			if {[info exists customWriteActionParamArray] && $customWriteActionParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_write_action $myhandle $customWriteActionParamArray($i)
			}

			if {[info exists customClearActionParamArray] && $customClearActionParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_clear_action $myhandle $customClearActionParamArray($i)
			}
			
			if {[info exists customMeterParamArray] && $customMeterParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_meter $myhandle $customMeterParamArray($i)
			}

			if {[info exists customExpParamArray] && $customExpParamArray($i) ne "-"} {
                ::sth::openflow::process_custom_flowblock_exp $myhandle $customExpParamArray($i)
			}
            #This is workaround provided by STC Eng team
			if {([info exists customActionParamArray] && $customActionParamArray($i) ne "-") ||
				([info exists customMatchParamArray] && $customMatchParamArray($i) ne "-") ||
				([info exists customGotoTableParamArray] && $customGotoTableParamArray($i) ne "-") ||
				([info exists customMetatdataParamArray] && $customMetatdataParamArray($i) ne "-") ||
				([info exists customWriteActionParamArray] && $customWriteActionParamArray($i) ne "-") ||
				([info exists customClearActionParamArray] && $customClearActionParamArray($i) ne "-") ||
				([info exists customMeterParamArray] && $customMeterParamArray($i) ne "-") ||
				([info exists customExpParamArray] && $customExpParamArray($i) ne "-")} {
				set frameConfig [sth::sthCore::invoke stc::get $myhandle -FrameConfig]
				sth::sthCore::invoke stc::config $myhandle -FrameConfig $frameConfig
			}
		}
	}
	
	keylset ::sth::openflow::keyedList flow_handles $flow_handles
}

proc ::sth::openflow::processSplitList {num paramList element} {
    array set retParam {};
    
    for {set i 0} {$i<$num} {incr i} {
        set elemList ""
        switch -- $element {
            0 {
                foreach {attr val} $paramList {
                    #if the customer doesn't input the same number of element as the number, we will provide the default value
                    if {$i < [llength $val]} {
						set item [lindex $val $i]
						if {$item ne "-"} {
							lappend elemList $attr $item
						}
                    }
                }
            }
            1 {
                foreach {elem attr val} $paramList {
                    #if the customer doesn't input the same number of element as the number, we will provide the default value
                    if {$i < [llength $val]} {
                        lappend elemList $elem $attr [lindex $val $i]
                    }
                }
            }
        }
       
		if {$elemList ne "" } {
			set retParam($i) $elemList
		} else {
			set retParam($i) "-"
		}
    }
    
    set retList ""
    set retList [array get retParam]
    return  $retList
}

proc ::sth::openflow::controller_config {devhandle mode} {
	variable ::sth::openflow::keyedList
	
	set openflow_handle [::sth::sthCore::invoke stc::create OpenflowControllerProtocolConfig -under $devhandle]
    set optionValueList [getStcOptionValueList emulation_openflow_config controller_config $mode $openflow_handle]
	
	if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $openflow_handle $optionValueList
    }
	
	keylset ::sth::openflow::keyedList handle $openflow_handle
}

proc ::sth::openflow::controller_modify {devhandle mode} {
	variable ::sth::openflow::keyedList
	
	set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]
    set optionValueList [getStcOptionValueList emulation_openflow_config controller_modify $mode $openflow_handle]
	
	if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $openflow_handle $optionValueList
    }
	
	keylset ::sth::openflow::keyedList handle $openflow_handle
}

proc ::sth::openflow::async_msg_config {devhandle mode} {
	variable ::sth::openflow::keyedList

    set openflow_handle [::sth::sthCore::invoke stc::get $devhandle -children-OpenflowControllerProtocolConfig]
	set async_msg_handle [::sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowSetAsyncMessageConfig]
    set optionValueList [getStcOptionValueList emulation_openflow_config async_msg_config $mode $async_msg_handle]

	if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $async_msg_handle $optionValueList
    }
}

proc ::sth::openflow::switch_config {dev_handle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $dev_handle -children-OpenflowControllerProtocolConfig]
    
	switch_config_common $openflow_handle $mode
}

proc ::sth::openflow::switch_modify {dev_handle mode} {
	set openflow_handle [::sth::sthCore::invoke stc::get $dev_handle -children-OpenflowControllerProtocolConfig]
	set switch_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowSwitchConfig]
	foreach handle $switch_handles {
		sth::sthCore::invoke stc::delete $handle
	}
	
	switch_config_common $openflow_handle $mode
}

proc ::sth::openflow::switch_config_common {openflow_handle mode} {
	variable ::sth::openflow::userArgsArray
	variable ::sth::openflow::switchHandleArray

	set optionValueList ""
	if {$mode eq "enable"} {
		set optionValueList [getStcOptionValueList emulation_openflow_config switch_config $mode ""]
	} else {
		set optionValueList [getStcOptionValueList emulation_openflow_config switch_modify $mode ""]
	}
	regexp {\-num\s?(\d+)} $optionValueList match num
	set myvalueList [regsub -all {\-num\s?(\d+)} $optionValueList ""]
	set openflowParamList [processSplitList $num $myvalueList 0]
	array set openflowParamArray $openflowParamList
	array unset ::sth::openflow::switchHandleArray
	array set ::sth::openflow::switchHandleArray {}
	
	set j 0
	array set flow_handle_change ""
	set flowblock_handles [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowFlowBlock]
	foreach flow_handle $flowblock_handles {
		set type [sth::sthCore::invoke stc::get $flow_handle -FlowBlockType]
		set dpid [sth::sthCore::invoke stc::get $flow_handle -AffiliatedOpenflowSwitch-targets]
		if {$dpid eq ""} {
			set flow_handle_change($j) $flow_handle
			incr j
		}
	}
	for {set i 0} {$i<$num} {incr i} {
		set ::sth::openflow::switchHandleArray($i) [sth::sthCore::invoke stc::create OpenflowSwitchConfig -under $openflow_handle $openflowParamArray($i)]
		if {$i < $j} {
			sth::sthCore::invoke stc::config $flow_handle_change($i) -AffiliatedOpenflowSwitch-targets $::sth::openflow::switchHandleArray($i)
		}
	}
	for {set k 0} {$k<[expr $j - $i]} {incr k} {
		sth::sthCore::invoke stc::config $flow_handle_change($k) -AffiliatedOpenflowSwitch-targets $::sth::openflow::switchHandleArray([expr $i - 1])
	}
	
	foreach myswitches $::sth::openflow::userArgsArray(switch_link_list) {
		set itemList [split $myswitches "-"]
		set index ""
		set item ""
		array set switchPortNumArray {}
		foreach myitem $itemList {
			if {[regexp {dpid(\d+)\/(\d+)} $myitem match sub sub1]} {
				if {$index eq ""} {
					set index $sub
					set switchPortNumArray($index) 1
					if {[info exists sub1]} {
						set switchPortNumArray($index) $sub1
					}
				} else {
					set item $sub
					set switchPortNumArray($item) 1
					if {[info exists sub1]} {
						set switchPortNumArray($item) $sub1
					}
				}
			} else {
				set item [regsub {\/.\+} $myitem ""]
			}
		}
		
		if {[regexp {^port} $item]} {
			sth::sthCore::invoke stc::create OpenflowSwitchPortConfig -under $switchHandleArray($index) -portnum $switchPortNumArray($index) -openflowswitchlinkedport-Targets $item
		} else {
			array set switchPortHandleArray {}
			set switchPortHandleArray($index) [sth::sthCore::invoke stc::create OpenflowSwitchPortConfig -under $::sth::openflow::switchHandleArray($index)]
			set switchPortHandleArray($item) [sth::sthCore::invoke stc::create OpenflowSwitchPortConfig -under $::sth::openflow::switchHandleArray($item)]
									  
			sth::sthCore::invoke stc::config $switchPortHandleArray($index) -portnum $switchPortNumArray($index) -openflowswitchlinkedport-Targets $switchPortHandleArray($item)
			sth::sthCore::invoke stc::config $switchPortHandleArray($item) -portnum $switchPortNumArray($item) -openflowswitchlinkedport-Targets $switchPortHandleArray($index)
		}
	}

    set switch_handles ""
    foreach {index switchHnd} [array get ::sth::openflow::switchHandleArray] {
        lappend switch_handles $switchHnd
    }
    keylset ::sth::openflow::keyedList switch_handles $switch_handles
}

proc ::sth::openflow::calc_num {handle opt value} {
	set len [llength $value]
	set stcAttr [::sth::sthCore::getswitchprop ::sth::openflow:: emulation_openflow_config $opt stcattr]
	return "-$stcAttr \"$value\" -num $len"
}

proc ::sth::openflow::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::openflow::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::openflow:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::openflow:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::openflow:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                #::sth::openflow::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::openflow::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::openflow:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::openflow:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::openflow:: $cmdType $opt $::sth::openflow::userArgsArray($opt)} value]} {
						lappend optionValueList -$stcAttr $value
					} else {
						lappend optionValueList -$stcAttr $::sth::openflow::userArgsArray($opt)
					}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::openflow::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}


proc ::sth::openflow::emulation_openflow_control_start_controller {returnKeyedList} {
	set protocol_list [emulation_openflow_control_common]
	::sth::sthCore::invoke stc::perform ProtocolStartCommand -protocolList $protocol_list
}

proc ::sth::openflow::emulation_openflow_control_stop_controller {returnKeyedList} {
	set protocol_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform ProtocolStopCommand -protocolList $protocol_list
}

proc ::sth::openflow::emulation_openflow_control_start_discovery {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::doStcApply
		
	::sth::sthCore::invoke stc::perform OpenflowStartDiscoveryCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_update_switch {returnKeyedList} {
	upvar $returnKeyedList myreturnKeyedList
	set handle_list [emulation_openflow_control_common]

	foreach openflow_handle $handle_list {
		set i 0
		set ret ""
		set oldret ""
		set switch_handles ""
		while {$ret eq ""} {
			::sth::sthCore::invoke stc::sleep [expr 30+$i]
			set pp [::sth::sthCore::invoke stc::perform OpenflowDiscoveryUpdateSwitchConfigCommand -HandleList $openflow_handle]
			set ret [sth::sthCore::invoke stc::get $openflow_handle -children-OpenflowSwitchConfig]
			if {$ret ne ""} {
				if {$ret eq $oldret} {
					set switch_handles [concat $switch_handles $ret]
				} else {
					set oldret $ret
					set ret ""
					incr i 10
				}
			}
		}
        ::sth::sthCore::invoke stc::perform OpenflowAddConnectedSwitchesToConfigCommand -HandleList $openflow_handle
		if {$switch_handles ne ""} {
			keylset myreturnKeyedList $openflow_handle.switch_handles $switch_handles
		}
	}
}

proc ::sth::openflow::emulation_openflow_control_stop_discovery {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowStopDiscoveryCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_add_flows {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowAddFlowsToSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_remove_flows {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowRemoveFlowsFromSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_add_meters {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowAddMeterModsToSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_remove_meters {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowRemoveMeterModsFromSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_add_group_entries {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowAddGroupEntriesToSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_verify_discovery {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowDiscoveryVerifySwitchConfigCommand  -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_modify_flows {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowModifyFlowsOnSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_modify_group_entries {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowModifyGroupEntriesOnSwitchCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_modify_meters {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowModifyMeterModsOnSwitchCommand  -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_remove_group_entries {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowRemoveGroupEntriesFromSwitchCommand  -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_send_barrier_req {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	
	::sth::sthCore::invoke stc::perform OpenflowBarrierRequestCommand  -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_send_controller_req {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle_list $::sth::openflow::userArgsArray(handle)

    set configList "stc::perform OpenflowRoleRequestCommand -HandleList \{$handle_list\} "
    append configList [getStcOptionValueList emulation_openflow_control control_req enable ""]

	::sth::sthCore::invoke $configList
}

proc ::sth::openflow::emulation_openflow_control_send_feature_req {returnKeyedList} {
	set handle_list [emulation_openflow_control_common]
	#Handle list - List of switches to send the features request to
	::sth::sthCore::invoke stc::perform OpenflowFeaturesRequestCommand  -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_send_get_async_req {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle_list $::sth::openflow::userArgsArray(switch_handles)
	#HandleList- List of switches to send the GET command to
	::sth::sthCore::invoke stc::perform OpenflowGetAsyncRequestCommand -HandleList $handle_list
}

proc ::sth::openflow::emulation_openflow_control_send_set_async_req {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle_list $::sth::openflow::userArgsArray(switch_handles)
    
	#HandleList: List of switches to send the SET command to.
    set configList "stc::perform OpenflowSetAsyncMessageCommand -HandleList \{$handle_list\} "
    append configList [getStcOptionValueList emulation_openflow_control async_set_req enable ""]

	::sth::sthCore::invoke $configList
}

proc ::sth::openflow::emulation_openflow_control_view_meter_features {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set filePath ""
    
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePath $::sth::openflow::userArgsArray(file_path)
    }
    
    ::sth::sthCore::invoke stc::perform OpenflowViewMeterFeaturesCommand -Controller $handle -SwitchList $switch_handle_list -ExportStatistics true -ExportPath $filePath
}

proc ::sth::openflow::emulation_openflow_control_view_table_stats {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set filePath ""
    
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePath $::sth::openflow::userArgsArray(file_path)
    }
    
    ::sth::sthCore::invoke stc::perform OpenflowViewTableStatisticsCommand -Controller $handle -SwitchList $switch_handle_list -ExportStatistics true -ExportPath $filePath
}

proc ::sth::openflow::emulation_openflow_control_view_table_features {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set filePath ""
    
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePath $::sth::openflow::userArgsArray(file_path)
    }
    
    ::sth::sthCore::invoke stc::perform OpenflowViewTableFeaturesCommand -Controller $handle -SwitchList $switch_handle_list -ExportStatistics true -ExportPath $filePath
}

proc ::sth::openflow::emulation_openflow_control_view_port_stats {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set filePath ""
    
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePath $::sth::openflow::userArgsArray(file_path)
    }
    
    ::sth::sthCore::invoke stc::perform OpenflowViewPortStatisticsCommand -Controller $handle -SwitchList $switch_handle_list -ExportStatistics true -ExportPath $filePath -AllPorts true
}

proc ::sth::openflow::emulation_openflow_control_view_port_description {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set filePath ""
    
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePath $::sth::openflow::userArgsArray(file_path)
    }
    
    ::sth::sthCore::invoke stc::perform OpenflowViewPortDescriptionCommand -Controller $handle -SwitchList $switch_handle_list -ExportStatistics true -ExportPath $filePath
}

proc ::sth::openflow::emulation_openflow_control_view_switch_description {returnKeyedList} {
	variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set filePath ""
    
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePath $::sth::openflow::userArgsArray(file_path)
    }
    
    ::sth::sthCore::invoke stc::perform OpenflowViewSwitchDescriptionCommand -Controller $handle -SwitchList $switch_handle_list -ExportStatistics true -ExportPath $filePath
}


proc ::sth::openflow::emulation_openflow_control_manage_tls_files {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
	variable ::sth::openflow::userArgsArray
    set port_handle_list $::sth::openflow::userArgsArray(port_handle)

    if {[info exists ::sth::openflow::userArgsArray(tls_file_action)]} {
        set tls_action $::sth::openflow::userArgsArray(tls_file_action)
    } else {
        ::sth::sthCore::processError myreturnKeyedList "Option tls_file_action mandatroy for action- manage_tls_files" {}
        return -code error $myreturnKeyedList 
    }

    switch -- $tls_action {
        upload {
            set cmd "spirent.core.TlsKeyCertificateUploadCommand"
        }
        delete {
            set caFileList ""
            set certFileList ""
            set priKeyFileList ""
            set cmd "spirent.core.TlsKeyCertificateDeleteCommand"
            #If "tls_file_name_list"  is not specified, get it from port handle
            if {![info exists ::sth::openflow::userArgsArray(tls_file_name_list)]} {
                foreach port $port_handle_list {
                    array set fileHndRet [::sth::sthCore::invoke "stc::perform spirent.core.TlsKeyCertificateEnumerateCommand -Port $port"]
                    if {$fileHndRet(-CaCertificateFiles) != ""} {
                        append caFileList " $fileHndRet(-CaCertificateFiles)"
                    }
                    if {$fileHndRet(-CertificateFiles) != ""} {
                        append certFileList " $fileHndRet(-CertificateFiles)"
                    }
                    if {$fileHndRet(-PrivateKeyFiles) != ""} {
                        append priKeyFileList " $fileHndRet(-PrivateKeyFiles)"
                    }
                }
                set tls_file_type $::sth::openflow::userArgsArray(tls_file_type)
                switch -- $tls_file_type {
                   private_key {
                        if { $priKeyFileList == "" } {
                            ::sth::sthCore::log warn "Private Key File not present in the port"
                            #::sth::sthCore::processError myreturnKeyedList "Private Key File not present in the port" {}
                            #return -code error $myreturnKeyedList 
                        } else {
                            set ::sth::openflow::userArgsArray(tls_file_name_list) "\{ $priKeyFileList \}"
                        }
                   }
                   certificate {
                        if { $certFileList == "" } {
                            ::sth::sthCore::log warn "Certificate File not present in the port"
                            #::sth::sthCore::processError myreturnKeyedList "Certificate File not present in the port" {}
                            #return -code error $myreturnKeyedList 
                        } else {
                            set ::sth::openflow::userArgsArray(tls_file_name_list) "\{ $certFileList \}"
                        }
                   }
                   ca_certificate {
                        if { $caFileList == "" } {
                            ::sth::sthCore::log warn "CA Certificate File not present in the port"
                            #::sth::sthCore::processError myreturnKeyedList "CA Certificate File not present in the port" {}
                            #return -code error $myreturnKeyedList 
                        } else {
                            set ::sth::openflow::userArgsArray(tls_file_name_list) "\{ $caFileList \}"
                        }
                   }
                }
            }
        }
    }

	#HandleList: List of switches to send the SET command to.
    set configList "stc::perform $cmd -PortList \{$port_handle_list\} "
    append configList [getStcOptionValueList emulation_openflow_control manage_tls_files enable ""]

	::sth::sthCore::invoke $configList
}


proc ::sth::openflow::emulation_openflow_control_common {} {
    variable ::sth::openflow::userArgsArray
		
	set handle_list ""
	if {[info exists ::sth::openflow::userArgsArray(handle)]} {
		foreach hostList $::sth::openflow::userArgsArray(handle) {
			set openflow [::sth::sthCore::invoke stc::get $hostList -children-OpenflowControllerProtocolConfig]
			lappend handle_list $openflow
		}
	} else {
		set port_list $::sth::openflow::userArgsArray(port_handle)
		foreach port $port_list {
			set devices [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
			foreach device $devices {
				set openflow [::sth::sthCore::invoke stc::get $device -children-OpenflowControllerProtocolConfig]
				if {![regexp "^$" $openflow]} {
					set handle_list [concat $handle_list $openflow]
				}
			}
		}
	}

	return $handle_list
}

proc ::sth::openflow::emulation_openflow_stats_func {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
	
    set device_list ""
	if {[info exists ::sth::openflow::userArgsArray(handle)]} {
		set device_list $::sth::openflow::userArgsArray(handle)
	} else {
		set port_list $::sth::openflow::userArgsArray(port_handle)
		foreach port $port_list {
			set devices [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
			foreach device $devices {
				set openflow [::sth::sthCore::invoke stc::get $device -children-OpenflowControllerProtocolConfig]
				if {![regexp "^$" $openflow]} {
					set device_list [concat $device_list $device]
				}
			}
		}
	}
	
	set num 1
	set mymode $::sth::openflow::userArgsArray(mode)
	if {[regexp -nocase "all" $mymode]} {
		set mymode "controller switch_result switchport_result async_result reactive_mode_result"
	}
	
	if {[regexp -nocase "controller" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
						 -ConfigType OpenflowControllerProtocolConfig -resulttype OpenflowControllerResults]
		incr num
	}
	if {[regexp -nocase "switch_result" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
						 -ConfigType OpenflowControllerProtocolConfig -resulttype OpenflowControllerSwitchResults]
		incr num
	}
	
	if {[regexp -nocase "switchport_result" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType OpenflowControllerProtocolConfig -resulttype OpenflowControllerSwitchPortResults]
		incr num
	}

	if {[regexp -nocase "async_result" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType OpenflowControllerProtocolConfig -resulttype OpenflowAsyncConfigResults]
		incr num
	}
    
	if {[regexp -nocase "reactive_mode_result" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType OpenflowControllerProtocolConfig -resulttype OpenflowReactiveModeAggregateResults]
		incr num
	}
    
	::sth::sthCore::invoke stc::sleep 3
	
	foreach device $device_list {
		set openflow [::sth::sthCore::invoke stc::get $device -children-OpenflowControllerProtocolConfig]
		
		if {[regexp -nocase "controller" $mymode]} {
			set control_result [::sth::sthCore::invoke stc::get $openflow -children-OpenflowControllerResults]

			if {$control_result ne ""} {
				set myresult [::sth::sthCore::invoke stc::get $control_result]
				set retVal {}
				foreach {attr val} $myresult {
					keylset retVal $attr $val
				}
				keylset myreturnKeyedList $device.controller_result $retVal
			}
		}
		
		if {[regexp -nocase "switch_result" $mymode]} {
			set switch_results [::sth::sthCore::invoke stc::get $openflow -children-OpenflowControllerSwitchResults]
			foreach result $switch_results {
				set myresult [::sth::sthCore::invoke stc::get $result]
				set switchname [::sth::sthCore::invoke stc::get $result -SwitchName]
				
				if {$switchname ne ""} {
					set myswitch [::sth::sthCore::invoke stc::perform GetObjects -RootList $openflow -ClassName OpenflowSwitchConfig -condition "name = $switchname"]
					regexp {\-ObjectList\s(.*?)\s\-} $myswitch mymatch myswitch 
					set retVal {}
					foreach {attr val} $myresult {
						keylset retVal $attr $val
					}
					keylset myreturnKeyedList $device.switch_result.$myswitch $retVal
				}
			}
		}
		
		if {[regexp -nocase "switchport_result" $mymode]} {
			set switch_port_results [::sth::sthCore::invoke stc::get $openflow -children-OpenflowControllerSwitchPortResults]

			array set myData {}
			foreach result $switch_port_results {
				set myresult [::sth::sthCore::invoke stc::get $result]
				set retVal {}

				foreach {attr val} $myresult {
					keylset retVal $attr $val
				}
				
				set myport [keylget retVal "-DiscoveredPort"]
				set myData($myport) $retVal
			}
			
			set index 1
			foreach portkey [lsort -dictionary [array names myData]] {
				keylset myreturnKeyedList $device.switchport_result$index $myData($portkey)
				incr index
			}
		}

		if {[regexp -nocase "async_result" $mymode]} {
			set async_result [::sth::sthCore::invoke stc::get $openflow -children-OpenflowAsyncConfigResults]
			foreach result $async_result {
				set myresult [::sth::sthCore::invoke stc::get $result]
				set dpid [::sth::sthCore::invoke stc::get $result -Dpid]
				
				if {$dpid ne ""} {
					set myswitch [::sth::sthCore::invoke stc::perform GetObjects -RootList $openflow -ClassName OpenflowSwitchConfig -condition "Dpid = $dpid"]
					regexp {\-ObjectList\s(.*?)\s\-} $myswitch mymatch myswitch 
					set retVal {}
					foreach {attr val} $myresult {
						keylset retVal $attr $val
					}
					keylset myreturnKeyedList $device.async_result.$myswitch $retVal
				}
			}
		}

		if {[regexp -nocase "reactive_mode_result" $mymode]} {
			set reactive_mode_result [::sth::sthCore::invoke stc::get $openflow -children-OpenflowReactiveModeAggregateResults ]

			if {$reactive_mode_result ne ""} {
				set myresult [::sth::sthCore::invoke stc::get $reactive_mode_result]
				set retVal {}
				foreach {attr val} $myresult {
					keylset retVal $attr $val
				}
				keylset myreturnKeyedList $device.reactive_mode_result $retVal
			}
		}
	}
	
	for {set i 1} {$i < $num} {incr i} {
		::sth::sthCore::invoke stc::unsubscribe [set resultDataSet$i]
	}
}

# US39315 HLTAPI ehancement for getting openflow group and flow stats

proc ::sth::openflow::emulation_openflow_control_view_individual_flow {returnKeyedList} {
    
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set returnValues ""

    set configList "stc::perform OpenflowViewIndividualFlowStatisticsCommand -Controller \{$handle\} -SwitchList \{$switch_handle_list\} "
    # config export stats parameters
    set exprotCmdList [getStcOptionValueList emulation_openflow_control export_file_set enable ""]
    if {[llength $exprotCmdList] > 0} {
        append configList "$exprotCmdList "
    }
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePathConfig "-ExportPath $::sth::openflow::userArgsArray(file_path) "
        append configList $filePathConfig
    }
    # config flow stats parameters
    set flowStatsCmdList [getStcOptionValueList emulation_openflow_control flow_stats_set enable ""]
    # insert a blank bewteen parameters
    if {[llength $flowStatsCmdList] > 0} {
        append configList $flowStatsCmdList
    }
    
    set retVal [::sth::sthCore::invoke $configList]
    set returnValues [::sth::openflow::get_flow_stats $retVal]
    keylset myreturnKeyedList individual_flow_stats $returnValues
}


proc ::sth::openflow::emulation_openflow_control_view_aggregate_flow {returnKeyedList} {

    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set returnValues ""
    
    set configList "stc::perform OpenflowViewAggregateFlowStatisticsCommand -Controller \{$handle\} -SwitchList \{$switch_handle_list\} "
    # config export stats parameters
    set exprotCmdList [getStcOptionValueList emulation_openflow_control export_file_set enable ""]
    if {[llength $exprotCmdList] > 0} {
        append configList "$exprotCmdList "
    }
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePathConfig "-ExportPath $::sth::openflow::userArgsArray(file_path) "
        append configList $filePathConfig
    }
    # config flow stats parameters
    set flowStatsCmdList [getStcOptionValueList emulation_openflow_control flow_stats_set enable ""]
    # insert a blank bewteen parameters
    if {[llength $flowStatsCmdList] > 0} {
        append configList $flowStatsCmdList
    }
    
    set retVal [::sth::sthCore::invoke $configList]
    set returnValues [::sth::openflow::get_flow_stats $retVal]
    keylset myreturnKeyedList aggregate_flow_stats $returnValues
}


proc ::sth::openflow::emulation_openflow_control_view_group_stats {returnKeyedList} {

    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    set handle $::sth::openflow::userArgsArray(handle)
    set switch_handle_list $::sth::openflow::userArgsArray(switch_handles)
    set returnValues ""
    set configList "stc::perform OpenflowViewGroupStatisticsCommand  -Controller \{$handle\} -SwitchList \{$switch_handle_list\} "
    # config export stats parameters
    set exprotCmdList [getStcOptionValueList emulation_openflow_control export_file_set enable ""]
    if {[llength $exprotCmdList] > 0} {
        append configList "$exprotCmdList "
    }
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set filePathConfig "-ExportPath $::sth::openflow::userArgsArray(file_path) "
        append configList $filePathConfig
    }
    # config flow stats parameters
    set groupStatsCmdList [getStcOptionValueList emulation_openflow_control group_stats_set enable ""]
    # insert a blank bewteen parameters
    if {[llength $groupStatsCmdList] > 0} {
        append configList $groupStatsCmdList
    }
    
    set retVal [::sth::sthCore::invoke $configList]
    set returnValues [::sth::openflow::get_flow_stats $retVal]
    keylset myreturnKeyedList group_stats $returnValues
}

proc ::sth::openflow::get_flow_stats {input} {
    
    # get file name 
    set fileNameList ""
    set returnValues ""
    set itemNum 0

    set fileNameIndex [lsearch $input "-ExportedFileNames"]
    if { $fileNameIndex > -1 } {
        set fileNameList [lindex $input [expr $fileNameIndex + 1]]
    }
    if {$fileNameList ne ""} {
        foreach fileName $fileNameList {
            if {[file exists $fileName]} {
                set fileHandle [open $fileName "r"]
                set csvDatas [split [read $fileHandle] \n]
                set rowCount [llength $csvDatas]
                if {$rowCount > 1} {
                    set statsKeyList [lindex $csvDatas 0]
                    set rowCount [expr $rowCount - 1 ]
                    for {set rowIndex 1} {$rowIndex < $rowCount} {incr rowIndex} {
                        set statsData [lindex $csvDatas $rowIndex]
                        set flowStatsData [::sth::openflow::process_stats_datas $statsKeyList $statsData]
                        keylset returnValues item$itemNum $flowStatsData
                        incr itemNum
                    }
                }
            }
        }
    }
    keylset returnValues results_count $itemNum
    # sort results
    set resultsCount [keylget returnValues results_count]
    if {$resultsCount > 0} {
        set Dpids ""
        for {set i 0} {$i < $resultsCount} {incr i} {
            set Dpid [keylget returnValues item$i.Dpid(hex)]
            set resultsId($Dpid) item$i
            set Dpids [concat $Dpids $Dpid]
        }
        set Dpids [lsort $Dpids]
        set results ""
        keylset results result_count $resultsCount
        for {set i 0 } {$i < $resultsCount} {incr i} {
            set flowStats [keylget returnValues $resultsId([lindex $Dpids $i])]
            keylset results item$i $flowStats
        }
        set returnValues $results
    }
    return $returnValues
}

proc ::sth::openflow::process_stats_datas {statsDataKeys statsDatas} {
    
    set flowStats ""
    # replace the " " with "_" between two words in one column
    regsub -all {\ } $statsDataKeys "_" statsDataKeys
    # replace ",_" with " " between two columns
    regsub -all {,_} $statsDataKeys " " statsDataKeys
    # split columns
    set statsDatas [split $statsDatas ","]
    # replace "." with "_" in the datas
    regsub -all {\.} $statsDatas " " statsDatas
    
    set datasCount [llength $statsDataKeys ]
    for {set i 0} {$i < $datasCount} {incr i} {
        keylset flowStats [lindex $statsDataKeys $i] [lindex $statsDatas $i]
    }
    return $flowStats
}

####################### support openflow switch in hltapi ####################
# US35019 support openflow switch in HLTAPI

proc ::sth::openflow::emulation_openflow_switch_config_enable {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::keyedList
    set ::sth::openflow::keyedList ""
    
    set device $::sth::openflow::userArgsArray(handle)
    processSwitchCount $device
    set functionsToRun [getFunctionToRun emulation_openflow_switch_config enable]
    foreach func $functionsToRun {
        $func $device enable
    }
    set myreturnKeyedList $::sth::openflow::keyedList
    return $myreturnKeyedList
}

proc ::sth::openflow::emulation_openflow_switch_config_modify {returnKeyedList} {

    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::keyedList
    set ::sth::openflow::keyedList ""

    if {[info exists ::sth::openflow::userArgsArray(handle)]} {
        set devhnd $::sth::openflow::userArgsArray(handle)
        if {[regexp -nocase {host} $devhnd]} {
            set device $devhnd
        } elseif {[regexp -nocase {oseswitchconfig} $devhnd]} {
            set device [::sth::sthCore::invoke stc::get $devhnd -parent]
        }
        if {$device != ""} {
            processSwitchCount $device
            set functionsToRun [getFunctionToRun emulation_openflow_switch_config modify]
            foreach func $functionsToRun {
                $func $device modify
            }
            set myreturnKeyedList $::sth::openflow::keyedList
        } else {
            ::sth::sthCore::log error "$device is a invalid openflow switch emulation handle"
            keylset myreturnKeyedList status $::sth::sthCore::FAILURE
        }
    } else {
        ::sth::sthCore::log error "Either handle or port_handle need to be specified"
        keylset myreturnKeyedList status $::sth::sthCore::FAILURE
    }
    return $myreturnKeyedList
}

proc ::sth::openflow::emulation_openflow_switch_config_disable {returnKeyedList} {

    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::keyedList
    set ::sth::openflow::keyedList ""
    
    if {[info exists ::sth::openflow::userArgsArray(handle)]} {
        set devhnd $::sth::openflow::userArgsArray(handle)
        if {[regexp -nocase {host} $devhnd]} {
            set oseSwitchHnd [::sth::sthCore::invoke stc::get $devhnd -children-OseSwitchConfig]
        } elseif {[regexp -nocase {oseswitchconfig} $devhnd]} {
            set oseSwitchHnd $devhnd
        }
        if {$oseSwitchHnd != ""} {
            ::sth::sthCore::invoke stc::perform delete -ConfigList $oseSwitchHnd
            keylset myreturnKeyedList status $::sth::sthCore::SUCCESS
        }
    } else {
        ::sth::sthCore::log error "Either handle or port_handle need to be specified"
        keylset myreturnKeyedList status $::sth::sthCore::FAILURE
    }
    return $myreturnKeyedList
}

proc ::sth::openflow::processSwitchCount {devhandle} {

    if {[info exists ::sth::openflow::userArgsArray(count)]} {
        set totalSwitchCount $::sth::openflow::userArgsArray(count)
        if {[string equal "grid" $::sth::openflow::userArgsArray(topo_type)]} {
            if {[expr $totalSwitchCount < $::sth::openflow::userArgsArray(grid_row_count) ]} {
                return -code 1 -errorcode -1 "Device count must be greater or equal to row count in OSE Grid Topology"
            }
        } elseif {[string equal "spine_leaf" $::sth::openflow::userArgsArray(topo_type)]} {
            set spineLeafCount [expr $::sth::openflow::userArgsArray(edge_switches_count) + $::sth::openflow::userArgsArray(spine_switches_count) + $::sth::openflow::userArgsArray(leaf_switches_count)]
            if {[expr $totalSwitchCount != $spineLeafCount]} {
                return -code 1 -errorcode -1 "Device count must be equal to the sum of configured numbers for Spine,Edge and Leaf Switches in OSE Spine_Leaf Topology"
            }
        }
    } else {
        set devCount [::sth::sthCore::invoke stc::get $devhandle -devicecount]
        if {[string equal "grid" $::sth::openflow::userArgsArray(topo_type)]} {
            if {[expr $devCount < $::sth::openflow::userArgsArray(grid_row_count) ]} {
                set totalSwitchCount $::sth::openflow::userArgsArray(grid_row_count)
            } else {
                set totalSwitchCount $devCount
            }
        } elseif {[string equal "spine_leaf" $::sth::openflow::userArgsArray(topo_type)]} {
            set totalSwitchCount [expr $::sth::openflow::userArgsArray(edge_switches_count) + $::sth::openflow::userArgsArray(spine_switches_count) + $::sth::openflow::userArgsArray(leaf_switches_count)]
        } else {
            set totalSwitchCount 4
        }
    }
    ::sth::sthCore::invoke stc::config $devhandle -devicecount $totalSwitchCount
}

proc ::sth::openflow::oseswitch_config {devhandle mode} {

    variable ::sth::openflow::keyedList
    set ipv4Handle ""

    set topIfHandles [::sth::sthCore::invoke stc::get $devhandle -toplevelif-Targets]
    foreach topIfHandle $topIfHandles {
        if {[string match ipv4* $topIfHandle]} {
            set ipv4Handle $topIfHandle
        }
    }
    set oseSwitchCount [::sth::sthCore::invoke stc::get $devhandle -devicecount]
    if {[string equal "false" $::sth::openflow::userArgsArray(configure_hosts)]} {
        if {[string equal "true" $::sth::openflow::userArgsArray(customize_packet_in)]} {
            return -code 1 -errorcode -1 "OSE $devhandle must have hosts enabled for Customize Packet-In Hosts Params."
        }
        if {[string equal "arp" $::sth::openflow::userArgsArray(traffic_type)]} {
            return -code 1 -errorcode -1 "OSE $devhandle must have hosts enabled for the ARP traffic test type."
        }
    }
    if {[expr $oseSwitchCount == 1] && [expr $::sth::openflow::userArgsArray(host_port_count) == 1] && [string equal "arp" $::sth::openflow::userArgsArray(traffic_type)]} {
        return -code 1 -errorcode -1 "ARP Traffic requires a minimum of 2 hosts. Please increase number of switch or number of hosts on OSE $devhandle."
    }
    if {[string equal "true" $::sth::openflow::userArgsArray(traffic_enable)] && [string equal "standalone" $::sth::openflow::userArgsArray(topo_type)]} {
        return -code 1 -errorcode -1 "Traffic is not supported on Standalone toptlogy type for device OSE $devhandle."
    }
    if {$ipv4Handle == ""} {
        return -code 1 -errorcode -1 "$devhandle OSE protocol is not connected to any valid IPv4 interface"
    } else {
        set oseSwitchHandle [::sth::sthCore::invoke stc::create OseSwitchConfig -under $devhandle]
        ::sth::sthCore::invoke stc::config $oseSwitchHandle -usesif-Targets $ipv4Handle
        set optionValueList [getStcOptionValueList emulation_openflow_switch_config oseswitch_config $mode $oseSwitchHandle]
        if {[llength $optionValueList]} {
            ::sth::sthCore::invoke stc::config $oseSwitchHandle $optionValueList
        }
        if {[info exists ::sth::openflow::userArgsArray(controller_ip_addr)]} {
            ::sth::sthCore::invoke stc::config $oseSwitchHandle -ControllerIpAddrList $::sth::openflow::userArgsArray(controller_ip_addr)
        }
        keylset ::sth::openflow::keyedList handle $oseSwitchHandle
    }
}

proc ::sth::openflow::oseswitch_modify {devhandle mode} {

    variable ::sth::openflow::keyedList
    
    set oseSwitchHandle [::sth::sthCore::invoke stc::get $devhandle -children-OseSwitchConfig]
    set optionValueList [getStcOptionValueList emulation_openflow_switch_config oseswitch_modify $mode $oseSwitchHandle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $oseSwitchHandle $optionValueList
    }
    if {[info exists ::sth::openflow::userArgsArray(controller_ip_addr)]} {
        ::sth::sthCore::invoke stc::config $oseSwitchHandle -ControllerIpAddrList $::sth::openflow::userArgsArray(controller_ip_addr)
    }
    keylset ::sth::openflow::keyedList handle $oseSwitchHandle
}

proc ::sth::openflow::osetopo_config {devhandle mode} {

    variable ::sth::openflow::keyedList

    set oseSwitchHandle [::sth::sthCore::invoke stc::get $devhandle -children-OseSwitchConfig]
    set optionValueList [getStcOptionValueList emulation_openflow_switch_config osetopo_config $mode $oseSwitchHandle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $oseSwitchHandle $optionValueList
    }
    keylset ::sth::openflow::keyedList handle $oseSwitchHandle
}

proc ::sth::openflow::osehost_config {devhandle mode} {

    variable ::sth::openflow::keyedList
    
    set oseSwitchHandle [::sth::sthCore::invoke stc::get $devhandle -children-OseSwitchConfig]
    set optionValueList [getStcOptionValueList emulation_openflow_switch_config osehost_config $mode $oseSwitchHandle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $oseSwitchHandle $optionValueList
    }
    keylset ::sth::openflow::keyedList handle $oseSwitchHandle
}

proc ::sth::openflow::osetraffic_config {devhandle mode} {

    variable ::sth::openflow::keyedList

    set oseSwitchHandle [::sth::sthCore::invoke stc::get $devhandle -children-OseSwitchConfig]
    set oseTrafficHandle [::sth::sthCore::invoke stc::get $oseSwitchHandle -children-OseTrafficConfig]
    set optionValueList [getStcOptionValueList emulation_openflow_switch_config osetraffic_config $mode $oseTrafficHandle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $oseTrafficHandle $optionValueList
    }
    keylset ::sth::openflow::keyedList handle $oseSwitchHandle
}
proc ::sth::openflow::oseglobalparams_config {devhandle mode} {

    variable ::sth::openflow::keyedList
    
    set oseGloblaParamsHnd [::sth::sthCore::invoke stc::get project1 -children-OseGlobalParams]
    set optionValueList [getStcOptionValueList emulation_openflow_switch_config oseglobalparams_config $mode $oseGloblaParamsHnd]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $oseGloblaParamsHnd $optionValueList
    }
}

proc ::sth::openflow::emulation_openflow_switch_control_common {} {
    variable ::sth::openflow::userArgsArray
    
    set handleList ""
    if {[info exists ::sth::openflow::userArgsArray(handle)]} {
        foreach handle $::sth::openflow::userArgsArray(handle) {
            if {[regexp -nocase {^oseswitchconfig[0-9]+} "$handle" ]} {
                lappend handleList $handle
            } else {
                set oseSwitch [::sth::sthCore::invoke stc::get $handle -children-OseSwitchConfig]
                lappend handleList $oseSwitch
            }
        }
    } else {
        set portList $::sth::openflow::userArgsArray(port_handle)
        foreach portHandle $portList {
            set devices [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
            foreach deviceHandle $devices {
                set oseSwitch [::sth::sthCore::invoke stc::get $deviceHandle -children-OseSwitchConfig]
                if {![regexp "^$" $oseSwitch]} {
                    set handleList [concat $handleList $oseSwitch]
                }
            }
        }
    }
    
    return $handleList
}

proc ::sth::openflow::emulation_openflow_switch_check_state {oseSwitchHandles actionType} {
    foreach oseSwitchHandle $oseSwitchHandles {
        set oseState [::sth::sthCore::invoke stc::get $oseSwitchHandle -state]
        if {[string equal "STARTED" $oseState]} {
            set myReturnValue "true"
        } else {
            switch -- $actionType {
                "break_link" {
                   set commandName "break link"
                }
                "restore_link" {
                    set commandName "restore link"
                }
                "start_ose_traffic" {
                    set commandName "start ose traffic"
                }
                "stop_ose_traffic" {
                    set commandName "stop ose traffic"
                }
                "restore_all_links" {
                    set commandName "restore all links"
                }
                "get_ose_flows" {
                    set commandName "get ose flows"
                }
                default {
                    return -code 1 -errorcode -1 "Action $commandName is not supported in emulation_openflow_switch_control."
                }
            } 
            return -code 1 -errorcode -1 "To execute $commandName command the openflow switch $oseSwitchHandle must be started ."
        }
    }
    return $myReturnValue
}

proc ::sth::openflow::emulation_openflow_switch_control_start_ose {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    ::sth::sthCore::invoke stc::perform ProtocolStartCommand -protocolList $protocolList
    ::sth::sthCore::invoke stc::perform OseWaitForSwitchConfigStateCommand -ObjectList $protocolList -WaitForState STARTED -WaitTime 30
}

proc ::sth::openflow::emulation_openflow_switch_control_stop_ose {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    ::sth::sthCore::invoke stc::perform ProtocolStopCommand -protocolList $protocolList
    ::sth::sthCore::invoke stc::perform OseWaitForSwitchConfigStateCommand -ObjectList $protocolList -WaitForState STOPPED -WaitTime 30
}

proc ::sth::openflow::emulation_openflow_switch_control_start_ose_traffic {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    if {[emulation_openflow_switch_check_state $protocolList start_ose_traffic]} {
        ::sth::sthCore::invoke stc::perform OseStartTrafficCommand -SwitchBlockList $protocolList
        ::sth::sthCore::invoke stc::perform spirent.switching.ose.OseWaitForTrafficStateCommand -ObjectList $protocolList -WaitState STARTED -WaitTime 30
    }
}

proc ::sth::openflow::emulation_openflow_switch_control_stop_ose_traffic {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    if {[emulation_openflow_switch_check_state $protocolList stop_ose_traffic]} {
        ::sth::sthCore::invoke stc::perform OseStopTrafficCommand -SwitchBlockList $protocolList
        ::sth::sthCore::invoke stc::perform spirent.switching.ose.OseWaitForTrafficStateCommand -ObjectList $protocolList -WaitState STOPPED -WaitTime 30
    }
}

proc ::sth::openflow::emulation_openflow_switch_control_restore_all_links {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    if {[emulation_openflow_switch_check_state $protocolList restore_all_links]} {
        ::sth::sthCore::invoke stc::perform OseRestoreAllLinksCommand -SwitchBlockList $protocolList
    }
}

proc ::sth::openflow::emulation_openflow_switch_control_break_link {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    if {[llength $protocolList] > 1 } {
        return -code 1 -errorcode -1 "The break link command only support a signle openflow switch device block."
    } else {
        if {[emulation_openflow_switch_check_state $protocolList break_link ]} {
            set configList "stc::perform OseLinkCommand -SwitchBlockHandleList \{$protocolList\} -PortStatus BREAK "
            append configList [getStcOptionValueList emulation_openflow_switch_control ose_link_command enable ""]
            ::sth::sthCore::invoke $configList
        }
    }
}

proc ::sth::openflow::emulation_openflow_switch_control_restore_link {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    if {[llength $protocolList] > 1 } {
        return -code 1 -errorcode -1 "The restore link command only support a signle openflow switch device block."
    } else {
        if {[emulation_openflow_switch_check_state $protocolList restore_link ]} {
            set configList "stc::perform OseLinkCommand -SwitchBlockHandleList \{$protocolList\} -PortStatus RESTORE "
            append configList [getStcOptionValueList emulation_openflow_switch_control ose_link_command enable ""]
            ::sth::sthCore::invoke $configList
        }
    }
}

proc ::sth::openflow::emulation_openflow_switch_control_get_ose_flows {returnKeyedList} {
    set protocolList [emulation_openflow_switch_control_common]
    # the argument ExportFilePath is not work , this is a temporary soluition.
    if {[info exists ::sth::openflow::userArgsArray(file_path)]} {
        set myFilePath [file join $::sth::openflow::userArgsArray(file_path) oseFlows.txt]
    } else {
        set myFilePath [file join [pwd] oseFlows.txt]
    }
    if {[emulation_openflow_switch_check_state $protocolList get_ose_flows]} {
        set configList "stc::perform OseGetFlowsCommand -SwitchBlockHandleList \{$protocolList\} -ExportFilePath $myFilePath"
        set getflows [::sth::sthCore::invoke $configList] 
        set flowsDumpIndex [expr [lsearch $getflows "-FlowsDump" ] + 1]
        set flowsData [lindex $getflows $flowsDumpIndex]
        set fileHandle [open $myFilePath "w"]
        puts $fileHandle $flowsData
        close $fileHandle
    }
}


proc ::sth::openflow::emulation_openflow_switch_control_manage_tls_files {returnKeyedList} {
    
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    
    set port_handle_list $::sth::openflow::userArgsArray(port_handle)

    if {[info exists ::sth::openflow::userArgsArray(tls_file_action)]} {
        set tls_action $::sth::openflow::userArgsArray(tls_file_action)
    } else {
        ::sth::sthCore::processError myreturnKeyedList "Option tls_file_action mandatroy for action- manage_tls_files" {}
        return -code error $myreturnKeyedList 
    }
    switch -- $tls_action {
        upload {
            set cmd "spirent.core.TlsKeyCertificateUploadCommand"
        }
        delete {
            set caFileList ""
            set certFileList ""
            set priKeyFileList ""
            set cmd "spirent.core.TlsKeyCertificateDeleteCommand"
            #If "tls_file_name_list"  is not specified, get it from port handle
            if {![info exists ::sth::openflow::userArgsArray(tls_file_name_list)]} {
                foreach port $port_handle_list {
                    array set fileHndRet [::sth::sthCore::invoke "stc::perform spirent.core.TlsKeyCertificateEnumerateCommand -Port $port"]
                    if {$fileHndRet(-CaCertificateFiles) != ""} {
                        append caFileList " $fileHndRet(-CaCertificateFiles)"
                    }
                    if {$fileHndRet(-CertificateFiles) != ""} {
                        append certFileList " $fileHndRet(-CertificateFiles)"
                    }
                    if {$fileHndRet(-PrivateKeyFiles) != ""} {
                        append priKeyFileList " $fileHndRet(-PrivateKeyFiles)"
                    }
                }
                set tls_file_type $::sth::openflow::userArgsArray(tls_file_type)
                switch -- $tls_file_type {
                   private_key {
                        if { $priKeyFileList == "" } {
                            ::sth::sthCore::log warn "Private Key File not present in the port"
                            #::sth::sthCore::processError myreturnKeyedList "Private Key File not present in the port" {}
                            #return -code error $myreturnKeyedList 
                        } else {
                            set ::sth::openflow::userArgsArray(tls_file_name_list) "\{ $priKeyFileList \}"
                        }
                   }
                   certificate {
                        if { $certFileList == "" } {
                            ::sth::sthCore::log warn "Certificate File not present in the port"
                            #::sth::sthCore::processError myreturnKeyedList "Certificate File not present in the port" {}
                            #return -code error $myreturnKeyedList 
                        } else {
                            set ::sth::openflow::userArgsArray(tls_file_name_list) "\{ $certFileList \}"
                        }
                   }
                   ca_certificate {
                        if { $caFileList == "" } {
                            ::sth::sthCore::log warn "CA Certificate File not present in the port"
                            #::sth::sthCore::processError myreturnKeyedList "CA Certificate File not present in the port" {}
                            #return -code error $myreturnKeyedList 
                        } else {
                            set ::sth::openflow::userArgsArray(tls_file_name_list) "\{ $caFileList \}"
                        }
                   }
                }
            }
        }
    }

    #HandleList: List of switches to send the SET command to.
    set configList "stc::perform $cmd -PortList \{$port_handle_list\} "
    append configList [getStcOptionValueList emulation_openflow_switch_control manage_tls_files enable ""]

    ::sth::sthCore::invoke $configList
}


proc ::sth::openflow::emulation_openflow_switch_stats_func {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::openflow::userArgsArray
    set protocolList [emulation_openflow_switch_control_common] 
    set mymode $::sth::openflow::userArgsArray(mode)
    if {[regexp -nocase "all" $mymode]} {
        set mymode "controller_aggregate switch_results"
    }
    
    if {[regexp -nocase "controller_aggregate" $mymode]} {
        set oseCtrlAggResultDataSet [::sth::sthCore::invoke stc::subscribe -parent project1 -ConfigType port -resulttype osecontrolleraggregateresults]
        ::sth::sthCore::invoke stc::sleep 3
        set oesCtrlAggResultHnds [::sth::sthCore::invoke stc::get $oseCtrlAggResultDataSet -resultchild-Targets]
        if {$oesCtrlAggResultHnds ne ""} {
            set ctrlNum 1
            foreach oesCtrlAggResultHnd $oesCtrlAggResultHnds {
                set oseCtrlAggreResult [::sth::sthCore::invoke stc::get $oesCtrlAggResultHnd]
                foreach {attr val} $oseCtrlAggreResult {
                    set attr [string range $attr 1 end]
                    keylset retVal $attr $val
                }
                keylset ctrlResults Controller$ctrlNum $retVal
                incr ctrlNum
            }
            keylset myreturnKeyedList controller_aggregate $ctrlResults
        }
        ::sth::sthCore::invoke stc::unsubscribe $oseCtrlAggResultDataSet
    }

    if {[regexp -nocase "switch_results" $mymode]} {
        set oseSwitchResults [sth::drv_stats \
            -drv_name "oseSwitchResults" \
            -size 100 \
            -query_from $protocolList \
            -properties "OseSwitchConfig.SwitchName OseSwitchConfig.SwitchIpAddress OseSwitchConfig.State OseSwitchConfig.Dpid OseSwitchConfig.OpenflowVersion OseSwitchConfig.ConnectedControllerCount OseSwitchConfig.PortCount OseSwitchConfig.ActiveFlowCount" \
            ]
        if {[llength $oseSwitchResults] > 0} {
            set resultsCount [keylget oseSwitchResults result_count]
            set oseSwitchNames {}
            # sort the results 
            for {set i 0} {$i < $resultsCount} {incr i} {
                set oseSwitchName [keylget oseSwitchResults item$i.OseSwitchConfigSwitchName]
                set resultsId($oseSwitchName) item$i
                set oseSwitchNames [concat $oseSwitchNames $oseSwitchName]
            }
            set oseSwitchNames [lsort $oseSwitchNames]
            set results ""
            keylset results result_count $resultsCount
            for {set i 0 } {$i < $resultsCount} {incr i} {
                set oseResult [keylget oseSwitchResults $resultsId([lindex $oseSwitchNames $i])]
                keylset results item$i $oseResult
            }
        }
        keylset myreturnKeyedList ose_switch_results $results
    }
}
