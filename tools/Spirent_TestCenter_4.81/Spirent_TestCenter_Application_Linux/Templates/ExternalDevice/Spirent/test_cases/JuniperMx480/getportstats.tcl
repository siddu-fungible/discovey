
proc parsePortStats { portStatsInfo portlist } {

 set portstatisticList {}
 if { [string length $portStatsInfo ] > 0 } {
  set portstatisticList $portStatsInfo
 }
 return $portstatisticList

}