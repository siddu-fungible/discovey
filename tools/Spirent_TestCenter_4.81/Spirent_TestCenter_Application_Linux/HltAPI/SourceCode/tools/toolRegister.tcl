package require registry

namespace eval ::sth::hlapiGen:: {

}

proc ::sth::hlapiGen::newxml_withlocation {xmlfile scriptpath} {
	set fileR [open $xmlfile r]
	set readbuf [read $fileR]
	
	set mypath $scriptpath
	if {$mypath eq "." || [regexp "relative" [file pathtype $mypath]]} {
		set mypwd [pwd]
		set mypath [file normalize [file join $mypwd $mypath]]
	}
	puts "Working path is: $mypath"
	set newbuf [regsub "scriptname=\"hlapiGen" $readbuf "scriptname=\"$mypath"]
	close $fileR
	
	set fileD [open $xmlfile\.new w]
	puts $fileD $newbuf
	close $fileD
	return $xmlfile\.new
}

proc ::sth::hlapiGen::register {version} {
   set myscript [info script]
   set scriptpath [file dirname $myscript]
   puts "Current OS: $::tcl_platform(os), version $::tcl_platform(osVersion)."
   set mypath "C:/ProgramData/Spirent/TestCenter $version/"
   
   set newxml [newxml_withlocation [file join $scriptpath "hlapiGenCustomTool.xml"] $scriptpath]
   # windows 7 is windows NT, version 6.1
   if {$::tcl_platform(osVersion) >= 6.1 || [file exist $mypath]} {
      if {[file exist $mypath]} {
        set path [file join $mypath "./ScriptWizards/"]
        file copy -force $newxml "$path/hlapiGenCustomTool.xml"
		set genpath [file join $path "./hlapiGen/"]
		file delete -force $genpath
      }
   } else { 
	   set regpath "HKEY_LOCAL_MACHINE\\SOFTWARE\\Spirent communications\\Spirent TestCenter\\$version\\\Components\\Spirent TestCenter Application\\"
	   if {[catch {set stcpath [registry get $regpath "TARGETDIR"]} errMsg]} {
			puts $errMsg
	   } else {
		   set mypath [file normalize $stcpath] 
		   if {[file exist $mypath] && [file isdirectory $mypath]} {
			    set path [file join $mypath "./Spirent TestCenter Application/ScriptWizards/"]
			    file copy -force $newxml "$path/hlapiGenCustomTool.xml"
		 		set genpath [file join $path "./hlapiGen/"]
				file delete -force $genpath
		   }
	   }
   }
   file delete -force $newxml
   if {[info exist path]} {
       if {[file exist [file join $path "hlapiGenCustomTool.xml"]]} {
	       puts "Registration to Spirent TestCenter $version succeeded."
		} else {
		   puts "Registration failed: Cannot copy hlapiGen tool to Spirent TestCenter $version installation folder."
		}
   } else {
	   puts "Registration failed: Cannot find Spirent TestCenter $version installation folder."
   }
}

if { [regexp -- {[0-9.]+} [lindex $argv 0] match]} {
	if {![string compare -nocase $::tcl_platform(platform) "windows"]} {
		::sth::hlapiGen::register [lindex $argv 0]
	} else {
		puts "This tool can be registered to windows only."
	}
} else {	
	puts "Usage sample:"
	puts "\ttclsh C:\\Tcl\\lib\\hltapi\\tools\\toolRegister.tcl 4.30"
}