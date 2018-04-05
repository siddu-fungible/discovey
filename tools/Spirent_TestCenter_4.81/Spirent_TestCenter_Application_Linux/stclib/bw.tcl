###############################################################################
# build version 1.9
# bw.tcl --
#
#   Extensions and addition to the standard "BWidget" library..
#
# Copyright (c) 2006 by Spirent Communications, Inc.
# All Rights Reserved
#
# By accessing or executing this software, you agree to be bound 
# by the terms of this agreement.
# 
# Redistribution and use of this software in source and binary
# forms, with or without modification, are permitted provided
# that the following conditions are met: 
#
#   1. Redistribution of source code must contain the above 
#	   copyright notice, this list of conditions, and the
#	   following disclaimer.
#
#   2. Redistribution in binary form must reproduce the above
#	   copyright notice, this list of conditions and the
#	   following disclaimer in the documentation and/or other
#	   materials provided with the distribution.
#
#   3. Neither the name Spirent Communications nor the names of 
#	   its contributors may be used to endorse or promote 
#      products derived from this software without specific 
#      prior written permission.
#
# This software is provided by the copyright holders and
# contributors [as is] and any express or implied warranties, 
# limited to, the implied warranties of merchantability and 
# fitness for a particular purpose are disclaimed.  In no event 
# shall Spirent Communications, Inc. or its contributors be 
# liable for any direct, indirect, incidental, special, 
# exemplary, or consequential damages  (including, but not 
# limited to: procurement of substitute goods or services; loss 
# of use, data, or profits; or business interruption) however 
# caused and on any theory of liability, whether in contract, 
# strict liability, or tort (including negligence or otherwise) 
# arising in any way out of the use of this software, even if 
# advised of the possibility of such damage.
#

namespace eval ::stclib::bw {}


package require Tclx
package require snit

# stclib::bw::bllTree --
#
#   Creates a megawidget conatining a labelled, hierarchical tree display of 
#   BLL objects, based on the BWidget tree widget.
#
# Arguments:
#
#   name - name of the megawidget to be created, in the usual Tk format.
#
# Results:
#
#   Returns the megawidget ID, which is also defined as a command.
#
# Pre-requisites:
#
#   Uses TCLx, BWidget, Snit
#
# Notes:
#
#   If the tree already exists on entry it will be destroyed and redrawn. This
#   allows bllTree to be called repeatedly as the tree changes.
#
# History:
#
#   2006-07-13 First cut - john.morris@spirentcom.com
#
#   2006-10-02 Reimplemented using the SNIT framework. john.morris@spirentcom.com

namespace eval ::stclib::bw {
        variable helpInfo
        
        set helpInfo {}

    # modified from code at http://wiki.tcl.tk/3307 - by Donal Fellows 
    proc zipFileList {filename} {
        set names {}
        set fd [open $filename rb]
        set off -22
        while 1 {
            seek $fd $off end
            binary scan [read $fd 4] i sig
            if {$sig == 0x06054b50} {
                seek $fd $off end
                break
            }
            incr off -1
        }
        binary scan [read $fd 22] issssiis sig disk cddisk nrecd nrec \
                dirsize diroff clen
        if {$clen > 0} {
            set comment [read $fd $clen]
        } else {
            set comment ""
        }
        if {$disk != 0} {
            error "multi-file zip not supported"
        }
        seek $fd $diroff
        for {set i 0} {$i < $nrec} {incr i} {
            binary scan [read $fd 46] issssssiiisssssii \
                sig ver mver flag method time date crc csz usz n m k d ia ea \
                off
            if {$sig != 0x02014b50} {
                error "bad directory entry"
            }
            set name [read $fd $n]
            set extra [read $fd $m]
            if {$k == 0} {
                set c ""
            } else {
                set c [read $fd $k]
            }
            lappend names $name
            # set directory($name) [dict create timestamp [list $date $time] \
            #         size $csz disksize $usz offset $off method $method \
            #         extra $extra comment $c]
        }
        return $names
    }

        proc initHelpZip {} {
                global env
        	if [catch {set fileNames [zipFileList [file join $env(STC_PRIVATE_INSTALL_DIR) HelpInfo.zip]]} err] {
        		puts stderr $err
                        return 0
        	}
        	foreach fileName $fileNames {        	 
        	regexp {HelpInfo/(.*).txt} $fileName match obj        	  
        	set obj [string tolower $obj]
        	keylset ::stclib::bw::helpInfo $obj [stc::help $obj]
        	}
                return 1
        }

        proc initHelp {} {
                if {!$::stclib::gdbg::helpFlag} {
                        return
                }
                global env
                set orgDir [pwd]
        	if [catch {cd [file join $env(STC_PRIVATE_INSTALL_DIR) HelpInfo]} err] {
	                if {[initHelpZip]} {
        	                return
                	}
        		puts stderr $err
                        return
        	}
        	foreach fileName [glob -nocomplain *.txt] {        	 
        	regexp {(.*).txt} $fileName match obj        	  
        	set obj [string tolower $obj]
        	keylset ::stclib::bw::helpInfo $obj [stc::help $obj]
        	}
                if [catch {cd $orgDir} err] {
        		puts stderr $err
        		return
        	}
        }
        
        ::snit::widgetadaptor bllTree {
        
                variable isopen -array {}
        
                delegate method * to hull
                delegate option * to hull
        
                constructor {args} {
                        installhull using TitleFrame -text "Spirent System Explorer"
                        ::stclib::bw::initHelp
                        $self configurelist $args
                }
                
                # ::stclib::bw::BllTree::populate --
                #
                #   Widget command to populate the tree.
                #
                # Arguments:
                #
                #   objtree     update the tree with the contents of this
                #               Txlx keyed list.
                #
                # Results:
                #
                #   The tree widget gets deleted if it already exists and redrawn with
                #   the new Tclx tree contents.

                method populate {objtree {filter system1}} {
                        if {[info exists ::TIMESTS_SWITCH ] && $::TIMESTS_SWITCH == "on"} {
                                set populateStart [clock seconds]
                        }
			if {[string equal $filter All]} {
				set filter system1
			}
                        set tframe [$hull getframe]
                        set window $tframe.window
                        catch {destroy $tframe.window}
                        set window [ScrolledWindow $tframe.window -relief sunken -borderwidth 2]
                        set tree   [Tree $window.tree \
                                -relief flat -borderwidth 0 -width 15 -highlightthickness 0\
        		        -redraw 1 -dropenabled 1 -dragenabled 1 -dragevent 3 \
                                -opencmd   [mymethod DoOpen $window.tree] \
                                -closecmd  [mymethod DoClose $window.tree] \
                                ]                       
                        $window setwidget $tree
                        pack $window -side top -fill both -expand yes
            
                        if {[catch {$tree insert end root $filter -text $filter \
                                -open true -image [Bitmap::get openfold] } ret]} {
                        puts "tree insert error $errorInfo"
                        }
                        $self DoPopulate $tree $filter $objtree
            
                        if {[info exists ::TIMESTS_SWITCH ] && $::TIMESTS_SWITCH == "on"} {
                                set populateEnd [clock seconds]
                                puts "populate cost [expr $populateEnd - $populateStart]s"
                        }
                }
                
                # ::stclib::bw::bllTree::showHelp --
                #
                #   Private utility to add help text to every leaf node
                #
                # Arguments:
                #
                #   obj         Parent node. That is the object which attribute belongs to.
                #               
                #   attribute   Leaf node. 
                #
                # Results:
                #
                #   Help info about the attribute extracted from [stc::help $obj] 
        
                proc showHelp {obj attribute} {
			set res ""
                        set match 0      	     	
      	
                        #remove character of '-' from the attribute
                        regexp {\s*-(.*)} $attribute mmm key
      	
                        foreach line [split $obj \n] {
                                if {!$match} {
                                        if {[regexp {^\s{2,3}([^\s]+)\s-\s.*} $line m attr]} {
                                                if {[string equal $attr $key]} {
                                                append res $line
                                                set match 1
                                                }
                                        }
                                        continue					
                                } else {
                                        if {[regexp {^\s\s[^\s].*} $line m attr] || \
                                                [regexp {^\s[^\s].*} $line m attr]} {
                                                break
                                        } else {
                                                if {[string first - $line] != -1} {
                                                continue
                                                }
                                                append res $line
                                        }
                                }
			}
                        return $res
        
                }
                
                # ::stclib::bw::BllTree::changeAttrValue --
		#
		#   Private function used to change the lable text of selected node 
		#   by double clicking.
		#
		# Arguments:
		#
		#   tree    The BWidget name for the tree part of the display. 
		#           That is the pathname.
		#
		#   node    Name of current selected node.
		#
		# Results:
		#
		#   The label of selected node becomes editable. When users press "Enter"
		#   after editing, applyChange is evoked with new value as a parameter. Otherwise
		#   edition is cancelled.
		    
		proc changeAttrValue {tree node} {
		    	# The selected node is not a leaf, just skip 
		    	if {![regexp {(.+)\.-(.+)} $node match obj pro]} {
		    		return
		    	} 
		    	set displayText [stc::get $obj -$pro]
		    	if {[regexp {.+\s.+} $displayText]} {
                                set displayText "{$displayText}"
		    	}
		    	set displayText "$pro: $displayText"
		    	$tree edit $node $displayText [list ::stclib::bw::bllTree::applyChange $node $tree]
                        }
                    		
                        # ::stclib::bw::BllTree::applyChange --
                        #
                        #   Private function used to apply the change to lable text of selected node 		
                        #
                        # Arguments:
                        #
                        #   tree    The BWidget name for the tree part of the display. 
                        #           That is the pathname.
                        #
                        #   node    Name of current selected node.
                        #
                        #   text    New text should be applied to the label of selected node.
                        #
                        # Results:
                        #
                        #   Change attribute' value. If succeed return 1, means the change is applied successfully.
                        #   If failed (caused by stc::config) return 0, means the change is simply ignored.
                        #
                        # Implementation note:
                        #   If attribute value has space, {} should be treated specially
		    
                        proc applyChange {node tree text} {
                        	set value ""
                                regexp {(.+)\.-(.+)} $node match obj pro
                                regsub -all {[\{\}]} $text {} ptext
                                regexp {.+:\s(.+)} $ptext match value
                                if { $value == "" } {
                                        tk_messageBox -message "Invalid format. Attribut Name: Attribute Value  " -type ok -icon warning -title "Error Message"
                                        return 0
                                }
                                if {[catch {stc::config $obj -$pro $value} result]} {
                                        tk_messageBox -message $result -type ok -icon warning -title "Error Message"
                                        return 0
                                } else {
                                        puts error
                                        $tree itemconfigure $node -text $text 
			     
                                        return 1
                                }
                        }
                        
                # ::stclib::bw::BllTree::DoPopulate --
                #
                #   Private recursive function used to action the "populate" bllTree
                #   widget command.
                #
                # Arguments:
                #
                #   tree    The BWidget name for the tree part of the display
                #
                #   stateName   Name of an array to be used to hold node state
                #           (open, closed) information to allow the tree to be
                #           redrawn consistently when the data changes.
                #
                #   parent  The parent node (name in the BWidget tree's name space)
                #           of the (sub-)tree to be drawn.
                #
                #   objtree Tclx keyed list of the corresponding BLL data.
                #
                # Results:
                #
                #   The tree is drawn recursively.
                #
                # Implementation note:
                #
                #   BLL tree widget node names must be unique. They are generated
                #   by dot-concatenating the corresponding BLL node names (e.g
                #   "system1.project1.port1".)
        
                method DoPopulate {tree parent objtree} {
                        #Get the class name of object
                        regexp {^Object[:]?\s*([^\n\r]*)\n*} [stc::help $parent] match objClass 
						set objClass [string tolower $objClass]
                        foreach key [keylkeys objtree] {
                                if {[string index $key 0] eq "-"} {\
                                        set value [keylget objtree $key]
                                        set value [regsub -all {[\r\n]} $value ""]
                                        if {!$::stclib::gdbg::helpFlag} {
                                                $tree insert end $parent $parent.$key \
                                                -text "[string range $key 1 end]: $value" \
                                                -image [Bitmap::get file]
                                        } else {
                                                if [catch {keylget stclib::bw::helpInfo $objClass}] {
                                                        set helpText ""  														
                                                } else {
                                                        set helpText [keylget stclib::bw::helpInfo $objClass]														
                                                }
                                                $tree insert end $parent $parent.$key \
                                                        -text "[string range $key 1 end]: $value" \
                                                        -image [Bitmap::get file] \
                                                        -helptext [::stclib::bw::bllTree::showHelp $helpText $key]  
                                        }                                                            
                                        $tree bindText <Double-1> [list ::stclib::bw::bllTree::changeAttrValue $tree]                    
                                } else {
                                        set state false
                                        set piccy [Bitmap::get folder]
                                        if {[info exists isopen($key)]} {
                                                set state $isopen($key)
                                                if {$state} {
                                                        set piccy [Bitmap::get openfold]
                                                }
                                        }
                                        if {[catch {$tree insert end $parent $key -text $key -open $state -image $piccy} ret]} {
                                                puts "tree insert error: $::errorInfo, parent = $parent, key = $key"
                                        }
                                        $self DoPopulate $tree $key [keylget objtree $key]
                                }
                        }
                }
        
                # ::stclib::bw::BllTree::DoOpen --
                #
                #   Private function invoked automatically when the user clicks
                #   on a bllTree node to open it.
                #
                # Arguments:
                #
                #   tree    The BWidget name for the tree part of the display
                #
                #   node    The name of the node within the BWidget tree that
                #           is being opened.
                #
                # Results:
                #
                #   Changes the node icon to an open folder. Notes the state
                #   in the "isopen" instance array.
        
                method DoOpen {tree node} {
                        $tree itemconfigure $node -image [Bitmap::get openfold]
                        set isopen($node) 1
                }
        
                # ::stclib::bw::BllTree::DoClose --
                #
                #   Private function invoked automatically when the user clicks
                #   on a bllTree node to close it.
                #
                # Arguments:
                #
                #   tree    The BWidget name for the tree part of the display
                #
                #   node    The name of the node within the BWidget tree that
                #           is being closed.
                #
                # Results:
                #
                #   Changes the node icon to a closed folder. Notes the state
                #   in the "isopen" instance array.
                
                method DoClose {tree node} {
                        $tree itemconfigure $node -image [Bitmap::get folder]
                        set isopen($node) 0
                }
        }
}

namespace eval ::stclib::bw {
                variable filename "initial"
        ::snit::widgetadaptor traceFrame {
                
                variable ts
                variable hooked {}
                variable clockFormat "%Y-%m-%d %H:%M:%S"
        
                # The hull is a BWidget scrolled window. A few options and
                # methods should go to it, but most go to the embedded
                # text widget.
                
                delegate method setwidget to hull
                delegate option -auto to hull
                
                component textwin
                delegate method * to textwin
                delegate option * to textwin
                
                constructor {args} {
                        installhull using ScrolledWindow -scrollbar both -auto both
                        install textwin using text $self.textwin -wrap none -width 80 \
                                    -font {-family courier -size 10} -state disabled
                        $self setwidget $textwin
                        $self tag configure annot   -background white
                        $self tag configure command -background LightBlue; # -font {-family courier -size 12}
                        $self tag configure normal  -background PaleGreen
                        $self tag configure error   -background pink                        
                        set ::stclib::bw::filename stcTraceCommand[clock clicks]                        
                }
        
                destructor {
                        #$self unhook ::stc::*
                        foreach procname $hooked {
                                $self DoUnhook $procname
                        }
                }
        
                method wrapappend {lines args} {
                        $self configure -state normal
                        foreach text [split $lines "\r\n"] { 
                                set maxwidth 78
                                set prepad ""
                                while {$text ne ""} {
                                        if {[string length $text] < $maxwidth} {
                                        eval $self insert end {$prepad$text\n} $args
                                        break
                                        } else {
                                                set i [string last " " $text $maxwidth]
                                                if {$i < 0} {
                                                        set i $maxwidth
                                                }
                                                set line [string range $text 0 $i]
                                                set text [string range $text [expr {$i + 1}] end]
                                                eval $self insert end {$prepad$line\\\n} $args
                                        }
                                        set maxwidth 74
                                        set prepad "    "
                                }
                        }
                        $self yview moveto 1.0
                        $self configure -state disabled
                }
                
                method hook {args} {
                        set thishook {}
                        foreach pattern $args {
                                foreach procname [namespace eval :: info procs $pattern] {
                                        set procname [namespace eval :: namespace which $procname]
        
                                        # Only hook procs not already hooked.
        
                                        if {[lsearch $hooked $procname] < 0} {
                                                lappend thishook $procname
                                                lappend hooked $procname
                                                trace add execution $procname enter [mymethod Enter]
                                                trace add execution $procname leave [mymethod Leave]
                                        }
                                }
                        }
                        return $thishook
                }
                
                method unhook {args} {
                        set tounhook {}
                        foreach pattern $args {
                                foreach procname [namespace eval :: info procs $pattern] {
                                        set procname [namespace eval :: namespace which $procname]
                                        set idx [lsearch $hooked $procname]
                                        if {$idx >= 0} {
                                                set hooked [lreplace $hooked $idx $idx]
                                                lappend tounhook $procname
                                        }
                                        $self DoUnhook $procname
                                }
                        }
                        return $tounhook
                }
                
                method hooked {} {
                        return $hooked
                }
                
                # Make this a proc so it can be called from the destructor, after
                # the actual widget has gone away...
                
                method DoUnhook {procname} {
                        trace remove execution $procname enter [mymethod Enter]
                        trace remove execution $procname leave [mymethod Leave]
                }
                
                method Enter {callinfo command} {
                        if { ($::stclib::gtrace::sstFlag == "true")&&($::stclib::gtrace::traceFlag  == "true")  } {
                                set ts [clock format [clock seconds] -format $clockFormat]
                                set procname [lindex $callinfo 0]
                                $self wrapappend "$ts: entering $procname" annot
                                $self wrapappend "$callinfo" command
                                incr ::stclib::gtrace::command_count
                                update idletasks
                        }
                }
                
                method writeToFile {  commandName  } {
        
                        
                        if {  $::stclib::gtrace::traceFlag  == "true" } {                                                 
                                
                                if { [ file exists $::stclib::bw::filename] == 0 } {
                                        set fileId [ open ./$::stclib::bw::filename w 0666 ] 
                                } else {
                                        set fileId [ open ./$::stclib::bw::filename a+ 0600 ]
                                }
                                puts $fileId $commandName
                                close $fileId
                        }
                }
                
                method Leave {callinfo code result op} {
                   
                        set ts [clock format [clock seconds] -format $clockFormat]
                        if { ($::stclib::gtrace::sstFlag == "false" )||($::stclib::gtrace::traceFlag  == "false") } {
                        return 
                        }
                        set procname [lindex $callinfo 0]
                        $self writeToFile $callinfo
                        switch $code {
                                0   {
                                        $self wrapappend "$ts: $procname returned normally" annot
                                        set tag normal
                                }
                
                                1   {
                                        $self wrapappend "$ts: $procname returned with error" annot
                                        set tag error
                                        incr ::stclib::gtrace::error_count
                                }
                        
                                2   {
                                        $self wrapappend "$ts: $procname returned with return" annot
                                        set tag normal
                                }
                        
                                3   {
                                        $self wrapappend "$ts: $procname returned with break"  annot
                                        set tag normal
                                }
                        
                                4   {
                                        $self wrapappend "$ts: $procname returned with continue" annot
                                        set tag normal
                                }
                        
                                default {
                                        $self wrapappend "$ts: $procname returned with unknown code $code" annot
                                        set tag error
                                        incr ::stclib::gtrace::error_count
                                }                    
                        }
                        $self wrapappend "$result" $tag
                        update idletasks
                }            
        }
}



