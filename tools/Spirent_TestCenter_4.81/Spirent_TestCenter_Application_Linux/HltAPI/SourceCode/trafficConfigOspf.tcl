# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Traffic:: {
}


proc ::sth::traffic_config_ospf { args } {
    ::sth::sthCore::Tracker ::sth::traffic_config_ospf $args
    set mns "sth::Traffic";
    variable ::sth::Traffic::prioritisedAttributeList
    variable ::sth::Traffic::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}

    set trafficKeyedList ""

    #get the type
    if {[regexp {\-type} $args]} {
        set indx [lsearch $args -type]
        set type [lindex $args [expr {$indx + 1}]]
    }
    
    if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficOspfTable $args \
							::sth::Traffic:: \
                                                        traffic_config_ospf_$type\
							::sth::Traffic::userArgsArray \
							::sth::Traffic::prioritisedAttributeList} eMsg]} {
	::sth::sthCore::processError trafficKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg"
	return $trafficKeyedList
    }                 
    
    switch -- $type {
        "packets" {
            set processFunction "processCreateOspfHeader"
	    if {[info exists userArgsArray(ospf_type)]} {
                set type $userArgsArray(ospf_type)
	    } else {
		set errMsg "\"ospf_type\" is mandatory when \"type\" is configured as \"packets\"\n";
		::sth::sthCore::processError trafficKeyedList $errMsg {}
                return -code 1 -errorcode -1 $errMsg;
	    }
            set paramCheck "stream_id"
        }
        "update_router_lsa_link" {
            set processFunction "processOspfv2UpdateRouterLsaLink"
            set paramCheck "phandle"
        }
        "update_router_lsa_tos" -
	"update_summary_lsa_tos" -
	"update_asexternal_lsa_tos" {
            set processFunction "processOspfv2UpdateLsaTos"
            set paramCheck "phandle"
        }
    }
    
    #update the hanlde in case the handle changes when apply is called
    if {[catch {
        if {[info exists userArgsArray(handle)] || [info exists userArgsArray(phandle)]} {
            if {[info exists userArgsArray(handle)]} {set typ "handle"}
            if {[info exists userArgsArray(phandle)]} {set typ "phandle"}
            
            set updatehdl [::sth::Traffic::processUpdateHandle $userArgsArray(stream_id) $userArgsArray($typ)]
            
            regsub -all {\d+$} $updatehdl "" objectName
            if {[string match -nocase "ospfv2lsa" $objectName]} {
                #only used for update ospf header
                set userArgsArray($typ) [::sth::sthCore::invoke stc::get $updatehdl -children]
            } else {
                set userArgsArray($typ) $updatehdl
            }
        }
    } errMsg]} {
        ::sth::sthCore::processError trafficKeyedList "internal operation failed. $errMsg";
        return -code error $trafficKeyedList 
    }
    
    set mode $userArgsArray(mode)
    if {$mode == "delete"} {
        if {[info exists userArgsArray(handle)]} {
            set hdlList $userArgsArray(handle)
            foreach hdl $hdlList {
                if {[catch {::sth::sthCore::invoke stc::delete $hdl} errMsg]} {
                    ::sth::sthCore::processError trafficKeyedList "internal operation failed. $errMsg";
                    return -code error $trafficKeyedList 
                } else {
                    keylset trafficKeyedList status $::sth::sthCore::SUCCESS;
                }
            }
        } else {
            set errMsg "\"handle\" is mandatory in \"delete\" mode\n";
	    ::sth::sthCore::processError trafficKeyedList $errMsg {}
            return -code 1 -errorcode -1 $errMsg;
        }
        
    } else {
        #check if the stream id is configured in create mode
        if {$mode == "create"} {
	    if {$userArgsArray(type) == "packets"} {
		# check if the l4_protocol is configured as "ospf" in traffic_config function
		if {[info exists ::$mns\::arrayHeaderTypesInCreate(l4_protocol)] && [set ::$mns\::arrayHeaderTypesInCreate(l4_protocol)] == "ospf"} {
		    ::sth::sthCore::log info "\[Traffic\] \"l4_protocol\" has been configured as \"ospf\"\n";
		} else {
		    set errMsg "\[Traffic\] \"l4_protocol\" in traffic_config function must be configured as \"ospf\" before calling traffic_config_ospf function\n";
		    ::sth::sthCore::processError trafficKeyedList $errMsg {}
		    return -code 1 -errorcode -1 $errMsg;
		}
	    }
	    if {![info exists userArgsArray($paramCheck)]} {
		set errMsg "\"$paramCheck\" is mandatory in \"create\" mode when \"type\" is configured as \"$userArgsArray(type)\"\n";
		::sth::sthCore::processError trafficKeyedList $errMsg {}
		return -code 1 -errorcode -1 $errMsg;
	    }
        }
        #check if the handle is configured in modify mode
        if {$mode == "modify"} {
            if {![info exists userArgsArray(handle)]} {
		::sth::sthCore::processError trafficKeyedList $errMsg {}
                return -code 1 -errorcode -1 $errMsg;
            }
        }
        
        if {[catch {::sth::Traffic::$processFunction $type} errMsg]} {
	    ::sth::sthCore::processError trafficKeyedList "internal operation failed. $errMsg" {}
            return -code 1 -errorcode -1 $errMsg;
        } else {
            keylset trafficKeyedList status $::sth::sthCore::SUCCESS;
        }
    }
	
    
    if {[catch {::sth::sthCore::doStcApply} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $procName: Error while applying configuration: $err" {}
	return -code error $returnKeyedList  
    }
	
    return $trafficKeyedList
}
