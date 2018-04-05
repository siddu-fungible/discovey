#
# telnet.tcl --
#
#   Telnet package for communication with remote hosts. Based on
#   Expect, but with a more usable API.
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

package require Expect

namespace eval ::stclib::telnet {
	variable spawn_id
	variable timeout
	variable prompt
	variable printStdOut
	variable printLog
	variable logFileName
	variable mode
	variable EXPECTMODE
	variable PROMPTMODE
	namespace export init
}

# ::stclib::telnet::init --
#
#   Initialize the variables used internally by the telnet package.
#
# Arguments:
#
#   None
#
# Results:
#
#   The internal variables used by the telnet package are initialized.

proc ::stclib::telnet::init {} {
	variable spawn_id       ""
	variable timeout        10
	variable prompt         ""
	variable printStdOut    1
	variable printLog       1
	variable logFileName    "stctelnet.log"
	variable EXPECTMODE     0
	variable PROMPTMODE     1
	variable mode           $PROMPTMODE
}

#
# ::stclib::telnet::open --
#
#   Opens a telnet session to the given IP address.
#
# Arguments:
# 
#   server      ip address
#
#   user        login name. Put "" if login name is not required
#
#   pass        password
#
#   args        optional tagged arguments:
#
#			    -prompt (string) - The next prompt that user will expect after user login successfully
#
#				-passwordPrompt (string) - The password prompt that the user
#										 expect after login name is sent
#
#               -printToScreen (boolean) - If true, the program dumps out everything to the screen.
#                                         If false the program will suppress the output.
#
#               -printToLog (boolean) - If true the program will print the output to stctelnet.log.
#                                       If false, the program will not print to the log file. The
#                                       file will be overwritten for each script.
#
#               -timeout (integer) - specify the time (in second) for the program to wait
#								 		  for response.
# Results:
#
#   The telnet session is started, the login exchange is done, and the Expect 
#   session information (spawn_id) is noted for future use.

proc ::stclib::telnet::open {server user pass args} {
	global spawn_id
	set prompt      ""
	set passPrompt  ""
	set port        23
	set printStdOut 1
	set timeout     10

	foreach {tag varName} {
    	"-prompt"           prompt
    	"-timeout"          timeout
    	"-passwordPrompt"   passPrompt
    	"-port"             port
    	"-printToScreen"    printStdOut
    	"-printToLog"       ::stclib::telnet::printLog
	} {
      	set f [lsearch -exact $args $tag]
 	    if {$f > -1} {
     	    set $varName [lindex $args [expr $f + 1]] 
        }
    }

	# Debug code - switch this off for release
	
	if {1} {
	    puts "prompt = $prompt"
	    puts "timeout = $timeout"
	    puts "passwordPrompt = $passPrompt"
	    puts "port = $port"
	    puts "printStdOut = $printStdOut"
	    puts "printLog = $::stclib::telnet::printLog"
    }
    
	spawn telnet $server $port
	if {$::stclib::telnet::printLog} {
		# if {[file exist $::stclib::telnet::logFileName]} {
		#     file delete -force $::stclib::telnet::logFileName
		# }
		exp_internal -f $::stclib::telnet::logFileName 0
	}
	
	log_user $printStdOut
	set ::stclib::telnet::printStdOut $printStdOut
	
	set ::stclib::telnet::spawn_id $spawn_id
	after 2000
	if {[string length $user] != 0} {
		exp_send "$user\r"
		expect "$passPrompt"
		exp_send "$pass\r"
		expect "$prompt"
	} else {
		exp_send "$pass\r"
		expect "$prompt"
	}

}


# ::stclib::telnet::send --
#
#   Sends a message on an opened telnet session. 
#
#   There are two modes in this command : Prompt Mode and Expect Mode. The Prompt 
#   mode will dump out everything from the buffer to the return value. The Expect
#   mode will grab the string pattern that is specified in the -expect attribute.
#
# Arguments:
#
# 	command     the command that user wants to send in Telnet
#
#   args        optional tagged arguments:
#
#				-prompt 			= The next prompt that user will expect after the 
#										  command is sent. If this attribute is set, Prompt
#										  mode is enabled.
#
#				-expect 			= The expect string that the user will expect after the
#										  command is set. If this attribute is set, Expect mode
#										  is enabled.
#
#				-printToLog 		= the value is 1 or 0. If 1 is set, the program will
#										  print the output to stctelnet.log. If 0 is set, the
#										  program will not print to the log file. The file
#										  will be overwritten for each script
#.
#				-timeout 			= specify the time (second) for the program to wait
#								 		  for response.
#
#				-printToScreen 	= the value is 1 or 0. If 1 is set, the program
#									 	  dump out everything to the screen. If 0 is set, 
#									 	  the program will suppress the output.
#
#				-nextPagePrompt		= if the -scrollPage is specified. User need to input waitPrompt
#										  value to make the program to scroll the page automatically.
# Results:
#
#   Returns the response from the remote telnet host.

proc ::stclib::telnet::send {command args} {
	global spawn_id
	# Setup local variables
	set prompt "*?"
	set result ""
	set isMoreData 0
	set expectString ""
	set waitString ""
	set prompt ""
	set hasPromptFlag 0
	set hasExpectFlag 0
	set hasStdOut $::stclib::telnet::printStdOut
	set printStdOut 1	


  	set f [lsearch -exact $args "-prompt"]
  	if {$f > -1} {
  		# If prompt attribute is specified, prompt mode will be used
  		set prompt [lindex $args [expr $f + 1]]
  		set hasPromptFlag 1 
  		set ::stclib::telnet::MODE $::stclib::telnet::PROMPTMODE
  	}

  	# Check -expect attribute      	
  	set f [lsearch -exact $args "-expect"]
  	if {$f > -1} {
  		# If expect attribute is specified, expect mode will be used
  		set prompt [lindex $args [expr $f + 1]]
  		set ::stclib::telnet::MODE $::stclib::telnet::EXPECTMODE
  		set hasExpectFlag 1
  	}

  	# Check -timeout attribute       	
  	set f [lsearch -exact $args "-timeout"]
  	if {$f > -1} {
  		set timeout [lindex $args [expr $f + 1]] 
  	}
  	
  	# Check -printStdOut attribute    
  	set f [lsearch -exact $args "-printToScreen"]
  	if {$f > -1} {
  		set printStdOut [lindex $args [expr $f + 1]] 
  		set ::stclib::telnet::printStdOut 1
  		#set hasStdOut $::stclib::telnet::printStdOut	
		set hasStdOut 1
	}
  	
  	# Check -printStdOut attribute    
  	set f [lsearch -exact $args "-printToLog"]
  	if {$f > -1} {
  		set ::stclib::telnet::printLog [lindex $args [expr $f + 1]]
  	}
	
	# Enable redirect log feature
	if {$::stclib::telnet::printLog == 1} {
		# Expect function to redirect log file to stctelnet.log
		exp_internal -f $::stclib::telnet::logFileName 0
	}
	
	# Enable suppress output
	if {$hasStdOut == 0} {
		set logValue $::stclib::telnet::printStdOut
	} else {
		set logValue $printStdOut
	}
	
	# Expect function to enable suppress output
	log_user $logValue
	
	# If prompt is not specified, the prompt from the last EX_TelnetSendCommand will be used 
	if {$hasPromptFlag == 0 && $hasExpectFlag == 0} {
		set prompt $::stclib::telnet::prompt 
		set ::stclib::telnet::MODE $::stclib::telnet::PROMPTMODE
	} else {
		set ::stclib::telnet::prompt $prompt
	}
	
	# If the return prompt is not more than 1 page, the program will just send the command and expect
	# the return string
	if {!$isMoreData} {
		exp_send "$command\r"
		# Expect different string
		if {$::stclib::telnet::MODE == $::stclib::telnet::PROMPTMODE} {
			expect "$prompt"
		} else {
			expect "$prompt"
		}
		# If it is a prompt mode, we expect the returned string from the buffer (no matter we find a matched string or not)
		if {$::stclib::telnet::MODE == $::stclib::telnet::PROMPTMODE} {
		    if {[catch {set result $expect_out(buffer)} iErr] == 1} {
			    set result ""
			    return $result
		    } else {
			    return $result
		    }
		} else {
		# If it is a expect mode, we expect the returned string
			if {[catch {set result $expect_out(0,string)} iErr] == 1} {
			    set result ""
			    return $result
		    } else {
			    return $result
		    }
		}
	} 
}

# ::stclib::telnet::close --
#
#   Terminates the telnet session.
#
# Arguments:
#
#   None
#
# Result:
#
#   The telnet session is closed.

proc ::stclib::telnet::close {} {
	global spawn_id
	exp_close
}

# Initialize the telnet structure
::stclib::telnet::init

#########################################################################

package provide stclib::telnet 0.0.1