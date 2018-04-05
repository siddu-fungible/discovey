# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth {

}

proc ::sth::emulation_pim_config {args} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    array unset userArgsArray
    array set userArgsArray {}
    set returnKeyedList ""
    ::sth::sthCore::Tracker "::sth::emulation_pim_config" $args
    if {[catch {::sth::sthCore::commandInit \
            ::sth::pimTable \
            $args \
            ::sth:: \
            emulation_pim_config \
            userArgsArray \
            sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
        return $returnKeyedList
    }

    set mode $userArgsArray(mode)
    set retVal [catch {
        switch -exact $mode {
            create -
            enable -
            enable_all {
                if {[info exists userArgsArray(ip_version)] && [info exists userArgsArray(type)]} {
                    emulation_pim_config_create returnKeyedList
                } else {
                    ::sth::sthCore::processError returnKeyedList " Missing mandatory arguments: ip_version   type" {}
                    return $returnKeyedList
                }
            }
            modify {
                emulation_pim_config_modify returnKeyedList
            }
            delete -
            disable -
            disable_all {
                emulation_pim_config_delete returnKeyedList
            }
            active {
                emulation_pim_config_active returnKeyedList
            }
            inactive {
                emulation_pim_config_inactive returnKeyedList
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error:  Unsupported -mode value $mode" {}
                return -code error $returnKeyedList
            }
        }
    } returnedString]
    
    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    
    return -code $retVal $returnedString
}


proc ::sth::emulation_pim_control {args} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    array unset userArgsArray
    array set userArgsArray {}
    set returnKeyedList ""
    ::sth::sthCore::Tracker "::sth::emulation_pim_control" $args
    ::sth::sthCore::commandInit \
            ::sth::pimTable \
            $args \
            ::sth:: \
            emulation_pim_control \
            userArgsArray \
            sortedSwitchPriorityList

    set mode $userArgsArray(mode)
    set retVal [catch {
        switch -exact $mode {
            stop {
                emulation_pim_control_stop returnKeyedList
            }
            start {
                emulation_pim_control_start returnKeyedList
            }
            restart {
                emulation_pim_control_restart returnKeyedList
            }
            join {
                emulation_pim_control_join returnKeyedList
            }
            prune {
                emulation_pim_control_prune returnKeyedList
            }
            default {
               ::sth::sthCore::processError returnKeyedList \
                     "Error:  Unsupported -mode value $mode" {}
               return -code error $returnKeyedList
            }
        }
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    
    return -code $retVal $returnedString
}

proc ::sth::emulation_pim_group_config {args} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    array unset userArgsArray
    array set userArgsArray {}
    set returnKeyedList ""
    ::sth::sthCore::Tracker "::sth::emulation_pim_group_config" $args
    ::sth::sthCore::commandInit \
            ::sth::pimTable \
            $args \
            ::sth:: \
            emulation_pim_group_config \
            userArgsArray \
            sortedSwitchPriorityList

#parray userArgsArray
    set mode $userArgsArray(mode)
    set retVal [catch {
        switch -exact $mode {
            create {
                emulation_pim_group_config_create returnKeyedList
            }
            modify {
                emulation_pim_group_config_modify returnKeyedList
            }
            delete {
                emulation_pim_group_config_delete returnKeyedList
            }
            default {
               ::sth::sthCore::processError returnKeyedList \
                     "Error:  Unsupported -mode value $mode" {}
               return -code error $returnKeyedList
            }

        }
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    
    return -code $retVal $returnedString
}

proc ::sth::emulation_pim_info {args} {
    variable userArgsArray
    variable version
    variable startTimeArray
    variable stopTimeArray
    variable sortedSwitchPriorityList
    array unset userArgsArray
    array set userArgsArray {}
    set returnKeyedList ""
    ::sth::sthCore::Tracker "::sth::emulation_pim_info" $args
    ::sth::sthCore::commandInit \
            ::sth::pimTable \
            $args \
            ::sth:: \
            emulation_pim_info \
            userArgsArray \
            sortedSwitchPriorityList

    set pimPortList ""
    set retVal [catch {
        if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to access PIM " \
                  "statistics.  Missing mandatory argument \"-handle\".  "]
        }
        set pimRtrHandle $userArgsArray(handle)

        array unset stats
        set stats(hello_tx) 0
        set stats(hello_rx) 0
        set stats(group_join_tx) 0
        set stats(group_join_rx) 0
        set stats(s_g_join_tx) 0
        set stats(s_g_join_rx) 0
#        set stats(group_assert_tx) 0
        set stats(group_assert_rx) 0
#        set stats(reg_tx) 0
        set stats(reg_rx) 0
#        set stats(reg_stop_tx) 0
        set stats(reg_stop_rx) 0
        set stats(j_p_pdu_tx) 0
        set stats(j_p_pdu_rx) 0
#        set stats(crp_tx) 0
        set stats(crp_rx) 0
        set stats(bsm_tx) 0
        set stats(bsm_rx) 0
        array unset routerStats
        array set routerStats [::sth::sthCore::invoke stc::get $pimRtrHandle]
        set router_id "$routerStats(-RouterId)"

        foreach pimRtrConfig [::sth::sthCore::invoke stc::get $pimRtrHandle -children-pimrouterconfig] {
            array set pimRtrStats [::sth::sthCore::invoke stc::get $pimRtrConfig]
            lappend router_state "$pimRtrStats(-RouterState)"
            lappend upstream_neighbor_addr "$pimRtrStats(-UpstreamNeighborV[string trim $version])"

            foreach pimRouterResult [::sth::sthCore::invoke stc::get $pimRtrConfig -children-pimrouterresults] {
                foreach stat [array names stats] {
                    set attr [::sth::sthCore::getswitchprop ::sth:: emulation_pim_info $stat stcattr]
                    set stats($stat) [::sth::sthCore::invoke stc::get $pimRouterResult "-$attr"]
                }
            }
        }
        #these stats do not have stc attributes map to them
        if {[info exists stopTimeArray(-EndTime)] == 0} {
            #if stop command is not called, use current time. 
            set stats(duration) [expr [clock seconds] - $startTimeArray($pimRtrHandle)]
        } else {
            if {[info exists startTimeArray(-EndTime)] == 0} {
                set stats(duration) 0
            } else {
                #if stop command is not call at all.
                set stats(duration) [expr $stopTimeArray($pimRtrHandle) - $startTimeArray($pimRtrHandle)]
            }
        }
        set stats(handle) $pimRtrHandle
		
	    # Insert the statistics into the keyed list
		keylset returnKeyedList router_id $router_id
		keylset returnKeyedList router_state $router_state
		keylset returnKeyedList upstream_neighbor_addr $upstream_neighbor_addr
		foreach stat [array names stats] {
			keylset returnKeyedList $stat $stats($stat)
		}
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    return $returnKeyedList
}

