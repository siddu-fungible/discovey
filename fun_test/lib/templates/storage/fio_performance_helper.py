from lib.host.linux import *
from lib.system.fun_test import *
import re

'''
Script to find the best performance numbers 
'''


class FioPerfHelper(object):
    def __init__(self, handle, fio_testfile_size, dpc_conntroller, num_jobs=1, iodepth=1,
                 num_cores=1, fio_rwmode='read', nvme_device_name='/dev/nvme0n1', fio_test_runtime=20,
                 cpu_usage_limit=80, iowait_limit=2, iostat_skip_lines=10, block_size="4k", ioengine="libaio",
                 max_iodepth=500, eqm_limit=5):

        self.handle = handle
        self.dpc_conntroller = dpc_conntroller
        self.fio_testfile_size = fio_testfile_size
        self.nvme_device_name = nvme_device_name
        self.fio_rwmode = fio_rwmode
        self.fio_test_runtime = fio_test_runtime
        self.num_jobs = num_jobs
        self.iodepth = iodepth
        self.num_cores = num_cores
        self.block_size = block_size
        self.ioengine = ioengine
        # Threshold values
        self.cpu_usage_limit = cpu_usage_limit
        self.iowait_limit = iowait_limit
        self.iostat_skip_lines = iostat_skip_lines
        self.max_iodepth = max_iodepth
        self.eqm_limit = eqm_limit
        # Initialize
        self.overall_results_list = []

    def cores_allowed_comma_format(self, cores_allowed_list, num_cores):
        cpus_allowed = cores_allowed_list[:num_cores]
        comma_format = ','.join(cpus_allowed)
        return comma_format

    def start_iostat_in_background(self):
        '''
        Starts storing the iostat results in a file
        '''
        fun_test.debug("Starting iostat in background")
        iostat_device = self.nvme_device_name[5:]
        cmd = "iostat -d %s 1" % (iostat_device)
        pid = self.handle.start_bg_process(command=cmd, output_file="iostat.txt", timeout=self.fio_test_runtime * 2)
        return pid

    def start_mpstat_in_background(self, num_cores_str_format=None):
        '''
        Start storing mpstat results in the file
        '''
        if not num_cores_str_format:
            number_of_cores = self.present_result["num_cores"]
            fun_test.debug("Starting the mpstat in background")
            num_cores_str_format = self.cores_allowed_comma_format(self.cores_allowed_list, number_of_cores)
        cmd = "mpstat -P %s 1" % (num_cores_str_format)
        pid = self.handle.start_bg_process(command=cmd, output_file="mpstat.txt", timeout=self.fio_test_runtime * 2)
        return pid

    def run_fio_command(self):
        '''
        Runs the fio command using the given credentials
        '''
        cores_str_format = self.cores_allowed_comma_format(self.cores_allowed_list, self.present_result["num_cores"])
        fun_test.debug("Cpus allowed are : {}".format(cores_str_format))
        fun_test.log_section("\n\nStarting traffic")
        fun_test.log("\nStarting Fio with "
                     "\nNumber of jobs  : %s "
                     "\nIodepth         : %s "
                     "\nNumber of cores : %s"
                     "\nFio rw mode     : %s" %
                     (self.present_result["num_jobs"],
                      self.present_result["iodepth"],
                      self.present_result["num_cores"],
                      self.fio_rwmode))

        fio_output = self.handle.pcie_fio(filename=self.nvme_device_name,
                                          size=self.fio_testfile_size,
                                          bs=self.block_size,
                                          rw=self.fio_rwmode,
                                          iodepth=self.present_result["iodepth"],
                                          numjobs=self.present_result["num_jobs"],
                                          cpus_allowed=cores_str_format,
                                          name="pci_fio_test",
                                          group_reporting=1,
                                          prio=0,
                                          direct=1,
                                          ioengine=self.ioengine,
                                          time_based=1,
                                          runtime=self.fio_test_runtime,
                                          timeout=self.fio_test_runtime * 2)
        return fio_output

    def parse_iostat_file(self, iostat_file_location="iostat.txt"):
        '''
        From the iostat.txt file grep the values and finds average and max values[like tps(IOPS) and Kb read/s]
        '''
        fun_test.debug("Parsing {}".format(iostat_file_location))
        iostat_device = self.nvme_device_name[5:]

        result_dictionary = {}
        iostat_list = []

        # grep only the lines with nvme device name
        cmd = "cat {} | grep {}".format(iostat_file_location, iostat_device)
        output = self.handle.command(cmd)
        match_no_file = re.search(r'No such file', output)
        if match_no_file:
            fun_test.critical("{} file not found".format(iostat_file_location))
            return False

        # split the output into list of lines
        lines_list = output.split('\n')

        # Avoid some starting and some end values to get proper result
        number_of_lines = len(lines_list)
        lines_list = lines_list[self.iostat_skip_lines:(number_of_lines - self.iostat_skip_lines)]

        # if there is nothing in the iostat.txt file

        for line in lines_list:
            try:
                tmp_dict = {}
                values_list = re.findall(r'(?<= )[0-9.]+', line)
                tps = float(values_list[0])
                kb_read = float(values_list[1])
                if tps > 0:
                    tmp_dict['tps'] = tps
                if kb_read > 0:
                    tmp_dict['kb_read'] = kb_read
                if not (tmp_dict == {}):
                    iostat_list.append(tmp_dict.copy())
                    fun_test.debug(tmp_dict)
            except:
                # Skip the lines which are unparsable
                fun_test.log("Unable to parse this line : {}".format(line))

        if iostat_list:
            tps_list = list(item['tps'] for item in iostat_list)
            kb_read_list = list(item['kb_read'] for item in iostat_list)
            tps_values_sum = sum(tps_list)
            kbr_values_sum = sum(kb_read_list)
            max_tps = max(tps_list)
            max_kbread = max(kb_read_list)

            count = len(iostat_list)

            average_tps = round(tps_values_sum / float(count), 2)
            average_kbps_read = round(kbr_values_sum / float(count), 2)

            result_dictionary['average_tps'] = average_tps
            result_dictionary['average_kbr'] = average_kbps_read
            result_dictionary['maximum_tps'] = max_tps
            result_dictionary['maximum_kbr'] = max_kbread
            result_dictionary["iostat_list"] = iostat_list

            fun_test.log("Iostat result \nMaximum \ntps : %s    Kb_read/s : %s\nAverage \ntps : %s    Kb_read/s : %s  "
                         % (max_tps, max_kbread, average_tps, average_kbps_read))
            fun_test.debug("Overall result list : {}".format(result_dictionary))
            return result_dictionary
        else:
            fun_test.critical("Error in parsing {} file".format(iostat_file_location))
            return False

    def parse_mpstat_file(self, mpstat_file_location="mpstat.txt", iowait_limit=0, cpu_usage_limit=90):
        '''
        From the mpstat.txt file greps the cpu usage and iowait values for each core and stores them
        in a list of dictionaries, calculates the max cpu usage and
        iostat values.
        '''
        mpstat_list = []
        mpstat_result_dictionary = {}
        iowait_error = False
        cpu_error = False
        maximum_cpu_usage = 0
        maximum_iowait = 0
        error_msg = ''

        cmd = "cat {}".format(mpstat_file_location)
        output = self.handle.command(cmd)
        match_no_file = re.search(r'No such file', output)
        if match_no_file:
            fun_test.critical("{} file not found".format(mpstat_file_location))
            return False

        lines_list = output.split('\n')

        for line in lines_list:
            match_values = re.findall(r'(?<= )[0-9.]+', line)
            number_of_values = len(match_values)
            if number_of_values == 11:
                tmp_dict = {}
                core = int(match_values[0])
                user_cpu_usage = float(match_values[1])
                system_cpu_uage = float(match_values[3])
                total_cpu_usage = round(user_cpu_usage + system_cpu_uage, 2)
                iowait = float(match_values[4])
                idle = float(match_values[10])
                tmp_dict['core'] = core
                tmp_dict['total_cpu_usage'] = total_cpu_usage
                tmp_dict['iowait'] = iowait
                tmp_dict['idle'] = idle
                mpstat_list.append(tmp_dict)
                fun_test.debug(tmp_dict)
                if iowait > iowait_limit:
                    error_msg = error_msg + "Iowait of core {} is {} [greater than {}]\n" \
                        .format(core, iowait, iowait_limit)
                    iowait_error = True
                if total_cpu_usage > cpu_usage_limit:
                    error_msg = error_msg + "Cpu usage of core {} is {} [greater than {}]\n" \
                        .format(core, total_cpu_usage, cpu_usage_limit)
                    cpu_error = True
                if total_cpu_usage > maximum_cpu_usage:
                    maximum_cpu_usage = total_cpu_usage
                if iowait > maximum_iowait:
                    maximum_iowait = iowait

        mpstat_result_dictionary['maximum_cpu_usage'] = maximum_cpu_usage
        mpstat_result_dictionary['maximum_iowait'] = maximum_iowait
        mpstat_result_dictionary['cpu_usage_error'] = cpu_error
        mpstat_result_dictionary['iowait_error'] = iowait_error
        mpstat_result_dictionary["mpstat_list"] = mpstat_list
        mpstat_result_dictionary["error_msg"] = error_msg
        fun_test.debug("Mpstat result dictionary: {}".format(mpstat_result_dictionary))
        return mpstat_result_dictionary

    def save_the_resuts_obtained(self):
        '''
        save for number of jobs, iodepth, number of cores
        what are the results i.e from
        iostat : maximum and average, [tps and kbs read values]
        mpstat :1. max cpu usage and iowait
                2. iowait_error occured or not
                3. cpu usage is exceeded or not
                4. error message

        eqm error has occured or not
        eqm difference that is obtained
        overall result
        '''
        pass

    def analyse_fio(self):
        '''
        Runs the fio command and stores all the iostat and mpstat values during the fio run and
        :returns if the given conditions(example : iowait == 0 , cpu usage < 90%) are passed or not
        '''

        self.present_result = {}
        self.pid_dictionary = {}
        self.present_result['error_msg'] = ''
        self.present_result["num_jobs"] = self.num_jobs
        self.present_result["iodepth"] = self.iodepth
        self.present_result["num_cores"] = self.num_cores
        self.present_result["fio_rwmode"] = self.fio_rwmode
        self.present_result["fio_test_runtime"] = self.fio_test_runtime

        self.clear_iostat_mpstat_file()
        self.pid_dictionary["iostat"] = self.start_iostat_in_background()
        self.pid_dictionary["mpstat"] = self.start_mpstat_in_background()

        eqm_before = self.get_eqm_number()
        self.present_result["eqm_before_fio"] = eqm_before
        self.run_fio_command()
        eqm_after = self.get_eqm_number()
        self.present_result["eqm_after_fio"] = eqm_after
        eqm_difference = abs(eqm_after - eqm_before)

        if eqm_difference >= 0 and eqm_difference <= self.eqm_limit:
            eqm_error = False
        else:
            eqm_error = True
            error_msg = "EQM difference is {}\n".format(eqm_difference)
            self.present_result['error_msg'] = self.present_result['error_msg'] + error_msg

        self.present_result["eqm_error"] = eqm_error
        self.present_result["eqm_difference"] = eqm_difference
        self.handle.kill_process(self.pid_dictionary["iostat"], kill_seconds=1)
        self.handle.kill_process(self.pid_dictionary["mpstat"], kill_seconds=1)

        iostat_result_list = self.parse_iostat_file()
        if not iostat_result_list:
            return False
        self.update_iostat_result(iostat_result_list)

        mpstat_result_list = self.parse_mpstat_file(iowait_limit=self.iowait_limit,
                                                    cpu_usage_limit=self.cpu_usage_limit)
        if not mpstat_result_list:
            return False

        self.update_mpstat_result(mpstat_result_list)

        overall_result = fun_test.PASSED
        if eqm_error or self.present_result["iowait_error"] or self.present_result["cpu_usage_error"]:
            overall_result = fun_test.FAILED
        self.present_result["overall_result"] = overall_result
        self.overall_results_list.append(self.present_result)
        self.print_key_value_sorted(title="Result", dictionary=self.present_result)
        self.cleanup_everything()
        return self.present_result

    ''' Logic function design section '''

    ''' iodepth logic '''

    def get_fio_iodepth(self, numa=False, max_time=1200):

        self.overall_results_list = []
        if numa:
            self.cores_allowed_list = self.form_cores_allowed_list_numa()
        else:
            self.cores_allowed_list = self.form_cores_allowed_list()
        if not self.cores_allowed_list:
            return False
        self.analyse_fio()
        self.best_result = self.present_result.copy()
        first = 0
        last = 0
        flag = True
        iodepth = self.present_result['iodepth']
        num_jobs = self.present_result['num_jobs']
        timer = FunTimer(max_time)
        while not timer.is_expired():
            condition = self.iodepth_condition()
            if condition == "working":
                first = iodepth
                if flag:
                    iodepth = iodepth * 2
                else:
                    iodepth = ((iodepth + last) / 2)
            elif condition == 'not_working':
                last = iodepth
                flag = False
                iodepth = ((first + last) / 2)

            if (iodepth == last or iodepth == first):
                break

            self.iodepth = iodepth
            self.num_jobs = num_jobs
            self.num_cores = num_jobs
            self.limit_number_of_cores()
            self.analyse_fio()
            if iodepth >= self.max_iodepth:
                break

        self.iodepth = iodepth
        self.num_jobs = num_jobs
        self.num_cores = num_jobs
        self.print_the_overall_summary()
        self.print_the_final_result()
        self.cleanup_everything()
        if self.iodepth == 0:
            self.iodepth = 1
        return self.iodepth

    def iodepth_condition(self):

        if (self.present_result["overall_result"] == fun_test.PASSED and
                self.best_result["maximum_tps"] <= self.present_result["maximum_kbr"] and
                self.best_result['maximum_kbr'] <= self.present_result['maximum_kbr']):
            self.best_result = self.present_result.copy()
            return 'working'
        else:
            return "not_working"

    ''' Num jobs , iodepth and num cores logic'''

    def get_fio_iodepth_num_jobs_num_cores(self, numa=False, max_time=1200):
        self.overall_results_list = []
        if numa:
            self.cores_allowed_list = self.form_cores_allowed_list_numa()
        else:
            self.cores_allowed_list = self.form_cores_allowed_list()
        if not self.cores_allowed_list:
            return False
        self.analyse_fio()
        self.best_result = self.present_result.copy()
        first = 0
        last = 0
        flag = True
        worked = True
        iodepth = self.present_result['iodepth']
        num_jobs = self.present_result['num_jobs']
        forced = False
        timer = FunTimer(max_time)
        while not timer.is_expired():
            condition = self.iodepth_num_jobs_cores_condition()
            if condition == "working":
                worked = True
                first = iodepth
                if flag:
                    iodepth = iodepth * 2
                else:
                    iodepth = ((iodepth + last) / 2)
            elif condition == 'not_working':
                last = iodepth
                flag = False
                iodepth = ((first + last) / 2)

            elif condition == 'cpu_error':
                num_jobs = num_jobs * 2
                s_first = first
                s_last = iodepth
                worked = False
                first = 0
            elif condition == 'values_are_low':
                forced = True

            if (iodepth == last or iodepth == first) and worked:
                break
            elif (iodepth == last or iodepth == first and not (worked)) or forced:
                forced = False
                num_jobs = num_jobs / 2
                iodepth = int((s_first + s_last) / 2)
                first = s_first
                last = s_last
                worked = True
                if iodepth == first or iodepth == last:
                    break
            self.iodepth = iodepth
            self.num_jobs = num_jobs
            self.num_cores = num_jobs
            self.limit_number_of_cores()
            self.analyse_fio()
            if iodepth >= self.max_iodepth:
                break

        self.iodepth = iodepth
        self.num_jobs = num_jobs
        self.num_cores = num_jobs
        self.print_the_overall_summary()
        self.print_the_final_result()
        self.cleanup_everything()
        if self.iodepth == 0:
            self.iodepth = 1
        return self.num_jobs, self.iodepth, self.num_cores

    def iodepth_num_jobs_cores_condition(self):
        if (self.present_result["cpu_usage_error"] and not
            (self.present_result['iowait_error']) and not
                (self.present_result['eqm_error'])):
            return "cpu_error"

        elif (self.present_result["overall_result"] == fun_test.PASSED and
              self.best_result["maximum_tps"] <= self.present_result["maximum_kbr"] and
              self.best_result['maximum_kbr'] <= self.present_result['maximum_kbr']):
            self.best_result = self.present_result.copy()
            return 'working'
        elif (self.present_result["overall_result"] == fun_test.PASSED and
              self.best_result["maximum_tps"] >= self.present_result["maximum_kbr"] and
              self.best_result['maximum_kbr'] >= self.present_result['maximum_kbr']):
            return 'values_are_low'
        else:
            return "not_working"

    '''  MMAP Logic '''

    def get_num_jobs_num_cores(self, numa=False, max_time=1200):
        # self.cpu_usage_limit = 99
        # self.iowait_limit = 99

        self.overall_results_list = []
        # Form a list of allowed cores using numa and lscpu
        if numa:
            self.cores_allowed_list = self.form_cores_allowed_list_numa()
        else:
            self.cores_allowed_list = self.form_cores_allowed_list()
        if not self.cores_allowed_list:
            return False
        # initially run once with the results obtained and than continue with applying logic
        self.analyse_fio()
        # Best results stores the best performance paramters
        self.best_result = self.present_result.copy()
        timer = FunTimer(max_time)
        while not timer.is_expired():
            self.print_key_value_sorted(title="Previous result", dictionary=self.best_result)
            condition = self.num_jobs_condition()

            if condition == "working":
                self.num_jobs = self.num_jobs * 2
                self.num_cores = self.num_cores * 2
                self.limit_number_of_cores()
                self.analyse_fio()
            elif condition == "not_working":
                break

        start = int(self.num_jobs/2)
        end = self.num_jobs
        self.num_jobs = int((start + end) / 2)
        self.num_cores = self.num_jobs
        self.limit_number_of_cores()

        if start == 0 or start == 1:
            self.num_jobs = 1
            self.num_cores = 1
            fun_test.log("Error iodepth, failed at too low values")
            self.print_the_overall_summary()
            self.print_the_final_result()
            return self.num_jobs, self.num_cores
        timer = FunTimer(max_time)
        while not timer.is_expired():
            self.analyse_fio()
            self.print_key_value_sorted(title="Previous result", dictionary=self.best_result)
            condition = self.num_jobs_condition()
            if condition == 'working':
                start = self.num_jobs
            elif condition == 'not_working':
                end = self.num_jobs
            self.num_jobs = int((start+end)/2)
            self.num_cores = self.num_jobs
            self.limit_number_of_cores()
            if end == self.num_jobs or start == self.num_jobs:
                self.print_the_overall_summary()
                self.print_the_final_result()
                return self.num_jobs, self.num_cores

    def num_jobs_condition(self):
        if (self.present_result["overall_result"] == fun_test.PASSED and
            self.best_result["maximum_tps"] <= self.present_result["maximum_kbr"] and
                self.best_result['maximum_kbr'] <= self.present_result['maximum_kbr']):

            self.best_result = self.present_result.copy()
            return 'working'
        else:
            return 'not_working'

    def start_fio_analysis(self, cpus_allowed, num_jobs, iodepth, num_cores, fio_rwmode='read',
                           numa=False, fio_test_runtime=60):

        self.present_result = {}
        self.pid_dictionary = {}
        self.present_result['error_msg'] = ''
        self.present_result["num_jobs"] = num_jobs
        self.present_result["iodepth"] = iodepth
        self.present_result["num_cores"] = num_cores
        self.present_result["fio_rwmode"] = fio_rwmode
        self.present_result["fio_test_runtime"] = fio_test_runtime

        if numa:
            self.cores_allowed_list = self.form_cores_allowed_list_numa()
        else:
            self.cores_allowed_list = self.form_cores_allowed_list()
        if not self.cores_allowed_list:
            return False

        self.clear_iostat_mpstat_file()
        self.pid_dictionary["iostat"] = self.start_iostat_in_background()
        self.pid_dictionary["mpstat"] = self.start_mpstat_in_background(num_cores_str_format=cpus_allowed)
        eqm_before = self.get_eqm_number()
        self.present_result["eqm_before_fio"] = eqm_before

    def get_fio_analysis_results(self):
        eqm_after = self.get_eqm_number()
        self.present_result["eqm_after_fio"] = eqm_after
        eqm_difference = abs(self.present_result['eqm_before_fio'] - eqm_after)

        if eqm_difference >= 0 and eqm_difference <= 5:
            eqm_error = False
        else:
            eqm_error = True
            error_msg = "EQM difference is {}\n".format(eqm_difference)
            self.present_result['error_msg'] = self.present_result['error_msg'] + error_msg

        self.present_result["eqm_error"] = eqm_error
        self.present_result["eqm_difference"] = eqm_difference
        self.handle.kill_process(self.pid_dictionary["iostat"])
        self.handle.kill_process(self.pid_dictionary["mpstat"])

        iostat_result_list = self.parse_iostat_file()
        if not iostat_result_list:
            return False
        self.update_iostat_result(iostat_result_list)

        mpstat_result_list = self.parse_mpstat_file(iowait_limit=self.iowait_limit,
                                                    cpu_usage_limit=self.cpu_usage_limit)
        if not mpstat_result_list:
            return False
        self.update_mpstat_result(mpstat_result_list)

        overall_result = fun_test.PASSED
        if eqm_error or self.present_result["iowait_error"] or self.present_result["cpu_usage_error"]:
            overall_result = fun_test.FAILED
        self.present_result["overall_result"] = overall_result
        # self.overall_results_list.append(self.present_result)
        self.print_key_value_sorted(title="Fio Result", dictionary=self.present_result)
        self.cleanup_everything()
        return self.present_result

    ''' Helper functions '''

    def print_the_final_result(self):
        for index, dictionary in enumerate(self.overall_results_list):
            if (dictionary['num_jobs'] == self.num_jobs and
                dictionary['iodepth'] == self.iodepth and
                    dictionary['num_cores'] == self.num_cores):

                break
        self.print_key_value_sorted(title="\nFinal values", dictionary=self.overall_results_list[index])

    def update_iostat_result(self, iostat_result_dictionary):
        self.present_result["average_tps"] = iostat_result_dictionary['average_tps']
        self.present_result["average_kbr"] = iostat_result_dictionary['average_kbr']
        self.present_result["maximum_tps"] = iostat_result_dictionary['maximum_tps']
        self.present_result['maximum_kbr'] = iostat_result_dictionary['maximum_kbr']
        self.iostat_list = iostat_result_dictionary['iostat_list']

    def update_mpstat_result(self, mpstat_result_dictionary):
        self.present_result["maximum_cpu_usage"] = mpstat_result_dictionary['maximum_cpu_usage']
        self.present_result["maximum_iowait"] = mpstat_result_dictionary['maximum_iowait']
        self.present_result["cpu_usage_error"] = mpstat_result_dictionary['cpu_usage_error']
        self.present_result["iowait_error"] = mpstat_result_dictionary['iowait_error']
        self.present_result['error_msg'] = self.present_result['error_msg'] + mpstat_result_dictionary["error_msg"]
        self.mpstat_list = mpstat_result_dictionary["mpstat_list"]


    def clear_iostat_mpstat_file(self):
        '''
        Clears all the data in iostat and mpstat
        Note: Very important otherwise may result in errors
        '''
        cmd = " > iostat.txt"
        self.handle.command(cmd)
        cmd = " > mpstat.txt"
        self.handle.command(cmd)
        self.handle.remove_file(file_name="iostat.txt")
        self.handle.remove_file(file_name="mpstat.txt")
        fun_test.debug("Cleared the iostat.txt and mpstat.txt")

    def get_eqm_number(self):
        '''
        Returns the eqm number
        '''
        eqm_stat = self.dpc_conntroller.peek(props_tree="stats/eqm")
        eqm_required_data = int(eqm_stat["data"]["EFI->EQC Enqueue Interface valid"])
        fun_test.debug("EFI->EQC Enqueue Interface valid : {}".format(eqm_required_data))
        return eqm_required_data

    def limit_number_of_cores(self):
        '''
        will not let num_cores to be more than cpu cores present
        '''
        number_of_cores_present = self.handle.get_number_cpus()
        if self.num_cores > (number_of_cores_present - 1):
            self.num_cores = number_of_cores_present - 1
        return self.num_cores

    def print_the_overall_summary(self):
        fun_test.log_section("overall summary")
        for index, i in enumerate(self.overall_results_list):
            self.print_key_value_sorted(title="Result {}".format(index + 1), dictionary=i)

    def print_key_value_sorted(self, dictionary, title='', spacing=50):
        order_of_print = ['num_jobs', 'iodepth', 'num_cores', 'maximum_kbr', 'average_kbr',
                          'maximum_tps', 'average_tps', 'maximum_cpu_usage', 'maximum_iowait',
                          'eqm_after_fio', 'eqm_before_fio', 'eqm_difference',
                          'cpu_usage_error', 'iowait_error', 'eqm_error', 'fio_test_runtime',
                          'fio_rwmode', 'error_msg', 'overall_result']
        fun_test.log_section(title)
        use_this = "{:<"+str(spacing)+"}{}"
        for key in order_of_print:
            fun_test.log(use_this.format(key, dictionary[key]))

    def set_iostat_skip_lines(self, skip_lines):
        '''
        Skips the first n lines of the iostat.txt file
        '''
        self.iostat_skip_lines = skip_lines

    def clear_the_cache(self):
        # get free memory before clearing cache
        free_memory_dictionary = self.handle.free(memory="m")
        free_memory = free_memory_dictionary['free']
        fun_test.log("Free memory before clearing cache {}".format(free_memory))
        # clear all the cache
        cmd = "echo 3 > /proc/sys/vm/drop_caches"
        self.handle.command(cmd)
        # get free memory after clearing cache
        free_memory_dictionary = self.handle.free(memory="m")
        free_memory = free_memory_dictionary['free']
        fun_test.log("Free memory after clearing cache {}".format(free_memory))

    def cleanup_everything(self):
        self.clear_iostat_mpstat_file()
        self.handle.kill_process(self.pid_dictionary["iostat"], kill_seconds=1)
        self.handle.kill_process(self.pid_dictionary["mpstat"], kill_seconds=1)

    def form_cores_allowed_list_numa(self):
        output = self.handle.lspci(grep_filter="-i mellanox")
        id = output[0]['id']
        output = self.handle.lspci(slot=id, verbose=True)
        numa_node = output[0]['numa_node']
        try:
            lscpu_dictionary = self.handle.lscpu(grep_filter="node{}".format(numa_node))
            num_cores_data = lscpu_dictionary.values()
            numbers_list = re.findall(r'[0-9]+', num_cores_data)
            numbers_list_int = map(int, numbers_list)
            len_num = len(numbers_list_int)
            cores_allowed_list = []
            for index in range(0, len_num, 2):
                cores_allowed_list += range(numbers_list_int[index], numbers_list_int[index+1]+1)
            cores_allowed_list = map(str, cores_allowed_list)
            return cores_allowed_list
        except:
            fun_test.critical("NUMA node CPU(s) data not obtained")
            return False

    def form_cores_allowed_list(self):
        number_of_cores_present = self.handle.get_number_cpus()
        cores_allowed_list = map(str, range(1, number_of_cores_present))
        fun_test.log("Cores allowed list : {}".format(cores_allowed_list))
        return cores_allowed_list
