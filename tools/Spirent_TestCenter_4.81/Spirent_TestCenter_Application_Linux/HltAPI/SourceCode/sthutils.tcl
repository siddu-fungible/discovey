# This file contains confidential and / or privileged information belonging to Spirent Communicaions plc,
# its affiliates and / or subsidiaries.



###/*! \file sthutils.tcl
###	\brief Utility File
###	
###	This file contains all the common utilities useful through the project.
###*/

###/*! \namespace sth::sthCore
###\brief Common Commands/Utility
###
###This namespace contains the procedures common to various Api

###*/
### namespace sth::sthCore {

namespace eval ::sth::sthCore {
	variable _INT_SHA_CMD_FAIL 0
	variable _INT_SHA_CMD_PASS 1
	array set 64BitAssignedNumbers {}
	variable _INT_LOG_FILE_HND ""
	array set macAddress {}
	array set bfd_available_ipaddr {}
}

###/*! \ingroup gen_utils
###\fn getNext64BitNumber ()
###\brief Generate Unique 64 Bit Hex
###
###This procedure generates a unique 64bit hex number which has not been used before. 
###\return Unique 64 Bit Hex
###
###\author Saumil Mehta (smehta)
###*/
###
###getNext64BitNumber ();
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
proc ::sth::sthCore::getNext64BitNumber {  } {
	
	variable 64BitAssignedNumbers

	::sth::sthCore::log internalcall "Generating Unique 64 bit number"
	set numberGenerated 0
	while {$numberGenerated != 1} {

		set num1 [format %04X [expr {int(65535 * rand())}]]
		set num2 [format %04X [expr {int(65535 * rand())}]]
		set num3 [format %04X [expr {int(65535 * rand())}]]
		set num4 [format %04X [expr {int(65535 * rand())}]]
		
		if {[info exists 64BitAssignedNumbers($num1$num2$num3$num4)]} {
			
		} else {
			set 64BitAssignedNumbers($num1$num2$num3$num4) 1
			set numberGenerated 1
		}
	}
	return "$num1$num2$num3$num4"
}


###/*! \ingroup gen_utils
###\fn isValidStepValue (int ipVer, str stepVal, str errMsg)
###\brief Validate if input is valid ip step
###
###This procedure validates if the input is a valid ip step value or not. 
###\return _INT_SHA_CMD_PASS or _INT_SHA_CMD_FAIL
###
###\author Saumil Mehta (smehta)
###*/
###
###isValidStepValue (int ipVer, str stepVal, str errMsg);
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
proc ::sth::sthCore::isValidIpStepValue { ipVer stepVal } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	switch -exact -- $ipVer \
		4 {
			set octets [split $stepVal .]
			if {[llength $octets] != 4} {
				return $::sth::sthCore::FAILURE
			}
			foreach oct $octets {
				if {![string is integer $oct]} {
					return $::sth::sthCore::FAILURE
				}
			}
		}\
		6 {
			set normaizedIpAddressValue [::sth::sthCore::normalizeIPv6Addr $stepVal];
			if {$normaizedIpAddressValue == 0} {
				return $::sth::sthCore::FAILURE
			}
		}\
		default {
			return $::sth::sthCore::FAILURE
		}

	return $::sth::sthCore::SUCCESS

}

###/*! \ingroup gen_utils
###\fn normalizeIPv6Addr (str ip)
###\brief Returns the normalized ipv6 address for the input ipv6 address
###
###This procedure is used to normalize a given ipv6 address
###
###\param[in] ipv6 address that needs to be normalized
###\param[out] normalized ipv6 address
###\return 0 or 1
###
###\author Rajesh Shroff (rshroff)
###*/
###
###normalizeIPv6Addr (str ip)
###
# Edited: Sapna Leupold: 10/19/06
# Removed args
proc ::sth::sthCore::normalizeIPv6Addr {ip} {
	set octets [split $ip :]
	set ip4embed [string first . $ip]
	set len [llength $octets]
	if {$len < 0 || $len > 8} {
		#puts "invalid address: this is not an IPv6 address";
		return 0;
	}
	set result "";
	for {set n 0} {$n < $len} {incr n} {
		set octet [lindex $octets $n]
		if {$octet == {}} {
			if {$n == 0 || $n == ($len - 1)} {
				set octet \0\0
			} else {
				set missing [expr {9 - $len}]
				if {$ip4embed != -1} {incr missing -1}
				set octet [string repeat \0\0 $missing]
			}
		} else {
			set m [expr {4 - [string length $octet]}]
			if {$m != 0} {
				set octet [string repeat 0 $m]$octet
			}
			set octet [binary format H4 $octet]
		}
		append result $octet
	}
	if {[string length $result] != 16} {
		#puts "invalid address: \"$ip\" is not an IPv6 address";
		return 0;
	}
	  
	set bin $result;
	set len [string length $bin]
	set r ""
	
	binary scan $bin H32 hex
	for {set n 0} {$n < 32} {incr n} {
		append r [string range $hex $n [incr n 3]]:
	}
	return [string trimright $r :]
}

###/*! \ingroup gen_utils
###\fn ipv6Step (str Baseipv6Addr str ipv6Step)
###\brief Returns the new address after incrementing the given ipv6 address by the step provided. 
###
###This procedure is used to increment the given ipv6 address with step provided.
###
###\param[in] ipv6 address that needs to be incremented
###\param[in] ipv6 step in the ipv6 address format
###\param[out] incremented ipv6 address
###\return 0 or incremented ipv6 addr
###
###\author Rajesh Shroff (rshroff)
###*/
###
###ipv6Step (str Baseipv6Addr str ipv6Step)
###

proc ::sth::sthCore::ipv6Step { ipv6BaseAddress ipv6Step } {
	set norBaseAddr [::sth::sthCore::normalizeIPv6Addr $ipv6BaseAddress];
	if {$norBaseAddr == 0} {
		return 0;
	}
	set norStep [::sth::sthCore::normalizeIPv6Addr $ipv6Step];
	if {$norStep == 0} {
		return 0;
	}
	
	set newAddr "";
	set iStatus [::sth::sthCore::binaryAddition $norBaseAddr $norStep newAddr];
	if {$iStatus != 1} {
		return 0;
	}
	return $newAddr;
}

###/*! \ingroup gen_utils
###\fn getValueOfSwitch (str inputString, str switchToGetValue, varRef switchValueRefName)
###\brief Returns the value of the switch from the input string
###
###This procedure is used to fetch the value of a particular switch from the user input. 
###
###\param[in] inputString Contains the user input which needs to be scanned for the switch
###\param[in] switchToGetValue Contains the name of the switch whose value needs to be returned.
###\param[out] switchValueRefName Contains the name of the variable which will hold the value.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Saumil Mehta (smehta)
###*/
###
###getValueOfSwitch (str inputString, str switchToGetValue, varRef switchValueRefName );
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success failure calls
proc ::sth::sthCore::getValueOfSwitch { inputString switchToGetValue switchValueRefName} {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	upvar 1 $switchValueRefName switchValue

	set sIndex [lsearch $inputString "-$switchToGetValue"]
	set getValue 1
	set sValue ""
	set argsLastIndex [llength $inputString]
	if {$sIndex != -1} {
		incr sIndex
		if {$sIndex != $argsLastIndex} {
			while {$getValue == 1} {
				set sIndexValue [lindex $inputString $sIndex]
				#		puts $sIndexValue
				if {[string index $sIndexValue 0] == "-"} {
					set getValue 0
				} else {
					if {$sValue == ""} {
						set sValue "$sIndexValue"
					} else {
						set sValue "$sValue $sIndexValue"
					}
					if {$argsLastIndex == [incr sIndex]} {
						set getValue 0
					}
				}
			}
		}
	} else {
		set switchValue "SHA_UNKNWN_SWITCH"
		return $::sth::sthCore::FAILURE
	}
	
	if {$sValue == ""} {
		#This should not occur.
		set switchValue "SHA_NO_USER_INPUT"
		return $::sth::sthCore::FAILURE
	} else {
		set switchValue $sValue
		return $::sth::sthCore::SUCCESS
	}
	
}


###/*! \ingroup gen_utils
###\fn parseInputArgs (listRef switchListName, array switchValueListName, str inputString)
###\brief Parses the input string
###
###This procedure is used to generate an array switchvalue pairs from the user input. It also generates a lis of all the switches entered by the user.
###
###\param[out] switchListName Contains the list of the switches
###\param[out] switchValueListName The name of the array variable which needs to filled with swith,value pairs.
###\param[in] inputString Contains the inputString which needs to be parsed
###\return Nothing
###
###\author Saumil Mehta (smehta)
###*/
###
###parseInputArgs (listRef switchListName, array switchValueListName, str inputString);
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success failure calls.
# Removed calls in function to args
proc ::sth::sthCore::parseInputArgs { switchListName switchValueListName userInput} {

	variable ::sth::sthCore::SUCCESS
	upvar 1 $switchListName switchList
	upvar 1 $switchValueListName switchValueList

	set swVal ""
	set swName ""
	set tmpVar ""

	if {$userInput == ""} {
		 return 0
	}

	foreach inputVal $userInput {
		if {[string index $inputVal 0] == "-"} {
			#This is a switch
			if {$swVal == "" && $swName != ""} {
				#SHA_NO_USER_INPUT for previous
				lappend tmpVar "SHA_NO_USER_INPUT"
			} elseif {$swName != "" && $swVal != ""} {
				lappend tmpVar "$swVal"
			}
			set swName [string replace $inputVal 0 0]
			lappend tmpVar $swName
			set swVal ""
		} else {
			if {$swName == ""} {
				#A switch was not entered for this value. ERROR
				return 0
			} else {
				if {$swVal == ""} {
					set swVal $inputVal
				} else {
					set swVal "$swVal $inputVal"
				}
			}
		}
	}
	
	if {$swVal != ""} {
		lappend tmpVar $swVal
	} else {
		lappend tmpVar "SHA_NO_USER_INPUT"
	}

	array set switchValueList $tmpVar
	array set tmpSwitchList $tmpVar
	set switchList [array names tmpSwitchList]

	return $::sth::sthCore::SUCCESS

}

###/*! \ingroup gen_utils
###\fn updateUserInput (listRef argsName, str mode, str switchName, str switchValue)
###\brief Updates User input 
###
###This procedure updates the value of switch in the user input. 
###
###\param[in,out] argsName Reference to the var which contains user Input
###\param[in] mode Specifies if the switch needs to be deleted or updated
###\li \c 0 Indication to delete.
###\li \c 1 Indication to update
###\param[in] switchName Contains the name of the switch which needs to be updated
###\param[in] switchValue Contains the new value of the switch. This is not required if mode is delete
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\attention As this is internal utility, no validation is done.
###\warning No Validation
###\author Saumil Mehta (smehta)
###
###*/
###
###updateUserInput (listRef argsName, str mode, str switchName, str switchValue);
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
proc ::sth::sthCore::updateUserInput { argsName mode switchName switchValue} {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	upvar 1 $argsName userInput

	set swName ""
	set tmpVar ""

	foreach element $userInput {
		if {[string index $element 0] == "-"} {
			#This is a switch
			if {[info exists switchFound]} {
				#this is the next switch after the one to be found. So add the value.
				switch -exact -- $mode \
					1 {
						set cmd "lappend tmpVar $switchName $switchValue"
						eval $cmd 				   
					}\
					0 {

					}\
					default {
						#If it reaches this stage, it is possibly an error
					}
				catch {unset switchFound}
				lappend tmpVar $element
			} elseif {[string equal $element $switchName]} {
				#Matches with the switchName, thus update subsequent value of it.
				set switchFound 1
				set switchMatched 1
			} else {
				lappend tmpVar $element
			}
		} else {
			if {![info exists switchFound]} {
				lappend tmpVar $element 		   
			}
		}
	}

	if {[info exists switchFound]} {
		#Last element is userInput is value which needs to be replaced.
		set cmd "lappend tmpVar $switchName $switchValue"
		eval $cmd 	   
	}
	
	if {![info exists switchMatched] && $mode == 1} {
		# Addition of new switch
		set cmd "lappend tmpVar $switchName $switchValue"
		eval $cmd 	
	}
	
	set userInput "$tmpVar"

	return $::sth::sthCore::SUCCESS

}

###/*! \ingroup gen_utils
### \fn updateReturnInfo (keyedList returnInfo, str KeyName, str keyValue)
###\brief Updates the value of the string
###
###This procedure updates the value of the currentReturnInfoString with the new key,value. Currently, if the key already exists, the value is appended to the old value of the key with | as the seperator.
###
###\param[in] returnInfo Provides the keyed list which needs to be updated with keyName,keyValue
###\param[in] KeyName Name of the Key to be used 
###\param[in] keyValue Value of the key.
###\return updated returnInfo
###
###\attention If a key is currently present in the \em returnInfo, it will be updated with space as a delimiter. It will NOT be overwritten
###\author Saumil Mehta (smehta)
###*/
###
###updateReturnInfo (keyedList ReturnInfo, str KeyName, str keyValue);
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
# Arguments:
#   option      "add" | ""
#               "add"   If there is a value in $keyName, add $keyValue to the existing value.
#               ""      If there is a value in $keyName, append $keyValue to the existing value.
#               If there is no $keyName in $returnInfo (a keyed list), both will set $keyValue for $keyName.
proc ::sth::sthCore::updateReturnInfo {returnInfo keyName keyValue {option ""}} {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	if {[string equal $keyName "status"] == 1} {
		if {![catch {keylget returnInfo $keyName} statusKeyValue]} {
			if {($statusKeyValue == $::sth::sthCore::SUCCESS) && ($keyValue == $::sth::sthCore::FAILURE)} {
				keylset returnInfo status $::sth::sthCore::FAILURE
				return $returnInfo
			} else {
				return $returnInfo
			}
		} else {
			keylset returnInfo status $keyValue
			return $returnInfo
		}
	} elseif {[string equal $keyName "log"] == 1} {	
		if {[catch {keylget returnInfo $keyName} logMsg]} {
			keylset returnInfo $keyName $keyValue
			return $returnInfo
		} else {
			keylset returnInfo $keyName "$keyValue $logMsg"
			return $returnInfo
		}
	} else {
		if {[catch {keylget returnInfo $keyName} currentMsg]} {
			keylset returnInfo $keyName $keyValue	   
		} else {
            if {$option == ""} {
                # append the value
                keylset returnInfo $keyName "$currentMsg $keyValue"
            } elseif {$option == "add"} {
                # accumulate the value
                set value [keylget returnInfo $keyName]
                set newvalue [expr $value + $keyValue]
                keylset returnInfo $keyName $newvalue
            }
		}
        return $returnInfo
	}
}

proc ::sth::sthCore::lreverse_local l {
	if {[info command lreverse] == ""} {
		set r {}
		set i [llength $l]
		while {[incr i -1]} {lappend r [lindex $l $i]}
		lappend r [lindex $l 0]
	} else {
		lreverse $l
	}
}

###/*! \ingroup gen_utils
### \fn binaryAddition (str string1, str string2, Ref returnVarName)
###\brief Performs Binary Addition
###
###This procedure performs the binary addition of string1 and string2
###\param[in] string1 First String
###\param[in] string2 Second String.
###\param[out] returnVarName Return Var Name.
###\author Saumil Mehta (smehta)
###*/
###
###binaryAddition (str string1, str string2, Ref returnVarName);
###
#Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
# This function will be removed
proc ::sth::sthCore::binaryAddition { string1 string2 returnVarName} {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	upvar 1 $returnVarName returnValue

	set str1 [split $string1 {}]
	set str2 [split $string2 {}]

	set str1Len [llength $str1]
	set str2Len [llength $str2]
	
	set newStr1 ""
	foreach char $str1 {
		set newStr1 "$char $newStr1"
	}
	set newStr2 ""
	foreach char $str2 {
		set newStr2 "$char $newStr2"
	}
	
	set addCarry 0
	set rt ""
	
	#puts "$newStr1||$newStr2"
	foreach s1 $newStr1 s2 $newStr2 {
		#puts "s1:$s1||s2:$s2"
		if {$s1 == 1 && $s2 == 1} {
			if {$addCarry == 1} {
				set rt "1$rt"
			} else {
				set rt "0$rt"
			}
			set addCarry 1
		} elseif {($s1 == 1 && $s2 == 0) || ($s1 == 0 && $s2 == 1)} {
			if {$addCarry == 1} {
				set addCarry 1
				set rt "0$rt"
			} else {
				set addCarry 0
				set rt "1$rt"			
			}
		} elseif {$s1 == 0 && $s2 == 0} {
			if {$addCarry == 1} {
				set addCarry 0
				set rt "1$rt"
			} else {
				set addCarry 0
				set rt "0$rt"			
			}		
		} else {
			if {$addCarry == 1 && $s1 == 1} {
				set addCarry 1
				set rt "0$rt"
			} elseif {$addCarry == 1 && $s1 == 0} {
				set addCarry 0
				set rt "1$rt"
			} else {
				set rt "$s1$rt"
			}
		}
	}
	
	if {$addCarry == 1} {
		set rt "1$rt"
	}

	set returnValue $rt
	return $::sth::sthCore::SUCCESS
}

###/*! \ingroup gen_utils
### \fn binaryMultiplication (str string1, str string2, Ref returnVarName)
###\brief Performs Binary Multiplication
###
###This procedure performs the binary multiplication of string1 and string2
###\param[in] string1 First String
###\param[in] string2 Second String.
###\param[out] returnVarName Return Var Name.
###\author Saumil Mehta (smehta)
###*/
###
###binaryMultiplication (str string1, str string2, Ref returnVarName);
###
#Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
# This function will be removed
proc ::sth::sthCore::binaryMultiplication { string1 string2 returnVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	upvar 1 $returnVarName returnValue

	set str1 [split $string1 {}]
	set str2 [split $string2 {}]

	set str1Len [llength $str1]
	set str2Len [llength $str2]
	
	set newStr1 ""
	foreach char $str1 {
		set newStr1 "$char $newStr1"
	}
	set newStr2 ""
	foreach char $str2 {
		set newStr2 "$char $newStr2 "
	}
	
	set rt ""
	array set rtArray {}
	set cnt 0
	foreach s2 $newStr2 {
		incr cnt
		foreach s1 $newStr1 {
			#puts "s1:$s1||s2:$s2"
			if {$s1 == 1 && $s2 == 1} {
				set rt "1$rt"
			} elseif {$s1 == 0 || $s2 == 0} {
				set rt "0$rt"
			} else {
				set rt "$s1$rt"
			}
			#puts "rt:$rt"
		}
		for {set i 1} {$i < $cnt} {incr i} {
			append rt 0
		}
		set rtArray($cnt) $rt
		set rt ""
	}
	set result ""
	puts "||[array get rtArray]||"
	set isFirst 1
	foreach {ind} "[lsort -decreasing [array names rtArray]]" {
		puts "Before ADD:$result"
		if {$isFirst} {
			set isFirst 0
			::sth::sthCore::binaryAddition $rtArray($ind) 0 result
		} else {
			::sth::sthCore::binaryAddition $result $rtArray($ind) result
		}
		puts "After ADD:$result"
	}
	puts "Result:$result"
	set returnValue $result
	return $::sth::sthCore::SUCCESS
}

# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
#Edited code so that project handle is sent in and is not
#hardcoded
proc ::sth::sthCore::IsPortValid { port_handle msgName} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::GBLHNDMAP
    
    
    upvar 1 $msgName errorMsg       

    set hltprojecthandle $::sth::sthCore::GBLHNDMAP(project)
    if {[catch {set children [::sth::sthCore::invoke stc::get $hltprojecthandle -children-port] } errorMsg]} {
	    return $::sth::sthCore::FAILURE
    } else {
	    if {[lsearch $children $port_handle] >= 0} {
		    return $::sth::sthCore::SUCCESS
	    } else {
		    return $::sth::sthCore::FAILURE
	    }
    }
}

##
##validate BFD ip address to avoiding creating BFD routers on different interfaces with the same ipaddr.
##
proc ::sth::sthCore::IsBfdIpAddrValid {rtrHandle ipaddr} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::bfd_available_ipaddr   
    
    if {[catch {set rtrchild [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList
    }
    foreach router $rtrchild {
	if {$router != $rtrHandle && $bfd_available_ipaddr($router) == $ipaddr} {
	    set errorMsg "conflicted bfd IP address $ipaddr"
            return $FAILURE
	}
    }
    
    set bfd_available_ipaddr($rtrHandle) $ipaddr
    return $SUCCESS
} 

###/*! \ingroup isishelperfuncs
### \fn updateIpAddress (str ipVersion, str ipAddressValue, str stepValue, str stepCnt)
###\brief Update the ipaddress
###
###This procedure updates the value of the ip address by the step value specified.
###\param[in] ipVersion The ip version \em 4 or \em 6.
###\param[in] ipAddressValue The current ip address which needs to be stepped.
###\param[in] stepValue The step value between two consequtive ip addresses.
###\param[in] stepCnt The Cnt value by which ip address needs to be stepped.
###\param[in] Mode. Possbile values are INCR and DECR, default is INCR. Determine increase or decrease the address.
###                 Currently it's just for ipv4.
###
###\return _INT_SHA_CMD_FAIL or new Ip Address
###
###\author Jeremy Chang (jchang)
###\todo update the procedure for ipv6 address
###*/
###
###updateIpAddress (str ipVersion, str ipAddressValue, str stepValue, str stepCnt);
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
# Edited: Fei Cheng: 07/27/10
# Added an option "Mode" to control whether increase or decrease the address 
proc ::sth::sthCore::updateIpAddress { ipVersion ipAddressValue stepValue stepCnt {Mode INCR}} {
	
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
#	set stepValue [expr {$stepValue*$stepCnt}]
	
#	puts "$ipVersion : $ipAddressValue : $stepValue"
#	return $ipAddressValue
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
			binary scan [binary format B32 [format %032s $binIpAddress]] I ipAddress
			#puts $ipAddress
			#convert the step ip address to decimal
			set octets [split $stepValue .]
			if {[llength $octets] != 4} {
				set octets [lrange [concat 0 0 0 $octets] 0 3]
			}
			set binStepIpAddress ""
			foreach oct $octets {
				binary scan [binary format c $oct] B* bin
				set binStepIpAddress "$binStepIpAddress$bin"
			}
			binary scan [binary format B32 [format %032s $binStepIpAddress]] I stepIpAddress
			#multiply by the count
			set stepIpAddress [expr {$stepIpAddress*$stepCnt}]
			if {$Mode == "INCR"} {
			    binary scan [binary format I [expr {$ipAddress+$stepIpAddress}]] B* newBinIpAddress
			} else {
			    binary scan [binary format I [expr {$ipAddress-$stepIpAddress}]] B* newBinIpAddress
			}
			for {set x 0; set y 7} {$y < 32} {} {
				set oct [string range $newBinIpAddress $x $y]
				binary scan [binary format B32 $oct] i i
				lappend newIp $i
				set x [expr {$x+8}]
				set y [expr {$y+8}]
			}
			set returnIp [join $newIp .]
			return $returnIp
		}\
		6 {
			set myStepValue $stepValue
			
#			if {[string first "::" $stepValue] <0} {
#				if {[string length $stepValue] > 4} {
#					set stepValue [string range $stepValue 0 3]
#				}
#				set stepValue "0::$stepValue"
#			}
#			
#			
#                        set count 0
#                        for {set i 0} {$i<[string length $myStepValue]} {incr i} {
#                               if {[string equal : [string range $myStepValue $i $i]]} {
#                                       incr count
#                                }
#                        }              
#			if {[string equal 7 $count]} {
#				set starIndex [expr [string last ":" $myStepValue] + 1]
#				set endIndex [expr [string length $myStepValue] - 1]
#				set stepValue [string range $myStepValue $starIndex $endIndex]
#				set stepValue "0::$stepValue"
#			}
			
			set normaizedIpAddressValue [::sth::sthCore::normalizeIPv6Addr $ipAddressValue];
			if {$normaizedIpAddressValue == 0} {
				return 0;
			} else {
				set ipAddressValue $normaizedIpAddressValue
			}
			
			set normalizedStepValue [::sth::sthCore::normalizeIPv6Addr $stepValue];
			if {$normalizedStepValue == 0} {
				return 0;
			} else {
				set stepValue $normalizedStepValue
			}

			set octets [split $ipAddressValue :]
			set binIpAddress ""
			foreach oct $octets {
				binary scan [binary format H4 $oct] B* bin
				set binIpAddress "$binIpAddress$bin"
			}
			#puts "Binary: $binIpAddress"
			#binary scan [binary format B* $binIpAddress] I ipAddress
			
			#converting the step to binary
			set octets [split $stepValue :]
			set binStepIpAddress ""
			foreach oct $octets {
				binary scan [binary format H4 $oct] B* bin
				set binStepIpAddress "$binStepIpAddress$bin"
			}
			#puts "Binary Step Address: $binStepIpAddress"
			#binary scan [binary format B* $binStepIpAddress] I binStepValue
			
			#Convert stepCnt to binary
			binary scan [binary format c $stepCnt] B* binStepCnt
			#puts "Binary Cnt: $binStepCnt"
			
			#multiply the step values with step cnt
			#if {![::sth::sthCore::binaryMultiplication $binStepIpAddress $binStepCnt binStep]} {
			#	#error @TODO  Decide return Value
			#}
			#puts "Binary New Step: $binStep"
			#Perform Binary addition of newStepValue to IpAddress
			set newBinIpAddress $binIpAddress
			for {set i 0} {$i < $stepCnt} {incr i} {
				if {![::sth::sthCore::binaryAddition $newBinIpAddress $binStepIpAddress newBinIpAddress]} {
					#error @TODO  Decide return Value
				}
			}
			
			for {set x 0; set y 15} {$y < 128} {} {
				set oct [string range $newBinIpAddress $x $y]
				binary scan [binary format B16 $oct] H* i
				lappend newIp $i
				set x [expr {$x+16}]
				set y [expr {$y+16}]
			}
			
			set returnIp [join $newIp :]
			return $returnIp
		
		}\
		default {
		
		}
	
}


###/*! \ingroup isishelperfuncs
### \fn stepSwitchValue (str switchCurrentValue, str stepValue, str stepCnt)
###\brief Update the switchValue
###
###This procedure updates the value of the ip address by the step value specified.
###\param[in] switchCurrentValue The current value of the switch.
###\param[in] stepValue The value by which the switchValue needs to be stepped.
###\param[in] stepCnt The count by which the switchValue needs to be stepped.
###
###\return _INT_SHA_CMD_FAIL or new switch Value
###
###
###\author Saumil Mehta (smehta)
###*/
###
###stepSwitchValue (str switchCurrentValue, str stepValue, str stepCnt);
###
# Edited: Sapna Leupold: 10/19/06
# Removed args and changed success and failure calls
proc ::sth::sthCore::stepSwitchValue {switchCurrentValue stepValue stepCnt newStepSwitchValueVarName} {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	upvar 1 $newStepSwitchValueVarName newStepValue

	set incrValue [expr {$stepValue * $stepCnt}]
	if {$incrValue != 0} {
		set newStepValue [expr {$switchCurrentValue + $incrValue}]
	} else {
		set newStepValue $switchCurrentValue
	}
	
	return $::sth::sthCore::SUCCESS
	

}

###/*! \ingroup isishelperfuncs
### \fn ResultDataSetSubscribe (str myNameSpace, str protocolObj, str resultsObj, keyed_list returnInfoVarName)
###\brief subscribe the resultdataset and generate the results object
###
###This procedure subscribe the resultdataset and generate the results object
###\param[in] myNameSpace The namespace of the protocol
###\param[in] protocolObj The object name of the protocol, e.g., BgpRouterConfig, IsisRouterConfig, etc.
###\param[in] resultsObj The object name of the protocol results, e.g., BgpRouterResults, IsisRouterResults, etc.
###\param[in,out] returnInfoVarName The return keyed list
###
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###
###\author Tong Zhou
###*/
###
###ResultDataSetSubscribe (str myNameSpace, str protocolObj, str resultsObj, keyed_list returnInfoVarName);
###

proc ::sth::sthCore::ResultDataSetSubscribe {myNameSpace protocolObj resultsObj returnInfoVarName} {

	variable ::sth::sthCore::FAILURE
	variable ::sth::sthCore::SUCCESS
	variable ::sth::GBLHNDMAP
	
	upvar 1 $returnInfoVarName returnKeyedList
	
	set cmdStatus $SUCCESS
	set cmdError 0
	set cmd "set myCreateResultQuery \$$myNameSpace\createResultQuery"
	eval $cmd
	set hltproject $::sth::GBLHNDMAP(project)
	set foundDataset 0
	if {$myCreateResultQuery <= 0} {
		if {[catch {set resultDataSet [::sth::sthCore::invoke stc::create ResultDataSet -under $hltproject "-InternalXmlFormatString \"\""]} createStatus]} {
			set cmdError 1
			::sth::sthCore::processError returnKeyedList "Internal Command Error while creating the resultDataSet under $hltproject, Error:$createStatus" {}
			return $FAILURE
		} else {
			if {[catch {set resultQuery [::sth::sthCore::invoke stc::create Resultquery -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId $protocolObj -ResultClassId $resultsObj"]} createStatus]} {
				set cmdError 1
				::sth::sthCore::processError returnKeyedList "Internal Command Error while creating the resultquery under $resultDataSet, Error:$createStatus" {}
				return $FAILURE
			} else {
				set cmd "set $myNameSpace\createResultQuery 1"
				eval $cmd
				set resultData $resultDataSet
			}
		}
	} else {
# 		tk_messageBox -message "set resultDataSet [::sth::sthCore::invoke stc::get $hltproject -children-resultdataset]"
		if {[catch {set resultDataSet [::sth::sthCore::invoke stc::get $hltproject -children-resultdataset]} getStatus]} {
			set cmdError 1
			::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the resultdataset handle from $hltproject, Error: $getStatus" {}
			return $FAILURE
		} else {
			foreach resultData $resultDataSet {
				if {[catch {set resultQueryHandle [::sth::sthCore::invoke stc::get $resultData -children-Resultquery]} getStatus]} {
					set cmdError 1
					::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the resultquery handle from $resultData, Error: $getStatus" {}
				} else {
					if {[catch {set configclassid [::sth::sthCore::invoke stc::get $resultQueryHandle -ConfigClassId]} getStatus]} {
						set cmdError 1
						::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the configclassId from $resultQueryHandle, Error: $getStatus" {}
					} else {
						if {[string equal [string tolower $configclassid] [string tolower $protocolObj]]} {
							set tmpHandle $resultData
							set foundDataset 1
						}
					}
				}
				if {$foundDataset > 0} {
					set cmdError 0
					set resultData $tmpHandle
					break
				}
			}
		}
	}
	
	if {$cmdError <= 0} {
		if {[catch {::sth::sthCore::invoke stc::perform "ResultDataSetSubscribe -ResultDataSet $resultData"} performStatus]} {
			::sth::sthCore::processError returnKeyedList "Internal Command Error while subscribing the resultdataset $resultData. Error: $performStatus" {}
			return $FAILURE
		} else {
			catch {keyldel returnKeyedList log}
			return $SUCCESS
		}
	} else {
		::sth::sthCore::processError returnKeyedList "Internal Command Error: Broken resultdataset." {}
		return $FAILURE
	}
}

###/*! \ingroup gen_utils
###\fn configureNextMacAddress ()
###\brief Generate Unique MAC address
###
###This procedure generates a unique MAC address for a router,
### and configures the router with the MAC address
###
###\author Tong Zhou
###*/
###
###configureNextMacAddress ();
###
proc ::sth::sthCore::configureNextMacAddress { routerHandle } {
	
	variable macAddress
	variable ::sth::sthCore::FAILURE
	variable ::sth::sthCore::SUCCESS	

	::sth::sthCore::log internalcall "Generating Unique MAC address"
	set numberGenerated 0
	while {$numberGenerated != 1} {

	#	set num1 [format %X [expr {int(16777216 * rand())}]]
		set num2 [format %X [expr {int(16777216 * rand())}]]
		
	#	set num1head0 [expr 6-[string length $num1]]
		set num2head0 [expr 6-[string length $num2]]
		
# 		if {$num1head0 > 0} {
# 			set num1 "[string repeat 0 $num1head0]$num1"
# 		}
		if {$num2head0 > 0} {
			set num2 "[string repeat 0 $num2head0]$num2"
		}
		
		if {[info exists macAddress($num2)]} {
			
		} else {
			set macAddress($num2) 1
			set numberGenerated 1
		}
	}
	set tmpMac $num2
	set configMac "00:00:00:[string range $tmpMac 0 1]:[string range $tmpMac 2 3]:[string range $tmpMac 4 5]"
	if {[catch {set EthIIResultIf [::sth::sthCore::invoke stc::get $routerHandle -children-ethiiif]} getStatus]} {
		return $FAILURE
	} else {
		if {[catch {::sth::sthCore::invoke stc::config $EthIIResultIf -SourceMac $configMac} configStatus]} {
			return $FAILURE
		} else {
			return $SUCCESS
		}
	}
}


#######################################ADD by WEST##############################
#replace ::sth::sthCore::macToDouble by ::sth::Pppox::MACToDouble
proc ::sth::sthCore::macToDouble {mac} {
	return [::sth::Pppox::MACToDouble $mac]
}

#replace ::sth::sthCore::doubleToMac by ::sth::Pppox::DoubleToMAC
proc ::sth::sthCore::doubleToMac {macDouble} {
	return [::sth::Pppox::DoubleToMAC $macDouble]
}


###/*! \ingroup gen_utils
###\fn macStep ()
###\brief Steps the MAC address based on step and count
###
###This procedure generates a MAC address based on start, step, and count
###
###\author 
###*/
###
###macStep ();
###
proc ::sth::sthCore::macStep {startMac stepMac count} {
    return [doubleToMac [expr {[::sth::Pppox::MACToDouble $startMac] + ([::sth::Pppox::MACToDouble $stepMac] * $count)}]]
}

###/*! \ingroup gen_utils
###\fn prefixLengthToIpMask ()
###\brief Converts the specified prefix length to IP mask format
###
###This procedure converts the specified prefix length to either IPv4 or IPv6 format
###
###\author 
###*/
###
###prefixLengthToIpMask ();
###
proc ::sth::sthCore::prefixLengthToIpMask {prefix {ipVersion 4}} {
    switch -- $ipVersion {
        4 {
            set bits   8
            set tokens 4
            set maxlen 32
        }
        6 {
            set bits   16
            set tokens 8
            set maxlen 128
        }
        default { error "unknown ip version: $ipVersion" }
    }
    if {$prefix < 0 || $prefix > $maxlen} {
        error "prefix must be in the range 0 to $maxlen"
    }
    
    set n [expr {$prefix / $bits}] ;# significant tokens
    set r [expr {$prefix % $bits}] ;# remaining significant bits

    # init all binary tokens to 0
    for {set i 1} {$i <= $tokens} {incr i} {
        set b$i [string repeat 0 $bits]
    }

    # set all significant binary tokens to 1
    for {set i 1} {$i <= $n} {incr i} {
        set b$i [string repeat 1 $bits]
    }
    # set any remaining significant bits to 1
    if {$r > 0} {
        set b$i [string repeat 1 $r][string repeat 0 [expr {$bits-$r}]]
    }
    
    # create the mask
    set mask ""
    if {[string match -nocase "4" $ipVersion]} {
        for {set i 1} {$i <= $tokens} {incr i} {
            upvar 0 b$i token
            append mask "[binToInt $token]."
        }
        set mask [string trimright $mask .]
    } else {
        for {set i 1} {$i <= $tokens} {incr i} {
            upvar 0 b$i token
            append mask "[binToHex $token]:"
        }
        set mask [string trimright $mask :]
    }
    return $mask
}

###/*! \ingroup gen_utils
###\fn binToInt ()
###\brief Converts the binary value to integer
###
###This procedure converts the binary value to integer
###
###\author 
###*/
###
###binToInt ();
###
proc ::sth::sthCore::binToInt {bits {order lohi}} {
    # Convert a binary value into an integer.
    set result 0
    if {$order == "lohi"} {
        set bits [string trimleft $bits 0]
    }

    set i 0
    while {$bits != ""} {
        if {$order == "hilo"} {
            set bit [string index $bits 0]
            set bits [string replace $bits 0 0]
            set result [expr {$result + ($bit * int(pow(2,$i)))}]
        } else {
            set bit [string index $bits 0]
            set bits [string range $bits 1 end]
            set result [expr {($result << 1) + $bit}]
        }
        incr i
    }
    
    return $result
}

###/*! \ingroup gen_utils
###\fn binToHex ()
###\brief Converts the binary value to hex
###
###This procedure converts the binary value to hex
###
###\author 
###*/
###
###binToHex ();
###
proc ::sth::sthCore::binToHex {bin} {
    set bytes [expr {ceil(([string length $bin]/8.0))}]
    set padLen [expr {int([expr {$bytes * 8}] - [string length $bin])}]
    set bin [join [list [string repeat 0 $padLen] $bin] ""]
    binary scan [binary format B* $bin] H* result
    return $result
}


###/*! \ingroup gen_utils
###\fn getIpv4Gw ()
###\brief get the gw addr according to the ipv4 addr
###
###This procedure produce the gw addr according to the ipv4 addr
###
###\author Fei Cheng
###*/
###
###getIpv4Gw ();
###
proc ::sth::sthCore::getIpv4Gw {addr} {
    set octes [split $addr .]
    set gwOctes [lreplace $octes 3 3 1]
    set gwAddr [join $gwOctes .]
    return $gwAddr
}

###/*! \ingroup gen_utils
###\fn intToIpv4Address ()
###\brief Converts the integer value to IPv4 address format
###
###This procedure converts nteger value to IPv4 address format
###
###\author Xiaozhi, Liu
###*/
###
###intToIpv4Address ();
###
proc ::sth::sthCore::intToIpv4Address {intValue} {
	
    set ipAddress ""
    #convert integer to IPv4
    binary scan [binary format I* $intValue] B32 step
    for {set x 0; set y 7} {$y < 32} {} {
        set oct [string range $step $x $y]
        binary scan [binary format B32 $oct] i ip
        lappend ipAddress $ip
        set x [expr {$x+8}]
        set y [expr {$y+8}]
    }
    set newIPAddr [join $ipAddress .]
    
    return $newIPAddr
}

proc ::sth::sthCore::processErrorSub { errMsg } {
    ::sth::sthCore::log error $errMsg
    error $errMsg
}

proc ::sth::sthCore::isHandleValid { handle objType } {
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
    
	if {[catch {::sth::sthCore::invoke stc::get $handle} getStatus]} {
		::sth::sthCore::processErrorSub "Input STC handle: $handle is not valid."
	}
    
    if {[string first [string tolower $objType] $handle] != 0 } {
        ::sth::sthCore::processErrorSub "Input STC handle: $handle is not Type: $objType."
    }
    
    return $SUCCESS
}


proc ::sth::sthCore::prefixLengthToIpStepValue {ip_version prefixLength intStepValue} {
    set retValue ""
    if {$ip_version ==4} {
        # To be done
    } else {
        set cnt [expr 128 - $prefixLength]
        
        set reminder [expr $cnt % 16]
        set divider [expr $cnt / 16]
        
        set part 1
        for {set i 1} {$i <= $reminder} {incr i} {
            set part [expr 2 * $part]
        }
        
        set part [expr $intStepValue * $part]
        set part [format "%X" $part]
        set part [split $part {}]
        
        for {set i 1} {$i <= $divider} {incr i} {
            if {$i ==1 } {
                set retValue "0"
            } else {
                set retValue "0:$retValue"
            }
        }
        
        for {set i [llength $part]} {$i >= 1 } {set i [expr $i - 1]} {
            if { [expr ([llength $part] - $i) % 4] == 0 } {
                if {$retValue != ""} {
                    set retValue ":$retValue"
                }
            }
            set char [lindex $part [expr $i - 1]]
            set retValue "$char$retValue"
        }
        
        if {[regexp -all {:} $retValue] == 6 } {
            set retValue "0:$retValue"
        } elseif {[regexp -all {:} $retValue] < 6} {
            set retValue "::$retValue"
        } elseif {[regexp -all {:} $retValue] > 7} {
            return -code error "Integer step value $intStepValue for IPv6 Prefix Length $prefixLength is un-available."
        }
        
        set retValue [::sth::sthCore::normalizeIPv6Addr $retValue]
    }
    
    return $retValue
}

###}; //ending for namespace comment for doc
