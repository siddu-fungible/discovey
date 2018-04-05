
proc parseAllPorts { allPortsInfo   } {

set portlist {} 

if { [ string length $allPortsInfo ] > 0 } {
   foreach line [split $allPortsInfo \n] {
   regexp {^(\w+(-WAN)?\d+/\d+(/\d+)?)\s+([^\r\n]+)\s+(\w+)\s+\w+\s+$} $line dummary port dummary2 dummary3 dummary4 status
   if {![info exists status ] } {
       continue
    }
    if { [ info exists port ] } {
    set portList($port) $status
    }
    unset port
    unset status
   }
 }
 set portlist [array get portList]
 return $portlist

}