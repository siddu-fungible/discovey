namespace eval ::sth::packetDecode {
    variable tshark_tmp
    variable decode_PduList
    
    set tshark_tmp "tshark_tmp.pcap"
    
    #ipv4 attached header field
    set decode_PduList(ipv4,version) "ip.version"
    set decode_PduList(ipv4,hlen) "ip.hdr_len"
    set decode_PduList(ipv4,tos_precedence) "ip.tos.precedence"
    set decode_PduList(ipv4,tos_value) "ip.tos"
    set decode_PduList(ipv4,tos_delay) "ip.tos.delay"
    set decode_PduList(ipv4,tos_throughput) "ip.tos.throughput"
    set decode_PduList(ipv4,tos_reliability) "ip.tos.reliability"
    set decode_PduList(ipv4,tos_unused) "ip.tos"
    set decode_PduList(ipv4,ds_codepoint) "ip.dsfield.dscp"
    set decode_PduList(ipv4,ds_unused) "ip.dsfield.ecn"
    set decode_PduList(ipv4,tot_len) "ip.len"
    set decode_PduList(ipv4,identification) "ip.id"
    set decode_PduList(ipv4,flags) "ip.flags"
    set decode_PduList(ipv4,fragment_offset) "ip.frag_offset"
    set decode_PduList(ipv4,ttl) "ip.ttl"
    set decode_PduList(ipv4,protocol) "ip.proto"
    set decode_PduList(ipv4,header_checksum) "ip.checksum"
    set decode_PduList(ipv4,source_address) "ip.src"
    set decode_PduList(ipv4,destination_address) "ip.dst"
    
    #ethernet_2 attached header field
    set decode_PduList(ethernet_2,destination_address) "eth.dst"
    set decode_PduList(ethernet_2,source_address) "eth.src"
    set decode_PduList(ethernet_2,ether_type) "eth.type"
    
    #ethernet_2_vlan attached header field
    set decode_PduList(ethernet_2_vlan,destination_address) "eth.dst"
    set decode_PduList(ethernet_2_vlan,source_address) "eth.src"
    set decode_PduList(ethernet_2_vlan,ether_type) "eth.type"
    set decode_PduList(ethernet_2_vlan,vlan_tag_type) "vlan.etype"
    set decode_PduList(ethernet_2_vlan,vlan_cfi) "vlan.cfi"
    set decode_PduList(ethernet_2_vlan,vlan_id) "vlan.id"
    set decode_PduList(ethernet_2_vlan,vlan_user_priority) "vlan.priority"
    
    #ipv6 attached header field
    set decode_PduList(ipv6,version) "ipv6.version"
    set decode_PduList(ipv6,flow_label) "ipv6.flow"
    set decode_PduList(ipv6,payload_length) "ipv6.plen"
    set decode_PduList(ipv6,hop_limit) "ipv6.hlim"
    set decode_PduList(ipv6,next_header) "ipv6.nxt"
    set decode_PduList(ipv6,source_address) "ipv6.src"
    set decode_PduList(ipv6,destination_address) "ipv6.dst"
    set decode_PduList(ipv6,traffic_class) "ipv6.traffic_class.dscp -e ipv6.traffic_class.ect -e ipv6.traffic_class.ce"
}

proc ::sth::packetDecode::packet_decode {userInput returnKeyedListName cmdStatusName} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::packetDecode::tshark_tmp
    variable ::sth::packetDecode::decode_PduList
   
    upvar 1 $returnKeyedListName returnKeyedList
    upvar 1 $cmdStatusName cmdState
    upvar 1 $userInput userInputArgs
    ::sth::sthCore::log debug "Executing Internal Command for: packet_decode"
    set cmdState $FAILURE
    
    if {![info exists userInputArgs(open_captured_file)]} {
        :sth::sthCore::processError returnKeyedList "Error while running packet_decode.  Error: open_captured_file field is not specified."
        return $returnKeyedList
    }
    #Using tshark,get frame count and individual frame captured length
    set openfilehandle $userInputArgs(open_captured_file) 
    set cmd {exec tshark -2 -r $openfilehandle -T fields -e frame.number -e frame.cap_len -E separator=\;}
    if {[catch {set frame_num_lenlist [eval $cmd]} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }
    set framecount [llength $frame_num_lenlist]
    
    #get the details according to frame_decode_type
    if {[info exists userInputArgs(frame_decode_type)]} {
        set framedecodetype $userInputArgs(frame_decode_type)
        if {$framedecodetype == "contents"} {
            set cmd {exec tshark -2 -r $openfilehandle -x -S "#####frameseparator#####"}
            if {[catch {set entireframedata [eval $cmd]} errorMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
                return $returnKeyedList
            }
            #delete the specific characters ",{,},[,]
            regsub -all {(\"|{|}|\]|\[)} $entireframedata "" entireframedata
            set entireframedata [string trimright $entireframedata "#####frameseparator#####"]
            regsub -all {\s#####frameseparator#####\s+0000} $entireframedata "\} \{0000" entireframedata
            set entireframedata "{$entireframedata}"
            
            for { set i 0 } { $i < $framecount } { incr i } {
                #get per frame data
                set datalist [split [lindex $entireframedata $i] \n]
                
                #get packet length
                set packetlen [lindex [split [lindex $frame_num_lenlist $i] ";"] 1]
                #Because the data part shows 16 columns in the "data bytes" pane on Wireshark, that is the number "16" meant.
                #the number "17" means 16 plus 1.                
                set dataline [expr $packetlen/16]
                set datemod [expr $packetlen%16]
                set datalisttmp ""
                set datanewlist ""
                for {set index 0} {$index <= $dataline} {incr index} {
                    if {$index!=$dataline} {
                        set datatmp [lreplace [lindex $datalist $index] 17 end]
                    } else {
                        set datatmp [lreplace [lindex $datalist $index] [expr $datemod+1] end]
                    }
                    set datatmp$index [lreplace $datatmp 0 0]
                    set datalisttmp [concat $datalisttmp [set datatmp$index]]
                }
                #puts "The packet hexadecimal data is:\n$datalisttmp"
                foreach tmp $datalisttmp {
                    lappend datanewlist [format "%i" 0x$tmp]                    
                }
                #puts "The packet decimal data is:\n$datanewlist"
                keylset returnKeyedList contents.$i $datanewlist
            }
        } elseif { $framedecodetype == "l2encap" } {
            #get frame protocols, eth.type, vlan.etype, llc.dsap, llc.ssap, llc.control
            set cmd {exec tshark -2 -r $openfilehandle -T fields -e frame.protocols -e eth.type -e vlan.etype -e llc.dsap -e llc.ssap -e llc.control -e frame.cap_len -e ppp.address -e ppp.control -E separator=\;}
            if {[catch {set protocresult [eval $cmd]} errorMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
                return $returnKeyedList
            }
            
            for { set i 0 } { $i < $framecount } { incr i } {
                set encapType ""
                set l2EncapType ""
                set protocols [lindex $protocresult $i]
                regsub -all ";" $protocols "\} \{" protocoltmp
                set protocolnew "\{$protocoltmp\}"
                set frameproto [lindex $protocolnew 0]
                set ethtype [lindex $protocolnew 1]
                set vlantype [lindex $protocolnew 2]
                set llcdsap [lindex $protocolnew 3]
                set llcssap [lindex $protocolnew 4]
                set llccontrol [lindex $protocolnew 5]
                set framelen [lindex $protocolnew 6]
                set pppaddr [lindex $protocolnew 7]
                set pppcontr [lindex $protocolnew 8]
                set proto1 [string range $frameproto 0 2]
                set vlanllcparams [string first "ethertype:vlan:llc" $frameproto]
                set llcparams [string first "eth:llc" $frameproto]
                if {[string equal -nocase $proto1 "eth"]} {
                    if {$ethtype=="0x8100"} {
                        set encapid [lindex [split $vlantype ","] end]
                        if {($encapid=="" || $encapid=="0x8100")&&$vlanllcparams!="-1"} {
                            if {$llcdsap=="0xaa" && $llcssap=="0xaa" && $llccontrol=="0x0003"} {
                                if {$framelen>9022} {
                                    set l2EncapType "l2_ethernet_snap_jumbo_vlan"
                                } else {
                                    set l2EncapType "l2_ethernet_snap_vlan"
                                }
                            } else {
                                if {$framelen>9022} {
                                    set l2EncapType "l2_ethernet_sap_jumbo_vlan"
                                } else {
                                    set l2EncapType "l2_ethernet_sap_vlan"
                                }
                            }
                        } else {
                            #ARP,IP,IPv6,RARP,PPPoE
                            switch $encapid {                                
                                "0x0806" -
                                "0x0800" -                            
                                "0x86dd" -
                                "0x0835" { set l2EncapType "l2_ethernet_dix_vlan" }
                                "0x8863" -
                                "0x8864" { set l2EncapType "ethernet_dix_ppp_vlan" }
                            }
                        }
                    } else {
                        if {$ethtype=="" && $llcparams!="-1"} {
                            if {$llcdsap=="0xaa" && $llcssap=="0xaa" && $llccontrol=="0x0003"} {
                                if {$framelen>9022} {
                                    set l2EncapType "l2_ethernet_snap_jumbo"
                                } else {
                                    set l2EncapType "l2_ethernet_snap"
                                }
                            } else {
                                if {$framelen>9022} {
                                    set l2EncapType "l2_ethernet_sap_jumbo"
                                } else {
                                    set l2EncapType "l2_ethernet_sap"
                                }
                            }
                        } else {
                            #ARP,IP,IPv6,RARP,PPPoE
                            switch $ethtype {                               
                                "0x0806" -
                                "0x0800" -                            
                                "0x86dd" -
                                "0x0835" { set l2EncapType "l2_ethernet_dix" }
                                "0x8863" -
                                "0x8864" { set l2EncapType "ethernet_dix_ppp" }
                                default { set l2EncapType "l2_unknown" }
                            }
                        }
                    }
                }
                if {$pppaddr=="0xff" && $pppcontr=="0x21"} {
                    set l2EncapType "l2_pos_ppp"
                }               
                keylset returnKeyedList l2encap.$i $l2EncapType
            }
        } elseif { $framedecodetype == "hdr_fields" } {
            if {![info exists userInputArgs(header_field_types)]} {
                :sth::sthCore::processError returnKeyedList "Error while running packet_decode.  Error: Header field type is not specified."
                return $returnKeyedList
            }
            if {![info exists userInputArgs(protocol_field)]} {
                :sth::sthCore::processError returnKeyedList "Error while running packet_decode.  Error: Protocol field is not specified."
                return $returnKeyedList
            }
            
            #Using tshark, get all header_field_types returned value based on the protocol_field
            set protoField $userInputArgs(protocol_field)
            set cmd "exec tshark -2 -r $openfilehandle -T fields"
            set dscpflag 0
            set tosflag 0
            set hdrNum 0
            set hdrflag 0
            foreach headerField $userInputArgs(header_field_types) {
                set filtertmp $decode_PduList($protoField,$headerField)
                set ipv4dscpflag [regexp {^ds_.*} $headerField]
                set ipv4tosflag [regexp {^tos_.*} $headerField]
                if {$ipv4tosflag==1} {
                    set tosflag 1
                }
                if {$ipv4dscpflag==1} {
                    set dscpflag 1
                }               
                append cmd " -e $filtertmp"
                if {$dscpflag && $tosflag} {
                    regsub "ip.dsfield.dscp" $cmd "ip.tos" cmd
                    regsub "ip.dsfield.ecn" $cmd "ip.tos" cmd
                }
                set hdrArr($hdrNum) $headerField
                incr hdrNum  
            }
            if {($dscpflag && $tosflag) || (!$dscpflag && $tosflag)} {
                append cmd " -o ip.decode_tos_as_diffserv:false"
            } elseif {$dscpflag && (!$tosflag)} {
                append cmd " -o ip.decode_tos_as_diffserv:true"
            }    
            append cmd { -E header=y -E separator=\;}

            if {[catch {set proHdrResult [eval $cmd]} errorMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
                return $returnKeyedList
            }
            set headerList [split [lindex $proHdrResult 0] ";"]
            set index 0
            foreach tmp $headerList {
                if {$tmp=="ip.tos"} {
                    lappend tospost $index
                }
                incr index
            }
            
            for { set i 0 } { $i < $framecount } { incr i } {

                set proHdrResulttmp [lindex $proHdrResult [expr $i+1]]
                regsub -all ";" $proHdrResulttmp "\} \{" proHdrtmp
                set proHdrtmp "{$proHdrtmp}"
                set ipv6traflag 0
                if {[info exists tospost]} {                        
                        set tosvaluetmp [lindex $proHdrtmp [lindex $tospost end]]
                        foreach tmp $tospost {
                        set proHdrtmp [lreplace $proHdrtmp $tmp $tmp $tosvaluetmp]
                        }
                    }
                for { set j 0 } { $j < $hdrNum } { incr j } {
                    
                    if {$protoField =="ipv6" && $hdrArr($j)=="traffic_class"} {
                        #get ipv6 traffic class through ipv6.traffic_class.dscp , ipv6.traffic_class.ect and ipv6.traffic_class.ce
                        set traffic_class_dscp [lindex [split [lindex $proHdrtmp $j] ","] 0]
                        set traffic_class_ect [lindex [split [lindex $proHdrtmp [expr $j+1]] ","] 0]
                        set traffic_class_ce [lindex [split [lindex $proHdrtmp [expr $j+2]] ","] 0]
                        set traffic_class ""
                        if {$traffic_class_dscp!=""} {
                        set traffic_class [expr $traffic_class_dscp << 2|($traffic_class_ect$traffic_class_ce)]
                        }
                        keylset returnKeyedList hdr_fields.$i.$hdrArr($j) $traffic_class
                        set ipv6traflag 1
                    } else {
                        if {$ipv6traflag==1} {
                            set proHdrnew [lindex $proHdrtmp [expr $j+2]]
                        } else {
                            set proHdrnew [lindex $proHdrtmp $j]
                        }
                        
                        set procrsttmp [split [lindex [split $proHdrnew ","] 0] "."]

                        set retlisttmp ""
                        set fmt ""
                        if {$procrsttmp!="" && $protoField=="ipv4" && $hdrArr($j)=="tos_unused"} {
                            set returnList [expr $procrsttmp&3]
                        } elseif {$procrsttmp!="" && $protoField=="ipv4" && $hdrArr($j)=="tos_value"} {
                            set returnList [expr ($procrsttmp>>1)&15]
                        } elseif {$procrsttmp!="" && $dscpflag && $tosflag && $hdrArr($j)=="ds_codepoint"} {
                            set returnList [expr $procrsttmp>>2]
                        } elseif {$procrsttmp!="" && $dscpflag && $tosflag && $hdrArr($j)=="ds_unused"} {
                            set returnList [expr $procrsttmp&3]                           
                        } elseif {$procrsttmp!="" && $protoField=="ipv6" && ($hdrArr($j)=="source_address"||$hdrArr($j)=="destination_address")} {
                            set procrsttmp [split [::sth::sthCore::normalizeIPv6Addr $procrsttmp] ":"]
                            set procrsttmp1 ""
                            foreach tmp $procrsttmp {
                                set procrsttmp1 [concat $procrsttmp1 [scan $tmp %2s%2s]]
                            }
                            foreach tmp $procrsttmp1 {
                                lappend retlisttmp [format "%i" 0x$tmp]
                            }
                            set returnList $retlisttmp
                        } elseif {[string range $procrsttmp 0 1] == "0x"} {
                            if {$hdrArr($j)=="flow_label"} {
                                set procrsttmp [string replace $procrsttmp 2 3]
                            }
                            set procrsttmp [string replace $procrsttmp 0 1]
                            set datalen [string length $procrsttmp]
                            
                            for { set index 0 } { $index < $datalen/2 } { incr index } {
                                append fmt "%2s"
                            }
                            set procrsttmp [scan $procrsttmp $fmt]
                            foreach tmp $procrsttmp {
                                lappend retlisttmp [format "%i" 0x$tmp]
                            }
                            set returnList $retlisttmp
                        } elseif {[regexp -nocase {([0-9a-f]{2}:){5}[0-9a-f]{2}} $procrsttmp]} {
                            set procrsttmp [split $procrsttmp ":"]                        
                            foreach tmp $procrsttmp {
                                lappend retlisttmp [format "%i" 0x$tmp]
                            }
                            set returnList $retlisttmp
                        } elseif { $procrsttmp > 255 } {
                            set procrsttmp [format "%x" $procrsttmp]
                            set datalen [string length $procrsttmp]
                            set datamod [expr $datalen%2]
                            switch $datamod {
                                0 { set hexdataNum [expr $datalen/2] }
                                1 { set hexdataNum [expr $datalen/2 + 1]
                                set procrsttmp "0$procrsttmp" }
                            }
                            for { set index 0 } { $index < $hexdataNum } { incr index } {
                                append fmt "%2s"
                            }
                            set procrsttmp [scan $procrsttmp $fmt]
                            foreach tmp $procrsttmp {
                                lappend retlisttmp [format "%i" 0x$tmp]
                            }
                            set returnList $retlisttmp
                        } else {       
                            set returnList $procrsttmp
                        }
                        
                        keylset returnKeyedList hdr_fields.$i.$hdrArr($j) $returnList
                    }
                }               
            }
        }                       
    }    
    set cmdState $SUCCESS
}