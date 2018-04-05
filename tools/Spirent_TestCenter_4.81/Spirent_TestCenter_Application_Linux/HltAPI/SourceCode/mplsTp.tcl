# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth:: {
}

proc ::sth::emulation_mpls_tp_config { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_tp_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::MplsTp::emulation_mpls_tp_config\_input_and_default_args_array
    array unset ::sth::MplsTp::emulation_mpls_tp_config\_input_and_default_args_array
    array set ::sth::MplsTp::emulation_mpls_tp_config\_input_and_default_args_array {}
    
    variable ::sth::MplsTp::emulation_mpls_tp_config\_sortedSwitchPriorityList
    
    set _hltCmdName "emulation_mpls_tp_config"
    
            
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
 
    if {[catch {::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $args \
                                ::sth::MplsTp:: \
                                $_hltCmdName \
                                ::sth::MplsTp::emulation_mpls_tp_config\_input_and_default_args_array \
                                ::sth::MplsTp::emulation_mpls_tp_config\_sortedSwitchPriorityList } eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $eMsg" {}
        return $returnKeyedList
    }
            
    #switch to call processing functions for the mode of API
    set modeValue $::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(mode)
    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
    switch -exact $modeValue {
        create {
            set modeValue "create"
            set cmdStatus 0
            set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        delete {
            set modeValue "delete"
            set cmdStatus 0
            set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList                 
        }
    }

    
    if {[catch {set procResult [eval $cmd]} eMsg]} { 
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
        
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying MplsTp configuration: $msg"
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

proc ::sth::emulation_mpls_tp_port_config { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_tp_port_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::MplsTp::emulation_mpls_tp_port_config\_input_and_default_args_array
    array unset ::sth::MplsTp::emulation_mpls_tp_port_config\_input_and_default_args_array
    array set ::sth::MplsTp::emulation_mpls_tp_port_config\_input_and_default_args_array {}
    
    variable ::sth::MplsTp::emulation_mpls_tp_port_config\_sortedSwitchPriorityList
    
    set _hltCmdName "emulation_mpls_tp_port_config"
      
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
    
    if {[catch {::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $args \
                                ::sth::MplsTp:: \
                                $_hltCmdName \
                                ::sth::MplsTp::emulation_mpls_tp_port_config\_input_and_default_args_array \
                                ::sth::MplsTp::emulation_mpls_tp_port_config\_sortedSwitchPriorityList } eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $eMsg" {}
        return $returnKeyedList
    }
        
    #switch to call processing functions for the mode of API
    set modeValue "generic"
    set cmdStatus 0
    set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "

    
    if {[catch {set procResult [eval $cmd]} eMsg]} { 
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
        
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying MplsTp configuration: $msg"
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

proc ::sth::emulation_mpls_tp_control { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_tp_control $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::MplsTp::emulation_mpls_tp_control\_input_and_default_args_array
    array unset ::sth::MplsTp::emulation_mpls_tp_control\_input_and_default_args_array
    array set ::sth::MplsTp::emulation_mpls_tp_control\_input_and_default_args_array {}
    
    variable ::sth::MplsTp::emulation_mpls_tp_control\_sortedSwitchPriorityList
    
    set _hltCmdName "emulation_mpls_tp_control"

    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
    
    if {[catch {::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $args \
                                ::sth::MplsTp:: \
                                $_hltCmdName \
                                ::sth::MplsTp::emulation_mpls_tp_control\_input_and_default_args_array \
                                ::sth::MplsTp::emulation_mpls_tp_control\_sortedSwitchPriorityList } eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $eMsg" {}
        return $returnKeyedList
    }
           
    #switch to call processing functions for the mode of API
    set modeValue $::sth::MplsTp::emulation_mpls_tp_control_input_and_default_args_array(action)
    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"
    switch -exact $modeValue {
        start {
            set modeValue "start"
            set cmdStatus 0
            set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        stop {
            set modeValue "stop"
            set cmdStatus 0
            set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        start_lsp_ping {
            set modeValue "start_lsp_ping"
            set cmdStatus 0
            set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        stop_lsp_ping {
            set modeValue "stop_lsp_ping"
            set cmdStatus 0
            set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList                 
        }
    }

    
    if {[catch {set procResult [eval $cmd]} eMsg]} { 
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
        
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying MplsTp configuration: $msg"
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

proc ::sth::emulation_lsp_ping_info { args } {
    ::sth::sthCore::Tracker ::emulation_lsp_ping_info $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::MplsTp::emulation_lsp_ping_info\_input_and_default_args_array
    array unset ::sth::MplsTp::emulation_lsp_ping_info\_input_and_default_args_array
    array set ::sth::MplsTp::emulation_lsp_ping_info\_input_and_default_args_array {}
    
    variable ::sth::MplsTp::emulation_lsp_ping_info\_sortedSwitchPriorityList
    
    set _hltCmdName "emulation_lsp_ping_info"
    
            
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
    
    if {[catch {::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $args \
                                ::sth::MplsTp:: \
                                $_hltCmdName \
                                ::sth::MplsTp::emulation_lsp_ping_info\_input_and_default_args_array \
                                ::sth::MplsTp::emulation_lsp_ping_info\_sortedSwitchPriorityList } eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $eMsg" {}
        return $returnKeyedList
    }

    set modeValue $::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(mode)
    set cmdStatus 0
    set cmd "::sth::MplsTp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {set procResult [eval $cmd]} eMsg]} { 
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
        
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying MplsTp configuration: $msg"
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

