namespace eval ::sth::alarms {
    set alarmsTable {
        ::sth::alarms::
        {alarms_control
            {hname          stcobj      stcattr     type                                                            priority   default      range     supported       dependency      mandatory       procfunc      mode        constants}
            {port_handle    _none_      _none_      ANY                                                              1          _none_      _none_      true            _none_          true            _none_      _none_          _none_}
            {alarm_type     _none_      _none_      {CHOICES line_ais line_bip24 line_bip96 line_bip384 line_rdi line_rei \
                                                    path_ais path_bip8 path_rdi path_rei sec_bip8 unequip}              2       _none_      _none_      true            _none_          false           _none_      _none_          _none_}
            {count          _none_      _none_      NUMERIC                                                             3       5           _none_      true            _none_          false           _none_      _none_          _none_}
            {interval       _none_      _none_      NUMERIC                                                             4       30          _none_      true            _none_          false           _none_      _none_          _none_}
            {state          _none_      _none_      {CHOICES 0 1}                                                       5       0           _none_      true            _none_          false           _none_      _none_          _none_}
            {mode           _none_      _none_      {CHOICES momentary continuous}                                      6       momentary   _none_      true            _none_          false           _none_      _none_          _none_}
            {reset          _none_      _none_      {CHOICES 0 1}                                                       7       _none_      _none_      true            _none_          false           _none_      _none_          _none_}
        }
        {alarms_stats
            {hname              stcobj              stcattr         type           priority   default      range     supported       dependency      mandatory       procfunc      mode        constants}
            {port_handle        _none_              _none_          ANY             1           _none_      _none_      true        _none_              true            _none_      _none_      _none_}
            {hdlc_abort_count   SonetResults        AbortCount      NUMERIC         2           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {hdlc_drop_count    SonetResults        DropCount       NUMERIC         3           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {b1_error_count     SonetResults        SectionCount    NUMERIC         4           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {b2_error_count     SonetResults        LineCount       NUMERIC         5           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {reil_count         SonetResults        REILCount       NUMERIC         6           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {b3_error_count     SonetResults        PathCount       NUMERIC         7           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {reip_count         SonetResults        REIPCount       NUMERIC         8           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {hdlc_abort_rate    SonetResults        AbortRate       NUMERIC         9           _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {hdlc_drop_rate     SonetResults        DropRate        NUMERIC         10          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {b1_error_rate      SonetResults        SectionRate     NUMERIC         11          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {b2_error_rate      SonetResults        LineRate        NUMERIC         12          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {reil_rate          SonetResults        REILRate        NUMERIC         13          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {b3_error_rate      SonetResults        PathRate        NUMERIC         14          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {reip_rate          SonetResults        REIPRate        NUMERIC         15          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
            {active_alarms      SonetAlarmsResults  _none_          ANY             16          _none_      _none_      true        _none_              false           _none_      _none_      _none_}
        }
    }
}