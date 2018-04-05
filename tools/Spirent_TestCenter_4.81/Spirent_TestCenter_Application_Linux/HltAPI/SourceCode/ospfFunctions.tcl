# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::sthCore:: {
}

proc ::sth::ospf::calGateway {version ipaddr prefix} {
    #Make a fully qualified address to make things easy
    set ipList {}
    if {[regexp "4" $version]} {
        #set mask "[string repeat 1 $prefix][string repeat 0 [expr 32 - $prefix -1]]1"
        set octets [split $ipaddr .]
        if {[llength $octets] != 4} {
                set octets [lrange [concat $octets 0 0 0] 0 3]
        }
        set binIpAddress ""
        foreach oct $octets {
            binary scan [binary format c $oct] B* bin
            set binIpAddress "$binIpAddress$bin"
        }
        set gatewayIpAddress "[string range $binIpAddress 0 [expr $prefix -1]][string repeat 0 [expr 32 - $prefix -1]]1"
        for {set x 0; set y 7} {$y < 32} {} {
            set oct [string range $gatewayIpAddress $x $y]
            binary scan [binary format B32 $oct] i i
            lappend newIp $i
            set x [expr {$x+8}]
            set y [expr {$y+8}]
        }
        set r [join $newIp .]
    } else {
        set ipAddressValue [::sth::sthCore::normalizeIPv6Addr $ipaddr]
        set octets [split $ipAddressValue :]
        set binIpAddress ""
        foreach oct $octets {
            binary scan [binary format H4 $oct] B* bin
            set binIpAddress "$binIpAddress$bin"
        }
        set gwaddress "[string range $binIpAddress 0 [expr ($prefix -1)]][string repeat 0 [expr 128 - $prefix -1]]1"
        for {set x 0; set y 15} {$y < 128} {} {
            set oct [string range $gwaddress $x $y]
            binary scan [binary format B16 $oct] H* i
            lappend newGwIp $i
            set x [expr {$x+16}]
            set y [expr {$y+16}]
        }

        set returnGwIp [join $newGwIp :]
        set r ""
        foreach octet [split $returnGwIp :] {
            append r [format %X: 0x$octet]
        }
        set r [string trimright $r :]
        regsub {(?:^|:)0(?::0)+(?::|$)} $r {::} r
    }
    return $r

}

###/* \ingroup oSPFFunctions
###\fn proc ::sth::ospf::emulation_ospf_config_create { str switchArgs str mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to create an ospf object based on the user input.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_config_create {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_config_create {switchArgs mySortedPriorityList procPrefix} {

    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_config_create $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar ospfHandlesList ospfHandlesList
    upvar returnKeyedList returnKeyedList
    variable ipv4Version
    variable ::sth::sthCore::bfd_available_ipaddr

    # set conditional default values before creating ospf router sessions
    set networkType $userInputArgs(network_type)

    if {![info exists userInputArgs(option_bits)]} {
            set ::sth::ospf::flag_option_bits 0
            set userInputArgs(option_bits) 0x2
    }
    if {$networkType != "broadcast"} {
        if {![info exists userInputArgs(dead_interval)]} {
            set userInputArgs(dead_interval) 120
        }

        if {![info exists userInputArgs(hello_interval)]} {
            set userInputArgs(hello_interval) 30
        }
    } else {
        if {![info exists userInputArgs(dead_interval)]} {
            set userInputArgs(dead_interval) 40
        }

        if {![info exists userInputArgs(hello_interval)]} {
            set userInputArgs(hello_interval) 10
        }

        if {![info exists userInputArgs(router_priority)]} {
            set userInputArgs(router_priority) 0
        }
    }
    if {![info exists userInputArgs(gateway_ip_addr)]} {
        switch -exact -- $userInputArgs(session_type) {
            "ospfv2" {
                if {[info exists userInputArgs(intf_ip_addr)]&&[info exists userInputArgs(intf_prefix_length)]} {
                    set userInputArgs(gateway_ip_addr) [calGateway v4 $userInputArgs(intf_ip_addr) $userInputArgs(intf_prefix_length)]
                } else {
                    set userInputArgs(gateway_ip_addr) 192.85.1.1
                }
            }
            "ospfv3" {
                if {[info exists userInputArgs(intf_ip_addr)]&&[info exists userInputArgs(intf_prefix_length)]} {
                    set userInputArgs(gateway_ip_addr) [calGateway v6 $userInputArgs(intf_ip_addr) $userInputArgs(intf_prefix_length)]
                } else {
                    set userInputArgs(gateway_ip_addr) 2000:0:0:0:0:0:0:1
                }
            }
            default {
                ::sth::sthCore::processError returnKeyedList \
                        [concat "Setting gateway IP address failed: Unknown " \
                                "session_type " \
                                "\"$userInputArgs(session_type)\".  "] \
                        {}
                return $::sth::sthCore::FAILURE
            }
        }
    }

    # end of setting conditional default values

    if {[info exists userInputArgs(port_handle)]} {
        #setup global address/step/id params, put return value in 'device'
        if {[catch {set ret [set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]]} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
            return -code error $returnKeyedList
        }
        #setup ethernet mac address start
        if {[info exists userInputArgs(mac_address_start)]} {
            set deviceSettings "-NextMac $userInputArgs(mac_address_start)"
            ::sth::sthCore::invoke stc::config $device $deviceSettings
        }

        if {[info exists userInputArgs(count)]} {
            set ospfCount $userInputArgs(count)
        } else {
            # assuming defualt count value is 1
            set ospfCount 1
        }

        if {$ospfCount > 1} {

            #Check if intf_ip_addr_step & router_id_step are valid
            set ipv4StepList [list router_id_step]
            foreach param $ipv4StepList {
                if {[info exists userInputArgs($param)]} {
                    set tmpIp [split $userInputArgs($param) "\."]
                    set size [llength $tmpIp]
                    if {$size != 4 && $size != 1} {
                        ::sth::sthCore::processError returnKeyedList "Invalid value for $param: $userInputArgs($param)" {}
                        return $::sth::sthCore::FAILURE
                    }
                    if {$size == 1} {
                        #Check if non-negative integer
                        if {[string is integer $tmpIp] != 1 || $tmpIp < 0} {
                            ::sth::sthCore::processError returnKeyedList "Invalid value for $param: $userInputArgs($param)" {}
                            return $::sth::sthCore::FAILURE
                        }
                    } else {
                        #Check if valid ipv4 address
                        foreach tmp $tmpIp {
                            if {[string is integer $tmp] != 1 || $tmp < 0 || $tmp > 255} {
                                ::sth::sthCore::processError returnKeyedList "Invalid value for $param: $userInputArgs($param)" {}
                                return $::sth::sthCore::FAILURE
                            }
                        }
                    }
                }
            }

            if {[catch {set area_id_step $userInputArgs(area_id_step)}]} {
                set area_id_step 0
            }

            set intf_ip_addr_step $userInputArgs(intf_ip_addr_step)
            set gateway_ip_addr_step $userInputArgs(gateway_ip_addr_step)

            if {$userInputArgs(session_type) == "ospfv3"} {
                set instance_id_step $userInputArgs(instance_id_step)
            }

            # add qinq support
            if {[info exists userInputArgs(vlan_outer_id)] || [info exists userInputArgs(vlan_outer_user_priority)]} {
                if {[catch {set vlan_outer_id_mode $userInputArgs(vlan_outer_id_mode)}]} {
                    if {[catch {set vlan_id_step $userInputArgs(vlan_outer_id_step)}]} {
                        set vlan_outer_id_step 0
                    }
                } else {
                    if {[string equal -nocase $vlan_outer_id_mode increment]} {
                        if {[catch {set vlan_outer_id_step $userInputArgs(vlan_outer_id_step)}]} {
                            set vlan_outer_id_step 1
                        }
                    } else {
                        set vlan_outer_id_step 0
                    }
                }
            }

            if {[info exists userInputArgs(vlan_id)] || [info exists userInputArgs(vlan_cfi)] || [info exists userInputArgs(vlan_user_priority)]} {
                if {[catch {set vlan_id_mode $userInputArgs(vlan_id_mode)}]} {
                    if {[catch {set vlan_id_step $userInputArgs(vlan_id_step)}]} {
                        set vlan_id_step 0
                    }
                } else {
                    if {[string equal -nocase $vlan_id_mode increment]} {
                        if {[catch {set vlan_id_step $userInputArgs(vlan_id_step)}]} {
                            set vlan_id_step 1
                        }
                    } else {
                        set vlan_id_step 0
                    }
                }
            }

            #add for ATM
            if {[info exists userInputArgs(vci)] || [info exists userInputArgs(vpi)]} {
                if {[catch {set vpi_step $userInputArgs(vpi_step)}]} {
                    set vpi_step 1
                }
                if {[catch {set vci_step $userInputArgs(vci_step)}]} {
                    set vci_step 1
                }
            }

            if {[catch {set router_id_step $userInputArgs(router_id_step)}]} {
                set router_id_step 0
            }
            if {[catch {set ipv6_router_id_step $userInputArgs(ipv6_router_id_step)}]} {
                set ipv6_router_id_step 0
            } else {
                set temp_ipv6_router_id $userInputArgs(ipv6_router_id)
            }
        }

        set proj $::sth::GBLHNDMAP(project)
        #these contents are later altered, so save it for the next loop
        set temp_ip_addr $userInputArgs(intf_ip_addr)
        set temp_gateway_ip_addr $userInputArgs(gateway_ip_addr)

        if {$userInputArgs(session_type) == "ospfv3"} {
            set ipVersion $userInputArgs(ip_version)
        } else {
            set ipVersion 4
        }

        for {set i 0} { $i < $ospfCount } { incr i 1 } {
            if {$i > 0} {
                #increment attributes for consecutive ospf sessions
                if {$area_id_step > 0} {
                    if {[catch {::sth::ospf::incrementIPv4Address userInputArgs area_id $area_id_step} err]} {
                        ::sth::sthCore::processError returnKeyedList "::sth::ospf::incrementIPv4Address Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                }

               if {$router_id_step > 0} {
                    if {[catch {::sth::ospf::incrementIPv4Address userInputArgs router_id $router_id_step} err]} {
                        ::sth::sthCore::processError returnKeyedList "::sth::ospf::incrementIPv4Address Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                }
                if {$ipv6_router_id_step != 0} {
                    set userInputArgs(ipv6_router_id) $temp_ipv6_router_id
                    set userInputArgs(ipv6_router_id) [::sth::sthCore::updateIpAddress 6 \
                        $userInputArgs(ipv6_router_id) $userInputArgs(ipv6_router_id_step) $i]
                }

                #Incrementing mac address
                if {[info exists userInputArgs(mac_address_start)]} {
                    set srcMac $userInputArgs(mac_address_start)
                } else {
            ::sth::sthCore::processError returnKeyedList "mac_address_start is mandatory when count > 1: $err" {}
                        return $::sth::sthCore::FAILURE
                }
                set srcMacStep $userInputArgs(mac_address_step)
                set nextMac [::sth::sthCore::macStep $srcMac $srcMacStep $i]
                 set deviceSettings "-NextMac $nextMac"
                 ::sth::sthCore::invoke stc::config $device $deviceSettings

                if {$userInputArgs(session_type) == "ospfv3" && $instance_id_step > 0} {
                    set tempInstanceId $userInputArgs(instance_id)
                    set userInputArgs(instance_id) [expr {$tempInstanceId + $instance_id_step}]
                }

                if {$userInputArgs(session_type) == "ospfv2"} {
                    if {[catch {::sth::ospf::incrementIPv4Address userInputArgs intf_ip_addr $intf_ip_addr_step}]} {
                        ::sth::sthCore::processError returnKeyedList "::sth::ospf::incrementIPv4Address Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                    if {[catch {::sth::ospf::incrementIPv4Address userInputArgs gateway_ip_addr $gateway_ip_addr_step}]} {
                        ::sth::sthCore::processError returnKeyedList "::sth::ospf::incrementIPv4Address Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                } else {
                    set userInputArgs(intf_ip_addr) $temp_ip_addr
                    set userInputArgs(gateway_ip_addr) $temp_gateway_ip_addr
                    #this is where ipv6 interface and gateway addresses are configured
                    set userInputArgs(intf_ip_addr) [::sth::sthCore::updateIpAddress 6 \
                        $userInputArgs(intf_ip_addr) $userInputArgs(intf_ip_addr_step) $i]
                    set userInputArgs(gateway_ip_addr) [::sth::sthCore::updateIpAddress 6 \
                        $userInputArgs(gateway_ip_addr) $userInputArgs(gateway_ip_addr_step) $i]
                }

                    if {$ipVersion == "4_6"} {
                        set userInputArgs(intf_ipv4_addr) [::sth::sthCore::updateIpAddress 4 \
                            $userInputArgs(intf_ipv4_addr) $userInputArgs(intf_ipv4_addr_step) $i]
                        set userInputArgs(gateway_ipv4_addr) [::sth::sthCore::updateIpAddress 4 \
                            $userInputArgs(gateway_ipv4_addr) $userInputArgs(gateway_ipv4_addr_step) $i]
                    }

                # add qinq support
                if {[info exists userInputArgs(vlan_outer_id)]} {
                    set tempVlanOuterId $userInputArgs(vlan_outer_id)
                    set userInputArgs(vlan_outer_id) [expr {$tempVlanOuterId + $vlan_outer_id_step}]
                }

                if {[info exists userInputArgs(vlan_id)]} {
                    set tempVlanId $userInputArgs(vlan_id)
                    set userInputArgs(vlan_id) [expr {$tempVlanId + $vlan_id_step}]
                }

                if {[info exists userInputArgs(vci)] || [info exists userInputArgs(vpi)]} {
                    set tempVpi $userInputArgs(vpi)
                    set tempVci $userInputArgs(vci)
                    set userInputArgs(vpi) [expr {$tempVpi + $vpi_step}]
                    set userInputArgs(vci) [expr {$tempVci + $vci_step}]
                }
            }
            set routerHandle uncreatedRouterHandle

            #TODO
            #make sure if creating an ipv4/v6if is necessary
            if {$userInputArgs(session_type) == "ospfv2"} {
                set ipIf Ipv4If
            } elseif {$userInputArgs(session_type) == "ospfv3"} {
                    if {$ipVersion == "4_6"} {
                        set ipIf "Ipv6If Ipv4If"
                    } else {
                        set ipIf Ipv6If
                    }
            } else {
                set ipIf Ipv6If
            }

            # create unique ospf sessions regardless of ospfCount
            set portHandle $userInputArgs(port_handle)

            ##################################################
            if {[info exists userInputArgs(vpi)] || [info exists userInputArgs(vci)]} {
                set baseIf "Aal5If"
            } else {
                set baseIf "EthIIIf"
            }

            if {[info exists userInputArgs(vlan_id)] && $baseIf == "EthIIIf"} {
                if {[info exists userInputArgs(vlan_outer_id)]} {
                    set IfStack "$ipIf VlanIf VlanIf $baseIf"
                    set IfCount "1 1 1 1"
                } else {
                    # there is only vlan configuration
                    set IfStack "$ipIf VlanIf $baseIf"
                    set IfCount "1 1 1"
                }
            }  else {
                # No vlan configuration
                set IfStack "$ipIf $baseIf"
                set IfCount "1 1"
            }

            if {$ipVersion == "4_6"} {
                lappend IfCount "1"
            }

            if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $proj -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set routerHandle $DeviceCreateOutput(-ReturnList)} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::perform DeviceCreate Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }

            ###add for gre
            if {[info exists userInputArgs(tunnel_handle)]} {
                set greTopIf [::sth::sthCore::invoke stc::get $routerHandle -TopLevelIf-targets]
                set greLowerIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]

                #create the gre stack and setup the relation
                if {[catch {::sth::createGreStack $userInputArgs(tunnel_handle) $routerHandle $greLowerIf [expr $i +1]} greIf]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::createGreStack Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }

                #stack the top ipif on the greif
                ::sth::sthCore::invoke stc::config $greTopIf "-StackedOnEndpoint-targets $greIf"

                #store the gre delivery header for futher use
                set ::sth::ospf::greIpHeader [::sth::sthCore::invoke stc::get $greIf -StackedOnEndpoint-targets]
            }
            #end

            #######################################################
            # For Ipv6, there must be two Ipv6Ifs under the router:
            # One for local link and one for global link
            # Add the local link to the IfStack
            if {$userInputArgs(session_type) == "ospfv3"} {

                if {$ipVersion == "4_6"} {
                    #get the stack if that global ipv4if stack on
                    if {[catch {set GlobalIpHandle [::sth::sthCore::invoke stc::get $routerHandle -children-ipv4if]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Get Ethernet Interface failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                } else {
                    #get the stack if that global ipv6if stack on
                    if {[catch {set GlobalIpHandle [::sth::sthCore::invoke stc::get $routerHandle -children-ipv6if]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Get Ethernet Interface failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                }
                if {[catch {set IpBaseHandle [::sth::sthCore::invoke stc::get $GlobalIpHandle -StackedOnEndpoint-targets]} err]} {
                    ::sth::sthCore::processError returnKeyedList "Get Ethernet Interface failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
                # attach another Ipv6If
                if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $routerHandle -IfStack "Ipv6If" -IfCount "1" -AttachToIf $IpBaseHandle} err]} {
                    ::sth::sthCore::processError returnKeyedList "add locallink Ipv6If Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
                # assign the link local address
                if {[catch {set ipv6ifList [::sth::sthCore::invoke stc::get $routerHandle -children-ipv6if]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$switchName* Internal command error while getting the Ipv6 interface handle, error msg: $getStatus" {}
                    return $::sth::sthCore::FAILURE
                } else {
                    set ipv6ifLocal [lindex $ipv6ifList 1]
#                    set link64BitAddr [::sth::sthCore::getNext64BitNumber]
#                    set linkLocalIp "FE80:0:0:0"
#                    foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
#                        append linkLocalIp ":$num1$num2$num3$num4"
#                    }
                    if {[catch {
                        ::sth::sthCore::invoke stc::config $ipv6ifLocal -Address FE80::2
                        ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true
                    } configStatus]} {
                        ::sth::sthCore::processError returnKeyedList "$switchName* Internal command error while setting the IPv6 link local address" {}
                        return $::sth::sthCore::FAILURE
                    }
                }

                if {$ipVersion == "4_6"} {
                    #get the stack if that global ipv4if stack on
                    if {[catch {set ipv4If [::sth::sthCore::invoke stc::get $routerHandle -children-ipv4if]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Get Ipv4If failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                    if {[catch {::sth::sthCore::invoke stc::config $ipv4If "-StackedOnEndpoint-targets $IpBaseHandle"} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                        return -code error $returnKeyedList
                    }
                    set ipv6If [lindex $ipv6ifList 0]
                    if {[catch {::sth::sthCore::invoke stc::config $ipv6If "-StackedOnEndpoint-targets $IpBaseHandle"} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                        return -code error $returnKeyedList
                    }
                    if {[catch {::sth::sthCore::invoke stc::config $routerHandle "-TopLevelIf-targets \"$ipv6ifList $ipv4If\""} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                        return -code error $returnKeyedList
                    }
                }
            }
            ######################################################
            if {$userInputArgs(session_type) == "ospfv2"} {
                set ospfversion ospfv2
                set hOSPFRouterHandle uncreatedOSPFHandle

                if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $routerHandle  -CreateClassId [string tolower Ospfv2RouterConfig]]
                              set hOSPFRouterHandle $ProtocolCreateOutput(-ReturnList)} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolCreate $err" {}
                    return $::sth::sthCore::FAILURE
                }

                ::sth::sthCore::invoke stc::config $hOSPFRouterHandle Options 0x42
            } else {
                set ospfversion ospfv3
                set hOSPFRouterHandle uncreatedOSPFHandle

                if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $routerHandle  -CreateClassId [string tolower Ospfv3RouterConfig]]
                              set hOSPFRouterHandle $ProtocolCreateOutput(-ReturnList)} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolCreate $err" {}
                    return $::sth::sthCore::FAILURE
                }

                #TODO
                #must add V6Bit
                ::sth::sthCore::invoke stc::config $hOSPFRouterHandle Options 0x13
            }



            #set bfd_avaliable_ipaddr for validating BFD ipaddr
            set ::sth::sthCore::bfd_available_ipaddr($routerHandle) ""

            #enable/disable BFD
            if {[info exists userInputArgs(bfd_registration)]} {
                configBfdRegistration $routerHandle $userInputArgs(mode) userInputArgs

                #bfd relation
                set bfdRtrCfg [::sth::sthCore::invoke stc::get $routerHandle -children-bfdrouterconfig]
                if {[llength $bfdRtrCfg] != 0} {
                if {[catch {set ipResultIf [::sth::sthCore::invoke stc::get $routerHandle -PrimaryIf-Targets]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
                    return -code error $returnKeyedList
                }
                if {$userInputArgs(session_type) == "ospfv3"} {
                    foreach ipif $ipResultIf {
                        set addr [::sth::sthCore::invoke stc::get  $ipif -Address]
                        if {![regexp -nocase "FE80" $addr] } {
                            set ipResultIf $ipif
                            break
                        }
                    }
                }
                ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
                }
            }
            # BFD end

            lappend ospfHandlesList $hOSPFRouterHandle
            set intf_ip_addrValue $userInputArgs(intf_ip_addr)

            if { [catch {set ret [::sth::ospf::configOSPFRouter $procPrefix $hOSPFRouterHandle userInputArgs sortedPriorityList]} err] } {
                ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFRouter Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
            if {$ret == $::sth::sthCore::FAILURE} {
                ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFRouter Failed: $returnKeyedList"
                return $ret
            }
        }
    } else {
        #RXu: Enable OSPF under an existing Device.
        set routerHandle $userInputArgs(handle)
        #modify the source mac address and the ethernet mac address start
        if {[info exists userInputArgs(mac_address_start)]} {
            if {[catch {set ret [set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]]} error]} {
             ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
             return -code error $returnKeyedList
            }
            set srcMac $userInputArgs(mac_address_start)
            set srcMacStep $userInputArgs(mac_address_step)
            set nextMac [::sth::sthCore::macStep $srcMac $srcMacStep 1]
             set deviceSettings "-NextMac $nextMac"
            ::sth::sthCore::invoke stc::config $device $deviceSettings
            set ethiff [::sth::sthCore::invoke stc::get $routerHandle -children-EthIIIf]

            set ethiffSettings "-SourceMac $srcMac"
            if {$ethiff == ""} {
                ::sth::sthCore::invoke stc::create EthIIIf -under $routerHandle $ethiffSettings
            } else {
                ::sth::sthCore::invoke stc::config $ethiff $ethiffSettings
            }
        }
        set ipResultIf [::sth::sthCore::invoke stc::get $routerHandle -PrimaryIf-Targets]
        if {$userInputArgs(session_type) == "ospfv3"} {
            foreach ipif $ipResultIf {
                set addr [::sth::sthCore::invoke stc::get  $ipif -Address]
                if {![regexp -nocase "FE80" $addr] } {
                    set ipResultIf $ipif
                    break
                }
            }
        } elseif {[llength $ipResultIf]>1} {
            # the ipiflist is more than one only when the ipv6 interface/dual stack is configured on the device
            foreach ipif $ipResultIf {
                if {[regexp -nocase {ipv4if(\d+)?$} $ipif]} {
                    set ipResultIf $ipif
                    break
                }
            }
        }
        set deviceName [::sth::sthCore::invoke stc::get $routerHandle -Name]
        if {$deviceName eq "port_address"} {
            ###if handle is generated from interface_config
            ###need care about the gateway address
            foreach hname {tunnel_handle router_id intf_ip_addr intf_prefix_length vci vlan_cfi vlan_id vlan_user_priority vlan_outer_id vlan_outer_user_priority vpi} {
                if {[info exists userInputArgs($hname)]} {
                        unset userInputArgs($hname)
                }
            }
        } else {
            foreach hname {tunnel_handle router_id intf_ip_addr gateway_ip_addr intf_prefix_length vci vlan_cfi vlan_id vlan_user_priority vlan_outer_id vlan_outer_user_priority vpi} {
                if {[info exists userInputArgs($hname)]} {
                        unset userInputArgs($hname)
                }
            }
        }

        if {$userInputArgs(session_type) == "ospfv2"} {
            set hOSPFRouterHandle uncreatedOSPFHandle
            array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $routerHandle  -CreateClassId [string tolower Ospfv2RouterConfig]]
            set hOSPFRouterHandle $ProtocolCreateOutput(-ReturnList)
            ::sth::sthCore::invoke stc::config $hOSPFRouterHandle Options 0x02
        } else {
            set hOSPFRouterHandle uncreatedOSPFHandle
            if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $routerHandle  -CreateClassId [string tolower Ospfv3RouterConfig]]
                              set hOSPFRouterHandle $ProtocolCreateOutput(-ReturnList)} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolCreate $err" {}
                    return $::sth::sthCore::FAILURE
            }
            ::sth::sthCore::invoke stc::config $hOSPFRouterHandle Options 0x13
        }
        set ospfHandlesList $hOSPFRouterHandle
        ::sth::sthCore::invoke stc::config $hOSPFRouterHandle "-UsesIf-targets $ipResultIf"
        if { [catch {set ret [::sth::ospf::configOSPFRouter $procPrefix $hOSPFRouterHandle userInputArgs sortedPriorityList]} err] } {
                 ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFRouter Failed: $err" {}
                return -code error $returnKeyedList
        }

        #set bfd_avaliable_ipaddr for validating BFD ipaddr
        set ::sth::sthCore::bfd_available_ipaddr($routerHandle) ""
        #enable/disable BFD
        if {[info exists userInputArgs(bfd_registration)]} {
            configBfdRegistration $routerHandle $userInputArgs(mode) userInputArgs
            #bfd relation
            set bfdRtrCfg [::sth::sthCore::invoke stc::get $routerHandle -children-bfdrouterconfig]
            if {[llength $bfdRtrCfg] != 0} {
                ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
            }
        }
    }
    #Enable OSPF under an existing device. End

    if {[catch {set ret [::sth::sthCore::doStcApply]} err] } {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup oSPFFunctions
###\fn proc ::sth::ospf::emulation_ospf_config_modify { array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to modify an ospf object based on the user input.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_config_modify {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_config_modify {switchArgs mySortedPriorityList procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_config_modify $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList
    upvar ospfHandlesList ospfHandlesList
    upvar $mySortedPriorityList sortedPriorityList
    variable ipv4Version

    set ospfHandle $userInputArgs(handle)

    if {![info exists userInputArgs(option_bits)]} {
            set ::sth::ospf::flag_option_bits 0
    }
    #modify the source mac address and the ethernet mac address start
    if {[info exists userInputArgs(mac_address_start)]} {
        if {[catch {set ret [set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]]} error]} {
         ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
         return -code error $returnKeyedList
        }
         set srcMac $userInputArgs(mac_address_start)
         set srcMacStep 1
         if {[info exists userInputArgs(mac_address_step)]} {
            set srcMacStep $userInputArgs(mac_address_step)
         }
         set nextMac [::sth::sthCore::macStep $srcMac $srcMacStep 1]
         set deviceSettings "-NextMac $nextMac"
         ::sth::sthCore::invoke stc::config $device $deviceSettings
         set routerhandle [::sth::sthCore::invoke stc::get $ospfHandle -parent]
         set ethiff [::sth::sthCore::invoke stc::get $routerhandle -children-EthIIIf]
         set ethiffSettings "-SourceMac $srcMac"
         ::sth::sthCore::invoke stc::config $ethiff $ethiffSettings
    }
    ###add for gre. config the gre objects here
    if {[info exists userInputArgs(tunnel_handle)] != 0} {
        if {[catch {::sth::sthCore::invoke stc::get  $ospfHandle -parent} routerHandle]} {
            return -code 1 -errorcode -1 $routerHandle;
        }

        if {[catch {::sth::configGreStack  $userInputArgs(tunnel_handle) $routerHandle} err]} {
            return -code error "unable to config gre stack"
        }
    }

    lappend ospfHandlesList $ospfHandle

    #enable/disable BFD
    if {[info exists userInputArgs(bfd_registration)]} {
        set rtrHandle [::sth::sthCore::invoke stc::get $ospfHandle -parent]
        configBfdRegistration $rtrHandle $userInputArgs(mode) userInputArgs
    }
    if {[catch {set ret [::sth::ospf::configOSPFRouter $procPrefix $ospfHandle userInputArgs sortedPriorityList]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFRouter Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }
    if { $ret == $::sth::sthCore::FAILURE } {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFRouter Failed: $err"
        return $ret
    }
    if {[catch {set ret [::sth::sthCore::doStcApply]} err] } {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }
    return $::sth::sthCore::SUCCESS
}

###/* \ingroup oSPFFunctions
###\fn proc ::sth::ospf::emulation_ospf_config_disable { array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to disable an ospf object.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_config_disable {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_config_inactive {switchArgs mySortedPriorityList procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_config_inactive $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar ospfHandlesList ospfHandlesList
    upvar returnKeyedList returnKeyedList

    set ospfHandle $userInputArgs(handle)
    lappend ospfHandlesList $ospfHandle

    if {[catch {::sth::sthCore::invoke stc::config $ospfHandle "-Active FALSE -LocalActive FALSE"} err]} {
            ::sth::sthCore::processError returnKeyedList "Failed to inactive OSPF protocol: $err" {}
            return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup oSPFFunctions
###\fn proc ::sth::ospf::emulation_ospf_config_enable { array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to enable an ospf object.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_config_active {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_config_active {switchArgs mySortedPriorityList procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_config_active $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar ospfHandlesList ospfHandlesList
    upvar returnKeyedList returnKeyedList

    set ospfHandle $userInputArgs(handle)
    lappend ospfHandlesList $ospfHandle

    if {[catch {::sth::sthCore::invoke stc::config $ospfHandle "-Active TRUE -LocalActive TRUE"} err]} {
            ::sth::sthCore::processError returnKeyedList "Failed to active OSPF protocol: $err" {}
            return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup oSPFFunctions
###\fn proc ::sth::ospf::emulation_ospf_config_delete { array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to delete an ospf object.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_config_delete {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_config_delete {switchArgs mySortedPriorityList procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_config_delete $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList
    #delete the router object, not the ospfv2routerconfig/ospfv3routerconfig object
    set ospfHandle1 $userInputArgs(handle)
    set ospfHandle [::sth::sthCore::invoke stc::get $ospfHandle1 -parent]
    if {[catch {set ret [::sth::sthCore::invoke stc::delete $ospfHandle]} err] } {
            ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }
    if {$ret == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err"
            return $ret
    }

    set ret [catch {::sth::sthCore::doStcApply} err]

    if {$ret} {
        ::sth::sthCore::processError returnKeyedList $err {}
        return $::sth::sthCore::FAILURE
    }

        return $::sth::sthCore::SUCCESS
}


proc ::sth::ospf::emulation_ospf_config_activate { switchArgs mySortedPriorityList procPrefix } {
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar ospfHandlesList ospfHandlesList
    upvar returnKeyedList returnKeyedList
    variable ipv4Version

    array set mainDefaultAry {}
    set opList "area_id area_id_step graceful_restart_enable graceful_restart_type network_type router_priority option_bits"
    foreach key $opList {
        if {[info exists ::sth::ospf::$procPrefix\_default($key)]} {
            set value [set ::sth::ospf::$procPrefix\_default($key)]
            set mainDefaultAry($key) $value
        }
    }
    set opList "authentication_mode password md5_key_id"
    foreach key $opList {
        if {[info exists ::sth::ospf::$procPrefix\_default($key)]} {
            set value [set ::sth::ospf::$procPrefix\_default($key)]
            set authDefaultAry($key) $value
        }
    }

    set mOptionList ""
    set authOptionList ""
    foreach idx [array names mainDefaultAry] {
        if {[info exists userInputArgs($idx)]} {
            if {[info exists ::sth::ospf::$procPrefix\_$idx\_fwdmap($userInputArgs($idx))]} {
                set value [set ::sth::ospf::$procPrefix\_$idx\_fwdmap($userInputArgs($idx))]
                set userInputArgs($idx) $value
            }
            set mainDefaultAry($idx) $userInputArgs($idx)
        }
        if {[string equal $mainDefaultAry($idx) "_none_"]} { continue }
        regsub -all {[.]} [set ::sth::ospf::$procPrefix\_stcattr($idx)] "" stcAttr
        append mOptionList " -$stcAttr $mainDefaultAry($idx)"
    }

    foreach idx [array names authDefaultAry] {
        if {[info exists userInputArgs($idx)]} {
            set authDefaultAry($idx) $userInputArgs($idx)
        }
        if {[string equal $authDefaultAry($idx) "_none_"]} { continue }
        append authOptionList " -[set ::sth::ospf::$procPrefix\_stcattr($idx)] $authDefaultAry($idx)"
    }
        
    if {![info exists userInputArgs(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the activate mode of emulation_ospf_config" {}
        return $FAILURE
    } else {
        if {[string equal -nocase $userInputArgs(session_type) ospfv2]} {
            set ospfGenHnd [::sth::sthCore::invoke stc::create Ospfv2DeviceGenProtocolParams -under $userInputArgs(handle) $mOptionList]
            set authHnd [::sth::sthCore::invoke stc::get $ospfGenHnd -children-ospfv2AuthenticationParams]
            if { $authOptionList != "" } {
                ::sth::sthCore::invoke stc::config $authHnd $authOptionList
            }
        } elseif {[string equal -nocase $userInputArgs(session_type) ospfv3]} {
            set ospfGenHnd [::sth::sthCore::invoke stc::create Ospfv3DeviceGenProtocolParams -under $userInputArgs(handle) $mOptionList]
        }
        
        if {[info exists userInputArgs(expand)] &&
            $userInputArgs(expand) == "false"} {
            keylset returnKeyedList handle_list ""
        } else {
            array set return [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $userInputArgs(handle)]
            keylset returnKeyedList handle_list $return(-ReturnList)
            array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv2RouterConfig -rootlist $return(-ReturnList)]
            set ospfv2HndList $rtn(-ObjectList)
            array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3RouterConfig -rootlist $return(-ReturnList)]
            set ospfv3HndList $rtn(-ObjectList)
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList ospfv2_handle_list $ospfv2HndList]
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList ospfv3_handle_list $ospfv3HndList]
        }
    }

    return $::sth::sthCore::SUCCESS
}




###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_lsa_config_create {array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to create a ospf lsa based on the user input.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_lsa_config_create {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_lsa_config_create {switchArgs mySortedPriorityList procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_lsa_config_create $switchArgs $mySortedPriorityList $procPrefix"
    upvar $mySortedPriorityList sortedPriorityList
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    set lsaType $userInputArgs(type)
    set stcLsaType [::sth::sthCore::getFwdmap ::sth::ospf:: $procPrefix type $lsaType]

    set lsaHandle ""

    #make sure that te_tlv_type exists before an object of teLSA is created
    if {$stcLsaType == "TeLsa"} {
        if {![info exists userInputArgs(te_tlv_type)]} {
                ::sth::sthCore::processError returnKeyedList "Error: te_tlv_type not provided for -mode create" {}
                return $::sth::sthCore::FAILURE
        }
    }

    if {[catch { set ret [set lsaHandle [::sth::sthCore::invoke stc::create $stcLsaType -under $userInputArgs(handle)]] } err] } {
            ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }

    if {$stcLsaType == "TeLsa"} {
        set teType $userInputArgs(te_tlv_type)
        set stcTeType [::sth::sthCore::getFwdmap ::sth::ospf:: $procPrefix te_tlv_type $teType]

        if {[catch { set ret [set tlvHandle [::sth::sthCore::invoke stc::create $stcTeType -under $lsaHandle]] } err] } {
                ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }
    }

    set extLsaType empty
    if {[string first ospfv2 [string tolower $userInputArgs(handle)]] >= 0} {
        set type Type
        if {$lsaType == "nssa_ext_pool"} {
            set extLsaType NSSA
        } elseif {$lsaType == "ext_pool"} {
            set extLsaType EXT
        }
    } else {
        set type LsType
        if {$lsaType == "nssa_ext_pool"} {
            set extLsaType NSSA_LSA
        } elseif {$lsaType == "ext_pool"} {
            set extLsaType AS_EXT_LSA
        }
    }


    if {$extLsaType != "empty"} {
        ::sth::sthCore::invoke stc::config $lsaHandle -$type $extLsaType
    }

    switch -exact -- [string tolower $lsaType] {
        "asbr_summary" {
            set userInputArgs(asbr_router_id) $userInputArgs(adv_router_id)
            lappend sortedPriorityList [list 0 asbr_router_id]
        }
        "router_info" {
            if {![info exists userInputArgs(router_info_opaque_type)]} {
                set userInputArgs(router_info_opaque_type) router_information
                lappend sortedPriorityList [list 0 router_info_opaque_type]
            }
        }
        "extended_prefix" {
            if {![info exists userInputArgs(extended_prefix_opaque_type)]} {
                set userInputArgs(extended_prefix_opaque_type) extended_prefix
                lappend sortedPriorityList [list 0 extended_prefix_opaque_type]
            }
        }
        "extended_link" {
            if {![info exists userInputArgs(extended_link_opaque_type)]} {
                set userInputArgs(extended_link_opaque_type) extended_link
                lappend sortedPriorityList [list 0 extended_link_opaque_type]
            }
        }
    }

    if {[catch {set ret [::sth::ospf::configOSPFLsa $procPrefix $lsaHandle userInputArgs sortedPriorityList]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFLsa Failed: $err" {}
        return $::sth::sthCore::FAILURE
    } else {
        if { $::sth::sthCore::FAILURE == $ret } {
            ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFLsa Failed: $err"
            return $ret
        }
    }

    set adv unknown
    if {[info exists userInputArgs(adv_router_id)]} {
        set adv $userInputArgs(adv_router_id)
    } else {
        if {[catch {set ret [set adv [::sth::sthCore::invoke stc::get $lsaHandle AdvertisingRouterId]]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
    }

    keylset returnKeyedList lsa_handle $lsaHandle
    keylset returnKeyedList adv_router_id $adv

    if {$userInputArgs(return_detail)} {
        switch $lsaType {
            network {
                if { [catch {set ret [::sth::ospf::encodeNetworkLsaAndLinks $lsaHandle network $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeNetworkLsaAndLinks Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            router {
                if { [catch {set ret [::sth::ospf::encodeRouterLsaAndLinks $lsaHandle router $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeRouterLsaAndLinks Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            summary_pool {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle summary $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            intra_area_prefix {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle intraarea $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            ext_pool {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle external $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            nssa_ext_pool {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle nssa $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            asbr_summary {
                if { [catch {set ret [::sth::ospf::encodeLsaCommon $lsaHandle asbrsummary $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeLsaCommon Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            opaque_type_10 {
                if { [catch {set ret [::sth::ospf::encodeTeLsaAndTlvs $lsaHandle opaque_type_10 $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeTeLsaAndTlvs Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
        }
    }

    variable ospfLsaTypeInfo

    set ospfLsaTypeInfo($lsaHandle) [string tolower $stcLsaType]

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_lsa_config_reset {array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to reset a ospf whose handle is -lsa_handle.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_lsa_config_reset {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_lsa_config_reset {switchArgs mySortedPriorityList procPrefix} {

    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_lsa_config_reset $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList
    upvar $mySortedPriorityList sortedPriorityList


    set ospfHandle $userInputArgs(handle)

    if {[catch {set ret [set childList [::sth::sthCore::invoke stc::get $ospfHandle children]]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    foreach elem $childList {
        if {[regexp -nocase "ospfv2simplifiedsrlsa" $elem] == 0 && [string first "lsa" $elem] >= 0 || [string first "Lsa" $elem] >= 0} {
            if {[catch {set ret [::sth::sthCore::invoke stc::delete $elem]} err] } {
                ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
                return $::sth::sthCore::FAILURE
            }
        }
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_lsa_config_delete {array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
### This procedure is used to delete a ospf lsa whose handle is specified by -lsa_handle.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_lsa_config_delete {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_lsa_config_delete {switchArgs mySortedPriorityList procPrefix} {

    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_lsa_config_delete $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar returnKeyedList returnKeyedList

    set lsaHandle $userInputArgs(lsa_handle)

    if {[catch {set ret [::sth::sthCore::invoke stc::delete $lsaHandle]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }
    if {$ret == $::sth::sthCore::FAILURE} {
        ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err"
        return $ret
    }

    set ret [catch {
       variable ospfLsaTypeInfo
       if {[info exists ospfLsaTypeInfo($lsaHandle)]} {
            unset ospfLsaTypeInfo($lsaHandle)
       }
    } err]

    if {$ret} {
       ::sth::sthCore::processError returnKeyedList [concat "Error:  Unable " \
             "to find internal LSA type information for LSA " \
             "\"$userInputArgs(lsa_handle)\".  "] \
             {}
       return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_lsa_config_modify {array switchArgs list mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to modify the switches of a ospf lsa based on the user input.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_lsa_config_modify {switchArgs mySortedPriorityList procPrefix}
proc ::sth::ospf::emulation_ospf_lsa_config_modify {switchArgs mySortedPriorityList procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_lsa_config_modify $switchArgs $mySortedPriorityList $procPrefix"
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar returnKeyedList returnKeyedList

    set lsaHandle $userInputArgs(lsa_handle)

    if {[catch {set ret [set name [::sth::sthCore::invoke stc::get $lsaHandle name]]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    if {[info exists userInputArgs(type)]} {
            set lsaType $userInputArgs(type)
    } else {
            set oType [lindex $name 0]
            set lsaType [::sth::sthCore::getRvsmap ::sth::ospf:: $procPrefix type $oType]
    }

    switch -exact -- [string tolower $lsaType] {
        "asbr_summary" {
            if {[info exists userInputArgs(adv_router_id)]} {
                set userInputArgs(asbr_router_id) $userInputArgs(adv_router_id)
                lappend sortedPriorityList [list 0 asbr_router_id]
            }
        }
    }

    if {[catch {set ret [::sth::ospf::configOSPFLsa $procPrefix $lsaHandle userInputArgs sortedPriorityList]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::configOSPFLsa Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    if {$ret == $::sth::sthCore::FAILURE} {
        ::sth::sthCore::log error "::sth::ospf::configOSPFLsa Failed: $err"
        return $ret
    }

    set adv unknown
    if {[info exists userInputArgs(adv_router_id)]} {
            set adv $userInputArgs(adv_router_id)
    } else {
        if {[catch {set ret [set adv [::sth::sthCore::invoke stc::get $lsaHandle AdvertisingRouterId]]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
    }

    keylset returnKeyedList lsa_handle $lsaHandle
    keylset returnKeyedList adv_router_id $adv

    if {$userInputArgs(return_detail)} {
        switch $lsaType {
            network {
                if { [catch {set ret [::sth::ospf::encodeNetworkLsaAndLinks $lsaHandle network $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeNetworkLsaAndLinks Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            router {
                if { [catch {set ret [::sth::ospf::encodeRouterLsaAndLinks $lsaHandle router $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeRouterLsaAndLinks Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            summary_pool {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle summary $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            intra_area_prefix {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle intraarea $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            ext_pool {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle external $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            nssa_ext_pool {
                if { [catch {set ret [::sth::ospf::encodeSumPoolPrefixes $lsaHandle nssa $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeSumPoolPrefixes Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            asbr_summary {
                if { [catch {set ret [::sth::ospf::encodeLsaCommon $lsaHandle asbrsummary $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeLsaCommon Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            opaque_type_10 {
                if { [catch {set ret [::sth::ospf::encodeTeLsaAndTlvs $lsaHandle opaque_type_10 $procPrefix userInputArgs] } err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::ospf::encodeTeLsaAndTlvs Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
        }
    }

    if {[catch {set ret [::sth::sthCore::doStcApply]} err] } {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    if {[catch {
       variable ospfLsaTypeInfo
       set ospfLsaTypeInfo($lsaHandle) [string tolower [::sth::sthCore::getFwdmap ::sth::ospf:: $procPrefix type $lsaType]]
    } err]} {
       ::sth::sthCore::processError returnKeyedList [concat "Failed: Unable to record OSPF LSA's type information."] {}
       keylset returnKeyedList log $err

        return $::sth::sthCore::FAILURE
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::ospf::emulation_ospf_tlv_config_create { userArray  returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ospf_tlv_config_create"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $userArray userArgsArray;
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    set procPrefix "emulation_ospf_tlv_config"

    set retVal [catch {

        switch -exact -- $userArgsArray(type) {
            extended_link_tlv     -
            adj_sid_tlv           -
            lan_adj_sid_tlv       -
            ipv4_ero_tlv          -
            ero_tlv               -
            sid_label_binding_tlv -
            prefix_sid_tlv        -
            extended_prefix_tlv   -
            sid_label_range_tlv   -
            algorithm_tlv {
                set tlvType $userArgsArray(type)
                set stcTlvType [::sth::sthCore::getFwdmap ::sth::ospf:: $procPrefix type $tlvType]
                set tlvHnd [::sth::sthCore::invoke stc::create $stcTlvType -under $userArgsArray(handle)]

                sth::ospf::configOSPFTlv $procPrefix $tlvHnd userArgsArray

                if {($userArgsArray(type) == "sid_label_range_tlv") ||
                    ($userArgsArray(type) == "adj_sid_tlv") ||
                    ($userArgsArray(type) == "lan_adj_sid_tlv") ||
                    ($userArgsArray(type) == "sid_label_binding_tlv")} {
                    set tlvSubHnd [::sth::sthCore::invoke stc::get $tlvHnd -children-SidLabelTlv]
                    ::sth::ospf::configOSPFTlv $procPrefix $tlvSubHnd userArgsArray
                } elseif { $userArgsArray(type) == "ipv4_ero_tlv"} {
                    set tlvSubHnd [::sth::sthCore::invoke stc::get $tlvHnd -children-Ipv4NetworkBlock]
                    ::sth::ospf::configOSPFTlv $procPrefix $tlvSubHnd userArgsArray
                }

                keylset returnKeyedList handle $tlvHnd
            }
            default {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::emulation_ospf_tlv_config_create Failed: Unknown Type($type)" {}
                return $::sth::sthCore::FAILURE
            }
        }

    } returnedString]

    if {$retVal} {
       ::sth::sthCore::processError returnKeyedList $returnedString {}
       keylset returnKeyedList status $::sth::sthCore::FAILURE
    }

    return $returnKeyedList
}


proc ::sth::ospf::emulation_ospf_tlv_config_modify { userArray  returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ospf_tlv_config_modify"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $userArray userArgsArray;
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    set procPrefix "emulation_ospf_tlv_config"
    set tlvHnd $userArgsArray(handle)

    set retVal [catch {

        switch -exact -- $userArgsArray(type) {
            extended_link_tlv     -
            adj_sid_tlv           -
            lan_adj_sid_tlv       -
            ipv4_ero_tlv          -
            ero_tlv               -
            sid_label_binding_tlv -
            prefix_sid_tlv        -
            extended_prefix_tlv   -
            sid_label_range_tlv   -
            algorithm_tlv {
                ::sth::ospf::configOSPFTlv $procPrefix $tlvHnd userArgsArray

                if {($userArgsArray(type) == "sid_label_range_tlv") ||
                    ($userArgsArray(type) == "adj_sid_tlv") ||
                    ($userArgsArray(type) == "lan_adj_sid_tlv") ||
                    ($userArgsArray(type) == "sid_label_binding_tlv")} {
                    set tlvSubHnd [::sth::sthCore::invoke stc::get $tlvHnd -children-SidLabelTlv]
                    ::sth::ospf::configOSPFTlv $procPrefix $tlvSubHnd userArgsArray
                } elseif { $userArgsArray(type) == "ipv4_ero_tlv"} {
                    set tlvSubHnd [::sth::sthCore::invoke stc::get $tlvHnd -children-Ipv4NetworkBlock]
                    ::sth::ospf::configOSPFTlv $procPrefix $tlvSubHnd userArgsArray
                }

                keylset returnKeyedList handle $tlvHnd
            }
            default {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::emulation_ospf_tlv_config_create Failed: Unknown Type($type)" {}
                return $::sth::sthCore::FAILURE
            }
        }

    } returnedString]

    if {$retVal} {
       ::sth::sthCore::processError returnKeyedList $returnedString {}
       keylset returnKeyedList status $::sth::sthCore::FAILURE
    }

    return $returnKeyedList
}


proc ::sth::ospf::emulation_ospf_tlv_config_delete { userArray  returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ospf_tlv_config_delete"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $userArray userArgsArray;
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    set tlvHnd $userArgsArray(handle)

    ::sth::sthCore::invoke stc::delete $tlvHnd

    return $returnKeyedList
}


###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_control_withdraw_lsa {array switchArgs} {
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to restart(stop,then start) a ospf specified by -handle and -port_handle
###
###\param[in] switchArgs contains the user input
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_control_withdraw_lsa {switchArgs}
proc ::sth::ospf::emulation_ospf_control_withdraw_lsa {switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_control_withdraw_lsa $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    set withdrawLsaValue $userInputArgs(withdraw_lsa)

    foreach lsaHandle $withdrawLsaValue {
        if {[catch {set ret [::sth::sthCore::invoke stc::delete $lsaHandle]} err] } {
            ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
    }

    if {[catch {set ret [::sth::sthCore::invoke stc::apply]} err] } {
        ::sth::sthCore::processError returnKeyedList "stc::apply Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}


###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_control_age_lsa {array switchArgs} {
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to restart(stop,then start) a ospf specified by -handle and -port_handle
###
###\param[in] switchArgs contains the user input
###
###Author: Fanfei
###
###*/
###::sth::ospf::emulation_ospf_control_age_lsa {switchArgs}
proc ::sth::ospf::emulation_ospf_control_age_lsa {switchArgs} {
    variable ospfLsaTypeInfo
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_control_age_lsa $switchArgs"

    set retVal [catch {
        upvar $switchArgs userInputArgs
        upvar returnKeyedList returnKeyedList

        set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $::sth::sthCore::GBLHNDMAP(sequencer)]

        catch { unset readvertiseCmds }
        set ageLsaValue $userInputArgs(age_lsa)

        foreach lsa $ageLsaValue {
            set lsa_handle $lsa
            if {[info exists ospfLsaTypeInfo]} {
                set lsa_handle $ospfLsaTypeInfo($lsa)
            }
            set lsaParent [::sth::sthCore::invoke stc::get $lsa -parent]

            # Determine session type
            switch -regexp -- [string tolower $lsaParent] {
                 {^ospfv2} {
                     set sessionType 2
                     set tableName emulation_ospfv2_control
                 }
                 {^ospfv3} {
                     set sessionType 3
                     set tableName emulation_ospfv3_control
                 }
                 default {
                     ::sth::sthCore::processError returnKeyedList \
                     [concat "Error:  Unable to determine session " \
                           "type using LSA's object information.  Possible " \
                           "that object's name format was changed " \
                           "internally.  "] {}
                     return $::sth::sthCore::FAILURE
                 }
             }

             # Create the appropriate LSA command
            switch $sessionType {
                2 {
                    switch -exact -- $lsa_handle {
                        "asbrsummarylsa" {
                           set lsaCmd "Ospfv2AgeAsbrLsaCommand"
                        }
                        "externallsablock" {
                           set lsaCmd "Ospfv2AgeExternalLsaCommand"
                        }
                        "routerlsa" {
                           set lsaCmd "Ospfv2AgeRouterLsaCommand"
                        }
                        "networklsa" {
                           set lsaCmd "Ospfv2AgeNetworkLsaCommand"
                        }
                        "telsa" {
                           set lsaCmd "Ospfv2AgeTeLsaCommand"
                        }
                        "summarylsablock" {
                           set lsaCmd "Ospfv2AgeSummaryLsaCommand"
                        }
                        "extendedprefixlsa" -
                        "extendedlinklsa"   -
                        "routerinfolsa" {
                           set lsaCmd "Ospfv2AgeOpaqueLsaCommand"
                        }
                        default {
                            if {[info exists ospfLsaTypeInfo]} {
                                ::sth::sthCore::processError returnKeyedList \
                                        [concat "Error:  Unable to flap LSAs " \
                                        "on OSPFv2 session $userArgsArray(handle).  " \
                                        "Unable to determine LSA type of LSA handle " \
                                        "\"$lsa\".  "] {}
                                return $::sth::sthCore::FAILURE
                            } else {
                                ::sth::sthCore::log hltcall "skip $lsa_handle when do aging LSAs on OSPFv2 session $userArgsArray(handle)."
                                ::sth::sthCore::outputConsoleLog warning "skip $lsa_handle when do aging LSAs on OSPFv2 session $userArgsArray(handle)."
                            }
                        }
                    }
                }
                3 {
                    switch -exact -- $lsa_handle {
                        "ospfv3interarearouterlsablock" {
                           set lsaCmd "Ospfv3AgeInterAreaRouterLsaCommand"
                        }
                        "ospfv3asexternallsablock" {
                           set lsaCmd "Ospfv3AgeExternalLsaCommand"
                        }
                        "ospfv3routerlsa" {
                           set lsaCmd "Ospfv3AgeRouterLsaCommand"
                        }
                        "ospfv3networklsa" {
                           set lsaCmd "Ospfv3AgeNetworkLsaCommand"
                        }
                        "ospfv3nssalsablock" {
                           set lsaCmd "Ospfv3AgeNssaLsaCommand"
                        }
                        "ospfv3interareaprefixlsablk" {
                           set lsaCmd "Ospfv3AgeInterAreaPrefixLsaCommand"
                        }
                        default {
                            if {[info exists ospfLsaTypeInfo]} {
                                ::sth::sthCore::processError returnKeyedList \
                                    [concat "Error:  Unable to flap LSAs " \
                                    "on OSPFv3 session $userArgsArray(handle).  " \
                                    "Unable to determine LSA type of LSA handle " \
                                    "\"$lsa\".  "] {}
                                return $::sth::sthCore::FAILURE
                            } else {
                                ::sth::sthCore::log hltcall "skip $lsa_handle when do aging LSAs on OSPFv3 session $userArgsArray(handle)."
                                ::sth::sthCore::outputConsoleLog warning "skip $lsa_handle when do aging LSAs on OSPFv3 session $userArgsArray(handle)."
                            } 
                        }
                    }
                }
                default {
                   ::sth::sthCore::processError returnKeyedList \
                         [concat "Error:  Unable to determine session " \
                               "type using LSA's object information"] {}
                   return $::sth::sthCore::FAILURE
                }
            }

            if {[info exists ospfLsaTypeInfo]} {
                lappend lsaCmds($lsaCmd) $lsa
            }
        }

        catch {unset cmdList}

        # Age LSA command
        foreach lsaCmd [array names lsaCmds] {
            if {[regexp -nocase "extendedprefixlsa" $lsaCmds($lsaCmd)]  ||
                [regexp -nocase "routerinfolsa" $lsaCmds($lsaCmd)]  ||
                [regexp -nocase "extendedlinklsa" $lsaCmds($lsaCmd)]} {
                foreach lsaHnd $lsaCmds($lsaCmd) {
                   switch -regexp -- [string tolower $lsaHnd] {
                       "extendedprefixlsa" {
                           lappend cmdList [::sth::sthCore::invoke stc::create $lsaCmd -under $seqLoopCmd -lsaList $lsaHnd -Type EXTENDED_PREFIX]
                       }
                       "extendedlinklsa"   {
                           lappend cmdList [::sth::sthCore::invoke stc::create $lsaCmd -under $seqLoopCmd -lsaList $lsaHnd -Type EXTENDED_LINK]
                       }
                       default {
                           lappend cmdList [::sth::sthCore::invoke stc::create $lsaCmd -under $seqLoopCmd -lsaList $lsaHnd]
                       }
                   }
                }
            } else {
                lappend cmdList [::sth::sthCore::invoke stc::create $lsaCmd -under $seqLoopCmd [list "-lsaList" $lsaCmds($lsaCmd)]]
            }
        }

        # Configure sequencer
        ::sth::sthCore::invoke stc::config $seqLoopCmd [list "-CommandList" $cmdList]

        ::sth::sthCore::invoke stc::config $::sth::sthCore::GBLHNDMAP(sequencer) "-CommandList $seqLoopCmd"

        #::sth::sthCore::doStcApply

        # Start the sequencer
        ::sth::sthCore::invoke stc::perform sequencerStart
        #if we don't wait here, the clean up will delete the sequencer object
        ::sth::sthCore::invoke ::stc::waituntilcomplete

        # Clean up
        foreach cmd $cmdList {
              ::sth::sthCore::invoke stc::delete $cmd
        }
        ::sth::sthCore::invoke stc::delete $seqLoopCmd

    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_control_readvertise_lsa {array switchArgs} {
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to restart(stop,then start) a ospf specified by -handle and -port_handle
###
###\param[in] switchArgs contains the user input
###
###Author: Fanfei
###
###*/
###::sth::ospf::emulation_ospf_control_readvertise_lsa {switchArgs}
proc ::sth::ospf::emulation_ospf_control_readvertise_lsa {switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_control_readvertise_lsa $switchArgs"

    set retVal [catch {
        upvar $switchArgs userInputArgs
        upvar returnKeyedList returnKeyedList

        set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $::sth::sthCore::GBLHNDMAP(sequencer)]

        catch { unset readvertiseCmds }

        set readvertiseLsaValue $userInputArgs(readvertise_lsa)

        foreach lsa $readvertiseLsaValue {
            set lsaParent [::sth::sthCore::invoke stc::get $lsa -parent]

             # Determine session type
             switch -regexp -- [string tolower $lsaParent] {
                 {^ospfv2} {
                     set sessionType 2
                     set tableName emulation_ospfv2_control
                 }
                 {^ospfv3} {
                     set sessionType 3
                     set tableName emulation_ospfv3_control
                 }
                 default {
                     ::sth::sthCore::processError returnKeyedList \
                     [concat "Error:  Unable to determine session " \
                           "type using LSA's object information.  Possible " \
                           "that object's name format was changed " \
                           "internally.  "] {}
                     return $::sth::sthCore::FAILURE
                 }
             }

             # Create the appropriate LSA command
             switch $sessionType {
                 2 {
                     set readvertiseCmds($lsaParent) "Ospfv2ReadvertiseLsaCommand"
                 }
                 3 {
                     set readvertiseCmds($lsaParent) "Ospfv3ReadvertiseLsaCommand"
                 }
                 default {
                    ::sth::sthCore::processError returnKeyedList \
                          [concat "Error:  Unable to determine session " \
                                "type using LSA's object information"] {}
                    return $::sth::sthCore::FAILURE
                 }
             }
         }

        catch {unset cmdList}

        # Readvertise LSA command
        catch {unset readvertiseRtrCmds}
        foreach rtr [array names readvertiseCmds] {
           lappend readvertiseRtrCmds($readvertiseCmds($rtr)) $rtr
        }
        foreach readvertiseRtrCmd [array names readvertiseRtrCmds] {
          lappend cmdList [::sth::sthCore::invoke stc::create $readvertiseRtrCmd -under $seqLoopCmd [list "-routerList" $readvertiseRtrCmds($readvertiseRtrCmd)]]
        }

        # Configure sequencer
        ::sth::sthCore::invoke stc::config $seqLoopCmd [list "-CommandList" $cmdList]

        ::sth::sthCore::invoke stc::config $::sth::sthCore::GBLHNDMAP(sequencer) "-CommandList $seqLoopCmd"

        #::sth::sthCore::doStcApply

        # Start the sequencer
        ::sth::sthCore::invoke stc::perform sequencerStart
        #if we don't wait here, the clean up will delete the sequencer object
        ::sth::sthCore::invoke ::stc::waituntilcomplete

        # Clean up
        foreach cmd $cmdList {
              ::sth::sthCore::invoke stc::delete $cmd
        }
        ::sth::sthCore::invoke stc::delete $seqLoopCmd

    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}


###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_control_stop {array switchArgs} {
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to stop a ospf specified by -handle and -port_handle
###
###\param[in] switchArgs contains the user input
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_control_stop
proc ::sth::ospf::emulation_ospf_control_stop {switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_control_stop $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    #port_handle always takes precendence over ospf handle
    if {![catch {set portHandles $userInputArgs(port_handle)} err] } {
    foreach portHandle $portHandles {
        if {[catch {set ret [set rHandles [::sth::sthCore::invoke stc::get $portHandle affiliationport-Sources]]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }

        if {[catch {set ret [::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $rHandles]} err] } {
            ::sth::sthCore::processError returnKeyedList "stc::perform DeviceStop -DeviceList $portHandle Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        }
    }

    if {[info exists userInputArgs(handle)]} {
        set ospfHandles $userInputArgs(handle)
        foreach ospfHandle $ospfHandles {
        if {[catch {set iStatus [::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $ospfHandle] } err]} {
            ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolStop -ProtocolList $ospfHandle Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        }
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_control_start {array switchArgs} {
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to start a ospf specified by -handle and -port_handle
###
###\param[in] switchArgs contains the user input
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_control_start
proc ::sth::ospf::emulation_ospf_control_start {switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_control_start $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    #port_handle always takes precendence over ospf handle
    if {![catch {set portHandles $userInputArgs(port_handle)} err] } {
    foreach portHandle $portHandles {
        if {[catch {set ret [set rHandles [::sth::sthCore::invoke stc::get $portHandle affiliationport-Sources]]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }

        if {[catch {set ret [::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $rHandles]} err] } {
                ::sth::sthCore::processError returnKeyedList "stc::perform DeviceStart -DeviceList $rHandles Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }
        }
    }

    #The port_handle is not specified, start the ospf router specified.
    if {[info exist userInputArgs(handle)] } {
        set ospfHandles $userInputArgs(handle)
        foreach ospfHandle $ospfHandles {
        if {[catch {set ret [::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $ospfHandle] } err ] } {
                ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolStart -ProtocolList $ospfHandle Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }
        }
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::emulation_ospf_control_restart {array switchArgs} {
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS
###
###This procedure is used to restart(stop,then start) a ospf specified by -handle and -port_handle
###
###\param[in] switchArgs contains the user input
###
###Author: Fadi Hassan
###
###*/
###::sth::ospf::emulation_ospf_control_restart
proc ::sth::ospf::emulation_ospf_control_restart {switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::emulation_ospf_control_restart $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    #port_handle always takes precendence over ospf handle
    if {![catch {set portHandles $userInputArgs(port_handle)} err] } {
    foreach portHandle $portHandles {
        if {[catch {set ret [set rHandles [::sth::sthCore::invoke stc::get $portHandle affiliationport-Sources]]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }

        if {[catch {set ret [::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $rHandles]} err] } {
            ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolStop Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }

        if {[catch {set ret [::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $rHandles]} err] } {
            ::sth::sthCore::processError returnKeyedList "stc::perform DeviceStart -DeviceList $portHandle Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        }
    }

    if {[info exist userInputArgs(handle)] } {
        set ospfHandles $userInputArgs(handle)
        foreach ospfHandle $ospfHandles {
        if {[catch {set ret [::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $ospfHandle] } err] } {
            ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolStop Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }

        if {[catch {set ret [::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $ospfHandle] } err] } {
            ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolStart Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        }
    }

    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup sthOSPFFunctions
###\fn ::sth::ospf::determineLsaLinkType { string switchName string ospfversion string myLsaLinkType }
###\brief Returns $::sth::sthCore::FAILURE or return $::sth::sthCore::SUCCESS
###
###
###\param[in] swtichName contains the name of the switch.
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###\param[out] myLsaLinkType contains LSA link type
###
###
###\author: Davison Zhang and modified by Fadi Hassan
###*/
###
### ::sth::ospf::determineLsaLinkType { switchName procPrefix myLsaLinkType }
###
###
proc ::sth::ospf::determineLsaLinkType { switchName procPrefix myLsaLinkType } {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::determineLsaLinkType $switchName $procPrefix $myLsaLinkType"
    upvar $myLsaLinkType LinkTypeName
    #Determine which link type name to use for creating the lsa link.
    if {[string first "_ospfv2_" $procPrefix ] >= 0 } {
        if { [string equal -nocase $switchName net_attached_router] } {
                set LinkTypeName networklsalink
        } else {
            if { [string equal -nocase $switchName router_link_mode] } {
                set LinkTypeName routerlsalink
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: Link Type is neither net_attached_router nor router_link_mode" {}
                return $::sth::sthCore::FAILURE
            }
        }
    } elseif {[string first "_ospfv3_" $procPrefix ] >= 0 } {
        if { [string equal -nocase $switchName net_attached_router] } {
            set LinkTypeName Ospfv3AttachedRouter
        } else {
            if { [string equal -nocase $switchName router_link_mode] } {
                set LinkTypeName Ospfv3RouterLsaIf
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: Link Type is neither net_attached_router nor router_link_mode" {}
                return $::sth::sthCore::FAILURE
            }
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "Internal Error: Invalid procPrefix: $procPrefix" {}
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup sthOSPFFunctions
###\fn proc ::sth::ospf::doProcessLsaLink {str procPrefix str lsaHandle str switchName str switchValue str myHLsaLink array myUserInputArgs}
###\brief Returns return $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This process creates, delete or reset lsa link.
###
###
###\param [in] procPrefix contains the subcommand table name and the version number of the session
###\param [in] lsaHandle under which the lsa link handle is created.
###\param [in] switchName is the switch name representing the lsa link.
###\param [in] switchValue is the swtich value (create)
###\param [in] myUserInputArgs contains an array of switch values indexed by switch names.
###\param [out] myHLsaLink will contain the handle of the created lsa link
###
###
###\author: Davison Zhang and modified by Fadi Hassan
###*/
###
###\ proc ::sth::ospf::doProcessLsaLink { procPrefix lsaHandle switchName switchValue myHLsaLink myUserInputArgs}
###
###
proc ::sth::ospf::doProcessLsaLink { procPrefix lsaHandle switchName switchValue myHLsaLink myUserInputArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::doProcessLsaLink $procPrefix $lsaHandle $switchName $switchValue $myHLsaLink $myUserInputArgs"
    upvar returnKeyedList returnKeyedList
    upvar $myHLsaLink hLsaLink
    upvar $myUserInputArgs userInputArgs

    variable LinkTypeName
    variable router_link_idxValue
    variable hLinkIdvalue
    variable iLsaLinkCount
    variable attached_router_idValue

    set attached_router_idValue ""
    set iLsaLinkCount ""
    set hLinkIdvalue ""
    set router_link_idxValue ""
    set LinkTypeName ""

    if { [catch {set ret [::sth::ospf::determineLsaLinkType $switchName $procPrefix LinkTypeName] } err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::determineLsaLinkType $switchName $procPrefix LinkTypeName FAILED: $err" {}
        return $::sth::sthCore::FAILURE
    } else {
        if { $::sth::sthCore::FAILURE == $ret } {
            ::sth::sthCore::processError returnKeyedList "::sth::ospf::determineLsaLinkType $switchName $procPrefix LinkTypeName FAILED: $err"
            return $::sth::sthCore::FAILURE
        }
    }

    if {[info exists userInputArgs(router_link_count)]} {
        set router_link_count $userInputArgs(router_link_count)
    } else {
        set router_link_count 1
    }

    # Handle the lsa link: create, delete or reset.
    switch $switchValue {
        create {
            for {set i 1} {$i<=$router_link_count } {incr i 1} {
                set thLsaLink invalidLsaLinkHandle
                if { [catch {set iStatus [set thLsaLink [::sth::sthCore::invoke stc::create $LinkTypeName -under $lsaHandle]] } err ]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return $::sth::sthCore::FAILURE
                } else {
                    if { $thLsaLink < 0 } {
                        ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                }
                lappend hLsaLink $thLsaLink
            }
        }
        delete -
        reset {
            if { ![catch {set ret1 [set hLsaLinkItr [::sth::sthCore::invoke stc::get $lsaHandle children]] } error1]} {
                foreach elem $hLsaLinkItr {
                    if { [string equal -nocase $switchValue reset] } {
                        if {[catch {set ret2 [::sth::sthCore::invoke stc::delete $elem] } err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::delete $elem FAILED: $err" {}
                            return $::sth::sthCore::FAILURE
                        }
                    } else {
                        if { [string equal -nocase $LinkTypeName routerlsalink] || [string equal -nocase $LinkTypeName Ospfv3RouterLsaIf] } {
                            set routerLinkId $userInputArgs(router_link_id)

                            if {[catch {set ret [set lid [::sth::sthCore::invoke stc::get $elem LinkId]]} err]} {
                                ::sth::sthCore::processError returnKeyedList "stc::get LinkId $elem lid FAILED: $err" {}
                                return $::sth::sthCore::FAILURE
                            }

                            if {$ret == $::sth::sthCore::FAILURE} {
                                ::sth::sthCore::processError returnKeyedList "stc::get LinkId $elem lid FAILED: $err"
                                return $ret
                            }

                            if {[string equal -nocase $routerLinkId $lid]} {
                                if {[catch {set ret [::sth::sthCore::invoke stc::delete $elem]} err]} {
                                    ::sth::sthCore::processError returnKeyedList "stc::delete $elem FAILED: $err" {}
                                    return $::sth::sthCore::FAILURE
                                }

                                if {$ret == $::sth::sthCore::FAILURE} {
                                    ::sth::sthCore::processError returnKeyedList "stc::delete $elem FAILED: $err"
                                    return $ret
                                }
                            }
                        } else {
                            if {[string equal -nocase $LinkTypeName networklsalink] || [string equal -nocase $LinkTypeName Ospfv3AttchedRouter] } {
                                set attachedRouterId $userInputArgs(attached_router_id)

                                if {[catch {set ret [set lid [::sth::sthCore::invoke stc::get $elem LinkId]]} err]} {
                                    ::sth::sthCore::processError returnKeyedList "stc::get LinkId $elem lid FAILED: $err" {}
                                    return $::sth::sthCore::FAILURE
                                }

                                if {$ret == $::sth::sthCore::FAILURE} {
                                    ::sth::sthCore::processError returnKeyedList "stc::get LinkId $elem lid FAILED: $err"
                                    return $ret
                                }

                                if {[string equal -nocase $attachedRouterId $lid]} {
                                    if {[catch {set ret [::sth::sthCore::invoke stc::delete $elem]} err]} {
                                        ::sth::sthCore::processError returnKeyedList "stc::delete $elem FAILED: $err" {}
                                        return $::sth::sthCore::FAILURE
                                    }

                                    if {$ret == $::sth::sthCore::FAILURE} {
                                        ::sth::sthCore::processError returnKeyedList "stc::delete $elem FAILED: $err"
                                        return $ret
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Incorrect mode" {}
            return $::sth::sthCore::FAILURE
        }
    }
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::configOSPFLsa ( str procPrefix str lsaHandle str myuserInputArgs str mySortedPriorityList )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to configure ospf LSA switches from the user input.
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] lsaHandle contains the ospf lsa handle.
###\param[in] myuserInputArgs contains the array of switch values indexed by switch names.
###\param[in] mySortedPriorityList contains the list of switch priority/name pairs.
###*/
###::sth::ospf::configOSPFLsa ( procPrefix lsaHandle myuserInputArgs mySortedPriorityList)
proc ::sth::ospf::configOSPFLsa {procPrefix lsaHandle myuserInputArgs mySortedPriorityList} {

    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::configOSPFLsa $procPrefix $lsaHandle $myuserInputArgs $mySortedPriorityList"
    upvar $mySortedPriorityList sortedPriorityList
    upvar $myuserInputArgs userInputArgs
    upvar returnKeyedList returnKeyedList
    set networkBlock ""
    set bLsaLinkHandleUsed false
    set hLsaLink empty1

    if {[string first _ospfv2_ $procPrefix] >= 0} {
        set sessionType ospfv2
        set netBlockType ipv4networkblock
    } else {
        set sessionType ospfv3
        set netBlockType ipv6networkblock
    }

    if {$userInputArgs(mode) == "create"} {
        set lsaType $userInputArgs(type)
    } else {
        #make sure this works, otherwise remove line below and uncomment above block
        upvar lsaType lsaType
    }

    if { [string equal -nocase $lsaType summary_pool] ||
         [string equal -nocase $lsaType ext_pool] ||
         [string equal -nocase $lsaType intra_area_prefix] ||
         [string equal -nocase $lsaType nssa_ext_pool] } {

        if { [catch {set iStatus [set networkBlock [::sth::sthCore::invoke stc::get $lsaHandle children-$netBlockType]] } err] } {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }

        set networkBlockHandle [lindex $networkBlock 0]

        if {$networkBlockHandle == ""} {
                ::sth::sthCore::processError returnKeyedList "Error: could not retrieve $netBlockType" {}
                return $::sth::sthCore::FAILURE
        }
    } elseif {$lsaType == "opaque_type_10"} {
        if { [catch {set iStatus [set tlv [::sth::sthCore::invoke stc::get $lsaHandle children]] } err] } {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }

        set tlvHandle [lindex $tlv 0]

        if { [catch {set iStatus [set name [::sth::sthCore::invoke stc::get $tlvHandle Name]] } err] } {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }

        set tlvType [lindex $name 0]
    }

    set listofFunctions {}
    array set functionListSwitch {}
    array set functionListValue {}

    foreach elem $sortedPriorityList {
        set switchName [lindex $elem 1]
        set switchValue $userInputArgs($switchName)
        set mode $userInputArgs(mode)
        set switchProcFunc [::sth::sthCore::getModeFunc ::sth::ospf:: $procPrefix $switchName $mode]

        if {$switchProcFunc == ""} {
            continue
        }
        if {[::info exists ::sth::ospf::commonLsaSwitches($switchName)] } {
            if {[string equal -nocase link_state_id $switchName]} {
                if {[catch {set ret [::sth::ospf::convertLinkStateId $lsaType $switchName $switchValue newSwitchName newSwitchValue $procPrefix] } err]} {
                        ::sth::sthCore::processError returnKeyedList "::sth::ospf::convertLinkStateId Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                }

                if {$::sth::sthCore::FAILURE == $ret } {
                        ::sth::sthCore::processError returnKeyedList "::sth::ospf::convertLinkStateId Failed: $err"
                        return $ret
                }

                if {[info exists functionListSwitch($switchProcFunc,$lsaHandle)]} {
                        lappend functionListSwitch($switchProcFunc,$lsaHandle) $newSwitchName
                        lappend functionListValue($switchProcFunc,$lsaHandle) $newSwitchValue
                } else {
                        set functionListSwitch($switchProcFunc,$lsaHandle) $newSwitchName
                        set functionListValue($switchProcFunc,$lsaHandle) $newSwitchValue
                        lappend listofFunctions "$switchProcFunc,$lsaHandle"
                }
            } else {
                if {[info exists functionListSwitch($switchProcFunc,$lsaHandle)]} {
                        lappend functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                        lappend functionListValue($switchProcFunc,$lsaHandle) $switchValue
                } else {
                        set functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                        set functionListValue($switchProcFunc,$lsaHandle) $switchValue
                        lappend listofFunctions "$switchProcFunc,$lsaHandle"
                }
            }
        } else {
            if {[string equal $lsaType router] && [::info exists ::sth::ospf::routerLsaSwitches($switchName)] ||\
            [string equal $lsaType network] && [::info exists ::sth::ospf::networkLsaSwitches($switchName)] ||\
            [string equal $lsaType summary_pool] && [::info exists ::sth::ospf::sumLsaSwitches($switchName)] ||\
            [string equal $lsaType intra_area_prefix] && [::info exists ::sth::ospf::intraLsaSwitches($switchName)] ||\
            [string equal $lsaType asbr_summary] && [::info exists ::sth::ospf::asbrSumLsaSwitches($switchName)] ||\
            [string equal $lsaType ext_pool] && [::info exists ::sth::ospf::extLsaSwitches($switchName)] ||\
            [string equal $lsaType opaque_type_10] && [::info exists ::sth::ospf::teLsaSwitches($switchName)] ||\
            [string equal $lsaType router_info] && [::info exists ::sth::ospf::routerInfoLsaSwitches($switchName)] ||\
            [string equal $lsaType extended_prefix] && [::info exists ::sth::ospf::extendedPrefixLsaSwitches($switchName)] ||\
            [string equal $lsaType extended_link] && [::info exists ::sth::ospf::extendedLinkLsaSwitches($switchName)] ||\
            [string equal $lsaType nssa_ext_pool] && [::info exists ::sth::ospf::nssaLsaSwitches($switchName)] }  {

                set stcobj [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName stcobj]

                #procPrefix stcObjHandle switchName switchValue
                if {[string equal -nocase $stcobj $netBlockType]} {
                    #        set cmd "::sth::ospf::$switchProcFunc $procPrefix $networkBlock $switchName $switchValue"
                    if {[info exists functionListSwitch($switchProcFunc,$networkBlock)]} {
                        lappend functionListSwitch($switchProcFunc,$networkBlock) $switchName
                        lappend functionListValue($switchProcFunc,$networkBlock) $switchValue
                    } else {
                        set functionListSwitch($switchProcFunc,$networkBlock) $switchName
                        set functionListValue($switchProcFunc,$networkBlock) $switchValue
                        lappend listofFunctions "$switchProcFunc,$networkBlock"
                    }

                } elseif {[::info exists ::sth::ospf::teLsaSwitches($switchName)]} {
                    if {$switchName == "te_router_addr" && [string equal -nocase $tlvType LinkTlv] ||\
                    $switchName != "te_router_addr" && [string equal -nocase $tlvType RouterTlv] && $switchName != "te_route_category"} {
                            ::sth::sthCore::processError returnKeyedList "Error: $switchName is not a compatible switch for $tlvType type of TLV" {}
                            return $::sth::sthCore::FAILURE
                    } else {
                        if {[string equal -nocase $stcobj TeLsa]} {
                            if {[info exists functionListSwitch($switchProcFunc,$lsaHandle)]} {
                                lappend functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                lappend functionListValue($switchProcFunc,$lsaHandle) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                set functionListValue($switchProcFunc,$lsaHandle) $switchValue
                                lappend listofFunctions "$switchProcFunc,$lsaHandle"
                            }
                        } else {
                            if {[info exists functionListSwitch($switchProcFunc,$tlvHandle)]} {
                                lappend functionListSwitch($switchProcFunc,$tlvHandle) $switchName
                                lappend functionListValue($switchProcFunc,$tlvHandle) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$tlvHandle) $switchName
                                set functionListValue($switchProcFunc,$tlvHandle) $switchValue
                                lappend listofFunctions "$switchProcFunc,$tlvHandle"
                            }
                        }
                    }
                } else {
                    switch $switchName {
                        net_attached_router -
                        router_link_mode {
                            #        set cmd "::sth::ospf::$switchProcFunc $procPrefix $lsaHandle $switchName $switchValue hLsaLink userInputArgs"
                            if {[info exists functionListSwitch($switchProcFunc,$lsaHandle)]} {
                                lappend functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                lappend functionListValue($switchProcFunc,$lsaHandle) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                set functionListValue($switchProcFunc,$lsaHandle) $switchValue
                                lappend listofFunctions "$switchProcFunc,$lsaHandle"
                            }
                        }
                        router_link_data {
                            if {[info exists functionListSwitch($switchProcFunc,$hLsaLink)]} {
                                lappend functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                lappend functionListValue($switchProcFunc,$hLsaLink) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                set functionListValue($switchProcFunc,$hLsaLink) $switchValue
                                lappend listofFunctions "$switchProcFunc,$hLsaLink"
                            }
                            set bLsaLinkHandleUsed true
                        }
                        attached_router_id {
                            if {![info exists userInputArgs(net_attached_router)]} {
                                ::sth::sthCore::processError returnKeyedList \
                                                [concat "Unable to process the argument " \
                                                                "\"-attached_router_id\" " \
                                                                "without the argument " \
                                                                "\"-net_attached_router\".  Please " \
                                                                "specify the -net_attached_router mode." \
                                                                "  " \
                                                ] \
                                                {}
                                return $::sth::sthCore::FAILURE
                            }

                            if {$userInputArgs(net_attached_router) == "delete"} {
                                continue
                            }
                            if {[info exists functionListSwitch($switchProcFunc,$hLsaLink)]} {
                                lappend functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                lappend functionListValue($switchProcFunc,$hLsaLink) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                set functionListValue($switchProcFunc,$hLsaLink) $switchValue
                                lappend listofFunctions "$switchProcFunc,$hLsaLink"
                            }
                            set bLsaLinkHandleUsed true
                        }
                        router_link_id {
                            if {$userInputArgs(router_link_mode) == "delete"} {
                                continue
                            }

                            if {[info exists functionListSwitch($switchProcFunc,$hLsaLink)]} {
                                lappend functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                lappend functionListValue($switchProcFunc,$hLsaLink) $switchValue
                        } else {
                                set functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                set functionListValue($switchProcFunc,$hLsaLink) $switchValue
                                lappend listofFunctions "$switchProcFunc,$hLsaLink"
                            }
                            set bLsaLinkHandleUsed true
                        }
                        nssa_prefix_forward_addr -
                        external_prefix_forward_addr {
                        #        set cmd "::sth::ospf::$switchProcFunc $procPrefix $lsaHandle $switchName $switchValue"
                            if {[info exists functionListSwitch($switchProcFunc,$lsaHandle)]} {
                                lappend functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                lappend functionListValue($switchProcFunc,$lsaHandle) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                set functionListValue($switchProcFunc,$lsaHandle) $switchValue
                                lappend listofFunctions "$switchProcFunc,$lsaHandle"
                            }
                        }
                        router_link_metric -
                        router_link_type {
                        #        set cmd "::sth::ospf::$switchProcFunc $procPrefix $hLsaLink $switchName $switchValue"
                            if {[info exists functionListSwitch($switchProcFunc,$hLsaLink)]} {
                                lappend functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                lappend functionListValue($switchProcFunc,$hLsaLink) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$hLsaLink) $switchName
                                set functionListValue($switchProcFunc,$hLsaLink) $switchValue
                                lappend listofFunctions "$switchProcFunc,$hLsaLink"
                            }
                            set bLsaLinkHandleUsed true
                        }
                        default {
                        #        set cmd "::sth::ospf::$switchProcFunc $procPrefix $lsaHandle $switchName $switchValue"
                            if {[info exists functionListSwitch($switchProcFunc,$lsaHandle)]} {
                                lappend functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                lappend functionListValue($switchProcFunc,$lsaHandle) $switchValue
                            } else {
                                set functionListSwitch($switchProcFunc,$lsaHandle) $switchName
                                set functionListValue($switchProcFunc,$lsaHandle) $switchValue
                                lappend listofFunctions "$switchProcFunc,$lsaHandle"
                            }
                        }
                    }
                }
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: $switchName is not a compatible switch for $lsaType type of LSA" {}
                return  $::sth::sthCore::FAILURE
            }
        }
    }

    if {[info exists userInputArgs(router_link_count)]} {
        set router_link_count $userInputArgs(router_link_count)
    } else {
        set router_link_count 1
    }

    if {[info exists userInputArgs(router_link_step)]} {
        set router_link_step $userInputArgs(router_link_step)
    } else {
        set router_link_step "0.0.0.1"
    }

    if {[string equal $lsaType router]} {
        if {[info exists functionListSwitch(doGenericConfig,empty1)] && [regexp {router_link_id} $functionListSwitch(doGenericConfig,empty1)]} {
            set value $functionListValue(doGenericConfig,empty1)
            set key    $functionListSwitch(doGenericConfig,empty1)
            set index 0
            foreach tmp [split $key] {
                if {[string equal $tmp router_link_id]} {
                        break
                } else {
                        set index [expr $index +1]
                }
            }
            set old_router_link_id [lindex [split $value] $index]
            for {set i 2} {$i<=$router_link_count } {incr i 1} {
                set new_router_link_id [::sth::sthCore::updateIpAddress 4 $old_router_link_id $router_link_step 1]
                set escapeDot "\\."
                regsub -all {\.} $old_router_link_id $escapeDot old_router_link_id
                regsub $old_router_link_id $value $new_router_link_id value
                lappend listofFunctions "doGenericConfig,empty$i"
                set  old_router_link_id $new_router_link_id
                set functionListSwitch(doGenericConfig,empty$i) $key
                set functionListValue(doGenericConfig,empty$i) $value
            }
        }
    }



    if {[string equal -nocase $bLsaLinkHandleUsed true] } {
        if {![info exists functionListSwitch(doProcessLsaLink,$lsaHandle)]} {
                ::sth::sthCore::processError returnKeyedList "$lsaType link not created" {}
                return  $::sth::sthCore::FAILURE
        } else {
            set cmd "::sth::ospf::doProcessLsaLink $procPrefix $lsaHandle {$functionListSwitch(doProcessLsaLink,$lsaHandle)} {$functionListValue(doProcessLsaLink,$lsaHandle)} hLsaLink userInputArgs"
            ::sth::sthCore::log debug "calling $cmd"
            if { [catch {set iStatus [eval $cmd] } err] } {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
                return  $::sth::sthCore::FAILURE
            } else {
                if { $iStatus == $::sth::sthCore::FAILURE } {
                    ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err"
                    return  $::sth::sthCore::FAILURE
                } else {
                    set createval ""
                    catch {set createval $userInputArgs(net_attached_router)}
                    if {[string equal -nocase $createval create]} {
                        set hNetworkLsaLink $hLsaLink
                    } else {
                        catch {set createval $userInputArgs(router_link_mode)}
                        if {[string equal -nocase $createval create]} {
                           set hRouterLsaLink $hLsaLink
                        }
                    }
                }
            }

            set tfunctionListSwitch [array get functionListSwitch]
            set tfunctionListValue  [array get functionListValue]
            array unset  functionListSwitch
            array unset  functionListValue
            for {set i 1} {$i<=$router_link_count } {incr i 1} {
                    set empty "empty$i "
                    set thLsaLink "[lindex [split $hLsaLink] $i] "
                    regsub "empty$i" $listofFunctions "[lindex [split $hLsaLink] $i]" listofFunctions
                    #set listofFunctions [string map "$empty $thLsaLink" $listofFunctions]
                    regsub $empty $tfunctionListSwitch $thLsaLink tfunctionListSwitch
                    regsub $empty $tfunctionListValue  $thLsaLink tfunctionListValue
            }
            array set functionListSwitch $tfunctionListSwitch
            array set functionListValue  $tfunctionListValue
        }
    }

    foreach functionObj $listofFunctions {
        set func_obj_list [split $functionObj ","]
        set switchProcFunc [lindex $func_obj_list 0]
        set object_handle [lindex $func_obj_list 1]
        if {[string equal $switchProcFunc doProcessLsaLink]} {
        #        set cmd "::sth::ospf::$switchProcFunc $procPrefix $object_handle $switchName $switchValue hLsaLink userInputArgs"
        continue
        } else {
                set cmd "::sth::ospf::$switchProcFunc $procPrefix $object_handle {$functionListSwitch($functionObj)} {$functionListValue($functionObj)}"
        }
        ::sth::sthCore::log debug "calling $cmd"
        if { [catch {set iStatus [eval $cmd] } err] } {
            ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
            return  $::sth::sthCore::FAILURE
        } else {
            if { $iStatus == $::sth::sthCore::FAILURE } {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err"
                return  $::sth::sthCore::FAILURE
            } else {
                set createval ""
                catch {set createval $userInputArgs(net_attached_router)}
                if {[string equal -nocase $createval create]} {
                    set hNetworkLsaLink $hLsaLink
                } else {
                    catch {set createval $userInputArgs(router_link_mode)}
                    if {[string equal -nocase $createval create]} {
                       set hRouterLsaLink $hLsaLink
                    }
                }
            }
        }
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $::sth::sthCore::SUCCESS

}


proc ::sth::ospf::configOSPFTlv {procPrefix hOSPFTlvHandle switchArgs } {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::configOSPFTlv $procPrefix $hOSPFTlvHandle $switchArgs "
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    set mode $userInputArgs(mode)

    set listofFunctions {}
    array set functionListSwitch {}
    array set functionListValue {}
    foreach {switchName switchValue} [array get userInputArgs] {

        if {[::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName supported]} {
            #set switchValue $userInputArgs($switchName)
            set procFunction [::sth::sthCore::getModeFunc ::sth::ospf:: $procPrefix $switchName $mode]
            set objType [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName stcobj]

            if {$procFunction == ""} {
                continue
            }
            if {![regexp -nocase $objType $hOSPFTlvHandle]} {
                continue
            }

            if {[info exist functionListSwitch($procFunction,$hOSPFTlvHandle)]} {
                lappend functionListSwitch($procFunction,$hOSPFTlvHandle) $switchName
                lappend functionListValue($procFunction,$hOSPFTlvHandle) $switchValue
            } else {
                set functionListSwitch($procFunction,$hOSPFTlvHandle) $switchName
                set functionListValue($procFunction,$hOSPFTlvHandle) $switchValue
                lappend listofFunctions "$procFunction,$hOSPFTlvHandle"
            }

        } else {
            ::sth::sthCore::processError returnKeyedList "Error: -$switchName is not a supported switch" {}
            return $::sth::sthCore::FAILURE
        }
    }

    foreach functionObj $listofFunctions {
        set function_obj_list [split $functionObj ","]
        set procFunction [lindex $function_obj_list 0]
        set objHandle [lindex $function_obj_list 1]
        set cmd "::sth::ospf::$procFunction $procPrefix $objHandle {$functionListSwitch($functionObj)} {$functionListValue($functionObj)}"
        set ret [eval $cmd]
        if {$::sth::sthCore::FAILURE == $ret} {
            ::sth::sthCore::processError returnKeyedList "$cmd Failed" {}
            return $::sth::sthCore::FAILURE
        }
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::convertLinkStateId ( str lsatype str hltSwitchName str hltSwitchValue str stcSwitchName str stcSwitchValue str procPrefix )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to convert link state ids
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] lsatype contains the LSA type.
###\param[in] hltSwitchName contains the HLTAPI switch name
###\param[in] hltSwitchValue contains the HLTAPI switch value
###\param[out] stcSwitchName will contain the STC switch value
###\param[out] stcSwitchValue will contain the STC switch value
###*/
###::sth::ospf::convertLinkStateId (lsatype hltSwitchName hltSwitchValue stcSwitchName stcSwitchValue procPrefix)
proc ::sth::ospf::convertLinkStateId { lsatype hltSwitchName hltSwitchValue stcSwitchName stcSwitchValue procPrefix} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::convertLinkStateId $lsatype $hltSwitchName $hltSwitchValue $stcSwitchName $stcSwitchValue $procPrefix"
    upvar $stcSwitchName myStcSwitchName
    upvar $stcSwitchValue myStcSwitchValue
    upvar returnKeyedList returnKeyedList

    set returnKeyedList ""

    switch $lsatype {
        network -
        router {
            set myStcSwitchName link_state_id
            set myStcSwitchValue $hltSwitchValue
            return $::sth::sthCore::SUCCESS
        }

        asbr_summary {
            set myStcSwitchName asbr_router_id
            set myStcSwitchValue $hltSwitchValue
            return $::sth::sthCore::SUCCESS
        }

        summary_pool -
        intra_area_prefix -
        ext_pool -
        nssa_ext_pool {
            ::sth::sthCore::processError returnKeyedList "switch -link_state_id is not supported for ospfv2 $lsatype" {}
            return $::sth::sthCore::FAILURE
        }

        default {
            ::sth::sthCore::processError returnKeyedList "Incorrect LSA Type" {}
            return $::sth::sthCore::FAILURE
        }
    }

    return $::sth::sthCore::SUCCESS
}


###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::encodeNetworkLsaAndLinks ( str lsaHandle str LsaName str procPrefix str switchArgs )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure encodes the LSA properties into the returnKeyedList in order to be returened to the user
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] LsaName contains the name of the LSA
###\param[in] switchArgs contains the user input in an array with keyed values
###\param[in] lsaHandle contains the handle of the LSA to be encoded
###*/
###::sth::ospf::encodeNetworkLsaAndLinks (lsaHandle LsaName procPrefix switchArgs)
proc ::sth::ospf::encodeNetworkLsaAndLinks {lsaHandle LsaName procPrefix switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::encodeNetworkLsaAndLinks $lsaHandle $LsaName $procPrefix $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable AttachedRouterKeyedList
    variable AttachedRouterList
    variable linkidValue
    variable stcObj
    variable stcAttr

    set AttachedRouterKeyedList ""
    set linkidValue ""
    set AttachedRouterList ""

    if {[string first _ospfv2_ $procPrefix] >= 0 } {
            set stcObj networklsalink
            set stcAttr linkid
    } else {
            set stcObj Ospfv3AttachedRouter
            set stcAttr routerId
    }

    if {![catch {set ret1 [set lsaLinkChildren [::sth::sthCore::invoke stc::get $lsaHandle children-$stcObj]]} err]} {
        foreach elem $lsaLinkChildren {
            if {![catch {set ret2 [set linkidValue [::sth::sthCore::invoke stc::get $elem $stcAttr]]} err]} {
                    lappend AttachedRouterList $linkidValue
            }
        }
    }

    keylset AttachedRouterKeyedList attached_router_ids  $AttachedRouterList
    keylset returnKeyedList network $AttachedRouterKeyedList

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::encodeTeLsaAndTlvs ( str lsaHandle str LsaName str procPrefix str switchArgs )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure encodes the LSA properties into the returnKeyedList in order to be returened to the user
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] LsaName contains the name of the LSA
###\param[in] switchArgs contains the user input in an array with keyed values
###\param[in] lsaHandle contains the handle of the LSA to be encoded
###*/
###::sth::ospf::encodeTeLsaAndTlvs (lsaHandle LsaName procPrefix switchArgs)
proc ::sth::ospf::encodeTeLsaAndTlvs {lsaHandle lsaName procPrefix switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::encodeTeLsaAndTlvs $lsaHandle $lsaName $procPrefix $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    set tlvName ""
    set instanceId ""
    set teMetric ""
    set linkId ""
    set linktype ""
    set routerAddress ""
    set teLocalIp ""
    set teRemoteIp ""
    set teGroup ""
    set teMaxBandwidth ""
    set teRsvrBandwidth ""
    set teUnrsvrBand0 ""
    set teUnrsvrBand1 ""
    set teUnrsvrBand2 ""
    set teUnrsvrBand3 ""
    set teUnrsvrBand4 ""
    set teUnrsvrBand5 ""
    set teUnrsvrBand6 ""
    set teUnrsvrBand7 ""

    set tlvList {}
    set subList {}

    if {![catch {set ret [set teHandleList [::sth::sthCore::invoke stc::get $lsaHandle children]]} err]} {
        if {![catch {set ret [set instanceId [::sth::sthCore::invoke stc::get $lsaHandle Instance]]} err]} {
            set tlvHandle [lindex $teHandleList 0]
            if {![catch {set ret [set n [::sth::sthCore::invoke stc::get $tlvHandle name]]} err]} {
                set tlvName [lindex $n 0]

                if {[string equal -nocase $tlvName LinkTlv]} {
                    if {![catch {set ret [set teMetric [::sth::sthCore::invoke stc::get $tlvHandle TeMetric]]} err]} {
                        keylset subList te_metric $teMetric
                        if {![catch {set ret [set linkId [::sth::sthCore::invoke stc::get $tlvHandle LinkId]]} err]} {
                            keylset subList te_link_id $linkId
                            if {![catch {set ret [set linkType [::sth::sthCore::invoke stc::get $tlvHandle LinkType]]} err]} {
                                set linkType [::sth::sthCore::getRvsmap ::sth::ospf:: $procPrefix te_link_type $linkType]
                                keylset subList te_link_type $linkType

                                if {![catch {set ret [set teparam [::sth::sthCore::invoke stc::get $tlvHandle children]]} err]} {
                                    set teParamHandle [lindex $teparam 0]

                                    if {$teParamHandle != ""} {
                                        if {![catch {set ret [set subtlv [::sth::sthCore::invoke stc::get $teParamHandle SubTlv]]} err]} {
                                            set sublist [split $subtlv "|"]

                                            foreach subElem $sublist {
                                                switch $subElem {
                                                    NONE {
                                                            #do nothing
                                                    }

                                                    GROUP {
                                                            catch {set ret [set teGroup [::sth::sthCore::invoke stc::get $teParamHandle TeGroup]]}
                                                            keylset subList te_admin_group $teGroup
                                                    }

                                                    MAX_BW {
                                                            catch {set ret [set teMaxBandwidth [::sth::sthCore::invoke stc::get $teParamHandle TeMaxBandwidth]]}
                                                            keylset subList te_max_bw $teMaxBandwidth
                                                    }

                                                    MAX_RSV_BW {
                                                            catch {set ret [set teRsvrBandwidth [::sth::sthCore::invoke stc::get $teParamHandle TeRsvrBandwidth]]}
                                                            keylset subList te_max_resv_bw $teRsvrBandwidth
                                                    }

                                                    UNRESERVED {
                                                            catch {set ret [set teUnrsvrBand0 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth0]]}
                                                            keylset subList te_unresv_bw_priority0 $teUnrsvrBand0

                                                            catch {set ret [set teUnrsvrBand1 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth1]]}
                                                            keylset subList te_unresv_bw_priority1 $teUnrsvrBand1

                                                            catch {set ret [set teUnrsvrBand2 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth2]]}
                                                            keylset subList te_unresv_bw_priority2 $teUnrsvrBand2

                                                            catch {set ret [set teUnrsvrBand3 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth3]]}
                                                            keylset subList te_unresv_bw_priority3 $teUnrsvrBand3

                                                            catch {set ret [set teUnrsvrBand4 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth4]]}
                                                            keylset subList te_unresv_bw_priority4 $teUnrsvrBand4

                                                            catch {set ret [set teUnrsvrBand5 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth5]]}
                                                            keylset subList te_unresv_bw_priority5 $teUnrsvrBand5

                                                            catch {set ret [set teUnrsvrBand6 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth6]]}
                                                            keylset subList te_unresv_bw_priority6 $teUnrsvrBand6

                                                            catch {set ret [set teUnrsvrBand7 [::sth::sthCore::invoke stc::get $teParamHandle TeUnRsvrBandwidth7]]}
                                                            keylset subList te_unresv_bw_priority7 $teUnrsvrBand7

                                                    }

                                                    LOCAL_IP {
                                                            catch {set ret [set teLocalIp [::sth::sthCore::invoke stc::get $teParamHandle TeLocalIp]]}
                                                            keylset subList te_local_ip $teLocalIp
                                                    }

                                                    REMOTE_IP {
                                                            catch {set ret [set teRemoteIp [::sth::sthCore::invoke stc::get $teParamHandle TeRemoteIp]]}
                                                            keylset subList te_remote_ip $teRemoteIp
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                } elseif {[string equal -nocase $tlvName RouterTlv]} {
                    if {![catch {set ret [set routerAddress [::sth::sthCore::invoke stc::get $tlvHandle RouterAddr]]} err]} {
                        keylset subList te_router_addr $routerAddress
                    }
                }
            }
        }
    }

    keylset tlvList instance_id $instanceId
    keylset tlvList $tlvName $subList
    keylset returnKeyedList opaque_type_10 $tlvList
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::encodeRouterLsaAndLinks ( str lsaHandle str LsaName str procPrefix str switchArgs )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure encodes the LSA properties into the returnKeyedList in order to be returened to the user
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] LsaName contains the name of the LSA
###\param[in] switchArgs contains the user input in an array with keyed values
###\param[in] lsaHandle contains the handle of the LSA to be encoded
###*/
###::sth::ospf::encodeRouterLsaAndLinks (lsaHandle LsaName procPrefix switchArgs)
proc ::sth::ospf::encodeRouterLsaAndLinks {lsaHandle lsaName procPrefix switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::encodeRouterLsaAndLinks $lsaHandle $lsaName $procPrefix $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    variable AttachedRouterKeyedList
    variable AttachedRouterList
    variable iLsaLinkCount
    variable linkidValue
    variable AllLinksKeyedList
    variable linktypeValue
    variable linkdataValue

    set AttachedRouterKeyedList ""
    set AttachedRouterList ""
    set linkidValue ""
    set AttachedRouterList ""
    set oneRouterLink {}
    set AllLinksKeyedList ""
    set linkdataValue ""
    set linktypeValue ""
    set AllLinks {}
    set i 0

    variable stcObj
    variable stcAttrId
    variable stcAttrData
    variable stcAttrType

    if {[string first _ospfv2_ $procPrefix] >= 0 } {
        set stcObj RouterLsaLink
        set stcAttrId LinkId
        set stcAttrData LinkData
        set stcAttrType LinkType
    } else {
        set stcObj Ospfv3RouterLsaIf
        set stcAttrId NeighborRouterId
        set stcAttrData IfId
        set stcAttrType IfType
    }

    if {![catch {set ret [set objChildren [::sth::sthCore::invoke stc::get $lsaHandle children-$stcObj]]} err]} {
        foreach elem $objChildren {
            set oneRouterLink {}
            if {![catch {set ret [set linkidValue [::sth::sthCore::invoke stc::get $elem $stcAttrId]]} err]} {
                if {![catch {set ret [set linkdataValue [::sth::sthCore::invoke stc::get $elem $stcAttrData]]} err]} {
                    if {![catch {set ret [set linktypeValue [::sth::sthCore::invoke stc::get $elem $stcAttrType]]} err]} {
                        keylset oneRouterLink $i-id $linkidValue
                        keylset oneRouterLink data  $linkdataValue

                        set linktypeValue [::sth::sthCore::getRvsmap ::sth::ospf:: $procPrefix router_link_type $linktypeValue]
                        keylset oneRouterLink type  $linktypeValue

                        incr i 1
                    }
                }
            }

            lappend AllLinks $oneRouterLink
        }
    }

    keylset AllLinksKeyedList links $AllLinks
    keylset returnKeyedList router $AllLinksKeyedList
#        keylset returnKeyedList lsa_handle $lsaHandle

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::encodeSumPoolPrefixes ( str lsaHandle str LsaName str procPrefix str switchArgs )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure encodes the LSA properties into the returnKeyedList in order to be returened to the user
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] LsaName contains the name of the LSA
###\param[in] switchArgs contains the user input in an array with keyed values
###\param[in] lsaHandle contains the handle of the LSA to be encoded
###*/
###::sth::ospf::encodeSumPoolPrefixes (lsaHandle LsaName procPrefix switchArgs)
proc ::sth::ospf::encodeSumPoolPrefixes {lsaHandle LsaName procPrefix switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::encodeSumPoolPrefixes $lsaHandle $LsaName $procPrefix $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    variable networkBlockHandle
    variable startIPList
    variable prefix
    variable count
    variable step

    set networkBlockHandle -1
    set startIPList none
    set prefix none
    set count none
    set step none

    if {[string first _ospfv2_ $procPrefix] >= 0 } {
        set stcObj ipv4networkblock
    } else {
        set stcObj ipv6networkblock
    }

    if {[catch {set ret [set NetworkBlock [::sth::sthCore::invoke stc::get $lsaHandle children-$stcObj]]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    set networkBlockHandle [lindex $NetworkBlock 0]

    if { $networkBlockHandle != ""} {
        if {[catch {set ret [set startIPList [::sth::sthCore::invoke stc::get $networkBlockHandle StartIpList]]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }
        if {[catch {set ret [set count [::sth::sthCore::invoke stc::get $networkBlockHandle NetworkCount]]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }
        if {[catch {set ret [set step [::sth::sthCore::invoke stc::get $networkBlockHandle AddrIncrement]]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }
        if {[catch {set ret [set prefix [::sth::sthCore::invoke stc::get $networkBlockHandle PrefixLength]]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return $::sth::sthCore::FAILURE
        }

        variable SummaryBlock
        set SummaryBlock ""

        keylset SummaryBlock num_prefx     $count
        keylset SummaryBlock prefix_length $prefix
        keylset SummaryBlock prefix_start  $startIPList
        keylset SummaryBlock prefix_step   $step
        #keylset SummaryBlock lsa_handle         $lsaHandle

        keylset returnKeyedList $LsaName $SummaryBlock
    } else {
        ::sth::sthCore::processError returnKeyedList "Error: Could not get $stcObj" {}
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/* \ingroup ospfLsaFunctions
###\fn proc ::sth::ospf::encodeLsaCommon ( str lsaHandle str LsaName str procPrefix str switchArgs )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure encodes the LSA properties into the returnKeyedList in order to be returened to the user
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] LsaName contains the name of the LSA
###\param[in] switchArgs contains the user input in an array with keyed values
###\param[in] lsaHandle contains the handle of the LSA to be encoded
###*/
###::sth::ospf::encodeLsaCommon (lsaHandle LsaName procPrefix switchArgs)
proc ::sth::ospf::encodeLsaCommon {lsaHandle LsaName procPrefix switchArgs} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::encodeLsaCommon $lsaHandle $LsaName $procPrefix $switchArgs"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList

    variable advRouterId
    set advRouterId ""

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $::sth::sthCore::SUCCESS
}

proc ::sth::ospf::getHandleOfRemainingObject {ospfRouterHandle objType objHandleStr} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::getHandleOfRemainingObject $ospfRouterHandle $objType $objHandleStr"
    upvar returnKeyedList returnKeyedList
    upvar $objHandleStr objHandle

    if {[catch {set ret [set routerHandle [::sth::sthCore::invoke stc::get $ospfRouterHandle parent]]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    if {$objType != "Router"} {
        if {[catch {set ret [set objHandle [::sth::sthCore::invoke stc::get $routerHandle children-$objType]]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
        if {$objType == "Ipv6If"} {
            set objHandle [lindex $objHandle 0]
        }
    } else {
        set objHandle $routerHandle
    }

    return $::sth::sthCore::SUCCESS
}


###/* \ingroup ospfFunctions
###\fn proc ::sth::ospf::configOSPFRouter ( procPrefix hOSPFRouterHandle switchArgs mySortedPriorityList )
###\breif Returns  $::sth::sthCore::FAILURE or  $::sth::sthCore::SUCCESS.
###
###This procedure is used to configure ospf router switches from the user input.
###
###\param[in] procPrefix procPrefix contains the command table name and the version number of the session
###\param[in] hOSPFRouterHandle contains the ospf handle.
###\param[in] switchArgs contains the array of switch values indexed by switch names.
###\param[in] mySortedPriorityList contains the list of switch priority/name pairs.
###*/
###::sth::ospf::configOSPFRouter ( procPrefix hOSPFRouterHandle switchArgs mySortedPriorityList)
proc ::sth::ospf::configOSPFRouter {procPrefix hOSPFRouterHandle switchArgs mySortedPriorityList} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::configOSPFRouter $procPrefix $hOSPFRouterHandle $switchArgs $mySortedPriorityList"
    upvar $switchArgs userInputArgs
    upvar returnKeyedList returnKeyedList
    upvar $mySortedPriorityList sortedPriorityList

    variable objHandle
    variable TEHandle

    set objHandle -1
    set mode $userInputArgs(mode)

    if {[catch {array set objList [::sth::ospf::getConfigObjHandles $hOSPFRouterHandle]} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while obtaining necessary objects. Error: $eMsg"
            return $::sth::sthCore::FAILURE
    }
    set listofFunctions {}
    array set functionListSwitch {}
    array set functionListValue {}
    foreach {switchName switchValue} [array get userInputArgs] {
        #set switchName [lindex $elem 1]
        if {$switchName == "mac_address_start"} { continue }
        if {$switchName == "tunnel_handle"} {continue}
        if {$switchName == "expand"} {continue}
        if {[::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName supported]} {
            #set switchValue $userInputArgs($switchName)
            set procFunction [::sth::sthCore::getModeFunc ::sth::ospf:: $procPrefix $switchName $mode]
            set objType [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName stcobj]

            if {$procFunction == ""} {
                    continue
            }

            if {$switchName == "demand_circuit" || $switchName == "area_type"} {
                if {$::sth::ospf::flag_option_bits} {
                        continue
                }
            }
            if {$objType eq "VlanIf_Outer"} {
                set objType "VlanIf"
            }
            set objHandle $objList($objType)

            #add qinq support
            if {[string tolower $objType] == "vlanif" && [llength $objHandle] == 2} {
                if {[regexp outer $switchName]} {
                    set objHandle [lindex $objHandle 1]
                } else {
                    set objHandle [lindex $objHandle 0]
                }
            }

            if {[info exist functionListSwitch($procFunction,$objHandle)]} {
                lappend functionListSwitch($procFunction,$objHandle) $switchName
                lappend functionListValue($procFunction,$objHandle) $switchValue
            } else {
                set functionListSwitch($procFunction,$objHandle) $switchName
                set functionListValue($procFunction,$objHandle) $switchValue
                lappend listofFunctions "$procFunction,$objHandle"
            }

        } else {
            ::sth::sthCore::processError returnKeyedList "Error: -$switchName is not a supported switch" {}
            return $::sth::sthCore::FAILURE
        }
    }

    foreach functionObj $listofFunctions {
        set function_obj_list [split $functionObj ","]
        set procFunction [lindex $function_obj_list 0]
        set objHandle [lindex $function_obj_list 1]
        set cmd "::sth::ospf::$procFunction $procPrefix $objHandle {$functionListSwitch($functionObj)} {$functionListValue($functionObj)}"
        if {[catch {set ret [eval $cmd]} err]} {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
                return -code error $returnKeyedList
        } elseif {$::sth::sthCore::FAILURE == $ret} {
                ::sth::sthCore::processError returnKeyedList "$cmd Failed" {}
                return -code error $returnKeyedList
        }
    }


    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup oSPFFunctions
###\fn proc ::sth::ospf::processOSPFv2TEParamsForLinkTlv {procPrefix ospfHandle switchName switchValue}
###\brief Returns $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This processes TE parameters for a TLV

###\param [in] tlvHandle under which the TEParams is created and configured.
###\param [in] switchName is TEenable.
###\param [in] switchValue is 0 or 1 (1 means "create")
###\param [in] procPrefix is the name of ospf configure under which TELsa is configured.
###
###\author: Fadi Hassan
###*/
###
###\ ::sth::ospf::processOSPFv2TEParamsForLinkTlv { integer hOSPFRouterHandle string switchName string switchValue string cmdName keyedlist myReturnKeyedList array mySwitchNameValueArray }
###
###
proc ::sth::ospf::processOSPFv2TEParamsForLinkTlv {procPrefix tlvHandle switchName switchValue} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::processOSPFv2TEParamsForLinkTlv $procPrefix $tlvHandle $switchName $switchValue"
    upvar returnKeyedList returnKeyedList

    if {[catch {set ret [set te [::sth::sthCore::invoke stc::get $tlvHandle children-teparams]]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    set teHandle [lindex $te 0]

    if {$teHandle == ""} {
        if {[catch {set ret [set teHandle [::sth::sthCore::invoke stc::create teparams -under $tlvHandle]] } err]} {
            ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
            return $::sth::sthCore::FAILURE
        }
    }

    if {[catch {set ret [::sth::ospf::doGenericConfig $procPrefix $teHandle $switchName $switchValue]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::doGenericConfig Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    if {[catch {set ret [set sub [::sth::sthCore::invoke stc::get $teHandle SubTlv]]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    set sublist [split $sub "|"]
    if {[string equal $sub 0]} {
        set sub ""
    }
    foreach switchName_ $switchName {
        switch $switchName_ {
            te_local_ip {
                if {[lsearch $sublist "LOCAL_IP"] == -1} {
                    append sub "|LOCAL_IP"
                }
            }
            te_remote_ip {
                if {[lsearch $sublist "REMOTE_IP"] == -1} {
                    append sub "|REMOTE_IP"
                }
            }
            te_admin_group {
                if {[lsearch $sublist "GROUP"] == -1} {
                    append sub "|GROUP"
                }
            }
            te_max_bw {
                if {[lsearch $sublist "MAX_BW"] == -1} {
                    append sub "|MAX_BW"
                }
            }
            te_max_resv_bw {
                if {[lsearch $sublist "MAX_RSV_BW"] == -1} {
                    append sub "|MAX_RSV_BW"
                }
            }
            te_unresv_bw_priority0 -
            te_unresv_bw_priority1 -
            te_unresv_bw_priority2 -
            te_unresv_bw_priority3 -
            te_unresv_bw_priority4 -
            te_unresv_bw_priority5 -
            te_unresv_bw_priority6 -
            te_unresv_bw_priority7 {
                if {[lsearch $sublist "UNRESERVED"] == -1} {
                        append sub "|UNRESERVED"
                }
            }
        }
    }

    ::sth::sthCore::invoke stc::config $teHandle SubTlv $sub
}

###/*! \ingroup oSPFFunctions
###\fn proc ::sth::ospf::createOSPFv2TEParams {procPrefix ospfHandle switchName switchValue}
###\brief Returns $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This process creates, delete or reset lsa link.
###\param [in] ospfHandle under which the TELsa is created and configured.
###\param [in] switchName is TEenable.
###\param [in] switchValue is 0 or 1 (1 means "create")
###\param [in] procPrefix is the name of ospf configure under which TELsa is configured.
###
###\author: Fadi Hassan
###*/
###
###\ ::sth::ospf::createOSPFv2TEParams { integer hOSPFRouterHandle string switchName string switchValue string cmdName keyedlist myReturnKeyedList array mySwitchNameValueArray }
###
###
proc ::sth::ospf::createOSPFv2TEParams {procPrefix ospfHandle switchName switchValue} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::createOSPFv2TEParams $procPrefix $ospfHandle $switchName $switchValue"
    upvar returnKeyedList returnKeyedList


    set teHandle $ospfHandle
    if {$teHandle == ""} {
            ::sth::sthCore::processError returnKeyedList "Error: Error retreiving TeParams" {}
            return $::sth::sthCore::FAILURE
    }

    if {[catch {set ret [::sth::ospf::doGenericConfig $procPrefix $teHandle $switchName $switchValue]} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doGenericConfig Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }

    if {[catch {set ret [set sub [::sth::sthCore::invoke stc::get $teHandle SubTlv]]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }

    set sublist [split $sub "|"]
    if {[string equal $sub 0]} {
            set sub ""
    }
    foreach switchName_ $switchName {
        switch $switchName_ {
            te_admin_group {
                if {[lsearch $sublist "GROUP"] == -1} {
                    append sub "|GROUP"
                }
            }

            te_max_bw {
                if {[lsearch $sublist "MAX_BW"] == -1} {
                    append sub "|MAX_BW"
                }
            }

            te_max_resv_bw {
                if {[lsearch $sublist "MAX_RSV_BW"] == -1} {
                    append sub "|MAX_RSV_BW"
                }
            }

            te_unresv_bw_priority0 -
            te_unresv_bw_priority1 -
            te_unresv_bw_priority2 -
            te_unresv_bw_priority3 -
            te_unresv_bw_priority4 -
            te_unresv_bw_priority5 -
            te_unresv_bw_priority6 -
            te_unresv_bw_priority7 {
                if {[lsearch $sublist "UNRESERVED"] == -1} {
                    append sub "|UNRESERVED"
                }
            }
        }
    }

   ::sth::sthCore::invoke stc::config $teHandle SubTlv $sub

    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup oSPFFunctions
###\fn proc ::sth::ospf::doAreaTypeConfig {procPrefix objHandle switchName switchValue}
###\brief Returns $::sth::sthCore::FAILURE or $::sth::sthCore::SUCCESS
###
###This procedure is used to set the DemandCircuit bit in the option. It needs
### special processing. If -demand_circuit is set to 1, DC is turned on.
### If -demand_circuit is set to zero, the DC is turned off. Since other bits
### of the options should not be changed when setting DCs, bitwise operations
### are required.
###
###\param[in] objHandle contains the ospf session handle.
###\param[in] switctName contains "demand_circuit"
###\param[in] switchValue contains the value of demand_circuit 0 or 1.
###\param[in] procPrefix        contains the subcommand emulation_ospf_config_create or
###                   emulation_ospf_config_config.
###
###\author: Fadi Hassan
###*/
###
###doAreaTypeConfig ( procPrefix objHandle switchName switchValue}
###
proc ::sth::ospf::doAreaTypeConfig {procPrefix objHandle switchName switchValue} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::doAreaTypeConfig $procPrefix $objHandle $switchName $switchValue"
    upvar returnKeyedList returnKeyedList
    set switchName [lindex $switchName 0]
    set switchValue [lindex $switchValue 0]

    set stcAttrName [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName stcattr]
    set stcAttrValue "non-numeric"

    if {[catch {set ret [set stcAttrValue [::sth::sthCore::invoke stc::get $objHandle $stcAttrName]] } err] } {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }

    if {$ret == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err"
            return $::sth::sthCore::FAILURE
    }
    if {[string first "_ospfv3_" $procPrefix] >= 0} {
        set bitList [split $stcAttrValue "|" ]
        set newStcAttrValue 0

        foreach elem $bitList {
            switch $elem {
                V6BIT {
                        set newStcAttrValue [expr {1 + $newStcAttrValue}]
                }
                EBIT {
                        set newStcAttrValue [expr {2 + $newStcAttrValue}]
                }
                MCBIT {
                        set newStcAttrValue [expr {4 + $newStcAttrValue}]
                }
                NBIT {
                        set newStcAttrValue [expr {8 + $newStcAttrValue}]
                }
                RBIT {
                        set newStcAttrValue [expr {16 + $newStcAttrValue}]
                }
                DCBIT {
                        set newStcAttrValue [expr {32 + $newStcAttrValue}]
                }
                UNUSED6 {
                        set newStcAttrValue [expr {64 + $newStcAttrValue}]
                }
                default {
                        ::sth::sthCore::processError returnKeyedList "Error: $elem" {}
                        return $::sth::sthCore::FAILURE
                }
            }
        }

        set stcAttrValue $newStcAttrValue
    } elseif {[string first "_ospfv2_" $procPrefix] >= 0} {
        set bitList [split $stcAttrValue "|" ]
        set newStcAttrValue 0

        foreach elem $bitList {
            switch $elem {
                TBIT {
                        set newStcAttrValue [expr {1 + $newStcAttrValue}]
                }
                EBIT {
                        set newStcAttrValue [expr {2 + $newStcAttrValue}]
                }
                MCBIT {
                        set newStcAttrValue [expr {4 + $newStcAttrValue}]
                }
                NPBIT {
                        set newStcAttrValue [expr {8 + $newStcAttrValue}]
                }
                EABIT {
                        set newStcAttrValue [expr {16 + $newStcAttrValue}]
                }
                DCBIT {
                        set newStcAttrValue [expr {32 + $newStcAttrValue}]
                }
                OBIT {
                        set newStcAttrValue [expr {64 + $newStcAttrValue}]
                }
                default {
                        ::sth::sthCore::processError returnKeyedList "Error: $elem" {}
                        return $::sth::sthCore::FAILURE
                }
            }
        }

        set stcAttrValue $newStcAttrValue
    } else {
            ::sth::sthCore::processError returnKeyedList "Error: invalid ospf protocol $procPrefix" {}
    }

    if {$switchValue == "external_capable"} {
            set stcAttrValue [expr {$stcAttrValue | 0x02}]
            set stcAttrValue [expr {$stcAttrValue & 0xF7}]
    } elseif {$switchValue == "stub"} {
            set stcAttrValue [expr {$stcAttrValue & 0xF5}]
    } elseif {$switchValue == "nssa"} {
            set stcAttrValue [expr {$stcAttrValue | 0x08}]
            set stcAttrValue [expr {$stcAttrValue & 0xFD}]
    }

    if {[catch {set ret [::sth::ospf::doGenericConfig $procPrefix $objHandle $switchName $stcAttrValue]} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::ospf::doGenericConfig Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }
    if {$ret == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::processError returnKeyedList "::sth::ospf::doGenericConfig Failed: $err"
            return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup oSPFFunctions
###\fn proc ::sth::ospf::OSPFRouterDemanCircuit {procPrefix objHandle switchName switchValue}
###\brief Returns $::sth::sthCore::FAILURE or $::sth::sthCore::SUCCESS
###
###This procedure is used to set the DemandCircuit bit in the option. It needs
### special processing. If -demand_circuit is set to 1, DC is turned on.
### If -demand_circuit is set to zero, the DC is turned off. Since other bits
### of the options should not be changed when setting DCs, bitwise operations
### are required.
###
###\param[in] objHandle contains the ospf session handle.
###\param[in] switctName contains "demand_circuit"
###\param[in] switchValue contains the value of demand_circuit 0 or 1.
###\param[in] procPrefix        contains the subcommand emulation_ospf_config_create or
###                   emulation_ospf_config_config.
###
###\author: Fadi Hassan
###*/
###
###OSPFRouterDemanCircuit ( procPrefix objHandle switchName switchValue}
###
proc ::sth::ospf::processOSPFRouterDemandCircuit {procPrefix objHandle switchName switchValue} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::processOSPFRouterDemandCircuit $procPrefix $objHandle $switchName $switchValue"
    upvar returnKeyedList returnKeyedList
    set switchName [lindex $switchName 0]
    set switchValue [lindex $switchValue 0]
    set stcAttrName [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName stcattr]
    set stcAttrValue -1
    if {[catch {set ret [set stcAttrValue [::sth::sthCore::invoke stc::get $objHandle $stcAttrName]] } err] } {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return $::sth::sthCore::FAILURE
    }

    if {[string first "_ospfv3_" $procPrefix] >= 0} {
        set bitList [split $stcAttrValue "|" ]
        set newStcAttrValue 0

        foreach elem $bitList {
            switch $elem {
                V6BIT {
                        set newStcAttrValue [expr {1 + $newStcAttrValue}]
                }
                EBIT {
                        set newStcAttrValue [expr {2 + $newStcAttrValue}]
                }
                MCBIT {
                        set newStcAttrValue [expr {4 + $newStcAttrValue}]
                }
                NBIT {
                        set newStcAttrValue [expr {8 + $newStcAttrValue}]
                }
                RBIT {
                        set newStcAttrValue [expr {16 + $newStcAttrValue}]
                }
                DCBIT {
                        set newStcAttrValue [expr {32 + $newStcAttrValue}]
                }
                UNUSED6 {
                        set newStcAttrValue [expr {64 + $newStcAttrValue}]
                }
                default {
                        ::sth::sthCore::processError returnKeyedList "Error: $elem" {}
                        return $::sth::sthCore::FAILURE
                }
            }
        }
        set stcAttrValue $newStcAttrValue
    } elseif {[string first "_ospfv2_" $procPrefix] >= 0} {
        set bitList [split $stcAttrValue "|" ]
        set newStcAttrValue 0
        foreach elem $bitList {
            switch $elem {
                TBIT {
                        set newStcAttrValue [expr {1 + $newStcAttrValue}]
                }
                EBIT {
                        set newStcAttrValue [expr {2 + $newStcAttrValue}]
                }
                MCBIT {
                        set newStcAttrValue [expr {4 + $newStcAttrValue}]
                }
                NPBIT {
                        set newStcAttrValue [expr {8 + $newStcAttrValue}]
                }
                EABIT {
                        set newStcAttrValue [expr {16 + $newStcAttrValue}]
                }
                DCBIT {
                        set newStcAttrValue [expr {32 + $newStcAttrValue}]
                }
                OBIT {
                        set newStcAttrValue [expr {64 + $newStcAttrValue}]
                }
                default {
#                        ::sth::sthCore::processError returnKeyedList "Error: $elem" {}
#                        return $::sth::sthCore::FAILURE
                }
            }
        }
        set stcAttrValue $newStcAttrValue
    } else {
        ::sth::sthCore::processError returnKeyedList "Error: invalid ospf protocol $procPrefix" {}
    }

    if { $switchValue == 1 } {
        set stcAttrValue [expr {$stcAttrValue | 0x20} ]
        #set stcAttrValue [format "0x%X" $stcAttrValue]
    } else {
        set stcAttrValue [expr {$stcAttrValue & 0xDF} ]
        #set stcAttrValue [format "0x%X" $stcAttrValue]
    }
    if {[catch {set ret [::sth::ospf::doGenericConfig $procPrefix $objHandle $switchName $stcAttrValue]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::doGenericConfig Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }
    if {$ret == $::sth::sthCore::FAILURE} {
        ::sth::sthCore::log error "::sth::ospf::doGenericConfig Failed: $err"
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup oSPFFunctions
###\fn sth::ospf::doGenericConfig (procPrefix stcObjHandle switchName switchValue)
###\brief Returns $::sth::sthCore::FAILURE or $::sth::sthCore::SUCCESS
###
###This procedure sets the switchValue to switchName for objHandle.
###
###
###\param[in] stcObjHandle:  the object handle to set value for;
###\param[in] switchName: the name of the switch to set value for;
###\param[in] switchName: the value for switchName of objHandle.
###\param[in] procPrefix:        the subcommand name under which this set is
###                                           performed.
###
###
###\author: Davison Zhang
###\modified by: Fadi Hassan
###*/
###
###procedure header here.
###
proc ::sth::ospf::doGenericConfig {procPrefix stcObjHandle switchName switchValue} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::doGenericConfig $procPrefix $stcObjHandle $switchName $switchValue"
    upvar returnKeyedList returnKeyedList

    set configString ""

    set i 0
    foreach switchName_ $switchName {
        set stcAttrName [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName_ stcattr]
        set switchValue_ [lindex $switchValue $i]
        if {[catch {set stcAttrValue [::sth::sthCore::getFwdmap ::sth::ospf:: $procPrefix $switchName_ $switchValue_]}]} {
                set stcAttrValue $switchValue_
        }
        append configString " -$stcAttrName $stcAttrValue"
        incr i
    }

    ::sth::sthCore::invoke stc::config $stcObjHandle $configString

    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup sthOSPFFunctions
###\fn proc ::sth::ospf::incrementIPv4Address ( array mySwitchNameValueArray, str switchName, str switchStepName )
###\brief Returns return $::sth::sthCore::SUCCESS when the function runs successfully. Otherwise, $::sth::sthCore::FAILURE.
###
###This procedure is used to increment the IPv4 address of any switch. It is needed when creating
###multiple sessions of ospf.
###
###
###\param[in, out] mySwitchNameValueArray contains an array of switch values indexed by switches names.
###\param[in] switchName contains switch name whose value is IPv4 address and needs to be incremented.
###\param[in] switchStepValue contains the value of the swith step as the increment for the switch value.
###
###
###\author: Davison Zhang
###\modified by: Fadi Hassan
###*/
###
### incrementIPv4Address ( array mySwitchNameValueArray, str switchName, str switchStepVale )
###
proc ::sth::ospf::incrementIPv4Address { mySwitchNameValueArray switchName switchStepValue } {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::incrementIPv4Address $mySwitchNameValueArray $switchName $switchStepValue"
    upvar $mySwitchNameValueArray switchNameValueArray
    variable switchValue
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    array set IPv4Address {}
    array set tempIPv4Address {}

    set switchValue $switchNameValueArray($switchName)
    #set switchStepValue $switchNameValueArray($switchStepName)

    set tmpStepIp [split $switchStepValue "\."]
    set switchStepValue 0
    foreach stepIp $tmpStepIp {
            set switchStepValue [expr $switchStepValue*256+$stepIp]
    }
    set IPList [split $switchValue "\." ]
    set index 0

    foreach ipcomp $IPList {
            set IPv4Address($index) $ipcomp
            incr index
    }

    set carryover 0
    set size [array size IPv4Address]

    if { $size != 4 } {
            return $::sth::sthCore::FAILURE
    } else {
        set carryover [expr {$carryover + $switchStepValue}]

        for {set i 3} { $i >= 0 } {incr i -1} {
            set tempVal $IPv4Address($i)
            set tempVal [expr {$tempVal + $carryover} ]

            if {$tempVal > 255 } {
                set tempIPv4Address($i) [expr {$tempVal % 256} ]
                set carryover [ expr {$tempVal / 256}]
            } else {
                set tempIPv4Address($i) $tempVal
                set carryover 0
            }
        }
    }

    set switchNameValueArray($switchName) "$tempIPv4Address(0).$tempIPv4Address(1).$tempIPv4Address(2).$tempIPv4Address(3)"
    return $::sth::sthCore::SUCCESS
}

proc ::sth::ospf::processOspfv3RouterType {procPrefix lsaHandle switchName switchValue} {
    ::sth::sthCore::log debug "Internal HLTAPI call executed ::sth::ospf::processOspfv3RouterType $procPrefix $lsaHandle $switchName $switchValue"
    upvar returnKeyedList returnKeyedList

    set switchName_ [lindex $switchName 0]
    set stcAttrName [::sth::sthCore::getswitchprop ::sth::ospf:: $procPrefix $switchName_ stcattr]
    set stcAttrValue "non-numeric"

    if {[catch {set ret [set stcAttrValue [::sth::sthCore::invoke stc::get $lsaHandle -RouterType]] } err] } {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }

    if {[string equal $stcAttrValue "0"]} {
        set stcAttrValue ""
    }
    set bitList [split $stcAttrValue "|" ]
    set newStcAttrValue 0

    foreach elem $bitList {
        switch $elem {
            BBIT {
                set newStcAttrValue [expr {1 + $newStcAttrValue}]
            }

            EBIT {
                set newStcAttrValue [expr {2 + $newStcAttrValue}]
            }

            VBIT {
                set newStcAttrValue [expr {4 + $newStcAttrValue}]
            }

            WBIT {
                set newStcAttrValue [expr {8 + $newStcAttrValue}]
            }

            default {
                ::sth::sthCore::processError returnKeyedList "Error: $elem" {}
                return $::sth::sthCore::FAILURE
            }
        }
    }

    set stcAttrValue $newStcAttrValue
    set i 0
    foreach switchName_ $switchName {
        set switchValue_ [lindex $switchValue $i]
        if {$switchName_ == "router_abr"} {
            if {$switchValue_ == "1"} {
                set stcAttrValue [expr {$stcAttrValue | 0x01}]
            } else {
                set stcAttrValue [expr {$stcAttrValue & 0xFE}]
            }
        } elseif {$switchName_ == "router_asbr"} {
            if {$switchValue_ == "1"} {
                set stcAttrValue [expr {$stcAttrValue | 0x02}]
            } else {
                set stcAttrValue [expr {$stcAttrValue & 0xFD}]
            }
        } elseif {$switchValue_ == "router_virtual_link_endpt"} {
            if {$switchValue_ == "1"} {
                set stcAttrValue [expr {$stcAttrValue | 0x04}]
            } else {
                set stcAttrValue [expr {$stcAttrValue & 0xFB}]
            }
        }
        incr i
    }

    if {[catch {set ret [::sth::ospf::doGenericConfig $procPrefix $lsaHandle $switchName_ $stcAttrValue]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::doGenericConfig Failed: $err" {}
        return $::sth::sthCore::FAILURE
    }
    if {$ret == $::sth::sthCore::FAILURE} {
        ::sth::sthCore::processError returnKeyedList "::sth::ospf::doGenericConfig Failed: $err"
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup sthOSPFFunctions
###\fn proc ::sth::ospf::getConfigObjHandles ( ospfRouterHandle )
###\brief Returns return $::sth::sthCore::SUCCESS when the function runs successfully. Otherwise, $::sth::sthCore::FAILURE.
###
###This procedure is used obtain the object handle of VlanIf, Ipv4If, Ipv6If, Ospfv2AuthenticationParams
###
###
###\param[in] switchStepValue contains the value of the swith step as the increment for the switch value.
###
###
###\author: Tong Zhou
###*/
###
### getConfigObjHandles ( ospfRouterHandle )
###
proc ::sth::ospf::getConfigObjHandles { ospfRouterHandle } {
    set objList {}

    if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $ospfRouterHandle -parent]} getStatus]} {
            return -code 1 -errorcode -1 $getStatus;
    } else {
            lappend objList Router $routerHandle
    }

    if {[catch {set getObjs [::sth::sthCore::invoke stc::get $routerHandle "-children-VlanIf -children-Ipv4If -children-Ipv6If"]} getStatus]} {
        return -code 1 -errorcode -1 $getStatus;
    } else {
        ###the gre delevery header has been configured. delete from the objList here
        if {$::sth::ospf::greIpHeader != "" } {
            set ipv4List [lindex $getObjs 3]
            set value $::sth::ospf::greIpHeader
            set ix [lsearch -exact $ipv4List $value]
            if {$ix >=0 } {
                    set ipv4List [lreplace $ipv4List $ix $ix]
            }
            set ipv6List [lindex [lindex $getObjs 5] 0]
            set ix [lsearch -exact $ipv6List $value]
            if {$ix >=0 } {
                    set ipv6List [lreplace $ipv6List $ix $ix]
            }

            lappend objList VlanIf [lindex $getObjs 1] Ipv4If $ipv4List Ipv6If $ipv6List
        } else {
            lappend objList VlanIf [lindex $getObjs 1] Ipv4If [lindex [lindex $getObjs 3] 0] Ipv6If [lindex [lindex $getObjs 5] 0]
        }
    }

    #get Aal5If
    if {[catch {set aal5IfHandle [::sth::sthCore::invoke stc::get $routerHandle "-children-Aal5If"]} errMsg]} {
            ::sth::sthCore::log debug "error occured while excuting \"stc::get $routerHandle -children-Aal5If\", errMsg: $errMsg."
    } else {
            lappend objList Aal5If $aal5IfHandle
    }

    if {[string first ospfv2 $ospfRouterHandle] >= 0} {
        if {[catch {set children [::sth::sthCore::invoke stc::get $ospfRouterHandle "-children-Ospfv2AuthenticationParams -children-TeParams"]} getStatus]} {
            return -code 1 -errorcode -1 $getStatus;
        } else {
            if {$children == ""} {
                return -code 1 -errorcode -1 "Ospfv2RouterConfig object created without Ospfv2AuthenticationParams object!"
            } else {
                set authObj [lindex $children 1]
                set teObj [lindex $children 3]
                lappend objList Ospfv2AuthenticationParams $authObj TeParams $teObj
            }
        }
        lappend objList Ospfv2RouterConfig $ospfRouterHandle
    } elseif {[string first ospfv3 $ospfRouterHandle] >= 0} {
        lappend objList Ospfv3RouterConfig $ospfRouterHandle
    }

    return $objList
}


array unset ::sth::ospf::ospfLsaTypeInfo

proc ::sth::ospf::emulation_ospf_control_flap_lsa {userArgsArrayVarName returnKeyedListVarName {level 1}} {
   variable ospfLsaTypeInfo

   set retVal [catch {
        upvar $level $userArgsArrayVarName userArgsArray
        upvar $level $returnKeyedListVarName returnKeyedList

        if {![info exists userArgsArray(flap_lsa)]} {
            return -code error [concat "Error:  No LSA has been specified to " \
                  "be flapped.  "]
        }

        set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $::sth::sthCore::GBLHNDMAP(sequencer)]

        catch { unset readvertiseCmds }

        foreach lsa $userArgsArray(flap_lsa) {
            set lsaParent [::sth::sthCore::invoke stc::get $lsa -parent]

            # Determine session type
            switch -regexp -- [string tolower $lsaParent] {
                {^ospfv2} {
                    set sessionType 2
                    set tableName emulation_ospfv2_control
                }
                {^ospfv3} {
                    set sessionType 3
                    set tableName emulation_ospfv3_control
                }
                default {
                    ::sth::sthCore::processError returnKeyedList \
                    [concat "Error:  Unable to determine session " \
                          "type using LSA's object information.  Possible " \
                          "that object's name format was changed " \
                          "internally.  "] {}
                    return $::sth::sthCore::FAILURE
                }
            }

            # Get defaults if not specified by user
            if {![info exists userArgsArray(flap_count)]} {
               set userArgsArray(flap_count) [::sth::sthCore::getswitchprop \
                     ::sth::ospf:: \
                     $tableName \
                     "flap_count" \
                     default]
            }

            if {![info exists userArgsArray(flap_down_time)]} {
               set userArgsArray(flap_down_time) [::sth::sthCore::getswitchprop \
                     ::sth::ospf:: \
                     $tableName \
                     "flap_down_time" \
                     default]
            }

            if {![info exists userArgsArray(flap_interval_time)]} {
               set userArgsArray(flap_interval_time) [::sth::sthCore::getswitchprop \
                     ::sth::ospf:: \
                     $tableName \
                     "flap_interval_time" \
                     default]
            }

            set rtrCfg [::sth::sthCore::invoke stc::get $lsa -parent]

            set lsa_handle $lsa
            if {[info exists ospfLsaTypeInfo]} {
                set lsa_handle $ospfLsaTypeInfo($lsa)
            }
            # Create the appropriate LSA command
            switch $sessionType {
                2 {
                    switch -exact -- $lsa_handle {
                        "asbrsummarylsa" {
                           set lsaCmd "Ospfv2AgeAsbrLsaCommand"
                        }
                        "externallsablock" {
                           set lsaCmd "Ospfv2AgeExternalLsaCommand"
                        }
                        "routerlsa" {
                           set lsaCmd "Ospfv2AgeRouterLsaCommand"
                        }
                        "networklsa" {
                           set lsaCmd "Ospfv2AgeNetworkLsaCommand"
                        }
                        "telsa" {
                           set lsaCmd "Ospfv2AgeTeLsaCommand"
                        }
                        "summarylsablock" {
                           set lsaCmd "Ospfv2AgeSummaryLsaCommand"
                        }
                        default {
                            if {[info exists ospfLsaTypeInfo]} {
                                ::sth::sthCore::processError returnKeyedList \
                                      [concat "Error:  Unable to flap LSAs " \
                                            "on OSPFv2 session $userArgsArray(handle).  " \
                                            "Unable to determine LSA type of LSA handle " \
                                            "\"$lsa\".  "] {}
                                return $::sth::sthCore::FAILURE
                            } else {
                                ::sth::sthCore::log hltcall "skip $lsa_handle when do flapping LSAs on OSPFv2 session $userArgsArray(handle)."
                                ::sth::sthCore::outputConsoleLog warning "skip $lsa_handle when do flapping LSAs on OSPFv2 session $userArgsArray(handle)."
                            }
                        }
                    }
                    if {[info exists ospfLsaTypeInfo]} {
                        set readvertiseCmds($rtrCfg) "Ospfv2ReadvertiseLsaCommand"
                    }
                }
                3 {
                    switch -exact -- $lsa_handle {
                        "ospfv3interarearouterlsablock" {
                           set lsaCmd "Ospfv3AgeInterAreaRouterLsaCommand"
                        }
                        "ospfv3asexternallsablock" {
                           set lsaCmd "Ospfv3AgeExternalLsaCommand"
                        }
                        "ospfv3routerlsa" {
                           set lsaCmd "Ospfv3AgeRouterLsaCommand"
                        }
                        "ospfv3networklsa" {
                           set lsaCmd "Ospfv3AgeNetworkLsaCommand"
                        }
                        "ospfv3nssalsablock" {
                           set lsaCmd "Ospfv3AgeNssaLsaCommand"
                        }
                        "ospfv3interareaprefixlsablk" {
                           set lsaCmd "Ospfv3AgeInterAreaPrefixLsaCommand"
                        }
                        default {
                            if {[info exists ospfLsaTypeInfo]} {
                                ::sth::sthCore::processError returnKeyedList \
                                      [concat "Error:  Unable to flap LSAs " \
                                            "on OSPFv3 session $userArgsArray(handle).  " \
                                            "Unable to determine LSA type of LSA handle " \
                                            "\"$lsa\".  "] {}
                                return $::sth::sthCore::FAILURE
                            } else {
                                ::sth::sthCore::log hltcall "skip $lsa_handle when do flapping LSAs on OSPFv3 session $userArgsArray(handle)."
                                ::sth::sthCore::outputConsoleLog warning "skip $lsa_handle when do flapping LSAs on OSPFv3 session $userArgsArray(handle)."
                            }
                        }
                    }
                    if {[info exists ospfLsaTypeInfo]} {
                        set readvertiseCmds($rtrCfg) "Ospfv3ReadvertiseLsaCommand"
                    }
                }
                default {
                   ::sth::sthCore::processError returnKeyedList \
                         [concat "Error:  Unable to determine session " \
                               "type using LSA's object information"] {}
                   return $::sth::sthCore::FAILURE
                }
            }
            if {[info exists ospfLsaTypeInfo]} {
                lappend lsaCmds($lsaCmd) $lsa
            }
        }

        catch {unset cmdList}

        # LSA flap interval command
        lappend cmdList [::sth::sthCore::invoke stc::create "waitCommand" -under $seqLoopCmd [list "-waitTime" $userArgsArray(flap_interval_time)]]

        # Age LSA command
        foreach lsaCmd [array names lsaCmds] {
           lappend cmdList [::sth::sthCore::invoke stc::create $lsaCmd -under $seqLoopCmd [list "-lsaList" $lsaCmds($lsaCmd)]]
        }

        # Down LSA interval command
        lappend cmdList [::sth::sthCore::invoke stc::create "waitCommand" -under $seqLoopCmd [list "-waitTime" $userArgsArray(flap_down_time)]]

        # Readvertise LSA command
        catch {unset readvertiseRtrCmds}
        foreach rtr [array names readvertiseCmds] {
           lappend readvertiseRtrCmds($readvertiseCmds($rtr)) $rtr
        }
        foreach readvertiseRtrCmd [array names readvertiseRtrCmds] {
          lappend cmdList [::sth::sthCore::invoke stc::create $readvertiseRtrCmd -under $seqLoopCmd [list "-routerList" $readvertiseRtrCmds($readvertiseRtrCmd)]]
        }

        # Configure sequencer
        ::sth::sthCore::invoke stc::config $seqLoopCmd [list "-IterationCount" $userArgsArray(flap_count) "-ExecutionMode" "BACKGROUND" "-GroupCategory" "REGULAR_COMMAND" "-ContinuousMode" FALSE "-ExecuteSynchronous" FALSE "-CommandList" $cmdList]

        ::sth::sthCore::invoke stc::config $::sth::sthCore::GBLHNDMAP(sequencer) "-CommandList $seqLoopCmd"

        #::sth::sthCore::doStcApply

        # Start the sequencer
        ::sth::sthCore::invoke stc::perform sequencerStart
        #if we don't wait here, the clean up will delete the sequencer object
        ::sth::sthCore::invoke ::stc::waituntilcomplete

        # Clean up
        foreach cmd $cmdList {
              ::sth::sthCore::invoke stc::delete $cmd
        }
        ::sth::sthCore::invoke stc::delete $seqLoopCmd

        #::sth::sthCore::doStcApply
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS
}


proc ::sth::ospf::emulation_ospf_control_common {switchArgs} {
    upvar $switchArgs userInputArgs
    array set ospfv2CmdNameArr {restore Ospfv2RestoreRouterCommand shutdown Ospfv2ShutdownRouterCommand advertise ProtocolAdvertiseCommand establish ProtocolEstablishCommand stop_hellos Ospfv2StopHellosCommand resume_hellos Ospfv2ResumeHellosCommand}
    array set ospfv3CmdNameArr {restore Ospfv3RestoreRoutersCommand shutdown Ospfv3ShutdownRoutersCommand advertise ProtocolAdvertiseCommand establish ProtocolEstablishCommand stop_hellos Ospfv3StopHellosCommand resume_hellos Ospfv3ResumeHellosCommand}
    array set attrNameArr {restore RouterList shutdown RouterList advertise ProtocolList establish ProtocolList stop_hellos RouterList resume_hellos RouterList}
    set ospfv2Handles ""
    set ospfv3Handles ""
    set mode $userInputArgs(mode)
    #port_handle always takes precendence over ospf handle
    if {[info exist userInputArgs(port_handle)] } {
        set portHandles $userInputArgs(port_handle)
        foreach portHandle $portHandles {
            if {[catch {set ret [set rHandles [::sth::sthCore::invoke stc::get $portHandle affiliationport-Sources]]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                    return $::sth::sthCore::FAILURE
            }
            foreach rHandle $rHandles {
                lappend ospfv2Handles [::sth::sthCore::invoke stc::get $rHandle -children-ospfv2routerconfig]
                lappend ospfv3Handles [::sth::sthCore::invoke stc::get $rHandle -children-ospfv3routerconfig]
            }
        }
    } elseif {[info exist userInputArgs(handle)] } {
        #The port_handle is not specified, start the ospf router specified.
        set rHandles $userInputArgs(handle)
        foreach rHandle $rHandles {
            if {[regexp "ospfv2" $rHandle]} {
                lappend ospfv2Handles $rHandle
            } else {
                lappend ospfv3Handles $rHandle
            }
        }
    }
    set attrName $attrNameArr($mode)
    if {$ospfv2Handles != "" && $ospfv2Handles !={}} {
        set v2CmdName $ospfv2CmdNameArr($mode)
        ::sth::sthCore::invoke stc::perform $v2CmdName -$attrName $ospfv2Handles
    }
    if {$ospfv3Handles != "" && $ospfv3Handles != {}} {
        set v3CmdName $ospfv3CmdNameArr($mode)
        ::sth::sthCore::invoke stc::perform $v3CmdName -$attrName $ospfv3Handles
    }
    return $::sth::sthCore::SUCCESS
}

#Sapna Leupold
proc ::sth::ospf::IsOspfRouterHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $msgName errorMsg

    if {[catch {set protocolHandle [::sth::sthCore::invoke stc::get $handle -parent]} getStatus]} {
            set errorMsg $getStatus
            return $FAILURE
    } else {
        if {[llength $protocolHandle] <= 0} {
            set errorMsg "The router is not running rsvp protocol."
            return $FAILURE
        } else {
            if {[regexp "router|emulateddevice|host" $protocolHandle]} {
                #set errorMsg $protocolHandle
                return $SUCCESS
            } else {
                return $FAILURE
            }
        }
    }
}

#Sapna Leupold
proc ::sth::ospf::makekeyedlist {rtrHandle type} {

    upvar returnKeyedList returnKeyedList;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;

    if {$type == "ospfv2routerresults"} {
        set TableName ::sth::ospf::emulation_ospfv2_info_stcattr
        set ospfHltList [array names $TableName]
    } else {
        set TableName ::sth::ospf::emulation_ospfv3_info_stcattr
        set ospfHltList [array names $TableName]
    }

    array set stcAttrs [::sth::sthCore::invoke stc::get $rtrHandle]

   # puts "Attributes in $rtrHandle:"
#    foreach stcAttrName [array names stcAttrs] {
#        set stcAttrValue $stcAttrs($stcAttrName)
#        #puts "  $stcAttrName: $stcAttrs($stcAttrName)"
#        keylset ospfv2StatsKeyedList $stcAttrName $stcAttrValue
#    }

    foreach hltName $ospfHltList {
        if {$type == "ospfv2routerresults"} {
            set stcName $::sth::ospf::emulation_ospfv2_info_stcattr($hltName)
        } else {
            set stcName $::sth::ospf::emulation_ospfv3_info_stcattr($hltName)
        }
        if {$stcName != "_none_"} {
            set stcName -$stcName
            set stcValue $stcAttrs($stcName);
            keylset returnKeyedList $hltName $stcValue
        }
    }

    return $::sth::sthCore::SUCCESS;
}

#Sapna Leupold
proc ::sth::ospf::getOspfcounterResults {rtrHandle type} {

    upvar returnKeyedList returnKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);

    set routerResults ""
    set ospfVType $type
    set children [::sth::sthCore::invoke stc::get $rtrHandle -children]
    set rrlen [expr [string length $ospfVType] - 1]
    foreach child $children {
        set prefix [string tolower [string range $child 0 $rrlen]]
        if {$prefix == $ospfVType} {
            set routerResults $child
            set cmdRet [::sth::ospf::makekeyedlist $child $ospfVType]
        }
    }
}


#Sapna Leupold
proc ::sth::ospf::subscribeOspfRoutercounters {handle ConfigClassId ResultClassId} {

    upvar returnKeyedList returnKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);

    #set ResultDataSet [stc::create "ResultDataSet" -under $ProjHnd ]
    if {[catch {set ResultDataSet [::sth::sthCore::invoke stc::create ResultDataSet -under $::sth::sthCore::GBLHNDMAP(project)]} createStatus ]} {
        ::sth::sthCore::processError returnKeyedList "stc::create Failed: Error creating ResultDataSet: $createStatus" {}
        return $::sth::sthCore::FAILURE
    }

    set ResultQuery [::sth::sthCore::invoke stc::create "ResultQuery" \
                     -under $ResultDataSet \
                     -ResultRootList $ProjHnd \
                     -ConfigClassId $ConfigClassId \
                     -ResultClassId $ResultClassId ]

    if {$ConfigClassId == "Ospfv2RouterConfig"} {
        set ::sth::ospf::ospfv2Resultdataset $ResultQuery
    } else {
        set ::sth::ospf::ospfv3Resultdataset $ResultQuery
    }

    ::sth::sthCore::doStcApply
    if {[catch {::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $ResultDataSet} performStatus]} {
        ::sth::sthCore::processError returnKeyedList "stc::perform Failed: Error while setting ResultDataSetSubscribe: $performStatus" {}
        return -code 1 -errorcode -1 $performStatus;
    }
}

#Sapna Leupold
proc ::sth::ospf::getOspfCounters {handle type} {

    upvar returnKeyedList returnKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ProjHnd $::sth::sthCore::GBLHNDMAP(project);

    if {$type == "ospfv2RouterResults"} {
        set cmdRet [::sth::ospf::subscribeOspfRoutercounters $handle Ospfv2RouterConfig Ospfv2RouterResults]
        set cmdRet [::sth::ospf::getOspfcounterResults $handle "ospfv2routerresults"]
    } else {
        set cmdRet [::sth::ospf::subscribeOspfRoutercounters $handle Ospfv3RouterConfig Ospfv3RouterResults]
        set cmdRet [::sth::ospf::getOspfcounterResults $handle "ospfv3routerresults"]
    }
    set router_state [::sth::sthCore::invoke stc::get $handle -RouterState]
    set adjacency_status [::sth::sthCore::invoke stc::get $handle -AdjacencyStatus]
    keylset returnKeyedList router_state $router_state
    keylset returnKeyedList adjacency_status $adjacency_status
}

proc ::sth::ospf::configBfdRegistration {rtrHandle mode switchArgs} {
    upvar $switchArgs userArgsArray

    if {[catch {set handle [::sth::sthCore::invoke stc::get $rtrHandle -children]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList
    }

    switch -regexp -- $handle {
        "ospfv2routerconfig" {
                set ipVersion 4
                set ospfRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ospfv2routerconfig]
        }
        "ospfv3routerconfig" {
                set ipVersion 6
                set ospfRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ospfv3routerconfig]
        }
        default {
        }
    }

    if {![info exist ospfRtrHandle]} {
        ::sth::sthCore::processError returnKeyedList "Failed finding ospfrouterconfig object" {}
        return -code error $returnKeyedList
    }

    if {[catch {set ipIfHandle [ ::sth::sthCore::invoke stc::get $rtrHandle -children-ipv$ipVersion\if ]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList
    }

     #For Ipv6, there are two Ipv6Ifs under the router, get the global link one
        if {$ipVersion == 6} {
                set ipIfHandle [lindex $ipIfHandle 0]
        }
        if {[catch {set ipaddr [::sth::sthCore::invoke stc::get $ipIfHandle -Address]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
        }


    ##validate BFD having different ipaddr on different interfaces
    #if {![::sth::sthCore::IsBfdIpAddrValid $rtrHandle $ipaddr]} {
    #    ::sth::sthCore::processError returnKeyedList "unable to enable BFD under different interfaces with the same IP address" {}
    #    return -code error $returnKeyedList
    #}

    if {$userArgsArray(bfd_registration) == "1"} {
        #create bfdrouterconfig
        set bfdrtrcfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
        if {[llength $bfdrtrcfg] == 0} {
            if {[catch {set bfdrtrcfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $rtrHandle]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                return -code error $returnKeyedList
            }
        }
        if {[catch {::sth::sthCore::invoke stc::config $ospfRtrHandle "-EnableBfd true"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList
        }
    } elseif {$userArgsArray(bfd_registration) == "0"} {
        if {[catch {::sth::sthCore::invoke stc::config $ospfRtrHandle "-EnableBfd false"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList
        }
    }
}


proc ::sth::ospf::emulation_ospf_route_info_generic { ospfRouterHandle returnKeyedListVarName} {
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    upvar 1 $returnKeyedListVarName returnKeyedList

    if {[catch {set ospfHandle [::sth::sthCore::invoke stc::get $ospfRouterHandle -children-Ospfv2RouterConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not get children object ospfv2routerconfig from router $ospfRouterHandle" {}
        return $FAILURE
    }

    if { $ospfHandle == "" } {
        if {[catch {set ospfHandle [::sth::sthCore::invoke stc::get $ospfRouterHandle -children-Ospfv3RouterConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not get children object ospfv3routerconfig from router $ospfRouterHandle" {}
            return $FAILURE
        }
        if { $ospfHandle != "" } {
            set version "ospfv3"
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: input router is not a ospf router." {}
            return $FAILURE
        }
    } else {
        set version "ospfv2"
    }

    if {$version == "ospfv2"} {
        set subCmdPreName "emulation_ospfv2_route_info"
        set returnKeyTypes {
            router
            network
            summary
            asbr_summary
            external
            nssa
            te_router
            te_link
        }
    } else {
        set subCmdPreName "emulation_ospfv3_route_info"
        set returnKeyTypes {
            router
            network
            external
            nssa
            link
            intra_area_prefix
            inter_area_prefix
            inter_area_router
        }
    }

    if { [::sth::ospf::GetOspfRouteInfo $ospfHandle $subCmdPreName $returnKeyTypes returnKeyedList]} {
        return $SUCCESS
    } else {
        return $FAILURE
    }


}

proc ::sth::ospf::GetOspfRouteInfo { ospfHandle cmdPreName returnKeyTypes returnKeyedListVarName} {
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;

    foreach returnKeyType $returnKeyTypes {
        set routeType [set ::sth::ospf::$cmdPreName\_$returnKeyType\_stcobj(adv_router_id)]
        if {[catch {set routeHdlArr [::sth::sthCore::invoke stc::get $ospfHandle -Children-$routeType]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error: Can not get children object $routeType from $ospfHandle. Error Msg: $errMsg." {}
                return $FAILURE
        }
        if {$routeHdlArr == ""} {
                continue
        }
        foreach routeHdl $routeHdlArr {
            array unset routeAttrs
            if {[catch {array set routeAttrs [::sth::sthCore::invoke stc::get $routeHdl]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: Can not get attributes info from $routeHdl. Error Msg: $errMsg." {}
                    return $FAILURE
            }

            if { ![info exists routeAttrs(-children)]} {
                    continue
            }
            foreach childHdl $routeAttrs(-children) {
                if {[catch {array set $childHdl [::sth::sthCore::invoke stc::get $childHdl]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error: Can not get attributes info from $routeHdl. Error Msg: $errMsg." {}
                        return $FAILURE
                }
                #puts [array get $childHdl]
            }

            if {[regexp -nocase "LinkTlv" $childHdl]} {
                set returnKeyType te_link
            }
            if {[regexp -nocase "RouterTlv" $childHdl]} {
                set returnKeyType te_router
            }

            set returnKeyNameList [array names ::sth::ospf::$cmdPreName\_$returnKeyType\_mode]
            foreach returnKeyName $returnKeyNameList {
                set supported [set ::sth::ospf::$cmdPreName\_$returnKeyType\_supported($returnKeyName)]
                if {$supported == "false"} {
                    continue
                }

                set objName [set ::sth::ospf::$cmdPreName\_$returnKeyType\_stcobj($returnKeyName)]
                set stcName [set ::sth::ospf::$cmdPreName\_$returnKeyType\_stcattr($returnKeyName)]

                if {$objName == $routeType} {
                    set stcValue $routeAttrs(-$stcName)
                    keylset returnKeyedList $returnKeyType\.lsa_handle\.$routeHdl\.$returnKeyName $stcValue
                } elseif {$returnKeyType == "router" } {
                    if {[info exists routeAttrs(-children)]} {
                        set i "1"
                        foreach childHdl $routeAttrs(-children) {
                            set stcValue [set $childHdl\(-$stcName)]
                            regsub {<Index>} $returnKeyName $i keyName
                            keylset returnKeyedList $returnKeyType\.lsa_handle\.$routeHdl\.$keyName $stcValue
                            incr i
                        }
                    }
                } elseif {$returnKeyType == "network" } {
                    if {[info exists routeAttrs(-children)]} {
                        set stcValue ""
                        foreach childHdl $routeAttrs(-children) {
                            lappend stcValue [set $childHdl\(-$stcName)]
                        }
                        keylset returnKeyedList $returnKeyType\.lsa_handle\.$routeHdl\.$returnKeyName $stcValue
                    }
                } else {
                    if {[info exists routeAttrs(-children)]} {
                        set stcValue [set $childHdl\(-$stcName)]
                        keylset returnKeyedList $returnKeyType\.lsa_handle\.$routeHdl\.$returnKeyName $stcValue
                    }
                }
            }
        }

    }

    return $SUCCESS
}




##############################Functions for ospf_lsa_generator#######################
##############################################
#emulation_ospf_lsa_generator_create
##############################################
##########LOGIC############
#A)if session_type is ospfv3?
#   1)Create and config Ospfv3LsaGenParams
#   2)Create Ipv6RouteGenParams and configure INTRAAREA INTERAREA and EXTERNAL routes
# else (ospfv2)
#   1)Create and config Ospfv2LsaGenParams
#   2)if ospfv2_enable_te is true then create and configure TeParams attributes
#   3)if ospfv2_enable_sr is true then create and configure Ospfv2SegmentRouteParams attributes
#   4)Create Ipv4RouteGenParams and configure STUB SUMMARY and EXTERNAL routes
#B)create and configure topology
#C)routegenapply(Expand)
#D)Collect Return handles
###########LOGIC ENDS####
proc ::sth::ospf::emulation_ospf_lsa_generator_create { userArray  returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ospf_lsa_generator_create"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $userArray userArgsArray;
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    set procPrefix "emulation_ospf_lsa_generator"

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
                    ::sth::sthCore::processError returnKeyedList "Error: handle not provided by user for -mode $userArgsArray(mode)" {}
                    return
        }
        set ospfHandle $userArgsArray(handle)

        #A)if session_type is ospfv3
        if {$userArgsArray(session_type)=="ospfv3"} {
            #1)Create and config Ospfv3LsaGenParams
            set Ospfv3LsaGenParamsHdl  [stc::create Ospfv3LsaGenParams -under $::sth::GBLHNDMAP(project)]
            set LsaGenParamsHdl $Ospfv3LsaGenParamsHdl
            stc::config $Ospfv3LsaGenParamsHdl -SelectedRouterRelation-targets $ospfHandle
            ConfigOspfv3LsaGenParams $Ospfv3LsaGenParamsHdl create

            #2)Create Ipv6RouteGenParams and configure INTRAAREA INTERAREA and EXTERNAL routes
            #INTRAAREA
            set ipv6HndIntra [stc::create Ipv6RouteGenParams -under $Ospfv3LsaGenParamsHdl]
            procOspfv3Intra $ipv6HndIntra create
            set ospfRouteHndIntra [stc::create Ospfv3LsaGenRouteAttrParams -under $ipv6HndIntra]
            stc::config $ospfRouteHndIntra -RouteType INTRAAREA
            procOspfv3RouteAttrIntra $ospfRouteHndIntra create

            #INTERAREA
            set ipv6HndInter [stc::create Ipv6RouteGenParams -under $Ospfv3LsaGenParamsHdl]
            procOspfv3Inter $ipv6HndInter create
            set ospfRouteHndInter [stc::create Ospfv3LsaGenRouteAttrParams -under $ipv6HndInter]
            stc::config $ospfRouteHndInter -RouteType INTERAREA
            procOspfv3RouteAttrInter $ospfRouteHndInter create

            #EXTERNAL
            set ipv6HndExt [stc::create Ipv6RouteGenParams -under $Ospfv3LsaGenParamsHdl]
            procOspfv3Ext $ipv6HndExt create
            set ospfRouteHndExt [stc::create Ospfv3LsaGenRouteAttrParams -under $ipv6HndExt]
            stc::config $ospfRouteHndExt -RouteType EXTERNAL
            procOspfv3RouteAttrExt $ospfRouteHndExt create

        } else {
            #1)Create and config Ospfv2LsaGenParams
            set Ospfv2LsaGenParamsHdl  [stc::create Ospfv2LsaGenParams -under $::sth::GBLHNDMAP(project)]
            set LsaGenParamsHdl $Ospfv2LsaGenParamsHdl
            stc::config $Ospfv2LsaGenParamsHdl -SelectedRouterRelation-targets $ospfHandle
            ConfigOspfv2LsaGenParams $Ospfv2LsaGenParamsHdl create

            #2)if ospfv2_enable_te is true then create and configure TeParams attributes
            if { $userArgsArray(ospfv2_enable_te) == "true" } {
                set TeParamsHdl  [stc::create TeParams -under $Ospfv2LsaGenParamsHdl]
                ConfigOspfv2TeParams $TeParamsHdl create
            }
            #3)if ospfv2_enable_sr is true then create and configure Ospfv2SegmentRouteParams attributes
            if { $userArgsArray(ospfv2_enable_sr) == "true" } {
                set Ospfv2SegmentRouteParamsHdl  [stc::create Ospfv2SegmentRouteParams -under $Ospfv2LsaGenParamsHdl]
                ConfigOspfv2SegmentRouteParams $Ospfv2SegmentRouteParamsHdl create
            }
            #4)Create Ipv4RouteGenParams and configure STUB SUMMARY and EXTERNAL routes
            ##Stub Routes
            set ipv4HndStub [stc::create Ipv4RouteGenParams -under $Ospfv2LsaGenParamsHdl]
            procStub $ipv4HndStub create
            set ospfRouteHndStub [stc::create Ospfv2LsaGenRouteAttrParams -under $ipv4HndStub]
            stc::config $ospfRouteHndStub -RouteType STUB
            procRouteAttrStub $ospfRouteHndStub create

            #Summary Routes
            set ipv4HndSum [stc::create Ipv4RouteGenParams -under $Ospfv2LsaGenParamsHdl]
            procSum $ipv4HndSum create
            set ospfRouteHndSum [stc::create Ospfv2LsaGenRouteAttrParams -under $ipv4HndSum]
            stc::config $ospfRouteHndSum -RouteType SUMMARY
            procRouteAttrSum $ospfRouteHndSum create

            ##External Routes
            set ipv4HndExt [stc::create Ipv4RouteGenParams -under $Ospfv2LsaGenParamsHdl]
            procExt $ipv4HndExt create
            set ospfRouteHndExt [stc::create Ospfv2LsaGenRouteAttrParams -under $ipv4HndExt]
            stc::config $ospfRouteHndExt -RouteType EXTERNAL
            procRouteAttrExt $ospfRouteHndExt create
        }

        #B)Create and configure topology
        switch -exact -- $userArgsArray(topo_type) {
                tree {
                    set TreeTopologyGenParamsHdl [stc::create TreeTopologyGenParams -under $LsaGenParamsHdl]
                    configTreeTopo $TreeTopologyGenParamsHdl create
                }
                grid {
                    set GridTopologyGenParamsHdl [stc::create GridTopologyGenParams -under $LsaGenParamsHdl]
                    configGridTopo $GridTopologyGenParamsHdl create
                }
                full_mesh {
                    set FullMeshTopologyGenParamsHdl [stc::create FullMeshTopologyGenParams -under $LsaGenParamsHdl]
                    configFullMeshTopo $FullMeshTopologyGenParamsHdl create
                }
                ring {
                    set RingTopologyGenParamsHdl [stc::create RingTopologyGenParams -under $LsaGenParamsHdl]
                    configRingTopo $RingTopologyGenParamsHdl create
                }
                hub_spoke {
                    set HubSpokeTopologyGenParamsHdl [stc::create HubSpokeTopologyGenParams -under $LsaGenParamsHdl]
                    configHubTopo $HubSpokeTopologyGenParamsHdl create
                }
            }

        #C)Expand command
        stc::perform routegenapply -genparams $LsaGenParamsHdl -deleteroutesonapply no

        if {[llength $ospfHandle] > 1} {
            if {[string equal -nocase $userArgsArray(session_type) ospfv3]} {
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3RouterConfig -rootlist $ospfHandle]
                set ospfv3HndList $rtn(-ObjectList)

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3InterAreaPrefixLsaBlk -rootlist $ospfv3HndList]
                set Ospfv3InterAreaPrefixLsaBlk $rtn(-ObjectList)
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv6NetworkBlock -rootlist $rtn(-ObjectList)]
                keylset returnKeyedList inter_lsa_block $rtn(-ObjectList)

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3IntraAreaPrefixLsaBlk -rootlist $ospfv3HndList]
                set Ospfv3IntraAreaPrefixLsaBlk $rtn(-ObjectList)
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv6NetworkBlock -rootlist $rtn(-ObjectList)]
                keylset returnKeyedList intra_lsa_block $rtn(-ObjectList)

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3AsExternalLsaBlock -rootlist $ospfv3HndList]
                set Ospfv3AsExternalLsaBlock $rtn(-ObjectList)
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv6NetworkBlock -rootlist $rtn(-ObjectList)]
                keylset returnKeyedList external_lsa_block $rtn(-ObjectList)

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3NssaLsaBlock -rootlist $ospfv3HndList]
                set Ospfv3NssaLsaBlock $rtn(-ObjectList)
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv6NetworkBlock -rootlist $rtn(-ObjectList)]
                keylset returnKeyedList nssa_lsa_block $rtn(-ObjectList)
                
                #Get handles of OSPFv3 LSAs (multiple OSPF handles) and add them in returnKeyedList -- Jeff Jun30,2017
                if { $Ospfv3InterAreaPrefixLsaBlk != "" } {
                    keylset returnKeyedList inter_prefix_lsa_block_handle $Ospfv3InterAreaPrefixLsaBlk
                }
                if { $Ospfv3IntraAreaPrefixLsaBlk != "" } {
                    keylset returnKeyedList intra_prefix_lsa_block_handle $Ospfv3IntraAreaPrefixLsaBlk
                }
                if { $Ospfv3AsExternalLsaBlock != "" } {
                    keylset returnKeyedList v3_external_lsa_block_handle $Ospfv3AsExternalLsaBlock
                }
                if { $Ospfv3NssaLsaBlock != "" } {
                    keylset returnKeyedList v3_nssa_lsa_block_handle $Ospfv3NssaLsaBlock
                }

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3RouterLsa -rootlist $ospfv3HndList]
                set Ospfv3RouterLsa $rtn(-ObjectList)
                
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3NetworkLsa -rootlist $ospfv3HndList]
                set Ospfv3NetworkLsa $rtn(-ObjectList)
                
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3InterAreaRouterLsaBlock -rootlist $ospfv3HndList]
                set Ospfv3InterAreaRouterLsaBlock $rtn(-ObjectList)
                
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv3LinkLsaBlk -rootlist $ospfv3HndList]
                set Ospfv3LinkLsaBlk $rtn(-ObjectList)
                
                if { $Ospfv3RouterLsa != "" } {
                    keylset returnKeyedList v3_router_lsa_handle $Ospfv3RouterLsa
                }
                if { $Ospfv3NetworkLsa != "" } {
                    keylset returnKeyedList v3_network_lsa_handle $Ospfv3NetworkLsa
                }
                if { $Ospfv3InterAreaRouterLsaBlock != "" } {
                    keylset returnKeyedList inter_router_lsa_handle $Ospfv3InterAreaRouterLsaBlock
                }
                if { $Ospfv3LinkLsaBlk != "" } {
                    keylset returnKeyedList link_lsa_handle $Ospfv3LinkLsaBlk
                }

            } elseif {[string equal -nocase $userArgsArray(session_type) ospfv2]} {
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ospfv2RouterConfig -rootlist $ospfHandle]
                set ospfv2HndList $rtn(-ObjectList)

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className ExternalLsaBlock -rootlist $ospfv2HndList]
                set ExternalLsaBlock $rtn(-ObjectList)
                set ExtList ""
                set nssaList ""
                foreach ELB $ExternalLsaBlock {
                    set ELB_type [stc::get $ELB -Type]
                    if { $ELB_type == "EXT" } {
                        lappend ExtList [stc::get $ELB -children-Ipv4NetworkBlock]
                    } elseif { $ELB_type == "NSSA" } {
                        lappend nssaList [stc::get $ELB -children-Ipv4NetworkBlock]
                    }
                }
                
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className SummaryLsaBlock -rootlist $ospfv2HndList]
                set SummaryLsaBlock $rtn(-ObjectList)
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv4NetworkBlock -rootlist $rtn(-ObjectList)]
                set SumList $rtn(-ObjectList)

                #STUBLsaBlock
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className routerlsa -rootlist $ospfv2HndList]
                set routerlsa $rtn(-ObjectList)
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className RouterLsaLink -rootlist $rtn(-ObjectList)]
                set RouterLsaLink $rtn(-ObjectList)
                set stubList ""
                foreach RLL $RouterLsaLink {
                    set stub_network [stc::get $RLL -LinkType]
                    if { $stub_network == "STUB_NETWORK" } {
                        lappend stubList [stc::get $RLL -children-Ipv4NetworkBlock]
                    }
                }
                if { $SumList != "" } {
                    keylset returnKeyedList summary_lsa_block $SumList
                }
                if { $ExtList != "" } {
                    keylset returnKeyedList external_lsa_block $ExtList
                }
                if { $stubList != "" } {
                    keylset returnKeyedList stub_lsa_block $stubList
                }
                if { $nssaList != "" } {
                    keylset returnKeyedList nssa_lsa_block $nssaList
                }
                
                #Get handles of OSPFv2 LSAs (multiple OSPF handles) and add them in returnKeyedList -- Jeff Jun30,2017
                if { $SummaryLsaBlock != "" } {
                    keylset returnKeyedList summary_lsa_block_handle $SummaryLsaBlock
                }
                if { $ExternalLsaBlock != "" } {
                    keylset returnKeyedList external_lsa_block_handle $ExternalLsaBlock
                }
                if { $routerlsa != "" } {
                    keylset returnKeyedList stub_lsa_block_handle $routerlsa
                }

                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className NetworkLsa -rootlist $ospfv2HndList]
                set NetworkLsa $rtn(-ObjectList)
                
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className AsbrSummaryLsa -rootlist $ospfv2HndList]
                set AsbrSummaryLsa $rtn(-ObjectList)
                
                if { $NetworkLsa != "" } {
                    keylset returnKeyedList network_lsa_handle $NetworkLsa
                }
                if { $AsbrSummaryLsa != "" } {
                    keylset returnKeyedList asbr_summary_handle $AsbrSummaryLsa
                }
                
            }
            if { $LsaGenParamsHdl != "" } {
                keylset returnKeyedList handle $LsaGenParamsHdl
            }
        } else {
            #D)List of handles(summary_lsa_block,external_lsa_block,stub_lsa_block,nssa_lsa_block) to return, Can be used to create traffic
            if {$userArgsArray(session_type)=="ospfv2"} {
                set routeConfig [stc::get $ospfHandle -children-Ospfv2RouterConfig]
                #ExternalLsaBlock and #NSSALsaBlock
                set ExtList ""
                set nssaList ""
                set ExternalLsaBlock [stc::get $routeConfig -children-ExternalLsaBlock]
                foreach ELB $ExternalLsaBlock {
                    set ELB_type [stc::get $ELB -Type]
                    if { $ELB_type == "EXT" } {
                        lappend ExtList [stc::get $ELB -children-Ipv4NetworkBlock]
                    } elseif { $ELB_type == "NSSA" } {
                        lappend nssaList [stc::get $ELB -children-Ipv4NetworkBlock]
                    }
                }
                #SummaryLsaBlock
                set SumList ""
                set SummaryLsaBlock [stc::get $routeConfig -children-SummaryLsaBlock]
                foreach SLB $SummaryLsaBlock {
                        lappend SumList [stc::get $SLB -children-Ipv4NetworkBlock]
                }
                #STUBLsaBlock
                set stubList ""
                set routerlsa [stc::get $routeConfig -children-routerlsa]
                foreach RL $routerlsa {
                    set RouterLsaLink [stc::get $RL -children-RouterLsaLink]
                    foreach RLL $RouterLsaLink {
                        set stub_network [stc::get $RLL -LinkType]
                        if { $stub_network == "STUB_NETWORK" } {
                            lappend stubList [stc::get $RLL -children-Ipv4NetworkBlock]
                        }
                    }
                }
                if { $SumList != "" } {
                    keylset returnKeyedList summary_lsa_block $SumList
                }
                if { $ExtList != "" } {
                    keylset returnKeyedList external_lsa_block $ExtList
                }
                if { $stubList != "" } {
                    keylset returnKeyedList stub_lsa_block $stubList
                }
                if { $nssaList != "" } {
                    keylset returnKeyedList nssa_lsa_block $nssaList
                }
                #Get handles of OSPFv2 LSAs and add them in returnKeyedList -- Jeff Jun30,2017
                if { $SummaryLsaBlock != "" } {
                    keylset returnKeyedList summary_lsa_block_handle $SummaryLsaBlock
                }
                if { $ExternalLsaBlock != "" } {
                    keylset returnKeyedList external_lsa_block_handle $ExternalLsaBlock
                }
                if { $routerlsa != "" } {
                    keylset returnKeyedList stub_lsa_block_handle $routerlsa
                }
                set NetworkLsa [stc::get $routeConfig -children-NetworkLsa]
                set AsbrSummaryLsa [stc::get $routeConfig -children-AsbrSummaryLsa]
                if { $NetworkLsa != "" } {
                    keylset returnKeyedList network_lsa_handle $NetworkLsa
                }
                if { $AsbrSummaryLsa != "" } {
                    keylset returnKeyedList asbr_summary_handle $AsbrSummaryLsa
                }
                
                
            } else {
            #E)List of handles(inter_lsa_block,intra_lsa_block,external_lsa_block,nssa_lsa_block) to return, Can be used to create traffic
                set routeConfig [stc::get $ospfHandle -children-Ospfv3RouterConfig]
                #Ospfv3InterAreaPrefixLsaBlk
                set interList ""
                set Ospfv3InterAreaPrefixLsaBlk [stc::get $routeConfig -children-Ospfv3InterAreaPrefixLsaBlk]
                foreach Ospfv3InterAreaPrefLsaBlk $Ospfv3InterAreaPrefixLsaBlk {
                        lappend interList [stc::get $Ospfv3InterAreaPrefLsaBlk -children-Ipv6NetworkBlock]
                }
                #Ospfv3IntraAreaPrefixLsaBlk
                set intraList ""
                set Ospfv3IntraAreaPrefixLsaBlk [stc::get $routeConfig -children-Ospfv3IntraAreaPrefixLsaBlk]
                foreach Ospfv3IntraAreaPrefLsaBlk $Ospfv3IntraAreaPrefixLsaBlk {
                        lappend intraList [stc::get $Ospfv3IntraAreaPrefLsaBlk -children-Ipv6NetworkBlock]
                }
                #Ospfv3AsExternalLsaBlock
                set exterList ""
                set Ospfv3AsExternalLsaBlock [stc::get $routeConfig -children-Ospfv3AsExternalLsaBlock]
                foreach Ospfv3AsExtLsaBlk $Ospfv3AsExternalLsaBlock {
                        lappend exterList [stc::get $Ospfv3AsExtLsaBlk -children-Ipv6NetworkBlock]
                }
                #Ospfv3NssaLsaBlock
                set nssaV3List ""
                set Ospfv3NssaLsaBlocks [stc::get $routeConfig -children-Ospfv3NssaLsaBlock]
                foreach Ospfv3NssaLsaBlock $Ospfv3NssaLsaBlocks {
                        lappend nssaV3List [stc::get $Ospfv3NssaLsaBlock -children-Ipv6NetworkBlock]
                }

                if { $interList != "" } {
                    keylset returnKeyedList inter_lsa_block $interList
                }
                if { $intraList != "" } {
                    keylset returnKeyedList intra_lsa_block $intraList
                }
                if { $exterList != "" } {
                    keylset returnKeyedList external_lsa_block $exterList
                }
                if { $nssaV3List != "" } {
                    keylset returnKeyedList nssa_lsa_block $nssaV3List
                }
                #Get handles of OSPFv3 LSAs and add them in returnKeyedList -- Jeff Jun30,2017
                if { $Ospfv3InterAreaPrefixLsaBlk != "" } {
                    keylset returnKeyedList inter_prefix_lsa_block_handle $Ospfv3InterAreaPrefixLsaBlk
                }
                if { $Ospfv3IntraAreaPrefixLsaBlk != "" } {
                    keylset returnKeyedList intra_lsa_block_handle $Ospfv3IntraAreaPrefixLsaBlk
                }
                if { $Ospfv3AsExternalLsaBlock != "" } {
                    keylset returnKeyedList v3_external_lsa_block_handle $Ospfv3AsExternalLsaBlock
                }
                if { $Ospfv3NssaLsaBlocks != "" } {
                    keylset returnKeyedList v3_nssa_lsa_block_handle $Ospfv3NssaLsaBlocks
                }
                set Ospfv3RouterLsa [stc::get $routeConfig -children-Ospfv3RouterLsa]
                set Ospfv3NetworkLsa [stc::get $routeConfig -children-Ospfv3NetworkLsa]
                set Ospfv3InterAreaRouterLsaBlock [stc::get $routeConfig -children-Ospfv3InterAreaRouterLsaBlock]
                set Ospfv3LinkLsaBlk [stc::get $routeConfig -children-Ospfv3LinkLsaBlk]
                
                if { $Ospfv3RouterLsa != "" } {
                    keylset returnKeyedList v3_router_lsa_handle $Ospfv3RouterLsa
                }
                if { $Ospfv3NetworkLsa != "" } {
                    keylset returnKeyedList v3_network_lsa_handle $Ospfv3NetworkLsa
                }
                if { $Ospfv3InterAreaRouterLsaBlock != "" } {
                    keylset returnKeyedList inter_router_lsa_handle $Ospfv3InterAreaRouterLsaBlock
                }
                if { $Ospfv3LinkLsaBlk != "" } {
                    keylset returnKeyedList link_lsa_handle $Ospfv3LinkLsaBlk
                }
            }
            if { $LsaGenParamsHdl != "" } {
                keylset returnKeyedList handle $LsaGenParamsHdl
            }
            
        }
    } returnedString]

    if {$retVal} {
       ::sth::sthCore::processError returnKeyedList $returnedString {}
       keylset returnKeyedList status $::sth::sthCore::FAILURE
    }

    return $returnKeyedList
}

##############################################
#emulation_ospf_lsa_generator_delete
##############################################
##########LOGIC############
#1)Get ospf router handle from userArgsArray(handle) [ospfv2lsagenparams or ospfv3lsagenparams]
#2)if session_type is ospfv2
#       get all children of Ospfv2RouterConfig and delete
# else(ospfv3)
#       get all children of Ospfv3RouterConfig and delete
###########LOGIC ENDS####
proc ::sth::ospf::emulation_ospf_lsa_generator_delete { userArray  returnKeyedListVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $userArray userArgsArray;


    set _OrigHltCmdName "emulation_ospf_lsa_generator"
    set _hltCmdName "emulation_ospf_lsa_generator_delete"
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"


    if {[info exists userArgsArray(session_type)]} {
        set sessionType $userArgsArray(session_type)
    }

    if {(![info exists userArgsArray(handle)] || $userArgsArray(handle) == "")} {
          ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        return $returnKeyedList
    } else {
        set ospfRouteHandles $userArgsArray(handle)
        foreach ospfHandle $ospfRouteHandles {

            set ospfrouterHandles [::sth::sthCore::invoke stc::get $ospfHandle -selectedrouterrelation-Targets]

            foreach ospfrouterHandle $ospfrouterHandles {
                if { $sessionType == "ospfv2" } {
                    set OspfRouterConfigString [::sth::sthCore::invoke stc::get $ospfrouterHandle -children-Ospfv2RouterConfig]

                    set OspfRouterConfigList [split $OspfRouterConfigString " "]
                    foreach OspfRouterConfigHandle $OspfRouterConfigList {
                        set deleteList ""
                        set AsbrSummaryLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-AsbrSummaryLsa]
                        if {$AsbrSummaryLsaList != ""} {
                            append deleteList " " $AsbrSummaryLsaList
                        }
                        set ExtendedLinkLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-ExtendedLinkLsa]
                        if {$ExtendedLinkLsaList != ""} {
                            append deleteList " " $ExtendedLinkLsaList
                        }
                        set ExtendedPrefixLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-ExtendedPrefixLsa]
                        if {$ExtendedPrefixLsaList != ""} {
                            append deleteList " " $ExtendedPrefixLsaList
                        }
                        set ExternalLsaBlockList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-ExternalLsaBlock]
                        if {$ExternalLsaBlockList != ""} {
                            append deleteList " " $ExternalLsaBlockList
                        }
                        set NetworkLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-NetworkLsa]
                        if {$NetworkLsaList != ""} {
                            append deleteList " " $NetworkLsaList
                        }
                        set RouterInfoLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-RouterInfoLsa]
                        if {$RouterInfoLsaList != ""} {
                            append deleteList " " $RouterInfoLsaList
                        }
                        set RouterLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-RouterLsa]
                        if {$RouterLsaList != ""} {
                            append deleteList " " $RouterLsaList
                        }
                        set SummaryLsaBlockList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-SummaryLsaBlock]
                        if {$SummaryLsaBlockList != ""} {
                            append deleteList " " $SummaryLsaBlockList
                        }
                        set TeLsaList [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-TeLsa]
                        if {$TeLsaList != ""} {
                            append deleteList " " $TeLsaList
                        }
                        if { $deleteList != "" } {
                            ::sth::sthCore::invoke stc::perform delete -ConfigList "$deleteList"
                        }
                    }
                } else {
                    set OspfRouterConfigString [::sth::sthCore::invoke stc::get $ospfrouterHandle -children-Ospfv3RouterConfig]

                    set OspfRouterConfigList [split $OspfRouterConfigString " "]
                    foreach OspfRouterConfigHandle $OspfRouterConfigList {
                        set deleteList ""
                        set Ospfv3AsExternalLsaBlock [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3AsExternalLsaBlock]
                        if {$Ospfv3AsExternalLsaBlock != ""} {
                            append deleteList " " $Ospfv3AsExternalLsaBlock
                        }
                        set Ospfv3InterAreaPrefixLsaBlk [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3InterAreaPrefixLsaBlk]
                        if {$Ospfv3InterAreaPrefixLsaBlk != ""} {
                            append deleteList " " $Ospfv3InterAreaPrefixLsaBlk
                        }
                        set Ospfv3InterAreaRouterLsaBlock [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3InterAreaRouterLsaBlock]
                        if {$Ospfv3InterAreaRouterLsaBlock != ""} {
                            append deleteList " " $Ospfv3InterAreaRouterLsaBlock
                        }
                        set Ospfv3IntraAreaPrefixLsaBlk [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3IntraAreaPrefixLsaBlk]
                        if {$Ospfv3IntraAreaPrefixLsaBlk != ""} {
                            append deleteList " " $Ospfv3IntraAreaPrefixLsaBlk
                        }
                        set Ospfv3LinkLsaBlk [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3LinkLsaBlk]
                        if {$Ospfv3LinkLsaBlk != ""} {
                            append deleteList " " $Ospfv3LinkLsaBlk
                        }
                        set Ospfv3NetworkLsa [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3NetworkLsa]
                        if {$Ospfv3NetworkLsa != ""} {
                            append deleteList " " $Ospfv3NetworkLsa
                        }
                        set Ospfv3NssaLsaBlock [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3NssaLsaBlock]
                        if {$Ospfv3NssaLsaBlock != ""} {
                            append deleteList " " $Ospfv3NssaLsaBlock
                        }
                        set Ospfv3RouterLsa [::sth::sthCore::invoke stc::get $OspfRouterConfigHandle -children-Ospfv3RouterLsa]
                        if {$Ospfv3RouterLsa != ""} {
                            append deleteList " " $Ospfv3RouterLsa
                        }
                        if { $deleteList != "" } {
                            ::sth::sthCore::invoke stc::perform delete -ConfigList "$deleteList"
                        }
                    }
                }
            }
        }
    }
    keylset returnKeyedList status  $SUCCESS
    return $returnKeyedList

}
###############################################################
#Config helper functions for ospfv2
###############################################################
proc ::sth::ospf::configTreeTopo {TreeTopoHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator configTreeTopo $mode $TreeTopoHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $TreeTopoHddl $optionValueList
    }
}

proc ::sth::ospf::configFullMeshTopo {FullMeshTopoHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator configFullMeshTopo $mode $FullMeshTopoHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $FullMeshTopoHddl $optionValueList
    }
}

proc ::sth::ospf::configGridTopo {GridTopoHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator configGridTopo $mode $GridTopoHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $GridTopoHddl $optionValueList
    }
}

proc ::sth::ospf::configRingTopo {RingTopoHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator configRingTopo $mode $RingTopoHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RingTopoHddl $optionValueList
    }
}

proc ::sth::ospf::configHubTopo {HubTopoHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator configHubTopo $mode $HubTopoHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $HubTopoHddl $optionValueList
    }
}

proc ::sth::ospf::ConfigOspfv2LsaGenParams {Ospfv2LsaGenParamsHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator ConfigOspfv2LsaGenParams $mode $Ospfv2LsaGenParamsHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv2LsaGenParamsHddl $optionValueList
    }
}

proc ::sth::ospf::ConfigOspfv2TeParams {Ospfv2TeParamsHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator ConfigOspfv2TeParams $mode $Ospfv2TeParamsHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv2TeParamsHddl $optionValueList
    }
}

proc ::sth::ospf::ConfigOspfv2SegmentRouteParams {Ospfv2SegmentRouteParamsHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator ConfigOspfv2SegmentRouteParams $mode $Ospfv2SegmentRouteParamsHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv2SegmentRouteParamsHddl $optionValueList
    }
}

proc ::sth::ospf::procStub {Ospfv2StubHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procStub $mode $Ospfv2StubHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv2StubHddl $optionValueList
    }
}

proc ::sth::ospf::procRouteAttrStub {RouteAttrStubHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procRouteAttrStub $mode $RouteAttrStubHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RouteAttrStubHddl $optionValueList
    }
}

proc ::sth::ospf::procSum {Ospfv2SumHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procSum $mode $Ospfv2SumHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv2SumHddl $optionValueList
    }
}

proc ::sth::ospf::procRouteAttrSum {RouteAttrSumHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procRouteAttrSum $mode $RouteAttrSumHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RouteAttrSumHddl $optionValueList
    }
}

proc ::sth::ospf::procExt {Ospfv2ExtHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procExt $mode $Ospfv2ExtHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv2ExtHddl $optionValueList
    }
}

proc ::sth::ospf::procRouteAttrExt {RouteAttrExtHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procRouteAttrExt $mode $RouteAttrExtHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RouteAttrExtHddl $optionValueList
    }
}

###############################################################
#Config helper functions for ospfv3
###############################################################
proc ::sth::ospf::ConfigOspfv3LsaGenParams {Ospfv3LsaGenParamsHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator ConfigOspfv3LsaGenParams $mode $Ospfv3LsaGenParamsHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3LsaGenParamsHddl $optionValueList
    }
}

proc ::sth::ospf::procOspfv3Intra {Ospfv3IntraHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procOspfv3Intra $mode $Ospfv3IntraHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3IntraHddl $optionValueList
    }
}

proc ::sth::ospf::procOspfv3RouteAttrIntra {Ospfv3RouteAttrIntraHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procOspfv3RouteAttrIntra $mode $Ospfv3RouteAttrIntraHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3RouteAttrIntraHddl $optionValueList
    }
}

proc ::sth::ospf::procOspfv3Inter {Ospfv3InterHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procOspfv3Inter $mode $Ospfv3InterHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3InterHddl $optionValueList
    }
}

proc ::sth::ospf::procOspfv3RouteAttrInter {Ospfv3RouteAttrInterHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procOspfv3RouteAttrInter $mode $Ospfv3RouteAttrInterHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3RouteAttrInterHddl $optionValueList
    }
}

proc ::sth::ospf::procOspfv3Ext {Ospfv3ExtHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procOspfv3Ext $mode $Ospfv3ExtHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3ExtHddl $optionValueList
    }
}

proc ::sth::ospf::procOspfv3RouteAttrExt {Ospfv3RouteAttrExtHddl mode } {
    set optionValueList [getStcOptionValueList emulation_ospf_lsa_generator procOspfv3RouteAttrExt $mode $Ospfv3RouteAttrExtHddl]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Ospfv3RouteAttrExtHddl $optionValueList
    }
}

#############################################
#Helper function
#############################################
proc ::sth::ospf::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column
    foreach item $::sth::ospf::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::ospf:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::ospf:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::ospf:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::ospf:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::ospf:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::ospf:: $cmdType $opt $::sth::ospf::userArgsArray($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::ospf::userArgsArray($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::ospf::userArgsArray($opt)]
                }
            }
        }
    }
    return $optionValueList
}
