namespace eval ::sth::hlapiGen:: {

}

#########################################################################################################
#    hlapiGenFunctionP.tcl includes the functions to handle the hltapi configure functions 
#    whose (protocol) name is from P to Z.
#    Added protocols/functions:
#              a. pppox
#              b. ppp
#              c. pim
#              d. rsvp
#########################################################################################################

proc ::sth::hlapiGen::hlapi_gen_device_pimconfig {device class mode hlt_ret cfg_args first_time} {
    
    ::sth::sthCore::InitTableFromTCLList $::sth::pimTable
    
    #pre-process the attr under PimGlobalConfig
    set project [stc::get $device -parent]
    set pim_global_config [stc::get $project -children-pimglobalconfig]
    get_attr $pim_global_config $pim_global_config
    set prune_delay_enable [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-enablingpruningdelayoption)]
    if {[regexp -nocase "FALSE" $prune_delay_enable]} {
        unset ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-overrideinterval)
        unset ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-lanprunedelay)
    }
    append cfg_args [config_obj_attr ::sth:: emulation_pim_config $pim_global_config $pim_global_config pimglobalconfig]
    #pre-process the attr under PimRpMap:c_bsr_rp_addr c_bsr_rp_holdtime c_bsr_rp_priority c_bsr_rp_mode
    set pim_router_config [set ::sth::hlapiGen::$device\_obj(pimrouterconfig)]
    set ipversion [string tolower [set ::sth::hlapiGen::$device\_$pim_router_config\_attr(-ipversion)]]
    set pimrpmap "pim$ipversion"
    append pimrpmap "rpmap"
    if {[info exists ::sth::hlapiGen::$pim_router_config\_obj($pimrpmap)]} {
        set pim_rp_map [set ::sth::hlapiGen::$pim_router_config\_obj($pimrpmap)]
        set c_bsr_rp_addr [set ::sth::hlapiGen::$pim_router_config\_$pim_rp_map\_attr(-rpipaddr)]
        set c_bsr_rp_holdtime [set ::sth::hlapiGen::$pim_router_config\_$pim_rp_map\_attr(-rpholdtime)]
        set c_bsr_rp_priority [set ::sth::hlapiGen::$pim_router_config\_$pim_rp_map\_attr(-rppriority)]
        set c_bsr_rp_mode "create"
        foreach arg "c_bsr_rp_addr c_bsr_rp_holdtime c_bsr_rp_priority c_bsr_rp_mode" {
            append cfg_args "-$arg         [set $arg]\\\n"
        }
    }
    
    if {[info exists sth::hlapiGen::$device\_obj(greif)] && $first_time == 1} {
        
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args
        append cfg_args "                       -tunnel_handle              \$gre_ret\\\n"
    }
    
    #pre-process some special args: neighbor_intf_ip_addr, and tunnel_handle
    #for the scaling test, the length of the neighbor_intf_ip_addr should qual to the count
    #neighbor_intf_ip_addr can be UpstreamNeighborV6, UpstreamNeighborV4, Gateway
    if {$sth::hlapiGen::scaling_test} {
        if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-count)]} {
            set count [set ::sth::hlapiGen::$device\_$device\_attr(-count)]
        } else {
            set count 1
        }
        
        #calculate the gateway list
        set pim_routers [set ::sth::hlapiGen::protocol_to_devices(pimrouterconfig)]
        set dev_ret [lindex [set sth::hlapiGen::device_ret($device)] 0]
        set neighbor_intf_ip_addr ""
        foreach pim_router $pim_routers {
            set router_ret [lindex [set sth::hlapiGen::device_ret($pim_router)] 0]
            if {$dev_ret != $router_ret} {
                continue
            }
            if {[info exists sth::hlapiGen::$pim_router\_obj(ipv6if)]} {
                set ipifs [set sth::hlapiGen::$pim_router\_obj(ipv6if)]
                foreach ipif $ipifs {
                    set addr [set ::sth::hlapiGen::$pim_router\_$ipif\_attr(-address)]
                    if {![regexp "^fe80" $addr]} {
                        break
                    }
                }
                
            } else {
                set ipif [set sth::hlapiGen::$pim_router\_obj(ipv4if)]
            }
            set gateway [set ::sth::hlapiGen::$pim_router\_$ipif\_attr(-gateway)]
            set neighbor_intf_ip_addr [concat $neighbor_intf_ip_addr $gateway]
        }
        if {$first_time == 1} {
            append cfg_args "  -neighbor_intf_ip_addr  $neighbor_intf_ip_addr\\\n" 
        }
        set ::sth::emulation_pim_config_stcobj(neighbor_intf_ip_addr) _none_
    } else {
        if {[info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
            set ::sth::emulation_pim_config_stcobj(neighbor_intf_ip_addr) Ipv6If
        } else {
            set ::sth::emulation_pim_config_stcobj(neighbor_intf_ip_addr) Ipv4If
        }
    }

    if {[info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
        foreach arg "intf_ip_addr intf_ip_addr_step intf_ip_prefix_len" {
            set ::sth::emulation_pim_config_stcobj($arg) Ipv6If
        }
    } else {
        foreach arg "intf_ip_addr intf_ip_addr_step intf_ip_prefix_len" {
            set ::sth::emulation_pim_config_stcobj($arg) Ipv4If
        }
    }
    
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    
    #decide wether to call the sth::emulation_pim_group_config
    #check if the group has already been created or not, if not need to call the 
    #emulation_multicast_group_config to create the group
    #and wether need to use the sth::emulation_multicast_source_config to create the session_handle
    #Pimv4GroupBlk ,   Pimv6GroupBlk
    set j 0
    set pim_router_config [set ::sth::hlapiGen::$device\_obj(pimrouterconfig)]
    if {[info exists ::sth::hlapiGen::$pim_router_config\_obj(pim$ipversion\groupblk)]} {
        set pimgroupblks [set ::sth::hlapiGen::$pim_router_config\_obj(pim$ipversion\groupblk)]
        
        foreach pimgroupblk $pimgroupblks {
            hlapi_gen_pim_group $pim_global_config $pimgroupblk $pim_router_config $hlt_ret\_pim_group$j
            incr j
        }
        
    }
    
    ##Add for register pim groups
    if {[info exists ::sth::hlapiGen::$pim_router_config\_obj(pim[set ipversion]registerblk)]} {
        set pimgroupblks [set ::sth::hlapiGen::$pim_router_config\_obj(pim[set ipversion]registerblk)]
        foreach pimgroupblk $pimgroupblks {
            hlapi_gen_pim_register $pim_global_config $pimgroupblk $pim_router_config $hlt_ret\_pim_group$j
            incr j
        }
        
    }
    
}


proc ::sth::hlapiGen::hlapi_gen_pim_group {pim_global_config pimgroupblk pim_router_config hlt_ret} {
    #variable pim_global_config
    set cfg_args ""
    set dev_def ""
    append cfg_args "set $hlt_ret \[sth::emulation_pim_group_config \\\n"
    append cfg_args "-mode      create\\\n"

    #  group_pool_handle, session_handle, source_pool_handle
    #handle, not used in the hltapi code when the mode is creat
    set session_handle [stc::get $pim_router_config -parent]
    set group_pool_handle [set ::sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-joinedgroup-targets)]
    if {[regexp "v4" $group_pool_handle]} {
        set version "v4"
    } else {
        set version "v6"
    }
    #need to create te ipv4 or ipv6group first
    set first_time 1
    if {![info exists sth::hlapiGen::device_ret($group_pool_handle)]} {
        get_attr $group_pool_handle $group_pool_handle
        set table_name "::sth::multicast_group::multicast_groupTable"
        set name_space "::sth::multicast_group::"
        set cmd_name emulation_multicast_group_config
        if {[regexp "6" $version]} {
            
            if {[info exists $name_space$cmd_name\_Initialized]} {
                unset $name_space$cmd_name\_Initialized
            }
            ::sth::sthCore::InitTableFromTCLList [set $table_name]
            
            foreach arg "ip_addr_start ip_addr_step ip_prefix_len num_groups pool_name" {
                set $name_space$cmd_name\_stcobj($arg) "Ipv6NetworkBlock"
            }
        }
        
        hlapi_gen_device_basic $group_pool_handle ip$version\group create $hlt_ret\_macstgroup "" $first_time
        set sth::hlapiGen::device_ret($group_pool_handle) "$hlt_ret\_macstgroup 0"
        if {[info exists $name_space$cmd_name\_Initialized]} {
            unset $name_space$cmd_name\_Initialized
        }
    }
    if {$sth::hlapiGen::scaling_test} {
        set devices [update_device_handle $session_handle pimrouterconfig 1]
        append dev_def [get_device_created_scaling $devices session_handle handle]
    } else {
        append dev_def [get_device_created $session_handle session_handle handle]
    }
    
    
    append dev_def [get_device_created $group_pool_handle group_pool_handle handle]
    append cfg_args "-session_handle        \$session_handle\\\n"
    append cfg_args "-group_pool_handle     \$group_pool_handle\\\n"
    #source_pool_handle, need check the grouptype only when the 
    set group_type [set sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-grouptype)]
    if {[regexp -nocase "STARSTARRP" $group_type]} {
        #in hltapi although will not configure the source_pool_handle for this group, but need source_pool_handle
        #to decide if the group_type is STARSTARRP, so here use the Pimv4JoinSrc to create it's source pool
        
    } elseif {[regexp -nocase "STARG" $group_type]} {
        #no need to create the source_pool_handle, since hltapi will always ignore the source pool, if hltapi changed
        #then need to change to code to create the source_pool_handle
        #source_pool_handle is related to Pimv4PruneSrc
        set prun_en [set sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-enablingpruning)]
        if {[regexp -nocase "true" $prun_en]} {
            set wildcard_group 1
            set pim_src [set sth::hlapiGen::$pimgroupblk\_obj(pim[string trim $version]prunesrc)]
            set pim_src_class pim$version\prunesrc
        }
        
    } else {
        #source_pool_handle is related to Pimv4JoinSrc
        set wildcard_group 0
        set pim_src [set sth::hlapiGen::$pimgroupblk\_obj(pim[string trim $version]\joinsrc)]
        set pim_src_class pim$version\joinsrc
    }
    if {[info exists pim_src]} {
        set macstsource_args ""
        set pim_src_attr_value ""
        append macstsource_args "set $hlt_ret\_macstsource \[sth::emulation_multicast_source_config\\\n"
        append macstsource_args "-mode      create\\\n"
        set ip_addr_start [set sth::hlapiGen::$pimgroupblk\_$pim_src\_attr(-startiplist)]
        set ip_addr_step [set sth::hlapiGen::$pimgroupblk\_$pim_src\_attr(-addrincrement)]
        set ip_prefix_len [set sth::hlapiGen::$pimgroupblk\_$pim_src\_attr(-prefixlength)]
        set num_sources [set sth::hlapiGen::$pimgroupblk\_$pim_src\_attr(-networkcount)]
        foreach arg "ip_addr_start ip_addr_step ip_prefix_len num_sources" {
            append macstsource_args "-$arg      [set $arg]\\\n"
            set pim_src_attr_value [join "$pim_src_attr_value [set $arg]" "_"]
        }
         
        append macstsource_args "\]\n"
        if {[info exists ::sth::hlapiGen::multicast_src_array($pim_src_attr_value)]} {
            set pim_src_ret [set sth::hlapiGen::device_ret([set ::sth::hlapiGen::multicast_src_array($pim_src_attr_value)])]
            
        } else {
            puts_to_file $macstsource_args
            gen_status_info $hlt_ret\_macstsource "sth::emulation_multicast_source_config"
            set pim_src_ret $hlt_ret\_macstsource
            set ::sth::hlapiGen::multicast_src_array($pim_src_attr_value) $pim_src
        }
        
        set sth::hlapiGen::device_ret($pim_src) "$pim_src_ret 0"
        append dev_def [get_device_created $pim_src source_pool_handle handle]
        append cfg_args "-source_pool_handle     \$source_pool_handle\\\n"
        unset pim_src
    }
    #PimGlobalConfig
    #MsgInterval: interval
    #MsgRate: rate_control, join_prune_per_interval, register_per_interval, register_stop_per_interval,
    #set project [stc::get $pim_global_config -parent]
    set interval [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-msginterval)]
    append cfg_args "-interval  $interval\\\n"
    set msg_rate [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-msgrate)]
    set rate_control [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-enablemsgrate)]
    if {[regexp -nocase true $rate_control]} {
        #not the STC default value
        append cfg_args "-rate_control  1\\\n"
        foreach arg "join_prune_per_interval register_per_interval register_stop_per_interval" {
            append cfg_args "-$arg  $msg_rate\\\n"
        }
    } else {
        append cfg_args "-rate_control  0\\\n"
    }
    #PimGroupBlk -RpIpAddr
    if {![regexp -nocase "SG" $group_type]} {
        set rp_ip_addr [set ::sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-rpipaddr)]
        append cfg_args "-rp_ip_addr    $rp_ip_addr\\\n"
    }
    
    
    #wildcard_group
    #if source_pool_handle not exisits no need to output the wildcard_group, if it exists, then check the GroupType
    #under the pimgroupblk, if it is SG, then the wildcard_group is 0, else wildcard_group is 1
    if {[info exists wildcard_group]} {
        append cfg_args "-wildcard_group        $wildcard_group\\\n"
        unset wildcard_group
    }
    append cfg_args "\]\n"
    puts_to_file $dev_def
    puts_to_file $cfg_args
    gen_status_info $hlt_ret "sth::emulation_pim_group_config"
}

proc ::sth::hlapiGen::hlapi_gen_pim_register {pim_global_config pimgroupblk pim_router_config hlt_ret} {
    #variable pim_global_config
    set cfg_args ""
    set dev_def ""
    append cfg_args "set $hlt_ret \[sth::emulation_pim_group_config \\\n"
    append cfg_args "-mode      create\\\n"

    #  group_pool_handle, session_handle, source_pool_handle
    #handle, not used in the hltapi code when the mode is creat
    set session_handle [stc::get $pim_router_config -parent]
    
    set group_pool_handle [set ::sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-associatedmulticastgroup-targets)]
    if {[regexp "v4" $group_pool_handle]} {
        set version "v4"
    } else {
        set version "v6"
    }
    #need to create te ipv4 or ipv6group first
    set first_time 1
    if {![info exists sth::hlapiGen::device_ret($group_pool_handle)]} {
        get_attr $group_pool_handle $group_pool_handle
        set table_name "::sth::multicast_group::multicast_groupTable"
        set name_space "::sth::multicast_group::"
        set cmd_name emulation_multicast_group_config
        if {[regexp "6" $version]} {
            
            if {[info exists $name_space$cmd_name\_Initialized]} {
                unset $name_space$cmd_name\_Initialized
            }
            ::sth::sthCore::InitTableFromTCLList [set $table_name]
            
            foreach arg "ip_addr_start ip_addr_step ip_prefix_len num_groups pool_name" {
                set $name_space$cmd_name\_stcobj($arg) "Ipv6NetworkBlock"
            }
        }
        
        hlapi_gen_device_basic $group_pool_handle ip$version\group create $hlt_ret\_macstgroup "" $first_time
        set sth::hlapiGen::device_ret($group_pool_handle) "$hlt_ret\_macstgroup 0"
        if {[info exists $name_space$cmd_name\_Initialized]} {
            unset $name_space$cmd_name\_Initialized
        }
    }
    if {$sth::hlapiGen::scaling_test} {
        set devices [update_device_handle $session_handle pimrouterconfig 1]
        append dev_def [get_device_created_scaling $devices session_handle handle]
    } else {
        append dev_def [get_device_created $session_handle session_handle handle]
    }
    
    
    append dev_def [get_device_created $group_pool_handle group_pool_handle handle]
    puts_to_file $dev_def
    ##add src config
    set ipv4networkblock [set sth::hlapiGen::$pimgroupblk\_obj(ipv4networkblock)]
    set macstsource_args ""
    append macstsource_args "set $hlt_ret\_macstsource \[sth::emulation_multicast_source_config\\\n"
    append macstsource_args "-mode      create\\\n"
    set ip_addr_start [lindex [set sth::hlapiGen::$pimgroupblk\_$ipv4networkblock\_attr(-startiplist)] 0]
    set ip_addr_step [set sth::hlapiGen::$pimgroupblk\_$ipv4networkblock\_attr(-addrincrement)]
    set ip_prefix_len [set sth::hlapiGen::$pimgroupblk\_$ipv4networkblock\_attr(-prefixlength)]
    set num_sources [set sth::hlapiGen::$pimgroupblk\_$ipv4networkblock\_attr(-networkcount)]
    foreach arg "ip_addr_start ip_prefix_len ip_addr_step num_sources" {
        append macstsource_args "-$arg      [set $arg]\\\n"
    }
    append macstsource_args "\]\n"
    
    puts_to_file $macstsource_args
    gen_status_info $hlt_ret\_macstsource "sth::emulation_multicast_source_config"
    set igmp_src_ret $hlt_ret\_macstsource

    set sth::hlapiGen::device_ret($ipv4networkblock) "$igmp_src_ret 0"
    puts_to_file "set source_pool_handle \[keylget $igmp_src_ret handle\]"
    #####
    
    append cfg_args "-session_handle        \$session_handle\\\n"
    append cfg_args "-group_pool_handle     \$group_pool_handle\\\n"
    append cfg_args "-group_pool_mode     register\\\n"
    append cfg_args "-source_pool_handle     \$source_pool_handle\\\n"
    
    ##prepare source_group_mapping
    set source_group_mapping [set sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-multicastgrouptosourcedistribution)]
    if {[regexp -nocase "BACKBONE" $source_group_mapping]} {
        set source_group_mapping fully_meshed
    } else {
        set source_group_mapping one_to_one
    }
    append cfg_args "-source_group_mapping     $source_group_mapping\\\n"
    
    #PimGlobalConfig
    #MsgInterval: interval
    #MsgRate: rate_control, join_prune_per_interval, register_per_interval, register_stop_per_interval,
    #set project [stc::get $pim_global_config -parent]
    set interval [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-msginterval)]
    append cfg_args "-interval  $interval\\\n"
    set msg_rate [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-msgrate)]
    set rate_control [set ::sth::hlapiGen::$pim_global_config\_$pim_global_config\_attr(-enablemsgrate)]
    if {[regexp -nocase true $rate_control]} {
        #not the STC default value
        append cfg_args "-rate_control  1\\\n"
        foreach arg "join_prune_per_interval register_per_interval register_stop_per_interval" {
            append cfg_args "-$arg  $msg_rate\\\n"
        }
    } else {
        append cfg_args "-rate_control  0\\\n"
    }
    set rp_ip_addr [set ::sth::hlapiGen::$pim_router_config\_$pimgroupblk\_attr(-rpipaddr)]
    append cfg_args "-rp_ip_addr    $rp_ip_addr\\\n"
    
    #wildcard_group
    #if source_pool_handle not exisits no need to output the wildcard_group, if it exists, then check the GroupType
    #under the pimgroupblk, if it is SG, then the wildcard_group is 0, else wildcard_group is 1
    if {[info exists wildcard_group]} {
        append cfg_args "-wildcard_group        $wildcard_group\\\n"
        unset wildcard_group
    }
    append cfg_args "\]\n"
    puts_to_file $cfg_args
    gen_status_info $hlt_ret "sth::emulation_pim_group_config"
}

proc ::sth::hlapiGen::hlapi_gen_device_pppoxserverconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    pppox_server_pre_process $cfg_args $device
    ::sth::sthCore::InitTableFromTCLList $::sth::PppoxServer::pppoxServerTable
    
    set pppoe_server_block_handle  [set ::sth::hlapiGen::$device\_obj($class)]
    if {[info exists ::sth::hlapiGen::$pppoe_server_block_handle\_obj(pppoxserveripv6peerpool)]} {
        set pppoe_server_pool_class pppoxserveripv6peerpool
    } else {
        set pppoe_server_pool_class pppoeserveripv4peerpool
    }
    set pppoe_server_pool_handle [set ::sth::hlapiGen::$pppoe_server_block_handle\_obj($pppoe_server_pool_class)]
    append cfg_args [config_obj_attr ::sth::PppoxServer:: pppox_server_config $pppoe_server_block_handle $pppoe_server_pool_handle $pppoe_server_pool_class]
    #
    #set class "PppoeServerBlockConfig"
    #hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    set hlapi_script [hlapi_gen_device_basic_without_puts $device $class create $hlt_ret $cfg_args $first_time]
    pppox_client_server_common_post_process $hlapi_script $device
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    
}
proc ::sth::hlapiGen::pppox_client_server_common_pre_process {device class} {
    set cfg_args_local ""
    if {![info exists sth::hlapiGen::$device\_obj(vlanif)]} {
        if {[info exists sth::hlapiGen::$device\_obj(aal5if)]} {
            set aal5if [set sth::hlapiGen::$device\_obj(aal5if)]
            set encp [set sth::hlapiGen::$device\_$aal5if\_attr(-vcencapsulation)]
            if {[regexp -nocase {VC_MULTIPLEXED} $encp]} {
                append cfg_args_local "                -encap                 vc_mux\\\n"
            } else {
                append cfg_args_local "                -encap                 llcsnap\\\n"
            }
            
        } else {
            append cfg_args_local "                -encap                 ethernet_ii\\\n"
        }
    } else {
        if {[llength [set sth::hlapiGen::$device\_obj(vlanif)]] == 1} {
            append cfg_args_local "                -encap                 ethernet_ii_vlan\\\n"
        } else {
            #qinq mode
            append cfg_args_local "                -encap                 ethernet_ii_qinq\\\n"
        }
    }
    #protcol pre_process, it can be pppoe pppoa or pppoeoa
    if {[info exists sth::hlapiGen::$device\_obj(ethiiif)]} {
        if {[info exists sth::hlapiGen::$device\_obj(aal5if)]} {
            append cfg_args_local "                -protocol                 pppoeoa\\\n" 
        } else {
            append cfg_args_local "                -protocol                 pppoe\\\n" 
        }
    } else {
        append cfg_args_local "                -protocol                 pppoa\\\n" 
    }

    set pppoeblock [set sth::hlapiGen::$device\_obj($class)]
    if {[regexp "server" $pppoeblock]} {
        if {[regexp -nocase "ipv4v6" [set sth::hlapiGen::$device\_$pppoeblock\_attr(-ipcpencap)]]} {
            puts_msg "pppox server don't support ipv4v6"
            set sth::hlapiGen::$device\_$pppoeblock\_attr(-ipcpencap) ipv4
        } 
    }
    
    #wildcard_pound_end
    #wildcard_pound_fill
    #wildcard_pound_start
    #wildcard_question_end
    #wildcard_question_start
    #wildcard_question_fill
    #wildcard_bang_start
    #wildcard_bang_end
    #wildcard_bang_fill
    #wildcard_dollar_start
    #wildcard_dollar_end
    #wildcard_dollar_fill
    #username_wildcard
    #password_wildcard
    #username
    #password
    
    set username [set sth::hlapiGen::$device\_$pppoeblock\_attr(-username)]
    set password [set sth::hlapiGen::$device\_$pppoeblock\_attr(-password)]
    #get the @x() in the username and the password
    #{# pound} {? question} {! bang} {$ dollar}
    set pound_list ""
    set question_list ""
    set bang_list ""
    set dollar_list ""
    
    set wildcard_list ""
    
    if {[regexp {@x\([0-9,]+\)} $username]} {
        append cfg_args_local "          -username_wildcard 1\\\n"
    }
    if {[regexp {@x\([0-9,]+\)} $password]} {
        append cfg_args_local "          -password_wildcard 1\\\n"
    }
    set username_password [concat $username $password]
    while (1) {
        
        if {[regexp {@x\([0-9,]+\)} $username_password wildcard]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            
            regsub -all $wildcard $username_password "#" username_password
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
            set cfg_string [process_wildcard pound $wildcard]
            append cfg_args_local $cfg_string
            set pound_list "#"
            #wildcard_pound_end, wildcard_pound_fill, wildcard_pound_start
        } elseif {[regexp {^$} $question_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "?" username
            regsub $wildcard $password "?" password
            set cfg_string [process_wildcard question $wildcard]
            append cfg_args_local $cfg_string
            set question_list "?"
            #wildcard_question_end, wildcard_question_start, wildcard_question_fill
        } elseif {[regexp {^$} $bang_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "!" username
            regsub $wildcard $password "!" password
            set cfg_string [process_wildcard bang $wildcard]
            append cfg_args_local $cfg_string
            set bang_list "!"
            #wildcard_bang_start, wildcard_bang_end, wildcard_bang_fill
        } else {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            regsub $wildcard $username "$" username
            regsub $wildcard $password "$" password
            set cfg_string [process_wildcard dollar $wildcard]
            append cfg_args_local $cfg_string
            #wildcard_dollar_start, wildcard_dollar_end, wildcard_dollar_fill
        }
    }
    set sth::hlapiGen::$device\_$pppoeblock\_attr(-username) $username
    set sth::hlapiGen::$device\_$pppoeblock\_attr(-password) $password
    return $cfg_args_local
}

proc ::sth::hlapiGen::pppox_client_server_common_post_process {hlapi_script device} {
    
    upvar hlapi_script hlapi_script_local
    #process the dual vlan, when there is no vlan_id_count and no vlan_id_outer_count,
    #need to set vlan_id_count and vlan_id_outer_count to be the value of num_session, esle
    #the vlan_id_count and vlan_id_outer_count as the default value.
    #and also set the qinq_incr_mode to be both, else it will use outer as the default value.
    set num_session [set ::sth::hlapiGen::$device\_$device\_attr(-devicecount)]
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        set vlan_count_settings ""
        if {[llength $vlanifs] > 1} {
            if {[lsearch $hlapi_script_local " -vlan_id_count"] < 0 && [lsearch $hlapi_script_local " -vlan_id_outer_count"] < 0} {
                if {$num_session > 1} {
                    append vlan_count_settings "-vlan_id_count $num_session \\\n"
                    append vlan_count_settings "-vlan_id_outer_count    $num_session \\\n"
                    append vlan_count_settings "-qinq_incr_mode   both \\\n"
                    append vlan_count_settings "\]\n"
                    regsub "]" $hlapi_script_local $vlan_count_settings hlapi_script_local
                }
            } elseif {[lsearch $hlapi_script_local " -vlan_id_count"] > 0 && [lsearch $hlapi_script_local " -vlan_id_outer_count"] > 0} {
                set vlan_id_count [lindex $hlapi_script_local [expr [lsearch $hlapi_script_local " -vlan_id_count"] + 1]]
                set vlan_id_outer_count [lindex $hlapi_script_local [expr [lsearch $hlapi_script_local " -vlan_id_outer_count"] + 1]]
                if {[expr $vlan_id_count * $vlan_id_outer_count] > $num_session} {
                    append vlan_count_settings "-qinq_incr_mode   both \\\n"
                    append vlan_count_settings "\]\n"
                    regsub "]" $hlapi_script_local $vlan_count_settings hlapi_script_local
                }
            }
        } else {
            if {[lsearch $hlapi_script_local " -vlan_id_count"] < 0 && [lsearch $hlapi_script_local " -vlan_id_step"] > 0} {
                set vlan_id_step [set ::sth::hlapiGen::$device\_$vlanifs\_attr(-idstep)]
                if {$vlan_id_step > 0} {
                    append vlan_count_settings "-vlan_id_count $num_session \\\n"
                    append vlan_count_settings "\]\n"
                    regsub "]" $hlapi_script_local $vlan_count_settings hlapi_script_local
                }
            }
        }
    }
}

proc ::sth::hlapiGen::pppox_server_pre_process {cfg_args device} {
    
    upvar cfg_args cfg_args_local
    
    #encap  and protocol pre_process
    append cfg_args_local [pppox_client_server_common_pre_process $device pppoeserverblockconfig]
    
}

proc ::sth::hlapiGen::process_wildcard {marker wildcard} {
    #only support the step to be 1 and repeat to 0
    set start 1
    set count 1
    set step 1
    set fill 0
    set repeat 0
    
    set cfg_string ""
    
    regexp {[0-9,]+} $wildcard wildcard
    set wildcard_values [split $wildcard ","]
    set i 0
    foreach wildcard_arg {start count step fill repeat} {
        set len [llength $wildcard_values]
        set $wildcard_arg [lindex $wildcard_values $i]
        incr i
        if {$i >= $len} {
            break
        }
    }
    append cfg_string "-wildcard_$marker\_start $start\\\n"
    
    if {$count > 1} {
        set end [expr "($start + $count) - 1"]
        append cfg_string "-wildcard_$marker\_end $end\\\n"
    }
    
    if {$fill != 0} {
        append cfg_string "-wildcard_$marker\_fill $fill\\\n"
    }

    return $cfg_string
}


proc ::sth::hlapiGen::hlapi_gen_device_pppoxclientconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    pppox_client_pre_process $cfg_args $device
    ::sth::sthCore::InitTableFromTCLList $::sth::Pppox::pppoxTable
    
    #hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    set hlapi_script [hlapi_gen_device_basic_without_puts $device $class create $hlt_ret $cfg_args $first_time]
    pppox_client_server_common_post_process $hlapi_script $device
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
}
proc ::sth::hlapiGen::multi_dev_check_func_pppoeclient {class devices} {
    variable devicelist_obj
    foreach device $devices {
        if {[set ::sth::hlapiGen::$device\_$device\_attr(-devicecount)] > 1} {
            return -code error "can not use the scaling mode"
        }
    }
    set update_obj [multi_dev_check_func_basic $class $devices]

    return $update_obj
}
proc ::sth::hlapiGen::pppox_client_pre_process {cfg_args device} {
    upvar cfg_args cfg_args_local
    #encap
    #protocol
    #wildcard_pound_end
    #wildcard_pound_fill
    #wildcard_pound_start
    #wildcard_question_end
    #wildcard_question_start
    #wildcard_question_fill
    #wildcard_bang_start
    #wildcard_bang_end
    #wildcard_bang_fill
    #wildcard_dollar_start
    #wildcard_dollar_end
    #wildcard_dollar_fill
    #username_wildcard
    #password_wildcard
    #username
    #password
    set pppoeclient_obj [set sth::hlapiGen::$device\_obj(pppoeclientblockconfig)]
    append cfg_args_local [pppox_client_server_common_pre_process $device pppoeclientblockconfig]
    if {$::sth::hlapiGen::scaling_test && [info exists ::sth::hlapiGen::$device\_$device\_attr(-count)]} {
        set count [set ::sth::hlapiGen::$device\_$device\_attr(-count)]
        set num_session [set ::sth::hlapiGen::$device\_$device\_attr(-devicecount)]
        if {$count > $num_session} {
            set ::sth::hlapiGen::$device\_$device\_attr(-devicecount) $count
            append cfg_args_local "-device_block_mode one_device_per_block \\\n"
        }
        #process the scaling mode when the device_block_mode is one_device_per_blcok
        #class need to process: EthIIIf VlanIf Ipv4If Ipv6If
        if {[info exists sth::hlapiGen::$device\_obj(ethiiif)]} {
            set ethiiif [set sth::hlapiGen::$device\_obj(ethiiif)]
            if {[info exists sth::hlapiGen::$device\_$ethiiif\_attr(-sourcemac.step)]} {
                set sth::hlapiGen::$device\_$ethiiif\_attr(-srcmacstep) [set sth::hlapiGen::$device\_$ethiiif\_attr(-sourcemac.step)]
            }
        }
        
        if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {    
            set vlanifs [set sth::hlapiGen::$device\_obj(vlanif)]
            foreach vlanif $vlanifs {
                if {[info exists sth::hlapiGen::$device\_$vlanif\_attr(-vlanid.count)]} {
                    set sth::hlapiGen::$device\_$vlanif\_attr(-ifrecyclecount) [set sth::hlapiGen::$device\_$vlanif\_attr(-vlanid.count)]
                }
                if {[info exists sth::hlapiGen::$device\_$vlanif\_attr(-vlanid.step)]} {
                    set sth::hlapiGen::$device\_$vlanif\_attr(-idstep) [set sth::hlapiGen::$device\_$vlanif\_attr(-vlanid.step)]
                }
            }
        }
        set ipifs ""
        if {[info exists sth::hlapiGen::$device\_obj(ipv4if)]} {
            append ipifs [set sth::hlapiGen::$device\_obj(ipv4if)]
        }
        if {[info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
            append ipifs " [set sth::hlapiGen::$device\_obj(ipv6if)]"
        }
        foreach ipif $ipifs {
            if {[info exists sth::hlapiGen::$device\_$ipif\_attr(-address.step)]} {
                set sth::hlapiGen::$device\_$ipif\_attr(-addrstep) [set sth::hlapiGen::$device\_$ipif\_attr(-address.step)]
            }
            if {[info exists sth::hlapiGen::$device\_$ipif\_attr(-address.step)]} {
                set sth::hlapiGen::$device\_$ipif\_attr(-gatewaystep) [set sth::hlapiGen::$device\_$ipif\_attr(-gateway.step)]
            }
        }
    }
    #max_auth_req
    #auth_req_timeout
    set auth_mode [string tolower [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-authentication)]]
    switch -- $auth_mode {
        pap {
            set auth_req_timeout [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-paprequesttimeout)]
            set max_auth_req [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-maxpaprequestattempts)]
            
            append cfg_args_local "-auth_req_timeout   $auth_req_timeout\\\n"
            append cfg_args_local "-max_auth_req       $max_auth_req\\\n"
        }
        auto {
            set pap_auth_req_timeout [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-paprequesttimeout)]
            set pap_max_auth_req [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-maxpaprequestattempts)]
            set chap_auth_req_timeout [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-chapchalrequesttimeout)]
            set chap_max_auth_req [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-maxchaprequestreplyattempts)]
            
            append cfg_args_local "-auth_req_timeout   $pap_auth_req_timeout\\\n"
            append cfg_args_local "-max_auth_req       $pap_max_auth_req\\\n"
            
            if {($pap_auth_req_timeout != $chap_auth_req_timeout) || ($pap_max_auth_req != $chap_max_auth_req)} {
                set auto_warn_message "pap_or_chap (negotiate) authentication mode only supports\
                the same values of PAP and CHAP req timeout/req max attempts."
                if {[info exist ::sth::hlapiGen::warnings(pppox_config)]} {
                    set ::sth::hlapiGen::warnings(pppox_config) "$::sth::hlapiGen::warnings(pppox_config), $auto_warn_message"
                } else {
                    set ::sth::hlapiGen::warnings(pppox_config) $auto_warn_message                     
                }
            }
        }
        chap_md5 {
            set auth_req_timeout [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-chapchalrequesttimeout)]
            set max_auth_req [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-maxchaprequestreplyattempts)]
            
            append cfg_args_local "-auth_req_timeout   $auth_req_timeout\\\n"
            append cfg_args_local "-max_auth_req       $max_auth_req\\\n"
        }
        default {
            #do nothing
        }
    }
    
    #comment this args, becuase it will create two dhcpv6pdblock object if pppox works with dhcpv6pd.
    #use_internal_dhcpv6 if there is Dhcpv6PdBlockConfig, then use_internal_dhcpv6 is 1
    #if {[info exists sth::hlapiGen::$device\_obj(dhcpv6pdblockconfig)]} {
    #    append cfg_args_local "-use_internal_dhcpv6     1\\\n"
    #}
    #ac_select_mode always set  to service_name
    append cfg_args_local "-ac_select_mode     service_name\\\n"
    
    #client_traffic_behavior          PppoxOptions
    set pppoxoptions_obj [stc::get project1 -children-PppoxOptions]
    set client_traffic_behavior [stc::get $pppoxoptions_obj -TrafficBehavior]
    if {[regexp -nocase "IGNORE_FAILED_SESSIONS" $client_traffic_behavior]} {
        append cfg_args_local "-client_traffic_behavior     $client_traffic_behavior\\\n"
    }
    
    #circuit_id_suffix_mode, circuit_id_incr_start, circuit_id_incr_step, circuit_id_incr_count
    #remote_id_suffix_mode, remote_id_incr_start, remote_id_incr_step, remote_id_incr_count
    set pppoe_circuit_id [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-circuitid)]
    set pppoe_remote_id  [set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-remoteorsessionid)]
    foreach type {circuit remote} {
        if {[llength [set pppoe_$type\_id]] > 1} {
            set pppoe_id [lindex [set pppoe_$type\_id] 0]
            set pppoe_id_suffix [lindex [set pppoe_$type\_id] 1]
            if {[regexp "@x" $pppoe_id_suffix]} {
                #only handle this kind of suffix, since the hltapi only support this kind
                append cfg_args_local "-$type\_id_suffix_mode     incr\\\n"
                
                regexp {[0-9,]+} $pppoe_id_suffix pppoe_id_suffix
                set suffix_values [split $pppoe_id_suffix ","]
                set id_incr_start [lindex $suffix_values 0]
                append cfg_args_local "-$type\_id_incr_start     $id_incr_start\\\n"
                if {[llength $suffix_values] > 2} {
                    set id_incr_step  [lindex $suffix_values 2]
                    append cfg_args_local "-$type\_id_incr_step     $id_incr_step\\\n"
                }
                
                if {[llength $suffix_values] > 4} {
                    set id_incr_count  [expr {[lindex $suffix_values 4] + 1}]
                    append cfg_args_local "-$type\_id_incr_count     $id_incr_count\\\n"
                }
                
            } else {
                append cfg_args_local "-$type\_id_suffix_mode     none\\\n"
            }
            set pppoe_$type\_id $pppoe_id
        }
    }
    
    set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-circuitid)          $pppoe_circuit_id
    set sth::hlapiGen::$device\_$pppoeclient_obj\_attr(-remoteorsessionid)  $pppoe_remote_id
}



proc ::sth::hlapiGen::hlapi_gen_device_pppconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    ::sth::sthCore::InitTableFromTCLList $::sth::ppp::pppTable
    ppp_pre_process $cfg_args $device $class
    set mode "config"
    variable $device\_obj
    set object_handle [set $device\_obj($class)]
    variable $device\_$object_handle\_attr
    set hlapi_script ""
    set name_space "::sth::ppp::"
    set cmd_name "ppp_config"
    if {![info exists ::sth::hlapiGen::$device\_$object_handle\_attr(-usesif-targets)]} {
        return
    }
    
    append hlapi_script "set $hlt_ret \[sth::$cmd_name\\\n"
    append hlapi_script     "-action            config\\\n"
    set port_handle     $::sth::hlapiGen::port_ret($device)
    append hlapi_script     "-port_handle       $port_handle\\\n"
    append hlapi_script $cfg_args
    set obj_handles [set $device\_obj($class)]
        foreach obj_handle $obj_handles {
        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    }
    
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret sth::$cmd_name
    #hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::ppp_pre_process {cfg_args device class} {
    upvar cfg_args cfg_args_local
    
    set name_space "::sth::ppp::"
    set cmd_name "ppp_config" 
    #fcs_size and local_fcs
    if {[info exists ::sth::hlapiGen::$device\_obj(atmphy)]} {
        set atm_obj [set ::sth::hlapiGen::$device\_obj(atmphy)]
        set sonet_obj [set ::sth::hlapiGen::$atm_obj\_obj(sonetconfig)]
        set fcs [set ::sth::hlapiGen::$atm_obj\_$sonet_obj\_attr(-fcs)]
        
        if {![regexp -nocase "FCS32" $fcs]} {
            append cfg_args_local "     -local_fcs      1\\\n"
        }
    } elseif {[info exists ::sth::hlapiGen::$device\_obj(posphy)]} {
        set pos_obj [set ::sth::hlapiGen::$device\_obj(posphy)]
        set sonet_obj [set ::sth::hlapiGen::$pos_obj\_obj(sonetconfig)]
        set fcs [set ::sth::hlapiGen::$pos_obj\_$sonet_obj\_attr(-fcs)]
        
        if {![regexp -nocase "FCS32" $fcs]} {
            append cfg_args_local "     -local_fcs      1\\\n"
        }
    }
    #ipv6_cp
    set ppp_obj [set ::sth::hlapiGen::$device\_obj($class)]
    set ipv6_cp [set ::sth::hlapiGen::$device\_$ppp_obj\_attr(-ipcpencap)]
    if {[regexp "v6" $ipv6_cp]} {
        set ::sth::hlapiGen::$device\_$ppp_obj\_attr(-ipcpencap) 1
        set $name_space$cmd_name\_stcobj(peer_addr) "_none_"
    } else {
        set ::sth::hlapiGen::$device\_$ppp_obj\_attr(-ipcpencap) 0
        set $name_space$cmd_name\_stcobj(peer_intf_id) "_none_"
    } 
    #local_auth_mode and password, username
    set local_auth_mode [set ::sth::hlapiGen::$device\_$ppp_obj\_attr(-authentication)]
    if {[regexp -nocase "none" $local_auth_mode]} {
        set $name_space$cmd_name\_stcobj(password) "_none_"
        set $name_space$cmd_name\_stcobj(username) "_none_"
    }
    #local_addr_given
    #local_addr_override
    if {[regexp "v6" $ipv6_cp]} {
        set host_obj [set ::sth::hlapiGen::$device\_obj(host)]
        set ipv6_obj [set ::sth::hlapiGen::$host_obj\_obj(ipv6if)]
        set local_intf_id [set ::sth::hlapiGen::$host_obj\_$ipv6_obj\_attr(-address)]
        if {[regexp "0:0:0:0" $local_intf_id] || [regexp "^::$" $local_intf_id]} {
            append cfg_args_local "     -local_addr_given           0\\\n"
            append cfg_args_local "     -local_addr_override        1\\\n"
        } else {
            append cfg_args_local "     -local_addr_given           1\\\n"
            append cfg_args_local "     -local_addr_override        0\\\n"
        }
        
        set peer_intf_id [set ::sth::hlapiGen::$device\_$ppp_obj\_attr(-ipv6peeraddr)]
        if {[regexp "0:0:0:0" $peer_intf_id] || [regexp "^::$" $peer_intf_id]} {
            append cfg_args_local "     -peer_addr_given                0\\\n"
            append cfg_args_local "     -peer_addr_override             1\\\n"
        } else {
            append cfg_args_local "     -peer_addr_given                1\\\n"
            append cfg_args_local "     -peer_addr_override             0\\\n"
        }                 
    } else {
        set host_obj [set ::sth::hlapiGen::$device\_obj(host)]
        set ipv4_obj [set ::sth::hlapiGen::$host_obj\_obj(ipv4if)]
        
        set local_addr [set ::sth::hlapiGen::$host_obj\_$ipv4_obj\_attr(-address)]
        if {[regexp "0.0.0.0" $local_addr]} {
            append cfg_args_local "     -local_addr_given           0\\\n"
            append cfg_args_local "     -local_addr_override        1\\\n"
        } else {
            append cfg_args_local "     -local_addr_given           1\\\n"
            append cfg_args_local "     -local_addr_override        0\\\n"
        }
        
        set peer_addr [set ::sth::hlapiGen::$device\_$ppp_obj\_attr(-ipv4peeraddr)]
        if {[regexp "0.0.0.0" $peer_addr]} {
            append cfg_args_local "     -peer_addr_given                0\\\n"
            append cfg_args_local "     -peer_addr_override             1\\\n"
        } else {
            append cfg_args_local "     -peer_addr_given                1\\\n"
            append cfg_args_local "     -peer_addr_override             0\\\n"
        }
    }
}

proc ::sth::hlapiGen::hlapi_gen_device_rsvpconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    set name_space "::sth::Rsvp::"
    set cmd_name "emulation_rsvp_config"
    ::sth::sthCore::InitTableFromTCLList $::sth::Rsvp::rsvpTable
     
    #pre-process the tunnel handle, to config this, need to call the gre config function
    if {[info exists sth::hlapiGen::$device\_obj(greif)]} {
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args
        append cfg_args "                       -tunnel_handle              \$gre_ret\\\n"
    }
    
    #cfi is replaced with "-vlan_cfi"
    set $name_space$cmd_name\_stcattr(cfi) "_none_"
    set $name_space$cmd_name\_stcattr(bundle_msgs) "_none_"
    #update the stcattr of vlan_id_mode and vlan_outer_id_mode
    set $name_space$cmd_name\_stcattr(vlan_id_mode) "vlanid.mode"
    set $name_space$cmd_name\_stcattr(vlan_outer_id_mode) "vlanid.mode"
    
    set router_paramlist "count"
    regsub {\d+$} $device "" update_obj
    foreach router_param $router_paramlist {
        set $name_space$cmd_name\_stcobj($router_param) "$update_obj"
    }
    
    set rsvphdl [set ::sth::hlapiGen::$device\_obj($class)]
    #add summary_refresh: this argument needs to be enable while using srefresh_interval
    if {[set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-refreshreductionsummaryrefreshinterval)] != "null"} {
        append cfg_args "-summary_refresh  1\\\n"
        set refresh_reduc_enable 1
    }
    
    #for emulation_rsvp_custom_object_config
    set rsvpcustomobjectHndList [stc::get project1 -children-RsvpCustomObject]
    if {[llength $rsvpcustomobjectHndList] != 0} {
        set customIndex 0
        foreach customObj $rsvpcustomobjectHndList {
            ::sth::hlapiGen::rsvp_custom_object_gen $device $customObj $hlt_ret\_custom\_$customIndex $name_space
            incr customIndex
        }
    }

    #add summary_refresh: this argument needs to be enable while using srefresh_interval
    if {[set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-refreshreductionbundleinterval)] != "null" } {
        append cfg_args "-bundle_msgs  1\\\n"
        set refresh_reduc_enable 1
        set $name_space$cmd_name\_stcobj(bundle_msgs) "_none_"
    }
    
    #add refresh_reduction: this argument needs to be enable while using summary_refresh or bundle_msgs
    if {[info exists refresh_reduc_enable]} {
        append cfg_args "-refresh_reduction  1\\\n"
    }
    
    if {[set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-dutipaddr)] == "null" && [info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        #if current dutipaddr is null, set the gateway as dutipaddr
        set ipv4if [set ::sth::hlapiGen::$device\_obj(ipv4if)]
        set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-dutipaddr) [set ::sth::hlapiGen::$device\_$ipv4if\_attr(-gateway)]
    }
    
    #get enablerecordroute value
    if {[info exists ::sth::hlapiGen::$rsvphdl\_obj(rsvpingresstunnelparams)]} {
        set rsvp_tunnel_params_hdl [lindex [set ::sth::hlapiGen::$rsvphdl\_obj(rsvpingresstunnelparams)] 0]
        set record_route [set ::sth::hlapiGen::$rsvphdl\_$rsvp_tunnel_params_hdl\_attr(-enablerecordroute)]
        if {[regexp -nocase "false" $record_route]} {
            set record_route 0
        } else {
            set record_route 1
        }
        append cfg_args "-record_route  $record_route\\\n"
    }

    if {[info exists ::sth::hlapiGen::$device\_$rsvphdl\_attr(-patherrorcustomobject-sources)] } {
        set customHndVar ""
        set custom_handle_list [set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-patherrorcustomobject-sources)]
        foreach custom_handle $custom_handle_list {
            append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
        }
		set customHndVar [lsort $customHndVar]
        regsub -all {\{|\}} $customHndVar "" customHndVar 
		append cfg_args "-path_err_custom_handle  \"$customHndVar\"\\\n"
    }

    if {[info exists ::sth::hlapiGen::$device\_$rsvphdl\_attr(-hellocustomobject-sources)] } {
        set customHndVar ""
        set custom_handle_list [set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-hellocustomobject-sources)]
        foreach custom_handle $custom_handle_list {
            append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
        }
		set customHndVar [lsort $customHndVar]
        regsub -all {\{|\}} $customHndVar "" customHndVar 
        append cfg_args "-hello_custom_handle  \"$customHndVar\"\\\n"
    }

    if {[info exists ::sth::hlapiGen::$device\_$rsvphdl\_attr(-reservationerrorcustomobject-sources)] } {
        set customHndVar ""
        set custom_handle_list [set ::sth::hlapiGen::$device\_$rsvphdl\_attr(-reservationerrorcustomobject-sources)]
        foreach custom_handle $custom_handle_list {
            append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
        }
		set customHndVar [lsort $customHndVar]
        regsub -all {\{|\}} $customHndVar "" customHndVar 
        append cfg_args "-reser_err_custom_handle  \"$customHndVar\"\\\n"
    }

    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    
    #process the rsvp tunnel config
    set devicelist [update_device_handle $device $class $first_time]
    
    #the device need update in scaling mode
    set i 0
    foreach device $devicelist {
        set rsvphdl [set ::sth::hlapiGen::$device\_obj($class)]
        
        #update the stcobj for record_route
        if {[info exists ::sth::hlapiGen::$rsvphdl\_obj]} {
            gather_info_for_ctrl_res_func $device "rsvptunnelparams"
            set rsvp_tunnel_params_hdl_list ""
            if {$::sth::hlapiGen::scaling_test && $first_time} {
                set attrlist "TunnelId SrcIpAddr DstIpAddr"
                set rsvp_tunnel_params_hdl_list [route_scaling_pre_process "" $rsvphdl $attrlist]
            } else {
                if {[info exists ::sth::hlapiGen::$rsvphdl\_obj(rsvpingresstunnelparams)]} {
                    set rsvp_tunnel_params_hdl_list [concat $rsvp_tunnel_params_hdl_list [set ::sth::hlapiGen::$rsvphdl\_obj(rsvpingresstunnelparams)]]
                }
                if {[info exists ::sth::hlapiGen::$rsvphdl\_obj(rsvpegresstunnelparams)]} {    
                    set rsvp_tunnel_params_hdl_list [concat $rsvp_tunnel_params_hdl_list [set ::sth::hlapiGen::$rsvphdl\_obj(rsvpegresstunnelparams)]]
                }
            }
        
            foreach rsvp_tunnel_params_hdl $rsvp_tunnel_params_hdl_list {
                set cfg_args ""
                gather_info_for_ctrl_res_func $rsvp_tunnel_params_hdl "rsvptunnelparams_ctrl"
                set route_cfg_args ""
                set hlt_ret_route $hlt_ret\_route$i
                set sth::hlapiGen::device_ret($rsvp_tunnel_params_hdl) "$hlt_ret_route 0"
                rsvp_tunnel_pre_process $rsvphdl $rsvp_tunnel_params_hdl $hlt_ret_route
                puts_to_file [get_device_created $device $hlt_ret\_hdl handle]
                append route_cfg_args "      set $hlt_ret_route \[sth::emulation_rsvp_tunnel_config\\\n"
                append route_cfg_args "-mode                                    create \\\n"
                append route_cfg_args "-handle 					\$$hlt_ret\_hdl \\\n"
                append route_cfg_args $cfg_args
                append route_cfg_args "\]\n"
                puts_to_file $route_cfg_args
                gen_status_info $hlt_ret_route "sth::emulation_rsvp_tunnel_config"
                incr i

                #Sub-Group/LSP under tunnel configuration
                sth::hlapiGen::rsvp_tunnel_sub_group_lsp_gen $hlt_ret $hlt_ret_route $rsvp_tunnel_params_hdl
            }
        }
    }
}

proc ::sth::hlapiGen::rsvp_custom_object_gen {device custom_handle hlt_ret name_space} {
    set class rsvpcustomobject
    set cmd_name emulation_rsvp_custom_object_config
    set cfg_args ""
   
    if {[info exists sth::hlapiGen::device_ret($custom_handle)]} {
        return;
    }

    get_attr $custom_handle project1
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    }

    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name project1 $custom_handle $class]
    append hlapi_script $cfg_args
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"

    set sth::hlapiGen::device_ret($custom_handle) "$hlt_ret 0"
    puts_to_file [get_device_created $custom_handle $hlt_ret\_hdl handle]

    #store Var name
    set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var) $hlt_ret\_hdl
}


proc ::sth::hlapiGen::rsvp_tunnel_sub_group_lsp_gen {hlt_ret hlt_ret_route rsvp_tunnel_params_hdl} {
    set name_space "::sth::Rsvp::"
    set cmd_name "emulation_rsvp_tunnel_config"

    if {[regexp "rsvpingresstunnelparams" $rsvp_tunnel_params_hdl]} {
        #RsvpP2MpSubGroupParams
        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_params_hdl\_obj(rsvpp2mpsubgroupparams)]} {
            set rsvp_tunnel_p2mp_sub_group_hdl_list [set ::sth::hlapiGen::$rsvp_tunnel_params_hdl\_obj(rsvpp2mpsubgroupparams)]
            set index 0
            foreach rsvp_tunnel_p2mp_sub_group_hdl $rsvp_tunnel_p2mp_sub_group_hdl_list {
                set route_cfg_args ""
                set hlt_ret_sub_grp $hlt_ret\_sub_grp$index
                set sth::hlapiGen::device_ret($rsvp_tunnel_p2mp_sub_group_hdl) "$hlt_ret_sub_grp 0"
                puts_to_file [get_device_created $rsvp_tunnel_params_hdl $hlt_ret_route\_hdl tunnel_handle]
                puts_to_file "#Creating RsvpP2MpSubGroupParams\n"
                append route_cfg_args "      set $hlt_ret_sub_grp \[sth::emulation_rsvp_tunnel_config\\\n"
                append route_cfg_args "-mode                                    create \\\n"
                append route_cfg_args "-element_handle 					\$$hlt_ret_route\_hdl \\\n"
                append route_cfg_args "-element_type                            ingress_p2mp_sub_group \\\n"
                append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_params_hdl $rsvp_tunnel_p2mp_sub_group_hdl RsvpP2MpSubGroupParams]
                append route_cfg_args "\]\n"
                puts_to_file $route_cfg_args
                gen_status_info $hlt_ret_sub_grp "sth::emulation_rsvp_tunnel_config"
                incr index
                
                #RsvpIngressS2lSubLspParams
                if {[info exists ::sth::hlapiGen::$rsvp_tunnel_p2mp_sub_group_hdl\_obj(rsvpingresss2lsublspparams)]} {
                    set rsvp_tunnel_sub_lsp_hdl_list [set ::sth::hlapiGen::$rsvp_tunnel_p2mp_sub_group_hdl\_obj(rsvpingresss2lsublspparams)]
                    set index1 0
                    foreach rsvp_tunnel_sub_lsp_hdl $rsvp_tunnel_sub_lsp_hdl_list {
                        set route_cfg_args ""
                        set hlt_ret_sub_lsp $hlt_ret\_sub_lsp$index1
                        set sth::hlapiGen::device_ret($rsvp_tunnel_sub_lsp_hdl) "$hlt_ret_sub_lsp 0"
                        puts_to_file [get_device_created $rsvp_tunnel_p2mp_sub_group_hdl $hlt_ret_sub_grp\_hdl handle]
                        puts_to_file "#Creating RsvpIngressS2lSubLspParams\n"
                        append route_cfg_args "      set $hlt_ret_sub_lsp \[sth::emulation_rsvp_tunnel_config\\\n"
                        append route_cfg_args "-mode                                    create \\\n"
                        append route_cfg_args "-element_handle 					\$$hlt_ret_sub_grp\_hdl \\\n"
                        append route_cfg_args "-element_type                            ingress_sub_lsp \\\n"
                        append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_p2mp_sub_group_hdl $rsvp_tunnel_sub_lsp_hdl RsvpIngressS2lSubLspParams]
                        append route_cfg_args "\]\n"
                        puts_to_file $route_cfg_args
                        gen_status_info $hlt_ret_sub_lsp "sth::emulation_rsvp_tunnel_config"
                        incr index1

                        #RsvpIpv4EroObject
                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_obj(rsvpipv4eroobject)]} {
                            set rsvp_tunnel_sub_lsp_ero_hdl_list [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_obj(rsvpipv4eroobject)]
                            set index2 0
                            foreach rsvp_tunnel_sub_lsp_ero_hdl $rsvp_tunnel_sub_lsp_ero_hdl_list {
                                set route_cfg_args ""
                                set hlt_ret_sub_lsp_ero $hlt_ret\_sub_lsp_ero$index2
                                set sth::hlapiGen::device_ret($rsvp_tunnel_sub_lsp_ero_hdl) "$hlt_ret_sub_lsp_ero 0"
                                puts_to_file [get_device_created $rsvp_tunnel_sub_lsp_hdl $hlt_ret_sub_lsp\_hdl handle]
                                puts_to_file "#Creating RsvpIpv4EroObject\n"
                                append route_cfg_args "      set $hlt_ret_sub_lsp_ero \[sth::emulation_rsvp_tunnel_config\\\n"
                                append route_cfg_args "-mode                                    create \\\n"
                                append route_cfg_args "-element_handle                        \$$hlt_ret_sub_lsp\_hdl \\\n"
                                append route_cfg_args "-element_type                            ingress_sub_lsp_ero \\\n"
                                append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_sub_lsp_hdl $rsvp_tunnel_sub_lsp_ero_hdl RsvpIpv4EroObject]
                                append route_cfg_args "\]\n"
                                puts_to_file $route_cfg_args
                                gen_status_info $hlt_ret_sub_lsp_ero "sth::emulation_rsvp_tunnel_config"
                                incr index2
                                
                                #RsvpIpv4ExplicitRouteParams 
                                if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_hdl\_obj(rsvpipv4explicitrouteparams)]} {
                                    set rsvp_tunnel_sub_lsp_ero_exp_hdl_list [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_hdl\_obj(rsvpipv4explicitrouteparams)]
                                    set index3 0
                                    foreach rsvp_tunnel_sub_lsp_ero_exp_hdl $rsvp_tunnel_sub_lsp_ero_exp_hdl_list {
                                        set route_cfg_args ""
                                        set hlt_ret_sub_lsp_ero_exp $hlt_ret\_sub_lsp_ero_exp$index3
                                        set sth::hlapiGen::device_ret($rsvp_tunnel_sub_lsp_ero_exp_hdl) "$hlt_ret_sub_lsp_ero_exp 0"
                                        puts_to_file [get_device_created $rsvp_tunnel_sub_lsp_ero_hdl $hlt_ret_sub_lsp_ero\_hdl handle]
                                        puts_to_file "#Creating RsvpIpv4ExplicitRouteParams\n"
                                        append route_cfg_args "      set $hlt_ret_sub_lsp_ero_exp \[sth::emulation_rsvp_tunnel_config\\\n"
                                        append route_cfg_args "-mode                                    create \\\n"
                                        append route_cfg_args "-element_handle                        \$$hlt_ret_sub_lsp_ero\_hdl \\\n"
                                        append route_cfg_args "-element_type                            ingress_sub_lsp_ero_sub_obj \\\n"

                                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_hdl\_attr(-routetype)]} {
                                            set attr_value [string tolower [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_hdl\_attr(-routetype)]]
                                            append route_cfg_args "-ingress_sub_lsp_ero_route_type                    \"$attr_value\" \\\n"
                                        }
                                        
                                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_hdl\_attr(-interfaceid)]} {
                                            set attr_value [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_hdl\_attr(-interfaceid)]
                                            append route_cfg_args "-ingress_sub_lsp_ero_interface_id                    $attr_value \\\n"
                                        }

                                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_exp_hdl\_obj(ipv4networkblock)]} {
                                            set rsvp_tunnel_sub_lsp_ero_exp_ipv4_net_hdl [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_exp_hdl\_obj(ipv4networkblock)]
                                            if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_exp_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_ipv4_net_hdl\_attr(-startiplist)]} {
                                                set attr_value [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_exp_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_ipv4_net_hdl\_attr(-startiplist)]
                                                append route_cfg_args "-ingress_sub_lsp_ero_start_ip_list                    $attr_value \\\n"
                                            }
                                        
                                            if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_exp_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_ipv4_net_hdl\_attr(-prefixlength)]} {
                                                set attr_value [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_ero_exp_hdl\_$rsvp_tunnel_sub_lsp_ero_exp_ipv4_net_hdl\_attr(-prefixlength)]
                                                append route_cfg_args "-ingress_sub_lsp_ero_prefix_length                    $attr_value \\\n"
                                            }
                                        }
                                        append route_cfg_args "\]\n"
                                        puts_to_file $route_cfg_args
                                        gen_status_info $hlt_ret_sub_lsp_ero_exp "sth::emulation_rsvp_tunnel_config"
                                        incr index3
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    } elseif {[regexp "rsvpegresstunnelparams" $rsvp_tunnel_params_hdl]} {
        #RsvpEgressS2lSubLspParams
        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_params_hdl\_obj(rsvpegresss2lsublspparams)]} {
            set rsvp_tunnel_sub_lsp_hdl_list [set ::sth::hlapiGen::$rsvp_tunnel_params_hdl\_obj(rsvpegresss2lsublspparams)]
            set index 0
            foreach rsvp_tunnel_sub_lsp_hdl $rsvp_tunnel_sub_lsp_hdl_list {
                set route_cfg_args ""
                set hlt_ret_egress_sub_lsp $hlt_ret\_egress_sub_lsp$index
                set sth::hlapiGen::device_ret($rsvp_tunnel_sub_lsp_hdl) "$hlt_ret_egress_sub_lsp 0"
                puts_to_file [get_device_created $rsvp_tunnel_params_hdl $hlt_ret_route\_hdl tunnel_handle]
                puts_to_file "#Creating RsvpEgressS2lSubLspParams\n"
                append route_cfg_args "      set $hlt_ret_egress_sub_lsp \[sth::emulation_rsvp_tunnel_config\\\n"
                append route_cfg_args "-mode                                    create \\\n"
                append route_cfg_args "-element_handle 					\$$hlt_ret_route\_hdl \\\n"
                append route_cfg_args "-element_type                            egress_sub_lsp \\\n"
                append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_params_hdl $rsvp_tunnel_sub_lsp_hdl RsvpEgressS2lSubLspParams]
                append route_cfg_args "\]\n"
                puts_to_file $route_cfg_args
                gen_status_info $hlt_ret_egress_sub_lsp "sth::emulation_rsvp_tunnel_config"
                incr index
                
                #RsvpIpv4LsrParams
                if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_obj(rsvpipv4lsrparams)]} {
                    set rsvp_tunnel_egress_ipv4_lsr_hdl_list [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_obj(rsvpipv4lsrparams)]
                    set index1 0
                    foreach rsvp_tunnel_egress_ipv4_lsr_hdl $rsvp_tunnel_egress_ipv4_lsr_hdl_list {
                        set route_cfg_args ""
                        set hlt_ret_sub_lsp_rro $hlt_ret\_sub_lsp_rro$index1
                        set sth::hlapiGen::device_ret($rsvp_tunnel_egress_ipv4_lsr_hdl) "$hlt_ret_sub_lsp_rro 0"
                        puts_to_file [get_device_created $rsvp_tunnel_sub_lsp_hdl $hlt_ret_egress_sub_lsp\_hdl handle]
                        puts_to_file "#Creating RsvpIpv4LsrParams\n"
                        append route_cfg_args "      set $hlt_ret_sub_lsp_rro \[sth::emulation_rsvp_tunnel_config\\\n"
                        append route_cfg_args "-mode                                    create \\\n"
                        append route_cfg_args "-element_handle 					\$$hlt_ret_egress_sub_lsp\_hdl \\\n"
                        append route_cfg_args "-element_type                            egress_sub_lsp_rro \\\n"

                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-frrmergepoint)]} {
                            set attr_value [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-frrmergepoint)]
                            append route_cfg_args "-egress_sub_lsp_rro_frr_merge_point                    $attr_value \\\n"
                        }

                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-interfaceid)]} {
                            set attr_value [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-interfaceid)]
                            append route_cfg_args "-egress_sub_lsp_rro_interface_id                    $attr_value \\\n"
                        }
                        
                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-label)]} {
                            set attr_value [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-label)]
                            append route_cfg_args "-egress_sub_lsp_rro_label                    $attr_value \\\n"
                        }

                        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-rroflags)]} {
                            set attr_value [string tolower [set ::sth::hlapiGen::$rsvp_tunnel_sub_lsp_hdl\_$rsvp_tunnel_egress_ipv4_lsr_hdl\_attr(-rroflags)]]
                            append route_cfg_args "-egress_sub_lsp_rro_flags                    \"$attr_value\" \\\n"
                        }
                        
                        append route_cfg_args "\]\n"
                        puts_to_file $route_cfg_args
                        gen_status_info $hlt_ret_sub_lsp_rro "sth::emulation_rsvp_tunnel_config"
                        incr index1
                    }
                }
            }
        }
    }

}


proc ::sth::hlapiGen::rsvp_tunnel_pre_process {rsvp_hdl rsvp_tunnel_hdl hlt_ret} {
    upvar cfg_args cfg_args_local
    set name_space "::sth::Rsvp::"
    set cmd_name "emulation_rsvp_tunnel_config"
    
    if {[regexp -nocase ingress $rsvp_tunnel_hdl]} {

        #for emulation_multicast_group_config
        set group_pool_handle ""
        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-membergroup-targets)]} {
            set group_pool_handle [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-membergroup-targets)]
            if {[regexp "v4" $group_pool_handle]} {
                set version "v4"
            } else {
                set version "v6"
            }
            #need to create te ipv4 or ipv6group first
            set first_time 1
            if {![info exists sth::hlapiGen::device_ret($group_pool_handle)]} {
                get_attr $group_pool_handle $group_pool_handle
                set tmp_table_name "::sth::multicast_group::multicast_groupTable"
                set tmp_name_space "::sth::multicast_group::"
                set tmp_cmd_name emulation_multicast_group_config
                if {[regexp "6" $version]} {
                    
                    if {[info exists $tmp_name_space$tmp_cmd_name\_Initialized]} {
                        unset $tmp_name_space$tmp_cmd_name\_Initialized
                    }
                    ::sth::sthCore::InitTableFromTCLList [set $table_name]
                    
                    foreach arg "ip_addr_start ip_addr_step ip_prefix_len num_groups pool_name" {
                        set $tmp_name_space$tmp_cmd_name\_stcobj($arg) "Ipv6NetworkBlock"
                    }
                }
                hlapi_gen_device_basic $group_pool_handle ip$version\group create $hlt_ret\_mcastgroup "" $first_time
                set sth::hlapiGen::device_ret($group_pool_handle) "$hlt_ret\_mcastgroup"
                puts_to_file [get_device_created $group_pool_handle "$hlt_ret\_mcastgroup\_hdl" handle]
                if {[info exists $tmp_name_space$tmp_cmd_name\_Initialized]} {
                    unset $tmp_name_space$tmp_cmd_name\_Initialized
                }
            }
            if {[info exists sth::hlapiGen::device_ret($group_pool_handle)]} {
                set varName "$[set sth::hlapiGen::device_ret($group_pool_handle)]\_hdl"
                append cfg_args_local "-ingress_ip_multicast_group   $varName\\\n"
            }
        }

        append cfg_args_local "-direction  ingress\\\n"
        append cfg_args_local "-rsvp_behavior  rsvpIngress\\\n"
        
        #handle flag
        set flag [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-flag)]
        if {$flag != 0} {
            array set paramslist "session_attr_local_protect LOCAL_PROTECTION_DESIRED session_attr_label_record LABLE_RECORD \
            session_attr_se_style SHARED_EXPLICIT session_attr_bw_protect BANDWIDTH_PROTECTION_DESIRED session_attr_node_protect NODE_PROTECTION_DESIRED"
            foreach param [array names paramslist] {
                if {[regexp -nocase $paramslist($param) $flag]} {
                    append cfg_args_local "-$param  1\\\n"
                } else {
                    append cfg_args_local "-$param  0\\\n"
                }
            }
            array unset paramslist
        }
        
        
        #handle FastRerouteObject
        set fastrerouteobject [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-fastrerouteobject)]
        switch -regexp -- [string toupper $fastrerouteobject] {
            "ONE_TO_ONE_BACKUP" {
                set  $name_space$cmd_name\_stcobj(facility_backup) "none"
            }
            "FACILITY_BACKUP" {
                set  $name_space$cmd_name\_stcobj(one_to_one_backup) "none"
            }
        }
        if {[regexp -nocase "none" $fastrerouteobject]} {
            set  $name_space$cmd_name\_stcobj(fast_reroute_bandwidth) "none"
            set  $name_space$cmd_name\_stcobj(fast_reroute_exclude_any) "none"
            set  $name_space$cmd_name\_stcobj(fast_reroute_holding_priority) "none"
            set  $name_space$cmd_name\_stcobj(fast_reroute_hop_limit) "none"
            set  $name_space$cmd_name\_stcobj(fast_reroute_include_all) "none"
            set  $name_space$cmd_name\_stcobj(fast_reroute_include_any) "none"
            set  $name_space$cmd_name\_stcobj(fast_reroute_setup_priority) "none"
        } else {
            append cfg_args_local "-fast_reroute 1\\\n"
        }
        append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_hdl $rsvp_tunnel_hdl RsvpIngressTunnelParams] 
        
        unset ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-flag)
        unset ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-fastrerouteobject)
        # remove egress_ip_addr from rsvpIngress arguments list
        if {[info exists $name_space$cmd_name\_stcattr(egress_ip_addr)] } {
            set attrToRemove [string tolower [set $name_space$cmd_name\_stcattr(egress_ip_addr)]]
            set attrValue [set sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-$attrToRemove)]
            unset sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-$attrToRemove)
        }
        # remove tunnel_count for scaling mode 
        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-count)] } {
            if {[info exists sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-tunnelcount)]} {
                unset sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-tunnelcount)
            }
        }
        append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_hdl $rsvp_tunnel_hdl RsvpTunnelParams]
        # recover deleted Variables
        if {[string length $attrValue] > 0} {
            set sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-$attrToRemove) $attrValue
            unset attrToRemove
            unset attrValue
        }

        #config ero 
        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpipv4eroobject)]} {
            #currently hltapi only create one rsvpipv4eroobject under rsvptunnelparams handle
            set rsvp_ero_hdl [lindex [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpipv4eroobject)] 0]
            if {[info exists ::sth::hlapiGen::$rsvp_ero_hdl\_obj(rsvpipv4explicitrouteparams)]} {
                set ero_list_loose ""
                set ero_list_ipv4 ""
                set ero_list_pfxlen ""
                set i 0
                foreach explicit_route_hdl [set ::sth::hlapiGen::$rsvp_ero_hdl\_obj(rsvpipv4explicitrouteparams)] {
                    #if the start_ip equal the DutIpAddr of the RsvpRouterConfig, it will be the DUT ero which will be
                    #configed with the ero_mode and ero_dut_pfxlen
                    set route_type [set ::sth::hlapiGen::$rsvp_ero_hdl\_$explicit_route_hdl\_attr(-routetype)]
                    set ipv4network_hdl [set ::sth::hlapiGen::$explicit_route_hdl\_obj(ipv4networkblock)]
                    set start_ip [set ::sth::hlapiGen::$explicit_route_hdl\_$ipv4network_hdl\_attr(-startiplist)]
                    set prefixlen [set ::sth::hlapiGen::$explicit_route_hdl\_$ipv4network_hdl\_attr(-prefixlength)]
                    switch -regexp -- [string tolower $route_type] {
                        "rsvp_strict" {
                            set route_type 0
                            set dut_route_type "strict"
                        }
                        "rsvp_loose" {
                            set route_type 1
                            set dut_route_type "loose"
                        }
                    }
                    if {[stc::get $rsvp_hdl -DutIpAddr] == $start_ip} {
                        set dut_route $dut_route_type
                        set ero_dut_pfxlen $prefixlen
                    } else {
                        set ero_list_loose [concat $ero_list_loose $route_type]
                        set ero_list_ipv4 [concat $ero_list_ipv4 $start_ip]
                        set ero_list_pfxlen [concat $ero_list_pfxlen $prefixlen]
                    }
                    incr i
                }
                if {[info exists dut_route]} {
                    append cfg_args_local "-ero_mode  $dut_route\\\n"
                    append cfg_args_local "-ero_dut_pfxlen  $ero_dut_pfxlen\\\n"
                    append cfg_args_local "-ero  1\\\n"
                } 
                if {$ero_list_loose != ""} {
                    append cfg_args_local "-ero_list_loose  \{$ero_list_loose\}\\\n"
                    append cfg_args_local "-ero_list_ipv4  \{$ero_list_ipv4\}\\\n"
                    append cfg_args_local "-ero_list_pfxlen  \{$ero_list_pfxlen\}\\\n"
                    append cfg_args_local "-ero  1\\\n"
                }
            }
        }
        
        #config RsvpDetourSubObject:
        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpdetoursubobject)]} {
            #hltapi doesn't support a list input for below parameters now
            set detour_hdl [lindex [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpdetoursubobject)] 0]
            append cfg_args_local "-send_detour 1\\\n"
            append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_hdl $detour_hdl RsvpDetourSubObject]
        }
        
        #config RsvpGmplsParams:
        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpgmplsparams)]} {
            #hltapi doesn't support a list input for below parameters now
            set gmpls_hdl [lindex [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpgmplsparams)] 0]
            append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_hdl $gmpls_hdl RsvpGmplsParams]
        }
        
        #Custom object configs
        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-pathcustomobject-sources)] } {
            set customHndVar ""
            set custom_handle_list [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-pathcustomobject-sources)]
            foreach custom_handle $custom_handle_list {
                append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
            }
            set customHndVar [lsort $customHndVar]
            regsub -all {\{|\}} $customHndVar "" customHndVar 
            append cfg_args_local "-ingress_path_custom_object_list  \"$customHndVar\"\\\n"
        }
        #Custom object configs
        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-pathtearcustomobject-sources)] } {
            set customHndVar ""
            set custom_handle_list [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-pathtearcustomobject-sources)]
            foreach custom_handle $custom_handle_list {
                append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
            }
            set customHndVar [lsort $customHndVar]
            regsub -all {\{|\}} $customHndVar "" customHndVar 
            append cfg_args_local "-ingress_path_tear_custom_object_list  \"$customHndVar\"\\\n"
        }

        #Multicast configs
    } else {
        append cfg_args_local "-direction  egress\\\n"
        append cfg_args_local "-rsvp_behavior  rsvpEgress\\\n"

        append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_hdl $rsvp_tunnel_hdl RsvpEgressTunnelParams]
        # remove ingress_ip_addr from rsvpIngress arguments list
        if {[info exists $name_space$cmd_name\_stcattr(ingress_ip_addr)] } {
            set attrToRemove [string tolower [set $name_space$cmd_name\_stcattr(ingress_ip_addr)]]
            set attrValue [set sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-$attrToRemove)]
            unset sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-$attrToRemove)
        }
        # remove tunnel_count for scaling mode
        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-count)] } {
            if {[info exists sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-tunnelcount)]} {
                unset sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-tunnelcount)
            }
        }
        append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_hdl $rsvp_tunnel_hdl RsvpTunnelParams]
        # recover deleted Variables
        if {[string length $attrValue] > 0} {
            set sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-$attrToRemove) $attrValue
            unset attrToRemove
            unset attrValue
        }
        #config RsvpGmplsParams:
        if {[info exists ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpgmplsparams)]} {
            #hltapi doesn't support a list input for below parameters now
            set gmpls_hdl [lindex [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpgmplsparams)] 0]
            append cfg_args_local [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rsvp_tunnel_hdl $gmpls_hdl RsvpGmplsParams]
        }
        
        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-reservationcustomobject-sources)] } {
            set customHndVar ""
            set custom_handle_list [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-reservationcustomobject-sources)]
            foreach custom_handle $custom_handle_list {
                append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
            }
            set customHndVar [lsort $customHndVar]
            regsub -all {\{|\}} $customHndVar "" customHndVar 
            append cfg_args_local "-egress_resv_custom_object_list  \"$customHndVar\"\\\n"
        }

        if {[info exists ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-reservationtearcustomobject-sources)] } {
            set customHndVar ""
            set custom_handle_list [set ::sth::hlapiGen::$rsvp_hdl\_$rsvp_tunnel_hdl\_attr(-reservationtearcustomobject-sources)]
            foreach custom_handle $custom_handle_list {
                append customHndVar "$[set sth::hlapiGen::project1\_$custom_handle\_attr(-handle_var)] "
            }
            set customHndVar [lsort $customHndVar]
            regsub -all {\{|\}} $customHndVar "" customHndVar 
            append cfg_args_local "-egress_resv_tear_custom_object_list  \"$customHndVar\"\\\n"
        }
        #config rro, the user doc lists the rro related parameters in the unsupported parameters list, so comment this code snap
        #if {[info exists ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpipv4lsrparams)]} {
        #    set rro_list_label ""
        #    set rro_frr_merge_point ""
        #    set rro_list_ipv4 ""
        #    set rro_list_pfxlen ""
        #    foreach lsr_params_hdl [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_obj(rsvpipv4lsrparams)] {
        #        set merge_point [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_$lsr_params_hdl\_attr(-frrmergepoint)]
        #        set label_var [set ::sth::hlapiGen::$rsvp_tunnel_hdl\_$lsr_params_hdl\_attr(-label)]
        #        set ipv4network_hdl [set ::sth::hlapiGen::$lsr_params_hdl\_obj(ipv4networkblock)]
        #        set start_ip [set ::sth::hlapiGen::$lsr_params_hdl\_$ipv4network_hdl\_attr(-startiplist)]
        #        set prefixlen [set ::sth::hlapiGen::$lsr_params_hdl\_$ipv4network_hdl\_attr(-prefixlength)]
        #        if {[regexp -nocase "false" $merge_point]} {
        #            set merge_point 0
        #        } else {
        #            set merge_point 1
        #        }
        #        set rro_list_label [concat $rro_list_label $label_var]
        #        set rro_frr_merge_point [concat $rro_frr_merge_point $merge_point]
        #        set rro_list_ipv4 [concat $rro_list_ipv4 $start_ip]
        #        set rro_list_pfxlen [concat $rro_list_pfxlen $prefixlen]
        #    }
        #    append cfg_args_local "-rro  1\\\n"
        #    append cfg_args_local "-rro_list_label  $rro_list_label\\\n"
        #    append cfg_args_local "-rro_frr_merge_point  $rro_frr_merge_point\\\n"
        #    append cfg_args_local "-rro_list_ipv4  $rro_list_ipv4\\\n"
        #    append cfg_args_local "-rro_list_pfxlen  $rro_list_pfxlen\\\n"
        #    append cfg_args_local "-rro_list_type  ipv4\\\n"
        #}
    }
}

proc ::sth::hlapiGen::hlapi_gen_device_ripconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    set name_space "::sth::rip::"
    set cmd_name "emulation_rip_config"
    ::sth::sthCore::InitTableFromTCLList $::sth::rip::ripTable
     
    #pre-process the tunnel handle, to config this, need to call the gre config function
    if {[info exists sth::hlapiGen::$device\_obj(greif)]} {
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args
        append cfg_args "                       -tunnel_handle              \$gre_ret\\\n"
    }
    
    #update the stcobj and stcattr
    set router_paramlist "count router_id router_id_step"
    regsub {\d+$} $device "" update_obj
    foreach router_param $router_paramlist {
        set $name_space$cmd_name\_stcobj($router_param) "$update_obj"
    }

    #update the stcattr of vlan_id_mode and vlan_id_step
    set $name_space$cmd_name\_stcattr(vlan_id_mode) "vlanid.mode"
    set $name_space$cmd_name\_stcattr(vlan_outer_id_mode) "vlanid.mode"
    
    set riphdl [set ::sth::hlapiGen::$device\_obj($class)]
    set rip_version [set ::sth::hlapiGen::$device\_$riphdl\_attr(-ripversion)]
    switch -regexp -- [string tolower $rip_version] {
        "v1" -
        "v2" {
            set route_type "Ripv4RouteParams"
            set intf_type "ipv4if"
        }
        "ng" {
            set route_type "RipngRouteParams"
            set intf_type "ipv6if"
        }
    }
    
    set paramslist "intf_ip_addr intf_ip_addr_step intf_prefix_length gateway_ip_addr gateway_ip_addr_step"
    foreach param $paramslist {
        set $name_space$cmd_name\_stcobj($param) $intf_type
    }
    set ipv6_paramslist "link_local_intf_ip_addr link_local_intf_ip_addr_step link_local_intf_prefix_len"
    foreach param $ipv6_paramslist {
        set $name_space$cmd_name\_stcobj($param) "Ipv6If_Link_Local"
    }

    set updatetype [set ::sth::hlapiGen::$device\_$riphdl\_attr(-updatetype)]
    if {[regexp -nocase "unicast" $updatetype]} {
        set dutip_paramslist "neighbor_intf_ip_addr neighbor_intf_ip_addr_step"
        foreach param $dutip_paramslist {
            set $name_space$cmd_name\_stcobj($param) "RipRouterConfig"
        }
    }
    regsub "if" $intf_type "addr" attr
    set attr dut$attr
    set $name_space$cmd_name\_stcattr(neighbor_intf_ip_addr) $attr
    set $name_space$cmd_name\_stcattr(neighbor_intf_ip_addr_step) $attr\.step

    if {[set ::sth::hlapiGen::$device\_$riphdl\_attr(-$attr)] == "null"} {
        set ipif [set ::sth::hlapiGen::$device\_obj($intf_type)]
        if {[regexp -nocase "ipv6if" $ipif]} {
            if {[llength $ipif] > 1} {
                set ipif [lindex $ipif 1]
            }
            set ::sth::hlapiGen::$device\_$riphdl\_attr(-$attr) [set ::sth::hlapiGen::$device\_$ipif\_attr(-address)]
            if {$::sth::hlapiGen::scaling_test && $first_time && [info exists ::sth::hlapiGen::$device\_$ipif\_attr(-address.step)]} {
                set ::sth::hlapiGen::$device\_$riphdl\_attr(-$attr\.step) [set ::sth::hlapiGen::$device\_$ipif\_attr(-address.step)]
            }
        } else {
            set ::sth::hlapiGen::$device\_$riphdl\_attr(-$attr) [set ::sth::hlapiGen::$device\_$ipif\_attr(-gateway)]
            if {$::sth::hlapiGen::scaling_test && $first_time && [info exists ::sth::hlapiGen::$device\_$ipif\_attr(-gateway.step)]} {
                set ::sth::hlapiGen::$device\_$riphdl\_attr(-$attr\.step) [set ::sth::hlapiGen::$device\_$ipif\_attr(-gateway.step)]
            }
        }
    }
    
    #set the step attribute for scaling mode
    if {$::sth::hlapiGen::scaling_test && $first_time} {
        array set stepattrlist "intf_ip_addr_step Address link_local_intf_ip_addr_step Address gateway_ip_addr_step Gateway\
                                    router_id_step RouterId vlan_id_step VlanId vlan_outer_id_step VlanId"
        foreach param [array name stepattrlist] {
            set $name_space$cmd_name\_stcattr($param) $stepattrlist($param)\.step
        }
        array unset stepattrlist
    }
    
    if {[regexp -nocase "v2" $rip_version]} {
        set rip_auth_hdl [set ::sth::hlapiGen::$riphdl\_obj(ripauthenticationparams)]
        if {[regexp -nocase "none" [set ::sth::hlapiGen::$riphdl\_$rip_auth_hdl\_attr(-authentication)]]} {
            append cfg_args "-authentication_mode   null\\\n"
        } elseif {[regexp -nocase "simple" [set ::sth::hlapiGen::$riphdl\_$rip_auth_hdl\_attr(-authentication)]]} {
            append cfg_args "-authentication_mode   text\\\n"
            append cfg_args "-password   [set ::sth::hlapiGen::$riphdl\_$rip_auth_hdl\_attr(-password)]\\\n"
        } elseif {[regexp -nocase "MD5" [set ::sth::hlapiGen::$riphdl\_$rip_auth_hdl\_attr(-authentication)]]} {
            append cfg_args "-authentication_mode   md5\\\n"
            append cfg_args "-md5_key   [set ::sth::hlapiGen::$riphdl\_$rip_auth_hdl\_attr(-password)]\\\n"
            append cfg_args "-md5_key_id   [set ::sth::hlapiGen::$riphdl\_$rip_auth_hdl\_attr(-md5keyid)]\\\n"
        }
    }

    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    
    #process the rsvp tunnel config
    set devicelist [update_device_handle $device $class $first_time]
    
    #the device need update in scaling mode
    set i 0
    set update_table 1
    foreach device $devicelist {
        set riphdl [set ::sth::hlapiGen::$device\_obj($class)]
        if {[info exists ::sth::hlapiGen::$riphdl\_obj([string tolower $route_type])]} {
            puts_to_file [get_device_created $device $hlt_ret\_hdl handle]
            foreach rip_route_hdl [set ::sth::hlapiGen::$riphdl\_obj([string tolower $route_type])] {
                set route_cfg_args ""
                set cmd_name "emulation_rip_route_config"
                set hlt_ret_route $hlt_ret\_route$i
                set sth::hlapiGen::device_ret($rip_route_hdl) $hlt_ret_route
                regsub "if" $intf_type "networkblock" netblk_type
                if {$update_table == 1} {
                    set route_paramslist "metric next_hop route_tag"
                    foreach param $route_paramslist {
                        set $name_space$cmd_name\_stcobj($param) $route_type
                    }
                    set route_netblk_paramslist "num_prefixes prefix_length prefix_start prefix_step"
                    foreach param $route_netblk_paramslist {
                        set $name_space$cmd_name\_stcobj($param) $netblk_type
                    }
                    
                    set update_table 0
                }
                
                if {[set ::sth::hlapiGen::$riphdl\_$rip_route_hdl\_attr(-nexthop)] == "null"} {
                    set ipif [set ::sth::hlapiGen::$device\_obj($intf_type)]
                    if {[regexp -nocase "ipv6if" $ipif]} {
                        set ipif [lindex $ipif 1]
                        set ::sth::hlapiGen::$riphdl\_$rip_route_hdl\_attr(-nexthop) [set ::sth::hlapiGen::$device\_$ipif\_attr(-address)]
                    } else {
                        set ::sth::hlapiGen::$riphdl\_$rip_route_hdl\_attr(-nexthop) [set ::sth::hlapiGen::$device\_$ipif\_attr(-address)]
                    }
                }
                    
                set network_blk_hdl [set ::sth::hlapiGen::$rip_route_hdl\_obj($netblk_type)]
                append route_cfg_args "      set $hlt_ret_route \[sth::$cmd_name\\\n"
                append route_cfg_args "-mode                                    create \\\n"
                append route_cfg_args "-handle 					\$$hlt_ret\_hdl \\\n"
                append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $riphdl $rip_route_hdl $route_type]
                append route_cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $rip_route_hdl $network_blk_hdl $netblk_type]
                append route_cfg_args "\]\n"
                puts_to_file $route_cfg_args
                gen_status_info $hlt_ret_route "sth::$cmd_name"
                incr i
            }
        }
    }
}

proc ::sth::hlapiGen::multi_dev_check_func_rsvp {class devices} {
    variable devicelist_obj
    variable scaling_tmp
    set update_obj [multi_dev_check_func_basic $class $devices]     
    
    set attrlist "DutIpAddr"
    foreach obj $update_obj {
        if {[info exists devicelist_obj($obj)]} {
            set device0 [lindex $devicelist_obj($obj) 0]
            set rsvprouter0 [set ::sth::hlapiGen::$device0\_obj(rsvprouterconfig)]
            if {[set ::sth::hlapiGen::$device0\_$rsvprouter0\_attr(-dutipaddr)] == "null" && [info exists ::sth::hlapiGen::$device0\_obj(ipv4if)]} {
                #if current dutipaddr is null, set the gateway as dutipaddr
                set ipv4if [set ::sth::hlapiGen::$device0\_obj(ipv4if)]
                if {[llength $ipv4if] > 1} {
                    set ipv4iflist $ipv4if
                    foreach ipv4if $ipv4iflist {
                        set stacked_target [stc::get $ipv4if -stackedonendpoint-Targets]
                        if {[regexp -nocase "ethiiif" $stacked_target]} {
                            break
                        }
                    }
                }
                set ::sth::hlapiGen::$device0\_$rsvprouter0\_attr(-dutipaddr) [set ::sth::hlapiGen::$device0\_$ipv4if\_attr(-gateway)]
                set scaling_tmp($device0\_$rsvprouter0\_dutipaddr.step) $scaling_tmp($device0\_$ipv4if\_gateway.step)
            } else {
                #call update-step to update the step value of bgprouterconfig obj
                if {[info exists devicelist_obj($obj)]} {
                    update_step $class $devicelist_obj($obj) $attrlist ""
                }
            }
        }
    }
    return $update_obj
}


proc ::sth::hlapiGen::hlapi_gen_device_ptp {device class mode hlt_ret cfg_args first_time} {
    
    set ieee1588v2clockconfig [stc::get $device -children-$class]
    set ieee1588v2clockconfig [lindex $ieee1588v2clockconfig 0]
    
    #handle name
    set name [stc::get $device -Name]
    if {$name ne ""} {
        set name [join [split $name " "] "_"]
        append cfg_args "     -name    \"$name\"\\\n"
    }
    
    #pre_process the encapsulation
    variable $device\_obj
    if {[info exists $device\_obj(ethiiif)]} {
        if {[info exists $device\_obj(aal5if)]} {
            set aal5if [set $device\_obj(aal5if)]
            set vc_encap [set sth::hlapiGen::$device\_$aal5if\_attr(-vcencapsulation)]
            if {[regexp -nocase "LLC_ENCAPSULATED" $vc_encap]} {
                append cfg_args "-encapsulation    ETHERNETII_LLC_SNAP\\\n"
            } else {
                append cfg_args "-encapsulation    ETHERNETII_VC_MUX\\\n"
            }
        } else {
            append cfg_args "-encapsulation   ETHERNETII\\\n"
        }
    } elseif {[info exists $device\_obj(aal5if)]} {
        set aal5if [set $device\_obj(aal5if)]
        set vc_encap [set sth::hlapiGen::$device\_$aal5if\_attr(-vcencapsulation)]
        if {[regexp -nocase "LLC_ENCAPSULATED" $vc_encap]} {
            append cfg_args "-encapsulation    LLC_SNAP\\\n"
        } else {
            append cfg_args "-encapsulation    VC_MUX\\\n"
        }
    }
    
    set table_name "::sth::Ptp::PtpTable"
    set name_space [string range $table_name 0 [string last : $table_name]]    
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_ptp_config
    
    #handle stcobj for count
    regsub {\d+$} $device "" update_obj
    set $name_space$cmd_name\_stcobj(count) "$update_obj"
    
    #handle ptp_clock_id_step
    set $name_space$cmd_name\_stcobj(ptp_clock_id_step) "Ieee1588v2ClockConfig"
    set $name_space$cmd_name\_stcattr(ptp_clock_id_step) "ClockIdentity.step"
    
    
    #handle ptp_clock_id-Ieee1588v2ClockConfig-ClockIdentity
    set ptp_clock_id [set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-clockidentity)]
    set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-clockidentity) [format "0x%lx" $ptp_clock_id]
    
    #handle log_sync_message_interval-Ieee1588v2ClockConfig-LogSyncInterval
    set log_sync_message_interval [set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-logsyncinterval)]
    if {($log_sync_message_interval >= -5) && ($log_sync_message_interval <= 5)} {
        if {$log_sync_message_interval < 0} {
            set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-logsyncinterval) "{\"$log_sync_message_interval\"}"
        }
    } else {
        set $name_space$cmd_name\_stcattr(log_sync_message_interval) "_none_"
    }
    
    #handle log_minimum_delay_request_interval-Ieee1588v2ClockConfig-LogMinDelayRequestInterval
    set log_minimum_delay_request_interval [set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-logmindelayrequestinterval)]
    if {($log_minimum_delay_request_interval >= -5) && ($log_minimum_delay_request_interval <= 5)} {
        if {$log_minimum_delay_request_interval < 0} {
            set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-logmindelayrequestinterval) "{\"$log_minimum_delay_request_interval\"}"
        }
    } else {
        set $name_space$cmd_name\_stcattr(log_minimum_delay_request_interval) "_none_"
    }
    
    #vlan_id_mode1
    #vlan_id_mode2
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        foreach vlanif $vlanifs {
            set tpid [set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid)]
            set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid) [format "0x%04x" $tpid]
            set stack_target [set ::sth::hlapiGen::$device\_$vlanif\_attr(-stackedonendpoint-targets)]
            set isrange [set ::sth::hlapiGen::$device\_$vlanif\_attr(-isrange)]
            if {[regexp -nocase "true" $isrange]} {
                set vlan_mode "increment"
            } else {
                set vlan_mode "fixed"
            }
            if {[llength $vlanifs] > 1} {
                if {[regexp {ethiiif} $stack_target]} {
                    append cfg_args "     -vlan_id_mode2    $vlan_mode\\\n"
                } else {
                    append cfg_args "     -vlan_id_mode1    $vlan_mode\\\n"
                }
            } else {
                append cfg_args "     -vlan_id_mode1    $vlan_mode\\\n"
            }
        }
    }
    
    #handle the dependency between enable_correction and sync_correction/followup_correction/delay_request_correction/delay_response_correction
    if {[set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-configcorrectionfield)] eq "false"} {
        set $name_space$cmd_name\_stcattr(sync_correction) "_none_"
        set $name_space$cmd_name\_stcattr(followup_correction) "_none_"
        set $name_space$cmd_name\_stcattr(delay_request_correction) "_none_"
        set $name_space$cmd_name\_stcattr(delay_response_correction) "_none_"
    }
    
    #handle tos_xxx and diff_xxx in ipv4
    if {[set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-encap)] eq "UDP_IPV4"} {
        set ipv4if [lindex [stc::get $device -children-ipv4if] 0]
        set tosvalue [stc::get $ipv4if -Tos]
        #handle tos
        if {[set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tostype)] eq "TOS"} {
            
            #handle ip_tos_field, default support this kind of parameter, same in DIFFSERV
            append cfg_args "     -ip_tos_field    [format "0x%x" $tosvalue]\\\n"

            #handle all Tos attr
            if {0} {
                #need also change hltapi config table
                set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tos_precedence)    [sth::hlapiGen::decimal2binary [expr [expr $tosvalue >> 5] & 0x3] 3]
                set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tos_delay)         [sth::hlapiGen::decimal2binary [expr [expr $tosvalue >> 4] & 0x1] 1]
                set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tos_throughput)    [sth::hlapiGen::decimal2binary [expr [expr $tosvalue >> 3] & 0x1] 1]
                set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tos_reliability)   [sth::hlapiGen::decimal2binary [expr [expr $tosvalue >> 2] & 0x1] 1]
                set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tos_monetary_cost) [sth::hlapiGen::decimal2binary [expr [expr $tosvalue >> 1] & 0x1] 1]
                set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tos_unused)        "0x[sth::hlapiGen::decimal2binary [expr $tosvalue & 0x1] 1]"
            }
        }
        #handle diff
        if {[set ::sth::hlapiGen::$device\_$ipv4if\_attr(-tostype)] eq "DIFFSERV"} {
                append cfg_args "     -diff_default    [format "%d" $tosvalue]\\\n"
        }
    }
    
    #for scaling
    if {[info exists ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-clockidentity.step)]} {
        append cfg_args "     -ptp_clock_id_mode    increment\\\n"
        set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-clockidentity.step) \
        [format "0x%x" [set ::sth::hlapiGen::$device\_$ieee1588v2clockconfig\_attr(-clockidentity.step)]]
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}



proc ::sth::hlapiGen::multi_dev_check_func_ptp {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]
                    
    set attrlist "ClockIdentity"
    foreach obj $update_obj {
        #call update-step to update the step value of bgprouterconfig obj
        if {[info exists devicelist_obj($obj)]} {
            update_step $class $devicelist_obj($obj) $attrlist ""
        }
    }   
    return $update_obj
}

proc ::sth::hlapiGen::multi_dev_check_func_rip {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]
                    
    set attrlist "DutIpv4Addr DutIpv6Addr"
    foreach obj $update_obj {
        #call update-step to update the step value of bgprouterconfig obj
        if {[info exists devicelist_obj($obj)]} {
            update_step $class $devicelist_obj($obj) $attrlist ""
            set devicehdl [lindex $devicelist_obj($obj) 0]
            set subobjhdl [lindex [set ::sth::hlapiGen::$devicehdl\_obj($class)] 0]
        }
    }
    return $update_obj
}
proc ::sth::hlapiGen::hlapi_gen_device_sip {device class mode hlt_ret cfg_args first_time} {
    #vlan_ether_type1, vlan_ether_type2
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        
        foreach vlanif $vlanifs {
            set tpid [set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid)]
            set tpid_update [format "0x%04x" $tpid]
            set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid) $tpid_update
        }
    }    
    #call_accept_delay_enable
    #gateway_enable
    #gateway_ipv4_address
    
    
    #local_ip_addr_step Address
    #remote_ip_addr_step  GatewayStep
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        set ipv4if [set ::sth::hlapiGen::$device\_obj(ipv4if)]
        
        set local_ip_addr_step [set ::sth::hlapiGen::$device\_$ipv4if\_attr(-addrstep)]
        set local_ip_addr_step [ipaddr2dec $local_ip_addr_step]
        set ::sth::hlapiGen::$device\_$ipv4if\_attr(-addrstep) $local_ip_addr_step
        set remote_ip_addr_step [set ::sth::hlapiGen::$device\_$ipv4if\_attr(-gatewaystep)]
        set remote_ip_addr_step [ipaddr2dec $remote_ip_addr_step]
        set ::sth::hlapiGen::$device\_$ipv4if\_attr(-gatewaystep) $remote_ip_addr_step
    }
    
    #output ip_version which is added for enhancement of dual stack of sip
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv6if)]} {
        if {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
            append cfg_args "-ip_version 4_6\\\n"
        } else {
            append cfg_args "-ip_version 6\\\n"
        }
    }   
    #SipUaProtocolProfile this is under clientProfile
    set sip_ua_config [set sth::hlapiGen::$device\_obj(sipuaprotocolconfig)]
    set client_profile [set sth::hlapiGen::$device\_$sip_ua_config\_attr(-affiliatedclientprofile-targets)]
    set sip_ua_protocol [stc::get $client_profile -children-SipUaProtocolProfile]
    get_attr $sip_ua_protocol $sip_ua_protocol
    set registration_server_enable [set sth::hlapiGen::$sip_ua_protocol\_$sip_ua_protocol\_attr(-useuatouasignaling)]
    
    if {[info exists sth::hlapiGen::$device\_$sip_ua_config\_attr(-connectiondestination-targets)]} {
        set connected_sip_ua_config [set sth::hlapiGen::$device\_$sip_ua_config\_attr(-connectiondestination-targets)]
        
    } elseif {[info exists sth::hlapiGen::$device\_$sip_ua_config\_attr(-connectiondestination-sources)]} {
        set connected_sip_ua_config [set sth::hlapiGen::$device\_$sip_ua_config\_attr(-connectiondestination-sources)]
    }
    if {[info exists connected_sip_ua_config]} {
        set connected_device [stc::get $connected_sip_ua_config -parent]
        
        if {[regexp -nocase "false" $registration_server_enable]} {
            #remote_username_prefix, remote_username_suffix, remote_username_suffix_step, call_using_aor
            set remote_username_prefix [set sth::hlapiGen::$connected_device\_$connected_sip_ua_config\_attr(-uanumformat)]
            set remote_username_prefix [regsub {%.+} $remote_username_prefix ""]
            set remote_username_suffix [set sth::hlapiGen::$connected_device\_$connected_sip_ua_config\_attr(-uanumstart)]
            set remote_username_suffix_step [set sth::hlapiGen::$connected_device\_$connected_sip_ua_config\_attr(-uanumstep)]
            
            foreach arg "remote_username_prefix remote_username_suffix remote_username_suffix_step" {
                append cfg_args        "-$arg       [set $arg]\\\n"
            }
            
        } else {
            #remote_host, remote_host_repeat, remote_host_step
            #add dualstack for sip
            if {[info exists sth::hlapiGen::$connected_device\_obj(ipv4if)]} {
                set callee_ip [set sth::hlapiGen::$connected_device\_obj(ipv4if)]
            } elseif {[info exists sth::hlapiGen::$connected_device\_obj(ipv6if)]} {
                set ipv6If [set sth::hlapiGen::$connected_device\_obj(ipv6if)]
                foreach ipIf $ipv6If {
                    set ipaddr [::sth::sthCore::invoke stc::get $ipIf -Address]
                    if {![regexp -nocase "FE80" $ipaddr]} {
                        set callee_ip $ipIf
                    }
                }
                set local_ip_addr_repeat [set sth::hlapiGen::$connected_device\_$ipIf\_attr(-addrrepeatcount)]
                set sth::hlapiGen::$connected_device\_$ipIf\_attr(-addrrepeatcount) [expr $local_ip_addr_repeat + 1]
            }
            set remote_host [set sth::hlapiGen::$connected_device\_$callee_ip\_attr(-address)]
            set remote_host_repeat [set sth::hlapiGen::$connected_device\_$callee_ip\_attr(-addrrepeatcount)]
            set remote_host_step [set sth::hlapiGen::$connected_device\_$callee_ip\_attr(-addrstep)]
            if {[regexp {\.} $remote_host_step]} {
                set remote_host_step [ipaddr2dec $remote_host_step]
            }
            set call_using_aor 1
            
            foreach arg "remote_host remote_host_repeat remote_host_step call_using_aor" {
                append cfg_args        "-$arg       [set $arg]\\\n"
            }
        }
    } else {
        if {[regexp -nocase "true" $registration_server_enable]} {
            append cfg_args        " -call_using_aor 1\\\n"
        }
    }
    
    #local_ip_addr_repeat  remote_ip_addr_repeat
    # in hltapi remote_ip_addr_repeat is equal to [AddrRepeatCount+1];
    # remote_ip_addr_repeat is euqal to [GatewayRepeatCount + 1]
    if {[info exists sth::hlapiGen::$device\_obj(ipv4if)]} {
        set ipv4if [set sth::hlapiGen::$device\_obj(ipv4if)]
        set local_ip_addr_repeat [set sth::hlapiGen::$device\_$ipv4if\_attr(-addrrepeatcount)]
        set sth::hlapiGen::$device\_$ipv4if\_attr(-addrrepeatcount) [expr $local_ip_addr_repeat + 1]
        set remote_ip_addr_repeat [set sth::hlapiGen::$device\_$ipv4if\_attr(-gatewayrepeatcount)]
        set sth::hlapiGen::$device\_$ipv4if\_attr(-gatewayrepeatcount) [expr $remote_ip_addr_repeat + 1]
    }
    ::sth::sthCore::InitTableFromTCLList $::sth::sip::sipTable
    #if it is ipv6 version, we need to unset the ipv4if stcobj, or else the ipv4if whose parent is port will be configured here
    
    if {![info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        set arglist "local_ip_addr local_ip_addr_step local_ip_addr_repeat remote_ip_addr remote_ip_addr_step remote_ip_addr_repeat"
        foreach arg $arglist {
            set ::sth::sip::emulation_sip_config_stcobj($arg) "_none_"
        }
    }
    append cfg_args [config_obj_attr ::sth::sip:: emulation_sip_config $sip_ua_protocol $sip_ua_protocol sipuaprotocolprofile]
    
    set local_username_prefix [set sth::hlapiGen::$device\_$sip_ua_config\_attr(-uanumformat)]
    set local_username_prefix [regsub {%.+} $local_username_prefix ""]
    set sth::hlapiGen::$device\_$sip_ua_config\_attr(-uanumformat) $local_username_prefix
    
    #handle the vlan_id_mode1 and vlan_id_mode2
    if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set sth::hlapiGen::$device\_obj(vlanif)]
        
        if {[llength $vlanifs] > 1} {
            foreach vlanif $vlanifs {
                set vlan_stack_on [set sth::hlapiGen::$device\_$vlanif\_attr(-stackedonendpoint-targets)]
                if {[regexp "vlanif" $vlan_stack_on]} {
                    set vlanif_inner $vlanif
                } else {
                    set vlanif_outer $vlanif
                }
            }
            #vlan_id_mode2
            set vlan_step [set sth::hlapiGen::$device\_$vlanif_outer\_attr(-idstep)]
            if {$vlan_step == 0} {
                append cfg_args   "-vlan_id_mode2       fixed\\\n"
            } else {
                append cfg_args   "-vlan_id_mode2       increment\\\n"
            }
            
        } else {
            set vlanif_inner $vlanifs
        }
        #vlan_id_mode1
        set vlan_step [set sth::hlapiGen::$device\_$vlanif_inner\_attr(-idstep)]
        if {$vlan_step == 0} {
            append cfg_args   "-vlan_id_mode1       fixed\\\n"
        } else {
            append cfg_args   "-vlan_id_mode1       increment\\\n"
        }
    }
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
}


proc ::sth::hlapiGen::sort_sip_pri sip_ua_config_list {
    set sip_with_connection ""
    set sip_without_connection ""
    foreach sip_ua_config $sip_ua_config_list {
        set sip_device [stc::get $sip_ua_config -parent]
        if {[info exists sth::hlapiGen::$sip_device\_$sip_ua_config\_attr(-connectiondestination-targets)]} {
            set sip_with_connection [concat $sip_with_connection $sip_ua_config]
        } else {
            set sip_without_connection [concat $sip_without_connection $sip_ua_config]
        }
    }
    set new_sip_ua_config_list [concat $sip_without_connection $sip_with_connection]
}


proc ::sth::hlapiGen::hlapi_gen_device_stp {device class mode hlt_ret cfg_args first_time} {

    set bridgeportconfig [stc::get $device -children-$class]
    set bridgeportconfig [lindex $bridgeportconfig 0]

    set port [stc::get $device -affiliationport-Targets]
    set stpportconfig [stc::get $port -children-stpportconfig]
    set stp_type [stc::get $stpportconfig -StpType]
    set port_type [stc::get $stpportconfig -PortType]

    if {[regexp -nocase "mstpregionconfig" [stc::get $stpportconfig]]} {
        set mstpregionconfig [stc::get $stpportconfig -memberof-Sources]
    }

    if {[regexp -nocase "mstpbridgeportconfig" [stc::get $bridgeportconfig]]} {
        set mstpbridgeportconfig [stc::get $bridgeportconfig -children-mstpbridgeportconfig]
        if {[regexp -nocase "msticonfig" [stc::get $mstpbridgeportconfig]]} {
            set msticonfigList [stc::get $mstpbridgeportconfig -children-msticonfig]
        }
    }

    set stpbridgeportconfig [stc::get $bridgeportconfig -children-stpbridgeportconfig]
    if {$stpbridgeportconfig ne ""} {
        set vlanblock [stc::get $stpbridgeportconfig -children-vlanblock]
    }

    set table_name "::sth::Stp::stpTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_stp_config

    #handle stcobj for count
    regsub {\d+$} $device "" update_obj
    set $name_space$cmd_name\_stcobj(count) "$update_obj"

    if {$stp_type eq "MSTP"} {
        if {[info exists mstpbridgeportconfig]} {
            append cfg_args "     -region_root_bridge_type    [string tolower [stc::get $mstpbridgeportconfig -RegionRootBridge]]\\\n"
            append cfg_args "     -region_root_priority    [stc::get $mstpbridgeportconfig -CistRegionalRootPriority]\\\n"
            append cfg_args "     -region_root_mac_address    [stc::get $mstpbridgeportconfig -CistRegionalRootMacAddr]\\\n"
            append cfg_args "     -region_root_path_cost    [stc::get $mstpbridgeportconfig -CistInternalRootPathCost]\\\n"
            append cfg_args "     -remaining_hops    [stc::get $mstpbridgeportconfig -RemainingHops]\\\n"
        }
    }
    if {[info exists vlanblock]&&([regexp -nocase "pvst" $stp_type]) && ([regexp -nocase "trunk" $port_type])} {
        append cfg_args "     -vlan_start    [stc::get $vlanblock -StartVlanList]\\\n"
        append cfg_args "     -vlan_count    [stc::get $vlanblock -NetworkCount]\\\n"
        append cfg_args "     -vlan_priority    [stc::get $vlanblock -Priority]\\\n"
    }
    set ip_version ipv4
    if {[regexp -nocase "ipv6" [stc::get $device -children]]} {
        set ip_version ipv6
    }
    append cfg_args "     -ip_version    $ip_version\\\n"
    append cfg_args "     -encap    [getencap $device]\\\n"
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time

    #handle emulation_mstp_region_config and emulation_msti_config
    if {$stp_type eq "MSTP"} {
        set hltapi_script ""
        set cmd_name emulation_mstp_region_config
        if {[info exists mstpregionconfig]} {
            get_attr $mstpregionconfig $mstpregionconfig
            append hlt_ret_mstp $hlt_ret "mstp"
            set args_list "     -mode    create\\\n"
            append args_list "     -port_handle    $::sth::hlapiGen::port_ret($port)\\\n"
            foreach mstpregionconfig_obj [array names ::sth::hlapiGen::$mstpregionconfig\_obj] {
                append args_list [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $mstpregionconfig $mstpregionconfig $mstpregionconfig_obj]
            }
            append hltapi_script "      set $hlt_ret_mstp \[sth::$cmd_name\\\n"
            append hltapi_script $args_list
            append hltapi_script "\]\n"
            puts_to_file $hltapi_script
            gen_status_info $hlt_ret_mstp "sth::$cmd_name"
        }

        set cmd_name emulation_msti_config
        if {[info exists msticonfigList]} {
            foreach msticonfig $msticonfigList {
                set hltapi_script ""
                set hlt_ret_msti ""
                get_attr $msticonfig $msticonfig
                append hlt_ret_msti $hlt_ret "msti"
                set args_list "     -port_handle    $::sth::hlapiGen::port_ret($port)\\\n"
                foreach msticonfig_obj [array names ::sth::hlapiGen::$msticonfig\_obj] {
                    append args_list [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $msticonfig $msticonfig $msticonfig_obj]
                }
                append hltapi_script "      set $hlt_ret_msti \[sth::$cmd_name\\\n"
                append hltapi_script $args_list
                append hltapi_script "\]\n"
                puts_to_file $hltapi_script
                gen_status_info $hlt_ret_msti "sth::$cmd_name"
            }
        }
    }
}


proc ::sth::hlapiGen::hlapi_gen_device_rfc3918 {rfcobj class mode hlt_ret strblklist} {
    upvar mystrblklist mystrblklist
    #init the rfc table
    variable traffic_ret
    set str_dev ""
    ::sth::sthCore::InitTableFromTCLList $::sth::Rfctest::rfctestTable
    set rfc3918_children [array name sth::hlapiGen::$rfcobj\_obj]
    foreach rfc3918 $rfc3918_children {
        if {![regexp -nocase "testcaseconfig" $rfc3918]} {
            continue
        }
        
        set test_case_type $rfc3918
        #it should have only one kind of test case
        break
    }
    set objs_to_update ""
    #set test_type ""
    switch -regexp [string tolower $test_case_type] {
        rfc3918mixedclassthroughputtestcaseconfig {
            set test_type "mixed_tput"
            set objs_to_update "Rfc3918GroupIterationTestCaseConfig"
        }
        rfc3918aggregatedmulticastthroughputtestcaseconfig {
            set test_type "agg_tput"
            set objs_to_update "Rfc3918GroupIterationTestCaseConfig"
        }
        rfc3918scaledgroupforwardingtestcaseconfig {
            set test_type "matrix"
            set objs_to_update "Rfc3918GroupIterationTestCaseConfig|Rfc3918GroupAndLoadIterationTestCaseConfig"
        }
        rfc3918multicastforwardinglatencytestcaseconfig {
            set test_type "fwd_latency"
            set objs_to_update "Rfc3918GroupIterationTestCaseConfig|Rfc3918GroupAndLoadIterationTestCaseConfig"
        }
        rfc3918joinleavelatencytestcaseconfig {
            set test_type "join_latency"
            set objs_to_update "Rfc3918GroupIterationTestCaseConfig|Rfc3918GroupAndLoadIterationTestCaseConfig"
        }
        rfc3918multicastgroupcapacitytestcaseconfig {
            set test_type "capacity"
            set objs_to_update "Rfc3918GroupAndLoadIterationTestCaseConfig"
        }
    }
    append objs_to_update "|Rfc3918TestCaseConfig"
    set name_space "::sth::Rfctest::"
    set cmd_name "test_rfc3918_config"
    foreach arg [array names $name_space$cmd_name\_stcobj] {
        set stcobj [set $name_space$cmd_name\_stcobj($arg)]
        if {[regexp -nocase $objs_to_update $stcobj]} {
            set $name_space$cmd_name\_stcobj($arg) $test_case_type
        }
    }
    append cfg_args "-test_type         $test_type\\\n"
    #multicast_streamblock
    if {[info exists ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-multicaststreamblockbinding-targets)]} {
        set multicast_streamblock [set ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-multicaststreamblockbinding-targets)]
    } else {
        set rfc3918_gens [set ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-rfc3918generated-targets)]
        set multicast_streamblock ""
        foreach rfc3918_gen $rfc3918_gens {
            if {[regexp -nocase "streamblock" $rfc3918_gen]} {
                set multicast_streamblock [concat $multicast_streamblock $rfc3918_gen]
            }
        }
        
    }
    if {[llength $multicast_streamblock] != 0} {
        
        set str_def ""
        foreach multicast_str $multicast_streamblock {
            set str_var [set traffic_ret($multicast_str)]
            set str_def [concat $str_def "\[keylget $str_var stream_id\]"]
            regsub $multicast_str $mystrblklist "" mystrblklist
        }
        if {[llength $multicast_streamblock] > 1} {
            append str_dev "set mc_str \"$str_def\"\n"
        } else {
            append str_dev "set mc_str $str_def\n"
        }
        
        append cfg_args "-multicast_streamblock           \$mc_str\\\n"
    }
    
    
    set rfc3918_device_list ""
    if {[info exists ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-multicastdstbinding-targets)]} {
        set rfc3918_device_list [concat $rfc3918_device_list [set ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-multicastdstbinding-targets)]]
    }
    if {[info exists ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-multicastsrcbinding-targets)]} {
        set rfc3918_device_list [concat $rfc3918_device_list [set ::sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-multicastsrcbinding-targets)]]
    }
    
    foreach dev_class [array names ::sth::hlapiGen::protocol_to_devices] {
        set devices [set ::sth::hlapiGen::protocol_to_devices($dev_class)]
        foreach rfc3918_device $rfc3918_device_list {
            if {[regexp $rfc3918_device $devices]} {
                regsub $rfc3918_device $devices "" devices
            }
        }
        if {[llength $devices] == 0} {
            unset ::sth::hlapiGen::protocol_to_devices($dev_class)
        } else {
            set ::sth::hlapiGen::protocol_to_devices($dev_class) $devices
        }
    }
    #unicast_streamblock
    #only when the testtype is mixed_tput, the unicast stream can be configured
    if {[regexp "mixed_tput" $test_type]} {
        set testcaseobj [set ::sth::hlapiGen::$rfcobj\_obj([string tolower $test_case_type])]
        set unicast_streamblock [set ::sth::hlapiGen::$rfcobj\_$testcaseobj\_attr(-unicaststreamblockbinding-targets)]
        
        if {[llength $unicast_streamblock] != 0} {
        
            set str_def ""
            foreach unicast_str $unicast_streamblock {
                set str_var [set traffic_ret($unicast_str)]
                set str_def [concat $str_def "\[keylget $str_var stream_id\]"]
                regsub $unicast_str $mystrblklist "" mystrblklist
            }
            if {[llength $multicast_streamblock] > 1} {
                append str_dev "set uc_str \"$str_def\"\n"
            } else {
                append str_dev "set uc_str $str_def\n"
            }
            
            append cfg_args "-unicast_streamblock           \$uc_str\\\n"
        }
        
    }
    #hlapi_gen_device_basic $rfcobj $class create $hlt_ret $cfg_args 1
    set hlapi_script [hlapi_gen_device_basic_without_puts $rfcobj $class create $hlt_ret $cfg_args 1]
    #precess the attr which has the dependency
    set hlapi_script [remove_unuse_attr $hlapi_script $name_space $cmd_name]
    puts_to_file $str_dev
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
}

proc ::sth::hlapiGen::remove_unuse_attr {hlapi_script name_space cmd_name} {
    set lines [split $hlapi_script "\n"]
    set len [llength $lines]
    array set attr_value_arr {}
    array set attr_dependency_arr {}
    set new_lines ""
    for {set i 0} {$i < $len} {incr i} {
	set line [lindex $lines $i]
        set attr [lindex $line 0]
        set value [lindex $line 1]
        if {![regexp "^$" $value]} {
            if {[regexp {\-} $attr]} {
                set attr [regsub {\-} $attr ""]
                #puts "$attr $value"
                set attr_value_arr($attr) $value
            }
        }
    }
    for {set i 0} {$i < $len} {incr i} {
        set line [lindex $lines $i]
        set attr [lindex $line 0]
        set value [lindex $line 1]
        if {[regexp {\-} $attr]} {
            set attr [regsub {\-} $attr ""]
            if {[catch {::sth::sthCore::getswitchprop $name_space $cmd_name $attr dependency} dependency]} { return $dependency}
            if {$attr == "resolution_second" && $value < 1} {
                #will not output the resolution_second, since hltapi only support it to be interger
            } elseif {![string match -nocase $dependency "_none_"]} {
                set dep_attr [lindex $dependency 0]
                set dependent_value [lindex $dependency 1]
                if {[info exists attr_value_arr($dep_attr)]} {
                    set dep_value $attr_value_arr($dep_attr)
                    if {[regexp "^$dependent_value" $dep_value]} {
                        if {[catch {::sth::sthCore::getswitchprop $name_space $cmd_name $dep_attr dependency} dependency1]} { return $dependency1}
                        if {[string match -nocase $dependency1 "_none_"]} {
                            append new_lines "$line\n"
                        } else {
                            set dep_attr1 [lindex $dependency1 0]
                            set dependent_value1 [lindex $dependency1 1]
                            if {[info exists attr_value_arr($dep_attr1)]} {
                                set dep_value1 $attr_value_arr($dep_attr1)
                                if {[regexp "^$dependent_value1" $dep_value1]} {
                                    append new_lines "$line\n"
                                }
                            }
                        }
                        
                    }
                }
                
            } else {
                append new_lines "$line\n"
            }
        } else {
            append new_lines "$line\n"
        }
        
    }
    return $new_lines 
}

proc ::sth::hlapiGen::hlapi_gen_device_rfc {rfcobj class mode hlt_ret strblklist} {

      upvar strblklist mystrblklist
      set rfc_parent [stc::get $rfcobj -parent]
      if {[regexp -- "project" $rfc_parent]} {
         hlapi_gen_device_rfc2544 $rfcobj $class $mode $hlt_ret $mystrblklist
      } else {
         hlapi_gen_device_asymmetric $rfcobj $class $mode $hlt_ret $mystrblklist $rfc_parent
      }

}

proc ::sth::hlapiGen::hlapi_gen_device_asymmetric {rfcobj class mode hlt_ret strblklist rfc_parent} {

    set str_dev ""
    variable traffic_ret
    set profile_config_mode [stc::get $rfcobj -ProfileConfigMode]
    switch -regexp [string tolower $class] {
        rfc2544framelossconfig {
            set test_type fl
        }
        rfc2544latencyconfig {
            set test_type latency
        }
        rfc2544throughputconfig {
            set test_type throughput
        }
    }
    set str_def ""
    ::sth::sthCore::InitTableFromTCLList $::sth::Rfctest::rfctestTable
    set cmd_name "rfc2544_asymmetric_config"
    set name_space "::sth::Rfctest::"
    append cfg_args "-test_type           $test_type\\\n"
    set portgroups [stc::get project1 -children-PortGroup]
    foreach portgroup $portgroups {
         set portgroup_name [stc::get $portgroup -GroupName]
         set portvalue [stc::get $portgroup -MemberOfGroup]
         if {$portgroup_name eq "Downstream"} {
           set port_hdl $::sth::hlapiGen::port_ret($portvalue)
           append cfg_args "-downstream_port           $port_hdl\\\n"
         } else {
           set port_hdl $::sth::hlapiGen::port_ret($portvalue)
           append cfg_args "-upstream_port           $port_hdl\\\n"
          }

    }
    set accessConcGen [stc::get project1 -children-AccessConcentratorGenParams]
    if {$accessConcGen ne ""} {
       set traffic_config_mode [stc::get $accessConcGen -TrafficConfigMode]
    } else {
         set traffic_config_mode ""
    }
    if {$traffic_config_mode eq "MANUAL" } {
       set ports [stc::get project1 -children-Port]
       foreach port $ports {
       lappend streamblock_list [stc::get $port -children-StreamBlock]
      
       }
      foreach streamblock $streamblock_list {
          if {[info exists traffic_ret($streamblock)]} {
            set str_var [set traffic_ret($streamblock)]
            set str_def [concat $str_def "\[keylget $str_var stream_id\]"]
        }
      
      
      }
      append str_dev "set streamblock_handle \"$str_def\" \n"
      append cfg_args "-streamblock_handle           \$streamblock_handle \\\n"
      }
    if {$traffic_config_mode eq "AUTO" } {
        set Stc_AccessConcGenList "TrafficConfigMode TrafficDevices TrafficFlow TrafficConnectivity DownstreamTrafficIpTos DownstreamTrafficVlanPriority UpstreamTrafficIpTos UpstreamTrafficVlanPriority IpNextProtocolId Ttl"
        set hlapi_AccessConcGenList "traffic_config_mode traffic_devices traffic_flow traffic_connectivity downstream_traffic_ip_tos downstream_traffic_vlan_priority upstream_traffic_ip_tos upstream_traffic_vlan_priority ip_next_protocol_id ttl"    
        foreach stcvalue $Stc_AccessConcGenList hlapiValue $hlapi_AccessConcGenList {
            set value [stc::get $rfc_parent -$stcvalue]
            if {$value ne ""} {
               append cfg_args "-$hlapiValue          [string tolower $value]\\\n"
            }
        }
     }
      
   set learning_mode [set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-learningmode)]
    if {[regexp -nocase "L2_LEARNING" $learning_mode]} {
        set $name_space$cmd_name\_stcattr(l3_learning_retry_count) "_none_"
        set $name_space$cmd_name\_stcattr(enable_cyclic_resolution) "_none_"
        set $name_space$cmd_name\_stcattr(l3_rate) "_none_"
        set $name_space$cmd_name\_stcattr(l3_delay_before_learning) "_none_"
    } else {
        set $name_space$cmd_name\_stcattr(learning_rate) "_none_"
        set $name_space$cmd_name\_stcattr(l2_learning_repeat_count) "_none_"
        set $name_space$cmd_name\_stcattr(l2_delay_before_learning) "_none_"
    }
    set duration_mode [set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-durationmode)]
    if {[regexp -nocase "BURSTS" $duration_mode]} {
       set $name_space$cmd_name\_stcattr(test_duration) "_none_"
    } else {
        set $name_space$cmd_name\_stcattr(duration_burst) "_none_"
    
     }

    foreach arg [array names $name_space$cmd_name\_stcobj] {
        set stcobj [set $name_space$cmd_name\_stcobj($arg)]
        if {[regexp -nocase "Rfc2544Config" $stcobj] || [regexp -nocase "TrafficDescriptor" $stcobj] || [regexp -nocase "AccessConcentratorGenParam" $stcobj]} {
            set $name_space$cmd_name\_stcobj($arg) $class
        }
        
        if {$arg == "accept_frame_loss" && $test_type == "throughput"} {
            set $name_space$cmd_name\_stcobj($arg) $class
            set $name_space$cmd_name\_stcattr($arg) "AcceptableFrameLoss"
        }
        if {$arg == "frame_size_imix"} {
            set attr [string tolower [set $name_space$cmd_name\_stcattr($arg)]]
            set imix_list [set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-$attr)]
            set value ""
			set imix_name ""
            foreach imix $imix_list {
                #change "JMIX Upstream and JMIX Downstream" to "jmix_upstream and jmix_downstream"
                set imix_name [stc::get $imix -name]
                if {$imix_name == "JMIX Upstream"} {
                    lappend value "jmix_upstream"
                } elseif {$imix_name == "JMIX Downstream"} {
                    lappend value "jmix_downstream"
                } else {
                    lappend value $imix_name
                }
            }
            puts $value
            set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-$attr) $value
        }
    }
    
    set hlapi_script [hlapi_gen_device_basic_without_puts $rfcobj $class create $hlt_ret $cfg_args 1]
    set hlapi_script [remove_unuse_attr $hlapi_script $name_space $cmd_name]
    puts_to_file $str_dev
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    unset $name_space$cmd_name\_Initialized
    array unset $name_space$cmd_name\_stcobj
    
       hlapi_gen_device_asymm_profile $rfcobj $hlt_ret $test_type
    
}


proc ::sth::hlapiGen::hlapi_gen_device_asymm_profile {rfcobj hlt_ret test_type} {

    
     
     if {[regexp -- "rfc2544throughput" $rfcobj]} {
        set class rfc2544throughputprofile
        set profileObj [stc::get $rfcobj -children-Rfc2544ThroughputProfile]
     }
     if {[regexp -- "rfc2544frameloss" $rfcobj]} {
        set class rfc2544framelossprofile
        set profileObj [stc::get $rfcobj -children-Rfc2544FrameLossProfile]
     }
     if {[regexp -- "rfc2544latency" $rfcobj]} {
        set class rfc2544latencyprofile
        set profileObj [stc::get $rfcobj -children-Rfc2544LatencyProfile]
     }
     set profile_config_mode [stc::get $rfcobj -ProfileConfigMode]
     set name_space "::sth::Rfctest::"
     set cmd_name rfc2544_asymmetric_profile
     set i 0
     foreach profile $profileObj {
         if {$profile_config_mode ne "MANUAL"} {
            puts_to_file "set profileHandle_$i \[lindex \[keylget $hlt_ret profile_handles\] $i\] \n"
            append cfg_args "-profile_handle                      \$profileHandle_$i \\\n"
         } else {
            append cfg_args "-test_handle           $rfcobj\\\n"
           }
         set streamblock [stc::get $profile -StreamBlockBinding-targets]
         append cfg_args "-streamblock_handle           $streamblock\\\n"
         set Profile_name [stc::get $profile -Name]
         set prof_name [regsub -all -nocase {\[} $Profile_name "\\\["]
         set prof_name [regsub -all -nocase {\]} $prof_name "\\\]"]
         append cfg_args "-profile_name                 \"$prof_name\"\\\n"
         set Load_spec_mode [stc::get $profile -LoadSpecMode]
         append cfg_args "-load_spec_mode                 [string tolower $Load_spec_mode]\\\n"
         set Load_units [stc::get $profile -LoadUnits]
         append cfg_args "-load_units                 [string tolower $Load_units]\\\n"

         
         if {[regexp -nocase "throughput" $profile]} {
             set acceptable_frame_loss [stc::get $profile -AcceptableFrameLoss]
             append cfg_args "-acceptable_frame_loss                 $acceptable_frame_loss\\\n"
             set back_off [stc::get $profile -BackOff]
             append cfg_args "-back_off                 $back_off\\\n"
             set enable_latency_threshold [stc::get $profile -EnableMaxLatencyThreshold]
             if {$enable_latency_threshold eq "true" } {
                set enable_latency_threshold 1
             } else {
                 set enable_latency_threshold 0
               } 
             append cfg_args "-enable_latency_threshold                 $enable_latency_threshold\\\n"
             set enable_seq_threshold [stc::get $profile -EnableOutofSeqThreshold]
             if {$enable_seq_threshold eq "true" } {
                set enable_seq_threshold 1
             } else {
                 set enable_seq_threshold 0
               } 
             append cfg_args "-enable_seq_threshold                 $enable_seq_threshold\\\n"
             set ignore_limit [stc::get $profile -IgnoreMinMaxLimits]
             if {$ignore_limit eq "true" } {
                set ignore_limit 1
             } else {
                 set ignore_limit 0
               }
             append cfg_args "-ignore_limit                 $ignore_limit\\\n"
             set max_latency_threshold [stc::get $profile -MaxLatencyThreshold]
             append cfg_args "-max_latency_threshold                 $max_latency_threshold\\\n"
             set out_of_seq_threshold [stc::get $profile -OutOfSeqThreshold]
             append cfg_args "-out_of_seq_threshold                 $out_of_seq_threshold\\\n"
             set initial_rate [stc::get $profile -RateInitial]
             append cfg_args "-initial_rate                 $initial_rate\\\n"
             set rate_lower_limit [stc::get $profile -RateLowerLimit]
             append cfg_args "-rate_lower_limit                 $rate_lower_limit\\\n"
             set rate_upper_limit [stc::get $profile -RateUpperLimit]
             append cfg_args "-rate_upper_limit                 $rate_upper_limit\\\n"
             set rate_step [stc::get $profile -RateStep]
             append cfg_args "-rate_step                 $rate_step\\\n"
             set resolution [stc::get $profile -Resolution]
             append cfg_args "-resolution                 $resolution\\\n"
             set search_mode [stc::get $profile -SearchMode]
             append cfg_args "-search_mode                 [string tolower $search_mode]\\\n"

         } else {
                 set Load_type [stc::get $rfcobj -LoadType]
                 set profileRateobject [stc::get $profile -children-Rfc2544ProfileRate]
                 set profile_rate_mode [stc::get $profile -ProfileRateMode]
                 append cfg_args "-profile_rate_mode                 [string tolower $profile_rate_mode]\\\n"
                 foreach profilerate $profileRateobject {
                      set frame_size_list [stc::get $profilerate -FrameSize]
                      lappend FrameSizelist "$frame_size_list"
                      set custom_load_list [stc::get $profilerate -CustomLoadList]
                      lappend customlist "$custom_load_list"
                      set random_max_load [stc::get $profilerate -RandomMaxLoad]
                      lappend MaxRandomList "$random_max_load"
                      set random_min_load [stc::get $profilerate -RandomMinLoad]
                      lappend MinxRandomList "$random_min_load"
                      set load_start [stc::get $profilerate -LoadStart]
                      lappend StartLoad "$load_start"
                      set load_end [stc::get $profilerate -LoadEnd]
                      lappend endLoad "$load_end"
                      set load_step [stc::get $profilerate -LoadStep]
                      lappend StepLoad "$load_end"
                 }
                     switch -- $Load_type {
                         RANDOM {
                         if {$profile_rate_mode ne "PER_TEST"} {
                             append cfg_args "-frame_size                 \{$FrameSizelist\}\\\n"
                             
                         }
                         append cfg_args "-random_max_load                \{$MaxRandomList\}\\\n"
                         append cfg_args "-random_min_load                \{$MinxRandomList\}\\\n"
                         set MaxRandomList ""
                         set MinxRandomList ""
                         set FrameSizelist ""
                         }
                         STEP {
                         if {$profile_rate_mode ne "PER_TEST"} {
                             append cfg_args "-frame_size                 \{$FrameSizelist\}\\\n"
                             
                         }
                         append cfg_args "-load_start                      \{$StartLoad\}\\\n"
                         append cfg_args "-load_end                        \{$endLoad\}\\\n"
                         append cfg_args "-load_step                 \{$StepLoad\}\\\n"
                         set StartLoad ""
                         set endLoad ""
                         set StepLoad ""
                         set FrameSizelist ""
                         }
                        CUSTOM {
                        if {$profile_rate_mode ne "PER_TEST"} {
                            append cfg_args "-frame_size                 \{$FrameSizelist\}\\\n"
                            
                        }
                        append cfg_args "-custom_load_list                 \{$customlist\}\\\n"
                        set customlist ""
                        set FrameSizelist ""
                        }
                         
                    }

         }
             set j 0
             set hlt_ret_prof $hlt_ret\_profile$i
             incr i
             if {$profile_config_mode eq "MANUAL"} {
             set hlapi_script [hlapi_gen_device_basic_without_puts $class $class create $hlt_ret_prof $cfg_args 1]
         } else {
             set hlapi_script [hlapi_gen_device_basic_without_puts $class $class modify $hlt_ret_prof $cfg_args 1]
           }
         puts_to_file $hlapi_script
         #set hlapi_script [remove_unuse_attr $hlapi_script $name_space $cmd_name]
         gen_status_info $hlt_ret "sth::$cmd_name" 
         set cfg_args ""
    }
}



proc ::sth::hlapiGen::hlapi_gen_device_rfc2544 {rfcobj class mode hlt_ret strblklist} {
    upvar mystrblklist mystrblklist
    variable traffic_ret
    set str_dev ""
    switch -regexp [string tolower $class] {
        rfc2544backtobackframesconfig {
            set test_type b2b
            
        }
        rfc2544framelossconfig {
            set test_type fl
        }
        rfc2544latencyconfig {
            set test_type latency
        }
        rfc2544throughputconfig {
            set test_type throughput
        }
    }
    #set traffic_des_group [set sth::hlapiGen::$rfcobj\_$rfcobj_attr(-trafficdescriptorgroupbinding-targets)]    
    set traffic_des_group_list [stc::get project1 -children-TrafficDescriptorGroup]
    set traffic_des_list ""    
    foreach traffic_des_group $traffic_des_group_list {
        foreach traffic_desc [stc::get $traffic_des_group -children-TrafficDescriptor] {
            lappend traffic_des_list $traffic_desc
        }        
    }
    foreach traffic_des $traffic_des_list {
        get_attr $traffic_des $traffic_des
    }
    
    set str_def ""
    #get all the rfc2544 related streamblocks streamblock_handle
    set sequencer [stc::get system1 -children-sequencer]
    switch -- $test_type {
        b2b {
            set rfc2544_cmd_group_type "rfc2544backtobackframessequencergroupcommand"
            set rfc2544_cmd_type "Rfc2544BackToBackFramesCommand"
            set rfc2544_config_type "Rfc2544BackToBackFramesConfig"
        }
        fl {
            set rfc2544_cmd_group_type "rfc2544framelosssequencergroupcommand"
            set rfc2544_cmd_type "Rfc2544FrameLossCommand"
            set rfc2544_config_type "Rfc2544FrameLossConfig"
        }
        latency {
            set rfc2544_cmd_group_type "rfc2544latencysequencergroupcommand"
            set rfc2544_cmd_type "Rfc2544LatencyCommand"
            set rfc2544_config_type "Rfc2544LatencyConfig"
        }
        throughput {
            set rfc2544_cmd_group_type "rfc2544throughputsequencergroupcommand"
            set rfc2544_cmd_type "Rfc2544ThroughputCommand"
            set rfc2544_config_type "Rfc2544ThroughputConfig"
        }
        default {
            return
        }
    }
    set rfc2544_cmd_group [stc::get $sequencer -children-$rfc2544_cmd_group_type]
    if {$rfc2544_cmd_group == ""} {
        set rfc2544_cmd [stc::get $sequencer -children-$rfc2544_cmd_type]
    } else {
        set rfc2544_cmd [stc::get $rfc2544_cmd_group -children-$rfc2544_cmd_type]
    }
    if {$rfc2544_cmd == ""} {
        unset ::sth::hlapiGen::protocol_to_devices($class)
        return
    } else {
        set rfc2544_config [stc::get $rfc2544_cmd -children-$rfc2544_config_type]    
    }
    set streamblock_profile [stc::get $rfc2544_config -children-Rfc2544StreamBlockProfile]
    set strblks [stc::get $streamblock_profile -StreamBlockList]
    
    foreach strblk $strblks {
        if {[info exists traffic_ret($strblk)]} {
            set str_var [set traffic_ret($strblk)]
            set str_def [concat $str_def "\[keylget $str_var stream_id\]"]
        }
        regsub $strblk $mystrblklist "" mystrblklist
    }
    
    #1. if the streamblock need to be created in rfc2544, if need then the trafficdescriptor need to be configured
    #   case1. if the streamblock is bound stream and the src and dst deivce can't be created out of rfc2544, such as raw device.
    #   case2. if the src and the dst of the streamblock is port not device, it will be created in the rfc2544
    #2. if the streamblock will be created before the rfc2544.
    #   case1: if the streamblock is raw stream, it will be created outof rfc2544
    #   case2: if the streamblock is bound stream and the src and dst device and the stream can be created out of the rfc2544
    
    set sth::hlapiGen::$traffic_des\_$traffic_des\_attr(-endpointcreation) "CREATE_NEW_ENDPOINTS"

    #remove the streamblock which can be created with the birdireaction in the other stream.
    set src_dst_list ""
    set src_ips ""
    set dst_ips ""
    foreach streamblock $strblks {
        set src_dst ""
        set dst_src ""
        set stream_port [stc::get $streamblock -parent]
        if {[info exists sth::hlapiGen::$stream_port\_$streamblock\_attr(-srcbinding-targets)] && [info exists sth::hlapiGen::$stream_port\_$streamblock\_attr(-dstbinding-targets)]} {
            set src_ip [set sth::hlapiGen::$stream_port\_$streamblock\_attr(-srcbinding-targets)]
            set dst_ip [set sth::hlapiGen::$stream_port\_$streamblock\_attr(-dstbinding-targets)]
            append src_dst $src_ip $dst_ip
            append dst_src $dst_ip $src_ip
            if {[lsearch $src_dst_list $dst_src] == -1} {
                set src_dst_list [concat $src_dst_list $src_dst]
                set src_ips [concat $src_ips $src_ip]
                set dst_ips [concat $dst_ips $dst_ip]
            }
        }
    }
    set endpoint_creation 1
    if {$src_ips == ""} {
        #raw stream
        set endpoint_creation 0
        set sth::hlapiGen::$traffic_des\_$traffic_des\_attr(-endpointcreation) "USE_EXISTING_ENDPOINTS"
        set src_ports ""
        set dst_ports ""
        set all_ports [stc::get project1 -children-port]
        foreach streamblock $strblks {
            set port [stc::get $streamblock -parent]
            if {[lsearch $src_ports [set sth::hlapiGen::port_ret($port)]] == -1} {
                set src_ports [concat $src_ports [set sth::hlapiGen::port_ret($port)]]
            }
        }
        foreach port $all_ports {
            if {[lsearch $src_ports [set sth::hlapiGen::port_ret($port)]] == -1} {
                set dst_ports [concat $dst_ports [set sth::hlapiGen::port_ret($port)]]
            }
        }
        append cfg_args "-src_port           \"$src_ports\" \\\n"
        append cfg_args "-dst_port           \"$dst_ports\" \\\n"
        
    } elseif {[regexp -nocase "port" $src_ips] && [regexp -nocase "port" $dst_ips]} {
        set src_port_list $src_bind
        set dst_port_list $dst_bind
        set src_ports ""
        set dst_ports ""
        foreach src_port $src_port_list {
            set src_port [set sth::hlapiGen::port_ret($src_port)]
            set src_ports [concat $src_ports $src_port]
        }
        
        foreach dst_port $dst_port_list {
            set dst_port [set sth::hlapiGen::port_ret($dst_port)]
            set dst_ports [concat $dst_ports $dst_port]
        }
        append cfg_args "-src_port           \"$src_ports\" \\\n"
        append cfg_args "-dst_port           \"$dst_ports\" \\\n"
    } else {
        set src_endpoint [stc::get [lindex $src_ips 0] -parent]
        set dst_endpoint [stc::get [lindex $dst_ips 0] -parent]
        #if the device has been created then the streamblock should also have already been created,
        #no need to output the src_endpoints and the dst_endpoints only the streamblock is ok.
        if {![info exists sth::hlapiGen::device_ret($src_endpoint)]} {
            
            set src_ports ""
            foreach src_ip $src_ips {
                set src_endpoint [stc::get $src_ip -parent]
                set src_port [set sth::hlapiGen::$src_endpoint\_$src_endpoint\_attr(-affiliationport-targets)]
                set src_port [set sth::hlapiGen::port_ret($src_port)]
                if {[lsearch $src_ports $src_port] == -1} {
                    set src_ports [concat $src_ports $src_port]
                }
            }
            append cfg_args "-src_port        \"$src_ports\" \\\n"
        }  else {
            set endpoint_creation 0
            set src_endpoints ""
            foreach src_ip $src_ips {
                set src_endpoints [concat $src_endpoints [stc::get $src_ip -parent]]
            }
            foreach dev_class [array names ::sth::hlapiGen::protocol_to_devices] {
                set devices [set ::sth::hlapiGen::protocol_to_devices($dev_class)]
                foreach src_endpoint $src_endpoints {
                    if {[regexp $src_endpoint $devices]} {
                        regsub $src_endpoint $devices "" devices
                    }
                }
                if {[llength $devices] == 0} {
                    unset ::sth::hlapiGen::protocol_to_devices($dev_class)
                } else {
                    set ::sth::hlapiGen::protocol_to_devices($dev_class) $devices
                }
            }
        }
        if {![info exists sth::hlapiGen::device_ret($dst_endpoint)]} {
            set dst_ports ""
            foreach dst_ip $dst_ips {
                set dst_endpoint [stc::get $dst_ip -parent]
                set dst_port [set sth::hlapiGen::$dst_endpoint\_$dst_endpoint\_attr(-affiliationport-targets)]
                set dst_port [set sth::hlapiGen::port_ret($dst_port)]
                if {[lsearch $dst_ports $dst_port] == -1} {
                    set dst_ports [concat $dst_ports $dst_port]
                }
            }
            append cfg_args "-dst_port        \"$dst_ports\" \\\n"
        } else {
            set endpoint_creation 0
            set dst_endpoints ""
            foreach dst_ip $dst_ips {
                set dst_endpoints [concat $dst_endpoints [stc::get $dst_ip -parent]]
            }
            foreach dev_class [array names ::sth::hlapiGen::protocol_to_devices] {
                set devices [set ::sth::hlapiGen::protocol_to_devices($dev_class)]
                foreach dst_endpoint $dst_endpoints {
                    if {[regexp $dst_endpoint $devices]} {
                        regsub $dst_endpoint $devices "" devices
                    }
                }
                if {[llength $devices] == 0} {
                    unset ::sth::hlapiGen::protocol_to_devices($dev_class)
                } else {
                    set ::sth::hlapiGen::protocol_to_devices($dev_class) $devices
                }
            }
        }
    }
    ::sth::sthCore::InitTableFromTCLList $::sth::Rfctest::rfctestTable
    set name_space "::sth::Rfctest::"
    set cmd_name "test_rfc2544_config"
    append cfg_args "-test_type         $test_type \\\n"
    #TrafficDescriptor
    if {$endpoint_creation == 0} {
        if {[llength $strblks] > 1} {
            append str_dev "set streamblock_handle \"$str_def\" \n"
        } else {
            append str_dev "set streamblock_handle $str_def \n"
        }
        append cfg_args "-streamblock_handle           \$streamblock_handle \\\n"
        append cfg_args "-endpoint_creation             $endpoint_creation \\\n"
    } else {
        append cfg_args "-endpoint_creation $endpoint_creation \\\n"
    }
    #when there is only raw stream will not configure the parameters under the trafficdescriptor
    if {$endpoint_creation == 1} {
        #get the ip address for the raw device.
        set src_ip [lindex $src_ips 0]
        set src_dev [stc::get $src_ip -parent]
        foreach trf_des_arg "traffic_pattern endpoint_map bidirectional enable_stream_only_gen device_count QoS" {
            set stc_attr [string tolower [set $name_space$cmd_name\_stcattr($trf_des_arg)]]
            set trf_des_value [set sth::hlapiGen::$traffic_des\_$traffic_des\_attr(-$stc_attr)]
            if {$trf_des_value == ""} {
                continue
            }
            if {$trf_des_value == true} {
                set trf_des_value 1
            } elseif {$trf_des_value == false} {
                set trf_des_value 0
            } else {
                set trf_des_value [string tolower $trf_des_value ]
            }
            append cfg_args "-$trf_des_arg      $trf_des_value \\\n"
        }
        
        set version v4
        if {[regexp "v6" $src_ip]} {
            set version v6
        }
        #get the ip address for the raw device.
        set src_ip [lindex $src_ips 0]
        set src_dev [stc::get $src_ip -parent]
        #ipv4_addr ipv4_prefix_len ipv4_gateway
        #ipv6_addr ipv6_prefix_len ipv6_gateway
        #the src can be ipv4 ipv6, etheriif or vlan. not only ip.
        if {[info exists sth::hlapiGen::$src_dev\_obj(ip$version\if)]} {
            set ipif [set sth::hlapiGen::$src_dev\_obj(ip$version\if)]
            set ip$version\_addr [set sth::hlapiGen::$src_dev\_$ipif\_attr(-address)]
            set ip$version\_prefix_len [set sth::hlapiGen::$src_dev\_$ipif\_attr(-prefixlength)]
            set ip$version\_gateway [set sth::hlapiGen::$src_dev\_$ipif\_attr(-gateway)]
        
            foreach ip_arg "ip$version\_addr ip$version\_prefix_len ip$version\_gateway" {
                append cfg_args "-$ip_arg       [set $ip_arg] \\\n"
            }
        }
        
        if {[info exists sth::hlapiGen::$src_dev\_obj(vlanif)]} {
            set vlanif [lindex [set sth::hlapiGen::$src_dev\_obj(vlanif)] 0]
            #vlan vlan_priority
            set vlan [set sth::hlapiGen::$src_dev\_$vlanif\_attr(-vlanid)]
            set vlan_priority [set sth::hlapiGen::$src_dev\_$vlanif\_attr(-priority)]
            foreach vlan_arg "vlan vlan_priority" {
                append cfg_args "-$vlan_arg       [set $vlan_arg] \\\n"
            }
        }
        if {[info exists sth::hlapiGen::$src_dev\_obj(ethiiif)]} {
            set ethiiif [set sth::hlapiGen::$src_dev\_obj(ethiiif)]
            #mac_addr
            set mac_addr [set sth::hlapiGen::$src_dev\_$ethiiif\_attr(-sourcemac)]
            append cfg_args "-mac_addr      $mac_addr \\\n"
        }
        set dst_ip [lindex $dst_ips 0]
        set dst_dev [stc::get $dst_ip -parent]
        #port_ipv4_addr_step port_ipv4_gateway_step port_vlan_step port_ipv6_addr_step port_ipv6_gateway_step
        if {[info exists sth::hlapiGen::$src_dev\_obj(ip$version\if)] && [info exists sth::hlapiGen::$dst_dev\_obj(ip$version\if)] && [regexp $version $dst_ip]} {
            set ipif [set sth::hlapiGen::$dst_dev\_obj(ip$version\if)]
            set next_port_ip_addr [set sth::hlapiGen::$dst_dev\_$ipif\_attr(-address)]
            set next_port_ip_gateway [set sth::hlapiGen::$dst_dev\_$ipif\_attr(-gateway)]
            set port_ip$version\_addr_step [calculate_difference [set ip$version\_addr] $next_port_ip_addr ip$version]
            set port_ip$version\_gateway_step [calculate_difference [set ip$version\_gateway] $next_port_ip_gateway ip$version]
            foreach port_step_arg "port_ip$version\_addr_step port_ip$version\_gateway_step" {
                append cfg_args "-$port_step_arg       [set $port_step_arg] \\\n"
            }
        }
        if {[info exists sth::hlapiGen::$src_dev\_obj(vlanif)] && [info exists sth::hlapiGen::$dst_dev\_obj(vlanif)]} {
            set vlanif [set sth::hlapiGen::$dst_dev\_obj(vlanif)]
            set next_port_vlan [set sth::hlapiGen::$dst_dev\_$vlanif\_attr(-vlanid)]
            set port_vlan_step [expr $next_port_vlan - $vlan]
            append cfg_args "-port_vlan_step        $port_vlan_step \\\n"
        }
        if {[info exists sth::hlapiGen::$src_dev\_obj(ethiiif)] && [info exists sth::hlapiGen::$dst_dev\_obj(ethiiif)]} {
            set ethiiif1 [set sth::hlapiGen::$src_dev\_obj(ethiiif)]
            set ethiiif2 [set sth::hlapiGen::$dst_dev\_obj(ethiiif)]
            set mac_addr1 [set sth::hlapiGen::$src_dev\_$ethiiif1\_attr(-sourcemac)]
            set mac_addr2 [set sth::hlapiGen::$dst_dev\_$ethiiif2\_attr(-sourcemac)]
            set port_mac_step [calculate_difference $mac_addr1 $mac_addr2 mac]
            append cfg_args "-port_mac_step      $port_mac_step \\\n"
        }
        set device_count [set sth::hlapiGen::$dst_dev\_$dst_dev\_attr(-devicecount)]
        if {$device_count == 1} {
            #"device_ipv4_addr_step device_vlan_step device_ipv6_addr_step"
            if {[llength $src_ips]>1} {
                set ipif0 [lindex $src_ips 0]
                set ipif1 [lindex $src_ips 1]
                set dev0 [stc::get $ipif0 -parent]
                set dev1 [stc::get $ipif1 -parent] 
            } elseif {[llength $dst_ips]>1} {
                set ipif0 [lindex $dst_ips 0]
                set ipif1 [lindex $dst_ips 1]
                set dev0 [stc::get $ipif0 -parent]
                set dev1 [stc::get $ipif1 -parent] 
            }
            if {[llength $src_ips]>1 || [llength $dst_ips]>1} {
                if {[info exists sth::hlapiGen::$dev0\_obj(ip$version\if)] && [info exists sth::hlapiGen::$dev1\_obj(ip$version\if)]} {
                    set ipif0 [set sth::hlapiGen::$dev0\_obj(ip$version\if)]
                    set ipif1 [set sth::hlapiGen::$dev1\_obj(ip$version\if)]
                    set ip_addr [set sth::hlapiGen::$dev0\_$ipif0\_attr(-address)]
                    set next_ip_addr [set sth::hlapiGen::$dev1\_$ipif1\_attr(-address)]
                    set device_ip$version\_addr_step [calculate_difference $ip_addr $next_ip_addr ip$version]
                    append cfg_args "-device_ip$version\_addr_step [set device_ip$version\_addr_step] \\\n"
                }
                
                if {[info exists sth::hlapiGen::$dev0\_obj(vlanif)] && [info exists sth::hlapiGen::$dev1\_obj(vlanif)]} {
                    set vlanif0 [set sth::hlapiGen::$dev0\_obj(vlanif)]
                    set vlanif1 [set sth::hlapiGen::$dev1\_obj(vlanif)]
                    set vlanid [set sth::hlapiGen::$dev0\_$vlanif0\_attr(-vlanid)]
                    set next_vlanid [set sth::hlapiGen::$dev1\_$vlanif1\_attr(-vlanid)]
                    set device_vlan_step [expr $next_vlanid - $vlanid]
                    append cfg_args "-device_vlan_step      $device_vlan_step \\\n"
                }
                # port_mac_step, device_mac_step
                if {[info exists sth::hlapiGen::$dev0\_obj(ethiiif)] && [info exists sth::hlapiGen::$dev1\_obj(ethiiif)]} {
                    set ethiiif1 [set sth::hlapiGen::$dev0\_obj(ethiiif)]
                    set ethiiif2 [set sth::hlapiGen::$dev1\_obj(ethiiif)]
                    set mac_addr1 [set sth::hlapiGen::$dev0\_$ethiiif1\_attr(-sourcemac)]
                    set mac_addr2 [set sth::hlapiGen::$dev1\_$ethiiif2\_attr(-sourcemac)]
                    set device_mac_step [calculate_difference $mac_addr1 $mac_addr2 mac]
                    append cfg_args "-device_mac_step      $device_mac_step \\\n"
                }
            }
        } else {
            #device_ipv4_addr_step device_vlan_step device_ipv6_addr_step device_mac_step
            if {[info exists sth::hlapiGen::$src_dev\_obj(ip$version\if)]} {
                set ipif [set sth::hlapiGen::$src_dev\_obj(ip$version\if)]
                set device_ip$version\_addr_step [set sth::hlapiGen::$src_dev\_$ipif\_attr(-addrstep)]
                set device_ip$version\_gateway_step [set sth::hlapiGen::$src_dev\_$ipif\_attr(-gatewaystep)]
            }
            
            if {[info exists sth::hlapiGen::$src_dev\_obj(vlanif)]} {
                set vlanif [set sth::hlapiGen::$src_dev\_obj(vlanif)]
                set device_vlan_step [set sth::hlapiGen::$src_dev\_$vlanif\_attr(-idstep)]
            }
            
            if {[info exists sth::hlapiGen::$src_dev\_obj(ethiiif)]} {
                set ethiiif [set sth::hlapiGen::$src_dev\_obj(ethiiif)]
                set device_mac_step [set sth::hlapiGen::$src_dev\_$ethiiif\_attr(-srcmacstep)]
            }
            foreach device_arg "device_ip$version\_addr_step device_vlan_step device_mac_step" {
                if {[info exists $device_arg]} {
                    append cfg_args "-$device_arg       [set $device_arg] \\\n"
                    unset $device_arg
                }
                
            }
        }
    }

    #when learning_mode is l2, l3_learning_retry_count(L3RetryCount) and enable_cyclic_resolution(L3EnableCyclicAddrResolution) should not be output.
    #when learning_mode is l3 learning_rate(L2LearningFrameRate) and l2_learning_repeat_count(L2LearningRepeatCount) should not be output
    #LearningMode:L2_LEARNING L3_LEARNING
     set learning_mode [set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-learningmode)]
     if {[regexp -nocase "L2_LEARNING" $learning_mode]} {
         set $name_space$cmd_name\_stcattr(l3_learning_retry_count) "_none_"
         set $name_space$cmd_name\_stcattr(enable_cyclic_resolution) "_none_"
     } else {
         set $name_space$cmd_name\_stcattr(learning_rate) "_none_"
         set $name_space$cmd_name\_stcattr(l2_learning_repeat_count) "_none_"
     }
    #Rfc2544Config
    foreach arg [array names $name_space$cmd_name\_stcobj] {
        set stcobj [set $name_space$cmd_name\_stcobj($arg)]
        if {[regexp -nocase "Rfc2544Config" $stcobj]} {
            set $name_space$cmd_name\_stcobj($arg) $class
        }
        if {$arg == "accept_frame_loss" && $test_type == "throughput"} {
            set $name_space$cmd_name\_stcobj($arg) $class
            set $name_space$cmd_name\_stcattr($arg) "AcceptableFrameLoss"
        }
        if {$arg == "frame_size_imix"} {
            set attr [string tolower [set $name_space$cmd_name\_stcattr($arg)]]
            set imix_list [set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-$attr)]
            set value ""
			set imix_name ""
            foreach imix $imix_list {
                #change "JMIX Upstream and JMIX Downstream" to "jmix_upstream and jmix_downstream"
                set imix_name [stc::get $imix -name]
                if {$imix_name == "JMIX Upstream"} {
                    lappend value "jmix_upstream"
                } elseif {$imix_name == "JMIX Downstream"} {
                    lappend value "jmix_downstream"
                } else {
                    lappend value $imix_name
                }
            }
            puts $value
            set sth::hlapiGen::$rfcobj\_$rfcobj\_attr(-$attr) $value
        }
    }
    if {[info exists sth::hlapiGen::$rfcobj\_obj(rfc5180config)]} {
        append cfg_args "-rfc5180_enable       true \\\n"
        set rfc5180config [set sth::hlapiGen::$rfcobj\_obj(rfc5180config)]
        if {[info exists sth::hlapiGen::$rfcobj\_$rfc5180config\_attr(-coexistingstreamblockbinding-targets)]} {
            set coStrList [set sth::hlapiGen::$rfcobj\_$rfc5180config\_attr(-coexistingstreamblockbinding-targets)]
            set coStr_def ""
            foreach strblk $coStrList {
                if {[info exists traffic_ret($strblk)]} {
                    set str_var [set traffic_ret($strblk)]
                    set coStr_def [concat $coStr_def "\[keylget $str_var stream_id\]"]
                }

            }
            append str_dev "set co_streamblock_handle \"$coStr_def\" \n"
            set sth::hlapiGen::$rfcobj\_$rfc5180config\_attr(-coexistingstreamblockbinding-targets) "\$co_streamblock_handle"

        }
    }
    set hlapi_script [hlapi_gen_device_basic_without_puts $rfcobj $class create $hlt_ret $cfg_args 1]
    #precess the attr which has the dependency
    set hlapi_script [remove_unuse_attr $hlapi_script $name_space $cmd_name]
    puts_to_file $str_dev
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name" 

}


proc ::sth::hlapiGen::hlapi_gen_device_stak {device class mode hlt_ret cfg_args first_time} {
    if {[catch {
        set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
        #::sth::sthCore::InitTableFromTCLList $::sth::pimTable
        ::sth::sthCore::InitTableFromTCLList [set $table_name]
        
        set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
        if {$first_time == 1} {
            #need to call the emulation_device_config
            hlapi_gen_device_deviceconfig $device "emulateddevice" "create" $hlt_ret "" $first_time
            set hlt_ret $hlt_ret\_cfg
        }
        set dev_def [get_device_created $device emulated_device handle]
        puts_to_file $dev_def
        set dev_ret [lindex [set sth::hlapiGen::device_ret($device)] 0]
        set type $::sth::hlapiGen::output_type
        set ret1 [stc::perform spirent.xtapi.SaveAsCommand -device $device -deviceVar emulated_device -className $class -returnVar $hlt_ret -Parse $::sth::hlapiGen::Parse]
        regsub {.*-Scripts \{\[} $ret1 "" ret
        regsub -all {\]\} -CommandName.*} $ret "" ret
        #regsub -all { -} $ret "\\\n -" ret
        regsub -all {,} $ret " " ret
        set len [llength $ret]
        for {set i 0} {$i < $len} {incr i} {
            set hlapi_script [lindex $ret $i]
            regsub -all { -} $hlapi_script "\\\n -" hlapi_script
            puts_to_file $hlapi_script
        }
        set ::sth::hlapiGen::Parse "False"
    } retMsg]} {
        return -code 1 -errorcode -1 "exception during saveas stak: $retMsg"
    }
}

################Save as support for TWAMP###########################

proc ::sth::hlapiGen::hlapi_gen_device_twampserverconfig {device class mode hlt_ret cfg_args first_time} {

    set table_name "::sth::twamp::twampTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_twamp_config 
    append cfg_args "-type         server\\\n"
    set twampserverconfighdl [set ::sth::hlapiGen::$device\_obj(twampserverconfig)]
    if {[info exists ::sth::hlapiGen::$device\_$twampserverconfighdl\_attr(-ipversion)]} {
            set ipversion [set ::sth::hlapiGen::$device\_$twampserverconfighdl\_attr(-ipversion)]
            if { $ipversion == "IPV4"} {
                unset ::sth::hlapiGen::$device\_$twampserverconfighdl\_attr(-ipv6iftype)
            }
    }
    if {[info exists ::sth::hlapiGen::$device\_$twampserverconfighdl\_attr(-willingtoparticipate)]} {
            set willingtoparticipate [set ::sth::hlapiGen::$device\_$twampserverconfighdl\_attr(-willingtoparticipate)]
            if { $willingtoparticipate == "false"} {
                unset ::sth::hlapiGen::$device\_$twampserverconfighdl\_attr(-mode)
            }
    } 
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
}



proc ::sth::hlapiGen::hlapi_gen_device_twampclientconfig {device class mode hlt_ret cfg_args first_time} {

    set table_name "::sth::twamp::twampTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set cmd_name emulation_twamp_config 
    append cfg_args "-type         client\\\n"
    set twampclientconfighdl [set ::sth::hlapiGen::$device\_obj(twampclientconfig)]
    if {[info exists ::sth::hlapiGen::$device\_$twampclientconfighdl\_attr(-ipversion)]} {
            set ipversion [set ::sth::hlapiGen::$device\_$twampclientconfighdl\_attr(-ipversion)]
            if { $ipversion == "IPV4"} {
                unset ::sth::hlapiGen::$device\_$twampclientconfighdl\_attr(-ipv6iftype)
            }
    } 
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
    
    
    #For emulation_twamp_session_config
    if {[info exists ::sth::hlapiGen::$device\_$twampclientconfighdl\_attr(-children)]} {
        set twamptestsessionHdllist [set ::sth::hlapiGen::$device\_$twampclientconfighdl\_attr(-children)]
        set inc "0"
        foreach twamptestsessionHdl $twamptestsessionHdllist {
            twamp_session_config $twampclientconfighdl $twamptestsessionHdl $name_space $hlt_ret\_sessionhandle_$inc $inc 
            incr inc     
        }
    }
}


proc ::sth::hlapiGen::twamp_session_config {device obj_handle name_space hlt_ret incrm } {
    set class twamptestsession
    set cmd_name emulation_twamp_session_config
    
    
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
    } 
    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-handle			    \$device_created\\\n"
    #Unset attributes based on conditions
    if {[info exists ::sth::hlapiGen::$device\_$obj_handle\_attr(-paddingpattern)]} {
            set padding_pattern [set ::sth::hlapiGen::$device\_$obj_handle\_attr(-paddingpattern)]
            if { $padding_pattern == "RANDOM"} {
                unset ::sth::hlapiGen::$device\_$obj_handle\_attr(-paddinguserdefinedpattern)
            }
    }
    if {[info exists ::sth::hlapiGen::$device\_$obj_handle\_attr(-durationmode)]} {
            set duration_mode [set ::sth::hlapiGen::$device\_$obj_handle\_attr(-durationmode)]
            if { $duration_mode == "CONTINUOUS"} {
                unset ::sth::hlapiGen::$device\_$obj_handle\_attr(-duration)
                unset ::sth::hlapiGen::$device\_$obj_handle\_attr(-packetcount)
            } elseif { $duration_mode == "PACKETS"} {
                unset ::sth::hlapiGen::$device\_$obj_handle\_attr(-duration)
            } elseif { $duration_mode == "SECONDS"} {
                unset ::sth::hlapiGen::$device\_$obj_handle\_attr(-packetcount)
            }
    }
    
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    
    puts_to_file "set sessionhandle_$incrm \[keylget $hlt_ret handle\] "
}

proc ::sth::hlapiGen::hlapi_gen_device_vqahost {device class mode hlt_ret cfg_args first_time} {
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::hlapi_gen_device_vqaport {device class mode hlt_ret cfg_args first_time} {
    #if {![isVqaConfigured $device]} {
    #    return
    #}
    append cfg_args "-port_handle $::sth::hlapiGen::port_ret($device)\\\n"
    set vqaAnalyzer [set ::sth::hlapiGen::$device\_obj($class)]
    if {[info exists ::sth::hlapiGen::$vqaAnalyzer\_obj(vqdynamicpayloadconfig)]} {
        #need to configure the options for the vqdynamic payload
        set vqaDynamicPayload [set ::sth::hlapiGen::$vqaAnalyzer\_obj(vqdynamicpayloadconfig)]
        sth::hlapiGen::get_attr $vqaDynamicPayload $vqaDynamicPayload
        set table_name $sth::hlapiGen::hlapi_gen_tableName($class)
        ::sth::sthCore::InitTableFromTCLList [set $table_name]
        append cfg_args [::sth::hlapiGen::config_obj_attr "::sth::Vqa::" "emulation_vqa_port_config" $vqaAnalyzer $vqaDynamicPayload "vqdynamicpayloadconfig"]
    }

    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::hlapi_gen_device_vqaprobe {device class mode hlt_ret cfg_args first_time} {
    set port [stc::get $device -parent]
    append cfg_args "-port_handle $::sth::hlapiGen::port_ret($port)\\\n"
    gather_info_for_ctrl_res_func $port "vqprobechannelblock"
    set obj [set ::sth::hlapiGen::$device\_obj($class)]
    if {[regexp -nocase "unicast" [set ::sth::hlapiGen::$device\_$obj\_attr(-filtertype)]]} {
        #only the unicast related options can be output
        foreach attr {multicastipv4min multicastipv4max multicastipv6min multicastipv6max multicastudpmin multicastudpmax} {
            unset ::sth::hlapiGen::$device\_$obj\_attr(-$attr)
        }
    } else {
        # only the multicast related options can be output
        foreach attr {unicastipv4min unicastipv4max unicastipv6min unicastipv6max unicastudpmin unicastudpmax } {
            unset ::sth::hlapiGen::$device\_$obj\_attr(-$attr)
        }
    }
    set hlapi_script [hlapi_gen_device_basic_without_puts $device $class $mode $hlt_ret $cfg_args $first_time]
    puts_to_file $hlapi_script
}

proc ::sth::hlapiGen::hlapi_gen_device_vqaglobal {device class mode hlt_ret cfg_args first_time} {
    #if {![isVqaConfigured project1]} {
    #    return
    #}
    set hlapi_script [hlapi_gen_device_basic_without_puts $device $class "" $hlt_ret $cfg_args $first_time]
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::emulation_vqa_global_config"
}
proc ::sth::hlapiGen::isVqaConfigured {ports} {
    if {[regexp "project" $ports]} {
        set ports [stc::get project1 -children-port]
    }
    foreach port $ports {
        set probes [stc::get $port -children-probe]
        if {$probes != ""} {
            return 1
        }
        set devices [stc::get $port -AffiliationPort-sources]
        foreach device $devices {
            set vqa [stc::get $device -children-VqDeviceChannelBlock]
            if {$vqa != ""} {
                return 1
            }
        }
    }
    return 0
}

proc ::sth::hlapiGen::hlapi_gen_device_video {device class mode hlt_ret cfg_args first_time} {

    variable profile_ret
    set table_name ::sth::video::videoTable
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space "::sth::video::"
    if {$first_time} {
        hlapi_gen_device_deviceconfig $device "emulateddevice" "create" $hlt_ret $cfg_args $first_time
    }
    #::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $sub_class
    if {[regexp -nocase "server" $class]} {
        append cfg_args "			-type         server\\\n"
    } else {
        append cfg_args "			-type         client\\\n"
    }
    set sessionHnd [::sth::sthCore::invoke stc::get $device -children-$class]
    set ::sth::hlapiGen::device_ret($sessionHnd) "$hlt_ret\_$class 0"
    if {[info exists ::sth::hlapiGen::$device\_$sessionHnd\_attr(-connectiondestination-targets)]} {
        set connectedServer [set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-connectiondestination-targets)]
        if {[info exists ::sth::hlapiGen::device_ret($connectedServer)]} {
            puts_to_file "set connected_server \[keylget [lindex [set ::sth::hlapiGen::device_ret($connectedServer)] 0] session_handle\]"
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-connectiondestination-targets) \$connected_server
        }
    }

    ##process for clientprofile
    if {[info exists ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientprofile-targets)]} {
        set clientprofile [set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientprofile-targets)]

        if {[info exists profile_ret($clientprofile)]} {
            set hlt_returnval $profile_ret($clientprofile)
            puts_to_file "set clientprofilehandle \[keylget $hlt_returnval handle\] "
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientprofile-targets) \$clientprofilehandle
        } else {
            set profile_ret($clientprofile) $hlt_ret\_clientprofile
            sth::hlapiGen::get_attr $clientprofile $clientprofile
            set retclientprofile [client_profile_config $clientprofile $name_space $hlt_ret\_clientprofile]
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientprofile-targets) \$$retclientprofile
        }
    }
    #process for clientloadprofile
    if {[info exists ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientloadprofile-targets)]} {
        set loadprofile [set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientloadprofile-targets)]
        if {[info exists profile_ret($loadprofile)]} {
            set hlt_returnval $profile_ret($loadprofile)
            puts_to_file "set loadprofilehandle \[keylget $hlt_returnval handle\] "
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientloadprofile-targets) \$loadprofilehandle
        } else {
            set profile_ret($loadprofile) $hlt_ret\_loadprofile
            sth::hlapiGen::get_attr $loadprofile $loadprofile
            set retloadprofile [load_profile_config $loadprofile $name_space $hlt_ret\_loadprofile]
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedclientloadprofile-targets) \$$retloadprofile
        }
    }
    #process for serverprofile
    if {[info exists ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedserverprofile-targets)]} {
        set serverprofile [set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedserverprofile-targets)]
        if {[info exists profile_ret($serverprofile)]} {
            set hlt_returnval $profile_ret($serverprofile)
            puts_to_file "set serverprofilehandle \[keylget $hlt_returnval server_profile_handle\] "
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedserverprofile-targets) \$serverprofilehandle
        } else {
            set profile_ret($serverprofile) $hlt_ret\_serverprofile
            sth::hlapiGen::get_attr $serverprofile $serverprofile
            set retserverprofile [profile_server_config $serverprofile $name_space $hlt_ret\_serverprofile]
            set ::sth::hlapiGen::$device\_$sessionHnd\_attr(-affiliatedserverprofile-targets) \$$retserverprofile
        }
    }
    hlapi_gen_device_basic $device $class "enable" $hlt_ret\_$class $cfg_args 0
    set serverStreamList [::sth::sthCore::invoke stc::get $sessionHnd -children-videoserverstream]
    #generate the server stream for the videoserverprotocolconfig
    if {$serverStreamList != ""} {
        set i 0
        set session_def [get_device_created $sessionHnd session_created "session_handle"]
        puts_to_file $session_def
        set serverStreamCfg "			-handle			    \$session_created\\\n"

        foreach serverStream $serverStreamList {
            get_attr $serverStream $serverStream
            hlapi_gen_device_basic $serverStream "videoserverstream" "create" $hlt_ret\_$class\_serverStream\_$i $serverStreamCfg 1
            incr i
        }
    }
}
proc ::sth::hlapiGen::profile_server_config {device name_space hlt_ret} {
    variable $device\_obj
    set class serverprofile
    set cmd_name emulation_profile_config
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$cmd_name\\\n"
    }
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-profilename)]} {
        set profilename [set ::sth::hlapiGen::$device\_$device\_attr(-profilename)]
        regsub -all \\s+ $profilename _ profilename
        append cfg_args "			-profile_name			    $profilename\\\n"
    }
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_type	            server\\\n"
    #for serverprofile
    set class serverprofile
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    puts_to_file "set serverprofilehandle \[keylget $hlt_ret handle\] "
    return serverprofilehandle
}

proc ::sth::hlapiGen::client_profile_config {device name_space hlt_ret} {
    variable $device\_obj
    set class clientprofile
    set cmd_name emulation_profile_config
    set cfg_args ""
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$cmd_name\\\n"
    }
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-profilename)]} {
        set profilename [set ::sth::hlapiGen::$device\_$device\_attr(-profilename)]
        regsub -all \\s+ $profilename _ profilename
        append cfg_args "			-profile_name			    $profilename\\\n"
    }
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_type	            client\\\n"

    #for clientprofile
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]

    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    puts_to_file "set clientprofilehandle \[keylget $hlt_ret handle\] "
    return clientprofilehandle
}

proc ::sth::hlapiGen::load_profile_config {device name_space hlt_ret} {
    variable $device\_obj
    set class clientloadprofile
    set cmd_name emulation_profile_config
    if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
        append hlapi_script "        set $hlt_ret \[sth::$cmd_name\\\n"
    }
    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-profilename)]} {
        set profilename [set ::sth::hlapiGen::$device\_$device\_attr(-profilename)]
        regsub -all \\s+ $profilename _ profilename
        set ::sth::hlapiGen::$device\_$device\_attr(-profilename) $profilename
    }
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_type	            load\\\n"
    set obj_handle [set $device\_obj($class) ]
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    puts_to_file "set loadprofilehandle \[keylget $hlt_ret handle\] "

    #for emulation_load_phase_config
    if {[info exists ::sth::hlapiGen::$device\_obj(clientloadphase)]} {
        set phaselist [set ::sth::hlapiGen::$device\_obj(clientloadphase)]
        set phasenum 0
        foreach phase $phaselist {
            load_phase_config $device $phase $hlt_ret\_$phasenum $name_space
            incr phasenum
        }
    }
    return loadprofilehandle
}
proc ::sth::hlapiGen::load_phase_config {device phase_handle hlt_ret name_space} {
    set class clientloadphase
    set cmd_name emulation_load_phase_config
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
        append hlapi_script "        set $hlt_ret \[sth::emulation_client_load_phase_config\\\n"
    }

    #set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    set cmd_name "emulation_client_load_phase_config"
    append hlapi_script "			-mode			    create\\\n"
    append hlapi_script "			-profile_handle	            \$loadprofilehandle  \\\n"
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $phase_handle $class]
    append hlapi_script $cfg_args
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
}

proc ::sth::hlapiGen::isRealismConfigured {ports} {
    if {[regexp "project" $ports]} {
        set realismoptions [stc::get project1 -children-realismoptions]
        set realismMode [stc::get $realismoptions -RealismMode]
        if {[regexp -nocase "CONTROL_PLANE" $realismMode]} {
            return 1
        }
    }
    return 0
}

proc ::sth::hlapiGen::hlapi_gen_device_realism {device class mode hlt_ret cfg_args first_time} {
    set hlapi_script [hlapi_gen_device_basic_without_puts $device $class "" $hlt_ret $cfg_args $first_time]
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::system_settings"
}
