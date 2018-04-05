#!/volume/perl/bin/perl -w
#-----------------------------------------------------------------------+
#
#   To enable RT only debugging, add the following line to your .pl file
#       $JT::FACILITY_LOG_LEVEL{RT} = 'DEBUG';
#
#-----------------------------------------------------------------------+
 
#-------------------------------------------------------+
# Here are a list of issues that need to be resolved or kept in mind:
#
#  Multiple chassis addressing needs to be tested.
#
#-------------------------------------------------------+

package SpirentHLTAPIforPerl;

use JT;
#use tt_notify;
use JT::Scaling;
use RT;
use POSIX 'strftime';
use strict;
use warnings;
use XML::Simple;
require Data::Dumper;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw($STC_MODULE_INITIALIZED);

use vars qw(@ISA $VERSION );
@ISA = qw(RT);
$VERSION = do { my @r = (q$Change: 855331 $ =~ /\d+/g); sprintf "%d."."%02d" x $#r, @r };

our $STC_MODULE_INITIALIZED = undef;

my $_HLTAPI_VERSION = '4.81';

BEGIN {
    # minimum version
    # use constant VERSION => "1.0";
    # use constant INTERNAL_VERSION => "1.00 Beta";
    #@EXPORT = qw(get_next_mac);

}

sub chk_chassis_version {
    my $host = shift;
    my $params = shift;
    
    my ($stc_install_dir, $firmware);
    
    if (exists $ENV{STC_INSTALL_DIR}) {
        $stc_install_dir = $ENV{STC_INSTALL_DIR};
        
        if (exists $ENV{STC_VERSION}) {
           $firmware = $ENV{STC_VERSION};
        } else {
            ($firmware) = $stc_install_dir =~ /(\d+.\d+)/;
            unless ($firmware) {
                eval {
                    my $simple = XML::Simple->new();
                    my $data   = $simple->XMLin("$stc_install_dir/ILVersion.xml");
                    $firmware = $data->{Version};
                };
                if ($@) {
                    $firmware = "2.20";
                }
                $firmware = "2.20" unless ($firmware);
            }
        }
        put_log( level => 'INFO', msg => "TestCenter library location specified via environment variable." );
    } else {    
        # telnet to test center to get chassis firmware version
        my $spt;
        foreach (1..3) {
            $spt = JT->new(host=>"$host", user=>'admin', password=>'spt_admin', os=>'generic', slow_delay=>1);
            if ( $spt ) {
                $spt->cmd(cmd=>'version', pattern=>'admin', slow=>1);
                $firmware = $spt->get_response();
                last if $firmware;
                $spt->close();
            } elsif ($_ == 3) {
                put_log( level => "ERROR", msg => "Failed to detect TestCenter firmware version");
                $firmware = '';
            }
        }
        $spt->close() if $spt;
        put_log( level => 'INFO', msg => "TestCenter firmware string gotten by connecting with the chassis: $firmware" );        
        # change firmware from 'Chassis OS = 2.15.0111' to just '2.15'
        # N-11U chassis "Version : 1.0.0 \r\nChassis Version : chos-4.31.1696"
        # STCv chassis "Version : tmos-4.30.4143 0"
        if ($firmware =~ /chassis.*?(\d+.\d+)/i) {
            $firmware = $1;
        } else {
            $firmware =~ /(\d+.\d+)/;
            $firmware = $1;
        }
        if ($firmware) {
            my $OS_Type = "";
            if ($^O eq "linux") {
                $OS_Type = "Linux";
            } elsif ($^O eq "freebsd") {
                JT::error_handler('HARD', "FreeBSD is only supported on library versions 2.32 and higher.", JT::ABORT)
                    if ($firmware < 2.32);
                JT::error_handler('HARD', "FreeBSD must be used in conjunction with Spirent Lab Server.", JT::ABORT)
                    unless exists $params->{"X-MY-LABSERVER-ADDR"};

                $OS_Type = qx/uname -r/;
                if ($OS_Type  =~ /6./) {
                	$OS_Type = "FreeBSD63";
                } else {
		            $OS_Type = "FreeBSD71";
                }
            }
	        put_log( level => 'INFO', msg => "TestCenter library location derived from chassis firmware version: $firmware" ); 
            put_log( level => 'INFO', msg => "TestCenter library detected $OS_Type operating system.");
            $stc_install_dir = '/volume/labtools/lib/Spirent/Spirent_TestCenter_' . $firmware . "/Spirent_TestCenter_Application_$OS_Type/";
            put_log( level => 'INFO', msg => "Loading library from $stc_install_dir");
        }
        put_log( level => 'INFO', msg => "TestCenter library location derived from chassis firmware version." );        
    }    
    
    return $stc_install_dir, $firmware;
    
}

sub get_hltapi_for_perl_version {
    my $host = shift;
    my $params = shift;
    
    my ($hltapi_install_dir, $hltapi_for_perl_dir);

    if (exists $ENV{SPIRENT_HLTAPI_INSTALL_DIR}) {
        $hltapi_install_dir = $ENV{SPIRENT_HLTAPI_INSTALL_DIR};
        if (exists $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR}) {
           $hltapi_for_perl_dir = $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR};
        } 
        put_log( level => 'INFO', msg => "HLTAPI library location specified via environment variable." );
    } else {
        if (exists $ENV{SPIRENT_TAPI_VERSION}) {
            if ($_HLTAPI_VERSION != $ENV{SPIRENT_TAPI_VERSION}) {
                put_log( level => 'RT:WARN', msg => " HLTAPI library version in SpirentHLTAPIforPerl.pm: $_HLTAPI_VERSION is not same as $ENV{SPIRENT_TAPI_VERSION} specified by environment variable" );
            }
            $_HLTAPI_VERSION = $ENV{SPIRENT_TAPI_VERSION};
        }
        put_log( level => 'INFO', msg => "To find HLTAPI library version: $_HLTAPI_VERSION" );
        $hltapi_install_dir = "/volume/labtools/lib/Spirent/HLTAPI/$_HLTAPI_VERSION/SourceCode";
        $hltapi_for_perl_dir = "/volume/labtools/lib/Spirent/HLTAPI/$_HLTAPI_VERSION/SourceCode/hltapiForPerl";
    }
    unshift(@INC,$hltapi_for_perl_dir);

    return $hltapi_install_dir, $hltapi_for_perl_dir;

}

#-------------------------------------------------------+
# Intialize the environment.
# Returns a handle to Object RT
# Inputs:
#     Host: ip address of the TestCenter chassis
#     Version: (optional) version of the library
#     Params: (optional) parameters to JT
#
#    Returns a handle to the RT object or undef.
#
#    Example:
#
#       my $rt = RT->new (host => "192.168.0.1", version => "2.0");
#        die "Cannot get handle to RT" unless ($rt);
#
#-------------------------------------------------------+
sub new {     
    my $classname = shift;
    my $sub = sub_name();
    my $options_display = Data::Dumper::Dumper(\@_);
    put_log( level=>"RT:DEBUG", msg=>"In $sub" );
    put_log( level=>"RT:DEBUG", msg=>"\n". $options_display);
    my ($args, $arg_str) = get_args( [ qw(HOST VERSION PARAMS MEMORY_MONITOR) ], @_);
    my $host = $args->{HOST};
    my $version = $args->{VERSION};
    my $params = $args->{PARAMS};
    my $memory_monitor = uc($args->{MEMORY_MONITOR}) || 'FALSE';

    return error_handler( 'HARD', "The hostname was not supplied. " ) unless (defined $host);
 
    my ($stc_install_dir, $firmware, $hltapi_install_dir, $hltapi_for_perl_dir);
    my $self = {};
 
    unless ($STC_MODULE_INITIALIZED) {
        bless( $self, ref($classname) || $classname );

        $self->{LOG_LEVEL} = JT::get_log_level($JT::LOG_LEVEL);
        
        my ($status, $service);
        my $caller_pkg = caller() || '';

        #if in JT Test environment, services status check has already been done so don't need to check again    
        if ($caller_pkg !~ /^JT::Device/i) {
           # ($status, $service) = &chk_service_status(services=>["JT"]);
           # if ($status == JT::FALSE) {
            #    JT::error_handler('HARD', "There is a problem with [$service->{'name'}] with status [$service->{'status'}]", JT::ABORT);
           # }
        }

        my $jt_ref = new JT( host => $host, params => $params);
        return error_handler( 'HARD', "[$host] new: Cannot open test session" ) unless (defined $jt_ref);
        $self->{JTREF} = $jt_ref;

        ($stc_install_dir, $firmware) = chk_chassis_version($host, $params);
            
        put_log( level => 'INFO', msg => "TestCenter library location: $stc_install_dir" );
        put_log( level => 'INFO', msg => "TestCenter firmware version: $firmware" );
        
        $STC_MODULE_INITIALIZED->{FIRMWARE_VERSION} = $firmware;
        $STC_MODULE_INITIALIZED->{STCDIR} = $stc_install_dir;
        $STC_MODULE_INITIALIZED->{OBJECT} = $self;
        $STC_MODULE_INITIALIZED->{MEMORY_MONITOR} = $memory_monitor;
        if (exists $params->{"X-MY-LABSERVER-ADDR"}) {
			#Lab server todo
        }

        # workaround nfs file permission issue
        my $filename = "$stc_install_dir" . 'FileEntry.db';
        my($dev, $ino, $mode, $nlink, $uid, $gid, $rdev,
           $size, $atime, $mtime, $ctime, $blksize, $blocks) = stat($filename);
        
        if ((defined $uid && $uid eq 65534) || (defined $gid && $gid eq 65534)) {
            if (unlink $filename) {
                put_log('TRACE', "File $filename deleted due to invalid nfs owner");
            }
        }

    } else {   
        ($stc_install_dir, $firmware) = chk_chassis_version($host, $params);
        return error_handler( 'HARD', 
            "Firmware mismatch.  Requested: $STC_MODULE_INITIALIZED->{FIRMWARE_VERSION} -- $host: $firmware " )
                if ($firmware != $STC_MODULE_INITIALIZED->{FIRMWARE_VERSION});
        $self = $STC_MODULE_INITIALIZED->{OBJECT};
    }

    ($hltapi_install_dir, $hltapi_for_perl_dir) = get_hltapi_for_perl_version();
    put_log( level => 'INFO', msg => "HLTAPI library location: $hltapi_install_dir" );
    put_log( level => 'INFO', msg => "HLTAPI for Perl location: $hltapi_for_perl_dir" );
    $STC_MODULE_INITIALIZED->{HLTAPI_DIR} = $hltapi_install_dir;
    $STC_MODULE_INITIALIZED->{HLTAPI_FOR_PERL_DIR} = $hltapi_for_perl_dir;
    
    $ENV{TCLLIBPATH} = defined $ENV{TCLLIBPATH} ? $ENV{TCLLIBPATH} : $STC_MODULE_INITIALIZED->{STCDIR}; 
    $ENV{PERL5LIB}   = defined $ENV{PERL5LIB} ? $ENV{PERL5LIB} : $STC_MODULE_INITIALIZED->{HLTAPI_FOR_PERL_DIR};
    $ENV{TCLLIBPATH} = "$STC_MODULE_INITIALIZED->{STCDIR} ". $ENV{TCLLIBPATH};
    $ENV{TCLLIBPATH} = "$STC_MODULE_INITIALIZED->{HLTAPI_DIR} ". $ENV{TCLLIBPATH};
    $ENV{PERL5LIB}   = "$STC_MODULE_INITIALIZED->{HLTAPI_FOR_PERL_DIR} ". $ENV{PERL5LIB};
    
    $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR} = defined $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR} ? $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR} : $STC_MODULE_INITIALIZED->{HLTAPI_FOR_PERL_DIR}; 
    $ENV{JT_ENV}     = 1;
    #unshift (@INC, "/homes/jgarapat/demo_for_hlpapi/JT_MOD");
    #print "INC is @INC\n\n\n";
    require "sth.pm"; 
    
    return $self;
} 

#
# Exception handling: close session if script aborts abnormally
#
sub DESTROY {
    my $self = shift;
    (my $package, my $filename, my $line) = caller;
    JT::put_log(level => 'RT:DEBUG', msg=>"destroy called from: package: $package  file: $filename  line: $line");
    JT::put_log(level=>'RT:INFO', msg=>'JTAPI Destroy');

     if (defined $JT::global_put_log_file_handle && $JT::global_put_log_file_handle) {
         CORE::close $JT::global_put_log_file_handle;
     }
}

sub _close { 

    #HLTAPI cleanup call in order to Release ports, disconnect chassis, delete project
    my %intStatus = sth::cleanup_session ();

    return JT::TRUE;
}

sub get_os { 'Spirent' }
sub get_version { "$_HLTAPI_VERSION"}


1;


