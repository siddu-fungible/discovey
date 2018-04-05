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


proc ::sth::Traffic::processCreateOspfHeader {ospfTyp} {
    
    set _procName "processCreateOspfHeader";
    
    upvar userArgsArray userArgsArray;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set listArgsList {}
    set listArgsOspfObj {}
    set listArgsOspfHeaderObj {}
    set listArgsOspfHeaderAuthObj {}
    array set paramArr {};
    
    switch -exact $ospfTyp {
        "unknown" {
         set headerName "ospfv2:Ospfv2Unknown"
         set processSubOption "processOspfv2Unknown"
        }
        "hello" {
         set headerName "ospfv2:Ospfv2Hello"
         set processSubOption "processOspfv2Hello" 
        }
        "dd" {
         set headerName "ospfv2:Ospfv2DatabaseDescription"
         set processSubOption "processOspfv2DatabaseDescription"
        }
        "req" {
         set headerName "ospfv2:Ospfv2LinkStateRequest"
         set processSubOption "processOspfv2LinkStateRequest"
        }
        "update" {
         set headerName "ospfv2:Ospfv2LinkStateUpdate"
         set processSubOption "processOspfv2LinkStateUpdate"
        }
        "ack" {
         set headerName "ospfv2:Ospfv2LinkStateAcknowledge"
         set processSubOption "processOspfv2LinkStateAcknowledge"
        }
    }
                
    foreach elementPair $prioritisedAttributeList {
        set element [lindex $elementPair 1]
        set stcAttr [set ::$mns\::traffic_config_ospf_packets_stcattr($element)];
        ::sth::sthCore::log info " $_procName HLT: $element \t STC: $stcAttr"
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_packets_stcobj($element)];
        
        #check dependency
        set extHeaderType $ospfTyp;
        set intHeaderType [set ::$mns\::traffic_config_ospf_packets_dependency($element)];
    
        if {[lsearch $intHeaderType $extHeaderType] >= 0  || $intHeaderType == "_none_"} {
            switch -exact $stcObj {
                "ospfv2" {
                    #the common config for ospfobject
                    lappend listArgsOspfObj -$stcAttr $userArgsArray($element);
                }
                "ospfv2.header" {
                    #for common header config
                    if {$element == "ospf_type"} {
                        set tableName "::$mns\::traffic_config_ospf_packets_ospf_type_fwdmap"
                        set stcConst [set $tableName\($ospfTyp)];
                        lappend listArgsOspfHeaderObj -$stcAttr $stcConst;
                    } else {
                        lappend listArgsOspfHeaderObj -$stcAttr $userArgsArray($element);
                    }
                }
                "authSelect" {
                    #for common header config- auth
                    lappend listArgsOspfHeaderAuthObj -$stcAttr $userArgsArray($element);
                }
                "_none_" {
                    #nothing to do
                }
                default {
                    if {$ospfTyp == "update"} {
                        lappend listArgsList $element -$stcAttr $userArgsArray($element);
                    } else {
                        lappend listArgsList -$stcAttr $userArgsArray($element);
                    }
                }
            }
        } else {
            set errorString "Dependency Error for $element. ENTERED: $extHeaderType. EXPECTED: $intHeaderType";
            ::sth::sthCore::log debug " $_procName: $errorString "
            return -code 1 -errorcode -1 $errorString;
        }
    }


    if {$userArgsArray(mode) == "create"} {
        # we would have to create the header irrespective of the mode.
        set streamId $userArgsArray(stream_id)
        ::sth::sthCore::log debug " $_procName: Calling stc::create $headerName $streamId $listArgsOspfObj"
        set cmdName "::sth::sthCore::invoke ::stc::create $headerName -under $streamId $listArgsOspfObj";
        if {[catch {eval $cmdName} retHandle]} {
            ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
            return $::sth::sthCore::FAILURE;
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
	    ::sth::Traffic::processRetHandle ospf_handle $retHandle
        }
        
        # Add the header to the stream Handle array. This will be useful at the time of modify
        set listOfHeaders {};
        if {[info exists ::$mns\::arraystreamHnd($streamId)]} {
            set listOfHeaders [set ::$mns\::arraystreamHnd($streamId)];
        }
        
        lappend listOfHeaders "l4_header";
        lappend listOfHeaders "[set retHandle]";
        set ::$mns\::arraystreamHnd($streamId) $listOfHeaders;
        
        #create the packet header
        if {[catch {::sth::Traffic::processOspfPacketHeader $retHandle $listArgsOspfHeaderObj $listArgsOspfHeaderAuthObj} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
            return -code error $trafficKeyedList;
        }
        
        #process the sub options
        if {$processSubOption!= "processOspfv2Unknown"} {
            if {[catch {::sth::Traffic::$processSubOption $retHandle $listArgsList} errMsg]} {
                ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
                return -code error $trafficKeyedList;
            }
        }
    } else {
        set handle $userArgsArray(handle)
        if {[regexp -nocase $headerName $handle]} {
            if {$listArgsOspfObj != ""} {
                ::sth::sthCore::log debug " $_procName: Calling stc::config $handle $listArgsOspfObj"
                set cmdName "::sth::sthCore::invoke ::stc::config $handle $listArgsOspfObj";
                if {[catch {eval $cmdName} errMsg]} {
                    #puts "error while configuring $headerToConfigure";
                    ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
                    return $::sth::sthCore::FAILURE;
                } else {
                    ::sth::sthCore::log info " $_procName: stc::configNew Success. ";
                }
            }
           #modify the packet header
            if {$listArgsOspfHeaderObj != "" || $listArgsOspfHeaderAuthObj != ""} {
                if {[catch {::sth::Traffic::processOspfPacketHeader $handle $listArgsOspfHeaderObj $listArgsOspfHeaderAuthObj} errMsg]} {
                    ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
                    return -code error $trafficKeyedList;
                }
            }
        }
        
        #process the sub options
        if {$processSubOption!= "processOspfv2Unknown"} {
            if {[catch {::sth::Traffic::$processSubOption $handle $listArgsList} errMsg]} {
                ::sth::sthCore::processError trafficKeyedList "Error: $errMsg"
                return -code error $trafficKeyedList;
            }
        }
    }
    
    return ::sth::sthCore::SUCCESS;
    
}

#create the packet header for each kind of ospf object
proc ::sth::Traffic::processOspfPacketHeader {handle listHeader listAuth} {
    
    set _procName "processPacketHeader";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    set authSelectObj "";
    
    #create packet header
    if {[catch {::sth::sthCore::invoke stc::get $handle -children-header} retHeaderHandle]} {
        ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
        return -code error $trafficKeyedList 
    } else {
        ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
    }
    if { $retHeaderHandle =="" } {
        if {[catch {::sth::sthCore::invoke stc::create header -under $handle} retHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
        }
    }
    
    #config the header
    if {$listHeader != ""} {
        if {[catch {::sth::sthCore::invoke stc::config $retHeaderHandle $listHeader} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::config Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::config Success.";
        }
    }
    
    if {[info exists userArgsArray(ospf_auth_type)]} {
       switch -exact $userArgsArray(ospf_auth_type) {
        "none" {
            set authSelectObj "hdrAuthSelectNone"
            set type 0
        }
        "password" {
            set authSelectObj "hdrAuthSelectPassword"
            set type 1
        }
        "md5" {
            set authSelectObj "hdrAuthSelectCrypto"
            set type 2
        }
        "userdefined" {
            set authSelectObj "hdrAuthSelectUserDef"
            set type 3
        }
       }
       #replace the type with value
        set p [lsearch $listAuth $userArgsArray(ospf_auth_type)] 
            if {$p < 0} {
                lappend listAuth authType $type
            } else {
                #replace the original value
                set listAuth [lreplace $listAuth $p $p $type]
        }
    } elseif {$userArgsArray(mode) == "create"} {
        set authSelectObj "hdrAuthSelectNone"
        lappend listAuth "-authType 0"
    }
    
    if {[catch {::sth::sthCore::invoke stc::get $retHeaderHandle -children-authSelect} retAuthHandle]} {
        ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retAuthHandle"
        return -code error $trafficKeyedList 
    } else {
        ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retAuthHandle";
    }
    
    if {$retAuthHandle == ""} {
        if {[catch {::sth::sthCore::invoke stc::create authSelect -under $retHeaderHandle} retAuthHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retAuthHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retAuthHandle";
        }
        
        #create the autuselect
        if {[catch {::sth::sthCore::invoke stc::create $authSelectObj -under $retAuthHandle} retHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
        }
    } else {
        if {[catch {::sth::sthCore::invoke stc::get $retAuthHandle -children} retHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::getFail: $retHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::getSuccess. Handle is $retHandle";
        }
        #check if the auth_type is changed
        if {$authSelectObj != ""} {
            if {![regexp -nocase $authSelectObj $retHandle]} {
                #delete the created children and creat a new one
                ::sth::sthCore::invoke stc::delete $retHandle
                if {[catch {::sth::sthCore::invoke stc::create $authSelectObj -under $retAuthHandle} retHandle]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHandle"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
                }
            }
        }
        
    }
    
    if {$listAuth != ""} {
        if {[catch {::sth::sthCore::invoke stc::config $retHandle $listAuth} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::config Success.";
        }
    }

    

}

#process ospfv2 database description
proc ::sth::Traffic::processOspfv2DatabaseDescription {handle listName} {
    
    set _procName "processOspfv2DatabaseDescription";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    #handle ospf_packets_options and ospf_dd_options
    if {$userArgsArray(mode) == "create"} {
         #config the packet options
        if {[catch {::sth::sthCore::invoke stc::create ddOptions -under $handle} retPktOptHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retPktOptHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retPktOptHandle";
        }
        if {[info exists userArgsArray(ospf_packets_options)]} {
            ::sth::Traffic::processOspfv2BitOptionsList $retPktOptHandle pktOpt $userArgsArray(ospf_packets_options)
        }
        
        #config dd options
        if {[catch {::sth::sthCore::invoke stc::create ddSpecificOptions -under $handle} retDdOptHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retDdOptHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retDdOptHandle";
        }
        if {[info exists userArgsArray(ospf_dd_options)]} {
            ::sth::Traffic::processOspfv2BitOptionsList $retDdOptHandle ddOpt $userArgsArray(ospf_dd_options)
        }
    } else {
        if {[info exists userArgsArray(ospf_packets_options)]} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-ddOptions} retPktOptHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: $handle -children-ddOptions $retPktOptHandle"
                return $::sth::sthCore::FAILURE;
            } else {
                ::sth::sthCore::log info " $_procName: $handle -children-ddOptions $retPktOptHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retPktOptHandle pktOpt $userArgsArray(ospf_packets_options)
        }
        if {[info exists userArgsArray(ospf_dd_options)]} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-ddSpecificOptions} retDdOptHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: $handle -children-ddSpecificOptions $retDdOptHandle"
                return $::sth::sthCore::FAILURE;
            } else {
                ::sth::sthCore::log info " $_procName: $handle -children-ddSpecificOptions $retDdOptHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retDdOptHandle ddOpt $userArgsArray(ospf_dd_options)
        }
    }
    
    #modify the lsa handle
    if {$userArgsArray(mode) == "modify" && [regexp -nocase "Ospfv2LsaHeader" $handle]} {
        if {[catch {::sth::sthCore::invoke stc::config $handle $listName} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $errMsg"
            return -code error $trafficKeyedList
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success.";
        }
        if {[info exists userArgsArray(ospf_lsa_header_options)]} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-lsahdroptions} retOptionHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retOptionHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retOptionHeaderHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retOptionHeaderHandle lsaOpt $userArgsArray(ospf_lsa_header_options)
        }
    } elseif {[info exists userArgsArray(ospf_lsa_num)]} {
        #the lsa list will be created
        #1. if the "ospf_lsa_num" is configured in create mode
        #2. if the "ospf_lsa_num" is configured and the handle is "Ospfv2DatabaseDescription" in modify mode
        #get the seperate list from the parameter list
        set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_lsa_num) $listName 0]
        array set ospfLsaParamArray $ospfLsaParamList
        set ddLsaHdl ""
        for {set i 0} {$i<$userArgsArray(ospf_lsa_num)} {incr i} {
            if {[catch {::sth::sthCore::invoke stc::create lsaHeaders -under $handle} retLsaHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
            }
            
            if {[catch {::sth::sthCore::invoke stc::create Ospfv2LsaHeader -under $retLsaHeaderHandle $ospfLsaParamArray($i)} retHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
            }
            
            if {[catch {::sth::sthCore::invoke stc::create lsahdroptions -under $retHeaderHandle} retOptionHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retOptionHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retOptionHeaderHandle";
            }
           
            lappend ddLsaHdl $retHeaderHandle
            #config ospf_lsa_header_options
            if {[info exists userArgsArray(ospf_lsa_header_options)] && $i < [llength $userArgsArray(ospf_lsa_header_options)]} {
                ::sth::Traffic::processOspfv2BitOptionsList $retOptionHeaderHandle lsaOpt [lindex $userArgsArray(ospf_lsa_header_options) $i]
            }
        }
        ::sth::Traffic::processRetHandle dd_lsa_handle $ddLsaHdl
    }

}

#process ospfv2 hello packets
proc ::sth::Traffic::processOspfv2Hello {handle listName} {
    
    set _procName "processOspfv2Hello";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    #config the packet options
    if {$userArgsArray(mode) == "create"} {
        if {[catch {::sth::sthCore::invoke stc::create helloOptions -under $handle} retPktOptHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retPktOptHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retPktOptHandle";
        }
        if {[info exists userArgsArray(ospf_packets_options)]} {
            ::sth::Traffic::processOspfv2BitOptionsList $retPktOptHandle pktOpt $userArgsArray(ospf_packets_options)
        }
    } else {
        if {[info exists userArgsArray(ospf_packets_options)]} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-helloOptions} retPktOptHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retPktOptHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retPktOptHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retPktOptHandle pktOpt $userArgsArray(ospf_packets_options)
        }
    }
    
    #config neighbor id
    if {[info exists userArgsArray(ospf_neighbor_id)]} {
        # in modify mode, deleted the existed neighbors handle
        if {$userArgsArray(mode) == "modify"} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-neighbors} retNeighborHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retNeighborHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retNeighborHandle";
            }
            foreach neighborHdl $retNeighborHandle {
                if {[catch {::sth::sthCore::invoke stc::delete $neighborHdl} errMsg]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::delete Fail: $errMsg"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::delete Success.";
                }
            }
        }
        foreach neighborId $userArgsArray(ospf_neighbor_id) {
            if {[catch {::sth::sthCore::invoke stc::create neighbors -under $handle} retNeighborHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retNeighborHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retNeighborHandle";
            }
            if {[catch {::sth::sthCore::invoke stc::create Ospfv2Neighbor -under $retNeighborHandle "-neighborID $neighborId"} retHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
            }
        }
    }
    
}

#process ospfv2 link state acknowledge
proc ::sth::Traffic::processOspfv2LinkStateAcknowledge {handle listName} {
    
    set _procName "processOspfv2LinkStateAcknowledge";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    if {$userArgsArray(mode) == "modify" && [regexp -nocase "Ospfv2LsaHeader" $handle]} {
        #modify the ack lsa list
        if {[catch {::sth::sthCore::invoke stc::config $handle $listName} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
            return -code error $trafficKeyedList
        } else {
            ::sth::sthCore::log info " $_procName: stc::configNew Success.";
        }
        if {[info exists userArgsArray(ospf_lsa_header_options)]} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-lsahdroptions} retOptionHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retOptionHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retOptionHeaderHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retOptionHeaderHandle lsaOpt $userArgsArray(ospf_lsa_header_options)
        }
    } elseif {[info exists userArgsArray(ospf_lsa_num)]} {
        #the lsa list will be created
        #1. if the "ospf_lsa_num" is configured in create mode
        #2. if the "ospf_lsa_num" is configured and the handle is "Ospfv2LinkStateAcknowledge" in modify mode
        #get the seperate list from the parameter list
        set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_lsa_num) $listName 0]
        array set ospfLsaParamArray $ospfLsaParamList
        set ackLsaHdl ""
        for {set i 0} {$i<$userArgsArray(ospf_lsa_num)} {incr i} {
            if {[catch {::sth::sthCore::invoke stc::create lsaHeaders -under $handle} retLsaHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
            }
            
            if {[catch {::sth::sthCore::invoke stc::create Ospfv2LsaHeader -under $retLsaHeaderHandle $ospfLsaParamArray($i)} retHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
            }
            
            if {[catch {::sth::sthCore::invoke stc::create lsahdroptions -under $retHeaderHandle} retOptionHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retOptionHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retOptionHeaderHandle";
            }
            
            #config ospf_lsa_header_options
            if {[info exists userArgsArray(ospf_lsa_header_options)] && $i < [llength $userArgsArray(ospf_lsa_header_options)]} {
                ::sth::Traffic::processOspfv2BitOptionsList $retOptionHeaderHandle lsaOpt [lindex $userArgsArray(ospf_lsa_header_options) $i]
            }
            lappend ackLsaHdl $retHeaderHandle
        }
        ::sth::Traffic::processRetHandle ack_lsa_handle $ackLsaHdl
    }
}




#process ospfv2 link state request
proc ::sth::Traffic::processOspfv2LinkStateRequest {handle listName} {
    
    set _procName "processOspfv2LinkStateRequest";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    if {$userArgsArray(mode) == "modify" && [regexp -nocase "Ospfv2RequestedLsa" $handle]} {
        #modify the req lsa list
        #check if the input handle is reqlsa handle
        if {[catch {::sth::sthCore::invoke stc::config $handle $listName} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::configNew Success.";
        }
    } elseif {[info exists userArgsArray(ospf_req_lsa_num)]} {
        #the lsa list will be created
        #1. if the "ospf_req_lsa_num" is configured in create mode
        #2. if the "ospf_req_lsa_num" is configured and the handle is "Ospfv2LinkStateRequest" in modify mode
        #get the seperate list from the parameter list
        set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_req_lsa_num) $listName 0]
        array set ospfLsaParamArray $ospfLsaParamList
        set reqLsaHdl ""
        for {set i 0} {$i<$userArgsArray(ospf_req_lsa_num)} {incr i} {
            if {[catch {::sth::sthCore::invoke stc::create requestedLsas -under $handle} retLsaHeaderHandle]} {
               ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
               return -code error $trafficKeyedList 
            } else {
               ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
            }
           
            if {[catch {::sth::sthCore::invoke stc::create Ospfv2RequestedLsa -under $retLsaHeaderHandle $ospfLsaParamArray($i)} retHeaderHandle]} {
               ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
               return -code error $trafficKeyedList 
            } else {
               ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
            }
            lappend reqLsaHdl $retHeaderHandle
        }
        ::sth::Traffic::processRetHandle req_lsa_handle $reqLsaHdl
    }
    
}

#process ospfv2 link state update
proc ::sth::Traffic::processOspfv2LinkStateUpdate {handle listName} {
    
    set _procName "processOspfv2LinkStateUpdate";

    upvar userArgsArray userArgsArray;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    
    if {$userArgsArray(mode) == "modify" && ![regexp -nocase "Ospfv2LinkStateUpdate" $handle]} {
        switch -regexp $handle {
            "ospfv2routerlsa" {
                ::sth::Traffic::processOspfv2LinkStateUpdateRouterLsa $handle $listName 0 config
            }
            "ospfv2networklsa" {
                ::sth::Traffic::processOspfv2LinkStateUpdateNetworkLsa $handle $listName 0 config
            }
            "ospfv2summarylsa" {
                ::sth::Traffic::processOspfv2LinkStateUpdateSummaryLsa $handle $listName summaryLsa 0 config
            }
            "ospfv2summaryasbrlsa" {
                ::sth::Traffic::processOspfv2LinkStateUpdateSummaryLsa $handle $listName summaryAsbrLsa 0 config
            }
            "ospfv2asexternallsa" {
                ::sth::Traffic::processOspfv2LinkStateUpdateAsExternalLsa $handle $listName 0 config
            }
        }
    } else {
        #the lsa list will be created
        #1. if the "ospf_***_lsa_num" is configured in create mode
        #2. if the "ospf_***_lsa_num" is configured and the handle is not "Ospfv2LinkStateUpdate" in modify mode
        if {[info exists userArgsArray(ospf_router_lsa_num)]} {
            #get the seperate list from the parameter list
            set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_router_lsa_num) $listName 1]
            array set ospfLsaParamArray $ospfLsaParamList
            set updateRouterLsaHdl ""
            for {set i 0} {$i<$userArgsArray(ospf_router_lsa_num)} {incr i} {
                lappend updateRouterLsaHdl [::sth::Traffic::processOspfv2LinkStateUpdateRouterLsa $handle $ospfLsaParamArray($i) $i create]
            }
            ::sth::Traffic::processRetHandle update_router_lsa $updateRouterLsaHdl
        }
    
        if {[info exists userArgsArray(ospf_network_lsa_num)]} {
            #get the seperate list from the parameter list
            set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_network_lsa_num) $listName 1]
            array set ospfLsaParamArray $ospfLsaParamList
            set updateNetworkLsaHdl ""
            for {set i 0} {$i<$userArgsArray(ospf_network_lsa_num)} {incr i} {
                lappend updateNetworkLsaHdl [::sth::Traffic::processOspfv2LinkStateUpdateNetworkLsa $handle $ospfLsaParamArray($i) $i create]
            }
            ::sth::Traffic::processRetHandle update_network_lsa $updateNetworkLsaHdl
        }
    
        if {[info exists userArgsArray(ospf_summary_lsa_num)]} {
            #get the seperate list from the parameter list
            set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_summary_lsa_num) $listName 1]
            array set ospfLsaParamArray $ospfLsaParamList
            set updateSummaryLsaHdl ""
            for {set i 0} {$i<$userArgsArray(ospf_summary_lsa_num)} {incr i} {
                lappend updateSummaryLsaHdl [::sth::Traffic::processOspfv2LinkStateUpdateSummaryLsa $handle $ospfLsaParamArray($i) summaryLsa $i create]
            }
            ::sth::Traffic::processRetHandle update_summary_lsa $updateSummaryLsaHdl
        }
    
        if {[info exists userArgsArray(ospf_summaryasbr_lsa_num)]} {
            #get the seperate list from the parameter list
            set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_summaryasbr_lsa_num) $listName 1]
            array set ospfLsaParamArray $ospfLsaParamList
            set updateSummaryasbrLsaHdl ""
            for {set i 0} {$i<$userArgsArray(ospf_summaryasbr_lsa_num)} {incr i} {
                lappend updateSummaryasbrLsaHdl [::sth::Traffic::processOspfv2LinkStateUpdateSummaryLsa $handle $ospfLsaParamArray($i) summaryAsbrLsa $i create]
            }
            ::sth::Traffic::processRetHandle update_summaryasbr_lsa $updateSummaryasbrLsaHdl
        }
    
        if {[info exists userArgsArray(ospf_asexternal_lsa_num)]} {
            #get the seperate list from the parameter list
            set ospfLsaParamList [::sth::Traffic::processSplitList $userArgsArray(ospf_asexternal_lsa_num) $listName 1]
            array set ospfLsaParamArray $ospfLsaParamList
            set updateAsexternalLsaHdl ""
            for {set i 0} {$i<$userArgsArray(ospf_asexternal_lsa_num)} {incr i} {
                lappend updateAsexternalLsaHdl [::sth::Traffic::processOspfv2LinkStateUpdateAsExternalLsa $handle $ospfLsaParamArray($i) $i create]
            }
            ::sth::Traffic::processRetHandle update_asexternal_lsa $updateAsexternalLsaHdl
        }
    }

}
#process the router lsa of ospf link state update packets
proc ::sth::Traffic::processOspfv2LinkStateUpdateRouterLsa {handle paramList i mode} {
    
    set _procName "processOspfv2LinkStateUpdateRouterLsa";

    upvar userArgsArray userArgsArray;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    
    set paramLsaList ""
    set paramLsaHeaderList ""
    

    foreach {element attr value}  $paramList {
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_packets_stcobj($element)];
        switch -exact $stcObj {
            ospfv2RouterLsa {
                lappend  paramLsaList $attr $value;
            }
            ospfv2RouterLsa.Header {
                lappend  paramLsaHeaderList $attr $value;
            }
        }
    }
    
    if {$mode == "create"} {
        if {[catch {::sth::sthCore::invoke stc::create updatedLsas -under $handle} retLsaHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
        }
        
        if {[catch {::sth::sthCore::invoke stc::create Ospfv2Lsa -under $retLsaHeaderHandle} retHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
        }
        #create updated router lsa
        if {[catch {::sth::sthCore::invoke stc::create ospfv2RouterLsa -under $retHeaderHandle $paramLsaList} retRouterLsaHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retRouterLsaHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retRouterLsaHandle";
        }
        
        #process header under updated router lsa 
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $retRouterLsaHandle $paramLsaHeaderList routerLsa $i $mode
        
        #config the routerLsaOptions
        if {[catch {::sth::sthCore::invoke stc::create routerLsaOptions -under $retRouterLsaHandle} retRouterOptHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retRouterOptHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retRouterOptHandle";
        }
        
        if {[info exists userArgsArray(ospf_router_lsa_options)] && [lindex $userArgsArray(ospf_router_lsa_options) $i] !="" } {
            ::sth::Traffic::processOspfv2BitOptionsList $retRouterOptHandle routerLsaOpt [lindex $userArgsArray(ospf_router_lsa_options) $i]
        }
        return $retHeaderHandle
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $handle $paramLsaList} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::configNew Success.";
        }
        
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $handle $paramLsaHeaderList routerLsa $i $mode
    
        if {[info exists userArgsArray(ospf_router_lsa_options)]} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-routerLsaOptions} retOptHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::getFail: $retOptHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::getSuccess. Handle is $retOptHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retOptHandle routerLsaOpt $userArgsArray(ospf_router_lsa_options)
        }
    }

   
}

proc ::sth::Traffic::processOspfv2LinkStateUpdateNetworkLsa {handle paramList i mode} {
    
    set _procName "processOspfv2LinkStateUpdateNetworkLsa";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set paramLsaList ""
    set paramLsaHeaderList ""
    
    foreach {element attr value}  $paramList {
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_packets_stcobj($element)];
        switch -exact $stcObj {
            ospfv2NetworkLsa {
                lappend  paramLsaList $attr $value;
            }
            ospfv2NetworkLsa.Header {
                lappend  paramLsaHeaderList $attr $value;
            }
        }
    }
    #create updated network lsa
    if {$mode == "create"} {
        if {[catch {::sth::sthCore::invoke stc::create updatedLsas -under $handle} retLsaHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
        }
        
        if {[catch {::sth::sthCore::invoke stc::create Ospfv2Lsa -under $retLsaHeaderHandle} retHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
        }
        if {[catch {::sth::sthCore::invoke stc::create ospfv2NetworkLsa -under $retHeaderHandle $paramLsaList} retNetworkLsaHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retNetworkLsaHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retNetworkLsaHandle";
        }
        
        #process header under updated router lsa 
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $retNetworkLsaHandle $paramLsaHeaderList networkLsa $i $mode
        
        #config router id
        if {[info exists userArgsArray(ospf_network_lsa_attached_router_id)] && [lindex $userArgsArray(ospf_network_lsa_attached_router_id) $i] !="" } {
            foreach element [lindex $userArgsArray(ospf_network_lsa_attached_router_id) $i] {
                if {[catch {::sth::sthCore::invoke stc::create attachedRouters -under $retNetworkLsaHandle} retAttachedRoutersHandle]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retAttachedRoutersHandle"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retAttachedRoutersHandle";
                }
                if {[catch {::sth::sthCore::invoke stc::create Ospfv2AttachedRouter -under $retAttachedRoutersHandle "-routerID $element"} retHandle]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHandle"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
                }
            }
        }
        return $retHeaderHandle
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $handle $paramLsaList} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::configNew Success.";
        }
        
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $handle $paramLsaHeaderList networkLsa $i $mode
    
        if {[info exists userArgsArray(ospf_network_lsa_attached_router_id)]} {
            #delete the existed attached router handles
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-attachedRouters} retAttRouterHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::getFail: $retAttRouterHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::getSuccess. Handle is $retAttRouterHandle";
            }
            foreach hdl $retAttRouterHandle {
                if {[catch {::sth::sthCore::invoke stc::delete $hdl} errMsg]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::delete Fail: $errMsg"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::delete Success.";
                }
            }
            foreach element $userArgsArray(ospf_network_lsa_attached_router_id) {
                if {[catch {::sth::sthCore::invoke stc::create attachedRouters -under $handle} retAttachedRoutersHandle]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retAttachedRoutersHandle"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retAttachedRoutersHandle";
                }
                if {[catch {::sth::sthCore::invoke stc::create Ospfv2AttachedRouter -under $retAttachedRoutersHandle "-routerID $element"} retHandle]} {
                    ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHandle"
                    return -code error $trafficKeyedList 
                } else {
                    ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
                }
            }
        }
    }
}

#process ospfv2SummaryLsa and ospfv2SummaryAsbrLsa
proc ::sth::Traffic::processOspfv2LinkStateUpdateSummaryLsa {handle paramList type i mode} {
    
    set _procName "processOspfv2LinkStateUpdateSummaryLsa";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    
    set paramLsaList ""
    set paramLsaHeaderList ""
    set paramLsaTosMetric ""
    
    foreach {element attr value}  $paramList {
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_packets_stcobj($element)];
        switch -exact $stcObj {
            ospfv2SummaryLsa -
            ospfv2SummaryAsbrLsa {
                lappend  paramLsaList $attr $value;
            }
            ospfv2SummaryLsa.Header -
            ospfv2SummaryAsbrLsa.Header {
                lappend  paramLsaHeaderList $attr $value;
            }
        }
    }
    
    
    #create updated summary/summaryasbr lsa
    switch -- $type {
        summaryLsa {
            set obj ospfv2SummaryLsa
        }
        summaryAsbrLsa {
            set obj ospfv2SummaryAsbrLsa
        }
    }
    
    if {$mode == "create"} {
        if {[catch {::sth::sthCore::invoke stc::create updatedLsas -under $handle} retLsaHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
        }
        
        if {[catch {::sth::sthCore::invoke stc::create Ospfv2Lsa -under $retLsaHeaderHandle} retHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
        }
        if {[catch {::sth::sthCore::invoke stc::create $obj -under $retHeaderHandle $paramLsaList} retSummaryLsaHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retSummaryLsaHandle"
            return -code error $trafficKeyedList
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retSummaryLsaHandle";
        }
        #process header under updated router lsa 
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $retSummaryLsaHandle $paramLsaHeaderList $type $i $mode
        return $retHeaderHandle
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $handle $paramLsaList} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::configNew Success. Handle is $errMsg";
        }
        #process header under updated router lsa 
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $handle $paramLsaHeaderList $type $i $mode
    }
    
}

proc ::sth::Traffic::processOspfv2LinkStateUpdateAsExternalLsa {handle paramList i mode} {
    
    set _procName "processOspfv2LinkStateUpdateAsExternalLsa";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    
    set paramLsaList ""
    set paramLsaHeaderList ""
    set paramLsaOptions ""
    
    foreach {element attr value}  $paramList {
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_packets_stcobj($element)];
        switch -exact $stcObj {
            ospfv2AsExternalLsa {
                lappend  paramLsaList $attr $value;
            }
            ospfv2AsExternalLsa.Header {
                lappend  paramLsaHeaderList $attr $value;
            }
            externalLsaOptions {
                lappend  paramLsaOptions $attr $value;
            }
        }
    }

    
    #create updated asexternal lsa
    if {$mode == "create"} {
        if {[catch {::sth::sthCore::invoke stc::create updatedLsas -under $handle} retLsaHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaHeaderHandle";
        }
        
        if {[catch {::sth::sthCore::invoke stc::create Ospfv2Lsa -under $retLsaHeaderHandle} retHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHeaderHandle";
        }
        if {[catch {::sth::sthCore::invoke stc::create ospfv2AsExternalLsa -under $retHeaderHandle $paramLsaList} retAsExternalLsaHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retAsExternalLsaHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retAsExternalLsaHandle";
        }
    
        #process header under updated asexternal lsa 
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $retAsExternalLsaHandle $paramLsaHeaderList asExternalLsa $i $mode
        #process externalLsaOptions
        if {[catch {::sth::sthCore::invoke stc::create externalLsaOptions -under $retAsExternalLsaHandle $paramLsaOptions} retHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retHandle";
        }
        return $retHeaderHandle
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $handle $paramLsaList} errMsg]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::configNew Success. Handle is $errMsg";
        }
    
        #process header under updated router lsa 
        ::sth::Traffic::processOspfv2UpdatedLsaHeader $handle $paramLsaHeaderList asExternalLsa $i $mode
        if {$paramLsaOptions != "" } {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-externalLsaOptions} retHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::get Fail: $retHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::get Success. Handle is $retHandle";
            }
            if {[catch {::sth::sthCore::invoke stc::config $retHandle $paramLsaOptions} errMsg]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::configNew Fail: $errMsg"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::configNew Success. Handle is $errMsg";
            }
        }
        
    }
}

proc ::sth::Traffic::processOspfv2UpdatedLsaHeader {handle valueList type i mode} {

    set _procName "processOspfv2UpdatedLsaHeader";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    switch -regexp $type {
        routerLsa {
            set optionParam  ospf_router_lsa_header_options
        }
        networkLsa {
            set optionParam  ospf_network_lsa_header_options
        }
        summaryLsa {
            set optionParam  ospf_summary_lsa_header_options
        }
        summaryAsbrLsa {
            set optionParam  ospf_summaryasbr_lsa_header_options
        }
        asExternalLsa {
            set optionParam  ospf_asexternal_lsa_header_options
        }
        
    }

    #create header
    if {$mode == "create"} {
        if {[catch {::sth::sthCore::invoke stc::create header -under $handle $valueList} retRouterLsaHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retRouterLsaHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retRouterLsaHeaderHandle";
        }
        #create the lsahdroptions header
        if {[catch {::sth::sthCore::invoke stc::create lsaHdrOptions -under $retRouterLsaHeaderHandle} retOptionHeaderHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retOptionHeaderHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retOptionHeaderHandle";
        }
        #config ospf_lsa_header_options
        #get the header options from $valueList
        if {[info exists userArgsArray($optionParam)] && [lindex $userArgsArray($optionParam) $i] !="" } {
            ::sth::Traffic::processOspfv2BitOptionsList $retOptionHeaderHandle lsaOpt [lindex $userArgsArray($optionParam) $i]
        }
    } else {
        if {[info exists userArgsArray($optionParam)] || $valueList != ""} {
            if {[catch {::sth::sthCore::invoke stc::get $handle -children-header} retHeaderHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::getFail: $retHeaderHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::getSuccess. Handle is $retHeaderHandle";
            }
        }
        if {$valueList != ""} {
            if {[catch {::sth::sthCore::invoke stc::config $retHeaderHandle $valueList} errMsg]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::config Fail: $errMsg"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::config Success.";
            }
        }
        if {[info exists userArgsArray($optionParam)]} {
            if {[catch {::sth::sthCore::invoke stc::get $retHeaderHandle -children-lsaHdrOptions} retOptHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::config Fail: $retOptHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::config Success. Handle is $retOptHandle";
            }
            ::sth::Traffic::processOspfv2BitOptionsList $retOptHandle lsaOpt $userArgsArray($optionParam)
        }
    }
}


proc ::sth::Traffic::processOspfv2UpdateRouterLsaLink {type} {
    
    set _procName "processOspfv2UpdateRouterLsaLink";

    upvar userArgsArray userArgsArray;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    
    set paramLsaList ""
    set paramLsaLinksList ""
    

    if {![info exists userArgsArray(ospf_router_lsa_link_num)] || $userArgsArray(mode) == "modify"} {
        set lsaNum 1
    } else {
        set lsaNum $userArgsArray(ospf_router_lsa_link_num)
    }

    foreach elementPair $prioritisedAttributeList {
        set element [lindex $elementPair 1]
        set stcAttr [set ::$mns\::traffic_config_ospf_$type\_stcattr($element)];
        ::sth::sthCore::log info " $_procName HLT: $element \t STC: $stcAttr"
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_$type\_stcobj($element)];
        switch -exact $stcObj {
            Ospfv2RouterLsaLink {
                lappend  paramLsaLinksList -$stcAttr $userArgsArray($element);
            }
        }
    }
    
            
    if {$userArgsArray(mode) == "create"} {
        #create updated router lsa
        set ospfLsaParamList [::sth::Traffic::processSplitList $lsaNum $paramLsaLinksList 0]
        array set ospfLsaParamArray $ospfLsaParamList
        set LsaListHdl ""
        for {set i 0} {$i<$lsaNum} {incr i} {
            if {[catch {::sth::sthCore::invoke stc::create routerLsaLinks -under $userArgsArray(phandle)} retLsaLinksHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaLinksHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaLinksHandle";
            }
            
            if {[catch {::sth::sthCore::invoke stc::create Ospfv2RouterLsaLink -under $retLsaLinksHandle $ospfLsaParamArray($i)} retRouterLsaLinkHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retRouterLsaLinkHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retRouterLsaLinkHandle";
            }
            lappend LsaListHdl $retRouterLsaLinkHandle
        }
        ::sth::Traffic::processRetHandle router_lsa_link_handle $LsaListHdl
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $userArgsArray(handle) $paramLsaLinksList} retRouterLsaLinkHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retRouterLsaLinkHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retRouterLsaLinkHandle";
        }
    }
}

proc ::sth::Traffic::processOspfv2UpdateLsaTos {type} {
    
    set _procName "processOspfv2UpdateRouterLsaTos";

    upvar userArgsArray userArgsArray;
    upvar prioritisedAttributeList prioritisedAttributeList;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;

    set paramLsaTosMetric ""
    
    switch -regexp $type {
        "update_router_lsa_tos" {
            set numAttr "ospf_router_lsa_tos_num"
            set stcObject "Ospfv2RouterLsaTosMetric"
            set obj1 "routerLsaTosMetrics"
            set obj2 "Ospfv2RouterLsaTosMetric"
            set retHdl "router_lsa_tos_handle"
        }
        "update_summary_lsa_tos" {
            set numAttr "ospf_summary_lsa_tos_num"
            set stcObject "Ospfv2SummaryLsaTosMetric"
            set obj1 "summaryAdditionalMetrics"
            set obj2 "Ospfv2SummaryLsaTosMetric"
            set retHdl "summary_lsa_tos_handle"
        }
        "update_asexternal_lsa_tos" {
            set numAttr "ospf_asexternal_lsa_tos_num"
            set stcObject "Ospfv2ExternalLsaTosMetric"
            set obj1 "externalAdditionalMetrics"
            set obj2 "Ospfv2ExternalLsaTosMetric"
            set retHdl "asexternal_lsa_tos_handle"
        }
    }
    
    if {![info exists userArgsArray($numAttr)] || $userArgsArray(mode) == "modify"} {
        set lsaNum 1
    } else {
        set lsaNum $userArgsArray($numAttr)
    }

    foreach elementPair $prioritisedAttributeList {
        set element [lindex $elementPair 1]
        set stcAttr [set ::$mns\::traffic_config_ospf_$type\_stcattr($element)];
        ::sth::sthCore::log info " $_procName HLT: $element \t STC: $stcAttr"
        #seperate the elements into differet list accoring to its stcobj
        set stcObj [set ::$mns\::traffic_config_ospf_$type\_stcobj($element)];
        if {[regexp -nocase $stcObject $stcObj]} {
            lappend  paramLsaTosMetric -$stcAttr $userArgsArray($element);
        }
    }
    
    if {$userArgsArray(mode) == "create"} {
        set ospfLsaTosParamList [::sth::Traffic::processSplitList $lsaNum $paramLsaTosMetric 0]
        array set ospfLsaParamTosArray $ospfLsaTosParamList
        set lsaTosHdl ""
        for {set i 0} {$i<$lsaNum} {incr i} {
            if {[catch {::sth::sthCore::invoke stc::create $obj1 -under $userArgsArray(phandle)} retLsaTosHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaTosHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaTosHandle";
            }
            if {[catch {::sth::sthCore::invoke stc::create $obj2 -under $retLsaTosHandle $ospfLsaParamTosArray($i)} reHandle]} {
                ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $reHandle"
                return -code error $trafficKeyedList 
            } else {
                ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $reHandle";
            }
            lappend lsaTosHdl $reHandle
        }
        ::sth::Traffic::processRetHandle $retHdl $lsaTosHdl
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $userArgsArray(handle) $paramLsaTosMetric} retLsaLinkHandle]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::create Fail: $retLsaLinkHandle"
            return -code error $trafficKeyedList 
        } else {
            ::sth::sthCore::log info " $_procName: stc::create Success. Handle is $retLsaLinkHandle";
        }
    }
}




proc ::sth::Traffic::processOspfv2BitOptionsList {handle optionTyp valueList} {

    set _procName "processOspfv2BitOptionsList";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    
    set configList ""
    set p 0
    
    switch -regexp $optionTyp {
        "lsaOpt" -
        "pktOpt" {
            set attrList "-reserved7 -reserved6 -dcBit -eaBit -npBit -mcBit -eBit -reserved0"
        }
        "ddOpt" {
            set attrList "-reserved7 -reserved6 -reserved5 -reserved4 -reserved3 -iBit -mBit -msBit"
        }
        "routerLsaOpt" {
            set attrList "-reserved7 -reserved6 -reserved5 -reserved4 -reserved3 -vBit -eBit -bBit"
        }
    }
    
    foreach attr $attrList {
        #get the bit value
        set value [string range $valueList $p $p]
        lappend configList $attr $value
        incr p
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $handle $configList} err]} {
        ::sth::sthCore::processError trafficKeyedList " $_procName: stc::config Fail: $err"
        return -code error $trafficKeyedList
    }
}

#process the list input
proc ::sth::Traffic::processSplitList {num paramList element} {

    set _procName "processSplitList";

    upvar userArgsArray userArgsArray;
    upvar trafficKeyedList trafficKeyedList;
    upvar mns mns;
    array set retParam {};
    
    for {set i 0} {$i<$num} {incr i} {
        set elemList ""
        switch -- $element {
            0 {
                foreach {attr val} $paramList {
                    #if the customer doesn't input the same number of element as the number, we will provide the default value
                    if {$i < [llength $val]} {
                        lappend elemList $attr [lindex $val $i]
                    }
                }
            }
            1 {
                foreach {elem attr val} $paramList {
                    #if the customer doesn't input the same number of element as the number, we will provide the default value
                    if {$i < [llength $val]} {
                        lappend elemList $elem $attr [lindex $val $i]
                    }
                }
            }
        }
       
        set retParam($i) $elemList
    }
    
    set retList ""
    set retList [array get retParam]
    return  $retList
}

proc ::sth::Traffic::processRetHandle {handleTyp hdlList} {
    
    set _procName "processRetHandle";
    
    upvar trafficKeyedList trafficKeyedList;
    set retHdlList ""
    foreach handle $hdlList {
        if {[catch {::sth::sthCore::invoke stc::get $handle -name} retName]} {
            ::sth::sthCore::processError trafficKeyedList " $_procName: stc::getFail: $retName"
            return -code error $trafficKeyedList 
        }
        set retHandle $handle\_$retName
        lappend retHdlList $retHandle
    }
    
    keylset trafficKeyedList $handleTyp $retHdlList
    
}

#update the input handle in case the handle changes after applying.
proc ::sth::Traffic::processUpdateHandle {strblkHdl handle} {
    
    set _procName "processUpdateHandle";
    
    #1. get the name of the hanlde
    set n [string first "_" $handle]
    if {$n >= 0} {
        #name is appended after the original handle
        set hdl [string range $handle 0 [expr $n - 1]]
        set nameHdl [string replace $handle 0 $n ""]
    }

    #2. get the update handle by checking PduInfo, the updated handle value follows after handle name
    set pduInfo [::sth::sthCore::invoke stc::get $strblkHdl -PduInfo]
    if {[regexp -nocase $nameHdl $pduInfo]} {
        foreach element $pduInfo {
            set nameIndex [string first $nameHdl $element]
            if {$nameIndex >=0} {
                set updateList [split $element ,]
                set updateHdl [lindex $updateList 1]
                break
            }
        }
    } else {
        #the handle will not change on offline test OR no apply command is called
        set updateHdl $hdl
    }
    
    #return update handle
    return $updateHdl
    
}
