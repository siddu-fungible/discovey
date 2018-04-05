namespace eval ::sth::hlapiGen:: {
    #device_ret is used to store the name of the var returned from the confgiure fuinction, the key is the device hnd in the xml.
    variable device_ret
    variable port_ret
    #used to store on which devie on protocol is configured, used in the ctrl and result function
    variable protocol_to_devices
    #used to store on which port on protocol is configured, used in the ctrl and result function
    variable protocol_to_ports
    #used to store the device handle for the specific object, used in scaling test
    variable devicelist_obj
    #used to store the parameter value for scaling
    variable scaling_tmp
    #remeber md_level_step for eoam which object is under project1
    variable md_level_step ""
    #to avoid outputting the params of same objects used in different hlt commands
    variable subclass_obj_dup ""
    variable eoam_router_without_control ""
    variable dhcpv4serverconfigured
    variable dhcpv6serverconfigured
    variable dhcpv4portconfigured
    variable currentconfighandle ""
    variable dhcpv6portconfigured
    variable device_index_scaling
    variable scaling_format    ""
    variable scaling_lrange    0
    variable test_config    1
    variable test_control   1
    variable online         1
    variable test_run       1
    variable test_result    1
    variable pkt_capture    0
    variable device_info    1
    variable traffic        1
    variable scaling_test   0
    variable interface_config     1
    variable output_type          tcl
    variable default_value  1
    variable savexml              0
    variable default_yaml              0

    variable v_plugins	{}
    variable v_linkmap

    ##add for L3_forwarding link
    variable links_gen
    #To map profile and http
    variable profile_to_http
    #To map devices to httphandle
    variable devices_to_httphandle
    variable testCaseStart
}

proc ::sth::hlapi_gen {args} {

    set ::sth::hlapiGen::test_config 1
    set ::sth::hlapiGen::test_control 1
    set ::sth::hlapiGen::online 1
    set ::sth::hlapiGen::test_run 1
    set ::sth::hlapiGen::test_result 1
    set ::sth::hlapiGen::pkt_capture 0
    set ::sth::hlapiGen::device_info 1
    set ::sth::hlapiGen::traffic 1
    set ::sth::hlapiGen::scaling_test 0
    set ::sth::hlapiGen::interface_config 1
    set ::sth::hlapiGen::savexml     0
    set ::sth::hlapiGen::output_type tcl
    set ::sth::hlapiGen::default_value 1
    set ::sth::hlapiGen::default_yaml  0

    foreach arg "config_file output test_config test_control online test_run test_result pkt_capture device_info traffic scaling_test interface_config output_type savexml default_value default_yaml" {
        if {[lsearch $args "-$arg"] > -1} {
            set ::sth::hlapiGen::$arg [lindex $args [expr {[lsearch $args "-$arg"] + 1}]]
        }
    }

    set config_file $::sth::hlapiGen::config_file
    if {[info exists ::sth::hlapiGen::output]} {
        set output $::sth::hlapiGen::output
    }

    if {![info exist config_file] } {
        puts_msg "wrong arguments: $args, one xml file input is required."
        return
    }

    ##################################################################################
    ##load the xml file and get the
    ##################################################################################
    if {[regexp ".xml$" $config_file]} {
        set pattern ".xml$"
        stc::perform LoadFromXmlCommand -FileName $config_file
    } elseif {[regexp ".tcc$" $config_file]} {
        set pattern ".tcc$"
        stc::perform LoadFromDatabaseCommand -DatabaseConnectionString $config_file
    } else {
        puts "$config_file: its file format should be .xml or .tcc"
        return
    }

    ##################################################################################
    ##generate the script for each device and puts to the file
    ##################################################################################
    if { $::sth::hlapiGen::output_type eq "python" } {
        set gen_script_name "[regsub $pattern $config_file ""].py"
    } elseif { $::sth::hlapiGen::output_type eq "perl" ||
        $::sth::hlapiGen::output_type eq "jt_perl" } {
        set gen_script_name "[regsub $pattern $config_file ""].pl"
    } elseif { $::sth::hlapiGen::output_type eq "robot" } {
        set gen_script_name "[regsub $pattern $config_file ""].robot"
    } else {
        set gen_script_name "[regsub $pattern $config_file ""].tcl"
    }

    if {[info exist output]} {
        if {[file isdirectory $output]} {
        set gen_script_name [file join $output [file tail $gen_script_name]]
        } else {
            set gen_script_name $output
        }
    }
    ::sth::hlapiGen::do_hlapi_gen $gen_script_name
}

proc ::sth::hlapiGen::do_hlapi_gen {gen_script_name} {
    if {[catch {do_hlapi_gen_incatch $gen_script_name} retMsg]} {
        regsub "invoked.*" $::errorInfo "" myerror
        puts_msg "\nFailed to generate script: \n$myerror"
        return ""
    }
    return $retMsg
}

proc ::sth::hlapiGen::do_hlapi_gen_incatch {gen_script_name} {
    #init the device_ret, port_ret, protocol_to_devices, and protocol_to_devices
    array unset ::sth::hlapiGen::device_ret
    array set ::sth::hlapiGen::device_ret {}

    array unset ::sth::hlapiGen::port_ret
    array set ::sth::hlapiGen::port_ret {}
    array unset ::sth::hlapiGen::handle_to_port
    array set ::sth::hlapiGen::handle_to_port {}
    array unset ::sth::hlapiGen::protocol_to_devices
    array set ::sth::hlapiGen::protocol_to_devices {}

    array unset ::sth::hlapiGen::protocol_to_ports
    array set ::sth::hlapiGen::protocol_to_ports {}

    array unset ::sth::hlapiGen::devicelist_obj
    array set ::sth::hlapiGen::devicelist_obj {}

    array unset ::sth::hlapiGen::scaling_tmp
    array set ::sth::hlapiGen::scaling_tmp {}

    array unset ::sth::hlapiGen::traffic_ret
    array set ::sth::hlapiGen::traffic_ret {}

    array unset ::sth::hlapiGen::dhcpv4servertconfigured
    array set ::sth::hlapiGen::dhcpv4servertconfigured {}
    array unset ::sth::hlapiGen::dhcpv6servertconfigured
    array set ::sth::hlapiGen::dhcpv6servertconfigured {}
    array unset ::sth::hlapiGen::dhcpv4portconfigured
    array unset ::sth::hlapiGen::dhcpv6portconfigured
    array set ::sth::hlapiGen::dhcpv4portconfigured {}
    array set ::sth::hlapiGen::dhcpv6portconfigured {}
    array unset ::sth::hlapiGen::lagportconfigured
    array set ::sth::hlapiGen::lagportconfigured {}
    array unset ::sth::hlapiGen::v_linkmap
    array set ::sth::hlapiGen::v_linkmap {}
    ##add for L3_forwarding link
    set ::sth::hlapiGen::links_gen ""
    #To map profile and http
    array unset ::sth::hlapiGen::profile_to_http
    array set ::sth::hlapiGen::profile_to_http {}
    #To map devices to httphandle
    array unset ::sth::hlapiGen::devices_to_httphandle
    array set ::sth::hlapiGen::devices_to_httphandle {}
    array unset ::sth::hlapiGen::multicast_src_array
    array set ::sth::hlapiGen::multicast_src_array {}
    set ::sth::hlapiGen::md_level_step ""
    set ::sth::hlapiGen::eoam_router_without_control ""
    set ::sth::hlapiGen::variable_name_list ""
    set ::sth::hlapiGen::Parse "True"
    #Checking output_type: TCL, PERL, JT_PERL, PYTHON or other plugin like TEST CASE
    if {[::sth::hlapiGen::notSupport $::sth::hlapiGen::output_type $gen_script_name]} {
        return ""
    }
    set ::sth::hlapiGen::script_file_name $gen_script_name
    
    set ::sth::hlapiGen::testCaseStart 0
    set ports [stc::get project1 -children-port]
    if {[llength $ports] == 0} {
        puts_msg "\n\n\WARNING - You must reserve at least 1 port in order to use this wizard.\n"
        return ""
    }

    #preprocess offline port, add different port num in location
    set portIndex 1
    foreach offlineport $ports {
        set location [stc::get $offlineport -Location]
        if {[regexp -nocase "Offline" $location]} {
            stc::config $offlineport -Location "//(Offline)/1/$portIndex"
            incr portIndex
        }
    }

    set devices [stc::get project1 -children-EmulatedDevice]

    set strblklist ""
    foreach port $ports {
        set strblk [stc::get $port -children-streamblock]
        if {$strblk != ""} {
            set strblklist [concat $strblklist $strblk]
        }
    }

    ::sth::sthCore::InitTableFromTCLList $sth::hlapiGen::hlapiGenTable

    puts_to_file "package require SpirentHltApi \n"

    if {$::sth::hlapiGen::test_config} {
        hlapi_gen_testConfig $gen_script_name
    }
    if {$::sth::hlapiGen::test_control} {
        hlapi_gen_testControl
    }

    ###need to reserve port
    set stepIndex 0
    puts_msg "step[incr stepIndex]: generate the reserve ports command"
    hlapi_gen_reservePorts $ports
    if {$::sth::hlapiGen::device_info} {
        hlapi_gen_deviceInfo $ports
    }

    if {$::sth::hlapiGen::interface_config} {
        puts_msg "step[incr stepIndex]: generate the config interface command"
        hlapi_gen_interface $ports
    }
 
    puts_msg "step[incr stepIndex]: generate the create and config devices command"
    hlapi_gen_device $devices $ports

    #SIP can create some streamblock, so need to remove this from the strblklist
    #code for checking the ctraffic config mode
    set accessConcGen [stc::get project1 -children-AccessConcentratorGenParams]
    if {$accessConcGen ne ""} {
       set traffic_config_mode [stc::get $accessConcGen -TrafficConfigMode]
    } else {
         set traffic_config_mode ""
    }
    if {$traffic_config_mode ne "AUTO" } {
    set new_strblklist ""
    foreach strblk $strblklist {
        set gen_by [stc::get $strblk -ControlledBy]
        if {![regexp -nocase "sip" $gen_by]} {
            set new_strblklist [concat $new_strblklist $strblk]
        }
    }
    set strblklist $new_strblklist
    if {$::sth::hlapiGen::traffic && $strblklist != ""} {
        #check if the streamblock is needed to creat
        set strblklist [update_streamblock_list $strblklist]
        if {$strblklist != ""} {
            puts_msg "step[incr stepIndex]: generate the create streams command"
            hlapi_gen_stream $strblklist
        }
    }
   }
    array unset rfcobjarry
    array set rfcobjarry {}
    set rfcobjlist ""
    foreach rfcobj "Rfc3918Config Rfc2544BackToBackFramesConfig Rfc2544FrameLossConfig Rfc2544LatencyConfig Rfc2544ThroughputConfig" {
        set rfchdl [stc::get project1 -children-$rfcobj]
        if {$rfchdl ne ""} {
        set rfcHandle $rfchdl
        }
        set accessConcGen [stc::get project1 -children-AccessConcentratorGenParams]
        if {$accessConcGen ne ""} {
            set rfchdl [stc::get $accessConcGen -children-$rfcobj]
            if {$rfchdl ne ""} {
               set rfcHandle $rfchdl
            }
        }
        if {$rfchdl ne "" } {
            if {![regexp "^$" $rfchdl]} {
                set rfcobjarry([string tolower $rfcobj]) [concat $rfcobjlist $rfchdl]
                set rfcarrykey [string tolower $rfcobj]
               }

        }
 
    }
    hlapi_gen_benchmarking rfcobjarry $strblklist

    set myseq [hlapi_gen_sequencer $stepIndex]
    #save as xml
    if {$::sth::hlapiGen::savexml} {
        if {[regexp -nocase "\\.tcl" $gen_script_name]} {
            if {[regexp -nocase {\\} $gen_script_name]} {
                set templist [split $gen_script_name {\\}]
            } elseif {[regexp -nocase "/" $gen_script_name]} {
                set templist [split $gen_script_name /]
            } else {
                set templist $gen_script_name
            }
            set len [llength $templist]
            set xml_name [lindex $templist [incr len -1]]
            append xml_name ".xml"
            puts_to_file "stc::perform SaveAsXml -filename $xml_name"
        }
    }
    if {$myseq eq ""} {
        if {$::sth::hlapiGen::test_run} {
            puts_msg "step[incr stepIndex]: generate the start devices command"
            hlapi_gen_start_devices
            if {[info exists rfcHandle] && $rfcHandle ne ""} {
             set rfc5180en [::sth::sthCore::invoke stc::get $rfcHandle -children-Rfc5180Config]
            }
            if {[info exists rfcobjarry] && [info exists rfcarrykey] && [regexp -- "rfc2544" $rfcobjarry($rfcarrykey)]} {
               if {[info exists rfc5180en] && $rfc5180en eq ""} {
               set strblklist ""
             }
            }
            if {[llength $strblklist] != 0} {
                puts_msg "step[incr stepIndex]: generate the start streams command"
                hlapi_gen_start_streams $ports $strblklist
            }
        }

        if {$::sth::hlapiGen::test_result} {
            puts_msg "step[incr stepIndex]: generate the get device results command"
            hlapi_gen_device_results
            if {[info exists rfcobjarry] && [info exists rfcarrykey] && [regexp -- "rfc2544" $rfcobjarry($rfcarrykey)] } {
               if {[info exists rfc5180en] && $rfc5180en eq ""} {
               set strblklist ""
             }
            }
            if {[llength $strblklist] != 0} {
                puts_msg "step[incr stepIndex]: generate the get streams command"
                hlapi_gen_stream_results $ports $strblklist
            }
        }
    }
    #set packetCaptureFlag 0
    if {$::sth::hlapiGen::pkt_capture} {
        puts_msg "step[incr stepIndex]: generate the packet capture command"
        hlapi_gen_packet_capture $ports
    }

    puts_msg "step[incr stepIndex]: clean up session"
    hlapi_gen_cleanup_session $ports

    if {[info exists ::sth::hlapiGen::unSupported]} {
        foreach cls [lsort [array name ::sth::hlapiGen::unSupported]] {
            puts_msg "Not supported by Save as HLTAPI: $cls on \"$::sth::hlapiGen::unSupported($cls)\""
        }
        array unset ::sth::hlapiGen::unSupported
    }
    
    if {[info exists ::sth::hlapiGen::warnings]} {
        foreach warn [lsort [array name ::sth::hlapiGen::warnings]] {
            puts_msg "Warn: $warn $::sth::hlapiGen::warnings($warn)"
        }
        array unset ::sth::hlapiGen::warnings
    }

    set objects [concat $devices $ports]
    unset_data_model_attr $objects
    return $gen_script_name
}

proc ::sth::hlapiGen::hlapi_gen_reservePorts {ports} {

    set comments ""
    set cfg_str ""
    append comments "\n##############################################################\n"
    append comments "#connect to chassis and reserve port list\n"
    append comments "##############################################################\n"
    puts_to_file $comments

    array set chassis_port_map {}
    array set port_to_location {}
    set port_list ""
    foreach port_handle $ports {
        set lag_handle [stc::get $port_handle -children-lag]
        if {$lag_handle eq ""} {
            lappend port_list $port_handle
        } else {
            set ::sth::hlapiGen::port_ret($port_handle) "$port_handle"
            set ::sth::hlapiGen::handle_to_port($port_handle) $port_handle
        }
    }
    foreach port_handle $port_list {
        set port_location [stc::get $port_handle -Location]
        regsub {\/\/} $port_location "" port_location
        set chassis_ip [lindex [split $port_location "\/"] 0]
        set port [join [lrange [split $port_location "\/"] 1 2] "\/"]
        if {[info exists chassis_port_map($chassis_ip)]} {
            append chassis_port_map($chassis_ip) " $port"
        } else {
            set chassis_port_map($chassis_ip) $port
        }
        set port_to_location($port_location) $port_handle
    }
    set j 0
    append cfg_str "set i 0\n"
    set chassis_name [array names chassis_port_map]
    set chassis_ip_index [lrange $chassis_name 1 end]
    lappend  chassis_ip_index [lindex $chassis_name 0]
    foreach chassis  $chassis_ip_index {
        append cfg_str "set device $chassis\n"
        append cfg_str "set port_list \"$chassis_port_map($chassis)\"\n"
        if {$::sth::hlapiGen::online == 0} {
            set connect_cmd "set intStatus \[sth::connect -device \$device -port_list \$port_list -offline 1\]\n"
        } else {
            set connect_cmd "set intStatus \[sth::connect -device \$device -port_list \$port_list -break_locks 1 -offline 0\]\n"
        }
        append cfg_str "$connect_cmd\n"
        append cfg_str "set chassConnect \[keylget intStatus status\]\n"
        foreach port [set chassis_port_map($chassis)] {
            incr j
            set port_handle $port_to_location($chassis\/$port)
            set ::sth::hlapiGen::port_ret($port_handle) "\$port$j"
            set ::sth::hlapiGen::handle_to_port(\$port$j) $port_handle
        }
        append cfg_str "if \{\$chassConnect\} \{\n	foreach port \$port_list \{\n	incr i\n    set port\$i \[keylget intStatus port_handle.\$device.\$port\]\n	puts \"\\n reserved ports : \$intStatus\"\n	\}\n  \} else \{\n	set passFail FAIL\n	puts \"\\nFailed to retrieve port handle! Error message: \$intStatus\"\n\}\n"
        puts_to_file $cfg_str
        set cfg_str ""
        }

}
proc ::sth::hlapiGen::hlapi_gen_interface {ports} {
    set comments ""
    set cfg_str ""
    append comments "\n##############################################################\n"
    append comments "#interface config\n"
    append comments "##############################################################\n"
    puts_to_file $comments


    set mode "config"
    set i 0
    set hlt_ret "int_ret$i"
    set port_list ""
    foreach port_handle $ports {
        set lag_handle [stc::get $port_handle -children-lag]
        if {$lag_handle eq ""} {
            lappend port_list $port_handle
        }
    }
    set ports $port_list
    foreach port $ports {
        get_attr $port $port
        #handle port level info
        set hlt_ret "int_ret$i"
        hlapi_gen_interface_convert_func $port $mode $hlt_ret
        incr i
        #process raw device
        gen_status_info $hlt_ret "sth::interface_config"
        unset_data_model_attr $port
    }
}

proc ::sth::hlapiGen::hlapi_gen_device {devices ports} {
    variable device_ret
    variable devicelist_obj
    variable protocol_to_devices

    set comments ""
    set cfg_str ""
    append comments "\n##############################################################\n"
    append comments "#create device and config the protocol on it\n"
    append comments "##############################################################\n"
    puts_to_file $comments
    set i 0
    set enable_index 0
    #get the obj which will trigger the hltapi function
    if {[isRealismConfigured project1]} {
        set devices [concat $devices [stc::get project1 -children-realismoptions]]
    }
    if {[isVqaConfigured project1]} {
        set objects [concat $devices $ports [stc::get project1 -children-vqanalyzeroptions]]
    } else {
        set objects [concat $devices $ports]
    }
    array set hltapi_obj [get_objs $objects]
    set  mode create
    set first_time 1
    set device_created ""
    set class_list [array names hltapi_obj]
    create_switch_priority_list sth::hlapiGen:: hlapi_gen $class_list switch_priority_list
    #puts dhcp releated end of list
    set switch_priority_list_new ""
    foreach item $switch_priority_list {
        set class [lindex $item 1]
        if {[regexp -nocase "dhcp" $class]} {
            set item [list "300" $class]
        }
        lappend switch_priority_list_new $item
    }
    set switch_priority_list [lsort -integer -index 0 $switch_priority_list_new]
    foreach item $switch_priority_list {
        set class [lindex $item 1]
       #here need to check if the objects of this class can be created in one hltapi comamnd
        if {[regexp -nocase "dhcpv4portconfig" $class] || [regexp -nocase "dhcpv6portconfig" $class]|| [regexp -nocase "dhcpv4serverpoolconfig" $class]} {
            continue
        }
        array set object_status {}

        set hltapi_obj_cfg [get_hltapi_needed_objs $class $hltapi_obj($class) $device_created]
        if { ($hltapi_obj_cfg == "" && $class == "emulateddevice" ) || ( $hltapi_obj_cfg == "" && $class == "host" )  } {
            continue
        }
        if {$::sth::hlapiGen::scaling_test} {
            #when the device has already created, for the protocol to be configured on this device, no need to do scaling.
            set new_devices ""
            foreach device $devices {
                if {![info exists ::sth::hlapiGen::device_ret($device)]} {
                    set new_devices [concat $new_devices $device]
                }
            }
            set devices $new_devices
            set multi_dev_check_func $::sth::hlapiGen::hlapi_gen_multiDevCheckFunc($class)
            if {![regexp {_none_} $multi_dev_check_func]} {
                set hltapi_obj_cfg_old $hltapi_obj_cfg
                if {[regexp {vpn_site} $multi_dev_check_func]} {
                    set hltapi_obj_cfg [multi_dev_check_func_$multi_dev_check_func $class $devices]
                } else {
                    set hltapi_obj_cfg [get_obj_for_scaling $devices $class $multi_dev_check_func $hltapi_obj_cfg_old]
                }
            }
        }
        #need to store the map between the device handle in the configured file and the returnd value
        dev_to_cfg_ret $class $hltapi_obj_cfg $i object_status
        set j 0
        set cfg_convert_func $::sth::hlapiGen::hlapi_gen_cfgConvertFunc($class)
        set cfg_func "::sth::[set ::sth::hlapiGen::hlapi_gen_cfgFunc($class)]"
        #configure the mpls_l2vpn_pe or mpls_l3vpn_pe (VrfProviderLink)
        if {[regexp -nocase "VrfProviderLink" $class]} {
            hlapi_gen_$cfg_convert_func $class pe_router
            continue
        }
        if {[regexp -nocase "sipuaprotocolconfig" $class]} {
            set hltapi_obj_cfg [sort_sip_pri $hltapi_obj_cfg]
        }
        foreach obj $hltapi_obj_cfg {
            # add protocol_to_devices to check the device created by igmpv3 source filter
            if {[info exists ::sth::hlapiGen::protocol_to_devices($obj)] } {
                continue
            }
            if {[regexp "vqanalyzer" $obj]} {
                set port [stc::get $obj -parent]
                if {![isVqaConfigured $port]} {
                    continue
                }
            }
            variable hltapi_sript ""
            if {[regexp "vpnsiteinfovplsldp" $obj] || [regexp "vpnsiteinfovplsbgp" $obj] || [regexp "vpnsiteinforfc2547" $obj]} {
                set device [stc::get $obj -memberofvpnsite-sources]
            } elseif {[regexp "emulateddevice" $obj] || [regexp -nocase "^host" $obj] || [regexp -nocase "^vqanalyzeroptions" $obj] || [regexp -nocase "^realismoptions" $obj]} {
                set device $obj
            } else {
                set device [stc::get $obj -parent]
            }
            catch {set link [stc::get $device -containedlink-Targets]}
            if {[info exists link] && $link != ""} {
                set ::sth::hlapiGen::v_linkmap($link) $device
            }
            if {[regexp {project} [stc::get $device -parent]] && ![regexp {project} $obj]} {
                set device_name [stc::get $device -name]
            } else {
                set device_name [stc::get $obj -name]
            }
            ##add for L3_forwarding link
            catch {
                set L3ForwardingLinks [stc::get $device -children-l3forwardinglink]
                foreach L3ForwardingLink $L3ForwardingLinks {
                    if {$L3ForwardingLink != ""} {
                        lappend ::sth::hlapiGen::links_gen $L3ForwardingLink
                    }
                }
            }
            if {[lsearch $device_created $device] != -1} {
                if { $class == "emulateddevice" || $class == "host" } {
                    continue
                }
                if {![regexp -nocase bfdrouterconfig $obj] && ![regexp -nocase greif $obj]} {
                    puts_to_file "#start to config protocol on the device: $device_name"
                }
                set hlt_ret device_cfg_ret$enable_index
                set mode enable
                set first_time 0
                incr enable_index
            } else {
                set comments "$device_name"
                if {$::sth::hlapiGen::scaling_test} {
                    if {[info exists devicelist_obj($obj)] && [llength $devicelist_obj($obj)] > 1} {
                        set device_end [lindex $devicelist_obj($obj) [expr [llength $devicelist_obj($obj)] - 1]]
                        set device_end_name [stc::get $device_end -name]
                        set comments "from $device_name to $device_end_name"
                    }
                }
                puts_to_file "#start to create the device: $comments"
                set first_time 1
                set mode create
                set hlt_ret device_ret$i
                incr i
                set device_created [concat $device_created $device]
            }
            #update the created device handle for the scaling test
            if {[info exists devicelist_obj($obj)]} {
                set index 0
                foreach devicehdl $devicelist_obj($obj) {
                    if {![info exists device_ret($devicehdl)]} {
                        set device_ret($devicehdl) "$hlt_ret $index"
                    }
                    if {[lsearch $device_created $devicehdl] < 0} {
                        set device_created [concat $device_created $devicehdl]
                    }
                    #update the protocol_to_device for scaling test
                    if {[lsearch $protocol_to_devices($class) $devicehdl] < 0} {
                        lappend protocol_to_devices($class) "$devicehdl"
                    }
                    incr index
                }
            }
            #get the cfg convert function which will be used,if it is basic will call the basic function, else
            #will use the function for the specific config function.
            set cfg_convert_func $::sth::hlapiGen::hlapi_gen_cfgConvertFunc($class)
            set cfg_func "::sth::[set ::sth::hlapiGen::hlapi_gen_cfgFunc($class)]"
            if {![info exists cfg_args($obj)]} {
                 set cfg_args($obj) ""
            }
            hlapi_gen_device_$cfg_convert_func $device $class $mode $hlt_ret $cfg_args($obj) $first_time
            #clear the stcobj and stcattr data after configuring the protocols
            unset_table_obj_attr $class
        }

        if {[regexp ancpaccessnodeconfig $class]} {
            #handle the emulation_ancp_subscriber_lines_config, since in this funtion may use the ancp router created in the
            #ancp_config function, so process it here.
            if {[info exists hltapi_obj_cfg_old]} {
                hlapi_gen_device_subscribe_line $hltapi_obj_cfg_old
            } else {
                hlapi_gen_device_subscribe_line $hltapi_obj_cfg
            }
        }
    }
}

proc ::sth::hlapiGen::hlapi_gen_stream {strblklist} {
    set comments ""
    set cfg_str ""
    append comments "\n##############################################################\n"
    append comments "#create traffic\n"
    append comments "##############################################################\n"
    puts_to_file $comments
    hlapi_gen_streamblock $strblklist
}
proc ::sth::hlapiGen::hlapi_gen_benchmarking {rfcobjarry strblklist} {
    set i 0
    upvar $rfcobjarry myrfcobjarry
    upvar strblklist mystrblklist
    foreach class [array names myrfcobjarry] {
        set rfcobjlist $myrfcobjarry($class)
        array set ::sth::hlapiGen::protocol_to_devices "$class [lindex $rfcobjlist 0]"
        if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
            foreach rfcobj $rfcobjlist {
                if {[regexp -nocase "rfc3918" $rfcobj]} {
                    set mc [stc::get $rfcobj -multicaststreamblockbinding-targets]
                    set rfc3918_gens [stc::get $rfcobj -rfc3918generated-targets]

                    foreach rfc3918_gen $rfc3918_gens {
                        if {[regexp -nocase "streamblock" $rfc3918_gen]} {
                            set mc [concat $mc $rfc3918_gen]
                        }
                    }
                    if {[llength $mc] == 0} {
                        continue
                    }
                }
                get_attr $rfcobj $rfcobj
                set cfg_convert_func [set sth::hlapiGen::hlapi_gen_cfgConvertFunc($class)]
                set mode "create"
                set hlt_ret "rfc_cfg$i"
                hlapi_gen_device_$cfg_convert_func $rfcobj $class $mode $hlt_ret $mystrblklist
                incr i
            }
        }
        unset_table_obj_attr $class
    }
}

proc ::sth::hlapiGen::hlapi_gen_start_devices {} {
    set comments ""
    set cfg_str ""
    ##add for L3_forwarding link
    catch {
        foreach link $::sth::hlapiGen::links_gen {
            set srcDevice [stc::get $link -containedlink-Sources]
            set dstDevice [stc::get $link -linkdstdevice-Targets]

            ##here need check srcDevice whether need create links any more,
            if {[regexp -nocase $dstDevice [stc::get $srcDevice -AffiliatedRouter-targets]]} {
                continue
            }

            set srcdevicekey "handle"
            if {[stc::get $srcDevice -children-dhcpv6serverconfig] ne ""} {
                set srcdevicekey "handle.dhcpv6_handle"
            }
            if {[stc::get $srcDevice -children-dhcpv4serverconfig] ne ""} {
                set srcdevicekey "handle.dhcp_handle"
            }
            if {[stc::get $srcDevice -children-dhcpv6blockconfig] ne ""} {
                set srcdevicekey "dhcpv6_handle"
            }
            if {[stc::get $srcDevice -children-dhcpv6blockconfig] ne ""} {
                set srcdevicekey "dhcpv6_handle"
            }

            set dstdevicekey "handle"
            if {[stc::get $dstDevice -children-dhcpv6serverconfig] ne ""} {
                set dstdevicekey "handle.dhcpv6_handle"
            }
            if {[stc::get $dstDevice -children-dhcpv4serverconfig] ne ""} {
                set dstdevicekey "handle.dhcp_handle"
            }
            if {[stc::get $dstDevice -children-dhcpv6blockconfig] ne ""} {
                set dstdevicekey "dhcpv6_handle"
            }
            if {[stc::get $dstDevice -children-dhcpv6blockconfig] ne ""} {
                set dstdevicekey "dhcpv6_handle"
            }
            if {[info exists ::sth::hlapiGen::device_ret($srcDevice)] && ([info exists ::sth::hlapiGen::device_ret($dstDevice)])} {
                puts_to_file "set srcDevice \[lindex \[keylget [lindex $::sth::hlapiGen::device_ret($srcDevice) 0] $srcdevicekey\] 0\]\n"
                puts_to_file "set dstDevice \[lindex \[keylget [lindex $::sth::hlapiGen::device_ret($dstDevice) 0] $dstdevicekey\] 0\]\n"
                puts_to_file "set [lindex $::sth::hlapiGen::device_ret($srcDevice) 0]_link_[lindex $::sth::hlapiGen::device_ret($dstDevice) 0] \[::sth::link_config\\\n -link_src \$srcDevice\\\n -link_dst \$dstDevice\\\n -link_type \"L3_Forwarding_Link\"\\\n\]"
                gen_status_info "[lindex $::sth::hlapiGen::device_ret($srcDevice) 0]_link_[lindex $::sth::hlapiGen::device_ret($dstDevice) 0]" "sth::link_config"
            }
        }
    }

    append comments "#config part is finished\n"
    append comments "\n##############################################################\n"
    append comments "#start devices\n"
    append comments "##############################################################\n"
    puts_to_file $comments

    set name_space "::sth::hlapiGen::"
    set cmd_name "hlapi_gen"
    set i 0
    #here need to sort the protcol to start. since sometimes for the multiple protcol it has the dependency
    set class_list [array names ::sth::hlapiGen::protocol_to_devices]
    create_switch_priority_list sth::hlapiGen:: hlapi_gen $class_list switch_priority_list
    set test_rfc2544_control_first_time 1
    foreach item $switch_priority_list {
        set class [lindex $item 1]
        set ctrl_func_config ""
        set comments ""
        set protocol_device_list_new ""
        incr i
        if {[regexp "ldprouterconfig_pe" $class]} {
            set class "ldprouterconfig"
        }
        set ctrl_convert_func [set ::sth::hlapiGen::hlapi_gen_ctrlConvertFunc($class)]
        if {![regexp {_none_} $ctrl_convert_func]} {
            if {[regexp "rfc" $ctrl_convert_func]} {
                set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
                if {[regexp "test_rfc2544_control" $ctrl_func]} {
                    if {!$test_rfc2544_control_first_time} {
                        continue
                    }
                    set test_rfc2544_control_first_time 0
                }
            }
            ::sth::hlapiGen::ctrl_convert_$ctrl_convert_func $i $class
        }
    }
}



proc ::sth::hlapiGen::hlapi_gen_device_results {} {
    set comments ""
    set cfg_str ""
    append comments "\n##############################################################\n"
    append comments "#start to get the device results\n"
    append comments "##############################################################\n"
    puts_to_file $comments

    set name_space "::sth::hlapiGen::"
    set cmd_name "hlapi_gen"
    set bgp_devices_handle_list ""
    set i 0
    set class_list [array names ::sth::hlapiGen::protocol_to_devices]
    create_switch_priority_list sth::hlapiGen:: hlapi_gen $class_list switch_priority_list
    foreach item $switch_priority_list {
        set class [lindex $item 1]
        set result_func_config ""
        set comments ""
        incr i
        if {[regexp "ldprouterconfig_pe" $class]} {
            set class "ldprouterconfig"
        }
        set result_convert_func	[set ::sth::hlapiGen::hlapi_gen_resultConvertFunc($class)]

        if {![regexp {_none_} $result_convert_func]} {
            ::sth::hlapiGen::result_convert_$result_convert_func $i $class
            set res_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
        }
    }
}

proc ::sth::hlapiGen::hlapi_gen_packet_capture {ports} {
    variable port_ret

    set comments ""
    append comments "\n##############################################################\n"
    append comments "#packet capture\n"
    append comments "##############################################################\n"
    puts_to_file $comments

    foreach port $ports {
        #packet_config_buffers
        set comments ""
        append comments "#packet_config_buffers\n"
        puts_to_file $comments
        set hltapi_string ""
        set capturehnd [stc::get $port -children-Capture]
        set buffer_action [stc::get $capturehnd -BufferMode]
        if {$buffer_action eq "WRAP"} {
            set buffer_action wrap
        } else {
            set buffer_action stop
            }
        append hltapi_string "set control_sta \[sth::packet_config_buffers\\\n"
        append hltapi_string "			-port_handle		$port_ret($port)\\\n"
        append hltapi_string "			-action		$buffer_action]\n"
        #append hltapi_string "puts \"$port packet_config_buffers result is:\$control_sta\""
        puts_to_file  $hltapi_string
        gen_status_info control_sta "sth::packet_config_buffers"

        #packet_config_triggers
        set comments ""
        append comments "#packet_config_triggers\n"
        puts_to_file $comments

        set PacketErrorMap(signature)  "SigPresent"
        set PacketErrorMap(oversize)   "Oversized"
        set PacketErrorMap(jumbo)      "Jumbo"
        set PacketErrorMap(undersize)  "Undersized"
        set PacketErrorMap(invalidfcs) "FcsError"
        set PacketErrorMap(ipCheckSum)   "Ipv4CheckSumError"
        set PacketErrorMap(oos)        "SigSeqNumError"
        set PacketErrorMap(prbs)       "PrbsError"

        foreach stop_start "Start Stop" {
            set captureconhnd [stc::get $capturehnd "-children-CaptureFilter[set stop_start]Event"]

            foreach {trigger value} [array get PacketErrorMap] {
                if {[stc::get $captureconhnd "-$value"] eq "INCLUDE"} {
                    set hltapi_string ""
                    append hltapi_string "set control_sta \[sth::packet_config_triggers\\\n"
                    append hltapi_string "			-port_handle		$port_ret($port)\\\n"
                    append hltapi_string "			-exec		[string tolower $stop_start]\\\n"
                    append hltapi_string "			-mode		add\\\n"
                    append hltapi_string "			-action		event\\\n"
                    append hltapi_string "			-trigger		$trigger]\n"
                    #append hltapi_string "puts \"$port packet_config_triggers result is:\$control_sta\""
                    puts_to_file  $hltapi_string
                    gen_status_info control_sta "sth::packet_config_triggers"
                }
            }

            #handle length here
            if {[stc::get $captureconhnd -FrameLenMatch] eq "INCLUDE"} {
                set hltapi_string ""
                append hltapi_string "set control_sta \[sth::packet_config_triggers\\\n"
                append hltapi_string "			-port_handle		$port_ret($port)\\\n"
                append hltapi_string "			-exec		[string tolower $stop_start]\\\n"
                append hltapi_string "			-mode		add\\\n"
                append hltapi_string "			-action		event\\\n"
                append hltapi_string "			-trigger		\"length [stc::get $captureconhnd -FrameLength]\"]\n"
                #append hltapi_string "puts \"$port packet_config_triggers result is:\$control_sta\""
                puts_to_file  $hltapi_string
                gen_status_info control_sta "sth::packet_config_triggers"
            }
        }

        #packet_config_filter
        set comments ""
        append comments "#packet_config_filter\n"
        puts_to_file $comments

        set captureconhnd [stc::get $capturehnd "-children-CaptureFilter"]
        foreach {filter value} [array get PacketErrorMap] {
            if {[stc::get $captureconhnd "-$value"] eq "INCLUDE"} {
                set hltapi_string ""
                append hltapi_string "set control_sta \[sth::packet_config_filter\\\n"
                append hltapi_string "			-port_handle		$port_ret($port)\\\n"
                append hltapi_string "			-mode		add\\\n"
                append hltapi_string "			-filter		$filter]\n"
                #append hltapi_string "puts \"$port packet_config_filter result is:\$control_sta\""
                puts_to_file  $hltapi_string
                gen_status_info control_sta "sth::packet_config_filter"
            }
        }
        #handle length here
        if {[stc::get $captureconhnd -FrameLenMatch] eq "INCLUDE"} {
            set hltapi_string ""
            append hltapi_string "set control_sta \[sth::packet_config_filter\\\n"
            append hltapi_string "			-port_handle		$port_ret($port)\\\n"
            append hltapi_string "			-mode		add\\\n"
            append hltapi_string "			-filter		\"length [stc::get $captureconhnd -FrameLength]\"]\n"
            #append hltapi_string "puts \"$port packet_config_filter result is:\$control_sta\""
            puts_to_file  $hltapi_string
            gen_status_info control_sta "sth::packet_config_filter"
        }

        if {0} {
        #handle pattern here, since it's too complex to add support filter:pattern
        #btw, packet capture rarely used by customers
        set CapAnaFilterList [stc::get $captureconhnd -children-CaptureAnalyzerFilter]
        if {$CapAnaFilterList ne ""} {
            set patternList ""
            set operator ""
            foreach CapAnaFilter $CapAnaFilterList {
                set pattern ""
                append patternList " $operator "
                append pattern "-pattern_name [stc::get $CapAnaFilter -FilterDescription] "
                append pattern "-frameconfig [stc::get $CapAnaFilter -FrameConfig] "
                puts "#[stc::get $CapAnaFilter -FrameConfig]#"
                append pattern "-value [stc::get $CapAnaFilter -ValueToBeMatched] "
                append patternList "\{ $pattern \}"
                set operator [stc::get $CapAnaFilter -RelationToNextFilter]
            }
            set hltapi_string ""

            append hltapi_string "set control_sta \[sth::packet_config_filter\\\n"
            append hltapi_string "			-port_handle		$port_ret($port)\\\n"
            append hltapi_string "			-mode		add\\\n"
            append hltapi_string "			-filter		\{pattern \{ $patternList \}\}]\n"
            #append hltapi_string "puts \"$port packet_config_filter result is:\$control_sta\""
            puts_to_file  $hltapi_string
            gen_status_info control_sta "sth::packet_config_filter"
        }
        }

    }


    #packet_control: start the packet capture
    set comments ""
    append comments "#packet capture start on each port\n"
    puts_to_file $comments
    set hltapi_string ""
    append hltapi_string "set control_sta \[sth::packet_control\\\n"
    append hltapi_string "			-port_handle		all\\\n"
    append hltapi_string "			-action		start]\n"
    #append hltapi_string "puts \"packet_control:start|all result is:\$control_sta\""
    puts_to_file  $hltapi_string
    gen_status_info control_sta "sth::packet_control"

    foreach port $ports {
        #packet_info
        set comments ""
        append comments "#packet capture info on each port after start\n"
        puts_to_file $comments
        set hltapi_string ""
        append hltapi_string "set control_sta \[sth::packet_info\\\n"
        append hltapi_string "			-port_handle		$port_ret($port)\\\n"
        append hltapi_string "			-action		status]\n"
        #append hltapi_string "puts \"$port packet_info result is:\$control_sta\""
        puts_to_file  $hltapi_string
        gen_status_info control_sta "sth::packet_info"
        set packet_info_hltapi $hltapi_string

        #packet_stats
        set comments ""
        append comments "#packet capture stats on each port\n"
        puts_to_file $comments
        #set script_name [regsub {\..*$} $::sth::hlapiGen::script_file_name ""]
        set pcapfilename ""
        set location [stc::get $port -Location]
        regsub -all // $location "" location
        regsub -all / $location _ location
        append pcapfilename  "$location" ".pcap"

        set hltapi_string ""
        append hltapi_string "set control_sta \[sth::packet_stats\\\n"
        append hltapi_string "			-port_handle		$port_ret($port)\\\n"
        append hltapi_string "			-stop		1\\\n"
        append hltapi_string "			-format		pcap\\\n"
        append hltapi_string "			-filename		$pcapfilename\\\n"
        append hltapi_string "			-action		filtered]\n"
        #append hltapi_string "puts \"$port packet_stats result is:\$control_sta\""
        puts_to_file  $hltapi_string
        gen_status_info control_sta "sth::packet_stats"
    }

    #packet_control: stop the packet capture
    set comments ""
    append comments "#packet capture stop on each port\n"
    puts_to_file $comments
    set hltapi_string ""
    append hltapi_string "set control_sta \[sth::packet_control\\\n"
    append hltapi_string "			-port_handle		all\\\n"
    append hltapi_string "			-action		stop]\n"
    #append hltapi_string "puts \"packet_control:stop|all result is:\$control_sta\""
    puts_to_file  $hltapi_string
    gen_status_info control_sta "sth::packet_control"

}

proc ::sth::hlapiGen::hlapi_gen_cleanup_session {ports} {
    variable port_ret
    set comments ""
    append comments "\n##############################################################\n"
    append comments "#clean up the session, release the ports reserved and cleanup the dbfile\n"
    append comments "##############################################################\n"
    puts_to_file $comments
    set port_handle_list ""
    foreach port_handle $ports {
        set lag_handle [stc::get $port_handle -children-lag]
        if { $lag_handle eq  "" } {
            lappend port_handle_list $port_handle
        }
    }
    if { $port_handle_list ne  "" } {
        set ports $port_handle_list
    }
    append cleanup_hltapi_string "set cleanup_sta \[sth::cleanup_session\\\n"
    foreach port $ports {
        append ports_new "$port_ret($port) "
    }
    append cleanup_hltapi_string "			-port_handle		$ports_new\\\n"
    append cleanup_hltapi_string "			-clean_dbfile		1]\n"
    puts_to_file  $cleanup_hltapi_string
    gen_status_info cleanup_sta "sth::cleanup_session"
    puts_to_file "\nputs \"**************Finish***************\""
}

proc ::sth::hlapiGen::hlapi_gen_deviceInfo {ports} {
    variable port_ret
    set comments ""
    append comments "\n##############################################################\n"
    append comments "#get the device info\n"
    append comments "##############################################################\n"
    puts_to_file $comments
    set port_list ""
    foreach port_handle $ports {
        set lag_handle [stc::get $port_handle -children-lag]
        if {$lag_handle eq ""} {
            lappend port_list $port_handle
        }
    }
    set ports $port_list
    append device_info_hltapi_string "set device_info \[sth::device_info\\\n"
    foreach port $ports {
        append ports_new "$port_ret($port) "
    }
    append device_info_hltapi_string "			-ports\\\n"
    append device_info_hltapi_string "			-port_handle		$ports_new\\\n"
    append device_info_hltapi_string "			-fspec_version]\n"
    puts_to_file  $device_info_hltapi_string
    gen_status_info device_info "sth::device_info"
}

proc ::sth::hlapiGen::hlapi_gen_testConfig {script_name} {
    set comments ""
    append comments "\n##############################################################\n"
    append comments "#config the parameters for the logging\n"
    append comments "##############################################################\n"
    puts_to_file $comments

    #remove the path of the script_name
    #set script_dir [file dirname $script_name]
    set script_name [file tail $script_name]
    set script_name_new [regsub {\..*$} $script_name ""]
    append test_config_hltapi_str "set test_sta \[sth::test_config\\\n"
    append test_config_hltapi_str "			-log			1\\\n"
    append test_config_hltapi_str "			-logfile		$script_name_new\_logfile\\\n"
    append test_config_hltapi_str "			-vendorlogfile		$script_name_new\_stcExport\\\n"
    append test_config_hltapi_str "			-vendorlog		1\\\n"
    append test_config_hltapi_str "			-hltlog			1\\\n"
    append test_config_hltapi_str "			-hltlogfile		$script_name_new\_hltExport\\\n"
    append test_config_hltapi_str "			-hlt2stcmappingfile	$script_name_new\_hlt2StcMapping\\\n"
    append test_config_hltapi_str "			-hlt2stcmapping		1\\\n"
    append test_config_hltapi_str "			-log_level		7]\n"
    puts_to_file $test_config_hltapi_str
    gen_status_info test_sta "sth::test_config"
}

proc ::sth::hlapiGen::hlapi_gen_testControl {} {
    set comments ""
    append comments "\n##############################################################\n"
    append comments "#config the parameters for optimization and parsing\n"
    append comments "##############################################################\n"
    puts_to_file $comments

    append test_ctrl_str "set test_ctrl_sta \[sth::test_control\\\n"
    append test_ctrl_str "		-action		enable]\n"
    puts_to_file $test_ctrl_str
    gen_status_info test_ctrl_sta "sth::test_control"
}

proc ::sth::hlapiGen::notSupport {type gen_script_name} {
    variable v_plugins
    upvar gen_script_name local_script_name
    switch -- [string tolower $type] {
        tcl {
        }
        perl {
        }
        python {
        }
        jt_perl {
        }
        robot {
        }
        default {
            set version [package present SpirentHltApi]
            if {[regexp -nocase $type $v_plugins match] } {
                if {[isSupport_$match $version]} {
                    set mysuffix [getInfo_$match suffix]
                    regsub ".tcl" $gen_script_name $mysuffix local_script_name
                } else {
                    puts_msg "HLTAPI Ver. $version cannot work with output type: \"$type\", please check the version of HLTAPI or $match plugin\n"
                    return 1
                }
            } else {
                set upper_plugin [regsub "" [string toupper $v_plugins] " | "]
                puts_msg "Output Type: Unknown type\[$type\], It should be one of TCL | PERL | PYTHON | JT_PERL | ROBOT | $upper_plugin.\n"
                return 1
            }
        }
    }

    if {[file exists $local_script_name]} {
        if {[file isfile $local_script_name]} {
            puts_msg "\n$local_script_name to save is an existing file, will be overwritten."
            file delete -force $local_script_name
        } elseif {[file isdirectory $local_script_name]} {
            puts_msg "\n$local_script_name to save cannot be an existing directory"
            return 1
        } else {
            puts_msg "Cannot go to here"
            return 1
        }
    }

    puts_msg "\nGenerating to $local_script_name..."
    return 0
}


proc ::sth::hlapiGen::loadPluginFile {basepath} {
    variable v_plugins
    set localErr ""
    if {[catch {
        set hlapiGen_files [glob -nocomplain $basepath/hlapiGen*]
        if {$hlapiGen_files ne ""} {
            foreach eachfile $hlapiGen_files {
                if {[regexp -nocase {hlapiGen(\w*)Function} $eachfile match sub]
                        && $sub ne ""
                        && ![regexp -nocase $sub "perl python robot"]} {
                    if {[catch {source [file join $basepath $eachfile]} e  ]} {
                        append localErr "Loading Spirent HLTApi hlapiGen \"$sub\" plugin files \"$eachfile\" . ($e).\n"
                    } else {
                        set err [loadPluginFiles_$sub $basepath]
                        if {$err eq ""} {
                            lappend v_plugins $sub
                        } else {
                            append localErr $err
                        }
                    }
                }
            }
        }
    } catcherr]} {
        append localErr $catcherr
    }

    return $localErr
}
