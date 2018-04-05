namespace eval ::sth:: {

}

proc ::sth::emulation_iptv_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_iptv_config" $args

    variable ::sth::iptv::userArgsArray
    variable ::sth::iptv::sortedSwitchPriorityList
    array unset ::sth::iptv::userArgsArray
    array set ::sth::iptv::userArgsArray {}

    set _hltCmdName "emulation_iptv_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::iptv::iptvTable $args \
                                                            ::sth::iptv:: \
                                                            emulation_iptv_config \
                                                            ::sth::iptv::userArgsArray \
                                                            ::sth::iptv::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::iptv::userArgsArray(mode)
    if {[catch {::sth::iptv::emulation_iptv_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing iptv device : $err"
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}



proc ::sth::emulation_iptv_channel_viewing_profile_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_iptv_channel_viewing_profile_config" $args

    variable ::sth::iptv::userArgsArray
    variable ::sth::iptv::sortedSwitchPriorityList
    array unset ::sth::iptv::userArgsArray
    array set ::sth::iptv::userArgsArray {}

    set _hltCmdName "emulation_iptv_channel_viewing_profile_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::iptv::iptvTable $args \
                                                            ::sth::iptv:: \
                                                            emulation_iptv_channel_viewing_profile_config \
                                                            ::sth::iptv::userArgsArray \
                                                            ::sth::iptv::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::iptv::userArgsArray(mode)
    if {[catch {::sth::iptv::emulation_iptv_channel_viewing_profile_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing iptv channel viewing profile config : $err"
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}


proc ::sth::emulation_iptv_viewing_behavior_profile_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_iptv_viewing_behavior_profile_config" $args

    variable ::sth::iptv::userArgsArray
    variable ::sth::iptv::sortedSwitchPriorityList
    array unset ::sth::iptv::userArgsArray
    array set ::sth::iptv::userArgsArray {}

    set _hltCmdName "emulation_iptv_viewing_behavior_profile_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::iptv::iptvTable $args \
                                                            ::sth::iptv:: \
                                                            emulation_iptv_viewing_behavior_profile_config \
                                                            ::sth::iptv::userArgsArray \
                                                            ::sth::iptv::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::iptv::userArgsArray(mode)
    if {[catch {::sth::iptv::emulation_iptv_viewing_behavior_profile_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing iptv viewing behavior profile config : $err"
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}


proc ::sth::emulation_iptv_channel_block_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_iptv_channel_block_config" $args

    variable ::sth::iptv::userArgsArray
    variable ::sth::iptv::sortedSwitchPriorityList
    array unset ::sth::iptv::userArgsArray
    array set ::sth::iptv::userArgsArray {}

    set _hltCmdName "emulation_iptv_channel_block_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::iptv::iptvTable $args \
                                                            ::sth::iptv:: \
                                                            emulation_iptv_channel_block_config \
                                                            ::sth::iptv::userArgsArray \
                                                            ::sth::iptv::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::iptv::userArgsArray(mode)
    if {[regexp "create" $mode]} {
        #multicast_group_handle is mandatory for the mode create
        if {![info exists ::sth::iptv::userArgsArray(multicast_group_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: multicast_group_handle is mandatory when the mode is create" {}
            return -code error $returnKeyedList
        }
    }
    if {[catch {::sth::iptv::emulation_iptv_channel_block_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing iptv channel block config : $err"
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}



proc ::sth::emulation_iptv_control { args } {

    ::sth::sthCore::Tracker "::sth::emulation_iptv_control" $args

    variable ::sth::iptv::userArgsArray
    variable ::sth::iptv::sortedSwitchPriorityList
    array unset ::sth::iptv::userArgsArray
    array set ::sth::iptv::userArgsArray {}

    set _hltCmdName "emulation_iptv_control"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::iptv::iptvTable $args \
                                                            ::sth::iptv:: \
                                                            emulation_iptv_control \
                                                            ::sth::iptv::userArgsArray \
                                                            ::sth::iptv::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::iptv::userArgsArray(mode)
    if {[catch {::sth::iptv::emulation_iptv_control_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing iptv block : $err"
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}


proc ::sth::emulation_iptv_stats { args } {

    ::sth::sthCore::Tracker "::sth::emulation_iptv_stats" $args

    variable ::sth::iptv::userArgsArray
    variable ::sth::iptv::sortedSwitchPriorityList
    array unset ::sth::iptv::userArgsArray
    array set ::sth::iptv::userArgsArray {}

    set _hltCmdName "emulation_iptv_stats"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::iptv::iptvTable $args \
                                                            ::sth::iptv:: \
                                                            emulation_iptv_stats \
                                                            ::sth::iptv::userArgsArray \
                                                            ::sth::iptv::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    if {[catch {::sth::iptv::emulation_iptv_stats returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get $type result : $err"
        return $returnKeyedList
    }
    return $returnKeyedList
}
