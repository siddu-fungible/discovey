# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth:: {
    
}

namespace eval ::sth::testconfigcontrol:: {
    
}

namespace eval ::sth::sthCore:: {
    
}


proc ::sth::testconfigcontrol::procTestConfigArg { userArgArray switchName } {
    upvar $userArgArray myUserArgsArray
    variable localVarName
    set localVarName $switchName
    set localVarName $myUserArgsArray($switchName)
}

proc ::sth::testconfigcontrol::processTestControlAction { userArgsArray mySwitch } {
    
    upvar $userArgsArray myUserArgsArray
    set returnKeyedList ""

    set switchVal [set myUserArgsArray($mySwitch)]
    switch $switchVal {
        enable {
            set ::sth::sthCore::optimization 1
        }
        
        disable {
            set ::sth::sthCore::optimization 0
        }
        
        sync {
            ::sth::sthCore::invoke "stc::apply"
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Invalid call: ::sth::test_control -action $mySwitch"
            return $returnKeyedList
        }
    }
    keylset returnKeyedList status $:sth::sthCore::SUCCESS
    return $returnKeyedList
}


