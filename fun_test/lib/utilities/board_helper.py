from   pexpect import pxssh
import pexpect
import dlipower
import time, os
import json, commentjson
import re

class board_helper:
    def __init__(self, target_machine):
        self.target_machine = target_machine
        test_board_asset = self.find_asset(target_machine)
        if(test_board_asset["apc_info"] is None):
            print("No apc_info for : " + str(target_machine))
            return(None)
        D = test_board_asset["apc_info"]
        self.H = D["host_ip"]
        self.N = D["outlet_number"];
        self.P = D["password"]
        print(" POWER Host ("+ self.H + ") outlet (" + str(self.N) + ")")
        print(" BMC IP is " + test_board_asset["bmc"]["mgmt_ip"])
        D = test_board_asset["bmc"]
        self.BMC  = D["mgmt_ip"]
        self.BMCU = D["mgmt_ssh_username"]
        self.BMCP = D["mgmt_ssh_password"]
        self.FBUS = { 0 : "3", 1 : "5" }
        self.switch = None
    def _switch_login( self ):
        if( self.switch is None ): 
            try:
                self.switch =  dlipower.PowerSwitch( hostname=self.H, userid="admin", password=self.P )
            except:
                print("CRITICAL: There was an error in getting the PowerSwitch\n")
                return(None)
    def find_asset( self, board_name ):
        base_path = os.environ["PYTHONPATH"]
        json_file = base_path + "/asset/fs.json"
        result = None
        with open(json_file, "r") as JF:
            json_spec = commentjson.load(JF)
        for fs in json_spec:
            if fs["name"] == board_name:
                result = fs
                break
        return result
    def power_on( self, target_port ):
        if( target_port is None ) : target_port = self.N
        print("power ON  machine : " + self.target_machine + " port " + str(target_port))
        self._switch_login()
        self.switch.on( target_port )
    def power_off( self, target_port ):
        if( target_port is None ) : target_port = self.N
        print("power OFF machine : " + self.target_machine + " port " + str(target_port))
        self._switch_login()
        self.switch.off( target_port )
    def bmc_test ( self, fnum = 0 ):
        bus = self.FBUS.get(fnum, "3" )
        s = pxssh.pxssh()
        try:
            s.login(self.BMC, self.BMCU, self.BMCP)
            print("BMC test : MIO scratchpad register : write data 0xf then read")
            s.sendline("i2c-test -b " + bus + " -s 0x70 -m 1 -rc 1 -d 0x01 0xb8 0x00 0x00 0x00 0x78 0 0 0 0 0 0 0 0xF")
            s.prompt();
            print(s.before)
            s.sendline("i2c-test -b " + bus + " -s 0x70 -m 1 -rc 9 -d 0x00 0xb8 0x00 0x00 0x00 0x78")
            s.prompt()
            print(s.before)
            s.logout()
        except pxssh.ExceptionPxssh as e:
            print("CRITICAL: There was a problem logging into the BMC : (" + self.BMC + ") " + self.BMCU )
            print(e)
    ## faults --------------------------------------------------------
    def power_cycle( self, target_port ):
        if( target_port is None ) : target_port = self.N
        self._switch_login()
        status = self.switch.status(target_port)
        print("power cycling machine : " + self.target_machine + " port " + str(target_port))
        if( status == "OFF" ) :
            print " --- leaving port " + str(target_port) + " status = " + status    
        else :
            self.switch.off(target_port)
            print "port " + str(target_port) + " is OFF, sleeping for 5 seconds\n"
            time.sleep(5)
            self.switch.on (target_port)
            self.switch.printstatus()

    def fault_fatal_error ( self, fnum = 0 ): # cause a fatal error in F1
        # mio_fatal_intr_mask                   :0xB000000028
        # mio_fatal_intr_bset                   :0xB000000030
        # mio_fatal_intr_bclr                   :0xB000000038
        bus = self.FBUS.get(fnum, "3" )
        s = pxssh.pxssh()
        try:
            s.login(self.BMC, self.BMCU, self.BMCP)
            s.sendline("i2c-test -b " + bus + " -s 0x70 -m 1 -rc 1 -d 0x01 0xB0 0x00 0x00 0x00 0x28 0 0 0 0 0 0 0 0x1"); # mask
            s.prompt()
            s.sendline("i2c-test -b " + bus + " -s 0x70 -m 1 -rc 1 -d 0x01 0xB0 0x00 0x00 0x00 0x28 0 0 0 0 0 0 0 0x1"); # bset = fatal emmc error
            s.prompt()
            s.logout()
        except pxssh.ExceptionPxssh as e:
            print("CRITICAL: There was a problem logging into the BMC : (" + self.BMC + ") " + self.BMCU )
            print(e)
            return( None )

    def fault_stop_heartbeat( self, fnum = 0):
        # `define F1_SUBSYSTEM_CPC_REG_BLOCK_PUT_1_1_RESET_N_LSB   33
        # `define F1_SUBSYSTEM_CPC_REG_BLOCK_CUT_2_2_RESET_N_LSB   37
        # f1_subsystem_cpc_reg                  :0xB0 00 00 00 88
        bus = self.FBUS.get(fnum, "3" )
        s = pxssh.pxssh()
        try:
            s.login(self.BMC, self.BMCU, self.BMCP)
            v = 0;            
            s.sendline("i2c-test -b " + bus + " -s 0x70 -m 1 -rc 9 -d 0x00 0xB0 00 00 00 88"); # f1_subsystem (read)
            s.prompt()
            m = re.search("Bytes read:\s+9\s*\n80 (\w+) (\w+) (\w+) (\w+) (\w+) (\w+) (\w+) (\w+)", s.before)
            if (m):
                v = 0
                for i in range(1, 8+1):
                    v = v << 8 | int(m.group(i), 16)
                pc1 = 1 << 33 # PUT 1 reset
                v = v & ~pc1
                data = "";
                for i in range(8): 
                    data = " " + hex(v & 0xff) + data
                    v >>= 8
                print( " putting PUT1 into reset new subsystem_cpc_reg CSR value : " + data)
                s.sendline("i2c-test -b " + bus + " -s 0x70 -m 1 -rc 1 -d 0x01 0xB0 0x00 0x00 0x00 0x88 " + data ); # f1_subsystem (write)
            else: print(" --- CRITICAL : cannot find I2C read data for subsystem_cpc_reg CSR read" + s.before);
            s.logout()
        except pxssh.ExceptionPxssh as e:
            print("CRITICAL: There was a problem logging into the BMC : (" + self.BMC + ") " + self.BMCU )
            print(e)
