proc parseAllPorts { allPortsInfo   } {

set portlist {} 

if { [ string length $allPortsInfo ] > 0 } {
   foreach line [split $allPortsInfo \n] {
   regexp {^(\w+(-)?(\d)?(/\d+/\d+)?)\s+\w+\s+(\w+)(.*)$} $line dummary port dum1 dum2 dum3 status 
   if {![info exists status ] } {
       continue
    }
    if { ($status != "up") && ($status != "down") } {
       continue
    }
    if { [ info exists port ] && ($port!= "lo0")&& ($port!= "demux0") && ($port!= "tap") && ($port!= "dsc") && ($port!= "gre") && ($port!= "ipip")&& ($port!= "mtun") && ($port!= "pimd")&& ($port!= "pime")&& ($port!= "lsi") } {
    lappend portlist $port $status
    }
    unset port
    unset status
   }
 }
return $portlist

}