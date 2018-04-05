# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

###/*! \file hltapi_5.10_stc_2.0.tcl
###    \brief Main file
###
###    This file is the main entry point for 'source' or 'package require', usuages.
###    It  implements the namespace ::sth::
###*/

# incase the toolMain.tcl will source this file, need to put the message to the GUI console.
proc puts_msg {message} {
        if {[info exists ::text]} {
                $::text insert end "\n$message"
                update
        } else {
                puts $message
    }
}

puts_msg "\nOS: $::tcl_platform(os), $::tcl_platform(osVersion), $::tcl_platform(platform); Tcl version: $::tcl_patchLevel\n"
if {![regexp "8.4" $::tcl_patchLevel]&&![regexp "8.5" $::tcl_patchLevel]} {
	puts_msg "HLTAPI supports tcl 8.4.xxx: \n\tWrong Tcl version $::tcl_patchLevel may load HLTAPI wrongly!"
}

set _HLT_VERSION 4.81
#set _STC_VERSION 3.00
set _Tclx_VERSION 8.3

#if {[catch {package require SpirentTestCenter $_STC_VERSION}]} {
#    set _errorMsg "Error Loading Spirent TestCenter Automation Version $_STC_VERSION"
#    set _errorInfoMsg "Error Loading Spirent HLT Api (Ver. $_HLT_VERSION)"
#    set __NOSTC__ 1
#}

if {[catch {package require SpirentTestCenter}]} {
    set _errorMsg "Error Loading Spirent TestCenter Automation"
    set _errorInfoMsg "Error Loading Spirent HLT Api (Ver. $_HLT_VERSION)"
    set __NOSTC__ 1
}

if {[catch {package require Tclx $_Tclx_VERSION}]} {
    append _errorMsg "Error Loading Tcl Extension Version $_Tclx_VERSION"
    set __NOSTC__ 1
}

if {[::info exists __NOSTC__]} {
    return -code 1 -errorcode -1 $_errorMsg
}
### John Moris comment: we may use a simple bool variable for this _NOSTC_ variable.

variable _CURRENT_DIR [file dirname [::info script]]

###/*! \namespace sth
###\brief Exports all the commands for the HltApi
###
###All the commands for the HltApi are exported through this namespace. The list of the exported commands are :
###\li \c connect
###*/
### namespace sth {
namespace eval ::sth {

    # Trying to dynamically create the list of valid Arguments for the commands in HLT Api
    variable serverflag 0
    variable _RUNNING_DIR $env(TCL_RUNNING_DIR)
    variable _UtilityFiles {sthCore \
                            Session \
                            SessionFunctions \
                            bll \
                            doStcLib \
                            sthutils \
                            sessionTable \
                            traffic \
                            trafficFunctions \
                            trafficTable \
                            trafficConfig \
                            trafficConfigFunctions \
                            trafficConfigTable \
                            IsIs \
                            isisTable \
                            isisFunctions \
                            bfd \
                            bfdFunctions \
                            bfdTable \
                            bgp \
                            bgpFunctions \
                            bgpTable \
                            convergence \
                            convergenceFunctions \
                            convergenceTable \
                            ldp \
                            ldpFunctions \
                            ldpTable \
                            ospf \
                            ospfFunctions \
                            ospfTable \
                            linkOam \
                            linkOamFunctions\
                            linkOamTable \
                            rsvp \
                            RsvpFunctions \
                            rsvpTable \
                            parse_dashed_args\
                            testconfigcontrol\
                            testconfigcontrolFunctions\
                            testconfigcontrolTable\
                            pppox \
                            pppoxFunctions \
                            pppoxTable \
                            dhcp \
                            dhcpFunctions \
                            dhcpTable \
                            multicast_group \
                            multicast_groupFunctions \
                            multicast_groupTable \
                            dhcpServer \
                            dhcpServerFunctions \
                            dhcpServerTable \
                            igmp \
                            igmpFunctions \
                            igmpTable \
                            mld \
                            mldFunctions \
                            mldTable \
                            pim \
                            pimFunctions \
                            pimTable \
                            packetCapture \
                            packetCaptureTable \
                            packetCaptureFunctions \
							packetDecode \
                            packetDecodeTable \
                            packetDecodeFunctions \
                            ping \
                            pingFunctions \
                            pingTable \
                            rip \
                            ripFunctions \
                            ripTable \
                            ospfTopologyTable \
                            ospfTopology \
                            ospfTopologyFunctions \
                            greTable \
                            gre \
                            greFunctions \
                            l2tp \
                            l2tpFunctions \
                            l2tpTable \
                            l2tpv3 \
                            l2tpv3Functions \
                            l2tpv3Table \
                            vplsTable \
                            vpls \
                            vplsFunctions \
                            eoamTable \
                            eoam \
                            eoamFunctions \
                            sip \
                            sipFunctions \
                            sipTable \
                            rfctest \
                            rfctestTable \
                            rfctestFunctions \
                            ancp \
                            ancpTable \
                            ancpFunctions \
                            mvpnTable \
                            mvpn \
                            mvpnFunctions \
                            lacp \
                            lacpTable \
                            lacpFunctions \
                            alarms \
                            alarmsFunctions \
                            alarmsTable \
                            mplsvpn \
                            mplsvpnTable \
                            mplsvpnFunctions \
                            fc\
                            fcTable \
                            fcFunctions \
                            fcoe\
                            fcoeTable \
                            fcoeFunctions \
                            fcoeTraffic \
                            fcoeTrafficTable \
                            fcoeTrafficFunctions \
                            lldp \
                            lldpTable \
                            lldpFunctions \
                            pppoxServer \
                            pppoxServerFunctions \
                            pppoxServerTable \
                            ptp \
                            ptpFunctions \
                            ptpTable \
                            dot1x \
                            dot1xFunctions \
                            dot1xTable \
                            mplsTp \
                            mplsTpTable \
                            mplsTpFunctions \
			                stp \
                            stpFunctions\
                            stpTable\
			                synce \
                            synceFunctions\
                            synceTable\
                            dhcpv6 \
                            dhcpv6Table \
                            dhcpv6Functions\
                            dhcpv6Server \
                            dhcpv6ServerTable \
                            dhcpv6ServerFunctions \
                            ppp\
                            pppFunctions\
                            pppTable \
                            ipv6AutoConfig\
                            ipv6AutoConfigTable\
                            ipv6AutoConfigFunctions\
                            trafficConfigOspf\
                            trafficConfigOspfTable\
                            trafficConfigOspfFunctions\
                            igmpQuerier\
                            igmpQuerierTable\
                            igmpQuerierFunctions\
                            device\
                            deviceTable\
                            deviceFunctions\
                            vxlan\
                            vxlanTable\
                            vxlanFunctions\
                            fortyHundredGigTable\
                            fortyHundredGigFunctions \
                            fortyHundredGig \
                            openflow \
                            openflowTable \
                            openflowFunctions \
                            http \
                            httpTable \
                            httpFunctions
                            pcep \
                            twamp \
                            twampTable \
                            twampFunctions \
                            iptv \
                            iptvFunctions \
                            iptvTable \
                            vqa \
                            vqaTable \
                            vqaFunctions \
                            video\
                            videoTable\
                            videoFunctions\
                            6pe6vpe \
                            6pe6vpeFunctions \
                            6pe6vpeTable \
                            vxlanEvpnOverlay\
                            vxlanEvpnOverlayTable\
                            vxlanEvpnOverlayFunctions\
                            mplsIpVpn \
                            mplsIpVpnFunctions \
                            mplsIpVpnTable \
                            mplstpY1731Oam\
                            mplstpY1731OamTable\
                            mplstpY1731OamFunctions\
                            microBfd\
                            microBfdTable\
                            microBfdFunctions\
                            lspPing\
                            lspPingFunctions\
                            lspPingTable\
                            }
    foreach fileName $_UtilityFiles {
    	if {[catch {source [file join $_CURRENT_DIR $fileName.tcl]} e  ]} {
    	    append eMsg "Error loading the Spirent HLTApi Internal File $fileName.tcl (Ver. $_HLT_VERSION). ($e).\n"
    	    set errorLoadingUtilityFiles 1
    	}
    }

	set etbcMsg ""
	variable _tbcUtilityFiles {tools//hlapiGenUtilities\
	                        tools//hlapiGen\
							tools//hlapiGenTable\
							tools//hlapiGenFunction\
							tools//hlapiGenFunctionH\
							tools//hlapiGenFunctionM\
							tools//hlapiGenFunctionP\
							tools//hlapiGenTraffic\
							tools//hlapiGenBasic\
							tools//hlapiGenFunctionCtrl\
							tools//hlapiGenFunctionResults\
							tools//hlapiGenPythonFunction\
                            tools//hlapiGenPerlFunction\
                            tools//hlapiGenRobotFunction\
							tools//hlapiGenFunctionSequencer\
							tools//xtapi\
							}
	foreach fileName $_tbcUtilityFiles {
		if {[catch {source [file join $_CURRENT_DIR $fileName.tcl]} e  ]} {
			append etbcMsg "Loading Spirent HLTApi hlapiGen files \"$fileName.tcl\" (Ver. $_HLT_VERSION). ($e).\n"
		}
	}
    if {[::info exists errorLoadingUtilityFiles]} {
    	catch {package forget SpirentTestCenter}
    	catch {namespace delete ::stc::}
    	return -code 1 -errorcode -2 $eMsg
    } else {
		if {$etbcMsg ne "" } {
			puts_msg "<warning>: \"Save As HLTAPI\" functionality is disabled due to wrong loading hlapiGen files:"
			puts_msg $etbcMsg
		} else {
			set ePluginMsg [::sth::hlapiGen::loadPluginFile "$_CURRENT_DIR\//tools"]
			if {$ePluginMsg ne "" } {
				puts_msg "<warning>: \"Save As HLTAPI\"'s plugin loading mistakes:"
				puts_msg $ePluginMsg
			}
		}
		::sth::sthCore::sthCoreInit
		package require ip

    	# Exporting the commands provided by Spirent HLT Api
        namespace export alarms_control
        namespace export alarms_stats
        namespace export cleanup_session
        namespace export connect
        namespace export device_info
        namespace export emulation_ancp_config
        namespace export emulation_ancp_control
        namespace export emulation_ancp_stats
        namespace export emulation_ancp_subscriber_lines_config
        namespace export emulation_bfd_config
        namespace export emulation_bfd_control
        namespace export emulation_bfd_info
        namespace export emulation_bgp_config
        namespace export emulation_bgp_control
        namespace export emulation_bgp_info
        namespace export emulation_bgp_route_config
        namespace export emulation_bgp_custom_attribute_config
        namespace export emulation_bgp_route_info
        namespace export emulation_convergence_config
        namespace export emulation_convergence_control
        namespace export emulation_convergence_info
        namespace export emulation_dhcp_config
        namespace export emulation_dhcp_group_config
        namespace export emulation_dhcp_control
        namespace export emulation_dhcp_stats
        namespace export emulation_dhcp_server_config
        namespace export emulation_dhcp_server_control
        namespace export emulation_dhcp_server_relay_agent_config
        namespace export emulation_dhcp_server_stats
        namespace export emulation_efm_config
        namespace export emulation_efm_control
        namespace export emulation_efm_stat
        namespace export emulation_gre_config
        namespace export emulation_igmp_config
        namespace export emulation_igmp_control
        namespace export emulation_igmp_group_config
        namespace export emulation_igmp_info
        namespace export emulation_isis_config
        namespace export emulation_isis_control
        namespace export emulation_isis_info
        namespace export emulation_isis_topology_route_config
        namespace export emulation_l2vpn_pe_config
        namespace export emulation_lacp_config
        namespace export emulation_lacp_control
        namespace export emulation_lacp_info
        namespace export emulation_ldp_config
        namespace export emulation_ldp_control
        namespace export emulation_ldp_info
        namespace export emulation_ldp_route_config
        namespace export emulation_lldp_config
        namespace export emulation_lldp_control
        namespace export emulation_lldp_dcbx_tlv_config
        namespace export emulation_lldp_info
        namespace export emulation_lldp_optional_tlv_config
        namespace export emulation_mld_config
        namespace export emulation_mld_control
        namespace export emulation_mld_group_config
        namespace export emulation_mld_info
        namespace export emulation_mpls_l2vpn_pe_config
        namespace export emulation_mpls_l2vpn_site_config
        namespace export emulation_mpls_l3vpn_pe_config
        namespace export emulation_mpls_l3vpn_site_config
        namespace export emulation_multicast_group_config
        namespace export emulation_multicast_source_config
        namespace export emulation_mvpn_config
        namespace export emulation_mvpn_control
        namespace export emulation_mvpn_customer_port_config
        namespace export emulation_mvpn_info
        namespace export emulation_mvpn_provider_port_config
        namespace export emulation_oam_config_msg
        namespace export emulation_oam_config_topology
        namespace export emulation_oam_control
        namespace export emulation_oam_info
        namespace export emulation_ospf_config
        namespace export emulation_ospf_control
        namespace export emulation_ospf_lsa_config
        namespace export emulation_ospf_route_info
        namespace export emulation_ospf_topology_route_config
        namespace export emulation_ospfv2_info
        namespace export emulation_ospfv3_info
        namespace export emulation_pim_config
        namespace export emulation_pim_control
        namespace export emulation_pim_group_config
        namespace export emulation_pim_info
        namespace export emulation_ping
        namespace export emulation_ptp_config
        namespace export emulation_ptp_control
        namespace export emulation_ptp_stats
        namespace export emulation_rip_config
        namespace export emulation_rip_control
        namespace export emulation_rip_info
        namespace export emulation_rip_route_config
        namespace export emulation_rsvp_config
        namespace export emulation_rsvp_control
        namespace export emulation_rsvp_info
        namespace export emulation_rsvp_tunnel_config
        namespace export emulation_rsvp_tunnel_info
        namespace export emulation_rsvpte_tunnel_control
        namespace export emulation_sip_config
        namespace export emulation_sip_control
        namespace export emulation_sip_stats
        namespace export emulation_synce_config
        namespace export emulation_synce_control
        namespace export emulation_synce_stats
        namespace export emulation_vpls_site_config
        namespace export emulation_mpls_tp_config
        namespace export emulation_mpls_tp_port_config
        namespace export emulation_mpls_tp_control
        namespace export emulation_lsp_ping_info
        namespace export emulation_dot1x_config
        namespace export emulation_dot1x_control
        namespace export emulation_dot1x_stats
        namespace export emulation_stp_config
        namespace export emulation_mstp_region_config
        namespace export emulation_msti_config
        namespace export emulation_stp_control
        namespace export emulation_stp_stats
        namespace export emulation_ipv6_autoconfig
        namespace export emulation_ipv6_autoconfig_control
        namespace export emulation_ipv6_autoconfig_stats
        namespace export fc_config
        namespace export fc_control
        namespace export fc_stats
        namespace export fcoe_config
        namespace export fcoe_control
        namespace export fcoe_stats
        namespace export fcoe_traffic_config
        namespace export fip_traffic_config
        namespace export interface_config
        namespace export interface_stats
        namespace export l2tp_config
        namespace export l2tp_control
        namespace export l2tp_stats
        namespace export labserver_connect
        namespace export labserver_disconnect
        namespace export packet_config_buffers
        namespace export packet_config_filter
        namespace export packet_config_triggers
        namespace export packet_control
        namespace export packet_info
        namespace export packet_stats
        namespace export packet_decode
        namespace export ppp_config
        namespace export ppp_stats
        namespace export pppox_config
        namespace export pppox_control
        namespace export pppox_server_config
        namespace export pppox_server_control
        namespace export pppox_server_stats
        namespace export pppox_stats
        namespace export test_config
        namespace export test_control
        namespace export test_rfc2544_config
        namespace export test_rfc2544_control
        namespace export test_rfc2544_info
        namespace export test_rfc3918_config
        namespace export test_rfc3918_control
        namespace export test_rfc3918_info
        namespace export traffic_config
        namespace export traffic_control
		namespace export start_test
    	namespace export emulation_mcast_wizard_config
        namespace export traffic_stats
        namespace export traffic_config_ospf
        namespace export emulation_igmp_querier_config
        namespace export emulation_igmp_querier_control
        namespace export emulation_igmp_querier_info
        namespace export emulation_openflow_config
        namespace export emulation_openflow_control
        namespace export emulation_openflow_stats
        namespace export emulation_openflow_switch_config
        namespace export emulation_openflow_switch_control
        namespace export emulation_openflow_switch_stats
        namespace export hlapiGen
        namespace export emulation_http_profile_config
        namespace export emulation_http_config
        namespace export emulation_http_control
        namespace export emulation_http_stats
        namespace export emulation_twamp_config
        namespace export emulation_twamp_session_config
        namespace export emulation_twamp_control
        namespace export emulation_twamp_stats
        namespace export emulation_iptv_config
        namespace export emulation_vqa_host_config
        namespace export emulation_vqa_config
        namespace export emulation_vqa_port_config
        namespace export emulation_vqa_global_config
        namespace export emulation_vqa_control
        namespace export emulation_vqa_stats
        namespace export emulation_video_config
        namespace export emulation_video_server_streams_config
        namespace export emulation_video_clips_manage
        namespace export emulation_video_stats
        namespace export emulation_mplstp_y1731_oam_control
        namespace export emulation_mplstp_y1731_oam_stats
        namespace export emulation_micro_bfd_config
        namespace export emulation_micro_bfd_control
        namespace export emulation_micro_bfd_info
    }

    if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
        #set hlt_dir [file dirname [file join [pwd] [info script]]]
        set mydirectory [file dirname [file join [pwd] [info script]]]
        set sqldir "sqllibraries\\Windows"
        set hlt_dir [file join $mydirectory $sqldir]
        load $hlt_dir/tclsqlite3.dll
    } else {
	set filename "libtclsqlite3.so"
        if {![string compare -nocase $::tcl_platform(os) "SunOS"]} {
            set sqldir "sqllibraries\/SunOS"
            #set hlt_dir [file join [pwd] $sqldir]
            set mydirectory [file dirname [file join [pwd] [info script]]]
            set hlt_dir [file join $mydirectory $sqldir]
        } elseif {![string compare -nocase $::tcl_platform(os) "Linux"]} {
            set sqldir "sqllibraries\/Linux"
            set mydirectory [file dirname [file join [pwd] [info script]]]
            set hlt_dir [file join $mydirectory $sqldir]
	    #check if it is 64bit system, if it is 64 bit the the file name will
	    #be the one for the 64 bits
	#    if {[regexp "64" $::tcl_platform(machine)]} {
	#	set filename "libtclsqlite3_64.so"
	#    }
	    if {[info exists ::tcl_platform(pointerSize)]} {
		#pointerSize only defined in tcl version greater than 8.15
		if {$::tcl_platform(pointerSize) == 8} {
		    set filename "libtclsqlite3_64.so"
		}
	    } elseif {[info exists ::tcl_platform(wordSize)] && $::tcl_platform(wordSize) == 8} {
		set filename "libtclsqlite3_64.so"
	    }
        }

        load $hlt_dir/$filename
    }

}
###}; //ending for namespace comment for doc

set mycheck [file join $_CURRENT_DIR checkConfig.tcl]
if {[file exist $mycheck]} {
	source $mycheck
	puts "Sourcing checkConfig.tcl for regression test"
	namespace export regression
	namespace export check_config
}

package provide SpirentHltApi $_HLT_VERSION
package provide sth $_HLT_VERSION
puts "SpirentTestCenter Automation Version: [stc::get system1 -version]"
puts "Hlt Api (Ver. $_HLT_VERSION) was successfully loaded and initialized"

# This version is used during the development and PV test process
set internal_ver 4.81.1222
puts "Internal Version: $internal_ver"

namespace eval ::sth:: {
}

namespace eval ::sth::xtapi {

}
# Provide our own implementation
proc ::sth::emulation_evpn_config {args} {
        set cmdName "::sth::emulation_evpn_config"
        ::sth::sthCore::Tracker $cmdName $args
        set ::sth::xtapi::returnKeyedList ""
        set commandName [string trim $cmdName "::"]
        set commandName "::$commandName"
        if {[catch {
                set ::sth::xtapi::returnKeyedList [eval ::xtapi::scriptrun_stak $commandName $args]} err]} {
                ::sth::sthCore::processError ::sth::xtapi::returnKeyedList "Error in processing stak command : $err"
                return $::sth::xtapi::returnKeyedList
        }
        keylget ::sth::xtapi::returnKeyedList vpnevpngenparams_hnd myparam
        if {[info exists myparam] && $myparam != ""} {
                ::sth::sthCore::invoke stc::perform VpnGenConfigExpand -clearportconfig no -genparams $myparam
                set devices [stc::get project1 -children-emulateddevice]
                set ldp_device ""
                set bfd_device ""
                set ospfv2_device ""
                set bgp_device ""
                set ldp_config ""
                set bfd_config ""
                set ospfv2_config ""
                set bgp_config ""
                set streamblocks ""
                foreach dev $devices {
                        set config [stc::get $dev -children-LdpRouterConfig]
                        if {$config != ""} {
                                append ldp_device "$dev "
                                append ldp_config "$config "
                        }

                        set config [stc::get $dev -children-BfdRouterConfig]
                        if {$config != ""} {
                                append bfd_device "$dev "
                                append bfd_config "$config "
                        }

                        set config [stc::get $dev -children-Ospfv2RouterConfig]
                        if {$config != ""} {
                                append ospfv2_device "$dev "
                                append ospfv2_config "$config "
                        }

                        set config [stc::get $dev -children-BgpRouterConfig]
                        if {$config != ""} {
                                append bgp_device "$dev "
                                append bgp_config "$config "
                        }

						set deviceName [::sth::sthCore::invoke stc::get $dev -Name]
						if { [string first "CE Router" $deviceName] > -1 } {
							lappend ceRouter $dev
						} elseif { [string first "PE Router" $deviceName] > -1 } {
							lappend peRouter $dev
						}
                }

                keylset ::sth::xtapi::returnKeyedList LdpRouterConfig $ldp_config
                keylset ::sth::xtapi::returnKeyedList BfdRouterConfig $bfd_config
                keylset ::sth::xtapi::returnKeyedList Ospfv2RouterConfig $ospfv2_config
                keylset ::sth::xtapi::returnKeyedList BgpRouterConfig $bgp_config

				keylset ::sth::xtapi::returnKeyedList BgpRouter $bgp_device
				keylset ::sth::xtapi::returnKeyedList LdpRouter $ldp_device
                keylset ::sth::xtapi::returnKeyedList OspfRouter $ospfv2_device
				keylset ::sth::xtapi::returnKeyedList BfdRouter $bfd_device
                
				keylset ::sth::xtapi::returnKeyedList CERouter $ceRouter
				keylset ::sth::xtapi::returnKeyedList PERouter $peRouter

                set ports [stc::get project1 -children-port]
                foreach p $ports {
                        set config [stc::get $p -children-Streamblock]
                        if {$config != ""} {
                                append streamblocks "$config "
                        }
                }
                set streamblocks [string trim $streamblocks]
                keylset ::sth::xtapi::returnKeyedList Streamblock $streamblocks

        }
        keylset ::sth::xtapi::returnKeyedList status $::sth::sthCore::SUCCESS
        return $::sth::xtapi::returnKeyedList
}

namespace eval ::sth::sthCore {
    array set GBLHNDMAP {}
    ProcessDefaultYamlFile
}

