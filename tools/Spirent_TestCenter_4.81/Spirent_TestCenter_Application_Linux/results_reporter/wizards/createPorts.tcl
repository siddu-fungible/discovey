proc makePorts {numPorts} {
    if {[llength [stc::get system1 -children-project]] == 0} {
        stc::create project
    }
    set project [stc::get system1 -children-project]
    for {set i 0} {$i < $numPorts} {incr i} {
        stc::create port -under $project
    }
}

proc terminateWizard {} {
    set ::__done true
}

proc finishWizard {} {
    makePorts [$::f.entry get]
    terminateWizard
}

set w [toplevel .u]
wm title $w "Port Wizard"
wm deiconify $w

set f [frame $w.f1]
pack [label $f.title -text "Port Wizard"] -side top
pack [label $f.label -text "Number of ports to create: "] -side left
pack [entry $f.entry] -side left -fill x -expand true
$f.entry insert 0 {1}
pack $f -fill x -padx 2 -pady 2

set f2 [frame $w.f5]
button $f2.b3 -text Cancel -default normal -command { terminateWizard }
button $f2.b4 -text Finish -default active -command { finishWizard }
pack $f2.b3 $f2.b4 -padx 10 -side left
pack $f2 -pady 2

vwait __done
unset __done
destroy $f
destroy $f2
destroy $w
