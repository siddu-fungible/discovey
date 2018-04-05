namespace eval ::sth:: {

}


proc ::sth::emulation_video_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_video_config" $args

    variable ::sth::video::userArgsArray
    variable ::sth::video::sortedSwitchPriorityList
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}

    set _hltCmdName "emulation_video_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::video::videoTable $args \
                                                            ::sth::video:: \
                                                            emulation_video_config \
                                                            ::sth::video::userArgsArray \
                                                            ::sth::video::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::video::userArgsArray(mode)
    if {[catch {::sth::video::emulation_video_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing video : $err"
        return $returnKeyedList
    }
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: the handle is mandatory" {}
        return -code error $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_video_server_streams_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_video_server_streams_config" $args

    variable ::sth::video::userArgsArray
    variable ::sth::video::sortedSwitchPriorityList
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}

    set _hltCmdName "emulation_video_server_streams_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::video::videoTable $args \
                                                            ::sth::video:: \
                                                            emulation_video_server_streams_config \
                                                            ::sth::video::userArgsArray \
                                                            ::sth::video::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::video::userArgsArray(mode)
    if {[catch {::sth::video::emulation_video_server_streams_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing server streams : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::emulation_profile_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_profile_config" $args

    variable ::sth::video::userArgsArray
    variable ::sth::video::sortedSwitchPriorityList
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}

    set _hltCmdName "emulation_profile_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::video::videoTable $args \
                                                            ::sth::video:: \
                                                            emulation_profile_config \
                                                            ::sth::video::userArgsArray \
                                                            ::sth::video::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::video::userArgsArray(mode)
    if {[catch {::sth::video::emulation_profile_config returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing server streams : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::emulation_client_load_phase_config {args} {
    ::sth::sthCore::Tracker ::emulation_client_load_phase_config $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_client_load_phase_config $args"

    variable returnKeyedList ""
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}
    variable ::sth::video::sortedSwitchPriorityList
    set _hltCmdName emulation_client_load_phase_config

    if {[catch {
        ::sth::sthCore::commandInit ::sth::video::videoTable $args ::sth::video:: $_hltCmdName ::sth::video::userArgsArray  sortedSwitchPriorityList
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_client_load_phase_config Failed: Command init error: $errMsg" {}
        return $returnKeyedList
    }

    set cmd "sth::video::emulation_client_load_phase_config_$::sth::video::userArgsArray(mode) returnKeyedList "
    if {[catch {
        set tempResult [eval $cmd]
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $errMsg" {}
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
proc ::sth::emulation_video_clips_manage { args } {

    ::sth::sthCore::Tracker "::sth::emulation_video_clips_manage" $args

    variable ::sth::video::userArgsArray
    variable ::sth::video::sortedSwitchPriorityList
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}

    set _hltCmdName "emulation_video_clips_manage"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::video::videoTable $args \
                                                            ::sth::video:: \
                                                            emulation_video_clips_manage \
                                                            ::sth::video::userArgsArray \
                                                            ::sth::video::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {
        set mode $::sth::video::userArgsArray(mode)
        if {$mode == "upload"} {
            foreach filename $::sth::video::userArgsArray(file_name) {
                ::sth::sthCore::invoke stc::perform VideoClipDownloadCommand -FileName $filename -ServerRefList $::sth::video::userArgsArray(server_list)
            }
        } else {
            foreach filename $::sth::video::userArgsArray(file_name) {
                ::sth::sthCore::invoke stc::perform VideoClipDeleteCommand -FileName $filename -ServerRefList $::sth::video::userArgsArray(server_list)
            }
        }
    } err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_video_clips_manage : $err"
        return $returnKeyedList
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_video_control { args } {

    ::sth::sthCore::Tracker "::sth::emulation_video_control" $args

    variable ::sth::video::userArgsArray
    variable ::sth::video::sortedSwitchPriorityList
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}

    set _hltCmdName "emulation_video_control"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::video::videoTable $args \
                                                            ::sth::video:: \
                                                            emulation_video_control \
                                                            ::sth::video::userArgsArray \
                                                            ::sth::video::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {
        set videoSession ""
        if {[info exists userArgsArray(port_handle)]} {
            set portHndList $userArgsArray(port_handle)
            foreach port $portHndList {
                set deviceList [::sth::sthCore::invoke stc::get $port -AffiliatedPortSource]
                foreach device $deviceList {
                    set videoServerSession [::sth::sthCore::invoke stc::get $device -children-VideoServerProtocolConfig]
                    if {$videoServerSession != ""} {
                        lappend videoSession $videoServerSession
                    }
                    set videoClientSession [::sth::sthCore::invoke stc::get $device -children-VideoClientProtocolConfig]
                    if {$videoClientSession != ""} {
                        lappend videoSession $videoClientSession
                    }
                }
            }
        } elseif {[info exists userArgsArray(handle)]} {
            set deviceList $userArgsArray(handle)
            foreach device $deviceList {
                set videoServerSession [::sth::sthCore::invoke stc::get $device -children-VideoServerProtocolConfig]
                if {$videoServerSession != ""} {
                    lappend videoSession $videoServerSession
                }
                set videoClientSession [::sth::sthCore::invoke stc::get $device -children-VideoClientProtocolConfig]
                if {$videoClientSession != ""} {
                    lappend videoSession $videoClientSession
                }
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: either handle or port_handle should be input" {}
            return -code error $returnKeyedList
        }

        set mode $::sth::video::userArgsArray(mode)
        if {$mode == "start"} {
            ::sth::sthCore::invoke stc::perform ProtocolStartCommand -ProtocolList $videoSession
        } else {
            ::sth::sthCore::invoke stc::perform ProtocolStopCommand -ProtocolList $videoSession
        }
    } err]} {
        ::sth::sthCore::processError returnKeyedList "Error in emulation_video_control : $err"
        return $returnKeyedList
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_video_stats { args } {

    ::sth::sthCore::Tracker "::sth::emulation_video_stats" $args

    variable ::sth::video::userArgsArray
    variable ::sth::video::sortedSwitchPriorityList
    array unset ::sth::video::userArgsArray
    array set ::sth::video::userArgsArray {}

    set _hltCmdName "emulation_video_stats"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::video::videoTable $args \
                                                            ::sth::video:: \
                                                            emulation_video_stats \
                                                            ::sth::video::userArgsArray \
                                                            ::sth::video::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::video::userArgsArray(mode)
    if {[catch {::sth::video::emulation_video_stats $mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get $type stats : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
