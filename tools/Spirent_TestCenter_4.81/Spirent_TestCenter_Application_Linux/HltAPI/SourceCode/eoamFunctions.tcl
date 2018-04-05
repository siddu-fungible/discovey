# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx

namespace eval ::sth::Eoam {
    array set topologyHandleNameArr {}
    array set msgHandleNameArr {}
    set usedMACList ""
    set usedMEP_ID ""
    set resultDataSetSubscribed 0
    set resultDataSetHdl ""
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_config_msg_create (str userInput str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em create for emulation_oam_config_msg_create cmd
###
###This procedure execute the emulation_oam_config_msg_create command when the mode is create. It will create Eoam msg session based on the \em -count switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_config_msg_create (str userInput str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::emulation_oam_config_msg_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_msg"    
    set _hltCmdName "emulation_oam_config_msg_create"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    set modeValue "create"
	set portHandle ""

	if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
		#Check if te port_handle is valid
		if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
			::sth::sthCore::processError returnKeyedList "port_handle needed when creating EOAM Msgs"
			set cmdState $FAILURE
			return $returnKeyedList
		} else {
			set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
		}
		
		if {![::sth::sthCore::IsPortValid $portHandle msg]} {
			::sth::sthCore::processError returnKeyedList "Invalid Value of port_handle"
			set cmdState $FAILURE
			return $returnKeyedList
		}
	} else {
		set handle [set  ${_hltSpaceCmdName}\_user_input_args_array(handle)]
		set portHandle [::sth::sthCore::invoke stc::get $handle -AffiliationPort-Targets]
	}
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]} {
        ::sth::sthCore::processError returnKeyedList "Did not input msg type of the msg to create." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set msgType [set ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]
    }
    
    #get number of EOAM Msg to create
    if {![::info exists ${_hltSpaceCmdName}\_user_input_args_array(count)]} {
        set ${_hltSpaceCmdName}\_user_input_args_array(count) 1
    } 
    set msgNum [set ${_hltSpaceCmdName}\_user_input_args_array(count)]
    
    lappend stepValueList mac_local mac_remote mac_dst vlan_id vlan_outer_id md_level
    for {set msgCount 0} {$msgCount < $msgNum} {incr msgCount} { 
        if {$msgCount == 0} {
            foreach stepValueType $stepValueList {
                if {[info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_incr_mode)]} {
                    set incrMode [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_incr_mode)]
                    if {$incrMode == "list"} {
                        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_list)]} {
                            set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType) [lindex [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_list)] 0]
                        } else {
                            ::sth::sthCore::processError returnKeyedList "$stepValueType\_list needed when creating EOAM Msgs." {}
                            set cmdState $FAILURE
                            return $returnKeyedList                            
                        }
                        
                    }
                }
            }
            #end of foreach
        }
        
        
	#step value mac_local mac_remote mac_dst vlan_id vlan_outer_id
        if {$msgCount > 0} {
	    foreach stepValueType $stepValueList {
		switch -exact $stepValueType {
		    mac_local -	
		    mac_remote -
		    mac_dst {
			if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType)]} {
			    continue
			}
			if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_incr_mode)]} {
			    ::sth::sthCore::processError returnKeyedList "$stepValueType\_incr_mode needed when creating multiple EOAM Msgs"
			    set cmdState $FAILURE
			    return $returnKeyedList                  
			}
			set IncrMode [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_incr_mode)]
			if {$IncrMode != "none"} {
			    set flag 0
			    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_repeat)]} {
				set repeat [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_repeat)]
				if {$repeat == 0 } {
				    set flag 1
				} elseif {[expr [expr $msgCount % $repeat] == 0]} {
				    set flag 1
				}
			    } else {
				set flag 1
			    }
			    if {$flag} {
				set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType) [::sth::Eoam::StepMacAddress $_hltSpaceCmdName $stepValueType]		    
			    }			    
			}
		    }
		    vlan_id {
			if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType)]} {
			    continue
			}
			
			set flag 0
			if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id_outer_repeat)]} {
			    set repeat [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_id_outer_repeat)]
			    if {$repeat == 0 } {
				set flag 1
			    } elseif {[expr [expr $msgCount % $repeat] == 0]} {
				set flag 1
			    }
			} else {
			    set flag 1
			}
			if {$flag} {
			    set Value [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType)]
			    set IncrMode "increment"
			    set StepValue [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_step)]
			    #set Value [::sth::Eoam::StepMacAddress $IncrMode $Value $StepValue]
			    set Value [expr $Value + $StepValue]
			    set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType) $Value			    
			}			
		    }
		    vlan_outer_id {
			if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType)]} {
			    continue
			}
			
			set flag 0
			if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id_outer_repeat)]} {
			    set repeat [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_id_outer_repeat)]
			    if {$repeat == 0 } {
				set flag 1
			    } elseif {[expr [expr $msgCount % $repeat] == 0]} {
				set flag 1
			    }
			} else {
			    set flag 1
			}
			if {$flag} {
			    set Value [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType)]
			    set IncrMode "increment"
			    set StepValue [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_id_outer_step)]
			    #set Value [::sth::Eoam::StepMacAddress $IncrMode $Value $StepValue]
			    set Value [expr $Value + $StepValue]
			    set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType) $Value			    
			}			
		    }
		    md_level {
			if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType)]} {
			    continue
			}
			if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_incr_mode)]} {
			    ::sth::sthCore::processError returnKeyedList "$stepValueType\_incr_mode needed when creating multiple EOAM Msgs"
			    set cmdState $FAILURE
			    return $returnKeyedList                  
			}
			set IncrMode [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_incr_mode)]
			if {$IncrMode != "none"} {
			    set flag 0
			    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_repeat)]} {
				set repeat [set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType\_repeat)]
				if {$repeat == 0 } {
				    set flag 1
				} elseif {[expr [expr $msgCount % $repeat] == 0]} {
				    set flag 1
				}
			    } else {
				set flag 1
			    }
			    if {$flag} {
					set ${_hltSpaceCmdName}\_user_input_args_array($stepValueType) [::sth::Eoam::StepMdLevel $_hltSpaceCmdName]		    
			    }			
			}
		    }
		    default {
			#TODO finish
		    }
		}
		#end of swith
	    }
	    #end of foreach
        }
	#end of if
        
	#Create MEG
	#create the handle instances for all configure
	#set configedObjectTypes {Port Meg Mp}
	
        #create all using objects
	set CmdReturn [::sth::Eoam::ProcessObjectsCreate_Msg returnKeyedList cmdState]
	if {$cmdState } {
	    array set configedObjectHandleArr $CmdReturn
	} else {
	    return $returnKeyedList
	}

	::sth::sthCore::log debug "Msg Object handles created successfully"
	
	#process attribute config
	array set configedObjectAttributeArr {
	    EoamPortConfig ""
	    EoamMegConfig ""
	    EoamRemoteMegEndPointConfig ""
	    EoamRemoteMegEndPointConfig ""
	    Router ""
        IpIf ""
	    EthIIIf ""
	    VlanIf ""
	    VlanIf_Outer ""
	    EoamNodeConfig ""
	    EoamMaintenancePointConfig ""
	    EoamMaintenancePointConfig_MIP ""
	    EoamMaintenancePointConfig_MEP ""
	    EoamContChkCommandConfig ""
        EoamLoopbackCommandConfig ""
        EoamLinkTraceCommandConfig ""
		EoamDelayMeasurementCommandConfig ""
		EoamLossMeasurementCommandConfig ""
		EoamSlmCommandConfig ""
		EoamAisCommandConfig ""
		EoamLckCommandConfig ""
	}
    set PDUFrameSwitchList ""
        
	set userInputList [array get ${_hltSpaceCmdName}\_user_input_args_array]
	foreach {switchName switchValue} $userInputList {
	    ::sth::sthCore::log debug "Process switch:$switchName value:$switchValue config"
	    
	    if { $switchName == "optional_args" } {
			continue
	    }
	    
	    if { $switchName == "mandatory_args" } {
			continue
	    }
            
		if { $switchName == "sut_ip_address"} {
			if {[string first ":" $switchValue] > -1} {
				set switchValue [::sth::sthCore::normalizeIPv6Addr $switchValue]
			}
		}
	    
	    set switchProcFunc [::sth::sthCore::getModeFunc2 $_hltNameSpace $_OrigHltCmdName $switchName $modeValue]
	    
        #set unicast dst mac to type XX-XX-XX-XX-XX-XX
	    if {$switchName == "mac_dst"} {
            set switchValue [join [split $switchValue ":"] "-"]
        }
	    
	    if {[string equal $switchProcFunc "ProcessConfigCmd"]} {
			set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
			if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
				append configedObjectAttributeArr($stcObjName) " -$stcAttrName $attrValue"
			} else {
				append configedObjectAttributeArr($stcObjName) " -$stcAttrName $switchValue"
			} 
	    } elseif {[string equal $switchProcFunc "ProcessCommmandConfig"]} {
			set msgCmdName ""
			switch -exact $msgType {
				loopback {
					set msgCmdName "Loopback"
				}
				linktrace {
					set msgCmdName "LinkTrace"
				}
				test {
					set msgCmdName "Loopback"
					#TODO finish
				}
                continuous_check {
                    set msgCmdName "ContChk" 
                }
                dm {
                    set msgCmdName "DelayMeasurement" 
                }
                lm {
                    set msgCmdName "LossMeasurement" 
                }
                slm {
                    set msgCmdName "Slm" 
                }
                ais {
                    set msgCmdName "Ais" 
                }
                lck {
                    set msgCmdName "Lck" 
                }
			}
			set stcObjName "Eoam$msgCmdName\CommandConfig"
			
			if {$switchName == "transmit_mode"} {
				set stcAttrName "$msgCmdName\TxType"
			} elseif {$switchName == "pkts_per_burst"} {
				set stcAttrName "$msgCmdName\BurstSize"
			} elseif {$switchName == "rate_pps"} {
				set stcAttrName "$msgCmdName\BurstRate"
			} elseif {$switchName == "ttl"} {
				if {$msgType != "linktrace"} {
					puts "Warning: Ttl can only be configured when msg_tpye is linktrace. ttl now can not be configured."
					::sth::sthCore::log debug "Warning: Ttl can only be configured when msg_tpye is linktrace. ttl now can not be configured."
					continue
				}
				
				set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
			} else {
				set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
			}
			
			if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
				append configedObjectAttributeArr($stcObjName) " -$stcAttrName $attrValue"
			} else {
				append configedObjectAttributeArr($stcObjName) " -$stcAttrName $switchValue"
			}                
		} elseif {[string equal $switchProcFunc "ProcessVlanConfig"]} {
            set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            #convert HEX to decimal
            set decVlantype [format "%i" $switchValue] 
		    if {$switchName == "vlan_ether_type"} {
                append configedObjectAttributeArr($stcObjName) " -$stcAttrName $decVlantype"
			}
            if {$switchName == "vlan_outer_ether_type"} {
                append configedObjectAttributeArr($stcObjName) " -$stcAttrName $decVlantype"
			}
		} elseif {[string equal $switchProcFunc "ProcessFrameConfig"]} {
			lappend PDUFrameSwitchList $switchName $switchValue
		} else {
			#TODO finish
		}
	    #end of if elseif else
	}
        #end of foreach
	::sth::sthCore::log debug [array get configedObjectAttributeArr]
        ::sth::sthCore::log debug [array get configedObjectHandleArr]
        set objectTypeList [array names configedObjectHandleArr]
	foreach objectType $objectTypeList {
            if {$configedObjectHandleArr($objectType) != ""} {
                foreach objectHandle $configedObjectHandleArr($objectType) {
                    ::sth::sthCore::log debug "process objectHandle:$objectHandle, configedObjectAttributeArr($objectType):$configedObjectAttributeArr($objectType)"
                    if {$configedObjectAttributeArr($objectType) != ""} {
                        ::sth::sthCore::log debug "Process config $objectHandle $configedObjectAttributeArr($objectType)"
                        if {[catch {::sth::sthCore::invoke stc::config $objectHandle $configedObjectAttributeArr($objectType)} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Error ocured when config $objectHandle $configedObjectAttributeArr($objectType) errMsg: $errMsg." {}
                            set cmdState $FAILURE
                            return $returnKeyedList                    
                        }                
                    }
                }                
            }
	}
	::sth::sthCore::log debug "Process profunc cmd config successfully"	
	
        #Eoam PDU frame config, TLV config
	if {![::sth::Eoam::ProcessFrameConfig $msgType $configedObjectHandleArr(EoamMaintenancePointConfig) $PDUFrameSwitchList $userInput]} {
            ::sth::sthCore::processError returnKeyedList "Error Occured while process PDU Frame config."
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {$cmdState} {
            set tmpHandleList {}
            catch {set tmpHandleList [keylget returnKeyedList handle]}
            lappend tmpHandleList $configedObjectHandleArr(EoamMaintenancePointConfig)
            keylset returnKeyedList handle $tmpHandleList
			keylset returnKeyedList device_handle $configedObjectHandleArr(Router)
            global $_hltNameSpace\msgHandleNameArr
			lappend $_hltNameSpace\msgHandleNameArr($portHandle) $configedObjectHandleArr(EoamMaintenancePointConfig)
        } 	
    }
    #end of for
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_config_msg_modify (str userInput str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em modify for emulation_oam_config_msg cmd
###
###This procedure execute the emulation_oam_config_msg_modify command when the mode is modify. It will modify Eoam msg session based on the \em -handle switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_config_msg_modify (str userInput str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::emulation_oam_config_msg_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_msg"    
    set _hltCmdName "emulation_oam_config_msg_modify"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Handle is needed while in modify mode." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    set msgHandleList [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    if {$msgHandleList == ""} {
        ::sth::sthCore::processError returnKeyedList "Input handle is null " "." {}
        set cmdState $FAILURE
        return $returnKeyedList         
    }
    set modeValue "modify"
    #get all handles of a msg
    foreach msgHandle $msgHandleList {
        
        if {![::sth::Eoam::IsMsgHandleValid $msgHandle]} {
            ::sth::sthCore::processError returnKeyedList "Input msg handle is not avialable." {}
            set cmdState $FAILURE
            return $returnKeyedList         
        }
        
            array set configedObjectHandleArr {
                EoamPortConfig ""
                EoamMegConfig ""
                EoamRemoteMegEndPointConfig ""
                Router ""
                EthIIIf ""
                VlanIf ""
                VlanIf_Outer ""
                EoamNodeConfig ""
                EoamMaintenancePointConfig ""
                EoamMaintenancePointConfig_MIP ""
                EoamMaintenancePointConfig_MEP ""
                EoamContChkCommandConfig ""
                EoamLoopbackCommandConfig ""
                EoamLinkTraceCommandConfig ""
				EoamDelayMeasurementCommandConfig ""
				EoamLossMeasurementCommandConfig ""
				EoamSlmCommandConfig ""
				EoamAisCommandConfig ""
				EoamLckCommandConfig ""
            }
        
        set configedObjectHandleArr(EoamMaintenancePointConfig) $msgHandle
            
        if {[catch {set EoamNodeHandle [::sth::sthCore::invoke stc::get $msgHandle -Parent]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while getting EoamNodeConfig from $msgHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        lappend configedObjectHandleArr(EoamNodeConfig) $EoamNodeHandle
        
        if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $EoamNodeHandle -Parent]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while getting Router from $EoamNodeHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        lappend configedObjectHandleArr(Router) $routerHandle
        
        #get IpIf handle
        if {[catch {set ipIfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-Ipv4If]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting Ipv4If from $routerHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        if {$ipIfHandle == ""} {
            if {[catch {set ipIfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-Ipv6If]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error ocured when gettting Ipv6If from $routerHandle errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList             
            }            
        }
        lappend configedObjectHandleArr(IpIf) $ipIfHandle      
        
         #get EthiiIf handle
        if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-EthIIIf]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting EthIIIf from $routerHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        lappend configedObjectHandleArr(EthIIIf) $EthIIIfHandle
        
        #get vlanif handle
        if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-VlanIf]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting VlanIf from $routerHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList                           
        }                    
        if {[llength $VlanIfHandle] == 2} {
            #There is S-Vlan and C-vlan
            lappend configedObjectHandleArr(VlanIf_Outer) [lindex $VlanIfHandle 1]
            lappend configedObjectHandleArr(VlanIf) [lindex $VlanIfHandle 0]
        } elseif {[llength $VlanIfHandle] == 1} {
            # There is vlan
            lappend configedObjectHandleArr(VlanIf) $VlanIfHandle
        }       
        
        if {[catch {set portHandle [::sth::sthCore::invoke stc::get $routerHandle -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting -AffiliationPort-Targets from $routerHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        if {[catch {set EoamPorthandle [::sth::sthCore::invoke stc::get $portHandle -Children-EoamPortConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting -Children-EoamPortConfig from $portHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        lappend configedObjectHandleArr(EoamPortConfig) $EoamPorthandle
        
        if {[catch {set MegHandle [::sth::sthCore::invoke stc::get $msgHandle -MegAssociation-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting -MegAssociation-Targets from $msgHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        lappend configedObjectHandleArr(EoamMegConfig) $MegHandle
        
        if {![catch {set handleList [::sth::sthCore::invoke stc::get $msgHandle -Children]} errMsg]} {
            foreach handle $handleList {
                switch -glob $handle {
                    *contchkcommandconfig* {
                        set msgType "continuous_check"
                        lappend configedObjectHandleArr(EoamContChkCommandConfig) $handle
                        break
                    }
                    *delaymeasurementcommandconfig* {
                        set msgType "dm"
                        lappend configedObjectHandleArr(EoamDelayMeasurementCommandConfig) $handle
                        break
                    }
					*lossmeasurementcommandconfig* {
                        set msgType "lm"
                        lappend configedObjectHandleArr(EoamLossMeasurementCommandConfig) $handle
                        break
                    }
                    *slmcommandconfig* {
                        set msgType "slm"
                        lappend configedObjectHandleArr(EoamSlmCommandConfig) $handle
                        break
                    }
                    *aiscommandconfig* {
                        set msgType "ais"
                        lappend configedObjectHandleArr(EoamAisCommandConfig) $handle
                        break
                    }
                    *lckcommandconfig* {
                        set msgType "lck"
                        lappend configedObjectHandleArr(EoamLckCommandConfig) $handle
                        break
                    }
                    *linktracecommandconfig* {
                        set msgType "linktrace"
                        lappend configedObjectHandleArr(EoamLinkTraceCommandConfig) $handle
                        break
                    }
                    *loopbackcommandconfig* {
                        if {[catch {set frameConfig [::sth::sthCore::invoke stc::get $msgHandle -LbmOptionalTlvs]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting -LbmOptionalTlvs from $msgHandle errMsg: $errMsg." 
                            set cmdState $FAILURE
                            return $returnKeyedList                             
                        }
                        if {[string first $frameConfig "EOAMTLV:TestTLV"] > -1} {
                            set msgType "test"
                        } else {
                            set msgType "loopback"
                        }
                        lappend configedObjectHandleArr(EoamLoopbackCommandConfig) $handle
                    }
                }
                #end of switch
            }
            #end of foreach
        } else {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting -Children from $msgHandle errMsg: $errMsg." 
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        #end of if
        
        ::sth::sthCore::log debug "finished getting object handle, successfully."
        
	#process attribute config
	array set configedObjectAttributeArr {
	    EoamPortConfig ""
	    EoamMegConfig ""
	    EoamRemoteMegEndPointConfig ""
	    Router ""
	    EthIIIf ""
        IpIf ""
	    VlanIf ""
	    VlanIf_Outer ""
	    EoamNodeConfig ""
	    EoamMaintenancePointConfig ""
	    EoamMaintenancePointConfig_MIP ""
	    EoamMaintenancePointConfig_MEP ""
	    EoamContChkCommandConfig ""
        EoamLoopbackCommandConfig ""
        EoamLinkTraceCommandConfig ""
		EoamDelayMeasurementCommandConfig ""
		EoamLossMeasurementCommandConfig ""
		EoamSlmCommandConfig ""
		EoamAisCommandConfig ""
		EoamLckCommandConfig ""
	}
        set PDUFrameSwitchList ""
        
	set userInputList [array get ${_hltSpaceCmdName}\_user_input_args_array]
	foreach {switchName switchValue} $userInputList {
	    ::sth::sthCore::log debug "Process switch:$switchName value:$switchValue config"
	    
	    if { $switchName == "optional_args" } {
		continue
	    }
	    
	    if { $switchName == "mandatory_args" } {
		continue
	    }

            if { $switchName == "sut_ip_address"} {
                if {[string first ":" $switchValue] > -1} {
                    set switchValue [::sth::sthCore::normalizeIPv6Addr $switchValue]
                }
            }
            
	    set switchProcFunc [::sth::sthCore::getModeFunc2 $_hltNameSpace $_OrigHltCmdName $switchName $modeValue]
	    
        #set unicast dst mac to type XX-XX-XX-XX-XX-XX
	    if {$switchName == "mac_dst"} {
            set switchValue [join [split $switchValue ":"] "-"]
        }
	    
	    if {[string equal $switchProcFunc "ProcessConfigCmd"]} {
            set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
            set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
                append configedObjectAttributeArr($stcObjName) " -$stcAttrName $attrValue"
            } else {
                append configedObjectAttributeArr($stcObjName) " -$stcAttrName $switchValue"
            } 
	    } elseif {[string equal $switchProcFunc "ProcessCommmandConfig"]} {
            set msgCmdName ""
            switch -exact $msgType {
                loopback {
                    set msgCmdName "Loopback"
                }
                linktrace {
                    set msgCmdName "LinkTrace"
                }
                test {
                    set msgCmdName "Loopback"
                    #TODO finish
                }
            }
            set stcObjName "Eoam$msgCmdName\CommandConfig"
            
            if {$switchName == "transmit_mode"} {
                set stcAttrName "$msgCmdName\TxType"
            } elseif {$switchName == "pkts_per_burst"} {
                set stcAttrName "$msgCmdName\BurstSize"
            } elseif {$switchName == "rate_pps"} {
                set stcAttrName "$msgCmdName\BurstRate"
            } elseif {$switchName == "ttl"} {
                if {$msgType != "linktrace"} {
                    puts "Warning: Ttl can only be configured when msg_tpye is linktrace. ttl now can not be configured."
                    ::sth::sthCore::log debug "Warning: Ttl can only be configured when msg_tpye is linktrace. ttl now can not be configured."
                    continue
                } 
                
                set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            } else {
                set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            }
            if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
                append configedObjectAttributeArr($stcObjName) " -$stcAttrName $attrValue"
            } else {
                append configedObjectAttributeArr($stcObjName) " -$stcAttrName $switchValue"
            }
            } elseif {[string equal $switchProcFunc "ProcessVlanConfig"]} {
                set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
                set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
                #convert HEX to decimal
                set decVlantype [format "%i" $switchValue] 
                if {$switchName == "vlan_ether_type"} {
                    append configedObjectAttributeArr($stcObjName) " -$stcAttrName $decVlantype"
                }
                if {$switchName == "vlan_outer_ether_type"} {
                    append configedObjectAttributeArr($stcObjName) " -$stcAttrName $decVlantype"
                }
            } elseif {[string equal $switchProcFunc "ProcessFrameConfig"]} {
                lappend PDUFrameSwitchList $switchName $switchValue
            } else {
                #TODO finish
            }
	    #end of if elseif else
	}
        #end of foreach
	::sth::sthCore::log debug [array get configedObjectAttributeArr]
    ::sth::sthCore::log debug [array get configedObjectHandleArr]
    set objectTypeList [array names configedObjectHandleArr]
	foreach objectType $objectTypeList {
            if {![string equal $configedObjectHandleArr($objectType) ""] &&
                ![string equal $configedObjectHandleArr($objectType) "{}"]} {
                foreach objectHandle $configedObjectHandleArr($objectType) {
                    ::sth::sthCore::log debug "process objectHandle:$objectHandle, configedObjectAttributeArr($objectType):$configedObjectAttributeArr($objectType)"
                    if {![string equal $configedObjectAttributeArr($objectType) ""]} {
                        ::sth::sthCore::log debug "Process config $objectHandle $configedObjectAttributeArr($objectType)"
                        if {[catch {::sth::sthCore::invoke stc::config $objectHandle $configedObjectAttributeArr($objectType)} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Error ocured when config $objectHandle $configedObjectAttributeArr($objectType) errMsg: $errMsg." {}
                            set cmdState $FAILURE
                            return $returnKeyedList                    
                        }                
                    }
                }                
            }
	}
	::sth::sthCore::log debug "Process profunc cmd config successfully"
	
    #Eoam PDU frame config, TLV config
	if {![::sth::Eoam::ProcessFrameConfig $msgType $configedObjectHandleArr(EoamMaintenancePointConfig) $PDUFrameSwitchList $userInput]} {
            ::sth::sthCore::processError returnKeyedList "Error Occured while process PDU Frame config."
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {$cmdState} {
            set tmpHandleList {}
            catch {set tmpHandleList [keylget returnKeyedList handle]}
            lappend tmpHandleList $configedObjectHandleArr(EoamMaintenancePointConfig)
            keylset returnKeyedList handle $tmpHandleList
        }     
    }
    #end of foreach
    

}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_config_msg_reset (str userInput str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em reset for emulation_oam_config_msg cmd
###
###This procedure execute the emulation_oam_config_msg command when the mode is reset. It will dlelete Eoam msg session based on the \em -handle switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_config_msg_reset (str userInput str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::emulation_oam_config_msg_reset { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_msg"    
    set _hltCmdName "emulation_oam_config_msg_reset"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "do not input Eoam msg handle." {}
        set cmdState $FAILURE
        return $returnKeyedList         
    }
    set msgHandleList [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    
    foreach msgHandle $msgHandleList {
        if {![::sth::Eoam::IsMsgHandleValid $msgHandle]} {
            ::sth::sthCore::processError returnKeyedList "Input msg handle is not avialable." {}
            set cmdState $FAILURE
            return $returnKeyedList         
        }
        
        if {[catch {set EoamNodeHandle [::sth::sthCore::invoke stc::get $msgHandle -Parent]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while getting EoamNodeConfig from $msgHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $EoamNodeHandle -Parent]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while getting Router from $EoamNodeHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        if {[catch {set MegHandle [::sth::sthCore::invoke stc::get $msgHandle -MegAssociation-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting -MegAssociation-Targets from $msgHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        
        lappend routerHandleList $routerHandle

        if {![string equal $MegHandle ""]} {
            if {[catch {::sth::sthCore::invoke stc::delete $MegHandle} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error ocured when delete $MegHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList             
            }
        }
        
        foreach arrayName [array names $_hltNameSpace\msgHandleNameArr] {
            set XCount [lsearch [set $_hltNameSpace\msgHandleNameArr($arrayName)] $msgHandle]
            set $_hltNameSpace\msgHandleNameArr($arrayName) [lreplace [set $_hltNameSpace\msgHandleNameArr($arrayName)] $XCount $XCount]
        }
    }

    if {[catch {::sth::sthCore::invoke stc::perform delete -ConfigList $routerHandleList} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error ocured when delete $routerHandle, errMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList            
    }

    set cmdState $SUCCESS
    return $returnKeyedList    
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_config_topology_create (str userInput str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em create for emulation_oam_config_topology_create cmd
###
###This procedure execute the emulation_oam_config_topology_create command when the mode is create. It will create Eoam topology session based on the \em -count switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_config_topology_create (str userInput str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::emulation_oam_config_topology_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "emulation_oam_config_topology_create"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    #Check if te port_handle is valid
    if {![::info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when creating EOAM Topology"
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
    }
	
    if {![::sth::sthCore::IsPortValid $portHandle msg]} {
	::sth::sthCore::processError returnKeyedList "Invalid Value of port_handle,$msg"
	set cmdState $FAILURE
	return $returnKeyedList
    }

    set modeValue "create"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(count)]} {
        set ${_hltSpaceCmdName}\_user_input_args_array(count) 1
    }

    set topologyNum [set ${_hltSpaceCmdName}\_user_input_args_array(count)]
    
    for {set topologyCount 0} {$topologyCount < $topologyNum} {incr topologyCount} {
        
        set cmdReturn \{[::sth::Eoam::ProcessObjectsCreate_Topology returnKeyedList cmdState]\}
        
        if {$cmdState} {
            set cmd "array set configedObjectHandleArr $cmdReturn"
            ::sth::sthCore::log debug $cmd
            eval $cmd
            ::sth::sthCore::log debug [array get configedObjectHandleArr]
        } else {
            ::sth::sthCore::processError returnKeyedList "error creating objects of Eoam topology."
            return $returnKeyedList
        }
        
        ::sth::sthCore::log debug "Objects created successfully" 
            
        ::sth::Eoam::ProcessSwitchConfig returnKeyedList cmdState configedObjectHandleArr
        
        if {$cmdState} {
            ::sth::sthCore::log debug "Process switch config successfully."
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting ::sth::Eoam::ProcessSwitchConfig."
            return $returnKeyedList
        }
        
        #copy configedObjectHandleArr to global variable TopologyHandleArr as the handle of whole topology
        set i 0    
        while {1} {
            if {![info exists ::sth::Eoam::$portHandle\.TopologyHandleArr$i]} {
                global array set ::sth::Eoam::$portHandle\.TopologyHandleArr$i {}
                array set $portHandle\.TopologyHandleArr$i [array get configedObjectHandleArr]
                set TopologyHandle ::sth::Eoam::$portHandle\.TopologyHandleArr$i
                ::sth::sthCore::log debug "Topology handle : $TopologyHandle, [array get ::sth::Eoam::$portHandle\.TopologyHandleArr$i]"
                break
            } else {
                incr i
            }
        }
        ::sth::sthCore::log debug "Topology handle created successfully"       
        
        if {$cmdState} {
            set tmpHandleList {}
            catch {set tmpHandleList [keylget returnKeyedList handle]}
            lappend tmpHandleList $TopologyHandle
            keylset returnKeyedList handle $tmpHandleList
            lappend $_hltNameSpace\topologyHandleNameArr($portHandle) $TopologyHandle
        }          
    }

    #apply all configurations
    ::sth::sthCore::invoke stc::apply
        
    set cmdState $SUCCESS
    return $returnKeyedList
    
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_config_topology_modify (str userInput str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em modify for emulation_oam_config_topology cmd
###
###This procedure execute the emulation_oam_config_topology_modify command when the mode is modify. It will modify Eoam topology session based on the \em -handle switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_config_topology_modify (str userInput str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::emulation_oam_config_topology_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "emulation_oam_config_topology_modify"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    set modeValue "modify"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Need input handle." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    set topologyHandle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    
    if {![::sth::Eoam::IsTopologyHandleValid $topologyHandle]} {
        ::sth::sthCore::processError returnKeyedList "Error while validating topology handle."
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    
    ::sth::sthCore::log debug [array get $topologyHandle]
    array set configedObjectHandleArr [array get $topologyHandle]
    ::sth::sthCore::log debug [array get configedObjectHandleArr]
    
        #genneral config, profunc "ProcessConfigCmd"
            
        ::sth::Eoam::ProcessSwitchConfig returnKeyedList cmdState configedObjectHandleArr
        if {$cmdState} {
            ::sth::sthCore::log debug "Process switch config successfully."
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting ::sth::Eoam::ProcessSwitchConfig."
            return $returnKeyedList
        }
        
    keylset returnKeyedList handle $topologyHandle
    set cmdState $SUCCESS
    return $returnKeyedList
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_config_topology_reset (str userInput str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em reset for emulation_oam_config_msg cmd
###
###This procedure execute the emulation_oam_config_topology command when the mode is reset. It will dlelete Eoam topology session based on the \em -handle switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_config_topology_reset (str userInput str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::emulation_oam_config_topology_reset { userInput returnKeyedListVarName cmdStatusVarName } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "emulation_oam_config_topology_modify"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Need input handle." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    set topologyHandleList [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    
    foreach topologyHandle $topologyHandleList {
        if {![::sth::Eoam::IsTopologyHandleValid $topologyHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error while validating topology handle." 
            set cmdState $FAILURE
            return $returnKeyedList          
        }
        foreach handleType {EoamMegConfig Router} {
            foreach handle [set $topologyHandle\($handleType)] {
                if {[catch {::sth::sthCore::invoke stc::delete $handle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error deleting Eoam $handleType Object, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList            
                }                
            }
        }
        
        set portHandle [lindex [split [lindex [split $topologyHandle "::"] end] "."] 0]
        set XCount [lsearch [set $_hltNameSpace\topologyHandleNameArr($portHandle)] $topologyHandle]
        set $_hltNameSpace\topologyHandleNameArr($portHandle) [lreplace [set $_hltNameSpace\topologyHandleNameArr($portHandle)] $XCount $XCount]
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_control_start (str args)
###\brief Process \em -mode switch with value \em start for emulation_oam_control_start cmd
###
###This procedure executes the emulation_oam_control command when the mode is start. It will start eoam session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_control_start (str args);
###
proc ::sth::Eoam::emulation_oam_control_start { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_control"    
    set _hltCmdName "emulation_oam_control_start"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
  
    set handleList ""
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
            append handleList " [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]"
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
            foreach portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)] {
                catch {append handleList " [set $_hltNameSpace\topologyHandleNameArr($portHandle)]"}
                catch {append handleList " [set $_hltNameSpace\msgHandleNameArr($portHandle)]"}
            }
        }        
    } else {
        ::sth::sthCore::processError returnKeyedList "Need input handle or port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
     #set handleList [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    
    foreach handle $handleList {
        if {[string match -nocase "*topology*" $handle]} {
            set handleType "Topology"
            if {![::sth::Eoam::IsTopologyHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Error while validating topology handle."
                set cmdState $FAILURE
                return $returnKeyedList       
            }
            
            set startHandleList [set $handle\(EoamContChkCommandConfig)]
            #start topology
            if {[catch {::sth::sthCore::invoke stc::perform EoamStartContChkCommand -ContChkConfigList $startHandleList} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error starting the Eoam topology.errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                 
            }
            
        } else {
            set handleType "Msg"
            if {![::sth::Eoam::IsMsgHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Input msg handle is not avialable." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            }
            
            set msgType ""
			if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]} {
				set msg_type [set ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]
				switch -glob $msg_type {
					continuous_check {
						set msgType "ContChk" 
					}
					loopback {
						set msgType "Loopback" 
					}
					linktrace {
						set msgType "LinkTrace" 
					}
					dm {
						set msgType "DelayMeasurement" 
					}
					lm {
						set msgType "LossMeasurement" 
					}
					slm {
						set msgType "Slm" 
					}
					ais {
						set msgType "Ais" 
					}
					lck {
						set msgType "Lck" 
					}
				}
				set startHandle [::sth::sthCore::invoke stc::get $handle -Children-Eoam$msgType\CommandConfig]
			} else {
				#get EoamXXCommandConfig, use to check Msg Type
				if {[catch {set childHandleList [::sth::sthCore::invoke stc::get $handle -Children]} errMsg]} {
					::sth::sthCore::processError returnKeyedList "Error ocured when excuting \"stc::GetNew $handle -Children\", errMsg: $errMsg." {}
					set cmdState $FAILURE
					return $returnKeyedList             
				} else {
					foreach childHandle $childHandleList {
						switch -glob $childHandle {
							*contchkcommandconfig* {
								set msgType "ContChk" 
								set startHandle $childHandle
								break
							}
							*delaymeasurementcommandconfig* {
								set msgType "DelayMeasurement" 
								set startHandle $childHandle
								break
							}
							*lossmeasurementcommandconfig* {
								set msgType "LossMeasurement" 
								set startHandle $childHandle
								break
							}
							*slmcommandconfig* {
								set msgType "Slm" 
								set startHandle $childHandle
								break
							}
							*aiscommandconfig* {
								set msgType "Ais" 
								set startHandle $childHandle
								break
							}
							*lckcommandconfig* {
								set msgType "Lck" 
								set startHandle $childHandle
								break
							}
							*linktracecommandconfig* {
								set msgType "LinkTrace"
								set startHandle $childHandle
								break
							}
							*loopbackcommandconfig* {
								if {[catch {set frameConfig [::sth::sthCore::invoke stc::get $handle -LbmOptionalTlvs]} errMsg]} {
									::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $handle -LbmOptionalTlvs\", errMsg: $errMsg." {}
									set cmdState $FAILURE
									return $returnKeyedList                                 
								}
								if {[string first "EOAMTLV:TestTLV" $frameConfig] > -1} {
									set msgType "Loopback"
								} else {
									set msgType "Loopback"
								}
								set startHandle $childHandle
							}
						}
						#end of switch
					}
					#end of foreach
				}
            }
            
			if {$startHandle != ""} {
				if {[catch {::sth::sthCore::invoke stc::perform EoamStart$msgType\Command -$msgType\ConfigList $startHandle} errMsg]} {
					::sth::sthCore::processError returnKeyedList "Error starting the Eoam Msg, errMsg: $errMsg" {}
					set cmdState $FAILURE
					return $returnKeyedList                
				}
			}
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_control_stop (str args)
###\brief Process \em -mode switch with value \em start for emulation_oam_control_stop cmd
###
###This procedure executes the emulation_oam_control command when the mode is stop. It will stop eoam session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_control_stop (str args);
###
proc ::sth::Eoam::emulation_oam_control_stop { userInput returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_control"    
    set _hltCmdName "emulation_oam_control_stop"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    set handleList ""
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
            append handleList " [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]"
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
            foreach portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)] {
                catch {append handleList " [set $_hltNameSpace\topologyHandleNameArr($portHandle)]"}
                catch {append handleList " [set $_hltNameSpace\msgHandleNameArr($portHandle)]"}
            }
        }       
    } else {
        ::sth::sthCore::processError returnKeyedList "Need input handle or port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    foreach handle $handleList {
        if {[string match -nocase "*topology*" $handle]} {
            set handleType "Topology"
            if {![::sth::Eoam::IsTopologyHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Error while validating topology handle."
                set cmdState $FAILURE
                return $returnKeyedList              
            }
            
            set stopHandleList [set $handle\(EoamMaintenancePointConfig_MEP)]
            if {[catch {::sth::sthCore::invoke stc::perform EoamStopContChkCommand -MepList $stopHandleList} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error stopping the Eoam topology.errMsg: $errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList                 
            }
            
        } else {
            set handleType "Msg"
            if {![::sth::Eoam::IsMsgHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Input msg handle is not avialable." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            }
            
            set msgType ""
			if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]} {
				set msg_type [set ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]
				switch -glob $msg_type {
					continuous_check {
						set msgType "ContChk" 
					}
					loopback {
						set msgType "Loopback" 
					}
					linktrace {
						set msgType "LinkTrace" 
					}
					dm {
						set msgType "DelayMeasurement" 
					}
					lm {
						set msgType "LossMeasurement" 
					}
					slm {
						set msgType "Slm" 
					}
					ais {
						set msgType "Ais" 
					}
					lck {
						set msgType "Lck" 
					}
				}
			} else {
				if {[catch {set childHandleList [::sth::sthCore::invoke stc::get $handle -Children]} errMsg]} {
					::sth::sthCore::processError returnKeyedList "Error ocured when excuting \"stc::GetNew $handle -Children\", errMsg: $errMsg." {}
					set cmdState $FAILURE
					return $returnKeyedList             
				} else {
					foreach childHandle $childHandleList {
						switch -glob $childHandle {
							*contchkcommandconfig* {
								set msgType "ContChk" 
								set startHandle $childHandle
								break
							}
							*delaymeasurementcommandconfig* {
								set msgType "DelayMeasurement" 
								set startHandle $childHandle
								break
							}
							*lossmeasurementcommandconfig* {
								set msgType "LossMeasurement" 
								set startHandle $childHandle
								break
							}
							*slmcommandconfig* {
								set msgType "Slm" 
								set startHandle $childHandle
								break
							}
							*aiscommandconfig* {
								set msgType "Ais" 
								set startHandle $childHandle
								break
							}
							*lckcommandconfig* {
								set msgType "Lck" 
								set startHandle $childHandle
								break
							}
							*linktracecommandconfig* {
								set msgType "LinkTrace"
								set startHandle $childHandle
								break
							}
							*linktracecommandconfig* {
								set msgType "LinkTrace"
								#set stopHandleList $childHandle
								break
							}
							*loopbackcommandconfig* {
								if {[catch {set frameConfig [::sth::sthCore::invoke stc::get $handle -LbmOptionalTlvs]} errMsg]} {
									::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $handle -LbmOptionalTlvs\", errMsg: $errMsg." {}
									set cmdState $FAILURE
									return $returnKeyedList                                
								}
								if {[string first "EOAMTLV:TestTLV" $frameConfig] > -1} {
									set msgType "Loopback"
								} else {
									set msgType "Loopback"
								}
								#set stopHandleList $childHandle
							}
						}
						#end of switch
					}
					#end of foreach
				}
			}            
            if {[catch {::sth::sthCore::invoke stc::perform EoamStop$msgType\Command -MepList $handle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error stopping the Eoam Msg.errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                 
            }
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList    
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_control_reset (str args)
###\brief Process \em -mode switch with value \em start for emulation_oam_control_reset cmd
###
###This procedure executes the emulation_oam_control command when the mode is reset. It will stop eoam session based on the handle switch value, and then clear all the result stats to 0.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_control_reset (str args);
###
proc ::sth::Eoam::emulation_oam_control_reset { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_control"    
    set _hltCmdName "emulation_oam_control_stop"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    set handleList ""
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
            append handleList " [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]"
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
            foreach portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)] {
                catch {append handleList " [set $_hltNameSpace\topologyHandleNameArr($portHandle)]"}
                catch {append handleList " [set $_hltNameSpace\msgHandleNameArr($portHandle)]"}
            }
        }       
    } else {
        ::sth::sthCore::processError returnKeyedList "Need input handle or port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #stop Eoam
    foreach handle $handleList {
        if {[string match -nocase "*topology*" $handle]} {
            set handleType "Topology"
            if {![::sth::Eoam::IsTopologyHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Error while validating topology handle."
                set cmdState $FAILURE
                return $returnKeyedList          
            }
            
            set stopHandleList [set $handle\(EoamMaintenancePointConfig_MEP)]
            if {[catch {::sth::sthCore::invoke stc::perform EoamStopContChkCommand -MepList $stopHandleList} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error stopping the Eoam topology.errMsg: $errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList                 
            }
            
        } else {
            set handleType "Msg"
            if {![::sth::Eoam::IsMsgHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Input msg handle is not avialable." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            }
            
            set msgType ""
			if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]} {
				set msg_type [set ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]
				switch -glob $msg_type {
					continuous_check {
						set msgType "ContChk" 
					}
					loopback {
						set msgType "Loopback" 
					}
					linktrace {
						set msgType "LinkTrace" 
					}
					dm {
						set msgType "DelayMeasurement" 
					}
					lm {
						set msgType "LossMeasurement" 
					}
					slm {
						set msgType "Slm" 
					}
					ais {
						set msgType "Ais" 
					}
					lck {
						set msgType "Lck" 
					}
				}
			} else {
				if {[catch {set childHandleList [::sth::sthCore::invoke stc::get $handle -Children]} errMsg]} {
					::sth::sthCore::processError returnKeyedList "Error ocured when excuting \"stc::GetNew $handle -Children\", errMsg: $errMsg." {}
					set cmdState $FAILURE
					return $returnKeyedList             
				} else {
					foreach childHandle $childHandleList {
						switch -glob $childHandle {
							*contchkcommandconfig* {
								#TODO finish
								set msgType "ContChk" 
								break
							}
							*delaymeasurementcommandconfig* {
								set msgType "DelayMeasurement" 
								break
							}
							*lossmeasurementcommandconfig* {
								set msgType "LossMeasurement" 
								break
							}
							*slmcommandconfig* {
								set msgType "Slm" 
								break
							}
							*aiscommandconfig* {
								set msgType "Ais" 
								break
							}
							*lckcommandconfig* {
								set msgType "Lck" 
								break
							}
							*linktracecommandconfig* {
								set msgType "LinkTrace"
								break
							}
							*linktracecommandconfig* {
								set msgType "LinkTrace"
								#set stopHandleList $childHandle
								break
							}
							*loopbackcommandconfig* {
								if {[catch {set frameConfig [::sth::sthCore::invoke stc::get $handle -LbmOptionalTlvs]} errMsg]} {
									::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $handle -LbmOptionalTlvs\", errMsg: $errMsg." {}
									set cmdState $FAILURE
									return $returnKeyedList                                
								}
								if {[string first "EOAMTLV:TestTLV" $frameConfig] > -1} {
									set msgType "Loopback"
								} else {
									set msgType "Loopback"
								}
								#set stopHandleList $childHandle
							}
						}
						#end of switch
					}
					#end of foreach
				}
            }
            if {[catch {::sth::sthCore::invoke stc::perform EoamStop$msgType\Command -MepList $handle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error stopping the Eoam Msg.errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                 
            }
        }
    }
    
    #clear all the result statistics
    if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAllProtocolCommand} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error clearing result stats." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList 
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_info_aggregate (str args)
###\brief Process \em -mode switch with value \em agregate for emulation_oam_info cmd
###
###This procedure execute the emulation_oam_info command when the mode is aggregate. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###author Yulin Chen (Ychen)
###*/
###
###emulation_oam_info_aggregate (str args);
###
proc ::sth::Eoam::emulation_oam_info_aggregate { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_info"    
    set _hltCmdName "emulation_oam_info_aggregate"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    array set resultObjectHandleArr {
        EoamPortResults ""
        EoamContChkLocalResults ""
        EoamLinkTraceResults ""
        EoamLoopbackResults ""
        EoamMegResults ""
		EoamDelayMeasurementResults	""
		EoamLckResults	""
		EoamLossMeasurementResults	""
		EoamSlmResults	""
		EoamAisResults	""
    }
    if {![::sth::Eoam::SubscribeEoamResultdataset]} {
        ::sth::sthCore::processError returnKeyedList "Internal command error while subscribing Eoam Results." {}
        set cmdState $FAILURE
        return $returnKeyedList                
    }
    if {[::info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
        set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
        #Check if te port_handle is valid
        if {![::sth::sthCore::IsPortValid $portHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "Invalid Value of port_handle, $msg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {set portEoamHandle [::sth::sthCore::invoke stc::get $portHandle -Children-EoamPortConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $portHandle -Children-EoamPortConfig\", errMsg: $errMsg."
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        if {[catch {set portResultHandle [::sth::sthCore::invoke stc::get $portEoamHandle -Children-EoamPortResults]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $portHandle -Children-EoamPortResults\", errMsg: $errMsg."
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        set resultObjectHandleArr(EoamPortResults) $portResultHandle
        
        set portMsgHandleList ""
        if {[info exists $_hltNameSpace\msgHandleNameArr($portHandle)]} {
            set portMsgHandleList [set $_hltNameSpace\msgHandleNameArr($portHandle)] 
        }
        set portTopologyHandleList ""
        if {[info exists $_hltNameSpace\topologyHandleNameArr($portHandle)]} {
            set portTopologyHandleList [set $_hltNameSpace\topologyHandleNameArr($portHandle)]
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(action)]} {
            set actionType [set ${_hltSpaceCmdName}\_user_input_args_array(action)]
            
            if { $actionType == "get_topology_stats"} {
                #get topology stats
                set TopologyResultsFlag 1
                set MsgResultsFlag 0
            } elseif {$actionType == "get_message_stats"} {
                set TopologyResultsFlag 0
                set MsgResultsFlag 1
            }
        } else {
                set TopologyResultsFlag 1
                set MsgResultsFlag 1
        }
            
        if {$TopologyResultsFlag } {
            #get topology result object handle
            foreach portTopologyHandle $portTopologyHandleList {
                if {$portTopologyHandle == ""} {
                    continue
                }
                
                if {![::sth::Eoam::GetTopologyResultHandle $portTopologyHandle resultObjectHandleArr returnKeyedList cmdState]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"::sth::Eoam::GetTopologyResultHandle $portTopologyHandle resultObjectHandleArr returnKeyedList cmdState\"."
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                } else {
                    ::sth::sthCore::log debug "Successfully get topology result objects handles."
                }
            }
        }
        
        if {$MsgResultsFlag} {
            #get msg result object handle
            foreach portMsgHandle $portMsgHandleList {
                if {$portMsgHandle == ""} {
                    continue
                }
                
                if {![::sth::Eoam::GetMsgResultHandle $portMsgHandle resultObjectHandleArr returnKeyedList cmdState]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"::sth::Eoam::GetMsgResultHandle $portMsgHandle resultObjectHandleArr returnKeyedList cmdState\"."
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                } else {
                    ::sth::sthCore::log debug "Successfully get msg result objects handles."
                }
            }                
        }
    } elseif {[::info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        set topologyHandle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
        
        #check if topology handle is available
        if {![::sth::Eoam::IsTopologyHandleValid $topologyHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error while validating topology handle."
            set cmdState $FAILURE
            return $returnKeyedList
        }
        set TopologyResultsFlag 1
        
        set portEoamHandle [set $topologyHandle\(EoamPortConfig)]
        
        if {[catch {set portResultHandle [::sth::sthCore::invoke stc::get $portEoamHandle -Children-EoamPortResults]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $portHandle -Children-EoamPortResults\", errMsg: $errMsg."
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        set resultObjectHandleArr(EoamPortResults) $portResultHandle
        
        if {![::sth::Eoam::GetTopologyResultHandle $topologyHandle resultObjectHandleArr returnKeyedList cmdState]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"::sth::Eoam::GetTopologyResultHandle $topologyHandle resultObjectHandleArr returnKeyedList cmdState\"."
            set cmdState $FAILURE
            return $returnKeyedList                     
        }        
    } else {
    	::sth::sthCore::processError returnKeyedList "port_handle/handle needed when getting aggregate Eoam info." {}
    	set cmdState $FAILURE
        return $returnKeyedList        
    }
    
    ::sth::sthCore::log debug [array get resultObjectHandleArr]
    set aggregateReturnKeyType {rx tx error detected_failure_stats states}
    foreach returnKeyType $aggregateReturnKeyType {
        ::sth::Eoam::GetEoamInfo_aggregate $returnKeyType resultObjectHandleArr returnKeyedList cmdState
        if {$cmdState} {
            ::sth::sthCore::log debug "Successfully get results info of $returnKeyType."
        } else {
            ::sth::sthCore::processError returnKeyedList "error geting results info of $returnKeyType." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    #get topology_stats
    if {$TopologyResultsFlag  && [info exists ${_hltSpaceCmdName}\_user_input_args_array(action)]} {
        set returnKeyType "topology_stats"
        set returnKeyNameList [array names $_hltNameSpace$_hltCmdName\_$returnKeyType\_mode]
        
        foreach returnKeyName $returnKeyNameList {
            set supported [set $_hltNameSpace$_hltCmdName\_$returnKeyType\_supported($returnKeyName)]
            if {$supported == "true"} {                    
                switch $returnKeyName {
                    total_md_levels {
                        set mdLevelList ""
                        foreach megResultHandle $resultObjectHandleArr(EoamMegResults) {
                            if {[catch {set Mdlevel [::sth::sthCore::invoke stc::get $megResultHandle -MeLevel]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "error excuting \"stc::GetNew $megResultHandle -MeLevel\" , errMsg: $errMsg." {}
                                set cmdState $FAILURE
                                return $returnKeyedList                                    
                            }
                            if {[string first $Mdlevel $mdLevelList] <= -1} {
                                lappend mdLevelList $Mdlevel
                            }
                            
                        }
                        keylset returnKeyedList aggregate.$returnKeyType.$returnKeyName [llength $mdLevelList]
                    }
                    operational_md_levels {
                        set mdLevelList ""
                        foreach megResultHandle $resultObjectHandleArr(EoamMegResults) {
                            if {[catch {set Mdlevel [::sth::sthCore::invoke stc::get $megResultHandle -MeLevel]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "error excuting \"stc::GetNew $megResultHandle -MeLevel\" , errMsg: $errMsg." {}
                                set cmdState $FAILURE
                                return $returnKeyedList                                    
                            }
                            if {[catch {set ContChkTxState [::sth::sthCore::invoke stc::get $megResultHandle -ContChkTxState]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "error excuting \"stc::GetNew $megResultHandle -ContChkTxState\" , errMsg: $errMsg." {}
                                set cmdState $FAILURE
                                return $returnKeyedList                                    
                            }
                            if {$ContChkTxState == "UP"} {
                                if {[string first $Mdlevel $mdLevelList] <= -1} {
                                    lappend mdLevelList $Mdlevel
                                }                                
                            }
                            
                        }
                        keylset returnKeyedList aggregate.$returnKeyType.$returnKeyName [llength $mdLevelList]
                    }
                    total_maintenance_points {
                        set totalMepNum 0
                        foreach megResultHandle $resultObjectHandleArr(EoamMegResults) {
                            if {[catch {set tmpMepNum [::sth::sthCore::invoke stc::get $megResultHandle -NumOfMegEndPoints]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "error excuting \"stc::GetNew $megResultHandle -NumOfMegEndPoints\" , errMsg: $errMsg." {}
                                set cmdState $FAILURE
                                return $returnKeyedList                                    
                            }
                            set totalMepNum [expr $totalMepNum + $tmpMepNum]
                            
                        }
                        keylset returnKeyedList aggregate.$returnKeyType.$returnKeyName $totalMepNum
                    }
                    operational_maintenance_points {
                        set totalOplMepNum 0
                        foreach ContChkResultHandle $resultObjectHandleArr(EoamContChkLocalResults) {
                            if {[catch {set ContChkTxCount [::sth::sthCore::invoke stc::get $ContChkResultHandle -ContChkTxCount]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "error excuting \"stc::GetNew $ContChkResultHandle -ContChkTxCount\" , errMsg: $errMsg." {}
                                set cmdState $FAILURE
                                return $returnKeyedList                                     
                            }
                            if {$ContChkTxCount >0} {
                                incr totalOplMepNum
                            }
                        }
                        keylset returnKeyedList aggregate.$returnKeyType.$returnKeyName $totalOplMepNum
                    }
                }
            }
        }
    }
        ::sth::Eoam::UnSubscribeEoamResultdataset
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

###/*! \ingroup eoamswitchprocfuncs
###\fn emulation_oam_info_session (str args)
###\brief Process \em -mode switch with value \em session for emulation_oam_info cmd
###
###This procedure execute the emulation_oam_info command when the mode is session. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###*/author Yulin Chen (Ychen)
###
###emulation_oam_info_session (str args);
###
proc ::sth::Eoam::emulation_oam_info_session { userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_info"    
    set _hltCmdName "emulation_oam_info_session"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Do not input handle." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    set oamHandle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    
    if {[string match -nocase "*topology*" $oamHandle ]} {
        ::sth::sthCore::processError returnKeyedList "In -mode session, cmd emulation_oam_info only support Msg handle." {}
        set cmdState $FAILURE
        return $returnKeyedList         
    } else {
        set handleType msg
    }
    
    array set resultObjectHandleArr {
        EoamPortResults ""
        EoamContChkLocalResults ""
        EoamLinkTraceResults ""
        EoamLoopbackResults ""
        EoamMegResults ""
		EoamDelayMeasurementResults	""
		EoamLckResults	""
		EoamLossMeasurementResults	""
		EoamSlmResults	""
		EoamAisResults	""
    }

    if {[catch {set handleList [::sth::sthCore::invoke stc::get $oamHandle -Children]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error ocured when excuting \"stc::GetNew $oamHandle -Children\", errMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList             
    } else {
        foreach handle $handleList {
            switch -glob $handle {
                *contchkcommandconfig* {
                    set msgType "continuous_check"
                    lappend configedObjectHandleArr(EoamContChkCommandConfig) $handle
                    break
                }
                *delaymeasurementcommandconfig* {
                    set msgType "dm" 
                    lappend configedObjectHandleArr(EoamDelayMeasurementCommandConfig) $handle
                    break
                }
                *lossmeasurementcommandconfig* {
                    set msgType "lm" 
                    lappend configedObjectHandleArr(EoamLossMeasurementCommandConfig) $handle
                    break
                }
                *slmcommandconfig* {
                    set msgType "slm" 
                    lappend configedObjectHandleArr(EoamSlmCommandConfig) $handle
                    break
                }
                *aiscommandconfig* {
                    set msgType "ais" 
                    lappend configedObjectHandleArr(EoamAisCommandConfig) $handle
                    break
                }
                *lckcommandconfig* {
                    set msgType "lck" 
                    lappend configedObjectHandleArr(EoamLckCommandConfig) $handle
                    break
                }
                *linktracecommandconfig* {
                    set msgType "linktrace"
                    lappend configedObjectHandleArr(EoamLinkTraceCommandConfig) $handle
                    break
                }
                *loopbackcommandconfig* {
                    if {[catch {set frameConfig [::sth::sthCore::invoke stc::get $oamHandle -LbmOptionalTlvs]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error ocured when excuting \"stc::GetNew $oamHandle -LbmOptionalTlvs\", errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList                            
                    }
                    
                    if {[string first "EOAMTLV:TestTLV" $frameConfig] > -1} {
                        set msgType "tst"
                    } else {
                        set msgType "loopback"
                    }
                    lappend configedObjectHandleArr(EoamLoopbackCommandConfig) $handle
                }
            }
            #end of switch
        }
        #end of foreach
    }
    #end of if
    if {![::sth::Eoam::SubscribeEoamResultdataset]} {
        ::sth::sthCore::processError returnKeyedList "Internal command error while subscribing Eoam Results." {}
        set cmdState $FAILURE
        return $returnKeyedList                
    }

    if {![::sth::Eoam::GetMsgResultHandle $oamHandle resultObjectHandleArr returnKeyedList cmdState]} {
        ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"::sth::Eoam::GetMsgResultHandle $oamHandle resultObjectHandleArr returnKeyedList cmdState\"."
        set cmdState $FAILURE
        return $returnKeyedList          
    } else {
        ::sth::sthCore::log debug "Successfully get msg result objects handles. resultObjectHandleArr:[array get resultObjectHandleArr]"
    }
    
    #set sessionReturnKeyType {linktrace loopback tst}
    set returnKeyType $msgType
    #foreach returnKeyType $sessionReturnKeyType {
        ::sth::Eoam::GetEoamInfo_session $returnKeyType resultObjectHandleArr returnKeyedList cmdState
        if {$cmdState} {
            ::sth::sthCore::log debug "Successfully get results info of $returnKeyType."
        } else {
            ::sth::sthCore::processError returnKeyedList "error geting results info of $returnKeyType."
            set cmdState $FAILURE
            return $returnKeyedList            
        }
    #}

    ::sth::Eoam::UnSubscribeEoamResultdataset

    set cmdState $SUCCESS
    return $returnKeyedList    
    
}

###/*! \ingroup eoamhelperprocfuncs
###\fn ProcessObjectsCreate_Msg ( str returnKeyedListVarName str cmdStatusVarName)
###\brief Process \em -mode switch with value \em create for emulation_oam_config_msg cmd
###
###This procedure execute the ProcessObjectsCreate_Msg command when the mode is create. It will create all the object of a Eoam msg session based on the \em -msg_type switch.
###
###\param[in] userInput This is the list of user configuration input excluding the step related switches.
###\param[in] cmdStatusVarName record the command excuting state -TRUE for success -FAILURE for fail.
###\return updatedKeyedList with eoam msg handles.
###
###author Yulin Chen (Ychen)
###*/
###
###ProcessObjectsCreate_Msg ( str returnKeyedListVarName str cmdStatusVarName);
###
proc ::sth::Eoam::ProcessObjectsCreate_Msg { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_msg"    
    set _hltCmdName "ProccessCreate_Msg"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "
    
    set msgType [set ${_hltSpaceCmdName}\_user_input_args_array(msg_type)]
    #handle array
	array set configedObjectHandleArr {
	    EoamPortConfig ""
	    EoamMegConfig ""
	    EoamRemoteMegEndPointConfig ""
	    Router ""
        IpIf ""
	    EthIIIf ""
	    VlanIf ""
	    VlanIf_Outer ""
	    EoamNodeConfig ""
	    EoamMaintenancePointConfig ""
	    EoamMaintenancePointConfig_MIP ""
	    EoamMaintenancePointConfig_MEP ""
	    EoamContChkCommandConfig ""
        EoamLoopbackCommandConfig ""
        EoamLinkTraceCommandConfig ""
		EoamDelayMeasurementCommandConfig ""
		EoamLossMeasurementCommandConfig ""
		EoamSlmCommandConfig ""
		EoamAisCommandConfig ""
		EoamLckCommandConfig ""
	}
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(sut_ip_address)]} {
        set ipAddr [set ${_hltSpaceCmdName}\_user_input_args_array(sut_ip_address)]
        if {[string first "." $ipAddr] > -1} {
            set ipIf "Ipv4If"
        } elseif {[string first ":" $ipAddr] > -1} {
            set ipIf "Ipv6If"
        } else {
            ::sth::sthCore::processError returnKeyedList "input sut_ip_address is not available ip address." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        }
    } else {
        set ipIf "Ipv4If"
    }
    
	
    #Create the MP router IF stack info.
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
        #There is S-Vlan and C-vlan
        set IfStack "$ipIf VlanIf VlanIf EthIIIf"
        set IfCount "1 1 1 1"
    } elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && ! [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
		# There is vlan
		set IfStack "$ipIf VlanIf EthIIIf"
		set IfCount "1 1 1 "
    } else {
		# There is no vlan
		set IfStack "$ipIf EthIIIf"
		set IfCount "1 1"
    }
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
		set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
		#EoamPortConfig
		lappend configedObjectHandleArr(EoamPortConfig) [::sth::sthCore::invoke stc::get $portHandle -Children-EoamPortConfig]
	}
	
	set enableMpOnly "false"
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(enable_mp_only)]} {
		set enableMpOnly [set ${_hltSpaceCmdName}\_user_input_args_array(enable_mp_only)]
	}
	
	if {[string equal $enableMpOnly "false"]} {
		#EoamMegConfig
		set megHandle [::sth::sthCore::invoke stc::create EoamMegConfig -under $::sth::GBLHNDMAP(project)]
		lappend configedObjectHandleArr(EoamMegConfig) $megHandle
		keylset returnKeyedList eoam_meg_config_handle $megHandle

		#EoamRemoteMegEndPointConfig -under EoamMegConfig
		if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_remote)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_remote_list)]} {
			set remoteMepHandle [::sth::sthCore::invoke stc::create EoamRemoteMegEndPointConfig -under $megHandle]
			lappend configedObjectHandleArr(EoamRemoteMegEndPointConfig) $remoteMepHandle
		}
	}
	
	set mepHandle ""
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
		set mepHandle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
	} else {
		#create eoam router
		if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
			set mepHandle $DeviceCreateOutput(-ReturnList)} errMsg]} {
			::sth::sthCore::processError returnKeyedList "Error ocured when creating Router under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
			set cmdState $FAILURE
			return $returnKeyedList                     
		}
	}
	lappend configedObjectHandleArr(Router) $mepHandle
	
	#get ipIf handle
	if {[catch {set ipIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-$ipIf]} errMsg]} {
				::sth::sthCore::processError returnKeyedList "Error ocured when gettting $ipIf from $mepHandle errMsg: $errMsg." {}
				set cmdState $FAILURE
				return $returnKeyedList             
	}
	lappend configedObjectHandleArr(IpIf) $ipIfHandle
	
	#get EthiiIf handle
	if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-EthIIIf]} errMsg]} {
				::sth::sthCore::processError returnKeyedList "Error ocured when gettting EthIIIf from $mepHandle errMsg: $errMsg." {}
				set cmdState $FAILURE
				return $returnKeyedList             
	}
	lappend configedObjectHandleArr(EthIIIf) $EthIIIfHandle
	
	#get vlanif handle
	if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-VlanIf]} errMsg]} {
		::sth::sthCore::processError returnKeyedList "Error ocured when gettting VlanIf from $mepHandle errMsg: $errMsg." {}
		set cmdState $FAILURE
		return $returnKeyedList                           
	}                    
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
		#There is S-Vlan and C-vlan
		lappend configedObjectHandleArr(VlanIf_Outer) [lindex $VlanIfHandle 1]
		lappend configedObjectHandleArr(VlanIf) [lindex $VlanIfHandle 0]
	} elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && ![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
		# There is vlan
		lappend configedObjectHandleArr(VlanIf) $VlanIfHandle
	}
	
	set eoamNodeHandle ""
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
		set eoamNodeHandle [::sth::sthCore::invoke stc::get $mepHandle -children-EoamNodeConfig]
	} else {
		#create EoamNodeconfig object
		set eoamNodeHandle [::sth::sthCore::invoke stc::create EoamNodeConfig -under $mepHandle]
	}
	lappend configedObjectHandleArr(EoamNodeConfig) $eoamNodeHandle
		
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {	
		set mepConfigHandle [::sth::sthCore::invoke stc::create EoamMaintenancePointConfig -under $eoamNodeHandle]
	} else {
		#config EoamMaintenancePointConfig object
		set mepConfigHandle [::sth::sthCore::invoke stc::get $eoamNodeHandle -Children-EoamMaintenancePointConfig]
	}
	keylset returnKeyedList eoam_mp_config_handle $mepConfigHandle
	
	if {[string equal $enableMpOnly "false"]} {
		#set EoamMepconfig MegAssociation to EoamMegConfig
		::sth::sthCore::invoke stc::config $mepConfigHandle "-MegAssociation-targets $megHandle"
	}
	lappend configedObjectHandleArr(EoamMaintenancePointConfig) $mepConfigHandle
	lappend configedObjectHandleArr(EoamMaintenancePointConfig_MEP) $mepConfigHandle
	
    #create EoamXXXCommandConfig object
	switch -exact $msgType {
            loopback {
				set loopbackCommandConfigHandle [::sth::sthCore::invoke stc::create EoamLoopbackCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamLoopbackCommandConfig) $loopbackCommandConfigHandle
            }
            linktrace {
				set linktraceCommandConfigHandle [::sth::sthCore::invoke stc::create EoamLinkTraceCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamLinkTraceCommandConfig) $linktraceCommandConfigHandle                
            }
			continuous_check {
				set EoamContChkCommandConfigHandle [::sth::sthCore::invoke stc::create EoamContChkCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamContChkCommandConfig) $EoamContChkCommandConfigHandle                
            }
            dm {
				set dmCommandConfigHandle [::sth::sthCore::invoke stc::create EoamDelayMeasurementCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamDelayMeasurementCommandConfig) $dmCommandConfigHandle
            }
            lm {
				set lmCommandConfigHandle [::sth::sthCore::invoke stc::create EoamLossMeasurementCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamLossMeasurementCommandConfig) $lmCommandConfigHandle
            }
            slm {
				set slmCommandConfigHandle [::sth::sthCore::invoke stc::create EoamSlmCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamSlmCommandConfig) $slmCommandConfigHandle
            }
            ais {
				set aisCommandConfigHandle [::sth::sthCore::invoke stc::create EoamAisCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamAisCommandConfig) $aisCommandConfigHandle
            }
            lck {
				set lckCommandConfigHandle [::sth::sthCore::invoke stc::create EoamLckCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]
                lappend configedObjectHandleArr(EoamLckCommandConfig) $lckCommandConfigHandle
            }
            test {
                #TODO finish
                if {[catch {set loopbackCommandConfigHandle [::sth::sthCore::invoke stc::create EoamLoopbackCommandConfig -under $configedObjectHandleArr(EoamMaintenancePointConfig)]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when create EoamLoopbackCommandConfig under $configedObjectHandleArr(EoamMaintenancePointConfig), errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
                lappend configedObjectHandleArr(EoamLoopbackCommandConfig) $loopbackCommandConfigHandle
            }
        }
        
    return [array get configedObjectHandleArr]
}

###/*! \ingroup eoamhelperprocfuncs
###\fn ProcessFrameConfig (str msgType str msgHandle str swithList)
###\brief Process config TLV frame pattern in Eoam Msgs.
###
###This procedure execute the ProcessFrameConfig command. It will config TLV setup in a Eoam Msg based on -msg_type.
###
###\param[in] msgType. This is the type of eoam msg.
###\param[in] msgHandle. This is the input eoam msg handle.
###\param[in] swithList. This is the input eoam msg TLV configure switches.
###\return command excuting state -TRUE for success -FAILURE for fail.
###
###author Yulin Chen (Ychen)
###*/
###
###ProcessFrameConfig (str msgType str msgHandle str swithList);
###
proc ::sth::Eoam::ProcessFrameConfig { msgType msgHandle swithList userInput} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_msg"    
    set _hltCmdName "ProcessFrameConfig"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "
    
    set msgHandle 
    set _msgFrame "<frame><config><pdus>\$pdu\\</pdus></config></frame>"
    set pdu ""
    
    set _SenderTLVLengthValue "0000"
    set _ChassisIDLengthValue "00"
    set _ChassisIDSubtypeValue "00"
    set _ChassisIDValue "00"
    
    set _OrgTLVLengthValue "0000"
    set _OUIValue "000000"
    
    set _SubTypeValue "00"
    set _ValueValue ""
    
    set _DataTLVLengthValue "0000"
    set _DataPatternValue ""
    
    #not support User TLV
    #set userTLV ""
    
    set _TestTLVLengthValue "0000"
    set _TestPatternTypeValue "1"
    
    set _EndTLV "<pdu name=\"EndTLV_1\" pdu=\"EOAMTLV:EndTLV\" />"
    
    set SenderTLV ""
    set SenderTLVFlag 0
    set OrgTLV ""
    set OrgTLVFlag 0
    set DataTLV ""
    set DataTLVFlag 0
    set TestTLV ""
    set TestTLVFlag 0
    
    #LtrOptionalTlvs
	set LtrTLV ""
    set LtrTLVFlag 0
	set _LtrTLVLengthValue "0000"
	set _LtrTLVTypeValue "08"
	
    #IntStat
	set IntTLV ""
    set IntTLVFlag 0
	set _IntTLVLengthValue "0000"
	set _IntTLVTypeValue "04"
	set _IntTLVValue "01"
	
	#LTMEgrID
	set LtmTLV ""
    set LtmTLVFlag 0
	set _LtmTLVLengthValue "0000"
	set _LtmTLVTypeValue "07"
	
    #PrtStat
	set PrtTLV ""
    set PrtTLVFlag 0
	set _PrtTLVLengthValue "0000"
	set _PrtTLVTypeValue "02"
	set _PrtTLVStatusValue "02"
	
	#RplyEgr
	set RplyEgrTLV ""
    set RplyEgrTLVFlag 0
	set _RplyEgrTLVLengthValue "0000"
	set _RplyEgrTLVTypeValue "06"
	set _RplyEgrTLVAction "01"
	set _RplyEgrTLVMacAddr "00:00:00:00:00:00"
	
	#RplyIng
	set RplyIngTLV ""
    set RplyIngTLVFlag 0
	set _RplyIngTLVLengthValue "0000"
	set _RplyIngTLVTypeValue "06"
	set _RplyIngTLVAction "01"
	set _RplyIngTLVMacAddr "00:00:00:00:00:00"

	#PbbTeMip
	set PbbTeMipTLV ""
    set PbbTeMipTLVFlag 0
	set _PbbTeMipTLVLengthValue "000E"
	set _PbbTeMipTLVTypeValue "09"
	set _PbbTeMipTLVMipMac "00:00:00:00:00:00"
	set _PbbTeMipTLVReverseMac "00:00:00:00:00:00"
	set _PbbTeMipTLVReverseVid "0"
	
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(tlv_type)]} {
		set swithList $userInput
	}
	
    ::sth::sthCore::log debug "$swithList"
    
    set _LtrTLVLengthValue    "0000"
    set _LtrTLVTypeValue      "08"
    set _LtrTLVLastIndexValue "0000"
    set _LtrTLVLastMacAddr    "00:00:00:00:00:00"
    set _LtrTLVNextIndexValue "0000"
    set _LtrTLVNextMacAddr    "00:00:00:00:00:00"
    
    foreach {switchName switchValue} $swithList {
        ::sth::sthCore::log debug "process frame config switchName:$switchName, switchValue:$switchValue"
        regsub -all "^-"  $switchName "" switchName
        if {[info exists ::sth::Eoam::emulation_oam_config_msg_$switchName\_fwdmap($switchValue)]} {
            set switchValue [set ::sth::Eoam::emulation_oam_config_msg_$switchName\_fwdmap($switchValue)]
        }
        if {[string first "tlv_sender_" $switchName] > -1} {
                switch -glob -- $switchName {
                    *chassis_id_length {
                        set _ChassisIDLengthValue [format "%02X" $switchValue]
                    }
					*length {
                        set _SenderTLVLengthValue [format "%04X" $switchValue]
                    }
                    *chassis_id {
                        set _ChassisIDValue [format "%02X" $switchValue]
                    }
                    *chassis_id_subtype {
                        set _ChassisIDSubtypeValue [format "%02X" $switchValue]
                    }
                }
                set SenderTLVFlag 1
        } elseif {[string first "tlv_org_" $switchName] > -1} {
                switch -glob -- $switchName {
                    *length {
                        set _OrgTLVLengthValue [format "%04X" $switchValue]
                    }
                    *oui {
                        set _OUIValue [format "%06X" $switchValue]
                    }
                    *subtype {
                        set _SubTypeValue [format "%02X" $switchValue]
                    }
                    *value {
                        if {[string match -nocase "0x*" $switchValue]} {
                            set switchValue [string range $switchValue 2 end]
                        }
                        set _ValueValue $switchValue
                    }
                }
                set OrgTLVFlag 1
        } elseif {[string first "tlv_data_" $switchName] > -1} {
                switch -glob -- $switchName {
                    *length {
                        set _DataTLVLengthValue [format "%04X" $switchValue]
                    }
                    *pattern {
                        if {[string match -nocase "0x*" $switchValue]} {
                            set switchValue [string range $switchValue 2 end]
                        }
                        set _DataPatternValue $switchValue
                    }
                }
                set DataTLVFlag 1
        } elseif {[string first "tlv_user_" $switchName] > -1} {
            #TODO finish (not support now)
        } elseif {[string first "tlv_test_" $switchName] > -1} {
                switch -glob -- $switchName {
                    *length {
                        set  _TestTLVLengthValue [format "%04X" $switchValue]
                    }
                    *pattern {
                        set _TestPatternTypeValue $switchValue
                    }
                }
                set TestTLVFlag 1
        } elseif {[string first "tlv_ltr_egress_id_" $switchName] > -1} {           
			switch -glob -- $switchName {
				*length {
					set _LtrTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _LtrTLVTypeValue $switchValue
				}
				*last_index {
					set _LtrTLVLastIndexValue $switchValue
				}
				*last_mac_addr {
					set _LtrTLVLastMacAddr $switchValue
				}
				*next_index {
					set _LtrTLVNextIndexValue $switchValue
				}
				*next_mac_addr {
					set _LtrTLVNextMacAddr $switchValue
				}
			}
			set LtrTLVFlag 1
        } elseif {[string first "tlv_int_status_" $switchName] > -1} {
			switch -glob -- $switchName {
				*length {
					set _IntTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _IntTLVTypeValue $switchValue
				}
				*value {
					set _IntTLVValue $switchValue
				}
			}
			set IntTLVFlag 1
        } elseif {[string first "tlv_ltm_id_" $switchName] > -1} {
			switch -glob -- $switchName {
				*length {
					set _LtmTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _LtmTLVTypeValue $switchValue
				}
			}
			set LtmTLVFlag 1
        } elseif {[string first "tlv_port_status_" $switchName] > -1} {
			switch -glob -- $switchName {
				*length {
					set _PrtTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _PrtTLVTypeValue $switchValue
				}
				*value {
					set _PrtTLVValue $switchValue
				}
			}
			set PrtTLVFlag 1
        } elseif {[string first "tlv_reply_egress_" $switchName] > -1} {
			switch -glob -- $switchName {
				*length {
					set _RplyEgrTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _RplyEgrTLVTypeValue $switchValue
				}
				*action {
					set _RplyEgrTLVActionValue $switchValue
				}
				*mac_addr {
					set _RplyEgrTLVMacAddr $switchValue
				}
			}
			set RplyEgrTLVFlag 1
        } elseif {[string first "tlv_reply_ingress_" $switchName] > -1} {
			switch -glob -- $switchName {
				*length {
					set _RplyIngTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _RplyIngTLVTypeValue $switchValue
				}
				*action {
					set _RplyIngTLVActionValue $switchValue
				}
				*mac_addr {
					set _RplyIngTLVMacAddr $switchValue
				}
			}
			set RplyIngTLVFlag 1
        } elseif {[string first "tlv_pbb_te_mip_" $switchName] > -1} {
			switch -glob -- $switchName {
				*length {
					set _PbbTeMipTLVLengthValue [format "%04X" $switchValue]
				}
				*type {
					set _PbbTeMipTLVTypeValue $switchValue
				}
				*mip_mac {
					set _PbbTeMipTLVMipMac $switchValue
				}
				*reverse_mac {
					set _PbbTeMipTLVReverseMac $switchValue
				}
				*reverse_vid {
					set _PbbTeMipTLVReverseVid $switchValue
				}
			}
			set PbbTeMipTLVFlag 1
		}
    }


    if { $SenderTLVFlag } {
        set sender_TLV "<pdu name=\"SndrID_1\" pdu=\"EOAMTLV:SndrID\">  <Length>$_SenderTLVLengthValue\</Length> <ChassisIDLen>$_ChassisIDLengthValue\</ChassisIDLen> <theChassisID>  <ChassisIDList name=\"ChassisIDList_0\">  <Custom>  <ChassisIDSubtype>$_ChassisIDSubtypeValue\</ChassisIDSubtype>  <ChassisID>$_ChassisIDValue\</ChassisID> </Custom>  </ChassisIDList></theChassisID> </pdu>  "        
    }
    if { $OrgTLVFlag } {
        set org_TLV "<pdu name=\"OrgSpec_1\" pdu=\"EOAMTLV:OrgSpec\">  <Length>$_OrgTLVLengthValue\</Length> <OUI>$_OUIValue\</OUI> <SubType>$_SubTypeValue\</SubType> <theValue>  <Value name=\"Value_0\"> <Value>$_ValueValue\</Value> </Value></theValue> </pdu>"
	}
    if { $DataTLVFlag } {
        set data_TLV "<pdu name=\"DataTLV_1\" pdu=\"EOAMTLV:DataTLV\">  <Length>$_DataTLVLengthValue\</Length> <theData>  <Data name=\"Data_0\">  <Data> $_DataPatternValue </Data>  </Data></theData> </pdu>"
	}
    if { $TestTLVFlag } {
        set test_TLV "<pdu name=\"TestTLV_1\" pdu=\"EOAMTLV:TestTLV\"> <Length>$_TestTLVLengthValue\</Length> <PatternType>$_TestPatternTypeValue\</PatternType> </pdu>  "
	}
    if { $LtrTLVFlag } {
        set ltr_egress_id_TLV "<pdu name=\"LtrTLV_1\" pdu=\"EOAMTLV:LTREgrID\"> <Length>$_LtrTLVLengthValue\</Length> <Type>$_LtrTLVTypeValue\</Type> <LastEgressIdent> <Index>$_LtrTLVLastIndexValue\</Index> <MacAddr>$_LtrTLVLastMacAddr\</MacAddr> </LastEgressIdent> <NextEgressIdent> <Index>$_LtrTLVNextIndexValue\</Index> <MacAddr>$_LtrTLVNextMacAddr\</MacAddr> </NextEgressIdent></pdu>  "
	}
    if { $IntTLVFlag } {
        set int_status_TLV "<pdu name=\"IntTLV_1\" pdu=\"EOAMTLV:IntStat\"> <Length>$_IntTLVLengthValue\</Length> <Type>$_IntTLVTypeValue\</Type> <IntStatusValues>$_IntTLVValue\</IntStatusValues> </pdu>  "
	}
    if { $LtmTLVFlag } {
        set ltm_id_TLV "<pdu name=\"LtmEgrTLV_1\" pdu=\"EOAMTLV:LTMEgrID\"> <Length>$_LtmTLVLengthValue\</Length> <Type>$_LtmTLVTypeValue\</Type> </pdu>  "
	}
    if { $PrtTLVFlag } {
        set port_status_TLV "<pdu name=\"PrtTLV_1\" pdu=\"EOAMTLV:PrtStat\"> <Length>$_PrtTLVLengthValue\</Length> <Type>$_PrtTLVTypeValue\</Type> <PortStatusValues>$_PrtTLVValue\</PortStatusValues> </pdu>  "
	}
    if { $RplyEgrTLVFlag } {
        set reply_egress_TLV "<pdu name=\"RplyEgrTLV_1\" pdu=\"EOAMTLV:RplyEgr\"> <Length>$_RplyEgrTLVLengthValue\</Length> <Type>$_RplyEgrTLVTypeValue\</Type> <EgressAction>$_RplyEgrTLVActionValue\</EgressAction> <EgressMac>$_RplyEgrTLVMacAddr\</EgressMac> </pdu>  "
	}
    if { $RplyIngTLVFlag } {
        set reply_ingress_TLV "<pdu name=\"RplyIngTLV_1\" pdu=\"EOAMTLV:RplyIng\"> <Length>$_RplyIngTLVLengthValue\</Length> <Type>$_RplyIngTLVTypeValue\</Type> <IngressAction>$_RplyIngTLVActionValue\</IngressAction> <IngressMac>$_RplyIngTLVMacAddr\</IngressMac> </pdu>  "
	}

    if { $PbbTeMipTLVFlag } {
        set pbb_te_mip_TLV "<pdu name=\"PbbTeMip_1\" pdu=\"EOAMTLV:PbbTeMip\">  <Length>$_PbbTeMipTLVLengthValue\</Length> <Type>$_PbbTeMipTLVTypeValue\</Type> <MipMac>$_PbbTeMipTLVMipMac\</MipMac> <ReverseMac>$_PbbTeMipTLVReverseMac\</ReverseMac> <ReverseVid>$_PbbTeMipTLVReverseVid\</ReverseVid> </pdu>  "        
    }


    set tlv_order_list "sender org data test ltr_egress_id int_status ltm_id port_status reply_egress reply_ingress pbb_te_mip"
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(tlv_order_list)]} {
        set tlv_order_list [set ${_hltSpaceCmdName}\_user_input_args_array(tlv_order_list)]
    }
    
    foreach tlv_order $tlv_order_list {
		if {[info exists $tlv_order\_TLV]} {
    		append pdu [set $tlv_order\_TLV]
		}
    }
    
	append pdu $_EndTLV
	set cmd "set FrameConfigValue \"$_msgFrame\""
	eval $cmd
	::sth::sthCore::log debug "FrameConfigValue:$FrameConfigValue"
	

	set attrName ""
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(tlv_type)]} {
		set tlvType [set ${_hltSpaceCmdName}\_user_input_args_array(tlv_type)]
		switch -exact $tlvType {
			cc {
				set attrName "CcOptionalTlvs"
			}
			ltr {
				set attrName "LtrOptionalTlvs"
			}
			lbm {
				set attrName "LbmOptionalTlvs"
			}
			ltm {
				set attrName "LtmOptionalTlvs"
			}
			dmm {
				set attrName "DmmOptionalTlvs"
			}
			dmr {
				set attrName "DmrOptionalTlvs"
			}
			lbr {
				set attrName "LbrOptionalTlvs"
			}
			lmm {
				set attrName "LmmOptionalTlvs"
			}
			lmr {
				set attrName "LmrOptionalTlvs"
			}
			slm {
				set attrName "SlmOptionalTlvs"
			}
			slr {
				set attrName "SlrOptionalTlvs"
			}
		}
	} else {
		switch -exact $msgType {
			loopback {
				set attrName "LbmOptionalTlvs"
			}
			linktrace {
				set attrName "LtmOptionalTlvs"
			}
			test {
				set attrName "LbmOptionalTlvs"
					#TODO finish
			}
		}
	}
	
    if {$attrName != ""} {
        ::sth::sthCore::invoke stc::config $msgHandle "-$attrName \{$FrameConfigValue\}"
    }
    
    return $SUCCESS
}

###/*! \ingroup eoamhelperprocfuncs
###\fn IsMsgHandleValid ( str msgHandle )
###\brief Process check the input eoam msg handle is available.
###
###This procedure execute the IsMsgHandleValid command. It will check the input eoam msg handle is available based on \em -mode vlaue modify and reset.
###
###\param[in] msgHandle. This is the input eoam msg handle.
###\return msg handle checking results: -TRUE for available -FAILURE for unavailable.
###*/author Yulin Chen (Ychen)
###
###IsMsgHandleValid (str msgHandle );
###
proc ::sth::Eoam::IsMsgHandleValid { msgHandle } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set flag 1
    if {[catch {set routerHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Router]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured while get -Children-Router from $::sth::GBLHNDMAP(project), errMsg: $errMsg."
        return $FAILURE
    }
    foreach routerHandle $routerHandleList {
        if {[catch {set EoamNodeHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-EoamNodeConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while get -Children-EoamNodeConfig from $routerHandle, errMsg: $errMsg."
            return $FAILURE            
        }
        if {$EoamNodeHandle != ""} {
            if {[catch {set MepHandle [::sth::sthCore::invoke stc::get $EoamNodeHandle -Children-EoamMaintenancePointConfig]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while get -Children-EoamMaintenancePointConfig from $EoamNodeHandle, errMsg: $errMsg."
                return $FAILURE                 
            }
            if {[regexp -nocase $msgHandle $MepHandle]} {
                return $SUCCESS
            }
        }
    }
    return $FAILURE
}

###/*! \ingroup eoamhelperfunc
###\fn ProcessSwitchConfig (str args)
###\brief Process \em -mode switch with value \em start for emulation_oam_control_reset cmd
###
###This procedure executes the emulation_oam_control command when the mode is reset. It will stop eoam session based on the handle switch value, and then clear all the result stats to 0.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/author Yulin Chen (Ychen)
###
###emulation_oam_control_reset (str args);
###
proc ::sth::Eoam::ProcessSwitchConfig { returnKeyedListVarName cmdStatusVarName ObjectHandleArr } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "ProcessSwitchConfig"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    upvar 1 $ObjectHandleArr  configedObjectHandleArr
    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "    
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_local_incr_mode)]} {
        set macLocalIncrMode [set ${_hltSpaceCmdName}\_user_input_args_array(mac_local_incr_mode)]
        if {$macLocalIncrMode == "list"} {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_local)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(mac_local) [lindex [set ${_hltSpaceCmdName}\_user_input_args_array(mac_local_list)] 0]
            }
        }
    }
    
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_id_incr_mode)]} {
        set MepIdIncrMode [set ${_hltSpaceCmdName}\_user_input_args_array(mep_id_incr_mode)]
        if {$MepIdIncrMode == "list"} {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_id)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(mep_id) [lindex [set ${_hltSpaceCmdName}\_user_input_args_array(mep_id_list)] 0]
            }
        }
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_remote_incr_mode)]} {
        set macRemoteIncrMode [set ${_hltSpaceCmdName}\_user_input_args_array(mac_remote_incr_mode)]
        if {$macRemoteIncrMode == "list"} {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_remote)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(mac_remote) [lindex [set ${_hltSpaceCmdName}\_user_input_args_array(mac_remote_list)] 0]
            }
        }
    }
    
    set userInputList [array get ${_hltSpaceCmdName}\_user_input_args_array]
    #set configObjectList
    foreach {switchName switchValue} $userInputList {
        ::sth::sthCore::log debug "Process switch:$switchName value:$switchValue config"
            
        if { $switchName == "optional_args" } {
            continue
        }
        
        if { $switchName == "mandatory_args" } {
            continue
        }
        
        if {$switchName == "continuity_check_ucast_mac_dst"} {
            set stcObjName "EoamContChkCommandConfig"
            set stcAttrName "EnableMulticastTarget"
            set configArgs " -$stcAttrName FALSE"
            
            
            set switchValue [join [split $switchValue ":"] "-"]
            set stcAttrName "UnicastTargetList"
            append configArgs " -$stcAttrName $switchValue"
            
            foreach configHandle $configedObjectHandleArr($stcObjName) {
                if {[catch {::sth::sthCore::invoke stc::config $configHandle $configArgs} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle $configArgs\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                    
                }
            }
        } elseif {$switchName == "continuity_check_mcast_mac_dst" } {
            set stcObjName "EoamContChkCommandConfig"
            set stcAttrName "EnableMulticastTarget"
	    
            if {$switchValue} {
                set configArgs " -$stcAttrName TRUE"
            } else {
                set configArgs " -$stcAttrName FALSE"
            }
            
            foreach configHandle $configedObjectHandleArr($stcObjName) {
                if {[catch {::sth::sthCore::invoke stc::config $configHandle $configArgs} errMsg]} {
                     ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle $configArgs\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                      
                }
            }
    
        } elseif {$switchName == "mac_local" } {
	    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
	    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            
            foreach configHandle $configedObjectHandleArr($stcObjName) {
                set switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(mac_local)]
                
                set configArgs " -$stcAttrName $switchValue"
                if {[catch {::sth::sthCore::invoke stc::config $configHandle $configArgs} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle $configArgs\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                       
                }
                
                set ${_hltSpaceCmdName}\_user_input_args_array(mac_local) [::sth::Eoam::StepMacLocalAddress $_hltSpaceCmdName]
            }
        } elseif {$switchName == "mac_remote"} {
            set stcObjName "EoamRemoteMegEndPointConfig"
            set stcAttrName "RemoteMacAddr"
            
            set switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(mac_remote)]
            set configArgs " -$stcAttrName $switchValue"
            set configHandle [lindex $configedObjectHandleArr($stcObjName) 0]
            
            if {[catch {::sth::sthCore::invoke stc::config $configHandle $configArgs} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle $configArgs\". errMsg: $errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList                   
            }
            set ${_hltSpaceCmdName}\_user_input_args_array(mac_remote) [::sth::Eoam::StepMacRemoteAddress $_hltSpaceCmdName]
            
            set configHandleList [lrange $configedObjectHandleArr($stcObjName) 1 end]
            #add local mep mac to remote mep in meg
            foreach localMepHandle $configedObjectHandleArr(EoamMaintenancePointConfig_MEP) configHandle $configHandleList {
                if {[catch {set eoamNodeHandle [::sth::sthCore::invoke stc::get $localMepHandle -Parent]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $localMepHandle -SourceMac\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
                if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $eoamNodeHandle -Parent]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $eoamNodeHandle -SourceMac\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                      
                }
                if {[catch {set LocalMepMacValue [::sth::sthCore::invoke stc::get $routerHandle.EthIIIf -SourceMac]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $routerHandle.EthIIIf -SourceMac\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
                if {[catch {::sth::sthCore::invoke stc::config $configHandle "-$stcAttrName $LocalMepMacValue"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle \"-$stcAttrName $LocalMepMacValue\"\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
            }
        } elseif {$switchName == "mep_id"} {
	    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
	    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            
            foreach configHandle $configedObjectHandleArr($stcObjName) {
                set switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(mep_id)]
                set configArgs " -$stcAttrName $switchValue"
                
                if {[catch {::sth::sthCore::invoke stc::config $configHandle $configArgs} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle $configArgs\". errMsg: $errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList                       
                }
                set ${_hltSpaceCmdName}\_user_input_args_array(mep_id) [::sth::Eoam::StepMepId $_hltSpaceCmdName]
            }
        } else {
            set switchProcFunc [::sth::sthCore::getModeFunc2 $_hltNameSpace $_OrigHltCmdName $switchName $modeValue]
            if {[string equal $switchProcFunc "ProcessConfigCmd"]} {
                set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
                set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
                if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
                    set configArgs " -$stcAttrName $attrValue"
                } else {
                    set configArgs " -$stcAttrName $switchValue"
                }
                foreach configHandle $configedObjectHandleArr($stcObjName) {
                    if {[catch {::sth::sthCore::invoke stc::config $configHandle $configArgs} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::ConfigNew $configHandle $configArgs\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $returnKeyedList                           
                    }
                }                 
            } elseif {[string equal $switchProcFunc "ProcessMEGNameConfig"]} {
                if {![::sth::Eoam::ProcessMEGNameConfig returnKeyedList cmdState $switchName $configedObjectHandleArr(EoamMegConfig)]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"::sth::Eoam::ProcessMEGNameConfig returnKeyedList cmdState $switchName $configedObjectHandleArr(EoamMegConfig)\"." 
                        set cmdState $FAILURE
                        return $returnKeyedList                    
                }
            } else {
                #TODO finish
            }
        }
        #end of if elseif else
    }
    #end of foreach

    return $returnKeyedList
}

proc ::sth::Eoam::CreateRandomMAC { } {
    while {1} {
        set randMAC ""
        for {set i 0} {$i < 6} {incr i} {
            lappend randMAC [format "%X" [expr { int(255 * rand()) }]]
        }
        set randMAC [join $randMAC :]
        #check if the new random MAC has been used
        set UsedFlag 0
        foreach Mac $::sth::Eoam::usedMACList {
            if {$randMAC == $Mac} {
                set UsedFlag 1
                break
            }
        }
        if { $UsedFlag } {
            break
        } else {
            continue
        }
    }
    return $randMac
}

proc ::sth::Eoam::ProcessObjectsCreate_Topology { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "ProcessObjectsCreate_Topology"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "

    #create the handle instances for all configure
    set configedObjectTypes {Port Meg Mp}
    
    array set configedObjectHandleArr {
        EoamPortConfig ""
        EoamMegConfig ""
        EoamRemoteMegEndPointConfig ""
        Router ""
        IpIf ""
        EthIIIf ""
        VlanIf ""
        VlanIf_Outer ""
        EoamNodeConfig ""
        EoamMaintenancePointConfig ""
        EoamMaintenancePointConfig_MIP ""
        EoamMaintenancePointConfig_MEP ""
        EoamContChkCommandConfig ""
    }
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(sut_ip_address)]} {
        set ipAddr [set ${_hltSpaceCmdName}\_user_input_args_array(sut_ip_address)]
        if {[string first ":" $ipAddr] >-1} {
            set ipIf "Ipv6If"
        } else {
            set ipIf "Ipv4If"
        }
    } else {
        set ipIf "Ipv4If"
    }

    #Create the MP router Interface stack info.
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
        #There is S-Vlan and C-vlan
        set IfStack "$ipIf VlanIf VlanIf EthIIIf"
        set IfCount "1 1 1 1"
    } elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && ![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
	# There is vlan
	set IfStack "$ipIf VlanIf EthIIIf"
	set IfCount "1 1 1"
    } else {
	# There is no vlan
	set IfStack "$ipIf EthIIIf"
	set IfCount "1 1"
    }
    
    set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
    #object create and handle fetch

        lappend configedObjectHandleArr(EoamPortConfig) [::sth::sthCore::invoke stc::get $portHandle -Children-EoamPortConfig]
        
        
        #Meg level configure handles create
        
        set megHandle [::sth::Eoam::GetMegObjectHandle returnKeyedList cmdState]
        if {!$cmdState} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamMegConfig: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
            lappend configedObjectHandleArr(EoamMegConfig) $megHandle

        #EoamRemoteMegEndPointConfig -under EoamMegConfig
        #mac_local    
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_count)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(mep_count) 1
            }
            set mepCount [set ${_hltSpaceCmdName}\_user_input_args_array(mep_count)]
            for {set i 0} {$i < $mepCount} {incr i} {                
                if {[catch {set remoteMepHandle [::sth::sthCore::invoke stc::create EoamRemoteMegEndPointConfig -under $megHandle]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamRemoteMegEndPointConfig under $megHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                 
                }
                lappend configedObjectHandleArr(EoamRemoteMegEndPointConfig) $remoteMepHandle                                
            }
        #mac_remote
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_remote)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_remote_list)]} {
            if {[catch {set remoteMepHandle [::sth::sthCore::invoke stc::create EoamRemoteMegEndPointConfig -under $megHandle]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamRemoteMegEndPointConfig under $megHandle errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList                 
            }
            lappend configedObjectHandleArr(EoamRemoteMegEndPointConfig) $remoteMepHandle
        }
        
        #Mp Level configure handles create
            #mip entities' handles create
############Define the number of simulated MIPs for the level, connected in series.
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(mip_count)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(mip_count) 1
            }
            set mipCount [set ${_hltSpaceCmdName}\_user_input_args_array(mip_count)]
            set LastMIPHandle ""
            for {set i 0} {$i < $mipCount} {incr i} {
                #the first mip is directly connected to port
                if {$i == 0} {
                    #create eoam router
                    if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set mipHandle $DeviceCreateOutput(-ReturnList)} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error ocured when creating MIP Router under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList                         
                    }
                } else {
                    #new created mep (router) is Affiliated with the last created one (they are connected in series)
                    #create eoam router
                    if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set mipHandle $DeviceCreateOutput(-ReturnList)} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error ocured when creating MIP Router under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList                         
                    }
                    if {[catch {::sth::sthCore::invoke stc::config $mipHandle "-AffiliatedRouter-targets $LastMIPHandle"} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error ocured when config MIP Router $mipHandle -AffiliatedRouter-targets $LastMIPHandle errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList                          
                    }
                }
                lappend configedObjectHandleArr(Router) $mipHandle
                set LastMIPHandle $mipHandle
                
                #get Ip If handle
                if {[catch {set IpIfHandle [::sth::sthCore::invoke stc::get $mipHandle -Children-Ipv4If]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when gettting Ipv4If from $mipHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                           
                }
                if {$IpIfHandle == ""} {
                    if {[catch {set IpIfHandle [::sth::sthCore::invoke stc::get $mipHandle -Children-Ipv6If]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error ocured when gettting Ipv6If from $mipHandle errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList                           
                    }                    
                }
                lappend configedObjectHandleArr(IpIf) $IpIfHandle
                
                #get vlanif handle
                if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $mipHandle -Children-VlanIf]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when gettting VlanIf from $mipHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                           
                }                    
                if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
                    #There is S-Vlan and C-vlan
                    lappend configedObjectHandleArr(VlanIf_Outer) [lindex $VlanIfHandle 1]
                    lappend configedObjectHandleArr(VlanIf) [lindex $VlanIfHandle 0]
                } elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && ![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
                    # There is vlan
                    lappend configedObjectHandleArr(VlanIf) $VlanIfHandle
                }
                
                #get EthiiIf handle
                if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $mipHandle -Children-EthIIIf]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting EthIIIf from $mipHandle errMsg: $errMsg." {}
                            set cmdState $FAILURE
                            return $returnKeyedList             
                }
                lappend configedObjectHandleArr(EthIIIf) $EthIIIfHandle
                    
                #create EoamNodeconfig object
                if {[catch {set eoamNodeHandle [::sth::sthCore::invoke stc::create EoamNodeConfig -under $mipHandle]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamNodeConfig under $mipHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                           
                }
                lappend configedObjectHandleArr(EoamNodeConfig) $eoamNodeHandle
                    
                #config EoamMaintenancePointConfig object
                if {[catch {set mipConfigHandle [::sth::sthCore::invoke stc::get $eoamNodeHandle -Children-EoamMaintenancePointConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when geting EoamMaintenancePointConfig under $eoamNodeHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
                
                if {[catch {::sth::sthCore::invoke stc::config $mipConfigHandle "-MegAssociation-targets $megHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when config EoamMaintenancePointConfig \"-MegAssociation-targets $megHandle\" errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                         
                }
                lappend configedObjectHandleArr(EoamMaintenancePointConfig) $mipConfigHandle
                lappend configedObjectHandleArr(EoamMaintenancePointConfig_MIP) $mipConfigHandle        
            #end of for
            }
            
            #mep entities' handles create
############The simulated MEPs are all connected to the last simulated MIP.
############If zero MIPs are defined, the MEP is connected directly to the TGN
############port. Therefore, only one MEP per subinterface (device instance)
############may be defined.
            if {$mipCount == 0} {
                set ${_hltSpaceCmdName}\_user_input_args_array(mep_count) 1
            } else {
                if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_count)]} {
                    set ${_hltSpaceCmdName}\_user_input_args_array(mep_count) 1
                }                
            }
            set mepCount [set ${_hltSpaceCmdName}\_user_input_args_array(mep_count)]
            
            for {set i 0} {$i < $mepCount} {incr i} {
                #All MEPs are connected to the last created MIP
                #create eoam router
                if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $portHandle]
                            set mepHandle $DeviceCreateOutput(-ReturnList)} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when creating Router under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
		if {$mipCount > 0} {
		    if {[catch {::sth::sthCore::invoke stc::config $mepHandle "-AffiliatedRouter-targets $LastMIPHandle"} errMsg]} {
			::sth::sthCore::processError returnKeyedList "Error ocured when config MEP Router $mepHandle -AffiliatedRouter-targets $LastMIPHandle errMsg: $errMsg." {}
			set cmdState $FAILURE
			return $returnKeyedList                     
		    }		    
		}
                lappend configedObjectHandleArr(Router) $mepHandle
                
                #get Ip If handle
                if {[catch {set IpIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-Ipv4If]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when gettting Ipv4If from $mepHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                           
                }
                if {$IpIfHandle == ""} {
                    if {[catch {set IpIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-Ipv6If]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error ocured when gettting Ipv6If from $mepHandle errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList                           
                    }                    
                }
                lappend configedObjectHandleArr(IpIf) $IpIfHandle
                
                #get vlanif handle
                if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-VlanIf]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when gettting VlanIf from $mepHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                           
                }                    
                if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
                    #There is S-Vlan and C-vlan
                    lappend configedObjectHandleArr(VlanIf_Outer) [lindex $VlanIfHandle 1]
                    lappend configedObjectHandleArr(VlanIf) [lindex $VlanIfHandle 0]
                } elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)] && ![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_outer_id)]} {
                    # There is vlan
                    lappend configedObjectHandleArr(VlanIf) $VlanIfHandle
                }
                
                #get EthiiIf handle
                if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-EthIIIf]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Error ocured when gettting EthIIIf from $mepHandle errMsg: $errMsg." {}
                            set cmdState $FAILURE
                            return $returnKeyedList             
                }
                lappend configedObjectHandleArr(EthIIIf) $EthIIIfHandle
                
                #create EoamNodeconfig object
                if {[catch {set eoamNodeHandle [::sth::sthCore::invoke stc::create EoamNodeConfig -under $mepHandle]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamNodeConfig under $mepHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                           
                }
                lappend configedObjectHandleArr(EoamNodeConfig) $eoamNodeHandle
                
                #create EoamMaintenancePointConfig object
                if {[catch {set mepConfigHandle [::sth::sthCore::invoke stc::get $eoamNodeHandle -Children-EoamMaintenancePointConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when geting EoamMaintenancePointConfig under $eoamNodeHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
                
                if {[catch {::sth::sthCore::invoke stc::config $mepConfigHandle "-MegAssociation-targets $megHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when config EoamMaintenancePointConfig \"-MegAssociation-targets $megHandle\" errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                         
                }
                lappend configedObjectHandleArr(EoamMaintenancePointConfig) $mepConfigHandle
                lappend configedObjectHandleArr(EoamMaintenancePointConfig_MEP) $mepConfigHandle
                
                #create EoamContChkCommandConfig object
                if {[catch {set CCMComConfigHandle [::sth::sthCore::invoke stc::create EoamContChkCommandConfig -under $mepConfigHandle]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamContChkCommandConfig under $mepConfigHandle errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList                         
                }
                lappend configedObjectHandleArr(EoamContChkCommandConfig) $CCMComConfigHandle
            #end of for    
            }
        #end of if

    #multi level MPs spanning acrcoss
    #if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(domain_level)]} {
    #    set domainLevelList [set ${_hltSpaceCmdName}\_user_input_args_array(domain_level)]
    #    foreach LevelValue $domainLevelList {
    #        
    #    }
    #}
    
    
    set cmdState $SUCCESS
    return [array get configedObjectHandleArr]     
}

proc ::sth::Eoam::ProcessMEGNameConfig { returnKeyedListVarName cmdStatusVarName switchName MEGHandle} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "ProcessMEGNameConfig"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $switchName $MEGHandle"

    set oamStandard [set ${_hltSpaceCmdName}\_user_input_args_array(oam_standard)]
    
    #oam standard itu
    if {$oamStandard == "itut_y1731" } {
        if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_name_format)]} {
            set ${_hltSpaceCmdName}\_user_input_args_array(md_name_format) "icc_based"
        }
        
        set mdNameFormat [set ${_hltSpaceCmdName}\_user_input_args_array(md_name_format)]
        
        if {$mdNameFormat == "icc_based" } {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_name)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(md_name) "DEFAULT"
            }
            set MDName [set ${_hltSpaceCmdName}\_user_input_args_array(md_name)]
            if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-MegId_IccString $MDName"} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-MegId_IccString $MDName\". errMsg: $errMsg" {}
                set cmdState $FAILURE
                return $cmdState
            }
            set cmdState $SUCCESS
            return $cmdState
        } else {
            ::sth::sthCore::processError returnKeyedList "md_name_format should be icc_based when oam_standard is itut_y1731." {}
            set cmdState $FAILURE
            return $cmdState            
        }
        
    } elseif {$oamStandard != "ieee_802.1ag" } {
    #oam standard wrong
        ::sth::sthCore::processError returnKeyedList "Wrong switch value of oam_standard." {}
        set cmdState $FAILURE
        return $cmdState    
    }
    
    #oam standard ieee
    switch -glob -- $switchName {
        md* {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_name_format)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(md_name_format) char_str
            } 
            set MDNameType [set ${_hltSpaceCmdName}\_user_input_args_array(md_name_format)]
            
            set stcMdNameType [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName md_name_format $MDNameType]
            if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-DomainIdType $stcMdNameType"} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-DomainIdType $stcMdNameType\". errMsg: $errMsg" {}
                set cmdState $FAILURE
                return $cmdState                  
            }
            
            switch -exact $MDNameType {
                mac_addr {
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_mac)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(md_mac) 00:00:00:00:00:01
                    }
                    set MDName [set ${_hltSpaceCmdName}\_user_input_args_array(md_mac)]
                    set MDName [join [split $MDName :] -]
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_integer)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(md_integer) 0
                    }
                    append MDName ":"
                    append MDName [format "%04x" [set ${_hltSpaceCmdName}\_user_input_args_array(md_integer)]]
                    set MDName [join $MDName :]
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-DomainId_Mac_2Octets $MDName"} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-DomainId_Mac_2Octets $MDName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                        
                    }                   
                }
                domain_name {
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_name)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(md_name) "Domain1.com"
                    }
                    set MDName [set ${_hltSpaceCmdName}\_user_input_args_array(md_name)]
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-DomainId_DnsLike $MDName"} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-DomainId_DnsLike $MDName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                         
                    }
                }
                char_str {
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(md_name)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(md_name) "DEFAULT"
                    }
                    set MDName [set ${_hltSpaceCmdName}\_user_input_args_array(md_name)]
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-DomainId_string $MDName"} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-DomainId_string $MDName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                         
                    }
                }
                none {
                    #not to config MD ID
                    
                }
                default {
                    #error
                    ::sth::sthCore::processError returnKeyedList "Wrong switch value of -md_name_format" {}
                    set cmdState $FAILURE
                    return $cmdState                      
                }
            }
        }
        short_ma* {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_format)]} {
                set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_format) integer
            }
            set MANameType [set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_format)]
            
            set stcMANameType [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName short_ma_name_format $MANameType]
            if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-MegIdType $stcMANameType"} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-DomainIdType $stcMANameType\". errMsg: $errMsg" {}
                set cmdState $FAILURE
                return $cmdState                  
            }
            
            switch -exact $MANameType {
                primary_vid {
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value) 1
                    }
                    
                    set MAName [set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-MegId_PrimaryVid $MAName"} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-MegId_PrimaryVid $MAName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                     
                    }                  
                }
                char_str {
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value) "DEFAULT"
                    }
                    set MAName [set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]
                    
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-MegId_string $MAName"} errMsg]} {
                       ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-MegId_string $MAName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                     
                    }                
                }
                integer {
                    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]} {
                        set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value) 1
                    }
                    set MAName [set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]
                    set MAName [format "%04X" $MAName]
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-MegId_2Octets $MAName"} errMsg]} {
                       ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-MegId_2Octets $MAName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                     
                    }                  
                }
                rfc_2685_vpn_id {
                    if { ![info exists ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)] } {
                        set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value) 00-00-01:00-00-00-01
                    }
                    set MAName [set ${_hltSpaceCmdName}\_user_input_args_array(short_ma_name_value)]
                    if {[catch {::sth::sthCore::invoke stc::config $MEGHandle "-MegId_VpnId $MAName"} errMsg]} {
                       ::sth::sthCore::processError returnKeyedList "Error occured when config $MEGHandle \"-MegId_VpnId $MAName\". errMsg: $errMsg" {}
                        set cmdState $FAILURE
                        return $cmdState                     
                    }                 
                }
                none {
                    #not to config MD ID
                }
                default {
                    #error
                    ::sth::sthCore::processError returnKeyedList "Wrong switch value of -short_md_name_format" {}
                    set cmdState $FAILURE
                    return $cmdState                 
                }
            }
        }
    }
    
    set cmdState $SUCCESS
    return $cmdState
}


proc ::sth::Eoam::StepMacAddress { _hltSpaceCmdName switchName } {
    set incrMode [set $_hltSpaceCmdName\_user_input_args_array($switchName\_incr_mode)]
    set startMac [set $_hltSpaceCmdName\_user_input_args_array($switchName)]
    switch -exact $incrMode {
        increment {
            set stepValue [set $_hltSpaceCmdName\_user_input_args_array($switchName\_step)]
            set startMac [::sth::sthCore::macStep $startMac $stepValue 1]
        }
        random {
            set startMac [::sth::Eoam::CreateRandomMAC]
        }
        list {
            set MacList [set $_hltSpaceCmdName\_user_input_args_array($switchName\_list)]
            set startMac [lindex $MacList [expr [lsearch $MacList $startMac] + 1]]
        }
    }
    set $_hltSpaceCmdName\_user_input_args_array($switchName) $startMac
    return $startMac
}

proc ::sth::Eoam::StepMacLocalAddress { _hltSpaceCmdName } {
    set incrMode [set $_hltSpaceCmdName\_user_input_args_array(mac_local_incr_mode)]
    set startMac [set $_hltSpaceCmdName\_user_input_args_array(mac_local)]
    switch -exact $incrMode {
        increment {
            set stepValue [set $_hltSpaceCmdName\_user_input_args_array(mac_local_step)]
            set startMac [::sth::sthCore::macStep $startMac $stepValue 1]
        }
        random {
            set startMac [::sth::Eoam::CreateRandomMAC]
        }
        list {
            set MacList [set $_hltSpaceCmdName\_user_input_args_array(mac_local_list)]
            set startMac [lindex $MacList [expr [lsearch $MacList $startMac] + 1]]
        }
    }
    set $_hltSpaceCmdName\_user_input_args_array(mac_local) $startMac
    return $startMac
}

proc ::sth::Eoam::StepMacRemoteAddress { _hltSpaceCmdName } {
    set incrMode [set $_hltSpaceCmdName\_user_input_args_array(mac_remote_incr_mode)]
    set startMac [set $_hltSpaceCmdName\_user_input_args_array(mac_remote)]
    switch -exact $incrMode {
        increment {
            set stepValue [set $_hltSpaceCmdName\_user_input_args_array(mac_remote_step)]
            set startMac [::sth::sthCore::macStep $startMac $stepValue 1]
        }
        random {
            set startMac [::sth::Eoam::CreateRandomMAC]
        }
        list {
            set MacList [set $_hltSpaceCmdName\_user_input_args_array(mac_remote_list)]
            set startMac [lindex $MacList [expr [lsearch $MacList $startMac] + 1]]
        }
    }
    set $_hltSpaceCmdName\_user_input_args_array(mac_remote) $startMac
    return $startMac
}

proc ::sth::Eoam::StepMdLevel { _hltSpaceCmdName } {
    set incrMode [set $_hltSpaceCmdName\_user_input_args_array(md_level_incr_mode)]
    set startMdLevel [set $_hltSpaceCmdName\_user_input_args_array(md_level)]
    switch -exact $incrMode {
        increment {
            set stepValue [set $_hltSpaceCmdName\_user_input_args_array(md_level_step)]
            set startMdLevel [expr $startMdLevel + $stepValue]
        }
        random {
            set startMdLevel [::sth::Eoam::CreateRandomMdLevel]
        }
        list {
            set MdLevelList [set $_hltSpaceCmdName\_user_input_args_array(md_level_list)]
            set startMdLevel [lindex $MdLevelList [expr [lsearch $MdLevelList $startMdLevel] +1]]
        }
    }
    set $_hltSpaceCmdName\_user_input_args_array(md_level) $startMdLevel
    return $startMdLevel    
}

proc ::sth::Eoam::CreateRandomMdLevel { } {

        set randMdLevel ""

        set randMdLevel [expr { int(7 * rand()) }]

    return $randMdLevel
}

proc ::sth::Eoam::StepMepId { _hltSpaceCmdName} {
 
    set incrMode [set $_hltSpaceCmdName\_user_input_args_array(mep_id_incr_mode)]
    set startMepId [set $_hltSpaceCmdName\_user_input_args_array(mep_id)]
    
    switch -exact $incrMode {
        increment {
            set MepIdStep [set $_hltSpaceCmdName\_user_input_args_array(mep_id_step)]
            if {$startMepId == ""} {
                set startMepId 1
            } else {
                set startMepId [expr $startMepId + $MepIdStep]
            }
        }
        list {
            if {$startMepId == ""} {
                set XCount 0
            } else {
                set XCount [lsearch [set ${_hltSpaceCmdName}\_user_input_args_array(mep_id_list)] $startMepId]
                incr XCount
            }
            set startMepId [lindex [set ${_hltSpaceCmdName}\_user_input_args_array(mep_id_list)] $XCount]
        }
        random {
            while {1} {
                set startMepId [expr { int(8191 * rand()) }]
                if {$startMepId == 0} {
                    continue
                }
                foreach MepId $::sth::Eoam::usedMEP_ID {
                    set UsedFlag 0
                    if {$MepId == $startMepId} {
                        set UsedFlag 1  
                        break
                    }
                }
                if {$UsedFlag} {
                    continue
                } else {
                    break
                }                
            }
        }
    }
    set $_hltSpaceCmdName\_user_input_args_array(mep_id) $startMepId
    return $startMepId
}

proc ::sth::Eoam::GetEoamInfo_aggregate { returnKeyType resultHandleArrVarName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_info"    
    set _hltCmdName "emulation_oam_info_aggregate_$returnKeyType"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "
    
    upvar 1 $resultHandleArrVarName resultObjectHandleArr
    
    #return keys init   
    set returnKeyNameList [array names $_hltSpaceCmdName\_mode]
    
    if {$returnKeyType == "error"} {
        foreach returnKeyName $returnKeyNameList {
            set supported [set $_hltSpaceCmdName\_supported($returnKeyName)]
            if {$supported == "true"} {
                if {$returnKeyName == "fm_pkts"} {
                    continue
                }
                
                set returnSourceList ""
                switch $returnKeyName {
                    lbm_pkts {
                        lappend returnSourceList EoamLoopbackResults -DroppedPktCount
                        lappend returnSourceList EoamLoopbackResults -NumOfTimeouts
                        lappend returnSourceList EoamLoopbackResults -NumOfTransactionIdMismatches
                    }
                    ltm_pkts {
                        lappend returnSourceList EoamLinkTraceResults -DroppedPktCount
                        lappend returnSourceList EoamLinkTraceResults -NumOfTimeouts                    
                    }
                    ccm_pkts {
                        lappend returnSourceList EoamContChkLocalResults -DroppedPktCount
                        lappend returnSourceList EoamContChkLocalResults -NumOfTimeouts
                        #lappend returnSourceList EoamContChkLocalResults -BadContChkRxCount 
                    }
                    default {
                        ::sth::sthCore::processError returnKeyedList "error emulation_oam_info_aggregate_$returnKeyType return keys $returnKeyName."
                    }
                }
                set totalStats 0
                foreach {objType objAttr} $returnSourceList {
                    foreach objHandle $resultObjectHandleArr($objType) {
                        if {$objHandle ==""} {
                            continue
                        }
                        if {[catch {set tmpStats [::sth::sthCore::invoke stc::get $objHandle $objAttr]} errMsg]} {
                            ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $objHandle $objAttr\", errMsg: $errMsg."
                            set cmdState $FAILURE
                            return $returnKeyedList                            
                        }
                        set totalStats [expr $totalStats + $tmpStats]
                    }
                }
                
                keylset returnKeyedList aggregate.$returnKeyType.$returnKeyName $totalStats
            }
        }
    } else {
        foreach returnKeyName $returnKeyNameList {
            set supported [set $_hltSpaceCmdName\_supported($returnKeyName)]
            if {$supported == "true"} {
                if {$returnKeyName == "fm_pkts"} {
                    continue
                }

                set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_hltCmdName $returnKeyName stcobj]
                set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_hltCmdName $returnKeyName stcattr]
                
                set totalStats 0
                foreach resultObjectHandle $resultObjectHandleArr($stcObjName) {
                    if {$resultObjectHandle ==""} {
                        continue
                    }
                    set resultObjectHandle [lindex $resultObjectHandle 0]
                    if {[catch {set tmpStats [::sth::sthCore::invoke stc::get $resultObjectHandle -$stcAttrName]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $resultObjectHandle -$stcAttrName\", errMsg: $errMsg."
                        set cmdState $FAILURE
                        return $returnKeyedList                  
                    }
                    set totalStats [expr $totalStats + $tmpStats]
                }
                
                keylset returnKeyedList aggregate.$returnKeyType.$returnKeyName $totalStats            
            }
        }        
    }
    
    #set fm_pkts = sum of lbm_pkts ltm_pkts ccm_pkts
    if {$returnKeyType == "rx" || $returnKeyType =="tx" || $returnKeyType == "error"} {
        keylset returnKeyedList aggregate.$returnKeyType.fm_pkts  [expr [keylget returnKeyedList aggregate.$returnKeyType.lbm_pkts] + \
                                                                        [keylget returnKeyedList aggregate.$returnKeyType.ltm_pkts] + \
                                                                        [keylget returnKeyedList aggregate.$returnKeyType.ccm_pkts]]        
    }

    
    set cmdState $SUCCESS    
    return $returnKeyedList
}


proc ::sth::Eoam::GetMsgResultHandle { msgHandle resultHandleArrVarName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_info"    
    set _hltCmdName "GetMsgResultHandle"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName"
    
    upvar 1 $resultHandleArrVarName resultObjectHandleArr
    
	set megHandle [::sth::sthCore::invoke stc::get $msgHandle -MegAssociation-Targets]
	set megResultHandle [::sth::sthCore::invoke stc::get $megHandle -Children-EoamMegResults]
	lappend resultObjectHandleArr(EoamMegResults) [split $megResultHandle " "]
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamContChkLocalResults]
	lappend resultObjectHandleArr(EoamContChkLocalResults) $ResultHandle
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamLinkTraceResults]
	lappend resultObjectHandleArr(EoamLinkTraceResults) $ResultHandle
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamLoopbackResults]
	lappend resultObjectHandleArr(EoamLoopbackResults) $ResultHandle
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamDelayMeasurementResults]
	lappend resultObjectHandleArr(EoamDelayMeasurementResults) $ResultHandle
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamLckResults]
	lappend resultObjectHandleArr(EoamLckResults) $ResultHandle

	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamLossMeasurementResults]
	lappend resultObjectHandleArr(EoamLossMeasurementResults) $ResultHandle
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamSlmResults]
	lappend resultObjectHandleArr(EoamSlmResults) $ResultHandle
	
	set ResultHandle [::sth::sthCore::invoke stc::get $msgHandle -Children-EoamAisResults]
	lappend resultObjectHandleArr(EoamAisResults) $ResultHandle
		
    ::sth::sthCore::log debug "resultObjectHandleArr: [array get resultObjectHandleArr]"
    return $SUCCESS
}

proc ::sth::Eoam::GetTopologyResultHandle {topologyHandle resultHandleArrVarName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_info"    
    set _hltCmdName "GetTopologyResultHandle"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName"
    
    upvar 1 $resultHandleArrVarName resultObjectHandleArr
    
        foreach megHandle [set $topologyHandle\(EoamMegConfig)] {
            if {[catch {set megResultHandle [::sth::sthCore::invoke stc::get $megHandle -Children-EoamMegResults]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $megHandle -Children-EoamMegResults\", errMsg: $errMsg."
                set cmdState $FAILURE
                return $FAILURE                 
            }
            foreach handle $megResultHandle {
                if {[catch {set portName1 [::sth::sthCore::invoke stc::get $handle -PortName]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $handle -PortName\", errMsg: $errMsg."
                    set cmdState $FAILURE
                    return $FAILURE                    
                }
                set portHandle [lindex [split [lindex [split $topologyHandle "::"] end] "."] 0]
                if {[catch {set portName2 [::sth::sthCore::invoke stc::get $portHandle -Name]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $portHandle -Location\", errMsg: $errMsg."
                    set cmdState $FAILURE
                    return $FAILURE                    
                }
                if {$portName1 == $portName2} {
                    lappend resultObjectHandleArr(EoamMegResults) $handle
                }
            }
            
        }
        
        foreach mepHandle [set $topologyHandle\(EoamMaintenancePointConfig_MEP)] {
            if {[catch {set ResultHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-EoamContChkLocalResults]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $mepHandle -Children-EoamContChkLocalResults\", errMsg: $errMsg."
                set cmdState $FAILURE
                return $FAILURE                  
            }
            lappend resultObjectHandleArr(EoamContChkLocalResults) $ResultHandle
            
            if {[catch {set ResultHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-EoamLinkTraceResults]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $mepHandle -Children-EoamLinkTraceResults\", errMsg: $errMsg."
                set cmdState $FAILURE
                return $FAILURE                  
            }
            lappend resultObjectHandleArr(EoamLinkTraceResults) $ResultHandle          
            if {[catch {set ResultHandle [::sth::sthCore::invoke stc::get $mepHandle -Children-EoamLoopbackResults]} errMsg]} {
		::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $mepHandle -Children-EoamLoopbackResults\", errMsg: $errMsg."
                set cmdState $FAILURE
                return $FAILURE                
            }
            lappend resultObjectHandleArr(EoamLoopbackResults) $ResultHandle
        }
        
    return $SUCCESS
}

proc ::sth::Eoam::GetEoamInfo_session { returnKeyType resultHandleArrVarName returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_info"    
    set _hltCmdName "emulation_oam_info_session_$returnKeyType"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName "
    
    upvar 1 $resultHandleArrVarName resultObjectHandleArr
    
    #return keys init   
    set returnKeyNameList [array names $_hltSpaceCmdName\_mode]
    
    foreach returnKeyName $returnKeyNameList {
        set supported [set $_hltSpaceCmdName\_supported($returnKeyName)]
        if {$supported == "true"} {
            set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_hltCmdName $returnKeyName stcobj]
            set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_hltCmdName $returnKeyName stcattr]
            
            if {[catch {set tmpStats [::sth::sthCore::invoke stc::get $resultObjectHandleArr($stcObjName) -$stcAttrName]} errMsg]} {
		::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::GetNew $resultObjectHandleArr($stcObjName) $stcAttrName\", errMsg: $errMsg."
                set cmdState $FAILURE
                return $returnKeyedList                 
            }
            
            keylset returnKeyedList session.$returnKeyType.$returnKeyName $tmpStats            
        }
    }    

    set cmdState $SUCCESS    
    return $returnKeyedList    
}

proc ::sth::Eoam::SubscribeEoamResultdataset { } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::Eoam::resultDataSetSubscribed
    variable ::sth::Eoam::resultDataSetHdl
    
    set projectHandle $::sth::GBLHNDMAP(project)
    
    if {!$::sth::Eoam::resultDataSetSubscribed} {
        if {[catch {set resultDataSetHandle [::sth::sthCore::invoke stc::create ResultDataSet -under $projectHandle]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::CreateNew ResultDataSet $projectHandle\", errMsg: $errMsg."
            return $FAILURE                 
        }
        set ::sth::Eoam::resultDataSetHdl $resultDataSetHandle
        
        array set resultSubscribeArr {
            EoamPortConfig "EoamPortResults"
            EoamMegConfig "EoamMegResults"
            EoamMaintenancePointConfig "EoamLinkTraceResults EoamLoopbackResults EoamContChkLocalResults EoamDelayMeasurementResults EoamLckResults	EoamLossMeasurementResults	EoamSlmResults	EoamAisResults"
        }
    
        foreach configObj [array names resultSubscribeArr] {
            foreach resultsObj $resultSubscribeArr($configObj) {
                if {[catch {set resultQueryHandle [::sth::sthCore::invoke stc::create ResultQuery -under $resultDataSetHandle "-ResultRootList $projectHandle -ConfigClassId $configObj -ResultClassId $resultsObj"]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::CreateNew ResultQuery $resultDataSetHandle \"-ResultRootList $projectHandle -ConfigClassId $configObj -ResultClassId $resultsObj\"\", errMsg: $errMsg."
                    return $FAILURE                 
                }
            }
        }
	
	if {[catch {::sth::sthCore::invoke stc::perform "ResultDataSetSubscribe -ResultDataSet $resultDataSetHandle"} errMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::Perform \"ResultDataSetSubscribe -ResultDataSet $resultDataSetHandle\"\", errMsg: $errMsg."
	    return $FAILURE                
	}
    }

    ::sth::sthCore::log debug "successfully subscribe eoam result data set."
    set ::sth::Eoam::resultDataSetSubscribed 1
    return $SUCCESS
}

proc ::sth::Eoam::UnSubscribeEoamResultdataset { } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::Eoam::resultDataSetSubscribed
    variable ::sth::Eoam::resultDataSetHdl
    
    if {$::sth::Eoam::resultDataSetHdl ne "" } {
        ::sth::sthCore::invoke stc::perform ResultDataSetUnsubscribe -ResultDataSet $::sth::Eoam::resultDataSetHdl
        ::sth::sthCore::invoke stc::delete $::sth::Eoam::resultDataSetHdl
        set ::sth::Eoam::resultDataSetSubscribed 0
    }
    
    return $::sth::sthCore::SUCCESS
    
}

proc ::sth::Eoam::IsTopologyHandleValid { topologyHandle } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    if {[catch {set routerHandleList [set $topologyHandle\(Router)]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "input topology handle is not availble, errMsg: $errMsg" {}
        return $FAILURE    
    }
        if {[catch {set routerList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Router]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal command error \"stc::get $::sth::GBLHNDMAP(project) -Children-Router\", errMsg: $errMsg" {}
            return $FAILURE
        }
        
        foreach routerHandle $routerHandleList {
            foreach router $routerList {
                set availFlag 0
                if {[string equal $routerHandle $router]} {
                    set availFlag 1
                    break
                }
            }
            if {! $availFlag} {
                ::sth::sthCore::processError returnKeyedList "router handle $routerHandle is not available." 
                ::sth::sthCore::processError returnKeyedList "input topology handle is not availble." {}
                return $FAILURE
            }
        }
        
    return $SUCCESS
}

proc ::sth::Eoam::GetMegObjectHandle { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_topology"    
    set _hltCmdName "GetMegObjectHandle"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: _hltNameSpace $_hltCmdName "
        
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set returnMegHandle ""
    set projectHandle $::sth::GBLHNDMAP(project)
    
    set oamStandard [set ${_hltSpaceCmdName}\_user_input_args_array(oam_standard)]
    set megName [set ${_hltSpaceCmdName}\_user_input_args_array(md_name)]
    set mdLevel [set ${_hltSpaceCmdName}\_user_input_args_array(md_level)]
    
    set flag 0
    if { $oamStandard == "itut_y1731"} {
        if {[catch {set megHandleList [::sth::sthCore::invoke stc::get $projectHandle -Children-EoamMegConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when getting EoamMegConfig under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList 
        }
        
        foreach megHandle $megHandleList {
            if {[catch {set megId [::sth::sthCore::invoke stc::get $megHandle -MegId_IccString]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error ocured when getting MegId_IccString under $megHandle errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            if {[catch {set meLevel [::sth::sthCore::invoke stc::get $megHandle -MeLevel]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error ocured when getting MeLevel under $megHandle errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            if {($megId == $megName) && ($meLevel == $mdLevel)} {
                set returnMegHandle $megHandle
                set flag 1
                break
            }
        }
    }
    
    if {!$flag} {
        if {[catch {set returnMegHandle [::sth::sthCore::invoke stc::create EoamMegConfig -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamMegConfig under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList 
        }
    }

    set cmdState $SUCCESS
    return $returnMegHandle
}

###############################################################################
#emulation_oam_config_ma_meg_create
###############################################################################

proc ::sth::Eoam::emulation_oam_config_ma_meg_add { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
	set configedObjectAttributeArr ""
    set configedObjectAttributeArrR ""
    set remoteMepHandle ""
    set handle ""
    set megHandle ""
    
    set _OrigHltCmdName "emulation_oam_config_ma_meg"    
    set _hltCmdName "emulation_oam_config_ma_meg_add"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    set modeValue "add"
	  
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mp_handle)]} {
        set EoamMPHandle [set ${_hltSpaceCmdName}\_user_input_args_array(mp_handle)]       
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        set megHandle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]        
    }
    if {$megHandle == ""} {
        if {[catch {set megHandle [::sth::sthCore::invoke stc::create EoamMegConfig -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamMegConfig under $::sth::GBLHNDMAP(project) errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList 
        }
        keylset returnKeyedList handle $megHandle
    }
    #EoamRemoteMegEndPointConfig -under EoamMegConfig
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_mac_addr)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_id)]} {
        if {[catch {set remoteMepHandle [::sth::sthCore::invoke stc::create EoamRemoteMegEndPointConfig -under $megHandle]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when creating EoamRemoteMegEndPointConfig under $megHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList                 
        }
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_mac_addr)]} {
            set mep_mac_addr [set ${_hltSpaceCmdName}\_user_input_args_array(mep_mac_addr)]
            append configedObjectAttributeArrR " -RemoteMacAddr $mep_mac_addr"
        }
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mep_id)]} {
            set mep_id [set ${_hltSpaceCmdName}\_user_input_args_array(mep_id)]
            append configedObjectAttributeArrR " -RemoteMegEndPointId $mep_id"
        }
        ::sth::sthCore::invoke stc::config $remoteMepHandle $configedObjectAttributeArrR
    }
    
	set userInputList [array get ${_hltSpaceCmdName}\_user_input_args_array]
	foreach {switchName switchValue} $userInputList {
		if { $switchName == "optional_args" || $switchName == "mandatory_args"} {
			continue
		}
		set switchProcFunc [::sth::sthCore::getModeFunc2 $_hltNameSpace $_OrigHltCmdName $switchName $modeValue]
		if {[string equal $switchProcFunc "ProcessConfigCmd"]} {
			set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
			if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
				append configedObjectAttributeArr " -$stcAttrName $attrValue"
			} else {
				append configedObjectAttributeArr " -$stcAttrName $switchValue"
			} 
		} elseif {[string equal $switchProcFunc "ProcessConfigCmdHandle"]} {
			foreach mphandle $EoamMPHandle {
				::sth::sthCore::invoke stc::config $mphandle -MegAssociation-targets $megHandle
			}
		} 
	}
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        if {[catch {::sth::sthCore::invoke stc::config $megHandle $configedObjectAttributeArr} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when config $megHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList                    
        }
    }
        
    set cmdState $SUCCESS
    return $returnKeyedList
    
}

###
###emulation_oam_config_ma_meg_modify 
###
proc ::sth::Eoam::emulation_oam_config_ma_meg_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_ma_meg"    
    set _hltCmdName "emulation_oam_config_ma_meg_modify"
    set _hltNameSpace "::sth::Eoam::"
    
    set configedObjectAttributeArr ""
    set configedObjectAttributeArrR ""
    set remoteMepHandle ""
    set EoamMPHandle ""

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    set modeValue "modify"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Need input handle." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    set Handle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
	
	if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mp_handle)]} {
        set EoamMPHandle [set ${_hltSpaceCmdName}\_user_input_args_array(mp_handle)]  
    }
	
    set userInputList [array get ${_hltSpaceCmdName}\_user_input_args_array]
	foreach {switchName switchValue} $userInputList {
        if {![regexp -nocase $switchName $userInput]} {
            continue
        }
		set switchProcFunc [::sth::sthCore::getModeFunc2 $_hltNameSpace $_OrigHltCmdName $switchName $modeValue]
		if {[string equal $switchProcFunc "ProcessConfigCmd"]} {
			set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
			if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
				append configedObjectAttributeArr " -$stcAttrName $attrValue"
			} else {
				append configedObjectAttributeArr " -$stcAttrName $switchValue"
			} 
		} elseif {[string equal $switchProcFunc "ProcessConfigCmdHandle"]} {
				foreach mphandle $EoamMPHandle {
				::sth::sthCore::invoke stc::config $mphandle -MegAssociation-targets $Handle
			}
		}
	}
	if {[catch {::sth::sthCore::invoke stc::config $Handle $configedObjectAttributeArr} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error ocured when config $Handle errMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList                    
	}
    if {$remoteMepHandle != "" } { 
        if {[catch {::sth::sthCore::invoke stc::config $remoteMepHandle $configedObjectAttributeArrR} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error ocured when config $remoteMepHandle errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList                    
        }
    }
        
    set cmdState $SUCCESS
    return $returnKeyedList
}


###
###emulation_oam_config_ma_meg_delete 
###
proc ::sth::Eoam::emulation_oam_config_ma_meg_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_oam_config_ma_meg"    
    set _hltCmdName "emulation_oam_config_ma_meg_delete"
    set _hltNameSpace "::sth::Eoam::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Need input handle." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    set handle [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    
	::sth::sthCore::invoke stc::perform deletecommand -configlist "$handle"
	
    set cmdState $SUCCESS
    return $returnKeyedList
}
