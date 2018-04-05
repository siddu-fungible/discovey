namespace eval ::sth::fcoe:: {
    proc ::sth::fcoe::fcoe_config_create { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {![info exists userArgsArray(port_handle)]} {
            set result "The -port_handle is required when \"-mode create\" is used."
            return -code 1 -errorcode -1 $result
        }
        set hltPort $userArgsArray(port_handle)
        
        set fcoeHostConfigParamList ""
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        
        switch -exact -- $userArgsArray(encap) {
            "ethernet_ii_vlan" {
                set IfStack "FcIf VlanIf EthIIIf"
                set IfCount "1 1 1"
            }
            "ethernet_ii_qinq" {
                set IfStack "FcIf VlanIf VlanIf EthIIIf"
                set IfCount "1 1 1 1"
            }
            "ethernet_ii" {
                set IfStack "FcIf EthIIIf"
                set IfCount "1 1"
            }
        }
        
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle)]
        set host $DeviceCreateOutput(-ReturnList)

        if {[info exists userArgsArray(vnport_count)]} {::sth::sthCore::invoke stc::config $host "-deviceCount $userArgsArray(vnport_count)"}
        
        set IfStack [::sth::sthCore::invoke stc::get $host -children]
        foreach ele $IfStack  {
            lappend configHandleList  $ele
        }
        set ::sth::fcoe::arrayHostCurrentIfStack($host) $IfStack
        set FcoeGlobalParams [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) "-children-FcoeGlobalParams"]
        if {$FcoeGlobalParams eq ""} {
		set FcoeGlobalParams [::sth::sthCore::invoke stc::create FcoeGlobalParams -under $::sth::GBLHNDMAP(project)]
        }
set fcoeHostConfig [::sth::sthCore::invoke stc::create FcoeHostConfig -under $host]
        lappend configHandleList $host $FcoeGlobalParams $fcoeHostConfig
        ::sth::sthCore::invoke stc::config $fcoeHostConfig "-UsesIf-targets [::sth::sthCore::invoke stc::get $host -children-fcif]"
        if {[catch {::sth::fcoe::processCofigAttr vlan $configHandleList returnKeyedList} err]} {
            ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
            return $::sth::sthCore::FAILURE
        }
        
        if {[catch {::sth::fcoe::processCofigAttr others $configHandleList returnKeyedList} err]} {
            ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
            return $::sth::sthCore::FAILURE
        }
        
        keylset returnKeyedList handle $host;# will now be used for traffic    
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fcoe::fcoe_config_modify { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
        variable sortedSwitchPriorityList
    
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
    
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {![info exists userArgsArray(handle)]} {
            set result "The -handle is required when \"-mode modify\" is used."
            return -code 1 -errorcode -1 $result
        }
        
        foreach ele $sortedSwitchPriorityList {
            set switchName [lindex $ele 1]
            set newUserArgsArray($switchName) $userArgsArray($switchName)
        }
        unset userArgsArray
        array set userArgsArray [array get newUserArgsArray]
        
        foreach host $userArgsArray(handle) {
            if {![info exists ::sth::fcoe::arrayHostCurrentIfStack($host)] || $::sth::fcoe::arrayHostCurrentIfStack($host) == ""} {
                ::sth::sthCore::processError returnKeyedList "$host is not a valid FCoE device"
                return $::sth::sthCore::FAILURE
            }

            set CurrentIfStack [set ::sth::fcoe::arrayHostCurrentIfStack($host)]
            if {[info exists userArgsArray(encap)]}  {
                set len [llength [lsearch -regexp -all $CurrentIfStack vlanif]]
                switch -exact -- $userArgsArray(encap) {
                    "ethernet_ii" {
                        regsub -all -nocase {vlanif\d+} $CurrentIfStack  "" IfStack
                    }
                    "ethernet_ii_vlan" {
                        if {$len == 2} {
                            regsub -nocase {vlanif\d+} $CurrentIfStack  "" IfStack
                        } elseif {$len ==1} {
                            set IfStack $CurrentIfStack
                        } else {
							set VlanIf1 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack [linsert $CurrentIfStack [lsearch -regexp $CurrentIfStack ethiiif] $VlanIf1]
                        }
                    }
                    "ethernet_ii_qinq" {
                        if {$len == 2} {
                            set IfStack $CurrentIfStack
                        } elseif {$len == 1} {
							set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack [linsert $CurrentIfStack [lsearch -regexp $CurrentIfStack ethiiif] $VlanIf2]
                        } else {
							set VlanIf1 [::sth::sthCore::invoke stc::create VlanIf -under $host]
							set VlanIf2 [::sth::sthCore::invoke stc::create VlanIf -under $host]
                            set IfStack [linsert $CurrentIfStack [lsearch -regexp $CurrentIfStack ethiiif] $VlanIf1 $VlanIf2]
                        }
                    }
                }
            } else {
                set IfStack $CurrentIfStack
            }
    
            if {[catch {::sth::sthCore::invoke stc::perform IfStackReplace  -DeviceList $host -NewIfStack $IfStack  -CurrentIfStack $CurrentIfStack} err]} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                return $::sth::sthCore::FAILURE
            }
            set ::sth::fcoe::arrayHostCurrentIfStack($host) $IfStack
            set fcHnd [::sth::sthCore::invoke stc::get $host -children]
            set FcoeGlobalParams [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) "-children-FcoeGlobalParams"]
            if {$FcoeGlobalParams eq ""} {
		set FcoeGlobalParams [::sth::sthCore::invoke stc::create FcoeGlobalParams -under $::sth::GBLHNDMAP(project)]
        	}
            foreach ele $fcHnd  {
                lappend configHandleList  $ele
            }
            lappend configHandleList $FcoeGlobalParams $host
            
            if {[info exists userArgsArray(vnport_count)]} {
                ::sth::sthCore::invoke stc::config $host "-DeviceCount $userArgsArray(vnport_count)"
            } else {
                set userArgsArray(vnport_count) [::sth::sthCore::invoke stc::get $host -DeviceCount]
            }
            
            if {[catch {::sth::fcoe::processCofigAttr vlan $configHandleList returnKeyedList} err]} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                return $::sth::sthCore::FAILURE
            }
            if {[catch {::sth::fcoe::processCofigAttr others $configHandleList returnKeyedList} err]} {
                ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                return $::sth::sthCore::FAILURE
            }
        }
        keylset returnKeyedList handle $userArgsArray(handle)
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fcoe::fcoe_config_reset { returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
        variable sortedSwitchPriorityList
    
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {![info exists userArgsArray(handle)]} {
           ::sth::sthCore::processError returnKeyedList "The -handle is required when \"-mode reset\" is used."
            return $::sth::sthCore::FAILURE
        }
        
        foreach host $userArgsArray(handle) {
            if {![info exists ::sth::fcoe::arrayHostCurrentIfStack($host)] || $::sth::fcoe::arrayHostCurrentIfStack($host) == ""} {
                ::sth::sthCore::processError returnKeyedList "$host is not a valid FCoE device"
                return $::sth::sthCore::FAILURE
            }
            set handle [::sth::sthCore::invoke stc::get $host -affiliationport-targets]
            foreach streamblock [::sth::sthCore::invoke stc::get $handle -Children-StreamBlock ] {
                set sb_dstbding [::sth::sthCore::invoke stc::get $streamblock -DstBinding-targets]
                set sb_srcbding [::sth::sthCore::invoke stc::get $streamblock -SrcBinding-targets]
                if {($sb_dstbding == "" )|| ($sb_srcbding == "")} {
                    if {[catch {::sth::sthCore::invoke stc::delete $streamblock} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error: $err"
                        return $::sth::sthCore::FAILURE
                    }
                }
            }
            if {[catch {::sth::sthCore::invoke stc::delete $host} err]} {
                ::sth::sthCore::processError returnKeyedList "Error: $err"
                return $::sth::sthCore::FAILURE
            }
            set ::sth::fcoe::arrayHostCurrentIfStack($host) ""
        }
        return $::sth::sthCore::SUCCESS
    }
    

    proc ::sth::fcoe::processFcMapConfig {configHandleList switchName switchValue returnInfoVarName} {
        upvar 1 $switchValue  value
        
        set value 0x$value
        return $::sth::sthCore::SUCCESS
    }
    
    proc ::sth::fcoe::processWWPNCountConfig {configHandleList switchName switchValue returnInfoVarName} {
        upvar 1 $switchValue  value
        
        variable userArgsArray
        set host [lindex $configHandleList [lsearch -regexp $configHandleList ^host]]
        set devicecount [::sth::sthCore::invoke stc::get $host -deviceCount]
        set value [expr $devicecount/$value - 1]
        if {$value<-1} {
            ::sth::sthCore::processError returnKeyedList "-$switchName should be equal or less than -vnport_count"
            return $::sth::sthCore::FAILURE
        
        }
        return $::sth::sthCore::SUCCESS
    }
    proc ::sth::fcoe::processCofigAttr {type configHandleList returnInfoVarName} {
        set procName [lindex [info level [info level]] 0]
        upvar 1 $returnInfoVarName returnKeyedList
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable userArgsArray
        variable sortedSwitchPriorityList
        
        if {$type == "vlan"} {
            if {[lsearch -regexp $configHandleList vlanif] != -1 } {
                set indexs [lsearch -regexp -all $configHandleList vlanif]
                set len [llength $indexs]
                set host [lindex $configHandleList [lsearch -regexp $configHandleList host]]
                if {$len == 1} {
                    set vlanif [lindex $configHandleList $indexs]
                    ::sth::sthCore::invoke stc::config $vlanif "-idstep 0"
                    foreach {stcattr hname} {VlanId vlan_id Priority vlan_pri Cfi vlan_cfi } {
                        if {[info exists userArgsArray($hname)]} {
                            ::sth::sthCore::invoke stc::config $vlanif "-$stcattr $userArgsArray($hname)"
                        }
                    }
                } elseif {$len == 2} {
                    set vlanif2 [lindex $configHandleList [lindex $indexs 1]]
                    set vlanif1 [lindex $configHandleList [lindex $indexs 0]]
                    ::sth::sthCore::invoke stc::config $vlanif2 "-idstep 0"
                    ::sth::sthCore::invoke stc::config $vlanif1 "-idstep 0"
                    foreach {stcattr hname} {VlanId vlan_id_outer Priority vlan_pri_outer Cfi vlan_cfi_outer } {
                        if {[info exists userArgsArray($hname)]} {
                            ::sth::sthCore::invoke stc::config $vlanif2 "-$stcattr $userArgsArray($hname)"
                        }
                    }
                    foreach {stcattr hname} {VlanId vlan_id Priority vlan_pri Cfi vlan_cfi } {
                        if {[info exists userArgsArray($hname)]} {
                            ::sth::sthCore::invoke stc::config $vlanif1 "-$stcattr $userArgsArray($hname)"
                        }
                    }
                }
            }
        } else {
            foreach key $sortedSwitchPriorityList {
                set switchName [lindex $key 1]
                set switchValue $userArgsArray($switchName)
                set stcObj     [::sth::sthCore::getswitchprop ::sth::fcoe:: fcoe_config $switchName stcobj]
                set stcAttr     [::sth::sthCore::getswitchprop ::sth::fcoe:: fcoe_config $switchName stcattr]
                set procFunc [::sth::sthCore::getModeFunc ::sth::fcoe:: fcoe_config $switchName create]
                if {$stcAttr == "_none_"} { continue }
                if {[set index [lsearch -regexp [string tolower $configHandleList] $stcObj\\d+]] !=-1} {
                    if {$procFunc != ""} {
                        if {[catch {$procFunc $configHandleList switchName switchValue returnKeyedList} err]} {
                            ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
                            return $::sth::sthCore::FAILURE
                        }
                    }
                    set configHandle [lindex $configHandleList $index]
                    lappend ${configHandle}_configList -$stcAttr $switchValue
                }
            }
        }
        
        foreach handle [split $configHandleList] {
            if {[info exists ${handle}_configList] && ([set ${handle}_configList] != "")} {
                if {[catch {::sth::sthCore::invoke stc::config  $handle "[set ${handle}_configList]"} err]} {
                    ::sth::sthCore::processError returnKeyedList "config $handle Error: $err" {}
                    return $::sth::sthCore::FAILURE
                }
            }
        }
        return $::sth::sthCore::SUCCESS
    }
}
