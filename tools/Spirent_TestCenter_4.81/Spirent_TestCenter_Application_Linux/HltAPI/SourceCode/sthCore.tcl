# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

######################################################################
### This file contains the sth::sthCore functions used by all modules.
### It loads the TCL tables into internal tables for each command
######################################################################
#package require yaml
#package require huddle

namespace eval ::sth::sthCore:: {
    variable SUCCESS 1
    variable FAILURE 0
    variable DEFAULT_HUDDLE
}

proc ::sth::sthCore::ProcessDefaultYamlFile {} {
    global env
    set dirname [file join [file dirname [info script]] "default"]
    if {[info exists env(DEFAULTYAML_DIR)]} {
        set dirname $env(DEFAULTYAML_DIR)
    }
    set dirname [regsub -all {\\} $dirname "/"]

    variable DEFAULT_HUDDLE
    foreach myfile [lsort -dictionary -increasing [glob -nocomplain $dirname/*.yaml]] {
        set myhuddle [::yaml::yaml2huddle -file $myfile]
        puts_msg "Loading Default yaml file: $myfile"
        if {[info exist DEFAULT_HUDDLE]} {
            set DEFAULT_HUDDLE [huddle combine $myhuddle $DEFAULT_HUDDLE]
        } else {
            set DEFAULT_HUDDLE $myhuddle
        }
    }
}

###/*! \ingroup sthCore functions
###\fn procedure ::sth::sthCore::Tracker ( cmd args )
###\return $::sth::sthCore::SUCCESS
###
### This function accomplishes the followng two tasks:
### a) tracks each hltapi function call by sending a message "$cmd $args" to CISCO UDP tracker server
### b) call ::sth::sthCore::log hltcall "$cmd $args"
###
###\param [in] cmd: its value the name of the hltapi function being tracked or logged
###\param [in] args: the args of the hltapi call specfied by the user.
###
###\warning None
###\author Davison Zhang
###*/
###
### ::sth::sthCore::tracker (cmd args)
proc ::sth::sthCore::Tracker { cmd args } {
    variable ::sth::sthCore::SUCCESS
    variable DEFAULT_HUDDLE
    upvar 1 args myarg
    if {[info exist ::DEFAULT_YAML]} {
        catch {
            set default [yaml::yaml2huddle $::DEFAULT_YAML]
            if {[info exist DEFAULT_HUDDLE]} {
                set DEFAULT_HUDDLE [huddle combine $default $DEFAULT_HUDDLE]
            } else {
                set DEFAULT_HUDDLE $default
            }
        } msg
    }

    if {[info exist DEFAULT_HUDDLE]} {
        catch {
            set myns ""
            set mycmd [regsub "::sth::|sth::" $cmd ""]
            set namespaces [namespace children ::sth]
            foreach ns $namespaces {
                set tables [split [info vars $ns\::*Table]]
                foreach table $tables {
                    if {[catch {
                        if {[IsCmdInTCLTable [set $table] $ns $mycmd]} {
                            set myCmdTableName $table
                            set flag $myCmdTableName\_Initialized
                            if { ![info exists $flag] } {
                                variable $flag
                                set $flag true
                                ::sth::sthCore::InitTableFromTCLList [set $table]
                            }
                            set myns $ns
                            break
                        }
                    } err]} {
                        set i $err
                    }
                }
                if {$myns != ""} {
                    break
                }
            }
            
            set myhuddle [huddle get $DEFAULT_HUDDLE $mycmd]
            set append_args ""
            foreach key [huddle keys $myhuddle] {
                if {![regexp "\\-$key" $myarg]} {
                    set myvalue [string trim [huddle strip [huddle get $myhuddle $key]] "\n"]
                    set value [set $myns\::$mycmd\_type($key)]
                    if {[regexp -nocase "CHOICE" $value]} {
                        if {$myvalue eq "1" && ![regexp -nocase $myvalue $value]} {
                            set myvalue "true"
                        }
                        if {$myvalue eq "0" && ![regexp -nocase $myvalue $value]} {
                            set myvalue "false"
                        }
                    }
                    append append_args " -$key $myvalue"
                }
            }
            
            if {[llength $append_args] > 0} {
                ::sth::sthCore::log hltcall "#$cmd $args"
                puts "<info>: append $append_args to $cmd calling"
                append myarg $append_args
                set args $myarg
            }
        } err
    } 

    ::sth::sthCore::log hltcall "$cmd $args"

    return $::sth::sthCore::SUCCESS
}

proc ::sth::sthCore::procConstantsToArray { mynamespace mycommand myswitch myconstants} {
    #puts "myconstants = $myconstants"
    
    array set constarray $myconstants
    set tableFwd $mynamespace$mycommand\_$myswitch\_fwdmap
    set tableRvs $mynamespace$mycommand\_$myswitch\_rvsmap    
    foreach hconst [array names constarray] {
        set ${tableFwd}($hconst) [set constarray($hconst)]
        set ${tableRvs}([set constarray($hconst)]) $hconst
    }
}

proc ::sth::sthCore::procModesToArray { mynamespace mycommand myswitch mymodechoices} {
    array set modearray $mymodechoices
    set tableMode $mynamespace$mycommand\_$myswitch\_mode  
    foreach mode [array names modearray] {
        set ${tableMode}($mode) [set modearray($mode)]
    }
}

proc ::sth::sthCore::getModeFunc2 { args } {
    set mynamespace [lindex $args 0]
    set cmd [lindex $args 1]
    set myswitch [lindex $args 2]
    set mymode [lindex $args 3]
    set tableName $mynamespace$cmd\_$myswitch\_mode
    variable ${tableName}
    return [set ${tableName}($mymode)]
}

proc ::sth::sthCore::getModeFunc { mynamespace cmd myswitch mymode } {
    set tableName $mynamespace$cmd\_$myswitch\_mode
    return [set ${tableName}($mymode)]
}

proc ::sth::sthCore::getFwdmap { mynamespace cmd myswitch myconst } {
    set tableName $mynamespace$cmd\_$myswitch\_fwdmap
    return [set ${tableName}($myconst)]
}

proc ::sth::sthCore::getRvsmap { mynamespace cmd myswitch myconst } {
    set tableName $mynamespace$cmd\_$myswitch\_rvsmap
    return [set ${tableName}($myconst)]
}
proc ::sth::sthCore::getswitchprop { mynamespace cmd myswitch myswitchprop } {
    set tableName $mynamespace$cmd\_$myswitchprop
    return [set ${tableName}($myswitch)]
}


proc ::sth::sthCore::sthCoreInit { } {
    
    variable ::sth::sthCore::logfilesuffix
    variable ::sth::sthCore::logfile
    variable ::sth::sthCore::log
    
    variable ::sth::sthCore::hltlogfilesuffix
    variable ::sth::sthCore::hltlogfile
    variable ::sth::sthCore::hltlog
    
    variable ::sth::sthCore::vendorlogfilesuffix
    variable ::sth::sthCore::vendorlogfile
    variable ::sth::sthCore::vendorlog
    
    variable ::sth::sthCore::log_level
    variable ::sth::sthCore::logLevelArray
 
    variable ::sth::sthCore::hlt2stcmappingfilesuffix
    variable ::sth::sthCore::hlt2stcmappingfile
    variable ::sth::sthCore::hlt2stcmapping
    
    variable ::sth::sthCore::iEnableTimeStamp
    variable ::sth::sthCore::iEnableTypeTag

    variable ::sth::sthCore::use_parse_dashed_args_option
    variable ::sth::sthCore::spirentTracker
    ##variable ::sth::sthCore::bMakeCmdDbTable
    ##variable ::sth::sthCore::zeroString
    variable ::sth::sthCore::enableSetupPortMapping
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::optimization
    variable ::sth::sthCore::custom_path
    
    variable ::sth::sthCore::showSthCmd 0
    variable ::sth::sthCore::showStcCmd 0
    variable ::sth::sthCore::UseModifier4TrafficBinding 0
    

    set ::sth::sthCore::log 0
    set ::sth::sthCore::logfile log
    set ::sth::sthCore::logfilesuffix txt
    
    set ::sth::sthCore::hltlog 0
    set ::sth::sthCore::hltlogfile hltlog
    set ::sth::sthCore::hltlogfilesuffix txt
    
    set ::sth::sthCore::vendorlog 0   
    set ::sth::sthCore::vendorlogfile vendorlog
    set ::sth::sthCore::vendorlogfilesuffix txt
    
    set ::sth::sthCore::log_level 0
    array set ::sth::sthCore::logLevelArray {\
                            emergency  0\
                            alert      1\
                            critical   2\
                            error      3\
                            warn       4\
                            notify     5\
                            info       6\
                            debug      7
    }
    
    array set ::sth::sthCore::loglevelInverseArray {}
    
    foreach {index value} [array get ::sth::sthCore::logLevelArray] {
        set ::sth::sthCore::loglevelInverseArray($value) $index
    }
    
    set ::sth::sthCore::hlt2stcmapping 0
    set ::sth::sthCore::hlt2stcmappingfile hlt2stcmapping
    set ::sth::sthCore::hlt2stcmappingfilesuffix txt
    
    set ::sth::sthCore::iEnableSpirentTracker 1
    
    set ::sth::sthCore::iEnableTimeStamp 1
    set ::sth::sthCore::iEnableTypeTag 1
    
    set ::sth::sthCore::custom_path ""
    set ::sth::sthCore::enableSetupPortMapping 0
    
    variable ::sth::sthCore::previousSthCmd ""
    variable ::sth::sthCore::previousStcCmd ""

    #set ::sth::sthCore::bMakeCmdDbTable false
    #set ::sth::sthCore::zeroString 0000000000000000000000000000000000000000000000000
    
    set ::sth::sthCore::use_parse_dashed_args_option cisco
    set ::sth::sthCore::SUCCESS 1
    set ::sth::sthCore::FAILURE 0
    set ::sth::sthCore::optimization 0
    
    if {[catch {::sth::sthCore::doStcCreate project retvalue} returnMsg ]} {
        ::sth::sthCore::log debug "{Failed to create project $returnMsg}"
  	if {[catch {::sth::sthCore::doStcDestroy} msg]} {
              ::sth::sthCore::log debug "{Failed to destroy: $msg}"
        }
    } else {
        catch {set ::sth::sthCore::GBLHNDMAP(project) $retvalue
        set ::sth::GBLHNDMAP(project) $::sth::sthCore::GBLHNDMAP(project)
        set ::sth::sthCore::GBLHNDMAP(system)  [::stc::get $::sth::sthCore::GBLHNDMAP(project) -parent]
        set ::sth::sthCore::GBLHNDMAP(sequencer) [::stc::get $::sth::sthCore::GBLHNDMAP(system) -children-sequencer]}
    }  
    
    if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
        set cmdName "::stc::config automationoptions -logTo NUL -logLevel ERROR";
    } else {
        set cmdName "::stc::config automationoptions -logTo /dev/null -logLevel ERROR";
    }
    
    if {[catch {eval $cmdName} returnMsg ]} {
        ::sth::sthCore::log debug "Failed to set automationOptions $returnMsg"
    } else {
  	::sth::sthCore::log info "automationOptions set. $cmdName"
    }
    
    if { $::sth::sthCore::log } {
        if { ![string compare -nocase $::sth::sthCore::logfile "stdout"] } {
            set fileD $::sth::sthCore::logfile
        } else {
            set fileD [open $::sth::sthCore::logfile\.$::sth::sthCore::logfilesuffix w+]
            puts $fileD "\############# Spirent HLTAPI Log File #############"
            close $fileD           
        }
    }
    
    if { $::sth::sthCore::hlt2stcmapping } {
        if { ![string compare -nocase $::sth::sthCore::hlt2stcmappingfile "stdout"] } {
            set mFileD $::sth::sthCore::hlt2stcmappingfile
        } else {
            set mFileD [open $::sth::sthCore::hlt2stcmappingfile\.$::sth::sthCore::hlt2stcmappingfilesuffix w]
            puts $mFileD "\############# HLT2STC Mapping Log File #############"
            close $mFileD           
        }
    }
    
    if { $::sth::sthCore::hltlog } {
        if { ![string compare -nocase $::sth::sthCore::hltlogfile "stdout"] } {
            set hltFileD $::sth::sthCore::hltlogfile
        } else {
            set hltFileD [open $::sth::sthCore::hltlogfile\.$::sth::sthCore::logfilesuffix w]
            puts $hltFileD "\############# Spirent HLTAPI Export Log File #############"
            puts $hltFileD "puts \"source hltapi_5.10_stc_2.10.tcl\""
            puts $hltFileD "source  hltapi_5.10_stc_2.10.tcl"
            puts $hltFileD "#puts \"package require SpirentHltApi\""
            puts $hltFileD "#package require SpirentHltApi"
            close $hltFileD           
        }
    }
    
    if { $::sth::sthCore::vendorlog} {
        if { ![string compare -nocase $::sth::sthCore::vendorlogfile "stdout"] } {
            set stcFileD $::sth::sthCore::vendorlogfile
        } else {
            set stcFileD [open $::sth::sthCore::vendorlogfile\.$::sth::sthCore::vendorlogfilesuffix w]
            puts $stcFileD "\############# Spirent HLTAPI STC Export Log File #############"
            puts $stcFileD "puts \"package require SpirentTestCenter\""
            puts $stcFileD "package require SpirentTestCenter"
            puts $stcFileD "#puts \"source SpirentTestCenter.tcl\""
            puts $stcFileD "#source SpirentTestCenter.tcl"  
            close $stcFileD           
        }
    }

}

proc ::sth::sthCore::AddStcTrace {} {
    variable ::sth::sthCore::previousStcCmd
    set ::sth::sthCore::previousStcCmd ""
    
    trace add execution "::after" enter ::sth::sthCore::stcTrace
    if { $::sth::sthCore::showStcCmd } {
        puts "trace procedure: ::after"
    }
    
    foreach p [info procs ::stc::*] {
        trace add execution $p enter ::sth::sthCore::stcTrace
        if { $::sth::sthCore::showStcCmd } {
            puts "trace procedure: $p"
        }
    }
}

proc ::sth::sthCore::RemoveStcTrace {} {
    variable ::sth::sthCore::previousStcCmd
    set ::sth::sthCore::previousStcCmd ""
    
    trace remove execution "::after" enter ::sth::sthCore::stcTrace
    if { $::sth::sthCore::showStcCmd } {
        puts "remove procedure: ::after"
    }
    
    foreach p [info procs ::stc::*] {
        trace remove execution $p enter ::sth::sthCore::stcTrace
        if { $::sth::sthCore::showStcCmd } {
            puts "remove procedure: $p"
        }
    }
}

proc ::sth::sthCore::stcTrace {command op} {
    variable ::sth::sthCore::previousStcCmd
    
    if {[string first "after" $command] == 0 && [string first "\:\:sleep" $::sth::sthCore::previousStcCmd] > 0} {
        # do nothing
    } else {
        set msg "$command"
        set ::sth::sthCore::previousStcCmd $command
        ::sth::sthCore::log xstccall $msg
        if { $::sth::sthCore::showStcCmd } {
            puts $command
        }
    }
}

proc ::sth::sthCore::AddSthTrace {} {
    variable ::sth::sthCore::previousSthCmd
    set ::sth::sthCore::previousSthCmd ""

    #set mySthTclTraceFileName $file
    #set previousCmd ""
    trace add execution "::after" enter ::sth::sthCore::sthTrace
    if { $::sth::sthCore::showSthCmd } {
        puts "trace procedure: ::after"
    }
    
    foreach p [info procs ::sth::*] {
        trace add execution $p enter ::sth::sthCore::sthTrace
        if { $::sth::sthCore::showSthCmd } {
            puts "trace procedure: $p"
        }
    }
    
    trace add execution "::after" leave ::sth::sthCore::sthLeaveTrace
    foreach p [info procs ::sth::*] {
        trace add execution $p leave ::sth::sthCore::sthLeaveTrace
    }
    
    #set sthTraceFile [open "$mySthTclTraceFileName" "w"]
    #puts $sthTraceFile "package require SpirentHltApi"
    #puts $sthTraceFile "#source hltapi_5.10_stc_2.10.tcl"
    #    
    #puts $sthTraceFile"\n\n"
    #close $sthTraceFile
}

proc ::sth::sthCore::RemoveSthTrace {} {
    variable ::sth::sthCore::previousSthCmd
    set ::sth::sthCore::previousSthCmd ""

    trace remove execution "::after" enter ::sth::sthCore::sthTrace
    trace remove execution "::after" leave ::sth::sthCore::sthLeaveTrace
    if { $::sth::sthCore::showSthCmd } {
        puts "remove procedure: ::after"
    }
    
    foreach p [info procs ::sth::*] {
        trace remove execution $p enter ::sth::sthCore::sthTrace
        trace remove execution $p leave ::sth::sthCore::sthLeaveTrace
        if { $::sth::sthCore::showSthCmd } {
            puts "remove procedure: $p"
        }
    }
}

proc ::sth::sthCore::sthLeaveTrace {command code result op} {
     variable ::sth::sthCore::previousSthCmd   
    
    if {[string first "after" $command] == 0 && [string first "\:\:sleep" $::sth::sthCore::previousSthCmd] > 0} {
        # do nothing
    } elseif {[string first "\:\:sth\:\:parse\_" $command] == 0} {
        # do nothing
    } elseif {[string first "\:\:sth\:\:\_parse\_" $command] == 0} {
        # do nothing
    } else {
        #set sthTraceFile [open "$mySthTclTraceFileName" "a"]
        #puts $sthTraceFile "puts \"$command\""
        if { [string first "after" $command] == 0 && [string first "set" $command] > 0 } {
            set msg "[lindex $command 0] [lindex $command 1]"
        } else {
            set msg "$command"
        }
        if { $::sth::sthCore::previousSthCmd eq "" } {
            set ::sth::sthCore::previousSthCmd "--"
        } elseif { $::sth::sthCore::previousSthCmd == $msg } {
            if { $::sth::sthCore::hltlog } {
                set hltlogfileD [open $::sth::sthCore::hltlogfile\.txt a+]
                puts $hltlogfileD "set logged_ret \"$result\""
                puts $hltlogfileD "if \{\$ret ne \$logged_ret\} \{"
                puts $hltlogfileD "    puts \"<warning>NOT same return value as logged result.\""
                puts $hltlogfileD "\}"
                puts $hltlogfileD "puts \$ret"
                close $hltlogfileD
            }
            set ::sth::sthCore::previousSthCmd "--"
        }
    }

}

proc ::sth::sthCore::sthTrace {command op} {
    variable ::sth::sthCore::previousSthCmd   

    if {[string first "after" $command] == 0 && [string first "\:\:sleep" $::sth::sthCore::previousSthCmd] > 0} {
        # do nothing
    } elseif {[string first "\:\:sth\:\:parse\_" $command] == 0} {
        # do nothing
    } elseif {[string first "\:\:sth\:\:\_parse\_" $command] == 0} {
        # do nothing
    } else {
        #set sthTraceFile [open "$mySthTclTraceFileName" "a"]
        #puts $sthTraceFile "puts \"$command\""
        if { [string first "after" $command] == 0 && [string first "set" $command] > 0 } {
            set msg "[lindex $command 0] [lindex $command 1]"
        } else {
            set msg "$command"
        }
        if { $::sth::sthCore::previousSthCmd == $msg } {
            #do nothing
        } else {
            if {$::sth::sthCore::previousSthCmd eq "--"} {
                ::sth::sthCore::log xhltcall $msg
                if { $::sth::sthCore::showSthCmd } {
                    puts $msg
                }
            }
            set ::sth::sthCore::previousSthCmd $msg
        }
    }
}


###/*! \ingroup sth::sthCore functions
###\fn log (type message)
###\brief logs messages and export tcl scripts. The reason why two functionality
###       are implemented in the same function is for run-time efficiency.
### 
###\param[in] type: Contains the type of the message to be logged
###\param[in] message: contains the message to be logged
###\return ::sth::sthCore::SUCCESS
###
### valid types: hltcall, stccall, info, error, warning and message
### if log is set to 1 and hltlog is true,
###   a) hltcall & message will be logged to $::sth::sthCore::logfile.txt
###   b) message will be logged to hlt2stcmapping.txt
### if log is set to 1 and vendorlog is true,
###   a) stccall & message will be logged to $::sth::sthCore::logfile.txt
###   b) message will be logged to hlt2stcmapping.txt
### if log is set 1,
###   a) thiscall and message is logged as a debug message
### if log is set 1,
###   a) error & message will be logged to $::sth::sthCore::logfile.txt
###   b) warn & message  will be logged to $::sth::sthCore::logfile.txt
###   c) info & message  will be logged to $::sth::sthCore::logfile.txt
###   d) debug & message will be logged to $::sth::sthCore::logfile.txt
###
### User Information
###  a) hltcalls and stcalls are automatically logged when $::sth::sthCore::log
###     is set to 1. Each developer does not need to log these two type of messages.
###  b) To log a function call other than a hltcall or a stccall as a debug message,
###     use the following ::sth::sthCore::log thiscall "".
###     Note that "" must be put as the second argument.
###     Sometimes, a developer may want to track any internal function call.
###  c) If $::sth::sthCore::log is set 1, all four types of messages (error, warn, info and debug)
###     will be logged to $::shtCor::logfile.txt. The user cannot selectively log one of
###     them. All of them have the equal level.
###  d) If $::sth::sthCore::log is set to 0, no messages will be logged, no functions
###     will be exported. The time cost of this function call in this case is 3 microseconds,
###     which is similar to that of a tcl log function when disabled.
###
###\warning None
###\author Davison Zhang
###*/
###
### ::sth::sthCore::log ( type message )
###
proc ::sth::sthCore::log { type message } {
    variable ::sth::sthCore::log
    if {$::sth::sthCore::log } {
        if {$::sth::sthCore::iEnableTimeStamp } {
            set timeStamp [clock format [clock seconds]]
        } else {
            set timeStamp ""
        }
        if { $::sth::sthCore::iEnableTypeTag } {
            set myTypeTag "\[$type\]"
        } else {
            set myTypeTag ""
        }
        set fileD [open $::sth::sthCore::logfile\.txt a+]
        switch $type {
            xhltcall {
                if { $::sth::sthCore::hlt2stcmapping } {
                    set mFileD [open $::sth::sthCore::hlt2stcmappingfile\.txt a+]
                    puts $mFileD "\n"
                    puts $mFileD $message
                    close $mFileD                    
                }
                if { $::sth::sthCore::hltlog } {
                    set hltlogfileD [open $::sth::sthCore::hltlogfile\.txt a+]
                    puts $hltlogfileD ""
                    puts $hltlogfileD "puts \"\\n$message\""
                    puts $hltlogfileD "set ret \[$message\]"
                    close $hltlogfileD
                }
            }
            xstccall {
                if { $::sth::sthCore::hlt2stcmapping } {
                    set mFileD [open $::sth::sthCore::hlt2stcmappingfile\.txt a+]
                    puts $mFileD $message
                    close $mFileD                    
                }
                if { $::sth::sthCore::vendorlog } {
                    set vendorlogfileD [open $::sth::sthCore::vendorlogfile\.txt a+]
                    puts $vendorlogfileD ""
                    puts $vendorlogfileD "puts \"$message\""
                    puts $vendorlogfileD "set status \[$message\]"
                    puts $vendorlogfileD "puts \$status"
                    close $vendorlogfileD
                }
            }
            thiscall {
                if { $::sth::sthCore::logLevelArray(debug) <= $::sth::sthCore::log_level } {
                    set myTypeTag "\[Debug\]"
                    set _procName [lindex [::info level 1] 0] ;
                    set _procArgs [lrange [::info level 1] 1 end] ;
                    if { ![string compare -nocase $::sth::sthCore::logfile stdout] } {
                        puts  "$timeStamp $myTypeTag $_procName $_procArgs"
                    } else {
                        puts $fileD "$timeStamp $myTypeTag $_procName $_procArgs"
                    }
                }
            }
            info -
            warn -
            error -
            debug -
            emergency -
            alert -
            critical -
            notify {
                if { $::sth::sthCore::logLevelArray($type) <= $::sth::sthCore::log_level } {
                    if { ![string compare -nocase $::sth::sthCore::logfile stdout] } {
                        puts  "$timeStamp $myTypeTag $message"
                    } else {
                        puts $fileD "$timeStamp $myTypeTag $message"
                    }
                }
            }

	    hltcall -
	    stccall {
		if { ![string compare -nocase $::sth::sthCore::logfile stdout] } {
		    puts  "$timeStamp $myTypeTag $message"
		} else {
		    puts $fileD "$timeStamp $myTypeTag $message"
		}
            }

            default {
                if { ![string compare -nocase $::sth::sthCore::logfile.txt stdout] } {
                    puts  "$timeStamp $myTypeTag $message"
                } else {
                    puts $fileD "$timeStamp $myTypeTag $message"
                }
                set myTypeTag "\[error\]"
                if { ![string compare -nocase $::sth::sthCore::logfile stdout] } {
                    puts  "$timeStamp $myTypeTag $message"
                } else {
                    puts $fileD "$timeStamp $myTypeTag $message"
                }
            }
        }
        close $fileD
        return $::sth::sthCore::SUCCESS
   }
}

proc ::sth::sthCore::commandInit { cmdTable userArgs mynamespace mycmd userArgsArray sortedSwitchPriorityList } {
    set myCmdTableName $cmdTable
    upvar $cmdTable myCmdTable
    upvar $sortedSwitchPriorityList mySortedSwitchPriorityList
    upvar $userArgsArray myUserArgsArray
    set returnKeyedList ""
    set flag $myCmdTableName\_Initialized
    if { ![info exists $flag] } {
        variable $flag
        set $flag true
        ::sth::sthCore::InitTableFromTCLList ${myCmdTable}
        #puts "$myCmdTableName is loaded, $flag = [set ${flag} ]"  
    }
    #check if the Input args is supported
    set num_args [llength $userArgs]
    for { set i 0 } { $i < $num_args } { incr i } {
    set arg [lindex $userArgs $i]
        if {[regexp {^-} $arg]} {
            # Remove the dash from the variable
            regsub {^-} $arg {} arg
	    set tableName $mynamespace$mycmd\_supported
	    if {[info exists ${tableName}($arg)]} {
		if {![::sth::sthCore::getswitchprop $mynamespace $mycmd $arg supported]} {
		    #return -code error "-$arg is not a supported switch"
		    ::sth::sthCore::log warn "** WARN ** -$arg is not a supported switch, will be ignored." 
		}
	    }
	} 
	incr i
    }
    
    catch {unset mySortedSwitchPriorityList} err
    set man_args $mynamespace$mycmd\_mandatory_args
    set opt_args $mynamespace$mycmd\_optional_args
    switch $::sth::sthCore::use_parse_dashed_args_option {
        cisco -
        improved_cisco
        {
            set status [::sth::sthCore::createMandatoryOptional_args $mynamespace $mycmd type default range]
            if { ![string compare -nocase cisco $::sth::sthCore::use_parse_dashed_args_option] } {
                ::sth::parse_dashed_args -args  $userArgs \
                    -mandatory_args [set ${man_args}]\
                    -optional_args  [set ${opt_args}]\
                    -return_array myUserArgsArray
            } else {
                improved_parsed_dashed_args -args $userArgs \
                    -mandatory_args [set ${man_args}]\
                    -optional_args  [set ${opt_args}]\
                    -return_array myUserArgsArray 
            }
            
            ::sth::sthCore::createSwitchPriorityList $mynamespace $mycmd $userArgs \
                                                    mySortedSwitchPriorityList ""
            
            #check the range of argument with numeric type
            ::sth::sthCore::checkNumericRange $mynamespace $mycmd myUserArgsArray $mySortedSwitchPriorityList
        }
        spirent
        {
            array set myUserArgsArray {}
            ::sth::sthCore::parseInputArgs switchList myUserArgsArray $userArgs
            ::sth::sthCore::createSwitchPriorityList $mynamespace $mycmd $userArgs \
                                                    mySortedSwitchPriorityList $switchList
        }
        default
        {
            ::sth::sthCore::log error "Invalid parse_dashed_args_option: $::sth::sthCore::Invalid_parse_dashed_args_option"
            return $::sth::sthCore::FAILURE
        }
    }
    ##if {[catch {set ret [::sth::sthCoreDb::caculateTestedCmdAttributes $mynamespace $mycmd myUserArgsArray]} errMsg]} {
    ##    ::sth::sthCore::processError $returnKeyedList $errMsg "function1 arg1" "function2 arg1 arg2 "
    ##    return -code error $::sth::sthCore::FAILURE
    ##}
    catch {array unset ::sth::sthCore::inputArg}
    foreach item $mySortedSwitchPriorityList {
        foreach {priority opt} $item {
            set ::sth::sthCore::inputArg([string tolower $opt]) 1
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::sthCore::IsInputOpt {optname} {
    set name [string tolower [string trim $optname "- "]]
    if {[info exists ::sth::sthCore::inputArg($name)]} {
        return true
    }
    return false
}

proc ::sth::sthCore::checkNumericRange { mynamespace mycmd userArray sortedPriorityList} {
    upvar $userArray  userArgsArray
    
    foreach item $sortedPriorityList {
        foreach {priority myswitch} $item {} 
        set type [::sth::sthCore::getswitchprop $mynamespace $mycmd $myswitch type]

        if {[string match -nocase "NUMERIC" $type]} {
            set myvalue $userArgsArray($myswitch)
            set range [::sth::sthCore::getswitchprop $mynamespace $mycmd $myswitch range]
            if {$range != "_none_"} {
                #exclude negative value
                if {![regexp {^-} $range]} {
                    set dash [string first "-" $range]
                } else {
                    set newrange [string trimleft $range "-"]
                    set dash [expr [string first "-" $newrange]+1]
                }
                set length [string length $range]
                set lowrange [string range $range 0 [expr $dash-1]]
                set uprange [string range $range [expr $dash+1] $length]
                #if $myvalue is "", program will not go into the loop below and value-check will not be applied
                if {"" == $myvalue} {
                    return -code error "The value of switch -$myswitch SHOULD be NUMERIC and in the range of $range"
                }
                foreach value $myvalue {
				    set check_val {^[\-\+0-9]+$}
					if {![regexp "$check_val" $value]} {
						catch {set value [expr $value]}
					}
                   ::sth::sthCore::compareLargeNumber $lowrange $uprange $value $myswitch $range
                }
            }
        }
    }
}

#for the large number, compare the length and if the length is equal, then compare the value.
#it also can be handled by adding decimal point to range values, the same as the if {$check_type == "RANGE"} branch in the parse_dashed_args.tcl file.
proc ::sth::sthCore::compareLargeNumber {lowrange uprange value myswitch range} {
    set lowLen [string length $lowrange]
    set upLen [string length $uprange]
    set valueLen [string length $value]
    #check the length firstly
    if {$valueLen < $lowLen || $valueLen > $upLen} {
        return -code error "The value of switch -$myswitch is out of valid range, SHOULD be in the range of $range" 
    }
    #if the value length equals to the lower/uper length, compare the value.
    if {$valueLen == $lowLen && $value < $lowrange || $valueLen == $upLen && $value > $uprange} {
        return -code error "The value of switch -$myswitch is out of valid range, SHOULD be in the range of $range" 
    }
}

proc ::sth::sthCore::createSwitchPriorityList { mynamespace cmd userArgs switchPriorityList switchList } {
    variable switchPriList
    upvar $switchPriorityList switchPriList
    set switchPriList ""
    #puts "userArgs = $userArgs"
    set priorityTableName $mynamespace$cmd\_priority
    if { ![string compare -nocase simple $::sth::sthCore::use_parse_dashed_args_option]} {
        foreach switch $switchList {
            if {[::info exists ${priorityTableName}($switch)]} {
                lappend switchPriList "[set ${priorityTableName}($switch)] $switch"
            }
        }
    } else {
        foreach switch $userArgs {
            set switch [string range $switch 1 end ]
            if {[::info exists ${priorityTableName}($switch)]} {
                lappend switchPriList "[set ${priorityTableName}($switch)] $switch"
            }
        }
    }
    set switchPriList [lsort -integer -index 0 $switchPriList]
    return $::sth::sthCore::SUCCESS
}

proc ::sth::sthCore::IsCmdInTCLTable {myMasterList myns mycmd} {
    set myMasterListLen [llength $myMasterList]
    set myNamespace [string trimright [lindex $myMasterList 0] ":"]
    for {set k 1 } { $k < $myMasterListLen } {incr k } {
        set masterList [lindex $myMasterList $k]
        set cmd [lindex $masterList 0]
        if {$cmd eq $mycmd && $myNamespace eq $myns} {
            return $::sth::sthCore::SUCCESS
        }
    }
    
    return $::sth::sthCore::FAILURE
}

proc ::sth::sthCore::InitTableFromTCLList { myMasterList } {
    set myMasterListLen [llength $myMasterList]
    set myNamespace [lindex $myMasterList 0]
    set returnKeyedList ""
    for {set k 1 } { $k < $myMasterListLen } {incr k } {
        set masterList [lindex $myMasterList $k]
        set cmd [lindex $masterList 0]
        set listHeader [lindex $masterList 1]
        set listHeaderLength [llength $listHeader]
        set listLength [llength $masterList]
        set flag $myNamespace$cmd\_Initialized
        if { ![info exists $flag] } {
            variable $flag
            set $flag true
            #puts "flag = $flag, [set ${flag} ]"            
        } else {
            continue
        }
        for {set i 2} { $i < $listLength } {incr i} {
            set propertyRow [lindex $masterList $i]
            for {set j 0} { $j < $listHeaderLength} {incr j} {
                variable column
                set column [lindex $listHeader $j ]
                if {[string compare -nocase constants $column] } {
                    set {table$j} $cmd\_$column
                    variable $myNamespace${table$j}
                    if { ![::info exists $myNamespace${table$j} ] } {
                        array set $myNamespace${table$j} {}
                    }
                    if { 0 == $j } {
                        set $myNamespace${table$j}\([expr {$i-2}]) [lindex $propertyRow $j]                        
                    } else {
                        set $myNamespace${table$j}\([lindex $propertyRow 0]) [lindex $propertyRow $j]  
                    }
                } else {
                    if { [string compare -nocase [lindex $propertyRow $j] _none_] } {
                        set switchName [lindex $propertyRow 0]
                        set constants [lindex $propertyRow $j]
                        ::sth::sthCore::procConstantsToArray $myNamespace $cmd $switchName $constants
                    }
                }
                if {![string compare -nocase mode $column] } {
                    if { [string compare -nocase [lindex $propertyRow $j] _none_] } {
                        set switchName [lindex $propertyRow 0]
                        set modes [lindex $propertyRow $j]
                        ::sth::sthCore::procModesToArray $myNamespace $cmd $switchName $modes
                    }
                }                
            }
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::sthCore::processError { returnKeyedList errMsg args} {
    upvar $returnKeyedList myReturnKeyedList
    set status $::sth::sthCore::SUCCESS
    
    ::sth::sthCore::log error $errMsg
    keylset myReturnKeyedList log $errMsg
    keylset myReturnKeyedList status $::sth::sthCore::FAILURE
    set argsLen [llength $args]
    
    if { $argsLen > 0 } {
        foreach action $args {
            if {$action ne ""} {
                if {[catch {set ret [eval $action]} myError]} {
                    ::sth::sthCore::log error $myError
                    return $::sth::sthCore::FAILURE
                }
            }
        }
    }

    ::sth::sthCore::outputConsoleLog error $errMsg

    return $status
}
    
proc ::sth::sthCore::outputConsoleLog { type message} {
    
    puts "<$type>: $message"

}

#Could build the list once and used it many times.
proc ::sth::sthCore::createMandatoryOptional_args { myNSpace cmd args } {
  
    variable opt_args
    variable man_args
    variable optstr_args
    variable manstr_args
    set opt_args $myNSpace$cmd\_optional_args
    set man_args $myNSpace$cmd\_mandatory_args
    set optstr_args ""
    set manstr_args ""
    set argsLen [llength $args]
    set tableName $myNSpace$cmd\_[lindex $args 0]
    foreach index [array names ${tableName} ] {
        set mandatoryTable $myNSpace$cmd\_mandatory
        if { ![string compare -nocase [set ${mandatoryTable}($index) ] true] } {
            set manstr_args "$manstr_args \-$index "        
        } else {
            set optstr_args "$optstr_args \-$index "          
        }

        for {set i 0} { $i < $argsLen } {incr i } {
            set tableName $myNSpace$cmd\_[lindex $args $i]
            variable ${tableName}
            #puts "args\[$i] = [lindex $args $i]"
            set value [set ${tableName}($index)]
            if { [string compare -nocase $value _none_ ] } {
                if { ![string compare -nocase [set ${mandatoryTable}($index) ] true] } {
                    if { [string compare -nocase [lindex $args $i] default] } {
                        if {[string compare -nocase [lindex $args $i] type]} {
                            set tempstr $manstr_args
                            set tempval [string toupper [lindex $args $i]]
                            set manstr_args "$tempstr\t$tempval"
                        }
                        set tempstr $manstr_args
                        set tempval [set ${tableName}($index)]
                        set manstr_args "$tempstr $tempval \n"
                    }
                } else {
                    if {[string compare -nocase [lindex $args $i] type]} {
                        set tempstr $optstr_args
                        set tempval [string toupper [lindex $args $i]]
                        set optstr_args "$tempstr\t$tempval"
                    }
                    set tempstr $optstr_args
                    set tempval [set ${tableName}($index) ]
                    set optstr_args "$tempstr $tempval\n"
                }
            } 
        }     
    }
    set ${opt_args} $optstr_args
    set ${man_args} $manstr_args
}
# update all the elements in a list to hexadecimal representation by prepending "0x"
# Examples:
#   set myList {{01} {0x17 ff} {0d 0a}}
#   convertListToHex myList
# myList will be {{0x01} {0x17 0xff} {0x0d 0x0a}}
proc ::sth::sthCore::updateListToHex { inputList } {
    upvar $inputList myInputList
    set toString $myInputList
    
    if {[regexp {\{|\}} $toString]} {
        set i 0
        foreach sublist $myInputList {            
            set j 0
            foreach item $sublist {
                if {![regexp {^0x} $item]} {
                    lset myInputList $i $j "0x$item"
                }
                incr j
            }
            incr i
        }        
    } else {
        set i 0
        foreach item $myInputList {
            if {![regexp {^0x} $item]} {
                lset myInputList $i "0x$item"
            }
            incr i
        }
    }
}
# wait for a list of streamblocks to stop traffic, with a timeout.
# Examples:
#   set handles "streamblock1 streamblock2"
#   StreamblockWaitForStop $handles -1
# Arguments:
#   sbHndList   the list of streamblock handles
#   timeOut     number of seconds to wait, negative value means default (60 seconds)
proc ::sth::sthCore::StreamblockWaitForStop { sbHndList timeOut } {
    set defaultMaxWaitTime 60
    set waitInterval 1
    set maxWaitTime [ expr $timeOut < 0 ? $defaultMaxWaitTime : $timeOut ]
    set totalWaitTime 0
        
    foreach sbHnd $sbHndList {
        while { $totalWaitTime < $maxWaitTime } {
            set state [::sth::sthCore::invoke stc::get $sbHnd -RunningState]
            if { $state != "STOPPED" } {
                ::sth::sthCore::invoke stc::sleep $waitInterval
                set totalWaitTime [expr $totalWaitTime + $waitInterval]
            } else {
                break
            }
        }
    }
    if { $totalWaitTime >= $maxWaitTime } {
        return -code error "Timeout ($maxWaitTime seconds) waiting streamblocks to stop traffic" 
    } else {
        return $::sth::sthCore::SUCCESS
    }
}

# Synopsis:
#   Get all the values from a keyed list.
#   It is often used in the wizard config API implementation, in which "-mode delete"
#   needs to delete all the handes created by expanding wizard config. 
# Examples:
#   set VxWizard [sth::emulation_vxlan_evpn_overlay_wizard_config ...]
#   set handles_in_list [::sth::sthCore::keylvalues $VxWizard "status"]
#
#   This will return all the handles except "{status 1}" from $VxWizard.
# Arguments:
#   keyedlist   A keyed list.
#   ignorekeys  Keys to ignore. Won't return the values under these keys. 
#               Currently not supporting hierarchical keys.

proc ::sth::sthCore::keylvalues {keyedlist {ignorekeys ""}} {
    set resultlist ""
    foreach key [keylkeys keyedlist] {
        if { [lsearch -exact $ignorekeys $key] == -1 } {
            set sublist [keylget keyedlist $key]
            if {[catch {keylkeys sublist}]} {
                set resultlist [concat $resultlist $sublist]
            } else {
                set resultlist [concat $resultlist [keylvalues $sublist $ignorekeys]]
            }
        }
    }
    return $resultlist
}