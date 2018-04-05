# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.


namespace eval ::sth::Gre:: {

}

#this procedure just store all the options into a list for further use 

proc ::sth::emulation_gre_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_gre_config" $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable sortedSwitchPriorityList
    variable userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set _hltCmdName "emulation_gre_config"
    
    set underScore "_"

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Gre::greTable $args ::sth::Gre:: $_hltCmdName userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList $err
        return $returnKeyedList
    }
    #For modify option
    if {[info exists userArgsArray(optional_args) ]} {
        array set OptionalGreConfig $userArgsArray(optional_args)
        set returnKey [list [array get userArgsArray]]
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
        if {[info exists OptionalGreConfig(-mode) ]} {
            if { [ string match -nocase "modify" $OptionalGreConfig(-mode) ]} {
                if {![info exists OptionalGreConfig(-gre_handle) ]} {
                    ::sth::sthCore::processError returnKeyedList "-gre_handle need to be specified when -mode is modify"
                    keylset returnKeyedList status $::sth::sthCore::FAILURE  
                } else {
                    if {[catch { ::sth::modifyGreDbd "$returnKey" } err]} {
                        keylset returnKeyedList status $::sth::sthCore::FAILURE
                    }
                }
                return $returnKeyedList
            }
        } elseif {[info exists OptionalGreConfig(-gre_handle)]} {
            if {[catch { ::sth::modifyGreDbd "$returnKey" } err]} {
                        keylset returnKeyedList status $::sth::sthCore::FAILURE
            }
            return $returnKeyedList
        }
    }
    
    set returnKeyedList [list [array get userArgsArray]]
}






