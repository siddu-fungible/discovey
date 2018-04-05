
namespace eval ::sth:: {

}

namespace eval ::sth::pcep:: {
    variable returnKeyedList
    variable myclass2relation
    variable handles_generated
}
namespace eval ::sth::Session {}

proc ::sth::emulation_pcep_config { args } {
    ::sth::sthCore::Tracker "::sth::emulation_pcep_config" $args
    
    set ::sth::pcep::returnKeyedList ""
    set _hltCmdName "::sth::emulation_pcep_config"
    if {[catch {
            set idx [lsearch -exact $args "-mode"]
            if {$idx != -1} {
                set arg [lindex $args [expr $idx+1]]
                if {[regexp -nocase $arg "enable"]
                    || [regexp -nocase $arg "add"]} {
                    set arg_new "create"
					set args [lreplace $args [expr $idx+1] [expr $idx+1] "$arg_new"]
                }
            }
            set idx [lsearch -exact $args "-tlv_value"]
            set idx1 [lsearch -exact $args "-length"]
            if {$idx != -1 && $idx1 == -1} {
                set arg [lindex $args [expr $idx+1]]
                set num_args [llength $arg]
                set mylen "-length {"
                for { set i 0 } { $i < $num_args } { incr i } {
                    set myarg1 [lindex $arg $i]
                    set len [llength $myarg1]
                    append mylen " $len"
                }
                append mylen "}"
                set args "$args $mylen"
            }

            set ::sth::pcep::returnKeyedList [eval ::xtapi::scriptrun_stak $_hltCmdName $args]} err]} {
	    ::sth::sthCore::processError ::sth::pcep::returnKeyedList "Error in processing pcep protocol : $err"
	    return $::sth::pcep::returnKeyedList
    }
    keylset ::sth::pcep::returnKeyedList status $::sth::sthCore::SUCCESS 
    return $::sth::pcep::returnKeyedList
	
	package require tdom
	
    variable ::sth::pcep::userArgsArray
    array unset ::sth::pcep::userArgsArray
    array set ::sth::pcep::userArgsArray {}
    variable ::sth::pcep::myprop2class

    if {[catch {
        if {![array size myprop2class]} {
            set scriptpath [file join $::sth::mydirectory "model"]
            ::sth::Session::parse_xml [file join $scriptpath stcPcep.processed.xml]
            ::sth::Session::parse_customized_xml [file join $scriptpath stcPcep.tapi.xml] 
        }
        
        ::sth::pcep::process_args $args $_hltCmdName
            
        ::sth::pcep::emulation_pcep_config_imp $_hltCmdName} err]} {
        ::sth::sthCore::processError ::sth::pcep::returnKeyedList "Error in implementing pcep protocol : $err"
        return $::sth::pcep::returnKeyedList
    }
    
    keylset ::sth::pcep::returnKeyedList status $::sth::sthCore::SUCCESS 
    return $::sth::pcep::returnKeyedList
}

proc ::sth::pcep::process_args {userArgs function} {
    variable ::sth::pcep::userArgsArray
    variable ::sth::pcep::myprop2class
    variable ::sth::pcep::myclass2relation
    
    array unset ::sth::pcep::myclass2relation
    array set ::sth::pcep::myclass2relation {}
    array unset ::sth::pcep::myprop2class
    array set ::sth::pcep::myprop2class {}
    array unset ::sth::pcep::userArgsArray
    array set ::sth::pcep::userArgsArray {}
    
    set duplicate_args ""
    set num_args [llength $userArgs]
    for { set i 0 } { $i < $num_args } { incr i } {
        set arg [lindex $userArgs $i]
        if {[regexp {^-} $arg]} {
            # Remove the dash from the variable
            regsub {^-} $arg {} myarg
            incr i
    
            set value [lindex $userArgs $i]
            if {[info exist ::sth::Session::valueproc($myarg)]} {
                if {[regexp -nocase $value $::sth::Session::valueproc($myarg)]} {
                    set value [regsub -nocase "$value\->" $::sth::Session::valueproc($myarg) ""]
                }
            }
            set ::sth::pcep::userArgsArray($myarg) $value                         
            set arg_match [regsub -all "_" $myarg ""]
            set find [array names ::sth::Session::prop2class -glob *\.$arg_match]
            if {$find eq ""} {
                if {[regexp -nocase {mode|handle} $myarg]} {
                    if {[regexp -nocase {mode} $myarg]} {
                        set value [lindex $userArgs $i]
                        if {![regexp -nocase {enable|modify|add} $value]} {
                            append args "-$arg $value, "
                            continue
                        }
                    }
                } else {
                    append args "-$arg $value, "
                    continue
                }
            } else {
                if {[regexp " " $find]} {
                    lappend duplicate_args $find
                    continue
                }
                if {[regexp -all {\.(.*?)\.} $find match1 match2]} {
                    set ::sth::pcep::myprop2class($find) $::sth::Session::prop2class($find)
                    process_arg_by_find $find $match2 $value
                } else {
                    set ::sth::pcep::myprop2class($find) $::sth::Session::prop2class($find)
                    set myclsname [regsub {\..*} $find ""]
                    process_arg_by $myclsname $value
                }
            }
        } 
    }
        
    if {[info exists args] && $args ne ""} {
        puts "skip invalid args: $args"
    }
    
    foreach dup_arg $duplicate_args {
        foreach arg $dup_arg {
            set pname [regsub {\..*} $arg ""]
            if {[regexp -nocase "base" $pname]} {
                continue
            }
            if {[process_func_key "::sth::emulation_pcep_config" $pname]} {                              
                set clsfind [array names ::sth::Session::class2relation -glob *\.$pname]
                if {$clsfind ne ""} {
                    set ::sth::pcep::myprop2class($arg) $::sth::Session::prop2class($arg)
                    set ::sth::pcep::myclass2relation($clsfind) $::sth::Session::class2relation($clsfind)
                }
            }
        }
    }

    set exist [array names ::sth::pcep::myclass2relation]          
    foreach rel [lsort -dictionary $exist] {
        regsub {^\d+\.} $rel "" my_rel
        if {![process_func_key "::sth::emulation_pcep_config" $my_rel]} {
            set argNames [array names ::sth::pcep::userArgsArray]
            set propfind [regsub -nocase -all "$my_rel." [array names ::sth::pcep::myprop2class -glob $my_rel\.*] ""]
            foreach prop $propfind {
                foreach argn $argNames {
                    regsub -all "_" $argn "" argName
                    if {[regexp -nocase $prop $argName]} {
                        append wrong_args "-$argn $::sth::pcep::userArgsArray($argn), "
                        unset ::sth::pcep::userArgsArray($argn)
                        if {[info exists ::sth::pcep::myclass2relation($rel)]} {
                            unset ::sth::pcep::myclass2relation($rel)
                        }
                        
                        unset ::sth::pcep::myprop2class($my_rel\.$prop)
                        regsub $rel $exist "" exist
                    }
                }
            }
            continue
        }
        set parents ""
        foreach myrel $::sth::pcep::myclass2relation($rel) {
            regexp { (.*?) } $myrel match
            set mymatch [split [string trim $match] "-"]
            set size [expr [llength $mymatch]-1]
            if {[regexp -nocase {framework.ParentChild sources$} $myrel]} {
                if {[regexp -nocase "base" [lindex $myrel 0]]} {
                    set basefind [array names ::sth::Session::baseclass2relation -glob *\.[lindex $myrel 0]]
                    foreach base $basefind {
                        foreach baserel $::sth::Session::baseclass2relation($base) {
                            if {[regexp -nocase {base base$} $baserel]} {
                                set clsname [lindex $baserel 0]
                                if {[regexp -nocase $clsname $exist]}  {
                                    set b$rel $clsname
                                } else {
                                    append parents "$clsname,$size "
                                }
                            }
                        }
                    }
                } else {
                    if {![regexp -nocase [lindex $myrel 0] $exist] && ![regexp -nocase {^core.emulateddevice} $myrel]} {
                        append parents "[lindex $myrel 0],$size "
                    } else {
                        set b$rel true
                    }
                }
            }
        }
        
        if {[info exist b$rel]} {
            if {[process_func_key "::sth::emulation_pcep_config" $my_rel]} {
                set bfind [array names ::sth::pcep::myclass2relation -glob *\.[set b$rel]]
                foreach myrel_a $::sth::pcep::myclass2relation($rel) {
                    if {[regexp -nocase {framework.ParentChild sources$} $myrel_a]} {
                        if {[regexp -nocase {^core.emulateddevice} $myrel_a]} {
                            set bfind [lindex $myrel_a 0]
                        } else {
                            set obj [lindex $myrel_a 0]
                            append bfind [array names ::sth::pcep::myclass2relation -glob *\.$obj]
                        }
                    }
                }
                if {$bfind eq ""} {
                    return -code 1 -errorcode -1 "args are not consistent with each other, cannot continue"
                }
            } else {
                set argNames [array names ::sth::pcep::userArgsArray]
                set propfind [regsub -nocase -all "$my_rel." [array names ::sth::pcep::myprop2class -glob $my_rel\.*] ""]
                foreach prop $propfind {
                    foreach argn $argNames {
                        regsub -all "_" $argn "" argName
                        if {[regexp -nocase $prop $argName]} {
                            append wrong_args "-$argn $::sth::pcep::userArgsArray($argn), "
                            unset ::sth::pcep::userArgsArray($argn)
                            if {[info exists ::sth::pcep::myclass2relation($rel)]} {
                                unset ::sth::pcep::myclass2relation($rel)
                            }
                            
                            unset ::sth::pcep::myprop2class($my_rel\.$prop)
                        }
                    }
                }
            }
            unset b$rel
        } elseif {$parents ne ""} {
            set bOK "false"
            foreach pname $parents {
                set num [regsub {.*,} $pname ""]
                set pname [regsub {,.*} $pname ""]
                if {[process_func_key "::sth::emulation_pcep_config" $pname]} { 
                    set clsfind [array names ::sth::Session::class2relation -glob *\.$pname]
                    if {$clsfind ne ""} {
                        if {$num == 1} {
                            set ::sth::pcep::myclass2relation($clsfind) $::sth::Session::class2relation($clsfind)
                        } else {
                            set ::sth::pcep::myclass2relation($clsfind) [regsub -all "unbounded" $::sth::Session::class2relation($clsfind) $num]
                        }
                        createparent_recursive $clsfind
                    }
                    set bOK "true"
                    break
                }
            }
            if {$bOK eq "false"} {
                return -code 1 -errorcode -1 "args are not consistent with each other, cannot continue"
            }
        }
    }
    
    if {[info exists ::sth::pcep::option_value]} {
        unset ::sth::pcep::option_value
    }
    
    if {[info exists wrong_args] && $wrong_args ne ""} {
        puts "skip wrong args: $wrong_args because they are not consistent with other args, so are skipped."
    }
}

proc ::sth::pcep::process_arg_by_find {find match value} {
    set myclsname [regsub {\..*} $find ""]
    process_arg_by $myclsname $value
    set doublecls $myclsname\.$match
    set myclsname $match
    
    if {$myclsname ne ""} {
        set clsfind [array names ::sth::Session::class2relation -glob *\.$myclsname]
    
        foreach cls $clsfind {
            regexp -all {(\d+\.).*} $cls mymatch index
            if {$value ne ""} {
                set unbound $::sth::Session::class2relation($cls)
                if {[regexp {\{} $value]} {
                    set num ""
                    foreach v $value {
                        append num "[llength $v]-"
                    }
                } else {
                    set num "[llength $value]-"
                }
                if {$num eq "1-"} {
                    set ::sth::pcep::myclass2relation($index$doublecls) $unbound
                } else {
                    set ::sth::pcep::myclass2relation($index$doublecls) [regsub -all "unbounded-" $unbound $num]
                }
            } else {
                set ::sth::pcep::myclass2relation($index$doublecls) $::sth::Session::class2relation($cls)
            }
        }
    }
}

proc ::sth::pcep::createparent_recursive {clsfind} {
    foreach myrel_a $::sth::pcep::myclass2relation($clsfind) {
        if {[regexp -nocase {framework.ParentChild sources$} $myrel_a]} {
            if {![regexp -nocase {^core.emulateddevice} $myrel_a]} {
                set obj [lindex $myrel_a 0]
                if {[process_func_key "::sth::emulation_pcep_config" $obj]} {
                    set parent [array names ::sth::pcep::myclass2relation -glob *\.$obj]
                    if {$parent eq ""} {
                        set pfind [array names ::sth::Session::class2relation -glob *\.$obj]
                        if {[regexp -nocase base $pfind]} {
                            puts "add $pfind parent into myclass2relation"
                        }
                        if {$pfind ne ""} {
                            set ::sth::pcep::myclass2relation($pfind) $::sth::Session::class2relation($pfind)
                            createparent_recursive $pfind
                        }
                    }
                    break
                }
            }
        }
    }  
}

proc ::sth::pcep::process_arg_by {myclsname {value ""}} {
    if {$myclsname ne ""} {
        set clsfind [array names ::sth::Session::class2relation -glob *\.$myclsname]
    
        foreach cls $clsfind {
            if {$value ne ""} {
                set unbound $::sth::Session::class2relation($cls)
                if {[regexp {\{} $value]} {
                    set num ""
                    foreach v $value {
                        append num "[llength $v]-"
                    }
                } else {
                    set num "[llength $value]-"
                }
                if {$num eq "1-"} {
                    set ::sth::pcep::myclass2relation($cls) $unbound
                } else {
                    set ::sth::pcep::myclass2relation($cls) [regsub -all "unbounded-" $unbound $num]
                }
            } else {
                set ::sth::pcep::myclass2relation($cls) $::sth::Session::class2relation($cls)
            }
        }
    }
}

proc ::sth::pcep::save_clshandle_by {myclsname} {
    if {$myclsname ne ""} {
        set clsfind [array names ::sth::Session::class2relation -glob *\.$myclsname]
        
        set clslist ""
        foreach cls $clsfind {
            append clslist "$cls "
        }
        
        return $clslist
    }
    
    return ""
}

proc ::sth::pcep::emulation_pcep_config_imp {funcname} {
    set mymode ""
    if {[info exist ::sth::pcep::userArgsArray(mode)]} {
        set mymode [string tolower $::sth::pcep::userArgsArray(mode)]
    }
    
    set myhandle ""
    if {[info exist ::sth::pcep::userArgsArray(handle)]} {
        set myhandle [string tolower $::sth::pcep::userArgsArray(handle)]
    }
    
    if {$mymode eq "" && $myhandle eq ""} {
        return [emulation_pcep_config_common $funcname]
    }
    
    
    if {$mymode eq ""} {
       return -code 1 -errorcode -1 "mode is a mandatory argument, cannot be empty"
    }
    if {$myhandle eq ""} {
        return -code 1 -errorcode -1 "handle is a mandatory argument, cannot be empty"
    }

    if {[regexp " " $myhandle]} {
        return -code 1 -errorcode -1 "handle cannot be multiple values"
    }
    
    emulation_pcep_config_$mymode $funcname
}

proc ::sth::pcep::emulation_pcep_config_delete {funcname} {
    set myhandle $::sth::pcep::userArgsArray(handle)
    
    foreach hnd $myhandle {
        ::sth::sthCore::invoke stc::delete $hnd
    }
}

proc ::sth::pcep::emulation_pcep_config_enable {funcname} {
    array unset ::sth::pcep::handles_generated
    array set ::sth::pcep::handles_generated {}
    
    emulation_pcep_config_common $funcname
}

proc ::sth::pcep::filter_handleprop {myhandle mode} {
    array unset ::sth::pcep::handles_generated
    array set ::sth::pcep::handles_generated {}
    
    set my_handle $myhandle
    set mycls [regsub {\d+$} $myhandle ""]
    regexp {(\d+)\..*} [array names ::sth::pcep::myclass2relation -glob *\.$mycls] match mynum
    foreach numcls [lsort -dictionary [array names ::sth::pcep::myclass2relation]] {
        regexp {(\d+)\.(.*)} $numcls match num cls
        if {$num == 0} {
            if {![info exists mynum] || $mynum eq ""} {
                set my_handle [::sth::sthCore::invoke stc::get $my_handle -children-$cls]
                if {$my_handle eq ""} {
                    return
                }
                set mynum $num
                set mycls [regsub {\d+$} $my_handle ""]
            }
        }
        
        if {$num > $mynum} {
            set parent [find_parent_hnd $numcls $mycls]
            if {$parent eq ""} {
                unset ::sth::pcep::myclass2relation($numcls)
            }
        } else {
            if {$mynum == $num} {
                set ::sth::pcep::handles_generated($cls) $my_handle
            }
            
            if {$num < $mynum 
                    || ($mode eq "add" && $mynum == $num)} {
                unset ::sth::pcep::myclass2relation($numcls)
                set argNames [array names ::sth::pcep::userArgsArray]
                set propfind [array names ::sth::pcep::myprop2class -glob $cls\.*]
                foreach prop $propfind {
                    set prop [regsub -nocase -all "$cls." $prop ""] 
                    foreach argn $argNames {
                        regsub -all "_" $argn "" argName
                        if {[regexp -nocase $prop $argName]} {
                            lappend wrong_args "$argn"
                            unset ::sth::pcep::myprop2class($cls\.$prop)
                        }
                    }
                }
            }
        }
    }
    
    if {[info exists wrong_args] && [llength $wrong_args] > 0} {
        set wrongargs ""
        foreach argn $wrong_args {
            regsub -all "_" $argn "" argName
            set propfind [array names ::sth::pcep::myprop2class -glob *\.$argName]
            if {$propfind eq ""} {
                append wrongargs "-$argn $::sth::pcep::userArgsArray($argn), "
                unset ::sth::pcep::userArgsArray($argn)
            }
        }
        if {[info exists wrongargs] && $wrongargs ne "" } {
            puts "skip wrong args: $wrongargs because they cannot do \"$mode\" on -handle $myhandle."
        }
    }
}

proc ::sth::pcep::emulation_pcep_config_modify {funcname} {
    set myhandle $::sth::pcep::userArgsArray(handle)
	filter_handleprop $myhandle modify
        
    emulation_pcep_config_common $funcname
}

proc ::sth::pcep::emulation_pcep_config_add {funcname} {
    set myhandle $::sth::pcep::userArgsArray(handle)
	filter_handleprop $myhandle add
    emulation_pcep_config_common $funcname
}

proc ::sth::pcep::find_parent_hnd {handle mycls} {
    if {[regexp {^\d+} $handle]} {
        set cls_rels $::sth::pcep::myclass2relation($handle)
    } else {
        set cls_rels [array names ::sth::pcep::myclass2relation -glob *\.$handle]
        if {$cls_rels ne ""} {
            set cls_rels $::sth::pcep::myclass2relation($cls_rels)
        }
    }
    foreach rel $cls_rels {     
        if {[regexp -nocase {framework.ParentChild sources$} $rel]} {
            set my_parent [lindex $rel 0]
            if {[regexp "base" $my_parent]} {
                set value_Rels [array names ::sth::Session::baseclass2relation -glob *\.$my_parent]
                foreach rel_handle $value_Rels {
                    foreach myrel $::sth::Session::baseclass2relation($rel_handle) {
                        if {[regexp -nocase {base base$} $myrel]} {
                            set hnd [lindex $myrel 0]
                                
                            set find [array names ::sth::pcep::myclass2relation -glob *\.$hnd]
                            if {$find ne "" || [regexp -nocase $hnd $mycls]} {
                                return $hnd
                            }
                
                            set parent_hnd [find_parent_hnd $hnd $mycls]
                            if {$parent_hnd ne ""} {
                                return $parent_hnd 
                            }
                        }
                    }
                }
            } else {
                set find [array names ::sth::pcep::myclass2relation -glob *\.$my_parent]
                if {$find ne "" || [regexp -nocase $my_parent $mycls]} {
                    return $my_parent
                }
            }
        }
    }
    
    return ""
}

proc ::sth::pcep::emulation_pcep_config_common {funcname} {
    array set myUsersArgs [array get ::sth::pcep::userArgsArray]

    variable ::sth::Session::obj2ret
    
    variable ::sth::pcep::myprop2class
    variable ::sth::pcep::myclass2relation
    variable ::sth::pcep::handles_generated
    
    array unset children_cls 
    array set children_cls {}
        
    set i 0
    set clslist [lsort -dictionary [array names ::sth::pcep::myclass2relation]]
    if {$clslist eq ""} {
        puts "there isn't any valid parameters to configure, so return without doing nothing."
        return
    }
    while {1} {
        set cls_ [lindex $clslist $i]
        set mycls ""
        set cls [regsub {.*\.} $cls_ ""]
        set mycls_ [regsub {\d+\.} $cls_ ""]
        
        set maxmin "1-0"
        set rel_others ""
        set rel_types ""
        set found_parent 0
        if {[regexp -nocase {framework.project } $::sth::pcep::myclass2relation($cls_)]} {
            set parent project1
            set maxmin [lindex [lindex $::sth::pcep::myclass2relation($cls_) 0] 1]
        } else {
            set device $myUsersArgs(handle)
            set parent $device
            foreach rel_handle $::sth::pcep::myclass2relation($cls_) {
				if {[regexp -nocase {framework.ParentChild sources$} $rel_handle]} {
                    if {$found_parent} break
                    
					set rel_parent [lindex $rel_handle 0]
                    if {[info exist ::sth::pcep::handles_generated($rel_parent)]} {
                        if {$mycls_ != $cls} {
                            if {![regexp $rel_parent $mycls_]} {
                                continue
                            }
                        }
                        set parent $::sth::pcep::handles_generated($rel_parent)
                        set found_parent 1
                    } elseif {![regexp "core.emulateddevice" $rel_parent] && ![regexp $rel_parent $device]} {
                        set parent $rel_parent
                        set phnd [array names ::sth::Session::class2relation -glob *\.[string tolower $parent]]
                        if {$phnd eq ""} {
                            set phnd [array names ::sth::Session::baseclass2relation -glob *\.[string tolower $parent]]
                        }
                        if {[regexp "base" $phnd]} {
                            foreach rel_hnd $::sth::Session::baseclass2relation($phnd) {             
                                if {[regexp -nocase {base base$} $rel_hnd]} {
                                    set hnd [lindex $rel_hnd 0]
                                    if {[info exist ::sth::pcep::handles_generated($hnd)]} {
                                        set parent $::sth::pcep::handles_generated($hnd)
                                        set found_parent 1
                                        break
                                    }
                                }
                            }
                        }
                    }
                    set maxmin [lindex $rel_handle 1]
                    if {[regexp $rel_parent $clslist]} {
                        break
                    }
				} else {
                    set maxmin [lindex $rel_handle 1]
                    if {[regexp "\\-0$" $maxmin]} {
                        continue
                    }
					if {[info exist ::sth::pcep::handles_generated([lindex $rel_handle 0])]} {
						append rel_others "[lindex $::sth::pcep::handles_generated([lindex $rel_handle 0]) 0] "
						append rel_types "[lindex $rel_handle 2]-[lindex $rel_handle 3] "
					} else {
						set base [lindex $rel_handle 0]
                        set append_ok false
						set baseRels [array names ::sth::Session::baseclass2relation -glob *\.$base]
						foreach rel_base $baseRels {
							set rel_base_value $::sth::Session::baseclass2relation($rel_base)
							foreach rel_value $rel_base_value {
								if {![regexp -nocase {framework.ParentChild sources$|fake fake$} $rel_value]} {
									set rel_value_hnd [lindex $rel_value 0]
									if {[info exist ::sth::pcep::handles_generated($rel_value_hnd)]} {
										append rel_others "[lindex $::sth::pcep::handles_generated($rel_value_hnd) 0] "
										append rel_types "[lindex $rel_handle 2]-[lindex $rel_handle 3] "
                                        break
									} elseif {[regexp -nocase "base" $rel_value_hnd]} {
                                        set value_Rels [array names ::sth::Session::baseclass2relation -glob *\.$rel_value_hnd]
                                        foreach value_base $value_Rels {
                                            set value_base_value $::sth::Session::baseclass2relation($value_base)
                                            foreach value $value_base_value {
                                                if {![regexp -nocase {framework.ParentChild sources$} $value]} {
                                                    set value_hnd [lindex $value 0]
                                                    if {[info exist ::sth::pcep::handles_generated($value_hnd)]} {
                                                        append rel_others "[lindex $::sth::pcep::handles_generated($value_hnd) 0] "
                                                        append rel_types "[lindex $rel_handle 2]-[lindex $rel_handle 3] "
                                                        break
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    if {[regexp $rel_value_hnd $clslist]} {
                                        set append_ok true
                                        break
                                    }
								}
							}
                            
                            if {$append_ok eq "true"} {
                                break
                            }
						}
					}
				}
			}
        }
    
        set myprops ""
        foreach prop [array names myUsersArgs] {
            set prop1 [regsub -all "_" $prop ""]
            set myprop ""
            if {[info exist ::sth::pcep::myprop2class($cls\.$prop1)]} {
                set myprop $::sth::pcep::myprop2class($cls\.$prop1)
            } elseif {[info exist ::sth::pcep::myprop2class($mycls_\.$prop1)]} {
                set myprop $::sth::pcep::myprop2class($mycls_\.$prop1)
            } 
            if {$myprop != ""} {
                if {[llength $myUsersArgs($prop)] > 1} {
                    set num 0
                    foreach val $myUsersArgs($prop) {
                        foreach v $val {
                            append lprop$num "-$myprop $v "
                            incr num
                        }
                    }
                }
                
                if {[llength $myUsersArgs($prop)] == 1} {
                    append myprops "-$myprop $myUsersArgs($prop) "
                } else {
                    append myprops "-$myprop \{$myUsersArgs($prop)\} "
                }
            }
        }
        
        set listprops {}
        if {[info exist num]} {
            for {set l 0} {$l < $num} {incr l} {
                lappend listprops [set lprop$l]
                unset lprop$l
            }
            unset num
        }
        
        set myhandle ""
        set parent [string trim $parent]
        if {[info exist myUsersArgs(mode)] && [regexp -nocase "modify" $myUsersArgs(mode)]
            && [info exist ::sth::pcep::handles_generated($cls)]} {
			set mycls $::sth::pcep::handles_generated($cls)
        } else {
            catch {
                foreach phandle $parent {
                    set myclass [::sth::sthCore::invoke stc::get $phandle -children-$cls]
                    append mycls "$myclass  "
                }
                set mycls [string trim $mycls]
            }
        }
        
        if {$myprops ne "" || $listprops ne ""} {
            if {[catch {
                if {$mycls ne ""} {
                    if {$maxmin eq "1-1" ||
                        ([info exist myUsersArgs(mode)] && [regexp -nocase "modify" $myUsersArgs(mode)]
                         && ($maxmin eq "1-0" || ([info exist myUsersArgs(handle)] && [regexp $myUsersArgs(handle) $mycls])))} {
                        set myhandle $mycls
                        if {$listprops eq ""} {
                            foreach myh $myhandle {
                                ::sth::sthCore::invoke stc::config $myh $myprops
                            }
                        } else {
                            if {[llength $myhandle] > 1} {
                                set ii 0
                                foreach val $listprops {
                                    set handlei [lindex $myhandle $ii]
                                    set ret [::sth::sthCore::invoke stc::config $handlei "$val"]
                                    incr ii
                                }
                            } else {
                                set ret [::sth::sthCore::invoke stc::config $myhandle "$myprops"]
                            }   
                        }
                    } else {
                        if {[info exist myUsersArgs(mode)] && [regexp -nocase "modify" $myUsersArgs(mode)]} {
                            set handles_gen ""
                            if {[info exist ::sth::pcep::handles_generated($cls)]} {
                                set handles_gen $::sth::pcep::handles_generated($cls)
                            }
                            foreach chnd $mycls {
                                ::sth::sthCore::invoke stc::delete $chnd
                                regsub $chnd $handles_gen "" handles_gen
                            }
                            if {$handles_gen ne ""} {
                                set ::sth::pcep::handles_generated($cls) $handles_gen
                            } elseif {[info exist ::sth::pcep::handles_generated($cls)]} {
                                unset ::sth::pcep::handles_generated($cls)
                            }
                        }

                        if {$listprops eq ""} {
                            foreach myph $parent {
                                set myhandle [::sth::sthCore::invoke stc::create $cls -under $myph $myprops]
                            }
                        } else {
                            set ii 0
                            foreach val $listprops {
                                set ph [lindex $parent $ii]
                                set ret [::sth::sthCore::invoke stc::create $cls -under $ph "$val"]
                                append myhandle "$ret "
                                if {$ii < [expr [llength $parent]-1]} {
                                    incr ii
                                }
                            }
                        }
                    } 
                } else {
                    if {$listprops eq ""} {
                        foreach myph $parent {
                            set myhandle [::sth::sthCore::invoke stc::create $cls -under $myph $myprops]
                        }
                    } else {                       
                        foreach match_rel $::sth::pcep::myclass2relation($cls_) {
                            if {[compare_cls $parent $match_rel]} {
                                continue
                            }
                            set ii 0
                            regexp { (.*?) } $match_rel match
                            set mymatch [split [string trim $match] "-"]
                            set pi 0
                            foreach ph $parent {
                                set match [lindex $mymatch $pi]
                                if {[regexp -nocase "unbounded" $match]} {
                                    set match 1
                                }
                                    
                                while {$match > 0} {
                                    set val [lindex $listprops $ii]
                                    set ret [::sth::sthCore::invoke stc::create $cls -under $ph "$val"]
                                    append myhandle "$ret "
                
                                    incr match -1
                                    if {$ii < [expr [llength $listprops]-1]} {
                                        incr ii
                                    }
                                }
                                incr pi
                            }
                        }
                    }
                }

                set children_cls($cls) 1
                set ::sth::pcep::handles_generated($cls) $myhandle
                foreach myhnd $myhandle {
                    set children [::sth::sthCore::invoke stc::get $myhnd -children]

                    foreach hnd $children {
                        set child [regsub {\d+$} $hnd ""]
                        set children_cls($child) 1
                        process_arg_by $child
                        append ::sth::pcep::handles_generated($child) " $hnd"
                    }

                    set index 0
                    foreach rel_hnd $rel_others {
                        set type [lindex $rel_types $index]
                        catch {::sth::sthCore::invoke stc::config $myhnd -$type $rel_hnd}
                    }
                }
                
                process_func $funcname $myhandle
            } ret ]} {
                puts "$cls cannot be created/configured, because : $ret"
            }
        } else {
            if {$mycls ne ""} {
                set index 0
                foreach rel_hnd $rel_others {
                    set type [lindex $rel_types $index]
                    if {$type ne "" && ![regexp {base-base|fake-fake} $type]} {
                        catch {::sth::sthCore::invoke stc::config $mycls -$type $rel_hnd}
                    }
                    incr index
                }
            }   
            
            if {![info exists ::sth::pcep::handles_generated($cls)]} {
                if {[info exist myUsersArgs(mode)] && [regexp -nocase "modify" $myUsersArgs(mode)]} {
                    if {$mycls ne ""} {
                        set ::sth::pcep::handles_generated($cls) $mycls
                    }
                }
            }
            if {![info exists ::sth::pcep::handles_generated($cls)]} {
                foreach match_rel $::sth::pcep::myclass2relation($cls_) {
                    if {[compare_cls $parent $match_rel]} {
                        continue
                    }
                    regexp { (.*?) } $match_rel match
                    set mymatch [split [string trim $match] "-"]
                    set pi 0
                    foreach ph $parent {
                        set match [lindex $mymatch $pi]
                        if {[regexp -nocase "unbounded" $match]} {
                            set match 1
                        }
                            
                        while {$match > 0} {
                            set ret [::sth::sthCore::invoke stc::create $cls -under $ph]
                            append myhandle "$ret "
        
                            incr match -1
                        }
                        incr pi
                    }
                        
                    set children_cls($cls) 1
                    set ::sth::pcep::handles_generated($cls) $myhandle
                    foreach myhnd $myhandle {
                        set children [::sth::sthCore::invoke stc::get $myhnd -children]

                        foreach hnd $children {
                            set child [regsub {\d+$} $hnd ""]
                            set children_cls($child) 1
                            process_arg_by $child
                            append ::sth::pcep::handles_generated($child) " $hnd"
                        }
                
                        set index 0
                        foreach rel_hnd $rel_others {
                            set type [lindex $rel_types $index]
                            catch {::sth::sthCore::invoke stc::config $myhnd -$type $rel_hnd}
                        }
                    }
                }
            }
        }
        set clslist [lsort -dictionary [array names ::sth::pcep::myclass2relation]]
        set myindex -1
        set myclsrmv ""
        set myrmvlst ""
        foreach check $clslist {
            regexp {(\d+\.).*} $check mymatch index
            if {$myindex != $index} {
                set myindex $index
                set myclsrmv $check
            } else {
                if {[regexp -all {\.} $myclsrmv] == 1} {
                    if {$myrmvlst == "" || ![regexp $myclsrmv $myrmvlst]} {
                        append myrmvlst "$myclsrmv "
                    }
                }
            }                
        }
        
        foreach rmv $myrmvlst {
            unset ::sth::pcep::myclass2relation($rmv)
        }
        if {$myrmvlst != "" } {
            set clslist [lsort -dictionary [array names ::sth::pcep::myclass2relation]]
        }
        incr i
        if {$i >= [llength $clslist]} {
            break
        }
    }
    
    foreach child [array names children_cls] {
        handle_condition $child
    }
}

proc ::sth::pcep::compare_cls {parent match_rel} {
    set pcls [regsub {\d+$} [lindex $parent 0] ""]
    if {[regexp -nocase "framework.ParentChild sources" $match_rel]} {
        set match_cls [lindex $match_rel 0]
        if {[regexp -nocase $pcls $match_cls]} {
            return false
        }
        
        if {[regexp -nocase "base" $match_cls]} {
            set clsfind [array names ::sth::Session::baseclass2relation -glob *\.$match_cls]
            if {$clsfind ne ""} {
                foreach rel $::sth::Session::baseclass2relation($clsfind) {
                    if {[regexp -nocase {base base$} $rel]} {
                        if {[regexp -nocase $pcls [lindex $rel 0]]} {
                            return false
                        }
                    }
                }
            }
        }
    }
    
    return true
}

proc ::sth::pcep::handle_condition {child} {
    if {[info exist ::sth::Session::classCondition($child)]} {
        set condition $::sth::Session::classCondition($child)
        
        set cond [split [string trim $condition] ","]
        set cond_cls [string tolower [lindex [split [lindex $cond 0] "."] 0]]
        if {[info exist ::sth::pcep::handles_generated($cond_cls)]} {
            set cond_cls_hnd $::sth::pcep::handles_generated($cond_cls)
            set cond_cls_param [lindex [split [lindex $cond 0] "."] 1]
            set op [lindex $cond 1] 
            set v [regsub {.*\.} [lindex $cond 2] ""]
            set value [::sth::sthCore::invoke stc::get $cond_cls_hnd -$cond_cls_param]
            if {[regexp -nocase "equal" $op]} {
                if {$value == $v} {
                    if {[info exist ::sth::Session::obj2ret($child)]} {
                        foreach keyret $::sth::Session::obj2ret($child) {
                            set values_bk ""
                            keylget ::sth::pcep::returnKeyedList $keyret values_bk
                            keylset ::sth::pcep::returnKeyedList $keyret [string trim "$values_bk $::sth::pcep::handles_generated($child)"]
                        }
                    }
                }
            }
        }
    } else {
        if {[info exist ::sth::Session::obj2ret($child)]} {
            foreach keyret $::sth::Session::obj2ret($child) {
                set values_bk ""
                keylget ::sth::pcep::returnKeyedList $keyret values_bk
                keylset ::sth::pcep::returnKeyedList $keyret [string trim "$values_bk $::sth::pcep::handles_generated($child)"]
            }
        }
    }
}

proc ::sth::pcep::process_func {funcname myhandle} {
    variable ::sth::Session::ApiArray
    variable ::sth::Session::prop2class
    
    foreach func [array names ::sth::Session::ApiArray] {
        if {$func == $funcname} {
            set prop2process $::sth::Session::ApiArray($func)
            set prop2process [split [string map [list ";" \0] $prop2process] \0]
            foreach myhnd $myhandle {
                set clsname [regsub {\d+$} $myhnd ""]
                if {![regexp -nocase "$clsname." $prop2process]} {
                    continue
                }
                foreach pp $prop2process {
                    if { $pp ne ""} {
                        set cls_option [string tolower [lindex $pp 0]]    
                        if {[info exist ::sth::Session::prop2class($cls_option)]} {
                            set proc_name [lindex $pp 1]
                            if {$proc_name eq "none"} {
                                continue
                            }
                            set cls [regsub {\..*} $cls_option ""]
                            set myoption [regsub {.*\.} $cls_option ""]
    
                            if {$myhandle ne ""} {
                                set myclass [regsub -all {\d+$} $myhnd ""]
                                if {$cls == $myclass} {
                                    set option_value [::sth::sthCore::invoke stc::get $myhnd -$myoption]
                                                            
                                    set parent [::sth::sthCore::invoke stc::get $myhnd -parent]
                                    $proc_name $parent $myhnd $option_value
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

proc ::sth::pcep::process_Usesif {device myprotocol ipversion} {
    #puts "$pcep_handle $ipversion "
    set usesif [::sth::sthCore::invoke stc::get $device -children-$ipversion\if]
    set old [::sth::sthCore::invoke stc::get $myprotocol -usesif-targets]
    foreach myif $usesif {
        set myvalue [::sth::sthCore::invoke stc::get $myif -Address]
        if {![regexp -nocase {^fe80::} $myvalue]} {
            if {$old ne ""} {
                if {![regexp $myif $old]} {
                    ::sth::sthCore::invoke stc::config $myprotocol -usesif-targets "$old $myif"
                }
            } else {
                ::sth::sthCore::invoke stc::config $myprotocol -usesif-targets "$myif"
            }
        }
    }
}

proc ::sth::pcep::process_Customtlv_Value {project mycustomtlv_hnd tlv_value} {
    if {$mycustomtlv_hnd ne ""} {
        if {[catch {binary scan [binary format H* $tlv_value] B* val}]} {
            set length [expr [string length $tlv_value] - [regexp -all " " $tlv_value]]
        } else {
            set length [expr int(1+[string length $val]/32.0)*4]
        }
        ::sth::sthCore::invoke stc::config $mycustomtlv_hnd -length $length
    }
}

proc ::sth::pcep::getValue_from_userArgs {myalias} {
    foreach prop_ [array names ::sth::pcep::userArgsArray] {
        set prop [regsub -all "_" $prop_ ""]
        if {[regexp -nocase $prop $myalias]} {
            return $::sth::pcep::userArgsArray($prop_)
        }
    }
    
    return ""
}

proc ::sth::pcep::get_specific_value_bymode {cls_option} {
    set mymode ""
    if {[info exist ::sth::pcep::userArgsArray(mode)]} {
        set mymode [string tolower $::sth::pcep::userArgsArray(mode)]
    }
    
    set cls [regsub {\..*} $cls_option ""]
    regexp {\.(.*)\.} $cls_option match myoption
    set myalias [regsub {.*\.} $cls_option ""]
    
    if {$mymode eq "enable"} {
        set option_value [getValue_from_userArgs $myalias]
        if {$option_value ne ""} {
            return $option_value
        } else {
            return "PCE"
        }
    } elseif {$mymode eq "add"} {
        set myhandle [lindex $::sth::pcep::userArgsArray(handle) 0]
        if {[regexp $cls $::sth::pcep::userArgsArray(handle)]} {
            set option_value [::sth::sthCore::invoke stc::get $myhandle -$myoption]
            return $option_value
        }
        
        catch {set myobj [::sth::sthCore::invoke stc::get $myhandle -children-$cls]} ret
        if {$myobj ne ""} {
            set option_value [::sth::sthCore::invoke stc::get $myobj -$myoption]
            return $option_value
        } else {
            while {$myhandle ne ""} {
                set myobj [::sth::sthCore::invoke stc::get $myhandle -parent]
                if {[regexp "^$cls\\d+$" $myobj]} {
                    set option_value [::sth::sthCore::invoke stc::get $myobj -$myoption]
                    return $option_value
                }
                set myhandle $myobj
            }
        }
    } elseif {$mymode eq "modify"} {
        set myhandle [lindex $::sth::pcep::userArgsArray(handle) 0]
        if {[regexp $cls $::sth::pcep::userArgsArray(handle)]} {
            if {[info exist ::sth::pcep::userArgsArray($myalias)]} {
                set option_value $::sth::pcep::userArgsArray($myalias)
                return $option_value
            } else {
                set option_value [::sth::sthCore::invoke stc::get $myhandle -$myoption]
                return $option_value
            }
        }
        
        catch {set myobj [::sth::sthCore::invoke stc::get $myhandle -children-$cls]} ret
        if {$myobj ne ""} {
            set option_value [::sth::sthCore::invoke stc::get $myobj -$myoption]
            return $option_value
        } else {
            while {$myhandle ne ""} {
                set myobj [::sth::sthCore::invoke stc::get $myhandle -parent]
                if {[regexp "^$cls\\d+$" $myobj]} {
                    set option_value [::sth::sthCore::invoke stc::get $myobj -$myoption]
                    return $option_value
                }
                set myhandle $myobj
            }
        }
    } 
    
    return "xxx"  
}

proc ::sth::pcep::process_func_key {funcname myhandle} {
    variable ::sth::Session::ApiArray
    variable ::sth::Session::prop2class
    
    set ret ""
    foreach func [array names ::sth::Session::ApiArray_key] {
        if {$func == $funcname} {
            set prop2process $::sth::Session::ApiArray_key($func)
            set prop2process [split [string map [list ";" \0] $prop2process] \0]

            foreach pp $prop2process {
                if { $pp ne ""} {
                    set proc_name [lindex $pp 1]
                    set cls_option [string tolower [lindex $pp 0]]  
                    set cls [regsub {\..*} $cls_option ""]
                    regexp {\.(.*)\.} $cls_option match myoption
                    set myalias [regsub {.*\.} $cls_option ""]
                    if {$myhandle ne ""} {
                        if {![info exist ::sth::pcep::option_value]} {
                            set ::sth::pcep::option_value [get_specific_value_bymode $cls_option]
                        }
                     
                        if {$::sth::pcep::option_value ne ""} {
                            append ret [$proc_name $myhandle $::sth::pcep::option_value]
                        } else {
                            return false
                        }
                    }
                }
            }
        }
    }
    
    return $ret
}

proc ::sth::pcep::process_key_role {myclass role_value} {
    set clslist "PcepProtocolConfig PceLspConfig PcepLspObject PcepSrpObject PcepIpv4EroToUpdateObject PcepIpv6EroToUpdateObject PcepIpv4ExplicitRouteParams \
					PcepIpv6ExplicitRouteParams PcepSREroObject PcepSRExplicitRouteParams PcepMetricListToUpdateObject \
					PcepBwToUpdateObject PcepLspaToUpdateObject Ipv4NetworkBlock Ipv6NetworkBlock \
                    StartDeviceInitiateCommandConfig StartDeviceUpdateCommandConfig StartDeviceReplyCommandConfig"   
    set clslist2 "PcepProtocolConfig PccLspConfig PcepLspObject PcepRPObject PcepIpv4EroObject PcepIpv6EroObject PcepIpv4ExplicitRouteParams \ 
                PcepIpv6ExplicitRouteParams PcepIpv4RroObject PcepIpv4ReportedRouteParams PcepIpv6RroObject \
                PcepIpv6ReportedRouteParams PcepSRRroObject PcepSRReportedRouteParams PcepSREroObject \
                PcepSRExplicitRouteParams PcepMetricListObject PcepBwObject PcepLspaObject Ipv4NetworkBlock Ipv6NetworkBlock \
                StartDeviceSyncCommandConfig StartDeviceDelegateCommandConfig StartDeviceRequestCommandConfig"
    
    if {[regexp -nocase $myclass $clslist] || [regexp -nocase $myclass $clslist2]} {
        set in 1
    } else {
        set in 0
    }
    
    if {[regexp -nocase "PCC" $role_value]} {
        set clslist $clslist2
    }
    
    if {[regexp -nocase $myclass $clslist] } {
        return true
    } else {
        if {!$in} {
            return true
        }
        return false
    }
}

set ::sth::pcep::pcepTable {
    ::sth::pcep::
    {   emulation_pcep_control
        {hname                          stcobj                 				 stcattr                          type                                                               priority          default      range           supported   dependency              mandatory   procfunc                       mode                  constants}
        {port_handle                    _none_                  			  _none_                          ALPHANUM                                                             2               _none_        _none_          true        _none_                  false       _none_                         _none_                 _none_}
        {handle                         _none_                  			  _none_                          ALPHANUM                                                             2               _none_        _none_          true        _none_                  false       _none_                         _none_                 _none_}
        {action                         _none_                  			  _none_   {CHOICES start_sessions stop_sessions establish_sessions initiate_lsp remove_delegate_lsp remove_initiate_lsp}           3          start_sessions   _none_          true        _none_                  true        _none_                         _none_                 _none_}
	}
    {   emulation_pcep_stats
        {hname                          stcobj                  stcattr                          type                                                priority          default       range           supported   dependency              mandatory   procfunc             mode                                         constants}
        {port_handle                    _none_                  _none_                          ALPHANUM                                                2               _none_       _none_          true        _none_                  false       _none_              _none_                                          _none_}
        {handle                         _none_                  _none_                          ALPHANUM                                                2               _none_       _none_          true        _none_                  false       _none_              _none_                                          _none_}
		{mode                           _none_                  _none_                      {CHOICES device_block_result port_result lsp_result lsp_block_result}    3               device_block_result   _none_          true        all                  false        _none_             _none_           								_none_}
    }
}

proc ::sth::emulation_pcep_control {args} {
	::sth::sthCore::Tracker "::sth::emulation_pcep_control" $args
    
    variable ::sth::pcep::userArgsArray
    variable ::sth::pcep::sortedSwitchPriorityList
    array unset ::sth::pcep::userArgsArray
    array set ::sth::pcep::userArgsArray {}
    
    set _hltCmdName "emulation_pcep_control"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::pcep::pcepTable $args \
                                                            ::sth::pcep:: \
                                                            emulation_pcep_control \
                                                            ::sth::pcep::userArgsArray \
                                                            ::sth::pcep::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::pcep::emulation_pcep_control_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing pcep protocol control : $err"
        return $returnKeyedList
    }
    
	keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}


proc ::sth::pcep::emulation_pcep_control_imp {returnKeyedList} {
	upvar $returnKeyedList myreturnKeyedList
    
    ::sth::sthCore::doStcApply
    set myaction [regsub -all "_" $::sth::pcep::userArgsArray(action) ""]   
	set handle_list [emulation_pcep_control_common]
	
	if {[regexp -nocase "remove_initiate_lsp" $::sth::pcep::userArgsArray(action)]} {
		set myaction "deletelsp"
	} elseif {[regexp -nocase "remove_delegate_lsp" $::sth::pcep::userArgsArray(action)]} {
		set myaction "removelsp"
	}
	::sth::sthCore::invoke stc::perform Pcep$myaction\Command -HandleList $handle_list
}

proc ::sth::pcep::emulation_pcep_control_common {} {
    variable ::sth::pcep::userArgsArray
		
	set handle_list ""
	if {[info exists ::sth::pcep::userArgsArray(handle)]} {
        set handles $::sth::pcep::userArgsArray(handle)
        foreach hnd $handles {
            set pcep [::sth::sthCore::invoke stc::get $hnd -children-PcepProtocolConfig]
            set handle_list [concat $handle_list $pcep]
        }
        
        if {$handle_list eq ""} {
            set handle_list $handles
        }
	} else {
		set port_list $::sth::pcep::userArgsArray(port_handle)
		foreach port $port_list {
			set devices [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
			foreach device $devices {
				set pcep [::sth::sthCore::invoke stc::get $device -children-PcepProtocolConfig]
				if {![regexp "^$" pcep]} {
					set handle_list [concat $handle_list $pcep]
				}
			}
		}
	}

	return $handle_list
}


proc ::sth::emulation_pcep_stats {args} {
    variable ::sth::pcep::userArgsArray
    variable ::sth::pcep::sortedSwitchPriorityList
    array unset ::sth::pcep::userArgsArray
    array set ::sth::pcep::userArgsArray {}
    
    set _hltCmdName "emulation_pcep_stats"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    if {[catch {::sth::sthCore::commandInit ::sth::pcep::pcepTable $args \
                                                            ::sth::pcep:: \
                                                            emulation_pcep_stats \
                                                            ::sth::pcep::userArgsArray \
                                                            ::sth::pcep::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::pcep::emulation_pcep_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get pcep stats : $err"
    }
    return $returnKeyedList
}

proc ::sth::pcep::emulation_pcep_stats_func {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::pcep::userArgsArray
	   	
	set num 1
	set mymode $::sth::pcep::userArgsArray(mode)
	if {[regexp -nocase "device_block_result" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
						 -ConfigType PcepProtocolConfig -resulttype PcepDeviceBlockResults]
        incr num
        
        set pcep_handle_list $::sth::pcep::userArgsArray(handle)
        foreach pcep_handle $pcep_handle_list {
            set device_result [::sth::sthCore::invoke stc::get $pcep_handle -children-PcepDeviceBlockResults]
        
            ::sth::sthCore::invoke stc::sleep 3
            if {$device_result ne ""} {
                set myresult [::sth::sthCore::invoke stc::get $device_result]
                set retVal {}
                foreach {attr val} $myresult {
                    keylset retVal $attr $val
                }
                keylset myreturnKeyedList $pcep_handle $retVal
            }
        }
	}
	if {[regexp -nocase "port_result" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
						 -ConfigType PcepProtocolConfig -resulttype PcepPortResults]
        incr num
        
        ::sth::sthCore::invoke stc::sleep 3
        set port_list $::sth::pcep::userArgsArray(port_handle)
		foreach port $port_list {
            set port_result [::sth::sthCore::invoke stc::get $port -children-PcepPortResults]

            if {$port_result ne ""} {
                set myresult [::sth::sthCore::invoke stc::get $port_result]
                set retVal {}
                foreach {attr val} $myresult {
                    keylset retVal $attr $val
                }
                keylset myreturnKeyedList $port $retVal
            }
        }
	}
	
	if {[regexp -nocase "lsp_result" $mymode]} {
        set myhnd_list $::sth::pcep::userArgsArray(handle)
        if {[regexp -nocase {PccLspConfig\d+} $myhnd_list]} {
            set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
                             -ConfigType PccLspConfig -resulttype PcepLspResults]
        } else {
            set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
                             -ConfigType PceLspConfig -resulttype PcepLspResults]
        }
        ::sth::sthCore::invoke stc::sleep 3
        incr num
        
        foreach myhnd $myhnd_list {
            set lsp_result [::sth::sthCore::invoke stc::get $myhnd -children-PcepLspResults]
    
            if {$lsp_result ne ""} {
                set myresult [::sth::sthCore::invoke stc::get $lsp_result]
                set retVal {}
                foreach {attr val} $myresult {
                    keylset retVal $attr $val
                }
                keylset myreturnKeyedList $myhnd.lsp_result $retVal
            }
        }
		incr num
	}
    
    if {[regexp -nocase "lsp_block_result" $mymode]} {
        set myhnd_list $::sth::pcep::userArgsArray(handle)
        
        if {[regexp -nocase {PccLspConfig\d+} $myhnd_list]} {
            set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType PccLspConfig -resulttype PcepLspBlockResults]
        } else {
            set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType PceLspConfig -resulttype PcepLspBlockResults]  
        }
		incr num
        ::sth::sthCore::invoke stc::sleep 3
        
        foreach myhnd $myhnd_list {
            set lsp_result [::sth::sthCore::invoke stc::get $myhnd -children-PcepLspBlockResults]
    
            if {$lsp_result ne ""} {
                set myresult [::sth::sthCore::invoke stc::get $lsp_result]
                set retVal {}
                foreach {attr val} $myresult {
                    keylset retVal $attr $val
                }
                keylset myreturnKeyedList $myhnd.lsp_block_result $retVal
            }
        }
	}
    
   	for {set i 1} {$i < $num} {incr i} {
		::sth::sthCore::invoke stc::unsubscribe [set resultDataSet$i]
	} 
}