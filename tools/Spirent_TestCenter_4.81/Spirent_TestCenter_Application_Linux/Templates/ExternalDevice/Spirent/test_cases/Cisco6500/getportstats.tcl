
proc parsePortStats { portStatsInfo portlist } {

    set portstatisticList {}  
    set list portstatslist
    set portListInfo [ split $portlist | ]
    foreach port $portListInfo {
      set expression  {spirentport(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n(.*?)\n?}
      regsub {spirentport} $expression "$port" changedExp
      regexp $changedExp $portStatsInfo dummary d1 d2 d3 d4 d5 TotalRow d7 
      if { [info exists TotalRow] } {
          regexp {Total\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)} $TotalRow  dummary in_pkt in_char out_pkt out_char
          if {![info exists in_pkt ] } {
            lappend portstatisticList  0 0 0 0    
          } else {
            lappend portstatisticList  $in_pkt $in_char $out_pkt $out_char
            unset in_pkt
            unset in_char
            unset out_pkt
            unset out_char
        }
     }
  }

 return $portstatisticList

}