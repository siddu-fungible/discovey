package sth;

use Cwd;
use File::Spec;
use File::Copy;
use File::Basename;
use strict;
use warnings;

require Data::Dumper;

use Socket;

require Exporter;
our @ISA = qw(Exporter);

my $TS ;
my $JT_ENV_FLAG = defined $ENV{JT_ENV} ? $ENV{JT_ENV} : 0;
use vars qw($TMP);

my $log_name;
my $log_dir;

BEGIN {
    use constant TRUE => 1;
    use constant FALSE => 0;
    use constant ERROR => -1;
    use constant ABORT => -2;
    my $JT_ENV_FLAG = defined $ENV{JT_ENV} ? $ENV{JT_ENV} : 0;

	my $perlv = sprintf("%vd", $^V);
    print "Current OS: $^O; perl version: $perlv\n";
	
    # get the protocol value to use in all the socket connections
    my $proto = getprotobyname('tcp');

    # Create the temporary server socket
    # A zero value for the port will allow the system to assign us an unused number
    my $tmp_port = 0;
    socket(Server, PF_INET, SOCK_STREAM, $proto);
    bind(Server, sockaddr_in($tmp_port, INADDR_ANY));
    listen(Server,SOMAXCONN);

    # Get the port number assigned by the system
    my $mysockaddr = getsockname(Server);
    my ($bnd_port, $myaddr) = sockaddr_in($mysockaddr);
    my ($tcl_path, $hltapiserver);
    
    if ($JT_ENV_FLAG) {
        #setting default tcl path
        if ($^O =~/win/i) {
            $tcl_path = defined $ENV{STC_TCL}? $ENV{STC_TCL} : 'C://Tcl//bin//tclsh84.exe';
        } else {
            $tcl_path = defined $ENV{STC_TCL}? $ENV{STC_TCL} : "/volume/perl/bin/tclsh8.4";
			print "<HLTAPI WARN> Env variable STC_TCL not defined, hence Tcl path defaults to \"/volume/perl/bin/tclsh8.4\" \
<<Recommended to define STC_TCL env with valid Tcl path>>";
        }
        #Log file naming
        $log_dir = $JT::LOG_DIR;
        $log_dir = "." if !(defined $log_dir);
        $log_name = "$JT::SCRIPT_NAME.$JT::PID.hltlog";
        
		my $dirname = dirname(__FILE__);
        my @base_dir = defined $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR} ? $ENV{SPIRENT_HLTAPI_FOR_PERL_DIR} : $dirname;
        $hltapiserver = "|$tcl_path " . File::Spec->catdir(@base_dir, 'hltapiserver.srv') . " $bnd_port 120 log $log_dir $log_name INFO";
    } else {
        if (defined $ENV{STC_TCL}) {
            $tcl_path = $ENV{STC_TCL};
        } else {
            print "<error> STC_TCL env not defined, please define.\n";
            exit;
        }
        $log_dir = defined $ENV{HLTAPI_FOR_PERL_LOG}? $ENV{HLTAPI_FOR_PERL_LOG} : getcwd();
        $log_name = $0;
        if($log_name =~ /\./) {
            my @tmp_array = split(/\./, $log_name);
            $log_name = "$tmp_array[0]" . ".hltlog";
        } else {
            $log_name = "hltapiforperl.hltlog";
        }
		
		my $dirname = dirname(__FILE__);
        my @base_dir = $dirname;
        $hltapiserver = "|$tcl_path " . File::Spec->catdir(@base_dir, 'hltapiserver.srv') . " $bnd_port 120 log $log_dir $log_name INFO";
    }
    #print "DEBUG : Log Directory: $log_dir\n Log Name: $log_name \n";

    open(TMP, $hltapiserver);
    #print"DEBUG :Tcl Server connect... have spawned server process \n";

    # Now wait for the spawned process to connect up to us
    my $asock = accept(Client,Server);
    my($clnt_port,$iaddr) = sockaddr_in($asock);
    my $name = gethostbyaddr($iaddr,AF_INET);
    my $msg = "connection from $name [" . inet_ntoa($iaddr) . "] at port $clnt_port";
    #print"DEBUG :Tcl Server connect... $msg \n";

    # The spawned process sends over the port associated with it's newly created socket
    my $spwn_port = <Client>;
    $spwn_port =~ s/\s+$//;
    #print"DEBUG :Tcl Server connect... server port of spawned process: $spwn_port \n";

    # Connect to the spawned process
    my $remote = "127.0.0.1";
    my $raddr   = inet_aton($remote);
    my $xaddr   = sockaddr_in($spwn_port, $raddr);

    my $sock;
    socket($sock, PF_INET, SOCK_STREAM, $proto);
    connect($sock, $xaddr);

    # Set the socket to autoflush
    my $oldfh = select($sock);
    $| = 1;
    select($oldfh);

    $TS = $sock;

    # Print the auto path variable for debugging purpose.
    my $cmd1 = "set auto_path";
    my $ret1;
    eval {
        print $sock "$cmd1\n";
        $ret1 = <$sock>;
    };
    #print "TCLLIBPATH / auto_path in TCL Shell :: $ret1\n";
    my $cmd = "package require SpirentHltApi";    
    my $ret;
    eval {
        print $sock "$cmd\n";
        $ret = <$sock>;
    };
    print "Loaded SpirentHltApi: $ret\n";
}

sub invoke {
    my $cmd = shift;
    private_log_output("# INFO Native Call : $cmd");
    
    my $ret = private_invoke($cmd);
    
    return $ret;
}

sub private_invoke {

    my $cmd = shift;
    my $sock = $TS;
    
    $cmd =~ s/[\f\n\r]//g;
    
    my $ret;
    eval {
        print $sock "$cmd\n";
        $ret = <$sock>;
    };
    
    $ret =~ s/\s+$//;
    $ret =~ s/^STCSERVER_RET_SUCCESS://;
    $ret =~ s/^STCSERVER_RET_ERROR://;

    return $ret;
} ## end sub private_invoke

sub hlt_params_conv {

    my $params = shift;
    my %paramhash = %$params;
    my $argsStr = "";
    my (@keys_var, @values_var);
    @keys_var = keys %paramhash;
    @values_var = values %paramhash;

    foreach my $key (keys %paramhash) {
        if($paramhash{$key} =~ / +/g) {
            if ($key eq "custom_pdus") {
                $argsStr .= ('-'.$key.' '.$paramhash{$key}.' ');
            } else {
                $argsStr .= ('-'.$key.' '.'"'.$paramhash{$key}.'"'.' ');
            }
        } else {
            $argsStr .= ('-'.$key.' '.$paramhash{$key}.' ');
        }
    }
    return $argsStr;
}

sub format_keyed_list {
    my $keyArray = shift;
    my $valueArray = shift;
    #my @keyArray = $keyArrayRef;
    #my @valueArray = $valueArrayRef;
    #print "--$retVal--\n";
    #my $retVal = private_invoke("set ret \"{port_handle { port1 port2}} {status 1}\" ");
    
    #convert the HLT return value keyed list into hash and return   
    private_invoke("set hashkey \"\"; set hashvalue \"\"; set nested_hashkey \"\"");
    private_invoke("ret_hash ret hashkey hashvalue nested_hashkey");
    my $keys = private_invoke("set key \$hashkey");
    my $values = private_invoke("set value \$hashvalue");
    #print "Keys: $keys\n";
    #print "values: $values\n";
    $keys =~ s/STCSERVER_RET_SUCCESS://;
    $values =~ s/STCSERVER_RET_SUCCESS://;
    
    my @tmpKeyArray = split (/ +/, $keys);
    my $i = 0;
    my $brace = 0;
    foreach my $item (@tmpKeyArray) {
        if ($item =~ /\{.*\}+/) {
            $$keyArray[$i] = $item;
            $i++;
        } elsif($item =~ /\{+/) {
            $$keyArray[$i] = $item;
            $brace = 1;
        } elsif($item =~ /\}+/) {
            $$keyArray[$i] .= " ";
            $$keyArray[$i] .= $item;
            $i++;
            $brace = 0;
        } else {
            if ($brace == 1) {
                $$keyArray[$i] .= " ";
                $$keyArray[$i] .= $item;
            } else {
                $$keyArray[$i] = $item;
                $i++;
            }
        }
    }


    my @tmpValArray = split (/ +/, $values);
    my $flag = 0;
    $i = 0;
    $brace = 0;

    foreach my $item (@tmpValArray) {    
        my @tmpAry = split(//, $item);
        foreach my $char (@tmpAry) {
          if ($char =~ /\{/) {
            $brace++;
          } elsif ($char =~ /\}/) {
            $brace--;
          }
        }    
        
        if (($item =~ /\{.*\}+/) && ($brace == 0)) {
            $$valueArray[$i] = $item;
            $i++;
        } elsif ($brace != 0) {
            $$valueArray[$i] .= " " . $item;
            $flag = 1;
        } else {
            if ($flag) {
                $$valueArray[$i] .= " " . $item;
                $flag = 0;
            } else {
                $$valueArray[$i] = $item;
            }
            $i++;
        }    
    }
}

sub create_hash {
    my $keyArray = shift;
    my $valueArray = shift;
    my $keylen = scalar @$keyArray;
    my $vallen = scalar @$valueArray;
    my %hash;
    #print "Keys($keylen): @{$keyArray}\n";
    #print "Values($vallen): @{$valueArray}\n";

    #create hash with keys and values
    for(my $i=0; $i < $keylen; $i++ ){
        #Removal of unwanted characters
        my $hash_key = "";
        my @tmpArray;
        $$valueArray[$i] =~ s/[^a-zA-Z0-9_\.\/\-\s\(\):]+//g;
        $$keyArray[$i] =~ s/[^a-zA-Z0-9_\-\/\.:]+//g;
        if ($$keyArray[$i] =~ /^port_handle\.[\d]+\.[\d]+\.[\d]+\.[\d]+/) {
            #connect return keyedlist
            my @array = split(/\./, $$keyArray[$i]);
            my $chassisIp = "$array[1]".".$array[2]".".$array[3]".".$array[4]";
            $hash_key = "\$hash{port_handle}{\"$chassisIp\"}";
            for(my $j = 5; $j<@array; $j++) {
                $hash_key .= "{\"$array[$j]\"}";
            }
            $hash_key .= "= \"$$valueArray[$i]\""; 
        } elsif ($$keyArray[$i] =~ /^[\d]+\.[\d]+\.[\d]+\.[\d]+/) {
            #device_info return keyedlist
            my @array = split(/\./, $$keyArray[$i]);
            my $chassisIp = "$array[0]".".$array[1]".".$array[2]".".$array[3]";
            $hash_key = "\$hash{\"$chassisIp\"}";
            for(my $j = 4; $j<@array; $j++) {
                $hash_key .= "{\"$array[$j]\"}";
            }
            $hash_key .= "= \"$$valueArray[$i]\""; 
        } elsif ($$keyArray[$i] =~ /\./) {
            #For nested hash
            my @array = split(/\./, $$keyArray[$i]);
            if ($array[0] =~ /[^A-Za-z0-9_]/) {
                $hash_key = "\$hash{$array[0]}";
            } else {
                $hash_key = "\$hash{\"$array[0]\"}";
            }
            for(my $j = 1; $j<@array; $j++) {
                if ($array[0] =~ /[^A-Za-z0-9_]/) {
                    $hash_key .= "{$array[$j]}";
                } else {
                    $hash_key .= "{\"$array[$j]\"}";
                }
            }
            $hash_key .= "= \"$$valueArray[$i]\""; 
        } else {
            @tmpArray = split(" ",$$valueArray[$i]);
            my $value= $$valueArray[$i];
            $value =~ s/^\s+|\s+$|\r|\n//g;
            $hash_key = "\$hash{$$keyArray[$i]} = \"$value\"";
        }
        eval $hash_key;
    }
    
    return %hash;
}

sub create_special_hash {
    my $retVal = shift;    
    my %hash;
    my (@tmpArray, @tmpHndArray);
    
    $retVal =~ s/STCSERVER_RET_SUCCESS://;

    if ($retVal =~ /\{status 1\}/g) {
        $hash{status} = '1';
    } else {
        $hash{status} = '0';
    }
    
    $retVal =~ s/{handle {//;
    $retVal =~ s/}} {status 1}//;
    $retVal =~ s/{/\\{/g;
    $retVal =~ s/}/\\}/g;
    $hash{handle} = $retVal;
    
    return %hash;
}

sub check_error {
    my $retVal = shift;
    my %hash;
    my (@tmpArray, @tmpHndArray);
    
    if ($retVal =~ /\{status 0\}/) {
        $hash{status} = '0';
        $hash{log} = $retVal;
    } else {
        $hash{status} = '1';
    }
    
    return %hash;
}

sub private_log_output {
    my $msg = shift;
    my $level = 'SPIRENT DEBUG';
    
    if ($JT_ENV_FLAG) {
       if ($msg =~ m/HLTAPI ERROR/) {
            $level = 'RT:ERROR';
       }
        JT::put_log(level=>$level,msg=>$msg);
        if ($msg =~ m/HLTAPI ERROR/) {
            JT::error_handler( $level, $msg);
        }
    } else {
        print "level=>$level  msg=>$msg\n";
    }

}

sub AUTOLOAD {
    my $sub = our $AUTOLOAD;
    my (%input_hash) = @_;
    $sub =~ s/.*:://;  # trim package name
    private_log_output("# INFO sth::$sub");
    #print "\nHLP-API: Running $sub ... \n";    

    #convert the args into hlt arguments format
    my $hlt_args = hlt_params_conv(\%input_hash);
    
    #execute the HLT command
    my $retVal = private_invoke("set ret [sth::$sub $hlt_args] ");

    #HLTAPI Error Handling
    my %hash = check_error($retVal);
    if ($hash{status} == 0) {
        private_log_output("HLTAPI ERROR : Check Log message for details");
        return %hash;
    }
    
    my (@keyArray, @valueArray);
    format_keyed_list(\@keyArray, \@valueArray);

    return create_hash(\@keyArray, \@valueArray);
}

################################################################################
## HLP-APIs Subroutines for special handling
################################################################################
sub device_info {
    my (%input_hash) = @_;
    private_log_output("# INFO sth::device_info");
    #print "\nHLP: Running device_info...\n";

    #convert the args into hlt arguments format
    my $hlt_args = hlt_params_conv(\%input_hash);
    #execute the HLT command
    my $dev_info = private_invoke("set ret [sth::device_info $hlt_args]");

    #HLTAPI Error Handling
    my %hash = check_error($dev_info);
    if ($hash{status} == 0) {
        private_log_output("HLTAPI ERROR : Check Log message for details");
        return %hash;
    }

    my (@keyArray, @valueArray);
    format_keyed_list(\@keyArray, \@valueArray);
    
    #Special handling for device Info return    
    my @tmpArray = split (/ +/, $valueArray[0]);
    shift @valueArray;
    unshift @valueArray, @tmpArray;

    return create_hash(\@keyArray, \@valueArray);
}

sub emulation_gre_config {
    my (%input_hash) = @_;
    private_log_output("# INFO sth::emulation_gre_config");
    #convert the args into hlt arguments format
    my $hlt_args = hlt_params_conv(\%input_hash);
    
    #execute the HLT command
    my $retVal = private_invoke("set ret [sth::emulation_gre_config $hlt_args] ");
    $retVal =~ s/STCSERVER_RET_SUCCESS://;
    return $retVal;
}
sub cleanup_session {
    my (%input_hash) = @_;
    private_log_output("# INFO sth::cleanup_session");
	if (( exists $input_hash{"clean_logs"} ) && ($input_hash{"clean_logs"} eq '1') ){
		invoke("stcserver::close_file");
		if (unlink $log_name) {
		    print "Delete $log_name success\n";
		} else {
		    print "Delete $log_name failure\n";
		}
	} 
    #convert the args into hlt arguments format
    my $hlt_args = hlt_params_conv(\%input_hash);
    
    #execute the HLT command
    my $retVal = invoke("set ret [sth::cleanup_session $hlt_args] ");

    #HLTAPI Error Handling
    my %hash = check_error($retVal);
    if ($hash{status} == 0) {
        private_log_output("HLTAPI ERROR : Check Log message for details");
        return %hash;
    }
    
    my (@keyArray, @valueArray);
    format_keyed_list(\@keyArray, \@valueArray);

    return create_hash(\@keyArray, \@valueArray);
}
sub emulation_lldp_optional_tlv_config {
    my (%input_hash) = @_;
    private_log_output("# INFO sth::emulation_lldp_optional_tlv_config");
    #convert the args into hlt arguments format
    my $hlt_args = hlt_params_conv(\%input_hash);    
    #execute the HLT command
    my $retVal = private_invoke("set ret [sth::emulation_lldp_optional_tlv_config $hlt_args] ");
    
    #HLTAPI Error Handling
    my %hash = check_error($retVal);
    if ($hash{status} == 0) {
        private_log_output("HLTAPI ERROR : Check Log message for details");
        return %hash;
    }
    
    return create_special_hash($retVal);
}

sub emulation_lldp_dcbx_tlv_config {
    my (%input_hash) = @_;
    private_log_output("# INFO sth::emulation_lldp_dcbx_tlv_config");
    #convert the args into hlt arguments format
    my $hlt_args = hlt_params_conv(\%input_hash);
    #execute the HLT command
    my $retVal = private_invoke("set ret [sth::emulation_lldp_dcbx_tlv_config $hlt_args] ");

    #HLTAPI Error Handling
    my %hash = check_error($retVal);
    if ($hash{status} == 0) {
        private_log_output("HLTAPI ERROR : Check Log message for details");
        return %hash;
    }

    return create_special_hash($retVal);
}


1;