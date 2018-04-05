variable stc::scriptParameters

set savedTime [ clock format [clock scan now] -format "%a %b %d %H:%M:%S %Y" ]

set hFile [open $stc::scriptParameters(-launcherFileAbsPath) w]
puts $hFile "
# Spirent TestCenter Tcl Launcher Script
# Saved $savedTime
# Filename: $stc::scriptParameters(-launcherFile)
# Comments: 
# 
# 

source \[ file join \[ file dirname \[ info script ] \] {$stc::scriptParameters(-logicFile)} ]

init
config \[list $stc::scriptParameters(-portList) ]
configResultLocation \[ file dirname \[ info script ] ] 
configMiscOptions
connect
apply
set test_status \[eval \[concat run ]]
disconnect
return \$test_status 

"

close $hFile

