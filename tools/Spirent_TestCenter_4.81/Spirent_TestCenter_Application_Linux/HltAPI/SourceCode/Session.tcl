# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and  / or subsidiaries.

namespace eval ::sth {
}



namespace eval ::sth::Session:: {
    set fillTraffic all
    set fillIsIsDevice all
    
	array set PORTHNDLIST {}
	array set CHASSISID2DEVICEMAP {}
	array set PERPORTSTREAMCOUNTTOBEARPED {}
	array set PERPORTARPRESULTHANDLE {}
	array set PORTLEVELARPSENDREQUEST {}
	array set PORTLEVELARPDONE {}
	set macAddrFormat ""
	set nosOfColonsDotsDashes ""
	set MacAddress ""
	set sessionInterfaceStats 0
	set isEotIntStats 0
	set intStats 0
	set xmlFlag 0
    # This table is used for subscribing results after loadxml
    set ::sth::Session::resultTable {
        ::sth::Session::
        {result
            {class                              resulttype                         relatedtype                                     supported}
            {pppoeclientblockconfig             PppoeClientBlockResults            {pppoxportconfig PppoePortResults}              true}
            {pppoeserverblockconfig             PppoeServerBlockResults            {pppoxportconfig PppoePortResults}              true}
            {dhcpv6serverconfig                 Dhcpv6ServerResults                {Dhcpv6PortConfig Dhcpv6PortResults}            true}
            {dhcpv6blockconfig                  Dhcpv6BlockResults                 {Dhcpv6PortConfig Dhcpv6PortResults}            true}
            {dhcpv6pdblockconfig                Dhcpv6BlockResults                 {Dhcpv6PortConfig Dhcpv6PortResults}            true}
            {dhcpv4serverconfig                 Dhcpv4ServerResults                {Dhcpv4PortConfig Dhcpv4PortResults}            true}
            {dhcpv4blockconfig                  Dhcpv4BlockResults                 {Dhcpv4PortConfig Dhcpv4PortResults}            true}
        }
    }
}

proc ::sth::labserver_connect { args } {
    ::sth::sthCore::Tracker :: "::sth::labserver_connect" $args
    variable ::sth::userArgsArray
    variable ::sth::sortedSwitchPriorityList 
     array unset userArgsArray
     array set userArgsArray {}
     variable ::sth::sthCore::SUCCESS
     variable ::sth::sthCore::FAILURE
     set returnKeyedList ""

    keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  labserver_connect \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] labserver_connect commandInit FAILED. $eMsg" {}
        return $returnKeyedList
     }
    set retVal [catch {    
		set lab_server $userArgsArray(server_ip)
		set sessionname $userArgsArray(session_name)
		set username $userArgsArray(user_name)
		set sessionflag $userArgsArray(keep_session)
		if {$userArgsArray(create_new_session) == 0} {
		    ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession false -testsessionname $sessionname -ownerid $username
            #function to support actions on streamblock[currently action run is supported]
            ::sth::fill_global_variables
		} else {
            if {[catch {::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname -ownerid $username} err]} {
                if {[regexp -nocase "already exists" $err]} {
                    set cstestsessionlist [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(system)\.csserver -children-cstestsession]
                    set session_list ""
                    foreach ls $cstestsessionlist {
                           catch {append session_list [::sth::sthCore::invoke stc::get $ls -name]}
                           append session_list " "
                    }
                    set mynum 1
                    while {[regexp "$sessionname\_$mynum" $session_list]} {
                        incr mynum
                    }
                    set i 1
                    if {$sessionflag} {
                        #puts "testsession with the same id existing, will check session state first"
                        foreach ls $cstestsessionlist {
                            if { ![catch {set session_name [::sth::sthCore::invoke stc::get $ls -name]} err1]} {
                                if {[string equal $session_name "$sessionname - $username"]} {
                                    if { ![catch {set tsstate [::sth::sthCore::invoke stc::get $ls -TestSessionState]} err2]} {
                                        if {[regexp -nocase "NONE|UNKNOWN_ERROR|SEQUENCER_IDLE" $tsstate]} {
                                            if {![catch {::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession false -testsessionname $sessionname -ownerid $username
                                                        ::sth::sthCore::invoke stc::perform CSTestSessionDisconnectCommand  -Terminate  1} myerr]} {
                                                while {1} {
                                                    if {[catch {::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname -ownerid $username} err]} {
                                                        if {[regexp -nocase "already exists" $err]} {
                                                            ::sth::sthCore::invoke stc::sleep 1
                                                            incr i
                                                            if {$i==60} {
                                                                puts "Deleting test session $sessionname - $username on Labserver is timeout(60s), creating new session \"$sessionname\_$mynum\" "
                                                                ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname\_$mynum -ownerid $username
                                                                break
                                                            }
                                                        }
                                                    } else {
                                                        break
                                                    }
                                                }
                                            } else {
                                                #now create a new one by appending _1 at the end of the session name.
                                                puts "Failed deleting test session $sessionname - $username on Labserver, creating new session \"$sessionname\_$mynum\" "
                                                ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname\_$mynum -ownerid $username
                                            }
                                        } else {
                                            #now create a new one by appending _1 at the end of the session name.
                                            puts "Not deleting test session $sessionname - $username on Labserver because its state is $tsstate, creating new session \"$sessionname\_$mynum\" "
                                            ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname\_$mynum -ownerid $username
                                        }
                                    }
                                }
                            }
                        }
                    } else {
                        if {![catch {::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession false -testsessionname $sessionname -ownerid $username
                                    ::sth::sthCore::invoke stc::perform CSTestSessionDisconnectCommand  -Terminate  1} myerr]} {
                            while {1} {
                                if {[catch {::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname -ownerid $username} err]} {
                                    if {[regexp -nocase "already exists" $err]} {
                                        ::sth::sthCore::invoke stc::sleep 1
                                        incr i
                                        if {$i==60} {
                                            puts "Deleting test session $sessionname - $username on Labserver is timeout(60s), creating new session \"$sessionname\_$mynum\" "
                                            ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname\_$mynum  -ownerid $username
                                            break
                                        }
                                    }
                                } else {
                                    break
                                }
                            }
                        } else {
                            #now create a new one by appending _1 at the end of the session name.
                            puts "Failed deleting test session $sessionname - $username on Labserver, creating new session \"$sessionname\_$mynum\" "
                            ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession true -testsessionname $sessionname\_$mynum  -ownerid $username
                        }
                    }
                }
            }
		}
		set ::sth::serverflag 1
	} returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    
    keylset returnKeyedList procName labserver_connect
    return $returnKeyedList
}

proc ::sth::labserver_disconnect { args } {
    ::sth::sthCore::Tracker :: "::sth::labserver_disconnect" $args
    variable ::sth::userArgsArray
    variable ::sth::sortedSwitchPriorityList 
     array unset userArgsArray
     array set userArgsArray {}
     variable ::sth::sthCore::SUCCESS
     variable ::sth::sthCore::FAILURE
     set returnKeyedList ""

    keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  labserver_disconnect \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] labserver_disconnect commandInit FAILED. $eMsg" {}
        return $returnKeyedList
     }
	 
	 set retVal [catch {
        if {[info exists userArgsArray(server_ip)] && [info exists userArgsArray(terminate_session)]} {
            set lab_server $userArgsArray(server_ip)
            if {[info exists userArgsArray(session_name)] && [info exists userArgsArray(user_name)]} {
                ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -createnewtestsession false  -testsessionname $userArgsArray(session_name) -ownerid $userArgsArray(user_name)
                ::sth::sthCore::invoke stc::perform CSTestSessionDisconnectCommand  -Terminate  $userArgsArray(terminate_session)
            } else {
                ::sth::sthCore::invoke stc::perform CSServerConnect -host $lab_server
                if {[set cstestsessions [::sth::sthCore::invoke stc::get system1.csserver "-children-cstestsession"]] != ""} {
                    if {$cstestsessions != ""} {
                        puts $cstestsessions
                        foreach cstestsession  $cstestsessions  {
                             puts $cstestsession
                             ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $lab_server -TestSession  $cstestsession
                             ::sth::sthCore::invoke stc::perform CSTestSessionDisconnectCommand  -Terminate  $userArgsArray(terminate_session)
                        }
                    }
                }
            }
        } elseif {[info exists userArgsArray(terminate_session)]} {
           ::sth::sthCore::invoke stc::perform CSTestSessionDisconnectCommand  -Terminate  $userArgsArray(terminate_session)
        }
        
		set ::sth::serverflag 0
	}  returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}

    keylset returnKeyedList procName labserver_disconnect
    return $returnKeyedList
}


proc ::sth::connect { args } {
    ::sth::sthCore::Tracker ::sth::connect  $args 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
     
    #add labserver check here
    if {[catch {set returnKeyedList [::sth::Session::labserverHandler]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with emptry error messag is raised when handling lab server"
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in labserverHandler -->$errMsg";    
    }
    if {[catch {
        set ::sth::sthCore::GBLHNDMAP(project) [::sth::sthCore::invoke "stc::create project"]
        set ::sth::GBLHNDMAP(project) $::sth::sthCore::GBLHNDMAP(project)
        set ::sth::sthCore::GBLHNDMAP(system)  [::stc::get $::sth::sthCore::GBLHNDMAP(project) -parent]
        set ::sth::sthCore::GBLHNDMAP(sequencer) [::stc::get $::sth::sthCore::GBLHNDMAP(system) -children-sequencer]
	} errMsg]} {
	::sth::sthCore::processError returnKeyedList "error when creating stc project: $errMsg"
    }
       
    set cmdName "::sth::Session::connect_imp $args"
    if {[lsearch -exact $args "-chassis_list"] != -1 ||
        [lsearch -exact $args "-slot_list"] != -1 ||
        [lsearch -exact $args "-location_list"] != -1} {    
        set cmdName "::sth::Session::reserveports_imp $args"
    } 

    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::Session::connect_imp { args } {
    
     set connectKeyedList ""
     variable userArgsArray;
     array set userArgsArray {};
     variable sortedSwitchPriorityList {};
     variable ::sth::sthCore::SUCCESS;
     variable ::sth::sthCore::FAILURE;
     
     ::sth::sthCore::log debug "{Calling sth::connect}"
     
     ::sth::sthCore::log info "{Generating session table}"
     set args1 "-mode aggregate"
     if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficTable $args1 \
                                     ::sth::Traffic:: \
                                     traffic_stats \
                                     userArgsArray1 \
                                     sortedSwitchPriorityList1} eMsg]} {
         ::sth::sthCore::log debug "\[Traffic\] commandInit FAILED. $eMsg";
           #::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
           return 
      } 
        
     if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  connect \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError connectKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
        return $connectKeyedList;
     }
      if {$::sth::Session::xmlFlag == 1} {
         set unMatchPort [expr [llength $userArgsArray(port_list)] - [llength [::sth::sthCore::invoke stc::get project1 -children-port]]]
         if {$unMatchPort > 0} {
             ::sth::sthCore::processError connectKeyedList "portlist parameters are unmatched in the loaded config file, the number of unmatched port is $unMatchPort " {}
             return $connectKeyedList
         }
     }    
     if {[llength $userArgsArray(port_list)] == 0} {
         ::sth::sthCore::processError connectKeyedList "internal operation failed as missing portlist parameters" {}
         return $connectKeyedList
     } elseif {[llength $userArgsArray(device)] == 0} {
         ::sth::sthCore::processError connectKeyedList "internal operation failed as missing device parameter" {}
         return $connectKeyedList
     }
     
     keylset connectKeyedList offline 0
     if { [info exists userArgsArray(offline)] && ($userArgsArray(offline) == 1) } {
         set myFunc ::sth::Session::processOfflinePort
         set cmdResult [eval $myFunc]
         if {$cmdResult == $::sth::sthCore::FAILURE} {
             set cmdFailed ::sth::sthCore::FAILURE
         }
         keylset connectKeyedList offline 1
     } else {
         if {[info exists userArgsArray(username)]} {
             set cmdResult [::sth::Session::processConnectUsername]
             if {$cmdResult == $::sth::sthCore::FAILURE} {
               ::sth::sthCore::processError connectKeyedList "internal operation failed while setting username" {}
                 return $connectKeyedList
             }
         }
            
         foreach key $sortedSwitchPriorityList {
             set switchName [lindex $key 1]
             set myFunc $::sth::Session::connect_procfunc($switchName)
             ::sth::sthCore::log info "{Calling: $myFunc}"
             if {[string equal $myFunc "_none_"]} {
             } else {
                 set cmdResult [eval $myFunc]
                 if {$cmdResult == $::sth::sthCore::FAILURE} {
                  set cmdFailed ::sth::sthCore::FAILURE
                  break
                 } 
             }
            
         }
     }
     if {[::info exists cmdFailed]} {
        ::sth::sthCore::processError connectKeyedList "internal operation failed with connect: $connectKeyedList" {}
        return $connectKeyedList
    } else {
        ::sth::Session::SetFECTrue100Gig
        keylset connectKeyedList status $::sth::sthCore::SUCCESS;
        return $connectKeyedList
    }
}


proc ::sth::interface_config { args } {
    ::sth::sthCore::Tracker ::sth::interface_config $args 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
    
    set cmdName "::sth::Session::interface_config_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName \{ $args \} --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::Session::interface_config_imp { args } {

    set _hltCmdName "interface_config"
    set interfaceConfKeyList ""
    variable sessionTable
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {};
    variable sortedSwitchPriorityList {};
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::objecttype
    
    ::sth::sthCore::log debug "{Calling: sth::interface_config}"
    ::sth::sthCore::log info "{Generating session table}"
    array set usrArray {}
    array set usrArray $args
    set modify_without_phy_mode 0
	
    #US35322 - to use lists of ports in HLTAPI.
    if {[info exists usrArray(-port_handle)] && [string match -nocase "all" $usrArray(-port_handle)]} {
        set listOfpHandles [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"]
    } else {
        set listOfpHandles $usrArray(-port_handle);
    }
    
    foreach usrArray(-port_handle) $listOfpHandles {
        if {[info exists usrArray(-mode)] && $usrArray(-mode) == "modify" && (![info exists usrArray(-phy_mode)])} {
            set modify_without_phy_mode 1
        }
        
        # AtmPhy, Ethernet100GigFiber, Ethernet10GigCopper, Ethernet10GigFiber, Ethernet25GigFiber, Ethernet40GigFiber,
        #Ethernet50GigFiber, EthernetCopper, EthernetFiber, FcPhy, Ieee80211Phy, POSPhy, Wimax16dPhy
        if {[catch {::sth::sthCore::invoke stc::get $usrArray(-port_handle) -ActivePhy-targets} activePhy]} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error while getting active physical layer interfaces." {}
            return $interfaceConfKeyList
        }

        #get the supported physical layer interfaces under the port
        if {[catch {::sth::sthCore::invoke stc::get $usrArray(-port_handle) -supportedPhys} SupportedPhys]} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error while getting supported physical layer interfaces." {}
            return $interfaceConfKeyList
        }
        
        set detectPhy $SupportedPhys
        set existLineSpeed 0
        if {$activePhy != ""} {
            set detectPhy $activePhy
            catch {set existLineSpeed [::sth::sthCore::invoke stc::get $activePhy -LineSpeed]}
        }

        if {[info exists usrArray(-phy_mode)]} {
            set mediatypemode $usrArray(-phy_mode)
        } else {
            if {[info exists usrArray(-speed)] && ([regexp "ether40Gig" $usrArray(-speed)] ||
                [regexp "ether100Gig" $usrArray(-speed)] || [regexp "ether25Gig" $usrArray(-speed)] || 
                [regexp "ether50Gig" $usrArray(-speed)])} {
                    set mediatypemode "fiber"
                    set usrArray(-phy_mode) "fiber"
            } else {
                if {[regexp -nocase "fiber" $detectPhy]} {
                    set mediatypemode "fiber"
                    set usrArray(-phy_mode) "fiber"
                } else {
                    set mediatypemode "copper"
                    set usrArray(-phy_mode) "copper"
                }
            }
        }
        # Determine if the port is online (we may be operating in offline mode).
        set online [::sth::sthCore::invoke stc::get $usrArray(-port_handle) -Online]
        if {![regexp -nocase $usrArray(-phy_mode) $detectPhy] && $online} {
            if {[regexp -nocase "ethernet_copper" $detectPhy] || [regexp -nocase "ethernet_fiber" $detectPhy] } {
                ::sth::sthCore::processError interfaceConfKeyList "port type mismatch: $usrArray(-phy_mode), $detectPhy." {}
                return $interfaceConfKeyList
            }
        }

        if {[info exists usrArray(-intf_mode)]} {
            if {([string equal $usrArray(-intf_mode) "pos_hdlc"]) || ([string equal $usrArray(-intf_mode) "pos_ppp"])} {
                set mediatypemode "POSPhy"
            } elseif {([string equal $usrArray(-intf_mode) "atm"])} {
                set mediatypemode "AtmPhy"
            } elseif {([string equal $usrArray(-intf_mode) "fc"])} {
                set mediatypemode "FcPhy"
            }
        } else {
            #get the interface mode if the intf_mode is not configured: atm, pos, ethernet
            switch -exact $SupportedPhys {
                "fc" {
                     set mediatypemode "FcPhy"
                     set usrArray(-intf_mode) "fc"
                }
                "atm" {
                     set mediatypemode "AtmPhy"
                     set usrArray(-intf_mode) "atm"
                }
                "pos" {
                    set mediatypemode "POSPhy"
                    set usrArray(-intf_mode) "pos_dhlc"
                }
                default {
                    set usrArray(-intf_mode) "ethernet"
                }
            }
        }
        if {[info exists usrArray(-speed)]} {
            set speedmode $usrArray(-speed)
        } else {
            if {([string equal $usrArray(-intf_mode) "pos_hdlc"]) || ([string equal $usrArray(-intf_mode) "pos_ppp"])} {
                    set speedmode "oc192"
            } elseif {[string equal $usrArray(-intf_mode) "atm"]} {
                    set speedmode "oc12"
            } elseif {[string equal $usrArray(-intf_mode) "fc"]} {
                    set speedmode "ether2000"
            } else {
                if {[string equal $usrArray(-phy_mode) "fiber"]} {
                    set speedmode "ether1000"
                } elseif {[string equal $usrArray(-phy_mode) "copper"]} {
                   # here only deal with the Ethernet10GigCopper, for the Ethernet10GigFibber, Ethernet40GigFibber, Ethernet100GigFibber
                   # maybe also need to take care of
                    if {[regexp -nocase "10GIG" $detectPhy] || [regexp -nocase "10_GIG" $detectPhy]} {
                        set speedmode "ether10Gig"
                    } else {
                        set speedmode "ether10"
                    }
                }
            }
        }
        
        set ::sth::sthCore::objecttype "EthernetCopper"
        if {[string match -nocase $mediatypemode "copper"] && \
            [string equal -nocase "ETHERNET_10_GIG_COPPER" $SupportedPhys] \
            && (([string match -nocase $speedmode "ether5Gig"]) || \
                ([string match -nocase $speedmode "ether2500"]) || \
                ([string match -nocase $speedmode "ether100"]) || \
                ([string match -nocase $speedmode "ether1000"]))} {
            set ::sth::sthCore::objecttype "Ethernet10GigCopper"
        } elseif {[string match -nocase $mediatypemode "copper"] && [string match -nocase $speedmode "ether10Gig"]} {
            set ::sth::sthCore::objecttype "Ethernet10GigCopper"
        } elseif {[string match -nocase $mediatypemode "copper"] && [string match -nocase $speedmode "ether10000"]} {
            set ::sth::sthCore::objecttype "Ethernet10GigCopper"
        } elseif {[string match -nocase $mediatypemode "copper"] && (([string match -nocase $speedmode "ether10"]) || ([string equal $speedmode "ether100"]))} {
            set ::sth::sthCore::objecttype "EthernetCopper"
        } elseif {([string match -nocase $mediatypemode "fiber"]) && ([string match -nocase $speedmode "ether1000"])} {
            set ::sth::sthCore::objecttype "EthernetFiber"
        } elseif {([string match -nocase $mediatypemode "fiber"]) && ([string match -nocase $speedmode "ether10000"])} {
            set ::sth::sthCore::objecttype "Ethernet10GigFiber"
        } elseif {([string match -nocase $mediatypemode "fiber"]) && (([string match -nocase $speedmode "ether10"]) || ([string match -nocase $speedmode "ether100"]))} {
            set ::sth::sthCore::objecttype "EthernetFiber"
        } elseif {[string match -nocase $mediatypemode "fiber"] && [string match -nocase $speedmode "ether100Gig"]} {
            set ::sth::sthCore::objecttype "Ethernet100GigFiber"
        }  elseif {[string match -nocase $mediatypemode "fiber"] && [string match -nocase $speedmode "ether25Gig"]} {
            set ::sth::sthCore::objecttype "Ethernet25GigFiber"
        }  elseif {[string match -nocase $mediatypemode "fiber"] && [string match -nocase $speedmode "ether40Gig"]} {
            set ::sth::sthCore::objecttype "Ethernet40GigFiber"
        }  elseif {[string match -nocase $mediatypemode "fiber"] && [string match -nocase $speedmode "ether50Gig"]} {
            set ::sth::sthCore::objecttype "Ethernet50GigFiber"
        } elseif {([string match -nocase $mediatypemode "POSPhy"])} {
            switch -exact $speedmode {
            "ether100" -
            "ether1000" -
            "ether10000" -
            "oc3" -
            "oc12" -
            "oc48" -
            "oc192" {set ::sth::sthCore::objecttype "POSPhy"}
            default {set ::sth::sthCore::objecttype "EthernetCopper"}
            }
        } elseif {[string match -nocase $mediatypemode "AtmPhy"]} {
            set ::sth::sthCore::objecttype "AtmPhy"
        } elseif {[string match -nocase $mediatypemode "FcPhy"]} {
            set ::sth::sthCore::objecttype "FcPhy"
        } 

        # For modify mode, added by xiaozhi
        if {[info exists usrArray(-mode)] && $usrArray(-mode) == "modify" && ($modify_without_phy_mode)} {
            set portHandle $usrArray(-port_handle)
            set phy [::sth::sthCore::invoke stc::get $portHandle "-activephy-Targets"]
            switch -glob [string tolower $phy] {
                 "ethernetcopper*" {set ::sth::sthCore::objecttype "EthernetCopper"}
                 "ethernet10gigcopper*" {set ::sth::sthCore::objecttype "Ethernet10GigCopper"}
                 "ethernetfiber*" {set ::sth::sthCore::objecttype "EthernetFiber"}
                 "ethernet10gigfiber*" {set ::sth::sthCore::objecttype "Ethernet10GigFiber"}
                 "ethernet100gigfiber*" {set ::sth::sthCore::objecttype "Ethernet100GigFiber"}
                 "ethernet40gigfiber*" {set ::sth::sthCore::objecttype "Ethernet40GigFiber"}
                 "ethernet25gigfiber*" {set ::sth::sthCore::objecttype "Ethernet25GigFiber"}
                 "ethernet50gigfiber*" {set ::sth::sthCore::objecttype "Ethernet50GigFiber"}
                 "posphy*" {set ::sth::sthCore::objecttype "POSPhy"}
                 "atmphy*" {set ::sth::sthCore::objecttype "AtmPhy"}
                 "fcphy*" {set ::sth::sthCore::objecttype "FcPhy"}
                 default {
                    set ::sth::sthCore::objecttype "EthernetCopper"
                 }
            }
        }
        
        if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                      ::sth::Session:: \
                                      interface_config\_$objecttype \
                                      userArgsArray \
                                      sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError interfaceConfKeyList "\[Session\] commandInit FAILED. $eMsg" {}
            return -code error "$eMsg"
         }
         
         keylset interfaceConfKeyList arpnd_status "none"
         keylset interfaceConfKeyList arpnd_cache "none"
         keylset interfaceConfKeyList arpnd_report "none"
         
         if {$::sth::sthCore::objecttype eq "POSPhy"} {
            set userArgsArray(arp_send_req) 0
         }
         set userArgsArray(port_handle) $usrArray(-port_handle)
         
         if {[::info exists userArgsArray(arp_send_req)]} {
            set ::sth::Session::PORTLEVELARPSENDREQUEST($userArgsArray(port_handle)) $userArgsArray(arp_send_req)
         } else {
            set ::sth::Session::PORTLEVELARPSENDREQUEST($userArgsArray(port_handle)) 1
         }
         
         if { ![::info exists ::sth::Session::PORTLEVELARPDONE($userArgsArray(port_handle))] } {
            set ::sth::Session::PORTLEVELARPDONE($userArgsArray(port_handle)) false
         }
         
             
         if {[::info exists userArgsArray(mode)]} {
            set modevalue $userArgsArray(mode)
            if {(![string equal $modevalue "config"]) && (![string equal $modevalue "modify"]) && (![string equal $modevalue "destroy"])} {
                ::sth::sthCore::processError interfaceConfKeyList "Error in <interface_config>: Invalid argument $modevalue for -mode. Valid arguments are config|modify|destroy: $interfaceConfKeyList" {}
                return $interfaceConfKeyList     
            }
                    
            ::sth::sthCore::log info "{Calling interface_config for mode: $modevalue}"
            if {([string equal $modevalue "config"]) || ([string equal $modevalue "modify"])} {
                    set myFunc ::sth::Session::interface_config_config_modify 
            } else {
                    set myFunc ::sth::Session::interface_config_$modevalue
            }
            ::sth::sthCore::log info "{Calling: $myFunc}"
            set cmdResult [eval $myFunc $modevalue]
            keylget cmdResult status cmdStatus
            if {$cmdStatus == $::sth::sthCore::FAILURE} {
                set cmdFailed ::sth::sthCore::FAILURE
            } 
        }

        if {([regexp "40" $existLineSpeed] && [regexp -nocase "Ethernet100GigFiber" $::sth::sthCore::objecttype])||
            ([regexp "100" $existLineSpeed ] && [regexp -nocase "Ethernet40GigFiber" $::sth::sthCore::objecttype])} {
            #from 100G to 40G from 40G to 100G need to release  the port and re-reserve it before the apply is called
            set portList $userArgsArray(port_handle)
            set portLocList ""
            foreach port $portList {
                lappend portLocList $::sth::Session::PORTHNDLIST($port)
            }
            #need to wait faw seconds when change the active physical ports, else the status will be NONE
            ::sth::sthCore::invoke stc::sleep 10
            ::sth::sthCore::invoke stc::perform ReleasePort -Location $portLocList -PortList $portList
            ::sth::sthCore::invoke stc::perform ReservePort -Location $portLocList -PortList $portList -RevokeOwner TRUE
            ::sth::sthCore::invoke stc::perform setupPortMappings
        }
	}
    if {[::info exists cmdFailed]} {
        ::sth::sthCore::processError interfaceConfKeyList "internal operation failed with interface_config" {}
        return $interfaceConfKeyList
    } else {
        ::sth::Session::SetFECTrue100Gig
        keylset interfaceConfKeyList status $::sth::sthCore::SUCCESS;
        if {[regexp -nocase "handles" $cmdResult]} {
            keylset interfaceConfKeyList handles [keylget cmdResult handles]
        }
        return $interfaceConfKeyList
    }
}

proc ::sth::interface_stats {args} {
    ::sth::sthCore::Tracker ::sth::interface_stats  $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
    
    set cmdName "::sth::Session::interface_stats_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::Session::interface_stats_imp { args } {
    set _hltCmdName "interface_stats"
    set interfaceStatsKeyList ""
    variable sessionTable
    variable userArgsArray
    array unset userArgsArray;
    variable sortedSwitchPriorityList {};
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    set port_list ""
    set genresult_keys ""
    set anaresult_keys ""
    set fcresult_keys ""
    set sysmonitorresult_keys ""

    ::sth::sthCore::log debug "{Calling: sth::interface_stats}"
    ::sth::sthCore::log info "{Generating session table}"
    
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  interface_stats \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError interfaceStatsKeyList "\[Session\] commandInit FAILED. $eMsg" {}
        return $interfaceStatsKeyList;
    }
    
    if {([info exists userArgsArray(port_handle)] && [info exists userArgsArray(port_handle_list)])} {
        ::sth::sthCore::processError interfaceStatsKeyList "Error in $_hltCmdName: The options -port_handle and -port_handle_list are mutually exclusive." {}
        return $interfaceStatsKeyList;
    }

    if {[info exists userArgsArray(port_handle)]} {
        set port_list $userArgsArray(port_handle)
    } elseif {[info exists userArgsArray(port_handle_list)]} {
        set port_list $userArgsArray(port_handle_list)
    }
    
    if {[info exists userArgsArray(properties)]} {
	    set genresult_keys [sth::Traffic::getTypeProperties gen $userArgsArray(properties)]
	    set anaresult_keys [sth::Traffic::getTypeProperties ana $userArgsArray(properties)]
        set fcresult_keys [sth::Traffic::getTypeProperties fc $userArgsArray(properties)]
        
        if {$genresult_keys == ""} {
            set genresult_keys "_none_"
        }
        if {$anaresult_keys == ""} {
            set anaresult_keys "_none_"
        }
        
        if {$fcresult_keys == ""} {
            set fcresult_keys "_none_"
        }
    }

    if {$sth::Traffic::isEOTResults ==0} {
        if {$port_list != ""} {
            foreach port $port_list {
                set ::sth::Traffic::aggTxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_txjoin Generator GeneratorPortResults portlevel $port $genresult_keys]
                set ::sth::Traffic::aggRxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer AnalyzerPortResults portlevel $port $anaresult_keys]
                set ::sth::Traffic::fcresultDataset [::sth::Traffic::processTrafficStatsSubscribeCounters fc_port Port fcResults portlevel $port $fcresult_keys]
                if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                    set ::sth::Traffic::systemMonitorDataset [::sth::Traffic::processTrafficStatsSubscribeCounters system_monitor PhysicalPortGroup SystemMonitorResults portlevel $port $sysmonitorresult_keys]
                }
                ::sth::Traffic::delay "GeneratorPortResults AnalyzerPortResults"
                #Call function to get the list of supported counters
                set cmdResult [::sth::Session::getStatsVarsFromTable $port]

                if {$cmdResult == $::sth::sthCore::FAILURE} {
                    set cmdFailed ::sth::sthCore::FAILURE
                }
                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggTxjoinDataset
                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxjoinDataset
                ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::fcresultDataset
                if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                    ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::systemMonitorDataset
                }

                if {[info exists userArgsArray(port_handle_list)]} {
                    keylset tempStatsList $port $interfaceStatsKeyList
                    set interfaceStatsKeyList ""
                }
            }
        } else {
            set cmdFailed ::sth::sthCore::FAILURE
        }
   } else {
        #EOT Results
         if {$sth::Traffic::EOTResultsFileNameCurrent == 0} {
            ::sth::sthCore::log warn "No DB File is saved after traffic stopped, so the real time results return";
            if {$port_list != ""} {
                foreach port $port_list {
                    set ::sth::Traffic::aggTxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_txjoin Generator GeneratorPortResults portlevel $port $genresult_keys]
                    set ::sth::Traffic::aggRxjoinDataset [::sth::Traffic::processTrafficStatsSubscribeCounters aggregate_rxjoin Analyzer AnalyzerPortResults portlevel $port $anaresult_keys]
                    set ::sth::Traffic::fcresultDataset [::sth::Traffic::processTrafficStatsSubscribeCounters fc_port Port fcResults portlevel $port $fcresult_keys]
                    if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                        set ::sth::Traffic::systemMonitorDataset [::sth::Traffic::processTrafficStatsSubscribeCounters system_monitor PhysicalPortGroup SystemMonitorResults portlevel $port $sysmonitorresult_keys]
                    }
                    ::sth::Traffic::delay "GeneratorPortResults AnalyzerPortResults"
                    #Call function to get the list of supported counters
                    set cmdResult [::sth::Session::getStatsVarsFromTable $port]

                    if {$cmdResult == $::sth::sthCore::FAILURE} {
                        set cmdFailed ::sth::sthCore::FAILURE
                    }
                    ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggTxjoinDataset
                    ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::aggRxjoinDataset
                    ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::fcresultDataset
                    if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                        ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::systemMonitorDataset
                    }

                    if {[info exists userArgsArray(port_handle_list)]} {
                        keylset tempStatsList $port $interfaceStatsKeyList
                        set interfaceStatsKeyList ""
                    }
                }
            } else {
                set cmdFailed ::sth::sthCore::FAILURE
            }
        } else {
            set ::sth::Session::isEotIntStats 1
            if {$port_list != ""} {
                foreach port $port_list {
                    if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                        set ::sth::Traffic::systemMonitorDataset [::sth::Traffic::processTrafficStatsSubscribeCounters system_monitor PhysicalPortGroup SystemMonitorResults portlevel $port $sysmonitorresult_keys]
                    }
                    set cmdResult [::sth::Session::getStatsVarsFromTable $port]
                    if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                        ::sth::Traffic::processUnSubscribeProjectLevelCounters $::sth::Traffic::systemMonitorDataset
                    }
                    if {[info exists userArgsArray(port_handle_list)]} {
                        keylset tempStatsList $port $interfaceStatsKeyList
                        set interfaceStatsKeyList ""
                    }
                }
            }
       }
    }

    if {[info exists userArgsArray(port_handle_list)]} {
        set interfaceStatsKeyList $tempStatsList
    }

    if {[::info exists cmdFailed]} {
        ::sth::sthCore::processError interfaceStatsKeyList "internal operation failed with interface_stats" {}
        return $interfaceStatsKeyList
    } else {
        keylset interfaceStatsKeyList status $::sth::sthCore::SUCCESS;
        if {$sth::Traffic::eotPortQueryEmpty == 1} {
            ::sth::sthCore::log warn "Port stats are not available at this time, please check your configuration";
            set sth::Traffic::eotPortQueryEmpty 0
        }
        return $interfaceStatsKeyList
    }
}


proc ::sth::cleanup_session {args} {
    ::sth::sthCore::Tracker ::sth::cleanup_session  $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
    
    set cmdName "::sth::Session::cleanup_session_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}
proc ::sth::Session::cleanup_session_imp { args } {
    
    set _hltCmdName "cleanup_session"
    set cleanUpSessionKeyList ""
    variable sessionTable
    array set userArgsArray {};
    variable sortedSwitchPriorityList {};
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    ::sth::sthCore::log debug "{Calling: sth::cleanup_session}"
    ::sth::sthCore::log info "{Generating session table}"
    
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  cleanup_session \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError cleanUpSessionKeyList "::sth::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $cleanUpSessionKeyList
     }
    
    foreach key $sortedSwitchPriorityList {
        set switchName [lindex $key 1]
        set myFunc $::sth::Session::cleanup_session_procfunc($switchName)
    if {$myFunc != "_none_"} {
        ::sth::sthCore::log info "{Calling: $myFunc $userArgsArray($switchName)}"
        #fix CR323427703
		if {$switchName == "port_list" || $switchName == "port_handle"} {
            set cmdResult [eval $myFunc {$userArgsArray($switchName)}]
        } else {
            set cmdResult [eval $myFunc]
        }
            
        if {$cmdResult == 0} {
            set cmdFailed 0
            break
        }
    }
    }
    
    ##delete saved database
    if {![info exists userArgsArray(clean_dbfile)]} {
        set userArgsArray(clean_dbfile) 1
    }
    if {$userArgsArray(clean_dbfile)} {
        if {($::sth::Traffic::EOTResultsFileName!="" )&&($::sth::Traffic::hltDir!="")} {
        set hltfile [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
        while {[file exists $hltfile]} {
        file delete $hltfile
                }
        }
    }
	
	
	
    ##delete lab server session clean_labserver_session
   if {$::sth::serverflag == 1} {
   if {![info exists userArgsArray(clean_labserver_session)]} {
        set userArgsArray(clean_labserver_session) 1
    }
    if {$userArgsArray(clean_labserver_session)} {
    	if {[catch {::sth::sthCore::invoke stc::perform CSTestSessionDisconnectCommand  -Terminate  1} err]} {
                ::sth::sthCore::processError cleanUpSessionKeyList "Error while disconnecting Lab-Server: $err"
        	return $cleanUpSessionKeyList
    	}
    }
   }
   ##delete stc logs and hltapi logs
    if {![info exists userArgsArray(clean_logs)]} {
        set userArgsArray(clean_logs) 0
    }
    if {$userArgsArray(clean_logs)} {
        #deleting stc logs
        array set sysPaths [stc::perform GetSystemPaths]
        set sessionDataPath $sysPaths(-SessionDataPath)
        if {($sessionDataPath!="")} {
            if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
                stc::destroy
            }
            if {[file exists $sessionDataPath]} {
                if {[catch {[file delete -force $sessionDataPath]} err] } {
                    if {[file exists $sessionDataPath]} {
                        ::sth::sthCore::invoke stc::sleep 5
                        file delete -force $sessionDataPath
                    }
                } 
            }
        }

        #Deleting hltapi logs
        if {($::sth::sthCore::logfile!="")} {
            if {[file exists $::sth::sthCore::logfile\.$::sth::sthCore::logfilesuffix ]} {
                file delete $::sth::sthCore::logfile\.$::sth::sthCore::logfilesuffix
            }
        }
        if {($::sth::sthCore::hltlogfile!="")} {
            if {[file exists $::sth::sthCore::hltlogfile\.$::sth::sthCore::hltlogfilesuffix]} {
                file delete $::sth::sthCore::hltlogfile\.$::sth::sthCore::hltlogfilesuffix
            }
        }
        if {($::sth::sthCore::vendorlogfile!="")} {
            if {[file exists $::sth::sthCore::vendorlogfile\.$::sth::sthCore::vendorlogfilesuffix]} {
                file delete $::sth::sthCore::vendorlogfile\.$::sth::sthCore::vendorlogfilesuffix
            }
        }
        if {($::sth::sthCore::hlt2stcmappingfile!="")} {
            if {[file exists $::sth::sthCore::hlt2stcmappingfile\.$::sth::sthCore::hlt2stcmappingfilesuffix]} {
                file delete $::sth::sthCore::hlt2stcmappingfile\.$::sth::sthCore::hlt2stcmappingfilesuffix
            }
        }
    }
   
    if {[::info exists cmdFailed]} {
        set cleanUpSessionKeyList [::sth::sthCore::updateReturnInfo $cleanUpSessionKeyList status 0]
        ::sth::sthCore::processError cleanUpSessionKeyList "{Error: Cleanup_Session: $cleanUpSessionKeyList}"
        return $cleanUpSessionKeyList
    } else {
        set cleanUpSessionKeyList [::sth::sthCore::updateReturnInfo $cleanUpSessionKeyList status 1]
        #::sth::sthCore::log info "{SUCCESS: Cleanup_Session: $cleanUpSessionKeyList}"
        return $cleanUpSessionKeyList
    }

}

proc ::sth::device_info { args } {
    ::sth::sthCore::Tracker ::sth::device_info  $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set returnKeyedList ""
    
    set cmdName "::sth::Session::device_info_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}
proc ::sth::Session::device_info_imp { args } {
    
    set _hltCmdName "device_info"
    set deviceinfoSessionKeyList ""
    variable sessionTable
    variable userArgsArray
    array set userArgsArray {};
    variable sortedSwitchPriorityList {};
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
   
    ::sth::sthCore::log debug "{Calling: sth::device_info}"
    ::sth::sthCore::log info "{Generating session table}"

    set tablereturn [::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  device_info \
                                  userArgsArray \
                                  sortedSwitchPriorityList]
    
    if {$tablereturn == 0} {
        set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList status 0]
        return $deviceinfoSessionKeyList
     }
    
    foreach key $sortedSwitchPriorityList {
        set switchName [lindex $key 1]
        set myFunc $::sth::Session::device_info_procfunc($switchName)
        ::sth::sthCore::log info "{Calling: $myFunc}"
        set cmdResult [eval $myFunc]
    if {$cmdResult == 0} {
            set cmdFailed 0
            break
    } 
    }
    
    if {[::info exists cmdFailed]} {
        set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList status 0]
        ::sth::sthCore::processError deviceinfoSessionKeyList "{Error: Device_Info: $deviceinfoSessionKeyList}"
        return $deviceinfoSessionKeyList
    } else {
        set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList status 1]
        #::sth::sthCore::log info "{SUCCESS: Device_Info: $deviceinfoSessionKeyList}"
        return $deviceinfoSessionKeyList
    }
}

proc ::sth::interface_control { args } {
    ::sth::sthCore::Tracker ::interface_control $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::Session::interface_control\_input_and_default_args_array
    array unset interface_control\_input_and_default_args_array
    array set interface_control\_input_and_default_args_array {}
    
    variable ::sth::Session::interface_control\_sortedSwitchPriorityList
    
    set _hltCmdName "interface_control"
      
    set returnKeyedList ""
    set underScore "_"
    
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                ::sth::Session:: \
                                $_hltCmdName \
                                interface_control\_input_and_default_args_array \
                                interface_control\_sortedSwitchPriorityList } eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $eMsg" {}
        return $returnKeyedList
    }
    
    #switch to call processing functions for the mode of API
    set modeValue $::sth::Session::interface_control_input_and_default_args_array(mode)
    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"
    switch -exact $modeValue {
        break_link {
            set cmdStatus 0
            set cmd "::sth::Session::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for action($modeValue): $cmd "
        }
        restore_link {
            set cmdStatus 0
            set cmd "::sth::Session::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for action($modeValue): $cmd "
        }
        pfc_response_time {
            set cmdStatus 0
            set cmd "::sth::Session::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for action($modeValue): $cmd "
        }
        restart_autonegotiation {
            set cmdStatus 0
            set cmd "::sth::Session::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for action($modeValue): $cmd "
        }
        enable_monitor {
            set cmdStatus 0
            set cmd "::sth::Session::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for action($modeValue): $cmd "
        }
        disable_monitor {
            set cmdStatus 0
            set cmd "::sth::Session::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for action($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList                 
        }
    }

    
    if {[catch {eval $cmd} eMsg]} { 
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList                        
    }
}

proc ::sth::start_devices { args } {
    ::sth::sthCore::Tracker ::sth::start_devices  $args 
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    set cmdName "::sth::sthCore::invoke stc::perform DevicesStartAllCommand"
    if {[catch {
	    ::sth::sthCore::doStcApply
	    eval $cmdName
	} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}


proc ::sth::stop_devices { args } {
    ::sth::sthCore::Tracker ::sth::stop_devices  $args 
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    set cmdName "::sth::sthCore::invoke stc::perform DevicesStopAllCommand"
    if {[catch {eval $cmdName} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with emptry error messag is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::load_xml { args } {
    ::sth::sthCore::Tracker ::sth::load_xml  $args 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set connectKeyedList ""
    keylset connectKeyedList status $::sth::sthCore::SUCCESS
    set cmdName "::sth::Session::loadxml_imp $args"
    if {[catch {eval $cmdName} errMsg]} {
        if {[string length $errMsg] == 0} {
                ::sth::sthCore::processError connectKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError connectKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $connectKeyedList] == 0} {
            ::sth::sthCore::processError connectKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    ::sth::Session::subscribe_results
    return $connectKeyedList
}

proc ::sth::Session::loadxml_imp { args } {
     upvar connectKeyedList connectKeyedList;
     variable userArgsArray;
     array unset userArgsArray;
     array set userArgsArray {};
     variable sortedSwitchPriorityList {};
     variable ::sth::sthCore::SUCCESS;
     variable ::sth::sthCore::FAILURE;
     
     ::sth::sthCore::log debug "{Calling sth::loadxml}"
     
     ::sth::sthCore::log info "{Executing command: loadxml $args}"     
     if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  load_xml \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
        return $connectKeyedList;
     }
	 
     if {[catch {::sth::sthCore::invoke stc::perform LoadFromXml -FileName $userArgsArray(filename)} errMsg ]} {
        ::sth::sthCore::processError connectKeyedList "stc::perform LoadFromXml Failed: $errMsg"
     } else {
        set ::sth::Session::xmlFlag 1
        set ::sth::Session::xmlFilename $userArgsArray(filename)
        keylset connectKeyedList status $::sth::sthCore::SUCCESS
     }
     
    #function to support actions on streamblock[currently action run is supported]
     ::sth::fill_global_variables
     return $connectKeyedList     
}
# function to subscribe results.
proc ::sth::Session::subscribe_results { } {
    ::sth::sthCore::InitTableFromTCLList $::sth::Session::resultTable
    set subscribedList ""    
    set resultDataSetList ""
    # delete all existing result objects
    set xml_results [stc::get project1 -children-resultdataset]
    if { "" != $xml_results } {
        ::sth::sthCore::invoke stc::perform delete -ConfigList $xml_results
    }
    
    # subscribe
    set devices [stc::get project1 -children-EmulatedDevice]
    foreach device $devices {
        sth::hlapiGen::get_attr $device $device
        foreach class [array names sth::hlapiGen::$device\_obj] {
            if {[info exists sth::Session::result_supported($class)] && ("true" == $sth::Session::result_supported($class))} {
                update_subscribed_results $class $sth::Session::result_resulttype($class) resultDataSetList subscribedList
            }
            if {[info exists sth::Session::result_relatedtype($class)] && ($sth::Session::result_relatedtype($class) != "_none_")} {
                array unset related_results
                array set related_results $sth::Session::result_relatedtype($class)
                foreach rtype [array names related_results] {
                    update_subscribed_results $rtype $related_results($rtype) resultDataSetList subscribedList                   
                }
            }
        }   
    }
}

proc ::sth::Session::update_subscribed_results {configType resultType resultDataSetList subscribedList} {
    upvar $resultDataSetList myResultDataSetList
    upvar $subscribedList mySubscribedList
    set valueList ""
    
    set configType [string tolower $configType]
    set resultType [string tolower $resultType]
    # check if already subscribed
    if { [lsearch [keylkeys mySubscribedList] $configType] >= 0 } {
        set valueList [keylget mySubscribedList $configType]
        if {[lsearch $valueList $resultType] >= 0} {
            return
        } 
    } 
    set rDataSet [::sth::sthCore::invoke stc::subscribe -Parent project1 -ResultParent project1 -ConfigType $configType -resulttype $resultType]
    keylset mySubscribedList $configType "$valueList $resultType"
    lappend myResultDataSetList $rDataSet
        
    # some other results will be created automatically when subscribing, need to check and update
    set current_results [stc::get project1 -children-resultdataset]
    if {[llength $current_results] > [llength $myResultDataSetList]} {
        foreach res $current_results {
            if {![regexp -nocase $res $myResultDataSetList]} {
                foreach rquery [stc::get $res -children-resultquery] {
                    set rConfigType [stc::get $rquery -ConfigClassId]
                    set rResultType [stc::get $rquery -ResultClassId]
                    set valueList ""
                    if {[lsearch [keylkeys mySubscribedList] $rConfigType] >= 0} {
                        set valueList [keylget mySubscribedList $rConfigType]
                    } 
                    keylset mySubscribedList $rConfigType "$valueList $rResultType"
                }
                lappend myResultDataSetList $res    
            }
        }
    }
}

#function to support actions on streamblock[currently action run is verified]
proc ::sth::fill_global_variables {  } {
    if {$::sth::Session::fillTraffic eq "all" ||  $::sth::Session::fillTraffic eq "set"} {
        set ports [::sth::sthCore::invoke stc::get project1 -children-port]
        foreach portHnd $ports {
            set streamBlockHandles [::sth::sthCore::invoke stc::get $portHnd -children-streamblock]
            set ::sth::Session::PORTLEVELARPSENDREQUEST($portHnd) 1
            set ::sth::Session::PORTLEVELARPDONE($portHnd) 0
            set loc [::sth::sthCore::invoke stc::get $portHnd -location]
            regsub -all {^//} $loc "" loc
            set ::sth::Session::PORTHNDLIST($portHnd) $loc
            if { $streamBlockHandles != "" } {
                set ::sth::Traffic::arrayPortHnd($portHnd) $streamBlockHandles                                
            }
        }
    }
    
    if {$::sth::Session::fillIsIsDevice eq "all" || $::sth::Session::fillIsIsDevice eq "set"} {
        set deviceHnds [::sth::sthCore::invoke stc::get project1 -children-emulateddevice]
        set ::sth::IsIs::ISISROUTECOUNT 0
        foreach hnd $deviceHnds {
            set isisHnds [::sth::sthCore::invoke stc::get $hnd -children-IsisRouterConfig]
            if { $isisHnds != "" } {
                foreach isis $isisHnds {
                    set ipVersion 4
                    set ver [::sth::sthCore::invoke stc::get $isis -ipVersion]
                    switch -exact -- $ver {
                        IPV4 {
                            set ipVersion 4
                        }
                        IPV6 {
                            set ipVersion 6
                        }
                        IPV4_AND_IPV6 {
                            set ipVersion 4_6
                        }
                    }
                    set lspHnds [::sth::sthCore::invoke stc::get $isis -children-IsisLspConfig]
                    foreach lsp $lspHnds {
                        set ipv4Hnd [::sth::sthCore::invoke stc::get $lsp -children-Ipv4IsisRoutesConfig]
                        set ipv6Hnd [::sth::sthCore::invoke stc::get $lsp -children-Ipv6IsisRoutesConfig]
                        
                        set name "isisRouteHandle$::sth::IsIs::ISISROUTECOUNT"
                        set ::sth::IsIs::ISISROUTEHNDLIST($name) [list $lsp $ipVersion $ipv4Hnd $ipv6Hnd]
                        incr ::sth::IsIs::ISISROUTECOUNT
                    }
                }
            }
        }
    }
    
    set ::sth::Session::fillTraffic all
    set ::sth::Session::fillIsIsDevice all
}

proc ::sth::get_handles { args } {
	variable ::sth::Session::userArgsArray
    array unset ::sth::Session::userArgsArray
    array set ::sth::Session::userArgsArray {}
	variable sortedSwitchPriorityList {}
	upvar returnKeyedList returnKeyedList;
	set returnKeyedList ""
	
	::sth::sthCore::log debug "{Calling sth::get_handles}"
	
	::sth::sthCore::log info "{Executing command: get_handles $args}"     
	if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
				::sth::Session:: \
				get_handles \
				userArgsArray \
				sortedSwitchPriorityList} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
		return $returnKeyedList;
	}
    
    if {[catch {::sth::Session::get_handles_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing get_handles: $err"
    }
	return $returnKeyedList
}

proc ::sth::Session::get_handles_imp {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    keylset myreturnKeyedList status $::sth::sthCore::FAILURE
    variable ::sth::Session::myroot 
	set type $::sth::Session::userArgsArray(type)

	set portcondition ""
	if {[info exists ::sth::Session::userArgsArray(from_ports)]} {
		set portcondition $::sth::Session::userArgsArray(from_ports)
	}
	
	set deviceflag 1
    array set namespace_root_map {}
    foreach index [lsort -dictionary [array names ::sth::Session::device_classname_map_array]] {
        set value $::sth::Session::device_classname_map_array($index)
		set varray [split $value "/"]
        set name [lindex $varray 0]
		if {$type eq $name} {			
			if {[lindex $varray 1] eq "config"} {
				set deviceflag 0
			}
		
			set classname [lindex $varray 2]
            set mynamespace [lindex $varray 4]
            if {[info exists namespace_root_map($mynamespace)]} {
                set ::sth::Session::myroot $namespace_root_map($mynamespace)
            } else {
                catch {set ::sth::Session::myroot [lindex $varray 5]}
            }
            break
		} else {
            set othernamespace [lindex $varray 4]
            set othervalue [lindex $varray 2]
            if {[info exists namespace_root_map($othernamespace)]} {
                set othervalue "$othervalue;$namespace_root_map($othernamespace)"
            }
            set namespace_root_map($othernamespace) $othervalue
        }
	}
	
	if {$classname eq ""} {
        ::sth::sthCore::processError myreturnKeyedList "\[Session\] get_handles FAILED. The handle type requested is Not Supportted";
		return $myreturnKeyedList
	}

    if {[info exists ::sth::Session::userArgsArray(from_devices)]} {
        set namelist $::sth::Session::userArgsArray(from_devices)
        set condition_device [lindex $varray 3]
        set rootlist [::sth::Session::condition_device_port $condition_device $namelist $portcondition]
        if {$rootlist ne ""} {
            set myreturnKeyedList [::sth::Session::getobjects_from $deviceflag $classname "" $rootlist]
        }
    } else {
        if {$portcondition ne ""} {
            set condition_device [lindex $varray 3]
            set rootlist [::sth::Session::condition_device_port $condition_device "" $portcondition]
            if {$rootlist ne "" || $condition_device eq "port"} {
                set myreturnKeyedList [::sth::Session::getobjects_from $deviceflag $classname "" $rootlist]
            }
        } else {
            set rootlist ""
			if {[info exists ::sth::Session::myroot] && $::sth::Session::myroot ne ""} {
                set rarray [lindex [split $::sth::Session::myroot ";"] 0]
                set rarray [split $rarray ","]
            	foreach root $rarray {
					set returnList [::sth::sthCore::invoke stc::perform GetObjects -RootList $::sth::GBLHNDMAP(project) -ClassName $root]
                    set ttarray [split [string map [list " -" \0] $returnList] \0]
                    set obj [keylget ttarray ObjectList]
                    if {$obj ne ""} {
                        lappend rootlist [keylget ttarray ObjectList]
                    }
				}
			}
            set myreturnKeyedList [::sth::Session::getobjects_from $deviceflag $classname $portcondition $rootlist]
        }
    }
    
    if {[catch {keylget myreturnKeyedList handles}]} {
        keylset myreturnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS
    }
	return $myreturnKeyedList
}


proc ::sth::link_config { args } {
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
    
    variable userArgsArray;
	array unset userArgsArray;
	array set userArgsArray {};
	variable sortedSwitchPriorityList {};
	upvar returnKeyedList returnKeyedList;
	set returnKeyedList ""
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	::sth::sthCore::log debug "{Calling sth::get_handles}"
	
	::sth::sthCore::log info "{Executing command: link_config $args}"     
	if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
				::sth::Session:: \
				link_config \
				userArgsArray \
				sortedSwitchPriorityList} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
		return $returnKeyedList;
	}
    
	if {[catch {
		set src  $userArgsArray(link_src)
		set dst1  $userArgsArray(link_dst)
		set dst $dst1
		switch -exact -- $userArgsArray(link_type) {
			"L3_Forwarding_Link" -
			"L2tpv3_Tunnel_Link" -
			"VLAN_Switch_Link" -
			"Ethernet_Bridge_Link" -
			"I-Tag_Service_Link" -
			"VRF_Customer_Link" -
			"OTV_Edge_Device_Link" -
			"DHCPv4_Relay Agent_Link" -
			"DHCPv4_Relay_Agent_Link" -
            "DHCPv6_Relay_Agent_Link" -
			"Home_Gateway_Link" -
			"ANCP_CPE_To_DSLAM_Link" -
			"EOAM_Link" -
			"VIF_To_VIC_Link" -
			"VSI_to_Station_Link" -
			"Station_to_S-Comp_Link" -
			"IPv6_Transition_Link" {
					regsub -all "_"  $userArgsArray(link_type) " " type
			}
			"L2_GRE_Tunnel_Link" {
					regsub -all "_"  $userArgsArray(link_type) " " type
					set dst [::sth::createGreDbd $dst1]
					keylset returnKeyedList gre_handle $dst
			}
			"VXLAN_VM_to_VTEP_Device_Link" -
			"VXLAN_VM_TO_VTEP_LINK" {
					set vxlanvmtovteplink [::sth::sthCore::invoke stc::create VxlanVmToVtepLink -under $src]
					::sth::sthCore::invoke stc::config $src -ContainedLink-targets $vxlanvmtovteplink
					::sth::sthCore::invoke stc::config $vxlanvmtovteplink  -LinkDstDevice-targets $dst
			
					set ethif [::sth::sthCore::invoke stc::get $src -children-EthIIIf]
					set vxlanif [::sth::sthCore::invoke stc::get $src -children-VxlanIf]
					::sth::sthCore::invoke stc::config $vxlanvmtovteplink -LinkSrc-targets $ethif
					::sth::sthCore::invoke stc::config $vxlanvmtovteplink -LinkDst-targets $vxlanif
					return $returnKeyedList
			}

		}
		
		if {[regexp " " $src] || [regexp " " $dst] } {
			::sth::sthCore::processError returnKeyedList "\[Session\] link_config FAILED. cannot process handle list in -link_src or -link_dst" {}
			return $returnKeyedList;
		}
		
		::sth::sthCore::invoke stc::perform LinkCreate -SrcDev $src -DstDev $dst -LinkType $type
	} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "\[Session\] link_config FAILED. $eMsg" {}
	}
	
	return $returnKeyedList
}

proc ::sth::arp_control { args } {
    ::sth::sthCore::Tracker ::sth::arp_control  $args 
    variable ::sth::userArgsArray
    variable ::sth::sortedSwitchPriorityList 
    array unset userArgsArray
    array set userArgsArray {}
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    set returnKeyedList ""
    set porthandlevalue ""
    set handlevalue ""
    set wait ""
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    #keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
        ::sth::Session:: \
        arp_control \
        userArgsArray \
        sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] ARP FAILED. $eMsg" {}
        return $returnKeyedList
    }
    if {[info exists userArgsArray(port_handle)]} {
        set porthandlevalue $userArgsArray(port_handle)
    }
    
    if {[info exists userArgsArray(handle)]} {
        set handlevalue $userArgsArray(handle)
    }

    if {[info exists userArgsArray(wait)]} {
        set wait $userArgsArray(wait)
    }    
    
    set devices {}
    set target  ""
    
    switch -exact -- $userArgsArray(arp_target) {
        device {
            set target $handlevalue
        }
        stream {
            set target $handlevalue
        }
        port {
            set target $porthandlevalue
        }
        all {
            set myports [::sth::sthCore::invoke stc::get project1 -children-port];
            set porthandlevalue [split [string map [list " " \0] $myports] \0]
            foreach port_hnd $porthandlevalue {
            set hosts [::sth::sthCore::invoke stc::get $port_hnd "-AffiliationPort-Sources"]
            set streams [::sth::sthCore::invoke stc::get $port_hnd "-children-StreamBlock"]
            append target "$hosts $streams "
            }
        }
        allstream -
        alldevice {
        set myports [::sth::sthCore::invoke stc::get project1 -children-port];
        set porthandlevalue [split [string map [list " " \0] $myports] \0]
        set target $porthandlevalue
        }
    }

    
    if  {$target != "" && $userArgsArray(arp_target) != "allstream" && $userArgsArray(arp_target) != "alldevice"} {
        set arpResults [::sth::sthCore::invoke ::stc::perform ArpNdStart -HandleList "$target" -WaitForArpToFinish $wait]
    } elseif {$target != "" && $userArgsArray(arp_target) == "alldevice"} {
        set arpResults [::sth::sthCore::invoke ::stc::perform ArpNdStartOnAllDevices -PortList "$target" -WaitForArpToFinish $wait]
    } elseif {$target != "" && $userArgsArray(arp_target) == "allstream"} {
        set arpResults [::sth::sthCore::invoke ::stc::perform ArpNdStartOnAllStreamBlocks -PortList "$target" -WaitForArpToFinish $wait]
    }

    if {[info exists userArgsArray(arp_cache_retrieve)] && $userArgsArray(arp_cache_retrieve)} {
        if {[catch {::sth::sthCore::invoke ::stc::perform ArpNdUpdateArpCache -HandleList "$target"} err]} {}
        foreach port_hnd $porthandlevalue { 
            set i 0
            set arpCacheData [::sth::sthCore::invoke stc::get [stc::get $port_hnd -children-arpcache] -ArpCacheData]
            foreach arpndattr $arpCacheData {
                if {[regexp -nocase "port_address" $arpndattr]} {
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.location [lindex $arpndattr 2]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.ip [lindex $arpndattr 3]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.gateway_ip [lindex $arpndattr 4]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.resolved_mac [lindex $arpndattr 5]
                } elseif {[regexp -nocase "streamblock.*" $arpndattr]} {
                    set ret [lindex $arpndattr 2]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.location $ret
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.ip [lindex $arpndattr 4]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.gateway_ip [lindex $arpndattr 5]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.resolved_mac [lindex $arpndattr 6]
                } else {
                    set ret [join [lrange $arpndattr 2 3] ""]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.location $ret
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.ip [lindex $arpndattr 4]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.gateway_ip [lindex $arpndattr 5]
                    keylset returnKeyedList $port_hnd.arpnd_cache$i.resolved_mac [lindex $arpndattr 6]
                    }
                incr i
            }
        }
    }
                    
    if {[info exists userArgsArray(arpnd_report_retrieve)] && $userArgsArray(arpnd_report_retrieve)} {
        foreach port_hnd $porthandlevalue {
            set arpReport ""
            set arpndReportHandle [::sth::sthCore::invoke stc::get $port_hnd -Children-ArpNdReport]
            set arpndReportAttr "ArpNdStatus FailedArpNdCount SuccessfulArpNdCount AttemptedArpNdCount"
            set arpndReportAttrName "arpnd_status failed_arpnd_count successful_arpnd_count attempted_arpnd_count"
            array set arpReportArray [::sth::sthCore::invoke stc::get $arpndReportHandle]
            foreach attr $arpndReportAttr attrName $arpndReportAttrName {
                set arpStatus $arpReportArray(-$attr)
                set arpReport [::sth::sthCore::updateReturnInfo $arpReport "$attrName" $arpStatus]
            }
            keylset returnKeyedList arpnd_report.$port_hnd $arpReport
        }
    }        
    
    if {[regexp -nocase "ArpNdState FAILURE" $arpResults]} {
        keylset returnKeyedList arpnd_status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList arpnd_status $::sth::sthCore::SUCCESS
    }
    
    return $returnKeyedList
}

proc ::sth::sequencer_control {{action start} args} {
    ::sth::sthCore::Tracker ::sth::sequencer_control  $action $args 
    
	set returnKeyedList ""
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	
    if {$args != ""} {
        set action $args
    }
    
	if {[catch {::sth::Session::sequencer_control_imp $action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing sequencer protocol : $err"
    }
	
	return $returnKeyedList
}

proc ::sth::Session::sequencer_control_imp {action returnKeyedList} {
	upvar $returnKeyedList myreturnKeyedList
	
	set sqrHandle [stc::get system1 -children-sequencer]
	if {[regexp -nocase $action "start"]} {
		::sth::Session::start_sequencer $sqrHandle
	} elseif {[regexp -nocase $action "stop step pause"]} {
		::sth::sthCore::invoke stc::perform sequencer$action
		::sth::sthCore::invoke stc::waituntilcomplete
	} else {
	     ::sth::sthCore::processError myreturnKeyedList "HLTAPI does not support this action in command sequencer: $action"
		return $myreturnKeyedList
	}
	
	set sqrStatus [::sth::sthCore::invoke stc::get $sqrHandle -Status]
	set sqrTestState [::sth::sthCore::invoke stc::get $sqrHandle -TestState]
	if { $sqrStatus eq "" }  {
		keylset myreturnKeyedList seq_status $sqrTestState
	} else {
		keylset myreturnKeyedList seq_status $sqrStatus
	}
	
	return $myreturnKeyedList
}


#####################################
#arp_nd_config
#####################################
proc ::sth::arp_nd_config { args } {
    ::sth::sthCore::Tracker ::sth::arp_nd_config  $args 
    variable ::sth::Session::arpNduserArgsArray
    variable ::sth::sortedSwitchPriorityList 
    array unset ::sth::Session::arpNduserArgsArray
    array set ::sth::Session::arpNduserArgsArray {}
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    set returnKeyedList ""
  
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
        ::sth::Session:: \
        arp_nd_config \
        ::sth::Session::arpNduserArgsArray \
        sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] ARP FAILED. $eMsg" {}
        return $returnKeyedList
    }
    
    if {[set ArpNdConfigVar [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ArpNdConfig]] != ""} {  
        set optionValueList [::sth::Session::getStcOptionValueList arp_nd_config configArpNd "modify" $ArpNdConfigVar 0]
        if {[llength $optionValueList]} {
            ::sth::sthCore::invoke stc::config $ArpNdConfigVar $optionValueList
        }
    }

    return $returnKeyedList
}


proc ::sth::Session::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in sessionTable.tcl
    foreach item $::sth::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Session:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Session:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Session:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Session:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Session:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Session:: $cmdType $opt $::sth::Session::arpNduserArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::Session::arpNduserArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Session::arpNduserArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}

proc ::sth::save_xml { args } {
    ::sth::sthCore::Tracker ::sth::save_xml  $args 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set connectKeyedList ""
    keylset connectKeyedList status $::sth::sthCore::SUCCESS
    set cmdName "::sth::Session::savexml_imp $args"
    if {[catch {eval $cmdName} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError connectKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError connectKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $connectKeyedList] == 0} {
            ::sth::sthCore::processError connectKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $connectKeyedList
}

proc ::sth::Session::savexml_imp { args } {
     upvar connectKeyedList connectKeyedList;
     variable userArgsArray;
     array unset userArgsArray;
     array set userArgsArray {};
     variable sortedSwitchPriorityList {};
     variable ::sth::sthCore::SUCCESS;
     variable ::sth::sthCore::FAILURE;
     
     ::sth::sthCore::log debug "{Calling sth::savexml}"
     
     ::sth::sthCore::log info "{Executing command: savexml $args}"     
     if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  save_xml \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
        return $connectKeyedList;
     }
    if {$::sth::sthCore::custom_path ne ""} {
        set xml_abspath $::sth::sthCore::custom_path
    } else {
        set xml_abspath "[file rootname [file normalize [info script]]].xml"
      }
    if {![info exists userArgsArray(filename)]} {
        set userArgsArray(filename) $xml_abspath        
    } elseif { ! [regexp -nocase -- {^[a-z]:|^/} $userArgsArray(filename)] } {
        # relative pathname or filename
         if {$::sth::sthCore::custom_path ne ""} {
              set userArgsArray(filename) "$xml_abspath/$userArgsArray(filename)"
         } else {
             set userArgsArray(filename) "[file dirname $xml_abspath]/$userArgsArray(filename)"
           }
    
        
    }
    ::sth::sthCore::log info "{Saving the configuration to $userArgsArray(filename)}"      
     if {[catch {::sth::sthCore::invoke stc::perform SaveAsXml -FileName $userArgsArray(filename)} errMsg ]} {
        ::sth::sthCore::processError connectKeyedList "stc::perform SaveAsXml Failed: $errMsg"
     } else {
        set ::sth::Session::xmlFlag 1
	keylset connectKeyedList status $::sth::sthCore::SUCCESS
     }
     
    #function to support actions on streamblock[currently action run is supported]
     ::sth::fill_global_variables
     return $connectKeyedList     
}

proc ::sth::system_settings { args } {
    ::sth::sthCore::Tracker ::sth::system_settings  $args 
    
    set connectKeyedList ""
    keylset connectKeyedList status $::sth::sthCore::SUCCESS
    set cmdName "::sth::Session::system_settings_imp $args"
    if {[catch {eval $cmdName} errMsg]} {
        if {[string length $errMsg] == 0} {
                ::sth::sthCore::processError connectKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError connectKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $connectKeyedList] == 0} {
            ::sth::sthCore::processError connectKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $connectKeyedList
}
proc ::sth::Session::system_settings_imp { args } {
     upvar connectKeyedList connectKeyedList
     variable userArgsArray
     array unset userArgsArray
     array set userArgsArray {}
     variable sortedSwitchPriorityList {}
     
     ::sth::sthCore::log debug "{Calling sth::system_settings}"
     
     ::sth::sthCore::log info "{Executing command: system_settings $args}"
     
     if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  system_settings \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError connectKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
        return $connectKeyedList;
     }
    if {[info exists userArgsArray(realism_mode)]} {
        set port_list [::sth::sthCore::invoke stc::get project1 -children-port]
        if { [llength $port_list] > 0 } {
            ::sth::sthCore::invoke stc::perform detachports -portlist $port_list
        }
        # get RealismOptions
        set realismOptionsHandle [::sth::sthCore::invoke stc::get project1 -children-RealismOptions]
        # config global RealismOptions, need to take ports offline and online to take effect.
        ::sth::sthCore::invoke stc::config $realismOptionsHandle -RealismMode $userArgsArray(realism_mode)
        ::sth::sthCore::invoke stc::sleep 2
        if { [llength $port_list] > 0 } {
            ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
        }
    }
    if {[info exists userArgsArray(tshark_path)]} {
        # get TrafficOptions
        set trafficOptionsHandle [::sth::sthCore::invoke stc::get project1 -children-TrafficOptions]
        ::sth::sthCore::invoke stc::config $trafficOptionsHandle -TSharkPath $userArgsArray(tshark_path)
    }
}

proc ::sth::reserve_ports {args} {
    ::sth::sthCore::Tracker ::sth::reserve_ports  $args

    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    set cmdName "::sth::Session::reserveports_imp $args"
    if {[catch {eval $cmdName} errMsg]} {
        if {[string length $errMsg] == 0} {
            ::sth::sthCore::processError returnKeyedList "exception with empty error message is raised"
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}


proc ::sth::Session::reserveports_imp {args} {
    upvar returnKeyedList returnKeyedList
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    variable sortedSwitchPriorityList {}
     
    ::sth::sthCore::log debug "{Calling sth::reserveports}"
     
    ::sth::sthCore::log info "{Executing command: reserveports $args}"     
    if {[catch {::sth::sthCore::commandInit ::sth::Session::sessionTable $args \
                                  ::sth::Session:: \
                                  reserve_ports \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "\[Session\] commandInit FAILED. $eMsg" {}
        return $returnKeyedList
    }
       
    if {[catch {::sth::sthCore::invoke stc::perform CreateAndReservePorts \
                -revokeowner TRUE -ChassisList $userArgsArray(chassis_list) -SlotList $userArgsArray(slot_list) \
                -LocationList $userArgsArray(location_list)} ret ]} {
        ::sth::sthCore::processError returnKeyedList "stc::perform CreateAndReservePorts Failed: $ret"
    } else {
        if {[regexp {\-PortList (.*?) \-} $ret mymatch myporthnds]} {
            set i 0
            set portlist [split [string map [list "\{" "" "\}" ""] $myporthnds] " "]
            foreach porthnd $portlist {
                set location [::sth::sthCore::invoke stc::get $porthnd -location]
                if {[regexp {//(.*?)/(.*)$} $location mymatch chassisip csp]} {
                    if {![info exists ::sth::Session::CHASSISID2DEVICEMAP($chassisip)]} {
                        set ::sth::Session::CHASSISID2DEVICEMAP($chassisip) $chassisip
                    }
                }
                
                set ::sth::Session::PORTHNDLIST($porthnd) $location
                set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
				set ::sth::Session::PORTLEVELARPDONE($porthnd) false 
                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "port_handle.$chassisip\.$csp" "$porthnd"]
                incr i
            }
            keylset returnKeyedList offline 0
        }
        ::sth::Session::SetFECTrue100Gig
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
     
    return $returnKeyedList
}

# Get host attributes to fill an array, intended to be used for modify mode which lacks some information
# if create mode is not called before.
# Examples:
# array set hostAttrs "
#        _outervlan          ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)
#        _innervlan          ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)
#        _hostnum            ::sth::Dhcp::DHCPHOSTNUMSESS($hostHandle)
#    "
#    ::sth::Session::getHostAttrToArray $hostHandle hostAttrs
# Arguments:
# handle:       host handle
# attrArray:    an array mapping the attributes and the data structures you want to fill, use the following keys:
#   _outervlan    outer vlan handle
#   _innervlan    inner vlan handle
#   _hostnum      number of hosts 
proc ::sth::Session::getHostAttrToArray { handle attrArray } {
    set host_handle $handle
    upvar $attrArray my_attrArray 
    
    set attrArray_keys [array names my_attrArray]
    
    # vlan
    if {[lsearch -regexp $attrArray_keys ^_outervlan|^_innervlan] > -1} {
        set ethiiif [::sth::sthCore::invoke stc::get $host_handle -children-ethiiif]
        if {$ethiiif != ""} {
            set outervlan [::sth::sthCore::invoke stc::get $ethiiif -stackedonendpoint-Sources]
            if {[regexp "^vlanif" $outervlan]} {
                if {[info exist my_attrArray(_outervlan)]} {
                    set $my_attrArray(_outervlan) $outervlan
                }
                
                set innervlan [::sth::sthCore::invoke stc::get $outervlan -stackedonendpoint-Sources]
                if {[regexp "^vlanif" $innervlan]} {
                    set $my_attrArray(_innervlan) $innervlan
                }
            }
        }
    }
    # number of hosts/sessions
    if {[lsearch -exact $attrArray_keys _hostnum] > -1} {
        set $my_attrArray(_hostnum) [::sth::sthCore::invoke stc::get $host_handle -DeviceCount]
    }
    
}

