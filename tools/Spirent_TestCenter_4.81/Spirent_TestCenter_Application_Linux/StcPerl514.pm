package StcPerl;
use strict;
use Config;
use Cwd;
use File::Spec;

BEGIN {
  use vars qw($VERSION @ISA @EXPORT @EXPORT_OK);
  require Exporter;
  @ISA = qw(Exporter DynaLoader);
  @EXPORT = qw();
  $VERSION = '1.0';

  my $orig_dir = getcwd();  
  $ENV{'TCL_RUNNING_DIR'} = "$orig_dir/";

  #########################################
  # get stc directory
  #########################################
  if ($ENV{'STC_PRIVATE_INSTALL_DIR'} eq "") { 
    use File::Basename;
    my @fullName = grep /StcPerl514.pm/, map {"$INC{$_}\n"} keys %INC;  
    my ($name, $stc_dir) = fileparse($fullName[0]);
    chop($stc_dir);  
    $ENV{'STC_PRIVATE_INSTALL_DIR'} = Cwd::abs_path($stc_dir);    
  } 
  my $iniPath = File::Spec->catfile( $ENV{'STC_PRIVATE_INSTALL_DIR'}, "stcbll.ini" );
  unless (-e $iniPath) {   
    print "$ENV{'STC_PRIVATE_INSTALL_DIR'} is not a valid STC install directory.";
    exit();
  } 
}

sub _toString {
  my $arg = shift;
  my $ret = "";
  if (ref($arg) eq "HASH") {
    while (my($key,$value) = each %$arg) {
      $ret .= $key  . " {" . _toString($value) . "} ";
    }
  } elsif (ref($arg) eq "ARRAY") {
    for my $value (@$arg) { 
      if ($value =~ m/\S+\s+\S+/ or ref($value) eq "ARRAY" or ref($value) eq "HASH") { 
        $ret .= " {" . _toString($value) . "} " ;
      } else {
        $ret .= " " . _toString($value);
      }
    }
  } else {
	  $ret = "" . $arg;
  }
  return $ret;
}

sub _packArgs {
  my ($sv, @args) = @_;
  my $i = 0;
  for my $value (@args) { 
    if ($i % 2 == 0) { 
      $sv->push("-$value");
    } else {
      $sv->push(_toString($value));
    }
    $i += 1;
  }
}

sub new {
  my $package = shift;
  _checkConfig();  
  
  use sPerl514mt;
  sPerl514mtc::salInit();
  return bless({}, $package);
}

sub _checkConfig {
   my $msg = "The Perl configuration is unsupported: ";
   
   if ($] !~ m/5.008|5.014/) {
      print "$msg Only Perl versions 5.8 and 5.14 are supported.";
      exit();
   }

   my $perl_V = Config::myconfig();

   if ($] =~ m/5.008/) {  
      if($perl_V !~ m/use64bitint=undef/) { 
         print "$msg re-install Perl with use64bitint=undef.";
         exit();
      }
   
      if($^O =~ m/Win32/) {
         if ($perl_V !~ m/usethreads=define use5005threads=undef useithreads=define usemultiplicity=define/) {
            print "$msg re-install Perl with threads support.";
            exit();
         }
      } elsif($^O !~ m/linux/ && $^O !~ m/freebsd/) {      
         print "$msg Operating system is unsupported.";
         exit();
      } 
   } else {      
      if ($perl_V !~ m/useithreads=define, usemultiplicity=define/) {
         print "$msg re-install Perl with threads support.";
         exit();
      }

      if($^O =~ m/Win32/) {
         if($perl_V !~ m/use64bitint=undef/) { 
            print "$msg 64 bit is not supported on Windows.";
            exit();
         }         
      } elsif($^O !~ m/linux/) {
         print "$msg Operating system is unsupported.";            
         exit();
      }         
   }
}

##################################################################
#
# Procedure name: destroy
# Input arguments: 
# Output arguments:
# Description: This routine cleans up the project(s), 
# disconnects from all the chasssis, and performs BLL cleanup.
# Once this command is called, subroutines in the StcPerl
# package are no longer allowed.
##################################################################
sub destroy {
   perform("","ChassisDisconnectAll");
   perform("","ResetConfig", config=>"system1");
   sPerl514mtc::salShutdownNoExit();
   my $self = shift;
   my $old_class = ( grep {
      $_ !~ /__PACKAGE__/
   } ( Class::ISA::super_path( ref($self) ) ) )[0];
   bless $self, $old_class;
}

####################################
#  wrap the salInit function
#  void salInit(void);
####################################
sub init {  
  #sPerl514mtc::salInit();
}

####################################
#  wrap the salShutdown function
#  void salShutdown(void);
####################################
sub shutdown { 
  sPerl514mtc::salShutdown();
}

####################################
#  wrap the salLog function
#  void salLog(std::string logLevel, std::string msg);
####################################
sub log { 
  my($head, $logLevel, $msg) = @_;
  sPerl514mtc::salLog($logLevel, $msg);
}

####################################
#  wrap the salCreate function
#  std::string salCreate(std::string type, StringVector propertyPairs);
####################################
sub create {  
  my($head, $type, @pairs) = @_;
  my($sv, $retHandle);
  $sv = sPerl514mt::StringVector->new();
  _packArgs($sv, @pairs);
  $retHandle = sPerl514mtc::salCreate($type, $sv);  
  return $retHandle;
}

####################################
#  wrap the salGet function
#  StringVector salGet(std::string handle, StringVector propertyNames);
####################################
sub get {  
  my($head, $type, @propNames) = @_;  
  my @svecdashes;  
  foreach (@propNames) {
     push(@svecdashes, "-$_");
  }  
  my @retV = @{sPerl514mtc::salGet($type, \@svecdashes)};
  if(scalar(@retV) != 1) {
     for(my $i = 0; $i < scalar(@retV); $i+=2) {        
        $retV[$i] =~ s/-//;        
     }
  }
  return "@retV" unless (wantarray);
  return @retV if (@retV != 1);
  return split(/ +/, $retV[0]);
}

####################################
#  wrap the salSet function
#  void salSet(std::string handle, StringVector propertyPairs);
####################################
sub config {  
  my($head, $type, @pairs) = @_;
  my($i, $sv, $retV);
  $sv = sPerl514mt::StringVector->new();
  _packArgs($sv, @pairs);
  $retV = sPerl514mtc::salSet($type, $sv);
  return $retV;
}

# internal help info
sub _helpInfo {

   my %helpInfo = ( 'create' => {
                                    'desc'    => 'create: -Creates an object in a test hierarchy',
                                    'usage'   => '$stc->create( className, under => parentObjectHandle, propertyName1 => propertyValue1, ... );',
                                    'example' => '$stc->create( \'port\', under=>\'project1\', location => \'//10.1.1.1/1/1\' );'
                                },

                    'config' => {
                                    'desc'    => 'config: -Sets or modifies the value of an attribute',
                                    'usage'   => '$stc->config( objectHandle, propertyName1 => propertyValue1, ... );',
                                    'example' => '$stc->config( $streamHandle, enabled => 1 );'
                                },

                    'get' =>    {
                                    'desc'    => 'get: -Retrieves the value of an attribute',
                                    'usage'   => '$stc->get( objectHandle, propertyName1, propertyName2, ... );',
                                    'example' => '$stc->get( $streamHandle, \'enabled\', \'name\' );'
                                },

                    'perform' => {
                                    'desc'    => 'perform: -Invokes an operation',
                                    'usage'   => '$stc->perform( commandName, propertyName1 => propertyValue1, ... );',
                                    'example' => '$stc->perform( \'createdevice\', parentHandleList => \'project1\', createCount => 4 );'
                                 },

                    'delete'  => {
                                    'desc'    => 'delete: -Deletes an object in a test hierarchy',
                                    'usage'   => '$stc->delete( objectHandle );',
                                    'example' => '$stc->delete( $streamHandle );'
                                 },

                    'connect' => {
                                    'desc'    => 'connect: -Establishes a connection with a Spirent TestCenter chassis',
                                    'usage'   => '$stc->connect( hostnameOrIPaddress, ... );',
                                    'example' => '$stc->connect( $mychassis );'
                                 },

                    'disconnect' => {
                                     'desc'    => 'disconnect: -Removes a connection with a Spirent TestCenter chassis',
                                     'usage'   => '$stc->disconnect( hostnameOrIPaddress, ... );' ,
                                     'example' => '$stc->disconnect( $mychassis );'
                                    },

                    'reserve' =>    {
                                      'desc'   => 'reserve: -Reserves a port group',
                                      'usage'  => '$stc->reserve( CSP1, CSP2, ... );',
                                      'example'=> '$stc->reserve( \'//10.1.1.1/1/1\', \'//10.1.1.1/1/2\' );'
                                    },

                    'release' =>    {
                                      'desc'   => 'release: -Releases a port group',
                                      'usage'  => '$stc->release( CSP1, CSP2, ... );',
                                      'example'=> '$stc->release( \'//10.1.1.1/1/1\', \'//10.1.1.1/1/2\' );'
                                    },

                    'apply'   =>    {
                                      'desc'   => 'apply: -Applies a test configuration to the Spirent TestCenter firmware',
                                      'usage'  => '$stc->apply();',
                                      'example'=> '$stc->apply();'
                                    },

                    'log'     =>    {
                                      'desc'   => 'log: -Writes a diagnostic message to the log file',
                                      'usage'  => '$stc->log( logLevel, message );',
                                      'example'=> '$stc->log( \'DEBUG\', \'This is a debug message\' );'
                                    },                                    

                    'waituntilcomplete' => {
                                             'desc'    => 'waituntilcomplete: -Suspends your application until the test has finished',
                                             'usage'   => '$stc->waituntilcomplete();',
                                             'example' => '$stc->waituntilcomplete();'
                                           },

                    'subscribe' =>         {
                                             'desc'    => 'subscribe: -Directs result output to a file or to standard output',
                                             'usage'   => '$stc->subscribe( parent=>parentHandle, resultParent=>parentHandles, configType=>configType, resultType=>resultType, viewAttributeList=>attributeList, interval=>interval, fileNamePrefix=>fileNamePrefix );',
                                             'example' => '$stc->subscribe( parent=>\'project1\', configType=>\'Analyzer\', resulttype=>\'AnalyzerPortResults\', filenameprefix=>\'analyzer_port_counter\' );'
                                           },

                    'unsubscribe' =>       {
                                             'desc'    => 'unsubscribe: -Removes a subscription',
                                             'usage'   => '$stc->unsubscribe( resultDataSetHandle );',
                                             'example' => '$stc->unsubscribe( $resultDataSetHandle );'
                                           },

                    'destroy' =>           {
                                             'desc'    => 'destroy: -Cleans up the project, disconnects from all the chassis, and unloads the BLL.',
                                             'usage'   => '$stc->destroy();',
                                             'example' => '$stc->destroy();'
                                           }
                  );
}
   

####################################
#  wrap the salHelp function
#  std::string salHelp(std::string info);
####################################
sub help {    
  my($head, $topic) = @_;  
  if($topic eq '' or $topic =~ m/ /) {
     return <<'END'
Usage: 
   $stc->help('commands');
   $stc->help(<handle>);
   $stc->help(<className>);
   $stc->help(<subClassName>);
END
      
   }

  if($topic eq 'commands') {
     my @allCommands;
     my %cmdinfo = _helpInfo();
     foreach (keys %cmdinfo) {
        push(@allCommands, $cmdinfo{$_}{'desc'});
     }
     
     return join("\n", sort(@allCommands)) . "\n";
  }
  my %cmdinfo = _helpInfo();
  if(exists $cmdinfo{"$topic"}) {     
     return "Desc: $cmdinfo{$topic}{'desc'} \nUsage: $cmdinfo{$topic}{'usage'} \nExample: $cmdinfo{$topic}{'example'} \n";    
  }
  return  sPerl514mtc::salHelp($topic);
}

####################################
#  wrap the salConnect function
#  void salConnect(StringVector hostNames);
####################################
sub connect {  
  my($head, @hostName) = @_;
  my($i, $sv);
  $sv = sPerl514mt::StringVector->new();
  for $i ( 0 .. $#hostName )   {
    $sv->push($hostName[$i]);
  }  
  sPerl514mtc::salConnect($sv);
}
####################################
#  wrap the salDisconnect function
#  void salDisconnect(StringVector hostNames);
####################################
sub disconnect {  
  my($head, @hostName) = @_;
  my($i, $sv);
  $sv = sPerl514mt::StringVector->new();
  for $i ( 0 .. $#hostName )   {
    $sv->push($hostName[$i]);
  }  
  sPerl514mtc::salDisconnect($sv);
}

####################################
#  wrap the salDelete function
#  void salDelete(std::string handle);
####################################
sub delete {  
  my($head, $handle) = @_;
  sPerl514mtc::salDelete($handle);
}

####################################
#  wrap the salPerform function
#  StringVector salPerform(std::string commandName, StringVector propertyPairs);
####################################
sub perform {  
  my($head, $type, @pairs) = @_;    
  my $sv = sPerl514mt::StringVector->new();
  _packArgs($sv, @pairs);
  my @retV = @{sPerl514mtc::salPerform($type, $sv)};  
  if (scalar(@retV) == 1) {
     my @values = split(/ /, $retV[0]);   
     return ( scalar(@values) > 1 ) ? @values : $retV[0];
  }
  for(my $i = 0; $i < scalar(@retV); $i+=2) {        
     $retV[$i] =~ s/-//;        
  }  
  return @retV;
}
    
####################################
#  wrap the salReserve function
#  StringVector salReserve(StringVector CSPs);
####################################
sub reserve {  
  my($head, @chassislist) = @_;
  my($i, $sv);
  $sv = sPerl514mt::StringVector->new();
  for $i ( 0 .. $#chassislist )   {
    $sv->push($chassislist[$i]);
  }  
  sPerl514mtc::salReserve($sv);
}
    
####################################
#  wrap the salRelease function
#  void salRelease(StringVector CSPs);
####################################
sub release {  
  my($head, @pairs) = @_;
  my($i, $sv, @retV, @retInfo);
  $sv = sPerl514mt::StringVector->new();
  for $i ( 0 .. $#pairs )   {
    $sv->push($pairs[$i]);
  }  
  sPerl514mtc::salRelease($sv);
}
    
####################################
#  wrap the salSubscribe function
#  std::string salSubscribe(StringVector inputParameters);
####################################
sub subscribe {  
  my($head, @pairs) = @_;
  my($i, $sv, $retV);
  $sv = sPerl514mt::StringVector->new();
  _packArgs($sv, @pairs);
  $retV = sPerl514mtc::salSubscribe($sv);
  return $retV;
}
    
####################################
#  wrap the salUnsubscribe function
#  void salUnsubscribe(std::string handle);
####################################
sub unsubscribe {  
  my($head, $handle) = @_;
  sPerl514mtc::salUnsubscribe($handle);
}

####################################
#  wrap the salApply function
#  void salApply(void);
####################################
sub apply {  
  sPerl514mtc::salApply();
}
####################################
#  sleeps for specified number of seconds.
####################################
sub sleep { 
  my($head, $sec) = @_;
  sleep $sec;
}

####################################
#  wait until the sequencer has completed 
#  with optional timeout in secs.
#  returns the teststate of the sequencer.
####################################
sub waituntilcomplete  {  
  my($head, @timeout) = @_;  
  my $myTimer = 0;
  my $timeOutVal = 0;
  my $argc = $#timeout + 1;  
  my $self = shift;
  
  if(($argc > 0 )&&($argc != 2)) {
    print "ERROR: Valid Attribute Value Pairs not found \n";     
  } elsif ($argc == 2) {
    my $name = lc($timeout[0]);
    if( $name ne "timeout" ) {
      print "ERROR: Invalid Attribute name $name\n"; 
    } else {
      $timeOutVal = $timeout[1];
    }
  }
 
  my $sequencer = $self->get("system1", "children-sequencer");  

  while (1) {
    my $currTestState = $self->get($sequencer, "state");    
    last if($currTestState eq "PAUSE" or $currTestState eq "IDLE");
    CORE::sleep(1); 
    $myTimer++;
    if($timeOutVal > 0) {
      if ( $myTimer >= $timeOutVal ) {
      	print "ERROR: Timeout \n";
        last;
      }
    } 
  }
  
  if (defined($ENV{"STC_SESSION_SYNCFILES_ON_SEQ_COMPLETE"})
    && $ENV{"STC_SESSION_SYNCFILES_ON_SEQ_COMPLETE"} == 1) {
    my %retV = perform("", "CSGetBllInfo");
   
    if ($retV{"-ConnectionType"} =="SESSION") {
      perform("", "CSSynchronizeFiles");
    }
  }

  return $self->get($sequencer, "teststate");
}

END {
  sPerl514mtc::salShutdown($?);
}

1;
__END__
