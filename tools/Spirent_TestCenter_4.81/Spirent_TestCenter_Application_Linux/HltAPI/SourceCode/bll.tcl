# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# bll.tcl --
#
#   Miscellaneous utility procs for interacting with the BLL.
#
#   Part of the stclib package.
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
#          copyright notice, this list of conditions, and the
#          following disclaimer.
#
#   2. Redistribution in binary form must reproduce the above
#          copyright notice, this list of conditions and the
#          following disclaimer in the documentation and/or other
#          materials provided with the distribution.
#
#   3. Neither the name Spirent Communications nor the names of 
#          its contributors may be used to endorse or promote 
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

namespace eval ::stclib::bll {}

package require Tclx
package require SpirentTestCenter

# stclib::bll::treeWalk --
#
#   BLL object hierarchy tree walker. Walks the BLL object tree starting
#   from the specified root node and returns a TCLx representation of
#   that tree.
#
# Arguments:
#
#   root    Optional. The root node of the sub-tree to be walked. Defaults
#           to "system1", which means walk the entire configuration. (Defaulting
#           this parameter is the expected usage. It is present to allow
#           the proc to recurse to itself as it explores the tree.)
#   
#
# Results:
#
#   The tree representation is returned as a TCLx hierarchical keyed list.
#
#   The object tree, as held in the keyed list, has leaf nodes and branch
#   nodes. 
#
#   A leaf node is an actual attribute, with a name and a value. In the keyed
#   list, the key is the attribute name (including the leading "-") and 
#   value is the attribute value.
#
#   A branch node just has other nodes branching off it. In the keyed list
#   the key is the object name and the value is a nested keyed list potentially
#   containing both leaf nodes (these are the attributes of this object) and 
#   other branch nodes (these are the children of this object).
#
#   Leaf and branch nodes may be distinguished by the presence or not of
#   the leading "-" in the keyed list tag.
#
# Pre-requisites:
#
#   TCLx, ::stc::
#
# Notes:
#
#   Assumes that the BLL interface consistenly and accurately returns the
#   "-children" attribute when an object has descendants.
#
#   Has not yet been tested with very large object trees.
#
# History:
#
#   2006-07-13 First cut - john.morris@spirentcom.com

proc ::stclib::bll::treeWalk {{root system1}} {
    set objtree {}
    array set attrlist [::sth::sthCore::invoke stc::get $root]
    foreach attr [array names attrlist] {
        if {($attr ne "-parent") && ($attr ne "-children")} {
            keylset objtree $attr [list $attrlist($attr)]
        }
    }

    if {[info exists attrlist(-children)]} {
        set children $attrlist(-children)
        foreach child $children {
            keylset objtree $child [::stclib::bll::treeWalk $child]
        }
    }
    return $objtree
}

# Give Chassis/Slot/Port params, get a list of PhysicalProtGroups without duplicates
proc ::stclib::bll::getPortGroupsForCspList {ports} {
    set portGroupList [list]

    # For each CSP
    foreach csp $ports {
        # Get chassis, slot, and port separately
        regexp {(//)?(.*)/(.*)/(.*)} $csp slashes other chassis slot port

        # Find chassis
        set chassisManager [::sth::sthCore::invoke stc::get system1 -children-physicalChassisManager]
        set physicalChassis NONE
        foreach physicalChassisChild [::sth::sthCore::invoke stc::get $chassisManager -children-physicalChassis] {
            if {$chassis == [::sth::sthCore::invoke stc::get $physicalChassisChild -hostname]} {
                set physicalChassis $physicalChassisChild
                break
            }
        }
        if {"NONE" == $physicalChassis} {
            error "Cannot find physical chassis with hostname $chassis"
        }

        # Find test module by index
        set physicalTestModule NONE
        foreach physicalTestModuleChild [::sth::sthCore::invoke stc::get $physicalChassis -children-physicalTestModule] {
            if {$slot == [::sth::sthCore::invoke stc::get $physicalTestModuleChild -index]} {
                set physicalTestModule $physicalTestModuleChild
                break
            }
        }
        if {"NONE" == $physicalTestModule} {
            error "Cannot find test module at slot $slot"
        }
        
        # Find port group
        set physicalPortGroup NONE
        foreach physicalPortGroupChild [::sth::sthCore::invoke stc::get $physicalTestModule -children-physicalPortGroup] {
            foreach physicalPortChild [::sth::sthCore::invoke stc::get $physicalPortGroupChild -children-physicalPort] {
                if {$port == [::sth::sthCore::invoke stc::get $physicalPortChild -index]} {
                    set physicalPortGroup $physicalPortGroupChild
                    break
                }
            }
        }
        if {"NONE" == $physicalPortGroup} {
            error "Cannot find port group at index $port"
        }
        
        # If not already in list
        if {-1 == [lsearch $portGroupList $physicalPortGroup]} {
            # Add to list
            lappend portGroupList  $physicalPortGroup
        }
    }

    return $portGroupList
}

# Return list of port groups whose status property is "down"
proc ::stclib::bll::getDownPortGroups {portGroups} {
    set downPortGroupList [list]

    # Loop looking for status of down
    foreach portGroup $portGroups {
        if {"MODULE_STATUS_DOWN" == [::sth::sthCore::invoke stc::get $portGroup -Status]} {
            lappend downPortGroupList $portGroup
        }
    }

    return $downPortGroupList
}

# Return true if any port groups are down
proc ::stclib::bll::anyPortGroupsAreDown {portGroups} {
    return [expr 0 < [llength [getDownPortGroups $portGroups]]]
}

# Safe stc::release replacement
proc ::stclib::bll::release {ports} {
    eval ::sth::sthCore::invoke stc::release $ports
}

# Safe stc::reserve replacement
proc ::stclib::bll::reserve {ports} {
    set portGroupRecoveryTimeout 50
    set maxFirstDownReportLatency 2

    # Wait for any old release to get past "UP" phase
    ::sth::sthCore::invoke stc::sleep $maxFirstDownReportLatency

    # Create list of port groups
    set portGroups [getPortGroupsForCspList $ports]

    # Loop checking for status to become "UP" for all
    set secondsSlept 0
    while {[anyPortGroupsAreDown $portGroups]} {
        ::sth::sthCore::invoke stc::sleep 1
        incr secondsSlept

        if {$secondsSlept > $portGroupRecoveryTimeout} {
            error "Reserve Timed out while waiting $portGroupRecoveryTimeout seconds for reboot.  These port groups are down: [getDownPortGroups $portGroups]"
        }
    }
    
    # Reserve using STC
    eval ::sth::sthCore::invoke stc::reserve $ports
}

package provide stclib::bll 0.0.1
