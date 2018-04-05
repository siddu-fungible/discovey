# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/pppoxServer.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::PppoxServer:: {

}

proc ::sth::pppox_server_config { args } {
    
    ::sth::sthCore::Tracker "::sth::pppox_server_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "pppox_server_config"
    
    variable ::sth::PppoxServer::sortedSwitchPriorityList
    variable ::sth::PppoxServer::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::PppoxServer::userArgsArray
    array set ::sth::PppoxServer::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::PppoxServer::pppoxServerTable \
                                            $args \
                                            ::sth::PppoxServer:: \
                                            pppox_server_config \
                                            ::sth::PppoxServer::userArgsArray \
                                            ::sth::PppoxServer::sortedSwitchPriorityList} err]} {
        keylset returnKeyedList log "Error in $procName: $err"
        return $returnKeyedList  
    }
	
	set retVal [catch {
		if {!([info exists ::sth::PppoxServer::userArgsArray(handle)] || [info exists ::sth::PppoxServer::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
			return -code error $returnKeyedList   
		}

		if {([info exists ::sth::PppoxServer::userArgsArray(handle)] && [info exists ::sth::PppoxServer::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
			return -code error $returnKeyedList   
		}
		
		set modeVal create
		if {[info exists ::sth::PppoxServer::userArgsArray(mode)]} {
			set modeVal $userArgsArray(mode)
		}
		
		# check mandatory parameters for create mode
		if {$modeVal == "create"} {
			foreach param_name [list num_sessions encap protocol] { 
				if {! [info exists ::sth::PppoxServer::userArgsArray($param_name)]} {
					::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: Missing mandatory arguments $param_name." {}
					return -code error $returnKeyedList   
				}
			}
		}
		
		set cmd "::sth::PppoxServer::${hltCmdName}\_$modeVal"
		if {[catch {eval $cmd returnKeyedList} err]} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
			return -code error $returnKeyedList  
		}
		
		if {!$::sth::sthCore::optimization} {
			if {[catch {::sth::sthCore::doStcApply} err]} {
				::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $err" {}
				return -code error $returnKeyedList  
		}
		}
	} returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    return $returnKeyedList  
}


proc ::sth::pppox_server_control { args } {
    
    ::sth::sthCore::Tracker "::sth::pppox_server_control" $args
        
    set procName [lindex [info level [info level]] 0]

    variable ::sth::PppoxServer::sortedSwitchPriorityList
    variable ::sth::PppoxServer::userArgsArray
    array unset ::sth::PppoxServer::userArgsArray
    array set ::sth::PppoxServer::userArgsArray {}

    set hltCmdName "pppox_server_control"
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::PppoxServer::pppoxServerTable \
                                            $args \
                                            ::sth::PppoxServer:: \
                                            $hltCmdName \
                                            ::sth::PppoxServer::userArgsArray \
                                            ::sth::PppoxServer::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err"
        return $returnKeyedList  
    }

	set retVal [catch {
		if {!([info exists ::sth::PppoxServer::userArgsArray(handle)] || [info exists ::sth::PppoxServer::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
			return -code error $returnKeyedList   
		}
		if {([info exists ::sth::PppoxServer::userArgsArray(handle)] && [info exists ::sth::PppoxServer::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
			return -code error $returnKeyedList   
		}
		
		set hostHandleList ""
		set pppoxServerList ""
		if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
			foreach hostHandle $userArgsArray(handle) {
				if {![::sth::PppoxServer::IsPppoxServerHandleValid $hostHandle]} {
					::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not valid PPPox Server handle" {}
					return -code error $returnKeyedList
				}
			}
			
			set hostHandleList $userArgsArray(handle)            
		} elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
			
			foreach port_handle $userArgsArray(port_handle) {
				if {[::sth::sthCore::IsPortValid $port_handle err]} {
					if {[catch {set hostHandle [::sth::sthCore::invoke stc::get $port_handle -affiliationport-sources]} err]} {
						::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
						return -code error $returnKeyedList   
					}
					
				} else {
					::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
					return -code error $returnKeyedList
				}
				foreach host $hostHandle {
					set host_name [::sth::sthCore::invoke stc::get $host -name]
					if {[regexp {^port_address$} $host_name]} {
						continue
					}
					if {![::sth::PppoxServer::IsPppoxServerHandleValid $host]} {
						continue
					}
					lappend hostHandleList $host
				}
			}       
		}
		
		if {[llength $hostHandleList] == 0} {
			::sth::sthCore::processError returnKeyedList "Error: No valid PPPox Server handle specified" {}
			return -code error $returnKeyedList
		}
		
		foreach host $hostHandleList {
			if {[catch {set port [::sth::sthCore::invoke stc::get $host -AffiliationPort-targets]} err]} {
				::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
				return -code error $returnKeyedList 
			}
			set pppoxBlock [set ::sth::PppoxServer::PPPOXSERVEROBJTYPE($port)]ServerBlockConfig
			
			if {[catch {set pppoxBlockHandle [::sth::sthCore::invoke stc::get $host -children-$pppoxBlock]} err]} {
				::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
				return -code error $returnKeyedList   
			}
			lappend pppoxServerList $pppoxBlockHandle
		}

		# Action is mandatory
		if {! [info exists userArgsArray(action)]} {
			::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires argument -action." {}
			return -code error $returnKeyedList
		}

		set action [string tolower $userArgsArray(action)]

		switch -exact -- $action {
			connect -
			disconnect -
			reset -
			pause -
			resume -
			clear -
			retry -
			abort {
				if {[catch {::sth::sthCore::invoke stc::perform [set ::sth::PppoxServer::${hltCmdName}_action_fwdmap($action)] -BlockList $pppoxServerList} err]} {
					::sth::sthCore::processError returnKeyedList "Error in $procName: Perform $action pppox server Failed: $err" {}
					return -code error $returnKeyedList   
				}
			}
			SHA_NO_USER_INPUT {
				::sth::sthCore::processError returnKeyedList "No Value for -action Value:$action." {}
				return -code error $returnKeyedList   
			}
			SHA_UNKNWN_SWITCH -
			default {
				::sth::sthCore::processError returnKeyedList "Unknown Value for -action Value:$action." {}
				return -code error $returnKeyedList   
			}
		}

		if {$action == "clear"} {
			# Delay to allow time for stats to clear
			# May need to make value dependent on number of hosts, sessions, etc.
			after 5000
		}
		if {$action == "reset"} {
			# Must delete all stale objects, the lower layer does not take care of this
			foreach host $hostHandleList {
				if {[catch {::sth::sthCore::invoke stc::delete $host} err ]} {
					::sth::sthCore::log error "Error deleting previously created Host:$host: $err"
				}
			}
		}
	}  returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    return $returnKeyedList  
}


proc ::sth::pppox_server_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::PppoxServer::sortedSwitchPriorityList
    variable ::sth::PppoxServer::userArgsArray
    array unset ::sth::PppoxServer::userArgsArray
    array set ::sth::PppoxServeruserArgsArray {}

    set hltCmdName "pppox_server_stats"

    ::sth::sthCore::Tracker "::sth::pppox_server_stats" $args

    set returnKeyedList ""
	
	set retVal [catch {
		if {[catch {::sth::sthCore::commandInit ::sth::PppoxServer::pppoxServerTable \
												$args \
												::sth::PppoxServer:: \
												$hltCmdName \
												::sth::PppoxServer::userArgsArray \
												::sth::PppoxServer::sortedSwitchPriorityList} err]} {
			keylset returnKeyedList log "Error in $procName: ::sth::sthCore::commandInit $err"
			return -code error $returnKeyedList  
		}

		if {!([info exists userArgsArray(handle)] || [info exists userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
			return -code error $returnKeyedList   
		}
		
		if {([info exists userArgsArray(handle)] && [info exists userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
			return -code error $returnKeyedList   
		}

		if {[catch {::sth::PppoxServer::pppox_server_stats returnKeyedList} err]} {
			::sth::sthCore::processError returnKeyedList "$err" {}
			return -code error $returnKeyedList
		}
	}  returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    return $returnKeyedList  
}
