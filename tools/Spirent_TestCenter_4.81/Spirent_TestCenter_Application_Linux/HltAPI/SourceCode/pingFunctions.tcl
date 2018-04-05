namespace eval ::sth::Ping {
}
namespace eval ::sth::sthCore:: {}

proc ::sth::Ping::procPingPort_Handle { } {
    set errMsg ""
    upvar pingKeyedList pingKeyedList;
    upvar 1 userArgsArray userArray;
    variable ::sth::Session::PORTHNDLIST
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    set listOfpHandles $userArray(port_handle)
    if {$listOfpHandles == "all"} {
		return $::sth::sthCore::SUCCESS;
    }
    foreach portHnd $listOfpHandles {
		if {[info exists ::sth::Session::PORTHNDLIST($portHnd)]} {
		} else {
            ::sth::sthCore::processError pingKeyedList "Internal Command Error: port_handle $portHnd is not valid" {}
            return -code 1 -errorcode -1 $errMsg;
		}
    }
    return $::sth::sthCore::SUCCESS;
}

proc ::sth::Ping::procPingHost { } {
    #puts "Inside Ping Host";
    set errMsg "";
    upvar pingKeyedList pingKeyedList;
    upvar 1 userArgsArray userArray;
    
    set pingporthandle $userArray(port_handle)
     set pingaddress $userArray(host)
     if {[info exists userArray(interval)]} {
        set ::sth::Ping::pinginterval $userArray(interval)
     }      
     if {[info exists userArray(count)]} {
        set ::sth::Ping::pingcount $userArray(count)
     }
     
     if {[info exists userArray(size)]} {
        set ::sth::Ping::pingsize $userArray(size)
     } 
     
	 set ::sth::Ping::pinghost [::sth::sthCore::invoke stc::create "Host" -under $::sth::sthCore::GBLHNDMAP(project) "-name HostPing"]
     set srcAddress [split $pingaddress .]
     if {[llength $srcAddress] >= 3} {
        set tempAddress [expr [lindex $srcAddress 3] + 1]
     	set srcAddress [lreplace $srcAddress 3 3 $tempAddress]
     	set srcAddress [join $srcAddress .]
     }
     
     set pingEthII [::sth::sthCore::invoke stc::create "ETHIIIf" -under $::sth::Ping::pinghost]
     
     # Add support for Vlan id
     if {[info exists userArray(vlan_id)]} {
        set vlanId $userArray(vlan_id)
        set pingVlanIf [::sth::sthCore::invoke stc::create "VlanIf" -under $::sth::Ping::pinghost "-VlanId $vlanId"]
	}
	set pingIpv4 [::sth::sthCore::invoke stc::create "Ipv4If" -under $::sth::Ping::pinghost "-Address $srcAddress -Gateway $pingaddress"]
	::sth::sthCore::invoke stc::config $::sth::Ping::pinghost "-AffiliationPort-targets $pingporthandle"
	::sth::sthCore::invoke stc::config $::sth::Ping::pinghost "-TopLevelIf-targets $pingIpv4"
	::sth::sthCore::invoke stc::config $::sth::Ping::pinghost "-PrimaryIf-targets $pingIpv4"
 
    # Add support for Vlan id
	if {[info exists userArray(vlan_id)]} {
		::sth::sthCore::invoke stc::config $pingVlanIf "-StackedOnEndpoint-targets $pingEthII"
		set lowerIf $pingVlanIf
	} else {
	
		set lowerIf $pingEthII
	}
	::sth::sthCore::invoke stc::config $pingIpv4 "-StackedOnEndpoint-targets $lowerIf"
    append ::sth::Ping::pingCommandList " -DeviceList $::sth::Ping::pinghost -TimeInterval $::sth::Ping::pinginterval"
}

proc ::sth::Ping::procPingOptional { } {
    #puts "Inside ping optional"
}


