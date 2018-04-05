namespace eval ::sth:: {}
namespace eval ::sth::Ping {
    set pingCommandList "-ExecuteSynchronous True"
    set pinghost ""
    set pinginterval 1
    set pingsize 1
    set pingcount 1
}

proc ::sth::emulation_ping { args } {
    ::sth::sthCore::Tracker ::sth::emulation_ping $args
    set hltCmdName "emulation_ping"
    
     set errMsg "";
     set pingKeyedList ""
     variable userArgsArray
     array unset userArgsArray
     array set userArgsArray {};
     variable sortedSwitchPriorityList {};
     variable ::sth::sthCore::SUCCESS
     variable ::sth::sthCore::FAILURE

     ::sth::sthCore::log debug "{Calling sth::emulation_ping}"
     ::sth::sthCore::log info "{Generating ping table}"
     if {[catch {::sth::sthCore::commandInit ::sth::Ping::pingTable $args \
                                  ::sth::Ping:: \
                                  emulation_ping \
                                  userArgsArray \
                                  sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError pingKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg" {}
        return $pingKeyedList
     }
    
	set retVal [catch {
		if {!([info exists userArgsArray(handle)] || [info exists userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
			return -code error $returnKeyedList   
		}

		if {([info exists userArgsArray(handle)] && [info exists userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
			return -code error $returnKeyedList   
		}

		if {[info exists userArgsArray(handle)]} {
			set hostHandle $userArgsArray(handle)

			set portHandle [::sth::sthCore::invoke "stc::get $hostHandle -AffiliationPort-targets"]

			#get the initial string in PingReport, used to check if the PingResults updated later.
			set pingreport [::sth::sthCore::invoke stc::get $portHandle.PingReport "-PingResult"]
			set tempReport $pingreport
			
			 if {[info exists userArgsArray(interval)]} {
				set ::sth::Ping::pinginterval $userArgsArray(interval)
			 }      
			 
			 if {[info exists userArgsArray(count)]} {
				set ::sth::Ping::pingcount $userArgsArray(count)
			 }
			
			 set hostIp $userArgsArray(host)
			 if {[regexp {\:} $hostIp]} {
					 set pingIpDestAddr PingIpv6DstAddr
			 } else {
					 set pingIpDestAddr PingIpv4DstAddr
			 }
			 
			 set hostIp $userArgsArray(host)
			 ::sth::sthCore::invoke stc::perform PingStart -DeviceList $hostHandle -$pingIpDestAddr $hostIp -TimeInterval $::sth::Ping::pinginterval -FrameCount $::sth::Ping::pingcount -WaitForPingToFinish FALSE
		} else {
			foreach sortedSwitch $sortedSwitchPriorityList {
			   set hltObject [lindex $sortedSwitch end]
			   if {$::sth::Ping::emulation_ping_supported($hltObject) == "false"} {
					   ::sth::sthCore::log warn "{ignoring unsupported attribute $hltObject}"
					   continue
			   }
			   set funcToCall $::sth::Ping::emulation_ping_procfunc($hltObject)
			   if {[string equal $funcToCall "_none_"]} {
			   } else {
					   if {[catch {set cmdReturn [eval $funcToCall]} errMsg]} {
							   ::sth::sthCore::processError pingKeyedList "$funcToCall Failed: Error while processing $hltObject: $errMsg" {}
							   return -code error $pingKeyedList;
					   }
			   }
			}
			
			::sth::sthCore::doStcApply
			
			#####bellow are getting ping results####
		   
		   #get the initial string in PingReport, used to check if the PingResults updated later.
		   set pingreport [::sth::sthCore::invoke stc::get $userArgsArray(port_handle).PingReport "-PingResult"]
		   set tempReport $pingreport
		   
			#need to do the arp before start the ping, else the first ping packet will be dropped by STC.
		    ::sth::sthCore::invoke stc::perform  ArpNdStart -HandleList $::sth::Ping::pinghost
			::sth::sthCore::invoke stc::perform PingStart -DeviceList $::sth::Ping::pinghost -TimeInterval $::sth::Ping::pinginterval -FrameCount $::sth::Ping::pingcount -WaitForPingToFinish FALSE
			set portHandle $userArgsArray(port_handle)
		}

		set pingStatus [::sth::sthCore::invoke stc::get $portHandle.PingReport -PingStatus]
			 
		 set pingReportList "" 
		 while {$pingStatus == "INPROGRESS"} {
     		set pingreport [::sth::sthCore::invoke stc::get $portHandle.PingReport "-PingResult -PingStatus"]
			set pingStatus [lindex [split $pingreport " "] end]
			::sth::sthCore::log debug "pingStatus $pingStatus"
			
			set pingreport [lindex $pingreport 1]
			::sth::sthCore::log debug "new pingResults string: $pingreport"
				
			if {$pingreport == ""} {
				continue
			}
				
			if {$tempReport != $pingreport} {
				set tempReport $pingreport
				append pingReportList $pingreport
			} 
		}
		::sth::sthCore::log debug "pingReportList: $pingReportList\npingreport: $pingreport"
	   #  set timetowait [expr $::sth::Ping::pinginterval * $::sth::Ping::pingcount * 1000]
	   #  after [expr $timetowait + 10000]
	   #  if {[catch {::sth::sthCore::doStcGetNew $userArgsArray(port_handle).PingReport -PingResult} pingreport]} {
	   #     ::sth::sthCore::processError pingKeyedList "::sth::sthCore::doStcPerform Failed: Error while getting Ping result: $pingreport" {}
	   #     #keylset pingKeyedList status $::sth::sthCore::FAILURE;
	   #		return $pingKeyedList;
	   #  }
		
		#results of each trip
		set singlePingReportList [lrange [split $pingReportList "\n"] 0 end-4]
		#set aggregatePingReportList [lrange [split $pingReportList "\n"] end-3 end]
		#only read value of the rtt line
		set aggregatePingReportList [lrange [split $pingReportList "\n"] end-1 end]
		set count 1    
		 foreach pingResultString $singlePingReportList {
			if {[string match "PING*" $pingResultString] || $pingResultString == ""} {
				continue
			}
			
			set byteReport fail
			set fromReport fail
			set IcmpSeqReport fail
			set TtlReport fail
			set timeReport fail
			#puts $pingResultString
			set checkString [lindex [split $pingResultString " "] 1]
			if {$checkString == "bytes"} {
				#ping successfully
				regexp "(.*): " $pingResultString match tempReportString
				if {[info exists tempReportString]} {
					set byteReport [lindex [split $tempReportString " "] 0]
					set fromReport [lindex [split $tempReportString " "] end]
					
					set tempReportString [lindex [split $pingResultString :] end]
					set tempReportString [split $tempReportString " "]
					set IcmpSeqReport [lindex [split [lindex $tempReportString 1] =] end]
					set TtlReport [lindex [split [lindex $tempReportString 2] =] end]
					set timeReport [lindex [split [lindex $tempReportString 3] =] end]
				}
			} 
			
			set pingKeyedList [::sth::sthCore::updateReturnInfo $pingKeyedList $count\.bytes "$byteReport" ]
			set pingKeyedList [::sth::sthCore::updateReturnInfo $pingKeyedList $count\.replyfrom "$fromReport"]
			set pingKeyedList [::sth::sthCore::updateReturnInfo $pingKeyedList $count\.icmp_seq "$IcmpSeqReport"]
			set pingKeyedList [::sth::sthCore::updateReturnInfo $pingKeyedList $count\.ttl "$TtlReport"]
			set pingKeyedList [::sth::sthCore::updateReturnInfo $pingKeyedList $count\.time "$timeReport"]
			
			incr count
		 }
		 #aggregate results
		 set minReport ""
		 set avgReport ""
		 set maxReport ""
		 foreach reportString $aggregatePingReportList {
			#if {[lindex $reportString 1] == "packets"} {
			#	set reportString [split $reportString ,]
			#	set txpackets [lindex [lindex $reportString 0] 0]
			#	set rxpackets [lindex [lindex $reportString 1] 0]
			#	set errpackets [string range [lindex [lindex $reportString 2] 0] 1 end]
			#	set percentage [lindex [lindex $reportString 2] 0]
			#}
			if {[lindex $reportString 0] == "rtt"} {
				set rttreport [split [lindex $reportString 3] "/"]
				set minReport [lindex $rttreport 0]
				set avgReport [lindex $rttreport 1]
				set maxReport [lindex $rttreport 2]
			}
			#if ping failed, min avg and max will return N/A
			if {[lindex $reportString 1] == "pipe"} {
				set minReport "N/A"
				set avgReport "N/A"
				set maxReport "N/A"            
			}
		 }
		#config tx, rx, pct_loss and percentage
		set txpackets [::sth::sthCore::invoke stc::get $portHandle.PingReport -AttemptedPingCount] 
		set rxpackets [::sth::sthCore::invoke stc::get $portHandle.PingReport -SuccessfulPingCount]
		set errpackets [expr $txpackets - $rxpackets]
		set percentage [format "%.1f%%" [expr double($errpackets)*100/$txpackets]]
		
		keylset pingKeyedList tx $txpackets
		keylset pingKeyedList rx $rxpackets
		keylset pingKeyedList pct_loss $percentage
		keylset pingKeyedList count $txpackets
		keylset pingKeyedList min $minReport
		keylset pingKeyedList avg $avgReport
		keylset pingKeyedList max $maxReport
	} returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError pingKeyedList $returnedString
    } else {
	    keylset pingKeyedList status $::sth::sthCore::SUCCESS
	}
     return $pingKeyedList
}
