from __future__ import print_function
import socket
import subprocess
import re
import sys
import os
import select
import platform

TRUE = 1 
FALSE = 0
tclserversocket=''
socket_buffer = 1024
pythonver=0
WrapperVersion = '1.0.0918'

def autoload_func(hltapi_func_name,**arg):
   cmdline = hlt_params_conv(**arg)
   ret = private_invoke("set ret [ixia::"+hltapi_func_name+" " + cmdline + "]")
   return hlt_result_conv()

class AutoLoad(object):
    def __init__(self, mod_name):
        super(AutoLoad, self).__init__()
        self.wrapped_name = mod_name
        self.wrapped = sys.modules[mod_name]
    def __getattr__(self, name):
        try:
            return getattr(self.wrapped, name)
        except AttributeError:
            def f(**arg):
                funcRet=autoload_func(name,**arg)
                return funcRet
            return f

def hlpyapi_env():
    global pythonver
	#To get python version
    if (sys.version.split(' ')[0]).split('.')[0]=='3':
	    pythonver=3
    print('Current OS: '+platform.system()+','+platform.release()+','+platform.version()+';'+' python version: ' + sys.version.split(' ')[0])
	
    # spawn and connect to a server running on the local host
    # for a remote server, this will have to be changed somewhat
    # todo: implement a connection to a remote server
    global tclserversocket
    HOST = 'localhost'
    PORT = 0
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((HOST, PORT))
    srv.listen(1)
    HOST,PORT = srv.getsockname()
    portstr = '%d' %PORT
    if 'STC_TCL' in os.environ:
        tcl_path = os.environ['STC_TCL']
    else :
        print('HLPy Error: need set system environ variable STC_TCL firstly\n')
        sys.exit()
    if 'HLPYAPI_LOG' in os.environ:
        log_dir = os.environ['HLPYAPI_LOG']
    else :
        log_dir = os.getcwd()
    logname = "hlpyapi.hltlog"
    try:
        if sys.argv[0]:
            logname = os.path.basename(sys.argv[0])
            logname = logname.split('.py')[0]
            logname = logname + '.hltlog'
    except:
        logname = "hlpyapi.hltlog"
    basedir = os.path.dirname(os.path.realpath(__file__))
    filedir = os.path.join(basedir, "hltapiserver.srv")
    stcserver = tcl_path +" "+filedir+ " "+portstr+" 120 log "+ log_dir +" "+ logname +" INFO"
    subprocess.Popen(stcserver.split())

    connection, address = srv.accept()
    
    newport = connection.recv(socket_buffer)
    if pythonver == 3:
        newport = newport.decode("utf-8")
    match = re.search('[0-9]*',newport)
    newport = match.group(0)
    import locale
    newport = locale.atoi(newport)
    print("Connecting Tcl server via port", newport)
    tclserversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tclserversocket.connect((HOST, newport))

    #To set tcllibpath
    srcdir = "/".join(str(basedir).split('\\'))+"/SourceCode"
    if os.path.exists(srcdir):
        print("Setting HltApi TCLLIBPATH...")
        srcdir="set auto_path [linsert $auto_path 0 " +srcdir+"] \n"
        tclserversocket.send(srcdir)
        tclserversocket.recv(socket_buffer)
    


    print("Loading SpirentHltApiWrapper...")
    if pythonver == 3:
        tclserversocket.send(bytes("package require SpirentHltApiWrapper\n", 'UTF-8'))
    else:
        tclserversocket.send("package require SpirentHltApiWrapper\n")
    if pythonver == 3:
        result = (tclserversocket.recv(socket_buffer)).decode("utf-8")
    else:
        result = tclserversocket.recv(socket_buffer)
    print("Loaded SpirentHltApiWrapper:",result)
    if pythonver == 3:
        tclserversocket.send(bytes("package require SpirentHltApi\n", 'UTF-8'))
    else:
        tclserversocket.send("package require SpirentHltApi\n")
    if pythonver == 3:
        result = (tclserversocket.recv(socket_buffer)).decode("utf-8")
    else:
        result = tclserversocket.recv(socket_buffer)
    print("Loaded SpirentHltApi:",result)
    print("Python Wrapper version:",WrapperVersion)
    return TRUE;

def invoke(cmd):
    print ("Native call : " + cmd)
    ret = private_invoke(cmd)
    return ret;

    
def private_invoke(cmd):
    global tclserversocket
    if pythonver == 3:
        tclserversocket.send(bytes(cmd+'\n','UTF-8'))
    else:
        tclserversocket.send(cmd+'\n')
    ret = ''
    flag = 1
    socket_list = [tclserversocket]
    read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])

    while flag:
        for sock in read_sockets:
            if sock == tclserversocket:
                if pythonver == 3:
                    data = (tclserversocket.recv(socket_buffer)).decode("utf-8")
                else:
                    data = tclserversocket.recv(socket_buffer)
                ret += data
                if len(data) < socket_buffer :
                    flag = 0
                elif ('\r' == data[len(data) -2]) :
                    if('\n' == data[len(data) -1]):
                        flag = 0
    #removal of whitespaces at end of line
    ret = re.sub(r'\s+$', '', ret)
    #check ret: STCSERVER_RET_SUCCESS:/STCSERVER_RET_ERROR:/invalid rest
    ret = ret.replace('STCSERVER_RET_SUCCESS:','',1)
    if ret.find('STCSERVER_RET_ERROR') >= 0 :
        print('HLPy',cmd,'\nError:',ret)
        sys.exit()

    return ret;

def hlt_params_conv(**arg):
    ret = ''
    for key in list(arg.keys()):
        if type(arg[key]) is int:
            arg[key]= str(arg[key])
        elif type(arg[key]) is list:
            tcllist = '"'
            for element in arg[key]:
                tcllist = tcllist + ' ' +element
            tcllist += '"'
            tcllist = tcllist.replace('" ','"')
            arg[key]= tcllist
        elif type(arg[key]) is str:
            if arg[key].find(' ') >= 0:
                arg[key]= '"' + arg[key] + '"'
        else:
            print("HLPY: hlpyapi only accept int,list and string as parameters. ",key,type(arg[key]))
        keybak = key
        keybak = keybak.replace('python_','')
        ret = ret+ ' -' + keybak + ' ' + arg[key]
    return ret;


def init_dict_recursive(keysList, value) :
    dict_key = {}
    keyarray = keysList.split('.')
    mylen = len(keyarray)
    if mylen > 0 and keyarray[0] != '' :
        key = keyarray[0]
        newList = keysList.replace(key, '',1)
        newList = newList.lstrip('.')
        dict_key[key] = init_dict_recursive(newList, value)
        return dict_key
    else :
        return value
    
def merge_dict_recursive(a, b):
    '''recursively merges dict's. not just simple a['key'] = b['key'], if
    both a and bhave a key who's value is a dict then dict_merge is called
    on both values and the result stored in the returned dictionary.'''
    if not isinstance(b, dict):
        return b
    result = dict(a)
    if pythonver == 3:
        for k, v in b.items():
            if k in result and isinstance(result[k], dict):
                result[k] = merge_dict_recursive(result[k], v)
            else:
                result[k] = v
    else:
        for k, v in b.iteritems():
            if k in result and isinstance(result[k], dict):
                result[k] = merge_dict_recursive(result[k], v)
            else:
                result[k] = v
    return result

def hlt_result_conv():
    mydict = {}
    #catch the make sure error also can pass this function
    try:
        private_invoke("set hashkey \"\"; set hashvalue \"\"; set nested_hashkey \"\"")
        private_invoke("ret_hash ret hashkey hashvalue nested_hashkey")
        
        keys = private_invoke("set hashkey")
        values = private_invoke("set hashvalue")
        
        keysbackup = keys
        valuesbackup = values
        
        #delete '\r\n'
        keys = keys.replace('\r\n','')
        values = values.replace('\r\n','')
        values = values.replace('{{}}','{}')
        keys = keys.replace(' . ','.')
        keys = keys.replace('{','')
        keys = keys.replace('}','')
        valuesList = list(values)
        values = []
        listflag = 0
        valuetemp = ''
        for char in valuesList:
            if char == '{':
                listflag = 1
            elif char == '}':
                listflag = 0
                #output list
                values.append(valuetemp)
                valuetemp = ''
            elif char == ' ':
                if listflag == 0:
                    #output single value
                    if valuetemp != '':
                        values.append(valuetemp)
                    valuetemp = ''
                else:
                    #buffer value
                    valuetemp+= char
            else :
                #buffer value
                valuetemp+= char
        if valuetemp != '':
            values.append(valuetemp)

        keysList = keys.split()
        for i in range(0,len(keysList)):
            subdict = init_dict_recursive(keysList[i], values[i])
            mydict = merge_dict_recursive(mydict, subdict)
    except:
        print("HLPY: error happened when converting keys-values:",keysbackup,valuesbackup)
    return mydict

#used be emulation_lldp_optional_tlv_config and emulation_lldp_dcbx_tlv_config
def hlt_result_conv_special(ret):
    returnval = {}
    returnval['status'] = '1'
    ret = ret.replace('\r\n','')
    ret = ret.replace('{handle {','')
    ret = ret.replace('}} {status 1}','')
    ret = ret.replace('{','\{')
    ret = ret.replace('}','\}')
    returnval['handle'] = ret
    return returnval
    
def connect(**arg):
    #print "HLPY: connect:",  
    cmdline = hlt_params_conv(**arg)
    #print cmdline
    #execute the HLT command
    ret = private_invoke("ixia::connect"+cmdline)
    #convert the HLT return value keyed list into Dict and return
    #connect need special handle
    #{offline 0} {port_handle {{10 {{61 {{44 {{2 {{6/8 port1}}}}}}}}}}} {status 1}
    ret = ret.replace('{','')
    ret = ret.replace('}','')
    ret = ret.split()
    retnew = {}
    index = 0
    for element in ret:
        index += 1
        if element == 'offline':
            retnew['offline'] = ret[index]
            index1 = index + 1
        if element == 'status':
            retnew['status'] = ret[index]
        if element == 'connection_handle':
            retnew['connection_handle'] = ret[index]
            index2 = index - 1
        if element == 'port_handles':
            retnew['port_handles'] = ret[index]
    port_handle = ret[index1]
    chassis = ret[index1+1]+'.'+ret[index1+2]+'.'+ret[index1+3]+'.'+ret[index1+4]
    chassis_port = {}
    ports = {}
    index = index1+5
    while index < index2:
        ports[ret[index]] = ret[index + 1]
        index+= 2
    chassis_port[chassis] = ports
    retnew[port_handle] = chassis_port
    return retnew

#####sth.device_info#####
def device_info(**arg):
    #print "HLPY: device_info:",
    cmdline = hlt_params_conv(**arg)
    #print cmdline
    #execute the HLT command
    ret = private_invoke("ixia::device_info"+cmdline)
    #convert the HLT return value keyed list into hash and return
    #this is not same as other functions
    ret = ret.replace('{','')
    ret = ret.replace('}','')
    ret = ret.split()
    newret = {}
    newret[ret[0]] = ret[1]
    chassis = ret[2]+'.'+ret[3]+'.'+ret[4]+'.'+ret[5]
    chassisdict = {}
    availabledcit = {}
    inusedict = {}
    if ret.count('available') != 0:
        availableindex = ret.index('available')
        if ret.count('inuse') != 0:
            inusedindex = ret.index('inuse')
            i = availableindex+1
            while i < inusedindex :
                availabledcit[ret[i]] = {ret[i+1]:ret[i+2]}
                i += 3
    if ret.count('inuse') != 0:
        inusedindex = ret.index('inuse')
        if ret.count('port_handle') != 0:
            port_handleindex = ret.index('port_handle')
            i = inusedindex+1
            while i < port_handleindex :
                inusedict[ret[i]] = {ret[i+1]:ret[i+2],ret[i+3]:ret[i+4]}
                i += 5
    newret[chassis] = {'available':availabledcit,'inuse':inusedict}
    if ret.count('status') != 0:
        statusindex = ret.index('status')
        newret['status'] = ret[statusindex+1]
    return newret

#################################generate by tool################
#####sth.emulation_gre_config#####

def emulation_gre_config(**arg):

    #print "HLPY: emulation_gre_config:",

    cmdline = hlt_params_conv(**arg)

    #print cmdline

    #execute the HLT command

    ret = private_invoke("set ret [sth::emulation_gre_config" + cmdline + "]")

    #convert the HLT return value keyed list into hash and return

    ret = ret.replace('\r\n','')

    return ret


#####sth.emulation_lldp_dcbx_tlv_config#####

def emulation_lldp_dcbx_tlv_config(**arg):

    #print "HLPY: emulation_lldp_dcbx_tlv_config:",

    cmdline = hlt_params_conv(**arg)

    #print cmdline

    #execute the HLT command

    ret = private_invoke("set ret [sth::emulation_lldp_dcbx_tlv_config" + cmdline + "]")

    #convert the HLT return value keyed list into hash and return

    return hlt_result_conv_special(ret)


#####sth.emulation_lldp_optional_tlv_config#####

def emulation_lldp_optional_tlv_config(**arg):

    #print "HLPY: emulation_lldp_optional_tlv_config:",

    cmdline = hlt_params_conv(**arg)

    #print cmdline

    #execute the HLT command

    ret = private_invoke("set ret [sth::emulation_lldp_optional_tlv_config" + cmdline + "]")

    #convert the HLT return value keyed list into hash and return

    return hlt_result_conv_special(ret)

#################################################
#############close the socket manually###########
#####sth.close#####
def close(**arg):
    global tclserversocket
    tclserversocket.close()
    tclserversocket=''

#as default, hlpyapi_env need be called as initial
try:
    hlpyapi_env()
    sys.modules[__name__] = AutoLoad(__name__)
except:
    print("HLPY: error happened when connecting hltapiserver and loading hltapi.")
