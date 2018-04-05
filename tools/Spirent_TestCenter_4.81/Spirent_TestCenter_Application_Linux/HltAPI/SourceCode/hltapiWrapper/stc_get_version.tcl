# This script relies on the environment variable TCLLIBPATH being set correctly.
# It must point to at least one version of Spirent TestCenter.
package require SpirentTestCenter

set chassisip [lindex $argv 0]
set slotport  [lindex $argv 1]  ;# This is only used for controller 1 chassis.

stc::connect $chassisip

set version ""

# There should only be one chassis.
foreach chassis [stc::get system1.physicalchassismanager -children-physicalchassis] {
    set controller [stc::get $chassis -ControllerHwVersion]

    if { $controller > 1 } {
        set version [stc::get $chassis -FirmwareVersion]
    } else {
        # You need to extract the version from the module itself.
        # First, find the module specified by $slotport.
        set slot [lindex [split $slotport /] 0]

        foreach physicaltestmodule [stc::get $chassis -children-physicaltestmodule] {
            if { [stc::get $physicaltestmodule -Index] == $slot } {
                set version [stc::get $physicaltestmodule -FirmwareVersion]
                break
            }
        }
    }
    puts $version
}

return $version