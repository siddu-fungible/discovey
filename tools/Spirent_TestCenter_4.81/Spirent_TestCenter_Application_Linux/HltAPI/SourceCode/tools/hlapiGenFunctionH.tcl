namespace eval ::sth::hlapiGen:: {

}

#--------------------------------------------------------------------------------------------------------#
#igmp host config convert function, it is used to generate the hltapi emulation_igmp_config function
#emulation_igmp_group_config and emulation_multicast_group_config and emulation_multicast_source_config
#input:     device      =>  the port on which the interface config function will be used
#           calss       =>  the class name
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#           cfg_args    => the args prepared earlier for the bgp config function
#           first_time  => is this the first time to config the protocol on this device
#output:    the genrated hltapi interface_config funtion will be output to the file.
proc ::sth::hlapiGen::hlapi_gen_device_igmpconfig {device class mode hlt_ret cfg_args first_time} {
    set mode create
    #config the igmp host
    set devices $device
    if {$::sth::hlapiGen::scaling_test} {
        set igmp_obj [set sth::hlapiGen::$device\_obj($class)]
        set devices [set sth::hlapiGen::devicelist_obj($igmp_obj)]
        #for the scaling need to also update the attr in the table
        ::sth::sthCore::InitTableFromTCLList $::sth::igmp::igmpTable
        set name_space "::sth::igmp::"
        set cmd_name "emulation_igmp_config"
        
        if {[llength $devices] > 1} {
            set $name_space$cmd_name\_stcattr(count) "count"
            set $name_space$cmd_name\_stcattr(neighbor_intf_ip_addr_step) "gateway.step"
            set $name_space$cmd_name\_stcattr(intf_ip_addr_step) "address.step"
            
            set arg_list " vlan_id_outer_step vlan_id_step"
            foreach arg $arg_list {
                set $name_space$cmd_name\_stcattr($arg) "vlanid.step"
            }
            set arg_list "vlan_id_count vlan_id_outer_count"
            foreach arg $arg_list {
                set $name_space$cmd_name\_stcattr($arg) "vlanid.count"
            }
            set arg_list "vlan_id_mode vlan_id_outer_mode" 
            foreach arg $arg_list {
                set $name_space$cmd_name\_stcattr($arg) "vlanid.mode"
            }
        } else {
            if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {
                set vlanifs [set sth::hlapiGen::$device\_obj(vlanif)]
                set arg_list "vlan_id_count vlan_id_outer_count vlan_id_outer_step vlan_id_step vlan_id_mode vlan_id_outer_mode "
                foreach arg $arg_list {
                    set $name_space$cmd_name\_stcattr($arg) "_none_"
                }
            }
        }
        
    }
    
    ::sth::hlapiGen::igmp_host_pre_process $cfg_args $device
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
    #create and config the igmpv4group
    #determie the related igmpgroup related to this device
    set cfg_ret [lindex $::sth::hlapiGen::device_ret($device) 0]
    #set igmpv4_groups [stc::get project1 -children-ipv4group]
    variable $device\_obj
    set object_handle [set $device\_obj($class)]
    variable $device\_$object_handle\_attr
    set j 0
    set hltapi_config ""
    set group_pool_handle ""
    set source_pool_handle ""
    foreach obj_child [array names sth::hlapiGen::$object_handle\_obj] {
        if {[regexp -nocase {IgmpGroupMembership} $obj_child]} {
            foreach igmp_group_membership [set sth::hlapiGen::$object_handle\_obj($obj_child)] {
                incr j
                set version [set sth::hlapiGen::$device\_$object_handle\_attr(-version)]
                set user_defined_src [set sth::hlapiGen::$object_handle\_$igmp_group_membership\_attr(-userdefinedsources)]
                set igmpv4_group [set sth::hlapiGen::$object_handle\_$igmp_group_membership\_attr(-subscribedgroups-targets)]

                if {[info exists sth::hlapiGen::device_ret($igmpv4_group)]} {
                    set group_ret [lindex $sth::hlapiGen::device_ret($igmpv4_group) 0]
                    set group_pool_handle [concat $group_pool_handle "\[keylget $group_ret handle\]"]
			        # fix US34278, one device add more than one multicast_group will throw an error in IGMPv3:
                    # add array to mapping between igmp_group_member_ship and multicast_group 
                    set mappingMcastGroup($igmp_group_membership) $group_ret
                    set McastGroupTemp $mappingMcastGroup($igmp_group_membership)
                    ##only when it is ture we need to config the source, the source is always together with group
                    #if {[regexp -nocase {true} $user_defined_src] && [regexp -nocase {v3} $version]} {
                    #    set src_ret [lindex $sth::hlapiGen::device_ret($igmpv4_group) 1]
                    #    set source_pool_handle [concat $source_pool_handle "\[keylget $src_ret handle\]"]
                    #}
                } else {
                    if {![info exists sth::hlapiGen::device_ret($igmpv4_group)]} {
                        sth::hlapiGen::get_attr $igmpv4_group $igmpv4_group
                        hlapi_gen_device_basic $igmpv4_group ipv4group create $hlt_ret\_macstgroup_$j "" 1
                        set sth::hlapiGen::device_ret($igmpv4_group) $hlt_ret\_macstgroup_$j
                        set group_pool_handle [concat $group_pool_handle "\[keylget $hlt_ret\_macstgroup_$j handle\]"]
			            # fix US34278, one device add more than one multicast_group will throw an error in IGMPv3:
                        # add array to mapping between igmp_group_member_ship and multicast_group 
                        set mappingMcastGroup($igmp_group_membership) $hlt_ret\_macstgroup_$j
			            set McastGroupTemp $mappingMcastGroup($igmp_group_membership)
            
                      } else {
                        set group_pool_handle [concat $group_pool_handle "\[keylget [set sth::hlapiGen::device_ret($igmpv4_group)] handle\]"]
                    } 
                }
                set is_source_list [stc::get $igmp_group_membership -IsSourceList]
                if { [regexp -nocase {true} $user_defined_src] && [regexp -nocase {v3} $version] && [regexp -nocase {false} $is_source_list] } {
                    #need to check if the multicast source is the same with the earlier one
                    set ipv4networkblock [set sth::hlapiGen::$igmp_group_membership\_obj(ipv4networkblock)]
                    set macstsource_args ""
                    set igmp_src_attr_value ""
                    append macstsource_args "set $hlt_ret\_macstsource_$j \[sth::emulation_multicast_source_config\\\n"
                    append macstsource_args "-mode      create\\\n"
                    set ip_addr_start [lindex [set sth::hlapiGen::$igmp_group_membership\_$ipv4networkblock\_attr(-startiplist)] 0]
                    set ip_addr_step [set sth::hlapiGen::$igmp_group_membership\_$ipv4networkblock\_attr(-addrincrement)]
                    set ip_prefix_len [set sth::hlapiGen::$igmp_group_membership\_$ipv4networkblock\_attr(-prefixlength)]
                    set num_sources [set sth::hlapiGen::$igmp_group_membership\_$ipv4networkblock\_attr(-networkcount)]
                    foreach arg "ip_addr_start ip_prefix_len ip_addr_step num_sources" {
                        append macstsource_args "-$arg      [set $arg]\\\n"
                        set igmp_src_attr_value [join "$igmp_src_attr_value [set $arg]" "_"]
                    } 
                    append macstsource_args "\]\n"
                    if {[info exists ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value)]} {
                        set igmp_src_ret [lindex [set sth::hlapiGen::device_ret([set ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value)])] 0]
                        set mappingMcastSrc($hlt_ret\_macstgroup_$j) $igmp_src_ret
                        
                    } else {
                        puts_to_file $macstsource_args
                        gen_status_info $hlt_ret\_macstsource_$j "sth::emulation_multicast_source_config"
                        set igmp_src_ret $hlt_ret\_macstsource_$j
                        set ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value) $ipv4networkblock
                    }
                    set sth::hlapiGen::device_ret($ipv4networkblock) "$igmp_src_ret 0"
                    #append dev_def [get_device_created $ipv4networkblock source_pool_handle handle]
                    set source_pool_handle [concat $source_pool_handle "\[keylget $igmp_src_ret handle\]"]
		            #add array to mapping between multicast_group and multicast_src
                    set mappingMcastSrc($McastGroupTemp) $igmp_src_ret
                }
                unset_data_model_attr $igmpv4_group
            }
        }
    }
    
    #create and configure the multicast group to the igmp host
    if {![regexp "^$" $group_pool_handle]} {
        #only when there is group the emulation_igmp_group_config will be called
        if {[llength $devices] > 1} {
            set devices [update_device_handle $device igmphostconfig 1]
            puts_to_file  [get_device_created_scaling $devices igmp_session handle]
        } else {
            puts_to_file  [get_device_created $device igmp_session handle]
        }
        # fix US34278, one device add more than one multicast_group will throw an error in IGMPv3:
        #  add "source filter"  and "starting source ip"
            set groupconfignum 0
            set retnum 0
            set igmphostconfig [set ::sth::hlapiGen::$device\_obj(igmphostconfig)] 
            set igmp_group_membership_list [set ::sth::hlapiGen::$igmphostconfig\_obj(igmpgroupmembership)]
            foreach igmp_group_membership $igmp_group_membership_list {
                set subscribedgroupsTargets ""
                incr groupconfignum
                set hltapi_config ""
                incr retnum
                set igmpgroup $mappingMcastGroup($igmp_group_membership)
                set group_pool_handle $igmpgroup
                set device_group_mapping [stc::get $igmp_group_membership -DeviceGroupMapping]
                puts_to_file "set macstgroup \[keylget $group_pool_handle handle\] \n"
                append hltapi_config "set $hlt_ret\_group_config$groupconfignum \[sth::emulation_igmp_group_config\\\n"
                append hltapi_config "              -session_handle         \$igmp_session\\\n"
                append hltapi_config "              -mode                   create\\\n"
                append hltapi_config "              -group_pool_handle      \$macstgroup\\\n"
                append hltapi_config "              -device_group_mapping   $device_group_mapping\\\n"
        if {[regexp -nocase {v3} $version]} {
            set objset ""
                set filter_mode [stc::get $igmp_group_membership -filtermode]
                set user_defined_source [stc::get $igmp_group_membership -UserDefinedSources]
                set is_source_list [stc::get $igmp_group_membership -IsSourceList]
                set ipv4_network_block [stc::get $igmp_group_membership -children-ipv4networkblock]
                set start_ip_list [stc::get $ipv4_network_block -StartIpList]
                set subscribedgroupsTargets [stc::get $igmp_group_membership -subscribedsources-targets]
                append hltapi_config "              -filter_mode             $filter_mode\\\n"
                if {[regexp -nocase "true" $user_defined_source]} {
                    append hltapi_config "              -enable_user_defined_sources            1\\\n"
                    if {[regexp -nocase "false" $is_source_list] } {
                        append hltapi_config "              -specify_sources_as_list            0\\\n"
                        if {![regexp "^$" $source_pool_handle]} { 
                            if { [info exists mappingMcastSrc($igmpgroup)]} {
                                set source_pool_handle $mappingMcastSrc($igmpgroup)
                                puts_to_file "set macstsource \[keylget $source_pool_handle handle\] \n\n"
                                append hltapi_config "              -source_pool_handle     \$macstsource\\\n"    
                            }
                        }
                    } elseif {[regexp -nocase "true" $is_source_list]} {
                        append hltapi_config "              -specify_sources_as_list            1\\\n"
                        append hltapi_config "              -ip_addr_list                       \"$start_ip_list\"\\\n"              
                    }
                } else {
                        append hltapi_config "              -enable_user_defined_sources        0\\\n"
                        append hltapi_config "              -specify_sources_as_list            0\\\n"
                        # support  source  filter in igmpv3 
                        if {[llength $subscribedgroupsTargets] > 0} {
                            if {[info exists sth::hlapiGen::device_ret($subscribedgroupsTargets)]} {
                                puts_to_file  [get_device_created $subscribedgroupsTargets sourcefilterdevice handle]
                                append hltapi_config "              -source_filters                 \$sourcefilterdevice\\\n" 
                            } else {
                                #  create source filter device.
                                sth::hlapiGen::get_attr $subscribedgroupsTargets $subscribedgroupsTargets
                                set gethltobj [::sth::hlapiGen::get_objs $subscribedgroupsTargets]
                                set lengthobj [llength $gethltobj]
                                set objclass [lindex $gethltobj [expr $lengthobj-2]]
                                set objt [lindex $gethltobj [expr $lengthobj-1]]
                                set cfg_convert_func $::sth::hlapiGen::hlapi_gen_cfgConvertFunc($objclass)
                                set cfg_func "::sth::[set ::sth::hlapiGen::hlapi_gen_cfgFunc($objclass)]"
                                hlapi_gen_device_$cfg_convert_func $subscribedgroupsTargets $objclass create $hlt_ret\_source\_filter\_$retnum "" 1
                                set sth::hlapiGen::device_ret($subscribedgroupsTargets) $hlt_ret\_source\_filter\_$retnum
                                set sth::hlapiGen::protocol_to_devices($objt) $subscribedgroupsTargets
                                unset_table_obj_attr $objclass 
                                puts_to_file  [get_device_created $subscribedgroupsTargets sourcefilterdevice handle]
                                append hltapi_config "              -source_filters                 \$sourcefilterdevice\\\n" 
                            }                       
                        }
                }
        }
        append hltapi_config "\]\n"
        puts_to_file $hltapi_config
        set sth::hlapiGen::device_ret($igmp_group_membership) $hlt_ret\_group_config$groupconfignum
        gen_status_info $hlt_ret\_group_config$groupconfignum sth::emulation_igmp_group_config
                }  
    }
}



proc ::sth::hlapiGen::igmp_host_pre_process {cfg_args device} {
    
    upvar cfg_args cfg_args_local

    set igmphostconfig [set ::sth::hlapiGen::$device\_obj(igmphostconfig)]
    #pre-process filter_mode
 # fix US34278 ,one device add more than one multicast_group will throw an error in IGMPv3:   
 #   if {[info exists ::sth::hlapiGen::$igmphostconfig\_obj(igmpgroupmembership)] && [regexp -nocase "v3" [set ::sth::hlapiGen::$device\_$igmphostconfig\_attr(-version)]]} {
 #       set igmp_group_membership [set ::sth::hlapiGen::$igmphostconfig\_obj(igmpgroupmembership)]
 #       set filter_mode [string tolower [set ::sth::hlapiGen::$igmphostconfig\_$igmp_group_membership\_attr(-filtermode)]]
 #       append cfg_args_local "     -filter_mode   $filter_mode\\\n"
 #   }
    #general_query  always be true, no need to configure it
    #group_query    always be true, no need to configure it
    #ip_router_alert always be true, no need to configure it
    #max_response_control always be fasle, no need to configure it
    #suppress_report always be true, no need to configure it
    #max_groups_per_pkts, not supported in the hltapi
    
    #vlan_id_mode
    #vlan_id_outer_mode
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        if {[llength $vlanifs] <= 2} {
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
                        append cfg_args_local "     -vlan_id_outer_mode    $vlan_mode\\\n"
                    } else {
                        append cfg_args_local "     -vlan_id_mode    $vlan_mode\\\n"
                    }
                } else {
                    append cfg_args_local "     -vlan_id_mode    $vlan_mode\\\n"
                }
            }
        }
        
    }
    #qinq_incr_mode
    #currently don't support this arg
}



#--------------------------------------------------------------------------------------------------------#
#isis config convert function, it is used to generate the hltapi emulation_isis_config function
#input:     device      =>  the port on which the interface config function will be used
#           calss       =>  the class name
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#           cfg_args    => the args prepared earlier for the bgp config function
#           first_time  => is this the first time to config the protocol on this device
#output:    the genrated hltapi interface_config funtion will be output to the file.
proc ::sth::hlapiGen::hlapi_gen_device_isisconfig {device class mode hlt_ret cfg_args first_time} {
    #config isis router
    #pre-process the options under IsisLspConfig, TeParams IsisAuthenticationParams
    
    isis_router_pre_process $cfg_args $device
    
    hlapi_gen_device_basic $device $class enable $hlt_ret $cfg_args $first_time
    set hltapi_config ""
    #config the isis routes under the router
    
    set lsp_mode "create"
    #get all the routes handles
    set cfg_ret [lindex $::sth::hlapiGen::device_ret($device) 0]
    set devices ""
    foreach dev [array names ::sth::hlapiGen::device_ret] {
        set ret [lindex $::sth::hlapiGen::device_ret($dev) 0]
        if {[regexp $cfg_ret $ret]} {
            lappend devices $dev
        }
    }
    #curentlly will not support the emulation_isis_topology_route_config, just leave this part of function here
    #incase later will support it.
#   set j 1
#   set name_space "::sth::IsIs::"
#   set cmd_name "emulation_isis_topology_route_config"
#    foreach device $devices {
#        set route_cfg_args ""
#        set route_types ""
#        set device_var [lindex [set ::sth::hlapiGen::device_ret($device)] 0]
#        set device_handle_indx [lindex [set ::sth::hlapiGen::device_ret($device)] 1]
#        
#        
#        variable $device\_obj
#        set isis_config_handle [set $device\_obj($class)]
#        variable $isis_config_handle\_obj
#        if {[info exists ::sth::hlapiGen::$isis_config_handle\_obj(isislspconfig)]} {
#            set lsp_handles [set ::sth::hlapiGen::$isis_config_handle\_obj(isislspconfig)]
#        }
#        foreach lsp_handle $lsp_handles {
#            set lsp_cfg_args ""
#            set hlt_ret_lsp $hlt_ret\_lsp$j
#            append lsp_cfg_args "      set $hlt_ret_lsp \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc(isislspconfig)\\\n"
#            append lsp_cfg_args "                       -handle                     \[lindex \[keylget $device_var handle\] $device_handle_indx\]\\\n"
#            append lsp_cfg_args "			-mode			    $mode\\\n"
#            isis_route_pre_process $lsp_cfg_args $lsp_handle 
#            set sth::hlapiGen::device_ret($lsp_handle) $hlt_ret_lsp
#            #for the obj IsisLspNeighborConfig, TeParams can not be configured in the
#            #basic function, since they are not under the BgpRouterConfig
#            if {[info exists ::sth::hlapiGen::$lsp_handle\_obj(isislspneighborconfig)]} {
#                set isis_lsp_neighbor [set ::sth::hlapiGen::$lsp_handle\_obj(isislspneighborconfig)]
#                append lsp_cfg_args "   -link_narrow_metric     [set ::sth::hlapiGen::$lsp_handle\_$isis_lsp_neighbor\_attr(-metric)]\\\n"
#                set te_param [set ::sth::hlapiGen::$isis_lsp_neighbor\_obj(teparams)]
#                append lsp_cfg_args [config_obj_attr $name_space $cmd_name $isis_lsp_neighbor $te_param teparams]
#            }
#            append lsp_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $isis_config_handle $lsp_handle isislspconfig]
#            append lsp_cfg_args "\]\n"
#            append lsp_cfg_args "puts \$$hlt_ret_lsp\n"
#            puts_to_file $lsp_cfg_args
#                    
#            incr j
#        }
#    }
    #puts_to_file $hlapi_script
}


proc ::sth::hlapiGen::isis_router_pre_process {cfg_args device} {
    upvar cfg_args cfg_args_local
    #pre-process the tunnel handle, to config this, need to call the gre config function
    if {[info exists ::sth::hlapiGen::$device\_obj(greif)]} {
        
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args_local
        append cfg_args_local "                       -tunnel_handle              \$gre_ret\\\n"
    }
    
    
    
    #pre-process the options under IsisLspConfig, TeParams IsisAuthenticationParams
    set isisrouter [set ::sth::hlapiGen::$device\_obj(isisrouterconfig)]
    ::sth::sthCore::InitTableFromTCLList $::sth::IsIs::isisTable
    
    #update the stcobj for the parameters whose stcobj is router in table file, the devicehandle may be emulateddevice, then these parameters will be missed.
    set router_paramlist "count router_id router_id_step"
    regsub {\d+$} $device "" update_obj
    foreach router_param $router_paramlist {
        set ::sth::IsIs::emulation_isis_config_stcobj($router_param) "$update_obj"
    }
    
    if {[info exists ::sth::hlapiGen::$isisrouter\_obj(isislspconfig)]} {
        set isislsp [set sth::hlapiGen::$isisrouter\_obj(isislspconfig)]
        append cfg_args_local [config_obj_attr ::sth::IsIs:: emulation_isis_config $isisrouter $isislsp isislspconfig]
    }
    
    set level [set ::sth::hlapiGen::$device\_$isisrouter\_attr(-level)]
    if {[regexp -nocase "level1" $level]} {
        set teparams [set ::sth::hlapiGen::$isisrouter\_obj(isislevel1teparams)]
        set teparams_type "isislevel1teparams"
        
    } else {
        set teparams [set ::sth::hlapiGen::$isisrouter\_obj(isislevel2teparams)]
        set teparams_type "isislevel2teparams" 
    }
    if {[info exists teparams]} {
        set subtlvs [set ::sth::hlapiGen::$isisrouter\_$teparams\_attr(-subtlv)]
        set subtlv_list [split $subtlvs "|"]
        if {[regexp -nocase "group|max_bw|max_rsv_bw|unreserved" $subtlvs]} {
            append cfg_args_local "-te_enable       1\\\n"
        }
        foreach subtlv $subtlv_list {
            switch -regexp -- [string tolower $subtlv] {
                group {
                    #only will conifg te_admin_group TeGroup
                    set te_admin_group [set ::sth::hlapiGen::$isisrouter\_$teparams\_attr(-tegroup)]
                    append cfg_args_local "-te_admin_group      $te_admin_group\\\n"
                }
                max_bw {
                    #only will configure te_max_bw TeMaxBandwidth
                    set te_max_bw [set ::sth::hlapiGen::$isisrouter\_$teparams\_attr(-temaxbandwidth)]
                    append cfg_args_local "-te_max_bw      $te_max_bw\\\n"
                }
                max_rsv_bw {
                    #only will configure te_max_resv_bw TeRsvrBandwidth
                    set te_max_resv_bw [set ::sth::hlapiGen::$isisrouter\_$teparams\_attr(-tersvrbandwidth)]
                    append cfg_args_local "-te_max_resv_bw      $te_max_resv_bw\\\n"
                }
                unreserved {
                    foreach arg "te_unresv_bw_priority0 te_unresv_bw_priority1 te_unresv_bw_priority2 te_unresv_bw_priority3\
                                    te_unresv_bw_priority4 te_unresv_bw_priority5 te_unresv_bw_priority6 te_unresv_bw_priority7" {
                        set ::sth::IsIs::emulation_isis_config_stcobj($arg) $teparams_type
                    }
                    set te_param [set ::sth::hlapiGen::$isisrouter\_obj($teparams_type)]
                    append cfg_args_local [config_obj_attr ::sth::IsIs:: emulation_isis_config $isisrouter $te_param $teparams_type]
                }
                default {
                    
                }
            }
        }
    }
    
    unset teparams

    set isis_auth_params [set ::sth::hlapiGen::$isisrouter\_obj(isisauthenticationparams)]
    set authentication_mode [set ::sth::hlapiGen::$isisrouter\_$isis_auth_params\_attr(-authentication)]
    append cfg_args_local "                       -authentication_mode              [string tolower $authentication_mode]\\\n"
    if {![regexp -nocase "none" $authentication_mode]} {
        set password [set ::sth::hlapiGen::$isisrouter\_$isis_auth_params\_attr(-password)]
        append cfg_args_local "                       -password              $password\\\n"
        if {[regexp -nocase "md5" $authentication_mode]} {
            set md5_key_id [set ::sth::hlapiGen::$isisrouter\_$isis_auth_params\_attr(-md5keyid)]
            append cfg_args_local "                       -md5_key_id              $md5_key_id\\\n"
        }
    } 
    #pre-process intf_metric
    if {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-l1metric)]} {
        append cfg_args_local "     -intf_metric    [set sth::hlapiGen::$device\_$isisrouter\_attr(-l1metric)]\\\n"
    } elseif {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-l1widemetric)]} {
        append cfg_args_local "     -intf_metric    [set sth::hlapiGen::$device\_$isisrouter\_attr(-l1widemetric)]\\\n"
    } elseif {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-l2metric)]} {
        append cfg_args_local "     -intf_metric    [set sth::hlapiGen::$device\_$isisrouter\_attr(-l2metric)]\\\n"
    } elseif {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-l2widemetric)]} {
        append cfg_args_local "     -intf_metric    [set sth::hlapiGen::$device\_$isisrouter\_attr(-l2widemetric)]\\\n"
    }
    #pre-process atm_encapsulation
    if {[info exists ::sth::hlapiGen::$device\_obj(aal5if)]} {
        append cfg_args_local "     -atm_encapsulation    1\\\n"
    }
    
    #pre-process vlan
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        append cfg_args_local "     -vlan    1\\\n"
    }
    #pre-process system_id
    if {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-systemid)]} {
        set systemid [set ::sth::hlapiGen::$device\_$isisrouter\_attr(-systemid)]
        if {![regexp "null" $systemid]} {
            if {[regexp {:} $systemid]} {
                set systemid [join [split $systemid ":"] ""]
            } elseif {[regexp {\.} $systemid]} {
                set systemid [join [split $systemid "."] ""]
            } else {
                set systemid [join [split $systemid "-"] ""]
            }
            append cfg_args_local "     -system_id    $systemid\\\n"
        }
        
    }
    if {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-systemid.step)]} {
        set systemidstep [set ::sth::hlapiGen::$device\_$isisrouter\_attr(-systemid.step)]
        if {![regexp "null" $systemidstep]} {
            if {[regexp ":" $systemidstep]} {
                set systemidstep [join [split $systemidstep ":"] ""]
            } else {
                set systemidstep [join [split $systemidstep "-"] ""]
            }
            append cfg_args_local "     -system_id_step    $systemidstep\\\n"
        }
    
    }
    #pre-process holding_time
    if {[info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-hellomultiplier)] && [info exists ::sth::hlapiGen::$device\_$isisrouter\_attr(-hellointerval)]} {
        set hellomultiplier [set ::sth::hlapiGen::$device\_$isisrouter\_attr(-hellomultiplier)]
        set hellointerval [set ::sth::hlapiGen::$device\_$isisrouter\_attr(-hellointerval)]
        set holding_time [expr $hellointerval * $hellomultiplier]
        append cfg_args_local "     -holding_time    $holding_time\\\n"
    }
}

proc ::sth::hlapiGen::isis_route_pre_process {lsp_cfg_args lsp_handle} {
    upvar lsp_cfg_args lsp_cfg_args_local
    set ipv4_routes ""
    set ipv6_routes ""
    set ipv4_networks ""
    set ipv6_networks ""
    
    if {[info exists sth::hlapiGen::$lsp_handle\_obj(ipv4isisroutesconfig)]} {
        set ipv4_routes [set sth::hlapiGen::$lsp_handle\_obj(ipv4isisroutesconfig)]
        set ipv4_networks ""
        foreach ipv4_route $ipv4_routes {
            set ipv4_networks [concat $ipv4_networks [set sth::hlapiGen::$ipv4_route\_obj(ipv4networkblock)]]
        }
    }
    
    if {[info exists sth::hlapiGen::$lsp_handle\_obj(ipv6isisroutesconfig)]} {
        set ipv6_routes [set sth::hlapiGen::$lsp_handle\_obj(ipv6isisroutesconfig)]
        set ipv6_networks ""
        foreach ipv6_route $ipv6_routes {
            set ipv6_networks [concat $ipv6_networks [set sth::hlapiGen::$ipv6_route\_obj(ipv6networkblock)]]
        }
    }
    
    if {[llength $ipv4_routes] > 1} {
        set ipv4_routes [lindex $ipv4_routes 0]
        set ipv4_networks [lindex $ipv4_networks 0]
    }
    if {[llength $ipv6_routes] > 1} {
        set ipv6_routes [lindex $ipv6_routes 0]
        set ipv6_networks [lindex $ipv6_networks 0]
    }
    
    #pre-process type  
    if {[llength [concat $ipv4_routes $ipv6_routes]] == 0} {
        set type "router"
    } else {
        set route [lindex [concat $ipv4_routes $ipv6_routes] 0]
        set routetype [set sth::hlapiGen::$lsp_handle\_$route\_attr(-routetype)]
        if {[regexp -nocase "INTERNAL" $routetype]} {
            set type "stub"
        } else {
            set type "external"
        }
    }
    append lsp_cfg_args_local "-type            $type\\\n"
    

    
    #pre-process external_count, external_ip_pfx_len, external_ip_start, external_ip_step
    #external_ipv6_pfx_len, external_ipv6_start, external_ipv6_step
    #pre-process stub_count, stub_ip_pfx_len, stub_ip_start, stub_ip_step, stub_ipv6_pfx_len, stub_ipv6_start, stub_ipv6_step
            #the stub_count and external_count should be same for ipv6 and ipv4
            
    if {![regexp "^$" $ipv4_networks]} {
        foreach arg "$type\_count $type\_ip_pfx_len $type\_ip_start $type\_ip_step" {
            set attr [string tolower [set ::sth::IsIs::emulation_isis_topology_route_config_stcattr($arg)]]
            set value [set ::sth::hlapiGen::$ipv4_routes\_$ipv4_networks\_attr(-$attr)]
            append lsp_cfg_args_local "-$arg    $value\\\n"
        }
    }
    
    if {![regexp "^$" $ipv6_networks]} {
        if {![regexp "^$" $ipv4_networks]} {
            set arg_list "$type\_ipv6_pfx_len $type\_ipv6_start $type\_ipv6_step"
        } else {
            set arg_list "$type\_count $type\_ipv6_pfx_len $type\_ipv6_start $type\_ipv6_step"
        }
        foreach arg $arg_list {
            set attr [string tolower [set ::sth::IsIs::emulation_isis_topology_route_config_stcattr($arg)]]
            set value [set ::sth::hlapiGen::$ipv6_routes\_$ipv6_networks\_attr(-$attr)]
            append lsp_cfg_args_local "-$arg    $value\\\n"
        }
    }
    
    #pre-process elem_handle
    
    #pre-process external_metric, stub_metric, external_metric_type, pre-process external_up_down_bit, stub_up_down_bit
    set isis_router [stc::get $lsp_handle -parent]
    set device [stc::get $isis_router -parent]
    set metric_mode [set sth::hlapiGen::$device\_$isis_router\_attr(-metricmode)]
    
    if {![regexp "^$" $ipv4_routes]} {
        if {[regexp -nocase "NARROW" $metric_mode] || [regexp -nocase "NARROW_AND_WIDE" $metric_mode]} {
            set metric [set sth::hlapiGen::$lsp_handle\_$ipv4_routes\_attr(-metric)]
        } else {
            set metric [set sth::hlapiGen::$lsp_handle\_$ipv4_routes\_attr(-widemetric)]
        }
        set metric_type [set sth::hlapiGen::$lsp_handle\_$ipv4_routes\_attr(-metrictype)]
        set up_down [set sth::hlapiGen::$lsp_handle\_$ipv4_routes\_attr(-updown)]
    } elseif {![regexp "^$" $ipv6_routes]} {
        if {[regexp -nocase "WIDE" $metric_mode] || [regexp -nocase "NARROW_AND_WIDE" $metric_mode]} {
            set metric [set sth::hlapiGen::$lsp_handle\_$ipv6_routes\_attr(-widemetric)]
        }
        set up_down [set sth::hlapiGen::$lsp_handle\_$ipv6_routes\_attr(-updown)]
    }
    
    if {![regexp "router" $type]} {
        if {[info exists metric]} {
            append lsp_cfg_args_local "-$type\_metric     $metric\\\n"
        }
        if {[info exists metric_type] && [regexp "external" $type]} {
            append lsp_cfg_args_local "-$type\_metric_type     $metric_type\\\n"
        }
        append lsp_cfg_args_local "-$type\_up_down_bit     $up_down\\\n"
    } 
    
    #pre-process router_connect
    #
    #pre-process link_te
}


proc ::sth::hlapiGen::hlapi_gen_device_ldpconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    
    ldp_router_pre_process $cfg_args $device
    
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    
    #config ldp route in cmd emulation_ldp_route_config
    #currently in hltapi, the fec_type supports "ipv4_prefix host_addr vc"
   
    set devicelist [update_device_handle $device $class $first_time]
    
    set i 0
    set cmd_name "emulation_ldp_route_config"
    set name_space "::sth::Ldp::"
    foreach device $devicelist {
        set ldp_router_config_hdl [set ::sth::hlapiGen::$device\_obj($class)]
        set objList "ipv4prefixlsp ipv4ingressprefixlsp ipv6prefixlsp ipv6ingressprefixlsp vclsp generalizedpwidlsp"
        foreach obj $objList {
            if {[info exists ::sth::hlapiGen::$ldp_router_config_hdl\_obj($obj)]} {
                set lsp_hdl_list  [set ::sth::hlapiGen::$ldp_router_config_hdl\_obj($obj)]
                puts_to_file [get_device_created $device $hlt_ret\_hdl handle]
                foreach lsp_hdl $lsp_hdl_list {
                    set route_cfg_args ""
                    set hlt_ret_route $hlt_ret\_route$i
                    set sth::hlapiGen::device_ret($lsp_hdl) $hlt_ret_route
                    append route_cfg_args "      set $hlt_ret_route \[sth::emulation_ldp_route_config\\\n"
                    append route_cfg_args "-mode 					create \\\n"
                    append route_cfg_args "-handle 					\$$hlt_ret\_hdl \\\n"
                    
                    #unset some parameter for different fce types
                    #{ipv4_prefix LDP_FEC_TYPE_PREFIX host_addr LDP_FEC_TYPE_HOST_ADDR vc LDP_FEC_TYPE_VC}

                    
                    set ipObj ""
                    set ipnetworkblock_hdl ""
                    if {[regexp -nocase "ipv4prefixlsp|ipv4ingressprefixlsp" $lsp_hdl]} {
                        set ipObj "ipv4networkblock"
                        set ipnetworkblock_hdl [set ::sth::hlapiGen::$lsp_hdl\_obj(ipv4networkblock)]
                        if {[regexp -nocase "ingress" $lsp_hdl]} {
                            set lsp_type "ipv4_ingress"
                        } else {
                            set lsp_type "ipv4_egress"
                        }
                    } elseif {[regexp -nocase "ipv6prefixlsp|ipv6ingressprefixlsp" $lsp_hdl]} {
                        set ipnetworkblock_hdl [set ::sth::hlapiGen::$lsp_hdl\_obj(ipv6networkblock)]
                        set ipObj "ipv6networkblock"
                        if {[regexp -nocase "ingress" $lsp_hdl]} {
                            set lsp_type "ipv6_ingress"
                        } else {
                            set lsp_type "ipv6_egress"
                        }
                    } elseif {[regexp -nocase "vclsp" $lsp_hdl]} {
                        set ipObj "macblock"
                        set lsp_type "pwid"
                        set ipnetworkblock_hdl [set ::sth::hlapiGen::$lsp_hdl\_obj(macblock)]
                    } else {
                        set lsp_type "generalized_pwid"
                    }
                    append route_cfg_args "-lsp_type $lsp_type \\\n"
                    append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $ldp_router_config_hdl $lsp_hdl $obj]
                    if {$ipnetworkblock_hdl != ""} {
                        set ipnetworkblock_hdl [set ::sth::hlapiGen::$lsp_hdl\_obj($ipObj)]
                        append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $lsp_hdl $ipnetworkblock_hdl $ipObj]
                    }
                    append route_cfg_args "\]\n"
                    puts_to_file $route_cfg_args
                    gen_status_info $hlt_ret_route "sth::emulation_ldp_route_config"
                    
                    #change back to the original value
                    #foreach unsupportedparam $unsupportedlist {
                    #    set $name_space$cmd_name\_stcobj($unsupportedparam) [set $name_space$cmd_name\_stcobj_bk($unsupportedparam)]
                    #}
                    
                    #generate the switching point tlvs
                    set tlv_obj "pseudowireswitchingpointtlv"
                    if {[info exists ::sth::hlapiGen::$lsp_hdl\_obj($tlv_obj)]} {
                        set switch_point_tlv_list [set ::sth::hlapiGen::$lsp_hdl\_obj($tlv_obj)]
                    } else {
                        incr i
                        continue
                    }
                    set j 0
                    set sub_cmd_name "emulation_lsp_switching_point_tlvs_config"
                    foreach switch_point_tlv $switch_point_tlv_list {
                        set tlv_cfg_args ""
                        puts_to_file [get_device_created $lsp_hdl $hlt_ret\_lsp$i\_hdl lsp_handle]
                        set hlt_ret_tlv $hlt_ret\_route$i\_tlv$j
                        set sth::hlapiGen::device_ret($switch_point_tlv) $hlt_ret_tlv
                        append tlv_cfg_args "      set $hlt_ret_tlv \[sth::emulation_lsp_switching_point_tlvs_config\\\n"
                        append tlv_cfg_args "-mode 					create \\\n"
                        append tlv_cfg_args "-lsp_handle 					\$$hlt_ret\_lsp$i\_hdl \\\n"
                        append tlv_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $sub_cmd_name $lsp_hdl $switch_point_tlv $tlv_obj]
                        append tlv_cfg_args "\]\n"
                        set tlv_cfg_args [remove_unuse_attr $tlv_cfg_args $name_space $sub_cmd_name]
                        puts_to_file $tlv_cfg_args
                        gen_status_info $hlt_ret_tlv "sth::emulation_lsp_switching_point_tlvs_config"
                        incr j
                    }
                    incr i
                }
            }
        }
    }
}

proc ::sth::hlapiGen::ldp_router_pre_process {cfg_args device} {
    upvar cfg_args cfg_args_local
    
    set table_name "::sth::Ldp::LdpTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_ldp_config"
    if {[info exists sth::hlapiGen::$device\_obj(ipv4if)] && [info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
        append cfg_args_local "     -ip_version    ipv46\\\n"
    } elseif {[info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
        append cfg_args_local "     -ip_version    ipv6\\\n"
    } else {
        append cfg_args_local "     -ip_version    ipv4\\\n"
        unset ::sth::hlapiGen::$device\_$device\_attr(-ipv6routerid)
    }
    
    #pre-process the tunnel handle, to config this, need to call the gre config function
    if {[info exists sth::hlapiGen::$device\_obj(greif)]} {
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args_local
        append cfg_args_local "                       -tunnel_handle              \$gre_ret\\\n"
    }
    
    #update the stcobj for the parameters whose stcobj is router in table file, the devicehandle may be emulateddevice, then these parameters will be missed.
    set router_paramlist "count lsr_id lsr_id_step ipv6_router_id ipv6_router_id_step"
    regsub {\d+$} $device "" update_obj
    foreach router_param $router_paramlist {
        set $name_space$cmd_name\_stcobj($router_param) "$update_obj"
    }
    if {$::sth::hlapiGen::scaling_test} {
        array set param_attr "count count intf_ip_addr_step Address.Step gateway_ip_addr_step Gateway.Step label_step LabelMin.Step lsr_id_step RouterId.Step\
                  remote_ip_addr_step DutIp.Step vlan_id_mode VlanId.mode vlan_id_step vlanid.step vlan_outer_id_step vlanid.step vlan_outer_id_mode VlanId.mode\
                  intf_ipv6_addr_step Address.Step link_local_ipv6_addr_step Address.Step ipv6_router_id_step IPv6RouterId.Step remote_ipv6_addr_step DutIpv6.Step"
        foreach param [array names param_attr] {
            set $name_space$cmd_name\_stcattr($param) $param_attr($param)
        }

        array unset param_attr
    }
    
    #process vlan_id_mode and vlan_outer_id_mode
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)] && $::sth::hlapiGen::scaling_test == 0} {
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
                    append cfg_args_local "     -vlan_outer_id_mode    $vlan_mode\\\n"
                } else {
                    append cfg_args_local "     -vlan_id_mode    $vlan_mode\\\n"
                }
            } else {
                   append cfg_args_local "     -vlan_id_mode    $vlan_mode\\\n"
            }
        }
    }
    
    #handle the affiliated_router_target
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-affiliatedrouter-targets)]} {
        set attached_router [set ::sth::hlapiGen::$device\_$device\_attr(-affiliatedrouter-targets)]
        if {![info exists ::sth::hlapiGen::$attached_router\_obj(ldprouterconfig)]} {
            set attached_router_hdl [get_device_created $attached_router attached_router_hdl handle]
            if {$attached_router_hdl != ""} {
                puts_to_file $attached_router_hdl
                set ::sth::hlapiGen::$device\_$device\_attr(-affiliatedrouter-targets) "\$attached_router_hdl"
            }
        }

    }
    
    #loopback_ip_addr has the same configuration attr as lsr_id, vlan_cfi has the same configuration attr as cfi, so unset loopback_ip_addr and vlan_cfi.
    set duplicated_attr_list "loopback_ip_addr cfi"
    foreach duplicated_attr $duplicated_attr_list {
        set $name_space$cmd_name\_stcobj($duplicated_attr) "_none_"
    }
    #check the hellotype to determine the hello interval: add the directed_hello_interval and targeted_hello_interval, so 
    #do not need the hell_interval
    #set ldprouter_hdl [set ::sth::hlapiGen::$device\_obj(ldprouterconfig)]
    #set hello_type [set ::sth::hlapiGen::$device\_$ldprouter_hdl\_attr(-hellotype)]
    #switch -regexp -- [string tolower $hello_type] {
    #    "ldp_directed_hello" {
    #        set $name_space$cmd_name\_stcattr(hello_interval) "DirectedHelloInterval"
    #    }
    #    "ldp_targeted_hello" {
    #        set $name_space$cmd_name\_stcattr(hello_interval) "TargetedHelloInterval"
    #    }
    #}
    
}

proc ::sth::hlapiGen::hlapi_gen_device_lldpconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    set variable_cfg_args ""
    set table_name "::sth::Lldp::lldpTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_lldp_config"
    
    
    if {$first_time != 1} {
        #set the control and results function to none
        set ::sth::hlapiGen::hlapi_gen_ctrlConvertFunc($class) "_none_"
        set ::sth::hlapiGen::hlapi_gen_resultConvertFunc($class) "_none_"
        puts_to_file "#lldp protocol doesn't support multiple protocols currently"
        return
    }
    

    set lldp_node_config_hdl [set ::sth::hlapiGen::$device\_obj($class)]
    set lldp_tlv_config_hdl [set ::sth::hlapiGen::$lldp_node_config_hdl\_obj(lldptlvconfig)]
    hlapi_gen_device_lldp_optional_tlv_config $lldp_tlv_config_hdl $hlt_ret 
    hlapi_gen_device_lldp_dcbx_tlv_config $lldp_tlv_config_hdl $hlt_ret $name_space
    if {$variable_cfg_args != ""} {
        puts_to_file $variable_cfg_args
    }
    if {[regexp -nocase "lldp_optional_tlv.*dcbx_tlvs" $cfg_args]} {
        append cfg_args "-reset_tlv_type    both\\\n"  
    } elseif {[regexp -nocase "lldp_optional_tlv" $cfg_args]} {
        append cfg_args "-reset_tlv_type    lldp\\\n"  
    } elseif {[regexp -nocase "dcbx_tlvs" $cfg_args]} {
        append cfg_args "-reset_tlv_type    dcbx\\\n"  
    }
    
    # the router of stcobj may need to be updated
    set router_paramlist "count loopback_ip_addr loopback_ip_addr_step"
    regsub {\d+$} $device "" update_obj
    foreach router_param $router_paramlist {
        set $name_space$cmd_name\_stcobj($router_param) "$update_obj"
    }
    
    #remove the Router- in the stcobj column
    foreach arg [array names $name_space$cmd_name\_stcobj] {
        if {$arg == "intf_ipv6_link_local_addr"} {
            set $name_space$cmd_name\_stcobj($arg) "Ipv6If_Link_Local"
        }
        regsub {^Router-} [set $name_space$cmd_name\_stcobj($arg)] "" $name_space$cmd_name\_stcobj($arg)                                                                                    
    }
    #update the stcattr for the step arguments
    set attrlist "loopback_ip_addr_step local_mac_addr_step vlan_id_step intf_ip_addr_step gateway_ip_addr_step intf_ipv6_addr_step "
    foreach arg $attrlist {
        set $name_space$cmd_name\_stcattr($arg) [set $name_space$cmd_name\_stcattr($arg)].Step
    }
    
    #handle intf_ipv6_link_local_addr
    
    #handle the chassidtlv, portidtlv and timetolivetlv
    if {[info exists ::sth::hlapiGen::$lldp_tlv_config_hdl\_obj(lldp:chassisidtlv)]} {
        set chassisidtlv [set ::sth::hlapiGen::$lldp_tlv_config_hdl\_obj(lldp:chassisidtlv)]
        set chassisid_hdl [set ::sth::hlapiGen::$chassisidtlv\_obj(chassisid)]
        set chassisid_type [array names ::sth::hlapiGen::$chassisid_hdl\_obj]
        set chassissubtype_hdl [set ::sth::hlapiGen::$chassisid_hdl\_obj($chassisid_type)]
        set chassisid [set ::sth::hlapiGen::$chassisid_hdl\_$chassissubtype_hdl\_attr(-id)]
        
        if {[regexp -nocase "networkaddress4" $chassissubtype_hdl]} {
            set chassisid_type "network_addr_4"
            if {$chassisid == "null"} {
                set chassisid "192.168.1.1"
            }
        } elseif {[regexp -nocase "networkaddress6" $chassissubtype_hdl]} {
            set chassisid_type "network_addr_6"
            if {$chassisid == "null"} {
                set chassisid "2000::"
            }
        } elseif {[regexp -nocase "macAddress" $chassissubtype_hdl]} {
            set chassisid_type "mac_addr"
            if {$chassisid == "null"} {
                set chassisid "00:00:00:00:00:00"
            }
        } else {
            foreach const [array names $name_space$cmd_name\_tlv_chassis_id_subtype_rvsmap] {
                if {[regexp -nocase "^$const$" $chassisid_type]} {
                    set chassisid_type [set $name_space$cmd_name\_tlv_chassis_id_subtype_rvsmap($const)]
                    break
                }
            }
        }
        
        append cfg_args "-tlv_chassis_id_subtype    $chassisid_type\\\n"
        if {$chassisid != "null"} {
            append cfg_args "-tlv_chassis_id_value      $chassisid\\\n"
        }
    }
    
    if {[info exists ::sth::hlapiGen::$lldp_tlv_config_hdl\_obj(lldp:portidtlv)]} {
        set portidtlv [set ::sth::hlapiGen::$lldp_tlv_config_hdl\_obj(lldp:portidtlv)]
        set portid_hdl [set ::sth::hlapiGen::$portidtlv\_obj(portid)]
        set portid_type [array names ::sth::hlapiGen::$portid_hdl\_obj]
        set portidsubtype_hdl [set ::sth::hlapiGen::$portid_hdl\_obj($portid_type)]
        set portid [set ::sth::hlapiGen::$portid_hdl\_$portidsubtype_hdl\_attr(-id)]
        
        if {[regexp -nocase "pidNetworkAddress4" $portidsubtype_hdl]} {
            set portid_type "network_addr_4"
            if {$portid == "null"} {
                set portid "192.168.1.1"
            }
        } elseif {[regexp -nocase "pidNetworkAddress6" $portidsubtype_hdl]}  {
            set portid_type "network_addr_6"
            if {$portid == "null"} {
                set portid "2000::"
            }
        } elseif {[regexp -nocase "pidMacAddress" $portidsubtype_hdl]} {
            set portid_type "mac_addr"
            if {$portid == "null"} {
                set portid "00:00:00:00:00:00"
            }
        } else {
            foreach const [array names $name_space$cmd_name\_tlv_port_id_subtype_rvsmap] {
                if {[regexp -nocase "^$const$" $portid_type]} {
                    set portid_type [set $name_space$cmd_name\_tlv_port_id_subtype_rvsmap($const)]
                    break
                }
            }
        }
        
        append cfg_args "-tlv_port_id_subtype    $portid_type\\\n"
        if {$portid != "null"} {
            append cfg_args "-tlv_port_id_value      $portid\\\n"
        }
    }
    
    if {[info exists ::sth::hlapiGen::$lldp_tlv_config_hdl\_obj(lldp:timetolivetlv)]} {
        set ttltlv_hdl [set ::sth::hlapiGen::$lldp_tlv_config_hdl\_obj(lldp:timetolivetlv)]
        set ttl [set ::sth::hlapiGen::$lldp_tlv_config_hdl\_$ttltlv_hdl\_attr(-ttl)]
        if {$ttl != "null"} {
            append cfg_args "-tlv_ttl_value      $ttl\\\n" 
        } else {
            append cfg_args "-tlv_ttl_value      0\\\n"
        }
    }
        
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    
}

proc ::sth::hlapiGen::hlapi_gen_device_lldp_optional_tlv_config {tlvcfg_hdl hlt_ret} {
    upvar cfg_args cfg_args_local
    upvar variable_cfg_args variable_cfg_args_local
    set optional_tlv_cfg_args ""
    #process emulation_lldp_optional_tlv_config
    set cmd "emulation_lldp_optional_tlv_config"
    array set optional_tlv_cfg_args_array ""
    
    #handle PortDescriptionTlv, SystemNameTlv, SystemDescriptionTlv, PortVlanIdTlv, MaxFrameSizeTlv and CustomTlv
    array set tlvlist "portdescriptiontlv {port_description description} systemnametlv {system_name name} systemdescriptiontlv {system_description description}\
                        portvlanidtlv {port_vlanid portvlanid} maxframesizetlv {maximum_frame_size framesize} customtlv {customized value}"
    foreach tlv_type [string tolower [array names tlvlist]] {
        if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:$tlv_type)]} {
            set subtlvhdl [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:$tlv_type)]
            set attr_in_table [lindex $tlvlist($tlv_type) 0]
            set attr_in_dm [lindex $tlvlist($tlv_type) 1]
            set value [set ::sth::hlapiGen::$tlvcfg_hdl\_$subtlvhdl\_attr(-$attr_in_dm)]
            array set optional_tlv_cfg_args_array "-tlv_$attr_in_table\_enable        1"
            array set optional_tlv_cfg_args_array "-tlv_$attr_in_table\_value         \"$value\""
            if {[regexp -nocase "CustomTlv" $tlv_type]} {
                set type [set ::sth::hlapiGen::$tlvcfg_hdl\_$subtlvhdl\_attr(-type)]
                array set optional_tlv_cfg_args_array "-tlv_$attr_in_table\_type         $type"
            }
        }
    }
    array unset tlvlist
    
    # handle the tlv with children: SystemCapabilitiesTlv MacPhyConfigStatusTlv PowerViaMdiTlv LinkAggregationTlv
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:systemcapabilitiestlv)]} {
        set sys_cap_tlv_hdl [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:systemcapabilitiestlv)]
        array set optional_tlv_cfg_args_array "-tlv_system_capabilities_enable     1"
        foreach sys_cap_tlv_child [array names ::sth::hlapiGen::$sys_cap_tlv_hdl\_obj] {
            set child_hdl [set ::sth::hlapiGen::$sys_cap_tlv_hdl\_obj($sys_cap_tlv_child)]
            set attrlist "other repeater bridge wlanaccesspoint router telephone docsiscabledevice stationonly"
            set bitstring ""
            foreach attr $attrlist {
                set bitvalue [set ::sth::hlapiGen::$sys_cap_tlv_hdl\_$child_hdl\_attr(-$attr)]
                if {$bitvalue == "null"} {
                    if {[string match router $attr]} {
                        set bitvalue 1
                    } else {
                        set bitvalue 0
                    }
                }
                append bitstring $bitvalue
            }
            if {[regexp -nocase "systemCapabilities" $child_hdl]} {
                array set optional_tlv_cfg_args_array "-tlv_system_capabilities_value     $bitstring"
            } else {
                array set optional_tlv_cfg_args_array "-tlv_enabled_capabilities_value     $bitstring"
            }
        }
    }
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:macphyconfigstatustlv)]} {
        set mac_phy_tlv_hdl [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:macphyconfigstatustlv)]
        set mau_type [set ::sth::hlapiGen::$tlvcfg_hdl\_$mac_phy_tlv_hdl\_attr(-operationalmautype)]
        array set optional_tlv_cfg_args_array "-tlv_mac_phy_config_status_enable     1"
        array set optional_tlv_cfg_args_array "-tlv_mac_phy_config_status_operational_mau_type     $mau_type"
        foreach mac_phy_tlv_child [array names ::sth::hlapiGen::$mac_phy_tlv_hdl\_obj] {
            set child_hdl [set ::sth::hlapiGen::$mac_phy_tlv_hdl\_obj($mac_phy_tlv_child)]
            if {[regexp -nocase "autoNegotiationSupportAndStatus" $mac_phy_tlv_child]} {
                set support_value [set ::sth::hlapiGen::$mac_phy_tlv_hdl\_$child_hdl\_attr(-autonegotiationsupported)]
                set enabled_value [set ::sth::hlapiGen::$mac_phy_tlv_hdl\_$child_hdl\_attr(-autonegotiationenabled)]
                array set optional_tlv_cfg_args_array "-tlv_mac_phy_config_status_auto_negotiation_status_flag     $enabled_value"
                array set optional_tlv_cfg_args_array "-tlv_mac_phy_config_status_auto_negotiation_supported_flag     $support_value"
            }
            if {[regexp -nocase "autoNegotiationAdvertisedCapability" $mac_phy_tlv_child]} {
                set attrlist "other b10baset b10basetfd b100baset4 b100basetx b100basetxfd b100baset2 b100baset2fd\
                             bfdxpause bfdxapause bfdxspause bfdxbpause b1000basex b1000basexfd b1000baset b1000basetfd"
                set bitstring ""
                foreach attr $attrlist {
                    set bitvalue [set ::sth::hlapiGen::$mac_phy_tlv_hdl\_$child_hdl\_attr(-$attr)]
                    if {$bitvalue == "null"} {
                        if {$attr == "b100baseTX"} {
                            set bitvalue 1
                        } else {
                            set bitvalue 0
                        }
                    }
                    append bitstring $bitvalue
                }
                binary scan [binary format B16 $bitstring] H* advertised_capability
                array set optional_tlv_cfg_args_array "-tlv_mac_phy_config_status_auto_negotiation_advertised_capability     $advertised_capability"
            }
        }
    }
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:powerviamditlv)]} {
        set power_via_tlv_hdl [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:powerviamditlv)]
        set psepowerclass [set ::sth::hlapiGen::$tlvcfg_hdl\_$power_via_tlv_hdl\_attr(-psepowerclass)]
        if {$psepowerclass == "null"} {
            set psepowerclass "01"
        }
        set psepowerpairs [set ::sth::hlapiGen::$tlvcfg_hdl\_$power_via_tlv_hdl\_attr(-psepowerpairs)]
        if {$psepowerpairs == "null"} {
            set psepowerpairs "01"
        }
        regsub {^0} $psepowerclass "class" psepowerclass
        switch -regexp -- $psepowerpairs {
            "01" {
                set psepowerpairs "signal"
            }
            "02" {
                set psepowerpairs "spare"
            }
        }
        
        set mldpower_hdl [set ::sth::hlapiGen::$power_via_tlv_hdl\_obj(mdipowersupport)]
        set attrlist "psepairscontrolability psemdipowerstate psemdipowersupport portclass"
        set bitstring ""
        foreach attr $attrlist {
            set bitvalue [set ::sth::hlapiGen::$power_via_tlv_hdl\_$mldpower_hdl\_attr(-$attr)]
            if {$bitvalue == "null"} {
                    set bitvalue 0
            }
            append bitstring $bitvalue
        }
        
        array set optional_tlv_cfg_args_array "-tlv_power_via_mdi_enable      1"
        array set optional_tlv_cfg_args_array "-tlv_power_via_mdi_pse_power_class     $psepowerclass"
        array set optional_tlv_cfg_args_array "-tlv_power_via_mdi_pse_power_pair     $psepowerpairs"
        array set optional_tlv_cfg_args_array "-tlv_power_via_mdi_power_support_bits        $bitstring"
    }
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:linkaggregationtlv)]} {
        set link_aggr_tlv_hdl [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:linkaggregationtlv)]
        set port_id [set ::sth::hlapiGen::$tlvcfg_hdl\_$link_aggr_tlv_hdl\_attr(-aggregatedportid)]
        set aggregation_status_hdl [set ::sth::hlapiGen::$link_aggr_tlv_hdl\_obj(aggregationstatus)]
        set status [set ::sth::hlapiGen::$link_aggr_tlv_hdl\_$aggregation_status_hdl\_attr(-aggregationstatus)]
        set capability [set ::sth::hlapiGen::$link_aggr_tlv_hdl\_$aggregation_status_hdl\_attr(-aggregationcapability)]
        array set optional_tlv_cfg_args_array "-tlv_link_aggregation_enable      1"
        array set optional_tlv_cfg_args_array "-tlv_link_aggregation_aggregated_port_id     $port_id"
        array set optional_tlv_cfg_args_array "-tlv_link_aggregation_status_flag     $status"
        array set optional_tlv_cfg_args_array "-tlv_link_aggregation_capability_flag        $capability"
    }
        
    
    # handle the tlv with count and can be configured as a list
    # ManagementAddrTlv PortAndProtocolVlanIdTlv VlanNameTlv ProtocolIdentityTlv
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:managementaddrtlv)]} {
        set attrlist "subtype value intf_numbering_subtype intf_number_value oid_value"
        foreach attr $attrlist {
            set $attr\_list ""
        }
        set manage_addr_tlv_list [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:managementaddrtlv)]
        set count [llength $manage_addr_tlv_list]
        foreach manage_addr_tlv $manage_addr_tlv_list {
            set manage_addr_hdl [set ::sth::hlapiGen::$manage_addr_tlv\_obj(managementaddr)]
            set addr_type [array names ::sth::hlapiGen::$manage_addr_hdl\_obj]
            set addr_hdl [set ::sth::hlapiGen::$manage_addr_hdl\_obj($addr_type)]
            set subtype [set ::sth::hlapiGen::$manage_addr_hdl\_$addr_hdl\_attr(-addrsubtype)]
            if {$subtype == "null"} {
                switch -regexp -- $addr_type {
                    "ipv4" {
                        set subtype "ipv4"
                    }
                    "ipv6" {
                        set subtype "ipv6"
                    }
                    "custom" {
                        set subtype "other"
                    }
                }
            } else {
                array set mapTable {00 other 01 ipv4 02 ipv6 03 nsap 04 hdlc 05 bbn1822 06 all_802 07 e163 \
                                                        08 e164 09 f69 0A x121 0B ipx 0C apple_talk 0D dec_net_iv 0E banyan_vines 0F \
                                                        e164_with_nsap 10 dns 11 distinguished_name 12 as_number 13 xtp_over_ipv4 14 \
                                                        xtp_over_ipv6 15 xtp_native_mode_xtp 16 fibre_channel_wwpn 17 \
                                                        fibre_channel_wwnn 18 gateway_identifier 19 afi}
                set subtype $mapTable($subtype)
            }
            set value [set ::sth::hlapiGen::$manage_addr_hdl\_$addr_hdl\_attr(-managementaddr)]
            set intf_numbering_subtype [set ::sth::hlapiGen::$tlvcfg_hdl\_$manage_addr_tlv\_attr(-ifnumberingsubtype)]
            set intf_number_value [set ::sth::hlapiGen::$tlvcfg_hdl\_$manage_addr_tlv\_attr(-ifnumber)]
            set oid_value [set ::sth::hlapiGen::$tlvcfg_hdl\_$manage_addr_tlv\_attr(-oid)]

            foreach attr $attrlist {
                if {[set $attr] == "null"} {
                    switch -- $attr {
                        "value" {
                            set value 00
                        }
                        "intf_numbering_subtype" {
                            set intf_numbering_subtype 01
                        }
                        "intf_number_value" {
                            set intf_number_value 0
                        }
                    }
                }
                set $attr\_list [concat [set $attr\_list] [set $attr]]
            }
            array unset mapTable
        }
        array set optional_tlv_cfg_args_array "-tlv_management_addr_enable      1"
        array set optional_tlv_cfg_args_array "-tlv_management_addr_count     $count"
        regsub "oid_value" $attrlist "" attrlist
        foreach attr $attrlist {
            array set optional_tlv_cfg_args_array "-tlv_management_addr_$attr\_list    \"[set $attr\_list]\""
        }
        
        set oid_value_len [llength $oid_value_list]
        if {$oid_value_len == 1 && $oid_value_list != "null"} {
            array set optional_tlv_cfg_args_array "-tlv_management_addr_oid_value_list  $oid_value_list"
        } elseif {$oid_value_len > 1} {
            set null_len 0
            set new_oid_value_list ""
            foreach oid_value $oid_value_list {
                if {$oid_value == "null"} {
                    set oid_value 0
                    incr null_len
                }
                set new_oid_value_list [concat $new_oid_value_list $oid_value]
            }
            if {$oid_value_len != $null_len} {
                array set optional_tlv_cfg_args_array "-tlv_management_addr_oid_value_list  \"$new_oid_value_list\""
            }
        }
    }
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:portandprotocolvlanidtlv)]} {
        set attrlist "value enabled_flag supported_flag"
        foreach attr $attrlist {
            set $attr\_list ""
        }
        set port_protocol_tlv_list [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:portandprotocolvlanidtlv)]
        set count [llength $port_protocol_tlv_list]
        
        foreach port_protocol_tlv $port_protocol_tlv_list {
            set value [set ::sth::hlapiGen::$tlvcfg_hdl\_$port_protocol_tlv\_attr(-portandprotocolvlanid)]
            set flags_hdl [set ::sth::hlapiGen::$port_protocol_tlv\_obj(flags)]
            set enabled_flag [set ::sth::hlapiGen::$port_protocol_tlv\_$flags_hdl\_attr(-portandprotocolvlanenabled)]
            set supported_flag [set ::sth::hlapiGen::$port_protocol_tlv\_$flags_hdl\_attr(-portandprotocolvlansupport)]
            foreach attr $attrlist {
                set $attr\_list [concat [set $attr\_list] [set $attr]]
            }
        }
        
        array set optional_tlv_cfg_args_array "-tlv_port_and_protocol_vlanid_enable      1"
        array set optional_tlv_cfg_args_array "-tlv_port_and_protocol_vlanid_count     $count"
        
        foreach attr $attrlist {
            array set optional_tlv_cfg_args_array "-tlv_port_and_protocol_vlanid_$attr\_list    \"[set $attr\_list]\""
        }
    }
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:vlannametlv)]} {
        set attrlist "vid value"
        foreach attr $attrlist {
            set $attr\_list ""
        }
        set vlan_name_tlv_list [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:vlannametlv)]
        set count [llength $vlan_name_tlv_list]
        
        foreach vlan_name_tlv $vlan_name_tlv_list {
            set vid [set ::sth::hlapiGen::$tlvcfg_hdl\_$vlan_name_tlv\_attr(-vlanid)]
            set value [set ::sth::hlapiGen::$tlvcfg_hdl\_$vlan_name_tlv\_attr(-vlanname)]
            if {$vid == "null"} {
                set vid 1
            }
            if {$value == "null"} {
                set value "Vlan_1"
            } else {
                regsub {\s} $value {\_} value
            }
            foreach attr $attrlist {
                set $attr\_list [concat [set $attr\_list] [set $attr]]
            }
        }
        
        array set optional_tlv_cfg_args_array "-tlv_vlan_name_enable      1"
        array set optional_tlv_cfg_args_array "-tlv_vlan_name_count     $count"
        foreach attr $attrlist {
            array set optional_tlv_cfg_args_array "-tlv_vlan_name_$attr\_list    \"[set $attr\_list]\""
        }
    }
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:protocolidentitytlv)]} {
        set value_list ""
        
        set proto_id_tlv_list [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:protocolidentitytlv)]
        set count [llength $proto_id_tlv_list]
        
        foreach proto_id_tlv $proto_id_tlv_list {
            set value [set ::sth::hlapiGen::$tlvcfg_hdl\_$proto_id_tlv\_attr(-protocolidentity)]
            if {$value == "null"} {
                set value "0000"
            }
            set value_list [concat $value_list $value]
        }
        
        array set optional_tlv_cfg_args_array "-tlv_protocol_identity_enable      1"
        array set optional_tlv_cfg_args_array "-tlv_protocol_identity_count     $count"
        array set optional_tlv_cfg_args_array "-tlv_protocol_identity_value_list   \"$value_list\""

    }
    
    if {[array names optional_tlv_cfg_args_array] != ""} {
        append optional_tlv_cfg_args "set $hlt_ret\_optional_tlv_config \[sth::$cmd\\\n"
        foreach attr [lsort [array names optional_tlv_cfg_args_array]] {
            set value $optional_tlv_cfg_args_array($attr)
            set value [null_to_default_value "::sth::Lldp::" $cmd $value $attr]
            append optional_tlv_cfg_args "$attr    $value\\\n"
        }
        append optional_tlv_cfg_args "\]\n"
        puts_to_file $optional_tlv_cfg_args
        gen_status_info $hlt_ret\_optional_tlv_config sth::$cmd
        
        append variable_cfg_args_local "set lldp_optional_tlv_hdl \[keylget $hlt_ret\_optional_tlv_config handle\]\n"
        append cfg_args_local "-lldp_optional_tlvs \$lldp_optional_tlv_hdl\\\n"
        
        #unset attrlist
        if {[info exists attrlist]} {
            unset attrlist
        }
        
        array unset optional_tlv_cfg_args_array
    }
    
}

proc ::sth::hlapiGen::hlapi_gen_device_lldp_dcbx_tlv_config {tlvcfg_hdl hlt_ret name_space} {
    upvar cfg_args cfg_args_local
    upvar variable_cfg_args variable_cfg_args_local
    set dcbx_tlv_cfg_args ""
    set dcbx_tlv_cfg_args_header ""
    array set dcbx_tlv_cfg_args_array ""
    #process emulation_lldp_dcbx_tlv_config
    set cmd_name "emulation_lldp_dcbx_tlv_config"
     
    
    if {[info exists ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:dcbxtlvt)]} {
        set dcbx_tlv_hdl [set ::sth::hlapiGen::$tlvcfg_hdl\_obj(lldp:dcbxtlvt)]
        if {[regexp "lldp:dcbxtlvt1" $dcbx_tlv_hdl]} {
            array set dcbx_tlv_cfg_args_array  "-version_num      ver_100"
            set version 1
        } elseif {[regexp "lldp:dcbxtlvt2" $dcbx_tlv_hdl]} {
            array set dcbx_tlv_cfg_args_array  "-version_num      ver_103"
            set version 2
        }  
    } else {
        return
    }
    
    set value_hdl [set ::sth::hlapiGen::$dcbx_tlv_hdl\_obj(value)]
    set dcbx_subtlv_hdl_list [set ::sth::hlapiGen::$value_hdl\_obj(dcbxsubtlvt)]
    
    foreach dcbx_subtlv_hdl $dcbx_subtlv_hdl_list {
        #dcbxCtlTlv
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(dcbxctltlv)]} {
            set dcbx_ctl_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(dcbxctltlv)]
            set oper_version [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_ctl_tlv\_attr(-operver)]
            set max_version [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_ctl_tlv\_attr(-maxver)]
            if {$oper_version == "null"} {
                set oper_version 0
            }
            if {$max_version == "null"} {
                set max_version 0
            }
            array set dcbx_tlv_cfg_args_array  "-control_tlv_oper_version     $oper_version"
            array set dcbx_tlv_cfg_args_array  "-control_tlv_max_version      $max_version"
        }
        
        #pg_feature
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(pgtlv)]} {
            set dcbx_pg_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(pgtlv)]
            set pg_header [set ::sth::hlapiGen::$dcbx_pg_tlv\_obj(header)]
            
            array set dcbx_tlv_cfg_args_array  "-pg_feature_tlv$version\_enable     1"
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_pg_tlv $pg_header TLV_DcbxPG_Type$version\-header]
            
            if {$version == 1} {
                set bwg_percentage [set ::sth::hlapiGen::$dcbx_pg_tlv\_obj(bwg_percentage)]
                set bwg_bitstring [process_bitstring $dcbx_pg_tlv $bwg_percentage bwg_percentage 8 "list"]
                array set dcbx_tlv_cfg_args_array  "-pg_feature_tlv1_bwg_percentage_list     $bwg_bitstring"
                
                set attrlist "bwg_id strict_prio bw_percentage"
                foreach attr $attrlist {
                    set $attr\_list ""
                }
                for {set i 0} {$i < 8} {incr i} {
                    #bound priority$iallocation attr into the list
                    set allocation_hdl [set ::sth::hlapiGen::$dcbx_pg_tlv\_obj(priority[string trim $i]allocation)]
                    set bwg_id [set ::sth::hlapiGen::$dcbx_pg_tlv\_$allocation_hdl\_attr(-bwg_id)]
                    set strict_prio [set ::sth::hlapiGen::$dcbx_pg_tlv\_$allocation_hdl\_attr(-strict_prio)]
                    set bw_percentage [set ::sth::hlapiGen::$dcbx_pg_tlv\_$allocation_hdl\_attr(-bw_percentage)]
                    foreach attr $attrlist {
                        if {[set $attr] == "null"} {
                            set $attr 0
                        }
                        set $attr\_list [concat [set $attr\_list] [set $attr]]
                    }
                }
                foreach attr $attrlist {
                    array set dcbx_tlv_cfg_args_array  "-pg_feature_tlv1_prio_alloc_$attr\_list    \"[set $attr\_list]\""
                }
                
            } else {
                set prio_allocation [set ::sth::hlapiGen::$dcbx_pg_tlv\_obj(prioallocation)]
                set pg_allocation [set ::sth::hlapiGen::$dcbx_pg_tlv\_obj(pgallocation)]
                set num_tcs [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_pg_tlv\_attr(-numtcs)]
                set prio_bitstring [process_bitstring $dcbx_pg_tlv $prio_allocation pgid 8 "list"]
                set pg_bitstring [process_bitstring $dcbx_pg_tlv $pg_allocation bw 8 "list"]
                array set dcbx_tlv_cfg_args_array  "-pg_feature_tlv2_prio_alloc_pgid_list     $prio_bitstring"
                array set dcbx_tlv_cfg_args_array  "-pg_feature_tlv2_pg_alloc_bw_percentage_list     $pg_bitstring"
                array set dcbx_tlv_cfg_args_array  "-pg_feature_tlv2_num_tcs_supported        $num_tcs"
            }
            
        }
        
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(pfctlv)]} {
            set dcbx_pfc_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(pfctlv)]
            set pfc_header [set ::sth::hlapiGen::$dcbx_pfc_tlv\_obj(header)]
            set admin_mode_bits [process_bitstring $dcbx_subtlv_hdl $dcbx_pfc_tlv pe 8 "bitstring"]
            
            array set dcbx_tlv_cfg_args_array  "-pfc_feature_tlv$version\_enable     1"
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_pfc_tlv $pfc_header TLV_DcbxPFC_Type$version\-header]
            array set dcbx_tlv_cfg_args_array  "-pfc_feature_tlv$version\_admin_mode_bits     $admin_mode_bits"
            
            if {$version == 2} {
                set num_tcp_fcs [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_pfc_tlv\_attr(-numtcpfcs)]
                array set dcbx_tlv_cfg_args_array  "-pfc_feature_tlv2_num_tcpfcs_supported     $num_tcp_fcs"
            }
        }
        
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(applicatontlv)]} {
            set dcbx_app_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(applicatontlv)]
            set app_header [set ::sth::hlapiGen::$dcbx_app_tlv\_obj(header)]
            
            if {$version == 1} {
                set param_prefix "application_feature"
                set stcobj_app "TLV_DcbxApp_Type1"
                set priority_map [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_app_tlv\_attr(-prioritymap)]
                if {$priority_map == "null"} {
                    set priority_map 1000
                }
                set len [string length $priority_map]
                for {set i 0} {$i < [expr {8 - $len}]} {incr i} {
                    set priority_map 0$priority_map
                }
                array set dcbx_tlv_cfg_args_array  "-application_feature_tlv1_prio_map     $priority_map"
            } else {
                set param_prefix "app_protocol"
                set stcobj_app "TLV_DcbxAppPro_Type2"
                set app_hdl [set ::sth::hlapiGen::$dcbx_app_tlv\_obj(app)]
                set appstruct_hdl_list [set ::sth::hlapiGen::$app_hdl\_obj(appstruct)]
                
                set attrlist "app_id oui_upper_6_bits sf oui_lower_2_bytes prio_map"
                foreach attr $attrlist {
                    set $attr\_list ""
                }
                set count [llength $appstruct_hdl_list]
                foreach appstruct_hdl $appstruct_hdl_list {
                    set app_id [set ::sth::hlapiGen::$app_hdl\_$appstruct_hdl\_attr(-appid)]
                    set oui_upper_6_bits [set ::sth::hlapiGen::$app_hdl\_$appstruct_hdl\_attr(-upperoui)]
                    set sf [set ::sth::hlapiGen::$app_hdl\_$appstruct_hdl\_attr(-sf)]
                    set oui_lower_2_bytes [set ::sth::hlapiGen::$app_hdl\_$appstruct_hdl\_attr(-loweroui)]
                    set prio_map [set ::sth::hlapiGen::$app_hdl\_$appstruct_hdl\_attr(-prioritymap)]
                    foreach attr $attrlist {
                        if {[set $attr] == "null"} {
                            switch -- $attr {
                                "app_id" {
                                    set app_id "8906"
                                }
                                "oui_upper_6_bits" {
                                    set oui_upper_6_bits "000000"
                                }
                                "sf" {
                                    set sf "00"
                                }
                                "oui_lower_2_bytes" {
                                    set oui_lower_2_bytes "1B21"
                                }
                                "prio_map" {
                                    set prio_map "00001000"
                                }
                            }
                        }
                        set $attr\_list [concat [set $attr\_list] [set $attr]]
                    }
                }
                foreach attr $attrlist {
                    array set dcbx_tlv_cfg_args_array "-app_protocol_tlv2_$attr\_list    \"[set $attr\_list]\""
                }
                array set dcbx_tlv_cfg_args_array  "-app_protocol_tlv2_protocol_count  $count" 
            
            }
            
            array set dcbx_tlv_cfg_args_array  "-$param_prefix\_tlv$version\_enable     1"
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_app_tlv $app_header $stcobj_app\-header]
        }
        
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(bcntlv)]} {
            set dcbx_bcn_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(bcntlv)]
            set bcn_header [set ::sth::hlapiGen::$dcbx_bcn_tlv\_obj(header)]
            array set dcbx_tlv_cfg_args_array  "-bcn_feature_tlv1_enable     1"
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_bcn_tlv $bcn_header TLV_DcbxBCN_Type1-header]
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_subtlv_hdl $dcbx_bcn_tlv TLV_DcbxBCN_Type1-bcnTlv]
            
            set attrlist "cp_admin rp_admin rp_oper rem_tag_oper"
            foreach attr $attrlist {
                set $attr\_list ""
            }
            #bound priority$iallocation attr into the list
            set bcn_mode [set ::sth::hlapiGen::$dcbx_bcn_tlv\_obj(bcnmode)]
            array set bcnmode_array [set ::sth::hlapiGen::$bcn_mode\_obj(bcnmode)]
            foreach bcn_mode_hdl [lsort -dictionary [array get bcnmode_array]] {
                if {[info exists ::sth::hlapiGen::$bcn_mode_hdl\_obj(bcnmode)]} {
                    set sub_bcn_mode_hdl [set ::sth::hlapiGen::$bcn_mode_hdl\_obj(bcnmode)]
                    set bcn_mode_update $bcn_mode_hdl
                    regsub {bcnmode} $bcn_mode_hdl "" num
                    regsub {[0-9]$} $bcn_mode_hdl "" var_prefix
                    set bcn_mode_hdl [append var_prefix $num]
                } else {
                    set bcn_mode_update $bcn_mode
                }
                set cp_admin [set ::sth::hlapiGen::$bcn_mode_update\_$bcn_mode_hdl\_attr(-cpadmin)]
                set rp_admin [set ::sth::hlapiGen::$bcn_mode_update\_$bcn_mode_hdl\_attr(-rpadmin)]
                set rp_oper [set ::sth::hlapiGen::$bcn_mode_update\_$bcn_mode_hdl\_attr(-rpoper)]
                set rem_tag_oper [set ::sth::hlapiGen::$bcn_mode_update\_$bcn_mode_hdl\_attr(-remtagoper)]
                
                foreach attr $attrlist {
                    if {[set $attr] == "null"} {
                        set $attr 0
                    }
                    set $attr\_list [concat [set $attr\_list] [set $attr]]
                }
            }
            foreach attr $attrlist {
                array set dcbx_tlv_cfg_args_array "-bcn_feature_tlv1_$attr\_mode_list    \"[set $attr\_list]\""
            }
            array unset bcnmode_array 
        }
        
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(logiclinkdowntlv)]} {
            set dcbx_lld_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(logiclinkdowntlv)]
            set lld_header [set ::sth::hlapiGen::$dcbx_lld_tlv\_obj(header)]
            set status [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_lld_tlv\_attr(-status)]
            
            array set dcbx_tlv_cfg_args_array  "-lld_feature_tlv1_enable     1"
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_lld_tlv $lld_header TLV_DcbxLLD_Type1-header]
            array set dcbx_tlv_cfg_args_array  "-lld_feature_tlv1_status_value     $status" 
        }
        
        if {[info exists ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(customtlv)]} {
            set dcbx_custom_tlv [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_obj(customtlv)]
            set custom_header [set ::sth::hlapiGen::$dcbx_custom_tlv\_obj(header)]
            set value [set ::sth::hlapiGen::$dcbx_subtlv_hdl\_$dcbx_custom_tlv\_attr(-value)]
            
            array set dcbx_tlv_cfg_args_array  "-customized_feature_tlv$version\_enable     1"
            append dcbx_tlv_cfg_args_header  [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $dcbx_custom_tlv $custom_header TLV_DcbxCustom_Type$version\-header]
            array set dcbx_tlv_cfg_args_array  "-customized_feature_tlv$version\_value     $value"
        }
    }
    
    if {[array names dcbx_tlv_cfg_args_array] != ""} {
        append dcbx_tlv_cfg_args "set $hlt_ret\_dcbx_tlv_config \[sth::$cmd_name\\\n"
        append dcbx_tlv_cfg_args $dcbx_tlv_cfg_args_header
        foreach attr [lsort [array names dcbx_tlv_cfg_args_array]] {
            set value $dcbx_tlv_cfg_args_array($attr)
            set value [null_to_default_value "::sth::Lldp::" $cmd_name $value $attr]
            append dcbx_tlv_cfg_args "$attr    $value\\\n"
        }
        append dcbx_tlv_cfg_args "\]\n"
        puts_to_file $dcbx_tlv_cfg_args
        gen_status_info $hlt_ret\_dcbx_tlv_config sth::$cmd_name
        
        append variable_cfg_args_local "set lldp_dcbx_tlv_hdl \[keylget $hlt_ret\_dcbx_tlv_config handle\]\n"
        append cfg_args_local "-dcbx_tlvs \$lldp_dcbx_tlv_hdl\\\n"
        
        #unset attrlist
        if {[info exists attrlist]} {
            unset attrlist
        }
        
        array unset dcbx_tlv_cfg_args_array
    }

}

proc ::sth::hlapiGen::process_bitstring {phdl hdl attr length type} {
    set bitstring ""
    
    for {set i 0} {$i < $length} {incr i} {
        set bit [set ::sth::hlapiGen::$phdl\_$hdl\_attr(-$attr$i)]
        if {$bit == "null"} {
            set bit 0
        }
        if {$type == "bitstring"} {
            append bitstring $bit
        } else {
            set bitstring [concat $bitstring $bit]
        }
        #append bitstring $bit
    }
    if {[llength $bitstring] > 1} {
        set bitstring \"$bitstring\"
    }
    return $bitstring
}

proc ::sth::hlapiGen::null_to_default_value {name_space cmd_name value attr} {
    # if the value is a list, check each value
    if {[llength $value] > 1 && [lsearch $value "null"] > -1} {
        set new_value ""
        foreach value_elem $value {
            if {[string match "null" $value_elem]} {
                regsub {^-} $attr "" attr
                set value_elem [set $name_space$cmd_name\_default($attr)]
            }
            set new_value [concat $new_value $value_elem]
        }
        set value $new_value
    }
    
    #if the value is null, used the default value of the table file instead
    if {$value == "null"} {
        regsub {^-} $attr "" attr
        set value [set $name_space$cmd_name\_default($attr)]
    }
    
    #if the length of the value if more than 1, add the ""
    if {[llength $value] > 1} {
        set value "\"$value\""
    }
    
    return $value
}

proc ::sth::hlapiGen::multi_dev_check_func_isis {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]     
    
    set attrlist "SystemId TeRouterID"
    foreach obj $update_obj {
        #call update-step to update the step value of bgprouterconfig obj
        if {[info exists devicelist_obj($obj)]} {
            update_step $class $devicelist_obj($obj) $attrlist ""
        }
    }   
    return $update_obj
}

proc ::sth::hlapiGen::multi_dev_check_func_ldp {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]     
    
    set attrlist "LabelMin DutIp DutIpv6"
    foreach obj $update_obj {
        #call update-step to update the step value of bgprouterconfig obj
        if {[info exists devicelist_obj($obj)]} {
            update_step $class $devicelist_obj($obj) $attrlist ""
        }
    }
    return $update_obj
}

proc ::sth::hlapiGen::hlapi_gen_device_lag {device class mode hlt_ret cfg_args first_time} {
    set mode "create"
    set port_lag $device
    set portoptions  [stc::get project1 -children-portoptions]
    set aggregatorresult [stc::get $portoptions -AggregatorResult] 
    append cfg_args "     -aggregatorresult    $aggregatorresult\\\n"
    set lag [stc::get $device -children-lag]
    set lag_name [stc::get $lag -name]
    regsub -all " " $lag_name "" lag_name
    append cfg_args "     -lag_name    $lag_name\\\n"
    set port_handle [stc::get $lag -PortSetMember-targets]
    set port_list ""
    foreach port $port_handle {
        append port_list "$::sth::hlapiGen::port_ret($port) "
    }
    append cfg_args "     -port_handle    $port_list\\\n"
    set lacpgroupconfig [stc::get $lag -children-lacpgroupconfig]
    if {$lacpgroupconfig ne ""} {
        append cfg_args "     -actor_system_priority    [stc::get $lacpgroupconfig -ActorSystemPriority]\\\n"
        append cfg_args "     -actor_system_id    [stc::get $lacpgroupconfig -ActorSystemId]\\\n"
        append cfg_args "     -protocol    lacp\\\n"
        set i 1
        foreach port $port_handle {
            set lacpportconfig [stc::get $port -children-lacpportconfig]
            set lacpportconfig [lindex $lacpportconfig 0]
            set ActorPort$i [stc::get $lacpportconfig -ActorPort]
            set ActorPortPriority$i [stc::get $lacpportconfig -ActorPortPriority]
            set ActorKey$i [stc::get $lacpportconfig -ActorKey]
            set LacpTimeout [stc::get $lacpportconfig -LacpTimeout]
            set LacpActivity [stc::get $lacpportconfig -LacpActivity]
            set host [stc::get $port -children-host]
            if {$host ne ""} {
                #handle  local_mac_addr-LacpGroupConfig-SourceMac
                set ethiiif [stc::get $host -children-ethiiif]
                if {$ethiiif ne ""} {
                    set lacp_port_mac_addr$i [stc::get $ethiiif -SourceMac]
                }
            }
            incr i
        }
        append cfg_args "     -lacp_port_mac_addr    $lacp_port_mac_addr1\\\n"
        append cfg_args "     -lacp_actor_key    $ActorKey1\\\n"
        set lacp_actor_key_step [expr $ActorKey2-$ActorKey1]
        append cfg_args "     -lacp_actor_key_step    $lacp_actor_key_step\\\n"
        append cfg_args "     -lacp_actor_port_number    $ActorPort1\\\n"
        set lacp_actor_port_step [expr $ActorPort2-$ActorPort1]
        append cfg_args "     -lacp_actor_port_step    $lacp_actor_port_step\\\n"
        append cfg_args "     -lacp_actor_port_priority    $ActorPortPriority1\\\n"
        set lacp_actor_port_priority_step [expr $ActorPortPriority2 -$ActorPortPriority1 ]
        append cfg_args "     -lacp_actor_port_priority_step    $lacp_actor_port_priority_step\\\n"
        append cfg_args "     -lacp_activity    $LacpActivity\\\n"
        append cfg_args "     -lacp_timeout    $LacpTimeout\\\n"
        set lacp_port_mac_addr1 [split $lacp_port_mac_addr1 :]
        set lacp_port_mac_addr2 [split $lacp_port_mac_addr2 :]
        set lacp_port_mac_addr_step ""
        for {set i 0} {$i<6} {incr i} {
            set step_lindex ""
            for {set j 0} {$j<2} {incr j} {
                append step_lindex [expr [string index [lindex $lacp_port_mac_addr2 $i] $j] - [string index [lindex $lacp_port_mac_addr1 $i] $j]]
            }
            lappend lacp_port_mac_addr_step $step_lindex
        }
        set lacp_port_mac_addr_step [join $lacp_port_mac_addr_step :]
        append cfg_args "     -lacp_port_mac_addr_step    $lacp_port_mac_addr_step\\\n"
    } else {
       append cfg_args "     -protocol    none\\\n"
    }
    set cfg_args  [string tolower $cfg_args]
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
    if {![regexp -nocase $port_lag [array names ::sth::hlapiGen::lagportconfigured]]} {
        set ::sth::hlapiGen::lagportconfigured($port_lag) $hlt_ret
        set index 0
        if {[regexp "\\d+"  $hlt_ret index ]} {
            puts_to_file "\nset lag_handle$index \[keylget $::sth::hlapiGen::lagportconfigured($port_lag) lag_handle\]\n"
            set ::sth::hlapiGen::port_ret($port_lag) "\$lag_handle$index"
            set ::sth::hlapiGen::handle_to_port(\$lag_handle$index) $port_lag                              
        }
    }
}
proc ::sth::hlapiGen::hlapi_gen_device_lacp {device class mode hlt_ret cfg_args first_time} {
    
    set mode "enable"
    set port $device
    append cfg_args "     -port_handle    \"$::sth::hlapiGen::port_ret($port) \"\\\n"
    
    set lacpportconfig [stc::get $port -children-lacpportconfig]
    set lacpportconfig [lindex $lacpportconfig 0]
    
    set host [stc::get $port -children-host]
    if {$host ne ""} {
        #handle  local_mac_addr-LacpGroupConfig-SourceMac
        set ethiiif [stc::get $host -children-ethiiif]
        if {$ethiiif ne ""} {
            append cfg_args "     -local_mac_addr    [stc::get $ethiiif -SourceMac]\\\n"
        }
    }
    
    set lacpgroupconfig [stc::get $lacpportconfig -memberoflag-Targets]
    if {$lacpgroupconfig ne ""} {
        #handle  act_system_priority-LacpGroupConfig-ActorSystemPriority
        #handle  act_system_id-LacpGroupConfig-ActorSystemId
        append cfg_args "     -act_system_priority    [stc::get $lacpgroupconfig -ActorSystemPriority]\\\n"
        append cfg_args "     -act_system_id    [stc::get $lacpgroupconfig -ActorSystemId]\\\n"
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}



proc ::sth::hlapiGen::hlapi_gen_device_l2tp {device class mode hlt_ret cfg_args first_time} {
    
    set mode ""
    append cfg_args [l2tp_pre_process $device $class]
    ::sth::sthCore::InitTableFromTCLList $::sth::l2tp::l2tpTable
    set name_space "::sth::l2tp::"
    set cmd_name "l2tp_config"
    
    #attempt_rate under PppoxPortConfig or L2tpPortConfig

    set $name_space$cmd_name\_stcobj(attempt_rate) "L2tpPortConfig"

    #in table, PppoL2tpBlockConfig, need to be changed to PppoL2tpv2ClientBlockConfig
    #or PppoL2tpv2ServerBlockConfig
    if {[info exists sth::hlapiGen::$device\_obj(pppol2tpv2serverblockconfig)]} {
        
        foreach arg [array names $name_space$cmd_name\_stcobj] {
            set obj [set $name_space$cmd_name\_stcobj($arg)]
            if {[regexp -nocase "PppoL2tpBlockConfig" $obj]} {
                set $name_space$cmd_name\_stcobj($arg) "PppoL2tpv2ServerBlockConfig"
            }
        }
        
    } else {
        foreach arg [array names $name_space$cmd_name\_stcobj] {
            set obj [set $name_space$cmd_name\_stcobj($arg)]
            if {[regexp -nocase "PppoL2tpBlockConfig" $obj]} {
                set $name_space$cmd_name\_stcobj($arg) "PppoL2tpv2ClientBlockConfig"
            }
        }
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

        
proc ::sth::hlapiGen::hlapi_gen_device_l2tpv3 {device class mode hlt_ret cfg_args first_time} {
    append cfg_args [l2tpv3_pre_process $device $class]
    ::sth::sthCore::InitTableFromTCLList $::sth::l2tpv3::l2tpv3Table
    set name_space "::sth::l2tpv3::"
    set cmd_name "l2tpv3_config"
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}
proc ::sth::hlapiGen::l2tpv3_pre_process {device class} {
    set cfg_args_local ""
    #mode
    #l2_encap
    if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanif [set sth::hlapiGen::$device\_obj(vlanif)]
        if {[llength $vlanif] > 1} {
            set l2_encap "ethernet_ii_qinq"
        } else {
            set l2_encap "ethernet_ii_vlan"
        }
    } else {
        set l2_encap "ethernet_ii"
    }
    append cfg_args_local "-l2_encap            $l2_encap\\\n"
    #echo_rsp
    set ipv4ifs [set sth::hlapiGen::$device\_obj(ipv4if)]
    foreach ipv4if $ipv4ifs {
        if {[info exists sth::hlapiGen::$device\_$ipv4if\_attr(-usesif-sources)]} {
            set useif [set sth::hlapiGen::$device\_$ipv4if\_attr(-usesif-sources)]
        }
        if {[info exists useif] } {
            set ipv4if_0 $ipv4if
        } else {
            set ipv4if_1 $ipv4if
        }
        if {[info exists useif]} {
            unset useif
        }
    }
    set count [set sth::hlapiGen::$device\_$device\_attr(-devicecount)]
    set ipv4if_1_addr [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-address)]
    set ipv4if_1_addr_step [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-addrstep)]
    set ipv4if_1_gateway [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-gateway)]
    set ipv4if_1_gateway_step [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-gatewaystep)]
    set port [set sth::hlapiGen::$device\_$device\_attr(-affiliationport-targets)]
    set l2tpport [set sth::hlapiGen::$port\_obj(l2tpportconfig)]
    set mode [set sth::hlapiGen::$port\_$l2tpport\_attr(-l2tpnodetype)]
    if {[regexp -nocase "lac" $mode]} {
        
        #when it is client, the l2tp_src_count is the device count,
        append cfg_args_local "-l2tpv3_src_count      $count\\\n"
        append cfg_args_local "-l2tpv3_src_addr      $ipv4if_1_addr\\\n"
        append cfg_args_local "-l2tpv3_src_step      $ipv4if_1_addr_step\\\n"
        append cfg_args_local "-l2tpv3_dst_addr      $ipv4if_1_gateway\\\n"
        append cfg_args_local "-l2tpv3_dst_step      $ipv4if_1_gateway_step\\\n"
    } elseif {[regexp -nocase "lns" $mode]} {
        append cfg_args_local "-l2tpv3_dst_count      $count\\\n"
        append cfg_args_local "-l2tpv3_src_addr      $ipv4if_1_gateway\\\n"
        append cfg_args_local "-l2tpv3_src_step      $ipv4if_1_gateway_step\\\n"
        append cfg_args_local "-l2tpv3_dst_addr      $ipv4if_1_addr\\\n"
        append cfg_args_local "-l2tpv3_dst_step      $ipv4if_1_addr_step\\\n"
       
    }

    set name_password ""
    set l2tpblock [set sth::hlapiGen::$device\_obj(l2tpv3blockconfig)]
    set remote_ipv4addr [stc::get $l2tpblock -UseGatewayAsRemoteIpv4Addr]
    set remote_ipv6addr [stc::get $l2tpblock -UseGatewayAsRemoteIpv6Addr]
    if {!$remote_ipv4addr} {
        set Ipv4NetworkBlock [stc::get $l2tpblock -children-Ipv4NetworkBlock]
        append cfg_args_local "-remote_ipv4addr      [stc::get $Ipv4NetworkBlock -StartIpList]\\\n"
    }
    if {!$remote_ipv6addr} {
        set Ipv6NetworkBlock [stc::get $l2tpblock -children-Ipv6NetworkBlock]
        append cfg_args_local "-remote_ipv6addr      [stc::get $Ipv6NetworkBlock -StartIpList]\\\n"
    }
    set L2tpv3SessionBlockParams [stc::get $l2tpblock -children-L2tpv3SessionBlockParams]
    if {$L2tpv3SessionBlockParams ne ""} {
        append cfg_args_local "-pseudowire_type      [stc::get $L2tpv3SessionBlockParams -PseudowireType]\\\n"
        append cfg_args_local "-remote_end_id_start      [stc::get $L2tpv3SessionBlockParams -RemoteEndIdStart]\\\n"
        append cfg_args_local "-remote_end_id_step      [stc::get $L2tpv3SessionBlockParams -RemoteEndIdStep]\\\n"
        append cfg_args_local "-session_count      [stc::get $L2tpv3SessionBlockParams -SessionCount]\\\n"
    } 
    set hostname [set sth::hlapiGen::$device\_$l2tpblock\_attr(-hostname)]
    set name_password [concat $name_password $hostname]
    set secret [set sth::hlapiGen::$device\_$l2tpblock\_attr(-txtunnelpassword)]
    set name_password [concat $name_password $secret]
    #get the @x() in the username and the password
    #{# pound} {? question} {! bang} {$ dollar}
    set pound_list ""
    set question_list ""
    set bang_list ""
    set dollar_list ""
    set wildcard_list ""
    if {[regexp {@x\([0-9,]+\)} $hostname]} {
        append cfg_args_local "          -hostname_wc 1\\\n"
            }
    if {[regexp {@x\([0-9,]+\)} $secret]} {
        append cfg_args_local "          -secret_wc 1\\\n"
    }
    while (1) {
        if {[regexp {@x\([0-9,]+\)} $name_password wildcard]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub -all $wildcard $name_password "#" name_password
            set wildcard_list [concat $wildcard_list $wildcard]
        } else {
            break
        }
    }
    
    if {[llength $wildcard_list]>4} {
        set wildcard_list [lrange $wildcard_list 0 3]
    }
    foreach wildcard $wildcard_list {
        if {[regexp {^$} $pound_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub -all $wildcard $hostname "" hostname
            regsub $wildcard $secret "#" secret
            set cfg_string [process_wildcard pound $wildcard]
            append cfg_args_local $cfg_string
            set pound_list "#"
            #wildcard_pound_end, wildcard_pound_fill, wildcard_pound_start
        } elseif {[regexp {^$} $question_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $hostname "?" hostname
            regsub $wildcard $secret "?" secret
            set cfg_string [process_wildcard question $wildcard]
            append cfg_args_local $cfg_string
            set question_list "?"
            #wildcard_question_end, wildcard_question_start, wildcard_question_fill
        } elseif {[regexp {^$} $bang_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $hostname "!" hostname
            regsub $wildcard $secret "!" secret
            set cfg_string [process_wildcard bang $wildcard]
            append cfg_args_local $cfg_string
            set bang_list "!"
            #wildcard_bang_start, wildcard_bang_end, wildcard_bang_fill
        } else {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $hostname "$" hostname
            regsub $wildcard $secret "$" secret
            set cfg_string [process_wildcard dollar $wildcard]
            append cfg_args_local $cfg_string
            #wildcard_dollar_start, wildcard_dollar_end, wildcard_dollar_fill
        }
    }
    set sth::hlapiGen::$device\_$l2tpblock\_attr(-hostname) $hostname
    set sth::hlapiGen::$device\_$l2tpblock\_attr(-secret) $secret
    set cfg_args_local [string tolower $cfg_args_local]
   return $cfg_args_local
}


proc ::sth::hlapiGen::l2tp_pre_process {device class} {
    
    set cfg_args_local ""
    #mode
    #l2_encap
    if {[info exists sth::hlapiGen::$device\_obj(aal5if)]} {
        set aal5if [set sth::hlapiGen::$device\_obj(aal5if)]
        set vc_encp [set sth::hlapiGen::$device\_$aal5if\_attr(-vcencapsulation)]
        if {[regexp -nocase "VC_MULTIPLEXED" $vc_encp]} {
            set l2_encap "atm_vc_mux" 
        } else {
            set l2_encap "atm_snap"
        }
    } else {
        if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {
            set vlanif [set sth::hlapiGen::$device\_obj(vlanif)]
            if {[llength $vlanif] > 1} {
                set l2_encap "ethernet_ii_qinq"
            } else {
                set l2_encap "ethernet_ii_vlan"
            }
        } else {
            set l2_encap "ethernet_ii"
        }
    }
    append cfg_args_local "-l2_encap            $l2_encap\\\n"
    #echo_rsp
    
    #l2tp_dst_addr
    #l2tp_dst_count
    #l2tp_dst_step
    #l2tp_src_addr
    #l2tp_src_count
    #l2tp_src_step
    #ppp_server_ip
    #ppp_server_step
    set ipv4ifs [set sth::hlapiGen::$device\_obj(ipv4if)]
    foreach ipv4if $ipv4ifs {
        if {[info exists sth::hlapiGen::$device\_$ipv4if\_attr(-usesif-sources)]} {
            set useif [set sth::hlapiGen::$device\_$ipv4if\_attr(-usesif-sources)]
            
        }
        if {[info exists useif] && [regexp -nocase "pppol2tpv2" $useif]} {
            set ipv4if_0 $ipv4if
            
        } else {
            set ipv4if_1 $ipv4if
        }
        if {[info exists useif]} {
            unset useif
        }
    }
    set count [set sth::hlapiGen::$device\_$device\_attr(-devicecount)]
    set ipv4if_1_addr [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-address)]
    set ipv4if_1_addr_step [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-addrstep)]
    set ipv4if_1_gateway [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-gateway)]
    set ipv4if_1_gateway_step [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-gatewaystep)]
    
    set port [set sth::hlapiGen::$device\_$device\_attr(-affiliationport-targets)]
    set l2tpport [set sth::hlapiGen::$port\_obj(l2tpportconfig)]
    set mode [set sth::hlapiGen::$port\_$l2tpport\_attr(-l2tpnodetype)]
    if {[regexp -nocase "lac" $mode]} {
        if {[info exists sth::hlapiGen::$device\_obj(pppol2tpv2clientblockconfig)]} {
            set l2tp_client_server_block [set sth::hlapiGen::$device\_obj(pppol2tpv2clientblockconfig)]
        }
        
        #when it is client, the l2tp_src_count is the device count,
        append cfg_args_local "-l2tp_src_count      $count\\\n"
        append cfg_args_local "-l2tp_src_addr      $ipv4if_1_addr\\\n"
        append cfg_args_local "-l2tp_src_step      $ipv4if_1_addr_step\\\n"
        append cfg_args_local "-l2tp_dst_addr      $ipv4if_1_gateway\\\n"
        append cfg_args_local "-l2tp_dst_step      $ipv4if_1_gateway_step\\\n"
        
        
    } elseif {[regexp -nocase "lns" $mode]} {
        if {[info exists sth::hlapiGen::$device\_obj(pppol2tpv2serverblockconfig)]} {
            set l2tp_client_server_block [set sth::hlapiGen::$device\_obj(pppol2tpv2serverblockconfig)]
        }
        # the l2tp_dst_count is the device count,
        append cfg_args_local "-l2tp_dst_count      $count\\\n"
        append cfg_args_local "-l2tp_src_addr      $ipv4if_1_gateway\\\n"
        append cfg_args_local "-l2tp_src_step      $ipv4if_1_gateway_step\\\n"
        append cfg_args_local "-l2tp_dst_addr      $ipv4if_1_addr\\\n"
        append cfg_args_local "-l2tp_dst_step      $ipv4if_1_addr_step\\\n"
        #when it is server, the ppp_server_ip and ppp_server_step will be ouput
        if {[info exists ipv4if_0]} {
            set ipv4if_0_addr [set sth::hlapiGen::$device\_$ipv4if_0\_attr(-address)]
            set ipv4if_0_addr_step [set sth::hlapiGen::$device\_$ipv4if_1\_attr(-addrstep)]
            append cfg_args_local "-ppp_server_ip       $ipv4if_0_addr\\\n"
            append cfg_args_local "-ppp_server_step     $ipv4if_0_addr_step\\\n"
        }
    }
    
    #secret
    #secret_wc
    #password_wc
    #username_wc
    #hostname_wc
    
    #wildcard_bang_end
    #wildcard_bang_start
    #wildcard_dollar_end
    #wildcard_dollar_start
    #wildcard_pound_end
    #wildcard_pound_start
    #wildcard_question_end
    #wildcard_question_start
    set name_password ""
    set l2tpblock [set sth::hlapiGen::$device\_obj(l2tpv2blockconfig)]
    
    if {[info exists l2tp_client_server_block]} {
        set username [set sth::hlapiGen::$device\_$l2tp_client_server_block\_attr(-username)]
        set password [set sth::hlapiGen::$device\_$l2tp_client_server_block\_attr(-password)]
        set name_password [concat $username $password]
    }
    
    set hostname [set sth::hlapiGen::$device\_$l2tpblock\_attr(-hostname)]
    set name_password [concat $name_password $hostname]
    set secret [set sth::hlapiGen::$device\_$l2tpblock\_attr(-rxtunnelpassword)]
    set name_password [concat $name_password $secret]
    #get the @x() in the username and the password
    #{# pound} {? question} {! bang} {$ dollar}
    set pound_list ""
    set question_list ""
    set bang_list ""
    set dollar_list ""
    
    set wildcard_list ""
    
    if {[info exists username] && [regexp {@x\([0-9,]+\)} $username]} {
        append cfg_args_local "          -username_wc 1\\\n"
    }
    if {[info exists password] && [regexp {@x\([0-9,]+\)} $password]} {
        append cfg_args_local "          -password_wc 1\\\n"
    }
    
    if {[regexp {@x\([0-9,]+\)} $hostname]} {
        append cfg_args_local "          -hostname_wc 1\\\n"
    }
    if {[regexp {@x\([0-9,]+\)} $secret]} {
        append cfg_args_local "          -secret_wc 1\\\n"
    }
    
    while (1) {
        
        if {[regexp {@x\([0-9,]+\)} $name_password wildcard]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            
            regsub -all $wildcard $name_password "#" name_password
            set wildcard_list [concat $wildcard_list $wildcard]
        } else {
            break
        }
    }
    
    if {[llength $wildcard_list]>4} {
        set wildcard_list [lrange $wildcard_list 0 3]
    }
    foreach wildcard $wildcard_list {
        if {[regexp {^$} $pound_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "#" username
            regsub $wildcard $password "#" password
            regsub $wildcard $hostname "#" hostname
            regsub $wildcard $secret "#" secret
            set cfg_string [process_wildcard pound $wildcard]
            append cfg_args_local $cfg_string
            set pound_list "#"
            #wildcard_pound_end, wildcard_pound_fill, wildcard_pound_start
        } elseif {[regexp {^$} $question_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "?" username
            regsub $wildcard $password "?" password
            regsub $wildcard $hostname "?" hostname
            regsub $wildcard $secret "?" secret
            set cfg_string [process_wildcard question $wildcard]
            append cfg_args_local $cfg_string
            set question_list "?"
            #wildcard_question_end, wildcard_question_start, wildcard_question_fill
        } elseif {[regexp {^$} $bang_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "!" username
            regsub $wildcard $password "!" password
            regsub $wildcard $hostname "!" hostname
            regsub $wildcard $secret "!" secret
            set cfg_string [process_wildcard bang $wildcard]
            append cfg_args_local $cfg_string
            set bang_list "!"
            #wildcard_bang_start, wildcard_bang_end, wildcard_bang_fill
        } else {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "$" username
            regsub $wildcard $password "$" password
            regsub $wildcard $hostname "$" hostname
            regsub $wildcard $secret "$" secret
            set cfg_string [process_wildcard dollar $wildcard]
            append cfg_args_local $cfg_string
            #wildcard_dollar_start, wildcard_dollar_end, wildcard_dollar_fill
        }
    }
    
    if {[info exists l2tp_client_server_block]} {
        set sth::hlapiGen::$device\_$l2tp_client_server_block\_attr(-username) $username
        set sth::hlapiGen::$device\_$l2tp_client_server_block\_attr(-password) $password
        
    }
    set sth::hlapiGen::$device\_$l2tpblock\_attr(-hostname) $hostname
    set sth::hlapiGen::$device\_$l2tpblock\_attr(-secret) $secret

    if {[info exists sth::hlapiGen::$device\_obj(pppol2tpv2serverblockconfig)]} {
        #config the args under PppoxServerIpv4PeerPool
        set ipv4peerpool [set sth::hlapiGen::$l2tp_client_server_block\_obj(pppoxserveripv4peerpool)]
        #ppp_client_ip StartIpList
        set ppp_client_ip [set sth::hlapiGen::$l2tp_client_server_block\_$ipv4peerpool\_attr(-startiplist)]
        #ppp_client_step  AddrIncrement
        set ppp_client_step [set sth::hlapiGen::$l2tp_client_server_block\_$ipv4peerpool\_attr(-addrincrement)]
        append cfg_args_local "-ppp_client_ip       $ppp_client_ip\\\n"
        set ppp_client_step [intToIpv4Address $ppp_client_step]
        append cfg_args_local "-ppp_client_step       $ppp_client_step\\\n"
    }
    return $cfg_args_local
}

#--------------------------------------------------------------------------------------------------------#
#ipv6 Auto config convert function, it is used to generate the hltapi emulation_ipv6_autoconfig function
#input:     device      =>  the port on which the interface config function will be used
#           calss       =>  the class name
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#           cfg_args    => the args prepared earlier for the Ipv6 Auto config function
#           first_time  => is this the first time to config the protocol on this device
#output:    the genrated hltapi emulation_ipv6_autoconfig funtion will be output to the file.
proc ::sth::hlapiGen::hlapi_gen_device_ipv6autoconfig {device class mode hlt_ret cfg_args first_time} {

    set table_name "::sth::Ipv6AutoConfig::ipv6AutoConfigTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_ipv6_autoconfig

    #DAD parameters
    if {[info exists ::sth::hlapiGen::$device\_obj(saadeviceconfig)]} {
        set ipv6AutoConfig [set ::sth::hlapiGen::$device\_obj(saadeviceconfig)]
        set dad [set ::sth::hlapiGen::$device\_$ipv6AutoConfig\_attr(-dupaddrdetection)]
        if {[regexp -nocase "false" $dad]} {
            set attr_list "dad_enable dad_transmit_count dad_retransmit_delay"
            foreach attr $attr_list {
            set $name_space$cmd_name\_stcobj($attr) "_none_"
            }
        }
    }

    #handle stcobj for count
    regsub {\d+$} $device "" update_obj
    set $name_space$cmd_name\_stcobj(count) "$update_obj"

    #ip_version
    set ip_version 6
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        set ip_version 4_6
    }
    append cfg_args "-ip_version        $ip_version\\\n"
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        if {[llength [set sth::hlapiGen::$device\_obj(vlanif)]] > 1} {
            append cfg_args "-encap        ethernet_ii_qinq\\\n"
        } else {
            append cfg_args "-encap        ethernet_vlan\\\n"
        }
    } else {
        append cfg_args "-encap        ethernet_ii\\\n"
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::multi_dev_check_func_igmp {class devices} {
    variable devicelist_obj
    #need to check if there is two vlan on every device, only when there is two vlan
    #hltapi will create multiple device block in one config function.
    array unset device_array
    array set device_array {}
    set device_list ""
    set dev_indx 0
    foreach device $devices {
        if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
            set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
            if {[llength $vlanifs] > 1} {
                set device_list [concat $device_list $device]
            } else {
                return -code error "no need to do the scaling when igmp have only one vlan";
                if {$device_list != ""} {
                    set device_array($dev_indx) $device_list
                    incr dev_indx
                    set device_list ""
                }
                set device_array($dev_indx) $device
                incr dev_indx
            }
        } else {
            return -code error "no need to do the scaling when igmp don't have vlan";
            set device_array($dev_indx) $device
            incr dev_indx
        }
        
    }

    set update_obj ""
    if {[llength [array names device_array]] == [llength $devices]} {
        #no need to update the obj, only return all the objs
        foreach device $devices {
            set update_obj [concat $update_obj [set ::sth::hlapiGen::$device\_obj($class)]]
        }
        return $update_obj
    }
    
    
    if {$dev_indx == 0} {
        set update_obj [multi_dev_check_func_basic $class $devices]
    } else {
        foreach index [array names device_array] {
            set devices [set device_array($index)]
            set update_obj [concat $update_obj [multi_dev_check_func_basic $class $devices]]
        }
    }
    return $update_obj
}
#######################################################################################
#http client
#######################################################################################
proc ::sth::hlapiGen::hlapi_gen_device_httpconfigclient {device class mode hlt_ret cfg_args first_time} {
    variable $device\_obj
    variable profile_to_http
    variable devices_to_httphandle
    set table_name "::sth::http::httpTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_http_config

    if {[info exists ::sth::hlapiGen::$device\_obj(httpclientprotocolconfig)]} {
        set httpclientprotocolconfig [set ::sth::hlapiGen::$device\_obj(httpclientprotocolconfig)]
        append cfg_args "-http_type        client\\\n"
       
        ##process for clientprofile
        if {[info exists ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-affiliatedclientprofile-targets)]} {
            set clientprofile [set ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-affiliatedclientprofile-targets)]
            
            if {[info exists profile_to_http($clientprofile)]} {
                set hlt_returnval $profile_to_http($clientprofile)
                puts_to_file "set clientprofilehandle \[keylget $hlt_returnval client_profile_handle\] "
                append cfg_args "-client_profiles        \$clientprofilehandle\\\n"
            } else {               
                set profile_to_http($clientprofile) $hlt_ret\_clientprofile
                sth::hlapiGen::get_attr $clientprofile $clientprofile
                set retclientprofile [http_profile_client $clientprofile $name_space $hlt_ret\_clientprofile]
                append cfg_args "-client_profiles        \$$retclientprofile\\\n"
            }                               
        }
        #process for clientloadprofile 
        if {[info exists ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-affiliatedclientloadprofile-targets)]} {
            set loadprofile [set ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-affiliatedclientloadprofile-targets)]
            if {[info exists profile_to_http($loadprofile)]} {
                set hlt_returnval $profile_to_http($loadprofile)
                puts_to_file "set loadprofilehandle \[keylget $hlt_returnval load_profile_handle\] "
                append cfg_args "-load_profiles        \$loadprofilehandle\\\n"
            } else {               
                set profile_to_http($loadprofile) $hlt_ret\_loadprofile
                sth::hlapiGen::get_attr $loadprofile $loadprofile
                set retloadprofile [http_profile_load $loadprofile $name_space $hlt_ret\_loadprofile]
                append cfg_args "-load_profiles        \$$retloadprofile\\\n"
            }    
        }
            
        #To get device_handle for device_handle
        if {[info exists ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-parent)]} {
            set rawdevicehandle [set ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-parent)]
            #To get device_handle
            if {[info exists ::sth::hlapiGen::device_ret($rawdevicehandle)]} {
                set handle [lindex $::sth::hlapiGen::device_ret($rawdevicehandle) 0]
                set handle_indx [lindex $::sth::hlapiGen::device_ret($rawdevicehandle) 1]
                set key_values [update_key_value_device device $rawdevicehandle ]
                puts_to_file "set devicehandle1 \[lindex \[keylget $handle $key_values\] $handle_indx\] "
                append cfg_args "-device_handle        \$devicehandle1\\\n"
            }
        }
        #To get device_handle for connected_server
        if {[info exists ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-connectiondestination-targets)]} {
            set httpserverprotocolconfiglist [set ::sth::hlapiGen::$device\_$httpclientprotocolconfig\_attr(-connectiondestination-targets)]
            set httpserverprotocolconfig [lindex $httpserverprotocolconfiglist 0]
            set serverdevicehandle [stc::get $httpserverprotocolconfig -parent]
            #To get device_handle
            if {[info exists ::sth::hlapiGen::device_ret($serverdevicehandle)]} {
                set handle [lindex $::sth::hlapiGen::device_ret($serverdevicehandle) 0]
                set handle_indx [lindex $::sth::hlapiGen::device_ret($serverdevicehandle) 1]
                set key_values [update_key_value_device device $serverdevicehandle ]
                puts_to_file "set devicehandle2 \[lindex \[keylget $handle $key_values\] $handle_indx\] "
                append cfg_args "-connected_server        \$devicehandle2\\\n"
            }
        }   
    }
   
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
            append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    } 
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script $cfg_args
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    if {[info exists devices_to_httphandle($class)]} {
        lappend devices_to_httphandle($class) "$hlt_ret"
    } else {
        set devices_to_httphandle($class) $hlt_ret
    }
}

#######################################################################################
#http server
#######################################################################################
proc ::sth::hlapiGen::hlapi_gen_device_httpconfigserver {device class mode hlt_ret cfg_args first_time} {
    variable $device\_obj
    variable profile_to_http
    variable devices_to_httphandle
    set table_name "::sth::http::httpTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_http_config

    if {[info exists ::sth::hlapiGen::$device\_obj(httpserverprotocolconfig)]} {
        set httpserverprotocolconfig [set ::sth::hlapiGen::$device\_obj(httpserverprotocolconfig)]
        append cfg_args "-http_type        server\\\n"       
        
        #process for serverprofile
        if {[info exists ::sth::hlapiGen::$device\_$httpserverprotocolconfig\_attr(-affiliatedserverprofile-targets)]} {
            set serverprofile [set ::sth::hlapiGen::$device\_$httpserverprotocolconfig\_attr(-affiliatedserverprofile-targets)]
            if {[info exists profile_to_http($serverprofile)]} {
                set hlt_returnval $profile_to_http($serverprofile)
                puts_to_file "set serverprofilehandle \[keylget $hlt_returnval server_profile_handle\] "
                append cfg_args "-server_profiles        \$serverprofilehandle\\\n"
            } else {               
                set profile_to_http($serverprofile) $hlt_ret\_serverprofile
                sth::hlapiGen::get_attr $serverprofile $serverprofile
                set retserverprofile [http_profile_server $serverprofile $name_space $hlt_ret\_serverprofile]
                append cfg_args "-server_profiles        \$$retserverprofile\\\n"                    
            } 
        }
        if {[info exists ::sth::hlapiGen::$device\_$httpserverprotocolconfig\_attr(-parent)]} {
            set rawdevicehandle [set ::sth::hlapiGen::$device\_$httpserverprotocolconfig\_attr(-parent)]
            #To get device_handle
            if {[info exists ::sth::hlapiGen::device_ret($rawdevicehandle)]} {
                set handle [lindex $::sth::hlapiGen::device_ret($rawdevicehandle) 0]
                set handle_indx [lindex $::sth::hlapiGen::device_ret($rawdevicehandle) 1]
                set key_values [update_key_value_device device $rawdevicehandle ]
                puts_to_file "set devicehandle1 \[lindex \[keylget $handle $key_values\] $handle_indx\] "
                append cfg_args "-device_handle        \$devicehandle1\\\n"
            }
        } 
    } 
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    } 
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script $cfg_args
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    if {[info exists devices_to_httphandle($class)]} {
        lappend devices_to_httphandle($class) "$hlt_ret"
    } else {
        set devices_to_httphandle($class) $hlt_ret
    }
}

proc ::sth::hlapiGen::http_profile_server {device name_space hlt_ret} {
    variable $device\_obj
    set class httpserverprotocolprofile
    set cmd_name emulation_http_profile_config
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    }
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-profilename)]} {
        set profilename [set ::sth::hlapiGen::$device\_$device\_attr(-profilename)]
        regsub -all \\s+ $profilename _ profilename
        append cfg_args "			-profile_name			    $profilename\\\n"
    }
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_type	            server\\\n"
    #for serverprofile
    set class serverprofile
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    
    #for httpserverprotocolprofile
    set class httpserverprotocolprofile
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    
    #for httpserverresponseconfig
    set class httpserverresponseconfig  
    set temp_obj_handle $obj_handle  
    variable $temp_obj_handle\_obj
    set obj_handle [set $temp_obj_handle\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $temp_obj_handle $obj_handle $class]
    
    
    append hlapi_script $cfg_args
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    puts_to_file "set serverprofilehandle \[keylget $hlt_ret server_profile_handle\] "
    return serverprofilehandle
}

proc ::sth::hlapiGen::http_profile_client {device name_space hlt_ret} {
    variable $device\_obj
    set class httpclientprotocolprofile
    set cmd_name emulation_http_profile_config
    set cfg_args ""
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    }
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-profilename)]} {
        set profilename [set ::sth::hlapiGen::$device\_$device\_attr(-profilename)]
        regsub -all \\s+ $profilename _ profilename
        append cfg_args "			-profile_name			    $profilename\\\n"
    }
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_type	            client\\\n"
    
    #for clientprofile
    set class clientprofile
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    
    set class httpclientprotocolprofile
    append hlapi_script $cfg_args
    set obj_handle [set $device\_obj($class) ]
    if {[info exists ::sth::hlapiGen::$device\_$obj_handle\_attr(-useragentheader)]} {
        set ::sth::hlapiGen::$device\_$obj_handle\_attr(-useragentheader) "\"\""
    }
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    puts_to_file "set clientprofilehandle \[keylget $hlt_ret client_profile_handle\] "
    return clientprofilehandle
}

proc ::sth::hlapiGen::http_profile_load {device name_space hlt_ret} {
    variable $device\_obj
    set class clientloadprofile
    set cmd_name emulation_http_profile_config
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    }
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-profilename)]} {
        set profilename [set ::sth::hlapiGen::$device\_$device\_attr(-profilename)]
        regsub -all \\s+ $profilename _ profilename
        set ::sth::hlapiGen::$device\_$device\_attr(-profilename) $profilename
    }
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_type	            load\\\n"
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    puts_to_file "set loadprofilehandle \[keylget $hlt_ret load_profile_handle\] "
    
    #for emulation_http_phase_config
    if {[info exists ::sth::hlapiGen::$device\_obj(clientloadphase)]} {
        set phaselist [set ::sth::hlapiGen::$device\_obj(clientloadphase)]
        set phasenum 0
        foreach phase $phaselist {
            http_phase_load $device $phase $hlt_ret\_$phasenum $name_space
            incr phasenum
        }
    }
    return loadprofilehandle
}
proc ::sth::hlapiGen::http_phase_load {device phase_handle hlt_ret name_space} {
    set class clientloadphase
    set cmd_name emulation_http_phase_config
    set cfg_args ""
   
    set phasetype [array names ::sth::hlapiGen::$phase_handle\_obj]
    set phasetypehandle [set ::sth::hlapiGen::$phase_handle\_obj($phasetype)]
    
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-height)]} {
        set height [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-height)]
        append cfg_args "			-height			    $height\\\n"
    }
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-ramptime)]} {
        set ramp_time [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-ramptime)]
        append cfg_args "			-ramp_time			    $ramp_time\\\n"
    }
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-steadytime)]} {
        set steady_time [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-steadytime)]
        append cfg_args "			-steady_time			    $steady_time\\\n"
    }
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-repetitions)]} {
        set repetitions [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-repetitions)]
        append cfg_args "			-repetitions			    $repetitions\\\n"
    }
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-bursttime)]} {
        set burst_time [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-bursttime)]
        append cfg_args "			-burst_time			    $burst_time\\\n"
    }
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-pausetime)]} {
        set pause_time [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-pausetime)]
        append cfg_args "			-pause_time			    $pause_time\\\n"
    }
    if {[info exists ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-period)]} {
        set period [set ::sth::hlapiGen::$phase_handle\_$phasetypehandle\_attr(-period)]
        append cfg_args "			-period			    $period\\\n"
    }
    
    
    if {[info exists ::sth::hlapiGen::$device\_$phase_handle\_attr(-phasename)]} {
        set phasename [set ::sth::hlapiGen::$device\_$phase_handle\_attr(-phasename)]
        regsub -all \\s+ $phasename _ phasename
        set ::sth::hlapiGen::$device\_$phase_handle\_attr(-phasename) $phasename
    }
    
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    }
    
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_handle	            \$loadprofilehandle  \\\n"
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $phase_handle $class]
    append hlapi_script $cfg_args
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
}
#this function is used to update the key value for the returned keyedlist
proc ::sth::hlapiGen::update_key_value_device {type hdl} {
    variable protocol_to_devices
    set return_key "handle"
    if {$type == "device"} {
        set devicehdl $hdl
        array set hltapi_obj_temp [array get ::sth::hlapiGen::$devicehdl\_obj]
        set class_list [array names hltapi_obj_temp]
        foreach class $class_list {
            if {[info exists ::sth::hlapiGen::protocol_to_devices($class)]} {
                if {[regexp -nocase $devicehdl $::sth::hlapiGen::protocol_to_devices($class)]} {
                    set class_created_device $class
                    break
                }
            }
        }
        switch -regexp -- $class_created_device {
            "dhcpv4serverconfig" {
                set return_key "handle.dhcp_handle"
            }
            "dhcpv6serverconfig" {
                set return_key "handle.dhcpv6_handle"
            }
            "dhcpv6blockconfig|dhcpv6pdblockconfig" {
                set return_key "dhcpv6_handle"
            }
        }
    }   
    return $return_key
}


#######################################
##function for save as emulation_device_config 
#######################################
proc ::sth::hlapiGen::hlapi_gen_device_deviceconfig {device class mode hlt_ret cfg_args first_time} {

    set table_name "::sth::device::deviceTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_device_config 


    #ip_version
    set ip_version "none"
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)] } {
        set ip_version "ipv4"
    }
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv6if)] } {
        set ip_version "ipv6" 
    }
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)] && [info exists ::sth::hlapiGen::$device\_obj(ipv6if)] } {
        set ip_version "ipv46"
    }
    if { $ip_version != "" } {
        append cfg_args "-ip_version        $ip_version\\\n"
    }
    if { $class == "host" } {
        if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-devicecount)]} {
            set devicecount [set ::sth::hlapiGen::$device\_$device\_attr(-devicecount)]
            append cfg_args "-count        $devicecount\\\n"
            unset ::sth::hlapiGen::$device\_$device\_attr(-devicecount)
        }
        if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-routerid)]} {
            set routerid [set ::sth::hlapiGen::$device\_$device\_attr(-routerid)]
            append cfg_args "-router_id        $routerid\\\n"
            unset ::sth::hlapiGen::$device\_$device\_attr(-routerid)
        }
        if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-enablepingresponse)]} {
            set enablepingresponse [set ::sth::hlapiGen::$device\_$device\_attr(-enablepingresponse)]
            if { $enablepingresponse == "true" } {
                append cfg_args "-enable_ping_response        1\\\n"
            } else {
                append cfg_args "-enable_ping_response        0\\\n"
            }
            unset ::sth::hlapiGen::$device\_$device\_attr(-enablepingresponse)
        }
    }
    #For router_id_ipv6
    if {$ip_version == "ipv46"  || $ip_version == "ipv6" } {
        if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-ipv6routerid)]} {
            set ipv6routerid [set ::sth::hlapiGen::$device\_$device\_attr(-ipv6routerid)]
            append cfg_args "-router_id_ipv6        $ipv6routerid\\\n"
            unset ::sth::hlapiGen::$device\_$device\_attr(-ipv6routerid)
        }   
    } else {
        unset ::sth::hlapiGen::$device\_$device\_attr(-ipv6routerid)
    }
    #For gatewayMac
    if {$ip_version == "ipv4" || $ip_version == "ipv46"} {
        set ipv4handle [ lindex [set ::sth::hlapiGen::$device\_obj(ipv4if)] 0 ]
        if { [set ::sth::hlapiGen::$device\_$ipv4handle\_attr(-gatewaymac)] == "00:00:01:00:00:01" } {
            unset ::sth::hlapiGen::$device\_$ipv4handle\_attr(-gatewaymac)
        }
    }
    if { $ip_version == "ipv6" || $ip_version == "ipv46" } {
        set ipv6handle [ lindex [set ::sth::hlapiGen::$device\_obj(ipv6if)] 0 ]
        if { [set ::sth::hlapiGen::$device\_$ipv6handle\_attr(-gatewaymac)] == "00:00:01:00:00:01" } {
            unset ::sth::hlapiGen::$device\_$ipv6handle\_attr(-gatewaymac)
        }
    }
    #For encapsulation
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        if {[llength [set sth::hlapiGen::$device\_obj(vlanif)]] > 1} {
            append cfg_args "-encapsulation        ethernet_ii_qinq\\\n"
        } else {
            append cfg_args "-encapsulation        ethernet_ii_vlan\\\n"
        }
    } else {
        append cfg_args "-encapsulation        ethernet_ii\\\n"
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}


proc ::sth::hlapiGen::hlapi_gen_device_iptvconfig {device class mode hlt_ret cfg_args first_time} {

    set table_name "::sth::iptv::iptvTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_iptv_config

    #pre-process
    # need to create the channel block, view profile and channel profiles
    #check the channel profile
    set iptvStbBlock [set sth::hlapiGen::$device\_obj($class)]
    set viewedChannels [set sth::hlapiGen::$device\_$iptvStbBlock\_attr(-stbchannel-targets)]
    set j 0
    set viewed_channel_handle ""
    foreach viewedChannel $viewedChannels {
        if {![info exists sth::hlapiGen::device_ret($viewedChannel)]} {
            sth::hlapiGen::get_attr $viewedChannel $viewedChannel
            # check the channel block
            set channel_block [set sth::hlapiGen::$viewedChannel\_$viewedChannel\_attr(-channelblock)]
            if {![info exists sth::hlapiGen::device_ret($channel_block)]} {
                sth::hlapiGen::get_attr $channel_block $channel_block
                #need to check the ipv4group or the ipv6group
                set muticastgroups [set sth::hlapiGen::$channel_block\_$channel_block\_attr(-multicastparam-targets)]
                set muticastgroup_handle ""
                foreach muticastgroup $muticastgroups {
                    if {![info exists sth::hlapiGen::device_ret($muticastgroup)]} {
                        #-----------------------------------------------------------------------------------------#
                        #create the muticastgroup
                        if {[regexp "ipv4" $muticastgroup]} {
                            set group_type "ipv4group"
                        } else {
                            set group_type "ipv6group"
                        }
                        ::sth::hlapiGen::hlapi_gen_multicast_group $group_type $hlt_ret\_macstgroup_$j $muticastgroup
                    }
                    set muticastgroup_handle [concat $muticastgroup_handle "\[keylget [set sth::hlapiGen::device_ret($muticastgroup)] handle\]"]
                }
                puts_to_file "set muticastgroup_handle \"$muticastgroup_handle\" \n"
                set sth::hlapiGen::$channel_block\_$channel_block\_attr(-multicastparam-targets) \$muticastgroup_handle
                #need to check the subscribed_source if the UserDefinedSources is true
                set hltapi_config ""
                if {[set sth::hlapiGen::$channel_block\_$channel_block\_attr(-userdefinedsources)]} {
                    #---------------------------------------------------------------------------------------#
                    #config the igmp source
                    if {[info exists sth::hlapiGen::$channel_block\_$channel_block\_attr(-trafficsources-targets)]} {
                        unset sth::hlapiGen::$channel_block\_$channel_block\_attr(-trafficsources-targets)
                    }
                    # here need the multicast source handle
                    set igmp_src_ret [::sth::hlapiGen::hlapi_gen_multicast_source $hlt_ret\_macstsource_$j $channel_block]
                    #set igmp_src_ret [lindex [set sth::hlapiGen::device_ret([set ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value)])] 0]
                    #-----------------------------------------------------------------------------------------------#
                    #set sth::hlapiGen::device_ret($networkblock) "$igmp_src_ret 0"
                    set source_pool_handle "\[keylget $igmp_src_ret handle\]"
                    puts_to_file "set source_pool_handle \"$source_pool_handle\" \n"
                    set hltapi_config "-source_pool_handle \$source_pool_handle\\\n"
                } else {
                    #the subscribed_source should be a device created
                    if {[info exists sth::hlapiGen::$channel_block\_$channel_block\_attr(-trafficsources-targets)]} {
                        set subscribed_source [set sth::hlapiGen::$channel_block\_$channel_block\_attr(-trafficsources-targets)]
                        set subscribed_source_handle "\[keylget [lindex [set sth::hlapiGen::device_ret($subscribed_source)] 0] handle\]"
                        puts_to_file "set subscribed_source_handle \"$subscribed_source_handle\" \n"
                        set sth::hlapiGen::$channel_block\_$channel_block\_attr(-trafficsources-targets) \$subscribed_source_handle
                    }
                }
                hlapi_gen_device_basic $channel_block iptvchannelblock create $hlt_ret\_channel_block_$j $hltapi_config 1
                set sth::hlapiGen::device_ret($channel_block) $hlt_ret\_channel_block_$j
                set channel_block_ret "\[keylget $hlt_ret\_channel_block_$j handle\]"
            } else {
                set channel_block_ret "\[keylget [set sth::hlapiGen::device_ret($channel_block)] handle\]"
            }
            puts_to_file "set channel_block \"$channel_block_ret\" \n"
            set sth::hlapiGen::$viewedChannel\_$viewedChannel\_attr(-channelblock) \$channel_block
            hlapi_gen_device_basic $viewedChannel iptvviewedchannels create $hlt_ret\_viewedchannel_$j "" 1
            set sth::hlapiGen::device_ret($viewedChannel) $hlt_ret\_viewedchannel_$j
            set viewed_channel_handle [concat $viewed_channel_handle "\[keylget $hlt_ret\_viewedchannel_$j handle\]"]
        } else {
            set viewed_channel_handle [concat $viewed_channel_handle "\[keylget [set sth::hlapiGen::device_ret($viewedChannel)] handle\]"]
        }
        incr j
    }


    #check the view behavior profile
    set viewBehaviorProfiles [set sth::hlapiGen::$device\_$iptvStbBlock\_attr(-iptvprofile-targets)]
    set view_behavior_handle ""
    set j 0
    foreach viewBehaviorProfile $viewBehaviorProfiles {
        if {![info exists sth::hlapiGen::device_ret($viewBehaviorProfile)]} {
            sth::hlapiGen::get_attr $viewBehaviorProfile $viewBehaviorProfile
            hlapi_gen_device_basic $viewBehaviorProfile iptvviewingprofileconfig create $hlt_ret\_viewbehavior_$j "" 1
            set sth::hlapiGen::device_ret($viewBehaviorProfile) $hlt_ret\_viewbehavior_$j
            set view_behavior_handle [concat $view_behavior_handle "\[keylget $hlt_ret\_viewbehavior_$j handle\]"]
        } else {
            set view_behavior_handle [concat $view_behavior_handle "\[keylget [set sth::hlapiGen::device_ret($viewBehaviorProfile)] handle\]"]
        }
        incr j
    }

    puts_to_file "set viewed_channel_handle \"$viewed_channel_handle\" \n"
    set sth::hlapiGen::$device\_$iptvStbBlock\_attr(-stbchannel-targets) \$viewed_channel_handle

    puts_to_file "set view_behaviors \"$view_behavior_handle\" \n"
    set sth::hlapiGen::$device\_$iptvStbBlock\_attr(-iptvprofile-targets) \$view_behaviors

    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}



proc ::sth::hlapiGen::hlapi_gen_multicast_group {class hlt_ret ipgroup} {

    if {[regexp "ipv6" $class]} {
        set cmd_name emulation_multicast_group_config
        set name_space "::sth::multicast_group::"
        set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_start) "Ipv6NetworkBlock"
        set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_step) "Ipv6NetworkBlock"
        set ::sth::multicast_group::$cmd_name\_stcobj(ip_prefix_len) "Ipv6NetworkBlock"
        set ::sth::multicast_group::$cmd_name\_stcobj(num_groups) "Ipv6NetworkBlock"
        set ::sth::multicast_group::$cmd_name\_stcobj(pool_name) "Ipv6Group"
        set hlapi_script "      set $hlt_ret \[sth::$cmd_name\\\n"
        get_attr $ipgroup $ipgroup
        foreach ipv6group_obj [array names ::sth::hlapiGen::$ipgroup\_obj] {
            append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $ipgroup $ipgroup $ipv6group_obj]
        }
        #handle ipv6networkblock
        set ipblock [stc::get $ipgroup -children-ipv6networkblock]
        set ipblock [lindex $ipblock 0]
        get_attr $ipblock $ipblock
        set ::sth::hlapiGen::$ipblock\_$ipblock\_attr(-startiplist) [lindex [set ::sth::hlapiGen::$ipblock\_$ipblock\_attr(-startiplist)] 0]
        foreach ipblock_obj [array names ::sth::hlapiGen::$ipblock\_obj] {
            append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $ipblock $ipblock $ipblock_obj]
        }
        append hlapi_script "			-mode         create\\\n"
        append hlapi_script "\]\n"
        puts_to_file $hlapi_script
        gen_status_info $hlt_ret "sth::$cmd_name"
    } else {
        sth::hlapiGen::get_attr $ipgroup $ipgroup
        hlapi_gen_device_basic $ipgroup $class create $hlt_ret "" 1
    }
     set sth::hlapiGen::device_ret($ipgroup) $hlt_ret
}


proc ::sth::hlapiGen::hlapi_gen_multicast_source {hlt_ret parent_obj} {
    if {[info exists sth::hlapiGen::$parent_obj\_obj(ipv4networkblock)]} {
        set networkblock_type "ipv4networkblock"
    } else {
        set networkblock_type "ipv6networkblock"
    }
    set networkblock [set sth::hlapiGen::$parent_obj\_obj($networkblock_type)]
    if {[regexp "ipv4" $networkblock_type]} {

        set macstsource_args ""
        set igmp_src_attr_value ""
        append macstsource_args "set $hlt_ret \[sth::emulation_multicast_source_config\\\n"
        append macstsource_args "-mode      create\\\n"
        set ip_addr_start [lindex [set sth::hlapiGen::$parent_obj\_$networkblock\_attr(-startiplist)] 0]
        set ip_addr_step [set sth::hlapiGen::$parent_obj\_$networkblock\_attr(-addrincrement)]
        set ip_prefix_len [set sth::hlapiGen::$parent_obj\_$networkblock\_attr(-prefixlength)]
        set num_sources [set sth::hlapiGen::$parent_obj\_$networkblock\_attr(-networkcount)]
        foreach arg "ip_addr_start ip_prefix_len ip_addr_step num_sources" {
            append macstsource_args "-$arg      [set $arg]\\\n"
            set igmp_src_attr_value [join "$igmp_src_attr_value [set $arg]" "_"]
        }
        append macstsource_args "\]\n"
        if {[info exists ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value)]} {
            set ret_name [lindex [set sth::hlapiGen::device_ret([set ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value)])] 0]
        } else {
            puts_to_file $macstsource_args
            gen_status_info $hlt_ret "sth::emulation_multicast_source_config"
            set ret_name $hlt_ret
            set ::sth::hlapiGen::multicast_src_array($igmp_src_attr_value) $networkblock
            set sth::hlapiGen::device_ret($networkblock) "$hlt_ret 0"
        }
        #-----------------------------------------------------------------------------------------------#
        #return $igmp_src_attr_value
    } else {
        if {![info exists sth::hlapiGen::device_ret($networkblock)]} {
            set cmd_name emulation_multicast_source_config
            set name_space "::sth::multicast_group::"
            set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_start) "Ipv6NetworkBlock"
            set ::sth::multicast_group::$cmd_name\_stcobj(ip_addr_step) "Ipv6NetworkBlock"
            set ::sth::multicast_group::$cmd_name\_stcobj(ip_prefix_len) "Ipv6NetworkBlock"
            set ::sth::multicast_group::$cmd_name\_stcobj(num_sources) "Ipv6NetworkBlock"
            set ::sth::multicast_group::$cmd_name\_stcobj(pool_name) "Ipv6Group"
            #set ipv6groupsrcret "$hlt_ret\_ipblock\_$j"
            set hlapi_script "      set $hlt_ret \[sth::$cmd_name\\\n"
            get_attr $networkblock $networkblock
            set ::sth::hlapiGen::$networkblock\_$networkblock\_attr(-startiplist) [lindex [set ::sth::hlapiGen::$networkblock\_$networkblock\_attr(-startiplist)] 0]
            foreach ipblock_obj [array names ::sth::hlapiGen::$networkblock\_obj] {
                append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $networkblock $networkblock $ipblock_obj]
            }
            append hlapi_script "			-mode         create\\\n"
            append hlapi_script "\]\n"
            puts_to_file $hlapi_script
            gen_status_info $hlt_ret "sth::$cmd_name"
            set sth::hlapiGen::device_ret($networkblock) "$hlt_ret 0"
            set ret_name $hlt_ret
        } else {
            set ret_name [set sth::hlapiGen::device_ret($networkblock)]
        }
    }
    return $ret_name
}
