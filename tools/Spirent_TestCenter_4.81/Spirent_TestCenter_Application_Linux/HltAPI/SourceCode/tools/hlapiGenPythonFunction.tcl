namespace eval ::sth::hlapiGen:: {
    variable v_seqcmd_inprocess 0
}

proc ::sth::hlapiGen::formatPythonScript {str} { 
    variable v_seqcmd_inprocess
    set formatStr ""

    if {[regexp {\[sth::connect} $str]} {
        #puts "connect command generating...\n"
        set formatStr [formatHltConnectCommandPy $str]
    }  elseif {$v_seqcmd_inprocess || [regexp {^proc sth::sequencer_config} $str]} {
        set formatStr [formatSequencerCommandPy $str]
    } elseif {[regexp {\[sth::} $str] || [regexp {\[::sth::} $str]} {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommandPy $str]
    } elseif {[regexp {set status \[keylget} $str]} {
        #puts "Status Check \n"
        set formatStr [formatStatusCheckPy $str]
    } elseif {[regexp {\[keylget} $str]} {
        #puts ">>> Device Handles: $str \n"
        set formatStr [formatHandlesPy $str]
    }  elseif {[regexp {foreach} $str]} {
        #puts ">>> scaling foreach"
        set formatStr [formatHltCommandPy $str]
    }  elseif {"\}\n" == $str} {
        set formatStr ""
    }  elseif {"package require SpirentHltApi \n" == $str} {
        set formatStr "##############################################################\n"
        append formatStr "#Loading HLTAPI for Python\n"
        append formatStr "##############################################################\n"
        append formatStr "from __future__ import print_function\n"
        append formatStr "import sth"
    } else {
        regsub "puts " $str "print(" formatStr
        if {![string match -nocase $str $formatStr]} {
            append formatStr ")"
        }
    }
    
    #Namespace name can be changed here
    regsub -all "sth::" $formatStr "sth." formatStr
    regsub -all "::sth" $formatStr "sth" formatStr
    
    return $formatStr
}

proc ::sth::hlapiGen::formatSequencerCommandPy {str} {
    variable v_seqcmd_inprocess
    set v_seqcmd_inprocess 1
    if {[regexp {^proc sth::sequencer_config} $str]} {
        if {[regexp {catch \{(.*)\} result} $str match extract]} {
            set seq_str [regsub -all {\n} $extract "\n\t\t"]
            set seq_str [string trim $seq_str]
            set seq_str "\t\t$seq_str"
            set my_python "def sequencer_config(**arg):\n"
            append my_python "\ttcl_str = '''\n"
            append my_python "$seq_str'''\n"
            append my_python "\treturn sth._hltpy_sequencer_config(tcl_str, **arg)\n"
            
            return $my_python
        }
    } elseif {[regexp {\[sth::sequencer_config} $str]} {
        set formatStr [formatHltCommandPy $str]
        return $formatStr
    } elseif {[regexp {\[sth::} $str] || [regexp {\[::sth::} $str]} {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommandPy $str]
        return $formatStr
    } elseif {[regexp {set seq_status \[keylget} $str]} {
        #puts "Status Check \n"
        set formatStr [formatStatusCheckPy $str]
        set v_seqcmd_inprocess 0
        return $formatStr
    } elseif {[regexp {^#} $str]} {
        return $str
    } else {
        set formatStr ""
        append formatStr "if (cfg_ret1 == \"\"):\n"
        append formatStr "\tprint(\"***** run sequencer_config successfully\")\n"
        append formatStr "else:\n"
        append formatStr "\tprint(\"<error>run sequencer_config failed\")\n"
        append formatStr "\tprint(cfg_ret1)\n"
        return $formatStr
    }
}

proc ::sth::hlapiGen::formatHltConnectCommandPy {str} {
    set mystr [string trim $str]

    set result ""
    set posflag 0
    set lines [split $mystr "\n\r"]
    set len [llength $lines]
    set connect_flag 0
    #1st line
    set index 0
    set line [lindex $lines 0]
    if {[regexp -nocase "set i 0" $line]} {
        set items [split $line " "]
        append result "[lindex $items 1] = [lindex $items 2]\n"
    } else {
        set index [expr $index-1]
        set connect_flag 1
    }
    
    #2nd line device(chassis ip)
    set line [lindex $lines [expr $index+1]]
    set items [split $line " "]
    append result "[lindex $items 1] = \"[lindex $items 2]\"\n"
    
    #3rd line port_list
    set line [lindex $lines [expr $index+2]]
    regsub -all "\"" $line "" line
    set items [split $line " "]
    append result "[lindex $items 1] = \["
    for { set i 2} { $i < [llength $items]} {incr i} {
        append result "'[lindex $items $i]',"
    }
    set result [string trimright $result ","]
    append result "\]\n"
    if {!$connect_flag} {
        append result "port_handle = \[\]\n"
    }

    #4th line
    set line [lindex $lines [expr $index+3]]    
    set items [split $line " "]

    set sub_name [string trim [lindex $items 2] "\[|\\"]
    set hash [lindex $items 1]
    append result "$hash = $sub_name (\n"
    set len [expr {[llength $items]-2}]
    for {set i 3} {$i < $len} {incr i 2} {
        set key [string trim [lindex $line $i] "-"]
        set value [lindex $items [expr {$i+1}]]
        set value [string trimleft $value "\$"]
        if {[regexp {[\$]+} $value]} {
            append result "\t\t$key" [formatline $key] "= $value,\n"
        } else {
            append result "\t\t$key" [formatline $key] "= $value,\n"
        }
    }
    set value [string trim [lindex $items [expr {$len+1}]] "\]"]
    set value [string trimleft $value "\$"]
    set key [string trim [lindex $items $len] "-"]
    if {[regexp {[\$]+} $value]} {
        append result "\t\t$key" [formatline $key] "= $value \)\n\n"
    } else {
        append result "\t\t$key" [formatline $key] "= $value \)\n\n"
    }

    append result "status = $hash\['status'\]\n\n"
    append result "if (status == '1') :\n"
    append result "\tfor port in port_list \:\n"
    append result "\t\tport_handle.append($hash\['port_handle'\]\[\device\]\[\port\])\n"
    append result "\t\tprint(\"\\n reserved ports\",port,\":\", port_handle\[i\])\n"
    append result "\t\ti += 1\n"
    
    append result "else :\n"
    append result "\tprint(\"\\nFailed to retrieve port handle!\\n\")\n"
    append result "\tprint(port_handle)\n"

    return $result
}

proc ::sth::hlapiGen::formatHltCommandPy {str} {
    set mystr [string trim $str]
     
    set result ""
    set posflag 0
    set format ""
    set lineindex 1
    set lines [split $mystr "\n"]
    set len [llength $lines]
    set line [lindex $lines 0]
    if {[regexp {foreach} $line]} {
        set ::sth::hlapiGen::scaling_format "\t\t"
        set format $::sth::hlapiGen::scaling_format
        set lineindex 2
        regsub -all "foreach" $line "for" line
        regsub -all "\\\$" $line "in " line
        regsub -all "\{" $line ":" line
        append result "$line\n"
        set device_name [lindex $line 1]
        if $::sth::hlapiGen::scaling_lrange {
            append result "\tfor device_handle in $device_name:\n"
            set ::sth::hlapiGen::scaling_lrange 0
        } else {
            append result "\tfor device_handle in $device_name.split() :\n"
        }
        set line [lindex $lines 1]
    }
    
    set sub_name [string trim [lindex $line 2] "\[|\\"]
    append result $format "[lindex $line 1] = $sub_name (\n"
        
    for {set i $lineindex} {$i < $len} {incr i} {
        set line [lindex $lines $i]
        set line [string trim $line]
        regsub -all "\"" $line "" line
        if {[regexp -nocase "^-custom_load_list" $line] || [regexp -nocase "^-mpls_labels" $line] ||[regexp -nocase "^-mpls_cos" $line]|| [regexp -nocase "^-mpls_ttl" $line] ||[regexp -nocase "^-mpls_bottom_stack_bit" $line]} {
           
           set line [string trim $line "\\"]
        } else {
            regsub -all "\{" $line "" line
            regsub -all "\}" $line "" line
        }
       
        #set line [string trim $line "\""]
        set lineLen [llength $line]
        set key [string trim [lindex $line 0] "-|\\"]
        #need special handle for python keyword exec
        if {$key == "exec"} {
            set key "python_$key"
        }
        #for lash element
        if {[regexp {\]} $line]} {
            if {$key == "]" } {
                continue
            }
        }
        set accessconcGen [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-AccessConcentratorGenParams]
        if {$accessconcGen ne "" && [regexp {profile_name} $line]} {
        set line [regsub -all {\[} $line "\\\\\["]
        set line [regsub -all {\\]} $line "\\\\\\\] \]"]
       }
        
        set key   [string trimright $key "\]"]
        set line  [string trim $line "\\"]
        set line  [string trim $line "\]"]
        set line [string trimright $line " "]
        set valuelist "\["
            
        for {set index 1} {$index < [llength $line]} {incr index} {
            set value0 [lindex $line $index]
            
            set value [string trimleft $value0 "\$"]
            if {[regexp {port_handle} $key]} {
                set lag ""
                if {![regexp -nocase "all" $value0] } {
                    set port_handle $::sth::hlapiGen::handle_to_port($value0)
                    set lag [stc::get $port_handle -children-lag]
                }
                if {$lag ne ""} {
                } elseif {[regexp -all {[0-9]+} $value portindex]} {
                    set value "port_handle\[[expr $portindex - 1]\]"
                } else {
                    set value "'$value'"    
                }
                append valuelist "$value,"
            } elseif {[regexp {handle} $key] || [regexp {stream_id} $key]\
                || [regexp {multicast_streamblock} $key]|| [regexp {lldp_optional_tlvs} $key]\
                || [regexp {dcbx_tlvs} $key] || [regexp {affiliated_router_target} $key]\
                || [regexp {tunnel_bottom_label} $key] || [regexp {egress_resv_custom_object_list} $key]\
                || [regexp {tunnel_next_label} $key] || [regexp {ingress_path_custom_object_list} $key]\
				|| [regexp {ingress_path_tear_custom_object_list} $key] || [regexp {egress_resv_tear_custom_object_list} $key]\
                || [regexp {unicast_streamblock} $key]} {
                if {[regexp {\$} $line]} {
                    append valuelist "$value,"
                } else {
                    append valuelist "'$value',"
                }
            } else {
                append valuelist "'$value',"
            }
        }
        
        set valuelist [string trimright $valuelist ","]
        append valuelist "\]"
        set b_var 0
        if {[llength $line] <= 2} {
            set value0 [lindex $line 1]
            if {[regexp {^\$} $value0]} {
                set b_var 1
            }
            set value [string trimleft $value0 "\$"]
            if {[regexp {port_handle} $key]} {
                set lag ""
                if {![regexp -nocase "all" $value0] } {
                    set port_handle $::sth::hlapiGen::handle_to_port($value0)
                    set lag [stc::get $port_handle -children-lag]
                }
                if {$lag ne ""} {
                      
                } elseif {[regexp -all {[0-9]+} $value portindex]} {
                    set value "port_handle\[[expr $portindex - 1]\]"
                } else {
                    set value "'$value'"    
                }
            } elseif {[regexp {^\$port(\d+)$} $value0 match index]} {
                set value "\port_handle\[[expr $index - 1]\]"
            }
            if {[regexp -nocase "^mpls_labels" $key]||[regexp -nocase "^mpls_cos" $key]||[regexp -nocase "^mpls_ttl" $key]||[regexp -nocase "^mpls_bottom_stack_bit" $key]} {
                 if {[regexp -nocase "\{" $value]|| [regexp -nocase "\}" $value]} {
                        set valuelist ""
                        append valuelist "\{$value0\}"
                    } else {
                        set valuelist ""
                        set valuelist $value0
                    }
                
               
            } else {
                set valuelist $value
            }
        }
        #replace the port_handle value
        if {[regexp {port_handle} $key]} {
            append result $format "\t\t$key" [formatline $key] "= $valuelist,\n"
        } elseif {[regexp {handle} $key] || [regexp {stream_id} $key]\
            || [regexp {multicast_streamblock} $key] || [regexp {lldp_optional_tlvs} $key]\
            || [regexp {dcbx_tlvs} $key] || [regexp {affiliated_router_target} $key]\
            || [regexp {tunnel_bottom_label} $key] || [regexp {tunnel_next_label} $key]\
            || [regexp {unicast_streamblock} $key]} {
            if {$format != ""} {
                set valuelist "device_handle"
            }
            if {[regexp {\$} $line]} {
                append result $format "\t\t$key" [formatline $key] "= $valuelist,\n"
            } else {
                append result $format "\t\t$key" [formatline $key] "= '$valuelist',\n"
            }
        } else {
            if {$key == "log_sync_message_interval"} {
                append result $format "\t\t$key" [formatline $key] "= '{\"$valuelist\"}',\n"
            } else {
                if {[llength $line] <= 2 && $b_var == 0} {
                    append result $format "\t\t$key" [formatline $key] "= '$valuelist',\n"
                } else {
                    append result $format "\t\t$key" [formatline $key] "= $valuelist,\n"
                }
            }
        }
    }
    set result [string trimright $result "\n"]
    
    if {[regexp "sth::sequencer_config" $str]} {
        set items [split $str " "]
        set i 0
        foreach item $items {
            incr i
            if {$i > 3} {
                set item_py_key [string trim $item "$\]"]
                set item_py_value $item_py_key
                if {[regexp {^port(\d+)} $item_py_key match num]} {
                    set item_py_value [regsub {^port(\d+)} $item_py_key "port_handle\[[expr $num - 1]\]"]
                }
                set py_str "py_$item_py_key\=$item_py_value, "
                append result $py_str
            }
        }
        regsub "sth::" $result "" result
    }
    
    set result [string trimright $result ", "]
    append result "\);\n"
    return $result
}

proc ::sth::hlapiGen::formatStatusCheckPy {str} {
    set mystr [string trim $str]
    
    set result ""
    set posflag 0
    set format $::sth::hlapiGen::scaling_format
    set ::sth::hlapiGen::scaling_format ""
    set lines [split $mystr "\n\r"]
    set len [llength $lines]
    
    #1st line
    set line [lindex $lines 0]
    set items [split $line " "]
    set key [string trim [lindex $items 4] "\]"]
    append result $format "[lindex $items 1] = [lindex $items 3]\['$key'\]\n"

    #2nd line
    set line [lindex $lines 1]
    set items [split $line " "]
    set status [string trim [lindex $items 1] "\{"]
    append result $format "if (status == '0') :\n"

    #3rd line
    set line [lindex $lines 2]
    set line [string trim $line]
    regsub "puts " $line "print(" line 
    append result $format "\t$line)\n"

    #4th line
    set line [lindex $lines 3]
    set items [split $line " "]
    set hash [string trim [lindex $items 1] "$"]
    append result $format "\tprint($hash)\n"

    #5th line
    set line [lindex $lines 4]
    append result $format "else:\n"
    
    #6th line
    set line [lindex $lines 5]
    set line [string trim $line]
    if {[regexp {set seq_status \[keylget} $str]} {
        set items [split $line " "]
        set key [string trim [lindex $items 4] "\]"]
        append result $format "\t[lindex $items 1] = [lindex $items 3]\['$key'\]\n"
        set hash $key
    } else {
        regsub "puts " $line "print(" line 
        append result $format "\t$line)\n"
    }
    
    #7th line
    set line [lindex $lines 6]
    if {[regexp {\}} $line]} {
        
    } else {
        #For stats api's
        append result $format "\tprint($hash)\n"
    }

    return $result
}

proc ::sth::hlapiGen::formatHandlesPy {str} {
    set mystr [string trim $str]

    set result ""
    set posflag 0
    set lines [split $mystr "\n\r"]
    set len [llength $lines]
    for {set i 0} {$i < $len} {incr i} {
        set line [lindex $lines $i]
        set line [string trim $line]
        regsub -all {[]|[|"|"]}  $line "" line
        set words [split $line " "]
        if {[llength $words] <= 7} {
            set keygetindex [lsearch $words "keylget"]
            if {[lindex $words 1] eq "device_list_scaling"} {
                if {[regexp -nocase "lindex" $line]} {
                    set temp [lindex $words [expr $keygetindex + 2]]
                        if {[regexp -nocase "\\." $temp]} {
                            regsub -all "\\." $temp "'\]\['" temp
                            set line "[lindex $words 1] = \[[lindex $words [expr $keygetindex + 1]]\['[set temp]'\].split()\[[lindex $words [expr [llength $words] - 1]]\]\]"
                        } else {
                            set line "[lindex $words 1] = \[[lindex $words [expr $keygetindex + 1]]\['[lindex $words [expr $keygetindex + 2]]'\].split()\[[lindex $words [expr [llength $words] - 1]]\]\]"
                        }
                    } else {
                        set temp [lindex $words [expr $keygetindex + 2]]
                        if {[regexp -nocase "\\." $temp]} {
                            regsub -all "\\." $temp "'\]\['" temp
                            set line "[lindex $words 1] = \[[lindex $words [expr $keygetindex + 1]]\['[set temp]'\]\]"
                        } else {
                            set line "[lindex $words 1] = \[[lindex $words [expr $keygetindex + 1]]\['[lindex $words [expr $keygetindex + 2]]'\]\]"
                        }
                    }                
                } else {
                    if {[regexp -nocase "lindex" $line]} {
                        set temp [lindex $words [expr $keygetindex + 2]]
                        if {[regexp -nocase "\\." $temp]} {
                            regsub -all "\\." $temp "'\]\['" temp
                            set line "[lindex $words 1] = [lindex $words [expr $keygetindex + 1]]\['[set temp]'\].split()\[[lindex $words [expr [llength $words] - 1]]\]"
                        } else {
                            set line "[lindex $words 1] = [lindex $words [expr $keygetindex + 1]]\['[lindex $words [expr $keygetindex + 2]]'\].split()\[[lindex $words [expr [llength $words] - 1]]\]"
                        }
                    } else {
                        if {[lindex $words 1] eq "profileHandles"} {
                           set temp [lindex $words [expr $keygetindex + 2]]
                           
                             set line "[lindex $words 1] = [lindex $words [expr $keygetindex + 1]]\['[set temp]'\].split()"
                          
                        } else  {



                    set temp [lindex $words [expr $keygetindex + 2]]
                    if {[regexp -nocase "\\." $temp]} {
                        regsub -all "\\." $temp "'\]\['" temp
                        set line "[lindex $words 1] = [lindex $words [expr $keygetindex + 1]]\['[set temp]'\]"
                    } else {
                        set line "[lindex $words 1] = [lindex $words [expr $keygetindex + 1]]\['[lindex $words [expr $keygetindex + 2]]'\]"
                    }
                }
              }
            }
        } else {
            
            if {[regexp -nocase "lindex" $line]} {
                set line "[lindex $words 1] = \["
                for {set index 4} {$index < [llength $words]} {incr index 5} {
                    append line "[lindex $words $index]\['[lindex $words [expr $index + 1]]'\].split()\[[lindex $words [expr $index + 2]]\],"
                }
            } elseif {[regexp -nocase "lrange" $line]} {
                #set flag for lrange
                set ::sth::hlapiGen::scaling_lrange 1
                set line "[lindex $words 1] = \["
                for {set index 4} {$index < [llength $words]} {incr index 6} {
                    append line "[lindex $words $index]\['[lindex $words [expr $index + 1]]'\].split()\[[lindex $words [expr $index + 2]]:[expr 1 + [lindex $words [expr $index + 3]]]\],"
                }
            } else {
                set line "[lindex $words 1] = \["
                for {set index 3} {$index < [llength $words]} {incr index 3} {
                    append line "[lindex $words $index]\['[lindex $words [expr $index + 1]]'\],"
                }
            }
            set line [string trimright $line ","]
            append line "\]"
        }
        append result "$line\n"
    }
    return $result;
}
