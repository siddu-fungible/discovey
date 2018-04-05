namespace eval ::sth::fcoetraffic:: {
    array set arrayFCoESbBlockHandle {}
    array set arrayFIPSbBlockHandle {}
    set commonsvcparams {
        fcphversionhigh fcphversionlow buffertobuffercredit commfeatures rcvdatasize totalconcurrentsequence reloffsetbyinfocategory edtov
    }
    set class1svcparams {
        serviceoptions ictl rctl recdatafieldsize currentsequences endtoendcredit openseqperexchange reserved1 reserved2
    }
    set class2svcparams {
        serviceoptions ictl rctl recdatafieldsize currentsequences endtoendcredit openseqperexchange reserved1 reserved2
    }
    set class3svcparams {
        serviceoptions ictl rctl recdatafieldsize currentsequences endtoendcredit openseqperexchange reserved1 reserved2
    }
    set class4svcparams {
        serviceoptions ictl rctl recdatafieldsize currentsequences endtoendcredit openseqperexchange reserved1 reserved2
    }    
    set classfsvcparams {
        val reserved1 reserved2 r xii reserved3 recvdatafieldsize concseq  endtoendcredit openseqperexchange reserved4
    }
    set class1interconnectportparams {
        val imx xps lks reserved recvdatafieldsize
    }
    set class2interconnectportparams {
        val rrr seq reserved recvdatafieldsize
    }
    set class3interconnectportparams {
        val rrr seq reserved recvdatafieldsize
    }
    set islflowcontrol {
        islflowcontrolmode islflowcontrollength bbcredit compatibilityparameters 
    }
    set domainid_lists {
        domainid reserved1 reserved2 switchname 
    }
    set multiid_lists {
        multicastgroupnumber  reserved1  reserved2 
    }
    set vendorescid {
        type length reserved vendorid
    }
    set lsr_lists {
        lsrtype reserved1 lsrage reserved2 linkstateid advdomainid lsincarnationnumber reserved
    }
    set fspfheader {
        fspfversion obsoletedfcsw4 authenticationtype reserved originatingdomainid authentication 
    }
    set lsh_lists {
        lsrtype reserved1 lsrage reserved2 linkstateid advdomainid lsincarnationnumber 
    }
    set ctiu {
        revision inid gstype gssubtype options reserved commandrespondcode maximumresidualsize fragmentid reserved 
    }
    set portidentifier_list {
        control portidentifier
    }
    set portname_list {
        control portidentifier reserved portname 
    }

    set nodename_list {
        control portidentifier reserved nodename 
    }
    set basiczoning_list {
        activezonesetlength zonesetdatabaseobjectlength
    }
    set enhancezoning_list {
        reserved enhancedzoningflags activezonesetlength zonesetdatabaseobjectlength
    }
    set validList {
        vendorescid lsr_lists fspfheader lsh_lists domainid_lists multiid_lists ctiu portidentifier_list portname_list nodename_list enhancezoning_list basiczoning_list \
        commonsvcparams class1svcparams class2svcparams class3svcparams class4svcparams classfsvcparams \
        class1interconnectportparams class2interconnectportparams class3interconnectportparams islflowcontrol \
    }
        
}
proc ::sth::fcoe_traffic_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fcoetraffic::userArgsArray
    array unset ::sth::fcoetraffic::userArgsArray
    array set ::sth::fcoetraffic::userArgsArray {}
    set _hltCmdName "fcoe_traffic_config"
    set underScore "_"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    keylset returnKeyedList procName $procName
    
    ::sth::sthCore::Tracker "::sth::fcoe_traffic_config" $args
    #this is a way to introduce non-user args into userArgsArray and sortedSwitchPriorityList
    #lappend args -h_rctl 22 -h_csctl 00
    
	set retVal [catch {
		if {[catch {::sth::sthCore::commandInit ::sth::fcoetraffic::fcoetrafficTable $args ::sth::fcoetraffic:: $_hltCmdName ::sth::fcoetraffic::userArgsArray ::sth::fcoetraffic::sortedSwitchPriorityList} err]} {
			::sth::sthCore::processError returnKeyedList "Error trying to initialize fcoe command: $err"
			return $returnKeyedList
		}
		
		if {[regexp -nocase {create|modify} $userArgsArray(mode)] && (![info exists ::sth::fcoetraffic::userArgsArray(pl_id)] )} {
			::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires -pl_id for create/modify"
			return $returnKeyedList
		}
		if {[info exists ::sth::fcoetraffic::userArgsArray(pl_id)] && [regexp -nocase fcpcmnd $userArgsArray(pl_id)]&& (![info exists userArgsArray(pl_cdbtype)])} {
			::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires -pl_cdbtype when pl_id is fcpcmnd"
			return $returnKeyedList
		}
		
		foreach hname {"sof" "eof" "pl_cdbtype" "pl_porttype"} {
			if {[info exist userArgsArray($hname)]} {
				set stcvalue  [::sth::sthCore::getFwdmap      ::sth::fcoetraffic::  fcoe_traffic_config  $hname $userArgsArray($hname)]
				set userArgsArray($hname)  $stcvalue
			}
		}
		if {[info exist userArgsArray(pl_id)]} {
			regsub -all {\s+} $userArgsArray(pl_id) " " pl_id
			regsub -all {^\s*|\s*$} $pl_id  "" pl_id
			foreach id [split $pl_id] {
				#set h_rctl  [::sth::sthCore::getFwdmap      ::sth::fcoetraffic::  fcoe_traffic_config  h_rctl $id]
				#set userArgsArray(h_rctl)  $h_rctl
				#set h_csctl  [::sth::sthCore::getFwdmap      ::sth::fcoetraffic::  fcoe_traffic_config  h_csctl $id]
				#set userArgsArray(h_csctl)  $h_csctl
				set stcvalue  [::sth::sthCore::getFwdmap      ::sth::fcoetraffic::  fcoe_traffic_config  pl_id $id]
				if {[regexp -nocase $id fcpcmnd]} {set stcvalue "$stcvalue-$userArgsArray(pl_cdbtype)"}
				lappend pl $stcvalue
			}
			set userArgsArray(pl_id)  [string tolower $pl]
		}
		
		if {[catch {::sth::fcoetraffic::${_hltCmdName}_${userArgsArray(mode)} returnKeyedList} err]} {
			::sth::sthCore::processError returnKeyedList "$procName Error: $err"
			return $returnKeyedList
		}

		if {[catch {::sth::sthCore::doStcApply } err ]} {
			::sth::sthCore::processError returnKeyedList "$procName Error: $err"
			return $returnKeyedList
		}
		keylset returnKeyedList streamid $userArgsArray(handle)
	} returnedString]
	 
    if {$retVal} {
        if {$returnedString ne ""} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        }
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::fip_traffic_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fcoetraffic::userArgsArray
    array unset ::sth::fcoetraffic::userArgsArray
    array set ::sth::fcoetraffic::userArgsArray {}
    set _hltCmdName "fip_traffic_config"
    set underScore "_"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    keylset returnKeyedList procName $procName
    
    ::sth::sthCore::Tracker "::sth::fip_traffic_config" $args

	set retVal [catch {
		if {[catch {::sth::sthCore::commandInit ::sth::fcoetraffic::fcoetrafficTable $args ::sth::fcoetraffic:: $_hltCmdName ::sth::fcoetraffic::userArgsArray ::sth::fcoetraffic::sortedSwitchPriorityList} err]} {
			::sth::sthCore::processError returnKeyedList "Error trying to initialize fcoe command: $err"
			return $returnKeyedList
		}
		
		if {[regexp -nocase {create|modify} $userArgsArray(mode)] && (![info exists ::sth::fcoetraffic::userArgsArray(dl_id)])} {
			::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires -dl_id for create/modify"
			return $::sth::sthCore::FAILURE
		}
		
		if {[info exist userArgsArray(dl_id)]} {
			regsub -all {\s+} $userArgsArray(dl_id) " " dl_id
			regsub -all {^\s*|\s*$} $dl_id  "" dl_id
			foreach id [split $dl_id] {
				set stcvalue  [::sth::sthCore::getFwdmap      ::sth::fcoetraffic::  fip_traffic_config  dl_id $id]
				lappend dl $stcvalue
			}
			set userArgsArray(dl_id)  [string tolower $dl]
		}
		
		set mode $userArgsArray(mode)
		if {[catch {::sth::fcoetraffic::${_hltCmdName}_${mode} returnKeyedList} err]} {
			::sth::sthCore::processError returnKeyedList "$procName Error: $err"
			return $returnKeyedList
		}

		if {[catch {::sth::sthCore::doStcApply } err ]} {
			::sth::sthCore::processError returnKeyedList "$procName Error: $err"
			return $returnKeyedList
		}
		keylset returnKeyedList streamid $userArgsArray(handle)
	} returnedString]
	 
    if {$retVal} {
        if {$returnedString ne ""} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        }
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}
