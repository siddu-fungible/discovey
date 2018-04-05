namespace eval ::sth::hlapiGen:: {
    #some global variabl for hlapiGenTraffic
    variable hlapi_traffic_script
    variable hlapi_traffic_script_var
    variable traffic_headers_array
    variable vlan_outer_hdl
    variable vlan_other_hdl
    variable ip_outer_hdl_list
    variable l4_ip_hdl_list
    variable traffic_config_ospf_params
    variable ospf_update_router_lsa_link
    variable ospf_update_router_lsa_tos
    variable ospf_update_summary_lsa_tos
    variable ospf_update_asexternal_lsa_tos
    variable ipheader_gre
    variable traffic_config_igmpv3report_params
    variable traffic_config_mpls
    variable traffic_config_mpls_count
    variable traffic_config_mpls_count_flag
    variable traffic_ret
    variable ipprotocol_map
}

array set ::sth::hlapiGen::ipprotocol_map {
        HOPOPT 0
        ICMP 1
        IGMP 2
        GGP 3
        IPV4 4
        ST 5
        TCP 6
        CBT 7
        EGP 8
        IGP 9
        BBN-RCC-MON 10
        NVP-II 11
        PUP 12
        ARGUS 13
        EMCON 14
        XNET 15
        CHAOS 16
        UDP 17
        MUX 18
        DCN-MEAS 19
        HMP 20
        PRM 21
        XNS-IDP 22
        TRUNK-1 23
        TRUNK-2 24
        LEAF-1 25
        LEAF-2 26
        RDP 27
        IRTP 28
        ISO-TP4 29
        NETBLT 30
        MFE-NSP 31
        MERIT-INP 32
        SEP 33
        3PC 34
        IDPR 35
        XTP 36
        DDP 37
        IDPR-CMTP 38
        TP++ 39
        IL 40
        IPV6 41
        SDRP 42
        IPV6-ROUTE 43
        IPV6-FRAG 44
        IDRP 45
        RSVP 46
        GRE 47
        MHRP 48
        BNA 49
        ESP 50
        AH 51
        I-NLSP 52
        SWIPE 53
        NARP 54
        MOBILE 55
        TLSP 56
        SKIP 57
        IPV6-ICMP 58
        IPV6-NONXT 59
        IPV6-OPTS 60
        CFTP 62
        SAT-EXPAK 64
        KRYPTOLAN 65
        RVD 66
        IPPC 67
        SAT-MON 69
        VISA 70
        IPCV 71
        CPNX 72
        CPHB 73
        WSN 74
        PVP 75
        BR-SAT-MON 76
        SUN-ND 77
        WB-MON 78
        WB-EXPAK 79
        ISO-IP 80
        VMTP 81
        SECURE-VMTP 82
        VINES 83
        TTP 84
        NSFNET-IGP 85
        DGP 86
        TCF 87
        EIGRP 88
        OSPFV2 89
        Sprite-RPC 90
        LARP 91
        MTP 92
        AX.25 93
        IPIP 94
        MICP 95
        SCC-SP 96
        ETHERNET 97
        ENCAP 98
        GMTP 100
        IFMP 101
        PNNI 102
        PIM 103
        ARIS 104
        SCPS 105
        QNX 106
        A/N 107
        IPComp 108
        SNP 109
        COMPAQ-PEER 110
        IPX-IN-IP 111
        VRRP 112
        PGM 113
        L2TP 115
        DDX 116
        IATP 117
        STP 118
        SRP 119
        UTI 120
        SMP 121
        SM 122
        PTP 123
        ISIS-OVER-IPV4 124
        FIRE 125
        CRTP 126
        CRUDP 127
        SSCOPMCE 128
        IPLT 129
        SPS 130
        PIPE 131
        SCTP 132
        FC 133
        RSVP-E2E-IGNORE 134
        MOBILITY-HEADER 135
        UDPLITE 136
        MPLS-IN-IP 137
        Experimental 253
        Reserved 255
    }

#this function is called by framework
proc ::sth::hlapiGen::hlapi_gen_streamblock {strblklist} {
    variable hlapi_traffic_script
    variable hlapi_traffic_script_var
    variable traffic_headers_array
    variable ospf_update_router_lsa_link
    variable ospf_update_router_lsa_tos
    variable ospf_update_summary_lsa_tos
    variable ospf_update_asexternal_lsa_tos
    variable ipheader_gre
    variable traffic_config_igmpv3report_params
    variable traffic_ret
    set index 1
    
    if {[catch {
        set table_name "::sth::Traffic::trafficConfigTable"
        ::sth::sthCore::InitTableFromTCLList [set $table_name]
        
        foreach strblk $strblklist {
            set hlapi_traffic_script ""
            set hlapi_traffic_script_var ""
            set traffic_ret($strblk) streamblock_ret$index
            set port [stc::get $strblk -parent]
            if {[catch {
                traffic_convert $strblk $port $traffic_ret($strblk)
                if {$hlapi_traffic_script_var != ""} {
                    set varList [split $hlapi_traffic_script_var "\n"]
                    foreach tmp $varList {
                        puts_to_file $tmp
                    }
                }
                #Split sth command and status
                set ary [split $hlapi_traffic_script ""]
                set len [string length $hlapi_traffic_script]
                set statusStrIndex [string first "set " $hlapi_traffic_script 4]
                for {set i 0} {$i < $len} {incr i} {
                    append sthStr [lindex $ary $i]
                    if {$i == [expr $statusStrIndex - 1]} {
                        #Sth Command
                        puts_to_file $sthStr
                        set sthStr ""
                        set statusStrIndex [string first "set " $hlapi_traffic_script [expr $i + 3]]
                    }
                }
                #Status
                puts_to_file $sthStr
                set sthStr ""
            } errMsg]} {
                regsub "invoked.*" $::errorInfo "" myerror
                puts_msg "\nFailed to config $strblk! Error message: \n$myerror"
            }
            unset_data_model_attr $strblk
            array unset traffic_headers_array
            array unset ipheader_gre
            array unset traffic_config_igmpv3report_params
            array unset ospf_update_router_lsa_link
            array unset ospf_update_router_lsa_tos
            array unset ospf_update_summary_lsa_tos
            array unset ospf_update_asexternal_lsa_tos
            incr index
        }
        
        unset_table_obj_attr streamblock
           
    } errMsg]} {
        regsub "invoked.*" $::errorInfo "" myerror
        puts_msg "\nFailed to config streamblock! Error message: \n$myerror"
    }
}


#this function is used to handle each streamblock
proc ::sth::hlapiGen::traffic_convert {strblk port traffic_ret} {
    variable hlapi_traffic_script
    variable traffic_headers_array
    set cmd_name "traffic_config"
    
    #1. output the function name
    set port_hdl $::sth::hlapiGen::port_ret($port)
         
    append hlapi_traffic_script "set $traffic_ret \[::sth::traffic_config    \\\n"
    append hlapi_traffic_script "			-mode			        create\\\n"
    append hlapi_traffic_script "			-port_handle			$port_hdl\\\n"
      
    
    #2. set emulation_src_handle and emulation_dst_handle for bound streamblock
    process_bound_stream_handle $strblk $port
    
    #3. set l2_encap, l3_protocol, l3_outer_protocol, l4_protocol values
    process_traffic_header $strblk
    
    foreach header [lsort [array names traffic_headers_array]] {
        set header_value $traffic_headers_array($header)
        if {$header_value != ""} {
            append hlapi_traffic_script "			-$header			$header_value\\\n"
        }
    }
    
    #4.common config for streamblock with correct stcobj and stcattr in the trafficConfigTable.tcl file
    #get the streamblock obj and attr info
    #add the "streamblock" in the streamblock list and set streamblock attribute list
    array set ::sth::hlapiGen::$strblk\_$strblk\_attr [array get ::sth::hlapiGen::$port\_$strblk\_attr]
    array set ::sth::hlapiGen::$strblk\_obj "streamblock $strblk"
    
    #5. pre process the traffic config obj and attr to adjust the datamodel info
    pre_process_obj_attr $strblk
    
    #6. config the obj and attr by mapping the datamodel and table file
    traffic_config_obj_attr $cmd_name $strblk
    
    #7. handle the specific obj and attr
    traffic_config_specific_obj_attr $cmd_name $strblk $port
    
    append hlapi_traffic_script "\]\n"
    append hlapi_traffic_script [gen_status_info_without_puts $traffic_ret "sth::$cmd_name"]
    #8. handle the specific header (for example: ospf header) which is not under traffic_config
    traffic_config_specific_function $strblk $traffic_ret
}



#this function is used to update the obj and attr before configuring
proc ::sth::hlapiGen::pre_process_obj_attr {strblk} {
    variable traffic_headers_array
    variable vlan_outer_hdl ""
    variable vlan_other_hdl ""
    variable ip_outer_hdl_list ""
    variable l4_ip_hdl_list ""
    #set modifier_ip_tos_list ""
    set l2_encap $traffic_headers_array(l2_encap)
    set l3_protocol $traffic_headers_array(l3_protocol)
    set l3_outer_protocol $traffic_headers_array(l3_outer_protocol)
    set l4_protocol $traffic_headers_array(l4_protocol)
    #check if the table modifier exists under streamblock, below operations can't be used for tosdiffserv
    set str [array get ::sth::hlapiGen::$strblk\_obj]
    if {[regexp "tablemodifier" $str]} {
        set hdl_list [set ::sth::hlapiGen::$strblk\_obj(tablemodifier)]
        #update the attr value
        foreach modifier_hdl $hdl_list {
            set offset_refer [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-offsetreference)]
            if {[regexp -nocase "tosdiffserv" $offset_refer]} {
                process_tos_modifier $strblk $modifier_hdl $offset_refer
            } else {
                set update_value [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-data)]
                regsub {^.*\.} [string tolower $offset_refer] "" arg
                regsub ".$arg" [string tolower $offset_refer] "" update_name
                if {[string first "." $update_name] >= 0} {
                    regsub {^.*\.} $update_name "" name
                } else {
                    set name $update_name
                }
                
                set hdl [get_handle_by_name $strblk $name]
                set phdl [stc::get $hdl -parent]
                set ::sth::hlapiGen::$phdl\_$hdl\_attr(-$arg) $update_value
            }
        }
    }
    
    #update the offset reference for the modifier of vlan outer
    if {[regexp "vlan" $l2_encap] || $l2_encap == "ethernet_ii_qinq_pppoe"} {
        foreach obj_child [array names ::sth::hlapiGen::$strblk\_obj] {
            if {[regexp -nocase "ethernet" $obj_child]} {
                set eth_hdl [set ::sth::hlapiGen::$strblk\_obj($obj_child)]
                foreach tempEthhdl $eth_hdl {
                    set vlans [set ::sth::hlapiGen::$tempEthhdl\_obj(vlans)]
                    if {[info exists ::sth::hlapiGen::$vlans\_obj(vlan)] &&
                        [llength [set ::sth::hlapiGen::$vlans\_obj(vlan)]] > 1} {
                        #the first handle is the outer header handle
                        set len [llength [set ::sth::hlapiGen::$vlans\_obj(vlan)]]
                        set outer_index [expr $len - 2]
                        set vlan_outer_hdl [lindex [set ::sth::hlapiGen::$vlans\_obj(vlan)] $outer_index]
                        set name [set ::sth::hlapiGen::$vlans\_$vlan_outer_hdl\_attr(-name)]
                        process_modifier_offsetrefer $strblk $name "vlanOuter"
                        set vlan_len [llength [set ::sth::hlapiGen::$vlans\_obj(vlan)]]
                        if {$vlan_len > 2} {
                            set other_index [expr $len - 3]
                            set vlan_other_hdl [lrange [set ::sth::hlapiGen::$vlans\_obj(vlan)] 0 $other_index]
                            #the last one should be the inner one
                            set vlan_other_inner [lindex [set ::sth::hlapiGen::$vlans\_obj(vlan)] $other_index]
                            set name_list ""
                            for {set i [expr [llength $vlan_other_hdl] - 1]} {$i >=0} {incr i -1} {
                                #the last one should be the inner one
                                if {[lindex $vlan_other_hdl $i] != $vlan_other_inner} {
                                    foreach vlan_attr [array names ::sth::hlapiGen::$vlans\_$vlan_other_inner\_attr] {
                                        if {[regexp "pri|cfi|id" $vlan_attr]} {
                                            set ::sth::hlapiGen::$vlans\_$vlan_other_inner\_attr($vlan_attr) [concat [set ::sth::hlapiGen::$vlans\_$vlan_other_inner\_attr($vlan_attr)] [set ::sth::hlapiGen::$vlans\_[lindex $vlan_other_hdl $i]\_attr($vlan_attr)]]
                                        }
                                    }
                                }
                                set name [set ::sth::hlapiGen::$vlans\_[lindex $vlan_other_hdl $i]\_attr(-name)]
                                set name_list [concat $name_list $name]
                            }
                            set vlan_other_hdl $vlan_other_inner
                            set ::sth::hlapiGen::$vlans\_obj(vlan) [concat $vlan_other_hdl [lrange [set ::sth::hlapiGen::$vlans\_obj(vlan)] [expr $vlan_len - 2] [expr $vlan_len - 1]]]
                            set name [set ::sth::hlapiGen::$vlans\_$vlan_other_inner\_attr(-name)]
                            process_modifier_offsetrefer $strblk $name_list "vlanOther"
                        }

                    }
                }
                break
            }
        }
    }
    
    if {$l3_outer_protocol != ""} {
        switch -regexp -- $l3_outer_protocol {
            ipv4 {
                set proto_type "ipv4:ipv"
            }
            ipv6 {
                set proto_type "ipv6:ipv"
            }
        }
        if {$l3_protocol == $l3_outer_protocol} {
            set ip_outer_hdl [lindex [set ::sth::hlapiGen::$strblk\_obj($proto_type)] 0]
        } else {
            set ip_outer_hdl [lindex [set ::sth::hlapiGen::$strblk\_obj($proto_type)] 0]
        }
        #get all the sub obj of outer header
        append ip_outer_hdl_list " $ip_outer_hdl"
        append ip_outer_hdl_list [get_sub_obj $ip_outer_hdl]
        set name [set ::sth::hlapiGen::$strblk\_$ip_outer_hdl\_attr(-name)]
        process_modifier_offsetrefer $strblk $name $proto_type
    }
    

    #if tos has been handled by modifier mode, there is no need to handle again
    if {$l3_protocol != ""} {
        foreach obj [array names ::sth::hlapiGen::$strblk\_obj] {
            if {[regexp -nocase "ip" $obj]} {
                foreach ip_hdl [set ::sth::hlapiGen::$strblk\_obj($obj)] {
                    if {[info exist ::sth::hlapiGen::$ip_hdl\_obj(tosdiffserv)] && [lsearch $ip_outer_hdl_list $ip_hdl] < 0} {
                        #currently there is no parameters to config tos of ip outer header in hlatp 
                        process_tos_diffserve [set ::sth::hlapiGen::$ip_hdl\_obj(tosdiffserv)] ""
                    }
                }
            }
            if {$l3_protocol == "arp" && [regexp -nocase "arp" $obj]} {
                #need to process the ip_src_addr, ip_dst_addr,
                foreach attr "ip_src_addr ip_dst_addr" {
                    set ::sth::Traffic::traffic_config_stcobj($attr) $obj
                }
                set ::sth::Traffic::traffic_config_stcattr(ip_dst_addr) "senderpaddr"
                set ::sth::Traffic::traffic_config_stcattr(ip_src_addr) "targetpaddr"
                #ip_dst_mode ip_dst_step ip_dst_count ip_src_mode ip_src_step ip_src_count
                foreach attr "ip_dst_mode ip_dst_step ip_dst_count" {
                    set ::sth::Traffic::traffic_config_stcobj($attr) "arp.targetpaddr"
                }
                foreach attr "ip_src_mode ip_src_step ip_src_count" {
                    set ::sth::Traffic::traffic_config_stcobj($attr) "arp.senderpaddr"
                }
            }
        }
    }
    
    if {$l4_protocol != ""} {
        foreach obj [array names ::sth::hlapiGen::$strblk\_obj] {
            if {[regexp -nocase "igmp" $obj]} {
                foreach igmp_hdl [set ::sth::hlapiGen::$strblk\_obj($obj)] {
                    process_igmp_attr $strblk $obj $igmp_hdl
                }
            } elseif {[regexp -nocase "$l4_protocol" $obj] && [regexp -nocase "ip" $l4_protocol]} {
                switch -regexp -- $l4_protocol {
                    ipv4 {
                        set proto_type "ipv4:ipv"
                    }
                    ipv6 {
                        set proto_type "ipv6:ipv"
                    }
                }
                set l4_ip_hdl [lindex [set ::sth::hlapiGen::$strblk\_obj($proto_type)] end]
                append l4_ip_hdl_list $l4_ip_hdl
                append l4_ip_hdl_list [get_sub_obj $l4_ip_hdl]
                set name [set ::sth::hlapiGen::$strblk\_$l4_ip_hdl\_attr(-name)]
                process_modifier_offsetrefer $strblk $name "$proto_type\_l4"
            }
        }
    }
    
    #need to check if the current header number is more than the limitation of hltapi
    foreach obj [array names ::sth::hlapiGen::$strblk\_obj] {
        switch -- $obj {
            "ipv4:ipv" -
            "ipv6:ipv" {
                if {[llength [set ::sth::hlapiGen::$strblk\_obj($obj)]] > 3} {
                    set ::sth::hlapiGen::$strblk\_obj($obj) [lrange [set ::sth::hlapiGen::$strblk\_obj($obj)] 0 2]
                }
            }
            "mpls:mpls" {
                if {[llength [set ::sth::hlapiGen::$strblk\_obj($obj)]] > 1} {
                    set ::sth::hlapiGen::$strblk\_obj($obj) [lrange  [set ::sth::hlapiGen::$strblk\_obj($obj)] 0 end]
                }
            }
            "fc:fcoeheader" {
                if {[regexp -nocase "custom:custom" [stc::get $strblk -children]]} {
                    set ::sth::Traffic::traffic_config\_stcattr(custom_pattern) "_none_"
                }
            }
        }
    }
}
#this funciton is used to config the obj and attr recursively 
proc ::sth::hlapiGen::traffic_config_obj_attr {cmd_name phdl} {
    variable hlapi_traffic_script
    variable ipheader_gre
    variable traffic_config_mpls_count
    variable traffic_config_mpls_count_flag
    variable traffic_config_mpls
    variable vlan_other_hdl
    set traffic_config_mpls_count 0
    set control_flag 1
    foreach obj [array names ::sth::hlapiGen::$phdl\_obj] {
        set obj_handle [set ::sth::hlapiGen::$phdl\_obj($obj)]
        
        foreach hdl $obj_handle {
            #update the object in some cases
            if {[lsearch [array names ipheader_gre] $hdl] >= 0} {
            #if current ip header is for gre, we use "tunnel handle" instead of configing the attr in trafficconfig
                continue
            }
            #check fc header with/without
            if {[sth::hlapiGen::check_fc_fcoe $phdl $hdl]} {
                continue;
            }
            if {[regexp -nocase "mpls:mpls" $hdl]} {
                incr  traffic_config_mpls_count
            }    
            set obj_new [update_obj $cmd_name $phdl $hdl $obj]
                process_obj_attr "::sth::Traffic::" $cmd_name $phdl $hdl $obj_new
            
            if {[string match -nocase $hdl $phdl]} {
                continue
            }
            if {[info exists ::sth::hlapiGen::$hdl\_obj]} {
                traffic_config_obj_attr $cmd_name $hdl
            }
            if {$traffic_config_mpls_count_flag==$traffic_config_mpls_count &&  $control_flag} {
                set name_index [array names traffic_config_mpls]
                foreach id $name_index {
                    if {$traffic_config_mpls_count==1} {
                        regsub -all "\{" $traffic_config_mpls($id) "" traffic_config_mpls($id)
                        regsub -all "\}" $traffic_config_mpls($id) "" traffic_config_mpls($id)
                        append hlapi_traffic_script "			-$id			$traffic_config_mpls($id)\\\n"
                    } else {
                        append hlapi_traffic_script "			-$id			\{$traffic_config_mpls($id)\}\\\n"
                    }
                }
                set control_flag 0
                array unset traffic_config_mpls 
                set traffic_config_mpls_count  0
                set traffic_config_mpls_count_flag 0
  
            } 
        }
        
    }
    
}

#this function checks if fc header is with fcoe header then it returns status as 1
#and if fc header is without fcoe header then returns status as 0
proc ::sth::hlapiGen::check_fc_fcoe {phdl hdl} {
        
        set status 0
        if {[info exists ::sth::hlapiGen::$phdl\_obj]} {
            if {[regexp -nocase {fc:fc\d+} $hdl]} {
                foreach hnd [array names ::sth::hlapiGen::$phdl\_obj] {
                    if {[regexp -nocase "fc:fcoe" $hnd]} {
                        set status 1
                    }
                }
            } else {
                set status 0
            }
        }
        return $status
}

#this function is used to process some specific stcobj and stcattr
#eg: 1.FrameLengthDistribution (parent: project) 2.GeneratorConfig(port->generator->generatorconfig)...
proc ::sth::hlapiGen::traffic_config_specific_obj_attr {cmd_name strblk porthdl} {
    variable hlapi_traffic_script
    variable hlapi_traffic_script_var
    variable ip_outer_hdl_list
    variable traffic_headers_array
    variable ipheader_gre
    variable traffic_config_igmpv3report_params
    variable l4_ip_hdl_list
    set l3_protocol $traffic_headers_array(l3_protocol)
    set l4_protocol $traffic_headers_array(l4_protocol)
    
    #1.FrameLengthDistribution (parent: project)
    #the output value of the l3_length depends on the framelengthmode
    if {[regexp -nocase "imix" [set ::sth::hlapiGen::$strblk\_$strblk\_attr(-framelengthmode)]]} {
        if {[info exists ::sth::hlapiGen::$strblk\_$strblk\_attr(-affiliationframelengthdistribution-targets)]} {
            set index 1
            set framelength_distri [set ::sth::hlapiGen::$strblk\_$strblk\_attr(-affiliationframelengthdistribution-targets)]
            set framelength_distri_slot_list [stc::get $framelength_distri -children]
            foreach framelength_distri_slot $framelength_distri_slot_list {
                if {$index > 4} {
                    break
                }
                set arg_ratio "l3_imix$index\_ratio"
                set value_ratio [stc::get $framelength_distri_slot -Weight]
                set arg_size "l3_imix$index\_size"
                set value_size [stc::get $framelength_distri_slot -FixedFrameLength]
                append hlapi_traffic_script "			-$arg_ratio			$value_ratio\\\n"
                append hlapi_traffic_script "			-$arg_size			$value_size\\\n"
                incr index
            }
        }
    }
    #2.GeneratorConfig(port->generator->generatorconfig)
    set generator_hdl [set ::sth::hlapiGen::$porthdl\_obj(generator)]
    set generator_cfg_hdl [set ::sth::hlapiGen::$generator_hdl\_obj(generatorconfig)]
    #check if the duration mode is second, if so the duration needs to be configured in traffic_control duration
    if {[info exists ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-durationmode)]} {
        set durationmode [set ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-durationmode)]
        if {[string match -nocase "seconds" $durationmode]} {
            set duration [set ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-duration)]
            array set ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr "-actionduration $duration"
            unset ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-durationmode)
            unset ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-duration)
        }
    }
    process_obj_attr "::sth::Traffic::" $cmd_name $generator_hdl $generator_cfg_hdl "generatorConfig"
    
    #3.config loadunit
    #update StreamBlockLoadProfile options(load and loadunit)
    set sb_load_handle [::sth::sthCore::invoke stc::get $strblk -AffiliationStreamBlockLoadProfile-targets]
    set load_unit [string tolower [::sth::sthCore::invoke stc::get $sb_load_handle -LoadUnit]]
    set value [::sth::sthCore::invoke stc::get $sb_load_handle -Load]
    switch -regexp -- $load_unit {
        "percent_line_rate" {
            set arg "rate_percent"
        }
        "frames_per_second" {
            set arg "rate_pps"
        }
        "bits_per_second" {
            set arg "rate_bps"
            if {[regexp "kilo" $load_unit]} {
				set arg "rate_kbps" 
            }
            if {[regexp "mega" $load_unit]} {
				set arg "rate_mbps"
            }
        }
    }
    append hlapi_traffic_script "			-$arg			$value\\\n"
    
    
   #4. config ipv6 extention header and ipv4 option header
    if {[regexp -nocase "ipv6" $l3_protocol]} {
        set ipv6_extention_headers ""
        foreach ele [array names ::sth::hlapiGen::$strblk\_obj] {
            switch -regexp -- $ele {
                "ipv6:ipv6authenticationheader" {
                    lappend ipv6_extention_headers "authentication"
                }
                "ipv6:ipv6destinationheader" {
                    lappend ipv6_extention_headers "destination"
                    process_ipv6_extention_header_options [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv6destinationheader)] "destination"
                }
                "ipv6:ipv6fragmentheader" {
                    lappend ipv6_extention_headers "fragment"
                }
                "ipv6:ipv6hopbyhopheader" {
                    lappend ipv6_extention_headers "hop_by_hop"
                    process_ipv6_extention_header_options [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv6hopbyhopheader)] "hop_by_hop"
                }
                "ipv6:ipv6routingheader" {
                    set ipv6routingheader_hdl [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv6routingheader)]
                    set ipv6addrlist ""
                    set nodes_hdl [set ::sth::hlapiGen::$ipv6routingheader_hdl\_obj(nodes)]
                    if {[info exists ::sth::hlapiGen::$nodes_hdl\_obj(ipv6addr)]} {
                        foreach ipv6addr_hdl [set ::sth::hlapiGen::$nodes_hdl\_obj(ipv6addr)] {
                            lappend ipv6addrlist [set ::sth::hlapiGen::$nodes_hdl\_$ipv6addr_hdl\_attr(-value)]
                        }
                        append hlapi_traffic_script "-ipv6_routing_node_list $ipv6addrlist \\\n"
                    }
                    lappend ipv6_extention_headers "routing"
                }
            }
        }
        if {$ipv6_extention_headers != ""} {
            append hlapi_traffic_script "-ipv6_extension_header \"$ipv6_extention_headers\" \\\n"
        }
    } elseif {[regexp -nocase "ipv4" $l3_protocol]} {
        foreach ele [set ::sth::hlapiGen::$strblk\_obj(ipv4:ipv)] {
            if {[lsearch $ip_outer_hdl_list $ele] < 0} {
                set option_hdl [set ::sth::hlapiGen::$ele\_obj(options)]
                if {[info exists ::sth::hlapiGen::$option_hdl\_obj(ipv4headeroption)]} {
                    set ipv4headeroption_hdl [set ::sth::hlapiGen::$option_hdl\_obj(ipv4headeroption)]
                    if {[info exists ::sth::hlapiGen::$ipv4headeroption_hdl\_obj(rtralert)]} {
                        set rtralert_hdl [set ::sth::hlapiGen::$ipv4headeroption_hdl\_obj(rtralert)]
                        set type [set ::sth::hlapiGen::$ipv4headeroption_hdl\_$rtralert_hdl\_attr(-type)]
                        array set type_mapping "0 end_of_options_list 1 nop 130 security 131 loose_source_route 68 time_stamp 133 extended_security 7 record_route 136 stream_identifier\
                                                137 strict_source_route 11 mtu_probe 12 mtu_reply 82 traceroute 147 address_extension 148 router_alert 149 selective_directed_broadcast_mode"
                        set type $type_mapping($type)
                        set len [set ::sth::hlapiGen::$ipv4headeroption_hdl\_$rtralert_hdl\_attr(-length)]
                        set value [set ::sth::hlapiGen::$ipv4headeroption_hdl\_$rtralert_hdl\_attr(-routeralert)]
                        append hlapi_traffic_script "-ip_router_alert 1 \\\n"
                        append hlapi_traffic_script "-ipv4_header_options router_alert \\\n"
                        append hlapi_traffic_script "-ipv4_router_alert \"optiontype:$type length:$len routeralertvalue:$value\" \\\n"
                        
                        array unset type_mapping
                    }
                }
                break
            }
        }
    }
    
    #5. config mac_discovery_gateway
    if {[regexp -nocase "ip" $l3_protocol]} {
        #get l3_protocol handle
        if {[regexp -nocase "ipv4" $l3_protocol]} {
            set proto_type "ipv4:ipv"
        } elseif {[regexp -nocase "ipv6" $l3_protocol]} {
            set proto_type "ipv6:ipv"
        }
        foreach iphdl [set ::sth::hlapiGen::$strblk\_obj($proto_type)] {
            if {[lsearch $ip_outer_hdl_list $iphdl] < 0} {
                set ip_hdl $iphdl
                break
            }
        }
        set gateway [set ::sth::hlapiGen::$strblk\_$ip_hdl\_attr(-gateway)]
        append hlapi_traffic_script "-mac_discovery_gw $gateway \\\n"
    }
    
    #6. config the gre info
    if {[array names ipheader_gre] != ""} {
        traffic_config_gre $strblk tunnel_hdl
        append hlapi_traffic_script "-tunnel_handle \$tunnel_hdl \\\n"
    }
    
    #7. config igmp_multicast_addr, igmp_record_type, igmp_multicast_src
    if {$l4_protocol != ""} {
        if {[regexp -nocase "igmp" $l4_protocol]} {
            set igmpv3report_address ""
            set igmpv3report_rectype ""
            set igmpv3report_addlist ""
            set srcnum 0
            set addnum 0
            set typenum 0
            set sorted_array [lsort [array names traffic_config_igmpv3report_params]]
            foreach arg [set sorted_array] {
                set value $traffic_config_igmpv3report_params($arg)
                regexp {[0-9]+} $arg number
                if {[regexp -nocase "igmp_multicast_src" $arg]} {
                    if {$igmpv3report_addlist == "" || $number == [expr $srcnum+1]} {
                        append igmpv3report_addlist "{$value} "
                    } else {
                        append igmpv3report_addlist "{} {$value} "
                    }
                    set srcnum $number
                    continue
                } elseif {[regexp -nocase "igmp_multicast_add" $arg]} {
                    if {$igmpv3report_address == "" || $number == [expr $addnum+1]} {
                        append igmpv3report_address "$value "
                    } else {
                        append igmpv3report_address "255.0.0.1 $value "
                    }
                    set addnum $number
                    continue
                } elseif {[regexp -nocase "igmp_record_type" $arg]} {
                    if {$igmpv3report_rectype == "" || $number == [expr $typenum+1]} {
                        append igmpv3report_rectype "$value "
                    } else {
                        append igmpv3report_rectype "5 $value "
                    }
                    set typenum $number
                    continue
                }
            }
            
            if {$igmpv3report_rectype != ""} {
                append hlapi_traffic_script "-igmp_record_type $igmpv3report_rectype\\\n"
            }        
            if {$igmpv3report_address != ""} {
                append hlapi_traffic_script "-igmp_multicast_addr $igmpv3report_address\\\n"
            }
            if {$igmpv3report_addlist != ""} {
                append hlapi_traffic_script "-igmp_multicast_src $igmpv3report_addlist\\\n"
            }
        }
    }
    

    #8. config the tunnel binding info:tunnel_bottom_label, tunnel_next_label, tunnel_top_label
    if {[info exists ::sth::hlapiGen::$strblk\_obj(pathdescriptor)]} {
        set pathdes_hdl [set ::sth::hlapiGen::$strblk\_obj(pathdescriptor)]
        if {[info exists ::sth::hlapiGen::$strblk\_$pathdes_hdl\_attr(-encapsulation-targets)]} {
            set index 0
            set mplslist [set ::sth::hlapiGen::$strblk\_$pathdes_hdl\_attr(-encapsulation-targets)]
            set tunnel_label_list "tunnel_bottom_label tunnel_next_label tunnel_top_label"
            foreach mplsif $mplslist {
                set device [stc::get $mplsif -parent]
                set arg [lindex $tunnel_label_list $index]
                if {[info exists ::sth::hlapiGen::device_ret($device)]} {
                    set handle [lindex $::sth::hlapiGen::device_ret($device) 0]
                    set handle_indx [lindex $::sth::hlapiGen::device_ret($device) 1]
                    append hlapi_traffic_script_var "set $arg\_device \[lindex \[keylget $handle handle\] $handle_indx\]\n"
                    append hlapi_traffic_script "-$arg \$$arg\_device\\\n"
                }
                incr index
            }    
        }
    }
    
    # 9. #add EnableStream support even only one parameter maps all the modifier, we can only check one modifier obj
    foreach obj_child [array names ::sth::hlapiGen::$strblk\_obj] {
        if {[regexp -nocase "modifier" $obj_child]} {
            foreach modifier_hdl [set ::sth::hlapiGen::$strblk\_obj($obj_child)] {
                set enable_stream_value [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-enablestream)]
                append hlapi_traffic_script "-enable_stream $enable_stream_value\\\n"
                break
            }
            break
        }
    }
    
    
    
}

#this function is used to handle the specific headers which are not used traffic_config function and table file
proc ::sth::hlapiGen::traffic_config_specific_function {strblk traffic_ret} {
    variable traffic_headers_array
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
        
    set l4_protocol $traffic_headers_array(l4_protocol)
    if {[regexp -nocase "ospf" $l4_protocol]} {
        traffic_config_specific_ospf $strblk $traffic_ret
    }
    
    #add other specific conditions if necessary
    
    #if the fc:fip header is created under streamblock, call fip_traffic_config
    if {[info exists ::sth::hlapiGen::$strblk\_obj(fc:fip)]} {
        traffic_config_specific_fip $strblk $traffic_ret
    }
    
    #add FCOE traffic here
    if {[regexp -nocase "fc:fcoeheader" [stc::get $strblk -children]]} {
        handle_fcoe_traffic $strblk $traffic_ret
    }
}

#this function is used to config the attr by mapping the hltapi table, it is similar to the "config_obj_attr" in hlapiGenFunction.tcl
proc ::sth::hlapiGen::process_obj_attr {name_space cmd_name phdl obj_handle obj} {
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
    variable traffic_config_igmpv3report_params
    variable traffic_config_mpls   
    
    foreach arg [array names $name_space$cmd_name\_stcobj] {
        set obj_in_table [string tolower [set $name_space$cmd_name\_stcobj($arg)]]
        set attr_in_table [string tolower [set $name_space$cmd_name\_stcattr($arg)]]
        if {[regexp -nocase "^$obj_in_table$" $obj]} {
            if {[info exists ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-$attr_in_table)]} {
                set type [set $name_space$cmd_name\_type($arg)]
                set value [set sth::hlapiGen::$phdl\_$obj_handle\_attr(-$attr_in_table)]
                #specially hanlde for some parameters
                set value [update_value $phdl $arg $value $name_space $cmd_name $type $attr_in_table]
                if {$value == ""} {
                    continue
                }

                #If default value option disable, then skip generating
                if { $::sth::hlapiGen::default_value == 0 } {
                    if {[info exists $name_space$cmd_name\_default($arg)]} {
                        set default_val [set $name_space$cmd_name\_default($arg)]
                        if {[string match -nocase $value $default_val ]} {
                            continue;
                        }
                    }
                }
                
                #If object is not ipv4:ipv4 and arg equals mf_bit/reserved/ip_fragment,then skip generating -- Jeff July 14,2017
                if {![regexp -nocase "ipv4:ipv4" $phdl]} {
                    if {[regexp {^mf_bit$} $arg] == 1 || [regexp {^reserved$} $arg] == 1 || [regexp {^ip_fragment$} $arg] == 1} {
                        continue
                    }
                }

                if {[regexp -nocase "traffic_config_ospf" $cmd_name]} {
                    #handle the list input by saving the param-value in an array
                    if {[regexp -nocase "ospfv2attachedrouter" $obj]} {
                        append arg "_$phdl"
                    }
                    if {[info exists traffic_config_ospf_params($arg)]} {
                        set value_list $traffic_config_ospf_params($arg)
                        lappend value_list $value
                        set traffic_config_ospf_params($arg) $value_list
                    } else {
                        array set traffic_config_ospf_params "$arg $value"
                    }
                } else {
                    if {[regexp -nocase "GroupRecord" $obj]
                        || [regexp -nocase "Ipv4Addr" $obj]} {
                        
                        if {[regexp -nocase "GroupRecord" $obj]} {
                            append arg "_$obj_handle"
                        } else {
                            append arg "_$phdl"
                        }
                        
                        if {[info exists traffic_config_igmpv3report_params($arg)]} {
                            set value_list $traffic_config_igmpv3report_params($arg)
                            lappend value_list $value
                            set traffic_config_igmpv3report_params($arg) $value_list
                        } else {
                            array set traffic_config_igmpv3report_params "$arg $value"
                        }
                    } else {
                        if {[regexp -nocase "^mpls_labels" $arg]||[regexp -nocase "^mpls_cos" $arg]||[regexp -nocase "mpls_ttl" $arg]||[regexp -nocase "mpls_bottom_stack_bit" $arg]} {
                            append  traffic_config_mpls($arg)  "\{$value\} "
                        } else {
                            append hlapi_traffic_script "			-$arg			$value\\\n"
                        }
                    }
                }
            }
        } 
    }
}

#this function is used to update the obj before configuring the attribute of this obj
proc ::sth::hlapiGen::update_obj {cmd_name phdl obj_handle obj} {
    variable vlan_outer_hdl
    variable vlan_other_hdl
    variable ip_outer_hdl_list
    variable l4_ip_hdl_list
    if {[regexp -nocase "ipv6:ipv6.+" $obj]} {
        #for ipv6 extention header
        return $obj
    }
    #  hanlde the ipv missed the last number and multi types of ethernet
    switch -regexp -- $obj {
        "ipv4:" { set obj "ipv4:ipv4" }
        "ipv6:" { set obj "ipv6:ipv6" }
        "icmp:" { set obj "icmp:icmp" }
        "igmp:" { set obj "igmp:igmp" }
    }
    if {[lsearch $ip_outer_hdl_list $obj_handle] >= 0} {
        append obj Outer
        return $obj
    }
    
    # update the obj for vlan outer
    if {[regexp -nocase {vlan} $obj] && [lsearch $vlan_outer_hdl $obj_handle]>= 0} {
        set obj "VlanOuter"
        return $obj
    }
    if {[regexp -nocase {vlan} $obj] && [lsearch $vlan_other_hdl $obj_handle]>= 0} {
        set obj "VlanOther"
        return $obj
    }
    if {[lsearch $l4_ip_hdl_list $obj_handle] >= 0} {
        append obj L4
        return $obj
    }
    # handle the modifier
    if {[regexp -nocase "Modifier" $obj_handle]} {
        set obj [update_modifier_obj $phdl $obj_handle $obj]
    } elseif {[regexp -nocase "ethernet" $obj]} {
        set obj "ethernet"
    }
    
    if {[string match -nocase "tos" $obj] || [string match -nocase "diffserv" $obj]} {
        #need to add one more layer to distinguish its origin
        set obj [add_parent_info $phdl $obj]
    }
    
    if {[string match -nocase "traffic_config_ospf_packets" $cmd_name]} {
        if {[regexp -nocase "ospfv2:" $obj]} {
            set obj "ospfv2"
        } elseif {[string match -nocase "header" $obj]} {
            if {[regexp ":" $phdl]} {
                regsub -all {\:.*} $phdl ".header" obj
            } else {
                regsub -all {\d$} $phdl ".header" obj
            }
        } elseif {[regexp -nocase "hdrAuthSelect" $obj]} {
            set obj "authSelect"
        } elseif {[regexp -nocase "Options" $obj] && ![string match -nocase "externalLsaOptions" $obj]} {
            process_ospf_options_list $phdl $obj_handle $obj
        }
        if {[string match -nocase "ospfv2RouterLsaLink" $obj] || [string match -nocase "Ospfv2RouterLsaTosMetric" $obj]\
            ||[string match -nocase "Ospfv2SummaryLsaTosMetric" $obj] ||[string match -nocase "Ospfv2ExternalLsaTosMetric" $obj]} {
            pre_process_ospf_update_msg_header $phdl $obj_handle $obj
        }
    }
    return $obj
}

#this function is used to update the value for some specific parameters
proc ::sth::hlapiGen::update_value {strblk arg value name_space cmd_name type attr_in_table} {
    variable ipprotocol_map
    if {[regexp -nocase {null} $value] || [regexp -nocase "^$" $value]} {
        return ""
    }
    
    switch -regexp -- $arg {
        "ip_protocol" {
            set frameconfig [set ::sth::hlapiGen::$strblk\_$strblk\_attr(-frameconfig)]
            if {![regexp {(<protocol override="true" >)(\d)(</protocol>)} $frameconfig]} {
                set idx1 [string first "pdu name=\"proto1\" pdu=" $frameconfig]
                set idx2 [string first ">" $frameconfig $idx1]
                if {$idx1 > -1 && $idx2 > -1} {
                    set myproto [string range $frameconfig $idx1 $idx2]
                    set idx1 [string first "pdu=" $myproto]
                    set idx2 [string first ":" $myproto]
                    set mykey [string toupper [string range $myproto [expr $idx1+5] [expr $idx2-1] ]]
                    if {[info exists ipprotocol_map($mykey)]} {
                        set value [set ipprotocol_map($mykey)]
                    }
                }
            }
        }
        "ipv6_next_header" {
            set frameconfig [set ::sth::hlapiGen::$strblk\_$strblk\_attr(-frameconfig)]
            if {![regexp {(<nextHeader override="true" >)(\d)(</nextHeader>)} $frameconfig]} {
                set nxtHdrIdx [string first "</payloadLength>" $frameconfig]
                set idx1 [string first "pdu=" $frameconfig $nxtHdrIdx]
                set idx2 [string first ">" $frameconfig $idx1]
                if {$idx1 > -1 && $idx2 > -1} {
                    set myproto [string range $frameconfig $idx1 $idx2]
                    set idx1 [string first "pdu=" $myproto]
                    set idx2 [string first ":" $myproto]
                    set mykey [string toupper [string range $myproto [expr $idx1+5] [expr $idx2-1] ]]
                    if {[info exists ipprotocol_map($mykey)]} {
                        set value [set ipprotocol_map($mykey)]
                    }
                }
            }
        }
        "tcp_reserved|^vlan_user_priority$|vlan_outer_user_priority" {
            set value [::sth::hlapiGen::binToInt $value]
        }
        "vlan_user_priority_other" {
            set value_new ""
            foreach v $value {
                set v [::sth::hlapiGen::binToInt $v]
                set value_new [concat $value_new $v]
            }
            set value $value_new
        }
        "vlan_tpid|vlan_outer_tpid" {
            set value [format "%d" 0X$value]
        }
        "ip_checksum|ip_outer_checksum|udp_checksum" {
            #specially handle for checksum, the value 65535 means corrupted packets, mapping hltapi value is 1
            if {$value == 65535} {
                set value 1
            } else {
                set value ""
            }
        }
        "ip_dscp_step" {
            set value [format "%d" 0X$value]
            set value [expr $value /4]
        }
        "ip_precedence_step" {
            set value [format "%d" 0X$value]
            set value [expr $value /32]
        }
        "ip_tos_step" {
            set value [format "%d" 0X$value]
            set value [expr $value /2]
        }
        "ipv6_routing_res" {
            #convert integer to hex with 16 bit
            set value [format "%04x" $value]
        }
        "ipv6_auth_string" {
            #convert to hex with 32 bit
            set value [format "%08x" 0x$value]
        }
        "mac_src_step|mac_dst_step" {
            if {![string is integer -strict $value]} {
                return ""
            }
        }
        "igmp_record_type" {
            if {$value == ""} {
                set value 5
            }    
        }
        "igmp_qrv" {
            set value [::sth::hlapiGen::binToInt $value]
        }
        "ether_type" {
            #handle the auto issue, if the value is the default value, this value will not be configured in hltapi, then the generated xml file will have auto value.
            if {[regexp -nocase "88b5" $value]} {
                set value ""
            }
        }
        "dest_port_list" {
            set value_new ""
            foreach port $value {
                set value_new [concat $value_new $::sth::hlapiGen::port_ret($port)]
            }
            set value $value_new
        }
    }
    
    if {[regexp -nocase "l3_length|frame_size" $arg]} {
        #for l3_length(fixed)|l3_length_min(random\incr)|l3_length_max(random\incr)|l3_length_step(incr)
        set length_mode [string tolower [set ::sth::hlapiGen::$strblk\_$strblk\_attr(-framelengthmode)]]
        switch -regexp -- $length_mode {
            "fixed" {
                if {!([string match -nocase "l3_length" $arg] || [string match -nocase "frame_size" $arg])} {
                    set value ""
                }
            }
            "incr" {
                if {[string match -nocase "l3_length" $arg] || [string match -nocase "frame_size" $arg]} {
                    set value ""
                }
            }
            "random" {
                if {!([string match -nocase "l3_length_min" $arg] || [string match -nocase "frame_size_min" $arg]) && !([string match -nocase "l3_length_max" $arg] ||[string match -nocase "frame_size_max" $arg])} {
                    set value ""
                }
            }
            "imix" {
                set value ""
            }
            "auto" {
                set value ""
            }
        }
        if {$value != "" && [regexp -nocase "l3_length" $arg] && ![string match -nocase "l3_length_step" $arg]} {
            set value [process_l3_length $arg $value]
        }
    }
    
    if {[regexp {CHOICES} $type]} {
        #convert the value get in the data model to be one of the choices
        set value_new ""
        foreach v $value {
            set v [::sth::hlapiGen::get_choice_value $arg $type $v $name_space $cmd_name]
            set value_new [concat $value_new $v]
        }
        set value $value_new
    }
 
    if {[llength $value] > 1 && [regexp -nocase {^name$} $attr_in_table]} {
        regsub -all { } $value "_" value
    }
    
    if {[regexp -nocase "RecycleCount" $attr_in_table] && $value == 0} {
        return ""
    }
    return $value
}

proc ::sth::hlapiGen::process_igmp_attr {strblk igmptype igmphandle} {
    #default version is 1
    set new_version 1 
    set new_type ""
    switch $igmptype {
        "igmp:igmpv2query" {
            set new_version 2
            set new_type "query"
        }
        "igmp:igmpv2report" {
            set new_version 2
            set new_type "report"
        }
        "igmp:igmpv3query" {
            set new_version 3
            set new_type "query"
        }
        "igmp:igmpv3report" {
            set new_version 3
            set new_type "report"
        }
    }
    
    array set ::sth::hlapiGen::$strblk\_$igmphandle\_attr "-igmpversion $new_version"
    if {"" != $new_type} {
        array set ::sth::hlapiGen::$strblk\_$igmphandle\_attr "-igmpmsgtype $new_type"
    }
}

#this function is used to process the bound streamblock handle
proc ::sth::hlapiGen::process_bound_stream_handle {strblk port} {
    variable hlapi_traffic_script
    variable traffic_headers_array
    set srcbinding_list [stc::get $strblk -SrcBinding-targets]
    set dstbinding_list [stc::get $strblk -DstBinding-targets]
    
    #To check for layer 2 traffic and append traffic_type as L2
    if {[regexp "ethiiif" $srcbinding_list ] || [regexp "vlanif" $srcbinding_list ]} {
        append hlapi_traffic_script "			-traffic_type			       L2\\\n"
        if {[regexp "ethiiif" $srcbinding_list ]} {
            array set traffic_headers_array "l2_encap ethernet_ii"
        } else {
            array set traffic_headers_array "l2_encap ethernet_ii_vlan"
        }
    }
    
    if {$srcbinding_list != ""} {
        process_bound_stream_handle_common src $srcbinding_list $strblk
    }
    
    if {$dstbinding_list != ""} {
        process_bound_stream_handle_common dst $dstbinding_list $strblk
    }
            
}

#this function is used to unset the ip address for bound streamblock
proc ::sth::hlapiGen::unset_ip_var {strblk paramslist} {
    if {[info exists ::sth::hlapiGen::$strblk\_obj(ipv4:ipv)]} {
        set ipv4header [set ::sth::hlapiGen::$strblk\_obj(ipv4:ipv)]
        foreach ipv4 $ipv4header {
            foreach param [string tolower $paramslist] {
                unset ::sth::hlapiGen::$strblk\_$ipv4\_attr(-$param)
            }
        }
    }
    if {[info exists ::sth::hlapiGen::$strblk\_obj(ipv6:ipv)]} {
        set ipv6header [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv)]
        foreach ipv6 $ipv6header {
            foreach param [string tolower $paramslist] {
                unset ::sth::hlapiGen::$strblk\_$ipv6\_attr(-$param)
            }
        }
    }
    
}
#this function is used to process boundstream handle for src handle and dst handle
proc ::sth::hlapiGen::process_bound_stream_handle_common {type binding_list strblk} {
    variable hlapi_traffic_script
    set $type\_hdl_list ""
    array set handlelist ""
    array set networkblocklist ""
    set arg "emulation_$type\_handle"
    
    foreach binding $binding_list {
        set hdl [stc::get $binding -parent]
        #if the hdl is routerlsalink, then we need to check routerlsa
        if {[regexp -nocase "routerlsalink" $hdl]} {
            set hdl [stc::get $hdl -parent]
            #ignore the networkblock if its parent has been added for emulation_src/dst_handle
            if {[info exist networkblocklist($hdl)]} {
                continue
            }
            array set networkblocklist "$hdl 1"
            
           
        }
        #get the related variable from the hdl based on framework
        if {[info exists ::sth::hlapiGen::device_ret($hdl)]} {
            set handle [lindex $::sth::hlapiGen::device_ret($hdl) 0]
            if {[regexp -nocase "networkblock" $binding]} {
                set handle_indx 0
                set key_values [update_key_value networkblock $hdl $strblk]
            } elseif {[regexp -nocase "if" $binding]} {
                set handle_indx [lindex $::sth::hlapiGen::device_ret($hdl) 1]
                #check if the key value is special
                set key_values [update_key_value device $hdl $strblk]
                set arg [process_bound_stream_arg $type $strblk $hdl $arg]
            }
            
            if {[info exists key_values]} {
                if {$::sth::hlapiGen::scaling_test && [llength $binding_list] > 2 && [regexp -nocase "emulateddevice|router|host" $hdl] && ![regexp -nocase "networkblock" $binding_list]} {
                    if {[info exists handlelist($key_values)]} {
                        set handlelist($key_values) [concat $handlelist($key_values) $hdl]
                    } else {
                        set handlelist($key_values) $hdl
                    }
                } else {
                    append $type\_hdl_list "\[lindex \[keylget $handle $key_values\] $handle_indx\] "
                }
            }
        }
    }
    
    if {[info exists key_values]} {
        process_bound_stream_var $type $binding_list [set $type\_hdl_list]
        append hlapi_traffic_script "			-$arg			\$$type\_hdl\\\n"
        array unset handlelist
        unset key_values
        if {[regexp -nocase src $type]} {
            set paramslist "sourceAddr"
        } else {
            set paramslist "destAddr"
        }
        unset_ip_var $strblk $paramslist
    }
    array unset networkblocklist
}
#this function is used to update the key value for the returned keyedlist
proc ::sth::hlapiGen::update_key_value {type hdl strblk} {
    variable protocol_to_devices
    set return_key "handle"
    if {$type == "device"} {
        set devicehdl $hdl
        array set hltapi_obj [get_objs $devicehdl]
        #get the first class in the configured list
        set class_list [array names hltapi_obj]
        create_switch_priority_list sth::hlapiGen:: hlapi_gen $class_list switch_priority_list
        #check the protocol config by priority to avoid handle selection disorder
        foreach item $switch_priority_list {
            set class [lindex $item 1]
            if { [info exists ::sth::hlapiGen::protocol_to_devices($class) ]} {
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
            "emulateddevice" {
                if {[info exists ::sth::hlapiGen::linkDeviceRetKey($hdl)]} {
                    set return_key [set ::sth::hlapiGen::linkDeviceRetKey($hdl)]
                }
            }
        }
    } elseif {$type == "networkblock"} {
        #networkblock may be from device or ipv*routeconfig
        switch -regexp -- $hdl {
            "routeconfig" {
                set return_key "handles"
                #currently in hltapi, the tunnel info only can be configured with "rsvp*gresstunnelparams*", "ipv4prefixlsp*","host*","router*","summarylsablock*",
                #so unset the pathdescriptor info in the datamodel
                if {[info exists ::sth::hlapiGen::$strblk\_obj(pathdescriptor)]} {
                    unset ::sth::hlapiGen::$strblk\_obj(pathdescriptor)
                }
            }
            "tunnelparams" {
                set return_key "tunnel_handle"
            }
            "prefixlsp" {
                set return_key "lsp_handle"
            }
            "routeparams" {
                set return_key "route_handle"
            }
            "group" {
                set return_key "handle"
            }
            "lsa" {
                set return_key "lsa_handle"
            }
        }
        
    }
    
    
    return $return_key
}

#this function is used to update arg for bound stream
proc ::sth::hlapiGen::process_bound_stream_arg {type strblk handle arg} {
    variable traffic_headers_array
    if {$type == "src"} {
        set type "source"
    } else {
        set type "destination"
    }
    #check if the device has vpnsiteinfovpls, vpls handles can be tested when vpls protocol is finished
    if {[info exists ::sth::hlapiGen::$handle\_$handle\_attr(-memberofvpnsite-targets)]} {
        set vplsinfo [set ::sth::hlapiGen::$handle\_$handle\_attr(-memberofvpnsite-targets)]
        if {$vplsinfo != ""} {
            set arg "vpls_$type\_handle"
        }
    }
    if {$type == "source"} {
        if {[info exists ::sth::hlapiGen::$handle\_obj(pppoeclientblockconfig)] || [info exists ::sth::hlapiGen$handle\_obj(pppoeserverblockconfig)]} {
            set traffic_headers_array(l2_encap) "ethernet_ii_pppoe"
            if {[info exists ::sth::hlapiGen::$strblk\_obj(pppoe:pppoesession)]} {
               set pppoe_hdl [set ::sth::hlapiGen::$strblk\_obj(pppoe:pppoesession)]
               unset ::sth::hlapiGen::$strblk\_$pppoe_hdl\_attr(-sessionid)
            }
        }
    }
    
    return $arg
}

#this function is used to process the variable for bound stream
proc ::sth::hlapiGen::process_bound_stream_var {type binding_list hdl_list} {
    variable hlapi_traffic_script_var
    upvar handlelist handlelist_local
    if {$::sth::hlapiGen::scaling_test && [llength $binding_list] > 2 && ![regexp -nocase "networkblock" $binding_list]} {
        #for the route or lsa bound condition, the list is not necessary to be concise, because the handle are from different function with different var
        set hdl_update $hdl_list
        foreach keyvalue [array names handlelist_local] {
            set update_value [get_device_created_scaling_common "$handlelist_local($keyvalue)" $keyvalue]
            set hdl_update [concat $hdl_update $update_value]
        }
        append hlapi_traffic_script_var "set $type\_hdl \"$hdl_update\"\n"
    } else {
        if {[regexp {.*\]\s\[.*} $hdl_list]} {
            append hlapi_traffic_script_var "set $type\_hdl \"$hdl_list\"\n"
        } else {
            append hlapi_traffic_script_var "set $type\_hdl $hdl_list\n"
        }
    }
}

#this function is used to get the headers under streamblock to determin l2_encap, l3_protocol, l3_outer_protocol, l4_protocol values
proc ::sth::hlapiGen::process_traffic_header {strblk} {
    variable traffic_headers_array
    variable ipheader_gre
    variable traffic_config_mpls_count_flag
    set l2_encap ""
    set l3_protocol ""
    set l3_outer_protocol ""
    set l4_protocol ""
    set l2_type ""
    set traffic_config_mpls_count_flag 0
    
    set strblk_header [stc::get $strblk -children]
    foreach mpls_header $strblk_header {
        if {[regexp -nocase "mpls:mpls" $mpls_header]} {
            incr traffic_config_mpls_count_flag
        }
    }
    
    #l2: ethernet_ii, ethernet_ii_vlan, ethernet_ii_unicast_mpls, ethernet_ii_vlan_mpls, atm_vc_mux, ethernet_8022,  
    #    ethernet_8022_vlan, ethernet_8023_snap, ethernet_8023_snap_vlan, ethernet_8023_raw, ethernet_8023_raw_vlan
    # currently hlapiGen traffic doesn't support ethernet_ii_pppoe, ethernet_ii_vlan_pppoe, ethernet_ii_qinq_pppoe
    switch -regexp -- $strblk_header {
        "ethernet:ethernetii" {
            if {[regexp -nocase "mpls:Mpls" $strblk_header]} {
                 set l2_encap "ethernet_ii_unicast_mpls"
            } else {
                set l2_encap "ethernet_ii"
            }
            set l2_type "ethernet:ethernetii"
        }
        "ethernet:ethernet8022" {
            set l2_encap "ethernet_8022"
            set l2_type "ethernet:ethernet8022"
        }
        "ethernet:ethernetsnap" {
            set l2_encap "ethernet_8023_snap"
            set l2_type "ethernet:ethernetsnap"
        }
        "ethernet:Ethernet8023Raw" {
            set l2_encap "ethernet_8023_raw"
            set l2_type "ethernet:Ethernet8023Raw"
        }
        "atm:ATM" {
            set l2_encap "atm_vc_mux"
        }
        "fc:fc" {
            set l2_encap "fibre_channel"
        }
    }
    
    if {$l2_encap != "" && $l2_type != ""} {
        #check if the l2_encap is created with vlan
        set l2hdl [stc::get $strblk -children-$l2_type]
        foreach tempL2hdl $l2hdl {
            set vlans [set ::sth::hlapiGen::$tempL2hdl\_obj(vlans)]
            if {[info exists ::sth::hlapiGen::$vlans\_obj(vlan)]} {
                set vlan [set ::sth::hlapiGen::$vlans\_obj(vlan)]
                if {[llength $vlan] > 1} {
                    set dualvlan_tag 1
                }
                if {[regexp "ethernet_ii_unicast_mpls" $l2_encap]} {
                    set l2_encap "ethernet_ii_vlan_mpls"
                } else {
                    set l2_encap $l2_encap\_vlan
                }
            }
        }
    }
    
    if {([info exists traffic_headers_array(l2_encap)] && $traffic_headers_array(l2_encap) == "ethernet_ii_pppoe") \
        || ([regexp -nocase "pppoe:PPPoESession" $strblk_header] && [regexp -nocase "ppp:PPP" $strblk_header])} {
        switch -- $l2_encap {
            "ethernet_ii" {
                set l2_encap "ethernet_ii_pppoe"
            }
            "ethernet_ii_vlan" {
                if {[info exists dualvlan_tag]} {
                    set l2_encap "ethernet_ii_qinq_pppoe"
                } else {
                    set l2_encap "ethernet_ii_vlan_pppoe"
                }
            }
        }
    }
    
    #l3: ipv4, ipv6, arp
    #if gre exists, need to check if the ip header is together with gre, then that header is created using emulation_gre_config
    if {[regexp -nocase "gre:gre" $strblk_header]} {
        if {[info exists ::sth::hlapiGen::$strblk\_obj(ipv4:ipv)]} {
            foreach ipv4header [set ::sth::hlapiGen::$strblk\_obj(ipv4:ipv)] {
                if {[set ::sth::hlapiGen::$strblk\_$ipv4header\_attr(-protocol)] == 47} {
                    array set ipheader_gre "$ipv4header \"\""
                    set gre_header [set ::sth::hlapiGen::$strblk\_obj(gre:gre)]
                    #unset ::sth::hlapiGen::$strblk\_obj(gre:gre)
                    append ipheader_gre($ipv4header) " $gre_header"
                    unset ::sth::hlapiGen::$strblk\_obj(gre:gre)
                    regsub "$ipv4header $gre_header" $strblk_header "" strblk_header
                }
            }
        }
        if {[info exists ::sth::hlapiGen::$strblk\_obj(ipv6:ipv)]} {
            foreach ipv6header [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv)] {
                if {[set ::sth::hlapiGen::$strblk\_$ipv6header\_attr(-nextheader)] == 47} {
                    array set ipheader_gre "$ipv6header \"\""
                    set gre_header [set ::sth::hlapiGen::$strblk\_obj(gre:gre)]
                    append ipheader_gre($ipv6header) " $gre_header"
                    unset ::sth::hlapiGen::$strblk\_obj(gre:gre)
                    regsub "$ipv6header $gre_header" $strblk_header "" strblk_header
                }
            }
        }
        
    }
    
    switch -regexp -- $strblk_header {
        {ipv4:ipv4[0-9]* ipv4:ipv4[0-9]* ipv4:ipv4} {
            set l3_outer_protocol "ipv4"
            set l3_protocol "ipv4"
            set l4_protocol "ipv4"
        }
        {ipv6:ipv6[0-9]* ipv4:ipv4[0-9]* ipv4:ipv4} {
            set l3_outer_protocol "ipv6"
            set l3_protocol "ipv4"
            set l4_protocol "ipv4"
        }
        {ipv4:ipv4[0-9]* ipv6:ipv6[0-9]* ipv4:ipv4} {
            set l3_outer_protocol "ipv4"
            set l3_protocol "ipv6"
            set l4_protocol "ipv4"
        }
        {ipv6:ipv6[0-9]* ipv6:ipv6[0-9]* ipv4:ipv4} {
            set l3_outer_protocol "ipv6"
            set l3_protocol "ipv6"
            set l4_protocol "ipv4"
        }
        {ipv4:ipv4[0-9]* ipv4:ipv4[0-9]* ipv6:ipv6} {
            set l3_outer_protocol "ipv4"
            set l3_protocol "ipv4"
            set l4_protocol "ipv6"
        }
        {ipv6:ipv6[0-9]* ipv4:ipv4[0-9]* ipv6:ipv6} {
            set l3_outer_protocol "ipv6"
            set l3_protocol "ipv4"
            set l4_protocol "ipv6"
        }
        {ipv4:ipv4[0-9]* ipv6:ipv6[0-9]* ipv6:ipv6} {
            set l3_outer_protocol "ipv4"
            set l3_protocol "ipv6"
            set l4_protocol "ipv6"
        }
        {ipv6:ipv6[0-9]* ipv6:ipv6[0-9]* ipv6:ipv6} {
            set l3_outer_protocol "ipv6"
            set l3_protocol "ipv6"
            set l4_protocol "ipv6"
        }
        {ipv4:ipv4[0-9]* gre:gre[0-9]* ipv4:ipv4} {
            set l3_outer_protocol "ipv4"
            set l3_protocol "gre"
            set l4_protocol "ipv4"
        }
        {ipv6:ipv6[0-9]* gre:gre[0-9]* ipv4:ipv4} {
            set l3_outer_protocol "ipv6"
            set l3_protocol "gre"
            set l4_protocol "ipv4"
        }
        {ipv4:ipv4[0-9]* gre:gre[0-9]* ipv6:ipv6} {
            set l3_outer_protocol "ipv4"
            set l3_protocol "gre"
            set l4_protocol "ipv6"
        }
        {ipv6:ipv6[0-9]* gre:gre[0-9]* ipv6:ipv6} {
            set l3_outer_protocol "ipv6"
            set l3_protocol "gre"
            set l4_protocol "ipv6"
        }
        {ipv4:ipv4[0-9]* ipv4:ipv4} {
            set l3_protocol "ipv4"
            set l3_outer_protocol "ipv4"
        }
        {ipv4:ipv4[0-9]* ipv6:ipv6} {
            set l3_protocol "ipv6"
            set l3_outer_protocol "ipv4"
        }
        {ipv6:ipv6[0-9]* ipv4:ipv4} {
            set l3_protocol "ipv4"
            set l3_outer_protocol "ipv6"
        }
        {ipv6:ipv6[0-9]* ipv6:ipv6} {
            #check if the later ipv6:ipv6 is ipv6 extention header and if the ipv6 header is for gre
            regsub [array names ipheader_gre] [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv)] "" ipv6header_list
            if {[llength $ipv6header_list] > 1} {
                set l3_protocol "ipv6"
                set l3_outer_protocol "ipv6"
            } else {
                set l3_protocol "ipv6"
            }
        }
        {ipv4:ipv4[0-9]* gre:gre} {
            set l3_protocol "gre"
            set l3_outer_protocol "ipv4"
        }
        {ipv6:ipv6[0-9]* gre:gre} {
            set l3_protocol "gre"
            set l3_outer_protocol "ipv6"
        }
        {arp:arp} {
            set l3_protocol "arp"
        }
        {arp:rarp} {
            set l3_protocol "arp"
        }
        {ipv4:ipv4} {
            set l3_protocol "ipv4"
        }
        {ipv6:ipv6} {
            #need to checkif the ipv6 header is for gre
            regsub [array names ipheader_gre] [set ::sth::hlapiGen::$strblk\_obj(ipv6:ipv)] "" ipv6header_list
            if {[llength $ipv6header_list] == 1} {
                set l3_protocol "ipv6"
            }
        }
    }
    
    #l4: tcp, udp, icmp, igmp, rtp, ospf
    #isis is configured by the custom pattern, so doesn't support to config isis by hlapi gen.
    switch -regexp -- $strblk_header {
        {tcp:tcp}       { set l4_protocol "tcp"  }
        {udp:udp}       { set l4_protocol "udp"  }
        {icmp:icmp}     { set l4_protocol "icmp" }
        {igmp:igmp}     { set l4_protocol "igmp" }
        {rtp:rtpheader} { set l4_protocol "rtp"  }
        {ospfv2:ospfv2} { set l4_protocol "ospf" }
    }
    if {[info exists traffic_headers_array(l2_encap)] && $traffic_headers_array(l2_encap) != "ethernet_ii_pppoe"} { 
        array set traffic_headers_array "l3_protocol \"$l3_protocol\" l3_outer_protocol \"$l3_outer_protocol\" l4_protocol \"$l4_protocol\""
    } else {
        array set traffic_headers_array "l2_encap \"$l2_encap\" l3_protocol \"$l3_protocol\" l3_outer_protocol \"$l3_outer_protocol\" l4_protocol \"$l4_protocol\""
    }
}



#this function is used to config gre with emulation_gre_config
#currently hltapi only accepts one tunnel handle,
#support to config parameters:gre_src_addr, gre_src_addr_count, gre_src_mode, gre_dst_addr, gre_dst_addr_count, gre_dst_addr_mode, gre_out_key, gre_checksum
proc ::sth::hlapiGen::traffic_config_gre {strblk ret_value} {
    set hlapi_traffic_script_gre ""
    variable ipheader_gre
    
    if {[llength [array names ipheader_gre]] > 1} {
        set ipheader_gre_hdl [lindex [array names ipheader_gre] 0]
    } else {
        set ipheader_gre_hdl [array names ipheader_gre]
    }
    set grehdl [lindex $ipheader_gre($ipheader_gre_hdl) 0]
    regsub $grehdl $ipheader_gre($ipheader_gre_hdl) "" ipheader_gre($ipheader_gre_hdl)
    set cmd_name "emulation_gre_config"
    append hlapi_traffic_script_gre "set $ret_value \[sth::$cmd_name\\\n"
    
    #gre_tnl_type
    if {[regexp -nocase "ipv6" $ipheader_gre_hdl]} {
        set gre_tnl_type 6
    } else {
        set gre_tnl_type 4
    }
    append hlapi_traffic_script_gre "-gre_tnl_type		$gre_tnl_type \\\n"
    #gre ckPresent
    set ckpresent [set ::sth::hlapiGen::$strblk\_$grehdl\_attr(-ckpresent)]
    append hlapi_traffic_script_gre "-gre_checksum $ckpresent \\\n"
    #gre ip address

    set src_ip [stc::get $ipheader_gre_hdl -sourceAddr]
    set dst_ip [stc::get $ipheader_gre_hdl -destaddr]
    
    append  hlapi_traffic_script_gre "-gre_src_addr $src_ip\\\n"
    append  hlapi_traffic_script_gre "-gre_dst_addr $dst_ip\\\n"
    #check if ip src or dst is modifier
    foreach modifier_hdl $ipheader_gre($ipheader_gre_hdl) {
        if {$modifier_hdl != ""} {
            set offset [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-offsetreference)]
            if {[regexp -nocase "sourceAddr" $offset]} {
                set type "src"
            } else {
                set type "dst"
            }
            set modifiermode [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-modifiermode)]
            if {[regexp -nocase "incr" $modifiermode]} {
                set modifiermode "increment"
            }
            append  hlapi_traffic_script_gre "-gre_$type\_mode $modifiermode\\\n"
            append  hlapi_traffic_script_gre "-gre_$type\_addr_step [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-stepvalue)]\\\n"
            append  hlapi_traffic_script_gre "-gre_$type\_addr_count [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-recyclecount)]\\\n"
        }
    }
    #gre key
    set grekeys [set ::sth::hlapiGen::$grehdl\_obj(keys)]
    if {[info exists ::sth::hlapiGen::$grekeys\_obj(grekey)]} {
        set grekey [set ::sth::hlapiGen::$grekeys\_obj(grekey)]
        append hlapi_traffic_script_gre "-gre_out_key [set ::sth::hlapiGen::$grekeys\_$grekey\_attr(-value)] \\\n"
    }
    append hlapi_traffic_script_gre "\]\n"
    puts_to_file $hlapi_traffic_script_gre
    puts_to_file "puts \"***** run sth::emulation_gre_config successfully\"\n"
    
    
}
#this function is used to handle the ipv6 extention header which is not in the standard format
proc ::sth::hlapiGen::process_ipv6_extention_header_options {ipv6_hdl type} {
    variable hlapi_traffic_script
    set options_hdl [set ::sth::hlapiGen::$ipv6_hdl\_obj(options)]
    regsub -all {\_} $type "" option_type
    set option_type ipv6$option_type\option
    set option_hdl [set ::sth::hlapiGen::$options_hdl\_obj($option_type)]
    foreach obj [array names ::sth::hlapiGen::$option_hdl\_obj] {
        if {[string match -nocase "pad" $obj]} {
            append hlapi_traffic_script "-ipv6_$type\_options \"type:pad1\" \\\n"
        }
        
        if {[string match -nocase "padn" $obj]} {
            set padn_hdl [set ::sth::hlapiGen::$option_hdl\_obj($obj)]
            set len [set ::sth::hlapiGen::$option_hdl\_$padn_hdl\_attr(-length)]
            set value [set ::sth::hlapiGen::$option_hdl\_$padn_hdl\_attr(-padding)]
            set value [format "%02x" 0x$value]
            append hlapi_traffic_script "-ipv6_$type\_options \"type:padn length:$len value:$value\" \\\n"
        }

        if {[regexp -nocase "hop_by_hop" $type]} {
            if {[string match -nocase "jumbo" $obj]} {
                set jumbo_hdl [set ::sth::hlapiGen::$option_hdl\_obj($obj)]
                set len [set ::sth::hlapiGen::$option_hdl\_$jumbo_hdl\_attr(-length)]
                set value [set ::sth::hlapiGen::$option_hdl\_$jumbo_hdl\_attr(-data)]
                append hlapi_traffic_script "-ipv6_hop_by_hop_options \"type:jumbo length:$len payload:$value\" \\\n"	 
            }
            if {[string match -nocase "routeralert" $obj]} {
                set routeralert_hdl [set ::sth::hlapiGen::$option_hdl\_obj($obj)]
                set len [set ::sth::hlapiGen::$option_hdl\_$routeralert_hdl\_attr(-length)]
                set value [set ::sth::hlapiGen::$option_hdl\_$routeralert_hdl\_attr(-value)]
                switch -- $value {
                    "0" {set alert_type "mld"}
                    "1" {set alert_type "rsvp"}
                    "2" {set alert_type "active_net"}
                }
                append hlapi_traffic_script "-ipv6_hop_by_hop_options \"type: router_alert length:$len alert_type:$alert_type\" \\\n"	
            } 
        }
    }
}

#this function is used to update the modifier obj
proc ::sth::hlapiGen::update_modifier_obj {phdl obj_handle obj} {
    variable traffic_headers_array
    variable ip_outer_hdl_list
    variable ipheader_gre
            
    switch -regexp -- $obj {
        "randommodifier" {
            if {![info exists ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-modifiermode)]} {
                set ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-modifiermode) "random"
            }
        }
        "tablemodifier" {
            if {[regexp -nocase "label" $obj]} {
                set ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-modifiermode) "list"
            }
        }
        "streamcollectionrangemodifier" {
            set obj "none"
            return $obj
        }
    }
        
    #get the object by offset reference
    set offset_refer [set ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-offsetreference)]
    #check if this modifier is for gre ip header
    if {[regexp -nocase "sourceAddr|destAddr" $offset_refer]} {
        regsub {\..*} $offset_refer "" ipheader_name
        set ipheader_hdl [get_handle_by_name $phdl $ipheader_name]
        if {[lsearch [array names ipheader_gre] $ipheader_hdl] >= 0} {
            append ipheader_gre($ipheader_hdl) " $obj_handle"
            set obj "none"
            return $obj
        }
    }

    #update the obj to contain the hld instead of the name
    set hdllist ""
    foreach ele [split $offset_refer .] {
        if {[regexp {.*\d$} $ele] && ![regexp {.*L4$} $ele]} {
            set hdl [get_handle_by_name $phdl $ele]
            regsub -all {\d+$} $hdl "" hdl
            regsub {\:.*} $hdl "" hdl
        } else {
            set hdl $ele
        }
        append hdllist " $hdl"
    }
    set obj [join $hdllist .]
    
    switch -regexp -- $obj {
        "sourceAddr|destAddr|senderHwAddr|targetHwAddr" {
            if {[regexp -nocase "outer|L4" $obj]} {
                regsub {^.*\:} $obj "" obj
            }
        }
        "label" {
            set obj "mpls.label"
        }
        "tosDiffserv" {
            #need to check mask for tos or precedence modifier
            if {[info exists ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-mask)]} {
                set mask [set ::sth::hlapiGen::$phdl\_$obj_handle\_attr(-mask)]
                if {$mask == "E0" && [regexp -nocase "tosDiffserv.tos" $obj]} {
                    regsub {tosDiffserv.tos} $obj {tosDiffserv.pecedence} obj
                }
            }
        }
        "gateway" {
            regsub {v\d} $obj "" obj
        }
    }

    return $obj
}

#this function is used to update the offset reference for outer header.
proc ::sth::hlapiGen::process_modifier_offsetrefer {strblk name type} {
    
    #  hanlde the ipv missed the last number and multi types of ethernet
    set name_ori $name
    switch -regexp -- $type {
        "ipv4:"     {
            if {[regexp -nocase "l4" $type]} {
                set type "ipv4:ipv4"
                append type L4
            } else {
                set type "ipv4:ipv4"
                append type Outer
            }

        }
        "ipv6:"     {
            if {[regexp -nocase "l4" $type]} {
                set type "ipv6:ipv6"
                append type L4
            } else {
                set type "ipv6:ipv6"
                append type Outer
            }
        }
        "vlanOther" {
            array set vlan_other_modifier {}
        }

    }
    set vlan_other_name_list ""
    foreach obj_child [array names ::sth::hlapiGen::$strblk\_obj] {
        if {[regexp -nocase "modifier" $obj_child] && ![regexp -nocase "table" $obj_child]} {
            set obj_hdl [set ::sth::hlapiGen::$strblk\_obj($obj_child)]
            foreach hdl $obj_hdl {
                set offset_refer [set ::sth::hlapiGen::$strblk\_$hdl\_attr(-offsetreference)]
                if {[regexp "vlanOther" $type]} {
                    foreach vlan_name $name_ori {
                        if {[regexp -nocase $vlan_name $offset_refer]} {
                            set name $vlan_name
                            set vlan_other_name_list [concat $vlan_other_name_list $vlan_name]
                            break
                        }
                    }
                }
                if {[regexp -nocase $name $offset_refer]} {
                    regsub "$name" $offset_refer "$type" ::sth::hlapiGen::$strblk\_$hdl\_attr(-offsetreference)
                    if {[regexp "vlanOther" $type]} {
                        set vlan_other_modifier($name) $hdl
                    }
                    continue
                }
            }
            
        } elseif {[regexp -nocase "modifier" $obj_child] && [regexp -nocase "table" $obj_child]} {
            set tablemodifier_list [set ::sth::hlapiGen::$strblk\_obj($obj_child)]
            foreach tablemodifier $tablemodifier_list {
                set ref [set ::sth::hlapiGen::$strblk\_$tablemodifier\_attr(-offsetreference)]
                set vlan_name [lindex [split $ref "."] 2]
                set vlan_attr [lindex [split $ref "."] 3]
                set eth  [set ::sth::hlapiGen::$strblk\_obj(ethernet:ethernetii)]
                set vlans [set ::sth::hlapiGen::$eth\_obj(vlans)]
                if {[info exists ::sth::hlapiGen::$vlans\_obj(vlan)]} {
                    foreach vlan  [set ::sth::hlapiGen::$vlans\_obj(vlan)] {
                        set n [set ::sth::hlapiGen::$vlans\_$vlan\_attr(-name)]
                        if {$n == $vlan_name} {
                            set ::sth::hlapiGen::$vlans\_$vlan\_attr(-$vlan_attr) [lindex [set ::sth::hlapiGen::$vlans\_$vlan\_attr(-$vlan_attr)] 0]
                        }
                    }
                }
                unset ::sth::hlapiGen::$strblk\_$tablemodifier\_attr
                regsub $tablemodifier [set ::sth::hlapiGen::$strblk\_obj($obj_child)] "" ::sth::hlapiGen::$strblk\_obj($obj_child)
                if {[set ::sth::hlapiGen::$strblk\_obj($obj_child)] == ""} {
                    unset ::sth::hlapiGen::$strblk\_obj($obj_child)
                }
            }
        }
    }
    if {[regexp "vlanOther" $type] && [info exists vlan_other_modifier] && [llength [array names vlan_other_modifier]] > 0} {
        array set default_value "-modifiermode fixed -stepvalue 0 -recyclecount 1 -repeatcount 0"
        set name ""
        foreach n $name_ori {
            if {[regexp $n $vlan_other_name_list]} {
                set name [concat $name $n]
            }
        }
        foreach n $name {
            if {[info exists vlan_other_modifier($n)]} {
                set modifier_left_name $n
                break
            }
        }

        set modifier_left $vlan_other_modifier($modifier_left_name)
        if {[regexp "random" $modifier_left]} {
            set ::sth::hlapiGen::$strblk\_$modifier_left\_attr(-modifiermode) "random"
            if {[llength [array names vlan_other_modifier]] > 1} {
                set ::sth::hlapiGen::$strblk\_$modifier_left\_attr(-stepvalue) 0
            }
        }
        array set modifier_attr {}
        foreach n $name_ori {
            foreach attr [array names ::sth::hlapiGen::$strblk\_$modifier_left\_attr] {
                if {![regexp "offsetreference" $attr]} {
                    if {[info exists vlan_other_modifier($n)]} {
                        set modifier $vlan_other_modifier($n)
                        if {[info exists ::sth::hlapiGen::$strblk\_$modifier\_attr($attr)]} {
                            set value [set ::sth::hlapiGen::$strblk\_$modifier\_attr($attr)]
                        } elseif {[info exists default_value($attr)]} {
                            if {[regexp "modifiermode" $attr]} {
                               set value "random" 
                            } else {
                                set value $default_value($attr)
                            }
                        }
                        
                    } else {
                        if {[info exists default_value($attr)]} {
                            set value $default_value($attr)
                        } else {
                            set value [set ::sth::hlapiGen::$strblk\_$modifier_left\_attr($attr)]
                        }
                    }
                    if {[info exists modifier_attr($attr)]} {
                        set modifier_attr($attr) [concat $modifier_attr($attr) $value]
                    } else {
                        set modifier_attr($attr) $value
                    }
                }
            }
        }
        set len [llength $modifier_attr($attr)]
        set mode_list $modifier_attr(-modifiermode)
        for {set i 0} {$i < [expr [llength $modifier_attr($attr)] - 1]} {incr i -1} {
            set mode [lindex $mode_list $i]
            if {$mode == "fixed"} {
                set len [expr $len - 1]
            } else {
                break   
            }
        }
        foreach attr [array names modifier_attr] {
            set ::sth::hlapiGen::$strblk\_$modifier_left\_attr($attr) [lrange $modifier_attr($attr) 0 [expr $len - 1]]
        }

        set vlan_modifier_list ""
        for {set i 1} {$i < [llength $name]} {incr i} {
            set vlan_name [lindex $name $i]
            if {$vlan_name != $modifier_left_name} {
                if {[info exists vlan_other_modifier($vlan_name)]} {
                    set vlan_modifier_list [concat $vlan_modifier_list $vlan_other_modifier($vlan_name)]
                }
                
            }
            
        }
        foreach vlan_modifier $vlan_modifier_list {
            unset ::sth::hlapiGen::$strblk\_$vlan_modifier\_attr
            regsub {[0-9]+} $vlan_modifier "" modifier_type
            set all_modifier [set ::sth::hlapiGen::$strblk\_obj($modifier_type)]
            regsub $vlan_modifier $all_modifier "" all_modifier
            set ::sth::hlapiGen::$strblk\_obj($modifier_type) $all_modifier
            if {[set ::sth::hlapiGen::$strblk\_obj($modifier_type)] == ""} {
                unset ::sth::hlapiGen::$strblk\_obj($modifier_type)
            }
        }
    }
    
}

#this function is used to process the table modifier of tos
proc ::sth::hlapiGen::process_tos_modifier {strblk modifier_hdl offset} {
    variable ip_outer_hdl_list
    #get the tos obj
    regsub {\..*} $offset "" name
    set ip_hdl [get_handle_by_name $strblk [string tolower $name]]
    if {[lsearch $ip_outer_hdl_list $ip_hdl] < 0} {
        #currently we don't support the tos for ip outer header
        set tosdiffserv_hdl [set ::sth::hlapiGen::$ip_hdl\_obj(tosdiffserv)]
        set datalist [set ::sth::hlapiGen::$strblk\_$modifier_hdl\_attr(-data)]
        process_tos_diffserve $tosdiffserv_hdl $datalist
    }
            
}

#this function is used to process tos diffserv by combining multiple parameters
proc ::sth::hlapiGen::process_tos_diffserve {tosdiffserv datalist} {
    set new_value ""
    set precedence_list ""
    set tos_list ""
    foreach obj [array names ::sth::hlapiGen::$tosdiffserv\_obj] {
        foreach hdl [set ::sth::hlapiGen::$tosdiffserv\_obj($obj)] {
            switch -regexp -- $hdl {
                "tos" {
                    set arg "-dbit tbit rbit mbit"
                    if {[info exists ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr($arg)]} {
                        return
                    }
                    if {$datalist == "" } {
                        set binary_value [set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-dbit)]
                        append binary_value [set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-tbit)]
                        append binary_value [set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-rbit)]
                        append binary_value [set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-mbit)]
                        set new_value [::sth::hlapiGen::binToInt $binary_value]
                    } else {
                        #currently in hltapi the modifier of tos and precedence can't be configured together,
                        #so we set precedence with higher priority to do the table modifier
                        #if hltapi supports to config the two together, will delete the "return" below
                        foreach data $datalist {
                            set value_dec [format "%d" 0X$data]
                            if {$value_dec >= 32} {
                                set accumulate_times 32
                                set var  "precedence_list"
                            } else {
                                set accumulate_times 2
                                set var  "tos_list"
                            }
                            set value [expr $value_dec/$accumulate_times]
                            lappend $var $value
                        }
                        if {[llength $precedence_list] > 1} {
                            set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-precedence) $precedence_list
                            return
                        }
                        if {[llength $tos_list] > 1} {
                            array set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr "{-dbit tbit rbit mbit} {$tos_list}"
                            return
                        }
                        return
                    }
                    
                    array set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr "{-dbit tbit rbit mbit} {$new_value}"
                }
                "diffserv" {
                    set arg "-dscphigh dscplow"
                    if {[info exists ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr($arg)]} {
                        return
                    }
                    if {$datalist == ""} {
                        set dscp_high [set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-dscphigh)]
                        set dscp_low [set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr(-dscplow)]
                        set binary_dscp_high [sth::hlapiGen::decimal2binary $dscp_high 3]
                        set binary_dscp_low [sth::hlapiGen::decimal2binary $dscp_low 3]
                        set binary_dscp "$binary_dscp_high$binary_dscp_low"
                        set new_value [::sth::hlapiGen::binToInt $binary_dscp]
                    } else {
                        foreach data $datalist {
                            set value [format "%d" 0X$data]
                            set value [expr $value /4]
                            lappend new_value $value
                        }
                    }
                    array set ::sth::hlapiGen::$tosdiffserv\_$hdl\_attr "{-dscphigh dscplow} {$new_value}"
                }
            }
        }
    }
}

#this function is used to get the correct l3_length
proc ::sth::hlapiGen::process_l3_length {arg value} {
    variable traffic_headers_array
    variable vlan_outer_hdl
    variable vlan_other_hdl
    set diff_value 0
    set l2_encap $traffic_headers_array(l2_encap)
    switch -- $l2_encap {
        "ethernet_ii" {
            set diff_value 18
        }
        "ethernet_ii_vlan" {
            #check if the outer vlan exists
            if {[llength $vlan_other_hdl] != 0} {
                set diff_value [expr 18+8+4*[llength $vlan_other_hdl]]
            } elseif {$vlan_outer_hdl != ""} {
                set diff_value [expr 18+8]
            } else {
                set diff_value [expr 18+4]
            }
        }
        "ethernet_ii_pppoe" {
            set diff_value [expr 18+2+6]
        }
        "ethernet_ii_vlan_pppoe" {
            set diff_value [expr 18+2+6+4]
        }
        "ethernet_ii_qinq_pppoe" {
            set diff_value [expr 18+2+6+8]
        }
    }
    set value [expr $value - $diff_value]
    return $value
}

#this function is used to get the handle by the name using streamblock pduinfo
proc ::sth::hlapiGen::get_handle_by_name {strblkhdl name} {
    set ret_hdl ""
    
    set pdu_info [stc::get $strblkhdl -pduInfo]
    if {[regexp -nocase $name $pdu_info]} {
        foreach element $pdu_info {
            set name_update [string tolower $name]
            append name_update ,
            set name_index [string first $name_update [string tolower $element]]
            if {$name_index >=0} {
                set updatelist [split $element ,]
                set ret_hdl [lindex $updatelist 1]
                break
            }
        }
    }
    return $ret_hdl
}

#this function is used to add more info into current obj, such as: tos->ipv4.tosdiffserv.tos
proc ::sth::hlapiGen::add_parent_info {phdl obj} {
    set ancester [stc::get $phdl -parent]
    if {[regexp -nocase "ipv4" $ancester]} {
        set ancester "ipv4"
    } elseif {[regexp -nocase "ipv6" $ancester]} {
        set ancester "ipv6"
    } else {
        regsub -all {\d} $ancester "" ancester
    }
    regsub -all {\d} $phdl "" phdl
    set obj_hdl_list $ancester\.$phdl\.$obj
    
    return $obj_hdl_list
}

#this function is used to get the sub obj under the given handle
proc ::sth::hlapiGen::get_sub_obj {hdl} {
    set hdl_list ""
    if {[array exists ::sth::hlapiGen::$hdl\_obj]} {
        foreach ele [array names ::sth::hlapiGen::$hdl\_obj] {
            foreach sub_obj [set ::sth::hlapiGen::$hdl\_obj($ele)] {
                append hdl_list " $sub_obj"
                set ret_hdl [get_sub_obj $sub_obj]
                if {$ret_hdl != ""} {
                    append hdl_list " $ret_hdl"
                }
            }
        }
    }
    
    return $hdl_list
    
}

#this function is used to handle specific ospf header which is not included in trafficConfigTable.tcl and trafficConfigFunctions.tcl
proc ::sth::hlapiGen::traffic_config_specific_ospf {strblk traffic_ret} {
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
        
    set table_name "::sth::Traffic::trafficOspfTable"
    set cmd_name "traffic_config_ospf_packets"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    
    foreach obj [array names ::sth::hlapiGen::$strblk\_obj] {
        if {[regexp -nocase "ospf" $obj]} {
            set ospf_obj $obj
            set ospf_hdl [set ::sth::hlapiGen::$strblk\_obj($ospf_obj)]
            switch -- $obj {
                "ospfv2:ospfv2databasedescription" {set ospf_type dd}
                "ospfv2:ospfv2hello" {set ospf_type hello}
                "ospfv2:ospfv2linkstaterequest" {set ospf_type req}
                "ospfv2:ospfv2linkstateacknowledge" {set ospf_type ack}
                "ospfv2:ospfv2unknown" {set ospf_type unknown}
                "ospfv2:ospfv2linkstateupdate" {set ospf_type update}
            }
            break
        }
    }
    append hlapi_traffic_script "set stream_id \[keylget $traffic_ret stream_id\] \n"
    append hlapi_traffic_script "set streamblock_ospf_ret \[::sth::traffic_config_ospf    \\\n"
    append hlapi_traffic_script "			-mode		  create\\\n"
    append hlapi_traffic_script "			-stream_id	\$stream_id\\\n"
    append hlapi_traffic_script "			-type				packets\\\n"


    #udpate the data model info of ospf header
    array set ::sth::hlapiGen::$ospf_hdl\_$ospf_hdl\_attr [array get ::sth::hlapiGen::$strblk\_$ospf_hdl\_attr]
    array set ::sth::hlapiGen::$ospf_hdl\_obj "$ospf_obj $ospf_hdl"

    traffic_config_obj_attr $cmd_name $ospf_hdl
    
    #add the num param for the list
    process_ospf_params_list_num $cmd_name $ospf_type
    
    foreach arg [array names traffic_config_ospf_params] {
        if {[regexp -nocase "ospf_network_lsa_attached_router_id" $arg]} {
            regsub  {\_attachedrouters.*} $arg "" new_arg
            lappend traffic_config_ospf_params($new_arg) $traffic_config_ospf_params($arg)
            continue
        }
        append hlapi_traffic_script "-$arg $traffic_config_ospf_params($arg)\\\n"
    }
    
    if {[info exists traffic_config_ospf_params(ospf_network_lsa_attached_router_id)]} {
        set arg "ospf_network_lsa_attached_router_id"
        append hlapi_traffic_script "-$arg $traffic_config_ospf_params($arg)\\\n"
    }
    
    append hlapi_traffic_script "\]\n"
    append hlapi_traffic_script [gen_status_info_without_puts streamblock_ospf_ret "sth::traffic_config_ospf"]
    
    array unset traffic_config_ospf_params
    # if it is the update msg with routerlsalink and tos metric, call another function
    if {[regexp "update" $ospf_type]} {
        process_ospf_update_msg_header $ospf_hdl
    }
    
    

}

#this function is used for ospf header: the parameter is a list input and then the num needs to be calculated
proc ::sth::hlapiGen::process_ospf_params_list_num {cmd_name ospf_type} {
    variable traffic_config_ospf_params
    array set params_list_num ""
    
    switch -- $cmd_name {
        "traffic_config_ospf_packets" {
            switch -regexp -- $ospf_type {
                "dd|ack" {
                    array set params_list_num "ospf_lsa_age ospf_lsa_num"
                }
                "req" {
                    array set params_list_num "ospf_req_ls_type ospf_req_lsa_num"
                }
                "update" {
                     array set params_list_num "ospf_router_lsa_age ospf_router_lsa_num ospf_network_lsa_age ospf_network_lsa_num\
                                            ospf_summary_lsa_age ospf_summary_lsa_num ospf_summaryasbr_lsa_age ospf_summaryasbr_lsa_num\
                                            ospf_asexternal_lsa_age ospf_asexternal_lsa_num"
                }
                default {
                    return
                }     
                
            }
        }
        "traffic_config_ospf_update_router_lsa_link" {
            array set params_list_num "ospf_router_lsa_link_id ospf_router_lsa_link_num"
        }
        "traffic_config_ospf_update_router_lsa_tos" {
            array set params_list_num "ospf_router_lsa_tos_type ospf_router_lsa_tos_num"
        }
        "traffic_config_ospf_update_summary_lsa_tos" {
            array set params_list_num "ospf_summary_lsa_tos_reserved ospf_summary_lsa_tos_num"
        }
        "traffic_config_ospf_update_asexternal_lsa_tos" {
            array set params_list_num "ospf_asexternal_lsa_tos_ebit ospf_asexternal_lsa_tos_num"
        }
    }
    
    
    foreach arg [array names params_list_num] {
        if {[info exists traffic_config_ospf_params($arg)]} {
            set param_num $params_list_num($arg)
            array set traffic_config_ospf_params "$param_num [llength $traffic_config_ospf_params($arg)]"
        }
    }
}

#this function is used for ospf header: append the bit value in a string
proc ::sth::hlapiGen::process_ospf_options_list {phdl obj_handle obj} {
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
    set value ""
   
    switch -regexp -- $obj {
        "lsahdroptions" {
            set attr_list "-reserved7 -reserved6 -dcbit -eabit -npbit -mcbit -ebit -reserved0"
            if {[regexp -nocase "ospfv2lsaheader" $phdl]} {
                set param "ospf_lsa_header_options"
            } elseif {[regexp -nocase "header" $phdl]} {
                set parent [string tolower [stc::get $phdl -parent]]
                regsub "ospfv2" $parent "ospf_" param
                regsub -all {lsa\d$} $param "_lsa_header_options" param
            }
            
        }
        "hellooptions|ddoptions" {
            set attr_list "-reserved7 -reserved6 -dcbit -eabit -npbit -mcbit -ebit -reserved0"
            set param "ospf_packets_options"
        }
        "ddspecificoptions" {
            set attr_list "-reserved7 -reserved6 -reserved5 -reserved4 -reserved3 -ibit -mbit -msbit"
            set param "ospf_dd_options"
        }
        "routerlsaoptions" {
            set attr_list "-reserved7 -reserved6 -reserved5 -reserved4 -reserved3 -vbit -ebit -bbit"
            set param "ospf_router_lsa_options"
        }
    }
    
   
    foreach attr $attr_list {
        append value [set ::sth::hlapiGen::$phdl\_$obj_handle\_attr($attr)]
    }
    if {[info exists traffic_config_ospf_params($param)]} {
        set value_list $traffic_config_ospf_params($param)
        lappend value_list $value
        set traffic_config_ospf_params($param) $value_list
    } else {
        array set traffic_config_ospf_params "$param $value"
    }
}


#this function is used for ospf header: to save the info of the specific sub headers of update msg
proc ::sth::hlapiGen::pre_process_ospf_update_msg_header {phdl obj_handle obj} {
    switch -- $obj {
        "ospfv2routerlsalink" {
            variable ospf_update_router_lsa_link
            set var_name "ospf_update_router_lsa_link"
        }
        "ospfv2routerlsatosmetric" {
            variable ospf_update_router_lsa_tos
            set var_name "ospf_update_router_lsa_tos"
        }
        "ospfv2summarylsatosmetric" {
            variable ospf_update_summary_lsa_tos
            set var_name "ospf_update_summary_lsa_tos"
        }
        "ospfv2externallsatosmetric" {
            variable ospf_update_asexternal_lsa_tos
            set var_name "ospf_update_asexternal_lsa_tos"
        }
    }
    
    if {[info exists $var_name\($phdl\)]} {
        set obj_list [set $var_name\($phdl\)]
        lappend obj_list $obj_handle
        set $var_name\($phdl\) $obj_list
    } else {
        array set $var_name "$phdl $obj_handle"
    }
}

#this funciton is used for ospf header: to handle ospf update msg header
proc ::sth::hlapiGen::process_ospf_update_msg_header {ospf_hdl} {
    #get the routerlsalink and tos metric handle to config each function and table
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
    variable ospf_update_router_lsa_link
    variable ospf_update_router_lsa_tos
    variable ospf_update_summary_lsa_tos
    variable ospf_update_asexternal_lsa_tos
    array set ospf_ret_value ""
    
    set index_routerlsa 0
    set index_summaryasbrlsa 0
    set index_summarylsa 0
    set index_asexternallsa 0
    set updatedlsa_hdl [stc::get $ospf_hdl -children-updatedlsas]
    
    foreach ospfv2lsa [set ::sth::hlapiGen::$updatedlsa_hdl\_obj(ospfv2lsa)] {
        set ospfv2lsa_type [stc::get $ospfv2lsa -children]
        switch -regexp -- $ospfv2lsa_type {
            "routerlsa" {
                array set ospf_ret_value "$ospfv2lsa_type \"\[lindex \[keylget streamblock_ospf_ret update_router_lsa\] $index_routerlsa\]\""
                incr index_routerlsa
            }
            "summaryasbrlsa" {
                array set ospf_ret_value "$ospfv2lsa_type \"\[lindex \[keylget streamblock_ospf_ret update_summaryasbr_lsa\] $index_summaryasbrlsa\]\""
                incr index_summaryasbrlsa
            }
            "summarylsa" {
                array set ospf_ret_value "$ospfv2lsa_type \"\[lindex \[keylget streamblock_ospf_ret update_summary_lsa\] $index_summarylsa\]\""
                incr index_summarylsa
            }
            "asexternallsa" {
                array set ospf_ret_value "$ospfv2lsa_type \"\[lindex \[keylget streamblock_ospf_ret update_asexternal_lsa\] $index_asexternallsa\]\""
                incr index_asexternallsa
            }
        }
    }
    
    set ospf_ret_value_list [array get ospf_ret_value]
    if {[array exists ospf_update_router_lsa_link]} {
        set ospf_ret_value_list [process_ospf_update_link_tos "update_router_lsa_link" "update_router_lsa" "Ospfv2RouterLsaLink" $ospf_ret_value_list]
        array set ospf_ret_value $ospf_ret_value_list
    }
    
    if {[array exists ospf_update_router_lsa_tos]} {
        set ospf_ret_value_list [array get ospf_ret_value]
        process_ospf_update_link_tos "update_router_lsa_tos" "update_router_lsa_link" "Ospfv2RouterLsaTosMetric" $ospf_ret_value_list
    }
    
    if {[array exists ospf_update_summary_lsa_tos]} {
        process_ospf_update_link_tos "update_summary_lsa_tos" "update_summary_lsa" "Ospfv2SummaryLsaTosMetric" $ospf_ret_value_list
    }
    
    if {[array exists ospf_update_asexternal_lsa_tos]} {
        process_ospf_update_link_tos "update_asexternal_lsa_tos" "update_asexternal_lsa" "Ospfv2ExternalLsaTosMetric" $ospf_ret_value_list
    }
    
    
}

#this funciton is used for ospf header: to handle ospf update msg header
proc ::sth::hlapiGen::process_ospf_update_link_tos {type key_ret obj ospf_ret_value_list} {
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
    variable ospf_$type
    set index 1
    array set ospf_ret_value ""
    
    array set ospf_ret_value $ospf_ret_value_list
    foreach phdl [lsort [array names ospf_$type]] {
        if {[string match -nocase "update_router_lsa_tos" $type]} {
            set ospfv2routerlsalink_hdl [stc::get $phdl -parent]
            set ret_value_update $ospf_ret_value($ospfv2routerlsalink_hdl)
        } else {
            set ospfv2lsa [stc::get $phdl -parent]
            set ret_value_update $ospf_ret_value($ospfv2lsa)
        }
        
        append hlapi_traffic_script "set $key_ret$index $ret_value_update\n"
        append hlapi_traffic_script "set ospf_$type$index \[::sth::traffic_config_ospf    \\\n"
        append hlapi_traffic_script "			-mode		  create\\\n"
        append hlapi_traffic_script "			-stream_id	\$stream_id\\\n"
        append hlapi_traffic_script "			-type		 $type\\\n"
        append hlapi_traffic_script "			-phandle	 \$$key_ret$index\\\n"
        
        
        foreach hdl [set ospf_$type\($phdl\)] {
            process_obj_attr "::sth::Traffic::" "traffic_config_ospf_$type" $phdl $hdl $obj
        }
        
        process_ospf_params_list_num "traffic_config_ospf_$type" "update"
        
        foreach arg [array names traffic_config_ospf_params] {
            append hlapi_traffic_script "-$arg $traffic_config_ospf_params($arg)\\\n"
        }
        append hlapi_traffic_script "\]\n"
        append hlapi_traffic_script [gen_status_info_without_puts ospf_$type$index "sth::traffic_config_ospf"]
        
        if {[string match -nocase "update_router_lsa_link" $type]} {
            #save the return value to config router lsa metric later
            set index_tos_ret 0
            foreach ospfv2routerlsalink [set ::sth::hlapiGen::ospf_update_router_lsa_link($phdl)] {
                array set ospf_ret_value "$ospfv2routerlsalink \"\[lindex \[keylget ospf_update_router_lsa_link$index router_lsa_link_handle\] $index_tos_ret\]\""
                incr index_tos_ret
            }
        }
        array unset traffic_config_ospf_params
        incr index
    }
    
    set ospf_ret_value_list [array get ospf_ret_value]
    return $ospf_ret_value_list
}

# this function is used for fip header
proc ::sth::hlapiGen::traffic_config_specific_fip {strblk traffic_ret} {
    variable hlapi_traffic_script
    variable traffic_config_ospf_params
        
    set table_name "::sth::fcoetraffic::fcoetrafficTable"
    set cmd_name "fip_traffic_config"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    
    append hlapi_traffic_script "set stream_id \[keylget $traffic_ret stream_id\] \n"
    append hlapi_traffic_script "set streamblock_fip_ret \["
    append hlapi_traffic_script "::sth::$cmd_name    \\\n"
    append hlapi_traffic_script "			-mode		  create\\\n"
    append hlapi_traffic_script "			-handle		  \$stream_id\\\n"
    
    set fip_hdl [set ::sth::hlapiGen::$strblk\_obj(fc:fip)]
    process_obj_attr "::sth::fcoetraffic::" $cmd_name $strblk $fip_hdl "fc:fip"
    
    set dl_hdl [set ::sth::hlapiGen::$fip_hdl\_obj(dl)]
    if {[info exists ::sth::hlapiGen::$fip_hdl\_$dl_hdl\_attr(-children)]} {
        set dl_choice_list [set ::sth::hlapiGen::$fip_hdl\_$dl_hdl\_attr(-children)]
        set dl_value_list ""
        array set attrlist ""
        set subhdllist ""
        foreach dl_choice $dl_choice_list {
            set dl_type ""
            set subhdl ""
            array set attrlist ""
            set sub_dl_hdl [stc::get $dl_choice -children]
            switch -regexp -- $sub_dl_hdl {
                "vlandescriptor" {
                    array set attrlist "vlanid vlanid"
                    set dl_type "vlan"
                }
                "priority" {
                    array set attrlist "priority priority priority_reserved reserved"
                    set dl_type "priority"
                }
                "macaddr" {
                    array set attrlist "macaddr macaddr"
                    set dl_type "macaddr"
                }
                "fcmap" {
                    array set attrlist "fcmap_reserved reserved fcmap fcmap"
                    set dl_type "fcmap"
                }
                "nameid" {
                    array set attrlist "nameid_reserved reserved nameid nameid"
                    set dl_type "nameid"
                }
                "fabricname" {
                    array set attrlist "fabricname_reserved reserved fabricname fabricname"
                    set dl_type "fabricname"
                }
                "maxrcvsize" {
                    array set attrlist "maxrcvsize maxreceivesize"
                    set dl_type "maxrcvsize"
                }
                "vxportid" {
                    array set attrlist "vxport_macaddr macaddr vxport_reserved reserved vxport_addrid addressidentifier vxport_portname portname"
                    set dl_type "vxport"
                }
                "fkaadvperiod" {
                    array set attrlist "fkaadvperiod fkaadvperiod fka_reserved reserved"
                    set dl_type "fka_adv_period"
                }
                "vendorid" {
                    array set attrlist "vendorid vendorid vendorid_reserved reserved"
                    set dl_type "vendorid"
                }
                "flogirequest" {
                    array set attrlist "flogireq_reserved reserved"
                    set dl_type "flogireq"
                    set flogi [set ::sth::hlapiGen::$sub_dl_hdl\_obj(flogi)]
                    set fc [set ::sth::hlapiGen::$flogi\_obj(fc)]
                    set subhdl "$flogi $fc"
                }
                "flogiaccept" {
                    array set attrlist "flogiacc_reserved reserved"
                    set dl_type "flogiacc"
                    set flogi_acc [set ::sth::hlapiGen::$sub_dl_hdl\_obj(flogiacc)]
                    set fc [set ::sth::hlapiGen::$flogi_acc\_obj(fc)]
                    set subhdl "$flogi_acc $fc"
                }
                "flogireject" {
                    array set attrlist "flogirjt_reserved reserved"
                    set dl_type "flogirjt"
                    set flogi_rjt [set ::sth::hlapiGen::$sub_dl_hdl\_obj(flogirjt)]
                    set fc [set ::sth::hlapiGen::$flogi_rjt\_obj(fc)]
                    set subhdl "$flogi_rjt $fc"
                }
                "npivfdiscrequest" {
                    array set attrlist "fdiscreq_reserved reserved"
                    set dl_type "fdiscreq"
                    set fdisc [set ::sth::hlapiGen::$sub_dl_hdl\_obj(fdisc)]
                    set fc [set ::sth::hlapiGen::$fdisc\_obj(fc)]
                    set subhdl "$fdisc $fc"
                }
                "npivfdiscaccept" {
                    array set attrlist "fdiscacc_reserved reserved"
                    set dl_type "fdiscacc"
                    set fdisc_acc [set ::sth::hlapiGen::$sub_dl_hdl\_obj(fdiscacc)]
                    set fc [set ::sth::hlapiGen::$fdisc_acc\_obj(fc)]
                    set subhdl "$fdisc_acc $fc"
                }
                "npivfdiscreject" {
                    array set attrlist "fdiscrjt_reserved reserved"
                    set dl_type "fdiscrjt"
                    set fdisc_rjt [set ::sth::hlapiGen::$sub_dl_hdl\_obj(fdiscrjt)]
                    set fc [set ::sth::hlapiGen::$fdisc_rjt\_obj(fc)]
                    set subhdl "$fdisc_rjt $fc"
                }
                "fabriclogorequest" {
                    array set attrlist "logoreq_reserved reserved"
                    set dl_type "logoreq"
                    set logo [set ::sth::hlapiGen::$sub_dl_hdl\_obj(logo)]
                    set fc [set ::sth::hlapiGen::$logo\_obj(fc)]
                    set subhdl "$logo $fc"
                }
                "fabriclogoaccept" {
                    array set attrlist "logoacc_reserved reserved"
                    set dl_type "logoacc"
                    set logo_acc [set ::sth::hlapiGen::$sub_dl_hdl\_obj(logoacc)]
                    set fc [set ::sth::hlapiGen::$logo_acc\_obj(fc)]
                    set subhdl "$logo_acc $fc"
                }
                "fabriclogoreject" {
                    array set attrlist "logorjt_reserved reserved"
                    set dl_type "logorjt"
                    set logo_rjt [set ::sth::hlapiGen::$sub_dl_hdl\_obj(logorjt)]
                    set fc [set ::sth::hlapiGen::$logo_rjt\_obj(fc)]
                    set subhdl "$logo_rjt $fc"
                }
                "elprequest" {
                    array set attrlist "elpreq_reserved reserved"
                    set dl_type "elpreq"
                    set elp [set ::sth::hlapiGen::$sub_dl_hdl\_obj(elp)]
                    set subhdllist [concat $subhdllist $elp]
                }
                "elpaccept" {
                    array set attrlist "elpacc_reserved reserved"
                    set dl_type "elpacc"
                    set elp [set ::sth::hlapiGen::$sub_dl_hdl\_obj(elp)]
                    set subhdllist [concat $subhdllist $elp]
                }
                "elpreject" {
                    array set attrlist "elprjt_reserved reserved"
                    set dl_type "elprjt"
                    set elp_rjt [set ::sth::hlapiGen::$sub_dl_hdl\_obj(elprjt)]
                    set fc [set ::sth::hlapiGen::$elp_rjt\_obj(fc)]
                    set subhdl "$elp_rjt $fc"
                }
            }
            
            if {$dl_type != ""} {
                set dl_value_list [concat $dl_value_list $dl_type]    
            }
            if {$subhdl != ""} {
                foreach hdl $subhdl {
                    if {[lsearch $subhdllist $hdl] < 0} {
                        set subhdllist [concat $subhdllist $hdl]
                    }
                }
            }
            foreach attr [array names attrlist] {
                set attr_value [stc::get $sub_dl_hdl -$attrlist($attr)]
                append hlapi_traffic_script "-$attr    $attr_value\\\n"
            }
            
            array unset attrlist
        }
        
        append hlapi_traffic_script "-dl_id		  \{$dl_value_list\}\\\n"
    
        
        #fc sub header and pl_*** : hltapi only provides the same configuration of fc header for different dl headres. so we only get one fc header as delegate
        process_fcoe_fip_pl_params $subhdllist $cmd_name 
    }
    append hlapi_traffic_script "\]\n"
    append hlapi_traffic_script [gen_status_info_without_puts streamblock_fip_ret "sth::fip_traffic_config"]
}

#this function is mainly used to config the parameters whose stcobj is a choice
proc ::sth::hlapiGen::process_fcoe_fip_pl_params {hdl_list cmd_name} {
    variable hlapi_traffic_script
    array set traffic_config_fcoe_fip_params ""
    set name_space "::sth::fcoetraffic::"
    foreach hdl $hdl_list {
        regsub {\d+$} $hdl "" obj
        set phdl [stc::get $hdl -parent]
        foreach arg [array names $name_space$cmd_name\_stcobj] {
            set obj_in_table [string tolower [set $name_space$cmd_name\_stcobj($arg)]]
            set attr_in_table [string tolower [set $name_space$cmd_name\_stcattr($arg)]]
            
            if {[info exists traffic_config_fcoe_fip_params($arg)] || ![regexp -nocase $obj $obj_in_table]} {
                continue
            }
            
            if {[regexp {\-} $obj_in_table]} {
                set obj_in_table_list [split $obj_in_table -]
                set objlist  [lindex $obj_in_table_list 0]
                set obj_in_table_len [llength $obj_in_table_list]
                set sub_hdl1 $hdl
                for {set i 1} {$i < $obj_in_table_len} {incr i} {
                    set sub_obj [lindex $obj_in_table_list $i]
                    set sub_hdl[expr $i + 1] [set ::sth::hlapiGen::[set sub_hdl$i]\_obj($sub_obj)]
                }
                set hdl_tmp [set sub_hdl$obj_in_table_len]
                set phdl_tmp [set sub_hdl[expr $obj_in_table_len - 1]]
                # update may need here for other header
                regsub {\d+$} $sub_hdl2 "" obj_tmp 
                set supported_params [set ::sth::fcoetraffic::$obj_tmp]
                foreach param [array names ::sth::hlapiGen::$phdl_tmp\_$hdl_tmp\_attr] {
                    regsub {\-} $param "" param
                    if {![regexp -nocase $param $supported_params]} {
                        unset ::sth::hlapiGen::$phdl_tmp\_$hdl_tmp\_attr(-$param)
                    }
                }
                set value_list [array get ::sth::hlapiGen::$phdl_tmp\_$hdl_tmp\_attr]
                array set traffic_config_fcoe_fip_params "$arg    \{$value_list\}"
                
            } else {
                foreach new_obj [split $obj_in_table /] {
                    if {[string match -nocase $new_obj $obj]} {
                        if {[info exists ::sth::hlapiGen::$phdl\_$hdl\_attr(-$attr_in_table)]} {
                            set value [set sth::hlapiGen::$phdl\_$hdl\_attr(-$attr_in_table)]
                            array set traffic_config_fcoe_fip_params "$arg    $value"
                        }
                    }
                }
            }
        }
    }
    
    foreach param [lsort -dictionary [array names traffic_config_fcoe_fip_params]] {
        set value $traffic_config_fcoe_fip_params($param)
        if {[llength $value] > 1} {
            set value \{$value\}
        }
        append hlapi_traffic_script "-$param    $value\\\n"
    }
    
}

#this function is used to start the streamblock under the givein porthandle
proc ::sth::hlapiGen::hlapi_gen_start_streams {portlist strblklist} {
    set hlapi_traffic_script ""
    set comments ""
    set port_list ""
    append comments "\n##############################################################\n"
    append comments "#start traffic\n"
    append comments "##############################################################\n"
    puts_to_file $comments
    
    if {$strblklist == ""} {
        return
    }
    set port_lag_list ""
    set port_handle_list ""
    set portoptions  [stc::get project1 -children-portoptions]
    set aggregatorresult [stc::get $portoptions -AggregatorResult] 
    foreach port_handle $portlist {
        set lag_handle [stc::get $port_handle -children-lag]
        if {$lag_handle ne ""} {
            lappend port_lag_list $port_handle
        } elseif { $lag_handle eq  "" } {
           lappend port_handle_list $port_handle
        }
    }
    if { $port_lag_list ne "" && [regexp -nocase "aggregated" $aggregatorresult]} {
        set portlist $port_lag_list
    } else {
        set portlist  $port_handle_list
    }
    foreach port $portlist {
        append port_list "$::sth::hlapiGen::port_ret($port) "
    }
        
    append hlapi_traffic_script "set traffic_ctrl_ret \[::sth::traffic_control    \\\n"
    append hlapi_traffic_script "			-port_handle			\"$port_list\"\\\n"
    append hlapi_traffic_script "			-action			        run\\\n"
    #check if the duration needs to be configured
    foreach port $portlist {
        set generator_hdl [set ::sth::hlapiGen::$port\_obj(generator)]
        set generator_cfg_hdl [set ::sth::hlapiGen::$generator_hdl\_obj(generatorconfig)]
        if {[info exists ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-actionduration)]} {
            append hlapi_traffic_script "-duration	[set ::sth::hlapiGen::$generator_hdl\_$generator_cfg_hdl\_attr(-actionduration)]\\\n"
            break
        }
    }
    append hlapi_traffic_script "\]\n"
    puts_to_file $hlapi_traffic_script
    gen_status_info traffic_ctrl_ret "sth::traffic_control"
}

#this function is used to get the traffic results
proc ::sth::hlapiGen::hlapi_gen_stream_results {portlist strblklist} {
    set hlapi_traffic_script ""
    set comments ""
    set port_list ""
    
    append comments "\n##############################################################\n"
    append comments "#start to get the traffic results\n"
    append comments "##############################################################\n"
    puts_to_file $comments
    
    if {$strblklist == ""} {
        return
    }
    set port_lag_list ""
    set port_handle_list ""
    set portoptions  [stc::get project1 -children-portoptions]
    set aggregatorresult [stc::get $portoptions -AggregatorResult] 
    foreach port_handle $portlist {
        set lag_handle [stc::get $port_handle -children-lag]
        if {$lag_handle ne ""} {
            lappend port_lag_list $port_handle
        } elseif { $lag_handle eq  "" } {
            lappend port_handle_list $port_handle
        }
    }
    if { $port_lag_list ne "" && [regexp -nocase "aggregated" $aggregatorresult]} {
        set portlist $port_lag_list
    } else {
        set portlist  $port_handle_list
    }
    foreach port $portlist {
        append port_list "$::sth::hlapiGen::port_ret($port) "
    }
    append hlapi_traffic_script "set traffic_results_ret \[::sth::traffic_stats    \\\n"
    append hlapi_traffic_script "			-port_handle			\"$port_list\"\\\n"
    append hlapi_traffic_script "			-mode			        all\\\n"
    append hlapi_traffic_script "\]\n"
    puts_to_file $hlapi_traffic_script
    gen_status_info_for_results traffic_results_ret "sth::traffic_stats"
}


#this function is to handle fcoe traffic:fcoe_traffic_config
proc ::sth::hlapiGen::handle_fcoe_traffic {strblk traffic_ret} {

    variable hlapi_traffic_script

    set table_name "::sth::fcoetraffic::fcoetrafficTable"
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name "fcoe_traffic_config"
    ::sth::sthCore::InitTableFromTCLList [set $table_name]

    set strChildList [stc::get $strblk -children]
    set payloadList ""
    foreach child $strChildList {
        switch -regexp -- $child {
            "fc:fcoeheader\\d" {
                set fcheader $child
            }
            "fc:fc\\d" {
                set fcfc $child
            }
            "fcp:fcpcmnddl\\d" {
                set fcpcmnddl $child
            }
            "scsi:" {
                #handle pl_cdbtype
                set cdbobj $child
                switch -regexp -- $child {
                    cdb6 {
                        set  pl_cdbtype  cdb6
                        set cdbobjname cdb6
                    }
                    cdb10 {
                        set  pl_cdbtype  cdb10
                        set cdbobjname cdb10
                    }
                    xdread10 {
                        set  pl_cdbtype  xd_r10
                        set cdbobjname xdread10
                    }
                    xdwrite10 {
                        set  pl_cdbtype  xd_w10
                        set cdbobjname xdwrite10
                    }
                    read6 {
                        set  pl_cdbtype  r_6
                        set cdbobjname read6
                    }
                    read10 {
                        set  pl_cdbtype  r_10
                        set cdbobjname read10
                    }
                    readbuffer {
                        set  pl_cdbtype  r_buff
                        set cdbobjname readbuffer
                    }
                    readlong10 {
                        set  pl_cdbtype  r_l10
                        set cdbobjname readlong10
                    }
                    readcapacity10 {
                        set  pl_cdbtype  r_capacity10
                        set cdbobjname readcapacity10
                    }
                    write6 {
                        set  pl_cdbtype  w_6
                        set cdbobjname write6
                    }
                    write10 {
                        set  pl_cdbtype  w_10
                        set cdbobjname write10
                    }
                    writebuffer {
                        set  pl_cdbtype  w_buff
                        set cdbobjname writebuffer
                    }
                    writelong10 {
                        set  pl_cdbtype  w_l10
                        set cdbobjname writelong10
                    }
                    writeandverify10 {
                        set  pl_cdbtype  w_verify10
                        set cdbobjname writeandverify10
                    }
                    startstopunit {
                        set  pl_cdbtype  ssu
                        set cdbobjname startstopunit
                    }
                    modesense6 {
                        set  pl_cdbtype  ms_6
                        set cdbobjname modesense6
                    }
                    modesense10 {
                        set  pl_cdbtype  ms_10
                        set cdbobjname modesense10
                    }
                    reportluns {
                        set  pl_cdbtype  r_lun
                        set cdbobjname reportluns
                    }

                }
            }
            "fcsw:" -
            "fcgs:" -
            "custom:custom" -
            "fcp:fcpcmnd" -
            "fc:" {
                append payloadList "$child "
            }
        }
    }

    set childParams ""

    foreach para "version reserved1 reserved2 reserved3 reserved4 sof eof reserved5" {
        set $name_space$cmd_name\_stcobj($para)  "fc:fcoeheader"
    }
    if {[info exists fcheader]} {
        get_attr $fcheader $fcheader
        foreach fcheader_obj [array names ::sth::hlapiGen::$fcheader\_obj] {
            append childParams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $fcheader $fcheader $fcheader_obj]
        }
    }

    foreach para "h_rctl h_type h_csctl h_did h_sid h_framecontrol h_seqid h_dfctl h_seqcnt h_origexchangeid h_responseexchangeid h_parameter" {
        set $name_space$cmd_name\_stcobj($para)  "fc:fc"
    }
    if {[info exists fcfc]} {
        get_attr $fcfc $fcfc
        foreach fcfc_obj [array names ::sth::hlapiGen::$fcfc\_obj] {
            append childParams [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $fcfc $fcfc $fcfc_obj]
        }
    }

    #handle payloadList into childParams
    #pl_id mapping
    array set pl_id_map "custom:custom custom fc:elsplogi plogireq fc:elsplogi plogiacc
    fc:elslsrjt plogirjt fc:elsflogi flogireq fc:elsflogilsacc flogiacc
    fc:elslsrjt flogirjt fc:elsflogi fdiscreq fc:elsflogilsacc fdiscacc
    fc:elslsrjt fdiscrjt  fc:elslogo logoreq  fc:elslogolsacc logoacc
    fc:elslsrjt logorjt fcp:fcpcmnd fcpcmnd fcsw:efpreq efpreq
    fcsw:efpacc efpacc fcsw:diareq diareq fcsw:diaacc diaacc fcsw:escreq escreq
    fcsw:escacc escacc fcsw:hloreq hloreq fcsw:lsureq lsureq fcsw:lsareq lsareq
    fcgs:ganxtaccept ganxtacc fcgs:gpnidaccept gpnidacc fcgs:gnnidaccept gnnidacc
    fcgs:gcsidaccept gcsidacc fcgs:gftidaccept gftidacc fcgs:gptidaccept gptidacc
    fcgs:gfpnidaccept gfpnidacc fcgs:gspnidaccept gspnidacc fcgs:gffidaccept gffidacc
    fcgs:gidpnaccept gidpnacc fcgs:gidnnaccept gidnnacc fcgs:gsnnnnaccept gsnnnnacc
    fcgs:gidftaccept gidftacc fcgs:gpnftaccept  gpnftacc fcgs:gnnftaccept gnnftacc
    fcgs:rsnnnn rsnnnn fcgs:rffid rffid fcgs:rspnid rspnid fcgs:rptid rptid
    fcgs:rftid rftid fcgs:rcsid rcsid fcgs:rnnid rnnid fcgs:rpnid rpnid fcgs:daid daid
    fcsw:mreq mergereq fcsw:mreqacc  mergereqacc"
    set payloadnameList ""
    set pl_idList ""

    array set pl_id_obj "custom customPayload plogireq plogirequest plogiacc plogiaccept \
    plogirjt plogireject flogireq flogirequest flogiacc flogiaccept flogirjt flogireject \
    fdiscreq fdiscrequest fdiscacc fdiscaccept fdiscrjt fdiscreject logoreq logorequest \
    logoacc logoaccept logorjt logoreject fcpcmnd fcpcmnd efpreq efprequest \
    efpacc efpaccept diareq diarequest diaacc diaaccept escreq escrequest escacc escaccept \
    hloreq hlorequest lsureq lsurequest lsareq lsarequest ganxtacc ganxtaccept \
    gpnidacc gpnidaccept gpnidacc gpnidaccept gnnidacc gnnidaccept gcsidacc gcsidaccept \
    gftidacc gftidaccept gptidacc gptidaccept gffidacc gffidaccept gfpnidacc gfpnidaccept \
    gidpnacc gidpnaccept gidnnacc gidnnaccept gsnnnnacc gsnnnnaccept  gspnidacc gspnidaccept \
    gidftacc gidftaccept gpnftacc gpnftaccept gnnftacc gnnftaccept rsnnnn rsnnnn rffid rffid \
    rspnid rspnid rptid rptid rftid rftid rcsid rcsid rnnid rnnid rpnid rpnid daid daid \
    mergereq mergerequest mergereqacc  mergerequestacc"

    foreach payload $payloadList {

        regsub {\d+$} $payload "" payloadtype

        if {![regexp -nocase $payloadtype [array names pl_id_map]]} {
            continue
        }

        if {[info exists payloadtype]} {

            switch -exact -- $payloadtype {
                "fc:elsplogi" {
                    #command plogireq 03000000   plogiacc 02000000
                    set command [stc::get $payload -command]
                    if {$command eq "03000000"} {
                        append pl_idList "plogireq "
                        set payloadname $pl_id_obj(plogireq)
                    } else {
                        append pl_idList "plogiacc "
                        set payloadname $pl_id_obj(plogiacc)    
                    }
                }
                "fc:elsflogi" {
                    set command [stc::get $payload -command]
                    #flogireq 04000000  fdiscreq 51000000
                    if {$command eq "04000000"} {
                        append pl_idList "flogireq "
                        set payloadname $pl_id_obj(flogireq)
                    } else {
                        append pl_idList "fdiscreq "
                        set payloadname $pl_id_obj(fdiscreq)    
                    }
                }
                "fc:elsflogilsacc" {
                    set command [stc::get $payload -command]
                    #flogiacc 02000000 fdiscacc 51000000
                    if {$command eq "02000000"} {
                        append pl_idList "flogiacc "
                        set payloadname $pl_id_obj(flogiacc)
                    } else {
                        append pl_idList "fdiscacc "
                        set payloadname $pl_id_obj(fdiscacc)    
                    }
                }
                "custom:custom" {
                    append pl_idList "$pl_id_map($payloadtype) "
                    set payloadname $pl_id_obj($pl_id_map($payloadtype))
                    append childParams "-pl_payload         [stc::get $payload -pattern]\\\n"
                }
                "fc:elslsrjt" -
                default {
                    append pl_idList "$pl_id_map($payloadtype) "
                    set payloadname $pl_id_obj($pl_id_map($payloadtype))
                }
            }
            
            #according payloadname to find all parameters about it
            foreach param [array names $name_space$cmd_name\_stcobj] {
                set hltapiobj [set $name_space$cmd_name\_stcobj($param)]
                if {[regexp -nocase $payloadname $hltapiobj]} {
                    if {[regexp -nocase "\\-" $hltapiobj]} {
                        regsub -all "pl_" $param "" param_child
                        set attrlevel [llength [split $hltapiobj -]]
                        if {$attrlevel == 2} { 
                            set attr [lindex [split $hltapiobj -] 1]
                            set attrList ""
                            if {[regexp -nocase $attr [stc::get $payload -children]]} {
                                if {[info exists ::sth::fcoetraffic::$param_child]} {
                                    
                                    foreach arg [set ::sth::fcoetraffic::$param_child] {
                                        switch -- $arg {
                                            endtoendcredit {
                                                set argnew nxportendtoendcredit
                                            }
                                            serviceoptions {
                                                set argnew options
                                            }
                                            ictl {
                                                set argnew initiatorCtrl
                                            }
                                            rctl {
                                                set argnew recipientCtrl
                                            }
                                            default {
                                                set argnew  $arg
                                            }
                                        }
                                        if {[regexp -nocase $argnew [stc::get [stc::get $payload -children-$attr]]]} {
                                            append  attrList "-$arg [stc::get [stc::get $payload -children-$attr] -$argnew] "
                                        }
                                    }
                                    if {$attrList ne ""} {
                                        append childParams "-$param         \"$attrList\"\\\n"
                                        set $name_space$cmd_name\_stcobj($param) "_none_"
                                    }
                                }
                            } else {
                                if {[regexp -nocase $attr [stc::get $payload]]} {
                                    append childParams "-$param         [stc::get $payload -$attr]\\\n"
                                    set $name_space$cmd_name\_stcobj($param) "_none_"
                                }
                            }
                        } else {
                            if {![regsub -all "pl_"  $param "" attr]} {
                                continue
                            }
                            if {$attrlevel == 3} { 
                                set childname [lindex [split $hltapiobj -] 1]
                                if {[regexp -nocase $childname [stc::get $payload -children]]} {
                                    set child [stc::get $payload -children-$childname]
                                    set child2name [lindex [split $hltapiobj -] 2]
                                    set attrList ""
                                    if {[regexp -nocase $child2name [stc::get $child -children]]} {
                                        set child2 [stc::get $child -children-$child2name]
                                        if {[info exists ::sth::fcoetraffic::$param_child]} {
                                            
                                            foreach arg [set ::sth::fcoetraffic::$param_child] {
                                                if {[regexp -nocase $arg [stc::get $child2]]} {
                                                    append  attrList "-$arg [stc::get $child2 -$arg] "
                                                }
                                            }
                                        }
                                    }
                                    if {$attrList ne ""} {
                                        append childParams "-$param         \"$attrList\"\\\n"
                                        set $name_space$cmd_name\_stcobj($param) "_none_"
                                    }
                                }
                            }
                            if {$attrlevel == 4} { 
                                set childname [lindex [split $hltapiobj -] 1]
                                if {[regexp -nocase $childname [stc::get $payload -children]]} {
                                    set child [stc::get $payload -children-$childname]
                                    set child2name [lindex [split $hltapiobj -] 2]
                                    set attrList ""
                                    if {[regexp -nocase $child2name [stc::get $child -children]]} {
                                        set child2 [stc::get $child -children-$child2name]
                                        set child3name [lindex [split $hltapiobj -] 3]
                                        if {[regexp -nocase $child3name [stc::get $child2 -children]]} {
                                            set child3 [stc::get $chil2 -children-$child3name]
                                            if {[info exists ::sth::fcoetraffic::$param_child]} {
                                                
                                                foreach arg [set ::sth::fcoetraffic::$param_child] {
                                                    if {[regexp -nocase $arg [stc::get $child3]]} {
                                                        append  attrList "-$arg [stc::get $child3 -$arg] "
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    if {$attrList ne ""} {
                                        append childParams "-$param         \"$attrList\"\\\n"
                                        set $name_space$cmd_name\_stcobj($param) "_none_"
                                    }
                                }
                            }
                        }
                    } else {
                        #config attr obj directly
                        set attr [set $name_space$cmd_name\_stcattr($param)]
                        switch -- $attr {
                            nportname {
                                set attrnew portname
                            }
                            nodename {
                                set attrnew nodeorfabricname
                            }
                            reasonCode {
                                set attrnew reason
                            }
                            reasonExplanation {
                                set attrnew explanation
                            }
                            reserved1 {
                                set attrnew reserved
                                if {[regexp -nocase $attr [stc::get $payload]]} {
                                    set attrnew $attr
                                }
                            }
                            default {
                                set attrnew  $attr
                            }
                        }
                        if {("_none_" ne $attrnew)&& [regexp -nocase $attrnew [stc::get $payload]]} {
                            if {"" ne [stc::get $payload -$attrnew]} {
                                if {"pl_porttype" eq $param} {
                                    switch -exact -- [stc::get $payload -$attrnew] {
                                        "00" {
                                            set porttype "unidentified"
                                        }
                                        "7f" {
                                            set porttype "nxport"
                                        }
                                        "02" {
                                            set porttype "nlport"
                                        }
                                        "01" {
                                            set porttype "nport"
                                        }
                                        "82" {
                                            set porttype "flport"
                                        }
                                        "81" {
                                            set porttype "fport"
                                        }
                                        "03" {
                                            set porttype "fnlport"
                                        }
                                        "84" {
                                            set porttype "eport"
                                        }
                                        "85" {
                                            set porttype "bport"
                                        }
                                        default {
                                            continue    
                                        }
                                    }
                                    append childParams "-$param         $porttype\\\n"
                                } else {
                                    append childParams "-$param         [stc::get $payload -$attrnew]\\\n"
                                }
                                set $name_space$cmd_name\_stcobj($param) "_none_"
                            }
                        }
                    }
                }
            }
        }
    }
    if {$pl_idList eq ""} {
        return
    }
    if {[info exists pl_cdbtype]} {
        append childParams "-pl_cdbtype         $pl_cdbtype\\\n"
        #handle the attr cdbobj cdbobjname
        foreach param [array names $name_space$cmd_name\_stcobj] {
            set hltapiobj [set $name_space$cmd_name\_stcobj($param)]
            if {[regexp -nocase $cdbobjname $hltapiobj]} {
                set attr [set $name_space$cmd_name\_stcattr($param)]
                if {[regexp -nocase $attr [stc::get $cdbobj]]} {
                    append childParams "-$param         [stc::get $cdbobj -$attr]\\\n"
                    set $name_space$cmd_name\_stcobj($param) "_none_"
                }
            }
        }
    }
    append childParams "-pl_id         $pl_idList\\\n"

    append hlapi_traffic_script "\nset stream_id \[keylget $traffic_ret stream_id\]\n\n"

    append hlapi_traffic_script "set stream_fcoe_ret \[sth::$cmd_name\\\n"
    append hlapi_traffic_script "-handle         \$stream_id\\\n"
    append hlapi_traffic_script "-mode         create\\\n"
    append hlapi_traffic_script $childParams
    append hlapi_traffic_script "\]\n"
    append hlapi_traffic_script [gen_status_info_without_puts stream_fcoe_ret $cmd_name]
}

