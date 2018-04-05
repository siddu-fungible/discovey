#!/bin/sh
# -*- tcl -*-
# The next line is executed by /bin/sh, but not tcl
namespace eval ::sth::Vqa {
    proc emulation_vqa_host_config_enable {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)

        #check if the device handle has been configured with the igmp or mld
        set deviceHnd $::sth::Vqa::userArgsArray(handle)

        set igmpHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-igmphostconfig]
        set mldHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-mldhostconfig]
        if {$igmpHnd == "" && $mldHnd == ""} {
            ::sth::sthCore::processError returnKeyedList "IGMP or MLD Device required !"
            return $returnKeyedList
        }
        set vqaHnd [::sth::sthCore::invoke stc::create VqDeviceChannelBlock -under $deviceHnd]
        set optionList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_host_config $optArg stcattr]
            if {[string equal -nocase $stcAttr "_none_"]} {
                continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr [list $switchValue] "
        }
        ::sth::sthCore::invoke stc::config $vqaHnd $optionList
        keylset returnKeyedList session_handle $vqaHnd
        return $returnKeyedList
    }

    proc emulation_vqa_host_config_modify {returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        #check if the device handle has been configured with the igmp or mld
        set vqaHnd $::sth::Vqa::userArgsArray(session_handle)
        #set vqaHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-VqDeviceChannelBlock]
        if {$vqaHnd != ""} {
            set optionList ""
            foreach optArg $switches {
                set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_host_config $optArg stcattr]
                if {[string equal -nocase $stcAttr "_none_"]} {
                   continue
                }
                set switchValue $switchValues($optArg)
                append optionList "-$stcAttr $switchValue "
            }
            ::sth::sthCore::invoke stc::config $vqaHnd $optionList
        }
    }


    proc emulation_vqa_config_create {returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        set probe [::sth::sthCore::invoke stc::create Probe -under $userArgsArray(port_handle)]
        set vqProbeHnd [::sth::sthCore::invoke stc::create VqProbeChannelBlock -under $probe]
        set optionList ""
        foreach optArg $switches {
           set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_config $optArg stcattr]
           if {[string equal -nocase $stcAttr "_none_"]} {
                continue
            }
           set switchValue $switchValues($optArg)
           append optionList "-$stcAttr $switchValue "
        }
        ::sth::sthCore::invoke stc::config $vqProbeHnd $optionList
        keylset returnKeyedList handle $vqProbeHnd
        return $returnKeyedList
    }

    proc emulation_vqa_config_modify {returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        set vqProbeHnd $userArgsArray(handle)
        set optionList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_config $optArg stcattr]
            if {[string equal -nocase $stcAttr "_none_"]} {
                continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr $switchValue "
        }
        ::sth::sthCore::invoke stc::config $vqProbeHnd $optionList
        return $returnKeyedList
    }

    proc emulation_vqa_port_config_create {returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues "$userArgsArray(optional_args) $userArgsArray(mandatory_args)"
        set vqana [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-VqAnalyzer]
        set vqanaOptionList ""
        set vqpayloadOptionList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_port_config $optArg stcattr]
            set stcobj [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_port_config $optArg stcobj]
            if {[string equal -nocase $stcAttr "_none_"]} {
               continue
            }
            set switchValue $switchValues($optArg)
            if {[string equal -nocase $stcobj "VqAnalyzer"]} {
                append vqanaOptionList "-$stcAttr $switchValue "
            } elseif {[string equal -nocase $stcobj "VqDynamicPayloadConfig"]} {
                append vqpayloadOptionList "-$stcAttr $switchValue "
            }
        }
        ::sth::sthCore::invoke stc::config $vqana $vqanaOptionList
        #create the VqDynamicPayloadConfig
        set vqpayload [::sth::sthCore::invoke stc::create VqDynamicPayloadConfig -under $vqana]
        ::sth::sthCore::invoke stc::config $vqpayload $vqpayloadOptionList
        keylset returnKeyedList handle $vqana
        return $returnKeyedList
    }

    proc emulation_vqa_port_config_modify {returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues "$userArgsArray(optional_args) $userArgsArray(mandatory_args)"
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "handle is required for the modify mode"
            return $returnKeyedList
        }
        set vqpayloadOptionList ""
        set vqList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_port_config $optArg stcattr]
            set stcobj [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_port_config $optArg stcobj]
            if {[string equal -nocase $stcAttr "_none_"]} {
               continue
            }
            set switchValue $switchValues($optArg)
            if {[string equal -nocase $stcobj "VqDynamicPayloadConfig"]} {
                append vqpayloadOptionList "-$stcAttr $switchValue "
            } else {
                append vqList "-$stcAttr $switchValue "
            }
        }
        ::sth::sthCore::invoke stc::config $userArgsArray(handle) $vqList
        set vqpayload [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-VqDynamicPayloadConfig]
        if {$vqpayload == ""} {
            ::sth::sthCore::invoke stc::create VqDynamicPayloadConfig -under $userArgsArray(handle)
        }
        ::sth::sthCore::invoke stc::config $vqpayload $vqpayloadOptionList
        return $returnKeyedList
    }

    proc emulation_vqa_global_config_config {returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        set vqanaoptions [::sth::sthCore::invoke stc::get project1 -children-VqAnalyzerOptions]
        set optionList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::Vqa:: emulation_vqa_global_config $optArg stcattr]
            if {[string equal -nocase $stcAttr "_none_"]} {
                continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr $switchValue "
        }
        ::sth::sthCore::invoke stc::config $vqanaoptions $optionList
        return $returnKeyedList
    }

    proc emulation_vqa_control {action returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedList
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        set vqaAnalyzerHndList ""
        if {[info exists userArgsArray(handle)]} {
            set vqaAnalyzerHndList $userArgsArray(handle)
        } elseif {[info exists userArgsArray(port_handle)]} {
            set portList ""
            if {[regexp -nocase "^all$" $userArgsArray(port_handle)]} {
                set portList [::sth::sthCore::invoke stc::get project1 -children-port]
            } else {
                set portList $userArgsArray(port_handle)
            }
            foreach port $portList {
                if {[::sth::sthCore::IsPortValid $port err]} {
                    lappend vqaAnalyzerHndList [stc::get $port -children-VqAnalyzer]
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                    return -code error $returnKeyedList
                }
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: either the port_handle or the handle need to be specified" {}
            return -code error $returnKeyedList
        }
        if {$action == "start"} {
            ::sth::sthCore::invoke stc::perform VqAnalyzerStartCommand -VqAnalyzerList $vqaAnalyzerHndList
        } else {
            ::sth::sthCore::invoke stc::perform VqAnalyzerStopCommand -VqAnalyzerList $vqaAnalyzerHndList
        }
        return $returnKeyedList
    }

    proc emulation_vqa_stats {mode returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedListRet


        if {[regexp "^video" $mode]} {
            set resultClass "VqVideoStreamResults"
        } elseif {[regexp "^audio" $mode]} {
            set resultClass "VqAudioStreamResults"
        } else {
            set resultClass "VqVideoStreamResults"
        }

        if {[info exists userArgsArray(port_handle)]} {
            set deviceHndList $userArgsArray(port_handle)
            set configClass "VqProbeChannelBlock"
        } elseif {[info exists userArgsArray(handle)]} {
            set deviceHndList $userArgsArray(handle)
            set configClass "VqDeviceChannelBlock"
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: either the port_handle or the handle need to be specified" {}
            return -code error $returnKeyedList
        }


        sth::sthCore::invoke stc::subscribe \
                                        -Parent $::sth::sthCore::GBLHNDMAP(project) \
                                        -ResultType $resultClass \
                                        -ConfigType $configClass \
                                        -ResultParent $deviceHndList
        ::sth::sthCore::invoke stc::sleep 3

        foreach deviceHnd $deviceHndList {
            #if {[regexp -nocase "VqProbeChannelBlock" $configClass]} {
            #    set configObjParents [::sth::sthCore::invoke stc::get $deviceHnd -children-probe]
            #} else {
            #    set configObjParents $deviceHnd
            #}
            if {[regexp -nocase "port" $deviceHnd]} {
                set configObjParents [::sth::sthCore::invoke stc::get $deviceHnd -children-probe]
                if {$configObjParents == ""} {
                    set configClass "VqDeviceChannelBlock"
                    set configObjParents [::sth::sthCore::invoke stc::get $deviceHnd -affiliationport-sources]
                } else {
                    set configClass "VqProbeChannelBlock"
                }
            } else {
                set configObjParents $deviceHnd
                set configClass "VqDeviceChannelBlock"
            }
            set resultList ""
            if {$configObjParents == ""} {
                continue
            }
            foreach configObjParent $configObjParents {

                set sessionHnd [::sth::sthCore::invoke stc::get $configObjParent -children-$configClass]
                if {$sessionHnd == ""} {
                    continue
                }
                set results [::sth::sthCore::invoke stc::get $sessionHnd -children-$resultClass]
                if {$results == ""} {
                    continue
                }
                set returnKeyedListList {}
                foreach result $results {
                    set returnKeyedList {}
                    foreach key [array names ::sth::Vqa::emulation_vqa_stats_$mode\_stcattr] {
                        set stcAttr [set ::sth::Vqa::emulation_vqa_stats_$mode\_stcattr($key)]
                        if {[string match $stcAttr  "_none_"]} {
                           continue
                        }
                        set val [::sth::sthCore::invoke stc::get $result -$stcAttr]
                        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList $key $val]
                    }
                    if {[llength $results] > 1} {
                        lappend returnKeyedListList $returnKeyedList
                    } else {
                        set returnKeyedListList $returnKeyedList
                    }
                }
                if {[regexp -nocase "port" $deviceHnd] && $configClass == "VqDeviceChannelBlock"} {
                    set resultList [::sth::sthCore::updateReturnInfo $resultList $configObjParent $returnKeyedListList]
                } else {
                    lappend resultList $returnKeyedListList
                }
            }
            set returnKeyedListRet [::sth::sthCore::updateReturnInfo $returnKeyedListRet $deviceHnd $resultList]
        }
    }
}
