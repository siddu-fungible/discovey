# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

#source sessionTable.tcl


namespace eval ::sth::Session:: {
    array set pfcFlag ""
        
    array set baseclass2relation {}
    array set prop2class {}
    array set class2relation {}
    array set obj2ret {}
    
    }
namespace eval ::sth::sthCore:: {}
namespace eval ::sth::Traffic {}

###/*! \ingroup sessionswitchprocfuncs
###\fn processConnectDevice (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName)
###\brief Returns the value of the switch from the input string
###
###This procedure is used to fetch the value of a particular switch from the user input. 
###
###\param[in] switchValinterface_configue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###
###\author Saumil Mehta
###\author Sapna Leupold (for P2)
###*/
###
###processConnectDevice (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName);
###
#set x [sth::connect -device $device -port_list $port_list];
proc ::sth::Session::processConnectDevice { } {
 
    variable ::sth::Session::CHASSISID2DEVICEMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar userArgsArray switchValuePairs;
    upvar connectKeyedList connectKeyedList;
    

    set _hltCmdName "Connect"
    set _switchName "device"
    set deviceCnt -1
    set devicelist $switchValuePairs(device)
    
    ::sth::sthCore::log info "{Calling processConnectDevice}"
    
    #If the connection already exists then STC ignores it.
    #According to Bll there is no need to add a check for this
    #::sth::sthCore::log debug "Trying to connect to the chassis.........\n"
    if {[info exists switchValuePairs(timeout)]} {
        set timeout $switchValuePairs(timeout)
    }
    foreach chassis $devicelist {
        incr deviceCnt
        if {[info exists switchValuePairs(timeout)]} {
            if {[catch {::sth::sthCore::invoke stc::perform ChassisConnect -TimeOutInSec $timeout -HostName $chassis -TcpPort 40004} performStatus]} {
                ::sth::sthCore::processError connectKeyedList "stc::perform Failed: Error while setting chassis timeout: $performStatus" {}
                set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList log "Internal Command Error while setting timeout for chassis: $performStatus"]
                set cmdFailed ::sth::sthCore::FAILURE
                return $::sth::sthCore::FAILURE
            } else {
                set ::sth::Session::CHASSISID2DEVICEMAP($chassis) $chassis
                ::sth::sthCore::log debug "{stc::perform: ChassisConnectCommand: $::sth::Session::CHASSISID2DEVICEMAP($chassis): Status: $performStatus}"
                ::sth::sthCore::log debug "Connected to chassis: $chassis"
            }
        } else {
            if {[catch {::sth::sthCore::invoke "stc::connect $chassis"} connectStatus ]} {
				::sth::sthCore::processError connectKeyedList "$chassis Internal Command Error while trying to connect to chassis $connectStatus" {}
				set cmdFailed ::sth::sthCore::FAILURE
				return $cmdFailed
            } else {
				set ::sth::Session::CHASSISID2DEVICEMAP($chassis) $chassis
				::sth::sthCore::log debug "{::sth::sthCore::invoke stc::connect Chassis: $::sth::Session::CHASSISID2DEVICEMAP($chassis): Status: $connectStatus}"
				::sth::sthCore::log debug "Connected to chassis: $chassis"
            }
        }
    }
        
    if {![::info exists cmdFailed]} {
        ::sth::sthCore::log info "{Successfully completed processing switch: $_switchName for HltCmd: $_hltCmdName}"
        return $::sth::sthCore::SUCCESS
    }
}

proc ::sth::Session::processConnectReset { } {
 
    variable ::sth::Session::CHASSISID2DEVICEMAP
    variable ::sth::Session::PORTHNDLIST
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar userArgsArray switchValuePairs;
    upvar connectKeyedList connectKeyedList;
    variable ::sth::sthCore::GBLHNDMAP
    
    set _hltCmdName "Connect"
    set _switchName "device"
    set deviceCnt -1
    
    set portlist $switchValuePairs(port_list)
    set resetPortList {}
    
    foreach port $portlist {
        foreach device $switchValuePairs(device) {
            set port "$device/$port"
            foreach {key value} [array get ::sth::Session::PORTHNDLIST] {
                if {$value == $port} {
                    lappend resetPortList $key
                }
            }
        }
    }
    
    ::sth::traffic_config -mode reset
    
    if {[llength $resetPortList] > 0} {
         foreach portHnd $resetPortList {
                #stc::delete $port
                if {[catch {::sth::sthCore::invoke stc::delete $portHnd} eMsg ]} {
                    #::sth::sthCore::processError cleanUpSessionKeyList "Error deleting $portHnd: $eMsg" {}
                    #return $::sth::sthCore::FAILURE
                } else {
                    catch {unset ::sth::Session::PORTHNDLIST($portHnd)}
                }
            }
    }
    
    if {![::info exists cmdFailed]} {
        return $::sth::sthCore::SUCCESS
    }
}

proc ::sth::Session::processConnectUsername { } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar userArgsArray usrArgsArray;
    upvar connectKeyedList connectKeyedList;
    
    set inputuserid $usrArgsArray(username)
    
        if {[catch {::sth::sthCore::invoke stc::get system1 -children-physicalchassismanager} getStatus]} {
            ::sth::sthCore::processError connectKeyedList "stc::get Failed: Error getting physicalchassismanager: $getStatus" {}
            set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList log "internal command error while getting children for physicalchassismanager"]
            return $::sth::sthCore::FAILURE
        }
        if {[catch {::sth::sthCore::invoke stc::config $getStatus -UserId $inputuserid} configStatus]} {
            ::sth::sthCore::processError connectKeyedList "stc::config Failed: Error while modifying setting Userid: $configStatus" {}
            set cmdFailed 1
            set connectKeyedList [::sth::sthCore::updateReturnInfo connectKeyedList log "Internal Command Error while modifying setting Userid $inputuserid"]
        }
        
        if {![::info exists cmdFailed]} {
            return $::sth::sthCore::SUCCESS
        } else {
            return $::sth::sthCore::FAILURE
        }
}


proc ::sth::Session::getPortGroupForPort {chassisIP slot port} {
    set chassisList [::sth::Session::getPhysicalChassis]
    foreach chassisHandle $chassisList {
        set hostname [::sth::sthCore::invoke stc::get $chassisHandle -Hostname]
        
        # This is the chassis that we want
        if {$hostname == $chassisIP} {
            ::sth::sthCore::log debug "chassis ip = $hostname"
            set moduleList [::sth::Session::getPhysicalTestModules $chassisHandle]
            foreach moduleHandle $moduleList {
                set slotIndex [::sth::sthCore::invoke stc::get $moduleHandle -Index]
                
                # This is the card we want
                if {$slot == $slotIndex} {
                    ::sth::sthCore::log debug "slot = $slotIndex"

                    # Determine the port group that the port resides in
                    set portGroupSize [::sth::sthCore::invoke stc::get $moduleHandle -PortGroupSize]
                    ::sth::sthCore::log debug "port group size = $portGroupSize"

                    set portGroupIndex [expr ( $port / $portGroupSize ) + ( $port % $portGroupSize )]
                    ::sth::sthCore::log debug "port group index = $portGroupIndex"

                    # Get the port group handle
                    set portGroupList [::sth::Session::getPhysicalPortGroups $moduleHandle]
                    foreach portGroupHandle $portGroupList {
                        set pgIndex [::sth::sthCore::invoke stc::get $portGroupHandle -Index]
                        
                        # This is the port group we want
                        if { $pgIndex == $portGroupIndex } {
                            ::sth::sthCore::log debug "port group handle = $portGroupHandle"
                            return $portGroupHandle
                        }
                    }
                }
            }
        }
    }

    ::sth::sthCore::log debug "** ERROR ** Could not find port group for $chassisIP/$slot/$port"
}

proc ::sth::Session::InstallChassisAndCardFw {  } {
 
    variable ::sth::Session::CHASSISID2DEVICEMAP
    variable ::sth::sthCore::SUCCESS 
    variable ::sth::sthCore::FAILURE
    variable ::sth::Session::PORTHNDLIST
    upvar userArgsArray switchValuePairs;
    upvar connectKeyedList connectKeyedList;
    
    set chassisHandle [::sth::Session::getPhysicalChassis]
    
    set version [::sth::sthCore::invoke stc::get  $chassisHandle -FirmwareVersion]
    ::sth::sthCore::log debug "Firmware version of chassisis: $version\n"
    
    #We will support only the fwversion that we release
    #hltapi with as discussed. Hardcoding for now, will remove it later as bll will have this
    #This will not work for Unix, this is going to be set by stc, this is temporary
    set fwDir "C:\Program Files\Spirent Communications\Spirent TestCenter\Spirent TestCenter Application\firmware"
    ::sth::sthCore::invoke stc::perform SetFirmwareArchivesDir -Dir $fwDir
    
    #Add the install version that hltapi will be released with
    set fwVersion "2.00.508"
    ::sth::sthCore::log debug "Installing chassis and card fw $fwVersion now....\n"
    ::sth::sthCore::invoke stc::perform InstallFirmware -EquipmentList $chassisHandle -Version $fwVersion
    ::sth::sthCore::log debug "Done installing chassis and card FW\n"
    
    set fwversion [::sth::sthCore::invoke stc::get $chassisHandle -FirmwareVersion]
    ::sth::sthCore::log debug "Firmware version of chassis is: $fwversion\n"
    
    return 1
}

proc ::sth::Session::processConnectNobios { } {
    if {$::sth::Session::xmlFlag == 1} {
        return;
    }
    
    variable ::sth::Session::CHASSISID2DEVICEMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Session::PORTHNDLIST
    upvar userArgsArray switchValuePairs;
    upvar connectKeyedList connectKeyedList;

    set _hltCmdName "Connect"
    set _switchName "nobios"
    set deviceCnt -1
    set portlist $switchValuePairs(port_list)
    set chassisIp $switchValuePairs(device)
    set installList {}
    set testPackage "stc"
    set testPackageVersion "2.0.508"
    
    ::sth::sthCore::log info "{Calling processConnectNobios}"
    
    if {$switchValuePairs(nobios) == 1} {
        
        #Install chassis FW and card module fw
        set status [::sth::Session::InstallChassisAndCardFw]
    
        foreach {cspToCreate} $portlist {
            #incr mapCnt
            #check the number of elements for the csp. Basically check if its a list or not.
            if {[llength $cspToCreate] > 1} {
                #the value is a list of csp. Process the List. Do a foreach loop to process each of them for the device.
                foreach {cspVal} $cspToCreate {
                    #Check if the user input is valid. If yes, proceed further.
                    set isValidInput 0
                    set seperatorUsed ""
                            foreach seperator ", /" {
                                set splittedInput [split $cspVal $seperator]
                                set splittedInputCnt [llength $splittedInput]
                                if {$splittedInputCnt == 2} {
                                    set isValidInput 1
                                    set seperatorUsed $seperator
                                    set cspToCreateLength 2
                                    set slotPortList $splittedInput
                                    break
                                }
                            }
                }
            } else {
                set isValidInput 0
                set seperatorUsed ""
                    foreach seperator ", /" {
                            set splittedInput [split $cspToCreate $seperator]
                            set splittedInputCnt [llength $splittedInput]
                    if {$splittedInputCnt == 2} {
                        set isValidInput 1
                        set seperatorUsed $seperator
                        set cspToCreateLength 2
                        set slotPortList $splittedInput
                        set slot "[lindex $slotPortList 0]"
                        set port "[lindex $slotPortList 1]"
                        #Call function to make port group list
                        set portgplist [::sth::Session::getPortGroupForPort $chassisIp $slot $port]
                        set found [lsearch -glob $installList $portgplist]
                        if {$found == -1} {
                            lappend installList $portgplist
                        } else {  
                        }
                        break
                    }
                }
            }
        }
        ::sth::sthCore::invoke stc::perform InstallTestPackage -PortGroupList $installList -TestPackage $testPackage -Version $testPackageVersion
    }
    
}


proc ::sth::Session::processOfflinePort {} {
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::Session::CHASSISID2DEVICEMAP
    variable ::sth::Session::PORTHNDLIST
    upvar userArgsArray switchValuePairs;
    upvar connectKeyedList connectKeyedList;
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar userArgsArray userArray
    set portlistarray ""

    set deviceCnt ""
    if {[::info exists switchValuePairs(device)]} {
        set deviceValue $switchValuePairs(device)
        set deviceCnt [llength $deviceValue]
    } else {
        return $::sth::sthCore::FAILURE
    }

    set portlist $switchValuePairs(port_list)
    set len [llength $portlist]
    if {$deviceCnt == 1 && [llength $portlist] > 1} {
        set portlist "{$portlist}"
    }
    
    set returnValue ""
    set mapCnt -1

    array set portArray {}
    set port_index 0
    if {$::sth::Session::xmlFlag == 1} {
        set myports [::sth::sthCore::invoke stc::get project1 -children-port];
        set ptArray [split [string map [list " " \0] $myports] \0]
        # if {[llength $ptArray] != $len} {
            # ::sth::sthCore::processError connectKeyedList "The number of reserving port is not equal to that of configuration file" {}
            # return $::sth::sthCore::FAILURE;
        # }
        foreach p $ptArray {
            set portArray($port_index) $p
            set port_index [expr $port_index + 1];
        }
    }
    
    set port_index 0

    foreach {cspToCreate} $portlist {
        incr mapCnt
        #check the number of elements for the csp. Basically check if its a list or not.
        if {[llength $cspToCreate] > 1} {
            #the value is a list of csp. Process the List. Do a foreach loop to process each of them for the device.
            foreach {cspVal} $cspToCreate {
                #Check if the user input is valid. If yes, proceed further.
                set isValidInput 0
                set seperatorUsed ""
                foreach seperator ", /" {
                    set splittedInput [split $cspVal $seperator]
                    set splittedInputCnt [llength $splittedInput]
                    if {$splittedInputCnt == 2} {
                        set isValidInput 1
                        set seperatorUsed $seperator
                        set cspToCreateLength 2
                        set slotPortList $splittedInput
                        break
                    }
                }
                if {$isValidInput != 1} {
                    return $::sth::sthCore::FAILURE                       
                }
                #Its a slot,port combination so will have to find the chassisIP
                if {[::info exists switchValuePairs(device)]} {
                    set ioDeviceAndIdList [lindex $switchValuePairs(device) $mapCnt]
                } else {
                    return $::sth::sthCore::FAILURE;
                }
                
                set chassisipaddr [lindex $deviceValue $mapCnt]
                set cspToReserve "$chassisipaddr/[lindex $slotPortList 0]/[lindex $slotPortList 1]"
                 
                set csp [split $cspToReserve /]
                set cspName "[join $csp -]"
                #Now create the port object and reserve the port
                if {$::sth::Session::xmlFlag == 1} {
                  # if current test is loaded by xml file, just use existed port object and config the location
                    set porthnd $portArray($port_index);
                    ::sth::sthCore::invoke stc::config $porthnd -location $cspToReserve -name $cspName
                    set port_index [expr $port_index + 1];
                    set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                    set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                    set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                    lappend portlistarray $porthnd
                } else {
                      if {[catch {set porthnd [::sth::sthCore::invoke stc::create Port -under $::sth::sthCore::GBLHNDMAP(project) "-location $cspToReserve -name $cspName"]} createStatus ]} {
                          ::sth::sthCore::processError connectKeyedList "Failed to create port under project $createStatus" {}
                          return $::sth::sthCore::FAILURE
                      } else {
                          set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                          set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                          set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                          lappend portlistarray $porthnd
                      }
                }
                #eval "$::sth::_SHA_DEBUG(level2) {Successfully Reserved the port:$cspToReserve. The port handle is $porthnd}"
                #saps check later if we we need to save the port name instead of the
                #chassis/slot/port
                if {[::info exists switchValuePairs(scheduling_mode)]} {
                      set listAttrList "-SchedulingMode $switchValuePairs(scheduling_mode)"
                      if {[catch {
			    set handleGenerator [::sth::sthCore::invoke stc::get $porthnd -children-generator]
			    set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
			    ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList	
					  } portMsg ]} {
                        ::sth::sthCore::processError connectKeyedList "stc::configGenerator Failed: Error Configuring Previously created port ($porthnd): $portMsg" {}
                        set cmdFailed 1
                      } 
                }
                set PORTHNDLIST($porthnd) $cspToReserve
                set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $ioDeviceAndIdList 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
            }
        } else {
            #Check if the user input is valid. If yes, proceed further.
            set isValidInput 0
            set seperatorUsed ""
                
            foreach seperator ", /" {
                set splittedInput [split $cspToCreate $seperator]
                set splittedInputCnt [llength $splittedInput]
                if {$splittedInputCnt == 2} {
                    set isValidInput 1
                    set seperatorUsed $seperator
                    set cspToCreateLength 2
                    set slotPortList $splittedInput
                    break
                }
            }
            if {$isValidInput != 1} {
                return 0                        
            }
    
            switch -exact -- $cspToCreateLength {
                2 {
                    
                    #The user has given only slot and port. ChassisID comes from the -device switch
                    #eval "$::sth::_SHA_DEBUG(level3) {The user has only specified Slot and Port.}"
                    #Its a slot,port combination so will have to find the chassisID
                    
                    if {[::info exists switchValuePairs(device)]} {
                        # SAPS: Chassis ip list to be made 
                        set ioDeviceAndIdList [lindex $switchValuePairs(device) $mapCnt]
                    } else {
                        return $::sth::sthCore::FAILURE;
                    }
                
                    set chassisipaddr [lindex $deviceValue $mapCnt]
                    set cspToReserve "$chassisipaddr/[lindex $slotPortList 0]/[lindex $slotPortList 1]"
                
                    set csp [split $cspToReserve /]
                    set cspName "[join $csp -]"               
                    if {$::sth::Session::xmlFlag == 1} {
                        # if current test is loaded by xml file, just use existed port object and config the location
                        set porthnd $portArray($port_index);
                        ::sth::sthCore::invoke stc::config $porthnd -location $cspToReserve -name $cspName
                            set port_index [expr $port_index + 1];
                            set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                            set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                            set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                            lappend portlistarray $porthnd
                     } else {
                        #Now create the port object and reserve the port
                        if {[catch {set porthnd [::sth::sthCore::invoke stc::create Port -under $::sth::sthCore::GBLHNDMAP(project) "-location $cspToReserve -name $cspName"]} createStatus ]} {
                           ::sth::sthCore::processError connectKeyedList "stc::create Failed: Error creating port: $createStatus" {}
                           return $::sth::sthCore::FAILURE
                        } else {
                            set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                            set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                            set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                            lappend portlistarray $porthnd
                        }
                     }
                    
                    if {[::info exists switchValuePairs(scheduling_mode)]} {
                          set listAttrList "-SchedulingMode $switchValuePairs(scheduling_mode)"
						  	
                          if {[catch {
				           set handleGenerator [::sth::sthCore::invoke stc::get $porthnd -children-generator]
				           set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
                                           ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList	
						  } portMsg ]} {
                            ::sth::sthCore::processError connectKeyedList "stc::configGenerator Failed: Error Configuring Previously created port ($porthnd): $portMsg" {}
                            set cmdFailed 1
                          } 
                    }
                    
                    set PORTHNDLIST($porthnd) $cspToReserve
                    set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $chassisipaddr 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
                }
                
                default {
                    #Unknown format for the chassisSlotPort
                    ::sth::sthCore::processError connectKeyedList "{UnSupported ChassisSlotPort combination}" {}
                    return $::sth::sthCore::FAILURE
                }
            } ;# switch
    
            set PORTHNDLIST($porthnd) $cspToCreate
            #set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $ioDeviceAndIdList 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
        }
    }
    
    if {[::info exists cmdFailed]} {
            return $::sth::sthCore::FAILURE
    } else {
            return $::sth::sthCore::SUCCESS
    }
}
###/*! \ingroup sessionswitchprocfuncs
###\fn processConnectPort_list (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName)
###\brief Process -port_list switch for connect command
###
###This procedure processes the -port_list switch for the connect command. For more details about valid inputs, check documentation
###
###
###\warning Depends on device switch output
###\author Saumil Mehta
###\author Sapna Leupold (For P2)
###*/
###
###processConnectPort_list 
###

proc ::sth::Session::processConnectPort_list {} {
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::Session::CHASSISID2DEVICEMAP
    variable ::sth::Session::PORTHNDLIST
    upvar userArgsArray switchValuePairs;
    upvar connectKeyedList connectKeyedList;
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar userArgsArray userArray;
    set portlistarray ""

    set deviceCnt ""
    if {[::info exists switchValuePairs(device)]} {
        set deviceValue $switchValuePairs(device)
        set deviceCnt [llength $deviceValue]
    } else {
        return $::sth::sthCore::FAILURE
    }

    set portlist $switchValuePairs(port_list)
    set len [llength $portlist]
    if {$deviceCnt == 1 && [llength $portlist] > 1} {
        set portlist "{$portlist}"
    }

    set returnValue ""
    set mapCnt -1

    array set portArray {}
    set port_index 0
    if {$::sth::Session::xmlFlag == 1} {
        set myports [::sth::sthCore::invoke stc::get project1 -children-port];
        set ptArray [split [string map [list " " \0] $myports] \0]
        # if {[llength $ptArray] != $len} {
            # ::sth::sthCore::processError connectKeyedList "The number of reserving port is not equal to that of configuration file" {}
            # return $::sth::sthCore::FAILURE;
        # }
        foreach p $ptArray {
            set portArray($port_index) $p
            set port_index [expr $port_index + 1];
        }
    }
    
    set port_index 0
    foreach {cspToCreate} $portlist {
        incr mapCnt
        #check the number of elements for the csp. Basically check if its a list or not.
        if {[llength $cspToCreate] > 1} {
            #the value is a list of csp. Process the List. Do a foreach loop to process each of them for the device.
            foreach {cspVal} $cspToCreate {
                #Check if the user input is valid. If yes, proceed further.
                set isValidInput 0
                set seperatorUsed ""
                        foreach seperator ", /" {
                                set splittedInput [split $cspVal $seperator]
                                set splittedInputCnt [llength $splittedInput]
                            if {$splittedInputCnt == 2} {
                               set isValidInput 1
                               set seperatorUsed $seperator
                               set cspToCreateLength 2
                               set slotPortList $splittedInput
                                break
                            }
                        }
                        
                        if {$isValidInput != 1} {
                            return $::sth::sthCore::FAILURE                       
                        }

                       #Its a slot,port combination so will have to find the chassisIP
                       if {[::info exists switchValuePairs(device)]} {
                           set ioDeviceAndIdList [lindex $switchValuePairs(device) $mapCnt]
                       } else {
                           return $::sth::sthCore::FAILURE;
                       }
            
                      set chassisipaddr [lindex $deviceValue $mapCnt]
                      set cspToReserve "$chassisipaddr/[lindex $slotPortList 0]/[lindex $slotPortList 1]"
                                         
                      set csp [split $cspToReserve /]
                      set cspName "[join $csp -]"
                      #Now create the port object and reserve the port
                      if {$::sth::Session::xmlFlag == 1} {
                        # if current test is loaded by xml file, just use existed port object and config the location
                        set porthnd $portArray($port_index);
                        ::sth::sthCore::invoke stc::config $porthnd -location $cspToReserve -name $cspName
                            set port_index [expr $port_index + 1];
                            set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                            set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                            set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                            lappend portlistarray $porthnd
                      } else {
                            if {[catch {set porthnd [::sth::sthCore::invoke stc::create Port -under $::sth::sthCore::GBLHNDMAP(project) "-location $cspToReserve -name $cspName"]} createStatus ]} {
                                ::sth::sthCore::processError connectKeyedList "Failed to create port under project $createStatus" {}
                                return $::sth::sthCore::FAILURE
                            } else {
                                set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                                set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                                set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                                lappend portlistarray $porthnd
                            }
                      }
                      
                      if {([info exists switchValuePairs(break_locks)]) && ($switchValuePairs(break_locks) == 1)} {
                        if {[catch {::sth::sthCore::invoke stc::perform ReservePort -Location $cspToReserve -RevokeOwner true} configStatus]} {
                            ::sth::sthCore::processError connectKeyedList "stc::perform Failed: Error while setting reserving port with breaklocks: $configStatus" {}
                            set cmdFailed 1
                            set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList log "Internal Command Error while reserving port with breaklocks"]
                        } else {

						  if {[::info exists switchValuePairs(scheduling_mode)]} {
							set listAttrList "-SchedulingMode $switchValuePairs(scheduling_mode)"
							if {[catch {
								set handleGenerator [::sth::sthCore::invoke stc::get $porthnd -children-generator]
								set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
								::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList
							} portMsg ]} {
							  ::sth::sthCore::processError connectKeyedList "stc::configGenerator Failed: Error Configuring Previously created port ($porthnd): $portMsg" {}
							  set cmdFailed 1
							} 
						  }
                                  
						  set PORTHNDLIST($porthnd) $cspToReserve
						  set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $ioDeviceAndIdList 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
                        }
                      } else {
                            if {[catch {::sth::sthCore::invoke stc::perform ReservePort -Location $cspToReserve} portMsg ]} {
                                ::sth::sthCore::processError connectKeyedList "{::sth::sthCore::invoke stc::perform ReservePort -Location $cspToReserve Failed : $portMsg}"
                                  if {[catch {::sth::sthCore::invoke stc::delete $porthnd} eMsg ]} {
                                      ::sth::sthCore::processError connectKeyedList "stc::delete Failed: Error Deleting Previously created port ($porthnd): $eMsg" {}
                                      set cmdFailed 1
                                  } else {
                                      ::sth::sthCore::log debug "{Deleted the Ethernet port with handle:$porthnd in the API.}"
                                  }                    
                                  return $::sth::sthCore::FAILURE
                          } else {
                                  #saps check later if we we need to save the port name instead of the
                                  #chassis/slot/port
							if {[::info exists switchValuePairs(scheduling_mode)]} {
								set listAttrList "-SchedulingMode $switchValuePairs(scheduling_mode)"
                                        if {[catch { 
											set handleGenerator [::sth::sthCore::invoke stc::get $porthnd -children-generator]
											set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
											::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList
										} portMsg ]} {
                                          ::sth::sthCore::processError connectKeyedList "stc::configGenerator Failed: Error Configuring Previously created port ($porthnd): $portMsg" {}
                                          set cmdFailed 1
                                        } 
							}

                                  set PORTHNDLIST($porthnd) $cspToReserve
                                  set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $ioDeviceAndIdList 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
                          }
                      }
            }
        } else {

                #Check if the user input is valid. If yes, proceed further.
            set isValidInput 0
            set seperatorUsed ""
            
                    foreach seperator ", /" {
                        set splittedInput [split $cspToCreate $seperator]
                        set splittedInputCnt [llength $splittedInput]
                    if {$splittedInputCnt == 2} {
                        set isValidInput 1
                        set seperatorUsed $seperator
                        set cspToCreateLength 2
                        set slotPortList $splittedInput
                        break
                    }
                    }
                    
                    if {$isValidInput != 1} {
                    return 0                        
                    }

                switch -exact -- $cspToCreateLength {
        
                    2 {
                            #The user has given only slot and port. ChassisID comes from the -device switch
                            #eval "$::sth::_SHA_DEBUG(level3) {The user has only specified Slot and Port.}"
                        #Its a slot,port combination so will have to find the chassisID
                    
                        if {[::info exists switchValuePairs(device)]} {
                           # SAPS: Chassis ip list to be made 
                           set ioDeviceAndIdList [lindex $switchValuePairs(device) $mapCnt]
                        } else {
                           return $::sth::sthCore::FAILURE;
                        }
                
                        set chassisipaddr [lindex $deviceValue $mapCnt]
                        set cspToReserve "$chassisipaddr/[lindex $slotPortList 0]/[lindex $slotPortList 1]"
                        set csp [split $cspToReserve /]
                        set cspName "[join $csp -]"               
                        if {$::sth::Session::xmlFlag == 1} {
                            # if current test is loaded by xml file, just use existed port object and config the location
                            set porthnd $portArray($port_index);
                            ::sth::sthCore::invoke stc::config $porthnd -location $cspToReserve -name $cspName
                                set port_index [expr $port_index + 1];
                                set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                                set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                                set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                                lappend portlistarray $porthnd
                         } else {
                            #Now create the port object and reserve the port
                            if {[catch {set porthnd [::sth::sthCore::invoke stc::create Port -under $::sth::sthCore::GBLHNDMAP(project) "-location $cspToReserve -name $cspName"]} createStatus ]} {
                               ::sth::sthCore::processError connectKeyedList "stc::create Failed: Error creating port: $createStatus" {}
                               return $::sth::sthCore::FAILURE
                            } else {
                                set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($porthnd) 0
                                set ::sth::Session::PORTLEVELARPSENDREQUEST($porthnd) 1
                                set ::sth::Session::PORTLEVELARPDONE($porthnd) 0
                                lappend portlistarray $porthnd
                            }
                        }

                        if {([info exists switchValuePairs(break_locks)]) && ($switchValuePairs(break_locks) == 1)} {
                            if {[catch {::sth::sthCore::invoke stc::perform ReservePort -Location $cspToReserve -RevokeOwner true} configStatus]} {
                                ::sth::sthCore::processError connectKeyedList "stc::perform Failed: Error while setting reserving port with breaklocks: $configStatus" {}
                                set cmdFailed 1
                                set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList log "Internal Command Error while reserving port with breaklocks"]
                            } else {
								#saps check later if we we need to save the port name instead of the
								#chassis/slot/port
								if {[::info exists switchValuePairs(scheduling_mode)]} {
									  set listAttrList "-SchedulingMode $switchValuePairs(scheduling_mode)"
                                      if {[catch { 
					                       set handleGenerator [::sth::sthCore::invoke stc::get $porthnd -children-generator]
					                       set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
					                       ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList
									  } portMsg ]} {
										::sth::sthCore::processError connectKeyedList "stc::configGenerator Failed: Error Configuring Previously created port ($porthnd): $eMsg" {}
										set cmdFailed 1
									  } 
								}
								set PORTHNDLIST($porthnd) $cspToReserve
								set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $ioDeviceAndIdList 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
                            }
                         } else {
                            if {[catch {::sth::sthCore::invoke "::sth::sthCore::invoke stc::perform ReservePort -Location $cspToReserve"} portMsg ]} {
                                        ::sth::sthCore::processError connectKeyedList "::sth::sthCore::invoke stc::perform ReservePort -Location $cspToReserve Failed: $cspToReserve $portMsg" {}
                                    if {[catch {::sth::sthCore::invoke stc::delete $porthnd} eMsg ]} {
                                        ::sth::sthCore::processError connectKeyedList "stc::delete Failed: Error Deleting Previously created port ($porthnd): $eMsg" {}
                                        set cmdFailed 1
                                    } else {
                                        ::sth::sthCore::log debug "{Deleted the Ethernet port with handle:$porthnd in the API.}"
                                    }                    
                                    return $::sth::sthCore::FAILURE
                            } else {
                                        #eval "$::sth::_SHA_DEBUG(level2) {Successfully Reserved the port:$cspToReserve. The port handle is $porthnd}"
                                    #saps check later if we we need to save the port name instead of the
                                    #chassis/slot/port
                                    if {[::info exists switchValuePairs(scheduling_mode)]} {
                                        set listAttrList "-SchedulingMode $switchValuePairs(scheduling_mode)"
										if {[catch { 
											set handleGenerator [::sth::sthCore::invoke stc::get $porthnd -children-generator]
											set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
											::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList
										} portMsg ]} {
                                            ::sth::sthCore::processError connectKeyedList "stc::configGenerator Failed: Error Configuring Previously created port ($porthnd): $portMsg" {}
                                            set cmdFailed 1
                                        } 
                                    }
                                    set PORTHNDLIST($porthnd) $cspToReserve
                                    set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList "port_handle.[lindex $ioDeviceAndIdList 0].[lindex $csp 1]$seperatorUsed[lindex $csp 2]" "$porthnd"]
                            }
                      }

                    }
                    default {
                        #Unknown format for the chassisSlotPort
                        ::sth::sthCore::processError connectKeyedList "{UnSupported ChassisSlotPort combination}" {}
                        return $::sth::sthCore::FAILURE
                    }
                } ;# switch

        }
    } ;#foreach
        
    #stc::perform setupPortMappings
    if {[catch {::sth::sthCore::invoke stc::perform setupPortMappings} configStatus]} {
        ::sth::sthCore::processError connectKeyedList "stc::perform Failed: Error with SetupPortMapping: $configStatus" {}
        set cmdFailed 1
        set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList log "Internal Command Error with SetupPortMapping"]
    }
    
        #::sth::sthCore::log debug "Start subscribe....this may take a few moments......\n"
        #set ret [::sth::Traffic::processTrafficStatsSubscribeProjectLevelCounters aggregate_tx Generator GeneratorPortResults]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeProjectLevelCounters aggregate_rx Analyzer AnalyerPortResults]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeProjectLevelCounters stream_tx StreamBlock TxStreamResults]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeProjectLevelCounters stream_rx StreamBlock RxStreamSummaryResults]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeProjectLevelCounters out_of_filter Analyzer OverflowResults]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeAggRxCounters $portlistarray]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeAggTxCounters $portlistarray]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeRxStreamCounters $portlistarray]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeTxStreamCounters $portlistarray]
        #set ret [::sth::Traffic::processTrafficStatsSubscribeUnknownOofRxCounters $portlistarray]
        #::sth::sthCore::log debug "End Subscribe"
    
    
    if {[::info exists cmdFailed]} {
            return $::sth::sthCore::FAILURE
    } else {
            return $::sth::sthCore::SUCCESS
    }
    
}

proc ::sth::Session::SetFECTrue100Gig {} {
	#return
	set hportslist [stc::get project1 -children-port]
	 
	foreach hport $hportslist {
		set hEterInterFace [stc::get $hport -ActivePhy-targets]
		if { ![string compare -length 19 "ethernet100gigfiber" $hEterInterFace ] } {
			::sth::sthCore::invoke stc::config $hEterInterFace -ForwardErrorCorrection true 
		}
	}
}
###\author Sapna Leupold
###*/
###
###processConfigCmd 
###

proc ::sth::Session::processConfigCmd {args} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar 1 userArray userSwitchArray
    upvar 1 userSwitchPriorityList userSwitchPList
    upvar interfaceConfKeyList interfaceConfKeyList;
    upvar stcattr stcattr
    upvar stcattrvalue stcattrvalue
    variable ::sth::sthCore::objecttype
    
    set switchValue [lindex $args 0]
    set switchName [lindex $args 1]
    set PortHndlValue [lindex $args 2]
    
    ::sth::sthCore::log info "{Calling: processConfigCmd}"
    
    if {[::info exists PortHndlValue]} {
        set PortHndlValue $PortHndlValue
    } else {
        return 1       
    }
    
    #check here to see that
    set value ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcattr
    set hlt2StcMapInfo [set $value\($switchName)]
    if {[info exists hlt2StcMapInfo]} {
        set stcattr $hlt2StcMapInfo
    } else {
        return $::sth::sthCore::SUCCESS
    }
    
    set hltswitchvalue $userSwitchArray($switchName)
    if {[info exists hltswitchvalue]} {
        set stcattrvalue $hltswitchvalue
        return $::sth::sthCore::SUCCESS
    } else {
        return $::sth::sthCore::FAILURE
    }

}

#Saps test cases
#macAddressToStcFormat "1122:3344:5566"
#macAddressToStcFormat "1122.3344.5566"
#macAddressToStcFormat "11.22.33.44.55.66"
#macAddressToStcFormat "11:22:33:44:55:66"
#macAddressToStcFormat "11-22-33-44-55-66"
#Stc Format: 11:22:33:44:55:66
proc ::sth::Session::macAddressToStcFormat {mac_value switchname portHndlValue} {

    upvar 1 userArray userSwitchArray
    upvar 1 userSwitchPriorityList userSwitchPList
    upvar interfaceConfKeyList interfaceConfKeyList;
    upvar stcattr stcattr
    upvar stcattrvalue stcattrvalue
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::objecttype
    
    if {[llength [split $mac_value {[\-|.|:]}]] != 6} {
        if {[llength [split $mac_value {.|:}]] != 3} {
            return -code 1 -errorcode -1 "Error: Invalid mac ($mac_value)"
        }
        regsub -all {[\:|.|\-]} $mac_value "" newMac
        if {[string length $newMac] != 12} {
            return -code 1 -errorcode -1 "Error: Invalid mac ($mac_value)"
        }
        set newMac_tmp ""
        for {set idx 0} {$idx <= 11} {incr idx 2} {
            set tmp [string range $newMac $idx [expr "$idx+1"]]
            set newMac_tmp "${newMac_tmp}:${tmp}"
        }
        set newMac [string trimleft $newMac_tmp :]
    } else {
        regsub -all {[\:|.|-]} $mac_value : newMac
    }
    #::sth::sthCore::log debug "new mac: $newMac\n"
    
    set value ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcattr
    set hlt2StcMapInfo [set $value\($switchname)]
    if {[info exists hlt2StcMapInfo]} {
        set stcattr $hlt2StcMapInfo
    } else {
        return $::stcCore::FAILURE
    }
    
    if {[info exists newMac]} {
        set stcattrvalue $newMac  
    } else {
        return $::stcCore::FAILURE
    }
    
    return $newMac

}

proc ::sth::Session::checkMacFormat {mac_value} {

    upvar 1 userArray userSwitchArray
    upvar 1 userSwitchPriorityList userSwitchPList
    
    upvar interfaceConfKeyList interfaceConfKeyList;
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::objecttype
    
    if {[string match *:* $mac_value]} {
        set ::sth::Session::macAddrFormat ":"
        if {[llength [split $mac_value {[\:]}]] == 6} {
            set ::sth::Session::nosOfColonsDotsDashes 5;
        } elseif {[llength [split $mac_value {[\:]}]] == 3} {
            set ::sth::Session::nosOfColonsDotsDashes 2;
        } 
    } elseif {[string match *-* $mac_value]} {
        set ::sth::Session::macAddrFormat "-"
        if {[llength [split $mac_value {[\:]}]] == 6} {
            set ::sth::Session::nosOfColonsDotsDashes 5;
        }
    } elseif {[string match *.* $mac_value]} {
        set ::sth::Session::macAddrFormat "."
        if {[llength [split $mac_value {[\.]}]] == 6} {
            set ::sth::Session::nosOfColonsDotsDashes 5;
        } elseif {[llength [split $mac_value {[\.]}]] == 3} {
            set ::sth::Session::nosOfColonsDotsDashes 2;
        } 
    }
}

proc ::sth::Session::covertStcMacToHltMacFormat {stcmac_value} {
    variable ::sth::Session::macAddrFormat
    variable ::sth::Session::nosOfColonsDotsDashes
    set newhltformat ""
    
    if {([string match *.* $stcmac_value]) || ([string match *:* $stcmac_value]) || ([string match *-* $stcmac_value])} {
        if {[string equal $::sth::Session::macAddrFormat "-"]} {
            regsub -all {[\:]} $stcmac_value - newhltformat
        } elseif {[string equal $::sth::Session::macAddrFormat "."]} {
            if {$::sth::Session::nosOfColonsDotsDashes == 5} {
                regsub -all {[\:]} $stcmac_value . newhltformat
            } elseif {$::sth::Session::nosOfColonsDotsDashes == 2} {
                regsub -all {[\:|.]} $stcmac_value "" newMac
                if {[string length $newMac] != 12} {
                    return -code 1 -errorcode -1 "Error: Invalid mac ($stcmac_value)"
                }
                set newMac_tmp ""
                for {set idx 0} {$idx <= 11} {incr idx 4} {
                    set tmp [string range $newMac $idx [expr "$idx+3"]]
                    set newMac_tmp "$newMac_tmp.$tmp"
                }
                set newhltformat [string trimleft $newMac_tmp .]
            }
        } elseif {[string equal $::sth::Session::macAddrFormat ":"]} {
            if {$::sth::Session::nosOfColonsDotsDashes == 5} {
                set newhltformat $stcmac_value
            } elseif {$::sth::Session::nosOfColonsDotsDashes == 2} {
                regsub -all {[\:]} $stcmac_value "" newMac
                if {[string length $newMac] != 12} {
                    return -code 1 -errorcode -1 "Error: Invalid mac ($stcmac_value)"
                }
                set newMac_tmp ""
                for {set idx 0} {$idx <= 11} {incr idx 4} {
                    set tmp [string range $newMac $idx [expr "$idx+3"]]
                    set newMac_tmp "$newMac_tmp:$tmp"
                }
                set newhltformat [string trimleft $newMac_tmp :]
            }
        } 
    }
    return $newhltformat
}

###\author Sapna Leupold
proc ::sth::Session::processConfigFwdCmd {switchValue switchName PortHndlValue} {

    upvar 1 userArray userSwitchArray
    upvar 1 userSwitchPriorityList userSwitchPList
    upvar interfaceConfKeyList interfaceConfKeyList;
    upvar stcattr stcattr
    upvar stcattrvalue stcattrvalue
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::objecttype
    
    ::sth::sthCore::log info "{Calling processConfigFwdCmd}"
    
    if {![::info exists PortHndlValue]} {
        return 0
    }
    set value ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcattr
    set hlt2StcMapInfo [set $value\($switchName)]
    if {[info exists hlt2StcMapInfo]} {
        set stcattr $hlt2StcMapInfo
    } else {
        return $::stcCore::FAILURE
    }
    
    set hltswitchvalue $userSwitchArray($switchName)
    if {[info exists hltswitchvalue]} {
        set hltswitchvalue $hltswitchvalue
        
    } else {
        return $::stcCore::FAILURE
    }
    
    set myVar "::sth::Session::interface_config_$::sth::sthCore::objecttype\_$switchName\_fwdmap"
    set stcattrvalue [set $myVar\($hltswitchvalue)];
    
    return $::sth::sthCore::SUCCESS
    
}

###/*! \ingroup sessionhelperfuncs
### \fn getPrefixLength (str ipVersion, str ipAddressValue)
###\brief Get the prefix Length
###
###This procedure returns the prefix length for the ipv4 address.
###\param[in] ipVersion The ip version \em 4 or \em 6.
###\param[in] ipAddressValue The current ip address
###
###\return _INT_SHA_CMD_FAIL or new Ip Address
###
###
###\author Saumil Mehta
###\todo Complete for ipv6 if needed.
###*/
###
###getPrefixLength (str ipVersion, str ipAddressValue);
###

proc ::sth::Session::getPrefixLength {args} {
        
    set ipVersion [lindex $args 0]
    set ipAddressValue [lindex $args 1]
    
    ::sth::sthCore::log info "{Calling getPrefixLength}"

    switch -exact -- $ipVersion \
        4 {
            set octets [split $ipAddressValue .]
            if {[llength $octets] != 4} {
                set octets [lrange [concat $octets 0 0 0] 0 3]
            }
            set binIpAddress ""
            foreach oct $octets {
                binary scan [binary format c $oct] B* bin
                set binIpAddress "$binIpAddress$bin"
            }

            for {set x 0;set prefixLength 0} {$x < 32} {incr x} {
                set oct [string range $binIpAddress $x $x]
                if {$oct != 1} {
                    break
                } else {
                    incr prefixLength
                }
            }
            return $prefixLength
        }\
        default {
        
        }
}

###\author Edited Sapna Leupold
proc ::sth::Session::processConfigNetmask {args} {
   
    upvar 1 userArray userSwitchArray
    upvar 1 userSwitchPriorityList userSwitchPList
    upvar interfaceConfKeyList interfaceConfKeyList;
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    upvar stcattr stcattr
    upvar stcattrvalue stcattrvalue
    variable ::sth::sthCore::objecttype
    
    set switchValue [lindex $args 0]
    set switchName [lindex $args 1]
    set PortHndlValue [lindex $args 2]
    
    ::sth::sthCore::log info "{Calling processConfigNetmask}"
 
    if {![::info exists PortHndlValue]} {
        return $::sth::sthCore::FAILURE
    } 
    
    #set stcattr ipv4PrefixLen
    set stcattrvalue [::sth::Session::getPrefixLength 4 $switchValue]
    if {![info exists stcattrvalue]} {
        return $::sth::sthCore::FAILURE
    } 
        
    set value ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcattr
    set hlt2StcMapInfo [set $value\($switchName)]

    #set hlt2StcMapInfo $::sth::Session::interface_config_stcattr($switchName)
    if {[info exists hlt2StcMapInfo]} {
        set stcattr $hlt2StcMapInfo
    } else {
        return $::sth::sthCore::SUCCESS
    }
    
    if {[::info exists cmdFailed]} {
            return $::sth::sthCore::FAILURE
    } else {
            return $::sth::sthCore::SUCCESS
    }  
}

proc ::sth::Session::configureEthernetAttributes {modeValue type porthandlevalue typelist} {
    upvar 1 userArgsArray userArray
    upvar interfaceConfKeyList interfaceConfKeyList;
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
	set activePhy [::sth::sthCore::invoke stc::get $porthandlevalue -activephy-Targets]
	if {$activePhy != ""} {
        set lineSpeed [::sth::sthCore::invoke stc::get $activePhy -LineSpeed]
        if {([regexp -nocase "40g" $type ] && [regexp -nocase "10g" $lineSpeed]) ||
            ([regexp -nocase "10g" $type ] && [regexp -nocase "40g" $lineSpeed])} {
            set speed "SPEED_10G"
            if {[regexp -nocase "40G" $type]} {
                set speed "SPEED_40G"
            }
            set ::sth::Session::sisterPortList [Config40GPort $porthandlevalue $speed]
        }
    }
	
    if {[string equal $modeValue "config"]} {
        if {$type == "EthernetWan"} {
            set ethernet10gHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-Ethernet10GigFiber"]
            if {[llength $ethernet10gHandle ] != 0} {
                set EthernetWanHndl [lindex [::sth::sthCore::invoke stc::get $ethernet10gHandle -children-EthernetWan] 0]
                if {![info exists EthernetWanHndl]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::get Failed: Error while getting EthernetWanHndl" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while getting EthernetWanHndl"]
                } else {
                    if {[llength $typelist] != 0} {
                        if {[catch {::sth::sthCore::invoke stc::config $EthernetWanHndl $typelist} configStatus]} {
                            ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting EthernetWanHndl parameters: $configStatus" {}
                            set cmdFailed 1
                            set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                        }
                    }
                }
            } else {
                #Create ethernet10GigFiber first
                if {[catch {set ethernet10gHandle [::sth::sthCore::invoke stc::create Ethernet10GigFiber -under $porthandlevalue $typelist]} createStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating Ethernet10GigFiber : $createStatus Switches: $typelist" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring Ethernet10GigFiber"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $createStatus} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
                set EthernetWanHndl [lindex [::sth::sthCore::invoke stc::get $ethernet10gHandle  -children-EthernetWan] 0]
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $EthernetWanHndl  $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting EthernetWan  parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                }
            }
        } else {
            set ethernetHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$type"]
            #when the type is EthernetCopper, it will also return the handle which is Ethernet10GigCopper, so need to remove it.
            if {[regexp -nocase "EthernetCopper" $type]} {
                set ethernetHanlde10G [::sth::sthCore::invoke stc::get $porthandlevalue "-children-Ethernet10GigCopper"]
                set ethernetHandle [string trim [regsub $ethernetHanlde10G $ethernetHandle ""]]
            } 
            if {[string equal $ethernetHandle ""]} {
                if {[catch {set ethernetHandle [::sth::sthCore::invoke stc::create $type -under $porthandlevalue $typelist]} createStatus ]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $type: $createStatus" {}
                    set cmdFailed 1
                    
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring $type"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $ethernetHandle} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
            } else {
                if {[llength $typelist] != 0} {
                    # fix "Observing 2 ethernetCopper handles withe FX2-1G-S16"
                    if {[llength $ethernetHandle] >1} {
                        set ethernetHandle [lindex $ethernetHandle 0]
                        }
                    if {[catch {::sth::sthCore::invoke stc::config $ethernetHandle $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                    if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $ethernetHandle} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                    }
                }
            }
			
            #check the value of the attribute "IsSpeedAutoNegotiationConfigurable", if it is false, then need to config autonegotiation as 1
            catch {
                set isSpeedAutoNegotiationConfigurable [::sth::sthCore::invoke stc::get $ethernetHandle -isSpeedAutoNegotiationConfigurable]
                if {[regexp -nocase "false" $isSpeedAutoNegotiationConfigurable]} {
                    ::sth::sthCore::invoke stc::config $ethernetHandle -AutoNegotiation true
                }
            }
        }
    } elseif {[string equal $modeValue "modify"]} {
        if {$type == "EthernetWan"} {
            set ethernet10GigHndl [::sth::sthCore::invoke stc::get $porthandlevalue "-children-Ethernet10GigFiber"]
            if {[llength $ethernet10GigHndl ] != 0} {
                set EthernetWanHndl [lindex [::sth::sthCore::invoke stc::get $ethernet10GigHndl -children-EthernetWan] 0]
                if {![info exists EthernetWanHndl]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::get Failed: Error while getting EthernetWanHndl" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while getting EthernetWan handle"]
                } else {
                    if {[llength $typelist] != 0} {
                        if {[catch {::sth::sthCore::invoke stc::config $EthernetWanHndl $typelist} configStatus]} {
                            ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting EthernetWan parameters: $configStatus" {}
                            set cmdFailed 1
                            set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                        }
                    }
                }
            } else {
                ::sth::sthCore::processError interfaceConfKeyList "stc::get Failed: Error while getting pos handle for config mode" {}
                set cmdFailed 1
                set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while getting wan handle for config mode"]
            }
        } else {
            set ethernetHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$type"]
            #when the type is EthernetCopper, it will also return the handle which is Ethernet10GigCopper, so need to remove it.
            if {[regexp -nocase "EthernetCopper" $type]} {
                set ethernetHanlde10G [::sth::sthCore::invoke stc::get $porthandlevalue "-children-Ethernet10GigCopper"]
                set ethernetHandle [string trim [regsub $ethernetHanlde10G $ethernetHandle ""]]
            } 
            # get the active ehternethandle
            set act_ethernetHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-activephy-Targets"]
            # fix "Observing 2 ethernetCopper handles withe FX2-1G-S16"
            if {[llength $ethernetHandle] >1} {
                set ethernetHandle [lindex $ethernetHandle 0]
                }            
            if {(![string equal $ethernetHandle $act_ethernetHandle]) && (![string equal $ethernetHandle ""])} {
                #create
                if {[catch {::sth::sthCore::invoke stc::config $porthandlevalue "-activephy-Targets $ethernetHandle"} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                }
            }
            if {[string equal $ethernetHandle ""]} {
                if {[catch {set ethernetHandle [::sth::sthCore::invoke stc::create $type -under $porthandlevalue $typelist]} createStatus ]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $type: $createStatus" {}
                    set cmdFailed 1
                    
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring $type"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $ethernetHandle} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
            } else {
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $ethernetHandle $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                    if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $ethernetHandle} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                    }
                }
            }
            catch {
                #check the value of the attribute "IsSpeedAutoNegotiationConfigurable", if it is false, then need to config autonegotiation as 1
                set isSpeedAutoNegotiationConfigurable [::sth::sthCore::invoke stc::get $ethernetHandle -isSpeedAutoNegotiationConfigurable]
                if {[regexp -nocase "false" $isSpeedAutoNegotiationConfigurable]} {
                        ::sth::sthCore::invoke stc::config $ethernetHandle -AutoNegotiation true
                }
            }
        }
    }
    
    if {[::info exists cmdFailed]} {
        return $::sth::sthCore::FAILURE
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::Config40GPort {port speed} {
    set physicalPort [::sth::sthCore::invoke stc::get $port -physicallogical-Sources]
    set sisterPortList ""
    #array set portGroupSiblings ()
    set portGroupSiblings [getSiblings $physicalPort]
    foreach portGroupSibling $portGroupSiblings {
        set sisterPhysicalPortList [::sth::sthCore::invoke stc::get $portGroupSibling -children-PhysicalPort]
        foreach sisterPhysicalPort $sisterPhysicalPortList {
            if {[regexp -nocase "^$sisterPhysicalPort$" $physicalPort]} {
                continue;
            }
            set sisterPort [::sth::sthCore::invoke stc::create port -under project1]
            lappend sisterPortList $sisterPort
            set port_loc [::sth::sthCore::invoke stc::get $sisterPhysicalPort -Location]
            set port_loc_ori [::sth::sthCore::invoke stc::get $sisterPort -Location]
            if {![regexp -nocase "^$port_loc$" $port_loc_ori]} {
                ::sth::sthCore::invoke stc::config $sisterPort -Location $port_loc
                ::sth::sthCore::invoke stc::perform setupportmappings
            }
            set activePhy [::sth::sthCore::invoke stc::get $sisterPort -activephy-Targets]
            ::sth::sthCore::invoke stc::config $activePhy -LineSpeed $speed
        }
    }
    return $sisterPortList
}

proc ::sth::Session::getSiblings {physicalPort} {
    set physicalPortGroup [::sth::sthCore::invoke stc::get $physicalPort -parent]
    set physicalTestModule [::sth::sthCore::invoke stc::get $physicalPortGroup -parent]
    set siblingsPerContainer [::sth::sthCore::invoke stc::get $physicalTestModule -PortGroupSize]
    
    if {$siblingsPerContainer} {
        set index [::sth::sthCore::invoke stc::get $physicalPortGroup -PortsCsvString]
        set tempIndex [split $index ","]
        set index [lindex $tempIndex 0]
        set basePortGroupIndex [expr {int(($index - 1) / $siblingsPerContainer) * $siblingsPerContainer + 1}]
        set lastPortGroupIndex  [expr {$basePortGroupIndex + $siblingsPerContainer}]
        set PhysicalPortsiblings ""
        set PhysicalPortGroupList [::sth::sthCore::invoke stc::get $physicalTestModule -children-PhysicalPortGroup]
        foreach PhysicalPortsibling $PhysicalPortGroupList {
            set index [::sth::sthCore::invoke stc::get $PhysicalPortsibling -PortsCsvString]
            set tempIndex [split $index ","]
            set index [lindex $tempIndex 0] 
            if {$index >= $basePortGroupIndex && $index < $lastPortGroupIndex} {
                lappend PhysicalPortsiblings $PhysicalPortsibling
            }
        }
    }
    return $PhysicalPortsiblings
}

proc ::sth::Session::configureOtherAttributes {modeValue type porthandlevalue typelist host} {
    upvar 1 userArray userArgsArray
    upvar interfaceConfKeyList interfaceConfKeyList;
    
    if {$type != "vlanif" && $type != "vlanouterif"} {
        if {[string equal $modeValue "config"]} {
            set returnhandl [::sth::sthCore::invoke stc::get $porthandlevalue -children-$type]
            if {[string equal $returnhandl ""]} {
                if {[catch {set returnhandl [::sth::sthCore::invoke stc::create $type -under $porthandlevalue $typelist]} createStatus ]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $type: $createStatus Switches: $typelist" {}
                    set cmdFailed 1
		    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring $type"]
                }
            } else {
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $returnhandl $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                }
            }
        } elseif {[string equal $modeValue "modify"]} {
            set returnhandl [::sth::sthCore::invoke stc::get $porthandlevalue -children-$type]
            if {[string equal $returnhandl ""]} {
                if {[catch {set returnhandl [::sth::sthCore::invoke stc::create $type -under $porthandlevalue $typelist]} createStatus ]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $type: $createStatus Switches: $typelist" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring $type"]
                }
            } else {
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $returnhandl $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting $type parameters $typelist : $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                }
            }
        }
    }
    if {[::info exists cmdFailed]} {
            return $::sth::sthCore::FAILURE
        }
	if { ( ![info exists userArgsArray(create_host)] || ![string equal $userArgsArray(create_host) "false"] ) && $host != 0} {
        if {$type == "ethiiif"} {
            set l2_if [::sth::sthCore::invoke stc::get $host -children-ethiiif]
            if {[string equal $l2_if ""]} {
                set l2_if [::sth::sthCore::invoke stc::create ethiiif -under $host]
            }
            ::sth::sthCore::invoke stc::config $l2_if $typelist
            return $l2_if
        }
        if {$type == "vlanif"} {
            set vlans [::sth::sthCore::invoke stc::get $host -children-vlanif]
            set vlan_if [lindex $vlans 0]
            if {[string equal $vlan_if ""]} {
                set vlan_if [::sth::sthCore::invoke stc::create vlanif -under $host]
            }
            ::sth::sthCore::invoke stc::config $vlan_if $typelist
            return $vlan_if
        }
        if {$type == "vlanouterif"} {
            set vlans [::sth::sthCore::invoke stc::get $host -children-vlanif]
            set vlanouter_if  [lindex $vlans 1]
            if {[string equal $vlanouter_if ""]} {
                set vlanouter_if [::sth::sthCore::invoke stc::create vlanif -under $host]
            }
            ::sth::sthCore::invoke stc::config $vlanouter_if $typelist
            return $vlanouter_if 
        }
        if {$type == "Ipv4If"} {
            set l3_if [::sth::sthCore::invoke stc::get $host -children-ipv4if]
            if {[string equal $l3_if ""]} {
                set l3_if [::sth::sthCore::invoke stc::create ipv4if -under $host]
            }
            ::sth::sthCore::invoke stc::config $l3_if $typelist
            return $l3_if
        }
        if {$type == "Ipv6If"} {
            set ipv6Stack [::sth::sthCore::invoke stc::get $host -children-ipv6if]
            if {![string equal $ipv6Stack ""]} {
                foreach ipif $ipv6Stack {
                    set addr [::sth::sthCore::invoke stc::get $ipif -Address]
                    if {[regexp -nocase "FE80" $addr] } {
                        set link_local $ipif
                    } else {
                        set ipv6if $ipif
                    }
                }
                ::sth::sthCore::invoke stc::config $ipv6if $typelist
            } else {
                set ipv6if [::sth::sthCore::invoke stc::create ipv6if -under $host]
                ::sth::sthCore::invoke stc::config $ipv6if $typelist
                set link_local [::sth::sthCore::invoke stc::create ipv6if -under $host -address "FE80::2"]
                ::sth::sthCore::invoke stc::config $link_local -AllocateEui64LinkLocalAddress true
            }
        }
        set handlelist {}
        if {[info exists ipv6if]} {
            lappend handlelist $ipv6if
        }
        if {[info exists link_local]} {
            lappend handlelist $link_local
        }
        return $handlelist
    }
   
    
    return $::sth::sthCore::SUCCESS
}


proc ::sth::Session::configureDeviceWizard {modeValue porthandlevalue} {
    upvar 1 userArray configArray
    upvar interfaceConfKeyList interfaceConfKeyList;
    
    if {[info exists configArray(count)]} {
        ##wizard way
		set blockMode ONE_DEVICE_PER_BLOCK
		if {[info exists configArray(block_mode)]} {
			set blockMode $configArray(block_mode)
		}
				
        set interfaceGen [::sth::sthCore::invoke stc::create EmulatedDeviceGenParams -under project1\
            -SelectedPort-targets $porthandlevalue -BlockMode $blockMode -Count $configArray(count)]
        
        set ethGen [::sth::sthCore::invoke stc::create DeviceGenEthIIIfParams -under $interfaceGen]
        if {[info exists configArray(src_mac_addr)]} {
            ::sth::sthCore::invoke stc::config $ethGen -SrcMac $configArray(src_mac_addr)]
        }
        set Lowif $ethGen
        
        if {[info exists configArray(vlan_id)]} {
            set vlan1Gen [::sth::sthCore::invoke stc::create DeviceGenVlanIfParams -under $interfaceGen]
            ::sth::sthCore::invoke stc::config $vlan1Gen -vlanId $configArray(vlan_id) -DeviceGenStackedOnIf-targets $ethGen
            if {[info exists configArray(vlan_id_count)]} {
                ::sth::sthCore::invoke stc::config $vlan1Gen -Count $configArray(vlan_id_count)
            }
            if {[info exists configArray(vlan_id_step)]} {
                ::sth::sthCore::invoke stc::config $vlan1Gen -IdStep $configArray(vlan_id_step)
            }
            if {[info exists configArray(vlan_user_priority)]} {
                ::sth::sthCore::invoke stc::config $vlan1Gen -Priority $configArray(vlan_user_priority)
            }
            set Lowif $vlan1Gen
        }
        
        if {[info exists configArray(vlan_outer_id)] && [info exists vlan1Gen]} {
            set vlan2Gen [::sth::sthCore::invoke stc::create DeviceGenVlanIfParams -under $interfaceGen]
            ::sth::sthCore::invoke stc::config $vlan2Gen -vlanId $configArray(vlan_outer_id) -DeviceGenStackedOnIf-targets $ethGen
            ::sth::sthCore::invoke stc::config $vlan1Gen -DeviceGenStackedOnIf-targets $vlan2Gen
            if {[info exists configArray(vlan_outer_id_count)]} {
                ::sth::sthCore::invoke stc::config $vlan2Gen -Count $configArray(vlan_outer_id_count)
            }
            if {[info exists configArray(vlan_outer_id_step)]} {
                ::sth::sthCore::invoke stc::config $vlan2Gen -IdStep $configArray(vlan_outer_id_step)
            }
            if {[info exists configArray(vlan_outer_user_priority)]} {
                ::sth::sthCore::invoke stc::config $vlan2Gen -Priority $configArray(vlan_outer_user_priority)
            }
        }
        
        if {[info exists configArray(intf_ip_addr)]} {
            set ipv4Gen [::sth::sthCore::invoke stc::create DeviceGenIpv4IfParams -under $interfaceGen\
                -Addr $configArray(intf_ip_addr) -DeviceGenStackedOnIf-targets $Lowif \
                -DeviceGenTopLevelIf-sources $interfaceGen]
            if {[info exists configArray(intf_ip_addr_step)]} {
                ::sth::sthCore::invoke stc::config $ipv4Gen -AddrStep $configArray(intf_ip_addr_step)
            }
            if {[info exists configArray(gateway)]} {
                ::sth::sthCore::invoke stc::config $ipv4Gen -Gateway $configArray(gateway)
            }
            if {[info exists configArray(gateway_step)]} {
                ::sth::sthCore::invoke stc::config $ipv4Gen -GatewayStep $configArray(gateway_step)
            }
        }
        if {[info exists configArray(ipv6_intf_addr)]} {
            set ipv6Gen1 [::sth::sthCore::invoke stc::create DeviceGenIpv6IfParams -under $interfaceGen -AddrType NON_LINK_LOCAL \
                -Addr $configArray(ipv6_intf_addr) -DeviceGenStackedOnIf-targets $Lowif \
                -DeviceGenTopLevelIf-sources $interfaceGen]
            if {[info exists configArray(ipv6_intf_addr_step)]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -AddrStep $configArray(ipv6_intf_addr_step)
            }
            if {[info exists configArray(ipv6_gateway)]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -Gateway $configArray(ipv6_gateway)
            }
            if {[info exists configArray(ipv6_gateway_step)]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -GatewayStep $configArray(ipv6_gateway_step)
            }
            if {[info exists configArray(ipv6_prefix_length)]} {
                ::sth::sthCore::invoke stc::config $ipv6Gen1 -PrefixLength $configArray(ipv6_prefix_length)
            }
            set ipv6Gen2 [::sth::sthCore::invoke stc::create DeviceGenIpv6IfParams -under $interfaceGen -AddrType LINK_LOCAL \
                -AutoAddrEnable TRUE -UseEui64LinkLocalAddress TRUE -DeviceGenStackedOnIf-targets $Lowif \
                -DeviceGenTopLevelIf-sources $interfaceGen]
        }
        
        if {[info exists configArray(expand)] &&
            $configArray(expand) == "false"} {
            keylset interfaceConfKeyList handle_list ""
            keylset interfaceConfKeyList param_handle $interfaceGen
        } else {
            array set return [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $interfaceGen]
            keylset interfaceConfKeyList handle_list $return(-ReturnList)
            keylset interfaceConfKeyList param_handle ""
        }
    }
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::configurePOSAttributes {modeValue type porthandlevalue typelist} {   
    variable userArgsArray
    upvar 1 userArgsArray userArray
    upvar interfaceConfKeyList interfaceConfKeyList;
    
    if {[string equal $modeValue "config"]} {
        if {[string equal $type "POSPhy"] || [string equal $type "AtmPhy"]} {
            set posHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$type"]
            if {[string equal $posHandle ""]} {
                if {[catch {set posHandle [::sth::sthCore::invoke stc::create $type -under $porthandlevalue $typelist]} createStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $type: $createStatus Switches: $typelist" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring $type"]
                }
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $posHandle $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                    
                }
            } else {
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $posHandle $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                    
                }
            }
            if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $posHandle} configStatus]} {
                ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                set cmdFailed 1
                set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
            }
        } elseif {[string equal $type "SonetConfig"]} {
            if {([string equal $::sth::sthCore::objecttype "AtmPhy"]) } {
                set parentobj "AtmPhy"
            } else {
                set parentobj "POSPhy"
            }
                
            set posHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$parentobj"]
            if {[llength $posHandle] != 0} {
                set SonetConfig [lindex [::sth::sthCore::invoke stc::get $posHandle -children-SonetConfig] 0]
                if {![info exists SonetConfig]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::get Failed: Error while getting SonetConfig" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while getting SonetConfig"]
                } else {
                    if {[llength $typelist] != 0} {
                        if {[catch {::sth::sthCore::invoke stc::config $SonetConfig $typelist} configStatus]} {
                            ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting SonetConfig parameters: $configStatus" {}
                            set cmdFailed 1
                            set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                        }
                    }
                }
            } else {
                #Create posphy first
                if {[catch {set posHandle [::sth::sthCore::invoke stc::create $parentobj -under $porthandlevalue $typelist]} createStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $parentobj: $createStatus Switches: $typelist" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring Ethiiif"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $createStatus} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
                set SonetConfig [lindex [::sth::sthCore::invoke stc::get $posHandle -children-SonetConfig] 0]
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $SonetConfig $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting SonetConfig parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                }
            }
        }
    } elseif {[string equal $modeValue "modify"]} {
        if {[string equal $type "SonetConfig"]} {
            if {([string equal $::sth::sthCore::objecttype "AtmPhy"])} {
                set parentobj "AtmPhy"
            } else {
                set parentobj "POSPhy"
            }
            
            set posHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$parentobj"]
            if {[llength $posHandle] != 0} {
                set SonetConfig [lindex [::sth::sthCore::invoke stc::get $posHandle -children-SonetConfig] 0]
                if {![info exists SonetConfig]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::get Failed: Error while getting SonetConfig" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while getting SonetConfig"]
                } else {
                    if {[llength $typelist] != 0} {
                        if {[catch {::sth::sthCore::invoke stc::config $SonetConfig $typelist} configStatus]} {
                            ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while setting SonetConfig parameters: $configStatus" {}
                            set cmdFailed 1
                            set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                        }
                    }
                }
            } else {
                ::sth::sthCore::processError interfaceConfKeyList "stc::get Failed: Error while getting pos handle for config mode" {}
                set cmdFailed 1
                set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while getting pos handle for config mode"]
            }
        } elseif {[string equal $type "POSPhy"]} {
            set posHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-POSPhy"]
            if {[llength $typelist] != 0} {
                if {[catch {::sth::sthCore::invoke stc::config $posHandle $typelist} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $posHandle} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
            }
        } elseif {[string equal $type "AtmPhy"]} {
            set posHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-AtmPhy"]
            if {[llength $typelist] != 0} {
                if {[catch {::sth::sthCore::invoke stc::config $posHandle $typelist} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $posHandle} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
            }
        }
    }

    if {[::info exists cmdFailed]} {
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS
}


proc ::sth::Session::configureFECAttributes {modeValue type porthandlevalue} {   
    variable userArgsArray
    upvar interfaceConfKeyList interfaceConfKeyList;

    set fecModeHandleList [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$type"]
    set i 0
    if {$fecModeHandleList ne ""} {
        set fecOptionList $userArgsArray(fec_option)
        foreach fecOption $fecOptionList {
            switch -exact -- $fecOption {
                ieee_cr_74_base_support {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode ieee -FecAction support -FecPhyType cr -FecType CLAUSE_74_BASE_R
                }
                ieee_cr_74_base_support_req {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode ieee -FecAction support_and_request -FecPhyType cr -FecType CLAUSE_74_BASE_R
                }
                ieee_cr_108_rs_support {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode ieee -FecAction support -FecPhyType cr -FecType CLAUSE_108_RS
                }
                ieee_cr_108_rs_support_req {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode ieee -FecAction support_and_request -FecPhyType cr -FecType CLAUSE_108_RS
                }
                ieee_cr_s_74_base_support {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode ieee -FecAction support -FecPhyType cr_s -FecType CLAUSE_74_BASE_R
                }
                ieee_cr_s_74_base_support_req {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode ieee -FecAction support_and_request -FecPhyType cr_s -FecType CLAUSE_74_BASE_R
                }
                consortium_25g_74_base_support {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode consortium_25g -FecAction support -FecPhyType none -FecType CLAUSE_74_BASE_R
                }
                consortium_25g_74_base_support_req {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode consortium_25g -FecAction support_and_request -FecPhyType none -FecType CLAUSE_74_BASE_R
                }
                consortium_25g_rs_support {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode consortium_25g -FecAction support -FecPhyType none -FecType CLAUSE_91_RS
                }
                consortium_25g_rs_support_req {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode consortium_25g -FecAction support_and_request -FecPhyType none -FecType CLAUSE_91_RS
                }
                disable_fec {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode force -FecAction disable -FecPhyType none -FecType none
                }
                enable_74_base {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode force -FecAction force -FecPhyType none -FecType CLAUSE_74_BASE_R
                }
                enable_108_rs {
                    ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecMode force -FecAction force -FecPhyType none -FecType CLAUSE_108_RS
                }
                default {
                    ::sth::sthCore::processError interfaceConfKeyList "fec_option: Invalid value: $type" {}
                    return $::sth::sthCore::FAILURE
                }
            }
            incr i
        }
        ##Disable others
        while { $i < [llength $fecModeHandleList]-5 } {
            ::sth::sthCore::invoke stc::config [lindex $fecModeHandleList $i] -FecAction NO_OP
            incr i
        }
    }
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::configureFcAttributes {modeValue type porthandlevalue typelist} {   
    variable userArgsArray
    upvar 1 userArgsArray userArray
    upvar interfaceConfKeyList interfaceConfKeyList;
    
    if {[string equal $modeValue "config"]} {
        if {[string equal $type "FcPhy"]} {
            set fcHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-$type"]
            if {[string equal $fcHandle ""]} {
                if {[catch {set fcHandle [::sth::sthCore::invoke stc::create $type -under $porthandlevalue $typelist]} createStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::create Failed: Error while creating $type: $createStatus Switches: $typelist" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while creating and configuring $type"]
                }
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $fcHandle $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                }
            } else {
                if {[llength $typelist] != 0} {
                    if {[catch {::sth::sthCore::invoke stc::config $fcHandle $typelist} configStatus]} {
                        ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                        set cmdFailed 1
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                    }
                    
                }
            }
            if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $fcHandle} configStatus]} {
                ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                set cmdFailed 1
                set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
            }
        }
    } elseif {[string equal $modeValue "modify"]} {
        if {[string equal $type "FcPhy"]} {
            set fcHandle [::sth::sthCore::invoke stc::get $porthandlevalue "-children-FcPhy"]
            if {[llength $typelist] != 0} {
                if {[catch {::sth::sthCore::invoke stc::config $fcHandle $typelist} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::config Failed: Error while modifying $type parameters: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while configuring $typelist"]
                }
                if {[catch {::sth::sthCore::invoke stc::perform PortSetupSetActivePhy -activephy $fcHandle} configStatus]} {
                    ::sth::sthCore::processError interfaceConfKeyList "stc::perform Failed: Error while setting activephy: $configStatus" {}
                    set cmdFailed 1
                    set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error while setting activePhy"]
                }
            }
        }
    }

    if {[::info exists cmdFailed]} {
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::interface_config_config_modify {modeValue } {
    variable ::sth::perfSwitch
    variable ::sth::Session::PORTHNDLIST
    upvar 1 userArgsArray userArray
    upvar interfaceConfKeyList interfaceConfKeyList;
    upvar 1 sortedSwitchPriorityList userSwitchPriorityList
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::objecttype
    set _OrigHltCmdName "interface_config"
    set _hltCmdName "interface_config_config_modify"
    set intconflistOfSwitches {};
    set intconfethiiiflistOfSwitches {};
    set intconfipv4iflistOfSwitches {};
    set intconfipv6iflistOfSwitches {};
    set intconfvlaniflistOfSwitches {};
    set intconfoutervlaniflistOfSwitches {};
    set intconfposlistOfSwitches {};
    set intconfatmlistOfSwitches {};
    set intconffclistOfSwitches {};
    set intconfsonetlistOfSwitches {};
    set intconfwanlistOfSwitches {};
    set intconfpfcmmlistOfSwitches {}
    set cmdResult ""
    set stcattr "" 
    set stcattrvalue ""
    set AlternateSpeedsStr ""
    set flagethiiif 0
    set flagipv4if 0
    set flagipv6if 0
    set flagposphy 0
    set flagatmphy 0
    set flagfcphy 0
    set flagsonetconfig 0 
    set flagwanconfig 0
    set flagvlanif 0
    set flagvlanouterif 0
    set flagpfcmmconfig 0
    variable ::sth::Session::macAddrFormat
    variable ::sth::Session::nosOfColonsDotsDashes
    set ::sth::Session::sisterPortList ""
    ::sth::sthCore::log info "{Calling interface_config_config_modify}"
    foreach key $userSwitchPriorityList {
        set switchName [lindex $key 1]
        if {([string equal $switchName "mode"]) || ([string equal $switchName "port_handle"])} {
        } else {
             set val ::sth::Session::interface_config_$::sth::sthCore::objecttype\_procfunc
             set myFunc [set $val\($switchName)]
             
             if {[string equal $switchName "src_mac_addr"]} {
                ::sth::Session::checkMacFormat $userArray(src_mac_addr)
             }
             
            if { [ string equal $switchName "alternate_speeds" ] } {
                    if {[info exists userArray(alternate_speeds)] && $userArray(alternate_speeds) != "" } {
                            set userArray(alternate_speeds) [string map {ether10000 SPEED_10G} $userArray(alternate_speeds)]
                            if {[set tempStr [string map {speed_unknown SPEED_UNKNOWN ether10000 SPEED_10G ether5Gig SPEED_5G ether2500 SPEED_2500M ether1000 SPEED_1G ether100 SPEED_100M} $userArray(alternate_speeds)]] != "$userArray(alternate_speeds)" } {
                               set userArray(alternate_speeds) $tempStr
                            }
                            set AlternateSpeedsStr "$userArray(alternate_speeds)"
                    }
                    
            }
             
             if {[string equal $switchName "dst_mac_addr"]} {
                if {[info exists userArray(ipv6_intf_addr)]} {
                    set stcobjvalue "Ipv6If"
                } else {
                    set stcobjvalue "Ipv4If"
                }
             } else {
                set stcobjval ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcobj
                set stcobjvalue [set $stcobjval\($switchName)]
             }
                
             if {[string equal $myFunc "_none_"]} {
                continue
             } else {
                set cmdResult [eval $myFunc $userArray($switchName) $switchName $userArray(port_handle)]
             }
             
             
             if {([string equal $stcattr "_none_"])} {
             } else {
                if {[string equal $stcobjvalue "ethiiif"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfethiiiflistOfSwitches -$stcattr $stcattrvalue;
                        set flagethiiif 1
                    }
                } elseif {[string equal $stcobjvalue "VlanIf"] && $userArray(vlan) == 1 && [info exists userArray(vlan_id)]} {
                   if {[llength $stcattr] != 0} {
                        lappend intconfvlaniflistOfSwitches -$stcattr $stcattrvalue;
                        set flagvlanif 1
                    }
                } elseif {[string equal $stcobjvalue "VlanOuterIf"] && $userArray(vlan) == 1 && [info exists userArray(vlan_outer_id)] && [info exists userArray(vlan_id)]} {
                   if {[llength $stcattr] != 0} {
                        lappend intconfvlanouteriflistOfSwitches -$stcattr $stcattrvalue;
                        set flagvlanouterif 1
                    }
                } elseif {[string equal $stcobjvalue "Ipv4If"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfipv4iflistOfSwitches -$stcattr $stcattrvalue;
                        # if stcattr is netmask, also map it to PrefixLength
                        if {$stcattr == "AddrStepMask"} {
                            set prefixValue [getPrefixLength 4 $stcattrvalue]
                            lappend intconfipv4iflistOfSwitches -PrefixLength $prefixValue;
                        }
                        set flagipv4if 1
                    }
                } elseif {[string equal $stcobjvalue "Ipv6If"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfipv6iflistOfSwitches -$stcattr $stcattrvalue;
                        set flagipv6if 1
                    }
                } elseif {[string equal $stcobjvalue "POSPhy"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfposlistOfSwitches -$stcattr $stcattrvalue;
                        set flagposphy 1
                    }
                } elseif {[string equal $stcobjvalue "AtmPhy"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfatmlistOfSwitches -$stcattr $stcattrvalue;
                        set flagatmphy 1
                    }
                } elseif {[string equal $stcobjvalue "FcPhy"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconffclistOfSwitches -$stcattr $stcattrvalue;
                        set flagfcphy 1
                    }
                } elseif {[string equal $stcobjvalue "SonetConfig"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfsonetlistOfSwitches -$stcattr $stcattrvalue;
                        set flagsonetconfig 1
                    }
                } elseif {([string equal $stcobjvalue "EthernetCopper"]) || ([string equal $stcobjvalue "EthernetFiber"]) || ([string equal $stcobjvalue "Ethernet10GigFiber"]
                    || [string equal $stcobjvalue "Ethernet100GigFiber"] || [string equal $stcobjvalue "Ethernet25GigFiber"] || [string equal $stcobjvalue "Ethernet40GigFiber"]
                    || [string equal $stcobjvalue "Ethernet10GigCopper"] || [string equal $stcobjvalue "Ethernet50GigFiber"])} {
                        if {([string equal $switchName "arp_req_timer"]) || ([string equal $switchName "arp_req_retries"]) || ([string equal $switchName "arp_send_req"])} {
                        } else {
                            if {([string equal $::sth::sthCore::objecttype "EthernetFiber"]) || ([string equal $::sth::sthCore::objecttype "Ethernet10GigFiber"])
                                || ([string equal $::sth::sthCore::objecttype "Ethernet10GigFiber"]) || ([string equal $::sth::sthCore::objecttype "Ethernet25GigFiber"])
                                || [string equal $stcobjvalue "Ethernet100GigFiber"] || [string equal $stcobjvalue "Ethernet40GigFiber"] || ([string equal $::sth::sthCore::objecttype "Ethernet50GigFiber"])} {
                                if {(![string equal $stcattr "LineSpeed"]) && (![string equal $switchName "Duplex"])} {
                                    if {[llength $stcattr] != 0} {
                                        lappend intconflistOfSwitches -$stcattr $stcattrvalue;
                                    }
                                }
                            } else {
                                if {[llength $stcattr] != 0} {
                                    lappend intconflistOfSwitches -$stcattr $stcattrvalue;
                                }
                            }
                        }
                } elseif {[string equal $stcobjvalue "EthernetWan"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfwanlistOfSwitches -$stcattr $stcattrvalue;
                        set flagwanconfig 1
                    }
                    
                } elseif {[string equal $stcobjvalue "PfcMeasurementConfig"]} {
                    if {[llength $stcattr] != 0} {
                        lappend intconfpfcmmlistOfSwitches -$stcattr $stcattrvalue;
                        set flagpfcmmconfig 1
                    }                    
                }
             }
        }
        if {$cmdResult == 0} {
            break
        }
    }

    set porthandlevalue $userArray(port_handle)
    
    #add by Fei Cheng. we need to create a host here to do the arp and let the DUT know the
    #info of the stc side. or the raw trffic couldn't get through. see CR #168232912
    #only do arp when arp_send_req is 1
    if {![info exists userArray(create_host)] || ![string equal $userArray(create_host) "false"] } {  
        if {[string equal $userArray(mode) "config"]} {
                if {[catch {::sth::sthCore::invoke stc::create host -under $::sth::GBLHNDMAP(project)} hostHandle]} {
                    return -code error "Failed to create host"
                }
        
            if {$flagvlanouterif} {
                if {[string equal $userArray(qinq_incr_mode) "both"]} {
                    if {$userArray(vlan_outer_id_count) >= $userArray(vlan_id_count) } {
                        set deviceCount $userArray(vlan_outer_id_count)
                        lappend intconfvlaniflistOfSwitches     -IdRepeatCount 0   -IfRecycleCount $userArray(vlan_id_count)
                    } else {
                        set deviceCount $userArray(vlan_id_count)
                        lappend intconfvlanouteriflistOfSwitches   -IdRepeatCount 0   -IfRecycleCount $userArray(vlan_outer_id_count)
                    }
                } elseif {[string equal $userArray(qinq_incr_mode) "inner"]} {
                    lappend intconfvlanouteriflistOfSwitches -IdRepeatCount [expr $userArray(vlan_id_count) - 1] -IfRecycleCount 0
                    lappend intconfvlaniflistOfSwitches     -IdRepeatCount 0   -IfRecycleCount $userArray(vlan_id_count)
                    set deviceCount [expr  $userArray(vlan_outer_id_count) * $userArray(vlan_id_count)]
                } else {
                    lappend intconfvlanouteriflistOfSwitches   -IdRepeatCount 0   -IfRecycleCount $userArray(vlan_outer_id_count)
                    lappend intconfvlaniflistOfSwitches   -IdRepeatCount [expr $userArray(vlan_outer_id_count) - 1] -IfRecycleCount 0
                    set deviceCount [expr  $userArray(vlan_outer_id_count) * $userArray(vlan_id_count)]
                }
            } elseif {$flagvlanif} {
                set deviceCount 1
                if {[info exists userArray(vlan_id_count)]} {
                    set deviceCount $userArray(vlan_id_count)
                }
            } else {
                set deviceCount 1
            }
        
        
            # setup relations
            set hostName "port_address"
            if {[catch {::sth::sthCore::invoke stc::config $hostHandle "-AffiliationPort-targets $porthandlevalue -name $hostName -DeviceCount $deviceCount"} error]} {
                ::sth::sthCore::processError returnKeyedList "stc::configNew Failed: $error"
            }
        
            # enable ping response
            if {[info exists userArray(enable_ping_response)]} {
                if {[catch {::sth::sthCore::invoke stc::config $hostHandle "-EnablePingResponse $userArray(enable_ping_response)"} error]} {
                ::sth::sthCore::processError returnKeyedList "stc::configNew Failed: $error"
                }
            }
        
        } else {
            set hosts [::sth::sthCore::invoke stc::get $porthandlevalue "-AffiliationPort-Sources"]
            if { $hosts == "" } {
                set  hostHandle 0 
            }
            foreach host $hosts {
                if {[string equal "port_address" [::sth::sthCore::invoke stc::get $host "-Name"]]} {
                    set hostHandle $host
                    set deviceCount [::sth::sthCore::invoke stc::get $host "-DeviceCount"]
                    break
                } else {
                    set  hostHandle 0  
                }
            }
        }
    } else {
        #when create_host is false
        set  hostHandle 0
        ::sth::Session::configureDeviceWizard $modeValue $porthandlevalue
    }
    
    set cmdResult [::sth::Session::configureEthernetAttributes $modeValue $::sth::sthCore::objecttype $porthandlevalue $intconflistOfSwitches]
    if {$cmdResult == 0} {
        ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring $::sth::sthCore::objecttype" {}
        return $::sth::sthCore::FAILURE
    }
    if {$AlternateSpeedsStr != ""} {
        set phyhandle [stc::get $porthandlevalue -children-Ethernet10GigCopper]
        if { $phyhandle != "" } {
        stc::config $phyhandle -AlternateSpeeds $AlternateSpeedsStr
        }
    } else {
        if {([info exists userArray(mode)]) && ($userArray(mode) != "modify")} {
            set phyhandle [stc::get $porthandlevalue -children-Ethernet10GigCopper]
            if { $phyhandle != "" } {
            stc::config $phyhandle -AlternateSpeeds SPEED_UNKNOWN
            }
        }
    }
    
    if {$flagwanconfig} {
        set cmdResult [::sth::Session::configureEthernetAttributes $modeValue EthernetWan $porthandlevalue $intconfwanlistOfSwitches]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring 10gigwan" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagethiiif} {
        set l2_if [::sth::Session::configureOtherAttributes $modeValue ethiiif $porthandlevalue $intconfethiiiflistOfSwitches $hostHandle]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring ethiiif" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagvlanif} {
        set vlan_if [::sth::Session::configureOtherAttributes $modeValue vlanif $porthandlevalue $intconfvlaniflistOfSwitches $hostHandle]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring vlanif" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagvlanouterif} {
        set vlanouter_if [::sth::Session::configureOtherAttributes $modeValue vlanouterif $porthandlevalue $intconfvlanouteriflistOfSwitches $hostHandle]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring vlanouterif" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagipv4if} {
        set ipv4_if [::sth::Session::configureOtherAttributes $modeValue Ipv4If $porthandlevalue $intconfipv4iflistOfSwitches $hostHandle]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring ipv4if" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagipv6if} {
        set ipv6_if [::sth::Session::configureOtherAttributes $modeValue Ipv6If $porthandlevalue $intconfipv6iflistOfSwitches $hostHandle]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring ipv6if" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagposphy} {
        set cmdResult [::sth::Session::configurePOSAttributes $modeValue POSPhy $porthandlevalue $intconfposlistOfSwitches]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring posPHY" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagatmphy} {
        set cmdResult [::sth::Session::configurePOSAttributes $modeValue AtmPhy $porthandlevalue $intconfatmlistOfSwitches]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring atmPHY" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagsonetconfig} {
        set cmdResult [::sth::Session::configurePOSAttributes $modeValue SonetConfig $porthandlevalue $intconfsonetlistOfSwitches]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring sonetPHY" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagfcphy} {
        set cmdResult [::sth::Session::configureFcAttributes $modeValue FcPhy $porthandlevalue $intconffclistOfSwitches]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring FcPHY" {}
            return $::sth::sthCore::FAILURE
        }
    }
    if {$flagpfcmmconfig} {
        set cmdResult [::sth::Session::configureOtherAttributes $modeValue PfcMeasurementConfig $porthandlevalue $intconfpfcmmlistOfSwitches $hostHandle]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring PFCMM" {}
            return $::sth::sthCore::FAILURE
        }
    }

    if {[info exists userArray(fec_option)]} {
        set cmdResult [::sth::Session::configureFECAttributes $modeValue FecModeObject $porthandlevalue]
        if {$cmdResult == 0} {
            ::sth::sthCore::processError interfaceConfKeyList "Internal Command Error: Error occured while configuring FEC" {}
            return $::sth::sthCore::FAILURE
        }
    }
    
    #Ignoring ethIf, vlan, ipv4, ipv4, since not valid for FC
    if {!$flagfcphy} {
        if { ( ![info exists userArray(create_host)] || ![string equal $userArray(create_host) "false"] ) && $hostHandle != 0 } {
            if {![info exists l2_if] && $userArray(mode) == "config"} {
                #create default l2 if
                if {[catch {::sth::sthCore::invoke stc::create ethiiif -under $hostHandle} l2_if]} {
                    return -code error "Failed to create host"
                }
            } 
            if {[info exists l2_if]} {
                set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
                set macStep "00:00:00:00:00:01"
                if {![info exists userArray(src_mac_addr)]} {
                    set srcMac [::sth::sthCore::invoke stc::get $addrOption -NextMac]
                    #converting xxxx.xxxx.xxxx format to xx.xx.xx.xx.xx
                    if {[regexp {[0-9a-fA-F]+\.[0-9a-fA-F]+\.[0-9a-fA-F]+} $srcMac]} {
                        set temp $srcMac
                        regsub -all {\.} $temp "" temp
                        set tmp [split $temp ""]
                        set cnt 0
                        foreach i $tmp {
                        if {$cnt == 2} {
                                append newStr ":"
                                set cnt 0
                        }
                        append newStr $i
                        incr cnt
                        }
                        set srcMac $newStr
                    }
                    ::sth::sthCore::invoke stc::config $l2_if "-SourceMac $srcMac"
                } else {
                    set srcMac $userArray(src_mac_addr)
                    if {[info exists userArray(src_mac_addr_step)]} {
                        set macStep $userArray(src_mac_addr_step)
                    } 
                }
                set nextMac [::sth::sthCore::macStep $srcMac $macStep $deviceCount]
                ::sth::sthCore::invoke stc::config $addrOption "-NextMac $nextMac"
            }
            if {![info exists ipv4_if] && ![info exists ipv6_if] && $userArray(mode) == "config"} {
                #create default l3 if
                if {[catch {::sth::sthCore::invoke stc::create ipv4if -under $hostHandle} ipv4_if]} {
                    return -code error "Failed to create host"
                }
            }
            set topifs {}
            if {[info exists vlanouter_if]} {
                if {![info exists l2_if]} {
                    #get l2 if
                    if {[catch {::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif} l2_if]} {
                        return -code error "Failed to create host"
                    }
                }
                ::sth::sthCore::invoke stc::config $vlanouter_if "-stackedonendpoint-targets $l2_if"
                ::sth::sthCore::invoke stc::config $vlan_if "-stackedonendpoint-targets $vlanouter_if"
                set lowif $vlan_if
            } elseif {[info exists vlan_if]} {
                if {![info exists l2_if]} {
                    #get l2 if
                    if {[catch {::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif} l2_if]} {
                        return -code error "Failed to create host"
                    }
                }
                ::sth::sthCore::invoke stc::config $vlan_if "-stackedonendpoint-targets $l2_if"
                set lowif $vlan_if
            } elseif {[info exists l2_if]} {
                set lowif $l2_if
            } elseif {[info exists hostHandle]} {
                set lowif [::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif]
            }
        
            if {[info exists ipv4_if]} {
                foreach ipif $ipv4_if {
                    ::sth::sthCore::invoke stc::config $ipif "-stackedonendpoint-targets $lowif"
                    lappend topifs $ipif
                }
            }
            
            if {[info exists ipv6_if]} {
                foreach ipif $ipv6_if {
                    ::sth::sthCore::invoke stc::config $ipif "-stackedonendpoint-targets $lowif"
                    lappend topifs $ipif
                }
        
            }
            if {$topifs!=""} {
                ::sth::sthCore::invoke stc::config $hostHandle "-toplevelif-targets {$topifs} -primaryif-targets {$topifs}"
            }
        }
        #end of create_host condition 
        if {[::info exists userArray(scheduling_mode)]} {
          set listAttrList "-SchedulingMode $userArray(scheduling_mode)"
          if {[catch { 
            set handleGenerator [::sth::sthCore::invoke stc::get $porthandlevalue -children-generator]
            set handleGeneratorConfig [::sth::sthCore::invoke stc::get $handleGenerator -children-generatorconfig]
            ::sth::sthCore::invoke stc::config $handleGeneratorConfig $listAttrList	
          } portMsg ]} {
            ::sth::sthCore::processError interfaceConfKeyList "stc::configGenerator Failed: Error configuring the attributes of the port ($porthandlevalue): $portMsg" {}
            return $::sth::sthCore::FAILURE
          }
           if {$userArray(scheduling_mode) == "PORT_BASED" && [::info exists userArray(port_loadunit)] && [::info exists userArray(port_load)]} {
             set loadAttrList "-LoadMode FIXED -LoadUnit $userArray(port_loadunit) -FixedLoad $userArray(port_load)"
             if {[catch {::sth::sthCore::invoke stc::config $handleGeneratorConfig $loadAttrList} error]} {
                ::sth::sthCore::processError returnKeyedList "stc::configGenerator Failed: $error"
             }
          }
        }
        if {![info exists userArray(intf_mode)] || $userArray(intf_mode) == "ethernet"} {
            if {[info exists userArray(arp_send_req)] && $userArray(arp_send_req)} {
    
                set hosts [::sth::sthCore::invoke stc::get $porthandlevalue "-AffiliationPort-Sources"]
                set streams [::sth::sthCore::invoke stc::get $porthandlevalue "-children-StreamBlock"]
                set devices {}
                set target  ""
                set port_address $porthandlevalue
                if { $hosts != "" } {
                    # For US37495, optimized for scaling scenario.
                    set devices $hosts
                    set last_host [lindex $hosts end]
                    if {[string equal "port_address" [::sth::sthCore::invoke stc::get $last_host "-Name"]]} {
                        set port_address $last_host
                    }
                }
                switch -exact -- $userArray(arp_target) {
                    device {
                        set target $devices
                    }
                    stream {
                        set target $streams
                    }
                    port {
                        set target $port_address
                    }
                    all {
                        set target "$hosts $streams"
                    }
                }
                set arpResults ""
                if  {$target != ""} {
                    if {[catch {set arpResults [::sth::sthCore::invoke ::stc::perform ArpNdStart -HandleList "$target"]} err]} {
                        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log $err]
                        set cmdFailed 0
                        set arpResults "ArpNdState FAILURE"
                    }
                                    
                    if {[info exists userArray(arp_cache_retrieve)] && $userArray(arp_cache_retrieve)} {
                        if {[catch {::sth::sthCore::invoke ::stc::perform ArpNdUpdateArpCache -HandleList "$target"} err]} {}
                        set arpCacheData [::sth::sthCore::invoke stc::get $userArray(port_handle).ArpCache "-ArpCacheData"]
                        keylset interfaceConfKeyList arpnd_cache $arpCacheData
                    }
                    
                    if {[info exists userArray(arpnd_report_retrieve)] && $userArray(arpnd_report_retrieve)} {
                        set arpReport ""
                        set arpndReportHandle [::sth::sthCore::invoke stc::get $porthandlevalue -Children-ArpNdReport]
                        set arpndReportAttr "ArpNdStatus FailedArpNdCount SuccessfulArpNdCount AttemptedArpNdCount"
                        set arpndReportAttrName "arpnd_status failed_arpnd_count successful_arpnd_count attempted_arpnd_count"                    
                        foreach attr $arpndReportAttr attrName $arpndReportAttrName {
                            set arpStatus [::sth::sthCore::invoke stc::get $arpndReportHandle "-$attr"]
                            set arpReport [::sth::sthCore::updateReturnInfo $arpReport "$attrName" $arpStatus]
                        }
                        keylset interfaceConfKeyList arpnd_report $arpReport
                    }
    
                    if {[regexp -nocase "ArpNdState FAILURE" $arpResults]} {
                        keylset interfaceConfKeyList arpnd_status $::sth::sthCore::FAILURE
                        keylset returnKeyList arpnd_status $::sth::sthCore::FAILURE
        
                    } else {
                        keylset interfaceConfKeyList arpnd_status $::sth::sthCore::SUCCESS
                        keylset returnKeyList arpnd_status $::sth::sthCore::SUCCESS
        
                    }
                }
            }
        } elseif {[info exists hostHandle]} {
            ::sth::sthCore::invoke stc::delete $hostHandle
        }
        if {[::info exists cmdFailed]} {
            set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error: STC command Failure"]
            set cmdState 0
            keylset returnKeyList status $cmdState;
            return $returnKeyList
        } 
    }


    if {$cmdResult == 0} {
        set cmdFailed 0
        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Internal Command Error: Error occured while configuring ethernetcopper"]
        set cmdState 0
        keylset returnKeyList status $cmdState;
        return $returnKeyList
    } 
     
    if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
        set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "Unable to apply configuration: $applyStatus"]
        set cmdState 0
    } else {
        set cmdState 1
        
    }
    foreach sisterPort $::sth::Session::sisterPortList {
        ::sth::sthCore::invoke stc::delete $sisterPort
    }
    
    #wait till link come up
    set phyhandleLink [stc::get $porthandlevalue -children-Ethernet10GigCopper]
    if {$phyhandleLink != ""} {
    set upCnt 1
    set port_link_status [stc::get $phyhandleLink -LinkStatus]
        while {$port_link_status != "UP" && $upCnt<120} {
            set port_link_status [stc::get $phyhandleLink -LinkStatus]
            incr upCnt
            after 1000
        }
    }
    
    if {[info exists hostHandle]} {
        keylset returnKeyList handles $hostHandle;
    }
    keylset returnKeyList status $cmdState;
    return $returnKeyList
}

proc ::sth::Session::processDeleteCmd {porthandles } {
    upvar interfaceConfKeyList interfaceConfKeyList;
    
    ::sth::sthCore::log info "{Calling processDeleteCmd}"
    foreach portname $porthandles {
        if {[catch {::sth::sthCore::invoke stc::delete $portname} deleteStatus ]} {
            ::sth::sthCore::processError interfaceConfKeyList "Unable to delete Object with handle:$userArray(port_handle). Error: $deleteStatus" {}
            set interfaceConfKeyList [::sth::sthCore::updateReturnInfo $interfaceConfKeyList log "$userArray(port_handle): Internal Command Error while deleting "]        
            return $::sth::sthCore::FAILURE
        } else {
            ::sth::sthCore::log info "{The object with handle: $porthandles was successfully deleted}"
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::interface_config_destroy {modeValue} {
    variable ::sth::Session::PORTHNDLIST
    upvar 1 userArgsArray userArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    upvar interfaceConfKeyList interfaceConfKeyList;
    upvar 1 sortedSwitchPriorityList userSwitchPriorityList

    set _OrigHltCmdName "interface_config"
    set _hltCmdName "interface_config_destroy"
    set cmdState $::sth::sthCore::SUCCESS

    #this variable is not used for this sub command but keeping to see if this can be replaced by a single command.
    set handleSwitchName port_handle
    #set cmd "::sth::Session::processDeleteCmd"
    set portHndlist $userArray(port_handle)
    ######## the port handle must be verified before these statement #######
    foreach portHnd $portHndlist {
        if {[info exists ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($portHnd)]} {
            unset ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($portHnd)
        }   
        unset ::sth::Session::PORTLEVELARPSENDREQUEST($portHnd)
        unset ::sth::Session::PORTLEVELARPDONE($portHnd)
    }
    
    set cmdResult [::sth::Session::processDeleteCmd $userArray(port_handle)]
    #set cmdResult [eval $cmd $userArray(port_handle)]

    if {$cmdResult == 0} {
        set logStatus "$_hltCmdName: Error occured while configuring switch $switchName with Value $switchValue"
        ::sth::sthCore::processError interfaceConfKeyList "$logStatus: Internal Command Error while deleting " {}
        set cmdState $::sth::sthCore::FAILURE
        keylset returnKeyList status $cmdState;
        return $returnKeyList
    }
    
    foreach port $portHndlist {
        if {[info exists ::sth::Session::PORTHNDLIST($port)]} {
            set ::sth::Session::PORTHNDLIST(($port),0) $::sth::Session::PORTHNDLIST($port))
            catch {unset ::sth::Session::PORTHNDLIST($port)}
        }
    }
    
    keylset returnKeyList status $cmdState;
    return $returnKeyList
}

proc ::sth::Session::processCleanup_sessionPort_list {handle} {
    variable ::sth::Session::PORTHNDLIST
    upvar 1 userArgsArray userArray
    upvar cleanUpSessionKeyList cleanUpSessionKeyList;
    upvar 1 sortedSwitchPriorityList userSwitchPriorityList
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::GBLHNDMAP
    
    ::sth::traffic_config -mode reset
    
    # fix CR 323427703
    if {([string equal $handle "all"])} {
        if {[catch {::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) "-children-port"} portlist]} {
            ::sth::sthCore::processError cleanUpSessionKeyList "Internal Command Error while getting ports: $porthandlelistnew" {}
            return -code 1 -errorcode -1 $portlist;
        } 
    } else {
        set portlist $handle
    }
    
    foreach portHnd $portlist {
        ######### Valid port handle must be passed over here ######
        if {[info exists ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($portHnd)]} {
            unset ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($portHnd)
        }
        if {[info exists ::sth::Session::PORTLEVELARPSENDREQUEST($portHnd)]} {
            unset ::sth::Session::PORTLEVELARPSENDREQUEST($portHnd)
        }
        if {[info exists ::sth::Session::PORTLEVELARPDONE($portHnd)]} {
            unset ::sth::Session::PORTLEVELARPDONE($portHnd)
        }

        if {[::info exists ::sth::Session::PORTHNDLIST($portHnd)]} {
            # add for CR 287690340 cleanup_session will produce error if connecting offline port
            if {[catch {set online_state [::sth::sthCore::invoke stc::get $portHnd -online]} eMsg]} {
                ::sth::sthCore::processError cleanUpSessionKeyList "Error get $portHnd online state: $eMsg" {}
                    return $::sth::sthCore::FAILURE
            }
            if {$online_state} {
                if {![info exists userArray(maintain_lock)] || ([info exists userArray(maintain_lock)] && $userArray(maintain_lock) ==0)} {
                    if {[catch {::sth::sthCore::invoke "stclib::bll::release $::sth::Session::PORTHNDLIST($portHnd)"} releaseStatus ]} {
                     ::sth::sthCore::processError cleanUpSessionKeyList "Unable to release ports:$::sth::Session::PORTHNDLIST($portHnd): $releaseStatus" {}
                     catch {unset ::sth::Session::PORTHNDLIST($portHnd)}
                     return $::sth::sthCore::FAILURE
                    } else {
                       catch {unset ::sth::Session::PORTHNDLIST($portHnd)}
                    }  
                }
                
            } else {
                catch {unset ::sth::Session::PORTHNDLIST($portHnd)}
            }
            
            if {[catch {::sth::sthCore::invoke stc::delete $portHnd} eMsg ]} {
                        ::sth::sthCore::processError cleanUpSessionKeyList "Error deleting $portHnd: $eMsg" {}
                        return $::sth::sthCore::FAILURE
            } else {
                    catch {unset ::sth::Session::PORTHNDLIST($portHnd)}
            }
        } else {
            #Check if this port is destroyed by used using Interface_config
            if {[::info exists ::sth::Session::PORTHNDLIST($portHnd,0)]} {
                #Found the port handle. It was destroyed before. Release the port. 
                if {[catch {::sth::sthCore::invoke "stclib::bll::release $::sth::Session::PORTHNDLIST($portHnd,0)"} releaseStatus ]} {
                    ::sth::sthCore::processError cleanUpSessionKeyList "Error Releasing port $portHnd: $releaseStatus" {}
                        catch {unset ::sth::Session::PORTHNDLIST($portHnd,0)}
                    return $::sth::sthCore::FAILURE
                } else {
                    catch {unset ::sth::Session::PORTHNDLIST($portHnd,0)}
                }
            } 
        }
    }

    if {([array exists ::sth::Session::PORTHNDLIST]) && ([array size ::sth::Session::PORTHNDLIST] > 0)} {
    } else {
        set chassislist [::sth::Session::getPhysicalChassis]
        foreach chassis $chassislist {
            set chassisip [::sth::sthCore::invoke stc::get $chassis -Hostname]
            if {![info exists userArray(maintain_lock)] || ([info exists userArray(maintain_lock)] && $userArray(maintain_lock) ==0)} {
                if {[info exists ::sth::Session::CHASSISID2DEVICEMAP($chassisip)]} {
                    if {[catch {::sth::sthCore::invoke "stc::disconnect $chassisip"} disconnectStatus ]} {
                       ::sth::sthCore::processError cleanUpSessionKeyList "Unable to disconnect chassis: $disconnectStatus" {}
                       return $::sth::sthCore::FAILURE
                    }
                }  
            }  
        }
    }

    if {[::info exists cmdFailed]} {
            return $::sth::sthCore::FAILURE
    } else {
        return $::sth::sthCore::SUCCESS
    }    

}

proc ::sth::Session::processInfoFspec_version {  } {
    upvar deviceinfoSessionKeyList deviceinfoSessionKeyList;
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    set _STC_VERSION 2.00
    set _HLT_VERSION 5.50
   
    set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList fspec_version "HLTAPI_$_HLT_VERSION\_STC_$_STC_VERSION"]
    return $::sth::sthCore::SUCCESS
}


proc ::sth::Session::getPhysicalChassisManager {} {
    set ret [::sth::sthCore::invoke stc::get system1 "-children-physicalchassismanager"]
    return $ret
}

proc ::sth::Session::getPhysicalChassis {} {
    set mgr [::sth::Session::getPhysicalChassisManager]
    set ret [::sth::sthCore::invoke stc::get $mgr "-children-physicalchassis"]
    return $ret
}

proc ::sth::Session::getPhysicalTestModules {chassisHandle} {
    set ret [::sth::sthCore::invoke stc::get $chassisHandle "-children-physicaltestmodule" ]
    return $ret
}

proc ::sth::Session::getPhysicalPortGroups {tmHandle} {
    set ret [::sth::sthCore::invoke stc::get $tmHandle "-children-physicalportgroup"]
    return $ret
}

proc ::sth::Session::getPhysicalPorts {portGroupHandle} {
    set ret [::sth::sthCore::invoke stc::get $portGroupHandle "-children-physicalport"]
    return $ret
}

proc ::sth::Session::processdeviceInfoPortHandle { } {
    upvar 1 userArgsArray userArray
    upvar deviceinfoSessionKeyList deviceinfoSessionKeyList;
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS

    if {([info exists userArray(port_handle)]) && ([llength $userArray(port_handle)] > 0)} {
        set portlist $userArray(port_handle)
        
        foreach portHnd $portlist {
            #array set out [stc::get $portHndlName]
            #array set output [stc::perform PortSetupGetActivePhy -port $portHndlName]
            #set activePhyState "$output(-ActivePhy)"
            #set portName "$output(-Port)"
            set portname [::sth::sthCore::invoke stc::get $portHnd -name]
            set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList port_handle.$portHnd.port_name "$portname"]
        }
    }
    
    return $::sth::sthCore::SUCCESS

}
proc ::sth::Session::processPhysicalPortInfo {porthndlist} {
    variable ::sth::Session::PORTHNDLIST
    upvar phyPortinfoSessionKeyList phyPortinfoSessionKeyList;
    
    set porthndliststr ""
    foreach porthnd $porthndlist {
        lappend porthndliststr "//$::sth::Session::PORTHNDLIST($porthnd)"
    }
    
    set chassislist [::sth::Session::getPhysicalChassis]
    foreach chassis $chassislist {
        set chassisip [::sth::sthCore::invoke stc::get $chassis -Hostname]
        set moduleHandles [::sth::Session::getPhysicalTestModules $chassis]
        foreach module $moduleHandles {
                set slotindex [::sth::sthCore::invoke stc::get $module -Index]
                set portGroupHandles [::sth::Session::getPhysicalPortGroups $module]
                foreach portGroup $portGroupHandles {
                        set portgroupindex [::sth::sthCore::invoke stc::get $portGroup -Index]
                            set portobjectlist [::sth::Session::getPhysicalPorts $portGroup]
                            foreach phyport $portobjectlist {
                                set loc [::sth::sthCore::invoke stc::get $phyport -location];
                                if  {[regexp -nocase $loc $porthndliststr]} {
                                    lappend phyPortinfoSessionKeyList $phyport;
                                }
                            }
                }
        }
    }
    
    return $phyPortinfoSessionKeyList
}

proc ::sth::Session::processdeviceInfo { } {
    upvar deviceinfoSessionKeyList deviceinfoSessionKeyList;
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    set cmdResult 0
    
    set chassislist [::sth::Session::getPhysicalChassis]
    foreach chassis $chassislist {
        set chassisip [::sth::sthCore::invoke stc::get $chassis -Hostname]
        set moduleHandles [::sth::Session::getPhysicalTestModules $chassis]
        foreach module $moduleHandles {
                set slotindex [::sth::sthCore::invoke stc::get $module -Index]
                set portGroupHandles [::sth::Session::getPhysicalPortGroups $module]
                foreach portGroup $portGroupHandles {
                        set portgroupindex [::sth::sthCore::invoke stc::get $portGroup -Index]
                            set portobjectlist [::sth::Session::getPhysicalPorts $portGroup]
                            foreach port $portobjectlist {
                                    set portindex [::sth::sthCore::invoke stc::get $port -Index]
                                set ownershipstate [::sth::sthCore::invoke stc::get $portGroup -OwnershipState]
                                set owneruserid [::sth::sthCore::invoke stc::get $portGroup -OwnerUserId]

                                switch -exact -- $ownershipstate {
                                           
                                        OWNERSHIP_STATE_RESERVED {
                                                set reservedbywho [::sth::sthCore::invoke stc::get $portGroup -ReservedByUser]
                                                if {$reservedbywho == "true" }  {
                                                    set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList "$chassisip.inuse.$slotindex/$portindex.owner" $owneruserid]
                                                    set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList "$chassisip.inuse.$slotindex/$portindex.type" ethernet]
                                                    set cmdResult 1
                                                } else {
                                                    set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList "$chassisip.inuse.$slotindex/$portindex.owner" $owneruserid]
                                                    set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList "$chassisip.inuse.$slotindex/$portindex.type" ethernet]
                                                    set cmdResult 1
                                                }
                                        }
                                        OWNERSHIP_STATE_AVAILABLE {   
                                            set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList "$chassisip.available.$slotindex/$portindex.type" ethernet]
                                            set cmdResult 1
                                        }
                                        OWNERSHIP_STATE_DISCONNECTED {
                                            set cmdResult 1
                                        }
                                    default {
                                            set deviceinfoSessionKeyList [::sth::sthCore::updateReturnInfo $deviceinfoSessionKeyList log "Unknown Value for ownerShipState Port:$portindex , Slot:$i on device: $chassisip"]
                                            set cmdResult 1
                                            
                                    }
                                }
                            }
                }
            }
        }
        if {$cmdResult == 1} {
                return $::sth::sthCore::SUCCESS
        } else {
                return $::sth::sthCore::FAILURE
        }
}


proc ::sth::Session::getAnalyzerCountersForPort { statsSpeed porthandleValue anaresult_keys} {   
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList
    
    if {$anaresult_keys == "_none_"} {
        return;
    }
    
    set analyzerhndl  [::sth::sthCore::invoke stc::get $porthandleValue -children-Analyzer]
    set analyzerResult1 [::sth::sthCore::invoke stc::get $analyzerhndl -children-analyzerportresults]
    array set ::sth::Session::interface_stats_Analyzer_$statsSpeed {}
    set arrayName ::sth::Session::interface_stats_Analyzer_$statsSpeed;
    if {$anaresult_keys != "" } {
        set retInterfaceStatsList $anaresult_keys
    } else {
        set retInterfaceStatsList [array names ::sth::Session::interface_stats_Analyzer_$statsSpeed];
    }

    set stclist [::sth::sthCore::invoke stc::get $analyzerResult1]
    array set stcArray $stclist;
    foreach ele $retInterfaceStatsList {
        set hltname $ele  
        set val ::sth::Session::interface_stats_procfunc
        set myFunc [set $val\($hltname)]
        if {$myFunc == "_none_"} {
            set stcValue [set $arrayName\($ele)];
            if {$stcValue == "_none_"} {
            } else {
                set stcValue -$stcValue 
                set stcReturnValue $stcArray($stcValue)
                set interfaceStatsKeyList [::sth::sthCore::updateReturnInfo $interfaceStatsKeyList $hltname "$stcReturnValue"]
            }
        } else {
            set cmdResult [eval $myFunc]
        }
    }
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::getSystemMonitor {sysmonitorresult_keys} {   
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList

    set waitInterval 1
    set maxWaitTime 10
    set totalWaitTime 0
    while { $totalWaitTime < $maxWaitTime } {
        set systemMonitorResultsList [::sth::sthCore::invoke stc::get $::sth::Traffic::systemMonitorDataset -ResultHandleList]
        if { $systemMonitorResultsList == "" } {
            ::sth::sthCore::invoke stc::sleep $waitInterval
            set totalWaitTime [expr $totalWaitTime + $waitInterval]
        } else {
            break
        }
    }
    set arrayName ::sth::Traffic::traffic_stats_system_monitor_results_stcattr;
    set retInterfaceStatsList [array names $arrayName]

    foreach systemMonitorResults $systemMonitorResultsList {
        set stclist [::sth::sthCore::invoke stc::get $systemMonitorResults]
        set daemonName [::sth::sthCore::invoke stc::get $systemMonitorResults -DaemonName]
        array set stcArray $stclist;
        foreach ele $retInterfaceStatsList {
            set hltname $ele  
            set stcValue [set $arrayName\($ele)];
            if {$stcValue == "_none_"} {
            } else {
                set stcValue -$stcValue 
                set stcReturnValue $stcArray($stcValue)
                set interfaceStatsKeyList [::sth::sthCore::updateReturnInfo $interfaceStatsKeyList $daemonName.$hltname "$stcReturnValue"]
            }
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::createIntStatsList {type statsSpeed properties} {  
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList
    set interfaceStatsList ""
    set statsList $properties

    if {$type == "aggregate_txjoin"} {
        array set ::sth::Session::interface_stats_eotGenerator_$statsSpeed {}
        set arrayName ::sth::Session::interface_stats_eotGenerator_$statsSpeed;
        if {$properties == ""} {
            set statsList [array names ::sth::Session::interface_stats_eotGenerator_$statsSpeed];
        }
    } else {
        array set ::sth::Session::interface_stats_eotAnalyzer_$statsSpeed {}
        set arrayName ::sth::Session::interface_stats_eotAnalyzer_$statsSpeed;
        if {$properties == ""} {
            set statsList [array names ::sth::Session::interface_stats_eotAnalyzer_$statsSpeed];
        }
    }
    foreach ele $statsList {
        set hltname $ele
        set stcName [set $arrayName\($ele)];
        if {$stcName != "_none_"} {
            lappend interfaceStatsList $stcName;
        }
    }   
    
    return $interfaceStatsList
}

proc ::sth::Session::getEOTCountersForPort { statsSpeed porthandleValue anaresult_keys genresult_keys} { 
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList
    
    
    set typelist {"aggregate_rxjoin" "aggregate_txjoin"}
    foreach type $typelist {
        set properties ""
        if {$type == "aggregate_rxjoin"} {
            ::sth::Session::processInterfaceStats_GetEOTResults $type $statsSpeed $porthandleValue $anaresult_keys
            set properties $anaresult_keys
        } else {
            ::sth::Session::processInterfaceStats_GetEOTResults $type $statsSpeed $porthandleValue $genresult_keys
            set properties $genresult_keys
        }
        if {$sth::Traffic::eotPortQueryEmpty == 1} {
            return
        }

        if {$properties == "_none_" } {
            continue
        }

        if {$type == "aggregate_txjoin"} {
            array set ::sth::Session::interface_stats_eotGenerator_$statsSpeed {}
            set arrayName ::sth::Session::interface_stats_eotGenerator_$statsSpeed;
            if {$genresult_keys == "" } {
                set retInterfaceStatsList [array names ::sth::Session::interface_stats_eotGenerator_$statsSpeed];
            } else {
                set retInterfaceStatsList $genresult_keys;
            }
        } else {
            array set ::sth::Session::interface_stats_eotAnalyzer_$statsSpeed {}
            set arrayName ::sth::Session::interface_stats_eotAnalyzer_$statsSpeed;
            if {$anaresult_keys == "" } {
                set retInterfaceStatsList [array names ::sth::Session::interface_stats_eotAnalyzer_$statsSpeed];
            } else {
                set retInterfaceStatsList $anaresult_keys;
            }
        }
        foreach ele $retInterfaceStatsList {
            set hltname $ele  
            set val ::sth::Session::interface_stats_procfunc
            set myFunc [set $val\($hltname)]
            if {$myFunc == "_none_"} {
                set stcValue [set $arrayName\($ele)];
                if {$stcValue != "_none_"} {
                    set stcReturnValue $::sth::Traffic::arraySTCArray($stcValue)
                    set interfaceStatsKeyList [::sth::sthCore::updateReturnInfo $interfaceStatsKeyList $hltname "$stcReturnValue"]
                }
            } else {
                set cmdResult [eval $myFunc]
            }
        } 
    }
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::getGeneratorCountersForPort { statsSpeed porthandleValue genresult_keys} {  
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList
    
    if {$genresult_keys == "_none_"} {
        return;
    }
    
    set generatorhndl [::sth::sthCore::invoke stc::get $porthandleValue -children-generator]
    set generatorResult1 [::sth::sthCore::invoke stc::get $generatorhndl -children-generatorportresults]
    array set ::sth::Session::interface_stats_Generator_$statsSpeed {}
    set arrayName ::sth::Session::interface_stats_Generator_$statsSpeed;

    if {$genresult_keys != "" } {
        set retInterfaceStatsList $genresult_keys
    } else {
        set retInterfaceStatsList [array names ::sth::Session::interface_stats_Generator_$statsSpeed];
    }
    
    #::sth::sthCore::log debug "$retInterfaceStatsList";
    set stclist [::sth::sthCore::invoke stc::get $generatorResult1]
    array set stcArray $stclist;
    foreach ele $retInterfaceStatsList {
        set hltname $ele
        set val ::sth::Session::interface_stats_procfunc
        set myFunc [set $val\($hltname)]
        if {$myFunc == "_none_"} {
            set stcValue [set $arrayName\($ele)];
            if {$stcValue == "_none_"} {
            } else {
                set stcValue -$stcValue
                set stcReturnValue $stcArray($stcValue)
                set interfaceStatsKeyList [::sth::sthCore::updateReturnInfo $interfaceStatsKeyList $hltname "$stcReturnValue"]
            }
        } else {
            set cmdResult [eval $myFunc]
        } 
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::getFCResultForPort { statsSpeed porthandleValue fcresult_keys} {  
    variable ::sth::sthCore::GBLHNDMAP
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList
    
    if {$fcresult_keys == "_none_"} {
        return;
    }
    
    set fcResult1 [::sth::sthCore::invoke stc::get $porthandleValue -children-fcresults]
    if {$fcResult1 != ""} {    
        if {$fcresult_keys != "" } {
            set retInterfaceStatsList $fcresult_keys
        } else {
            set TableName ::sth::Traffic::traffic_stats_fc_port_results_stcattr
            set retInterfaceStatsList  [array names $TableName]
        }
    
        #::sth::sthCore::log debug "$retInterfaceStatsList";
        set stclist [::sth::sthCore::invoke stc::get $fcResult1]
        array set stcArray $stclist;
        foreach ele $retInterfaceStatsList {
            set hltname $ele
            set myVar "::sth::Traffic::traffic_stats_fc_port_results_stcattr"
            set stcName -[set $myVar\($ele)];
            if {![catch {set stcReturnValue $stcArray($stcName)} err]} {
                set interfaceStatsKeyList [::sth::sthCore::updateReturnInfo $interfaceStatsKeyList $hltname "$stcReturnValue"]
            }
        }
    }
    
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Session::processInterfaceStats_GetEOTResults {type speed porthandlevalue properties} {
    upvar interfaceStatsKeyedList interfaceStatsKeyedList;
    upvar userArgsArray userArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    variable ::sth::sthCore::GBLHNDMAP
    set ::sth::Session::isEotIntStats 1
    
    if {$properties == "_none_"} {
        return;
    }
    
    #if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
    #    load tclsqlite3
    #} else {
    #    load libtclsqlite3.so
    #}
    
    #sqlite3 db [file join $::sth::Traffic::hltDir eotResultsHltApi.db]
    #rxu
    if {$::sth::Traffic::EOTResultsFileName != ""} {
        sqlite3 db [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
    } else {
        ::sth::sthCore::processError trafficStatsKeyedList "EOTResults db file name is null, can not open EOTResults DataBase" {}
        return $::sth::sthCore::FAILURE;
    }
    
    
    set userlist $porthandlevalue
    set viewEotlist [::sth::Session::createIntStatsList $type $speed $properties]

    set attrList $viewEotlist

    
    
    set formattedList ""
    foreach userInout $userlist {
            lappend formattedList '$userInout',
    }
    set formattedqueryList ""
    set len2 [llength $attrList]
    set i 0
    foreach attr $attrList {
        incr i
        if {$i == $len2} {
            lappend formattedqueryList $attr
        } else {
            lappend formattedqueryList $attr,
        }
    }
    ::sth::Traffic::processGetAggQuery $type $len2 $userlist $attrList $formattedList $formattedqueryList $properties
    
    #close the db file (fix CR297414265)
    db close [file join $::sth::Traffic::hltDir $::sth::Traffic::EOTResultsFileName]
    
    return 

}


proc ::sth::Session::getStatsVarsFromTable { porthandleValue } { 
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    upvar interfaceStatsKeyList interfaceStatsKeyList
    upvar userArgsArray usrArgsArray;
    variable ::sth::sthCore::objecttype
    
    set sth::Session::intStats 1
    
    array set out [::sth::sthCore::invoke stc::get $porthandleValue]
    array set output [::sth::sthCore::invoke stc::perform PortSetupGetActivePhy -port $porthandleValue]
    set activePhyState "$output(-ActivePhy)"
    set portName "$output(-Port)"
    if {[regexp posphy $activePhyState] || [regexp atmphy $activePhyState]} {
        set SonetConfig [lindex [::sth::sthCore::invoke stc::get $activePhyState -children-SonetConfig] 0]
        set liSpeed [::sth::sthCore::invoke stc::get $SonetConfig "-linespeed"]
    } else {
        set liSpeed [::sth::sthCore::invoke stc::get $output(-ActivePhy) "-linespeed"]
    }
    set liStatus [::sth::sthCore::invoke stc::get $output(-ActivePhy) "-LinkStatus"]
    if {[info exists usrArgsArray(phy_mode)]} {
        if {([string equal $usrArgsArray(phy_mode) "copper"]) || ([string equal $usrArgsArray(phy_mode) "Copper"])} {
            set duplexStatus [::sth::sthCore::invoke stc::get $output(-ActivePhy) "-Duplex"]
        } else {
            set duplexStatus "not_supported"
        }
    } else {
        if {([regexp fcphy $activePhyState] ||[regexp fiber $activePhyState]) || ([regexp posphy $activePhyState] || [regexp atmphy $activePhyState])} {
            set duplexStatus "not_supported"
        } else {
            set duplexStatus [::sth::sthCore::invoke stc::get $output(-ActivePhy) "-Duplex"]
        }
    }
    
    
    if {[catch {::sth::sthCore::invoke stc::get $porthandleValue -children-ethiiif} ethhndl]} {
        ::sth::sthCore::processError connectKeyedList "stc::get Failed: Error getting ethiif handle for stats: $ethhndl" {}
        return $::sth::sthCore::FAILURE
    }
    if {[llength $ethhndl] != 0} {
        set stcMacAddr [::sth::sthCore::invoke stc::get $ethhndl -SourceMac]
        #if {[catch {stc::get $ethhndl -children -SourceMac} stcMacAddr]} {
        #    ::sth::sthCore::processError connectKeyedList "stc::get Failed: Error getting source mac from address for stats: $stcMacAddr" {}
        #    set connectKeyedList [::sth::sthCore::updateReturnInfo $connectKeyedList log "internal command error while getting source mac from address for stats"]
        #    return $::sth::sthCore::FAILURE
        #}
        set macaddr [::sth::Session::covertStcMacToHltMacFormat $stcMacAddr]
    } else {
        set macaddr "_none_"
    }
   
    
    set physicalPort [::sth::sthCore::invoke stc::get $porthandleValue -physicallogical-sources]
    set physicalportgroup [::sth::sthCore::invoke stc::get $physicalPort -parent]
    set physicalcard [::sth::sthCore::invoke stc::get $physicalportgroup -parent]
    set cardname [::sth::sthCore::invoke stc::get $physicalcard -Model]
    
    switch -exact -- $liSpeed \
        SPEED_10M {
            set statsSpeed "10100"
            set hltSpeed "10"
        }\
        SPEED_100M {
            set statsSpeed "10100"
            set hltSpeed "100"
        }\
        SPEED_1G {
            set statsSpeed "gbic"
            set hltSpeed "1000"
        }\
        SPEED_10G {
            set statsSpeed "10gbic"
            set hltSpeed "10000"
        }\
        SPEED_100G {
            set statsSpeed "100gbic"
            set hltSpeed "100000"
        }\
        SPEED_16G {
            set statsSpeed "16gbic"
            set hltSpeed "fc"
        }\
        SPEED_32G {
            set statsSpeed "32gbic"
            set hltSpeed "fc"
        }\
        SPEED_40G {
            set statsSpeed "40gbic"
            set hltSpeed "40000"
        }\
        SPEED_9_286G {
            set statsSpeed "9_286gbic"
            set hltSpeed "9_286000"
        }\
        OC3 {
            set statsSpeed "ocPOS"
            set hltSpeed "oc3"
        }\
        OC12 {
            set statsSpeed "ocPOS"
            set hltSpeed "oc12"
        }\
        OC48 {
            set statsSpeed "ocPOS"
            set hltSpeed "oc48"
        }\
        OC192 {
            set statsSpeed "ocPOS"
            set hltSpeed "oc192"
        }\
        default {
            return $::sth::sthCore::FAILURE
        }
        
        #Get the list of common switches
        array set ::sth::Session::interface_stats_commonArray {}
        set retInterfaceStatsCommonList [array names ::sth::Session::interface_stats_commonArray];
        foreach ele $retInterfaceStatsCommonList {
            set hltname $ele
            if {$hltname == "port_name"} {
                set stcReturnValue $portName
            } elseif {$hltname == "intf_speed"} {
                set stcReturnValue $hltSpeed
            } elseif {$hltname == "link"} {
				set stcReturnValue $liStatus
                if {$liStatus == "UP"} {
                    set stcReturnValue 1
                } elseif {$liStatus == "DOWN" || $liStatus == "ADMIN_DOWN"} {
                    set stcReturnValue 0
                }
            } elseif {$hltname == "duplex"} {
                set stcReturnValue $duplexStatus
                if {$duplexStatus == "FULL"} {
                    set stcReturnValue "full"
                } elseif {$duplexStatus == "HALF"} {
                    set stcReturnValue "half"
                } elseif {$duplexStatus == "not_supported"} {
                    set stcReturnValue "not_supported"
                }
            } elseif {$hltname == "intf_type"} {
                #need to add support later when available
                #Hard coded for now
                #fixed by Fei Cheng. 2008-7-11
                switch -regexp -- $activePhyState {
                  {posphy} {
                    set stcReturnValue "pos"
                  }
                  {atmphy} {
                    set stcReturnValue "ATM"
                  }
                  {ethernet} {
                     set stcReturnValue "ethernet"
                  }
                  {fcphy} {
                     set stcReturnValue "fc"
                  }
                  default {
                    set stcReturnValue "ethernet"
                  }
                }
            } elseif {$hltname == "mac_address"} {
                set stcReturnValue $macaddr
            } elseif {$hltname == "card_name"} {
                set stcReturnValue $cardname
            }
            set interfaceStatsKeyList [::sth::sthCore::updateReturnInfo $interfaceStatsKeyList $hltname "$stcReturnValue"]
        }
        
        ######################end
        set genresult_keys ""
        set anaresult_keys ""
        set fcresult_keys ""
        set sysmonitorresult_keys ""
        
        if {[info exists usrArgsArray(properties)]} {
            set genresult_keys [sth::Traffic::getTypeProperties gen $usrArgsArray(properties)]
            set anaresult_keys [sth::Traffic::getTypeProperties ana $usrArgsArray(properties)]
            set fcresult_keys [sth::Traffic::getTypeProperties fc $usrArgsArray(properties)]
            if {$genresult_keys == ""} {
                set genresult_keys "_none_"
            }
            if {$anaresult_keys == ""} {
                set anaresult_keys "_none_"
            }
            
            if {$fcresult_keys == ""} {
                set fcresult_keys "_none_"
            }
        }

        if {$sth::Traffic::isEOTResults == 0} {
            set status [::sth::Session::getAnalyzerCountersForPort $statsSpeed $porthandleValue $anaresult_keys]
            set status [::sth::Session::getGeneratorCountersForPort $statsSpeed $porthandleValue $genresult_keys]
            set status [::sth::Session::getFCResultForPort $statsSpeed $porthandleValue $fcresult_keys]
            if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                set status [::sth::Session::getSystemMonitor $sysmonitorresult_keys]
            }
        } else {
            if {$sth::Traffic::EOTResultsFileName == ""} {
                set status [::sth::Session::getAnalyzerCountersForPort $statsSpeed $porthandleValue $anaresult_keys]
                set status [::sth::Session::getGeneratorCountersForPort $statsSpeed $porthandleValue $genresult_keys]
                set status [::sth::Session::getFCResultForPort $statsSpeed $porthandleValue $fcresult_keys]
                if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                    set status [::sth::Session::getSystemMonitor $sysmonitorresult_keys]
                }
            } else {
                set status [::sth::Session::getEOTCountersForPort $statsSpeed $porthandleValue $anaresult_keys $genresult_keys]
                if {[info exists ::sth::Traffic::systemMonitorResultsFlag] && $::sth::Traffic::systemMonitorResultsFlag == 1} {
                    set status [::sth::Session::getSystemMonitor $sysmonitorresult_keys]
                }
            #set status [::sth::Session::getEotGeneratorCountersForPort $statsSpeed $porthandleValue]
            }
        }

}

proc ::sth::Session::processConfigArpCmd { switchValue switchName  portHandle } {
     set projectHandle [::sth::sthCore::invoke ::stc::get $portHandle -parent]
     set ArpNdConfigHandle [::sth::sthCore::invoke ::stc::get $projectHandle -children-arpndconfig]
     
     ###### Assume that the arp_req_timer is in milli-seconds.
     if { $switchName == "arp_req_timer" } {
         ::sth::sthCore::invoke ::stc::config $ArpNdConfigHandle -learningrate [expr { 1000 / $switchValue}]
     }

     if { $switchName == "arp_req_retries" } {
         ::sth::sthCore::invoke ::stc::config $ArpNdConfigHandle -RetryCount $switchValue
     }
    
    if { $switchName == "arp_req_timeout" } {
        ::sth::sthCore::invoke ::stc::config $ArpNdConfigHandle -TimeOut $switchValue
    }     

    return $::sth::sthCore::SUCCESS    
}

# pfc 
proc ::sth::Session::processConfigPfcCmd { switchValue switchName portHandle } {
    upvar 1 userArray userArgsArray
    upvar stcattr stcattr
    upvar stcattrvalue stcattrvalue
    ::sth::sthCore::log info "{Calling processConfigPfcCmd}"
    
    if {$switchName == "pfc_negotiate_by_dcbx"} {
        set stcattr "IsPfcNegotiated"
        set stcattrvalue $switchValue
    } elseif {$switchName == "priority0" || $switchName == "priority1" || $switchName == "priority2" || $switchName == "priority3"
        || $switchName == "priority4" || $switchName == "priority5" || $switchName == "priority6" || $switchName == "priority7"} {
        if {[info exist ::sth::Session::pfcFlag($portHandle)] && $::sth::Session::pfcFlag($portHandle) == 1} {
            set stcattr ""
            set stcattrvalue ""
            return $::sth::sthCore::SUCCESS   
        }
        if {[info exists userArgsArray(pfc_negotiate_by_dcbx)] && $userArgsArray(pfc_negotiate_by_dcbx) == 0} {
            foreach item {priority0 priority1 priority2 priority3 priority4 priority5 priority6 priority7} {
                set $item  $userArgsArray($item)
            }
            set pfcArray "$priority0 $priority1 $priority2 $priority3 $priority4 $priority5 $priority6 $priority7"
            set stcattr "PriorityFlowControlArray"
            set stcattrvalue $pfcArray
            set ::sth::Session::pfcFlag($portHandle) 1
        }
    } elseif {$switchName == "pfc_priority_pause_quanta"} {
        # pfc measurement
        set value ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcattr
        set stcattr [set $value\($switchName)]
        set stcattrvalue ""
        foreach pause_quanta $switchValue {
            if {$pause_quanta < 0} {
                lappend stcattrvalue 0
            } elseif {$pause_quanta > 65535} {
                lappend stcattrvalue 65535
            } else {
                lappend stcattrvalue $pause_quanta
            }
        }
    } elseif {$switchName == "pfc_priority_enable"} { 
        # pfc measurement
        set value ::sth::Session::interface_config_$::sth::sthCore::objecttype\_stcattr
        set stcattr [set $value\($switchName)]
        
        foreach prienable $switchValue {
            if { ![string equal -nocase $prienable "true"] && ![string equal -nocase $prienable "false"] } {
                ::sth::sthCore::processErrorSub "Error while setting pfc_priority_enable, $prienable found, should be true or false"
            }
        }
        set stcattrvalue $switchValue
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc ::sth::Session::interface_control_break_link {userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "interface_control"
    set _hltCmdName "interface_control_break_link"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        port "Port"
    }
    
    foreach obj [array names objArr] {
        set handles $::sth::Session::interface_control_input_and_default_args_array(port_handle)
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform L2TestBreakLink -port $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while L2TestBreakLink $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Session::interface_control_restore_link {userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "interface_control"
    set _hltCmdName "interface_control_restore_link"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        port "Port"
    }
    
    foreach obj [array names objArr] {
        set handles $::sth::Session::interface_control_input_and_default_args_array(port_handle)
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform L2TestRestoreLink -port $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while L2TestRestoreLink $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Session::interface_control_pfc_response_time {userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "interface_control"
    set _hltCmdName "interface_control_pfc_response_time"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        port "Port"
    }
    
    foreach obj [array names objArr] {
        set handles $::sth::Session::interface_control_input_and_default_args_array(port_handle)
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform PfcMeasureResponseTime -portlist $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while PfcMeasureResponseTime $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Session::interface_control_restart_autonegotiation {userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "interface_control"
    set _hltCmdName "interface_control_restart_autonegotiation"
    
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    array set objArr {
        port "Port"
    }
    
    foreach obj [array names objArr] {
        set handles $::sth::Session::interface_control_input_and_default_args_array(port_handle)
        
        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            
        }
        
        if {[catch {::sth::sthCore::invoke stc::perform PortSetupRestartAutoNegotiation -portlist $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while PortSetupRestartAutoNegotiation $handles. Error: $eMsg"           
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Session::interface_control_enable_monitor {userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "interface_control"
    set _hltCmdName "interface_control_enable_monitor"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    array set objArr {
        port "Port"
    }

    foreach obj [array names objArr] {
        set handles $::sth::Session::interface_control_input_and_default_args_array(port_handle)

        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
            set location [::sth::sthCore::invoke stc::get $handle -location]
            lappend ports $location
        }
        set physicalPortGroupList [::stclib::bll::getPortGroupsForCspList $ports]
    }
    if {[catch {::sth::sthCore::invoke stc::perform configuresystemmonitorcommand -EnableMonitor 1 -PortGroupHandleList $physicalPortGroupList} eMsg]} {
        ::sth::sthCore::processErrorSub "Internal Command Error while EnableMonitor $handles. Error: $eMsg"           
    }
    set ::sth::Traffic::systemMonitorResultsFlag 1
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Session::interface_control_disable_monitor {userInput returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "interface_control"
    set _hltCmdName "interface_control_disable_monitor"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set args $userInput
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    array set objArr {
        port "Port"
    }

    foreach obj [array names objArr] {
        set handles $::sth::Session::interface_control_input_and_default_args_array(port_handle)

        foreach handle $handles {
            set objType $objArr($obj)
            ::sth::sthCore::isHandleValid $handle $objType
        }

        if {[catch {::sth::sthCore::invoke stc::perform configuresystemmonitorcommand -EnableMonitor 0 -PortGroupHandleList $handles} eMsg]} {
            ::sth::sthCore::processErrorSub "Internal Command Error while EnableMonitor $handles. Error: $eMsg"           
        }
    }
    set ::sth::Traffic::systemMonitorResultsFlag 0
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Session::condition_device_port {deviceparent namecondition portcondition} {
    set rootlist ""
	if {$deviceparent ne "port"} {          
        set devicelist [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-$deviceparent]

        foreach item $devicelist {
            set name [::sth::sthCore::invoke stc::get $item -name]
            if {[regexp $item $namecondition] || [regexp $name $namecondition]} {
                if {$portcondition eq ""} {
                    lappend rootlist $item
                } else {
                    set port [::sth::sthCore::invoke stc::get $item -affiliationport-targets]
                    if {[regexp $port $portcondition]} {
                        lappend rootlist $item
                        continue
                    }
                }
            }
            
            if {$portcondition ne ""} {
                set port [::sth::sthCore::invoke stc::get $item -affiliationport-targets]
                if {[regexp $port $portcondition]} {
                    lappend rootlist $item
                    continue
                }
            }
        }
    }
        
    return $rootlist
}

proc ::sth::Session::getobjects_from {deviceflag classarray portcondition {rootlist ""}} {
        set returnKeyedList ""
        set clsarray [::sth::sthCore::lreverse_local [split $classarray ","]]
        if {[info exists rootlist] && $rootlist ne ""} {
            if {[regexp {\{|\}} $rootlist]} {
                regsub -all {\{|\}} $rootlist "" rootlist
            }
            set root [split $rootlist  " "]
            foreach item $root {
                ::sth::Session::sortHandles $returnKeyedList $portcondition $deviceflag $clsarray $item
            }
        } else {
            ::sth::Session::sortHandles $returnKeyedList $portcondition $deviceflag $clsarray $::sth::GBLHNDMAP(project)
        }
        
        return $returnKeyedList
}

proc ::sth::Session::checkPath {mypath myclsarray myobj} {
    variable ::sth::Session::myroot
    set patharr [split $mypath  "."]
    foreach path $patharr {
        set mycls [regsub -all {\d+$} $path ""]
        if {[regexp -nocase $mycls "router emulateddevice host"]} {
            continue
        }
        if {[regexp -nocase $mycls $::sth::Session::myroot]} {
            continue
        }
        if {![regexp -nocase $mycls $myclsarray]} {
            return 0
        }
    }
    return 1    
}

proc ::sth::Session::sortHandles {returnKeyedList portcondition deviceflag clsarray root} {
    upvar returnKeyedList myReturnKeyedList
    
    set objList ""
    foreach name $clsarray {
        set returnList [::sth::sthCore::invoke stc::perform GetObjects -RootList $root -ClassName $name]
                        
        set ttarray [split [string map [list " -" \0] $returnList] \0]
        set objlist [keylget ttarray ObjectList]
        if {$objlist ne ""} {
            foreach obj $objlist {
                set myclass [regsub -all {\d+$} $obj ""]
                set myparent [::sth::sthCore::invoke stc::get $obj -parent]
                set port $myparent
                set path "$myparent"
                while {$myparent ne "" && ![regexp [regsub -all {\d+$} $myparent ""] "router emulateddevice host"]} {
                    set myparent [::sth::sthCore::invoke stc::get $myparent -parent]
                    set path "$myparent\.$path"
                }

                if {![regexp -nocase streamblock $myclass] && ![checkPath $path $clsarray $obj]} {
                    continue
                }
                if {$myparent ne ""} {
                    set port [::sth::sthCore::invoke stc::get $myparent -affiliationport-targets]
                    set path "$port\.$path"
                } else {
                    set path $port
                }
                if {$portcondition ne ""} {
                    if {[regexp $port $portcondition]} {
                        if {[catch {keylget myReturnKeyedList "$path\.$obj"} err]} {
                            set hndpath ""
                            catch {set hndpath [keylget myReturnKeyedList $path]}
                            if {$hndpath ne ""} {
                                if {[catch {keylkeys hndpath}]} {
                                    keylset myReturnKeyedList $path "$hndpath $obj"
                                } else {
                                    keylset myReturnKeyedList "$path\.$obj" "{}"
                                }
                            } else {
                                keylset myReturnKeyedList $path $obj
                            }
                        }
                    }
                } else {
                    if {[catch {keylget myReturnKeyedList "$path\.$obj"} err]} {
                        set hndpath ""
                        catch {set hndpath [keylget myReturnKeyedList $path]} 
                        if {$hndpath ne ""} {
                            if {[catch {keylkeys hndpath}]} {
                                keylset myReturnKeyedList $path "$hndpath $obj"
                            } else {
                                keylset myReturnKeyedList "$path\.$obj" "{}"
                            }
                        } else {
                            keylset myReturnKeyedList $path "$obj"
                        }
                    }
                }
            
                if {$deviceflag eq 1 && $myparent ne ""} {
                   append objList "$myparent "
                } else {
                   if {![regexp -nocase {ipv4networkblock|ipv6networkblock} $obj]} {
                        append objList "$obj "
                   }
                }
                
                set clshnds ""
                catch {set clshnds [keylget myReturnKeyedList "$myclass\_hnd"]}
                if {$clshnds ne ""} {
                    keylset myReturnKeyedList "$myclass\_hnd" "$clshnds $obj"
                } else {
                    keylset myReturnKeyedList "$myclass\_hnd" "$obj"
                }
            }
        }
    }
    
    if {$objList ne ""} {
        set hnds ""
        catch {set hnds [keylget myReturnKeyedList handles]}
        if {$hnds ne ""} {
            keylset myReturnKeyedList handles "$hnds [string trim $objList]"
        } else {
            keylset myReturnKeyedList handles "[string trim $objList]"
        }
    }
}

proc ::sth::Session::labserverHandler {} {
    global env
    if {[info exists env(STC_LAB_SERVER_ADDRESS)] && ($::sth::serverflag == 0)} {
        if {$env(STC_LAB_SERVER_ADDRESS) == ""} {
            
        } else {
            ::sth::sthCore::invoke stc::perform csserverconnect -host $env(STC_LAB_SERVER_ADDRESS)
            set labserver_session_list [::sth::sthCore::invoke stc::get system1.csserver -children-cstestsession]
            
            foreach labserver_session $labserver_session_list {
                set labserver_session_name [::sth::sthCore::invoke stc::get $labserver_session -name]
                set labserver_session_ownerid [::sth::sthCore::invoke stc::get $labserver_session -ownerid]
                if {[regexp "$env(STC_SESSION_NAME) -" $labserver_session_name]} {
                    #delete existed session
                    puts "Deleting existed lab server session..."
                    ::sth::sthCore::invoke stc::perform csserverdisconnect
                    ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $env(STC_LAB_SERVER_ADDRESS) -ownerid $labserver_session_ownerid\
                    -testsessionname $env(STC_SESSION_NAME) -createnewtestsession false
                    ::sth::sthCore::invoke stc::perform cstestsessiondisconnect -terminate true
                    #wait 10 sec to make sure session deleted
                    after  10000
                }
            }
            ::sth::sthCore::invoke stc::perform cstestsessionconnect -host $env(STC_LAB_SERVER_ADDRESS) -createnewtestsession true -testsessionname $env(STC_SESSION_NAME)
            
            set ::sth::serverflag 1
        }
    }
}

#cannot know the current step in if/else/elseif/loop/while command,
#so in nested loop commands, the sub command list cannot be enumerated during starting sequencer
proc ::sth::Session::process_loop {currentStep indent index} {
	if {[regexp -nocase {sequencer(if|else|while|loop|elseif)command} $currentStep]} {
        if {$index >= 0} {
            set step_cmdlist [::sth::sthCore::invoke stc::get $currentStep -commandlist]
            if {$index < [llength $step_cmdlist]} {
                set sub_currentstep [lindex $step_cmdlist $index]
                set i $indent
                set tab_str "\t"
                while {$i > 0} {
                    append tab_str "\t"
                    incr i -1
                } 
                set sub_name [::sth::sthCore::invoke stc::get $sub_currentstep -name]
                puts "$tab_str\"$sub_name\"..."
                set myindex [expr $index+1]
                #set subindex 0
                #process_loop $sub_currentstep [expr $indent+1] $subindex
                
                return $myindex
            }
        }
		return -1
	}
	
	return 0
}

proc ::sth::Session::process_loop_leftcmd {tmpStep indent index} {
    if {$tmpStep ne ""} {
        if {![catch {set step_cmdlist [::sth::sthCore::invoke stc::get $tmpStep -commandlist]}]} {
            if {$step_cmdlist ne ""} {
				set i $indent
				set tab_str "\t"
				while {$i > 0} {
					append tab_str "\t"
					incr i -1
				} 
								
                set myindex $index
				set len [llength $step_cmdlist]
                while {$myindex < $len} {
					set sub_currentstep [lindex $step_cmdlist $myindex]
                    set sub_name [::sth::sthCore::invoke stc::get $sub_currentstep -name]
                    puts "$tab_str\"$sub_name\"..."
                    incr myindex
                }
            }
        }
    }
    return 0
}

proc ::sth::Session::start_sequencer {seqHandle} {

    puts "..... start sequencer ....."
    
    ::sth::sthCore::invoke stc::perform sequencerStart
    after 2000
    
    set cmdList [::sth::sthCore::invoke stc::get $seqHandle -CommandList]
    set passedSteps ""
    set tmpStep ""
	set subindex 0
    while {1} {
        set seq_status [::sth::Rfctest::checkSeqState $seqHandle]
        set state [::sth::sthCore::invoke stc::get $seqHandle -state]
        if {$state == "IDLE" || $state == "PAUSE" || $state == "FINALIZE"} {
			if {[regexp -nocase "FAILED" $seq_status]} {
				set cmdList ""
			}
            break
        }
		
		set passedSteps ""
        set currentStep [::sth::sthCore::invoke stc::get $seqHandle -CurrentCommand]
        if {$currentStep == $tmpStep} {
			set subindex [process_loop $currentStep 1 $subindex]
		} else {
            set subindex [process_loop_leftcmd $tmpStep 1 $subindex]
            
            if {[regexp -nocase {sequencer(if|else|elseif)command} $currentStep]} {
                regexp "$currentStep (.*)" $cmdList matched nextElsecmd
                if {![regexp -nocase {sequencerelsecommand} $currentStep] && $nextElsecmd ne ""} {
                    foreach elsecmd $nextElsecmd {
                        if {[regexp -nocase {sequencer(else|elseif)command} $elsecmd]} {
                            regsub -nocase $elsecmd $cmdList "" cmdList
                        }
                        if {[regexp -nocase {sequencerelsecommand} $elsecmd]} {
                            break
                        }
                    }
                }
                
                regexp "(.*) $currentStep" $cmdList matched prevIfcmd
                if {![regexp -nocase {sequencerifcommand} $currentStep] && $prevIfcmd ne ""} {
                    foreach prevcmd $prevIfcmd {
                        if {[regexp -nocase {sequencer(if|elseif)command} $prevcmd]} {
                            regsub -nocase $prevcmd $cmdList "" cmdList
                        }
                        if {[regexp -nocase {sequencerifcommand} $prevcmd]} {
                            break
                        }
                    }
                }
            }
        
            regexp "(.*) $currentStep" $cmdList passedSteps
            foreach step $passedSteps {
                set stepName [::sth::sthCore::invoke stc::get $step -Name]
                puts "\t...command \"$stepName\"..."
            }
            
            regsub -nocase "$passedSteps" $cmdList "" cmdList
            set tmpStep $currentStep
        }
        
        after 2000
    }

    foreach left_step $cmdList {
        set stepName [::sth::sthCore::invoke stc::get $left_step -Name]
        puts "\t...Command \"$stepName\"..."
    }
}


proc ::sth::Session::parse_xml {filexml} {
    variable ::sth::Session::prop2class
    variable ::sth::Session::class2relation

    regsub -all {\\} $filexml {/} filexml
    
    if {![file exists $filexml]} {
        puts "unable to open $filexml"
        return
    }
    
    if {[array size ::sth::Session::baseclass2relation] > 0
        || [array size ::sth::Session::prop2class] > 0} {
        return
    }

    # Load the file into memory and drop the DOM on it...
    set fp [open $filexml r]
    set data [read $fp]
    close $fp

    set loaded_xml [dom parse $data]
    set loaded_xml [$loaded_xml documentElement]
   
    set dnodes [$loaded_xml childNodes]
    set i -1
    foreach dnode $dnodes {
        set nodeName [$dnode nodeName]
        if {$nodeName == "stc:relationType"} {
            
        } elseif {$nodeName == "stc:class"} {
            incr i            
            set cName_ [string tolower [$dnode getAttribute name]]
            set cName "$i.$cName_"

            if {[$dnode hasAttribute baseClass]} {
                set cBase [string tolower [$dnode getAttribute baseClass]]

                set baseProps [array names ::sth::Session::prop2class -glob $cBase\.*]
                if {$baseProps ne ""} {
                    foreach b_prop $baseProps {
                        set sName [regsub {.*\.} $b_prop ""]
                        set key "$cName_\.[string tolower $sName]"
                        set ::sth::Session::prop2class($key) "$sName"
                    }
                }
                
                set baseRel [array names ::sth::Session::class2relation -glob *\.$cBase]
                if {$baseRel ne ""} {
                    set sName $::sth::Session::class2relation($baseRel)
                    set ::sth::Session::class2relation($cName) $sName
                }
                set baseRel [array names ::sth::Session::baseclass2relation -glob *\.$cBase]
                if {$baseRel ne ""} {
                    set ::sth::Session::class2relation($cName) ""
                    foreach rel_cp $::sth::Session::baseclass2relation($baseRel) {
                        if {![regexp -nocase "base base" $rel_cp]} {
                            lappend ::sth::Session::class2relation($cName) $rel_cp
                        }
                    }
                    set ::sth::Session::baseclass2relation($baseRel) [concat $::sth::Session::baseclass2relation($baseRel) [list "$cName_ 0-0 base base"]]
                }
            }
            
            if {[$dnode hasAttribute canCreate]} {
                set canCreate [string tolower [$dnode getAttribute canCreate]]
            }
            set relList [$dnode child all stc:relation]
            set relations ""
            if {[info exist ::sth::Session::class2relation($cName)]} {
                set relations $::sth::Session::class2relation($cName)
            }
            foreach rel $relList {
                set dstRef [$rel getAttribute dstClassRef]
                set srcRef [$rel getAttribute srcClassRef]
                set type [$rel getAttribute type]
                set min [$rel getAttribute minOccurs]
                set max [$rel getAttribute maxOccurs]
                
                if {[regexp -nocase $cName_ $dstRef]} {
                    lappend relations "[string tolower $srcRef] $max-$min $type sources"
                } else {
                    if {[regexp -nocase "framework.ParentChild" $type]} {
                        set target [array names ::sth::Session::class2relation -glob *\.[string tolower $dstRef]]
                        if {$target ne ""} {
                            lappend ::sth::Session::class2relation($target) "[string tolower $cName_] $max-$min $type sources"
                        }
                        lappend relations "fake fake fake fake" 
                    } else {                    
                        lappend relations "[string tolower $dstRef] $max-$min $type targets"
                    }
                }				
            }
            
            if {$relations eq ""} {
                lappend relations "fake fake fake fake"        
            }
            
            if {$canCreate eq "false"} {
                set ::sth::Session::baseclass2relation($cName) $relations
            } else {
                if {[regexp -nocase "framework.Scriptable" $cBase]} {
                    set ::sth::Session::baseclass2relation($cName) $relations
                }
                set ::sth::Session::class2relation($cName) $relations
            }
            
            set propList [$dnode child all stc:property]
            foreach prop $propList {
                set sName [$prop getAttribute name]
                set readonly [$prop getAttribute isReadOnly]
                if {$readonly eq "false"} {
                    set key "$cName_\.[string tolower $sName]"
                    set ::sth::Session::prop2class($key) "$sName"
                }
            }
        }
    }
}

proc ::sth::Session::setobj_recursive {obj rName} {
    variable ::sth::Session::baseclass2relation
    variable ::sth::Session::obj2ret
    
    set baseRels [array names ::sth::Session::baseclass2relation -glob *\.$obj]
    foreach rel_base $baseRels {
        set rel_base_value $::sth::Session::baseclass2relation($rel_base)
        foreach rel_value $rel_base_value {
            if {[regexp -nocase {base base$} $rel_value]} {
                set rel_value_obj [lindex $rel_value 0]
                if {[info exist ::sth::Session::obj2ret($rel_value_obj)] && $rName != $::sth::Session::obj2ret($rel_value_obj)} {
                    set ::sth::Session::obj2ret($rel_value_obj) "$rName $::sth::Session::obj2ret($rel_value_obj)"
                } else {
                    set ::sth::Session::obj2ret($rel_value_obj) $rName
                }
                setobj_recursive $rel_value_obj $rName
            }
        }
    }    
}


proc ::sth::Session::findobj_children {baseobj} {
    variable ::sth::Session::baseclass2relation
    variable ::sth::Session::obj2ret
    
    set objs ""
    set baseRels [array names ::sth::Session::baseclass2relation -glob *\.$baseobj]
    foreach rel_base $baseRels {
        set rel_base_value $::sth::Session::baseclass2relation($rel_base)
        foreach rel_value $rel_base_value {
            if {[regexp -nocase {base base$} $rel_value]} {
                set rel_value_obj [lindex $rel_value 0]
                if {![regexp $rel_value_obj $objs]} {
                    append objs "$rel_value_obj "
                }
            }
        }
    }
    
    return $objs
}

proc ::sth::Session::parse_customized_xml {filexml} {
    regsub -all {\\} $filexml {/} filexml
    
    if {![file exists $filexml]} {
        puts "unable to open $filexml"
        return
    } 

    if {[array size ::sth::Session::obj2ret] > 0} {
        return
    }
        
    # Load the file into memory and drop the DOM on it...
    set fp [open $filexml r]
    set data [read $fp]
    close $fp

    set loaded_xml [dom parse $data]
    set loaded_xml [$loaded_xml documentElement]
    
    set clsList [$loaded_xml selectNode tapi:class]       
    foreach dnode $clsList {
        set cName [$dnode getAttribute name]
        set disable [$dnode getAttribute disable false]
        if {$disable} {
            set ::sth::Session::classDisable($cName) 1
        }
        
        set conditionList [$dnode selectNode tapi:condition]
        foreach condition $conditionList {
            set prop [$condition getAttribute property]
            set op [$condition getAttribute operator]
            set val [$condition getAttribute value]
            set ::sth::Session::classCondition([string tolower $cName]) "$prop,$op,$val"
        }
    }
    
    variable ::sth::Session::prop2class
    variable ::sth::Session::obj2ret
    variable ::sth::Session::baseclass2relation
    
    array set ::sth::Session::ApiArray {}
    array set ::sth::Session::ApiArray_key {}
    set grpList [$loaded_xml selectNode tapi:interface]       
    foreach dnode $grpList {
        set fName [$dnode getAttribute APIName]
        
        set retList [$dnode selectNode tapi:retval]
        foreach ret $retList {
            set keyList [$ret selectNode tapi:retkey]
            foreach key $keyList {
                set rName [$key getAttribute name]
                set obj [string tolower [$key getAttribute object]]
                if {[info exist ::sth::Session::obj2ret($obj)] && $rName != $::sth::Session::obj2ret($obj)} {
                    set ::sth::Session::obj2ret($obj) "$rName $::sth::Session::obj2ret($obj)"
                } else {
                    set ::sth::Session::obj2ret($obj) $rName
                }
                
                setobj_recursive $obj $rName
            }
        }
        
        set unsetList {}
        set mapList [$dnode selectNode tapi:map]
        foreach map $mapList {
            set prefix_lst ""
            set object_lst ""                
            append prefix_lst [$map getAttribute prefix]
            append object_lst [$map getAttribute object]
                   
            set propList [$map selectNode tapi:param]
            foreach prop $propList {
                set sName [$prop getAttribute name]
                set sName [string tolower [regsub {.*\.} $sName ""]]
                set disable [$prop getAttribute disable false]
                if {$disable} {
                    continue
                }
                set valueList [$prop selectNode tapi:value]

                set alias [$prop getAttribute alias]
                set alias [regsub -all "_" $alias ""]
                
                set index 0
                foreach obj $object_lst {
                    set prefix ""
                    catch {set prefix [regsub -all "_" [lindex $prefix_lst $index] ""]}
              
                    set myobj [string tolower $obj]
                    set myrealobj [regsub {.*\.} $myobj ""]
                    if {[regexp -nocase "base" $myobj]} {
                        set child_objs [findobj_children $myobj]
                        foreach my_obj $child_objs {
                            set ::sth::Session::prop2class($my_obj\.$prefix$alias) $::sth::Session::prop2class($myrealobj\.$sName)
                        }
                    } else {
                        set ::sth::Session::prop2class($myobj\.$prefix$alias) $::sth::Session::prop2class($myrealobj\.$sName)
                    }
                    lappend unsetList $myrealobj\.$sName
                    
                    foreach val $valueList {
                        set in [$val getAttribute input]
                        set out [$val getAttribute output] 
                        set ::sth::Session::valueproc($prefix\_$alias) "$in\->$out"
                    }
                    incr index
                } 
            }
        }

        set prop2process ""
        set prop2process_key ""
        
        set propList [$dnode selectNode tapi:param]
        foreach prop $propList {
            set disable [$prop getAttribute disable false]
            if {$disable} {
                continue
            }
            set sName [$prop getAttribute name]
            set alias [$prop getAttribute alias ""]
            set isKey [$prop getAttribute isParamKey false]
            set alias [regsub -all "_" $alias ""]
            
            set pName ""
            set pName_key ""
            set procList [$prop selectNode tapi:process]
            if {$procList ne ""} {
                foreach proce $procList {
                    if {[regexp true $isKey]} {
                        append pName_key "[$proce getAttribute procName] "
                    } else {
                        append pName "[$proce getAttribute procName] "
                    }
                }
                if {[regexp true $isKey]} {
                    append prop2process_key "$sName\.$alias $pName_key ;"
                } else {
                    append prop2process "$sName $pName;"
                }
            } 
           
            set myobj [string tolower [regsub {\..*} $sName ""]]
            set propName [string tolower [regsub {.*\.} $sName ""]]  
            set ::sth::Session::prop2class($myobj\.$alias) $propName
            set child_objs [findobj_children $myobj]
            foreach my_obj $child_objs {
                set ::sth::Session::prop2class($my_obj\.$alias) $::sth::Session::prop2class($myobj\.$alias)
                lappend unsetList $myobj\.$alias
            }
        }
               
        foreach v $unsetList {
            if {[info exist ::sth::Session::prop2class($v)]} {
                unset ::sth::Session::prop2class($v)
            }
        }
        set ::sth::Session::ApiArray_key($fName) $prop2process_key
        set ::sth::Session::ApiArray($fName) $prop2process
    }
}
