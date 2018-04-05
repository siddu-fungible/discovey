#package require yaml
#package require dict
#package require huddle

namespace eval ::sth::hlapiGen:: {
	variable script_fileD
	variable yaml_default
	array set yaml_default {}
}

proc ::sth::hlapiGen::process_table {formatedstr} {
	variable ::sth::hlapiGen::yaml_default
	if {$::sth::hlapiGen::default_yaml == 1} {
		if {[regexp {(\[sth|\[::sth)(.*?)(\-.*)\]} $formatedstr match match1 match2 match3]} {
			set mynamespace [string trim $match1 "\["]
			set mycmd [regsub -all {\\|\r|\n|\r\n|:|\s+} $match2 ""]
			if {[info exists ::sth::hlapiGen::yaml_default($mycmd)]} {
				set myhuddle $::sth::hlapiGen::yaml_default($mycmd)
				foreach key [huddle keys $myhuddle] {
					set value [huddle strip [huddle get $myhuddle $key]]
					if {[regexp -all "\\-" $formatedstr] > 1} {
						if {[regexp "\\-$key .*?$value\\\\\\\n.*?\\-" $formatedstr match_a]
							|| [regexp "\\-$key .*?$value.*?\\-" $formatedstr match_a]
							|| [regexp "\\-$key .*?$value\\\\\\\n.*?\\]" $formatedstr match_a]
							|| [regexp "\\-$key .*?$value.*?\\]" $formatedstr match_a]} {
							set index [string first $match_a $formatedstr]
							set formatedstr [string replace $formatedstr $index [expr $index+[string length $match_a]-2] ""]
						}
					}
				}
			} else {
				if {![catch {set yaml_huddle [huddle get $::sth::sthCore::DEFAULT_HUDDLE $mycmd]} err]
					&& [huddle llength $yaml_huddle] > 0} {
					foreach key [huddle keys $yaml_huddle] {
						set value [huddle strip [huddle get $yaml_huddle $key]]
						if {[catch {
							if {[regexp -all "\\-" $formatedstr] > 1} {
								if {[regexp "\\-$key .*?$value\\\\\\\n.*?\\-" $formatedstr match_a]
									|| [regexp "\\-$key .*?$value.*?\\-" $formatedstr match_a]
									|| [regexp "\\-$key .*?$value\\\\\\\n.*?\\]" $formatedstr match_a]
									|| [regexp "\\-$key .*?$value.*?\\]" $formatedstr match_a]} {
									set index [string first $match_a $formatedstr]
									set formatedstr [string replace $formatedstr $index [expr $index+[string length $match_a]-2] ""]
									if {[info exist my_yaml_huddle]} {
										huddle append my_yaml_huddle $key $value
									} else {
										set my_yaml_huddle [huddle create $key $value]
									}
								}
							}
							} myerr]} {
							set u $myerr
						}
					}
				} else {
					set namespaces [namespace children ::sth]
					foreach ns $namespaces {
						set tables [split [info vars $ns\::*Table]]
						foreach table $tables {
							if {[catch {
								if {[::sth::sthCore::IsCmdInTCLTable [set $table] $ns $mycmd]} {
									::sth::sthCore::InitTableFromTCLList [set $table]
									foreach key [array names $ns\::$mycmd\_default] {
										if {[regexp "\\-$key" $formatedstr] && [regexp -all "\\-" $formatedstr] > 1} {
											set value [set $ns\::$mycmd\_default($key)]
											if {$value != "_none_"} {
												if {[regexp "\\-$key .*?\\\\\\\n.*?\\-" $formatedstr match]
													|| [regexp "\\-$key .*?\\-" $formatedstr match]
													|| [regexp "\\-$key .*?\\\\\\\n.*?\\]" $formatedstr match]
													|| [regexp "\\-$key .*?\\]" $formatedstr match]} {			
													set index [string first $match $formatedstr]
													set formatedstr [string replace $formatedstr $index [expr $index+[string length $match]-2] ""]
	
													set v [regsub "\\-$key " $match ""]
													set v [string trim $v " \\\n\]-"]		
													if {[info exist my_yaml_huddle]} {
														huddle append my_yaml_huddle $key $v
													} else {
														set my_yaml_huddle [huddle create $key $v]
													}
												}
											}
										}
									}
									break
								}
							} err]} {
								set i $err
							}
						}
					}
				}			
				if {[info exist my_yaml_huddle]} {
					set ::sth::hlapiGen::yaml_default($mycmd) $my_yaml_huddle
					set my_yaml_huddle [huddle create $mycmd $my_yaml_huddle]
					set str_dict "set DEFAULT_YAML \"\n[::yaml::huddle2yaml $my_yaml_huddle]\"\n"
					set formatedstr $str_dict$formatedstr
				}
			}
		}
	}
	return $formatedstr
}

#the utility functions will be included in this file for hlapiGen
proc ::sth::hlapiGen::process_default {str} {
	variable ::sth::hlapiGen::yaml_default
	variable ::sth::sthCore::DEFAULT_HUDDLE
	set formatedstr $str
	if {$::sth::hlapiGen::default_yaml == 1} {
		if {[regexp {(\[sth|\[::sth)(.*?)(\-.*)\]} $str match match1 match2 match3]} {
			set man_args "mode port_handle"
			set mymatch1 [string trim $match1 "\["]
			set mymatch2 [regsub -all {\\|\r|\n|\r\n|:|\s+} $match2 ""]
			if {[info exists ::sth::hlapiGen::yaml_default($mymatch2)]} {
				set mymatch3 $::sth::hlapiGen::yaml_default($mymatch2)
			} else {
				if {[info exist ::sth::sthCore::DEFAULT_HUDDLE]} {
					if {![catch {set my_yaml_huddle [huddle get $::sth::sthCore::DEFAULT_HUDDLE $mymatch2]} err]} {
						if {[huddle llength $my_yaml_huddle] > 0} {
							foreach key [huddle keys $my_yaml_huddle] {
								set arg "-$key"
								set value [huddle strip [huddle get $my_yaml_huddle $key]]
								if {[catch {
									if {![regexp $key $man_args] && [regexp -all "\\-" $formatedstr] > 1} {
										if {[regexp "\\$arg.*?$value\\\\\\\n.*?\\-" $formatedstr match_a]
											|| [regexp "\\$arg.*?$value.*?\\-" $formatedstr match_a]
											|| [regexp "\\$arg.*?$value\\\\\\\n.*?\\]" $formatedstr match_a]
											|| [regexp "\\$arg.*?$value.*?\\]" $formatedstr match_a]} {
											set index [string first $match_a $formatedstr]
											set formatedstr [string replace $formatedstr $index [expr $index+[string length $match_a]-2] ""]
										}
									}
									} myerr]} {
									puts "$arg, $value"
								}
							}
						} else {
							set mymatch3 [split [regsub -all {\].*|\r|\n|\r\n|\t+|\s+|\\} $match3 " "] " "]
						}
					}
				} else {
					set mymatch3 [split [regsub -all {\].*|\r|\n|\r\n|\t+|\s+|\\} $match3 " "] " "]
				}
			}
			if {[info exists mymatch3]} {
				set num_args [llength $mymatch3]
				array set args_array {}
				for { set i 0 } { $i < $num_args } { incr i } {
					set arg [string trim [lindex $mymatch3 $i]]
					if {[regexp {^-} $arg]} {
						incr i
						set key [string trim $arg "-"]
						set value [string trim [lindex $mymatch3 $i]]
						if {![regexp $key $man_args] && [regexp -all "\\-" $formatedstr] > 1} {
							if {[regexp "\\$arg.*?$value\\\\\\\n.*?\\-" $formatedstr match_a]
								|| [regexp "\\$arg.*?$value.*?\\-" $formatedstr match_a]
								|| [regexp "\\$arg.*?$value\\\\\\\n.*?\\]" $formatedstr match_a]
								|| [regexp "\\$arg.*?$value.*?\\]" $formatedstr match_a]} {
								set index [string first $match_a $formatedstr]
								set formatedstr [string replace $formatedstr $index [expr $index+[string length $match_a]-2] ""]
								set args_array($key) $value
							}
						}
					}
				}
				
				set size [array size args_array]
				if {$size > 0} {
					set str_dict ""
					if {![info exists ::sth::hlapiGen::yaml_default($mymatch2)]} {
						set default_file_name [concat [file rootname $::sth::hlapiGen::script_file_name] "_default.yaml"]
						set yaml [open $default_file_name a+]
						puts $yaml $mymatch2
						set ::sth::hlapiGen::yaml_default($mymatch2) $mymatch3
						foreach key [array names args_array] {
							dict set my_yaml_dict $mymatch2 {$key $args_array($key)}
							dict set myarg_dict $key $args_array($key)
							puts $yaml "  $key\: $args_array($key)"
							
							if {[info exist my_yaml_huddle]} {
								huddle append my_yaml_huddle $key $args_array($key)
							} else {
								set my_yaml_huddle [huddle create $key $args_array($key)]
							}
						}
						close $yaml
						
						#dict set my_yaml_dict $mymatch2 $myarg_dict
						set my_yaml_huddle [huddle create $mymatch2 $my_yaml_huddle]
						set str_dict "set DEFAULT_YAML \"\n[::yaml::huddle2yaml $my_yaml_huddle]\"\n"
					}
					set formatedstr $str_dict$formatedstr
				}
			}
		}
	}
	return $formatedstr
}

#puts content to the file
proc ::sth::hlapiGen::puts_to_file {str} {

    set file_name $::sth::hlapiGen::script_file_name
    set ::sth::hlapiGen::script_fileD [open $file_name a+]
	 
    #Checking output_type: TCL, PERL, JT_PERL or PYTHON
    set type $::sth::hlapiGen::output_type

    if {[regexp -nocase tcl $type]} {
		#set formatstr $str
		set formatstr [formatTclScript $str]
		set formatstr [process_table $formatstr]
		puts $::sth::hlapiGen::script_fileD $formatstr
    } elseif {[regexp -nocase python $type]} {
		set formatstr $str
		set formatstr [formatPythonScript $str]
		puts $::sth::hlapiGen::script_fileD $formatstr
    } elseif {[regexp -nocase perl $type]} {
		set formatstr $str
		set formatstr [formatPerlScript $str]

		if {$formatstr != ""} {
			puts $::sth::hlapiGen::script_fileD $formatstr
		}
    } elseif {[regexp -nocase robot $type]} {
		set formatstr $str
		set formatstr [formatRobotScript $str]
		puts $::sth::hlapiGen::script_fileD $formatstr
    } elseif {[regexp -nocase $type $::sth::hlapiGen::v_plugins match]} {
    	set formatstr $str
    	set formatstr [formatScript_$match $str]
		if {$formatstr != ""} {
			puts $::sth::hlapiGen::script_fileD $formatstr
		}	
    } else {
		puts $::sth::hlapiGen::script_fileD $str
    }
	
	if {$::sth::hlapiGen::script_fileD != ""} {
		close $::sth::hlapiGen::script_fileD
	}
}

proc ::sth::hlapiGen::formatTclLine {line} {
    set pos1 [string first " " $line]
    set pos2 [string first "\t" $line]
    set pos 0
    if {$pos1 > 0 && $pos2 > 0} {
		set pos [expr {min($pos1, $pos2)}]
    } elseif {$pos1 < 0} {
		set pos $pos2
    } elseif {$pos2 < 0} {
		set pos $pos1
    }
    
    if {$pos > 0} {
		set param [string range $line 0 [expr $pos-1]]
		set value [string range $line $pos [string length $line]]
		set value [string trim $value]
		
		set result $param
		set num [expr 49-[string length $param]]
		for {set i 0} {$i < $num} {incr i} {
			append result " "
		}
		
		append result " $value"
		return $result
    }
    
    return $line
}

proc ::sth::hlapiGen::formatTclScript {str} {
    set mystr [string trim $str]
    
    set result ""
    set posflag 0
    set lines [split $mystr "\n"]
    set len [llength $lines]
    
    for {set i 0} {$i < $len} {incr i} {
		set line [lindex $lines $i]
		set myline [string trim $line]
		
		if {[regexp {^\}} $myline]} {
			incr posflag -1
		}
		
		for {set j 0} {$j < $posflag} {incr j} {
			append result "    "
		}
			
		if {[regexp "^-" $myline]} {
			append result "        [formatTclLine $myline]\n"
		} else {
			append result "$myline\n"
		}
				
		if {[regexp {\{$} $myline]} {
			incr posflag
		}
		
		if {[string compare "\}" $myline]} {
			if {[regexp {\}$} $myline]} {
			incr posflag -1
			}
		}
    }
    
    return $result
}

#puts content to GUI and console window
proc ::sth::hlapiGen::puts_msg {message} {
    if {[info exists ::text]} {
		$::text insert end "\n$message"
		update
	} else {
		puts $message
    }   
}

proc ::sth::hlapiGen::decimal2binary {i {bits {}}} {
    set res "";
    while {$i>0} {
        set res [expr {$i%2}]$res;
        set i [expr {$i/2}];   
    }
    if {$res==""} {
        set res 0;
    }
    if {$bits != {} } {
        append d [string repeat 0 $bits ] $res
        set res [string range $d [string length $res ] end ]
    }
    
    split $res ""
    return $res;
}
 
 
proc ::sth::hlapiGen::binToInt {bits {order lohi}} {
    # Convert a binary value into an integer.
    set result 0
    if {$order == "lohi"} {
        set bits [string trimleft $bits 0]
    }

    set i 0
    while {$bits != ""} {
        if {$order == "hilo"} {
            set bit [string index $bits 0]
            set bits [string replace $bits 0 0]
            set result [expr {$result + ($bit * int(pow(2,$i)))}]
        } else {
            set bit [string index $bits 0]
            set bits [string range $bits 1 end]
            set result [expr {($result << 1) + $bit}]
        }
        incr i
    }
    
    return $result
}


#in the hltapi table, for the choices type values, need to change the value of this attr in the xml to
#the value exactlly same with the one defined in the table
proc ::sth::hlapiGen::get_choice_value {arg type value name_space cmd_name} {

    if {[info exists $name_space$cmd_name\_$arg\_rvsmap]} {
        foreach const [array names $name_space$cmd_name\_$arg\_rvsmap] {
            if {[regexp -nocase "^$const$" $value]} {
                set value_new [set $name_space$cmd_name\_$arg\_rvsmap($const)]
                break
            }
        }
        if {![info exists value_new]} {
            set value_new $value
        }
    } else {
        set choices [regsub -nocase {CHOICES} $type ""]
        foreach choice $choices {
            if {[regexp -nocase "^$choice$" $value]} {
                set value_new $choice
                break
            }
            
        }
        #deal with the choice {0 1} and in the native API is true or false
        if {![info exists value_new]} {
            if {[regexp -nocase true $value]} {
                set value_new 1
            } elseif {[regexp -nocase false $value]} {
                set value_new 0
            } else {
                set value_new $value
            }
        }
    }
    return $value_new
}

#in the hlapiGen table when know one collum, can return the class name
proc ::sth::hlapiGen::getclassname { mynamespace cmd myswitch myswitchprop } {
    set tableName $mynamespace$cmd\_$myswitchprop
    foreach class [array names $tableName] {
        if {[regexp ^[set ${tableName}($class)]$ $myswitch]} {
            return $class
        }
    }
    return -code error "don't have the corresponding class name for $myswitch"
}

#convert ipv4 step into decimal number as hltapi use
proc ::sth::hlapiGen::ipaddr2dec { ipaddr } {
    regexp {([0-9]+).([0-9]+).([0-9]+).([0-9]+)} $ipaddr match byte1 byte2 byte3 byte4
    set dec [expr $byte1*255*255*255 + $byte2*255*255 + $byte3*255 + $byte4]
    return $dec
}

#get encap info from emulated_device
proc ::sth::hlapiGen::getencap { device } {
    set vlanList [stc::get $device -children-vlanif]
    set len [llength $vlanList]
    set encap "ethernet_ii"
    if {$len == 1} {
        set encap "ethernet_ii_vlan"    
    }
    if {$len == 2} {
        set encap "ethernet_ii_qinq"    
    }
    if {$len > 2} {
        set encap "ethernet_ii_mvlan"  
    }
    return $encap
}

#convert the int value to ipv4 address
proc ::sth::hlapiGen::intToIpv4Address {intValue} {
    set ipAddress ""
    #convert integer to IPv4
    binary scan [binary format I* $intValue] B32 step
    for {set x 0; set y 7} {$y < 32} {} {
        set oct [string range $step $x $y]
        binary scan [binary format B32 $oct] i ip
        lappend ipAddress $ip
        set x [expr {$x+8}]
        set y [expr {$y+8}]
    }
    set newIPAddr [join $ipAddress .]
    
    return $newIPAddr
}

#convert the int value to ipv6 address
proc ::sth::hlapiGen::intToIpv6Address {intValue mask} {
    set newBinIpAddress [::sth::hlapiGen::decimal2binary $intValue 128]
    set diff [expr 128 - $mask]
    for {set n 0} {$n < $diff} {incr n} {
        regsub {^\d} $newBinIpAddress "" newBinIpAddress
        append newBinIpAddress 0
    }
    
    for {set x 0; set y 15} {$y < 128} {} {
        set oct [string range $newBinIpAddress $x $y]
        binary scan [binary format B16 $oct] H* i
        lappend newIp $i
        set x [expr {$x+16}]
        set y [expr {$y+16}]
    }
    set newIPAddr [join $newIp :]
    regsub {^(0000:)+} $newIPAddr "::" newIPAddr
    return $newIPAddr

}

proc ::sth::hlapiGen::get_device_created {devices var_name hnd_type {child_class ""} } {
    
    #if don't know the hnd_type, then user can input the hnd_type as ""
    if {[regexp "^$" $hnd_type]} {
        #default is handle
        set device [lindex $devices 0]
        set hnd_type "handle"
		if {$child_class eq "" || [regexp -nocase dhcp $child_class]} {
			if {[info exists sth::hlapiGen::protocol_to_devices(dhcpv4serverconfig)]} {
				set dhcpv4_servers $sth::hlapiGen::protocol_to_devices(dhcpv4serverconfig)
				if {[lsearch $device $dhcpv4_servers] > -1} {
					set hnd_type "handle.dhcp_handle"
				}
				
			}
			if {[info exists sth::hlapiGen::protocol_to_devices(dhcpv6serverconfig)]} {
				set dhcpv6_servers $sth::hlapiGen::protocol_to_devices(dhcpv6serverconfig)
				if {[lsearch $device $dhcpv6_servers] > -1} {
					set hnd_type "handle.dhcpv6_handle"
				}
			}
		}
		
		if {$hnd_type eq "handle" && $child_class ne ""} {
			if {[regexp -nocase dhcpv6 $child_class]} {
				set hnd_type "dhcpv6_handle"
			} elseif {[regexp -nocase mldgroupmembership $child_class]} {
				set hnd_type "handles"
			}
		} 
    }
    set devices_new ""
    foreach device $devices {
		set devices_tmp ""
		if {$child_class ne "" && [regexp -nocase dhcp $child_class]} {		
			if {[info exists ::sth::hlapiGen::dhcpv4servertconfigured($device)]} {
				set devices_tmp "\[keylget $::sth::hlapiGen::dhcpv4servertconfigured($device) $hnd_type\]"
				set devices_new [concat $devices_new $devices_tmp]
			} elseif {[info exists ::sth::hlapiGen::dhcpv6servertconfigured($device)]} {
				set devices_tmp "\[keylget $::sth::hlapiGen::dhcpv6servertconfigured($device) $hnd_type\]"
				set devices_new [concat $devices_new $devices_tmp]
			}
		}
		
		if {$devices_tmp eq ""} {
			set device_var [lindex [set ::sth::hlapiGen::device_ret($device)] 0]
			set device_handle_indx [lindex [set ::sth::hlapiGen::device_ret($device)] 1]
			if {$device_handle_indx eq ""} {
				set device_handle_indx 0
			}
			set devices_new [concat $devices_new \[lindex \[keylget $device_var $hnd_type\] $device_handle_indx\]]
		}
    }
    if {[regexp {\] \[} $devices_new]} {
        set ouput_string "set $var_name \"$devices_new\" \n"
    } else {
        set ouput_string "set $var_name $devices_new \n"
    }
            
    return $ouput_string    
}

proc ::sth::hlapiGen::get_device_created_scaling_common {devices hnd_type} {
    variable device_ret
    array set devices_new ""
    array set devices_all ""
    set devices_update ""
    
    #get the device name and device index for current device handle list
    foreach device $devices {
        set device_var [lindex $device_ret($device) 0]
        set device_handle_index [lindex $device_ret($device) 1]
        if {[info exists devices_new($device_var)]} {
            set devices_new($device_var) [concat $devices_new($device_var) $device_handle_index]
        } else {
            array set devices_new "$device_var $device_handle_index"
        }
    }
    #get the device name and device index for all the device handle saved in device_ret
    foreach device [lsort [array name device_ret]] {
        if {!([regexp {^emulateddevice\d+} $device] || [regexp {^router\d+} $device] || [regexp {^host\d+} $device])} {
            continue
        }
        set device_var [lindex $device_ret($device) 0]
        set device_handle_index [lindex $device_ret($device) 1]
        if {[info exists devices_all($device_var)]} {
            set devices_all($device_var) [concat $devices_all($device_var) $device_handle_index]
        } else {
            array set devices_all "$device_var $device_handle_index"
        }
    }
    
    foreach devicevar [lsort [array name devices_new]] {
        set device_new_length [llength $devices_new($devicevar)]
        set device_all_length [llength $devices_all($devicevar)]
        if {$device_new_length != $device_all_length} {
            set first_index [lindex $devices_new($devicevar) 0]
            set last_index [lindex $devices_new($devicevar) [expr [llength $devices_new($devicevar)] - 1]]
            set devices_update [concat $devices_update \[lrange \[keylget $devicevar $hnd_type\] $first_index $last_index\]]
        } else {
            set devices_update [concat $devices_update \[keylget $devicevar $hnd_type\]]
        }
    }
    
    return $devices_update
}

proc ::sth::hlapiGen::get_device_created_scaling {devices var_name hnd_type} {
     
     set devices_update [get_device_created_scaling_common $devices $hnd_type]
    
    if {[regexp {\] \[} $devices_update]} {
        set ouput_string "set $var_name \"$devices_update\" \n"
    } else {
        set ouput_string "set $var_name $devices_update \n"
    }
    
    array unset devices_new
    array unset device_all
    
    return $ouput_string    
}

proc ::sth::hlapiGen::gen_status_info {hlt_ret func_name} {
    
    set status_check_str [gen_status_info_without_puts $hlt_ret $func_name]
    puts_to_file $status_check_str
}

proc ::sth::hlapiGen::gen_status_info_without_puts {hlt_ret func_name} {
    set status_check_str ""
    append status_check_str "set status \[keylget $hlt_ret status\]\n"
    append status_check_str "if \{\$status == 0\} \{\n"
    append status_check_str "puts \"run $func_name failed\"\n"
    append status_check_str "puts \$$hlt_ret\n"
    append status_check_str "\} else \{\n"
    append status_check_str "puts \"***** run $func_name successfully\"\n"
    append status_check_str "\}\n"
    return $status_check_str
}

proc ::sth::hlapiGen::gen_status_info_for_results {hlt_ret func_name} {
    set status_check_str ""
    append status_check_str "set status \[keylget $hlt_ret status\]\n"
    append status_check_str "if \{\$status == 0\} \{\n"
    append status_check_str "puts \"run $func_name failed\"\n"
    append status_check_str "puts \$$hlt_ret\n"
    append status_check_str "\} else \{\n"
    append status_check_str "puts \"***** run $func_name successfully, and results is:\"\n"
    append status_check_str "puts \"\$$hlt_ret\\n\"\n"
    append status_check_str "\}\n"
    puts_to_file $status_check_str
}


proc ::sth::hlapiGen::create_switch_priority_list { mynamespace cmd user_args switch_priority_list} {
    upvar $switch_priority_list switch_pri_list
    set switch_pri_list ""
    set priorityTableName $mynamespace$cmd\_priority
    foreach switch $user_args {
        #set switch [string range $switch 1 end ]
        if {[info exists ${priorityTableName}($switch)]} {
            lappend switch_pri_list "[set ${priorityTableName}($switch)] $switch"
        }
    }
    
    set switch_pri_list [lsort -integer -index 0 $switch_pri_list]
}

proc ::sth::hlapiGen::update_device_handle {device class first_time} {
    variable devicelist_obj
    
    if {$::sth::hlapiGen::scaling_test && $first_time} {
        set cnf_hdl [set ::sth::hlapiGen::$device\_obj($class)]
        if {[info exists devicelist_obj($cnf_hdl)]} {
            set device $devicelist_obj($cnf_hdl)
        }
    }
    
    return $device
}

proc ::sth::hlapiGen::formatline {key} {
    set ret ""
    set length [expr 49 - [string length $key]]
    for {set index 0} {$index < $length} {incr index} {
        append ret " "
    }
    return $ret
}