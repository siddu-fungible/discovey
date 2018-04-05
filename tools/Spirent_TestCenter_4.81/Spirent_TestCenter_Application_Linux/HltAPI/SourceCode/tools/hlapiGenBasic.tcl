namespace eval ::sth::hlapiGen:: {

}

#the hlapiGen device basic and common functions will be included in this file for hlapiGen

#--------------------------------------------------------------------------------------------------------#
#basic device config function, only can process the class under the device block, for the next level, 
#need to use a new defined function, which is related to the specific protcol, and in the new defined
#function, it can call this basic funtion.
#input:     device      =>  the port on which the interface config function will be used
#           calss       =>  the class name
#           mode        =>  the mode of the interface config fucntion
#           hlt_ret     =>  the return of the hltapi function in the generated script file
#           cfg_args    => the args prepared earlier for the bgp config function
#           first_time  => is this the first time to config the protocol on this device
#output:    the genrated hltapi interface_config funtion will be output to the file.
proc ::sth::hlapiGen::hlapi_gen_device_basic {device class mode hlt_ret cfg_args first_time} {

    set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    set hlapi_script [hlapi_gen_device_basic_without_puts $device $class $mode $hlt_ret $cfg_args $first_time]
    puts_to_file $hlapi_script
    gen_status_info $hlt_ret "sth::$cmd_name"
}
proc ::sth::hlapiGen::hlapi_gen_device_basic_without_puts {device class mode hlt_ret cfg_args first_time} {
    variable $device\_obj
    #set object_handle [set $device\_obj($class)]
    #variable $device\_$object_handle\_attr
    set hlapi_script ""
    #parse the table file
    set class_name $device
    set table_name $sth::hlapiGen::hlapi_gen_tableName($class)
    ::sth::sthCore::InitTableFromTCLList [set $table_name]
    set name_space [string range $table_name 0 [string last : $table_name]]
    if {[regexp -- {^rfc2544(.)+config(\d)+$} $class_name]} {
        set device_parent [stc::get $class_name -parent]
        if {[regexp -- "accessconcentratorgenparams" $device_parent]} {
             set cmd_name     rfc2544_asymmetric_config
        } else {
            set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
         }
    } else {
        set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
      }
    if {[info exists sth::hlapiGen::$device\_$device\_attr(-affiliationport-targets)]} {
        set port_handle [set sth::hlapiGen::$device\_$device\_attr(-affiliationport-targets)]
    }
    if {$first_time == 1} {
        if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
            set class_name $device
            if {[regexp -- {^rfc2544(.)+config(\d)+$} $class_name]} {
                set device_parent [stc::get $class_name -parent]
                if {[regexp -- "accessconcentratorgenparams" $device_parent]} {
                    append hlapi_script "set $hlt_ret \[sth::rfc2544_asymmetric_config \\\n"
                } else {
                    append hlapi_script "set $hlt_ret \[sth::test_rfc2544_config\\\n"
                  }
            } else {
            append hlapi_script "      set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
            }
            
        } else {
            puts_msg "hlapi gen don't support to convert the config on $class to the hltapi script"
            return
        }
        if {$class != "dhcpv4portconfig" && $class != "dhcpv6portconfig"} {
            set ::sth::hlapiGen::currentconfighandle $class
        }
        if {![regexp "^$" $mode]} {
            append hlapi_script "			-mode			    $mode\\\n"
        }
         
        append hlapi_script $cfg_args
         
       #cfg the port level objects
        if {[info exists port_handle]} {
            set port_handle_new $::sth::hlapiGen::port_ret($port_handle)
            if {[info exists $name_space$cmd_name\_stcattr(port_handle)]} {
                append hlapi_script "			-port_handle	            $port_handle_new\\\n"
            }
            
            foreach port_level_obj [array names ::sth::hlapiGen::$port_handle\_obj] {
                #only when the obj will not appear in the device will be handled here
                if {![info exists $device\_obj($port_level_obj)] && ![regexp -nocase "^host$" $port_level_obj]} {
                    set port_level_obj_handles [set ::sth::hlapiGen::$port_handle\_obj($port_level_obj)]
                    foreach obj_handle $port_level_obj_handles {
                        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $port_handle $obj_handle $port_level_obj]
                    }
                }
                
            }
        }
        
        foreach sub_class [array names $device\_obj] {
            set obj_handles [set $device\_obj($sub_class)]
            foreach obj_handle $obj_handles {
                set temp ""
                set temp [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $sub_class]
                if {$temp != ""} {
                    append hlapi_script $temp
                } else {
                    append ::sth::hlapiGen::subclass_obj_dup " $obj_handle"
                }
            }
        }
    } else {
        #this is to enble one protocol on this device, only this obj related
        #attr will be configured
        if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
            append hlapi_script "        set $hlt_ret \[sth::$sth::hlapiGen::hlapi_gen_cfgFunc($class)\\\n"
        } else {
            puts_msg "hlapi gen don't support to convert the config on $class to the hltapi script"
            return
        }
        
        append hlapi_script "			-mode			    $mode\\\n"
        
        append hlapi_script "			-handle			    \$device_created\\\n"

        set key_values [update_key_value device $device none]
        append dev_def [get_device_created $device device_created $key_values]

        append hlapi_script $cfg_args
        set obj_handle [set $device\_obj($class)]
        ##get the all the hltapi options and values to config
        #use the data get from the table
        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $class]
        #cfg the port level obj
        if {[info exists port_handle]} {
            
            foreach port_level_obj [array names ::sth::hlapiGen::$port_handle\_obj] {
                if {![info exists $device\_obj($port_level_obj)]} {
                    set port_level_obj_handles [set ::sth::hlapiGen::$port_handle\_obj($port_level_obj)]
                    foreach obj_handle $port_level_obj_handles {
                        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $port_handle $obj_handle $port_level_obj]
                    }
                }
            }
        }
        
        foreach sub_class [array names $device\_obj] {
            if {![regexp -nocase "$class" $sub_class]} {
                set obj_handles [set $device\_obj($sub_class)]
                foreach obj_handle $obj_handles {
                    set already_output 1
                    foreach prev_sub_class_obj $::sth::hlapiGen::subclass_obj_dup {
                        if {[regexp -nocase "$prev_sub_class_obj" $obj_handle]} {
                            set already_output 0
                            regsub "$prev_sub_class_obj" $::sth::hlapiGen::subclass_obj_dup "" ::sth::hlapiGen::subclass_obj_dup
                            break
                        }
                    }
                    if {!$already_output} {
                        append hlapi_script [::sth::hlapiGen::config_obj_attr $name_space $cmd_name $device $obj_handle $sub_class]
                    }
                }
            }
        }
        puts_to_file $dev_def
    }
    append hlapi_script "\]\n"
    return $hlapi_script
}
#--------------------------------------------------------------------------------------------------------#
#configure the attr in the specified objects, this object handle is specified in $obj_handle
#input:     name_space  =>  the name space, the name_space and the cmd_name are used to get the hltapi options
#                           which has already do a map in the hltapi table
#           cmd_name    =>  the cmd name in the table
#           device      =>  the device handle, the parent of the obj_handle
#           obj_handle  =>  the object handle on which the 
#           class       =>  the class name
#ouput: return the htlapi attr value pair in a list
proc ::sth::hlapiGen::config_obj_attr {name_space cmd_name device obj_handle class} {
    set hlapi_script ""
    set lag_transmit_algorithm_flag 0
    set class [::sth::hlapiGen::pre_process_obj $device $class $obj_handle]
    foreach arg [array names $name_space$cmd_name\_stcobj] {
        if {($lag_transmit_algorithm_flag==1) && ([regexp -nocase "l2_hash_option" $arg]||[regexp -nocase "l3_hash_option" $arg])} {
            continue
        }
        set class_in_table [string tolower [set $name_space$cmd_name\_stcobj($arg)]]
        set attr_in_table [string tolower [set $name_space$cmd_name\_stcattr($arg)]]
        if {[info exists $name_space$cmd_name\_supported($arg)]} {
            set supported [set $name_space$cmd_name\_supported($arg)]
            if {[regexp -nocase {false} $supported]} {
                continue
            }
        }
        if {[regexp -nocase "^$class_in_table$" $class]} {
            if {[info exists sth::hlapiGen::$device\_$obj_handle\_attr(-$attr_in_table)]} {
                set type [set $name_space$cmd_name\_type($arg)]
                set value [set sth::hlapiGen::$device\_$obj_handle\_attr(-$attr_in_table)]
                #If default value option disable, then skip generating
                if { $::sth::hlapiGen::default_value == 0 } {
                    if {[info exists $name_space$cmd_name\_default($arg)]} {
                        set default_val [set $name_space$cmd_name\_default($arg)]
                        if {[string match -nocase $value $default_val ]} {
                            continue;
                        }
                    }
                }

                if {[regexp -nocase {^null$} $value] || [regexp -nocase "^$" $value]} {
                    continue
                }
                if {[regexp -nocase "IfRecycleCount" $attr_in_table]} {
                    if {$value == 0} {
                        continue
                    } 
                }
                if {[regexp {CHOICES} $type]} {
                    #convert the value get in the data model to be one of the choices
                    set value [::sth::hlapiGen::get_choice_value $arg $type $value $name_space $cmd_name]
                    if {[regexp -nocase "transmit_algorithm" $arg] && [regexp -nocase "round_robin" $value]} {
                        set lag_transmit_algorithm_flag 1
                    }
                }
                
                if {([regexp -nocase "stack_ip_repeat" $arg] && $value == 0)|| ([regexp -nocase "stack_ipv6_repeat" $arg] && $value == 0)} {
                    continue
                }
                if {([regexp -nocase "stack_ip_recycle_count" $arg] && $value == 0)|| ([regexp -nocase "stack_ipv6_recycle_count" $arg] && $value == 0)} {
                    continue
                }
                if {([regexp -nocase "ip_stack_count" $arg] && $value == 1)|| ([regexp -nocase "ipv6_stack_count" $arg] && $value == 1)} {
                    continue
                }
                if {[regexp -nocase "enable_custom_pool" $arg] && [regexp -nocase "false" $value]} {
                    continue
                }
                if {[regexp -nocase "host_addr_prefix_length" $arg] &&  $value==24} {
                    continue
                }
                # Multiple Ipv4If children objects exist for a "Client & Relay Agent" object. Getting gateway_ipv4_addr_step and 
                # ipv4_gateway_address values are restricted to only one children object to avoid generating multiple "-arg value" pairs.
                if { $cmd_name eq "emulation_dhcp_group_config" 
                && ([regexp -nocase "gateway_ipv4_addr_step" $arg] || [regexp -nocase "ipv4_gateway_address" $arg]) 
                && ([info exists sth::hlapiGen::$device\_$obj_handle\_attr(-relayif-sources)] || [info exists sth::hlapiGen::$device\_$obj_handle\_attr(-arpproxyif-sources)])} { 
                    continue
                }
                if {[llength $value] > 1} {
                    if {[regexp -nocase {^name$} $attr_in_table]} {
                        regsub -all { } $value "_" value
                        append hlapi_script "			-$arg			$value \\\n"
                    } else {
                        append hlapi_script "			-$arg			\"$value\" \\\n"
                    }
                } else {
                    #for the bfd_registration  need to do special handle, if it is 0, should not output it.
                    #related hltapi functions are: 1) emulation_bgp_config, 2) emulation_isis_config
                    #3)emulation_ldp_config, 4) emulation_ospf_config, 5) emulation_rip_config, 6)emulation_rsvp_config
                    #also need to take care of emulation_mvpn_config later
                    if {[regexp "^bfd_registration$" $arg]} {
                        if {$value == 1} {
                            append hlapi_script "			-$arg			$value \\\n"
                        }
                    } else {
                        append hlapi_script "			-$arg			$value \\\n"
                    }
                    
                }
            }
        } 
    }
    return $hlapi_script
}




#--------------------------------------------------------------------------------------------------------#
#use this function to preprocess the class name, to make it keep consent with
#the class name in the hltapi table file. currently only deal with the vlan
#since for the vlan, when there is qinq, the outer vlan in the table will be
#defined as VlanIf_Outer, so change the vlanif in the xml for this vlan obj
#to be the vlanif_outer
#if there is some other class name need to be processed before use it, we can
#process it in this function.
#input: device      => the parent of the obj_handle
#       class       => the class of the obj_handle
#       obj_handle  => the object handle
#output: the new class after processed
proc ::sth::hlapiGen::pre_process_obj {device class obj_handle} {
    
    if {[info exists ::sth::hlapiGen::$device\_obj($class)]} {
        if {[llength [set ::sth::hlapiGen::$device\_obj($class)]] > 1} {
            if {[regexp -nocase {VlanIf} $class]} {
                #for the vlan obj we need to do more handle, since the outer vlan, in the table the obj name is vlanif_outer
                #if it is outer vlan then set the obj to be vlanif_outer
                set stack_target [set ::sth::hlapiGen::$device\_$obj_handle\_attr(-stackedonendpoint-targets)]
                if {[regexp {ethiiif} $stack_target]} {
                    set class "VlanIf_Outer"
                }

            } elseif {[regexp -nocase {Ipv6If} $class]} {
                #for the ipv6if there always two ipv6if, one is for the linklocal need to device if this link local addr will
                #be use or not.
                #check if the address is link local address, start with fe80::
                set ip_addr [set ::sth::hlapiGen::$device\_$obj_handle\_attr(-address)]
                if {[regexp {^fe80} $ip_addr]} {
                    set class "Ipv6If_Link_Local"
                }
            }
        }
    }
    return $class
}

#--------------------------------------------------------------------------------------------------------#
#convert the data model data to the arrays. there are 3 kinds of arrays:
#       sth::hlapiGen::$device\_obj:    the key is the children class of $object_handle, the value is
#                                       the handle, it also include the class of $object_handle
#       sth::hlapiGen::$device\_$object_handle\_attr: the key is the attr in the obj, $object_handle can be
#                                                       children of $device or the same with $device
#   input:  obj_handle  => the object handle, it can be chid of device or the device itself
#           device      => the object handle, it can be parent of obj_handle or the obj_handle itself
#   output:the global arrays described upper
proc ::sth::hlapiGen::get_attr {obj_handle device} {
    variable $device\_obj
    set class [regsub -all {\d+$} $obj_handle ""]
    variable $device\_$obj_handle\_attr

    if {[info exists $device\_obj($class)]} {
        if {[lsearch [set $device\_obj($class)] $obj_handle] == -1} {
            append $device\_obj($class) " $obj_handle"
        }
        
    } else {
        array set $device\_obj "$class $obj_handle"
    }
    
    set obj_attr [stc::get $obj_handle]
    set len [llength $obj_attr]
    for {set i 0} {$i < $len} {incr i} {
        set obj_attr [lreplace $obj_attr $i $i [string tolower [lindex $obj_attr $i]]]
        incr i
    }
    array set $device\_$obj_handle\_attr $obj_attr

    set obj_children [stc::get $obj_handle -children]
    if {![string match "" $obj_children ]} {
        foreach obj_child $obj_children {
            get_attr $obj_child $obj_handle
        }
    }
}



#--------------------------------------------------------------------------------------------------------#
#get the class which will trigger a hltapi function under the devices(port and the devices)
#input: devices=> the port and device handle list
#output: an array of the objects, the key is the class and the value is the objects of this class
proc ::sth::hlapiGen::get_objs {devices} {
    set port_list ""
    foreach device $devices {
        if {[regexp -nocase "port" $device]} {
            set lag_handle [stc::get $device -children-lag]
            if {$lag_handle ne ""} {
                set port_handle [stc::get $lag_handle -PortSetMember-targets]
                lappend port_list $port_handle
            }
        }
    }
    set port_handle ""
    if {$port_list ne ""} {
        foreach device $devices {
            if {![regexp -nocase $device $$port_list]} {
                lappend port_handle $device
            }
        }
        set devices $port_handle
    }

    if {![info exists ::sth::hlapiGen::unSupported]} {
        array set ::sth::hlapiGen::unSupported {}
    }
    if {![info exists ::sth::hlapiGen::warnings]} {
        array set ::sth::hlapiGen::warnings {}
    }
    foreach device $devices {
        if {![info exists sth::hlapiGen::$device\_obj]} {
            sth::hlapiGen::get_attr $device $device
        }
        set name [set ::sth::hlapiGen::$device\_$device\_attr(-name)]
        foreach class [array names sth::hlapiGen::$device\_obj] {
            #sth::hlapiGen::hltapi_obj have all the hltapi function needed
            if {[regexp -nocase "probe" $class]} {
                set probeList [set sth::hlapiGen::$device\_obj($class)]
                foreach probe $probeList {
                    lappend hltapi_obj(vqprobechannelblock) [set sth::hlapiGen::$probe\_obj(vqprobechannelblock)]
                }
            }
            # get captureanalyzerfilter objects for packet_config_pattern
            if {[regexp -nocase "^capture$" $class]} {
                set captureList [set sth::hlapiGen::$device\_obj($class)]
                foreach capture $captureList {
                    set captureFilterList [set sth::hlapiGen::$capture\_obj(capturefilter)]
                    foreach captureFilter $captureFilterList {                        
                        if {[info exists sth::hlapiGen::$captureFilter\_obj(captureanalyzerfilter)]} {
                            lappend hltapi_obj(capturefilter) $captureFilter
                        }
                    }
                }
            }
            if {[info exists sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
                if {[string match "_none_" $sth::hlapiGen::hlapi_gen_cfgFunc($class)]} {
                    puts_msg "Not supported by Save as HLTAPI: $class"
                } else {
                    set class_key $class
                    if {[info exists ::sth::hlapiGen::$device\_$device\_attr(-affiliatedrouter-targets)] && [regexp "ldprouterconfig" $class]} {
                        set attached_router [set ::sth::hlapiGen::$device\_$device\_attr(-affiliatedrouter-targets)]
                        set attch_ldp_router_config [stc::get $attached_router -children-ldprouterconfig]
                        if {![regexp "^$" $attch_ldp_router_config]} {
                            set class_key "ldprouterconfig_pe"
                        } 
                    }
                    if {![info exists hltapi_obj($class_key)]} {
                        set hltapi_obj($class_key) [set sth::hlapiGen::$device\_obj($class)]
                    } else {
                        lappend hltapi_obj($class_key) [set sth::hlapiGen::$device\_obj($class)]
                    }
                }
            } else {
                if {[regexp -nocase {config$} $class]} {
                    set obj [set sth::hlapiGen::$device\_obj($class)]
                    set active [set ::sth::hlapiGen::$device\_$obj\_attr(-active)]
                    if {$active} {
                        if {[info exist ::sth::hlapiGen::unSupported($class)]} {
                            set ::sth::hlapiGen::unSupported($class) "$::sth::hlapiGen::unSupported($class), $name"
                        } else {
                            set ::sth::hlapiGen::unSupported($class) $name                     
                        }
                    }
                }
            }
        }
        
        if {[info exists sth::hlapiGen::$device\_$device\_attr(-memberofvpnsite-targets)]} {
            set memberofvpnsite [set sth::hlapiGen::$device\_$device\_attr(-memberofvpnsite-targets)]
            foreach class "vpnsiteinfovplsldp vpnsiteinfovplsbgp vpnsiteinforfc2547" {
                if {[regexp $class $memberofvpnsite]} {
                    lappend hltapi_obj($class) $memberofvpnsite
                    break;
                }
            }
        }
    }
        
    return [array get hltapi_obj]
}

#get the objects that really will be used to triger to generate a hltapi fcuntion
#input:  the class name and objects list.
#ouput: the objects list will be used to triger the hltapi function.
proc ::sth::hlapiGen::get_hltapi_needed_objs {class objects device_created} {
    if {[regexp "pppprotocolconfig" $class]} {
        set objects_new ""
        foreach object $objects {
            set port [stc::get $object -parent]
            if {[info exists ::sth::hlapiGen::$port\_$object\_attr(-usesif-targets)]} {
                set objects_new [concat $objects_new "$object"]
            }
        }
        return $objects_new
    }
    
        #To check for raw emulated devices
        if {[string equal -nocase "emulateddevice" $class]==1 || [string equal -nocase "host" $class]==1} {
            set new_objects ""
            set rawemulateddevlist ""
            set flagEmu 0
            foreach emulateddev $objects {
                if { [array size ::sth::hlapiGen::protocol_to_devices] == 0 || ([info exist ::sth::hlapiGen::protocol_to_devices(emulateddevice)] && [array size ::sth::hlapiGen::protocol_to_devices] == 1)} {
                   set flagEmu -1 
                }
                foreach protocol [array names ::sth::hlapiGen::protocol_to_devices] {
                    if { [ set flagEmu [lsearch $::sth::hlapiGen::protocol_to_devices($protocol) $emulateddev ] ] != -1} {  
                        break   
                    }
                }
                if { $flagEmu == -1 && ![info exists ::sth::hlapiGen::$emulateddev\_$emulateddev\_attr(-containedlink-targets)] && [lsearch $device_created $emulateddev] == -1 } {
                    if { ![info exists ::sth::hlapiGen::$emulateddev\_obj(hdlcif)] } {
                        if {[info exists ::sth::hlapiGen::$emulateddev\_$emulateddev\_attr(-name)]} {
                            if {[string equal [set ::sth::hlapiGen::$emulateddev\_$emulateddev\_attr(-name)] "port_address"] !=1} {
                                set rawemulateddevlist [concat $rawemulateddevlist "$emulateddev"]
                            }
                        }
                    }
                }
            }
            if { $rawemulateddevlist != "" } {
                set new_objects "$rawemulateddevlist"
            } 
            return $new_objects 
        }   

    set new_objects ""
    foreach obj $objects {
        set active [stc::get $obj -active]
        if {[regexp -nocase true $active]} {
            set new_objects [concat $new_objects $obj]
        }
    }

    return $new_objects
}
#--------------------------------------------------------------------------------------------------------#
#a function used store the protocol related device and the ports

proc ::sth::hlapiGen::gather_info_for_ctrl_res_func {device class} {
    variable ::sth::hlapiGen::protocol_to_devices
    variable ::sth::hlapiGen::protocol_to_ports
    #here use the obj to indicit which protocol has been configured
    if {[info exists protocol_to_devices($class)]} {
        lappend protocol_to_devices($class) "$device"
    } else {
        set protocol_to_devices($class) $device
    }
    
    set port ""
    if {[regexp "port" $device]} {
        set port $device
    } elseif {[regexp -nocase "emulateddevice" $device] || [regexp -nocase "host" $device] || [regexp -nocase "router" $device]} {
        set port [stc::get $device -affiliationport-Targets]
    }
    if {![regexp "^$" $port]} {
        if {[info exists protocol_to_ports($class)]} {
            if {[lsearch $protocol_to_ports($class) $port] == -1} {
                append protocol_to_ports($class) " $port"
            }
            
        } else {
            set protocol_to_ports($class) $port
        }
    }
    
    
}

#--------------------------------------------------------------------------------------------------------#
proc ::sth::hlapiGen::dev_to_cfg_ret {class objects indx object_status} {
    upvar $object_status object_status_local
    #this part is used to set  the retrun value in of each obj which will be created in the hltapi script.
    foreach object $objects {
        if {[regexp "vqanalyzer" $object]} {
            set port [stc::get $object -parent]
            if {![isVqaConfigured $port]} {
                continue
            }
        }
        #if object is emulated device/host
        if {[regexp -nocase "emulateddevice" $object] || [regexp -nocase "^host" $object] || [regexp "vqanalyzer" $object]} {
            set device $object
        } else {
            set device [stc::get $object -parent]  
        }
        
        #set device [stc::get $object -parent]
        sth::hlapiGen::gather_info_for_ctrl_res_func $device $class
        if {![info exists object_status_local($object)] || $object_status_local($object) == 1} {
            set j 0
            if {[regexp {project} [stc::get $device -parent]]} {
                if {![info exists ::sth::hlapiGen::device_ret($device)]} {
                    set ::sth::hlapiGen::device_ret($device) "device_ret$indx $j"
                    set device_name [stc::get $device -name]
                    incr indx
                }
                
            } else {
                if {![info exists ::sth::hlapiGen::device_ret($object)]} {
                    set ::sth::hlapiGen::device_ret($object) "device_ret$indx $j"
                    set device_name [stc::get $object -name]
                    incr indx
                }
            }
            incr j
        } else {
            if {[regexp {project} [stc::get $device -parent]]} {
                set device_other [stc::get $object_status_local($object) -parent]
                set ret_var [set ::sth::hlapiGen::device_ret($device_other)]
                if {![info exists ::sth::hlapiGen::device_ret($device)]} {
                    set ::sth::hlapiGen::device_ret($device) "[lindex $ret_var 0] $j"
                }
            } else {
                set ret_var [set ::sth::hlapiGen::device_ret($object_status_local($object))]
                if {![info exists ::sth::hlapiGen::device_ret($object)]} {
                    set ::sth::hlapiGen::device_ret($object) "[lindex $ret_var 0] $j"
                }
            }
            incr j
            continue
        }    
    }
}

#--------------------------------------------------------------------------------------------------------#
#unset the arrays which store the attr and obj of the data model
# the sth::hlapiGen::$object\_obj and ::sth::hlapiGen::$object\_$sub_object\_attr will be unset
#$sub_object is the value in the sth::hlapiGen::$object\_obj
#input: objects => the object handle list
proc ::sth::hlapiGen::unset_data_model_attr {objects} {
    
    foreach object $objects {
        if {[array exists ::sth::hlapiGen::$object\_obj]} {
            foreach class [array names ::sth::hlapiGen::$object\_obj] {
                set sub_objects [set ::sth::hlapiGen::$object\_obj($class)]
                foreach sub_object $sub_objects {
                    if {![regexp "^$sub_object$" $object]} {
                        unset_data_model_attr $sub_object
                    }
                    if {[array exists ::sth::hlapiGen::$object\_$sub_object\_attr]} {
                        array unset ::sth::hlapiGen::$object\_$sub_object\_attr
                    }
                }
            }
            array unset ::sth::hlapiGen::$object\_obj
            
        }
    }
}

#################################################################################
#this function will be used to get the objects which will be used to call the
#hltapi functon, for example, three objs can be created in hltapi function with
#the count, step and some other thing be set in this function, will only keep
#one some obj to triger the hltapi function, and remove the other two obj in this
#obj list which will be used to call the hltapi function,
#when remove the objs, we need record devices handles which map the removed obj.
#and also we need to get the count, step infromation of the hltapi function
#corresponding to the object.
################################################################################
proc ::sth::hlapiGen::multi_dev_check_func_basic {class devices} {
    variable devicelist_obj
    variable scaling_tmp
    variable device_index_scaling
    set update_obj ""
    set attrlist_ipif "Address Gateway"
    set attrlist_device "RouterId IPv6RouterId"
    set attrlist_vlanif "vlanid"
    set attrlist_aal5if "vci vpi"
    set attrlist_ethiiif "sourcemac"
      
    set device [lindex $devices 0]
    set obj [set sth::hlapiGen::$device\_obj($class)]
    #update the obj to return
    set update_obj $obj
    if {[llength $devices] <= 2} {
        array set scaling_tmp "$device\_$device\_count 1"
        set eMsg "the scaling mode only supports the devicelist with more than 2 devices"
        return -code error $eMsg;
    }
    #save the device handles which will be created in the same hltapi api function to the global variable
    set devicelist_obj($obj) $devices
     
    #update the datamode info for the step related infomation
    set count [llength $devices]
    array set scaling_tmp "$device\_$device\_count $count"
    
    update_step emulateddevice $devices $attrlist_device emulateddevice
    if {[info exists sth::hlapiGen::$device\_obj(ethiiif)]} {
        update_step ethiiif $devices $attrlist_ethiiif mac
    }
    if {[info exists sth::hlapiGen::$device\_obj(ipv4if)]} {
        update_step ipv4if $devices $attrlist_ipif ipv4
    }
    if {[info exists sth::hlapiGen::$device\_obj(ipv6if)]} {
        update_step ipv6if $devices $attrlist_ipif ipv6
    }
    if {[info exists sth::hlapiGen::$device\_obj(vlanif)]} {
        update_step vlanif $devices $attrlist_vlanif vlan
        #handle the vlan_id_mode and vlan_outer_id_mode
        #maybe need to update for dual vlan
        set vlanifhdl [set ::sth::hlapiGen::$device\_obj(vlanif)]
        foreach vlanif $vlanifhdl {
            if {[info exists scaling_tmp($device\_$vlanif\_vlanid.step)]} {
                if {$scaling_tmp($device\_$vlanif\_vlanid.step) != 0} {
                    array set scaling_tmp "$device\_$vlanif\_vlanid.mode increment"
                    array set scaling_tmp "$device\_$vlanif\_vlanid.count $device_index_scaling"
                } else {
                    array set scaling_tmp "$device\_$vlanif\_vlanid.mode fixed"
                    array set scaling_tmp "$device\_$vlanif\_vlanid.count 1"
                    unset scaling_tmp($device\_$vlanif\_vlanid.step)
                }
            }
            
        }
    }
    if {[info exists sth::hlapiGen::$device\_obj(greif)]} {
        set greif [set sth::hlapiGen::$device\_obj(greif)]
        set remotev4 [stc::get $greif -RemoteTunnelEndPointV4]
        set remotev6 [stc::get $greif -RemoteTunnelEndPointV6]
        if {![regexp "2000::2" $remotev6]} {
            update_step greif $devices "RemoteTunnelEndPointV6" ipv6
        } else {
            update_step greif $devices "RemoteTunnelEndPointV4" ipv4
        }
    }
    if {[info exists sth::hlapiGen::$device\_obj(aal5if)]} {
        update_step aal5if $devices $attrlist_aal5if aal5
    }
        
    
    return $update_obj
    
}

#this function is used to update the datamode info for the step related parameters
proc ::sth::hlapiGen::update_step {class objhdllist attrlist difftype} {
    variable scaling_tmp
    variable device_index_scaling
    
    set cmp [llength $objhdllist]
    #add one more condition here, if the class is null, the objhdllist can be compared
    for {set i 0} {$i < $cmp} {incr i} {
        if {$class == ""} {
            set subobjhdllist$i [lindex $objhdllist $i]
            set objhdl_sample$i [stc::get [set subobjhdllist$i] -parent]
        } else {
            set objhdl_sample$i [lindex $objhdllist $i]
            if {[string match -nocase "emulateddevice|router" $class]} {
                set subobjhdllist$i [set objhdl_sample$i]
            } else {
                if {![info exists ::sth::hlapiGen::[set objhdl_sample$i]\_obj($class)]} {
                    if {$i < 2} {
                        return
                    } else {
                        set cmp $i
                        break
                    }
                }
                set subobjhdllist$i [set ::sth::hlapiGen::[set objhdl_sample$i]\_obj($class)]
            }
        }
    }
    
        
        
    foreach attr $attrlist {
        set attr [string tolower $attr]
        for {set i 0} {$i < [llength $subobjhdllist0]} {incr i} {
            set subobjhdl0 [lindex $subobjhdllist0 $i]
            set subobjhdl1 [lindex $subobjhdllist1 $i]
            set attr_value0 [set ::sth::hlapiGen::$objhdl_sample0\_$subobjhdl0\_attr(-$attr)]
            set attr_value1 [set ::sth::hlapiGen::$objhdl_sample1\_$subobjhdl1\_attr(-$attr)]
            if {$attr_value0 == "null" || $attr_value0 == "" || $attr_value1 == "null" || $attr_value1 == ""} {
                continue
            }
            if {[regexp -nocase "emulateddevice" $difftype] && [regexp -nocase "ipv6routerid" $attr]} {
                set difftype "ipv6"
            }
            set step_value [calculate_difference $attr_value0 $attr_value1 $difftype]
            set step_value_next $step_value
            for {set j 2} {$j < $cmp} {incr j} {
                set step_value_pre $step_value_next
                if {![info exists subobjhdllist$j]} {
                    continue
                }
                set subobjhdl$j [lindex [set subobjhdllist$j] $i]
                set attr_value$j [set ::sth::hlapiGen::[set objhdl_sample$j]\_[set subobjhdl$j]\_attr(-$attr)]
                if {[set attr_value$j] == "null" || [set attr_value$j] == ""} {
                    continue
                }
                set prej [expr $j - 1]
                if {[catch {set step_value_next [calculate_difference [set attr_value$prej] [set attr_value$j] $difftype]} eMsg]} {
                    if {$j < $device_index_scaling} {
                        if {$j == 2} {
                            set j 1
                        }
                        set device_index_scaling $j
                    }
                    break
                } else {
                    if {![string match $step_value_pre $step_value_next]} {
                        if {$j < $device_index_scaling} {
                            if {$j == 2} {
                                set j 1
                            }
                            set device_index_scaling $j
                        }
                        break
                    }
                }
            }
            if {[string is integer $step_value] && $step_value < 0} {
                set eMsg "the step_value between $objhdl_sample0 and $objhdl_sample1 is not an integer above 0"
                return -code error $eMsg;
            }
	    # US36836 convert SrcIpAddr.step DstIpAddr.step  TunnelId.step to SrcIpAddrStep SrcIpAddrStep DstIpAddrStep TunnelIdStep in rsvpTable.tcl
	    # add this for support scaling mode 
            if {[string match "rsvpegresstunnelparams*" $subobjhdl0 ] || [string match "rsvpingresstunnelparams*" $subobjhdl0 ]  } {
                set stepString "step"
                array set scaling_tmp "$objhdl_sample0\_$subobjhdl0\_$attr$stepString $step_value"
            } else {
                array set scaling_tmp "$objhdl_sample0\_$subobjhdl0\_$attr\.step $step_value"
            }

        }
    }
}

# this function is used to calculate the different between two values
proc ::sth::hlapiGen::calculate_difference {value1 value2 difftype} {
    if {$difftype == ""} {
        #set the correct difftype based on the format of value
        if {[regexp {([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)} $value1]} {
            set difftype ipv4
        } elseif {[regexp {([0-f]{2})\:([0-f]{2})\:([0-f]{2})\:([0-f]{2})} $value1] || [regexp {([0-f]{2})\-([0-f]{2})\-([0-f]{2})\-([0-f]{2})} $value1]} {
            set difftype mac
        } elseif {[::ip::is 6 $value1]} {
            set difftype ipv6
        } elseif {[regexp {([0-9]+)\:([0-9]+)} $value1]} {
            set difftype float
        }
        #specially handle
        
    }
    switch -regexp -- $difftype {
        "ipv4|emulateddevice" {
            #ipv4
            set split_sig "."
            set seg_diff 256
        }
        "ipv6" {
            set split_sig ":"
            set seg_diff 65536
            set value1 [::ip::normalize $value1]
            set value2 [::ip::normalize $value2]
        }
        "mac" {
            if {[regexp {\:} $value1]} {
                set split_sig ":"
            } elseif {[regexp {\-} $value1]} {
                set split_sig "-"
            } elseif {[regexp {\.} $value1]} {
                set split_sig "."
            }
            set seg_diff 256
        }
        "float" {
            set value1 [join [split $value1 :] .]
            set value2 [join [split $value2 :] .]
            set diff [expr $value2 - $value1]
            return $diff
        }
        default {
            set diff [expr $value2 - $value1]
            return $diff
        }
    }
    
    #calculate the difference after spliting the value list into seperate values
    if {[info exists split_sig]} {
        set diff_list ""
        set value_list1 [split $value1 $split_sig]
        set value_list2 [split $value2 $split_sig]
        set seg_length [expr [llength $value_list1] - 1]
        for {set i $seg_length} {$i >= 0} {} {
            set value_cmp1 [lindex $value_list1 $i]
            set value_cmp2 [lindex $value_list2 $i]
            if {$value_cmp1 == ""} {
                set i [expr $i - 1]
                continue
            }
            if {$split_sig == ":" || $split_sig == "-" || $split_sig == "."} {
                #update the value to int
                if {[regexp {ipv6|mac} $difftype]} {
                    set value_cmp1 [format "%d" 0X$value_cmp1]
                    set value_cmp2 [format "%d" 0X$value_cmp2]
                }
            }
            if {$value_cmp2 < $value_cmp1} {
                set value_cmp2 [expr $value_cmp2 + $seg_diff]
                set update_value [expr [lindex $value_list2 [expr $i-1]] - 1]
                set value_list2 [lreplace $value_list2 [expr $i-1] [expr $i-1] $update_value]
            }
            set diff [expr $value_cmp2 - $value_cmp1]
            
            if {$difftype == "mac"} {
                set diff  [format "%02x" $diff]
            } elseif {$difftype == "ipv6"} { 
                set diff  [format "%x" $diff]
            }
            set diff [concat $diff $diff_list]
            set diff_list $diff
            set i [expr $i - 1]
        }
        
        set update_diff [join $diff_list $split_sig]
        if {$difftype == "ipv6"} {
            regsub {^(0:)+} $update_diff "::" update_diff
            regsub {^::0$} $update_diff "::" update_diff
        }
        
        return $update_diff
    }
    
}

# this function is used to update the cound the attr step, return the updated route obj for scaling mode
proc ::sth::hlapiGen::route_scaling_pre_process {route_types router_hdl attrlist} {
    variable scaling_tmp
    set ret_route_hdl ""
    if {$route_types == ""} {
        set route_types [array names ::sth::hlapiGen::$router_hdl\_obj]
    }
    
    foreach route_type $route_types {
        set route_hdl_list [set ::sth::hlapiGen::$router_hdl\_obj($route_type)]
        set length [llength $route_hdl_list]
        if {$length >= 2} {
            set route_hdl [lindex $route_hdl_list 0]
            set ::sth::hlapiGen::$router_hdl\_$route_hdl\_attr(-count) $length
            if {[catch {update_step "" $route_hdl_list $attrlist ""} retMsg]} {
                set ret_route_hdl [concat $ret_route_hdl $route_hdl_list]
            } else {
                set ret_route_hdl [concat $ret_route_hdl $route_hdl]
                foreach args [lsort [array names scaling_tmp]] {
                    set sub_arg [split $args _]
                    set new_arg [lindex $sub_arg 0]\_[lindex $sub_arg 1]\_attr(-[lindex $sub_arg 2])
                    set ::sth::hlapiGen::$new_arg $scaling_tmp($args)
                }
                array unset scaling_tmp
            }
        } else {
            set ret_route_hdl [concat $ret_route_hdl $route_hdl_list]
        }
    }
    
    return $ret_route_hdl
}


# this function is used to unset the stcobj and stcattr of the table file,
# in case some stcobj and stcattr info will not be updated when sequent scripts are running
proc ::sth::hlapiGen::unset_table_obj_attr {class} {
    if {[regexp -nocase "streamblock" $class]} {
        set name_space "::sth::Traffic::"
        set cmd_name "traffic_config"
    } else {
        set table_name $sth::hlapiGen::hlapi_gen_tableName($class)
        set name_space [string range $table_name 0 [string last : $table_name]]
        set cmd_name $sth::hlapiGen::hlapi_gen_cfgFunc($class)
    }
    variable $name_space$cmd_name\_Initialized

    if {[info exists $name_space$cmd_name\_Initialized]} {
        unset $name_space$cmd_name\_Initialized
    }
}
# this function is used to handle the returned object in the scaling mode
proc ::sth::hlapiGen::get_obj_for_scaling {devices class multi_dev_check_func obj_old} {
    variable scaling_tmp
    variable devicelist_obj
    variable device_index_scaling
    #get the device list for the specific class with the same port
    set hltapi_obj_cfg ""
    array unset devicelist
    array set devicelist ""
    if {$devices == ""} {
        #when the device has already created, for the protocol to be configured on this device, no need to do scaling.
        return $obj_old
    }
    foreach device $devices {
        if {[info exists ::sth::hlapiGen::$device\_obj($class)] && [lsearch $obj_old [set ::sth::hlapiGen::$device\_obj($class)]] >= 0} {
            regsub -all {\{|\}} [array get devicelist_obj] "" list_tmp
            if {[lsearch $list_tmp $device] >= 0} {
                #if the device has been created in other protocol function, we need to keep the obj in returned value
                set obj [set sth::hlapiGen::$device\_obj($class)]
                set hltapi_obj_cfg [concat $hltapi_obj_cfg $obj]
                if {[info exists devicelist_obj($obj)]} {
                    set devicelist_obj($obj) [concat $devicelist_obj($obj) $device]
                } else {
                    set devicelist_obj($obj) $device
                }
            } else {
                set port_hdl [set sth::hlapiGen::$device\_$device\_attr(-affiliationport-targets)]
                if {[info exists devicelist($port_hdl)]} {
                    set devicelist($port_hdl) [concat $devicelist($port_hdl) $device]
                } else {
                    array set devicelist "$port_hdl $device"
                }
            }
        }
    }
    foreach port_hdl [lsort -dictionary [array names devicelist]] {
        set len [llength $devicelist($port_hdl)]
        for {set index 0} {$index < $len} {} {
            if {[string trim $devicelist($port_hdl)] == ""} {
                break
            }
            set device_each_port $devicelist($port_hdl)
            set device_index_scaling [llength $device_each_port]
            if {[catch {set update_obj [multi_dev_check_func_$multi_dev_check_func $class $device_each_port]} eMsg]} {
                #there is error while calculating the step, so the first device isn't hanlded with scalng mode
                set device_remove [lindex $device_each_port 0]
                set obj_remove [set sth::hlapiGen::$device_remove\_obj($class)]
                set hltapi_obj_cfg [concat $hltapi_obj_cfg $obj_remove]
                regsub $device_remove $devicelist($port_hdl) "" devicelist($port_hdl)
                set devicelist_obj($obj_remove) $device_remove
                incr index
            } else {
                # if the step is not the same value between the adjacent devices, we will save the minmum number of stardard devices.
                set remove_index [expr $device_index_scaling - 1]
                set devicelist_remove [lrange $device_each_port 0 $remove_index]
                set device_remove [lindex $devicelist_remove 0]
                set obj_remove [set sth::hlapiGen::$device_remove\_obj($class)]
                set hltapi_obj_cfg [concat $hltapi_obj_cfg $obj_remove]
                foreach each_device_remove $devicelist_remove {
                    regsub $each_device_remove $devicelist($port_hdl) "" devicelist($port_hdl)
                }
                set devicelist_obj($obj_remove) $devicelist_remove
                set count [llength $devicelist_remove]
                if {$count > 1} {
                    array set scaling_tmp "$device_remove\_$device_remove\_count $count"
                    foreach args [lsort [array names scaling_tmp]] {
                        set sub_arg [split $args _]
                        set new_arg [lindex $sub_arg 0]\_[lindex $sub_arg 1]\_attr(-[lindex $sub_arg 2])
                        set ::sth::hlapiGen::$new_arg $scaling_tmp($args)
                    }
                }
                set index [expr $index + $count]
            }
            
            
            array unset scaling_tmp
        }
    }
    
    return $hltapi_obj_cfg
}


proc ::sth::hlapiGen::update_streamblock_list {strblklist} {
    set strblk_for_rfc ""
    set strblklist_update ""
    set rfc_objlist "rfc2544backtobackframesconfig rfc2544framelossconfig rfc2544latencyconfig rfc2544throughputconfig"
    foreach rfc_obj $rfc_objlist {
        set rfc_hdllist [stc::get project1 -children-$rfc_obj]
        foreach rfc_hdl $rfc_hdllist {
            set strblk_profile [stc::get $rfc_hdl -children-rfc2544streamblockprofile]
            
            if {$strblk_profile == ""} {
                continue
            }
            set rfc_strblklist [stc::get $strblk_profile -streamblocklist]
            foreach rfc_strblk $rfc_strblklist {
                set tag ""
                set srcbinding_list [stc::get $rfc_strblk -SrcBinding-targets]
                set dstbinding_list [stc::get $rfc_strblk -DstBinding-targets]
                foreach srcbinding $srcbinding_list {
                    set src_hdl [stc::get $srcbinding -parent]
                    if {![info exists ::sth::hlapiGen::device_ret($src_hdl)]} {
                        set tag "raw"
                        set strblk_for_rfc [concat $strblk_for_rfc $rfc_strblk]
                        break
                    }
                }
                if {$tag == "raw"} {
                    continue
                }
                foreach dstbinding $dstbinding_list {
                    set dst_hdl [stc::get $dstbinding -parent]
                    if {![info exists ::sth::hlapiGen::device_ret($dst_hdl)]} {
                        set strblk_for_rfc [concat $strblk_for_rfc $rfc_strblk]
                        break
                    }
                }
            }
        }
    }
    
    foreach strblk $strblklist {
        if {[lsearch $strblk_for_rfc $strblk] < 0} {
            set strblklist_update [concat $strblklist_update $strblk]
        }
    }
    
    return $strblklist_update
}
