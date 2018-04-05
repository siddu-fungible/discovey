package SpirentTestCenter;

# This module is for the installation. The user needs to put it into 
# the correct directory inside their Perl installation.
# For example: 
# Linux    -> /usr/local/lib/perl5/site_perl/5.8.8/i686-linux
# Windows  -> C:/perl/site/lib


# Modify the next line to point to your STC application path.
# This is just an example.
use lib "/home/user/Spirent_TestCenter_2.3x/";

use if scalar($] =~ m/5.008/), "StcPerl";
use if scalar($] =~ m/5.014/), "StcPerl514";
if ($] !~ m/5.008|5.014/) {
   print "The Perl configuration is unsupported: Only Perl versions 5.8 and 5.14 are supported.";
   exit();
}

BEGIN {
  use vars qw($VERSION @ISA @EXPORT @EXPORT_OK);
  require Exporter;
  @ISA = qw(Exporter DynaLoader);
  @EXPORT = qw();
  $VERSION = '1.0';
}

sub new {
  my $package = shift;
  return bless({}, $package);
}

END {
}

1;
__END__
