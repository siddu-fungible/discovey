# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

proc ::sth::ospfTopology::Emulation_ospf_Topology_config_delete {} {
	set configType $::sth::ospfTopology::userArgsArray(type)
	set ospfHnd	   $::sth::ospfTopology::userArgsArray(handle)
	set ::sth::ospfTopology::returnedKeyList ""
	set elementHnd ""

	if {[regexp $::sth::ospfTopology::OSPFV3_STR $ospfHnd] == 1} {
		set ::sth::ospfTopology::isOspfv3 $::sth::ospfTopology::TRUE
		set ::sth::ospfTopology::currentOSPFVersion $::sth::ospfTopology::OSPFV3_STR
	} else {
		set ::sth::ospfTopology::isOspfv3 $::sth::ospfTopology::FALSE	
		set ::sth::ospfTopology::currentOSPFVersion $::sth::ospfTopology::OSPFV2_STR
	}		

	if {[info exist ::sth::ospfTopology::userArgsArray(elem_handle)] == 0} {
		return [::sth::ospfTopology::ReportError "ERROR: elem_handle is mandatory field"]
	} else {
		set elementHnd $::sth::ospfTopology::userArgsArray(elem_handle)
	}	
	
 	if {[string tolower $configType] == $::sth::ospfTopology::TYPE_GRID} {
		::sth::ospfTopology::DeleteGrid $elementHnd
	} else {
		::sth::ospfTopology::DeleteElement $elementHnd		
	}		
}

proc ::sth::ospfTopology::DeleteGrid {elementHnd} {
	set ospfHnd $::sth::ospfTopology::routerGridHndMap($elementHnd)
	set row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
	set col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)

	set connect_Row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
	set connect_Col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
	set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_Row,$connect_Col)
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)] == 1} {
		::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
		unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
	}
	
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)] == 1} {
		::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
		unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
	}

	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB)] == 1} {
				foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) {
					::sth::sthCore::invoke stc::delete $stubHnd
				}
				set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) ""
			}
			::sth::sthCore::invoke stc::delete $lsaHnd
			unset ::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
		}
	}

	set erHnd $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND)
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)] == 1} {
		foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB) {
			::sth::sthCore::invoke stc::delete $stubHnd
		}
	}

	unset ::sth::ospfTopology::routerGridHndMap($elementHnd)

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
	}
	
	set returnedSubKeyedList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	unset ::sth::ospfTopology::gridInfoMap($ospfHnd,GRIDHND)
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::DeleteElement {elementHnd} {
	if {[string tolower $::sth::ospfTopology::userArgsArray(type)] == $::sth::ospfTopology::TYPE_ROUTER} {
		if {[info exist ::sth::ospfTopology::routerConnectInfoMap($elementHnd)] == 1} {
			::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 0]
			::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
		}
	}

	if {[catch {::sth::sthCore::invoke stc::delete $elementHnd} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERRIR: $iErr"]
	}

	set returnedSubKeyedList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	
	return $::sth::ospfTopology::returnedKeyList		
}

proc ::sth::ospfTopology::Emulation_ospf_Topology_config_modify {} {
	set configType $::sth::ospfTopology::userArgsArray(type)
	set ospfHnd	   $::sth::ospfTopology::userArgsArray(handle)
	set ::sth::ospfTopology::returnedKeyList ""
	set elementHnd ""

	if {[regexp $::sth::ospfTopology::OSPFV3_STR $ospfHnd] == 1} {
		set ::sth::ospfTopology::isOspfv3 $::sth::ospfTopology::TRUE
		set ::sth::ospfTopology::currentOSPFVersion $::sth::ospfTopology::OSPFV3_STR
	} else {
		set ::sth::ospfTopology::isOspfv3 $::sth::ospfTopology::FALSE	
		set ::sth::ospfTopology::currentOSPFVersion $::sth::ospfTopology::OSPFV2_STR
	}	
	
	if {[info exist ::sth::ospfTopology::userArgsArray(elem_handle)] == 0} {
		return [::sth::ospfTopology::ReportError "ERROR: elem_handle is mandatory field"]
	} else {
		set elementHnd $::sth::ospfTopology::userArgsArray(elem_handle)
	}
	
	if {[string tolower $configType] == $::sth::ospfTopology::TYPE_SUMROUTES} {
		
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
			set validation [::sth::ospfTopology::CreateOSPFv2SumRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
							
			::sth::ospfTopology::ModifyOSPFv2SumRoutes $elementHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3InterAreaRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
					
			::sth::ospfTopology::ModifyOSPFv3InterAreaRoutes $elementHnd		
		}
		
	}  elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_EXTROUTES || [string tolower $configType] == $::sth::ospfTopology::TYPE_NSSAROUTES} {

		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {	
			set validation [::sth::ospfTopology::CreateOSPFv2ExtNssaRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}	
			
			::sth::ospfTopology::ModifyOSPFv2ExtNssaRoutes $elementHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3ExtNssaRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}			
		
			::sth::ospfTopology::ModifyOSPFv3ExtNssaRoutes $elementHnd
		}

	} elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_NETWORK} {
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {	
			set validation [::sth::ospfTopology::CreateOSPFv2NetworkRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}	
						
			::sth::ospfTopology::ModifyOSPFv2NetworkRoutes $elementHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3NetworkRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}	
		
			::sth::ospfTopology::ModifyOSPFv3NetworkRoutes $elementHnd
		}		
	} elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_ROUTER} {
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
			set validation [::sth::ospfTopology::CreateOSPFv2RoutersValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}	
					
			::sth::ospfTopology::ModifyOSPFv2Routers $elementHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3RoutersValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}	
					
			::sth::ospfTopology::ModifyOSPFv3Routers $elementHnd		
		}		
	}  elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_GRID} {

		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
			set validation [::sth::ospfTopology::CreateOSPFv2GridValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
					
			::sth::ospfTopology::ModifyOSPFv2Grid $elementHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3GridValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}		
		
			::sth::ospfTopology::ModifyOSPFv3Grid $elementHnd		
		}		
	} 
}


proc ::sth::ospfTopology::Emulation_ospf_Topology_config_create {} {
	set configType $::sth::ospfTopology::userArgsArray(type)
	set ospfHnd	   $::sth::ospfTopology::userArgsArray(handle)
	set ::sth::ospfTopology::returnedKeyList ""
	# topoType is used to store the ospf topology type: grid, none (fix CR306923057, by xiaozhi)
	array set ::sth::ospfTopology::topoType ""
	
	if {[regexp $::sth::ospfTopology::OSPFV3_STR $ospfHnd] == 1} {
		set ::sth::ospfTopology::isOspfv3 $::sth::ospfTopology::TRUE
		set ::sth::ospfTopology::currentOSPFVersion $::sth::ospfTopology::OSPFV3_STR
	} else {
		set ::sth::ospfTopology::isOspfv3 $::sth::ospfTopology::FALSE	
		set ::sth::ospfTopology::currentOSPFVersion $::sth::ospfTopology::OSPFV2_STR
	}

	if {[string tolower $configType] == $::sth::ospfTopology::TYPE_ROUTER} {
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
			set validation [::sth::ospfTopology::CreateOSPFv2RoutersValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
					
			::sth::ospfTopology::CreateOSPFv2Routers $ospfHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3RoutersValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
					
			::sth::ospfTopology::CreateOSPFv3Routers $ospfHnd		
		}
		
	} elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_GRID} {
		 ##DFFF
		set ::sth::ospfTopology::topoType($ospfHnd) "grid"
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
			set validation [::sth::ospfTopology::CreateOSPFv2GridValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
			
			::sth::ospfTopology::CreateOSPFv2Grid $ospfHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3GridValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
			
			::sth::ospfTopology::CreateOSPFv3Grid $ospfHnd
		}

	} elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_SUMROUTES} {
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
			set validation [::sth::ospfTopology::CreateOSPFv2SumRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
				
			::sth::ospfTopology::CreateOSPFv2SumRoutes $ospfHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3InterAreaRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
					
			::sth::ospfTopology::CreateOSPFv3InterAreaRoutes $ospfHnd
		}

	} elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_EXTROUTES || [string tolower $configType] == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {	
			set validation [::sth::ospfTopology::CreateOSPFv2ExtNssaRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
						
			::sth::ospfTopology::CreateOSPFv2ExtNssaRoutes $ospfHnd
		} else {
			set validation [::sth::ospfTopology::CreateOSPFv3ExtNssaRoutesValidation $ospfHnd]
			if {[lindex $validation 0] == "FALSE"} {
				return [::sth::ospfTopology::ReportError "ERROR: [lindex $validation 1]"]
			}
					
			::sth::ospfTopology::CreateOSPFv3ExtNssaRoutes $ospfHnd
		}

	} elseif {[string tolower $configType] == $::sth::ospfTopology::TYPE_NETWORK} {
		if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {		
			::sth::ospfTopology::CreateOSPFv2NetworkRoutes $ospfHnd
		} else {
			::sth::ospfTopology::CreateOSPFv3NetworkRoutes $ospfHnd 
		}		
	}
}



proc ::sth::ospfTopology::ModifyOSPFv2Routers {elementHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 1} {
		# redirect link
		if {[info exist ::sth::ospfTopology::routerConnectInfoMap($elementHnd)] == 1} {
			set connectLsa $::sth::ospfTopology::userArgsArray(router_connect)
			set connectRouterID [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
			set routerID [::sth::sthCore::invoke stc::get $elementHnd -AdvertisingRouterId]
			set linkInfo $::sth::ospfTopology::routerConnectInfoMap($elementHnd)
	
			set routerLsaLink [lindex $linkInfo 1]
			
			::sth::sthCore::invoke stc::config $routerLsaLink "-LinkId $connectRouterID"

			set lsaLinkList [::sth::sthCore::invoke stc::get $connectLsa -children-RouterLsaLink]
			set dataList ""
			foreach lsaLink $lsaLinkList {
				set linkType [::sth::sthCore::invoke stc::get $lsaLink -LinkType]
				if {![regexp -nocase "STUB_NETWORK" $linkType]} {
					lappend dataList [::sth::sthCore::invoke stc::get $lsaLink -LinkData]
				}
			}
			set linkData [GetUniqueID $dataList]
			if {$linkData == ""} {
				set linkData 0.0.0.1
			}
		
			lappend parameterList -LinkData $linkData
			lappend parameterList -LinkId $routerID
			
			lappend parameterList -LinkType POINT_TO_POINT		
			if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $connectLsa $parameterList} linkHnd] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $linkHnd"]
			}
			set ::sth::ospfTopology::routerConnectInfoMap($elementHnd) [list $linkHnd $routerLsaLink]
		} else {
			# Create link
			set connectLsa $::sth::ospfTopology::userArgsArray(router_connect)
			set connectRouterID [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
			set routerID [::sth::sthCore::invoke stc::get $elementHnd -AdvertisingRouterId]
			
			# For connect lsa
			set lsaLinkList [::sth::sthCore::invoke stc::get $connectLsa -children-RouterLsaLink]
			
			set dataList ""
			foreach lsaLink $lsaLinkList {
				set linkType [::sth::sthCore::invoke stc::get $lsaLink -LinkType]
				if {![regexp -nocase "STUB_NETWORK" $linkType]} {
					lappend dataList [::sth::sthCore::invoke stc::get $lsaLink -LinkData]
				}
			}
			set linkData [GetUniqueID $dataList]
			if {$linkData == ""} {
				set linkData 0.0.0.1
			}

			set parameterList ""
			lappend parameterList -LinkData $linkData
			lappend parameterList -LinkId $routerID
			lappend parameterList -LinkType POINT_TO_POINT		
			if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $connectLsa $parameterList} linkHnd] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $linkHnd"]
			}
	
			set networkBlock [::sth::sthCore::invoke stc::get $linkHnd -children-Ipv4NetworkBlock]
			::sth::sthCore::invoke stc::config $networkBlock "-StartIpList $routerID -NetworkCount 1 -AddrIncrement 0 -Active TRUE"
			
			# For target lsa
			set lsaLinkList [::sth::sthCore::invoke stc::get $elementHnd -children-RouterLsaLink]
			
			set dataList ""
			foreach lsaLink $lsaLinkList {
				set linkType [::sth::sthCore::invoke stc::get $lsaLink -LinkType]
				if {![regexp -nocase "STUB_NETWORK" $linkType]} {
					lappend dataList [::sth::sthCore::invoke stc::get $lsaLink -LinkData]
				}
			}
			set linkData [GetUniqueID $dataList]
			if {$linkData == ""} {
				set linkData 0.0.0.1
			}

			set parameterList ""
			lappend parameterList -LinkData $linkData
			lappend parameterList -LinkId $connectRouterID
			lappend parameterList -LinkType POINT_TO_POINT		
			if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $elementHnd $parameterList} elementLinkHnd] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $linkHnd"]
			}		

			set networkBlock [::sth::sthCore::invoke stc::get $elementLinkHnd -children-Ipv4NetworkBlock]
			::sth::sthCore::invoke stc::config $networkBlock "-StartIpList $routerID -NetworkCount 1 -AddrIncrement 0 -Active TRUE"
			
			
			set ::sth::ospfTopology::routerConnectInfoMap($elementHnd)	[list $linkHnd $elementLinkHnd]
		}
	}
	
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	
	set parameterList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_id) != [::sth::sthCore::invoke stc::get $elementHnd -AdvertisingRouterId]} {
			lappend parameterList -AdvertisingRouterId $::sth::ospfTopology::userArgsArray(router_id)
			set lsaLink [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
			::sth::sthCore::invoke stc::config $lsaLink "-LinkId $::sth::ospfTopology::userArgsArray(router_id)"
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(router_disconnect)] == 1} {
		set disconnectLsa $::sth::ospfTopology::userArgsArray(router_disconnect)
		if {[catch {set linkInfo $::sth::ospfTopology::routerConnectInfoMap($elementHnd)} iErr] != 1} {
			set linkHnd [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
			set parent [::sth::sthCore::invoke stc::get $linkHnd -parent]
			if {$parent == $disconnectLsa} {
				if {[catch {::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 0]} iErr] == 1} {
					return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
				} 
				if {[catch {::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]} iErr] == 1} {
					return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
				}
				unset ::sth::ospfTopology::routerConnectInfoMap($elementHnd)
			} else {
				return [::sth::ospfTopology::ReportError "ERROR: $elementHnd and $disConnectLsa are not connected"]
			}
		} else {
			return [::sth::ospfTopology::ReportError "ERROR: $elementHnd is not used"]
		}
	}
	
	set currentAbr [::sth::sthCore::invoke stc::get $elementHnd -Abr]
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_abr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_abr) == 1} {
			set newAbr TRUE
		} else {
			set newAbr FALSE
		}
		if {[string toupper $currentAbr] != $newAbr} {
			lappend parameterList -Abr $newAbr
		}
	}
	
	set currentAsbr [::sth::sthCore::invoke stc::get $elementHnd -Asbr]
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_asbr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			set newAsbr TRUE
		} else {
			set newAsbr FALSE
		}
		if {[string toupper $currentAsbr] != $newAsbr} {
			lappend parameterList -Asbr $newAsbr
		}		
	}
	
	set currentActive [::sth::sthCore::invoke stc::get $elementHnd -Active]
	
	if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
		set newActive TRUE
	} else {
		set newActive FALSE
	}	
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_enable)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
			set lsaLinkList [::sth::sthCore::invoke stc::get $elementHnd -children-RouterLsaLink]
			foreach lsaLink $lsaLinkList {
				::sth::sthCore::invoke stc::config $lsaLink "-Active TRUE"
			}
		} else {
			set lsaLinkList [::sth::sthCore::invoke stc::get $elementHnd -children-RouterLsaLink]
			foreach lsaLink $lsaLinkList {
				::sth::sthCore::invoke stc::config $lsaLink "-Active FALSE"
			}	
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_metric)] ==1} {
		set lsaLinkMetricValue $::sth::ospfTopology::userArgsArray(link_metric)
		set lsaLinkList [::sth::sthCore::invoke stc::get $elementHnd -children-RouterLsaLink]
		foreach lsaLink $lsaLinkList {
			if {[catch {::sth::sthCore::invoke stc::config $lsaLink "-Metric $lsaLinkMetricValue"} iErr]} {
				return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
			}
		}                
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_disconnect)] == 1} {
		unset ::sth::ospfTopology::userArgsArray(router_disconnect)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 1} {
		unset ::sth::ospfTopology::userArgsArray(router_id)
	}
	
	if {[catch {::sth::sthCore::invoke stc::config $elementHnd $parameterList} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERRIR: $iErr"]
	}
	
	set returnedSubKeyedList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	keylset returnedSubKeyedList version $::sth::ospfTopology::currentOSPFVersion
	keylset returnedSubkeyedList router_lsa $elementHnd
	keylset ::sth::ospfTopology::returnedKeyList router $returnedSubkeyedList
	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::DeleteLinks {elementHnd} {
	set disconnectLsa $::sth::ospfTopology::userArgsArray(router_disconnect)
	set linkInfo $::sth::ospfTopology::routerConnectInfoMap($elementHnd)
	if {[catch {set linkInfo $::sth::ospfTopology::routerConnectInfoMap($elementHnd)} iErr] != 1} {
		set linkHnd [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
		set parent [::sth::sthCore::invoke stc::get $linkHnd -parent]
		
		if {$parent == $disconnectLsa} {
			if {[catch {::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]} iErr] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
			}
			if {[catch {::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 0]} iErr] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
			}
			unset ::sth::ospfTopology::routerConnectInfoMap($elementHnd)
		} else {
			return 0
		}
	} else {
		return 0
	}
	return 1
}



proc ::sth::ospfTopology::ModifyOSPFv3Routers {elementHnd} {
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 1} {
		set connectLsa $::sth::ospfTopology::userArgsArray(router_connect)
		set routerLsa $elementHnd
		if {[info exist ::sth::ospfTopology::routerConnectInfoMap($elementHnd)] == 1} {
			# Redirect link
			set srcLink [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
			set targetLink [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 0]
			
			set srcIf [::sth::sthCore::invoke stc::get $srcLink -IfId]
			set targetIfId [::sth::sthCore::invoke stc::get $targetLink -IfId]
			
			::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
			::sth::sthCore::invoke stc::delete [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 0]
			unset ::sth::ospfTopology::routerConnectInfoMap($elementHnd)
		} else {
			# Get Unique If ID
			set ifList [::sth::sthCore::invoke stc::get $connectLsa -children-Ospfv3RouterLsaIf]
			set idList ""
			foreach interface $ifList {
				lappend idList [::sth::sthCore::invoke stc::get $interface -ifId]
			}
			set srcIfId [GetUniqueIDForV3 $idList]			

			# Get Unique If ID
			set ifList [::sth::sthCore::invoke stc::get $routerLsa -children-Ospfv3RouterLsaIf]
			set idList ""
			foreach interface $ifList {
				lappend idList [::sth::sthCore::invoke stc::get $interface -ifId]
			}
			set targetIfId [GetUniqueIDForV3 $idList]		
		}
		
		# Create target new LSA link
		set parameterList ""
		lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
		lappend parameterList -IfId $targetIfId
		lappend parameterList -NeighborIfId $srcIfId
		
		if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
			lappend parameterList -Active TRUE
		} else {
			lappend parameterList -Active FALSE	
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(link_metric)] ==1} {
			set lsaLinkMetricValue $::sth::ospfTopology::userArgsArray(link_metric)
			lappend parameterList -Metric $lsaLinkMetricValue
		}		
		
		if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $routerLsa $parameterList} targetRouterLsaIf] == 1} {
			return [::sth::ospfTopology::ReportError "Error: $routerLsa"]		
		}

		# Create new source router LSA link
		set parameterList ""
		lappend parameterList -IfId $srcIfId
		lappend parameterList -NeighborIfId $targetIfId
		lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $routerLsa -AdvertisingRouterId]
	
		if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
			lappend parameterList -Active TRUE
		} else {
			lappend parameterList -Active FALSE	
		}
	
		if {[info exist ::sth::ospfTopology::userArgsArray(link_metric)] ==1} {
			set lsaLinkMetricValue $::sth::ospfTopology::userArgsArray(link_metric)
			lappend parameterList -Metric $lsaLinkMetricValue
		}

		if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $connectLsa $parameterList} srcRouterLsaIf] == 1} {
			return [::sth::ospfTopology::ReportError "Error: $srcRouterLsaIf"]
		} 

		set ::sth::ospfTopology::routerConnectInfoMap($routerLsa) [list $targetRouterLsaIf $srcRouterLsaIf]
	} 
	
	set parameterList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_id) != [::sth::sthCore::invoke stc::get $elementHnd -AdvertisingRouterId]} {
			lappend parameterList -AdvertisingRouterId $::sth::ospfTopology::userArgsArray(router_id)
			set advId $::sth::ospfTopology::userArgsArray(router_id)
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_disconnect)] == 1} {
		if {[::sth::ospfTopology::DeleteLinks $elementHnd] == 0} {
			return [::sth::ospfTopology::ReportError "ERROR: router_disconnect returns error"]
		}
	}
	
	set routerTypeString [::sth::sthCore::invoke stc::get $elementHnd -RouterType]
	if {[info exist ::sth::ospfTopology::userArgsArray(router_abr)] == 1 && [info exist ::sth::ospfTopology::userArgsArray(router_asbr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_abr) == 1 && $::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			set routerTypeString "EBIT|BBIT"
			lappend parameterList -RouterType $routerTypeString
		} elseif {$::sth::ospfTopology::userArgsArray(router_abr) == 0 && $::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			set routerTypeString "EBIT"
			lappend parameterList -RouterType $routerTypeString
		} elseif {$::sth::ospfTopology::userArgsArray(router_abr) == 1 && $::sth::ospfTopology::userArgsArray(router_asbr) == 0} {
			set routerTypeString "BBIT"
			lappend parameterList -RouterType $routerTypeString
		}
	} elseif {[info exist ::sth::ospfTopology::userArgsArray(router_abr)] == 0 && [info exist ::sth::ospfTopology::userArgsArray(router_asbr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			if {$routerTypeString == 0} {
				lappend parameterList -RouterType "EBIT"
			} else {
				if {[regexp $routerTypeString "EBIT"] == 0} {
					set ebbitString "EBIT"
					lappend parameterList -RouterType "$routerTypeString$ebbitString"
				}
			}
		}
	} elseif {[info exist ::sth::ospfTopology::userArgsArray(router_abr)] == 1 && [info exist ::sth::ospfTopology::userArgsArray(router_asbr)] == 0} {
		if {$::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			if {$routerTypeString == 0} {
				lappend parameterList -RouterType "BBIT"
			} else {
				if {[regexp $routerTypeString "BBIT"] == 0} {
					set bbitString "BBIT"
					lappend parameterList -RouterType "$routerTypeString$bbitString"
				}
			}
		}
	}
	
	
	if {[catch {::sth::sthCore::invoke stc::config $elementHnd $parameterList} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 1} {
		set parameterList ""
		set targetLsaLinkHnd [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 0]
		set srcLsaLinkHnd [lindex $::sth::ospfTopology::routerConnectInfoMap($elementHnd) 1]
		set srcLsaHnd [::sth::sthCore::invoke stc::get $srcLsaLinkHnd -parent]
	
		lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $srcLsaHnd -AdvertisingRouterId]
		
		if {[catch {::sth::sthCore::invoke stc::config $targetLsaLinkHnd $parameterList} iErr] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
		}
	
		set parameterList ""
		lappend parameterList -NeighborRouterId $advId
		if {[catch {::sth::sthCore::invoke stc::config $srcLsaLinkHnd $parameterList} iErr] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
		}
	}
	::sth::sthCore::doStcApply

	set returnedSubKeyedList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	keylset returnedSubKeyedList version $::sth::ospfTopology::currentOSPFVersion
	keylset returnedSubkeyedList router_lsa $elementHnd
	keylset ::sth::ospfTopology::returnedKeyList router $returnedSubkeyedList
	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::ModifyOSPFv3ExtNssaRoutes {elementHnd} {
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	set parameterList ""
	set connectName ""
	set configType $::sth::ospfTopology::userArgsArray(type)
	if {[string tolower $configType] == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set connectName external_connect
	} else {
		set connectName nssa_connect
	}	
	
	if {[info exist ::sth::ospfTopology::userArgsArray($connectName)] == 1} {
		set row [lindex $::sth::ospfTopology::userArgsArray($connectName) 0]
		set col [lindex $::sth::ospfTopology::userArgsArray($connectName) 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
		set routerID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
		lappend parameterList -AdvertisingRouterId $routerID
	} else {
		set row 1
		set col 1
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
		set routerID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	}

	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set objectName "Ospfv3AsExternalLsaBlock"
	} else {
		set objectName "Ospfv3NssaLsaBlock"	
	}
	
	set curMetricType [::sth::sthCore::invoke stc::get $elementHnd -MetricType]
	if {[string tolower $curMetricType] == "true"} {
		set curMetricTypeValue 1
	} else {
		set curMetricTypeValue 0
	}
	
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
    	set prefix_type external_prefix_type
    	set metric external_prefix_metric
    } else {
    	set prefix_type nssa_prefix_type
    	set metric nssa_prefix_metric    
    }
	
    if {[info exist ::sth::ospfTopology::userArgsArray($prefix_type)] != 0} {
    	if {$curMetricTypeValue != $::sth::ospfTopology::userArgsArray($prefix_type)} {
    		if {$::sth::ospfTopology::userArgsArray($prefix_type) == 1} {
    			lappend parameterList -MetricType TRUE
    		} else {
    			lappend parameterList -MetricType FALSE
    		}
    	}
    }
    
    if {[info exist ::sth::ospfTopology::userArgsArray($metric)] != 0} {
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray($metric)
    }
    
    lappend parameterList -LsType "AS_EXT_LSA"
	 
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set objectName "Ospfv3AsExternalLsaBlock"
	} else {
		set objectName "Ospfv3NssaLsaBlock"	
	}	
	
	if {[catch {::sth::sthCore::invoke stc::config $elementHnd $parameterList} interAreaHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $interAreaHnd"]
	} else {
		set parameterList ""
		if {[catch {set networkBlock [::sth::sthCore::invoke stc::get $elementHnd -children-Ipv6NetworkBlock]} returnVal] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $returnVal"]
		} else {
			if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
				if {$::sth::ospfTopology::userArgsArray(external_prefix_step) != [::sth::sthCore::invoke stc::get $networkBlock -AddrIncrement]} {
					lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(external_prefix_step)
				}
				
				if {$::sth::ospfTopology::userArgsArray(external_number_of_prefix) != [::sth::sthCore::invoke stc::get $networkBlock -NetworkCount]} {
					lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(external_number_of_prefix)
				}
				
				if {$::sth::ospfTopology::userArgsArray(external_prefix_length) != [::sth::sthCore::invoke stc::get $networkBlock -PrefixLength]} {
					lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(external_prefix_length)
				}
				
				if {[info exist ::sth::ospfTopology::userArgsArray(external_prefix_start)] == 1} {
					lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(external_prefix_start)
				} 
 			} else {
				if {$::sth::ospfTopology::userArgsArray(nssa_number_of_prefix) != [::sth::sthCore::invoke stc::get $networkBlock -NetworkCount]} {
					lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(nssa_number_of_prefix)
				}
				
				if {$::sth::ospfTopology::userArgsArray(nssa_prefix_length) != [::sth::sthCore::invoke stc::get $networkBlock -PrefixLength]} {
					lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(nssa_prefix_length)
				}
				
				if {$::sth::ospfTopology::userArgsArray(nssa_prefix_step) != [::sth::sthCore::invoke stc::get $networkBlock -AddrIncrement]} {
					lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(nssa_prefix_step)
				}
				
				if {[info exist ::sth::ospfTopology::userArgsArray(nssa_prefix_start)] == 1} {
					lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(nssa_prefix_start)
				} 
			}
			
			if {[catch {::sth::sthCore::invoke stc::config $networkBlock $parameterList} networkBlock] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
			}
		}
	}
	
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set keyedName external
		set keyedLsaName external_lsas
		set ::sth::ospfTopology::extRouteHndLocationMap($interAreaHnd) [list $row $col]
	} else {
		set keyedName nssa
		set keyedLsaName nssa_lsas	
		set ::sth::ospfTopology::nssaRouteHndLocationMap($interAreaHnd) [list $row $col]
	}

	::sth::sthCore::doStcApply

	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	set subList ""
	keylset subList $keyedLsaName $elementHnd
	keylset subList connected_router $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset ::sth::ospfTopology::returnedKeyList $keyedLsaName $subList
	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
		
}

proc ::sth::ospfTopology::ModifyOSPFv3InterAreaRoutes {elementHnd} {
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]

	set parameterList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		set row [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 0]
		set col [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
		set routerID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
		lappend parameterList -AdvertisingRouterId $routerID
	}
	
	set parameterList ""
	#lappend parameterList -AdvertisingRouterId $routerID
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_metric)] == 1} {
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray(summary_prefix_metric)
	}
	if {[catch {::sth::sthCore::invoke stc::config $elementHnd $parameterList} interAreaHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $interAreaHnd"]
	} else {
		set parameterList ""
		if {[catch {set networkBlock [::sth::sthCore::invoke stc::get $elementHnd -children-Ipv6NetworkBlock]} returnVal] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $returnVal"]
		} else {
			if {$::sth::ospfTopology::userArgsArray(summary_number_of_prefix) != [::sth::sthCore::invoke stc::get $networkBlock -NetworkCount]} {
				lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(summary_number_of_prefix)
			}
			
			if {$::sth::ospfTopology::userArgsArray(summary_prefix_length) != [::sth::sthCore::invoke stc::get $networkBlock -PrefixLength]} {
				lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(summary_prefix_length)
			}
			
			if {$::sth::ospfTopology::userArgsArray(summary_prefix_step) != [::sth::sthCore::invoke stc::get $networkBlock -AddrIncrement]} {
				lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(summary_prefix_step)
			}
			
			if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_start)] == 1} {
				lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(summary_prefix_start)
			} 

			if {[catch {::sth::sthCore::invoke stc::config $networkBlock $parameterList} networkBlock] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
			}
		}
	}	
	
	::sth::sthCore::doStcApply
	
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	set subList ""
	set row [lindex $::sth::ospfTopology::sumRouteHndLocationMap($elementHnd) 0]
	set col [lindex $::sth::ospfTopology::sumRouteHndLocationMap($elementHnd) 1]
	keylset subList summary_lsa $elementHnd
	keylset subList connected_router $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset ::sth::ospfTopology::returnedKeyList summary $subList
	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::ModifyOSPFv2SumRoutes {elementHnd} {
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	
	set parameterList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		set row [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 0]
		set col [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
		set routerID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
		lappend parameterList -AdvertisingRouterId $routerID
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_metric)] == 1} {
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray(summary_prefix_metric)
	}
	if {[catch {::sth::sthCore::invoke stc::config $elementHnd $parameterList} sumBlockHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $sumBlockHnd"]
	} else {
		set parameterList ""
		if {[catch {::sth::sthCore::invoke stc::get $elementHnd  -children-Ipv4NetworkBlock} networkBlock] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
		} else {
		
			if {$::sth::ospfTopology::userArgsArray(summary_number_of_prefix) != [::sth::sthCore::invoke stc::get $networkBlock -NetworkCount]} {
				lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(summary_number_of_prefix)
			}
			
			if {$::sth::ospfTopology::userArgsArray(summary_prefix_length) != [::sth::sthCore::invoke stc::get $networkBlock -PrefixLength]} {
				lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(summary_prefix_length)
			}
			
			if {$::sth::ospfTopology::userArgsArray(summary_prefix_step) != [::sth::sthCore::invoke stc::get $networkBlock -PrefixLength]} {
				lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(summary_prefix_step)
			}
					
			if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_start)] == 1} {
				lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(summary_prefix_start)
			}	
		
			if {[catch {::sth::sthCore::invoke stc::config $networkBlock $parameterList} networkBlock] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
			}
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		set ::sth::ospfTopology::sumRouteHndLocationMap($elementHnd) $::sth::ospfTopology::userArgsArray(summary_connect)
	}
	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}


	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	set subList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		set connection $::sth::ospfTopology::userArgsArray(summary_connect)
		set row [lindex $connection 0]
		set col [lindex $connection 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	} else {
		# fix CR306923057, create default router lsa on the emulated router (no grid to create any simulated routers)
		if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
			set lsaHnd [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
			set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $lsaHnd
		} else {
			set lsaHnd $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
		}
	}
	keylset subList connected_router $lsaHnd
	#set row [lindex $::sth::ospfTopology::sumRouteHndLocationMap($elementHnd) 0]
	#set col [lindex $::sth::ospfTopology::sumRouteHndLocationMap($elementHnd) 1]
	keylset subList summary_lsa $elementHnd
	#keylset subList connected_router $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)

	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset ::sth::ospfTopology::returnedKeyList summary $subList
	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::ModifyOSPFv2ExtNssaRoutes {elementHnd} {
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	set parameterList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(external_connect)] == 1} {
		set row [lindex $::sth::ospfTopology::userArgsArray(external_connect) 0]
		set col [lindex $::sth::ospfTopology::userArgsArray(external_connect) 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
		lappend parameterList -AdvertisingRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	}
		
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		lappend parameterList -Type NSSA
		set prefix_metric "nssa_prefix_metric"
		set prefix_forward_addr "nssa_prefix_forward_addr"
		set prefix_type "nssa_prefix_type"
		set number_of_prefix "nssa_number_of_prefix"
		set prefix_step "nssa_prefix_step"
		set prefix_length "nssa_prefix_length"
		set prefix_start "nssa_prefix_start"
	} else {
		lappend parameterList -Type EXT		
		set prefix_metric "external_prefix_metric"
		set prefix_forward_addr "external_prefix_forward_addr"
		set prefix_type "external_prefix_type"
		set number_of_prefix "external_number_of_prefix"
		set prefix_step "external_prefix_step"
		set prefix_length "external_prefix_length"
		set prefix_start "external_prefix_start"
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray($prefix_metric)] == 1} {
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray($prefix_metric)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray($prefix_forward_addr)] == 1} {
		lappend parameterList -ForwardingAddr $::sth::ospfTopology::userArgsArray($prefix_forward_addr)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray($prefix_type)] == 1} {
		lappend parameterList -MetricType $::sth::ospfTopology::userArgsArray($prefix_type)
	}
		
	if {[catch {::sth::sthCore::invoke stc::config $elementHnd $parameterList} extLsaHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $extLsaHnd"]
	} else {		
		set parameterList ""		 
		set networkBlockHnd [::sth::sthCore::invoke stc::get $elementHnd -children-Ipv4NetworkBlock]
		
		if {$::sth::ospfTopology::userArgsArray($number_of_prefix) != [::sth::sthCore::invoke stc::get $networkBlockHnd -NetworkCount]} {
			lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray($number_of_prefix)
		}
		
		if {$::sth::ospfTopology::userArgsArray($prefix_step) != [::sth::sthCore::invoke stc::get $networkBlockHnd -AddrIncrement]} {
			lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray($prefix_step)
		}
		
		if {$::sth::ospfTopology::userArgsArray($prefix_length) != [::sth::sthCore::invoke stc::get $networkBlockHnd -PrefixLength]} {
			lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray($prefix_length)
		}
					
		if {[info exist ::sth::ospfTopology::userArgsArray($prefix_start)] == 1} {
			lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray($prefix_start)
		}
		
		if {[catch {::sth::sthCore::invoke stc::config $networkBlockHnd $parameterList} networkBlock] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
		}	
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(external_connect)] == 1 && $::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES } {
		set ::sth::ospfTopology::extRouteHndLocationMap($elementHnd) $::sth::ospfTopology::userArgsArray(external_connect)
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(nssa_connect)] == 1 && $::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		set ::sth::ospfTopology::nssaRouteHndLocationMap($elementHnd) $::sth::ospfTopology::userArgsArray(nssa_connect)
	}

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}	

	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set subList ""
		keylset subList connected_router $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
		keylset subList external_lsas $elementHnd
		keylset subList version $::sth::ospfTopology::currentOSPFVersion
		keylset ::sth::ospfTopology::returnedKeyList external $subList
	} else {
		set subList ""
		set row [lindex $::sth::ospfTopology::nssaRouteHndLocationMap($elementHnd) 0]
		set col [lindex $::sth::ospfTopology::nssaRouteHndLocationMap($elementHnd) 1]
		keylset subList connected_router $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
		keylset subList nssa_lsas $elementHnd
		keylset subList version $::sth::ospfTopology::currentOSPFVersion
		keylset ::sth::ospfTopology::returnedKeyList nssa $subList	
	}
	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::ModifyOSPFv3NetworkRoutes {elementHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(net_dr)] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: net_dr is not allowed in modify mode"]
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_count)] == 1} {
		if {$::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT) == 0} {
			return [::sth::ospfTopology::ReportError "ERROR: $elementHnd is deleted (net_count is set to 0 previously)"]
		} 
	}
	
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	set lsaHnd $::sth::ospfTopology::networkLSAInfoMap($elementHnd,DR)
	set lsaLinkHnd $::sth::ospfTopology::networkLSAInfoMap($elementHnd,DR_LINK)
	set drLsaLinkHnd $::sth::ospfTopology::networkLSAInfoMap($elementHnd,DR_NET_LINK)
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_count)] == 1} {
		if {$::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT) == 0} {
			return [::sth::ospfTopology::ReportError "ERROR: $elementHnd is deleted (net_count is set to 0 previously)"]
		} 
		
		set net_count $::sth::ospfTopology::userArgsArray(net_count)
		
		if {$net_count < $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT)} {
			set totalPair [llength $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR)]
			set count 0
			foreach lsaPair $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) {
				if {$count >= $net_count} {
					set routerLsaHnd [lindex $lsaPair 1]
					set attachRouterHnd [lindex $lsaPair 0]
					::sth::sthCore::invoke stc::delete $routerLsaHnd
					::sth::sthCore::invoke stc::delete $attachRouterHnd
				}
				incr count
				
				if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
					return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
				}
				::sth::sthCore::invoke stc::sleep 5
			
				set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) [lrange $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) 0 [expr $net_count - 1]]
			}
			
			if {$net_count == 0} {
				::sth::sthCore::invoke stc::delete $::sth::ospfTopology::networkLSAInfoMap($elementHnd,INTRABLK)
				::sth::sthCore::invoke stc::delete $elementHnd
				
				if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
					return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
				}
				
				unset ::sth::ospfTopology::userArgsArray
				set ::sth::ospfTopology::returnedKeyList ""
				keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
				keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd	
	
				set subList ""
				keylset subList network_lsa $elementHnd
				keylset subList version $::sth::ospfTopology::currentOSPFVersion
				keylset subList intra_area_prf_lsa $::sth::ospfTopology::networkLSAInfoMap($elementHnd,INTRABLK)
				keylset ::sth::ospfTopology::returnedKeyList network $subList
				set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT) $net_count	
				unset ::sth::ospfTopology::networkLSAInfoMap($elementHnd,INTRABLK)
				return $::sth::ospfTopology::returnedKeyList
			}
			
		} elseif {$net_count > $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT)} {
			set totalCount [llength $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR)]
			set hasChanged 1
			for {set count $totalCount} {$count < $net_count} {incr count} {
				set lsaPair ""
				set parameterList ""
				lappend parameterList -Active TRUE
				lappend parameterList -RouterType 0
				lappend parameterList -Options V6BIT|EBIT|RBIT
				set tempRouterLsa [::sth::sthCore::invoke stc::create "Ospfv3RouterLsa" -under $ospfHnd $parameterList]
		
				set parameterList ""
				lappend parameterList -IfType TRANSIT_NETWORK
				lappend parameterList -Metric 1
				lappend parameterList -IfId $::sth::ospfTopology::networkLSAInfoMap($elementHnd,IFID)
				lappend parameterList -NeighborIfId $::sth::ospfTopology::networkLSAInfoMap($elementHnd,IFID)
				lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
				lappend parameterList -Active TRUE
				set tempOspfRouterLsaIf [::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $tempRouterLsa $parameterList]

        		set parameterList ""
        		lappend parameterList -Active TRUE
        		set tempAttachedRouter [::sth::sthCore::invoke stc::create "Ospfv3AttachedRouter" -under $elementHnd $parameterList]

				lappend lsaPair $tempAttachedRouter $tempRouterLsa
				lappend ::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) $lsaPair		
			}			
		}	
		
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT) $net_count
	}
	
	set hasChanged 0
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip)] == 1} {
		set hasChanged 1
		set net_ip $::sth::ospfTopology::userArgsArray(net_ip)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP) $net_ip
	} else {
		set net_ip $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP)
	}
			
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip_step)] == 1} {
		set hasChanged 1
		set net_ip_step $::sth::ospfTopology::userArgsArray(net_ip_step)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_STEP) $net_ip_step
	} else {
		set net_ip_step $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_STEP)
	}			
			
	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix)] == 1} {
		set hasChanged 1
		set net_prefix $::sth::ospfTopology::userArgsArray(net_prefix)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX) $net_prefix
	} else {
		set net_prefix $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX)
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix_length)] == 1} {
		set hasChanged 1
		set net_prefix_length $::sth::ospfTopology::userArgsArray(net_prefix_length)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX_LENGTH) $net_prefix_length
	} else {
		set net_prefix_length $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX_LENGTH)
	}	
	
	if {$hasChanged == 1} {
		set intraBlk $::sth::ospfTopology::networkLSAInfoMap($elementHnd,INTRABLK)

		set networkBlk [::sth::sthCore::invoke stc::get $intraBlk -children-Ipv6NetworkBlock]
		set parameterList ""
		lappend parameterList -StartIpList $net_prefix
		lappend parameterList -PrefixLength $net_prefix_length
		::sth::sthCore::invoke stc::config $networkBlk $parameterList
	
		set tempID $net_ip
		for {set i 0} {$i < $net_count} {incr i} {
			set lsaPair [lindex $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) $i]
			set routerLsa [lindex $lsaPair 1]
			set attachedRouterLsa [lindex $lsaPair 0]
			
			set parameterList ""
			lappend parameterList -AdvertisingRouterId $tempID
			lappend parameterList -Active TRUE
			lappend parameterList -RouterType 0
			lappend parameterList -Options V6BIT|EBIT|RBIT
			::sth::sthCore::invoke stc::config $routerLsa $parameterList
			
			set lsaIf [::sth::sthCore::invoke stc::get $routerLsa -children-Ospfv3RouterLsaIf]
			
			set parameterList ""
			lappend parameterList -IfType TRANSIT_NETWORK
			lappend parameterList -Metric 1
			lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
			lappend parameterList -Active TRUE
			::sth::sthCore::invoke stc::config $lsaIf $parameterList

        	set parameterList ""
       	 	lappend parameterList -RouterId $tempID
        	lappend parameterList -Active TRUE
       		::sth::sthCore::invoke stc::config $attachedRouterLsa $parameterList


			set tempID [::sth::ospfTopology::IncrementIpV4Address $tempID $net_ip_step]
		}	
	}
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	unset ::sth::ospfTopology::userArgsArray
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd	
	
	set subList ""
	keylset subList network_lsa $elementHnd
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList intra_area_prf_lsa $::sth::ospfTopology::networkLSAInfoMap($elementHnd,INTRABLK)
	keylset ::sth::ospfTopology::returnedKeyList network $subList

	return 	$::sth::ospfTopology::returnedKeyList	
		
}

proc ::sth::ospfTopology::CreateOSPFv3NetworkRoutes {ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(net_dr)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(net_dr)
		set ospfHnd [::sth::sthCore::invoke stc::get $lsaHnd -parent]
	} else {
		return [::sth::ospfTopology::ReportError "ERROR: Missing net_dr"]
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_count)] == 1} {
		set net_count $::sth::ospfTopology::userArgsArray(net_count)
	} else {
		set net_count 1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix)] == 1} {
		set net_prefix $::sth::ospfTopology::userArgsArray(net_prefix)
	} else {
		set net_prefix 2000::1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip)] == 1} {
		set net_ip $::sth::ospfTopology::userArgsArray(net_ip)
	} else {
		set net_ip 2.0.0.1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix_length)] == 1} {
		set net_prefix_length $::sth::ospfTopology::userArgsArray(net_prefix_length)
	} else {
		set net_prefix_length 64
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip_step)] == 1} {
		set net_ip_step $::sth::ospfTopology::userArgsArray(net_ip_step)
	} else {
		set net_ip_step 0.0.0.1
	}

	if {[info exist ::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)] == 0} {
		set ::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID) 1
	} else {
		incr ::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID) 
	}
	
	set parameterList ""
	lappend parameterList -IfType TRANSIT_NETWORK
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	lappend parameterList -NeighborIfId $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	lappend parameterList -IfId $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	lappend parameterList -Active TRUE
	lappend parameterList -Metric 1
	set routerLsaIF [::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $lsaHnd $parameterList]
        
	set parameterList ""
	lappend parameterList -Options V6BIT|EBIT|RBIT
	lappend parameterList -LinkStateId $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	lappend parameterList -AdvertisingRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	lappend parameterList -Active TRUE
	lappend parameterList -LinkStateId $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	set networkLsa [::sth::sthCore::invoke stc::create "Ospfv3NetworkLsa" -under $ospfHnd $parameterList]
	
	set parameterList ""
	lappend parameterList -RouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	lappend parameterList -Active TRUE
	set drAttachedRouter [::sth::sthCore::invoke stc::create "Ospfv3AttachedRouter" -under $networkLsa $parameterList]

	set parameterList ""
	lappend parameterList -RefAdvertisingRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	lappend parameterList -AdvertisingRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	lappend parameterList -Active TRUE
	lappend parameterList -RefLsType 8194
	lappend parameterList -RefLinkStateId $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	lappend parameterList -LinkStateId $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	set intraLsaBlk [::sth::sthCore::invoke stc::create "Ospfv3IntraAreaPrefixLsaBlk" -under $ospfHnd $parameterList]
		
	set networkBlk [::sth::sthCore::invoke stc::get $intraLsaBlk -children-Ipv6NetworkBlock]
	set parameterList ""
	lappend parameterList -StartIpList $net_prefix
	lappend parameterList -PrefixLength $net_prefix_length
	lappend parameterList -NetworkCount 1
	lappend parameterList -AddrIncrement 1
	lappend parameterList -Active TRUE
	::sth::sthCore::invoke stc::config $networkBlk $parameterList

	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,INTRABLK) $intraLsaBlk
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,DR) $lsaHnd
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,DR_LINK) $routerLsaIF
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,DR_NET_LINK) $drAttachedRouter
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,NET_IP) $net_ip
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,NET_IP_STEP) $net_ip_step
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,NET_IP_COUNT) $net_count	
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,NET_IP_PREFIX) $net_prefix
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,NET_IP_PREFIX_LENGTH) $net_prefix_length	
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsa,IFID) $::sth::ospfTopology::ospfNetworkInfoMap($ospfHnd,IFID)
	
	set tempID $net_ip
	set tempPrefix $net_prefix
	for {set i 0} {$i < $net_count} {incr i} {
		set lsaPair ""
		set parameterList ""
		lappend parameterList -AdvertisingRouterId $tempID
		lappend parameterList -Active TRUE
		lappend parameterList -RouterType 0
		lappend parameterList -Options V6BIT|EBIT|RBIT
		set tempRouterLsa [::sth::sthCore::invoke stc::create "Ospfv3RouterLsa" -under $ospfHnd $parameterList]
		
		set parameterList ""
		lappend parameterList -IfType TRANSIT_NETWORK
		lappend parameterList -Metric 1
		lappend parameterList -IfId $::sth::ospfTopology::networkLSAInfoMap($networkLsa,IFID)
		lappend parameterList -NeighborIfId $::sth::ospfTopology::networkLSAInfoMap($networkLsa,IFID)
		lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
		lappend parameterList -Active TRUE
		set tempOspfRouterLsaIf [::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $tempRouterLsa $parameterList]

        set parameterList ""
        lappend parameterList -RouterId $tempID
        lappend parameterList -Active TRUE
        set tempAttachedRouter [::sth::sthCore::invoke stc::create "Ospfv3AttachedRouter" -under $networkLsa $parameterList]

		lappend lsaPair $tempAttachedRouter $tempRouterLsa
		lappend ::sth::ospfTopology::networkLSAInfoMap($networkLsa,LSAPAIR) $lsaPair

		set tempID [::sth::ospfTopology::IncrementIpV4Address $tempID $net_ip_step]
	}
	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	unset ::sth::ospfTopology::userArgsArray
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $networkLsa	
	
	set subList ""
	keylset subList network_lsa $networkLsa
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList intra_area_prf_lsa $::sth::ospfTopology::networkLSAInfoMap($networkLsa,INTRABLK)
	keylset ::sth::ospfTopology::returnedKeyList network $subList

	return 	$::sth::ospfTopology::returnedKeyList		
}

proc ::sth::ospfTopology::ModifyOSPFv2NetworkRoutes {elementHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(net_dr)] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: net_dr is not allowed in modify mode"]
	}
	
	set ospfHnd [::sth::sthCore::invoke stc::get $elementHnd -parent]
	set lsaHnd $::sth::ospfTopology::networkLSAInfoMap($elementHnd,DR)
	set lsaLinkHnd $::sth::ospfTopology::networkLSAInfoMap($elementHnd,DR_LINK)
	set drLsaLinkHnd $::sth::ospfTopology::networkLSAInfoMap($elementHnd,DR_NET_LINK)
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_count)] == 1} {
		set net_count $::sth::ospfTopology::userArgsArray(net_count)
		set hasChanged 0

		if {$net_count < $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT)} {
			set totalPair [llength $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR)]
			set count 0

			foreach lsaPair $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) {
				if {$count >= $net_count} {
					set routerLsaHnd [lindex $lsaPair 1]
					set networkLinkLsaHnd [lindex $lsaPair 0]
					::sth::sthCore::invoke stc::delete $routerLsaHnd
					::sth::sthCore::invoke stc::delete $networkLinkLsaHnd
				}
				incr count
			}
			if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
			}
			::sth::sthCore::invoke stc::sleep 5
			
			set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) [lrange $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) 0 [expr $net_count - 1]]
		} elseif {$net_count > $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT)} {
			set totalCount [llength $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR)]
			set hasChanged 1
			for {set count $totalCount} {$count < $net_count} {incr count} {
				set lsaPair ""
		
				set parameterList ""
 				lappend parameterList -Active TRUE
 				set networkLsaLinkHnd [::sth::sthCore::invoke stc::create NetworkLsaLink -under $elementHnd $parameterList]
 		
 				lappend lsaPair $networkLsaLinkHnd
 		
				set parameterList ""
				lappend parameterList -Abr FALSE
				lappend parameterList -Asbr FALSE	
				lappend parameterList -Active TRUE
				set tempRouterLsa [::sth::sthCore::invoke stc::create "RouterLsa" -under $ospfHnd $parameterList]
		
				lappend lsaPair $tempRouterLsa

				set parameterList ""
				lappend parameterList -LinkType TRANSIT_NETWORK
				lappend parameterList -Active TRUE
				set tempRouterLsaLink [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $tempRouterLsa $parameterList]
		
				set tempNetworkBlock [::sth::sthCore::invoke stc::get $tempRouterLsaLink -children-Ipv4NetworkBlock]
				set parameterList ""
				lappend parameterList -NetworkCount 1
				lappend parameterList -AddrIncrement 0
				lappend parameterList -Active TRUE
		
				::sth::sthCore::invoke stc::config $tempNetworkBlock $parameterList

 				lappend ::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) $lsaPair				
			}
		}
		
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_COUNT) $net_count
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip)] == 1} {
		set hasChanged 1
		set net_ip $::sth::ospfTopology::userArgsArray(net_ip)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP) $net_ip
	} else {
		set net_ip $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP)
	}
			
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip_step)] == 1} {
		set hasChanged 1
		set net_ip_step $::sth::ospfTopology::userArgsArray(net_ip_step)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_STEP) $net_ip_step
	} else {
		set net_ip_step $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_STEP)
	}			
			
	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix)] == 1} {
		set hasChanged 1
		set net_prefix $::sth::ospfTopology::userArgsArray(net_prefix)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX) $net_prefix
	} else {
		set net_prefix $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX)
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix_length)] == 1} {
		set hasChanged 1
		set net_prefix_length $::sth::ospfTopology::userArgsArray(net_prefix_length)
		set ::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX_LENGTH) $net_prefix_length
	} else {
		set net_prefix_length $::sth::ospfTopology::networkLSAInfoMap($elementHnd,NET_IP_PREFIX_LENGTH)
	}	
			
	if {$hasChanged == 1} {
		set parameterList ""
		lappend parameterList -LinkId $net_prefix
		lappend parameterList -LinkData $net_prefix
		::sth::sthCore::invoke stc::config $lsaLinkHnd $parameterList
	
		set parameterList ""
		lappend parameterList -StartIpList $net_ip
   		set networkBlk [::sth::sthCore::invoke stc::get $lsaLinkHnd -children-Ipv4NetworkBlock]
 		::sth::sthCore::invoke stc::config $networkBlk $parameterList
 
		# Create network lsa
		set parameterList ""
		lappend parameterList -LinkStateId $net_prefix
		lappend parameterList -PrefixLength $net_prefix_length
   		lappend parameterList -AdvertisingRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
   		::sth::sthCore::invoke stc::config $elementHnd $parameterList

		# Create network lsa Link for network lsa under lsaHnd
		set parameterList ""
   		lappend parameterList -LinkId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
 		::sth::sthCore::invoke stc::config $drLsaLinkHnd $parameterList
			
		set tempIPPrefix $net_ip
		set tempLinkData $net_prefix
		for {set i 0} {$i < $net_count} {incr i} {
			set lsaPair [lindex $::sth::ospfTopology::networkLSAInfoMap($elementHnd,LSAPAIR) $i]
			set networkLsaLinkHnd [lindex $lsaPair 0]
			set routerLsaHnd [lindex $lsaPair 1]
				
			set parameterList ""
    		lappend parameterList -LinkId $tempIPPrefix
 			::sth::sthCore::invoke stc::config $networkLsaLinkHnd $parameterList
 		
 			set parameterList ""
			lappend parameterList -AdvertisingRouterId $tempIPPrefix
			::sth::sthCore::invoke stc::config $routerLsaHnd $parameterList
		
			set tempLinkData [::sth::ospfTopology::IncrementIpV4Address $tempLinkData 0.0.0.1]	
 		
			set parameterList ""
			lappend parameterList -LinkId $net_prefix
			lappend parameterList -LinkData $tempLinkData
			set tempRouterLsaLink [::sth::sthCore::invoke stc::get $routerLsaHnd -children-RouterLsaLink]
			::sth::sthCore::invoke stc::config $tempRouterLsaLink $parameterList
		
			set tempNetworkBlock [::sth::sthCore::invoke stc::get $tempRouterLsaLink -children-Ipv4NetworkBlock]
			set parameterList ""
			lappend parameterList -StartIpList $net_prefix
			::sth::sthCore::invoke stc::config $tempNetworkBlock $parameterList

 			set tempIPPrefix [::sth::ospfTopology::IncrementIpV4Address $tempIPPrefix $net_ip_step]		
		}
	}
			
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}

	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	
	set subList ""
	keylset subList network_lsa $elementHnd
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList intra_area_prf_lsa $::sth::ospfTopology::networkLSAInfoMap($elementHnd,INTRABLK)
	keylset ::sth::ospfTopology::returnedKeyList network $subList	
	unset ::sth::ospfTopology::userArgsArray
	
	::sth::sthCore::invoke stc::sleep 5	
		
	return $::sth::ospfTopology::returnedKeyList	
	
}

proc ::sth::ospfTopology::CreateOSPFv2NetworkRoutes {ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(net_dr)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(net_dr)
		set ospfHnd [::sth::sthCore::invoke stc::get $lsaHnd -parent]
	} else {
		return [::sth::ospfTopology::ReportError "ERROR: Missing net_dr"]
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_count)] == 1} {
		set net_count $::sth::ospfTopology::userArgsArray(net_count)
	} else {
		set net_count 1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix)] == 1} {
		set net_prefix $::sth::ospfTopology::userArgsArray(net_prefix)
	} else {
		set net_prefix 1.0.0.1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip)] == 1} {
		set net_ip $::sth::ospfTopology::userArgsArray(net_ip)
	} else {
		set net_ip 2.0.0.1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix_length)] == 1} {
		set net_prefix_length $::sth::ospfTopology::userArgsArray(net_prefix_length)
	} else {
		set net_prefix_length 32
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip_step)] == 1} {
		set net_ip_step $::sth::ospfTopology::userArgsArray(net_ip_step)
	} else {
		set net_ip_step 0.0.0.1
	}	

	
	set parameterList ""
	lappend parameterList -LinkType TRANSIT_NETWORK
	lappend parameterList -LinkId $net_prefix
	lappend parameterList -LinkData $net_prefix
	lappend parameterList -Active TRUE
	
	set lsaLink [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $lsaHnd $parameterList]
	
	set parameterList ""
	lappend parameterList -StartIpList $net_ip
    lappend parameterList -NetworkCount 1
    lappend parameterList -AddrIncrement 0
 	lappend parameterList -Active TRUE
 	
 	set networkBlk [::sth::sthCore::invoke stc::get $lsaLink -children-Ipv4NetworkBlock]
 	::sth::sthCore::invoke stc::config $networkBlk $parameterList
 
# Create network lsa
	set parameterList ""
	lappend parameterList -LinkStateId $net_prefix
	lappend parameterList -PrefixLength $net_prefix_length
    lappend parameterList -AdvertisingRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
    lappend parameterList -Options EBIT
 	lappend parameterList -Active TRUE

	set networkLsaHnd [::sth::sthCore::invoke stc::create "NetworkLsa" -under $ospfHnd $parameterList]

# Create network lsa Link for network lsa under lsaHnd
	set parameterList ""
    lappend parameterList -LinkId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
 	lappend parameterList -Active TRUE
 	
 	set networkLsaLinkHnd [::sth::sthCore::invoke stc::create NetworkLsaLink -under $networkLsaHnd $parameterList]
	
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,INTRABLK) $networkLsaLinkHnd
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,DR) $lsaHnd
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,DR_LINK) $lsaLink
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,DR_NET_LINK) $networkLsaLinkHnd
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,NET_IP) $net_ip
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,NET_IP_STEP) $net_ip_step
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,NET_IP_COUNT) $net_count	
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,NET_IP_PREFIX) $net_prefix
	set ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,NET_IP_PREFIX_LENGTH) $net_prefix_length	
	
# Creaet network lsa links for network lsa
	#set tempIPPrefix [::sth::ospfTopology::IncrementIpV4Address $net_ip $net_ip_step]
	
	set tempIPPrefix $net_ip
	set tempLinkData $net_prefix
	for {set i 0} {$i < $net_count} {incr i} {
		set lsaPair ""
		
		set parameterList ""
    	lappend parameterList -LinkId $tempIPPrefix
 		lappend parameterList -Active TRUE
 	
 		set networkLsaLinkHnd [::sth::sthCore::invoke stc::create NetworkLsaLink -under $networkLsaHnd $parameterList]
 		
 		lappend lsaPair $networkLsaLinkHnd
 		
		set parameterList ""
		lappend parameterList -Abr FALSE
		lappend parameterList -Asbr FALSE	
		lappend parameterList -AdvertisingRouterId $tempIPPrefix	
		lappend parameterList -Active TRUE
		set tempRouterLsa [::sth::sthCore::invoke stc::create "RouterLsa" -under $ospfHnd $parameterList]
		
		lappend lsaPair $tempRouterLsa

		set tempLinkData [::sth::ospfTopology::IncrementIpV4Address $tempLinkData 0.0.0.1]	
 		
		set parameterList ""
		lappend parameterList -LinkType TRANSIT_NETWORK
		lappend parameterList -LinkId $net_prefix
		lappend parameterList -LinkData $tempLinkData 
		lappend parameterList -Active TRUE
		set tempRouterLsaLink [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $tempRouterLsa $parameterList]
		
		set tempNetworkBlock [::sth::sthCore::invoke stc::get $tempRouterLsaLink -children-Ipv4NetworkBlock]
		set parameterList ""
		lappend parameterList -StartIpList $net_prefix
		lappend parameterList -NetworkCount 1
		lappend parameterList -AddrIncrement 0
		lappend parameterList -Active TRUE
		
		::sth::sthCore::invoke stc::config $tempNetworkBlock $parameterList

 		set tempIPPrefix [::sth::ospfTopology::IncrementIpV4Address $tempIPPrefix $net_ip_step]		
 		
 		lappend ::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,LSAPAIR) $lsaPair
 		
	}
    	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	unset ::sth::ospfTopology::userArgsArray
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $networkLsaHnd	
	
	set subList ""
	keylset subList network_lsa $networkLsaHnd
	keylset subList intra_area_prf_lsa $::sth::ospfTopology::networkLSAInfoMap($networkLsaHnd,INTRABLK)
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	
	keylset ::sth::ospfTopology::returnedKeyList network $subList

	return 	$::sth::ospfTopology::returnedKeyList	
} 


proc ::sth::ospfTopology::CreateOSPFv3ExtNssaRoutes {ospfHnd} {
	set configType $::sth::ospfTopology::userArgsArray(type)
	set connectName ""
	if {[string tolower $configType] == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set connectName external_connect
	} else {
		set connectName nssa_connect
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray($connectName)] == 1} {
		set connection $::sth::ospfTopology::userArgsArray($connectName)
		set row [lindex $connection 0]
		set col [lindex $connection 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	} else {
		set row 1
		set col 1
		
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,1,1)
		} else {		
			# fix CR306923057, create default router lsa on the emulated router (no grid to create any simulated routers)
			if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
				set lsaHnd [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
				set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $lsaHnd
			} else {
				set lsaHnd $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
			}
		}
	}
		
	set routerBlockList [::sth::sthCore::invoke stc::get $ospfHnd -children-Ospfv3AsExternalLsaBlock]
	set idList ""
	foreach routerBlock $routerBlockList {
		lappend idList [::sth::sthCore::invoke stc::get $routerBlock -LinkStateId]
	}
	
	if {[llength $idList] != 0} {
		set linkStateId [GetUniqueIDForV3 $idList]
	} else {
		set linkStateId 1
	}	
	
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set bitName "EBIT"
	} else {
		set bitName "NBIT"
	}
	
	set parameterList ""
	set tempRouterType [::sth::sthCore::invoke stc::get $lsaHnd -RouterType]
	if {$tempRouterType != 0} {
		lappend parameterList -RouterType "$tempRouterType|EBIT"
	} else {
		lappend parameterList -RouterType "EBIT"
	}

	lappend parameterList -Options V6BIT|RBIT|$bitName
	if {[catch {::sth::sthCore::invoke stc::config $lsaHnd $parameterList} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}

	set advRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	set parameterList ""
	lappend parameterList -AdvertisingRouterId $advRouterId
	lappend parameterList -LinkStateId $linkStateId
    
    if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
    	set prefix_type external_prefix_type
    	set metric external_prefix_metric
    } else {
    	set prefix_type nssa_prefix_type
    	set metric nssa_prefix_metric    
    }
    
    if {[info exist ::sth::ospfTopology::userArgsArray($prefix_type)] == 1} {
    	if {$::sth::ospfTopology::userArgsArray($prefix_type) == 1} {
    		lappend parameterList -MetricType TRUE 
    	} else {
    		lappend parameterList -MetricType FALSE
    	}
    } else {
    	lappend parameterList -MetricType FALSE 
    }
    
    
    
    if {[info exist ::sth::ospfTopology::userArgsArray($metric)] == 1} {
    	lappend parameterList -Metric $::sth::ospfTopology::userArgsArray($metric)
    }
    
	lappend parameterList -LsType "AS_EXT_LSA"
	 
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set objectName "Ospfv3AsExternalLsaBlock"
	} else {
		set objectName "Ospfv3NssaLsaBlock"	
		lappend parameterList -PrefixOptions 8
	}
	
	if {[catch {::sth::sthCore::invoke stc::create $objectName -under $ospfHnd $parameterList} interAreaHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $interAreaHnd"]
	} else {
		set parameterList ""
		if {[catch {::sth::sthCore::invoke stc::get $interAreaHnd -children-Ipv6NetworkBlock} networkBlock] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
		} else {
			if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
				
				lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(external_prefix_step)
				
				lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(external_number_of_prefix)
				
				lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(external_prefix_length)
				 
				if {[info exist ::sth::ospfTopology::userArgsArray(external_prefix_start)] == 1} {
					lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(external_prefix_start)
				} 
 
			} else {
				lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(nssa_number_of_prefix)
				
				lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(nssa_prefix_length)
				
				lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(nssa_prefix_step)
				if {[info exist ::sth::ospfTopology::userArgsArray(nssa_prefix_start)] == 1} {
					lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(nssa_prefix_start)
				} 
			}
			
			if {[catch {::sth::sthCore::invoke stc::config $networkBlock $parameterList} networkBlock] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
			}
		}
	}
	
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set keyedName external
		set keyedLsaName external_lsas
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set ::sth::ospfTopology::extRouteHndLocationMap($interAreaHnd) [list $row $col]
		}
	} else {
		set keyedName nssa
		set keyedLsaName nssa_lsas
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set ::sth::ospfTopology::nssaRouteHndLocationMap($interAreaHnd) [list $row $col]
		}
	}

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}

	# Make key list
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $interAreaHnd
	set subList ""
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList $keyedLsaName $interAreaHnd
	keylset subList connect_routers $lsaHnd
	
	keylset ::sth::ospfTopology::returnedKeyList $keyedName $subList

	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList
}


proc ::sth::ospfTopology::CreateOSPFv3InterAreaRoutes {ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		set connection $::sth::ospfTopology::userArgsArray(summary_connect)
		set row [lindex $connection 0]
		set col [lindex $connection 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	} else {
		
		set row 1
		set col 1
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,1,1)
		} else {		
			# fix CR306923057, create default router lsa on the emulated router (no grid to create any simulated routers)
			if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
				set lsaHnd [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
				set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $lsaHnd
			} else {
				set lsaHnd $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
			}
		}
	}
	
	set routerBlockList [::sth::sthCore::invoke stc::get $lsaHnd -children-Ospfv3InterAreaPrefixLsaBlk]
	set idList ""
	foreach routerBlock $routerBlockList {
		lappend idList [::sth::sthCore::invoke stc::get $routerBlock -LinkStateId]
	}
	
	if {[llength $idList] != 0} {
		set linkStateId [GetUniqueIDForV3 $idList]
	} else {
		set linkStateId 1
	}
	
	set parameterList ""
	set tempRouterType [::sth::sthCore::invoke stc::get $lsaHnd -RouterType]
	if {$tempRouterType != 0} {
		lappend parameterList -RouterType "$tempRouterType|BBIT"
	} else {
		lappend parameterList -RouterType "BBIT"
	}
	
	lappend parameterList -Options V6BIT|EBIT|RBIT
	
	if {[catch {::sth::sthCore::invoke stc::config $lsaHnd $parameterList} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	set advRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	
	set parameterList ""
	lappend parameterList -AdvertisingRouterId $advRouterId
	lappend parameterList -LinkStateId $linkStateId
	lappend parameterList -RefLsType 0
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_metric)] == 1} {
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray(summary_prefix_metric)
	}
	lappend parameterList -Active TRUE
	if {[catch {::sth::sthCore::invoke stc::create "Ospfv3InterAreaPrefixLsaBlk" -under $ospfHnd $parameterList} interAreaHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $interAreaHnd"]
	} else {
		set parameterList ""
		if {[catch {::sth::sthCore::invoke stc::get $interAreaHnd -children-Ipv6NetworkBlock} networkBlock] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
		} else {
			if {[info exist ::sth::ospfTopology::userArgsArray(summary_number_of_prefix)] == 1} {
				lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(summary_number_of_prefix)
			}
			
			if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_length)] == 1} { 
				lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(summary_prefix_length)
			}
			
			if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_step)] == 1} {
				lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(summary_prefix_step)
			}
		
			lappend parameterList -Active TRUE
			
			if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_start)] == 1} {
				lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(summary_prefix_start)
			} 

			if {[catch {::sth::sthCore::invoke stc::config $networkBlock $parameterList} networkBlock] == 1} {
				return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
			}
		}
	}
	if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
		set ::sth::ospfTopology::sumRouteHndLocationMap($interAreaHnd) [list $row $col]
	}
	

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
		
	# Make key list
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $interAreaHnd
	
	set subList ""
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList summary_lsas $interAreaHnd
	keylset subList connect_routers $lsaHnd
	
	keylset ::sth::ospfTopology::returnedKeyList summary $subList	

	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::ReportError {msg} {
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::FAILURE
	keylset ::sth::ospfTopology::returnedKeyList log $msg
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::ModifyOSPFv3Grid {elementHnd} {
	set ospfHnd $::sth::ospfTopology::routerGridHndMap($elementHnd)
	set linkType ""
	set row ""
	set col ""

	set hasChanged 0
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 1} {
		set hasChanged 1
		set prefix_start $::sth::ospfTopology::userArgsArray(grid_prefix_start)
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX) $::sth::ospfTopology::userArgsArray(grid_prefix_start)
	} else {
		set prefix_start $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 1} {
		set hasChanged 1
		set prefix_step $::sth::ospfTopology::userArgsArray(grid_prefix_step)
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP) $::sth::ospfTopology::userArgsArray(grid_prefix_step)
	} else {
		set prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_length)] == 1} { 
		set hasChanged 1
		set prefix_length $::sth::ospfTopology::userArgsArray(grid_prefix_length)
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH) $::sth::ospfTopology::userArgsArray(grid_prefix_length)
	} else {
		set prefix_length $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)
	}

	
	set linkType $::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE)
	set row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
	set col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 1} {
		set newCol $::sth::ospfTopology::userArgsArray(grid_col)
	} else {
		set newCol $col
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 1} {
		set newRow $::sth::ospfTopology::userArgsArray(grid_row)
	} else {
		set newRow $row
	}
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW) $newRow
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL) $newCol
	
	if {$newRow != $row || $newCol != $col} {
		::sth::ospfTopology::ModifyGridSize $newRow $newCol $row $col $ospfHnd
	} else {
		::sth::ospfTopology::ModifyGridContent $ospfHnd $newRow $newCol
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] != 0} {
		set connect_Row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
		set connect_Col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_Row,$connect_Col)
		if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)] == 1} {
			::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
		}
		
		if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)] == 1} {
			::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
			unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
		}
		set connectHnd ""
		#Link the connect session.
		::sth::ospfTopology::LinkOSPFv3ConnectSession $ospfHnd connectHnd
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_disconnect)] != 0} {
		if {$::sth::ospfTopology::userArgsArray(grid_disconnect) == $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND) } {
			
			set connect_row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER) 
			set connect_col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)
			
			::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
			unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
			
			set erHnd $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND)
			
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)] == 1} {
				if {[llength $::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)] > 0} {
					foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB) {
						::sth::sthCore::invoke stc::delete $stubHnd
					}
					unset ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)
				}
			}
		} else {
			return [::sth::ospfTopology::ReportError "ERROR: $::sth::ospfTopology::userArgsArray(grid_disconnect) is not the connect session"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_stub_per_router)] == 1} {
		set row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
		set col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
		set stubPerRouter $::sth::ospfTopology::userArgsArray(grid_stub_per_router)
		if {$stubPerRouter != $::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB)} {
			if {$::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB) != 0} {
				for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
					for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
						set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
						foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) {
							::sth::sthCore::invoke stc::delete $stubHnd
						}
						set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) ""
						set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB) 0
					}
				}
				::sth::sthCore::doStcApply
				for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
					for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {				
						set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
						set prefix_start [::sth::ospfTopology::CreateIntraNetwork $ospfHnd $lsaHnd $prefix_start $prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH) $::sth::ospfTopology::userArgsArray(grid_stub_per_router) TRUE]
						::sth::sthCore::invoke "stc::sleep 2"
					}
				}
				
			}
			set ::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB) $::sth::ospfTopology::userArgsArray(grid_stub_per_router)
		} else {
			if {$isChanged == 1} {
				for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
					for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {				
						set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex) 
						set stubHndList $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB)
						foreach stubHnd $stubHndList {
							set link [::sth::sthCore::invoke stc::get $stubHnd -children-ipv6NetworkBlock]
							::sth::sthCore::invoke stc::config $link "-StartIpList $prefix_start -NetworkCount $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB) -PrefixLength $prefix_length"
							set prefix_start [::sth::ospfTopology::incrementIpV6Address $prefix_start $prefix_step]
						}
					}
				}
			}						
		}
	} 
	
	::sth::ospfTopology::ModifyOSPFv3Link $newRow $newCol $ospfHnd
	
	::sth::sthCore::doStcApply
	
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	set subList ""
	
	for {set rowIndex 1} {$rowIndex <= $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			keylset subList router.$rowIndex.$colIndex $lsaHnd
		}
	}
	
	keylset ::sth::ospfTopology::returnedKeyList grid $subList
	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList		
}

proc ::sth::ospfTopology::ModifyOSPFv3Link {row col ospfHnd} {
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			::sth::ospfTopology::DeleteLink $lsaHnd
		}
	}
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex) 
			# Create right LSA Link
			if {[expr $colIndex + 1] <= $col} {
				::sth::ospfTopology::CreateOSPFv3LSAIF $lsaHnd $rowIndex [expr $colIndex + 1] $ospfHnd
			}

			if {[expr $rowIndex + 1] <= $row} {
				::sth::ospfTopology::CreateOSPFv3LSAIF $lsaHnd [expr $rowIndex + 1] $colIndex $ospfHnd
			}
		}
	}	
}

proc ::sth::ospfTopology::ModifyOSPFv3LSAIF {lsaHnd row col parent} {
	set nextLsaHnd $::sth::ospfTopology::topologyHndMap($parent,$row,$col)
	set lsaLinkList [::sth::sthCore::invoke stc::get $lsaHnd -children-Ospfv3RouterLsaIf]
	set nextLsaLinkList [::sth::sthCore::invoke stc::get $nextLsaHnd -children-Ospfv3RouterLsaIf]
	
	if {[llength $lsaLinkList] == 0} {
		set ifId 1
	} else {
		foreach lsaLink $lsaLinkList {
			lappend idList [::sth::sthCore::invoke stc::get $lsaLink -ifid]
		}
		set ifId [GetUniqueIDForV3 $idList]
	}
	
	if {[llength $nextLsaLinkList] == 0} {
		set nextIfId 1
	} else {
		foreach lsaLink $nextLsaLinkList {
			lappend idList [::sth::sthCore::invoke stc::get $lsaLink -ifid]
		}
		set nextIfId [GetUniqueIDForV3 $idList]
	}
				
	set parameterList ""
	lappend parameterList -IfId $ifId
	lappend parameterList -NeighborIfId $nextIfId
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $nextLsaHnd -AdvertisingRouterId]
	if {[catch {::sth::sthCore::invoke stc::config $lsaHnd $parameterList} lsaLink] == 1} {
		return [::sth::ospfTopology::ReportError "Error: $lsaLink"]
	}
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) $lsaLink
	
	set parameterList ""
	lappend parameterList -NeighborIfId $ifId
	lappend parameterList -IfId $nextIfId
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	if {[catch {::sth::sthCore::invoke stc::config $nextLsaHnd $parameterList} lsaLink] == 1} {
		return [::sth::ospfTopology::ReportError "Error: $lsaLink"]
	}	
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) $lsaLink	
}



proc ::sth::ospfTopology::ModifyGridContent {ospfHnd row col} {
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id)] == 1} {
		set startID $::sth::ospfTopology::userArgsArray(grid_router_id)
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id_step)] == 1} {
			set idStep $::sth::ospfTopology::userArgsArray(grid_router_id_step)
			set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROUTER_STEP) $idStep
		} else {
			set idStep $::sth::ospfTopology::gridInfoMap($ospfHnd,ROUTER_STEP)
		}
		
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,INIROUTERID) $startID
		
		for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
			for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				::sth::sthCore::invoke stc::config $lsaHnd "-AdvertisingRouterId $startID"
				set startID [::sth::ospfTopology::IncrementIpV4Address $startID $idStep]
			}
		}
		
		set connectToERRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
		set connectToERCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
			
		set connectToERLsa $::sth::ospfTopology::topologyHndMap($ospfHnd,$connectToERRow,$connectToERCol)
		set linkHnd $::sth::ospfTopology::routerLSAInfoMap($connectToERLsa,ERTOSR_LINKS)
		if {$::sth::ospfTopology::currentOSPFVersion == $::sth::ospfTopology::OSPFV2_STR} {
			set parameterList ""
			lappend parameterList -LinkId [::sth::sthCore::invoke stc::get $connectToERLsa -AdvertisingRouterId]
			::sth::sthCore::invoke stc::config $linkHnd $parameterList
		} else {
			set parameterList ""
			lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $connectToERLsa -AdvertisingRouterId]
			::sth::sthCore::invoke stc::config $linkHnd $parameterList
		}
	
	}
}


proc ::sth::ospfTopology::ModifyOSPFv2Grid {elementHnd} {

	set ospfHnd $::sth::ospfTopology::routerGridHndMap($elementHnd)
	
	set linkType ""
	set row ""
	set col ""
	
	set linkType $::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE)
	set row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
	set col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 1} {
		set newCol $::sth::ospfTopology::userArgsArray(grid_col)
	} else {
		set newCol $col
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 1} {
		set newRow $::sth::ospfTopology::userArgsArray(grid_row)
	} else {
		set newRow $row
	}
	
	if {$newRow != $row || $newCol != $col} {
		::sth::ospfTopology::ModifyGridSize $newRow $newCol $row $col $ospfHnd
	} else {
		#Modify Grid Content 
		::sth::ospfTopology::ModifyGridContent $ospfHnd $newRow $newCol
	}
	
	set row $newRow
	set col $newCol

	# Store new coordinations
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW) $newRow
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL) $newCol
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 1} {
		set prefix_start $::sth::ospfTopology::userArgsArray(grid_prefix_start)
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX) $prefix_start
	} else {
		set prefix_start $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX)
	}
			
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 1} {
		set prefix_step $::sth::ospfTopology::userArgsArray(grid_prefix_step)
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP) $prefix_step
	} else {
		set prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_length)] == 1} { 
		set prefix_length $::sth::ospfTopology::userArgsArray(grid_prefix_length)
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH) $prefix_length
	} else {
		set prefix_length $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1} {
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 0} {
			return [::sth::ospfTopology::ReportError "ERROR: grid_connect is required for modifying grid_connect_session"]
		} else {
			set connect_row [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 0]
			set connect_col [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 1]
			set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER) $connect_row
			set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER) $connect_col
			set connectLsa $::sth::ospfTopology::userArgsArray(grid_connect_session)
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_link_type)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_link_type) != $linkType} {
			if {$::sth::ospfTopology::userArgsArray(grid_link_type) == "ptop_unnumbered"} {
				# Change from p2p number to p2p unnumbered
				::sth::ospfTopology::ModifyGridFromNumberToUnnumber $ospfHnd $row $col TRUE
				set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE) "ptop_unnumbered"
			} else {				
				::sth::ospfTopology::ModifyGridFromUnnumberToNumber $ospfHnd $row $col TRUE
				set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE) "ptop_numbered"				
			}
		} else {
			if {$::sth::ospfTopology::userArgsArray(grid_link_type) == "ptop_unnumbered"} {
				::sth::ospfTopology::ModifyGridFromNumberToUnnumber $ospfHnd $row $col			
			} else {
				::sth::ospfTopology::ModifyGridFromUnnumberToNumber $ospfHnd $row $col		
			}
		}
	} else {
		if {$::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE) == "ptop_unnumbered"} {
			::sth::ospfTopology::ModifyGridFromNumberToUnnumber $ospfHnd $row $col TRUE		
		} else {
			::sth::ospfTopology::ModifyGridFromUnnumberToNumber $ospfHnd $row $col
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_stub_per_router)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_stub_per_router) != $::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB)} {
			if {$::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB) != 0} {
				set row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
				set col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
				for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
					for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
						set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
						foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) {
							::sth::sthCore::invoke stc::delete $stubHnd
						}
						set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) ""
						set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB) 0
					}
				}
				set prefix_length [::ip::lengthToMask $prefix_length]
				for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
					for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {				
						set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex) 	
						for {set i 0} {$i < $::sth::ospfTopology::userArgsArray(grid_stub_per_router)} {incr i} {
							::sth::ospfTopology::CreateStubNetwork $prefix_start $prefix_length $lsaHnd TRUE
							set prefix_start [::sth::ospfTopology::IncrementIpV4Address $prefix_start $prefix_step]
						}				
					}
				}
				
			}
			set ::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB) $::sth::ospfTopology::userArgsArray(grid_stub_per_router)
		} else {
			set prefix_length [::ip::lengthToMask $prefix_length]
			for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
				for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {				
					set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex) 
					set stubHndList $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB)
					foreach stubHnd $stubHndList {
						::sth::sthCore::invoke stc::config $stubHnd "-LinkId $prefix_start -LinkData $prefix_length"
						
						set link [::sth::sthCore::invoke stc::get $stubHnd -children-ipv4NetworkBlock]
						::sth::sthCore::invoke stc::config $link "-StartIpList $prefix_start"
						set prefix_start [::sth::ospfTopology::IncrementIpV4Address $prefix_start $prefix_step]
					}
				}
			}			
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_disconnect)] != 0} {
		if {$::sth::ospfTopology::userArgsArray(grid_disconnect) == $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND) } {
			set connect_row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER) 
			set connect_col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)
			::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
			unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)			
			set erHnd $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND)
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)] == 1} {
				if {[llength $::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)] > 0} {
					foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB) {
						::sth::sthCore::invoke stc::delete $stubHnd
					}
					unset ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)
				}
			}
			
		} else {
			return [::sth::ospfTopology::ReportError "ERROR: $::sth::ospfTopology::userArgsArray(grid_disconnect) is not the connect session"]
		}
	}
	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}	
	
	# Make keyed list	
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $elementHnd
	set subList ""
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			keylset subList router.$rowIndex.$colIndex $lsaHnd
		}
	}
	
	keylset ::sth::ospfTopology::returnedKeyList grid $subList
	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::ModifyGridFromUnnumberToNumber {ospfHnd row col {modifyERLink FALSE}} {

	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			::sth::ospfTopology::DeleteLink $lsaHnd
		}
	}

	array set hndsNetworkMap ""
	array set hndsRouterTEMap ""
	set currentPrefix [::sth::ospfTopology::PrepareP2PNumberLinking hndsNetworkMap $row $col $ospfHnd]
		
	::sth::ospfTopology::CreateNumberLink hndsNetworkMap $row $col $ospfHnd		

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1 || $modifyERLink == "TRUE"} {
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1} {
			if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 0} {
				return [::sth::ospfTopology::ReportError "ERROR: grid_connect is required for modifying grid_connect_session"]
			} else {
				set connect_row [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 0]
				set connect_col [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 1]
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)
				set connectLsa $::sth::ospfTopology::userArgsArray(grid_connect_session)
				
				if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)] == 1} {
					::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
					unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
				}
			
				if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)] == 1} {
					::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
					unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
				}
				
				set currentPrefix [::sth::ospfTopology::ConnectSessionWithGridForP2PNumbered $currentPrefix $connect_row $connect_col $ospfHnd $connectLsa]
			}
		} elseif {$modifyERLink == TRUE} {
			set connect_row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
			set connect_col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)
			set connectLsa $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND)
			
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)] == 1} {
				::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
				unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
			}
			
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)] == 1} {
				::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
				unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			}
			::sth::ospfTopology::ConnectSessionWithGridForP2PNumbered $currentPrefix $connect_row $connect_col $ospfHnd $connectLsa
		}
	}
}

proc ::sth::ospfTopology::ModifyGridFromNumberToUnnumber {ospfHnd row col {modifyERLink FALSE}} {
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			::sth::ospfTopology::DeleteLink $lsaHnd
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB)] == 1} {
				foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) {
					::sth::sthCore::invoke stc::delete $stubHnd
				}
				set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) ""
			}
		}
	}
	
	set erHnd $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND)
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)] == 1} {
		foreach stubHnd $::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB) {
			::sth::sthCore::invoke stc::delete $stubHnd
		}	
		unset ::sth::ospfTopology::routerLSAInfoMap($erHnd,STUB)	
	}
	
	::sth::ospfTopology::LinkGrid $row $col $ospfHnd
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1 || $modifyERLink == TRUE} {
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1} {
			set connectLsa $::sth::ospfTopology::userArgsArray(grid_connect_session)
			set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $connectLsa
			if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 1} {
				set ::sth::ospfTopology::grid_connect $::sth::ospfTopology::userArgsArray(grid_connect)
				# Connect lsa to the grid
				set connect_row [lindex $::sth::ospfTopology::grid_connect 0]
				set connect_col [lindex $::sth::ospfTopology::grid_connect 1]
				set oldConnect_row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
				set oldConnect_col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$oldConnect_row,$oldConnect_col)
				if {$connect_row > $row || $connect_col > $col} {
					return [::sth::ospfTopology::ReportError "Error: grid_connect number is not compatabile with max row and max column"]
				}
				
				if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)] == 1} {
					::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
					unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
				}
			
				if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)] == 1} {
					::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
					unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
				}
						
				::sth::ospfTopology::ConnectSessionWithGridForP2PUnnumbered $connect_row $connect_col $ospfHnd $connectLsa	
				set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $connectLsa
			}
		} elseif {$modifyERLink == TRUE} {
			set connect_row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
			set connect_col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)
			set connectLsa $::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND)
			
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)] == 1} {
				::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
				unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS)
			}
			
			if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)] == 1} {
				::sth::sthCore::invoke stc::delete $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
				unset ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS)
			}
			::sth::ospfTopology::ConnectSessionWithGridForP2PUnnumbered $connect_row $connect_col $ospfHnd $connectLsa
		}
	}
	
}

proc ::sth::ospfTopology::DeleteLink {lsaHnd} {
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS)] == 1} {
		foreach linkHnd $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) {
			::sth::sthCore::invoke stc::delete $linkHnd
		}
	}
	# reset mapping
	set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) ""
}

proc ::sth::ospfTopology::CreateOSPFv2Grid {ospfHnd} {

	
	if {$::sth::ospfTopology::userArgsArray(grid_te) == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_link_type) == "ptop_unnumbered"} {
			return [::sth::ospfTopology::ReportError "ERROR: grid_link_type should be ptop_numbered when grid_te is 1"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 1} {
		set col $::sth::ospfTopology::userArgsArray(grid_col)
	} else {
		set col 1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 1} {
		set row $::sth::ospfTopology::userArgsArray(grid_row)
	} else {
		set row 1
	}
	
	# Create grid
	if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,GRIDHND)] == 0} {
		if {[::sth::ospfTopology::CreateGrid $row $col $ospfHnd] == $::sth::sthCore::FAILURE} {
			return [::sth::ospfTopology::ReportError "Create Grid returns failure"]	
		}
	} else {
		return [::sth::ospfTopology::ReportError "Grid is already created under $ospfHnd"]	
	}
	
	
	set lsaList [::sth::sthCore::invoke stc::get $ospfHnd -children-routerLsa]
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 0} {
		if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
			set connectLsa [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
			set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $connectLsa
		} else {
			set connectLsa $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
		}	
	} else {
		set connectLsa $::sth::ospfTopology::userArgsArray(grid_connect_session)
		if {[lsearch $lsaList $connectLsa] < 0} {
			return [::sth::ospfTopology::ReportError "ERROR: $connectLsa is not under $ospfHnd"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_link_type)] == 0} {
		set ::sth::ospfTopology::userArgsArray(grid_link_type) "ptop_unnumbered"
		set linkType "ptop_unnumbered"
	} else {
		if {$::sth::ospfTopology::userArgsArray(grid_link_type) == "ptop_unnumbered"} {
			set linkType "ptop_unnumbered"
		} else {
			set linkType "ptop_numbered"	
		}		
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 1} {
		set prefix_start $::sth::ospfTopology::userArgsArray(grid_prefix_start)
	} else {
		set prefix_start "192.0.0.1"
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 1} {
		set prefix_step $::sth::ospfTopology::userArgsArray(grid_prefix_step)
	} else {
		set prefix_step "0.0.0.1"
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_length)] == 1} { 
		set prefix_length $::sth::ospfTopology::userArgsArray(grid_prefix_length)
	} else {
		set prefix_length "24"
	}
		
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX) $prefix_start
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH) $prefix_length
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP) $prefix_step
	
	set currentPrefix $prefix_start
	
	if {[string tolower $::sth::ospfTopology::userArgsArray(grid_link_type)] == "ptop_unnumbered"} {
		::sth::ospfTopology::LinkGrid $row $col $ospfHnd
	
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 1} {
			set ::sth::ospfTopology::grid_connect $::sth::ospfTopology::userArgsArray(grid_connect)
		}
		
		# Connect lsa to the grid
		set connect_row [lindex $::sth::ospfTopology::grid_connect 0]
		set connect_col [lindex $::sth::ospfTopology::grid_connect 1]
		if {$connect_row > $row || $connect_col > $col} {
			return [::sth::ospfTopology::ReportError "Error: grid_connect number is not compatabile with max row and max column"]
		}
	
		::sth::ospfTopology::ConnectSessionWithGridForP2PUnnumbered $connect_row $connect_col $ospfHnd $connectLsa
	
		set ::sth::ospfTopology::isGridCreate $::sth::ospfTopology::TRUE

	} elseif {[string tolower $::sth::ospfTopology::userArgsArray(grid_link_type)] == "ptop_numbered"} {
		array set hndsNetworkMap ""
		array set hndsRouterTEMap ""
		set currentPrefix [::sth::ospfTopology::PrepareP2PNumberLinking hndsNetworkMap $row $col $ospfHnd]
		
		::sth::ospfTopology::CreateNumberLink hndsNetworkMap $row $col $ospfHnd	
	
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 1} {
			set ::sth::ospfTopology::grid_connect $::sth::ospfTopology::userArgsArray(grid_connect)
		}
		
		# Connect lsa to the grid
		set connect_row [lindex $::sth::ospfTopology::grid_connect 0]
		set connect_col [lindex $::sth::ospfTopology::grid_connect 1]
		if {$connect_row > $row || $connect_col > $col} {
			return [::sth::ospfTopology::ReportError "Error: grid_connect number is not compatabile with max row and max column"]
		}	
		
		# Create link on connect session
		#set currentPrefix [::sth::ospfTopology::IncrementIpV4Address $currentPrefix $::sth::ospfTopology::userArgsArray(grid_prefix_step)]
		set currentPrefix [::sth::ospfTopology::ConnectSessionWithGridForP2PNumbered $currentPrefix $connect_row $connect_col $ospfHnd $connectLsa]
	

	}	
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_stub_per_router)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_stub_per_router) > 0} {
			set prefix_start $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX) 
			set prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP)
			set prefix_length [::ip::lengthToMask $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)]
			set ::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB)  $::sth::ospfTopology::userArgsArray(grid_stub_per_router)
			#Create Stub Network
			for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
				for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
					set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
					for {set i 0} {$i < $::sth::ospfTopology::userArgsArray(grid_stub_per_router)} {incr i} {
						::sth::ospfTopology::CreateStubNetwork $currentPrefix $prefix_length $lsaHnd TRUE
						set currentPrefix [::sth::ospfTopology::IncrementIpV4Address $currentPrefix $prefix_step]
					}
				}
			}
		}
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB) 0
	}

	# Create TE for each router
	if {$::sth::ospfTopology::userArgsArray(grid_te) == 1} {
		#::sth::ospfTopology::CreateGridRouterLinkTEs $row $col $ospfHnd hndsNetworkMap
		::sth::ospfTopology::CreateGridTEs $row $col $ospfHnd $connectLsa
	}
	
	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
	#	return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE) $linkType
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW) $row
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL) $col

	# Make keyed list	
	set gridHndName [::sth::ospfTopology::GenerateGridHnd $ospfHnd]
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $gridHndName
	set subList ""
	keylset subList connected_session.$connectLsa.row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
	keylset subList connected_session.$connectLsa.col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			keylset subList router.$rowIndex.$colIndex $lsaHnd
		}
	}
	
	keylset ::sth::ospfTopology::returnedKeyList grid $subList

	unset ::sth::ospfTopology::userArgsArray
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,GRIDHND) $gridHndName
	
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::CreateRouterTlv {lsaHnd ospfHnd advId} {
	set parameterList ""
	lappend parameterList -Active TRUE
	lappend parameterList -AdvertisingRouterId $advId
	lappend parameterList -Options EBIT|OBIT
	
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE)] == 0} {
		lappend parameterList -Instance 0
		lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE) 0
	} else {
		set instance [GetUniqueIDForV3 $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE)]
		lappend parameterList -Instance $instance
		lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE) $instance 
	}
	
	set teLsaHnd [::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd $parameterList]
	
	set parameterList ""
	lappend parameterList -RouterAddr $advId
	lappend parameterList -Active TRUE
	set routerTlv [::sth::sthCore::invoke stc::create "RouterTlv" -under $teLsaHnd $parameterList]
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ROUTER_TELSA) $teLsaHnd
}



proc ::sth::ospfTopology::CreateGridTEs {row col ospfHnd connectLsa} {
	
	::sth::ospfTopology::InitLinkTEParam $ospfHnd
	
	set advId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
	::sth::ospfTopology::CreateRouterTlv $connectLsa $ospfHnd $advId
	

	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			set advId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
			::sth::ospfTopology::CreateRouterTlv $lsaHnd $ospfHnd $advId
		}
	}
	
	set connect_row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
	set connect_col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
	
	::sth::ospfTopology::CreateLinkTlv $connect_row $connect_col $ospfHnd $connectLsa
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			if {[expr $colIndex + 1] <= $col} {
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				::sth::ospfTopology::CreateLinkTlv $rowIndex [expr $colIndex + 1] $ospfHnd $lsaHnd
			}
			
			if {[expr $rowIndex + 1] <= $row} {
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				::sth::ospfTopology::CreateLinkTlv [expr $rowIndex + 1] $colIndex $ospfHnd $lsaHnd
			}
		}
	}
}

proc ::sth::ospfTopology::InitLinkTEParam {ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_max_bw)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TE_MAX_BW) $::sth::ospfTopology::userArgsArray(link_te_max_bw)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TE_MAX_BW) 100
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_max_resv_bw)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TE_MAX_RESV_BW) $::sth::ospfTopology::userArgsArray(link_te_max_resv_bw)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TE_MAX_RESV_BW) 100
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority0)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_0) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority0)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_0) 10000
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority1)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_1) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority1)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_1) 10000
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority2)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_2) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority2)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_2) 10000
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority3)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_3) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority3)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_3) 10000
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority4)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_4) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority4)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_4) 10000
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority5)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_5) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority5)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_5) 10000
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority6)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_6) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority6)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_6) 10000
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority7)] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_7) $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority7)
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,BW_7) 10000
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(link_te_admin_group)	] == 1} {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,ADMIN_GP) $::sth::ospfTopology::userArgsArray(link_te_admin_group)	
	} else {
		set ::sth::ospfTopology::gridInfoMap($ospfHnd,ADMIN_GP) 1
	}	
						
}

proc ::sth::ospfTopology::ConfigGirdLinkTEParam {linkTlv ospfHnd} {
	set teParam [::sth::sthCore::invoke stc::get $linkTlv -children-TeParams]
	set parameterList ""
	lappend parameterList -TeMaxBandwidth $::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TE_MAX_BW)
	lappend parameterList -TeRsvrBandwidth $::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TE_MAX_RESV_BW)
	lappend parameterList -TeUnRsvrBandwidth0 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_0)
	lappend parameterList -TeUnRsvrBandwidth1 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_1)
	lappend parameterList -TeUnRsvrBandwidth2 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_2)
	lappend parameterList -TeUnRsvrBandwidth3 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_3)	
	lappend parameterList -TeUnRsvrBandwidth4 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_4)
	lappend parameterList -TeUnRsvrBandwidth5 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_5)
	lappend parameterList -TeUnRsvrBandwidth6 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_6)
	lappend parameterList -TeUnRsvrBandwidth7 $::sth::ospfTopology::gridInfoMap($ospfHnd,BW_7)	
	lappend parameterList -Active TRUE
	lappend parameterList -TeGroup $::sth::ospfTopology::gridInfoMap($ospfHnd,ADMIN_GP)
	
	::sth::sthCore::invoke stc::config $teParam $parameterList
}

proc ::sth::ospfTopology::CreateLinkTlv {row col ospfHnd lsaHnd} {
	set nextLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	
	set linkPair $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,$nextLsaHnd,LINK_PAIR)
	
	set adv [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	set addr [::sth::sthCore::invoke stc::get [lindex $linkPair 1] -LinkId]
	set nextAdv [::sth::sthCore::invoke stc::get $nextLsaHnd -AdvertisingRouterId]
	set nextAddr [::sth::sthCore::invoke stc::get [lindex $linkPair 0] -LinkId]
	
	# lsaHnd
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE)] == 0} {
		lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE) 0
	} else {
		set instance [GetUniqueIDForV3 $::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE)]
		lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,INSTANCE) $instance 
	}
	
	set parameterList ""
	if {$::sth::ospfTopology::userArgsArray(link_te_type) == "ptop"} {
		lappend parameterList -LinkType POINT_TO_POINT
	} else {
		lappend parameterList -LinkType MULTIACCESS
	}	
			
	set teLsa [::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd "-Instance $instance -AdvertisingRouterId $nextAdv"]
	set linkTlv [::sth::sthCore::invoke stc::create "LinkTlv" -under $teLsa "-LinkId $adv $parameterList"]
	set teParams [::sth::sthCore::invoke stc::get $linkTlv -children-TeParams]
	::sth::sthCore::invoke stc::config $teParams "-TeLocalIpv4Addr $addr -TeRemoteIpv4Addr $nextAdv"

	::sth::ospfTopology::ConfigGirdLinkTEParam $linkTlv $ospfHnd
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,LINK_TELSA) $teLsa
	
	# nextLsaHnd
	if {[info exist ::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,INSTANCE)] == 0} {
		lappend $::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,INSTANCE) 0
	} else {
		set instance [GetUniqueIDForV3 $::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,INSTANCE)]
		lappend $::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,INSTANCE) $instance 
	}

	set parameterList ""
	if {$::sth::ospfTopology::userArgsArray(link_te_type) == "ptop"} {
		lappend parameterList -LinkType POINT_TO_POINT
	} else {
		lappend parameterList -LinkType MULTIACCESS
	}	

	set teLsa [::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd "-Instance $instance -AdvertisingRouterId $adv"]
	set linkTlv [::sth::sthCore::invoke stc::create "LinkTlv" -under $teLsa "-LinkId $nextAdv $parameterList"]
	set teParams [::sth::sthCore::invoke stc::get $linkTlv -children-TeParams]
	::sth::sthCore::invoke stc::config $teParams "-TeLocalIpv4Addr $nextAddr -TeRemoteIpv4Addr $addr"
	
	::sth::ospfTopology::ConfigGirdLinkTEParam $linkTlv $ospfHnd
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,LINK_TELSA) $teLsa	
}

proc ::sth::ospfTopology::CreateGridRouterLinkTEs {row col ospfHnd hndsNetworkMap} {
	upvar 1 $hndsNetworkMap hndsMap
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			::sth::ospfTopology::CreateRouterTEs $lsaHnd $ospfHnd
		}
	}
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			if {[expr $colIndex + 1] <= $col} {
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				::sth::ospfTopology::CreateLinkTEs $rowIndex [expr $colIndex + 1] $ospfHnd $lsaHnd hndsMap
			}
			
			if {[expr $rowIndex + 1] <= $row} {
				set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				::sth::ospfTopology::CreateLinkTEs [expr $rowIndex + 1] $colIndex $ospfHnd $lsaHnd hndsMap
			}
		}
	}
	
}

proc ::sth::ospfTopology::CreateLinkTEs {row col ospfHnd lsaHnd hndsNetworkMap} {
	upvar 1 $hndsNetworkMap hndsMap
	set instance 1
	set nextLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	set networkGroup [lindex $hndsMap($lsaHnd,$nextLsaHnd) 0]
	set adv [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	set addr [::sth::ospfTopology::IncrementIpV4Address $networkGroup 0.0.0.1]
	set nextAddr [::sth::ospfTopology::IncrementIpV4Address $networkGroup 0.0.0.2]
	set nextAdv [::sth::sthCore::invoke stc::get $nextLsaHnd -AdvertisingRouterId]
	
	set teLsa [::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd "-Instance $instance -AdvertisingRouterId $nextAdv"]
	set linkTlv [::sth::sthCore::invoke stc::create "LinkTlv" -under $teLsa "-LinkId $adv -LinkType POINT_TO_POINT"]
	set teParams [::sth::sthCore::invoke stc::get $linkTlv -children-TeParams]
	::sth::sthCore::invoke stc::config $teParams "-TeLocalIpv4Addr $addr -TeRemoteIpv4Addr $nextAdv"
	
	incr instance
	set teLsa [::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd "-Instance $instance -AdvertisingRouterId $adv"]
	set linkTlv [::sth::sthCore::invoke stc::create "LinkTlv" -under $teLsa "-LinkId $nextAdv -LinkType POINT_TO_POINT"]
	set teParams [::sth::sthCore::invoke stc::get $linkTlv -children-TeParams]
	::sth::sthCore::invoke stc::config $teParams "-TeLocalIpv4Addr $nextAddr -TeRemoteIpv4Addr $addr"
}

proc ::sth::ospfTopology::CreateRouterTEs {lsaHnd ospfHnd} {
	set advId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	set parameterList ""
	lappend parameterList -Instance 0
	lappend parameterList -AdvertisingRouterId $advId
	lappend parameterList -Active TRUE
	set teLsa [::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd $parameterList]

	set parameterList ""
	lappend parameterList -RouterAddr $advId
	lappend parameterList -Active TRUE
	set routerTlv [::sth::sthCore::invoke stc::create "RouterTlv" -under $teLsa $parameterList]
}

proc ::sth::ospfTopology::CreateStubNetwork {currentPrefix prefix_length lsaHnd {add FALSE}} {
	set parameterList ""
	lappend parameterList -LinkType STUB_NETWORK
	lappend parameterList -LinkId $currentPrefix
	lappend parameterList -LinkData $prefix_length
	set link [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $lsaHnd $parameterList]
	
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-ipv4NetworkBlock]
	set parameterList ""
	lappend parameterList -StartIpList $currentPrefix
	lappend parameterList -NetworkCount 1
	lappend parameterList -AddrIncrement 0
	::sth::sthCore::invoke stc::config $networkBlock $parameterList
	
	if {$add == "TRUE"} {
		lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) $link
		if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB)] == 0} {
			set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB) 1
		} else {
			incr ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB)
		}
	}
}


proc ::sth::ospfTopology::ConnectSessionWithGridForP2PUnnumbered {connect_row connect_col ospfHnd connectLsa} {
	# Create link on connect session
	set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)
	set linkID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	
	set parameterList ""
	
	set lsaLinkList [::sth::sthCore::invoke stc::get $connectLsa -children-RouterLsaLink]
	set dataList ""
	foreach lsaLink $lsaLinkList {
		set linkType [::sth::sthCore::invoke stc::get $lsaLink -LinkType]
		if {![regexp -nocase "STUB_NETWORK" $linkType]} {
			lappend dataList [::sth::sthCore::invoke stc::get $lsaLink -LinkData]
		}
	}
	
	set linkData [GetUniqueID $dataList]
	if {$linkData == ""} {
		set linkData 0.0.0.1
	}
	
	lappend parameterList -LinkData $linkData
	lappend parameterList -LinkId $linkID
	if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $connectLsa $parameterList} linkHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $linkHnd"]
	}
	
	set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS) $linkHnd
	
	# Create link on lsa hnd in grid
	set parameterList ""
	set linkID [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
	set lsaLinkList [::sth::sthCore::invoke stc::get $lsaHnd -children-RouterLsaLink]
	set dataList ""
	foreach lsaLink $lsaLinkList {
		set linkType [::sth::sthCore::invoke stc::get $lsaLink -LinkType]
		if {![regexp -nocase "STUB_NETWORK" $linkType]} {
			lappend dataList [::sth::sthCore::invoke stc::get $lsaLink -LinkData]
		}
	}
	
	set linkData [GetUniqueID $dataList]
	if {$linkData == ""} {
		set linkData 0.0.0.1
	}
	
	lappend parameterList -LinkData $linkData	
	lappend parameterList -LinkId $linkID
	if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $lsaHnd $parameterList} linkHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $linkHnd"]
	}
	
	set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS) $linkHnd
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER) $connect_row
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER) $connect_col

	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND) $connectLsa
}

proc ::sth::ospfTopology::ConnectSessionWithGridForP2PNumbered {currentPrefix connect_row connect_col ospfHnd connectLsa} {

	set prefix_start $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX)
	set prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP)
	set prefix_length [::ip::lengthToMask $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)]
	
	# For modify mode without grid_prefix_start given
	if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,$connectLsa,PREFIX_VALUE)] == 1 && [info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 0} {
		set currentPrefix $::sth::ospfTopology::gridInfoMap($ospfHnd,$connectLsa,PREFIX_VALUE)
	}
	
	set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$connect_row,$connect_col)	
	set advId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	set parameterList ""
		
	lappend parameterList -LinkId $advId
	set tempData [::sth::ospfTopology::IncrementIpV4Address $currentPrefix 0.0.0.1]
	lappend parameterList -LinkData $tempData
	set link [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $connectLsa $parameterList]
	
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-Ipv4NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlock "-StartIpList $advId -NetworkCount 1"
	
	set tempLink $link
	set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,ERTOSR_LINKS) $link
		
	set parameterList ""
	set advId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
	lappend parameterList -LinkId $advId
	lappend parameterList -LinkData [::sth::ospfTopology::IncrementIpV4Address $tempData 0.0.0.1]
	set link [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $lsaHnd $parameterList]
	
	set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,SRTOER_LINKS) $link
	
	set ::sth::ospfTopology::routerLSAInfoMap($connectLsa,$lsaHnd,LINK_PAIR) ""
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($connectLsa,$lsaHnd,LINK_PAIR) $link $tempLink
		 
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-Ipv4NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlock "-StartIpList $advId -NetworkCount 1"
	
	::sth::ospfTopology::CreateStubNetwork $currentPrefix $prefix_length $connectLsa TRUE
	
	::sth::ospfTopology::CreateStubNetwork $currentPrefix $prefix_length $lsaHnd TRUE
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER) $connect_row
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER) $connect_col
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND) $connectLsa
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,$connectLsa,PREFIX_VALUE) $currentPrefix

	return [::sth::ospfTopology::IncrementIpV4Address $currentPrefix $prefix_step]
}

proc ::sth::ospfTopology::LinkNumberGrid {hndMap currentLsaHnd nextLsaHnd ospfHnd} {

	upvar 1 $hndMap hndsNetworkMap
	
	set prefix_start $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX)
	set prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP)
	set prefix_length [::ip::lengthToMask $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)]

	set networkGroup [lindex $hndsNetworkMap($currentLsaHnd,$nextLsaHnd) 0]
					
	set currentLinkData [::sth::ospfTopology::IncrementIpV4Address $networkGroup 0.0.0.1]
				
	set parameterList ""
	set advId [::sth::sthCore::invoke stc::get $nextLsaHnd -AdvertisingRouterId]
	lappend parameterList -LinkId $advId
	lappend parameterList -LinkData $currentLinkData
	set link [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $currentLsaHnd $parameterList]
	
	#lappend ::sth::ospfTopology::lsaGridLinkMap($currentLsaHnd) $link		
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($currentLsaHnd,GRID_LINKS) $link
	
	set parameterList ""
	lappend parameterList -StartIpList $advId
	lappend parameterList -NetworkCount 1
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-Ipv4NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlock $parameterList
					
	set currentLinkData [::sth::ospfTopology::IncrementIpV4Address $currentLinkData 0.0.0.1] 
					
	set parameterList ""
	set advId [::sth::sthCore::invoke stc::get $currentLsaHnd -AdvertisingRouterId]
	lappend parameterList -LinkId $advId
	lappend parameterList -LinkData $currentLinkData
	set nextlink [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $nextLsaHnd $parameterList]
	
	#lappend ::sth::ospfTopology::lsaGridLinkMap($nextLsaHnd) $nextlink	
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,GRID_LINKS) $nextlink
	
	set ::sth::ospfTopology::routerLSAInfoMap($currentLsaHnd,$nextLsaHnd,LINK_PAIR) ""
	lappend ::sth::ospfTopology::routerLSAInfoMap($currentLsaHnd,$nextLsaHnd,LINK_PAIR) $link $nextlink
	
	set parameterList ""
	lappend parameterList -StartIpList $advId
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-Ipv4NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlock $parameterList
	
	set ::sth::ospfTopology::gridLinkPairMap([::sth::sthCore::invoke stc::get $currentLsaHnd -parent],$currentLsaHnd,$nextLsaHnd) [list $link $nextlink]
	
	# Create STUB Network
	set parameterList ""
	lappend parameterList -LinkType STUB_NETWORK
	lappend parameterList -LinkId $networkGroup
	lappend parameterList -LinkData $prefix_length
	set link [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $currentLsaHnd $parameterList]
	
	#lappend ::sth::ospfTopology::lsaGridLinkMap($currentLsaHnd) $link	
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($currentLsaHnd,GRID_LINKS) $link
			
	set parameterList ""
	lappend parameterList -StartIpList $networkGroup
	lappend parameterList -PrefixLength $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)
	lappend parameterList -NetworkCount 1
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-Ipv4NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlock $parameterList
					
					
	set parameterList ""
	lappend parameterList -LinkType STUB_NETWORK
	lappend parameterList -LinkId $networkGroup
	lappend parameterList -LinkData $prefix_length
	set link [::sth::sthCore::invoke stc::create "RouterLsaLink" -under $nextLsaHnd $parameterList]
	
	#lappend ::sth::ospfTopology::lsaGridLinkMap($nextLsaHnd) $link	
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,GRID_LINKS) $link
	
	set parameterList ""
	lappend parameterList -StartIpList $networkGroup
	lappend parameterList -PrefixLength $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)
	lappend parameterList -NetworkCount 1
	set networkBlock [::sth::sthCore::invoke stc::get $link -children-Ipv4NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlock $parameterList
				
}

proc ::sth::ospfTopology::CreateNumberLink {hndMap row col ospfHnd} {
	upvar 1 $hndMap hndsNetworkMap

	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set currentLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			if {[expr $colIndex + 1] <= $col} {
				set nextLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,[expr $colIndex + 1])
				::sth::ospfTopology::LinkNumberGrid hndsNetworkMap $currentLsaHnd $nextLsaHnd $ospfHnd
			}
				
			if {[expr $rowIndex + 1] <= $row} {
				set nextLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,[expr $rowIndex + 1],$colIndex)
				::sth::ospfTopology::LinkNumberGrid hndsNetworkMap $currentLsaHnd $nextLsaHnd $ospfHnd
			}
		}
	}
}

proc ::sth::ospfTopology::PrepareP2PNumberLinking {hndMap row col ospfHnd} {
	upvar 1 $hndMap hndsNetworkMap
	
	set prefix_start $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX)
	set prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP)
	set prefix_length [::ip::lengthToMask $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH)]
	
	set currentPrefix $prefix_start
		
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set currentLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			if {[expr $colIndex + 1] <= $col} {
				set nextLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,[expr $colIndex + 1])
				set hndsNetworkMap($currentLsaHnd,$nextLsaHnd) $currentPrefix
				set currentPrefix [::sth::ospfTopology::IncrementIpV4Address $currentPrefix $prefix_step]
			} 
				
			if {[expr $rowIndex + 1] <= $row} {
				set nextLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,[expr $rowIndex + 1],$colIndex)
				set hndsNetworkMap($currentLsaHnd,$nextLsaHnd) $currentPrefix
				set currentPrefix [::sth::ospfTopology::IncrementIpV4Address $currentPrefix $prefix_step]	
			}
		}
	}
	return $currentPrefix
}

proc ::sth::ospfTopology::GenerateGridHnd {ospfHnd} {
	set gridHndName $::sth::ospfTopology::GRIDID_STR$::sth::ospfTopology::currentGridID
	set ::sth::ospfTopology::routerGridHndMap($gridHndName) $ospfHnd
	incr ::sth::ospfTopology::currentGridID
	return $gridHndName
}

proc ::sth::ospfTopology::CreateDefaultLSA {ospfHnd} {
	set routerInterface [::sth::sthCore::invoke stc::get $ospfHnd -parent]
	set parameterList ""
	set subParameterList ""
	set router_id [::sth::sthCore::invoke stc::get $routerInterface -routerId]
	if {$::sth::ospfTopology::currentOSPFVersion != $::sth::ospfTopology::OSPFV3_STR} {
		lappend parameterList -LinkStateId 0.0.0.0
		lappend subParameterList -LinkData 255.255.255.255 -LinkId $router_id -LinkType STUB_NETWORK
		set objName RouterLsa
		set subObjName RouterLsaLink
	} else {
		lappend parameterList -LinkStateId 0
		lappend subParameterList -NeighborRouterId $router_id
		set objName Ospfv3RouterLsa
		set subObjName Ospfv3RouterLsaIf 
	}

	lappend parameterList -AdvertisingRouterId $router_id
	if {[catch {::sth::sthCore::invoke stc::create $objName -under $ospfHnd $parameterList} lsaHnd] == 1} {
		return $::sth::sthCore::FAILURE
	} else {
		if {[catch {::sth::sthCore::invoke stc::create $subObjName -under $lsaHnd $subParameterList} lsaLinkHnd] == 1} {
			return $::sth::sthCore::FAILURE
		}
		return $lsaHnd
	}
}

proc ::sth::ospfTopology::CreateOSPFv3Routers {ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 0} {
		set ::sth::ospfTopology::userArgsArray(router_id) 192.0.1.0
	}
	
	set ::sth::ospfTopology::returnedKeyList ""
	set lsaList [::sth::sthCore::invoke stc::get $ospfHnd -children-Ospfv3RouterLsa]

	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 0} {
		# Create a new one		
		if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
			set connectLsa [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
			set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $connectLsa
		} else {
			set connectLsa $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
		}	
	} else {
		set connectLsa $::sth::ospfTopology::userArgsArray(router_connect)
		if {[lsearch $lsaList $connectLsa] < 0} {
			return [::sth::ospfTopology::ReportError "ERROR: $ospfHnd is not the parent of $lsaList"]					
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 0} {
		return [::sth::ospfTopology::ReportError "ERROR: router_id is a mandatory field"]		
	}
	
	# Create Router LSA If from src
	set ifList [::sth::sthCore::invoke stc::get $connectLsa -children-Ospfv3RouterLsaIf]
	set idList ""
	foreach interface $ifList {
		lappend idList [::sth::sthCore::invoke stc::get $interface -ifId]
	}
	
	set srcIfId [GetUniqueIDForV3 $idList]
	# Always set to 1 since target router LSA is newly created
	set srcNeighborIfId 1
	
	# Create target Router LSA
	set parameterList ""
	lappend parameterList -AdvertisingRouterId $::sth::ospfTopology::userArgsArray(router_id)
	
	set routerTypeString ""
	set hasAbr 0
	if {[info exist ::sth::ospfTopology::userArgsArray(router_abr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_abr) == 1} {
			set routerTypeString "BBIT"
			set hasAbr 1
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_asbr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			if {$hasAbr == 1} {
				set tempString "|EBIT"
			} else {
				set tempString "EBIT"
			}
			set routerTypeString $routerTypeString$tempString
		}
	}
	
	lappend parameterList -RouterType $routerTypeString
	lappend parameterList -Options "V6BIT|EBIT|RBIT"
	
	if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsa" -under $ospfHnd $parameterList} routerLsa] == 1} {
		return [::sth::ospfTopology::ReportError "Error: $routerLsa"]				
	} else {
		# Create target new LSA link
		set parameterList ""
		lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
		lappend parameterList -IfId $srcNeighborIfId
		lappend parameterList -NeighborIfId $srcIfId
		
		if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
			lappend parameterList -Active TRUE
		} else {
			lappend parameterList -Active FALSE	
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(link_metric)] ==1} {
			set lsaLinkMetricValue $::sth::ospfTopology::userArgsArray(link_metric)
			lappend parameterList -Metric $lsaLinkMetricValue
		}

		if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $routerLsa $parameterList} targetRouterLsaIf] == 1} {
			return [::sth::ospfTopology::ReportError "Error: $routerLsa"]		
		}
	} 
	
	# Create new source router LSA link
	set parameterList ""
	lappend parameterList -IfId $srcIfId
	lappend parameterList -NeighborIfId $srcNeighborIfId
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $routerLsa -AdvertisingRouterId]
	
	if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
		lappend parameterList -Active TRUE
	} else {
		lappend parameterList -Active FALSE	
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(link_metric)] ==1} {
		set lsaLinkMetricValue $::sth::ospfTopology::userArgsArray(link_metric)
		lappend parameterList -Metric $lsaLinkMetricValue
	}

	if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $connectLsa $parameterList} srcRouterLsaIf] == 1} {
		return [::sth::ospfTopology::ReportError "Error: $srcRouterLsaIf"]
	} 

	#set ::sth::ospfTopology::routerConnectInfoMap($routerLsa) [list $srcRouterLsaIf $targetRouterLsaIf]
	set ::sth::ospfTopology::routerConnectInfoMap($routerLsa) [list $targetRouterLsaIf $srcRouterLsaIf]


	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERRIR: $iErr"]
	}

	# Make Keyed List
	set returnedSubKeyedList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $routerLsa
	
	keylset returnedSubKeyedList connected_handles $connectLsa
	keylset returnedSubKeyedList version $::sth::ospfTopology::currentOSPFVersion
	keylset returnedSubkeyedList router_lsa $routerLsa
	keylset returnedSubkeyedList link_lsa $srcRouterLsaIf
	
	keylset ::sth::ospfTopology::returnedKeyList router $returnedSubkeyedList
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 1} {
		unset ::sth::ospfTopology::userArgsArray(router_connect)
	}
	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
}


proc ::sth::ospfTopology::CreateOSPFv2Routers {ospfHnd} {

	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 0} {
		set ::sth::ospfTopology::userArgsArray(router_id) 192.0.1.0
	}

	set ::sth::ospfTopology::returnedKeyList ""
	
	set lsaList [::sth::sthCore::invoke stc::get $ospfHnd -children-routerLsa]
	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 0} {
		# Create a new one
		if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
			set connectLsa [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
			set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $connectLsa
		} else {
			set connectLsa $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
		}
	} else {
		set connectLsa $::sth::ospfTopology::userArgsArray(router_connect)
		if {[lsearch $lsaList $connectLsa] < 0} {
			return [::sth::ospfTopology::ReportError "ERROR: $ospfHnd is not the parent of $lsaList"]			
		}
	}

	#Create a single router
	set parameterList ""
	lappend parameterList -AdvertisingRouterId $::sth::ospfTopology::userArgsArray(router_id)
	lappend parameterList -Active TRUE
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_abr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_abr) == 1} {
			lappend parameterList -Abr TRUE
		} else {
			lappend parameterList -Abr FALSE
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_asbr)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(router_asbr) == 1} {
			lappend parameterList -Asbr TRUE
		} else {
			lappend parameterList -Asbr FALSE
		}	
	}
	
	if {[catch {::sth::sthCore::invoke stc::create "RouterLsa" -under $ospfHnd $parameterList} routerLsa] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $routerLsaHnd"]
	} else {
		# Create link and point to connect lsa
		set parameterList ""
		# Always set to 0.0.0.1 since it is the first one
		lappend parameterList -LinkData 0.0.0.1
		lappend parameterList -LinkId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
		lappend parameterList -LinkType POINT_TO_POINT
		
		if {$::sth::ospfTopology::userArgsArray(link_enable) == 1} {
			lappend parameterList -Active TRUE
		} else {
			lappend parameterList -Active FALSE	
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(link_metric)] ==1} {
			set lsaLinkMetricValue $::sth::ospfTopology::userArgsArray(link_metric)
			lappend parameterList -Metric $lsaLinkMetricValue
		}
		
		if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $routerLsa $parameterList} routerLsaLink] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $routerLsaLink"] 
		}
		
		# Create link from connect lsa and point to new lsa router
		set parameterList ""
		set lsaList [::sth::sthCore::invoke stc::get $connectLsa -children-RouterLsaLink]
		set dataList ""
		foreach lsa $lsaList {
			set linkType [::sth::sthCore::invoke stc::get $lsa -LinkType]
			if {![regexp -nocase "STUB_NETWORK" $linkType]} {
				lappend dataList [::sth::sthCore::invoke stc::get $lsa -LinkData]
			}
		}
		
		set linkData [GetUniqueID $dataList]
		lappend parameterList -LinkData $linkData
		lappend parameterList -LinkId [::sth::sthCore::invoke stc::get $routerLsa -AdvertisingRouterId]
		lappend parameterList -LinkType POINT_TO_POINT
		if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $connectLsa $parameterList} connectLink] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $connectLink"] 
		}
	}
	
	if {$::sth::ospfTopology::userArgsArray(link_te) == 1} {
		set connectTeLsaHnd ""
		set connectRouterTlvHnd ""
		set connectLinkTeLsaHnd ""
		set connectLinkTlvHnd ""
		set teLsaHnd ""
		set routerTlvHnd ""
		set linkTeLsaHnd ""
		set linkRouterTlvHnd ""
		
		::sth::ospfTopology::CreateRouterTE $ospfHnd $connectLsa connectTeLsaHnd connectRouterTlvHnd
		
		::sth::ospfTopology::CreateRouterTE $ospfHnd $routerLsa teLsaHnd routerTlvHnd $::sth::ospfTopology::userArgsArray(link_te_instance)
	
		::sth::ospfTopology::CreateLinkTE $ospfHnd $connectLsa connectLinkTeLsaHnd connectLinkTlvHnd
		
		::sth::ospfTopology::CreateLinkTE $ospfHnd $routerLsa linkTeLsaHnd linkRouterTlvHnd
				 
		::sth::sthCore::invoke stc::config $linkRouterTlvHnd "-LinkId $::sth::ospfTopology::userArgsArray(link_te_link_id)"
		
		::sth::sthCore::invoke stc::config $linkRouterTlvHnd "-TeMetric $::sth::ospfTopology::userArgsArray(link_te_metric)"
		
		::sth::sthCore::invoke stc::config $connectLinkTlvHnd "-LinkId [::sth::sthCore::invoke stc::get $routerLsa -AdvertisingRouterId]"
		
		::sth::ospfTopology::ConfigTEParam $linkRouterTlvHnd
	}
	
	set ::sth::ospfTopology::routerConnectInfoMap($routerLsa) [list $routerLsaLink $connectLink]

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERRIR: $iErr"]
	}
	
#	# Make Keyed List
	set returnedSubKeyedList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $routerLsa
	keylset returnedSubKeyedList version $::sth::ospfTopology::currentOSPFVersion
	keylset returnedSubkeyedList connected_handles $connectLsa
	keylset returnedSubkeyedList router_lsa $routerLsa
	keylset returnedSubkeyedList link_lsa $routerLsaLink
	keylset ::sth::ospfTopology::returnedKeyList router $returnedSubkeyedList

	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 1} {
		unset ::sth::ospfTopology::userArgsArray(router_connect)
	}
	
	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::ConfigTEParam {linkTlv} {
	set teParam [::sth::sthCore::invoke stc::get $linkTlv -children-TeParams]
	set parameterList ""
	lappend parameterList -TeLocalIpv4Addr $::sth::ospfTopology::userArgsArray(link_te_local_ip_addr)
	lappend parameterList -TeRemoteIpv4Addr $::sth::ospfTopology::userArgsArray(link_te_remote_ip_addr)
	lappend parameterList -TeMaxBandwidth $::sth::ospfTopology::userArgsArray(link_te_max_bw)
	lappend parameterList -TeRsvrBandwidth $::sth::ospfTopology::userArgsArray(link_te_max_resv_bw)
	lappend parameterList -TeUnRsvrBandwidth0 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority0)
	lappend parameterList -TeUnRsvrBandwidth1 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority1)
	lappend parameterList -TeUnRsvrBandwidth2 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority2)
	lappend parameterList -TeUnRsvrBandwidth3 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority3)	
	lappend parameterList -TeUnRsvrBandwidth4 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority4)
	lappend parameterList -TeUnRsvrBandwidth5 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority5)
	lappend parameterList -TeUnRsvrBandwidth6 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority6)
	lappend parameterList -TeUnRsvrBandwidth7 $::sth::ospfTopology::userArgsArray(link_te_unresv_bw_priority7)	
	lappend parameterList -Active TRUE
	lappend parameterList -TeGroup $::sth::ospfTopology::userArgsArray(link_te_admin_group)
	
	::sth::sthCore::invoke stc::config $teParam $parameterList
}

proc ::sth::ospfTopology::CreateRouterTE {ospfHnd connectLsa teLsaHnd routerTlvHnd {instance 1}} {
	upvar 1 $teLsaHnd teLsa
	upvar 1 $routerTlvHnd routerTlv
	#Create Router TE on the connected LSA
	set advId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
	set parameterList ""
	lappend parameterList -AdvertisingRouterId $advId
	lappend parameterList -Instance $instance
	
	if {[catch {::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd $parameterList} teLsa] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $teLsa"] 
	} else {
		set parameterList ""
		lappend parameterList -RouterAddr $advId
		if {[catch {::sth::sthCore::invoke stc::create "RouterTlv" -under $teLsa $parameterList} routerTlv] ==1} {
			return [::sth::ospfTopology::ReportError "ERROR: $routerTlv"] 
		}
	}
}

proc ::sth::ospfTopology::CreateLinkTE {ospfHnd connectLsa teLsaHnd routerTlvHnd {instance 1}} {
	upvar 1 $teLsaHnd teLsa
	upvar 1 $routerTlvHnd linkTlv
	set advId [::sth::sthCore::invoke stc::get $connectLsa -AdvertisingRouterId]
	set parameterList ""
	lappend parameterList -AdvertisingRouterId $advId
	
	set teList [::sth::sthCore::invoke stc::get $ospfHnd -children-TeLsa]
	set dataList ""
	foreach te $teList {
		lappend dataList [::sth::sthCore::invoke stc::get $te -Instance]
	}
	
	set instance [GetUniqueIDForV3 $dataList]
	lappend parameterList -Instance $instance
	
	if {[catch {::sth::sthCore::invoke stc::create "TeLsa" -under $ospfHnd $parameterList} teLsa] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $teLsa"] 
	} else {
		set parameterList ""
		
		if {$::sth::ospfTopology::userArgsArray(link_te_type) == "ptop"} {
			lappend parameterList -LinkType POINT_TO_POINT
		} else {
			lappend parameterList -LinkType MULTIACCESS
		}
		
		lappend parameterList -TeMetric $::sth::ospfTopology::userArgsArray(link_te_metric)
		if {[catch {::sth::sthCore::invoke stc::create "LinkTlv" -under $teLsa $parameterList} linkTlv] ==1} {
			return [::sth::ospfTopology::ReportError "ERROR: $linkTlv"] 
		}
	}	
}


proc ::sth::ospfTopology::CreateOSPFv2ExtNssaRoutes {ospfHnd} {
	set ::sth::ospfTopology::returnedKeyList ""
	set connectName ""
	set configType $::sth::ospfTopology::userArgsArray(type)
	
	if {[string tolower $configType] == $::sth::ospfTopology::TYPE_EXTROUTES} {
		set connectName external_connect
	} else {
		set connectName nssa_connect
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray($connectName)] == 1} {
		set connection $::sth::ospfTopology::userArgsArray($connectName)
		set row [lindex $connection 0]
		set col [lindex $connection 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	} else {
		set row 1
		set col 1
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,1,1)
		} else {		
			# fix CR306923057, create default router lsa on the emulated router (no grid to create any simulated routers)
			if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
				set lsaHnd [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
				set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $lsaHnd
			} else {
				set lsaHnd $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
			}
		}
	}
		
	set routerID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
		
	::sth::sthCore::invoke stc::config $lsaHnd "-Asbr TRUE"
		
	lappend parameterList -AdvertisingRouterId $routerID
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		lappend parameterList -Type NSSA
		lappend parameterList -Options NPBIT
		lappend parameterList -Active TRUE
		set prefix_metric "nssa_prefix_metric"
		set prefix_forward_addr "nssa_prefix_forward_addr"
		set prefix_type "nssa_prefix_type"
		set number_of_prefix "nssa_number_of_prefix"
		set prefix_step "nssa_prefix_step"
		set prefix_length "nssa_prefix_length"
		set prefix_start "nssa_prefix_start"
	} else {
		lappend parameterList -Type EXT		
		lappend parameterList -Active TRUE
		set prefix_metric "external_prefix_metric"
		set prefix_forward_addr "external_prefix_forward_addr"
		set prefix_type "external_prefix_type"
		set number_of_prefix "external_number_of_prefix"
		set prefix_step "external_prefix_step"
		set prefix_length "external_prefix_length"
		set prefix_start "external_prefix_start"
	}
	
	
	if {[info exist ::sth::ospfTopology::userArgsArray($prefix_forward_addr)] == 1} {
		lappend parameterList -ForwardingAddr $::sth::ospfTopology::userArgsArray($prefix_forward_addr)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray($prefix_metric)] == 1} {
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray($prefix_metric)
	}

	if {[info exist ::sth::ospfTopology::userArgsArray($prefix_type)] == 1} {
		lappend parameterList -MetricType $::sth::ospfTopology::userArgsArray($prefix_type)
	}
		
	if {[catch {::sth::sthCore::invoke stc::create "ExternalLsaBlock" -under $ospfHnd $parameterList} extLsaHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $extLsaHnd"]
	} else {		
		set parameterList ""		 
		set networkBlockHnd [::sth::sthCore::invoke stc::get $extLsaHnd -children-Ipv4NetworkBlock]
			
		lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray($number_of_prefix)
		
		lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray($prefix_step)
					
		lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray($prefix_length)
					
		if {[info exist ::sth::ospfTopology::userArgsArray($prefix_start)] == 1} {
			lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray($prefix_start)
		}
		
		if {[catch {::sth::sthCore::invoke stc::config $networkBlockHnd $parameterList} networkBlock] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
		}	
	}
	
	# Make Keyed List 
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		set keyName nssa
		set lsaKeyName nssa_lsas
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set ::sth::ospfTopology::nssaRouteHndLocationMap($extLsaHnd) [list $row $col]
		}
	} else {
		set keyName external
		set lsaKeyName external_lsas
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"] } {
			set ::sth::ospfTopology::extRouteHndLocationMap($extLsaHnd) [list $row $col]
		}
	}

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	
	set ::sth::ospfTopology::returnedKeyList ""
	set subList ""
	keylset subList $lsaKeyName $extLsaHnd
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList connected_routers $lsaHnd
	keylset ::sth::ospfTopology::returnedKeyList $keyName $subList
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $extLsaHnd

	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::CreateOSPFv2SumRoutes {ospfHnd} {
	set ::sth::ospfTopology::returnedKeyList ""
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		set connection $::sth::ospfTopology::userArgsArray(summary_connect)
		set row [lindex $connection 0]
		set col [lindex $connection 1]
		set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	} else {
		set row 1
		set col 1
		if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,1,1)
		} else {		
			# fix CR306923057, create default router lsa on the emulated router (no grid to create any simulated routers)
			if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
				set lsaHnd [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
				set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $lsaHnd
			} else {
				set lsaHnd $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
			}
		}
	}
		
		 
	set routerID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
		
	::sth::sthCore::invoke stc::config $lsaHnd "-Abr TRUE"
		
	lappend parameterList -AdvertisingRouterId $routerID
	
	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_metric)] == 1} { 
		lappend parameterList -Metric $::sth::ospfTopology::userArgsArray(summary_prefix_metric)
	}
		
	if {[catch {::sth::sthCore::invoke stc::create "SummaryLsaBlock" -under $ospfHnd $parameterList} sumBlockHnd] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $sumBlockHnd"]
	} else {
		set parameterList ""
		set networkBlock [::sth::sthCore::invoke stc::get $sumBlockHnd  -children-Ipv4NetworkBlock]

		if {[info exist ::sth::ospfTopology::userArgsArray(summary_number_of_prefix)] == 1} {
			lappend parameterList -NetworkCount $::sth::ospfTopology::userArgsArray(summary_number_of_prefix)
		}
			
		if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_length)] == 1} { 
			lappend parameterList -PrefixLength $::sth::ospfTopology::userArgsArray(summary_prefix_length)
		}
			
		if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_step)] == 1} {
			lappend parameterList -AddrIncrement $::sth::ospfTopology::userArgsArray(summary_prefix_step)
		}

		if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_start)] == 1} {
			lappend parameterList -StartIpList $::sth::ospfTopology::userArgsArray(summary_prefix_start)
		}	
			
		if {[catch {::sth::sthCore::invoke stc::config $networkBlock $parameterList} networkBlock] == 1} {
			return [::sth::ospfTopology::ReportError "ERROR: $networkBlock"]
		}
	}

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERROR: $iErr"]
	}
	if {[info exists ::sth::ospfTopology::topoType($ospfHnd)] && [string equal $::sth::ospfTopology::topoType($ospfHnd) "grid"]} {
		set ::sth::ospfTopology::sumRouteHndLocationMap($sumBlockHnd) [list $row $col]
	}
	
	set ::sth::ospfTopology::returnedKeyList ""
	set subList ""
	keylset subList summary_lsas $sumBlockHnd
	keylset subList version $::sth::ospfTopology::currentOSPFVersion
	keylset subList connected_routers $lsaHnd
	keylset ::sth::ospfTopology::returnedKeyList summary $subList
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $sumBlockHnd

	unset ::sth::ospfTopology::userArgsArray	
	return $::sth::ospfTopology::returnedKeyList	
}

proc ::sth::ospfTopology::LinkGrid {row col parent} {

	set prefixIP $::sth::ospfTopology::gridInfoMap($parent,PREFIX)
	set prefixLength $::sth::ospfTopology::gridInfoMap($parent,PREFIX_LENGTH)
	set prefixStep $::sth::ospfTopology::gridInfoMap($parent,PREFIX_STEP)
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($parent,$rowIndex,$colIndex)
#			# Create right LSA Link
			if {[expr $colIndex + 1] <= $col} {
				::sth::ospfTopology::CreateLsaLink $rowIndex [expr $colIndex + 1] $lsaHnd $parent
			}
			
			if {[expr $rowIndex + 1] <= $row} {
				::sth::ospfTopology::CreateLsaLink [expr $rowIndex + 1] $colIndex $lsaHnd $parent
			}	
		}
	}
}

proc ::sth::ospfTopology::CreateOSPFv3LSAIF {lsaHnd row col parent} {
	set nextLsaHnd $::sth::ospfTopology::topologyHndMap($parent,$row,$col)
	set lsaLinkList [::sth::sthCore::invoke stc::get $lsaHnd -children-Ospfv3RouterLsaIf]
	set nextLsaLinkList [::sth::sthCore::invoke stc::get $nextLsaHnd -children-Ospfv3RouterLsaIf]
	
	if {[llength $lsaLinkList] == 0} {
		set ifId 1
	} else {
		foreach lsaLink $lsaLinkList {
			lappend idList [::sth::sthCore::invoke stc::get $lsaLink -ifid]
		}
		set ifId [GetUniqueIDForV3 $idList]
	}
	
	if {[llength $nextLsaLinkList] == 0} {
		set nextIfId 1
	} else {
		foreach lsaLink $nextLsaLinkList {
			lappend idList [::sth::sthCore::invoke stc::get $lsaLink -ifid]
		}
		set nextIfId [GetUniqueIDForV3 $idList]
	}
				
	set parameterList ""
	lappend parameterList -IfId $ifId
	lappend parameterList -NeighborIfId $nextIfId
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $nextLsaHnd -AdvertisingRouterId]
	if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $lsaHnd $parameterList} lsaLink] == 1} {
		return [::sth::ospfTopology::ReportError "Error: $lsaLink"]
	}
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) $lsaLink
	
	set parameterList ""
	lappend parameterList -NeighborIfId $ifId
	lappend parameterList -IfId $nextIfId
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	if {[catch {::sth::sthCore::invoke stc::create "Ospfv3RouterLsaIf" -under $nextLsaHnd $parameterList} lsaLink] == 1} {
		return [::sth::ospfTopology::ReportError "Error: $lsaLink"]
	}
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,GRID_LINKS) $lsaLink	
}

proc ::sth::ospfTopology::LinkOSPFv3ConnectSession {ospfHnd cHnd} {
	upvar 1 $cHnd connectHnd 
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 0} {
		if {[lsearch [array names ::sth::ospfTopology::routerDefaultLSAMap] $ospfHnd] < 0} {
			set connectHnd [::sth::ospfTopology::CreateDefaultLSA $ospfHnd]
			set ::sth::ospfTopology::routerDefaultLSAMap($ospfHnd) $connectHnd
		} else {
			set connectHnd $::sth::ospfTopology::routerDefaultLSAMap($ospfHnd)
		}
	} else {
		set connectHnd $::sth::ospfTopology::userArgsArray(grid_connect_session)
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 0} {
		set col 1
		set row 1
	} else {
		set row [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 0]
		set col [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 1]
	}
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER) $row
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER) $col
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND) $connectHnd
	set gridLsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$row,$col)
	
	set parameterList ""
	set idList ""
	set lsaIfList [::sth::sthCore::invoke stc::get $gridLsaHnd -children-Ospfv3RouterLsaIf]
	foreach lsaIf $lsaIfList {
		lappend idList [::sth::sthCore::invoke stc::get $lsaIf -IfId]
	}
	
	set newId [GetUniqueIDForV3 $idList]
	
	lappend parameterList -IfId $newId
	lappend parameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $connectHnd -AdvertisingRouterId]
	
	::sth::sthCore::invoke stc::config $connectHnd "-RouterType 0"
	
	set connectParameterList ""
	set idList ""
	set lsaIfList [::sth::sthCore::invoke stc::get $connectHnd -children-Ospfv3RouterLsaIf]
	foreach lsaIf $lsaIfList {
		lappend idList [::sth::sthCore::invoke stc::get $lsaIf -IfId]
	}	
	
	set newConnectId [GetUniqueIDForV3 $idList]
	
	lappend connectParameterList -IfId $newConnectId
	lappend connectParameterList -NeighborRouterId [::sth::sthCore::invoke stc::get $gridLsaHnd -AdvertisingRouterId]
	lappend connectParameterList -NeighborIfId $newId
	lappend connectParameterList -IfType POINT_TO_POINT
	
	lappend parameterList -NeighborIfId $newConnectId
	lappend parameterList -IfType POINT_TO_POINT
	
	set gridLink [::sth::sthCore::invoke stc::create Ospfv3RouterLsaIf -under $gridLsaHnd $parameterList]
	
	set erLink [::sth::sthCore::invoke stc::create Ospfv3RouterLsaIf -under $connectHnd $connectParameterList]
	
	set ::sth::ospfTopology::routerLSAInfoMap($gridLsaHnd,ERTOSR_LINKS) $erLink
	set ::sth::ospfTopology::routerLSAInfoMap($gridLsaHnd,SRTOER_LINKS) $gridLink
	
	set ::sth::ospfTopology::routerLSAInfoMap($connectHnd,$gridLsaHnd,LINK_PAIR) ""
	lappend ::sth::ospfTopology::routerLSAInfoMap($connectHnd,$gridLsaHnd,LINK_PAIR) $erLink $gridLink
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ERHND) $connectHnd
	
}

proc ::sth::ospfTopology::CreateOSPFv3Grid {ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 1} {
		set col $::sth::ospfTopology::userArgsArray(grid_col)
	} else {
		set col 1
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 1} {
		set row $::sth::ospfTopology::userArgsArray(grid_row)
	} else {
		set row 1
	}
	
	
	if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,GRIDHND)] == 0} {
		if {[::sth::ospfTopology::CreateGrid $row $col $ospfHnd] == $::sth::sthCore::FAILURE} {
			return [::sth::ospfTopology::ReportError "Create Grid returns failure"]	
		}
	} else {
		return [::sth::ospfTopology::ReportError "Grid is already created under $ospfHnd"]	
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 1} {
		set prefix_start $::sth::ospfTopology::userArgsArray(grid_prefix_start)
	} else {
		set prefix_start "2000::"
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 1} {
		set prefix_step $::sth::ospfTopology::userArgsArray(grid_prefix_step)
	} else {
		set prefix_step "0:0:0:0:0:0:0:1"
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_length)] == 1} { 
		set prefix_length $::sth::ospfTopology::userArgsArray(grid_prefix_length)
	} else {
		set prefix_length "64"
	}
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX) $prefix_start
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH) $prefix_length
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_STEP) $prefix_step
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex) 
			# Create right LSA Link
			if {[expr $colIndex + 1] <= $col} {
				::sth::ospfTopology::CreateOSPFv3LSAIF $lsaHnd $rowIndex [expr $colIndex + 1] $ospfHnd
			}

			
			if {[expr $rowIndex + 1] <= $row} {
				::sth::ospfTopology::CreateOSPFv3LSAIF $lsaHnd [expr $rowIndex + 1] $colIndex $ospfHnd
			}
		}
	}
	
	set connectHnd ""
	#Link the connect session.
	::sth::ospfTopology::LinkOSPFv3ConnectSession $ospfHnd connectHnd
	
	set currentPrefix $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX)
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_stub_per_router)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_stub_per_router) > 0} {
			#Create Stub Network
			for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
				for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
					set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
					set ::sth::ospfTopology::gridInfoMap($ospfHnd,NUM_OF_STUB) $::sth::ospfTopology::userArgsArray(grid_stub_per_router)
					set currentPrefix [::sth::ospfTopology::CreateIntraNetwork $ospfHnd $lsaHnd $currentPrefix $prefix_step $::sth::ospfTopology::gridInfoMap($ospfHnd,PREFIX_LENGTH) $::sth::ospfTopology::userArgsArray(grid_stub_per_router) TRUE]
				}
			}
		}
	}

	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,LINK_TYPE) "ptop_unnumbered"
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW) $row
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL) $col

	if {[catch {::sth::sthCore::doStcApply} iErr] == 1} {
		return [::sth::ospfTopology::ReportError "ERRIR: $iErr"]
	}
		
	# Make keyed list
	set gridHndName [::sth::ospfTopology::GenerateGridHnd $ospfHnd]
	set ::sth::ospfTopology::returnedKeyList ""
	keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	keylset ::sth::ospfTopology::returnedKeyList elem_handle $gridHndName
	
	set subList ""
	keylset subList connected_session.$connectHnd.row $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW_TO_ER)
	keylset subList connected_session.$connectHnd.col $::sth::ospfTopology::gridInfoMap($ospfHnd,COL_TO_ER)
	
	for {set rowIndex 1} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex 1} {$colIndex <= $col} {incr colIndex} {
			set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
			keylset subList router.$rowIndex.$colIndex $lsaHnd
		}
	}
	
	keylset ::sth::ospfTopology::returnedKeyList grid $subList
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,GRIDHND) $gridHndName
	unset ::sth::ospfTopology::userArgsArray
	return $::sth::ospfTopology::returnedKeyList
}

proc ::sth::ospfTopology::CreateIntraNetwork {ospfHnd lsaHnd currentPrefix prefix_step prefixLength count {add FALSE}} {
	set advId [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	set lsaBlk [::sth::sthCore::invoke stc::create "Ospfv3IntraAreaPrefixLsaBlk" -under $ospfHnd "-AdvertisingRouterId $advId -RefAdvertisingRouterId $advId -RefLsType 8193"]
	set networkBlk [::sth::sthCore::invoke stc::get $lsaBlk -children-Ipv6NetworkBlock]
	::sth::sthCore::invoke stc::config $networkBlk "-StartIpList $currentPrefix -NetworkCount $count -PrefixLength $prefixLength -AddrIncrement $prefix_step"
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,STUB) $lsaBlk
	
	if {$add == "TRUE"} {
		if {[info exist ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB)] == 0} {
			set ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB) 1
		} else {
			incr ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,NUM_OF_STUB)
		}
	}
	#set maskedPrefixStep [::sth::ospfTopology::ConvertLengthToV6Step $prefixLength $prefix_step]
	#set currentPrefix [::sth::ospfTopology::incrementIpV6Address $currentPrefix $maskedPrefixStep]
	
	set maskedPrefixStep [::sth::ospfTopology::ConvertLengthToV6Step $prefixLength $prefix_step]
	for {set i 0} {$i < $count} {incr i} {
		set currentPrefix [::sth::ospfTopology::incrementIpV6Address $currentPrefix $maskedPrefixStep]
	}
	return $currentPrefix
	#return [::sth::ospfTopology::incrementIpV6Address $currentPrefix $maskedPrefixStep]
}

proc ::sth::ospfTopology::CreateLsaLink {row col lsaHnd parent} {
	# Link the next one
	set nextLsaHnd $::sth::ospfTopology::topologyHndMap($parent,$row,$col)
	set linkData $::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR)
	set nextLsaRouterID [::sth::sthCore::invoke stc::get $nextLsaHnd -AdvertisingRouterId]
	
	set parameterList ""
	lappend parameterList -LinkId $nextLsaRouterID
	lappend parameterList -LinkData $linkData
	if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $lsaHnd $parameterList} lasLinkHnd] == 1} {
		return [::sth::ospfTopology::ReportError "$lasLinkHnd"]
	}	
	
	lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) $lasLinkHnd
	
	set ::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR) \
			[::sth::ospfTopology::IncrementIpV4Address $::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR)]
	
	# Link Current one
	set linkData $::sth::ospfTopology::gridLsaInfoMap($nextLsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR)
	set nextLsaRouterID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
	
	set parameterList ""
	lappend parameterList -LinkId $nextLsaRouterID
	lappend parameterList -LinkData $linkData
	if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $nextLsaHnd $parameterList} linkHnd] == 1} {
		return [::sth::ospfTopology::ReportError "$linkHnd"]
	}	

	#lappend ::sth::ospfTopology::lsaGridLinkMap($lsaHnd) $lasLinkHnd

	#lappend ::sth::ospfTopology::routerLSAInfoMap($lsaHnd,GRID_LINKS) $linkHnd
	lappend ::sth::ospfTopology::routerLSAInfoMap($nextLsaHnd,GRID_LINKS) $linkHnd

	set ::sth::ospfTopology::gridLsaInfoMap($nextLsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR) \
			[::sth::ospfTopology::IncrementIpV4Address $::sth::ospfTopology::gridLsaInfoMap($nextLsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR)]

	set ::sth::ospfTopology::gridLinkPairMap($parent,$lsaHnd,$nextLsaHnd) [list $linkHnd $lasLinkHnd]
}

proc ::sth::ospfTopology::CreateLsaLinkOld {row col lsaHnd parent} {

	if {$::sth::ospfTopology::userArgsArray(grid_link_type) == "ptop_unnumbered"} {
		set lastLsaHnd $::sth::ospfTopology::topologyHndMap($parent,$row,$col)
		set linkData $::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR)
		set lastLsaRouterID [::sth::sthCore::invoke stc::get $lastLsaHnd -AdvertisingRouterId]
		
		set parameterList ""
		lappend parameterList -LinkId $lastLsaRouterID
		lappend parameterList -LinkData $linkData
		if {[catch {::sth::sthCore::invoke stc::create "RouterLsaLink" -under $lsaHnd $parameterList} lasLinkHnd] == 1} {
			return [::sth::ospfTopology::ReportError "$lasLinkHnd"]
		}
	
		set ::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR) \
			[::sth::ospfTopology::IncrementIpV4Address $::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR)]
	}
}

proc ::sth::ospfTopology::GetUniqueID {idList} {
	set idList [lsort $idList]
	set lastID [lindex $idList [expr [llength $idList] - 1]]
	set newID [::sth::ospfTopology::IncrementIpV4Address $lastID]
	set incrementValue 0.0.0.1
	while {[lsearch $idList $newID] != -1} {
		set newID [::sth::ospfTopology::IncrementIpV4Address $lastID $incrementValue]
		set incrementValue [::sth::ospfTopology::IncrementIpV4Address $lastID]
	}
	
	return $newID
}

proc ::sth::ospfTopology::GetUniqueIDForV3 {idList} {
	set idList [lsort $idList]
	set lastID [lindex $idList [expr [llength $idList] - 1]]
	set newID [expr $lastID + 1]
	while {[lsearch $idList $newID] != -1} {
		set newID [expr $lastId + 1]
	}
	if {$newID == ""} {
		set newID 0
	}
	return $newID
}

proc ::sth::ospfTopology::IncrementIpV4Address {ipToIncrement {ipIncrementValue 0.0.0.1}} {
    set ipList   [split $ipToIncrement    .]
    set incrVals [split $ipIncrementValue .]
    set o4 [expr [lindex $ipList 3] + [lindex $incrVals 3]]
    set o3 [expr [lindex $ipList 2] + [lindex $incrVals 2]]
    set o2 [expr [lindex $ipList 1] + [lindex $incrVals 1]]
    set o1 [expr [lindex $ipList 0] + [lindex $incrVals 0]]

    if {$o4 > 255} {incr o3; set o4 [expr $o4 - 256]}
    if {$o3 > 255} {incr o2; set o3 [expr $o3 - 256]}
    if {$o2 > 255} {incr o1; set o2 [expr $o2 - 256]}
    if {$o1 > 255} {
        return [::sth::ospfTopology::ReportError "ERROR: Cannot increment ip past 255.0.0.0"]
    }

    return ${o1}.${o2}.${o3}.${o4}
}

proc ::sth::ospfTopology::ModifyGridSize {newRow newCol oldRow oldCol ospfHnd} {
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id)] == 0} {
		set ::sth::ospfTopology::userArgsArray(grid_router_id) $::sth::ospfTopology::gridInfoMap($ospfHnd,INIROUTERID)
	}
	
	if {$newRow > $oldRow && $newCol > $oldCol} {
		::sth::ospfTopology::CreateGrid $newRow $newCol $ospfHnd
	} elseif {$newRow < $oldRow && $newCol < $oldCol} {
		for {set rowIndex 1} {$rowIndex <= $oldRow} {incr rowIndex} {
			for {set colIndex 1} {$colIndex <= $oldCol} {incr colIndex} {
				if {$rowIndex > $newRow || $colIndex > $newCol} {
					set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
					::sth::sthCore::invoke stc::delete $lsaHnd
					unset ::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				} 
			}
		}
		::sth::ospfTopology::CreateGrid $newRow $newCol $ospfHnd
	} elseif {$newRow >= $oldRow && $newCol <= $oldCol} {
		for {set rowIndex 1} {$rowIndex <= $oldRow} {incr rowIndex} {
			for {set colIndex 1} {$colIndex <= $oldCol} {incr colIndex} {
				if {$colIndex > $newCol} {
					set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
					::sth::sthCore::invoke stc::delete $lsaHnd
					unset ::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				}
			}
		}
		::sth::ospfTopology::CreateGrid $newRow $newCol $ospfHnd
	}  elseif {$newRow <= $oldRow && $newCol >= $oldCol} {
		for {set rowIndex 1} {$rowIndex <= $oldRow} {incr rowIndex} {
			for {set colIndex 1} {$colIndex <= $oldCol} {incr colIndex} {
				if {$rowIndex > $newRow} {
					set lsaHnd $::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
					::sth::sthCore::invoke stc::delete $lsaHnd
					unset ::sth::ospfTopology::topologyHndMap($ospfHnd,$rowIndex,$colIndex)
				}
				
			}
		}
		::sth::ospfTopology::CreateGrid $newRow $newCol $ospfHnd
	} 
	#keylset ::sth::ospfTopology::gridInfoMap($ospfHnd) row $newRow
	#keylset ::sth::ospfTopology::gridInfoMap($ospfHnd) col $newCol
	
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW) $newRow
	set ::sth::ospfTopology::gridInfoMap($ospfHnd,COL) $newCol
}


proc ::sth::ospfTopology::CreateGrid {row col parent {startRow 1} {startCol 1}} {
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id)] != 0} {
		set ::sth::ospfTopology::gridInfoMap($parent,INIROUTERID) $::sth::ospfTopology::userArgsArray(grid_router_id)
		set iniRouterID $::sth::ospfTopology::userArgsArray(grid_router_id)
	} else {
		if {[info exist ::sth::ospfTopology::gridInfoMap($parent,INIROUTERID)] == 0} {
			set ::sth::ospfTopology::gridInfoMap($parent,INIROUTERID) $::sth::ospfTopology::iniRouterID
			set iniRouterID $::sth::ospfTopology::iniRouterID
		} else {
			set iniRouterID $::sth::ospfTopology::gridInfoMap($parent,INIROUTERID)
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id_step)] != 0} {
		set routerStep $::sth::ospfTopology::userArgsArray(grid_router_id_step)
		set ::sth::ospfTopology::gridInfoMap($parent,ROUTER_STEP) $routerStep
	} else {
		if {[info exist ::sth::ospfTopology::gridInfoMap($parent,ROUTER_STEP)] == 0} {
			set routerStep $::sth::ospfTopology::routerStep
		} else {
			set routerStep $::sth::ospfTopology::gridInfoMap($parent,ROUTER_STEP)
		}
	}

	for {set rowIndex $startRow} {$rowIndex <= $row} {incr rowIndex} {
		for {set colIndex $startCol} {$colIndex <= $col} {incr colIndex} {
			if {[info exist ::sth::ospfTopology::topologyHndMap($parent,$rowIndex,$colIndex)] == 1} {
				set lsaHnd $::sth::ospfTopology::topologyHndMap($parent,$rowIndex,$colIndex)
				set advID [::sth::sthCore::invoke stc::get $lsaHnd -AdvertisingRouterId]
				if {$advID != $iniRouterID} {
					::sth::sthCore::invoke stc::config $lsaHnd "-AdvertisingRouterId $iniRouterID"
				}
				set iniRouterID [::sth::ospfTopology::IncrementIpV4Address $iniRouterID $routerStep]
				continue
			}
			
			set parameterList ""
			lappend parameterList -AdvertisingRouterId $iniRouterID
			
			if {$::sth::ospfTopology::isOspfv3 == $::sth::ospfTopology::FALSE} {
				set objectName "RouterLsa"
				set version $::sth::ospfTopology::OSPFV2_STR
			} else {
				set objectName "Ospfv3RouterLsa"
				set version $::sth::ospfTopology::OSPFV3_STR
			}
			
			if {[catch {::sth::sthCore::invoke stc::create $objectName -under $parent $parameterList} lsaHnd] == 1} {
				return $::sth::sthCore::FAILURE
			} else {
				set ::sth::ospfTopology::topologyHndMap($parent,$rowIndex,$colIndex) $lsaHnd
				set ::sth::ospfTopology::gridLsaInfoMap($lsaHnd,$::sth::ospfTopology::CURRENTLINKDATA_STR) 0.0.0.1
			}
			
			set iniRouterID [::sth::ospfTopology::IncrementIpV4Address $iniRouterID $routerStep]
		}
	}
	
	return $::sth::sthCore::SUCCESS
}



proc ::sth::ospfTopology::IsConnectSession {} {
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 0} {
		return $::sth::sthCore::FAILURE
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 0} {
		if {[info exist ::sth::ospfTopology::userArgsArray(grid_disconnect)] == 0} {
			return $::sth::sthCore::FAILURE
		}
	}
	
	return $::sth::sthCore::SUCCESS
}

proc ::sth::ospfTopology::IsCreateGrid {} {
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 1 && \
		[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 1} {
		return $::sth::sthCore::SUCCESS
	} 
	
	return $::sth::sthCore::FAILURE
}

proc ::sth::ospfTopology::Reset {} {
	array set ::sth::ospfTopology::userArgsArray ""
}

proc ::sth::ospfTopology::incrementIpV6Address {ipToIncrement {ipIncrementValue 0:0:0:0:0:0:0:1} {expanded 0}} {
    #Make a fully qualified address to make things easy
    set ipToIncrementOctets {}
    set tmpOctets [split $ipToIncrement :]
    for {set i 0} {$i < [llength $tmpOctets]} {incr i} {
        set str [lindex $tmpOctets $i]
        if {[string length $str]} {
            lappend ipToIncrementOctets $str
        } else {
            #we hit a ::
            lappend ipToIncrementOctets 0
            #how many segments are missing
            set missingSegments [expr 8 - [llength $tmpOctets]]
            for {set seg 0} {$seg < $missingSegments} {incr seg} {
                lappend ipToIncrementOctets 0
            }  ;# end for loop
        }  ;# end if-else statement
    }  ;# end for loop
    set ipIncrementValueOctets {}
    set tmpOctets [split $ipIncrementValue :]
    for {set i 0} {$i < [llength $tmpOctets]} {incr i} {
        set str [lindex $tmpOctets $i]
        if {[string length $str]} {
            lappend ipIncrementValueOctets $str
        } else {
            #we hit a ::
            lappend ipIncrementValueOctets 0
            #how many segments are missing
            set missingSegments [expr 8 - [llength $tmpOctets]]
            for {set seg 0} {$seg < $missingSegments} {incr seg} {
                lappend ipIncrementValueOctets 0
            }  ;#  end for loop
        }  ;# end if-else statment
    }  ;# end for loop


    set ipList   $ipToIncrementOctets
    set incrVals $ipIncrementValueOctets
    set o8 [expr 0x[lindex $ipList 7] + 0x[lindex $incrVals 7]]
    set o7 [expr 0x[lindex $ipList 6] + 0x[lindex $incrVals 6]]
    set o6 [expr 0x[lindex $ipList 5] + 0x[lindex $incrVals 5]]
    set o5 [expr 0x[lindex $ipList 4] + 0x[lindex $incrVals 4]]
    set o4 [expr 0x[lindex $ipList 3] + 0x[lindex $incrVals 3]]
    set o3 [expr 0x[lindex $ipList 2] + 0x[lindex $incrVals 2]]
    set o2 [expr 0x[lindex $ipList 1] + 0x[lindex $incrVals 1]]
    set o1 [expr 0x[lindex $ipList 0] + 0x[lindex $incrVals 0]]

    if {$o8 > 0xffff} {incr o7; set o8 [expr $o8 - 0xffff]}
    if {$o7 > 0xffff} {incr o6; set o7 [expr $o7 - 0xffff]}
    if {$o6 > 0xffff} {incr o5; set o6 [expr $o6 - 0xffff]}
    if {$o5 > 0xffff} {incr o4; set o5 [expr $o5 - 0xffff]}
    if {$o4 > 0xffff} {incr o3; set o4 [expr $o4 - 0xffff]}
    if {$o3 > 0xffff} {incr o2; set o3 [expr $o3 - 0xffff]}
    if {$o2 > 0xffff} {incr o1; set o2 [expr $o2 - 0xffff]}
    if {$o1 > 0xfffe} {
        return "ERROR: Cannot increment ip past fffe::0"
    }

    set ipv6Addr "[format %04X $o1]:[format %04X $o2]:[format %04X $o3]:[format %04X $o4]:[format %04X $o5]:[format %04X $o6]:[format %04X $o7]:[format %04X $o8]"

    if {$expanded} {
        return $ipv6Addr
    } else {

        set r ""
         foreach octet [split $ipv6Addr :] {
            append r [format %x: 0x$octet]
        }
        set r [string trimright $r :]
        regsub {(?:^|:)0(?::0)+(?::|$)} $r {::} r
        return $r
    }   ;# end if-else statement

}  ;# end procedure


proc ::sth::ospfTopology::ConvertLengthToV6Step {lengthValue {stepValue 1}} {
	set mask [::sth::sthCore::prefixLengthToIpMask $lengthValue 6]
	set maskLength [string length $mask]
	set stepMask ""
	set tempStepMask ""
	set found 0
	set zero 0
	set hexStepValue [format %x $stepValue]
	set symbol ""
	for {set i 0} {$i < $maskLength} {incr i} {
		set char [string index $mask $i]
		set nextChar [string index $mask [expr $i + 1]]
		if {$char == ":" || $char == "."} {
	#		set stepMask "$stepMask$char"
			set symbol $char
			continue
		} else {
			set tempStepMask $tempStepMask$char
		}
	}
	
	set maskLength [string length $tempStepMask]
	for {set i 0} {$i < $maskLength} {incr i} {
		set char [string index $tempStepMask $i]
		set nextChar [string index $tempStepMask [expr $i + 1]]
		if {$found == 0} {
			if {$nextChar == 0} {
				set found 1
				set stepMask "$stepMask$hexStepValue"
			} else {
				set stepMask "$stepMask$zero"
			}
		} else {
			set stepMask "$stepMask$zero"
		}
	}
	set newStepMask ""
	set lengthDiff [expr [string length $stepMask] - 32]
	set count 1
	for {set lengthDiff 0} {$lengthDiff < 32} {incr lengthDiff} {
		if {[expr $count % 4] == 0 && $count != 32} {
			set tempStepMask [string index $stepMask $lengthDiff]$symbol
		} else {
			set tempStepMask [string index $stepMask $lengthDiff]
		}
		set newStepMask $newStepMask$tempStepMask
		incr count
	}
	
	return $newStepMask
}

proc ::sth::ospfTopology::CreateOSPFv2NetworkRoutesValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_dr)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(net_dr)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(net_ip)] != 4} {
			return [list FALSE "net_ip expect ipv4 format"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix_length)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(net_prefix_length) > 32 || $::sth::ospfTopology::userArgsArray(net_prefix_length) < 0} {
			return [list FALSE "net_prefix_length expect range is 0-32"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(net_prefix)] != 4} {
			return [list FALSE "net_prefix expect ipv4 format"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip_step)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(net_ip_step)] != 4} {
			return [list FALSE "net_ip_step expect ipv4 format"]
		}
	}

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv3NetworkRoutesValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_dr)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(net_dr)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(net_ip)] != 4} {
			return [list FALSE "net_ip expect ipv4 format"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix_length)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(net_prefix_length) > 128 || $::sth::ospfTopology::userArgsArray(net_prefix_length) < 0} {
			return [list FALSE "net_prefix_length expect range is 0-32"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(net_prefix)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(net_prefix)] != 6} {
			return [list FALSE "net_prefix expect ipv6 format"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(net_ip_step)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(net_ip_step)] != 4} {
			return [list FALSE "net_ip_step expect ipv4 format"]
		}
	}

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv2SumRoutesValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		if {[llength $::sth::ospfTopology::userArgsArray(summary_connect)] != 2} {
			return [list FALSE "Expect summary_connect to have 2 elements"] 
		} else {
			set row [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 0]
			set col [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 1]
			
			if {$row < 0 || $col < 0} {
				return [list FALSE "Elements in summary_connect should be positive value"]
			}
			
			if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0 || [info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
				return [list FALSE "Grid does not exist"]
			} else {
				set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
				set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
				if {$row > $maxRow || $col > $maxCol} {
					return [list FALSE "summary_connect row/col values are invalid. Should be smaller than the grid size"]
				}
			}
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_length)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(summary_prefix_length) > 32 || $::sth::ospfTopology::userArgsArray(summary_prefix_length) < 0} {
			return [list FALSE "summary_prefix_length expect range is 0-32"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_start)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(summary_prefix_start)] != 4} {
			return [list FALSE "summary_prefix_start expect ipv4 format"]
		}
	}	

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv3InterAreaRoutesValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(summary_connect)] == 1} {
		if {[llength $::sth::ospfTopology::userArgsArray(summary_connect)] != 2} {
			return [list FALSE "Expect summary_connect to have 2 elements"] 
		} else {
			set row [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 0]
			set col [lindex $::sth::ospfTopology::userArgsArray(summary_connect) 1]
			
			if {$row < 0 || $col < 0} {
				return [list FALSE "Elements in summary_connect should be positive value"]
			}
		
			if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0 || [info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
				return [list FALSE "Grid does not exist"]
			} else {
				set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
				set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
				if {$row > $maxRow || $col > $maxCol} {
					return [list FALSE "summary_connect row/col values are invalid. Should be smaller than the grid size"]
				}
			}			
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_length)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(summary_prefix_length) > 128 || $::sth::ospfTopology::userArgsArray(summary_prefix_length) < 0} {
			return [list FALSE "summary_prefix_length expect range is 0-128"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(summary_prefix_start)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(summary_prefix_start)] != 6} {
			return [list FALSE "summary_prefix_start expect ipv4 format"]
		}
	}	

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv2ExtNssaRoutesValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}

	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		if {[info exist ::sth::ospfTopology::userArgsArray(external_prefix_length)] == 1} {
			if {$::sth::ospfTopology::userArgsArray(external_prefix_length) > 32 || $::sth::ospfTopology::userArgsArray(external_prefix_length) < 0} {
				return [list FALSE "external_prefix_length expect range is 0-32"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(external_prefix_start)] == 1} {
			if {[::ip::version $::sth::ospfTopology::userArgsArray(external_prefix_start)] != 4} {
				return [list FALSE "external_prefix_start expect ipv4 format"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(external_connect)] == 1} {
			if {[llength $::sth::ospfTopology::userArgsArray(external_connect)] != 2} {
				return [list FALSE "Expect external_connect to have 2 elements"] 
			} else {
				set row [lindex $::sth::ospfTopology::userArgsArray(external_connect) 0]
				set col [lindex $::sth::ospfTopology::userArgsArray(external_connect) 1]
			
				if {$row < 0 || $col < 0} {
					return [list FALSE "Elements in external_connect should be positive value"]
				}
				
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0 || [info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
					return [list FALSE "Grid does not exist"]
				} else {
					set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
					set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
					if {$row > $maxRow || $col > $maxCol} {
						return [list FALSE "summary_connect row/col values are invalid. Should be smaller than the grid size"]
					}
				}				
			}
		}				
	} elseif {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		if {[info exist ::sth::ospfTopology::userArgsArray(nssa_prefix_length)] == 1} {
			if {$::sth::ospfTopology::userArgsArray(nssa_prefix_length) > 32 || $::sth::ospfTopology::userArgsArray(nssa_prefix_length) < 0} {
				return [list FALSE "nssa_prefix_length expect range is 0-32"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(nssa_prefix_start)] == 1} {
			if {[::ip::version $::sth::ospfTopology::userArgsArray(nssa_prefix_start)] != 4} {
				return [list FALSE "nssa_prefix_start expect ipv4 format"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(nssa_connect)] == 1} {
			if {[llength $::sth::ospfTopology::userArgsArray(nssa_connect)] != 2} {
				return [list FALSE "Expect nssa_connect to have 2 elements"] 
			} else {
				set row [lindex $::sth::ospfTopology::userArgsArray(nssa_connect) 0]
				set col [lindex $::sth::ospfTopology::userArgsArray(nssa_connect) 1]
			
				if {$row < 0 || $col < 0} {
					return [list FALSE "Elements in nssa_connect should be positive value"]
				}
				
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0 || [info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
					return [list FALSE "Grid does not exist"]
				} else {
					set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
					set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
					if {$row > $maxRow || $col > $maxCol} {
						return [list FALSE "summary_connect row/col values are invalid. Should be smaller than the grid size"]
					}
				}				
			}
		}
	}

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv3ExtNssaRoutesValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}
	
	if {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_EXTROUTES} {
		if {[info exist ::sth::ospfTopology::userArgsArray(external_prefix_length)] == 1} {
			if {$::sth::ospfTopology::userArgsArray(external_prefix_length) > 128 || $::sth::ospfTopology::userArgsArray(external_prefix_length) < 0} {
				return [list FALSE "external_prefix_length expect range is 0-128"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(external_prefix_start)] == 1} {
			if {[::ip::version $::sth::ospfTopology::userArgsArray(external_prefix_start)] != 6} {
				return [list FALSE "external_prefix_start expect ipv4 format"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(external_connect)] == 1} {
			if {[llength $::sth::ospfTopology::userArgsArray(external_connect)] != 2} {
				return [list FALSE "Expect external_connect to have 2 elements"] 
			} else {
				set row [lindex $::sth::ospfTopology::userArgsArray(external_connect) 0]
				set col [lindex $::sth::ospfTopology::userArgsArray(external_connect) 1]
			
				if {$row < 0 || $col < 0} {
					return [list FALSE "Elements in external_connect should be positive value"]
				}
				
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0 || [info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
					return [list FALSE "Grid does not exist"]
				} else {
					set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
					set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
					if {$row > $maxRow || $col > $maxCol} {
						return [list FALSE "summary_connect row/col values are invalid. Should be smaller than the grid size"]
					}
				}				
			}
		}				
	} elseif {$::sth::ospfTopology::userArgsArray(type) == $::sth::ospfTopology::TYPE_NSSAROUTES} {
		if {[info exist ::sth::ospfTopology::userArgsArray(nssa_prefix_length)] == 1} {
			if {$::sth::ospfTopology::userArgsArray(nssa_prefix_length) > 128 || $::sth::ospfTopology::userArgsArray(nssa_prefix_length) < 0} {
				return [list FALSE "nssa_prefix_length expect range is 0-128"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(nssa_prefix_start)] == 1} {
			if {[::ip::version $::sth::ospfTopology::userArgsArray(nssa_prefix_start)] != 6} {
				return [list FALSE "nssa_prefix_start expect ipv4 format"]
			}
		}
		
		if {[info exist ::sth::ospfTopology::userArgsArray(nssa_connect)] == 1} {
			if {[llength $::sth::ospfTopology::userArgsArray(nssa_connect)] != 2} {
				return [list FALSE "Expect nssa_connect to have 2 elements"] 
			} else {
				set row [lindex $::sth::ospfTopology::userArgsArray(nssa_connect) 0]
				set col [lindex $::sth::ospfTopology::userArgsArray(nssa_connect) 1]
			
				if {$row < 0 || $col < 0} {
					return [list FALSE "Elements in nssa_connect should be positive value"]
				}
				
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0 || [info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
					return [list FALSE "Grid does not exist"]
				} else {
					set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
					set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
					if {$row > $maxRow || $col > $maxCol} {
						return [list FALSE "summary_connect row/col values are invalid. Should be smaller than the grid size"]
					}
				}				
			}
		}		
	}

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv2RoutersValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(router_connect)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(router_disconnect)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(router_disconnect)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(router_id)] != 4} {
			return [list FALSE "grid_router_id expect ipv4 format"]
		}
	}	
		
	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv3RoutersValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(router_connect)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(router_connect)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(router_disconnect)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(router_disconnect)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(router_id)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(router_id)] != 4} {
			return [list FALSE "grid_router_id expect ipv4 format"]
		}
	}	

	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv2GridValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 1} {
		if {[llength $::sth::ospfTopology::userArgsArray(grid_connect)] != 2} {
			return [list FALSE "Expect grid_connect to have 2 elements"] 
		} else {
			set row [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 0]
			set col [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 1]
			
			if {$row < 0 || $col < 0} {
				return [list FALSE "Elements in grid_connect should be positive value"]
			}
			
			if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 0} {
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
					return [list FALSE "There is no column specified in the grid creation under $ospfHnd"]
				} else {
					set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
				}
			} else {
				set maxCol $::sth::ospfTopology::userArgsArray(grid_col)
			}

			if {[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 0} {
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0} {
					return [list FALSE "There is no row specified in the grid creation under $ospfHnd"]
				} else {
					set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
				}
			} else {
				set maxRow $::sth::ospfTopology::userArgsArray(grid_row)
			}
			
			if {$row > $maxRow || $col > $maxCol} {
				return [list FALSE "grid row/col values are invalid. Should be smaller than the grid size"]
			}	
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_length)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_prefix_length) > 32 || $::sth::ospfTopology::userArgsArray(grid_prefix_length) <= 0} {
			return [list FALSE "grid_prefix_length range is 0-32"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_link_type)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_link_type) != "ptop_unnumbered" && $::sth::ospfTopology::userArgsArray(grid_link_type) != "ptop_numbered"} {
			return [list FALSE "Choice of grid_link_type is ptop_unnumbered or ptop_numbered"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_prefix_start)] != 4} {
			return [list FALSE "grid_prefix_start expect ipv4 format"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_prefix_step)] != 4} {
			return [list FALSE "grid_prefix_step expect ipv4 format"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_router_id)] != 4} {
			return [list FALSE "grid_router_id expect ipv4 format"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id_step)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_router_id_step)] != 4} {
			return [list FALSE "grid_router_id_step expect ipv4 format"]
		}
	}		
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(grid_connect_session)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_disconnect)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(grid_disconnect)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}
	
	return TRUE
}

proc ::sth::ospfTopology::CreateOSPFv3GridValidation {ospfHnd} {
	if {[catch {::sth::sthCore::invoke stc::get $ospfHnd -parent} iErr] == 1} {
		return [list FALSE "$ospfHnd is an invalid handle"]
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect)] == 1} {
		if {[llength $::sth::ospfTopology::userArgsArray(grid_connect)] != 2} {
			return [list FALSE "Expect grid_connect to have 2 elements"] 
		} else {
			set row [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 0]
			set col [lindex $::sth::ospfTopology::userArgsArray(grid_connect) 1]
			
			if {$row < 0 || $col < 0} {
				return [list FALSE "Elements in grid_connect should be positive value"]
			}
			
			if {[info exist ::sth::ospfTopology::userArgsArray(grid_col)] == 0} {
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,COL)] == 0} {
					return [list FALSE "There is no column specified in the grid creation under $ospfHnd"]
				} else {
					set maxCol $::sth::ospfTopology::gridInfoMap($ospfHnd,COL)
				}
			} else {
				set maxCol $::sth::ospfTopology::userArgsArray(grid_col)
			}

			if {[info exist ::sth::ospfTopology::userArgsArray(grid_row)] == 0} {
				if {[info exist ::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)] == 0} {
					return [list FALSE "There is no row specified in the grid creation under $ospfHnd"]
				} else {
					set maxRow $::sth::ospfTopology::gridInfoMap($ospfHnd,ROW)
				}
			} else {
				set maxRow $::sth::ospfTopology::userArgsArray(grid_row)
			}
			
			if {$row > $maxRow || $col > $maxCol} {
				return [list FALSE "grid row/col values are invalid. Should be smaller than the grid size"]
			}
		}
	}



	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_length)] == 1} {
		if {$::sth::ospfTopology::userArgsArray(grid_prefix_length) > 128 || $::sth::ospfTopology::userArgsArray(grid_prefix_length) <= 0} {
			return [list FALSE "grid_prefix_length range is 0-32"]
		}
	}
	
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_start)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_prefix_start)] != 6} {
			return [list FALSE "grid_prefix_start expect ipv4 format"]
		}
	}
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_prefix_step)] == 6} {
			return [list FALSE "grid_prefix_step expect integer in ipv6"]
		}
	}

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_router_id)] != 4} {
			return [list FALSE "grid_router_id expect ipv4 format"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_router_id_step)] == 1} {
		if {[::ip::version $::sth::ospfTopology::userArgsArray(grid_router_id_step)] != 4} {
			return [list FALSE "grid_router_id_step expect ipv4 format"]
		}
	}		
	
	if {[info exist ::sth::ospfTopology::userArgsArray(grid_connect_session)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(grid_connect_session)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}	

	if {[info exist ::sth::ospfTopology::userArgsArray(grid_disconnect)] == 1} {
		set lsaHnd $::sth::ospfTopology::userArgsArray(grid_disconnect)
		if {[catch {::sth::sthCore::invoke stc::get $lsaHnd -parent} iErr] == 1} {
			return [list FALSE "$lsaHnd is an invalid handle"]
		}
	}

	return TRUE
}

