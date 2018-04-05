
set tsharkLoc [lindex $argv 0]
set pcapWithNameLoc [lindex $argv 1]
set outputWithNameLoc [lindex $argv 2]
set outputWithNameByteLoc [lindex $argv 3]

# Set path for linux (this is for cs mode but shouldn't hurt to set it on non cs linux machine)
if {$tcl_platform(platform) != "windows"} {
		# check to see if it is a 32 biit or 64 bit machine
		catch {exec uname -a} res

		# 32 bit
		if {[regexp i386 $res] == 1} {
			set curPath "/home/stc/STC_Server/PDMLMap/HelperFiles/wireshark32bit"
			catch {exec chmod 777 "/home/stc/STC_Server/PDMLMap/HelperFiles/wireshark32bit/tshark"}
		} else {
			set curPath "/home/stc/STC_Server/PDMLMap/HelperFiles/wireshark64bit"
			catch {exec chmod 777 "/home/stc/STC_Server/PDMLMap/HelperFiles/wireshark64bit/tshark"}	
		}

        if {[info exist env(LD_LIBRARY_PATH)] == 0} {
                set env(LD_LIBRARY_PATH) "$curPath"
        } else {
                set env(LD_LIBRARY_PATH) "$curPath:$env(LD_LIBRARY_PATH)"
        }

        if {[info exist env(PATH)] == 0} {
                set env(PATH) "$curPath"
        } else {
                set env(PATH) "$curPath:$env(PATH)"
        }
}

# Get current tshark version. 
# If tshark version cannot be retrieved, print out a warning message and exit. 
# Output: Full tshark version is 1.6.17-Spirent. This procedure returns subversion 1 and 6.
proc getVersion { tsharkLoc } {
	# The output of command "tshark -v" is: TShark 1.6.17-Spirent (SVN Rev 49862 from /trunk-1.6) ...
	# Parse the version string and get subverion 1 and 6.
	catch {exec $tsharkLoc -v}  result
	
	# parse the result by space to get each string. Search for string "TShark"
	set fields [split $result " "]
	set strOffset [lsearch -exact $fields TShark]
	
	if { $strOffset < 0 } {
		puts "Failed to retrieve tshark version."
		exit 0
	}
	
	# Get the string next to TShark, which should be something like "1.6.17-Spirent". Parse the string by "." and "-".
	set verTshark [lindex $fields [expr ($strOffset+1)]]
	
	set subfields [split $verTshark ".-"]
	set t1 [lindex $subfields 0]
	set t2 [lindex $subfields 1]
	
	# Get subversion number and verify if they are integers
	if { [string is integer -strict $t1] && [string is integer -strict $t2]} {
		return [list $t1 $t2]
	}	else {
		puts "Failed to retrieve tshark version."
		exit 0
	}
}

# Parse with PDML
if {[catch {exec $tsharkLoc -T pdml -c 4000 -r - < $pcapWithNameLoc > $outputWithNameLoc} errmsg] == 1} {
}

# Parse with Byte
# For wireshark 1.9 and newer versions, "tshark -Px" should be used to get packet summary information. For older build (0.99.x, 1.1.x - 1.8.x), the command is "tshark -x".
set vtshark [ getVersion $tsharkLoc ]
if {([lindex $vtshark 0] == 0) || ([lindex $vtshark 0] == 1 && [lindex $vtshark 1] < 9) }	{
	if {[catch {exec $tsharkLoc -x -c 4000 -r - < $pcapWithNameLoc > CaptureToTempByte.txt} errmsg] == 1} {
	}
} else {
	if {[catch {exec $tsharkLoc -Px -c 4000 -r - < $pcapWithNameLoc > CaptureToTempByte.txt} errmsg] == 1} {
	}
}


set hnd [open CaptureToTempByte.txt]

set outHnd [open $outputWithNameByteLoc w]

set startParse 0
set frameDetected 0
set parseOutput ""
set str ""
set firstFound 0
set lastLineLen 0
while {![eof $hnd]} {
    gets $hnd line
    
    if {$startParse == 0} {
	set parseOutput ""
	set str ""
    }

    # Look for the packet number. This is because wireshark may translate same packet twice. 
    # Need to skip the second translation
    if {[regexp {^[1-9][[:digit:]]*} [string trim $line]] == 1} {
		set splitString [split [string trim $line]]
		set tmpCnt [lindex $splitString 0]
			
		if {$firstFound == 0} {
			set curCnt $tmpCnt
			set firstFound 1
			set frameDetected 1
		}
		
		# CR 2244281831: detect frame index only when last line was empty. Otherwise frame index and index of packet content hex index might messed up
		if {[expr $curCnt + 1] == $tmpCnt && $lastLineLen == 0} {
			set frameDetected 1
			incr curCnt
		}
    }

    # start parsing the byte output
    if {[regexp {^0000} $line] && $frameDetected == 1} {
		set startParse 1

		# manipulate the content
		set splitLine [split $line]
		set splitLine [lrange $splitLine 2 17]
	
		foreach byte $splitLine {
	    	set str $str$byte
		}

		lappend parseOutput $line

    } elseif {$startParse == 1} {

		# manipulate the content
		set splitLine [split $line]
		set splitLine [lrange $splitLine 2 17]
	
		foreach byte $splitLine {
	    	set str $str$byte
		}
    }

    if {[string length $line] == 0} {
		if {$startParse == 1} {
	    	set startParse 0
	    	set frameDetected 0
	    	puts $outHnd $str
		}
    }
	
	set lastLineLen [string length $line]
}   

close $hnd
close $outHnd
file delete CaptureToTempByte.txt

exit 0



