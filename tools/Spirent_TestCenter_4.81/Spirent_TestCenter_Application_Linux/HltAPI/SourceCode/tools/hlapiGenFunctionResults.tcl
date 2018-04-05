namespace eval ::sth::hlapiGen:: {

}

#***********************************************************************************************************->#
#result or info convert part function
#***********************************************************************************************************->#
#used for the control function which has the two options "-port_handle"
#input: i       => the index of the hltapi result fucntion in this script file.
#       class   => the class name, it will be used to know which hltapi result function will be called in the
#                   script file
#output: output the hltapi protocol result function to the file.
proc ::sth::hlapiGen::result_convert_port_list {i class} {

    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    foreach protocol_port $port_handle_list {
        append port_handle_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    set result_func_config [result_convert_port_common results_ret$i $result_func $class $port_handle_list_new]

    puts_to_file $result_func_config
    gen_status_info_for_results results_ret$i sth::$result_func
}


#used for the control function which has the two options "-handle and -mode", handle is the device handle list
#input: i       => the index of the hltapi result fucntion in this script file.
#       class   => the class name, it will be used to know which hltapi result function will be called in the
#                   script file
#output: output the hltapi protocol result function to the file.
proc ::sth::hlapiGen::result_convert_handle {i class} {
    upvar i j
    
    set devices_handle_list  $::sth::hlapiGen::protocol_to_devices($class)
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    set handle_type "handle"
    set device_var_name device
    if {$::sth::hlapiGen::scaling_test} {
        puts_to_file [get_device_created_scaling $devices_handle_list device_list_scaling $handle_type]
        set result_func_config "foreach device \$device_list_scaling \{\n"     
        append result_func_config [result_convert_handle_common results_ret$j $result_func $class $device_var_name]
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$j sth::$result_func
        puts_to_file "\}\n"
    } else {
        foreach device_handle $devices_handle_list {
            set result_func_config [get_device_created $device_handle $device_var_name $handle_type]
            puts_to_file $result_func_config
            set result_func_config [result_convert_handle_common results_ret$j $result_func $class $device_var_name]
            puts_to_file $result_func_config
            gen_status_info_for_results results_ret$j sth::$result_func
            incr j
        }
    }
    
}


proc ::sth::hlapiGen::result_convert_dhcp {i class} {

    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""
    set result_func_config ""
    regexp {([4|6])} $class match ipversion
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    foreach protocol_port $port_handle_list {
        append port_handle_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    foreach port_handle $port_handle_list_new {
        set result_func_config ""
        append result_func_config "set results_ret$i \[sth::$result_func    "
        append result_func_config "\\\n            -port_handle        \"$port_handle\""
        append result_func_config "\\\n            -action         collect"
        append result_func_config "\\\n            -mode         session"
        append result_func_config "\\\n            -ip_version         $ipversion"
        append result_func_config "\]\n"
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$i sth::$result_func
    }
}

proc ::sth::hlapiGen::result_convert_dhcpserver {i class} {

    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""
    set result_func_config ""
    regexp {([4|6])} $class match ipversion
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]

    foreach protocol_port $port_handle_list {
        append port_handle_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    foreach port_handle $port_handle_list_new {
        set result_func_config ""
        append result_func_config "set results_ret$i \[sth::$result_func    "
        append result_func_config "\\\n            -port_handle        \"$port_handle\""
        append result_func_config "\\\n            -action         COLLECT"
        append result_func_config "\\\n            -ip_version         $ipversion"
        append result_func_config "\]\n"
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$i sth::$result_func
    }
}

proc ::sth::hlapiGen::result_convert_ospf {i class} {

    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""
    set result_func_config ""
    set protocol_device_list  $::sth::hlapiGen::protocol_to_devices($class)
    #handle the device handle
    if {$::sth::hlapiGen::scaling_test} {
        puts_to_file [get_device_created_scaling $protocol_device_list device_list handle]
    } else {
        puts_to_file [get_device_created $protocol_device_list device_list handle]
    }
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    append result_func_config "set results_ret$i \[sth::$result_func    "
    append result_func_config "\\\n            -handle         \$device_list\\\n"
    
    append result_func_config "\]\n"
    puts_to_file $result_func_config
    gen_status_info_for_results results_ret$i sth::$result_func
    
    #add emulation_ospf_route_info here
    set result_func_config ""
    set result_func "emulation_ospf_route_info"
    if {$::sth::hlapiGen::scaling_test} {
        puts_to_file [get_device_created_scaling $protocol_device_list device_list handle]
    } else {
        puts_to_file [get_device_created $protocol_device_list device_list handle]
    }
    append result_func_config "set route_results_ret$i \[sth::$result_func    "
    
    append result_func_config "\\\n            -handle         \$device_list\\\n"
    
    append result_func_config "\]\n"
    puts_to_file $result_func_config
    gen_status_info_for_results route_results_ret$i sth::$result_func
}

proc ::sth::hlapiGen::result_convert_mld {i class} {

    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""
    set result_func_config ""
    set protocol_device_list  $::sth::hlapiGen::protocol_to_devices($class)
    #handle the device handle
        puts_to_file [get_device_created $protocol_device_list device_list handle]
        set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
        append result_func_config "set results_ret$i \[sth::$result_func    "
        append result_func_config "\\\n            -handle         \$device_list\\\n"
        
        append result_func_config "\]\n"
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$i sth::$result_func
}


proc ::sth::hlapiGen::result_convert_port {i class} {
    upvar i j
    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""
    set port_lag_handle ""
    foreach port $port_handle_list {
	set lag [stc::get $port -children-lag]
        if {$lag ne ""} {
	    lappend port_lag_handle  [stc::get $lag -PortSetMember-targets]
            set lacpgroupconfig_handle [stc::get $lag -children-lacpgroupconfig]
            if {$lacpgroupconfig_handle eq ""} {
                set comments ""
                append comments "\n##############################################################\n"
                append comments "#there is no lacp protocol on the lag , return\n"
                append comments "##############################################################\n"
                puts_to_file $comments
                return
            }
	} else {
	    lappend port_lag_handle $port
	}
    }
    regsub -all "\{" $port_lag_handle " " port_lag_handle
    regsub -all "\}" $port_lag_handle " " port_lag_handle
    set port_handle_list $port_lag_handle
    foreach protocol_port $port_handle_list {
        append port_handle_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    foreach port_handle $port_handle_list_new {
        set result_func_config [result_convert_port_common results_ret$j $result_func $class $port_handle]
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$j sth::$result_func
        incr j
    }
    
}


proc ::sth::hlapiGen::result_convert_route {i class} {
    upvar i j
    upvar bgp_devices_handle_list bgp_devices_handle_list
    set route_handle_list  $::sth::hlapiGen::protocol_to_devices($class)
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    set devices_handle_list ""
    foreach route_handle $route_handle_list {
        set device_handle [stc::get [stc::get $route_handle -parent] -parent]
        if {[regexp -nocase "bgpipv4routeconfig" $class] || [regexp -nocase "bgpipv6routeconfig" $class]} {
            if {[lsearch $bgp_devices_handle_list $device_handle] < 0} {
                set devices_handle_list [concat $devices_handle_list $device_handle]
                set bgp_devices_handle_list $devices_handle_list
            }
        } else {
            set devices_handle_list [concat $devices_handle_list $device_handle]
        }
    }
    
    if {$devices_handle_list == ""} {
        return
    }

    if {$::sth::hlapiGen::scaling_test} {
        puts_to_file [get_device_created_scaling $devices_handle_list device_list_scaling handle]
        set result_func_config "foreach device \$device_list_scaling \{\n"     
        append result_func_config [result_convert_handle_common results_ret$j $result_func $class device]
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$j sth::$result_func
        puts_to_file "\}\n"
    } else {
        foreach device_handle $devices_handle_list {
            set handle_type "handle"
            set device_var_name device
            puts_to_file [get_device_created $device_handle $device_var_name $handle_type]
            set result_func_config [result_convert_handle_common results_ret$j $result_func $class $device_var_name]
            puts_to_file $result_func_config
            gen_status_info_for_results results_ret$j sth::$result_func
            incr j
        }
    }
}

proc ::sth::hlapiGen::result_convert_handle_common {res_ret result_func class handlelist} {
    
    
    append result_func_config "set $res_ret \[sth::$result_func    "
    append result_func_config "\\\n             -handle       \$$handlelist\\\n"
    set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name $result_func
    

    if {[info exists $name_space$cmd_name\_type(mode)]} {
        set value_type [set $name_space$cmd_name\_type(mode)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append result_func_config "                     -mode        $value\\\n"
    }
    if {[info exists $name_space$cmd_name\_type(action)]} {
        set value_type [set $name_space$cmd_name\_type(action)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append result_func_config "                     -action        $value\\\n"
    }
    append result_func_config "\]\n"
    return $result_func_config    
}

proc ::sth::hlapiGen::result_convert_port_common {res_ret result_func class port_list} {
    set result_func_config ""
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    append result_func_config "set $res_ret \[sth::$result_func    "
    append result_func_config "\\\n            -port_handle         \"$port_list\"\\\n"
    
    set table_name [set ::sth::hlapiGen::hlapi_gen_tableName($class)]
    set name_space [string range $table_name 0 [string last : $table_name]]
    set cmd_name $result_func
    if {[info exists $name_space$cmd_name\_type(mode)]} {
        set value_type [set $name_space$cmd_name\_type(mode)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append result_func_config "                     -mode        $value\\\n"
    }
    
    if {[info exists $name_space$cmd_name\_type(action)]} {
        set value_type [set $name_space$cmd_name\_type(action)]
        if {[regexp {CHOICES} $value_type]} {
            set value [lindex [regsub {CHOICES} $value_type ""] 0]
        }
        append result_func_config "                     -action        $value\\\n"
    }
    
    append result_func_config "\]\n"
    return $result_func_config
}


proc ::sth::hlapiGen::result_convert_eoam {i class} {

    upvar i j
    set port_handle_list  $::sth::hlapiGen::protocol_to_ports($class)
    set port_handle_list_new ""

    foreach protocol_port $port_handle_list {
        append port_handle_list_new "$::sth::hlapiGen::port_ret($protocol_port) "
    }
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    foreach port_handle $port_handle_list_new {
        set result_func_config ""
        append result_func_config "set results_ret$j \[sth::$result_func\\\n"
        append result_func_config "            -port_handle         \"$port_handle\"\\\n"
        append result_func_config "            -mode         aggregate\\\n"
        append result_func_config "            -action         get_topology_stats\\\n"
        append result_func_config "\]\n"
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$i sth::$result_func
    }
}

proc ::sth::hlapiGen::result_convert_rfc {i class} {

    upvar i j
    set accessConcGen [stc::get project1 -children-AccessConcentratorGenParams]
    if {$accessConcGen eq ""} {
       if {[regexp -nocase "3918" $class]} {
             set result_func "test_rfc3918_info"
       } else {
           set result_func "test_rfc2544_info"
         }
    } else {
          set result_func "rfc2544_asymmetric_stats"
      }
    
    set rfcobj [set ::sth::hlapiGen::protocol_to_devices($class)]
    if {[regexp -nocase "rfc3918" $class]} {
        set rfc3918_children [array names sth::hlapiGen::$rfcobj\_obj]
        if {[llength $rfc3918_children] == 0} {
            return
        }
        foreach rfc3918 $rfc3918_children {
            if {![regexp -nocase "testcaseconfig" $rfc3918]} {
                continue
            }
            
            set test_case_type $rfc3918
            #it should have only one kind of test case
            break
        }
    } else {
        set test_case_type $class
    }
    
    switch -regexp [string tolower $test_case_type] {
        rfc3918mixedclassthroughputtestcaseconfig {
            set test_type "mixed_tput"
        }
        rfc3918aggregatedmulticastthroughputtestcaseconfig {
            set test_type "agg_tput"
        }
        rfc3918scaledgroupforwardingtestcaseconfig {
            set test_type "matrix"
        }
        rfc3918multicastforwardinglatencytestcaseconfig {
            set test_type "fwd_latency"
        }
        rfc3918joinleavelatencytestcaseconfig {
            set test_type "join_latency"
        }
        rfc3918multicastgroupcapacitytestcaseconfig {
            set test_type "capacity"
        }
        rfc2544backtobackframesconfig {
            set test_type "b2b"
        }
        rfc2544framelossconfig {
            set test_type "fl"
        }
        rfc2544latencyconfig {
            set test_type "latency"
        }
        rfc2544throughputconfig {
            set test_type "throughput"
        }
        
    }
    
    append result_func_config "set results_ret$j \[sth::$result_func\\\n"
    append result_func_config "            -test_type         $test_type\\\n"
    append result_func_config "            -clear_result         1\\\n"
    append result_func_config "\]\n"
    puts_to_file $result_func_config
    gen_status_info_for_results results_ret$i sth::$result_func
}


proc ::sth::hlapiGen::result_convert_httpmodehandleserver {i class} {
    upvar i j
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    set http_handle_list  $::sth::hlapiGen::devices_to_httphandle($class)
    foreach http_handle $http_handle_list {
        puts_to_file "set serverhandle \[keylget $http_handle server_handle\] "
        set result_func_config ""
        append result_func_config "set results_ret$i \[sth::$result_func    \\\n"
        append result_func_config "                     -handle        \$serverhandle\\\n"
        append result_func_config "\]\n"
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$i sth::$result_func
        incr i
    }
}
proc ::sth::hlapiGen::result_convert_httpmodehandleclient {i class} {
    upvar i j
    set result_func [set ::sth::hlapiGen::hlapi_gen_resultFunc($class)]
    set http_handle_list  $::sth::hlapiGen::devices_to_httphandle($class)
    foreach http_handle $http_handle_list {
        puts_to_file "set clienthandle \[keylget $http_handle client_handle\] "
        set result_func_config ""
        append result_func_config "set results_ret$i \[sth::$result_func    \\\n"
        append result_func_config "                     -handle        \$clienthandle\\\n"
        append result_func_config "\]\n"
        puts_to_file $result_func_config
        gen_status_info_for_results results_ret$i sth::$result_func
        incr i
    }
    
}

