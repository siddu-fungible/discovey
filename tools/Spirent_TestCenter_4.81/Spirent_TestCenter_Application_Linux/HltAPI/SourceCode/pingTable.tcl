# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Ping:: {}

set ::sth::Ping::pingTable {
 ::sth::Ping::
 {	emulation_ping
 	{hname                 stcobj      stcattr        type       priority		default	    range     supported    dependency    mandatory  procfunc                            mode	   constants    }
 	{port_handle           _none_	   _none_        ALPHANUM	1        	_none_      _none_      true         _none_        false    ::sth::Ping::procPingPort_Handle   	_none_     _none_       }
 	{handle                _none_	   _none_        ALPHANUM	1        	_none_      _none_      true         _none_        false    _none_   	                        _none_     _none_       }
	{host                  Host        Gateway       IP             1        	_none_      _none_      true         _none_        true     ::sth::Ping::procPingHost	  	_none_     _none_       }
	{count		       _none_      FrameCount    NUMERIC	3        	1           _none_      true         _none_        false    ::sth::Ping::procPingOptional  	_none_     _none_       }
	{size		       _none_      _none_        ANY		3        	_none_      _none_      false        _none_        false    _none_				_none_     _none_       } 	
	{interval	       _none_      TimeInterval  NUMERIC        3        	1           _none_      true         _none_        false    ::sth::Ping::procPingOptional	_none_     _none_       }
 	{pad	    	       _none_      _none_        ANY	        3       	_none_      _none_      false        _none_        false    _none_	                        _none_     _none_       }
 	{ttl		       _none_      _none_        ANY	        3       	_none_      _none_      false        _none_        false    _none_	                        _none_     _none_       }
 	{vci		       _none_      _none_        ANY	        3       	_none_      _none_      false        _none_        false    _none_	                        _none_     _none_       }
 	{vpi		       _none_      _none_        ANY	        3       	_none_      _none_      false        _none_        false    _none_	                        _none_     _none_       }
 	{vlan_id	       _none_      _none_        ANY	        3       	_none_      _none_      true         _none_        false    _none_	                        _none_     _none_       }
 }
 }
    
