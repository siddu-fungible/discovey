# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# TODO:
# write cleanup proc to be called in the end
# 12_08
# Put a check for the length of attribute list.
# if the length is 0, the dont call the config command.
# Same for config gen attributes (if length of attributes is 0, the dont call it.


namespace eval ::sth::Traffic:: {
}
namespace eval ::sth::Session:: {
}
namespace eval ::sth::sthCore:: {
}

proc ::sth::Traffic::processClearDataStructures {} {
    upvar mns mns;
    
    set ::$mns\::handleTxStream 0;
    set ::$mns\::handleRxStream 0;
    set ::$mns\::handleCurrentHeader 0;
    set ::$mns\::handleCurrentl2Header 0;
    set ::$mns\::handleCurrentl3Header 0;
    set ::$mns\::handleCurrentl4Header 0;
    
    set ::$mns\::modeOfOperation "";
    set ::$mns\::l2EncapType "_none_";
    set ::$mns\::l3HeaderType "_none_";
    set ::$mns\::l3OuterHeaderType "_none_";
    set ::$mns\::l4HeaderType "_none_";
    
    set ::$mns\::listGeneralAttributes {};
    set ::$mns\::listProcessedList {};
    set ::$mns\::listSbLoadProfileList {};
    set ::$mns\::listl3QosBits {};
    set ::$mns\::listl3OuterQosBits {};
    set ::$mns\::listl4QosBits {};
    set ::$mns\::listMplsHeaderAttributes_Mpls {};
    
    set ::$mns\::listThresholdList {};
    set ::$mns\::listl2encap_EthernetII {};
    set ::$mns\::listl2encap_EthernetII_bidirectional {};
    set ::$mns\::listl2encap_Vlan {};
    set ::$mns\::listl2encap_ATM {};
    set ::$mns\::listl2encap_FC {};
    set ::$mns\::listl2encap_FcSofEof {};
    set ::$mns\::listl2encap_OuterVlan {};
    set ::$mns\::listl2encap_OtherVlan {};
    set ::$mns\::listl2encap_Ethernet8022 {};
    set ::$mns\::listl2encap_Ethernet8022_bidirectional {};
    set ::$mns\::listl2encap_EthernetSnap {};
    set ::$mns\::listl2encap_EthernetSnap_bidirectional {};
    set ::$mns\::listl2encap_Ethernet8023Raw {};
    set ::$mns\::listl2encap_Ethernet8023Raw_bidirectional {};
    
    set ::$mns\::listl3Header_Ipv4 {};
    set ::$mns\::listl3Header_Ipv6 {};
    set ::$mns\::listl3Header_Arp  {};
    set ::$mns\::listl3Header_OuterIpv4 {};
    set ::$mns\::listl3Header_OuterIpv6 {};
    set ::$mns\::listl3Header_InnerIpv4 {};
    set ::$mns\::listl3Header_Gre {};
    set ::$mns\::listl4Headertcp {};
    set ::$mns\::listl4Headerudp {};
    set ::$mns\::listl4Headerisis {};
    set ::$mns\::listl4Headerigmp {};
    set ::$mns\::listl4Headeripv4 {};
    set ::$mns\::listl4Headeripv6 {};
    set ::$mns\::listl2VlanRangeModifier {};
    set ::$mns\::listl2VlanPriorityRangeModifier {};
    set ::$mns\::listl2VpiRangeModifier {};
    set ::$mns\::listl2VciRangeModifier {};
    set ::$mns\::listl2OuterVlanRangeModifier {};
    set ::$mns\::listl2OtherVlanRangeModifier {};
    set ::$mns\::listl2DstRangeModifier {};
    set ::$mns\::listl2SrcRangeModifier {};
    set ::$mns\::listl2Dst2RangeModifier {};
    set ::$mns\::listl2Src2RangeModifier {};
    set ::$mns\::listMacGwRangeModifier {};
    set ::$mns\::listArpMacSrcRangeModifier {};
    set ::$mns\::listArpMacDstRangeModifier {};
    set ::$mns\::listl3DstRangeModifier {};
    set ::$mns\::listl3SrcRangeModifier {};
    set ::$mns\::listl3OuterDstRangeModifier {};
    set ::$mns\::listl3OuterSrcRangeModifier {};
    set ::$mns\::listl3precedenceRangeModifier {};
    set ::$mns\::listl3OuterPrecedenceRangeModifier {};
    set ::$mns\::listl3tosRangeModifier {};
    set ::$mns\::listl3OuterTosRangeModifier {};
    set ::$mns\::listIgmpGroupAddrRangeModifier {};

    set ::$mns\::listl4DstRangeModifier {};
    set ::$mns\::listl4SrcRangeModifier {};
    set ::$mns\::listTcpPortSrcRangeModifier {};
    set ::$mns\::listTcpPortDstRangeModifier {};
    set ::$mns\::listUdpPortSrcRangeModifier {};
    set ::$mns\::listUdpPortDstRangeModifier {};
    set ::$mns\::listl4precedenceRangeModifier {};
    set ::$mns\::listl4tosRangeModifier {};

    set ::$mns\::listVxlanHeader {};
    set ::$mns\::listInnerl2encap_EthernetII {};
    set ::$mns\::listInnerl2encap_OuterVlan {};
    set ::$mns\::listInnerl2encap_Vlan {};
    set ::$mns\::listInnerl3Header_Ipv4 {};
    set ::$mns\::listInnerl2SrcRangeModifier {};
    set ::$mns\::listInnerl2DstRangeModifier {};
    set ::$mns\::listInnerl3SrcRangeModifier {};
    set ::$mns\::listInnerl3DstRangeModifier {};
    set ::$mns\::listInnerl2OuterVlanRangeModifier {};
    set ::$mns\::listInnerl2VlanPriorityRangeModifier {};
    set ::$mns\::listInnerl2VlanRangeModifier {};
    set ::$mns\::listInnerGwRangeModifier {};
    
    if {[info exists ::sth::Traffic::listModifierMap]} {
        array unset ::sth::Traffic::listModifierMap
    }
    
    array set ::sth::Traffic::_funcArray {}
}


#proc ::sth::Traffic::_procTemplate {mode stcobj switches options} {
#    upvar mns mns
#    upvar userArgsArray userArgsArray
#    upvar trafficKeyedList trafficKeyedList

#please uncomment following lines to debug
#    puts $mode
#    puts $stcobj
#    puts $switches
#    puts $options
#    set option1 [lindex option 0]
#    set option2 [lindex option 1]
#    set option3 [lindex option 3]

#    set _procName "_procTemplate"
#    ::sth::sthCore::log info "$_procName $mode $stcobj {$switches} $options"
#}

proc ::sth::Traffic::_procModifier {mode stcobj switches mask} {
    upvar mns mns
    upvar userArgsArray userArgsArray
    upvar trafficKeyedList trafficKeyedList
    
    set _procName "_procModifier"
    ::sth::sthCore::log info "$_procName $mode $stcobj {$switches} $mask"

    set stcitems [split $stcobj ":."]
    set obj [lindex $stcitems 0]
    set objs "$obj:$obj"
    set parentHnd [::sth::sthCore::invoke ::stc::get [set ::sth::Traffic::handleCurrentStream] -children-$objs]
    set offsetid [lindex $stcitems 1]
    
    if {[regexp "^$objs\\d+" $parentHnd]} {
        ::sth::Traffic::processCreateL2RangeModifier default $parentHnd $switches $offsetid $mask
    }
}

###!!!Please DON'T modify this function!!!
#    a. common configuration function for mode (create | modify) when the stcobj handle may exist, 
#    b. designed for the new options of the stc objects (except streamblock object) whose other options were implemented in OLD traffic_config() branch.
proc ::sth::Traffic::_procCommonConfigEx {mode stcobj switches options} {
    upvar mns mns
    upvar userArgsArray userArgsArray
    upvar trafficKeyedList trafficKeyedList

    set _procName "_procCommonConfigEx"
    ::sth::sthCore::log info "$_procName $mode $stcobj {$switches} $options"
    
    set argsValueList ""
    foreach sName $switches {
        set stcAttr $::sth::Traffic::traffic_config_stcattr($sName)
        lappend argsValueList -$stcAttr $userArgsArray($sName)
    }
    
    set myHnd [set ::sth::Traffic::handleCurrentStream]
    # First check if stcobj exist 
    if {[catch {::sth::sthCore::invoke ::stc::get $myHnd -children-$stcobj} retHandle] || $retHandle == ""} {
        # create stcobj header
        ::sth::sthCore::log debug "$_procName: Calling stc::create $stcobj $myHnd $argsValueList"
        set cmdName "::sth::sthCore::invoke ::stc::create $stcobj -under $myHnd $argsValueList";
        if {[catch {eval $cmdName} retHandle]} {
            return ""
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
    } else {        # If it does, then config that handle
        ::sth::sthCore::log info "$_procName: stc::config $retHandle $argsValueList";
        sth::sthCore::invoke stc::config $retHandle $argsValueList 
    }
    return $retHandle
}

###!!!Please DON'T modify this function!!!
#     a. common configuration function for mode (create | modify)
#     b. designed for the new options of the stc objects which are NOT implemented in OLD traffic_config() branch 
proc ::sth::Traffic::_procCommonConfig {mode stcobj switches options} {
    upvar mns mns
    upvar userArgsArray userArgsArray
    upvar trafficKeyedList trafficKeyedList

    set _procName "_procCommonConfig"
    ::sth::sthCore::log info "$_procName $mode $stcobj {$switches} $options"
    
    set argsValueList ""
    foreach sName $switches {
        set stcAttr $::sth::Traffic::traffic_config_stcattr($sName)
        lappend argsValueList -$stcAttr $userArgsArray($sName)
    }
    
    set myHnd [set ::sth::Traffic::handleCurrentStream]
    if {[regexp -nocase "^streamblock$" $stcobj]} {
        ::sth::sthCore::log info "$_procName: stc::config $myHnd $argsValueList";
        sth::sthCore::invoke stc::config $myHnd $argsValueList
        set retHandle $myHnd
    } else {
        if {$mode == "create"} {
            # create and config stcobj header
            ::sth::sthCore::log debug "$_procName: Calling stc::create $stcobj $myHnd $argsValueList"
            set retHandle [::sth::sthCore::invoke ::stc::create $stcobj -under $myHnd $argsValueList]
        } elseif {$mode == "modify"} {
            # First check if stcobj exist 
            if {[catch {::sth::sthCore::invoke ::stc::get $myHnd -children-$stcobj} retHandle] || $retHandle == ""} {
                # create stcobj header
                ::sth::sthCore::log debug "$_procName: Calling stc::create $stcobj $myHnd $argsValueList"
                set cmdName "::sth::sthCore::invoke ::stc::create $stcobj -under $myHnd $argsValueList";
                if {[catch {eval $cmdName} retHandle]} {
                    return ""
                } else {
                    ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                }
            } else {        # If it does, then config that handle
                ::sth::sthCore::log info "$_procName: stc::config $retHandle $argsValueList";
                sth::sthCore::invoke stc::config $retHandle $argsValueList 
            }
        }
    }
    
    return $retHandle
}

###!!!Please DON'T modify this function!!!
proc ::sth::Traffic::_traffic_config {mode {filter ""}} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar mns mns
    upvar userArgsArray userArgsArray
    upvar trafficKeyedList trafficKeyedList
    upvar prioritisedAttributeList prioritisedAttributeList

    set funcArrayList [array names ::sth::Traffic::_funcArray]
    foreach func [lsort -increasing $funcArrayList] {
        set items [split $func -]
        set stcobj [lindex $items 1]
        set funcName [lindex $items 2]
        if {[regexp {^(.*)_} $funcName match mylayer]} {
            set funcName [regsub $mylayer $funcName ""]
        }
        if {$filter == "" || $filter == $mylayer || [regexp -nocase ^$filter$ $stcobj$funcName]} {
            set funcOpts [split [lindex $items 3] -]
            set switches $::sth::Traffic::_funcArray($func)

            if {$funcName != "" && $funcName != "_none_"} {
                if {[catch {::sth::Traffic::$funcName $mode $stcobj $switches $funcOpts} errMsg]} {
                    ::sth::sthCore::log debug "$funcName $mode $stcobj $switches $funcOpts FAILED. $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                } else {
                    ::sth::sthCore::log info "$funcName for $mode $stcobj $switches $funcOpts \t PASSED."
                }
            }
            unset ::sth::Traffic::_funcArray($func)
        }
    }
    
    return ::sth::sthCore::SUCCESS
}

###!!!Please DON'T modify this function!!!
proc ::sth::Traffic::_traffic_config_preprocess {mode sName} {
    if {[info exists ::sth::Traffic::traffic_config_$sName\_mode(_$mode)]} {
        set value [set ::sth::Traffic::traffic_config_$sName\_mode(_$mode)]
        set priority $::sth::Traffic::traffic_config_priority($sName)
        if {$value != "" && $value != "_none_"} {
            set stcobj $::sth::Traffic::traffic_config_stcobj($sName)
            if {[info exists ::sth::Traffic::_funcArray($priority\-$stcobj\-$value)]} {
                lappend ::sth::Traffic::_funcArray($priority\-$stcobj\-$value) $sName
            } else {
                set ::sth::Traffic::_funcArray($priority\-$stcobj\-$value) $sName
            }
        }
    }
}

proc ::sth::Traffic::processTrafficConfigModecreate {} {
    
    set _procName "processTrafficConfigModecreate";
    
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    
    set errMsg "";
    
    if {[info exists userArgsArray(l2_encap)]} {
        set ::$mns\::l2EncapType $userArgsArray(l2_encap);
        set ::$mns\::arrayHeaderTypesInCreate(l2_encap) $userArgsArray(l2_encap);
    } 
    if {[info exists userArgsArray(inner_l2_encap)]} {
        set ::$mns\::innerl2EncapType $userArgsArray(inner_l2_encap);
        set ::$mns\::arrayHeaderTypesInCreate(inner_l2_encap) $userArgsArray(inner_l2_encap);
    }
    
    if {[info exists userArgsArray(l3_protocol)]} {
        set ::$mns\::l3HeaderType $userArgsArray(l3_protocol);
        set ::$mns\::arrayHeaderTypesInCreate(l3_protocol) $userArgsArray(l3_protocol);
    }
    
    if {[info exists userArgsArray(l3_outer_protocol)]} {
        set ::$mns\::l3OuterHeaderType outer_$userArgsArray(l3_outer_protocol);
        set ::$mns\::arrayHeaderTypesInCreate(l3_outer_protocol) $userArgsArray(l3_outer_protocol);
    }
    
    if {[info exists userArgsArray(l4_protocol)]} {
        set ::$mns\::l4HeaderType $userArgsArray(l4_protocol);
        if {[regexp "ip" $userArgsArray(l4_protocol)]} {
            set ::$mns\::l4HeaderType l4_$userArgsArray(l4_protocol);
        }
        set ::$mns\::arrayHeaderTypesInCreate(l4_protocol) $userArgsArray(l4_protocol);
    }
    
    if {[info exists userArgsArray(vxlan)]} {
        set ::$mns\::l3InnerHeaderType inner_$userArgsArray(l3_protocol);
    }
    set funcTableName1 "::$mns\::traffic_config_procfunc";
    set funcTableName2 "";
    set mpls_flag 1;
    set mpls_layer_count 0;
    #####################################################################
    # Process input attribues using the functions
    # defined in "mode" on trafficConfigTable.tcl
    ####################################################################
    foreach element $prioritisedAttributeList {
        foreach {prio sName} $element {         
            _traffic_config_preprocess create $sName
            
            if {[regexp "^mpls" $sName] && $mpls_flag} {
                if {[regexp "^\\s*\{" $userArgsArray($sName)]} {
                        set mpls_layer_count [llength $userArgsArray($sName)]
                } else {
                    set mpls_layer_count 1
                }
                for {set i 1} {$i<=$mpls_layer_count} {incr i} {
                    set ::$mns\::listMplsLabelTableModifier$i {};
                    set ::$mns\::listMplsLabelRangeModifier$i {};
                    set ::$mns\::listMplsLabelModifier$i {};
                }
                set mpls_flag 0
            }
            set funcTableName2 "::$mns\::traffic_config_$sName\_mode";
            
            if {[info exists $funcTableName2\(create)]} {
                set funcName [set $funcTableName2\(create)];
            } else {
                set funcName [set $funcTableName1\($sName)];
            }
            
            if {$funcName != "_none_"} {
                if {[catch {::sth::Traffic::$funcName $sName} errMsg]} {
                    ::sth::sthCore::log debug "$funcName FAILED. $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                } else {
                    ::sth::sthCore::log info "$funcName for $sName \t PASSED."
                }
            }
        }
    }
    
    if {[info exists userArgsArray(bidirectional)]} {
        set iterations 2
    } else {
        set iterations 1
    }
    
    set ::$mns\::handleCurrentStream $::sth::Traffic::handleTxStream;
    for {set x 0} {$x < $iterations} {incr x} {
        
        ##################################################
        # process general attributes
        ##################################################
        if {[catch {::$mns\::processConfigGeneralAttributes} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
        ##################################################
        # process IMIX attributes
        ##################################################
        if {[info exists userArgsArray(length_mode)] && $userArgsArray(length_mode) == "imix"} {
            if {[catch {::$mns\::processImixAttributes} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
       
        ##################################################
        # Create L2 encapsulation
        ##################################################
        if {[info exists userArgsArray(l2_encap)]} {
            if {[catch {::$mns\::processCreateL2Encap $_procName} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        
        ##################################################
        # Create PPPox/DHCP encapsulation
        ##################################################
        set origHandle $::sth::Traffic::handleTxStream;
        if {[catch {::sth::Traffic::processCreatePppoxDhcpEncap $x} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
        
        set ::sth::Traffic::handleTxStream $origHandle;
        
        ##################################################
        # Create GRE protocol
        ##################################################
        if {[info exists userArgsArray(tunnel_handle)]} {
         if {[catch {::$mns\::processCreateGreProtocol} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
          }
        }
        
        ##################################################
        # Process bound traffic 
        ##################################################
        
        set streamBlkHandle $::sth::Traffic::handleCurrentStream
        set emulation_src_handle 0
        set emulation_dst_handle 0
        if { [info exists userArgsArray(emulation_src_handle)] } {
            set emulation_src_handle $userArgsArray(emulation_src_handle)
        } 
        if { [info exists userArgsArray(emulation_dst_handle)] } {
            set emulation_dst_handle $userArgsArray(emulation_dst_handle)
        }
        
        set useNativeBinding false
        if { $emulation_src_handle != 0 || $emulation_dst_handle != 0 } {
            # check for bidirectional traffic
            if {[info exists userArgsArray(bidirectional)]} {
                if {[info exists userArgsArray(emulation_src_handle)] && [info exists userArgsArray(emulation_dst_handle)]} {
                # both exist so they can be swapped.
                } else {
                ##puts "both src and dst should exist for bidirectional traffic";
                set errMsg "For bidirectional traffic both emulation src and dst information should be provided"
                return -code 1 -errorcode -1 $errMsg;
                }
            }
            if {[catch {::sth::Traffic::processSrcAndDstEmulationHandles \
                 $streamBlkHandle $emulation_src_handle $emulation_dst_handle $useNativeBinding } errMsg]} {
                ::sth::sthCore::log error $errMsg
                return -code error $errMsg
            
            }
        }
        # check Src and Dst Handle
        if {![info exists userArgsArray(l3_protocol)]} {
            set ipv4Count 0
            set ipv6Count 0
            set srcTargets [::sth::sthCore::invoke ::stc::get $streamBlkHandle -srcbinding-Targets]
            set dstTargets [::sth::sthCore::invoke ::stc::get $streamBlkHandle -dstbinding-Targets]
            set targetHandles [concat $srcTargets $dstTargets]
            foreach endpoint $targetHandles {
                if {[regexp -nocase "v4" $endpoint]} {
                    incr ipv4Count
                } elseif {[regexp -nocase "v6" $endpoint]} {
                    incr ipv6Count
                }
            }
            if {$ipv4Count > 0 && $ipv6Count > 0} {
                return -code error "Type of l3 dst doesn't match with src. Please specify -l3_protocol!"
            }
        }
        #after the bound streamblock need to do the StreamBlockUpdate, if the l3 is used in the binding, only when the
        #StreamBlockUpdate is done, we can get the ipv4 header or ipv6 header
        ::sth::Traffic::processStreamHeader $streamBlkHandle
        #incase the ip header has already been created in the bound stream
        set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        array set arrayHeaders $headerSet;
        
        ::sth::Traffic::_traffic_config create L2
            
        ##################################################
        # Create L3 outer encapsulation
        ##################################################
        if {[info exists userArgsArray(l3_outer_protocol)]} {
            set ::$mns\::l3HeaderType outer_$userArgsArray(l3_outer_protocol);
            if {[info exists arrayHeaders(l3_header_outer)]} {
                set ::$mns\::handleCurrentHeader $arrayHeaders(l3_header_outer);
            } else {
                set ::$mns\::handleCurrentHeader 0;
            }
            if {[catch {::$mns\::processCreateL3Protocol} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        
        
        
        ##################################################
        # Create L3 encapsulation
        ##################################################
        if {[info exists userArgsArray(l3_protocol)]} {
            set ::$mns\::l3HeaderType $userArgsArray(l3_protocol);
            if {[info exists arrayHeaders(l3_header)]} {
                set ::$mns\::handleCurrentHeader $arrayHeaders(l3_header);
            } else {
                set ::$mns\::handleCurrentHeader 0;
            }
            if {[catch {::$mns\::processCreateL3Protocol} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        
        ##################################################
        # Create IPv6 Next header
        ##################################################
        if {([info exists userArgsArray(ipv6_extension_header)] || [info exists userArgsArray(ipv6_frag_offset)] || [info exists userArgsArray(ipv6_frag_more_flag)] || [info exists userArgsArray(ipv6_frag_id)]) && [info exists userArgsArray(l3_protocol)] && $userArgsArray(l3_protocol) == "ipv6"} {
            if {[catch {::$mns\::processCreateModifyIpv6NextHeader} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }

        ##################################################
        # Create IPv4 header Option, focus on routerAlert
        ##################################################
        if {([info exists userArgsArray(ipv4_header_options)] || [info exists userArgsArray(ipv4_router_alert)]) && [info exists userArgsArray(l3_protocol)] && $userArgsArray(l3_protocol) == "ipv4"} {
            if {[catch {::$mns\::processCreateModifyIpv4HeaderOptions} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        
        ::sth::Traffic::_traffic_config create L3
        
        ##################################################
        # Create L4 encapsulation
        ##################################################
        set ::$mns\::handleCurrentHeader 0
        if {[info exists userArgsArray(l4_protocol)] && $userArgsArray(l4_protocol) != "ospf"} {
            if {[catch {::$mns\::processCreateL4Protocol;} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        
        #####################################################
        #process the vxlanif, need to process the inner ip and the inner ethernet
        ######################################################
        if {[info exists userArgsArray(vxlan)]} {
            if {[catch {::$mns\::processCreateVxlan;} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        
        #######################################################
        # Create Custom encapsulation at the end of the frames
        #######################################################
        if {[info exists userArgsArray(custom_pattern)]} {
            if {[catch {::$mns\::processCreateCustomHeader custom_pattern create;} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
    
        ##################################################
        # Process vpls traffic 
        ##################################################
        if {[info exists userArgsArray(vpls_source_handle)] && [info exists userArgsArray(vpls_destination_handle)]} {
            if { $iterations == 2 && $x== 1 } {
                set vpls_source_handle $userArgsArray(vpls_destination_handle)
                set vpls_destination_handle $userArgsArray(vpls_source_handle)
            } else {
                set vpls_source_handle $userArgsArray(vpls_source_handle)
                set vpls_destination_handle $userArgsArray(vpls_destination_handle)
            }
            if {[catch {::$mns\::processVplsTraffic $vpls_source_handle $vpls_destination_handle} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
        ::sth::Traffic::_traffic_config create L4
        
        ##################################################
        # Process bidirectional traffic
        ##################################################
        
        if {$iterations == 2} {
            # for bidirectional traffic,
            # 1. Change to 2nd streamBlock handle.
            # 2. Get the 2nd set of l2 attributes into the main list.
            # 3. Swap the l3 src and dst attributes
            set ::$mns\::handleCurrentStream $::sth::Traffic::handleRxStream;
            set ::$mns\::listl2encap_EthernetII [set ::$mns\::listl2encap_EthernetII_bidirectional];
            
            # fix the bidirectional case for Ethernet 802.2
            if {[regexp "8022" $userArgsArray(l2_encap)]} {
                set ::$mns\::listl2encap_Ethernet8022 [set ::$mns\::listl2encap_Ethernet8022_bidirectional];    
            }
            #added bidirectional case for Ethernet snap
            if {[regexp "snap" $userArgsArray(l2_encap)]} {
                set ::$mns\::listl2encap_EthernetSnap [set ::$mns\::listl2encap_EthernetSnap_bidirectional];    
            }
            #added bidirectional case for Ethernet 802.3 raw
            if {[regexp "raw" $userArgsArray(l2_encap)]} {
                set ::$mns\::listl2encap_Ethernet8023Raw [set ::$mns\::listl2encap_Ethernet8023Raw_bidirectional];    
            }
            
            if {[catch {::sth::Traffic::processSwapl3ForBidirectional} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
            
            # this is bidirectional traffic
            if {$x == 1} {
                set HndPort $userArgsArray(port_handle2);
                set HndStream [set ::$mns\::handleRxStream];
            } else {
                set HndPort $userArgsArray(port_handle);
                set HndStream [set ::$mns\::handleTxStream];
            }
            set nameToUse "stream_id.$HndPort";
            keylset trafficKeyedList $nameToUse $HndStream;
        } else {
            set HndStream [set ::$mns\::handleTxStream];
            keylset trafficKeyedList stream_id $HndStream;
            #return $::sth::sthCore::SUCCESS;
            #break;
        }
    }
   
    keylset trafficKeyedList status $::sth::sthCore::SUCCESS;
    #return $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processTrafficConfigModemodify {} {
    
    # TODO: Check the validity of the stream handle entered by the user.
    
    set _procName "processTrafficConfigModeModify";
    
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    
    set errMsg "";
    
    if {[info exists userArgsArray(stream_id)]} {
        set ::$mns\::handleCurrentStream $userArgsArray(stream_id);
    } else {
        set errMsg "Missing mandatory arguments.. Expected:  mode stream_id";
        ::sth::sthCore::log debug "$_procName: $errMsg "
        return -code 1 -errorcode -1 $errMsg;
    }
    
    if {[info exists userArgsArray(enable_stream_only_gen)]} {
       ::sth::sthCore::invoke ::stc::config $userArgsArray(stream_id) -EnableStreamOnlyGeneration $userArgsArray(enable_stream_only_gen)
    }
    
    if {[regexp -nocase {^many_to_many$} $userArgsArray(endpoint_map)]} {
        set userArgsArray(endpoint_map) "one_to_many"
    }
    ::sth::sthCore::invoke ::stc::config $userArgsArray(stream_id) -EndpointMapping $userArgsArray(endpoint_map)
    
    array unset ::$mns\::arrayHeaderTypesInCreate
    array set ::$mns\::arrayHeaderTypesInCreate {}
   
    if {[catch {array set ::$mns\::arrayHeaderTypesInCreate [set ::$mns\::arrayStreamHeaderTypesInCreateMAP($userArgsArray(stream_id))]}]} {
        if {$::sth::Session::xmlFlag == 1 || $::sth::Session::fillTraffic eq "set"} {
            #when load_xml is used ip_dst_addr ip_src_addr mac_dst mac_src parameters can be modified 
            set streamHandle $userArgsArray(stream_id)
            #for l2_encap and modify mac_dst,mac_src
            if {[info exists userArgsArray(l2_encap)]} {
                if {[regexp -nocase 8022 $userArgsArray(l2_encap)]} {
                    set l2HeaderType "ethernet:Ethernet8022"
                } elseif {[regexp -nocase snap $userArgsArray(l2_encap)]} {
                    set l2HeaderType "ethernet:EthernetSnap"
                } elseif {[regexp -nocase raw $userArgsArray(l2_encap)]} {
                    set l2HeaderType "ethernet:Ethernet8023Raw"
                } else {
                    set l2HeaderType "ethernet:EthernetII"
                }
                set ethHandle [::sth::sthCore::invoke ::stc::get $streamHandle -children-$l2HeaderType]
                if {$ethHandle != ""} {
                    if {[info exists userArgsArray(mac_dst)]} {
                        ::sth::sthCore::invoke ::stc::config $ethHandle -dstMac $userArgsArray(mac_dst)
                    }
                    if {[info exists userArgsArray(mac_src)]} {
                        ::sth::sthCore::invoke ::stc::config $ethHandle -srcMac $userArgsArray(mac_src)
                    }
                }
            }
            
            #supported -l3_protocol ipv4: one ipv4 header
            if {[info exists userArgsArray(l3_protocol)]} {
                set ipv4Handle [lindex [::sth::sthCore::invoke ::stc::get $streamHandle -children-ipv4:IPv4] 0]
                if {$ipv4Handle != ""} {
                    if {[info exists userArgsArray(ip_dst_addr)]} {
                        ::sth::sthCore::invoke ::stc::config $ipv4Handle -destAddr $userArgsArray(ip_dst_addr)
                    }
                    if {[info exists userArgsArray(ip_src_addr)]} {
                        ::sth::sthCore::invoke ::stc::config $ipv4Handle -sourceAddr $userArgsArray(ip_src_addr)
                    }
                }
            }
            # Not returning here
            # keylset trafficKeyedList status $::sth::sthCore::SUCCESS
            # return $trafficKeyedList
        }
    } 
    ##################################################
    # Modify L2 encapsulation
    ##################################################
    if {[info exists userArgsArray(l2_encap)]} {
        set ::$mns\::l2EncapType $userArgsArray(l2_encap)
        set headerInModify $userArgsArray(l2_encap)
        if {[info exists ::sth::Traffic::arrayHeaderTypesInCreate(l2_encap)]} {
            set headerInCreate [set ::$mns\::arrayHeaderTypesInCreate(l2_encap)]
            if {$headerInCreate != $headerInModify} {
                    #################################################
                    # Modify "ethernet_ii" to "ethernet_ii_vlan"
                    # Modify "etherent_802" to "ethernet_8022_vlan"
                    # Modify "etherent_8023_snap" to "ethernet_8023_snap_vlan"
                    # Modify "etherent_8023_raw" to "ethernet_8023_raw_vlan"
                    # Modify "ethernet_ii_unicast_mpls" to "ethernet_ii_vlan_mpls"
                    #################################################
                    if { $headerInCreate == "ethernet_ii" && $headerInModify == "ethernet_ii_vlan"
                        || $headerInCreate == "ethernet_8022" && $headerInModify == "ethernet_8022_vlan"
                        || $headerInCreate == "ethernet_8023_snap" && $headerInModify == "ethernet_8023_snap_vlan"
                        || $headerInCreate == "ethernet_8023_raw" && $headerInModify == "ethernet_8023_raw_vlan"
                        || $headerInCreate == "ethernet_ii_unicast_mpls" && $headerInModify == "ethernet_ii_vlan_mpls"} {
                            
                   set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
                   ## xz, there is a bug if no l3_header defined
                   set index [string first "l3_header" $headerSet]
                   if {$index > 0} {
                        set index [expr $index - 2]
                   } else {
                        set index [expr [string length $headerSet]-1]
                   }
                   
                  
                   set streamHandle  [set ::$mns\::handleCurrentStream]
                   if {[regexp -nocase 8022 $headerInCreate]} {
                        set l2HeaderType "ethernet:Ethernet8022"
                   } elseif {[regexp -nocase snap $headerInCreate]} {
                        set l2HeaderType "ethernet:EthernetSnap"
                   } elseif {[regexp -nocase raw $headerInCreate]} {
                        set l2HeaderType "ethernet:Ethernet8023Raw"
                   } else {
                        set l2HeaderType "ethernet:EthernetII"
                   }
                   set ethHandle [::sth::sthCore::invoke ::stc::get $streamHandle -children-$l2HeaderType]
                   #set ethHandle [::stc::get $streamHandle -children-ethernet:EthernetII]
                   
                   set handleVlanList [::sth::sthCore::invoke ::stc::get [lindex $ethHandle 0] -children-vlans]
                   
                   if {[llength $handleVlanList] == 0} {
                      set handleVlanList [::sth::sthCore::invoke ::stc::create vlans -under $ethHandle]
                   }
                   
                   set vlanHandle [::sth::sthCore::invoke ::stc::create vlan -under $handleVlanList];
                    
                   set appendHead " Vlan $vlanHandle\}"

                   set headerSet [string replace $headerSet $index $index $appendHead]
                   set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $headerSet
                   set ::sth::Traffic::arrayHeaderTypesInCreate(l2_encap) $headerInModify
                   set ::$mns\::strHandlel2EncapMap($userArgsArray(stream_id)) $headerInModify
                   set ::$mns\::arrayStreamHeaderTypesInCreateMAP([set ::$mns\::handleCurrentStream]) [array get ::$mns\::arrayHeaderTypesInCreate]
                     
                } elseif { $headerInCreate == "ethernet_ii_vlan" && $headerInModify == "ethernet_ii"
                        || $headerInCreate == "ethernet_8022_vlan" && $headerInModify == "ethernet_8022"
                        || $headerInCreate == "ethernet_8023_snap_vlan" && $headerInModify == "ethernet_8023_snap"
                        || $headerInCreate == "ethernet_8023_raw_vlan" && $headerInModify == "ethernet_8023_raw"
                        || $headerInCreate == "ethernet_ii_vlan_mpls" && $headerInModify == "ethernet_ii_unicast_mpls"} {
                            
                    #################################################
                    # Modify "ethernet_ii_vlan" to "ethernet_ii"
                    # Modify "ethernet_8022_vlan" to "ethernet_8022"
                    # Modify "ethernet_8023_snap_vlan" to "ethernet_8023_snap"
                    # Modify "ethernet_8023_raw_vlan" to "ethernet_8023_raw"
                    # Modify "ethernet_ii_vlan_mpls" to "ethernet_ii_unicast_mpls"
                    #################################################
                    
                    set streamHandle  [set ::$mns\::handleCurrentStream]
                    
                    if {[regexp -nocase 8022 $headerInCreate]} {
                        set l2HeaderType "ethernet:Ethernet8022"
                    } elseif {[regexp -nocase snap $headerInCreate]} {
                        set l2HeaderType "ethernet:EthernetSnap"
                    } elseif {[regexp -nocase raw $headerInCreate]} {
                        set l2HeaderType "ethernet:Ethernet8023Raw"
                    } else {
                        set l2HeaderType "ethernet:EthernetII"
                    }
                    set ethHandle [::sth::sthCore::invoke ::stc::get $streamHandle -children-$l2HeaderType]
                    #set ethHandle [::stc::get $streamHandle -children-ethernet:EthernetII]
                    set handleVlanList [::sth::sthCore::invoke ::stc::get [lindex $ethHandle 0] -children-vlans]
                    if {[llength $handleVlanList] != 0} {
                        set vlanHandle [::sth::sthCore::invoke ::stc::get $handleVlanList -children];
                        if {[llength $vlanHandle] != 0} {
                            foreach vHdl $vlanHandle {
                                # fix 329671909, delete associated modifier
                                ProcessDirtyModifier $streamHandle $vHdl
                                ::sth::sthCore::invoke stc::delete $vHdl
                            }
                            set header [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]
                            set n [lsearch -regexp -all $header "l2_encap"]
                            if {$n >= 0} {
                                set head [lindex $header [expr {$n+1}]]
                                if {[llength $vlanHandle] == 2} {
                                    # delete dual vlan tags
                                    set loc1 [lsearch -regexp $head "OuterVlan"]
                                    set head [lreplace $head $loc1 [expr $loc1+1]]
                                    set loc2 [lsearch -regexp $head "Vlan"]
                                    set head [lreplace $head $loc2 [expr $loc2+1]]
                                } elseif {[llength $vlanHandle] == 1} {
                                    # delete vlan tag
                                    set loc [lsearch -regexp $head "Vlan"]
                                    set head [lreplace $head $loc [expr $loc+1]]
                                }
                                set header [lreplace $header [expr $n+1] [expr $n+1] $head]
                                set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $header
                            }
                        }
                    }
                    set ::sth::Traffic::arrayHeaderTypesInCreate(l2_encap) $headerInModify
                    set ::$mns\::strHandlel2EncapMap($userArgsArray(stream_id)) $headerInModify
                    set ::$mns\::arrayStreamHeaderTypesInCreateMAP([set ::$mns\::handleCurrentStream]) [array get ::$mns\::arrayHeaderTypesInCreate]

                } else {
                    set errMsg "l2_encap types dont match in mode create and mode modify";
                    ::sth::sthCore::processError trafficKeyedList "$_procName: $errMsg " {}
                    return -code 1 -errorcode -1 $errMsg;
                }
            }
        } else {
            ::sth::sthCore::log debug "$_procName l2 header to be added through mode modify ";
        }
    }
    
    ##################################################
    # Modify L3 encapsulation
    ##################################################
    
    if {[info exists userArgsArray(l3_protocol)]} {
        set ::$mns\::l3HeaderType $userArgsArray(l3_protocol);
        set headerInModify $userArgsArray(l3_protocol);
        if {[info exists ::sth::Traffic::arrayHeaderTypesInCreate(l3_protocol)]} {
            set headerInCreate [set ::$mns\::arrayHeaderTypesInCreate(l3_protocol)];
            if {$headerInCreate != $headerInModify} {
                set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
                set index1 [string last "l3_header" $headerSet]
                set index2 [string first "l4_header" $headerSet]
                if {$index2 == -1 } {
                   set index2 [string length $headerSet]    
                } else {
                   set index2 [expr $index2 - 1]
                }
                # xz, when the index is larger than 10, the below line will cause error (for example: l3_header ipv4:ipv417 l4_header)
                #set objectName [string range $headerSet [expr $index1 + 10] [expr $index2 - 2]]
                #set headerSet [string replace $headerSet [expr $index1 - 1] $index2 ""]
                set objectType [string range $headerSet [expr $index1 + 10] [expr $index1 + 12]]
                if {$objectType == "arp"} {
                    set objectName [string range $headerSet [expr $index1 + 10] [expr $index1 + 16]]
                } else {
                    set objectName [string range $headerSet [expr $index1 + 10] [expr $index1 + 18]]
                }
                set headerSet [string replace $headerSet $index1 $index2 ""]
                ##delete ipv4 handles if arp
                if {[regexp -nocase "arp" $headerInModify]} {
                    array set headerArray $headerSet
                    set index1 [string first "l4_header" $headerSet]
                    set index2 [string length $headerSet]
                    set handleList $headerArray(l4_header)
                    set headerSet [string replace $headerSet $index1 $index2 ""]
                    set streamHandle  [set ::$mns\::handleCurrentStream]
                    ::sth::Traffic::ProcessDeleteHandle $streamHandle $handleList l4
                    if {[info exists ::sth::Traffic::arrayHeaderTypesInCreate(l4_protocol)]} {
                        unset ::sth::Traffic::arrayHeaderTypesInCreate(l4_protocol)
                    }
                }
                set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $headerSet
                
                set streamHandle  [set ::$mns\::handleCurrentStream]
                       
                set handleName [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
                
                ProcessDirtyModifier $streamHandle $handleName
                
                if {"" != $handleName} {
                    ::sth::sthCore::invoke ::stc::delete $handleName
                }
                
                set ::sth::Traffic::arrayHeaderTypesInCreate(l3_protocol) $headerInModify
                set ::$mns\::arrayStreamHeaderTypesInCreateMAP([set ::$mns\::handleCurrentStream]) [array get ::$mns\::arrayHeaderTypesInCreate]

            }
        } else {
            ::sth::sthCore::log debug "$_procName l3 header to be added through mode modify ";
        }
    }
    
    ##################################################
    # Modify L3 Outer encapsulation
    ##################################################
    if {[info exists userArgsArray(l3_outer_protocol)]} {
        set ::$mns\::l3OuterHeaderType outer_$userArgsArray(l3_outer_protocol);
        set headerInModify $userArgsArray(l3_outer_protocol);
        if {[info exists ::sth::Traffic::arrayHeaderTypesInCreate(l3_outer_protocol)]} {
            set headerInCreate [set ::$mns\::arrayHeaderTypesInCreate(l3_outer_protocol)];
            if {$headerInCreate != $headerInModify} {
                set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
                set index1 [string first "l3_header_outer" $headerSet]
                set index2 [string first "l4_header" $headerSet]
                if {$index2 == -1 } {
                   set index2 [string length $headerSet]    
                }
                set objectName [string range $headerSet [expr $index1 + 16] [expr $index2 - 2]]
                set headerSet [string replace $headerSet $index1 $index2 ""]
                set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $headerSet
                
                set streamHandle  [set ::$mns\::handleCurrentStream]
                
                set handleName [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
                
                ProcessDirtyModifier $streamHandle $handleName
                ::sth::sthCore::invoke ::stc::delete $handleName
                
                set ::sth::Traffic::arrayHeaderTypesInCreate(l3_outer_protocol) $headerInModify
                set ::$mns\::arrayStreamHeaderTypesInCreateMAP([set ::$mns\::handleCurrentStream]) [array get ::$mns\::arrayHeaderTypesInCreate]
            }
        } else {
            ::sth::sthCore::log debug "$_procName l3 outer header to be added through mode modify ";
        }
    }
    
    ##################################################
    # Modify IPv6 next header
    ##################################################
    if {[info exists userArgsArray(ipv6_extension_header)] || [info exists userArgsArray(ipv6_frag_offset)] || [info exists userArgsArray(ipv6_frag_more_flag)] || [info exists userArgsArray(ipv6_frag_id)]} {
        if {[catch {::$mns\::processCreateModifyIpv6NextHeader} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }

    ##################################################
    # Modify IPv4 header Option, focus on routerAlert
    ##################################################
    if {[info exists userArgsArray(ipv4_header_options)] || [info exists userArgsArray(ipv4_router_alert)] } {
         if {[catch {::$mns\::processCreateModifyIpv4HeaderOptions} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }

    ##################################################
    # Modify L4 encapsulation
    ##################################################
    if {[info exists userArgsArray(l4_protocol)]} {
        set ::$mns\::l4HeaderType $userArgsArray(l4_protocol);
        if {[regexp "ip" $userArgsArray(l4_protocol)]} {
            set ::$mns\::l4HeaderType l4_$userArgsArray(l4_protocol);
        }
        set headerInModify $userArgsArray(l4_protocol);
        if {[info exists ::sth::Traffic::arrayHeaderTypesInCreate(l4_protocol)]} {
            set headerInCreate [set ::$mns\::arrayHeaderTypesInCreate(l4_protocol)];
            if {$headerInCreate != $headerInModify} {
                set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
                array set headerArray $headerSet
                set index1 [string first "l4_header" $headerSet]
                set index2 [string length $headerSet]
                set handleList $headerArray(l4_header)
                set headerSet [string replace $headerSet $index1 $index2 ""]
                set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $headerSet
                set streamHandle  [set ::$mns\::handleCurrentStream]
            
                ::sth::Traffic::ProcessDeleteHandle $streamHandle $handleList l4
                
                set ::sth::Traffic::arrayHeaderTypesInCreate(l4_protocol) $headerInModify
                set ::$mns\::arrayStreamHeaderTypesInCreateMAP([set ::$mns\::handleCurrentStream]) [array get ::$mns\::arrayHeaderTypesInCreate]
            }
        } else {
            ::sth::sthCore::log debug "$_procName l4 header to be added through mode modify ";
        }
    }
    
    set funcTableName1 "::$mns\::traffic_config_procfunc";
    set funcTableName2 "";
    
    ##################################################   
    # Process input attribues using the functions
    # defined in "mode" on trafficConfigTable.tcl
    ##################################################
    
    foreach element $prioritisedAttributeList {
        foreach {prio sName} $element {
            _traffic_config_preprocess modify $sName
            
            set funcTableName2 "::$mns\::traffic_config_$sName\_mode";
            
            if {[info exists $funcTableName2\(modify)]} {
                set funcName [set $funcTableName2\(modify)];
            } else {
                set funcName [set $funcTableName1\($sName)];
            }
            
            if {$funcName != "_none_"} {
                if {[catch {::sth::Traffic::$funcName $sName} errMsg]} {
                    ::sth::sthCore::log debug "$funcName FAILED. $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                } else {
                    ::sth::sthCore::log info "$funcName for $sName \t PASSED."
                }
            }
        }
    }
    
    ##################################################
    # Modify general attributes
    ##################################################
    
    ::$mns\::processConfigGeneralAttributes
    
    if {$::sth::Session::fillTraffic eq "set"} {
        ##################################################
        # Modify fiber channel protocol
        ##################################################
        if {[info exists userArgsArray(l2_encap)] && $userArgsArray(l2_encap) == "fibre_channel"} {
            set headerStream [set ::$mns\::handleCurrentStream]
            set fcHnd [::sth::sthCore::invoke stc::get $headerStream -children-fc:fc]
            set fcListOptions ""
            foreach opt $::sth::Traffic::listl2encap_FC {
                set stcAttr [set ::sth::Traffic::traffic_config_stcattr($opt)]
                lappend fcListOptions -$stcAttr $userArgsArray($opt)
            }
            if {$fcHnd ne ""} {
                if {$fcListOptions ne ""} {
                    ::sth::sthCore::invoke stc::config $fcHnd $fcListOptions
                } 
            }
            
            set fcSofEofHnd [::sth::sthCore::invoke stc::get $headerStream -children-fc:fcSofEof]
            set fcListOptions ""
            foreach opt $::sth::Traffic::listl2encap_FcSofEof {
                set stcAttr [set ::sth::Traffic::traffic_config_stcattr($opt)]
                lappend fcListOptions -$stcAttr $userArgsArray($opt)
            }
            if {$fcSofEofHnd ne "" && $fcListOptions ne ""} {
                ::sth::sthCore::invoke stc::config $fcSofEofHnd $fcListOptions
            }

        }
    } elseif {$::sth::Session::xmlFlag != 1} {
    # TODO: Bad fix, but the following code uses many data structures created in create api, 
    # skip them in modify mode for now. Modify mode has a limited range to modify.
    set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]
    array set arrayHeaders $headerSet
    ##################################################
    # Modify Imix attributes
    ##################################################
    #Add by Fei Cheng 08-09-27
    if {[info exists userArgsArray(length_mode)] && $userArgsArray(length_mode) == "imix"} {
            if {[catch {::$mns\::processImixAttributes} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
    }
    
    if {[info exists userArgsArray(l2_encap)]} {
        if {[catch {::$mns\::processCreateL2Encap $_procName} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    

    ##################################################
    # Modify Gre protocol
    ##################################################
    if {[info exists userArgsArray(tunnel_handle)]} {
        if {[catch {::$mns\::processCreateGreProtocol} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    
    ##################################################
    # Modify Vpls Traffic
    ##################################################
    if {[info exists userArgsArray(vpls_source_handle)] && [info exists userArgsArray(vpls_destination_handle)]} {
        if { $iterations == 2 && $x == 1 } {
            set vpls_source_handle $userArgsArray(vpls_destination_handle)
            set vpls_destination_handle $userArgsArray(vpls_source_handle)
        } else {
            set vpls_source_handle $userArgsArray(vpls_source_handle)
            set vpls_destination_handle $userArgsArray(vpls_destination_handle)
        }
        if {[catch {::$mns\::processVplsTraffic $vpls_source_handle $vpls_destination_handle} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    
    ##################################################
    # Process bound traffic
    ##################################################
    
    set streamBlkHandle $::sth::Traffic::handleCurrentStream
    set emulation_src_handle 0
    set emulation_dst_handle 0
    if { [info exists userArgsArray(emulation_src_handle)] } {
        set emulation_src_handle $userArgsArray(emulation_src_handle)
    } 
    if { [info exists userArgsArray(emulation_dst_handle)] } {
        set emulation_dst_handle $userArgsArray(emulation_dst_handle)
    }
    
    set useNativeBinding false
    if { $emulation_src_handle != 0 || $emulation_dst_handle != 0 } {
        if {[catch {::sth::Traffic::processSrcAndDstEmulationHandles \
             $streamBlkHandle $emulation_src_handle $emulation_dst_handle $useNativeBinding } errMsg]} {
            ::sth::sthCore::processError trafficKeyedList $errMsg {}
            return -code error $errMsg
        
        }
    }
    ::sth::Traffic::_traffic_config modify L2
    
    ##################################################
    # Process L3 outer encapsulation
    ##################################################
    if {[info exists userArgsArray(l3_outer_protocol)]} {
        if {[info exists arrayHeaders(l3_header_outer)]} {
            set ::$mns\::handleCurrentHeader $arrayHeaders(l3_header_outer);
        } else {
            set ::$mns\::handleCurrentHeader 0;
        }
        
        set ::$mns\::l3HeaderType outer_$userArgsArray(l3_outer_protocol);
        
        if {[catch {::$mns\::processCreateL3Protocol} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    
    ##################################################
    # Process L3 encapsulation
    ##################################################
    if {[info exists userArgsArray(l3_protocol)]} {
        set ::$mns\::l3HeaderType $userArgsArray(l3_protocol);
        if {[info exists arrayHeaders(l3_header)]} {
            set ::$mns\::handleCurrentHeader $arrayHeaders(l3_header);
        } else {
            set ::$mns\::handleCurrentHeader 0;
        }
        
        if {[catch {::$mns\::processCreateL3Protocol} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    ::sth::Traffic::_traffic_config modify L3
    
    ##################################################
    # Process L4 encapsulation
    ##################################################
    if {[info exists userArgsArray(l4_protocol)] && $userArgsArray(l4_protocol) != "ospf"} {
        if {[info exists arrayHeaders(l4_header)]} {
            set ::$mns\::handleCurrentHeader $arrayHeaders(l4_header);
        } else {
            set ::$mns\::handleCurrentHeader 0;
        }
        
        if {[catch {::$mns\::processCreateL4Protocol;} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
        
    }
    
    if {[info exists userArgsArray(vxlan)]} {
        if {[catch {::$mns\::processCreateVxlan} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    ##################################################
    # Process Inner L2 encapsulation when there is vxlan
    ##################################################
    if {[regexp -nocase "vxlan" [::sth::sthCore::invoke stc::get $streamBlkHandle -children]]} {
        set vxlan [::sth::sthCore::invoke stc::get $streamBlkHandle -children-vxlan:vxlan]
    } else {
        set vxlan ""
    }
    
    if {[info exists userArgsArray(inner_l2_encap)] && $vxlan != ""} {
        if {[catch {::$mns\::processCreateL2Encap vxlan_$_procName} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    
    ##################################################
    # Process L3 encapsulation
    ##################################################
    if {[info exists userArgsArray(inner_l3_protocol)]} {
        set ::$mns\::l3HeaderType inner_ipv4;
        if {[info exists arrayHeaders(inner_l3_header)]} {
            set ::$mns\::handleCurrentHeader $arrayHeaders(inner_l3_header);
        } else {
            set ::$mns\::handleCurrentHeader 0;
        }
        
        if {[catch {::$mns\::processCreateL3Protocol} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    #######################################################
    # Modify Custom encapsulation at the end of the frames
    #######################################################
    if {[info exists userArgsArray(custom_pattern)]} {
        if {[catch {::$mns\::processCreateCustomHeader custom_pattern modify;} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
    }
    }
    
    ::sth::Traffic::_traffic_config modify L4

    keylset trafficKeyedList status $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processValidateObjectList {objectType listObjectList} {
    
    set _procName "processValidateObjectList";
    
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    upvar mns mns;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    
    if {$objectType == "stream" } {
        set arrayName arraystreamHnd;
    } elseif {$objectType == "port" } {
        set arrayName arrayPortHnd;
    } else {
        # this should not happen.
        #puts "unknown object type defined to validate";
    }
    
    foreach objectHandle $listObjectList {
        if {[info exists ::$mns\::$arrayName\($objectHandle)]} {
        } else {
            ::sth::sthCore::log debug "$_procName bad handle $objectHandle entered. ";
            # call process error here.
            set errMsg "bad handle $objectHandle entered.";
            ::sth::sthCore::processError trafficKeyedList $errMsg {}
            return $::sth::sthCore::FAILURE;
        }
    }
    
    return $::sth::sthCore::SUCCESS;
}

# This mode enables/disables the streamBlocks entered by the user.
# It will accept a single streamBlock or a list of streamBlocks
# It will also accept a port handle, if the user wants to enable/disable all the streamBlocks under that port
# First validate if all streamBlocks are genuine.
# Even if one is wrong, we would fail the command

proc ::sth::Traffic::processTrafficConfigModeEnableDisable {} {
    
    set _procName "processTrafficConfigModerEnableDisable";
    
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::Traffic::modeOfOperation;
    
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    
    set dashedAttrValuePairs "-Active FALSE"
    set listStreamID "";
    if {$::sth::Traffic::modeOfOperation == "disable" ||
        $::sth::Traffic::modeOfOperation == "remove" } {
        
        set dashedAttrValuePairs "-Active FALSE"
    } else {
        set dashedAttrValuePairs "-Active TRUE"
    }
        
    
    if {[info exists userArgsArray(stream_id)] || [info exists userArgsArray(port_handle)]} {
        
        if {[info exists userArgsArray(stream_id)]} {
            set listStreamID $userArgsArray(stream_id);
        }
        
        if {[info exists userArgsArray(port_handle)]} {
            # deavtivate all streams under the port
            set listHLTporthandle $userArgsArray(port_handle);
            foreach HLTporthandle $listHLTporthandle {              
                set listStreamIDport [::sth::sthCore::invoke ::stc::get $HLTporthandle -children-streamblock]
                foreach streamID $listStreamIDport {
                    lappend listStreamID $streamID;
                }
            }
        }
        
        foreach streamID $listStreamID {
            # FIXME: (MGJ) If the user tries to delete a non-existent streamblock, don't throw an error.
            set streamExists 1
            if {[string equal -nocase $::sth::Traffic::modeOfOperation "remove"]} {
                if { [catch {stc::get $streamID} errmsg] } {
                    set streamExists 0
                }
            }

            if { $streamExists } {
                ::sth::sthCore::log debug "$_procName Calling stc::config $streamID $dashedAttrValuePairs"
                set cmdName "::sth::sthCore::invoke ::stc::config $streamID $dashedAttrValuePairs";
                if {[catch {eval $cmdName} retHandle]} {
                    # call process error here.
                    ##puts " i got $retHandle";
                    ::sth::sthCore::log info "$_procName $streamID Failed. $retHandle";
                    return -code 1 -errorcode -1 $retHandle;
                } else {
                    ::sth::sthCore::log info "$_procName $streamID Success. ";
                }
            } else {
                ::sth::sthCore::log info "$_procName $streamID doesn't exists. Unable to remove it.";
            }
        }
    } else {
        # call process error here.
        set errMsg "";
        ::sth::sthCore::processError trafficKeyedList "mandatory args missing. At least one of stream_id or port_handle should be present" {}
        return -code 1 -errorcode -1 $errMsg;
    }
    
    keylset trafficKeyedList status $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processTrafficConfigModereset {} {
    
    set _procName "processTrafficConfigModereset";
    
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::Traffic::modeOfOperation;
    
    upvar mns mns;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    set listStreamID "";

    set listHLTporthandle [::sth::sthCore::invoke ::stc::get project1 -children-port]
    if {[info exists userArgsArray(port_handle)]} {
        set listHLTporthandle $userArgsArray(port_handle) 
    }
    if {[info exists userArgsArray(stream_id)]} {
        foreach streamID [split $userArgsArray(stream_id) " "] {
            lappend listStreamID $streamID;
            if {[info exists ::$mns\::arraystreamHnd($streamID)]} {
                unset ::$mns\::arraystreamHnd($streamID);
            }
            foreach handlePortHandle $listHLTporthandle {
                regsub $streamID [set ::$mns\::arrayPortHnd($handlePortHandle)] ""
            }
        }
        ::sth::sthCore::invoke ::stc::perform DeleteCommand -ConfigList $listStreamID
    } else {
        foreach HLTporthandle $listHLTporthandle {              
            set listStreamIDport [::sth::sthCore::invoke ::stc::get $HLTporthandle -children-streamblock]
            foreach streamID $listStreamIDport {
                lappend listStreamID $streamID;
                if {[info exists ::$mns\::arraystreamHnd($streamID)]} {
                    unset ::$mns\::arraystreamHnd($streamID);
                }
            }
        }
        ::sth::sthCore::invoke ::stc::perform DeleteCommand -ConfigList $listStreamID
        
        set listPortHandleList [array names ::$mns\::arrayPortHnd];
        foreach handlePortHandle $listPortHandleList {
            set ::$mns\::arrayPortHnd($handlePortHandle) "";
        }
    }
    keylset trafficKeyedList status $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processHLTporthandle {switchName} {
    
    # TODO:
    # A bad fix for now. Setting the current handle the way it is set now.
    # Once the port_handle2 is implemented, i would put a check for the switchName and then set the current handle accordingly
    
    set _procName "processHLTporthandle";
    set retHandle "";
    set procStatus 0;
    upvar mns mns;
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    
    set HLTporthandle $userArgsArray($switchName);
    
    ::sth::sthCore::log debug "$_procName: Calling stc::create streamBlock $HLTporthandle retHandle"
    
    #new switch enable_stream_only_gen added to control whether to EnableStreamOnlyGeneration
    set flag "true";
    if {[info exists userArgsArray(enable_stream_only_gen)]} {
        if {$userArgsArray(enable_stream_only_gen) == 0} {
           set flag "false"
        }
    }
    
    #set the value for the global variable enableStream, default is true
    if {[info exists userArgsArray(enable_stream)]} {
        set  ::sth::Traffic::enableStream  $userArgsArray(enable_stream)
    }
    
    if {[regexp -nocase {^many_to_many$} $userArgsArray(endpoint_map)]} {
        set userArgsArray(endpoint_map) "one_to_many"
    }
    
    if {[catch {::sth::sthCore::invoke ::stc::create streamBlock -under $HLTporthandle -frameconfig "" -EndpointMapping $userArgsArray(endpoint_map) -EnableStreamOnlyGeneration $flag -ShowAllHeaders true} retHandle]} {
        set errorString "error while processing port handle";
        ::sth::sthCore::log debug "$_procName: $errorString $retHandle"
        return -code 1 -errorcode -1 $errorString;
    } else {
        # fix CR329671909, a critical design error for arrayHeaderTypesInCreate
        set ::$mns\::arrayStreamHeaderTypesInCreateMAP($retHandle) [array get ::$mns\::arrayHeaderTypesInCreate]
        
        ::sth::sthCore::log info "$_procName: stc::create. Handle is $retHandle";
        # fix for 121297056 (Sync card)
        # stream Block was created properly.
        # update the stream block and delete the ip header if present
        
        set ::$mns\::strHandlel2EncapMap($retHandle) [set ::$mns\::l2EncapType]
        
        if {[catch {::sth::sthCore::invoke ::stc::perform StreamBlockUpdate -streamblock $retHandle} updateRet]} {
            ::sth::sthCore::log error "$_procName: update streamblock $retHandle failed. $updateRet ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: update streamblock $retHandle passed. $updateRet ";
            # if IP header is present, delete it.
        }
        
        if {[catch {::sth::sthCore::invoke ::stc::get $retHandle -children} childrenList]} {
            ::sth::sthCore::log error "$_procName: $retHandle -children $childrenList ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $retHandle -children $childrenList ";
            # if IP header is present, delete it.
            foreach child $childrenList {
                if {[regexp fc:fc $child]} {
                    continue
                }
                if {![regexp (?i)HDLC $child]} {
                    if {[catch {::sth::sthCore::invoke ::stc::delete $child} deleteRet]} {
                        ::sth::sthCore::log error "$_procName: ::stc::delete $child failed. $deleteRet ";
                        return $::sth::sthCore::FAILURE;
                    } else {
                        ::sth::sthCore::log info "$_procName: ::stc::delete $child passed. $deleteRet  ";
                    }
                }
            }
        }
        
        if {$switchName == "port_handle"} {
            set ::$mns\::handleTxStream $retHandle;
        } else {   
            set ::$mns\::handleRxStream $retHandle;
        }
        #set ::$mns\::handleTxStream $retHandle;
        #set ::$mns\::handleCurrentStream $retHandle;
        
        set listOfStreams {};
        if {[info exists ::$mns\::arrayPortHnd($HLTporthandle)]} {
            set listOfStreams [set ::$mns\::arrayPortHnd($HLTporthandle)];
        }
        
        lappend listOfStreams $retHandle;
        set ::$mns\::arrayPortHnd($HLTporthandle) $listOfStreams;
        set ::$mns\::arraystreamHnd($retHandle) "";
    }
    
    return $::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processSwapl3ForBidirectional {} {
    set _procName "processSwapl3ForBidirectional";
    
    upvar mns mns;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    
    set ipElementsToSwap {addr mode step count};
    set l4ElementsToSwap {port port_mode port_step port_count};
    set prefixList {ip ipv6 tcp udp}
    #listl3Header_Ipv4_bidirectional
    foreach prefix $prefixList {
        if {$prefix == "ip" || $prefix == "ipv6"} {
            set elementsToSwap $ipElementsToSwap
        } else {
            set elementsToSwap $l4ElementsToSwap
        }
    foreach element $elementsToSwap {
    set sSwitch $prefix\_src_$element;
    set dSwitch $prefix\_dst_$element;
        if {[info exists userArgsArray($sSwitch)]} {
            if {[info exists userArgsArray($dSwitch)]} {
            # that mean both src and dst switch exist. 
            set src_loc $userArgsArray($sSwitch);
            set dst_loc $userArgsArray($dSwitch);
         set userArgsArray($dSwitch) $src_loc;
         set userArgsArray($sSwitch) $dst_loc;
         } else {
         # src exists and dst switch does not exist. 
         # set the dst and unset the src. Let the default be used for src. 
         set src_loc $userArgsArray($sSwitch);
         set userArgsArray($dSwitch) $src_loc;
        lappend switch_list $dSwitch;
         #unset userArgsArray($sSwitch);
         }
        } else {
            # check if dst switch exists 
            if {[info exists userArgsArray($dSwitch)]} {
                # this means dst exists and src switch does not exist. 
                # set the src and unset the dst. Let the default be used for dst. 
                set dst_loc $userArgsArray($dSwitch);
                set userArgsArray($sSwitch) $dst_loc;
                #unset userArgsArray($dSwitch);
            } else {
            # nither src nor dst exist. 
            # need not do anything. 
            }
        }
    }
    }
    
    # take care of ppp bidirectional traffic here.
    # at this point we know that both src and dst exist. Just swap the two.
    if {[info exists userArgsArray(ppp_link)] && $userArgsArray(ppp_link) == "1"} {
        set src_loc $userArgsArray(ppp_link_traffic_src_list);
        set dst_loc $userArgsArray(downstream_traffic_src_list);
        
        set userArgsArray(ppp_link_traffic_src_list) $dst_loc;
        set userArgsArray(downstream_traffic_src_list) $src_loc;
    }
    
    if {[info exists userArgsArray(emulation_src_handle)]} {
        # at this point we know that both src and dst exist. Just swap the two.
        set src_loc $userArgsArray(emulation_src_handle);
        set dst_loc $userArgsArray(emulation_dst_handle);
        
        set userArgsArray(emulation_src_handle) $dst_loc;
        set userArgsArray(emulation_dst_handle) $src_loc;
    }
    
    #Swap the listl3SrcRangeModifier and listl3DstRangeModifier
    set ListToSwap {listl3 listTcpPort listUdpPort}
    foreach element $ListToSwap {
        if {[llength [set ::$mns\::$element\DstRangeModifier]] || [llength [set ::$mns\::$element\SrcRangeModifier]]} {
            set $element\DstRangeModifier_loc [set ::$mns\::$element\DstRangeModifier];
            set $element\SrcRangeModifier_loc [set ::$mns\::$element\SrcRangeModifier];
            set ::$mns\::$element\SrcRangeModifier "";
            set ::$mns\::$element\DstRangeModifier "";
            
            #swap "src" to "dst" and "dst" to "src" of the argumemt in the list***Src/DstRangeModifier.
            foreach elementValue [set $element\DstRangeModifier_loc] {
                regsub {dst} $elementValue {src} newValue
                lappend ::$mns\::$element\SrcRangeModifier $newValue
            }
            
            foreach elementValue [set $element\SrcRangeModifier_loc] {
                regsub {src} $elementValue {dst} newValue
                lappend ::$mns\::$element\DstRangeModifier $newValue
            }
        }
    }
    
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processTransmitMode {switchName} {
    
    # At this point we would not error out if any dependency is not met.
    # Forward Rules:
    # 1.    Atleast one of rate_bps / rate_pps / rate_percent should be present when transmit_mode is present.
    #       If not present, the stc default of 10% line rate will take effect.
    #   Load:       10
    #   LoadUnit:   PERCENT_LINE_RATE
    #       
    # 2.    For transmit_mode = continuous
    #       pkts_per_burst = 1 (must) (will ignore whatever value entered by the user, and set to 1).
    #       
    # 3.    For transmit_mode = continuous_burst
    #       pkts_per_burst > 1 (must) (will flag an error if not so).
    #
    # 4.    For transmit_mode = multi_burst
    #       "burst_loop_count" should be present. Not flag an error if not present.
    #
    # 5.    For transmit_mode = single_burst    
    #       burst_loop_count = 1 (must) (will ignore whatever value entered by the user, and set to 1).
    #
    # 6.    For transmit_mode = single_pkt
    #       burst_loop_count = 1 (must) (will ignore whatever value entered by the user, and set to 1).
    #       pkts_per_burst = 1 (must) (will ignore whatever value entered by the user, and set to 1).
    
    # Reverse Rules:
    # We will have to revisit this section
    #   (will flag an error for all)
    # 1.    If "burst_loop_count" is present, then transmit_mode = multi_burst / single_burst / single_pkt
    # 2.    If burst_loop_count = 1, transmit_mode = single_burst / single_pkt
    # 3.    If pkts_per_burst > 1, transmit_mode = continuous_burst
    # 4.    If pkts_per_burst = 1, transmit_mode = continuous
    # 
    
    set _procName "processTransmitMode";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;    
    
    variable arrayTransmitModeSwitches;
    set listArgsList {};
    
    set supportedTransmitModes [array names arrayTransmitModeSwitches];
    set transmitMode "";
    set transmitMode $userArgsArray($switchName);
    
    if {[catch {set listLocalSwitches $arrayTransmitModeSwitches($transmitMode)}]} {
        ::sth::sthCore::log debug "$_procName $transmitMode";
        set errorString "Invalid Transmit mode $transmitMode entered. Supported transmit_modes: $supportedTransmitModes";
        # call procesError here
        return -code 1 -errorcode -1 $errorString;
    }
    
    if {$switchName == "transmit_mode"} {
        set transmitMode $userArgsArray($switchName);
        set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
        set tableName "::$mns\::traffic_config_$switchName\_fwdmap"
        set stcConst [set $tableName\($transmitMode)];
        
        set listProcessedLocalList {};
        lappend listProcessedLocalList -$stcAttr $stcConst;
        
    }
    
    foreach {element defaultValue} $listLocalSwitches {
        
        set valueToSet "_none_";
        if {$defaultValue == "_none_"} {
            # We have to set the value entered by the user.
            if {[info exists userArgsArray($element)]} {
                set userEnteredValue $userArgsArray($element);
                set valueToSet $userEnteredValue;
            } else {
                # Log here and move on. We do not error out for any depenedncies here.
                ::sth::sthCore::log warn "$_procName expected $element for transmit_mode $transmitMode. Setting STC default value."
            }
        } else {
            # set the default value as specified in HLT.
            set valueToSet $defaultValue;
            ::sth::sthCore::log warn "$_procName. Setting the value for $element to $defaultValue. Ignoring any value entered by the user."
        }
        
        if {$valueToSet != "_none_"} {
            set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
            if {$element == "inter_stream_gap_unit"} {
                set tableName "::$mns\::traffic_config_$element\_fwdmap"
                set valueToSet [set $tableName\($valueToSet)];
            }
            ::sth::sthCore::log info "$_procName HLT: $element \t STC: -$stcAttr $valueToSet"
            lappend listProcessedLocalList -$stcAttr $valueToSet;
        }
        
        #return -code 1 -errorcode -1 $errorString;
    }
    
    # get the generator and generator config here.
    # TODO:
    # As of now assuming this is mode create, so port handle is available.
    if {[info exists userArgsArray(port_handle)]} {
        set HLTporthandle $userArgsArray(port_handle);
        set handleGenerator [::sth::sthCore::invoke stc::get $HLTporthandle -children-generator]
    set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
    ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listProcessedLocalList
    } else {
        set errorString "can't read \"userArgsArray(port_handle)\": no such element in array. 'port_handle' is mandatory when calling 'transmit_mode'";
        return -code 1 -errorcode -1 $errorString;
    }
    
    #if it is bi-directional traffic, need to config the generator of the other port
    if {[info exists userArgsArray(bidirectional)] && $userArgsArray(bidirectional) && [info exists userArgsArray(port_handle2)]} {
        set HLTporthandle2 $userArgsArray(port_handle2);
        set handleGenerator [::sth::sthCore::invoke stc::get $HLTporthandle2 -children-generator]
    set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
    ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listProcessedLocalList
    }
        
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processTransmitModeSwitches {switchName} {
   
    set _procName "processTransmitModeSwitches";
    set listLocalList {};
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set listProcessedLocalList {};

    if {[info exists userArgsArray(transmit_mode)]} {
        ::sth::sthCore::log info "$_procName: transmit_mode exists in the definition. $switchName will be processed along with transmit_mode ";
    } else {
        ::sth::sthCore::log info "$_procName: transmit_mode does not exist in the definition. ";
        ::sth::sthCore::log info "The default transmit_mode is continuous. $switchName just mapped down";
        set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
        lappend listProcessedLocalList -$stcAttr $userArgsArray($switchName);
        if {[info exists userArgsArray(port_handle)]} {
            set HLTporthandle $userArgsArray(port_handle);
            set handleGenerator [::sth::sthCore::invoke stc::get $HLTporthandle -children-generator]
            set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
            ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listProcessedLocalList
        } else {
            set errorString "can't read \"userArgsArray(port_handle)\": no such element in array. 'port_handle' is mandatory when calling $switchName";
            return -code 1 -errorcode -1 $errorString;
        }
        
        #if it is bi-directional traffic, need to config the generator of the other port
        if {[info exists userArgsArray(bidirectional)] && $userArgsArray(bidirectional) && [info exists userArgsArray(port_handle2)]} {
            set HLTporthandle2 $userArgsArray(port_handle2);
            set handleGenerator [::sth::sthCore::invoke stc::get $$HLTporthandle2 -children-generator]
            set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
            ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listProcessedLocalList    
        }
    }
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processLengthMode {switchName} {
    # TODO: Add fixed and random length modes as choices to the table. Davison to provide
    
    set _procName "processLengthMode";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    if {![string compare -nocase -length 9 $switchName "l3_length"]
        || ![string compare -nocase -length 7 $switchName "l3_imix"] ||
        ![string compare -nocase -length 10 $switchName "frame_size"]} {
        set mode "length_mode";
        if {![info exists userArgsArray($mode)]} {
            set errorString "empty length mode. Should be one of the fixed|increment|random|imix|auto";
            return -code 1 -errorcode -1 $errorString;
        } else {
           return;   
        } 
    }
    
    variable arrayLengthModeSwitches;
    
    lappend ::$mns\::listGeneralAttributes $switchName;
    set lengthMode $userArgsArray($switchName);
    
    # TODO: put a catch to see if invalid length mode is entered
    #MOD Fei Cheng 08-09-27
    if {$lengthMode == "increment"} {
        #add special handle for length_mode  increment
        set userArgsArray($switchName) "incr"
        if {[info exists userArgsArray(l3_length_step)]} {
            lappend ::$mns\::listGeneralAttributes "l3_length_step";
        }
        if {[info exists userArgsArray(l3_length_max)]} {
            lappend ::$mns\::listGeneralAttributes "l3_length_max";
        }
        if {[info exists userArgsArray(l3_length_min)]} {
            lappend ::$mns\::listGeneralAttributes "l3_length_min";
        }
        if {[info exists userArgsArray(frame_size_step)]} {
            lappend ::$mns\::listGeneralAttributes "frame_size_step";
        }
        if {[info exists userArgsArray(frame_size_max)]} {
            lappend ::$mns\::listGeneralAttributes "frame_size_max";
        }
        if {[info exists userArgsArray(frame_size_min)]} {
            lappend ::$mns\::listGeneralAttributes "frame_size_min";
        }
    } elseif {$lengthMode == "imix"} {
        #if {[info exists userArgsArray(l3_imix1_ratio)]} {
        #    if {[info exists userArgsArray(port_handle)]} {
        #       set cur
        #    }
        #    set headerToConfigure [set ::$mns\::handleCurrentStream];
        #    #puts [stc::get port1]
        #    #puts [stc::get framelengthfistribution1]
        #}
        
    } elseif {$lengthMode != "fixed" && $lengthMode != "random" && $lengthMode != "auto"} {
        set errorString "invalid length mode: $lengthMode. Should be one of the  fixed|increment|random|imix|auto";
        return -code 1 -errorcode -1 $errorString;
    }
    
    set listLocalSwitches $arrayLengthModeSwitches($lengthMode);
    foreach element $listLocalSwitches {
        set key [lindex $element 0]
        set default [lindex $element 1]
        if {[info exists userArgsArray($key)]} {
            lappend ::$mns\::listGeneralAttributes $key;
        } else {
            # add default value for frame length instead of throwing out an error
            set userArgsArray($key) $default
            lappend ::$mns\::listGeneralAttributes $key;
        }
    }
    #if the frame_size is configured, ignore l3_length, the same as frame_size_min and frame_size_max
    if {[info exists userArgsArray(frame_size)]} {
        set ::$mns\::listGeneralAttributes [regsub -all {^l3_length$} [set ::$mns\::listGeneralAttributes] ""]
        lappend ::$mns\::listGeneralAttributes frame_size;
    }
    if {[info exists userArgsArray(frame_size_min)]} {
        set ::$mns\::listGeneralAttributes [regsub -all {l3_length_min} [set ::$mns\::listGeneralAttributes] ""]
        lappend ::$mns\::listGeneralAttributes frame_size_min;
    }
    if {[info exists userArgsArray(frame_size_max)]} {
        set ::$mns\::listGeneralAttributes [regsub -all {l3_length_max} [set ::$mns\::listGeneralAttributes] ""]
        lappend ::$mns\::listGeneralAttributes frame_size_max;
    }
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processLoadSwitches {switchName} {
    
    set _procName "processLoadSwitches";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set loadValue $userArgsArray($switchName);
    set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
    
    set tableName "::$mns\::traffic_config_$switchName\_fwdmap"
    set stcConst [set $tableName\($switchName)];
    
    ::sth::sthCore::log info "$_procName HLT: $switchName \t STC: -$stcAttr $stcConst -Load $loadValue"
    lappend ::$mns\::listSbLoadProfileList -$stcAttr $stcConst;
    lappend ::$mns\::listSbLoadProfileList -Load $loadValue;
    
    #return -code 1 -errorcode -1 $errorString;
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processSbLoadProfileSwitches {switchName} {
    
    set _procName "processSbLoadProfileSwitches";
   
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set switchValue $userArgsArray($switchName);
    set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
    if {$switchName == "inter_stream_gap_unit_sb"} {
      set tableName "::$mns\::traffic_config_$switchName\_fwdmap"
      set stcConst [set $tableName\($switchValue)];
      lappend ::$mns\::listSbLoadProfileList -$stcAttr $stcConst;
    } else {
      lappend ::$mns\::listSbLoadProfileList -$stcAttr $switchValue
    }
           
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processCommonSwitches {switchName} { 
    
    set _procName "processCommonSwitches";
   
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set switchValue $userArgsArray($switchName);
    set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
   
    if {$switchName == "fill_type" || $switchName == "disable_signature"} {
      set tableName "::$mns\::traffic_config_$switchName\_fwdmap"
      set stcConst [set $tableName\($switchValue)];
      lappend ::$mns\::listProcessedList -$stcAttr $stcConst;
    } else {
      lappend ::$mns\::listProcessedList -$stcAttr $switchValue
    }
    
    return ::sth::sthCore::SUCCESS;
}

# Proc to process the analyzer threshold values for a port - US38931 support Frame threshold. 
 proc ::sth::Traffic::processThresholdSwitches {switchName} {   
    
    set _procName "processThresholdSwitches";
   
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    set switchValue $userArgsArray($switchName);
    set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
    lappend ::$mns\::listThresholdList -$stcAttr $switchValue
    return ::sth::sthCore::SUCCESS;
}                                                                                              


proc ::sth::Traffic::processGroupProcessingl2 {switchName} {
    # use "variable l2EncapType" here instead of accessing l2EncapType on line 119
    
    # dependency {l2_encap ethernet_ii}
    set _procName "processGroupProcessingl2";
     
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    if {[regexp "inner" $switchName]} {
        set extEncapType [set ::$mns\::innerl2EncapType];
    } else {
        set extEncapType [set ::$mns\::l2EncapType];
    }
    set intEncapType [set ::$mns\::traffic_config_dependency($switchName)];
    
    if {[regexp "mpls" $extEncapType] || [regexp "pppoe" $extEncapType] || $extEncapType == "ethernet_ii_vlan" || $intEncapType == $extEncapType
                                || [lsearch $intEncapType $extEncapType] >= 0 || [regexp "_vlan" $extEncapType]} {
        switch -exact $extEncapType {
            "ethernet_ii_pppoe" -
            "ethernet_ii" {
                if {[regexp "inner" $switchName]} {
                    # process the inner l2 args which will be used when configure the vxlan
                    if {[regexp mac $switchName]} {
                        lappend ::$mns\::listInnerl2encap_EthernetII $switchName; 
                    }
                } else {
                    if {[regexp "2" $switchName]} {
                        lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                    } elseif {[regexp ether_type $switchName]} {
                        lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                        lappend ::$mns\::listl2encap_EthernetII $switchName;
                    } else {
                        lappend ::$mns\::listl2encap_EthernetII $switchName;
                    }
                }
            }
            "ethernet_ii_vlan_pppoe" -
            "ethernet_ii_qinq_pppoe" -
            "ethernet_ii_vlan" {
                if {[regexp inner $switchName]} {
                    # process the inner l2 args which will be used when configure the vxlan
                    if {[regexp mac $switchName]} {
                        lappend ::$mns\::listInnerl2encap_EthernetII $switchName;
                    } elseif {[regexp outer $switchName]} {
                        lappend ::$mns\::listInnerl2encap_OuterVlan $switchName;
                    } else {
                        lappend ::$mns\::listInnerl2encap_Vlan $switchName;
                    }
                } else {
                    if {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                        lappend ::$mns\::listl2encap_EthernetII $switchName;
                    } elseif {[regexp mac $switchName] && [regexp "2" $switchName] } {
                        lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                    } elseif {[regexp ether_type $switchName]} {
                        lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                        lappend ::$mns\::listl2encap_EthernetII $switchName;
                    } elseif {[regexp outer $switchName]} {
                        lappend ::$mns\::listl2encap_OuterVlan $switchName;
                    } elseif {[regexp "other" $switchName]} {
                        lappend ::$mns\::listl2encap_OtherVlan $switchName;
                    } else {
                        lappend ::$mns\::listl2encap_Vlan $switchName;
                    }
                }
            }
            "ethernet_ii_unicast_mpls" {
                if {[regexp mpls $switchName]} {
                    lappend ::$mns\::listMplsHeaderAttributes_Mpls $switchName;
                } elseif {[regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                } elseif {[regexp ether_type $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                    lappend ::$mns\::listl2encap_EthernetII $switchName;
                }  else {
                    lappend ::$mns\::listl2encap_EthernetII $switchName;
                }
            }
            "ethernet_ii_vlan_mpls" {
                if {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetII $switchName;
                } elseif {[regexp mac $switchName] && [regexp "2" $switchName] } {
                    lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                } elseif {[regexp outer $switchName]} {
                    lappend ::$mns\::listl2encap_OuterVlan $switchName;
                } elseif {[regexp "other" $switchName]} {
                    lappend ::$mns\::listl2encap_OtherVlan $switchName;
                } elseif {[regexp mpls $switchName]} {
                    lappend ::$mns\::listMplsHeaderAttributes_Mpls $switchName;
                } elseif {[regexp ether_type $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetII_bidirectional $switchName;
                    lappend ::$mns\::listl2encap_EthernetII $switchName;
                }  else {
                    lappend ::$mns\::listl2encap_Vlan $switchName;
                }
            }
            "atm_vc_mux" -
            "atm_llcsnap" {
                lappend ::$mns\::listl2encap_ATM $switchName;
            }
            "fibre_channel" {
                if {[regexp fc_eof $switchName] || [regexp fc_sof $switchName]} {
                    lappend ::$mns\::listl2encap_FcSofEof $switchName;
                } else {
                    lappend ::$mns\::listl2encap_FC $switchName;
                }
            }
            "ethernet_8022" {
                # arp to get mac2 if no mac_dst2, tbd
                if {[regexp mac $switchName] && [regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_Ethernet8022_bidirectional $switchName;
                } elseif {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_Ethernet8022 $switchName;
                } else {
                    lappend ::$mns\::listl2encap_Ethernet8022 $switchName;
                    lappend ::$mns\::listl2encap_Ethernet8022_bidirectional $switchName;
                }
            }
            "ethernet_8022_vlan" {
                if {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_Ethernet8022 $switchName;
                } elseif {[regexp mac $switchName] && [regexp "2" $switchName] } {
                    lappend ::$mns\::listl2encap_Ethernet8022_bidirectional $switchName;
                } elseif {[regexp outer $switchName]} {
                    lappend ::$mns\::listl2encap_OuterVlan $switchName;
                } elseif {[regexp "other" $switchName]} {
                    lappend ::$mns\::listl2encap_OtherVlan $switchName;
                } elseif {[regexp vlan $switchName]} {
                    lappend ::$mns\::listl2encap_Vlan $switchName;
                } else {
                    lappend ::$mns\::listl2encap_Ethernet8022 $switchName;
                    lappend ::$mns\::listl2encap_Ethernet8022_bidirectional $switchName;
                }
            }
            "ethernet_8023_snap" {
                if {[regexp mac $switchName] && [regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetSnap_bidirectional $switchName;
                } elseif {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetSnap $switchName;
                } else {
                    lappend ::$mns\::listl2encap_EthernetSnap $switchName;
                    lappend ::$mns\::listl2encap_EthernetSnap_bidirectional $switchName;
                }
            }
            "ethernet_8023_snap_vlan" {
                if {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_EthernetSnap $switchName;
                } elseif {[regexp mac $switchName] && [regexp "2" $switchName] } {
                    lappend ::$mns\::listl2encap_EthernetSnap_bidirectional $switchName;
                } elseif {[regexp outer $switchName]} {
                    lappend ::$mns\::listl2encap_OuterVlan $switchName;
                } elseif {[regexp "other" $switchName]} {
                    lappend ::$mns\::listl2encap_OtherVlan $switchName;
                } elseif {[regexp vlan $switchName]} {
                    lappend ::$mns\::listl2encap_Vlan $switchName;
                } else {
                    lappend ::$mns\::listl2encap_EthernetSnap $switchName;
                    lappend ::$mns\::listl2encap_EthernetSnap_bidirectional $switchName;
                }
            }
            "ethernet_8023_raw" {
                if {[regexp mac $switchName] && [regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_Ethernet8023Raw_bidirectional $switchName;
                } elseif {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_Ethernet8023Raw $switchName;
                } else {
                    lappend ::$mns\::listl2encap_Ethernet8023Raw $switchName;
                    lappend ::$mns\::listl2encap_Ethernet8023Raw_bidirectional $switchName;
                }
            }
            "ethernet_8023_raw_vlan" {
                if {[regexp mac $switchName] && ![regexp "2" $switchName]} {
                    lappend ::$mns\::listl2encap_Ethernet8023Raw $switchName;
                } elseif {[regexp mac $switchName] && [regexp "2" $switchName] } {
                    lappend ::$mns\::listl2encap_Ethernet8023Raw_bidirectional $switchName;
                } elseif {[regexp outer $switchName]} {
                    lappend ::$mns\::listl2encap_OuterVlan $switchName;
                } elseif {[regexp "other" $switchName]} {
                    lappend ::$mns\::listl2encap_OtherVlan $switchName;
                } elseif {[regexp vlan $switchName]} {
                    lappend ::$mns\::listl2encap_Vlan $switchName;
                } else {
                    lappend ::$mns\::listl2encap_Ethernet8023Raw $switchName;
                    lappend ::$mns\::listl2encap_Ethernet8023Raw_bidirectional $switchName;
                }
            }
        }
    } else {
        set free_depend "ipx_header xns_header llc_dsap llc_ssap llc_control snap_oui_id snap_ether_type appletalk_header aarp_header decnet_header vines_header"
        if {[string match -nocase "vlan*" $switchName] || [regexp -nocase $switchName $free_depend]} {
            # fix CR277739080
            set errorString "Dependency Error for $switchName. ENTERED: $extEncapType. EXPECTED: $intEncapType";
            ::sth::sthCore::log warn "$_procName: $errorString "
            unset userArgsArray($switchName)
        } else {
            set errorString "Dependency Error for $switchName. ENTERED: $extEncapType. EXPECTED: $intEncapType";
            ::sth::sthCore::log debug "$_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        }
    }
    
    
    # for list mode of modifier, in this case the start value is a list.
    if {[llength $userArgsArray($switchName)] > 1} {
        ::sth::Traffic::processRangeModifierSwitches $switchName
    }
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processGroupProcessingl3 {switchName} {
    
    set _procName "processGroupProcessingl3";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    if {[string match -nocase "mac_discovery_gw" $switchName]} {
        #mac_discovery_gw doesn't need to check the dependecny
        if {[llength $userArgsArray($switchName)] > 1} {
            ::sth::Traffic::processRangeModifierSwitches $switchName
        }
        return ::sth::sthCore::SUCCESS;
    }
    
    if {[regexp outer $switchName]} {
        set extHeaderType [set ::$mns\::l3OuterHeaderType];
    } elseif {[regexp inner $switchName]} {
        set extHeaderType [set ::$mns\::l3InnerHeaderType];
    } else {
        set extHeaderType [set ::$mns\::l3HeaderType];
    }
    set intHeaderType [set ::$mns\::traffic_config_dependency($switchName)];
    
    # MOD Cheng Fei 08-10-07
    # Add a condition to handle the case which option don't need dependency
    # Add support for ARP
    if {[lsearch $intHeaderType $extHeaderType] >= 0 || $intHeaderType == "_none_"} {
        switch -exact $extHeaderType {
            "ipv4" {
                #MOD He Nana 11-04-07
                 lappend ::$mns\::listl3Header_Ipv4 $switchName;
            }
            "outer_ipv4" {
                #MOD He Nana 11-04-07
                lappend ::$mns\::listl3Header_OuterIpv4 $switchName;
            }
            "ipv6" {
                lappend ::$mns\::listl3Header_Ipv6 $switchName;
            }
            "outer_ipv6" {
                lappend ::$mns\::listl3Header_OuterIpv6 $switchName;
            }
            "arp" {
                lappend ::$mns\::listl3Header_Arp $switchName; 
            }
            "inner_ipv4" {
                lappend ::$mns\::listInnerl3Header_Ipv4 $switchName;
            }
            "gre" {
                lappend ::$mns\::listl3Header_Gre $switchName;
            }
        }
    } else {
        set errorString "Dependency Error for $switchName. ENTERED: $extHeaderType. EXPECTED: $intHeaderType";
        ::sth::sthCore::log debug "$_procName: $errorString "
        return -code 1 -errorcode -1 $errorString;
    }
    
    # for list mode of modifier, in this case the start value is a list.
    if {[llength $userArgsArray($switchName)] > 1} {
        ::sth::Traffic::processRangeModifierSwitches $switchName
    }
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processl3QosBits {switchName} {
    # TODO:
    # Add support for ip_tos_field here later.
    # This function may be modified a bit at that time. 
    set _procName "processl3QosBits";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    
    set intHeaderType [set ::$mns\::traffic_config_dependency($switchName)];

    switch $intHeaderType {
        "l4_ipv4" {
            set headerType "l4HeaderType"
            set qosListName "listl4QosBits"
            set precedenceModifier "listl4precedenceRangeModifier"
            set tosModifier "listl4tosRangeModifier"
            set precedenceAttr "l4_ip_precedence"
            set tosAttr "l4_ip_tos_field"
            set dscpAttr "l4_ip_dscp"
        }
        "outer_ipv4" {
            set headerType "l3OuterHeaderType"
            set qosListName "listl3OuterQosBits"
            set precedenceModifier "listl3OuterPrecedenceRangeModifier"
            set tosModifier "listl3OuterTosRangeModifier"
            set precedenceAttr "ip_outer_precedence"
            set tosAttr "ip_outer_tos_field"
            set dscpAttr "ip_outer_dscp"
        }
        default {
            set headerType "l3HeaderType"
            set qosListName "listl3QosBits"
            set precedenceModifier "listl3precedenceRangeModifier"
            set tosModifier "listl3tosRangeModifier"
            set precedenceAttr "ip_precedence"
            set tosAttr "ip_tos_field"
            set dscpAttr "ip_dscp"
        }

    }
    set extHeaderType [set ::$mns\::$headerType];
    if {[lsearch $intHeaderType $extHeaderType] < 0} {
        set errorString "Dependency Error for $switchName. ENTERED: $extHeaderType. EXPECTED: $intHeaderType";
        ::sth::sthCore::log debug "$_procName: $errorString "
        return -code 1 -errorcode -1 $errorString;
    }
    
    if {[regexp count $switchName] || [regexp step $switchName] || [regexp mode $switchName]|| [llength $userArgsArray($switchName)] > 1} {
        if {$userArgsArray(mode) == "modify" ||[llength $userArgsArray($switchName)] > 1} {
            lappend ::$mns\::$qosListName $switchName;
        }
        if {[regexp precedence $switchName]} {
            # if the argument "ip_precedence" isn't set by user, but the mode or step or count is set, it will call the function "processCreateQosModifier".
            if {[lsearch $prioritisedAttributeList "\[0-9\]* $precedenceAttr"] == -1} {
                lappend ::$mns\::$qosListName $precedenceAttr;
            }
            lappend ::$mns\::$precedenceModifier $switchName;
        } elseif {[regexp tos $switchName]} {
            if {[lsearch $prioritisedAttributeList "\[0-9\]* $tosAttr"] == -1} {
                lappend ::$mns\::$qosListName $tosAttr;
            }
            lappend ::$mns\::$tosModifier $switchName;
        } elseif {[regexp dscp $switchName]} {
            if {[lsearch $prioritisedAttributeList "\[0-9\]* $dscpAttr"] == -1} {
                lappend ::$mns\::$qosListName $dscpAttr;
            }
        }
    } else {
        lappend ::$mns\::$qosListName $switchName;
    }
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processGroupProcessingl4 {switchName} {
    
    set _procName "processGroupProcessingl4";
     
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set extHeaderType [set ::$mns\::l4HeaderType];
    set intHeaderType [set ::$mns\::traffic_config_dependency($switchName)];
    
    if {$intHeaderType == $extHeaderType || ($extHeaderType == "rtp" && $intHeaderType == "udp")} {
        switch -exact $intHeaderType {
            "tcp" {
                lappend ::$mns\::listl4Headertcp $switchName;
            }
            "udp" {
                lappend ::$mns\::listl4Headerudp $switchName;
            }
            "icmp" {
                lappend ::$mns\::listl4Headericmp $switchName;
            }
            "icmpv6" {
                lappend ::$mns\::listl4Headericmpv6 $switchName;
            }
            "igmp" {
                lappend ::$mns\::listl4Headerigmp $switchName;
            }
            "rtp" {
                lappend ::$mns\::listl4Headerrtp $switchName;
            }
            "isis" {
                lappend ::$mns\::listl4Headerisis $switchName;
            }
            "l4_ipv4" {
                lappend ::$mns\::listl4Headeripv4 $switchName;
            }
            "l4_ipv6" {
                lappend ::$mns\::listl4Headeripv6 $switchName;
            }
        }
    } else {
        set errorString "Dependency Error for $switchName. ENTERED: $extHeaderType. EXPECTED: $intHeaderType";
        ::sth::sthCore::log debug "$_procName: $errorString "
        return -code 1 -errorcode -1 $errorString;
    }
    
    # for list mode of modifier, in this case the start value is a list.
    if {[llength $userArgsArray($switchName)] > 1} {
        ::sth::Traffic::processRangeModifierSwitches $switchName
    }
    
    return ::sth::sthCore::SUCCESS;
}


proc ::sth::Traffic::processGroupProcessingVxlan {switchName} {
    set _procName "processGroupProcessingVxlan";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    lappend ::$mns\::listVxlanHeader $switchName;
    return ::sth::sthCore::SUCCESS;
}
proc ::sth::Traffic::processConfigGeneralAttributes {} {
    
    set _procName "processConfigGeneralAttributes";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar prioritisedAttributeList prioritisedAttributeList
    upvar mns mns;
    
    variable listGeneralAttributes;
    variable listProcessedList;
    variable listSbLoadProfileList;
    variable listThresholdList;
    
    set listArgsList {};
    set headerToConfigure [set ::$mns\::handleCurrentStream];
    
    foreach element [set listGeneralAttributes] {
        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
        if {[string match -nocase "l3_length*" $element] && ![string match -nocase "l3_length_step" $element]} {
            processFrameLength $element newFrameLength
            lappend listArgsList -$stcAttr $newFrameLength;
        } else {
            #if the frame_size and l3_length both are input, then we take the frame_size as the configuration value, ignoring l3_length
            if {[string match -nocase "frame_size*" $element]} {
                if {[lsearch $listArgsList -$stcAttr] > -1} {
                    set index [expr [lsearch $listArgsList -$stcAttr] + 1]
                    set listArgsList [lreplace $listArgsList $index $index $userArgsArray($element)]
                } else {
                    lappend listArgsList -$stcAttr $userArgsArray($element)
                }
            } else {
                lappend listArgsList -$stcAttr $userArgsArray($element);
            }
        }
    }
    
    
    #lappend listArgsList $listProcessedList;
    
    ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList $listProcessedList"
    set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList $listProcessedList"
    
    
    if {[catch {eval $cmdName} retHandle]} {
        #puts "error while configuring $headerToConfigure";
        return $::sth::sthCore::FAILURE;
    } else {
        ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
    }

    if { $listSbLoadProfileList != "" } {
        set sbLoadProfile [::sth::sthCore::invoke ::stc::get $headerToConfigure -affiliationstreamblockloadprofile-targets]
        ::sth::sthCore::log debug "$_procName: Calling stc::config $sbLoadProfile $listSbLoadProfileList"
        set cmdName_sbLoadProfile "::sth::sthCore::invoke ::stc::config $sbLoadProfile $listSbLoadProfileList"
        if {[catch {eval $cmdName_sbLoadProfile} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $sbLoadProfile Success. ";
        }
    }
    
    #US38931 support Frame threshold
    # DE17295 Failed to modify Frame threshold values
    if { $listThresholdList != "" && [info exists userArgsArray(port_handle)]} {
        ::sth::Traffic::configFrameThreshold
    }

    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::getOtherVlanCount {attrList} {
    upvar userArgsArray userArgsArray
    upvar prioritisedAttributeList prioritisedAttributeList
    #need to process the vlan_user_priority_other, vlan_cfi_other, vlan_id_other, vlan_tpid_other, the max is the vlans_other_count, and the others will be set to default value to make sure 
    #they have the same length
    #process vlan_id_other_mode, vlan_id_other_step, vlan_id_other_count, vlan_id_other_repeat and then get the longest length, and need to make sure the length should not longer than vlans_other_count
    array set retList {}
    array set defaultList { vlan_user_priority_other            0
                        vlan_cfi_other                      0
                        vlan_tpid_other                     33024
                        vlan_id_other                       100
                        vlan_id_other_mode                  "increment"
                        vlan_id_other_step                  1
                        vlan_id_other_count                 1
                        vlan_id_other_repeat                0
                        }
    set modifier_count 0
    set vlans_other_count 0
    #if no vlan outer and vlan outer is given, then should not create any other layer vlan
    set noOtherVlan 1
    set outerVlanAttrList "vlan_id_outer vlan_outer_cfi vlan_outer_user_priority vlan_outer_tpid"
    foreach ele $prioritisedAttributeList {
        set ele [lindex $ele 1]
        if {[lsearch $outerVlanAttrList $ele] > -1} {
            set noOtherVlan 0
        }
    }
    if {$noOtherVlan} {
        set ::sth::Traffic::listl2encap_OtherVlan {}
        set ::sth::Traffic::listl2OtherVlanRangeModifier {}
        set retList(vlan_count) $vlans_other_count
        set retList(vlan_modifier_count) $modifier_count
        return [array get retList]
    }
    foreach element [array names defaultList] {
        if {[info exists userArgsArray($element)]} {
            set count [llength $userArgsArray($element)]
            if {$element == "vlan_user_priority_other" || $element == "vlan_cfi_other" || $element == "vlan_tpid_other" || $element == "vlan_id_other"} {
                if {$count > $vlans_other_count} {
                    set vlans_other_count $count
                }
            } else {
                if {$count > $modifier_count} {
                    set modifier_count $count
                }
            }
        }
    }
    if {$modifier_count > $vlans_other_count} {
        set modifier_count $vlans_other_count
    }
    foreach element [array names defaultList] {
        if {[info exists userArgsArray($element)]} {
            set count [llength $userArgsArray($element)]
            if {$element == "vlan_user_priority_other" || $element == "vlan_cfi_other" || $element == "vlan_tpid_other" || $element == "vlan_id_other"} {
                #to make the length to be same
                for {set i $count} {$i < $vlans_other_count} {incr i} {
                    lappend userArgsArray($element) $defaultList($element)
                }
            } else {
                #to make the length to be same
                for {set i $count} {$i < $modifier_count} {incr i} {
                    lappend userArgsArray($element) $defaultList($element)
                }
            }
        }
    }
    
    set retList(vlan_count) $vlans_other_count
    set retList(vlan_modifier_count) $modifier_count
    return [array get retList]
}
# MOD by xiaozhi on 2011-07-28
# CR296037075: l3_length is not supposed to be the same as the L2 length.
# CR304842911: "-l3_length_max" and "-l3_length_min" are changed to l3 layer frame length specific.
proc ::sth::Traffic::processFrameLength { element l2Length} {
    
    upvar $l2Length l2FrameLength 
    upvar userArgsArray userArgsArray
    upvar prioritisedAttributeList prioritisedAttributeList
    upvar mns mns
    
    variable arrayHeaderLists
    variable listl2encap_OuterVlan
    variable listl2encap_OtherVlan

    # EthernetII   18bytes
    # Vlan         4bytes
    # Vlan         4bytes
    # IPv4 header  20bytes
    # IPv6 header  40bytes
    # PPP          2 bytes
    # PPPoE        6 bytes
    # mpls         4 bytes
    
    set streamHld [set ::$mns\::handleCurrentStream]
    set l3FrameLength $userArgsArray($element)
    set l2FrameLength $l3FrameLength
        
    set l2EncapType ""
    catch {
        set l2EncapType [set ::$mns\::strHandlel2EncapMap($streamHld)]
        set headerSet [set ::$mns\::arrayHeaderLists($l2EncapType)]

        switch -- $l2EncapType {
            "ethernet_ii" {
                set l2FrameLength [expr $l3FrameLength+18]
            }
            "ethernet_ii_vlan" {
                if {$userArgsArray(mode) == "create"} {
                    if {[llength $listl2encap_OuterVlan] != 0} {
                        set l2FrameLength [expr $l3FrameLength+18+8]
                    } else {
                        set l2FrameLength [expr $l3FrameLength+18+4]
                    }
                    if {[llength $listl2encap_OtherVlan] != 0} {
                        # check how many vlan layers
                        array set retVal [getOtherVlanCount [set ::$mns\::listl2encap_OtherVlan]]
                        set vlanLayerCount $retVal(vlan_count)
                        set l2FrameLength [expr $l2FrameLength + 4*$vlanLayerCount]
                    }
                } elseif {$userArgsArray(mode) == "modify"} {
                    set objType [lindex $headerSet 0]
                    set ethHandle [::sth::sthCore::invoke ::stc::get $streamHld -children-$objType]
                    set vlansHandle [::sth::sthCore::invoke ::stc::get [lindex $ethHandle 0] -children-vlans]
                    set handleVlanList [::sth::sthCore::invoke ::stc::get $vlansHandle -children]
                    set l2FrameLength [expr $l3FrameLength+18+4*[llength $handleVlanList]]
                }
            }
            "ethernet_ii_pppoe" {
                set l2FrameLength [expr $l3FrameLength+18+2+6]
            }
            "ethernet_ii_vlan_pppoe" {
                set l2FrameLength [expr $l3FrameLength+18+2+6+4]
            }
            "ethernet_ii_qinq_pppoe" {
                set l2FrameLength [expr $l3FrameLength+18+2+6+8]
            }
            "ethernet_ii_vlan_mpls" {
                set l2FrameLength [expr $l3FrameLength+18+4+4]
            }
            "ethernet_ii_unicast_mpls" {
             if {[regexp "^\\s*\{" $userArgsArray(mpls_labels)]} {
                    set mpls_layer_count [llength $userArgsArray(mpls_labels)]
            } else {
                set mpls_layer_count 1
            }
                set l2FrameLength [expr $l3FrameLength+18+4*$mpls_layer_count]
            }
            default {
                
            }     
        }
    }
}

#MOD by Fei Cheng 08-09-27
proc ::sth::Traffic::processImixAttributes {} {
    
    set _procName "processImixAttributes";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set streamHld [set ::$mns\::handleCurrentStream];
    
    set name "custom"
    if {[info exists userArgsArray(l3_imix1_ratio)]} {
        set name $name$userArgsArray(l3_imix1_ratio)
        set name $name$userArgsArray(l3_imix1_size)
    }
    if {[info exists userArgsArray(l3_imix2_ratio)]} {
        set name $name$userArgsArray(l3_imix2_ratio)
        set name $name$userArgsArray(l3_imix2_size)
    }
    if {[info exists userArgsArray(l3_imix3_ratio)]} {
        set name $name$userArgsArray(l3_imix2_ratio)
        set name $name$userArgsArray(l3_imix2_size)
    }

    set flds [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) -children-FrameLengthDistribution]
    foreach fld $flds {
       set fldname  [::sth::sthCore::invoke stc::get $fld -name]
       if {$fldname == $name} {
           set exist_fld $fld
           break
       }
    }
    if {[info exists exist_fld]} {
       ::sth::sthCore::invoke stc::config $streamHld "-AffiliationFrameLengthDistribution-targets $exist_fld"
        return ::sth::sthCore::SUCCESS;
    }
    
    set fld [::sth::sthCore::invoke stc::get $streamHld -AffiliationFrameLengthDistribution]
    if {$fld != ""} {
        ::sth::sthCore::invoke stc::config $streamHld "-AffiliationFrameLengthDistribution-targets \"\""
    }
        
    set fld [::sth::sthCore::invoke stc::create FrameLengthDistribution -under $::sth::sthCore::GBLHNDMAP(project) "-AffiliationFrameLengthDistributionStreamBlock $streamHld -name $name"]
    
    if {[info exists userArgsArray(l3_imix1_ratio)]} {
       #puts [stc::get $fld]
       #the framelengthdistributionslot1 is auto created, config it directly
        set framelengthdistributionslot1 [lindex [::sth::sthCore::invoke stc::get $fld -children-framelengthdistributionslot] 0]
        ## when the streamblock -length_mode is imix , the sum of the packet length at least is 60,the length of the link layer is 14, so 60-14=46
        if {$userArgsArray(l3_imix1_size) < 46} {
            ::sth::sthCore::invoke stc::config $framelengthdistributionslot1 "-FixedFrameLength 46 -Weight $userArgsArray(l3_imix1_ratio)"
        } else {
            ::sth::sthCore::invoke stc::config $framelengthdistributionslot1 "-FixedFrameLength $userArgsArray(l3_imix1_size) -Weight $userArgsArray(l3_imix1_ratio)"
        }
    }
    ## when the streamblock -length_mode is imix , the sum of the packet length at least is 60,the length of the link layer is 14, so 60-14=46
    if {[info exists userArgsArray(l3_imix2_ratio)]} {
        if {$userArgsArray(l3_imix2_size) < 46} {
            ::sth::sthCore::invoke stc::create framelengthdistributionslot -under $fld "-FixedFrameLength 46 -Weight $userArgsArray(l3_imix2_ratio)"
        } else {
            ::sth::sthCore::invoke stc::create framelengthdistributionslot -under $fld "-FixedFrameLength $userArgsArray(l3_imix2_size) -Weight $userArgsArray(l3_imix2_ratio)"
        }
    }
    ## when the streamblock -length_mode is imix , the sum of the packet length at least is 60,the length of the link layer is 14, so 60-14=46
    if {[info exists userArgsArray(l3_imix3_ratio)]} {
        if {$userArgsArray(l3_imix3_size) < 46} {
            ::sth::sthCore::invoke stc::create framelengthdistributionslot -under $fld "-FixedFrameLength 46 -Weight $userArgsArray(l3_imix3_ratio)"
        } else {
            ::sth::sthCore::invoke stc::create framelengthdistributionslot -under $fld "-FixedFrameLength $userArgsArray(l3_imix3_size) -Weight $userArgsArray(l3_imix3_ratio)"
        }
    }
    ## when the streamblock -length_mode is imix , the sum of the packet length at least is 60,the length of the link layer is 14, so 60-14=46
     if {[info exists userArgsArray(l3_imix4_ratio)]} {
        if {$userArgsArray(l3_imix4_size) < 46} {
            ::sth::sthCore::invoke stc::create framelengthdistributionslot -under $fld "-FixedFrameLength 46 -Weight $userArgsArray(l3_imix4_ratio)"
        } else {
            ::sth::sthCore::invoke stc::create framelengthdistributionslot -under $fld "-FixedFrameLength $userArgsArray(l3_imix4_size) -Weight $userArgsArray(l3_imix4_ratio)"
        }
    }
    #puts [stc::get $fld]
    
    return ::sth::sthCore::SUCCESS;
}



#create custom header with the parameter
proc ::sth::Traffic::processCreateCustomHeader {customName mode} {
    
    set _procName "processCreateCustomHeader";
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    set existHdl 0;

    #get handle of streamblock
    set sbHandle [set ::$mns\::handleCurrentStream]

    if {$mode == "create"} {
        foreach element $prioritisedAttributeList {
            foreach {prio Name} $element {
                lappend sName $Name                              
            }
        }

        if {[regexp "l2_encap" $sName]!=1 && [regexp "l3_protocol" $sName]!=1 } {
            #clear encapsulation if both of l2 and l3 encap were not specified in API
            if {[catch {::sth::sthCore::invoke ::stc::config $sbHandle -frameconfig ""} retHandle]} {
                ::sth::sthCore::log debug "$_procName: stc::config frameconfig error: $retHandle"
            } else {
                ::sth::sthCore::log info "$_procName: stc::config frameconfig successfully.";
            }
            #config allow_invalid_header before adding custom header
            if {[catch {::sth::sthCore::invoke stc::config $sbHandle "-AllowInvalidHeaders True"} retHandle]} {
                return $::sth::sthCore::FAILURE;
            } else {
                ::sth::sthCore::log info "$_procName: stc::config is successful. Handle is $retHandle";
            }
        }

        #add custom header
        if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under $sbHandle "-pattern $userArgsArray($customName) -name $customName"} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create add custom successfully. Handle is $retHandle";
        }

    } else {
        set retHandle [::sth::sthCore::invoke stc::get $sbHandle "-children-custom:Custom"]
        foreach headerHandle $retHandle {
            set headerName [::sth::sthCore::invoke stc::get $headerHandle -name];
            if {[regexp $customName $headerName]} {
                if {[catch {::sth::sthCore::invoke stc::config $headerHandle "-pattern $userArgsArray($customName)"} err]} {
                        ::sth::sthCore::processError returnKeyedList "$_procName: stc::config Fail: $err"
                        return -code error $returnKeyedList
                }
                set existHdl 1
                break
            }
        }
        if {$existHdl == 0} {
            if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under $sbHandle "-pattern $userArgsArray($customName) -name $customName"} retHandle]} {
                return $::sth::sthCore::FAILURE
            } else {
               ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle"
            }
        }
    }   
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processCreateL2Encap {super_proc} {
    # NOTE:
    # If the l2_encap = ethernet_ii_vlan, then this is the object hierarchy:
    # streamBlock --> ethernet header --> vlansList --> vlan
    # A dirty(but quick) solution for creating mpls header as of now (as there is only one attribute from the user).
    # Will revisit this later. 
    
    set _procName "processCreateL2Encap";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar x directional;
    
    variable arrayHeaderLists;
    variable l2EncapType;
   
    
    set headerSet $arrayHeaderLists($l2EncapType);
    array set headerArray $headerSet;
    set listHeadersToCreate [array names headerArray];
    set createdHeaders {};
    set handleEthHeader "";
    set mpls_layer_count 0
    set vlans_other_count 0
    ##puts "[array statistics headerArray]"
    
    # headerSet is now a pair of header name and the corresponding lists. 
    foreach {headerToCreate listsToUse} $headerSet {
        set headerTag "";
        #set List $headerArray($headerToCreate);
        #process the listsToUse
        #listl2encap_OuterVlan listl2encap_Vlan listInnerl2encap_OuterVlan listInnerl2encap_Vlan
        #listl2encap_EthernetII listInnerl2encap_EthernetII
        #if here need to create the inner ether header of the vxlan, need to use the
        #listInnerl2encap_EthernetII
        set listsToUse_new ""
        if {[regexp -nocase vxlan $super_proc]} {
            # for the ethernet and the vlan, need to use the inner list
            foreach List $listsToUse {
                if {[regexp -nocase inner $List] && ([regexp -nocase EthernetII $List] || [regexp -nocase vlan $List])} {
                    lappend listsToUse_new $List
                }
            }
            set l2_encap_type inner_l2_encap
        } else {
            foreach List $listsToUse {
                if {![regexp -nocase inner $List]} {
                    lappend listsToUse_new $List
                }
            }
            set l2_encap_type l2_encap
        }
        set listsToUse $listsToUse_new
        foreach List $listsToUse {
            set listArgsList {};
            array set listArgsListArray {};
            
            if {[llength [set ::$mns\::$List]] != 0 || $headerToCreate == "ethernet:EthernetII" || $headerToCreate == "ethernet:Ethernet8022" || $headerToCreate == "ethernet:EthernetSnap" || $headerToCreate == "ethernet:Ethernet8023Raw"} {
                
                if {[regexp "OtherVlan" $List]} {
                    array set ret_value [::sth::Traffic::getOtherVlanCount [set ::$mns\::$List]]
                    set vlans_other_count $ret_value(vlan_count)
                    foreach element [set ::$mns\::$List] {
                        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
                        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
                        for {set i 0} {$i < $vlans_other_count} {incr i} {
                            if {![info exists listArgsListArray([expr $i + 3])]} {
                                set listArgsListArray([expr $i + 3]) {}
                            }
                            if {$element == "vlan_user_priority_other"} {
                                set decimalPriority [lindex $userArgsArray($element) $i]
                                set binaryPriority $::sth::Traffic::arrayDecimal2Bin($decimalPriority);
                                #vlan pri is a 3 bit string, so should cut this 4 bit string to 3 by remove first bit
                                regsub -all {^\d} $binaryPriority "" binaryPriority
                                lappend listArgsListArray([expr $i + 3]) -$stcAttr $binaryPriority;
                                
                            } elseif {$element == "vlan_tpid_other"} {
                                set tpid_value [format "%x" [lindex $userArgsArray($element) $i]]
                                lappend listArgsListArray([expr $i + 3]) -$stcAttr $tpid_value;
                            } else {
                                lappend listArgsListArray([expr $i + 3]) -$stcAttr [lindex $userArgsArray($element) $i];
                            }
                        }
                    }
                } else {
                    foreach element [set ::$mns\::$List] {
                        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
                        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
                        
                        if {$element == "vlan_user_priority" || $element == "vlan_outer_user_priority" || $element == "inner_vlan_user_priority" || $element == "inner_vlan_outer_user_priority"} {
                            set decimalPriority $userArgsArray($element);
                            if {[llength $decimalPriority] > 1} {
                                set decimalPriority [lindex $decimalPriority 0]
                            }
                            set binaryPriority $::sth::Traffic::arrayDecimal2Bin($decimalPriority);
                            
                            #vlan pri is a 3 bit string, so should cut this 4 bit string to 3 by remove first bit
                            regsub -all {^\d} $binaryPriority "" binaryPriority
                            
                            lappend listArgsList -$stcAttr $binaryPriority;
                            continue;
                        }
                        if {$element == "vpi"} {
                           lappend listVpiArgsList -$stcAttr $userArgsArray($element);
                            continue;
                        }
                        if {$element == "vci"} {
                           lappend listVciArgsList -$stcAttr $userArgsArray($element);
                            continue;
                        }
                        
                        if {$headerToCreate == "ethernet:EthernetSnap"} {
                            #the default value of llc header and snap header in 802.3 snap header
                            set listdefaultLlcList "-dsap AA -ssap AA -control 03"
                            set headerList "ipx_header xns_header appletalk_header aarp_header decnet_header vines_header"
                            if {[info exists userArgsArray(snap_oui_id)]} {
                                set snaporgcode $userArgsArray(snap_oui_id)
                            } else {
                                set snaporgcode 000000
                            }
                            #set the snap header value
                            if {[string match -nocase "snap_*" $element]} {
                                 lappend listSnapArgsList -$stcAttr $userArgsArray($element);
                                continue;
                            }
                            #get the EtherType in snap header by the custom header type
                            switch -regexp $element {
                                "ipx" {
                                    set listdefaultSnapList "-orgcode $snaporgcode -EthernetType 8137"
                                    set customerType ipx
                                }
                                "appletalk" {
                                    set listdefaultSnapList "-orgcode $snaporgcode -EthernetType 809B"
                                    set customerType appletalk
                                }
                                "aarp" {
                                    set listdefaultSnapList "-orgcode $snaporgcode -EthernetType 80F3"
                                    set customerType aarp
                                }
                                "decnet" {
                                    set listdefaultSnapList "-orgcode $snaporgcode -EthernetType 6003"
                                    set customerType decnet
                                }
                                "vines" {
                                    set listdefaultSnapList "-orgcode $snaporgcode -EthernetType 0BAD"
                                    set customerType vines
                                }
                                "xns" {
                                    set listdefaultSnapList "-orgcode $snaporgcode -EthernetType 0807"
                                    set customerType xns
                                }
                            }
                            #set the llc header value
                            if {[string match -nocase "llc_*" $element]} {
                                lappend listLlcArgsList -$stcAttr $userArgsArray($element);
                                continue;
                            }
                            #set the custom header value
                            if {[regexp "_header" $element]} {
                                foreach headerelement $headerList {
                                    if {[string match -nocase $headerelement $element]} {
                                        #check if only one kind of header exists
                                        foreach headerelement_check $headerList {
                                            if {($headerelement_check != $headerelement) && [info exists userArgsArray($headerelement_check)]} {
                                                ::sth::sthCore::processError returnKeyedList "$headerList headers are mutually exclusive."
                                                return -code error $returnKeyedList 
                                            }  
                                        }
                                        lappend listCustomHeaderList -$stcAttr $userArgsArray($element);
                                        break;
                                    }
                                }
                                continue;
                            }
                           
                            
                        } elseif {$headerToCreate != "ethernet:EthernetSnap"} {
                            if {[string match -nocase "llc_*" $element]} {
                                lappend listLlcArgsList -$stcAttr $userArgsArray($element);
                                continue;
                            }
                            
                            if {[string match -nocase "ipx_header" $element]} {
                                if {[info exists userArgsArray(xns_header)]} {
                                    ::sth::sthCore::processError returnKeyedList "IPX and XNS headers are mutually exclusive."
                                    return -code error $returnKeyedList 
                                }
                                lappend listCustomHeaderList -$stcAttr $userArgsArray($element);
                                set customerType "ipx"
                                set listdefaultLlcList "-dsap E0 -ssap E0"
                                continue;
                            }
                            
                            if {[string match -nocase "xns_header" $element]} {
                                if {[info exists userArgsArray(ipx_header)]} {
                                    ::sth::sthCore::processError returnKeyedList "IPX and XNS headers are mutually exclusive."
                                    return -code error $returnKeyedList 
                                }
                                lappend listCustomHeaderList -$stcAttr $userArgsArray($element);
                                set customerType "xns"
                                set listdefaultLlcList "-dsap 80 -ssap 80"
                                continue;
                            }
                        }
                        if {$headerToCreate == "fc:FcSofEof"} {
                            set tableName "::$mns\::traffic_config_$element\_fwdmap"
                            set elementVal [set $tableName\($userArgsArray($element))];
                            lappend listArgsList -$stcAttr $elementVal;
                            continue;
                        }
                        
                        if {[regexp Mpls $headerToCreate]} {
                            set i 1
                            if {[regexp "^\\s*\{" $userArgsArray($element)]} {
                                set mpls_layer_count [llength $userArgsArray($element)]
                                for {set i 1} {$i<=$mpls_layer_count} {incr i} {
                                    set mpls_listArgsList$i {}
                                    if {![info exists userArgsArray(mpls_bottom_stack_bit)]} {
                                        lappend listArgsList$i -sBit 1
                                    }
                                    if {[llength $userArgsArray($element)] >1 } {
                                        lappend listArgsList$i -$stcAttr [lindex [lindex $userArgsArray($element) [expr $i-1]] 0]
                                    } else {
                                        lappend listArgsList$i -$stcAttr [lindex $userArgsArray($element) 0]
                                    }
                                }
                                continue;
                            } else {
                                if {![info exists userArgsArray(mpls_bottom_stack_bit)]} {
                                    lappend listArgsList$i -sBit 1
                                }
                                if {[llength $userArgsArray($element)] >1 } {
                                    lappend listArgsList$i -$stcAttr [lindex $userArgsArray($element) 0]
                                } else {
                                    lappend listArgsList$i -$stcAttr $userArgsArray($element)
                                }
                                continue;
                            }
                        }
                        if {($element == "vlan_tpid") || ($element == "vlan_outer_tpid")} {
                            set tpid_value [format "%x" $userArgsArray($element)]
                            lappend listArgsList -$stcAttr $tpid_value;
                        } else {
                            lappend listArgsList -$stcAttr $userArgsArray($element);
                        }
                    }
                }
                set headerSet [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
                array set arrayHeadersUnderStream $headerSet;
                
                if {[info exists arrayHeadersUnderStream($l2_encap_type)]} {
                    
                    ####################################
                    # Modify L2 encap
                    ####################################
                    # this is mode modify. And this l2_encap was created earlier
                    
                    set listL2HeadersUnderStream $arrayHeadersUnderStream($l2_encap_type);
                    array set arrayL2HeadersUnderStream $listL2HeadersUnderStream;
                    
                    # block the next codes to extend to support Ethernet8022  
                    ##set headerToConfigure $arrayL2HeadersUnderStream([lindex [split $headerToCreate :] 1])
                    ###the headname will be changed after the stc::apply. so we reget the object here
                    #regsub -all {\d+$} $headerToConfigure "" objectName
                    
                    set streamHandle [set ::$mns\::handleCurrentStream]
                    set objectName $headerToCreate
                    
                    if {[regexp -nocase vlan $objectName]} {
                        set headerToConfigure $arrayL2HeadersUnderStream([lindex [split $headerToCreate :] 1])
                        regsub -all {\d+$} $headerToConfigure "" objectName
                        
                        set headerlist [set ::$mns\::arrayHeaderLists($userArgsArray($l2_encap_type))]
                        set l2Header [lindex $headerlist 0]
                        #set ethHandle [::stc::get $streamHandle -children-ethernet:EthernetII]
                        #if there is vxlan configured in the streamblock, then there will be more than one ethernet header
                        set ethHandle [::sth::sthCore::invoke ::stc::get $streamHandle -children-$l2Header]
                        if {[regexp "inner" $l2_encap_type]} {
                            set ethHandle [lindex $ethHandle 1]
                        } else {
                            set ethHandle [lindex $ethHandle 0]
                        }
                        set handleVlanList [::sth::sthCore::invoke ::stc::get $ethHandle -children-vlans]
                        set headerToConfigure [::sth::sthCore::invoke ::stc::get $handleVlanList -children-$objectName]
                        #at most there will be 4: listl2encap_OuterVlan listl2encap_Vlan listInnerl2encap_OuterVlan listInnerl2encap_Vlan
                        set noOfVlanId [llength $listsToUse]
                        set noOfVlanHandles [llength $headerToConfigure]
                        
                        if {$noOfVlanHandles <= 1 && [regexp "Outer|OtherVlan" $List]} {
                            #check if there is reange modifier under the inner vlan, it can be the modifier for the id or the pri
                            set vlan_name [::sth::sthCore::invoke stc::get [lindex $headerToConfigure 0] -name]
                            set ether_name [::sth::sthCore::invoke stc::get $ethHandle -name]
                            set idOffsetReference "$ether_name.vlans.$vlan_name.id"
                            set priOffsetReference "$ether_name.vlans.$vlan_name.pri"
                            set rangeList_random [::sth::sthCore::invoke stc::get $streamHandle -children-randomModifier]
                            set rangeList_range [::sth::sthCore::invoke stc::get $streamHandle -children-rangeModifier]
                            set rangeList_table [::sth::sthCore::invoke stc::get $streamHandle -children-tableModifier]
                            foreach Obj [concat $rangeList_random $rangeList_range $rangeList_table] {
                                set ref [::sth::sthCore::invoke stc::get $Obj -OffsetReference]
                                if { $ref == $idOffsetReference } {
                                    set innerIdModifierHandle $Obj
                                }
                                if { $ref == $priOffsetReference } {
                                    set innerPriModifierHandle $Obj
                                }
                            }
                            
                            #create the outer vlan
                            set handleVlan $handleVlanList  
                            ::sth::sthCore::log debug "$_procName: Calling stc::create vlan $handleVlan"
                            set cmdName "::sth::sthCore::invoke ::stc::create vlan -under $handleVlan";
                            if {[catch {eval $cmdName} retHandle]} {
                                    return $::sth::sthCore::FAILURE;
                            } else {
                                set handleOuterVlanHeader $retHandle;
                                lappend headerToConfigure $retHandle;
                                set element "vlan_outer_user_priority"
                            }
                        }
                        
                        if {$noOfVlanHandles <= 2 && [regexp "OtherVlan" $List]} {
                            #check if there is reange modifier under the outer vlan(2nd vlan), it can be the modifier for the id
                            set vlan_name [::sth::sthCore::invoke stc::get [lindex $headerToConfigure 0] -name]
                            set ether_name [::sth::sthCore::invoke stc::get $ethHandle -name]
                            set idOffsetReference "$ether_name.vlans.$vlan_name.id"
                            set rangeList_random [::sth::sthCore::invoke stc::get $streamHandle -children-randomModifier]
                            set rangeList_range [::sth::sthCore::invoke stc::get $streamHandle -children-rangeModifier]
                            set rangeList_table [::sth::sthCore::invoke stc::get $streamHandle -children-tableModifier]
                            foreach Obj [concat $rangeList_random $rangeList_range $rangeList_table] {
                                set ref [::sth::sthCore::invoke stc::get $Obj -OffsetReference]
                                if { $ref == $idOffsetReference } {
                                    set outerIdModifierHandle $Obj
                                    break
                                }
                            }
                            
                            #need to create the other vlan
                            set handleVlan $handleVlanList  
                            
                            set handleOtherVlanHeader {}
                            for {set i [expr $vlans_other_count + 2]} {$i >= 3} {incr i -1} {
                                ::sth::sthCore::log debug "$_procName: Calling stc::createvlan $handleVlan"
                                set cmdName "::sth::sthCore::invoke ::stc::create vlan -under $handleVlan";
                                if {[catch {eval $cmdName} retHandle]} {
                                    return $::sth::sthCore::FAILURE;
                                } else {
                                    lappend handleOtherVlanHeader $retHandle;
                                    lappend headerToConfigure $retHandle
                                }
                            }
                            set retHandle $handleOtherVlanHeader
                        }
                        
                        #if there is qinq
                        if {[llength $headerToConfigure] >1} {
                            if {[regexp "OtherVlan" $List]} {
                                set handleOtherVlanHeader {}
                                set headerToConfigure [lrange $headerToConfigure 0 [expr {[llength $headerToConfigure] - 3}]]
                                set handleOtherVlanHeader $headerToConfigure
                            } elseif {[regexp "OuterVlan" $List]} {
                               set headerToConfigure [lindex $headerToConfigure [expr {[llength $headerToConfigure] - 2}]]
                               set handleOuterVlanHeader $headerToConfigure
                               if {[info exists outerIdModifierHandle]} {
                                    #change the offset refference name for id
                                    set vlan_name [::sth::sthCore::invoke stc::get $handleOuterVlanHeader -name]
                                    set idOffsetReference "$ether_name.vlans.$vlan_name.id"
                                    ::sth::sthCore::invoke stc::config $outerIdModifierHandle -OffsetReference $idOffsetReference
                                }
                            } else {
                                set headerToConfigure [lindex $headerToConfigure [expr {[llength $headerToConfigure] - 1}]]
                                set handleVlanHeader $headerToConfigure
                                if {[info exists innerPriModifierHandle]} {
                                    #change the offset refference name for pri
                                    set vlan_name [::sth::sthCore::invoke stc::get $handleVlanHeader -name]
                                    set priOffsetReference "$ether_name.vlans.$vlan_name.id"
                                    ::sth::sthCore::invoke stc::config $innerPriModifierHandle -OffsetReference $priOffsetReference
                                }
                                if {[info exists innerIdModifierHandle]} {
                                    #change the offset refference name for id
                                    set vlan_name [::sth::sthCore::invoke stc::get $handleVlanHeader -name]
                                    set idOffsetReference "$ether_name.vlans.$vlan_name.id"
                                    ::sth::sthCore::invoke stc::config $innerIdModifierHandle -OffsetReference $idOffsetReference
                                }
                            }
                        } else {
                            set handleVlanHeader $headerToConfigure
                        }
                    } else {
                        set headerToConfigure [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
                        if {[regexp -nocase mpls $objectName]} {
                            set handleMplsHeader $headerToConfigure;
                        }
                        if {[regexp -nocase ethernet:EthernetII $objectName]} {
                            #when vxlan is configured there will be two object
                            if {[regexp "inner" $l2_encap_type]} {
                                set headerToConfigure [lindex $headerToConfigure 1]
                            } else {
                                set headerToConfigure [lindex $headerToConfigure 0]
                            }
                            set handleEthHeader $headerToConfigure
                        }  
                    }
                    
                    if {[regexp -nocase atm $objectName]} {
                        ####################################
                        # Modify ATM header
                        ####################################
                        #modify the vci first
                        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listVciArgsList"
                        set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listVciArgsList"
                        if {[catch {eval $cmdName} retHandle]} {
                            #puts "error while configuring $headerToConfigure";
                            return $::sth::sthCore::FAILURE;
                        } else {
                            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
                            set retHandle $headerToConfigure;
                        }
                        
                        set handleAtmHeader $headerToConfigure;
                        #then modify the vpi
                        
                        set vpiHandle [::sth::sthCore::invoke stc::get $headerToConfigure -children-vpi]
                        set uniHandle [::sth::sthCore::invoke stc::get $vpiHandle -children-UNI]
                        
                        set cmdName "::sth::sthCore::invoke ::stc::config $uniHandle $listVpiArgsList"
                        if {[catch {eval $cmdName} retHandle]} {
                            #puts "error while configuring $vpiHandle";
                            return $::sth::sthCore::FAILURE;
                        } else {
                            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
                            set retHandle $vpiHandle;
                        }
                    } elseif {[regexp -nocase "ethernet:ethernet8022" $headerToConfigure] || [regexp -nocase "ethernet:EthernetSnap" $headerToConfigure]} {   
                        #################################################
                        # Modify Ethernet 8022 header or 8023 snap header
                        #################################################
                        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
                        if {[catch {::sth::sthCore::invoke stc::config $headerToConfigure $listArgsList} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::config Fail: $err"
                                return -code error $returnKeyedList
                        }
                        if {[info exists listLlcArgsList]} {
                            if {[catch {set llcheader [::sth::sthCore::invoke stc::get $headerToConfigure "-children-llcheader"]} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                            if {[catch {::sth::sthCore::invoke stc::config $llcheader $listLlcArgsList} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                        }
                        # modify customer header for ipx or xns
                        if {[info exists listCustomHeaderList]} {
                            if {[catch {set headerList [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] "-children"]} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                            
                            ######################################
                            ##### delete ip headers first    #####
                            ######################################
                            foreach head $headerList {    
                                if {![regexp -nocase "ethernet:ethernet8022" $head] && ![regexp -nocase "custom:custom" $head] && ![regexp -nocase "ethernet:EthernetSnap" $head] } {
                                    if {[catch {::sth::sthCore::invoke stc::delete $head} err]} {
                                        ::sth::sthCore::processError returnKeyedList "$_procName: stc::delete Fail: $err"
                                        return -code error $returnKeyedList 
                                    }
                                } 
                            }
                            
                            if {![regexp -nocase "custom:Custom" $headerList]} {
                                if {[catch {::sth::sthCore::invoke stc::create custom:Custom  -under [set ::$mns\::handleCurrentStream] "$listCustomHeaderList -name $customerType"} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                    return -code error $returnKeyedList 
                                }
                            } else {
                                set index [lsearch -regexp $headerList "custom:custom" ]
                                set customHeader [lindex $headerList $index]
                                if {[catch {::sth::sthCore::invoke stc::config $customHeader "$listCustomHeaderList -name $customerType"} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                    return -code error $returnKeyedList 
                                }
                            }
                            
                            # auto change the value of dsap and ssap
                            if {[info exists llcheader]} {
                                if {[catch {::sth::sthCore::invoke stc::config $llcheader $listdefaultLlcList} err]} {
                                        ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                        return -code error $returnKeyedList 
                                }
                }
                        }
                        #specially handling for snap header in 8023 snap
                        if {[regexp -nocase "ethernet:EthernetSnap" $headerToConfigure]} {
                            #get snap header, the snapheader must exist in EthernetSnap header
                            if {[catch {set snapheader [::sth::sthCore::invoke stc::get $headerToConfigure "-children-snapheader"]} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::get Fail: $err"
                                    return -code error $returnKeyedList 
                            }
                            if {![info exists snapheader]} {
                                 ::sth::sthCore::log error "$_procName: $headerToConfigure -children-snapheader should have snapheader returned"
                                return $::sth::sthCore::FAILURE;
                            }
                            if {[info exists listCustomHeaderList]} {
                                #auto change the value of ethertype in snap header
                                if {[catch {::sth::sthCore::invoke stc::config $snapheader $listdefaultSnapList} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::config Fail: $err"
                                    return -code error $returnKeyedList
                                }
                            } elseif {[info exists listSnapArgsList]} {
                                #delete the custom header if it is created in create mode
                                if {[catch {set headerList [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children]} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::get Fail: $err"
                                    return -code error $returnKeyedList 
                                }
                                foreach head $headerList {
                                    if {[regexp -nocase "custom:custom" $head]} {
                                        if {[catch {::sth::sthCore::invoke stc::delete $head} err]} {
                                            ::sth::sthCore::processError returnKeyedList "$_procName: stc::delete Fail: $err"
                                            return -code error $returnKeyedList 
                                        }
                                    }
                                }
                                
                                if {[catch {::sth::sthCore::invoke stc::config $snapheader $listSnapArgsList} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                    return -code error $returnKeyedList 
                                }
                            } 
                        }
                    } else {
                        if {[regexp "OtherVlan" $List]} {
                            foreach listArgsListIndex [array names listArgsListArray] {
                                set headerToConfigure [lindex $handleOtherVlanHeader [expr {[llength $handleOtherVlanHeader] - $listArgsListIndex +2}]]
                                set listArgsList $listArgsListArray($listArgsListIndex)
                                ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
                                set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList"
                                if {[catch {eval $cmdName} retHandle]} {
                                    #puts "error while configuring $headerToConfigure";
                                    return $::sth::sthCore::FAILURE;
                                } else {
                                   ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
                                   set retHandle $headerToConfigure;
                                }
                            }
                        } else {
                            ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
                            set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList"
                            if {[catch {eval $cmdName} retHandle]} {
                                #puts "error while configuring $headerToConfigure";
                                return $::sth::sthCore::FAILURE;
                            } else {
                               ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
                               set retHandle $headerToConfigure;
                            }
                        }
                    }

                } else {
                    
                    ####################################
                    # create L2 encap
                    ####################################
                    # this is:
                    # either mode create.
                    # or mode modify. And this l2_encap was NOT created earlier
                    
                    if {[regexp Vlan $headerToCreate]} {
                        ####################################
                        # create Vlan header
                        ####################################
                        
                        # First check if Vlans exist under the eth header.
                        # If it does, then use that handle to add more vlans under eth.
                        
                        if {[catch {::sth::sthCore::invoke ::stc::get $handleEthHeader -children} handleVlanList]} {
                            ::sth::sthCore::log error "$_procName: $handleEthHeader -children $handleVlanList ";
                            return $::sth::sthCore::FAILURE;
                        } else {
                            ::sth::sthCore::log info "$_procName: $handleEthHeader -children $handleVlanList ";
                        }
                        
                        if {[llength $handleVlanList] == 0 || [lsearch -regexp $handleVlanList "vlans"] < 0} {
                            ::sth::sthCore::log debug "$_procName: Calling stc::createvlans $handleEthHeader $listArgsList"
                            if {[catch {::sth::sthCore::invoke ::stc::create vlans -under $handleEthHeader} handleVlanList]} {
                                return $::sth::sthCore::FAILURE;
                            } else {
                                ::sth::sthCore::log info "$_procName: stc::create Success. vlans handle is $handleVlanList";
                            }
                        }
                        
                        #get the vlan handles excluding llcheader in 8022 or 8023 snap header
                        foreach handleVlan $handleVlanList {
                            if {[regexp -nocase "vlan" $handleVlan]} {
                                #process the other layer vlan
                                if {[regexp "OtherVlan" $List]} {
                                    #$listArgsListArray
                                    set handleOtherVlanHeader {}
                                    for {set i [expr $vlans_other_count + 2]} {$i >= 3} {incr i -1} {
                                        ::sth::sthCore::log debug "$_procName: Calling stc::createvlan $handleVlan $listArgsListArray($i)"
                                        set cmdName "::sth::sthCore::invoke ::stc::create vlan -under $handleVlan $listArgsListArray($i)";
                                        if {[catch {eval $cmdName} retHandle]} {
                                            return $::sth::sthCore::FAILURE;
                                        } else {
                                            lappend handleOtherVlanHeader $retHandle;
                                        }
                                    }
                                    set retHandle $handleOtherVlanHeader
                                    continue
                                }
                                ::sth::sthCore::log debug "$_procName: Calling stc::createvlan $handleVlan $listArgsList"
                                set cmdName "::sth::sthCore::invoke ::stc::create vlan -under $handleVlan $listArgsList";
                                if {[catch {eval $cmdName} retHandle]} {
                                    return $::sth::sthCore::FAILURE;
                                } else {
                                    if {[regexp Outer $List]} {
                                        set handleOuterVlanHeader $retHandle;
                                        if {[regexp -nocase "inner" $l2_encap_type]} {
                                            set element "inner_vlan_outer_user_priority"
                                        } else {
                                            set element "vlan_outer_user_priority"
                                        }
                                    } else {
                                        set handleVlanHeader $retHandle;
                                        if {[regexp -nocase "inner" $l2_encap_type]} {
                                            set element "inner_vlan_user_priority"
                                        } else {
                                            set element "vlan_user_priority"
                                        }
                                    }
                                }
                            }
                        }
                        
                        ####################################
                        # Modifier for vlan/qinq priority
                        ####################################
                        if {![regexp "OtherVlan" $List]} {
                            if {[info exists userArgsArray($element)]} {
                                set decimalPriority $userArgsArray($element);
                                set valueList {}
                                if {[llength $decimalPriority] > 1} {
                                    foreach value $decimalPriority {
                                       lappend valueList $::sth::Traffic::arrayDecimal2Bin($value)
                                    }
                                
                                    set listArgsList {};
                                    if {[catch {::sth::sthCore::invoke ::stc::get $retHandle -name} vlanHeaderName]} {
                                        ::sth::sthCore::log error "$_procName: $retHandle -name $vlanHeaderName";
                                        return -code 1 -errorcode -1 $vlanHeaderName;
                                    } else {
                                        ::sth::sthCore::log info "$_procName: $retHandle -name $vlanHeaderName ";
                                    }
                                    set ethName [::sth::sthCore::invoke stc::get $handleEthHeader -name]
                                    lappend listArgsList -OffsetReference "$ethName\.vlans.$vlanHeaderName.pri" -Data $valueList -EnableStream $::sth::Traffic::enableStream;
                        
                                    set cmdName "::sth::sthCore::invoke ::stc::create TableModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
                                    if {[catch {eval $cmdName} vlanModifierHandle]} {
                                        return $::sth::sthCore::FAILURE;
                                    } else {
                                        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $vlanModifierHandle";
                                    }
                                }
                            }
                        }
                    } elseif {[regexp atm $headerToCreate]} {
                        ####################################
                        # create ATM header
                        ####################################
                        set extEncapType [set ::$mns\::l2EncapType]
                        #comment out by Nana, since VC_MULTIPLEXED and  LLC_ENCAPSULATED are not the Attributes of ATM object,
                        # mey be they are Attribute of Aal5 object.now we just commet out the code to make sure vpi and vci can be configured.
                        #If there is requirement for the LLC_ENCAPSULATED, should look again this part of code.
                        #if {$extEncapType == "atm_vc_mux"} {
                        #    lappend listVciArgsList "-VcEncapsulation VC_MULTIPLEXED"
                        #} elseif {$extEncapType == "atm_llcsnap"} {
                        #    lappend listVciArgsList "-VcEncapsulation LLC_ENCAPSULATED"
                        #}
                        
                        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listVciArgsList"
                        set cmdName "::sth::sthCore::invoke ::stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listVciArgsList";
                        if {[catch {eval $cmdName} retHandle]} {
                            return $::sth::sthCore::FAILURE;
                        } else {
                        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                        }
                        set handleAtmHeader $retHandle;
                        
                        #puts [stc::get $handleAtmHeader]
                        
                        set cmdName "::sth::sthCore::invoke ::stc::create vpi -under $handleAtmHeader"
                        if {[catch {eval $cmdName} vpiHandle]} {
                            return $::sth::sthCore::FAILURE;
                        } else {
                        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $vpiHandle";
                        }
                        
                        set cmdName "::sth::sthCore::invoke ::stc::create UNI -under $vpiHandle"
                        if {[catch {eval $cmdName} uniHandle]} {
                            return $::sth::sthCore::FAILURE;
                        } else {
                           ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $uniHandle";
                        }
                        
                        set cmdName "::sth::sthCore::invoke ::stc::config $uniHandle $listVpiArgsList"
                        if {[catch {eval $cmdName} err]} {
                            return $::sth::sthCore::FAILURE;
                        } else {
                           ::sth::sthCore::log info "$_procName: $cmdName Success";
                        }
                        
                    }  elseif {[regexp mpls $headerToCreate]} {
                        ####################################
                        # create MPLS header
                        ####################################
                        if {[regexp "^\\s*\{" $userArgsArray(mpls_labels)]} {
                            set mpls_layer_count [llength $userArgsArray(mpls_labels)]
                        } else {
                           set mpls_layer_count 1
                        }
                        for {set i 1} {$i<=$mpls_layer_count} {incr i} {
                            set listArgsList [set listArgsList$i]
                            ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listArgsList"
                            set cmdName "::sth::sthCore::invoke ::stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listArgsList";
                            if {[catch {eval $cmdName} retHandle]} {
                                return $::sth::sthCore::FAILURE;
                            } else {
                                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                            }
                            set handleMplsHeader $retHandle;
                        }
                        
                    } elseif {[regexp 8022 $headerToCreate] || [regexp Snap $headerToCreate]} {
                        ####################################
                        # create etherent 802.2 header or 802.3 snap header
                        ####################################
                        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listArgsList"
                        
                        if {[catch {::sth::sthCore::invoke stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listArgsList} retHandle]} {
                            ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $retHandle"
                            return -code error $returnKeyedList 
                        } else {
                            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                        }
                        
                        # create llc header by default
                        if {[catch {set llcheader [::sth::sthCore::invoke stc::create llcheader -under $retHandle]} err]} {
                            ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                            return -code error $returnKeyedList 
                        }
                        
                        if {[info exists listLlcArgsList]} {
                            if {[catch {::sth::sthCore::invoke stc::config $llcheader $listLlcArgsList} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                        }
                        # create customer header for ipx or xns (8022) or ipx, xns,appletalk,aarp,decnet,vines(8023 snap)
                        if {[info exists listCustomHeaderList]} {
                            if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "$listCustomHeaderList -name $customerType"} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                            # auto change the value of dsap and ssap
                            if {[catch {::sth::sthCore::invoke stc::config $llcheader $listdefaultLlcList} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                        }
                        
                        #specially handling for snap header in 8023 snap
                        if {[regexp Snap $headerToCreate]} {
                            #create snap header by default
                            if {[catch {set snapheader [::sth::sthCore::invoke stc::create snapheader -under $retHandle]} err]} {
                                ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                return -code error $returnKeyedList 
                            }
                            #auto change the valud of ethertype in snap header
                            if {[info exists listCustomHeaderList]} {
                                if {[catch {::sth::sthCore::invoke stc::config $snapheader $listdefaultSnapList} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::config Fail: $err"
                                    return -code error $returnKeyedList 
                                }
                            } elseif {[info exists listSnapArgsList]} {
                                if {[catch {::sth::sthCore::invoke stc::config $snapheader $listSnapArgsList} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::config Fail: $err"
                                    return -code error $returnKeyedList
                                }
                                # auto change the value of dsap and ssap
                                if {[catch {::sth::sthCore::invoke stc::config $llcheader $listdefaultLlcList} err]} {
                                    ::sth::sthCore::processError returnKeyedList "$_procName: stc::create Fail: $err"
                                    return -code error $returnKeyedList 
                                }
                            }
                        }
                        # Note: name to handleEthHeader is to handle vlan headers
                        set handleEthHeader $retHandle; 
                    } elseif {[regexp -nocase fc:fc $headerToCreate]} {
                        # First check if Fc/FcSofEof exist 
                        # If it does, then use that handle
                        if {[catch {::sth::sthCore::invoke ::stc::get [set ::$mns\::handleCurrentStream] -children-$headerToCreate} retHandle]} {
                            ::sth::sthCore::log error "$_procName: [set ::$mns\::handleCurrentStream] -children $headerToCreate ";
                            return $::sth::sthCore::FAILURE;
                        } else {
                            ::sth::sthCore::log info "$_procName: [set ::$mns\::handleCurrentStream] -children $listArgsList ";
                            sth::sthCore::invoke stc::config $retHandle $listArgsList 
                        }
                    } else {
                        ####################################
                        # create Ethernet header
                        ####################################
                        # this is eth header
                        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listArgsList"
                        set cmdName "::sth::sthCore::invoke ::stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listArgsList";
                        if {[catch {eval $cmdName} retHandle]} {
                            return $::sth::sthCore::FAILURE;
                        } else {
                        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                        }
                        set handleEthHeader $retHandle;
                    }
                    
                    set headerTag [lindex [split $List _] 1];
                    lappend createdHeaders $headerTag $retHandle;
                    
                }
            }
        }
    }
    
    set listOfHeaders {};
    if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
        set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
    }
        
    #lappend listOfHeaders "l2_encap";
    #lappend listOfHeaders "[set createdHeaders]";
    #add by cf. it seems will have problem if the createdHeaders is null,
    if {[set createdHeaders] != ""} {
        lappend listOfHeaders "$l2_encap_type";
        lappend listOfHeaders "[set createdHeaders]";
    }
    set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
    
    ## If mac_dst_mode is set to discovery, retrieve the port handle
    ## under which the stream under which the l2 header is created.
    ## Save the port handle for later ARP operation
    ##puts " userArgsArray(mac_dst_mode) = $userArgsArray(mac_dst_mode)"
    if {[info exists userArgsArray(mac_dst_mode)] } {
        set userValue $userArgsArray(mac_dst_mode);
        #    if { $userValue == "discovery" } {
        #        if {[catch {::sth::Traffic::processMacDstMode $retHandle userArgsArray} errMsg ]} {
        #            #::sth::sthCore::log error $errMsg
        #            return -code 1 -errorcode -1 $errMsg
        #        }
        #    }
    }
    
    # Check if modifier is needed here.
    # This is layer 2 header. So as of now taking care of src/dst mac
    if {($userArgsArray(mode) == "create" && $directional == 0) || $userArgsArray(mode) == "modify"} {
        if {[regexp -nocase "inner" $l2_encap_type]} {
            #create the modifier for the inner ethernet header
            set listInnerl2SrcRangeModifier [set ::$mns\::listInnerl2SrcRangeModifier]
            ::sth::sthCore::log debug "listInnerl2SrcRangeModifier = $listInnerl2SrcRangeModifier"
            
            if {[llength [set ::$mns\::listInnerl2SrcRangeModifier]]} {
                ::sth::Traffic::processCreateL2RangeModifier ethernet $handleEthHeader listInnerl2SrcRangeModifier srcMac;
            }
            
            set listInnerl2DstRangeModifier [set ::$mns\::listInnerl2DstRangeModifier]
            ::sth::sthCore::log debug "listInnerl2DstRangeModifier = $listInnerl2DstRangeModifier"
            
            if {[llength [set ::$mns\::listInnerl2DstRangeModifier]]} {
                ::sth::Traffic::processCreateL2RangeModifier ethernet $handleEthHeader listInnerl2DstRangeModifier dstMac;
            }
        } else {
            set listl2SrcRangeModifier [set ::$mns\::listl2SrcRangeModifier]
            ::sth::sthCore::log debug "listl2SrcRangeModifier = $listl2SrcRangeModifier"
            
            if {[llength [set ::$mns\::listl2SrcRangeModifier]]} {
                ::sth::Traffic::processCreateL2RangeModifier ethernet $handleEthHeader listl2SrcRangeModifier srcMac;
            }
        
            set listl2DstRangeModifier [set ::$mns\::listl2DstRangeModifier]
            ::sth::sthCore::log debug "listl2DstRangeModifier = $listl2DstRangeModifier"
            
            if {[llength [set ::$mns\::listl2DstRangeModifier]]} {
                ::sth::Traffic::processCreateL2RangeModifier ethernet $handleEthHeader listl2DstRangeModifier dstMac;
            }
        }
    } elseif {$userArgsArray(mode) == "create" && $directional == 1} {
            #added for mac_src2, mac_dst2 modifier in bidirectional traffic
            set listl2Src2RangeModifier [set ::$mns\::listl2Src2RangeModifier]
            ::sth::sthCore::log debug "listl2Src2RangeModifier = $listl2Src2RangeModifier"
        
            if {[llength [set ::$mns\::listl2Src2RangeModifier]]} {
                ::sth::Traffic::processCreateL2RangeModifier ethernet $handleEthHeader listl2Src2RangeModifier srcMac;
            }
        
            set listl2Dst2RangeModifier [set ::$mns\::listl2Dst2RangeModifier]
            ::sth::sthCore::log debug "listl2Dst2RangeModifier = $listl2Dst2RangeModifier"
        
            if {[llength [set ::$mns\::listl2Dst2RangeModifier]]} {
                ::sth::Traffic::processCreateL2RangeModifier ethernet $handleEthHeader listl2Dst2RangeModifier dstMac;
            }
    }
    
    set listl2VpiRangeModifier [set ::$mns\::listl2VpiRangeModifier]
    ::sth::sthCore::log debug "listl2VpiRangeModifier = $listl2VpiRangeModifier"
    
    if {[llength [set ::$mns\::listl2VpiRangeModifier]]} {
            
        ::sth::Traffic::processCreateL2RangeModifier vpi $handleAtmHeader listl2VpiRangeModifier vpi;
        
    }
    
    set listl2VciRangeModifier [set ::$mns\::listl2VciRangeModifier]
    ::sth::sthCore::log debug "listl2VpiRangeModifier = $listl2VpiRangeModifier"
    
    if {[llength [set ::$mns\::listl2VciRangeModifier]]} {
            
        ::sth::Traffic::processCreateL2RangeModifier vci $handleAtmHeader listl2VciRangeModifier vci;
        
    }
    
    
    if {[regexp -nocase "inner" $l2_encap_type]} {
        set listInnerl2VlanRangeModifier [set ::$mns\::listInnerl2VlanRangeModifier]
        ::sth::sthCore::log debug "listInnerl2VlanRangeModifier = $listInnerl2VlanRangeModifier"
        if {[llength [set ::$mns\::listInnerl2VlanRangeModifier]]} {
            ::sth::Traffic::processCreateL2RangeModifier vlan $handleVlanHeader listInnerl2VlanRangeModifier id;
        }
    
        set listInnerl2VlanPriorityRangeModifier [set ::$mns\::listInnerl2VlanPriorityRangeModifier]
        ::sth::sthCore::log debug "listInnerl2VlanPriorityRangeModifier = $listInnerl2VlanPriorityRangeModifier"
        
        if {[llength [set ::$mns\::listInnerl2VlanPriorityRangeModifier]]} {
            ::sth::Traffic::processCreateL2RangeModifier vlan $handleVlanHeader listInnerl2VlanPriorityRangeModifier pri;
        }
    
        set listInnerl2OuterVlanRangeModifier [set ::$mns\::listInnerl2OuterVlanRangeModifier]
        ::sth::sthCore::log debug "listInnerl2OuterVlanRangeModifier = $listInnerl2OuterVlanRangeModifier"
        
        if {[llength [set ::$mns\::listInnerl2OuterVlanRangeModifier]]} {
           ::sth::Traffic::processCreateL2RangeModifier vlan $handleOuterVlanHeader listInnerl2OuterVlanRangeModifier id;
        }
    } else {
        set listl2VlanRangeModifier [set ::$mns\::listl2VlanRangeModifier]
        ::sth::sthCore::log debug "listl2VlanRangeModifier = $listl2VlanRangeModifier"
        if {[llength [set ::$mns\::listl2VlanRangeModifier]]} {
            ::sth::Traffic::processCreateL2RangeModifier vlan $handleVlanHeader listl2VlanRangeModifier id;
        }
    
        set listl2VlanPriorityRangeModifier [set ::$mns\::listl2VlanPriorityRangeModifier]
        ::sth::sthCore::log debug "listl2VlanPriorityRangeModifier = $listl2VlanPriorityRangeModifier"
        
        if {[llength [set ::$mns\::listl2VlanPriorityRangeModifier]]} {
            ::sth::Traffic::processCreateL2RangeModifier vlan $handleVlanHeader listl2VlanPriorityRangeModifier pri;
        }
    
        set listl2OuterVlanRangeModifier [set ::$mns\::listl2OuterVlanRangeModifier]
        ::sth::sthCore::log debug "listl2OuterVlanRangeModifier = $listl2OuterVlanRangeModifier"
        
        if {[llength [set ::$mns\::listl2OuterVlanRangeModifier]]} {
           ::sth::Traffic::processCreateL2RangeModifier vlan $handleOuterVlanHeader listl2OuterVlanRangeModifier id;
        }
        
        set listl2OtherVlanRangeModifier [set ::$mns\::listl2OtherVlanRangeModifier]
        ::sth::sthCore::log debug "listl2OtherVlanRangeModifier = $listl2OtherVlanRangeModifier"
        
        if {[llength [set ::$mns\::listl2OtherVlanRangeModifier]]} {
            set vlanNum [llength $handleOtherVlanHeader]
            set handleOtherVlanHeaderNew ""
            for {set i [expr $vlanNum - 1]} {$i >=0} {incr i -1} {
                lappend handleOtherVlanHeaderNew [lindex $handleOtherVlanHeader $i]
            }
           ::sth::Traffic::processCreateL2RangeModifier vlan $handleOtherVlanHeaderNew listl2OtherVlanRangeModifier id;
        }
    }
    
    if {$mpls_layer_count>0} {
        set streamHandle [set ::$mns\::handleCurrentStream]
        set mpls_header [::sth::sthCore::invoke ::stc::get $streamHandle -children-mpls:Mpls]
        for {set i 1} {$i<=$mpls_layer_count} {incr i} {
            set handleMplsHeader [lindex $mpls_header [expr $i-1]]
            if {$mpls_layer_count>1} {
                set mpls_labels_value [lindex $userArgsArray(mpls_labels) [expr $i-1]]
            } else {
                set mpls_labels_value  $userArgsArray(mpls_labels) 
            }
            if {[info exists ::$mns\::listMplsLabelModifier$i]} {
                if {[llength [set ::$mns\::listMplsLabelModifier$i]]} { 
                    if {[info exists ::$mns\::listMplsLabelRangeModifier$i]} {
                        if {[llength [set ::$mns\::listMplsLabelRangeModifier$i]]} {
                            set listMplsLabelRangeModifier$i [set ::$mns\::listMplsLabelRangeModifier$i];
                            ::sth::Traffic::processCreateL2RangeModifier mpls_labels $handleMplsHeader listMplsLabelRangeModifier$i label;
                        }
                    } else {
                        #dis active range modifier if exsist
                        if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_labels)] } {
                            ::sth::Traffic::processDisActiveRangeModifier mpls_labels $handleMplsHeader label; 
                        }
            
                    }
                
                    if {[info exists ::$mns\::listMplsLabelTableModifier$i]} {
                        if {[llength [set ::$mns\::listMplsLabelTableModifier$i]]} {
                            if {[info exists userArgsArray(mpls_labels_mode)]} {
                                set MplsLabelModeValue [lindex $userArgsArray(mpls_labels_mode) [expr $i-1]]
                            } else {
                                set MplsLabelModeValue "list"
                            }
                            if {$MplsLabelModeValue == "fixed"} {
                                #dis active table modifier if exsist
                                if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_labels)]} {
                                    ::sth::Traffic::processDisActiveTableModifier mpls_labels $handleMplsHeader label;
                                }
                                ::sth::sthCore::log info "$_procName: no need to call mpls label modifier for mpls header. ";
                            } else {
                                # TODO: put a catch here later
                                ::sth::Traffic::processCreateL2TableModifier mpls_labels $handleMplsHeader $mpls_labels_value label;
                            }
                        }
                    } else {
                        #dis active table modifier if exsist
                        if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_labels)]} {
                            ::sth::Traffic::processDisActiveTableModifier mpls_labels $handleMplsHeader label;
                        }
                    }
                }
            } else {
                #disactive both range and table modifier if exsist
                if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_labels)]} {
                    ::sth::Traffic::processDisActiveRangeModifier mpls_labels $handleMplsHeader label;
                    ::sth::Traffic::processDisActiveTableModifier mpls_labels $handleMplsHeader label;
                }    
            }
        }
    }
    if {$mpls_layer_count>0} {
        set streamHandle [set ::$mns\::handleCurrentStream]
        set mpls_header [::sth::sthCore::invoke ::stc::get $streamHandle -children-mpls:Mpls]
        for {set i 1} {$i<=$mpls_layer_count} {incr i} {
            set handleMplsHeader [lindex $mpls_header [expr $i-1]]
            if {[info exists userArgsArray(mpls_cos)]} {
                set mpls_cos_value [lindex $userArgsArray(mpls_cos) [expr $i-1]]
                if {[info exists ::$mns\::listMplsCosModifier$i]} {
                    if {[llength [set ::$mns\::listMplsCosModifier$i]]} {
                        if {[info exists ::$mns\::listMplsCosRangeModifier$i]} {
                            if {[llength [set ::$mns\::listMplsCosRangeModifier$i]]} {
                                set listMplsCosRangeModifier$i [set ::$mns\::listMplsCosRangeModifier$i];
                                ::sth::Traffic::processCreateL2RangeModifier mpls_cos $handleMplsHeader listMplsCosRangeModifier$i exp;
                            }
                        } else {
                            #dis active range modifier if exsist
                            if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_cos)] } {
                                ::sth::Traffic::processDisActiveRangeModifier mpls_cos $handleMplsHeader exp; 
                            }
            
                        }
                        if {[info exists ::$mns\::listMplsCosTableModifier$i]} {
                            if {[llength [set ::$mns\::listMplsCosTableModifier$i]]} {  
                                set MplsCosModeValue [lindex $userArgsArray(mpls_cos_mode) [expr $i-1]];
                                if {$MplsCosModeValue == "fixed"} {
                                    #dis active table modifier if exsist
                                    if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_cos)]} {
                                        ::sth::Traffic::processDisActiveTableModifier mpls_cos $handleMplsHeader exp;
                                    }
                                    ::sth::sthCore::log info "$_procName: no need to call mpls cos modifier for mpls header. ";
                                } else {
                                    # TODO: put a catch here later
                                    ::sth::Traffic::processCreateL2TableModifier mpls_cos $handleMplsHeader $mpls_cos_value exp;
                                }
                            }
                        } else {
                            #dis active table modifier if exsist
                            if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_cos)]} {
                                ::sth::Traffic::processDisActiveTableModifier mpls_cos $handleMplsHeader exp;
                            }
                        }
                    }
                } else {
                    #disactive both range and table modifier if exsist
                    if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_cos)]} {
                        ::sth::Traffic::processDisActiveRangeModifier mpls_cos $handleMplsHeader exp;
                        ::sth::Traffic::processDisActiveTableModifier mpls_cos $handleMplsHeader exp;
                    }
                }
            }
        }
    }
    if {$mpls_layer_count>0} {
        set streamHandle [set ::$mns\::handleCurrentStream]
        set mpls_header [::sth::sthCore::invoke ::stc::get $streamHandle -children-mpls:Mpls]
        for {set i 1} {$i<=$mpls_layer_count} {incr i} {
            set handleMplsHeader [lindex $mpls_header [expr $i-1]]
            if {[info exists userArgsArray(mpls_ttl)]} {
                set mpls_ttl_value [lindex $userArgsArray(mpls_ttl) [expr $i-1]]
                if {[info exists ::$mns\::listMplsTtlModifier$i]} {
                    if {[llength [set ::$mns\::listMplsTtlModifier$i]]} {
                        if {[info exists ::$mns\::listMplsTtlRangeModifier$i]} {
                            if {[llength [set ::$mns\::listMplsTtlRangeModifier$i]]} {
                                set listMplsTtlRangeModifier$i [set ::$mns\::listMplsTtlRangeModifier$i];
                                ::sth::Traffic::processCreateL2RangeModifier mpls_ttl $handleMplsHeader listMplsTtlRangeModifier$i ttl;
                            }
                        } else {
                            #dis active range modifier if exsist
                            if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_ttl)] } {
                                ::sth::Traffic::processDisActiveRangeModifier mpls_ttl $handleMplsHeader ttl; 
                            }
            
                        }
                        if {[info exists ::$mns\::listMplsTtlTableModifier$i]} {
                            if {[llength [set ::$mns\::listMplsTtlTableModifier$i]]} {  
                                set MplsTtlModeValue [lindex $userArgsArray(mpls_ttl_mode) [expr $i-1]];
                                if {$MplsTtlModeValue == "fixed"} {
                                    #dis active table modifier if exsist
                                    if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_ttl)]} {
                                        ::sth::Traffic::processDisActiveTableModifier mpls_ttl $handleMplsHeader ttl;
                                    }
                                    ::sth::sthCore::log info "$_procName: no need to call mpls ttl modifier for mpls header. ";
                                } else {
                                # TODO: put a catch here later
                                    ::sth::Traffic::processCreateL2TableModifier mpls_ttl $handleMplsHeader $mpls_ttl_value ttl;
                                }
                            }
                        } else {
                            #dis active table modifier if exsist
                            if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_ttl)]} {
                                ::sth::Traffic::processDisActiveTableModifier mpls_ttl $handleMplsHeader ttl;
                            }
                        }
                    }
                } else {
                    #disactive both range and table modifier if exsist
                    if {$userArgsArray(mode) == "modify" && [info exists userArgsArray(mpls_ttl)]} {
                        ::sth::Traffic::processDisActiveRangeModifier mpls_ttl $handleMplsHeader ttl;
                        ::sth::Traffic::processDisActiveTableModifier mpls_ttl $handleMplsHeader ttl;
                    }
                }
            }
        }
    }
    
    #process the custom_llc header after l2encap is configured
    if {[info exist userArgsArray(custom_llc)]} {
        ::sth::Traffic::processCreateCustomHeader custom_llc $userArgsArray(mode)
    }
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processCreatePppoxDhcpEncap {iteration} {
   
    set _procName "processCreatePppoxDhcpEncap";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    variable arrayHeaderLists;
    variable l2EncapType;
    
    # Just to avoid a lot of code changes at the moment.
    set ::sth::Traffic::handleTxStream $::sth::Traffic::handleCurrentStream;

    set pppox_link_true 0
    set dhcp_link_true 0
    if {[info exists userArgsArray(ppp_link)] && $userArgsArray(ppp_link) == "1"} { set pppox_link_true 1 }
    if {[info exists userArgsArray(dhcp_link)] && $userArgsArray(dhcp_link) == "1"} { set dhcp_link_true 1 }

    # If this is not access, do nothing and return
    if {! (([info exists userArgsArray(l2_encap)] && [regexp pppoe $userArgsArray(l2_encap)] && [info exists userArgsArray(ppp_session_id)]) || $pppox_link_true || $dhcp_link_true)} { return }

    # change for bi-dir traffic:
    if {$pppox_link_true == 1 && [info exists userArgsArray(bidirectional)]} {
        if {[info exists userArgsArray(ppp_link_traffic_src_list)] || [info exists userArgsArray(downstream_traffic_src_list)]} {
        # src or dst exits. Check if both exist
        if {[info exists userArgsArray(ppp_link_traffic_src_list)] && [info exists userArgsArray(downstream_traffic_src_list)]} {
            # both exist so they can be swapped.
            
        } else {
            ##puts "both src and dst should exist for bidirectional traffic";
            set errMsg "For bidirectional ppp traffic both upstream and downstream information should be provided"
            return -code 1 -errorcode -1 $errMsg;
        }
    }
    }
    # Error out if both the pppox|dhcp down stream or up stream are specified
    if {([info exists userArgsArray(ppp_link)] && $userArgsArray(ppp_link) == "1") && [info exists userArgsArray(ppp_link_traffic_src_list)] && ([info exists userArgsArray(dhcp_link)] && $userArgsArray(dhcp_link) == "1") && [info exists userArgsArray(dhcp_upstream)]} {
        set errMsg "The parameters -ppp_link_traffic_src_list and -dhcp_upstream are mutually exclusive."
        ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. Msg: $errMsg";
        ::sth::sthCore::processError trafficKeyedList $errMsg;
        return -code 1 -errorcode -1 $errMsg;
    }
    if {([info exists userArgsArray(ppp_link)] && $userArgsArray(ppp_link) == "1") && [info exists userArgsArray(downstream_traffic_src_list)] && ([info exists userArgsArray(dhcp_link)] && $userArgsArray(dhcp_link) == "1") && [info exists userArgsArray(dhcp_downstream)]} {
        set errMsg "The parameters -downstream_traffic_src_list and -dhcp_downstream are mutually exclusive."
        ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. Msg: $errMsg";
        ::sth::sthCore::processError trafficKeyedList $errMsg;
        return -code 1 -errorcode -1 $errMsg;
    }

    # PPP session ID case
    if {[info exists userArgsArray(ppp_session_id)]} {
        # Check that ppp_link is 0
        if {[info exists userArgsArray(ppp_link)] && $userArgsArray(ppp_link) != "0"} {
            set errMsg "The parameter -ppp_link must be 0 when -ppp_session_id is specified."
            ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
        if {[info exists userArgsArray(ppp_link_traffic_src_list)] && ([info exists userArgsArray(ppp_link)] && $userArgsArray(ppp_link) == "1")} {
            set errMsg "The parameters -ppp_link_traffic_src_list and -ppp_session_id are mutually exclusive."
            ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
        # Can consider changing this to allow only one IPs and MAC address
        # tied to each PPP session ID, but right now we allow for testing
        # purposes 
    }
    
    set pppox_src_ipv4if_list {}; set pppox_dst_ipv4if_list {}; set tmpIpv4IfList_pppox_forUpstream {}; set tmpIpv4IfList_pppox_forDownstream {}
    set dhcp_dst_ipv4if_list {}; set dhcp_src_ipv4if_list {}; set tmpIpv4IfList_dhcp_forUpstream {}; set tmpIpv4IfList_dhcp_forDownstream {}

    if {$pppox_link_true || $dhcp_link_true} {
        foreach proto_cur [list pppox dhcp] {
            set upstream_param_name ppp_link_traffic_src_list
            set downstream_param_name downstream_traffic_src_list
            if {[regexp $proto_cur dhcp]} {
                set upstream_param_name dhcp_upstream
                set downstream_param_name dhcp_downstream
            }
            if {[info exists userArgsArray($upstream_param_name)] && [set ${proto_cur}_link_true]} {
                foreach us_traffic_src_list_element [set userArgsArray($upstream_param_name)] {
                    if {[regexp $proto_cur pppox]} {
                        set ${proto_cur}clientblock_src_related_ifs [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $us_traffic_src_list_element "-children-Pppoeclientblockconfig"] -usesif-Targets]
                    } else {
                        set ${proto_cur}clientblock_src_related_ifs [::sth::sthCore::invoke stc::get $us_traffic_src_list_element -usesif-Targets]
                    }
                    if {[set ${proto_cur}clientblock_src_related_ifs] == ""} {
                        set errMsg "No PPPoE configuration exists on host [set userArgsArray($upstream_param_name)]"
                        ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. No PPPoE Client Block config exists on host [set userArgsArray($upstream_param_name)]. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg;
                    }
                    set ${proto_cur}_src_ipif [lindex [set ${proto_cur}clientblock_src_related_ifs] [lsearch -regexp [set ${proto_cur}clientblock_src_related_ifs] ipv4if]]
                    # if ipv4if is empty then check ipv6if
                    if {[set ${proto_cur}_src_ipif] == ""} {
                        set ${proto_cur}_src_ipif [lindex [set ${proto_cur}clientblock_src_related_ifs] [lsearch -regexp [set ${proto_cur}clientblock_src_related_ifs] ipv6if]]
                    }
                    if {[set ${proto_cur}_src_ipif] == ""} {
                        set errMsg "No IPIf exists on host $us_traffic_src_list_element"
                        ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. No IPv4IF is related to [string toupper $proto_cur] Client Block config (upstream) on host $us_traffic_src_list_element. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg;
                    }
                    lappend ${proto_cur}_src_ipv4if_list [set ${proto_cur}_src_ipif] 
                    if {[regexp $proto_cur dhcp]} {
                        if {[info exists userArgsArray(mac_discovery_gw)]} {
                            if {[catch {::sth::sthCore::invoke stc::config [set ${proto_cur}_src_ipif] [list -Gateway $userArgsArray(mac_discovery_gw) -ResolveGatewayMac TRUE]} retHandle]} {
                                set errMsg "Error configuring IPv4If [set ${proto_cur}_src_ipif] with gateway $userArgsArray(mac_dst)"
                                ::sth::sthCore::log debug "Error in sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. No PPPoE Client Block config exists on host [set userArgsArray($upstream_param_name)]. Msg: $errMsg";
                                ::sth::sthCore::processError trafficKeyedList $errMsg;
                                return -code 1 -errorcode -1 $retHandle;
                            }
                        } elseif {[info exists userArgsArray(mac_dst)]} {
                            if {[catch {::sth::sthCore::invoke stc::config [set ${proto_cur}_src_ipv4if] [list -GatewayMAC $userArgsArray(mac_dst) -ResolveGatewayMac FALSE]} retHandle]} {
                                set errMsg "Error configuring IPv4If [set ${proto_cur}_src_ipv4if] with gateway $userArgsArray(mac_dst)"
                                ::sth::sthCore::log debug "Error in sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. No PPPoE Client Block config exists on host [set userArgsArray($upstream_param_name)]. Msg: $errMsg";
                                ::sth::sthCore::processError trafficKeyedList $errMsg;
                                return -code 1 -errorcode -1 $retHandle;
                            }
                        } else {
                            # Default gateway will be used
                        }
                    }
                }
                
                if {! [info exists userArgsArray($downstream_param_name)] && [set ${proto_cur}_link_true]} {
                set tmpDevCount 1
                set mac_dst_count 1
                set ip_dst_count 1
                foreach param {mac_dst_count ip_dst_count} {
                    if {[info exists userArgsArray($param)]} {
                        set $param [set userArgsArray($param)]
                        if {[set userArgsArray($param)] > $tmpDevCount} { set tmpDevCount [set userArgsArray($param)] }
                    }
                }

                # Create Host
                if {[catch {set tmpHost [::sth::sthCore::invoke stc::create Host -under $::sth::sthCore::GBLHNDMAP(project) "-DeviceCount $tmpDevCount"]} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the Host for the static IP dst address. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
            }
                if {[catch {::sth::sthCore::invoke stc::config $tmpHost "-AffiliationPort-targets $userArgsArray(port_handle)"} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while setting the AffiliationPort-Targets to $userArgsArray(port_handle). Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }

                # Create EthIIIf

                # EthIIIf - mac_dst
                set tmpethlist {}

                if {[catch {set tmpEthiiIf [::sth::sthCore::invoke stc::create ethiiif -under $tmpHost "$tmpethlist"]} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the EthIIIf for the static IP dst address. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }

                # Create Ipv4If

                    set tmpipv4list [list -PrefixLength 24 -AddrStepMask 255.255.255.255]
                set ip_dst_mode "increment"
                set ip_dst_addr 192.83.1.3
                set ip_dst_step 0.0.0.1
                foreach param {mode addr step} {
                    if {[info exists userArgsArray(ip_dst_${param})]} {
                        set ip_dst_${param} [set userArgsArray(ip_dst_${param})]
                    }
                }
                switch $ip_dst_mode {
                    "fixed" {
                        lappend tmpipv4list -Address $ip_dst_addr -AddrStep 0.0.0.0
                    }
                    "increment" {
                        lappend tmpipv4list -Address $ip_dst_addr -AddrStep $ip_dst_step
                    }
                    "decrement" {
                        if {[catch {::sth::Pppox::IncrIPv4 $ip_dst_addr $ip_dst_step -[expr $ip_dst_count-1]} tmpipv4addr]} {
                            set errMsg "Error in sth::traffic_config: invalid IPv4 addr for -ip_dst_addr ($ip_dst_addr). Err: $tmpipv4addr"
                            ::sth::sthCore::log debug $errMsg
                            return -code 1 -errorcode -1 $errMsg;
                        }
                        lappend tmpipv4list -Address $tmpipv4addr -AddrStep $ip_dst_step
                    }
                    "random" {
                        # Random actually means shuffle, not a literal random in the HLTAPI core implementation
                        set tmpipv4addrlist $ip_dst_addr
                        set cur_ip_dst_addr $ip_dst_addr
                        for {set idx 0} {$idx < [expr $ip_dst_count - 1]} {incr idx} {
                            if {[catch {::Pppox::IncrIPv4 $cur_ip_dst_addr $ip_dst_step} cur_ip_dst_addr]} {
                                set errMsg "Error in sth::traffic_config: invalid IPv4 addr for -ip_dst_addr ($ip_dst_addr). Err: $tmpipv4addr"
                                ::sth::sthCore::log debug $errMsg
                                return -code 1 -errorcode -1 $errMsg;
                            }
                            lappend tmpipv4addrlist $cur_ip_dst_addr
                            set cur_ip_dst_addr $cur_ip_dst_addr
                        }
                        set randipv4addrlist {}
                        while {[llength $randipv4addrlist] < [llength $tmpipv4addrlist]} {
                            set cur_addr [lindex $tmpipv4addrlist [expr {int(rand()*[llength $tmpipv4addrlist])}]]
                            if {[lsearch $randipv4addrlist $cur_addr] < 0} {
                                lappend randipv4addrlist $cur_addr
                            }
                        }
                        lappend tmpipv4list -isRange FALSE -AddrList $randipv4addrlist
                    }
                    default {
                        set errMsg "Error in sth::traffic_config: unrecognized value for ip_dst_mode \"$userArgsArray(ip_dst_mode)\".  Valid values are fixed|increment|decrement|random."
                        ::sth::sthCore::log debug $errMsg
                        return -code 1 -errorcode -1 $errMsg;
                    }
                }

                if {[catch {set tmpIpv4If_${proto_cur}_forUpstream [::sth::sthCore::invoke stc::create ipv4if -under $tmpHost "$tmpipv4list"]} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the IPv4If for the static IP dst address. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }
                    if {[catch {::sth::sthCore::invoke stc::config $tmpHost "-TopLevelIf-targets [set tmpIpv4If_${proto_cur}_forUpstream]"} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while setting the TopLevelIf-targets for $tmpHost to [set tmpIpv4If_${proto_cur}_forUpstream]. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                } 
                    if {[catch {::sth::sthCore::invoke stc::config $tmpHost "-PrimaryIf-targets [set tmpIpv4If_${proto_cur}_forUpstream]"} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while setting the PrimaryIf-targets for $tmpHost to [set tmpIpv4If_${proto_cur}_forUpstream]. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
            }
                    if {[catch {::sth::sthCore::invoke stc::config [set tmpIpv4If_${proto_cur}_forUpstream] "-StackedOnEndpoint-targets $tmpEthiiIf"} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the IPv4If and EthIIIf. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
        }

                # Set the Source binding targets
                    for {set idx 0} {$idx < [llength [set userArgsArray($upstream_param_name)]]} {incr idx} {
                        lappend tmpIpv4IfList_${proto_cur}_forUpstream [set tmpIpv4If_${proto_cur}_forUpstream]
                }
            }
        }
            if {[info exists userArgsArray($downstream_param_name)] && [set ${proto_cur}_link_true]} {
                foreach ds_traffic_src_list_element [set userArgsArray($downstream_param_name)] {
                    if {[regexp $proto_cur pppox]} {
                        set ${proto_cur}clientblock_dst_related_ifs [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $ds_traffic_src_list_element "-children-pPpoeclientblockconfig"] -usesif-Targets]
                    } else {
                        set ${proto_cur}clientblock_dst_related_ifs [::sth::sthCore::invoke stc::get $ds_traffic_src_list_element -usesif-Targets]
                    }
                    if {[set ${proto_cur}clientblock_dst_related_ifs] == ""} {
                        set errMsg "No [string toupper $proto_cur] configuration exists on host $ds_traffic_src_list_element"
                        ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. No [string toupper $proto_cur] Client Block config exists on host $ds_traffic_src_list_element. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
                    set ${proto_cur}_dst_ipif [lindex [set ${proto_cur}clientblock_dst_related_ifs] [lsearch -regexp [set ${proto_cur}clientblock_dst_related_ifs] ipv4if]]
                    #if ipv4if is empty, check the ipv6if
                    if {[set ${proto_cur}_dst_ipif] == ""} {
                        set ${proto_cur}_dst_ipif [lindex [set ${proto_cur}clientblock_dst_related_ifs] [lsearch -regexp [set ${proto_cur}clientblock_dst_related_ifs] ipv6if]]
                    }
                    if {[set ${proto_cur}_dst_ipif] == ""} {
                        set errMsg "No IPIf exists on host $ds_traffic_src_list_element"
                        ::sth::sthCore::log debug "Error in ::sth::Traffic::processTrafficConfigModecreate: ::sth::Traffic::processCreatePppoxDhcpEncap FAILED. No IPv4IF is related to [string toupper $proto_cur] Client Block config (downstream) on host $ds_traffic_src_list_element. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg;
                    }
                    lappend ${proto_cur}_dst_ipv4if_list [set ${proto_cur}_dst_ipif]
            }
            #if {! [info exists userArgsArray(ppp_link_traffic_src_list)] && [info exists userArgsArray(ip_src_addr)]} {}
                if {! [info exists userArgsArray($upstream_param_name)]} {
                #if {! [info exists userArgsArray(mac_src)]} {
                        #    ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED. Please specify \"mac_src\".";
                #    ::sth::sthCore::processError trafficKeyedList $errMsg;
                #    return -code 1 -errorcode -1 $errMsg
                #}

                set tmpDevCount 1
                set mac_src_count 1
                set ip_src_count 1
                foreach param {mac_src_count ip_src_count} {
                    if {[info exists userArgsArray($param)]} {
                        set $param [set userArgsArray($param)]
                        if {[set userArgsArray($param)] > $tmpDevCount} { set tmpDevCount [set userArgsArray($param)] }
                    }
                }

                # Create Host
                if {[catch {set tmpHost [::sth::sthCore::invoke stc::create Host -under $::sth::sthCore::GBLHNDMAP(project) "-DeviceCount $tmpDevCount"]} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the Host for the static IP src address. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }
                if {[catch {::sth::sthCore::invoke stc::config $tmpHost "-AffiliationPort-targets $userArgsArray(port_handle)"} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while setting the AffiliationPort-Targets to $userArgsArray(port_handle). Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }

                # Create EthIIIf

                        # 4/3/07 - According to Davison and Hugh, the mac_discovery_gw should be used so we will change it here to ignore the mac_src, etc and use the mac_discovery_gw instead below
                set tmpethlist {}
                    if {! [info exists userArgsArray(mac_discovery_gw)]} {
                        # EthIIIf - mac_src
                set mac_src_mode "increment"
                set mac_src_addr 00:10:94:00:00:02
                set mac_src_step 00:00:00:00:00:01
                if {[info exists userArgsArray(mac_src)]} {
                    # convert mac_src
                            if {[::sth::Pppox::convertMacHltapi2Stc $userArgsArray(mac_src) mac_src_addr] != $::sth::sthCore::SUCCESS} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while converting MAC $userArgsArray(mac_src).";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                }
                # EthIIIf - mac_src_step
                if {[info exists userArgsArray(mac_src_step)]} {
                    # convert mac_src_step
                            if {[::sth::Pppox::convertMacHltapi2Stc $userArgsArray(mac_src) tmpmacsrcstep] != $::sth::sthCore::SUCCESS} {
                                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while converting MAC $userArgsArray(mac_src_step).";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                }
                foreach param {mode addr step} {
                    if {[info exists userArgsArray(mac_src_${param})]} {
                        set mac_src_${param} [set userArgsArray(mac_src_${param})]
                    }
                }
                switch $mac_src_mode {
                    "fixed" {
                        lappend tmpethlist -SourceMac $mac_src_addr -SrcMacStep 00:00:00:00:00:00
                    }
                    "increment" {
                        lappend tmpethlist -SourceMac $mac_src_addr -SrcMacStep $mac_src_step
                    }
                    "decrement" {
                        if {[catch {::sth::Pppox::MACIncr $mac_src_addr $mac_src_step -[expr $mac_src_count-1]} tmpmacaddr]} {
                            set errMsg "Error in sth::traffic_config: invalid MACaddr for -mac_src_addr ($mac_src_addr). Err: $tmpmacaddr"
                            ::sth::sthCore::log debug $errMsg
                    return -code 1 -errorcode -1 $errMsg;
            }
                        lappend tmpethlist -SourceMac $tmpmacaddr -SrcMacStep $mac_src_step
                    }
                    "random" {
                        # Random actually means shuffle, not a literal random in the HLTAPI core implementation
                        set tmpmacaddrlist $mac_src_addr
                        set cur_mac_src_addr $mac_src_addr
                        for {set idx 0} {$idx < [expr $mac_src_count - 1]} {incr idx} {
                            if {[catch {::sth::Pppox::MACIncr $cur_mac_src_addr $mac_src_step} cur_mac_src_addr]} {
                                set errMsg "Error in sth::traffic_config: invalid MAC addr for -mac_src_addr ($mac_src_addr). Err: $tmpmacaddr"
                                ::sth::sthCore::log debug $errMsg
                                return -code 1 -errorcode -1 $errMsg;
                            }
                            lappend tmpmacaddrlist $cur_mac_src_addr
                            set cur_mac_src_addr $cur_mac_src_addr
                        }
                        set randmacaddrlist {}
                        while {[llength $randmacaddrlist] < [llength $tmpmacaddrlist]} {
                            set cur_addr [lindex $tmpmacaddrlist [expr {int(rand()*[llength $tmpmacaddrlist])}]]
                            if {[lsearch $randmacaddrlist $cur_addr] < 0} {
                                lappend randmacaddrlist $cur_addr
                            }
                        }
                        lappend tmpethlist -isRange FALSE -SrcMacList $randmacaddrlist
                    }
                    default {
                        set errMsg "Error in sth::traffic_config: unrecognized value for mac_src_mode \"$userArgsArray(mac_src_mode)\". Valid values are fixed|increment|decrement|random."
                        ::sth::sthCore::log debug $errMsg
                        return -code 1 -errorcode -1 $errMsg;
                    }
                }
                    }
                if {[catch {set tmpEthiiIf [::sth::sthCore::invoke stc::create ethiiif -under $tmpHost "$tmpethlist"]} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the EthIIIf for the static IP src address. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }

                # Create Ipv4If

                    set tmpipv4list [list -PrefixLength 24 -AddrStepMask 255.255.255.255]

                    # 4/3/07 - According to Davison and Hugh, the mac_discovery_gw should be used so we will change it here to ignore the mac_src, etc and use the mac_discovery_gw instead below
                    # EthIIIf - mac_src_step
                    if {[info exists userArgsArray(mac_discovery_gw)]} {
                        lappend tmpipv4list -Gateway $userArgsArray(mac_discovery_gw) -ResolveGatewayMac true
                    }

                set ip_src_mode "increment"
                set ip_src_addr 192.83.1.3
                set ip_src_step 0.0.0.1
                foreach param {mode addr step} {
                    if {[info exists userArgsArray(ip_src_${param})]} {
                        set ip_src_${param} [set userArgsArray(ip_src_${param})]
                    }
                }
                switch $ip_src_mode {
                    "fixed" {
                        lappend tmpipv4list -Address $ip_src_addr -AddrStep 0.0.0.0
                    }
                    "increment" {
                        lappend tmpipv4list -Address $ip_src_addr -AddrStep $ip_src_step
                    }
                    "decrement" {
                        if {[catch {::sth::Pppox::IncrIPv4 $ip_src_addr $ip_src_step -[expr $ip_src_count-1]} tmpipv4addr]} {
                            set errMsg "Error in sth::traffic_config: invalid IPv4 addr for -ip_src_addr ($ip_src_addr). Err: $tmpipv4addr"
                            ::sth::sthCore::log debug $errMsg
                            return -code 1 -errorcode -1 $errMsg;
                        }
                        lappend tmpipv4list -Address $tmpipv4addr -AddrStep $ip_src_step
                    }
                    "random" {
                        # Random actually means shuffle, not a literal random in the HLTAPI core implementation
                        set tmpipv4addrlist $ip_src_addr
                        set cur_ip_src_addr $ip_src_addr
                        for {set idx 0} {$idx < [expr $ip_src_count - 1]} {incr idx} {
                            if {[catch {::sth::Pppox::IncrIPv4 $cur_ip_src_addr $ip_src_step} cur_ip_src_addr]} {
                                set errMsg "Error in sth::traffic_config: invalid IPv4 addr for -ip_src_addr ($ip_src_addr). Err: $tmpipv4addr"
                                ::sth::sthCore::log debug $errMsg
                                return -code 1 -errorcode -1 $errMsg;
                            }
                            lappend tmpipv4addrlist $cur_ip_src_addr
                            set cur_ip_src_addr $cur_ip_src_addr
                        }
                        set randipv4addrlist {}
                        while {[llength $randipv4addrlist] < [llength $tmpipv4addrlist]} {
                            set cur_addr [lindex $tmpipv4addrlist [expr {int(rand()*[llength $tmpipv4addrlist])}]]
                            if {[lsearch $randipv4addrlist $cur_addr] < 0} {
                                lappend randipv4addrlist $cur_addr
                            }
                        }
                        lappend tmpipv4list -isRange FALSE -AddrList $randipv4addrlist
                    }
                    default {
                        set errMsg "Error in sth::traffic_config: unrecognized value for ip_src_mode \"$userArgsArray(ip_src_mode)\".  Valid values are fixed|increment|decrement|random."
                        ::sth::sthCore::log debug $errMsg
                        return -code 1 -errorcode -1 $errMsg;
                    }
                }
                # mac_dst
                if {[info exists userArgsArray(mac_dst)]} {
                    # convert mac_dst
                        if {[::sth::Pppox::convertMacHltapi2Stc $userArgsArray(mac_dst) mac_dst_addr] != $::sth::sthCore::SUCCESS} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while converting MAC $userArgsArray(mac_dst).";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                    lappend tmpipv4list -ResolveGatewayMac false -GatewayMac $mac_dst_addr
                }
                    if {[catch {set tmpIpv4If_${proto_cur}_forDownstream [::sth::sthCore::invoke stc::create ipv4if -under $tmpHost "$tmpipv4list"]} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the IPv4If for the static IP src address. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }
                    if {[catch {::sth::sthCore::invoke stc::config $tmpHost "-TopLevelIf-targets [set tmpIpv4If_${proto_cur}_forDownstream]"} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while setting the TopLevelIf-targets for $tmpHost to [set tmpIpv4If_${proto_cur}_forDownstream]. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }
                    if {[catch {::sth::sthCore::invoke stc::config $tmpHost "-PrimaryIf-targets [set tmpIpv4If_${proto_cur}_forDownstream]"} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while setting the PrimaryIf-targets for $tmpHost to [set tmpIpv4If_${proto_cur}_forDownstream]. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }
                    if {[catch {::sth::sthCore::invoke stc::config [set tmpIpv4If_${proto_cur}_forDownstream] "-StackedOnEndpoint-targets $tmpEthiiIf"} errMsg]} {
                            ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the IPv4If and EthIIIf. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg
                }


                # Create VLAN If
                if {([info exists userArgsArray(l2_encap)] && [regexp vlan $userArgsArray(l2_encap)])
                  || ([info exists userArgsArray(l2_encap)] && [regexp qinq $userArgsArray(l2_encap)])} {
                    set tmpvlanlist {}
                    set vlan_id_mode "increment"
                    set vlan_id 1
                    set vlan_id_step 1
                    set vlan_user_priority 0
                    foreach param {vlan_id_mode vlan_id vlan_id_step vlan_user_priority} {
                        if {[info exists userArgsArray($param)]} {
                            set $param [set userArgsArray($param)]
                        }
                    }
                    switch $vlan_id_mode {
                        "fixed" {
                            lappend tmpvlanlist -VlanId $vlan_id -IdStep 0 -Priority $vlan_user_priority
                        }
                        "increment" {
                            lappend tmpvlanlist -VlanId $vlan_id -IdStep $vlan_id_step -Priority $vlan_user_priority
                        }
                        "decrement" {
                            incr vlan_id -[expr "$vlan_id_step * ($vlan_id_count-1)"]
                            lappend tmpvlanlist -VlanId $vlan_id -IdStep $vlan_id_step -Priority $vlan_user_priority
                        }
                        "random" {
                            # Random actually means shuffle, not a literal random in the HLTAPI core implementation
                            set tmpvlanlist $vlan_id
                            set cur_vlan_id $vlan_id
                            for {set idx 0} {$idx < [expr $vlan_id_count - 1]} {incr idx} {
                                lappend tmpvlanlist [incr cur_vlan_id $vlan_id_step]
                            }
                            set randvlanlist {}
                            while {[llength $randvlanlist] < [llength $tmpvlanlist]} {
                                set cur_vlan [lindex $tmpvlanlist [expr {int(rand()*[llength $tmpvlanlist])}]]
                                if {[lsearch $randvlanlist $cur_vlan] < 0} {
                                    lappend randvlanlist $cur_vlan
                                }
                            }
                            lappend tmpvlanlist -isRange FALSE -IdList $randvlanlist -Priority $vlan_user_priority
                        }
                        default {
                            set errMsg "Error in sth::traffic_config: unrecognized value for vlan_id_mode \"$userArgsArray(vlan_id_mode)\".  Valid values are fixed|increment|decrement|random."
                            ::sth::sthCore::log debug $errMsg
                    return -code 1 -errorcode -1 $errMsg;
                } 
            }            
                    if {[catch {set tmpvlanIf [::sth::sthCore::invoke stc::create vlanif -under $tmpHost "$tmpvlanlist"]} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the VlanIf for the static host. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
        }
                    if {[catch {::sth::sthCore::invoke stc::config $tmpvlanIf "-StackedOnEndpoint-targets $tmpEthiiIf"} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the VlanIf and EthIIIf. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
    }
                            if {[catch {::sth::sthCore::invoke stc::config [set tmpIpv4If_${proto_cur}_forDownstream] "-StackedOnEndpoint-targets $tmpvlanIf"} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the VlanIf and Ipv4If. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                }

                # Create QinQ (Vlan If)
                if {[info exists userArgsArray(l2_encap)] && [regexp qinq $userArgsArray(l2_encap)]} {
                    set tmpvlanouterlist {}
                    set vlan_id_outer_mode "increment"
                    set vlan_id_outer 1
                    set vlan_id_outer_step 1
                    set vlan_outer_user_priority 0
                            foreach param {vlan_id_outer_mode vlan_id_outer vlan_id_outer_step vlan_outer_user_priority} {
                        if {[info exists userArgsArray($param)]} {
                            set $param [set userArgsArray($param)]
                        }
                    }
                    switch $vlan_id_outer_mode {
                        "fixed" {
                                    lappend tmpvlanouterlist -VlanId $vlan_id_outer -IdStep 0 -Priority $vlan_outer_user_priority
                        }
                        "increment" {
                                    lappend tmpvlanouterlist -VlanId $vlan_id_outer -IdStep $vlan_id_outer_step -Priority $vlan_outer_user_priority
                        }
                        "decrement" {
                            incr vlan_id_outer -[expr "$vlan_id_outer_step * ($vlan_id_outer_count-1)"]
                            lappend tmpvlanouterlist -VlanId $vlan_id_outer -IdStep $vlan_id_outer_step
                        }
                        "random" {
                            # Random actually means shuffle, not a literal random in the HLTAPI core implementation
                            set tmpvlanouterlist $vlan_id_outer
                            set cur_vlan_id_outer $vlan_id_outer
                            for {set idx 0} {$idx < [expr $vlan_id_outer_count - 1]} {incr idx} {
                                lappend tmpvlanouterlist [incr cur_vlan_id_outer $vlan_id_outer_step]
                            }
                            set randvlanouterlist {}
                            while {[llength $randvlanouterlist] < [llength $tmpvlanouterlist]} {
                                set cur_vlanouter [lindex $tmpvlanouterlist [expr {int(rand()*[llength $tmpvlanouterlist])}]]
                                if {[lsearch $randvlanouterlist $cur_vlanouter] < 0} {
                                    lappend randvlanouterlist $cur_vlanouter
                                }
                            }
                                    lappend tmpvlanouterlist -isRange FALSE -IdList $randvlanouterlist -Priority $vlan_outer_user_priority
                        }
                        default {
                            set errMsg "Error in sth::traffic_config: unrecognized value for vlan_id_outer_mode \"$userArgsArray(vlan_id_outer_mode)\".  Valid values are fixed|increment|decrement|random."
                            ::sth::sthCore::log debug $errMsg
                            return -code 1 -errorcode -1 $errMsg;
                        }
                    }
                    if {[catch {set tmpvlanouterIf [::sth::sthCore::invoke stc::create vlanif -under $tmpHost "$tmpvlanouterlist"]} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while creating the VlanIf for the static host. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                    if {[catch {::sth::sthCore::invoke stc::config $tmpvlanouterIf "-StackedOnEndpoint-targets $tmpEthiiIf"} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the VlanIf (outer) and EthIIIf. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                    if {[catch {::sth::sthCore::invoke stc::config $tmpvlanIf "-StackedOnEndpoint-targets $tmpvlanouterIf"} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the VlanIf and EthIIIf. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                            if {[catch {::sth::sthCore::invoke stc::config [set tmpIpv4If_${proto_cur}_forDownstream] "-StackedOnEndpoint-targets $tmpvlanIf"} errMsg]} {
                                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while stacking the VlanIf and Ipv4If. Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                }

                # Set the Source binding targets
                    for {set idx 0} {$idx < [llength [set userArgsArray($downstream_param_name)]]} {incr idx} {
                        lappend tmpIpv4IfList_${proto_cur}_forDownstream [set tmpIpv4If_${proto_cur}_forDownstream]
                }
                    if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -SrcBinding-targets "[set tmpIpv4IfList_${proto_cur}_forDownstream]"} errMsg]} {
                        ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the $proto_cur link -SrcBinding-targets [set tmpIpv4IfList_${proto_cur}_forDownstream]. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                }
            }
        }
    }
    }

    set ::${mns}::l2ExtHeaderType ethernet_ii;
    if {[info exists userArgsArray(l2_encap)]} {
        set ::${mns}::l2ExtHeaderType $userArgsArray(l2_encap);
    }

    # Create PPPoE and PPP header
    if {[info exists userArgsArray(l2_encap)] && [regexp pppoe $userArgsArray(l2_encap)] && !$pppox_link_true} {
    set pppoeList {}
    if {[info exists userArgsArray(ppp_session_id)]} {
        lappend pppoeList -sessionID $userArgsArray(ppp_session_id)
    }
    if {[catch {::sth::sthCore::invoke stc::create pppoe:PPPoESession -under [set ::${mns}::handleTxStream] $pppoeList} errMsg]} {
        set errMsg "Error in sth::traffic_config while trying to create PPPoE session header. Msg: $errMsg"
        ::sth::sthCore::log debug $errMsg
        return -code 1 -errorcode -1 $errMsg;
    }
        if {[catch {::sth::sthCore::invoke stc::create ppp:PPP -under [set ::${mns}::handleTxStream]} errMsg]} {
        set errMsg "Error in sth::traffic_config while trying to create PPP header. Msg: $errMsg"
        ::sth::sthCore::log debug $errMsg
        return -code 1 -errorcode -1 $errMsg;
    }
    }

    if {$pppox_link_true} {
        if {[info exists userArgsArray(downstream_traffic_src_list)]} {
            if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -DstBinding-targets "$pppox_dst_ipv4if_list"} errMsg]} {
                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the PPPoX link -DstBinding-targets $pppox_dst_ipv4if_list. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
            }
        }
        if {[info exists userArgsArray(ppp_link_traffic_src_list)]} {
            if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -SrcBinding-targets "$pppox_src_ipv4if_list"} errMsg]} {
                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the PPPoX link -SrcBinding-targets $pppox_src_ipv4if_list. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
            }
        }
        if {[info exists userArgsArray(ppp_link_traffic_src_list)] && ! [info exists userArgsArray(downstream_traffic_src_list)]} {
            if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -DstBinding-targets "$tmpIpv4IfList_pppox_forUpstream"} errMsg]} {
                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the PPPoX link -DstBinding-targets $tmpIpv4IfList_pppox_forUpstream. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
        }
        if {[info exists userArgsArray(downstream_traffic_src_list)] && ! [info exists userArgsArray(ppp_link_traffic_src_list)]} {
            if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -SrcBinding-targets "$tmpIpv4IfList_pppox_forDownstream"} errMsg]} {
                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the PPPoX link -SrcBinding-targets $tmpIpv4IfList_pppox_forDownstream. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
        }
    }

    if {$dhcp_link_true} {
        if {[info exists userArgsArray(dhcp_downstream)]} {
            if {$iteration == 0} {
                if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -DstBinding-targets "$dhcp_dst_ipv4if_list"} errMsg]} {
                    ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the DHCP link -DstBinding-targets $dhcp_dst_ipv4if_list. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                }
            } else {
                if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -DstBinding-targets "$dhcp_src_ipv4if_list"} errMsg]} {
                    ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the DHCP link -DstBinding-targets $dhcp_dst_ipv4if_list. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                  }
            }
        }
        if {[info exists userArgsArray(dhcp_upstream)]} {
            if {$iteration == 0} {
                if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -SrcBinding-targets "$dhcp_src_ipv4if_list"} errMsg]} {
                    ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the DHCP link -SrcBinding-targets $dhcp_src_ipv4if_list. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                }
            } else {
                if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -SrcBinding-targets "$dhcp_dst_ipv4if_list"} errMsg]} {
                    ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the DHCP link -SrcBinding-targets $dhcp_src_ipv4if_list. Msg: $errMsg";
                    ::sth::sthCore::processError trafficKeyedList $errMsg;
                    return -code 1 -errorcode -1 $errMsg;
                }
            }
        }
        if {[info exists userArgsArray(dhcp_upstream)] && ! [info exists userArgsArray(dhcp_downstream)]} {
            if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -DstBinding-targets "$tmpIpv4IfList_dhcp_forUpstream"} errMsg]} {
                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the DHCP link -DstBinding-targets $tmpIpv4IfList_dhcp_forUpstream. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
        }
        if {[info exists userArgsArray(dhcp_downstream)] && ! [info exists userArgsArray(dhcp_upstream)]} {
            if {[catch {::sth::sthCore::invoke stc::config [set ::${mns}::handleTxStream] -EnableTxPortSendingTrafficToSelf TRUE -SrcBinding-targets "$tmpIpv4IfList_dhcp_forDownstream"} errMsg]} {
                ::sth::sthCore::log debug "::sth::Traffic::processCreatePppoxDhcpEncap FAILED while configuring the DHCP link -SrcBinding-targets $tmpIpv4IfList_dhcp_forDownstream. Msg: $errMsg";
                ::sth::sthCore::processError trafficKeyedList $errMsg;
                return -code 1 -errorcode -1 $errMsg;
            }
        }
    }

    return ::sth::sthCore::SUCCESS;
}

#add for gre
proc ::sth::Traffic::processCreateGreProtocol {} {
    
    set _procName "processCreateGreProtocol";
    upvar userArgsArray userArgsArray;
    upvar mns mns;
     
    array set GreConfigInfo $userArgsArray(tunnel_handle)
    
    set tunnelType $GreConfigInfo(gre_tnl_type)
    set ipv4Version 4
    if {$tunnelType == $ipv4Version } {
        set mask "255.255.255.255"
        set header "ipv4:IPv4"
        } else {
            set mask "::FFFF:FFFF"
            set  header "ipv6:IPv6" }
    
   set keyFlag "false" 
   if {[info exists GreConfigInfo(gre_out_key)]} {
    set keyFlag "true"
    set keyVakue $GreConfigInfo(gre_out_key)
   }
    
    set ipArgsList "-sourceAddr $GreConfigInfo(gre_src_addr) -destAddr $GreConfigInfo(gre_dst_addr)"
    set greArgsList "-ckPresent $GreConfigInfo(gre_checksum) -keyPresent $keyFlag"
    
    set mode $userArgsArray(mode)
    if {$mode == "modify" && [set ::$mns\::greIPHeader] != "" } {
    #this is the case for modify
        #the handle name will be changed after the stc:apply, so the config command not work here
        #need further check
        set streamHandle [set ::$mns\::handleCurrentStream]
        set greIPHeader [::sth::sthCore::invoke ::stc::get $streamHandle -children-$header]
            
        if {[set ::$mns\::greIPHeaderType] != $GreConfigInfo(gre_tnl_type)} {
            #puts "the config gre delivery type is not allowed different from create";
            return $::sth::sthCore::FAILURE;
        }
    
        set cmdName "::sth::sthCore::invoke stc::config $greIPHeader $ipArgsList"
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while processing $header -- $retHandle";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::config Success. Handle is $retHandle";
             set ::$mns\::greIPHeader $retHandle;
        }
        
        set headerToConfigure [set ::$mns\::greHeader]
        
        set length [string length $headerToConfigure]
        set index [expr $length - 2]
        set objectName [string range $headerToConfigure 0 $index]
        set greHeader [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
        
        set cmdName "::sth::sthCore::invoke stc::config $greHeader  $greArgsList"
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while processing $header -- $retHandle";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::config Success. Handle is $retHandle";
             set ::$mns\::greIPHeader $retHandle;
        }
        
        if {[catch {::sth::sthCore::invoke stc::get $greIPHeader -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $retHandle -name $headerName ";
            return $::sth::sthCore::FAILURE;
            } else {
            ::sth::sthCore::log info "$_procName: $retHandle -name $headerName ";
            }
    } else {
        # for the create mode
        
        #create the GRE deliver header
       set cmdName "::sth::sthCore::invoke stc::create $header -under [set ::$mns\::handleCurrentStream] \"$ipArgsList\""
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while processing $header -- $retHandle";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
            #store this handle for modify
             set ::$mns\::greIPHeader $retHandle;
             set ::$mns\::greIPHeaderType $GreConfigInfo(gre_tnl_type)
        }
        
        if {[catch {::sth::sthCore::invoke stc::get $retHandle -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $retHandle -name $headerName ";
            return $::sth::sthCore::FAILURE;
            } else {
            ::sth::sthCore::log info "$_procName: $retHandle -name $headerName ";
            }

        
   
       #create the GRE header
       set cmdName "::sth::sthCore::invoke stc::create gre:Gre -under [set ::$mns\::handleCurrentStream] \"$greArgsList\""
       if {[catch {eval $cmdName} greHandle]} {
            #puts "error while processing creat gre header -- $greHandle";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $greHandle";
            set ::$mns\::greHeader $greHandle;
        }
   
       if {$keyFlag == "true" } {
           if {[catch {::sth::sthCore::invoke stc::create Keys -under $greHandle} keysHandle]} {
                 #puts "error while processing creat gre keys-- $keysHandle";
                return $::sth::sthCore::FAILURE;
            } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $keysHandle";
            }
            if {[catch {::sth::sthCore::invoke stc::create GreKey -under $keysHandle "-value $keyVakue"} keyHandle]} {
                 #puts "error while processing creat gre key -- $keyHandle";
                 return $::sth::sthCore::FAILURE;
            } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $keyHandle";
            }
        }
    }
    
    #check if the gre delivery header src addr rangemodifier is needed 
    if {$GreConfigInfo(gre_src_addr_count) != 1 && $GreConfigInfo(gre_src_mode) != "fixed"} {
           if { [set ::$mns\::greRangeModifierSrc] == "" } {
                 set rangeConfigList "-RecycleCount $GreConfigInfo(gre_src_addr_count) \
                                -ModifierMode INCR -Mask $mask -StepValue $GreConfigInfo(gre_src_addr_step) -data $GreConfigInfo(gre_src_addr) \
                                -OffsetReference $headerName.sourceAddr"
            
                set cmdName  "::sth::sthCore::invoke stc::create rangeModifier -under [set ::$mns\::handleCurrentStream] \"$rangeConfigList\""
            
                 if {[catch {eval $cmdName} retHandle]} {
                      #puts "error while processing rangeModifier -- $retHandle";
                      return $::sth::sthCore::FAILURE;
                } else {
                     ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                      set ::$mns\::greRangeModifierSrc $retHandle;                      
                }
            } else {
                set rangeConfigList "-RecycleCount $GreConfigInfo(gre_src_addr_count) \
                                    -ModifierMode INCR -Mask $mask -StepValue $GreConfigInfo(gre_src_addr_step) -data $GreConfigInfo(gre_src_addr) \
                                    -OffsetReference $headerName.sourceAddr"
                set cmdName  "::sth::sthCore::invoke stc::config [set ::$mns\::greRangeModifier] \"$rangeConfigList\""
            
               if {[catch {eval $cmdName} retHandle]} {
                #puts "error while processing rangeModifier -- $retHandle";
                return $::sth::sthCore::FAILURE;
                } else {
                ::sth::sthCore::log info "$_procName: stc::config Success. Handle is $retHandle";               
               }
            }
    }
    
    #check if the gre delivery header src addr rangemodifier is needed 
    if {$GreConfigInfo(gre_dst_addr_count) != 1 && $GreConfigInfo(gre_dst_mode) != "fixed"} {
           if { [set ::$mns\::greRangeModifierDst] == "" } {
                set rangeConfigList "-RecycleCount $GreConfigInfo(gre_dst_addr_count) \
                                     -ModifierMode INCR -Mask $mask -StepValue $GreConfigInfo(gre_dst_addr_step) -data $GreConfigInfo(gre_dst_addr) \
                                     -OffsetReference $headerName.destAddr"
                set cmdName  "::sth::sthCore::invoke stc::create rangeModifier -under [set ::$mns\::handleCurrentStream] \"$rangeConfigList\""
            
               if {[catch {eval $cmdName} retHandle]} {
                #puts "error while processing rangeModifier -- $retHandle";
                return $::sth::sthCore::FAILURE;
                } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                set ::$mns\::greRangeModifierDst $retHandle;                      
               }
            } else {
                set rangeConfigList "-RecycleCount $GreConfigInfo(gre_dst_addr_count) \
                                    -ModifierMode INCR -Mask $mask -StepValue $GreConfigInfo(gre_dst_addr_step) -data $GreConfigInfo(gre_dst_addr) \
                                    -OffsetReference $headerName.destAddr"
                set cmdName  "::sth::sthCore::invoke stc::config [set ::$mns\::greRangeModifier] \"$rangeConfigList\""
            
                if {[catch {eval $cmdName} retHandle]} {
                #puts "error while processing rangeModifier -- $retHandle";
                return $::sth::sthCore::FAILURE;
                } else {
                ::sth::sthCore::log info "$_procName: stc::config Success. Handle is $retHandle";               
               }
            }
    }
}

proc ::sth::Traffic::processCreateL3Protocol {} {
    # TODO: Raise exception where ever there is return failure
    
    set _procName "processCreateL3Protocol";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    
    variable arrayHeaderLists;
    variable l3HeaderType;
    
    set headerSet $arrayHeaderLists($l3HeaderType);
    set headerToCreate [lindex $headerSet 0];
    set listsToUse [lindex $headerSet 1];
    set listArgsList {};
    set flaglist {}; #variable for -ip_fragement 
    
    foreach List $listsToUse {
        foreach element [set ::$mns\::$List] {
            set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
            # MOD Cheng Fei 08-10-07
            # ip_src_addr and ip_dst_addr are used both in ipv4 and arp.
            # if the l3_protocol is arp, they map to different stc attr.
            if {$headerToCreate == "arp:ARP" && $element == "ip_src_addr"} {
                set stcAttr "senderPAddr";
            }
            if {$headerToCreate == "arp:ARP" && $element == "ip_dst_addr"} {
                set stcAttr "targetPAddr";
            }
            if {$headerToCreate == "arp:ARP" && $element == "arp_operation"} {
               switch -exact $userArgsArray($element) {
                    "arpRequest" {
                        set userArgsArray($element) 1;
                    }
                    "arpReply" {
                        set userArgsArray($element) 2;
                    }
                    "rarpRequest" {
                        set userArgsArray($element) 3;
                        set headerToCreate "arp:RARP";
                    }
                    "rarpReply" {
                        set userArgsArray($element) 4;
                        set headerToCreate "arp:RARP";
                    }
               }
            }
            ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"

            # To support 'mf_bit' and 'reserved' -- Jeff July 4,2017
            if {$element == "ip_fragment" || $element == "mf_bit" || $element == "reserved" } {
                if {$element == "ip_fragment"} {
                    switch -exact $userArgsArray($element) {
                        "1" {
                            set userArgsArray($element) 0;
                        }
                        "0" {
                            set userArgsArray($element) 1;
                        }
                    }
                    lappend flaglist -$stcAttr $userArgsArray($element);
                } 
                if {$element == "mf_bit"} {
                    lappend flaglist -$stcAttr $userArgsArray($element);
                }
                if {$element == "reserved"} {
                    lappend flaglist -$stcAttr $userArgsArray($element);
                } 
            } else {
                lappend listArgsList -$stcAttr $userArgsArray($element);
            }
        }
    }
    ## If mac_discovery_gw is set by user for L2 header, the gateway ip
    ## is used in L3 IP header
    if {[info exists userArgsArray(mac_discovery_gw)] && ![regexp -nocase "outer" $listsToUse]} {
        lappend listArgsList -gateway $userArgsArray(mac_discovery_gw);
    }
    
    if {[set ::$mns\::handleCurrentHeader] == 0} {
        ###########################################
        # Create L3 header
        ###########################################
        #::sth::sthCore::invoke stc::perform StreamBlockUpdate -streamblock [set ::$mns\::handleCurrentStream]
        #set retHandle [::sth::sthCore::invoke ::stc::get [set ::$mns\::handleCurrentStream] -children-$headerToCreate]
        #if {$retHandle == ""} {
        #    # we would have to create the header irrespective of the mode.
        #    ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listArgsList"
        #    set cmdName "::sth::sthCore::invoke ::stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listArgsList"
        #    if {[catch {eval $cmdName} retHandle]} {
        #        #puts "error while processing $headerToCreate -- $retHandle";
        #        return $::sth::sthCore::FAILURE;
        #    } else {
        #        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        #    }
        #} else {
        #    ::sth::sthCore::invoke ::stc::config $retHandle $listArgsList
        #}
        # we would have to create the header irrespective of the mode.
        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listArgsList"
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while processing $headerToCreate -- $retHandle";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
       
        # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        }   
        
        if {[regexp outer $l3HeaderType]} {
            lappend listOfHeaders "l3_header_outer";
        } elseif {[regexp inner $l3HeaderType]} {
            lappend listOfHeaders "inner_l3_header";
        } else {
            lappend listOfHeaders "l3_header";
        }
        
        lappend listOfHeaders "[set retHandle]";
        set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
        
        ###########################################
        # handle Ipv4 flag field
        # Need to optimize
        ###########################################
        #CR278217627
        if {[regexp ipv4 $headerToCreate] && [llength $flaglist] != 0} {
            set handleCurrentIp "[set retHandle]";
            set flagsToCreate [::sth::sthCore::invoke ::stc::get $handleCurrentIp -children-flags]
            if {[regexp flags $flagsToCreate] == 0} {
                ::sth::sthCore::log debug "$_procName: Calling stc::create flags $handleCurrentIp $flaglist"
                set cmdName "::sth::sthCore::invoke ::stc::create flags -under $handleCurrentIp $flaglist"
                if {[catch {eval $cmdName} flagHandle]} {
                    ::sth::sthCore::processError trafficKeyedList "error while creating ip flags -- $flagHandle" {}
                    return $::sth::sthCore::FAILURE;
                } else {
                    ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $flagHandle";
                }
            } else {
                if {[llength $flaglist]} {
                    ::sth::sthCore::log debug "$_procName: Calling stc::config $flagsToCreate $flaglist"
                    set cmdName "::sth::sthCore::invoke ::stc::config $flagsToCreate $flaglist"
                    if {[catch {eval $cmdName} retValue]} {
                        #puts "error while configuring #flagsToCreate";
                        return $::sth::sthCore::FAILURE;
                    } else {
                        ::sth::sthCore::log info "$_procName: $flagsToCreate Success. ";
                    }
                }
            }
        }
    } else {
        ###########################################
        # Modify L3 header
        ###########################################
        
        # if this is not 0 that means this has to be mode modify and header was created earlier.
        # set retHandle to this value to be used below
        set retHandle [set ::$mns\::handleCurrentHeader];
        
        set headerToConfigure [set ::$mns\::handleCurrentHeader];
        
        set streamHandle [set ::$mns\::handleCurrentStream]
        #set length [string length $headerToConfigure]
        #set index [expr $length - 2]
        #set objectName [string range $headerToConfigure 0 $index]
        if {[regexp ipv4 $headerToConfigure]} {
            set objectName "ipv4:IPv4"
        } elseif {[regexp ipv6 $headerToConfigure]} {
            set objectName "ipv6:IPv6"
        } else {
            regsub -all {\d+$} $headerToConfigure "" objectName
        }
        #the ip header handle may be changed after applying, so we need to get the handle again here
        #if l3_outer_protocol is created, we need to get the specified ip header to modify
        set headerToConfigure [::stc::get $streamHandle -children-$objectName]
        #if there is vxlan, there will be also 2 ipv4 header, so here need to check if there is vxlan header
        if {[regexp -nocase "vxlan" [::sth::sthCore::invoke stc::get $streamHandle -children]]} {
            set vxlan_header [::sth::sthCore::invoke stc::get $streamHandle -children-vxlan:vxlan]
        } else {
            set vxlan_header ""
        }
        
        if {$vxlan_header == ""} {
            if {[llength $headerToConfigure] > 1} {
                if {[regexp outer $l3HeaderType]} {
                    set headerToConfigure [lindex $headerToConfigure 0]
                } else {
                    set headerToConfigure [lindex $headerToConfigure 1]
                }
            }
        } else {
            if {[llength $headerToConfigure] > 1} {
                if {[regexp inner $l3HeaderType]} {
                    set headerToConfigure [lindex $headerToConfigure 1]
                } else {
                    set headerToConfigure [lindex $headerToConfigure 0]
                }
            }
        }
        set retHandle $headerToConfigure
                    
        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList";
        if {[catch {eval $cmdName} retValue]} {
            #puts "error while configuring $headerToConfigure";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
        }
        
        ###########################################
        # handle Ipv4 flag field
        ###########################################
        #MOD He Nana
        #if exist flags then config it, else create one.
        #CR278217627
        if {[regexp ipv4 $objectName] && [llength $flaglist] != 0} {
            set flagsToConfigure [::sth::sthCore::invoke ::stc::get $headerToConfigure -children-flags]
            if {[regexp flags $flagsToConfigure]} {
                if {[llength $flaglist]} {
                    ::sth::sthCore::log debug "$_procName: Calling stc::config $flagsToConfigure $flaglist"
                    set cmdName "::sth::sthCore::invoke ::stc::config $flagsToConfigure $flaglist"   
                    if {[catch {eval $cmdName} retValue]} {
                        #puts "error while configuring $flagsToConfigure";
                        return $::sth::sthCore::FAILURE;
                    } else {
                        ::sth::sthCore::log info "$_procName: $flagsToConfigure Success. ";
                    }
                }
            } else {
                set ip_flags [::sth::sthCore::invoke ::stc::create flags -under $headerToConfigure]
                if {[llength $flaglist]} {
                    ::sth::sthCore::invoke stc::config $ip_flags $flaglist
                }
            }   
        }
    }
    
    # Check if modifier is needed here.
    # This is layer 3 header. So as of now taking care of src/dst for ipv4/ipv6
    
    if {[llength [set ::$mns\::listMacGwRangeModifier]]} {
        ::sth::Traffic::processCreateL3RangeModifier $retHandle listMacGwRangeModifier gateway;
    }
    
    if {[llength [set ::$mns\::listInnerGwRangeModifier]]} {
        ::sth::Traffic::processCreateL3RangeModifier $retHandle listInnerGwRangeModifier gateway;
    }
    
    ###########################################
    # Modifier for src/dst addr for IP Outer header
    ###########################################
    if {[regexp outer $l3HeaderType]} {    
        if {[llength [set ::$mns\::listl3OuterSrcRangeModifier]]} {
            # TODO: put a catch here later
            ::sth::Traffic::processCreateL3RangeModifier $retHandle listl3OuterSrcRangeModifier sourceAddr;
        }
        
        if {[llength [set ::$mns\::listl3OuterDstRangeModifier]]} {
            # TODO: put a catch here later
            ::sth::Traffic::processCreateL3RangeModifier $retHandle listl3OuterDstRangeModifier destAddr;
        }

        ###########################################
        # Handle L3 Qos bits
        ###########################################
        if {[llength [set ::$mns\::listl3OuterQosBits]]} {
            # TODO: put a catch here later
            if {[catch {::sth::Traffic::processCreateQosHeader $retHandle listl3OuterQosBits} errMsg]} {
                ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
                return -code error $trafficKeyedList;
            }
        }

    } elseif {[regexp inner $l3HeaderType]} {
        if {[llength [set ::$mns\::listInnerl3SrcRangeModifier]]} {
            ::sth::Traffic::processCreateL3RangeModifier $retHandle listInnerl3SrcRangeModifier sourceAddr;
        }
        
        if {[llength [set ::$mns\::listInnerl3DstRangeModifier]]} {
            ::sth::Traffic::processCreateL3RangeModifier $retHandle listInnerl3DstRangeModifier destAddr;
        }
    } else {
        ###########################################
        # Modifier for SRC addr for IP header
        ###########################################
        if {[llength [set ::$mns\::listl3SrcRangeModifier]]} {
                     #MOD Fei Cheng 08-10-10
            if {$userArgsArray(l3_protocol) == "arp"} {
                ::sth::Traffic::processCreateL3RangeModifier $retHandle listl3SrcRangeModifier senderPAddr;
            } else {
                ::sth::Traffic::processCreateL3RangeModifier $retHandle listl3SrcRangeModifier sourceAddr;
            }
        }
        
        ###########################################
        # Modifier for DST addr for IP header
        ###########################################
        if {[llength [set ::$mns\::listl3DstRangeModifier]]} {
            if {$userArgsArray(l3_protocol) == "arp"} {
                ::sth::Traffic::processCreateL3RangeModifier $retHandle listl3DstRangeModifier targetPAddr;
            } else {
                ::sth::Traffic::processCreateL3RangeModifier $retHandle listl3DstRangeModifier destAddr;
            }
        }
        
        ###########################################
        # Modifier for SRC addr for ARP header
        ###########################################   
        #MOD Fei Cheng 08-10-10
        #Add support for modifier on arp_src_hw_addr & arp_dst_hw_addr
        if {[llength [set ::$mns\::listArpMacSrcRangeModifier]]} {
            if {[info exists userArgsArray(arp_src_hw_mode)]} {
                set srcModeValue $userArgsArray(arp_src_hw_mode);
                if {$srcModeValue != "fixed"} {
                   ::sth::Traffic::processCreateL3RangeModifier $retHandle listArpMacSrcRangeModifier senderHwAddr;
                }
            }
        }
        
        ###########################################
        # Modifier for DST addr for ARP header
        ###########################################
        if {[llength [set ::$mns\::listArpMacDstRangeModifier]]} {
            if {[info exists userArgsArray(arp_dst_hw_mode)]} {
                set dstModeValue $userArgsArray(arp_dst_hw_mode);
                if {$dstModeValue != "fixed"} {
                ::sth::Traffic::processCreateL3RangeModifier $retHandle listArpMacDstRangeModifier targetHwAddr;
                }
            }
        }
        
        ###########################################
        # Handle L3 Qos bits
        ###########################################
        if {[llength [set ::$mns\::listl3QosBits]]} {
            # TODO: put a catch here later
            if {[catch {::sth::Traffic::processCreateQosHeader $retHandle listl3QosBits} errMsg]} {
                ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
                return -code error $trafficKeyedList;
            }
        }
    }
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processCreateModifyIpv6NextHeader {} {
    set _procName "processCreateModifyIpv6NextHeader";
    
    upvar userArgsArray userArgsArray
    upvar trafficKeyedList trafficKeyedList
    upvar mns mns;
    variable listOfIpv6NextHeaders
    
    if {[regexp -nocase "modify" $userArgsArray(mode)]} {
        if {[info exists ::$mns\::arraystreamIpv6NextHeadersHnd([set ::$mns\::handleCurrentStream]]} {
            set listOfIpv6NextHeaders [set ::$mns\::arraystreamIpv6NextHeadersHnd([set ::$mns\::handleCurrentStream])]
            if {$listOfIpv6NextHeaders != "none"} {
                foreach {previous_ipv6_next_header headerhandle} $listOfIpv6NextHeaders {
                    ::sth::sthCore::invoke stc::delete $headerhandle
                }
            }
        } 
    }
    set listOfIpv6NextHeaders ""
    
    if {[regexp -nocase "none" $userArgsArray(ipv6_extension_header)]} {
        set ::$mns\::arraystreamIpv6NextHeadersHnd([set ::$mns\::handleCurrentStream]) "none"
        return ::sth::sthCore::SUCCESS
    }
    # we would have to create the header irrespective of the mode.
    if {[regexp -nocase "hop_by_hop" $userArgsArray(ipv6_extension_header)]} {
        set retHandle [::sth::sthCore::invoke stc::create ipv6:Ipv6HopByHopHeader -under [set ::$mns\::handleCurrentStream]]
        lappend listOfIpv6NextHeaders hop_by_hop $retHandle
        if {[info exists userArgsArray(ipv6_hop_by_hop_options)]} {
            set options [::sth::sthCore::invoke stc::create options -under $retHandle]
            set hopbyhop_options [::sth::sthCore::invoke stc::create Ipv6HopByHopOption -under $options]
            set ipv6_hop_by_hop_options $userArgsArray(ipv6_hop_by_hop_options)
            if {[regexp {type:\s*(\w+)?\s*} $ipv6_hop_by_hop_options tmp type]} {
                if {[regexp -nocase "pad1" $type]} {
                    ::sth::sthCore::invoke stc::create PAD1 -under $hopbyhop_options
                } elseif {[regexp -nocase "padn" $type]} {
                    set padn [::sth::sthCore::invoke stc::create PADN -under $hopbyhop_options]
                    # mode by yinmeng 08/09/12
                    #check the format 
                    if {[regexp {value:\s*(.+)?\s*} $ipv6_hop_by_hop_options tmp value]} {
                        regsub -all {:|\.} $value "" value
                        #check the value format
                        if {[string length $value] == 2 && [regexp {[[:xdigit:]]{2}} $value]} {
                            ::sth::sthCore::invoke stc::config $padn "-padding $value"
                        } else {
                            set errorString "ipv6_hop_by_hop_options has invalid value format for padn type, it must be a 8-bit hexadecimal value. Current value is: $value";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                        }
                    }
                    if {[regexp {length:\s*(\w+)?\s*} $ipv6_hop_by_hop_options tmp length]} {
                        #check the length range
                        if {$length>=0 && $length<=255} {
                            ::sth::sthCore::invoke stc::config $padn "-length $length"
                        } else {
                            set errorString "ipv6_hop_by_hop_options has invalid length for padn type, the possible values range from 0 to 255. Current length: $length";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                        }
                    }
                } elseif {[regexp -nocase "jumbo" $type]} {
                    set jumbo [::sth::sthCore::invoke stc::create jumbo -under $hopbyhop_options]
                    if {[regexp {length:\s*(\w+)?\s*} $ipv6_hop_by_hop_options tmp length]} {
                        #check the length range
                        if {$length>=0 && $length<=255} {
                            ::sth::sthCore::invoke stc::config $jumbo "-length $length"
                        } else {
                             set errorString "ipv6_hop_by_hop_options has invalid length for jumbo type, the possible values range from 0 to 255. Current length: $length";
                             ::sth::sthCore::log debug "$_procName: $errorString "
                             return -code 1 -errorcode -1 $errorString;
                        }
                    }
                    if {[regexp {payload:\s*(\w+)?\s*} $ipv6_hop_by_hop_options tmp payload]} {
                        #check the payload range
                        if {$payload>=0 && $payload<=65535} {
                             ::sth::sthCore::invoke stc::config $jumbo "-data $payload"
                        } else {
                            set errorString "ipv6_hop_by_hop_options has invalid payload, the possible values range from 0 to 65535. Current value: $payload";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                        }
                    }
                } elseif {[regexp -nocase "router_alert" $type]} {
                    set router_alert [::sth::sthCore::invoke stc::create routerAlert -under $hopbyhop_options]
                    if {[regexp {alert_type:\s*(\w+)?\s*} $ipv6_hop_by_hop_options tmp alert_type]} {
                        if {[regexp -nocase "mld" $alert_type]} {
                            ::sth::sthCore::invoke stc::config $router_alert "-value 0"
                        } elseif {[regexp -nocase "rsvp" $alert_type]} {
                            ::sth::sthCore::invoke stc::config $router_alert "-value 1"
                        } elseif {[regexp -nocase "active_net" $alert_type]} {
                            ::sth::sthCore::invoke stc::config $router_alert "-value 2"
                        } else {
                            set errorString "router_alert has invalid alert type, the possible values are mld, rsvp, and active_net. Current type value is: $alert_type";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                        }
                    }
                    if {[regexp {length:\s*(\w+)?\s*} $ipv6_hop_by_hop_options tmp length]} {
                        if {$length>=0 && $length<=255} {
                            ::sth::sthCore::invoke stc::config $router_alert "-length $length"
                        } else {
                            set errorString "ipv6_hop_by_hop_options has invalid length for router_alert type, the possible values range from 0 to 255. Current length: $length";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                        }
                    }
                } else {
                    set errorString "ipv6_hop_by_hop_options has invalid type, the possible values are pad1, padn, jumbo, router_alert. Current type value is: $type";
                    ::sth::sthCore::log debug "$_procName: $errorString "
                    return -code 1 -errorcode -1 $errorString;
                }
            } else {
                set errorString "ipv6_hop_by_hop_options has no type attribute, it is mandatory. Current ipv6_hop_by_hop_options value is: $ipv6_hop_by_hop_options";
                ::sth::sthCore::log debug "$_procName: $errorString "
                return -code 1 -errorcode -1 $errorString;
            }
            
        }
    }
        
    if {[regexp -nocase "routing" $userArgsArray(ipv6_extension_header)]} {
        set retHandle [::sth::sthCore::invoke stc::create ipv6:Ipv6RoutingHeader -under [set ::$mns\::handleCurrentStream]]
        lappend listOfIpv6NextHeaders routing $retHandle
        if {[info exists userArgsArray(ipv6_routing_node_list)]} {
            set nodes [::sth::sthCore::invoke stc::create nodes -under $retHandle]
            foreach ipv6_routing_node [split $userArgsArray(ipv6_routing_node_list)] {
                ::sth::sthCore::invoke stc::create Ipv6Addr -under $nodes "-value $ipv6_routing_node"
            }
        }
        if {[info exists userArgsArray(ipv6_routing_res)]} {
            regsub -all {:|\.} $userArgsArray(ipv6_routing_res) "" ipv6_routing_res
             if {[string length $ipv6_routing_res] == 4 && [regexp {[[:xdigit:]]{4}} $ipv6_routing_res]} {
                set ipv6_routing_res [format "%d" 0X$ipv6_routing_res]
                ::sth::sthCore::invoke stc::config $retHandle "-reserved $ipv6_routing_res"
            } else {
                set errorString "ipv6_routing_res has invalid format, it must be a 16-bit hexadecimal value. Current ipv6_routing_res value is: $ipv6_routing_res";
                ::sth::sthCore::log debug "$_procName: $errorString "
                return -code 1 -errorcode -1 $errorString;
            }   
        }
    }
        
    if {[regexp -nocase "destination" $userArgsArray(ipv6_extension_header)]} {
        set retHandle [::sth::sthCore::invoke stc::create ipv6:Ipv6DestinationHeader -under [set ::$mns\::handleCurrentStream]]
        lappend listOfIpv6NextHeaders destination $retHandle
        if {[info exists userArgsArray(ipv6_destination_options)]} {
            set options [::sth::sthCore::invoke stc::create options -under $retHandle]
            set destination_options [::sth::sthCore::invoke stc::create Ipv6DestinationOption -under $options]
            set ipv6_destination_options $userArgsArray(ipv6_destination_options)
            if {[regexp {type:(.*)\s*} $ipv6_destination_options type]} {
                if {[regexp -nocase "pad1" $type]} {
                    ::sth::sthCore::invoke stc::create PAD1 -under $destination_options
                } elseif {[regexp -nocase "padn" $type]} {
                    set padn [::sth::sthCore::invoke stc::create PADN -under $destination_options]
                    if {[regexp {value:\s*(.+)?\s*} $ipv6_destination_options tmp value]} {
                        regsub -all {:|\.} $value "" value
                        # mode by yinmeng 08/09/12
                        #check the value format 
                        if {[string length $value] == 2 && [regexp {[[:xdigit:]]{2}} $value]} {
                            ::sth::sthCore::invoke stc::config $padn "-padding $value"
                        } else {
                            set errorString "ipv6_destination_options has invalid value for padn type, it must be a 8-bit hexadecimal value. Current value is: $value";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                        }   
                    }
                    if {[regexp {length:\s*(\w+)?\s*} $ipv6_destination_options tmp length]} {
                        #check the length range
                         if {$length>=0 && $length<=255} {
                             ::sth::sthCore::invoke stc::config $padn "-length $length"
                         } else {
                             set errorString "ipv6_destination_options has invalid length for padn type, the possible values range from 0 to 255. Current length: $length";
                             ::sth::sthCore::log debug "$_procName: $errorString "
                             return -code 1 -errorcode -1 $errorString;
                         }
                    }
                } else {
                    set errorString "ipv6_destination_options has invalid type, the possible values are pad1 or padn. Current type value is: $type";
                    ::sth::sthCore::log debug "$_procName: $errorString "
                    return -code 1 -errorcode -1 $errorString;
                }
            } else {
                    set errorString "ipv6_destination_options has no type attribute, it is mandatory. Current ipv6_destination_options value is: $ipv6_destination_options";
                    ::sth::sthCore::log debug "$_procName: $errorString "
                    return -code 1 -errorcode -1 $errorString;
            }
        }
    }
        
    if {[regexp -nocase "fragment" $userArgsArray(ipv6_extension_header)] ||
             [info exists userArgsArray(ipv6_frag_offset)] || [info exists userArgsArray(ipv6_frag_more_flag)] || [info exists userArgsArray(ipv6_frag_id)]} {
        set retHandle [::sth::sthCore::invoke stc::create ipv6:Ipv6FragmentHeader -under [set ::$mns\::handleCurrentStream]]
        lappend listOfIpv6NextHeaders fragment $retHandle
        if {[info exists userArgsArray(ipv6_frag_offset)]} {::sth::sthCore::invoke stc::config $retHandle "-fragOffset $userArgsArray(ipv6_frag_offset)"}
        if {[info exists userArgsArray(ipv6_frag_more_flag)]} {::sth::sthCore::invoke stc::config $retHandle "-m_flag $userArgsArray(ipv6_frag_more_flag)"}
        if {[info exists userArgsArray(ipv6_frag_id)]} {::sth::sthCore::invoke stc::config $retHandle "-ident $userArgsArray(ipv6_frag_id)"}
    }
        
    if {[regexp -nocase "authentication" $userArgsArray(ipv6_extension_header)]} {
        set retHandle [::sth::sthCore::invoke stc::create ipv6:Ipv6AuthenticationHeader -under [set ::$mns\::handleCurrentStream]]
        lappend listOfIpv6NextHeaders authentication $retHandle
        if {[info exists userArgsArray(ipv6_auth_seq_num)]} {::sth::sthCore::invoke stc::config $retHandle "-seqNum $userArgsArray(ipv6_auth_seq_num)"}
        if {[info exists userArgsArray(ipv6_auth_spi)]} {::sth::sthCore::invoke stc::config $retHandle "-spi $userArgsArray(ipv6_auth_spi)"}
        if {[info exists userArgsArray(ipv6_auth_payload_len)]} {::sth::sthCore::invoke stc::config $retHandle "-length $userArgsArray(ipv6_auth_payload_len)"}
        if {[info exists userArgsArray(ipv6_auth_string)]} {
            regsub -all {:|\.} $userArgsArray(ipv6_auth_string) "" ipv6_auth_string
            #check the ipv6_auth_string format: 32-bit hexadecimal value
            if {[string length $ipv6_auth_string] == 8 && [regexp {[[:xdigit:]]{8}} $ipv6_auth_string]} {
               ::sth::sthCore::invoke stc::config $retHandle "-authData $ipv6_auth_string"
            } else {
                set errorString "ipv6_auth_string has invalid format, it must be a 32-bit hexadecimal value. Current ipv6_auth_string value is: $ipv6_auth_string ";
                ::sth::sthCore::log debug "$_procName: $errorString "
                return -code 1 -errorcode -1 $errorString;
            }           
        }
    }
        
    # Add the header to the stream Handle array. This will be useful at the time of modify        
    set ::$mns\::arraystreamIpv6NextHeadersHnd([set ::$mns\::handleCurrentStream]) $listOfIpv6NextHeaders
    return ::sth::sthCore::SUCCESS;

}

proc ::sth::Traffic::processCreateModifyIpv4HeaderOptions {} {
    set _procName "processCreateModifyIpv4HeaderOptions";
    
    upvar userArgsArray userArgsArray
    upvar trafficKeyedList trafficKeyedList
    upvar mns mns;
    set configFlag 0
    if { [regexp -nocase "modify" $userArgsArray(mode)]} {
        if {[info exists ::$mns\::arraystreamIpv4RouterAlertHeadersHnd([set ::$mns\::handleCurrentStream])]} {
            set h_ip [::sth::sthCore::invoke "stc::get [set ::$mns\::handleCurrentStream] -children-ipv4:IPv4"]
            set options [::sth::sthCore::invoke "stc::get $h_ip -children-options"]
            set ipv4headeroption [::sth::sthCore::invoke "stc::get  $options -children-IPv4HeaderOption"]
            set iprouteralert [::sth::sthCore::invoke "stc::get $ipv4headeroption -children-rtrAlert"]
            set configFlag 1
        }
    }
    if {[regexp -nocase "router_alert" $userArgsArray(ipv4_header_options)] && ([regexp -nocase "create" $userArgsArray(mode)] || ![info exists ::$mns\::arraystreamIpv4RouterAlertHeadersHnd([set ::$mns\::handleCurrentStream])])} {
        if { [info exists userArgsArray(ip_router_alert)] && $userArgsArray(ip_router_alert) == 1} {
            #add routeralert for ipv4 header
            set streamblock [set ::$mns\::handleCurrentStream]

            if {[catch {
            set h_ip [::sth::sthCore::invoke "stc::get $streamblock -children-ipv4:IPv4"]
            set options [::sth::sthCore::invoke "stc::create options -under $h_ip"]
            set ipv4headeroption [::sth::sthCore::invoke "stc::create IPv4HeaderOption -under $options"]
            set iprouteralert [::sth::sthCore::invoke "stc::create rtrAlert -under $ipv4headeroption"]
            set ::$mns\::arraystreamIpv4RouterAlertHeadersHnd([set ::$mns\::handleCurrentStream]) $iprouteralert
            } errorString]} {
                ::sth::sthCore::log debug "$_procName: $errorString "
                return -code 1 -errorcode -1 $errorString;
            } 
            set configFlag 1
        } else {
            set errorString "router_alert valid only when ip_router_alert 1";
            ::sth::sthCore::log debug "$_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        }
    }
        
    if {$configFlag} {
        if { [info exists userArgsArray(ipv4_router_alert)] } {
            #parse ipv4_router_alert
            set routeralertsetting ""
            if {[regexp {optiontype:\s*(\w+)?\s*} $userArgsArray(ipv4_router_alert) tmp type]} {
                if {[regexp -nocase "end_of_options_list" $type]} {
                    set typevalue 0
                } elseif {[regexp -nocase "nop" $type]} {
                    set typevalue 1
                } elseif {[regexp -nocase "security" $type]} {
                    set typevalue 130
                } elseif {[regexp -nocase "loose_source_route" $type]} {
                    set typevalue 131
                } elseif {[regexp -nocase "time_stamp" $type]} {
                    set typevalue 68
                } elseif {[regexp -nocase "extended_security" $type]} {
                    set typevalue 133
                } elseif {[regexp -nocase "record_route" $type]} {
                    set typevalue 7
                } elseif {[regexp -nocase "stream_identifier" $type]} {
                    set typevalue 136
                } elseif {[regexp -nocase "strict_source_route" $type]} {
                    set typevalue 137
                } elseif {[regexp -nocase "mtu_probe" $type]} {
                    set typevalue 11
                } elseif {[regexp -nocase "mtu_reply" $type]} {
                    set typevalue 12
                } elseif {[regexp -nocase "traceroute" $type]} {
                    set typevalue 82
                } elseif {[regexp -nocase "address_extension" $type]} {
                    set typevalue 147
                } elseif {[regexp -nocase "router_alert" $type]} {
                    set typevalue 148
                } elseif {[regexp -nocase "selective_directed_broadcast_mode" $type]} {
                    set typevalue 149 
                } else {
                        set errorString "router_alert has invalid alert type, the possible values are end_of_options_list,
                            nop,security,loose_source_route,time_stamp,extended_security,record_route,stream_identifier,
                            strict_source_route,mtu_probe,mtu_reply,traceroute,address_extension,router_alert and 
                            selective_directed_broadcast_mode. Current type value is: $type";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                        return -code 1 -errorcode -1 $errorString;
                }
                ::sth::sthCore::invoke "stc::config $iprouteralert -type $typevalue" 
            }
            if {[regexp {length:\s*(\w+)?\s*} $userArgsArray(ipv4_router_alert) tmp length]} {
                ::sth::sthCore::invoke "stc::config $iprouteralert -length $length"
            }
            if {[regexp {routeralertvalue:\s*(\w+)?\s*} $userArgsArray(ipv4_router_alert) tmp routerAlert]} {
                ::sth::sthCore::invoke "stc::config $iprouteralert -routerAlert $routerAlert"
            }
        }
    }
    return ::sth::sthCore::SUCCESS;
}


proc ::sth::Traffic::processCreateRtp {} {
    
    set _procName "processCreateL4Protocol";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar l4Header l4Header;
    variable arrayHeaderLists;
    variable l4HeaderType;
    
     #create rtp header over the udp header
        if {[set ::$mns\::handleCurrentHeader] == 0} {
            #create the first 2 bytes
            #ver p x  cc               M     PT
            #10  0 0  rtp_csrc_count   0     rtp_payload_type
            set hexValue "8"
            if {[info exists userArgsArray(rtp_csrc_count)]} {
               set ccValue $userArgsArray(rtp_csrc_count)
            } else {
               set ccValue 0
            }
            set ccbValue [sth::Traffic::decimal2binary $ccValue 4];
            set cchexValue [::sth::sthCore::binToHex $ccbValue]
            set cchexValue [string range $cchexValue 1 1]
            set hexValue "$hexValue$cchexValue"
            if {[info exists userArgsArray(rtp_payload_type)]} {
               set ptValue $userArgsArray(rtp_payload_type)
            } else {
               set ptValue 18
            }
            set ptValue [sth::Traffic::decimal2binary $ptValue 8];
            set pthexValue [::sth::sthCore::binToHex $ptValue]
            
            set hexValue "$hexValue$pthexValue"

            if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $hexValue -name RTP_PT"} retHandle]} {
                return $::sth::sthCore::FAILURE;
            } else {
               ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
            }
            
            #create the sequencer number filed
            if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern {0000} -name RTP_Seq"} retHandle]} {
                return $::sth::sthCore::FAILURE;
            } else {
               ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
            }
            
            set optionList "-mask {FFFF} -stepvalue {0001} -RecycleCount 65535 -Data {0000} -OffsetReference {RTP_Seq.pattern}"
            ::sth::sthCore::invoke stc::create RangeModifier -under [set ::$mns\::handleCurrentStream] $optionList
            
            #create timestamp filed
            if {[info exists userArgsArray(timestamp_initial_value)]} {
               set timeValue $userArgsArray(timestamp_initial_value)
               set timeValue [sth::Traffic::decimal2binary $timeValue 32];
               set timeValue [::sth::sthCore::binToHex $timeValue]
            } else {
               set timeValue "00000000"
            }
            
            if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $timeValue -name RTP_TimeStamp"} retHandle]} {
                #puts "error while processing rtp header";
                return $::sth::sthCore::FAILURE;
            } else {
               ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
            }
            
            if {[info exists userArgsArray(timestamp_increment)]} {
               set timeStep $userArgsArray(timestamp_increment)
               set timeStep  [sth::Traffic::decimal2binary $timeStep 16];
               set timeStep  [::sth::sthCore::binToHex $timeStep]
            } else {
               set timeStep "0040"
            }
    
            set optionList "-mask {FFFFFFFF} -stepvalue $timeStep -RecycleCount 4294967295 -Data $timeValue -OffsetReference {RTP_TimeStamp.pattern} -name {RTP_TimeStamp}"
            ::sth::sthCore::invoke stc::create RangeModifier -under [set ::$mns\::handleCurrentStream] $optionList
            
            #create ssrc filed
            if {[info exists userArgsArray(ssrc)]} {
               set ssrcValue $userArgsArray(ssrc)
               set ssrcValue  [sth::Traffic::decimal2binary $ssrcValue 32];
               set ssrcValue  [::sth::sthCore::binToHex $ssrcValue]
            } else {
               set ssrcValue "4a48dd38"
            }
            
            if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $ssrcValue -name RTP_ssrc"} retHandle]} {
                #puts "error while processing rtp header";
                return $::sth::sthCore::FAILURE;
            } else {
               ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
            }
            
            #create the ccrc filed
            for {set i 0} {$i<$ccValue} {incr i} {
                if {![info exists userArgsArray(csrc_list)]} {
                    #puts "Please provide the csrc_list when rtp_csrc_count is not equal to 0";
                    return $::sth::sthCore::FAILURE;
                } else {
                    set csrcList $userArgsArray(csrc_list)
                    if {$ccValue != [llength $csrcList]} {
                        #puts "Warning! the item count in csrc_list is not equal to rtp_csrc_count";
                    }
                 
                    set  csrc [lindex $csrcList $i]
                    set csrcValue  [sth::Traffic::decimal2binary $csrc 32];
                    set csrcValue  [::sth::sthCore::binToHex $csrcValue]
                       
                    if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $csrcValue -name RTP_csrc$i"} retHandle]} {
                        #puts "error while processing rtp header";
                        return $::sth::sthCore::FAILURE;
                    } else {
                        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                    }
                }
            }
            
            # update l4Header
            set retHandle [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] "-children-custom:Custom"]
        foreach headerHandle $retHandle {
                set headerName [::sth::sthCore::invoke stc::get $headerHandle -name];
                if {[regexp {RTP_PT||RTP_Seq||RTP_TimeStamp||RTP_ssrc||RTP_csrc} $headerName]} {
                        lappend l4Header $headerHandle
                }
            }
            
            
        } else {
        # modify mode
            set streamHandle [set ::$mns\::handleCurrentStream]
            set headerHnds [::sth::sthCore::invoke stc::get $streamHandle "-children-custom:custom"]
            
            foreach header $headerHnds {
                if {[::sth::sthCore::invoke stc::get $header -name] == "RTP_PT"} {
                   set ptHand $header
                }
                if {[::sth::sthCore::invoke stc::get $header -name] == "RTP_TimeStamp"} {
                   set timeHand $header
                }
                
            }
            
            set hexvalue [::sth::sthCore::invoke stc::get $ptHand -pattern]
            set ccValue [string range $hexvalue 0 1]
            set ptValue [string range $hexvalue 2 3]
            
            if {[info exists userArgsArray(rtp_csrc_count)]} {
               set ccValue $userArgsArray(rtp_csrc_count)
               set ccValue [sth::Traffic::decimal2binary $ccValue 4];
               set ccValue [::sth::sthCore::binToHex $ccValue]
               set ccValue [string range $ccValue 1 1]
               set ccValue "8$ccValue"
            } 
           
            if {[info exists userArgsArray(rtp_payload_type)]} {
               set ptValue $userArgsArray(rtp_payload_type)
               set ptValue [sth::Traffic::decimal2binary $ptValue 8];
               set ptValue [::sth::sthCore::binToHex $ptValue]
            }
            set hexvalue "$ccValue$ptValue"
            ::sth::sthCore::invoke stc::config $ptHand "-pattern $hexvalue"
            
            if {[info exists userArgsArray(timestamp_initial_value)]} {
                set timeValue $userArgsArray(timestamp_initial_value)
                set timeValue [sth::Traffic::decimal2binary $timeValue 32];
                set timeValue [::sth::sthCore::binToHex $timeValue]
                ::sth::sthCore::invoke stc::config $timeHand "-pattern $timeValue"
            }
            
            if {[info exists userArgsArray(timestamp_increment)]} {
                set timeStep $userArgsArray(timestamp_increment)
                set timeStep  [sth::Traffic::decimal2binary $timeStep 16];
                set timeStep  [::sth::sthCore::binToHex $timeStep]
                set rangeHnds [::sth::sthCore::invoke stc::get $streamHandle "-children-RangeModifier"]
                foreach hnd $rangeHnds {
                   if {[::sth::sthCore::invoke stc::get $hnd -name] == "RTP_TimeStamp"} {
                       ::sth::sthCore::invoke stc::config $hnd "-stepvalue $timeStep"
                   }
                }
            }
            
            if {[info exists userArgsArray(rtp_csrc_count)]} {
                foreach header $headerHnds {
                    set name [::sth::sthCore::invoke stc::get $header -name]
                    if {[regexp "RTP_csrc" $name]} {
                        ::sth::sthCore::invoke stc::delete $header
                    }
                }
                
                if {![info exists userArgsArray(csrc_list)]} {
                        #puts "Please provide the csrc_list when rtp_csrc_count is not equal to 0";
                        return $::sth::sthCore::FAILURE;
                } else {
                        set csrcList $userArgsArray(csrc_list)
                        if {$userArgsArray(rtp_csrc_count) != [llength $csrcList]} {
                             #puts "Warning! the item count in csrc_list is not equal to rtp_csrc_count";
                        }
                }
                
                for {set i 0} {$i<$userArgsArray(rtp_csrc_count)} {incr i} {
                    
                        set  csrc [lindex $csrcList $i]
                        set csrcValue  [sth::Traffic::decimal2binary $csrc 32];
                        set csrcValue  [::sth::sthCore::binToHex $csrcValue]
                       
                        if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $csrcValue -name RTP_csrc$i"} retHandle]} {
                            #puts "error while processing rtp header";
                            return $::sth::sthCore::FAILURE;
                        } else {
                             ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
                        }
                }
            }
            
        }
    
}


proc ::sth::Traffic::processCreateIsis {} {
    
    set _procName "processCreateIsis";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar l4Header l4Header;
    variable arrayHeaderLists;
    variable l4HeaderType;
    
    
    #prepare the parameters to config L1 hello frame filed
    set l1HelloParamList {isis_pdu_header_len 00 isis_version 01 isis_system_id_len 00 isis_pdu_type 0f isis_version2 01 isis_reserved 00 \
                        isis_max_area_addr 00 isis_reserved_circuit_type 01 isis_source_id 000001000001 isis_holder_timer 001e \
                        isis_pdu_len 0000}
    set isisTyp "83"
    set l1HelloFrame "$isisTyp"
       
    #create the custom pattern list
    append l1HelloFrame [::sth::Traffic::processConstructCustomPattern "ISIS_L1Hello" $l1HelloParamList]
    #handle the reserved_bit and priority to create one byte
    if {![info exists userArgsArray(isis_lan_id)]} {
        set userArgsArray(isis_lan_id) "$userArgsArray(isis_source_id)ff"
    }
    if {![info exists userArgsArray(isis_reserved_bit)]} {
        set rBit 0
    } else {
        set rBit $userArgsArray(isis_reserved_bit)
    }
    if {![info exists userArgsArray(isis_priority)]} {
        set priority 0000000
    } else {
        set priority $userArgsArray(isis_priority)
    }
    
    set bitPriority "$rBit$priority"
    set bitPriorityHex [::sth::sthCore::binToHex $bitPriority]
    #check the length of bitPriorityHex
    if {![regexp {^[0-1]{8}$} $bitPriority]} {
         set errorString "Configuration Error for isis_reserved_bit and isis_priority: It should be 1 byte length of the combined two parameters.";
        ::sth::sthCore::log debug "$_procName: $errorString "
        return -code 1 -errorcode -1 $errorString;
    }
    append l1HelloFrame $bitPriorityHex
    append l1HelloFrame $userArgsArray(isis_lan_id)
    
    
    #create/modify the custom header        
    if {[set ::$mns\::handleCurrentHeader] == 0} {
        #create mode
        #create the first 3 bytes to make up llc part
        set dsap "fe"
        set ssap "fe"
        set controlField "03"
        set llcHexValue "$dsap$ssap$controlField"

        if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $llcHexValue -name ISIS_Llc"} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
           ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
        
        #create the custom for l1 hello frame with the parameters configured in upper code.
        if {[catch {::sth::sthCore::invoke stc::create custom:Custom -under [set ::$mns\::handleCurrentStream] "-pattern $l1HelloFrame -name ISIS_L1Hello"} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
           ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
        
        # update l4Header
        set retHandle [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] "-children-custom:Custom"]
        foreach headerHandle $retHandle {
            set headerName [::sth::sthCore::invoke stc::get $headerHandle -name];
            if {[regexp {ISIS_Llc||ISIS_L1Hello} $headerName]} {
                    lappend l4Header $headerHandle
            }
        }
         # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        }
        
        lappend listOfHeaders "l4_header";
        lappend listOfHeaders "$l4Header";
    
        set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
    
    } else {
        # modify mode
        set streamHandle [set ::$mns\::handleCurrentStream]
        set headerHnds [::sth::sthCore::invoke stc::get $streamHandle "-children-custom:custom"]
        
        foreach header $headerHnds {
            if {[::sth::sthCore::invoke stc::get $header -name] == "ISIS_L1Hello"} {
               set l1HelloFrameHdl $header
            } 
        }
        
        ::sth::sthCore::invoke stc::config $l1HelloFrameHdl "-pattern $l1HelloFrame"

    }
    
}


#get the confgured value of custom pattern param and update the arraystreamCustomParam
proc ::sth::Traffic::processConstructCustomPattern {customNam defaultParams} {
    set _procName "processConstructCustomPattern";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    set framList ""
    set paramList ""
    
    #check if the parameter has been configured under current stream
    if {[info exists ::$mns\::arraystreamCustomParam([set ::$mns\::handleCurrentStream])]} {
        set customList [set ::$mns\::arraystreamCustomParam([set ::$mns\::handleCurrentStream])]
        set pos [lsearch $customList $customNam]
        set paramList [lindex $customList [expr $pos + 1]]
        if {$paramList != ""} {
            foreach {param val} $paramList {
                if {![info exists userArgsArray($param)]} { 
                    set userArgsArray($param) $val
                }
            }
        }
        
        #update the arraystreamCustomParam
        foreach param [set ::$mns\::listl4Headerisis] {
            set p [lsearch $paramList $param] 
            if {$p < 0} {
                lappend paramList $param $userArgsArray($param)
            } else {
                #replace the original value
                set paramList [lreplace $paramList [expr $p + 1] [expr $p + 1] $userArgsArray($param)]
            }
        }
        set ::$mns\::arraystreamCustomParam([set ::$mns\::handleCurrentStream]) [lreplace [set ::$mns\::arraystreamCustomParam([set ::$mns\::handleCurrentStream])] [expr $pos + 1] [expr $pos + 1] $paramList]
    } else {
        set customValueList ""
        set ValueList ""
        foreach param [set ::$mns\::listl4Headerisis] {
            lappend ValueList $param $userArgsArray($param)
        }
        lappend customValueList $customNam $ValueList
        set ::$mns\::arraystreamCustomParam([set ::$mns\::handleCurrentStream]) $customValueList
    }
    
    
    
    #create a list as the custom pattern frame
    #get the default value of the isis L1 hello frame parameter
    foreach {param defaultVal} $defaultParams {
        if {![info exists userArgsArray($param)]} {
            switch -exact $param {
                "isis_source_id" {
                    if {[info exists userArgsArray(mac_src)]} {
                        set userArgsArray($param) [regsub -all {[\.]|[\:]|[\-]} $userArgsArray(mac_src) {}]
                    } else {
                        set userArgsArray($param) $defaultVal
                    }
                }
                default {
                    set userArgsArray($param) $defaultVal
                }
            }
        }
        append framList $userArgsArray($param)
    }
    
    return $framList
}
    

proc ::sth::Traffic::processCreateL4Protocol {} {
    
    set _procName "processCreateL4Protocol";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    
    variable arrayHeaderLists;
    variable l4HeaderType;
    variable l4Header;
    
    # if the l4_protocol is isis, call the function processCreateIsis to handle the custom header
    if {$userArgsArray(l4_protocol) == "isis"} {
        if {[catch {::$mns\::processCreateIsis} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
        return ::sth::sthCore::SUCCESS;
    }
    
    set headerSet $arrayHeaderLists($l4HeaderType);
    set headerToCreate [lindex $headerSet 0];
    set listsToUse [lindex $headerSet 1];
    set listArgsList {};
    
    
    foreach List $listsToUse {
        foreach element [set ::$mns\::$List] {
            # MOD Cheng Fei 08-10-13
            # use   to create icmp header
            if {$element == "icmp_type"} {
                 if {[catch {::sth::Traffic::processCreateIcmpHeader ::$mns\::handleCurrentStream $List} retHandle]} {
                    ::sth::sthCore::processError trafficKeyedList "$_procName:Error while processing icmp header."
                    return $::sth::sthCore::FAILURE
                 } else {
                     return ::sth::sthCore::SUCCESS;
                 }
            }
            if {$element == "icmpv6_type"} {
                 if {[catch {::sth::Traffic::processCreateIcmpv6Header ::$mns\::handleCurrentStream $List} retHandle]} {
                    ::sth::sthCore::processError trafficKeyedList "$_procName:Error while processing icmpv6 header."
                    return $::sth::sthCore::FAILURE
                 } else {
                     return ::sth::sthCore::SUCCESS;
                 }
            }
            if {$element == "igmp_version"} {
                 if {[catch {::sth::Traffic::processCreateIgmpHeader ::$mns\::handleCurrentStream $List} errMsg]} {
                    ::sth::sthCore::processError trafficKeyedList "$_procName:$errMsg"
                    return $::sth::sthCore::FAILURE
                 } else {
                     return ::sth::sthCore::SUCCESS;
                 }
            }
            #end
            set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
            ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
            lappend listArgsList -$stcAttr $userArgsArray($element);
        }
    }
    
    if {[set ::$mns\::handleCurrentHeader] == 0} {
        # we would have to create the header irrespective of the mode.
        
        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerToCreate [set ::$mns\::handleCurrentStream] $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::create $headerToCreate -under [set ::$mns\::handleCurrentStream] $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
        
        if {$userArgsArray(l4_protocol) == "rtp"} {
            lappend l4HeaderToCreate $headerToCreate
            if {[catch {::$mns\::processCreateRtp;} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            } 
        }
        #As the retHandle will change after excuting "::stc::apply", so the retHandle created above should be gotten again
        ::sth::sthCore::log debug "$_procName: Calling stc::get [set ::$mns\::handleCurrentStream] -children-$headerToCreate"
        set cmdName "::sth::sthCore::invoke ::stc::get [set ::$mns\::handleCurrentStream] -children-$headerToCreate";
        if {[catch {eval $cmdName} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::get Success. Handle is $retHandle";
        }
        
        # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        }

        lappend l4Header [lindex $retHandle end];
        lappend listOfHeaders "l4_header";
        lappend listOfHeaders "$l4Header";
        
        set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
        
    } else {
        # if this is not 0 that means this has to be mode modify and header was created earlier.
        
        set currentHeader [set ::$mns\::handleCurrentHeader];
        set value_list [split $currentHeader " "]
        set headerToConfigure [lindex $value_list end]
        
        set streamHandle [set ::$mns\::handleCurrentStream]
        #set length [string length $headerToConfigure]
        #set index [expr $length - 2]
        #set objectName [string range $headerToConfigure 0 $index]
        if { [string match *udp* $headerToConfigure]} {
            set objectName udp:udp
        } elseif { [string match *ipv4* $headerToConfigure]} {
            set objectName ipv4:ipv4
        } elseif { [string match *ipv6* $headerToConfigure]} {
            set objectName ipv6:ipv6
        } else {
            regsub -all {\d+$} $headerToConfigure "" objectName
        }

        set headerToConfigure [lindex [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName] end]

        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while configuring $headerToConfigure";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
        }
        set retHandle $headerToConfigure
        
        if {$userArgsArray(l4_protocol) == "rtp"} {
            if {[catch {::$mns\::processCreateRtp;} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
    }
    
    # Check if modifier is needed here.
    # This is layer 4 header. 
    if {[llength [set ::$mns\::listTcpPortSrcRangeModifier]]} {
        ::sth::Traffic::processCreateL4RangeModifier $retHandle listTcpPortSrcRangeModifier sourcePort;
    }
    if {[llength [set ::$mns\::listTcpPortDstRangeModifier]]} {
        ::sth::Traffic::processCreateL4RangeModifier $retHandle listTcpPortDstRangeModifier destPort;
    }
    if {[llength [set ::$mns\::listUdpPortSrcRangeModifier]]} {
        ::sth::Traffic::processCreateL4RangeModifier $retHandle listUdpPortSrcRangeModifier sourcePort;
    }
    if {[llength [set ::$mns\::listUdpPortDstRangeModifier]]} {
        ::sth::Traffic::processCreateL4RangeModifier $retHandle listUdpPortDstRangeModifier destPort;
    }
    if {[llength [set ::$mns\::listl4DstRangeModifier]]} {
        ::sth::Traffic::processCreateL4RangeModifier [lindex $retHandle end] listl4DstRangeModifier destAddr;
    }
    if {[llength [set ::$mns\::listl4SrcRangeModifier]]} {
        ::sth::Traffic::processCreateL4RangeModifier [lindex $retHandle end] listl4SrcRangeModifier sourceAddr;
    }

    ###########################################
    # Handle L3 Qos bits
    ###########################################
    if {[llength [set ::$mns\::listl4QosBits]]} {
        # TODO: put a catch here later
        if {[catch {::sth::Traffic::processCreateQosHeader [lindex $retHandle end] listl4QosBits} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
            return -code error $trafficKeyedList;
        }
    }

    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processCreateVxlan {} {
    set _procName "processCreateVxlan";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar x x 
    #create vxlan header
    set listArgsList {};
    foreach element [set ::$mns\::listVxlanHeader] {
        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
        lappend listArgsList -$stcAttr $userArgsArray($element);
    }

    if {$userArgsArray(mode) == "create"} {
        ::sth::sthCore::invoke ::stc::create vxlan:VxLAN -under [set ::$mns\::handleCurrentStream] $listArgsList
        #create ethernet header
       
        if {[catch {::$mns\::processCreateL2Encap $_procName} procStatus]} {
            ::sth::sthCore::processError trafficKeyedList $procStatus {}
            return -code 1 -errorcode -1 $procStatus;
        }
        
        #create ipv4 header
        if {[info exists userArgsArray(inner_l3_protocol)]} {
            set ::$mns\::l3HeaderType inner_ipv4;
            if {[catch {::$mns\::processCreateL3Protocol} procStatus]} {
                ::sth::sthCore::processError trafficKeyedList $procStatus {}
                return -code 1 -errorcode -1 $procStatus;
            }
        }
    } else {
        #modify the vxlan
        set vxlan [::sth::sthCore::invoke ::stc::get [set ::$mns\::handleCurrentStream] -children-vxlan:VxLAN]
        ::sth::sthCore::invoke ::stc::config $vxlan $listArgsList
    }
}
proc ::sth::Traffic::decimal2binary {i {bits {}}} {
    set res "";
    while {$i>0} {
        set res [expr {$i%2}]$res;
        set i [expr {$i/2}];   
    }
    if {$res==""} {
        set res 0;
    }
    if {$bits != {} } {
        append d [string repeat 0 $bits ] $res
        set res [string range $d [string length $res ] end ]
    }
    
    split $res ""
    return $res;
 }
 
proc ::sth::Traffic::processCreateIgmpHeader {Handle listName} {
    
    set _procName "processCreateIgmpHeader";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    set listArgsList {};
    set attrList [set ::$mns\::$listName];
    set maxnum 0;
    set listArgsList_GrpRecord {};
    foreach element $attrList {
            if {$element == "igmp_version"} {
                switch -exact $userArgsArray($element) {
                  "1" {
                    set headerName "igmp:Igmpv1"
                  }
                   "2" {
                    if {[info exist userArgsArray(igmp_msg_type)]} {
                         if {$userArgsArray(igmp_msg_type) == "query"} {
                             set headerName "igmp:Igmpv2Query"
                         } elseif {$userArgsArray(igmp_msg_type) == "report"} {
                             set headerName "igmp:Igmpv2Report"
                         } else {
                                set errorString "igmp_msg_type should be specified either query or report, current value: $userArgsArray(igmp_msg_type)";
                                ::sth::sthCore::log debug "$_procName: $errorString "
                                return -code 1 -errorcode -1 $errorString;
                         }
                      } else {
                            set errorString "igmp_msg_type should be provided when igmp verison is 2";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                      } 
                  }
                  "3" {
                      if {[info exist userArgsArray(igmp_msg_type)]} {
                         if {$userArgsArray(igmp_msg_type) == "query"} {
                             set headerName "igmp:Igmpv3Query"
                         } elseif {$userArgsArray(igmp_msg_type) == "report"} {
                             set headerName "igmp:Igmpv3Report"
                         } else {
                                set errorString "igmp_msg_type should be specified either query or report, current value: $userArgsArray(igmp_msg_type)";
                                ::sth::sthCore::log debug "$_procName: $errorString "
                                return -code 1 -errorcode -1 $errorString;
                         }
                      } else {
                            set errorString "igmp_msg_type should be provided when igmp verison is 3";
                            ::sth::sthCore::log debug "$_procName: $errorString "
                            return -code 1 -errorcode -1 $errorString;
                      }
                      
                    }
                }
                continue
            }
            
            set stcObj [set ::$mns\::traffic_config_stcobj($element)];
            set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
            if { $stcObj == "igmp:igmp" || $stcObj == "igmp.groupAddress"}  {
                ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
                if {$stcAttr == "qrv" } {
                    if {$userArgsArray($element)<= 7} {
                        set qrv_value $::sth::Traffic::arrayDecimal2Bin($userArgsArray($element));
                        set qrv_value [string range $qrv_value 1 3]
                        lappend listArgsList -$stcAttr $qrv_value;
                        
                    }
                } else {
                    lappend listArgsList -$stcAttr $userArgsArray($element);
                }
            } elseif {$stcObj == "GroupRecord"} {
                set size [llength $userArgsArray($element)]
                array unset ::sth::Traffic::listArgsList_GrpRecord_$stcAttr
                for {set i 0} {$i < $size} {incr i} {
                    set myrecord [lindex $userArgsArray($element) $i]
                    set ::sth::Traffic::listArgsList_GrpRecord_$stcAttr\($i) "-$stcAttr $myrecord"
                }
                
                set maxnum [expr max($size, $maxnum)]
                lappend listArgsList_GrpRecord "$stcAttr"
                
            } elseif {$stcObj == "Ipv4Addr"} {
                set size [llength $userArgsArray($element)]
                array unset ::sth::Traffic::listArgsList_Ipv4Addr;
                for {set i 0} {$i < $size} {incr i} {
                    set myrecord [lindex $userArgsArray($element) $i]
                    set ::sth::Traffic::listArgsList_Ipv4Addr($i) [string trim $myrecord "\{\}"]
                }
                
                set maxnum [expr max($size, $maxnum)]
            } 
    }
      
    if {[set ::$mns\::handleCurrentHeader] == 0} {
        # we would have to create the header irrespective of the mode.
        
        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerName [set ::$mns\::handleCurrentStream] $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::create $headerName -under [set ::$mns\::handleCurrentStream] $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            set errorString "error while processing $headerName";
            ::sth::sthCore::log debug "$_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
        
        if {$headerName eq "igmp:Igmpv3Query"} {            
            for {set i 0} {$i < [array size ::sth::Traffic::listArgsList_Ipv4Addr]} {incr i} {              
                set myIpAddr [set ::sth::Traffic::listArgsList_Ipv4Addr($i)]
                set addList1 [::sth::sthCore::invoke "stc::create addrList -under $retHandle"]
                foreach element $myIpAddr {
                    set ipv4addr1 [::sth::sthCore::invoke "stc::create Ipv4Addr -under $addList1"]
                    ::sth::sthCore::invoke "stc::config $ipv4addr1 -value $element";
                }
                ::sth::sthCore::invoke "stc::config $retHandle -numSource [llength $myIpAddr]"
            }
        } elseif {$headerName eq "igmp:Igmpv3Report"} {
            if {$maxnum > 0} {
                set grphandle [::sth::sthCore::invoke "stc::create grpRecords -under $retHandle"]
                
                set grpRrdhandles [processIgmpv3Report $listArgsList_GrpRecord $maxnum $grphandle false]
                
                ::sth::sthCore::invoke "stc::config $retHandle -numGrpRecords $maxnum"
                ::sth::Traffic::processRetHandle igmpgrprec_handle $grpRrdhandles
            }
        }
                
        # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        }
        
        lappend listOfHeaders "l4_header";
        lappend listOfHeaders "[set retHandle]";
        set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
    } else {    
        # if this is not 0 that means this has to be mode modify and header was created earlier.
        
        set headerToConfigure [set ::$mns\::handleCurrentHeader];
                
        set streamHandle [set ::$mns\::handleCurrentStream]
        if {[regexp -nocase {igmp:Igmpv1(\d+)?$} $headerToConfigure]} {
            set objectName "igmp:Igmpv1"
        } elseif {[regexp -nocase {igmp:Igmpv2(\d+)?$} $headerToConfigure]} {
            set objectName "igmp:Igmpv2"
        } else {
            regsub -all {\d+$} $headerToConfigure "" objectName
        }
        set headerToConfigure [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
        
        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            set errorString "error while configuring $headerToConfigure";
            ::sth::sthCore::log debug "$_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        } else {
            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
        }
        set retHandle $headerToConfigure
        
        if {$headerName eq "igmp:Igmpv3Query"} {
             set addList1 [::sth::sthCore::invoke "stc::get $retHandle -children"]
            ::sth::sthCore::invoke "stc::delete $addList1"

            for {set i 0} {$i < [array size ::sth::Traffic::listArgsList_Ipv4Addr]} {incr i} {              
                set myIpAddr [set ::sth::Traffic::listArgsList_Ipv4Addr($i)]
                set addList1 [::sth::sthCore::invoke "stc::create addrList -under $retHandle"]
                foreach element $myIpAddr {
                    set ipv4addr1 [::sth::sthCore::invoke "stc::create Ipv4Addr -under $addList1"]
                    ::sth::sthCore::invoke "stc::config $ipv4addr1 -value $element";
                }
                ::sth::sthCore::invoke "stc::config $retHandle -numSource [llength $myIpAddr]"
            }
        } else {
            if {[info exist userArgsArray(igmpv3_grprechandle)]} {
                set grprecord $userArgsArray(igmpv3_grprechandle)
                set updatehdl [::sth::Traffic::processUpdateHandle $streamHandle $grprecord]
                processIgmpv3Report $listArgsList_GrpRecord $maxnum $updatehdl true
                
            } elseif {$maxnum > 0} {
                set grphandle [eval "::sth::sthCore::invoke ::stc::get $headerToConfigure -children"]
                set grpRrdhandles [processIgmpv3Report $listArgsList_GrpRecord $maxnum $grphandle false]
               
                set num [eval "::sth::sthCore::invoke ::stc::get $headerToConfigure -numGrpRecords"]
                ::sth::sthCore::invoke "stc::config $headerToConfigure -numGrpRecords [expr {$num+1}]"
               
                ::sth::Traffic::processRetHandle igmpgrprec_handle $grpRrdhandles
            }
        }
    }
    
    if {[llength [set ::$mns\::listIgmpGroupAddrRangeModifier]]} {
           ::sth::Traffic::processCreateL3RangeModifier $retHandle listIgmpGroupAddrRangeModifier groupAddress;
    }
    
    return ::sth::sthCore::SUCCESS;
}


proc ::sth::Traffic::processIgmpv3Report {listArgsList_GrpRecord num updateHandle modify} {

    set _procName "processIgmpv3Report";

    upvar userArgsArray userArgsArray;

    if {$modify && $num > 1} {
        set errorString "only can modify one group record in igmpv3 report message";
        ::sth::sthCore::log debug "processIgmpv3Report: $errorString "
        return -code 1 -errorcode -1 $errorString;
    }
    
    set grpRrdhandles ""
    for {set i 0} {$i < $num} {incr i} {
        if {$modify} {
            set grpRrdhandle $updateHandle
        } else {
            set grpRrdhandle [::sth::sthCore::invoke "stc::create GroupRecord -under $updateHandle"]
        }
        
        foreach argElement $listArgsList_GrpRecord {
            if {$i < [array size ::sth::Traffic::listArgsList_GrpRecord_$argElement]} {
                set oneAttr [set ::sth::Traffic::listArgsList_GrpRecord_$argElement\($i)]
                ::sth::sthCore::invoke "stc::config $grpRrdhandle $oneAttr"
            } elseif {[regexp -nocase "mcastAddr" $argElement]} {
                ::sth::sthCore::invoke "stc::config $grpRrdhandle -mcastAddr \"255.0.0.1\""
            }
        }
        
        if {![info exist userArgsArray(igmp_multicast_addr)]} {
             ::sth::sthCore::invoke "stc::config $grpRrdhandle -mcastAddr \"255.0.0.1\""
        }
        
        if {$i < [array size ::sth::Traffic::listArgsList_Ipv4Addr]} {
            if {$modify} {
                set addList1 [::sth::sthCore::invoke "stc::get $grpRrdhandle -children"]
                ::sth::sthCore::invoke "stc::delete $addList1"
            }
            
            set myIpAddr [set ::sth::Traffic::listArgsList_Ipv4Addr($i)]
            set addList1 [::sth::sthCore::invoke "stc::create addrList -under $grpRrdhandle"]
            foreach element $myIpAddr {
                set ipv4addr1 [::sth::sthCore::invoke "stc::create Ipv4Addr -under $addList1"]
                ::sth::sthCore::invoke "stc::config $ipv4addr1 -value $element";
            }
            ::sth::sthCore::invoke "stc::config $grpRrdhandle -numSource [llength $myIpAddr]"
        }
        
        lappend grpRrdhandles $grpRrdhandle
    }
    
    return $grpRrdhandles
}



proc ::sth::Traffic::processCreateIcmpv6Header {Handle listName} {
    
    set _procName "processCreateIcmpv6Header";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    set listArgsList {};
    set ipDataArgsList {};
    set ipHdrArgsList {};
    set linkLayerArgsList {};
    set mtuArgsList {};
    set prefixArgsList {};
    set redirectArgsList {};
    set addrListArgsList {};
    set grpRecordArgsList {};
    set redirectFlag 0;
    set mldv2GroupRecordFlag 0;
    set attrList [set ::$mns\::$listName];
    
    foreach element $attrList {
            if {$element == "icmpv6_type"} {
                switch -exact $userArgsArray($element) {
                  "1" {
                    set headerName "icmpv6:Icmpv6DestUnreach"
                  }
                  "2" {
                    set headerName "icmpv6:Icmpv6PacketTooBig"
                  }
                  "3" {
                    set headerName "icmpv6:Icmpv6TimeExceeded"
                  }
                  "4" {
                    set headerName "icmpv6:Icmpv6ParameterProblem"
                  }
                  "128" {
                    set headerName "icmpv6:Icmpv6EchoRequest"
                  }
                  "129" {
                    set headerName "icmpv6:Icmpv6EchoReply"
                  }
                  "131" - "132" {
                    set headerName "icmpv6:MLDv1"
                  }
                  "130" {
                    #130    MLDv1 Query
                    set headerName "icmpv6:MLDv2Query"
                  }
                  "143" {
                    set headerName "icmpv6:MLDv2Report"
                    set mldv2GroupRecordFlag 1
                  }
                  "133" {
                    set headerName "icmpv6:RouterSolicitation"
                  }
                  "134" {
                    set headerName "icmpv6:RouterAdvertisement"
                  }
                  "135" {
                    set headerName "icmpv6:NeighborSolicitation"
                  }
                  "136" {
                    set headerName "icmpv6:NeighborAdvertisement"
                  }
                  "137" {
                    set headerName "icmpv6:Redirect"
                    set redirectFlag 1
                  }
                }
            }
            set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
            set stcObj [set ::$mns\::traffic_config_stcobj($element)];
            ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
            if {$stcObj == "icmpv6:ipData"} {
                lappend ipDataArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "ipData:ipHdr"} {
                lappend ipHdrArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "linkLayerOption:LinkLayerAddress"} {
                lappend linkLayerArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "mtuOption:MTU"} {
                lappend mtuArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "prefixOption:PrefixInformation"} {
                lappend prefixArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "redirectedHdrOption:RedirectedHeader"} {
                lappend redirectArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "grpRecords:MLDv2GroupRecord"} {
                lappend grpRecordArgsList -$stcAttr $userArgsArray($element);
            } elseif {$stcObj == "addrList:Ipv6Addr"} {
                lappend addrListArgsList -$stcAttr $userArgsArray($element);
            } else {
                lappend listArgsList -$stcAttr $userArgsArray($element);
            }
    }
    
     if {[set ::$mns\::handleCurrentHeader] == 0} {
        # we would have to create the header irrespective of the mode.
        
        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerName [set ::$mns\::handleCurrentStream] $listArgsList"
        set retHandle [::sth::sthCore::invoke ::stc::create $headerName -under [set ::$mns\::handleCurrentStream] $listArgsList]

        if {[llength $ipDataArgsList] != 0 && $redirectFlag == 0} {
            set ipDataHnd [::sth::sthCore::invoke stc::create ipData -under $retHandle $ipDataArgsList]
            set ipHdrHnd [::sth::sthCore::invoke stc::create ipHdr -under $ipDataHnd $ipHdrArgsList]
        }
        if {[llength $linkLayerArgsList] != 0} {
            set linkLayerOptionHnd [::sth::sthCore::invoke stc::create linkLayerOption -under $retHandle]
            set linkLayerAddressHnd [::sth::sthCore::invoke stc::create LinkLayerAddress -under $linkLayerOptionHnd $linkLayerArgsList]
        }
        if {[llength $mtuArgsList] != 0} {
            set mtuOptionHnd [::sth::sthCore::invoke stc::create mtuOption -under $retHandle]
            set mtuHnd [::sth::sthCore::invoke stc::create MTU -under $mtuOptionHnd $mtuArgsList]
        }
        if {[llength $prefixArgsList] != 0} {
            set prefixOptionHnd [::sth::sthCore::invoke stc::create prefixOption -under $retHandle]
            set prefixHnd [::sth::sthCore::invoke stc::create PrefixInformation -under $prefixOptionHnd $prefixArgsList]
        }
        if {[llength $redirectArgsList] != 0} {
            set redirectOptionHnd [::sth::sthCore::invoke stc::create redirectedHdrOption -under $retHandle]
            set redirectHnd [::sth::sthCore::invoke stc::create RedirectedHeader -under $redirectOptionHnd $redirectArgsList]
            set ipDataHnd [::sth::sthCore::invoke stc::create ipData -under $redirectHnd $ipDataArgsList]
            set ipHdrHnd [::sth::sthCore::invoke stc::create ipHdr -under $ipDataHnd $ipHdrArgsList]
        }
        if {[llength $addrListArgsList] != 0 && $mldv2GroupRecordFlag == 0} {
            set addrListHnd [::sth::sthCore::invoke stc::create addrList -under $retHandle]
            set ipv6AddrHnd [::sth::sthCore::invoke stc::create Ipv6Addr -under $addrListHnd $addrListArgsList]
        }

        if {[llength $grpRecordArgsList] != 0} {
            set grpRecordsHnd [::sth::sthCore::invoke stc::create grpRecords -under $retHandle]
            set mldv2GroupRecordHnd [::sth::sthCore::invoke stc::create MLDv2GroupRecord -under $grpRecordsHnd $grpRecordArgsList]
            set addrListHnd [::sth::sthCore::invoke stc::create addrList -under $mldv2GroupRecordHnd]
            set ipv6AddrHnd [::sth::sthCore::invoke stc::create Ipv6Addr -under $addrListHnd $addrListArgsList]
        }
        
        # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        }
        
        lappend listOfHeaders "l4_header";
        lappend listOfHeaders "[set retHandle]";
        set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
        
    } else {    
        # if this is not 0 that means this has to be mode modify and header was created earlier.
        set headerToConfigure [set ::$mns\::handleCurrentHeader];
        
        set streamHandle [set ::$mns\::handleCurrentStream]
        if { [regexp "mldv1" [string tolower $headerToConfigure]]} {
            set objectName "icmpv6:MLDv1"
        } else {
            regsub -all {\d+$} $headerToConfigure "" objectName
        }
        set headerToConfigure [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
        
        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
        }
        
        if {[llength $ipDataArgsList] != 0 && $redirectFlag == 0} {
            set ipDataHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-ipData]
            ::sth::sthCore::invoke stc::config $ipDataHnd $ipDataArgsList
            set ipHdrHnd [::sth::sthCore::invoke stc::get $ipDataHnd -children-ipHdr]
            ::sth::sthCore::invoke stc::config $ipHdrHnd $ipHdrArgsList
        }
        if {[llength $linkLayerArgsList] != 0} {
            set linkLayerOptionHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-linkLayerOption]
            set linkLayerAddressOptionHnd [::sth::sthCore::invoke stc::get $linkLayerOptionHnd -children-LinkLayerAddress]
            ::sth::sthCore::invoke stc::config $linkLayerAddressOptionHnd $linkLayerArgsList
        }
        if {[llength $mtuArgsList] != 0} {
            set mtuOptionHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-mtuOption]
            set mtuHnd [::sth::sthCore::invoke stc::get $mtuOptionHnd -children-MTU]
            ::sth::sthCore::invoke stc::config $mtuHnd $mtuArgsList
        }
        if {[llength $prefixArgsList] != 0} {
            set prefixOptionHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-prefixOption]
            set prefixHnd [::sth::sthCore::invoke stc::get $prefixOptionHnd -children-PrefixInformation]
            ::sth::sthCore::invoke stc::config $prefixHnd $prefixArgsList
        }
        if {[llength $redirectArgsList] != 0} {
            set redirectOptionHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-redirectedHdrOption]
            set redirectHnd [::sth::sthCore::invoke stc::get $redirectOptionHnd -children-RedirectedHeader]
            ::sth::sthCore::invoke stc::config $redirectHnd $redirectArgsList
            
            set ipDataHnd [::sth::sthCore::invoke stc::get $redirectHnd -children-ipData]
            ::sth::sthCore::invoke stc::config $ipDataHnd $ipDataArgsList
            set ipHdrHnd [::sth::sthCore::invoke stc::get $ipDataHnd -children-ipHdr]
            ::sth::sthCore::invoke stc::config $ipHdrHnd $ipHdrArgsList
        }

        if {[llength $addrListArgsList] != 0 && $mldv2GroupRecordFlag == 0} {
            set addrListHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-addrList]
            set ipv6AddrHnd [::sth::sthCore::invoke stc::get $addrListHnd -children-Ipv6Addr]
            ::sth::sthCore::invoke stc::config $ipv6AddrHnd $addrListArgsList
        }
        
        if {[llength $grpRecordArgsList] != 0} {
            set grpRecordsHnd [::sth::sthCore::invoke stc::get $headerToConfigure -children-grpRecords]
            set mldv2GroupRecordHnd [::sth::sthCore::invoke stc::get $grpRecordsHnd -children-MLDv2GroupRecord]
            ::sth::sthCore::invoke stc::config $mldv2GroupRecordHnd $grpRecordArgsList
            set addrListHnd [::sth::sthCore::invoke stc::get $mldv2GroupRecordHnd -children-addrList]
            set ipv6AddrHnd [::sth::sthCore::invoke stc::get $addrListHnd -children-Ipv6Addr]
            ::sth::sthCore::invoke stc::config $ipv6AddrHnd $addrListArgsList
        }
    }
    #clear the list after processing
    set sth::Traffic::listl4Headericmpv6 {};
    
    return ::sth::sthCore::SUCCESS;
    
}


proc ::sth::Traffic::processCreateIcmpHeader {Handle listName} {
    
    set _procName "processCreateIcmpHeader";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    set listArgsList {};
    set attrList [set ::$mns\::$listName];
    #default it will create the echo reply header, but only the integer value of the icmp_type will take effect.
    set headerName "icmp:IcmpEchoReply"
    foreach element $attrList {
            if {$element == "icmp_type"} {
                switch -exact $userArgsArray($element) {
                  "0" {
                    set headerName "icmp:IcmpEchoReply"
                  }
                   "8" {
                    set headerName "icmp:IcmpEchoRequest"
                  }
                   "3" {
                    set headerName "icmp:IcmpDestUnreach"
                  }
                   "4" {
                    set headerName "icmp:IcmpSourceQuench"
                  }
                   "5" {
                    set headerName "icmp:IcmpRedirect"
                  }
                   "11" {
                    set headerName "icmp:IcmpTimeExceeded"
                  }
                   "12" {
                    set headerName "icmp:IcmpParameterProblem"
                  }
                   "13" {
                    set headerName "icmp:IcmpTimestampRequest"
                  }
                    "14" {
                    set headerName "icmp:IcmpTimestampReply"
                  }
                    "15" {
                    set headerName "icmp:IcmpInfoRequest"
                  }
                    "16" {
                    set headerName "icmp:IcmpInfoReply"
                  }
                }
            }
            set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
            ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
            lappend listArgsList -$stcAttr $userArgsArray($element);
    }
    
     if {[set ::$mns\::handleCurrentHeader] == 0} {
        # we would have to create the header irrespective of the mode.
        
        ::sth::sthCore::log debug "$_procName: Calling stc::create $headerName [set ::$mns\::handleCurrentStream] $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::create $headerName -under [set ::$mns\::handleCurrentStream] $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while processing $headerName";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
        
        # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])];
        }
        
        lappend listOfHeaders "l4_header";
        lappend listOfHeaders "[set retHandle]";
        set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
        
    } else {    
        # if this is not 0 that means this has to be mode modify and header was created earlier.
        
        set headerToConfigure [set ::$mns\::handleCurrentHeader];
        
        set streamHandle [set ::$mns\::handleCurrentStream]
        #set length [string length $headerToConfigure]
        #set index [expr $length - 2]
        #set objectName [string range $headerToConfigure 0 $index]
        regsub -all {\d+$} $headerToConfigure "" objectName
        set headerToConfigure [::sth::sthCore::invoke ::stc::get $streamHandle -children-$objectName]
        
        ::sth::sthCore::log debug "$_procName: Calling stc::config $headerToConfigure $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::config $headerToConfigure $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            #puts "error while configuring $headerToConfigure";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $headerToConfigure Success. ";
        }
    }

    #clear the list after processing
    set sth::Traffic::listl4Headericmp {};
    return ::sth::sthCore::SUCCESS;
    
}


proc ::sth::Traffic::processCreateQosHeader {Handle listName} {

    set _procName "processCreateQosHeader";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    
    set listArgsList {};
    set attrList [set ::$mns\::$listName];
    switch $listName {
        "listl3OuterQosBits" {
            set dscpAttrName "ip_outer_dscp"
            set dscpStepName "ip_outer_dscp_step"
            set dscpCountName "ip_outer_dscp_count"
            set tosAttrName "ip_outer_tos_field"
            set precedenceAttrName "ip_outer_precedence"
            set precedenceModifier "listl3OuterPrecedenceRangeModifier"
            set tosModifier "listl3OuterTosRangeModifier"
            set tosTag "ip_outer_tos"
            set precedenceTag "ip_outer_precedence"
        }
        "listl4QosBits" {
            set dscpAttrName "l4_ip_dscp"
            set dscpStepName "l4_ip_dscp_step"
            set dscpCountName "l4_ip_dscp_count"
            set tosAttrName "l4_ip_tos_field"
            set precedenceAttrName "l4_ip_precedence"
            set precedenceModifier "listl4precedenceRangeModifier"
            set tosModifier "listl4tosRangeModifier"
            set tosTag "l4_ip_tos"
            set precedenceTag "l4_ip_precedence"
        }
        default {
            set dscpAttrName "ip_dscp"
            set dscpStepName "ip_dscp_step"
            set dscpCountName "ip_dscp_count"
            set tosAttrName "ip_tos_field"
            set precedenceAttrName "ip_precedence"
            set precedenceModifier "listl3precedenceRangeModifier"
            set tosModifier "listl3tosRangeModifier"
            set tosTag "ip_tos"
            set precedenceTag "ip_precedence"
        }
    }

    if {[lsearch $attrList $dscpAttrName] != -1} {
        # only one of diffserv or tos be created at this point
        set userValue $userArgsArray($dscpAttrName);
        if {[llength $userValue] == 1} {
            set binaryValue [sth::Traffic::decimal2binary $userValue 6];
            set dscpbinvalue [append binaryValue "00"]
            set dscphexvalue [::sth::sthCore::binToHex $dscpbinvalue]
            set highValue [string range $binaryValue 0 2];
            set lowValue [string range $binaryValue 3 5]
        
            set highValue [expr $userValue / 8];
            set lowValue [expr $userValue % 8];
            set listArgsList "-dscpHigh $highValue -dscpLow $lowValue";
            

            set tosDiffServHandle [::sth::sthCore::invoke stc::get $Handle -children-tosDiffserv]
            if { $tosDiffServHandle == "" } {
                ::sth::sthCore::log debug "$_procName: Calling stc::createtosDiffserv $Handle"
                if {[catch {::sth::sthCore::invoke ::stc::create tosDiffserv -under $Handle} diffServHandle]} {
                    return -code 1 -errorcode -1 $diffServHandle;
                } else {
                    ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $diffServHandle";
                }
        
                ::sth::sthCore::log debug "$_procName: Calling stc::create diffServ $diffServHandle $listArgsList"
                set cmdName "::sth::sthCore::invoke ::stc::create diffServ -under $diffServHandle $listArgsList";
                if {[catch {eval $cmdName} diffServHandle]} {
                    return -code 1 -errorcode -1 $diffServHandle;
                } else {
                    ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $diffServHandle";
                }
            } else {
                set diffServHandle [::sth::sthCore::invoke stc::get $tosDiffServHandle -children-diffServ]
                if {$diffServHandle == ""} {
                    set diffServHandle [::sth::sthCore::invoke stc::create diffServ -under $tosDiffServHandle] 
                }
                ::sth::sthCore::invoke stc::config $diffServHandle $listArgsList
            }
            #process the range modifier
            if {[info exists userArgsArray($dscpCountName)] || [info exists userArgsArray($dscpStepName)]} {
                set listArgsList {};
                if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} ipHeaderName]} {
                    ::sth::sthCore::log error "$_procName: $Handle -name $ipHeaderName ";
                    return -code 1 -errorcode -1 $ipHeaderName;
                } else {
                   ::sth::sthCore::log info "$_procName: $Handle -name $ipHeaderName ";
                }
                lappend listArgsList -OffsetReference "$ipHeaderName\.tosDiffserv.diffServ" -Data $dscphexvalue -Mask "FF" -EnableStream $::sth::Traffic::enableStream;
                if {[info exists userArgsArray($dscpCountName)]} {
                    lappend listArgsList -RecycleCount $userArgsArray($dscpCountName)
                }
                if {[info exists userArgsArray($dscpStepName)]} {
                    set stepValue $userArgsArray($dscpStepName)
                    set stepValue [expr $stepValue * 4]
                    set stepbin [sth::Traffic::decimal2binary $stepValue 8]
                    set stephex [::sth::sthCore::binToHex $stepbin]
                    lappend listArgsList -StepValue $stephex
                }

                set rangeModifierHandle [::sth::sthCore::invoke "stc::get [set ::$mns\::handleCurrentStream] -children-rangeModifier"]
                set rangeModifierExist ""
                if {$rangeModifierHandle != "" } {
                    #need to check if it is the modifier need to be modified
                    #set modifierList [::sth::sthCore::invoke ::stc::get $rangeModifierHandle -OffsetReference]
                    foreach modifier $rangeModifierHandle {
                        set refName [::sth::sthCore::invoke ::stc::get $modifier -OffsetReference]
                        if {$refName == "$ipHeaderName\.tosDiffserv.diffServ"} {
                            set rangeModifierExist $modifier
                        }
                    }
                }
                if {$rangeModifierExist != ""} {
                    ::sth::sthCore::invoke "stc::config $rangeModifierExist $listArgsList"
                } else {
                    ::sth::sthCore::log debug "$_procName: Calling stc::create rangeModifier [set ::$mns\::handleCurrentStream] $listArgsList"
                    set cmdName "::sth::sthCore::invoke ::stc::create rangeModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
                    if {[catch {eval $cmdName} dscpModifierHandle]} {
                        return $::sth::sthCore::FAILURE;
                    } else {
                        ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $dscpModifierHandle";
                    }
                }
            }
                
            return $::sth::sthCore::SUCCESS;   
        } else {
            set valueList {}
            foreach value $userValue {
                set dscpbinvalue [sth::Traffic::decimal2binary $value 6]
                set dscpbinvalue [append dscpbinvalue "00"]
                set dscphexvalue [::sth::sthCore::binToHex $dscpbinvalue]
                lappend valueList $dscphexvalue
            }
            
             ::sth::sthCore::log debug "$_procName: Calling stc::createtosDiffserv $Handle"
            if {[catch {::sth::sthCore::invoke ::stc::create tosDiffserv -under $Handle} diffServHandle]} {
                return -code 1 -errorcode -1 $diffServHandle;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $diffServHandle";
            }
        
            ::sth::sthCore::log debug "$_procName: Calling stc::create diffServ $diffServHandle $listArgsList"
            set cmdName "::sth::sthCore::invoke ::stc::create diffServ -under $diffServHandle";
            if {[catch {eval $cmdName} diffServHandle]} {
                return -code 1 -errorcode -1 $diffServHandle;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $diffServHandle";
            }
            
            set listArgsList {};
            if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} ipHeaderName]} {
                ::sth::sthCore::log error "$_procName: $Handle -name $ipHeaderName ";
                 return -code 1 -errorcode -1 $ipHeaderName;
            } else {
                ::sth::sthCore::log info "$_procName: $Handle -name $ipHeaderName ";
            }
            lappend listArgsList -OffsetReference "$ipHeaderName\.tosDiffserv.diffServ" -Data $valueList;
            
            set cmdName "::sth::sthCore::invoke ::stc::create TableModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
            if {[catch {eval $cmdName} dscpModifierHandle]} {
                return $::sth::sthCore::FAILURE;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $dscpModifierHandle";
            }
            return $::sth::sthCore::SUCCESS; 
        }

    }


    ###########################################################################
    #guess this part will never be used, since there is no ip_tos in the traffic_config
    #API, since not very sure about the guess, just keep it here
    # add a new option ip_tos to configure the whole ip tos 8 bytes
    if {[lsearch $attrList ip_tos] != -1} {
        set userValue $userArgsArray(ip_tos);
       
        if {[llength $userValue] == 1} {
            set tosbinvalue [sth::Traffic::decimal2binary $userValue 8]
            set toshexvalue [::sth::sthCore::binToHex $tosbinvalue]
            set precedenceBit  [string range $tosbinvalue 0 2]
            set precedenceValue  [::sth::sthCore::binToInt $precedenceBit]
            set dBit [string range $tosbinvalue 3 3]
            set tBit [string range $tosbinvalue 4 4]
            set rBit [string range $tosbinvalue 5 5]
            set mBit [string range $tosbinvalue 6 6]
            set reserveBit [string range $tosbinvalue 7 7]
            set listArgsList "-precedence $precedenceValue -dBit $dBit -tBit $tBit -rBit $rBit -mBit $mBit -reserved $reserveBit";
            
            ::sth::sthCore::log debug "$_procName: Calling stc::create tosDiffserv $Handle"
            if {[catch {::sth::sthCore::invoke ::stc::create tosDiffserv -under $Handle} diffServHandle]} {
                return -code 1 -errorcode -1 $diffServHandle;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $diffServHandle";
            }
        
            ::sth::sthCore::log debug "$_procName: Calling stc::create tos $diffServHandle $listArgsList"
            set cmdName "::sth::sthCore::invoke ::stc::create tos -under $diffServHandle $listArgsList";
            if {[catch {eval $cmdName} tosHandle]} {
                return -code 1 -errorcode -1 $tosHandle;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $tosHandle";
            }
            #process the range modifier
            if {[info exists userArgsArray(ip_tos_count)] || [info exists userArgsArray(ip_tos_step)]} {
                set listArgsList {};
                if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} ipHeaderName]} {
                    ::sth::sthCore::log error "$_procName: $Handle -name $ipHeaderName ";
                    return -code 1 -errorcode -1 $ipHeaderName;
                } else {
                   ::sth::sthCore::log info "$_procName: $Handle -name $ipHeaderName ";
                }
                lappend listArgsList -OffsetReference "$ipHeaderName\.tosDiffserv.tos" -Data $toshexvalue -Mask "FF" -EnableStream $::sth::Traffic::enableStream;
                if {[info exists userArgsArray(ip_tos_count)]} {
                    lappend listArgsList -RecycleCount $userArgsArray(ip_tos_count)
                }
                if {[info exists userArgsArray(ip_tos_step)]} {
                    set stepValue $userArgsArray(ip_tos_step)
                    set stepbin [sth::Traffic::decimal2binary $stepValue 8]
                    set stephex [::sth::sthCore::binToHex $stepbin]
                    lappend listArgsList -StepValue $stephex
                }
                
                ::sth::sthCore::log debug "$_procName: Calling stc::create rangeModifier [set ::$mns\::handleCurrentStream] $listArgsList"
                set cmdName "::sth::sthCore::invoke ::stc::create rangeModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
                if {[catch {eval $cmdName} tosModifierHandle]} {
                    return $::sth::sthCore::FAILURE;
                } else {
                    ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $tosModifierHandle";
                }
            }
                
            return $::sth::sthCore::SUCCESS;   
        } else {
            set valueList {}
            foreach value $userValue {
                set tosbinvalue [sth::Traffic::decimal2binary $value 8]
                set toshexvalue [::sth::sthCore::binToHex $tosbinvalue]
                lappend valueList $toshexvalue
            }
            
             ::sth::sthCore::log debug "$_procName: Calling stc::create tosDiffserv $Handle"
            if {[catch {::sth::sthCore::invoke ::stc::create tosDiffserv -under $Handle} diffServHandle]} {
                return -code 1 -errorcode -1 $diffServHandle;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $diffServHandle";
            }
        
            ::sth::sthCore::log debug "$_procName: Calling stc::create diffServ $diffServHandle $listArgsList"
            set cmdName "::sth::sthCore::invoke ::stc::create tos -under $diffServHandle";
            if {[catch {eval $cmdName} tosHandle]} {
                return -code 1 -errorcode -1 $tosHandle;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $tosHandle";
            }
            
            set listArgsList {};
            if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} ipHeaderName]} {
                ::sth::sthCore::log error "$_procName: $Handle -name $ipHeaderName ";
                 return -code 1 -errorcode -1 $ipHeaderName;
            } else {
                ::sth::sthCore::log info "$_procName: $Handle -name $ipHeaderName ";
            }
            lappend listArgsList -OffsetReference "$ipHeaderName\.tosDiffserv.tos" -Data $valueList;
            
            set cmdName "::sth::sthCore::invoke ::stc::create TableModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
            if {[catch {eval $cmdName} tosModifierHandle]} {
                return $::sth::sthCore::FAILURE;
            } else {
                ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $tosModifierHandle";
            }
            return $::sth::sthCore::SUCCESS; 
        }
    }
    
   

    
    foreach element [set ::$mns\::$listName] {
        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
        if {[info exists userArgsArray($element)]} {
            set userValue $userArgsArray($element);
        }
        # only ip_tos_field and ip_precedence will be configed here, for the step, mode and count will be configured in processCreateQosModifier
        if {$element == $tosAttrName} {
            if {![info exists userArgsArray($element)]} {
                set userValue 0;
            }
            if {[llength $userValue] > 1} {
                set value_list [split $userValue " "]
            } else {
                set value_list $userValue
            }
            foreach value $value_list {
                set binValue $::sth::Traffic::arrayDecimal2Bin($value);
                set individualBits [split $binValue ""];
                foreach bitName $stcAttr bitValue $individualBits {
                    lappend listArgsList -$bitName $bitValue;
                }
            }
        } elseif {$element == $precedenceAttrName} {
            if {![info exists userArgsArray($element)]} {
                set userValue 0;
            }
            lappend listArgsList -$stcAttr $userValue;
        }
    }

    if {[catch {::sth::sthCore::invoke stc::get $Handle -children-tosDiffserv} diffServHandle]} {
        ::sth::sthCore::processError trafficKeyedList "Error: $diffServHandle"
        return -code error $trafficKeyedList
    } else {
       if {$diffServHandle == ""} {
            ::sth::sthCore::log debug "$_procName: Calling stc::create tosDiffserv $Handle"
            if {[catch {::sth::sthCore::invoke stc::create tosDiffserv -under $Handle} diffServHandle]} {
                ::sth::sthCore::processError trafficKeyedList "Error: $diffServHandle"
                return -code error $trafficKeyedList
            }
            ::sth::sthCore::log debug "$_procName: Calling stc::create tos $diffServHandle $listArgsList"
            set cmdName "::sth::sthCore::invoke stc::create tos -under $diffServHandle \"$listArgsList\"";
        } else {
            if {[catch {::sth::sthCore::invoke stc::get $diffServHandle -children-tos} tosHandle]} {
                ::sth::sthCore::processError trafficKeyedList "Error: $tosHandle"
                return -code error $trafficKeyedList
            } else {
                if {$tosHandle == ""} {
                    ::sth::sthCore::log debug "$_procName: Calling stc::create tos $diffServHandle $listArgsList"
                    set cmdName "::sth::sthCore::invoke stc::create tos -under $diffServHandle \"$listArgsList\"";
                } else {
                    ::sth::sthCore::log debug "$_procName: Calling stc::config tos tosHandle  $listArgsList"
                    set cmdName "::sth::sthCore::invoke stc::config $tosHandle \"$listArgsList\"";
                }
            }
        }  
    }
    
    
    if {[catch {eval $cmdName} retHandle]} {
        ::sth::sthCore::processError trafficKeyedList "Error: $retHandle"
        return -code error $trafficKeyedList
    } 
    
    # check if a range modifer is needed here
    ###########################################
    #Modifier for ip_precedence for IP Header #
    ###########################################
    if {[llength [set ::$mns\::$precedenceModifier]]} {
        if {[catch {::sth::Traffic::processCreateQosModifier $Handle $precedenceModifier $precedenceTag} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
            return -code error $trafficKeyedList
        }
    }
    
    ###########################################
    #Modifier for ip_tos for IP Header        #
    ###########################################
    if {[llength [set ::$mns\::$tosModifier]]} {
        if {[catch {::sth::Traffic::processCreateQosModifier $Handle $tosModifier $tosTag} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
            return -code error $trafficKeyedList
        }
    }
}
proc ::sth::Traffic::processRangeModifierSwitches {switchName} {
    #TODO:
    # To verify whether src_count/dst_count need a dependency of src_step/dst_step.
    
    set _procName "processRangeModifierSwitches";
     
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    # Here we decide what list the attribute goes to.
    if {([regexp mac $switchName] && ![regexp  mac_discovery $switchName]) || [regexp vlan $switchName] || [regexp {v[pc]i} $switchName] || [regexp mpls $switchName]} {
        # This is layer 2
        #set extEncapType [set ::$mns\::l2EncapType];
        #process the inner ethernet header for the vxlan
        if {[regexp "inner" $switchName]} {
            set extEncapType [set ::$mns\::innerl2EncapType];
        } else {
            set extEncapType [set ::$mns\::l2EncapType];
        }
        set intEncapType [set ::$mns\::traffic_config_dependency($switchName)];
                                    
        if {[regexp "mpls" $extEncapType] || $extEncapType == "ethernet_ii_vlan" || $intEncapType == $extEncapType ||$extEncapType == "atm_vc_mux"
                    || [lsearch $intEncapType $extEncapType] >= 0 || [regexp "_vlan" $extEncapType]} {
            
            if {[regexp "mpls" $switchName]} {
                if {[regexp "^\\s*\{" $userArgsArray($switchName)]} {
                    set mpls_layer_count [llength $userArgsArray($switchName)]
                } else {
                    set mpls_layer_count 1
                }
               
                if {[regexp "labels" $switchName]} {
                    for {set i 1} {$i<=$mpls_layer_count} {incr i} {
                        if {[info exists userArgsArray(mpls_labels_mode)]} {
                            set mpls_labels_mode_length [llength $userArgsArray(mpls_labels_mode)]
                            if {$mpls_labels_mode_length != $mpls_layer_count} {
                                ::sth::sthCore::log error "the mpls_labels_mode length $mpls_labels_mode_length must as the same as the mpls_labels length $mpls_layer_count";
                                return 
                            }
                            set mpls_labels_mode [lindex $userArgsArray(mpls_labels_mode) [expr $i-1]]
                        } else {
                            set mpls_labels_mode "list" 
                        }
                        if {$mpls_labels_mode== "list"} {
                            lappend ::$mns\::listMplsLabelTableModifier$i $switchName;
                            lappend ::$mns\::listMplsLabelModifier$i $switchName;
                        } 
                        if {$mpls_labels_mode== "increment" || $mpls_labels_mode== "decrement"} {
                            lappend ::$mns\::listMplsLabelModifier$i $switchName;
                            lappend ::$mns\::listMplsLabelRangeModifier$i $switchName;
                        }
                    }
                }
                if {[regexp "cos" $switchName]} {
                    if {[info exists userArgsArray(mpls_cos_mode)]} {
                        for {set i 1} {$i<=$mpls_layer_count} {incr i} {
                            set ::$mns\::listMplsCosTableModifier$i {};
                            set ::$mns\::listMplsCosRangeModifier$i {};
                            set ::$mns\::listMplsCosModifier$i {};
                            set mpls_cos_mode_length [llength $userArgsArray(mpls_cos_mode)]
                            if {$mpls_cos_mode_length!=$mpls_layer_count} {
                                ::sth::sthCore::log error "the  mpls_cos_mode length must as the same as the mpls_labels length";
                                return 
                            }
                            set mpls_cos_mode [lindex $userArgsArray(mpls_cos_mode) [expr $i-1]]
                            if {$mpls_cos_mode== "list"} {
                                lappend ::$mns\::listMplsCosTableModifier$i $switchName;
                                lappend ::$mns\::listMplsCosModifier$i $switchName;
                            } 
                            if {$mpls_cos_mode== "increment" || $mpls_cos_mode== "decrement"} {
                                lappend ::$mns\::listMplsCosModifier$i $switchName;
                                lappend ::$mns\::listMplsCosRangeModifier$i $switchName;
                            }
                        }
                    }
                }
                if {[regexp "ttl" $switchName]} {
                    if {[info exists userArgsArray(mpls_ttl_mode)]} {
                        for {set i 1} {$i<=$mpls_layer_count} {incr i} {
                            set ::$mns\::listMplsTtlTableModifier$i {};
                            set ::$mns\::listMplsTtlRangeModifier$i {};
                            set ::$mns\::listMplsTtlModifier$i {};
                            set mpls_ttl_mode_length [llength $userArgsArray(mpls_ttl_mode)]
                            if {$mpls_ttl_mode_length!=$mpls_layer_count} {
                                ::sth::sthCore::log error "the  mpls_ttl_mode length must as the same as the mpls_labels length";
                                return 
                            }
                            set mpls_ttl_mode [lindex $userArgsArray(mpls_ttl_mode) [expr $i-1]]
                            if {$mpls_ttl_mode== "list"} {
                                lappend ::$mns\::listMplsTtlTableModifier$i $switchName;
                                lappend ::$mns\::listMplsTtlModifier$i $switchName;
                            }
                        
                            if {$mpls_ttl_mode == "increment" || $mpls_ttl_mode== "decrement"} {
                                lappend ::$mns\::listMplsTtlModifier$i $switchName;
                                lappend ::$mns\::listMplsTtlRangeModifier$i $switchName;
                            }
                        }
                    }
                }
                
            } else {
                if {[regexp -nocase "inner" $switchName]} {
                    #process the inner ethernet header
                    if {[regexp mac $switchName]} {
                        if {[regexp src $switchName]} {
                            lappend ::$mns\::listInnerl2SrcRangeModifier $switchName;
                            if {![info exists userArgsArray(inner_mac_src_step)]} {
                                set userArgsArray(inner_mac_src_step) 1
                                lappend ::$mns\::listInnerl2SrcRangeModifier inner_mac_src_step
                            }
                        } elseif {[regexp dst $switchName]} {
                            lappend ::$mns\::listInnerl2DstRangeModifier $switchName;
                            if {![info exists userArgsArray(inner_mac_dst_step)]} {
                                set userArgsArray(inner_mac_dst_step) 1
                                lappend ::$mns\::listInnerl2DstRangeModifier inner_mac_dst_step
                            }
                        }
                    } elseif {[regexp vlan $switchName]} {
                        if {[regexp outer $switchName]} {
                            lappend ::$mns\::listInnerl2OuterVlanRangeModifier $switchName;
                        } else {
                            if {[regexp priority $switchName]} {
                                lappend ::$mns\::listInnerl2VlanPriorityRangeModifier $switchName;
                            } else {
                                lappend ::$mns\::listInnerl2VlanRangeModifier $switchName;
                            }
                        }
                    }
                    
                } else {
                    if {"mac_dst_mode" != $switchName } {
                        if {[regexp mac $switchName]} {
                            if {[regexp src2 $switchName]} {
                                lappend ::$mns\::listl2Src2RangeModifier $switchName;
                                #set the default value of the mac_src2_step
                                if {![info exists userArgsArray(mac_src2_step)]} {
                                    set userArgsArray(mac_src2_step) 1
                                    lappend ::$mns\::listl2Src2RangeModifier mac_src2_step
                                }
                            } elseif {[regexp dst2 $switchName]} {
                                lappend ::$mns\::listl2Dst2RangeModifier $switchName;
                                #set the default value of the mac_dst2_step
                                if {![info exists userArgsArray(mac_dst2_step)]} {
                                    set userArgsArray(mac_dst2_step) 1
                                    lappend ::$mns\::listl2Dst2RangeModifier mac_dst2_step
                                }
                            } elseif {[regexp src $switchName]} {
                                lappend ::$mns\::listl2SrcRangeModifier $switchName;
                                #set the default value of the mac_src_step
                                if {![info exists userArgsArray(mac_src_step)]} {
                                    set userArgsArray(mac_src_step) 1
                                    lappend ::$mns\::listl2SrcRangeModifier mac_src_step
                                }
                            } elseif {[regexp dst $switchName]} {
                                lappend ::$mns\::listl2DstRangeModifier $switchName;
                                #set the default value of the mac_dst_step
                                if {![info exists userArgsArray(mac_dst_step)]} {
                                    set userArgsArray(mac_dst_step) 1
                                    lappend ::$mns\::listl2DstRangeModifier mac_dst_step
                                }
                            }
                        } elseif {[regexp vlan $switchName]} {
                            if {[regexp outer $switchName]} {
                                lappend ::$mns\::listl2OuterVlanRangeModifier $switchName;
                            } elseif {[regexp "other" $switchName]} {
                                lappend ::$mns\::listl2OtherVlanRangeModifier $switchName;
                            } else {
                                if {[regexp priority $switchName]} {
                                    lappend ::$mns\::listl2VlanPriorityRangeModifier $switchName;
                                } else {
                                    lappend ::$mns\::listl2VlanRangeModifier $switchName;
                                }
                            }
                        } elseif {[regexp {vpi} $switchName]} {
                            lappend ::$mns\::listl2VpiRangeModifier $switchName;
                        } elseif {[regexp {vci} $switchName]} {
                            lappend ::$mns\::listl2VciRangeModifier $switchName;
                        }
                    } else {
                        ### Do special processing for mac_dst_mode attribute
                        if {$userArgsArray(mac_dst_mode) != "discovery"} {
                            if {[regexp src $switchName]} {
                                lappend ::$mns\::listl2SrcRangeModifier $switchName;
                                if {[regexp src2 $switchName]} {
                                    if {![info exists userArgsArray(mac_src2_step)]} {
                                        lappend ::$mns\::listl2SrcRangeModifier mac_src2_step;
                                        set userArgsArray(mac_src2_step) 1
                                    }
                                } else {
                                    if {![info exists userArgsArray(mac_src_step)]} {
                                        lappend ::$mns\::listl2SrcRangeModifier mac_src_step;
                                        set userArgsArray(mac_src_step) 1
                                    }
                                }
                            } else {
                                lappend ::$mns\::listl2DstRangeModifier $switchName;
                                if {[regexp dst2 $switchName]} {
                                    if {![info exists userArgsArray(mac_dst2_step)]} {
                                        lappend ::$mns\::listl2DstRangeModifier mac_dst2_step;
                                        set userArgsArray(mac_dst2_step) 1
                                    }
                                } else {
                                    if {![info exists userArgsArray(mac_dst_step)]} {
                                        lappend ::$mns\::listl2DstRangeModifier mac_dst_step;
                                        set userArgsArray(mac_dst_step) 1
                                    }
                                }
                            }
                        } 
                    }
                }
            }
        } elseif {[lsearch $intEncapType $extEncapType] < 0} {
            #throwing dependency error
            set errorString "Dependency Error for $switchName. ENTERED: $extEncapType. EXPECTED: $intEncapType";
            ::sth::sthCore::log debug "$_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        }
    } elseif {[regexp ip $switchName]} {
        # This is layer 3     
        if {[regexp outer $switchName]} {
            set extHeaderType [set ::$mns\::l3OuterHeaderType];
        } elseif {[regexp inner $switchName]} {
            set extHeaderType inner_ipv4;
        } elseif {[regexp "^l4" $switchName]} {
            set extHeaderType [set ::$mns\::l4HeaderType];
        } else {
            set extHeaderType [set ::$mns\::l3HeaderType];
        }
        set intHeaderType [set ::$mns\::traffic_config_dependency($switchName)];
        
        if {$intHeaderType == $extHeaderType || $extHeaderType == "arp"} {
            if {[regexp src $switchName]} {
                if {[regexp outer $switchName]} {
                    lappend ::$mns\::listl3OuterSrcRangeModifier $switchName;
                } elseif {[regexp -nocase inner $switchName]} {
                    lappend ::$mns\::listInnerl3SrcRangeModifier $switchName;
                } elseif {[regexp -nocase "^l4" $switchName]} {
                    lappend ::$mns\::listl4SrcRangeModifier $switchName;
                } else {
                    lappend ::$mns\::listl3SrcRangeModifier $switchName;
                }
            } elseif {[regexp dst $switchName]} {
                # if not src, it has to be dst attribute
                if {[regexp outer $switchName]} {
                    lappend ::$mns\::listl3OuterDstRangeModifier $switchName;
                } elseif {[regexp -nocase inner $switchName]} {
                    lappend ::$mns\::listInnerl3DstRangeModifier $switchName;
                } elseif {[regexp -nocase "^l4" $switchName]} {
                    lappend ::$mns\::listl4DstRangeModifier $switchName;
                } else {
                    lappend ::$mns\::listl3DstRangeModifier $switchName;
                }
            } else {
                lappend ::$mns\::listInnerGwRangeModifier $switchName;
            }
        } elseif {[lsearch $intHeaderType $extHeaderType] < 0} {
            #throwing dependency error
            set errorString "Dependency Error for $switchName. ENTERED: $extHeaderType. EXPECTED: $intHeaderType";
            ::sth::sthCore::log debug "$_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        }
    } elseif {[regexp tcp_src $switchName]} {
        lappend ::$mns\::listTcpPortSrcRangeModifier $switchName;
    } elseif {[regexp tcp_dst $switchName]} {
        lappend ::$mns\::listTcpPortDstRangeModifier $switchName;
    } elseif {[regexp udp_src $switchName]} {
        lappend ::$mns\::listUdpPortSrcRangeModifier $switchName;
    } elseif {[regexp udp_dst $switchName]} {
        lappend ::$mns\::listUdpPortDstRangeModifier $switchName;
    } 
    
    if {[regexp mac_discovery $switchName]} {
        lappend ::$mns\::listMacGwRangeModifier $switchName;
    }
    
    #MOD Cheng Fei 08-10-09
    #Add support for ARP and igmp range modifier
    if {[regexp arp $switchName]} {
        if {[regexp src_hw $switchName]} {
            lappend ::$mns\::listArpMacSrcRangeModifier $switchName;
        }
        if {[regexp dst_hw $switchName]} {
            lappend ::$mns\::listArpMacDstRangeModifier $switchName;
        }
    }
    if {[regexp igmp $switchName]} {
        lappend ::$mns\::listIgmpGroupAddrRangeModifier $switchName;
    }
    #end
   
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::processCreateL2TableModifier {headerType Handle List tag} {
    #headerType is used to extend to other type of table modifier
    set _procName "processCreateL2TableModifier";
    upvar userArgsArray userArgsArray;
    #upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    set listArgsList {};
    if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
        ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
        return $::sth::sthCore::FAILURE;
    } else {
        ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
    }  
    set offsetReferenceName "$headerName\.$tag";
    if {("mpls_labels"==$headerType)||("mpls_cos"==$headerType)||("mpls_ttl"==$headerType)} {
        set data $List
    } else {
        set data $userArgsArray($List)
    }
    lappend listArgsList -EnableStream $::sth::Traffic::enableStream;
    lappend listArgsList -OffsetReference $offsetReferenceName -data $data -active true;
    
    if {$userArgsArray(mode) == "modify"} {
        set tableList [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children-tableModifier]
        foreach tableObj $tableList {
           set ref [::sth::sthCore::invoke stc::get $tableObj -OffsetReference]
           if { $ref == $offsetReferenceName } {
                set tableModifier $tableObj
                break
           }
        }
        if {[llength $List]} {
            if {[info exists tableModifier]} {
                ::sth::sthCore::log debug "$_procName: Calling stc::config tableModifier [set ::$mns\::handleCurrentStream] $listArgsList"
                set cmdName "::sth::sthCore::invoke ::stc::config $tableModifier $listArgsList";    
            } else {
                ::sth::sthCore::log debug "$_procName: Calling stc::create tableModifier [set ::$mns\::handleCurrentStream] $listArgsList"
                set cmdName "::sth::sthCore::invoke ::stc::create tableModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
            }
        } else {
            if {[info exists tableModifier]} {
            ::sth::sthCore::log debug "$_procName: Calling stc::delete tableModifier [set ::$mns\::handleCurrentStream]"
            set cmdName "::sth::sthCore::invoke stc::delete $tableModifier";
            }
        }
        
        if {[catch {eval $cmdName} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } 
    } else {
        ::sth::sthCore::log debug "$_procName: Calling stc::create tableModifier [set ::$mns\::handleCurrentStream] $listArgsList"
        set cmdName "::sth::sthCore::invoke ::stc::create tableModifier -under [set ::$mns\::handleCurrentStream] $listArgsList";
        if {[catch {eval $cmdName} retHandle]} {
            ##puts "error while processing rangeModifier $retHandle";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: stc::create Success. Handle is $retHandle";
        }
    }
   
}

proc ::sth::Traffic::processDisActiveTableModifier {headerType Handle tag} {
    set _procName "processDisActiveTableModifier";
    upvar userArgsArray userArgsArray;
    upvar mns mns;
    if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
        ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
        return $::sth::sthCore::FAILURE;
    } else {
        ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
    }
    set offsetReferenceName "$headerName\.$tag";
    
    set tableList [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children-tableModifier]
    foreach tableObj $tableList {
       set ref [::sth::sthCore::invoke stc::get $tableObj -OffsetReference]
       if { $ref == $offsetReferenceName } {
           set tableModifier $tableObj
           break
        }
    }
    if {[info exists tableModifier]} {
        ::sth::sthCore::log debug "$_procName: Calling stc::config tableModifier [set ::$mns\::handleCurrentStream] active"
        set cmdName "::sth::sthCore::invoke ::stc::config $tableModifier -active false";
        if {[catch {eval $cmdName} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } 
    }
}

proc ::sth::Traffic::processDisActiveRangeModifier {headerType Handle tag} {
    set _procName "processDisActiveRangeModifier";
    upvar userArgsArray userArgsArray;
    upvar mns mns;
    if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
        ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
        return $::sth::sthCore::FAILURE;
    } else {
        ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
    }
    set offsetReferenceName "$headerName\.$tag";
                
    set rangeList [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children-rangeModifier]
    foreach rangeObj $rangeList {
       set ref [::sth::sthCore::invoke stc::get $rangeObj -OffsetReference]
       if { $ref == $offsetReferenceName } {
           set rangeModifier $rangeObj
           break
        }
    }
    if {[info exists rangeModifier]} {
        ::sth::sthCore::log debug "$_procName: Calling stc::config rangeModifier [set ::$mns\::handleCurrentStream] active"
        set cmdName "::sth::sthCore::invoke ::stc::config $rangeModifier -active false";
        if {[catch {eval $cmdName} retHandle]} {
            return $::sth::sthCore::FAILURE;
        } 
    }  
}

proc ::sth::Traffic::processCreateL2RangeModifier {headerType Handle listName tag {mymask "00:00:FF:FF:FF:FF"}} {
    # TODO:
    # set offsetReferenceName and mask for eth header
    # The offsetreference and the mask will change depending upon, whether this range modifier is for vlan or eth header.
    
    set _procName "processCreateL2RangeModifier";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    
    set listArgsList {};
    array set arrayArgsList {};
    set offsetVal 0;
    set modeArg "";
    set rangeModifier "";
                
       
    switch $headerType {
      "vlan" {
        # In case of Vlans, we need to provide the fully qualified name.
        # Thus it should be the following: $ethName.vlans.$vlanName.id
        set offsetReferenceNameList {}
        for {set i 0} {$i < [llength $Handle]} {incr i} {
            set CurrentCommand [lindex $Handle $i];
            set listNameList {};
            # for vlan, get parent and grandparent here.
            
            # Write a for loop here
            for {set x 0} {$x < 3} {incr x} {
                
                ::sth::sthCore::log debug "$_procName: Calling ::stc::get $CurrentCommand -name"
                if {[catch {::sth::sthCore::invoke ::stc::get $CurrentCommand -name} headerName]} {
                    ::sth::sthCore::log error "$_procName: $CurrentCommand -name $headerName ";
                    return $::sth::sthCore::FAILURE;
                } else {
                    ::sth::sthCore::log info "$_procName: $CurrentCommand -name $headerName ";
                }
                lappend listNameList $headerName;
                
                if {[catch {::sth::sthCore::invoke ::stc::get $CurrentCommand -parent} handleParent]} {
                    ::sth::sthCore::log error "$_procName: $Handle -parent $handleParent ";
                    return $::sth::sthCore::FAILURE;
                } else {
                    ::sth::sthCore::log info "$_procName: $Handle -parent $handleParent ";
                }
                
                set CurrentCommand $handleParent;
            }
            
            set offsetReferenceName [lindex $listNameList 2].vlans.[lindex $listNameList 0].$tag;
            if {$listName == "listl2OtherVlanRangeModifier"} {
                lappend offsetReferenceNameList $offsetReferenceName
            }
            if {[regexp pri $tag]} {
                set mask 111
            } else {
                set mask 4095;
            }
        }
     }
     "vpi" {
        set atmHandle $Handle
        set atmHandleName [::sth::sthCore::invoke stc::get $atmHandle -name]
        set vpiHandle [::sth::sthCore::invoke stc::get $atmHandle -children-vpi]
        set uniHandle [::sth::sthCore::invoke stc::get $vpiHandle -children-UNI]
    
        set offsetReferenceName "$atmHandleName\.vpi.uni.vpi";
        set mask 255;
        set Handle $uniHandle
        
        lappend listArgsList -EnableStream $::sth::Traffic::enableStream
        
     }
     "mpls_labels" {
        if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
        }
        
        set offsetReferenceName "$headerName\.$tag";
        set mask 1048575;
        
        lappend listArgsList -EnableStream $::sth::Traffic::enableStream -active true
    }
     "mpls_cos" {
        if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
        }
        
        set offsetReferenceName "$headerName\.$tag";
        set mask 111;
        
        lappend listArgsList -EnableStream $::sth::Traffic::enableStream -active true
    }
     "mpls_ttl" {
        if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
        }
        
        set offsetReferenceName "$headerName\.$tag";
        set mask 255;
        
        lappend listArgsList -EnableStream $::sth::Traffic::enableStream -active true
        }
     "vci" {
         if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
        }
        
        set offsetReferenceName "$headerName\.$tag";
        set mask 4095;
        
        lappend listArgsList -EnableStream $::sth::Traffic::enableStream
        
     }
     default {
        if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
            ::sth::sthCore::log error "$_procName: $Handle -name $headerName ";
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info "$_procName: $Handle -name $headerName ";
        }
        
        set offsetReferenceName "$headerName\.$tag";
        set mask $mymask
     }
    }
    
    #get the args name
    switch -- $listName {
        "listl2SrcRangeModifier" {
            set ArgName "mac_src"
        }
        "listl2DstRangeModifier" {
            set ArgName "mac_dst"
        }
        "listl2Src2RangeModifier" {
            set ArgName "mac_src2"
        }
        "listl2Dst2RangeModifier" {
            set ArgName "mac_dst2"
        }
        "listl2VlanRangeModifier" {
            set ArgName "vlan_id"
        }
        "listl2OuterVlanRangeModifier" {
            set ArgName "vlan_id_outer"
        }
        "listl2OtherVlanRangeModifier" {
            set ArgName "vlan_id_other"
        }
        "listl2VlanPriorityRangeModifier" {
            set ArgName "vlan_user_priority"
        }
        "listInnerl2SrcRangeModifier" {
            set ArgName "inner_mac_src"
        }
        "listInnerl2DstRangeModifier" {
            set ArgName "inner_mac_dst"
        }
        "listInnerl2VlanRangeModifier" {
            set ArgName "inner_vlan_id"
        }
        "listInnerl2OuterVlanRangeModifier" {
            set ArgName "inner_vlan_id_outer"
        }
        "listInnerl2VlanPriorityRangeModifier" {
            set ArgName "inner_vlan_user_priority"
        }
    }
    set offsetReferenceValueList {}
    for {set i 0} {$i < [llength $Handle]} {incr i} {
        if {[catch {::sth::sthCore::invoke ::stc::get [lindex $Handle $i] -$tag} offsetReferenceValue]} {
            ::sth::sthCore::processError trafficKeyedList "$_procName: $Handle -$tag $offsetReferenceValue " {}
            return $::sth::sthCore::FAILURE;
        } else {
            if {$listName == "listl2OtherVlanRangeModifier"} {
                lappend offsetReferenceValueList $offsetReferenceValue
            }
            ::sth::sthCore::log info "$_procName: [lindex $Handle $i] -$tag $offsetReferenceValue ";
        }
    }
    
    # add by xiaozhi, 2011/12/22 temporarily fix the qinq case for bound traffic
    if {[info exist userArgsArray(vlan_id_outer)] || [info exist userArgsArray(inner_vlan_id_outer)] && ![info exists userArgsArray(emulation_src_handle)] && ![info exists userArgsArray(emulation_dst_handle)]} {
        if {$listName == "listl2VlanRangeModifier" || $listName == "listl2OuterVlanRangeModifier" || $listName == "listInnerl2VlanRangeModifier" || $listName == "listInnerl2OuterVlanRangeModifier"} {
            if {[info exist userArgsArray(vlan_id_count)]} {
                set vlan_id_count $userArgsArray(vlan_id_count)
            } else {
                set vlan_id_count 1
            }
            if {[info exist userArgsArray(vlan_id_outer_count)]} {
                set vlan_id_outer_count $userArgsArray(vlan_id_outer_count)
            } else {
                set vlan_id_outer_count 1
            }
            
            if {[info exist userArgsArray(inner_vlan_id_count)]} {
                set inner_vlan_id_count $userArgsArray(inner_vlan_id_count)
            } else {
                set inner_vlan_id_count 1
            }
            if {[info exist userArgsArray(inner_vlan_id_outer_count)]} {
                set inner_vlan_id_outer_count $userArgsArray(inner_vlan_id_outer_count)
            } else {
                set inner_vlan_id_outer_count 1
            }
            
            
            switch -exact -- $userArgsArray(qinq_incr_mode) {
               "both" {
                    # fix CR311406748
                    if {[info exists userArgsArray(l3_protocol)]} {
                        if {[string match -nocase "ipv4" $userArgsArray(l3_protocol)] && [info exist userArgsArray(ip_src_count)]} {
                            set count $userArgsArray(ip_src_count)
                        } elseif {[string match -nocase "ipv6" $userArgsArray(l3_protocol)] && [info exist userArgsArray(ipv6_src_count)]} {
                            set count $userArgsArray(ipv6_src_count)
                        } else {
                            set count 1
                        }
                        #if {[expr {$count/$vlan_id_outer_count} - 1] < 0} {
                        #   set userArgsArray(vlan_id_outer_repeat) 0
                        #} else {
                        #   set userArgsArray(vlan_id_outer_repeat) [expr {$count/$vlan_id_outer_count} - 1]
                        #}
                        #if {[expr {$count/$vlan_id_count} - 1] < 0} {
                        #   set userArgsArray(vlan_id_repeat) 0
                        #} else {
                        #   set userArgsArray(vlan_id_repeat) [expr {$count/$vlan_id_count} - 1]
                        #}
                        if {![info exists userArgsArray(vlan_id_repeat)]} {
                            set userArgsArray(vlan_id_repeat) 0
                        }
                        if {![info exists userArgsArray(vlan_id_outer_repeat)]} {
                            set userArgsArray(vlan_id_outer_repeat) 0
                        }  
                    } else {
                        set userArgsArray(vlan_id_repeat) 0
                        set userArgsArray(vlan_id_outer_repeat) 0
                    }

                    if {$listName == "listl2VlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "vlan_id_repeat"] == -1} {
                            lappend ::$mns\::$listName "vlan_id_repeat";
                        }
                    }
                    if {$listName == "listl2OuterVlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "vlan_id_outer_repeat"] == -1} {
                            lappend ::$mns\::$listName "vlan_id_outer_repeat";
                        }
                    }
                }
                "inner" {
                    if {![info exists userArgsArray(vlan_id_repeat)]} {
                        set userArgsArray(vlan_id_repeat) 0
                    }
                    set repeat [expr $userArgsArray(vlan_id_repeat) + 1]
                    set userArgsArray(vlan_id_outer_repeat) [expr $vlan_id_count*$repeat - 1]
                    if {$listName == "listl2OuterVlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "vlan_id_outer_repeat"] == -1} {
                            lappend ::$mns\::$listName "vlan_id_outer_repeat";
                        }
                    }
                }
                "outer" {
                    if {![info exists userArgsArray(vlan_id_outer_repeat)]} {
                        set userArgsArray(vlan_id_outer_repeat) 0
                    }
                    set repeat [expr $userArgsArray(vlan_id_outer_repeat) + 1]
                    set userArgsArray(vlan_id_repeat) [expr $vlan_id_outer_count*$repeat - 1]
                    if {$listName == "listl2VlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "vlan_id_repeat"] == -1} {
                            lappend ::$mns\::$listName "vlan_id_repeat";
                        }
                    }
                }
            }
            
            switch -exact -- $userArgsArray(inner_qinq_incr_mode) {
               "both" {
                    # fix CR311406748
                    if {[info exists userArgsArray(inner_l3_protocol)]} {
                        if {[string match -nocase "ipv4" $userArgsArray(inner_l3_protocol)] && [info exist userArgsArray(inner_ip_src_count)]} {
                            set count $userArgsArray(inner_ip_src_count)
                        } else {
                            set count 1
                        }
                        
                        if {![info exists userArgsArray(inner_vlan_id_repeat)]} {
                            set userArgsArray(inner_vlan_id_repeat) 0
                        }
                        if {![info exists userArgsArray(inner_vlan_id_outer_repeat)]} {
                            set userArgsArray(inner_vlan_id_outer_repeat) 0
                        }  
                    } else {
                        set userArgsArray(inner_vlan_id_repeat) 0
                        set userArgsArray(inner_vlan_id_outer_repeat) 0
                    }

                    if {$listName == "listInnerl2VlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "inner_vlan_id_repeat"] == -1} {
                            lappend ::$mns\::$listName "inner_vlan_id_repeat";
                        }
                    }
                    if {$listName == "listInnerl2OuterVlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "inner_vlan_id_outer_repeat"] == -1} {
                            lappend ::$mns\::$listName "inner_vlan_id_outer_repeat";
                        }
                    }
                }
                "inner" {
                    if {![info exists userArgsArray(inner_vlan_id_repeat)]} {
                        set userArgsArray(inner_vlan_id_repeat) 0
                    }
                    set repeat [expr $userArgsArray(inner_vlan_id_repeat) + 1]
                    set userArgsArray(inner_vlan_id_outer_repeat) [expr $inner_vlan_id_count*$repeat - 1]
                    if {$listName == "listInnerl2OuterVlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "inner_vlan_id_outer_repeat"] == -1} {
                            lappend ::$mns\::$listName "inner_vlan_id_outer_repeat";
                        }
                    }
                }
                "outer" {
                    if {![info exists userArgsArray(inner_vlan_id_outer_repeat)]} {
                        set userArgsArray(inner_vlan_id_outer_repeat) 0
                    }
                    set repeat [expr $userArgsArray(inner_vlan_id_outer_repeat) + 1]
                    set userArgsArray(inner_vlan_id_repeat) [expr $inner_vlan_id_outer_count*$repeat - 1]
                    if {$listName == "listInnerl2VlanRangeModifier"} {
                        if {[lsearch -exact ::$mns\::$listName "inner_vlan_id_repeat"] == -1} {
                            lappend ::$mns\::$listName "inner_vlan_id_repeat";
                        }
                    }
                }
            }
            
        }
    }
    
    set listNames $listName
    catch {set listNames [set ::$mns\::$listName]}
    
    foreach element $listNames {
        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
        set userValue $userArgsArray($element);
        if { $element == "mac_dst_mode" && $userValue == "discovery" } {
            continue
        }
        if {[regexp step $element] && $headerType == "ethernet"} {
            if {!([regexp "\\." $userValue]||[regexp ":" $userValue])} {
                set userValue [::sth::Pppox::DoubleToMAC $userValue]
            }
        }
        #handle modifier mode
        if {[llength $offsetReferenceValue] > 1  || ([regexp mode $element] && $userValue == "list") } {
            set mode "TABLE"
            lappend listArgsList -ModifierMode $mode;
        } elseif {[regexp mode $element] && $userValue != "fixed"} {
            if {$listName == "listl2OtherVlanRangeModifier"} {
                #process the 3rd layer vlans
                set userValueNew ""
                set tableName "::$mns\::traffic_config_$element\_fwdmap"
                foreach val $userValue {
                    if {$val != "fixed"} {
                        set stcConst [set $tableName\($val)]
                        lappend userValueNew $stcConst
                    } else {
                         lappend userValueNew $val
                    }
                }
                lappend listArgsList -$stcAttr $userValueNew;
            } else {
                set tableName "::$mns\::traffic_config_$element\_fwdmap"
                set stcConst [set $tableName\($userValue)];
                lappend listArgsList -$stcAttr $stcConst;
            }
        } else {
            lappend listArgsList -$stcAttr $userValue;
        }
        if {[regexp step $element] && $headerType == "ethernet"} {
            if {[string is integer -strict $userArgsArray($element)]} {
                # user has entered integer step value
                set mask "00:00:FF:FF:FF:FF";
                set offsetVal 0;
                if {[llength $offsetReferenceValue] == 1} {
                    lappend listArgsList -offset $offsetVal -dataType NATIVE;
                }
            }
        }
    }
    if { $headerType == "ethernet"} {
        if {![regexp step [set ::$mns\::$listName]]} {
            if {$userArgsArray(mode) == "modify"} {
                set rangeList_random [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children-randomModifier]
                set rangeList_range [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children-rangeModifier]
                set rangeList_table [::sth::sthCore::invoke stc::get [set ::$mns\::handleCurrentStream] -children-tableModifier]
                foreach Obj [concat $rangeList_random $rangeList_range $rangeList_table] {
                    set ref [::sth::sthCore::invoke stc::get $Obj -OffsetReference]
                    if { $ref == $offsetReferenceName } {
                        set rangeModifier $Obj
                        break
                   }
                }
                if {$rangeModifier != "" && [regexp range $rangeModifier]} {
                    set stepVal [::sth::sthCore::invoke stc::get $rangeModifier -StepValue]
                    if {[string is integer -strict $stepVal]} {
                        set mask "00:00:FF:FF:FF:FF";
                        set offsetVal 0;
                        
                    }
                } else {
                    set mask "00:00:FF:FF:FF:FF";
                    set offsetVal 0;
                    if {[llength $offsetReferenceValue] == 1} {
                        lappend listArgsList -offset $offsetVal -dataType NATIVE;
                    }
                }
            } else {
                set mask "00:00:FF:FF:FF:FF";
                set offsetVal 0;
                if {[llength $offsetReferenceValue] == 1} {
                
                    lappend listArgsList -offset $offsetVal -dataType NATIVE;
                }
                
            }
        }  
    }
   
    
    if {$listName == "listl2OtherVlanRangeModifier"} {
        #process the other layer vlans
        lappend listArgsList -OffsetReference $offsetReferenceNameList -data $offsetReferenceValueList -mask $mask;
    } else {
        lappend listArgsList -OffsetReference $offsetReferenceName -data $offsetReferenceValue -mask $mask;
    }
    
    lappend listArgsList -EnableStream $::sth::Traffic::enableStream
    foreach {attr val} $listArgsList {
        set arrayArgsList($attr) $val;
    }
    if {$listName == "listl2OtherVlanRangeModifier"} {
        #process the other layer vlans
        array set retVal [getOtherVlanCount [set ::$mns\::listl2encap_OtherVlan]]
        set valNum $retVal(vlan_modifier_count)
        for {set i 0} {$i < $valNum} {incr i} {
            array unset arrayArgsListNew
            array set arrayArgsListNew {}
            foreach attr [array names arrayArgsList] {
                if {[llength $arrayArgsList($attr)] < [expr $i + 1]} {
                    #process the enable stream, it should be configured
                    if {[regexp -nocase "EnableStream" $attr]} {
                        set arrayArgsListNew($attr) $::sth::Traffic::enableStream
                    }
                    if {[regexp -nocase "mask" $attr]} {
                        set arrayArgsListNew($attr) 4095
                    }
                } else {
                    set value [lindex $arrayArgsList($attr) $i]
                    set arrayArgsListNew($attr) $value
                }
                
            }
            set handle [set ::$mns\::handleCurrentStream]
            #if the mode is modify
            if {$userArgsArray(mode) == "modify"} {
                set attrList [array get arrayArgsListNew]
                if {[regexp {^-} $attrList]} {
                    regsub {^-} $attrList {} attrList 
                }
                foreach {attr val} $attrList {
                    if {[info exists prioritisedAttributeList($attr)]} {
                        set arrayArgsListNew($attr) $val
                    }
                } 
            }
            set arrayList [array get arrayArgsListNew]
            ::sth::Traffic::ProcessModifier $handle $arrayList;
        }

    } else {
        #set the default value for RecycleCount
        if {![info exists arrayArgsList(-RecycleCount)]} {
            set arrayArgsList(RecycleCount) 1
        }
        
        set handle [set ::$mns\::handleCurrentStream]
        #if the mode is modify
        if {$userArgsArray(mode) == "modify"} {
            set attrList [array get arrayArgsList]
            if {[regexp {^-} $attrList]} {
                regsub {^-} $attrList {} attrList 
            }
            foreach {attr val} $attrList {
                if {[info exists prioritisedAttributeList($attr)]} {
                    set arrayArgsList($attr) $val
                }
            } 
        }
        set arrayList [array get arrayArgsList]
        set retHnd [::sth::Traffic::ProcessModifier $handle $arrayList]
        set ::sth::Traffic::listModifierMap($retHnd) 1
    }
}


proc ::sth::Traffic::processCreateL4RangeModifier {Handle listName tag} {
    
    set _procName "processCreateL4RangeModifier";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
    
    set listArgsList {};
    array set arrayArgsList {};
    
    switch -- $listName {
        "listTcpPortSrcRangeModifier" {
            set portOption "sourcePort"
            set portArg "tcp_src_port"
            set mask "65535";
            set modeArg "tcp_src_port_mode"
            set countArg "tcp_src_port_count"
            set stepArg "tcp_src_port_step"
            set repeatArg "tcp_src_port_repeat_count"
        }
        "listTcpPortDstRangeModifier" {
            set portOption "destPort"
            set portArg "tcp_dst_port"
            set mask "65535";
            set modeArg "tcp_dst_port_mode"
            set countArg "tcp_dst_port_count"
            set stepArg "tcp_dst_port_step"
            set repeatArg "tcp_dst_port_repeat_count"
        }
         "listUdpPortSrcRangeModifier" {
            set portOption "sourcePort"
            set portArg "udp_src_port"
            set mask "65535";
            set modeArg "udp_src_port_mode"
            set countArg "udp_src_port_count"
            set stepArg "udp_src_port_step"
            set repeatArg "udp_src_port_repeat_count"
        }
          "listUdpPortDstRangeModifier" {
            set portOption "destPort"
            set portArg "udp_dst_port"
            set mask "65535";
            set modeArg "udp_dst_port_mode"
            set countArg "udp_dst_port_count"
            set stepArg "udp_dst_port_step"
            set repeatArg "udp_dst_port_repeat_count"
        }
        "listl4DstRangeModifier" {
            set portOption "destAddr"

            if {[regexp ipv4 $Handle]} {
                set mask "255.255.255.255";
                set portArg "l4_ip_dst_addr"
                set modeArg "l4_ip_dst_mode"
                set countArg "l4_ip_dst_count"
                set stepArg "l4_ip_dst_step"
                set repeatArg "l4_ip_dst_repeat_count"
            } else {
                if {$userArgsArray(enable_stream) == 1} {
                   set mask "FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF";
                } else {
                   set mask "::FFFF:FFFF";
                }
                set portArg "l4_ipv6_dst_addr"
                set modeArg "l4_ipv6_dst_mode"
                set countArg "l4_ipv6_dst_count"
                set stepArg "l4_ipv6_dst_step"
                set repeatArg "l4_ipv6_dst_repeat_count"
            }

        }
        "listl4SrcRangeModifier" {
            set portOption "sourceAddr"
            if {[regexp ipv4 $Handle]} {
                set mask "255.255.255.255";
                set portArg "l4_ip_src_addr"
                set modeArg "l4_ip_src_mode"
                set countArg "l4_ip_src_count"
                set stepArg "l4_ip_src_step"
                set repeatArg "l4_ip_src_repeat_count"
            } else {
                if {$userArgsArray(enable_stream) == 1} {
                   set mask "FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF";
                } else {
                   set mask "::FFFF:FFFF";
                }
                set portArg "l4_ipv6_src_addr"
                set modeArg "l4_ipv6_src_mode"
                set countArg "l4_ipv6_src_count"
                set stepArg "l4_ipv6_src_step"
                set repeatArg "l4_ipv6_src_repeat_count"
            }

        }
    }
    
    set HandleName [::sth::sthCore::invoke stc::get $Handle -name]
          
    set offsetReferenceName "$HandleName\.$portOption";
    set startValue [::sth::sthCore::invoke stc::get $Handle -$portOption]
    if {[info exists userArgsArray($portArg)]} {
        set port_list [split $userArgsArray($portArg) " "]
        set startValue $port_list
    }
    
    set offsetReferenceValue $startValue
    set arrayArgsList(OffsetReference) $offsetReferenceName
    set arrayArgsList(data) $offsetReferenceValue 
            
    #set ModifierMode
    if {[info exists userArgsArray($modeArg)]} {
        set mode $userArgsArray($modeArg)
        set tableName "::$mns\::traffic_config_$modeArg\_fwdmap"
        set mode [set $tableName\($mode)];
        
    } else {
        set mode "INCR"
    }
    
    if {[llength $startValue] > 1} {
        set arrayArgsList(ModifierMode) TABLE
    } else {
        set arrayArgsList(ModifierMode) $mode
    }
            
    #set count
    if {[info exists userArgsArray($countArg)]} {
        set count $userArgsArray($countArg)
    } else {
        set count 1
    }
    set arrayArgsList(RecycleCount) $count

    #set repeatcount
    if {[info exists userArgsArray($repeatArg)]} {
        set repeat_count $userArgsArray($repeatArg)
    } else {
        set repeat_count 1
    }
    set arrayArgsList(RepeatCount) $repeat_count

    #set step
    if {[info exists userArgsArray($stepArg)]} {
        set step $userArgsArray($stepArg)
    } else {
        set step 1
    }
    
    set arrayArgsList(StepValue) $step
    set arrayArgsList(Mask) $mask 
    
    #set enable stream
    set arrayArgsList(EnableStream) $::sth::Traffic::enableStream
    
    set handle [set ::$mns\::handleCurrentStream]
    if {$userArgsArray(mode) == "modify"} {
        #handle arrayArgsList, generate the list with default value and without default value sepereately
        set attrList [array get arrayArgsList]
        foreach {attr val} $attrList {
            if {[info exists prioritisedAttributeList($attr)]} {
                set arrayArgsList($attr) $val
            }
        }
    }
    set arrayList [array get arrayArgsList]
    ::sth::Traffic::ProcessModifier $handle $arrayList;
}


proc ::sth::Traffic::ProcessModifier {parentHdl arrayList} {
    
    set _procName "ProcessModifier";
    set ObjectName ""
    set listArgsList ""
    set myarrayList ""
    
    #delete the "-" of the arrayList
    foreach value $arrayList {
        if {[regexp {^-} $value]} {
            regsub {^-} $value {} value
        }
        lappend myarrayList $value
    }
    array set myarrayArgsList $myarrayList;
    
    # prepare the arguments 
    set OffsetReference $myarrayArgsList(OffsetReference)
    if {![info exists myarrayArgsList(ModifierMode)]} {
        set myarrayArgsList(ModifierMode) "INCR"
    }
    set ModifierMode [string toupper $myarrayArgsList(ModifierMode)]
    set modifierHandle ""
    set ExistedModifierMode ""
    
    #check the existed modifierMode
    set rangeList_random [::sth::sthCore::invoke stc::get $parentHdl -children-randomModifier]
    set rangeList_range [::sth::sthCore::invoke stc::get $parentHdl -children-rangeModifier]
    set rangeList_table [::sth::sthCore::invoke stc::get $parentHdl -children-tableModifier]
    foreach Obj [concat $rangeList_random $rangeList_range $rangeList_table] {
        set ref [::sth::sthCore::invoke stc::get $Obj -OffsetReference]
       
        if { $ref == $OffsetReference } {
            set modifierHandle $Obj
            if {[regexp {random} $modifierHandle]} {
                set ExistedModifierMode "RANDOM"
            } elseif {[regexp {range} $modifierHandle]} {
                set ExistedModifierMode [string toupper [::sth::sthCore::invoke stc::get $modifierHandle -ModifierMode]]
            } elseif {[regexp {table} $modifierHandle]} {
                set ExistedModifierMode "TABLE"
            }           
            break
       }
    }
    
    #handle the config arguments    
    switch $ModifierMode {
        "FIXED" {
            if { $modifierHandle != ""} {
                if {[catch {::sth::sthCore::invoke stc::delete $modifierHandle} errMsg]} {
                    ::sth::sthCore::log error $errMsg
                    return -code error $errMsg
                } else {
                    ::sth::sthCore::log debug "$_procName: Calling stc::delete $modifierHandle in fixed mode"
                }
            }
            return $::sth::sthCore::SUCCESS;
        }
        "RANDOM" {
            set ObjectName randomModifier
            set AttrConfigList {DataType EnableStream Mask Offset RecycleCount RepeatCount}
        }
        "TABLE" {
            set ObjectName tableModifier
            set AttrConfigList {data DataType EnableStream Offset RepeatCount}
        }
        default {
            set ObjectName rangeModifier
            set AttrConfigList {data DataType EnableStream Mask ModifierMode Offset RecycleCount RepeatCount StepValue}
        }
    }
    foreach attr $AttrConfigList {
        if {[info exists myarrayArgsList($attr)]} {
        lappend listArgsList -$attr $myarrayArgsList($attr);
        } else {
            #check if the attr difference is up case and lower case 
            foreach {attrCmpcase value} $myarrayList {
                if {[string match -nocase $attr $attrCmpcase]} {
                    lappend listArgsList -$attr $myarrayArgsList($attrCmpcase);
                }
            }
        }
    }

    # delete the existed modifierMode       
    if {$modifierHandle != ""} {
        if {[info exists ::sth::Traffic::listModifierMap] && [info exists ::sth::Traffic::listModifierMap($modifierHandle)]} {
            set modifierHandle ""
        } elseif {$ExistedModifierMode != $ModifierMode} {
                if {[catch {::sth::sthCore::invoke stc::delete $modifierHandle} errMsg]} {
                     ::sth::sthCore::log error $errMsg
                     return -code error $errMsg
                }
                set modifierHandle ""
        }
    }
     
    # create object  
    if {$modifierHandle == ""} {
        if {[catch {::sth::sthCore::invoke ::stc::create $ObjectName -under $parentHdl -OffsetReference $OffsetReference} modifierHandle]} {
             :sth::sthCore::log error $modifierHandle
             return -code error $modifierHandle
        }
    }
        
    #config
    ::sth::sthCore::log debug "$_procName: Calling stc::config $ObjectName $parentHdl $listArgsList"
    set cmdName "::sth::sthCore::invoke ::stc::config $modifierHandle $listArgsList";
    if {[catch {eval $cmdName} errMsg]} {
         ::sth::sthCore::log error $errMsg
         return -code error $errMsg
    }
    return $modifierHandle
}


# Added by xiaozhi on Jun 15th, 2011
# (CR 294055582) HLTAPI raw stream with src/dst IP modifier set to Random but not work.
# For xx_xx_mode(ip_src_mode/ip_dst_mode), option "Random" was designed to be "Shuffle" of RangeModifier in old version;
####
proc ::sth::Traffic::processCreateL3RangeModifier {Handle listName tag} {
    # Default IP address for src/dst ip addresses --> "192.85.1.2"
    set _procName "processCreateL3RangeModifier";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;

    set listArgsList {};
    array set arrayArgsList {};
    set prefixLenAttrNeeded 0;
    
    if {[regexp -nocase {igmp:Igmpv3report(\d+)?$} $Handle]} {
        ::sth::sthCore::log info "$_procName: Range Modifier is not supported for $Handle."
        return
    }
    
    # Get the name of the header here
    ::sth::sthCore::log debug "$_procName: Calling ::stc::get $Handle -name"
    if {[catch {::sth::sthCore::invoke ::stc::get $Handle -name} headerName]} {
        ::sth::sthCore::processError trafficKeyedList "$_procName: $Handle -name $headerName " {}
        return $::sth::sthCore::FAILURE;
    } else {
        ::sth::sthCore::log info "$_procName: $Handle -name $headerName "
    }
    
    ################################
    #  get Modifier OffsetReference
    #  get Modifier data
    ################################
    #CR 325322805  Mod Liu Yinmeng
    #if it is bound traffic, need to get the ip address using emulation handle as below
    if {([regexp dest $tag] && [info exists userArgsArray(emulation_dst_handle)]) || ([regexp source $tag] && [info exists userArgsArray(emulation_src_handle)]) } {
        if {[regexp dest $tag]} {
            set emulation_hdl $userArgsArray(emulation_dst_handle)
        } else {
            set emulation_hdl $userArgsArray(emulation_src_handle)
        }   
        set BlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_hdl]
        if {[regexp "networkblock" $BlockHandle]} {
            #this may be different from the display of GUI, what the bound stream of routeblock cares is the traffic betweeb different networks, not the specific host
            set BlockHandle [lindex $BlockHandle 0]
            set offsetReferenceValue ""
            if {[regexp "networkblock" $BlockHandle]} {
                set offsetReferenceValue [::sth::sthCore::invoke "stc::get $BlockHandle -StartIpList"]
            }
        } else {
            set offsetReferenceValue ""
            foreach BlockHandleTmp $BlockHandle {
                if {[catch {::sth::sthCore::invoke stc::get $BlockHandleTmp -address} offsetReferenceValueTmp]} {
                    ::sth::sthCore::processError trafficKeyedList "$_procName: $BlockHandle -$tag $offsetReferenceValue " {}
                    return $::sth::sthCore::FAILURE;
                } else {
                    set offsetReferenceValue "$offsetReferenceValue $offsetReferenceValueTmp" 
                    ::sth::sthCore::log info "$_procName: $BlockHandleTmp -$tag $offsetReferenceValueTmp ";
                }   
            }
        }
    } elseif {[catch {::sth::sthCore::invoke stc::get $Handle -$tag} offsetReferenceValue]} {
        ::sth::sthCore::processError trafficKeyedList "$_procName: $Handle -$tag $offsetReferenceValue" {}
        return $::sth::sthCore::FAILURE;
    } else {
        # use the default here.
        # Putting the default here as of now. Will move it to the table later.
        if {[regexp . $offsetReferenceValue] || [regexp : $offsetReferenceValue]} {
            # nothing needs to be done here
        } else {
            if {[regexp ipv4 $Handle]} {
                #set offsetReferenceValue "192.85.1.2";
                set arrayArgsList(offsetReferenceValue) "192.85.1.2";
            } else {
                #set offsetReferenceValue "2000::2";
                set arrayArgsList(offsetReferenceValue) "2000::2";
            }
        }
        ::sth::sthCore::log info "$_procName: $Handle -$tag $offsetReferenceValue ";
    }
    
    # dirty solution for now. Appending the data and the mask to the args list for now.
    # Once the flag (CR: <put CR # here>) is fixed, the this would change accordingly.
    # As of now mask is set to 255.255.255.255 so depending on the step value, all octets can be touched upon. 
    
    #lappend listArgsList -OffsetReference $headerName\.$tag -data $offsetReferenceValue;
    set arrayArgsList(OffsetReference) $headerName\.$tag;
    set arrayArgsList(data) $offsetReferenceValue;
            
    #############################################################
    ############  #handle the mode and count      ###############
    #############################################################  
    switch -- $listName {
        "listl3SrcRangeModifier" {
            if {$userArgsArray(l3_protocol) == "ipv4" || $userArgsArray(l3_protocol) == "arp"} {
                set modeArg "ip_src_mode"
                set modeCount "ip_src_count"
            } elseif {$userArgsArray(l3_protocol) == "ipv6"} {
                set modeArg "ipv6_src_mode"
                set modeCount "ipv6_src_count"
            }
        }
        "listl3DstRangeModifier" {
             if {$userArgsArray(l3_protocol) == "ipv4" || $userArgsArray(l3_protocol) == "arp"} {
                set modeArg "ip_dst_mode"
                set modeCount "ip_dst_count"
            } elseif {$userArgsArray(l3_protocol) == "ipv6"} {
                set modeArg "ipv6_dst_mode"
                set modeCount "ipv6_dst_count"
            }
        }
        "listl3OuterSrcRangeModifier" {
            if {$userArgsArray(l3_outer_protocol) == "ipv4"} {
                set modeArg "ip_src_outer_mode"
                set modeCount "ip_src_outer_count"
            } else {
                set modeArg "ipv6_src_outer_mode"
                set modeCount "ipv6_src_outer_count"
            }
        }
        "listl3OuterDstRangeModifier" {
            if {$userArgsArray(l3_outer_protocol) == "ipv4"} {
                set modeArg "ip_dst_outer_mode"
                set modeCount "ip_dst_outer_count"
            } else {
                set modeArg "ipv6_dst_outer_mode"
                set modeCount "ipv6_dst_outer_count"
            }
        }
        "listInnerl3SrcRangeModifier" {
            set modeArg "inner_ip_src_mode"
            set modeCount "inner_ip_src_count"
        }
        "listInnerl3DstRangeModifier" {
            set modeArg "inner_ip_dst_mode"
            set modeCount "inner_ip_dst_count"
            
        }
        "listIgmpGroupAddrRangeModifier" {
            if {$userArgsArray(l4_protocol) == "igmp"} {
                set modeArg "igmp_group_mode"
                set modeCount "igmp_group_count"
            } else {
                ::sth::sthCore::processError trafficKeyedList "$_procName: igmp header should assgined l4_protocol with igmp" {}
                return $::sth::sthCore::FAILURE;
            }
        }
        "listMacGwRangeModifier" {
            set modeArg "none"
            set modeCount "mac_discovery_gw_count"
        }
        "listInnerGwRangeModifier" {
            set modeArg "none"
            set modeCount "inner_gw_count"
        }
        "listArpMacSrcRangeModifier" {
            set modeArg "arp_src_hw_mode"
            set modeCount "arp_src_hw_count"
        }
        "listArpMacDstRangeModifier" {
            set modeArg "arp_dst_hw_mode"
            set modeCount "arp_dst_hw_count"
        }
    }
    

    #if it is bound traffic, no need to handle range modifier.
    set boundTrafficFlag 0
    if {[info exists userArgsArray(emulation_src_handle)] || [info exists userArgsArray(emulation_dst_handle)]} {
        set boundTrafficFlag 1
    }
    set srcCount 1
    if {[info exists userArgsArray($modeCount)]} {
        set srcCount $userArgsArray($modeCount)
    }
    if {($boundTrafficFlag && $srcCount == 1)} {
        ::sth::sthCore::log info "$_procName: no need to call ip range modifier for inner header. ";
        return $::sth::sthCore::SUCCESS;
    }
    
    #############################################################
    ############  handle modifiermode  ####################
    ############################################################# 
    if {[llength $arrayArgsList(data)] > 1} {
        set mode "TABLE"
    } elseif {[info exists userArgsArray($modeArg)]} {
        if {$userArgsArray($modeArg) == "fixed"} {
            set mode "FIXED"
        } else {
            set mode $userArgsArray($modeArg)
            set tableName "::$mns\::traffic_config_$modeArg\_fwdmap"
            set mode [set $tableName\($mode)];
        }
    } else {
        set mode "INCR"
    }
    set arrayArgsList(ModifierMode) $mode;
    
    
    #############################################################
    ############  handle ip_dst_block_count  ####################
    #############################################################  
    # destAddr && ip_dst_block_count -> create multiple blocks of dest ipv4 address, with ip_dst_block_step to be incr step among blocks,
    # and ip_dst_step to be incr step within each block. 
    #   example: destAddr 10.0.0.1, ip_dst_block_count 2, ip_dst_block_step 0.0.1.0, ip_dst_count 10, ip_dst_step 0.0.0.1
    #   TableModifier: 10.0.0.1  10.0.0.2  10.0.0.3  10.0.0.4  10.0.0.5
    #                  10.0.1.1  10.0.1.2  10.0.1.3  10.0.1.4  10.0.1.5
    # comments above added by xiaozhi 2011.6.19
    if {[regexp destAddr $tag] && [info exists userArgsArray(ip_dst_block_count)]} {
        set blkNum $userArgsArray(ip_dst_block_count)
        if {[info exists userArgsArray(ip_dst_block_step)]} {
            set blkStep $userArgsArray(ip_dst_block_step)
        } else {
            set blkStep "0.0.1.0"
        }
        if {[info exists userArgsArray(ip_dst_count)]} {
            set dstNum $userArgsArray(ip_dst_count)
        } else {
            set dstNum "1"
        }
        if {[info exists userArgsArray(ip_dst_step)]} {
            set dstStep $userArgsArray(ip_dst_step)
        } else {
            set dstStep "0.0.0.1"
        }
        
        # CR200487631, when use table modifer to generate address list. Need to consider step mode
        if {[info exists userArgsArray(ip_dst_mode)]} {
            if {$userArgsArray(ip_dst_mode) == "increment"} {
                set mode "INCR"
            } else {
               set mode "DECR"
            } 
        } else {
            set mode "INCR"
        }
       
        set addr $userArgsArray(ip_dst_addr)
        for {set i 0} {$i < $blkNum} {incr i} {
            set tempaddr [::sth::sthCore::updateIpAddress 4 $addr $blkStep $i $mode] 
            for {set j 0} {$j < $dstNum} {incr j} {
                lappend addList $tempaddr
                set tempaddr [::sth::sthCore::updateIpAddress 4 $tempaddr $dstStep 1 $mode]
            }
        }
    }
    
    #############################################################
    ############  handle mac_discovery_gw_count  ################
    #############################################################
    
    if {[info exists userArgsArray(mac_discovery_gw_count)]} {
        set gwcount $userArgsArray(mac_discovery_gw_count)
    } else {
        set gwcount 1
    }
    if {[info exist userArgsArray(ip_src_count)]} {
        set srccount $userArgsArray(ip_src_count)
    } else {
        set srccount 1
    }
    if {[expr $srccount/$gwcount] > 1} {
        set ipblkcount [expr $srccount/$gwcount]
    }
    if {[regexp gateway $tag] && [info exists ipblkcount]} {
        lappend listArgsList -RepeatCount [expr $ipblkcount -1];
    }
    
    #############################################################
    ############  handle mac_discovery_gw_count  ################
    #############################################################
    # sourceAddr && ip_src_count/mac_discovery_gw_count -> create multiple blocks of source ipv4 address,
    # with mac_discovery_gw_step to be incr step among blocks, and ip_src_step to be incr step within each block. 
    #   example: sourceAddr 10.0.0.1, ipblkcount 2, mac_discovery_gw_step 0.0.1.0, ip_src_count 10, ip_src_step 0.0.0.1
    #   TableModifier: 10.0.0.1  10.0.0.2  10.0.0.3  10.0.0.4  10.0.0.5
    #                  10.0.1.1  10.0.1.2  10.0.1.3  10.0.1.4  10.0.1.5
    # comments above added by xiaozhi 2011.6.19
    
    if {[regexp sourceAddr $tag] && [info exists ipblkcount] && [info exists userArgsArray(mac_discovery_gw_count)]} {
        set srcNum $ipblkcount
        if {[info exists userArgsArray(mac_discovery_gw_step)]} {
            set blkStep $userArgsArray(mac_discovery_gw_step)
        } else {
            set blkStep "0.0.1.0"
        }
        if {[info exists userArgsArray(mac_discovery_gw_count)]} {
            set blkNum $userArgsArray(mac_discovery_gw_count)
        } else {
            set blkNum "1"
        }
        if {[info exists userArgsArray(ip_src_step)]} {
            set srcStep $userArgsArray(ip_src_step)
        } else {
            set srcStep "0.0.0.1"
        }
        # CR200487631, when use table modifer to generate address list. Need to consider step mode
        if {[info exists userArgsArray(ip_src_mode)]} {
            if {$userArgsArray(ip_src_mode) == "increment"} {
                set mode "INCR"
            } else {
                set mode "DECR"
            } 
        } else {
            set mode "INCR"
        }
       
        set addr $userArgsArray(ip_src_addr)
        for {set i 0} {$i < $blkNum} {incr i} {
            set tempaddr [::sth::sthCore::updateIpAddress 4 $addr $blkStep $i $mode] 
            for {set j 0} {$j < $srcNum} {incr j} {
                lappend addList $tempaddr
                set tempaddr [::sth::sthCore::updateIpAddress 4 $tempaddr $srcStep 1 $mode]
            }
        }
    }
    
    ################################
    #  get Modifier mask
    ################################
    
    if {[regexp ipv4|igmp $Handle]} {
        #lappend listArgsList -mask 255.255.255.255;
        set arrayArgsList(mask) "255.255.255.255";
    } else {
       if {$userArgsArray(enable_stream) == 1} {
           set arrayArgsList(mask) "FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF:FFFF";
       } else {
           set arrayArgsList(mask) "::FFFF:FFFF";
       }
    }
    
    #MOD Fei Cheng 08-10-10
    if {[regexp arp $Handle]} {
         #set mask and step value for arp hw addr          
         if {[regexp HwAddr $tag]} {
            set arrayArgsList(mask) "00:00:FF:FF:FF:FF";
            set arrayArgsList(StepValue) "00:00:00:00:00:01";
         }
         #set mask and step value for arp ip addr
         if {[regexp PAddr $tag]} {
            set arrayArgsList(mask) "255.255.255.255";
            set arrayArgsList(StepValue) "0.0.0.1";
         }
      
    }
    
    ################################
    #  get Modifier stepValue
    ################################
    
    ##### This just considers ipv4, need to add code for ipv6 
    if {[regexp ipv4|igmp $Handle]} {
        if {$tag == "sourceAddr"} {
            if {[regexp -nocase "listInner" $listName]} {
                if {![info exists userArgsArray(inner_ip_src_step)]} {
                    set arrayArgsList(StepValue) 0.0.0.1;
                }
            } else {
                if {![info exists userArgsArray(ip_src_step)]} {
                    set arrayArgsList(StepValue) 0.0.0.1;
                }
            }
        } elseif {$tag == "destAddr"} {
            if {[regexp -nocase "listInner" $listName]} {
                if {![info exists userArgsArray(inner_ip_dst_step)]} {
                    set arrayArgsList(StepValue) 0.0.0.1;
                }
            } else {
                if {![info exists userArgsArray(ip_dst_step)]} {
                    set arrayArgsList(StepValue) 0.0.0.1;
                }
            }
        } elseif {$tag == "gateway"} {
            if {![info exists userArgsArray(mac_discovery_gw_step)]} {
                set arrayArgsList(StepValue) 0.0.0.1;  
            }
        } elseif {$tag == "groupAddress"} {
            if {![info exists userArgsArray(igmp_group_step)]} {
                set arrayArgsList(StepValue) 0.0.0.1;
            }
        }
    } elseif {[regexp ipv6 $Handle]} {
        if {$tag == "sourceAddr"} {
            if {![info exists userArgsArray(ipv6_src_step)]} {
                set arrayArgsList(StepValue) "::1"
            }
        } elseif {$tag == "destAddr"} {
            if {![info exists userArgsArray(ipv6_dst_step)]} {
                set arrayArgsList(StepValue) "::1"
            }
        } elseif {$tag == "gateway"} {
            if {![info exists userArgsArray(mac_discovery_gw_step)]} {
                set arrayArgsList(StepValue) "::1"
            }
        }
    }
  

    foreach element [set ::$mns\::$listName] {
        set stcAttr [set ::$mns\::traffic_config_stcattr($element)];
        ::sth::sthCore::log info "$_procName HLT: $element \t STC: $stcAttr"
        set userValue $userArgsArray($element);
        if {![regexp mode $element]} {
            set arrayArgsList($stcAttr) $userValue;
        }
        
        #######################################
        # handle step for ipv6 src/st addr 
        #######################################
        if {[regexp step $element] && [regexp ipv6 $Handle]} {
            if {[string is integer -strict $userArgsArray($element)]} {
                # entered step value is in integer format
                set arrayArgsList(mask) "FFFF";
                set normalizedIPAddress [::ip::normalize $offsetReferenceValue];
                set splitList [split $normalizedIPAddress :];
                
                # default case: prefix length 64
                # taking last 2 bytes
                set data [lindex $splitList 7];
                set arrayArgsList(data) $data;
                set arrayArgsList(offset) 14;
                set arrayArgsList(dataType) Byte;
                
                # convert integer to hex
                set step [format %x $userArgsArray($element)]
                set arrayArgsList(StepValue) $step;
                set prefixLenAttrNeeded 1;
            }
        }
        
        ############################################
        # handle prefix length of ip src/dst address
        ############################################
        if {[regexp _len $element] && [regexp ipv6 $Handle] && $prefixLenAttrNeeded == 1} {
            set prefixLen $userArgsArray($element);
   
            # get the mask
            set len [expr 128-$prefixLen+1]
            for {set i 0} {$i < $len} {incr i} {
                append binStr 1
            }

            binary scan [binary format b* $binStr] h* hexStr
            set hexLength [string length $hexStr]
            for {set i $hexLength} {$i > 0} {incr i -1} {
                append newHexStr [string index $hexStr [expr $i-1]]
            }
            
            if {$hexLength%4 != 0} {
                set remain [expr 4-$hexLength%4]
                for {set j 0} {$j < $remain} {incr j} {
                    set newHexStr "0$newHexStr" 
                }
            }
            set arrayArgsList(mask) $newHexStr
            
            # get the offset
            set maskLength [string length $newHexStr]
            set offset [expr 16-$maskLength/2]
            set arrayArgsList(offset) $offset
            
            # get the step
            
            if {[regexp "src" $element]} {
                if {[info exists userArgsArray(ipv6_src_step)]} {
                    set step $userArgsArray(ipv6_src_step);
                } else {
                    set step 1
                }
            } elseif {[regexp "dst" $element]} {
                if {[info exists userArgsArray(ipv6_dst_step)]} {
                    set step $userArgsArray(ipv6_dst_step);
                } else {
                    set step 1
                }
            }
            set newStep [format %x $step]
            set arrayArgsList(StepValue) $newStep;
        }
    }
    
    set attrList [array get arrayArgsList];
    foreach {attr val} $attrList {
        lappend listArgsList $attr $val;
    }
    
    #MOD Fei Cheng 08-10-09
    #Modifier offset reference cannot be set at gateway when streams are not enabled.
    #if {$tag == "gateway"} {
    #   lappend listArgsList -EnableStream true;
    #}
    if {[regexp "gateway" $tag] && ([info exists userArgsArray(mac_discovery_gw_step)] || [info exists userArgsArray(mac_discovery_gw_count)]) } {
        # STC design - Modifier Offset Reference can not be set at gateway when streams are not enabled
       lappend listArgsList EnableStream true;
    } else {
       lappend listArgsList EnableStream $::sth::Traffic::enableStream;
    }
    
    #set the default value for RecycleCount
    if {![info exists arrayArgsList(RecycleCount)]} {
               set arrayArgsList(RecycleCount) 1
    }
        
    #if the mode is modify
    set handle [set ::$mns\::handleCurrentStream]
     
    foreach {attr val} $listArgsList {
        set arrayArgsList($attr) $val;
    }
    
    if {$userArgsArray(mode) == "modify"} {
        #handle arrayArgsList, generate the list with default value and without default value sepereately
         set attrList [array get arrayArgsList]
        if {[regexp {^-} $attrList]} {
            regsub {^-} $attrList {} attrList 
        }
        foreach {attr val} $attrList {
            if {[info exists prioritisedAttributeList($attr)]} {
                set arrayArgsList($attr) $val
            }
        }
        
    } else {
        if {[regexp "gateway" $tag] && ([info exists userArgsArray(mac_discovery_gw_step)] || [info exists userArgsArray(mac_discovery_gw_count)])} {
            set arrayArgsList(EnableStream) "true"
        } else {
            set arrayArgsList(EnableStream) $::sth::Traffic::enableStream
        }
        if {([regexp destAddr $tag] && [info exists userArgsArray(ip_dst_block_count)] && (![info exists userArgsArray(ip_dst_mode)] || ([info exists userArgsArray(ip_dst_mode)] && $userArgsArray(ip_dst_mode) != "random" && $userArgsArray(ip_dst_mode) != "shuffle")))
           || ([regexp sourceAddr $tag] && [info exists ipblkcount] && [info exists userArgsArray(mac_discovery_gw_count)])
           && (![info exists userArgsArray(ip_src_mode)] || ([info exists userArgsArray(ip_src_mode)] && $userArgsArray(ip_src_mode) != "random" && $userArgsArray(ip_src_mode) != "shuffle" ))} {
            set arrayArgsList(ModifierMode) "table"
            set arrayArgsList(data) $addList
        }
    }
    set arrayList [array get arrayArgsList]
    ::sth::Traffic::ProcessModifier $handle $arrayList;
}

proc ::sth::Traffic::processMacDstMode { headerHandle userArgsArray} {
    upvar $userArgsArray myUserArgsArray
    set parentHandle [::sth::sthCore::invoke stc::get $headerHandle -parent ]
    set grandParentHandle [::sth::sthCore::invoke stc::get $parentHandle -parent]
    set numStreamsTobeArped $::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($grandParentHandle)
    if {$numStreamsTobeArped == 0 && [info exists myUserArgsArray(mac_discovery_gw)]} {
        set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($grandParentHandle) 1
        set ::sth::Session::PERPORTARPRESULTHANDLE($grandParentHandle) [::sth::sthCore::invoke ::stc::create arpndresults -under $grandParentHandle]
    } else {
        set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($grandParentHandle) [expr {1 + $numStreamsTobeArped}]
    }        
    return $grandParentHandle;
}

# 3.30 enhancement 4/21/09
# Enable/disable control plane traffic, such as Ping and ARP
# added by xiaozhi, liu
proc ::sth::Traffic::processControlPlane {switchName} {
    
    set _procName "processControlPlane";
    
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set ctlPlane $userArgsArray($switchName);
    set stcAttr [set ::$mns\::traffic_config_stcattr($switchName)];
    
    ::sth::sthCore::log info "$_procName HLT: $switchName \t STC: -stcAttr $ctlPlane"
    lappend ::$mns\::listProcessedList -$stcAttr $ctlPlane;  
    
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::Traffic::GetLayerTwoHandle { emulation_handle } {
    upvar userArgsArray userArgsArray;
    if {[info exists userArgsArray(l2_encap)]} {
        switch -- $userArgsArray(l2_encap) {
            "ethernet_ii_vlan" {
                set L2Handle [::sth::sthCore::invoke stc::get $emulation_handle -children-VlanIf]
                set L2Handle [lindex $L2Handle 0]
            }
            "ethernet_ii" {
                set L2Handle [::sth::sthCore::invoke stc::get $emulation_handle -children-EthIIIf]
            }
        }
    }
    
    return $L2Handle   
}


proc ::sth::Traffic::GetIpOrNetworkBlockHandle { emulation_handles } {
    set blockHandleList ""
    set networkBlockHandle 0
    set hostBlockHandle 0
    set useNativeBinding 0
    set blockHandle 0
    array set myTempHandleArray {}
    foreach emulation_handle $emulation_handles {
        if {[::info exists myTempHandleArray($emulation_handle)]} {
            continue
        } else {
            set myTempHandleArray($emulation_handle) 1
        }
        if {[regexp ripsessionhandle [string tolower $emulation_handle]]} {
            set emulationType ripsessionhandle 
        } else {
            set emulationType [::sth::Traffic::TrimTailNumber [string tolower $emulation_handle]]
            if { [string first "routerconfig" $emulationType] >= 0 } {
                set emulationType router
                set emulation_handle [::sth::sthCore::invoke ::stc::get $emulation_handle -parent]
            }
        }
        
        switch $emulationType {
            ipv4prefixlsp {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]
            }
            rsvpegresstunnelparams -
            rsvpingresstunnelparams {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv4NetworkBlock} Ipv4NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: \
                        Cannot get networkBlockHandle(Ipv4NetworkBlock) from $emulation_handle: $Ipv4NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv4NetworkBlock
            }
            bgpipv4routeconfig {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]
            }
            bgpipv6routeconfig {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv6NetworkBlock]
            }
            host -
            router -
            emulateddevice {
                set hostBlockHandle [::sth::Traffic::GetFirstIpHeader $emulation_handle]
                if { $hostBlockHandle == 0} {
                    set hostBlockHandle [::sth::Traffic::GetTopLevelIfHandle $emulation_handle]
                }
            }
            dhcpv4blockconfig {
                set hostBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -usesif-Targets]
            }
            IsisLspConfig {
                set networkBlockHandle [::sth::Traffic::GetFirstIpHeader $emulation_handle]
            }
            ipv4networkblock -
            ipv6networkblock
            {
                set networkBlockHandle $emulation_handle
                }
            isisroutehandle {
                # for ISIS we would get this handle.
                if {[info exists ::sth::IsIs::ISISROUTEHNDLIST($emulation_handle)]} {
                    set retList $::sth::IsIs::ISISROUTEHNDLIST($emulation_handle);
                    set isisIpVersion [lindex $retList 1]
                    switch -- $isisIpVersion {
                        4 {
                            set isisRouteConfig [lindex $retList 2]
                            set networkBlockHandle [::sth::sthCore::invoke ::stc::get $isisRouteConfig -children-Ipv4NetworkBlock]
                        }
                        6 {
                            set isisRouteConfig [lindex $retList 3]
                            set networkBlockHandle [::sth::sthCore::invoke ::stc::get $isisRouteConfig -children-Ipv6NetworkBlock]
                        }
                        4_6 {
                            set errMsg "Error in traffic_config: Unable to support IPv4 and IPv6 network block handles at this time."
                            ::sth::sthCore::log error $errMsg
                            set networkBlockHandle 0
                            return -code error $errMsg
                        }
                    }
                } else {
                    set errMsg "Error in traffic_config: ISIS route Handle should have Type INTERNAL or EXTERNAL."
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
            }
            ipv4routeparams {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv4networkblock} networkBlockHandle]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get Ipv4NetworkBlock from $emulation_handle"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
            }
            ipv6routeparams {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv6networkblock} NetworkBlockHandle]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get Ipv4NetworkBlock from $emulation_handle: $NetworkBlockHandle"
                    ::sth::sthCore::log error $errMsg
                    set NetworkBlockHandle 0
                    return -code error $errMsg
                }
            }
            routerlsa {
                set hndLsaLinkList [::sth::sthCore::invoke ::stc::get $emulation_handle -children-RouterLsaLink]
                set networkBlockHandle ""
                foreach hndLsaLink $hndLsaLinkList {
                    set linkType [::sth::sthCore::invoke ::stc::get $hndLsaLink -LinkType]
                    if {[regexp -nocase "stub_network" $linkType] } {
                        set networkBlockHandle [concat $networkBlockHandle [::sth::sthCore::invoke ::stc::get $hndLsaLink -children-Ipv4NetworkBlock]]
                    }
                }
            }
            summarylsablock -
            externallsablock -
            asbrsummarylsa {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]    
            }
            ospfv3interareaprefixlsablk -
            ospfv3intraareaprefixlsablk -
            ospfv3asexternallsablock -
            ospfv3nssalsablock -
            ospfv3linklsablk {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv6NetworkBlock]                
            }
            pimv4groupblk {
                if {[catch {::sth::sthCore::invoke ::stc::get  [::sth::sthCore::invoke ::stc::get $emulation_handle -JoinedGroup-targets] -children-ipv4NetworkBlock} Ipv4NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv4NetworkBlock) from $emulation_handle: $Ipv4NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv4NetworkBlock
            }
            pimv6groupblk {
                if {[catch {::sth::sthCore::invoke ::stc::get  [::sth::sthCore::invoke ::stc::get $emulation_handle -JoinedGroup-targets] -children-ipv6NetworkBlock} Ipv6NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv6NetworkBlock) from $emulation_handle: $Ipv6NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv6NetworkBlock
            }
            ripsessionhandle {
                set hostBlockHandle [::sth::Traffic::GetFirstIpHeader [set ::sth::rip::$emulation_handle]]
            }
            ripv4routeparams {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]
            }
            ripngrouteparams {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv6NetworkBlock]
            }
            ipv4group {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv4NetworkBlock} Ipv4NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv4NetworkBlock) from $emulation_handle: $Ipv4NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv4NetworkBlock            
            }
            ipv6group {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv6NetworkBlock} Ipv6NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv6NetworkBlock) from $emulation_handle: $Ipv6NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv6NetworkBlock
            }
            defaults {
                if {[string first "routerconfig" $emulationType] > 0} {
                    set hostBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -parent]
                } else {
                    set errMsg "INVALID EMULATION_HANDLE ($emulation_handle)"
                    ::sth::sthCore::log error $errMsg
                    return -code error $errMsg
                }
            }
        }
        
        #################### Bind Host Block or Network Block to StreamBlock #################
        if { $networkBlockHandle != 0 } {
            foreach networkBlock $networkBlockHandle {
                set startIPAddr [::sth::sthCore::invoke ::stc::get $networkBlock -StartIpList]
                ::sth::sthCore::invoke ::stc::config $networkBlock -StartIpList [::ip::normalize $startIPAddr]
            }
            set blockHandle $networkBlockHandle
            
        } elseif { [string first "ip" $hostBlockHandle] > -1 } {
            set blockHandle $hostBlockHandle
            set startIPAddr [::sth::sthCore::invoke ::stc::get $blockHandle -address]
            ::sth::sthCore::invoke ::stc::config $blockHandle -address [::ip::normalize $startIPAddr]
        } else {
            set blockHandle $hostBlockHandle
        }
        set blockHandleList [concat $blockHandleList $blockHandle]
    }
    array unset myTempHandleArray
    return $blockHandleList 
}
        
proc ::sth::Traffic::GetFirstIpHeader { parentHandle} {
    variable ::sth::Traffic::l3Protocol;
    set ipHeader 0
    
    #will have problem if there are gre delivery ipheader
    #set children [::stc::get $parentHandle -children]
    set children [::sth::sthCore::invoke stc::get $parentHandle -TopLevelIf-targets]
    set listLen [llength $children]
    if {[info exists ::sth::Traffic::l3Protocol]} {
        foreach child $children {
            if { [string first $::sth::Traffic::l3Protocol $child] == 0 } {
                set childAddr [::sth::sthCore::invoke ::stc::get $child -address]
                if {[regexp -nocase "fe80" $childAddr ]} {
                    continue
                } else {
                    set ipHeader $child
                }
            }
        }
    } else {
        for {set i $listLen} { $i >= 0 } { set i [expr {$i -1}] } {
            set child [lindex $children $i]
            if { [string first ipv4 $child] == 0 } {
                set ipHeader $child
                break;
            }
            #if { [string first ipv6 $child] == 0 } {
            #    set ipHeader $child
            #    break
            #}
            if { [string first ipv6 $child] == 0 } {
                set childAddr [::sth::sthCore::invoke ::stc::get $child -address]
                if {[regexp -nocase "fe80" $childAddr ]} {
                    continue
                } else {
                    set ipHeader $child
                    break
                }
                
            }
        }
        
        #Modified Davisons code to add fix for emulation_src_interface, need t0 check with DAvison
        #Sapna
        #for {set i 0} { $i <= $listLen } { incr i} {
        #    set child [lindex $children $i]
        #    if { [string first ipv4 $child] == 0 } {
        #        set ipHeader $child
        #        break;
        #    }
        #    if { [string first ipv6 $child] == 0 } {
        #        set childAddr [::stc::get $child -address]
        #        if {[regexp $childAddr "FE80"]} {
        #            break
        #        } else {
        #        set ipHeader $child
        #        }
        #        break
        #    }
        #}
    }
    return $ipHeader

}

proc ::sth::Traffic::TrimTailNumber { emulationHandle } {
    
    set len [string length $emulationHandle ]
    if { $len == 0 } {
        return $::sth::sthCore::FAILURE
    } else {
        set firstChar [string range $emulationHandle 0 0]
        if { [string is integer $firstChar] } {
            return $::sth::sthCore::FAILURE
        } else {
            set position $len
            set DONE false
            while { $position >= 0 && !$DONE } {
                set myChar [string range $emulationHandle $position $position]
                if { [string is integer $myChar] } {
                    set position [expr { $position - 1} ]
                } else {
                    return [string range $emulationHandle 0 $position]
                }
            }
            if { $position < 0 } {
                return $::sth::sthCore::FAILURE
            }
        }
    }
}

proc ::sth::Traffic::BindHostOrNetworkBlockToStreamBlock { streamBlkHandle blockHandle SrcOrDst useNativeSrcDstBinding} {
#puts "???::sth::Traffic::BindHostOrNetworkBlockToStreamBlock \{ streamBlkHandle blockHandle=$blockHandle SrcOrDst useNativeSrcDstBinding \}"
    if { $useNativeSrcDstBinding } {
        set streamBlkFirstIpHeader [::sth::Traffic::GetFirstIpHeader $streamBlkHandle]
        if { [string first ipv4 $blockHandle] ==  0  && [string first ipv4 $streamBlkFirstIpHeader] == 0} {
            if { [string first ipv4networkblock $blockHandle] == 0} {
                set ipv4Addr [::sth::sthCore::invoke ::stc::get $blockHandle -startiplist]
                set listLength [::sth::sthCore::invoke ::stc::get $blockHandle -networkcount]
            } else {
                set addrlist [::sth::sthCore::invoke stc::get $blockHandle -addrList]
                set listLength [llength $addrlist]
                if { $listLength > 0 } {
                    set ipv4Addr [lindex $addrlist 0]
                } else {
                    set ipv4Addr [::sth::sthCore::invoke stc::get $blockHandle -address]
                }
            }
            if { $SrcOrDst == "src" } {
                ::sth::sthCore::invoke ::stc::config $streamBlkFirstIpHeader -sourceAddr $ipv4Addr
            } else {
                ::sth::sthCore::invoke ::stc::config $streamBlkFirstIpHeader -destAddr $ipv4Addr
            }
        } elseif { [string first ipv6 $blockHandle] >= 0 && [string first ipv6 $streamBlkFirstIpHeader] > 0} {
            set addrlist [::sth::sthCore::invoke stc::get $blockHandle -addrList]
            if { [string first ipv6networkblock $blockHandle] == 0} {
                set ipv6Addr [::sth::sthCore::invoke ::stc::get $blockHandle -startiplist]
                set listLength [::sth::sthCore::invoke ::stc::get $blockHandle -networkcount]
            } else {
                set addrlist [::sth::sthCore::invoke stc::get $blockHandle -addrList]
                set listLength [llength $addrlist]
                if { $listLength > 0 } {
                    set ipv6Addr [lindex $addrlist 0]
                } else {
                    set ipv6Addr [::sth::sthCore::invoke stc::get $blockHandle -address]
                }
            }
            if { $SrcOrDst == "src" } {
                ::sth::sthCore::invoke ::stc::config $streamBlkFirstIpHeader -sourceAddr $ipv6Addr
            } else {
                ::sth::sthCore::invoke ::stc::config $streamBlkFirstIpHeader -destAddr $ipv6Addr
            }
        } else {
            set errMsg "ERROR in ::sth::Traffic::BindHostOrNetworkBlockToStreamBlock: Address type in emulation handle does not match the address type of the first IP address of stream block"
            ::sth::sthCore::log error $errMsg
            return -code error $errMsg
        }
        if { $listLength > 1 } {
            if { $SrcOrDst == "src" } {
                if {[catch {set ret [::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $blockHandle]} errMsg]} {
                    ::sth::sthCore::log error $errMsg
                    return -code 1 -errorcode $::sth::sthCore::FAILURE $errMsg
                }
            } else {
                if {[catch {set ret [::sth::sthCore::invoke ::stc::config $streamBlkHandle -DstBinding-targets $blockHandle]} errMsg]} {
                    ::sth::sthCore::log error $errMsg
                    return -code 1 -errorcode $::sth::sthCore::FAILURE $errMsg
                }
            }
        }
        return $::sth::sthCore::SUCCESS
    } else {
        if {[catch {set ret [::sth::Traffic::useNetworkBlockForIPv4Modifier $streamBlkHandle $blockHandle $SrcOrDst]} errMsg]} {
            ::sth::sthCore::log error $errMsg
            return -code 1 -errorcode $::sth::sthCore::FAILURE $errMsg
        }
        return $::sth::sthCore::SUCCESS
    }
}

#######################################################################################
# This function validates that the stream block has proper protocol headers as follows:
# EthII IPv4
# EthII IPv6
# EthII VLAN IPv4
# EthII VLAN IPv6
# EthII VLAN VLAN IPv4
# EthII VLAN VLAN IPv6
# When the function returns successfully, it returns the first IP header and its source
# and destination modifiers.
#######################################################################################

proc ::sth::Traffic::GetHeaderAndSrcDstModifiers { streamBlkHandle } {
    
    set returnKeyedList ""
    keylset returnKeyedList ipheader 0
    keylset returnKeyedList srcmodifier 0
    keylset returnKeyedList dstmodifier 0
    
    set rangeModifiers [::sth::sthCore::invoke ::stc::get $streamBlkHandle -children-rangeModifier]
    set tableModifiers [::sth::sthCore::invoke ::stc::get $streamBlkHandle -children-tableModifier]
    set protocolHeaders [::sth::sthCore::invoke ::stc::get $streamBlkHandle -children]
    set ipheader [::sth::Traffic::GetFirstIpHeader $streamBlkHandle]
    if { $ipheader != 0 } {
        keylset returnKeyedList ipheader $ipheader
        foreach modifier $rangeModifiers {
            set offsetReference [::sth::sthCore::invoke ::stc::get $modifier -offsetreference]
            set headerName [::sth::sthCore::invoke ::stc::get $ipheader -name]
            if { ![string compare -nocase "$headerName\.sourceAddr" $offsetReference] } {
                keylset returnKeyedList ipheader $ipheader
                keylset returnKeyedList srcmodifier $modifier
            } elseif { ![string compare -nocase "$headerName\.destAddr" $offsetReference] } {
                keylset returnKeyedList ipheader $ipheader
                keylset returnKeyedList dstmodifier $modifier
            }
        }
        foreach modifier $tableModifiers {
            set offsetReference [::sth::sthCore::invoke ::stc::get $modifier -offsetreference]
            set headerName [::sth::sthCore::invoke ::stc::get $ipheader -name]
            if { ![string compare -nocase "$headerName\.sourceAddr" $offsetReference] } {
                keylset returnKeyedList ipheader $ipheader
                keylset returnKeyedList srcmodifier $modifier
            } elseif { ![string compare -nocase "$headerName\.destAddr" $offsetReference] } {
                keylset returnKeyedList ipheader $ipheader
                keylset returnKeyedList dstmodifier $modifier
            }
        }
        return $returnKeyedList
    } else {
        ::sth::sthCore::processError returnKeyedList "Invalid Stream Block Structure: Missing IP Header ($streamBlkHandle)" {}
        return -code error $returnKeyedList
    }
}
############################################################################################################################
# Rules of binding
# 1) If hostblock (host, router) is bound to the source, both source and destination
#       must be specified and native stc binding is used.
# 2) If the source is a network block (including multicast group), the source is bound
#       using RangeModifier
#       In this case (source is a networkblock), the destination emulation handle is
#       not required.
# 3) If source emulation handle is not a host block, the destination is:
#       a) network block, use RangeModifier to bind the destination address
#       b) host block with startIp and increment,    use RangeModifier to bind the
#          destination address
#       b) host block with ip address list, use TabelModifier to bind the desintation address
#
# Rules of RangeModifier Binding
# 1) The frame is properly configured, at least one L2 header followed by a L3 Header
# 2) L2 header may or may not have a range or table modifier for each header
# 3) L3 header may or may not already have a range or table modifier for each header
# 4) Only the first L3 header and its modifier (if any) are used for the binding
#    It must not create a new L3 header because the stacking effect of protocol headers in
#    stream block
# 5) If the L3 header does not have a range modifier, create one, pointing it to the
#    L3 header which it intends to modify.
# 6) Configure the modifier with information from the ipv4/v4If or network block.
#
# Rules of RangeModifier Binding
# 1) The frame is properly configured, at least  one L2 header followed by a L3 Header
# 2) L2 header may or may not have a range or table modifier for each header
#
#############################################################################################
proc ::sth::Traffic::processSrcAndDstEmulationHandles { streamBlkHandle emulation_src_handle emulation_dst_handle useNativeBinding } {
    set _procName "processSrcAndDstEmulationHandles"
    upvar userArgsArray userArgsArray;
    variable ::sth::sthCore::UseModifier4TrafficBinding
    variable L3Protocol 0
    
    upvar mns mns;
    
    # Set port handle to port_address host as emulation_src_handle
    if { [string first port $emulation_src_handle] == 0 } {
        set retStatus [::sth::Traffic::processValidateObjectList port $emulation_src_handle];
        if {$retStatus == $::sth::sthCore::FAILURE} {
            set errMsg "validate object failed";
            return -code 1 -errorcode -1 $errMsg;
        }
        
        set port_addres_host {}
        foreach port $emulation_src_handle {
            set hosts [::sth::sthCore::invoke stc::get $port "-AffiliationPort-Sources"]
            foreach host $hosts {
                if {[string equal "port_address" [::sth::sthCore::invoke stc::get $host "-Name"]]} {
                    #set hostHandle $host
                    lappend port_addres_host $host
                    break
                }
            }
        }
        
        set emulation_src_handle $port_addres_host
    }
    # Set port handle to port_address host as emulation_dst_handle
    if { [string first port $emulation_dst_handle] == 0 } {
        set retStatus [::sth::Traffic::processValidateObjectList port $emulation_dst_handle];
        if {$retStatus == $::sth::sthCore::FAILURE} {
            set errMsg "validate object failed";
            return -code 1 -errorcode -1 $errMsg;
        }
        
        set port_addres_host {}
        foreach port $emulation_dst_handle {
            set hosts [::sth::sthCore::invoke stc::get $port "-AffiliationPort-Sources"]
            foreach host $hosts {
                if {[string equal "port_address" [::sth::sthCore::invoke stc::get $host "-Name"]]} {
                    #set hostHandle $host
                    lappend port_addres_host $host
                    break
                }
            }
        }
        
        set emulation_dst_handle $port_addres_host
    }
    
    if { $emulation_src_handle != 0 || $emulation_dst_handle != 0 } {
        #To be written
        #::sth::Traffic::ValidateStreamBlockStructure $streamBlkHandle
        if { !$::sth::sthCore::UseModifier4TrafficBinding } {
            if {[info exists userArgsArray(l3_protocol)]} {
                set L3Protocol $userArgsArray(l3_protocol)
            } else {
                set L3Protocol 0
            }
            
                        
            #############################################################
            # A) emulation_src_handle && !emulation_dst_handle
            #    1) bind the stream block to emulation_src_handle as source end
            #    3) searching the dst port hanlde by matching gateway (why), if find, go to step5
            #    4) select a port different with src port as the dst port
            #    5) create a new HOST under the dst port
            #    6) bind the stream block the host as the dst end
            #
            #   !emulation_src_handle && emulation_dst_handle
            #    2) create a new HOST under port_handle
            #    3) bind the stream block to ipv4if under the host as the source end
            #    4) bind the stream block to emulation_dst_handle as the dst end
            #
            #   emulation_src_handle && emulation_dst_handle
            #    1) bind the stream block to emulation_src_handle as the source end
            #    2) bind the stream block to emulation_dst_handle as the dst end
            #
            # B) the variable "flag" indicates whether to create a new host
            #
            # C) RangeModifier Binding
            #    ip_src_addr_xx, ip_dst_addr_xx, using RangeModifier
            #    vlan_id_count, vlan_outer_id_count, using
            #
            # D) If emulation_src_handle(host count > 1) and ip_src_addr_count/ipv6_src_addr_count are both specified,
            #    the addresses created by ip_src_addr_count will overwrite the addresses inherited from emulation_src_handle
            #    eg, -emulation_src_handle host4 \  -> (10 inherited addr: 2000::2 -> 2000::b)
            #        -ipv6_src_count 5 \            -> (RangeModifier: 2000::2 -> 2000::6)
            #        -ipv6_src_mode increment \  
            #    => the created src addresses for the bound stream will be (2000::2 -> 2000::6))
            #
            # comment by xiaozhi, may not accurate since not the origianl designer, only for reference
            #
            # on Dec, 7th, 2011
            ###############################################################
           
            
            #################################################
            #################################################
            ############ emulation_src_handle
            #################################################
            #################################################
            
            if { $emulation_src_handle != 0 } {
                # Used for RSVP when there is (likely to be) more than one object in the dst handle list.
                set dstCount 0
                if {$emulation_dst_handle != 0} {
                    set dstCount [llength $emulation_dst_handle]
                }
                
                #For L2 traffic
                if { [info exists userArgsArray(traffic_type)] && [string match -nocase "l2" $userArgsArray(traffic_type) ] } {
                     set srcBlockHandle [::sth::Traffic::GetLayerTwoHandle $emulation_src_handle ]
                } else {
                    set srcBlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_src_handle ]
                }
                
                
               
                set srcCount [llength $srcBlockHandle]

                # Check the Src and Dst counts - we need the same number of source/destination blocks
                # on both sides of the streamblock.  This means that if they are unequal, we must
                # repeat blocks on the other side.
                # For example:
                # emu_src_handle contains rsvptun1 rsvptun2 rsvptun3
                # emu_dst_handle contains rsvptun4 rsvptun5
                # In the stream block, the src and dst binding would be configured as
                # srcBinding-targets = rsvptun1 rsvptun2 rsvptun3
                # dstBinding-targets = rsvptun4 rsvptun5 rsvptun4
                if {$srcCount < $dstCount} {
                    # we must repeat blocks on the source side.
                    set repeatCount [expr {$dstCount / $srcCount}]
                    set remainCount [expr {$dstCount % $srcCount}]
                    set i 0
                    set newSrcBlockHandle ""
                    while {$i < $repeatCount} {
                        set newSrcBlockHandle [concat $newSrcBlockHandle $srcBlockHandle]
                        incr i
                    }
                    set newSrcBlockHandle [concat $newSrcBlockHandle [lrange $srcBlockHandle 0 [expr {$remainCount - 1}]]]
                    set srcBlockHandle $newSrcBlockHandle
                }
                if { [catch {::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $srcBlockHandle} errMsg ] } {
                    ::sth::sthCore::log error $errMsg
                    return -code error $errMsg
                } else {
                    ::sth::sthCore::log info "$_procName: Success. \
                            ::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $srcBlockHandle";
                    
                    #########################################################################
                    # specially handle PathDescriptor for RSVP if emulation_src_handle is provided
                    #########################################################################
                    set objPos 0
                    foreach object $emulation_src_handle {
                        if {([string match "rsvp*gresstunnelparams*" $object]) || ([string match "ipv4prefixlsp*" $object]) || ([regexp {host\d+$} $object]) || ([regexp {router\d+$} $object]) || ([string match "summarylsablock*" $object])} {
                            set ipv4NetBlock [::sth::sthCore::invoke stc::get $object -children-ipv4networkblock]
                             if {$ipv4NetBlock == ""} {
                                break
                            }
                            if {[string match "host*" $object] || [string match "router*" $object]} {
                                if {[regexp -nocase "greif" [stc::get $object -children]]} {
                                    set temp_gre_handle [::sth::sthCore::invoke stc::get $object -children-greif]
                                    set ipv4NetBlock [::sth::sthCore::invoke stc::get $temp_gre_handle -StackedOnEndpoint-targets]
                                } else {
                                    if {[regexp -nocase "ipv4" $L3Protocol]} {
                                        set ipv4NetBlock [::sth::sthCore::invoke stc::get $object -children-ipv4if]
                                    } else {
                                        set ipv4NetBlock [lindex [::sth::sthCore::invoke stc::get $object -children-ipv6if] 0]
                                    }

                                }
                            }
                            set pdList [::sth::sthCore::invoke stc::get $streamBlkHandle -children-pathdescriptor]
                            set pathDescriptor ""
                            foreach pathDesc $pdList {
                                set srcBind [::sth::sthCore::invoke stc::get $pathDesc -srcbinding-targets]
                                set dstBind [::sth::sthCore::invoke stc::get $pathDesc -dstbinding-targets]
                                if {[string match -nocase $srcBind $ipv4NetBlock] || \
                                        [string match -nocase $dstBind $ipv4NetBlock]} {
                                    set pathDescriptor $pathDesc
                                    break
                                }
                            }
                            
                            # Determine whether we need to create a new path descriptor for this network block
                            # or if we just need to configure its endpoints.
                            if {$pathDescriptor == ""} {
                                set pathDescriptor [::sth::sthCore::invoke stc::create "PathDescriptor" -under $streamBlkHandle -Index $objPos]
                            }
                            
                            if {([string match "rsvp*gresstunnelparams*" $object])} {
                                set mplsif [::sth::sthCore::invoke stc::get $object -resolvesinterface-Targets]
                            } elseif {[string match "ipv4prefixlsp*" $object]} {
                                set ldpRtrConfHndl [::sth::sthCore::invoke stc::get $object -parent]
                                set rtrhndl [::sth::sthCore::invoke stc::get $ldpRtrConfHndl -parent]
                                set mplsif [::sth::sthCore::invoke stc::get $rtrhndl -children-mplsif]
                            } elseif {([string match "host*" $object])  || ([string match "router*" $object]) || ([string match "summarylsablock*" $object])} {                          
                                set mplsif ""
                                set tunnel_label_list "tunnel_bottom_label tunnel_next_label tunnel_top_label"
                                foreach tunnel_label $tunnel_label_list {
                                    if {[info exists userArgsArray($tunnel_label)]} {
                                        set tunnel_router $userArgsArray($tunnel_label);
                                        if {$tunnel_router == ""} {
                                            break;
                                        }
                                        if {[catch {append mplsif [lindex [::sth::sthCore::invoke stc::get $tunnel_router -children-mplsif] 0] " "} errMsg]} {
                                            ::sth::sthCore::log error $errMsg
                                            return -code error $errMsg
                                        }
                                    } else {
                                        break;    
                                    }
                                }
                            }
                            
                            ::sth::sthCore::invoke stc::config $pathDescriptor -Encapsulation-targets $mplsif -srcbinding-targets $ipv4NetBlock

                            # Try to configure the opposite side of the path descriptor if possible
                            if {$emulation_dst_handle != 0} {
                                set dstEmuListPos $objPos
                                if {$srcCount > $dstCount} {
                                    set dstEmuListPos [expr {($objPos % [llength $emulation_dst_handle])}]
                                }
                                set dstTargetHandle [lindex $emulation_dst_handle $dstEmuListPos]
                                if {$dstTargetHandle != ""} {
                                    set dst_ipv4NetBlock [::sth::sthCore::invoke stc::get $dstTargetHandle -children-ipv4networkblock]
                                    if {[string match "host*" $dstTargetHandle] || [string match "router*" $dstTargetHandle]} {
                                        if {[regexp -nocase "greif" [stc::get $dstTargetHandle -children]]} {
                                            set temp_gre_handle [::sth::sthCore::invoke stc::get $dstTargetHandle -children-greif]
                                            set dst_ipv4NetBlock [::sth::sthCore::invoke stc::get $temp_gre_handle -StackedOnEndpoint-targets]
                                        } else {
                                            #set dst_ipv4NetBlock [::sth::sthCore::invoke stc::get $dstTargetHandle -children-ipv4if]
                                            if {[regexp -nocase "ipv4" $L3Protocol]} {
                                                set dst_ipv4NetBlock [::sth::sthCore::invoke stc::get $dstTargetHandle -children-ipv4if]
                                            } else {
                                                set dst_ipv4NetBlock [lindex [::sth::sthCore::invoke stc::get $dstTargetHandle -children-ipv6if] 0]
                                            }
                                        }
                                    }
                                    ::sth::sthCore::invoke stc::config $pathDescriptor -dstbinding-targets $dst_ipv4NetBlock
                                }
                            } else {
                                ::sth::sthCore::invoke stc::config $pathDescriptor -dstbinding-targets $ipv4NetBlock
                            }
                        }
                        incr objPos
                    }
                }
            } else {
                # the user has not entered the emulation_src_handle
                # First, try to use the port_address host created by interface_config as the binding host
                # If the address doesn't match, we need to create a host and src bind the stream block to ipv4if under that host
                
                ###########################################################################
                ## user has not entered the emulation_src_handle, searching a correct host
                ###########################################################################
                #set flag 1
                #set bindHost ""
                #if { ![string compare -nocase $L3Protocol "ipv4"] } {
                #    if {[info exists userArgsArray(ip_src_addr)]} {
                #        set matchAddr $userArgsArray(ip_src_addr);
                #        set hosts [stc::get project1 -children-host]
                #        foreach host $hosts {
                #           set ipifs [stc::get $host -children-ipv4if]
                #           if {$ipifs != ""} {
                #                foreach ipif $ipifs {
                #                    set addr [stc::get $ipif -address]
                #                    if {$addr == $matchAddr} {
                #                       ::stc::config $streamBlkHandle -SrcBinding-targets $ipif
                #                        set bindHost $host
                #                        set ipBlk $ipif
                #                        set flag 0
                #                    }
                #                }
                #            }
                #        }
                #    }
                #} elseif {! [string compare -nocase $L3Protocol "ipv6"] } {
                #    if {[info exists userArgsArray(ipv6_src_addr)]} {
                #        set matchAddr [ip::normalize $userArgsArray(ipv6_src_addr)];
                #        set hosts [stc::get project1 -children-host]
                #        foreach host $hosts {
                #            set ipifs [stc::get $host -children-ipv6if]
                #            if {$ipifs != ""} {
                #                foreach ipif $ipifs {
                #                    set addr [stc::get $ipif -address]
                #                    set addr [ip::normalize $addr]
                #                    if {$addr == $matchAddr} {
                #                        ::stc::config $streamBlkHandle -SrcBinding-targets $ipif
                #                        set bindHost $host
                #                        set ipBlk  $ipif
                #                        set flag 0
                #                    }
                #                }
                #            }
                #        }
                #    }
                #}
                
                #################################################################
                # No correct host found, create New host for emulation_src_handle
                #################################################################
                set flag 1
                if {$flag} {
                    if { ![string compare -nocase $L3Protocol "ipv4"] } {
                        if {[info exists userArgsArray(ip_src_addr)]} {
                            set Address $userArgsArray(ip_src_addr);
                        } else {
                            set Address 1.1.1.1
                        }
                        if {[info exists userArgsArray(ip_src_count)]} {
                            set AddrRepeatCount $userArgsArray(ip_src_count);
                        } else {
                            set AddrRepeatCount 1
                        }
                        if {[info exists userArgsArray(ip_src_step)]} {
                            set AddrStep $userArgsArray(ip_src_step);
                        } else {
                            set AddrStep 0.0.0.1
                        }
                        if {[info exists userArgsArray(mac_discovery_gw)]} {
                            set Gateway $userArgsArray(mac_discovery_gw);
                        } else {
                            set Gateway [::sth::sthCore::getIpv4Gw $Address]
                        }
                    } elseif { ![string compare -nocase $L3Protocol "ipv6" ]} {
                        if {[info exists userArgsArray(ipv6_src_addr)]} {
                            set Address [ip::normalize $userArgsArray(ipv6_src_addr)];
                        } else {
                            set Address [ip::normalize 2000::2]
                        }
                        if {[info exists userArgsArray(ipv6_src_count)]} {
                            set AddrRepeatCount $userArgsArray(ipv6_src_count);
                        } else {
                            set AddrRepeatCount 1
                        }
                        if {[info exists userArgsArray(ipv6_src_step)]} {
                            set AddrStep [ip::normalize $userArgsArray(ipv6_src_step)];
                        } else {
                            set AddrStep [ip::normalize 0000::1]
                        }
                        if {[info exists userArgsArray(mac_discovery_gw)]} {
                            set Gateway [ip::normalize $userArgsArray(mac_discovery_gw)];
                        } else {
                            set Gateway "::0"
                            #set protHandle $userArgsArray(port_handle);
                            #set ipifHandle [::stc::get $protHandle -children-Ipv6If]
                            #set addr [::stc::get $ipifHandle -Gateway]
                            #set Gateway [ip::normalize $addr]
                        }
                    }
    
                    # as of now putting here for quick test. Will find a better way later to incorporate this.
                    if {[info exists userArgsArray(mac_src)]} {
                        set SourceMac $userArgsArray(mac_src);
                    } else {
                        set SourceMac 00.01.01.01.01.01
                    }
                    if {[info exists userArgsArray(mac_src_step)]} {
                        set srcMacStep $userArgsArray(mac_src_step);
                    } else {
                        set srcMacStep 00.00.00.00.00.01
                    }
                    if {[info exists userArgsArray(mac_src_count)]} {
                        set SrcMacRepeatCount $userArgsArray(mac_src_count);
                    } else {
                        set SrcMacRepeatCount 0
                    }
                    set hndSrchost [::sth::sthCore::invoke ::stc::create Host -under project1 -DeviceCount $AddrRepeatCount]
                    if {[catch {::sth::sthCore::invoke stc::config $hndSrchost -AffiliationPort-Targets $userArgsArray(port_handle)} errMsg]} {
                        ::sth::sthCore::log debug "FAILED while setting the AffiliationPort-Targets to $userArgsArray(port_handle). Msg: $errMsg";
                        ::sth::sthCore::processError trafficKeyedList $errMsg;
                        return -code 1 -errorcode -1 $errMsg
                    }
                    set lowerif [::sth::sthCore::invoke ::stc::create ethiiif -under $hndSrchost \
                                      -SourceMac $SourceMac \
                                      -SrcMacStep $srcMacStep \
                                      -SrcMacRepeatCount $SrcMacRepeatCount\
                                      -SrcMacStepMask "00:00:ff:ff:ff:ff"]
                    
                     if {[info exists userArgsArray(vlan_id_outer)]} {
                        set vlanid $userArgsArray(vlan_id_outer)
                        if {[info exists userArgsArray(vlan_id_outer_step)]} {
                            set vlanstep $userArgsArray(vlan_id_outer_step);
                        } else {
                            set vlanstep  0
                        }
                        if {[info exists userArgsArray(vlan_outer_user_priority)]} {
                            set pri $userArgsArray(vlan_outer_user_priority);
                        } else {
                            set pri  0
                        }
                        if {[info exists userArgsArray(vlan_id_outer_count)]} {
                            set outerCount $userArgsArray(vlan_id_outer_count);
                        } else {
                            set outerCount 1
                        }
                        if {[info exists userArgsArray(vlan_id_count)]} {
                            set count $userArgsArray(vlan_id_count);
                        } else {
                            set count 1
                        }
                        set outerRepeat 0
                        set repeat 0
                        switch -exact -- $userArgsArray(qinq_incr_mode) {
                            "both" {
                                #set outerRepeat [expr {$AddrRepeatCount/$outerCount} - 1]
                                #set repeat [expr {$AddrRepeatCount/$count} - 1]
                                if {[info exists userArgsArray(vlan_id_outer_repeat)]} {
                                    set outerRepeat $userArgsArray(vlan_id_outer_repeat)
                                } 
                                if {[info exists userArgsArray(vlan_id_repeat)]} {
                                    set repeat $userArgsArray(vlan_id_repeat)
                                } 
                            }
                            "inner" {
                                set outerRepeat [expr $count - 1]
                                if {[info exists userArgsArray(vlan_id_repeat)]} {
                                    set repeat $userArgsArray(vlan_id_repeat)
                                } 
                            }
                            "outer" {
                                if {[info exists userArgsArray(vlan_id_outer_repeat)]} {
                                    set outerRepeat $userArgsArray(vlan_id_outer_repeat)
                                } 
                                set repeat [expr $outerCount - 1]
                            }
                        }

                        set vlanif [::sth::sthCore::invoke ::stc::create vlanif -under $hndSrchost \
                                      -vlanid $vlanid \
                                      -Priority $pri \
                                      -idstep $vlanstep \
                                      -IdRepeatCount $outerRepeat \
                                      -IfRecycleCount $outerCount]
                          set configStatus [::sth::sthCore::invoke ::stc::config $vlanif -StackedOnEndpoint-targets $lowerif]
                          set lowerif $vlanif
                    }
                    if {[info exists userArgsArray(vlan_id)]} {
                        set vlanid $userArgsArray(vlan_id)
                        if {[info exists userArgsArray(vlan_id_step)]} {
                            set vlanstep $userArgsArray(vlan_id_step);
                        } else {
                            set vlanstep  0
                        }
                        if {[info exists userArgsArray(vlan_user_priority)]} {
                            set pri $userArgsArray(vlan_user_priority);
                        } else {
                            set pri  0
                        }
                        if {[info exists userArgsArray(vlan_id_count)]} {
                            set count $userArgsArray(vlan_id_count);
                        } else {
                            set count 1
                        }
                        if {![info exists repeat]} {
                            if {[info exists userArgsArray(vlan_id_repeat)]} {
                                set repeat $userArgsArray(vlan_id_repeat);
                            } else {
                                set repeat 0
                            }
                        } 
                        set vlanif [::sth::sthCore::invoke ::stc::create vlanif -under $hndSrchost \
                                      -vlanid $vlanid \
                                      -Priority $pri \
                                      -idstep $vlanstep \
                                      -IdRepeatCount $repeat \
                                      -IfRecycleCount $count]
                        set configStatus [::sth::sthCore::invoke ::stc::config $vlanif -StackedOnEndpoint-targets $lowerif]
                        set lowerif $vlanif
                    }
                    set ipBlk ""
                    if {![string compare -nocase $L3Protocol "ipv4" ] } {
                        set hndIpv4if [::sth::sthCore::invoke ::stc::create ipv4if -under $hndSrchost\
                                           -Address $Address -AddrStep $AddrStep\
                                           -AddrRepeatCount 0 \
                                           -Gateway $Gateway]
                        #-AddrRepeatCount $AddrRepeatCount
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndSrchost -TopLevelIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndSrchost -PrimaryIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndIpv4if -StackedOnEndpoint-targets $lowerif]
                        set configStatus [::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $hndIpv4if]
                        set ipBlk $hndIpv4if
                    } elseif {![string compare -nocase $L3Protocol "ipv6" ] } {
                        # Fix for the lower layer returning an interface stack
                        # validation error. The name of this variable should
                        # probably be changed. This repeat count on the 
                        # v4/v6 object should typically be set to 0.
                        set hndIpv6if [::sth::sthCore::invoke ::stc::create ipv6if -under $hndSrchost\
                                           -Address $Address\
                                           -AddrRepeatCount 0 \
                                           -AddrStep $AddrStep\
                                           -Gateway $Gateway]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndSrchost -TopLevelIf-targets $hndIpv6if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndSrchost -PrimaryIf-targets $hndIpv6if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndIpv6if -StackedOnEndpoint-targets $lowerif]
                        set configStatus [::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $hndIpv6if]
                        set ipBlk $hndIpv6if                     
                    } else {
                        set hndIpv4if [::sth::sthCore::invoke ::stc::create ipv4if -under $hndSrchost ]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndSrchost -TopLevelIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndSrchost -PrimaryIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndIpv4if -StackedOnEndpoint-targets $lowerif]
                        set configStatus [::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $hndIpv4if]
                        set ipBlk $hndIpv4if
                    }
                }
                ######################################################################
                # specially handle PathDescriptor for RSVP if No emulation_src_handle
                ######################################################################
                
                # Check for RSVP and configure the path descriptor if necessary
                # Given that we are in this proc, there MUST be an emulation_dst_handle but we'll check
                # just to make sure.
                if {$emulation_dst_handle != 0} {
                    set objPos 0
                    # Source binding is a single host block's ipvX interface right now...
                    # if there are multiple objects in the dstHandle list, we should repeat
                    # the ipvX interface block in the srcbinding list so that the pairwise block
                    # mapping will not error out (ie the number of blocks on the src and dst side
                    # should be the same)
                    set srcBind [::sth::sthCore::invoke stc::get $streamBlkHandle -SrcBinding-targets]
                    set srcBindList ""
                    foreach dstHandle $emulation_dst_handle {
                        lappend srcBindList $srcBind
# NOTE: It has been determined that we don't need path descriptors when sending traffic
#       to RSVP routers.
#                         if {[string match "rsvp*gresstunnelparams*" $dstHandle]} {
#                             set ipv4NetBlock [stc::get $dstHandle -children-ipv4networkblock]
#                             set pdList [stc::get $streamBlkHandle -children-pathdescriptor]
#                             set pathDescriptor ""
#                             foreach pathDesc $pdList {
#                                 set srcBind [stc::get $pathDesc -srcbinding-targets]
#                                 set dstBind [stc::get $pathDesc -dstbinding-targets]
#                                 if {[string match -nocase $srcBind $ipv4NetBlock] || \
#                                         [string match -nocase $dstBind $ipv4NetBlock]} {
#                                     set pathDescriptor $pathDesc
#                                     break
#                                 }
#                             }
#                             # Determine whether we need to create a new path descriptor for this network block
#                             # or if we just need to configure its endpoints.
#                             if {$pathDescriptor == ""} {
#                                 set pathDescriptor [stc::create "PathDescriptor" -under $streamBlkHandle -Index $objPos]
#                             }
#                             stc::config $pathDescriptor -srcbinding-targets $ipBlk \
#                                 -dstbinding-targets $ipv4NetBlock
#                         }
                    }
                    ::sth::sthCore::invoke stc::config $streamBlkHandle -SrcBinding-targets $srcBindList
                }
            }
            
            
            #################################################
            #################################################
            #########  emulation_dst_handle
            #################################################
            #################################################
            
            if { $emulation_dst_handle != 0 } {
                # Used for RSVP when there is (likely to be) more than one object in the src handle list.
                set srcCount 0
                if {$emulation_src_handle != 0} {
                    set srcCount [llength $emulation_src_handle]
                }
                
                if { [info exists userArgsArray(traffic_type)] && [string match -nocase "l2" $userArgsArray(traffic_type) ] } {
                    set dstBlockHandle [::sth::Traffic::GetLayerTwoHandle $emulation_dst_handle ]
                } else {
                    set dstBlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_dst_handle ]
                }
              
                set dstCount [llength $dstBlockHandle]

                # Check the Src and Dst counts - we need the same number of source/destination blocks
                # on both sides of the streamblock.  This means that if they are unequal, we must
                # repeat blocks on the other side.
                # For example:
                # emu_src_handle contains rsvptun1 rsvptun2 rsvptun3
                # emu_dst_handle contains rsvptun4 rsvptun5
                # In the stream block, the src and dst binding would be configured as
                # srcBinding-targets = rsvptun1 rsvptun2 rsvptun3
                # dstBinding-targets = rsvptun4 rsvptun5 rsvptun4
                if {$srcCount > $dstCount} {
                    # we must repeat blocks on the destination side.
                    set repeatCount [expr {$srcCount / $dstCount}]
                    set remainCount [expr {$srcCount % $dstCount}]
                    set i 0
                    set newDstBlockHandle ""
                    while {$i < $repeatCount} {
                        set newDstBlockHandle [concat $newDstBlockHandle $dstBlockHandle]
                        incr i
                    }
                    set newDstBlockHandle [concat $newDstBlockHandle [lrange $dstBlockHandle 0 [expr {$remainCount - 1}]]]
                    set dstBlockHandle $newDstBlockHandle
                }
                if { [catch {::sth::sthCore::invoke ::stc::config $streamBlkHandle -DstBinding-targets $dstBlockHandle} errMsg ] } {
                    ::sth::sthCore::log error $errMsg
                    return -code error $errMsg
                } else {
                    ::sth::sthCore::log info "$_procName: Success. \
                            ::sth::sthCore::invoke ::stc::config $streamBlkHandle -DstBinding-targets $dstBlockHandle";
                    
                    #########################################################################
                    # specially handle PathDescriptor for RSVP if emulation_dst_handle is provided
                    #########################################################################
                    set objPos 0
                    foreach object $emulation_dst_handle {
                        if {([string match "rsvp*gresstunnelparams*" $object]) || ([string match "summarylsablock*" $object])|| ([regexp {host\d+$} $object]) || ([regexp {router\d+$} $object])} {
                            # This block of code will set up PathDescriptors for MPLS - and is only
                            # necessary if the source needs the -encapsulation-targets (an MPLS interface).
                            # Check the source side (if one exists) to see if it is also running rsvp.
                            if {$srcCount > 0} {
                                set srcEmuListPos $objPos
                                if {$dstCount > $srcCount} {
                                    set srcEmuListPos [expr {($objPos % [llength $emulation_src_handle])}]
                                }
                                set srcTargetHandle [lindex $emulation_src_handle $srcEmuListPos]
                                if {([string match "rsvp*gresstunnelparams*" $srcTargetHandle]) || ([string match "ipv4prefixlsp*" $srcTargetHandle]) || ([string match "host*" $srcTargetHandle]) || ([string match "router*" $srcTargetHandle]) || ([string match "summarylsablock*" $srcTargetHandle])} {
                                    set ipv4NetBlock [::sth::sthCore::invoke stc::get $object -children-ipv4networkblock]
                                    if {[string match "host*" $object] || ([string match "router*" $object])} {
                                        if {[regexp -nocase "greif" [stc::get $object -children]]} {
                                            set temp_gre_handle [::sth::sthCore::invoke stc::get $object -children-greif]
                                            set ipv4NetBlock [::sth::sthCore::invoke stc::get $temp_gre_handle -StackedOnEndpoint-targets]
                                        } else {
                                            
                                            if {[regexp -nocase "ipv4" $L3Protocol]} {
                                                set ipv4NetBlock [::sth::sthCore::invoke stc::get $object -children-ipv4if]
                                            } else {
                                                set ipv4NetBlock [lindex [::sth::sthCore::invoke stc::get $object -children-ipv6if] 0]
                                            }
                                        }
                                    }
                                    if {$ipv4NetBlock == ""} {
                                        break
                                    }
                                    set pdList [::sth::sthCore::invoke stc::get $streamBlkHandle -children-pathdescriptor]
                                    set pathDescriptor ""
                                    # Determine whether we need to create a new path descriptor for this network block
                                    # or if we just need to configure its endpoints.
                                    foreach pathDesc $pdList {
                                        set srcBind [::sth::sthCore::invoke stc::get $pathDesc -srcbinding-targets]
                                        set dstBind [::sth::sthCore::invoke stc::get $pathDesc -dstbinding-targets]
                                        if {[string match -nocase $srcBind $ipv4NetBlock] || \
                                                [string match -nocase $dstBind $ipv4NetBlock]} {
                                            set pathDescriptor $pathDesc
                                            break
                                        }
                                    }
                                    if {$pathDescriptor == ""} {
                                        set pathDescriptor [::sth::sthCore::invoke stc::create "PathDescriptor" \
                                                                -under $streamBlkHandle \
                                                                -Index $objPos]
                                    }
                                    set src_ipv4NetBlock [::sth::sthCore::invoke stc::get $srcTargetHandle -children-ipv4networkblock]
                                    if {([string match "rsvp*gresstunnelparams*" $srcTargetHandle])} {
                                        set mplsif [::sth::sthCore::invoke stc::get $srcTargetHandle -resolvesinterface-Targets]
                                    } elseif {[string match "ipv4prefixlsp*" $srcTargetHandle]} {
                                        set ldpRtrConfHndl [::sth::sthCore::invoke stc::get $srcTargetHandle -parent]
                                        set rtrhndl [::sth::sthCore::invoke stc::get $ldpRtrConfHndl -parent]
                                        set mplsif [::sth::sthCore::invoke stc::get $rtrhndl -children-mplsif]
                                    } elseif {([string match "host*" $srcTargetHandle]) || ([string match "router*" $srcTargetHandle]) || ([string match "summarylsablock*" $srcTargetHandle])} {
                                        set mplsif ""
                                        set tunnel_label_list "tunnel_bottom_label tunnel_next_label tunnel_top_label"
                                        foreach tunnel_label $tunnel_label_list {
                                            if {[info exists userArgsArray($tunnel_label)]} {
                                                set tunnel_router $userArgsArray($tunnel_label);
                                                if {$tunnel_router == ""} {
                                                    break;
                                                }
                                                if {[catch {append mplsif [lindex [::sth::sthCore::invoke stc::get $tunnel_router -children-mplsif] 0] " "} errMsg]} {
                                                     ::sth::sthCore::log error $errMsg
                                                    return -code error $errMsg
                                                }
                                            } else {
                                                break;    
                                            }
                                        }
                                        if {[string match "host*" $srcTargetHandle] || [string match "router*" $srcTargetHandle]} {
                                            ##zzkkyy 2014-07-22 for GRE traffic
                                            if {[regexp -nocase "greif" [stc::get $srcTargetHandle -children]]} {
                                                set temp_gre_handle [::sth::sthCore::invoke stc::get $srcTargetHandle -children-greif]
                                                set src_ipv4NetBlock [::sth::sthCore::invoke stc::get $temp_gre_handle -StackedOnEndpoint-targets]
                                            } else {
                                                
                                                if {[regexp -nocase "ipv4" $L3Protocol]} {
                                                    set src_ipv4NetBlock [::sth::sthCore::invoke stc::get $srcTargetHandle -children-ipv4if]
                                                } else {
                                                    set src_ipv4NetBlock [lindex [::sth::sthCore::invoke stc::get $srcTargetHandle -children-ipv6if] 0]
                                                }
                                            }
                                        }
                                    }
                                    if {$mplsif == ""} {
                                        #here check if mpls if is empty, will check if there is the vxlanif, if there is, then will configure
                                        #the encapsulation of the pathDescriptor to be the vlanif of the vtep which is linked to this vm.
                                        set vteplink [::sth::sthCore::invoke stc::get $srcTargetHandle -children-vxlanvmtovteplink]
                                        if {$vteplink != ""} {
                                            set mplsif [::sth::sthCore::invoke stc::get $vteplink -linkdst-Targets]
                                        }
                                    }
                                    ::sth::sthCore::invoke stc::config $pathDescriptor -encapsulation-targets $mplsif \
                                        -dstbinding-targets $ipv4NetBlock \
                                        -srcbinding-targets $src_ipv4NetBlock
                                }
                            }
                        }
                        incr objPos
                    }
                }
            } else {
                # the user has not entered the emulation_dst_handle
                # First, try to use the port_address host created by interface_config as the binding host
                # If the address doesn't match, we need to create a host and dst bind the stream block to ipv4if under that host
            
                ###########################################################################
                ## user has not entered the emulation_dst_handle, searching a correct host
                ###########################################################################
                #set flag 1
                #if { ![string compare -nocase $L3Protocol "ipv4"] } {
                #    if {[info exists userArgsArray(ip_dst_addr)]} {
                #        set matchAddr $userArgsArray(ip_dst_addr);
                #        set hosts [stc::get project1 -children-host]
                #        foreach host $hosts {
                #           set ipifs [stc::get $host -children-ipv4if]
                #           if {$ipifs != ""} {
                #              foreach ipif $ipifs {
                #                set addr [stc::get $ipif -address]
                #                if {$addr == $matchAddr} {
                #                   ::stc::config $streamBlkHandle -DstBinding-targets $ipif
                #                   set ipBlk $ipif
                #                   set flag 0
                #                }
                #              }
                #           }
                #        }
                #    }
                #} elseif { ![string compare -nocase $L3Protocol "ipv6"] } {
                #    if {[info exists userArgsArray(ipv6_dst_addr)]} {
                #        set matchAddr [ip::normalize $userArgsArray(ipv6_dst_addr)];
                #        set hosts [stc::get project1 -children-host]
                #        foreach host $hosts {
                #           set ipifs [stc::get $host -children-ipv6if]
                #           if {$ipifs != ""} {
                #                foreach ipif $ipifs {
                #                   set addr [stc::get $ipif -address]
                #                   set addr [ip::normalize $addr]
                #                   if {$addr == $matchAddr} {
                #                      ::stc::config $streamBlkHandle -DstBinding-targets $ipif
                #                       set ipBlk $ipif
                #                       set flag 0
                #                    }
                #                }
                #            }
                #        }
                #    }
                #}
                
                #################################################################
                # No correct host found, create New host for emulation_dst_handle
                #################################################################
                set flag 1
                if {$flag} {
                    if {$L3Protocol != 0 } {
                        if { ![string compare -nocase ipv4 $L3Protocol] } {  
                            if {[info exists userArgsArray(ip_dst_addr)]} {
                                set Address $userArgsArray(ip_dst_addr);
                            } else {
                                set Address 1.1.1.1
                            }
                            if {[info exists userArgsArray(ip_dst_count)]} {
                                set AddrRepeatCount $userArgsArray(ip_dst_count);
                            } else {
                                set AddrRepeatCount 1
                            }
                            if {[info exists userArgsArray(ip_dst_step)]} {
                                set AddrStep [ip::normalize $userArgsArray(ip_dst_step)];
                            } else {
                                set AddrStep 0.0.0.1
                            }
                            if {[info exists userArgsArray(mac_discovery_gw)]} {
                                set Gateway $userArgsArray(mac_discovery_gw);
                            } else {
                                set Gateway [::sth::sthCore::getIpv4Gw $Address]
                            }
                        } elseif { ![string compare -nocase ipv6 $L3Protocol]} {
                            if {[info exists userArgsArray(ipv6_dst_addr)]} {
                                set Address [ip::normalize $userArgsArray(ipv6_dst_addr)];
                            } else {
                                set Address [ip::normalize 2000::1]
                            }
                            if {[info exists userArgsArray(ipv6_dst_count)]} {
                                set AddrRepeatCount $userArgsArray(ipv6_dst_count);
                            } else {
                                set AddrRepeatCount 1
                            }
                            if {[info exists userArgsArray(ipv6_dst_step)]} {
                                set AddrStep [ip::normalize $userArgsArray(ipv6_dst_step)];
                            } else {
                                set AddrStep [ip::normalize 0000::1]
                            }
                            if {[info exists userArgsArray(mac_discovery_gw)]} {
                                set Gateway [ip::normalize $userArgsArray(mac_discovery_gw)];
                            } else {
                                set Gateway "::0"
                                #set protHandle $userArgsArray(port_handle);
                                #set ipifHandle [::stc::get $protHandle -children-Ipv6If]
                                #foreach ipif $ipifHandle {
                                #    set ipaddr [::stc::get $ipif -Address]
                                #    if {![regexp "fe80" $ipaddr]} {
                                #        set addr [::stc::get $ipif -Gateway]
                                #        set Gateway [ip::normalize $addr]
                                #    }
                                #}
                            }
                        }
                    }
                    # as of now putting here for quick test. Will find a better way later to incorporate this.
                    if {[info exists userArgsArray(mac_dst)]} {
                        set SourceMac $userArgsArray(mac_dst);
                    } else {
                        set SourceMac 00:10:94:00:00:02
                    }
                    if {[info exists userArgsArray(mac_dst_step)]} {
                        set srcMacStep $userArgsArray(mac_dst_step);
                    } else {
                        set srcMacStep 00.00.00.00.00.01
                    }
                    if {[info exists userArgsArray(mac_dst_count)]} {
                        set SrcMacRepeatCount $userArgsArray(mac_dst_count);
                    } else {
                        set SrcMacRepeatCount 0
                    }
                     
                    #by xiaozhi, do not understand why searching port by matching gateway??
                    
                   #stc3.0 do not allow hosts not affiliate to a port. Need to get the port hanlde here
                    set hostList [::sth::sthCore::invoke stc::get project1 -children-host]
                    foreach host $hostList {
                        set hostIfs [::sth::sthCore::invoke stc::get $host -PrimaryIf-targets]
                        foreach hostIf $hostIfs {
                            set hostGw [::sth::sthCore::invoke stc::get $hostIf -Gateway]
                            set hostGw [ip::normalize $hostGw]
                            if {$Gateway == $hostGw} {
                                set portHnd [::sth::sthCore::invoke stc::get $host -AffiliationPort-targets]
                                break
                            }
                        }
                    }
                    #in case didn't find any port
                    if {! [info exists portHnd]} {
                        set ports [::sth::sthCore::invoke stc::get project1 -children-port]
                        foreach port $ports {
                           if {$port != $userArgsArray(port_handle)} {
                               set portHnd $port
                               break
                           }
                        }
                    }
                    set hndDsthost [::sth::sthCore::invoke ::stc::create Host -under project1 -DeviceCount $AddrRepeatCount -AffiliationPort-targets $portHnd]
                    set lowerif [::sth::sthCore::invoke ::stc::create ethiiif -under $hndDsthost \
                                      -SourceMac $SourceMac \
                                      -SrcMacStep $srcMacStep \
                                      -SrcMacRepeatCount $SrcMacRepeatCount\
                                      -SrcMacStepMask "00:00:ff:ff:ff:ff"];
                     if {[info exists userArgsArray(vlan_id_outer)]} {
                        set vlanid $userArgsArray(vlan_id_outer)
                        if {[info exists userArgsArray(vlan_id_outer_step)]} {
                            set vlanstep $userArgsArray(vlan_id_outer_step);
                        } else {
                            set vlanstep  0
                        }
                        if {[info exists userArgsArray(vlan_outer_user_priority)]} {
                            set pri $userArgsArray(vlan_outer_user_priority);
                        } else {
                            set pri  0
                        }
                        if {[info exists userArgsArray(vlan_id_outer_count)]} {
                            set outerCount $userArgsArray(vlan_id_outer_count);
                        } else {
                            set outerCount 1
                        }
                        if {[info exists userArgsArray(vlan_id_count)]} {
                            set count $userArgsArray(vlan_id_count);
                        } else {
                            set count 1
                        }
                        set outerRepeat 0
                        set repeat 0
                         switch -exact -- $userArgsArray(qinq_incr_mode) {
                          "both" {
                               #set outerRepeat [expr {$AddrRepeatCount/$outerCount} - 1]
                               #set repeat [expr {$AddrRepeatCount/$count} - 1]
                                if {[info exists userArgsArray(vlan_id_outer_repeat)]} {
                                    set outerRepeat $userArgsArray(vlan_id_outer_repeat)
                                } 
                                if {[info exists userArgsArray(vlan_id_repeat)]} {
                                    set repeat $userArgsArray(vlan_id_repeat)
                                } 
                           }
                           "inner" {
                                set outerRepeat [expr $count - 1]
                                if {[info exists userArgsArray(vlan_id_repeat)]} {
                                    set repeat $userArgsArray(vlan_id_repeat)
                                } 
                           }
                           "outer" {
                                if {[info exists userArgsArray(vlan_id_outer_repeat)]} {
                                    set outerRepeat $userArgsArray(vlan_id_outer_repeat)
                                } 
                                set repeat [expr $outerCount - 1]
                           }
                        }

                        set vlanif [::sth::sthCore::invoke ::stc::create vlanif -under $hndDsthost \
                                      -vlanid $vlanid \
                                      -Priority $pri \
                                      -idstep $vlanstep \
                                      -IdRepeatCount $outerRepeat \
                                      -IfRecycleCount $outerCount]
                          set configStatus [::sth::sthCore::invoke ::stc::config $vlanif -StackedOnEndpoint-targets $lowerif]
                          set lowerif $vlanif
                    }
                    if {[info exists userArgsArray(vlan_id)]} {
                        set vlanid $userArgsArray(vlan_id)
                        if {[info exists userArgsArray(vlan_id_step)]} {
                            set vlanstep $userArgsArray(vlan_id_step);
                        } else {
                            set vlanstep  0
                        }
                        if {[info exists userArgsArray(vlan_user_priority)]} {
                            set pri $userArgsArray(vlan_user_priority);
                        } else {
                            set pri  0
                        }
                        if {[info exists userArgsArray(vlan_id_count)]} {
                            set count $userArgsArray(vlan_id_count);
                        } else {
                            set count 1
                        }
                        if {![info exists repeat]} {
                            if {[info exists userArgsArray(vlan_id_repeat)]} {
                                set repeat $userArgsArray(vlan_id_repeat);
                            } else {
                                set repeat 0
                            }
                        } 
                        set vlanif [::sth::sthCore::invoke ::stc::create vlanif -under $hndDsthost \
                                      -vlanid $vlanid \
                                      -Priority $pri \
                                      -idstep $vlanstep \
                                      -IdRepeatCount $repeat \
                                      -IfRecycleCount $count]
                          set configStatus [::sth::sthCore::invoke ::stc::config $vlanif -StackedOnEndpoint-targets $lowerif]
                          set lowerif $vlanif
                    }
                    set ipBlk ""
                    if { ![string compare -nocase $L3Protocol "ipv4" ]} {
                        set hndIpv4if [::sth::sthCore::invoke ::stc::create ipv4if -under $hndDsthost\
                                           -Address $Address\
                                           -AddrRepeatCount 0 \
                                           -AddrStep $AddrStep\
                                           -Gateway $Gateway]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndDsthost -TopLevelIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndDsthost -PrimaryIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndIpv4if -StackedOnEndpoint-targets $lowerif]
                        set configStatus [::sth::sthCore::invoke ::stc::config $streamBlkHandle -DstBinding-targets $hndIpv4if];
                        set ipBlk $hndIpv4if
                    } elseif { ![string compare -nocase $L3Protocol "ipv6" ]} {
                        # Fix for the lower layer returning an interface stack
                        # validation error. The name of this variable should
                        # probably be changed. This repeat count on the 
                        # v4/v6 object should typically be set to 0.
                        set hndIpv6if [::sth::sthCore::invoke ::stc::create ipv6if -under $hndDsthost\
                                           -Address $Address\
                                           -AddrRepeatCount 0 \
                                           -AddrStep $AddrStep\
                                           -Gateway $Gateway]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndDsthost -TopLevelIf-targets $hndIpv6if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndDsthost -PrimaryIf-targets $hndIpv6if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndIpv6if -StackedOnEndpoint-targets $lowerif]
                        set configStatus [::sth::sthCore::invoke ::stc::config $streamBlkHandle -DstBinding-targets $hndIpv6if];
                        set ipBlk $hndIpv6if
                    } else {
                        set hndIpv4if [::sth::sthCore::invoke ::stc::create ipv4if -under $hndDsthost]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndDsthost -TopLevelIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndDsthost -PrimaryIf-targets $hndIpv4if]
                        set configStatus [::sth::sthCore::invoke ::stc::config $hndIpv4if -StackedOnEndpoint-targets $lowerif]
                        set configStatus [::sth::sthCore::invoke ::stc::config $streamBlkHandle -DstBinding-targets $hndIpv4if];
                        set ipBlk $hndIpv4if
                    }
                   
                    set portHandle $userArgsArray(port_handle)
                    set hosts [::sth::sthCore::invoke stc::get project1 -children-host]
                    foreach host $hosts {
                        if {[::sth::sthCore::invoke stc::get $host -name] == "port_address"} {
                            if {[info exists userArgsArray(mac_discovery_gw)]} {
                                set hostIfs [::sth::sthCore::invoke stc::get $host -PrimaryIf-targets]
                                foreach hostIf $hostIfs {
                                    set hostGw [::sth::sthCore::invoke stc::get $hostIf -Gateway]
                                    set hostGw [ip::normalize $hostGw]
                                    set Gateway $userArgsArray(mac_discovery_gw);
                                    if {$Gateway == $hostGw} {
                                       set bindhost $host
                                    }
                                }
                            } else {
                                set port [::sth::sthCore::invoke stc::get $host -AffiliationPort-targets]
                                if {$port != $portHandle} {
                                     set bindhost $host
                               }
                                         
                            }
                        }
                    }
                }
                
                
                ######################################################################
                # specially handle PathDescriptor for RSVP if No emulation_dst_handle
                ######################################################################
                # Check for RSVP and configure the path descriptor if necessary
                # Given that we are in this proc, there MUST be an emulation_src_handle but we'll check
                # just to make sure.
                if {$emulation_src_handle != 0} {
                    set objPos 0
                    # Destination binding is a single host block's ipvX interface right now...
                    # if there are multiple objects in the srcHandle list, we should repeat
                    # the ipvX interface block in the dstbinding list so that the pairwise block
                    # mapping will not error out (ie the number of blocks on the src and dst side
                    # should be the same)
                    set dstBindList ""
                    foreach srcHandle $emulation_src_handle {
                        lappend dstBindList $ipBlk
                        if {([string match "rsvp*gresstunnelparams*" $srcHandle]) || ([string match "ipv4prefixlsp*" $srcHandle]) || ([regexp {host\d+$} $object]) || ([regexp {router\d+$} $object]) || ([string match "summarylsablock*" $object])} {
                            set ipv4NetBlock [::sth::sthCore::invoke stc::get $srcHandle -children-ipv4networkblock]
                            if {[string match "host*" $srcHandle] || [string match "router*" $srcHandle]} {
                                if {[regexp -nocase "greif" [stc::get $srcHandle -children]]} {
                                    set temp_gre_handle [::sth::sthCore::invoke stc::get $srcHandle -children-greif]
                                    set ipv4NetBlock [::sth::sthCore::invoke stc::get $temp_gre_handle -StackedOnEndpoint-targets]
                                } else {
                                    set ipv4NetBlock [::sth::sthCore::invoke stc::get $srcHandle -children-ipv4if]
                                }
                            }
                            if {$ipv4NetBlock == ""} {
                                break
                            }
                            set pdList [::sth::sthCore::invoke stc::get $streamBlkHandle -children-pathdescriptor]
                            set pathDescriptor ""
                            foreach pathDesc $pdList {
                                set srcBind [::sth::sthCore::invoke stc::get $pathDesc -srcbinding-targets]
                                set dstBind [::sth::sthCore::invoke stc::get $pathDesc -dstbinding-targets]
                                if {[string match -nocase $srcBind $ipv4NetBlock] || \
                                        [string match -nocase $dstBind $ipv4NetBlock]} {
                                    set pathDescriptor $pathDesc
                                    break
                                }
                            }
                            # Determine whether we need to create a new path descriptor for this network block
                            # or if we just need to configure its endpoints.
                            if {$pathDescriptor == ""} {
                                set pathDescriptor [::sth::sthCore::invoke stc::create "PathDescriptor" -under $streamBlkHandle -Index $objPos]
                            }
                            if {([string match "rsvp*gresstunnelparams*" $srcHandle])} {
                                set mplsif [::sth::sthCore::invoke stc::get $srcHandle -resolvesinterface-targets]
                            } elseif {[string match "ipv4prefixlsp*" $srcHandle]} {
                                set ldpRtrConfHndl [::sth::sthCore::invoke stc::get $srcHandle -parent]
                                set rtrhndl [::sth::sthCore::invoke stc::get $ldpRtrConfHndl -parent]
                                set mplsif [::sth::sthCore::invoke stc::get $rtrhndl -children-mplsif]
                            } elseif {([string match "host*" $srcHandle]) || ([string match "router*" $srcHandle]) || ([string match "summarylsablock*" $srcHandle])} {                          
                                set mplsif ""
                                set tunnel_label_list "tunnel_bottom_label tunnel_next_label tunnel_top_label"
                                foreach tunnel_label $tunnel_label_list {
                                    if {[info exists userArgsArray($tunnel_label)]} {
                                        set tunnel_router $userArgsArray($tunnel_label);
                                        if {$tunnel_router == ""} {
                                            break;
                                        }
                                        if {[catch {append mplsif [lindex [::sth::sthCore::invoke stc::get $tunnel_router -children-mplsif] 0] " "} errMsg]} {
                                            ::sth::sthCore::log error $errMsg
                                            return -code error $errMsg
                                        }
                                    } else {
                                        break;    
                                    }
                                }
                            }
                            #set mplsif [stc::get $srcHandle -resolvesinterface-targets]
                            ::sth::sthCore::invoke stc::config $pathDescriptor -srcbinding-targets $ipv4NetBlock \
                                -dstbinding-targets $ipBlk -encapsulation-targets $mplsif
                        }
                    }
                    ::sth::sthCore::invoke stc::config $streamBlkHandle -DstBinding-targets $dstBindList
                }
            }
            return $::sth::sthCore::SUCCESS;
        }

        ################################################################################
        ############# When ::sth::sthCore::UseModifier4TrafficBinding = 0, the following
        ############# block of code is not used
        ################################################################################
        if { [llength $emulation_src_handle] > 1 || [llength $emulation_dst_handle] > 1} {
            set errMsg "Handle list is not supported for UseModifier4TrafficBinding"
            ::sth::sthCore::log error $errMsg
            return -code error errMsg
        }
        if { $emulation_src_handle != 0 } {
            #if { [string first host $emulation_src_handle] == 0 ||\
            #     [string first router $emulation_src_handle] >= 0 } {
                if { $emulation_dst_handle != 0 } {
                    
                    #For L2 and L3 traffic check
                    if { [info exists userArgsArray(traffic_type)] && [string match -nocase "l2" $userArgsArray(traffic_type) ] } {
                        set srcBlockHandle [::sth::Traffic::GetLayerTwoHandle $emulation_src_handle ]
                        set dstBlockHandle [::sth::Traffic::GetLayerTwoHandle $emulation_dst_handle ]
                    } else {
                        set srcBlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_src_handle ]
                        set dstBlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_dst_handle ]
                    } 
                  
                    ##puts "srcBlockHandle = [stc::get $srcBlockHandle]"
                    if { [catch {::sth::sthCore::invoke ::stc::config $streamBlkHandle -SrcBinding-targets $srcBlockHandle \
                                                                -DstBinding-targets $dstBlockHandle } errMsg ] } {
                        ::sth::sthCore::log error $errMsg
                        return -code error $errMsg
                    }
                    return $::sth::sthCore::SUCCESS
                } else {
                    #set errMsg "Error in processSrcDstEmulationHandles: Missing emulation_dst_handle for $streamBlkHandle. \nWhen you bind host/router to the src of a streamblock, you have to bind a host/router \n or a networkblock to emulation_dst_handle"
                    #::sth::sthCore::log error $errMsg
                    #return -code error $errMsg
                    set networkBlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_src_handle]
                    #Bind to traffic source via RangeModifier
                    if { [catch {::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier $streamBlkHandle $networkBlockHandle src} errMsg] } {
                        set errorMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: $errMsg"
                        ::sth::sthCore::log error $errorMsg
                        return -code error $errorMsg
                    }
                }
            #}
            #else {
            #    set networkBlockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_src_handle]
            #    #Bind to traffic source via RangeModifier
            #    if { [catch {::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier $streamBlkHandle $networkBlockHandle src} errMsg] } {
            #        set errorMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: $errMsg"
            #        ::sth::sthCore::log error $errorMsg
            #        return -code error $errorMsg
            #    }
            #}
        }
    }
    
    
    if { $emulation_dst_handle != 0 } {
        set blockHandle [::sth::Traffic::GetIpOrNetworkBlockHandle $emulation_dst_handle]
        if { [string first host $emulation_dst_handle] == 0 || \
             [string first router $emulation_dst_handle] >= 0 } {
            #Bind to traffic dst via tablemodifier
            #Delete the dst range modifier first if any.
            if {[string first  ipv4if $blockHandle] == 0} {
                set addrListLen [llength [::sth::sthCore::invoke ::stc::get $blockHandle -addrList]]
            } else {
                set addrListLen [llength [::sth::sthCore::invoke ::stc::get $blockHandle -addrList]]
            }
            if { $addrListLen ==  0} {
                #Bind to traffic dst via rangeModifier
                if { [catch {::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier $streamBlkHandle $blockHandle dst} errMsg] } {
                    set errorMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: $errMsg"
                    ::sth::sthCore::log error $errorMsg
                    return -code error $errorMsg
                }
            } else {
                #Bind to traffic dst via tableModifier
                if { [catch {::sth::Traffic::BindIpAddrListToTrafficUseTableModifier $streamBlkHandle $blockHandle dst} errMsg] } {
                    set errorMsg "Error in ::sth::Traffic::BindIpAddrListToTrafficUseTableModifier: $errMsg"
                    ::sth::sthCore::log error $errorMsg
                    return -code error $errorMsg
                }                
            }
        } else {
            #Bind to traffic dst via rangeModifier
            if { [catch {::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier $streamBlkHandle $blockHandle dst} errMsg] } {
                set errorMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: $errMsg"
                ::sth::sthCore::log error $errorMsg
                return -code error $errorMsg
            }
        }
    }
    return $::sth::sthCore::SUCCESS
}


proc ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier { streamBlkHandle blockHandle SrcOrDst } {
    
    upvar userArgsArray userArgsArray;
    
    #puts "::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier \{ streamBlkHandle blockHandle=$blockHandle SrcOrDst \}"
    if {[string first ipv4 $blockHandle] == 0} {
        set addrType ipv4
    } elseif {[string first ipv6 $blockHandle] == 0} {
        set addrType ipv6
    } else {
       set errMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: Invalid blockHandle; it should be either ipv4if/ipv4networkblock, ipv6/ipv6networkblock"
       ::sth::sthCore::log error $errMsg
       return -code error $errMsg
    }
    #set listOfModifiers [::stc::get $streamBlkHandle -children-RangeModifier]
    #set modifier 0
    set keyedList [::sth::Traffic::GetHeaderAndSrcDstModifiers $streamBlkHandle]
    set header [keylget keyedList ipheader]
    set headerName [::sth::sthCore::invoke ::stc::get $header -name]
    if { $header == 0 || [string first $addrType $headerName] != 0} {
        set errMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: Missing or Mismatch IP Header in $streamBlkHandle \(ipheader = $header, addrType = $addrType\)"
        ::sth::sthCore::log error $errMsg
        return -code error "$errMsg"
    }
    set srcmodifier [keylget keyedList srcmodifier]
    set dstmodifier [keylget keyedList dstmodifier]
    if { $SrcOrDst == "src" } {
        if { $srcmodifier == 0 } {
            set modifier [::sth::sthCore::invoke ::stc::create "RangeModifier" -under $streamBlkHandle -offsetReference "$headerName\.sourceAddr" ]
        } else {
            set modifier $srcmodifier
        }
    } elseif { $SrcOrDst == "dst" } {
        if { $dstmodifier == 0 } {
            set modifier [::sth::sthCore::invoke ::stc::create "RangeModifier" -under $streamBlkHandle -offsetReference "$headerName\.destAddr" ]
        } else {
            set modifier $dstmodifier
        }
    } else {
        ::sth::sthCore::log error "Invalid value ($SrcOrDst): please set to src or dst"
        return -code error "Invalid value ($SrcOrDst): please set to src or dst"
    }
    set offsetReference [::sth::sthCore::invoke ::stc::get $modifier -offsetReference]
    
    if { [string first networkblock $blockHandle] > 0 } {
        set ipAddrBlockStartIp [::sth::sthCore::invoke ::stc::get $blockHandle -StartIpList]
        set prefixleng [::sth::sthCore::invoke ::stc::get $blockHandle -prefixlength]
        set stepValue  [::sth::sthCore::invoke ::stc::get $blockHandle -addrIncrement]
        set networkCount [::sth::sthCore::invoke ::stc::get $blockHandle -NetworkCount]
    } else {
        set ipAddrBlockStartIp [::sth::sthCore::invoke ::stc::get $blockHandle -address]
        set prefixleng [::sth::sthCore::invoke ::stc::get $blockHandle -prefixlength]
        set stepValue  [::sth::sthCore::invoke ::stc::get $blockHandle -addrStep]
        set networkCount  [::sth::sthCore::invoke ::stc::get $blockHandle -AddrRepeatCount]
    }
    set networkCount 3
    ##puts "ip header\:$header = [stc::get $header]"
    
    if { $SrcOrDst == "src"  } {
        set status [::sth::sthCore::invoke ::stc::config $header -sourceAddr [::ip::normalize $ipAddrBlockStartIp] ]
        set destAddr [::sth::sthCore::invoke ::stc::get $header -destAddr]
        if {[string length $destAddr] == 0} {
            set errMsg "ERROR In  ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: $header\.destAddr is empty, please set destAddr in $header"
            ::sth::sthCore::log error $errMsg
            return -code error $errMsg
        }
    } elseif { $SrcOrDst == "dst" } {
        set status [::sth::sthCore::invoke ::stc::config $header -destAddr [::ip::normalize $ipAddrBlockStartIp] ]
        set sourceAddr [::sth::sthCore::invoke ::stc::get $header -sourceAddr]
        if {[string length $sourceAddr] == 0} {
            set errMsg "ERROR In  ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: $header\.sourceAddr is empty, please set sourceAddr in $header:[::sth::sthCore::invoke stc::get $header]"
            ::sth::sthCore::log error $errMsg
            return -code error $errMsg
        }
    } else {
        set errMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: Invalid Src or Dst ($SrcOrDst)"
        ::sth::sthCore::log error $errMsg
        return -code error $errMsg
    }
    
    ##puts "header = [stc::get $header]"
    
    if { $addrType == "ipv6" } {
        set retKeyedList [::sth::Traffic::prepareIPv6RangeModifier \
                          $ipAddrBlockStartIp\
                          $prefixleng\
                          $stepValue]
        if { [catch {set reStatus [::sth::sthCore::invoke ::stc::config $modifier \
            -enableStream $userArgsArray(enable_stream)\
            -dataType byte\
            -data [keylget retKeyedList data]\
            -Offset [keylget retKeyedList offset]\
            -ModifierMode "INCR"\
            -mask [keylget retKeyedList mask]\
            -offsetReference $offsetReference\
            -StepValue [keylget retKeyedList stepvalue]\
            -RecycleCount $networkCount\
            -RepeatCount 0 ] } errMsg]} {
                ::sth::sthCore::log error $errMsg
                return -code error $errMsg
        }                  
    } else {
        set position [expr {32 - $prefixleng}]
        set mask [::ip::lengthToMask $prefixleng]
        set stepValue [::ip::intToString [expr {$stepValue * [expr int ( [expr pow(2, $position)])]}]]
        if { [catch {set reStatus [::sth::sthCore::invoke ::stc::config $modifier \
            -enableStream false\
            -data $ipAddrBlockStartIp\
            -Offset 0\
            -ModifierMode "INCR"\
            -mask $mask\
            -offsetReference $offsetReference\
            -StepValue $stepValue\
            -RecycleCount $networkCount\
            -RepeatCount 0 ] } errMsg ]} {
                ::sth::sthCore::log error $errMsg
                return -code error $errMsg
        }
    }
    return $::sth::sthCore::SUCCESS
}        


proc ::sth::Traffic::prepareIPv6RangeModifier { ipv6Addr prefixLength stepValue } {
    array set byteMask { 1 128 \
                   2 192 \
                   3 224 \
                   4 240 \
                   5 248 \
                   6 252 \
                   7 254 }
    set returnKeyedList ""
    set q [expr { $prefixLength / 8 } ]
    set r [expr { $prefixLength % 8 } ]
    
    set stepValue [format "%02x" $stepValue]
    keylset returnKeyedList stepvalue $stepValue
    
    set ipv6Addr [::ip::normalize $ipv6Addr]
    set ipv6Addr [split $ipv6Addr ":"]
    set ipv6Addr [join $ipv6Addr "" ]
    if { $r == 0 } {
        set start [expr {$q * 2}]
        set end   [expr {$start + 1}]
        keylset returnKeyedList offset $q
    } else {
        set start [expr {[expr {$q * 2}] + 1}]
        set end [expr {$start + 1}]
        keylset returnKeyedList [expr {$q + 1}]
    }
    set data [string range $ipv6Addr $start $end]
    keylset returnKeyedList data $data
    keylset returnKeyedList ipv6addr $ipv6Addr
    
    if { $r != 0 } {
        set mask [format "%02x" $byteMask($r)]
        
    } else {
        set mask ff
    }
    keylset returnKeyedList mask $mask
    
    return $returnKeyedList
}

proc ::sth::Traffic::BindIpAddrListToTrafficUseTableModifier { streamBlkHandle blockHandle SrcOrDst } {
    
    upvar userArgsArray userArgsArray;
    
    if {[string first ipv4 $blockHandle] == 0} {
        set addrType ipv4
    } elseif {[string first ipv6 $blockHandle] == 0} {
        set addrType ipv6
    } else {
       set errMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: Invalid blockHandle; it should be either ipv4if/ipv4networkblock, ipv6/ipv6networkblock"
       ::sth::sthCore::log error $errMsg
       return -code error $errMsg
    }
    #set listOfModifiers [::stc::get $streamBlkHandle -children-RangeModifier]
    #set modifier 0
    set keyedList [::sth::Traffic::GetHeaderAndSrcDstModifiers $streamBlkHandle]
    set header [keylget keyedList ipheader]
    set headerName [::sth::sthCore::invoke ::stc::get $header -name]
    if { $header == 0 || [string first $addrType $headerName] != 0} {
        set errMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: Missing or Mismatch IP Header in $streamBlkHandle (ipheader = $header, addrType = $addrType)"
        ::sth::sthCore::log error $errMsg
        return -code error "$errMsg"
    }
    set srcmodifier [keylget keyedList srcmodifier]
    set dstmodifier [keylget keyedList dstmodifier]
    if { $SrcOrDst == "src" } {
        if { $srcmodifier == 0 } {
            set modifier [::sth::sthCore::invoke ::stc::create "TableModifier" -under $streamBlkHandle -offsetReference "$headerName\.sourceAddr"]
            set offsetReference [::sth::sthCore::invoke ::stc::get $modifier -offsetReference]
        }
    } elseif { $SrcOrDst == "dst" } {
        if { $dstmodifier == 0 } {
            set modifier [::sth::sthCore::invoke ::stc::create "TableModifier" -under $streamBlkHandle -offsetReference "$headerName\.destAddr"]
            set offsetReference [::sth::sthCore::invoke ::stc::get $modifier -offsetReference]
        }
    } else {
        ::sth::sthCore::log error "Invalid value ($SrcOrDst): please set to src or dst"
        return -code error "Invalid value ($SrcOrDst): please set to src or dst"
    }    

    #Before this function is called, the value of -address is checked  and it is not null.
    set ipAddrList [::sth::sthCore::invoke ::stc::get $blockHandle -addrList]
    set ipAddrBlockStartIp [lindex $ipAddrList 0]

    # replace the ip address in the IP header
    if { $SrcOrDst == "src"  } {
        set status [::sth::sthCore::invoke ::stc::config $header -sourceAddr $ipAddrBlockStartIp ]
    } elseif { $SrcOrDst == "dst" } {
        set status [::sth::sthCore::invoke ::stc::config $header -destAddr $ipAddrBlockStartIp ]
    } else {
        set errMsg "Error in ::sth::Traffic::BindIpAddrBlockToTrafficUseRangeModifier: Invalid Src or Dst ($SrcOrDst)"
        ::sth::sthCore::log error $errMsg
        return -code error $errMsg
    }
   
    #Create the tableModifier for Ip interface which as a list of ip addresses in addrlist
    if { [catch {::sth::sthCore::invoke ::stc::config $modifier \
        -enableStream $userArgsArray(enable_stream)\
        -data $ipAddrList\
        -Offset 0\
        -offsetReference $offsetReference\
        -RepeatCount 0 } errMsg]} {
            ::sth::sthCore::log error $errMsg
            return -code 1 -errorcode $::sth::sthCore::FAILURE $errMsg
    }
    return $::sth::sthCore::SUCCESS
}        

proc ::sth::Traffic::processVplsTraffic { srcHandle dstHandle } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _procName "processVplsTraffic";
    upvar userArgsArray userArgsArray;
    upvar mns mns;
    
    set streamHandle [set ::$mns\::handleCurrentStream]
    
    set srcIf ""
    set dstIf ""
    
    #get src and dst interfaces' handles
    #source
    if {[catch {set srcIf [::sth::sthCore::invoke stc::get $srcHandle -PrimaryIf-Targets]} errMsg]} {
        ::sth::sthCore::log error "Error in $_procName: $errMsg" 
        return $FAILURE
    }
    
    #destination
    if {[catch {set dstIf [::sth::sthCore::invoke stc::get $dstHandle -PrimaryIf-Targets]} errMsg]} {
        ::sth::sthCore::log error "Error in $_procName: $errMsg" 
        return $FAILURE
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $streamHandle "-SrcBinding $srcIf -DstBinding $dstIf"}]} {
        ::sth::sthCore::log error "Error in $_procName: $errMsg" 
        return $FAILURE                    
    }
    
    #auto select mpls tunnel
    if {[catch {::sth::sthCore::invoke stc::perform StreamBlockAutoSelectTunnel -StreamBlockList $streamHandle} errMsg]} {
        ::sth::sthCore::log error "Error in $_procName: $errMsg" 
        return $FAILURE                    
    }
    return $SUCCESS
}

proc ::sth::Traffic::GetTopLevelIfHandle { emulation_handles } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _procName "GetTopLevelIfHandle";
    set ifHandleList ""
    foreach emulation_handle $emulation_handles {
        set ifHandle 0
        if {[catch {set ifHandle [::sth::sthCore::invoke stc::get $emulation_handle -TopLevelIf-Targets]} errMsg]} {
            ::sth::sthCore::log error "Error in $_procName: $errMsg" 
            return $FAILURE
        }
        
        lappend ifHandleList $ifHandle
        
    }
    return $ifHandleList
}

# to remove the xxModifier associated with the object which is to be deleted
proc ::sth::Traffic::ProcessDirtyModifier { strHandle deleteHandle } {
    if {[llength $strHandle] != 0 && [llength $deleteHandle] != 0} {
            
        if {[catch {set name [::sth::sthCore::invoke stc::get $deleteHandle -name]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList 
        }
        
        if {[catch {set strChild [::sth::sthCore::invoke stc::get $strHandle -children]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList 
        }
    
        foreach child $strChild {
            if {![regexp -nocase "modifier" $child]} {
                continue
            }
            if {[catch {set offset [::sth::sthCore::invoke stc::get $child -OffsetReference]} err]} {
                ::sth::sthCore::processError returnKeyedList "::stc::get Failed: $err" {}
                return -code error $returnKeyedList 
            }
            if {[regexp -nocase $name $offset]} {
                if {[catch {::sth::sthCore::invoke stc::delete $child} err]} {
                    ::sth::sthCore::processError returnKeyedList "::stc::delete Failed: $err" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
}


# to delete the handle, currently this profunction is only used for layer 4
# it can also be used for other layer in the future
proc ::sth::Traffic::ProcessDeleteHandle { strHandle Handle tag } {
    
    set _procName "ProcessDeleteHandle";   
  
    #the customTyp need to update in the future.
    switch -exact $tag {
        "l4" {
            set customTyp "RTP_PT RTP_Seq RTP_TimeStamp RTP_ssrc RTP_csrc ISIS_Llc ISIS_L1Hello";
        }
        "l3" {
            set customTyp "";
        }
        "l2" {
            set customTyp "ipx appletalk aarp decnet vines xns";
        }
    }
    
    foreach headerHandle $Handle {
        set updateHdl "";
        #if the headerhandle is ended with number, it must be handled specially
        #specally handling for the igmpv1/v2
        if {[regexp -nocase {igmp:Igmpv1(\d+)?$} $headerHandle]} {
            set objectName "igmp:Igmpv1"
        } elseif {[regexp -nocase {igmp:Igmpv2(\d+)?$} $headerHandle]} {
            set objectName "igmp:Igmpv2"
        } else {
            regsub -all {\d+$} $headerHandle "" objectName
        }
        
        #update handle because the handle will be changed after applying
        if {[catch {set updateHandleList [::sth::sthCore::invoke stc::get $strHandle -children-$objectName]} errMsg]} {
            ::sth::sthCore::log error $errMsg
            return -code error $errMsg
        } else {
            ::sth::sthCore::log info "$_procName: stc::get Success. Handle is $updateHandleList";
        }
        
        foreach updateHandle $updateHandleList {
            if {[regexp -nocase "custom:custom" $updateHandle]} {
                # if the Handle is custom handle, need to check if it is indeed for this layer
                if {[catch {set headerName [::sth::sthCore::invoke stc::get $updateHandle -name]} errMsg]} {
                    ::sth::sthCore::log error $errMsg
                    return -code error $errMsg
                }
                foreach customElement $customTyp {
                    if {[regexp -nocase $customElement $headerName]} {
                        lappend updateHdl $updateHandle;
                        break;
                    }
                }
            } else {
                lappend updateHdl $updateHandle;
            }
        }
        #to delete the handle;
        foreach deleteHandle $updateHdl {
            ProcessDirtyModifier $strHandle $deleteHandle
            ::sth::sthCore::invoke stc::delete $deleteHandle
        }
    }
    
}
proc ::sth::Traffic::processCreateQosModifier {Handle listName tag} {
    set _procName "processCreateQosModifier";
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    upvar prioritisedAttributeList prioritisedAttributeList;
        
    set listArgsList {};
    array set arrayArgsList {};
    set prefixLenAttrNeeded 0;
    set data "";
    set data_list "";
    set AccumulateTimes 2;
    set offsetReferenceValue 0;
    
    # Get the name of the header here
    ::sth::sthCore::log debug "$_procName: Calling ::stc::get $Handle -name"
    set ipHeaderName [::sth::sthCore::invoke stc::get $Handle -name]
    
    # set the offsetReference and offsetReferenceValue in tos or precedence mode.
    
    if {[regexp tos $tag]} {
        set offsetReferenceName "$ipHeaderName\.tosDiffserv.tos";
        set AccumulateTimes 2
        if {[info exists userArgsArray($tag\_field)]} {
            set offsetReferenceValue [split $userArgsArray($tag\_field) " "]
        }
    } else {
        set offsetReferenceName "$ipHeaderName\.tosDiffserv.tos";
        set AccumulateTimes 32
        if {[info exists userArgsArray($tag)]} {
            set offsetReferenceValue [split $userArgsArray($tag) " "]
        }
    }
    
    #handle the data
    foreach value $offsetReferenceValue {
            set valuedecimal [expr $value*$AccumulateTimes]
            set valuebin [sth::Traffic::decimal2binary $valuedecimal 8]
            set data [::sth::sthCore::binToHex $valuebin]
            lappend data_list $data;
    }

    lappend listArgsList -OffsetReference $offsetReferenceName;
    lappend listArgsList -data $data_list;
    
    #set ModifierMode
    set mod ""
    
    if {[llength $offsetReferenceValue] >1} {
        set mod "TABLE"
    } elseif {[info exists userArgsArray($tag\_mode)]} {
        set mod $userArgsArray($tag\_mode)
        if { $mod != "fixed"} {
            set tableName "::$mns\::traffic_config_$tag\_mode_fwdmap"
            set mod [set $tableName\($mod)];
        }
    } else {
        set mod "INCR"
    }
    
    
    lappend listArgsList -ModifierMode $mod;
    
      
      
    #set modifierType
    set rangeModifier "";
    set randomModifier "";
    set modifierType "";

    if {[llength $offsetReferenceValue] >1} {
        set modifierType "tableModifier"
    } elseif {[info exists userArgsArray($tag\_mode)]} {
        if { $userArgsArray($tag\_mode) == "random"} {
            set modifierType "randomModifier"
        } elseif {$userArgsArray($tag\_mode) != "fixed"} {
            set modifierType "rangeModifier"
        }
    } elseif {![info exists userArgsArray($tag\_mode)] && ([info exists userArgsArray($tag\_count)] || [info exists userArgsArray($tag\_step)])} {
        set modifierType "rangeModifier"
    }
        
     
    #add other necessary arguments.
    lappend listArgsList -EnableStream $::sth::Traffic::enableStream;
    lappend listArgsList -Offset 0;
    lappend listArgsList -DataType BYTE;    
    
    #count
    set countValue 1;
    if {[info exists userArgsArray($tag\_count)]} {
        set countValue $userArgsArray($tag\_count);
    }
    set stcAttr [set ::$mns\::traffic_config_stcattr($tag\_count)];
    lappend listArgsList -$stcAttr $countValue;
    
    # step
    if {[regexp precedence $tag]} {
     
        if {$modifierType == "rangeModifier"} {
            set stcAttr [set ::$mns\::traffic_config_stcattr($tag\_step)];
            if {[info exists userArgsArray($tag\_step)]} {
                set stepValuedecimal [expr $userArgsArray($tag\_step)*32];
                set stepValuebin [sth::Traffic::decimal2binary $stepValuedecimal 8];
                set stepValue [::sth::sthCore::binToHex $stepValuebin]
            } else {
                set stepValue 20;
            }
            lappend listArgsList -$stcAttr $stepValue;
        }
        
        lappend listArgsList -Mask "E0";
    }
    
    if {[regexp tos $tag]} {
        
        if {$modifierType == "rangeModifier"} {
            set stcAttr [set ::$mns\::traffic_config_stcattr($tag\_step)];
            if {[info exists userArgsArray($tag\_step)]} {
                set stepValuedecimal [expr $userArgsArray($tag\_step)*2];
                set stepValuebin [sth::Traffic::decimal2binary $stepValuedecimal 8];
                set stepValue [::sth::sthCore::binToHex $stepValuebin]
                
            } else {
                set stepValue 02;
            }
            
            lappend listArgsList -$stcAttr $stepValue;
        }
        
        lappend listArgsList -Mask "1E";
    }
    
    #create modifer or modify the modifier

    set handle [set ::$mns\::handleCurrentStream]
    if {[regexp {^-} $listArgsList]} {
        regsub {^-} $listArgsList {} listArgsList
    }
    foreach {attr val} $listArgsList {
        set arrayArgsList($attr) $val;
    }
    
    if {$userArgsArray(mode) == "modify"} {
        #handle arrayArgsList, generate the list with default value and without default value sepereately
        set attrList [array get arrayArgsList]
        foreach {attr val} $attrList {
            if {[info exists prioritisedAttributeList($attr)]} {
                set arrayArgsList($attr) $val
            }
        }
    }
    
    set arrayList [array get arrayArgsList]
    ::sth::Traffic::ProcessModifier $handle $arrayList;
    
}

proc ::sth::Traffic::processStreamHeader {streamBlkHandle} {
    
    upvar mns mns;
    set listOfHeaders [set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream])]
    ::sth::sthCore::invoke stc::perform StreamBlockUpdate -streamblock $streamBlkHandle
    #here only process the IPv4 header, when there is vxlan if there will be 2 ipv4 header, and the 2nd one is the inner_l3_header 
    #other wise if the is 2 IPv4 header the 1st one will be l3_header_outer
    set str_chidlren [::sth::sthCore::invoke stc::get $streamBlkHandle -children]
    if {[regexp -nocase "ipv4" $str_chidlren]} {
        set ipv4_headers [::sth::sthCore::invoke stc::get $streamBlkHandle -children-ipv4:ipv4]
    } else {
        set ipv4_headers ""
    }
    if {[regexp -nocase "ipv6" $str_chidlren]} {
        set ipv6_headers [::sth::sthCore::invoke stc::get $streamBlkHandle -children-ipv6:ipv6]
    } else {
        set ipv6_headers ""
    }
    if {[regexp -nocase "vxlan" $str_chidlren]} {
        set vxlan_header [::sth::sthCore::invoke stc::get $streamBlkHandle -children-vxlan:vxlan]
    } else {
        set vxlan_header ""
    }

    if {[llength $ipv4_headers] > 1} {
        if {$vxlan_header == ""} {
            lappend listOfHeaders "l3_header_outer"
            lappend listOfHeaders [lindex $ipv4_headers 0]
            lappend listOfHeaders "l3_header"
            lappend listOfHeaders [lindex $ipv4_headers 1]
        } else {
            lappend listOfHeaders "l3_header"
            lappend listOfHeaders [lindex $ipv4_headers 0]
            lappend listOfHeaders "inner_l3_header"
            lappend listOfHeaders [lindex $ipv4_headers 1]
        }
    } elseif {[llength $ipv4_headers] == 1} {
        lappend listOfHeaders "l3_header"
        lappend listOfHeaders $ipv4_headers
    }
    if {[llength $ipv6_headers] > 0} {
        lappend listOfHeaders "l3_header"
        lappend listOfHeaders $ipv6_headers
    }
    set ::$mns\::arraystreamHnd([set ::$mns\::handleCurrentStream]) $listOfHeaders;
}

proc ::sth::Traffic::imix_config_create {rklName} {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Traffic::imix_config_create $rklName"
    variable userArgsArray
    upvar 1 $rklName returnKeyedList
    set frameLenDist [::sth::sthCore::invoke stc::create FrameLengthDistribution -under $::sth::GBLHNDMAP(project)]
    if {[info exists userArgsArray(name)]} {
        ::sth::sthCore::invoke stc::config $frameLenDist -name $userArgsArray(name)
    }
    if {[info exists userArgsArray(seed)]} {
        ::sth::sthCore::invoke stc::config $frameLenDist -seed $userArgsArray(seed)
    }
    
    set frameLenDistSlot [::sth::sthCore::invoke stc::get $frameLenDist -children-FrameLengthDistributionSlot]
    configImixFrameLenDistSlot $frameLenDistSlot
    
    set name [::sth::sthCore::invoke stc::get $frameLenDist -name]
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    keylset returnKeyedList handle $frameLenDist
    keylset returnKeyedList name $name
}

proc ::sth::Traffic::imix_config_add {rklName} {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Traffic::imix_config_add $rklName"
    variable userArgsArray
    upvar 1 $rklName returnKeyedList
    if {![info exists userArgsArray(handle)]} {
        return -code error "handle is mandatory in the mode add"
    }
    set frameLenDistSlot [::sth::sthCore::invoke stc::create FrameLengthDistributionSlot -under $userArgsArray(handle)]
    configImixFrameLenDistSlot $frameLenDistSlot
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
}
proc ::sth::Traffic::configImixFrameLenDistSlot {frameLenDistSlot} {
    variable userArgsArray
    if {[info exists userArgsArray(frame_length_mode)]&&[regexp -nocase "random" $userArgsArray(frame_length_mode)]} {
        #random frame length
        ::sth::sthCore::invoke stc::config $frameLenDistSlot -FrameLengthMode random
        if {[info exists userArgsArray(min_frame_size)]} {
            ::sth::sthCore::invoke stc::config $frameLenDistSlot -MinFrameLength $userArgsArray(min_frame_size)
        }
        if {[info exists userArgsArray(max_frame_size)]} {
            ::sth::sthCore::invoke stc::config $frameLenDistSlot -MaxFrameLength $userArgsArray(max_frame_size)
        }
    } else {
        #fixed frame length
        if {[info exists userArgsArray(frame_size)]} {
            ::sth::sthCore::invoke stc::config $frameLenDistSlot -FixedFrameLength $userArgsArray(frame_size)
        }
    }
    if {[info exists userArgsArray(weight)]} {
        ::sth::sthCore::invoke stc::config $frameLenDistSlot -Weight $userArgsArray(weight)
    }
}

proc ::sth::Traffic::deletePduHandle {pduHandle} {
    set _procName "deletePduHandle";
    if {[catch {::sth::sthCore::invoke ::stc::delete $pduHandle} deleteRet]} {
    ::sth::sthCore::log error "$_procName: ::stc::delete $pduHandle failed. $deleteRet ";
    return $::sth::sthCore::FAILURE;
    } else {
      ::sth::sthCore::log info "$_procName: ::stc::delete $pduHandle passed. $deleteRet ";
    }
}

# DE17295 Failed to modify Frame threshold values
proc ::sth::Traffic::processThresholdAttributeList { prioritisedAttributeList } {
       
        set attributeLength [llength $prioritisedAttributeList]
        set thresholdAttributes {}
        set attributes {}
        
        # return frame threshold attributes and remove them from prioritisedAttributeList in modif mode.
        for {set elemIndex 0} {$elemIndex < $attributeLength} {incr elemIndex} {
            if {[lsearch [lindex $prioritisedAttributeList $elemIndex] "advanced_sequence_threshold"] == 1} {
                lappend thresholdAttributes "advanced_sequence_threshold"
                set prioritisedAttributeList [lreplace $prioritisedAttributeList $elemIndex $elemIndex]
                #update index and attributes count 
                set elemIndex [expr $elemIndex - 1]
                set attributeLength [expr $attributeLength - 1 ]
                continue
            }
            if {[lsearch [lindex $prioritisedAttributeList $elemIndex] "jumbo_frame_threshold"] == 1} {
                lappend thresholdAttributes "jumbo_frame_threshold"
                set prioritisedAttributeList [lreplace $prioritisedAttributeList $elemIndex $elemIndex]
                set elemIndex [expr $elemIndex - 1]
                set attributeLength [expr $attributeLength - 1 ]
                continue
            }
            if {[lsearch [lindex $prioritisedAttributeList $elemIndex] "oversize_frame_threshold"] == 1} {
                lappend thresholdAttributes "oversize_frame_threshold"
                set prioritisedAttributeList [lreplace $prioritisedAttributeList $elemIndex $elemIndex]
                set elemIndex [expr $elemIndex - 1]
                set attributeLength [expr $attributeLength - 1 ]
                continue
            }
            if {[lsearch [lindex $prioritisedAttributeList $elemIndex] "undersize_frame_threshold"] == 1} {
                lappend thresholdAttributes "undersize_frame_threshold"
                set prioritisedAttributeList [lreplace $prioritisedAttributeList $elemIndex $elemIndex]
                set elemIndex [expr $elemIndex - 1]
                set attributeLength [expr $attributeLength - 1 ]
                continue
            }
            
        }
        lappend attributes $prioritisedAttributeList
        lappend attributes $thresholdAttributes 
    return $attributes 
}
# DE17295 Failed to modify Frame threshold values
proc ::sth::Traffic::configFrameThreshold {} {

    set _procName "configFrameThreshold"
    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    variable listThresholdList

    foreach currPort $userArgsArray(port_handle) {
        set analyzerCurrent [::sth::sthCore::invoke stc::get $currPort -children-Analyzer]
        set analyzerConfig [::sth::sthCore::invoke stc::get $analyzerCurrent -children-AnalyzerConfig]
        set configStatus "::sth::sthCore::invoke stc::config $analyzerConfig $listThresholdList"
        if {[catch {eval $configStatus} returnHandle]} {
            return $::sth::sthCore::FAILURE;
        } else {
                ::sth::sthCore::log info "$_procName: Analyzer threshold config Success. ";
        }
    }

}
