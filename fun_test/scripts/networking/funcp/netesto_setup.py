#!/usr/bin/python
import sys
import os
sys.path.append('/workspace/Integration/fun_test')
from lib.system.fun_test import *
from lib.host.linux import Linux
import pandas as pd
from StringIO import StringIO
import random

controller = 'mpoc-server01'

hosts = []

#for i in range(30,49):
for i in [ '03', '04', '05', '06']:
    hosts.append('mpoc-server' + str(i))

#hosts.append(controller)

fw = open('interface_info', 'w')

etc_hosts = '''
::1     localhost ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
10.80.2.130 mpoc-server30.localadmin mpoc-server30
10.80.2.131 mpoc-server31.localadmin mpoc-server31
10.80.2.132 mpoc-server32.localadmin mpoc-server32
10.80.2.133 mpoc-server33.localadmin mpoc-server33
10.80.2.134 mpoc-server34.localadmin mpoc-server34
10.80.2.135 mpoc-server35.localadmin mpoc-server35
10.80.2.137 mpoc-server37.localadmin mpoc-server37
10.80.2.138 mpoc-server38.localadmin mpoc-server38
10.80.2.140 mpoc-server40.localadmin mpoc-server40
10.80.2.141 mpoc-server41.localadmin mpoc-server41
10.80.2.142 mpoc-server42.localadmin mpoc-server42
10.80.2.143 mpoc-server43.localadmin mpoc-server43
10.80.2.144 mpoc-server44.localadmin mpoc-server44
10.80.2.145 mpoc-server45.localadmin mpoc-server45
10.80.2.146 mpoc-server46.localadmin mpoc-server46
10.80.2.147 mpoc-server47.localadmin mpoc-server47
10.80.2.148 mpoc-server48.localadmin mpoc-server48
10.80.2.101 mpoc-server01.localadmin mpoc-server01
10.80.2.102 mpoc-server02.localadmin mpoc-server02
10.80.2.103 mpoc-server03.localadmin mpoc-server03
10.80.2.104 mpoc-server04.localadmin mpoc-server04
10.80.2.105 mpoc-server05.localadmin mpoc-server05
10.80.2.106 mpoc-server06.localadmin mpoc-server06

20.2.22.3 mpoc-server30t.localadmin mpoc-server30t
20.2.22.2 mpoc-server31t.localadmin mpoc-server31t
20.2.21.4 mpoc-server32t.localadmin mpoc-server32t
20.2.21.3 mpoc-server33t.localadmin mpoc-server33t
20.2.21.2 mpoc-server34t.localadmin mpoc-server34t
20.2.2.3 mpoc-server40t.localadmin mpoc-server40t
20.2.2.2 mpoc-server41t.localadmin mpoc-server41t
20.2.1.4 mpoc-server42t.localadmin mpoc-server42t
20.2.1.3 mpoc-server43t.localadmin mpoc-server43t
20.2.1.2 mpoc-server44t.localadmin mpoc-server44t
20.2.4.3 mpoc-server45t.localadmin mpoc-server45t
20.2.4.2 mpoc-server46t.localadmin mpoc-server46t
20.2.3.3 mpoc-server47t.localadmin mpoc-server47t
20.2.3.2 mpoc-server48t.localadmin mpoc-server48t

20.2.0.2 mpoc-server01t.localadmin mpoc-server01t
20.2.0.3 mpoc-server02t.localadmin mpoc-server02t
20.2.0.4 mpoc-server03t.localadmin mpoc-server03t
20.2.0.5 mpoc-server04t.localadmin mpoc-server04t
20.2.0.6 mpoc-server05t.localadmin mpoc-server05t
20.2.0.7 mpoc-server06t.localadmin mpoc-server06t

'''
interface = {
'mpoc-server30' : 'hu3-f0',
'mpoc-server31' : 'hu1-f0',
'mpoc-server32' : 'hu0-f0',
'mpoc-server33' : 'hu1-f0',
'mpoc-server34' : 'hu2-f0',
'mpoc-server40' : 'hu3-f0',
'mpoc-server41' : 'hu1-f0',
'mpoc-server42' : 'hu0-f0',
'mpoc-server43' : 'hu1-f0',
'mpoc-server44' : 'hu2-f0',
'mpoc-server45' : 'hu3-f0',
'mpoc-server46' : 'hu1-f0',
'mpoc-server47' : 'hu1-f0',
'mpoc-server48' : 'hu2-f0',
'mpoc-server01' : 'enp216s0',
'mpoc-server02' : 'enp216s0',
'mpoc-server03' : 'enp216s0',
'mpoc-server04' : 'enp216s0',
'mpoc-server05' : 'enp216s0',
'mpoc-server06' : 'enp216s0',
}
for host in hosts:
    if 0:

        try:
            netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            for file in ['netesto_fcp_scale.tar.gz', 'netperf-2.7.0-with-patch.gz']:
                netesto_controller.command("wget http://10.1.105.194/"+file)
            # get netesto
            #netesto_controller.command("wget https://fungible.box.com/s/w4qw0qgcuad027cf7dpueblh6n0ucbwg")
            # get netperf
            #netesto_controller.command("wget https://fungible.box.com/s/u732pqsmo68ad420t28mctdv6aggmaxp")
            netesto_controller.sudo_command("apt-get update --fix-missing")

            # Install packages
            packages = ['make','gcc', 'openssh-server', 'sysstat', 'bc', 'ethtool', 'dc', 'tcpdump', 'python']

            for package in packages:
                netesto_controller.sudo_command("apt-get install -y " + str(package))

            # install netperf
            netesto_controller.command("tar -xvf netperf-2.7.0-with-patch.gz")
            netesto_controller.command("cd netperf-netperf-2.7.0 && ./configure --enable-intervals=yes  --enable-demo=yes --enable-histogram=yes && make")
            netesto_controller.sudo_command("make install")

            # untar netesto
            netesto_controller.command("tar -xvf netesto_fcp_scale.tar.gz")

            if host == 'mpoc-server01':
                # Controller setup
                netesto_controller.sudo_command("apt-get update --fix-missing")

                # Install controller packages
                packages = ['apache2', 'nodejs', 'ghostscript']

                for package in packages:
                    netesto_controller.sudo_command("apt-get install -y " + str(package))

                # install matplot lib
                netesto_controller.command("python -m pip install -U pip setuptools && python -m pip install matplotlib")


        except:
             print "ERROR during setup of host " + str(host)


    if 0:
        try:
            netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            netesto_controller.sudo_command("cd ~/netperf-netperf-2.7.0; sudo make clean; ./configure --enable-intervals=yes  --enable-demo=yes --enable-histogram=yes; sudo make; sudo make install ")
            #netesto_controller.sudo_command("cp /etc/hosts /etc/hosts.bak")
            netesto_controller.command("netperf -V")

        except:
            print "ERROR during setup of host " + str(host)

    if 1:
        try:
            netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            #netesto_controller.sudo_command("cp /etc/hosts /etc/hosts.bak")
            netesto_controller.sudo_command("ln -s /usr/bin/python /usr/local/bin/python")
            netesto_controller.command("echo  10.80.2.101 > ~/netesto_git/remote/clients.txt")
            #netesto_controller.sudo_command("wget http://10.1.105.194/hosts")
            #netesto_controller.sudo_command("chmod 777 /etc/hosts")


        except:
            print "ERROR during setup of host " + str(host)

    if 1:
        try:
            netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            packages = ['openssh-server', 'sysstat', 'bc', 'ethtool', 'dc', 'tcpdump', 'python']

            for package in packages:
                netesto_controller.sudo_command("apt-get install -y " + str(package))


        except:
            print "ERROR during setup of host " + str(host)


    if 0:
        try:
            netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            #netesto_controller.sudo_command("cp /etc/hosts /etc/hosts.bak")
            netesto_controller.sudo_command("mv /etc/hosts /etc/hosts.bak ; cd /etc ; wget http://10.1.105.194/hosts; chmod 777 /etc/hosts")
            #netesto_controller.sudo_command("wget http://10.1.105.194/hosts")
            #netesto_controller.sudo_command("chmod 777 /etc/hosts")


        except:
            print "ERROR during setup of host " + str(host)

    if 0:
        try:
            netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            output = netesto_controller.command("ip r show|grep \" src \"|cut -d \" \" -f 3,9")
            fw.writelines("Host: " + host + '\n')
            fw.writelines(output + '\n')
            fw.writelines("#-----------------------#\n")

        except:
            print "ERROR during setup of host " + str(host)




    if 0:
        if host in interface:
            try:
                netesto_controller = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
                netesto_controller.command("sed -i 's/hu2-f0/{INF}/g' ~/netesto_git/remote/doClient.sh".format(INF=interface[host]))
                netesto_controller.command(
                    "sed -i 's/hu2-f0/{INF}/g' ~/netesto_git/remote/netesto.py".format(INF=interface[host]))
                netesto_controller.command(
                    "sed -i 's/hu2-f0/{INF}/g' ~/netesto_git/remote/numa_script.py".format(INF=interface[host]))
                netesto_controller.command(
                    "sed -i 's/eth0/{INF}/g' ~/netesto_git/remote/doServer.sh".format(INF=interface[host]))



            except:
                print "ERROR during setup of host " + str(host)

fw.close()

# Host: mpoc-server30
# eno1 10.80.2.130
# hu3-f0 20.2.22.3
# #-----------------------#
# Host: mpoc-server31
# eno1 10.80.2.131
# hu1-f0 20.2.22.2
# #-----------------------#
# Host: mpoc-server32
# eno1 10.80.2.132
# hu0-f0 20.2.21.4
# #-----------------------#
# Host: mpoc-server33
# eno1 10.80.2.133
# hu1-f0 20.2.21.3
# #-----------------------#
# Host: mpoc-server34
# eno1 10.80.2.134
# hu2-f0 20.2.21.2
# #-----------------------#
# Host: mpoc-server35
# eno1 10.80.2.135
# #-----------------------#
# Host: mpoc-server37
# eno1 10.80.2.137
# #-----------------------#
# Host: mpoc-server38
# eno1 10.80.2.138
# #-----------------------#
# Host: mpoc-server40
# eno1 10.80.2.140
# hu3-f0 20.2.2.3
# #-----------------------#
# Host: mpoc-server41
# eno1 10.80.2.141
# hu1-f0 20.2.2.2
# #-----------------------#
# Host: mpoc-server42
# eno1 10.80.2.142
# hu0-f0 20.2.1.4
# #-----------------------#
# Host: mpoc-server43
# eno1 10.80.2.143
# hu1-f0 20.2.1.3
# #-----------------------#
# Host: mpoc-server44
# eno1 10.80.2.144
# hu2-f0 20.2.1.2
# #-----------------------#
# Host: mpoc-server45
# eno1 10.80.2.145
# #-----------------------#
# Host: mpoc-server46
# eno1 10.80.2.146
# #-----------------------#
# Host: mpoc-server47
# eno1 10.80.2.147
# #-----------------------#
# Host: mpoc-server48
# eno1 10.80.2.148
# #-----------------------#
# Host: mpoc-server01
# eno1 10.80.2.101
# enp216s0 20.2.0.2
# #-----------------------#
