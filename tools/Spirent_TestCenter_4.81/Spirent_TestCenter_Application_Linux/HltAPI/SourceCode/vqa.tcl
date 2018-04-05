#!/bin/sh
# -*- tcl -*-
# The next line is executed by /bin/sh, but not tcl
namespace eval ::sth:: {

}

proc ::sth::emulation_vqa_host_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_vqa_host_config" $args

    variable ::sth::Vqa::userArgsArray
    variable ::sth::Vqa::sortedSwitchPriorityList
    array unset ::sth::Vqa::userArgsArray
    array set ::sth::Vqa::userArgsArray {}

    set _hltCmdName "emulation_vqa_host_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Vqa::vqaTable $args \
                                                            ::sth::Vqa:: \
                                                            emulation_vqa_host_config \
                                                            ::sth::Vqa::userArgsArray \
                                                            ::sth::Vqa::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::Vqa::userArgsArray(mode)
    if {[catch {::sth::Vqa::emulation_vqa_host_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing VQA device : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}



proc ::sth::emulation_vqa_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_vqa_config" $args

    variable ::sth::Vqa::userArgsArray
    variable ::sth::Vqa::sortedSwitchPriorityList
    array unset ::sth::Vqa::userArgsArray
    array set ::sth::Vqa::userArgsArray {}

    set _hltCmdName "emulation_vqa_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Vqa::vqaTable $args \
                                                            ::sth::Vqa:: \
                                                            emulation_vqa_config \
                                                            ::sth::Vqa::userArgsArray \
                                                            ::sth::Vqa::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::Vqa::userArgsArray(mode)
    if {[catch {::sth::Vqa::emulation_vqa_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing VQA config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_vqa_port_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_vqa_port_config" $args

    variable ::sth::Vqa::userArgsArray
    variable ::sth::Vqa::sortedSwitchPriorityList
    array unset ::sth::Vqa::userArgsArray
    array set ::sth::Vqa::userArgsArray {}

    set _hltCmdName "emulation_vqa_port_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Vqa::vqaTable $args \
                                                            ::sth::Vqa:: \
                                                            emulation_vqa_port_config \
                                                            ::sth::Vqa::userArgsArray \
                                                            ::sth::Vqa::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $::sth::Vqa::userArgsArray(mode)
    if {[catch {::sth::Vqa::emulation_vqa_port_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing VQA port config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_vqa_global_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_vqa_global_config" $args

    variable ::sth::Vqa::userArgsArray
    variable ::sth::Vqa::sortedSwitchPriorityList
    array unset ::sth::Vqa::userArgsArray
    array set ::sth::Vqa::userArgsArray {}

    set _hltCmdName "emulation_vqa_global_config"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Vqa::vqaTable $args \
                                                            ::sth::Vqa:: \
                                                            emulation_vqa_global_config \
                                                            ::sth::Vqa::userArgsArray \
                                                            ::sth::Vqa::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode config
    if {[catch {::sth::Vqa::emulation_vqa_global_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing VQA global config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}



proc ::sth::emulation_vqa_control { args } {

    ::sth::sthCore::Tracker "::sth::emulation_vqa_control" $args

    variable ::sth::Vqa::userArgsArray
    variable ::sth::Vqa::sortedSwitchPriorityList
    array unset ::sth::Vqa::userArgsArray
    array set ::sth::Vqa::userArgsArray {}

    set _hltCmdName "emulation_vqa_control"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Vqa::vqaTable $args \
                                                            ::sth::Vqa:: \
                                                            emulation_vqa_control \
                                                            ::sth::Vqa::userArgsArray \
                                                            ::sth::Vqa::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set action $::sth::Vqa::userArgsArray(action)
    if {[catch {::sth::Vqa::emulation_vqa_control $action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $action\ing VQA block : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_vqa_stats { args } {

    ::sth::sthCore::Tracker "::sth::emulation_vqa_stats" $args

    variable ::sth::Vqa::userArgsArray
    variable ::sth::Vqa::sortedSwitchPriorityList
    array unset ::sth::Vqa::userArgsArray
    array set ::sth::Vqa::userArgsArray {}

    set _hltCmdName "emulation_vqa_stats"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Vqa::vqaTable $args \
                                                            ::sth::Vqa:: \
                                                            emulation_vqa_stats \
                                                            ::sth::Vqa::userArgsArray \
                                                            ::sth::Vqa::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    set mode $userArgsArray(mode)
    if {[catch {::sth::Vqa::emulation_vqa_stats $mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get $mode result : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
