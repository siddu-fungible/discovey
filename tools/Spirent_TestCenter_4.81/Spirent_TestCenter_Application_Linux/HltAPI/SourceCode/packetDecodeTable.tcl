namespace eval ::sth::packetDecode:: {
}

set ::sth::packetDecode::packetDecodeTable {
 ::sth::packetDecode::
 { packet_decode
    {hname                          stcobj              stcattr                       type                         priority    default      range           supported   dependency                  mandatory    procfunc                mode                                   constants}
    {port_handle                    _none_              _none_                      ALPHANUM                        1           _none_      _none_            true        _none_                      false       _none_                 _none_                                 _none_}
    {open_captured_file             _none_              _none_                        ANY                           1           _none_      _none_            true        _none_                      false       _none_                 _none_                                 _none_}
    {frame_decode_type              _none_              _none_  {CHOICES contents l2encap hdr_fields test_payload}  2          contents     _none_            true        _none_                      false       _none_                 _none_                                 _none_}
    {header_field_types             _none_              _none_                        ANY                           3           _none_      _none_            true        _none_                      false       _none_                 _none_                                 _none_} 
    {protocol_field                 _none_              _none_                        ANY                           3           _none_      _none_            true        _none_                      false       _none_                 _none_                                 _none_} 
 }
}
    
    
