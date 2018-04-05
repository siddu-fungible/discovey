namespace eval ::sth::mplstpOam {

}


proc ::sth::mplstpOam::emulation_mplstp_y1731_oam_control_action { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_mplstp_y1731_oam_control_action"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::mplstpOam::userArgsArray
    
    set mplstpOamHandleList ""
    if {[info exists ::sth::mplstpOam::userArgsArray(handle)]} {
        set mplstpOamHandleList $::sth::mplstpOam::userArgsArray(handle)
    } elseif {[info exists ::sth::mplstpOam::userArgsArray(port_handle)]} {
        set port_list $::sth::mplstpOam::userArgsArray(port_handle)
        foreach port $port_list {
            if {[::sth::sthCore::IsPortValid $port err]} {
                set deviceHdl [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className MplsTpOamMpConfig -rootlist $deviceHdl]
                append mplstpOamHandleList " $rtn(-ObjectList)"
            } else {
                ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $port" {}
                return -code error $returnKeyedList
            }
        }
    }

    set configCmdList [::sth::mplstpOam::get_config_command $mplstpOamHandleList $::sth::mplstpOam::userArgsArray(msg_type)]

    switch -exact -- $::sth::mplstpOam::userArgsArray(action) {
        "start" {
            switch -exact -- $::sth::mplstpOam::userArgsArray(msg_type) {
                "cc" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartCcCommand -MepList $mplstpOamHandleList
                }
                "lb" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartLbCommand -LbConfigList $configCmdList
                }
                "lck" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartLckCommand -MepList $mplstpOamHandleList
                }
                "ais" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartAisCommand -MepList $mplstpOamHandleList
                }
                "tst" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartTstCommand -TstConfigList $configCmdList
                }
                "csf" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartCsfCommand -CsfConfigList $configCmdList
                }
                "dm" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartDmCommand -DmConfigList $configCmdList
                }
                "lm" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStartLmCommand -LmConfigList $configCmdList
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Unknown msg_type $::sth::mplstpOam::userArgsArray(msg_type)."
                    return -code error $returnKeyedList
                }
            }
        }
        "stop" {
            switch -exact -- $::sth::mplstpOam::userArgsArray(msg_type) {
                "cc" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopCcCommand -MepList $mplstpOamHandleList
                }
                "lb" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopLbCommand -MepList $mplstpOamHandleList
                }
                "lck" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopLckCommand -MepList $mplstpOamHandleList
                }
                "ais" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopAisCommand -MepList $mplstpOamHandleList
                }
                "tst" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopTstCommand -MepList $mplstpOamHandleList
                }
                "csf" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopCsfCommand -MepList $mplstpOamHandleList
                }
                "dm" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopDmCommand -MepList $mplstpOamHandleList
                }
                "lm" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopLmCommand -MepList $mplstpOamHandleList
                }
                "stop_all" {
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopCcCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopLbCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopLckCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopAisCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopTstCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopCsfCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopDmCommand -MepList $mplstpOamHandleList
                    ::sth::sthCore::invoke stc::perform MplsTpOamStopLmCommand -MepList $mplstpOamHandleList
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Unknown msg_type $::sth::mplstpOam::userArgsArray(msg_type)."
                    return -code error $returnKeyedList
                }
            }
        }
        "delete" {
            ::sth::sthCore::invoke stc::perform DeleteCommand -ConfigList $mplstpOamHandleList
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unknown action $::sth::mplstpOam::userArgsArray(action)."
            return -code error $returnKeyedList
        }
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

proc ::sth::mplstpOam::get_config_command {mplstpOamHandleList msgType} {
    variable ::sth::mplstpOam::userArgsArray
    set configCmdList ""
    
    foreach mplstpOamHandle $mplstpOamHandleList {
        switch -exact -- $msgType {
                "lb" {
                    set optionValueList [getStcOptionValueList emulation_mplstp_y1731_oam_control configLbCommand start ""]
                    #Handling RemoteMpHandleList
                    if {[info exists ::sth::mplstpOam::userArgsArray(lb_meg_handle_list)]} {
                        set megHndList $::sth::mplstpOam::userArgsArray(lb_meg_handle_list)
                        set remoteHnd ""
                        foreach megHnd $megHndList {
                            lappend remoteHnd [::sth::sthCore::invoke stc::get $megHnd -children-MplsTpOamRemoteMpConfig]
                        }
                        append optionValueList " -RemoteMpHandleList \{$remoteHnd\}"
                    }
                    lappend configCmdList [::sth::sthCore::invoke stc::create MplsTpOamLbCommandConfig -under $mplstpOamHandle $optionValueList]
                }
                "tst" {
                    set optionValueList [getStcOptionValueList emulation_mplstp_y1731_oam_control configTstCommand start ""]
                    lappend configCmdList [::sth::sthCore::invoke stc::create MplsTpOamTstCommandConfig -under $mplstpOamHandle $optionValueList]
                }
                "csf" {
                    set optionValueList [getStcOptionValueList emulation_mplstp_y1731_oam_control configCsfCommand start ""]
                    lappend configCmdList [::sth::sthCore::invoke stc::create MplsTpOamCsfCommandConfig -under $mplstpOamHandle $optionValueList]
                }
                "dm" {
                    set optionValueList [getStcOptionValueList emulation_mplstp_y1731_oam_control configDmCommand start ""]
                    lappend configCmdList [::sth::sthCore::invoke stc::create MplsTpOamDmCommandConfig -under $mplstpOamHandle $optionValueList]
                }
                "lm" {
                    set optionValueList [getStcOptionValueList emulation_mplstp_y1731_oam_control configLmCommand start ""]
                    lappend configCmdList [::sth::sthCore::invoke stc::create MplsTpOamLmCommandConfig -under $mplstpOamHandle $optionValueList]
                }
        }
    }
    
    return $configCmdList
}


proc ::sth::mplstpOam::emulation_mplstp_y1731_oam_stats_func {myreturnKeyedList} {
    upvar $myreturnKeyedList returnKeyedList
    variable ::sth::mplstpOam::userArgsArray
    
    set port_list ""
    set handle_list ""
    if {[info exists ::sth::mplstpOam::userArgsArray(handle)]} {
        set handle_list $::sth::mplstpOam::userArgsArray(handle)
    } else {
        set port_list $::sth::mplstpOam::userArgsArray(port_handle)
        if {[regexp "meg" $::sth::mplstpOam::userArgsArray(mode)]} {
            set device_list ""
            foreach port $port_list {
                append device_list "[::sth::sthCore::invoke stc::get $port -affiliationport-Sources] "
            }
            array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className MplsTpOamMpConfig -rootlist $device_list]
            if {$rtn(-ObjectList) ne ""} {
                foreach mpConfig $rtn(-ObjectList) {
                    append handle_list "[::sth::sthCore::invoke stc::get $mpConfig -mplstpoammegassociation-Targets] "
                }
            } else {
                ::sth::sthCore::log warn "No MP-MEG Association on specified port"
            }
        } else {
            set handle_list $port_list
        }
    }
    
    #subscribe
    set resultDataSet [::sth::mplstpOam::subscribeObjects $::sth::mplstpOam::userArgsArray(mode) $handle_list]
    
    #get results
    ::sth::mplstpOam::getResults $resultDataSet
    
    #unsubscribe    
    ::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSet
    ::sth::sthCore::invoke stc::perform delete -configlist $resultDataSet
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::mplstpOam::getResults {resultDataSet} {
    upvar returnKeyedList returnKeyedList
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    set totalPage 1

    set totalPage [sth::sthCore::invoke stc::get $resultDataSet -TotalPageCount]
    
    #Getting mapping the native and hlt return keys/values
    for {set pageNumber 1} { $pageNumber <= $totalPage} {incr pageNumber} {
        
        if {$pageNumber > 1} {
            sth::sthCore::invoke stc::config $resultDataSet -pageNumber $pageNumber
            sth::sthCore::invoke stc::apply
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::sleep 2
        }

        set resultHndLists [sth::sthCore::invoke stc::get $resultDataSet -ResultHandleList]

        foreach resultHnd $resultHndLists {
            array set hnd [sth::sthCore::invoke stc::get $resultHnd]
            if {[regexp -nocase "MplsTpOamCcLocalResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "cc"
            } elseif {[regexp -nocase "MplsTpOamAisResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "ais"
            } elseif {[regexp -nocase "MplsTpOamDmResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "dm"
            } elseif {[regexp -nocase "MplsTpOamTstResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "tst"
            } elseif {[regexp -nocase "MplsTpOamCsfResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "csf"
            } elseif {[regexp -nocase "MplsTpOamLbResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "lb"
            } elseif {[regexp -nocase "MplsTpOamLckResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "lck"
            } elseif {[regexp -nocase "MplsTpOamLmResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "lm"
            } elseif {[regexp -nocase "MplsTpOamMegResults" $resultHnd]} {
                ::sth::mplstpOam::updateMplsTpOamStats [array get hnd] $resultHnd "meg"
            }
        }
    }

    return $returnKeyedList
}

proc ::sth::mplstpOam::updateMplsTpOamStats {resultVal resultHnd type} {
    upvar userArgsArray userArgsArray;
    upvar returnKeyedList returnKeyedList
    
    array set hnd $resultVal
    set key "$type.$hnd(-parent)"

    #Getting mapping the native and hlt return keys/values
    set TableName ::sth::mplstpOam::emulation_mplstp_y1731_oam_stats_$type\_stcattr
    set hltOptionList [array names $TableName]

    foreach hltName $hltOptionList {
        if {[info exists ::sth::mplstpOam::emulation_mplstp_y1731_oam_stats_$type\_stcattr($hltName)]} {
            set stcName [set ::sth::mplstpOam::emulation_mplstp_y1731_oam_stats_$type\_stcattr($hltName)]
            set stcValue $hnd(-$stcName)
            keylset returnKeyedList $key.$hltName $stcValue
        }
    }

    return $::sth::sthCore::SUCCESS
}

proc ::sth::mplstpOam::subscribeObjects {modeList configHnd} {
    upvar userArgsArray userArgsArray;
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    set resultObj ""

    #Create Single resultdatatset
    set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]

    #Create differet result queries based on different modes
    foreach mode [split $modeList |]  {
        set configResultClass [::sth::mplstpOam::getConfigResultClass $mode]
        sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$configHnd\} -ConfigClassId [lindex $configResultClass 0] -ResultClassId [lindex $configResultClass 1]"
    }

    sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
    sth::sthCore::invoke stc::sleep 3

    return $resultDataSet
}

proc ::sth::mplstpOam::getConfigResultClass {mode} {
    set resultObj ""

    switch -exact $mode { 
        cc {
            set resultObj "MplsTpOamMpConfig MplsTpOamCcLocalResults"
        }
        ais {
            set resultObj "MplsTpOamMpConfig MplsTpOamAisResults"
        }
        dm {
            set resultObj "MplsTpOamMpConfig MplsTpOamDmResults"
        }
        tst {
            set resultObj "MplsTpOamMpConfig MplsTpOamTstResults"
        }
        csf {
            set resultObj "MplsTpOamMpConfig MplsTpOamCsfResults"
        }
        lb {
            set resultObj "MplsTpOamMpConfig MplsTpOamLbResults"
        }
        lck {
            set resultObj "MplsTpOamMpConfig MplsTpOamLckResults"
        }
        lm {
            set resultObj "MplsTpOamMpConfig MplsTpOamLmResults"
        }
        meg {
            set resultObj "MplsTpOamMegConfig MplsTpOamMegResults"
        }
    }

    return $resultObj
}

proc ::sth::mplstpOam::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    
    foreach item $::sth::mplstpOam::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::mplstpOam:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::mplstpOam:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::mplstpOam:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                #::sth::mplstpOam::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::mplstpOam::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::mplstpOam:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::mplstpOam:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::mplstpOam:: $cmdType $opt $::sth::mplstpOam::userArgsArray($opt)} value]} {
						lappend optionValueList -$stcAttr $value
					} else {
						lappend optionValueList -$stcAttr $::sth::mplstpOam::userArgsArray($opt)
					}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::mplstpOam::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}
