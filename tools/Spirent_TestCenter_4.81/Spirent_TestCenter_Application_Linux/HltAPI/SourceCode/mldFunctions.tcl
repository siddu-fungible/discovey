# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::Mld:: {

   # Keep track of host blocks created by MLD commands.  This is to prevent
   # hosts created by other protocols from being manipulated unnecessarily.
   # For example, host created by PPPoX command being deleted by MLD command.
   array unset mldCreatedHosts
   variable subscription_state 0

   # Spirent TestCenter configures the source filter mode in the MLD group
   # membership object.  HLTAPI configures the filter mode through the
   # MLD session config create/modify commands which do not modify the MLD
   # group membership object.  Therefore, the filter mode must be recorded
   # here when the MLD session is created/modified, where the HLTAPI group
   # create/modify config commands can retrieve them.
   array unset hostFilterMode
   array unset hostFilterIpAddr

   proc ::Mld::emulation_mld_config_create {returnKeyedListVarName} {
      variable ::Mld::userArgsArray

      upvar 1 $returnKeyedListVarName returnKeyedList

      array unset deviceList

      set retVal [catch {
         if {([info exists ::Mld::userArgsArray(port_handle)] == 0) && \
               ([info exists ::Mld::userArgsArray(handle)] == 0)} {
            return -code error [concat "Error: Unable to create an MLD " \
                  "session.  Missing argument \"-port_handle\" or " \
                  "\"-handle\".  "]
         }

         if {[info exists ::Mld::userArgsArray(handle)]} {
            set hostList $::Mld::userArgsArray(handle)
         } else {
            set hostList [::Mld::emulation_mld_config_getHostList \
                  hostList]
         }

         # Convert DHCP block config handle to parent host handle
         set newHostList ""
         foreach host $hostList {
            set type [::sth::sthCore::invoke stc::get $host -name]
            if {[lindex $type 0] == "Dhcpv6BlockConfig"} {
               set host [::sth::sthCore::invoke stc::get $host -parent]
               # Grab other associated Dhcp hosts (for QINQ)
               if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($host)]} {
                  set host $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($host)
               }
            }
            set newHostList [concat $newHostList $host]
         }

         # Special case where the filter mode and filter ip addr are processed later in the MLD
         # group config command.  Record the setting in
         # ::Mld::hostFilterMode and ::Mld::hostFilterIpAddr for later retrieval.
         variable hostFilterMode
         variable hostFilterIpAddr

         if {![regexp -nocase -- {-filter_mode} \
               $::Mld::userArgsArray(optional_args)]} {
            set filterMode [::sth::sthCore::getswitchprop \
                  ::Mld:: emulation_mld_config filter_mode default]
         } else {
            set filterMode $::Mld::userArgsArray(filter_mode)
         }


         if {![regexp -nocase -- {-filter_ip_addr}  $::Mld::userArgsArray(optional_args)]} {
            set filterIpAddr [::sth::sthCore::getswitchprop  ::Mld:: emulation_mld_config filter_ip_addr default]
         } else {
            set filterIpAddr $::Mld::userArgsArray(filter_ip_addr)
         }

         set hostList $newHostList
         set mldHostCfgList ""

         foreach host $hostList {
            set hostFilterMode($host) $filterMode
            set hostFilterIpAddr($host) $filterIpAddr
            set ipv6Handles [::sth::sthCore::invoke stc::get $host -children-Ipv6If]
            set mldConfigDefaults [list -UsesIf-targets $ipv6Handles -Version MLD_V1 -UnsolicitedReportInterval 100 -robustnessVariable 2]
            # Add MLD block config to each host
            lappend mldHostCfgList \
                  [::sth::sthCore::invoke stc::create mldHostConfig -under $host $mldConfigDefaults]

            if {![info exists ::Mld::userArgsArray(handle)]} {
               # Link local IPv6 interface
               ::sth::sthCore::invoke stc::perform IfStackAttach -IfStack "Ipv6If" -IfCount 1 -DeviceList $host -AttachToIf [::sth::sthCore::invoke stc::get $host -children-ethIIIf]
               set ipv6LinkLocalHandle [::sth::sthCore::invoke stc::get $host -Ipv6If.2.Handle]
               set linkLocalPrefixLen [::sth::sthCore::getswitchprop ::Mld:: \
                  emulation_mld_config link_local_intf_prefix_len default]
               set linkLocalAddrStep [::sth::sthCore::getswitchprop ::Mld:: \
                  emulation_mld_config link_local_intf_ip_addr_step default]
               set ipv6LinkLocalDefaults [list -Address FE80::0 -PrefixLength $linkLocalPrefixLen \
                     -addrStepMask FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF \
                     -addrStep $linkLocalAddrStep]
               ::sth::sthCore::invoke stc::config $ipv6LinkLocalHandle $ipv6LinkLocalDefaults
               ::sth::sthCore::invoke stc::config $ipv6LinkLocalHandle -AllocateEui64LinkLocalAddress true
            }
         }

         if {[info exists ::Mld::userArgsArray(handle)]} {
            ::Mld::emulation_mld_config_pppox $hostList \
                  $returnKeyedListVarName
         } else {
            ::Mld::emulation_mld_config_modify_common \
                  $mldHostCfgList $returnKeyedListVarName
         }
      }]

      return $returnKeyedList
   }

   proc ::Mld::emulation_mld_config_modify {returnKeyedListVarName} {
      variable ::Mld::userArgsArray

      upvar 1 $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists ::Mld::userArgsArray(handle)] == 0} {
            return -code error [concat "Error: Unable to modify MLD " \
                  "session.  Missing mandatory argument \"-handle\".  "]
         }

         if {[llength ::Mld::userArgsArray(handle)] > 1} {
            return -code error [concat "Error: Unable to modify "\
               "multiple MLD sessions at a time.  "]
         }

         set userArgsArray(handle) [emulation_mld_config_getMldHostCfgList $userArgsArray(handle)]

         ::Mld::emulation_mld_config_modify_common \
               $::Mld::userArgsArray(handle) \
               $returnKeyedListVarName
      } returnedString]

      if {$retVal} {
         ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return -code $retVal $returnKeyedList
   }

   proc ::Mld::emulation_mld_config_pppox {hostList returnKeyedListVarName} {
      variable ::Mld::userArgsArray

      upvar 1 $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         set mldHostCfgArgs ""

         foreach {arg val} $::Mld::userArgsArray(optional_args) {
            set arg [string tolower [string trim [string trimleft \
                  $arg "-"]]]
            switch -exact -- $arg {
               "mld_version" {
                  switch -exact $val {
                     v1 { set val mld_v1 }
                     v2 { set val mld_v2 }
                     default {
                        return -code error [concat "Error:  Error encountered "
                              "while configuring MLD session.  Invalid MLD "
                              "version \"$::Mld::userArgsArray(mld_version)\".  "
                              "Should be v1 or v2.  "]
                     }
                  }
                  set stcArg [::sth::sthCore::getswitchprop \
                        ::Mld:: \
                        emulation_mld_config $arg stcattr]
                  lappend mldHostCfgArgs "-$stcArg" $val
               }
               "robustness" {
                  set stcArg [::sth::sthCore::getswitchprop \
                        ::Mld:: \
                        emulation_mld_config $arg stcattr]
                  lappend mldHostCfgArgs "-$stcArg" $val
               }
               "msg_interval" {
                  set stcArg [::sth::sthCore::getswitchprop \
                        ::Mld:: \
                        emulation_mld_config $arg stcattr]
                  lappend mldPortCfgArgs "-$stcArg" $val
               }
            }
         }

         set mldPortConfigList ""
         set igmpPortConfigList ""
         set mldHostCfgList ""
         set i 0
         foreach host $hostList {
            #when enable the mld protocol on this device and there is no ipv6 interface need to create it.
            set ethif [::sth::sthCore::invoke "stc::get $host -children-ethiiif"]
            set ipv6if [::sth::sthCore::invoke "stc::get $host -children-Ipv6If"]
            if {$ipv6if == ""} {
               set ipv6if [::sth::sthCore::invoke stc::create ipv6if -under $host]
               set ipv6iflocal [::sth::sthCore::invoke stc::create ipv6if \
                                 -under $host\
                                 -Address FE80::0 \
                                 -PrefixLength $::Mld::userArgsArray(link_local_intf_prefix_len)\
                                 -addrStepMask FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF \
                                 -addrStep $::Mld::userArgsArray(link_local_intf_ip_addr_step)]
                ::sth::sthCore::invoke stc::config $ipv6iflocal -AllocateEui64LinkLocalAddress true
               set ipIfStackedOnEndpointTarget $ethif
               set vlanif [::sth::sthCore::invoke stc::get $host -children-vlanif]
               if {$vlanif != ""} {
                  set ipIfStackedOnEndpointTarget [lindex $vlanif 0]
               }
               ::sth::sthCore::invoke stc::config $ipv6if -stackedonendpoint-Targets $ipIfStackedOnEndpointTarget
               ::sth::sthCore::invoke stc::config $ipv6iflocal -stackedonendpoint-Targets $ipIfStackedOnEndpointTarget
               set toplevelifTargets [stc::get $host -toplevelif-Targets]
               lappend toplevelifTargets $ipv6if
               lappend toplevelifTargets $ipv6iflocal
               ::sth::sthCore::invoke stc::config $host \
                        -toplevelif-Targets $toplevelifTargets
               #config ipv6if
               set stcObjLst(Ipv6If) ""
               lappend stcObjLst(Ipv6If) \
                  "-address" [::sth::sthCore::updateIpAddress \
                        6 $::Mld::userArgsArray(intf_ip_addr) \
                        $::Mld::userArgsArray(intf_ip_addr_step) $i] \
                  "-gateway" [::sth::sthCore::updateIpAddress \
                        6 $::Mld::userArgsArray(neighbor_intf_ip_addr) \
                        $::Mld::userArgsArray(neighbor_intf_ip_addr_step) $i]
               ::sth::sthCore::invoke stc::config $ipv6if $stcObjLst(Ipv6If)

               # config link local ipv6
               array set optionalValueArray  $::Mld::userArgsArray(optional_args)
               if {[info exists optionalValueArray(-link_local_intf_ip_addr)]} {
                  set link_local_intf_ip_addr [::sth::sthCore::updateIpAddress 6 \
                     $::Mld::userArgsArray(link_local_intf_ip_addr) \
                     $::Mld::userArgsArray(link_local_intf_ip_addr_step) $i]
                  append stcObjLst(Ipv6LinkLocalIf) " -Address $link_local_intf_ip_addr \
                                                      -AddrStep $::Mld::userArgsArray(link_local_intf_ip_addr_step)"
               }
               if {[info exists optionalValueArray(-link_local_intf_prefix_len)]} {
                  append stcObjLst(Ipv6LinkLocalIf) " -PrefixLength $::Mld::userArgsArray(link_local_intf_prefix_len)"
               }
               if {[info exists stcObjLst(Ipv6LinkLocalIf)]} {
                  ::sth::sthCore::invoke stc::config $ipv6iflocal $stcObjLst(Ipv6LinkLocalIf)
               }
               ::sth::sthCore::invoke stc::config $ipv6if $stcObjLst(Ipv6If)
            }
            set mldHostCfg [::sth::sthCore::invoke stc::get $host -children-MldHostConfig]
            if {[string length $mldHostCfgArgs] > 0} {
               ::sth::sthCore::invoke stc::config $mldHostCfg $mldHostCfgArgs
            }
            lappend mldHostCfgList $mldHostCfg
            # Modify MLD host block config to use the information provided by
            # the PPPoX object
            ::sth::sthCore::invoke stc::config $mldHostCfg [list "-usesIf-targets" [::sth::sthCore::invoke stc::get $host "-toplevelif-Targets"]]

            set port [::sth::sthCore::invoke stc::get $host "-affiliationport-Targets"]
            lappend mldPortConfigList [::sth::sthCore::invoke stc::get $port -children-mldPortConfig]
            lappend igmpPortConfigList [::sth::sthCore::invoke stc::get $port -children-igmpPortConfig]
            incr i
         }

         if {[info exists mldPortCfgArgs]} {
            foreach mldPortCfg [lsort -unique $mldPortConfigList] {
               ::sth::sthCore::invoke stc::config $mldPortCfg $mldPortCfgArgs
            }
            foreach igmpPortCfg [lsort -unique $igmpPortConfigList] {
               ::sth::sthCore::invoke stc::config $igmpPortCfg $mldPortCfgArgs
            }
         }
         #move the result subscriber to the emulation_mld_info, since if the result is subscibed, and then enable the iptv on it, it will get the demon died.
         #so in the hltapi script, need to make sure the emulation_iptv_config should not be called after the emulation_mld_info
         #if {$::Mld::subscription_state == 0} {
         ## Create an MLD port dataset
         #set portResultDataSet \
         #      [::Mld::emulation_mld_config_create_resultDataset \
         #            "MldPortConfig" \
         #            "MldPortResults" \
         #            [list \
         #                  "multicastportresults.txgroupandsourcespecificquerycount" \
         #                  "multicastportresults.rxgroupandsourcespecificquerycount" \
         #                  "multicastportresults.rxv1querycount" \
         #                  "multicastportresults.txv1reportcount" \
         #                  "multicastportresults.rxv1reportcount" \
         #                  "multicastportresults.rxv2querycount" \
         #                  "multicastportresults.txv2reportcount" \
         #                  "multicastportresults.rxv2reportcount" \
         #                  "multicastportresults.rxunknowntypecount" \
         #                  "mldportresults.rxmldchecksumerrorcount" \
         #                  "mldportresults.rxmldlengtherrorcount"] \
         #      ]
         ## Create an MLD group membership dataset
         #set mldGroupMembershipResultDataSet \
         #      [::Mld::emulation_mld_config_create_resultDataset \
         #            "MldGroupMembership" \
         #            "MldGroupMembershipResults" \
         #            [list "mldgroupmembershipresults.hostaddr" \
         #                  "mldgroupmembershipresults.groupaddr" \
         #                  "multicastgroupmembershipresults.state" \
         #                  "multicastgroupmembershipresults.joinlatency" \
         #                  "multicastgroupmembershipresults.leavelatency"] \
         #      ]
         #
         #set mldResultsDataSet \
         #      [::Mld::emulation_mld_config_create_resultDataset \
         #            "MldHostConfig" \
         #            "MldHostResults" \
         #            [list "mldhostresults.minjoinlatency" \
         #                  "mldhostresults.maxjoinlatency" \
         #                  "mldhostresults.avgjoinlatency" \
         #                  "mldhostresults.minleavelatency" \
         #                  "mldhostresults.maxleavelatency" \
         #                  "mldhostresults.avgleavelatency"] \
         #      ]
         #
         #::sth::sthCore::doStcApply
         #
         ## Subscribe to the datasets
         ##::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $portResultDataSet
         ##::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $mldGroupMembershipResultDataSet
         ##::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $mldResultsDataSet
         #set ::Mld::subscription_state 1
         #sleep 3
         #}

         keylset returnKeyedList handle $mldHostCfgList
         keylset returnKeyedList handles $mldHostCfgList
      } returnedString]

      if {$retVal} {
         ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }
      return -code $retVal $returnKeyedList
   }

   proc ::Mld::emulation_mld_config_modify_common {mldHostCfgList returnKeyedListVarName} {
      variable ::Mld::userArgsArray

      upvar 1 $returnKeyedListVarName returnKeyedList

      array unset deviceList

      set retVal [catch {
         # Parse for mandatory arguments given by the user.
         ::sth::sthCore::parseInputArgs switches switchValues \
               $::Mld::userArgsArray(mandatory_args)

         foreach mandArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::Mld:: \
                  emulation_mld_config $mandArg stcattr]

            set switchValue ""
            set switchValue $switchValues($mandArg)

            set stcObj [::sth::sthCore::getswitchprop ::Mld:: \
                 emulation_mld_config $mandArg stcobj]
            append stcObjLst($stcObj) "-$stcAttr $switchValue "
         }

         # Parse for optional arguments given by the user.
         ::sth::sthCore::parseInputArgs switches switchValues \
               $::Mld::userArgsArray(optional_args)

         set vlanOptFound false
         if {[regexp -nocase -- {-vlan.*} $::Mld::userArgsArray(optional_args)]} {
            set vlanOptFound true
         }

         set vlanCfi [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_cfi default]
         set vlanUserPriority [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_user_priority default]

         set vlanOuterOptFound false
         if {[regexp -nocase -- {(vlan_id_outer)|(vlan_outer)|(qinq)} \
               $::Mld::userArgsArray(optional_args)]} {
            set vlanOuterOptFound true
         }

         set vlanOuterCfi [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_cfi default]
         set vlanOuterUserPriority [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_user_priority default]

         ::Mld::emulation_mld_config_getVlanIdList switchValues \
               vlanIdList
         foreach optArg $switches {
            set linkLocalOptFound false
            set stcAttr [::sth::sthCore::getswitchprop ::Mld:: \
                  emulation_mld_config $optArg stcattr]

            if {[string equal -nocase $stcAttr "_none_"]} {
               continue
            }

            set switchValue ""

            switch $optArg {
               "mld_version" {
                  switch -exact $::Mld::userArgsArray(mld_version) {
                     v1 { set switchValue mld_v1 }
                     v2 { set switchValue mld_v2 }
                     default {
                        return -code error [concat "Error:  Error encountered "
                              "while configuring MLD session.  Invalid MLD "
                              "version \"$::Mld::userArgsArray(mld_version)\".  "
                              "Should be v1 or v2.  "]
                     }
                  }
               }
               "neighbor_intf_ip_addr" {
                  set switchValue [concat $switchValues($optArg) \
                        "-UsePortDefaultIpv6Gateway false "]
                  continue
               }
               "link_local_intf_ip_addr" -
               "link_local_intf_ip_addr_step" -
               "link_local_intf_prefix_len" {
                  set switchValue $switchValues($optArg)
                  set linkLocalOptFound true
               }
               "vlan_outer_cfi" {
                  set vlanOuterCfi $::Mld::userArgsArray($optArg)
                  continue
               }
               "vlan_outer_user_priority" {
                  set vlanOuterUserPriority $::Mld::userArgsArray($optArg)
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
            if {$linkLocalOptFound == true} {
               set stcObj "Ipv6LinkLocalIf"
            } else {
               set stcObj [::sth::sthCore::getswitchprop ::Mld:: \
                  emulation_mld_config $optArg stcobj]
            }

            append originalStcObjLst($stcObj) "-$stcAttr $switchValue "
         }

         if {[info exists ::Mld::userArgsArray(count)] == 0} {
            set ::Mld::userArgsArray(count) [::sth::sthCore::getswitchprop \
                  ::Mld:: emulation_mld_config \
                  count default]
         }

         set returnHandle ""
         set rethostHandle ""

         set i 0

         foreach mldHostCfg $mldHostCfgList {
            array unset stcObjLst
            array set stcObjLst [array get originalStcObjLst]

            set host [::sth::sthCore::invoke stc::get $mldHostCfg -parent]

            set ipv6ObjHandle [::sth::sthCore::invoke stc::get $host -Ipv6If.1.handle]

            set ipv6LinkLocalObjHandle [::sth::sthCore::invoke stc::get $host -Ipv6If.2.handle]

            set ethiiIfObjHandle [::sth::sthCore::invoke stc::get $host -ethiiIf.handle]

            set vlanIfObjHandle [::sth::sthCore::invoke stc::get $ipv6ObjHandle -stackedonendpoint-Targets]

            set mldHostCfgObjHandle [::sth::sthCore::invoke stc::get $host -children-MldHostConfig]

            lappend returnHandle $mldHostCfgObjHandle
            lappend rethostHandle $host

            # Modify MLD block config of host
            lappend stcObjLst(MldHostConfig) "-UsesIf-targets" \
                  "$ipv6ObjHandle $ipv6LinkLocalObjHandle"
	    ::sth::sthCore::invoke stc::config $mldHostCfgObjHandle $stcObjLst(MldHostConfig)

            set ipIfStackedOnEndpointTarget \
                  [::sth::sthCore::invoke stc::get $ipv6ObjHandle -stackedonendpoint-Targets]
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

               #Set Outer VLAN information
               if {$vlanOuterOptFound} {
                  set outerVlanIfObjHandle [::sth::sthCore::invoke stc::get $vlanIfObjHandle -stackedOnEndpoint-Targets
                  ]
                  if {![regexp -nocase {vlanif[0-9a-f]} \
                        $outerVlanIfObjHandle]} {
                     set outerVlanIfObjHandle [::sth::sthCore::invoke stc::create vlanIf -under $host [list -stackedonendpoint-Sources $vlanIfObjHandle -stackedonendpoint-Targets $ethiiIfObjHandle]]
                  }
                  ::sth::sthCore::invoke stc::config $outerVlanIfObjHandle [list "-vlanId" [lindex $vlanIdList [expr ($i*2)+1]] "-cfi" $vlanOuterCfi "-priority" $vlanOuterUserPriority]

                  lappend stcObjLst(VlanIf) \
                        "-vlanId" [lindex $vlanIdList [expr $i*2]]

                  set vlanIfStackedOnEndpointTarget $outerVlanIfObjHandle
                  set ethiiIfStackedOnEndpointSources $outerVlanIfObjHandle
               }

               lappend stcObjLst(VlanIf) \
                     "-stackedonendpoint-Sources" [::sth::sthCore::invoke stc::get $host -toplevelif-Targets]\
                     "-stackedonendpoint-Targets" \
                           $vlanIfStackedOnEndpointTarget

               ::sth::sthCore::invoke stc::config $vlanIfObjHandle $stcObjLst(VlanIf)
               set stcObjLst(VlanIf) ""
            }

            lappend stcObjLst(Ipv6If) \
                  "-stackedonendpoint-Targets" $ipIfStackedOnEndpointTarget \
                  "-address" [::sth::sthCore::updateIpAddress \
                        6 $::Mld::userArgsArray(intf_ip_addr) \
                        $::Mld::userArgsArray(intf_ip_addr_step) $i] \
                  "-gateway" [::sth::sthCore::updateIpAddress \
                        6 $::Mld::userArgsArray(neighbor_intf_ip_addr) \
                        $::Mld::userArgsArray(neighbor_intf_ip_addr_step) $i]
            ::sth::sthCore::invoke stc::config $ipv6ObjHandle $stcObjLst(Ipv6If)


            # Set link local starting IP
            if {[info exists stcObjLst(Ipv6LinkLocalIf)]} {
               ::sth::sthCore::invoke stc::config $ipv6LinkLocalObjHandle $stcObjLst(Ipv6LinkLocalIf)
            }

            lappend stcObjLst(EthiiIf) \
                  -stackedonendpoint-Sources \
                        $ethiiIfStackedOnEndpointSources
            ::sth::sthCore::invoke stc::config $ethiiIfObjHandle $stcObjLst(EthiiIf)

            incr i
         }
         #move the result subscriber to the emulation_mld_info, since if the result is subscibed, and then enable the iptv on it, it will get the demon died.
         #so in the hltapi script, need to make sure the emulation_iptv_config should not be called after the emulation_mld_info
         #if {$::Mld::subscription_state == 0} {
         ## Create an MLD port dataset
         #set portResultDataSet \
         #      [::Mld::emulation_mld_config_create_resultDataset \
         #            "MldPortConfig" \
         #            "MldPortResults" \
         #            [list \
         #                  "multicastportresults.txgroupandsourcespecificquerycount" \
         #                  "multicastportresults.rxgroupandsourcespecificquerycount" \
         #                  "multicastportresults.rxv1querycount" \
         #                  "multicastportresults.txv1reportcount" \
         #                  "multicastportresults.rxv1reportcount" \
         #                  "multicastportresults.rxv2querycount" \
         #                  "multicastportresults.txv2reportcount" \
         #                  "multicastportresults.rxv2reportcount" \
         #                  "multicastportresults.rxunknowntypecount" \
         #                  "mldportresults.rxmldchecksumerrorcount" \
         #                  "mldportresults.rxmldlengtherrorcount"] \
         #      ]
         ## Create an MLD group membership dataset
         #set mldGroupMembershipResultDataSet \
         #      [::Mld::emulation_mld_config_create_resultDataset \
         #            "MldGroupMembership" \
         #            "MldGroupMembershipResults" \
         #            [list "Mldgroupmembershipresults.hostaddr" \
         #                  "Mldgroupmembershipresults.groupaddr" \
         #                  "multicastgroupmembershipresults.state" \
         #                  "multicastgroupmembershipresults.joinlatency" \
         #                  "multicastgroupmembershipresults.leavelatency"] \
         #      ]
         #
         #set mldResultsDataSet \
         #      [::Mld::emulation_mld_config_create_resultDataset \
         #            "MldHostConfig" \
         #            "MldHostResults" \
         #            [list "mldhostresults.minjoinlatency" \
         #                  "mldhostresults.maxjoinlatency" \
         #                  "mldhostresults.avgjoinlatency" \
         #                  "mldhostresults.minleavelatency" \
         #                  "mldhostresults.maxleavelatency" \
         #                  "mldhostresults.avgleavelatency"] \
         #      ]
         #
         #::sth::sthCore::doStcApply
         #
         ## Subscribe to the datasets
         #::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $portResultDataSet
         #::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $mldGroupMembershipResultDataSet
         #::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $mldResultsDataSet
         #set ::Mld::subscription_state 1
         #sleep 3
         #}
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

   proc ::Mld::emulation_mld_config_delete {returnKeyedListVarName {level 1}} {
      variable ::Mld::userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         variable mldCreatedHosts
         variable hostFilterMode
         variable hostFilterIpAddr

         set userArgsArray(handle) [emulation_mld_config_getMldHostCfgList $userArgsArray(handle)]

         foreach sessionHandle $::Mld::userArgsArray(handle) {
            # Record the MLD host config block's parent handle before
            # deleting the block
            set hostHandle [::sth::sthCore::invoke stc::get $sessionHandle -parent]

            ::sth::sthCore::invoke stc::delete $sessionHandle

            # Delete host parent only if created by MLD commands
            if {[info exists mldCreatedHosts($hostHandle)]} {
               unset mldCreatedHosts($hostHandle)
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
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while deleting MLD "
                       "session \"$::Mld::userArgsArray(handle)\".  \n"
                       "Returned Error:  $returnedString"] \
               {}
      } else {
         keylset returnKeyedList handle $::Mld::userArgsArray(handle)
         keylset returnKeyedList handles $::Mld::userArgsArray(handle)
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return $returnKeyedList
   }

   proc emulation_mld_config_enable_all {returnKeyedListVarName {level 1}} {
      variable ::Mld::userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retval [catch {
         if {[info exists ::Mld::userArgsArray(handle)] == 0} {
            return -code error [concat "Error: MLD session was not enabled.  " \
                  "Missing mandatory argument \"-handle\".  "]
         }

         set userArgsArray(handle) [emulation_mld_config_getMldHostCfgList $userArgsArray(handle)]

         foreach mldHostConfig $::Mld::userArgsArray(handle) {
            ::sth::sthCore::invoke stc::config $mldHostConfig [list -Active true]
         }
         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retval} {
         ::sth::sthCore::processError returnKeyedList \
            [concat "Error: Error encountered while enabling MLD "
                  "session \"$::Mld::userArgsArray(handle)\".  \n"
                  "Returned Error: $returnedString"]
         keylset returnKeyedList status $::sth::sthCore::FAILURE
      } else {
         keylset returnKeyedList handle $::Mld::userArgsArray(handle)
         keylset returnKeyedList handles $::Mld::userArgsArray(handle)
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return $returnKeyedList
   }

   proc emulation_mld_config_disable_all {returnKeyedListVarName {level 1}} {
      variable ::Mld::userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retval [catch {
         if {[info exists ::Mld::userArgsArray(handle)] == 0} {
            return -code error [concat "Error: MLD session was not disabled.  " \
                  "Missing mandatory argument \"-handle\".  "]
         }

         set userArgsArray(handle) [emulation_mld_config_getMldHostCfgList $userArgsArray(handle)]

         foreach mldHostConfig $::Mld::userArgsArray(handle) {
            ::sth::sthCore::invoke stc::config $mldHostConfig [list -Active false]
         }
         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
         ::sth::sthCore::processError returnKeyedList \
            [concat "Error: Error encountered while disabling MLD "
                  "session \"$::Mld::userArgsArray(handle)\".  \n"
                  "Returned Error: $returnedString"]
         keylset returnKeyedList status $::sth::sthCore::FAILURE
      } else {
         keylset returnKeyedList handle $::Mld::userArgsArray(handle)
         keylset returnKeyedList handles $::Mld::userArgsArray(handle)
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return $returnKeyedList
   }


   proc emulation_mld_group_config_create {returnKeyedListVarName {level 1}} {
      variable ::Mld::userArgsArray
      variable hostFilterMode
      variable hostFilterIpAddr

      upvar $level $returnKeyedListVarName returnKeyedList

      array unset deviceList
      set mldGrpMembership ""

      set retVal [catch {
         if {[info exists ::Mld::userArgsArray(session_handle)] == 0} {
            return -code error [concat "Error: Unable to create an MLD " \
                  "group membership.  Missing mandatory argument " \
                  "\"-session_handle\".  "]
         }

         #to stardardize the output format, we modify the returned keyedlist as below, so need to update the input value again
         #{handle mldhostconfig1} {handles mldhostconfig1} {status 1}  => {handle host1} {handles mldhostconfig1} {status 1}
         set userArgsArray(session_handle) [emulation_mld_config_getMldHostCfgList $userArgsArray(session_handle)]

         set mld_session_handle $::Mld::userArgsArray(session_handle)

         if {[info exists ::Mld::userArgsArray(group_pool_handle)] == 0} {
            return -code error [concat "Error: Unable to create an MLD " \
                  "group membership.  Missing mandatory argument " \
                  "\"-group_pool_handle\".  "]
         }

         foreach groupPoolHandle $::Mld::userArgsArray(group_pool_handle) {
            foreach sessionHandle $::Mld::userArgsArray(session_handle) {
               set mldGrpMembership [::sth::sthCore::invoke stc::create "MldGroupMembership" -under $sessionHandle [list -SubscribedGroups-targets $groupPoolHandle]
               ]
               if {[info exists ::Mld::userArgsArray(host_handle)] != 0} {
                  foreach hosthandle $::Mld::userArgsArray(host_handle) {
                     ::sth::sthCore::invoke stc::config $mldGrpMembership SubscribedSources-targets $hosthandle
                  }
               }
               if {[info exists ::Mld::userArgsArray(device_group_mapping)] != 0} {
                  ::sth::sthCore::invoke stc::config $mldGrpMembership -DeviceGroupMapping $::Mld::userArgsArray(device_group_mapping)
               }
               set host [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $mldGrpMembership "-parent"] "-parent"]
               if {[info exists ::Mld::userArgsArray(user_defined_src)] != 0} {
                  ::sth::sthCore::invoke stc::config $mldGrpMembership [list "-filterMode" $hostFilterMode($host) "-userDefinedSources" $::Mld::userArgsArray(user_defined_src)]         
               }

               #Rxu: add switch filter_ip_addr
               set mldVersion [::sth::sthCore::invoke stc::get $sessionHandle -Version]
               if {[regexp -nocase "MLD_V2" $mldVersion ]} {
                  set ipv6NetworkBlock [::sth::sthCore::invoke stc::get $mldGrpMembership -children-Ipv6NetworkBlock]
                  ::sth::sthCore::invoke stc::config $ipv6NetworkBlock  [list "-StartIpList" $hostFilterIpAddr($host) ]
               }
               #end

               if {[info exists ::Mld::userArgsArray(source_pool_handle)]} {
                  ::Mld::emulation_mld_group_config_srcPool \
                        $::Mld::userArgsArray(source_pool_handle) \
                        $mldGrpMembership
               }
            }
         }

         ::sth::sthCore::doStcApply

      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $mldGrpMembership
      }

      return -code $retVal $returnKeyedList
   }

   proc ::Mld::emulation_mld_group_config_modify {returnKeyedListVarName} {
      variable ::Mld::userArgsArray

      upvar 1 $returnKeyedListVarName returnKeyedList

      set mldGrpMembership ""

      set retVal [catch {
         if {[info exists ::Mld::userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to modify the MLD " \
                  "group member.  Missing mandatory argument " \
                  "\"-handle\".  "]
         }

         set mldGrpMembership $::Mld::userArgsArray(handle)

         variable hostFilterMode
         variable hostFilterIpAddr

         if {[info exists ::Mld::userArgsArray(group_pool_handle)]} {
            set mldHostCfgs ""
            # Clear all group memberships first
            foreach handle $Mld::userArgsArray(handle) {
               # Remember the MLD host config parent objects
               lappend mldHostCfgs [::sth::sthCore::invoke stc::get $handle -parent]
               ::sth::sthCore::invoke stc::delete $handle
            }

            foreach mldHostCfg $mldHostCfgs {
               foreach handle $::Mld::userArgsArray(group_pool_handle) {
                  set mldGrpMembership [::sth::sthCore::invoke stc::get $handle -SubscribedGroups-Sources]

                  if {[string length [string trim $mldGrpMembership]] == 0} {
                     set mldGrpMembership [::sth::sthCore::invoke stc::create "MldGroupMembership" -under $mldHostCfg]
                  }
                  set host [::sth::sthCore::invoke stc::get $mldHostCfg "-parent"]
                  if {[info exists ::Mld::userArgsArray(user_defined_src)] != 0} {
                     ::sth::sthCore::invoke stc::config $mldGrpMembership [list "-SubscribedGroups-targets" $handle "-filterMode" $hostFilterMode($host) "-UserDefinedSources" $::Mld::userArgsArray(user_defined_src) ]
                  }
                  if {[info exists ::Mld::userArgsArray(host_handle)] != 0} {
                     foreach hosthandle $::Mld::userArgsArray(host_handle) {
                        ::sth::sthCore::invoke stc::config $mldGrpMembership SubscribedSources-targets $hosthandle
                     }
                  }
                  #Rxu: add switch filter_ip_addr
                  set mldVersion [::sth::sthCore::invoke stc::get $mldHostCfg -Version]
                  if {[regexp -nocase "MLD_V2" $mldVersion ]} {
                     set ipv6NetworkBlock [::sth::sthCore::invoke stc::get $mldGrpMembership -children-Ipv6NetworkBlock]
                     ::sth::sthCore::invoke stc::config $ipv6NetworkBlock [list "-StartIpList" $hostFilterIpAddr($host)  ]
                  }
                  #end

                  if {[info exists ::Mld::userArgsArray(source_pool_handle)]} {
                     ::Mld::emulation_mld_group_config_srcPool \
                           $::Mld::userArgsArray(source_pool_handle) \
                           $mldGrpMembership
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
         keylset returnKeyedList handle $mldGrpMembership
      }

      return -code $retVal $returnKeyedList
   }

   proc ::Mld::emulation_mld_group_config_delete {returnKeyedListVarName} {
      variable ::Mld::userArgsArray

      upvar 1 $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists ::Mld::userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to delete the " \
                  "specified pool from the MLD group member.  Missing " \
                  "mandatory argument \"-handle\".  "]
         }
         if {[info exists ::Mld::userArgsArray(group_pool_handle)]} {
            foreach membership [::sth::sthCore::invoke stc::get $::Mld::userArgsArray(group_pool_handle) -subscribedgroups-Sources] {
               foreach grpMembership $::Mld::userArgsArray(handle) {
                  if {[lsearch -exact $grpMembership $membership] == -1} {
                        puts [concat "Warning:  Unable to delete the " \
                              "group pool \"$::Mld::userArgsArray(group_pool_handle)\" " \
                              "from the MLD group membership " \
                              "$::Mld::userArgsArray(handle)\".  The group pool is not " \
                              "part of the membership.  "]
                  }
               }
            }
         }
         foreach grpMembership $::Mld::userArgsArray(handle) {
            ::sth::sthCore::invoke stc::delete $grpMembership
         }

         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
   	 ::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $::Mld::userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc ::Mld::emulation_mld_group_config_clear_all {returnKeyedListVarName {level 1}} {
      variable ::Mld::userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists ::Mld::userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to remove all group " \
                  "pools from the MLD group member.  Missing mandatory " \
                  "argument \"-handle\".  "]
         }

         foreach grpConfig $::Mld::userArgsArray(handle) {
            set mldHostConfig [::sth::sthCore::invoke stc::get $grpConfig -parent]

            foreach grpMembership [::sth::sthCore::invoke stc::get $mldHostConfig -children-MldGroupMembership] {
               ::sth::sthCore::invoke stc::delete $grpMembership
            }
         }

         ::sth::sthCore::doStcApply
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $::Mld::userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc ::Mld::emulation_mld_config_create_resultDataset {configClass resultClass propertyIdArray} {
      set resultDataSet ""

      set retVal [catch {
         set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]

         ::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list "-ResultRootList" $::sth::GBLHNDMAP(project) "-ConfigClassId" $configClass "-ResultClassId" $resultClass "-PropertyIdArray" $propertyIdArray]
      } returnedString]

      return -code $retVal $resultDataSet
   }

   proc ::Mld::emulation_mld_group_config_srcPool {srcPoolHandleList mldGrpMembershipHandle} {
        # : Modified the code to allow for multiple sources to be added at once.

       # ::sth::sthCore::invoke stc::config $mldGrpMembershipHandle [list "-UserDefinedSources" "TRUE"]
        set srcIpv6NetworkBlock [::sth::sthCore::invoke stc::get $mldGrpMembershipHandle -children-Ipv6NetworkBlock]

        # The following code will build a list of source IP addresses for the IPv6NetworkBlock object.
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

            ::sth::sthCore::invoke stc::config $srcIpv6NetworkBlock $ipNetworkBlkArgs

            set ipAddr       [::sth::sthCore::invoke stc::get $srcIpv6NetworkBlock -startIpList]
            set stepValue    [::sth::sthCore::invoke stc::get $srcIpv6NetworkBlock -addrIncrement]
            set prefixLength [::sth::sthCore::invoke stc::get $srcIpv6NetworkBlock -PrefixLength]
            set stepValue    [::sth::sthCore::prefixLengthToIpStepValue 6 $prefixLength $stepValue]

            set ipAddr [::sth::sthCore::normalizeIPv6Addr $ipAddr]

            # Don't add duplicate addresses.
            if { [lsearch -exact $ipList $ipAddr] == -1 } {
                lappend ipList $ipAddr
            }

            for {set i 1} {$i < [::sth::sthCore::invoke stc::get $srcIpv6NetworkBlock -networkCount]} {incr i} {
                set nextIpAddr [::sth::sthCore::updateIpAddress 6 $ipAddr $stepValue $i]
                set nextIpAddr [::sth::sthCore::normalizeIPv6Addr $nextIpAddr]

                # Don't add duplicate addresses.
                if { [lsearch -exact $ipList $nextIpAddr] == -1 } {
                    lappend ipList $nextIpAddr
                }
            }
        }

        # The "startIpList" is actually a list, so we need to configure it that way.
        if {![regexp "channel" $mldGrpMembershipHandle]} {
         ::sth::sthCore::invoke stc::config $mldGrpMembershipHandle [list -IsSourceList TRUE]
        }

        ::sth::sthCore::invoke stc::config $srcIpv6NetworkBlock [list -startIpList $ipList]
   }

   proc ::Mld::emulation_mld_config_getVlanIdList {switchValuesVarName vlanIdListVarName {level 1}} {
      variable ::Mld::userArgsArray

      upvar $level $vlanIdListVarName vlanIdList
      upvar $level $switchValuesVarName switchValues

      set retVal [catch {
         set vlanIdList ""

         set vlanOptFound [regexp -nocase -- {-vlan.*} \
               $::Mld::userArgsArray(optional_args)]

         set qinqOptFound [regexp -nocase -- {(vlan_id_outer)|(vlan_outer)|(qinq)} \
               $::Mld::userArgsArray(optional_args)]

         if {!$vlanOptFound && !$qinqOptFound} {
            return
         }

         set vlanCount [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config count default]
         set vlanId [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id default]
         set vlanIdStep [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_step default]
         set vlanIdCount [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_count default]
         set vlanIdMode [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_mode default]
         set vlanIdOuter [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_outer default]
         set vlanIdOuterStep [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_outer_step default]
         set vlanIdOuterCount [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_outer_count default]
         set vlanIdOuterMode [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config vlan_id_outer_mode default]
         set qinqIncrMode [::sth::sthCore::getswitchprop ::Mld:: \
               emulation_mld_config qinq_incr_mode default]

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
                  for {set o 0} {$o < $vlanIdOuterCount} {incr o} {
                     for {set i 0} {$i < $vlanIdCount} {incr i} {
                        lappend vlanIdList $vlanId $vlanIdOuter
                        incr n

                        if {$n >= $vlanCount} {
                           break
                        }

                        incr vlanId $vlanIdStep
                     }

                     incr vlanIdOuter $vlanIdOuterStep
                  }
               }
            }
            "outer" {
               if {[info exists switchValues(vlan_id_count)] == 0} {
                  set vlanIdCount $vlanIdOuterCount
               }

               for {set n 0} {$n < $vlanCount} {} {
                  for {set i 0} {$i < $vlanIdOuterCount} {incr i} {
                     for {set o 0} {$o < $vlanIdOuterCount} {incr o} {
                        lappend vlanIdList $vlanId $vlanIdOuter
                        incr n

                        if {$n >= $switchValues(count)} {
                           break
                        }

                        incr vlanIdOuter $vlanIdOuterStep
                     }

                     incr vlanId $vlanIdStep
                  }
               }
            }
            "both" {
               set i $vlanId
               set o $vlanIdOuter

               for {set n 0} {$n < $vlanCount} {incr n} {
                  lappend vlanIdList $i $o

                  incr i $vlanIdStep
                  incr o $vlanIdOuterStep
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

   proc ::Mld::emulation_mld_config_getHostList {hostListVarName {level 1}} {
      variable ::Mld::userArgsArray

      upvar $level $hostListVarName hostList

      set retVal [catch {
         ::sth::sthCore::parseInputArgs switches switchValues \
               $::Mld::userArgsArray(optional_args)

         if {[info exists ::Mld::userArgsArray(count)] == 0} {
            set ::Mld::userArgsArray(count) [::sth::sthCore::getswitchprop \
                  ::Mld:: emulation_mld_config \
                  count default]
         }

         set deviceCount $::Mld::userArgsArray(count)
         set createCount 1

         if {[regexp -nocase -- {(vlan_id_outer)|(vlan_outer)|(qinq)} \
               $::Mld::userArgsArray(optional_args)]} {
            set deviceCount 1
            set createCount $::Mld::userArgsArray(count)
         }

         array set deviceList [::sth::sthCore::invoke stc::perform deviceCreate "-parentList" $::sth::GBLHNDMAP(project) "-ifStack" "Ipv6If EthIIIf" "-ifCount" "1 1" "-port" $::Mld::userArgsArray(port_handle) "-deviceType" "Host" "-deviceCount" $deviceCount "-createCount" $createCount]
         set hostList $deviceList(-ReturnList)

         # Track the newly created host(s)
         variable mldCreatedHosts

         foreach hostHandle $hostList {
            set mldCreatedHosts($hostHandle) {}

            # Set the IPv6 address stepmask for full address increment
            ::sth::sthCore::invoke stc::config [::sth::sthCore::invoke stc::get $hostHandle "-topLevelIf-Targets"] [list "-addrStepMask" FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF]
         }
      } returnedString]

      if {$retVal} {
         return -code $retVal $returnedString
      } else {
         return $hostList
      }
   }
}

proc ::Mld::emulation_mld_config_getMldHostCfgList {inputHdlList} {
      variable userArgsArray
      set mldHostCfgList ""

      set retVal [catch {
         foreach inputHdl $inputHdlList {
            if {[string match "host*" $inputHdl] || [string match "router*" $inputHdl] || [string match "emulateddevice*" $inputHdl] } {
               set mldHostCfg [::sth::sthCore::invoke "stc::get $inputHdl -children-mldHostConfig"]
               lappend mldHostCfgList $mldHostCfg
            } else {
               #current input handle is mldhostconfig handle, nothing needs to do
               set mldHostCfgList $inputHdlList
            }
         }
      } returnedString]

      if {$retVal} {
         return -code $retVal $returnedString
      } else {
         return $mldHostCfgList
      }
   }
