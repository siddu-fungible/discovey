Set up Tcl 

If you are using an existing Tcl installation, or if you downloaded Tcl from a source other than the Spirent support site (http://support.spirent.com), you must set up Tcl for use with Spirent TestCenter by following the instructions below. 

Note:  [FreeBSD users] Before you follow the set up instructions, you must set the correct LS-Client parameters in FreeBSD, and make sure LS session is established between the LS server and FreeBSD. 

Use these commands: 
setenv STC_SERVER_ADDRESS x.x.x.x (x.x.x.x is Lab Server address) setenv STC_SESSION_NAME __NEW_TEST_SESSION__ 
setenv LD_LIBRARY_PATH /home/Executer/bin/Spirent/Current (STC installer path) 

To set up Tcl to run with Spirent TestCenter: 
1 Type tclsh at the command line.
    The Tcl prompt % displays.
2  Type set auto_path and press enter.
     The list of Tcl/lib directories recognized by Tcl displays.
3    Select a directory to use with Spirent TestCenter.
4    Create an stc2.0 sub-directory in the Tcl/lib directory you selected.
5     Locate pkgIndex.tcl in the Spirent TestCenter Application directory in your Spirent TestCenter directory. For example:

	• Windows: Spirent_TestCenter_x.xx\Spirent _TestCenter_Application
	• Solaris: Spirent_TestCenter_x.xx/Spirent_TestCenter_Application_Solaris
	• Linux: Spirent_TestCenter_x.xx/Spirent_TestCenter_Application_Linux

6  Copy pkgIndex.tcl to the Tcl/lib/stc2.0 directory (created in Step 4).
    For example, if your Tcl installation is in the path ~/pkg/tcl the path to the copy of the file should be ~/pkg/tcl/lib/stc2.0/pkgIndex.tcl 
7  Modify the copy of the pkgIndex.tcl file. The file contains the following lines (use the Spirent TestCenter version identifier that matches your installation):
	package ifneeded Spirent TestCenter x.xx [list source [file join STC_INSTALL_DIR SpirentTestCenter.tcl]] 
	package ifneeded stc x.xx [list source [file join STC_INSTALL_DIR SpirentTestCenter.tcl]]
8  Replace both instances of the STC_INSTALL_DIR keyword with the Spirent TestCenter installation directory path.
   For the Windows OS, use the forward slash character (‘/’) as a delimiter. 
   For non-Windows OS, use the forward slash character (/) as a delimiter. For example: 
	•  C:\Program Files\Spirent Communications\Spirent TestCenter x.xx\Spirent TestCenter Application (for Windows) 
	• /opt/SW/Spirent Communications/Spirent TestCenter x.xx/Spirent TestCenter Application (Solaris or Linux)
    The resulting, modified version of pkgIndex.tcl would look like the following (use the Spirent TestCenter version identifier that matches your installation): 
	package ifneeded Spirent TestCenter x.xx [list source [file join "/opt/SW/Spirent Communications/Spirent TestCenter x.xx/Spirent TestCenter Application" SpirentTestCenter.tcl]] 
	package ifneeded stc x.xx [list source [file join "/opt/SW/Spirent Communications/Spirent TestCenter x.xx/ Spirent TestCenter Application" SpirentTestCenter.tcl]] 
9  [FreeBSD users] Add the Spirent TestCenter installation directory to the front of your LD_LIBRARY_PATH variable. For example, in the bash shell, type:  export LD_LIBRARY_PATH=/STC_INSTALL_DIR. 
To avoid typing this command each time you log on, add this command to the .bash_profile file. 
10  [FreeBSD users] 	
	• [FreeBSD 6.3] export LD_PRELOAD=libpthread.so.2
	• [FreeBSD 7.1] export LD_PRELOAD=libthr.so.3
	• [FreeBSD 8.1] export LD_PRELOAD=libthr.so.3

Tcl is ready to be used with Spirent TestCenter.






