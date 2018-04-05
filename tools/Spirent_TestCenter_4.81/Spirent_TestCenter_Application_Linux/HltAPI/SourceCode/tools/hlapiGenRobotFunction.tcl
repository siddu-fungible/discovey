namespace eval ::sth::hlapiGen:: {
    variable v_seqcmd_inprocess 0
    #variable testCaseStart 0
}

proc ::sth::hlapiGen::formatRobotScript {str} {
    variable v_seqcmd_inprocess
    variable testCaseStart

    if {[regexp {\[sth::connect} $str]} {
        #puts "connect command generating...\n"
        set formatStr [formatHltConnectCommandRobot $str]
    }  elseif {$v_seqcmd_inprocess || [regexp {^proc sth::sequencer_config} $str]} {
        set formatStr [formatSequencerCommandRobot $str]
    } elseif {[regexp {\[sth::} $str] || [regexp {\[::sth::} $str]} {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommandRobot $str]
    } elseif {[regexp {set status \[keylget} $str]} {
        #puts "Status Check \n"
        set formatStr [formatStatusCheckRobot $str]
    } elseif {[regexp {\[keylget} $str]} {
        #puts ">>> Device Handles: $str \n"
        set formatStr [formatHandlesRobot $str]
    }  elseif {[regexp {foreach} $str]} {
        #puts ">>> scaling foreach"
        set formatStr [formatHltCommandRobot $str]
    }  elseif {"\}\n" == $str} {
        set formatStr ""
    }  elseif {"package require SpirentHltApi \n" == $str} {
        set formatStr "*** Settings ***\n"
        append formatStr "Documentation  xxx\n"
        append formatStr "Library  BuiltIn\n"
        append formatStr "Library  Collections\n"
        append formatStr "Library  sth\n"
        append formatStr "*** Variables ***\n"
        append formatStr "\n"
        append formatStr "*** Keywords ***\n"
        append formatStr "Get Port Handle\n"
        append formatStr "    \[Arguments\]  \$\{dict\}  \$\{chassis\}  @\{port_list\}\n"
        append formatStr "    \$\{port\} =  Set Variable  \$\{EMPTY\}\n"
        append formatStr "    :FOR  \$\{port\}  IN  @\{port_list\}\n"
        append formatStr "    \\  $\{Rstatus\} =  Get From Dictionary  \$\{dict\}  port_handle\n"
        append formatStr "    \\  $\{Rstatus\} =  Get From Dictionary  \$\{Rstatus\}  \$\{chassis\}\n"
        append formatStr "    \\  $\{Rstatus\} =  Get From Dictionary  \$\{Rstatus\}  \$\{port\}\n"
        append formatStr "    \\  Set Test Variable    \$\{port\$\{port_index\}\}    \$\{Rstatus\}\n"
        append formatStr "    \\  Log To Console  \\nreserved ports: \$\{chassis\} \$\{port\} \$\{Rstatus\}\n"
        append formatStr "    \\  \$\{port_index\}    Evaluate    \$\{port_index\}+1\n"
        append formatStr "    \\  Set Test Variable  \$\{port_index\}  \$\{port_index\}\n"
        #append formatStr "    Return From Keyword  \$\{Rstatus\}\n"
        append formatStr "*** Test Cases ***\n"
        append formatStr "Test case name\n"
    } elseif {[regexp {set\s+(.*)\s+"(.*)"} $str -> sname svalue]} {
        append formatStr "\$\{$sname\} =  Set Variable  $svalue"
    } else {
        regsub "puts " $str "Log To Console  \\n" formatStr
        regsub -all "\"" $formatStr "" formatStr
        #customer asked not removing underscores in API names
        #regsub -all "_" $formatStr " " formatStr
    }

    #Namespace name can be changed here
    regsub -all "::sth::" $formatStr "" formatStr
    regsub -all "sth::" $formatStr "" formatStr
    regsub -all "::sth" $formatStr "" formatStr
    #inside the test case, before evry sentence,there will be 4 spaces.
    if {$testCaseStart} {
        set lines [split $formatStr "\n\r"]
        set result ""
        foreach line $lines {
            append result "    $line\n"
        }
        if {[info exists ::sth::hlapiGen::scaling_format] && $::sth::hlapiGen::scaling_format != ""} {
            set result [string trimright $result "\n"]
        }
        return $result
    }
    if {"package require SpirentHltApi \n" == $str} {
        set testCaseStart 1
    }
    return $formatStr
}

proc ::sth::hlapiGen::formatSequencerCommandRobot {str} {
    variable v_seqcmd_inprocess
    set v_seqcmd_inprocess 1
    if {[regexp {^proc sth::sequencer_config} $str]} {
        set my_robot "\$\{sequencer_config\} =  Catenate  SEPARATOR=\\n"
        if {[regexp {catch \{(.*)\} result} $str match extract]} {
            set seq_str [string trim $extract]
            set seq_str [regsub -all {\n} $seq_str "\n...  "]
            set seq_str "\n...  $seq_str"
            append my_robot $seq_str
            return $my_robot
        }
    } elseif {[regexp {\[sth::sequencer_config} $str]} {
        set formatStr [formatHltCommandRobot $str]
        return $formatStr
    } elseif {[regexp {\[sth::} $str] || [regexp {\[::sth::} $str]} {
        #puts "HLP command generating...\n"
        set formatStr [formatHltCommandRobot $str]
        return $formatStr
    } elseif {[regexp {set seq_status \[keylget} $str]} {
        #puts "Status Check \n"
        set formatStr [formatStatusCheckRobot $str]
        set v_seqcmd_inprocess 0
        return $formatStr
    } elseif {[regexp {^#} $str]} {
        return $str
    } else {
        set formatStr ""
        append formatStr "Run Keyword If  \"\$\{cfg_ret1\}\" != \"\"  Log To Console  \\nrun sequencer_config failed\\n\$\{cfg_ret1\}\n"
        append formatStr "...  ELSE  Log To Console  \\n***** run sequencer_config successfully"
        return $formatStr
    }
}

proc ::sth::hlapiGen::formatHltConnectCommandRobot {str} {
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
        append result "Set Test Variable  \$\{port_index\}  [expr [lindex $items 2]+1]\n"
    } else {
        set index [expr $index-1]
        set connect_flag 1
    }

    #2nd line device(chassis ip)
    set line [lindex $lines [expr $index+1]]
    set items [split $line " "]
    set deviceVar [lindex $items 1]
    append result "\$\{[lindex $items 1]\} =  Set Variable  [lindex $items 2]\n"

    #3rd line port_list
    set line [lindex $lines [expr $index+2]]
    regsub -all "\"" $line "" line
    set items [split $line " "]
    append result "@\{[lindex $items 1]\} =  Create List  "
    set port_list ""
    for { set i 2} { $i < [llength $items]} {incr i} {
        append port_list "[lindex $items $i]  "
    }
    set port_list [string trimright $port_list]
    append result $port_list
    append result "\n"
    #leave it here, when the connect_flag is 0, need to add the support
    #if {!$connect_flag} {
    #    append result "port_handle = \[\]\n"
    #}

    #4th line
    set line [lindex $lines [expr $index+3]]
    set items [split $line " "]

    set sub_name [string trim [lindex $items 2] "\[|\\"]
    set hash [lindex $items 1]
    append result "\$\{$hash\} =  $sub_name"
    set len [expr {[llength $items]-2}]
    for {set i 3} {$i < $len} {incr i 2} {
        set key [string trim [lindex $line $i] "-"]
        set value [lindex $items [expr {$i+1}]]
        if {[regexp {[\$]+} $value]} {
            set value [string trimleft $value "\$"]
            append result "  $key=\$\{$value\}"
        } else {
            append result "  $key=$value"
        }
    }
    set value [string trim [lindex $items [expr {$len+1}]] "\]"]
    set value [string trimleft $value "\$"]
    set key [string trim [lindex $items $len] "-"]
    append result "  $key=$value\n"
    append result "\$\{status\} =  Get From Dictionary  \$\{intStatus\}  status\n"
    append result "Run Keyword If  \$\{status\} == 1  Get Port Handle  \$\{intStatus\}  \$\{device\}  @\{port_list\}\n"
    append result "...  ELSE  log to console  \\n<error> Failed to retrieve port handle! Error message: \$\{intStatus\}\n"
    return $result
}

proc ::sth::hlapiGen::formatHltCommandRobot {str} {
    set mystr [string trim $str]

    set result ""
    set posflag 0
    set format ""
    set lineindex 1
    set lines [split $mystr "\n"]
    set len [llength $lines]
    set line [lindex $lines 0]

    if {[regexp {foreach} $line]} {
        set ::sth::hlapiGen::scaling_format "\\  "
        #set format $::sth::hlapiGen::scaling_format
        set lineindex 2
        regsub -all "\\\$" $line "" line
        regsub -all "\{" $line "" line
        set device_name [lindex $line 1]
        set iter_list [lindex $line 2]
        if $::sth::hlapiGen::scaling_lrange {
            set ::sth::hlapiGen::scaling_lrange 0
        } else {
            append result "\@\{$iter_list\} =  Convert To List  \$\{$iter_list.split()\}\n"
        }
        append result ":FOR  \$\{$device_name\}  IN  \@\{$iter_list\}\n\\  "
        set line [lindex $lines 1]
    }

    set sub_name [string trim [lindex $line 2] "\[|\\"]
    ####Todo parse the robot lib to get the keywords
    #customer asked not removing underscores in API names
    #regsub -all "_" $sub_name " " sub_name
    append result $format "$\{[lindex $line 1]\} =  $sub_name"

    for {set i $lineindex} {$i < $len} {incr i} {
        set line [lindex $lines $i]
        set line [string trim $line]
        regsub -all "\"" $line "" line
        if {[regexp -nocase "^-mpls_labels" $line] ||[regexp -nocase "^-mpls_cos" $line]|| [regexp -nocase "^-mpls_ttl" $line] ||[regexp -nocase "^-mpls_bottom_stack_bit" $line]} {
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
        set key   [string trimright $key "\]"]
        set line  [string trim $line "\\"]
        set line  [string trim $line "\]"]
        set line [string trimright $line " "]
        set valuelist ""

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
                    set value "\$\{$value\}"
                } elseif {[regexp -all {[0-9]+} $value portindex]} {
                    set value "\$\{port$portindex\}"
                } else {
                    set value "$value"
                }
                append valuelist "$value "
            } else {
                if { $key == "log_sync_message_interval" } {
                    append valuelist "\{\"$value\"\} "
                } elseif {[regexp {\$} $line]} {
                    append valuelist "\$\{$value\} "
                } else {
                    append valuelist "$value "
                }
            }
        }
        if {[llength $line] == 1} {
            append result "  $key=1"
        } else {
            append result "  $key=$valuelist"
        }
    }
    set result [string trimright $result "\n"]

    if {[regexp "sth::sequencer_config" $str]} {
        append result "  tcl_str=\$\{sequencer_config\}"
        set items [split $str " "]
        set i 0
        foreach item $items {
            incr i
            if {$i > 3} {
                set item_py_key [string trim $item "$\]"]
                set item_py_value $item_py_key
                set py_str "  py_$item_py_key\=\$\{$item_py_value\}"
                append result $py_str
            }
        }
        regsub "sth::" $result "" result
    } elseif {[regexp "sth::sequencer_control" $str]} {
        if {[regexp {sequencer_control\s+(.*)\s*]} $str -> seqcmd]} {
            append result "  action=$seqcmd"
        }
    }

    set result [string trimright $result ", "]
    return $result
}

proc ::sth::hlapiGen::formatStatusCheckRobot {str} {
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
    append result $format "\$\{[lindex $items 1]\} =  Get From Dictionary  \$\{[lindex $items 3]\}  $key\n"
    
    #2nd line
    set line [lindex $lines 1]
    set items [split $line " "]
    set status [string trim [lindex $items 1] "\{"]
    
    append result $format "Run Keyword If  \$\{status\} == 0  "

    #3rd line
    set line [lindex $lines 2]
    set line [string trim $line]
    regsub "puts " $line "Log To Console  \\n" line
    regsub -all -- "\"" $line "" line
    #customer asked not removing underscores in API names
    #regsub -all "_" $line " " line
    #append result $format "$line"
    append result "$line"
    
    #4th line
    set line [lindex $lines 3]
    set items [split $line " "]
    set hash [string trim [lindex $items 1] "$"]
    #append result $format "\\n\$\{$hash\}\n"
    append result "\\n\$\{$hash\}\n"

    #5th line
    set line [lindex $lines 4]
    append result $format "...  ELSE  "
    
    
    #6th line  
    set line [lindex $lines 5]
    set line [string trim $line]
    if {[regexp {set seq_status \[keylget} $str]} {
        set items [split $line " "]
        set key [string trim [lindex $items 4] "\]"]
        set preresult "$\{[lindex $items 1]\} =  Get From Dictionary  \$\{[lindex $items 3]\}  $key\n"
        set hash $key
        set result  $preresult$result
        set line [lindex $lines 6]
        set line [string trim $line]
        regsub "\\$.*$" $line "" line
    } 
        regsub "puts " $line "Log To Console  \\n" line
        regsub -all -- "\"" $line "" line
        # customer asked not removing underscores in API names
        # regsub -all "_" $line " " line
        #append result $format "$line"
        append result "$line"
    

    #7th line
    set line [lindex $lines 6]
    if {[regexp {\}} $line]} {

    } else {
        #For stats api's
        #append result $format "\\n\$\{$hash\}\n"
        append result "\\n\$\{$hash\}\n"
    }
    
    return $result
}

proc ::sth::hlapiGen::formatHandlesRobot {str} {
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
        #set line ""
        if {[llength $words] <= 7} {
            set keygetindex [lsearch $words "keylget"]
            if {[regexp -nocase "lindex" $line]} {
                set temp [lindex $words [expr $keygetindex + 2]]
                set line ""
                set varNameNew [lindex $words 1]
                set varName [lindex $words [expr $keygetindex + 1]]
                set listIdx [lindex $words [expr $keygetindex + 3]]
                foreach insideList [split $temp .] {
                    append line "\$\{$varNameNew\} =  Get From Dictionary  \$\{$varName\}  $insideList\n"
                    set varName $varNameNew
                }
                append line "\$\{$varNameNew\} =  Get From List  \$\{$varNameNew.split()\}  $listIdx\n"
            } else {
                set temp [lindex $words [expr $keygetindex + 2]]
                set varNameNew [lindex $words 1]
                set varName [lindex $words [expr $keygetindex + 1]]
                set line ""
                foreach key [split $temp "\."] {
                    append line "\$\{$varNameNew\} =  Get From Dictionary  \$\{$varName\}  $key\n"
                    set varName $varNameNew
                }
            }
        } else {
            if {[regexp -nocase "lindex" $line]} {
                set line ""
                set varNameNew [lindex $words 1]
                set varNameList ""
                set i 0
                for {set index 4} {$index < [llength $words]} {incr index 5} {
                    set lineTemp ""
                    set lineTempGetList ""
                    set varNameNewTemp $varNameNew$i
                    set varNameNewTempGetList $varNameNew\_item$i
                    set varName [lindex $words $index]
                    set key [lindex $words [expr $index + 1]]
                    set lineTemp "\$\{$varNameNewTemp\} =  Get From Dictionary  \$\{$varName\}  $key"
                    set lineTempGetList "\$\{$varNameNewTempGetList\} =  Get From List  \$\{$varNameNewTemp.split()\}  0"
                    append varNameList "\$\{$varNameNewTempGetList\} "
                    append line "$lineTemp\n$lineTempGetList\n"
                    incr i
                }
                set varNameList [string trimright $varNameList]
                append line "\$\{$varNameNew\} =  Set Variable  $varNameList"
            } elseif {[regexp -nocase "lrange" $line]} {
                #set flag for lrange
                set ::sth::hlapiGen::scaling_lrange 1
                set varNameNew [lindex $words 1]
                set line ""
                set varNameList ""
                for {set index 4} {$index < [llength $words]} {incr index 6} {
                    set dict_name [lindex $words $index]
                    set dict_key [lindex $words [expr $index + 1]]
                    set range_start [lindex $words [expr $index + 2]]
                    set range_end [lindex $words [expr $index + 3]]
                    append line "\$\{$dict_name\_val\} =  Get From Dictionary  \$\{$dict_name\}  $dict_key\n"
                    append line "\$\{$dict_name\_val\_range\} =  Get Slice From List  \$\{$dict_name\_val.split()\}  $range_start  [expr $range_end+1]\n"
                    append varNameList "\$\{$dict_name\_val\_range\}  "
                }
                set varNameList [string trimright $varNameList]
                append line "\$\{$varNameNew\} =  Combine Lists  $varNameList"
            } else {
                set line ""
                set i 0
                set varNameNew [lindex $words 1]
                set varNameList ""
                for {set index 3} {$index < [llength $words]} {incr index 3} {
                    set varNameNewTemp $varNameNew$i
                    set varName [lindex $words $index]
                    set key [lindex $words [expr $index + 1]]
                    append varNameList "\$\{$varNameNewTemp\} "
                    append line "\$\{$varNameNewTemp\} =  Get From Dictionary  \$\{$varName\}  $key\n"
                    incr i
                }
                set varNameList [string trimright $varNameList]
                append line "\$\{$varNameNew\} =  Set Variable  $varNameList"
            }
        }
        append result "$line\n"
    }
    return $result;
}
