from prettytable import PrettyTable, FRAME
from datetime import datetime
import time
import re
from nu_commands import do_sleep_for_interval

VOL_TYPE_BLK_LOCAL_THIN = 'VOL_TYPE_BLK_LOCAL_THIN'
VOL_TYPE_BLK_RDS = 'VOL_TYPE_BLK_RDS'


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
                                    if type(result[key][_key][inner_key]) == unicode:
                                        diff_result[key][_key][inner_key] = result[key][_key][inner_key]
                                    else:
                                        diff_value = result[key][_key][inner_key] - prev_result[key][_key][inner_key]
                                        diff_result[key][_key][inner_key] = diff_value
                                else:
                                    diff_result[key][_key][inner_key] = 0
                        else:
                            if type(result[key][_key]) == unicode:
                                diff_result[key][_key] = result[key][_key]
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
                    diff_result[key] = result[key]

        return diff_result

    def _get_required_ssd_results(self, result, ssd_ids):
        output = {}
        not_found_list = []
        for ssd_id in ssd_ids:
            if ssd_id not in result.keys():
                not_found_list.append(ssd_id)
            else:
                output[ssd_id] = result[ssd_id]
        if not_found_list:
            str1 = ' '.join(not_found_list)
            print "SSDs with ids %s not found" % str1
        return output


    def peek_connected_ssds(self, ssd_ids=[], grep=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "storage/devices/nvme/ssds"
                    result = self.dpc_client.execute(verb="peek", arg_list=[cmd], tid=4)
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.header = False
                    if ssd_ids:
                        result = self._get_required_ssd_results(result, ssd_ids)
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                table_obj.sortby = 'Field Name'
                                for _key in sorted(result[key]):
                                    if grep:
                                        if re.search(grep, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])

                                else:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                table_obj.sortby = 'Field Name'
                                for _key in sorted(result[key]):
                                    if grep:
                                        if re.search(grep, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, result[key][_key]])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        do_sleep_for_interval()
                    else:
                        print "Empty result"
                        break
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
                        do_sleep_for_interval()
                    else:
                        print "Empty result"

                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_blt_vol_stats(self, vol_id):
        cmd = "storage/volumes/%s/%s" % (VOL_TYPE_BLK_LOCAL_THIN, vol_id)
        self._peek_vol_stats(cmd=cmd)

    def peek_rds_vol_stats(self, vol_id):
        cmd = "storage/volumes/%s/%s" % (VOL_TYPE_BLK_RDS, vol_id)
        self._peek_vol_stats(cmd=cmd)

    def peek_storage_volumes(self, grep=None):
        cmd = "storage/volumes"
        try:
            result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
            if result:
                for key, val in result.iteritems():
                    if key == VOL_TYPE_BLK_RDS:
                        table_obj = PrettyTable(['sl no', 'volume uuid'])
                        table_obj.align = 'l'
                        counter = 0
                        for vol in val.keys():
                            counter += 1
                            table_obj.add_row([counter, vol])
                        print "******* %s ********" % key
                        print table_obj
                    if key == VOL_TYPE_BLK_LOCAL_THIN:
                        drives = result[VOL_TYPE_BLK_LOCAL_THIN]['drives']
                        table_obj = PrettyTable(['sl no', 'volume_uuid', 'drive_uuid', 'drive_id'])
                        table_obj.align = 'l'
                        counter = 0
                        print_table = False
                        for vol in val.keys():
                            if not vol == 'drives':
                                drive_uuid = None
                                drive_id = None
                                counter += 1
                                drive_uuid = val[vol]['stats']['drive_uuid']
                                drive_id = drives[drive_uuid]['drive_id']
                                table_obj.add_row([counter, vol, drive_uuid, drive_id])
                                print_table = True
                        if print_table:
                            print "******* %s ********" % key
                            print table_obj
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()
