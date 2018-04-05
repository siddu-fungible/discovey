namespace eval ::sth::hunderdGig:: {
    
}
set ::sth::hunderdGig::hunderdGigTable {
 ::sth::hunderdGig::
  { pcs_error_config
    {hname                      stcobj                          stcattr             type                                                priority    default         range       supported    dependency     mandatory       procfunc     mode       constants   }
    {port_handle                _none_                          _none_              ANY                                                 2           _none_          _none_      true        _none_          true           _none_      _none_      _none_      }
    {burst_count                PcsErrorInsertionConfig         BurstCount          NUMERIC                                             2           1               _none_      true         _none_         FALSE           _none_      _none_     _none_       }
    {burst_interval             PcsErrorInsertionConfig         BurstInterval       NUMERIC                                             2           1               _none_      true         _none_         FALSE           _none_      _none_     _none_       }
    {burst_length               PcsErrorInsertionConfig         BurstLength         NUMERIC                                             2           1               _none_      true         _none_         FALSE           _none_      _none_     _none_       }
    {continuous_mode            PcsErrorInsertionConfig         ContinuousMode      {CHOICES true false}                                2           true            _none_      true         _none_         FALSE          _none_      _none_     _none_       }
    {error_insertion_mode       PcsErrorInsertionConfig         ErrorInsertionMode  {CHOICES LANE_MARKERS_ONLY LANE_MARKERS_AND_PAYLOAD} 2      LANE_MARKERS_ONLY   _none_      true         _none_         FALSE          _none_      _none_     _none_       }
    {lane_enable                PcsErrorInsertionConfig         LaneEnable          ANY                                2           _none_           _none_      true         _none_         FALSE          _none_      _none_     _none_       }
    {sync_header                PcsErrorInsertionConfig         SyncHeader          NUMERIC                                             2           0               0-3         true         _none_         FALSE          _none_      _none_     _none_       }
    {marker0                    PcsErrorInsertionConfig         Marker0             NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {marker1                    PcsErrorInsertionConfig         Marker1             NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {marker2                    PcsErrorInsertionConfig         Marker2             NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {bip3                       PcsErrorInsertionConfig         Bip3                NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {marker4                    PcsErrorInsertionConfig         Marker4             NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {marker5                    PcsErrorInsertionConfig         Marker5             NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {marker6                    PcsErrorInsertionConfig         Marker6             NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    {bip7                       PcsErrorInsertionConfig         Bip7                NUMERIC                                             2           0               0-255         true         _none_         FALSE          _none_      _none_     _none_       }
    }
  { pcs_error_control
    {hname                      stcobj                          stcattr             type                                                priority    default         range       supported   dependency     mandatory       procfunc     mode       constants   }
    {port_handle                _none_                          _none_              ANY                                                 2           _none_          _none_      true        _none_          true           _none_      _none_      _none_      }
    {action                     _none_                          _none_              {CHOICES start stop}                                2           _none_          _none_      true        _none_          true           _none_      _none_      _none_      }
  }
  { random_error_config
    {hname                      stcobj                          stcattr             type                                                priority    default         range       supported   dependency     mandatory       procfunc     mode       constants   }
    {port_handle                _none_                          _none_              ANY                                                 2           _none_          _none_      true        _none_          true           _none_      _none_      _none_      }
    {lane_enable                RandomErrorInsertionConfig      LaneEnable          ANY                                                 2           false           _none_      true        _none_          FALSE          _none_      _none_     _none_       }
    {rate                       RandomErrorInsertionConfig      Rate                ANY                                                 2       0.000000001 0.00000000001-0.1 true        _none_          FALSE          _none_      _none_     _none_       }
  }
  { random_error_control
    {hname                      stcobj                          stcattr             type                                                priority    default         range       supported   dependency     mandatory       procfunc     mode       constants   }
    {port_handle                _none_                          _none_              ANY                                                 2           _none_          _none_      true        _none_          true           _none_      _none_      _none_      }
    {action                     _none_                          _none_              {CHOICES start stop}                                2           _none_          _none_      true        _none_          true           _none_      _none_      _none_      }
  }
  { forty_hundred_gig_l1_results
    {hname                      stcobj                          stcattr             type                                                priority    default         range       supported   dependency     mandatory       procfunc     mode       constants   }
    {port_handle                _none_                          _none_              ANY                                                 2           _none_          _none_      true        _none_          FALSE           _none_      _none_      _none_      }
    {type                       _none_                          _none_              {CHOICES pcs pcs_lane pma_lane}                     2           pcs             _none_      true        _none_          false           _none_      _none_      _none_      }
    {mode                       _none_                          _none_              {CHOICES port lanes all}                             2           port             _none_      true        _none_          false           _none_      _none_      _none_      }
  }
}