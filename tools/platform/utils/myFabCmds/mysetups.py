from fabric.api import env


###################################################################################
# Set below values if you keep your image at same path after build
# default kept this some dummy values to avoid booting from any-image
###################################################################################
env.DEFAULT_NFSFILE   = "/home/user/tftpboot/funos-f1.signed"
env.DEFAULT_TFTPFILE = "user/tftpboot/funos-f1.signed"
env.DEFAULT_BOOTARGS = 'app=load_mods --serial --all_100g --dpc-server --dpc-uart syslog=6 workload=storage'

###################################################################################
env.NFSSERVER = "10.1.20.54"
env.TFTPSERVER = "10.1.21.48"

env.TFTPROOT = "localadmin"
env.TFTPPASS = "Precious1*"
env.TFTPPATH = '/tftpboot'
###########   ADD YOU FS BOX DETAILS BELOW  #######################################
setups = {
    'FS2' : {
        'bmc'  : [ '10.1.40.110', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.40.110', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.40.110', 'admin', 'admin' ],
        'fpga' : [ '10.1.40.138', 'root', '""' ],
        'come' : [ '10.1.40.131', 'fun', '123' ]
    },
    'FS4' : {
        'bmc'  : [ '10.1.40.163', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.163', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.163', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.122', 'root', '""' ],
        'come' : [ '10.1.20.164', 'fun', '123' ]
    },
    #'FS6' : {
    #    'bmc'  : [ '10.1.20.153', 'sysadmin', 'superuser' ],
    #    'rf'   : [ '10.1.20.153', 'Administrator', 'superuser' ],
    #    'ipmi' : [ '10.1.20.153', 'admin', 'admin' ],
    #    'fpga' : [ '10.1.20.124', 'root', '""' ],
    #    'come' : [ '10.1.20.154', 'fun', '123' ]
    #},
    'FS7' : {
        'bmc'  : [ '10.1.20.19', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.19', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.19', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.157', 'root', '""' ],
        'come' : [ '10.1.20.129', 'fun', '123' ]
    },
    'FS9' : {
        'bmc'  : [ '10.1.21.212', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.21.212', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.21.212', 'admin', 'admin' ],
        'fpga' : [ '10.1.21.211', 'root', '""' ],
        'come' : [ '10.1.21.213', 'fun', '123' ]
    },
    'FS11' : {
        'bmc'  : [ '10.1.20.146', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.146', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.146', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.145', 'root', '""' ],
        'come' : [ '10.1.20.166', 'fun', '123' ]
    },
    'FX1' : {
        'bmc'  : [ '10.1.20.151', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.151', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.151', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.120', 'root', '""' ],
        'come' : [ '10.1.20.21', 'fun', '123' ]
    },
    'FS12' : {
        'bmc'  : [ '10.1.20.39', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.39', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.39', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.157', 'root', '""' ],
        'come' : [ '10.1.20.129', 'fun', '123' ]
    },
    'FS13' : {
        'bmc'  : [ '10.1.20.177', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.177', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.177', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.125', 'root', 'root' ],
        'come' : [ '10.1.21.30', 'fun', '123' ]
    },
    'FS14' : {
        'bmc'  : [ '10.1.20.38', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.38', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.38', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.149', 'root', '""' ],
        'come' : [ '10.1.20.179', 'fun', '123' ]
    },
    'FS15' : {
        'bmc'  : [ '10.1.20.26', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.26', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.26', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.140', 'root', '""' ],
        'come' : [ '10.1.20.170', 'fun', '123' ]
    },
    'FS20' : {
        'bmc'  : [ '10.1.20.132', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.132', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.132', 'admin', 'admin' ],
        'fpga' : [ '10.1.21.28', 'root', '""' ],
        'come' : [ '10.1.20.151', 'fun', '123' ]
    },
    'FS39' : {
        'bmc'  : [ '10.1.21.89', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.21.89', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.21.89', 'admin', 'admin' ],
        'fpga' : [ '10.1.21.90', 'root', 'root' ],
        'come' : [ '10.1.21.91', 'fun', '123' ]
    },
    'FS41' : {
        'bmc'  : [ '10.1.105.52', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.52', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.52', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.69', 'root', '""' ],
        'come' : [ '10.1.105.70', 'fun', '123' ]
    },
    'FS42' : {
        'bmc'  : [ '10.1.105.59', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.59', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.59', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.63', 'root', '""' ],
        'come' : [ '10.1.105.64', 'fun', '123' ]
    },
    'FS43' : {
        'bmc'  : [ '10.1.105.61', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.61', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.61', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.62', 'root', '""' ],
        'come' : [ '10.1.105.65', 'fun', '123' ]
    },
    'FS20' : {
        'bmc'  : [ '10.1.20.132', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.20.132', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.20.132', 'admin', 'admin' ],
        'fpga' : [ '10.1.21.28', 'root', '""' ],
        'come' : [ '10.1.20.151', 'fun', '123' ]
     },
    'FS44' : {
        'bmc'  : [ '10.1.105.66', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.66', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.66', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.70', 'root', '""' ],
        'come' : [ '10.1.105.71', 'fun', '123' ]
    },
    'FS45' : {
        'bmc'  : [ '10.1.105.85', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.85', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.85', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.89', 'root', '""' ],
        'come' : [ '10.1.105.97', 'fun', '123' ]
    },
    'FS48' : {
        'bmc'  : [ '10.1.105.85', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.85', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.85', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.89', 'root', '""' ],
        'come' : [ '10.1.105.97', 'fun', '123' ]
    },
    'FS49' : {
        'bmc'  : [ '10.1.105.86', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.86', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.86', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.65', 'root', '""' ],
        'come' : [ '10.1.105.67', 'fun', '123' ]
    },
    'FS50' : {
        'bmc'  : [ '10.1.105.87', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.87', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.87', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.56', 'root', '""' ],
        'come' : [ '10.1.105.77', 'fun', '123' ]
    },
    'FS51' : {
        'bmc'  : [ '10.1.104.147', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.147', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.147', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.152', 'root', '""' ],
        'come' : [ '10.1.104.154', 'fun', '123' ]
    },
    'FS52' : {
        'bmc'  : [ '10.1.104.153', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.153', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.153', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.155', 'root', '""' ],
        'come' : [ '10.1.104.157', 'fun', '123' ]
    },
    'FS53' : {
        'bmc'  : [ '10.1.104.149', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.149', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.149', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.158', 'root', '""' ],
        'come' : [ '10.1.104.159', 'fun', '123' ]
    },
   'FS54' : {
        'bmc'  : [ '10.1.104.163', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.163', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.163', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.169', 'root', '""' ],
        'come' : [ '10.1.104.170', 'fun', '123' ]
    },
   'FS55' : {
        'bmc'  : [ '10.1.21.28', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.21.28', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.21.28', 'admin', 'admin' ],
        'fpga' : [ '10.1.20.175', 'root', 'root' ],
        'come' : [ '10.1.21.32', 'fun', '123' ]
    },
   'FS56' : {
        'bmc'  : [ '10.1.105.70', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.70', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.70', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.74', 'root', '""' ],
        'come' : [ '10.1.105.73', 'fun', '123' ]
    },
   'FS57' : {
        'bmc'  : [ '10.1.104.173', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.173', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.173', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.174', 'root', '""' ],
        'come' : [ '10.1.104.170', 'fun', '123' ]
    },
   'FS58' : {
        'bmc'  : [ '10.1.104.175', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.175', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.175', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.176', 'root', '""' ],
        'come' : [ '10.1.104.170', 'fun', '123' ]
    },
   'FS59' : {
        'bmc'  : [ '10.1.105.71', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.71', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.71', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.81', 'root', '""' ],
        'come' : [ '10.1.105.89', 'fun', '123' ]
    },
   'FS60' : {
        'bmc'  : [ '10.1.105.52', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.105.52', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.105.52', 'admin', 'admin' ],
        'fpga' : [ '10.1.105.66', 'root', '""' ],
        'come' : [ '10.1.105.171', 'fun', '123' ]
    },
   'FS61' : {
        'bmc'  : [ '10.1.104.113', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.113', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.113', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.141', 'root', '""' ],
        'come' : [ '10.1.104.128', 'fun', '123' ]
    },
   'FS62' : {
        'bmc'  : [ '10.1.104.116', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.116', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.116', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.135', 'root', '""' ],
        'come' : [ '10.1.104.132', 'fun', '123' ]
    },
   'FS63' : {
        'bmc'  : [ '10.1.104.121', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.121', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.121', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.174', 'root', '""' ],
        'come' : [ '10.1.104.133', 'fun', '123' ]
    },
   'FS64' : {
        'bmc'  : [ '10.1.104.127', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.127', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.127', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.129', 'root', 'root' ],
        'come' : [ '10.1.104.128', 'fun', '123' ]
    },
   'FS65' : {
        'bmc'  : [ '10.1.104.164', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.164', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.164', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.155', 'root', 'root' ],
        'come' : [ '10.1.104.166', 'fun', '123' ]
    },
   'FS66' : {
        'bmc'  : [ '10.1.104.165', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.104.165', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.104.165', 'admin', 'admin' ],
        'fpga' : [ '10.1.104.153', 'root', 'root' ],
        'come' : [ '10.1.104.167', 'fun', '123' ]
    },
   'FS63' : {
        'bmc'  : [ '10.1.107.61', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.107.61', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.107.61', 'admin', 'admin' ],
        'fpga' : [ '10.1.107.55', 'root', 'root' ],
        'come' : [ '10.1.104.136', 'fun', '123' ]
    },
   'FS32' : {
        'bmc'  : [ '10.80.4.156', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.80.4.156', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.80.4.156', 'admin', 'admin' ],
        'fpga' : [ '10.80.4.157', 'root', '""' ],
        'come' : [ '10.80.4.158', 'fun', '123' ]
    },
   'FS37' : {
        'bmc'  : [ 'fs37-bmc.fungible.local', 'sysadmin', 'superuser' ],
        'rf'   : [ 'fs37-bmc.fungible.local', 'Administrator', 'superuser' ],
        'ipmi' : [ 'fs37-bmc.fungible.local', 'admin', 'admin' ],
        'fpga' : [ 'fs37-fpga.fungible.local', 'root', '""' ],
        'come' : [ 'fs37-come.fungible.local', 'fun', '123' ]
    },
   'FS104' : {
        'bmc'  : [ '10.1.108.46', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.108.46', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.108.46', 'admin', 'admin' ],
        'fpga' : [ '10.1.108.48', 'root', '""' ],
        'come' : [ '10.1.108.47', 'fun', '123' ]
    },
   'FS110' : {
        'bmc'  : [ '10.90.4.106', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.90.4.106', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.90.4.106', 'admin', 'admin' ],
        'fpga' : [ '10.90.4.108', 'root', '""' ],
        'come' : [ '10.90.4.107', 'fun', '123' ]
   },
   'FS142' : {
        'bmc'  : [ '10.1.22.33', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.22.33', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.22.33', 'admin', 'admin' ],
        'fpga' : [ '10.1.22.35', 'root', '""' ],
        'come' : [ '10.1.22.33', 'fun', '123' ]
   },
   'FS143' : {
        'bmc'  : [ '10.1.22.94', 'sysadmin', 'superuser' ],
        'rf'   : [ '10.1.22.94', 'Administrator', 'superuser' ],
        'ipmi' : [ '10.1.22.94', 'admin', 'admin' ],
        'fpga' : [ '10.1.22.96', 'root', '""' ],
        'come' : [ '10.1.22.95', 'fun', '123' ]
   },
}



#making below dictionaries for fabric # no not change
def _make_passwords(setups):
    for (sk, sv) in setups.iteritems():
        for (k, v) in sv.iteritems():
            setups[sk][k].append(v[1] + '@' + v[0] + ':22') # makeing user@host
            yield (v[1]+'@'+v[0]+':22', v[2])

env.passwords.update(_make_passwords(setups))
env.setdefault('setups', dict()).update(setups)

#import pprint
#pprint.pprint(env)
