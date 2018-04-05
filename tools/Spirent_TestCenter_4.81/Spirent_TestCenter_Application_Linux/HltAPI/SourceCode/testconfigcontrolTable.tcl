# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::testconfigcontrol:: {
    
}

set ::sth::testconfigcontrol::testconfigcontrolTable {
    ::sth::testconfigcontrol::
    { test_config
        {hname          stcobj        stcattr      type        priority   default           range       supported  procFunc                  dependency mandatory  mode          constants    }
        {logfile        _none_        _none_       ANY              2          log          _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {log            _none_        _none_       {CHOICES 0 1}    4          0            _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {hltlogfile     _none_        _none_       ANY              10         hltlog       _none_       true    ::testconfig::procTestConfigArg  _none_     false      _none_          _none_ }
        {hltlog         _none_        _none_       {CHOICES 0 1}    12         0            _none_       true    ::testconfig::procTestConfigArg  _none_     false      _none_          _none_ }
        {showStcCmd     _none_        _none_       {CHOICES 0 1}    13         0            _none_       true    ::testconfig::procTestConfigArg  _none_     false      _none_          _none_ }
        {showSthCmd     _none_        _none_       {CHOICES 0 1}    14         0            _none_       true    ::testconfig::procTestConfigArg  _none_     false      _none_          _none_ }
        {vendorlogfile  _none_        _none_       ANY              16         vendorlog    _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {vendorlog      _none_        _none_       {CHOICES 0 1}    18         0            _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {hlt2stcmapping _none_        _none_       {CHOICES 0 1}    20         0            _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {hlt2stcmappingfile  _none_   _none_       ANY              22        hlt2stcmapping _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {log_level      _none_        _none_       {CHOICES 0 1 2 3 4 5 6 7}  24   0         _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
        {custom_path     _none_        _none_       ANY  24   _none_         _none_       true    ::testconfig::procTestConfigArg  _none_     false     _none_          _none_ }
    }
    { test_control
        {hname                      stcobj         stcattr        type                         priority      default           range         supported      procFunc                                        dependency mandatory  mode          constants    }
        {parser                     _none_         _none_     {CHOICES cisco spirent}           1           cisco             _none_          true       ::sth::testconfigcontrol::processTestControlAction  _none_     false     _none_          _none_ }
        {action                     _none_         _none_     {CHOICES enable disable sync}     1           disable           _none_          true       ::sth::testconfigcontrol::processTestControlAction  _none_     false     _none_          _none_ }
        {UseModifier4TrafficBinding _none_         _none_        NUMERIC                        1           1                 _none_          true       ::sth::testconfigcontrol::processTestControlAction  _none_     false     _none_          _none_ }

    }
}
