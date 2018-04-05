#!/bin/sh
# -*- tcl -*-
# The next line is executed by /bin/sh, but not tcl
namespace eval ::sth::video {

    proc emulation_video_config_enable {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray
        set deviceHnd $userArgsArray(handle)
        if {$userArgsArray(type) == "client"} {
            set sessionObj VideoClientProtocolConfig
        } else {
            set sessionObj VideoServerProtocolConfig
        }
        set sessionHnd [::sth::sthCore::invoke stc::create $sessionObj -under $deviceHnd]
        emulation_video_config_common $sessionHnd $sessionObj
        keylset returnKeyedList session_handle $sessionHnd
        return $returnKeyedList
    }

    proc emulation_video_config_modify {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray
        set deviceHnd $userArgsArray(handle)
        set clientSessionHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-VideoClientProtocolConfig]
        set serverSessionHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-VideoServerProtocolConfig]
        if {$userArgsArray(type) == "client"} {
            set sessionObj VideoClientProtocolConfig
            set sessionHnd $clientSessionHnd
            if {$serverSessionHnd != ""} {
                ::sth::sthCore::invoke stc::delete $serverSessionHnd
            }
        } else {
            set sessionObj VideoServerProtocolConfig
            set sessionHnd $serverSessionHnd
            if {$clientSessionHnd != ""} {
                ::sth::sthCore::invoke stc::delete $clientSessionHnd
            }
        }
        if {$sessionHnd == ""} {
            set sessionHnd [::sth::sthCore::invoke stc::create $sessionObj -under $deviceHnd]
        }
        emulation_video_config_common $sessionHnd $sessionObj
        keylset returnKeyedList session_handle $sessionHnd
        return $returnKeyedList
    }

    proc emulation_video_config_common {sessionHnd sessionObj} {
        set optionList ""
        variable userArgsArray
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::video:: emulation_video_config $optArg stcattr]
            set stcObj [::sth::sthCore::getswitchprop ::sth::video:: emulation_video_config $optArg stcobj]
            if {[string equal -nocase $stcAttr "_none_"] && ![regexp -nocase $sessionObj $stcObj]} {
                continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr [list $switchValue] "
        }
        ::sth::sthCore::invoke stc::config $sessionHnd $optionList
    }

    proc emulation_video_server_streams_config_create {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray

        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: the handle is require for the mode create" {}
            return -code error $returnKeyedList
        }
        set serverStream [::sth::sthCore::invoke stc::create VideoServerStream -under $userArgsArray(handle)]
        emulation_video_server_streams_config_common $serverStream
        keylset returnKeyedList handle $serverStream
    }

    proc emulation_video_server_streams_config_modify {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray
        if {![info exists userArgsArray(stream_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: the handle is require for the mode modify" {}
            return -code error $returnKeyedList
        }
        emulation_video_server_streams_config_common $userArgsArray(stream_handle)
    }

    proc emulation_video_server_streams_config_delete {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray
        if {![info exists userArgsArray(stream_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: the handle is require for the mode delete" {}
            return -code error $returnKeyedList
        }
        ::sth::sthCore::invoke stc::delete $userArgsArray(stream_handle)
    }

    proc emulation_video_server_streams_config_common {serverStream} {
        variable userArgsArray
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        set optionList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::video:: emulation_video_server_streams_config $optArg stcattr]
            set stcObj [::sth::sthCore::getswitchprop ::sth::video:: emulation_video_server_streams_config $optArg stcobj]
            if {[string equal -nocase $stcAttr "_none_"]} {
                continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr [list $switchValue] "
        }
        ::sth::sthCore::invoke stc::config $serverStream $optionList
    }

    proc emulation_profile_config {returnKeyedListVarName} {
        upvar 1 $returnKeyedListVarName returnKeyedList
        variable userArgsArray
        if {$userArgsArray(profile_type) == "client"} {
            set profileObj "ClientProfile"
        } elseif {$userArgsArray(profile_type) == "server"} {
            set profileObj "ServerProfile"
        } else {
            set profileObj "ClientLoadProfile"
        }
        if {$userArgsArray(mode) == "create"} {
            set profileHnd [::sth::sthCore::invoke stc::create $profileObj -under project1]
        } else {
           
            set profileHnd $userArgsArray(handle)
        }
        if {$userArgsArray(mode) == "delete"} {
            ::sth::sthCore::invoke stc::delete $profileHnd
        } else {
            ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
            set optionList ""
            foreach optArg $switches {
                set stcAttr [::sth::sthCore::getswitchprop ::sth::video:: emulation_profile_config $optArg stcattr]
                set stcObj [::sth::sthCore::getswitchprop ::sth::video:: emulation_profile_config $optArg stcobj]
                if {[string equal -nocase $stcAttr "_none_"] && ![regexp -nocase $profileObj $stcObj]} {
                    continue
                }
                set switchValue $switchValues($optArg)
                append optionList "-$stcAttr [list $switchValue] "
            }
            ::sth::sthCore::invoke stc::config $profileHnd $optionList
            if {$userArgsArray(mode) == "create"} {
                keylset returnKeyedList handle $profileHnd
            }
        }
    }
    #######################################################################
    #Functions: emulation_client_load_phase_config_create
    #           emulation_client_load_phase_config_modify
    #           emulation_client_load_phase_config_delete
    #######################################################################
    proc ::sth::video::emulation_client_load_phase_config_create {returnKeyedList} {
        ::sth::sthCore::log hltcall "User executed ::sth::video::emulation_client_load_phase_config_create "
        variable userArgsArray
        upvar 1 $returnKeyedList returnKeyedLst

        set optionList ""
        set optionList [getStcOptionValueList emulation_client_load_phase_config "ClientLoadPhase" "create"]

        if {[info exists userArgsArray(profile_handle)]} {
            set profileHandle $userArgsArray(profile_handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: the profile_handle is require for the mode create" {}
            return -code error $returnKeyedList
        }

        if {[info exists userArgsArray(load_pattern)]} {
            set loadPattern $userArgsArray(load_pattern)
        } else {
            set loadPattern "stair"
        }
        set phaseHandle [::sth::sthCore::invoke stc::create ClientLoadPhase -under $profileHandle $optionList]
        load_phase_config "create" $phaseHandle $loadPattern
        keylset returnKeyedLst load_phase_handle $phaseHandle
    }

    proc ::sth::video::emulation_client_load_phase_config_modify {returnKeyedListarg} {
        ::sth::sthCore::log hltcall "User executed ::sth::video::emulation_client_load_phase_config_modify "
        variable userArgsArray
        upvar 1 $returnKeyedListarg returnKeyedList
        if {[info exists userArgsArray(phase_handle)]} {
            set tempPatternType [::sth::sthCore::invoke stc::get $::sth::video::userArgsArray(phase_handle) -LoadPattern]
            if {![string equal -nocase $tempPatternType $userArgsArray(load_pattern)]} {
                set tempPatternHandle [::sth::sthCore::invoke stc::get $userArgsArray(phase_handle) -children]
                ::sth::sthCore::invoke stc::delete $tempPatternHandle
                load_phase_config "create" $userArgsArray(phase_handle) $userArgsArray(load_pattern)
            } else {
                load_phase_config "modify" $userArgsArray(phase_handle) $userArgsArray(load_pattern)
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: the phase_handle is require for the mode modify" {}
            return -code error $returnKeyedList
        }
    }

    proc ::sth::video::emulation_client_load_phase_config_delete {returnKeyedListarg} {
        upvar 1 $returnKeyedListarg returnKeyedList
        variable userArgsArray
        ::sth::sthCore::log hltcall "User executed ::sth::video::emulation_client_load_phase_config_delete "
        if {[info exists userArgsArray(phase_handle) ]} {
            ::sth::sthCore::invoke stc::delete $userArgsArray(phase_handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: the phase_handle is require for the mode delete" {}
            return -code error $returnKeyedList
        }
    }
    proc ::sth::video::load_phase_config {mode phaseHandle loadPattern} {
        set optionList ""
        switch -exact $loadPattern {
            stair {
                set patternDescCls "StairPatternDescriptor"
            }
            flat {
                set patternDescCls "FlatPatternDescriptor"
            }
            burst {
                set patternDescCls "BurstPatternDescriptor"
            }
            sinusoid {
                set patternDescCls "SinusoidPatternDescriptor"
            }
            random {
                set patternDescCls "RandomPatternDescriptor"
            }
            sawtooth {
                set patternDescCls "SawToothPatternDescriptor"
            }
            default {
                set patternDescCls "StairPatternDescriptor"
            }
        }
        if {$mode == "create"} {
            set patternDes [::sth::sthCore::invoke stc::create $patternDescCls -under $phaseHandle]
        } else {
            set patternDes [::sth::sthCore::invoke stc::get $phaseHandle -children-$patternDescCls]
            if {$patternDes == ""} {
                set patternDes [::sth::sthCore::invoke stc::create $patternDescCls -under $phaseHandle]
            }
        }
        set optionList [getStcOptionValueList emulation_client_load_phase_config $patternDescCls "create"]
        ::sth::sthCore::invoke stc::config $patternDes $optionList
    }

    proc emulation_video_stats {mode returnKeyedListVarName} {
        variable userArgsArray
        upvar 1 $returnKeyedListVarName returnKeyedListRet
        set returnKeyedList {}
        if {$mode == "client"} {
            set configClass "VideoClientProtocolConfig"
            set resultClass "VideoClientResults"
        } elseif {$mode == "server"} {
            set configClass "VideoServerProtocolConfig"
            set resultClass "VideoServerResults"
        } else {
            set configClass "VideoServerProtocolConfig"
            set resultClass "VideoServerSessions"
        }

        if {[info exists userArgsArray(handle)]} {
            set deviceHndList $userArgsArray(handle)
            sth::sthCore::invoke stc::subscribe \
                                            -Parent $::sth::sthCore::GBLHNDMAP(project) \
                                            -ResultType $resultClass \
                                            -ConfigType $configClass \
                                            -ResultParent $deviceHndList

            ::sth::sthCore::invoke stc::sleep 3
            foreach deviceHnd $deviceHndList {
                set clientSessionHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-$configClass]
                if {$clientSessionHnd == ""} {
                    continue
                }
                set videoClientResults [::sth::sthCore::invoke stc::get $clientSessionHnd -children-$resultClass]
                if {$videoClientResults == ""} {
                    continue
                }
                foreach key [array names ::sth::video::emulation_video_stats_$mode\_stcattr] {
                    set stcAttr [set ::sth::video::emulation_video_stats_$mode\_stcattr($key)]
                    if {[string match $stcAttr  "_none_"]} {
                       continue
                    }
                    set val [::sth::sthCore::invoke stc::get $videoClientResults -$stcAttr]
                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList $key $val]
                }
                set returnKeyedListRet [::sth::sthCore::updateReturnInfo $returnKeyedListRet $deviceHnd $returnKeyedList]
            }
        } elseif {[info exists userArgsArray(port_handle)]} {
            set portHndList $userArgsArray(port_handle)
            sth::sthCore::invoke stc::subscribe \
                                            -Parent $::sth::sthCore::GBLHNDMAP(project) \
                                            -ResultType $resultClass \
                                            -ConfigType $configClass \
                                            -ResultParent $portHndList
            foreach portHnd $portHndList {
                set deviceHndList [::sth::sthCore::invoke stc::get $portHnd -AffiliatedPortSource]
                set returnKeyedListRetTmp {}
                foreach deviceHnd $deviceHndList {
                    set clientSessionHnd [::sth::sthCore::invoke stc::get $deviceHnd -children-$configClass]
                    if {$clientSessionHnd == ""} {
                        continue
                    }
                    set videoClientResults [::sth::sthCore::invoke stc::get $clientSessionHnd -children-$resultClass]
                    if {$videoClientResults == ""} {
                        continue
                    }
                    foreach key [array names ::sth::video::emulation_video_stats_$mode\_stcattr] {
                        set stcAttr [set ::sth::video::emulation_video_stats_$mode\_stcattr($key)]
                        if {[string match $stcAttr  "_none_"]} {
                           continue
                        }
                        set val [::sth::sthCore::invoke stc::get $videoClientResults -$stcAttr]
                        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList $key $val]
                    }
                    set returnKeyedListRetTmp [::sth::sthCore::updateReturnInfo $returnKeyedListRetTmp $deviceHnd $returnKeyedList]
                }
                set returnKeyedListRet [::sth::sthCore::updateReturnInfo $returnKeyedListRet $portHnd $returnKeyedListRetTmp]
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: either the port_handle or the handle need to be specified" {}
            return -code error $returnKeyedList
        }
    }
    proc getStcOptionValueList {cmdType class mode} {
        variable userArgsArray
        ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
        set optionList ""
        foreach optArg $switches {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::video:: $cmdType $optArg stcattr]
            set stcObj [::sth::sthCore::getswitchprop ::sth::video:: $cmdType $optArg stcobj]
            if {[string equal -nocase $stcAttr "_none_"] || ![regexp -nocase $class $stcObj]} {
                continue
            }
            set switchValue $switchValues($optArg)
            append optionList "-$stcAttr [list $switchValue] "
        }
        return $optionList
    }
}
