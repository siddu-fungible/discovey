namespace eval ::sth:: {
}
proc ::sth::packet_decode { args } {
    ::sth::sthCore::Tracker "::sth::packet_decode" $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::packetDecode::processFlag
    
    variable sortedSwitchPriorityList
    variable userArgsArray
    
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
    
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_decode $args"
    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetDecode::packetDecodeTable $args ::sth::packetDecode:: packet_decode userArgsArray sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in packet_decode: commandInit FAILED. $err" {}
        return $returnKeyedList  
    }
    
    set cmdStatus 0
    set cmd "::sth::packetDecode::packet_decode userArgsArray returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd " 
    if {[catch {set procResult [eval $cmd]} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }

    ::sth::sthCore::log debug "COMMAND RESULT for command: packet_decode ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}