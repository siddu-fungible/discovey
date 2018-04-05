# Copyright (c) 2010 by Spirent Communications, Inc.
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

# File Name:    TestResultSetting.tcl
# Description:  This script demonstrates how to configure the 
#               TestResultSetting ( TRS ) object and how TRS paths
#               are formed.

#package require SpirentTestCenter
source SpirentTestCenter.tcl

# Create a project.
# Note ConfigurationFileName is not normally required. The framework would 
# typically handle this. It's set here only to show how Test Result Setting ( TRS ) paths are formed. 
stc::create project -Name My_Project -ConfigurationFileName My_Project

# These are the system paths that Spirent Test Center uses to load various system files 
# and write log files to. The user typically does not care about these, but may need
# to know where the system logs are for the session.
puts "System paths\n--------------------"
puts "[stc::perform GetSystemPaths]\n"

# These are the TRS paths used by default.
puts "Default Test result setting paths --------------------\n[stc::perform GetTestResultSettingPaths]\n"

# Notice how -OutputBasePath and -ResultDbBasePath properties are formed for each TRS config change ...

# Change resultsDirectory to my_results
set trs [lindex [stc::get project1 -children-TestResultSetting] 0]
stc::config $trs -saveResultsRelativeTo NONE -resultsDirectory my_results
puts "resultsDirectory changed to my_results --------------------\n[stc::perform GetTestResultSettingPaths]\n"

# Change saveResultsRelativeTo to INSTALL_DIR 
stc::config $trs -saveResultsRelativeTo INSTALL_DIR -resultsDirectory my_results
puts "saveResultsRelativeTo changed to INSTALL_DIR --------------------\n[stc::perform GetTestResultSettingPaths]\n"

# Change saveResultsRelativeTo to CURRENT_WORKING_DIR
stc::config $trs -saveResultsRelativeTo CURRENT_WORKING_DIR -resultsDirectory my_results
puts "saveResultsRelativeTo changed to CURRENT_WORKING_DIR --------------------\n[stc::perform GetTestResultSettingPaths]\n"

# Change saveResultsRelativeTo to USER_WORKING_DIR
stc::config $trs -saveResultsRelativeTo USER_WORKING_DIR -resultsDirectory my_results
puts "saveResultsRelativeTo changed to USER_WORKING_DIR --------------------\n[stc::perform GetTestResultSettingPaths]\n"

# Change saveResultsRelativeTo to CURRENT_CONFIG_DIR
stc::config $trs -saveResultsRelativeTo CURRENT_CONFIG_DIR -resultsDirectory my_results
puts "saveResultsRelativeTo changed to CURRENT_CONFIG_DIR --------------------\n[stc::perform GetTestResultSettingPaths]\n"

# If none of the above suits your needs, you may use an absolute path.
stc::config $trs -saveResultsRelativeTo NONE -resultsDirectory C:/temp
puts "saveResultsRelativeTo changed to an absolute path C:/temp --------------------\n[stc::perform GetTestResultSettingPaths]\n"

