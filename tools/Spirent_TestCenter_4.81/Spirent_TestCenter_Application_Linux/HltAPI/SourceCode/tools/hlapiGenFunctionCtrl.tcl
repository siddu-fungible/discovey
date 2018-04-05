namespace eval ::sth::hlapiGen:: {

}

#***********************************************************************************************************->#
#control convert part function
#***********************************************************************************************************->#
#used for the control function which has the two options "-port_handle and -mode"
#input: i       => the index of the hltapi control fucntion in this script file.
#       class   => the class name, it will be used to know which hltapi control function will be called in the
#                   script file
#output: output the hltapi protocol control function to the file.
proc ::sth::hlapiGen::ctrl_convert_port_list {i class} {

    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    
    #handle the port_handle
    set protocol_port_list_new ""
    foreach protocol_port $protocol_port_list {
        append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    set ctrl_func_config [ctrl_convert_port_common ctrl_ret$i $ctrl_func $class $protocol_port_list_new]
    puts_to_file $ctrl_func_config
    gen_status_info ctrl_ret$i sth::$ctrl_func	
}

proc ::sth::hlapiGen::ctrl_convert_port {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    #handle the port_handle
    set protocol_port_list_new ""
    foreach protocol_port $protocol_port_list {
        #append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
        set ctrl_func_config [ctrl_convert_port_common ctrl_ret$j $ctrl_func $class $::sth::hlapiGen::port_ret($protocol_port)]
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$j sth::$ctrl_func	
        incr j
    }
}

proc ::sth::hlapiGen::ctrl_convert_port_common {ctrl_ret ctrl_func class handlelist} {
    
    append ctrl_func_config "set $ctrl_ret \[sth::$ctrl_func    \\\n"
    append ctrl_func_config "                     -port_handle        \"$handlelist\"\\\n"
    
    #handle the mode
    set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name $ctrl_func
    if {[info exists $name_space$cmd_name\_type(mode)]} {
        set value_type [set $name_space$cmd_name\_type(mode)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append ctrl_func_config "                     -mode        $value\\\n"
    }
    
    if {[info exists $name_space$cmd_name\_type(action)]} {
        set value_type [set $name_space$cmd_name\_type(action)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append ctrl_func_config "                     -action        $value\\\n"
    }
    
    append ctrl_func_config "\]\n"
}

#---------------------------------------------------------------------------------------------------------------#
#used for the control function which has the two options "-handle and -mode", the handle is the device handle
#input: i       => the index of the hltapi control fucntion in this script file.
#       class   => the class name, it will be used to know which hltapi control function will be called in the
#                   script file
#output: output the hltapi protocol control function to the file.

proc ::sth::hlapiGen::ctrl_convert_handle_list {i class} {
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    
    set protocol_device_list  $::sth::hlapiGen::protocol_to_devices($class)
    if {$::sth::hlapiGen::scaling_test} {
        #update the device list for scaling test
        set ctrl_func_config [get_device_created_scaling $protocol_device_list device_list handle]
    } else {
        set ctrl_func_config [get_device_created $protocol_device_list device_list handle]
    }
    puts_to_file $ctrl_func_config
    set ctrl_func_config [ctrl_convert_handle_common ctrl_ret$i $ctrl_func $class device_list]
    puts_to_file $ctrl_func_config
    gen_status_info ctrl_ret$i sth::$ctrl_func	
}

proc ::sth::hlapiGen::ctrl_convert_handle {i class} {
    
    upvar i j
    variable eoam_router_without_control
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_device_list  $::sth::hlapiGen::protocol_to_devices($class)
    if {$::sth::hlapiGen::scaling_test} {
        #update the device list for scaling test
        puts_to_file [get_device_created_scaling $protocol_device_list device_list_scaling handle]
        set ctrl_func_config "foreach device \$device_list_scaling \{\n"
        append ctrl_func_config [ctrl_convert_handle_common ctrl_ret$i $ctrl_func $class device]
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$i sth::$ctrl_func
        puts_to_file "\}\n"
    } else {
        foreach device_handle $protocol_device_list {
            if {[regexp -nocase $device_handle $eoam_router_without_control]} {
                continue    
            }
            puts_to_file [get_device_created $device_handle device_list handle]
            set ctrl_func_config [ctrl_convert_handle_common ctrl_ret$i $ctrl_func $class device_list]
            puts_to_file $ctrl_func_config
            gen_status_info ctrl_ret$i sth::$ctrl_func
            incr j
        }
    }
    
}

proc ::sth::hlapiGen::ctrl_convert_handle_common {ctrl_ret ctrl_func class handlelist} {
    
    
    append ctrl_func_config "set $ctrl_ret \[sth::$ctrl_func    \\\n"
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    append ctrl_func_config "                     -handle        \$$handlelist\\\n"
    
    #handle the mode
    set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name $ctrl_func
    if {[info exists $name_space$cmd_name\_type(mode)]} {
        set value_type [set $name_space$cmd_name\_type(mode)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append ctrl_func_config "                     -mode        $value\\\n"
    }
    if {[info exists $name_space$cmd_name\_type(action)]} {
        set value_type [set $name_space$cmd_name\_type(action)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append ctrl_func_config "                     -action        $value\\\n"
    }
    append ctrl_func_config "\]\n"
    return $ctrl_func_config
}

proc ::sth::hlapiGen::ctrl_convert_dhcp {i class} {

    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    
    regexp {([4|6])} $class match ipversion
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    #handle the port_handle
    set protocol_port_list_new ""
    foreach protocol_port $protocol_port_list {
        append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    foreach protocol_port $protocol_port_list_new {
        set ctrl_func_config ""
        append ctrl_func_config "set ctrl_ret$i \[sth::$ctrl_func    \\\n"
        append ctrl_func_config "                     -port_handle        \"$protocol_port\"\\\n"
        append ctrl_func_config "                     -action        bind\\\n"
        append ctrl_func_config "                     -ip_version        $ipversion\\\n"
        #handle the mode
        set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
        set name_space [string range $table_name 0 [string last : $table_name]]
        set cmd_name $ctrl_func
        if {[info exists $name_space$cmd_name\_type(mode)]} {
            set value_type [set $name_space$cmd_name\_type(mode)]
            if {[regexp {CHOICES} $value_type]} {
                set value [lindex [regsub {CHOICES} $value_type ""] 0]
            }
            append ctrl_func_config "                     -mode        $value\\\n"
        }
            
        append ctrl_func_config "\]\n"
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$i sth::$ctrl_func
    }
}


proc ::sth::hlapiGen::ctrl_convert_dhcpserver {i class} {

    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    
    regexp {([4|6])} $class match ipversion
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    #handle the port_handle
    set protocol_port_list_new ""
    foreach protocol_port $protocol_port_list {
        append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    foreach protocol_port $protocol_port_list_new {
        set ctrl_func_config ""
        append ctrl_func_config "set ctrl_ret$i \[sth::$ctrl_func    \\\n"
        append ctrl_func_config "                     -port_handle        \"$protocol_port\"\\\n"
        append ctrl_func_config "                     -action        connect\\\n"
        append ctrl_func_config "                     -ip_version        $ipversion\\\n"
        #handle the mode
        set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
        set name_space [string range $table_name 0 [string last : $table_name]]
        set cmd_name $ctrl_func
        if {[info exists $name_space$cmd_name\_type(mode)]} {
            set value_type [set $name_space$cmd_name\_type(mode)]
            if {[regexp {CHOICES} $value_type]} {
                set value [lindex [regsub {CHOICES} $value_type ""] 0]
            }
            append ctrl_func_config "                     -mode        $value\\\n"
        }
            
        append ctrl_func_config "\]\n"
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$i sth::$ctrl_func
    }
}

proc ::sth::hlapiGen::ctrl_convert_ppp {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    
    #handle the device handle
    foreach protocol_port $protocol_port_list {
        set ctrl_func_config ""
        set port_handle $::sth::hlapiGen::port_ret($protocol_port)
        append ctrl_func_config "set ctrl_ret$j \[sth::$ctrl_func    \\\n"
        append ctrl_func_config "                     -port_handle        \"$port_handle\"\\\n"
        append ctrl_func_config "                     -action        up\\\n"
        append ctrl_func_config "\]\n"
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$j sth::$ctrl_func
        incr j
    }   
}

proc ::sth::hlapiGen::ctrl_convert_lacp {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    set lag_port ""
    foreach protocol_port $protocol_port_list {
        set lag_handle [stc::get $protocol_port -children-lag]
        if {$lag_handle ne ""} {
            set lag_port_handle  [stc::get $lag_handle -PortSetMember-targets]
            set lacpgroupconfig_handle [stc::get $lag_handle -children-lacpgroupconfig]
            foreach port $lag_port_handle {
                lappend lag_port  $port 
            }
            if {$lacpgroupconfig_handle eq ""} {
                set comments ""
                append comments "\n##############################################################\n"
                append comments "#there is no lacp protocol on the lag , return\n"
                append comments "##############################################################\n"
                puts_to_file $comments
                return
            }
        } else {
             lappend lag_port  $protocol_port
        }
    }
    set protocol_port_list $lag_port
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    
    #handle the device handle
    foreach protocol_port $protocol_port_list {
        set ctrl_func_config ""
        set port_handle $::sth::hlapiGen::port_ret($protocol_port)
        append ctrl_func_config "set ctrl_ret$j \[sth::$ctrl_func    \\\n"
        append ctrl_func_config "                     -port_handle        \"$port_handle\"\\\n"
        append ctrl_func_config "                     -action        start\\\n"
        append ctrl_func_config "\]\n"
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$j sth::$ctrl_func
        incr j
    }   
}

proc ::sth::hlapiGen::ctrl_convert_ospf {i class} {

    #prepare a fake table for emulation_ospf_control from either v2 or v3
    regexp {([2|3])} $class match ospfversion
    set table_name "::sth::ospf::ospfTable"
    set cmd_name "emulation_ospfv2_control"
    if {$ospfversion == 3} {
        set cmd_name "emulation_ospfv3_control"
    }
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]

    #prepare a fake table for ospf common
    array unset ::sth::ospf::emulation_ospf_control_stcobj
    array unset ::sth::ospf::emulation_ospf_control_stcattr
    array unset ::sth::ospf::emulation_ospf_control_type
    array set ::sth::ospf::emulation_ospf_control_stcobj [array get $name_space$cmd_name\_stcobj]
    array set ::sth::ospf::emulation_ospf_control_stcattr [array get $name_space$cmd_name\_stcattr]
    array set ::sth::ospf::emulation_ospf_control_type [array get $name_space$cmd_name\_type]
    
    ctrl_convert_handle $i $class
}


proc ::sth::hlapiGen::ctrl_convert_ancp {i class} {

    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set ancp_ctrl_func_config ""
    append ancp_ctrl_func_config "set ancp_ctrl \[sth::$ctrl_func    \\\n"
    append ancp_ctrl_func_config "-ancp_handle   all\\\n"
    append ancp_ctrl_func_config "-ancp_subscriber   all\\\n"
    append ancp_ctrl_func_config "-action   initiate\\\n"
    append ancp_ctrl_func_config "-action_control   start\\\n"
    append ancp_ctrl_func_config "\]\n"
    puts_to_file $ancp_ctrl_func_config
    gen_status_info ancp_ctrl sth::$ctrl_func

}

proc ::sth::hlapiGen::ctrl_convert_rsvp_tunnel {i class} {
    
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    
    set protocol_device_list  $::sth::hlapiGen::protocol_to_devices(rsvptunnelparams_ctrl)
    
    puts_to_file [get_device_created $protocol_device_list device_list tunnel_handle]
    
    set ctrl_func_config [ctrl_convert_handle_common ctrl_ret$i $ctrl_func $class device_list]
    puts_to_file $ctrl_func_config
    gen_status_info ctrl_ret$i sth::$ctrl_func	
}

proc ::sth::hlapiGen::ctrl_convert_ptp {i class} {

    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    append ctrl_func_config "set ctrl_ret$i \[sth::$ctrl_func    \\\n"
    #in the basic function only config the port handle for the ctrl fucntion and the mode
    
    #handle the port_handle
    set protocol_port_list_new ""
    foreach protocol_port $protocol_port_list {
        append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    append ctrl_func_config "                     -port_handle        \"$protocol_port_list_new\"\\\n"
    append ctrl_func_config "                     -action_control        start\\\n"
    
    append ctrl_func_config "\]\n"
    puts_to_file $ctrl_func_config
    gen_status_info ctrl_ret$i sth::$ctrl_func	
}


proc ::sth::hlapiGen::ctrl_convert_dot1x {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_device_list  $::sth::hlapiGen::protocol_to_devices($class)
    #handle the port_handle
    foreach device_handle $protocol_device_list {
        #append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
        set ctrl_func_config ""
        set comments "#! if you need to download the PAC key file or the supplicant Certificate, need to add the two options:\n"
        append comments "#       -action \n"
        append comments "#       -certificate_dir\n"
        append comments "# also the -port_handle is need to download the file"
        puts_to_file [get_device_created $device_handle device_list handle]
        append ctrl_func_config "set ctrl_ret$j \[sth::$ctrl_func    \\\n"
        append ctrl_func_config "                     -handle       \$device_list\\\n"
        append ctrl_func_config "                     -mode        start\\\n"
        append ctrl_func_config "\]\n"
        puts_to_file $comments
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$j sth::$ctrl_func	
        incr j
    }
}

proc ::sth::hlapiGen::ctrl_convert_rfc {i class} {
    upvar i j
    set accessConcGen [stc::get project1 -children-AccessConcentratorGenParams]
    if {$accessConcGen eq ""} {
       if {[regexp -nocase "3918" $class]} {
             set ctrl_func "test_rfc3918_control"
       } else  {
           set ctrl_func "test_rfc2544_control"
        }
    } else {
          set ctrl_func "rfc2544_asymmetric_control"
      }
    append ctrl_func_config "set ctrl_ret$j \[sth::$ctrl_func    \\\n"
    append ctrl_func_config "                     -action       run\\\n"
    append ctrl_func_config "                     -wait        1\\\n"
    append ctrl_func_config "\]\n"
    puts_to_file $ctrl_func_config
    gen_status_info ctrl_ret$j sth::$ctrl_func	
    incr j
}
proc ::sth::hlapiGen::ctrl_convert_httpmodehandleserver {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set http_handle_list  $::sth::hlapiGen::devices_to_httphandle($class)
    foreach http_handle $http_handle_list {
                puts_to_file "set serverhandle \[keylget $http_handle server_handle\] "
                set ctrl_func_config ""
                append ctrl_func_config "set ctrl_ret$i \[sth::$ctrl_func    \\\n"
                append ctrl_func_config "                     -mode        start\\\n"
                append ctrl_func_config "                     -handle        \$serverhandle\\\n"
                append ctrl_func_config "\]\n"
                puts_to_file $ctrl_func_config
                gen_status_info ctrl_ret$i sth::$ctrl_func
                incr i
    }
}
proc ::sth::hlapiGen::ctrl_convert_httpmodehandleclient {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set http_handle_list  $::sth::hlapiGen::devices_to_httphandle($class)
    foreach http_handle $http_handle_list {
        puts_to_file "set clienthandle \[keylget $http_handle client_handle\] "
                set ctrl_func_config ""
                append ctrl_func_config "set ctrl_ret$i \[sth::$ctrl_func    \\\n"
                append ctrl_func_config "                     -mode        start\\\n"
                append ctrl_func_config "                     -handle        \$clienthandle\\\n"
                append ctrl_func_config "\]\n"
        puts_to_file $ctrl_func_config
        gen_status_info ctrl_ret$i sth::$ctrl_func
        incr i
    }
}

proc ::sth::hlapiGen::ctrl_convert_iptv {i class} {
    upvar i j
    set ctrl_func [set ::sth::hlapiGen::hlapi_gen_ctrlFunc($class)]
    set protocol_port_list  $::sth::hlapiGen::protocol_to_ports($class)
    #in the basic function only config the port handle for the ctrl fucntion and the mode

    #handle the port_handle
    set protocol_port_list_new ""
    foreach protocol_port $protocol_port_list {
        append protocol_port_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }

    set ctrl_func_config "set ctrl_ret$j \[sth::$ctrl_func    \\\n"
    append ctrl_func_config "                     -port_handle       $protocol_port_list_new\\\n"
    append ctrl_func_config "                     -mode       start\\\n"
    append ctrl_func_config "                     -test_env      testing_env\\\n"
    append ctrl_func_config "                     -test_duration    30 \\\n"
    append ctrl_func_config "                     -test_type        channel_zapping_test\\\n"
    append ctrl_func_config "\]\n"
    puts_to_file $ctrl_func_config
    gen_status_info ctrl_ret$j sth::$ctrl_func
    incr j
}
#***********************************************************************************************************<-#

