# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# This file now has all the doStc procs.
# They have been removed from the sthUtils.tcl file.
# As of now, since some parts of the code are working on the old format and some on the new format,
# this file has two sets of functions.
# For now, to remove conflict, there is a "new" tag appened to those procs that are in conflict.
# Thus down the line we should be able to globally remove the "new" tag, once everyone moves to the new code.

# CREATED: 10/23/06



# NAME: doStcCreateNew
# INPUT: object parentHandle dashedAttrValuePairs
# OUTPUT:
#	Success: Created Handle
#	Failure: exception with failure Status
# SAMPLE:
#	Use catch here to catch any error condition
#	set porthnd [::sth::sthCore::doStcCreate Port $project1 "-name abc -location //$chassisAddress/$TxSlot/$TxPort"]

proc ::sth::sthCore::doStcCreateNew {object parentHandle {dashedAttrValuePairs {}}} {
	
	# We would have to go the eval way to be able to set the attributes propoerly down. 	
	set cmd "::stc::create $object -under $parentHandle $dashedAttrValuePairs";
	
	########### log stccall ###########
	::sth::sthCore::log stccall $cmd;
	
	if {[catch {eval $cmd} createStatus ]} {
		::sth::sthCore::log debug "\[doStcCreate\] $cmd FAILED. $createStatus";
		return -code 1 -errorcode -1 $createStatus;
	} else {
		::sth::sthCore::log info "\[doStcCreate\] $cmd PASSED. $createStatus";
		return $createStatus;
	}
}

# NAME: doStcGet
# INPUT: objHandle dashedAttribute
# OUTPUT:
#	Success: Returned value from ::stc::get call
#	Failure: exception with failure Status
# SAMPLE:
#	Use catch here to catch any error condition
#	set generator1 [::sth::sthCore::doStcGet $port1 -children-Generator]

proc ::sth::sthCore::doStcGetNew {objHandle {dashedAttribute {}}} {
        
        
	########### log stccall ###########
	::sth::sthCore::log stccall "::stc::get $objHandle $dashedAttribute";
        if {[llength $dashedAttribute] == 0} {
                set cmd "::stc::get $objHandle" 
        } else {
                set cmd "::stc::get $objHandle $dashedAttribute" 
        }

	if {[catch {eval $cmd} getStatus ]} {
		::sth::sthCore::log debug "\[doStcGet\] ::stc::get $objHandle $dashedAttribute FAILED. $getStatus";
		return -code 1 -errorcode -1 $getStatus;
	} else {
		::sth::sthCore::log info "\[doStcGet\] ::stc::get $objHandle $dashedAttribute PASSED. $getStatus";
		return $getStatus;
	}
}

# NAME: doStcConfig
# INPUT: objHandle dashedAttrValuePairs
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	set myList {	-DurationMode "CONTINUOUS" \
#			-Duration "1000" \
#			-TimestampLatchMode "END_OF_FRAME" \
#			-RandomLengthSeed "2" \
#			-JumboFrameThreshold "1500"}
#
#	Use catch here to catch any error condition
#	::sth::sthCore::doStcConfig $generatorConfig1 $myList

proc ::sth::sthCore::doStcConfigNew {objHandle dashedAttrValuePairs} {
	
	# We would have to go the eval way to be able to set the attributes propoerly down. 	
	set cmd "::stc::config $objHandle $dashedAttrValuePairs";
	
	########### log stccall ###########
	::sth::sthCore::log stccall $cmd;
	
	if {[catch {eval $cmd} configStatus ]} {
		::sth::sthCore::log debug "\[doStcConfig\] $cmd FAILED. $configStatus";
		return -code 1 -errorcode -1 $configStatus;
	} else {
		::sth::sthCore::log info "\[doStcConfig\] $cmd PASSED. $configStatus";
		return $::sth::sthCore::SUCCESS;
	}
}

proc ::sth::sthCore::doStcCreateDevice {portHandle parentHandle handleName ifStack ifCount {type Router}} {
	# Currently, a router/host is created directly under a project, and affiliates with a port.
	
	upvar 1 $handleName returnHandle
	set stcCmd {array set DeviceCreateOutput [stc::perform DeviceCreate \
					  -ParentList $parentHandle \
					  -DeviceType $type \
					  -IfStack $ifStack \
					  -IfCount $ifCount \
					  -Port $portHandle]}
	
	########### log stccall ###########
	::sth::sthCore::log stccall $stcCmd;

	if {[catch {eval $stcCmd} createStatus ]} {
		::sth::sthCore::log debug "\[doStcCreateDevice\] $stcCmd FAILED. $createStatus";
		return -code 1 -errorcode -1 $createStatus;
	} else {
		::sth::sthCore::log info "\[doStcCreateDevice\] $stcCmd PASSED. $createStatus";
		set returnHandle $DeviceCreateOutput(-ReturnList);
		return $::sth::sthCore::SUCCESS;
	}
	
}

proc ::sth::sthCore::doStcProtocolCreate {protocolType parentHandle handleName} {
	# Currently, a protocol is created directly under a router.
	
	upvar 1 $handleName returnHandle;
	set stcCmd {array set ProtocolCreateOutput [stc::perform ProtocolCreate \
					  -ParentList $parentHandle \
					  -CreateClassId [string tolower $protocolType]]}

	
	########### log stccall ###########
	::sth::sthCore::log stccall $stcCmd;

	if {[catch {eval $stcCmd} createStatus ]} {
		::sth::sthCore::log debug "\[doStcProtocolCreate\] $stcCmd FAILED. $createStatus";
		return -code 1 -errorcode -1 $createStatus;
	} else {
		::sth::sthCore::log info "\[doStcProtocolCreate\] $stcCmd PASSED. $createStatus";
		set returnHandle $ProtocolCreateOutput(-ReturnList);
		return $::sth::sthCore::SUCCESS;
	}
}

# NAME: doStcApply
# INPUT: 
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	Use catch here to catch any error condition
#	sthCore::doStcApply

proc ::sth::sthCore::doStcApply {} {

    if {!$::sth::sthCore::optimization} {
	########### log stccall ###########
	::sth::sthCore::log stccall "::stc::apply";

	if {[catch {::stc::apply} applyStatus ]} {
		::sth::sthCore::log debug "\[doStcApply\] ::stc::apply FAILED. $applyStatus";
		return -code 1 -errorcode -1 $applyStatus;
	} else {
		::sth::sthCore::log info "\[doStcApply\] ::stc::apply PASSED. $applyStatus";
		return $::sth::sthCore::SUCCESS;
	}
    }
}

# NAME: doStcApplyExplicit
# INPUT: 
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	Use catch here to catch any error condition
#	sthCore::doStcApplyExplicit

proc ::sth::sthCore::doStcApplyExplicit {} {

	########### log stccall ###########
	::sth::sthCore::log info "#Explicit call to ::stc::apply"
	::sth::sthCore::log stccall "::stc::apply";

	if {[catch {::stc::apply} applyStatus ]} {
		::sth::sthCore::log debug "\[doStcApply\] ::stc::apply FAILED. $applyStatus";
		return -code 1 -errorcode -1 $applyStatus;
	} else {
		::sth::sthCore::log info "\[doStcApply\] ::stc::apply PASSED. $applyStatus";
		return $::sth::sthCore::SUCCESS;
	}
}

# NAME: doStcDelete
# INPUT: objHandle
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	Use catch here to catch any error condition
#	::sth::sthCore::doStcDelete $ospfHandle

proc ::sth::sthCore::doStcDelete {objHandle} {
	
	########### log stccall ###########
	::sth::sthCore::log stccall "::stc::delete $objHandle";

	if {[catch {::stc::delete $objHandle} deleteStatus ]} {
		::sth::sthCore::log debug "\[doStcDelete\] ::stc::delete $objHandle FAILED. $deleteStatus";
		return -code 1 -errorcode -1 $deleteStatus;
	} else {
		::sth::sthCore::log info "\[doStcDelete\] ::stc::delete $objHandle PASSED. $deleteStatus";
		return $::sth::sthCore::SUCCESS;
	}
}

# NAME: doStcReserve
# INPUT: chassisSlotPort
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	::sth::sthCore::doStcReserve 10.100.20.56/1/2

proc ::sth::sthCore::doStcReserve { chassisSlotPort } {

	########### log stccall ###########
	::sth::sthCore::log stccall "stclib::bll::reserve $chassisSlotPort"
	
	if {[catch {stclib::bll::reserve $chassisSlotPort} reserveStatus ]} {
		::sth::sthCore::log debug "\[doStcReserve\] stclib::bll::reserve $chassisSlotPort FAILED. $reserveStatus";
		return -code 1 -errorcode -1 $reserveStatus;
	} else {
		::sth::sthCore::log info "\[doStcReserve\] stclib::bll::reserve $chassisSlotPort PASSED. $reserveStatus";
		return $::sth::sthCore::SUCCESS
	}
}

# NAME: doStcRelease
# INPUT: chassisSlotPort
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	::sth::sthCore::doStcRelease 10.100.20.56/1/2

proc ::sth::sthCore::doStcRelease { chassisSlotPort } {
		
	########### log stccall ###########
	::sth::sthCore::log stccall "stclib::bll::release $chassisSlotPort"
	
	if {[catch {stclib::bll::release $chassisSlotPort} releaseStatus ]} {
		::sth::sthCore::log debug "\[doStcRelease\] stclib::bll::release $chassisSlotPort FAILED. $releaseStatus";
		return -code 1 -errorcode -1 $releaseStatus;
	} else {
		::sth::sthCore::log info "\[doStcRelease\] stclib::bll::release $chassisSlotPort PASSED. $releaseStatus";
		return $::sth::sthCore::SUCCESS
	}
}

# NAME: doStcDisconnect
# INPUT: chassisId
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	

proc ::sth::sthCore::doStcDisconnect { chassisId } {
		
	########### log stccall ###########
	::sth::sthCore::log stccall "::stc::disconnect $chassisId"

	if {[catch {::stc::disconnect $chassisId} disconnectStatus ]} {
		::sth::sthCore::log debug "\[doStcDisconnect\] ::stc::disconnect $chassisId FAILED. $disconnectStatus";
		return -code 1 -errorcode -1 $disconnectStatus;
	} else {
		::sth::sthCore::log info "\[doStcDisconnect\] ::stc::disconnect $chassisId PASSED. $disconnectStatus";
		return $::sth::sthCore::SUCCESS
	}
}

# NAME: doStcPerform
# INPUT: operation dashedAttrValuePairs
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	::sth::sthCore::doStcPerform ProtocolStop -ProtocolList \{$normalRestartSessionList\}

proc ::sth::sthCore::doStcPerform {operation args} {
	
	set dashedAttrValuePairs [lrange $args 0 end];
	set performCmd "stc::perform $operation $dashedAttrValuePairs";

	########### log stccall ###########
	::sth::sthCore::log stccall $performCmd;

	if {[catch {eval $performCmd} performStatus ]} {
		::sth::sthCore::log debug "\[doStcPerform\] $performCmd FAILED. $performStatus";
		return -code 1 -errorcode -1 $performStatus;
	} else {
		::sth::sthCore::log info "\[doStcPerform\] $performCmd PASSED. $performStatus";
		return $performStatus;
	}	
}

proc ::sth::sthCore::doStcUnSubscribe {resultDataSet} {
	
	set unSubscribeCmd "stc::unsubscribe $resultDataSet"
	########### log stccall ###########
	::sth::sthCore::log stccall $unSubscribeCmd;

	if {[catch {eval $unSubscribeCmd} unSubscribeStatus ]} {
		::sth::sthCore::log debug "\[doStcUnSubscribe] $unSubscribeCmd FAILED. $unSubscribeStatus";
		return -code 1 -errorcode -1 $unSubscribeStatus;
	} else {
		::sth::sthCore::log info "\[doStcUnSubscribe\] $unSubscribeCmd PASSED. $unSubscribeStatus";
		return $unSubscribeStatus;
	}	
}

proc ::sth::sthCore::doStcSubscribe {dashedAttrValuePairs} {
	
	set subscribeCmd "stc::subscribe $dashedAttrValuePairs"
	########### log stccall ###########
	::sth::sthCore::log stccall $subscribeCmd;

	if {[catch {eval $subscribeCmd} subscribeStatus ]} {
		::sth::sthCore::log debug "\[doStcSubscribe] $subscribeCmd FAILED. $subscribeStatus";
		return -code 1 -errorcode -1 $subscribeStatus;
	} else {
		::sth::sthCore::log info "\[doStcSubscribe\] $subscribeCmd PASSED. $subscribeStatus";
		return $subscribeStatus;
	}	
}
# NAME: doStcSleep
# INPUT: sleepTime
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	::sth::sthCore::doStcSleep 10

proc ::sth::sthCore::doStcSleep { sleepTime } {
	
	########### log stccall ###########
	::sth::sthCore::log stccall "::stc::sleep $sleepTime"

	if {[catch {::stc::sleep $sleepTime} sleepStatus ]} {
		::sth::sthCore::log debug "\[doStcSleep\] ::stc::sleep $sleepTime FAILED. $sleepStatus";
		return -code 1 -errorcode -1 $sleepStatus;
	} else {
		::sth::sthCore::log info "\[doStcSleep\] ::stc::sleep $sleepTime PASSED. $sleepStatus";
		return $::sth::sthCore::SUCCESS
	}
}

# NAME: doStcConnect
# INPUT: chassisIp
# OUTPUT:
#	Success: ::sth::sthCore::SUCCESS
#	Failure: exception with failure Status
# SAMPLE:
#	::sth::sthCore::doStcConnect 10.100.20.56

proc ::sth::sthCore::doStcConnect { chassisIp } {
	
	########### log stccall ###########
	::sth::sthCore::log stccall "::stc::connect $chassisIp"

	if {[catch {::stc::connect $chassisIp } connectStatus ]} {
		::sth::sthCore::log debug "\[doStcConnect\] ::stc::connect $chassisIp FAILED. $connectStatus";
		return -code 1 -errorcode -1 $connectStatus;
	} else {
		::sth::sthCore::log info "\[doStcConnect\] ::stc::connect $chassisIp PASSED. $connectStatus";
		return $::sth::sthCore::SUCCESS;
	}
}

#################
# Old Functions still there for backward compatibility.
# This Function should be removed down the line and, 
# everyone should move to *new functions.
# Then the *new functions will be renamed and the old functions will be deleted. 
#################

proc ::sth::sthCore::doStcCreate { args } {
		
	set objectName [lindex $args 0]
	set parentHandle [lindex $args 1]
	set handleName [lindex $args 2]
	set attributeValuePairs [lindex $args 3]
	
	upvar 1 $handleName returnHandle
	
	if {[string equal $objectName "project"]} {
	    ::sth::sthCore::log info "{stc::create: Trying to call StcCreate to create object:$objectName}"
	    set stcCmd "::stc::create $objectName"
	    upvar $parentHandle returnHandle
	} else {
	    ::sth::sthCore::log info "{stc::create: Trying to call StcCreate to create object:$objectName under parent:$parentHandle with attributes:$attributeValuePairs}"
	    set stcCmd "::stc::create $objectName -under $parentHandle $attributeValuePairs"
	}

	########### log stccall ###########
	::sth::sthCore::log stccall $stcCmd

	if {[catch {eval $stcCmd} createStatus ]} {
		::sth::sthCore::log error "{stc::create: Internal Command Error: $createStatus}"
		set cmdFailed 1		
	} else {
		::sth::sthCore::log debug "{The object:$objectName was successfully created under parentHandle:$parentHandle with handle:$createStatus}"
		set returnHandle $createStatus
		return $sth::sthCore::SUCCESS
	}
		
	if {[info exists cmdFailed]} {
			return -code 1 -errorcode -1 $createStatus
	}
}

proc ::sth::sthCore::doStcGet { args } {
	
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	set attr [lindex $args 0]
	set handle [lindex $args 1]
	set varName [lindex $args 2]

	upvar 1 $varName getValue

	if {[string index $attr 0]!= "-"} {
		set attr "-$attr"
	}
	sth::sthCore::log info "Trying to call StcGet for handle:$handle Attribute:$attr "
	set evalCmd "stc::get $handle $attr"

	########### log stccall ###########
	::sth::sthCore::log stccall $evalCmd
	
	if {[catch {eval $evalCmd} getStatus ]} {
		regsub -all {\n} $getStatus ";#" getStatus
		sth::sthCore::log debug "Unable to get value for attribute:$attr from handle:$handle. Error: $getStatus"
		return -code 1 -errorcode -1 $getStatus
	} else {
		sth::sthCore::log debug "The value:$getStatus of attribute:$attr from object:$handle was successfully fetched"
		set getValue $getStatus
		return 1
	}
	
}
proc ::sth::sthCore::doStcConfig { args } {
	
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	set handle [lindex $args 0]
	set stcAttr [lrange $args 1 end]
	set stcAttrPairs [concat [lindex $stcAttr 0] [lrange $stcAttr 1 end]]
	if {[string index $stcAttrPairs 0]!= "-"} {
		set stcAttrPairs -$stcAttrPairs
	}
	set configString "::stc::config $handle $stcAttrPairs"
	
	########### log stccall ###########
	::sth::sthCore::log stccall $configString
	
	if {[catch {eval $configString} configStatus ]} {
		regsub -all {\n} $configStatus ";#" configStatus
		::sth::sthCore::log error "Internal Command Error: $configStatus"
		set cmdFailed 1
		return -code 1 -errorcode -1 $configStatus
	} else {
		::sth::sthCore::log debug "The attribute:$stcAttrPairs was successfully set for handle:$handle"
		return $SUCCESS
	}
	
}

proc ::sth::sthCore::doStcConfigGenerator {HLTporthandle dashedAttrValuePairs} {
	set handleGenerator [::sth::sthCore::invoke stc::get $HLTporthandle -children-generator]
	set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
	set retHandle [::sth::sthCore::invoke stc::config $handleGeneratorConfig $dashedAttrValuePairs]	
    ::sth::sthCore::log info "doStcConfigGenerator: $handleGeneratorConfig Success."
    return ::sth::sthCore::SUCCESS;
}

proc ::sth::sthCore::invoke { args } {
    set num [llength $args]
    if {$num eq 1} {
	set cmdMsg [lindex $args 0]
    } else {
	set cmdMsg [lindex $args 0]
	if {[regexp -nocase "stc::perform" $cmdMsg]} {
	    set operation [lindex $args 1]
	    set dashedAttrValuePairs [lrange $args 2 end];
	    set cmdMsg "stc::perform $operation $dashedAttrValuePairs";
	    if {[regexp -nocase "DeviceCreate" $operation]} {
		if {![regexp -nocase "DeviceType" $dashedAttrValuePairs]} {
		    append cmdMsg " -DeviceType Router"
		}
	    }
	} elseif {[regexp -nocase "stc::config" $cmdMsg]} {
	    set handle [lindex $args 1]
	    set stcAttr [lrange $args 2 end]
	    set stcAttrPairs [concat [lindex $stcAttr 0] [lrange $stcAttr 1 end]]
	    if {$stcAttrPairs ne "" && [string index $stcAttrPairs 0] != "-"} {
		set stcAttrPairs -$stcAttrPairs
	    }
	    set cmdMsg "stc::config $handle $stcAttrPairs"  
	} elseif {[regexp -nocase "stc::get" $cmdMsg]} {
	    set handle [lindex $args 1]
	    set stcAttr [lindex $args 2]
	    if {$stcAttr ne "" && [string index $stcAttr 0] != "-"} {
		set stcAttr -$stcAttr
	    }
	    set cmdMsg "stc::get $handle $stcAttr"  
	} elseif {[regexp -nocase "stc::create" $cmdMsg]} {
	    if {$num eq 5}  {
		set cmdMsg [lrange $args 0 3]
		set stcAttr [lindex $args 4]
		append cmdMsg " $stcAttr"
	    } else {
		set cmdMsg "$args"
	    }
	} else {
	    set cmdMsg "$args"
	}
    }
    ::sth::sthCore::log stccall $cmdMsg
    
    if {[catch {eval $cmdMsg} cmdStatus ]} {
        regsub -all {\n} $cmdStatus ";#" cmdStatus
        ::sth::sthCore::log error "Internal Command Error: $cmdStatus "
        set cmdFailed 1
        return -code 1 -errorcode -1 "<$cmdMsg>: $cmdStatus"
    } else {
        # DE16818 fix
        # remove vxlan/fc handles from "stc::get port -AffiliationPort-sources" return values
        if {[regexp -nocase {stc::get.*port.*AffiliationPort-sources} $cmdMsg]} {
            if {[regsub -nocase -all { ?\S*vxlan\S*} $cmdStatus "" cmdStatus]} {
                regsub {^ } $cmdStatus "" cmdStatus
            }
            if {[regsub -nocase -all { ?\S*fc.*params\S*} $cmdStatus "" cmdStatus]} {
                regsub {^ } $cmdStatus "" cmdStatus
            }
        }

        ::sth::sthCore::log debug "return value: $cmdStatus "
        return $cmdStatus;
    }	
}
