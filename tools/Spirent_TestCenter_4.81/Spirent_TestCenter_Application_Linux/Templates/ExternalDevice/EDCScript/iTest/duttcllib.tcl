#!/bin/sh
# -*- tcl -*-
# The next line is executed by /bin/sh, but not tcl \

package require tdom
package require itest

package provide edc 3.4

namespace eval edc {
      namespace export RunRecordedTestcase edcconnectWorkSpace  edctelnetConnectDUT  edcloadConfig edcwriteConfig \
                     edcreset  edcstopSession edcgetAllPorts edcgetPortStats\
                      edccustomizedCmd 
     
   variable workspacePath   
   variable savedtestcasePath
   variable edcLogLevel
   

}
proc edc::readXMLFile { FileName }  {

    if { [file exists $FileName] == 0 } {
     return "";
    }  
	  set fid [ open $FileName ] 
	  set context [ read $fid ] 
	  close $fid 
	 return $context 
	} 

proc edc::writeXMLFile {FileName data } {
	  set fid [ open $FileName w ]
    puts $fid $data
    close $fid 
}

proc edc::convertTestCaseFile { XML mainprocname  } {
upvar  $mainprocname procname

set regValue [ regsub -all {session=\"[^\r\n]+\"} $XML {session="$session"} changeSessionXML ]
if { $regValue == 0 } {
  set changeSessionXML $XML
} 

set doc [dom parse $changeSessionXML ]
set root [$doc documentElement ]
set list procnodelist 
set path "/testCase/procedures/item"
set procnodelist [ $root selectNodes $path ]
if { [llength $procnodelist ] == 1 } {
    set singlenode [lindex $procnodelist 0 ]
    set procname [ $singlenode getAttribute name ]
    updateStepNode $singlenode
  } else {
   for { set i 0 } { $i < [llength $procnodelist ] } { incr i } {
     set itemnode [lindex $procnodelist $i ] 
     
     if { [$itemnode hasAttribute description]} {
       
       set procname [ $itemnode getAttribute name ]
     } 
     updateStepNode $itemnode 
   }
 }
return [$root asXML]
}

proc edc::changeChildNode { node } {
 puts [ $node nodeName ]
 set iTemChildNode [ $node selectNodes item ]
 puts "1"
 if { $iTemChildNode != "" } {
       for { set i  0 }  { $i < [llength $iTemChildNode ] } { incr i } {
        set childItem [lindex $iTemChildNode $i ]
        puts [ $childItem nodeName ]
        if { [$childItem hasAttribute session ] } {
          $node setAttribute session "\$session"
        } else {
           set nestedChildNode [$childItem selectNodes nestedSteps ]
           if { $nestedChildNode != "" } {
            changeChildNode $nestedChildNode
          }
      }
    }
 }
}

proc edc::updateStepNode { node } {
    $node setAttribute defaultSessionType "com.fnfr.svt.applications.telnet"
    set parentnode [$node selectNodes steps ]
    set nodelist [ $parentnode selectNodes item ]
    for { set i  0 }  { $i < [llength $nodelist ] } { incr i} {
      set node [lindex $nodelist $i ]
      set opena [ $node getAttribute action ]
      if { ($opena == "open") ||($opena == "close" ) } {
        $parentnode removeChild $node
        continue
      } 
      #if { [$node hasAttribute session ] } {
        #$node setAttribute session "\$session"
        #continue
      #}
      #puts "---node value ----"
      #puts [$node nodeName ]
      #puts $i
      #set childnode [ $node selectNodes nestedSteps ]
      #if { $childnode != "" } {
        #puts "==== Begin to process recurse node ===="
        #changeChildNode $childnode  
      #}  
    }
}

proc edc::processTestCaseFile { session testcaseFile  entrypoint } {
   set path [ file dirname $testcaseFile ]
   set XML [edc::readXMLFile $testcaseFile ]
   if { [llength $XML ] == 0 } {
     return ""
   }
   
   variable mainprocname
   variable runtimefilename
   
   set content [ edc::convertTestCaseFile $XML mainprocname ]
   if { [info exists mainprocname] == 0 } {
      set mainprocname "main"
   }
   upvar $entrypoint procname
   set procname $mainprocname
   
   set temptime [clock seconds]
   set runtimefilename "[list $session]_[list $temptime].fftc"
   
   if { [file exists $path/$runtimefilename ] > 0 } {
      file delete $path/$runtimefilename
   } 
   edc::writeXMLFile $path/$runtimefilename $content
   return $path/$runtimefilename
}

proc edc::updateNodeValue {readFileName writeFileName args } {

    set XMLStruct [edc::readXMLFile $readFileName ]
    if { [string length $XMLStruct] == 0 } {
      return false;
    }

    set doc [dom parse $XMLStruct]
    set root [$doc documentElement ]
    for {set i 0} {$i < [llength $args]} {incr i} {
        set param [lindex $args $i]
        incr i
        set paramvalue [lindex $args $i] 
        set node [$root selectNode $param/text() ]
        $node nodeValue $paramvalue 
    }
    edc::writeXMLFile $writeFileName [$root asXML]
    return true
}

proc stdout { switch { file "" } } {
     if { ! [ llength [ info command __puts ] ] && \
            [ string equal off $switch ] } {
        rename puts __puts
        if { [ string length $file ] } {
           eval [ subst -nocommands {proc puts { args } {
              set fid [ open $file a+ ]
              if { [ llength \$args ] > 1 && \
                   [ lsearch \$args stdout ] == 0 } {
                 set args [ lreplace \$args 0 0 \$fid ]
              } elseif {  [ llength \$args ] == 1 } {
                 set args [ list \$fid \$args ]
              }
              if { [ catch {
                 eval __puts \$args
              } err ] } {
                 close \$fid
                 return -code error \$err
              }
              close \$fid
           }} ]
        } else {
           eval [ subst -nocommands {proc puts { args } {
              if { [ llength \$args ] > 1 && \
                   [ lsearch \$args stdout ] == 0 || \
                   [ llength \$args ] == 1 } {
                 # no-op
              } else {
                 eval __puts \$args
              }
           }} ]
        }
     } elseif { [ llength [ info command __puts ] ] && \
                [ string equal on $switch ] } {
        rename puts {}
        rename __puts puts
     }
 }

###############################################################################
#
# Brief: Run a recorded test file in its own workspace
#
# Description:
#     Run a testcase without using ExternalDeviceSession handle. It has the
#     similar function as iTestcli, but supercede it by returning response data.
#
# Parameter:
#     workspace:  iTest workspace path
#     testcase:   relative file under workspace
#
# Return:
#     EDC_Error_Info:xxx    error information
#     other:      formatted result data, just like other custom command's result
#
# Use case:
#    set response [ edc::RunRecordedTestcase "E:/iTest/workspace" \
#                       "my_project/test_cases/show_cca.fftc"]
#
###############################################################################
proc edc::RunRecordedTestcase { workspace testcase} {
    
    set testcaseUrl [itest::convertPathToURL $testcase ]
    
    stdout off

    itest::open -w $workspace ;# -d 3
    
    set cmd " itest::step call \"\" {project://$testcaseUrl#main} -storeResponse customizedValue"
    
    if {[ catch { eval $cmd } errmsg ]} {
        itest::close
        return "EDC_Error_Info: $errmsg "
    }
    set ret [itest::stepResultCode]
    #puts "resutcode is $ret"
    
    if { $ret == 0 } {
        set responseValue [itest::response customizedValue ]
        #puts $responseValue
        itest::close 
        if { [ string length $responseValue ] <= 0 } {
          set result " "
        }  else {
          set result [ edc::changeTable $responseValue ]
        }
        return $result
    } else {
        set errorInfo [  itest::stepIssues ]
        itest::close 
        return "EDC_Error_Info: $errorInfo"
    }
}

proc edc::edcconnectWorkSpace { workspace publicfolderPath {logLevel "1"} } {
#
#  Debug information
    set edc::edcLogLevel $logLevel
   
    if {[catch {
#    itest::open -w $workspace -d 3 -p $workspace/parameters.ffpt
     set edc::workspacePath $workspace
     set commonparameterfile "parameters.ffpt" 
     if { [file exists $workspace/$commonparameterfile ] == 0 } {
       file copy $publicfolderPath/$commonparameterfile $workspace/
     }
     itest::open -w $workspace -i 1
    } errmsg]} {
      return "connect itest workspace."
    }
    return 0
}

#
#This functions intions to set XML parameters
#Before opening workspace, make these parameter work
#
# 
proc edc::edcSetParams { duthost port username passwd } {
 variable paramXMLTemplate
 
 set paramXMLTemplate "
     <parameters>
            <dut>
                <ip_address>$duthost</ip_address>
                <port>$port</port>
            </dut>
            <connect>
                <username>$username</username>
                <password>$passwd</password>
            </connect>
    </parameters>
  "
  itest::paramSet $paramXMLTemplate 
}

#telnetConnectDUT
 
#connectedSession,
#testcaseFile,
#DUThost,
#port,
#username,
#password
#

proc  edc::edctelnetConnectDUT { session sessionprofile testcaseFile duthost port {username ""} {passwd ""} {privilegedpasswd ""} } {

  if { [ expr $edc::edcLogLevel < 1 ] } {
   stdout off
  } else {
   stdout off [list $edc::workspacePath/itest.log ]
  }
   if { [file exists $sessionprofile] == 0 } {
     return "EDC_Error_Info: session profile does not exist.";
    }  
   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  

    variable stepstr;
    edc::edcSetParams $duthost $port $username  $passwd 
    set testcaseStr [itest::convertPathToURL $testcaseFile ]
    set sessionprofile [itest::convertPathToURL $sessionprofile ]
    itest::close 
#    itest::open -w $edc::workspacePath -p $sessionparameters 
    itest::open -w $edc::workspacePath  -i 1
    if { [string length $username] == 0 } {
      set username "\"\""
    }
    if { [string length $passwd] == 0 } {
      set passwd "\"\""
    }
    if { [ string length $privilegedpasswd] == 0 } {
      set privilegedpasswd "\"\""
    }
    if { [ string length $privilegedpasswd ] } {
     set stepstr " itest::step call \"\" {$testcaseStr#main -session $session -session_profile $sessionprofile -username $username -password $passwd -privilegedpasswd $privilegedpasswd} "
    } else {
     set stepstr " itest::step call \"\" {$testcaseStr#main -session $session -session_profile $sessionprofile -username $username -password $passwd} "
    }

    if {[ catch {     
    eval $stepstr
    } errmsg ]} {
    itest::close
      return "EDC_Error_Info: Login invalid or fails to run test case "
    }
    if { [itest::stepResultCode] == 2 } {
     set errorInfo [  itest::stepIssues ]
     itest::close 
     return "EDC_Error_Info: Login invalid $errorInfo"
    } else {
     return [itest::stepResultCode]
    }
}


proc  edc::edcSSHConnectDUT { session sessionprofile testcaseFile duthost port {username ""} {passwd ""} {privilegedpasswd ""}}  {


   if { [file exists $sessionprofile] == 0 } {
     return "EDC_Error_Info: session profile does not exist.";
    }  
   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  

   variable workspacePath
   if { [ expr $edc::edcLogLevel < 1 ] } {
    stdout off
   } else {
    stdout off [list $edc::workspacePath/itest.log ]
   } 
   
    variable stepstr;

    edc::edcSetParams $duthost $port $username  $passwd
    set testcaseStr [itest::convertPathToURL $testcaseFile ]
    set sessionprofile [itest::convertPathToURL $sessionprofile ]

    itest::close
#    itest::open -w $edc::workspacePath -p $sessionparameters 
    itest::open -w $edc::workspacePath  -i 1

    if { [ string length $privilegedpasswd ] } {
     set stepstr " itest::step call \"\" {$testcaseStr#main -session $session -session_profile $sessionprofile -privilegedpasswd $privilegedpasswd} "
    } else {
     set stepstr " itest::step call \"\" {$testcaseStr#main -session $session -session_profile $sessionprofile } "
    }

    if {[ catch {     
    eval $stepstr
    } errmsg ]} {
      itest::close
      return "EDC_Error_Info:  Tcl Interperter fails to run test case."
    }
    if { [itest::stepResultCode] == 2 } {
     set errorInfo [  itest::stepIssues ]
     itest::close
     return "EDC_Error_Info: $errorInfo"
    } else {
     return [itest::stepResultCode]
    }
}

#===============================================================================
# PROCEDURE: edc::reConnect
# AUTHOR: Spirent
# UPDATED: Spirent
# PARAMETERS:
#          Input Parameters:
#                 @session: sessionID
#                 @sessionprofile: 
#                 @testcaseFile
#                 @duthost
#                 @port
#                 @username
#                 @passwd
#                 @privilegedpasswd
#          Output Parameters:
#                 reture procedure run status: error infomation or status code
# WHAT THE PROCEDURE DOES:
#          If the session connect status is stop, it'll be invoked instead connect session procedure
#===============================================================================
proc edc::reConnect { session sessionprofile testcaseFile duthost port {username ""} {passwd ""} {privilegedpasswd ""} } {
    variable stepstr;
    variable result;
    
    if { [file exists $sessionprofile] == 0 } {
     return "EDC_Error_Info: session profile does not exist.";
    }  
   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  

    edc::edcSetParams $duthost $port $username  $passwd
    set testcaseStr [itest::convertPathToURL $testcaseFile ]
    set sessionprofileStr [itest::convertPathToURL $sessionprofile ]
#    set sessionparameters "$edc::workspacePath/[list $session]_parameters.ffpt"
    
#    if { [file exists $sessionparameters ] } {
      
#      itest::open -w $edc::workspacePath -p $sessionparameters 
      itest::open -w $edc::workspacePath -i 1
      if { [string length $username] == 0 } {
        set username "\"\""
      }
      if { [string length $passwd] == 0 } {
        set passwd "\"\""
     }
      if { [ string length $privilegedpasswd] == 0 } {
        set privilegedpasswd "\"\""
     }
      if { [ string length $privilegedpasswd ] } {
       set stepstr " itest::step call \"\" {$testcaseStr#main -session $session -session_profile $sessionprofileStr  -username $username -password $passwd -privilegedpasswd $privilegedpasswd} "
      } else {
       set stepstr " itest::step call \"\" {$testcaseStr#main -session $session  -session_profile $sessionprofileStr -username $username -password $passwd} "
      }
     if {[ catch {   
#    itest::step close $session  
     eval $stepstr
     } errmsg ]} {
     itest::close
     return "EDC_Error_Info:  Tcl Interperter fails to run test case."
    }
    if { [itest::stepResultCode] == 2 } {
     set errorInfo [  itest::stepIssues ]
     itest::close
     return "EDC_Error_Info: $errorInfo"
    } else {
     return [itest::stepResultCode]
    }
#   } else {
#     if { [ regexp {.*telnetconnection.*} $testcaseFile dummary d1 ] == 1 } {
#       set result [ edc::edctelnetConnectDUT $session $sessionprofile $testcaseFile $duthost $port $username $passwd $privilegedpasswd ]
#     } else {
#       set result [ edc::edcSSHConnectDUT $session $sessionprofile $testcaseFile $duthost $port $username $passwd $privilegedpasswd ]
#     
#     }
#     return $result  
#   } 
}

#loadConfig,
#session,
#testcaseFile,
#sourcename,
#destname
proc edc::edcloadConfig { session testcaseFile sourcename destname  tftpServer {privilegedpasswd ""} } {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable stepstr;
    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }
    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    if { [ string length $privilegedpasswd] } {
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -host $tftpServer -file $sourcename -backupcfg $destname -privilegedpasswd $privilegedpasswd} "
    } else {
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -host $tftpServer -file $sourcename -backupcfg $destname} "
    }
    
    if { [catch {
      eval $stepstr 
      } errmsg ] } {
       return "EDC_Error_Info: LoadConfig command needs privileged password or fails to run test case file"
      }
    if { [file exists $runtestcaseFile ] == 1 } {
     file delete $runtestcaseFile
    }
    if { [itest::stepResultCode] == 2 } {
     set errorInfo [  itest::stepIssues ]
     return "EDC_Error_Info: LoadConfig command fails, wrong privileged password or transitation protocol is blocked by fireewall, $errorInfo"
    } else {
     return [itest::stepResultCode]
    }
}

#writeConfig
#session
#testcaseFile,
#sourcename,
#destname
proc edc::edcwriteConfig {session testcaseFile sourcename destname tftpServer {privilegedpasswd ""} } {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable stepstr;
    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }
    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    if { [ string length $privilegedpasswd ] } {
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -host $tftpServer -file $destname -backupcfg $sourcename -privilegedpasswd $privilegedpasswd } "
    } else {
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -host $tftpServer -file $destname -backupcfg $sourcename} "
    }
    if { [catch {
     eval $stepstr
      } errmsg ] } {
       return "EDC_Error_Info: WriteConfig command needs privileged password or fails to run test case file "
      }
    if { [file exists $runtestcaseFile ] == 1 } {
     file delete $runtestcaseFile
    }
    if { [itest::stepResultCode] == 2 } {
     set errorInfo [  itest::stepIssues ]
     return "EDC_Error_Info: WriteConfig command fails, wrong privileged password, or transmitation protocol is blocked by firewall,$errorInfo"
    } else {
     return [itest::stepResultCode]
    }

}

#reset,
#session,
#testcaseFile
proc edc::edcreset { session testcaseFile {privilegedpasswd ""} } {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable stepstr;
    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }
    
    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    if { [string length $privilegedpasswd] } {
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -privilegedpasswd $privilegedpasswd} -storeResponse resetResult   "
    } else {
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session} -storeResponse resetResult   "
    }
    
    if { [catch {
     eval $stepstr
      } errmsg ] } {
       return "EDC_Error_Info:  wrong priviledge password or fails to reset."
      }
    if { [file exists $runtestcaseFile ] == 1 } {
     file delete $runtestcaseFile
    }
    if { [itest::stepResultCode] == 2 } {
     set errorResult [itest::response resetResult ]
     set errorInfo [  itest::stepIssues ]
     return "EDC_Error_Info: wrong priviledge password or fails to reset, $errorInfo"
    } else {
     return [itest::stepResultCode]
    }

}

#stopSession,
#session,
#testcaseFile
proc edc::edcstopSession { session testcaeFile } {
    
#     variable result 
     
#     itest::step close $session
#     set result [ edc::edcstopWorkSpace $session $testcaeFile ]
#     if { $result == 2 } {
#     set errorInfo [  itest::stepIssues ]
#     return "EDC_Error_Info: $errorInfo"
#    } else {
#     return [itest::stepResultCode]
#    }
     edc::edcstopWorkSpace $session $testcaeFile
     return 0
}


#stopSession,
#session,
#testcaseFile
proc edc::edcstopWorkSpace { session testcaeFile } {
     itest::close
    if { [itest::stepResultCode] == 2 } {
     set errorInfo [  itest::stepIssues ]
     return "EDC_Error_Info: $errorInfo"
    } else {
     return [itest::stepResultCode]
    }
}

#getAllPorts,
#session,
#testcaseFile
proc edc::edcgetAllPorts { session testcaseFile } {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable stepstr;
    variable allportlist;
    variable portandratelist
    variable allportInfo
    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }
   
    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session} -storeResponse allports "
    if { [catch {
      eval $stepstr
      set allportInfo [itest::response allports] 
      } errmsg ] } {
       return "EDC_Error_Info:  Tcl Interperter fails to run test case."
      }
      if { [itest::stepResultCode ] != 0 } {
       set errorInfo [  itest::stepIssues ]
       return "EDC_Error_Info: $errorInfo"
      }
    set path [ file dirname $testcaseFile ]
    set parserFile $path/getallports.tcl
    if {[ file exists $parserFile ]  } {
     source $parserFile
     set allportlist [ parseAllPorts $allportInfo ]
    } else {
     set allportlist $allportInfo
    }
    if { [file exists $runtestcaseFile ] == 1 } {
     file delete $runtestcaseFile
    }
    
    return $allportlist
}

#getPortStats,
#session,
#testcaseFile,
#portlist
#this test case includes 6 procedures
# one Pkt_in
# two pkt_out
# three byte_in
# four byte_out
# five status
# six  speed

proc edc::edcgetPortStats { session testcaseFile portlist  } {
   
   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable stepstr;
    variable portstatisticStr
    variable  portstatisticList

    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }

    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -portlist $portlist } -storeResponse portstatsvalue "
    if { [catch {
     eval $stepstr
      } errmsg ] } {
       return "EDC_Error_Info:  Tcl Interperter fails to run test case."
      }
    if { [itest::stepResultCode ] != 0 } {
       set errorInfo [  itest::stepIssues ]
       return "EDC_Error_Info: $errorInfo"
     }
    set portstatisticStr [itest::response portstatsvalue]   
    set path [ file dirname $testcaseFile ]
    set parserFile $path/getportstats.tcl
    if {[ file exists $parserFile ]  } {
     source $parserFile
     set allportlist [ parsePortStats $portstatisticStr $portlist ]
    } else {
     set allportlist $portstatisticStr
    }
    if { [file exists $runtestcaseFile ] == 1 } {
      file delete $runtestcaseFile
     }
    return $allportlist    
}


proc edc::edcgetPortStatus { session testcaseFile portlist  } {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable portstr;
    variable portstatusStr 
    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }
    set  portstatusStr ""
    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    set portstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -portlist $portlist } -storeResponse portstatusvalue "
    if { [catch {
       eval $portstr
      } errmsg ] } {
       return "EDC_Error_Info:  Tcl Interperter fails to run test case."
      }
    if { [itest::stepResultCode ] != 0 } {
       set errorInfo [  itest::stepIssues ]
       return "EDC_Error_Info: $errorInfo"
     }
  
    set portstatusStr [ itest::response portstatusvalue ]
    set path [ file dirname $testcaseFile ]
    set parserFile $path/getportstatus.tcl
    
    if {[ file exists $parserFile ]  } {
     source $parserFile
     set portstatusStr [ parsePortStatus $portstatusStr $portlist ]
    } 
    if { [file exists $runtestcaseFile ] == 1 } {
     file delete $runtestcaseFile
    }
    return $portstatusStr
}


proc edc::changeTable { content } {
    set i 0
    array unset arr
    if { ([string length $content] < 0 ) } {
      return ""
    }
#    if { ([string first "\n" $content] < 0 ) } {
#      set content "$content\n"
#    }

#    foreach line [ split $content \n] {
#      if { [string length $line ] > 0 } {
##        set collist [split $line ]
#        set collist $line
#        set arr($i) $collist
#        unset collist
#        incr i 
#      }
#    }
#   switch [ catch {set columnCount [llength $arr(0)] } ] {
#    1 { set tableStr "1,$content" ; return $tableStr}
#   }
#   set columnCount [llength $arr(0)]
#   set rowCount $i

#   set tableStr "$rowCount"
#   for { set column 0 } { $column < $columnCount } { incr column } {
#    for { set row 0 } { $row < $rowCount } { incr row } {
#      set tableStr "$tableStr,[lindex $arr($row) $column ]"
#  }
#}
# return $tableStr

#
# 11-05-2009 Comments 
# According to Kate's comments on 11-05-2009, the customized data is showed to result view
# one row per session; The cell in result view is sperated with "\t"
#

    set tablestr ""
    if { ([string first "\t" $content] < 0 ) } {
      set tablestr "1,$content"
      return $tablestr
    }
    set ColumnCount [regsub -all {\t} $content "," tablestr ]
    if { $ColumnCount == 0 } {
     set tablestr "1,$tablestr"
    } else {
     set ColumnCount [ incr ColumnCount ]
     set tablestr "$ColumnCount,$tablestr"
    }
    return $tablestr
}

#customizedCmd,
#session,
#testcaseFile
proc edc::edccustomizedCmd { session testcaseFile {isUpdate  "false" }} {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable stepstr;
    variable result;
 
   
#    itest::open -w $edc::workspacePath -p $sessionparameters 
    
    variable entrypoint
    variable runtestcaseFile
    
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
   if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }
    if { $isUpdate == "false" } {
      set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session} -storeResponse customizedValue "
    } else {
      set testcaseStr [itest::convertPathToURL $testcaseFile ]  
      set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint }  -storeResponse customizedValue "   
    }
    
    if { [catch {
     eval $stepstr
      } errmsg ] } {
        set result "EDC_Error_Info:  Tcl Interperter fails to run test case."
      } 
#      set result [itest::response customizedValue ]
#      set tableName [itest::response customizedValue ]
#      if { [string length $tableName ] <= 0 } {
#        set result "1"
#      }
#      set path  [ file dirname $testcaseFile ]
#      set tableFile $path/$tableName
#      if { [ file exists $tableFile ] == 1 } {
#        set fileContent  [edc::readXMLFile $path/$tableName ]
#        set result [ edc::changeTable $fileContent ]
#      }
 
    if { [itest::stepResultCode ] != 0 } {
       set errorInfo [  itest::stepIssues ]
       set result "EDC_Error_Info: $errorInfo"
     }
       
      set responseValue [itest::response customizedValue ]
      if { [ string length $responseValue ] <= 0 } {
        set result " "
      }  else {
        set result [ edc::changeTable $responseValue ]
      }
       
      if { [file exists $runtestcaseFile ] == 1 } {
        file delete $runtestcaseFile
      }
      return $result
}


proc clearPortResult { session testcaseFile portlist } {

   if { [file exists $testcaseFile] == 0 } {
     return "EDC_Error_Info: test case file does not exist.";
    }  
    variable Result

    variable entrypoint
    variable runtestcaseFile
    set runtestcaseFile [ edc::processTestCaseFile $session $testcaseFile  entrypoint ]
    if { [ llength $runtestcaseFile ] == 0 } {
      return "EDC_Error_Info: run null test case file."
    }
    if { [ info exists entrypoint ] == 0 } {
      set entrypoint "main"
    }

    set testcaseStr [itest::convertPathToURL $runtestcaseFile ]
    set stepstr "  itest::step call \"\" {$testcaseStr#$entrypoint  -session $session -portlist $portlist } "
    if { [catch {
     eval $stepstr
      } errmsg ] } {
       set Result "EDC_Error_Info:  Tcl Interperter fails to run test case." 
      }

    if { [file exists $runtestcaseFile ] == 1 } {
      file delete $runtestcaseFile
     }
      
    if { [itest::stepResultCode ] != 0 } {
       set Result [  itest::stepIssues ]
       return "EDC_Error_Info: $Result"
     } else {
       return 0
     }
}
