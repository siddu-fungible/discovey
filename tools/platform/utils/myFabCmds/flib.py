from fabric.api import *
from fabric.contrib.files import exists, append
import time, re, os
import pexpect, sys
import pprint
import socket
import tempfile

from mysetups import *

class Exception(BaseException):
    pass

import signal
import sys

child = None

def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        sys.stdout.flush()
        if child:
            child.close()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


#####################################################################################
####################### ALL TASK FROM HERE ##########################################
#####################################################################################

NFSPATH  = env.NFSSERVER + ":" + env.DEFAULT_NFSFILE
TFTPPATH = env.TFTPSERVER + ":" + env.DEFAULT_TFTPFILE
BOOTARGS = env.DEFAULT_BOOTARGS

def _runme_too(cmd):
    run(cmd + ' -a')

@task
def sample_usage(cmd):
    """ demo : sample use cases """
    run(cmd)
    execute(_runme_too, cmd)
    execute(_runme_too, cmd, hosts="localadmin@10.1.21.48")

@roles('bmc')
def _deploy_bmc():
    with settings(hide('stdout', 'stderr'), warn_only=True):
        o = run('ls -l /mnt/sdmmc0p1/_install/web/fungible/RUN_TCP_PYSERIAL.sh')
        if o.return_code == 0:
            print "[%s] essentials already installed on ... \n" % (env.host_string)
        else:
            with cd('/mnt/sdmmc0p1/_install'):
                with settings(hide('stdout', 'stderr')):
                    run('wget -O pyserial-install.tar http://vnc-shared-06.fungible.local:9669/pkgs/for-f1/pyserial-install.tar')

                    run('tar xvf pyserial-install.tar')
                    run('rm -f pyserial-install.tar')
                    print "[%s] essentials installed on ... \n" % (env.host_string)

@roles('come')
def _deploy_come():
    """deploy neccessary stuff on node provided"""
    pass

@task
def deploy_pkgs(on='bmc'):
    """deploy neccessary stuff on node provided"""
    if 'bmc' in on:
        execute(_deploy_bmc, hosts=env.thissetup['bmc'][3])

    if 'come' in on:
        execute(_deploy_come, hosts=env.thissetup['come'][3])

@task
def setup(name="FS0", details=False):
    """Initialize the working setup and its role definitions"""
    if name not in env.setups:
        raise ValueError("Setup name %s is not defined ..." % name)
    else:
        env.setdefault('thissetup', dict()).update(env.setups[name])
        env.roledefs.update(map(lambda (k,v): (k, [v[3]]), env.thissetup.iteritems()))
        print "Initialize this setup and roledefs definitions ..."
        if details:
            #pprint.pprint(env.thissetup)
            for node in env.thissetup.keys():
                with settings( hide('stdout', 'stderr', 'running')):
                    try:
                        local("ping -c 1 %s" % env.thissetup[node][0])
                        print "setup %s (%s) [%s] ... up." % (name, node, env.thissetup[node][0])
                    except:
                        print "Alert! setup %s (%s)[%s] ... down." % (name, node, env.thissetup[node][0])

@roles('ipmi')
def discover_management():
    """ list a system management (bmc) ip"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            cmd = "ipmitool -I lanplus -H {} -U {} -P {} lan print".format(*ipmi_credentials)
            mgmtip = local(cmd + " | grep -E 'IP Address\s+:' | awk -F: '{print $2}'", capture=True)
            if mgmtip.return_code == 0:
                print "[%s] discover_management info ... %s" % (env.host_string, mgmtip)
                return mgmtip
            else:
                raise ValueError("Cannot determine requested info ...")

#@task
@roles('ipmi')
def get_dcmi_sensors(verbose=False):
    """get sensor database from ipmi using the DCMI subsystem"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            cmd = "ipmitool -I lanplus -H {} -U {} -P {} dcmi get_temp_reading".format(*ipmi_credentials)
            info = local(cmd, capture=True)
            if info.return_code == 0:
                print "[%s] get_dcmi_sensors info ... \n%s" % (env.host_string, info)
                return info
            else:
                raise ValueError("Cannot determine requested info ...")

#@task
@roles('ipmi')
def get_dcmi_records(verbose=False):
    """get record database from ipmi using the DCMI subsystem"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            cmd = "ipmitool -I lanplus -H {} -U {} -P {} dcmi sensors".format(*ipmi_credentials)
            info = local(cmd, capture=True)
            if info.return_code == 0:
                print "[%s] get_dcmi_records info ... \n%s" % (env.host_string, info)
                return info
            else:
                raise ValueError("Cannot determine requested info ...")

#@task
@roles('ipmi')
def get_fan_sensors(verbose=False):
    """get fan sensors from ipmi using the native subsystem over lanplus interface"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            if verbose:
                cmd = "ipmitool -I lanplus -H {} -U {} -P {} sensor".format(*ipmi_credentials)
            else:
                cmd = "ipmitool -I lanplus -H {} -U {} -P {} sdr".format(*ipmi_credentials)
            info = local(cmd + " | grep -E '^Fan'", capture=True)
            if info.return_code == 0:
                print "[%s] get_fan_sensors info ... \n%s" % (env.host_string, info)
                return info
            else:
                raise ValueError("Cannot determine requested info ...")

#@task
@roles('ipmi')
def get_chip_sensors(verbose=False):
    """get chip sensors from ipmi using the native subsystem over lanplus interface"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            if verbose:
                cmd = "ipmitool -I lanplus -H {} -U {} -P {} sensor".format(*ipmi_credentials)
            else:
                cmd = "ipmitool -I lanplus -H {} -U {} -P {} sdr".format(*ipmi_credentials)
            info = local(cmd + " | grep -E '^F1'", capture=True)
            if info.return_code == 0:
                print "[%s] get_chip_sensors info ... \n%s" % (env.host_string, info)
                return info
            else:
                raise ValueError("Cannot determine requested info ...")

#@task
@roles('ipmi')
def get_temperature_readings():
    """get temperature readings from ipmi using the DCMI subsystem"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            cmd = "ipmitool -I lanplus -H {} -U {} -P {} dcmi get_temp_reading".format(*ipmi_credentials)
            info = local(cmd, capture=True)
            if info.return_code == 0:
                print "[%s] get_temperature_readings info ... \n%s" % (env.host_string, info)
                return info
            else:
                raise ValueError("Cannot determine requested info ...")

#@task
@roles('ipmi')
def get_temperature_sensors():
    """get temperature sensors from ipmi using the DCMI subsystem"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
            ipmi_credentials = env.thissetup['ipmi'][0:3]
            cmd = "ipmitool -I lanplus -H {} -U {} -P {} dcmi sensors".format(*ipmi_credentials)
            info = local(cmd, capture=True)
            if info.return_code == 0:
                print "[%s] get_temperature_sensors info ... \n%s" % (env.host_string, info)
                return info
            else:
                raise ValueError("Cannot determine requested info ...")

def alive(host):
    """ guess if a host is alive"""
    try:
        #with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
        with quiet():
            o = local("ping -c 2 %s" % host)
            if o.return_code == 0:
                return True
    except:
        return False

def wait_until_alive(host, wait=300):
    """ guess if a host is alive; else giveup in %s seconds """ % wait
    datefmt = '%m-%d-%Y %H:%M:%S'
    start = time.time()
    count = 0
    print "[%s] attempting to connect to (%s) at %s ..." % (env.host_string, host, time.strftime(datefmt))
    while True:
        if alive(host):
            break
        else:
            time.sleep(10)
            count += 10
            print " [%03d]" % count,
            sys.stdout.flush()
            if time.time() - start > wait :
                print "fail"
                return False
    #below sleep is for ssh layer to be up after network interface is up.
    time.sleep(15)
    print "ok"
    return True

@task
@roles('come')
def warmboot(waitfor=500):
    """ COMe reboot a system with os command and waitfor x seconds for it to come alive """
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
        print "[%s] waiting for %s sec for system to boot ..." % (env.host_string, waitfor)
        reboot(wait=waitfor)
    run('date')

#@task
def ospoweroff(waitfor=30):
    """ poweroff a system with os command and waitfor x seconds for it to cleanly shutdown"""
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
        print "[%s] waiting for %s sec for system to poweroff ..." % (env.host_string, waitfor)
        run('poweroff')
        time.sleep(waitfor)

def oscoldboot(waitfor=600):
    """ coldboot directly using a mgmt ip and waitfor x seconds for server to be alive """
    from fabric.network import disconnect_all
    with settings( hide('stdout', 'stderr', 'running'), warn_only=True ):
        mgmtip = discover_management()
        run('poweroff')
        time.sleep(20)
        disconnect_all()
    local('ipmitool -I lanplus -H %s -U %s -P %s power status' % (mgmtip, env.user, env.password))
    local('ipmitool -I lanplus -H %s -U %s -P %s power on' % (mgmtip, env.user, env.password))
    print "[%s] waiting for %s sec for system to boot ..." % (env.host_string, waitfor)
    if not wait_until_alive(env.host_string, waitfor):
        raise RuntimeError("Cannot power-on system in %s seconds ... giving up ..." % waitfor)
    run('date')

@task
def poweroff():
    """ poweroff host using ipmi subsystem """
    with settings( hide('stderr', 'running'), warn_only=True ):
        ipmi_credentials = env.thissetup['ipmi'][0:3]
        local("ipmitool -I lanplus -H {} -U {} -P {} power status".format(*ipmi_credentials))
        local("ipmitool -I lanplus -H {} -U {} -P {} power off".format(*ipmi_credentials))

@task
def poweron():
    """just poweron host using ipmi subsystem"""
    with settings( hide('stderr', 'running'), warn_only=True ):
        ipmi_credentials = env.thissetup['ipmi'][0:3]
        local("ipmitool -I lanplus -H {} -U {} -P {} power status".format(*ipmi_credentials))
        local("ipmitool -I lanplus -H {} -U {} -P {} power on".format(*ipmi_credentials))

@task
def powerstatus():
    """ status directly using a mgmt ip """
    with settings( hide('stderr', 'running'), warn_only=True ):
        ipmi_credentials = env.thissetup['ipmi'][0:3]
        local("ipmitool -I lanplus -H {} -U {} -P {} power status".format(*ipmi_credentials))

@task
def powercycle(waitfor=500):
    """power-off and power-on host using ipmi subsystem"""
    with settings( hide('stderr', 'running'), warn_only=True ):
        ipmi_credentials = env.thissetup['ipmi'][0:3]
        local("ipmitool -I lanplus -H {} -U {} -P {} power status".format(*ipmi_credentials))
        local("ipmitool -I lanplus -H {} -U {} -P {} power off".format(*ipmi_credentials))
        time.sleep(5)
        local("ipmitool -I lanplus -H {} -U {} -P {} power status".format(*ipmi_credentials))
        local("ipmitool -I lanplus -H {} -U {} -P {} power on".format(*ipmi_credentials))
        print "[%s] waiting for %s sec for system to boot ..." % (env.host_string, waitfor)
        if not wait_until_alive(env.thissetup['come'][0], waitfor):
            raise RuntimeError("Cannot power-on system in %s seconds ... giving up ..." % waitfor)


@task
def poweronandwait(waitfor=500):
    """poweron host using ipmi subsystem"""
    with settings( hide('stderr', 'running'), warn_only=True ):
        ipmi_credentials = env.thissetup['ipmi'][0:3]
        local("ipmitool -I lanplus -H {} -U {} -P {} power status".format(*ipmi_credentials))
        local("ipmitool -I lanplus -H {} -U {} -P {} power on".format(*ipmi_credentials))
        print "[%s] waiting for %s sec for system to boot ..." % (env.host_string, waitfor)
        if not wait_until_alive(env.thissetup['come'][0], waitfor):
            raise RuntimeError("Cannot power-on system in %s seconds ... giving up ..." % waitfor)

pci_table = {
    "fs1600"     : ("1dad" , "1000" , "1590" , "021e"),
}

@roles('come')
@task 
def show_dev():
    """Query fungible device on pcie from COMe system"""
    return sudo('lspci -d1dad: -Dnnmm')

@roles('come')
@task
def ssdon(index=0, slot=0):
    """poweron fungible SSD device on pcie from COMe system"""
    with settings( hide('stderr', 'running'), warn_only=True ):
        O = dpcshF(index=index, cmd='slot output {"slot": %s, "type": "hotswap", "action":"on" }' % slot)
        if '"result": true' not in O.stdout: raise "SSD slot %s power on failed ..." % slot
        O = dpcshF(index=index, cmd='slot input {"slot": %s, "type":"powergood"}' % slot)
        if '"input": 0' not in O.stdout: raise "SSD slot %s power still off ..." % slot
        print "[%s] dpu=%s ssdslot=%s powered-on with success ..." % (env.host_string, index, slot)

@roles('come')
@task
def ssdoff(index=0, slot=0):
    """poweroff fungible SSD device on pcie from COMe system"""
    with settings( hide('stderr', 'running'), warn_only=True ):
        O = dpcshF(index=index, cmd='slot output {"slot": %s, "type": "hotswap", "action":"off" }' % slot)
        if '"result": true' not in O.stdout: raise "SSD slot %s power off failed ..." % slot
        O = dpcshF(index=index, cmd='slot input {"slot": %s, "type":"powergood"}' % slot)
        if '"input": 1' not in O.stdout: raise "SSD slot %s power still on ..." % slot
        print "[%s] dpu=%s ssdslot=%s powered-off with success ..." % (env.host_string, index, slot)

@roles('come')
@task
def show_ssd(index=0):
    """Query fungible SSD device on pcie from COMe system"""
    return dpcshF(index=index, cmd='peek nvme/ssds/info')

@roles('come')
@task
def show_ports(index=0):
    """Query fungible fpg device on pcie from COMe system"""
    return dpcshF(index=index, cmd='port linkstatus')

@roles('come')
@task 
def rescan_pcie():
    """perform pcie rescan from COMe system"""
    sudo('echo 1 > /sys/bus/pci/rescan')

### no stable yet !!!
@roles('bmc')
@task
def bmcresetF(index=0):
    """ reset the chip from BMC system"""
    with cd('/mnt/sdmmc0p1/scripts'), settings( hide('stderr'), warn_only=True ):
        run("bash ./REV2_f1_reset.sh %s" % index)

@roles('fpga')
@task
def fpgaresetF(index=0):
    """ reset the chip from FPGA system"""
    #env.password = 'root'
    run('/home/root/f1reset -s {} 0 && sleep 2 && /home/root/f1reset -s {} 1 && /home/root/f1reset -g && sleep 1'.format(index, index), shell=False)

@roles('bmc')
@task
def get_fs_rev():
    """ get FS1600 platform revision """
    with settings( hide('stderr', 'running'), warn_only=True ):
        o =  run("cd /mnt/sdmmc0p1/scripts && gpiotool 8 --get-data | grep High >/dev/null 2>&1 && echo FS1600_REV2 || echo FS1600_REV1")
        if o.return_code == 0: return o.stdout

@roles('bmc')
@task
def resetF(index=0):
    revstring = execute(get_fs_rev)
    if 'REV1' in revstring.values()[0] :
        execute(fpgaresetF, index=index)
    elif 'REV2' in revstring.values()[0] :
        execute(bmcresetF, index=index)
    else:
        raise('Unknown platform revision ...')

@roles('bmc')
@task
def get_bmc_info():
    """ get FS1600 bmc platform revision """
    run("uname -a")
    run("cat /proc/ractrends/Helper/FwInfo")

@roles('fpga')
@task
def get_fpga_info():
    """ get FS1600 fpga platform revision """
    run("uname -a", shell=False)
    run("cat /etc/angstrom-version", shell=False)
    run("cat /etc/machine-id", shell=False)

@roles('come')
@task
def get_come_info():
    """ get FS1600 come platform revision """
    run("uname -a")
    run("cat /etc/lsb-release")

@roles('fpga')
@task
def get_platform_info():
    """ get FS1600 platform revision """
    execute(get_bmc_info)
    execute(get_fpga_info)
    execute(get_come_info)

@roles('bmc')
@task
def check_serial_sockets():
    """ check if tcp sockets are running to replay serial interfaces /dev/ttySD """
    with settings( hide('stderr', 'running'), warn_only=True ):
        try:
            o = run("ps -ef | grep tcp_serial_redirect | grep -v grep")
            return True if len(map(lambda l: l.split()[1], o.splitlines())) == 2 else False
        except:
            return False

@roles('bmc')
#@task
def start_serial_sockets():
    """ start tcp sockets to replay serial interfaces /dev/ttySD """
    with settings( hide('stderr', 'running'), warn_only=True ):
        try:
            run("ps -ef | grep tcp_serial_redirect | grep -v grep")
            print "Sockets servers are already started ..."
            return True #map(lambda l: l.split()[1], o.splitlines())
        except:
            with settings( hide('stderr', 'stdout'), warn_only=True ):
                run("rm /var/local/LCK*ttyS")
                run("bash /mnt/sdmmc0p1/_install/web/fungible/RUN_TCP_PYSERIAL.sh")
                time.sleep(5)
                run("ps -ef | grep tcp_serial_redirect | grep -v grep")

#@task
def disable_pcie(bus=None):
    unload_fun_drivers()
    pfs = get_pcie_functions(bus)
    for pf in pfs.splitlines():
        sudo('echo 1 > /sys/bus/pci/devices/0000:%s/remove'%pf)


@roles('bmc')
@task
def stop_serial_sockets():
    """ kill and restart the relay socket for serial consoles on BMC """
    with settings(hide('stdout'), warn_only=True ):
        run("ps -ef | grep -v grep | grep tcp_serial | grep ttyS0 | awk '{print $2}' | xargs kill -9")
        run("ps -ef | grep -v grep | grep tcp_serial | grep ttyS2 | awk '{print $2}' | xargs kill -9")
        time.sleep(3)
        run("ps -ef | grep tcp_serial")
        time.sleep(3)

@roles('bmc')
@task
def restart_serial_sockets():
    """ kill and restart the relay socket for serial consoles on BMC """
    with settings(hide('stdout'), warn_only=True ):
        run("ps -ef | grep -v grep | grep ttyS0 | awk '{print $2}' | xargs kill -9")
        run("ps -ef | grep -v grep | grep ttyS2 | awk '{print $2}' | xargs kill -9")
        run("ps -ef | grep -v grep | grep F1_CON | awk '{print $2}' | xargs kill -9")
        run("rm -rf /var/lock/LCK..ttyS0")
        run("rm -rf /var/lock/LCK..ttyS2")
        time.sleep(3)
        run("ps -ef | grep tcp_serial")
        run("sh /mnt/sdmmc0p1/_install/web/fungible/RUN_TCP_PYSERIAL.sh", pty=False, combine_stderr=True)
        time.sleep(5)
        run("ps -ef | grep tcp_serial")
        time.sleep(3)

@roles('bmc')
@task
def connectF(index=0, reset=False, force=True):
    """ connect to chip[index] with reset """
    global child
    try:
        child = pexpect.spawn('nc {} 999{}'.format(env.host, index))
        child.logfile = sys.stdout
        if reset:
            execute(resetF, index=index)
            try:
                i = child.expect (['\nAutoboot in 5 seconds.', '\nf1 # '])
                if i==0:
                    child.sendline ('noboot')
                else:
                    child.sendline ('echo pass')
                child.expect ('\nf1 # ')
            except:
                SESSION_ERROR_MSG = "\n\nspawn error: check why serial sockets are failing on {}\n\n".format(env.host) 
                sys.exit(SESSION_ERROR_MSG)
            else:
                pass
    except:
        SESSION_BUSY_MSG = "\n\ntimeout: check if any other session holding connection ... to {}:999{}\n\n".format(env.host, index) 
        sys.exit(SESSION_BUSY_MSG)

    child.sendline ('echo uboot connect chip={} done...'.format(index))
    child.expect ('\nf1 # ')
    return child

def _mac_random_mac(index=0):
    ip = env.thissetup['bmc'][0]
    a,b,c,d = socket.gethostbyname(ip).split('.')
    return ':'.join(['02'] + [ '1d', 'ad', "%02x"%int(c), "%02x"%int(d)]  + ["%02x" % int(index)])

def _make_gateway(index=0):
    ip = env.thissetup['bmc'][0]
    a,b,c,d = socket.gethostbyname(ip).split('.')
    return '.'.join([a, b, c, '1'])

## flash image ##
@roles('bmc')
@task
def flashF(index=0, flags=False, type=None, image=None, version=None, old=True):
    """ flash image of chip[index] over type tftp with provided arguments """
    global child
    CCHUID = 3 - int(index)
    bootargs = 'cc_huid={} sku=SKU_FS1600_{} app=fw_upgrade syslog=6 boot-reserved=0x2000000@0x12000000 '.format(CCHUID, index)
    #print bootargs

    command = 'tftpboot'
    if image and version:
        sys.exit("image-path and version are multually exclusive ...")

    if version:
        if type not in [ 'pufr', 'frmw', 'eepr', 'host', 'emmc', 'sbpf', 'husd', 'husm', 'hbsb' ]:
            sys.exit("image-type %s not-supported only=['pufr', 'frmw', 'sbpf', 'eepr', 'host', 'emmc', 'husd', 'husm', 'hbsb' ] ..." % type)
        elif type == 'eepr':
            fimage='funsdk-release/{}/eeprom_fs1600_{}_packed.bin'.format(version, index)
        elif type == 'host':
            fimage='funsdk-release/{}/host_firmware_packed.bin'.format(version)
        elif type == 'emmc':
            fimage='funsdk-release/{}/emmc_image.bin'.format(version)
        elif type == 'sbpf':
            fimage='funsdk-release/{}/esecure_firmware_all.bin'.format(version)
        elif type == 'pufr':
            fimage='funsdk-release/{}/esecure_puf_rom_packed.bin'.format(version)
        elif type == 'frmw':
            fimage='funsdk-release/{}/esecure_firmware_packed.bin'.format(version)
        elif type == 'husd':
            fimage='funsdk-release/{}/hu_sds.bin'.format(version)
        elif type == 'husm':
            fimage='funsdk-release/{}/hu_sbm.bin'.format(version)
        elif type == 'hbsb':
            fimage='funsdk-release/{}/hbm_sbus.bin'.format(version)
        else:
            sys.exit("image-type %s not-supported ..." % type)
    elif image:
        fimage = image

    with settings(hide('stdout', 'stderr')):
        try:
            local('wget -O /tmp/wgetfile http://vnc-shared-06.fungible.local:9669/{}'.format(fimage))
        except:
            sys.exit("ERROR: image not present in release directory ...")

    st = os.stat('/tmp/wgetfile')
    fsize = st.st_size
    FLAGS = "" if not flags else ":%s" % flags
    bootargs += 'fw-upgrade-{}={}@0xa800000080000000{}'.format(type, fsize, FLAGS)
    print bootargs

    child = connectF(index, True)
    child.sendline ('echo connected to chip={} ...'.format(index))
    child.expect ('\nf1 # ')
    child.sendline ('setenv ethaddr %s' % _mac_random_mac(index))
    child.expect ('\nf1 # ')
    child.sendline ('setenv autoload no')
    child.expect ('\nf1 # ')
    child.sendline ('lmpg;lfw;ltrain;ls;')
    child.expect ('\nf1 # ')
    child.sendline ('setenv gatewayip %s' % _make_gateway(index))
    child.expect ('\nf1 # ')
    child.sendline ('dhcp')
    child.expect ('\nf1 # ')
    child.sendline ('setenv serverip {}'.format(env.TFTPSERVER))
    child.expect ('\nf1 # ')
    child.sendline ('setenv bootargs {}'.format(bootargs))
    child.expect ('\nf1 # ')
    child.sendline ('setenv bootcmd ""')
    child.expect ('\nf1 # ')
    child.sendline ('printenv')
    child.expect ('\nf1 # ')
    child.sendline('{} 0xa800000080000000 {}:{};'.format(command, env.TFTPSERVER, fimage))
    child.expect ('\nf1 # ')
    if old:
        child.sendline('{} 0xffffffff99000000 {}:funsdk-release/latest/funos-f1.stripped;'.format(command, env.TFTPSERVER))
    else:
        child.sendline('{} 0xffffffff99000000 {}:funsdk-release/latest/funos.signed.bin;authfw 0xffffffff99000000'.format(command, env.TFTPSERVER))
    child.expect ('\nf1 # ')
    child.sendline ('echo booting to chip={} ...'.format(index))
    child.expect ('\nf1 # ')
    if old:
        child.sendline('bootelf -p 0xffffffff99000000')
    else:
        child.sendline('bootelf -p ${loadaddr}')
    try:
        child.expect ('\nf1 # ', timeout=30)
    except:
        SESSION_ACTIVE_MSG = "\n\ntimeout: Seem DPU are actively flashed image. monitor nc {} 999{}\n\n".format(env.host, index)
        sys.exit(SESSION_ACTIVE_MSG)
        child.close()

@roles('come')
#@task
def fwupgrade(index=0, flags=False, type=None, image=None, version=None):
    """ flash image of chip[index] over type tftp with provided arguments """
    global child
    if image and version:
        sys.exit("image-path and version are multually exclusive ...")
    if '"Unassigned class [ff00]" "Vendor [1dad]"' not in show_dev():
        sys.exit("Fungible control function is NOT discovered ...")


@roles('come')
@task
def deploy_dpcsh_install_dependencies():
    with settings(hide('stdout', 'stderr'), warn_only=True):
        o = run('mkdir -p ~/tools/dpudebug')
        with cd('~/tools/dpudebug'):
            run('wget http://dochub.fungible.local/doc/jenkins/funsdk/latest/Linux/dpcsh.tgz')
            run('tar xvf dpcsh.tgz')

@roles('come')
#@task
def check_dpcsh_install_dependencies():
    """ check depencencies for dpcsh """
    dpcsh_directory = '/home/fun/tools/dpudebug/bin/Linux'
    dpcsh_binary = dpcsh_directory + '/dpcsh'
    if not exists(dpcsh_binary, use_sudo=True):
        deploy_dpcsh_install_dependencies()

@roles('come')
@task
def dpcshF(index=0, cmd=None):
    """ execute a dpcsh command over NVMe e.g dpcshF:cmd="peek storage" """
    dpcsh_directory = '/home/fun/tools/dpudebug/bin/Linux'
    O = show_dev()
    if '[0108]" "Vendor [1dad]"' not in O:
        sys.exit("Fungible NVMe control function is NOT discovered ...")
    #if index == 0 and '0000:04:00.2' not in O:
    #    sys.exit("Fungible DPU#0 control function is NOT discovered ...")
    #if index == 1 and '0000:06:00.2' not in O:
    #    sys.exit("Fungible DPU#1 control function is NOT discovered ...")
    check_dpcsh_install_dependencies()
    dev = '/dev/nvme0' if (int(index) == 0 and '0000:04:00.2' in O) else '/dev/nvme1' if (int(index) == 1 and any(x in O for x in ['0000:05:00.2', '0000:06:00.2'])) else '/dev/null'
    with cd(dpcsh_directory):
        return sudo('./dpcsh --pcie_nvme_sock=%s --nvme_cmd_timeout=60000 --nocli %s' % (dev, cmd))

def check_file_unsigned(image=TFTPPATH, type='tftp'):
    (server, filename) = image.split(':')
    with settings(warn_only=True):
        o = run('file -L -z /tftpboot/{} | grep ELF && true || false'.format(filename))
        status = True if o.return_code == 0 else False
        print ("{} file downloaded - {} seem {} ...".format(type, filename, 'unsigned' if status == True else 'signed'))
        return status

@roles('bmc')
@task
def imageF(index=0, server=env.TFTPSERVER, imagefile=env.DEFAULT_TFTPFILE, type='tftp', selfip=None):
    """ upgrade image of chip[index] over type [nfs|tftp] with provided arguments """
    global child
    image = "%s:%s" % (server, imagefile)
    env.signed_image = True if '.signed' in image else False
    print ("{} file {} seem {} ...".format(type, image, 'signed' if env.signed_image == True else 'unsigned'))
    command = 'nfs' if 'nfs' in type else 'tftpboot'
    child = connectF(index, True)
    child.sendline ('echo connected to chip={} ...'.format(index))
    child.expect ('\nf1 # ')
    child.sendline ('setenv ethaddr %s' % _mac_random_mac(index))
    child.expect ('\nf1 # ')
    child.sendline ('setenv autoload no')
    child.expect ('\nf1 # ')
    child.sendline ('lmpg;lfw;ltrain;ls;')
    child.expect ('\nf1 # ')
    child.sendline ('setenv gatewayip %s' % _make_gateway(index))
    child.expect ('\nf1 # ')
    if selfip:
        child.sendline ('setenv ipaddr %s' % selfip)
        child.expect ('\nf1 # ')
    else:
        child.sendline ('dhcp')
        child.expect ('\nf1 # ')
    child.sendline ('setenv serverip {}'.format(server))
    child.expect ('\nf1 # ', timeout=10)
    child.sendline ('printenv')
    child.expect ('\nf1 # ')
    if '.gz' in image:
        child.sendline('{} 0xa800000080000000 {}; unzip 0xa800000080000000 0xffffffff99000000;'.format(command, image))
    else:
        child.sendline('{} 0xffffffff99000000 {};'.format(command, image))
    child.expect ('hex\)\r\r\n')

    time.sleep(2)
    child.sendline('authfw 0xffffffff99000000;')
    child.expect ('authentication OK\r\r\nf1 # ')

    child.close()

@roles('bmc')
@task
def nfsF(index=0, server=env.NFSSERVER, imagefile=env.DEFAULT_NFSFILE, selfip=None):
    """ upgrade image of chip[index] over NFS with provided arguments """
    imageF(index=index, server=server, imagefile=imagefile, type='nfs', selfip=selfip)

@roles('bmc')
@task
def tftpF(index=0, server=env.TFTPSERVER, imagefile=env.DEFAULT_TFTPFILE, selfip=None):
    """ upgrade image of chip[index] over TFTP with provided arguments """
    imageF(index=index, server=server, imagefile=imagefile, type='tftp', selfip=selfip)

@roles('bmc')
@task
def argsF(index=0, bootargs=BOOTARGS):
    """ set bootargs of chip[index] with provided arguments """
    global child
    CCHUID = 3 - int(index)
    bootargs = 'cc_huid={} '.format(CCHUID) + bootargs
    bootargs = 'sku=SKU_FS1600_{} '.format(index) + bootargs
    child = connectF(index, reset=False)
    child.sendline ('echo connected to chip={} ...'.format(index))
    child.expect ('\nf1 # ')
    child.sendline('setenv bootargs %s' % (bootargs))
    child.expect ('\nf1 # ')
    child.sendline('printenv')
    child.expect ('\nf1 # ')
    child.close()

@roles('bmc')
@task
def bootF(index=0):
    """ boot the image on chip[index] """
    global child
    print ("downloaded file was {} ...".format('signed' if env.signed_image == True else 'unsigned'))
    child = connectF(index, False)
    child.sendline ('echo connected to chip={} ...'.format(index))
    child.expect ('\nf1 # ')
    if env.signed_image:
        child.sendline('bootelf -p ${loadaddr};')
    else:
        child.sendline('bootelf -p 0xffffffff99000000;')
    try:
        i = child.expect (['Image not authorised', '\nf1 #'], timeout=20)
        if i == 0:
            raise("\n\nnewer uboot strictly boot only SIGNED IMAGES ... please compile with SIGN=1 ...\n\n")
        if i == 1:
            raise("\n\nSeem DPU did not boot. User intervention required !!! ...\n\n")
    except pexpect.TIMEOUT as e:
        SESSION_ACTIVE_MSG = "\n\ntimeout: Seem DPU are actively booted up. Kindly monitor using cmd= nc {} 999{}\n\n".format(env.host, index) 
        child.close()
        sys.exit(SESSION_ACTIVE_MSG)

@roles('bmc')
#@task
def redfish_systems():
    """ get system information via redfish  """
    with prefix('source ~/py3venv/bin/activate'):
        redfish_credentials = env.thissetup['rf'][0:3]
        rfcmd = "redfishtool -r {} -u {} -p {} -A Basic -S Always Systems".format(*redfish_credentials)
        local(rfcmd)

@roles('bmc')
#@task
def redfish_chassis():
    """ get chassis information via redfish  """
    with prefix('source ~/py3venv/bin/activate'):
        redfish_credentials = env.thissetup['rf'][0:3]
        rfcmd = "redfishtool -r {} -u {} -p {} -A Basic -S Always Chassis".format(*redfish_credentials)
        local(rfcmd)

@roles('bmc')
#@task
def redfish_power():
    """ get power sensor information via redfish  """
    with prefix('source ~/py3venv/bin/activate'):
        redfish_credentials = env.thissetup['rf'][0:3]
        rfcmd = "redfishtool -r {} -u {} -p {} -A Basic -S Always Chassis -1 Power".format(*redfish_credentials)
        local(rfcmd)

@roles('bmc')
@task
def redfish_thermals():
    """ get thermal sensor information via redfish  """
    with prefix('source ~/py3venv/bin/activate'):
        redfish_credentials = env.thissetup['rf'][0:3]
        rfcmd = "redfishtool -r {} -u {} -p {} -A Basic -S Always Chassis -1 Thermal".format(*redfish_credentials)
        local(rfcmd)

@roles('bmc')
@task
def redfish_fans():
    """ get fan sensor information via redfish  """
    with prefix('source ~/py3venv/bin/activate'):
        redfish_credentials = env.thissetup['rf'][0:3]
        rfcmd = "redfishtool -r {} -u {} -p {} -A Basic -S Always Chassis -1 Thermal".format(*redfish_credentials)
        local(rfcmd)

def redfish_generic(tag='Systems'):
    """ get generic redfish-data """
    with prefix('source ~/py3venv/bin/activate'):
        redfish_credentials = env.thissetup['rf'][0:3]
        rfcmd = "redfishtool -r {} -u {} -p {} -A Basic -S Always ".format(*redfish_credentials) + tag
        local(rfcmd)
