namespace eval ::sth::gre:: {
	array set v_gre_map {}
}


#format the gre object config string list
proc ::sth::gre_config {configList id } {
   upvar $configList greConfigList
   #puts $greConfigList
   set ipv4Version 4
   set ipv6Version 6
  
   array set GreConfigInfo $greConfigList
   set GreConfig [list]
   
   if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
      set version $ipv4Version
   } else {
      set version $ipv6Version
   }
   
   #if {[info exists GreConfigInfo(gre_tnl_addr_step)]} {
   #   set tnlStep $GreConfigInfo(gre_tnl_addr_step)
   #} else {
   #   if {$version == $ipv4Version} {
   #      set tnlStep "0.0.0.1"
   #   } else {
   #      set tnlStep "0:0:0:0:0:0:0:1"
   #   }
   #}
   #
   #if {$GreConfigInfo(gre_tnl_addr_count) != 1 } {
   #   set tnladdr [::sth::sthCore::updateIpAddress $version $GreConfigInfo(gre_tnl_addr) $tnlStep [expr $id-1]]
   #} else {
   #   set tnladdr $GreConfigInfo(gre_tnl_addr)
   #}
   #
   #if {[info exists GreConfigInfo(gre_src_addr_step)]} {
   #   set srcStep $GreConfigInfo(gre_src_addr_step)
   # } else {
   #   if{$version == $ipv4Version} {
   #      set srcStep "0.0.0.1"
   #   } else {
   #      set srcStep "0:0:0:0:0:0:0:1"
   #   }
   #}
   #
   #if {$GreConfigInfo(gre_src_addr_count) != 1 && $GreConfigInfo(gre_src_mode) != "fixed"} {
   #   set srcaddr [::sth::sthCore::updateIpAddress $version $GreConfigInfo(gre_src_addr) $srcStep [expr $id-1]]
   #} else {
   #   set srcaddr $GreConfigInfo(gre_src_addr)
   #}
   # 
   if {[info exists GreConfigInfo(gre_dst_addr_step)]} {
      set dstStep $GreConfigInfo(gre_dst_addr_step)
   } else {
      if {$version == $ipv4Version} {
         set dstStep "0.0.0.1"
      } else {
         set dstStep "0:0:0:0:0:0:0:1"
      }
   }

   if {$GreConfigInfo(gre_dst_addr_count) != 1 && $GreConfigInfo(gre_dst_mode) != "fixed"} {
      set dstaddr [::sth::sthCore::updateIpAddress $version $GreConfigInfo(gre_dst_addr) $dstStep [expr $id-1]]
   } else {
      set dstaddr $GreConfigInfo(gre_dst_addr)
   }
    
   foreach {attr val} [array get GreConfigInfo] {
        switch -- [string tolower $attr] {
            gre_checksum  { lappend GreConfig "-ChecksumEnabled" $val }
               
            gre_in_key           {
                lappend GreConfig "-InFlowKeyFieldEnabled" 1
                lappend GreConfig "-RxFlowKeyField" $val
            }
            gre_out_key           {
                lappend GreConfig "-OutFlowKeyFieldEnabled" 1
                lappend GreConfig "-TxFlowKeyField" $val }
            gre_dst_addr          {
                if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
                  lappend GreConfig "-RemoteTunnelEndPointV4" $dstaddr
                 } else {
                 lappend GreConfig "-RemoteTunnelEndPointV6" $dstaddr
                 }
            }
			gre_dst_addr_step     {
				if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
					lappend GreConfig "-RemoteTunnelEndPointV4Step" $dstStep
                } else {
					lappend GreConfig "-RemoteTunnelEndPointV6Step" $dstStep
                }
			}
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetVlanIntfSetup: $GreConfig"
    
    return $GreConfig       
			   
}


#format the gre deliver ip header config string list
proc ::sth::gre_ipif_config {configList id } {
   upvar $configList greConfigList
   #puts $greConfigList
   
   array set GreConfigInfo $greConfigList
    
   set ipv4Version 4
   set ipv6Version 6
   if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
      set version $ipv4Version
   } else {
      set version $ipv6Version
   }
  
   set GreipifConfig [list]
   
   if {$GreConfigInfo(gre_tnl_addr_count) != 1 } {
      set tnladdr [::sth::sthCore::updateIpAddress 4 $GreConfigInfo(gre_tnl_addr) $GreConfigInfo(gre_tnl_addr_step) [expr $id-1]]
   } else {
      set tnladdr $GreConfigInfo(gre_tnl_addr)
   }
   if {[info exists GreConfigInfo(gre_tnl_addr_step)]} {
        set tnladdrstep $GreConfigInfo(gre_tnl_addr_step)
   } else {
        set tnladdrstep 0.0.0.0
   }
   
   
   if {$GreConfigInfo(gre_src_addr_count) != 1 && $GreConfigInfo(gre_src_mode) != "fixed"} {
      set srcaddr [::sth::sthCore::updateIpAddress 4 $GreConfigInfo(gre_src_addr) $GreConfigInfo(gre_src_addr_step) [expr $id-1]]
   } else {
      set srcaddr $GreConfigInfo(gre_src_addr)
   }
   if {[info exists GreConfigInfo(gre_src_addr_step)]} {
        set srcaddrstep $GreConfigInfo(gre_src_addr_step)
   } else {
        set srcaddrstep 0.0.0.1
   }
   set prefix_len $GreConfigInfo(gre_prefix_len)

   #if {$GreConfigInfo(gre_dst_addr_count) != 1 && $GreConfigInfo(gre_dst_mode) != "fixed"} {
   #   set dstaddr [::sth::sthCore::updateIpAddress 4 $GreConfigInfo(gre_dst_addr) $GreConfigInfo(gre_dst_addr_step) [expr $id-1]]
   #} else {
   #   set dstaddr $GreConfigInfo(gre_dst_addr)
   #}
   #
   #if {[info exists GreConfigInfo(gre_dst_addr_step)]} {
   #   set dstStep $GreConfigInfo(gre_dst_addr_step)
   #} else {
   #   if {$version == $ipv4Version} {
   #      set dstStep "0.0.0.1"
   #   } else {
   #      set dstStep "0:0:0:0:0:0:0:1"
   #   }
   #}
   #
   #if {$GreConfigInfo(gre_dst_addr_count) != 1 && $GreConfigInfo(gre_dst_mode) != "fixed"} {
   #   set dstaddr [::sth::sthCore::updateIpAddress $version $GreConfigInfo(gre_dst_addr) $dstStep [expr $id-1]]
   #} else {
   #   set dstaddr $GreConfigInfo(gre_dst_addr)
   #}
   
   #set gwAddr [::sth::sthCore::getIpv4Gw $srcaddr]
   
   foreach {attr val} [array get GreConfigInfo] {
        switch -- [string tolower $attr] {
            gre_src_addr          {
               lappend GreipifConfig "-Address" $srcaddr
               lappend GreipifConfig "-AddrStep" $srcaddrstep
               lappend GreipifConfig "-Gateway" $tnladdr
               lappend GreipifConfig "-GatewayStep" $tnladdrstep
               lappend GreipifConfig "-PrefixLength" $prefix_len
               }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetVlanIntfSetup: $GreipifConfig"
    
    return $GreipifConfig       
}

proc ::sth::gredbd_config {configList} {
   upvar $configList greConfigList
   #puts $greConfigList
   set ipv4Version 4
   set ipv6Version 6
  
   array set GreConfigInfo $greConfigList
   set GreConfig [list]
   
   if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
      set version $ipv4Version
   } else {
      set version $ipv6Version
   }
 
   if {[info exists GreConfigInfo(gre_dst_addr_step)]} {
      set dstStep $GreConfigInfo(gre_dst_addr_step)
   } else {
      if {$version == $ipv4Version} {
         set dstStep "0.0.0.1"
      } else {
         set dstStep "0:0:0:0:0:0:0:1"
      }
   }

    if {[info exists GreConfigInfo(gre_dst_addr)]} {
      set dstaddr $GreConfigInfo(gre_dst_addr)
   }

   foreach {attr val} [array get GreConfigInfo] {
        switch -- [string tolower $attr] {
            gre_checksum  { lappend GreConfig "-ChecksumEnabled" $val }
               
            gre_in_key           {
                lappend GreConfig "-InFlowKeyFieldEnabled" 1
                lappend GreConfig "-RxFlowKeyField" $val
            }
            gre_out_key           {
                lappend GreConfig "-OutFlowKeyFieldEnabled" 1
                lappend GreConfig "-TxFlowKeyField" $val }
            gre_dst_addr          {
                if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
                  lappend GreConfig "-RemoteTunnelEndPointV4" $dstaddr
                 } else {
				  lappend GreConfig "-RemoteTunnelEndPointV6" $dstaddr
                 }
            }
			gre_dst_addr_step     {
			     if {$GreConfigInfo(gre_tnl_type) == $ipv4Version} {
                  lappend GreConfig "-RemoteTunnelEndPointV4Step" $dstStep
                 } else {
				  lappend GreConfig "-RemoteTunnelEndPointV6Step" $dstStep
                 }
			}
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetVlanIntfSetup: $GreConfig"
    
    return $GreConfig       		   
}


#create the gre protocol DBD
proc ::sth::createGreDbd {configList} {
    if {[info exist ::sth::gre::v_gre_map($configList)]} {
		set gredevice $::sth::gre::v_gre_map($configList)
	} else {
	   array set GreConfigInfo $configList
	   set ipv4Version 4
	   set ipv6Version 6
	   set returnKeyedList ""

	   set tunnelType $GreConfigInfo(gre_tnl_type)
	   if {$tunnelType == $ipv4Version} {
		  set ip_version ipv4
	   } else {
		  set ip_version ipv6
	   }
	   
	   switch -- $ip_version {
		  "ipv4"  {
			  set topif "Ipv4If"
			  set ifCount "1"
		  }
		  "ipv6"  {
			  set topif "Ipv6If"
			  set ifCount "1"
		  }
		  "ipv46" {
			  set topif "Ipv6If Ipv4If"
			  set ifCount "1 1"
		  }
		  "none" {
			  # the interface does not have the L3 layer encapsulation
			  set topif ""
			  set ifCount ""
		  }
	   }
			
	  set encap $GreConfigInfo(gre_encapsulation)
	   switch -- $encap {
			 "ethernet_ii" {
				 set IfStack "GreIf $topif EthIIIf"
				 set IfCount "1 $ifCount 1"
			 }
			 "ethernet_ii_vlan" {
				 set IfStack "GreIf $topif VlanIf EthIIIf"
				 set IfCount "1 $ifCount 1 1"
			 }
			 "ethernet_ii_qinq" {
				 set IfStack "GreIf $topif VlanIf VlanIf EthIIIf"
				 set IfCount "1 $ifCount 1 1 1"
			 }
			 default {
				 ::sth::sthCore::processError returnKeyedList "Error in emulation_gre_config: Invalid -encap $encap" {}
				 return -code error $returnKeyedList  
			 }
		 }
	   set port_handle $GreConfigInfo(gre_port_handle) 
	   #create the gre device
	   array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project)\
									 -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $port_handle -devicecount $GreConfigInfo(gre_count)]
	   set gredevice $DeviceCreateOutput(-ReturnList)
	   
	   #config the stack
	   set ethIIIf [::sth::sthCore::invoke stc::get $gredevice -children-EthIIIf]
	   ::sth::sthCore::invoke stc::config $ethIIIf -SourceMac $GreConfigInfo(gre_src_mac_addr)
	   if {[info exists GreConfigInfo(gre_src_mac_addr_step)]} {
                ::sth::sthCore::invoke stc::config $ethIIIf -SrcMacStep $GreConfigInfo(gre_src_mac_addr_step) } 
	   
	   if {[regexp "ethernet_ii_vlan" $encap]} {
		   set vlanIntf [::sth::sthCore::invoke stc::get $gredevice -children-VlanIf]
		   ::sth::gre::configVlanIfInner $configList $vlanIntf
	   } elseif {[regexp "ethernet_ii_qinq" $encap]} {
		   set vlanIntf [::sth::sthCore::invoke stc::get $gredevice -children-VlanIf]
		   ::sth::gre::configVlanIfInner $configList [lindex $vlanIntf 0]
		   ::sth::gre::configVlanIfOuter $configList [lindex $vlanIntf 1]
	   }

	   if {$tunnelType == $ipv4Version} {
		  set greIpIf [::sth::sthCore::invoke stc::get $gredevice -children-Ipv4If]
	   } else {
		  set greIpIf [::sth::sthCore::invoke stc::get $gredevice -children-Ipv6If]
	   }
	  
	   #config the gre stack
	   set greResultIf [::sth::sthCore::invoke stc::get $gredevice -children-GreIf]
	   set greIfSettings [::sth::gredbd_config configList]
	   if {[catch {::sth::sthCore::invoke stc::config $greResultIf $greIfSettings} error]} {
		 ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
		 return -code error $returnKeyedList
	   }
				   
	   set greipIfSettings [::sth::gre_ipif_config configList 0]
	   if {[catch {::sth::sthCore::invoke stc::config $greIpIf $greipIfSettings} error]} {
		  ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
		  return -code error  $returnKeyedList
	   }

		set ::sth::gre::v_gre_map($configList) $gredevice
	}
					
   return $gredevice     
}

proc ::sth::gre::configVlanIfInner {configList vlanIfHandle} {
   array set GreConfigInfo $configList
   set optionList ""
   if {[info exists GreConfigInfo(gre_vlan_id)]} {
      lappend optionList -VlanId $GreConfigInfo(gre_vlan_id)
   }
   
   if {[info exists GreConfigInfo(gre_vlan_id_step)]} {
      lappend optionList -IdStep $GreConfigInfo(gre_vlan_id_step)
   }
   
   if {[info exists GreConfigInfo(gre_vlan_id_count)]} {
      lappend optionList -IfRecycleCount $GreConfigInfo(gre_vlan_id_count)
   }
   if {[info exists GreConfigInfo(gre_vlan_user_priority)]} {
      lappend optionList -Priority $GreConfigInfo(gre_vlan_user_priority)
   }
   
   #qinq_incr_mode is outer/both by default
   lappend optionList -IdRepeatCount 0  
   ::sth::sthCore::invoke stc::config $vlanIfHandle $optionList
}


proc ::sth::gre::configVlanIfOuter {configList vlanIfHandle} {
   array set GreConfigInfo $configList
   set optionList ""
   if {[info exists GreConfigInfo(gre_vlan_outer_id)]} {
      lappend optionList -VlanId $GreConfigInfo(gre_vlan_outer_id)
   }
   
   if {[info exists GreConfigInfo(gre_vlan_id_step)]} {
      lappend optionList -IdStep $GreConfigInfo(gre_vlan_outer_id_step)
   }
   
   if {[info exists GreConfigInfo(gre_vlan_id_count)]} {
      lappend optionList -IfRecycleCount $GreConfigInfo(gre_vlan_outer_id_count)
   }
   
   if {[info exists GreConfigInfo(gre_vlan_outer_user_priority)]} {
      lappend optionList -Priority $GreConfigInfo(gre_vlan_outer_user_priority)
   }
   
   #qinq_incr_mode is outer/both by default
   lappend optionList -IdRepeatCount 0
   ::sth::sthCore::invoke stc::config $vlanIfHandle $optionList
}

#create the gre protocol stack
proc ::sth::createGreStack {configList routerHandle lowerIf rtID} {
   
    array set GreConfigInfo $configList
    set ipv4Version 4
    set ipv6Version 6
    set returnKeyedList ""
    
   #create the stack
   if {[catch {set greResultIf [::sth::sthCore::invoke stc::create GreIf -under $routerHandle]} error]} {
                ::sth::sthCore::processError returnKeyedList "Internal error creating GreIf: $error"
                return -code error $returnKeyedList
                }
		
               
   set tunnelType $GreConfigInfo(gre_tnl_type)
   if {$tunnelType == $ipv4Version} {
      if {[catch {set greIpIf [::sth::sthCore::invoke stc::create Ipv4If -under $routerHandle]} error]} {
	 ::sth::sthCore::processError returnKeyedList "Internal error creating GreIf: $error"
	 return -code error  $returnKeyedList
      }
   } else {
      if {[catch {set greIpIf [::sth::sthCore::invoke stc::create Ipv6If -under $routerHandle]} error]} {
	 ::sth::sthCore::processError returnKeyedList "Internal error creating GreIf: $error"
	 return -code error $returnKeyedList
      }
   }
   
   #config the gre stack    
   set greIfSettings [::sth::gre_config configList $rtID]
   if {[catch {::sth::sthCore::invoke stc::config $greResultIf $greIfSettings} error]} {
      ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
      return -code error $returnKeyedList
   }
                
   set greipIfSettings [::sth::gre_ipif_config configList $rtID]
   if {[catch {::sth::sthCore::invoke stc::config $greIpIf $greipIfSettings} error]} {
       ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
       return -code error  $returnKeyedList
   }
   
   #setup the relation          
   if {[catch {::sth::sthCore::invoke stc::config $greIpIf "-StackedOnEndpoint-targets $lowerIf"} error]} {
      ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
      return -code error $returnKeyedList 
   }
   if {[catch {::sth::sthCore::invoke stc::config $greResultIf "-StackedOnEndpoint-targets $greIpIf"} error]} {
      ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
      return -code error $returnKeyedList 
   }
                    
   set lowerIf $greResultIf
            
   return $lowerIf
         
}

#config the gre protocol stack
proc ::sth::configGreStack {configList router } {
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    set ipv4Version 4
    
    array set GreConfigInfo $configList
    
    set greTopIf [::sth::sthCore::invoke stc::get $router -TopLevelIf-targets]
    set greIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]
    set greIpIf [::sth::sthCore::invoke stc::get $greIf -StackedOnEndpoint-targets]
    set stackIf [::sth::sthCore::invoke stc::get $greIpIf -StackedOnEndpoint-targets]
    
    #delete existing gre ip header
    ::sth::sthCore::invoke stc::delete $greIpIf
    
    #create new gre ip header
    
    set tunnelType $GreConfigInfo(gre_tnl_type)
    if {$tunnelType == $ipv4Version} {
        if {[catch {set greIpIf [::sth::sthCore::invoke stc::create Ipv4If -under $router]} error]} {
            ::sth::sthCore::processError returnKeyedList "Internal error creating GreIf: $error"
            return $FAILURE
        }
    } else {
        if {[catch {set greIpIf [::sth::sthCore::invoke stc::create Ipv6If -under $router]} error]} {
            ::sth::sthCore::processError returnKeyedList "Internal error creating GreIf: $error"
            return $FAILURE 
        }
    }
    
    #config the object
    set greIfSettings [::sth::gre_config configList 0]
    if {[catch {::sth::sthCore::invoke stc::config $greIf $greIfSettings} error]} {
	::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
        return $FAILURE 
    }
                
    set greipIfSettings [::sth::gre_ipif_config configList 0]
    if {[catch {::sth::sthCore::invoke stc::config $greIpIf $greipIfSettings} error]} {
	::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
        return $FAILURE
    } 
           
    #modify the relation
    if {[catch {::sth::sthCore::invoke stc::config $greIpIf "-StackedOnEndpoint-targets $stackIf"} error]} {
	::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
        return $FAILURE
    }
    if {[catch {::sth::sthCore::invoke stc::config $greIf "-StackedOnEndpoint-targets $greIpIf"} error]} {
	::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
        return $FAILURE 
    }
    return $SUCCESS
    
}

#delete the gre ip header from the ipiflit
proc ::sth::deleteGreIP {ipIfList router } {
   
   set greIf [::sth::sthCore::invoke stc::get $router -children-greif]
   if {[llength $greIf] == 0} {
      return $ipIfList
   } else {
      set greIpIf [::sth::sthCore::invoke stc::get $greIf -StackedOnEndpoint-targets]
   
      set ipIf $ipIfList
   
      if {$greIpIf != ""} {
       set ix [lsearch -exact $ipIfList $greIpIf]
			if {$ix >=0 } {
				set ipIf [lreplace $ipIf $ix $ix]
			}
      }
   
      return $ipIf
   }
   
}

#To modify existing gre protocol DBD
proc ::sth::modifyGreDbd {configList} {
        set ipv4Version 4
           
        set configList [string replace $configList 0 0]
        set configList [string replace $configList end end]
        array set GreConfigInfo $configList
        array set OptionalGreConfig $GreConfigInfo(optional_args)
        
        array set configParam { }
        foreach idx [array names OptionalGreConfig] {
                set tempvalue $OptionalGreConfig($idx)
                set tempidx [string replace $idx 0 0]
                set configParam($tempidx) $tempvalue
        }
        set configlist [array get configParam]
           
	#To get GreHandle
	set gredev $OptionalGreConfig(-gre_handle)
        if {[ regexp "," $gredev ]} {
               set gredevicelist [split $gredev ,]
               set gredev $gredevicelist
        }
        set handlenum 0
        while {$handlenum<[llength $gredev]} {
                set gredevice [lindex $gredev $handlenum]
                #For gre_count 
                if { [ info exists OptionalGreConfig(-gre_count) ] } {
                        ::sth::sthCore::invoke stc::config $gredevice -devicecount $OptionalGreConfig(-gre_count)
                }   
                   
                #For gre_src_mac_addr
                if {[ info exists OptionalGreConfig(-gre_src_mac_addr) ]} {
                        set ethIIIf [::sth::sthCore::invoke stc::get $gredevice -children-EthIIIf]
                        ::sth::sthCore::invoke stc::config $ethIIIf -SourceMac $OptionalGreConfig(-gre_src_mac_addr)
                }
                
                #For gre_src_mac_addr_step
                if {[ info exists OptionalGreConfig(-gre_src_mac_addr_step) ]} {
                        set ethIIIf [::sth::sthCore::invoke stc::get $gredevice -children-EthIIIf]
                        ::sth::sthCore::invoke stc::config $ethIIIf -SrcMacStep $OptionalGreConfig(-gre_src_mac_addr_step)
                }
                        
                #To get ip version
                set childrenlist [::sth::sthCore::invoke stc::get $gredevice -children]
                if {[ regexp -nocase "Ipv4If" $childrenlist]} {
                        set version 4
                        lappend configlist gre_tnl_type 
                        lappend configlist 4
                } else {
                        set version 6
                        lappend configlist gre_tnl_type 
                        lappend configlist 6
                }
        
                if {[ regexp -nocase "VlanIf" $childrenlist]} {  
                        set vlanIntf [::sth::sthCore::invoke stc::get $gredevice -children-VlanIf]
                        if { [llength $vlanIntf] == 1 } {
                                set vlanIntf [::sth::sthCore::invoke stc::get $gredevice -children-VlanIf]
                                ::sth::gre::configVlanIfInner $configlist $vlanIntf
                        } elseif { [llength $vlanIntf] == 2 } {
                                set vlanIntf [::sth::sthCore::invoke stc::get $gredevice -children-VlanIf]
                                ::sth::gre::configVlanIfInner $configlist [lindex $vlanIntf 0]
                                ::sth::gre::configVlanIfOuter $configlist [lindex $vlanIntf 1]  
                        }
                }    
        
                set greResultIf [::sth::sthCore::invoke stc::get $gredevice -children-GreIf]
                if {![ regexp -nocase "gre_dst_addr_step" $configlist]} {
                        if {$version == $ipv4Version} {
                           lappend configlist gre_dst_addr_step 
                           lappend configlist [::sth::sthCore::invoke stc::get $greResultIf -RemoteTunnelEndPointV4Step]
                        } else {                       
                           lappend configlist gre_dst_addr_step 
                           lappend configlist [::sth::sthCore::invoke stc::get $greResultIf -RemoteTunnelEndPointV6Step]
                        }
                }
                set greIfSettings [::sth::gredbd_config configlist]
                if {[catch {::sth::sthCore::invoke stc::config $greResultIf $greIfSettings} error]} {
                        ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
                        return -code error $returnKeyedList
                }	   	
                #To get Ip interface
                if {$version == $ipv4Version} {
                        set greIpIf [::sth::sthCore::invoke stc::get $gredevice -children-Ipv4If]
                        if { [llength $greIpIf] > 1 } {
                                set greTopIf [::sth::sthCore::invoke stc::get $gredevice -TopLevelIf-targets]
                                set greIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]
                                set greIpIf [::sth::sthCore::invoke stc::get $greIf -StackedOnEndpoint-targets]
                        }
                } else {
                        set greIpIf [::sth::sthCore::invoke stc::get $gredevice -children-Ipv6If]
                        if { [llength $greIpIf] > 1 } {
                                set greTopIf [::sth::sthCore::invoke stc::get $gredevice -TopLevelIf-targets]
                                set greIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]
                                set greIpIf [::sth::sthCore::invoke stc::get $greIf -StackedOnEndpoint-targets]
                        }
                }
                if {![info exists OptionalGreConfig(-gre_tnl_addr)]} {
                           lappend configlist gre_tnl_addr 
                           lappend configlist [::sth::sthCore::invoke stc::get $greIpIf -Gateway ]    
                }
                if {![info exists OptionalGreConfig(-gre_tnl_addr_step)]} {
                           lappend configlist gre_tnl_addr_step 
                           lappend configlist [::sth::sthCore::invoke stc::get $greIpIf -GatewayStep ]    
                }
                if {![info exists OptionalGreConfig(-gre_tnl_addr_count)]} {
                           lappend configlist gre_tnl_addr_count 
                           lappend configlist 1    
                }
                if {![info exists OptionalGreConfig(-gre_src_addr_count)]} {
                           lappend configlist gre_src_addr_count 
                           lappend configlist 1    
                }
                if {![info exists OptionalGreConfig(-gre_src_mode)]} {
                           lappend configlist gre_src_mode 
                           lappend configlist "fixed"   
                }
                if {![info exists OptionalGreConfig(-gre_src_addr)]} {
                        lappend configlist gre_src_addr 
                        lappend configlist [::sth::sthCore::invoke stc::get $greIpIf -Address]
                }
                if {![info exists OptionalGreConfig(-gre_src_addr_step)]} {
                        lappend configlist gre_src_addr_step 
                        lappend configlist [::sth::sthCore::invoke stc::get $greIpIf -AddrStep]
                }
                if {![info exists OptionalGreConfig(-gre_prefix_len)]} {
                        lappend configlist gre_prefix_len 
                        lappend configlist [::sth::sthCore::invoke stc::get $greIpIf -PrefixLength]
                }
                set greipIfSettings [::sth::gre_ipif_config configlist 0]
                if {[catch {::sth::sthCore::invoke stc::config $greIpIf $greipIfSettings} error]} {
                        ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
                        return -code error  $returnKeyedList
                }    
                incr handlenum
        }
        return 0     
}

