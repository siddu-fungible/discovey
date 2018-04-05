# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Traffic:: {
}

set ::sth::Traffic::trafficOspfTable {
    ::sth::Traffic::
    {   traffic_config_ospf_packets
        {hname                  stcobj              stcattr             type                                        priority    default     range     dependency                 mandatory   procfunc         mode        constants                                                                                           constants}
        {mode                   _none_              _none_          {CHOICES create modify delete}                  1     _none_        _none_    _none_                        true       _none_         _none_       _none_}
        {handle                 _none_              _none_          ANY                                             2     _none_        _none_    _none_                        false      _none_         _none_       _none_}
        {type	                _none_	            _none_	{CHOICES packets update_router_lsa_link update_router_lsa_tos update_summary_lsa_tos update_asexternal_lsa_tos}   1	_none_  _none_  _none_   true	   _none_   _none_    _none_}
        {stream_id	        _none_	            _none_	    ALPHANUM  	                                    2	  _none_	_none_	  _none_	                true	  _none_	  _none_       _none_}	
        {ospf_type	        ospfv2.header	    type	    {CHOICES dd hello req ack unknown update}	    1	  _none_	_none_	  _none_		        true	  _none_	  _none_     {dd 2 hello 1 req  3 ack 5 unknown 0 update 4}}
        {ospf_router_id	        ospfv2.header	    routerID  	    IP  	  	                            5	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
	{ospf_area_id	        ospfv2.header	    areaID	    IP  	  	                            5	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
	{ospf_checksum	        ospfv2.header	    checksum	    HEX 	  	                            5	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
	{ospf_auth_type	        authSelect          authType  	    {CHOICES none password md5 userdefined}	    5	  _none_	_none_	  _none_		        false	  _none_	  _none_     {none 0 password 1 md5 2 userdefined 3}}
        {ospf_auth_value1       authSelect          authValue1      NUMERIC	  	                            5	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_auth_value2       authSelect          authValue2      NUMERIC	  	                            5	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
        
        {ospf_lsa_num            _none_             _none_      	    NUMERIC	  	                            8	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        {ospf_lsa_age           ospfv2LsaHeader     lsaAge  	            NUMERIC	  	                            9	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        {ospf_lsa_header_options _none_             _none_  	            {REGEXP ^[0-1]{8}$}                             9	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        {ospf_ls_type           ospfv2LsaHeader     lsType  	            NUMERIC	  	                            9	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        {ospf_ls_link_state_id  ospfv2LsaHeader     linkStateId  	    IP       	  	                            9	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        {ospf_ls_ad_router      ospfv2LsaHeader     advertisingRouter 	    IP        	  	                            9	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        {ospf_ls_seq_number     ospfv2LsaHeader     lsSequenceNumber  	    HEX  	  	                            9	  _none_	_none_	  {dd ack}		        false	  _none_	  _none_       _none_}
        
        {ospf_interface_mtu         ospfv2	    interfaceMtu   	    NUMERIC	  	                            6	  _none_	_none_	  {dd}		                false	  _none_	  _none_       _none_}
        {ospf_packets_options       _none_          _none_  	            {REGEXP ^[0-1]{8}$}                             6	  _none_	_none_	  {dd hello}		        false	  _none_	  _none_       _none_}
        {ospf_dd_options            _none_          _none_  	            {REGEXP ^[0-1]{8}$}	  	                    6	  _none_	_none_	  {dd}		                false	  _none_	  _none_       _none_}
        {ospf_dd_seq_number         ospfv2	    sequenceNumber          NUMERIC	  	                            6	  _none_	_none_	  {dd}		                false	  _none_	  _none_       _none_}
        
        {ospf_network_mask          ospfv2	    networkMask  	    IP  	  	                            6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        {ospf_hello_interval        ospfv2	    helloInterval  	    NUMERIC	  	                            6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        {ospf_router_priority       ospfv2	    routerPriority  	    NUMERIC	  	                            6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        {ospf_router_dead_interval  ospfv2          routerDeadInterval	    NUMERIC	  	                            6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        {ospf_designated_router     ospfv2          designatedRouter  	    IP	  	                                    6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        {ospf_bk_designated_router  ospfv2          backupDesignatedRouter  IP	  	                                    6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        {ospf_neighbor_id           ospfv2neighbor  neighborID  	    IP  	  	                            6	  _none_	_none_	  {hello}		        false	  _none_	  _none_       _none_}
        
        {ospf_req_lsa_num        _none_              _none_      	    NUMERIC	  	                            6	  _none_	_none_	  {req}		                false	  _none_	  _none_       _none_}
        {ospf_req_ls_type        ospfv2RequestedLsa  lsTypeWide   	    NUMERIC	  	                            7	  _none_	_none_	  {req}		                false	  _none_	  _none_       _none_}
        {ospf_req_link_state_id  ospfv2RequestedLsa  linkStateId   	    IP       	  	                            7	  _none_	_none_	  {req}		                false	  _none_	  _none_       _none_}
        {ospf_req_ad_router      ospfv2RequestedLsa  advertisingRouter      IP        	  	                            7	  _none_	_none_	  {req}		                false	  _none_	  _none_       _none_}
   
        {ospf_num_of_lsas                   ospfv2                     numberOfLsas  	    NUMERIC	  	    6	  _none_	_none_	  {update}		        false	  _one_	          _none_       _none_}
        {ospf_router_lsa_num                _none_                     _none_      	    NUMERIC	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_age                ospfv2RouterLsa.Header     lsaAge  	            NUMERIC	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_header_options     _none_                     _none_  	            {REGEXP ^[0-1]{8}$}     7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_type               ospfv2RouterLsa.Header     lsType  	            NUMERIC	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_link_state_id      ospfv2RouterLsa.Header     linkStateId  	     IP       	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_ad_router          ospfv2RouterLsa.Header     advertisingRouter     IP        	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_seq_number         ospfv2RouterLsa.Header     lsSequenceNumber      HEX  	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}        
        {ospf_router_lsa_options            _none_                     _none_  	            {REGEXP ^[0-1]{8}$}     7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_reserved           ospfv2RouterLsa            routerLsaReserved1    NUMERIC  	  	    7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_router_lsa_num_of_linklist    ospfv2RouterLsa            numberOfLinks  	     NUMERIC                7	  _none_	_none_	  {update}		        false	  _none_	  _none_       _none_}
        {ospf_network_lsa_num                _none_                      _none_      	            NUMERIC	  	    6	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_age                ospfv2NetworkLsa.Header     lsaAge  	            NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_header_options     _none_                      _none_  	            {REGEXP ^[0-1]{8}$}     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_type               ospfv2NetworkLsa.Header     lsType  	            NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_link_state_id      ospfv2NetworkLsa.Header     linkStateId  	            IP       	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_ad_router          ospfv2NetworkLsa.Header     advertisingRouter          IP        	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_seq_number         ospfv2NetworkLsa.Header     lsSequenceNumber           HEX  	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}        
        {ospf_network_lsa_network_mask       ospfv2NetworkLsa            networkMask  	            IP                      7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_network_lsa_attached_router_id Ospfv2AttachedRouter        routerID  	            MULTILIST                     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_num                _none_                      _none_      	            NUMERIC	  	    6	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_age                ospfv2SummaryLsa.Header     lsaAge  	            NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_header_options     _none_                      _none_  	            {REGEXP ^[0-1]{8}$}     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_type               ospfv2SummaryLsa.Header     lsType  	            NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_link_state_id      ospfv2SummaryLsa.Header     linkStateId  	            IP       	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_ad_router          ospfv2SummaryLsa.Header     advertisingRouter          IP        	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_seq_number         ospfv2SummaryLsa.Header     lsSequenceNumber           HEX  	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}        
        {ospf_summary_lsa_network_mask       ospfv2SummaryLsa            networkMask  	            IP                      7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_reserved           ospfv2SummaryLsa            summaryLsaReserved1  	    NUMERIC                 7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_metric             ospfv2SummaryLsa            summaryLsaMetric  	    NUMERIC                 7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_num               _none_                          _none_      	     NUMERIC	  	    6	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_age               ospfv2SummaryAsbrLsa.Header     lsaAge  	     NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_header_options    _none_                          _none_  	    {REGEXP ^[0-1]{8}$}     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_type              ospfv2SummaryAsbrLsa.Header     lsType  	     NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_link_state_id     ospfv2SummaryAsbrLsa.Header     linkStateId  	     IP       	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_ad_router         ospfv2SummaryAsbrLsa.Header     advertisingRouter    IP        	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_seq_number        ospfv2SummaryAsbrLsa.Header     lsSequenceNumber     HEX  	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}        
        {ospf_summaryasbr_lsa_network_mask      ospfv2SummaryAsbrLsa            networkMask  	     IP                     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_reserved          ospfv2SummaryAsbrLsa            summaryLsaReserved1  NUMERIC                7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_summaryasbr_lsa_metric            ospfv2SummaryAsbrLsa            summaryLsaMetric     NUMERIC                7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_num                _none_                          _none_      	     NUMERIC	  	    6	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}        
        {ospf_asexternal_lsa_age                ospfv2AsExternalLsa.Header      lsaAge  	     NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_header_options     _none_                          _none_  	     {REGEXP ^[0-1]{8}$}    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_type               ospfv2AsExternalLsa.Header      lsType  	     NUMERIC	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_link_state_id      ospfv2AsExternalLsa.Header      linkStateId  	     IP       	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_ad_router          ospfv2AsExternalLsa.Header      advertisingRouter    IP        	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_seq_number         ospfv2AsExternalLsa.Header      lsSequenceNumber     HEX  	  	    7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}        
        {ospf_asexternal_lsa_network_mask       ospfv2AsExternalLsa             networkMask  	     IP                     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_route_metric       ospfv2AsExternalLsa             externalRouteMetric  NUMERIC                7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_forwarding_addr    ospfv2AsExternalLsa             forwardingAddress    IP                     7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_route_tag          ospfv2AsExternalLsa             externalRouteTag     NUMERIC                7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_option_ebit        externalLsaOptions              eBit  	             {CHOICES 0 1}          7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_option_reserved    externalLsaOptions              reserved  	     NUMERIC                7	  _none_	_none_	  {update}		false	  _none_	  _none_       _none_}
   }
    
    
    {   traffic_config_ospf_update_router_lsa_link
        {hname                               stcobj                     stcattr                   type          priority  default       range     dependency                 mandatory   procfunc            mode      constants                                                                                           constants}
        {mode                               _none_                      _none_      {CHOICES create modify delete}  1     _none_        _none_    _none_                        true      _none_            _none_      _none_} 
        {stream_id	                    _none_	                _none_	                   ALPHANUM  	    2	  _none_	_none_	  _none_	                true	  _none_	    _none_      _none_}	
        {handle                             _none_                      _none_                     ANY              2     _none_        _none_    _none_                        false     _none_            _none_      _none_}
        {phandle                            _none_                      _none_                     ANY              2     _none_        _none_    _none_                        false     _none_            _none_      _none_}
        {type	                            _none_	                _none_	                   ANY 	  	    1	  _none_	_none_	  _none_		        true	  _none_	    _none_      _none_}
        {ospf_router_lsa_link_num           _none_                    _none_      	           NUMERIC	    3	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_link_id            Ospfv2RouterLsaLink       linkId  	                   IP               4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_link_data          Ospfv2RouterLsaLink       linkData  	           IP               4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_link_type          Ospfv2RouterLsaLink       routerLsaLinkType  	   NUMERIC          4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_tos_metric_num     Ospfv2RouterLsaLink       numRouterLsaTosMetrics  	   NUMERIC          4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_link_metric        Ospfv2RouterLsaLink       routerLinkMetrics  	   NUMERIC          4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
    }
    
   {   traffic_config_ospf_update_router_lsa_tos
        {hname                               stcobj                     stcattr                     type        priority  default       range     dependency                 mandatory   procfunc            mode      constants                                                                                           constants}
        {mode                               _none_                      _none_       {CHOICES create modify delete} 1     _none_        _none_    _none_                        true      _none_            _none_      _none_} 
        {handle                             _none_                      _none_                      ANY             2     _none_        _none_    _none_                        false     _none_            _none_      _none_}
        {phandle                            _none_                      _none_                      ANY             2     _none_        _none_    _none_                        false     _none_            _none_      _none_}
        {stream_id	                    _none_	                _none_	                    ALPHANUM  	    2	  _none_	_none_	  _none_	                true	  _none_	    _none_      _none_}	
        {type	                            _none_	                _none_	                    ANY 	    1	  _none_	_none_	  _none_		        true	  _none_	    _none_      _none_}
        {ospf_router_lsa_tos_num            _none_                    _none_      	            NUMERIC	    3	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_tos_type           Ospfv2RouterLsaTosMetric  routerLsaLinkType  	    NUMERIC         4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_tos_reserved       Ospfv2RouterLsaTosMetric  routerLsaMetricReserved  	    NUMERIC         4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
        {ospf_router_lsa_tos_metric         Ospfv2RouterLsaTosMetric  routerTosLinkMetrics  	    NUMERIC         4	  _none_	_none_	  _none_		        false	  _none_	    _none_      _none_}
    }
    
    
    {   traffic_config_ospf_update_summary_lsa_tos
        {hname                               stcobj                     stcattr                         type        priority      default       range     dependency                 mandatory   procfunc         mode      constants                                                                                           constants}
        {mode                                _none_                      _none_         {CHOICES create modify delete}  1         _none_        _none_    _none_                        true      _none_          _none_       _none_} 
        {handle                              _none_                      _none_                         ANY             2         _none_        _none_    _none_                        false     _none_          _none_       _none_}
        {phandle                             _none_                      _none_                         ANY             2         _none_        _none_    _none_                        false     _none_          _none_       _none_}
        {stream_id	                     _none_	                _none_	                        ALPHANUM  	2	  _none_	_none_	  _none_	                true	  _none_	    _none_      _none_}	
        {type	                             _none_	                 _none_	                        ANY 	  	1	  _none_	_none_	  _none_		        true	  _none_	  _none_       _none_}
        {ospf_summary_lsa_tos_num            _none_                      _none_      	                NUMERIC	  	3	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_tos_reserved       Ospfv2SummaryLsaTosMetric  summaryLsaMetricReserved        NUMERIC         4	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_summary_lsa_tos_metric         Ospfv2SummaryLsaTosMetric  routerTosLinkMetrics  	        NUMERIC         4	  _none_	_none_	  _none_		        false	  _none_	  _none_       _none_}
    }
    
  {   traffic_config_ospf_update_asexternal_lsa_tos
        {hname                                  stcobj                  stcattr                         type         priority    default       range     dependency                 mandatory   procfunc           mode      constants                                                                                          constants}
        {mode                                   _none_                  _none_         {CHOICES create modify delete}    1       _none_        _none_     _none_                        true      _none_          _none_       _none_}  
        {handle                                 _none_                  _none_                          ANY              2       _none_        _none_     _none_                        false     _none_          _none_       _none_} 
        {phandle                                _none_                  _none_                          ANY              2       _none_        _none_     _none_                        false     _none_          _none_       _none_} 
        {stream_id	                        _none_	                _none_	                        ALPHANUM  	 2	  _none_	_none_	  _none_	                true	  _none_	    _none_      _none_}	
        {type	                                _none_	                _none_	                        ANY 	  	 1	 _none_	       _none_	  _none_		        true	  _none_	  _none_       _none_} 
        {ospf_asexternal_lsa_tos_num            _none_                  _none_      	                NUMERIC	  	 3	 _none_	       _none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_tos_ebit           Ospfv2ExternalLsaTosMetric    eBit  	                {CHOICES 0 1}    4	 _none_        _none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_tos_type           Ospfv2ExternalLsaTosMetric    externalLsaRouteTos       NUMERIC          4	 _none_	       _none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_tos_metric         Ospfv2ExternalLsaTosMetric    externalLsaRouteMetrics   NUMERIC          4	 _none_	       _none_	  _none_		        false	  _none_	  _none_       _none_}
        {ospf_asexternal_lsa_tos_forwarding_addr Ospfv2ExternalLsaTosMetric   forwardingAddress         IP               4	 _none_	       _none_	  _none_		        false	  _none_	  _none_       _none_}
    }
}
