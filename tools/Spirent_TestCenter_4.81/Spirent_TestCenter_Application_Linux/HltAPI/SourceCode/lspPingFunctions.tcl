namespace eval ::sth::lspPing {
}
proc ::sth::lspPing::emulation_lsp_ping_config_enable {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""

#judge if handle is configured    
    if {[info exists userArgsArray(handle)]} {
        set handle $userArgsArray(handle)
    } else {
        return -code 1 -errorcode -1 "handle needed for enable mode."
    }

#get handle of lspPingProtocolConfig    
    set lspPingProtocolConfigHnd [::sth::sthCore::invoke stc::get $handle -Children-lspPingProtocolConfig ]
    if {[string equal "" $lspPingProtocolConfigHnd]} {
        set lspPingProtocolConfigHnd [::sth::sthCore::invoke stc::create "lspPingProtocolConfig" -under $handle]
    }
#activate lspPingProtocolConfig
    ::sth::sthCore::invoke stc::config $lspPingProtocolConfigHnd -active "true"

#return
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    keylset myReturnKeyedList handle $lspPingProtocolConfigHnd
    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_config_disable {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""
    
    if {![::info exists ::sth::lspPing::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for disable mode."
    } else {
        set handle $userArgsArray(handle)
        set lspPingProtocolConfigHnd [::sth::sthCore::invoke stc::get $handle -Children-lspPingProtocolConfig ]
    }
    ::sth::sthCore::invoke stc::config $lspPingProtocolConfigHnd -active "false"
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_config_config {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""

    set lspPingGlobalConfigHnd [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-lspPingGlobalConfig ]
    if {[string equal "" $lspPingGlobalConfigHnd]} {
        set lspPingGlobalConfigHnd [::sth::sthCore::invoke stc::create "lspPingGlobalConfig" -under $::sth::GBLHNDMAP(project)]
    }

#invoke function in mode in table
    set functionsToRun [getFunctionToRun emulation_lsp_ping_config config] 
    foreach func $functionsToRun {
        $func $lspPingGlobalConfigHnd config
    }
#return
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_message_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""

#judge if handle is configured    
    if {[info exists userArgsArray(handle)]} {
        set handle $userArgsArray(handle)
    } else {
        return -code 1 -errorcode -1 "handle needed for create mode."
    }

    if {[info exists userArgsArray(message_type)]} {
        set message_type $userArgsArray(message_type)
    } else {
        return -code 1 -errorcode -1 "message_type needed for create mode."
    }
#if message_type is echo_request,and then
#get handle of ipv4EchoRequestConfig
#get/create ipv4EchoRequestConfig under lspPingProtocolConfig
    if {[string equal "echo_request" $message_type]} {
        set ipv4EchoRequestConfigHnd [::sth::sthCore::invoke stc::get $handle -Children-ipv4EchoRequestConfig ]
        if {[string equal "" $ipv4EchoRequestConfigHnd]} {
            set ipv4EchoRequestConfigHnd [::sth::sthCore::invoke stc::create "ipv4EchoRequestConfig" -under $handle]
        }

#invoke function in mode in table
        set functionsToRun [getFunctionToRun emulation_lsp_ping_message_config create] 
        foreach func $functionsToRun {
            $func $ipv4EchoRequestConfigHnd create
        }
#return
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
        keylset myReturnKeyedList handle $ipv4EchoRequestConfigHnd
    }

#if message_type is error_reply,and then
#get handle of echoreplyerrorgeneration
#get/create echoreplyerrorgeneration under lspPingProtocolConfig
    if {[string equal "error_reply" $message_type]} {
        set echoReplyErrorGenerationHnd [::sth::sthCore::invoke stc::get $handle -Children-echoReplyErrorGeneration ]
        if {[string equal "" $echoReplyErrorGenerationHnd]} {
            set echoReplyErrorGenerationHnd [::sth::sthCore::invoke stc::create "echoReplyErrorGeneration" -under $handle]
        }

#invoke function in mode in table
        set functionsToRun [getFunctionToRun emulation_lsp_ping_message_config create] 
        foreach func $functionsToRun {
            $func $echoReplyErrorGenerationHnd create
        }
#return
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
        keylset myReturnKeyedList handle $echoReplyErrorGenerationHnd
    }

    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_message_config_modify {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""

#judge if handle is configured    
    if {[info exists userArgsArray(handle)]} {
        set handle $userArgsArray(handle)
    } else {
        return -code 1 -errorcode -1 "handle needed for modify mode."
    }

#invoke function in mode in table
    set functionsToRun [getFunctionToRun emulation_lsp_ping_message_config modify] 
    foreach func $functionsToRun {
        $func $handle modify
    }
#return
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    keylset myReturnKeyedList handle $handle
    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_message_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""
    
    if {![::info exists ::sth::lspPing::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for delete mode."
    } else {
        set lspHndList $::sth::lspPing::userArgsArray(handle)
        foreach lsp $lspHndList {
            ::sth::sthCore::invoke ::sth::sthCore::invoke stc::delete $lsp
        }
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
        return $myReturnKeyedList
    }
}
proc ::sth::lspPing::emulation_lsp_ping_fec_config_create {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""

#judge if handle/label_type/fec_type are configured    
    if {[info exists userArgsArray(handle)]} {
        set handle $userArgsArray(handle)
    } else {
        return -code 1 -errorcode -1 "handle needed for create mode."
    }

    if {[info exists userArgsArray(label_type)]} {
        set label_type $userArgsArray(label_type)
        if {[string equal "middle" $label_type]} {
            if {[info exists userArgsArray(inner_fec_handle)]} {
                set inner_fecHnd $userArgsArray(inner_fec_handle)
            } else {
                return -code 1 -errorcode -1 "inner_fec_handle needed when label_type is middle."
            }
        }
        if {[string equal "outer" $label_type]} {
            if {[info exists userArgsArray(middle_fec_handle)]} {
                set middle_fecHnd $userArgsArray(middle_fec_handle)
            } else {
                return -code 1 -errorcode -1 "middle_fec_handle needed when label_type is outer."
            }
        }
    } else {
        return -code 1 -errorcode -1 "label_type needed for create mode."
    }
    if {[info exists userArgsArray(fec_type)]} {
        set fec_type $userArgsArray(fec_type)
    } else {
        return -code 1 -errorcode -1 "fec_type needed for create mode."
    }

#get fec handle via fec_type 
#get/create fec handle under ipv4EchoRequestConfig
    set fecHnd [::sth::sthCore::invoke stc::get $handle -Children-$fec_type ]
    if {[string equal "" $fecHnd]} {
        set fecHnd [::sth::sthCore::invoke stc::create $fec_type -under $handle]
    }
    set fecHnd [::sth::sthCore::invoke stc::get $handle -Children-$fec_type ]

#set relationship of inner/middle/outer fec
    if {[string equal "inner" $label_type]} {
         ::sth::sthCore::invoke stc::config $fecHnd -innermostfecinfo-sources $handle
         keylset myReturnKeyedList inner_fec_handle $fecHnd
        }

    if {[string equal "middle" $label_type]} {
         ::sth::sthCore::invoke stc::config $fecHnd -nextfecinfo-sources $inner_fecHnd
         keylset myReturnKeyedList middle_fec_handle $fecHnd
        }

    if {[string equal "outer" $label_type]} {
         ::sth::sthCore::invoke stc::config $fecHnd -nextfecinfo-sources $middle_fecHnd
         keylset myReturnKeyedList outer_fec_handle $fecHnd
        }
    
#invoke function in mode in table
    set functionsToRun [getFunctionToRun emulation_lsp_ping_fec_config create] 
    foreach func $functionsToRun {
        $func $fecHnd create
    }

    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_fec_config_modify {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""

#judge if handle is configured    
    if {[info exists userArgsArray(handle)]} {
        set handle $userArgsArray(handle)
    } else {
        return -code 1 -errorcode -1 "handle needed for modify mode."
    }

#invoke function in mode in table
    set functionsToRun [getFunctionToRun emulation_lsp_ping_fec_config modify] 
    foreach func $functionsToRun {
        $func $handle modify
    }
#return
    keylset myReturnKeyedList status $::sth::sthCore::SUCCESS
    keylset myReturnKeyedList handle $handle
    return $myReturnKeyedList
}
proc ::sth::lspPing::emulation_lsp_ping_fec_config_delete {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    variable ::sth::lspPing::userArgsArray
    variable ::sth::lspPing::keyedList
    set ::sth::lspPing::keyedList ""
    
    if {![::info exists ::sth::lspPing::userArgsArray(handle)]} {
        return -code 1 -errorcode -1 "handle needed for delete mode."
    } else {
        set lspHndList $::sth::lspPing::userArgsArray(handle)
        foreach lsp $lspHndList {
            ::sth::sthCore::invoke ::sth::sthCore::invoke stc::delete $lsp
        }
        keylset myReturnKeyedList status $::sth::sthCore::SUCCESS 
        return $myReturnKeyedList
    }
}
proc ::sth::lspPing::lspping_global_config {handle mode} {

    variable ::sth::lspPing::keyedList

    set optionValueList [getStcOptionValueList emulation_lsp_ping_config lspping_global_config $mode $handle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}
proc ::sth::lspPing::lspping_er_config {handle mode} {

    variable ::sth::lspPing::keyedList

    set optionValueList [getStcOptionValueList emulation_lsp_ping_message_config lspping_er_config $mode $handle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}
proc ::sth::lspPing::lspping_error_config {handle mode} {

    variable ::sth::lspPing::keyedList

    set optionValueList [getStcOptionValueList emulation_lsp_ping_message_config lspping_error_config $mode $handle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}
proc ::sth::lspPing::lspping_fec_config {handle mode} {

    variable ::sth::lspPing::keyedList

    set optionValueList [getStcOptionValueList emulation_lsp_ping_fec_config lspping_fec_config $mode $handle]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}
proc ::sth::lspPing::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::lspPing::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::lspPing:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::lspPing:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::lspPing:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                #check dependency
                #::sth::lspPing::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::lspPing::userArgsArray($opt)]} { continue }
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::lspPing:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::lspPing:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::lspPing:: $cmdType $opt $::sth::lspPing::userArgsArray($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::lspPing::userArgsArray($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::lspPing::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}
proc ::sth::lspPing::getFunctionToRun {mycmd mode} {

    variable sortedSwitchPriorityList
    set functionsToRun {}
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {

            # make sure the option is supported
             
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::lspPing:: $mycmd $switchname mode] "_none_"]} { 
                continue 
            }
            set func [::sth::sthCore::getModeFunc ::sth::lspPing:: $mycmd $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    return $functionsToRun
}
