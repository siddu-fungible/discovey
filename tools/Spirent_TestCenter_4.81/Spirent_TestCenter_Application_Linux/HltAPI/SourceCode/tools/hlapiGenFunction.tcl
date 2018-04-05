namespace eval ::sth::hlapiGen:: {

}

#########################################################################################################
#    hlapiGenFunction.tcl includes the functions to handle the hltapi configure functions 
#    whose (protocol) name is from A to G.
#    Added protocols/functions:
#              a. interface_config
#              b. bgp
#              c. dhcp
#              d. gre
#########################################################################################################


#--------------------------------------------------------------------------------------------------------#
#interface config convert function, it is used to generate the hltapi interface_config function
#input:     port        =>  the port on which the interface config function will be used
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#output:    the genrated hltapi interface_config funtion will be output to the file.

proc ::sth::hlapiGen::hlapi_gen_interface_convert_func {port mode hlt_ret} {
    set name_space "::sth::Session::"
    set table_name "::sth::Session::sessionTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    
    
    variable $port\_obj
    variable $port\_$port\_attr
	set phy_types "EthernetCopper Ethernet10GigCopper EthernetFiber Ethernet10GigFiber Ethernet100GigFiber Ethernet40GigFiber POSPhy AtmPhy FcPhy"
    foreach phy_type $phy_types {
        if {[info exists $port\_obj([string tolower $phy_type])]} {
            if {![info exists $port\_$port\_attr(-activephy-targets)] || [regexp -nocase $phy_type [set $port\_$port\_attr(-activephy-targets)]]} {
                set class [string tolower $phy_type]
                set cmd_name "interface_config_$phy_type"
                break
            }
        }
    }
    if {![info exists class]} {
        puts "hltapi only support the phy type to be \
                EthernetCopper, Ethernet10GigCopper, EthernetFiber, Ethernet10GigFiber, \
                Ethernet100GigFiber, Ethernet40GigFiber ,POSPhy or AtmPhy"
        return
    }
     
    set cfg_args [::sth::hlapiGen::interface_pre_process $port $class $cmd_name]

    set hlapi_script ""
    set port_handle $::sth::hlapiGen::port_ret($port)
    
    append hlapi_script "set $hlt_ret \[sth::interface_config \\\n"
    append hlapi_script "                   -mode               $mode \\\n"
    append hlapi_script "                   -port_handle        $port_handle \\\n"
	append hlapi_script "                   -create_host        false \\\n"
    append hlapi_script $cfg_args
    
    #process the host related attr
    set class "host"
    set host_handle [set $port\_obj($class)]
    if {[llength $host_handle] > 1} {
        set host_handle [lindex $host_handle 0]
    }
    
    foreach class [array names ::sth::hlapiGen::$port\_obj] {
        set phytypeFlag 0
        foreach phy_type $phy_types {
            if {[regexp -nocase $phy_type $class]} {
                set phytypeFlag 1
                break
            }
        }
        if {$phytypeFlag} {
            continue    
        }
        set obj_handles [set ::sth::hlapiGen::$port\_obj($class)]
        
        foreach obj_handle $obj_handles {
            append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $port $obj_handle $class]
        }
    }
    #handle active phy interface
    set obj_handle [stc::get $port -activephy-Targets]
    regsub {\d+$} $obj_handle "" class
    append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $port $obj_handle $class]
    
    append hlapi_script "\]\n"  
    puts_to_file $hlapi_script
}

#--------------------------------------------------------------------------------------------------------#
# to pre-process the args in the interface_config fucntion, which are special.
#input:     port        => the port handle which will be used
#           class       => the class name
#output: return the arg and value pairs in the hltapi function
proc ::sth::hlapiGen::interface_pre_process {port class cmd_name} {
    set cfg_args ""
    
    #pre-process the -intf_mode, phy_mode,
    if {[regexp -nocase "ethernet" $class]} {
        append cfg_args "           -intf_mode              ethernet\\\n"
        if {[regexp -nocase "fiber" $class]} {
            append cfg_args "           -phy_mode               fiber\\\n"
        } else {
            append cfg_args "           -phy_mode               copper\\\n"
        }
    } elseif {[regexp -nocase "atm" $class]} {
        append cfg_args "           -intf_mode              atm\\\n"
    } elseif {[regexp -nocase "pos" $class]} {
        set posphy [set ::sth::hlapiGen::$port\_obj($class)]
        set sonet [set ::sth::hlapiGen::$posphy\_obj(sonetconfig)]
        if {[regexp -nocase "DISABLE" [set ::sth::hlapiGen::$posphy\_$sonet\_attr(-hdlcenable)]]} {
            append cfg_args "           -intf_mode              pos_ppp\\\n"
        } else {
            append cfg_args "           -intf_mode              pos_hdlc\\\n"
        }
    } elseif {[regexp -nocase "fc" $class]} {
        append cfg_args "           -intf_mode              fc\\\n"
    }
    
    #pre-process vlan
    if {[info exists ::sth::hlapiGen::$port\_obj(vlanif)]} {
        append cfg_args "           -vlan              1\\\n"
    }
    set name_space "::sth::Session::"
    set table_name "::sth::Session::sessionTable"
    
    foreach arg {vlan_outer_cfi vlan_outer_id vlan_outer_id_step vlan_outer_user_priority} {
        if {[info exists $name_space$cmd_name\_stcobj($arg)]} {
            set $name_space$cmd_name\_stcobj($arg) "VlanIf_Outer"
        }
        
    }

    # internal_ppm_adjust: changing the format for negative values {"-2"}
    if {[regexp -nocase "fiber" $class]} {
        set obj_handle [stc::get $port -activephy-Targets]
        set value [set ::sth::hlapiGen::$port\_$obj_handle\_attr(-internalppmadjust)]
        if {$value < 0} {
            set value "{\"$value\"}"
            set ::sth::hlapiGen::$port\_$obj_handle\_attr(-internalppmadjust) $value
        }
    }
    #pre-process qinq_incr_mode vlan_id_count vlan_outer_id_count
    
    #pre-process arp_cache_retrieve, arpnd_report_retrieve, arp_target, arp_send_req, arp_req_timer
    # for these attr, we can only output that we can config these attr
    
    ##enable_ping_response host-EnablePingResponse
    #set host [set ::sth::hlapiGen::$port\_obj(host)]
    #set enable_ping_response [set ::sth::hlapiGen::$port\_$host\_attr(-enablepingresponse)]
    #if {[regexp -nocase "true" $enable_ping_response]} {
    #    set enable_ping_response 1
    #} else {
    #    set enable_ping_response 0
    #}
    
    #append cfg_args "                -enable_ping_response           $enable_ping_response \\\n"
    
    #scheduling_mode port-children-Generator-children-GeneratorConfig-SchedulingMode
    set generator [set ::sth::hlapiGen::$port\_obj(generator)]
    set generator_config [set ::sth::hlapiGen::$generator\_obj(generatorconfig)]
    set scheduling_mode [set ::sth::hlapiGen::$generator\_$generator_config\_attr(-schedulingmode)]
    set port_loadunit [set ::sth::hlapiGen::$generator\_$generator_config\_attr(-loadunit)]
    set port_load [set ::sth::hlapiGen::$generator\_$generator_config\_attr(-fixedload)]
    append cfg_args "                -scheduling_mode           $scheduling_mode \\\n"
    append cfg_args "                -port_loadunit           $port_loadunit \\\n"
    append cfg_args "                -port_load           $port_load \\\n"
    return $cfg_args
}



#--------------------------------------------------------------------------------------------------------#
proc ::sth::hlapiGen::hlapi_gen_device_ancpconfig {device class mode hlt_ret cfg_args first_time} {
    variable $device\_obj
    #pre_process the encap_type
    if {[info exists $device\_obj(ethiiif)]} {
        if {[info exists $device\_obj(aal5if)]} {
            set aal5if [set $device\_obj(aal5if)]
            set vc_encap [set sth::hlapiGen::$device\_$aal5if\_attr(-vcencapsulation)]
            if {[regexp -nocase "LLC_ENCAPSULATED" $vc_encap]} {
                append cfg_args "-encap_type    ATM_LLC_SNAP_ETHERNETII\\\n"
            } else {
                append cfg_args "-encap_type    ATM_VC_MUX_ETHERNETII\\\n"
            }
        } else {
            append cfg_args "-encap_type   ETHERNETII\\\n"
        }
    } elseif {[info exists $device\_obj(aal5if)]} {
        set aal5if [set $device\_obj(aal5if)]
        set vc_encap [set sth::hlapiGen::$device\_$aal5if\_attr(-vcencapsulation)]
        if {[regexp -nocase "LLC_ENCAPSULATED" $vc_encap]} {
            append cfg_args "-encap_type    LLC_SNAP\\\n"
        } else {
            append cfg_args "-encap_type    VC_MUX\\\n"
        }
    }
    set table_name "::sth::Ancp::ancpTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set ancpconfig [set $device\_obj($class)]
    set ipv4network [set sth::hlapiGen::$ancpconfig\_obj(ipv4networkblock)]
    append cfg_args [config_obj_attr ::sth::Ancp:: emulation_ancp_config $ancpconfig $ipv4network ipv4networkblock]
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::hlapi_gen_device_subscribe_line {ancp_router_config_list} {
    
    #next check if need the sth::emulation_ancp_subscriber_lines_config
    #ancpaccessnodeconfig ancpaccessloopblockconfig -L2NetworkIf
    set i 0
    foreach ancpconfig $ancp_router_config_list {
        if {[info exists ::sth::hlapiGen::$ancpconfig\_obj(ancpaccessloopblockconfig)]} {
            set ancploopblocklist [set ::sth::hlapiGen::$ancpconfig\_obj(ancpaccessloopblockconfig)]
            foreach ancploopblock $ancploopblocklist {
                set l2networkif [stc::get $ancploopblock -l2networkif]
                if {![regexp "^$" $l2networkif]} {
                    #here will call the  sth::emulation_ancp_subscriber_lines_config
                    set host_handle [stc::get $l2networkif -parent]
                    set subscribe_cfg_args ""
                    set device [stc::get $ancpconfig -parent]
                    puts_to_file [get_device_created $device ancp_router ""]
                    puts_to_file [get_device_created $host_handle subscribe_host ""]
                    append subscribe_cfg_args "set ancp_subscriber$i \[sth::emulation_ancp_subscriber_lines_config\\\n"
                    append subscribe_cfg_args " -mode       create\\\n"
                    append subscribe_cfg_args "             -ancp_client_handle        \$ancp_router\\\n"
                    append subscribe_cfg_args "             -handle        \$subscribe_host\\\n"
                    #next need to handle the subscribe_host related 
                    set subscribe_host_args [subscribe_host_process $host_handle]
                    append subscribe_cfg_args $subscribe_host_args
                    #next need to find the tlv info
                    set subscount [stc::get $host_handle -DeviceCount]
                    append subscribe_cfg_args "-subscriber_lines_per_access_node  $subscount\\\n"
                    set ancptlv1 [set ::sth::hlapiGen::$ancploopblock\_obj(ancptlvconfig)]
                    set tvl_args1 [ancptlv_process $ancptlv1 $subscount]
                    append subscribe_cfg_args $tvl_args1
                    if {[info exists ::sth::hlapiGen::$ancpconfig\_$ancploopblock\_attr(-affiliatedancpdsllineprofile-targets)]} {
                        set ancpdsllineprofile [set ::sth::hlapiGen::$ancpconfig\_$ancploopblock\_attr(-affiliatedancpdsllineprofile-targets)]
                        set ancptlv2 [stc::get $ancpdsllineprofile -children-ancptlvconfig]
                        set tvl_args2 [ancptlv_process $ancptlv2 $subscount]
                        append subscribe_cfg_args $tvl_args2
                    }
                    append subscribe_cfg_args "\]\n"
                    puts_to_file $subscribe_cfg_args
					set sth::hlapiGen::device_ret($ancpconfig) ancp_subscriber$i
                    gen_status_info ancp_subscriber$i "sth::emulation_ancp_subscriber_lines_config"
                }
            }
        }
        incr i
    }
}
proc ::sth::hlapiGen::subscribe_host_process {host_handle} {
    variable $host_handle\_obj
    set subscribe_host_args ""
    if {[info exists $host_handle\_obj(vlanif)]} {
        append subscribe_host_args "-vlan_allocation_model      1_1\\\n"
        append subscribe_host_args "-enable_c_vlan      1\\\n"
        set vlanif [lindex [set $host_handle\_obj(vlanif)] 0]
        set isrange [set ::sth::hlapiGen::$host_handle\_$vlanif\_attr(-isrange)]
        if {[regexp -nocase "false" $isrange]} {
            set vlan_id [set ::sth::hlapiGen::$host_handle\_$vlanif\_attr(-idlist)]
            append subscribe_host_args "-customer_vlan_id       \"$vlan_id\"\\\n"
        } else {
            set vlan_id [set ::sth::hlapiGen::$host_handle\_$vlanif\_attr(-vlanid)]
            append subscribe_host_args "-customer_vlan_id       $vlan_id\\\n"
            set vlan_id_step [set ::sth::hlapiGen::$host_handle\_$vlanif\_attr(-idstep)]
            if {$vlan_id_step > 1} {
                append subscribe_host_args "-customer_vlan_id_step       $vlan_id_step\\\n"
            }
            set vlan_id_repeat [set ::sth::hlapiGen::$host_handle\_$vlanif\_attr(-idrepeatcount)]
            if {$vlan_id_repeat > 0} {
                set vlan_id_repeat [expr $vlan_id_repeat + 1]
                append subscribe_host_args "-customer_vlan_id_repeat        $vlan_id_repeat\\\n"
            }
        }
    }
    return $subscribe_host_args
}

proc ::sth::hlapiGen::ancptlv_process {ancptlv subscribe_count} {
    set tlv_args ""
    set tlv_list [stc::get $ancptlv -children]
    set upstream_rate_tlv_list ""
    set downstream_rate_tlv_list ""
    set rate_delay_args ""
    foreach tlv $tlv_list {
        switch -regexp -- [string tolower $tlv] {
            accessloopcircuitidtlv {
                #-circuit_id
                #-circuit_id_suffix
                #-circuit_id_suffix_step
                #-circuit_id_suffix_repeat
                
                if {[lsearch $tlv_args "^-circuit_id$"] == -1} {
                    set circuit_id [stc::get $tlv -ID]
                    if {[regexp "null" $circuit_id]} {
                        append tlv_args "-circuit_id        Access-Node-Identifier\\\n"
                    } else {
                        append tlv_args "-circuit_id        $circuit_id\\\n"
                    }
                    
                }
                set accessloopcircuitidtlv_name [stc::get $tlv -name]
                set wildcardmodifers [stc::get $ancptlv -children-AncpWildcardModifier]
                foreach wildcardmodifer $wildcardmodifers {
                    set wildcardmodifer_offset [stc::get $wildcardmodifer -OffsetReference]
                    if {[regexp -nocase "$accessloopcircuitidtlv_name.ID" $wildcardmodifer_offset]} {
                        set wildcardmodifer_data [stc::get $wildcardmodifer -Data]
                        #hltapi only support the @x()
                        if {[regexp {@x\(} $wildcardmodifer_data]} {
                            set index [expr [string first "@x\(" $wildcardmodifer_data] - 1]
                            set wildcardmodifer_data [string replace $wildcardmodifer_data 0 $index ""]
                            set index2 [string first "\)" $wildcardmodifer_data]
                            set wildcardmodifer [string range $wildcardmodifer_data 3 [expr $index2 - 1]]
                            #the format can be @x($suffix,0,$suffixStep,1,$suffixRepeat)
                            set wilcard_list [split $wildcardmodifer ","]
                            set suffix [lindex $wilcard_list 0]
                            append tlv_args "-circuit_id_suffix  $suffix\\\n"
                            if {[llength $wilcard_list] > 2} {
                                set suffix_step [lindex $wilcard_list 2]
                                if {$suffix_step > 1} {
                                    append tlv_args "-circuit_id_suffix_step   $suffix_step\\\n"
                                }
                            }
                            if {[llength $wilcard_list] > 4} {
                                set suffix_repeat [lindex $wilcard_list 4]
                                if {$suffix_repeat > 0} {
                                    set suffix_repeat [expr $suffix_repeat + 1]
                                    append tlv_args "-circuit_id_suffix_repeat   $suffix_repeat\\\n"
                                }
                            }
                        }
                        break
                    }
                }
                
            }
            
            accessloopremoteidtlv {
                # -remote_id
                # -remote_id_suffix
                # -remote_id_suffix_step
                # -remote_id_suffix_repeat
                
                if {[lsearch $tlv_args "^-remote_id$"] == -1} {
                    set remote_id [stc::get $tlv -ID]
                    if {[regexp null $remote_id]} {
                        append tlv_args "-remote_id        SPIRENT\\\n"
                    } else {
                        append tlv_args "-remote_id        $remote_id\\\n"
                    }
                }
                set accessloopremoteidtlv_name [stc::get $tlv -name]
                set wildcardmodifers [stc::get $ancptlv -children-AncpWildcardModifier]
                foreach wildcardmodifer $wildcardmodifers {
                    set wildcardmodifer_offset [stc::get $wildcardmodifer -OffsetReference]
                    if {[regexp -nocase "$accessloopremoteidtlv_name.ID" $wildcardmodifer_offset]} {
                        set wildcardmodifer_data [stc::get $wildcardmodifer -Data]
                        #hltapi only support the @x()
                        if {[regexp {@x\(} $wildcardmodifer_data]} {
                            set index [expr [string first "@x\(" $wildcardmodifer_data] - 1]
                            set wildcardmodifer_data [string replace $wildcardmodifer_data 0 $index ""]
                            set index2 [string first "\)" $wildcardmodifer_data]
                            set wildcardmodifer [string range $wildcardmodifer_data 3 [expr $index2 - 1]]
                            #the format can be @x($suffix,0,$suffixStep,1,$suffixRepeat)
                            set wilcard_list [split $wildcardmodifer ","]
                            set suffix [lindex $wilcard_list 0]
                            append tlv_args "-remote_id_suffix  $suffix\\\n"
                            if {[llength $wilcard_list] > 2} {
                                set suffix_step [lindex $wilcard_list 2]
                                if {$suffix_step > 1} {
                                    append tlv_args "-remote_id_suffix_step   $suffix_step\\\n"
                                }
                            }
                            if {[llength $wilcard_list] > 4} {
                                set suffix_repeat [lindex $wilcard_list 4]
                                if {$suffix_repeat > 0} {
                                    set suffix_repeat [expr $suffix_repeat + 1]
                                    append tlv_args "-remote_id_suffix_repeat   $suffix_repeat\\\n"
                                }
                            }
                        }
                        break
                    }
                }
            }
            
            accessaggregationcircuitidbinaryvlantlv {
                # -tlv_service_vlan_id
                # -tlv_service_vlan_id_wildcard
                # -tlv_customer_vlan_id
                # -tlv_customer_vlan_id_wildcard
                if {[lsearch $tlv_args "^-tlv_service_vlan_id$"] == -1} {
                    set tlv_service_vlan_id [stc::get $tlv -Vlan1]
                    if {[regexp null $tlv_service_vlan_id]} {
                        append tlv_args "-tlv_service_vlan_id        0\\\n"
                    }
                }
                if {[lsearch $tlv_args "^-tlv_customer_vlan_id$"] == -1} {
                    set tlv_customer_vlan_id [stc::get $tlv -Vlan2]
                    if {[regexp null $tlv_customer_vlan_id]} {
                        append tlv_args "-tlv_customer_vlan_id        0\\\n"
                    }
                }
                set accessaggregationcircuitidbinaryvlantlv_name [stc::get $tlv -name]
                set wildcardmodifers [stc::get $ancptlv -children-AncpWildcardModifier]
                foreach wildcardmodifer $wildcardmodifers {
                    set wildcardmodifer_offset [stc::get $wildcardmodifer -OffsetReference]
                    if {[regexp -nocase "$accessaggregationcircuitidbinaryvlantlv_name.Vlan1" $wildcardmodifer_offset]} {
                        set tlv_service_vlan_id [stc::get $wildcardmodifer -Data]
                        append tlv_args "-tlv_service_vlan_id_wildcard  1\\\n"
                    } elseif {[regexp -nocase "$accessaggregationcircuitidbinaryvlantlv_name.Vlan2" $wildcardmodifer_offset]} {
                        set tlv_customer_vlan_id [stc::get $wildcardmodifer -Data]
                        append tlv_args "-tlv_customer_vlan_id_wildcard  1\\\n"
                    }
                }
                append tlv_args "-tlv_service_vlan_id        $tlv_service_vlan_id\\\n"
                append tlv_args "-tlv_customer_vlan_id        $tlv_customer_vlan_id\\\n"
            }
            
            accessloopencapsulationtlv {
                #-include_encap {0|1}]
                #-data_link { ethernet | atm_aal5}]
                #-encap1 { na | untagged_ethernet | single_tagged_ethernet }] 
                #-encap2 {na | pppoa_llc| pppoa_null | ipoa_llc | ipoa_null | aal5_llc_w_fcs | 
                        #aal5_llc_wo_fcs | aal5_null_w_fcs | aal5_null_wo_fcs }]
                if {[lsearch $tlv_args "^-include_encap$"] == -1} {
                    set tlv_attr [stc::get $tlv]
                    set include_encap 1
                    set data_link [stc::get $tlv -DataLink]
                    if {[regexp "00" $data_link]} {
                        set data_link "atm_aal5"
                    } else {
                        set data_link "ethernet"
                    }
                    set encap1 [stc::get $tlv -Encaps1]
                    switch -regexp -- $encap1 {
                        01 {
                            set encap1 untagged_ethernet
                        }
                        02 {
                            set encap1 single_tagged_ethernet
                        }
                        default {
                            set encap1 na
                        }
                    }
                    set encap2 [stc::get $tlv -Encaps2]
                    switch -regexp -- $encap2 {
                        01 {
                            set encap2 pppoa_llc
                        }
                        02 {
                            set encap2 pppoa_null
                        }
                        03 {
                            set encap2 ipoa_llc
                        }
                        04 {
                            set encap2 ipoa_null
                        }
                        05 {
                            set encap2 aal5_llc_w_fcs
                        }
                        06 {
                            set encap2 aal5_llc_wo_fcs
                        }
                        07 {
                            set encap2 aal5_null_w_fcs
                        }
                        08 {
                            set encap2 aal5_null_wo_fcs
                        }
                        default {
                            set encap2 na
                        }
                    }
                    append tlv_args "-include_encap     $include_encap\\\n"
                    append tlv_args "-data_link   $data_link\\\n"
                    append tlv_args  "-encap1           $encap1\\\n"
                    append tlv_args  "-encap2           $encap2\\\n"
                }
            }
            
            dsltypetlv {
                #-dsl_type { adsl1 | adsl2 | adsl2_plus | vdsl1 | vdsl2 | sdsl | unknown }
                
                if {[lsearch $tlv_args "^-dsl_type$"] == -1} {
                    set dsl_type [stc::get $tlv -DslType]
                    switch -regexp -- $dsl_type {
                        01 {
                            set dsl_type adsl1
                        }
                        02 {
                            set dsl_type adsl2
                        }
                        03 {
                            set dsl_type adsl2_plus
                        }
                        04 {
                            set dsl_type vdsl1
                        }
                        05 {
                            set dsl_type vdsl2
                        }
                        06 {
                            set dsl_type sdsl
                        }
                        07 {
                            set dsl_type "unknown"
                        }
                        default {
                            set dsl_type ""
                        }
                    }
                    if {![regexp "^$" $dsl_type]} {
                        append tlv_args "-dsl_type        $dsl_type\\\n"
                    }
                    
                }
            }
            
            actualnetdatarateupstreamtlv {
                set upstream_rate_tlv_list [concat $upstream_rate_tlv_list $tlv]
            }
            
            minimumnetdatarateupstreamtlv {
                #upstream_min_rate
                set rate_delay_args [concat $rate_delay_args upstream_min_rate]
                set upstream_min_rate [stc::get $tlv -Rate]

            }
            
            maximumnetdatarateupstreamtlv {
                #upstream_max_rate
                set rate_delay_args [concat $rate_delay_args upstream_max_rate]
                set upstream_max_rate [stc::get $tlv -Rate]
            }
            
            attainablenetdatarateupstreamtlv {
                #upstream_attainable_rate
                set rate_delay_args [concat $rate_delay_args upstream_attainable_rate]
                set upstream_attainable_rate [stc::get $tlv -Rate]
            }
            
            minimumnetlowpowerdatarateupstreamtlv {
                #upstream_min_low_power_rate
                set rate_delay_args [concat $rate_delay_args upstream_min_low_power_rate]
                set upstream_min_low_power_rate [stc::get $tlv -Rate]
            }
            
            maximuminterleavingdelayupstreamtlv {
                #upstream_max_interleaving_delay
                set rate_delay_args [concat $rate_delay_args upstream_max_interleaving_delay]
                set upstream_max_interleaving_delay [stc::get $tlv -time]
            }
            
            actualinterleavingdelayupstreamtlv {
                #upstream_act_interleaving_delay
                set rate_delay_args [concat $rate_delay_args upstream_act_interleaving_delay]
                set upstream_act_interleaving_delay [stc::get $tlv -time]
            }
            
            actualnetdataratedownstreamtlv {
                set downstream_rate_tlv_list [concat $downstream_rate_tlv_list $tlv]
                
            }
            
            minimumnetdataratedownstreamtlv {
                #-downstream_min_rate
                set rate_delay_args [concat $rate_delay_args downstream_min_rate]
                set downstream_min_rate [stc::get $tlv -Rate]
            }
            
            maximumnetdataratedownstreamtlv {
                #downstream_max_rate
                set rate_delay_args [concat $rate_delay_args downstream_max_rate]
                    set downstream_max_rate [stc::get $tlv -Rate]
                  
            }
            
            attainablenetdataratedownstreamtlv {
                #downstream_attainable_rate
                set rate_delay_args [concat $rate_delay_args downstream_attainable_rate]
                set downstream_attainable_rate [stc::get $tlv -Rate]
            }
            
            minimumnetlowpowerdataratedownstreamtlv {
                #downstream_min_low_power_rate
                set rate_delay_args [concat $rate_delay_args downstream_min_low_power_rate]
                set downstream_min_low_power_rate [stc::get $tlv -Rate]
            }
            
            maximuminterleavingdelaydownstreamtlv {
                #downstream_max_interleaving_delay
                set rate_delay_args [concat $rate_delay_args downstream_max_interleaving_delay]
                set downstream_max_interleaving_delay [stc::get $tlv -time]
            }
            
            actualinterleavingdelaydownstreamtlv {
                #downstream_act_interleaving_delay
                set rate_delay_args [concat $rate_delay_args downstream_act_interleaving_delay]
                set downstream_act_interleaving_delay [stc::get $tlv -time]
            }
            
            ancpwildcardmodifier {
                
            }
            default {
                set tlv_name [stc::get $tlv -name]
                puts "hltapi don't support this kind of tlv: $tlv_name\n"
            }
        }
        
    }
    foreach rate_delay_arg $rate_delay_args {
        if {[lsearch $tlv_args "^-$rate_delay_arg$"] == -1} {
            if {![regexp "null" [set $rate_delay_arg]]} {
                append tlv_args "-$rate_delay_arg  [set $rate_delay_arg]\\\n"  
            } else {
                append tlv_args "-$rate_delay_arg  0\\\n"  
            }
        }
    }
    #set ancploop [stc::get $ancptlv -parent]
    #set subscribe_count []
    #-actual_rate_downstream <integer>] 
    #-actual_rate_downstream_step <integer>]
    #-actual_rate_downstream_repeat <integer>]
    set actual_rate_downstream_list ""
    foreach downstream_rate_tlv $downstream_rate_tlv_list {
        set actual_rate_downstream [stc::get $downstream_rate_tlv -Rate]
        set actual_rate_downstream_list [concat $actual_rate_downstream_list $actual_rate_downstream]
    }
    set count [llength $actual_rate_downstream_list]
    if {$count> 0} {
        set actual_rate_downstream_list [lsort $actual_rate_downstream_list]
        set actual_rate_downstream1 [lindex $actual_rate_downstream_list 0]
        if {[regexp "null" $actual_rate_downstream1]} {
            append tlv_args "-actual_rate_downstream        0\\\n"
        } else {
            append tlv_args "-actual_rate_downstream        $actual_rate_downstream1\\\n"
        }
        if {$count >= 2} {
            set actual_rate_downstream2 [lindex $actual_rate_downstream_list 1]
            set actual_rate_downstream_step [expr {$actual_rate_downstream2 - $actual_rate_downstream1}]
            append tlv_args "-actual_rate_downstream_step       $actual_rate_downstream_step\\\n"
            
            set actual_rate_downstream_repeat [expr {$subscribe_count/$count - 1}]
            if {[expr $subscribe_count%$count] != 0} {
                set actual_rate_downstream_repeat [expr $actual_rate_downstream_repeat + 1]
            }
            if {$actual_rate_downstream_repeat >= 1} {
                append tlv_args "-actual_rate_downstream_repeat       $actual_rate_downstream_repeat\\\n"
            }
            
        }
        
    }
    
    #set tlv_attr [stc::get $tlv -Rate]
    #-actual_rate_upstream <integer>] 
    #-actual_rate_upstream_step <integer>]
    #-actual_rate_upstream_repeat <integer>]
    set actual_rate_upstream_list ""
    foreach upstream_rate_tlv $upstream_rate_tlv_list {
        set actual_rate_upstream [stc::get $upstream_rate_tlv -Rate]
        set actual_rate_upstream_list [concat $actual_rate_upstream_list $actual_rate_upstream]
    }
    set count [llength $actual_rate_upstream_list]
    
    if {$count> 0} {
        set actual_rate_upstream_list [lsort $actual_rate_upstream_list]
        set actual_rate_upstream1 [lindex $actual_rate_upstream_list 0]
        if {[regexp "null" $actual_rate_upstream1]} {
            append tlv_args "-actual_rate_upstream        0\\\n"
        } else {
            append tlv_args "-actual_rate_upstream        $actual_rate_upstream1\\\n"
        }
        
        if {$count >= 2} {
            set actual_rate_upstream2 [lindex $actual_rate_upstream_list 1]
            set actual_rate_upstream_step [expr {$actual_rate_upstream2 - $actual_rate_upstream1}]
            append tlv_args "-actual_rate_upstream_step       $actual_rate_upstream_step\\\n"
            
            set actual_rate_upstream_repeat [expr {$subscribe_count/$count - 1}]
            if {[expr $subscribe_count%$count] != 0} {
                set actual_rate_upstream_repeat [expr $actual_rate_upstream_repeat + 1]
            }
            if {$actual_rate_upstream_repeat >= 1} {
                append tlv_args "-actual_rate_upstream_repeat       $actual_rate_upstream_repeat\\\n"
            }
            
        }
        
    }
    return $tlv_args
    
}
#--------------------------------------------------------------------------------------------------------#
#bgp config convert function, it is used to generate the hltapi emulation_bgp_config function
#input:     device      =>  the port on which the interface config function will be used
#           calss       =>  the class name
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#           cfg_args    => the args prepared earlier for the bgp config function
#           first_time  => is this the first time to config the protocol on this device
#output:    the genrated hltapi interface_config funtion will be output to the file.
proc ::sth::hlapiGen::hlapi_gen_device_bgpconfig {device class mode hlt_ret cfg_args first_time} {
   
    #config bgp router
    #pre-process the options under BgpGlobalConfig, first need to get the bgpGlobalConfig
    
    bgp_router_pre_process $cfg_args $device
    
    hlapi_gen_device_basic $device $class enable $hlt_ret $cfg_args $first_time
    set hltapi_config ""
    #config the bgp routes under the router
    
    set route_mode "add"
    #get all the routes handles
    set cfg_ret [lindex $::sth::hlapiGen::device_ret($device) 0]
    
    set devices [update_device_handle $device $class $first_time]
    

    set j 1
    
    foreach device $devices {
        
        set route_types ""
        
        variable $device\_obj
	set bgp_config_handle [set $device\_obj($class)]
	variable $bgp_config_handle\_obj
        if {[info exists ::sth::hlapiGen::$bgp_config_handle\_obj(bgpipv4routeconfig)]} {
            #cofig the ipv4 bgp routes
            set networkblock "ipv4networkblock"
            set route_types "bgpipv4routeconfig"
            
        }
        if {[info exists ::sth::hlapiGen::$bgp_config_handle\_obj(bgpipv6routeconfig)]} {
            #config the ipv6 bgp routes
            set networkblock "ipv4networkblock"
            set route_types [concat $route_types bgpipv6routeconfig]
        }
        # for bgpflowspecconfig
        if {[info exists ::sth::hlapiGen::$bgp_config_handle\_obj(bgpflowspecconfig)]} {
            set route_types [concat $route_types bgpflowspecconfig]
        }
        if {[info exists ::sth::hlapiGen::$bgp_config_handle\_obj(bgpsrtepolicyconfig)]} {
            set route_types [concat $route_types bgpsrtepolicyconfig]
        }                                                                                  

        foreach route_type $route_types {
            set route_cfg_args_common ""
            append route_cfg_args_common "			-mode			    add\\\n"
            if {[regexp "bgpipv4routeconfig" $route_type]} {
                append route_cfg_args_common "           -ip_version         4\\\n"
            } elseif {[regexp "bgpipv6routeconfig" $route_type]} {
                append route_cfg_args_common "           -ip_version         6\\\n"
            }
            #BgpIpv4VplsConfig BgpVplsAdConfig
            if {$route_type!="bgpflowspecconfig"} {
                foreach subclass "bgpipv4vplsConfig bgpipv6vplsConfig bgpvplsadconfig" {
                    if {[info exists $bgp_config_handle\_obj($subclass)]} {
                        set sub_obj [set $bgp_config_handle\_obj($subclass)]
                        append route_cfg_args_common [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgp_config_handle $sub_obj $subclass]
                    }
                }
            }
            set bgproute_handles [set ::sth::hlapiGen::$bgp_config_handle\_obj($route_type)]
            foreach bgproute_handle $bgproute_handles {
                gather_info_for_ctrl_res_func $bgproute_handle $route_type
                puts_to_file [get_device_created $device bgp_router$j handle]
                
                set element_cfg_args ""
                set element_flag 0
                set route_cfg_args ""
                set hlt_ret_route $hlt_ret\_route$j
                set sth::hlapiGen::device_ret($bgproute_handle) $hlt_ret_route
                append route_cfg_args "      set $hlt_ret_route \[sth::emulation_bgp_route_config\\\n"
                append route_cfg_args "             -handle        \$bgp_router$j\\\n"
                append route_cfg_args $route_cfg_args_common
                 #For bgpflowspec attributes
                if {$route_type=="bgpflowspecconfig"} {
                    append route_cfg_args "             -route_type        flow_spec\\\n"
                    set type12 ""
                    set typeOther ""
                    if {[info exists ::sth::hlapiGen::$bgp_config_handle\_$bgproute_handle\_attr(-componenttypes)]} {
                        set componenttypes [set ::sth::hlapiGen::$bgp_config_handle\_$bgproute_handle\_attr(-componenttypes)]
                        if { [string match *|* $componenttypes]} {
                            set componentList [split $componenttypes |]
                            foreach comp_type $componentList  {
                             switch -- [string tolower $comp_type] {
                                "type1_destination_prefix" {
                                    lappend type12 "bgpfstype1destinationprefix"
                                }
                                "type2_source_prefix" {
                                    lappend type12 "bgpfstype2sourceprefix"
                                }
                                "type4_port" {
                                    lappend typeOther "bgpfstype4port"
                                }
                                "type5_destination_port" {
                                    lappend typeOther "bgpfstype5destinationport"
                                }
                                "type6_source_port" {
                                    lappend typeOther "bgpfstype6sourceport"
                                }
                                "type10_packet_length" {
                                    lappend typeOther "bgpfstype10packetlength"
                                }
                                "type11_dscp_value" {
                                    lappend typeOther "bgpfstype11dscpvalue"
                                }
                            }
                            } 
                            
                        }
                    }
                    #For type 1 and 2
                    foreach obj_class $type12  {
                        if {[info exists ::sth::hlapiGen::$bgproute_handle\_obj($obj_class)]} {
                            set obj_handle [set ::sth::hlapiGen::$bgproute_handle\_obj($obj_class)]
                            append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgproute_handle $obj_handle $obj_class]
                        }
                    }
                    #For other types
                    foreach obj_parentclass $typeOther {
                        if {[info exists ::sth::hlapiGen::$bgproute_handle\_obj($obj_parentclass)]} {
                            set type_handle [set ::sth::hlapiGen::$bgproute_handle\_obj($obj_parentclass)]
                            
                            if {[info exists ::sth::hlapiGen::$type_handle\_obj(bgpfsoperatorvaluepair) ]} {
                                set obj_handle [set ::sth::hlapiGen::$type_handle\_obj(bgpfsoperatorvaluepair)]
                            } else {
                                set obj_handle [set ::sth::hlapiGen::$type_handle\_obj(bgpfsdscpopvaluepair)]
                            }
                            
                            #if obj_handle is more than 1
                            if { [llength $obj_handle] >1 } {
                                set obj_ele_handle ""
                                set element_flag 1
                                append element_cfg_args "set bgpRouteHandle \[keylget $hlt_ret_route handles\] \n"
                                for {set index 1} {$index < [llength $obj_handle]} {incr index} {
                                    lappend obj_ele_handle [lindex $obj_handle $index]
                                }
                                foreach objs $obj_ele_handle {
                                    set temp_element_cfg_args [::sth::hlapiGen::hlapi_gen_device_bgpelementconfig $obj_parentclass $type_handle $objs $hlt_ret_route]
                                    append element_cfg_args $temp_element_cfg_args
                                }
                            }
                            
                            set obj_handle [lindex $obj_handle 0]
                            switch -- [string tolower $obj_parentclass] {
                                "bgpfstype4port" {
                                    set obj_class "BgpFsOperatorValuePairT4"
                                }
                                "bgpfstype5destinationport" {
                                    set obj_class "BgpFsOperatorValuePairT5"
                                }
                                "bgpfstype6sourceport" {
                                    set obj_class "BgpFsOperatorValuePairT6"
                                }
                                "bgpfstype10packetlength" {
                                    set obj_class "BgpFsOperatorValuePairT10"
                                }
                                "bgpfstype11dscpvalue" {
                                    set obj_class "BgpFsDscpOpValuePair"
                                }
                            }
                            append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $type_handle $obj_handle $obj_class]
                        }
                    }
                    #when SubAfi is FLOW_SPEC_VPN attributes of BgpVpnRouteConfigFs will be  available
                    if {[info exists ::sth::hlapiGen::$bgp_config_handle\_$bgproute_handle\_attr(-subafi)]} {
                        set subafitype [set ::sth::hlapiGen::$bgp_config_handle\_$bgproute_handle\_attr(-subafi)]
                        if {[string match -nocase $subafitype "FLOW_SPEC_VPN"]} {
                            if {[info exists ::sth::hlapiGen::$bgproute_handle\_obj(bgpvpnrouteconfig)]} {
                                set obj_handle [set ::sth::hlapiGen::$bgproute_handle\_obj(bgpvpnrouteconfig)]
                                append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgproute_handle $obj_handle bgpvpnrouteconfigfs]
                            }
                        }
                    }
                    
                } elseif {$route_type=="bgpsrtepolicyconfig"} {
                    append route_cfg_args "             -route_type        srte\\\n"
                    foreach obj_class {bgpsrtepolicyattribute bgpsrtepolicytlvtypeconfig} {    
                        if {[info exists ::sth::hlapiGen::$bgproute_handle\_obj($obj_class)]} {
                            set obj_handle [set ::sth::hlapiGen::$bgproute_handle\_obj($obj_class)]
                            append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgproute_handle $obj_handle $obj_class]
                        }
                    }
                        if {[info exists ::sth::hlapiGen::$bgproute_handle\_obj(bgpsrtepolicysglistattribute)]} {
                            set obj_handle [set ::sth::hlapiGen::$bgproute_handle\_obj(bgpsrtepolicysglistattribute)]     ;# ::sth::hlapiGen::bgpsrtepolicyconfig1_obj - parray ::sth::hlapiGen::bgpsrtepolicyconfig1_obj - ::sth::hlapiGen::bgpsrtepolicyconfig1_obj(bgpsrtepolicyattribute) = bgpsrtepolicyattribute1, ::sth::hlapiGen::bgpsrtepolicyconfig1_obj(bgpsrtepolicysglistattribute) = bgpsrtepolicysglistattribute1, ::sth::hlapiGen::bgpsrtepolicyconfig1_obj(bgpsrtepolicytlvtypeconfig)   = bgpsrtepolicytlvtypeconfig1
                            #foreach objhandle $obj_handle {
                                     set objhandle [lindex $obj_handle 0]
				     append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgproute_handle $objhandle bgpsrtepolicysglistattribute]
                        #}
						
						
					}
                } else {
                    bgp_route_pre_process $route_cfg_args $route_type $bgproute_handle
                }
                #for the obj BgpVpnRouteConfig, Ipv4NetworkBlock and BgpVpnRouteConfig, Ipv6NetworkBlock , and BgpGlobalConfig can not be configured in the
                #basic function, since they are not under the BgpRouterConfig
                foreach obj_class {bgpvpnrouteconfig ipv4networkblock ipv6networkblock} {
                    if {[info exists ::sth::hlapiGen::$bgproute_handle\_obj($obj_class)]} {
                        set obj_handle [set ::sth::hlapiGen::$bgproute_handle\_obj($obj_class)]
                        append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgproute_handle $obj_handle $obj_class]
                    }
                }
                #config BgpGlobalConfig
                append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgp_config_handle $bgproute_handle $route_type]
                #hlapi_gen_device_basic $bgp_config_handle $route_type $route_mode $hlt_ret_route $route_cfg_args $first_time
                append route_cfg_args "\]\n"
                puts_to_file $route_cfg_args
                gen_status_info $hlt_ret_route "sth::emulation_bgp_route_config"
                incr j
                if {[llength $obj_handle] > 1 } {
                    #calling the new proc for configuration of segments
                    bgpsrtelistattrconfig $bgproute_handle $obj_handle $hlt_ret $hlt_ret_route
                }
                #Append bgp_route_element_config API 
                if {$element_flag==1} {  
                    #All the bgp_route_element_config for particular bgprouteconfighandle
                    puts_to_file $element_cfg_args 
                }
            }
            unset_table_obj_attr $route_type
           }
    }
    #puts_to_file $hlapi_script
}
#proc for the configuration of all the segments
proc ::sth::hlapiGen::bgpsrtelistattrconfig {bgproute_handle obj_handle hlt_ret hlt_ret_route} {

    set j 0
    set listattrchildren [stc::get [lindex $obj_handle 0] -children]
    if {$listattrchildren ne "" } {
        #calling a new proc for the configuration of segment types
        bgpsrtesegmenttypconfig bgproute_handle $listattrchildren [lindex $obj_handle 0] $hlt_ret $hlt_ret_route
    }
    set obj_handle_length [llength $obj_handle]
    set bgplistattr [lrange $obj_handle 1 [expr $obj_handle_length - 1]]
    foreach bgplist $bgplistattr {
        puts_to_file "set bgp_policyconfig_handle \[keylget $hlt_ret_route handles\]"
        set hlt_ret_route $hlt_ret\_segment_list$j
        append route_cfg_args "      set $hlt_ret_route \[sth::emulation_bgp_route_config\\\n"
        append route_cfg_args "             -route_handle       \$bgp_policyconfig_handle\\\n"
        append route_cfg_args "             -mode        add\\\n"
        append route_cfg_args "             -route_type        srte\\\n"
        append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgproute_handle $bgplist bgpsrtepolicysglistattribute]
        append route_cfg_args "\]\n"
        puts_to_file $route_cfg_args
        gen_status_info $hlt_ret_route "sth::emulation_bgp_route_config"
        set route_cfg_args ""
        set segment_type [stc::get $bgplist -children]
        if {$segment_type ne "" } {
            #calling a new proc for the configuration of segment types
            bgpsrtesegmenttypconfig bgproute_handle $segment_type $bgplist $hlt_ret $hlt_ret_route
        }
        incr j
    }
        
}


#proc for the configuration of segment types
proc ::sth::hlapiGen::bgpsrtesegmenttypconfig {bgproute_handle segment_type bgplist hlt_ret hlt_ret_route} {

    set j 0
    puts_to_file "set bgp_policy_seg_list_handle \[keylget $hlt_ret_route bgp_srte_segment_list_handles\]"
    foreach seg_type $segment_type {
        set temp [regexp -- {^bgpsrtepolicysegmenttype+[1-8]?} $seg_type class]
        set hlt_ret_route $hlt_ret\_segment_list_sub_tlv$j
        append route_cfg_args "      set $hlt_ret_route \[sth::emulation_bgp_route_config\\\n"
        append route_cfg_args "             -route_handle       \$bgp_policy_seg_list_handle\\\n"
        append route_cfg_args "             -mode        add\\\n"
        append route_cfg_args "             -route_type        srte\\\n"
        append route_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_config $bgplist $seg_type $class]
        append route_cfg_args "\]\n"
        puts_to_file $route_cfg_args
        gen_status_info $hlt_ret_route "sth::emulation_bgp_route_config"
        set route_cfg_args ""
        incr j
        set class bgpsrtepolicysegmenttype
    }
}

#Helper function for bgp route element function 
proc ::sth::hlapiGen::hlapi_gen_device_bgpelementconfig {obj_parentclassArg type_handleArg obj_handleArg hlt_ret_routeArg} {
    set ret_element_cfg_args ""
    
    append ret_element_cfg_args "      set bgpElementHandle \[sth::emulation_bgp_route_element_config\\\n"
    append ret_element_cfg_args "             -handle        \$bgpRouteHandle\\\n"
    append ret_element_cfg_args "             -mode        add\\\n"
    
    switch -- [string tolower $obj_parentclassArg] {
                                "bgpfstype4port" {
                                    set obj_class "BgpFsOperatorValuePairT4"
                                    append ret_element_cfg_args "             -element_type        fs_type4\\\n"
                                }
                                "bgpfstype5destinationport" {
                                    set obj_class "BgpFsOperatorValuePairT5"
                                    append ret_element_cfg_args "             -element_type        fs_type5\\\n"
                                }
                                "bgpfstype6sourceport" {
                                    set obj_class "BgpFsOperatorValuePairT6"
                                    append ret_element_cfg_args "             -element_type        fs_type6\\\n"
                                }
                                "bgpfstype10packetlength" {
                                    set obj_class "BgpFsOperatorValuePairT10"
                                    append ret_element_cfg_args "             -element_type        fs_type10\\\n"
                                }
                                "bgpfstype11dscpvalue" {
                                    set obj_class "BgpFsDscpOpValuePair"
                                    append ret_element_cfg_args "             -element_type        fs_type11\\\n"
                                }
                            }
    append ret_element_cfg_args [config_obj_attr ::sth::Bgp:: emulation_bgp_route_element_config $type_handleArg $obj_handleArg $obj_class]
    append ret_element_cfg_args "\]\n"
    append ret_element_cfg_args [::sth::hlapiGen::gen_status_info_without_puts bgpElementHandle "sth::emulation_bgp_route_element_config"]
    return $ret_element_cfg_args
}



#--------------------------------------------------------------------------------------------------------#
# pre-process the special args in the emulation_bgp_config function
#input:     cfg_args    => the special args and value pair
#           device      => the device handle on which these special arg will be configured
#output:   the special args pair value will be appended to the cfg_args     
proc ::sth::hlapiGen::bgp_router_pre_process {cfg_args device} {
    upvar cfg_args cfg_args_local
    
    #pre-process the tunnel handle, to config this, need to call the gre config function
    if {[info exists sth::hlapiGen::$device\_obj(greif)]} {
        
        hlapi_gen_device_greconfig $device greif create gre_ret $cfg_args_local
        append cfg_args_local "                       -tunnel_handle              \$gre_ret\\\n"
    }
    #pre-process the bgpglobalconfig
    set project [stc::get $device -parent]
    set bgp_global_config [stc::get $project -children-BgpGlobalConfig]
    ::sth::sthCore::InitTableFromTCLList $::sth::Bgp::bgpTable
    get_attr $bgp_global_config $bgp_global_config
    append cfg_args_local [config_obj_attr ::sth::Bgp:: emulation_bgp_config $bgp_global_config $bgp_global_config bgpglobalconfig]
    
    # staggered_start_enable need to be set to 1 when the staggered_start_time is in the config list
    if {[lsearch $cfg_args_local {*staggered_start_time*}] > -1} {
        append cfg_args_local "                 -staggered_start_enable             1\\\n"
    }
    #pre_process the option under BgpAuthenticationParams
    set bgp_router_handle [set sth::hlapiGen::$device\_obj(bgprouterconfig)]
    if {[info exists ::sth::hlapiGen::$bgp_router_handle\_obj(bgpauthenticationparams)]} {
        set obj_handle [set ::sth::hlapiGen::$bgp_router_handle\_obj(bgpauthenticationparams)]
        append cfg_args_local [config_obj_attr ::sth::Bgp:: emulation_bgp_config $bgp_router_handle $obj_handle bgpauthenticationparams]
    }
    
    #pre_process the option under BgpCustomPdu    
    if {[info exists ::sth::hlapiGen::$bgp_router_handle\_obj(bgpcustompdu)]} {
        set newstr "			-custom_pdus			"
        set obj_handles [set ::sth::hlapiGen::$bgp_router_handle\_obj(bgpcustompdu)]
        foreach obj_handle $obj_handles {            
            set pdu [set ::sth::hlapiGen::$bgp_router_handle\_$obj_handle\_attr(-pdu)]            
            set i 0
            foreach dec $pdu {
                set toHex [format %02x $dec]
                lset pdu $i $toHex
                incr i
            }
            append newstr "{" $pdu "} "            
        }
        append cfg_args_local $newstr "\\\n"        
    }
    #pre-process local_as4 remote_as4 Enable4ByteAsNum AsNum4Byte Enable4ByteDutAsNum DutAsNum4Byte
    if {[regexp -nocase "true" [set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-enable4byteasnum)]]} {
        set local_as4 [set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-asnum4byte)]
        set local_as4 [join [split $local_as4 "."] ":"] 
        set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-asnum4byte) $local_as4
    } else {
        set sth::Bgp::emulation_bgp_config_stcobj(local_as4) "_none_"
    }
    
     if {[regexp -nocase "true" [set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-enable4bytedutasnum)] ]} {
        set remote_as4 [set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-dutasnum4byte)]
        set remote_as4 [join [split $remote_as4 "."] ":"]
        set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-dutasnum4byte) $remote_as4
    } else {
        set sth::Bgp::emulation_bgp_config_stcobj(remote_as4) "_none_"
    }
    #pre-process ipv4_mpls_nlri, ipv4_mpls_vpn_nlri,ipv4_multicast_nlri,ipv4_unicast_nlri,ipv6_mpls_nlri,ipv6_mpls_vpn_nlri,
    #ipv6_multicast_nlri, ipv6_unicast_nlri,vpls_nlri
    #use afi and subAfi under BgpRouterConfig's chidren BgpCapabilityConfig 
    set bgp_capabilities [stc::get $bgp_router_handle -children-BgpCapabilityConfig]
    foreach bgp_capability $bgp_capabilities {
        set afi [stc::get $bgp_capability -afi]
        set sub_afi [stc::get $bgp_capability -subAfi]
	set option "afi $afi subAfi $sub_afi"
	array set stcAttrMap {    {afi 1 subAfi 1} -ipv4_unicast_nlri  \
			                  {afi 1 subAfi 2} -ipv4_multicast_nlri  \
                              {afi 1 subAfi 3} -ipv4_unicast_multicast_nlri  \
			                  {afi 1 subAfi 4} -ipv4_mpls_nlri  \
                              {afi 1 subAfi 5} -ipv4_multicast_vpn_nlri  \
			                  {afi 1 subAfi 65} -ipv4_vpls_nlri  \
                              {afi 1 subAfi 66} -ipv4_mdt_nlri  \
                              {afi 1 subAfi 70} -ipv4_e_vpn_nlri  \
                              {afi 1 subAfi 71} -ipv4_ls_non_vpn_nlri  \
                              {afi 1 subAfi 128} -ipv4_mpls_vpn_nlri  \
                              {afi 1 subAfi 132} -ipv4_rt_constraint_nlri  \
                              {afi 1 subAfi 133} -ipv4_flow_spec_nlri  \
                              {afi 1 subAfi 134} -ipv4_flow_spec_vpn_nlri  \
			                  {afi 2 subAfi 1} -ipv6_unicast_nlri  \
			                  {afi 2 subAfi 2} -ipv6_multicast_nlri  \
                              {afi 2 subAfi 3} -ipv6_unicast_multicast_nlri  \
			                  {afi 2 subAfi 4} -ipv6_mpls_nlri  \
                              {afi 2 subAfi 5} -ipv6_multicast_vpn_nlri  \
                              {afi 2 subAfi 65} -ipv6_vpls_nlri  \
                              {afi 2 subAfi 66} -ipv6_mdt_nlri  \
                              {afi 2 subAfi 70} -ipv6_e_vpn_nlri  \
                              {afi 2 subAfi 71} -ipv6_ls_non_vpn_nlri  \
                              {afi 2 subAfi 128} -ipv6_mpls_vpn_nlri  \
                              {afi 2 subAfi 132} -ipv6_rt_constraint_nlri  \
                              {afi 2 subAfi 133} -ipv6_flow_spec_nlri  \
                              {afi 2 subAfi 134} -ipv6_flow_spec_vpn_nlri  \
			                  {afi 25 subAfi 1}  -vpls_unicast_nlri  \
			                  {afi 25 subAfi 2} -vpls_multicast_nlri  \
                              {afi 65 subAfi 3} -vpls_unicast_multicast_nlri  \
			                  {afi 25 subAfi 4} -vpls_mpls_nlri  \
                              {afi 25 subAfi 5} -vpls_multicast_vpn_nlri  \
                              {afi 25 subAfi 65} -vpls_nlri  \
                              {afi 25 subAfi 66} -vpls_mdt_nlri  \
                              {afi 25 subAfi 70} -vpls_e_vpn_nlri  \
                              {afi 25 subAfi 71} -vpls_ls_non_vpn_nlri  \
                              {afi 25 subAfi 128} -vpls_mpls_vpn_nlri  \
                              {afi 25 subAfi 132} -vpls_rt_constraint_nlri  \
                              {afi 25 subAfi 133} -vpls_flow_spec_nlri  \
                              {afi 25 subAfi 134} -vpls_flow_spec_vpn_nlri  \
                              {afi 196 subAfi 1} -kompella_vpls_unicast_nlri  \
			                  {afi 196 subAfi 2} -kompella_vpls_multicast_nlri  \
                              {afi 196 subAfi 3} -kompella_vpls_unicast_multicast_nlri  \
			                  {afi 196 subAfi 4} -kompella_vpls_mpls_nlri  \
                              {afi 196 subAfi 5} -kompella_vpls_multicast_vpn_nlri  \
                              {afi 196 subAfi 65} -kompella_vpls_vpls_nlri  \
                              {afi 196 subAfi 66} -kompella_vpls_mdt_nlri  \
                              {afi 196 subAfi 70} -kompella_vpls_e_vpn_nlri  \
                              {afi 196 subAfi 71} -kompella_vpls_ls_non_vpn_nlri  \
                              {afi 196 subAfi 128} -kompella_vpls_mpls_vpn_nlri  \
                              {afi 196 subAfi 132} -kompella_vpls_rt_constraint_nlri  \
                              {afi 196 subAfi 133} -kompella_vpls_flow_spec_nlri  \
                              {afi 196 subAfi 134} -kompella_vpls_flow_spec_vpn_nlri  \
                              {afi 16388 subAfi 1} -link_unicast_nlri  \
			                  {afi 16388 subAfi 2} -link_multicast_nlri  \
                              {afi 16388 subAfi 3} -link_unicast_multicast_nlri  \
			                  {afi 16388 subAfi 4} -link_mpls_nlri  \
                              {afi 16388 subAfi 5} -link_multicast_vpn_nlri  \
                              {afi 16388 subAfi 65} -link_vpls_nlri  \
                              {afi 16388 subAfi 66} -link_mdt_nlri  \
                              {afi 16388 subAfi 70} -link_e_vpn_nlri  \
                              {afi 16388 subAfi 71} -link_ls_non_vpn_nlri  \
                              {afi 16388 subAfi 128} -link_mpls_vpn_nlri  \
                              {afi 16388 subAfi 132} -link_rt_constraint_nlri  \
                              {afi 16388 subAfi 133} -link_flow_spec_nlri  \
                              {afi 16388 subAfi 134} -link_flow_spec_vpn_nlri  \
                              }
	    if {[info exists stcAttrMap($option)]} {
	   
	        append cfg_args_local  "                $stcAttrMap($option)                 1\\\n" 
	    }
	
        
    }
    
    
    #pre-process ip_stack_version
    if {[info exists sth::hlapiGen::$device\_obj(ipv4if)] && [info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
        append cfg_args_local "                -ip_stack_version                 4_6\\\n" 
    } elseif {[info exists sth::hlapiGen::$device\_obj(ipv4if)]} {
        append cfg_args_local "                -ip_stack_version                 4\\\n" 
    } else {
        append cfg_args_local "                -ip_stack_version                 6\\\n"
    }
    #pre-process staggered_start_enable local_router_id_enable
    
    #pre-process the gateway step... for scaling test
    if {$::sth::hlapiGen::scaling_test} {
        array set update_param_list "next_hop_ip_step Gateway.Step next_hop_ipv6_step Gateway.Step"
        foreach arg [array names update_param_list] {
            set sth::Bgp::emulation_bgp_config_stcattr($arg) $update_param_list($arg)
        }
        array unset update_param_list
    }
    
    if {[set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-dutipv4addr)] == "null" && [info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        #if current dutipaddr is null, set the gateway as dutipaddr
        set ipv4if [set ::sth::hlapiGen::$device\_obj(ipv4if)]
        set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-dutipv4addr) [set ::sth::hlapiGen::$device\_$ipv4if\_attr(-gateway)]
    }
    if {[set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-dutipv6addr)] == "null" && [info exists ::sth::hlapiGen::$device\_obj(ipv6if)]} {
        #if current dutipaddr is null, set the gateway as dutipaddr
        set ipv6iflist [set ::sth::hlapiGen::$device\_obj(ipv6if)]
        foreach ipv6if $ipv6iflist {
            set addr [set ::sth::hlapiGen::$device\_$ipv6if\_attr(-address)]
            if {![regexp -nocase "FE80" $addr]} {
                break				
            }
        }
        set ::sth::hlapiGen::$device\_$bgp_router_handle\_attr(-dutipv6addr) [set ::sth::hlapiGen::$device\_$ipv6if\_attr(-gateway)]
    }
    
}


#--------------------------------------------------------------------------------------------------------#
# pre-process the special args in the emulation_bgp_config function
#input:     route_cfg_args      => the special args and value pair
#           class               => the class name, it can be either bgpipv4routeconfig or bgpipv6routeconfig
#           bgproute_handle     => the bgp route handle
#output:   the special args pair value will be appended to the cfg_args     
proc ::sth::hlapiGen::bgp_route_pre_process {route_cfg_args class bgproute_handle} {
    upvar route_cfg_args cfg_args_local
    
    #pre-handle the options:  num_routes, prefix, prefix_step
    #pre-handle the stcobj, need to check if it is ipv4 or ipv6, the stcobj need to pre-process defined in the table are:
    #BgpIpv4RouteConfig, NetworkBlock, BgpIpv4VplsConfig, 
    foreach arg [array names ::sth::Bgp::emulation_bgp_route_config_stcobj] {
        if {[regexp "bgpipv4routeconfig" $class]} {
            #this is ipv4 route
            if {[regexp {^NetworkBlock$} $::sth::Bgp::emulation_bgp_route_config_stcobj($arg)]} {
                set ::sth::Bgp::emulation_bgp_route_config_stcobj($arg) "Ipv4NetworkBlock"
            }
            
            if {[regexp {^BgpIpv6RouteConfig$} $::sth::Bgp::emulation_bgp_route_config_stcobj($arg)]} {
                set ::sth::Bgp::emulation_bgp_route_config_stcobj($arg) "BgpIpv4RouteConfig"
            }
            if {[regexp {^BgpIpv6VplsConfig$} $::sth::Bgp::emulation_bgp_route_config_stcobj($arg)]} {
                set ::sth::Bgp::emulation_bgp_route_config_stcobj($arg) "BgpIpv4VplsConfig"
            }
            
            #pre-process netmask PrefixLength
            if {[regexp "netmask" $arg]} {
                set network_block [set sth::hlapiGen::$bgproute_handle\_obj(ipv4networkblock)]
                set prefix_len [set sth::hlapiGen::$bgproute_handle\_$network_block\_attr(-prefixlength)]
                set netmask [::sth::sthCore::prefixLengthToIpMask $prefix_len 4]
                set sth::hlapiGen::$bgproute_handle\_$network_block\_attr(-prefixlength) $netmask
            }
            
        } else {
            #this is IPv6 route
            if {[regexp {^NetworkBlock$} $::sth::Bgp::emulation_bgp_route_config_stcobj($arg)]} {
                set ::sth::Bgp::emulation_bgp_route_config_stcobj($arg) "Ipv6NetworkBlock"
            }
            if {[regexp {^BgpIpv4RouteConfig$} $::sth::Bgp::emulation_bgp_route_config_stcobj($arg)]} {
                set ::sth::Bgp::emulation_bgp_route_config_stcobj($arg) "BgpIpv6RouteConfig"
            }
            if {[regexp {^BgpIpv4VplsConfig$} $::sth::Bgp::emulation_bgp_route_config_stcobj($arg)]} {
                set ::sth::Bgp::emulation_bgp_route_config_stcobj($arg) "BgpIpv6VplsConfig"
            }
        }
    }
    
    
    #pre-handle as_path
    set as_path [stc::get $bgproute_handle -AsPath]
    if {![regexp "^$" $as_path]} {
        set as_path [split $as_path " "]
        set as_path_type [stc::get $bgproute_handle -AsPathSegmentType]
        if {[llength $as_path] > 1} {
            set as_path [join $as_path ,]
        }
        switch -- [string tolower $as_path_type] {
            "set" {
                set as_path_value [join [list "as_set" $as_path] :]
            }
            "sequence" {
                set as_path_value [join [list "as_seq" $as_path] :]
            }
            "confed_seq" {
                set as_path_value [join [list "as_confed_seq" $as_path] :]
            }
            "confed_set" {
                set as_path_value [join [list "as_confed_set" $as_path] :]
            }
        }
        append cfg_args_local "                -as_path            $as_path_value\\\n"
    }
    
        
    #pre-handle communities and communities_enable
    set community [stc::get $bgproute_handle -Community]
    if {![regexp {^$} $community]} {
        #need to do more research about how to configure the community in the HLTAPI.
        #append cfg_args_local "                -communities_enable            1\\\n"
        #append cfg_args_local "                -communities                   as_id:$community\\\n"
        
    }
    #pre-handle target_type target target_assign
    set bgpvpnroute_handle [stc::get $bgproute_handle -children-BgpVpnRouteConfig ] 
    set target [stc::get $bgpvpnroute_handle -RouteTarget]
    set target_value [lindex [split $target ":"] 0]
    set target_assign_value [lindex [split $target ":"] 1]
    if {[regexp {^[0-9]+$} $target_value]} {
        set target_type_value "as"
    } else {
        set target_type_value "ip"
    }
    append cfg_args_local "                -target_type             $target_type_value\\\n"
    append cfg_args_local "                -target                  $target_value\\\n"
    append cfg_args_local "                -target_assign           $target_assign_value\\\n"
    
    #pre-handle rd_type rd_admin_step rd_admin_value rd_assign_step rd_assign_value
    set rd_admin_value [lindex [split [stc::get $bgpvpnroute_handle -RouteDistinguisher] :] 0]
    set rd_assign_value [lindex [split [stc::get $bgpvpnroute_handle -RouteDistinguisher] :] 1]
    
    set rd_admin_step [lindex [split [stc::get $bgpvpnroute_handle -RouteDistinguisherStep] :] 0]
    set rd_assign_step [lindex [split [stc::get $bgpvpnroute_handle -RouteDistinguisherStep] :] 1]
    
    if {[regexp {^[0-9]+$} $rd_admin_value]} {
        set rd_type 0 
    } else {
        set rd_type 1
    }
    foreach arg {rd_type rd_admin_step rd_admin_value rd_assign_step rd_assign_value} {
        append cfg_args_local "                -$arg                 [set $arg]\\\n"
    }

    
    #pre-handle next_hop_ip_version and next_hop_set_mode
    if {[regexp "bgpipv4routeconfig" $class]} {
        set ip_version 4
    } else {
        set ip_version 6
    }
    append cfg_args_local "                -next_hop_ip_version                 $ip_version\\\n"
    append cfg_args_local "                -next_hop_set_mode                 manual\\\n"
    
    #pre-handle cluster_list_enable and originator_id_enable
    #unless originator_id is not null and cluster_list is not empty, then it will be enabled
    set cluster_id [stc::get $bgproute_handle -clusteridlist]
    if {![regexp -nocase {^$} $cluster_id]} {
        append cfg_args_local "                -cluster_list_enable                 1\\\n"
    }
    set originator_id [stc::get $bgproute_handle -OriginatorId]
    if {![regexp -nocase {null} $originator_id]} {
        append cfg_args_local "                -originator_id_enable                 1\\\n"
    }
    
    #pre-handle ipv4_mpls_nlri, ipv4_mpls_vpn_nlri,ipv4_multicast_nlri,ipv4_unicast_nlri,ipv6_mpls_nlri,ipv6_mpls_vpn_nlri,
    #ipv6_multicast_nlri, ipv6_unicast_nlri,vpls_nlri
    #use afi and subAfi under BgpRouterConfig and BgpIpv4RouteConfig 
    set sub_afi [stc::get $bgproute_handle -RouteSubAfi]
    if {$ip_version == 4} {
        switch -- [string tolower $sub_afi] {
            "labeled_ip" {
                set arg "ipv4_mpls_nlri"
            }
            "vpn" {
                set arg "ipv4_mpls_vpn_nlri"
            }
            "unicast" {
                set arg "ipv4_unicast_nlri"
            }
            "multicast" {
                set arg "ipv4_multicast_nlri"
            }
            default {
                set arg "none"
            }
        }
    } else {
        switch -- [string tolower $sub_afi] {
            "labeled_ip" {
                set arg "ipv6_mpls_nlri"
            }
            "vpn" {
                set arg "ipv6_mpls_vpn_nlri"
            }
            "unicast" {
                set arg "ipv6_unicast_nlri"
            }
            "multicast" {
                set arg "ipv6_multicast_nlri"
            }
            default {
                set arg "none"
            }
        }
    }
    if {![regexp {none} $arg]} {
        append cfg_args_local "                -$arg                 1\\\n"
    }
    
    #pre-process aggregator
    set asn [stc::get $bgproute_handle -AggregatorAs]
    set aggregator [stc::get $bgproute_handle -AggregatorIp]
    if {![regexp "null" $aggregator] && ![regexp "^$" $asn]} {
        append cfg_args_local "                -aggregator                 $asn:$aggregator\\\n"
    }
}

proc ::sth::hlapiGen::hlapi_gen_device_bfdconfig {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    set table_name "::sth::bfd::bfdTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_bfd_config"
    
    if {$first_time != 1} {
        #set the control and results function to none
        set ::sth::hlapiGen::hlapi_gen_ctrlConvertFunc($class) "_none_"
        set ::sth::hlapiGen::hlapi_gen_resultConvertFunc($class) "_none_"
        return
    }
    
    #the step attributes have values in the table file, so we need to change the stcattr in the scaling test
    if {$::sth::hlapiGen::scaling_test} {
        array set stepattrlist "intf_ip_addr_step Address intf_ipv6_addr_step Address remote_ip_addr_step StartIpList remote_ipv6_addr_step StartIpList\
            local_mac_addr_step SourceMac vlan_id_step1 VlanId vlan_id_step2 VlanId gateway_ip_addr_step Gateway gateway_ipv6_addr_step Gateway"
        foreach param [array name stepattrlist] {
            set $name_space$cmd_name\_stcattr($param) $stepattrlist($param)\.step
        }
        set router_paramlist "count"
        regsub {\d+$} $device "" update_obj
        foreach router_param $router_paramlist {
            set ::sth::bfd::$cmd_name\_stcobj($router_param) "$update_obj"
        }
        array unset stepattrlist
    }
    
    set bfd_router_config_hdl  [set ::sth::hlapiGen::$device\_obj($class)]
    if {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        set ip_version IPv4
    } elseif {[info exists ::sth::hlapiGen::$device\_obj(ipv6if)]} {
        set ip_version IPv6
    }
    append cfg_args "-ip_version $ip_version\\\n"
    
    #process vlan_id_mode1/2 and vlan_ether_type1/2
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        foreach vlanif $vlanifs {
            set tpid [set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid)]
            set tpid_update vlan_tag_[format "0x%04x" $tpid]
            set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid) $tpid_update
            
            if {!$::sth::hlapiGen::scaling_test} {
                # vlan id step and vlan id mode is handled differently in scaling mode
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
    }

    if {[info exists ::sth::hlapiGen::$bfd_router_config_hdl\_obj(bfdipv4controlplaneindependentsession)]} {
        set bfd_control_plane_class bfdipv4controlplaneindependentsession
        set ipnetwork_class ipv4networkblock
    } elseif {[info exists ::sth::hlapiGen::$bfd_router_config_hdl\_obj(bfdipv6controlplaneindependentsession)]} {
        set bfd_control_plane_class bfdipv6controlplaneindependentsession
        set ipnetwork_class ipv6networkblock
    }
    if {[info exists bfd_control_plane_class]} {
        set bfd_controlplane_session_handle [set ::sth::hlapiGen::$bfd_router_config_hdl\_obj($bfd_control_plane_class)]
        if {[set ::sth::hlapiGen::$bfd_router_config_hdl\_$bfd_controlplane_session_handle\_attr(-enablemydiscriminator)] == "true"} {
            set mydiscriminator_value [set ::sth::hlapiGen::$bfd_router_config_hdl\_$bfd_controlplane_session_handle\_attr(-mydiscriminator)]
            set mydiscriminatorincrement_value [set ::sth::hlapiGen::$bfd_router_config_hdl\_$bfd_controlplane_session_handle\_attr(-mydiscriminatorincrement)]
            append cfg_args "-session_discriminator $mydiscriminator_value\\\n"
            append cfg_args "-session_discriminator_step $mydiscriminatorincrement_value\\\n"
        }
        set ipnetwork_hdl [set ::sth::hlapiGen::$bfd_controlplane_session_handle\_obj($ipnetwork_class)]
        set ipaddrincr [set ::sth::hlapiGen::$bfd_controlplane_session_handle\_$ipnetwork_hdl\_attr(-addrincrement)]
        if {[regexp -nocase "ipv4networkblock" $ipnetwork_class]} {
            set ::sth::hlapiGen::$bfd_controlplane_session_handle\_$ipnetwork_hdl\_attr(-addrincrement) [::sth::hlapiGen::intToIpv4Address $ipaddrincr]
        } else {
            set mask [set ::sth::hlapiGen::$bfd_controlplane_session_handle\_$ipnetwork_hdl\_attr(-prefixlength)]
            set ::sth::hlapiGen::$bfd_controlplane_session_handle\_$ipnetwork_hdl\_attr(-addrincrement) [::sth::hlapiGen::intToIpv6Address $ipaddrincr $mask]
        }
        append cfg_args [config_obj_attr $name_space $cmd_name $bfd_controlplane_session_handle $ipnetwork_hdl $ipnetwork_class]
    }
    
    hlapi_gen_device_basic $device $class create $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::hlapi_gen_device_capturefilter {device class mode hlt_ret cfg_args first_time} {
    set cfg_args ""
    set table_name "::sth::packetCapture::PacketCaptureTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "packet_config_pattern"
    set j 0
    
    set captureFilter [set sth::hlapiGen::$device\_obj($class)]
    set obj_handles [set sth::hlapiGen::$captureFilter\_obj(captureanalyzerfilter)]
    
    foreach obj_handle $obj_handles {
        # for now, only support selected filters with offset/mask
        if { "false" == [set sth::hlapiGen::$captureFilter\_$obj_handle\_attr(-isselected)] ||
             "" == [set sth::hlapiGen::$captureFilter\_$obj_handle\_attr(-mask)]} {
            continue
        }
        if {![info exists sth::hlapiGen::device_ret($obj_handle)]} {
            set sth::hlapiGen::device_ret($obj_handle) $hlt_ret\_pcp_$j
        }
        set port_handle [stc::get $device -parent]
        set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
        set    cfg_args "                   -port_handle               $port_handle_new\\\n"        
        append cfg_args [config_obj_attr $name_space $cmd_name $captureFilter $obj_handle CaptureAnalyzerFilter]
        # adjust some values
        update_field_value cfg_args pattern_mask
        update_field_value cfg_args pattern_match
        set hlapi_script [hlapi_gen_device_basic_without_puts $device $class add $sth::hlapiGen::device_ret($obj_handle) $cfg_args $first_time]
        puts_to_file $hlapi_script        
        gen_status_info $sth::hlapiGen::device_ret($obj_handle) "sth::$cmd_name"
        incr j
    }    
}
# udpate the value of a specified field in a string
# 1 convert decimal to hex
# 2 remove inner spaces
# Examples:
#   set inin "-operator                                         AND \\\n"
#   append inin        "-pattern_offset                                   30 \\\n"
#   append inin        "-pattern_mask                                     \"255 255 255 255\" \\\n"
#   append inin        "-pattern_match                                    192 \\\n"
#   updateFieldValue inin pattern_mask
# the line will be : 
#   -pattern_mask                                     FFFFFFFF\

proc ::sth::hlapiGen::update_field_value { cfg_args field } {
    upvar $cfg_args my_cfg_args
    set value ""
    set pattern "(-$field\\s+)(\[0-9 \"\]*)"
    regexp -nocase -- $pattern $my_cfg_args "" attr value
    if { "" != $value } {
        set value [string trim $value " \""]
        set hex ""
        foreach dec $value {
            append hex [format "%02X" $dec] 
        }
        regsub -nocase -- $pattern $my_cfg_args "$attr$hex" my_cfg_args
    }
}

proc ::sth::hlapiGen::hlapi_gen_device_dhcpv4_wildcard_setting {id_name id} {
            set wildcard_id ""
		    set wildcard_id_suffix ""
		    set wildcard_id_suffix_count ""
		    set wildcard_id_suffix_step ""
		    set wildcard_id_suffix_repeat ""
		    set wildcard_id_suffix_zeropad ""
			set cfgWildcard ""
		    if {[regexp -nocase {^@[x|\$]\([\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*\)$} $id {} wildcard_id_suffix wildcard_id_suffix_count wildcard_id_suffix_step wildcard_id_suffix_zeropad wildcard_id_suffix_repeat] } {
                incr wildcard_id_suffix_repeat
		    } elseif {[regexp -nocase {^@[x|\$]\([\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*\)$} $id {} wildcard_id_suffix wildcard_id_suffix_count wildcard_id_suffix_step wildcard_id_suffix_zeropad] } {
		        set wildcard_id_suffix_repeat 1
		    } elseif {[regexp -nocase {^@[x|\$]\([\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*\)$} $id {} wildcard_id_suffix wildcard_id_suffix_count wildcard_id_suffix_step] } {
                set wildcard_id_suffix_repeat 1
			    set wildcard_id_suffix_zeropad 1
		    } elseif {[regexp -nocase {^@[x|\$]\([\s]*(\d+)[\s]*,[\s]*(\d+)[\s]*\)$} $id {} wildcard_id_suffix wildcard_id_suffix_count] } {
                set wildcard_id_suffix_repeat 1
		    	set wildcard_id_suffix_zeropad 1
	    		set wildcard_id_suffix_step 1
		    }  elseif {[regexp -nocase {^@[x|\$]\((\d+)\)$} $id {} wildcard_id_suffix] } {
                set wildcard_id_suffix_repeat 1
		    	set wildcard_id_suffix_zeropad 1
		    	set wildcard_id_suffix_step 1
	    		set wildcard_id_suffix_count 1
		    } else {
			     append cfgWildcard "                    -$id_name\_id                          $id\\\n"
				 return $cfgWildcard
			    } 
		    if {[regexp -nocase {(^\d+)(\d$)} $wildcard_id_suffix {} wildcard_id wildcard_id_suffix ]} {
		    } else {
		            set wildcard_id 0
				}
			if {$wildcard_id_suffix_repeat == 0} {
			    set wildcard_id_suffix_repeat 1
			}
		    append cfgWildcard "			            -$id_name\_id			                 $wildcard_id\\\n"
		    append cfgWildcard "			            -$id_name\_id_suffix			         $wildcard_id_suffix\\\n"
		    append cfgWildcard "			            -$id_name\_id_suffix_count			     $wildcard_id_suffix_count\\\n"		
		    append cfgWildcard "			            -$id_name\_id_suffix_step			     $wildcard_id_suffix_step\\\n"
		    append cfgWildcard "			            -$id_name\_id_suffix_repeat			     $wildcard_id_suffix_repeat\\\n"
		    return $cfgWildcard
	}

proc ::sth::hlapiGen::hlapi_gen_device_dhcpv4 {device class mode hlt_ret cfg_args first_time} {
    #config dhcpv4portconfig
    set port [stc::get $device -affiliationport-Targets]
    set dhcpv4portconfighandle [stc::get $port -children-dhcpv4portconfig]
    set dhcpv4portconfighandle [lindex $dhcpv4portconfighandle 0]
    set table_name "::sth::Dhcp::dhcpTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_dhcp_config"
    set port_handle $port 
    #get ip version.
    regexp {([4|6])} $class match ipversion
    if {![regexp -nocase $port [array names ::sth::hlapiGen::dhcpv4portconfigured]]} {
        append hlt_ret_port $hlt_ret "port"

            append hlapi_script "			-ip_version			    $ipversion\\\n"
            set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
            append hlapi_script "			-port_handle	            $port_handle_new\\\n"
            #handle msgtimeout
            if {[info exists sth::hlapiGen::$port\_$dhcpv4portconfighandle\_attr(-msgtimeout)]} {
                set tmpvalue [set sth::hlapiGen::$port\_$dhcpv4portconfighandle\_attr(-msgtimeout)]
                set sth::hlapiGen::$port\_$dhcpv4portconfighandle\_attr(-msgtimeout) [append tmpvalue "000"]
            }           


            hlapi_gen_device_basic $port dhcpv4portconfig create $hlt_ret_port $hlapi_script 1
        set ::sth::hlapiGen::dhcpv4portconfigured($port) $hlt_ret_port
    }

    set hlapi_script ""  

    set cmd_name "emulation_dhcp_group_config"
    if {$first_time == 1} {
        puts_to_file "\nset dhcp_handle \[keylget $::sth::hlapiGen::dhcpv4portconfigured($port) handles\]\n"
    }
    #maybe need change the stcobj of num_sessions
    if {[regexp -nocase "host" $device]} {
        set $name_space$cmd_name\_stcobj(num_sessions) "Host"
    }
    if {[regexp -nocase "router" $device]} {
        set $name_space$cmd_name\_stcobj(num_sessions) "Router"
    }
    
    #get the encap info
    set encap [::sth::hlapiGen::getencap $device]
    append hlapi_script "			-dhcp_range_ip_type			    $ipversion\\\n"
    append hlapi_script "			-encap			    $encap\\\n"
    append hlapi_script "			-gateway_addresses			    1\\\n"
    #append hlapi_script "			-num_sessions			    1\\\n"
    append hlapi_script $cfg_args
	
    set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
    if {$first_time == 1} {
        append hlapi_script "			-handle        \$dhcp_handle\\\n"
    }
    #process the circuit_id and the remote_id, if they are not enabled should not output the default value which is appeared in the STC data model
    set dhcpv4block [set sth::hlapiGen::$device\_obj(dhcpv4blockconfig)]
    if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablecircuitid)]} {
        set circuitid_enable [set sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablecircuitid)]
        if {[regexp -nocase "false" $circuitid_enable]} {
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-circuitid)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-circuitid)
            }
        } else {
		    set  wildcardid [stc::get $dhcpv4block -CircuitId]
            append hlapi_script [::sth::hlapiGen::hlapi_gen_device_dhcpv4_wildcard_setting "circuit" $wildcardid]
		    unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-circuitid)
		  }

    }
    if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-enableremoteid)]} {
        set remoteid_enable [set sth::hlapiGen::$device\_$dhcpv4block\_attr(-enableremoteid)]
        if {[regexp -nocase "false" $remoteid_enable]} {
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-remoteid)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-remoteid)
            }
        } else {
		    set  wildcardid [stc::get $dhcpv4block -remoteid]
            append hlapi_script [::sth::hlapiGen::hlapi_gen_device_dhcpv4_wildcard_setting "remote" $wildcardid]
		    unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-remoteid)
		  }

    }
	#process the DHCP Custom Options 
	set dhcpOption [stc::get $dhcpv4block -children-dhcpv4msgoption ]
	if { [llength $dhcpOption] > 0 } {
	    foreach option $dhcpOption {
		    set client_id_type ""
			set clientid [stc::get $option -Payload]
		    if {[regexp -nocase "true" [stc::get $option -enablewildcards]]} {
			    append client_id_type "[stc::get $option -OptionType]"
		        append hlapi_script "         -client_id_type            $client_id_type\\\n"
				append hlapi_script [::sth::hlapiGen::hlapi_gen_device_dhcpv4_wildcard_setting "client" $clientid]
			}
		}
	}
    #process the retry_attempts and the enable_auto_retry
    if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-enableautoretry)]} {
        set autoretry_enable [set sth::hlapiGen::$device\_$dhcpv4block\_attr(-enableautoretry)]
        if {[regexp -nocase "false" $autoretry_enable]} {
            unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-enableautoretry)
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-retryattempts)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-retryattempts)
            }
        }
    }
    #process the enable_relay_link_selection and the relay_link_selection
    if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelaylinkselection)]} {
        set relaylinkselection_enable [set sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelaylinkselection)]
        if {[regexp -nocase "false" $relaylinkselection_enable]} {
            unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelaylinkselection)
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-relaylinkselection)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-relaylinkselection)
            }
        }
    }
    #process the enable_relay_vpn_id and the vpn_id, vpn_type
    if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelayvpnid)]} {
        set relayvpnid_enable [set sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelayvpnid)]
        if {[regexp -nocase "false" $relayvpnid_enable]} {
            unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelayvpnid)
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-vpnid)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-vpnid)
            }
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-vpntype)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-vpntype)
            }
        }
    }
    #process the relay_agent_flag and the relay_pool_ip_addr, relay_agent_ip_addr, relay_agent_ip_addr
    if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelayagent)]} {
        set relayagent_enable [set sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelayagent)]
        if {[regexp -nocase "false" $relayagent_enable]} {
            unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-enablerelayagent)
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-relaypoolipv4addr)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-relaypoolipv4addr)
            }
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-relayserveripv4addr)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-relayserveripv4addr)
            }
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-relayagentipv4addr)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-relayagentipv4addr)
            }
            if {[info exists sth::hlapiGen::$device\_$dhcpv4block\_attr(-relayagentipv4addrmask)]} {
                unset sth::hlapiGen::$device\_$dhcpv4block\_attr(-relayagentipv4addrmask)
            }
        }
    }
    #process the vlan_id_count and the vlan_id_outer_count if it the IfRecycleCount is 0, then  make it same with devicecount
    if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set sth::hlapiGen::$device\_obj(vlanif)]
        set idrepeatcountInn 0
        set idrepeatcountOut 0
           
        if {  [llength $vlanifs] >1 } {    
            set vlanifInn [lindex $vlanifs 0]
            set vlanifOut [lindex $vlanifs 1]
        
            set idrepeatcountInn [set sth::hlapiGen::$device\_$vlanifInn\_attr(-idrepeatcount)]
            set idrepeatcountOut [set sth::hlapiGen::$device\_$vlanifOut\_attr(-idrepeatcount)]
        
            set ifrecyclecountInn [set sth::hlapiGen::$device\_$vlanifInn\_attr(-ifrecyclecount)]
            set ifrecyclecountOut [set sth::hlapiGen::$device\_$vlanifOut\_attr(-ifrecyclecount)]
            
            if { [llength $vlanifs] >2 } {
                foreach myarg {vlan_id_list vlan_id_count_list vlan_id_step_list vlan_user_priority_list vlan_id_repeat_count_list vlan_ether_type_list} {
                    set value_list ""
                    for {set i 2} {$i < [llength $vlanifs]} {incr i} {
                        set myvlanif [lindex $vlanifs $i]
                        set class_in_table [string tolower [set $name_space$cmd_name\_stcobj($myarg)]]
                        set attr_in_table [string tolower [set $name_space$cmd_name\_stcattr($myarg)]]
                        if {[info exists $name_space$cmd_name\_supported($myarg)]} {
                            set supported [set $name_space$cmd_name\_supported($myarg)]
                            if {[regexp -nocase {false} $supported]} {
                                continue
                            }
                        }
                        if {[regexp -nocase "^$class_in_table$" "VlanIf_List"]} {
                            if {[info exists sth::hlapiGen::$device\_$myvlanif\_attr(-$attr_in_table)]} {
                                set value [set sth::hlapiGen::$device\_$myvlanif\_attr(-$attr_in_table)]
                                if {[regexp -nocase "tpid" $attr_in_table]} {
                                    set value [format "0x%04X" $value]
                                } 
                                append value_list "$value "
                                unset sth::hlapiGen::$device\_$myvlanif\_attr(-$attr_in_table)
                            }
                        } 
                    }
                    if {$value_list != ""} {
                        append hlapi_script "			-$myarg			$value_list\\\n"
                    }
                }
                
                for {set i 2} {$i < [llength $vlanifs]} {incr i} {
                    set myvlanif [lindex $vlanifs $i]
                    unset sth::hlapiGen::$device\_$myvlanif\_attr
                }
                set vlanifs "$vlanifInn $vlanifOut"
                set sth::hlapiGen::$device\_obj(vlanif) "$vlanifInn $vlanifOut"
            }
        }
        
          
        foreach vlanif $vlanifs {
            set tpid [set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid)]
            set tpid_update [format "0x%04X" $tpid]
            set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid) $tpid_update
        }
        
        if { $idrepeatcountInn == 0 && $idrepeatcountOut ==0 } {
            foreach vlanif $vlanifs {
                set count [set sth::hlapiGen::$device\_$vlanif\_attr(-ifrecyclecount)]
                if {$count == 0} {
                    set sth::hlapiGen::$device\_$vlanif\_attr(-ifrecyclecount) [set sth::hlapiGen::$device\_$device\_attr(-devicecount)]
                }
            }   
        } else {
            append hlapi_script "			-vlan_id_repeat_count			    $idrepeatcountInn\\\n"
            append hlapi_script "			-vlan_id_outer_repeat_count			    $idrepeatcountOut\\\n"
            # if { $ifrecyclecountInn == 0 } {
                # append hlapi_script "			-vlan_id_count      			    $ifrecyclecountInn\\\n"
            # }
            # if { $ifrecyclecountOut == 0 } {
                # append hlapi_script "			-vlan_id_outer_count			    $ifrecyclecountOut\\\n"
            # }
        }
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $hlapi_script $first_time   
}
proc ::sth::hlapiGen::hlapi_gen_device_dhcpv6 {device class mode hlt_ret cfg_args first_time} {
    
    #config dhcpv6portconfig
    set port [stc::get $device -affiliationport-Targets]
    set dhcpv6portconfighandle [stc::get $port -children-dhcpv6portconfig]
    set dhcpv6portconfighandle [lindex $dhcpv6portconfighandle 0]
    set table_name "::sth::Dhcpv6::dhcpv6Table"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_dhcpv6_config"
    set port_handle $port
    #get ip version.
    regexp {([4|6])} $class match ipversion
    if {![regexp -nocase $port [array names ::sth::hlapiGen::dhcpv6portconfigured]]} {
        append hlt_ret_port $hlt_ret "port"
    
            append hlapi_script "			-ip_version			    $ipversion\\\n"
            #append hlapi_script $cfg_args
            
            set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
            append hlapi_script "			-port_handle	            $port_handle_new\\\n"
                
            set dhcp_config [hlapi_gen_device_basic_without_puts $port dhcpv6portconfig create $hlt_ret_port $hlapi_script 1]

        set ::sth::hlapiGen::dhcpv6portconfigured($port) $hlt_ret_port
    }
    
    if {$first_time == 1} {
        #puts_to_file "\nset dhcp_handle \[keylget $::sth::hlapiGen::dhcpv6portconfigured($port) handles\]\n"
        set dhcpv6blockcfg_args "			-handle        \$dhcp_handle\\\n"
    } 
    set cmd_name "emulation_dhcpv6_group_config"
    set hlapi_script ""
    set dhcpgrouphandl [stc::get $device -children-$class]
    set dhcpgrouphandl [lindex $dhcpgrouphandl 0]
    set cfgFromChildren ""
    set childList [stc::get $dhcpgrouphandl -children]
    
    set dhcp6_delayed_auth_key_id ""
    set dhcp6_delayed_auth_key_value ""
    set option_value ""
    set option_payload ""
    set remove_option ""
    set enable_wildcards ""
    set string_as_hex_value ""
    set include_in_message ""
    
    #maybe need change the stcobj of num_sessions
    if {[regexp -nocase "host" $device]} {
        set $name_space$cmd_name\_stcobj(num_sessions) "Host"
    }
    if {[regexp -nocase "router" $device]} {
        set $name_space$cmd_name\_stcobj(num_sessions) "Router"
    }
    
    foreach child $childList {
        if {[regexp -nocase "Dhcpv6MsgOption" $child]} {
            append option_value         "[stc::get $child -OptionType] "
            append option_payload       "[stc::get $child -Payload] "
            append remove_option        "[stc::get $child -Remove] "
            append enable_wildcards     "[stc::get $child -EnableWildcards] "
            append string_as_hex_value  "[stc::get $child -HexValue] "
            append include_in_message   "[stc::get $child -MsgTypeList] "
        }
        if {[regexp -nocase "Dhcpv6DelayedAuthKey" $child]} {
            append dhcp6_delayed_auth_key_id        "[stc::get $child -KeyId] "
            append dhcp6_delayed_auth_key_value      "[stc::get $child -KeyValue] "
            
        }
        
    }
    if {$dhcp6_delayed_auth_key_id ne ""} {
        append cfgFromChildren "			-dhcp6_delayed_auth_key_id	    $dhcp6_delayed_auth_key_id\\\n"
        append cfgFromChildren "			-dhcp6_delayed_auth_key_value	    $dhcp6_delayed_auth_key_value\\\n"
    }
    
    if {$option_value ne ""} {
        append cfgFromChildren "			-option_value			    $option_value\\\n"
        append cfgFromChildren "			-option_payload			    $option_payload\\\n"
        append cfgFromChildren "			-remove_option			    $remove_option\\\n"
        append cfgFromChildren "			-enable_wildcards		    $enable_wildcards\\\n"
        append cfgFromChildren "			-string_as_hex_value		    $string_as_hex_value\\\n"
        append cfgFromChildren "			-include_in_message		    $include_in_message\\\n"
    
    }
    
    #get the encap info
    set encap [::sth::hlapiGen::getencap $device]
        append hlapi_script "			-dhcp_range_ip_type			    $ipversion\\\n"
        append hlapi_script "			-encap			    $encap\\\n"
        #append hlapi_script "			-num_sessions			    1\\\n"
        append hlapi_script $cfg_args
        append hlapi_script $cfgFromChildren
        
        #vlan_id_mode
        #vlan_id_outer_mode
        if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
            set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
            if {[llength $vlanifs] > 1} {
                append hlapi_script "     -qinq_incr_mode    both\\\n"
            }
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
                        append hlapi_script "     -vlan_id_outer_mode    $vlan_mode\\\n"
                    } else {
                        append hlapi_script "     -vlan_id_mode    $vlan_mode\\\n"
                    }
                } else {
                    append hlapi_script "     -vlan_id_mode    $vlan_mode\\\n"
                }
            }
        }
	
	set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
        if {$first_time == 1} {
            append hlapi_script $dhcpv6blockcfg_args
        }
        if {[set sth::hlapiGen::$device\_$dhcpgrouphandl\_attr(-enableauth)] eq false} {
            set ::sth::Dhcpv6::emulation_dhcpv6_group_config_stcobj(auth_protocol) "_none_"
        }
        
    # process RemoteId and RemoteIdEnterprise, should not output the default values if they are not enabled 
    set dhcpv6block [set sth::hlapiGen::$device\_obj(dhcpv6blockconfig)]
    if {[info exists sth::hlapiGen::$device\_$dhcpv6block\_attr(-enableremoteid)]} {
        set remoteid_enable [set sth::hlapiGen::$device\_$dhcpv6block\_attr(-enableremoteid)]
        if {[regexp -nocase "false" $remoteid_enable]} {
            if {[info exists sth::hlapiGen::$device\_$dhcpv6block\_attr(-remoteid)]} {
                unset sth::hlapiGen::$device\_$dhcpv6block\_attr(-remoteid)
                unset sth::hlapiGen::$device\_$dhcpv6block\_attr(-remoteidenterprise)
            }
        } else {
		    set wildcardid [stc::get $dhcpv6block -RemoteId]
            append hlapi_script [::sth::hlapiGen::hlapi_gen_device_dhcpv4_wildcard_setting "remote" $wildcardid]
		    unset sth::hlapiGen::$device\_$dhcpv6block\_attr(-remoteid)
		  }
    }    
    set dhcp_group_config [hlapi_gen_device_basic_without_puts $device $class $mode $hlt_ret $hlapi_script $first_time]

    if {[info exists dhcp_config]} {
        #replace emulation_dhcpv6_config => emulation_dhcp_config
        regsub -all emulation_dhcpv6_config  $dhcp_config emulation_dhcp_config dhcp_config
        puts_to_file $dhcp_config
        gen_status_info $hlt_ret_port "sth::emulation_dhcp_config"
    }
    if {$first_time == 1} {
        puts_to_file "\nset dhcp_handle \[keylget $::sth::hlapiGen::dhcpv6portconfigured($port) handles\]\n"
    }
    #replace emulation_dhcpv6_group_config => emulation_dhcp_group_config
    regsub -all emulation_dhcpv6_group_config  $dhcp_group_config emulation_dhcp_group_config dhcp_group_config
    puts_to_file $dhcp_group_config
    gen_status_info $hlt_ret "sth::emulation_dhcp_group_config"
    
}

proc ::sth::hlapiGen::hlapi_gen_device_dhcpv6pd {device class mode hlt_ret cfg_args first_time} {
    
    #config dhcpv6portconfig
    set port [stc::get $device -affiliationport-Targets]
    set dhcpv6portconfighandle [stc::get $port -children-dhcpv6portconfig]
    set dhcpv6portconfighandle [lindex $dhcpv6portconfighandle 0]
    set table_name "::sth::Dhcpv6::dhcpv6Table"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_dhcpv6_config"
    set port_handle $port
    
    #get ip version.
    regexp {([4|6])} $class match ipversion
    if {![regexp -nocase $port [array names ::sth::hlapiGen::dhcpv6portconfigured]]} {
        append hlt_ret_port $hlt_ret "port"

            append hlapi_script "			-ip_version			    $ipversion\\\n"
            #append hlapi_script $cfg_args
            
            set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
            append hlapi_script "			-port_handle	            $port_handle_new\\\n"
                
            set dhcp_config [hlapi_gen_device_basic_without_puts $port dhcpv6portconfig create $hlt_ret_port $hlapi_script 1]
        set ::sth::hlapiGen::dhcpv6portconfigured($port) $hlt_ret_port
    }
    
    if {$first_time == 1} {
        #puts_to_file "\nset dhcp_handle \[keylget $::sth::hlapiGen::dhcpv6portconfigured($port) handles\]\n"
        set dhcpv6blockcfg_args "			-handle        \$dhcp_handle\\\n"
    }     
    set cmd_name "emulation_dhcpv6pd_group_config"
    
    set hlapi_script ""
    
    set dhcpgrouphandl [stc::get $device -children-$class]
    set dhcpgrouphandl [lindex $dhcpgrouphandl 0]
    set cfgFromChildren ""
    set childList [stc::get $dhcpgrouphandl -children]
    set option_value ""
    set option_payload ""
    set remove_option ""
    set enable_wildcards ""
    set string_as_hex_value ""
    set include_in_message ""
    
    #maybe need change the stcobj of num_sessions
    if {[regexp -nocase "host" $device]} {
        set $name_space$cmd_name\_stcobj(num_sessions) "Host"
    }
    #check if the default host is created
    set linkedstatus [stc::get $device -linkdstdevice-Sources]
    array set ::sth::hlapiGen::linkDeviceRetKey {}
    if {$linkedstatus != ""} {
        append hlapi_script "-export_addr_to_clients 1\\\n"
	foreach link $linkedstatus {
	    set linkSrc [stc::get $link -containedlink-Sources]
	    if {[regexp -nocase "emulateddevice" $linkSrc]} {
		if {![info exists ::sth::hlapiGen::device_ret($linkSrc)]} {
		    set ::sth::hlapiGen::device_ret($linkSrc) "$hlt_ret 0"
		    lappend ::sth::hlapiGen::protocol_to_devices(emulateddevice) "$linkSrc"
		    set ::sth::hlapiGen::linkDeviceRetKey($linkSrc) "linked_host_handle"
		}
	    }
	}
    }
    

    if {[regexp -nocase "router" $device]} {
        set $name_space$cmd_name\_stcobj(num_sessions) "Router"
    }
    
    foreach child $childList {
        if {[regexp -nocase "Dhcpv6MsgOption" $child]} {
            append option_value         "[stc::get $child -OptionType] "
            append option_payload       "[stc::get $child -Payload] "
            append remove_option        "[stc::get $child -Remove] "
            append enable_wildcards     "[stc::get $child -EnableWildcards] "
            append string_as_hex_value  "[stc::get $child -HexValue] "
            append include_in_message   "[stc::get $child -MsgTypeList] "
        }
        
    }
    
    if {$option_value ne ""} {
        append cfgFromChildren "			-option_value			    $option_value\\\n"
        append cfgFromChildren "			-option_payload			    $option_payload\\\n"
        append cfgFromChildren "			-remove_option			    $remove_option\\\n"
        append cfgFromChildren "			-enable_wildcards		    $enable_wildcards\\\n"
        append cfgFromChildren "			-string_as_hex_value		    $string_as_hex_value\\\n"
        append cfgFromChildren "			-include_in_message		    $include_in_message\\\n"
    
    }
    #get the encap info
    set encap [::sth::hlapiGen::getencap $device]
        append hlapi_script "			-dhcp_range_ip_type			    $ipversion\\\n"
        append hlapi_script "			-dhcp6_client_mode			    DHCPPD\\\n"
        append hlapi_script "			-encap			    $encap\\\n"
        #append hlapi_script "			-num_sessions			    1\\\n"
        append hlapi_script $cfg_args
	append hlapi_script $cfgFromChildren
        
        #vlan_id_mode
        #vlan_id_outer_mode
        if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
            set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
            if {[llength $vlanifs] > 1} {
                append hlapi_script "     -qinq_incr_mode    both\\\n"
            }
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
                        append hlapi_script "     -vlan_id_outer_mode    $vlan_mode\\\n"
                    } else {
                        append hlapi_script "     -vlan_id_mode    $vlan_mode\\\n"
                    }
                } else {
                    append hlapi_script "     -vlan_id_mode    $vlan_mode\\\n"
                }
            }
        }
        
	set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
        if {$first_time == 1} {
            append hlapi_script $dhcpv6blockcfg_args
        }
        set dhcp_group_config [hlapi_gen_device_basic_without_puts $device $class $mode $hlt_ret $hlapi_script $first_time]

    if {[info exists dhcp_config]} {
        #replace emulation_dhcpv6_config => emulation_dhcp_config
        regsub -all emulation_dhcpv6_config  $dhcp_config emulation_dhcp_config dhcp_config
        puts_to_file $dhcp_config
        gen_status_info $hlt_ret_port "sth::emulation_dhcp_config"
    }
     if {$first_time == 1} {
        puts_to_file "\nset dhcp_handle \[keylget $::sth::hlapiGen::dhcpv6portconfigured($port) handles\]\n"
    }
    #replace emulation_dhcpv6_group_config => emulation_dhcp_group_config
    regsub -all emulation_dhcpv6pd_group_config  $dhcp_group_config emulation_dhcp_group_config dhcp_group_config
    puts_to_file $dhcp_group_config
    gen_status_info $hlt_ret "sth::emulation_dhcp_group_config"
}

proc ::sth::hlapiGen::hlapi_gen_device_dhcpserverv4 {device class mode hlt_ret cfg_args first_time} {
    
    #config all children and pass the parameters info basic
    set dhcpserverconfighandle [stc::get $device -children-$class]
    set dhcpserverconfighandle [lindex $dhcpserverconfighandle 0]
    set table_name "::sth::DhcpServer::dhcpServerTable"
    set cmd_name "emulation_dhcp_server_config"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]

    #maybe need change the stcobj of count
    if {[regexp -nocase "host" $device]} {
        set $name_space$cmd_name\_stcobj(count) "Host"
    }
    if {[regexp -nocase "router" $device]} {
        set $name_space$cmd_name\_stcobj(count) "Router"
    }
    
    #get ip version.
    regexp {([4|6])} $class match ipversion
    set encap [::sth::hlapiGen::getencap $device]
    set encap [string toupper $encap]
    set cfgFromChildren "			-ip_version			    $ipversion\\\n"
    append cfgFromChildren "			-encapsulation			    $encap\\\n"
    
    #vlan_id_mode
    #vlan_id_outer_mode
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
                    append cfgFromChildren "     -vlan_outer_id_mode    $vlan_mode\\\n"
                } else {
                    append cfgFromChildren "     -vlan_id_mode    $vlan_mode\\\n"
                }
            } else {
                append cfgFromChildren "     -vlan_id_mode    $vlan_mode\\\n"
            }
        }
    }
        
    set childList [stc::get $dhcpserverconfighandle -children]
    
    foreach child $childList {
        if {[regexp -nocase "Dhcpv4ServerDefaultPoolConfig" $child]} {
            #only handle Dhcpv4ServerDefaultPoolConfig and it's child:Dhcpv4ServerMsgOption
            get_attr $child $child
            #convert ipaddress_increment from a.c.b.d to a number 
            if {[info exists sth::hlapiGen::$child\_$child\_attr(-hostaddrstep)]} {
                set tmpvalue [set sth::hlapiGen::$child\_$child\_attr(-hostaddrstep)]
                set sth::hlapiGen::$child\_$child\_attr(-hostaddrstep) [::sth::hlapiGen::ipaddr2dec $tmpvalue]
            }
            foreach child_obj [array names ::sth::hlapiGen::$child\_obj] {
                append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $child $child $child_obj]
            }
            set defaultpoolchildList [stc::get $child -children]
            foreach defaultpoolchild $defaultpoolchildList {
                if {[regexp -nocase "Dhcpv4ServerMsgOption" $defaultpoolchild]} {
                    
                    #here gen parameter: dhcp_ack_* and dhcp_offer_*
                    set MsgType [stc::get $defaultpoolchild -MsgType]
                    set $name_space$cmd_name\_stcattr(dhcp_ack_options) "_none_"
                    set $name_space$cmd_name\_stcattr(dhcp_offer_options) "_none_"
                    if {[regexp -nocase "OFFER" $MsgType]&&(![regexp -nocase "dhcp_ack_options" $cfgFromChildren])} {
                        append cfgFromChildren "			-dhcp_ack_options			    1\\\n"
                    }
                    if {[regexp -nocase "ACK" $MsgType]&&(![regexp -nocase "dhcp_offer_options" $cfgFromChildren])} {
                        append cfgFromChildren "			-dhcp_offer_options			    1\\\n"
                    }
                    
                    get_attr $defaultpoolchild $defaultpoolchild
                    
                    foreach defaultpoolchild_obj [array names ::sth::hlapiGen::$defaultpoolchild\_obj] {
                        append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $defaultpoolchild $defaultpoolchild $defaultpoolchild_obj]
                        
                    }
                }
            }
        }
    }
    #remove ip_prefix_step for emulation_dhcp_server_config
    set $name_space$cmd_name\_stcattr(ip_prefix_step) "_none_"
    #call the basic function
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfgFromChildren $first_time
    set ::sth::hlapiGen::dhcpv4servertconfigured($device) $hlt_ret
											  
    #handle emulation_dhcp_server_relay_agent_config
    set derverpoolconfig [stc::get $dhcpserverconfighandle -children-Dhcpv4ServerPoolConfig]
    set cfgFromChildren ""
    
    if {[llength $derverpoolconfig] > 1} {
        append cfgFromChildren "			-relay_agent_pool_count			    [llength $derverpoolconfig]\\\n"
    
        set derverpoolconfig1 [lindex $derverpoolconfig 0]
        set startiplist1 [stc::get $derverpoolconfig1 -StartIpList]
        set derverpoolconfig2 [lindex $derverpoolconfig 1]
        set startiplist2 [stc::get $derverpoolconfig2 -StartIpList]
        set pool_step [calculate_difference $startiplist1 $startiplist2 ipv4]
        append cfgFromChildren "			-relay_agent_pool_step			    $pool_step\\\n"
    }
    if {$derverpoolconfig ne ""} {
        set derverpoolconfig1 [lindex $derverpoolconfig 0]

        puts_to_file  "set dhcpserver_handle \"\[keylget $hlt_ret handle.dhcp_handle]\" \n\n"
        
        append hlt_ret "_agent0"
        set cmd_name "emulation_dhcp_server_relay_agent_config"
        
        set derverpoolmsgoptionconfig [stc::get $derverpoolconfig1 -children-Dhcpv4ServerMsgOption]
        if {$derverpoolmsgoptionconfig ne ""} {
            #add child:Dhcpv4ServerMsgOption
            set derverpoolmsgoptionconfig [lindex $derverpoolmsgoptionconfig 0]
            #here gen parameter: dhcp_ack_* and dhcp_offer_*
            set MsgType [stc::get $derverpoolmsgoptionconfig -MsgType]
            set $name_space$cmd_name\_stcattr(dhcp_ack_options) "_none_"
            set $name_space$cmd_name\_stcattr(dhcp_offer_options) "_none_"
            if {[regexp -nocase "OFFER" $MsgType]&&(![regexp -nocase "dhcp_offer_options" $cfgFromChildren])} {
                append cfgFromChildren "			-dhcp_offer_options			    1\\\n"
            }
            if {[regexp -nocase "ACK" $MsgType]&&(![regexp -nocase "dhcp_ack_options" $cfgFromChildren])} {
                append cfgFromChildren "			-dhcp_ack_options			    1\\\n"
            }
            
            
            get_attr $derverpoolmsgoptionconfig $derverpoolmsgoptionconfig
            foreach derverpoolmsgoptionconfig_obj [array names ::sth::hlapiGen::$derverpoolmsgoptionconfig\_obj] {
                append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $derverpoolmsgoptionconfig $derverpoolmsgoptionconfig $derverpoolmsgoptionconfig_obj]
            }
        }
        
        #add Dhcpv4ServerPoolConfig
        
        append cfgFromChildren "			-handle			    \$dhcpserver_handle\\\n"
        get_attr $derverpoolconfig1 $derverpoolconfig1
        foreach derverpoolconfig1_obj [array names ::sth::hlapiGen::$derverpoolconfig1\_obj] {
            append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $derverpoolconfig1 $derverpoolconfig1 $derverpoolconfig1_obj]
        }
        append hlapi_script "      set $hlt_ret \[sth::$cmd_name\\\n"
        append hlapi_script "			-mode         create\\\n"
        append hlapi_script $cfgFromChildren
        append hlapi_script "\]\n"
        puts_to_file $hlapi_script
        gen_status_info $hlt_ret "sth::$cmd_name"
    }
}

proc ::sth::hlapiGen::hlapi_gen_device_dhcpserverv6 {device class mode hlt_ret cfg_args first_time} {
    
    #config all children and pass the parameters info basic
    set dhcpserverconfighandle [stc::get $device -children-$class]
    set dhcpserverconfighandle [lindex $dhcpserverconfighandle 0]
    set table_name "::sth::Dhcpv6Server::dhcpv6ServerTable"
    set cmd_name "emulation_dhcpv6_server_config"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set EmulationMode [stc::get $dhcpserverconfighandle -EmulationMode]
    #get ip version.
    regexp {([4|6])} $class match ipversion
    
    set cfgFromChildren "			-ip_version			    $ipversion\\\n"
    append cfgFromChildren "			-encapsulation			    [::sth::hlapiGen::getencap $device]\\\n"
    
    #don't handle reconfigure_key and reconfigure_key_value_type if enable_reconfigure_key:false
    if {[set sth::hlapiGen::$device\_$dhcpserverconfighandle\_attr(-enablereconfigurekey)] eq "false"} {
        set $name_space$cmd_name\_stcobj(reconfigure_key) "_none_"
        set $name_space$cmd_name\_stcobj(reconfigure_key_value_type) "_none_"
    }
    
    #maybe need change the stcobj of count
    if {[regexp -nocase "host" $device]} {
        set $name_space$cmd_name\_stcobj(count) "Host"
    }
    if {[regexp -nocase "router" $device]} {
        set $name_space$cmd_name\_stcobj(count) "Router"
    }
    #vlan_id_mode
    #vlan_id_outer_mode
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        if {[llength $vlanifs] > 1} {
            append cfgFromChildren "     -qinq_incr_mode    both\\\n"
        }
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
    
    set childList [stc::get $dhcpserverconfighandle -children]
    if {$EmulationMode == "DHCPV6"} {
        foreach type "server addr_pool prefix_pool" {
            set [set type]_custom_option_value ""
            set [set type]_custom_option_payload ""
            set [set type]_custom_enable_wildcards ""
            set [set type]_custom_string_as_hex_value ""
            set [set type]_custom_include_in_message "" 
        }
        
        set dhcp6_delayed_auth_key_id ""
        set dhcp6_delayed_auth_key_value ""
        
        foreach child $childList {
            if {[regexp -nocase "dhcpv6serverdefaultaddrpoolconfig" $child] || \
                [regexp -nocase "dhcpv6serverdefaultprefixpoolconfig" $child] || \
                [regexp -nocase "dhcpv6serveraddrpoolconfig" $child] || \
                [regexp -nocase "dhcpv6delayedauthkey" $child] || \
                [regexp -nocase "dhcpv6servermsgoption" $child] || \
                [regexp -nocase "dhcpv6serverprefixpoolconfig" $child] } {
                
                if {[regexp -nocase "dhcpv6servermsgoption" $child]} {
                    #store the dhcpv6servermsgoption for server_custom
                    append server_custom_option_value        "[stc::get $child -OptionType] "
                    append server_custom_option_payload      "[stc::get $child -Payload] "
                    append server_custom_enable_wildcards    "[stc::get $child -EnableWildcards] "
                    append server_custom_string_as_hex_value "[stc::get $child -HexValue] "
                    append server_custom_include_in_message  "[stc::get $child -MsgType] "
                    continue
                }
                
                if {[regexp -nocase "dhcpv6delayedauthkey" $child]} {
                    #store the dhcpv6servermsgoption for server_custom
                    append dhcp6_delayed_auth_key_id        "[stc::get $child -KeyId] "
                    append dhcp6_delayed_auth_key_value      "[stc::get $child -KeyValue] "
                    continue
                }
                
                get_attr $child $child
                foreach child_obj [array names ::sth::hlapiGen::$child\_obj] {
                    append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $child $child $child_obj]
                }
                
                
                
                foreach child2 [stc::get $child -children] {
                    if {[regexp -nocase "dhcpv6servermsgoption" $child2]} {
                        #store the dhcpv6servermsgoption for addr_pool_custom and prefix_pool_custom
                        if {[regexp -nocase "dhcpv6serverdefaultaddrpoolconfig" $child]} {
                            append addr_pool_custom_option_value        "[stc::get $child2 -OptionType] "
                            append addr_pool_custom_option_payload      "[stc::get $child2 -Payload] "
                            append addr_pool_custom_enable_wildcards    "[stc::get $child2 -EnableWildcards] "
                            append addr_pool_custom_string_as_hex_value "[stc::get $child2 -HexValue] "
                            append addr_pool_custom_include_in_message  "[stc::get $child2 -MsgType] "
                        }
                        if {[regexp -nocase "dhcpv6serverdefaultprefixpoolconfig" $child]} {
                            append prefix_pool_custom_option_value        "[stc::get $child2 -OptionType] "
                            append prefix_pool_custom_option_payload      "[stc::get $child2 -Payload] "
                            append prefix_pool_custom_enable_wildcards    "[stc::get $child2 -EnableWildcards] "
                            append prefix_pool_custom_string_as_hex_value "[stc::get $child2 -HexValue] "
                            append prefix_pool_custom_include_in_message  "[stc::get $child2 -MsgType] "
                        }
                        
                    }
                    
                }
            }
        }
    
        #add custom info
        foreach type "server addr_pool prefix_pool" {
            if {[set [set type]_custom_option_value] ne ""} {
                append cfgFromChildren "			-[set type]_custom_option_value			            [set [set type]_custom_option_value]\\\n"
                append cfgFromChildren "			-[set type]_custom_option_payload			    [set [set type]_custom_option_payload]\\\n"
                append cfgFromChildren "			-[set type]_custom_enable_wildcards			    [set [set type]_custom_enable_wildcards]\\\n"
                append cfgFromChildren "			-[set type]_custom_string_as_hex_value			    [set [set type]_custom_string_as_hex_value]\\\n"
                append cfgFromChildren "			-[set type]_custom_include_in_message			    [set [set type]_custom_include_in_message]\\\n"
                
            }    
        }
        if {$dhcp6_delayed_auth_key_id ne ""} {
                append cfgFromChildren "			-dhcp6_delayed_auth_key_id			            $dhcp6_delayed_auth_key_id\\\n"
                append cfgFromChildren "			-dhcp6_delayed_auth_key_value			    $dhcp6_delayed_auth_key_value\\\n"
                
        }
    } else {
        foreach type "server prefix_pool" {
            set [set type]_custom_option_value ""
            set [set type]_custom_option_payload ""
            set [set type]_custom_enable_wildcards ""
            set [set type]_custom_string_as_hex_value ""
            set [set type]_custom_include_in_message "" 
        }
        
        set dhcp6_delayed_auth_key_id ""
        set dhcp6_delayed_auth_key_value ""
        
        foreach child $childList {
            if {[regexp -nocase "dhcpv6serverdefaultprefixpoolconfig" $child] || \
                [regexp -nocase "dhcpv6delayedauthkey" $child] || \
                [regexp -nocase "dhcpv6servermsgoption" $child] } {
                
                if {[regexp -nocase "dhcpv6servermsgoption" $child]} {
                    #store the dhcpv6servermsgoption for server_custom
                    append server_custom_option_value        "[stc::get $child -OptionType] "
                    append server_custom_option_payload      "[stc::get $child -Payload] "
                    append server_custom_enable_wildcards    "[stc::get $child -EnableWildcards] "
                    append server_custom_string_as_hex_value "[stc::get $child -HexValue] "
                    append server_custom_include_in_message  "[stc::get $child -MsgType] "
                    continue
                }
                
                if {[regexp -nocase "dhcpv6delayedauthkey" $child]} {
                    #store the dhcpv6servermsgoption for server_custom
                    append dhcp6_delayed_auth_key_id        "[stc::get $child -KeyId] "
                    append dhcp6_delayed_auth_key_value      "[stc::get $child -KeyValue] "
                    continue
                }
                
                get_attr $child $child
                foreach child_obj [array names ::sth::hlapiGen::$child\_obj] {
                    append cfgFromChildren [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $child $child $child_obj]
                }
                
                
                
                foreach child2 [stc::get $child -children] {
                    if {[regexp -nocase "dhcpv6servermsgoption" $child2]} {
                        #store the dhcpv6servermsgoption for addr_pool_custom and prefix_pool_custom
                        
                        if {[regexp -nocase "dhcpv6serverdefaultprefixpoolconfig" $child]} {
                            append prefix_pool_custom_option_value        "[stc::get $child2 -OptionType] "
                            append prefix_pool_custom_option_payload      "[stc::get $child2 -Payload] "
                            append prefix_pool_custom_enable_wildcards    "[stc::get $child2 -EnableWildcards] "
                            append prefix_pool_custom_string_as_hex_value "[stc::get $child2 -HexValue] "
                            append prefix_pool_custom_include_in_message  "[stc::get $child2 -MsgType] "
                        }
                        
                    }
                    
                }
            }
        }
    
        #add custom info
        foreach type "server prefix_pool" {
            if {[set [set type]_custom_option_value] ne ""} {
                append cfgFromChildren "			-[set type]_custom_option_value			            [set [set type]_custom_option_value]\\\n"
                append cfgFromChildren "			-[set type]_custom_option_payload			    [set [set type]_custom_option_payload]\\\n"
                append cfgFromChildren "			-[set type]_custom_enable_wildcards			    [set [set type]_custom_enable_wildcards]\\\n"
                append cfgFromChildren "			-[set type]_custom_string_as_hex_value			    [set [set type]_custom_string_as_hex_value]\\\n"
                append cfgFromChildren "			-[set type]_custom_include_in_message			    [set [set type]_custom_include_in_message]\\\n"
                
            }    
        }
        if {$dhcp6_delayed_auth_key_id ne ""} {
                append cfgFromChildren "			-dhcp6_delayed_auth_key_id			            $dhcp6_delayed_auth_key_id\\\n"
                append cfgFromChildren "			-dhcp6_delayed_auth_key_value			    $dhcp6_delayed_auth_key_value\\\n"
                
        }
    }
    
    
    set dhcp_server_config [hlapi_gen_device_basic_without_puts $device $class $mode $hlt_ret $cfgFromChildren $first_time]
    regsub -all emulation_dhcpv6_server_config  $dhcp_server_config emulation_dhcp_server_config dhcp_server_config
    puts_to_file $dhcp_server_config
    gen_status_info $hlt_ret "sth::emulation_dhcp_server_config"
	
	set ::sth::hlapiGen::dhcpv6servertconfigured($device) $hlt_ret
}

#--------------------------------------------------------------------------------------------------------#
#gre config convert function, it is used to generate the hltapi emulation_gre_config function
#input:     device      =>  the port on which the interface config function will be used
#           calss       =>  the class name
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#           cfg_args    => the args prepared earlier for the bgp config function
#output:    the genrated hltapi interface_config funtion will be output to the file.
proc ::sth::hlapiGen::hlapi_gen_device_greconfig {device class mode hlt_ret cfg_args_local {first_time 0}} {
    if {![info exists sth::hlapiGen::$device\_obj(greif)] || $mode != "create"} {
        return
    }

    set greif [set sth::hlapiGen::$device\_obj(greif)]
    unset sth::hlapiGen::$device\_obj(greif)
    set greipv4if [stc::get $greif -stackedonendpoint-Targets]
    set ipv4iflist [stc::get $greif -stackedonendpoint-Sources]
    if {[regexp "ipv4if" $ipv4iflist]} {
        foreach ipv4if $ipv4iflist {
            if {[regexp -nocase "ipv4if" $ipv4if]} {
               set sth::hlapiGen::$device\_obj(ipv4if) $ipv4if
               break
            }
        }
    } else {
        unset sth::hlapiGen::$device\_obj(ipv4if)
    }
    
    #cofig the greif and greipv4if, and etheriiif
    
    set hlapi_script ""
    #parse the table file 
    set table_name "::sth::Gre::greTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space "::sth::Gre::"
    set cmd_name "emulation_gre_config"
    append hlapi_script "set $hlt_ret \[sth::$cmd_name\\\n"
    
    #handle the count and step for scaling mode
    if {[info exists  sth::hlapiGen::$device\_$device\_attr(-count)]} {
        set count [set  sth::hlapiGen::$device\_$device\_attr(-count)]
        append cfg_args "                    -gre_tnl_addr_count         $count \\\n"
        append cfg_args "                    -gre_src_addr_count         $count \\\n"
        append cfg_args "                    -gre_dst_addr_count         $count \\\n"
        append cfg_args "                    -gre_src_mode               increment \\\n"
        append cfg_args "                    -gre_dst_mode               increment \\\n"
        set $name_space$cmd_name\_stcattr(gre_tnl_addr_step) "Gateway.step"
        set $name_space$cmd_name\_stcattr(gre_src_addr_step) "Address.step"
    } else {
        set cfg_args ""
    }
    
    #gre_tnl_type
    set remotev4 [stc::get $greif -RemoteTunnelEndPointV4]
    set remotev6 [stc::get $greif -RemoteTunnelEndPointV6]
    set gre_tnl_type 4
    if {![regexp "2000::2" $remotev6]} {
        set gre_tnl_type 6
        set $name_space$cmd_name\_stcattr(gre_dst_addr) RemoteTunnelEndPointV6
        set $name_space$cmd_name\_stcattr(gre_dst_addr_step) RemoteTunnelEndPointV6Step
    } 
    append cfg_args "			-gre_tnl_type		$gre_tnl_type\\\n"   
    append cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $greif $class]
    set gre_in_key_en [set ::sth::hlapiGen::$device\_$greif\_attr(-inflowkeyfieldenabled)]
    set gre_out_key_en [set ::sth::hlapiGen::$device\_$greif\_attr(-outflowkeyfieldenabled)]
    if {[regexp -nocase "true" $gre_in_key_en]} {
        set gre_in_key [set ::sth::hlapiGen::$device\_$greif\_attr(-rxflowkeyfield)]
        append cfg_args "-gre_in_key            $gre_in_key\\\n"
    }
    
    if {[regexp -nocase "true" $gre_out_key_en]} {
        set gre_out_key [set ::sth::hlapiGen::$device\_$greif\_attr(-txflowkeyfield)]
        append cfg_args "-gre_out_key            $gre_out_key\\\n"
    }
    
    #gre checksum
    set checksum [set ::sth::hlapiGen::$device\_$greif\_attr(-checksumenabled)]
    if {[regexp -nocase "true" $checksum]} {
        append cfg_args "-gre_checksum            1\\\n"
    } else {
        append cfg_args "-gre_checksum            0\\\n"
    }

    append cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $greipv4if ipv4if]
    append hlapi_script $cfg_args 
    if {$first_time == 0} {
        append hlapi_script "\]\n"
        puts_to_file $hlapi_script
        puts_to_file "puts \"***** run sth::emulation_gre_config successfully\"\n"
    } else {
        set encap [::sth::hlapiGen::getencap $device]
        append cfg_args "-gre_encapsulation			    $encap\\\n"
        set port_handle $::sth::hlapiGen::port_ret([set ::sth::hlapiGen::$device\_$device\_attr(-affiliationport-targets)])
        append cfg_args "-gre_port_handle           $port_handle\\\n"
        
        set gre_config [hlapi_gen_device_basic_without_puts $device $class "" $hlt_ret $cfg_args $first_time]
        puts_to_file $gre_config
        puts_to_file "puts \"***** run sth::emulation_gre_config successfully\"\n"

        set mylinks [stc::get $device -linkdstdevice-Sources]
		set index 0
		set my_ret [lindex $::sth::hlapiGen::device_ret($device) 0]  
		foreach mylink $mylinks {
			if {[info exists ::sth::hlapiGen::v_linkmap($mylink)]} {
				set dev_behind $::sth::hlapiGen::v_linkmap($mylink)
				set cfg_ret [lindex $::sth::hlapiGen::device_ret($dev_behind) 0]
				set mychild [stc::get $dev_behind -children]
				if {[regexp -nocase "Dhcpv6ServerConfig" $mychild]} {
					puts_to_file "set dhcp_host$index\_to_$my_ret \[keylget $cfg_ret handle.dhcpv6_handle\]"
				} elseif {[regexp -nocase "Dhcpv4ServerConfig" $mychild]} {
					puts_to_file "set dhcp_host$index\_to_$my_ret \[keylget $cfg_ret handle.dhcp_handle\]"
				} elseif {[regexp -nocase "Dhcpv6" $mychild]} {
					puts_to_file "set dhcp_host$index\_to_$my_ret \[keylget $cfg_ret dhcpv6_handle\]" 
				} else {
					puts_to_file "set dhcp_host$index\_to_$my_ret \[keylget $cfg_ret handle\]"
				}
				 
				puts_to_file "set $my_ret\_link$index \[::sth::link_config\\\n -link_src \$dhcp_host$index\_to_$my_ret\\\n -link_dst \"$$my_ret\"\\\n -link_type \"L2_GRE_Tunnel_Link\"\]"
				gen_status_info "$my_ret\_link$index" "sth::link_config"
				incr index
			}
        }
    }
}


proc ::sth::hlapiGen::multi_dev_check_func_bgp {class devices} {
    variable devicelist_obj
    variable scaling_tmp
    set update_obj [multi_dev_check_func_basic $class $devices]
             
    set attrlist "AsNum AsNum4Byte DutIpv4Addr DutIpv6Addr"
    foreach obj $update_obj {
        #call update-step to update the step value of bgprouterconfig obj
        if {[info exists devicelist_obj($obj)] && [llength $devicelist_obj($obj)] > 1} {
            update_step $class $devicelist_obj($obj) $attrlist ""
            
            set devicehdl [lindex $devicelist_obj($obj) 0]
            set subobjhdl [lindex [set ::sth::hlapiGen::$devicehdl\_obj($class)] 0]
            
            #if dutipaddr is null, then we can set the gateway as dutip
            if {[set ::sth::hlapiGen::$devicehdl\_$subobjhdl\_attr(-dutipv4addr)] == "null" && [info exists ::sth::hlapiGen::$devicehdl\_obj(ipv4if)]} {
                #if current dutipaddr is null, set the gateway as dutipaddr
                #ipv4if maybe a list when gre over ipv4 is configured
                set ipv4iflist [set ::sth::hlapiGen::$devicehdl\_obj(ipv4if)]
                foreach ipv4if $ipv4iflist {
                    set stacked_target [stc::get $ipv4if -stackedonendpoint-Targets]
                    if {[regexp -nocase "ethiiif" $stacked_target]} {
                        break
                    }
                }
                set ::sth::hlapiGen::$devicehdl\_$subobjhdl\_attr(-dutipv4addr) [set ::sth::hlapiGen::$devicehdl\_$ipv4if\_attr(-gateway)]
                set scaling_tmp($devicehdl\_$subobjhdl\_dutipv4addr.step) $scaling_tmp($devicehdl\_$ipv4if\_gateway.step)
            }
            if {[set ::sth::hlapiGen::$devicehdl\_$subobjhdl\_attr(-dutipv6addr)] == "null" && [info exists ::sth::hlapiGen::$devicehdl\_obj(ipv6if)]} {
                #if current dutipaddr is null, set the gateway as dutipaddr
                set ipv6iflist [set ::sth::hlapiGen::$devicehdl\_obj(ipv6if)]
                foreach ipv6if $ipv6iflist {
                    set addr [set ::sth::hlapiGen::$devicehdl\_$ipv6if\_attr(-address)]
                    if {![regexp -nocase "FE80" $addr]} {
			break				
                    }
                }
                set ::sth::hlapiGen::$devicehdl\_$subobjhdl\_attr(-dutipv6addr) [set ::sth::hlapiGen::$devicehdl\_$ipv6if\_attr(-gateway)]
                set scaling_tmp($devicehdl\_$subobjhdl\_dutipv6addr.step) $scaling_tmp($devicehdl\_$ipv6if\_gateway.step)
            }
            
            #DutIpv4Addr DutIpv6Addr are in the same parameter, need to update the attr of the data model info
            if {[info exists scaling_tmp($devicehdl\_$subobjhdl\_dutipv4addr.step)]} {
                set scaling_tmp($devicehdl\_$subobjhdl\_dutipaddr.step) $scaling_tmp($devicehdl\_$subobjhdl\_dutipv4addr.step)
            } elseif {[info exists scaling_tmp($devicehdl\_$subobjhdl\_dutipv6addr.step)]} {
                set scaling_tmp($devicehdl\_$subobjhdl\_dutipaddr.step) $scaling_tmp($devicehdl\_$subobjhdl\_dutipv6addr.step)
            }
            
            #need to check if the asnum4byte is enabled
            if {[regexp -nocase "true" [set ::sth::hlapiGen::$devicehdl\_$subobjhdl\_attr(-enable4byteasnum)]]} {
                set local_as4_step $scaling_tmp($devicehdl\_$subobjhdl\_asnum4byte.step)
                set local_as4_step [join [split $local_as4_step "."] ":"] 
                set scaling_tmp($devicehdl\_$subobjhdl\_asnum4byte.step) $local_as4_step
            } else {
                unset scaling_tmp($devicehdl\_$subobjhdl\_asnum4byte.step)
            }
            
            #set the local_as_mode
            if {[info exists scaling_tmp($devicehdl\_$subobjhdl\_asnum.step)]} {
                set scaling_tmp($devicehdl\_$subobjhdl\_asnum.mode) "increment"
            }
        }
    }   

    return $update_obj
}

proc ::sth::hlapiGen::process_tlv_eoam {tlv} {
    set returnval ""

    ####split pdu
    set pduList [split $tlv " "]
    set SndrIDpdu ""
    set OrgSpecpdu ""
    set DataTLVpdu ""
    set TestTLVpdu ""
    foreach pdu $pduList {
        if {[regexp -nocase "EOAMTLV" $pdu]} {
            switch -regexp $pdu {
                SndrID {
                    set pdutype SndrIDpdu
                }
                OrgSpec {
                    set pdutype OrgSpecpdu
                }
                DataTLV {
                    set pdutype DataTLVpdu
                }
                TestTLV {
                    set pdutype TestTLVpdu
                }
            }
        }
        regsub -all "</"  $pdu " " pdu
        regsub -all ">"  $pdu " " pdu
        regsub -all "<"  $pdu " " pdu
        if {[info exists pdutype]} {
            append $pdutype $pdu
        }
    }

    set hlapi(ChassisIDLen)  tlv_sender_chassis_id_length
    set hlapi(ChassisIDSubtype) tlv_sender_chassis_id_subtype
    set hlapi(ChassisID) tlv_sender_chassis_id
    set hlapi(OUI) tlv_org_oui
    set hlapi(SubType) tlv_org_subtype
    set hlapi(Value) tlv_org_value
    set hlapi(Data) tlv_data_pattern
    set hlapi(PatternType) tlv_test_pattern

    set length [llength $SndrIDpdu]
    set hlapi(Length) tlv_sender_length
    foreach arg "Length ChassisIDLen ChassisIDSubtype ChassisID" {
        set i 0
        while {$i< $length} {
            if {[lindex $SndrIDpdu $i] eq $arg} {
                set j [expr $i + 2]
                if {$j< $length} {
                    if {[lindex $SndrIDpdu $j] eq $arg} {
                        set val [lindex $SndrIDpdu [expr $i + 1]]
                        set val [format "%d" "0x$val"]
                        append returnval "			-$hlapi($arg)			    $val\\\n"
                        break
                    }
                }
            }
            incr i
        }
    }

    set length [llength $OrgSpecpdu]
    set hlapi(Length) tlv_org_length
    foreach arg "Length OUI SubType Value" {
        set i 0
        while {$i< $length} {
            if {[lindex $OrgSpecpdu $i] eq $arg} {
                set j [expr $i + 2]
                if {$j< $length} {
                    if {[lindex $OrgSpecpdu $j] eq $arg} {
                        set val [lindex $OrgSpecpdu [expr $i + 1]]
                        if {$arg ne "Value"} {
                            set val [format "%d" "0x$val"]
                        }
                        append returnval "			-$hlapi($arg)			    $val\\\n"
                        break
                    }
                }
            }
            incr i
        }
    }

    set length [llength $DataTLVpdu]
    set hlapi(Length) tlv_data_length
    foreach arg "Length Data" {
        set i 0
        while {$i< $length} {
            if {[lindex $DataTLVpdu $i] eq $arg} {
                set j [expr $i + 2]
                if {$j< $length} {
                    if {[lindex $DataTLVpdu $j] eq $arg} {
                        set val [lindex $DataTLVpdu [expr $i + 1]]
                        if {$arg ne "Data"} {
                            set val [format "%d" "0x$val"]
                        } else {
                            set val "0x$val"
                        }
                        append returnval "			-$hlapi($arg)			    $val\\\n"
                        break
                    }
                }
            }
            incr i
        }
    }

    set length [llength $TestTLVpdu]
    set hlapi(Length) tlv_test_length
    foreach arg "Length PatternType" {
        set i 0
        while {$i< $length} {
            if {[lindex $TestTLVpdu $i] eq $arg} {
                set j [expr $i + 2]
                if {$j< $length} {
                    if {[lindex $TestTLVpdu $j] eq $arg} {
                        set val [lindex $TestTLVpdu [expr $i + 1]]
                        if {$arg ne "PatternType"} {
                            set val [format "%d" "0x$val"]
                        } else {
                            set val [lindex "null null_with_crc prbs prbs_with_crc" $val]
                        }
                        append returnval "			-$hlapi($arg)			    $val\\\n"
                        break
                    }
                }
            }
            incr i
        }
    }

    return $returnval

}

proc ::sth::hlapiGen::hlapi_gen_device_eoam_topo {device class mode hlt_ret cfg_args first_time} {
    
    set eoamrouterList ""
    
    #handle mac_local in EthIIIf
    set router1 $device
    set router2 [lindex $::sth::hlapiGen::protocol_to_devices($class) 1]
    set EthIIIf [stc::get $router1 -children-EthIIIf]
    set EthIIIf [lindex $EthIIIf 0]
    set mac_local1 [stc::get $EthIIIf -SourceMac]
    set mac_local1 [join [split $mac_local1 "-"] ":"]
    set EthIIIf [stc::get $router2 -children-EthIIIf]
    set EthIIIf [lindex $EthIIIf 0]
    set mac_local2 [stc::get $EthIIIf -SourceMac]
    set mac_local2 [join [split $mac_local2 "-"] ":"]
    append childrenparams "			-mac_local			    $mac_local1\\\n"
    append childrenparams "			-mac_local_incr_mode			    increment\\\n"
    append childrenparams "			-mac_local_step			    [::sth::hlapiGen::calculate_difference $mac_local1 $mac_local2 ""]\\\n"

    #handle Vlan
    set vlanList [stc::get $device -children-vlanif]
    if {[llength $vlanList] == 1} {
        append childrenparams "			-vlan_id			    [stc::get [lindex $vlanList 0] -VlanId]\\\n"

    } elseif {[llength $vlanList] > 1} {
        append childrenparams "			-vlan_outer_id			    [stc::get [lindex $vlanList 0] -VlanId]\\\n"
        append childrenparams "			-vlan_id			    [stc::get [lindex $vlanList 1] -VlanId]\\\n"

    }
    
    #handle sut_ip_address
    set childList [stc::get $device -children]
    if {[regexp -nocase "ipv4if" $childList]} {
        set ipv4if [stc::get $device -children-ipv4if]
        set ipv4if [lindex $ipv4if 0]
        append childrenparams "			-sut_ip_address			    [stc::get $ipv4if -Gateway]\\\n"
    } elseif {[regexp -nocase "ipv6if" $childList]} {
        set ipv6if [stc::get $device -children-ipv6if]
        set ipv6if [lindex $ipv6if 0]
        append childrenparams "			-sut_ip_address			    [stc::get $ipv6if -Gateway]\\\n"
    }
        
    upvar 2 device_created alldevices
    foreach router $::sth::hlapiGen::protocol_to_devices($class) {
        if {[regexp -nocase "eoamlink" [stc::get $router]]} {
            if {$device ne $router} {
                append eoamrouterList $router " "
            }
        }
    }
    set alldevices [concat $alldevices $eoamrouterList]
    
    variable eoam_router_without_control
    set eoam_router_without_control $eoamrouterList
    
    append eoamrouterList $device
    
    
    set miprouter ""
    set meprouter ""
    #search the link
    foreach router $eoamrouterList {
        set linktarget [stc::get $router -containedlink-Targets]
        if {$linktarget ne ""} {
            set link($router) [stc::get $linktarget -linkdstdevice-Targets]
            if {![regexp -nocase $router $meprouter]} {
                append meprouter $router " "
            }
            if {![regexp -nocase [stc::get $linktarget -linkdstdevice-Targets] $miprouter]} {
                append miprouter [stc::get $linktarget -linkdstdevice-Targets] " "
            }
        }
    }
    
    #count the mipcount the mepcount
    set mipcount [llength $miprouter]
    set mepcount [expr [llength $eoamrouterList] - $mipcount]

    set eoamnodeconfig [stc::get $device -children-$class]
    set eoamnodeconfig [lindex $eoamnodeconfig 0]
    set table_name "::sth::Eoam::EoamTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_oam_config_topology"
    
    set meprouters ""
    foreach routertemp $meprouter {
        if {![regexp -nocase $routertemp $miprouter]} {
            append meprouters $routertemp " "
        }
        
    }
    set routerselected [lindex $meprouters 0]
    if {[llength $meprouters] >= 2} {
        #find the mep_id and mep_id_step, also add mep_id_incr_mode
        set meprouter1 [lindex $meprouters 0]
        set meprouter2 [lindex $meprouters 1]
        set ::sth::Eoam::emulation_oam_config_topology_stcobj(mep_id) "_none_"
        set eoamnodeconfig1 [stc::get $meprouter1 -children-eoamnodeconfig]
        set eoammegconfig1 [stc::get [stc::get $eoamnodeconfig1 -children-eoammaintenancepointconfig]  -megassociation-Targets]
        set eoamremotemegendpointconfigList [stc::get $eoammegconfig1 -children-eoamremotemegendpointconfig]
        if {[llength $eoamremotemegendpointconfigList] >= 3} {
            set eoamremotemegendpointconfig1 [lindex $eoamremotemegendpointconfigList 0]
            set mip_id1 [stc::get $eoamremotemegendpointconfig1 -RemoteMegEndPointId]
            set eoamremotemegendpointconfig1 [lindex $eoamremotemegendpointconfigList 0]
            set mac_remote1 [stc::get $eoamremotemegendpointconfig1 -RemoteMacAddr]
            set mac_remote1 [join [split $mac_remote1 "-"] ":"]
            append childrenparams "			-mep_id			    $mip_id1\\\n"
            append childrenparams "			-mac_remote	            $mac_remote1\\\n"
    
            
            #set eoamnodeconfig2 [stc::get $meprouter2 -children-eoamnodeconfig]
            #set eoammegconfig2 [stc::get [stc::get $eoamnodeconfig2 -children-eoammaintenancepointconfig]  -megassociation-Targets]
            set eoamremotemegendpointconfig2 [lindex $eoamremotemegendpointconfigList 1]
            set mip_id2 [stc::get $eoamremotemegendpointconfig2 -RemoteMegEndPointId]
            set eoamremotemegendpointconfig1 [lindex $eoamremotemegendpointconfigList 1]
            set mac_remote1 [stc::get $eoamremotemegendpointconfig1 -RemoteMacAddr]
            set mac_remote1 [join [split $mac_remote1 "-"] ":"]
            set eoamremotemegendpointconfig2 [lindex $eoamremotemegendpointconfigList 2]
            set mac_remote2 [stc::get $eoamremotemegendpointconfig2 -RemoteMacAddr]
            set mac_remote2 [join [split $mac_remote2 "-"] ":"]
            append childrenparams "			-mep_id_incr_mode			    increment\\\n"
            append childrenparams "			-mep_id_step			    [::sth::hlapiGen::calculate_difference $mip_id1 $mip_id2 ""]\\\n"
            append childrenparams "			-mac_remote_incr_mode			    increment\\\n"
            append childrenparams "			-mac_remote_step			    [::sth::hlapiGen::calculate_difference $mac_remote1 $mac_remote2 ""]\\\n"
        }
    } else {
        #only get mep_id by eoamnodeconfigsel
        set ::sth::Eoam::emulation_oam_config_topology_stcobj(mep_id) "_none_"
        set eoammegconfigsel [stc::get [stc::get $eoamnodeconfig -children-eoammaintenancepointconfig]  -megassociation-Targets]
        set eoamremotemegendpointconfigsel [stc::get $eoammegconfigsel -children-eoamremotemegendpointconfig]
        append childrenparams "			-mep_id			    [stc::get $eoamremotemegendpointconfigsel -RemoteMegEndPointId]\\\n"
        append childrenparams "			-mac_remote			    [join [split [stc::get $eoamremotemegendpointconfigsel -RemoteMacAddr] "-"] ":"]\\\n"

    }
    
    ###check EoamContChkCommandConfig in MEP router
    set eoamnodeconfigsel [stc::get $routerselected -children-eoamnodeconfig]
    if {[info exists eoamnodeconfigsel]} {
        set childList [stc::get $eoamnodeconfigsel -children]
        if {[regexp -nocase "eoammaintenancepointconfig" $childList]} {
            set eoammaintenancepointconfig [stc::get $eoamnodeconfigsel -children-eoammaintenancepointconfig]
            set eoammaintenancepointconfig [lindex $eoammaintenancepointconfig 0]
        }
    }

    if {[info exists eoammaintenancepointconfig]} {
        set childList [stc::get $eoammaintenancepointconfig]
        if {[regexp -nocase "eoamcontchkcommandconfig" $childList]} {
            set eoamcontchkcommandconfig [stc::get $eoammaintenancepointconfig -children-eoamcontchkcommandconfig]
            set eoamcontchkcommandconfig [lindex $eoamcontchkcommandconfig 0]
            if {[info exists eoamcontchkcommandconfig]} {
                #handle eoamcontchkcommandconfig attr
                get_attr $eoamcontchkcommandconfig $eoamcontchkcommandconfig
                if {"true" eq [set sth::hlapiGen::$eoamcontchkcommandconfig\_$eoamcontchkcommandconfig\_attr(-enablemulticasttarget)]} {
                    append childrenparams "			-continuity_check_mcast_mac_dst			    true\\\n"
                        
                } else {
                    append childrenparams "			-continuity_check_mcast_mac_dst			    false\\\n"
                    set continuity_check_ucast_mac_dst [set sth::hlapiGen::$eoamcontchkcommandconfig\_$eoamcontchkcommandconfig\_attr(-unicasttargetlist)]
                    set continuity_check_ucast_mac_dst [join [split $continuity_check_ucast_mac_dst "-"] ":"]
                    if {$continuity_check_ucast_mac_dst ne ""} {
                        append childrenparams "			-continuity_check_ucast_mac_dst			    $continuity_check_ucast_mac_dst\\\n"
                    }
                }
                #handle continuity_check_burst_size
                append childrenparams "			-continuity_check_burst_size			    [stc::get $eoamcontchkcommandconfig -ContChkBurstSize]\\\n"

            }
        }
    }
    ####
    #get eoammaintenancepointconfig handle
    if {[info exists eoamnodeconfig]} {
    set childList [stc::get $eoamnodeconfig -children]
        if {[regexp -nocase "eoammaintenancepointconfig" $childList]} {
            set eoammaintenancepointconfig [stc::get $eoamnodeconfig -children-eoammaintenancepointconfig]
            set eoammaintenancepointconfig [lindex $eoammaintenancepointconfig 0]
        }
    }

    if {[info exists eoammaintenancepointconfig]} {
        #handle eoammaintenancepointconfig attr
        get_attr $eoammaintenancepointconfig $eoammaintenancepointconfig
        switch -- [set sth::hlapiGen::$eoammaintenancepointconfig\_$eoammaintenancepointconfig\_attr(-rdi)] {
            AUTO -
            ALWAYS_OFF {
                set sth::hlapiGen::$eoammaintenancepointconfig\_$eoammaintenancepointconfig\_attr(-rdi) 1
            }
            ALWAYS_ON {
                set sth::hlapiGen::$eoammaintenancepointconfig\_$eoammaintenancepointconfig\_attr(-rdi) 0
            }
        }
        foreach eoammaintenancepointconfig_obj [array names ::sth::hlapiGen::$eoammaintenancepointconfig\_obj] {
            append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammaintenancepointconfig $eoammaintenancepointconfig $eoammaintenancepointconfig_obj]
        }

        set childList [stc::get $eoammaintenancepointconfig]
        if {[regexp -nocase "megassociation" $childList]} {
            set eoammegconfig [stc::get $eoammaintenancepointconfig -megassociation-Targets]
            if {[info exists eoammegconfig]} {
                #handle eoammegconfig attr
                
                get_attr $eoammegconfig $eoammegconfig
                
                switch -- [set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-megidtype)] {
                    PRIMARY_VID {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-megidtype) "primary_vid"
                        append childrenparams "			-short_ma_name_value			    [stc::get $eoammegconfig -MegId_PrimaryVid]\\\n"
    
                    }
                    STRING {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-megidtype) "char_str"
                        append childrenparams "			-short_ma_name_value			    [stc::get $eoammegconfig -MegId_String]\\\n"
    
                    }
                    INT_2_OCTETS {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-megidtype) "integer"
                        append childrenparams "			-short_ma_name_value			    [format "%d" [stc::get $eoammegconfig -MegId_2Octets]]\\\n"
    
                    }
                    RFC_2685_VPN_ID {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-megidtype) "rfc_2685_vpn_id"
                        append childrenparams "			-short_ma_name_value			    [stc::get $eoammegconfig -MegId_VpnId]\\\n"
    
                    } 
                }
                if {"ITU_T" eq [set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-operationmode)]} {
                    set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-domainidtype) "icc_based"
                } 
                
                switch -- [set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-domainidtype)] {
                    DNS_LIKE {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-domainidtype) "domain_name"
                        append childrenparams "			-md_name			    [stc::get $eoammegconfig -DomainId_DnsLike]\\\n"
    
                    }
                    STRING {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-domainidtype) "char_str"
                        append childrenparams "			-md_name			    [stc::get $eoammegconfig -DomainId_string]\\\n"
    
                    }
                    MAC_2_OCTETS {
                        set sth::hlapiGen::$eoammegconfig\_$eoammegconfig\_attr(-domainidtype) "mac_addr"
                        set md_name [stc::get $eoammegconfig -DomainId_Mac_2Octets]
                        set mdnameList [split $md_name :]
                        set md_mac [lindex $mdnameList 0]
                        set md_integer [lindex $mdnameList 1]
                        set md_mac [join [split $md_mac -] :]
                        append childrenparams "			-md_mac			    $md_mac\\\n"
                        append childrenparams "			-md_integer			    $md_integer\\\n"

                    }
                    icc_based {
                        append childrenparams "			-md_name			    [stc::get $eoammegconfig -MegId_IccString]\\\n"

                    }
                    
                }
                
                set ::sth::Eoam::emulation_oam_config_topology_stcobj(md_mac) "_none_"
                set ::sth::Eoam::emulation_oam_config_topology_stcobj(md_integer) "_none_"
                set ::sth::Eoam::emulation_oam_config_topology_stcobj(domain_level) "_none_"
                
                foreach eoammegconfig_obj [array names ::sth::hlapiGen::$eoammegconfig\_obj] {
                    append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammegconfig $eoammegconfig $eoammegconfig_obj]
                }
				set sth::hlapiGen::device_ret($eoammegconfig) $hlt_ret
            }
        }
    }

    ###
    
    #get port
    set port [stc::get $device -affiliationport-Targets]
    set port $::sth::hlapiGen::port_ret($port)
    
    set hlapi_script ""
    append hlapi_script "      set $hlt_ret \[sth::$cmd_name\\\n"
    append hlapi_script "			-mode			    $mode\\\n"
    append hlapi_script "			-mip_count			    $mipcount\\\n"
    append hlapi_script "			-mep_count			    $mepcount\\\n"
    append hlapi_script "			-port_handle			     \"$port\"\\\n"
    append hlapi_script $childrenparams
    append hlapi_script "\]\n"
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
    
}
proc ::sth::hlapiGen::hlapi_gen_device_eoam {device class mode hlt_ret cfg_args first_time} {

    #can't handle the mode enable, add it for topology
    if {$first_time == 0} {
        return
    }
    #check whether contains eoamlink
    if {[regexp -nocase "eoamlink" [stc::get $device]]} {
        hlapi_gen_device_eoam_topo $device $class $mode $hlt_ret $cfg_args $first_time
        return    
    }
    set eoamnodeconfig [stc::get $device -children-$class]
    set eoamnodeconfig [lindex $eoamnodeconfig 0]
    set table_name "::sth::Eoam::EoamTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_oam_config_msg"
    
    if {[regexp -nocase "EmulatedDevice" $device]} {
        set ::sth::Eoam::emulation_oam_config_msg_stcobj(count) "EmulatedDevice"
    }
    
    set childlist [stc::get $device -children]
    foreach child $childlist {
        if {[regexp -nocase "ethiiif" $child]} {
            if {[info exists sth::hlapiGen::$device\_$child\_attr(-sourcemac.step)]} {
                append childrenparams "			-mac_local_incr_mode			    increment\\\n"    
            }
        }    
    }
    
    set msg_type test

    #get eoammaintenancepointconfig handle
    if {[info exists eoamnodeconfig]} {
    set childList [stc::get $eoamnodeconfig -children]
        if {[regexp -nocase "eoammaintenancepointconfig" $childList]} {
            set eoammaintenancepointconfig [stc::get $eoamnodeconfig -children-eoammaintenancepointconfig]
            set eoammaintenancepointconfig [lindex $eoammaintenancepointconfig 0]
        }
    }

    if {[info exists eoammaintenancepointconfig]} {
        #handle eoammaintenancepointconfig attr
        get_attr $eoammaintenancepointconfig $eoammaintenancepointconfig
        foreach eoammaintenancepointconfig_obj [array names ::sth::hlapiGen::$eoammaintenancepointconfig\_obj] {
            append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammaintenancepointconfig $eoammaintenancepointconfig $eoammaintenancepointconfig_obj]
        }

        set childList [stc::get $eoammaintenancepointconfig]
        if {[regexp -nocase "megassociation" $childList]} {
            set eoammegconfig [stc::get $eoammaintenancepointconfig -megassociation-Targets]
            if {[info exists eoammegconfig]} {
                #handle eoammegconfig attr
                get_attr $eoammegconfig $eoammegconfig
                if {$::sth::hlapiGen::md_level_step ne ""} {
                    append childrenparams  $::sth::hlapiGen::md_level_step
                    append childrenparams "			-md_level_incr_mode			    increment\\\n"    

                    set ::sth::hlapiGen::md_level_step ""
                }
                foreach eoammegconfig_obj [array names ::sth::hlapiGen::$eoammegconfig\_obj] {
                    append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammegconfig $eoammegconfig $eoammegconfig_obj]
                }
            }

        }
        if {[regexp -nocase "eoamlinktracecommandconfig" $childList]} {
            set eoamlinktracecommandconfig [stc::get $eoammaintenancepointconfig -children-eoamlinktracecommandconfig]
            set eoamlinktracecommandconfig [lindex $eoamlinktracecommandconfig 0]
            if {[info exists eoamlinktracecommandconfig]} {
                #prepare the stcobj for trans_id/dst_addr_type/mac_dst
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(trans_id) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(trans_id_step) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(dst_addr_type) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(mac_dst) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(mac_dst_step) "EoamLinkTraceCommandConfig"
                #prepare the stcobj for transmit_mode/pkts_per_burst/rate_pps
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(transmit_mode) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(pkts_per_burst) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(rate_pps) "EoamLinkTraceCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcattr(transmit_mode) "LinkTraceTxType"
                set ::sth::Eoam::emulation_oam_config_msg_stcattr(pkts_per_burst) "LinkTraceBurstSize"
                set ::sth::Eoam::emulation_oam_config_msg_stcattr(rate_pps) "LinkTraceBurstRate"

                #save msg_type
                set msg_type linktrace
                #handle eoamlinktracecommandconfig attr
                #get_attr $eoamlinktracecommandconfig $eoamlinktracecommandconfig
                #handle transmit_mode set single_msg|multiple_msg to single_pkt
                if {[set sth::hlapiGen::$eoammaintenancepointconfig\_$eoamlinktracecommandconfig\_attr(-linktracetxtype)] ne "CONTINUOUS"} {
                    set sth::hlapiGen::$eoammaintenancepointconfig\_$eoamlinktracecommandconfig\_attr(-linktracetxtype) single_pkt
                }
                if {[info exists sth::hlapiGen::$eoammaintenancepointconfig\_$eoamlinktracecommandconfig\_attr(-unicasttargetlist.step)]} {
                    append childrenparams "			-mac_dst_incr_mode			    increment\\\n"    
                }
                if {[info exists sth::hlapiGen::$eoammaintenancepointconfig\_$eoamlinktracecommandconfig\_attr(-initialtransactionid.step)]} {
                    append childrenparams "			-trans_id_incr_mode			    increment\\\n"    
                }
                append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammaintenancepointconfig $eoamlinktracecommandconfig eoamlinktracecommandconfig]
            }

        }
        if {[regexp -nocase "eoamloopbackcommandconfig" $childList]} {
            set eoamloopbackcommandconfig [stc::get $eoammaintenancepointconfig -children-eoamloopbackcommandconfig]
            set eoamloopbackcommandconfig [lindex $eoamloopbackcommandconfig 0]
            if {[info exists eoamloopbackcommandconfig]} {
                #prepare the stcobj for trans_id/dst_addr_type/mac_dst
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(trans_id) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(trans_id_step) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(dst_addr_type) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(mac_dst) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(mac_dst_step) "EoamLoopbackCommandConfig"
                #prepare the stcobj for transmit_mode/pkts_per_burst/rate_pps
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(transmit_mode) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(pkts_per_burst) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcobj(rate_pps) "EoamLoopbackCommandConfig"
                set ::sth::Eoam::emulation_oam_config_msg_stcattr(transmit_mode) "LoopbackTxType"
                set ::sth::Eoam::emulation_oam_config_msg_stcattr(pkts_per_burst) "LoopbackBurstSize"
                set ::sth::Eoam::emulation_oam_config_msg_stcattr(rate_pps) "LoopbackBurstRate"

                #save msg_type
                set msg_type loopback
                set LbmOptionalTlvs [stc::get $eoammaintenancepointconfig -LbmOptionalTlvs]
                if {[regexp -nocase "TestTLV" $LbmOptionalTlvs]} {
                    set msg_type test
                }

                if {[info exists sth::hlapiGen::$eoammaintenancepointconfig\_$eoamloopbackcommandconfig\_attr(-unicasttargetlist.step)]} {
                    append childrenparams "			-mac_dst_incr_mode			    increment\\\n"    
                }
                if {[info exists sth::hlapiGen::$eoammaintenancepointconfig\_$eoamloopbackcommandconfig\_attr(-initialtransactionid.step)]} {
                    append childrenparams "			-trans_id_incr_mode			    increment\\\n"    
                }

                #handle transmit_mode set single_msg|multiple_msg to single_pkt
                if {[set sth::hlapiGen::$eoammaintenancepointconfig\_$eoamloopbackcommandconfig\_attr(-loopbacktxtype)] ne "CONTINUOUS"} {
                    set sth::hlapiGen::$eoammaintenancepointconfig\_$eoamloopbackcommandconfig\_attr(-loopbacktxtype) single_pkt
                }
                
                append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammaintenancepointconfig $eoamloopbackcommandconfig eoamloopbackcommandconfig]
                
            }

        }
        if {[regexp -nocase "eoamcontchkcommandconfig" $childList]} {
            set eoamcontchkcommandconfig [stc::get $eoammaintenancepointconfig -children-eoamcontchkcommandconfig]
            set eoamcontchkcommandconfig [lindex $eoamcontchkcommandconfig 0]
            if {[info exists eoamcontchkcommandconfig]} {
                #handle eoamcontchkcommandconfig attr
                get_attr $eoamcontchkcommandconfig $eoamcontchkcommandconfig
                foreach eoamcontchkcommandconfig_obj [array names ::sth::hlapiGen::$eoamcontchkcommandconfig\_obj] {
                    append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoamcontchkcommandconfig $eoamcontchkcommandconfig $eoamcontchkcommandconfig_obj]
                }
            }

        }

        #handle LbmOptionalTlvs and LtmOptionalTlvs
        switch -- $msg_type {
            loopback -
            test {
                set tlv [stc::get $eoammaintenancepointconfig -lbmoptionaltlvs]
            }
            linktrace {
                set tlv [stc::get $eoammaintenancepointconfig -ltmoptionaltlvs]
            }
        }

        append childrenparams [process_tlv_eoam $tlv]

    }

    #get eoamremotemegendpointconfig handle
    if {[info exists eoammegconfig]} {
        set childList [stc::get $eoammegconfig -children]
        if {[regexp -nocase "eoamremotemegendpointconfig" $childList]} {
            set eoamremotemegendpointconfig [stc::get $eoammegconfig -children-eoamremotemegendpointconfig]
            set eoamremotemegendpointconfig [lindex $eoamremotemegendpointconfig 0]
            if {[info exists eoamremotemegendpointconfig]} {
                #handle eoamremotemegendpointconfig attr
                if {[info exists sth::hlapiGen::$eoammegconfig\_$eoamremotemegendpointconfig\_attr(-remotemacaddr.step)]} {
                    append childrenparams "			-mac_remote_incr_mode			    increment\\\n"    
                }
                append childrenparams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $eoammegconfig $eoamremotemegendpointconfig eoamremotemegendpointconfig]
            
            }

        }
    }

        append childrenparams "			-msg_type			    $msg_type\\\n"
        
	hlapi_gen_device_basic $device $class $mode $hlt_ret $childrenparams $first_time

}

proc ::sth::hlapiGen::multi_dev_check_func_eoam {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]
    
    foreach port_obj $update_obj {
        set port_devices $devicelist_obj($port_obj)    
        foreach device $port_devices {
            set eoamnodeconfig [stc::get $device -children-eoamnodeconfig]
            append eoamnodeconfigList $eoamnodeconfig " "
            set childList [stc::get $eoamnodeconfig -children]
            if {[regexp -nocase "eoammaintenancepointconfig" $childList]} {
                set eoammaintenancepointconfig [stc::get $eoamnodeconfig -children-eoammaintenancepointconfig]
                append eoammaintenancepointconfigList $eoammaintenancepointconfig " "
                set eoamchildList [stc::get $eoammaintenancepointconfig]
                if {[regexp -nocase "megassociation" $eoamchildList]} {
                    set eoammegconfig [stc::get $eoammaintenancepointconfig -megassociation-Targets]
                    append eoammegconfigList $eoammegconfig " "
                    
                    set childList [stc::get $eoammegconfig -children]
                    if {[regexp -nocase "eoamremotemegendpointconfig" $childList]} {
                        set eoamremotemegendpointconfig [stc::get $eoammegconfig -children-eoamremotemegendpointconfig]
                        append eoamremotemegendpointconfigList $eoamremotemegendpointconfig " "
                    }
                }
                if {[regexp -nocase "eoamlinktracecommandconfig" $eoamchildList]} {
                    set eoamlinktracecommandconfig [stc::get $eoammaintenancepointconfig -children-eoamlinktracecommandconfig]
                    set class "eoamlinktracecommandconfig"
                    append eoamlinktracecommandconfigList $eoamlinktracecommandconfig " "
                    set deviceList $eoamlinktracecommandconfigList
                }
                if {[regexp -nocase "eoamloopbackcommandconfig" $eoamchildList]} {
                    set eoamloopbackcommandconfig [stc::get $eoammaintenancepointconfig -children-eoamloopbackcommandconfig]
                    set class "eoamloopbackcommandconfig"
                    append eoamloopbackcommandconfigList $eoamloopbackcommandconfig " "
                    set deviceList $eoamloopbackcommandconfigList
                }    
            }
        }
        
        set attrlist "UnicastTargetList"
        #set class "EoamLoopbackCommandConfig"
        update_step $class $eoammaintenancepointconfigList $attrlist ""
        
        set attrlist "InitialTransactionId"
        #set class "EoamLoopbackCommandConfig"
        update_step $class $eoammaintenancepointconfigList $attrlist ""
        
        set attrlist "RemoteMacAddr"
        set class "eoamremotemegendpointconfig"
        for {set i 0} {$i < [llength $eoammegconfigList]} {incr i} {
            get_attr [lindex $eoammegconfigList $i] [stc::get [lindex $eoammegconfigList $i] -children-eoamremotemegendpointconfig]
        }
        
        update_step $class $eoammegconfigList $attrlist ""
   
        set attrlist "melevel"
        set handle1 [lindex $eoammegconfigList 0]
        set handle2 [lindex $eoammegconfigList 1]
        set sample1 [stc::get  $handle1 -$attrlist]
        set sample2 [stc::get  $handle2 -$attrlist]
        set step_value [::sth::hlapiGen::calculate_difference $sample1 $sample2 ""]
        variable md_level_step
        set ::sth::hlapiGen::md_level_step "			-md_level_step			    $step_value\\\n"
    }
     
    return $update_obj
}


proc ::sth::hlapiGen::hlapi_gen_device_efm {device class mode hlt_ret cfg_args first_time} {
    
    set linkoamrouterconfig [stc::get $device -children-$class]
    set table_name "::sth::LinkOam::LinkOamTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "emulation_efm_config"
    
    #handle the list for LinkOamVariableResponseConfig/LinkOamVariableRequestConfig/LinkOamOrgSpecificInfoConfig
    set paramList "variable_response_branch variable_response_data variable_response_indication
                   variable_response_leaf variable_response_width variable_request_branch
                   variable_request_leaf osi_enable osi_value osi_oui"
    foreach param $paramList { 
        set $param ""
    }
    foreach childname "linkoamorgspecificinfoconfig linkoamvariablerequestconfig
    linkoamvariableresponseconfig linkoameventnotificationconfig
    linkoamorgspecificconfig linkoamtimersconfig" {
        #handle the parameter from each child
        set childList [stc::get $linkoamrouterconfig -children-$childname]
        if {$childList ne ""} {
            
            if {$childname eq "linkoamvariableresponseconfig"} {
                foreach child $childList {
                    append variable_response_branch     "[join [stc::get $child -Branch] ""] "
                    append variable_response_data       "[join [stc::get $child -DataValue] ""] "
                    set Indication [stc::get $child -Indication]
                    if {$Indication eq "true"} {
                        set  Indication 1   
                    } else {
                        set  Indication 0   
                    }
                    append variable_response_indication "$Indication "
                    append variable_response_leaf       "[join [stc::get $child -Leaf] ""] "
                    append variable_response_width      "[join [stc::get $child -Width] ""] "
                }
                continue
            }
            
            if {$childname eq "linkoamvariablerequestconfig"} {
                foreach child $childList {
                    append variable_request_branch     "[join [stc::get $child -Branch] ""] "
                    append variable_request_leaf       "[join [stc::get $child -Leaf] ""] "
                }
                continue
            }
            
            if {$childname eq "linkoamorgspecificinfoconfig"} {
                foreach child $childList {
                    set ACTIVE [stc::get $child -ACTIVE]
                    if {$ACTIVE eq "true"} {
                        set  ACTIVE 1   
                    } else {
                        set  ACTIVE 0   
                    }
                    append osi_enable "$ACTIVE "
                    append osi_value       "[join [stc::get $child -DataValue] ""] "
                    append osi_oui         "[join [split [stc::get $child -Oui] "-"] ""] "
                }
                continue
            }
            
            set child [lindex $childList 0]
            #handle link_notifications_ose_oui-LinkOamEventNotificationConfig-Oui from xx-xx-xx to xxxxxx
            #handle osi_oui-LinkOamOrgSpecificInfoConfig-Oui from xx-xx-xx to xxxxxx
            #handle organization_specific_event_oui-LinkOamOrgSpecificConfig-Oui from xx-xx-xx to xxxxxx
            if {($childname eq "linkoameventnotificationconfig") ||
                ($childname eq "linkoamorgspecificinfoconfig") ||
                ($childname eq "linkoamorgspecificconfig")} {
                set ouival [set ::sth::hlapiGen::$linkoamrouterconfig\_$child\_attr(-oui)]
                set ::sth::hlapiGen::$linkoamrouterconfig\_$child\_attr(-oui) [join [split $ouival "-"] ""]
            }
            
            if {($childname eq "linkoameventnotificationconfig") ||
                ($childname eq "linkoamorgspecificconfig") } {
                set DataValue [set ::sth::hlapiGen::$linkoamrouterconfig\_$child\_attr(-datavalue)]
                set ::sth::hlapiGen::$linkoamrouterconfig\_$child\_attr(-datavalue) [join $DataValue ""]
            }
            
            append cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $linkoamrouterconfig $child $childname]
        }
    }
    
    foreach param $paramList {
        if {[set $param] ne ""} {
            append cfg_args "     -$param    \"[set $param]\"\\\n"
        }
    }
    
    #handle oui_value-LinkOamRouterConfig-Oui from xx-xx-xx to xxxxxx
    set oui_value [set ::sth::hlapiGen::$device\_$linkoamrouterconfig\_attr(-oui)]
    set ::sth::hlapiGen::$device\_$linkoamrouterconfig\_attr(-oui) [join [split $oui_value "-"] ""]
    #handle vsi_value-LinkOamRouterConfig-VendorSpecificInfo from "xxxx xxxx" to xxxxxxxx
    set vsi_value [set ::sth::hlapiGen::$device\_$linkoamrouterconfig\_attr(-vendorspecificinfo)]
    set ::sth::hlapiGen::$device\_$linkoamrouterconfig\_attr(-vendorspecificinfo) [join [split $vsi_value " "] ""]
    
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
                    append cfg_args "     -vlan_outer_id_mode    $vlan_mode\\\n"
                } else {
                    append cfg_args "     -vlan_id_mode    $vlan_mode\\\n"
                }
            } else {
                append cfg_args "     -vlan_id_mode    $vlan_mode\\\n"
            }
        }
    }
    
    #handle revision
    if {[set ::sth::hlapiGen::$device\_$linkoamrouterconfig\_attr(-overriderevision)] eq "false"} {
        set $name_space$cmd_name\_stcobj(revision) "_none_"     
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
    
}

proc ::sth::hlapiGen::hlapi_gen_device_fcoe {device class mode hlt_ret cfg_args first_time} {
       
    set fcoehostconfig [stc::get $device -children-$class]
    set table_name "::sth::fcoe::fcoeTable"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "fcoe_config"

    #handle stcobj for count
    regsub {\d+$} $device "" update_obj
    set $name_space$cmd_name\_stcobj(vnport_count) "$update_obj"
     
    #handle fc_map-fcoehostconfig-FcMap 
    set fc_map [format "%x" [set ::sth::hlapiGen::$device\_$fcoehostconfig\_attr(-fcmap)]]
    set ::sth::hlapiGen::$device\_$fcoehostconfig\_attr(-fcmap) $fc_map
    
    #handle encap
    append cfg_args "     -encap    [::sth::hlapiGen::getencap $device]\\\n"
    
    #get fcglobalconfig from project
    set fcoeglobalparams [stc::get project1 -children-FcoeGlobalParams]
    if {$fcoeglobalparams ne ""} {
    	get_attr $fcoeglobalparams $fcoeglobalparams
    	foreach fcoeglobalparams_obj [array names ::sth::hlapiGen::$fcoeglobalparams\_obj] {
        	append cfg_args [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $fcoeglobalparams $fcoeglobalparams $fcoeglobalparams_obj]
    	}
    }
    
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time 
}

proc ::sth::hlapiGen::hlapi_gen_device_dot1x {device class mode hlt_ret cfg_args first_time} {
    #ip_version
	if {[info exists ::sth::hlapiGen::$device\_obj(ipv6if)]&&[info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        set ip_version ipv4_6
    } elseif {[info exists ::sth::hlapiGen::$device\_obj(ipv6if)]} {
        set ip_version ipv6
    } elseif {[info exists ::sth::hlapiGen::$device\_obj(ipv4if)]} {
        set ip_version ipv4
    } else {
        set ip_version none
    }
    append cfg_args "-ip_version        $ip_version\\\n" 
    #encapsulation
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanif)]} {
        set vlanifs [set ::sth::hlapiGen::$device\_obj(vlanif)]
        
        foreach vlanif $vlanifs {
            set tpid [set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid)]
            set tpid_update [format "0x%04x" $tpid]
            set ::sth::hlapiGen::$device\_$vlanif\_attr(-tpid) $tpid_update
        }
            
        if {[llength $vlanifs] > 1} {
            set encapsulation ethernet_ii_qinq
        } else {
            set encapsulation ethernet_ii_vlan
        }
    } else {
        set encapsulation ethernet_ii
    }
    
    set dot1xblcokconfig [set ::sth::hlapiGen::$device\_obj(dot1xsupplicantblockconfig)]
    set username_password_key ""
    #Dot1xEapMd5Config
    if {[info exists ::sth::hlapiGen::$dot1xblcokconfig\_obj(dot1xeapmd5config)]} {
        set dot1x_md5 [set ::sth::hlapiGen::$dot1xblcokconfig\_obj(dot1xeapmd5config)]
        #username UserId, password Password
        set username [set ::sth::hlapiGen::$dot1xblcokconfig\_$dot1x_md5\_attr(-userid)]
        set password [set ::sth::hlapiGen::$dot1xblcokconfig\_$dot1x_md5\_attr(-password)]
        set username_password_key [concat $username_password_key username password]
        #append cfg_args "-username       $username\\\n"
        #append cfg_args "-password       $password\\\n"
    }
    
    #Dot1xEapFastConfig
    if {[info exists ::sth::hlapiGen::$dot1xblcokconfig\_obj(dot1xeapfastconfig)]} {
        set dot1x_fast [set ::sth::hlapiGen::$dot1xblcokconfig\_obj(dot1xeapfastconfig)]
        #pac_key_file PacKeyFileName
        set pac_key_file [set ::sth::hlapiGen::$dot1xblcokconfig\_$dot1x_fast\_attr(-packeyfilename)]
        
        set username_password_key [concat $username_password_key pac_key_file]
        #append cfg_args "-pac_key_file       $pac_key_file\\\n"
        #append cfg_args "-certificate       $certificate\\\n"
        
    }
    
    if {[info exists ::sth::hlapiGen::$dot1xblcokconfig\_obj(dot1xeaptlsconfig)]} {
        set dot1x_tls [set ::sth::hlapiGen::$dot1xblcokconfig\_obj(dot1xeaptlsconfig)]
        #, certificate Certificate
        set certificate [set ::sth::hlapiGen::$dot1xblcokconfig\_$dot1x_tls\_attr(-certificate)]
         set username_password_key [concat $username_password_key certificate]
    }
    
    #username_wildcard
    #password_wildcard
    #pac_key_file_wildcard
    #certificate_wildcard
    #wildcard_pound_start
    #wildcard_pound_end
    #wildcard_pound_fill
    #wildcard_question_start
    #wildcard_question_end
    #wildcard_question_fill
    #get the @x() in the username and the password
    #{# pound} {? question} {! bang} {$ dollar}
    set pound_list ""
    set question_list ""
    set bang_list ""
    set dollar_list ""
    
    set wildcard_list ""
    set username_password_value ""
    foreach attr $username_password_key {
        if {[info exists $attr] && [regexp {@x\([0-9,]+\)} [set $attr]]} {
            append cfg_args "          -$attr\_wildcard 1\\\n"
            set username_password_value [concat $username_password_value [set $attr]]
        }
    }
    
    while (1) {
        
        if {[regexp {@x\([0-9,]+\)} $username_password_value wildcard]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            
            regsub -all $wildcard $username_password_value "#" username_password_value
            set wildcard_list [concat $wildcard_list $wildcard]
        } else {
            break
        }
    }
    
    if {[llength $wildcard_list]>2} {
        set wildcard_list [lrange $wildcard_list 0 1]
    }
    foreach wildcard $wildcard_list {
        if {[regexp {^$} $pound_list]} {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            
            foreach attr $username_password_key {
                regsub $wildcard [set $attr] "#" $attr
            }
            set cfg_string [process_wildcard pound $wildcard]
            append cfg_args $cfg_string
            set pound_list "#"
            #wildcard_pound_end, wildcard_pound_fill, wildcard_pound_start
        } else {
            set wildcard [join [split $wildcard "\("] "\\("]
            set wildcard [join [split $wildcard "\)"] "\\)"]
            foreach attr $username_password_key {
                regsub $wildcard [set $attr] "?" $attr
            }
            set cfg_string [process_wildcard question $wildcard]
            append cfg_args $cfg_string
            set question_list "?"
            #wildcard_question_end, wildcard_question_start, wildcard_question_fill
        }
    }
    foreach attr $username_password_key {
        append cfg_args "-$attr         [set $attr]\\\n"
    }

    ###############################################################################
    #in the STC version ealier than 4.20, if there is vlan, stc only support the DBD
    #mechanisim to create the vlan, if there is one vlan, only one DBD host will
    #be created, and if there is two vlan, there will be two DBD host
    #curentlly hltapi only support the DBD mechanism to support the vlan on the 8.2.1x
    #if the config on the GUI using the DBD, here need to handle the vlan.
    #VlanSwitchLink
    if {[info exists ::sth::hlapiGen::$device\_obj(vlanswitchlink)]} {
        set name_space "::sth::Dot1x::"
        set cmd_name "emulation_dot1x_config"
        set vlan_link [set ::sth::hlapiGen::$device\_obj(vlanswitchlink)]
        set inner_vlan_host [set ::sth::hlapiGen::$device\_$vlan_link\_attr(-linkdstdevice-targets)]
        set vlanif [lindex [set ::sth::hlapiGen::$inner_vlan_host\_obj(vlanif)] 0]
        set tpid [set ::sth::hlapiGen::$inner_vlan_host\_$vlanif\_attr(-tpid)]
        set tpid_update [format "0x%04x" $tpid]
        set ::sth::hlapiGen::$inner_vlan_host\_$vlanif\_attr(-tpid) $tpid_update
        append cfg_args [config_obj_attr $name_space $cmd_name $inner_vlan_host $vlanif vlanif]
        set encapsulation "ethernet_ii_vlan"
        if {[info exists ::sth::hlapiGen::$inner_vlan_host\_obj(vlanswitchlink)]} {
            set vlan_link_outer [set ::sth::hlapiGen::$inner_vlan_host\_obj(vlanswitchlink)]
            set outer_vlan_host [set ::sth::hlapiGen::$inner_vlan_host\_$vlan_link_outer\_attr(-linkdstdevice-targets)]
            set vlanif_outer [lindex [set ::sth::hlapiGen::$outer_vlan_host\_obj(vlanif)] 0]
            set tpid [set ::sth::hlapiGen::$outer_vlan_host\_$vlanif_outer\_attr(-tpid)]
            set tpid_update [format "0x%04x" $tpid]
            set ::sth::hlapiGen::$outer_vlan_host\_$vlanif_outer\_attr(-tpid) $tpid_update
            append cfg_args [config_obj_attr $name_space $cmd_name $outer_vlan_host $vlanif_outer vlanif_outer]
            set encapsulation "ethernet_ii_qinq"
        }
    }
    append cfg_args "-encapsulation     $encapsulation\\\n"
    hlapi_gen_device_basic $device $class $mode $hlt_ret $cfg_args $first_time
}

proc ::sth::hlapiGen::multi_dev_check_func_ancp {class devices} {
    variable devicelist_obj
    
    set update_obj [multi_dev_check_func_basic $class $devices]
    
    set attrlist "StartIpList"
    foreach obj $update_obj {
        if {[info exists devicelist_obj($obj)]} {
            set device_list $devicelist_obj($obj)
            set device1 [lindex $device_list 0]
            set device2 [lindex $device_list 1]
            set ancpconfig1 [stc::get $device1 -children-AncpAccessNodeConfig]
            set ancpconfig2 [stc::get $device2 -children-ancpaccessnodeconfig]
            set obj_list [concat $ancpconfig1 $ancpconfig2]
            update_step ipv4networkblock $obj_list $attrlist ""
        }
    }
    return $update_obj
}
