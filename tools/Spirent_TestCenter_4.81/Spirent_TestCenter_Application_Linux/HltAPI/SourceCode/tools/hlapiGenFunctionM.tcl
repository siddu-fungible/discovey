namespace eval ::sth::hlapiGen:: {

}

#########################################################################################################
#    hlapiGenFunctionH.tcl includes the functions to handle the hltapi configure functions 
#    whose (protocol) name is from M to O.
#    Added protocols/functions:
#              a. mld
#              b. ospf
#########################################################################################################

proc ::sth::hlapiGen::hlapi_gen_device_mld {device class mode hlt_ret cfg_args first_time} {
    
    #handle ipv6group
    set table_name "::sth::multicast_group::multicast_groupTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_multicast_group_config"
    
    #make the mode also be create when not first time
    set mode create
    set port [stc::get $device -affiliationport-Targets]
    set igmpportconfig [lindex [stc::get $port -children-igmpportconfig] 0]
    set mldportconfig  [lindex [stc::get $port -children-mldportconfig ] 0]
    
    set ::sth::hlapiGen::$port\_$mldportconfig\_attr(-ratepps) [set ::sth::hlapiGen::$port\_$igmpportconfig\_attr(-ratepps)]
    
    if {[info exists $name_space\emulation_multicast_group_config\_Initialized]} {
        unset $name_space\emulation_multicast_group_config\_Initialized
    }
    if {[info exists $name_space\emulation_multicast_source_config\_Initialized]} {
        unset $name_space\emulation_multicast_source_config\_Initialized
    }
    ::sth::sthCore::InitTableFromTCLList [set $table_name]

    set mldhosthandle [stc::get $device -children-$class]
    set mldhosthandle [lindex $mldhosthandle 0]
	set sth::hlapiGen::device_ret($mldhosthandle) $hlt_ret
    set childList [stc::get $mldhosthandle -children]
    set childrenList [stc::get $mldhosthandle -children]
    set j 0
    set group_pool_handle ""
    set source_pool_handle ""
    if {[regexp -nocase "mldGroupMembership" $childrenList]} {
        set mldGroupMembershiphandles [stc::get $mldhosthandle -children-mldGroupMembership]
        foreach mldGroupMembershiphandle $mldGroupMembershiphandles {
            incr j
            set mldGroupMembershipattr [stc::get $mldGroupMembershiphandle]
            if {[regexp -nocase "subscribedgroups" $mldGroupMembershipattr]} {  
                #MldGroupMembership  SubscribedGroups Ipv6Group
                set ipv6group [stc::get $mldGroupMembershiphandle -subscribedgroups-Targets]
                if {![info exists sth::hlapiGen::device_ret($ipv6group)]} {
                    set cmd_name emulation_multicast_group_config
                    set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_start) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_step) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(ip_prefix_len) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(num_groups) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(pool_name) "Ipv6Group"
        
                    set ipv6groupret "$hlt_ret\_ipgroup\_$j"
                    set hlapi_script "      set $ipv6groupret \[sth::$cmd_name\\\n"
                    get_attr $ipv6group $ipv6group    
                    foreach ipv6group_obj [array names ::sth::hlapiGen::$ipv6group\_obj] {
                        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $ipv6group $ipv6group $ipv6group_obj]
                    }
                        
                    #handle ipv6networkblock
                    set ipblock [stc::get $ipv6group -children-ipv6networkblock]
                    set ipblock [lindex $ipblock 0]
                    get_attr $ipblock $ipblock
                    set ::sth::hlapiGen::$ipblock\_$ipblock\_attr(-startiplist) [lindex [set ::sth::hlapiGen::$ipblock\_$ipblock\_attr(-startiplist)] 0]
                    foreach ipblock_obj [array names ::sth::hlapiGen::$ipblock\_obj] {
                        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $ipblock $ipblock $ipblock_obj]
                    }
                        
                    append hlapi_script "			-mode         create\\\n"
                    append hlapi_script "\]\n"
                    puts_to_file $hlapi_script
                    gen_status_info $ipv6groupret "sth::$cmd_name"
                    set sth::hlapiGen::device_ret($ipv6group) $ipv6groupret
                    set group_pool_handle [concat $group_pool_handle "\[keylget $ipv6groupret handle\]"] 
                } else {
                    set group_ret [lindex $sth::hlapiGen::device_ret($ipv6group) 0]
                    set group_pool_handle [concat $group_pool_handle "\[keylget $group_ret handle\]"]
                }
            }
            if {[stc::get $mldGroupMembershiphandle -UserDefinedSources]} { 
                #MldGroupMembership  SubscribedGroups Ipv6Group
                set ipblock [stc::get $mldGroupMembershiphandle -children-Ipv6NetworkBlock]
                set ipblock [lindex $ipblock 0]
                if {![info exists sth::hlapiGen::device_ret($ipblock)]} {
                    set cmd_name emulation_multicast_source_config
                    set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_start) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_step) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(ip_prefix_len) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(num_sources) "Ipv6NetworkBlock"
                    set ::sth::multicast_group::$cmd_name\_stcobj(pool_name) "Ipv6Group"
                    set ipv6groupsrcret "$hlt_ret\_ipblock\_$j"
                    set hlapi_script "      set $ipv6groupsrcret \[sth::$cmd_name\\\n"
                    
                    get_attr $ipblock $ipblock
                    set ::sth::hlapiGen::$ipblock\_$ipblock\_attr(-startiplist) [lindex [set ::sth::hlapiGen::$ipblock\_$ipblock\_attr(-startiplist)] 0]
                    
                    foreach ipblock_obj [array names ::sth::hlapiGen::$ipblock\_obj] {
                        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $ipblock $ipblock $ipblock_obj]
                    }
                        
                    append hlapi_script "			-mode         create\\\n"
                    append hlapi_script "\]\n"
                    puts_to_file $hlapi_script
                    gen_status_info $ipv6groupsrcret "sth::$cmd_name"
                    set sth::hlapiGen::device_ret($ipblock) "$ipv6groupsrcret 0"
                    set source_pool_handle [concat $source_pool_handle "\[keylget $ipv6groupsrcret handle\]"]
                } else {
                    set src_ret [lindex $sth::hlapiGen::device_ret($ipv6group) 0]
                    set source_pool_handle [concat $source_pool_handle "\[keylget $src_ret handle\]"]
                }
            }
        }
    }
    
    if {[info exists $name_space\emulation_multicast_group_config\_Initialized]} {
        unset $name_space\emulation_multicast_group_config\_Initialized
    }
    if {[info exists $name_space\emulation_multicast_source_config\_Initialized]} {
        unset $name_space\emulation_multicast_source_config\_Initialized
    }
    
    #config all children and pass the parameters info basic
    set cfgFromChildren ""
    
    set childrenList [stc::get $mldhosthandle -children]
    if {[regexp -nocase "mldGroupMembership" $childrenList]&&("MLD_V2" == [stc::get $mldhosthandle -Version])} {
        set children [stc::get $mldhosthandle -children-mldGroupMembership]
        set ipnwblock [stc::get [lindex $children 0] -children-Ipv6NetworkBlock]
        append cfgFromChildren "			-filter_mode			    [string tolower [stc::get [lindex $children 0] -FilterMode]]\\\n"
        append cfgFromChildren "			-filter_ip_addr			    [lindex [stc::get $ipnwblock -StartIpList] 0]\\\n"

    }
    #vlan_id_mode
    #vlan_id_outer_mode
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        foreach vlanif $vlanifs {
            set stack_target [set ::sth::hlapiGen::$device\_$vlanif\_attr(-stackedonendpoint-targets)]
            set isrange [set ::sth::hlapiGen::$device\_$vlanif\_attr(-isrange)]
            if {[regexp -nocase "true" $isrange]} {
                set vlan_mode "increment"
            } else {
                set vlan_mode "fixed"
            }
            if {[llength $vlanifs] > 1} {
                if {[regexp {ethiiif} $stack_target]} {
                    append cfgFromChildren "     -vlan_id_outer_mode    $vlan_mode\\\n"
                } else {
                    append cfgFromChildren "     -vlan_id_mode    $vlan_mode\\\n"
                }
            } else {
                append cfgFromChildren "     -vlan_id_mode    $vlan_mode\\\n"
            }
        }
    }
    
    set table_name_mld "::Mld::mldTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name_mld]
    regsub {\d+$} $device "" update_obj
    set ::Mld::emulation_mld_config_stcobj(count) "$update_obj"
    
    if {$::sth::hlapiGen::scaling_test} {
        set ::Mld::emulation_mld_config_stcattr(count) "count"
    } else {
        set ::Mld::emulation_mld_config_stcattr(count) "DeviceCount"
    }
    #handle link_local_intf_ip_addr
    set ::Mld::emulation_mld_config_stcobj(link_local_intf_ip_addr) "_none_"
    set ::Mld::emulation_mld_config_stcobj(link_local_intf_ip_addr_step) "_none_"
    set ::Mld::emulation_mld_config_stcobj(link_local_intf_prefix_len) "_none_" 
    set ipv6ifs [stc::get $device -children-Ipv6If]
    if {1 < [llength $ipv6ifs]} {
        set local_ipv6 [lindex $ipv6ifs 0]
        foreach ipv6if $ipv6ifs {
            if {[regexp -nocase "Ipv6If_Link_Local" [::sth::hlapiGen::pre_process_obj $device ipv6if $ipv6if]]} {
                set local_ipv6 $ipv6if
            }
        }
        append cfgFromChildren "     -link_local_intf_ip_addr    [stc::get $local_ipv6 -Address]\\\n"
        append cfgFromChildren "     -link_local_intf_ip_addr_step    [stc::get $local_ipv6 -AddrStep]\\\n"
        append cfgFromChildren "     -link_local_intf_prefix_len    [stc::get $local_ipv6 -PrefixLength]\\\n"
    }
    
    if {"false" == [stc::get $mldhosthandle -ForceRobustJoin]} {
        set ::Mld::emulation_mld_config_stcobj(robustness) "_none_"
    }
    
    #call the basic function
    hlapi_gen_device_basic  $device $class $mode $hlt_ret $cfgFromChildren $first_time
    
    if {![regexp "^$" $group_pool_handle]} {    
        #handle emulation_mld_group_config 
        puts_to_file "set mld_host \[keylget $hlt_ret handle\] \n"
        #puts_to_file "set mld_group \[keylget $ipv6groupret handle\] \n"
        puts_to_file "set mld_group \"$group_pool_handle\" \n"
        if {![regexp "^$" $source_pool_handle]} {
            puts_to_file "set mld_group_src \"$source_pool_handle\" \n"
        }
        set hlapi_script "      set $hlt_ret\_group \[sth::emulation_mld_group_config\\\n"
        append hlapi_script "			-mode         create\\\n"
        append hlapi_script "			-session_handle         \$mld_host\\\n"
        
        append hlapi_script "			-group_pool_handle         \$mld_group\\\n"
        if {![regexp "^$" $source_pool_handle]} {
            append hlapi_script "			-source_pool_handle         \$mld_group_src\\\n"
        }
        append hlapi_script "\]\n"
        puts_to_file $hlapi_script
        gen_status_info $hlt_ret\_group "sth::emulation_mld_group_config"
    }
}



proc ::sth::hlapiGen::hlapi_gen_device_ospf {device class mode hlt_ret cfg_args first_time} {
    
    #config all children and pass the parameters info basic
     
    set ospfconfighandle [stc::get $device -children-$class]
    set ospfconfighandle [lindex $ospfconfighandle 0]
    set table_name "::sth::ospf::ospfTable"
    regexp {([2|3])} $class match ospfversion
    set cmd_name "emulation_ospfv2_config"
    set cfgFromChildren ""
    if {$ospfversion == 3} {
        set cmd_name "emulation_ospfv3_config"
        if {[regexp -nocase "ipv4if" [stc::get $device -children]]} {
            append cfgFromChildren "                       -ip_version              4_6\\\n"
        } else {
            append cfgFromChildren "                       -ip_version              6\\\n"
        }
    } 
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    
   if {[info exists sth::hlapiGen::$device\_obj(greif)]} {
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args
        append cfgFromChildren "                       -tunnel_handle              \$gre_ret\\\n"
    }
    
    set  ospfversion "ospfv$ospfversion"
    append cfgFromChildren "			-session_type			    $ospfversion\\\n"
    
    #update the stcobj for the parameters whose stcobj is router in table file, the devicehandle may be emulateddevice, then these parameters will be missed.
    set router_paramlist "count router_id router_id_step"
    regsub {\d+$} $device "" update_obj
    foreach router_param $router_paramlist {
        set ::sth::ospf::$cmd_name\_stcobj($router_param) "$update_obj"
    }
   
    #updat the stcobj for mac_addr_start
    set ::sth::ospf::$cmd_name\_stcobj(mac_address_start) "ethiiif"
    set ::sth::ospf::$cmd_name\_stcattr(mac_address_start) "sourceMac"
    
    set childList [stc::get $ospfconfighandle -children]
    
    foreach child $childList {
        if {[regexp -nocase "Ospfv2AuthenticationParams" $child] || [regexp -nocase "TeParams" $child]} {
            #only handle Dhcpv4ServerDefaultPoolConfig and it's child:Dhcpv4ServerMsgOption
            if {[regexp -nocase "TeParams" $child]} {
                set SubTlv [stc::get $child -SubTlv]
                if {($SubTlv eq "0") || ($SubTlv eq "NONE")} {
                    continue    
                }
                foreach arg "te_admin_group te_max_bw te_max_resv_bw te_unresv_bw_priority0 
                            te_unresv_bw_priority1 te_unresv_bw_priority2 te_unresv_bw_priority3
                            te_unresv_bw_priority4 te_unresv_bw_priority5 te_unresv_bw_priority6 
                            te_unresv_bw_priority7 " {
                    set ::sth::ospf::$cmd_name\_stcobj($arg) "_none_"
                }
                if {[regexp -nocase "GROUP" $SubTlv]} {
                    set ::sth::ospf::$cmd_name\_stcobj(te_admin_group) "TeParams"    
                }
                if {[regexp -nocase "MAX_BW" $SubTlv]} {
                    set ::sth::ospf::$cmd_name\_stcobj(te_max_bw) "TeParams"    
                }
                if {[regexp -nocase "MAX_RSV_BW" $SubTlv]} {
                    set ::sth::ospf::$cmd_name\_stcobj(te_max_resv_bw) "TeParams"    
                }
                if {[regexp -nocase "UNRESERVED" $SubTlv]} {
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority0) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority1) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority2) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority3) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority4) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority5) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority6) "TeParams"
                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority7) "TeParams" 
                }
                
            }
            if {[regexp -nocase "Ospfv2AuthenticationParams" $child]} {
                set Authentication [stc::get $child -Authentication]
                if {$Authentication eq "NONE"} {
                    set ::sth::ospf::$cmd_name\_stcattr(password) "_none_"
                    set ::sth::ospf::$cmd_name\_stcattr(md5_key_id) "_none_"
                }
                if {$Authentication eq "SIMPLE"} {
                    set ::sth::ospf::$cmd_name\_stcattr(md5_key_id) "_none_"
                }
            }
            get_attr $child $child
            #convert ipaddress_increment from a.c.b.d to a number 
            if {[info exists sth::hlapiGen::$child\_$child\_attr(-hostaddrstep)]} {
                set tmpvalue [set sth::hlapiGen::$child\_$child\_attr(-hostaddrstep)]
                set sth::hlapiGen::$child\_$child\_attr(-hostaddrstep) [::sth::hlapiGen::ipaddr2dec $tmpvalue]
            }
            foreach child_obj [array names ::sth::hlapiGen::$child\_obj] {
                append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $child $child $child_obj]
            }
        }
    }
    set ::sth::ospf::$cmd_name\_stcattr(password) "Password"
    set ::sth::ospf::$cmd_name\_stcattr(md5_key_id) "Md5KeyId"
    #change the cfgfunction of class
    set ::sth::ospf::$cmd_name\_stcobj(area_type) "_none_"
    set ::sth::ospf::$cmd_name\_stcobj(demand_circuit) "_none_"
    set ::sth::ospf::$cmd_name\_stcobj(option_bits) "_none_"
    set ::sth::ospf::$cmd_name\_stcobj(network_type) "_none_"
    
    set nw_type [stc::get $ospfconfighandle -NetworkType]
    switch -- $nw_type {
        P2P {
            set  nw_type "ptop"   
        }
        BROADCAST {
            set  nw_type "broadcast"   
        }
        NATIVE {
            set  nw_type "native"   
        } 
    }
    append cfgFromChildren "			-network_type			    $nw_type\\\n"
    
    set options [stc::get $ospfconfighandle -Options]
    set optionsHex 0
    if {[regexp "TBIT" $options]||[regexp "V6BIT" $options]} {
        set optionsHex [expr $optionsHex | 0x1]
    }
    if {[regexp "EBIT" $options]} {
        set optionsHex [expr $optionsHex | 0x2]
    }
    if {[regexp "MCBIT" $options]} {
        set optionsHex [expr $optionsHex | 0x4]
    }
    if {[regexp "NPBIT" $options]||[regexp "NBIT" $options]} {
        set optionsHex [expr $optionsHex | 0x8]
    }
    if {[regexp "EABIT" $options]||[regexp "RBIT" $options]} {
        set optionsHex [expr $optionsHex | 0x10]
    }
    if {[regexp "DCBIT" $options]} {
        set optionsHex [expr $optionsHex | 0x20]
        append cfgFromChildren "			-demand_circuit			    1\\\n"
    }
    if {[regexp "OBIT" $options]} {
        set optionsHex [expr $optionsHex | 0x40]
    }
    
    append cfgFromChildren "			-option_bits			    [format "0x%x" $optionsHex]\\\n"
    #call the basic function
    set ospf_config [hlapi_gen_device_basic_without_puts  $device $class create $hlt_ret $cfgFromChildren $first_time]
    regsub -all emulation_ospfv2_config  $ospf_config emulation_ospf_config ospf_config
    regsub -all emulation_ospfv3_config  $ospf_config emulation_ospf_config ospf_config
    set ospf_config [remove_unuse_attr $ospf_config $name_space $cmd_name]
    puts_to_file $ospf_config
    gen_status_info $hlt_ret "sth::emulation_ospf_config"
    handle_lsa_config $device $class $mode $hlt_ret $cfg_args $first_time $ospfversion
    handle_topo_route_config $device $class $mode $hlt_ret $cfg_args $first_time $ospfversion
}


proc ::sth::hlapiGen::mask_unused_ipnetworkblock {type ospfversion} {
    set stcobj "_none_"
    switch -- $type {
        "ext_pool" {
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_number_of_prefix) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_step) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_number_of_prefix) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_step) $stcobj
            if {$ospfversion eq "ospfv3"} {
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_number_of_prefix) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_length) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_start) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_step) $stcobj
            }
        }
        "summary_pool" {
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_number_of_prefix) $stcobj
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_step) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_number_of_prefix) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_step) $stcobj
            if {$ospfversion eq "ospfv3"} {
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_number_of_prefix) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_length) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_start) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_step) $stcobj
            }
        }
        "nssa_ext_pool" {
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_number_of_prefix) $stcobj
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_step) $stcobj  
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_number_of_prefix) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_step) $stcobj
            if {$ospfversion eq "ospfv3"} {
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_number_of_prefix) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_length) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_start) $stcobj 
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_step) $stcobj
            }
        }
        "intra_area_prefix" {
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_number_of_prefix) $stcobj
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_step) $stcobj  
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_number_of_prefix) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_step) $stcobj
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_number_of_prefix) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_length) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_start) $stcobj 
            set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_step) $stcobj 
        }
    }    
}

proc ::sth::hlapiGen::unmask_unused_ipnetworkblock {ospfversion} {
    
    set stcobj "ipv4networkblock"
    if {$ospfversion eq "ospfv3"} {
        set stcobj "ipv6networkblock"
        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_number_of_prefix) $stcobj 
        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_length) $stcobj 
        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_start) $stcobj 
        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(intra_area_prefix_step) $stcobj 
    }
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_number_of_prefix) $stcobj
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_length) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_start) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_step) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_number_of_prefix) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_length) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_start) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_step) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_number_of_prefix) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_length) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_start) $stcobj 
    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(summary_prefix_step) $stcobj

}

proc ::sth::hlapiGen::isValidlsalinkList {lsalinkList} {
    set attrlist "LinkData Metric LinkType"
    set lsalink0 [lindex $lsalinkList 0]
    array set attrvalue "LinkData [stc::get $lsalink0 -LinkData] Metric [stc::get $lsalink0 -Metric] LinkType [stc::get $lsalink0 -LinkType]"
    foreach attr $attrlist {
        foreach lsalink $lsalinkList {
            if {[stc::get $lsalink -$attr] ne $attrvalue($attr)} {
                return 0    
            }    
        }    
    }
    return 1
}

#####handler for ospf lsa config and topology route config#############
proc ::sth::hlapiGen::handle_lsa_config {device class mode hlt_ret cfg_args first_time ospfversion} {
    set ospfconfighandlelist ""
    #update the devices for the scaling test
    set devicelist [update_device_handle $device $class $first_time]
    
    foreach device $devicelist {
        set ospfconfighandle [stc::get $device -children-$class]
        set ospfconfighandle [lindex $ospfconfighandle 0]
        set ospfconfighandlelist [concat $ospfconfighandlelist $ospfconfighandle]
    }
    
    set table_name "::sth::ospf::ospfTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    
    if {$ospfversion eq "ospfv2"} {
        #ospfv2
        set cmd_name "emulation_ospfv2_lsa_config"    
    } else {
        #ospfv3
        set cmd_name "emulation_ospfv3_lsa_config"    
    }
    #prepare a fake table for ospf common
    array unset ::sth::ospf::emulation_ospf_lsa_config_stcobj
    array unset ::sth::ospf::emulation_ospf_lsa_config_stcattr
    array unset ::sth::ospf::emulation_ospf_lsa_config_type
    array set ::sth::ospf::emulation_ospf_lsa_config_stcobj [array get $name_space$cmd_name\_stcobj]
    array set ::sth::ospf::emulation_ospf_lsa_config_stcattr [array get $name_space$cmd_name\_stcattr]
    array set ::sth::ospf::emulation_ospf_lsa_config_type [array get $name_space$cmd_name\_type]
    set cmd_name "emulation_ospf_lsa_config"
    
    #find children args#
    ############ospfv2###################
    set index 0
    set lsa_index 0
    foreach ospfconfighandle $ospfconfighandlelist {
        set childList [stc::get $ospfconfighandle -children]
        foreach child $childList {
            set child [string tolower $child]
            set configFlag 0
            set lsa_handle ""
            switch -regexp -- $child {
                asbrsummarylsa {
                    set type asbr_summary
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) AsbrSummaryLsa
                }
                ospfv3interarearouterlsablock {
                    set type asbr_summary
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) Ospfv3InterAreaRouterLsaBlock
                }
                ospfv3asexternallsablock {
                    set type ext_pool
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_type) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_forward_addr) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_metric) "_none_"
		    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_route_category) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) Ospfv3AsExternalLsaBlock
                }
                externallsablock {
                    set type ext_pool
                    set configFlag 1
                    set ext_type [stc::get $child -type]
                    if {$ext_type eq "NSSA"} {
                        set type nssa_ext_pool
                        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_type) "_none_"
                        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_forward_addr) "_none_"
                        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_metric) "_none_"
			set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_route_category) "_none_"
                    } else {
                        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_type) "_none_"
                        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_forward_addr) "_none_"
                        set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_metric) "_none_"
			set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_route_category) "_none_"
                    }
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) ExternalLsaBlock
                    
                }
                ospfv3networklsa {
                    set type network
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) Ospfv3NetworkLsa
                }
                
                networklsa {
                    set type network
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) NetworkLsa
                }
                ospfv3routerlsa {
                    set type router
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) Ospfv3RouterLsa
                }
                routerlsa {
                    set type router
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) RouterLsa
                }
                
                summarylsablock {
                    set type summary_pool
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) SummaryLsaBlock
                }
                ospfv3interareaprefixlsablk {
                    set type summary_pool
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) Ospfv3InterAreaPrefixLsaBlk
                }
                ospfv3intraareaprefixlsablk {
                    set type intra_area_prefix
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) "_none_"
                }
                ospfv3nssalsablock {
                    set type nssa_ext_pool
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_type) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_forward_addr) "_none_"
		    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_route_category) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_metric) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) Ospfv3NssaLsaBlock
                }
                telsa {
                    set type opaque_type_10
                    set configFlag 1
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(adv_router_id) TeLsa
                }
               
            }
            if {$configFlag == 1} {
                append lsa_handle $hlt_ret "_$type$lsa_index"
                set sth::hlapiGen::device_ret($child) $lsa_handle
                set hlapi_script ""
                set args_list ""
                #get the child info into args_list
                set child2List [stc::get $child -children]
                
                if {[regexp -nocase "telsa" $child]} {
                    set instanceId [stc::get $child -Instance]
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(te_instance_id) "_none_"
                }
                if {[regexp -nocase "ospfv3routerlsa" $child]} {
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(router_abr) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(router_asbr) "_none_"
                    set ::sth::ospf::emulation_ospf_lsa_config_stcobj(router_virtual_link_endpt) "_none_"
                    set RouterType [stc::get $child -RouterType]
                    if {[regexp -nocase "BBIT" $RouterType]} {
                        append args_list "			-router_abr			    1\\\n"
                    }
                    if {[regexp -nocase "EBIT" $RouterType]} {
                        append args_list "			-router_asbr			    1\\\n"
                    }
                    if {[regexp -nocase "VBIT" $RouterType]} {
                        append args_list "			-router_virtual_link_endpt			    1\\\n"
                    } 
                }
                
                ::sth::hlapiGen::mask_unused_ipnetworkblock $type $ospfversion
                foreach child2 $child2List {
                    if {[regexp -nocase "ipv4networkblock" $child2] || \
                        [regexp -nocase "linktlv" $child2] || \
                        [regexp -nocase "routertlv" $child2] || \
                        [regexp -nocase "ipv6networkblock" $child2] || \
                        [regexp -nocase "dhcpv6serverprefixpoolconfig" $child2] } {
                        
                        get_attr $child2 $child2
                        foreach child2_obj [array names ::sth::hlapiGen::$child2\_obj] {
                            append args_list [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $child2 $child2 $child2_obj]
                        }
                        
                        if {[regexp -nocase "linktlv" $child2]} {
                            
                            append args_list "			-te_instance_id			    $instanceId\\\n"
                            
                            set Teparams [stc::get $child2 -children-TeParams]
    
                            set SubTlv [stc::get $Teparams -SubTlv]
                            if {$SubTlv ne "0"} {
                                foreach arg "te_local_ip te_remote_ip te_admin_group te_max_bw te_max_resv_bw te_unresv_bw_priority0 
                                            te_unresv_bw_priority1 te_unresv_bw_priority2 te_unresv_bw_priority3
                                            te_unresv_bw_priority4 te_unresv_bw_priority5 te_unresv_bw_priority6 
                                            te_unresv_bw_priority7 " {
                                    set ::sth::ospf::$cmd_name\_stcobj($arg) "_none_"
                                }
                                if {[regexp -nocase "GROUP" $SubTlv]} {
                                    set ::sth::ospf::$cmd_name\_stcobj(te_admin_group) "TeParams"    
                                }
                                if {[regexp -nocase "MAX_BW" $SubTlv]} {
                                    set ::sth::ospf::$cmd_name\_stcobj(te_max_bw) "TeParams"    
                                }
                                if {[regexp -nocase "LOCAL_IP" $SubTlv]} {
                                    set ::sth::ospf::$cmd_name\_stcobj(te_local_ip) "TeParams"    
                                }
                                if {[regexp -nocase "REMOTE_IP" $SubTlv]} {
                                    set ::sth::ospf::$cmd_name\_stcobj(te_remote_ip) "TeParams"    
                                }
                                if {[regexp -nocase "MAX_RSV_BW" $SubTlv]} {
                                    set ::sth::ospf::$cmd_name\_stcobj(te_max_resv_bw) "TeParams"    
                                }
                                if {[regexp -nocase "UNRESERVED" $SubTlv]} {
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority0) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority1) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority2) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority3) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority4) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority5) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority6) "TeParams"
                                    set ::sth::ospf::$cmd_name\_stcobj(te_unresv_bw_priority7) "TeParams" 
                                }
                                get_attr $Teparams $Teparams
                                
                                foreach Teparams_obj [array names ::sth::hlapiGen::$Teparams\_obj] {
                                    append args_list [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $Teparams $Teparams $Teparams_obj]
                                }
                            }
                        }
    
                        #add te_tlv_type
                        if {[regexp -nocase "linktlv" $child2]} {
                            append args_list "			-te_tlv_type			    link\\\n"
                        }
                        if {[regexp -nocase "routertlv" $child2]} {
                            append args_list "			-te_tlv_type			    router\\\n"
                        }
                        
                        #handle the same parameters of ipv4networkblock/ipv6networkblock for ext_pool|summary_pool|nssa_ext_pool
                        
                    }
                }
                ::sth::hlapiGen::unmask_unused_ipnetworkblock $ospfversion
                puts_to_file "set ospf_router$index \"\[lindex \[keylget $hlt_ret handle\] $index\]\" \n\n"
                append hlapi_script "      set $lsa_handle \[sth::$cmd_name\\\n"
                append hlapi_script $args_list
                append hlapi_script "			-type			    $type\\\n"           
                #add itself parameters
                get_attr $child $child
                
                if {[regexp -nocase "externallsablock" $child]} {
                    if {[set sth::hlapiGen::$child\_$child\_attr(-metrictype)] eq "TYPE1"} {
                        set   sth::hlapiGen::$child\_$child\_attr(-metrictype) 1
                    }
                    if {[set sth::hlapiGen::$child\_$child\_attr(-metrictype)] eq "TYPE2"} {
                        set   sth::hlapiGen::$child\_$child\_attr(-metrictype) 2
                    }
                }
                foreach child_obj [array names ::sth::hlapiGen::$child\_obj] {
                    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $child $child $child_obj]
                }
                #convert te_link_type: replace POINT_TO_POINT => ptop
                regsub -all POINT_TO_POINT  $hlapi_script ptop hlapi_script
                # add router handle
                append hlapi_script "			-handle         \$ospf_router$index\\\n"
                array set hlapi_script_link_type {}
                if {[regexp -nocase "routerlsa" $child]} {
                    #handle RouterLsaLink
                    #router_link_data router_link_id router_link_metric router_link_mode router_link_type router_link_count router_link_step
                    if {[regexp -nocase "routerlsalink" [stc::get $child -children]]} {
                        set lsalinkList [stc::get $child -children-routerlsalink]
                        set lsalink0 [lindex $lsalinkList 0]
						set returnValue [isValidlsalinkList $lsalinkList]
                        if { $returnValue == 1} {
                            append hlapi_script "			-router_link_mode         create\\\n"
                            append hlapi_script "			-router_link_data         [stc::get $lsalink0 -LinkData]\\\n"
                            append hlapi_script "			-router_link_id         [stc::get $lsalink0 -LinkId]\\\n"
                            append hlapi_script "			-router_link_metric         [stc::get $lsalink0 -Metric]\\\n"
                            append hlapi_script "			-router_link_count         [llength $lsalinkList]\\\n"
                            switch -- [stc::get $lsalink0 -LinkType] {
                                POINT_TO_POINT {
                                    set iftype ptop
                                }
                                TRANSIT_NETWORK {
                                    set iftype transit
                                }
                                VL {
                                    set iftype virtual
                                }
                                STUB_NETWORK {
                                    set iftype stub
                                }
                                default {
                                    set iftype ptop
                                }
                            }   
                            append hlapi_script "			-router_link_type         $iftype\\\n"
                            if {[llength $lsalinkList] > 1} {
                                set lsalink1 [lindex $lsalinkList 1]
                                set id0 [stc::get $lsalink0 -LinkId]
                                set id1 [stc::get $lsalink1 -LinkId]
                                append hlapi_script "			-router_link_step         [calculate_difference $id0 $id1 ""]\\\n"
                            }
                        } elseif { $returnValue == 0 }  {
							#when LSA link type is different
							append hlapi_script "			-router_link_mode         create\\\n"
                            append hlapi_script "			-router_link_data         [stc::get $lsalink0 -LinkData]\\\n"
                            append hlapi_script "			-router_link_id         [stc::get $lsalink0 -LinkId]\\\n"
                            append hlapi_script "			-router_link_metric         [stc::get $lsalink0 -Metric]\\\n"
                            switch -- [stc::get $lsalink0 -LinkType] {
                                POINT_TO_POINT {
                                    set iftype ptop
                                }
                                TRANSIT_NETWORK {
                                    set iftype transit
                                }
                                VL {
                                    set iftype virtual
                                }
                                STUB_NETWORK {
                                    set iftype stub
                                }
                                default {
                                    set iftype ptop
                                }
                            }   
                            append hlapi_script "			-router_link_type         $iftype\\\n"
							set lsaIdx 0
							foreach lsalink0 $lsalinkList {
								if { [lindex $lsalinkList 0] == $lsalink0 } {
									continue
								}
                                append hlapi_script_link_type($lsaIdx) "      set $lsa_handle\_lsa \[sth::$cmd_name\\\n"
								append hlapi_script_link_type($lsaIdx) "			-type         router\\\n"
								append hlapi_script_link_type($lsaIdx) "			-lsa_handle       \$ospf_lsa_handle\\\n"
								append hlapi_script_link_type($lsaIdx) "			-mode         modify\\\n"
								append hlapi_script_link_type($lsaIdx) "			-router_link_mode         create\\\n"
								append hlapi_script_link_type($lsaIdx) "			-router_link_data         [stc::get $lsalink0 -LinkData]\\\n"
								append hlapi_script_link_type($lsaIdx) "			-router_link_id         [stc::get $lsalink0 -LinkId]\\\n"
								append hlapi_script_link_type($lsaIdx) "			-router_link_metric         [stc::get $lsalink0 -Metric]\\\n"
								switch -- [stc::get $lsalink0 -LinkType] {
									POINT_TO_POINT {
										set iftype ptop
									}
									TRANSIT_NETWORK {
										set iftype transit
									}
									VL {
										set iftype virtual
									}
									STUB_NETWORK {
										set iftype stub
									}
									default {
										set iftype ptop
									}
								}   
								append hlapi_script_link_type($lsaIdx) "			-router_link_type         $iftype\\\n"
								append hlapi_script_link_type($lsaIdx) "\]\n"
								incr lsaIdx
							}	
						} else {
                            unset sth::hlapiGen::device_ret($child)
                        }
                    }
                }
                if {[regexp -nocase "ospfv3routerlsa" $child]} {
                    #handle Ospfv3RouterLsaIf
                    #router_link_data router_link_id router_link_metric router_link_mode router_link_type
                    if {[regexp -nocase "ospfv3routerlsaif" [stc::get $child -children]]} {
                        set lsaif [lindex [stc::get $child -children-ospfv3routerlsaif] 0]
                        append hlapi_script "			-router_link_data         [stc::get $lsaif -IfId]\\\n"
                        append hlapi_script "			-router_link_id         [stc::get $lsaif -NeighborRouterId]\\\n"
                        append hlapi_script "			-router_link_metric         [stc::get $lsaif -Metric]\\\n"
                        append hlapi_script "			-router_link_mode         create\\\n"
                        switch -- [stc::get $lsaif -IfType] {
                            POINT_TO_POINT {
                                set iftype ptop
                            }
                            TRANSIT_NETWORK {
                                set iftype transit
                            }
                            VIRTUAL_LINK {
                                set iftype virtual
                            }
                            default {
                                set iftype ptop
                            }
                        }
                        append hlapi_script "			-router_link_type         $iftype\\\n"
                        
                    }
                }
                append hlapi_script "			-mode         create\\\n"
                append hlapi_script "\]\n"
                #append hlapi_script "puts \$$lsa_handle\n"
                puts_to_file $hlapi_script
                gen_status_info $lsa_handle "sth::$cmd_name"
                incr lsa_index
				if {[array size hlapi_script_link_type] != 0} {
				    puts_to_file "set ospf_lsa_handle \"\[lindex \[keylget $lsa_handle lsa_handle\] 0\]\" \n"
					for {set idx 0} {$idx < $lsaIdx} {incr idx} {
                         puts_to_file $hlapi_script_link_type($idx)
						 gen_status_info $lsa_handle\_lsa "sth::$cmd_name"
                    }
					array unset hlapi_script_link_type
				}
            }
            if {$ospfversion eq "ospfv2"} {
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_type) "ExternalLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_forward_addr) "ExternalLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_metric) "ExternalLsaBlock"
		set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_route_category) "ExternalLsaBlock"

                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_type) "ExternalLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_forward_addr) "ExternalLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_metric) "ExternalLsaBlock"
		set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_route_category) "ExternalLsaBlock"
            }
            if {$ospfversion eq "ospfv3"} {
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_type) "Ospfv3AsExternalLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_forward_addr) "Ospfv3AsExternalLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_metric) "Ospfv3AsExternalLsaBlock"
		set ::sth::ospf::emulation_ospf_lsa_config_stcobj(external_prefix_route_category) "Ospfv3AsExternalLsaBlock"

                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_type) "Ospfv3NssaLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_forward_addr) "Ospfv3NssaLsaBlock"
                set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_metric) "Ospfv3NssaLsaBlock"
		set ::sth::ospf::emulation_ospf_lsa_config_stcobj(nssa_prefix_route_category) "Ospfv3NssaLsaBlock"
            }
        }
        incr index
    }
}
proc ::sth::hlapiGen::handle_topo_route_config {device class mode hlt_ret cfg_args first_time ospfversion} {
    #will add this function later if need
}



proc ::sth::hlapiGen::hlapi_gen_mpls_vpn_pe {class hlt_ret} {
    
    #VRF Provider Link
    variable protocol_to_devices
    set src_dev_list $protocol_to_devices($class)
    array set src_bgp {}
    array set src_ldp {}
    array set l3_bgp {}
    
    foreach src_dev $src_dev_list {
        
        set vrfproviderlink [set sth::hlapiGen::$src_dev\_obj(vrfproviderlink)]
        set dst_dev [set sth::hlapiGen::$src_dev\_$vrfproviderlink\_attr(-linkdstdevice-targets)]
        #need to check which kind of vpn_pe, l2vpn_pe or l3vpn_pe.
        if {[info exists sth::hlapiGen::$src_dev\_obj(mplsl3vpnpetoplink)]} {
            set pe_type l3vpn_pe
        } else {
            set pe_type l2vpn_pe
        }
        if {[regexp "l2vpn_pe" $pe_type]} {
         
            if {[info exists sth::hlapiGen::$src_dev\_obj(bgprouterconfig)]} {
                set src_type "vpls_bgp_session_handle"
                set vpn_type "bgp_vpls"
                set array_name src_bgp
            } else {
                set src_type "targeted_ldp_session_handle"
                set vpn_type "ldp_vpls"
                set array_name src_ldp
            }
        } else {
            set vpn_type l3_pe
            set src_type "bgp_session_handle"
            set array_name l3_bgp
        }
        if {[info exists $array_name\(src_dev)]} {
            set $array_name\(src_dev) [concat [set $array_name\(src_dev)] $src_dev]
        } else {
            set $array_name\(src_dev) $src_dev
            set $array_name\(src_type) $src_type
            set $array_name\(vpn_type) $vpn_type
        }
        if {[info exists $array_name\(dst_dev)]} {
            set $array_name\(dst_dev) [concat [set $array_name\(dst_dev)] $dst_dev]
        } else {
            set $array_name\(dst_dev) $dst_dev
        }
    }
    
    foreach vpn_pe_array "src_bgp src_ldp l3_bgp" {
        if {![info exists $vpn_pe_array\(src_dev)]} {
            continue
        }
        set src_dev_list [set $vpn_pe_array\(src_dev)]
        set dst_dev_list [set $vpn_pe_array\(dst_dev)]
        
        #check if the device in the dst_dev_list same or not, if they are the same, set the enable_p_router to be 1
        #else the dst device count need to be same with the pe_count
        set args_common ""
        if {[regexp "l3_pe" [set $vpn_pe_array\(vpn_type)]]} {
            append args_common  "set $hlt_ret \[sth::emulation_mpls_l3vpn_pe_config\\\n"
            
        } else {
            append args_common  "set $hlt_ret \[sth::emulation_mpls_l2vpn_pe_config\\\n"
            append args_common  "-vpn_type   [set $vpn_pe_array\(vpn_type)]\\\n"
        }
        
        append args_common  "-mode enable\\\n"
        
        array set dst_src_map {}
        set i 0
        foreach dst_dev $dst_dev_list {
            if {[info exists dst_src_map($dst_dev)]} {
                set dst_src_map($dst_dev) [concat [set dst_src_map($dst_dev)] [lindex $src_dev_list $i]]
            } else {
                set dst_src_map($dst_dev) [lindex $src_dev_list $i]   
            }
            
            incr i
        }
        
        
        foreach dst_dev [array names dst_src_map] {
            set args_to_puts ""
            if {[llength [set dst_src_map($dst_dev)]] > 1} {
                #this kind need to set the enable_p_router to be 1
                
                set scr_devs $dst_src_map($dst_dev)
                array set port_src_map {}
                foreach src_dev $scr_devs {
                    set port_handle [set sth::hlapiGen::$src_dev\_$src_dev\_attr(-affiliationport-targets)]
                    if {[info exists port_src_map($port_handle)]} {
                        set port_src_map($port_handle) [concat $port_src_map($port_handle) $src_dev]
                    } else {
                        set port_src_map($port_handle) $src_dev
                    }
                }
                
                foreach port_handle [array names port_src_map] {
                    append args_to_puts $args_common
                    append args_to_puts "-port_handle   $sth::hlapiGen::port_ret($port_handle)\\\n"
                    if {[llength [set port_src_map($port_handle)]] > 1} {
                        append args_to_puts "-enable_p_router        1\\\n"
                    }
                    set pe_count [llength [set port_src_map($port_handle)]]
                    append args_to_puts "-pe_count       $pe_count\\\n"
                    set src_dev [set dst_src_map($dst_dev)]
                    set dev_def ""
                    append dev_def "[get_device_created $dst_devs mpls_session_handle handle]"
                    append dev_def "[get_device_created $dst_devs igp_session_handle handle]"
                    append dev_def "[get_device_created $src_devs [set $vpn_pe_array\(src_type)] handle]"
                    append args_to_puts "-[set $vpn_pe_array\(src_type)]        \$[set $vpn_pe_array\(src_type)]\\\n"
                    append args_to_puts "-mpls_session_handle        \$mpls_session_handle\\\n"
                    append args_to_puts "-igp_session_handle        \$igp_session_handle\\\n"
                    append args_to_puts "\]\n"
                    
                    puts_to_file $dev_def 
                    puts_to_file $args_to_puts   
                    unset dst_src_map($dst_dev)
                }
                
            }
        }
        set args_to_puts ""
        if {[info exists dst_src_map]} {
            array set port_src_map {}
            foreach dst_dev [array names dst_src_map] {
                set src_dev $dst_src_map($dst_dev)
                set port_handle [set sth::hlapiGen::$src_dev\_$src_dev\_attr(-affiliationport-targets)]
                if {[info exists port_src_map($port_handle)]} {
                    set port_src_map($port_handle) [concat $port_src_map($port_handle) $src_dev]
                } else {
                    set port_src_map($port_handle) $src_dev
                }
            }
            foreach port_handle [array names port_src_map] {
                set pe_count [llength $port_src_map($port_handle)]
                append args_to_puts $args_common
                append args_to_puts "-port_handle   $sth::hlapiGen::port_ret($port_handle)\\\n"
                append args_to_puts "-pe_count       $pe_count\\\n"
                set src_devs $port_src_map($port_handle)
                set dst_devs ""
                set dst_src_list [array get dst_src_map]
                foreach src_dev $src_devs {
                    set dst_dev [lindex $dst_src_list [expr {[lsearch $dst_src_list $src_dev] - 1}]]
                    set dst_devs [concat $dst_devs $dst_dev]
                }
                set dev_def ""
                append dev_def "[get_device_created $dst_devs mpls_session_handle handle]"
                append dev_def "[get_device_created $dst_devs igp_session_handle handle]"
                append dev_def "[get_device_created $src_devs [set $vpn_pe_array\(src_type)] handle]"
                
                append args_to_puts "-[set $vpn_pe_array\(src_type)]        \$[set $vpn_pe_array\(src_type)]\\\n"
                append args_to_puts "-mpls_session_handle        \$mpls_session_handle\\\n"
                append args_to_puts "-igp_session_handle        \$igp_session_handle\\\n"
                append args_to_puts "\]\n"
                puts_to_file $dev_def 
                puts_to_file $args_to_puts
                if {[regexp "l3_pe" [set $vpn_pe_array\(vpn_type)]]} {
                    gen_status_info $hlt_ret "sth::emulation_mpls_l3vpn_pe_config"
                } else {
                    gen_status_info $hlt_ret "sth::emulation_mpls_l2vpn_pe_config"
                }
            }
            
        }
        
        
    }
}



proc ::sth::hlapiGen::hlapi_gen_device_mpls_vpn_site {device class mode hlt_ret cfg_args first_time} {
    variable devicelist_obj
    set dev_def ""
    set site_count 1
    set first_time 1
    #check the cfg_args, if there is the site_count.
    if {[lsearch $cfg_args "\-site_count"] > -1} {
        set cfg_list [split $cfg_args \\]
        foreach cfg_arg $cfg_list {
            if {[regexp "site_count" $cfg_arg]} {
                set site_count [lindex $cfg_arg 1]
                break
            }
        }
    }
    set obj_handle [set sth::hlapiGen::$device\_$device\_attr(-memberofvpnsite-targets)]
    if {$::sth::hlapiGen::scaling_test && $first_time} {
        set obj_list $devicelist_obj($obj_handle)
    } else {
        set obj_list $obj_handle
    }
    get_attr $obj_handle $obj_handle
    #vpnsiteinforfc2547
    if {[regexp "vpnsiteinforfc2547" $class]} {
        #this is l3vpn_site
        
        set dst_dev_list ""
        foreach obj $obj_list {
            set dev [stc::get $obj -memberofvpnsite-sources]
            if {[info exists sth::hlapiGen::$dev\_obj(l3forwardinglink)]} {
                set l3forwardinglink [set sth::hlapiGen::$dev\_obj(l3forwardinglink)]
                set dst_dev [set sth::hlapiGen::$dev\_$l3forwardinglink\_attr(-linkdstdevice-targets)]
                set dst_dev_list [concat $dst_dev_list $dst_dev]
            }
        }
        #check if the ce_session_handle is needed, check if there is L3 Forwarding Link
        
        if {[llength $dst_dev_list] != 0} {
            set dev_def [get_device_created $dst_dev_list ce_session_handle handle]
            append cfg_args "-ce_session_handle     \$ce_session_handle\\\n"
            if {[llength $dst_dev_list] != $site_count} {
                append dev_def "\#WARN: ce_session_handle number need to be the same with site_count\n"
            }
        }
        
    }
    
    set dst_dev_list ""
    foreach obj $obj_list {
        set dev [stc::get $obj -memberofvpnsite-sources]
        if {[info exists sth::hlapiGen::$dev\_obj(vrfcustomerlink)]} {
            set vrfcustomerlink [set sth::hlapiGen::$dev\_obj(vrfcustomerlink)]
            set dst_dev [set sth::hlapiGen::$dev\_$vrfcustomerlink\_attr(-linkdstdevice-targets)]
            set dst_dev_list [concat $dst_dev_list $dst_dev]
            #check if the pe_handle is needed, check if there is VRF Customer Link
        }
    }
    if {[llength $dst_dev_list] != 0} {
        append dev_def [get_device_created $dst_dev_list pe_handle handle]
        append cfg_args "-pe_handle     \$pe_handle\\\n"
        if {[llength $dst_dev_list] != $site_count} {
            append dev_def "\#WARN: pe_handle number need to be the same with site_count\n"    
        }
    }
    #prpcess the vpn_id all kind of the site can use the vpn id, this id will not take real effect to the STC,
    #not configured to STC, just used as a index,
    #get all the vpnidgroup from the project
    set project [stc::get $obj_handle -parent]
    set vpnidgroups [stc::get $project -children-vpnidgroup]
    if {[info exists vpn_id_array]} {
        array unset vpn_id_array
        array set vpn_id_array {}
    }
    set i 100
    foreach vpnidgroup $vpnidgroups {
        set vpn_id_array($vpnidgroup) $i
        incr i
    }
    if {[info exists sth::hlapiGen::$obj_handle\_$obj_handle\_attr(-memberofvpnidgroup-sources)]} {
        set vpnidgroup [set sth::hlapiGen::$obj_handle\_$obj_handle\_attr(-memberofvpnidgroup-sources)]
        set vpn_id [set vpn_id_array($vpnidgroup)]
        append cfg_args "-vpn_id            $vpn_id\\\n"
    }
    set vpnidgroup
    if {[llength $dst_dev_list] == 0 && [regexp "vpnsiteinfovplsldp" $class]} {
        #when there is no pe_handle and the type is ldp_vpls,the emulation_vpls_site_config can do the same thing
        #here will call  the sth::emulation_vpls_site_config instead of the emulation_mpls_l2vpn_site_config
        hlapi_gen_device_vpls_site $device $class $mode $hlt_ret $cfg_args $first_time
        
    } else {
        if {[regexp "vpnsiteinfovplsldp" $class]} {
            set vpn_type "ldp_vpls"
            append cfg_args "-vpn_type  $vpn_type\\\n"
        } elseif {[regexp "vpnsiteinfovplsbgp" $class]} {
            set vpn_type "bgp_vpls"
            append cfg_args "-vpn_type  $vpn_type\\\n"
        }
        
        set table_name $sth::hlapiGen::hlapi_gen_tableName($class)
        ::sth::sthCore::InitTableFromTCLList [set $table_name]
        set name_space [string range $table_name 0 [string last : $table_name]]
        set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
        
        foreach arg "pe_loopback_ip_addr pe_loopback_ip_prefix" {
            set $name_space$cmd_name\_stcobj($arg) $class
        }
        append cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $obj_handle $obj_handle $class]
        puts_to_file $dev_def
        hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    }
}


proc ::sth::hlapiGen::hlapi_gen_device_vpls_site {device class mode hlt_ret cfg_args first_time} {
    set dev_def ""
    set table_name "::sth::Vpls::VplsTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space "::sth::Vpls::"
    set cmd_name "emulation_vpls_site_config"
    variable devicelist_obj
    #set hltapi_script ""
    #append hltapi_script "set $hlt_ret \[sth::emulation_vpls_site_config\\\n"
    #append hltapi_script "-mode     creaet"
    set obj_handle [set sth::hlapiGen::$device\_$device\_attr(-memberofvpnsite-targets)]
    if {$::sth::hlapiGen::scaling_test && $first_time} {
        set obj_list $devicelist_obj($obj_handle)
    } else {
        set obj_list $obj_handle
    }
    get_attr $obj_handle project1
    #check if we need the pe_handle's routerid and 32 or attached_dut_ip_addr and attached_dut_ip_prefix as the PeIpv4Addr and PeIpv4PrefixLength
    #need to check all the device with ldprouter, then check if the routerid is the same with the peipv4addr
    if {[info exists ::sth::hlapiGen::protocol_to_devices(ldprouterconfig)] || [info exists ::sth::hlapiGen::protocol_to_devices(ldprouterconfig_pe)]} {
        set ldprouter_list ""
        if {[info exists ::sth::hlapiGen::protocol_to_devices(ldprouterconfig)]} {
            set ldprouter_list [concat $ldprouter_list $::sth::hlapiGen::protocol_to_devices(ldprouterconfig)]
        }
        if {[info exists ::sth::hlapiGen::protocol_to_devices(ldprouterconfig_pe)]} {
            set ldprouter_list [concat $ldprouter_list $::sth::hlapiGen::protocol_to_devices(ldprouterconfig_pe)]
        }
        foreach ldprouter $ldprouter_list {
            set ldprouterconfig [set ::sth::hlapiGen::$ldprouter\_obj(ldprouterconfig)]
            if {[info exists ::sth::hlapiGen::$ldprouterconfig\_obj(vclsp)]} {
                #here this router may be the pe_handle, check the rotuer id
                set router_id [stc::get $ldprouter -RouterId]
                set pe_ipaddr [set ::sth::hlapiGen::project1_$obj_handle\_attr(-peipv4addr)]
                if {$router_id == $pe_ipaddr} {
                    #this is the pe_handle
                    append dev_def [get_device_created $ldprouter pe_handle handle]
                    append cfg_args "-pe_handle     \$pe_handle\\\n"
                    #vc_type
                    #4 LDP_LSP_ENCAP_ETHERNET_VLAN 5 LDP_LSP_ENCAP_ETHERNET B LDP_LSP_ENCAP_ETHERNET_VPLS
                    set vclsp [set ::sth::hlapiGen::$ldprouterconfig\_obj(vclsp)]
                    set vc_type [set ::sth::hlapiGen::$ldprouterconfig\_$vclsp\_attr(-encap)]
                    switch -regexp -- [string toupper $vc_type] {
                        ^LDP_LSP_ENCAP_ETHERNET_VLAN$ {
                            set vc_type 4
                        }
                        ^LDP_LSP_ENCAP_ETHERNET$ {
                            set vc_type 5
                        }
                        ^LDP_LSP_ENCAP_ETHERNET_VPLS$ {
                            set vc_type B
                        }
                        default {
                            set vc_type 4
                        }
                    }
                    append cfg_args "-vc_type     $vc_type\\\n"
                    set mtu [set ::sth::hlapiGen::$ldprouterconfig\_$vclsp\_attr(-ifmtu)]
                    append cfg_args "-mtu     $mtu\\\n"
                    break
                }
            }
        }
    }
    if {![regexp {\-pe_handle} $cfg_args]} {
        #if no pe_handle need to input the attached_dut_ip_addr and the attached_dut_ip_prefix
        set attached_dut_ip_addr [set ::sth::hlapiGen::project1_$obj_handle\_attr(-peipv4addr)]
        set attached_dut_ip_prefix [set ::sth::hlapiGen::project1_$obj_handle\_attr(-peipv4prefixlength)]
        append cfg_args "-attached_dut_ip_addr      $attached_dut_ip_addr\\\n"
        append cfg_args "-attached_dut_ip_prefix    $attached_dut_ip_prefix\\\n"
    }
    #vc_id    
    set vc_id [set ::sth::hlapiGen::project1_$obj_handle\_attr(-startvcid)]
    append cfg_args "-vc_id    $vc_id\\\n"
    puts_to_file $dev_def
    set class "vpnsiteinfovplsldp_other"
    hlapi_gen_device_basic $device $class "" $hlt_ret $cfg_args $first_time
    
}


proc ::sth::hlapiGen::hlapi_gen_device_vpls_pe {device class mode hlt_ret cfg_args first_time} {
    hlapi_gen_device_basic $device $class "" $hlt_ret $cfg_args $first_time
    
}
#***********************************************************************************************************<-#

proc ::sth::hlapiGen::multi_dev_check_func_ospf {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]
                    
    set attrlist "AreaId"
    foreach obj $update_obj {
        #call update-step to update the step value of bgprouterconfig obj
        if {[info exists devicelist_obj($obj)]} {
            update_step $class $devicelist_obj($obj) $attrlist ""
        }
    }   
    return $update_obj
}

proc ::sth::hlapiGen::multi_dev_check_func_vpn_site {class devices} {
    upvar cfg_args cfg_args_local
    set update_obj ""
    variable devicelist_obj
    #set obj_list ""
    
    foreach device $devices {
        set obj [stc::get $device -memberofvpnsite-targets]
        if {![regexp "^$" $obj] && [regexp $class $obj]} {
            #set obj_list [concat $obj_list $obj]
            set port [stc::get $device -affiliationport-Targets]
            if {[info exists obj_list($port)]} {
                set obj_list($port) [concat $obj_list($port) $obj]
            } else {
                array set obj_list "$port $obj"
            }
        }
    }
    foreach port_hdl [lsort [array names obj_list]] {
        set count [llength $obj_list($port_hdl)]
        set obj [lindex $obj_list($port_hdl) 0]
        append cfg_args_local($obj) "-site_count     $count\\\n"
        if {$count > 1} {
            
            set obj2 [lindex $obj_list($port_hdl) 1]
            #calculate the pe_loopback_ip_step
            set pe_loopback_ip1 [stc::get $obj -PeIpv4Addr]
            set pe_loopback_ip2 [stc::get $obj -PeIpv4Addr]
            set pe_loopback_ip_step [calculate_difference $pe_loopback_ip1 $pe_loopback_ip2 ipv4]
            append cfg_args_local($obj) "-pe_loopback_ip_step     $pe_loopback_ip_step\\\n"
            #calculate the rd_step, for the l3vpn_site
            if {[regexp vpnsiteinforfc2547 $class]} {
                set rd_start1 [stc::get $obj -RouteDistinguisher]
                set rd_start1_header [lindex [split $rd_start1 :] 0]
                set rd_start1_tail [lindex [split $rd_start1 :] 1]
                
                set rd_start2 [stc::get $obj2 -RouteDistinguisher]
                set rd_start2_header [lindex [split $rd_start2 :] 0]
                set rd_start2_tail [lindex [split $rd_start2 :] 1]
                
                set rd_header_step [calculate_difference $rd_start1_header $rd_start1_header ""]
                set rd_tail_step [calculate_difference $rd_start1_tail $rd_start2_tail ""]
                set rd_step [join "$rd_header_step $rd_tail_step" :]
                append cfg_args_local($obj) "-rd_step     $rd_step\\\n"
                
                #interface_ip_step
                set host1 [stc::get $obj -memberofvpnsite-sources]
                set host2 [stc::get $obj2 -memberofvpnsite-sources]
                set ipv4if1 [set sth::hlapiGen::$host1\_obj(ipv4if)]
                set ipv4if2 [set sth::hlapiGen::$host2\_obj(ipv4if)]
                set interface_ip_addr1 [set sth::hlapiGen::$host1\_$ipv4if1\_attr(-address)]
                set interface_ip_addr2 [set sth::hlapiGen::$host2\_$ipv4if2\_attr(-address)]
                set interface_ip_step [calculate_difference $interface_ip_addr1 $interface_ip_addr2 ""]
                append cfg_args_local($obj) "-interface_ip_step     $interface_ip_step\\\n"
            }
        }
        set devicelist_obj($obj) $obj_list($port_hdl)
        set update_obj [concat $update_obj $obj]
    }
    return $update_obj
}
