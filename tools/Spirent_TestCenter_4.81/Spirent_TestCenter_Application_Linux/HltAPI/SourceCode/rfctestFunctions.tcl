# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.
namespace eval ::sth::Rfctest {
    set createResultQuery 0
}

proc ::sth::Rfctest::rfc2544_asymmetric_config_create { rklName } {
        
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_config_create $rklName"
    upvar 1 $rklName returnKeyedList
    
    set trafficDescriptorGroup [::sth::sthCore::invoke stc::create TrafficDescriptorGroup -under $::sth::GBLHNDMAP(project)]
    set dsPortGroup [::sth::sthCore::invoke stc::create PortGroup -under $::sth::GBLHNDMAP(project) -GroupName {Downstream} -Name {Downstream}]
    set usPortGroup [::sth::sthCore::invoke stc::create PortGroup -under $::sth::GBLHNDMAP(project) -GroupName {Upstream} -Name {Upstream}]
    set GroupType [::sth::sthCore::invoke stc::create GroupType -under $::sth::GBLHNDMAP(project) -Name {Port Side}]
    set dwnstrmport $::sth::Rfctest::userArgsArray(downstream_port)
    set upstrmport $::sth::Rfctest::userArgsArray(upstream_port)
    ::sth::sthCore::invoke stc::config $GroupType -GroupOfType-targets "$dsPortGroup $usPortGroup"
    ::sth::sthCore::invoke stc::config $dsPortGroup -GroupMembership-targets "$dwnstrmport"
    ::sth::sthCore::invoke stc::config $usPortGroup -GroupMembership-targets "$upstrmport" 
    
    #creates AccessConcentratorGenParam under project
    set AccessConcentratorHandle [::sth::sthCore::invoke stc::create AccessConcentratorGenParams -under $::sth::GBLHNDMAP(project)]
    configAccessConcentratorGeneratorParam $AccessConcentratorHandle create
    set testType $::sth::Rfctest::userArgsArray(test_type)
    #creates test configuration handle under AccessConcentratorGenParam
    set testConfigHandle [configrfc2544_asymmetric_config create $testType $AccessConcentratorHandle]
    set AsymTestConfigHdl $testConfigHandle 
    configImix $testConfigHandle
   
      
    
    if {$::sth::Rfctest::userArgsArray(traffic_config_mode) eq "manual"} {
        set trafficDescriptorGroup [::sth::sthCore::invoke stc::create TrafficDescriptorGroup -under $::sth::GBLHNDMAP(project)]
        set trafficDescriptor [::sth::sthCore::invoke stc::create TrafficDescriptor -under $trafficDescriptorGroup]
        configTrafficDescriptor  rfc2544_asymmetric_config $trafficDescriptor create
         

        if {$::sth::Rfctest::userArgsArray(endpoint_creation) == 1} {
            if {![info exists ::sth::Rfctest::userArgsArray(upstream_port)] || ![info exists ::sth::Rfctest::userArgsArray(downstream_port)]} {
                ::sth::sthCore::processError returnKeyedList "Please provide upstream_port and downstream_port options when endpoint_creation is set"
                return $returnKeyedList
            } else {
                set srcPort $::sth::Rfctest::userArgsArray(downstream_port)
                set dstPort $::sth::Rfctest::userArgsArray(upstream_port)
                ::sth::sthCore::invoke stc::config $trafficDescriptor "-SrcBinding-targets $srcPort -DstBinding-targets $dstPort"
            }
        } else {
            if {[info exists ::sth::Rfctest::userArgsArray(downstream_endpoint)] && [info exists ::sth::Rfctest::userArgsArray(upstream_endpoint)]} {
                 set srcBlockHandle [GetIpOrNetworkBlockHandle $::sth::Rfctest::userArgsArray(downstream_endpoint)]
                 set dstBlockHandle [GetIpOrNetworkBlockHandle $::sth::Rfctest::userArgsArray(upstream_endpoint)]
                 ::sth::sthCore::invoke stc::config $trafficDescriptor "-SrcBinding-targets {$srcBlockHandle} -DstBinding-targets {$dstBlockHandle}"
            }
            if {[info exists ::sth::Rfctest::userArgsArray(streamblock_handle)]} {
                 set streamHandle [list $::sth::Rfctest::userArgsArray(streamblock_handle)]
            }
        }
        
    } else {
        if {$::sth::Rfctest::userArgsArray(traffic_config_mode) eq "auto"} {
            ::sth::sthCore::invoke stc::perform AccessConcentratorGenUpdateTrafficCommand -GenParams $AccessConcentratorHandle
        }
    }
    #creates test configuration profile and test configuration handle
    set TestProfile ""
    if {[info exists ::sth::Rfctest::userArgsArray(profile_config_mode)] && $::sth::Rfctest::userArgsArray(profile_config_mode) eq "per_side" } { 
        set streamHandledwnstream [::sth::sthCore::invoke stc::get $::sth::Rfctest::userArgsArray(downstream_port) -children-streamblock]
        if {$streamHandledwnstream ne ""} {
            set dsProfileHandle [configAsymmetricProfile create $testType down_stream $testConfigHandle]
            lappend TestProfile $dsProfileHandle
            ::sth::sthCore::invoke stc::config $dsProfileHandle -StreamBlockBinding-targets "$streamHandledwnstream"
        }
           
        set streamHandleupstream [::sth::sthCore::invoke stc::get $::sth::Rfctest::userArgsArray(upstream_port) -children-streamblock]
        if {$streamHandleupstream ne ""} {
            set usProfileHandle [configAsymmetricProfile create $testType up_stream $testConfigHandle]
            lappend TestProfile $usProfileHandle
           ::sth::sthCore::invoke stc::config $usProfileHandle -StreamBlockBinding-targets "$streamHandleupstream"
        }
       } else {
           if {[info exists ::sth::Rfctest::userArgsArray(profile_config_mode)] && $::sth::Rfctest::userArgsArray(profile_config_mode) eq "per_port" } {
               set portlist [::sth::sthCore::invoke stc::get project1 -children-port]
               foreach port $portlist {
                   set strmblk [::sth::sthCore::invoke stc::get $port -children-streamblock]
                   if {$strmblk ne ""} {
                       set PortProfileHandle [configAsymmetricProfile create $testType per_port $testConfigHandle]                
                       lappend TestProfile $PortProfileHandle
                       ::sth::sthCore::invoke stc::config $PortProfileHandle -StreamBlockBinding-targets "$strmblk"
                   }
               }
           }
       }
    
    
    
    ::sth::sthCore::invoke stc::perform AccessConcentratorGenConfigExpandCommand -GenParams $AccessConcentratorHandle    
    set streamProfileHnd [::sth::sthCore::invoke stc::create Rfc2544StreamBlockProfile -under $testConfigHandle]
    ::sth::sthCore::invoke stc::config $testConfigHandle "-TrafficDescriptorGroupBinding-targets $trafficDescriptorGroup"
    set testConfigHandle_sb $testConfigHandle
    set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
    set cmds [::sth::sthCore::invoke stc::get $seqHandle -children]
     foreach cmd $cmds {
     set testConfigHandle [::sth::sthCore::invoke stc::get $cmd -children]
     switch -- $testType {
         fl {
         if {[regexp -- "rfc2544framelossconfig" $testConfigHandle]} {
             set returnHnd $testConfigHandle
             
         }
         if {[regexp -- "rfc2544framelosssequencergroupcommand" $cmd]} {
             foreach seqCmd $testConfigHandle {
             set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
             if {[regexp -- "rfc2544framelossconfig" $configHandle]} {
                 set returnHnd $configHandle
             }
             }
         }
         }
         throughput {
         if {[regexp -- "rfc2544throughputconfig" $testConfigHandle]} {
             set returnHnd $testConfigHandle
         }
         if {[regexp -- "rfc2544throughputsequencergroupcommand" $cmd]} {
             foreach seqCmd $testConfigHandle {
             set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
             if {[regexp -- "rfc2544throughputconfig" $configHandle]} {
                 set returnHnd $configHandle
             }
             }
         }
         }
         latency {
         if {[regexp -- "rfc2544latencyconfig" $testConfigHandle]} {
             set returnHnd $testConfigHandle
         }
         if {[regexp -- "rfc2544latencysequencergroupcommand" $cmd]} {
             foreach seqCmd $testConfigHandle {
             set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
             if {[regexp -- "rfc2544latencyconfig" $configHandle]} {
                 set returnHnd $configHandle
             }
             }
         }
         }
     }
     }
      if {[info exists ::sth::Rfctest::userArgsArray(streamblock_handle)]} {
    set cmdHanld [::sth::sthCore::invoke stc::get $returnHnd -parent]
    ::sth::sthCore::invoke stc::config $cmdHanld "-StreamBlockList $streamHandle"
    set streamProfileHnd [::sth::sthCore::invoke stc::get $testConfigHandle_sb -children-rfc2544streamblockprofile]
    ::sth::sthCore::invoke stc::config $streamProfileHnd "-StreamBlockList $streamHandle"
    
    ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList $::sth::Rfctest::userArgsArray(streamblock_handle)
    }
    
    
    #applyconfig
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        return -code error $applyError
    }
    set ports [llength [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-port]]
    set streamHandles ""
    for {set port 0} {$port < $ports} {incr port} {
      set streamhandle [::sth::sthCore::invoke stc::get [lindex [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-port] $port] -children-streamblock]
      lappend streamHandles $streamhandle
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    keylset returnKeyedList handle $AsymTestConfigHdl
    keylset returnKeyedList stream_handles $streamHandles
    keylset returnKeyedList profile_handles $TestProfile 
    return $returnKeyedList
    
}


proc ::sth::Rfctest::rfc2544_asymmetric_profile_create { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_profile_create $rklName"

    upvar 1 $rklName returnKeyedList
    set testProfile ""
    set testhandle1 [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-AccessConcentratorGenParams]
    foreach handle $testhandle1 {
        set handlechild [::sth::sthCore::invoke stc::get $handle -children]
        if {$handlechild ne ""} {
        set validHandle $handle
        }
    }
    set testconfighandle [::sth::sthCore::invoke stc::get $validHandle -children]
     if {[regexp -- "rfc2544framelossconfig" $testconfighandle]} {
       set testProfile "Rfc2544FrameLossProfile"
     }
     if {[regexp -- "rfc2544throughputconfig" $testconfighandle]} {
       set testProfile "Rfc2544ThroughputProfile"
     }
     if {[regexp -- "rfc2544latencyconfig" $testconfighandle]} {
       set testProfile "Rfc2544LatencyProfile"
          
     }

    set testProfileHandle [::sth::sthCore::invoke stc::create $testProfile -under $testconfighandle]
    configProfileHandl $testProfileHandle create
      
    set Rfc2544ProfileRate [stc::get $testProfileHandle -children-Rfc2544ProfileRate]

    if {![regexp -nocase "throughput" $testconfighandle]} {
       set ProfileRateMode [stc::get $testProfileHandle -ProfileRateMode]

       if {$ProfileRateMode eq "PER_FRAME_SIZE"} {
          configprofileratemode $testProfileHandle $testconfighandle
       } else {
             set ProfileRateMode [stc::get $testProfileHandle -ProfileRateMode]
             configRfc2544Profile $Rfc2544ProfileRate modify
       }

    }

    #set ProfileRateMode [stc::get $testProfileHandle -ProfileRateMode]
    #configRfc2544Profile $Rfc2544ProfileRate modify
    set streamblock $::sth::Rfctest::userArgsArray(streamblock_handle)
   
    ::sth::sthCore::invoke stc::config $testProfileHandle -StreamBlockBinding-targets "$streamblock"
    
    ::sth::sthCore::invoke stc::perform AccessConcentratorGenConfigExpandCommand -GenParams $validHandle
    

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    keylset returnKeyedList handle $testProfileHandle
    
    return $returnKeyedList


}

proc ::sth::Rfctest::rfc2544_asymmetric_profile_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_profile_modify $rklName"
     variable userArgsArray
     upvar 1 $rklName returnKeyedList
     set children [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-AccessConcentratorGenParams]
    foreach accessconcChild $children {
          set validAccess [::sth::sthCore::invoke stc::get $accessconcChild -children]
    }
    if {$validAccess ne ""} {
        set AccessConcHdl $accessconcChild
    }
    if {![info exists ::sth::Rfctest::userArgsArray(profile_handle)]} {
         return -code error "the switch \"-profile_handle\" is mandatory in modify mode"
   } else {
           set testProfileHandle $::sth::Rfctest::userArgsArray(profile_handle)
     }
    configProfileHandl $testProfileHandle create
    set Rfc2544ProfileRate [stc::get $testProfileHandle -children-Rfc2544ProfileRate]
    
 if {![regexp -nocase "throughput" $validAccess]} {
    set ProfileRateMode [stc::get $testProfileHandle -ProfileRateMode]
    
    
    if {$ProfileRateMode eq "PER_FRAME_SIZE"} {

    configprofileratemode $testProfileHandle $validAccess

    } else {
       configProfileHandl $testProfileHandle create
    
       set Rfc2544ProfileRate [stc::get $testProfileHandle -children-Rfc2544ProfileRate]
       configRfc2544Profile $Rfc2544ProfileRate modify
    }
  
}



    ::sth::sthCore::invoke stc::perform AccessConcentratorGenConfigExpandCommand -GenParams $AccessConcHdl
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList

}


proc ::sth::Rfctest::configprofileratemode {testProfileHandle validAccess} {

       variable userArgsArray
       set Rfc2544ProfileRate [stc::get $testProfileHandle -children-Rfc2544ProfileRate]
       set frame_sizes $userArgsArray(frame_size)
       set Frame_Sizes [llength [split $frame_sizes " "]]
       if {[llength $Rfc2544ProfileRate] != $Frame_Sizes } {
           set Rfc2544ProfileRatesList $Rfc2544ProfileRate
           for { set profile_rate 1} {$profile_rate <= [expr {$Frame_Sizes - [llength $Rfc2544ProfileRate]}] } {incr profile_rate} {
               set Rfc2544ProfileRate_create [stc::create "Rfc2544ProfileRate" -under $testProfileHandle]
               lappend Rfc2544ProfileRatesList $Rfc2544ProfileRate_create
           }
           foreach prof_rate_obj $Rfc2544ProfileRatesList frm_sz $frame_sizes {
               set FrameSize_value [stc::get $prof_rate_obj -FrameSize]
               if {$FrameSize_value != $frm_sz } {
               ::sth::sthCore::invoke stc::config $prof_rate_obj -FrameSize "$frm_sz"
               }
           }
       } else {
          set Rfc2544ProfileRatesList $Rfc2544ProfileRate
       }
    
    
    set prof_load_type [stc::get $validAccess -LoadType]
    
    if {$prof_load_type eq "CUSTOM"} {
       set no_of_framesizes $::sth::Rfctest::userArgsArray(frame_size)
       set Custom_load_list $::sth::Rfctest::userArgsArray(custom_load_list)
       foreach frames $no_of_framesizes cust_load_list $Custom_load_list {
           foreach prof_rate_obj $Rfc2544ProfileRatesList {
               set FrameSize_value [stc::get $prof_rate_obj -FrameSize]
               if {$frames == $FrameSize_value} {
               set AssymProfobj $prof_rate_obj
               ::sth::sthCore::invoke stc::config $AssymProfobj -CustomLoadList "$cust_load_list"
               }
           }
       }
    }
    
    if {$prof_load_type eq "STEP"} {
       set no_of_framesizes $::sth::Rfctest::userArgsArray(frame_size)
       set startLoad $::sth::Rfctest::userArgsArray(load_start)
       set endLoad   $::sth::Rfctest::userArgsArray(load_end)
       set Loadstep  $::sth::Rfctest::userArgsArray(load_step)
       foreach prof_rate_obj $Rfc2544ProfileRatesList {
           foreach frames $no_of_framesizes strtload $startLoad eodload $endLoad stepload $Loadstep {
               set FrameSize_value [stc::get $prof_rate_obj -FrameSize]
               if {$frames == $FrameSize_value} {
                  set AssymProfobj $prof_rate_obj
                  ::sth::sthCore::invoke stc::config $AssymProfobj -LoadStart "$strtload" -LoadEnd "$eodload" -LoadStep "$stepload"
                  break;
               }
           }
       }
    }
    
    if {$prof_load_type eq "RANDOM"} {
       set no_of_framesizes $::sth::Rfctest::userArgsArray(frame_size)
       set min_random_list  $::sth::Rfctest::userArgsArray(random_min_load)
       set max_random_list  $::sth::Rfctest::userArgsArray(random_max_load)
       foreach prof_rate_obj $Rfc2544ProfileRatesList {
          foreach frames $no_of_framesizes min_random $min_random_list max_random $max_random_list {
             set FrameSize_value [stc::get $prof_rate_obj -FrameSize]
             if {$frames == $FrameSize_value} {
                 set AssymProfobj $prof_rate_obj
                 ::sth::sthCore::invoke stc::config $AssymProfobj -RandomMaxLoad "$max_random" -RandomMinLoad "$min_random"
             }
          }
       }
    }




}

proc ::sth::Rfctest::rfc2544_asymmetric_profile_delete { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_config_delete $rklName"

    upvar 1 $rklName returnKeyedList
    set children [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-AccessConcentratorGenParams]
    foreach accessconcParam $children {
        set configchildren [::sth::sthCore::invoke stc::get $accessconcParam -children]
        if {$configchildren ne ""} {
           set configchildren1 [::sth::sthCore::invoke stc::get $configchildren -children]
        }
        
    }
    

    if {![info exists ::sth::Rfctest::userArgsArray(profile_handle)]} {
        return -code error "the switch \"-profile_name\" is mandatory in delete mode"
    } else {
        set testProfileHandle $::sth::Rfctest::userArgsArray(profile_handle)
    }
    ::sth::sthCore::invoke stc::perform delete -configlist $::sth::Rfctest::userArgsArray(profile_handle)
    ::sth::sthCore::invoke stc::perform AccessConcentratorGenConfigExpandCommand -GenParams $accessconcParam
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList

}



proc ::sth::Rfctest::rfc2544_asymmetric_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_config_modify $rklName"
    
    upvar 1 $rklName returnKeyedList

    if {![info exists ::sth::Rfctest::userArgsArray(handle)]} {
       return -code error "the switch \"-handle\" is mandatory in modify mode"
    } else {
        set testConfigHandle $::sth::Rfctest::userArgsArray(handle)
    }

    set test_type $::sth::Rfctest::userArgsArray(test_type) 
    set accessConcentrator [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-AccessConcentratorGenParams]
    foreach accessconc $accessConcentrator {
        set AccessGenChild [::sth::sthCore::invoke stc::get $accessconc -children]
        if {$AccessGenChild ne ""} {
           set accessconc $accessconc
        }
       
    }
    set testConfigHandle [configrfc2544_asymmetric_config modify test_type accessconc]
    configImix $testConfigHandle
    
    ::sth::sthCore::invoke stc::perform AccessConcentratorGenConfigExpandCommand -GenParams $accessconc
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        return -code error $applyError
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    keylset returnKeyedList handle $testConfigHandle
    return $returnKeyedList
}

proc ::sth::Rfctest::rfc2544_asymmetric_config_delete { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_config_delete $rklName"
    
    upvar 1 $rklName returnKeyedList
    set accessConcParam [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-AccessConcentratorGenParams]
    foreach accessconcentrator $accessConcParam {
         set ConcChild [::sth::sthCore::invoke stc::get $accessconcentrator -children]
         if {$ConcChild ne ""} {
         set DeleteAccessconc $accessconcentrator
         }
    }
    
    if {![info exists ::sth::Rfctest::userArgsArray(handle)]} {
        return -code error "the switch \"-handle\" is mandatory in delete mode"
    } else {
        set testConfigHandle $::sth::Rfctest::userArgsArray(handle)
    }
    
    set ports [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Port]
    
    foreach port $ports {
            set streamblock [::sth::sthCore::invoke stc::get $port -children-StreamBlock]
            lappend streamblocks $streamblock
    }
    
    ::sth::sthCore::invoke stc::perform delete -configlist $::sth::Rfctest::userArgsArray(handle)
    foreach streamblk $streamblocks {
       foreach sb $streamblk {
           ::sth::sthCore::invoke stc::delete $sb
       }
    }
    ::sth::sthCore::invoke stc::perform AccessConcentratorGenConfigExpandCommand -GenParams $DeleteAccessconc
    
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
         return -code error $applyError
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList        
 
}

proc ::sth::Rfctest::test_rfc2544_config_create { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc2544_config_create $rklName"
    
    upvar 1 $rklName returnKeyedList
    variable ipv4Version
    variable ipv6Version

    set trafficDescriptorGroup [::sth::sthCore::invoke stc::create TrafficDescriptorGroup -under $::sth::GBLHNDMAP(project)]
     
    set trafficDescriptor [::sth::sthCore::invoke stc::create TrafficDescriptor -under $trafficDescriptorGroup]
    
    configTrafficDescriptor test_rfc2544_config $trafficDescriptor create
    
    set testType $::sth::Rfctest::userArgsArray(test_type)
    
    set testConfigHandle [configRfc2544Test create $testType]
    configImix $testConfigHandle 
    if {$::sth::Rfctest::userArgsArray(endpoint_creation) == 1} {
    if {![info exists ::sth::Rfctest::userArgsArray(src_port)] || ![info exists ::sth::Rfctest::userArgsArray(src_port)]} {
        ::sth::sthCore::processError returnKeyedList "Please provide src_port and dest_port options when endpoint_creation is set"
        return $returnKeyedList
    } else {
        set srcPort $::sth::Rfctest::userArgsArray(src_port)
        set dstPort $::sth::Rfctest::userArgsArray(dst_port)
        ::sth::sthCore::invoke stc::config $trafficDescriptor "-SrcBinding-targets {$srcPort} -DstBinding-targets {$dstPort}"
    }
    } else {
    if {[info exists ::sth::Rfctest::userArgsArray(src_endpoints)] && [info exists ::sth::Rfctest::userArgsArray(dst_endpoints)]} {
        set srcBlockHandle [GetIpOrNetworkBlockHandle $::sth::Rfctest::userArgsArray(src_endpoints)]
        set dstBlockHandle [GetIpOrNetworkBlockHandle $::sth::Rfctest::userArgsArray(dst_endpoints)]
        ::sth::sthCore::invoke stc::config $trafficDescriptor "-SrcBinding-targets {$srcBlockHandle} -DstBinding-targets {$dstBlockHandle}"
    }
    if {[info exists ::sth::Rfctest::userArgsArray(streamblock_handle)]} {
        set streamHandle [list $::sth::Rfctest::userArgsArray(streamblock_handle)]
    }
       
    }
    #create streamblockfile
    set streamProfileHnd [::sth::sthCore::invoke stc::create Rfc2544StreamBlockProfile -under $testConfigHandle]
    
    ::sth::sthCore::invoke stc::config $testConfigHandle "-TrafficDescriptorGroupBinding-targets $trafficDescriptorGroup"

    set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
    configRfc5180 create $testConfigHandle
    ::sth::sthCore::invoke stc::perform ExpandBenchmarkConfig -Config $testConfigHandle
    set cmds [::sth::sthCore::invoke stc::get $seqHandle -children]

    foreach cmd $cmds {
    set testConfigHandle [::sth::sthCore::invoke stc::get $cmd -children]
    #just get the new created rfc test config
    switch -- $testType {
        b2b {
        if {[regexp -- "rfc2544backtobackframesconfig" $testConfigHandle]} {
            set returnHnd $testConfigHandle
        }
        if {[regexp -- "rfc2544backtobackframesgroupcommand" $cmd]} {
            foreach seqCmd $testConfigHandle {
            set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
            if {[regexp -- "rfc2544backtobackframesconfig" $configHandle]} {
                set returnHnd $configHandle
            }
            }
        }
        }
        fl {
        if {[regexp -- "rfc2544framelossconfig" $testConfigHandle]} {
            set returnHnd $testConfigHandle
        }
        if {[regexp -- "rfc2544framelosssequencergroupcommand" $cmd]} {
            foreach seqCmd $testConfigHandle {
            set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
            if {[regexp -- "rfc2544framelossconfig" $configHandle]} {
                set returnHnd $configHandle
            }
            }
        }
        }
        throughput {
        if {[regexp -- "rfc2544throughputconfig" $testConfigHandle]} {
            set returnHnd $testConfigHandle
        }
        if {[regexp -- "rfc2544throughputsequencergroupcommand" $cmd]} {
            foreach seqCmd $testConfigHandle {
            set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
            if {[regexp -- "rfc2544throughputconfig" $configHandle]} {
                set returnHnd $configHandle
            }
            }
        }
        }
        latency {
        if {[regexp -- "rfc2544latencyconfig" $testConfigHandle]} {
            set returnHnd $testConfigHandle
        }
        if {[regexp -- "rfc2544latencysequencergroupcommand" $cmd]} {
            foreach seqCmd $testConfigHandle {
            set configHandle [::sth::sthCore::invoke stc::get $seqCmd -children]
            if {[regexp -- "rfc2544latencyconfig" $configHandle]} {
                set returnHnd $configHandle
            }
            }
        }
        }
    }
    }

    if {[info exists ::sth::Rfctest::userArgsArray(streamblock_handle)]} {
    set cmdHanld [::sth::sthCore::invoke stc::get $returnHnd -parent]
    ::sth::sthCore::invoke stc::config $cmdHanld "-StreamBlockList $streamHandle"
    set streamProfileHnd [::sth::sthCore::invoke stc::get $returnHnd -children-rfc2544streamblockprofile]
    ::sth::sthCore::invoke stc::config $streamProfileHnd "-StreamBlockList $streamHandle"
    
    ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList $::sth::Rfctest::userArgsArray(streamblock_handle)
    }
    
  #apply config
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        return -code error $applyError
    }
#    
#    # prepare the keyed list to be returned to HLTAPI layer
#    if {[catch { keylset returnKeyedList handle $routers } err]} {
#    ::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. $err"
#    }    
#
 
  keylset returnKeyedList status $::sth::sthCore::SUCCESS
  keylset returnKeyedList handle $returnHnd
#    
    return $returnKeyedList
}

proc ::sth::Rfctest::test_rfc2544_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc2544_config_modify $rklName"
    
    upvar 1 $rklName returnKeyedList
        
        if {![info exists ::sth::Rfctest::userArgsArray(handle)]} {
        return -code error "the switch \"-handle\" is mandatory in modify mode"
    } else {
        set testConfigHandle $::sth::Rfctest::userArgsArray(handle)
    }
        

        set trafficGroup [::sth::sthCore::invoke stc::get $testConfigHandle -TrafficDescriptorGroupBinding-targets]
        
        if {$trafficGroup != ""} {
            set trafficDescriptor [::sth::sthCore::invoke stc::get $trafficGroup -children]
            configTrafficDescriptor test_rfc2544_config $trafficDescriptor create
        }
        
        set testConfigHandle [configRfc2544Test modify ""]
        configImix $testConfigHandle 
        if {[info exists ::sth::Rfctest::userArgsArray(endpoint_creation)] && $::sth::Rfctest::userArgsArray(endpoint_creation) == 1} {
            if {[info exists ::sth::Rfctest::userArgsArray(src_port)]&& [info exists ::sth::Rfctest::userArgsArray(dst_port)]} {
                set srcPort $::sth::Rfctest::userArgsArray(src_port)
                set dstPort $::sth::Rfctest::userArgsArray(dst_port)
                ::sth::sthCore::invoke stc::config $trafficDescriptor "-SrcBinding-targets {$srcPort} -DstBinding-targets {$dstPort}"
            }
        } else {
            if {[info exists ::sth::Rfctest::userArgsArray(streamblock_handle)]} {
                ::sth::sthCore::invoke stc::config $trafficDescriptor "-StreamBlockBinding-targets $::sth::Rfctest::userArgsArray(streamblock_handle)"
            }
           
        }
        
    
        set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
    configRfc5180 modify $testConfigHandle
        set cmds [::sth::sthCore::invoke stc::get $seqHandle -children]
        if {[info exists ::sth::Rfctest::userArgsArray(streamblock_handle)]} {
            foreach cmd $cmds {
                ::sth::sthCore::invoke stc::config $cmd "-StreamBlockList $::sth::Rfctest::userArgsArray(streamblock_handle)"
            
            set testConfigHandle [::sth::sthCore::invoke stc::get $cmd -children]
            set streamProfileHnd [::sth::sthCore::invoke stc::get $testConfigHandle -children]
            ::sth::sthCore::invoke stc::config $streamProfileHnd "-StreamBlockList $::sth::Rfctest::userArgsArray(streamblock_handle)"
            }
        
            ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList $::sth::Rfctest::userArgsArray(streamblock_handle)
            
        }
        
      #apply config
     if {[catch {::sth::sthCore::doStcApply} applyError]} {
        return -code error $applyError
     }

   keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

proc ::sth::Rfctest::test_rfc2544_config_delete { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc2544_config_delete $rklName"
    
    upvar 1 $rklName returnKeyedList
        
        if {![info exists ::sth::Rfctest::userArgsArray(handle)]} {
        return -code error "the switch \"-handle\" is mandatory in delete mode"
    } else {
        set testConfigHandle $::sth::Rfctest::userArgsArray(handle)
    }
        
        set testCmdHandle [::sth::sthCore::invoke stc::get $testConfigHandle -parent]
        
        set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
        
        set cmdlist [::sth::sthCore::invoke stc::get $seqHandle -CommandList]
        set  newcmdlist ""
        foreach cmd $cmdlist {
           if {$cmd != $testCmdHandle} {
               lappend newcmdlist $cmd
           }
        }
        if {$newcmdlist != ""} {
            ::sth::sthCore::invoke stc::config $seqHandle "-CommandList $newcmdlist"
        } else {
            ::sth::sthCore::invoke stc::config $seqHandle "-CommandList {}"
        }
        
        set objectList [::sth::sthCore::invoke stc::get $seqHandle -children]
        foreach object $objectList {
            if {$object == $testCmdHandle} { 
                ::sth::sthCore::invoke stc::delete $object
            }
        }
        
        if {[catch {::sth::sthCore::doStcApply} applyError]} {
            return -code error $applyError
        }
        
        keylset returnKeyedList status $::sth::sthCore::SUCCESS

        return $returnKeyedList
        

}

proc ::sth::Rfctest::rfc2544_asymmetric_control { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_control $rklName"
    upvar 1 $rklName returnKeyedList
    set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
    

    switch -- $::sth::Rfctest::userArgsArray(action) {
        run {
            ::sth::sthCore::invoke stc::perform sequencerStart
            set cmdList [::sth::sthCore::invoke stc::get $seqHandle -children]
            
            if {[regexp "rfc2544.*sequencergroupcommand" $cmdList]} {
                set rfcSequencerGroupCmd ""
                foreach cmd $cmdList {
                    if {[regexp "rfc2544.*sequencergroupcommand" $cmd]} {
                        set rfcSequencerGroupCmd $cmd
                    }      
                }
            if {$rfcSequencerGroupCmd!=""} {
                set cmdList $rfcSequencerGroupCmd
            }
            } 
            after 2000
            
            if {$::sth::Rfctest::userArgsArray(wait)} {
                set tmpStep ""
                foreach cmd $cmdList {
                    for {set i 0} {$i<10000} {incr i} {
                        
                        #process the error/fail branch
                        ::sth::Rfctest::checkSeqState $seqHandle
                        
                        set state [::sth::sthCore::invoke stc::get $cmd -state]
                        if {$state != "RUNNING"} {
                            puts "the exit state is $state"
                            break
                        }
            if {[regexp ".*groupcommand" $cmd]} {
                set currentStep [::sth::sthCore::invoke stc::get $cmd -ProgressCurrentStepName]
                
            } else {
                  set currentStep [::sth::sthCore::invoke stc::get $cmd -teststatus]
                 
              } 

            if {$currentStep != $tmpStep} {
                regexp {(^.+?)command.*} $cmd match testname
                puts "$testname test is running, $currentStep\n"
                set tmpStep $currentStep
            }
            after 2000
                    }
                }
            #delete previous rfc2544 test instance
            ::sth::Rfctest::cleanUpRfc2544 $seqHandle
            }
           
            
        }
        stop {
            ::sth::sthCore::invoke stc::perform sequencerStop
            #delete previous rfc2544 test instance
            ::sth::Rfctest::cleanUpRfc2544 $seqHandle
        }
    }
     
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
  
    return $returnKeyedList

}

proc ::sth::Rfctest::rfc2544_asymmetric_stats { rklName } {
     ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::rfc2544_asymmetric_stats $rklName"
    upvar 1 $rklName trafficStatsKeyedList
    global curDir
    global resultDir
    
    set Result ""        
    set trafficStatsKeyedList ""
     switch -- $::sth::Rfctest::userArgsArray(test_type) {
        fl {
            set testType "2544-FL"
            set dbFile [getDatabaseList $testType]
            sqlite db $dbFile
            set cmdReturn1 [db eval "select trialnum, framesize, IntendedLoad, framesizetype, framelengthdistribution, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter, txsigframecount, rxsigframecount FROM Rfc2544AsymmetricFrameLossPerLoadResult"]
            set row [db eval "select trialnum, framesize, IntendedLoad, framesizetype, framelengthdistribution, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter, txsigframecount, rxsigframecount FROM Rfc2544AsymmetricFrameLossPerLoadResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricFrameLossPerLoadResult"]
            set first 0
            set last [expr $row_length - 1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn1 $first $last]
                set detailList [list trial_num frame_size intended_load frame_size_type frame_length_distribution min_latency avg_latency max_latency min_jitter avg_jitter max_jitter tx_sig_frame_count rx_sig_frame_count]
                foreach stcName $detailList value $res {
                   keylset final_value $stcName $value
                   
                }
               
               keylset Result $key $final_value
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }

            keylset trafficStatsKeyedList FrameLossPerLoadResult $Result
           
            
            set cmdReturn2 [db eval "select Duration, FrameSize, FrameSizeType,IterationNum, LoadIterationNum FROM Rfc2544AsymmetricFrameLossStreamGroupResult"]
            set row [db eval "select Duration, FrameSize, FrameSizeType, IterationNum, LoadIterationNum FROM Rfc2544AsymmetricFrameLossStreamGroupResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricFrameLossStreamGroupResult"]
            set first 0
            set last [expr $row_length-1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn2 $first $last]
                set detailList [list duration frame_size frame_size_type iteration_num load_iteration_num]
                foreach stcName $detailList value $res {
                   keylset final_value_tbl2 $stcName $value
                   
                }
               keylset Result_two $key $final_value_tbl2
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
               
            }
            
            keylset trafficStatsKeyedList FrameLossStreamGroupResult $Result_two

            set cmdReturn2 [db eval "select LoadPassed, LoadResult, Result, RxFrameCount, TxFrameCount, StreamBlockHnd  FROM Rfc2544AsymmetricFrameLossStreamResult"]
            set row [db eval "select LoadPassed, LoadResult, Result, RxFrameCount, TxFrameCount, StreamBlockHnd  FROM Rfc2544AsymmetricFrameLossStreamResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricFrameLossStreamResult"]
            set first 0
            set last [expr $row_length-1]
                       
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn2 $first $last]
                set detailList [list load_passed loadresult result rx_frame_count tx_frame_count streamblock_hnd]
                foreach stcName $detailList value $res {
                   keylset final_valuet_tbl3 $stcName $value
                   
                }
               keylset Result_three $key $final_valuet_tbl3
                set first [expr {$first + [expr $row_length]}]
                set last [expr {$last + [expr $row_length]}]
                
            }
            
            keylset trafficStatsKeyedList FrameLossStreamResult $Result_three
        
        }
        throughput {
            set testType "2544-Tput"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            set cmdReturn1 [db eval "SELECT trialnum, framesize, framesizetype, framelengthdistribution, IntendedLoad,OfferedLoad,ThroughputRate,ForwardingRate,MbpsLineRate,PercentLoss,MaxLatencyThresholdExceeded,OutOfSeqThresholdExceeded, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter FROM Rfc2544AsymmetricThroughputPerFrameSizeResult"]
            set row [db eval "SELECT trialnum, framesize, framesizetype, framelengthdistribution, IntendedLoad,OfferedLoad,ThroughputRate,ForwardingRate,MbpsLineRate,PercentLoss,MaxLatencyThresholdExceeded,OutOfSeqThresholdExceeded, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter FROM Rfc2544AsymmetricThroughputPerFrameSizeResult LIMIT 1"] 
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricThroughputPerFrameSizeResult"]
            set first 0
            set last [expr $row_length-1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn1 $first $last]
                set detailList [list trial_num frame_size frame_size_type frame_length_distribution intended_load offered_load throughput_rate forwarding_rate mbps_line_rate percent_loss max_latency_threshold_exceeded out_of_seq_threshold_exceeded min_latency avg_latency max_latency min_jitter avg_jitter max_jitter]
                foreach stcName $detailList value $res {
                   keylset final_value $stcName $value
                }
               keylset Result $key $final_value
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }
            
            keylset trafficStatsKeyedList Rfc2544AsymmetricThroughputPerFrameSizeResult $Result 

            set cmdReturn2 [db eval "SELECT Duration, FrameLengthDistribution, FrameSize, FrameSizeType, IterationNum FROM Rfc2544AsymmetricThroughputStreamGroupResult"]
            set row [db eval "SELECT Duration, FrameLengthDistribution, FrameSize, FrameSizeType, IterationNum FROM Rfc2544AsymmetricThroughputStreamGroupResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricThroughputStreamGroupResult"]
            set first 0
            set last [expr $row_length -1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn2 $first $last]
                
                set detailList [list duration frame_length_distribution frame_size frame_size_type iteration_num]
                foreach stcName $detailList value $res {
                   keylset final_value_tbl2 $stcName $value
                   
                }
               keylset Result_two $key $final_value_tbl2
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }
            
            keylset trafficStatsKeyedList Rfc2544AsymmetricThroughputStreamGroupResult $Result_two

            set cmdReturn3 [db eval "SELECT LoadPassed, LoadResult, Result, RxFrameCount, TxFrameCount, StreamBlockHnd FROM Rfc2544AsymmetricThroughputStreamResult"]
            set row [db eval "SELECT LoadPassed, LoadResult, Result, RxFrameCount, TxFrameCount, StreamBlockHnd FROM Rfc2544AsymmetricThroughputStreamResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricThroughputStreamResult"]
            set first 0
             set last [expr $row_length -1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn3 $first $last]
                set detailList [list load_passed load_result result rx_frame_count tx_frame_count streamblock_hnd]
                foreach stcName $detailList value $res {
                   keylset final_value_tbl3 $stcName $value
                   
                }
               keylset Result_three $key $final_value_tbl3
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }
            keylset trafficStatsKeyedList Rfc2544AsymmetricThroughputStreamResult $Result_three
        }
        latency {
            set testType "2544-Lat"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            set cmdReturn1 [db eval "SELECT TrialNum,FrameSize,IntendedLoad, FrameSizeType, FrameLengthDistribution, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter, txsigframecount, rxsigframecount FROM Rfc2544AsymmetricLatencyPerLoadResult"]
            set row [db eval "SELECT TrialNum,FrameSize, IntendedLoad,FrameSizeType, FrameLengthDistribution, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter, txsigframecount, rxsigframecount FROM Rfc2544AsymmetricLatencyPerLoadResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricLatencyPerLoadResult"]
            set first 0
            set last [expr $row_length-1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn1 $first $last]
                set detailList [list trialNum frame_size intended_load frame_size_type frame_length_distribution min_latency avg_latency max_latency min_jitter avg_jitter max_jitter tx_sig_frame_count rx_sig_frame_count]
                foreach stcName $detailList value $res {
                   keylset final_value $stcName $value
                }
               keylset Result $key $final_value
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }
             keylset trafficStatsKeyedList Rfc2544AsymmetricLatencyPerLoadResult $Result

            set cmdReturn2 [db eval "SELECT Duration, FrameLengthDistribution, FrameSize, FrameSizeType, IterationNum, LoadIterationNum FROM Rfc2544AsymmetricLatencyStreamGroupResult"]
            set row [db eval "SELECT Duration, FrameLengthDistribution, FrameSize, FrameSizeType, IterationNum, LoadIterationNum FROM Rfc2544AsymmetricLatencyStreamGroupResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricLatencyStreamGroupResult"]
            set first 0
            set last [expr $row_length-1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn2 $first $last]
                set detailList [list duration frame_length_distribution frame_size frame_size_type iteration_num load_iteration_num]
                foreach stcName $detailList value $res {
                   keylset final_value_tbl2 $stcName $value
                }
               keylset Result_two $key $final_value_tbl2
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }
             keylset trafficStatsKeyedList Rfc2544AsymmetricLatencyStreamGroupResult $Result_two
             

            set cmdReturn3 [db eval "SELECT AvgJitter, LoadPassed, LoadResult, MaxJitter, MaxLatency, MinJitter, MinLatency, Result, RxFrameCount, TxFrameCount, StreamBlockHnd, TotalJitter, TotalLatency   FROM Rfc2544AsymmetricLatencyStreamResult"]
            set row [db eval "SELECT AvgJitter, LoadPassed, LoadResult, MaxJitter, MaxLatency, MinJitter, MinLatency, Result, RxFrameCount, TxFrameCount, StreamBlockHnd, TotalJitter, TotalLatency   FROM Rfc2544AsymmetricLatencyStreamResult LIMIT 1"]
            set row_length [llength $row]
            set count [db eval "SELECT count(*) from Rfc2544AsymmetricLatencyStreamResult"]
            set first 0
            set last [expr $row_length-1]
            for {set key 1} {$key <= $count} {incr key} {
                set res [lrange $cmdReturn3 $first $last]
                set detailList [list avg_jitter load_passed load_result max_jitter max_latency min_jitter min_latency result rx_frame_count tx_frame_count streamblock_hnd total_jitter total_latency]
                foreach stcName $detailList value $res {
                   keylset final_valuet_tbl3 $stcName $value
                }
               keylset Result_three $key $final_valuet_tbl3
               set first [expr {$first + [expr $row_length]}]
               set last [expr {$last + [expr $row_length]}]
            }
             keylset trafficStatsKeyedList Rfc2544AsymmetricLatencyStreamResult $Result_three
        }
    }
    db close $dbFile
    
    cd /
    cd $curDir
    cd "Results"
    set test [pwd]
    if {$::sth::Rfctest::userArgsArray(clear_result)} {
        file delete -force $resultDir
    }
   
    cd /
    cd $curDir
   
    keylset trafficStatsKeyedList status $::sth::sthCore::SUCCESS
    return $trafficStatsKeyedList

}

proc ::sth::Rfctest::test_rfc2544_control { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc2544_control $rklName"
    upvar 1 $rklName returnKeyedList
    set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
    
     
    switch -- $::sth::Rfctest::userArgsArray(action) {
        run {
            ::sth::sthCore::invoke stc::perform sequencerStart
            set cmdList [::sth::sthCore::invoke stc::get $seqHandle -children]
            
            if {[regexp "rfc2544.*sequencergroupcommand" $cmdList]} {
                set rfcSequencerGroupCmd ""
                foreach cmd $cmdList {
                    if {[regexp "rfc2544.*sequencergroupcommand" $cmd]} {
                        set rfcSequencerGroupCmd $cmd
                    }      
                }
            if {$rfcSequencerGroupCmd!=""} {
                set cmdList $rfcSequencerGroupCmd
            }
            } 
            after 2000
            
            if {$::sth::Rfctest::userArgsArray(wait)} {
                set tmpStep ""
                foreach cmd $cmdList {
                    if {[regexp -nocase "benchmarksequenceablecommandproperties" $cmd ]} {continue;}
                    for {set i 0} {$i<10000} {incr i} {
                        
                        #process the error/fail branch
                        ::sth::Rfctest::checkSeqState $seqHandle
                        set state [::sth::sthCore::invoke stc::get $cmd -state]
                        if {$state != "RUNNING"} {
                            puts "the exit state is $state"
                            break
                        }
                        if {[regexp ".*groupcommand" $cmd]} {
                            set currentStep [::sth::sthCore::invoke stc::get $cmd -ProgressCurrentStepName]
                        } else {
                            set currentStep [::sth::sthCore::invoke stc::get $cmd -teststatus]
                        } 
        
                        if {$currentStep != $tmpStep} {
                            regexp {(^.+?)command.*} $cmd match testname
                            puts "$testname test is running, $currentStep\n"
                            set tmpStep $currentStep
                        }
                        after 2000
                    }
                }
                #delete previous rfc2544 test instance
                ::sth::Rfctest::cleanUpRfc2544 $seqHandle
            }
           
            
        }
        
        stop {
            ::sth::sthCore::invoke stc::perform sequencerStop
            #delete previous rfc2544 test instance
            ::sth::Rfctest::cleanUpRfc2544 $seqHandle
        }
    }
     
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
  
    return $returnKeyedList
}

proc ::sth::Rfctest::test_rfc2544_info { rklName } {
     ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc2544_control $rklName"
    upvar 1 $rklName trafficStatsKeyedList
    global curDir
    global resultDir
    
    set trafficStatsKeyedList ""
     switch -- $::sth::Rfctest::userArgsArray(test_type) {
        b2b {
            set testType "2544-BTBF"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
    
            set cmdReturn1 [db eval "SELECT TrialNum FROM Rfc2544Back2BackPerIterationResult"]
            set query "select trialnum,framesize,framesizetype, framelengthdistribution,IntendedLoad,OfferedLoad,txsigframecount,rxsigframecount,FrameLoss,burstsize,durationinsec,minlatency,maxlatency,avglatency FROM Rfc2544Back2BackPerFrameSizeResult"
            set cmdReturn2 [db eval $query]
            set detailList [list framelengthdistribution iload oload tx_frames rx_frames frame_lost burst_size burst_duration min_latency max_latency avg_latency]
            set testNum [llength $cmdReturn1]
            set summaryList [list burst_size burst_duration iload tx_frames rx_frames frame_lost min_latency max_latency avg_latency]
            set frame_size_mode [::sth::sthCore::invoke stc::get [lindex [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-rfc2544backtobackframesconfig] 0] -FrameSizeIterationMode]
            set rfc_type "rfc2544b2b"
            set trafficStatsKeyedList [get_rfc2544_b2b_throughput_info $detailList $testNum $cmdReturn2 $summaryList $frame_size_mode $rfc_type]
            if ($::sth::Rfctest::userArgsArray(enable_load_detail)) {
            keylset trafficStatsKeyedList  $rfc_type.load_detail [get_rfc2544_detail_per_framesize_info $testType $rfc_type $cmdReturn1 $detailList $frame_size_mode] 
            }
        }
        fl {
            set testType "2544-FL"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            set cmdReturn1 [db eval "SELECT TrialNum FROM Rfc2544FrameLossPerIterationResult"]
            set query "select trialnum,framesize,IntendedLoad,framesizetype, framelengthdistribution, txsigframecount,rxsigframecount,FrameLoss,PercentLoss FROM Rfc2544FrameLossPerLoadResult"
            set cmdReturn2 [db eval $query]
            set testNum [llength $cmdReturn1]
            set detailList [list framelengthdistribution tx_frames rx_frames frame_lost frame_loss]
            set summaryList [list tx_frames rx_frames frame_lost frame_loss]
            set frame_size_mode [::sth::sthCore::invoke stc::get [lindex [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Rfc2544FrameLossConfig] 0] -FrameSizeIterationMode]
            set rfc_type "rfc2544fl"
            set trafficStatsKeyedList [get_rfc2544_fl_latency_info $detailList $testNum $cmdReturn2 $summaryList $frame_size_mode $rfc_type]
        
        }
        throughput {
            set testType "2544-Tput"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            set cmdReturn1 [db eval "SELECT TrialNum FROM Rfc2544ThroughputPerIterationResult"]
            set query "select trialnum, framesize, framesizetype, framelengthdistribution, IntendedLoad,OfferedLoad,ThroughputRate,ForwardingRate,MbpsLineRate,PercentLoss,MaxLatencyThresholdExceeded,OutOfSeqThresholdExceeded, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter FROM  Rfc2544ThroughputPerFrameSizeResult"
            set cmdReturn2 [db eval $query]
            set detailList [list framelengthdistribution iload oload throughput_percent throughput_fps throughput_mbps frame_loss max_latency_exceed out_of_seq_exceed min_latency avg_latency max_latency min_jitter avg_jitter max_jitter]
            set testNum [llength $cmdReturn1]
            set summaryList [list iload oload throughput_percent throughput_fps throughput_mbps min_latency avg_latency max_latency min_jitter avg_jitter max_jitter]
            set frame_size_mode [::sth::sthCore::invoke stc::get [lindex [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-rfc2544throughputconfig] 0] -FrameSizeIterationMode]
            set rfc_type "rfc2544throughput"
            set trafficStatsKeyedList [get_rfc2544_b2b_throughput_info $detailList $testNum $cmdReturn2 $summaryList $frame_size_mode $rfc_type]
            if ($::sth::Rfctest::userArgsArray(enable_load_detail)) {
            keylset trafficStatsKeyedList  $rfc_type.load_detail [get_rfc2544_detail_per_framesize_info $testType $rfc_type $cmdReturn1 $detailList $frame_size_mode] 
            }
        }
        latency {
            set testType "2544-Lat"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            set cmdReturn1 [db eval "SELECT TrialNum FROM Rfc2544LatencyPerIterationResult"]
            set query "select trialnum,framesize,IntendedLoad,framesizetype, framelengthdistribution,MinLatency,AvgLatency,MaxLatency,MinJitter,AvgJitter,MaxJitter,txsigframecount,rxsigframecount FROM Rfc2544LatencyPerLoadResult"
            set detailList [list framelengthdistribution latency_min latency_avg latency_max jitter_min jitter_avg jitter_max tx_frames rx_frames]
            set cmdReturn2 [db eval $query]
 
            set testNum [llength $cmdReturn1]
            set rfc_type "rfc2544latency"
            set summaryList [list latency_min latency_avg latency_max]
            set frame_size_mode [::sth::sthCore::invoke stc::get [lindex [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Rfc2544LatencyConfig] 0] -FrameSizeIterationMode]
            set trafficStatsKeyedList [get_rfc2544_fl_latency_info $detailList $testNum $cmdReturn2 $summaryList $frame_size_mode $rfc_type]
        }
    }
    
    set x [db close $dbFile]
    
    cd /
    cd $curDir
    cd "Results"
    set test [pwd]
    if {$::sth::Rfctest::userArgsArray(clear_result)} {
        file delete -force $resultDir
    }
    
    cd /
    cd $curDir
    
    keylset trafficStatsKeyedList status $::sth::sthCore::SUCCESS
   
    return $trafficStatsKeyedList
}

proc ::sth::Rfctest::get_rfc2544_b2b_throughput_info {detailList testNum cmdReturn2 summaryList frame_size_mode rfc_type} {
    set no_key_num 3
    set key_num [expr [llength $detailList] + $no_key_num]
    set count [expr [llength $cmdReturn2] / ($key_num*$testNum)]
    set frameSizeList {}
    set imixDistList {}
    for {set i 1} {$i <= $testNum} {incr i} {
        set frameSizevalueList {}
        for {set j 1} {$j <= $count} {incr j} {
            set n 0
            set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + 1]
            set frameSize [lindex $cmdReturn2 $index]
            regsub -all {\.0+$} $frameSize "" frameSize
            regsub -all {\.+} $frameSize "_" frameSize
            lappend frameSizeList $frameSize
            if { $frameSizevalueList != "" } {
                lappend frameSizevalueList $frameSize
                
            } else {
                set frameSizevalueList $frameSize
                
            }
            set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + 2]
            set framesizetype [lindex $cmdReturn2 $index]
           
            #get  the imix distribute list 
            if {[regexp -nocase "imix" $framesizetype]} {
                if {$i == 1} {
                    set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + $no_key_num +$n]
                    set framelengthdistribution [lindex $cmdReturn2 $index]
                    lappend imixDistList $framelengthdistribution
                }
            }
            foreach stcName $detailList {
                set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + $no_key_num +$n]
                set value [lindex $cmdReturn2 $index]
                if {[regexp "framelengthdistribution" $stcName]} {
                    if {[regexp -nocase "imix" $framesizetype]} {
                        keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value $frameSizevalueList
                        keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.$stcName $value
                    }
                } else {
                    keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value $frameSizevalueList
                    keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.$stcName $value
                }
                incr n
            }
        }
    }
    
    keylset trafficStatsKeyedList $rfc_type.summary.total_iteration_count $testNum
    
    if {[regexp -nocase "imix" $frame_size_mode]} {
        set frameSizeValueList ""
        foreach imixDist $imixDistList {
            set frameSizeValue 0
            for {set i 1} {$i <= $testNum} {incr i} {
                set frameSizeList [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value]
                foreach frameSize $frameSizeList {
                    set imixDistEach [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.framelengthdistribution]
                    if {$imixDist == $imixDistEach} {
                        regsub -all "_" $frameSize {.} frameSize
                        set frameSizeValue [expr $frameSizeValue + $frameSize]
                    }
                }
            }
            set frameSizeValue [expr $frameSizeValue/$testNum]
            regsub -all {\.+} $frameSizeValue "_" frameSizeValue
            lappend frameSizeValueList $frameSizeValue
            foreach stcName $summaryList {
                set value 0
                for {set i 1} {$i <= $testNum} {incr i} {
                    set frameSizeList [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value ]
                    foreach frameSize $frameSizeList {
                        set imixDistEach [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.framelengthdistribution]
                        if {$imixDist == $imixDistEach} {
                            set tempValue [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.$stcName]    
                            set value [expr $value + $tempValue]
                        }
                    }
                }
                set value [expr $value/$testNum] 
                keylset trafficStatsKeyedList $rfc_type.summary.frame_size.$frameSizeValue.$stcName $value
            }
        }
        keylset trafficStatsKeyedList $rfc_type.summary.frame_size.frame_size_value $frameSizeValueList
        
    } else {
        foreach frameSize $frameSizeList {
            foreach stcName $summaryList {
                set value 0
                for {set i 1} {$i <= $testNum} {incr i} {
                    set frame_size_value [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value ]
                    foreach eachFrame $frame_size_value {
                        if { $frameSize == $eachFrame } {
                            set tempValue [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.$stcName]    
                            set value [expr $value + $tempValue]
                        }
                    }
                }
                set value [expr $value/$testNum] 
                keylset trafficStatsKeyedList $rfc_type.summary.frame_size.frame_size_value $frameSizevalueList
                keylset trafficStatsKeyedList $rfc_type.summary.frame_size.$frameSize.$stcName $value
            }
        }
    }
    return $trafficStatsKeyedList
}

proc ::sth::Rfctest::get_rfc2544_fl_latency_info {detailList testNum cmdReturn2 summaryList frame_size_mode rfc_type} {
    set no_key_num 4
    set key_num [expr [llength $detailList] + $no_key_num]
    set count [expr [llength $cmdReturn2] / ($key_num*$testNum)]
    set frameSizeList {}
    set imixDistList {}
    set loadValueList {}
    for {set i 1} {$i <= $testNum} {incr i} {
        set frameSizevalueList {}
        for {set j 1} {$j <= $count} {incr j} {
            set n 0
            set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + 1]
            set frameSize [lindex $cmdReturn2 $index]
            regsub -all {\.0+$} $frameSize "" frameSize
            regsub -all {\.+} $frameSize "_" frameSize
            lappend frameSizeList $frameSize
            set flag 0
            foreach item $frameSizevalueList {
               if {$frameSize == $item} {
                   set flag 1
                   break
               }
            }
            if {!$flag} {
               lappend frameSizevalueList $frameSize
            }
            set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + 3]
            set framesizetype [lindex $cmdReturn2 $index]
            #get  the imix distribute list 
            if {[regexp -nocase "imix" $framesizetype]} {
                if {$i == 1} {
                    set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + $no_key_num +$n]
                    set framelengthdistribution [lindex $cmdReturn2 $index]
                    if {[lsearch $imixDistList $framelengthdistribution] == -1} {
                        lappend imixDistList $framelengthdistribution
                    }
                }
            }
            set loadValue [lindex $cmdReturn2 [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + 2]]
            regsub -all {\.0+} $loadValue "" loadValue
            set flag 0
            foreach item $loadValueList {
                if {$loadValue == $item} {
                   set flag 1
                   break
                }
            }
            if {!$flag} {
               lappend loadValueList $loadValue
            }
            foreach stcName $detailList {
                set index [expr ($i-1)*$count*$key_num + ($j-1)*$key_num + $no_key_num +$n]
                set value [lindex $cmdReturn2 $index]
                if {[regexp "framelengthdistribution" $stcName]} {
                    if {[regexp -nocase "imix" $framesizetype]} {
                        keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value $frameSizevalueList
                        keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.load.$loadValue.$stcName $value
                    }
                } else {
                    keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value $frameSizevalueList
                    keylset trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.load.$loadValue.$stcName $value
                }
                incr n
            }
        }
    }
    
    keylset trafficStatsKeyedList $rfc_type.summary.total_iteration_count $testNum
                        
    if {[regexp -nocase "imix" $frame_size_mode]} {
        set frameSizeValueList ""
        foreach imixDist $imixDistList {
            foreach loadValue $loadValueList { 
                set frameSizeValue 0
                for {set i 1} {$i <= $testNum} {incr i} {
                    set frameSizeList [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value]
                    foreach frameSize $frameSizeList {
                        if {[catch {set imixDistEach [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.load.$loadValue.framelengthdistribution]}]} {
                            continue
                        } else {
                            if {$imixDist == $imixDistEach} {
                                regsub -all "_" $frameSize {.} frameSize
                                set frameSizeValue [expr $frameSizeValue + $frameSize]
                            }
                        }
                    }
                }
                set frameSizeValue [expr $frameSizeValue/$testNum]
                regsub -all {\.+} $frameSizeValue "_" frameSizeValue
                if {[lsearch $frameSizeValueList $frameSizeValue] == -1} {
                    lappend frameSizeValueList $frameSizeValue
                }

                foreach stcName $summaryList {
                    set value 0
                    for {set i 1} {$i <= $testNum} {incr i} {
                        set frameSizeList [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value]
                        foreach frameSize $frameSizeList {
                            if {[catch {set imixDistEach [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.load.$loadValue.framelengthdistribution]}]} {
                                continue
                            } else {
                                if {$imixDist == $imixDistEach} {
                                    set tempValue [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.load.$loadValue.$stcName]    
                                    set value [expr $value + $tempValue]
                                }
                            }
                        }
                    }
                    set value [expr $value/$testNum] 
                    keylset trafficStatsKeyedList $rfc_type.summary.frame_size.$frameSizeValue.load.$loadValue.$stcName $value
                }
            }
        }
        keylset trafficStatsKeyedList $rfc_type.summary.frame_size.frame_size_value $frameSizeValueList
    } else {    
        foreach frameSize $frameSizeList {
            foreach loadValue $loadValueList {
                foreach stcName $summaryList {
                    set value 0
                    for {set i 1} {$i <= $testNum} {incr i} {
                        set frame_size_value [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.frame_size_value]
                        foreach eachFrame $frame_size_value {
                            if { $frameSize == $eachFrame } {
                                if {[catch {set tempValue [keylget trafficStatsKeyedList $rfc_type.detail.iteration.$i.frame_size.$frameSize.load.$loadValue.$stcName]}]} {
                                    #when framesize is random, the framesize for every load can be different.
                                    continue
                                    
                                } else {
                                    set value [expr $value + $tempValue]
                                }
                            }
                        }
                    }
                    set value [expr $value/$testNum] 
                    keylset trafficStatsKeyedList $rfc_type.summary.frame_size.frame_size_value $frameSizevalueList
                    keylset trafficStatsKeyedList $rfc_type.summary.frame_size.$frameSize.load.$loadValue.$stcName $value
                }
            }
        }
    }
    return $trafficStatsKeyedList
}


proc ::sth::Rfctest::configTrafficDescriptor {cmd descriptorHandle mode} {
    set optionValueList [getStcOptionValueList $cmd configTrafficDescriptor $mode]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $descriptorHandle $optionValueList
    }
    
    if {[info exists ::sth::Rfctest::userArgsArray(ipv6_addr)] || [info exists ::sth::Rfctest::userArgsArray(ipv6_gateway)]} {
        ::sth::sthCore::invoke stc::config $descriptorHandle "-EnableIpv4 false -EnableIpv6 true"
    }
        
    if {[info exists ::sth::Rfctest::userArgsArray(vlan)]} {
        ::sth::sthCore::invoke stc::config $descriptorHandle "-EnableVlan true"
    }
    
}

proc ::sth::Rfctest::configRfc2544Profile {Rfc2544ProfileRate mode} {
    set optionValueList [getStcOptionValueList rfc2544_asymmetric_profile configRfc2544Profile $mode]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $Rfc2544ProfileRate $optionValueList
    }
     
}



proc ::sth::Rfctest::configAccessConcentratorGeneratorParam {AccessConcentratorHandle mode} {
    set optionValueList [getStcOptionValueList rfc2544_asymmetric_config configAccessConcentratorGeneratorParam $mode]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $AccessConcentratorHandle $optionValueList
    }
     
}

proc ::sth::Rfctest::configRfc3918Test {testConfigHnd mode} {
    set optionValueList [getStcOptionValueList test_rfc3918_config configRfc3918Test $mode]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $testConfigHnd $optionValueList
    }
    
}
#This proc creates test configuration handle
proc ::sth::Rfctest::configrfc2544_asymmetric_config {mode testType AccessConcentratorHandle} {
    
    set optionValueList [getStcOptionValueList rfc2544_asymmetric_config configrfc2544_asymmetric_config $mode]
    
    if {$mode == "create"} {
    switch -- $testType {
        fl {
           set testObject "Rfc2544FrameLossConfig"
        }
        latency {
           set testObject "Rfc2544LatencyConfig"
        }
        throughput {
           set testObject "Rfc2544ThroughputConfig"
        }
    }
    
    
    
    set testConfigHandle [::sth::sthCore::invoke stc::create $testObject -under $AccessConcentratorHandle]
    ::sth::sthCore::invoke stc::config $testConfigHandle -EnableExposedInternalCommands true
    

    }
    if {$mode == "modify"} {
        set testConfigHandle $::sth::Rfctest::userArgsArray(handle)
    }
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $testConfigHandle $optionValueList
    }
    
    return $testConfigHandle
    #::sth::sthCore::invoke stc::config $testConfigHandle -EnableExposedInternalCommands true
}

#This proc creates test configuration profile
proc ::sth::Rfctest::configAsymmetricProfile {mode testType profileType testConfigHandle} {
     
     set optionValueList [getStcOptionValueList rfc2544_asymmetric_config configAsymmetricProfile $mode]
     if {$mode == "create"} {
     switch  $testType {
        fl {
           set testProfile "Rfc2544FrameLossProfile"
        }
        latency {
            set testProfile "Rfc2544LatencyProfile"
        }
        throughput {
            set testProfile "Rfc2544ThroughputProfile"
        }
        
     }
     if {[info exists ::sth::Rfctest::userArgsArray(profile_config_mode)] && ($::sth::Rfctest::userArgsArray(profile_config_mode) eq "per_side")} {
         if {$profileType eq "down_stream" } {
         set dwnstrmport $::sth::Rfctest::userArgsArray(downstream_port)
         set chkstrmblk [::sth::sthCore::invoke stc::get $dwnstrmport -children-streamblock]
         if {$chkstrmblk ne ""} {
            foreach stream $chkstrmblk {
           set downstreamProfileHandle [::sth::sthCore::invoke stc::create $testProfile -under $testConfigHandle]
           return $downstreamProfileHandle
            }
           }
           }
        if {$profileType eq "up_stream" } {   
        set upstrmport $::sth::Rfctest::userArgsArray(upstream_port)
        set chkstrmblk2 [::sth::sthCore::invoke stc::get $upstrmport -children-streamblock]
        if {$chkstrmblk2 ne ""} {
           set upstreamProfileHandle [::sth::sthCore::invoke stc::create $testProfile -under $testConfigHandle]
           return $upstreamProfileHandle
           }
           }
           
     }
     if {[info exists ::sth::Rfctest::userArgsArray(profile_config_mode)] && ($::sth::Rfctest::userArgsArray(profile_config_mode) eq "per_port")} {
        if {$profileType eq "per_port" } {
        set portlist [::sth::sthCore::invoke stc::get project1 -children-port]
        foreach port $portlist {
            set strmBlk [::sth::sthCore::invoke stc::get $port -children-streamblock]
            if {$strmBlk ne ""} {
            set PortProfHandle [::sth::sthCore::invoke stc::create $testProfile -under $testConfigHandle]
            configProfileHndl $PortProfHandle create
            return $PortProfHandle
            }
            
            
        }
        
        
      }  
     }
    }
    
}

proc ::sth::Rfctest::configProfileHndl {ProfileHandle mode} {
    set optionValueList [getStcOptionValueList rfc2544_asymmetric_config configAsymmetricProfile $mode]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ProfileHandle $optionValueList
    }
    }

proc ::sth::Rfctest::configProfileHandl {ProfileHandle mode} {
    set optionValueList [getStcOptionValueList rfc2544_asymmetric_profile configAsymmetricProfile $mode]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ProfileHandle $optionValueList
    }
    return $ProfileHandle
    }

proc ::sth::Rfctest::configRfc2544Test {mode testType} {
    
    set optionValueList [getStcOptionValueList test_rfc2544_config configRfc2544Test $mode]
    
    if {$mode == "create"} {
    switch -- $testType {
        b2b {
           set testObject "Rfc2544BackToBackFramesConfig"
        }
        fl {
           set testObject "Rfc2544FrameLossConfig"
        }
        latency {
           set testObject "Rfc2544LatencyConfig"
        }
        throughput {
           set testObject "Rfc2544ThroughputConfig"
        }
    }
    

    set testConfigHandle [::sth::sthCore::invoke stc::create $testObject -under $::sth::GBLHNDMAP(project)]
    
    set objects [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children]
    
    }
    if {$mode == "modify"} {
        set testConfigHandle $::sth::Rfctest::userArgsArray(handle)
    }
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $testConfigHandle $optionValueList
    }
    
    return $testConfigHandle
}


proc ::sth::Rfctest::configRfc5180 {mode testConfigHandle} {
    set rfc5180Handle [::sth::sthCore::invoke stc::get $testConfigHandle -children-rfc5180config]
    if {([info exists ::sth::Rfctest::userArgsArray(rfc5180_enable)] && $::sth::Rfctest::userArgsArray(rfc5180_enable)) || ($mode == "modify" && $rfc5180Handle != "")} {
    #need to create and config the rfc5180
    ::sth::sthCore::invoke stc::config $testConfigHandle -UseExistingStreamBlocks true -EnableExposedInternalCommands true
    if {$rfc5180Handle == ""} {
        set rfc5180Handle [::sth::sthCore::invoke stc::create rfc5180config -under $testConfigHandle]
    }
    set rfc5180OptionValueList [getStcOptionValueList test_rfc2544_config configRfc5180 $mode]
    if {[llength $rfc5180OptionValueList]} {
        ::sth::sthCore::invoke stc::config $rfc5180Handle $rfc5180OptionValueList
        if {[info exist ::sth::Rfctest::userArgsArray(custom_extension_header_list)]} {
        array set customExtensionHeaderArray {HOP_BY_HOP "Hop by Hop" DESTINATION_OPTIONS "Destination Options" ROUTING Routing AUTHENTICATION Authentication FRAGMENT Fragment ESP Encapsulation}
        set customExtensionHeaderList $::sth::Rfctest::userArgsArray(custom_extension_header_list)
        set customExtensionHeaderString ""
        foreach customExtensionHeader $customExtensionHeaderList {
            if {$customExtensionHeaderString != ""} {
            append customExtensionHeaderString ","
            }
            append customExtensionHeaderString [set customExtensionHeaderArray($customExtensionHeader)]
        }
        ::sth::sthCore::invoke stc::config $rfc5180Handle -CustomIpv6ExtensionHeaderString $customExtensionHeaderString
        }

    }
    if {[info exists ::sth::Rfctest::userArgsArray(coexistence_streamblock_handle)]} {
        set coexistence_streamblock_handle $::sth::Rfctest::userArgsArray(coexistence_streamblock_handle)
        set trafficDescriptorGroup [::sth::sthCore::invoke stc::get $testConfigHandle -TrafficDescriptorGroupBinding-targets]
        set trafficDescriptor [::sth::sthCore::invoke stc::create TrafficDescriptor -under $trafficDescriptorGroup]
        ::sth::sthCore::invoke stc::config $trafficDescriptor "-StreamBlockBinding-targets {$coexistence_streamblock_handle}"
        configTrafficDescriptor test_rfc2544_config $trafficDescriptor create
        ::sth::sthCore::invoke stc::config $trafficDescriptor "-EnableIpv4 true -EnableIpv6 false"
    }
    }
}
proc ::sth::Rfctest::configRfc3918TestCase {mode testType testConfig} {
    
    set optionValueList [getStcOptionValueList test_rfc3918_config configRfc3918TestCase $mode]
    
    if {$mode == "create"} {
    switch -- $testType {
        mixed_tput {
           set testObject "Rfc3918MixedClassThroughputTestCaseConfig"
           set name "RFC 3918: Mixed Class Throughput Test"
        }
        agg_tput {
           set testObject "Rfc3918AggregatedMulticastThroughputTestCaseConfig"
           set name "RFC 3918: Aggregated Multicast Throughput Test"
        }
        matrix {
           set testObject "Rfc3918ScaledGroupForwardingTestCaseConfig"
           set name "RFC 3918: Scaled Group Forwarding Test"
        }
        fwd_latency {
           set testObject "Rfc3918MulticastForwardingLatencyTestCaseConfig"
           set name "RFC 3918: Multicast Forwarding Latency Test"
        }
        join_latency {
           set testObject "Rfc3918JoinLeaveLatencyTestCaseConfig"
           set name "RFC 3918: Join/Leave Latency Test"
        }
        capacity {
           set testObject "Rfc3918MulticastGroupCapacityTestCaseConfig"
           set name "RFC 3918: Multicast Group Capacity Test"
        }
    }
    
    set testCaseHandle [::sth::sthCore::invoke stc::create $testObject -under $testConfig]
    
    ::sth::sthCore::invoke stc::config $testCaseHandle -Name "$name"
    
    }
    if {$mode == "modify"} {
        set testCaseHandle $::sth::Rfctest::userArgsArray(handle)
    }
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $testCaseHandle  $optionValueList
    }
    
    return $testCaseHandle
}

proc ::sth::Rfctest::test_rfc3918_config_create { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc3918_config_create $rklName"
    
    upvar 1 $rklName returnKeyedList
    variable ipv4Version
    variable ipv6Version
       
        set testConfig [::sth::sthCore::invoke stc::create Rfc3918Config -under $::sth::GBLHNDMAP(project)]
         
        configRfc3918Test $testConfig create
        
        if {![info exists ::sth::Rfctest::userArgsArray(test_type)]} {
            return -code error "\"test_type\" is a mandatory option"
        } else {
            set testType $::sth::Rfctest::userArgsArray(test_type)
        } 
        
        set testCaseHandle [configRfc3918TestCase create $testType $testConfig]
        
        if {![info exists ::sth::Rfctest::userArgsArray(multicast_streamblock)]} {
            return -code error "\"multicast_streamblock\" is a mandatory option"
        } else {
            ::sth::sthCore::invoke stc::config $testConfig -MulticastStreamBlockBinding-targets $::sth::Rfctest::userArgsArray(multicast_streamblock)
        }
        
        if {$testType == "mixed_tput"} {
            if {![info exists ::sth::Rfctest::userArgsArray(unicast_streamblock)]} {
                return -code error "option \"unicast_streamblock\" is mandatory when the test type is mixed_tput"
            } else {
                ::sth::sthCore::invoke stc::config $testCaseHandle -UnicastStreamBlockBinding-targets $::sth::Rfctest::userArgsArray(unicast_streamblock)
            }
        }
        
        set returnHnd $testCaseHandle
        
        set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
        
        ::sth::sthCore::invoke stc::perform ExpandBenchmarkConfig -Config $testConfig
            
      #apply config
       if {[catch {::sth::sthCore::doStcApply} applyError]} {
        return -code error $applyError
     }
 
  keylset returnKeyedList status $::sth::sthCore::SUCCESS
  keylset returnKeyedList handle $returnHnd
#    
    return $returnKeyedList
}

proc ::sth::Rfctest::test_rfc3918_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc2544_config_modify $rklName"
    
    upvar 1 $rklName returnKeyedList
        
        set testCaseHnd $::sth::Rfctest::userArgsArray(handle)
        
        set testConfig [::sth::sthCore::invoke stc::get $testCaseHnd -parent]
        
        configRfc3918Test $testConfig modify
        
        set testCaseHnd  [configRfc3918TestCase modify "" $testConfig]
        
        if {[info exists ::sth::Rfctest::userArgsArray(multicast_streamblock)]} {
            ::sth::sthCore::invoke stc::config $testConfig -MulticastStreamBlockBinding-targets $::sth::Rfctest::userArgsArray(multicast_streamblock)
        }
        
        if {[info exists ::sth::Rfctest::userArgsArray(unicast_streamblock)]} {
          
            ::sth::sthCore::invoke stc::config $testCaseHnd -UnicastStreamBlockBinding-targets $::sth::Rfctest::userArgsArray(unicast_streamblock)
            
        }
        
        ::sth::sthCore::invoke stc::perform ExpandBenchmarkConfig -Config $testConfig
    
      #apply config
     if {[catch {::sth::sthCore::doStcApply} applyError]} {
        return -code error $applyError
     }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

proc ::sth::Rfctest::test_rfc3918_config_delete { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc3918_config_delete $rklName"
    global loopList
    upvar 1 $rklName returnKeyedList
    set seqHandle [::sth::sthCore::invoke  "stc::get system1 -children-Sequencer"]
    set objectList [::sth::sthCore::invoke stc::get $seqHandle -children]
    foreach object $objectList {
        if {[regexp -nocase {^rfc3918sequencergroupcommand[0-9]+} $object]} {
        ::sth::sthCore::invoke stc::delete $object }
    }
    ::sth::sthCore::invoke stc::config $seqHandle "-CommandList {}"
    set loopList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList    
}

proc ::sth::Rfctest::test_rfc3918_control { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc3918_control $rklName"
    upvar 1 $rklName returnKeyedList
    global loopList
    #Get sequencer handle before config
    set seqHandle [::sth::sthCore::invoke  "stc::get system1 -children-Sequencer"]
     
    switch -- $::sth::Rfctest::userArgsArray(action) {
        run {
            ::sth::sthCore::invoke stc::perform sequencerStart
            set seqGrpCmdList [::sth::sthCore::invoke stc::get $seqHandle -children]
        
            after 2000
           
            set x [::sth::sthCore::invoke stc::get $seqHandle] 
            getLoopCmd $seqHandle

            #printobjects $seqHandle
            if {$::sth::Rfctest::userArgsArray(wait)} {
                set tempStep ""
                foreach seqGrpCmd $seqGrpCmdList {
                    if {[regexp -nocase sequencergroupcommand $seqGrpCmd]} {
                        for {set i 0} {$i<10000} {incr i} {
                        #process the error/fail branch
                            ::sth::Rfctest::checkSeqState $seqHandle
                            set currentStep ""
                            set state [::sth::sthCore::invoke stc::get $seqGrpCmd -state]
                            if {$state != "RUNNING"} {
                                puts "the exit state is $state"
                                break
                            }
                            foreach cmd $loopList {
                                set stepName [::sth::sthCore::invoke stc::get $cmd -ProgressCurrentStepName]
                                #puts "the step is $stepName\n"
                                if {$stepName != "" } { 
                                    lappend currentStep $stepName
                                }
                            }
                            if {$currentStep != $tempStep} {
                                puts "test is running, $currentStep\n"
                                set tempStep $currentStep
                            }
                        
                            after 2000
                        }
                    }
                }
               #delete previous rfc3918 test instance
               ::sth::Rfctest::cleanUpRfc3918 $seqHandle
            }
        }
        
   


        stop {
            ::sth::sthCore::invoke stc::perform sequencerStop
            #delete previous rfc3918 test instance            
            ::sth::Rfctest::cleanUpRfc3918 $seqHandle
        }
    }
     
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
  
    return $returnKeyedList
}

proc ::sth::Rfctest::test_rfc3918_info { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Rfctest::test_rfc3918_info $rklName"
    upvar 1 $rklName trafficStatsKeyedList
    global curDir
    global resultDir
    
    set trafficStatsKeyedList ""
   
    switch -- $::sth::Rfctest::userArgsArray(test_type) {
        mixed_tput {
            set testType "RFC3918-MixedClassTput"
            
            set dbFile [getDatabaseList $testType]
    
            sqlite3 db $dbFile
    
            set cmdReturn1 [db eval "SELECT DISTINCT TrialNum FROM  Rfc3918MixedClassThroughputPerIterationResult"]
            #set query "select trialnum,MulticastUnicastRatio,MulticastGroupCount,UnicastAvgFrameSize, MulticastAvgFrameSize,UnicastIntendedLoad,UnicastOfferedLoad,MixedClassIntendedLoad,MixedClassOfferedLoad,MulticastIntendedLoad, \
            #           MulticastOfferedLoad  from Rfc3918MixedClassThroughputPerIterationResult \
            #           where DroppedFrameCount = '0' GROUP BY MulticastGroupCount, MulticastAvgFrameSize "
            set query "select MulticastUnicastRatio,MulticastAvgFrameSize,UnicastAvgFrameSize,MixedClassIntendedLoad,MixedClassOfferedLoad,MulticastIntendedLoad, \
                       MulticastOfferedLoad,UnicastIntendedLoad,UnicastOfferedLoad from Rfc3918MixedClassThroughputPerIterationResult \
                       where DroppedFrameCount = '0' GROUP BY MulticastUnicastRatio,MulticastAvgFrameSize,UnicastAvgFrameSize"
            set cmdReturn2 [db eval $query]
   
            set testNum [llength $cmdReturn1]
            keylset trafficStatsKeyedList rfc3918mixed_tput.summary.total_iteration_count $testNum
            set rows [expr [llength $cmdReturn2] / 9]
            set detailList [list mixed_iload mixed_tput mc_iload mc_tput unicast_iload unicast_tput]
            set frameSizeList {}
            for {set i 1} {$i <= $rows} {incr i} {
                set index [expr ($i-1)*9]
                set Ratio [lindex $cmdReturn2 $index]
                incr index
                set mcFrameSize [lindex $cmdReturn2 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                incr index
                set uniFrameSize [lindex $cmdReturn2 $index]
                regsub -all {\.0} $uniFrameSize "" uniFrameSize
                regsub -all {\.+} $uniFrameSize "_" uniFrameSize
                
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn2 $index]
                        keylset trafficStatsKeyedList rfc3918mixed_tput.summary.mc_ratio.$Ratio.mc_frame_size.mc_frame_size_value $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918mixed_tput.summary.mc_ratio.$Ratio.mc_frame_size.$mcFrameSize.unicast_frame_size.unicast_frame_size_value $uniFrameSize
                        keylset trafficStatsKeyedList rfc3918mixed_tput.summary.mc_ratio.$Ratio.mc_frame_size.$mcFrameSize.unicast_frame_size.$uniFrameSize.$stcName $value
                }
            }
            set query "select DurationMode,Duration from Rfc3918Config"
            set results [db eval $query]
            set index 0
            keylset trafficStatsKeyedList rfc3918mixed_tput.summary.test_duration_mode [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918mixed_tput.summary.test_duration [lindex $results $index]
            
            set query "select TrialNum,MulticastGroupCount,MulticastUnicastRatio,MulticastAvgFrameSize,UnicastAvgFrameSize,MulticastEgressPortCount,MixedClassIntendedLoad,MixedClassOfferedLoad,MulticastIntendedLoad, \
                       MulticastOfferedLoad,UnicastIntendedLoad,UnicastOfferedLoad,TxFrameCount,RxFrameCount,MinLatency, AvgLatency,MaxLatency,\
                       MinJitter,AvgJitter,MaxJitter,DroppedFrameCount,DroppedFramePct from Rfc3918MixedClassThroughputPerIterationResult \
                       where DroppedFrameCount = '0' GROUP BY TrialNum,MulticastGroupCount,MulticastUnicastRatio,MulticastAvgFrameSize,UnicastAvgFrameSize"
            set cmdReturn3 [db eval $query]
            set rows [expr [llength $cmdReturn3] / 22]
            set detailList [list mc_egress_port mixed_iload mixed_tput mc_iload mc_tput unicast_iload unicast_tput tx_frames rx_frames latency_min latency_avg latency_max jitter_min jitter_avg jitter_max frame_lost frame_loss]
            for {set i 1} {$i <= $rows} {incr i} {
                set index [expr ($i-1)*22]
                set iCount [lindex $cmdReturn3 $index]
                incr index
                set gpCount [lindex $cmdReturn3 $index]
                incr index
                set Ratio [lindex $cmdReturn3 $index]
                incr index
                set mcFrameSize [lindex $cmdReturn3 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                incr index
                set uniFrameSize [lindex $cmdReturn3 $index]
                regsub -all {\.0} $uniFrameSize "" uniFrameSize
                
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn3 $index]
                        keylset trafficStatsKeyedList rfc3918mixed_tput.detail.iteration.$iCount.gp_count.$gpCount.mc_ratio.$Ratio.mc_frame_size.mc_frame_size_value $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918mixed_tput.detail.iteration.$iCount.gp_count.$gpCount.mc_ratio.$Ratio.mc_frame_size.$mcFrameSize.unicast_frame_size.$uniFrameSize.$stcName $value
                }
            }
            
            
        }
        agg_tput {
            set testType "RFC3918-AggregatedMulticastTput"
            set dbFile [getDatabaseList $testType]
    
            sqlite3 db $dbFile
    
            set cmdReturn1 [db eval "SELECT DISTINCT TrialNum FROM  Rfc3918AggregatedMulticastThroughputPerIterationResult"]
            set query "select MulticastGroupCount,MulticastAvgFrameSize,MulticastIntendedLoad,\
                       MulticastOfferedLoad,DroppedFramePct from Rfc3918AggregatedMulticastThroughputPerIterationResult \
                       where DroppedFrameCount = '0' GROUP BY MulticastGroupCount,MulticastAvgFrameSize,MulticastIntendedLoad"
            
            set testNum [llength $cmdReturn1]
            keylset trafficStatsKeyedList rfc3918agg_tput.summary.total_iteration_count $testNum
            set cmdReturn2 [db eval $query]
            if {$cmdReturn2 != ""} {
                set rows [expr [llength $cmdReturn2] / 5]
                #set detailList [list mixed_iload mixed_tput mc_iload mc_tput unicast_iload unicast_tput]
                for {set i 1} {$i <= $rows} {incr i} {
                    set index [expr ($i-1)*5]
                    set gpCount [lindex $cmdReturn2 $index]
                    incr index
                    set mcFrameSize [lindex $cmdReturn2 $index]
                    regsub -all {\.0} $mcFrameSize "" mcFrameSize
                    regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                    incr index
                    set iload [lindex $cmdReturn2 $index]
                    regsub -all {\.0} $iload "" iload
                    incr index
                    set oload [lindex $cmdReturn2 $index]
                    regsub -all {\.0} $oload "" oload
                    incr index
                    set dropPct [lindex $cmdReturn2 $index]
                    keylset trafficStatsKeyedList rfc3918agg_tput.summary.gp_count.$gpCount.frame_size.frame_size_value $mcFrameSize
                    keylset trafficStatsKeyedList rfc3918agg_tput.summary.gp_count.$gpCount.frame_size.$mcFrameSize.iload.$iload.tput $oload
                    keylset trafficStatsKeyedList rfc3918agg_tput.summary.gp_count.$gpCount.frame_size.$mcFrameSize.iload.$iload.frame_loss $dropPct
                }
            
            }
            set query "select DurationMode,Duration from Rfc3918Config"
            set results [db eval $query]
            set index 0
            keylset trafficStatsKeyedList rfc3918agg_tput.summary.test_duration_mode [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918agg_tput.summary.test_duration [lindex $results $index]
            
            set query "select TrialNum,MulticastGroupCount,MulticastAvgFrameSize,MulticastIntendedLoad, \
                        MulticastEgressPortCount,MulticastOfferedLoad,TxFrameCount,RxFrameCount,MinLatency, AvgLatency,MaxLatency,\
                       MinJitter,AvgJitter,MaxJitter,DroppedFrameCount,DroppedFramePct from Rfc3918AggregatedMulticastThroughputPerIterationResult"
            set cmdReturn3 [db eval $query]
            set rows [expr [llength $cmdReturn3] / 16]
            set detailList [list mc_egress_ports tput tx_frames rx_frames latency_min latency_avg latency_max jitter_min jitter_avg jitter_max frame_lost frame_loss]
            for {set i 1} {$i <= $rows} {incr i} {
                set index [expr ($i-1)*16]
                set iCount [lindex $cmdReturn3 $index]
                incr index
                set gpCount [lindex $cmdReturn3 $index]
                incr index
                set mcFrameSize [lindex $cmdReturn3 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                incr index
                set iload [lindex $cmdReturn3 $index]
                regsub -all {\.0} $iload "" iload
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn3 $index]
                        keylset trafficStatsKeyedList rfc3918agg_tput.detail.iteration.$iCount.gp_count.$gpCount.frame_size.frame_size_value $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918agg_tput.detail.iteration.$iCount.gp_count.$gpCount.frame_size.$mcFrameSize.iload.$iload.$stcName $value
                }
            }
            
        }
        matrix {
            set testType "RFC3918-ScaledGroupFwd"
            set dbFile [getDatabaseList $testType]
    
            sqlite3 db $dbFile

            set cmdReturn1 [db eval "SELECT Distinct TrialNum FROM Rfc3918ScaledGroupForwardingPerIterationResult"]
            set query "select trialnum,MulticastGroupCount,MulticastAvgFrameSize,MulticastIntendedLoad,MulticastRxGroupCount,MulticastOfferedLoad,TxFrameCount, \
                       ExpectedRxFrameCount,RxFrameCount,DroppedFrameCount,DroppedFramePct,ForwardingRate,MinLatency,AvgLatency,MaxLatency,MinJitter,AvgJitter,MaxJitter \
                       FROM  Rfc3918ScaledGroupForwardingPerIterationResult"
            set cmdReturn2 [db eval $query]
   
            set testNum [llength $cmdReturn1]
            keylset trafficStatsKeyedList rfc3918matrix.summary.total_iteration_count $testNum
            set count [expr [llength $cmdReturn2] /18]
            set detailList [list rx_gp_count oload tx_frames expected_rx_frames rx_frames frame_lost frame_loss fwd_rate latency_min latency_avg latency_max jitter_min jitter_avg jitter_max]
            set frameSizeList {}
            set loadValueList {}
            set gpCountList {}
            for {set i 1} {$i <= $count} {incr i} {
                set index [expr ($i-1)*18]
                set iCount [lindex $cmdReturn2 $index]
                incr index
                set gpCount [lindex $cmdReturn2 $index]
                set gpCountList [AddtoList $gpCount $gpCountList]
                incr index
                set mcFrameSize [lindex $cmdReturn2 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                
                set frameSizeList [AddtoList $mcFrameSize $frameSizeList]
                incr index
                set iload [lindex $cmdReturn2 $index]
                regsub -all {\.0+} $iload "" iload
                set loadValueList [AddtoList $iload $loadValueList]
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn2 $index]
                        keylset trafficStatsKeyedList rfc3918matrix.detail.iteration.$iCount.gp_count.$gpCount.frame_size.frame_size_value $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918matrix.detail.iteration.$iCount.gp_count.$gpCount.frame_size.$mcFrameSize.iload.$iload.$stcName $value
                }
            }
            
        foreach gpCount $gpCountList {   
            foreach frameSize $frameSizeList {
                foreach iload $loadValueList {
                    set txFrames 0
                    set rxFrames 0
                    set dropFrames 0
                    set rate 0
                    for {set i 1} {$i <= $iCount} {incr i} {
                        set txFrames [expr $txFrames + [keylget trafficStatsKeyedList rfc3918matrix.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.tx_frames]]
                        set rxFrames [expr $rxFrames + [keylget trafficStatsKeyedList rfc3918matrix.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.rx_frames]]
                        set dropFrames [expr $dropFrames + [keylget trafficStatsKeyedList rfc3918matrix.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.frame_lost]]
                        set rate [expr $rate + [keylget trafficStatsKeyedList rfc3918matrix.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.fwd_rate]]
                    }
                    set rate [expr $rate /$iCount]
                    keylset trafficStatsKeyedList rfc3918matrix.summary.gp_count.$gpCount.frame_size.frame_size_value $frameSize
                    keylset trafficStatsKeyedList rfc3918matrix.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.total_tx_frames $txFrames
                    keylset trafficStatsKeyedList rfc3918matrix.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.total_rx_frames $rxFrames
                    keylset trafficStatsKeyedList rfc3918matrix.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.total_frame_lost $dropFrames
                    keylset trafficStatsKeyedList rfc3918matrix.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.fwd_rate $rate
                    
                }
            }
        }
        
            
            set query "select DurationMode,Duration,LatencyType from Rfc3918Config"
            set results [db eval $query]
            set index 0
            keylset trafficStatsKeyedList rfc3918matrix.summary.test_duration_mode [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918matrix.summary.test_duration [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918matrix.summary.latency_type [lindex $results $index]
        }
        fwd_latency {
            set testType "RFC3918-MulticastFwdLatency"
            set dbFile [getDatabaseList $testType]
    
            sqlite3 db $dbFile
    
            set cmdReturn1 [db eval "SELECT Distinct TrialNum FROM Rfc3918MulticastForwardingLatencyPerIterationResult"]
            set query "select trialnum,MulticastGroupCount,MulticastAvgFrameSize,MulticastIntendedLoad,MulticastEgressPortCount,MulticastRxGroupCount,MulticastOfferedLoad,MinLatency,AvgLatency,MaxLatency,TxFrameCount, \
                       ExpectedRxFrameCount,RxFrameCount FROM Rfc3918MulticastForwardingLatencyPerIterationResult"
            set cmdReturn2 [db eval $query]
   
            set testNum [llength $cmdReturn1]
            keylset trafficStatsKeyedList rfc3918fwd_latency.summary.total_iteration_count $testNum
            set count [expr [llength $cmdReturn2] / 13]
            set detailList [list mc_egress_port rx_gp_count oload latency_min latency_avg latency_max tx_frames expected_rx_frames rx_frames]
            set frameSizeList {}
            set loadValueList {}
            set gpCountList {}
            for {set i 1} {$i <= $count} {incr i} {
                set index [expr ($i-1)*13]
                set iCount [lindex $cmdReturn2 $index]
                incr index
                set gpCount [lindex $cmdReturn2 $index]
                set gpCountList [AddtoList $gpCount $gpCountList]
                incr index
                set mcFrameSize [lindex $cmdReturn2 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                set frameSizeList [AddtoList $mcFrameSize $frameSizeList]
                incr index
                set iload [lindex $cmdReturn2 $index]
                regsub -all {\.0+} $iload "" iload
                set loadValueList [AddtoList $iload $loadValueList]
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn2 $index]
                        keylset trafficStatsKeyedList rfc3918fwd_latency.detail.iteration.$iCount.gp_count.$gpCount.frame_size.frame_size_value $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918fwd_latency.detail.iteration.$iCount.gp_count.$gpCount.frame_size.$mcFrameSize.iload.$iload.$stcName $value
                }
            }
            
        foreach gpCount $gpCountList {   
            foreach frameSize $frameSizeList {
                foreach iload $loadValueList {
                    set minLatency 1000000
                    set maxLatency 0
                    set avgLatency 0
                    set oload 0
                    for {set i 1} {$i <= $iCount} {incr i} {
                        set minValue [keylget trafficStatsKeyedList rfc3918fwd_latency.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.latency_min]
                        if {$minValue < $minLatency} {
                           set minLatency $minValue
                        }
                        set maxValue [keylget trafficStatsKeyedList rfc3918fwd_latency.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.latency_max]
                        if {$maxValue > $maxLatency} {
                           set maxLatency $maxValue
                        }
                        
                        set avgLatency [expr $avgLatency + [keylget trafficStatsKeyedList rfc3918fwd_latency.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.latency_avg]]
                        set oload [expr $oload + [keylget trafficStatsKeyedList rfc3918fwd_latency.detail.iteration.$i.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.oload]]
                    }
                    set avgLatency [expr $avgLatency /$iCount]
                    set oload [expr $oload /$iCount]
                    keylset trafficStatsKeyedList rfc3918fwd_latency.summary.gp_count.$gpCount.frame_size.frame_size_value $frameSize
                    keylset trafficStatsKeyedList rfc3918fwd_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.oload $oload
                    keylset trafficStatsKeyedList rfc3918fwd_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.latency_min $minLatency
                    keylset trafficStatsKeyedList rfc3918fwd_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.latency_max $maxLatency
                    keylset trafficStatsKeyedList rfc3918fwd_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.latency_avg $avgLatency
                    
                }
            }
        }
        
            
            set query "select DurationMode,Duration,LatencyType from Rfc3918Config"
            set results [db eval $query]
            set index 0
            keylset trafficStatsKeyedList rfc3918fwd_latency.summary.test_duration_mode [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918fwd_latency.summary.test_duration [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918fwd_latency.summary.latency_type [lindex $results $index]
        }
        join_latency {
            set testType "RFC3918-JoinLeaveLatency"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            
            set cmdReturn1 [db eval "SELECT Distinct TrialNum FROM Rfc3918JoinLeaveLatencyPerIterationResult"]
            set query "select trialnum,MulticastGroupCount,MulticastAvgFrameSize,MulticastIntendedLoad,MulticastEgressPortCount,MulticastRxGroupCount,MulticastOfferedLoad,\
                       MinJoinLatency,AvgJoinLatency,MaxJoinLatency,MinLeaveLatency,AvgLeaveLatency,MaxLeaveLatency,TxFrameCount, \
                       ExpectedRxFrameCount,RxFrameCount,DroppedFrameCount,DroppedFramePct FROM Rfc3918JoinLeaveLatencyPerIterationResult"
            set cmdReturn2 [db eval $query]
   
            set testNum [llength $cmdReturn1]
            keylset trafficStatsKeyedList rfc3918join_latency.summary.total_iteration_count $testNum
            set count [expr [llength $cmdReturn2] / 18]
            set detailList [list mc_egress_port rx_gp_count oload join_latency_min join_latency_avg join_latency_max leave_latency_min leave_latency_avg leave_latency_max tx_frames expected_rx_frames rx_frames frame_lost frame_loss]
            set frameSizeList {}
            set loadValueList {}
            set gpCountList {}
            for {set i 1} {$i <= $count} {incr i} {
                set index [expr ($i-1)*18]
                set iCount [lindex $cmdReturn2 $index]
                incr index
                set gpCount [lindex $cmdReturn2 $index]
                set gpCountList [AddtoList $gpCount $gpCountList]
                incr index
                set mcFrameSize [lindex $cmdReturn2 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                set frameSizeList [AddtoList $mcFrameSize $frameSizeList]
                incr index
                set iload [lindex $cmdReturn2 $index]
                regsub -all {\.0+} $iload "" iload
                set loadValueList [AddtoList $iload $loadValueList]
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn2 $index]
                        keylset trafficStatsKeyedList rfc3918join_latency.detail.iteration.$iCount.gp_count.$gpCount.mc_frame_size.mc_frame_size_value   $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918join_latency.detail.iteration.$iCount.gp_count.$gpCount.mc_frame_size.$mcFrameSize.iload.$iload.$stcName $value
                }
            }
            
            foreach gpCount $gpCountList {   
                foreach frameSize $frameSizeList {
                    foreach iload $loadValueList {
                        set minJoinLatency 1000000
                        set maxJoinLatency 0
                        set avgJoinLatency 0
                        set minLeaveLatency 1000000
                        set maxLeaveLatency 0
                        set avgLeaveLatency 0
                        set oload 0
                        for {set i 1} {$i <= $iCount} {incr i} {
                            set minJoinValue [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.join_latency_min]
                            if {$minJoinValue < $minJoinLatency} {
                               set minJoinLatency $minJoinValue
                            }
                            set maxJoinValue [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.join_latency_max]
                            if {$maxJoinValue > $maxJoinLatency} {
                               set maxJoinLatency $maxJoinValue
                            }
                set avgJoinLatency [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.join_latency_avg]
                            if {[llength $avgJoinLatency] == 0} {
                set avgJoinLatency 0
                }
                set minLeaveValue [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.leave_latency_min]
                            if {$minLeaveValue < $minLeaveLatency} {
                               set minLeaveLatency $minLeaveValue
                            }
                            set maxLeaveValue [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.leave_latency_max]
                            if {$maxLeaveValue > $maxLeaveLatency} {
                               set maxLeaveLatency $maxLeaveValue
                            }
                            set avgLeaveLatency [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.leave_latency_avg]
                if {[llength $avgLeaveLatency] == 0} {
                set avgLeaveLatency 0
                }
                            set oload [expr $oload + [keylget trafficStatsKeyedList rfc3918join_latency.detail.iteration.$i.gp_count.$gpCount.mc_frame_size.$frameSize.iload.$iload.oload]]
                        }
                        set avgJoinLatency [expr $avgJoinLatency /$iCount]
                        set avgLeaveLatency [expr $avgLeaveLatency /$iCount]
                        set oload [expr $oload /$iCount]
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.frame_size_value  $frameSize
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.oload $oload
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.join_latency_min $minJoinLatency
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.join_latency_max $maxJoinLatency
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.join_latency_avg $avgJoinLatency
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.join_latency_min $minJoinLatency
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.leave_latency_max $maxLeaveLatency
                        keylset trafficStatsKeyedList rfc3918join_latency.summary.gp_count.$gpCount.frame_size.$frameSize.iload.$iload.leave_latency_avg $avgLeaveLatency
                    }
                }
            }
            set query "select DurationMode,Duration,LatencyType from Rfc3918Config"
            set results [db eval $query]
            set index 0
            keylset trafficStatsKeyedList rfc3918join_latency.summary.test_duration_mode [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918join_latency.summary.test_duration [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918join_latency.summary.latency_type [lindex $results $index]
            
        }
        capacity {
            set testType "RFC3918-MulticastGroupCapacity"
            set dbFile [getDatabaseList $testType]
            sqlite3 db $dbFile
            set cmdReturn1 [db eval "SELECT Distinct TrialNum FROM Rfc3918MulticastGroupCapacityPerIterationResult"]
            set query "select MulticastAvgFrameSize,MulticastIntendedLoad,\
                       MulticastOfferedLoad, MAX(MulticastRxGroupCount) from Rfc3918MulticastGroupCapacityPerIterationResult \
                       where MulticastEgressPortNoFramesRxGroupCount = '0' GROUP BY MulticastAvgFrameSize,MulticastIntendedLoad"
            set cmdReturn2 [db eval $query]
            
             set testNum [llength $cmdReturn1]
            keylset trafficStatsKeyedList rfc3918capacity.summary.total_iteration_count $testNum
            
            set detailList [list oload group_capacity]
            if {$cmdReturn2 != ""} {
                set rows [expr [llength $cmdReturn2] / 4]
                for {set i 1} {$i <= $rows} {incr i} {
                    set index [expr ($i-1)*4]
                    set mcFrameSize [lindex $cmdReturn2 $index]
                    regsub -all {\.0} $mcFrameSize "" mcFrameSize
                    regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                    incr index
                    set iload [lindex $cmdReturn2 $index]
                    regsub -all {\.0} $iload "" iload
                    foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn2 $index]
                        keylset trafficStatsKeyedList rfc3918capacity.summary.frame_size.frame_size_value $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918capacity.summary.frame_size.$mcFrameSize.iload.$iload.$stcName $value
                    }
                }
            
            }
            set query "select DurationMode,Duration from Rfc3918Config"
            set results [db eval $query]
            set index 0
            keylset trafficStatsKeyedList rfc3918capacity.summary.test_duration_mode [lindex $results $index]
            incr index
            keylset trafficStatsKeyedList rfc3918capacity.summary.test_duration [lindex $results $index]
            
            set query "select TrialNum,MulticastAvgFrameSize,MulticastIntendedLoad,MulticastGroupCount,MulticastRxGroupCount, \
                        MulticastEgressPortCount,MulticastEgressPortNoFramesRxGroupCount,MulticastOfferedLoad,TxFrameCount,RxFrameCount,MinLatency, AvgLatency,MaxLatency,\
                       MinJitter,AvgJitter,MaxJitter,DroppedFrameCount,DroppedFramePct from Rfc3918MulticastGroupCapacityPerIterationResult"
            set cmdReturn3 [db eval $query]
            set rows [expr [llength $cmdReturn3] / 18]
            set detailList [list  mc_rx_gp_count mc_egress_ports no_rx_gp tput tx_frames rx_frames latency_min latency_avg latency_max jitter_min jitter_avg jitter_max frame_lost frame_loss]
            for {set i 1} {$i <= $rows} {incr i} {
                set index [expr ($i-1)*18]
                set iCount [lindex $cmdReturn3 $index]
                incr index
                set mcFrameSize [lindex $cmdReturn3 $index]
                regsub -all {\.0} $mcFrameSize "" mcFrameSize
                regsub -all {\.+} $mcFrameSize "_" mcFrameSize
                incr index
                set iload [lindex $cmdReturn3 $index]
                regsub -all {\.0} $iload "" iload
                incr index
                set gpCount [lindex $cmdReturn3 $index]
                foreach stcName $detailList {
                        incr index
                        set value [lindex $cmdReturn3 $index]
                        keylset trafficStatsKeyedList rfc3918capacity.detail.iteration.$iCount.frame_size.frame_size_value  $mcFrameSize
                        keylset trafficStatsKeyedList rfc3918capacity.detail.iteration.$iCount.frame_size.$mcFrameSize.iload.$iload.gp_count.$gpCount.$stcName $value
                }
            }
        }
    }
    
    set x [db close $dbFile]
    
    cd /
    cd $curDir
    cd "Results"
    set test [pwd]
    if {$::sth::Rfctest::userArgsArray(clear_result)} {
        file delete -force $resultDir
    }
    
    cd /
    cd $curDir
    
    keylset trafficStatsKeyedList status $::sth::sthCore::SUCCESS
   
    return $trafficStatsKeyedList
}

proc ::sth::Rfctest::getDatabaseList {testType {scriptName "Untitled"}} {
    global curDir
    global scriptNameFolder
    set curDir [pwd]

    if {$::sth::Session::xmlFlag} {
        regexp -- {(.*[\/|\\])*((.+)\.xml)$}  $::sth::Session::xmlFilename sub1 sub2 sub3 scriptName
    }

    # Get BLL version
    #set bllVer [stc::get system1 -version]
    set bllVer "3.00.2132"
    
    #puts "get the db file: $::sth::serverflag\n"
    if {$::sth::serverflag == 1} {
        puts "get the db";
        if {[catch {
           set db_name [::sth::sthCore::invoke stc::get project1.TestResultSetting -CurrentResultFileName]
            puts "DB name:$db_name; running_dir: $::sth::_RUNNING_DIR"
            puts "----------get the db from the lab server-----------------------\n"
            set ret [::sth::sthCore::invoke stc::perform CSSynchronizeFiles];
        } err]} {
            puts "get db err:$err"
        }
    }
    
    if {[string first "2." $bllVer] != -1}  {
    set scriptNameFolder ${scriptName}-????-??-??_??-??-??
    set testTypeFolder   ${testType}-????-??-??_??-??-??
        switch $testType {
          "RFC3918-MixedClassTput" {
            set dbSumFile "RFC3918-MixedClassTput-Summary*.db"
          }
          "RFC3918-AggregatedMulticastTput" {
            set dbSumFile "RFC3918-AggregatedMulticastTput-Summary*.db"
          }
          "RFC3918-MulticastFwdLatency" {
                set dbSumFile "RFC3918-MulticastFwdLatency-Summary*.db"
          }
          "RFC3918-ScaledGroupFwd" {
                set dbSumFile "RFC3918-ScaledGroupFwd-Summary*.db"
          }
         "RFC3918-JoinLeaveLatency" {
                set dbSumFile "RFC3918-JoinLeaveLatency-Summary*.db"
          }
          "RFC3918-MulticastGroupCapacity" {
                set dbSumFile "RFC3918-MulticastGroupCapacity-Summary*.db"
          }
          
          default {
            set dbSumFile ${testType}*-????-??-??_??-??-??.db  
          }
        }
    
    }

    if {[string first "3." $bllVer] != -1}  {
    set scriptNameFolder ${scriptName}_????-??-??_??-??-??
    set testTypeFolder   ${testType}_????-??-??_??-??-??
    switch $testType {
          "RFC3918-MixedClassTput" {
                set dbSumFile "RFC3918-MixedClassTput-Summary*.db"
          }
          "RFC3918-AggregatedMulticastTput" {
            set dbSumFile "RFC3918-AggregatedMulticastTput-Summary*.db"
          }
          "RFC3918-MulticastFwdLatency" {
                set dbSumFile "RFC3918-MulticastFwdLatency-Summary*.db"
          }
          "RFC3918-ScaledGroupFwd" {
                set dbSumFile "RFC3918-ScaledGroupFwd-Summary*.db"
          }
           "RFC3918-JoinLeaveLatency" {
                set dbSumFile "RFC3918-JoinLeaveLatency-Summary*.db"
          }
          "RFC3918-MulticastGroupCapacity" {
            set dbSumFile "RFC3918-MulticastGroupCapacity-Summary*.db"
          }
          default {
            set dbSumFile ${testType}*_????-??-??_??-??-??.db
          }
        }
    }
    

    if {$scriptName == "Untitled"} {
        lappend pathPat Results $scriptNameFolder $testTypeFolder
    } else {
    lappend pathPat Results $scriptNameFolder $testTypeFolder
    }

    foreach path $pathPat {
        if {[cdMatchedDir [list [list $path]] $scriptName]} {
            cd /
            cd $curDir
            puts "can't find the matched directory!"
        }
    }; # end foreach

    #To retreive the summary database filename. If not found - return error
    if {[catch {set fileList [glob $dbSumFile]} err]} {
        cd /
        cd $curDir
        return -code error "$err"
    }

    #If there are more than one summary files - return error
    if {[llength $fileList] != 1 } {
        cd /
        cd $curDir
        return -code error "The count of db file matched with $dbSumFile should be 1, but found [llength $fileList]"
    }

    #sqlite3 dbQuery [lindex $fileList 0]
    #if {[catch {set dbFileNameList [dbQuery eval "SELECT DISTINCT DBFileName FROM EotResultIterations"] } err]} {
    #    puts "There is no any Iteration db file"
    #} else {
    #    foreach dbFileName $dbFileNameList {
    #        lappend fileList $dbFileName
    #    }
    #}
    #dbQuery close

    return $fileList
}


proc ::sth::Rfctest::cdMatchedDir {namePat scriptName} {
    
    global resultDir
    catch {set fileList [glob -- $namePat]
        set index 0
    
        # If there are more than one matched directory, the latest created directory will be selected
        if {[llength $fileList] > 1} {
            set preTime [file mtime [lindex $fileList $index]]
    
            for {set i 1} { $i < [llength $fileList] } { incr i } {
                set time [file mtime [lindex $fileList $i]]
                if { $time >$preTime } {
                    set index $i
                    set preTime $time
                }
            }
        }
        set file [lindex $fileList $index]
        if {[regexp -- $scriptName $namePat]} {
            set resultDir $file
        }
        cd $file
    }
   return 0
}

proc ::sth::Rfctest::checkDependency {cmdType option dependentValue} {  
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::Ancp:: $cmdType $option dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists ::sth::Ancp::userArgsArray($dependency)]} {
            return -code error "\"-$option\" is dependent upon the existence of \"-$dependency\"."
        } elseif {![string match -nocase $dependentValue $::sth::Ancp::userArgsArray($dependency)]} {
            return -code error "\"-$option\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}

proc ::sth::Rfctest::getStcOptionValueList {cmdType modeFunc mode} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in the rfctestTable.tcl
    foreach item $::sth::Rfctest::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Rfctest:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Rfctest:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Rfctest:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Rfctest:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Rfctest:: $cmdType $opt stcattr]
                    if {$opt == "test_duration"} {
                        if {[info exists $::sth::Rfctest::userArgsArray(test_duration_mode)] && $::sth::Rfctest::userArgsArray(test_duration_mode) == "bursts"} {
                           set stcAttr "DurationBursts"
                        }
                    }
                  
                    if {$opt == "accept_frame_loss"} {
                        if {[info exists ::sth::Rfctest::userArgsArray(test_type)] && $::sth::Rfctest::userArgsArray(test_type) == "b2b"} {
                           set stcAttr "DurationAcceptableFrameLoss"
                        }
                        if {[info exists ::sth::Rfctest::userArgsArray(test_type)] && $::sth::Rfctest::userArgsArray(test_type) == "throughput"} {
                           set stcAttr "AcceptableFrameLoss"
                        }
                    }
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Rfctest:: $cmdType $opt $::sth::Rfctest::userArgsArray($opt)} value]} {
                if {$stcAttr == "LearningMode"} {
                           if {$value == "l2"} {
                             set value "L2_LEARNING"
                           }
                           if {$value == "l3"} {
                            set value "L3_LEARNING"
                           }
                           lappend optionValueList -$stcAttr $value
                        } else {
                            lappend optionValueList -$stcAttr $value
                        }
                } else {
                        if {$stcAttr == "LearningMode"} {
                           if {$::sth::Rfctest::userArgsArray($opt) == "l2"} {
                             set value "L2_LEARNING"
                           }
                           if {$::sth::Rfctest::userArgsArray($opt) == "l3"} {
                            set value "L3_LEARNING"
                           }
                           lappend optionValueList -$stcAttr $value
                        } else {
                    lappend optionValueList -$stcAttr $::sth::Rfctest::userArgsArray($opt)
                        }
                }
                } else {
                    #eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Rfctest::userArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}

proc ::sth::Rfctest::GetIpOrNetworkBlockHandle { emulation_handles } {
    set blockHandleList ""
    set networkBlockHandle 0
    set hostBlockHandle 0
    set useNativeBinding 0
    set blockHandle 0
    array set myTempHandleArray {}
    foreach emulation_handle $emulation_handles {
        if {[::info exists myTempHandleArray($emulation_handle)]} {
            continue
        } else {
            set myTempHandleArray($emulation_handle) 1
        }
        if {[regexp ripsessionhandle [string tolower $emulation_handle]]} {
            set emulationType ripsessionhandle 
        } else {
            set emulationType [::sth::Traffic::TrimTailNumber [string tolower $emulation_handle]]
            if { [string first "routerconfig" $emulationType] >= 0 } {
                set emulationType router
                set emulation_handle [::sth::sthCore::invoke ::stc::get $emulation_handle -parent]
            }
        }
        
        switch $emulationType {
            ipv4prefixlsp {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]
            }
            rsvpegresstunnelparams -
            rsvpingresstunnelparams {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv4NetworkBlock} Ipv4NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: \
                        Cannot get networkBlockHandle(Ipv4NetworkBlock) from $emulation_handle: $Ipv4NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv4NetworkBlock
            }
            bgpipv4routeconfig {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]
            }
            bgpipv6routeconfig {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv6NetworkBlock]
            }
            host -
            router {
                set hostBlockHandle [::sth::Traffic::GetFirstIpHeader $emulation_handle]
            }
            dhcpv4blockconfig {
                set hostBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -usesif-Targets]
            }
            IsisLspConfig {
                set networkBlockHandle [::sth::Traffic::GetFirstIpHeader $emulation_handle]
            }
            isisroutehandle {
                # for ISIS we would get this handle.
                if {[info exists ::sth::IsIs::ISISROUTEHNDLIST($emulation_handle)]} {
                    set retList $::sth::IsIs::ISISROUTEHNDLIST($emulation_handle);
                    set isisIpVersion [lindex $retList 1]
                    switch -- $isisIpVersion {
                        4 {
                            set isisRouteConfig [lindex $retList 2]
                            set networkBlockHandle [::sth::sthCore::invoke ::stc::get $isisRouteConfig -children-Ipv4NetworkBlock]
                        }
                        6 {
                            set isisRouteConfig [lindex $retList 3]
                            set networkBlockHandle [::sth::sthCore::invoke ::stc::get $isisRouteConfig -children-Ipv6NetworkBlock]
                        }
                        4_6 {
                            set errMsg "Error in traffic_config: Unable to support IPv4 and IPv6 network block handles at this time."
                            ::sth::sthCore::log error $errMsg
                            set networkBlockHandle 0
                            return -code error $errMsg
                        }
                    }
                } else {
                    set errMsg "Error in traffic_config: ISIS route Handle should have Type INTERNAL or EXTERNAL."
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
            }
            ipv4routeparams {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv4networkblock} networkBlockHandle]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get Ipv4NetworkBlock from $emulation_handle"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
            }
            ipv6routeparams {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv6networkblock} NetworkBlockHandle]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get Ipv4NetworkBlock from $emulation_handle: $NetworkBlockHandle"
                    ::sth::sthCore::log error $errMsg
                    set NetworkBlockHandle 0
                    return -code error $errMsg
                }
            }
            routerlsa {
                set hndLsaLink [::sth::sthCore::invoke ::stc::get $emulation_handle -children-RouterLsaLink]
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $hndLsaLink -children-Ipv4NetworkBlock]
            }
            summarylsablock -
            externallsablock -
            asbrsummarylsa {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]    
            }
            ospfv3intraareaprefixlsablk -
            ospfv3asexternallsablock -
            ospfv3nssalsablock -
            ospfv3linklsablk {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv6NetworkBlock]                
            }
            pimv4groupblk {
                if {[catch {::sth::sthCore::invoke ::stc::get  [::sth::sthCore::invoke ::stc::get $emulation_handle -JoinedGroup-targets] -children-ipv4NetworkBlock} Ipv4NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv4NetworkBlock) from $emulation_handle: $Ipv4NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv4NetworkBlock
            }
            pimv6groupblk {
                if {[catch {::sth::sthCore::invoke ::stc::get  [::sth::sthCore::invoke ::stc::get $emulation_handle -JoinedGroup-targets] -children-ipv6NetworkBlock} Ipv6NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv6NetworkBlock) from $emulation_handle: $Ipv6NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv6NetworkBlock                           
            }
            ripsessionhandle {
                set hostBlockHandle [::sth::Traffic::GetFirstIpHeader [set ::sth::rip::$emulation_handle]]
            }
            ripv4routeparams {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv4NetworkBlock]
            }
            ripngrouteparams {
                set networkBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -children-Ipv6NetworkBlock]
            }
            ipv4group {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv4NetworkBlock} Ipv4NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv4NetworkBlock) from $emulation_handle: $Ipv4NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv4NetworkBlock            
            }
            ipv6group {
                if {[catch {::sth::sthCore::invoke ::stc::get $emulation_handle -children-ipv6NetworkBlock} Ipv6NetworkBlock]} {
                    set errMsg "Error in ::sth::Traffic::processEmulationHandle: Cannot get networkBlockHandle(Ipv6NetworkBlock) from $emulation_handle: $Ipv6NetworkBlock"
                    ::sth::sthCore::log error $errMsg
                    set networkBlockHandle 0
                    return -code error $errMsg
                }
                set networkBlockHandle $Ipv6NetworkBlock
            }
            defaults {
                if {[string first "routerconfig" $emulationType] > 0} {
                    set hostBlockHandle [::sth::sthCore::invoke ::stc::get $emulation_handle -parent]
                } else {
                    set errMsg "INVALID EMULATION_HANDLE ($emulation_handle)"
                    ::sth::sthCore::log error $errMsg
                    return -code error $errMsg
                }
            }
        }
        
        #################### Bind Host Block or Network Block to StreamBlock #################
        if { $networkBlockHandle != 0 } {
            set startIPAddr [::sth::sthCore::invoke ::stc::get $networkBlockHandle -StartIpList]
            ::sth::sthCore::invoke ::stc::config $networkBlockHandle -StartIpList [::ip::normalize $startIPAddr]
            set blockHandle $networkBlockHandle
        } else {
            set blockHandle $hostBlockHandle
            set startIPAddr [::sth::sthCore::invoke ::stc::get $blockHandle -address]
            ::sth::sthCore::invoke ::stc::config $blockHandle -address [::ip::normalize $startIPAddr]
        }
        lappend blockHandleList $blockHandle
    }
    array unset myTempHandleArray
    return $blockHandleList 
}

proc ::sth::Rfctest::AddtoList {item itemList} {
        set flag 0
        foreach vlaue $itemList {
            if {$vlaue == $item} {
                set flag 1
                break
            }
        }
        if {!$flag} {
            lappend itemList $item
        }
        return $itemList
}

proc ::sth::Rfctest::printobjects {object} {
    set x ""
    set x [::sth::sthCore::invoke stc::get $object -children]
    if {$x != ""} {
       foreach obj $x {
          puts "the object is $obj, and the content is:"
          puts [::sth::sthCore::invoke stc::get $obj]
          printobjects $obj
       }
    }
}

proc ::sth::Rfctest::getLoopCmd {object} {
    global loopList 
    
    set x [::sth::sthCore::invoke stc::get $object -children]
    if {$x != ""} {
       foreach obj $x {
            if {[regexp -- "sequencerloopcommand" $obj]} {
                lappend loopList $obj
               }
       getLoopCmd $obj 
     }
}
}

proc ::sth::Rfctest::checkSeqState {seqHandle} {
    set seq_status [::sth::sthCore::invoke stc::get $seqHandle -TestState]
    set stopped_cmd ""
    set stopped_reason ""
    set stopcmdargs ""
    if {[regexp -nocase "FAILED" $seq_status]} {
        set stopped_cmd [::sth::sthCore::invoke stc::get $seqHandle -StoppedCommand]
        if {$stopped_cmd ne ""} {
            set stopcmdargs [::sth::sthCore::invoke stc::get $stopped_cmd]
            if {[regexp -nocase "StoppedReason" $stopcmdargs]} {
                set stopped_reason [::sth::sthCore::invoke stc::get $stopped_cmd -StoppedReason]
            } elseif {[regexp -nocase "Status" $stopcmdargs]} {
                set stopped_reason [::sth::sthCore::invoke stc::get $stopped_cmd -Status] 
            }
            
            set stopcmd_name [::sth::sthCore::invoke stc::get $stopped_cmd -name]
        }
        puts "<error>Sequencer status:FAILED. Stopped command:\"$stopcmd_name\", stopped reason:$stopped_reason"
    }
    
    return $seq_status
}

proc ::sth::Rfctest::configImix {testConfigHandle} {
    variable userArgsArray
    if {![info exists userArgsArray(frame_size_imix)]} {
    return
    }
    set imixStrList $userArgsArray(frame_size_imix)
    array set name2handle ""
    set frameLenDistList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-FrameLengthDistribution]
    foreach frameLenDist $frameLenDistList {
    set name [::sth::sthCore::invoke stc::get $frameLenDist -name]
    set name2handle($name) $frameLenDist
    }
    set imixNew ""
    foreach imix $imixStrList {
        # add "jmix_upstream and jmix_downstream" to support "JMIX Upstream and MIX Downstream"
        if {[regexp -nocase "jmix_upstream" $imix]} {
            set imix "JMIX Upstream"
        }
        if {[regexp -nocase "jmix_downstream" $imix] } {
            set imix "JMIX Downstream"
        }
        if {[info exists name2handle($imix)]} {
            set imixNew [concat $imixNew $name2handle($imix)]
        } else {
            return -code error "STC don't support the iMIX to be $imix"
        }
    }
    ::sth::sthCore::invoke stc::config $testConfigHandle -ImixDistributionList $imixNew
}

#add get rfc2544 results detail per framesize info 

proc ::sth::Rfctest::get_rfc2544_detail_per_framesize_info { testType rfc_type trialNumList detailList  frameSizeMode} {
    set frameSizePerIteration ""
    set trafficStatsKeyedList ""
    set queryLoadPerFrameSize ""
    set keyNum [llength $detailList]
    switch -- $testType {
        2544-BTBF {
            set loadeTable "Rfc2544Back2BackPerLoadResult"
            set frameSizeTable "Rfc2544Back2BackPerFrameSizeResult"
            set queryElem "framelengthdistribution,IntendedLoad,OfferedLoad,txsigframecount,rxsigframecount,FrameLoss,burstsize,durationinsec,minlatency,maxlatency,avglatency"
        }
        2544-Tput {
            set loadeTable "Rfc2544ThroughputPerLoadResult"
            set frameSizeTable "Rfc2544ThroughputPerFrameSizeResult"
            set queryElem "framelengthdistribution, IntendedLoad,OfferedLoad,ThroughputRate,ForwardingRate,MbpsLineRate,PercentLoss,MaxLatencyThresholdExceeded,OutOfSeqThresholdExceeded, MinLatency, AvgLatency, MaxLatency, MinJitter, AvgJitter, MaxJitter"
            }
    }
    foreach eachNum $trialNumList {
        set frameSizeList ""
        if {[regexp -nocase "imix" $frameSizeMode]} {
            set queryFrameSizePerIteration "select FrameSize FROM  $loadeTable where TrialNum = $eachNum"
        } else {
            set queryFrameSizePerIteration "select FrameSize FROM  $frameSizeTable where TrialNum = $eachNum"
        } 
        set frameSizePerIteration [db eval $queryFrameSizePerIteration]
        foreach eachFrameSize $frameSizePerIteration {
            set loadValueList ""
            set queryDetailPerLoad "select $queryElem FROM  $loadeTable where TrialNum = $eachNum and FrameSize = $eachFrameSize "
            set DetailPerLoad [db eval $queryDetailPerLoad]
            set loadNum [expr [llength $DetailPerLoad] / $keyNum]
            regsub -all {\.0+$} $eachFrameSize "" eachFrameSize
            regsub -all {\.+} $eachFrameSize "_" eachFrameSize
            lappend frameSizeList $eachFrameSize
            for {set i 1} {$i <= $loadNum} {incr i} {
                set n 0
                set keyLoad 0
                set index [expr ($i-1)* $keyNum + 1 ]
                set loadValue [lindex $DetailPerLoad $index]
                lappend loadValueList $loadValue
                foreach stcName $detailList {
                    set index [expr ($i-1)* $keyNum + $n]
                    set value [lindex $DetailPerLoad $index]
                    regsub -all {\.0+$} $loadValue "" loadValue
                    regsub -all {\.+} $loadValue "_" loadValue
                    if {[regexp "framelengthdistribution" $stcName]} {
                        if {[regexp -nocase "imix" $frameSizeMode]} {
                            keylset trafficStatsKeyedList iteration.$eachNum.frame_size.frame_size_value $frameSizeList
                            keylset trafficStatsKeyedList iteration.$eachNum.frame_size.$eachFrameSize.load_value $loadValueList
                            keylset trafficStatsKeyedList iteration.$eachNum.frame_size.$eachFrameSize.$loadValue.$stcName $value
                        }
                     } else {
                        keylset trafficStatsKeyedList iteration.$eachNum.frame_size.frame_size_value $frameSizeList
                        keylset trafficStatsKeyedList iteration.$eachNum.frame_size.$eachFrameSize.load_value $loadValueList
                        keylset trafficStatsKeyedList iteration.$eachNum.frame_size.$eachFrameSize.$loadValue.$stcName $value
                    }
                    incr n
                }
              }
             }             
        }
      return $trafficStatsKeyedList
   }
   
proc ::sth::Rfctest::cleanUpRfc3918 {seqHandle} {
    global loopList
    if { [info exists ::sth::Rfctest::userArgsArray(cleanup)] &&  $::sth::Rfctest::userArgsArray(cleanup) == 1} {
        set objectList [::sth::sthCore::invoke stc::get $seqHandle -children]
        foreach object $objectList {
            if {[regexp -nocase {^rfc3918sequencergroupcommand[0-9]+} $object]} {
                ::sth::sthCore::invoke stc::delete $object 
            }
        }
        ::sth::sthCore::invoke stc::config $seqHandle "-CommandList {}"
        set loopList ""
    }         
}

proc ::sth::Rfctest::cleanUpRfc2544 {seqHandle} {
    if { [info exists ::sth::Rfctest::userArgsArray(cleanup)] &&  $::sth::Rfctest::userArgsArray(cleanup) == 1} {
        set objectList [::sth::sthCore::invoke stc::get $seqHandle -children]
        foreach object $objectList {
            if {[regexp "rfc2544" $object]} {
                ::sth::sthCore::invoke stc::delete $object
            }
        }
        ::sth::sthCore::invoke stc::config $seqHandle "-CommandList {}"
    }
}
