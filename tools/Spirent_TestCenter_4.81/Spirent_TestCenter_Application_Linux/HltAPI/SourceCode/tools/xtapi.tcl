package provide xtapi 4.52

set stc_dir [file dirname [file join [pwd] [info script]]]
puts "xtapi Debug :: $stc_dir :: Spirent xtapi library was successfully loaded and initialized"

namespace eval ::xtapi {
    namespace export scriptrun_stak 
}

proc ::xtapi::process_args {args} {
    set str_args ""
    set num_args [llength $args]
    for { set i 0 } { $i < $num_args } { incr i } {
        set arg [lindex $args $i]
        if {[regexp {^-} $arg]} {
            # Remove the dash from the variable
            regsub {^-} $arg {} myargs
            append str_args "\"$myargs\":"
            incr i
    
            set value [lindex $args $i]
            if {[regexp " " $value]} {
                set myvalue ""
                if {[regexp {\{} $value]} {
                    foreach v $value {
                        set v [string trim $v]
                        set v1 [regsub -all " " $v "\",\""]
                        append myvalue "\[\"$v1\"\],"
                    }
                    set myvalue [string trimright $myvalue ","]
                } else {
                    set value [string trim $value]
                    set myvalue [regsub -all " " $value "\",\""]
                    set myvalue "\"$myvalue\""
                }
                append str_args "\[$myvalue\],"
            } else {
                append str_args "\"$value\","
            }
        }
    }
    set str_args [string trimright $str_args ","]
    set str_args "\{$str_args\}"
    return $str_args
}

proc ::xtapi::scriptrun_stak {api_name args} {
    if {[catch {
            set myargs [eval process_args $args]
            set reta [stc::perform spirent.xtapi.ScriptRunCommand -ApiName $api_name -InputArgs $myargs]]

            if {[regsub {.*-RunResult \{\"\{} $reta "" ret]} {
				regsub -all {\}\"\} -CommandName.*} $ret "" ret
				regsub -all { -} $ret "\\\n -" ret
            } else {
				regsub {.*-RunResult \{} $reta "" ret
				regsub -all {\} -CommandName.*} $ret "" ret
				regsub -all { -} $ret "\\\n -" ret
            }
          } retMsg]} {
        return -code 1 -errorcode -1 "exception during scriptrun_stak: $retMsg"
    }
    
	if {[regexp "Traceback (most recent call last)" $reta]} {
		return -code 1 -errorcode -1 "wrong return during scriptrun_stak: $reta"
	} elseif {[regexp {\-PassFailState PASSED} $reta]} {
		set myret [eval process_ret $ret]
		return $myret
    } else {
		return -code 1 -errorcode -1 "wrong return during scriptrun_stak: $reta"
    }
}

proc ::xtapi::process_ret {args} {
    set str_ret ""
	if {[catch {keylset str_ret status 1} err]} {
		return $args
	} else {
	    if {[catch {	
				set uargs [split $args ","]
				set num_args [llength $uargs]
				for { set i 0 } { $i < $num_args } { incr i } {
					set arg [lindex $uargs $i]
					if {[regexp {:} $arg]} {
						regexp -all {(.*)?\': \'(.*)} $arg match myargument myvalue
				
						regsub -all {\'|^\s} $myargument {} myargument
						regsub -all {\'|\s$} $myvalue {} myvalue
						keylset str_ret $myargument $myvalue
					}
				}} myret]} {
			return -code 1 -errorcode -1 "$myret, wrong when processing the return of scriptrun_stak: $args"
		}
		return $str_ret
	}
}
