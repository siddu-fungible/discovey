# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth::MplsTp {
	set createResultQuery 0
    array set coreParamHndAry {}
}

proc ::sth::MplsTp::emulation_mpls_tp_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_config"
    set _hltCmdName "emulation_mpls_tp_config_create"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    set stepError $::sth::sthCore::FAILURE
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    if {[info exists ::sth::MplsTp::emulation_mpls_tp_config_mode(port_handle)]} {
        #Check if input port handle is valid
        if {![info exists ::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(port_handle)]} {
            ::sth::sthCore::processErrorsub "port_handle switch with valid value is not provided." 
        } else {
            set handle $::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(port_handle)
            ::sth::sthCore::log debug "__VALIDATE__: Validate value of emulation_mpls_tp_config handle"
            
            # Defined input handle"s STC Object Type
            set objType "Port"
            ::sth::sthCore::isHandleValid $handle $objType
        }
    }
    
    set objectList {VpnMartiniGenParams VpnLspPingGenIpv4CoreParams VpnLspPingGenIpv4VpnParams VpnMplsTpGenParams VpnMplsTpLinearProtectionGenParams VpnMplsTpStaticProtectingLspGenParams VpnMplsTpStaticProtectingPwGenParams VpnMplsTpStaticWorkingLspGenParams VpnMplsTpStaticWorkingPwGenParams}
    array set hdlArray {}
    foreach objectName $objectList {
        set hdlArray($objectName) ""
    }
    
    if {$::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(test_type) eq "mplstp"} {
        set hdlArray(VpnMplsTpGenParams) [::sth::sthCore::invoke stc::create "VpnMplsTpGenParams" -under $::sth::GBLHNDMAP(project)]
        set hdlArray(VpnMplsTpLinearProtectionGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpGenParams) -children-VpnMplsTpLinearProtectionGenParams]
        set hdlArray(VpnMplsTpStaticProtectingLspGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpGenParams) -children-VpnMplsTpStaticProtectingLspGenParams]
        set hdlArray(VpnMplsTpStaticProtectingPwGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpGenParams) -children-VpnMplsTpStaticProtectingPwGenParams]
        set hdlArray(VpnMplsTpStaticWorkingLspGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpGenParams) -children-VpnMplsTpStaticWorkingLspGenParams]
        set hdlArray(VpnMplsTpStaticWorkingPwGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpGenParams) -children-VpnMplsTpStaticWorkingPwGenParams]

        ::sth::sthCore::configureCreate $_OrigHltCmdName MplsTp hdlArray
        set hdlKeyList [expandConfiguration $hdlArray(VpnMplsTpGenParams)]
        keylset returnKeyedList handle $hdlKeyList
    } else {
        set hdlArray(VpnMartiniGenParams) [::sth::sthCore::invoke stc::create "VpnMartiniGenParams" -under $::sth::GBLHNDMAP(project) {-CreatePeWithDirectTargetLdpSessions true}]
        set hdlArray(VpnLspPingGenIpv4CoreParams) [::sth::sthCore::invoke stc::create "VpnLspPingGenIpv4CoreParams" -under $hdlArray(VpnMartiniGenParams)]
        set hdlArray(VpnLspPingGenIpv4VpnParams) [::sth::sthCore::invoke stc::create "VpnLspPingGenIpv4VpnParams" -under $hdlArray(VpnMartiniGenParams)]
        
        ::sth::sthCore::configureCreate $_OrigHltCmdName MplsTp hdlArray
        
        set hdlKeyList [expandConfiguration $hdlArray(VpnMartiniGenParams)]
        keylset returnKeyedList handle $hdlKeyList
    }
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_mpls_tp_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_config"
    set _hltCmdName "emulation_mpls_tp_config_delete"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    set stepError $::sth::sthCore::FAILURE
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if input handle is valid
    #if {![info exists ::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(handle)]} {
    #    ::sth::sthCore::processErrorSub "handle switch with valid value is not provided." 
    #} else {
    #    set handle $::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(handle)
    #    ::sth::sthCore::log debug "__VALIDATE__: Validate value of emulation_mpls_tp_config handle"
    #    
    #    # Defined input handle"s STC Object Type
    #    set objType ""
    #    ::sth::sthCore::isHandleValid $handle $objType
    #}
    
    # vpnsite "VpnSiteInfoVplsLdp" - failing from 4.72 stc - deleting child object.
    array set objArr {
        vpn "VpnIdGroup"
        host "Host"
        router "Router"
    }
    
        

    #delete the streamblock firstly
    set handles [keylget ::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(handle) traffic]
    foreach handle $handles {
	::sth::sthCore::isHandleValid $handle streamblock
	if {[catch {::sth::sthCore::invoke stc::delete $handle} eMsg]} {
	    ::sth::sthCore::processErrorSub "Internal Command Error while deleting $handle. Error: $eMsg"           
	}
    }
    
    foreach obj [array names objArr] {
        set handles [keylget ::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(handle) $obj]
	foreach handle $handles {
		set objType $objArr($obj)
		::sth::sthCore::isHandleValid $handle $objType
		    
		if {[catch {::sth::sthCore::invoke stc::delete $handle} eMsg]} {
		     ::sth::sthCore::processErrorSub "Internal Command Error while deleting $handle. Error: $eMsg"           
		}
	}
    }
    
	
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_mpls_tp_lsp_work_bfd_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_bfd"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_bfd \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamBfdGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticWorkingLspGenParams) -children-VpnMplsTpOamBfdGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}

proc ::sth::MplsTp::emulation_mpls_tp_lsp_work_lsp_ping_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_lsp_ping"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_lsp_ping \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamLspPingGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticWorkingLspGenParams) -children-VpnMplsTpOamLspPingGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}


proc ::sth::MplsTp::emulation_mpls_tp_lsp_work_y1731_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_y1731"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"   
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_y1731 \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamY1731GenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticWorkingLspGenParams) -children-VpnMplsTpOamY1731GenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray

}


proc ::sth::MplsTp::emulation_mpls_tp_lsp_protect_bfd_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_bfd"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_bfd \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamBfdGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticProtectingLspGenParams) -children-VpnMplsTpOamBfdGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}

proc ::sth::MplsTp::emulation_mpls_tp_lsp_protect_lsp_ping_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_lsp_ping"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_lsp_ping \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamLspPingGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticProtectingLspGenParams) -children-VpnMplsTpOamLspPingGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}


proc ::sth::MplsTp::emulation_mpls_tp_lsp_protect_y1731_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_y1731"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"   
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_y1731 \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamY1731GenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticProtectingLspGenParams) -children-VpnMplsTpOamY1731GenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray

}

proc ::sth::MplsTp::emulation_mpls_tp_pwe_work_bfd_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_bfd"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_bfd \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamBfdGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticWorkingPwGenParams) -children-VpnMplsTpOamBfdGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}

proc ::sth::MplsTp::emulation_mpls_tp_pwe_work_lsp_ping_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_lsp_ping"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_lsp_ping \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamLspPingGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticWorkingPwGenParams) -children-VpnMplsTpOamLspPingGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}


proc ::sth::MplsTp::emulation_mpls_tp_pwe_work_y1731_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_y1731"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"   
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_y1731 \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamY1731GenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticWorkingPwGenParams) -children-VpnMplsTpOamY1731GenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray

}


proc ::sth::MplsTp::emulation_mpls_tp_pwe_protect_bfd_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_bfd"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_bfd \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_bfd\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamBfdGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticProtectingPwGenParams) -children-VpnMplsTpOamBfdGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}

proc ::sth::MplsTp::emulation_mpls_tp_pwe_protect_lsp_ping_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_lsp_ping"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"      
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_lsp_ping \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_lsp_ping\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamLspPingGenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticProtectingPwGenParams) -children-VpnMplsTpOamLspPingGenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}


proc ::sth::MplsTp::emulation_mpls_tp_pwe_protect_y1731_config { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_y1731"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"   
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_y1731 \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_y1731\_sortedSwitchPriorityList
    
    set hdlArray(VpnMplsTpOamY1731GenParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnMplsTpStaticProtectingPwGenParams) -children-VpnMplsTpOamY1731GenParams]
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray

}

proc ::sth::MplsTp::emulation_mpls_tp_config_core_lsp_ping { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_core_lsp_ping"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"
    
    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $switchValue"        
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_core_lsp_ping \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_core_lsp_ping\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_core_lsp_ping\_sortedSwitchPriorityList
    
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}

proc ::sth::MplsTp::emulation_mpls_tp_config_vpn_to_dut_lsp_ping { hdlArrayName switchName switchValue } {

    set _hltCmdName "emulation_mpls_tp_config_vpn_to_dut_lsp_ping"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"
    
    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $switchValue"        
    
    ::sth::sthCore::commandInit ::sth::MplsTp::MplsTpTable $switchValue \
                                                    ::sth::MplsTp:: \
                                                    emulation_mpls_tp_config_vpn_to_dut_lsp_ping \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_vpn_to_dut_lsp_ping\_input_and_default_args_array \
                                                    ::sth::MplsTp::emulation_mpls_tp_config_vpn_to_dut_lsp_ping\_sortedSwitchPriorityList
    
    ::sth::sthCore::configureCreate $_hltCmdName MplsTp hdlArray
    
}

proc ::sth::MplsTp::processCorePairList { hdlArrayName switchName switchValue } {
    set _hltCmdName "processCorePairList"
    
    foreach {work protect} $switchValue {
        ::sth::sthCore::invoke stc::config $::sth::MplsTp::coreParamHndAry($work) -WorkingProtectingRelation-targets "$::sth::MplsTp::coreParamHndAry($protect)"
    }
}

proc ::sth::MplsTp::processPortConfigCmd { hdlArrayName switchName switchValue } {
    set _hltCmdName "processPortConfigCmd"
    
    upvar 1 $hdlArrayName hdlArray
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName $hdlArrayName $switchName $switchValue"
    
    foreach port $switchValue {
        #remove the dash before the switch name in optional_args
        for {set i 0} {$i < [expr {[llength $port]/2}]} {incr i} {
            set index [expr {$i*2}]
            set nameNoDash [string range [lindex $port $index] 1 end]
            lset port $index $nameNoDash
        }
        array set switchPairArr $port
        if {$switchPairArr(type) == "core"} {
            if {$::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(test_type) eq "mplstp"} {
                set portHdl [::sth::sthCore::invoke stc::create "VpnMplsTpCorePortGenParams" -under $hdlArray(VpnMplsTpGenParams)]
            } else {
                if {$::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(pseudowire_type) == "single_segment"} {
                    set portHdl [::sth::sthCore::invoke stc::create "VpnMartiniGenCorePortParams" -under $hdlArray(VpnMartiniGenParams)]
                } else {
                    set portHdl [::sth::sthCore::invoke stc::create "MultiSegmentRightSitePortParams" -under $hdlArray(VpnMartiniGenParams)]
                }
            }
        } else {
            if {$::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(test_type) eq "mplstp"} {
                set portHdl [::sth::sthCore::invoke stc::create "VpnMplsTpCustPortGenParams" -under $hdlArray(VpnMplsTpGenParams)]
            } else {
                if {$::sth::MplsTp::emulation_mpls_tp_config_input_and_default_args_array(pseudowire_type) == "single_segment"} {
                    set portHdl [::sth::sthCore::invoke stc::create "VpnMartiniGenCustPortParams" -under $hdlArray(VpnMartiniGenParams)]
                } else {
                    set portHdl [::sth::sthCore::invoke stc::create "MultiSegmentLeftSitePortParams" -under $hdlArray(VpnMartiniGenParams)]
                }
            }
        }
        
        foreach {name value} $port {
            if {$name eq "type"} {
                continue
            } elseif {$name eq "name"} {
                array set ::sth::MplsTp::coreParamHndAry "$value $portHdl"
                continue
            }
            set dashedPair [list -$::sth::MplsTp::emulation_mpls_tp_port_config_stcattr($name) $value]
            ::sth::sthCore::invoke stc::config $portHdl $dashedPair
        }
    }
    
}

proc ::sth::MplsTp::emulation_mpls_tp_port_config_generic { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_port_config"
    set _hltCmdName "emulation_mpls_tp_port_config_generic"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    set stepError $::sth::sthCore::FAILURE
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if input handle is valid
    if {![info exists ::sth::MplsTp::emulation_mpls_tp_port_config_input_and_default_args_array(port_handle)]} {
        ::sth::sthCore::processErrorSub "handle switch with valid value is not provided."     
    } else {
        set handle $::sth::MplsTp::emulation_mpls_tp_port_config_input_and_default_args_array(port_handle)
        ::sth::sthCore::log debug "__VALIDATE__: Validate value of emulation_mpls_tp_port_config handle"
        
        # Defined input handle"s STC Object Type
        set objType "Port"
        ::sth::sthCore::isHandleValid $handle $objType
    }
    
    keylset returnKeyedList handle $args
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_mpls_tp_control_start { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_control"
    set _hltCmdName "emulation_mpls_tp_control_start"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        host "Host"
        router "Router"
    }
    
    foreach obj [array names objArr] {
        set handles [keylget ::sth::MplsTp::emulation_mpls_tp_control_input_and_default_args_array(handle) $obj]
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while Start $handles. Error: $eMsg"           
        }
    }
    if {$::sth::MplsTp::emulation_mpls_tp_control_input_and_default_args_array(handle) eq "pwe"} {
        ::sth::sthCore::ResultDataSetSubscribe ::sth::MplsTp:: IsisRouterConfig IsisRouterResults returnKeyedList
        set ::sth::MplsTp::createResultQuery 0
        ::sth::sthCore::ResultDataSetSubscribe ::sth::MplsTp:: BgpRouterConfig BgpRouterResults returnKeyedList
        set ::sth::MplsTp::createResultQuery 0
        ::sth::sthCore::ResultDataSetSubscribe ::sth::MplsTp:: LdpRouterConfig LdpRouterResults returnKeyedList
        set ::sth::MplsTp::createResultQuery 0
        ::sth::sthCore::ResultDataSetSubscribe ::sth::MplsTp:: RsvpRouterConfig RsvpRouterResults returnKeyedList
        set ::sth::MplsTp::createResultQuery 0
        ::sth::sthCore::ResultDataSetSubscribe ::sth::MplsTp:: OspfRouterConfig OspfRouterResults returnKeyedList
        set ::sth::MplsTp::createResultQuery 0
        ::sth::sthCore::ResultDataSetSubscribe ::sth::MplsTp:: RipRouterConfig RipRouterResults returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_mpls_tp_control_stop { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_control"
    set _hltCmdName "emulation_mpls_tp_control_stop"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        host "Host"
        router "Router"
    }
    
    foreach obj [array names objArr] {
        set handles [keylget ::sth::MplsTp::emulation_mpls_tp_control_input_and_default_args_array(handle) $obj]
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while stop $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_mpls_tp_control_start_lsp_ping { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_control"
    set _hltCmdName "emulation_mpls_tp_control_start_lsp_ping"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        lsp-ping "LspPingProtocolConfig"
    }
    
    foreach obj [array names objArr] {
        set handles [keylget ::sth::MplsTp::emulation_mpls_tp_control_input_and_default_args_array(handle) $obj]
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while start $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_mpls_tp_control_stop_lsp_ping { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_mpls_tp_control"
    set _hltCmdName "emulation_mpls_tp_control_stop_lsp_ping"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        lsp-ping "LspPingProtocolConfig"
    }
    
    foreach obj [array names objArr] {
        set handles [keylget ::sth::MplsTp::emulation_mpls_tp_control_input_and_default_args_array(handle) $obj]
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while stop $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_lsp_ping_info_aggregate { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_lsp_ping_info"
    set _hltCmdName "emulation_lsp_ping_info_aggregate"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if input handle is valid
    if {![info exists ::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(port_handle)]} {
        ::sth::sthCore::processErrorSub "handle switch with valid value is not provided."      
    } else {
        set handle $::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(port_handle)
        ::sth::sthCore::log debug "__VALIDATE__: Validate value of emulation_lsp_ping_info handle"
        
        foreach portHdl $handle {
            # Defined input handle"s STC Object Type
            set objType "Port"
            ::sth::sthCore::isHandleValid $portHdl $objType
        }
    }
    
    set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
    set resultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId LspPingProtocolConfig -ResultClassId LspPingProtocolResults"]
    ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
    ::sth::sthCore::invoke stc::sleep 3
    
    set index 1
    foreach portHdl $handle {
        set deviceHdls [sth::sthCore::invoke stc::get $portHdl -AffiliationPort-Sources]
        foreach device $deviceHdls {
            if {$device == ""} {
                continue
            }
            if {[string first router $device] >=0 || [string first emulateddevice $device] >=0 } {
                set lspHdl [sth::sthCore::invoke stc::get $device -Children-LspPingProtocolConfig]
               
                if {$lspHdl == ""} {
                    continue
                }
                set result_handle [sth::sthCore::invoke stc::get $lspHdl -Children-LspPingProtocolResults]
                
                foreach resultObj $result_handle {
                    array set resultValueAry [sth::sthCore::invoke stc::get $resultObj]
                    foreach switchName [array names ::sth::MplsTp::emulation_lsp_ping_info_aggregate_mode] {
                        set stcAttrName [::sth::sthCore::getswitchprop ::sth::MplsTp:: emulation_lsp_ping_info_aggregate $switchName stcattr]
                        if {$stcAttrName == "_none_"} {
                            continue
                        }
                        set switchValue $resultValueAry(-$stcAttrName)
                        keylset returnKeyedList $index\.$switchName $switchValue
                    }
                    keylset returnKeyedList $index\.port_handle $portHdl
                    keylset returnKeyedList $index\.device_handle $lspHdl
                    incr index
                }
            }
        }
    }
    ::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSet
    ::sth::sthCore::invoke stc::perform delete -ConfigList $resultDataSet
    
                        
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::MplsTp::emulation_lsp_ping_info_ping { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_lsp_ping_info"
    set _hltCmdName "emulation_lsp_ping_info_ping"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    set stepError $::sth::sthCore::FAILURE
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if input handle is valid
    if {![info exists ::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(port_handle)]} {
        ::sth::sthCore::processErrorSub "handle switch with valid value is not provided."      
    } else {
        set handle $::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(port_handle)
        ::sth::sthCore::log debug "__VALIDATE__: Validate value of emulation_lsp_ping_info handle"
        
        foreach portHdl $handle {
            # Defined input handle"s STC Object Type
            set objType "Port"
            ::sth::sthCore::isHandleValid $portHdl $objType
        }
    }
    
    set resultDataSet [sth::sthCore::invoke "stc::subscribe -parent $::sth::GBLHNDMAP(project) -ResultParent $::sth::GBLHNDMAP(project) -ConfigType LspPingProtocolConfig -resulttype LspPingPingResults"]
    after 2000
    set result_handle [sth::sthCore::invoke stc::get $resultDataSet -resultchild-Targets]
    
    set index 1
    foreach portHdl $handle {
        set deviceHdls [sth::sthCore::invoke stc::get $portHdl -AffiliationPort-Sources]
        foreach device $deviceHdls {
            if {$device == ""} {
                continue
            }
            if {[string first router $device] >=0 || [string first emulateddevice $device] >=0 } {
                set lspHdl [sth::sthCore::invoke stc::get $device -Children-LspPingProtocolConfig]
               
                if {$lspHdl == ""} {
                    continue
                }
                
                
                foreach resultObj $result_handle {
                    array set resultValueAry [sth::sthCore::invoke stc::get $resultObj]
                    set parent $resultValueAry(-parent)
                    if {$parent != $lspHdl} {
                        continue
                    }
                    foreach switchName [array names ::sth::MplsTp::emulation_lsp_ping_info_ping_mode] {
                        set stcAttrName [::sth::sthCore::getswitchprop ::sth::MplsTp:: emulation_lsp_ping_info_ping $switchName stcattr]
                        if {$stcAttrName == "_none_"} {
                            continue
                        }
                        set switchValue $resultValueAry(-$stcAttrName)
                        keylset returnKeyedList $index\.$switchName $switchValue
                    }
                    keylset returnKeyedList $index\.port_handle $portHdl
                    keylset returnKeyedList $index\.device_handle $lspHdl
                    incr index
                }
                
            }
        }
        
    }
    
    sth::sthCore::invoke "stc::unsubscribe $resultDataSet"
    sth::sthCore::invoke stc::delete $resultDataSet
                        
    set cmdState $SUCCESS
    return $returnKeyedList
}


proc ::sth::MplsTp::emulation_lsp_ping_info_trace_route { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_lsp_ping_info"
    set _hltCmdName "emulation_lsp_ping_info_trace_route"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if input handle is valid
    if {![info exists ::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(port_handle)]} {
        ::sth::sthCore::processErrorSub "handle switch with valid value is not provided."      
    } else {
        set handle $::sth::MplsTp::emulation_lsp_ping_info_input_and_default_args_array(port_handle)
        ::sth::sthCore::log debug "__VALIDATE__: Validate value of emulation_lsp_ping_info handle"
        
        foreach portHdl $handle {
            # Defined input handle"s STC Object Type
            set objType "Port"
            ::sth::sthCore::isHandleValid $portHdl $objType
        }
    }
    
    set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
    set resultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId LspPingProtocolConfig -ResultClassId LspPingTraceRouteResults"]
    ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
    ::sth::sthCore::invoke stc::sleep 3

    set index 1
    foreach portHdl $handle {
        set deviceHdls [sth::sthCore::invoke stc::get $portHdl -AffiliationPort-Sources]
        foreach device $deviceHdls {
            if {$device eq ""} {
                continue
            }
            if {[string first router $device] >=0 || [string first emulateddevice $device] >=0 } {
                set lspHdl [sth::sthCore::invoke stc::get $device -Children-LspPingProtocolConfig]
               
                if {$lspHdl eq ""} {
                    continue
                }
                set result_handle [sth::sthCore::invoke stc::get $lspHdl -Children-LspPingTraceRouteResults]
                
                foreach resultObj $result_handle {
                    array set resultValueAry [sth::sthCore::invoke stc::get $resultObj]
                    foreach switchName [array names ::sth::MplsTp::emulation_lsp_ping_info_trace_route_mode] {
                        set stcAttrName [::sth::sthCore::getswitchprop ::sth::MplsTp:: emulation_lsp_ping_info_trace_route $switchName stcattr]
                        if {$stcAttrName eq "_none_"} {
                            continue
                        }
                        set switchValue $resultValueAry(-$stcAttrName)
                        keylset returnKeyedList $index\.$switchName $switchValue
                    }
                    keylset returnKeyedList $index\.port_handle $portHdl
                    keylset returnKeyedList $index\.device_handle $lspHdl
                    incr index
                }
            }
        }
        
    }
    ::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSet
    ::sth::sthCore::invoke stc::perform delete -ConfigList $resultDataSet
    
    set cmdState $SUCCESS
    return $returnKeyedList
}


proc ::sth::MplsTp::expandConfiguration { VpnGenHandle } {
    
    set pre_streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
    ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
    set cmdState $::sth::sthCore::FAILURE
    return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set pre_streamList [concat $pre_streamList $stream]
        }
    }
    if {[catch {set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
    ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
    set cmdState $::sth::sthCore::FAILURE
    return $returnKeyedList
    }
    
    
    if {[catch {::sth::sthCore::invoke stc::perform VpnGenConfigExpand -clearportconfig no -genparams $VpnGenHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Unable to expand M-VPN configuration. Error: $errMsg" {} 
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    } 
    #if {[catch {::sth::sthCore::invoke stc::perform RtgTestGenConfigExpandCommand -clearportconfig no -genparams $VpnGenHandle -UseEmulatedDeviceType TRUE -EnableDetails TRUE}]} {
    #    ::sth::sthCore::processError returnKeyedList "Unable to expand MPLS-TP configuration." {} 
    #    set cmdState $::sth::sthCore::FAILURE
    #    return $returnKeyedList
    #}
    
    #if {[catch {::sth::sthCore::invoke stc::delete $VpnGenHandle} eMsg]} {
    #    ::sth::sthCore::processErrorSub "Internal Command Error while deleting $VpnGenHandle. Error: $eMsg"           
    #}
    
    set streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set streamList [concat $streamList $stream]
        }
    }
    if {[catch {set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
    ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
    set cmdState $::sth::sthCore::FAILURE
    return $returnKeyedList
    }
    
    #get new created devices" handles within mvpn 
    foreach stream $pre_streamList {
        set x [lsearch $streamList $stream]
        if { $x > -1 } {
            set streamList [lreplace $streamList $x $x]
        }
    }
    
    set childrenList [split $childrenStr]
    foreach child $pre_childrenStr {
        set x [lsearch $childrenList $child]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    
    set vpnIdGroupHdl ""
    set emulatedDeviceHdl ""
    set ipv4GroupHdl ""
    set vpnSiteInfoHdl ""
    set hostHdl ""
    set speRouter ""
    set tpeRouter ""
    set peRouter ""
    set pRouter ""
    set ospfSession ""
    set isisSession ""
    set ldpSession ""
    set rsvpSession ""
    set bgpSession ""
    set lspPingSession ""
    set bfdSession ""
    set mplstpOamHandleList ""
    set mplstpOamMegHandleList ""
    foreach child $childrenList {
        if { [string first "vpnidgroup" [string tolower $child]] > -1} {
            lappend vpnIdGroupHdl $child
        } elseif { [string first "emulateddevice" [string tolower $child]] > -1} {
            lappend emulatedDeviceHdl $child
        } elseif { [string first "router" [string tolower $child]] > -1} { 
            lappend emulatedDeviceHdl $child
        } elseif { [string first "vpnsiteinfovplsldp" [string tolower $child]] > -1} {
            lappend vpnSiteInfoHdl $child
        } elseif { [string first "host" [string tolower $child]] > -1} {
            lappend hostHdl $child
        }
    }
    
    foreach device $emulatedDeviceHdl {
        if {[catch {set deviceName [::sth::sthCore::invoke stc::get $device -Name]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Name from $device. Error: $errMsg" {} 
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList
        }
        
        lappend ospfSession [::sth::sthCore::invoke stc::get $device -Children-Ospfv2RouterConfig  ]
        lappend isisSession [::sth::sthCore::invoke stc::get $device -Children-IsisRouterConfig  ]
        lappend ldpSession [::sth::sthCore::invoke stc::get $device -Children-LdpRouterConfig  ]
        lappend rsvpSession [::sth::sthCore::invoke stc::get $device -Children-RsvpRouterConfig  ]
        lappend bgpSession [::sth::sthCore::invoke stc::get $device -Children-BgpRouterConfig  ]
        lappend lspPingSession [::sth::sthCore::invoke stc::get $device -Children-LspPingProtocolConfig  ]
        
        set bfdDevice [::sth::sthCore::invoke stc::get $device -Children-BfdRouterConfig]
        if {$bfdDevice ne ""} {
            lappend bfdSession $device
        }

        array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className MplsTpOamMpConfig -rootlist $device]
        append mplstpOamHandleList " $rtn(-ObjectList)"
        if {$rtn(-ObjectList) ne ""} {
            array set rtn [::sth::sthCore::invoke stc::get $rtn(-ObjectList)]
            append mplstpOamMegHandleList " $rtn(-mplstpoammegassociation-Targets)"
        }
        
        if { [string first "S-PE" $deviceName] > -1 } {
            lappend speRouter $device
        } elseif { [string first "T-PE" $deviceName] > -1 } {
            lappend tpeRouter $device
        } elseif { [string first "PE" $deviceName] > -1 } {
            lappend peRouter $device
        } elseif { [string first "P" $deviceName] > -1 } {
            lappend pRouter $device
        }
    }
    
    #Update Traffic API's global vars
    foreach streamHandle $streamList {
        set l2_encap "ethernet_ii"
        set ethHeader [stc::get $streamHandle -children-ethernet:ethernetii]
        set vlansHdr [stc::get $ethHeader -children-vlans]
        set vlan [stc::get $vlansHdr -children-vlan]
        if {$vlan ne ""} {
            set l2_encap "ethernet_ii_vlan"
        }
        set ::sth::Traffic::strHandlel2EncapMap($streamHandle) $l2_encap
        set ::sth::Traffic::arraystreamHnd($streamHandle) [set ::sth::Traffic::arrayHeaderLists($l2_encap)]
    }
    
    set handleKeyList ""
    keylset handleKeyList vpn $vpnIdGroupHdl
    keylset handleKeyList vpnsite $vpnSiteInfoHdl
    keylset handleKeyList host $hostHdl
    keylset handleKeyList router $emulatedDeviceHdl
    keylset handleKeyList s-pe $speRouter
    keylset handleKeyList t-pe $tpeRouter
    keylset handleKeyList pe $peRouter
    keylset handleKeyList p $pRouter
    keylset handleKeyList ospf $ospfSession
    keylset handleKeyList isis $isisSession
    keylset handleKeyList ldp $ldpSession
    keylset handleKeyList rsvp $rsvpSession
    keylset handleKeyList bgp $bgpSession
    keylset handleKeyList bfd $bfdSession
    keylset handleKeyList lsp-ping $lspPingSession
    keylset handleKeyList traffic $streamList
    keylset handleKeyList mplstp_y1731_oam.mp_handle $mplstpOamHandleList
    keylset handleKeyList mplstp_y1731_oam.meg_handle $mplstpOamMegHandleList
    #::stc::perform saveasxml -filename mpls_tp.xml
    return $handleKeyList
}

proc ::sth::sthCore::configureCreate { funcName MySpaceName hdlArrayName } {
    
    upvar 1 $hdlArrayName hdlArray
    
    set _hltCmdName "configureCreate"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName $funcName $MySpaceName $hdlArrayName"
    
    array set cmdArray {}
    foreach objectName [array names hdlArray] {
        set cmdArray($objectName) ""
    }
    
    foreach {switchName switchValue} [array get ::sth::$MySpaceName\::$funcName\_input_and_default_args_array] {
        if {$switchName == "mandatory_args" || $switchName == "optional_args"} {
            continue
        }
        # check dependency
        #if { $$funcName_dependency($switchName) != "_none_" } {
        #    array set dependencyList = $$funcName_dependency($switchName)
        #    foreach depParaName [array names dependencyList] {
        #        if ($$funcName_default($switchName) != $dependencyList(depParaName)) {
        #            continue
        #        }
        #    }
        #}
        set profuncName [::sth::sthCore::getswitchprop ::sth::$MySpaceName\:: $funcName $switchName procfunc]
        if {$profuncName == "CommonConfig"} {
            set stcObjName [::sth::sthCore::getswitchprop ::sth::$MySpaceName\:: $funcName $switchName stcobj]
            set stcAttrName [::sth::sthCore::getswitchprop ::sth::$MySpaceName\:: $funcName $switchName stcattr]
            if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::$MySpaceName\:: $funcName $switchName $switchValue]} getStatus]} {
                append cmdArray($stcObjName) " -$stcAttrName $attrValue"
            } else {
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            }
        } elseif { $profuncName == "_none_"} {
            continue
        } else {
            set cmd "::sth::$MySpaceName\::$profuncName hdlArray $switchName {$switchValue}"
            if {[catch {eval $cmd} status]} {
                ::sth::sthCore::processErrorSub "Config $switchName FAILED: errMsg = $status" 
            }
        }
    }
        
    #process all switches handled by CommonConfig
    foreach objName [array names cmdArray] {
#        puts "objName=$objName handle=$hdlArray($objName) cmd=$cmdArray($objName)"
        if {($cmdArray($objName) != "") & ([string length $hdlArray($objName)] > 3)} {
            set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
            #puts $cmd
            if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
                ::sth::sthCore::log error "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
                ::sth::sthCore::processErrorSub "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus" 
            } else {
                ::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
            }
        }
    }
    
    return
}

proc ::sth::sthCore::configureModify { userInput funcName MySpaceName hdlArrayName} {
    
    upvar 1 $hdlArrayName hdlArray
    
    set _hltCmdName "configureModify"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName $funcName $MySpaceName $hdlArrayName"
    
    #remove the dash before the switch name 
    for {set i 0} {$i < [expr {[llength $userInput]/2}]} {incr i} {
        set index [expr {$i*2}]
        set nameNoDash [string range [lindex $userInput $index] 1 end]
        lset userInput $index $nameNoDash
    }
    
    # Configure default
    foreach {switchName switchValue} $userInput {
        if {$switchName == "mandatory_args" || $switchName == "optional_args"} {
            continue
        }
        # check dependency
        #if { $$funcName_dependency($switchName) != "_none_" } {
        #    array set dependencyList = $$funcName_dependency($switchName)
        #    foreach depParaName [array names dependencyList] {
        #        if ($$funcName_default($switchName) != $dependencyList(depParaName)) {
        #            continue
        #        }
        #    }
        #}
        set profuncName [::sth::sthCore::getswitchprop ::sth::$MySpaceName\:: $funcName $switchName procfunc]
        if {$profuncName == "CommonConfig"} {
            set stcObjName [::sth::sthCore::getswitchprop ::sth::$MySpaceName\:: $funcName $switchName stcobj]
            set stcAttrName [::sth::sthCore::getswitchprop ::sth::$MySpaceName\:: $funcName $switchName stcattr]
            if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::$MySpaceName\:: $funcName $switchName $switchValue]} getStatus]} {
                append cmdArray($stcObjName) " -$stcAttrName $attrValue"
            } else {
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            }
        } elseif { $profuncName == "_none_"} {
            continue
        } else {
            set cmd "$$funcName_profunc($switchName) hdlArray $$funcName_default($switchName)"
            if {[catch {eval $cmd} status]} {
                ::sth::sthCore::processErrorSub "Config $switchName FAILED: errMsg = $status" 
            }
        }
    }
    
    
    #process all switches handled by CommonConfig
    foreach objName $objList {
#        puts "objName=$objName handle=$hdlArray($objName) cmd=$cmdArray($objName)"
        if {($cmdArray($objName) != "") & ([string length $hdlArray($objName)] > 3)} {
            set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
            #puts $cmd
            if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
                ::sth::sthCore::log error "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
                ::sth::sthCore::processErrorSub "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus" 
            } else {
                ::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
            }
        }
    }
    
    return
}

