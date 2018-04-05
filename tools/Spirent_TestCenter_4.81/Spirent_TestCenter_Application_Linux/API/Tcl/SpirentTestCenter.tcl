set vers "9.90"

package provide SpirentTestCenter $vers
package provide stc $vers

set stc_dir [file dirname [file join [pwd] [info script]]]

# In some Solaris/Tcl combinations stc_dir ends up with a tilde, which is not
# handled correctly inside of the BLL
if {[string index $stc_dir 0] == "~"} {
    set stc_dir [file normalize $stc_dir]
}

set env(STC_PRIVATE_INSTALL_DIR) "$stc_dir/"

set orig_dir [pwd]
set env(TCL_RUNNING_DIR) "$orig_dir/"

cd $stc_dir

# sTcl.dll is libsTcl.so on unix
if {$tcl_platform(platform) == "unix"} {
    set sharedlibpretension lib
} else {
    set sharedlibpretension ""
}

if {[catch {load [file join $stc_dir [subst $sharedlibpretension]sTcl[info sharedlibextension]] sTcl } e ]} {
    puts "Error Occured while loading the Spirent Automation Internal Utility Library ($e)."
}

cd $orig_dir

namespace eval ::stc:: {

        namespace export    init \
                connect \
                disconnect \
                create \
                delete \
                config \
                get \
                perform \
                reserve \
                release \
                subscribe \
                unsubscribe \
                help \
                apply \
                sleep \
                waituntilcomplete \
                waitUntilComplete \
                destroy \
                log
}

namespace eval ::stc_int {}

#handle exceptions on some functions

set stc_int::wrapped_command_list {}

# replacement for proc that creates two procs,
# one that catches errors and returns -1, and one that lets them bubble up
proc wrap_proc {procname argz script} {
  global stc_int::wrapped_command_list
  lappend stc_int::wrapped_command_list $procname

  set noerrorscript "stc_int::execcatch \{$script\}"

  set procname [lindex [split $procname ":"] end]

  # Handle the case where this is re-sourced with automationoptions
  # in the non-default state (default == false)
  if {[info proc stc::get] == "" || ![stc::get automationoptions -suppressTclErrors]} {
    uplevel 1 [list proc stc::$procname $argz $script]
    uplevel 1 [list proc stc_int::$procname\_noerrors $argz $noerrorscript]
  } else {
    uplevel 1 [list proc stc_int::$procname\_orig $argz $script]
    uplevel 1 [list proc stc::$procname $argz $noerrorscript]
  }
}

##################################################################
#
# Procedure name: destroy
# Input arguments:
# Output arguments:
# Description: This routine cleans up the project(s),
# disconnects from all the chasssis, and performs BLL cleanup.
# Once this command is called, commands in the ::stc namespace
# are no longer allowed.
##################################################################
proc ::stc::destroy {} {
   set result1 [ ::stc::perform ChassisDisconnectAll ]
   set result2 [ ::stc::perform ResetConfig -config system1 ]
   stc_int::salShutdownNoExit
   namespace delete ::stc
   return
}

proc ::stc::init {} {
    #stc_int::salInit
}

wrap_proc ::stc::log { level message } {
    stc_int::salLog $level $message
}

wrap_proc ::stc::connect { args } {
    stc_int::salConnect $args
}

wrap_proc ::stc::disconnect { args } {
    stc_int::salDisconnect $args
}

wrap_proc ::stc::create { type args } {
    stc_int::salCreate $type $args
}

wrap_proc ::stc::delete {args} {
   stc_int::salDelete $args
}

wrap_proc ::stc::config { handle args } {
   stc_int::salSet $handle $args
}

wrap_proc ::stc::get { handle args } {
    set result [ stc_int::salGet $handle $args ]
    if { [llength $result] == 1 } { return [lindex $result 0] }
    return $result
}

wrap_proc ::stc::perform { commandName args } {
    set result [ stc_int::salPerform $commandName $args ]
    if { [llength $result] == 1 } { join $result }
    return $result
}

wrap_proc ::stc::reserve { args } {
    set result [ stc_int::salReserve $args ]
    if { [llength $result] == 1 } { join $result }
    return $result
}

wrap_proc ::stc::release { args } {
    stc_int::salRelease $args
}

wrap_proc ::stc::subscribe { args } {
    return [ stc_int::salSubscribe $args ]
}

wrap_proc ::stc::unsubscribe { args } {
    return [ stc_int::salUnsubscribe $args ]
}

wrap_proc ::stc::help {args } {
    return [ stc_int::salHelp $args ]
}

wrap_proc ::stc::apply {} {
    return [ stc_int::salApply ]
}

proc ::stc::sleep {seconds} {
    set stc_sleep_flag 0
    after [expr $seconds * 1000] set ::stc_sleep_flag 1
    catch { vwait stc_sleep_flag }
}

wrap_proc ::stc::waituntilcomplete {args} {
    set doWaiting 1
    set myTimer 0
    set timeOutVal 0
    if {$args != ""} {
        #check the args name and value
        if {[expr [llength $args] % 2] != 0} {
          error "ERROR: Valid Attribute Value Pairs not found"
        }

        foreach {optionName optionValue} $args {
          set name [string tolower $optionName]
          if {[string index $name 0] == "-" } {
              set name [string replace $name 0 0 ]
          }
          if {$name != "timeout"} {
              error "ERROR: Invalid Attribute name $name "
          }
          set timeOutVal [string tolower $optionValue]
        }
    }
    set sequencer [stc_int::salGet system1 -children-sequencer]
    while {$doWaiting != 0} {
      set currTestState [stc_int::salGet $sequencer -state]
      switch -exact -- $currTestState {
         PAUSE {
            set doWaiting 0
         }
         IDLE {
            set doWaiting 0
         }
         default {
         }
      }
      ::stc::sleep 1
      #check the timeout
      incr myTimer
      if { $timeOutVal > 0} {
        if { $myTimer >= $timeOutVal} {
            error "ERROR: Timeout "
        }
      }
    }

    if {[info exists ::env(STC_SESSION_SYNCFILES_ON_SEQ_COMPLETE)] \
        && $::env(STC_SESSION_SYNCFILES_ON_SEQ_COMPLETE) == 1} {

    array set bllInfo [stc::perform CSGetBllInfo]

    if {$bllInfo(-ConnectionType) == "SESSION"} {
        stc::perform CSSynchronizeFiles
    }
    }
    return $currTestState
}

wrap_proc ::stc::waitUntilComplete {args} {
    set retState [eval ::stc::waituntilcomplete $args]
    return $retState
}

proc ::stc_int::suppressTclErrorsCallback {flag} {
  global stc_int::wrapped_command_list
  if {$flag} {
    foreach command $stc_int::wrapped_command_list {
      set command [lindex [split $command ":"] end]
      rename ::stc::$command ::stc_int::$command\_orig
      rename ::stc_int::$command\_noerrors ::stc::$command
    }
  } else {
    foreach command $stc_int::wrapped_command_list {
      set command [lindex [split $command ":"] end]
      rename ::stc::$command ::stc_int::$command\_noerrors
      rename ::stc_int::$command\_orig ::stc::$command
    }
  }
}

proc ::stc_int::execcatch {script} {
  set returnCode [catch {uplevel 1 $script} catchInfo]
  if {$returnCode == 1} {
      return -1
  } else {
      return -code $returnCode $catchInfo
  }
}

if {[info tclversion] < 8.4 || [lindex [ split [ info patchlevel ] . ] 2] < 13 &&
    [info tclversion] == 8.4 } {
    stc::log WARN "Recommended minimum version for Spirent Test Center is 8.4.13"
} elseif {[info tclversion] == 8.5} {
    set patchLevel [ lindex [ split [ info patchlevel ] . ] 2 ]
    if {$patchLevel != 9 && $patchLevel != 14} {
        stc::log WARN "Only 8.5.9 and 8.5.14 Tcl versions are officially supported from the 8.5 series."
    }
} elseif {[info tclversion] > 8.5} {
    stc::log WARN "Tcl versions newer than 8.5.14 are not supported."
}

# exit command might not exist in some interpreter
if {[info commands exit] == "exit"} {

    proc ::stc_int::onExit {cmdArgs op} {
        set status 0
        if {[llength $cmdArgs] > 1} {
            set status [lindex $cmdArgs 1]
        }
        stc_int::salShutdown $status
        trace remove execution exit enter ::stc_int::onExit
    }

    trace add execution exit enter ::stc_int::onExit
}

