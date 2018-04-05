# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::iptv {
   proc emulation_iptv_config_enable {returnKeyedListVarName} {
      upvar 1 $returnKeyedListVarName returnKeyedList
      variable userArgsArray
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)

      #check if the device handle has been configured with the igmp or mld
      set deviceHnd $::sth::iptv::userArgsArray(handle)

      set igmpHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-igmphostconfig]
      set mldHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-mldhostconfig]
      if {$igmpHnd == "" && $mldHnd == ""} {
         ::sth::sthCore::processError returnKeyedList "IGMP or MLD Device required !"
         return $returnKeyedList
      }
      set iptvHnd [::sth::sthCore::invoke stc::create IptvStbBlockConfig -under $deviceHnd]
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr [list $switchValue] "
      }
      ::sth::sthCore::invoke stc::config $iptvHnd $optionList
      if {$igmpHnd != ""} {
         ::sth::sthCore::invoke stc::config $iptvHnd multicastparam-targets $igmpHnd
      }
      if {$mldHnd != ""} {
         ::sth::sthCore::invoke stc::config $iptvHnd multicastparam-targets $mldHnd
      }
      keylset returnKeyedList session_handle $iptvHnd
      return $returnKeyedList
   }

   proc emulation_iptv_config_modify {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      #check if the device handle has been configured with the igmp or mld

      if {[regexp -nocase "IptvStbBlockConfig" $::sth::iptv::userArgsArray(handle)]} {
         set iptvHnd $::sth::iptv::userArgsArray(handle)
      } elseif {[IsIptvHandleValid $::sth::iptv::userArgsArray(handle)]} {
         set deviceHnd $::sth::iptv::userArgsArray(handle)
         set iptvHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-IptvStbBlockConfig]
      }

      if {$iptvHnd != ""} {
         set optionList ""
         foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_config $optArg stcattr]
            if {[string equal -nocase $stcAttr "_none_"]} {
               continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr $switchValue "
         }
         ::sth::sthCore::invoke stc::config $iptvHnd $optionList
      }
   }

   proc emulation_iptv_config_disable {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      #check if the device handle has been configured with the igmp or mld
      set iptvHndList ""
      if {[regexp -nocase "IptvStbBlockConfig" $::sth::iptv::userArgsArray(handle)]} {
         set iptvHndList $userArgsArray(handle)
      } else {
         foreach device $::sth::iptv::userArgsArray(handle) {
            if {[IsIptvHandleValid $device]} {
               set iptvHnd [::sth::sthCore::invoke stc::get $device -children-IptvStbBlockConfig]
            }
            lappend iptvHndList $iptvHnd
         }
      }
      foreach iptvHnd $iptvHndList {
         ::sth::sthCore::invoke stc::delete $iptvHnd
      }
   }

   proc emulation_iptv_viewing_behavior_profile_config_create {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvProfileHnd [::sth::sthCore::invoke stc::create IptvViewingProfileConfig -under project1]
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_viewing_behavior_profile_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      ::sth::sthCore::invoke stc::config $iptvProfileHnd $optionList
      keylset returnKeyedList handle $iptvProfileHnd
      return $returnKeyedList
   }

   proc emulation_iptv_viewing_behavior_profile_config_modify {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvProfileHnd $userArgsArray(handle)
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_viewing_behavior_profile_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      ::sth::sthCore::invoke stc::config $iptvProfileHnd $optionList
      return $returnKeyedList
   }

   proc emulation_iptv_viewing_behavior_profile_config_delete {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvProfileHnd ""
      foreach iptvProfileHnd $userArgsArray(handle) {
         ::sth::sthCore::invoke stc::delete $iptvProfileHnd
      }
      return $returnKeyedList
   }

   proc emulation_iptv_channel_viewing_profile_config_create {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvChannelProfileHnd [::sth::sthCore::invoke stc::create IptvViewedChannels -under project1]
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_channel_viewing_profile_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      ::sth::sthCore::invoke stc::config $iptvChannelProfileHnd $optionList
      keylset returnKeyedList handle $iptvChannelProfileHnd
      return $returnKeyedList
   }

   proc emulation_iptv_channel_viewing_profile_config_modify {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvChannelProfileHnd $userArgsArray(handle)
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_channel_viewing_profile_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      ::sth::sthCore::invoke stc::config $iptvChannelProfileHnd $optionList
      return $returnKeyedList
   }

   proc emulation_iptv_channel_viewing_profile_config_delete {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvChannelProfileHnd ""
      foreach iptvChannelProfileHnd $userArgsArray(handle) {
         ::sth::sthCore::invoke stc::delete $iptvChannelProfileHnd
      }
      return $returnKeyedList
   }

   proc emulation_iptv_channel_block_config_create {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues "$userArgsArray(optional_args) $userArgsArray(mandatory_args)"
      set iptvChannelBlockHnd [::sth::sthCore::invoke stc::create IptvChannelBlock -under project1]
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_channel_block_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      ::sth::sthCore::invoke stc::config $iptvChannelBlockHnd $optionList
      if {[info exists userArgsArray(source_pool_handle)] && $userArgsArray(user_source_enable)} {
                  emulation_iptv_group_config_srcPool \
                        $userArgsArray(source_pool_handle) \
                        $iptvChannelBlockHnd
      }

      keylset returnKeyedList handle $iptvChannelBlockHnd
      return $returnKeyedList
   }


 proc emulation_iptv_group_config_srcPool {srcPoolHandleList iptvChannelBlockHnd} {
   variable userArgsArray
   if {[regexp "ipv4" $userArgsArray(multicast_group_handle)]} {
      set srcIpv4NetworkBlock [::sth::sthCore::invoke stc::get $iptvChannelBlockHnd -children-Ipv4NetworkBlock]
      if {$srcIpv4NetworkBlock == ""} {
         set srcIpv4NetworkBlock [::sth::sthCore::invoke stc::create Ipv4NetworkBlock -under $iptvChannelBlockHnd]
      }
      ::sth::igmp::emulation_igmp_group_config_srcPool $srcPoolHandleList $iptvChannelBlockHnd
   } else {
      set srcIpv6NetworkBlock [::sth::sthCore::invoke stc::get $iptvChannelBlockHnd -children-Ipv6NetworkBlock]
      if {$srcIpv6NetworkBlock == ""} {
         set srcIpv6NetworkBlock [::sth::sthCore::invoke stc::create Ipv6NetworkBlock -under $iptvChannelBlockHnd]
      }
      ::Mld::emulation_mld_group_config_srcPool $srcPoolHandleList $iptvChannelBlockHnd
   }
}


   proc emulation_iptv_channel_block_config_modify {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvChannelBlockHnd $userArgsArray(handle)
      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_channel_block_config $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      ::sth::sthCore::invoke stc::config $iptvChannelBlockHnd $optionList
      return $returnKeyedList
   }

   proc emulation_iptv_channel_block_config_delete {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      set iptvChannelBlockHnd ""
      foreach iptvChannelBlockHnd $userArgsArray(handle) {
         ::sth::sthCore::invoke stc::delete $iptvChannelBlockHnd
      }

      return $returnKeyedList
   }

   proc emulation_iptv_control_start {returnKeyedListVarName} {
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
      set iptvChannelBlockHnd ""
      if {[info exists userArgsArray(handle)]} {
         set device $userArgsArray(handle)
         if {[regexp -nocase "IptvStbBlockConfig" $userArgsArray(handle)]} {
            set iptvChannelBlockHnd $userArgsArray(handle)
         } else {
            foreach d $device {
               if {[IsIptvHandleValid $d]} {
                  lappend iptvChannelBlockHnd [::sth::sthCore::invoke stc::get $d -children-IptvStbBlockConfig]
               }
            }
         }
      } elseif {[info exists userArgsArray(port_handle)]} {
         foreach port $userArgsArray(port_handle) {
              if {[::sth::sthCore::IsPortValid $port err]} {
                  set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                  foreach device $deviceHandle {
                     if {![IsIptvHandleValid $device]} { continue }
                     lappend iptvChannelBlockHnd [::sth::sthCore::invoke stc::get $device -children-IptvStbBlockConfig]
                  }
               } else {
                  ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                  return -code error $returnKeyedList
               }
            }
      } else {
         ::sth::sthCore::processError returnKeyedList "Error: either the port_handle or the handle need to be specified" {}
         return -code error $returnKeyedList
      }

      set optionList ""
      foreach optArg $switches {
         set stcAttr [::sth::sthCore::getswitchprop ::sth::iptv:: emulation_iptv_control $optArg stcattr]
         if {[string equal -nocase $stcAttr "_none_"]} {
            continue
         }
         set switchValue $switchValues($optArg)
         append optionList "-$stcAttr $switchValue "
      }
      append optionList "-StbBlockList [list $iptvChannelBlockHnd]"
      eval ::sth::sthCore::invoke stc::perform IptvStartTestCommand $optionList
      return $returnKeyedList
   }

   proc emulation_iptv_control_stop {returnKeyedListVarName} {
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::invoke stc::perform IptvStopTestCommand
      return $returnKeyedList
   }
   proc emulation_iptv_control_wait {returnKeyedListVarName} {
      upvar 1 $returnKeyedListVarName returnKeyedList
      ::sth::sthCore::invoke stc::perform IptvWaitForTestCompletionCommand
      return $returnKeyedList
   }

   proc emulation_iptv_stats { returnKeyedListVarName } {
      set procName [lindex [info level [info level]] 0]
      variable userArgsArray
      upvar 1 $returnKeyedListVarName returnKeyedList
      set mode $userArgsArray(mode)
      set retVal [catch {
         set deviceHandleList ""
         array set portAgg ""
         if {[info exists userArgsArray(handle)]} {
            foreach handle $userArgsArray(handle) {
                if {![IsIptvHandleValid $handle]} {
                 ::sth::sthCore::processError returnKeyedList "Error: $handle is not valid iptv handle" {}
                 return -code error $returnKeyedList
               }
               lappend deviceHandleList $handle
            }
            if {$mode == "port" && ![info exists userArgsArray(port_handle)]} {
               ::sth::sthCore::processError returnKeyedList "Error: port_handle is required for mode: $mode" {}
               return -code error $returnKeyedList
            }
         } elseif {[info exists userArgsArray(port_handle)]} {
            foreach port $userArgsArray(port_handle) {
               set portAgg($port) 0
               if {[::sth::sthCore::IsPortValid $port err]} {
                  set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                  foreach device $deviceHandle {
                     if {![IsIptvHandleValid $device]} { continue }
                     lappend deviceHandleList $device
                  }
               } else {
                  ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                  return -code error $returnKeyedList
               }
            }
         } else {
            #neither port_handle or handle is input, only when the mode is test, it can work
            if {$mode != "test"} {
               if {$mode == "port"} {
                  ::sth::sthCore::processError returnKeyedList "Error: port_handle is required for mode: $mode" {}
                  return -code error $returnKeyedList
               } else {
                  ::sth::sthCore::processError returnKeyedList "Error: port_handle or handle is required for mode: $mode" {}
                  return -code error $returnKeyedList
               }
            }
         }

         ::sth::sthCore::invoke stc::sleep 10
         set configObjList ""
         set configClass ""
         array set resultType {set_top_box iptvstbblockresults viewing_profile IptvViewingProfileResults channel IptvChannelResults port IptvPortResults test IptvTestResults}
         if {[regexp "set_top_box" $mode]} {
            set configClass "iptvstbblockconfig"
            foreach device $deviceHandleList {
               set iptvBlockCfg [::sth::sthCore::invoke stc::get $device -children-iptvstbblockconfig]
               lappend configObjList $iptvBlockCfg
            }
         } elseif {[regexp "viewing_profile" $mode]} {
            set configClass "IptvViewingProfileConfig"
            foreach device $deviceHandleList {
               set iptvBlockCfg [::sth::sthCore::invoke stc::get $device -children-iptvstbblockconfig]
               set iptvViewingProfile [::sth::sthCore::invoke stc::get $iptvBlockCfg -iptvprofile-targets]
               lappend configObjList $iptvViewingProfile
            }
         } elseif {[regexp "channel" $mode]} {
            set configClass "IptvViewedChannels"
            foreach device $deviceHandleList {
               set iptvBlockCfg [::sth::sthCore::invoke stc::get $device -children-iptvstbblockconfig]
               set iptvChannel [::sth::sthCore::invoke stc::get $iptvBlockCfg -stbchannel-Targets]
               lappend configObjList $iptvChannel
            }
         } elseif {[regexp "test" $mode]} {
            set configObjList $::sth::sthCore::GBLHNDMAP(project)
         } elseif {[regexp "port" $mode]} {
            if {[info exists userArgsArray(port_handle)]} {
               set configObjList $userArgsArray(port_handle)
            } else {
               set configObjList [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) -children-port]
            }
         }
         if {$configClass !=""} {
            sth::sthCore::invoke stc::subscribe \
                                               -Parent $::sth::sthCore::GBLHNDMAP(project) \
                                               -ResultType $resultType($mode) \
                                               -ConfigType $configClass \
                                               -ResultParent $configObjList

            ::sth::sthCore::invoke stc::sleep 3
         }
         foreach configObj $configObjList {

            if {[regexp "set_top_box" $mode]} {
               set firstKey [::sth::sthCore::invoke stc::get $configObj -parent]
            } else {
               set firstKey $configObj
            }
            set name [::sth::sthCore::invoke stc::get $firstKey -name]
            set iptvResults [::sth::sthCore::invoke stc::get $configObj -children-$resultType($mode)]
            if {$iptvResults == ""} {
               continue
            }

            foreach key [array names ::sth::iptv::emulation_iptv_stats_$mode\_stcattr] {
               set stcAttr [set ::sth::iptv::emulation_iptv_stats_$mode\_stcattr($key)]
               if {[string match $stcAttr  "_none_"]} {
                  continue
               }
               set val [::sth::sthCore::invoke stc::get $iptvResults -$stcAttr]
               if {$mode == "test"} {
                  set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$mode.$key" $val]
               } else {
                  set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$mode.$firstKey.$key" $val]
               }
            }
            if {$mode != "test"} {
               set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$mode.$firstKey.name" $name]
            }
         }
      } returnedString]

      if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }
      return $returnKeyedList
   }

   proc IsIptvHandleValid {handle} {

      set cmdStatus 1

      if {[catch {set iptvStbConfig [::sth::sthCore::invoke stc::get $handle -children-IptvStbBlockConfig]} err]} {
         set cmdStatus 0
      }
      if {[string length $iptvStbConfig] == 0} {
         set cmdStatus 0
      }
      if {$cmdStatus == 1} {
         return $::sth::sthCore::SUCCESS
      } else {
         ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid iptv handle"
         return $::sth::sthCore::FAILURE
      }
   }
}
