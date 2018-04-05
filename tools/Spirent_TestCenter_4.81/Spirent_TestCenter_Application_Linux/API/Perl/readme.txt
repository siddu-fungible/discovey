Set up Perl

Please consult the Spirent TestCenter Base and Test Package Release Notes for supported versions of Perl. Release notes are included on the DVD and are available as a “Related Resource” on each software download page (http://support.spirent.com). Install a supported version of Perl on your workstation and then set it up to work with Spirent TestCenter Automation.

[FreeBSD users and any 64-bit OS users] Before you follow the set up instructions, you must set the correct LS-Client parameters in FreeBSD, and make sure LS session is established between the LS server and FreeBSD.

Use these commands:

setenv STC_SERVER_ADDRESS x.x.x.x (x.x.x.x is Lab Server address)
setenv STC_SESSION_NAME   __NEW_TEST_SESSION__
setenv LD_LIBRARY_PATH /home/Executer/bin/Spirent/Current (STC installer path)

To set up Perl to run with Spirent TestCenter:

1 Copy the SpirentTestCenter.pm file to the Perl installation's module lib directory on your workstation. 
For example, for Perl 5.8.8: 
/usr/local/lib/perl5/site_perl/5.8.8/i686-linux

2 Open the SpirentTestCenter.pm file and locate the use lib path.

3 Edit the library path so that it points to the Spirent TestCenter Application directory.
For example: 
use lib /home/.../Spirent_TestCenter_Application_Linux

4 [FreeBSD users] Add the Spirent TestCenter installation directory to the front of your LD_LIBRARY_PATH variable. For example, in the bash shell, type: export LD_LIBRARY_PATH=/STC_INSTALL_DIR. 
To avoid typing this command each time you log on, add this command to the .bash_profile file.

5 [FreeBSD users] If you are running Perl with threads disabled, set the LD_PRELOAD environment variable.
If this variable is not set correctly, you may see an error message similar to this: 
"Fatal error 'Recurse on a private mutex.'" 
If you are running Perl with threads enabled, you should not set this variable.
	[FreeBSD 6.3] export LD_PRELOAD=libpthread.so.2
	[FreeBSD 7.1] export LD_PRELOAD=libthr.so.3
	[FreeBSD 8.1] export LD_PRELOAD=libthr.so.3

Perl is ready to be used with Spirent TestCenter Automation.