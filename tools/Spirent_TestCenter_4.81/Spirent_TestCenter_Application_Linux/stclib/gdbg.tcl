# build version 1.9
# gdbg.tcl --
#
#   Graphical debug tools for use with the STC P2 automation interface.
#
# Copyright (c) 2006 by Spirent Communications, Inc.
# All Rights Reserved
#
# By accessing or executing this software, you agree to be bound 
# by the terms of this agreement.
# 
# Redistribution and use of this software in source and binary
# forms, with or without modification, are permitted provided
# that the following conditions are met: 
#
#   1. Redistribution of source code must contain the above 
#	   copyright notice, this list of conditions, and the
#	   following disclaimer.
#
#   2. Redistribution in binary form must reproduce the above
#	   copyright notice, this list of conditions and the
#	   following disclaimer in the documentation and/or other
#	   materials provided with the distribution.
#
#   3. Neither the name Spirent Communications nor the names of 
#	   its contributors may be used to endorse or promote 
#      products derived from this software without specific 
#      prior written permission.
#
# This software is provided by the copyright holders and
# contributors [as is] and any express or implied warranties, 
# limited to, the implied warranties of merchantability and 
# fitness for a particular purpose are disclaimed.  In no event 
# shall Spirent Communications, Inc. or its contributors be 
# liable for any direct, indirect, incidental, special, 
# exemplary, or consequential damages  (including, but not 
# limited to: procurement of substitute goods or services; loss 
# of use, data, or profits; or business interruption) however 
# caused and on any theory of liability, whether in contract, 
# strict liability, or tort (including negligence or otherwise) 
# arising in any way out of the use of this software, even if 
# advised of the possibility of such damage.
#

namespace eval ::stclib::gdbg {
	# Used by ssx
	variable ssxWin
        array set ssxWin {}
	variable exit_refresh
	variable tree_frame
	variable invocations 	0
	variable timestamp 	0
	namespace export update
	variable stoplabel  0
        variable ssxFlag    "false" ;#used for debug switch
	variable debugFlag  "false" ;#used for start|stop debug
        variable autotest   "false"
	variable helpFlag   "false"; #used to switch hover help
	
}

# stcdebug --
#
#   Set debug flag. If it is false, debug  request will be skipped
#
# Arguments:
#
#   flag         Indicate if debug switch is on   
#
# Results:
#
#   If it is false, debug  request will be skipped

proc ::stclib::gdbg::stcdebug {flag} {

	if {[string equal $flag on] || [string equal $flag On] || [string equal $flag ON]} {
	
		if {  $::stclib::gdbg::ssxFlag == "false" } {
                        package require BWidget
			set ::stclib::gdbg::ssxFlag true
                }
		return
	}
	if {[string equal $flag off] || [string equal $flag Off] || [string equal $flag OFF]} {
	  	if { $::stclib::gdbg::ssxFlag == "true" } {
            	if {$::stclib::gdbg::debugFlag == "true"} {
                		::stclib::gdbg::stop
            	}
			set ::stclib::gdbg::ssxFlag false
		}
               
		return
	}
	puts stderr {Parameter usage: stcdebug on|On|ON|off|Off|OFF}
	exit
}

# stchelp --
#
#   Set hover help flag. If it is set on, hover help will be added.
#
# Arguments:
#
#   flag         Indicate if hover help switch is on   
#
# Results:
#
#   If it is on, hover help will be loaded.

proc ::stclib::gdbg::stchelp {flag} {

	if {[string equal $flag on] || [string equal $flag On] || [string equal $flag ON]} {
		if {  $::stclib::gdbg::helpFlag == "false" } {
			set ::stclib::gdbg::helpFlag true
                }
		return
	}
	if {[string equal $flag off] || [string equal $flag Off] || [string equal $flag OFF]} {
                if { $::stclib::gdbg::helpFlag == "true" } {            
			set ::stclib::gdbg::helpFlag false
		}
		return
	}
	puts stderr {Parameter usage: stchelp on|On|ON|off|Off|OFF}
	exit
}

# ::stclib::gdbg::start --
#
#   Start script explorer and wait for ::stclib::gdbg::update
#
# Arguments:
#
#   None
#
# Results:
#
#   None
proc ::stclib::gdbg::start {args} {
	if {[string equal -nocase $args [concat -test auto]] || [string equal $args ""]} {
		if {  $::stclib::gdbg::ssxFlag == "false"  || $::stclib::gdbg::debugFlag == "true"} {
			return
		}
		set test "MANUAL"
		foreach param [split $args -] {
			regexp -nocase {test[\s]+([^\s]+)\s*} $param match test
		}
		# test = AUTO|MANUAL
		if {"AUTO" == [string toupper $test]} {
			set ::stclib::gdbg::autotest "true"
			puts "gdbg started with autotest"
		} else {
			set ::stclib::gdbg::autotest "false"
			#puts "gdbg started"
		}
    
		set ::stclib::gdbg::debugFlag true

		wm withdraw .
		wm protocol . WM_DELETE_WINDOW { exit }
    
		#create debug window
		stclib::gdbg::ssx
	} else {
		puts stderr {Parameter usage: "::stclib::gdbg::start [-test auto]"}
		exit
	}
}

proc ::stclib::gdbg::stop {} {
	if {  $::stclib::gdbg::ssxFlag == "false"  || $::stclib::gdbg::debugFlag == "false"} {
		return
	}
        destroy .ssx
        set ::stclib::gdbg::debugFlag "false"
        set ::stclib::gdbg::exit_refresh "true"
        if {[winfo exists .sst]==0 && [winfo exists .ssx]==0} {
                if {[file exists $::stclib::bw::filename]!=0} {
                        file delete -force $::stclib::bw::filename
                }
                exit
        }
    
    	set ::stclib::gdbg::exit_refresh "true"
    
	set ::stclib::gdbg::debugFlag false
	update idletask
	#puts "gdbg stopped"
}

#
# ::stcx::update --
#
#   BLL explorer tree synchronization routine. When invoked, will update the explorer display
#   and pause the users script until the continue button is pressed.
#
# Arguments:
#
#   None or -pause true|false -label $labelString
#
# Results:
#
#   The system explorer frame is refreshed
#
# Dependencies:
#
#   Uses the stcx::bll and stcx::bw packages.
#
# Revision history:
#
#   2006-09-19  john.mclendon@spirentcom.com - First cut.
#
#

proc ::stclib::gdbg::update { { args } } {
        set flag [regexp {(^-label(([\s][\d]*)|[\s]*)[\s]-pause[\s](true|false)$)|((^-pause[\s](true|false)[\s]-label(([\s][\d]*)|[\s]*))$)|(^idletask$)} $args]
        if {$flag == 0} {
           puts stderr {Parameter usage: "::stclib::gdbg::update -pause true|false -label [Numbers]" }
           exit     
        }
    	variable ssxWin
    
	if {  $::stclib::gdbg::ssxFlag == "false"  || $::stclib::gdbg::debugFlag == "false"} {
		return
	}
	#set breakpoint label
	set pause "true"
	set label 0
	foreach param [split $args -] {
		regexp {^label[\s]+([^\s]+)\s*} $param match label
		regexp {^pause[\s]+(true|false)} $param match pause
                #if {[$labelFlag == 0] && [$pauseFlag == 0]} {
                        #puts stderr {Parameter usage: "::stclib::gdbg::update -pause true|false -label [string]"}
                #        exit
                #}
	}
    	incr ::stclib::gdbg::stoplabel
	if {$label == 0} {
        	set breaklabel $::stclib::gdbg::stoplabel
	} else {
        	set breaklabel $label
	}	
    	$ssxWin(status) configure -text "$breaklabel"

    	incr ::stclib::gdbg::invocations
    	$::stclib::gdbg::timestamp configure -text "[clock format [clock seconds] -format %T]" 

	#save call stack
	set callStack {}
	for {set j [expr [info level]-1]} {$j>0} {incr j -1} {
		lappend callStack [info level $j]
	}
   	set items "call stacks: "
	#Format call stack as ""function<==evoke function..."
	if {[set callStackDeep [llength $callStack]]!=0} {
		set i 0
		foreach item $callStack {
			incr i
			if {$i<$callStackDeep} {
				set items [concat [concat $items $item] { <== }]
			} else {
				set items [concat $items $item]
			}
		}
        	$ssxWin(can) itemconfigure $ssxWin(stack) -text $items 
	} else {
		$ssxWin(can) itemconfigure $ssxWin(stack) -text [concat $items "none"]
	}

    	#get scope filter object
    	set scope $ssxWin(scope)
		set temp [$scope get]
    	if {[info exists ::TIMESTS_SWITCH ] && $::TIMESTS_SWITCH == "on"} {
        	set getObjectStart [clock seconds]
   	}
	set templist [concat All [::stclib::bll::getObjects]]
    	if {[info exists ::TIMESTS_SWITCH ] && $::TIMESTS_SWITCH == "on"} {
        	set getObjectEnd [clock seconds]
        	puts "getObjects cost [expr $getObjectEnd - $getObjectStart]"
    	}
	$scope configure -values $templist
	
	#draw tree
	#check if the current object does not exist any more
	if {[lsearch -exact $templist $temp]==-1} {
		$scope configure -text All
		set filter All
	} else {
		$scope configure -text $temp
		set filter $temp
	}	
    	$::stclib::gdbg::tree_frame populate [::stclib::bll::treeWalk $filter] $filter
    
    	::update idletasks
    	after 100
    	#if { [ string equal "nowait" "$flag" ] } {
    	#    return
    	#}
	if {$pause == "false" || $::stclib::gdbg::autotest == "true"} {
		return
	}
    	set ::stclib::gdbg::exit_refresh false
    	$ssxWin(cont) configure -state normal
    	vwait ::stclib::gdbg::exit_refresh
}

#
# stclib::gdbg::continueExec --
#
# Private proc to cause the users script to continue after being paused
# The stclib::gdbg::update proc performs a vwait on the variable stclib::gdbg::exit_refresh.
# This proc simply writes to that variable.
#
#
# Arguments:
#
#   None
#
# Results:
#
#   None
#
# Dependencies:
#
#   Uses the gdbg package.
#
# Revision history:
#
#   2006-08-19  john.mclendon@spirentcom.com - First cut.


proc ::stclib::gdbg::continueExec {} {
    	variable ssxWin
    	$ssxWin(cont) configure -state disabled
    	set ::stclib::gdbg::exit_refresh "true"
}



# ::stclib::gdbg::ssx --
#
#   BLL explorer tree display. Can be used either to display a stand-alone
#   window, or to create the tree in frame within the caller's application.
#
# Arguments:
#
#   frame   Optional. Name of the frame containing the tree and associated 
#           controls to be created. If omitted then a stand-alone top level
#           window is created.
#
# Results:
#
#   A frame containing the BLL tree is created and either returned to the 
#   caller or mapped as a stand-alone window. 
#
# Dependencies:
#
#   Uses the stclib::bll and stclib::bw packages.
#
# Revision history:
#
#   2006-07-13  john.morris@spirentcom.com - First cut.
#
#   2006-09-06  john.morris@spirentcom.com - Packagized
#
#   2006-09-09  john.morris@spirentcom.com - Add embedded or stand-alone option
#
#   2006-11-14  john.mclendon@spirentcom.com - Added buttons/counters

proc ::stclib::gdbg::ssx {{frame ""}} {
    
    	# If no frame was specified, create a new top level frame. Otherwise
    	# just use the one requested.
    
    	# McLendon
    	if {$frame eq ""} {
        	set frame [Toplevel ".ssx" "500x500+0+0"]
    		wm title	 $frame "Spirent Script Explorer"
    	} else {
        	frame $frame
    	}
    
    	variable ssxWin     	
    
    	wm protocol  $frame WM_DELETE_WINDOW {
    
                
                destroy .ssx ;
                set ::stclib::gdbg::debugFlag "false"
                set ::stclib::gdbg::exit_refresh "true"
                    
                    
                if {[winfo exists .sst]==0 && [winfo exists .ssx]==0} {
                        if {[file exists $::stclib::bw::filename]!=0} {
                                
                                file delete -force $::stclib::bw::filename
                                
                        }
                        
			exit
                }
                if {$::stclib::gtrace::traceFlag == "false"} { wm deiconify .}
        } 

    	set top_frame [frame $frame.f]
    	set ::stclib::gdbg::tree_frame [::stclib::bw::bllTree $top_frame.t]
	set call_frame [frame $top_frame.call -height 40]
	set buts1 [frame $top_frame.buts1]
	set labels [frame $top_frame.labels]
	#Continue button should be disabled by default
	#until it reaches ::stclib::gdbg::update command
	set cont [Button $buts1.cont -text "Continue"  \
				    -command ::stclib::gdbg::continueExec ]
	$cont configure -state disabled
	set ssxWin(cont) $cont	
	
	set invoke [Label $labels.label -text "Refresh Count:"  ]
	set counter [Label $labels.counter -fg red -textvariable ::stclib::gdbg::invocations ]
	set tlabel [Label $labels.tlabel -text "Last update:"  ]
	set ::stclib::gdbg::timestamp [Label $labels.timestamp -fg red -text "[clock format [clock seconds] -format %T]" ]
	set statuslabel [Label $labels.statusLabel -text "Label:"  ]
	set status [label $labels.status -fg red -text ""]
  	set ssxWin(status) $status
	
	set scope [ComboBox $buts1.scope -autocomplete true -autopost true -values [concat All [::stclib::bll::getObjects]]]
	$scope configure -text All -width 40 -height 30
	$scope configure -modifycmd "::stclib::gdbg::narrowScope $::stclib::gdbg::tree_frame $scope"
	bind $scope <Return> {::stclib::gdbg::narrowScope $::stclib::gdbg::tree_frame $scope}
    	set ssxWin(scope) $scope
	
	set can [canvas $call_frame.canvas -height 40]
	set stack [$can create text 20 15 -anchor nw]
	$can itemconfigure $stack -justify left -fill red -text "null" -font {size 10}
    	set ssxWin(stack) $stack
    	set ssxWin(can) $can
		
    
##############################################################33
	 
        pack $scope -side left -expand false -pady 1m -padx 1m   
        pack $cont -side left -expand false -pady 1m -padx 1m
    
        pack $invoke -side left -expand false -pady 2m
        pack $counter -side left -expand false -pady 0m
        pack $tlabel -side left -expand false -pady 2m
        pack $::stclib::gdbg::timestamp -side left -expand false -pady 0m
        pack $statuslabel -side left -expand false -pady 2m
        pack $status -side left -expand false -pady 1m -padx 1m
        
        pack $buts1 -side top -fill x
        pack $labels -side top -fill x
        pack $::stclib::gdbg::tree_frame -side top -fill both -expand true
        pack $call_frame -side top -fill both -expand false
        pack $can -side left -expand false
        pack $top_frame -fill both -expand true
    
    
        $::stclib::gdbg::tree_frame populate [::stclib::bll::treeWalk]

        set ::stclib::gdbg::invocations 1
    
        return $frame
}


# ::stclib::gdbg::Toplevel --
#
#   Private utility to creates a top level window.
#
# Arguments:
#
#   frame       Name of the toplevel frame to be created.
#
#   geometry    Window size and placement
#
#   minx        Minimum X size to allow
#
#   miny        Minimum Y size to allow
#
# Results:
#
#   The frame handle.

proc ::stclib::gdbg::Toplevel {name \
                    {geometry "450x600+0+0"} {minx 400} {miny 400}} {

        # Make sure this toplevel does not already exist.
                                        
        catch {
                destroy $name;
                #set ::stclib::gdbg::exit_refresh "true"
        }
    
    # See if Tk is already present. If not, load it but then hide
    # the default toplevel window. If Tk is already present then
    # do nothing - we are running under some Tk app that is probably
    # doing its own thing with the default window.
    
        if {![info exists ::tk_version]} {
            package require Tk
            wm withdraw .
        }
        toplevel     $name
        wm protocol  $name WM_DELETE_WINDOW [list catch "destroy $name"]
        #wm withdraw  $name
        wm geometry  $name $geometry
        wm minsize   $name $minx $miny
        #wm deiconify $name
        return $name
}

# narrowScope --
#
#   Narrow down tree objects according to filter. 
#
# Arguments:
#
#   tree_frame   Tree 
#   scope        The scope is the object name which is to be shown.
#
# Results:
#
#   None

proc ::stclib::gdbg::narrowScope {tree_frame scope} {
	set filter [$scope get]
	if {[string equal $filter All]} {
		$tree_frame populate [::stclib::bll::treeWalk system1]
		return
	}
	#if {![llength $::stclib::gdbg::tree]} {
	#}
		
	if {$filter!=""} {
		$tree_frame populate [::stclib::bll::treeWalk $filter] $filter
	}
}



