# This file was automatically generated by SWIG (http://www.swig.org).
# Version 3.0.10
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

package sPerl;
use base qw(Exporter);
use base qw(DynaLoader);
package sPerlc;
bootstrap sPerl;
package sPerl;
@EXPORT = qw();

# ---------- BASE METHODS -------------

package sPerl;

sub TIEHASH {
    my ($classname,$obj) = @_;
    return bless $obj, $classname;
}

sub CLEAR { }

sub FIRSTKEY { }

sub NEXTKEY { }

sub FETCH {
    my ($self,$field) = @_;
    my $member_func = "swig_${field}_get";
    $self->$member_func();
}

sub STORE {
    my ($self,$field,$newval) = @_;
    my $member_func = "swig_${field}_set";
    $self->$member_func($newval);
}

sub this {
    my $ptr = shift;
    return tied(%$ptr);
}


# ------- FUNCTION WRAPPERS --------

package sPerl;

*salLog = *sPerlc::salLog;
*salInit = *sPerlc::salInit;
*salShutdown = *sPerlc::salShutdown;
*salShutdownNoExit = *sPerlc::salShutdownNoExit;
*salConnect = *sPerlc::salConnect;
*salDisconnect = *sPerlc::salDisconnect;
*salCreate = *sPerlc::salCreate;
*salDelete = *sPerlc::salDelete;
*salSet = *sPerlc::salSet;
*salGet = *sPerlc::salGet;
*salPerform = *sPerlc::salPerform;
*salReserve = *sPerlc::salReserve;
*salRelease = *sPerlc::salRelease;
*salSubscribe = *sPerlc::salSubscribe;
*salUnsubscribe = *sPerlc::salUnsubscribe;
*salHelp = *sPerlc::salHelp;
*salApply = *sPerlc::salApply;

############# Class : sPerl::StringVector ##############

package sPerl::StringVector;
use vars qw(@ISA %OWNER %ITERATORS %BLESSEDMEMBERS);
@ISA = qw( sPerl );
%OWNER = ();
%ITERATORS = ();
sub new {
    my $pkg = shift;
    my $self = sPerlc::new_StringVector(@_);
    bless $self, $pkg if defined($self);
}

*size = *sPerlc::StringVector_size;
*empty = *sPerlc::StringVector_empty;
*clear = *sPerlc::StringVector_clear;
*push = *sPerlc::StringVector_push;
*pop = *sPerlc::StringVector_pop;
*get = *sPerlc::StringVector_get;
*set = *sPerlc::StringVector_set;
sub DESTROY {
    return unless $_[0]->isa('HASH');
    my $self = tied(%{$_[0]});
    return unless defined $self;
    delete $ITERATORS{$self};
    if (exists $OWNER{$self}) {
        sPerlc::delete_StringVector($self);
        delete $OWNER{$self};
    }
}

sub DISOWN {
    my $self = shift;
    my $ptr = tied(%$self);
    delete $OWNER{$ptr};
}

sub ACQUIRE {
    my $self = shift;
    my $ptr = tied(%$self);
    $OWNER{$ptr} = 1;
}


# ------- VARIABLE STUBS --------

package sPerl;

1;
