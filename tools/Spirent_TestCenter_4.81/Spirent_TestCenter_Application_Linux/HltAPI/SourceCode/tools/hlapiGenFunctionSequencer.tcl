#package require Memchan

namespace eval ::sth::hlapiGen:: {
	variable v_readonly_attr "-parent, -ElapsedTime, -EndTime, -ProgressCancelled, -ProgressCurrentStep, -ProgressCurrentStepName, -ProgressCurrentValue, -ProgressDisplayCounter, -ProgressMaxValue, -ProgressStepsCount, -StartTime, -Active, -State, -Status, -PassFailState, -Successful, -Unsuccessful, -CurrentIteration, -TestStatus, -CurrentLoad,"
	variable v_sequencer_attr "-sequencerfinalizetype-Targets, -BreakpointList, -CleanupCommand, -DisabledCommandList, -ErrorHandler, -Name,"
	variable v_seqgrpcommand_attr "-sequencerfinalizetype-Sources, -Name,"
	variable v_retvalues ""
	variable v_seqcmd_handles
}

#the sequencer functions will be included in this file for hlapiGen

proc copy_attr {obj_handle} {
    set class [regsub -all {\d+$} $obj_handle ""]
	
	set parent [stc::get $obj_handle -parent]
	
    set obj_attr [stc::get $obj_handle]
	set new_obj [stc::create $class -under $parent]
	
	catch {stc::config $new_obj $obj_attr} 

    set obj_children [stc::get $obj_handle -children]
    if {![string match "" $obj_children ]} {
        foreach obj_child $obj_children {
            copy_attr $obj_child
        }
    }
	
	return $new_obj
}

proc copy_objects {objects} {
	set new_objs ""
    foreach obj $objects {
		append new_objs [copy_attr $obj]
    }
	
	return $new_objs
}

#This function is not in use by "return" directly
#because we didn't re-direct standard output to avoid unexpected exception msg.
proc ::sth::hlapiGen::redirect_stdout {{redirect "true"}} {
	return
	if {[info exists ::text]} {
		return
	}
	
	close stdout
	if {$redirect eq "true"} {
		set stdout [fifo]
	} else {
		if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
			open "CON" "w"
		} else {
			open "/dev/tty" "w"
		}   
	}
}

proc ::sth::hlapiGen::find_handle {myvalue {child ""}} {
	upvar myvalue value_local
	variable v_retvalues
	variable v_seqcmd_handles
	
	set myret ""
	set matched ""
	set class [regsub -all {\d+$} $value_local ""]
	set childclass [regsub -all {\d+$} $child ""]
	if {[info exists ::sth::hlapiGen::device_ret($value_local)]} {
		if {[info exists v_seqcmd_handles($myvalue)]} {
			set value_local $v_seqcmd_handles($myvalue)
			regexp {\d+$} $value_local matched
		} else {
			set handle [lindex $::sth::hlapiGen::device_ret($value_local) 0]
			if {[regexp -nocase dhcp $childclass]} {
				if {[info exists ::sth::hlapiGen::dhcpv4servertconfigured($value_local)]} {
					set handle $::sth::hlapiGen::dhcpv4servertconfigured($value_local)
				} elseif {[info exists ::sth::hlapiGen::dhcpv6servertconfigured($value_local)]} {
					set handle $::sth::hlapiGen::dhcpv6servertconfigured($value_local)
				}
			}
			regexp {.*(\d+).*} $handle matched matched
			set hndType ""
            if {[regexp -nocase "videoserverprotocol" $value_local]} {
                set hndType "session_handle"
            }
            set myret [get_device_created $value_local my$class$matched $hndType $childclass]
			set value_local "\$my$class$matched"
			set v_seqcmd_handles($myvalue) $value_local
		}
		if {$child ne ""} {
			append myret "set my$childclass$matched \[stc::get $value_local -children-$childclass\]\n"
			set value_local "\$my$childclass$matched"
			set v_seqcmd_handles($child) $value_local
		} 
	} elseif {[info exists ::sth::hlapiGen::port_ret($value_local)]} {
		set handle [lindex $::sth::hlapiGen::port_ret($value_local) 0]
		regexp {\d+$} $handle matched
		set value_local "$handle"
		if {$child ne ""} {
			append myret "set my$childclass$matched \[stc::get $handle -children-$childclass\]\n"
			set value_local "\$my$childclass$matched"
			set v_seqcmd_handles($child) $value_local
		}
	} elseif {[info exists ::sth::hlapiGen::traffic_ret($value_local)]} {
		set handle [lindex $::sth::hlapiGen::traffic_ret($value_local) 0]
		regexp {\d+$} $handle matched
		set myret "set my$class$matched \[keylget $handle stream_id\] \n"
		set value_local "\$my$class$matched"
		set v_seqcmd_handles($myvalue) $value_local
	} else {
		set value_local -1
	}
	
	if {[info exists handle]} {
		set handle [string trim $handle "\$"]
		if {![regexp -nocase "$handle" $v_retvalues]} {
			append v_retvalues "\$$handle "
		}
	}
	
	return $myret
}

proc ::sth::hlapiGen::output_config {obj_handle newobj prop values emulate_obj} {
	upvar emulate_obj emulation_local
	variable v_seqcmd_handles
	variable unsupport_handles
	
	regsub -all {\\} $values "/" values 
	
	#append cfg_proc "stc::config $sequencer -ErrorHandler STOP_ON_ERROR\n"
	if {[regexp -nocase "^-ErrorHandler$" $prop]} {
		set newvalue "STOP_ON_ERROR"
	} elseif {[regexp -nocase "^-Name$" $prop]} {
		set newvalue $values
	} elseif {[regexp -nocase "^-ImixDistributionList$" $prop]} {
		set newvalue ""
		set distribute_list [stc::get project1 -children-framelengthdistribution]
		foreach value $values {
			set index [lsearch $distribute_list $value]
			set newvalue [concat $newvalue framelengthdistribution[expr $index+1]]
		}
	} else {
		set last_flag 0
		set newvalue ""
		foreach value $values {
			set flag 0
			set myvalue $value
			if {$value ne "project1" && $value ne "system1" &&
				[regexp {^[a-z]} $value] && [regexp {\d+$} $value] &&
				![catch {stc::get $value}]} { #$value is handle
				if {[info exists v_seqcmd_handles($value)]} {
					set myvalue "$v_seqcmd_handles($value)"
					if {![regexp {^\$} $myvalue]} {
						set flag 1
					}
				} else {
					append emulation_local [find_handle $myvalue]
					if {$myvalue eq -1} {
						set myvalue [stc::get $value -parent]
						if {$myvalue ne "project1" && $myvalue ne "system1" } {
							append emulation_local [find_handle $myvalue $value]
							if {$myvalue eq -1} {
								set flag 1
							}
						} else {
							set flag 1
						}
					} 
				}
			}
				
			if {$flag eq 1} {
				if {[regexp {command\d+$|^sequencer\d+$} $value]} {
					set last_flag [expr $flag|$last_flag]
                    if {![info exists v_seqcmd_handles($value)] || ![regexp "stc::config \\$$newobj \\$prop" $v_seqcmd_handles($value)]} {
                        lappend v_seqcmd_handles($value) "stc::config \$$newobj $prop"
                    }
				} else {
					append newvalue "$value\??? "
					set value_name [stc::get $value -name]
					puts_msg "$value \"$value_name\" used in command sequencer is not supported in HLTAPI or SaveAsHltapi.\n"
				}
				continue
			} else {
				append newvalue "$myvalue "
			}
		}
		
		set newvalue [string trim $newvalue]
		if {$last_flag eq 1} {
			if {$newvalue ne "" } {
				foreach value $values {
					if {[info exists v_seqcmd_handles($value)]} {
						set myoutput "$v_seqcmd_handles($value)"
						foreach output $myoutput {
							if {[regexp {^stc::config} $output] && [regexp $newobj $output] && [regexp \\$prop $output]} {
								lappend newoutput "stc::config \$$newobj $prop \"$newvalue\""
							} else {
								lappend newoutput $output
							}
						}
						set v_seqcmd_handles($value) $newoutput
						set myoutput $newoutput
					}
				}
			}
			if {[regexp -nocase "igmpmld" $obj_handle]} {
				if {[info exists myoutput]} {
					puts "enter the igmp handle: $myoutput"
				}
			}
            return
        }
    }
   
	if {[regexp -nocase "igmpmld" $obj_handle]} {
		if {[info exists myoutput]} {
			puts "enter the igmp handle: $myoutput"
		}
    }
	append emulation_local "stc::config \$$newobj $prop \"$newvalue\"\n"
}

proc ::sth::hlapiGen::emulate_copy_attr {obj_handle parent attrs readonly_attrs} {
	variable v_counter
	variable v_readonly_attr
	variable v_seqcmd_handles
	
	set obj_attr [stc::get $obj_handle]
	#set emulate_obj "\n# $obj_attr"

    set class [regsub -all {\d+$} $obj_handle ""]
	set myclass [regsub -all {\.} $class "_"]
	set newobj $myclass$v_counter
	if {$parent ne ""} {
		append emulate_obj "\nset $myclass$v_counter \[stc::create $class -under \$$parent\]\n"
	} else {
		set myparent [stc::get $obj_handle -parent]
		append emulate_obj "\nset $myclass$v_counter \[stc::create $class -under $myparent\]\n"
	}
	if {[info exists v_seqcmd_handles($obj_handle)]} {
		set myoutput $v_seqcmd_handles($obj_handle)
	}
	set v_seqcmd_handles($obj_handle) "\$$newobj"
	
	redirect_stdout true
	set len [llength $obj_attr]
	for {set i 0} {$i < $len} {incr i 2} {
		set prop [lindex $obj_attr $i]
		set myprop "\\$prop,"
		set value [lindex $obj_attr [expr $i+1]]

		if {$attrs ne "" && [regexp -nocase $myprop $attrs]} {
			output_config $obj_handle $class$v_counter $prop $value $emulate_obj
		} elseif {$readonly_attrs ne "" && ![regexp -nocase $myprop $readonly_attrs]} {
			if {![catch {stc::config $obj_handle $prop "$value"}]} {
				output_config $obj_handle $class$v_counter $prop $value $emulate_obj
			}
		}
	}
	redirect_stdout false
		
	incr v_counter
    if {[catch {set obj_cmdlist [stc::get $obj_handle -CommandList]} err]} {
		set obj_children [stc::get $obj_handle -children]
		foreach obj_child $obj_children {
			append emulate_obj [emulate_copy_attr $obj_child $newobj "" $v_readonly_attr]
		}
	} elseif {![string match "" $obj_cmdlist ]} {
		if {![regexp -nocase {^sequencer\d+$} $obj_handle]} {
			set obj_children [stc::get $obj_handle -children]
			set obj_filter [regsub -all " " $obj_cmdlist "|"]
			regsub -all "$obj_filter" $obj_children "" obj_children
			foreach obj_child $obj_children {
				append emulate_obj [emulate_copy_attr $obj_child $newobj "" $v_readonly_attr]
			}
		}
		foreach obj_child $obj_cmdlist {
			append emulate_obj [emulate_copy_attr $obj_child $newobj "" $v_readonly_attr]
		}
    } else {
		set obj_children [stc::get $obj_handle -children]
		foreach obj_child $obj_children {
			append emulate_obj [emulate_copy_attr $obj_child $newobj "" $v_readonly_attr]
		}
	}
	
	if {[info exists myoutput]} {
		foreach output $myoutput {
			set check ""
			foreach {key cmdoutput} [array get v_seqcmd_handles] {
				if {$key ne $obj_handle && [string first $output $cmdoutput]>0} {
					lappend check $key
				}
			}
			if {$check ne ""} {
				foreach key $check {
					set cmdoutput $v_seqcmd_handles($key)
					set index [string first $output $cmdoutput]
					set index2 [expr [string length $output]+$index-1] 
					if {$index >0} {
						if {[regexp -nocase {\"$} $output]} {
							set v_seqcmd_handles($key) [string replace $cmdoutput $index $index2 [concat [string trimright $output "\""] " \$$newobj\""]]
						} else {
							set v_seqcmd_handles($key) [string replace $cmdoutput $index $index2 "$output \"\$$newobj\""]
						}
					}
				}
			} else {
				if {[regexp -nocase {\"$} $output]} {
					append emulate_obj [concat [string trimright $output "\""] " \$$newobj\""]
					append emulate_obj "\n"
				} else {
					append emulate_obj "$output \$$newobj\n"
				}
			}
		}
	}
	
	if {[info exist obj_cmdlist] && ![string match "" $obj_cmdlist ]} {
		foreach cmd_handle $obj_cmdlist {
			append my_command_list "$v_seqcmd_handles($cmd_handle) "
		}
		
		set my_command_list [string trim $my_command_list]
		append emulate_obj "\nstc::config $v_seqcmd_handles($obj_handle) -commandlist \"$my_command_list\"\n"
	}

	return "$emulate_obj"
}

proc ::sth::hlapiGen::emulate_copy_objects {objects attrs} {
	upvar new_objects new_objects_local
	set emulate_str ""
    foreach obj $objects {			
		append emulate_str [emulate_copy_attr $obj "" $attrs ""]
    }
	
	return $emulate_str
}

proc ::sth::hlapiGen::hlapi_gen_sequencer_config {sequencer} {
	variable v_counter
	set v_counter 1
	variable v_retvalues
	set v_retvalues ""
	variable v_sequencer_attr
	variable v_seqgrpcommand_attr
	variable v_seqcmd_handles
	array unset v_seqcmd_handles
    array set v_seqcmd_handles {}
	
	set comments ""
    append comments "\n##############################################################\n"
    append comments "#config sequencer commands\n"
    append comments "##############################################################\n"
    puts_to_file $comments
	
	set seq_grpcmd [stc::get $sequencer -sequencerfinalizetype-Targets]
	
	set cfg_proc "catch \{\n"
	append cfg_proc [emulate_copy_objects $seq_grpcmd $v_seqgrpcommand_attr]
	append cfg_proc [emulate_copy_objects $sequencer $v_sequencer_attr]

	append cfg_proc "\n\} result \n"
	append cfg_proc "\nreturn \$result\n\}\n"
	
	set v_retvalues [string trim $v_retvalues]
	set v_retvalues [regsub -all {\$\$} $v_retvalues "\$"]
	set input [regsub -all {\$} $v_retvalues ""]
	set cfg_proc_str "proc sth::sequencer_config \{$input\} \{\n"
	append cfg_proc_str $cfg_proc
	puts_to_file $cfg_proc_str
	
	puts_to_file "set cfg_ret1 \[sth::sequencer_config $v_retvalues\]"
	
	set status "if \{\$cfg_ret1 == \"\"\} \{\n"
	append status "puts \"***** run sth::sequencer_config successfully\"\n"
	append status "\} else \{\n"
	append status "puts \"<error>run sth::sequencer_config failed\"\n"
	append status "puts \$cfg_ret1\n\}\n"
	puts_to_file $status
}

proc ::sth::hlapiGen::hlapi_gen_sequencer_control {} {
	set comments ""
    append comments "#config part is finished\n"
	append comments "\n##############################################################\n"
    append comments "#control sequencer commands\n"
    append comments "##############################################################\n"
	puts_to_file $comments
	
	puts_to_file "set ctrl_ret1 \[sth::sequencer_control start\]"
	
	set status "set status \[keylget ctrl_ret1 status\]\n"
	append status "if \{\$status == 0\} \{\n"
	append status "puts \"run sth::sequencer_control failed\"\n"
	append status "puts \$ctrl_ret1\n\} else \{\n"
	append status "set seq_status \[keylget ctrl_ret1 seq_status\]\n"
	append status "puts \"***** run sth::sequencer_control : \$seq_status\"\n\}\n"
	puts_to_file $status
}

proc ::sth::hlapiGen::hlapi_gen_sequencer {stepIndex} {
	upvar stepIndex step_idx

	set sequencer [stc::get system1 -children-sequencer]
	if {$sequencer eq ""} {
		return ""
	}
	set children [stc::get $sequencer -children]
	if {$children eq ""} {
		return ""
	}
	
	set cmdlist [stc::get $sequencer -commandlist]
	if {$cmdlist eq ""} {
		return ""
	}
	
	if {[regexp -nocase perl|jt_perl $::sth::hlapiGen::output_type]} {
		puts_msg "\ncommand sequencer in SaveAsHltapi doesn't support \"HLTAPI for $::sth::hlapiGen::output_type\", \n so skip sequencer configuration.\n"
	    return ""
	}
	
	if {[regexp -nocase {^rfc[0-9]+} $cmdlist]} {
		puts_msg "\nrfc-related command sequencer will not be saved to script.\n"
        return ""
	}

	puts_msg "step[incr step_idx]: generate the config & start sequencer commands"
    hlapi_gen_sequencer_config $sequencer
    hlapi_gen_sequencer_control
	return $sequencer
}
