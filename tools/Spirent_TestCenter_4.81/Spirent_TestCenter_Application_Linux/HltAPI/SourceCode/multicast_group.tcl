# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth {
   proc emulation_multicast_group_config {args} {
      variable ::sth::multicast_group::userArgsArray
      variable sortedSwitchPriorityList

      array unset ::sth::multicast_group::userArgsArray
      array set ::sth::multicast_group::userArgsArray {}

      set returnKeyedList ""

      ::sth::sthCore::Tracker emulation_multicast_group_config $args
      ::sth::sthCore::commandInit \
            ::sth::multicast_group::multicast_groupTable \
            $args \
            ::sth::multicast_group:: \
            emulation_multicast_group_config \
            ::sth::multicast_group::userArgsArray \
            sortedSwitchPriorityList

      set mode $::sth::multicast_group::userArgsArray(mode)

      set retVal [catch {
         switch -exact $mode {
            create {
               ::sth::multicast_group::emulation_multicast_group_config_create \
                     returnKeyedList
            }

            modify {
               ::sth::multicast_group::emulation_multicast_group_config_modify \
                     returnKeyedList
            }

            delete {
               ::sth::multicast_group::emulation_multicast_config_delete \
                     returnKeyedList
            }

            default {
               # Unsupported mode
               ::sth::sthCore::processError returnKeyedList \
                     "Error:  Unsupported -mode value $mode" {}
               return -code error $returnKeyedList
            }
         }
      } returnedString]

      return $returnKeyedList
   }

   proc emulation_multicast_source_config {args} {
      variable ::sth::multicast_group::userArgsArray
      variable sortedSwitchPriorityList

      array unset ::sth::multicast_group::userArgsArray
      array set ::sth::multicast_group::userArgsArray {}

      set returnKeyedList ""

      ::sth::sthCore::Tracker emulation_multicast_source_config $args
      ::sth::sthCore::commandInit \
            ::sth::multicast_group::multicast_groupTable \
            $args \
            ::sth::multicast_group:: \
            emulation_multicast_source_config \
            ::sth::multicast_group::userArgsArray \
            sortedSwitchPriorityList

      set mode $::sth::multicast_group::userArgsArray(mode)

      set retVal [catch {
         switch -exact $mode {
            create {
               ::sth::multicast_group::emulation_multicast_source_config_create \
                     returnKeyedList
            }

            modify {
               ::sth::multicast_group::emulation_multicast_source_config_modify \
                     returnKeyedList
            }

            delete {
               ::sth::multicast_group::emulation_multicast_source_config_delete \
                     returnKeyedList
            }

            default {
               # Unsupported mode
               ::sth::sthCore::processError returnKeyedList \
                     "Error:  Unsupported -mode value $mode" {}
               return -code error $returnKeyedList
            }
         }
      } returnedString]

      return $returnKeyedList
   }
   
    # This proc configures/deletes multicast configuration using Wizard method
    proc ::sth::emulation_mcast_wizard_config {args} { 
    
        ::sth::sthCore::Tracker "::sth::emulation_mcast_wizard_config" $args
        variable ::sth::multicast_group::userArgsArray
        variable ::sth::multicast_group::sortedSwitchPriorityList
        array unset ::sth::multicast_group::userArgsArray
        array set ::sth::multicast_group::userArgsArray {}
        set _hltCmdName "emulation_mcast_wizard_config"
        set returnKeyedList ""
        
        if {[catch {::sth::sthCore::commandInit ::sth::multicast_group::multicast_groupTable $args \
                                                                ::sth::multicast_group::\
                                                                emulation_mcast_wizard_config \
                                                                ::sth::multicast_group::userArgsArray \
                                                                ::sth::multicast_group::sortedSwitchPriorityList} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
                return $returnKeyedList
        }
    	
        set mode $::sth::multicast_group::userArgsArray(mode)   
        if {[catch {::sth::multicast_group::emulation_mcast_wizard_config_$mode returnKeyedList} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in emulation_mcast_wizard_config : $err"
        }
        return $returnKeyedList
    } 
}
