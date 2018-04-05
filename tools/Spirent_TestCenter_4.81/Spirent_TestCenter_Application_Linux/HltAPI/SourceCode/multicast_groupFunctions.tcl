# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::multicast_group {

   array unset multicastSourcePool

   proc emulation_multicast_group_config_create {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[emulation_multicast_group_isMulticastIpAddress \
               $userArgsArray(ip_addr_start)] == false} {
            return -code error [concat "Error:  Unable to create a " \
                  "multicast group with the non-multicast IP address " \
                  "\"$userArgsArray(ip_addr_start)\".  "]
         }

         set stcAttrPoolName "-[::sth::sthCore::getswitchprop \
               ::sth::multicast_group:: emulation_multicast_source_config \
               pool_name stcattr]"
         set poolName ""
         if {[info exists userArgsArray(pool_name)]} {
            set poolName $userArgsArray(pool_name)
         }

         emulation_multicast_config_create \
               userArgsArray \
               $stcAttrPoolName \
               $poolName
         emulation_multicast_group_config_modify $returnKeyedListVarName
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_multicast_source_config_create {returnKeyedListVarName {level 1}} {
      variable userArgsArray
      variable multicastSourcePool

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[emulation_multicast_group_isMulticastIpAddress \
               $userArgsArray(ip_addr_start)] == true} {
            return -code error [concat "Error:  Unable to create " \
                  "multicast sources with the multicast IP address " \
                  "\"$userArgsArray(ip_addr_start)\".  "]
         }

         set stcAttrPoolName "-[::sth::sthCore::getswitchprop \
               ::sth::multicast_group:: emulation_multicast_source_config \
               pool_name stcattr]"
         set poolName ""
         if {[info exists userArgsArray(pool_name)]} {
            set poolName $userArgsArray(pool_name)
         }

         set userArgsArray(handle) \
               multicastSourcePool([emulation_multicast_group_getNextSrcIdx])

         # Copy the contents of userArgsArray for future processing
         foreach i [array names userArgsArray] {
            lappend $userArgsArray(handle) $i $userArgsArray($i)
         }
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_multicast_config_create {userArgsArrayVarName stcAttrPoolName poolName {level 1}} {
      upvar $level $userArgsArrayVarName userArgsArray

      set retVal [catch {
         set ipGroup Ipv4Group

         if {[emulation_multicast_group_isIpv6 $userArgsArray(ip_addr_start)]} {
            set ipGroup Ipv6Group
         }

         set cmdAttrValPairs ""

         if {$poolName != ""} {
            set cmdAttrValPairs [list $stcAttrPoolName \
                  $userArgsArray(pool_name)]
         }

         set userArgsArray(handle) [::sth::sthCore::invoke stc::create $ipGroup -under $::sth::GBLHNDMAP(project) $cmdAttrValPairs]
      } returnedString]

      if {$retVal} {
   		return -code error [concat "Error:  Error encountered while " \
               "creating network block starting with IP address " \
               "$userArgsArray(ip_addr_start).  \n" \
               "Returned Error:  $returnedString"]
      }

      return $userArgsArray(handle)
   }

   proc emulation_multicast_group_config_modify {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists userArgsArray(ip_addr_start)]} {
            if {[emulation_multicast_group_isMulticastIpAddress \
                  $userArgsArray(ip_addr_start)] == false} {
               return -code error [concat "Error:  Unable to create a " \
                     "multicast group with the non-multicast IP " \
                     "address \"$userArgsArray(ip_addr_start)\".  "]
            }
         }

         emulation_multicast_config_modify emulation_multicast_group_config
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $returnedString
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_multicast_source_config_modify {returnKeyedListVarName {level 1}} {
      variable userArgsArray
      variable multicastSourcePool

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to modify multicast " \
                  "source pool.  Missing mandatory argument \"-handle\".  "]
         } elseif {[info exists $userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to modify multicast " \
                  "source pool.  Handle \"$userArgsArray(handle)\" does not " \
                  "exist.  "]
         }

         array set sourcePoolInfo [subst $$userArgsArray(handle)]
         array set srcPoolOptArgs $sourcePoolInfo(optional_args)
         array set newSrcPoolOptArgs $userArgsArray(optional_args)

         set sourcePoolInfo(optional_args) ""
         set $userArgsArray(handle) ""

         foreach s [array names newSrcPoolOptArgs] {
            set srcPoolOptArgs($s) $newSrcPoolOptArgs($s)
         }

         foreach s [array names srcPoolOptArgs] {
            set sourcePoolInfo([string trimleft $s "-"]) $srcPoolOptArgs($s)
         }

         foreach {s v} $userArgsArray(optional_args) {
            if {[string equal "-handle" [string tolower $s]]} {
               continue
            }

            lappend sourcePoolInfo(optional_args) $s $v
         }

         # Replace the contents of the original info
         foreach i [array names sourcePoolInfo] {
            lappend $userArgsArray(handle) $i $sourcePoolInfo($i)
         }
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList $returnedString {}
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

      return -code $retVal $returnKeyedList
   }

   proc emulation_multicast_config_modify {tableName {level 1}} {
      variable userArgsArray

      if {[info exists userArgsArray(handle)] == 0} {
   		return -code error [concat "Error:  Unable to modify multicast " \
               "block.  Missing mandatory argument \"-handle\".  "]
      }

      # Override Spirent TestCenter IP prefix length default to
      # HLTAPI default
      if {[emulation_multicast_group_isIpv6 $userArgsArray(ip_addr_start)]} {
         set networkBlockArg "-children-Ipv6NetworkBlock"

         if {[info exists userArgsArray(ip_prefix_len)] == 0} {
            set userArgsArray(ip_prefix_len) 128
         }
      } else {
         set networkBlockArg "-children-Ipv4NetworkBlock"

         if {[info exists userArgsArray(ip_prefix_len)] == 0} {
            set userArgsArray(ip_prefix_len) 32
         }
      }

      set NetworkBlockHandle [::sth::sthCore::invoke stc::get $userArgsArray(handle) $networkBlockArg]

      set cmd "::sth::sthCore::invoke stc::config $NetworkBlockHandle "
      set dashedArgs ""

      foreach s [array names userArgsArray] {
         switch -exact [string tolower $s] {
            "mandatory_args" -
            "optional_args" { continue; }
         }

         set v [::sth::sthCore::getswitchprop ::sth::multicast_group:: \
               $tableName $s stcattr]

         if {[string compare $v "_none_"] == 0} {
            continue
         }

         append dashedArgs "-$v " "$userArgsArray($s) "
      }

      lappend cmd $dashedArgs
      set retVal [catch $cmd returnedString]

      if {$retVal} {
   		return -code error \
               [concat "Error:  Error encountered while configuring network " \
                     "block \"$NetworkBlockHandle\".  \n" \
                     "Returned Error:  $returnedString"]
      }

		return $userArgsArray(handle)
   }

   proc emulation_multicast_config_delete {returnKeyedListVarName {level 1}} {
      variable userArgsArray

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         # First, clear any multicast group membership subscribing to this
         # group.  Any group membership after deleting the multicast pool
         # becomes invalid.
         foreach subscriber [::sth::sthCore::invoke stc::get $userArgsArray(handle) "-subscribedgroups-Sources"] {
            ::sth::sthCore::invoke stc::delete $subscriber
            keylset returnedKeyedList log [concat "Automatically deleted " \
                  "invalidated multicast group membership \"$subscriber\".  "]
         }
         ::sth::sthCore::invoke stc::delete $userArgsArray(handle)
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while deleting network "
                       "block \"$userArgsArray(handle)\".  \n"
                       "Returned Error:  $returnedString"]
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

		return -code $retVal $returnKeyedList
   }

   proc emulation_multicast_source_config_delete {returnKeyedListVarName {level 1}} {
      variable userArgsArray
      variable multicastSourcePool

      upvar $level $returnKeyedListVarName returnKeyedList

      set retVal [catch {
         if {[info exists $userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Multicast source pool " \
                  "\"$userArgsArray(handle)\" does not exist.  "]
         }

         unset $userArgsArray(handle)
      } returnedString]

      if {$retVal} {
   		::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while deleting network "
                       "block \"$userArgsArray(handle)\".  \n"
                       "Returned Error:  $returnedString"]
      } else {
         keylset returnKeyedList status $::sth::sthCore::SUCCESS
         keylset returnKeyedList handle $userArgsArray(handle)
      }

		return -code $retVal $returnKeyedList
   }

   proc emulation_multicast_group_isIpv6 {ip} {
      set retVal [catch {::sth::sthCore::normalizeIPv6Addr $ip}]

      if {$retVal} {
         return false
      }

      return true
   }

   proc emulation_multicast_group_isMulticastIpAddress_ipv4 {ip} {
      set hexNum "0x"

      set retVal [catch {
         scan $ip "%i.%i.%i.%i" bytes(1) bytes(2) bytes(3) bytes(4)

         for {set b 1} {$b <= 4} {incr b} {
            append hexNum [format "%02x" $bytes($b)]
         }
      }]

      if {$retVal == 0} {
         if {($hexNum >= 0xE0000000) && ($hexNum <= 0xEFFFFFFF)} {
            return true
         }
      }

      return false
   }

   proc emulation_multicast_group_isMulticastIpAddress_ipv6 {ip} {
      set retVal [catch {
         set ipv6 [::sth::sthCore::normalizeIPv6Addr $ip]

         scan $ipv6 "%x:%x:%x:%x:%x:%x:%x:%x" \
               w(1) w(2) w(3) w(4) w(5) w(6) w(7) w(8)
      }]
      
      if {$retVal == 0} {
         if {[expr $w(1) & 0xFF00] == 0xFF00} {
            return true
         }
      }
      
      return false
   }

   proc emulation_multicast_group_isMulticastIpAddress {ip} {
      if {[emulation_multicast_group_isIpv6 $ip]} {
         return [emulation_multicast_group_isMulticastIpAddress_ipv6 $ip]
      } else {
         return [emulation_multicast_group_isMulticastIpAddress_ipv4 $ip]
      }
   }

   proc emulation_multicast_group_getNextSrcIdx {} {
      variable multicastSourcePool
      set arrayLen [array size multicastSourcePool]
      set sortedIdx [lsort -increasing -integer [array names multicastSourcePool]]

      for {set i 0} {$i < $arrayLen} {incr i} {

         set idxFound [lsearch -start $i $sortedIdx $i]

         if {$idxFound == -1} {
            break
         }
      }

      return $i
   }

   proc emulation_multicast_group_getSrcPool {srcPoolHandle arrayVarName {level 1}} {
      variable multicastSourcePool

      upvar $level $arrayVarName srcPoolInfo

      if {[info exists $srcPoolHandle] == 0} {
         return -code error [concat "Error:  Unable to retrieve information " \
               "multicast source pool \"$srcPoolHandle\" does not " \
               "exist.  "]
      }

      array set srcPoolInfo [subst $$srcPoolHandle]
   }
}

proc ::sth::multicast_group::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} { 

	set optionValueList {}
    foreach item $::sth::multicast_group::sortedSwitchPriorityList {
        set opt [lindex $item 1]
        # make sure the option is supported
        if {![::sth::sthCore::getswitchprop ::sth::multicast_group:: $cmdType $opt supported]} {
            ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
            return -code error $returnKeyedList
        }
        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::multicast_group:: $cmdType $opt mode] "_none_"]} { continue }
            
        set func [::sth::sthCore::getModeFunc ::sth::multicast_group:: $cmdType $opt $mode]
        # only process options that have <modeFunc> as their mode function
        if {[string match -nocase $func $modeFunc]} {
            ##check dependency
            #::sth::multicast_group::checkDependency $cmdType $opt $modeFunc $mode
            if {![info exists ::sth::multicast_group::userArgsArray($opt)]} { continue }
             
            # some values need to be processed (or converted) to be stc friendly
            set processFunc [::sth::sthCore::getswitchprop ::sth::multicast_group:: $cmdType $opt procfunc]
            if {[string match -nocase $processFunc "_none_"]} {
                set stcAttr [::sth::sthCore::getswitchprop ::sth::multicast_group:: $cmdType $opt stcattr]
                if {[string match -nocase $stcAttr "_none_"]} { continue }
                if {![catch {::sth::sthCore::getFwdmap ::sth::multicast_group:: $cmdType $opt $::sth::multicast_group::userArgsArray($opt)} value]} {
				    lappend optionValueList -$stcAttr $value
                } else {
                    lappend optionValueList -$stcAttr $::sth::multicast_group::userArgsArray($opt)
			    }
            } else {
                eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::multicast_group::userArgsArray($opt)]
            }
        }    
    }
    return $optionValueList
}

########Logic for emulation_mcast_wizard_config_create############
#created McastGenParams?
#   1)config values for McastGenParams
#   2)config values for McastIpv4GroupParams
#   3)config values for McastIpv6GroupParams
#   4)config values for McastUpstreamPortParams
#   5)config values for McastUpstreamIpv4PortParams
#   6)config values for McastUpstreamIpv6PortParams
#   7)config values for McastDownstreamPortParams
#   8)config values for McastDownstreamIpv4PortParams
#   9)config values for McastDownstreamIpv6PortParams
#   10)set return value
#if McastGenParams not already created
#   11)create McastGenParams under project 
#   12)follow step 1 to 10 
###################################################################
proc ::sth::multicast_group::emulation_mcast_wizard_config_create {returnKeyedList} {

    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::multicast_group::userArgsArray
    set retVal [catch {
        
    set McastGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-McastGenParams]
	if { $McastGenParamsHdl eq ""} {
	    set McastGenParamsHdl [::sth::sthCore::invoke stc::create "McastGenParams" -under $::sth::GBLHNDMAP(project)]
	}
    
    #1) config values for McastGenParams
	if {$McastGenParamsHdl ne "" } {
	    set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastGenParams create $McastGenParamsHdl]
 	    ::sth::sthCore::invoke stc::config $McastGenParamsHdl $optionValueList
    }
		
	#2) config values for  McastIpv4GroupParams
    set McastIpv4GroupParamsHdl [::sth::sthCore::invoke stc::get $McastGenParamsHdl -Children-McastIpv4GroupParams]
    if {$McastIpv4GroupParamsHdl ne "" } {
        set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastIpv4GroupParams create $McastIpv4GroupParamsHdl]
        ::sth::sthCore::invoke stc::config $McastIpv4GroupParamsHdl $optionValueList
    }
    
    #3) config values for McastIpv6GroupParams
    set McastIpv6GroupParamsHdl [::sth::sthCore::invoke stc::get $McastGenParamsHdl -Children-McastIpv6GroupParams]
    if {$McastIpv6GroupParamsHdl ne "" } {
        set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastIpv6GroupParams create $McastIpv6GroupParamsHdl]
        ::sth::sthCore::invoke stc::config $McastIpv6GroupParamsHdl $optionValueList
    }
    
	#upstream
	#port_handle is mandatory 
    set portHandle1 $::sth::multicast_group::userArgsArray(port_handle_upstream)
    if { ![::info exists ::sth::multicast_group::userArgsArray(port_handle_upstream)]} {
        ::sth::sthCore::processError myreturnKeyedList "port_handle_upstream needed when adding port to multicast_group configuration." {}
	    return $returnKeyedList
    }
	
	#4) create McastUpstreamPortParams 
	set McastUpstreamPortParamsHdl [::sth::sthCore::invoke stc::create "McastUpstreamPortParams" -under $McastGenParamsHdl]
	
	#5) set affiliationport-Targets 
	::sth::sthCore::invoke stc::config $McastUpstreamPortParamsHdl "-AffiliationPort-Targets $portHandle1"	
	
	#6) set other config
	if {$McastUpstreamPortParamsHdl ne "" } {
	    set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastUpstreamPortParams create $McastUpstreamPortParamsHdl]
	    ::sth::sthCore::invoke stc::config $McastUpstreamPortParamsHdl $optionValueList
	}
	
	#7) config values for  McastUpstreamIpv4PortParams
    set McastUpstreamIpv4PortParamsHdl [::sth::sthCore::invoke stc::get $McastUpstreamPortParamsHdl -Children-McastUpstreamIpv4PortParams]
    if {$McastUpstreamIpv4PortParamsHdl ne "" } {
        set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastUpstreamIpv4PortParams create $McastUpstreamIpv4PortParamsHdl]
        ::sth::sthCore::invoke stc::config $McastUpstreamIpv4PortParamsHdl $optionValueList
    }
	
	# 8)config values for McastUpstreamIpv6PortParams
    set McastUpstreamIpv6PortParamsHdl [::sth::sthCore::invoke stc::get $McastUpstreamPortParamsHdl -Children-McastUpstreamIpv6PortParams]
    if {$McastUpstreamIpv6PortParamsHdl ne "" } {
        set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastUpstreamIpv6PortParams create $McastUpstreamIpv6PortParamsHdl]
        ::sth::sthCore::invoke stc::config $McastUpstreamIpv6PortParamsHdl $optionValueList
    }	
	
	#Downstream
	#port_handle is mandatory 
    set portHandle2 $::sth::multicast_group::userArgsArray(port_handle_downstream)
    if { ![::info exists ::sth::multicast_group::userArgsArray(port_handle_downstream)]} {
        ::sth::sthCore::processError myreturnKeyedList "port_handle_downstream needed when adding port to multicast_group configuration." {}
	    return $returnKeyedList
    }
	
	#4) create McastDownstreamPortParams 
	set McastDownstreamPortParamsHdl [::sth::sthCore::invoke stc::create "McastDownstreamPortParams" -under $McastGenParamsHdl]
	
	#5) set affiliationport-Targets 
	::sth::sthCore::invoke stc::config $McastDownstreamPortParamsHdl "-AffiliationPort-Targets $portHandle2"
	
	#6) set other config
	if {$McastDownstreamPortParamsHdl ne "" } {
	    set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastDownstreamPortParams create $McastDownstreamPortParamsHdl]
	    ::sth::sthCore::invoke stc::config $McastDownstreamPortParamsHdl $optionValueList
	}
	
	#7) config values for  McastDownstreamIpv4PortParams
    set McastDownstreamIpv4PortParamsHdl [::sth::sthCore::invoke stc::get $McastDownstreamPortParamsHdl -Children-McastDownstreamIpv4PortParams]
    if {$McastDownstreamIpv4PortParamsHdl ne "" } {
        set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastDownstreamIpv4PortParams create $McastDownstreamIpv4PortParamsHdl]
        ::sth::sthCore::invoke stc::config $McastDownstreamIpv4PortParamsHdl $optionValueList
    }
	# 8)config values for McastDownstreamIpv6PortParams
    set McastDownstreamIpv6PortParamsHdl [::sth::sthCore::invoke stc::get $McastDownstreamPortParamsHdl -Children-McastDownstreamIpv6PortParams]
    if {$McastDownstreamIpv6PortParamsHdl ne "" } {
        set optionValueList [getStcOptionValueList emulation_mcast_wizard_config McastDownstreamIpv6PortParams create $McastDownstreamIpv6PortParamsHdl]
        ::sth::sthCore::invoke stc::config $McastDownstreamIpv6PortParamsHdl $optionValueList
    }	
	
	#Wizard Expand and apply - Checking if already any streamblock handle is created and returned using traffic_config..or etc..before expand wizard.
    set ports [::sth::sthCore::invoke stc::get project1 -children-port]
    foreach portHnd $ports {
        set streamBlockHandles [::sth::sthCore::invoke stc::get $portHnd -children-streamblock]
		if { $streamBlockHandles ne "" } {
		    set prestream_handles($portHnd) "$streamBlockHandles"
		}
    }

    set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]
    ::sth::sthCore::invoke stc::perform RtgTestGenConfigExpandAndRunCommand -clearportconfig no -genParams $McastGenParamsHdl
	
    set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]
    set childrenList [split $childrenStr]
	foreach child $pre_childrenStr {
        set index [lsearch $childrenList $child]
        if { $index > -1 } {
            set childrenList [lreplace $childrenList $index $index]
        }
    }
    
    set mcast_hosts_routers ""
    set host_handle ""
    set upstream_handle ""
    set downstream_handle ""
	set router_handle ""
	
	#Getting host and router handles from wizard object.
    foreach child $childrenList {
        if {[string first "host" [string tolower $child]] > -1} {
            lappend mcast_hosts_routers $child
        }
        if {[string first "router" [string tolower $child]] > -1} {
            lappend mcast_hosts_routers $child
        }	
    }	
	foreach mcast_host_router $mcast_hosts_routers {
        
		if {[catch {set deviceName [::sth::sthCore::invoke stc::get $mcast_host_router -Name]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Name from $mcast_host_router. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }		
		#upstream host handle - host1 - ipv4if1 vlanif1 ethiiif1 
		if { [string first "Upstream Host" $deviceName] > -1 } {
            set AffPort_upstream [stc::get $mcast_host_router -AffiliationPort-Targets]
			lappend uphnd_host $mcast_host_router
        }
		
		#upstream Router handle contains- ospf, bgp, isis, pim-sm,pim-ssm 
		if { [string first "Upstream Router" $deviceName] > -1 } {
            set AffPort_upstream [stc::get $mcast_host_router -AffiliationPort-Targets]
			lappend uphnd_router $mcast_host_router
        } 	
		
        #Downstream Router handle contains- pim-sm,pim-ssm
        if { [string first "Downstream Router" $deviceName] > -1 } {
            set AffPort_downstream [stc::get $mcast_host_router -AffiliationPort-Targets]
			lappend downhnd_rtr $mcast_host_router
        }
		
		#Downstream Host handle v4 contains- igmpv1,igmpv2,igmpv3, v6 - mld_v1,mld_v2
		if { [string first "Downstream Host" $deviceName] > -1 } {
            set AffPort_downstream [stc::get $mcast_host_router -AffiliationPort-Targets]
			lappend downhnd_host $mcast_host_router
        }
	}
	if { [info exists uphnd_host]} {
		keylset upstream_handle $AffPort_upstream.host_handle $uphnd_host
	}
	if { [info exists uphnd_router]} {
		keylset upstream_handle $AffPort_upstream.router_handle $uphnd_router
	}
	if { [info exists downhnd_rtr]} {
		keylset downstream_handle $AffPort_downstream.router_handle $downhnd_rtr
	}
	if {[info exists downhnd_host]} {
		keylset downstream_handle $AffPort_downstream.host_handle $downhnd_host
	}
	
	#Streamblock handle - Getting/seperating stream handles after the expand..which inclues traffic config stream handles and wizard stream handles.
    set ports [::sth::sthCore::invoke stc::get project1 -children-port]
    foreach portHnd $ports {
	    set stream_handle [::sth::sthCore::invoke stc::get $portHnd -children-streamblock]
	    if { $stream_handle ne "" } {
			set poststream_handles($portHnd) "$stream_handle"
        }
    }
	#extracting/seperating wizard stream handles and appending to global variable ::sth::Traffic::arrayPortHnd($portHnd)
	foreach portHnd $ports {
		if {[info exists poststream_handles($portHnd)]} {
			set poststreams_list [split $poststream_handles($portHnd)]
			if {[info exists prestream_handles($portHnd)]} {
				foreach child $prestream_handles($portHnd) {
					set index [lsearch $poststreams_list $child]
					if { $index > -1 } {
						set expandstream($portHnd) [lreplace $poststreams_list $index $index]
					}
				}
				lappend ::sth::Traffic::arrayPortHnd($portHnd) $expandstream($portHnd)
				lappend return_stream $expandstream($portHnd)
			} else {
			        lappend ::sth::Traffic::arrayPortHnd($portHnd) $poststream_handles($portHnd)
					lappend return_stream $poststream_handles($portHnd)
			}
		}
	}
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        #9)set return value
        if { $upstream_handle ne "" } {
            keylset myreturnKeyedList upstream_handle $upstream_handle
        }
        if { $downstream_handle ne "" } {
            keylset myreturnKeyedList downstream_handle $downstream_handle
        }
		if {[string equal "$::sth::multicast_group::userArgsArray(create_traffic)" "true"]} {
            keylset myreturnKeyedList streamblock_handle $return_stream
        }
        keylset myreturnKeyedList handle $McastGenParamsHdl
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }    
    return $myreturnKeyedList
}

proc ::sth::multicast_group::emulation_mcast_wizard_config_delete {returnKeyedList} {
  
    upvar 1 $returnKeyedList myreturnKeyedList
    variable ::sth::multicast_group::userArgsArray
    set retVal [catch {
    #handle needed for delete mode
	if { ![::info exists ::sth::multicast_group::userArgsArray(handle)]} {
        ::sth::sthCore::processError myreturnKeyedList "handle needed for delete mode " {}
	    return $returnKeyedList
    }
	#Delete the handles provided by user
	if {[info exists ::sth::multicast_group::userArgsArray(handle)]} {
		foreach each_handle $::sth::multicast_group::userArgsArray(handle) {
			::sth::sthCore::invoke stc::delete $each_handle		
		}
	}    	
    } returnedString]
    if {$retVal} {
        ::sth::sthCore::processError myreturnKeyedList $returnedString {}
    } else {
        keylset myreturnKeyedList status $::sth::sthCore::SUCCESS 
    }
    return $myreturnKeyedList
}
