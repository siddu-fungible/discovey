#
# ip.tcl --
#
# Extensions and addition to the standard "ip" library..
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
# Dependencies:
#
#   Uses the tcllib ip package for IPv6 address manipulation (especially
#   verification and normalization).
#
# History:
#
#   2006-08-23 John Morris - initial version (ipv6::AddrRandom, ipv6::AddrAdd).

namespace eval ::stclib::ip {}
package require ip 1.0.0

#
# ip::v6AddrRandom --
#
#   Generate a totally or partially random IP v6 address in normalized format.
#   The caller may specify a fixed high order part and this proc will generate
#   random low order parts. Optionally, it will never produce the same address
#   twice.
#
# Arguments:
#
#   randomBits  The number of low order bits of the 128 bit IPv6 address to randomize.
#           For example, if this is set to 32 then the low 32 bits of the "base" argument
#           will be replaced by 32 random bits.
#
#   base    The initial IPv6 address to use as the basis for modification. This
#           may be in any of the legal IP v6 address formats (see RFC3513). Any
#           parts of this which are not modified by the random bit generation will
#           returned in the created address. Defaults to all zero.
#
#           Note that you can use the compressed "::" ipv6 address format for the low
#           parts of the input address to save you having to specify all of those
#           components which are about to be clobbered by randomness!
#
#   unique  Boolean, default false. If set, do not return any address which has previously
#           been returned by this function.
#
# Results:
#
#   A normalized IPv6 address string is returned. The low randomBits of the address
#   are generated randomly. The remaining bits are copied from the base argument.
#
#   A namespace array, IPv6RandomUsed, records each returned address and prevents
#   any given same address being returned more than once.
#
# Issues:
#
#   Since no address can be returned more than once, then sooner or later the proc
#   will not be able to generate any new address. It will also start to eat up memory,
#   and could get slow. If this is going to become an issue, may need to add a function
#   (or maybe a flag) to zap the duplicate avoidance array.
#
proc ::stclib::ip::v6AddrRandom {{randomBits 64} {base "::"} {unique 0}} {
    variable Ipv6RandomUsed

    # Use the tcllib ip package to do the grunt work of address format checking.

    if {![::ip::is ipv6 $base]} {
        error "[lindex [info level 0] 0]: invalid address \"$base\": value must be a valid IPv6 address"
    }

    if {($randomBits < 1) || ($randomBits > 128)} {
        error "[lindex [info level 0] 0]: invalid random bits \"$randomBits\": value must be 1 to 128"
    }

    set address [ip::normalize $base]
    set parts [split $address ":"]

    # Generate the address, then look to see if it has been used already. If not, we are
    # good to go. If yes, then try again for some limit.
    #
    # What limit to use? I choose to retry for two times the maximum number of possible
    # random values with the given number of bits. That's a compromise between giving up
    # too easily and getting into excessive run times.

    for {set tries [expr {(1 << $randomBits) * 2}]} {$tries >= 0} {incr tries -1} {

        # Since the address is normalized, we might as well deal with the 16 bit
        # components it already uses, one at a time.

        for {set i 7} {$randomBits >= 16} {incr randomBits -16} {
            set parts [lreplace $parts $i $i [format "%04X" [expr {int (rand() * 65536)}]]]
            incr i -1
        }

        # Deal with any remaining bits, which require modification of just part
        # of a component.

        if {$randomBits > 0} {
            set oldval [scan [lindex $parts $i] "%x"]
            set mask   [expr {(1 << $randomBits) - 1}]
            set random [expr {int (rand() * ($mask + 1))}]
            set newval [expr {($random & $mask) | ($oldval & ~$mask)}]
            set parts  [lreplace $parts $i $i [format "%04X" $newval]]
        }
        set result [join $parts ":"]

        if {$unique} {
            # Check this is not a duplicate. If it is, go and try again. Otherwise we're done.

            if {[info exists Ipv6RandomUsed($result)]} {
                continue;
            }
        }
        set Ipv6RandomUsed($result) 1
        return $result
    }
    error "[lindex [info level 0] 0]: could not find an unused address"
}

#
# ip::v6AddrAdd --
#
#   Add two values, each of which may be an IPv6 address or an integer, to give
#   a new IPv6 address.
#
# Arguments:
#
#   addr1   The first IP v6 address (in any of the formats defined in RFC3513), or an
#           integer (in any of the formats demmed valid by "string is integer").
#
#   addr2   The other one.
#
# Results:
#
#   Returns the sum of the two addresses, as a normalized IPv6 address.
#
# Restrictions:
#
#   Integers must be positive numbers, and within the range of positive values for
#   the TCL version being used. Currently that usually means 0 to 2^31-1.
#
proc ::stclib::ip::v6AddrAdd {addr1 addr2} {
    foreach {varName value} [list addr1 $addr1 addr2 $addr2] {
        if {[string is integer -strict $value]} {
            if {$value < 0} {
                error "[lindex [info level 0] 0]: invalid value \"$value\": negative values are not supported"
            }

            # Create an IPv6 address by inserting bits of the supplied integer
            # into the low order components, then using the standard compression
            # for the high order.

            set parts {}
            while {$value > 0} {
                set parts [linsert $parts 0 [format "%04X" [expr {$value % 65536}]]]
                set value [expr {$value / 65536}]
            }
            set ipv6 "::[join $parts ":"]"
        } elseif {[::ip::is ipv6 $value]} {
            set ipv6 $value
        } else {
            error "[lindex [info level 0] 0]: invalid value \"$value\": must be an integer or IPv6 address"
        }
        set address [ip::normalize $ipv6]
        set $varName [split $address ":"]
    }
    set carry 0
    set parts {}
    for {set i 7} {$i >= 0} {incr i -1} {
        set word1 [scan [lindex $addr1 $i] "%x"]
        set word2 [scan [lindex $addr2 $i] "%x"]
        set sum   [expr {$word1 + $word2 + $carry}]
        set carry [expr {$sum / 65536}]
        set sum   [expr {$sum & 65535}]
        set parts [linsert $parts 0 [format "%04X" $sum]]
    }
    return [join $parts ":"]
}

package provide stclib::ip 0.0.1
