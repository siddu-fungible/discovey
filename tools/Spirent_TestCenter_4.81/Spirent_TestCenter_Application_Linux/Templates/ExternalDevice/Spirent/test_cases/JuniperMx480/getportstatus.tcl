
proc parsePortStatus { {allPortsInfo ""} portlist } {

set statuslist {} 
if { [string length $portlist ] <= 0 } {
   return 2
}
if { [ string length $allPortsInfo ] > 0 } {
   foreach line [split $allPortsInfo \n] {
   
   regexp {^(\w+(-)?(\d)?(/\d+/\d+)?)\s+\w+\s+(\w+)(.*)$} $line dummary port dum1 dum2 dum3 status 
   if {![info exists status ] } {
       continue
    }
    if { [ info exists port ] } {
     set portStatusArr($port) $status
    }
    unset port
    unset status
   }
 }
 set portsInfoList [split $portlist |]
 if { [array exists portStatusArr ] } {
   foreach port $portsInfoList {
     lappend statuslist $portStatusArr($port)
  } 
 } 
return $statuslist

}
