#! /bin/bash

network=${1:-"10.1.105.0/24"}
mymac=${2:-"02:68:B3:29:DA:42"}  #(This is always religiously entered by Platform’s team in confluence).

###########################################################################
#on any linux host prefrebaly COMe on that *network*, use below command -
###########################################################################
sudo nmap -sP -n $network | awk '/Nmap scan report for/{printf $5;}/MAC Address:/{print " => "$3;}' | sort  | grep -i $mymac
