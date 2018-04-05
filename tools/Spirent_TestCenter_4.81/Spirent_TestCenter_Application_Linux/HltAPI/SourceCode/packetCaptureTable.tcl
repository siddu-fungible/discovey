# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::packetCapture:: {

    set ::sth::packetCapture::PacketCaptureTable \
        [list \
             ::sth::packetCapture:: \
             [list packet_config_buffers \
                  [list hname \
                       stcobj  stcattr  type  \
                       priority  default  range  \
                       supported  dependency  mandatory  \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port	_none_   ALPHANUM \
                       1  _none_  _none_  \
                       true  _none_  true  \
                       _none_   _none_  _none_] \
                  [list action \
                       _none_  _none_  [list CHOICES wrap stop] \
                       2  _none_  _none_  \
                       true  _none_  true \
                       _none_  _none_  _none_]
             ] \
             [list packet_config_triggers \
                  [list hname \
                       stcobj  stcattr  type \
                       priority  default  range \
                       supported  dependency  mandatory \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port  _none_  ALPHANUM \
                       1  _none_  _none_ \
                       true _none_  true \
                       _none_  _none_  _none_] \
                  [list exec \
                       capture  _none_  [list CHOICES start stop] \
                       2  _none_  _none_ \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  [list action \
                       capture  _none_  [list CHOICES counter event] \
                       3  _none_  _none_ \
                       true  _none_  false \
                       _none_  _none_ _none_] \
                  [list mode \
                       capture _none_  [list CHOICES add remove] \
                       4  _none_  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list trigger \
                       _none_  _none_  ANY \
                       5  _none_  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                 ] \
             [list packet_config_filter \
                  [list hname \
                       stcobj  stcattr  type \
                       priority  default  range \
                       supported  dependency  mandatory \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port  _none_  ALPHANUM \
                       1  _none_  _none_ \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  [list mode \
                       capture  _none_  [list CHOICES add remove] \
                       4  _none_  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list filter \
                       _none_  _none_  ANY \
                       5  _none_  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                 ] \
             [list packet_config_pattern \
                  [list hname \
                       stcobj  stcattr  type \
                       priority  default  range \
                       supported  dependency  mandatory \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port  _none_  ALPHANUM \
                       1  _none_  _none_ \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  [list mode \
                       capture  _none_  [list CHOICES add reset custom] \
                       6  _none_  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list byte_mask \
                       CaptureBytePattern  mask  ANY\
                       6  255  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list byte_name \
                       CaptureBytePattern  name  ANY\
                       6  ""  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list byte_offset \
                       CaptureBytePattern  offset  NUMERIC \
                       6  0  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list byte_value \
                       CaptureBytePattern  value  ANY\
                       6  0  _none_  \
                       true  _none_  false  \
                        _none_  _none_  _none_] \
                  [list range_min \
                       CaptureRangePattern  min  NUMERIC\
                       6  0  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list range_max \
                       CaptureRangePattern  max  NUMERIC\
                       6  0  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list range_name \
                       CaptureRangePattern  name  ANY \
                       6  ""  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list filter_fcserror \
                       CaptureFilter  fcserror  [list CHOICES IGNORE INCLUDE EXCLUDE] \
                       6  IGNORE  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list filter_prbserror \
                       CaptureFilter  prbserror  [list CHOICES IGNORE INCLUDE EXCLUDE]\
                       6  IGNORE  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                   [list statistics_flag \
                       _none_  _none  [list CHOICES 0 1 true false] \
                       6  0  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list statistics_fcserror \
                       CaptureStatisticsFilter  fcserror  [list CHOICES IGNORE INCLUDE EXCLUDE] \
                       6  IGNORE  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list statistics_prbserror \
                       CaptureStatisticsFilter  prbserror  [list CHOICES IGNORE INCLUDE EXCLUDE] \
                       6  IGNORE  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list statistics_byte \
                       CapturePatternExpression  byteexpression  ANY \
                       6  ""  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list statistics_framelength \
                       CapturePatternExpression  framelengthexpression  ANY \
                       6  ""  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list filter_byte \
                       CapturePatternExpression  byteexpression  ANY \
                       6  ""  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list filter_framelength \
                       CapturePatternExpression  framelengthexpression  ANY \
                       6  ""  _none_  \
                       true  _none_  false  \
                       _none_  _none_  _none_] \
                  [list pattern_mask \
                       CaptureAnalyzerFilter  Mask  ANY \
                       5  FF  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list pattern_type \
                       CaptureAnalyzerFilter  FilterDescription  ANY \
                       5  ""  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list pattern_offset \
                       CaptureAnalyzerFilter  Offset  NUMERIC \
                       5  0  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list pattern_match \
                       CaptureAnalyzerFilter  Value  ANY \
                       5  00  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list operator \
                       CaptureAnalyzerFilter  RelationToNextFilter  [list CHOICES AND OR] \
                       5  AND  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                 ] \
             [list packet_control \
                  [list hname \
                       stcobj  stcattr  type \
                       priority  default  range \
                       supported  dependency  mandatory \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port  _none_  ALPHANUM \
                       1  _none_  _none_ \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  [list action \
                       capture  _none_  [list CHOICES start stop] \
                       2  _none_  _none_  \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  ] \
             [list packet_info \
                  [list hname \
                       stcobj  stcattr  type \
                       priority  default  range \
                       supported  dependency  mandatory \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port  _none_  ALPHANUM \
                       1  _none_  _none_ \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  [list action \
                       Capture  _none_  [list CHOICES status] \
                       2  _none_  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
              ] \
             [list packet_stats \
                  [list hname \
                       stcobj  stcattr  type \
                       priority  default  range \
                       supported  dependency  mandatory \
                       procfunc  mode  constants] \
                  [list port_handle \
                       port  _none_  ALPHANUM \
                       1  _none_  _none_ \
                       true  _none_  true \
                       _none_  _none_  _none_] \
                  [list action \
                       Capture  _none_  [list CHOICES filtered all] \
                       2  filtered  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list stop \
                       _none_  _none_  FLAG \
                       3  1  _none_ \
                       true  _none_  false \
                       _none_  _none_  _none_] \
                  [list format \
                       CaptureDataSaveCommand FilenameFormat [list CHOICES var txt pcap enc none] \
                       4  _none_  _none_ \
                       true  _none_  false \
                       _none_ _none_ _none_] \
                  [list var_num_frames \
                       _none_ _none_ NUMERIC \
                       6  20  _none_ \
                       true  {format var}  false \
                       _none_ _none_ _none_] \
                  [list filename \
                       CaptureDataSave  _none_  ANY \
                       5  _none_ _none_ \
                       true _none_ false \
                       _none_  _none_ _none_] \
                  ] \
            ]
}