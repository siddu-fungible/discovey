#
# Non-shippable test, documentation, build and install utility.
#
# Source-able file to run all unit tests and generate documentation.
# Any unit tests added to this directory should get run automatically,
# and any code whould get run through the doc generator.
#
# Tested on:
#    Windows XP with ActiveState's distro of TCL 8.4.13
#    Linux (install must be run as root) on Ubuntu 6.06 and Fedora Core 4.
#

package require fileutil

set auto(version) 0.0.1
set auto(name) "stclib"
set auto(root) [file dirname [file normalize [info script]]]

proc Test {} {
    package require tcltest
    ::tcltest::configure -verbose {body error pass}
    ::tcltest::configure -notfile {*.html auto.tcl}
    ::tcltest::runAllTests
    ::tcltest::cleanupTests
}

proc Doc {} {
    global argv0 auto
    
    set pwd [pwd]
    cd $auto(root)
    
    puts "Generating documentation..."
    set sTclDoc [file join [pwd] "../Tools/sTclDoc/sTclDoc.tcl"]
    set files [glob *.tcl]
    foreach skip {auto.tcl pkgIndex.tcl} {
        set i [lsearch $files $skip]
        if {$i >= 0} {
            set files [lreplace $files $i $i]
        }
    }
    file mkdir ./doc
    eval exec $argv0 [file normalize $sTclDoc] ./doc $files
    puts "Done."
    
    
    cd $pwd
}

proc Install {} {
    global auto
    global auto_path
    global tcl_platform
    
    # User may have changed directory. Go back to where we belong.
        
    set pwd [pwd]
    cd $auto(root)

    # Do the code first. Assumes that the place to install is a subdirectory
    # of the second entry in the auto_path variable.

    switch -- $tcl_platform(platform) {
        unix {
            set mode "-m 0644"
        }

        default {
            set mode ""
        }
    }    
        
    set libPath [lindex $auto_path 1]
    set libPath [file join $libPath $auto(name)]
    
    puts "Installing $auto(name) code to $libPath"
    
    file mkdir $libPath
    foreach file [glob *.tcl] {
        if {$file ne "auto.tcl"} {
            puts "Installing $file..."
            eval ::fileutil::install $mode $file $libPath
        }
    }

    # Now do the documentation. Make sure it is up to date
    
    Doc
    
    switch -- $tcl_platform(platform) {
        windows {
            set installPath [file normalize [file join $libPath ".."]]
            set docPath [file join $installPath "doc"]
            set docPath [file join $docPath $auto(name)]
        }
        
        unix {
            set docPath [file join "/usr/share/doc" $auto(name)]
        }

        default {
            cd $pwd
            error "I don't know where to put the documentation on $tcl_platform(platform)."
        }
    }    
    
    puts "Installing $auto(name) documentation to $docPath."
    file mkdir $docPath
    cd doc
    foreach file [glob *.html] {
        puts "Installing $file..."
        eval ::fileutil::install $mode $file $docPath
    }
    
    # Tell the user what happened
    
    puts ""
    puts "The stclib packages have been installed in $libPath and should"
    puts "be accessible using 'package require'."
    puts ""
    puts "The documenation has been installed in $docPath."
    puts "To view the documentation cut and paste this link to your browser:"
    puts ""
    puts "     file://$docPath/index.html"
    puts ""
    
    cd $pwd
}

puts "Now use \"Test\", \"Doc\" or \"Install\""
