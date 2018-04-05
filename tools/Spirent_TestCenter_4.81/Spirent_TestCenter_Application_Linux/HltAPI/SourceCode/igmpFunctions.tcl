# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::igmp {

   # Keep track of host blocks created by IGMP commands.  This is to prevent
   # hosts created by other protocols from being manipulated unnecessarily.
   # For example, host created by PPPoX command being deleted by IGMP command.
   array unset igmpCreatedHosts

   # Spirent TestCenter configures the source filter mode in the IGMP group
   # membership object.  HLTAPI configures the filter mode through the
   # IGMP session config create/modify commands which do not modify the IGMP
   # group membership object.  Therefore, the filter mode must be recorded
   # here when the IGMP session is created/modified, where the HLTAPI group
   # create/modify config commands can retrieve them.
   array unset hostFilterMode
   array unset hostFilterIpAddr
   array unset igmpSessionConfig
   array unset igmpToClacLatencyMapper

   variable igmp_subscription_state 0

   proc emulation_igmp_config_create {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      array unset deviceList

      set retVal [catch {
         if {([info exists userArgsArray(port_handle)] == 0) && \
                  ([info exists userArgsArray(handle)] == 0)} {
            return -code error [concat "Error:  Unable to create an IGMP " \
                  "session.  Missing argument \"-port_handle\" or " \
                  "\"-handle\".  "]
         }

         if {[info exists userArgsArray(handle)]} {
            set hostList $userArgsArray(handle)
         } else {
            set hostList [::sth::igmp::emulation_igmp_config_getHostList \
                  hostList]
         }

         # Convert DHCP block config handle to parent host handle
         set newHostList ""
         foreach host $hostList {
            set type [::sth::sthCore::invoke stc::get $host -name]
            if {[lindex $type 0] == "Dhcpv4BlockConfig"} {
               set host [::sth::sthCore::invoke stc::get $host -parent]
               # Grab other associated Dhcp hosts (for QINQ)
               if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($host)]} {
                  set host $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($host)
               }
            }
            set newHostList [concat $newHostList $host]
         }

         # Special case where the filter mode is processed later in the IGMP
         # group config command.  Record the setting in
         # ::sth::igmp::hostFilterMode for later retrieval.
         variable hostFilterMode
         variable hostFilterIpAddr

         if {![regexp -nocase -- {-filter_mode} \
               $userArgsArray(optional_args)]} {
            set filterMode [::sth::sthCore::getswitchprop \
                  ::sth::igmp:: emulation_igmp_config filter_mode default]
         } else {
            set filterMode $userArgsArray(filter_mode)
         }
         
         #Rxu:  Support filter_ip_addr 
         if {![regexp -nocase -- {-filter_ip_addr } \
               $userArgsArray(optional_args)]} {
            set filterIpAddr [::sth::sthCore::getswitchprop \
                  ::sth::igmp:: emulation_igmp_config filter_ip_addr  default]
         } else {
            set filterIpAddr $userArgsArray(filter_ip_addr)
         }
         #end 
         
         set hostList $newHostList
         set igmpHostCfgList ""
         variable igmpToClacLatencyMapper
         if {[info exists userArgsArray(calculate_latency)] && $userArgsArray(calculate_latency) == "true"} {
               set calcLatency "true"
         } else {
               set calcLatency "false"
         }
         foreach host $hostList {
            set hostFilterMode($host) $filterMode
            set hostFilterIpAddr($host) $filterIpAddr
            # Add IGMP block config to each host
            set igmpHostCfgHnd [::sth::sthCore::invoke stc::create igmpHostConfig -under $host]
            set igmpToClacLatencyMapper($igmpHostCfgHnd) $calcLatency
            lappend igmpHostCfgList $igmpHostCfgHnd

         }

         if {[info exists userArgsArray(handle)]} {
            ::sth::igmp::emulation_igmp_config_pppox $hostList \
                  $returnKeyedListVarName
         } else {
            ::sth::igmp::emulation_igmp_config_modify_common \
                  $igmpHostCfgList $returnKeyedListVarName
         }
      }]

      return $returnKeyedList
   }

   proc emulation_igmp_config_modify {returnKeyedListVarName {level 1}} {
      variable userArgsArray
      variable igmpSessionConfig
      variable hostFilterMode
      variable hostFilterIpAddr
      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to modify IGMP " \
                  "session.  Missing mandatory argument \"-handle\".  "]
         }
         set userArgsArray(handle) [emulation_igmp_config_getIgmpHostCfgList $userArgsArray(handle)]
         set igmpHostCfgList $userArgsArray(handle)
               
         if {[info exists igmpSessionConfig($userArgsArray(handle))] == 0} {
            return -code error [concat "Error:  Unable to modify IGMP " \
                  "session.  Internal session configuration not found.  "]
         }
         # US38642 [CR23000][P1]Not able to modify filter_mode in emulation_igmp_group_config
         # update hostFilterMode(host) and hostFilterIpAddr(host) for igmp_config_modify
         if {[regexp -nocase -- {-filter_mode} $userArgsArray(optional_args)] && [regexp -nocase -- {-filter_ip_addr } $userArgsArray(optional_args)] } {
               foreach igmpHostCfgHnd $igmpHostCfgList {
                     set hostHnd [::sth::sthCore::invoke stc::get $igmpHostCfgHnd -parent]
                     set hostFilterMode($hostHnd) $userArgsArray(filter_mode) 
                     set hostFilterIpAddr($hostHnd) $userArgsArray(filter_ip_addr)
               }
         } elseif {[regexp -nocase -- {-filter_mode} $userArgsArray(optional_args)]} {
                      foreach igmpHostCfgHnd $igmpHostCfgList {
                          set hostHnd [::sth::sthCore::invoke stc::get $igmpHostCfgHnd -parent]
                          set hostFilterMode($hostHnd) $userArgsArray(filter_mode) 
                      }
         } elseif {[regexp -nocase -- {-filter_ip_addr} $userArgsArray(optional_args)]} {
                      foreach igmpHostCfgHnd $igmpHostCfgList {
                          set hostHnd [::sth::sthCore::invoke stc::get $igmpHostCfgHnd -parent]
                          set hostFilterIpAddr($hostHnd) $userArgsArray(filter_ip_addr)
                      }
         }
         if {[info exists userArgsArray(calculate_latency)]} {
             variable igmpToClacLatencyMapper
             set calcLatency $userArgsArray(calculate_latency)
             foreach igmpHostCfgHnd $igmpHostCfgList {
                 set  igmpToClacLatencyMapper($igmpHostCfgHnd) $calcLatency
                 set igmpGroupMembershipHnds [::sth::sthCore::invoke stc::get $igmpHostCfgHnd -children-igmpGroupMembership]
                 foreach igmpGroupMember $igmpGroupMembershipHnds {
                     ::sth::sthCore::invoke stc::config $igmpGroupMember -CalculateLatency $calcLatency
                 }
             }
         }
         array set igmpSessionCfg $igmpSessionConfig($userArgsArray(handle))
         array unset igmpSessionConfig $userArgsArray(handle)

         foreach {a v} $userArgsArray(optional_args) {
            if {[string equal $a "-handle"]} {
               continue
            }

            set igmpSessionCfg([string trimleft $a "-"]) $v
         }

         set igmpSessionCfg(optional_args) $userArgsArray(optional_args)
         array unset userArgsArray
         array set userArgsArray [array get igmpSessionCfg]
         
         ::sth::igmp::emulation_igmp_config_modify_common $igmpHostCfgList returnKeyedList

      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_config_pppox {hostList returnKeyedListVarName \
         {level 1}} {
      variable userArgsArray
      variable igmpSessionConfig
      
      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         set igmpHostCfgArgs ""

         foreach {arg val} $userArgsArray(optional_args) {
            set arg [string tolower [string trim [string trimleft \
                  $arg "-"]]]
            switch -exact -- $arg {
               "igmp_version" {
                  switch -exact $val {
                     v1 { set val igmp_v1 }
                     v2 { set val igmp_v2 }
                     v3 { set val igmp_v3 }
                     default {
                        return -code error [concat "Error:  Error encountered "\
                              "while configuring IGMP session.  Invalid IGMP "\
                              "version \"$userArgsArray(igmp_version)\".  "\
                              "Should be v1, v2, or v3.  "]
                     }
                  }
                  set stcArg [::sth::sthCore::getswitchprop \
                        ::sth::igmp:: \
                        emulation_igmp_config $arg stcattr]
                  lappend igmpHostCfgArgs "-$stcArg" $val
               }
               "older_version_timeout" -
               "force_single_join" -
               "force_robust_join" -
               "force_leave" -
               "insert_checksum_errors" -
               "unsolicited_report_interval" -
               "insert_length_errors" -
               "enable_df" -
               "tos" -
               "pack_reports" -
               "enable_router_alert" -
               "tos_type" -
               "robustness" {
                  set stcArg [::sth::sthCore::getswitchprop \
                        ::sth::igmp:: \
                        emulation_igmp_config $arg stcattr]
                  lappend igmpHostCfgArgs "-$stcArg" $val
               }
               "msg_interval" {
                  set stcArg [::sth::sthCore::getswitchprop \
                        ::sth::igmp:: \
                        emulation_igmp_config $arg stcattr]
                  lappend igmpPortCfgArgs "-$stcArg" $val
               }
            }
         }

         set igmpPortConfigList ""
         set igmpHostCfgList ""
         set i 0
         foreach host $hostList {
            
            #when enable the igmp protocol on this device and there is no ipv4 interface need to create it.
            set ethif [::sth::sthCore::invoke "stc::get $host -children-ethiiif"]
            set ipv4if [::sth::sthCore::invoke "stc::get $host -children-Ipv4If"]
            if {$ipv4if == ""} {
               set ipv4if [::sth::sthCore::invoke stc::create ipv4if -under $host]
               set ipIfStackedOnEndpointTarget $ethif
               set vlanif [::sth::sthCore::invoke stc::get $host -children-vlanif]
               if {$vlanif != ""} {
                  set ipIfStackedOnEndpointTarget [lindex $vlanif 0]
               }
               set stcObjLst(Ipv4If) ""
               lappend stcObjLst(Ipv4If) \
                     "-stackedonendpoint-Targets" $ipIfStackedOnEndpointTarget \
                     "-address" [::sth::sthCore::updateIpAddress \
                           4 $userArgsArray(intf_ip_addr) \
                           $userArgsArray(intf_ip_addr_step) $i] \
                     "-gateway" [::sth::sthCore::updateIpAddress \
                           4 $userArgsArray(neighbor_intf_ip_addr) \
                           $userArgsArray(neighbor_intf_ip_addr_step) $i]\
                     "-gatewaystep" $userArgsArray(neighbor_intf_ip_addr_step)
               
               ::sth::sthCore::invoke stc::config $ipv4if $stcObjLst(Ipv4If)

                set toplevelifTargets [stc::get $host -toplevelif-Targets]
                lappend toplevelifTargets $ipv4if
               ::sth::sthCore::invoke stc::config $host \
                        -toplevelif-Targets $toplevelifTargets
            } 

            set igmpHostCfg [::sth::sthCore::invoke stc::get $host -children-IgmpHostConfig]
            if {[string length $igmpHostCfgArgs] > 0} {
               ::sth::sthCore::invoke stc::config $igmpHostCfg $igmpHostCfgArgs
            }

            lappend igmpHostCfgList $igmpHostCfg
            # Modify IGMP host block config to use the information provided by
            # the PPPoX object
            ::sth::sthCore::invoke stc::config $igmpHostCfg [list "-usesIf-targets" [::sth::sthCore::invoke stc::get $host "-toplevelif-Targets"]]

            #DE17444 To set tostype of ipv4if as the tostype of igmphostconfig,so the settings of tostype on gui will be consistent.
            #DE17522 To avoid setting tostype of ipv6if which has no attribute of tostype.
            set ipv4ifObj [::sth::sthCore::invoke stc::get $igmpHostCfg -usesif-Targets]
            foreach ipv4ifObj $ipv4ifObj {
                if {[regexp "ipv4if" $ipv4ifObj]} { 
                    ::sth::sthCore::invoke stc::config $ipv4ifObj -tostype $userArgsArray(tos_type)
                } 
            }

            set port [::sth::sthCore::invoke stc::get $host "-affiliationport-Targets"]
            lappend igmpPortConfigList [::sth::sthCore::invoke stc::get $port -children-igmpPortConfig]
            incr i
         }

         if {[info exists igmpPortCfgArgs]} {
            foreach igmpPortCfg [lsort -unique $igmpPortConfigList] {
               ::sth::sthCore::invoke stc::config $igmpPortCfg $igmpPortCfgArgs
            }
         }

         ::sth::sthCore::doStcApply
         #set the unsupported paramters with the value of the created device
         set ethif [::sth::sthCore::invoke "stc::get $host -children-ethiiif"]
         set ipif [::sth::sthCore::invoke "stc::get $host -children-Ipv4If"]
         if {$ethif != ""} {
            set userArgsArray(source_mac) [::sth::sthCore::invoke "stc::get $ethif -SourceMac"]
         }
         if {$ipif != ""} {
            if {[llength $ipif] > 1} {
               foreach ipif_top $ipif {
                  set ipif_stacked_if [::sth::sthCore::invoke "stc::get $ipif_top -stackedonendpoint-Targets"]
                  if {![regexp "ethiiif" $ipif_stacked_if]} {
                     set ipif $ipif_top
                  }
               }
            }
            set userArgsArray(intf_ip_addr) [::sth::sthCore::invoke "stc::get $ipif -Address"]
            set userArgsArray(neighbor_intf_ip_addr) [::sth::sthCore::invoke "stc::get $ipif -Gateway"]
         }
         set igmpSessionConfig($igmpHostCfgList) [array get userArgsArray]
                               
         keylset returnKeyedList handle $host
         keylset returnKeyedList handles $igmpHostCfgList
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_config_modify_common {igmpHostCfgList returnKeyedListVarName \
         {level 1}} {
      variable userArgsArray
      variable igmpSessionConfig

      upvar $level $returnKeyedListVarName returnKeyedList

      array unset deviceList

      set retVal [catch {
         ::sth::sthCore::parseInputArgs switches switchValues \
               $userArgsArray(optional_args)

         set vlanOptFound false
         if {[regexp -nocase -- {-vlan.*} $userArgsArray(optional_args)]} {
            set vlanOptFound true
         }

         set vlanCfi [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_cfi default]
         set vlanUserPriority [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_user_priority default]

         set vlanOuterOptFound false
         if {[regexp -nocase -- {(vlan_id_outer)|(vlan_outer)|(qinq)} $userArgsArray(optional_args)]} {
            set vlanOuterOptFound true
         }

         set vlanOuterCfi [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_cfi default]
         set vlanOuterUserPriority [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_user_priority default]

         ::sth::igmp::emulation_igmp_config_getVlanIdList switchValues \
               vlanIdList

         foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::igmp:: \
                  emulation_igmp_config $optArg stcattr]

            if {[string equal -nocase $stcAttr "_none_"]} {
               continue
            }

            set switchValue ""

            switch $optArg {
               "igmp_version" {
                  switch -exact $userArgsArray(igmp_version) {
                     v1 { set switchValue igmp_v1 }
                     v2 { set switchValue igmp_v2 }
                     v3 { set switchValue igmp_v3 }
                     default {
                        return -code error [concat "Error:  Error encountered "\
                              "while configuring IGMP session.  Invalid IGMP "\
                              "version \"$userArgsArray(igmp_version)\".  "\
                              "Should be v1, v2, or v3.  "]
                     }
                  }
               }
               "neighbor_intf_ip_addr" {
                  set switchValue [concat $switchValues($optArg) \
                        "-UsePortDefaultIpv4Gateway false "]
                  continue
               }
               "vlan_outer_cfi" {
                  set vlanOuterCfi $userArgsArray($optArg)
                  continue
               }
               "vlan_outer_user_priority" {
                  set vlanOuterUserPriority $userArgsArray($optArg)
                  continue
               }
               "vlan_id" -
               "vlan_id_step" {
                  if {$vlanOuterOptFound} {
                     continue
                  } else {
                     set switchValue $switchValues($optArg)
                  }
               }
               "intf_ip_addr" -
               "vlan_id_outer" -
               "vlan_id_outer_step" -
               "qinq_incr_mode" -
               "handle" {
                  continue
               }
               default {
                  set switchValue $switchValues($optArg)
               }
            }

            set stcObj [::sth::sthCore::getswitchprop ::sth::igmp:: \
                  emulation_igmp_config $optArg stcobj]

            append originalStcObjLst($stcObj) "-$stcAttr $switchValue "
         }

         if {[info exists userArgsArray(count)] == 0} {
            set userArgsArray(count) [::sth::sthCore::getswitchprop \
                  ::sth::igmp:: emulation_igmp_config \
                  count default]
         }

         set returnHandle ""
         set rethostHandle ""
         set i 0

         foreach igmpHostCfg $igmpHostCfgList {
            array unset stcObjLst
            array set stcObjLst [array get originalStcObjLst]

            set host [::sth::sthCore::invoke stc::get $igmpHostCfg -parent]
            set ipv4ObjHandle [::sth::sthCore::invoke stc::get $host -ipv4If.handle]
            set ethiiIfObjHandle [::sth::sthCore::invoke stc::get $host -ethiiIf.handle]
            set vlanIfObjHandle [::sth::sthCore::invoke stc::get $ipv4ObjHandle -stackedonendpoint-Targets]
            set igmpHostCfgObjHandle [::sth::sthCore::invoke stc::get $host -children-IgmpHostConfig]
            lappend returnHandle $igmpHostCfgObjHandle
            lappend rethostHandle $host

            # Modify IGMP block config of host
            lappend stcObjLst(IgmpHostConfig) "-UsesIf-targets" \
                  [::sth::sthCore::invoke stc::get $host -toplevelif-Targets]
                ::sth::sthCore::invoke stc::config $igmpHostCfgObjHandle $stcObjLst(IgmpHostConfig)

            set ipIfStackedOnEndpointTarget \
                  [::sth::sthCore::invoke stc::get $ipv4ObjHandle -stackedonendpoint-Targets]
            set ethiiIfStackedOnEndpointSources \
                  [::sth::sthCore::invoke stc::get $ethiiIfObjHandle -stackedonendpoint-Sources]
            
            # Set VLAN information
            if {$vlanOptFound} {
               # Create/configure a VLAN interface if host does not already
               # have one
               if {![regexp -nocase {vlanif[0-9a-f]} $vlanIfObjHandle]} {
                  set vlanIfObjHandle [::sth::sthCore::invoke stc::create vlanIf -under $host]
               }

               set ipIfStackedOnEndpointTarget $vlanIfObjHandle
               set ethiiIfStackedOnEndpointSources $vlanIfObjHandle
               set vlanIfStackedOnEndpointTarget $ethiiIfObjHandle

               # Set Outer VLAN information
               if {$vlanOuterOptFound} {
                  set outerVlanIfObjHandle [::sth::sthCore::invoke stc::get $vlanIfObjHandle -stackedOnEndpoint-Targets
                  ]
                  if {![regexp -nocase {vlanif[0-9a-f]} \
                        $outerVlanIfObjHandle]} {
                     set outerVlanIfObjHandle [::sth::sthCore::invoke stc::create vlanIf -under $host [list -stackedonendpoint-Sources $vlanIfObjHandle -stackedonendpoint-Targets $ethiiIfObjHandle]
                     ]
                  }

                  ::sth::sthCore::invoke stc::config $outerVlanIfObjHandle [list "-vlanId" [lindex $vlanIdList [expr ($i*2)+1]] "-cfi" $vlanOuterCfi "-priority" $vlanOuterUserPriority]

                  lappend stcObjLst(VlanIf) \
                        "-vlanId" [lindex $vlanIdList [expr $i*2]]

                  set vlanIfStackedOnEndpointTarget $outerVlanIfObjHandle
                  set ethiiIfStackedOnEndpointSources $outerVlanIfObjHandle
               }

               lappend stcObjLst(VlanIf) \
                     "-stackedonendpoint-Sources" $ipv4ObjHandle \
                     "-stackedonendpoint-Targets" \
                           $vlanIfStackedOnEndpointTarget

               ::sth::sthCore::invoke stc::config $vlanIfObjHandle $stcObjLst(VlanIf)
               set stcObjLst(VlanIf) ""
            }
            
            lappend stcObjLst(Ipv4If) \
                  "-stackedonendpoint-Targets" $ipIfStackedOnEndpointTarget \
                  "-address" [::sth::sthCore::updateIpAddress \
                        4 $userArgsArray(intf_ip_addr) \
                        $userArgsArray(intf_ip_addr_step) $i] \
                  "-gateway" [::sth::sthCore::updateIpAddress \
                        4 $userArgsArray(neighbor_intf_ip_addr) \
                        $userArgsArray(neighbor_intf_ip_addr_step) $i]\
                  "-gatewaystep" $userArgsArray(neighbor_intf_ip_addr_step)
                  
            ::sth::sthCore::invoke stc::config $ipv4ObjHandle $stcObjLst(Ipv4If)
            #DE17444 set tostype of ipv4if to tostype of igmp,so the settings on gui will be consistent.
            ::sth::sthCore::invoke stc::config $ipv4ObjHandle -tostype $userArgsArray(tos_type)

            lappend stcObjLst(EthiiIf) \
                  -stackedonendpoint-Sources $ethiiIfStackedOnEndpointSources \
                  -SourceMac $userArgsArray(source_mac)\
                  -SrcMacStep $userArgsArray(source_mac_step)
            ::sth::sthCore::invoke stc::config $ethiiIfObjHandle $stcObjLst(EthiiIf)

            incr i
            }

         ::sth::sthCore::doStcApply
         
         set igmpSessionConfig($returnHandle) [array get userArgsArray]

         keylset returnKeyedList handle $rethostHandle
         keylset returnKeyedList handles $returnHandle
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_config_delete {returnKeyedListVarName {level 1}} {
      variable userArgsArray
      variable igmpSessionConfig
      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         variable igmpCreatedHosts
         variable hostFilterMode
         variable hostFilterIpAddr
         variable igmpToClacLatencyMapper
         set userArgsArray(handle) [emulation_igmp_config_getIgmpHostCfgList $userArgsArray(handle)]
         
         foreach sessionHandle $userArgsArray(handle) {
            # Record the IGMP host config block's parent handle before
            # deleting the block
            set hostHandle [::sth::sthCore::invoke stc::get $sessionHandle -parent]

            ::sth::sthCore::invoke stc::delete $sessionHandle
            if {[info exists igmpToClacLatencyMapper($sessionHandle)]} {
                  unset  igmpToClacLatencyMapper($sessionHandle)
            }
            # Delete host parent only if created by IGMP commands
            if {[info exists igmpCreatedHosts($hostHandle)]} {
               unset igmpCreatedHosts($hostHandle)
               ::sth::sthCore::invoke stc::delete $hostHandle
            }

            if {[info exists hostFilterMode($hostHandle)]} {
               unset hostFilterMode($hostHandle)
            }
            
             if {[info exists hostFilterIpAddr($hostHandle)]} {
               unset hostFilterIpAddr($hostHandle)
            }

            ::sth::sthCore::doStcApply
         }

         array unset igmpSessionConfig $userArgsArray(handle)
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while deleting IGMP "\
                       "session \"$userArgsArray(handle)\".  \n"\
                       "Returned Error:  $returnedString"] \
               {}
      } else {
         keylset returnKeyedList handle $userArgsArray(handle)
         keylset returnKeyedList handles $userArgsArray(handle)
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

        return $returnKeyedList
   }

   proc emulation_igmp_config_enable_all {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         set igmpHostConfig [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-igmpHostConfig]
         ::sth::sthCore::invoke stc::config $igmpHostConfig [list -Active true]
         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while enabling IGMP "\
                       "session \"$userArgsArray(handle)\".  \n"\
                       "Returned Error:  $returnedString"]
           keylset returnKeyedList status $::sth::sthCore::FAILURE
      } else {
         keylset returnKeyedList handle $userArgsArray(handle)
         keylset returnKeyedList handles $userArgsArray(handle)
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

        return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_config_disable_all {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {![info exists userArgsArray(port_handle)]} {
            set port_list [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-port]
            set host_list ""
            foreach port $port_list {
               set host_list [concat $host_list [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]]
            }
         } else {
            set host_list [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -AffiliationPort-sources]
         }
         foreach host $host_list {
            set igmpHostConfig [::sth::sthCore::invoke stc::get $host -children-igmpHostConfig]
            if {$igmpHostConfig != ""} {
               ::sth::sthCore::invoke stc::config $igmpHostConfig [list -Active false]
            }
            
         }
         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while disabling IGMP " \
                       "session.  \n" \
                       "Returned Error:  $returnedString"]
           keylset returnKeyedList status $::sth::sthCore::FAILURE
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

        return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_group_config_create {returnKeyedListVarName {level 1}} {
      variable userArgsArray
      variable hostFilterMode
      variable hostFilterIpAddr
      variable igmpToClacLatencyMapper
      upvar $level $returnKeyedListVarName returnKeyedList

      array unset deviceList
      set igmpGrpMembership ""

      set retVal [catch {
         if {[info exists userArgsArray(session_handle)] == 0} {
            return -code error [concat "Error:  Unable to create an IGMP " \
                  "group membership.  Missing mandatory argument " \
                  "\"-session_handle\".  "]
         }
         set userArgsArray(session_handle) [emulation_igmp_config_getIgmpHostCfgList $userArgsArray(session_handle)]
         if {[info exists userArgsArray(group_pool_handle)] == 0} {
            return -code error [concat "Error:  Unable to create an IGMP " \
                  "group membership.  Missing mandatory argument " \
                  "\"-group_pool_handle\".  "]
         }
         foreach groupPoolHandle $userArgsArray(group_pool_handle) {
            foreach sessionHandle $userArgsArray(session_handle) {
               set calcLatency $igmpToClacLatencyMapper($sessionHandle)
               set igmpGrpMembership [::sth::sthCore::invoke stc::create "IgmpGroupMembership" -under $sessionHandle [list -SubscribedGroups-targets $groupPoolHandle -CalculateLatency $calcLatency]
               ]
               set host [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $igmpGrpMembership "-parent"] "-parent"]
               if {[info exists userArgsArray(device_group_mapping)] != 0} {
                  ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-DeviceGroupMapping" $userArgsArray(device_group_mapping)]
               }
               set igmpVersion [::sth::sthCore::invoke stc::get $sessionHandle -Version]
               if {[info exists userArgsArray(filter_mode)]} {
                     set filter_mode $userArgsArray(filter_mode)
               } else {
                     set filter_mode $hostFilterMode($host)
               }

               if {[regexp -nocase "IGMP_V3" $igmpVersion] } {
                     # old script
                     if {![info exists userArgsArray(source_filters)] && ![info exists userArgsArray(enable_user_defined_sources)] && \
                     ![info exists userArgsArray(specify_sources_as_list)] && ![info exists userArgsArray(ip_addr_list)] } {
                           #Rxu: support filter_ip_addr
                           ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-userDefinedSources" "TRUE"]
                           set ipv4NetworkBlock [::sth::sthCore::invoke stc::get $igmpGrpMembership -children-Ipv4NetworkBlock]
                           ::sth::sthCore::invoke stc::config $ipv4NetworkBlock [list "-StartIpList" $hostFilterIpAddr($host) ]
                           if {[info exists userArgsArray(source_pool_handle)]} {
                                 ::sth::igmp::emulation_igmp_group_config_srcPool $userArgsArray(source_pool_handle) $igmpGrpMembership
                           }
                        }  else {
                              if {[info exists userArgsArray(source_filters)]} {
                                    # config source filter
                                    if { ( (![info exists userArgsArray(enable_user_defined_sources)] && ![info exists userArgsArray(specify_sources_as_list)] && \
                                           ![info exists userArgsArray(source_pool_handle)]) || ([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 0 && [info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 0)) && ![info exists userArgsArray(ip_addr_list)]} {
                                                 ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-UserDefinedSources" "FALSE"]
                                                 ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "FALSE"]
                                                 ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-subscribedsources-Targets" $userArgsArray(source_filters)]
                                    } else {
                                          return -code error [concat "Error: enable_user_defined_sources, specify_sources_as_list, \
                                          ip_addr_list and source_pool_handle options must be disabled when source_filters is configured"]
                                          }
                              } elseif {[info exists userArgsArray(ip_addr_list)] && [info exists userArgsArray(source_pool_handle)]} {
                                    return -code error [concat "Error: please use ip_addr_list or source_pool_handle to specify source filter"]
                              } elseif {[info exists userArgsArray(ip_addr_list)]} {
                                    if {([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 1) && \
                                        ([info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 1)} {
                                          ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-userDefinedSources" "TRUE"]
                                          ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "TRUE"]
                                          set ipv4NtworkBlock [::sth::sthCore::invoke stc::get  $igmpGrpMembership -children-ipv4Networkblock]
                                          ::sth::sthCore::invoke stc::config $ipv4NtworkBlock [list "-StartIpList" $userArgsArray(ip_addr_list)]
                                    } else {
                                          return -code error [concat "Error: enable_user_defined_sources and specify_sources_as_list options must be enable when ip_addr_list is configured"] 
                                          }
                              } elseif {[info exists userArgsArray(source_pool_handle)]} {
                                    if {([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 1) && \
                                        ([info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 0 )} {
                                              ::sth::igmp::emulation_igmp_group_config_srcPool $userArgsArray(source_pool_handle) $igmpGrpMembership
                                              ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "FALSE"]
                                    } else {
                                          return -code error [concat "Error: enable_user_defined_sources options must be enabled and specify_sources_as_list must be disabled when source_pool_handle is configured"]
                                          }
                              } elseif {([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 0) && \
                                        ([info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 0) } {
                                              if {[regexp -nocase {exclude} $filter_mode]} {
                                                    ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-userDefinedSources" "FALSE"]
                                                    ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "FALSE"]
                                                } else {
                                                      return -code error [concat "Error: please specify source filter when filter_mode is INCLUDE"] 
                                                }
                              } else {
                                    return -code error [concat "Error: Missing arguments ,please specify source filter"] 
                              }
                        }
               }
                     ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-filterMode" $filter_mode ]
            }
         }
         ::sth::sthCore::doStcApply
      } returnedString]
      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $igmpGrpMembership
      }
      return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_group_config_modify {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set igmpGrpMembership ""

      set retVal [catch {
         if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to modify the IGMP " \
                  "group member.  Missing mandatory argument " \
                  "\"-handle\".  "]
         }

         set igmpGrpMembership $userArgsArray(handle)

         variable hostFilterMode
         variable hostFilterIpAddr

         if {[info exists userArgsArray(group_pool_handle)]} {
            set igmpHostCfgs ""
            # Clear all group memberships first
            foreach handle $userArgsArray(handle) {
               # Remember the IGMP host config parent objects
               lappend igmpHostCfgs [::sth::sthCore::invoke stc::get $handle -parent]
 
            }

            foreach igmpHostCfg $igmpHostCfgs {
               foreach handle $userArgsArray(group_pool_handle) {
                  foreach sessionHandle $userArgsArray(session_handle) {
  
                    if {[string length [string trim $igmpGrpMembership]] == 0} {
                       set igmpGrpMembership [::sth::sthCore::invoke stc::create "IgmpGroupMembership" -under $igmpHostCfg]
                    }
                    set host [::sth::sthCore::invoke stc::get $igmpHostCfg "-parent"]
                    ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-SubscribedGroups-targets" $handle "-filterMode" $hostFilterMode($host) "-UserDefinedSources" "TRUE" ]
                    
                    if {[info exists userArgsArray(device_group_mapping)] != 0} {
                        ::sth::sthCore::invoke stc::config $igmpGrpMembership -DeviceGroupMapping $userArgsArray(device_group_mapping)
                    }
                    
                    #Rxu: support filter_ip_addr
                    if {[info exists userArgsArray(filter_mode)]} {
                          set filter_mode $userArgsArray(filter_mode)
                    } else {
                          set filter_mode [::sth::sthCore::invoke stc::get $igmpGrpMembership -FilterMode]
                    }

                    set igmpVersion [::sth::sthCore::invoke stc::get $igmpHostCfg -Version]
                    if {[regexp -nocase "IGMP_V3" $igmpVersion]} {
                          if {![info exists userArgsArray(source_filters)] && ![info exists userArgsArray(enable_user_defined_sources)] && \
                          ![info exists userArgsArray(specify_sources_as_list)] && ![info exists userArgsArray(ip_addr_list)] } {
                                #for old scripts
                                set ipv4NetworkBlock [::sth::sthCore::invoke stc::get $igmpGrpMembership -children-Ipv4NetworkBlock]
                                ::sth::sthCore::invoke stc::config $ipv4NetworkBlock [list "-StartIpList" $hostFilterIpAddr($host) ]
                                if {[info exists userArgsArray(source_pool_handle)]} {
                                      ::sth::igmp::emulation_igmp_group_config_srcPool \
                                      $userArgsArray(source_pool_handle) \
                                      $igmpGrpMembership
                                      }
                              }  else {
                                    if {[info exists userArgsArray(source_filters)]} {
                                          # config source filter
                                          if { ( (![info exists userArgsArray(enable_user_defined_sources)] && ![info exists userArgsArray(specify_sources_as_list)] && \
                                           ![info exists userArgsArray(source_pool_handle)]) || ([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 0 && \
                                           [info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 0)) && ![info exists userArgsArray(ip_addr_list)]} {
                                                 ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-UserDefinedSources" "FALSE"]
                                                 ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "FALSE"]
                                                 ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-subscribedsources-Targets" $userArgsArray(source_filters)]
                                          } else {
                                                return -code error [concat "Error: enable_user_defined_sources, specify_sources_as_list, \
                                                ip_addr_list and source_pool_handle options must be disabled when source_filters is configured"]
                                          }
                                    } elseif {[info exists userArgsArray(ip_addr_list)] && [info exists userArgsArray(source_pool_handle)]} {
                                          return -code error [concat "Error: please use ip_addr_list or source_pool_handle to specify source filter"]
                                    } elseif {[info exists userArgsArray(ip_addr_list)]} {
                                          if {([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 1) && \
                                          ([info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 1)} {
                                                ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-userDefinedSources" "TRUE"]
                                                ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "TRUE"]
                                                set ipv4NtworkBlock [::sth::sthCore::invoke stc::get  $igmpGrpMembership -children-ipv4Networkblock]
                                                ::sth::sthCore::invoke stc::config $ipv4NtworkBlock [list "-StartIpList" $userArgsArray(ip_addr_list)]
                                          } else {
                                                return -code error [concat "Error: enable_user_defined_sources and specify_sources_as_list options must be enable when ip_addr_list is configured"] 
                                          }
                                    } elseif {[info exists userArgsArray(source_pool_handle)]} {
                                          if {([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 1) && \
                                             ([info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 0 )} {
                                                ::sth::igmp::emulation_igmp_group_config_srcPool $userArgsArray(source_pool_handle) $igmpGrpMembership
                                                ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "FALSE"]
                                          } else {
                                                return -code error [concat "Error: enable_user_defined_sources options must be enabled and specify_sources_as_list must be disabled when source_pool_handle is configured"]
                                          }
                                    } elseif {([info exists userArgsArray(enable_user_defined_sources)] && $userArgsArray(enable_user_defined_sources) == 0) && \
                                            ([info exists userArgsArray(specify_sources_as_list)] && $userArgsArray(specify_sources_as_list) == 0) } {
                                                  if {[regexp -nocase {exclude} $filter_mode]} {
                                                        ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-userDefinedSources" "FALSE"]
                                                        ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-IsSourceList" "FALSE"]
                                                } else {
                                                      return -code error [concat "Error: please specify source filter when filter_mode is INCLUDE"] 
                                                }
                                    } else {
                                          return -code error [concat "Error: Missing arguments ,please specify source filter"] 
                                    }
                              }
                        }
                        # US38642 [CR23000][P1]Not able to modify filter_mode in emulation_igmp_group_config
                        ::sth::sthCore::invoke stc::config $igmpGrpMembership [list "-filterMode" $filter_mode ]
                    }
                }
            }
        }
         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $igmpGrpMembership
      }

      return -code $retVal $returnKeyedList
   }
 
   proc emulation_igmp_group_config_delete {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to delete the " \
                  "specified pool from the IGMP group member.  Missing " \
                  "mandatory argument \"-handle\".  "]
         }
         if {[info exists userArgsArray(group_pool_handle)]} {
            foreach membership [::sth::sthCore::invoke stc::get $userArgsArray(group_pool_handle) -subscribedgroups-Sources] {
               foreach grpMembership $userArgsArray(handle) {
                  if {[lsearch -exact $grpMembership $membership] == -1} {
                     puts [concat "Warning:  Unable to delete the " \
                           "group pool \"$userArgsArray(group_pool_handle)\" " \
                           "from the IGMP group membership " \
                           "$userArgsArray(handle)\".  The group pool is not " \
                           "part of the membership.  "]
                  }
               }
            }
         }
         foreach grpMembership $userArgsArray(handle) {
            ::sth::sthCore::invoke stc::delete $grpMembership
         }

         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_group_config_clear_all {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to remove all group " \
                  "pools from the IGMP group member.  Missing mandatory " \
                  "argument \"-handle\".  "]
         }

         foreach grpConfig $userArgsArray(handle) {
            set igmpHostConfig [::sth::sthCore::invoke stc::get $grpConfig -parent]

            foreach grpMembership [::sth::sthCore::invoke stc::get $igmpHostConfig -children-IgmpGroupMembership] {
               ::sth::sthCore::invoke stc::delete $grpMembership
            }
         }

         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_igmp_config_create_resultDataset {configClass resultClass propertyIdArray {level 1}} {
      set resultDataSet ""

      set retVal [catch {
         set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
         ::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list "-ResultRootList" $::sth::GBLHNDMAP(project) "-ConfigClassId" $configClass "-ResultClassId" $resultClass "-PropertyIdArray" $propertyIdArray]
      } returnedString]

      return -code $retVal $resultDataSet
   }

   proc emulation_igmp_group_config_srcPool {srcPoolHandleList igmpGrpMembershipHandle} {
      #Modified the code to allow for multiple sources to be added at once.
      ::sth::sthCore::invoke stc::config $igmpGrpMembershipHandle [list "-UserDefinedSources" "TRUE"]
      set srcIpv4NetworkBlock [::sth::sthCore::invoke stc::get $igmpGrpMembershipHandle -children-Ipv4NetworkBlock]

      # The following code will build a list of source IP addresses for the IPv4NetworkBlock object.
      set ipList ""
      foreach srcPoolHandle $srcPoolHandleList {

         ::sth::multicast_group::emulation_multicast_group_getSrcPool $srcPoolHandle srcPoolInfo

         set ipNetworkBlkArgs ""
         foreach {s v} $srcPoolInfo(optional_args) {
            lappend ipNetworkBlkArgs \
               "-[::sth::sthCore::getswitchprop \
                     ::sth::multicast_group:: \
                     emulation_multicast_source_config \
                     [string trimleft $s "-"] \
                     stcattr]" \
            $v
         }

         ::sth::sthCore::invoke stc::config $srcIpv4NetworkBlock $ipNetworkBlkArgs
         set ipAddr [::sth::sthCore::invoke stc::get $srcIpv4NetworkBlock -startIpList]
         set stepValue [::sth::sthCore::invoke stc::get $srcIpv4NetworkBlock -addrIncrement]

         # Don't add duplicate addresses.
         if { [lsearch -exact $ipList $ipAddr] == -1 } {
            lappend ipList $ipAddr
         }

         for {set i 1} {$i < [::sth::sthCore::invoke stc::get $srcIpv4NetworkBlock -networkCount]} {incr i} {
            set nextIpAddr [::sth::sthCore::updateIpAddress 4 $ipAddr $stepValue $i]
            # Don't add duplicate addresses.
            if { [lsearch -exact $ipList $nextIpAddr] == -1 } {
               lappend ipList $nextIpAddr
            }
         }
      }
      # The "startIpList" is actually a list, so we need to configure it that way.
      if {![regexp "channel" $igmpGrpMembershipHandle]} {
         ::sth::sthCore::invoke stc::config $igmpGrpMembershipHandle [list -IsSourceList TRUE]
      }

      ::sth::sthCore::invoke stc::config $srcIpv4NetworkBlock [list -startIpList $ipList]
   }

   proc emulation_igmp_config_getVlanIdList {switchValuesVarName vlanIdListVarName {level 1}} {
      variable userArgsArray

      upvar $level $vlanIdListVarName vlanIdList
      upvar $level $switchValuesVarName switchValues

      set retVal [catch {
         set vlanIdList ""

         set vlanOptFound [regexp -nocase -- {-vlan.*} \
               $userArgsArray(optional_args)]

         set qinqOptFound [regexp -nocase -- {(vlan_id_outer)|(vlan_outer)|(qinq)} $userArgsArray(optional_args)]

         if {!$vlanOptFound && !$qinqOptFound} {
            return
         }

         set vlanCount [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config count default]
         set vlanId [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id default]
         set vlanIdStep [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_step default]
         set vlanIdCount [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_count default]
         set vlanIdMode [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_mode default]
         set vlanIdOuter [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_outer default]
         set vlanIdOuterStep [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_outer_step default]
         set vlanIdOuterCount [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_outer_count default]
         set vlanIdOuterMode [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config vlan_id_outer_mode default]
         set qinqIncrMode [::sth::sthCore::getswitchprop ::sth::igmp:: \
               emulation_igmp_config qinq_incr_mode default]

         if {[info exists switchValues(vlan_id_mode)]} {
            set vlanIdMode $switchValues(vlan_id_mode)
         }
         if {[info exists switchValues(vlan_id_outer_mode)]} {
            set vlanIdOuterMode $switchValues(vlan_id_outer_mode)
         }
         if {[info exists switchValues(qinq_incr_mode)]} {
            set qinqIncrMode $switchValues(qinq_incr_mode)
         }

         foreach optArg [array names switchValues] {
            switch $optArg {
               "count" {
                  set vlanCount $switchValues($optArg)
               }
               "vlan_id" {
                  set vlanId $switchValues($optArg)
               }
               "vlan_id_step" {
                  switch -exact -- [string tolower $vlanIdMode] {
                     "fixed" {
                        set vlanIdStep 0
                     }
                     "increment" {
                        set vlanIdStep $switchValues($optArg)
                     }
                     default {
                        return -code error [concat "Error:  Invalid VLAN ID " \
                              "mode \"$optArg\".  Should be \"fixed\" or " \
                              "\"increment\".  "]
                     }
                  }
               }
               "vlan_id_count" {
                  set vlanIdCount $switchValues($optArg)
               }
               "vlan_id_outer" {
                  set vlanIdOuter $switchValues($optArg)
               }
               "vlan_id_outer_step" {
                  switch -exact -- [string tolower $vlanIdOuterMode] {
                     "fixed" {
                        set vlanIdOuterStep 0
                     }
                     "increment" {
                        set vlanIdOuterStep $switchValues($optArg)
                     }
                     default {
                        return -code error [concat "Error:  Invalid outer " \
                              "VLAN ID mode \"$optArg\".  Should be " \
                              "\"fixed\" or \"increment\".  "]
                     }
                  }
               }
               "vlan_id_outer_count" {
                  set vlanIdOuterCount $switchValues($optArg)
               }
            }
         }

         switch -- $qinqIncrMode {
            "inner" {
               if {[info exists switchValues(vlan_id_outer_count)] == 0} {
                  set vlanIdOuterCount $vlanIdCount
               }

               for {set n 0} {$n < $vlanCount} {} {
                  set outerVlanId $vlanIdOuter

                  for {set o 0} {($n < $vlanCount) && \
                        ($o < $vlanIdOuterCount)} {incr o} {

                     set innerVlanId $vlanId

                     for {set i 0} {($n < $vlanCount) && \
                           ($i < $vlanIdCount)} {incr i} {
                        lappend vlanIdList $innerVlanId $outerVlanId

                        incr n

                        incr innerVlanId $vlanIdStep
                     }

                     incr outerVlanId $vlanIdOuterStep
                  }
               }
            }
            "outer" {
               if {[info exists switchValues(vlan_id_count)] == 0} {
                  set vlanIdCount $vlanIdOuterCount
               }

               for {set n 0} {$n < $vlanCount} {} {
                  set innerVlanId $vlanId

                  for {set i 0} {($n < $vlanCount) && \
                        ($i < $vlanIdOuterCount)} {incr i} {
                     set outerVlanId $vlanIdOuter

                     for {set o 0} {($n < $vlanCount) && \
                           ($o < $vlanIdOuterCount)} {incr o} {
                        lappend vlanIdList $innerVlanId $outerVlanId

                        incr n

                        incr outerVlanId $vlanIdStep
                     }

                     incr innerVlanId $vlanIdOuterStep
                  }
               }
            }
            "both" {
               set i $vlanId
               set iNum 0
               set o $vlanIdOuter
               set oNum 0

               for {set n 0} {$n < $vlanCount} {incr n} {
                  lappend vlanIdList $i $o

                  incr i $vlanIdStep
                  incr iNum
                  if {!($iNum < $vlanIdCount)} {
                     set i $vlanId
                     set iNum 0
                  }

                  incr o $vlanIdOuterStep
                  incr oNum
                  if {!($oNum < $vlanIdOuterCount)} {
                     set o $vlanIdOuter
                     set oNum 0
                  }
               }
            }
            default {
               return -code error [concat "Error:  Invalid Q-in-Q increment " \
                     "mode \"$qinqIncrMode\".  Should be \"inner\", " \
                     "\"outer\", or \"both\".  "]
            }
         }
      } returnedString]

      if {($retVal != 0) && ($retVal != 2)} {
         return -code $retVal $returnedString
      } else {
         return $vlanIdList
      }
   }

   proc emulation_igmp_config_getHostList {hostListVarName {level 1}} {
      variable userArgsArray

      upvar $level $hostListVarName hostList

      set retVal [catch {
         ::sth::sthCore::parseInputArgs switches switchValues \
               $userArgsArray(optional_args)

         if {[info exists userArgsArray(count)] == 0} {
            set userArgsArray(count) [::sth::sthCore::getswitchprop \
                  ::sth::igmp:: emulation_igmp_config \
                  count default]
         }

         set deviceCount $userArgsArray(count)
         set createCount 1

         if {[regexp -nocase -- {(vlan_id_outer)|(vlan_outer)|(qinq)} $userArgsArray(optional_args)]} {
            set deviceCount 1
            set createCount $userArgsArray(count)
         }

         array set deviceList [::sth::sthCore::invoke stc::perform deviceCreate "-parentList" $::sth::GBLHNDMAP(project) "-ifStack" "Ipv4If EthIIIf" "-ifCount" "1 1" "-port" $userArgsArray(port_handle) "-deviceType" "Host" "-deviceCount" $deviceCount "-createCount" $createCount]
         set hostList $deviceList(-ReturnList)

         # Track the newly created host(s)
         variable igmpCreatedHosts

         foreach hostHandle $hostList {
            set igmpCreatedHosts($hostHandle) {}
            # Set the IPv4 address stepmask for full address increment
            ::sth::sthCore::invoke stc::config [::sth::sthCore::invoke stc::get $hostHandle "-topLevelIf-Targets"] [list "-addrStepMask" 255.255.255.255]
         }
      } returnedString]

      if {$retVal} {
         return -code $retVal $returnedString
      } else {
         return $hostList
      }
   }
   
   
   # the old version of igmp will have the igmphostconfig handle as the input list,
   # thinking of hlapiGen needs the host handle to do the boud streamblock, change the handle of returned value to host handle,
   # so this function needs to be called in modify and delete mode
   
   proc emulation_igmp_config_getIgmpHostCfgList {inputHdlList} {
      variable userArgsArray
      set igmpHostCfgList ""
      
      set retVal [catch {
         foreach inputHdl $inputHdlList {
            if {[string match "host*" $inputHdl] || [string match "router*" $inputHdl] || [string match "emulateddevice*" $inputHdl]} {
               set igmpHostCfg [::sth::sthCore::invoke "stc::get $inputHdl -children-igmpHostConfig"]
                
                if { $igmpHostCfg ne "" } {
                    lappend igmpHostCfgList $igmpHostCfg
                }
            } else {
               #current input handle is igmphostconfig handle, nothing needs to do
               lappend igmpHostCfgList $inputHdl
            }
         }
      } returnedString]
   
      if {$retVal} {
         return -code $retVal $returnedString
      } else {
         return $igmpHostCfgList
      }
   }
}
