# sJava setup
java::call System loadLibrary sJava
package provide SpirentTestCenter 2.30
package provide stc 2.30

namespace eval ::stc_int:: {}

set ::stc_int::sJava com.spirent.tc.ui.sJava.sJava
set ::stc_int::StringVector com.spirent.tc.ui.sJava.StringVector

proc ::stc_int::argsToSv { args } {
    set out [java::field System out]

    set sv [java::new $::stc_int::StringVector]
    java::lock $sv
    foreach arg $args {
        $sv add $arg
    }

    return $sv
}

proc ::stc_int::svToArgs { sv } {
    set out [java::field System out]

    set wrapper ""
    if {[$sv size] > 1} {
        set wrapper "\""
    }

    set args ""
    for {set i 0} {$i < [$sv size]} {incr i} {
        if {$i > 0} {
            set args "$args "
        }
        if {[expr $i % 2] != 0} {
            set args "$args$wrapper[$sv get $i]$wrapper"
        } else {
            set args "$args[$sv get $i]"
        }
    }

    return $args
}

namespace eval ::stc:: {
    namespace export \
        init \
        connect \
        disconnect \
        create \
        delete \
        config \
        get \
        perform \
        reserve \
        release \
        subscribe \
        unsubscribe \
        help \
        apply \
        sleep \
        waituntilcomplete \
        destroy \
        log 
}

proc ::stc::init { } {
    java::call $::stc_int::sJava salInit
}

proc ::stc::connect { args } {
    java::call $::stc_int::sJava salConnect [eval ::stc_int::argsToSv $args]
}

proc ::stc::disconnect { args } {
    java::call $::stc_int::sJava salDisconnect [eval ::stc_int::argsToSv $args]
}

proc ::stc::create { type args } {
    set newObject [java::call $::stc_int::sJava salCreate $type [eval ::stc_int::argsToSv $args]]
    return $newObject
}

proc ::stc::delete { handle } {
    java::call $::stc_int::sJava salDelete $handle
}

proc ::stc::config { handle args } {
    java::call $::stc_int::sJava salSet $handle [eval ::stc_int::argsToSv $args]
}

proc ::stc::get { name args } {
    set svValues [java::call $::stc_int::sJava salGet $name [eval ::stc_int::argsToSv $args]]
    return [::stc_int::svToArgs $svValues]
}

proc ::stc::perform { name args } {
    set svValues [java::call $::stc_int::sJava salPerform $name [eval ::stc_int::argsToSv $args]]
    return [::stc_int::svToArgs $svValues]
}

proc ::stc::reserve { CSPs } {
    set svValues [java::call $::stc_int::sJava salReserve [eval ::stc_int::argsToSv $CSPs]]
    return [::stc_int::svToArgs $svValues]
}

proc ::stc::release { CSPs } {
    java::call $::stc_int::sJava salRelease [eval ::stc_int::argsToSv $CSPs]
}

proc ::stc::subscribe { args } {
    return [java::call $::stc_int::sJava salSubscribe [eval ::stc_int::argsToSv $args]]
}

proc ::stc::unsubscribe { args } {
    java::call $::stc_int::sJava salUnsubscribe $args
}

proc ::stc::help { request } {
    return [java::call $::stc_int::sJava salHelp $request]
}

proc ::stc::apply { } {
    java::call $::stc_int::sJava salApply
}

proc ::stc::sleep {seconds} {
	set stc_sleep_flag 0
	after [expr $seconds * 1000] set ::stc_sleep_flag 1
	vwait stc_sleep_flag 
}

proc ::stc::waituntilcomplete {} {
    waitUntilComplete
}

proc ::stc::waitUntilComplete {} {
    set doWaiting 1
    while {$doWaiting != 0} {
      set currTestState [stc::get sequencer1 -state]
      switch -exact -- $currTestState {
         PAUSE {
            set doWaiting 0
         }
         IDLE {
            set doWaiting 0
         }
         default {
         }
      } 
      ::stc::sleep 1
    }
	return $currTestState      
}

proc ::stc::log { level message } {
    java::call $::stc_int::sJava salLog $level $message
}

proc ::stc::view { handle } {
    set out [java::field System out]
    set adapter [java::new com.caw.analyzer.sqlite.StcPcAdapter $handle]
    $out println "handle=$handle"
    set viewer [java::call com.spirent.tc.ui.core.PCViewer showPc $adapter]
}

proc ::stc::viewDetails { handleList } {
    set out [java::field System out]
    set adapterList [java::new java.util.ArrayList]
    foreach handle $handleList {
        set adapter [java::new com.caw.analyzer.sqlite.StcPcAdapter $handle]
        $out println "detail handle=$handle"
        $adapterList add $adapter
    }
    set viewer [java::call com.spirent.tc.ui.core.PCViewer showPcs $adapterList]
}

stc::init
