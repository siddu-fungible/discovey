# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.
package require Tclx

namespace eval ::sth {
}

proc ::sth::emulation_lldp_config { args } {
    ::sth::sthCore::Tracker ::emulation_lldp_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lldp::lldpTable

    set _hltCmdName "emulation_lldp_config"
    set myNameSpace "::sth::Lldp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lldp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lldp::lldpTable $args $myNameSpace $_hltCmdName ::sth::Lldp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList
    }
    
    set modeValue $::sth::Lldp::switchToValue(mode)
    
    switch -exact $modeValue {
        create {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue \{$args\} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        modify {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue \{$args\} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        reset_tlv {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue \{$args\} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        delete {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue \{$args\} returnKeyedList cmdStatus"
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
    #stc::perform SaveAsXml -FileName lldp_AT_test.xml
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying Lldp configuration in config: $msg"
        return $returnKeyedList 
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}

proc ::sth::emulation_lldp_optional_tlv_config { args } {
    ::sth::sthCore::Tracker ::emulation_lldp_optional_tlv_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lldp::lldpTable

    set _hltCmdName "emulation_lldp_optional_tlv_config"
    set myNameSpace "::sth::Lldp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lldp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lldp::lldpTable $args $myNameSpace $_hltCmdName ::sth::Lldp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList
    }
    
    set cmdStatus $SUCCESS
    set cmd "$myNameSpace$_hltCmdName\_img \{$args\} returnKeyedList cmdStatus"
    
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}

proc ::sth::emulation_lldp_dcbx_tlv_config { args } {
    ::sth::sthCore::Tracker ::emulation_lldp_dcbx_tlv_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lldp::lldpTable

    set _hltCmdName "emulation_lldp_dcbx_tlv_config"
    set myNameSpace "::sth::Lldp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lldp::switchToValue}
       
    set cmdStatus $SUCCESS
    set cmd "$myNameSpace$_hltCmdName\_img \{$args\} returnKeyedList cmdStatus"
    
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList handle $args
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}

proc ::sth::emulation_lldp_control { args } {
    ::sth::sthCore::Tracker ::emulation_lldp_control $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lldp::lldpTable

    set _hltCmdName "emulation_lldp_control"
    set myNameSpace "::sth::Lldp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lldp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lldp::lldpTable $args $myNameSpace $_hltCmdName ::sth::Lldp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList  
    }
    
    set modeValue $::sth::Lldp::switchToValue(mode)
    
    switch -exact $modeValue {
        start {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        stop {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        pause {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        resume {
            set cmdStatus $SUCCESS
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -action value $modeValue" {}
            return $returnKeyedList
        }
    }
    
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying Lldp configuration in config: $msg"
        return $returnKeyedList 
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}

proc ::sth::emulation_lldp_info { args } {
    ::sth::sthCore::Tracker ::emulation_lldp_info $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lldp::lldpTable

    set _hltCmdName "emulation_lldp_info"
    set myNameSpace "::sth::Lldp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lldp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lldp::lldpTable $args $myNameSpace $_hltCmdName ::sth::Lldp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList  
    }
    
    set modeValue $::sth::Lldp::switchToValue(mode)
    set cmdStatus $SUCCESS
    set cmd "$myNameSpace$_hltCmdName\_img returnKeyedList cmdStatus"
    ::sth::sthCore::log hltcall "CMD which will process: $cmd "
            
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}