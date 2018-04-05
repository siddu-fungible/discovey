#package spirentWrapper;
package ixiahlt;

use Cwd;
use File::Spec;
use File::Copy;
use File::Basename;
use strict;
use warnings;

require Data::Dumper;

use Socket;
use Switch;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(hlpapiGen_env test_config);
our %return_hash;
our $retVal;

##_##global variables to be used for physical to virtual ports.
our %vport_to_port_mapping;
our %phyport_to_port_mapping;
our %rfc_status;
##_##Global variable to used for saving configs
our $FILEHANDLE_COUNT = "1";
our $FILE_NAME;
our %file_hash;
#date to be used to save files
our $date;

my $TS ;
use vars qw($TMP);

BEGIN {
    use constant TRUE => 1;
    use constant FALSE => 0;
    use constant ERROR => -1;
    use constant ABORT => -2;
    
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

    my ($tcl_path, $log_dir, $log_name);
    if (defined $ENV{STC_TCL}) {
        $tcl_path = $ENV{STC_TCL};
    } else {
        $tcl_path = "/volume/perl/bin/tclsh";
        #print "HLP Error: need set system environ variable STC_TCL to be defined\n";
        #exit;
    }
    
    $log_dir = defined $ENV{HLPAPI_LOG}? $ENV{HLPAPI_LOG} : getcwd();
    
    $log_name = $0;
    if($log_name =~ /\./) {
        my @tmp_array = split(/\./, $log_name);
        $log_name = "$tmp_array[0]" . ".hltlog";
    } else {
        $log_name = "hlpapi.hltlog";
    }
    #print "DEBUG : Log Directory: $log_dir\n";
	my $stcserver;
	if (exists $ENV{'SPIRENT_HLTAPI_FOR_PERL_DIR'}) {
		$stcserver = "|$tcl_path " . "$ENV{'SPIRENT_HLTAPI_FOR_PERL_DIR'}"."hltapiserver.srv $bnd_port 120 log $log_dir $log_name INFO";
	} else {
		$stcserver = "|$tcl_path " . "$ENV{'SPIRENT_HLTAPI_INSTALL_DIR'}"."hltapiserver.srv $bnd_port 120 log $log_dir $log_name INFO";
	}
    open(TMP, $stcserver);
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

    #if (defined $STC_MODULE_INITIALIZED) {
    #    #Env variables
    #    print "---I am Here ---\n";
    #    $ENV{TCLLIBPATH} .= " \"$STC_MODULE_INITIALIZED->{STCDIR}\"";
    #    $ENV{TCLLIBPATH} .= " \"$STC_MODULE_INITIALIZED->{HLTAPI_DIR}\"";
    #    $ENV{PERL5LIB}  .= " \"$STC_MODULE_INITIALIZED->{HLTAPI_FOR_PERL_DIR}\"";
    #}

##_##Srini- Commented     
    my $cmd = "package require SpirentHltApiWrapper";    
 
    print"DEBUG :stcserver => $stcserver \n";
    my $ret;
    eval {
        print $sock "$cmd\n";
        $ret = <$sock>;
    };
	
    print "DEBUG 1 : Loaded SpirentHltApiWrapper: $ret\n";
    my $cmd = "package require SpirentHltApi";    
    my $ret;
    eval {
        print $sock "$cmd\n";
        $ret = <$sock>;
    };
    print "Loaded SpirentHltApi: $ret\n";
    print "Perl Wrapper version: 1.0.0918\n";
          
   
}

sub invoke {

    my $cmd = shift;
    my $sock = $TS;
    
    $cmd =~ s/[\f\n\r]//g;
    
    my $ret;
    eval {
        print $sock "$cmd\n";
        $ret = <$sock>;
    };
	
	##strip off the unwanted messages
	if ($ret =~ m/STCSERVER_RET_SUCCESS/){
		$ret =~ s/STCSERVER_RET_SUCCESS://;
		$ret =~ s/\r\n//g;
    }
	return $ret;
} ## end sub invoke

sub hlt_params_conv {

    my $params = shift;
    my %paramhash = %$params;
    my $argsStr = "";
    my (@keys_var, @values_var);
    @keys_var = keys %paramhash;
    @values_var = values %paramhash;

    foreach my $key (keys %paramhash) {
        if($paramhash{$key} =~ / +/g) {
            $argsStr .= ('-'.$key.' '.'"'.$paramhash{$key}.'"'.' ');
        } else {
            if (ref($paramhash{$key}) eq "ARRAY") {
	        my @array_arg = @{$paramhash{$key}};
		my $list;
		foreach (@array_arg) {
		    $list .= "$_ ";
		}
                    $argsStr .= ('-'.$key.' '.$list. ' ');
		} else {
                    $argsStr .= ('-'.$key.' '.$paramhash{$key}.' ');
		}
        }
    }
    return $argsStr;
}

sub format_keyed_list {
    my $keyArray = shift;
    my $valueArray = shift;
    
    #convert the HLT return value keyed list into hash and return   
    invoke("set hashkey \"\"; set hashvalue \"\"; set nested_hashkey \"\"");
    invoke("ret_hash ret hashkey hashvalue nested_hashkey");
    my $keys = invoke("set key \$hashkey");
    my $values = invoke("set value \$hashvalue");    
    
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
                ##_##$hash_key = "\$hash{$array[0]}";
				$hash_key = "\$hash{\"$array[0]\"}";
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

sub ixiahlt::status_item {
        my $user_key = shift;
        ##_## temp solution for getting traffic_stats pkt_mbit_rate.
      #  if (defined($return_hash{$user_key}))
#=pod 	  
#	   if (defined($user_key)){
#                if ($user_key eq 'traffic_item.aggregate.tx.total_pkts'){
#                        #return @{$return_hash{'traffic_item.aggregate.tx.total_pkts'}};
#						our $retVal = @{$return_hash{'traffic_item.aggregate.tx.total_pkts'}};
#                }
#                if ($user_key eq 'traffic_item.aggregate.rx.total_pkts'){
#                        #return @{$return_hash{'traffic_item.aggregate.rx.total_pkts'}};
#						our $retVal = @{$return_hash{'traffic_item.aggregate.tx.total_pkts'}};
#                }
#				if ($user_key =~ s/[0-9]+\/([0-9]+\/[0-9]+\/[0-9]+)/$1/ ){
#					#print "$port_tmp\n";
#					#$user_key = $port_tmp ;			
#					print "$user_key\n";        		
#					our $retVal =  @{$return_hash{$user_key}};
#					#return @{return_hash{$user_key}};
#				}
#                 #return $return_hash{$user_key};
#				 our $retVal = $return_hash{$user_key};
#        }
#=cut		
	if (%return_hash) {
		switch ($user_key) {
		#print "\nYes return hash \n";
			case ('traffic_item.aggregate.tx.total_pkts') {our $retVal = @{$return_hash{'traffic_item.aggregate.tx.total_pkts'}};}
			case ('traffic_item.aggregate.rx.total_pkts') {our $retVal = @{$return_hash{'traffic_item.aggregate.rx.total_pkts'}};}
			case ( /[0-9]+\/[0-9]+\/[0-9]+\/[0-9]+/ || /[0-9]+\/[0-9]+\/[0-9]+/ ) {
				  if ( $user_key =~ s/[0-9]+\/([0-9]+\/[0-9]+\/[0-9]+)/$1/ ) {
				   print "$user_key\n";        		
				   our $retVal =  $return_hash{$user_key};}
 		    }
			#case ('interface_handle') { $user_key = 'handle'; }
                        case (/traffic_item.streamblock[0-9]+.tx.total_pkt_rate/) {our $retVal = invoke("set ret [spirent::status_item $user_key] ");}
                        case (/traffic_item.streamblock[0-9]+.rx.total_pkt_rate/) {our $retVal = invoke("set ret [spirent::status_item $user_key] ");}
                        case (/traffic_item.[0-9]+.tx.total_pkt_rate/) {our $retVal = invoke("set ret [spirent::status_item $user_key] ");}
                        case (/traffic_item.[0-9]+.rx.total_pkt_rate/) {our $retVal = invoke("set ret [spirent::status_item $user_key] ");}
			case ('traffic_item.aggregate.rx.pkt_loss_duration') { return $return_hash{$user_key};}
			else  { 
                                        #print "\n default\n"; 
					our $retVal = $return_hash{$user_key};
					print  "\n Success1 : $retVal\n";
			}						
		}
	} else {
	print "\n No return hash \n";
		our $retVal = invoke("set ret [spirent::status_item $user_key] ");
		print  "\n Success2 : $retVal\n";
	}		     
        my @retArr = split(/ /,$retVal);
        my $length = @retArr;
        if ($length > 1) {
                return @retArr;
        } else {
                return $retVal;
        }
}

sub ixiahlt::status_item_keys {

	my $user_key = shift;
	my ( $tmp_item_port, $tmp_item_mode);
	##_## temp solution for getting traffic_stats for : ixiahlt::status_item_keys("$TxPort.aggregate.tx");
	if (defined($user_key)){	
		print "before : $user_key\n";	
        #		if ($user_key =~ s/[0-9]*\/([0-9]*\/[0-9]*)$/$1/) {   }
		if ($user_key =~ s/[0-9]*\/([0-9]*\/[0-9][0-9]+).aggregate.([t|r]x)/$1.aggregate.$2/) {
            $tmp_item_port = $1;
			$tmp_item_mode	= $2;
			print "$user_key\n";
			print "$tmp_item_port, $1, $tmp_item_mode, $2\n";
        }	
		print Data::Dumper::Dumper(%return_hash);		
		#return $return_hash{$user_key};
		#my $retVal1 = invoke("set ret [spirent::status_item_keys $user_key] ");
		#our $retVal = keys %return_hash;
		our $retVal = $return_hash{$tmp_item_port}->{'aggregate'}->{$tmp_item_mode};
		print Data::Dumper::Dumper($retVal)
	} else {
	    our $retVal = invoke("set ret [spirent::status_item_keys]");
		print $retVal;
	}
        my @retArr = split(/ /,$retVal);
        my $length = @retArr;
        if ($length > 1) {
                return @retArr;
        } else {
                return $retVal;
        }	
}

sub ixiaixn::getRoot{
    #print "AM in ixiaixn::getRoot API";
    #return "project1";
	return "::ixNet::OBJ-/";
}

sub ixiaixn::getNull {
	return "::ixNet::OBJ-null";
}

#ixiaixn::ixNet('isDone', $job)
sub ixiaixn::ixNet {
	my $arg1 = shift;
	my $arg2 = shift;
	my $logDir;
	my $path1;
	
	if ($arg1 eq "writeTo"){
		my $arg3 = shift;
		
		##ignoring arg2 as in ixia is saved in the windows machine
		## In Spirent we save directly to the present dir

		my $file_handle = "::ixNet::FILEHANDLE-$FILEHANDLE_COUNT";
		#converting the file extension from ixncfg to xml 
		#my @temp1 = split('/',$arg2);
		#my $text1 = $temp1[$#temp1];
		my $text1='';
		#$text1 =~ s/\./_/g;
		#$text1 .= "\.xml";
		#$temp1[$#temp1] = $text1;
		#$path1 = join('', @temp1);
		
		if ($arg3 eq "-ixNetRelative"){
			$logDir = $JT::LOG_DIR || $ENV{JT_LOG_DIR} || $ENV{TE_DATA_TMPDIR};
			$logDir = '.'  if !(defined $logDir);
			$logDir .= "$logDir.$text1";
		} elsif($arg3 eq "-overwrite") {
			$logDir = $arg2;
			return $logDir;
		}
		##save the file handle as key and file path as value in global variable file_hash
		$file_hash{$file_handle} = $logDir;
		$FILEHANDLE_COUNT++;
		return $file_handle;
		
	} elsif ($arg1 eq "execute"){
		if ($arg2 eq "saveConfig"){
			my $file = shift;
			##file = ::ixNet::FILEHANDLE-13 
			foreach(keys %file_hash){
				if ($_ eq $file){
					my $logDir = $file_hash{$_};
					$retVal = invoke("set ret [stc::perform SaveAsXml -filename $logDir] ");
					#$retVal =~ s/STCSERVER_RET_SUCCESS://;
					#$retVal =~ s/\r\n//g;
				}
			}
		} elsif ($arg2 eq "copyFile"){
			my ($src_path, $dst_path);
			
			my $src_file_handle = shift;
			my $dst_file_handle = shift;
			
			# foreach(keys %file_hash){
				# if ($_ eq $src_file_handle){
					# $src_path = $file_hash{$_};
				# } elsif($_ eq $dst_file_handle){
					# $dst_path = $file_hash{$_};
				# }
			# }
			if(defined($src_file_handle) && defined($dst_file_handle)){
				qx(cp $src_file_handle $dst_file_handle);
			
			}
		}
		#my $retVal = invoke("set ret [sth::traffic_control -action run] ");
	} elsif($arg1 eq "readFrom"){
		my $logDir = $JT::LOG_DIR || $ENV{JT_LOG_DIR} || $ENV{TE_DATA_TMPDIR};
		$logDir = '.'  if !(defined $logDir);
		
		#converting the file extension from ixncfg to xml 
		#my @temp1 = split('/',$arg2);
		#my $text1 = $temp1[$#temp1];
		#$text1 =~ s/\./_/g;
		#$text1 .= "\.xml";
		#$logDir .= "$logDir.$text1";
		return $arg2;
	} elsif ($arg1 eq 'isDone'){
		my $job = $arg2;
		if ($job eq "stop_job"){
			return 1;
		}
		$retVal = invoke("set ret [stc::get DevicesStartAllCommand] ")
	} elsif ($arg2 eq "execute") {
		my $arg3 = shift;
		if(defined($arg3)){
			if($arg3 eq 'stopAllProtocols'){
				invoke("stc::perform devicestop");
				return "stop_job";
			}
		}
		#my $arg3;
		# if(defined($arg3 = shift) && ($arg3 eq 'startAllProtocols')){

			##LOGIC:
			##Step1: Get the ports configured.
			## Step2: Get all devices configured on each port.
			## Step3: Get all prototcols configured on each device.
			
			##Step1: Get the ports configured.
			## Lets get the ports from the hash %phyport_to_port_mapping
			# my @ports_name = keys(%phyport_to_port_mapping);
			## Step2: Get all devices configured on each port.
			# foreach(@ports_name){
				# $retVal = invoke("set ret [stc::get port1 -affiliationport-Sources] ");
				# $retVal =~ s/STCSERVER_RET_SUCCESS://;
				# $retVal =~ s/\r\n//g;
				# my @devices = split(' ',$retVal);
				# foreach(@devices){
					# $retVal = invoke("set ret [stc::get $_ -children] ");
					# $retVal =~ s/STCSERVER_RET_SUCCESS://;
					# $retVal =~ s/\r\n//g;
					# my @protocols = split(' ',$retVal);
					# foreach(@protocols){
						# if ($_ =~ m/ospfv2routerconfig/){
							##ospfv2 is configured
							##get the state of the protocol
							# $retVal = invoke("set ret [stc::get $_ -AdjacencyStatus] ");
							# $retVal =~ s/STCSERVER_RET_SUCCESS://;
							# $retVal =~ s/\r\n//g; 
							# if ($retVal =~ m/FULL/){
								# return 1;##_##TODO: Need to change
							# }
						# }
					# }
				# }
			# }
			my @devicelist;
			our $retText = invoke("stc::get project1 -children-emulateddevice");
			#$retText =~ s/STCSERVER_RET_SUCCESS://;
			#$retText =~ s/\r\n//g;
			@devicelist = split(' ',$retText);
			##put_log "Starting all routing protocols.";
			
			##bug : OSPF route protocol config creates 2 lSAs due to which routes are not getting populated.
			##below code will be removed once the issue is fixed in HLPAPI layer.
			foreach (@devicelist){
				$retText = invoke("set ret [stc::get $_ -children]");
				#$retText =~ s/STCSERVER_RET_SUCCESS://;
				#$retText =~ s/\r\n//g;
				my @protocol_list = split(' ',$retText);
				foreach (@protocol_list){
					if ($_ =~ m/ospfv2routerconfig/){
						$retText = invoke("set ret [stc::get $_ -children]");
						#$retText =~ s/STCSERVER_RET_SUCCESS://;
						#$retText =~ s/\r\n//g;
						
						##at present just add the router lsa with baorder router set as 1.
						$retText = invoke("set ret [stc::config routerlsa1 -Abr True]");
						###$retText = invoke("set ret [stc::config routerlsa2 -Abr True]");
						$retText = invoke("set ret [stc::config routerlsa3 -Abr True]");
					}
				}
			}
			##apply before start of devices
			invoke("set ret [stc::apply] ");
			invoke("stc::perform devicestart");
			return 1;
			#
		#}
	} else {
		##put_log "This feature is not supported. Please raise a ticket to support\@spirent.com";
		return 1; 
	}
}

sub ixiaixn::execute{
	my $arg1 = shift;
	my $port;
	if ($arg1 eq 'releasePort'){
		my $arg2 = shift;
		foreach(keys %vport_to_port_mapping){
			if ($vport_to_port_mapping{$_} eq $arg2){
				$port = $_;
			}
		}
		#stc::release $chassisHost/$port
		##get the chassis and port
		our $retText = invoke("set ret [stc::get $port -Location] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
        #$retText =~ s/\r\n//g;
		my @temp1 = split('\/\/',$retText);
		
		##release the port
		$retText = invoke("set ret [stc::release $temp1[1]] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
        #$retText =~ s/\r\n//g;
	} elsif ($arg1 eq 'start'){
		##get the second argument
		
		my $arg2 = shift;
		##need to add code to check if its a rfc2544 test to execute.
		our $retText = invoke("set ret [sth::test_rfc2544_control -action run -wait 1 -cleanup 0]");
		my %hash = check_error($retText);
		if ($hash{status} == 0) {
			print "HLTAPI ERROR : Check Log message for details\n";
			return %hash;
		}
		%rfc_status = %hash;
		
		#put_log "Result: $retText";
		##we wwill be saving the result in a global variable for further verification.
		
	} elsif ($arg1 eq 'stop'){
		##get the second argument
		##delete any streamblocks not created by rfc_2544.
		
		my $arg2 = shift;
		
		##need to add code to check if its a rfc2544 test to execute.
		our $retText = invoke("set ret [sth::test_rfc2544_control -action stop -cleanup 0]");
		#HLTAPI Error Handling
		my %hash = check_error($retText);
		if ($hash{status} == 0) {
			print "HLTAPI ERROR : Check Log message for details\n";
			return %hash;
		}
		#put_log "Result: $retText";
		return $hash{'status'};
	}
}

sub ixiaixn::getList{
    ##print "AM in ixiaixn::getRoot API";
    #return "project1";
	my $root = shift;
	my $arg = shift;
	
	if(lc($arg) eq 'vport'){
		
		our $retText = invoke("set ret [stc::get project1 -children-port] ");
    
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
        #$retText =~ s/\r\n//g;
		
        my @retArr = split(/ /,$retText);
        my $count = 1;
		my $vPort_string='';
		my @vPortTempArray;
		foreach(@retArr){
			$vport_to_port_mapping{"port$count"} =  "::ixNet::OBJ-/vport:$count";
			$retText = invoke("set ret [stc::get port$count -location] ");
			
			#$retText =~ s/STCSERVER_RET_SUCCESS://;
			#$retText =~ s/\r\n//g;
			$retText =~ s/\/\///g;
			my @temp = split('\/',$retText);
			my $port_string = $temp[1]."\/".$temp[2];
			$phyport_to_port_mapping{"port$count"} = "1\/".$port_string;
			$vPortTempArray[$count-1]="::ixNet::OBJ-/vport:$count";
			$count++;
		}
		#foreach(keys %vport_to_port_mapping){
			$vPort_string = join(" ", @vPortTempArray);
		#}
		return $vPort_string;
	}
}

sub ixiaixn::getAttribute{
#($vport, '-assignedTo');
	my $vport = shift;
	my $args = shift;
	my $port;
	
	foreach(keys %vport_to_port_mapping){
		if ($vport_to_port_mapping{$_} eq "$vport"){
			$port = $_;
		}
	}
	
	if ($args eq '-assignedTo'){
		#stc::get <devicehandle> -children-ipv4if
		
		our $retText = invoke("set ret [stc::get $port -location] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
		$retText =~ s/\/\///g;
		$retText =~ s/\//:/g;
		
		return $retText;
	} elsif ($args eq '-type'){
		our $retText = invoke("set ret [stc::get $port -activephy-Targets] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
		
		if (($retText =~ m/ethernet10gigfiber/) ||($retText =~ m/ethernet10gigcopper/)){
			return 'tenGigLan';
		} elsif ($retText =~ m/ethernet100gigfiber/){
			return 'hundredGigLan';
		} elsif (($retText =~ m/ethernetfiber/) ||($retText =~ m/ethernetcopper/)){
			return 'ethernet';
		}
	} elsif($args eq '-state'){
		foreach(keys %vport_to_port_mapping){
			if ($vport_to_port_mapping{$_} eq $vport){
				$port = $_;
			}
		}
		our $retText = invoke("set ret [stc::get $port -Online] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
		if ($retText eq 'true'){
			return 'up';
		} elsif ($retText eq 'false'){
			return 'down';
		}
	} elsif ($args eq '-result'){
		##Get the 
		our $retText = invoke("sth::test_rfc2544_info -test_type throughput");
		my %hash = check_error($retText);
		if ($hash{'status'} == 1){
			return "PASS";
		}
	} elsif ($args eq '-resultPath'){
		my $db_file = invoke("stc::get testresultsetting1 -CurrentResultFileName");
		#$db_file =~ s/STCSERVER_RET_SUCCESS://;
		#$db_file =~ s/\r\n//g;
		#our $date = `date +"%m_%d_%y_%H_%M"`;
		#chomp($date);
		my $temp = invoke("stc::perform ExportDbResultsCommand -Format CSV -ResultDbFile $db_file -TemplateUri $ENV{TCLLIBPATH}/results_reporter/templates/Rfc2544ThroughputStats.rtp");
		#$temp =~ s/STCSERVER_RET_SUCCESS://;
		#$temp =~ s/\r\n//g;
		##below expectation is the csv file is save at the same location where the db file is.
		my @temp1 = split('/',$db_file);
		pop(@temp1); ##pop out the last element which is the db file name.
		my $path = join('/',@temp1)."/";
		#put_log "\n log path is $path";
		return $path;
	} elsif ($args eq '-isRunning') {
		if ($rfc_status{'status'}==1){
			return 0;##no need to check further as the test is complete now.
#		RunningState
		}
	} else {
	##need info -- should it be put_log/print ???
	#put_log "This feature is not supported\. Please raise a ticket to support\@spirent.com";
	}##TODO: else stmt - ticket
}

sub ixiaixn::setMultiAttrs {
	my $args1 = shift;
	my $args2 = shift;
	my $port;
	my @temp = split('\/', $args1);
	##Check for port configuration
	##At present we can only check for second array value as the first is a variable for port
	if ($args1 =~ m/liConfig/){
		foreach (keys %vport_to_port_mapping){
			if ($vport_to_port_mapping{$_} eq $temp[0]){
				$port = $_;
			}
		}
	}
	if ($temp[2] eq 'l1Config'){
		$args1 =~ /(::ixNet::OBJ-\/vport:\d+)/;
		my $temp = $1;
		foreach (keys %vport_to_port_mapping){
			if ($vport_to_port_mapping{$_} eq $temp){
				$port = $_;
			}
		}
		my %hash = %$args2;
		##query : can a port have both 1g, 10g at the same time.
		##becoz: below code we are only querying the activephy-Targets and 
		## not querying the 2nd argumnet
		our $retText = invoke("set ret [stc::get $port -activephy-Targets] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
		
		$retText = invoke("set ret [stc::config  $retText -InternalPpmAdjust 100] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
		
#		my $handle1 = stc::get port1 -Ethernet10GigCopper 
#		stc::config $handle1 -InternalPpmAdjust $value
#		stc::apply
	}

	
}

sub ixiaixn::setAttribute {
	my $arg1 = shift;
	my $arg2 = shift;
	my $arg3 = shift;
	my $port;
	
	if ($arg2 eq '-connectedTo'){
		foreach (keys %vport_to_port_mapping){
			if ($arg1 eq $vport_to_port_mapping{$_}){
				$port = $_;
			}
		}
		our $retText = invoke("set ret [stc::perform  resetconfig -config $port] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
	} elsif ($arg2 eq '-type'){
		
		our $retText = invoke("set ret [stc::get $port -activephy-Targets] ");
		#$retText =~ s/STCSERVER_RET_SUCCESS://;
		#$retText =~ s/\r\n//g;
	}
}

sub ixiaixn::commit{
	our $retText = invoke("set ret [stc::apply] ");
	
}

sub ixTclNet::ApplyTraffic {
	apply();
	return 1;
}

sub ixTclNet::StartTraffic {
	# Resolve ARP
	#send_arp();
	my $sub = sub_name();
	my $pl = invoke("stc::get project1 -children-port");
	#$pl =~ s/STCSERVER_RET_SUCCESS://;
	#$pl =~ s/\r\n//g;
	#resolved_stream_mac();
	my $wait;
	my (@anas,@unwait_gens, @wait_gens);
	foreach my $port (split(/ +/, $pl)) {
		my $durationmode = invoke("stc::get $port.generator.generatorconfig -durationmode");
	#	$durationmode =~ s/STCSERVER_RET_SUCCESS://;
	#	$durationmode =~ s/\r\n//g;
		my $gen = invoke("stc::get $port -children-generator");
	#	$gen =~ s/STCSERVER_RET_SUCCESS://;
	#	$gen =~ s/\r\n//g;
		my $ana = invoke("stc::get $port -children-analyzer");
	#	$ana =~ s/STCSERVER_RET_SUCCESS://;
	#	$ana =~ s/\r\n//g;
		push(@anas, $ana);
		
		# if ( $durationmode =~ /burst/i) {
			# #put_log( level => 'WARN', msg => "$port was burst mode previously, will not change its mode here" );
		# } else {
			# $self->invoke("stc::config $port.generator.generatorconfig
								# -duration $duration
								# -durationmode seconds");
			# $durationmode = "seconds";
		# }
		
		if ($durationmode =~ /continuous/i) {
            $wait = 0;
            push(@unwait_gens, $gen);
            
        } elsif ($durationmode =~ /burst/i ) {
            $wait = 1;
            push(@wait_gens, $gen);
        } else {
            if (defined $wait && $wait == 0) {
                push(@unwait_gens, $gen);
            } else {
                $wait = 1;
                push(@wait_gens, $gen);
            }
        }
        #put_log(level=>"INFO", msg=>"For $port, the Durationmode mode is $durationmode. Wait flag is $wait");
	}
	# do an apply here to make sure we've got the latest config
    # Note: if the gen is running at this moment, then the apply will not work!!
    apply();

    #put_log(level=>"INFO", msg=>"Clear ports statistic before starting the traffic.");
    invoke("stc::perform resultclearalltraffic -portlist { $pl }");
   
    #put_log(level=>"INFO", msg=>"Starting traffic.");
    

    return 1 unless (@wait_gens);
 
    # keep checking status...
    # can't just sleep for the duration
    my @tmp_gens;
    while (1) {
        sleep(1);
        foreach my $gen (@wait_gens) {
			my $state = invoke("stc::get $gen -state");
	#		$state =~ s/STCSERVER_RET_SUCCESS://;    # start all analyzers and generators
    invoke("stc::perform analyzerstart  -analyzerlist  { @anas  } ");
    sleep(1);
    invoke("stc::perform generatorstart -generatorlist { @wait_gens @unwait_gens  } ");
    
	#		$state =~ s/\r\n//g;
            next if ("stopped" eq lc($state));
            push(@tmp_gens, $gen);
        }
        @wait_gens = @tmp_gens;
        @tmp_gens = ();
        last unless (@wait_gens);
    }    

    sleep(5); # let packets get through test

    #put_log(level=>"INFO", msg=>"$sub END");
    
    return 1;

}

sub ixTclNet::StopTraffic {
	# Resolve ARP
	#send_arp();
	my $sub = sub_name();
	my $pl = invoke("stc::get project1 -children-port");
	#$pl =~ s/STCSERVER_RET_SUCCESS://;
	#$pl =~ s/\r\n//g;
	#resolved_stream_mac();
	my $wait;
	my (@anas,@unwait_gens, @wait_gens);
	foreach my $port (split(/ +/, $pl)) {
		my $durationmode = invoke("stc::get $port.generator.generatorconfig -durationmode");
	#	$durationmode =~ s/STCSERVER_RET_SUCCESS://;
	#	$durationmode =~ s/\r\n//g;
		my $gen = invoke("stc::get $port -children-generator");
	#	$gen =~ s/STCSERVER_RET_SUCCESS://;
	#	$gen =~ s/\r\n//g;
		my $ana = invoke("stc::get $port -children-analyzer");
	#	$ana =~ s/STCSERVER_RET_SUCCESS://;
	#	$ana =~ s/\r\n//g;
		push(@anas, $ana);
		
		
		
		if ($durationmode =~ /continuous/i) {
            $wait = 0;
            push(@unwait_gens, $gen);
            
        } elsif ($durationmode =~ /burst/i ) {
            $wait = 1;
            push(@wait_gens, $gen);
        } else {
            if (defined $wait && $wait == 0) {
                push(@unwait_gens, $gen);
            } else {
                $wait = 1;
                push(@wait_gens, $gen);
            }
        }
	}
	# do an apply here to make sure we've got the latest config
    # Note: if the gen is running at this moment, then the apply will not work!!
   
    #put_log(level=>"INFO", msg=>"Stoping traffic.");
 
    # keep checking status...
    # can't just sleep for the duration
    my @tmp_gens;
    while (1) {
        sleep(1);
        foreach my $gen (@wait_gens) {
			my $state = invoke("stc::get $gen -state");
	#		$state =~ s/STCSERVER_RET_SUCCESS://;    # start all analyzers and generators
			invoke("stc::perform analyzerstop  -analyzerlist  { @anas  } ");
			sleep(1);
			invoke("stc::perform generatorstop -generatorlist { @wait_gens @unwait_gens  } ");
			
	#		$state =~ s/\r\n//g;
            next if ("stopped" eq lc($state));
            push(@tmp_gens, $gen);
        }
        @wait_gens = @tmp_gens;
        @tmp_gens = ();
        last unless (@wait_gens);
    }    

    sleep(5); # let packets get through test

    #put_log(level=>"INFO", msg=>"$sub END");
    
    return 1;

}

sub ixiahlt::convert_vport_to_porthandle {
	my $args = shift;
	my %hash = %$args;
	foreach(keys %vport_to_port_mapping){
		if ($hash{'vport'} eq $vport_to_port_mapping{$_} ){
			##Comment
			my $temp = $_;
			$retVal = invoke("keylset return_list handle {$temp}")
		}
	}
}

sub ixiahlt::convert_porthandle_to_vport {
	my $args = shift;
	my %hash = %$args;
	my $port_handle = $hash{'port_handle'};
	foreach(keys %phyport_to_port_mapping){
		if ($port_handle eq $_ ){
			##Comment
			my $temp = $_;
			$retVal = invoke("keylset return_list handle {$temp}")
		}
	}
}

sub ixiahlt::status_item_private {
	my $args = shift;
	my $stat_item_1 = invoke("set stat_item [keylget return_list $args]");
	print (invoke("set stat_item [set return_list]"));
    return $stat_item_1;	
}

sub AUTOLOAD {
    my $sub = our $AUTOLOAD;
    print "\nHLP-API: Running $sub ... \n";    
    #my $a = shift;
    my %input_hash = @_;
    $sub =~ s/.*:://;  # trim package name
    #print "\nHLP-API: Running $sub ... \n";    
 
    #convert the args into hlt arguments format
    if ($sub =~ m/emulation_bgp_config/i) {
        $input_hash{"remote_as_flag"}=1;
        if(defined ($input_hash{md5_enable}) && ($input_hash{md5_enable} eq '')) {
		delete($input_hash{md5_enable});
	}
        
        
    }
   
    my $hlt_args = hlt_params_conv(\%input_hash);
    
    #execute the HLT command
    our $retVal = invoke("set ret [ixia::$sub $hlt_args] ");

    #HLTAPI Error Handling
    my %hash = check_error($retVal);
    if ($hash{status} == 0) {
        print "HLTAPI ERROR : Check Log message for details\n";
        return %hash;
    }
    
    my (@keyArray, @valueArray);
    format_keyed_list(\@keyArray, \@valueArray);

    %return_hash = create_hash(\@keyArray, \@valueArray);

    
	return %return_hash;
}

1;


