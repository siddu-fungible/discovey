package require SpirentTestCenter

set cspList "//10.100.21.7/11/5 //10.100.21.7/11/6"
# This is a sample mdio configuration file, be sure the hardware 
# support Ethernet 10Gig to test with these files
set fileName1 "jdsu802_3ae45.xml"
set fileName2 "ieee802_3ba.xml"
set L2TestFile1 [file join [file dirname [info script]] $fileName1]
set L2TestFile2 [file join [file dirname [info script]] $fileName2]

#####################################################################
# setup
foreach csp $cspList {
    stc::create port \
        -under project1 \
        -location $csp 
}

set ports [stc::get project1 -children-port]

stc::perform attachPorts 

#Load L2 test file to all available ports
stc::perform L2TestLoadTemplate -FileName $L2TestFile1

#Reset default setting for all available ports
stc::perform L2TestLoadTemplate -LoadDefault true

#Load different L2 Test file for different port
#For the first port, loading with $L2TestFile1 
stc::perform L2TestLoadTemplate -Port [lindex $ports 0] -FileName $L2TestFile1

#For the second port, loading with $L2TestFile2
stc::perform L2TestLoadTemplate -Port [lindex $ports 1] -FileName $L2TestFile2

#Reset default setting for individual port
stc::perform L2TestLoadTemplate -Port [lindex $ports 0] -LoadDefault true
stc::perform L2TestLoadTemplate -Port [lindex $ports 1] -LoadDefault true

stc::perform chassisDisconnectAll
stc::delete project1

