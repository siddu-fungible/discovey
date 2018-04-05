# Copyright (c) 2007 by Spirent Communications, Inc.
# All Rights Reserved
#
# By accessing or executing this software, you agree to be bound 
# by the terms of this agreement.
# 
# Redistribution and use of this software in source and binary forms,
# with or without modification, are permitted provided that the 
# following conditions are met:
#   1.  Redistribution of source code must contain the above copyright 
#       notice, this list of conditions, and the following disclaimer.
#   2.  Redistribution in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer
#       in the documentation and/or other materials provided with the
#       distribution.
#   3.  Neither the name Spirent Communications nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# This software is provided by the copyright holders and contributors 
# [as is] and any express or implied warranties, including, but not 
# limited to, the implied warranties of merchantability and fitness for
# a particular purpose are disclaimed.  In no event shall Spirent
# Communications, Inc. or its contributors be liable for any direct, 
# indirect, incidental, special, exemplary, or consequential damages
# (including, but not limited to: procurement of substitute goods or
# services; loss of use, data, or profits; or business interruption)
# however caused and on any theory of liability, whether in contract, 
# strict liability, or tort (including negligence or otherwise) arising
# in any way out of the use of this software, even if advised of the
# possibility of such damage.

# File Name:                 RunExternalProcessCommand.tcl
# Description:               This script demonstrates how to use the 
#                            RunExternalProcessCommand in conjuction
#                            with the Sequencer object.  This command
#                            will ONLY work with the Sequencer object.
#   

set ENABLE_CAPTURE 1


if {[catch {
  package require SpirentTestCenter

  puts "SpirentTestCenter system version:\t[stc::get system1 -Version]"

# Physical topology
  set szChassisIp 10.100.33.29
  set iTxSlot 11
  set iTxPort 1
  set iRxSlot 11
  set iRxPort 2

# Create the root project object.  This is required for the stc::perform
#   function to work.
  puts "Creating project ..."
  set hProject [stc::create project]

  set system1 system1

# Create a sequencer object.  
  set hSequencer [stc::create "Sequencer" -under $system1 \
        -Active "TRUE" \
        -Name "Sequencer"]

# Create an external process that will launch the notepad.exe application.
#   Note that the -ExecutionMode is set to BLOCKING.  This configuration
#   will wait (blocking) until the application is closed before continuing.
  set hRunExternalProcessCommand [stc::create "RunExternalProcessCommand" \
        -under $hSequencer \
        -AutoDestroy "FALSE" \
        -ExecuteSynchronous "FALSE" \
        -Active "TRUE" \
        -CommandLine "notepad.exe"\
        -UseTimeout FALSE \
        -TimeoutOption PROMPT_USER \
        -ExecutionMode BLOCKING]

# Additional configuration for the sequencer.  
  stc::config $hSequencer -CommandList "$hRunExternalProcessCommand" \
      -BreakpointList ""  \
      -DisabledCommandList ""
      
# Start the sequencer
  puts "Start the sequencer ..."    
  stc::perform sequencerStart

# Wait for sequencer to finish
  stc::waituntilcomplete
  puts "Sequencer complete."

# Delete configuration
  puts "Deleting project"
  stc::delete $hProject
} err] } {
	puts "Error caught: $err"
}
