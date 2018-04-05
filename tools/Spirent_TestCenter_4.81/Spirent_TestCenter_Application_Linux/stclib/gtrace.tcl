# build version 1.9
# gtrace.tcl --
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

namespace eval ::stclib::gtrace {
		
	variable command_count	0
	variable error_count	0
	variable trace_frame
	
	variable sstFlag       "false";  #used for trace switch
	variable traceFlag     "false";  #used for start|stop trace
	
	
	#package require ::stclib::bw
}

proc ::stclib::gtrace::sst {{frame ""}} {
	
	# If no frame was specified, create a new top level frame. Otherwise
	# just use the one requested.
	
	if {$frame eq ""} {
		set frame [::stclib::gdbg::Toplevel ".sst" "600x800-0+0"]        
		wm title $frame "Spirent Script Trace"
	} else {
		frame $frame
	}
	   

	set top_frame [frame $frame.f]
	set trace_frame [::stclib::bw::traceFrame $top_frame.t]

	set buts1 [frame $top_frame.buts1]
	set buts2 [frame $top_frame.buts2]
	
	set cmds [Label $buts1.label -text "Commands:" -font {-size 12  } ]
	set cmd_cnt [Label $buts1.counter -textvariable ::stclib::gtrace::command_count -font {-size 12 } ]
	set errs [Label $buts2.label -text "Errors:" -font {-size 12 } ]
	set err_cnt [Label $buts2.counter -textvariable ::stclib::gtrace::error_count -font {-size 12 } ]

	
	set save [button $buts1.save -text "SaveToFile" -font {-size 12} -command  ::stclib::gtrace::saveCommandsToFile  ]
	           
	
	pack $cmds -side left -expand false -pady 2m
	pack $cmd_cnt -side left -expand false -pady 0m
	pack $errs -side left -expand false -pady 2m
	pack $err_cnt -side left -expand false -pady 0m
	pack $buts1 -side top -fill x 
	pack $buts2 -side top -fill x 
	pack $top_frame -side top -fill both -expand true
	# Added by Sherwin to popluate the two button.
	pack $save   -side right -expand false -pady 2m -padx 2m
	set ::stclib::gtrace::command_count 0
	set ::stclib::gtrace::error_count 0

	pack $trace_frame -fill both -expand y
 
   
	$trace_frame hook ::stc::*
	$trace_frame unhook ::stc::help
	$trace_frame unhook ::stc::get
	set ::stclib::gtrace::trace_frame $trace_frame
	wm protocol $frame WM_DELETE_WINDOW {
		
		
		$::stclib::gtrace::trace_frame unhook ::stc::*
		destroy $::stclib::gtrace::trace_frame
		destroy .sst
		set ::stclib::gtrace::traceFlag false
		
		if {[winfo exists .sst]==0 && [winfo exists .ssx]==0} {
			file delete -force $::stclib::bw::filename
			exit
		}
		 
		
	}
	
	return $frame
}


# author: D.Xu
# date:
#       05/2007: 
#       end 05/2007
#reason: 
#Adding a function button to save the executed commands for a file
#name: 
# ::stclib::gtrace::saveCommandsToFile --
#function:
# Save the command records to the appoint file
#  
# Arguments:
#   None 
# Results:
# Return the full filename of the save commands file
# History:
# 2007-05-15 First cut -- Dean Xu
# 2007-05-16 Reimplemented the function to save the command to file.

proc ::stclib::gtrace::saveCommandsToFile {} {

	set types {
		{"Text files"		{.tcl }	}
		{"Text files"		{}		TEXT}
		{"All files"		*}
	}
	set file ""
	set file [tk_getSaveFile -filetypes $types  \
		-initialfile CommandsFile -defaultextension .tcl]
	if { $file == "" } {
		 return 0
	} else {
		if {[file exists $::stclib::bw::filename]==0} {
			if {[file exists $file]==0 } {
				set tempfile [ open $file w+ 0666]
				close $tempfile
			} else {                        
				return $file
			}
		} else {
			set newfile [open $file w+ 0666]
			
			set currentfile [open $::stclib::bw::filename r 0666]
			while { [gets $currentfile line] >=0 } {
			puts $newfile $line
			}
			
			close $newfile
			close $currentfile
			#file delete -force ./stcTraceCommand.txt
		}
	}
	return $file
}







# Author: 
#       Sherwin song
#
# Date:
#       2007-10-18
# Name: 
#
# ::stclib::gtrace::start --
#
# Function:
#
# Start the trace tool to record the commands related with STC.
#  
# Arguments:
#
# None
#
# Results:
#
# None
#

proc ::stclib::gtrace::start {  } {

	if {  $::stclib::gtrace::sstFlag == "false"  || $::stclib::gtrace::traceFlag == "true"} {
		return
	}
	
	set ::stclib::gtrace::traceFlag "true"
	wm withdraw . 
		  
}

# Author: 
#       Sherwin song
#
# Date:
#       2007-10-18
# Name: 
#
# stclib::gtrace::stop  --
#
# Function:
#
# Stop the trace windows
#  
# Arguments:
#
#   None
#
# Results:
#
# None
#

proc ::stclib::gtrace::stop {  } {
	
	if {  $::stclib::gtrace::sstFlag == "false"  || $::stclib::gtrace::traceFlag == "false"} {
		return
	}
	if { $::stclib::gtrace::sstFlag == "true" } { 
	  	set ::stclib::gtrace::traceFlag "false"
	}
	
}


# Author: 
#       Sherwin song
#
# Date:
#       2007-07-17
# Name: 
#
# stctrace  --
#
# Function:
#
# Start up the trace windows
#  
# Arguments:
#
#   token: "on","On" or "ON" represents to start up the trace window.
#
# Results:
#
# None
#

proc ::stclib::gtrace::stctrace { token } {
	

  	if { ($token == "on" ) || ($token == "On") || ($token == "ON" ) } {
	  	if { $::stclib::gtrace::sstFlag == "false" } {
			package require BWidget
			set ::stclib::gtrace::sstFlag  "true"
			::stclib::gtrace::sst
		}  
		
		return
 
	}
   
  	if { ($token == "off" ) || ($token == "Off") || ($token == "OFF" ) } {
	  	if { $::stclib::gtrace::sstFlag == "true" } {
	  		set ::stclib::gtrace::sstFlag  "false"
	  	}
		
	  	return
	}

   	puts stderr {Parameter usage: stctrace on|On|ON|off|Off|OFF}
   	exit
}

