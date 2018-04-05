# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth:: {
    
}

namespace eval ::sth::testconfigcontrol:: {
    
}

namespace eval ::sth::sthCore:: {
    
}

##Procedure Header
#
# Name:
#    sth::test_config
#
# Purpose:
#    Sets parameters for logging, debugging, and improving the performance of
#    the entire Spirent HLTAPI..
#
#    [[are any of these arguments Spirent extensions?]]
#
# Synopsis:
#    sth::test_config
#         [-log {1|0}]
#         [-logfile <demoLogfile>]
#         [-log_level <0-7>]
#         [-vendorlogfile stcExport\
#         [-vendorlog {1|0}]
#         [-hltlog {1|0}]
#         [-hltlogfile hltExport\
#         [-hlt2stcmappingfile hlt2StcMapping\
#         [-hlt2stcmapping {1|0}]
#
# Arguments:
#
#    -hlt2stcmapping
#                   Spirent Extension (for Spirent TestCenter only).
#                   Enables or disables the creation of a hlt2stcmapping.txt
#                   file. Valid values are 1 and 0. Specify the value 1 to
#                   generate a mapping file. Specify the value 0 if you do not
#                   want to generate this file. The default is 0.
#
#    -hlt2stcmappingfile
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the name of the file into which to capture the
#                   mapping from each executed HLTAPI command to all commands
#                   that are required to implement that HLTAPI command.
#                   The default file name is "hlt2stcmapping.txt". You can
#                   change the name of the mapping file to anything you like.
#    -hltlog
#                   Enables or disables the creation of an hltlog.txt file.
#                   Valid values are 1 and 0. Specify the value 1 to generate an
#                   hltlog.txt file. For Spirent HLTAPI, this file contains all
#                   of the HLTAPI commands executed. Specify the value 0 if you
#                   do not want to generate this file. The default is 0. The
#                   hltlog.txt file contains all executed commands (both HLTAPI
#                   and Spirent TestCenter) and up to seven levels of log
#                   messages, depending on your setting for the -log_level
#                   argument. You can change the name of the log file using the
#                   -hltlogfile argument.
#
#    -hltlogfile
#                   Specifies the name of the file into which to capture all
#                   HLTAPI commands executed during your test run. The default
#                   file name is "hltlog.txt". You can change the name of this
#                   file to anything you like.
#
#    -log
#                   Enables or disables logging. Valid values are
#                   1 and 0. Specify the value 1 to generate a log.txt file.
#                   Specify the value 0 to disable logging. If you disable
#                   logging, all logging features are also disabled.
#                   The default is 0. The log.txt file contains all executed
#                   commands (both HLTAPI and Spirent TestCenter) and up to
#                   seven levels of log messages, depending on your setting for
#                   the -log_level argument (see -log_level).
#
#    -logfile
#                   Specifies the name of the file into which to capture both
#                   your HLTAPI and Spirent TestCenter executed commands as well
#                   as other log messages determined by the log level you set in
#                   the -log_level argument. The default file name is "log.txt".
#                   You can change the name of the log file to anything you
#                   like.
#
#    -log_level
#                   Specifies the level of messages to be captured in the
#                   hltlog.txt file. These levels, as defined by the Cisco
#                   HLTAPI specification, are:
#
#                   emergency  0
#                   alert      1
#                   critical   2
#                   error      3
#                   warn       4
#                   notify     5
#                   info       6
#                   debug      7
#
#                   Set the log level to n, where 0 <= n <= 7.
#
#    -vendorlog
#                   Enables or disables the creation of an vendorlog.txt file.
#                   Valid values are 1 and 0. Specify the value 1 to generate an
#                   vendorlog.txt file. Specify the value 0 if you do not want
#                   to generate this file. The default is 0.
#
#    -vendorlogfile
#                   Specifies the name of the file into which to capture all
#                   Spirent TestCenter commands executed during your test run.
#                   The default file name is "vendorlog.txt". You can change the
#                   name of the vendor log file to anything you like.
#
# Return Values:
#    The sth::test_config function returns a keyed list using the
#    following keys (with corresponding data):
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
#
# Description:
#    The sth::test_config function enables you to set logging options for
#    capturing commands executed by HLTAPI, Spirent TestCenter, or both. It also
#    enables you to capture the following types of messages: alerts, critical,
#    error, warning, notification, information, and debug.
#
#    The function returns the requested type of data and a status value (1 for
#    success). If there is an error, the function returns the status value (0)
#    and an error message.
#
# Examples: See Sample Input and Sample Output.
#
# Sample Input:
#
#     sth::test_config      -log 1\
#                             -logfile demoLogfile \
#                             -log_level 7\
#                             -vendorlogfile stcExport\
#                             -vendorlog 1\
#                             -hltlog 1\
#                             -hltlogfile hltExport\
#                             -hlt2stcmappingfile hlt2StcMapping\
#                             -hlt2stcmapping 1
#
# Sample Output:
#
#    On success:
#    {status 1} {log {}}
#
#    On failure:
#    {status 0} {log {<errorMsg>}}
#
# Notes:
#
# End of Procedure Header

proc ::sth::test_config { args } {
    ::sth::sthCore::Tracker ::sth::test_config $args 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
    
    set cmdName "::sth::testconfigcontrol::test_config_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with emptry error messag is raised"
            ::sth::sthCore::log error $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}


    
proc ::sth::testconfigcontrol::test_config_imp { args } {
    #::sth::sthCore::Tracker ::sth::test_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    array unset userArgsArray 
    array set userArgsArray {}
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::testconfigcontrol::testconfigcontrolTable $args\
                                            ::sth::testconfigcontrol::\
                                            test_config \
                                            userArgsArray\
                                            sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "testconfigcontrol ::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }
    
    set cmd test_config
    set mynamespace ::sth::testconfigcontrol::
    foreach prioritySwitchpair $sortedSwitchPriorityList {
        set index [lindex $prioritySwitchpair 0]
        set myswitch [lindex $prioritySwitchpair end]
        #puts "myswitch == $myswitch"
        
        set temp ::sth::sthCore::$myswitch
        
        if { $myswitch == "log_level" } {
            set loglevel $userArgsArray($myswitch)
            if {[ info exists ::sth::sthCore::loglevelInverseArray($loglevel) ] } {
                set $temp $loglevel
            } else {
                set errMsg "Invalid log level: $loglevel; it should be 0..7"
                ::sth::sthCore::processError returnKeyedList $errMsg
                return -code error $errMsg
            }
        } else {
            set $temp $userArgsArray($myswitch)
            set temp1 $userArgsArray($myswitch)
            if {[regexp {file|custom} $myswitch]} {
            } else {
                if {$temp1 == 0 || $temp1 == 1} {
                } else {
                    set errMsg "Invalid value: $temp for switch $myswitch. Should be 0 OR 1"
                    ::sth::sthCore::processError returnKeyedList $errMsg
                    return -code error $errMsg
                }
            }
            

        }
        #puts "[set ${temp}]"
        #puts "::sth::sthCore::$myswitch"
    }
    if {[string length $::sth::sthCore::custom_path]} {
        set ::sth::sthCore::logfile [file join $::sth::sthCore::custom_path $::sth::sthCore::logfile]
        set ::sth::sthCore::hltlogfile [file join $::sth::sthCore::custom_path $::sth::sthCore::hltlogfile]
        set ::sth::sthCore::vendorlogfile [file join $::sth::sthCore::custom_path $::sth::sthCore::vendorlogfile]
        set ::sth::sthCore::hlt2stcmappingfile [file join $::sth::sthCore::custom_path $::sth::sthCore::hlt2stcmappingfile]
    }
    foreach prioritySwitchpair $sortedSwitchPriorityList {
        set index [lindex $prioritySwitchpair 0]
        set myswitch [lindex $prioritySwitchpair end]
        #puts "myswitch == $myswitch"        
        switch $myswitch {
            log {
                if { $::sth::sthCore::log } {
                    if { ![string compare -nocase $::sth::sthCore::logfile "stdout"] } {
                        set fileD $::sth::sthCore::logfile
                    } else {
                        set fileD [open $::sth::sthCore::logfile\.$::sth::sthCore::logfilesuffix w]                       
                        puts $fileD "\############# Spirent HLTAPI Log File #############"
                        puts $fileD "Hlt Api (Ver. $::_HLT_VERSION) was successfully loaded and initialized"
                        puts $fileD "Internal Version: $::internal_ver"
                        close $fileD           
                    }
                }
            }
            
            hltlog {
                if { $::sth::sthCore::log && $::sth::sthCore::hltlog } {
                    if { ![string compare -nocase $::sth::sthCore::hltlogfile "stdout"] } {
                        set hltFileD $::sth::sthCore::hltlogfile
                    } else {
                        set hltFileD [open $::sth::sthCore::hltlogfile\.$::sth::sthCore::logfilesuffix w]
                        puts $hltFileD "\############# Spirent HLTAPI Export Log File #############"
                        puts $hltFileD "#puts \"source hltapi_5.10_stc_2.10.tcl\""
                        puts $hltFileD "#source  hltapi_5.10_stc_2.10.tcl"
                        puts $hltFileD "puts \"package require SpirentHltApi\""
                        puts $hltFileD "package require SpirentHltApi"
                        close $hltFileD           
                    }
                    ::sth::sthCore::AddSthTrace
                } else {
                    ::sth::sthCore::RemoveSthTrace
                }
            }
            
            vendorlog {
                if { $::sth::sthCore::log && $::sth::sthCore::vendorlog} {
                    if { ![string compare -nocase $::sth::sthCore::vendorlogfile "stdout"] } {
                        set stcFileD $::sth::sthCore::vendorlogfile
                    } else {
                        set stcFileD [open $::sth::sthCore::vendorlogfile\.$::sth::sthCore::vendorlogfilesuffix w]
                        puts $stcFileD "\############# Spirent HLTAPI STC Export Log File #############"
                        puts $stcFileD "puts \"package require SpirentTestCenter\""
                        puts $stcFileD "package require SpirentTestCenter"
                        puts $stcFileD "#puts \"source SpirentTestCenter.tcl\""
                        puts $stcFileD "#source SpirentTestCenter.tcl"
                        puts $stcFileD "\n\n"
                        puts $stcFileD "::stc::create project -under system1"
                        close $stcFileD   
                    }
                    ::sth::sthCore::AddStcTrace
                } else {
                    ::sth::sthCore::RemoveStcTrace
                }
            }
            
            hlt2stcmapping {
                if { $::sth::sthCore::log && $::sth::sthCore::hlt2stcmapping } {
                    if { ![string compare -nocase $::sth::sthCore::hlt2stcmappingfile "stdout"] } {
                        set mFileD $::sth::sthCore::hlt2stcmappingfile
                    } else {
                        set mFileD [open $::sth::sthCore::hlt2stcmappingfile\.$::sth::sthCore::hlt2stcmappingfilesuffix w]
                        puts $mFileD "\############# HLT2STC Mapping Log File #############"
                        close $mFileD           
                    }
                }   
            }
        }
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


##Procedure Header
#
# Name:
#    sth::test_control
#
# Purpose:
#    Sets parameters for optimization and parsing.
#
# Synopsis:
#    sth::test_control
#         -action {enable|disable|sync}]
#         [-parser {cisco|spirent}]
#
# Arguments:
#    -action
#                   Specifies the action to take on the specified port handles.
#                   Possible values are:
#
#                   enable    - Enable optimization (that is, disable the
#                               implicit "apply" inside of each HLTAPI
#                               command).
#
#                   disable   - Do not enable optimization (that is, allow
#                               the implicit "apply" inside of each HLTAPI
#                               command).
#
#                   sync      - Applies the configuration created in HLTAPI to
#                               the card.
#
#                   You must specify an action. There is no default.
#
#    -parser
#                   Specifies which parser you want HLTAPI to use. Possible
#                   values are:
#
#                   cisco -   Use the Cisco parser function (parse_dashed_arg)
#                             for parsing. It is  slower but more sophisticated
#                             than the Spirent parser.
#
#                   spirent - Use the Spirent parser function
#                             (parse_dashed_args) for parsing. It is simpler and
#                             faster than the Cisco parser.
#
#                   The default is "cisco".
#
# Return Values:
#    The sth::test_control function returns a keyed list using the
#    following keys (with corresponding data):
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
#
# Description:
#    The sth::test_control function enables you to control optimization settings
#    and choose whether to use the Cisco or Spirent parser during test runs.
#
#    The function returns a status value (1 for success). If there is an error,
#    the function returns the status value (0) and an error message.
#
# Examples: See Sample Input and Sample Output.
#
# Sample Input:
#    sth::test_control -action enable;    //To turn off the implicit apply
#    sth::test_control -action disable:   //To allow implicit apply
#    sth::test_control -action sync;      //To call apply explicitly
#    sth::test_control -parser CSICO;     //to use CISCO parser
#    sth::test_control -parser spirent;   //to use Spirent parser
#
# Sample Output:
#
#    On success:
#    {status 1} {log {}}
#
#    On failure:
#    {status 0} {log {<errorMsg>}}
#
# Notes:
#
#
# End of Procedure Header

proc ::sth::test_control { args } {
    ::sth::sthCore::Tracker ::sth::test_control  $args 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
    
    set cmdName "::sth::testconfigcontrol::test_control_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error messag is raised"
            ::sth::sthCore::log error $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::testconfigcontrol::test_control_imp { args } {
    #::sth::sthCore::Tracker ::sth::test_control $args
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit   ::sth::testconfigcontrol::testconfigcontrolTable $args\
                                  ::sth::testconfigcontrol::\
                                  test_control\
                                  userArgsArray\
                                  sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "testconfigcontrol ::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }

    set cmd test_control
    set mynamespace ::sth::testconfigcontrol::
    foreach prioritySwitchpair $sortedSwitchPriorityList {
        set index [lindex $prioritySwitchpair 0]
        set myswitch [lindex $prioritySwitchpair end]
        set switchVal $userArgsArray($myswitch)
        if {![string compare -nocase $myswitch action]} {
            switch $switchVal {
                enable {
                    set ::sth::sthCore::optimization 1
                }
                disable {
                    set ::sth::sthCore::optimization 0
                }
                sync {
                    ::sth::sthCore::invoke "stc::apply"
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Invalid call: ::sth::test_control -action $switchVal"
                    return $returnKeyedList
                }
            }
        } elseif { ![string compare -nocase $myswitch parser] } {
            switch $switchVal {
                cisco {
                    set ::sth::sthCore::use_parse_dashed_args_option cisco
                }
                spirent {
                    set ::sth::sthCore::use_parse_dashed_args_option spirent
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Invalid call: ::sth::test_control -parser $switchVal"
                    return $returnKeyedList
                }
            }
        } elseif { ![string compare -nocase $myswitch UseModifier4TrafficBinding ] } {
            set ::sth::sthCore::UseModifier4TrafficBinding $switchVal
        }
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
