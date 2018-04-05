namespace eval ::sth::hlapiGen:: {
    variable variable_name_list ""
    variable formatStr_init ""
    variable formatStr_jt ""
    variable formatStr_temp ""
    variable hlp ""
}

proc ::sth::hlapiGen::formatPerlScript {str} { 

    variable hlp
    variable formatStr_init
    variable formatStr_jt
    variable formatStr_temp
    set formatStr ""
    set hlp_init 0
    set hlp_jt 0

    if {[regexp {\[sth::connect} $str]} {
        #puts "connect command generating...\n"
        if {$::sth::hlapiGen::output_type eq "jt_perl"} {
            set hlp_jt 1
            set mystr [string trim $str]
            set lines [split $mystr "\n\r"]
            set line [lindex $lines 1]
            set items [split $line " "]
            #check the same varaibles name, if same do not output my
            if {![varNameList "[lindex $items 1]"]} {
                append formatStr_jt "my "
            }
            append formatStr_jt "$[lindex $items 1] = \"[lindex $items 2]\";\n"
            append formatStr_jt "my \$rt = new SpirentHLTAPIforPerl(host => \$device);\n"
        }
        set formatStr [formatHltConnectCommand $str]
    } elseif {[regexp {\[sth::} $str]} {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommand $str]
    } elseif {[regexp {\[::sth::} $str] } {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommand $str]
        regsub -all "::sth" $formatStr "sth" formatStr
    } elseif {[regexp {foreach} $str] } {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommand $str]
        regsub -all "::sth" $formatStr "sth" formatStr
    } elseif {[regexp {set status \[keylget} $str]} {
        #puts "Status Check \n"
        set formatStr [formatStatusCheck $str]
    } elseif {[regexp {\[keylget} $str]} {
        #puts ">>> Device Handles: $str \n"
        #Split sth command and status
        set formatStr ""
        set ary [split $str ""]
        set len [string length $str]
        set statusStrIndex [string first "set " $str 4]
        for {set i 0} {$i < $len} {incr i} {
            append sthStr [lindex $ary $i]
            if {$i == [expr $statusStrIndex - 1]} {
                #Sth Command
                append formatStr [formatHandles $sthStr]
                set sthStr ""
                set statusStrIndex [string first "set " $str [expr $i + 3]]
            }
        }
        append formatStr [formatHandles $sthStr]
        set sthStr ""
    }  elseif {"package require SpirentHltApi \n" == $str} {
        if {$::sth::hlapiGen::output_type eq "jt_perl"} {
            set hlp_init 1
            set formatStr "use SpirentHLTAPIforPerl;\n"
        } else {
            set formatStr "use sth;\n"
        }
        append formatStr "use strict;\n"
        append formatStr "use warnings;\n"
        append formatStr "use Data::Dumper;\n\n"
        append formatStr "\n"
        append formatStr "my \$status = 0;\n"
    } else {
        if {[regsub "puts" $str "print" formatStr]} {
           if {![regexp {;$} $formatStr]} {
              set formatStr [string trimright $formatStr "\"\n\r"]
              append formatStr "\\n\";"
           }
        }
    }

    if {$::sth::hlapiGen::output_type eq "jt_perl"} {
        if {$hlp == ""} {
            if {$hlp_init} {
                append formatStr_init $formatStr
                set formatStr ""
            } elseif {$hlp_jt} {            
                append formatStr_temp $formatStr
                set formatStr $formatStr_init
                append formatStr $formatStr_jt
                append formatStr $formatStr_temp
                set hlp 1
            } else {
                append formatStr_temp $formatStr
                set formatStr ""
            }
        }
    }

    return $formatStr
}

proc ::sth::hlapiGen::formatHltConnectCommand {str} {

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
        #check the same varaibles name, if same do not output my
        if {![varNameList "[lindex $items 1]"]} {
            append result "my "
        }
        append result "$[lindex $items 1] = [lindex $items 2];\n"
    } else {
        set index [expr $index-1]
        set connect_flag 1
    }
    
    #2nd line device(chassis ip)
    if {$::sth::hlapiGen::output_type eq "perl" } {
        set line [lindex $lines [expr $index+1]]
        set items [split $line " "]
        #check the same varaibles name, if same do not output my
        if {![varNameList "[lindex $items 1]"]} {
            append result "my "
        }
        append result "$[lindex $items 1] = \"[lindex $items 2]\";\n"
    }
    #3rd line
    set line [lindex $lines [expr $index+2]]
    regsub -all "\"" $line "" line
    set items [split $line " "]
    
    #check the same varaibles name, if same do not output my
    if {![varNameList "[lindex $items 1]"]} {
        append result "my "
    }
    append result "$[lindex $items 1] = \""

    for { set i 2} { $i < [llength $items]} {incr i} {
        append result " [lindex $items $i]"
    }
    append result "\";\n"
    
    #check the same varaibles name, if same do not output my
    if {![varNameList "port_array"]} {
        append result "my "
    }
    append result "@port_array = \("

    for { set i 2} { $i < [llength $items]} {incr i} {
        append result " \"[lindex $items $i]\","
    }
    #append result "\);\n"
    set result [string trimright $result ","]
    append result ");\n"

    #check the same varaibles name, if same do not output my
    if {![varNameList "hport"]} {
        append result "my "
    }
    if {!$connect_flag} {
        append result "@hport = \"\"; \n"
    }

    #4th line
    set line [lindex $lines [expr $index+3]]    
    set items [split $line " "]

    set sub_name [string trim [lindex $items 2] "\[|\\"]
    set hash [lindex $items 1]
    if {!$connect_flag} {
        append result "my %$hash = $sub_name (\n"
    } else {
        append result "%$hash = $sub_name (\n"
    }
    
    set len [expr {[llength $items]-2}]
    for {set i 3} {$i < $len} {incr i 2} {
        set key [string trim [lindex $line $i] "-"]
        set value [lindex $items [expr {$i+1}]]
        if {[regexp {[\$]+} $value]} {
            append result "\t\t$key" [formatline $key] "=> \"$value\",\n"
        } else {
            append result "\t\t$key" [formatline $key] "=> '$value',\n"
        }
    }
    set value [string trim [lindex $items [expr {$len+1}]] "\]"]
    set key [string trim [lindex $items $len] "-"]
    if {[regexp {[\$]+} $value]} {
        append result "\t\t$key" [formatline $key] "=> \"$value\" \);\n\n"
    } else {
        append result "\t\t$key" [formatline $key] "=> '$value' \);\n\n"
    }

    append result "\$status = \$$hash{status};\n\n"
    append result "if (\$status == 1) \{\n"
    append result "\tforeach my \$port (\@port_array) \{\n"
    append result "\t\t\$i++;\n"
    append result "\t\t\$hport\[\$i\] = \$$hash\{port_handle\}\{\$device\}\{\$port\};\n"
    append result "\t\tprint \"\\n reserved ports \$port: \$hport\[\$i\]\\n\";\n"
    append result "\t\}\n"
    append result "\} else \{\n"
    append result "\tprint \"\\nFailed to retrieve port handle!\\n\";\n"
    append result "\tprint Dumper %$hash;\n"
    append result "\}\n\n"

    return $result
}

proc ::sth::hlapiGen::formatHltCommand {str} {
    set mystr [string trim $str]
    
    set result ""
    set posflag 0
    set lines [split $mystr "\n"]
    set len [llength $lines]
    set i 1
    set asymm_flag 0
    
    set line [lindex $lines 0]
    if {[regexp {foreach} $line]} {
        set line [split $line]
        append result "foreach \$[lindex $line 1] \(split\(\" \", [lindex $line 2]\)\) \{\n"
        set line [lindex $lines 1]
        set i 2
    }

    set sub_name [string trim [lindex $line 2] "\[|\\"]
    
    #check the same varaibles name, if same do not output my
    if {![varNameList "[lindex $line 1]"]} {
        append result "my "
    }
    
    #Special handling for emulation_gre_config
    if {[regexp {emulation_gre_config} $sub_name]} {
        append result "$[lindex $line 1] = $sub_name (\n"
    } else {
        append result "%[lindex $line 1] = $sub_name (\n"
    }
    for {set i} {$i < $len} {incr i} {
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
        #for last element


        if {[regexp {profile_name} $line]} {
           set accessConcGen [stc::get project1 -children-AccessConcentratorGenParams]
           if { $accessConcGen ne "" } {
               set asymm_flag 1
           }
        }
        
        if {[regexp {\]} $line] && $asymm_flag == 0 } {
            if {$key == "]" } {
                set result [string trimright $result ",\n"]
                append result ");\n"
            } else {
                if { $lineLen == 1} {
                    set key [string trim [lindex $line 0] "-|\]"]
                    append result "\t\t$key" [formatline $key] "=> ''\);\n"
                } else {
                    set value ""
                    for {set valIndex 1} {$valIndex < $lineLen} {incr valIndex} {
                        append value "[lindex $line $valIndex] "
                    }
                    set value [string trim $value " |\]"]
                    if {[regexp {[\$]+} $value]} {
                        append result "\t\t$key" [formatline $key] "=> \"$value\"\);\n"
                    } else {
                        append result "\t\t$key" [formatline $key] "=> '$value'\);\n"
                    }
                }
            }
        } else {
            set line [string trim $line "\\"]
            set valueLen [llength $line]
            if {$valueLen > 2} {
                set temp [split $line]
                set keyFlag 0
                set valueList ""
                set value ""
                foreach tmp $temp {
                    if {$keyFlag == 0} {
                        set keyFlag 1
                        continue
                    }
                    if {$tmp != ""} {
                        lappend valueList "$tmp"
                    }
                }
                #replace the port_handle value
                if {[regexp {^port_handle$} $key] ||
                    [regexp {^src_port$} $key]    ||
                    [regexp {^dst_port$} $key]    ||
                    [regexp {^dest_port_list$} $key]} {
                    foreach tmp $valueList {
                        set lag ""
                        if {![regexp -nocase "all" $tmp] } {
                            set port_handle $::sth::hlapiGen::handle_to_port($tmp)
                            set lag [stc::get $port_handle -children-lag]
                        }
                        if {$lag ne ""} {
                           append value "$tmp " 
                        } elseif {[regexp -all {[0-9]+} $tmp index]} {
                            append value "\$hport\[$index\] "
                        } else {
                            append value "\$tmp "
                        }
                    }
                } else {
                    foreach tmp $valueList {
                        append value "$tmp "
                    }
                }
            } else {
                set value [string trim [lindex $line 1] "\\"]
                if {[regexp -nocase "^mpls_labels" $key]||[regexp -nocase "^mpls_cos" $key]||[regexp -nocase "^mpls_ttl" $key]||[regexp -nocase "^mpls_bottom_stack_bit" $key]} {
                    if {[regexp -nocase "\{" $value]|| [regexp -nocase "\}" $value]} {
                        set  valueList ""       
                        append valueList "\{$value\} "
                        set value $valueList
                    }
                }
                #replace the port_handle value
                if {[regexp {^port_handle$} $key] ||
                    [regexp {^src_port$} $key]    ||
                    [regexp {^dst_port$} $key]    ||
                    [regexp {^dest_port_list$} $key]} {
                    set lag ""
                    if {![regexp -nocase "all" $value] && [info exists ::sth::hlapiGen::handle_to_port($value)]} {
                        set port_handle $::sth::hlapiGen::handle_to_port($value)
                        set lag [stc::get $port_handle -children-lag]
                    }
                    if {$lag ne ""} {
                        #append value "$value "
                    } elseif {[regexp -all {[0-9]+} $value index] && [info exists ::sth::hlapiGen::handle_to_port($value)]} {
                        set value "\$hport\[$index\]"
                    }
                } elseif {[regexp {^log_sync_message_interval$} $key]} {
                    set value "{\"$value\"}"
                } elseif {[regexp {^\$port(\d+)$} $value match index]} {
                    set value "\$hport\[$index\]"
                }
            }
            set value [string trimright $value " "]
            if {[regexp {[\$]+} $value]} {
                append result "\t\t$key" [formatline $key] "=> \"$value\",\n"
            } else {
                append result "\t\t$key" [formatline $key] "=> '$value',\n"
                set asymm_flag 0
            }
        }
    }

    return $result
}

proc ::sth::hlapiGen::formatStatusCheck {str} {
    set mystr [string trim $str]
    
    set result ""
    set posflag 0
    set lines [split $mystr "\n\r"]
    set len [llength $lines]
    
    #1st line
    set line [lindex $lines 0]
    set items [split $line " "]
    set key [string trim [lindex $items 4] "\]"]
    append result "$[lindex $items 1] = $[lindex $items 3]{$key};\n"

    #2nd line
    set line [lindex $lines 1]
    set items [split $line " "]
    set status [string trim [lindex $items 1] "\{"]
    append result "if ($status == 0) \{\n"

    #3rd line
    set line [lindex $lines 2]
    set line [string trim $line]
    regsub "puts" $line "print" line
    append line ";"
    regsub "\";" $line "\\n\";" line
    append result "\t$line\n"

    #4th line
    set line [lindex $lines 3]
    set items [split $line " "]
    set hash [string trim [lindex $items 1] "$"]
    append result "\tprint Dumper %$hash;\n"

    #5th line
    set line [lindex $lines 4]
    append result "$line\n"
    
    #6th line
    set line [lindex $lines 5]
    set line [string trim $line]
    regsub "puts" $line "print" line
    append line ";"
    regsub "\";" $line "\\n\";" line
    append result "\t$line\n"
    
    #7th line
    set line [lindex $lines 6]
    if {[regexp {\}} $line]} {
        append result "\}\n"
    } else {
        #For stats api's
        append result "\tprint Dumper %$hash;\n"
        append result "\}\n"
    }

    return $result
}

proc ::sth::hlapiGen::formatHandles {str} {
    set mystr [string trim $str]

    set result ""
    set result_var ""
    set result_arr_var ""
    #set posflag 0
    set lines [split $mystr "\n\r"]
    set len [llength $lines]
    set lrangeFlag 0
    set items [split $lines " "]
    set temp ""
    
    set i 0
    foreach temp $items {
        #puts ">>>>$temp \n"
        if {$i > 1} {
            append myTmpStr " $temp"
        }
        incr i 1
    }
    set myTmpStr [string trim $myTmpStr "\}"]
    
    #check the same varaibles name, if same do not output my
    if {![varNameList "[lindex $items 1]"]} {
        append result_var "my "
    }
    append result_var "\$[lindex $items 1] ="
    
    #processing string
    set arry [split $myTmpStr {}]
    
    set rB 0
    set lB 0
    set temp ""
    array set ary ""
    set len 0
    foreach item $arry {
       
        if {[regexp {\[} $item]} {
            incr rB 1
            #puts "-1-"
        } elseif {[regexp {\]} $item]} {
            incr lB 1
            #puts "-2-"
        } elseif {(($rB != 0) && ($lB != 0))&& ($rB == $lB) } {
            if {[regexp {[^\"]} $item]} {
                append temp $item
            }
            set ary($len) $temp
            set temp ""
            set rB 0
            set lB 0
            incr len 1
            #puts "-3-"
            #parray ary
        }
        
        #escaping quotes
        if {[regexp {[^\"]} $item]} {
            append temp $item
        }
    }
    
    if {(($rB != 0) && ($lB != 0))&& ($rB == $lB) } {
        if {[regexp {[^\"]} $item]} {
            append temp $item
        }
        set ary($len) $temp
        set temp ""
        set rB 0
        set lB 0
        incr len 1
        #puts "-Last element-"
    }
    
    list temp ""
    foreach {key value} [array get ary] {
        set value [string trim $value]
        set line [split $value]
        #removing unwanted chars([,],\)
        foreach tmp $line {
            lappend temp [string trim $tmp "\[|\]|\\"]
        }
        if {[regexp {lindex} $value]} {
            #check the same varaibles name, if same do not output my
            if {![varNameList "[lindex $temp 2]_arr"]} {
                append result "my "
            }
            append result "\@[lindex $temp 2]_arr = split( \" \", "
            append result "\$[lindex $temp 2]"
            append result_arr_var " $[lindex $temp 2]_arr\[[lindex $temp 4]\]"
            if {[regexp {\.} [lindex $temp 3]]} {
                set nestedKeys [split [lindex $temp 3] "\."]
                foreach tmpKey $nestedKeys { 
                    append result "\{$tmpKey\}"
                }
            } else {
                append result "\{[lindex $temp 3]\} "
            }
            append result ");\n"
        } elseif {[regexp {lrange} $value]} {
            set lrangeFlag 1
            #check the same varaibles name, if same do not output my
            if {![varNameList "[lindex $temp 2]_arr"]} {
                append result "my "
            }
            append result "\@[lindex $temp 2]_arr = split(\" \" ,"
            append result " \$[lindex $temp 2]\{[lindex $temp 3]\}";
            append result ");\n"
            append result_arr_var " \@[lindex $temp 2]_arr\[[lindex $temp 4]..[lindex $temp 5]\]"
        } elseif {[regexp {keylget} $value]} {
            if {[regexp {\.+} [lindex $temp 2]]} {
                set tmpKey [split [lindex $temp 2] "."]
                set keyList ""
                foreach tmpVar $tmpKey {
                    append hashKeyList "\{$tmpVar\}"
                }
                append result_arr_var " \$[lindex $temp 1]$hashKeyList"
            } else {
                append result_arr_var " \$[lindex $temp 1]\{[lindex $temp 2]\}"
            }
        }
        set line ""
        set temp ""
    }   
    
    if { $lrangeFlag } {
        append result "$result_var "
        foreach arrVar $result_arr_var {
            append result "join( \" \", $arrVar)"
            append result  " . \" \" ."
        }
        set result [string trimright $result " |\.|\""]
    } else {
        append result "$result_var \"$result_arr_var\""        
    }
    append result ";\n"

    return $result;
}

proc ::sth::hlapiGen::varNameList {str} {
    variable variable_name_list    
    set sameVarFlag 0

    #remove the unwanted chars(@, $) 
    regsub -all {[^a-zA-z0-9_ +]} $str "" str

    foreach var $variable_name_list {
        if {$var eq $str} {
            set sameVarFlag 1
        }
    }
    if {$sameVarFlag != 1} {
        #Store the variable names
        append variable_name_list " $str"
    }

    return $sameVarFlag
}