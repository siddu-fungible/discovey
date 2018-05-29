from cmd import Cmd
from prettytable import PrettyTable
from datetime import datetime
import os
import sys
import re
import time
import json


sdkdir = "/bin/" + os.uname()[0]
if ("SDKDIR" in os.environ):
    sys.path.append(os.environ["SDKDIR"] + sdkdir)
elif ("WORKSPACE" in os.environ):
    sys.path.append(os.environ["WORKSPACE"] + "/FunSDK/" + sdkdir)
else:
    raise RuntimeError("Please specify WORKSPACE or SDKDIR environment variable")

import dpc_client


class DpcshInteractive(Cmd):
    STATS_TYPE_FPG = "fpg"
    STATS_TYPE_PSW = "psw"
    STATS_TYPE_VP = "vp"
    STATS_TYPE_FCP = "fcp"
    STATS_TYPE_WRO = "wro"
    STATS_TYPE_WRED_ECN = "wred_ecn"
    VERB_PEEK = "peek"
    VERB_QOS = "qos"
    VERB_PORT = "port"
    TIME_INTERVAL = 2

    def __init__(self, target_ip, target_port, verbose=False):
        Cmd.__init__(self)
        self.prompt = "(dpcsh) "

        # Connect to DPC tcp_proxy server
        self.target_ip = target_ip
        self.target_port = target_port
        print "Connecting to DPC server..."
        self.dpc_client = dpc_client.DpcClient(unix_sock=False, server_address=(target_ip, target_port))
        self.dpc_client.__verbose = verbose
        self.sock = self.dpc_client._DpcClient__sock

        # Ensure DPC tcp_proxy is connected
        result = self.dpc_client.execute(verb="echo", arg_list=["hello"])
        result = "hello"
        if result != 'hello':
            print 'Connection to DPC server via tcp_proxy at %s:%s failed. ' % (
                self.target_ip, self.target_port)
            sys.exit(1)
        else:
            print 'Connected to DPC server via tcp_proxy at %s:%s.' % (
                self.target_ip, self.target_port)

    def do_set_time_interval(self, value):
        """ Time in secs to wait before fetching stats iteratively. set_time_interval <value>"""
        self.TIME_INTERVAL = int(value)

    def do_peek_fpg_stats(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Port Num required. See peek_fpg_stats help\n")
            port_num = arg_list[0]
            grep_regex = None
            if len(arg_list) > 1:
                grep_regex = arg_list[1]

            cmd = "stats/fpg/port/[%d]" % int(port_num)

            result = self.dpc_client.execute(verb=self.VERB_PEEK, arg_list=[cmd])
            result = test
            if result:
                self.display_stats(result=result, stats_type=self.STATS_TYPE_FPG, grep_regex=grep_regex)
                self._peek_stats_iteratively(cmd=cmd, prev_result=result, stats_type=self.STATS_TYPE_FPG,
                                             grep_regex=grep_regex)
            else:
                print "Results are empty"
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_peek_fpg_stats()

    def _display_fpg_stats(self, result, diff_result, grep_regex):
        if diff_result:
            tx_table_obj = PrettyTable(["Name", "Actual Stats", "Diff Stats"])
            tx_table_obj.align = "l"
            rx_table_obj = PrettyTable(["Name", "Actual Stats", "Diff Stats"])
            rx_table_obj.align = "l"
            if grep_regex:
                for key in result[0].keys():
                    if re.search(grep_regex, key, re.IGNORECASE):
                        if re.search(r".*tx.*", key, re.IGNORECASE):
                            tx_table_obj.add_row([key, result[0][key], diff_result[key]])
                        else:
                            rx_table_obj.add_row([key, result[0][key], diff_result[key]])
            else:
                for key in result[0].keys():
                    if re.search(r".*tx.*", key, re.IGNORECASE):
                        tx_table_obj.add_row([key, result[0][key], diff_result[key]])
                    else:
                        rx_table_obj.add_row([key, result[0][key], diff_result[key]])
            if tx_table_obj.rowcount > 0:
                print "\n######## TX FPG Port Stats ########\n"
                print tx_table_obj
            if rx_table_obj.rowcount > 0:
                print "\n######## RX FPG Port Stats ########\n"
                print rx_table_obj
        else:
            tx_table_obj = PrettyTable(["Name", "Count"])
            tx_table_obj.align = "l"
            rx_table_obj = PrettyTable(["Name", "Count"])
            rx_table_obj.align = "l"
            if grep_regex:
                for key in result[0].keys():
                    if re.search(grep_regex, key, re.IGNORECASE):
                        if re.search(r".*tx.*", key, re.IGNORECASE):
                            tx_table_obj.add_row([key, result[0][key]])
                        else:
                            rx_table_obj.add_row([key, result[0][key]])
            else:
                for key in result[0].keys():
                    if re.search(r".*tx.*", key, re.IGNORECASE):
                        tx_table_obj.add_row([key, result[0][key]])
                    else:
                        rx_table_obj.add_row([key, result[0][key]])
            if tx_table_obj.rowcount > 0:
                print "\n######## TX FPG Port Stats ########\n"
                print tx_table_obj
            if rx_table_obj.rowcount > 0:
                print "\n######## RX FPG Port Stats ########\n"
                print rx_table_obj

    def _display_psw_stats(self, result, diff_result, global_result, grep_regex):
        if global_result:
            if diff_result:
                if grep_regex:
                    for key in result.keys():
                        table_obj = PrettyTable(["Name", "Actual Count", "Diff Count"])
                        table_obj.align = "l"
                        table_obj.sortby = "Name"
                        for inner_key in result[key].keys():
                            if re.search(grep_regex, inner_key, re.IGNORECASE):
                                table_obj.add_row([inner_key, result[key][inner_key], diff_result[key][inner_key]])
                        if table_obj.rowcount > 0:
                            print "\n######## PSW Global Stats (%s) ########\n" % key
                            print table_obj
                else:
                    for key in result.keys():
                        table_obj = PrettyTable(["Name", "Actual Count", "Diff Count"])
                        table_obj.align = "l"
                        table_obj.sortby = "Name"
                        for inner_key in result[key].keys():
                            table_obj.add_row([inner_key, result[key][inner_key], diff_result[key][inner_key]])
                        if table_obj.rowcount > 0:
                            print "\n######## PSW Global Stats (%s) ########\n" % key
                            print table_obj
            else:
                if grep_regex:
                    for key in result.keys():
                        table_obj = PrettyTable(["Name", "Actual Count"])
                        table_obj.align = "l"
                        table_obj.sortby = "Name"
                        for inner_key in result[key].keys():
                            if re.search(grep_regex, inner_key, re.IGNORECASE):
                                table_obj.add_row([inner_key, result[key][inner_key]])
                        if table_obj.rowcount > 0:
                            print "\n######## PSW Global Stats (%s) ########\n" % key
                            print table_obj
                else:
                    for key in result.keys():
                        table_obj = PrettyTable(["Name", "Actual Count"])
                        table_obj.align = "l"
                        table_obj.sortby = "Name"
                        for inner_key in result[key].keys():
                            table_obj.add_row([inner_key, result[key][inner_key]])
                        if table_obj.rowcount > 0:
                            print "\n######## PSW Global Stats (%s) ########\n" % key
                            print table_obj
        else:
            if diff_result:
                queue_table_obj = PrettyTable(["Queue", "Bytes", "Bytes Diff", "Packets", "Packets Diff"])
                drop_table_obj = PrettyTable(["Drop Type", "No of drops", "Drops diff"])
                queue_table_obj.align = "l"
                drop_table_obj.align = "l"
                for key in result["count"].keys():
                    queue_table_obj.add_row([key, result["count"][key]["bytes"], diff_result["queue"][key]["bytes"],
                                             result["count"][key]["pkts"], diff_result["queue"][key]["pkts"]])

                for key in result["drops"].keys():
                    drop_table_obj.add_row([key, result["drops"][key], diff_result["drops"][key]])
            else:
                queue_table_obj = PrettyTable(["Queue", "Bytes", "Packets"])
                drop_table_obj = PrettyTable(["Drop Type", "No of drops"])
                queue_table_obj.align = "l"
                drop_table_obj.align = "l"
                for key in result["count"].keys():
                    queue_table_obj.add_row([key, result["count"][key]["bytes"], result["count"][key]["pkts"]])

                for key in result["drops"].keys():
                    drop_table_obj.add_row([key, result["drops"][key]])

            print "\n ######## Queue PSW Stats ########\n"
            print queue_table_obj
            print "\n ######## Drops PSW Stats ########\n"
            print drop_table_obj

    def _display_vp_stats(self, result, diff_result, grep_regex):
        if diff_result:
            table_obj = PrettyTable(["Name", "Actual Count", "Diff Count"])
            table_obj.align = "l"
            table_obj.sortby = "Name"
            if grep_regex:
                for key in result.keys():
                    if re.search(grep_regex, key, re.IGNORECASE):
                        table_obj.add_row([key, result[key], diff_result[key]])
            else:
                for key in result.keys():
                    table_obj.add_row([key, result[key], diff_result[key]])
        else:
            table_obj = PrettyTable(["Name", "Actual Count"])
            table_obj.align = "l"
            table_obj.sortby = "Name"
            if grep_regex:
                for key in result.keys():
                    if re.search(grep_regex, key, re.IGNORECASE):
                        table_obj.add_row([key, result[key]])
            else:
                for key in result.keys():
                    table_obj.add_row([key, result[key]])

        if table_obj.rowcount > 0:
            print "\n ######## VP Stats ########\n"
            print table_obj

    def _display_fcp_stats(self, result, diff_result, grep_regex, is_global):
        if is_global:
            pass
        else:
            if diff_result:
                table_obj = PrettyTable(["Name", "Actual Count", "Diff Count"])
                table_obj.align = "l"
                table_obj.sortby = "Name"
                if grep_regex:
                    for key in result.keys():
                        if re.search(grep_regex, key, re.IGNORECASE):
                            table_obj.add_row([key, result[key], diff_result[key]])
                else:
                    for key in result.keys():
                        table_obj.add_row([key, result[key], diff_result[key]])
            else:
                table_obj = PrettyTable(["Name", "Actual Count"])
                table_obj.align = "l"
                table_obj.sortby = "Name"
                if grep_regex:
                    for key in result.keys():
                        if re.search(grep_regex, key, re.IGNORECASE):
                            table_obj.add_row([key, result[key]])
                else:
                    for key in result.keys():
                        table_obj.add_row([key, result[key]])
            if table_obj.rowcount > 0:
                print "\n ######## FCP Tunnel Stats ########\n"
                print table_obj

    def display_stats(self, result, stats_type, diff_result=None, global_result=None, grep_regex=None):
        if stats_type == self.STATS_TYPE_FPG:
            self._display_fpg_stats(result=result, diff_result=diff_result, grep_regex=grep_regex)
        elif stats_type == self.STATS_TYPE_PSW:
            self._display_psw_stats(result=result, diff_result=diff_result, global_result=global_result,
                                    grep_regex=grep_regex)
        elif stats_type == self.STATS_TYPE_VP:
            self._display_vp_stats(result=result, diff_result=diff_result, grep_regex=grep_regex)
        elif stats_type == self.STATS_TYPE_FCP:
            self._display_fcp_stats(result=result, diff_result=diff_result, is_global=global_result,
                                    grep_regex=grep_regex)
        elif stats_type == self.STATS_TYPE_WRO:
            pass

    def _peek_stats_iteratively(self, cmd, prev_result, stats_type, grep_regex=None, is_global=False, verb=VERB_PEEK):
        try:
            while True:
                try:
                    ts = time.time()
                    st = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                    print "\n -----------> Wait time %d.  [%s]<----------- \n" % (self.TIME_INTERVAL, st)
                    time.sleep(self.TIME_INTERVAL)

                    if type(cmd) == list:
                        result = self.dpc_client.execute(verb=verb, arg_list=cmd)
                    else:
                        result = self.dpc_client.execute(verb=verb, arg_list=[cmd])

                    if verb == self.VERB_PEEK:
                        diff_result = self._get_differential_stats(new_stats=result, prev_stats=prev_result,
                                                                   stats_type=stats_type, is_global=is_global)
                        self.display_stats(result=result, diff_result=diff_result, stats_type=stats_type,
                                           grep_regex=grep_regex, global_result=is_global)
                    elif verb == self.VERB_QOS:
                        diff_result = self._get_qos_stats_diff(new_stats=result, prev_stats=prev_result)
                        self.display_qos_stats(result=result, diff_result=diff_result, grep_regex=grep_regex)
                    prev_result = result
                except KeyboardInterrupt:
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            sys.exit(1)

    def _get_differential_stats(self, stats_type, new_stats, prev_stats, is_global=False):
        diff_stats = {}
        if stats_type == self.STATS_TYPE_FPG or stats_type == self.STATS_TYPE_VP:
            if type(new_stats) == list and type(prev_stats) == list:
                new_stats = new_stats[0]
                prev_stats = prev_stats[0]
            for key in new_stats.keys():
                if key in prev_stats:
                    value = new_stats[key] - prev_stats[key]
                    diff_stats[key] = value
                else:
                    diff_stats[key] = 0
        elif stats_type == self.STATS_TYPE_PSW:
            if is_global:
                for key in new_stats.keys():
                    diff_stats[key] = {}
                    for inner_key in new_stats[key].keys():
                        if key in prev_stats:
                            if inner_key in prev_stats[key]:
                                value = new_stats[key][inner_key] - prev_stats[key][inner_key]
                                diff_stats[key][inner_key] = value
                            else:
                                diff_stats[key][inner_key] = 0
            else:
                queue_diff_stats = {}
                drop_diff_stats = {}
                for key in new_stats['count'].keys():
                    if key in prev_stats["count"]:
                        bytes_diff = new_stats["count"][key]["bytes"] - prev_stats["count"][key]["bytes"]
                        packets_diff = new_stats["count"][key]["pkts"] - prev_stats["count"][key]["pkts"]
                        queue_diff_stats[key] = {"bytes": bytes_diff, "pkts": packets_diff}
                    else:
                        queue_diff_stats[key] = {"bytes": 0, "pkts": 0}

                for key in new_stats['drops'].keys():
                    if key in prev_stats["drops"]:
                        drop_diff = new_stats["drops"][key] - prev_stats["drops"][key]
                        drop_diff_stats[key] = drop_diff
                    else:
                        drop_diff_stats[key] = 0
                diff_stats["queue"] = queue_diff_stats
                diff_stats['drops'] = drop_diff_stats
        elif stats_type == self.STATS_TYPE_FCP:
            if is_global:
                pass
            else:
                for key in new_stats.keys():
                    if key in prev_stats:
                        value = new_stats[key] - prev_stats[key]
                        diff_stats[key] = value
                    else:
                        diff_stats[key] = 0

        return diff_stats

    def display_qos_stats(self, result, diff_result=None, grep_regex=None):
        if diff_result:
            table_obj = PrettyTable(["Name", "Value", "Diff"])
            for key in result:
                if grep_regex:
                    if re.search(grep_regex, key, re.IGNORECASE):
                        table_obj.add_row([key, result[key], diff_result[key]])
                else:
                    table_obj.add_row([key, result[key], diff_result[key]])

        else:
            table_obj = PrettyTable(["Name", "Value"])
            for key in result:
                if grep_regex:
                    if re.search(grep_regex, key, re.IGNORECASE):
                        table_obj.add_row([key, result[key]])
                else:
                    table_obj.add_row([key, result[key]])
        print table_obj

    def _get_qos_stats_diff(self, new_stats, prev_stats):
        diff_stats = {}
        for key in new_stats:
            if key in prev_stats:
                value = new_stats[key] - prev_stats[key]
                diff_stats[key] = value
            else:
                diff_stats[key] = 0
        return diff_stats


    def do_exit(self, arg):
        """ Close connection and exit from application"""
        print "Closing connection and exiting...."
        self.sock.close()
        sys.exit(0)

    def do_peek_psw_stats(self, args):
        try:
            arg_list = args.split()
            grep_regex = None
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            if "global" in arg_list:
                cmd = "stats/psw/global"
                if len(arg_list) > 1:
                    grep_regex = arg_list[1]
            else:
                if len(arg_list) > 1:
                    port_num = arg_list[0]
                    queue_id = arg_list[1]
                    cmd = "stats/psw/port/[%d]/%s" % (int(port_num), queue_id)
                else:
                    if len(arg_list) == 1:
                        port_num = arg_list[0]
                        cmd = "stats/psw/port/[%d]" % int(port_num)
                    else:
                        raise RuntimeError("Insufficient arguments. See below help")

            result = self.dpc_client.execute(verb=self.VERB_PEEK, arg_list=[cmd])
            is_global = False
            if "global" in cmd:
                is_global = True

            self.display_stats(result=result, stats_type=self.STATS_TYPE_PSW, global_result=is_global,
                               grep_regex=grep_regex)
            self._peek_stats_iteratively(cmd=cmd, prev_result=result, stats_type=self.STATS_TYPE_PSW,
                                         is_global=is_global, grep_regex=grep_regex)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_peek_psw_stats()

    def do_peek_vp_stats(self, grep_regex):
        try:
            cmd = "stats/vppkts"
            result = self.dpc_client.execute(verb=self.VERB_PEEK, arg_list=[cmd])
            self.display_stats(result=result, stats_type=self.STATS_TYPE_VP, grep_regex=grep_regex)
            self._peek_stats_iteratively(cmd=cmd, stats_type=self.STATS_TYPE_VP, grep_regex=grep_regex,
                                         prev_result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_peek_vp_stats()

    def do_peek_fcp_stats(self, args):
        try:
            arg_list = args.split()
            grep_regex = None
            is_global = False
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            if "global" in arg_list:
                is_global = True
                cmd = "stats/fcp/global"
                if len(arg_list) > 1:
                    grep_regex = arg_list[0]
            else:
                if len(arg_list) > 1:
                    tunnel_id = arg_list[0]
                    grep_regex = arg_list[1]
                else:
                    tunnel_id = arg_list[0]
                cmd = "stats/fcp/tunnel[%d]" % int(tunnel_id)

            result = self.dpc_client.execute(verb=self.VERB_PEEK, arg_list=[cmd])
            self.display_stats(result=result, stats_type=self.STATS_TYPE_FCP, global_result=is_global,
                               grep_regex=grep_regex)
            self._peek_stats_iteratively(cmd=cmd, stats_type=self.STATS_TYPE_FCP, prev_result=result,
                                         is_global=is_global, grep_regex=grep_regex)

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_peek_fcp_stats()

    def do_peek_wro_stats(self, args):
        try:
            arg_list = args.split()
            grep_regex = None
            is_global = False
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            if "global" in arg_list:
                is_global = True
                cmd = "stats/wro/global"
                if len(arg_list) > 1:
                    grep_regex = arg_list[0]
            else:
                if len(arg_list) > 1:
                    tunnel_id = arg_list[0]
                    grep_regex = arg_list[1]
                else:
                    tunnel_id = arg_list[0]
                cmd = "stats/wro/tunnel[%d]" % int(tunnel_id)

            result = self.dpc_client.execute(verb=self.VERB_PEEK, arg_list=[cmd])
            self.display_stats(result=result, stats_type=self.STATS_TYPE_WRO, global_result=is_global,
                               grep_regex=grep_regex)
            self._peek_stats_iteratively(cmd=cmd, stats_type=self.STATS_TYPE_WRO, prev_result=result,
                                         is_global=is_global, grep_regex=grep_regex)

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_peek_wro_stats()

    def do_peek_erp_stats(self, args):
        pass

    # ------------------------------------------------------------------------------------------
    # Starting port commands
    def do_enable_port(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["enable", cmd_arg_dict])
            if result:
                print "Port %d enabled successfully" % port_num
            else:
                print "Something went wrong unable to enable port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port()

    def help_enable_port(self):
        print "Syntax: enable_port <port_num> <shape>"
        print "E.g enable_port 6 0"

    def do_disable_port(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["disable", cmd_arg_dict])
            if result:
                print "Port %d disabled successfully" % port_num
            else:
                print "Something went wrong unable to disable port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_disable_port()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_disable_port()

    def help_disable_port(self):
        print "Syntax: disable_port <port_num> <shape>"
        print "E.g disable_port 6 0"

    def do_clear_port_stats(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["clearstats", cmd_arg_dict])
            if result:
                print "Port %d stats cleared successfully" % port_num
            else:
                print "Something went wrong unable to clear port %d stats. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_clear_port_stats()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_clear_port_stats()

    def help_clear_port_stats(self):
        print "Syntax: clear_port_stats <port_num> <shape>"
        print "E.g clear_port_stats 6 0"

    def do_set_port_mtu(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            mtu = int(arg_list[2])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            mtu_dict = {"mtu": mtu}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["mtuset", cmd_arg_dict, mtu_dict])
            if result:
                print "Port %d MTU set to %d" % (port_num, mtu)
            else:
                print "Something went wrong unable to set port %d mtu. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_mtu()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_mtu()

    def help_set_port_mtu(self):
        print "Syntax: set_port_mtu <port_num> <shape> <mtu>"
        print "E.g set_port_mtu 6 0 16380"

    def do_get_port_mtu(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["mtuget", cmd_arg_dict])
            if result:
                print "Port %d MTU: %d" % (port_num, result)
            else:
                print "Something went wrong unable to set port %d mtu. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_mtu()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_mtu()

    def help_get_port_mtu(self):
        print "Syntax: get_port_mtu <port_num> <shape>"
        print "E.g get_port_mtu 6 0"

    def do_enable_port_link_pause(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lpena", cmd_arg_dict])
            if result:
                print "Link Pause on Port %d enabled successfully" % port_num
            else:
                print "Something went wrong unable to enable link pause on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_link_pause()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_link_pause()

    def help_enable_port_link_pause(self):
        print "Syntax: enable_port_link_pause <port_num> <shape>"
        print "E.g enable_port_link_pause 6 0"

    def do_disable_port_link_pause(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lpdis", cmd_arg_dict])
            if result:
                print "Link Pause on Port %d disabled successfully" % port_num
            else:
                print "Something went wrong unable to disable link pause on port %d. dpc result: %s" % (port_num,
                                                                                                        result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_disable_port_link_pause()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_disable_port_link_pause()

    def help_disable_port_link_pause(self):
        print "Syntax: disable_port_link_pause <port_num> <shape>"
        print "E.g disable_port_link_pause 6 0"

    def do_enable_port_tx_link_pause(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lptxon", cmd_arg_dict])
            if result:
                print "Tx Link Pause on Port %d enabled successfully" % port_num
            else:
                print "Something went wrong unable to enable tx link pause on port %d. dpc result: %s" % (port_num,
                                                                                                          result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_tx_link_pause()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_tx_link_pause()

    def help_enable_port_tx_link_pause(self):
        print "Syntax: enable_port_tx_link_pause <port_num> <shape>"
        print "E.g enable_port_tx_link_pause 6 0"

    def do_disable_port_tx_link_pause(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lptxoff", cmd_arg_dict])
            if result:
                print "Tx Link Pause on Port %d disabled successfully" % port_num
            else:
                print "Something went wrong unable to disable tx link pause on port %d. dpc result: %s" % (port_num,
                                                                                                           result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_disable_port_tx_link_pause()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_disable_port_tx_link_pause()

    def help_disable_port_tx_link_pause(self):
        print "Syntax: disable_port_tx_link_pause <port_num> <shape>"
        print "E.g disable_port_tx_link_pause 6 0"

    def do_set_port_link_pause_quanta(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            quanta = int(arg_list[2])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            quanta_dict = {"quanta": quanta}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lpqset", cmd_arg_dict, quanta_dict])
            if result:
                print "Link pause quanta on port %d set to %d" % (port_num, quanta)
            else:
                print "Something went wrong unable to set link pause quanta on port %d. dpc result: %s" % (port_num,
                                                                                                           result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_link_pause_quanta()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_link_pause_quanta()

    def help_set_port_link_pause_quanta(self):
        print "Syntax: set_port_link_pause_quanta <port_num> <shape> <quanta>"
        print "E.g set_port_link_pause_quanta 6 0 16380"

    def do_get_port_link_pause_quanta(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lpqget", cmd_arg_dict])
            if result:
                print "Port %d Link pause quanta: %d" % (port_num, result)
            else:
                print "Something went wrong unable to get link pause quanta on port %d. dpc result: %s" % (port_num,
                                                                                                           result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_link_pause_quanta()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_link_pause_quanta()

    def help_get_port_link_pause_quanta(self):
        print "Syntax: get_port_link_pause_quanta <port_num> <shape>"
        print "E.g get_port_link_pause_quanta 6 0"

    def do_set_port_link_pause_threshold(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            threshold = int(arg_list[2])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            threshold_dict = {"threshold": threshold}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lptset", cmd_arg_dict, threshold_dict])
            if result:
                print "Link pause threshold on port %d set to %d" % (port_num, threshold)
            else:
                print "Something went wrong unable to set link pause threshold on port %d. dpc result: %s" % (port_num,
                                                                                                              result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_link_pause_threshold()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_link_pause_threshold()

    def help_set_port_link_pause_threshold(self):
        print "Syntax: set_port_link_pause_threshold <port_num> <shape> <threshold>"
        print "E.g set_port_link_pause_threshold 6 0 16380"

    def do_get_port_link_pause_threshold(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["lptget", cmd_arg_dict])
            if result:
                print "Port %d Link pause threshold: %d" % (port_num, result)
            else:
                print "Something went wrong unable to get link pause threshold on port %d. dpc result: %s" % (port_num,
                                                                                                              result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_link_pause_threshold()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_link_pause_threshold()

    def help_get_port_link_pause_threshold(self):
        print "Syntax: get_port_link_pause_threshold <port_num> <shape>"
        print "E.g get_port_link_pause_threshold 6 0"

    def do_enable_port_pfc(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfcena", cmd_arg_dict])
            if result:
                print "PFC on Port %d enabled successfully" % port_num
            else:
                print "Something went wrong unable to enable pfc on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_pfc()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_pfc()

    def help_enable_port_pfc(self):
        print "Syntax: enable_port_pfc <port_num> <shape>"
        print "E.g enable_port_pfc 6 0"

    def do_disable_port_pfc(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfcdis", cmd_arg_dict])
            if result:
                print "PFC on Port %d disabled successfully" % port_num
            else:
                print "Something went wrong unable to disable pfc on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_disable_port_pfc()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_disable_port_pfc()

    def help_disable_port_pfc(self):
        print "Syntax: disable_port_pfc <port_num> <shape>"
        print "E.g disable_port_pfc 6 0"

    def do_enable_port_tx_pfc(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            class_num = int(arg_list[2])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            class_dict = {"class": class_num}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfctxon", cmd_arg_dict, class_dict])
            if result:
                print "Tx PFC on Port %d enabled successfully" % port_num
            else:
                print "Something went wrong unable to enable tx pfc on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_tx_pfc()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_tx_pfc()

    def help_enable_port_tx_pfc(self):
        print "Syntax: enable_port_tx_pfc <port_num> <shape> <class>"
        print "E.g enable_port_tx_pfc 6 0 2"

    def do_disable_port_tx_pfc(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            class_num = int(arg_list[2])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            class_dict = {"class": class_num}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfctxoff", cmd_arg_dict, class_dict])
            if result:
                print "Tx PFC on Port %d disabled successfully" % port_num
            else:
                print "Something went wrong unable to disable tx pfc on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_disable_port_tx_pfc()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_disable_port_tx_pfc()

    def help_disable_port_tx_pfc(self):
        print "Syntax: disable_port_tx_pfc <port_num> <shape> <class>"
        print "E.g disable_port_tx_pfc 6 0 2"

    def do_set_port_pfc_quanta(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 4:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            class_num = int(arg_list[2])
            quanta = int(arg_list[3])

            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            quanta_dict = {"class": class_num, "quanta": quanta}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfcqset", cmd_arg_dict, quanta_dict])
            if result:
                print "PFC quanta on port %d set to %d" % (port_num, quanta)
            else:
                print "Something went wrong unable to set pfc quanta on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_pfc_quanta()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_pfc_quanta()

    def help_set_port_pfc_quanta(self):
        print "Syntax: set_port_pfc_quanta <port_num> <shape> <class> <quanta>"
        print "E.g set_port_pfc_quanta 6 0 2 16380"

    def do_get_port_pfc_quanta(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfcqget", cmd_arg_dict])
            if result:
                print "Port %d PFC quanta: %d" % (port_num, result)
            else:
                print "Something went wrong unable to get pfc port %d quanta. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_pfc_quanta()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_pfc_quanta()

    def help_get_port_pfc_quanta(self):
        print "Syntax: get_port_pfc_quanta <port_num> <shape>"
        print "E.g get_port_pfc_quanta 6 0"

    def do_set_port_pfc_threshold(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 4:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            class_num = int(arg_list[2])
            threshold = int(arg_list[3])

            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            threshold_dict = {"class": class_num, "threshold": threshold}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfctset", cmd_arg_dict, threshold_dict])
            if result:
                print "PFC threshold on port %d set to %d" % (port_num, threshold)
            else:
                print "Something went wrong unable to set pfc threshold on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_pfc_threshold()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_pfc_threshold()

    def help_set_port_pfc_threshold(self):
        print "Syntax: set_port_pfc_threshold <port_num> <shape> <class> <threshold>"
        print "E.g set_port_pfc_threshold 6 0 2 16380"

    def do_get_port_pfc_threshold(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["pfctget", cmd_arg_dict])
            if result:
                print "Port %d PFC threshold: %d" % (port_num, result)
            else:
                print "Something went wrong unable to get pfc port %d threshold. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_pfc_threshold()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_pfc_threshold()

    def help_get_port_pfc_threshold(self):
        print "Syntax: get_port_pfc_threshold <port_num> <shape>"
        print "E.g get_port_pfc_threshold 6 0"

    def do_enable_port_ptp_peer_delay(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptppeerdelayena", cmd_arg_dict])
            if result:
                print "PTP peer delay on port %d enabled" % port_num
            else:
                print "Unable to enable PTP peer delay on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_ptp_peer_delay()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_ptp_peer_delay()

    def help_enable_port_ptp_peer_delay(self):
        print "Syntax: enable_ptp_peer_delay <port_num> <shape>"
        print "E.g enable_ptp_peer_delay 6 0"

    def do_disable_port_ptp_peer_delay(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptppeerdelaydis", cmd_arg_dict])
            if result:
                print "PTP peer delay on port %d disabled" % port_num
            else:
                print "Unable to disable PTP peer delay on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_disable_port_ptp_peer_delay()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_disable_port_ptp_peer_delay()

    def help_disable_port_ptp_peer_delay(self):
        print "Syntax: disable_port_ptp_peer_delay <port_num> <shape>"
        print "E.g disable_port_ptp_peer_delay 6 0"

    def do_set_port_ptp_peer_delay(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            delay = int(arg_list[2])

            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            delay_dict = {"delay": delay}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptppeerdelayset", cmd_arg_dict, delay_dict])
            if result:
                print "PTP peer delay on port %d set to %d" % (port_num, delay)
            else:
                print "Unable to set PTP peer delay on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_ptp_peer_delay()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_ptp_peer_delay()

    def help_set_port_ptp_peer_delay(self):
        print "Syntax: set_port_ptp_peer_delay <port_num> <shape> <delay>"
        print "E.g set_port_ptp_peer_delay 6 0 555"

    def do_get_port_ptp_peer_delay(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptppeerdelayget", cmd_arg_dict])
            if result:
                print "PTP peer delay on port %d is %d" % (port_num, result)
            else:
                print "Unable to get PTP peer delay on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_ptp_peer_delay()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_ptp_peer_delay()

    def help_get_port_ptp_peer_delay(self):
        print "Syntax: get_port_ptp_peer_delay <port_num> <shape>"
        print "E.g get_port_ptp_peer_delay 6 0"

    def do_get_port_ptp_tx_ts(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptptxtsget", cmd_arg_dict])
            if result:
                print "PTP TX ts on port %d is %d" % (port_num, result)
            else:
                print "Unable to get PTP TX ts on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_get_port_ptp_tx_ts()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_port_ptp_tx_ts()

    def help_get_port_ptp_tx_ts(self):
        print "Syntax: get_port_ptp_tx_ts <port_num> <shape>"
        print "E.g get_port_ptp_tx_ts 6 0"

    def do_dump_port_runt_filter(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            cmd_arg_dict = {"portnum": port_num, "shape": shape}

            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["runtfilterdump", cmd_arg_dict])
            if result:
                print "Dump runt filter on port %d" % (port_num)
            else:
                print "Unable to dump runt filter on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_dump_port_runt_filter()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_dump_port_runt_filter()

    def help_dump_port_runt_filter(self):
        print "Syntax: dump_port_runt_filter <port_num> <shape>"
        print "E.g dump_port_runt_filter 6 0"

    def do_set_port_runt_filter_dump(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 5:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])
            buffer = int(arg_list[2])
            runt_err_en = int(arg_list[3])
            en_delete = int(arg_list[4])
            
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            runt_dict = {"buffer_64": buffer, "runt_err_en": runt_err_en, "en_delete": en_delete}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["runtfilterset", cmd_arg_dict, runt_dict])
            if result:
                print "Set runt filter dump on port %d" % port_num
            else:
                print "Unable to set runt filter dump on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_set_port_runt_filter_dump()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_port_runt_filter_dump()

    def help_set_port_runt_filter_dump(self):
        print "Syntax: set_port_runt_filter_dump <port_num> <shape> <buffer_64> <runt_err_en> <en_delete>"
        print "E.g set_port_runt_filter_dump 6 0 0 1 0"

    def do_enable_port_ptp_1step(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])

            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptp1stepena", cmd_arg_dict])
            if result:
                print "Enable PTP 1st step on port %d" % port_num
            else:
                print "Unable to enable PTP 1st step on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_ptp_1step()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_ptp_1step()

    def help_enable_port_ptp_1step(self):
        print "Syntax: enable_port_ptp_1step <port_num> <shape>"
        print "E.g set_port_runt_filter_dump 6 0"

    def do_disable_port_ptp_1step(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            shape = int(arg_list[1])

            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb=self.VERB_PORT, arg_list=["ptp1stepdis", cmd_arg_dict])
            if result:
                print "Disabled PTP 1st step on port %d" % port_num
            else:
                print "Unable to disable PTP 1st step on port %d. dpc result: %s" % (port_num, result)
        except TypeError:
            print "ERROR: Given arguments are not in integer. See below help"
            self.help_enable_port_ptp_1step()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_enable_port_ptp_1step()

    def help_disable_port_ptp_1step(self):
        print "Syntax: disable_port_ptp_1step <port_num> <shape>"
        print "E.g disable_port_ptp_1step 6 0"

    # ------------------------------------------------------------------------------------------
    # Starting QoS Commands
    def _get_qos_buffer(self, arg_list):
        try:
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=arg_list)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            result = {}
        return result

    def _update_qos_buffer(self, buffer_type, value_dict, **kwargs):
        result = None
        try:
            for key in value_dict:
                try:
                    val = raw_input("Enter %s: " % key)
                except ValueError:
                    print "Please enter integer value"
                    val = int(raw_input("Enter %s: " % key))
                if val == '':
                    continue
                else:
                    value_dict[key] = int(val)
            if kwargs:
                for key in kwargs:
                    value_dict[key] = kwargs[key]
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", buffer_type, value_dict])
        except Exception as ex:
            print "ERROR: %s" % str(ex)
        return result

    def do_set_qos_egress_buffer_pool(self, args):
        try:
            get_arg_list = ["get", "egress_buffer_pool"]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get egress_buffer_pool values")
            result = self._update_qos_buffer(buffer_type="egress_buffer_pool", value_dict=existing_buffer_dict)
            if result:
                print "Updated QoS egress buffer pool successfully"
            else:
                print "Unable to set QoS egress buffer pool. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def help_set_qos_egress_buffer_pool(self):
        print "Syntax: set_qos_egress_buffer_pool"

    def do_get_qos_egress_buffer_pool(self, arg):
        try:
            result = self._get_qos_buffer(arg_list=["get", "egress_buffer_pool"])
            if not result:
                raise RuntimeError("Failed to get egress_buffer_pool values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_egress_buffer_pool()

    def help_get_qos_egress_buffer_pool(self):
        print "Syntax: get_qos_egress_buffer_pool"

    def do_set_qos_egress_port_buffer(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            get_arg_list = ["get", "egress_port_buffer", {"port": port_num}]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get egress_port_buffer values")
            kwargs = {"port": port_num}
            result = self._update_qos_buffer(buffer_type="egress_port_buffer",
                                             value_dict=existing_buffer_dict, **kwargs)
            if result:
                print "Set QoS egress port %d buffer " % port_num
            else:
                print "Unable to set QoS egress port buffer. dpc result: %s" % result

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_egress_port_buffer()

    def help_set_qos_egress_port_buffer(self):
        print "Syntax: set_qos_egress_port_buffer <port_num>"
        print "E.g set_qos_egress_buffer_pool 6"

    def do_get_qos_egress_port_buffer(self, arg):
        try:
            arg_list = arg.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            inputs = {"port": port_num}
            cmd_arg_list = ["get", "egress_port_buffer", inputs]
            result = self._get_qos_buffer(arg_list=cmd_arg_list)
            if not result:
                raise RuntimeError("Failed to get egress_port_buffer values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_egress_port_buffer()

    def help_get_qos_egress_port_buffer(self):
        print "Syntax: get_qos_egress_port_buffer <port_num>"
        print "E.g get_qos_egress_port_buffer 6"

    def do_set_qos_egress_queue_buffer(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            kwargs = {"port": port_num, "queue": queue_num}
            get_arg_list = ["get", "egress_queue_buffer", kwargs]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get egress_queue_buffer values")

            result = self._update_qos_buffer(buffer_type="egress_queue_buffer",
                                             value_dict=existing_buffer_dict, **kwargs)
            if result:
                print "Set QoS egress queue buffer Port: %d Queue: %d" % (port_num, queue_num)
            else:
                print "Unable to set QoS egress queue buffer. dpc result: %s" % result

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_egress_queue_buffer()

    def help_set_qos_egress_queue_buffer(self):
        print "Syntax: set_qos_egress_queue_buffer <port_num> <queue_num>"
        print "E.g set_qos_egress_queue_buffer 6 1"

    def do_get_qos_egress_queue_buffer(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            kwargs = {"port": port_num, "queue": queue_num}
            get_arg_list = ["get", "egress_queue_buffer", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get egress_queue_buffer values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_egress_queue_buffer()

    def help_get_qos_egress_queue_buffer(self):
        print "Syntax: get_qos_egress_queue_buffer <port_num> <queue_num>"
        print "E.g get_qos_egress_queue_buffer 6 1"

    def do_set_qos_ingress_priority_group(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            pg = int(arg_list[1])
            kwargs = {"port": port_num, "pg": pg}
            get_arg_list = ["get", "ingress_priority_group", kwargs]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get egress_queue_buffer values")

            result = self._update_qos_buffer(buffer_type="ingress_priority_group",
                                             value_dict=existing_buffer_dict, **kwargs)
            if result:
                print "Set QoS ingress_priority_group Port: %d Pg: %d" % (port_num, pg)
            else:
                print "Unable to set QoS ingress_priority_group. dpc result: %s" % result

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_ingress_priority_group()

    def help_set_qos_ingress_priority_group(self):
        print "Syntax: set_qos_ingress_priority_group <port_num> <pg>"
        print "E.g set_qos_ingress_priority_group 6 1"

    def do_get_qos_ingress_priority_group(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            pg = int(arg_list[1])
            kwargs = {"port": port_num, "pg": pg}
            get_arg_list = ["get", "ingress_priority_group", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get ingress_priority_group values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_ingress_priority_group()

    def help_get_qos_ingress_priority_group(self):
        print "Syntax: get_qos_ingress_priority_group <port_num> <pg>"
        print "E.g get_qos_ingress_priority_group 6 1"

    def do_set_qos_priority_to_pg_map(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            num_of_priorities = int(arg_list[1])
            kwargs = {"port": port_num, "map": []}
            for i in range(0, num_of_priorities):
                try:
                    val = raw_input("Enter Map val: ")
                except ValueError:
                    print "Please enter integer value"
                    val = int(raw_input("Enter mpa val: "))
                if val == '':
                    continue
                else:
                    kwargs["map"].append(val)

            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "priority_to_pg_map", kwargs])
            if result:
                print "Set QoS priority_to_pg_map Port: %d map_list: %s" % (port_num, kwargs["map"])
            else:
                print "Unable to set QoS priority_to_pg_map. dpc result: %s" % result

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_priority_to_pg_map()

    def help_set_qos_priority_to_pg_map(self):
        print "Syntax: set_qos_priority_to_pg_map <port_num> <n>"
        print "Where n is number of priorities, n = 16 for FPG ports and n = 8 for EPG ports "
        print "E.g set_qos_priority_to_pg_map 6 8"

    def do_get_qos_priority_to_pg_map(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            kwargs = {"port": port_num}
            get_arg_list = ["get", "priority_to_pg_map", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get priority_to_pg_map values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_priority_to_pg_map()

    def help_get_qos_priority_to_pg_map(self):
        print "Syntax: get_qos_priority_to_pg_map <port_num>"
        print "E.g get_qos_priority_to_pg_map 6"

    def do_set_qos_pfc(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            enable = int(arg_list[0])
            kwargs = {"enable": enable}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "pfc", kwargs])
            if result:
                print "Set QoS pfc enable: %d" % enable
            else:
                print "Unable to set QoS pfc. dpc result: %s" % result

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_pfc()

    def help_set_qos_pfc(self):
        print "Syntax: set_qos_pfc <enable>"
        print "E.g set_qos_pfc 1"

    def do_get_qos_pfc(self, args):
        try:
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["get", "pfc"])
            if not result:
                raise RuntimeError("Failed to get pfc values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_pfc()

    def help_get_qos_pfc(self):
        print "Syntax: get_qos_pfc"
        print "E.g get_qos_pfc"

    def do_set_qos_wred_queue_config(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            kwargs = {"port": port_num, "queue": queue_num}
            get_arg_list = ["get", "wred_queue_config", kwargs]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get wred_queue_config values")

            result = self._update_qos_buffer(buffer_type="wred_queue_config",
                                             value_dict=existing_buffer_dict, **kwargs)
            if result:
                print "Set QoS wred_queue_config Port: %d Queue: %d" % (port_num, queue_num)
            else:
                print "Unable to set QoS wred_queue_config. dpc result: %s" % result

        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_wred_queue_config()

    def help_set_qos_wred_queue_config(self):
        print "Syntax: set_qos_wred_queue_config <port_num> <queue_num>"
        print "E.g set_qos_wred_queue_config 6 1"

    def do_get_qos_wred_queue_config(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            kwargs = {"port": port_num, "queue": queue_num}
            get_arg_list = ["get", "wred_queue_config", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get wred_queue_config values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_wred_queue_config()

    def help_get_qos_wred_queue_config(self):
        print "Syntax: get_qos_wred_queue_config <port_num> <queue_num>"
        print "E.g get_qos_wred_queue_config 6 1"

    def do_set_qos_wred_profile(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            prof_num = int(arg_list[0])
            kwargs = {"prof_num": prof_num}
            get_arg_list = ["get", "wred_profile", kwargs]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get wred_profile values")

            result = self._update_qos_buffer(buffer_type="wred_profile",
                                             value_dict=existing_buffer_dict, **kwargs)
            if result:
                print "Set QoS wred_profile Port: %d" % prof_num
            else:
                print "Unable to set QoS wred_profile. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_wred_profile()

    def help_set_qos_wred_profile(self):
        print "Syntax: set_qos_wred_profile <prof_num>"
        print "E.g set_qos_wred_profile 6"

    def do_get_qos_wred_profile(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            prof_num = int(arg_list[0])
            kwargs = {"prof_num": prof_num}
            get_arg_list = ["get", "wred_profile", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get wred_profile values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_wred_profile()

    def help_get_qos_wred_profile(self):
        print "Syntax: get_qos_wred_profile <prof_num>"
        print "E.g get_qos_wred_profile 6"

    def do_set_qos_wred_prob(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            prob_idx = int(arg_list[0])
            prob = int(arg_list[1])
            kwargs = {"prob_idx": prob_idx, "prob": prob}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "wred_prob", kwargs])
            if result:
                print "Set QoS wred_profile prob idx: %d" % prob_idx
            else:
                print "Unable to set QoS wred_profile. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_wred_prob()

    def help_set_qos_wred_prob(self):
        print "Syntax: set_qos_wred_prob <prob_idx> <prob>"
        print "E.g set_qos_wred_prob 6 1"

    def do_get_qos_wred_prob(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            prob_idx = int(arg_list[0])
            kwargs = {"prob_idx": prob_idx}
            get_arg_list = ["get", "wred_prob", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get wred_profile values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_wred_prob()

    def help_get_qos_wred_prob(self):
        print "Syntax: get_qos_wred_prob <prob_idx>"
        print "E.g get_qos_wred_prob 6"

    def do_set_qos_ecn_profile(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            prof_num = int(arg_list[0])
            kwargs = {"prof_num": prof_num}
            get_arg_list = ["get", "ecn_profile", kwargs]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get ecn_profile values")

            result = self._update_qos_buffer(buffer_type="ecn_profile",
                                             value_dict=existing_buffer_dict, **kwargs)
            if result:
                print "Set QoS ecn_profile Prof: %d" % prof_num
            else:
                print "Unable to set QoS ecn_profile. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_ecn_profile()

    def help_set_qos_ecn_profile(self):
        print "Syntax: set_qos_ecn_profile <prof_num>"
        print "E.g set_qos_ecn_profile 6"

    def do_get_qos_ecn_profile(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            prof_num = int(arg_list[0])
            kwargs = {"prof_num": prof_num}
            get_arg_list = ["get", "ecn_profile", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get ecn_profile values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_ecn_profile()

    def help_get_qos_ecn_profile(self):
        print "Syntax: get_qos_ecn_profile <prof_num>"
        print "E.g get_qos_ecn_profile 6"

    def do_set_qos_ecn_prob(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 2:
                raise RuntimeError("Insufficient arguments. See below help")
            prob_idx = int(arg_list[0])
            prob = int(arg_list[1])
            kwargs = {"prob_idx": prob_idx, "prob": prob}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "ecn_prob", kwargs])
            if result:
                print "Set QoS wred_profile prob idx: %d" % prob_idx
            else:
                print "Unable to set QoS wred_profile. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_ecn_prob()

    def help_set_qos_ecn_prob(self):
        print "Syntax: set_qos_ecn_prob <prob_idx> <prob>"
        print "E.g set_qos_ecn_prob 6 1"

    def do_get_qos_ecn_prob(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            prob_idx = int(arg_list[0])
            kwargs = {"prob_idx": prob_idx}
            get_arg_list = ["get", "ecn_prob", kwargs]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get wred_profile values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_ecn_prob()

    def help_get_qos_ecn_prob(self):
        print "Syntax: get_qos_ecn_prob <prob_idx>"
        print "E.g get_qos_ecn_prob 6"

    def do_get_qos_scheduler_config(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) >= 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            grep_regex = None
            if len(arg_list) == 3:
                grep_regex = arg_list[3]
            kwargs = {"port": port_num, "queue": queue_num}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["get", "scheduler_config", kwargs])
            if not result:
                raise RuntimeError("Failed to get wred_profile values")
            for scheduler in result:
                if grep_regex:
                    if re.search(grep_regex, scheduler, re.IGNORECASE):
                        self.display_qos_stats(result=result[scheduler])
                else:
                    self.display_qos_stats(result=result[scheduler], grep_regex=grep_regex)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_ecn_prob()

    def help_get_qos_scheduler_config(self):
        print "Syntax: get_qos_scheduler_config <port_num> <queue_num> <scheduler_grep_regex>"
        print "E.g get_qos_scheduler_config 6 1 shaper"

    def do_set_qos_scheduler_dwrr_config(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 3:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            weight = int(arg_list[2])
            kwargs = {"port": port_num, "queue": queue_num, "weight": weight}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "scheduler_config", "dwrr", kwargs])
            if result:
                print "Set QoS scheduler dwrr config"
            else:
                print "Unable to set QoS scheduler dwrr config. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_scheduler_dwrr_config()

    def help_set_qos_scheduler_dwrr_config(self):
        print "Syntax: set_qos_scheduler_dwrr_config <port_num> <queue_num> <weight>"
        print "E.g set_qos_scheduler_dwrr_config 6 1 12"

    def do_set_qos_scheduler_shaper_config(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 5:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            shaper_enable = int(arg_list[2])
            min_rate = int(arg_list[3])
            max_rate = int(arg_list[4])
            kwargs = {"port": port_num, "queue": queue_num, "shaper_enable": shaper_enable, "min_rate": min_rate,
                      "max_rate": max_rate}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "scheduler_config", "shaper", kwargs])
            if result:
                print "Set QoS scheduler shaper config"
            else:
                print "Unable to set QoS scheduler shaper config. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_scheduler_shaper_config()

    def help_set_qos_scheduler_shaper_config(self):
        print "Syntax: set_qos_scheduler_shaper_config <port_num> <queue_num> <shaper_enable> <min_rate> <max_rate>"
        print "E.g set_qos_scheduler_shaper_config 6 1 1 50 90"

    def do_set_qos_scheduler_strict_priority_config(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) != 4:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            strict_priority_enable = int(arg_list[2])
            extra_bandwidth = int(arg_list[3])
            kwargs = {"port": port_num, "queue": queue_num, "strict_priority_enable": strict_priority_enable,
                      "extra_bandwidth": extra_bandwidth}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "scheduler_config", "strict_priority", kwargs])
            if result:
                print "Set QoS scheduler strict_priority config"
            else:
                print "Unable to set QoS scheduler strict_priority config. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_scheduler_strict_priority_config()

    def help_set_qos_scheduler_strict_priority_config(self):
        print "Syntax: set_qos_scheduler_strict_priority_config <port_num> <queue_num> <strict_priority_enable> " \
              "<extra_bandwidth>"
        print "E.g set_qos_scheduler_strict_priority_config 6 1 1 50"

    def do_set_qos_ecn_glb_sh_thresh(self, args):
        try:
            get_arg_list = ["get", "ecn_glb_sh_thresh"]
            existing_buffer_dict = self._get_qos_buffer(arg_list=get_arg_list)
            if not existing_buffer_dict:
                raise RuntimeError("Failed to get ecn_glb_sh_thresh values")

            result = self._update_qos_buffer(buffer_type="ecn_glb_sh_thresh",
                                             value_dict=existing_buffer_dict)
            if result:
                print "Set QoS ecn_glb_sh_thresh"
            else:
                print "Unable to set QoS ecn_glb_sh_thresh. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_ecn_glb_sh_thresh()

    def help_set_qos_ecn_glb_sh_thresh(self):
        print "Syntax: set_qos_ecn_glb_sh_thresh"
        print "E.g set_qos_ecn_glb_sh_thresh"

    def do_get_qos_ecn_glb_sh_thresh(self, args):
        try:
            get_arg_list = ["get", "ecn_glb_sh_thresh"]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get ecn_glb_sh_thresh values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_ecn_glb_sh_thresh()

    def help_get_qos_ecn_glb_sh_thresh(self):
        print "Syntax: get_qos_ecn_glb_sh_thresh"
        print "E.g get_qos_ecn_glb_sh_thresh"

    def do_get_qos_wred_ecn_stats(self, args):
        try:
            arg_list = args.split()
            if not arg_list or len(arg_list) >= 2:
                raise RuntimeError("Insufficient arguments. See below help")
            port_num = int(arg_list[0])
            queue_num = int(arg_list[1])
            grep_regex = None
            if len(arg_list) == 3:
                grep_regex = arg_list[2]
            kwargs = {"port": port_num, "queue": queue_num}
            result = self._get_qos_buffer(arg_list=["get", "wred_ecn_stats", kwargs])
            if not result:
                raise RuntimeError("Failed to get wred_ecn_stats values")
            self.display_qos_stats(result=result, grep_regex=grep_regex)
            self._peek_stats_iteratively(cmd=arg_list, stats_type=self.STATS_TYPE_WRED_ECN,
                                         prev_result=result, grep_regex=grep_regex, verb=self.VERB_QOS)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_wred_ecn_stats()

    def do_set_qos_arb_cfg(self, args):
        try:
            arg_list = args.split()
            if not arg_list:
                raise RuntimeError("Insufficient arguments. See below help")
            en = int(arg_list[0])
            kwargs = {"en": en}
            result = self.dpc_client.execute(verb=self.VERB_QOS, arg_list=["set", "arb_cfg", kwargs])
            if result:
                print "Set QoS arb_cfg"
            else:
                print "Unable to set QoS arb_cfg. dpc result: %s" % result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_set_qos_arb_cfg()

    def help_set_qos_arb_cfg(self):
        print "Syntax: set_qos_arb_cfg <en>"
        print "E.g set_qos_arb_cfg 1"

    def do_get_qos_arb_cfg(self, args):
        try:
            get_arg_list = ["get", "arb_cfg"]
            result = self._get_qos_buffer(arg_list=get_arg_list)
            if not result:
                raise RuntimeError("Failed to get arb_cfg values")
            self.display_qos_stats(result=result)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.help_get_qos_arb_cfg()

    def help_get_qos_arb_cfg(self):
        print "Syntax: get_qos_arb_cfg"
        print "E.g get_qos_arb_cfg"

    def help_get_qos_wred_ecn_stats(self):
        print "Syntax: get_qos_wred_ecn_stats <port_num> <queue_num> <grep_regex>"
        print "E.g get_qos_wred_ecn_stats 6 1 avg.*"

    def help_peek_erp_stats(self):
        pass

    def help_peek_wro_stats(self):
        print "Syntax: peek_wro_stats <tunnel_id> <grep_regex> or peek_wro_stats global <grep_regex>"
        print "E.g peek_wro_stats 204 dst.*"
        print "E.g peek_wro_stats global dst.*"
        print "grep_regex: Optional Argument: Enter regex to display only matched field/s"

    def help_peek_fcp_stats(self):
        print "Syntax: peek_fcp_stats <tunnel_id> <grep_regex> or peek_fcp_stats global <grep_regex>"
        print "E.g peek_fcp_stats 204 dst.*"
        print "E.g peek_fcp_stats global dst.*"
        print "grep_regex: Optional Argument: Enter regex to display only matched field/s"

    def help_peek_vp_stats(self):
        print "Syntax: peek_vp_stats <grep_regex>"
        print "grep_regex: Optional Argument: Enter regex to display only matched field/s"

    def help_peek_psw_stats(self):
        print "Syntax: peek_psw_stats <port_num> <queue_num> or peek_psw_stats global <grep_regex>"
        print "E.g peek_psw_stats 6 q_00"
        print "port_num: Required and queue_num: Optional"
        print "E.g peek_psw_stats global epg.*"
        print "grep_regex: Optional Argument: Enter regex to display only matched field/s Applicable only for " \
              "PSW global"

    def help_peek_fpg_stats(self):
        print "Syntax: peek_fpg_stats <port_num>  <grep regex>"
        print "grep_regex: Optional Argument. Enter regex to display only matched field/s"







if __name__ == "__main__":
    shell_obj = DpcshInteractive(target_ip='10.1.21.120', target_port=40221)
    print shell_obj.cmdloop(intro="Hello")

