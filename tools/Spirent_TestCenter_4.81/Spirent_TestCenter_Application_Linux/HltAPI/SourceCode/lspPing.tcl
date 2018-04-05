namespace eval ::sth:: {
}
namespace eval ::sth::lspPing:: {
}
proc ::sth::emulation_lsp_ping_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_lsp_ping_config" $args

    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::sortedSwitchPriorityList
    array unset ::sth::lspPing::userArgsArray
    array set ::sth::lspPing::userArgsArray {}

    set _hltCmdName "emulation_lsp_ping_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::lspPing::lspPingTable $args \
                                                            ::sth::lspPing:: \
                                                            emulation_lsp_ping_config \
                                                            ::sth::lspPing::userArgsArray \
                                                            ::sth::lspPing::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::lspPing::emulation_lsp_ping_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing lsp ping config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::lspPing::userArgsArray(mode)
    
    ::sth::lspPing::emulation_lsp_ping_config_$mode myReturnKeyedList
}
proc ::sth::emulation_lsp_ping_message_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_lsp_ping_message_config" $args

    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::sortedSwitchPriorityList
    array unset ::sth::lspPing::userArgsArray
    array set ::sth::lspPing::userArgsArray {}

    set _hltCmdName "emulation_lsp_ping_message_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::lspPing::lspPingTable $args \
                                                            ::sth::lspPing:: \
                                                            emulation_lsp_ping_message_config \
                                                            ::sth::lspPing::userArgsArray \
                                                            ::sth::lspPing::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::lspPing::emulation_lsp_ping_message_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing lsp ping message config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_message_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::lspPing::userArgsArray(mode)
    
    ::sth::lspPing::emulation_lsp_ping_message_config_$mode myReturnKeyedList
}
proc ::sth::emulation_lsp_ping_fec_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_lsp_ping_fec_config" $args

    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::sortedSwitchPriorityList
    array unset ::sth::lspPing::userArgsArray
    array set ::sth::lspPing::userArgsArray {}

    set _hltCmdName "emulation_lsp_ping_fec_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::lspPing::lspPingTable $args \
                                                            ::sth::lspPing:: \
                                                            emulation_lsp_ping_fec_config \
                                                            ::sth::lspPing::userArgsArray \
                                                            ::sth::lspPing::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::lspPing::emulation_lsp_ping_fec_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing lsp ping fec config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_fec_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::lspPing::userArgsArray(mode)
    
    ::sth::lspPing::emulation_lsp_ping_fec_config_$mode myReturnKeyedList
}