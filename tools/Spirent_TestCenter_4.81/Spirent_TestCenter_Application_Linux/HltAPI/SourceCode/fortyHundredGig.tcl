proc ::sth::pcs_error_config {args} {
    ::sth::sthCore::Tracker ::sth::pcs_error_config $args
 
    set returnKeyedList ""
    
    set cmdName "::sth::hunderdGig::pcs_error_config_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error message is raised."
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}

proc ::sth::hunderdGig::pcs_error_config_imp {args} {
    ::sth::sthCore::Tracker ::sth::hunderdGig::pcs_error_config_imp $args
    set hunderdGigKeyedList ""
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    variable sortedSwitchPriorityList {}
    if {[catch {::sth::sthCore::commandInit ::sth::hunderdGig::hunderdGigTable $args \
                                     ::sth::hunderdGig:: \
                                     pcs_error_config \
                                     userArgsArray \
                                     sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError hunderdGigKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $hunderdGigKeyedList
    }

    set pcs_error_insertion_handle [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-PcsErrorInsertionConfig]
    if {$pcs_error_insertion_handle == ""} {
        set pcs_error_insertion_handle  [::sth::sthCore::invoke stc::create PcsErrorInsertionConfig -under $userArgsArray(port_handle)]
    } 
    config_pcs_error_insertion $pcs_error_insertion_handle
    keylset hunderdGigKeyedList handle $pcs_error_insertion_handle
    return $hunderdGigKeyedList
}


proc ::sth::random_error_config {args} {
    ::sth::sthCore::Tracker ::sth::random_error_config $args
 
    set returnKeyedList ""
    
    set cmdName "::sth::hunderdGig::random_error_config_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with empty error message is raised."
            ::sth::sthCore::log debug $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    keylset returnKeyedList status 1
    return $returnKeyedList

}

proc ::sth::hunderdGig::random_error_config_imp {args} {
    ::sth::sthCore::Tracker ::sth::hunderdGig::random_error_config_imp $args
    set hunderdGigKeyedList ""
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    variable sortedSwitchPriorityList {}
    if {[catch {::sth::sthCore::commandInit ::sth::hunderdGig::hunderdGigTable $args \
                                     ::sth::hunderdGig:: \
                                     random_error_config \
                                     userArgsArray \
                                     sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError hunderdGigKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $hunderdGigKeyedList
    }
    
    set random_error_insertion_handle [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-RandomErrorInsertionConfig]
    if {$random_error_insertion_handle == ""} {
        set random_error_insertion_handle  [::sth::sthCore::invoke stc::create RandomErrorInsertionConfig  -under $userArgsArray(port_handle)]
    } 
    config_random_error_insertion $random_error_insertion_handle
    keylset hunderdGigKeyedList handle $random_error_insertion_handle
    return $hunderdGigKeyedList
}


proc ::sth::pcs_error_control {args} {
    ::sth::sthCore::Tracker ::sth::pcs_error_control $args
 
    set returnKeyedList ""
    
    if {[catch {
        set action [lindex $args [expr [lsearch $args "-action"] + 1]]
        set port_list [lindex $args [expr [lsearch $args "-port_handle"] + 1]]
        if {[regexp "start" $action]} {
            ::sth::sthCore::invoke stc::perform PcsErrorInsertionStartCommand -HandleList $port_list
        } else {
            ::sth::sthCore::invoke stc::perform PcsErrorInsertionStopCommand -HandleList $port_list
        }
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "error in pcs_error_control -->$errMsg";
        return $returnKeyedList
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}

proc ::sth::random_error_control {args} {
    ::sth::sthCore::Tracker ::sth::random_error_control $args
 
    set returnKeyedList ""
    
    if {[catch {
        set action [lindex $args [expr [lsearch $args "-action"] + 1]]
        set port_list [lindex $args [expr [lsearch $args "-port_handle"] + 1]]
        if {[regexp "start" $action]} {
            ::sth::sthCore::invoke stc::perform RandomErrorInsertionStartCommand  -HandleList $port_list
        } else {
            ::sth::sthCore::invoke stc::perform RandomErrorInsertionStopCommand  -HandleList $port_list
        }
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "error in random_error_control -->$errMsg";
        return $returnKeyedList
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}

proc ::sth::forty_hundred_gig_l1_results {args} {
    ::sth::sthCore::Tracker ::sth::forty_hundred_gig_l1_results $args
    set returnKeyedList ""
    variable ::sth::hunderdGig::userArgsArray
    array unset ::sth::hunderdGig::userArgsArray
    array set ::sth::hunderdGig::userArgsArray {}
    variable ::sth::hunderdGig::sortedSwitchPriorityList {}
    if {[catch {::sth::sthCore::commandInit ::sth::hunderdGig::hunderdGigTable $args \
                                     ::sth::hunderdGig:: \
                                     forty_hundred_gig_l1_results \
                                     ::sth::hunderdGig::userArgsArray \
                                     ::sth::hunderdGig::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError hunderdGigKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $hunderdGigKeyedList
    }
    
    if {[catch {
        if {[info exists userArgsArray(port_handle)]} {
            set object_list $userArgsArray(port_handle)
        } else {
            set object_list [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port]
        }
        set returnKeyedList [sth::hunderdGig::forty_hundred_gig_l1_results_$userArgsArray(type) $object_list]
        
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "error in forty_hundred_gig_l1_results -->$errMsg";
        return $returnKeyedList
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
    
}
