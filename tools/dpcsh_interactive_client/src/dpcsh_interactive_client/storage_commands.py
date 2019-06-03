from prettytable import PrettyTable, FRAME
from datetime import datetime
import time
import re

TIME_INTERVAL = 1


class StoragePeekCommands(object):
    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def _get_timestamp(self):
        ts = time.time()
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    def _get_difference(self, result, prev_result):
        """
        :param result: Should be dict or dict of dict
        :param prev_result: Should be dict or dict of dict
        :return: dict or dict of dict
        """
        diff_result = {}
        for key in result:
            if type(result[key]) == dict:
                diff_result[key] = {}
                for _key in result[key]:
                    if key in prev_result and _key in prev_result[key]:
                        if type(result[key][_key]) == dict:
                            diff_result[key][_key] = {}
                            for inner_key in result[key][_key]:
                                if inner_key in prev_result[key][_key]:
                                    diff_value = result[key][_key][inner_key] - prev_result[key][_key][inner_key]
                                    diff_result[key][_key][inner_key] = diff_value
                                else:
                                    diff_result[key][_key][inner_key] = 0
                        else:
                            diff_value = result[key][_key] - prev_result[key][_key]
                            diff_result[key][_key] = diff_value
                    else:
                        diff_result[key][_key] = 0
            elif type(result[key]) == str:
                diff_result[key] = result[key]
            else:
                if key in prev_result:
                    if type(result[key]) == list:
                        diff_result[key] = result[key]
                        continue
                    diff_value = result[key] - prev_result[key]
                    diff_result[key] = diff_value
                else:
                    diff_result[key] = 0

        return diff_result

    def peek_connected_ssds(self, grep=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "storage/devices/nvme/ssds"
                    result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.header = False
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                table_obj.sortby = 'Field Name'
                                for _key in sorted(result[key]):
                                    table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                if grep:
                                    if re.search(grep, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                table_obj.sortby = 'Field Name'
                                for _key in sorted(result[key]):
                                    table_obj.add_row([_key, result[key][_key]])
                                if grep:
                                    if re.search(grep, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def _peek_vol_stats(self, cmd):
        try:
            prev_result = None
            while True:
                try:
                    result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.header = False
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                table_obj.sortby = 'Field Name'
                                for _key in sorted(result[key]):
                                    table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                table_obj.sortby = 'Field Name'
                                for _key in sorted(result[key]):
                                    table_obj.add_row([_key, result[key][_key]])
                                master_table_obj.add_row([key, table_obj])
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)

                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_blt_vol_stats(self, vol_id):
        cmd = "storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/%d" % vol_id
        self._peek_vol_stats(cmd=cmd)

    def peek_rds_vol_stats(self, vol_id):
        cmd = "storage/volumes/VOL_TYPE_BLK_RDS/%d" % vol_id
        self._peek_vol_stats(cmd=cmd)









