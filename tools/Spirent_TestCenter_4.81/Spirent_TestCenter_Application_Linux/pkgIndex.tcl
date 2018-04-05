# SpirentTestCenter Tcl package index file.
# This file is sourced either when an application starts up or
# by a "package unknown" script.  It invokes the
# "package ifneeded" command to set up package-related
# information so that packages will be loaded automatically
# in response to "package require" commands.  The installer
# must fill in the directory where SpirentTestCenter.tcl can
# be found; this may differ between SpirentTestCenter
# and SpirentTestCenterConformance depending on the platform.

set vers "4.81"

package ifneeded SpirentTestCenterConformance 4.81 "[list set env(STC_CONFIGURATION_FILE) ctsbll.ini]; [list source [file join CTS_INSTALL_DIR SpirentTestCenter.tcl]]; [list package provide SpirentTestCenterConformance 4.81]"
package ifneeded SpirentTestCenter 4.81 [list source [file join $dir SpirentTestCenter.tcl]]
package ifneeded stc 4.81 [list source [file join $dir SpirentTestCenter.tcl]]
package ifneeded stclib 4.81 [list source [file join $dir stclib.tcl]]

#Creating HLTAPI Path
set hltDir [string trim $dir '\"']
set hltDir [string trimright $hltDir '/']
set hltDir "$hltDir/HltAPI/SourceCode/"

package ifneeded SpirentHltApi 4.81 [list source [file join "$hltDir" hltapi_5.10_stc_2.10.tcl]]
package ifneeded sth 4.81 [list source [file join "$hltDir" hltapi_5.10_stc_2.10.tcl]]
package ifneeded SpirentHltApiWrapper 4.81 [list source [file join "[set hltDir]hltapiWrapper/" sth_wrapper.lib]]