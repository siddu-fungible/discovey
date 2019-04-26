from lib.system.fun_test import *
import re
from datetime import datetime

'''
Script to find the best performance numbers 
'''


class FioPerfHelper(object):
    def __init__(self, handle, fio_testfile_size, dpc_conntroller, num_jobs=1, iodepth=1,
                 num_cores=1, fio_rwmode='read',
                 nvme_device_name='/dev/nvme0n1', fio_test_runtime=20,
                 cpu_usage_limit=99, iowait_limit=0, iostat_skip_lines=6):

        self.handle = handle
        self.dpc_conntroller = dpc_conntroller
        self.fio_testfile_size = fio_testfile_size
        self.nvme_device_name = nvme_device_name
        self.fio_rwmode = fio_rwmode
        self.fio_test_runtime = fio_test_runtime
        self.num_jobs = num_jobs
        self.iodepth = iodepth
        self.num_cores = num_cores
        # Threshold values
        self.cpu_usage_limit = cpu_usage_limit
        self.iowait_limit = iowait_limit
        self.iostat_skip_lines = iostat_skip_lines

    def convert_to_comma(self, number, start=1):
        numbers_list = map(str, range(start, number + start))
        comma_format = ','.join(numbers_list)
        return comma_format

    def start_iostat_in_background(self):
        '''
        Starts storing the iostat results in a file
        '''
        fun_test.debug("Starting iostat in background")
        iostat_device = self.nvme_device_name[5:]
        cmd = "iostat -d %s 1" % (iostat_device)
        pid = self.handle.start_bg_process(command=cmd, output_file="iostat.txt", timeout=self.fio_test_runtime * 2)
        # Try to get the pid number of the process
        try:
            fun_test.debug("Pid of iostat : {}".format(pid))
            self.pid_dictionary["iostat"] = pid
        except:
            fun_test.critical("Unable to fetch the pid of iostat")

    def start_mpstat_in_background(self, start=1):
        '''
        Start storing mpstat results in the file
        '''
        number_of_cores = self.present_result["num_cores"]
        fun_test.debug("Starting the mpstat in background")
        num_cores_str_format = self.convert_to_comma(number_of_cores, start)
        cmd = "mpstat -P %s 1" % (num_cores_str_format)
        pid = self.handle.start_bg_process(command=cmd, output_file="mpstat.txt", timeout=self.fio_test_runtime * 2)

        # Try to get the pid number of the process
        try:
            fun_test.debug("Pid of mpstat : {}".format(pid))
            self.pid_dictionary["mpstat"] = pid
        except:
            fun_test.critical("Unable to fetch the pid of mpstat")

    def run_fio_command(self):
        '''
        Runs the fio command using the given credentials
        '''
        cores_str_format = self.convert_to_comma(self.present_result["num_cores"])
        fun_test.debug("Cpus allowed are : {}".format(cores_str_format))
        fun_test.log_section("\n\nStarting traffic")
        fun_test.log("\nStarting Fio with "
                     "\nNumber of jobs  : %s "
                     "\nIodepth         : %s "
                     "\nNumber of cores : %s"
                     "\nFio mode        : %s" %
                     (self.present_result["num_jobs"],
                      self.present_result["iodepth"],
                      self.present_result["num_cores"],
                      self.fio_rwmode))
        self.handle.pcie_fio(filename=self.nvme_device_name,
                             size=self.fio_testfile_size,
                             bs="4k",
                             rw=self.fio_rwmode,
                             iodepth=self.present_result["iodepth"],
                             numjobs=self.present_result["num_jobs"],
                             name="pci_fio_test",
                             group_reporting=1,
                             prio=0,
                             direct=1,
                             ioengine="libaio",
                             runtime=self.fio_test_runtime,
                             time_based=1,
                             cpus_allowed=cores_str_format,
                             timeout=self.fio_test_runtime * 2
                             )

    def kill_process(self, process_name):
        '''
        Kills mainly the iostat and mpstat process which were started before fio run in background
        '''
        # assert self.pid_dictionary, "No backgruond processess are running"
        fun_test.debug("Killing {}".format(process_name))
        try:
            pid_of_process = self.pid_dictionary[process_name]
            cmd = "kill -9 {}".format(pid_of_process)
            self.handle.command(cmd)
        except Exception as ex:
            fun_test.critical(ex)

    def parse_iostat_file(self):
        '''
        From the iostat.txt file grep the values and finds average and max values[like tps(IOPS) and Kb read/s]
        '''
        fun_test.debug("Parsing Iostat.txt")
        iostat_device = self.nvme_device_name[5:]
        tps_list = []
        kb_read_list = []
        dictionary = {}
        self.iostat_list = []
        # grep only the lines with nvme device name
        cmd = "cat iostat.txt | grep {}".format(iostat_device)
        # cmd = "cat iostat.txt"
        output = self.handle.command(cmd)
        fun_test.debug("Iostat has finished\nIOSTAT output")

        # split the output into list of lines
        lines_list = output.split('\n')

        # Avoid some starting and some end values to get proper result
        number_of_lines = len(lines_list)
        lines_list = lines_list[self.iostat_skip_lines:number_of_lines - 6]

        if lines_list == []:
            fun_test.critical("The iostat.txt file is NULL or output is too small")
            return
        tmp_dict = {}
        for line in lines_list:
            try:
                values_list = re.findall(r'(?<= )[0-9.]+', line)
                tps = float(values_list[0])
                kb_read = float(values_list[1])
                if tps > 0:
                    tps_list.append(tps)
                    tmp_dict['tps'] = tps
                if kb_read > 0:
                    kb_read_list.append(kb_read)
                    tmp_dict['kb_read'] = kb_read
                self.iostat_list.append(tmp_dict.copy())
                fun_test.debug(tmp_dict)
            except:
                fun_test.log("Unable to parse this line : {}".format(line))

        try:
            average_tps = round(sum(tps_list) / float(len(tps_list)), 2)
            average_kbps_read = round(sum(kb_read_list) / len(kb_read_list), 2)
            max_tps = max(tps_list)
            max_kbread = max(kb_read_list)
            dictionary['average_tps'] = average_tps
            dictionary['average_kbr'] = average_kbps_read
            dictionary['max_tps'] = max_tps
            dictionary['max_kbr'] = max_kbread

            # save the results obtained in the dictionary
            self.present_result["average_tps"] = average_tps
            self.present_result["average_kbr"] = average_kbps_read
            self.present_result["maximum_tps"] = max_tps
            self.present_result['maximum_kbr'] = max_kbread

            fun_test.debug("Iostat result")
            fun_test.debug("Maximum \ntps : %s    Kb_read/s : %s " % (max_tps, max_kbread))
            fun_test.debug("Average \ntps : %s    Kb_read/s : %s " % (average_tps, average_kbps_read))
            fun_test.debug(dictionary)
            return dictionary
        except:
            fun_test.critical("Error in Parsing the iostat.txt file")

    def parse_mpstat_file(self):
        '''
        From the mpstat.txt file greps the cpu usage and iowait values
        '''
        fun_test.debug("Parsing Mpstat.txt")
        error_msg = self.present_result['error_msg']
        iowait_error = False
        cpu_error = False
        maximum_iowait = 0
        maximum_cpu_usage = 0
        self.mpstat_list = []

        fun_test.debug("MPSTAT output")
        cmd = "cat mpstat.txt"
        output = self.handle.command(cmd)

        # divided them into blocks
        cpu_block_list = output.split('CPU')

        # ignore some starting and ending blocks
        cpu_block_list = cpu_block_list[3:len(cpu_block_list) - 3]

        if cpu_block_list == []:
            fun_test.critical("Not enough output present to process")
            return

        for cpu_block in cpu_block_list:
            cpu_block_lines = cpu_block.split('\n')
            for index in range(self.present_result['num_cores']):
                try:
                    each_line = cpu_block_lines[index + 1]
                    # find all the values in mpstat output line
                    values_list = re.findall(r'(?<= )[0-9.]+', each_line)
                    if len(values_list) == 11:
                        tmp_dict = {}
                        core = int(values_list[0])
                        user_cpu_usage = float(values_list[1])
                        system_cpu_uage = float(values_list[3])
                        total_cpu_usage = round(user_cpu_usage + system_cpu_uage, 2)
                        iowait = float(values_list[4])
                        idle = float(values_list[10])
                        tmp_dict['core'] = core
                        tmp_dict['total_cpu_usage'] = total_cpu_usage
                        tmp_dict['iowait'] = iowait
                        tmp_dict['idle'] = idle
                        fun_test.debug(tmp_dict)
                        self.mpstat_list.append(tmp_dict.copy())
                        if iowait > self.iowait_limit:
                            error_msg = error_msg + "Iowait of core {} is {} [greater than {}]\n" \
                                .format(core, iowait, self.iowait_limit)
                            iowait_error = True

                        if total_cpu_usage > self.cpu_usage_limit:
                            error_msg = error_msg + "Cpu usage of core {} is {} [greater than {}]\n" \
                                .format(core, total_cpu_usage, self.cpu_usage_limit)
                            cpu_error = True

                        if total_cpu_usage > maximum_cpu_usage:
                            maximum_cpu_usage = total_cpu_usage

                        if iowait > maximum_iowait:
                            maximum_iowait = iowait
                except:
                    fun_test.critical("Unable to parse the Mpstat file")
                    return

        # store maximum cpu usage and iowait
        self.present_result["maximum_cpu_usage"] = maximum_cpu_usage
        self.present_result["maximum_iowait"] = maximum_iowait
        self.present_result["cpu_usage_error"] = cpu_error
        self.present_result["iowait_error"] = iowait_error

        fun_test.debug("Dictionary : {}".format(self.present_result))
        self.present_result["error_msg"] = error_msg
        if iowait_error or cpu_error:
            fun_test.log(error_msg)
        else:
            fun_test.debug("No errors were found")

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

    def execute_fio_and_grep_result(self):
        '''
        Runs the fio command and stores all the iostat and mpstat values during the fio run and
        :returns if the given conditions(example : iowait == 0 , cpu usage < 90%) are passed or not
        '''
        try:
            self.present_result = {}
            self.pid_dictionary = {}
            self.present_result['error_msg'] = ''

            self.present_result["num_jobs"] = self.num_jobs
            self.present_result["iodepth"] = self.iodepth
            self.present_result["num_cores"] = self.num_cores
            self.present_result["fio_rwmode"] = self.fio_rwmode
            self.present_result["fio_test_runtime"] = self.fio_test_runtime

            self.clear_iostat_mpstat_file()
            self.start_iostat_in_background()
            self.start_mpstat_in_background()
            eqm_before = self.get_eqm_number()
            self.present_result["eqm_before_fio"] = eqm_before
            self.run_fio_command()
            eqm_after = self.get_eqm_number()
            self.present_result["eqm_after_fio"] = eqm_after
            eqm_difference = abs(eqm_after - eqm_before)

            if eqm_difference >= 0 and eqm_difference <= 5:
                eqm_error = False
            else:
                eqm_error = True
                error_msg = "EQM difference is {}\n".format(eqm_difference)
                self.present_result['error_msg'] = self.present_result['error_msg'] + error_msg

            self.present_result["eqm_error"] = eqm_error
            self.present_result["eqm_difference"] = eqm_difference
            self.kill_process("iostat")
            self.kill_process("mpstat")
            self.parse_iostat_file()
            self.parse_mpstat_file()
            overall_result = "Passed"
            if eqm_error or self.present_result["iowait_error"] or self.present_result["cpu_usage_error"]:
                overall_result = "Failed"
            self.present_result["overall_result"] = overall_result
            self.overall_results_list.append(self.present_result)
            self.print_key_value_sorted(title="Result", dictionary=self.present_result)
        except:
            self.cleanup_everything()

    ''' Logic function design section '''

    ''' Logic iodepth '''

    def get_num_jobs_iodepth_num_cores(self):
        self.overall_results_list = []
        self.execute_fio_and_grep_result()
        self.best_result = self.present_result.copy()
        first = 0
        last = 0
        flag = True
        worked = True
        iodepth = self.present_result['iodepth']
        num_jobs = self.present_result['num_jobs']
        forced = False
        while True:
            condition = self.iodepth_condition()
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
            elif condition == 'values_are_low':
                forced = True

            if iodepth == last or iodepth == first and (worked):
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

            self.execute_fio_and_grep_result()

        self.print_the_overall_summary()
        self.cleanup_everything()
        if self.iodepth == 0:
            self.iodepth = 1
        return self.num_jobs, self.iodepth, self.num_cores

    def iodepth_condition(self):
        if (self.present_result["cpu_usage_error"] and not(self.present_result['iowait_error'] or
                                                           self.present_result['eqm_error'])):
            return "cpu_error"

        elif (self.present_result["overall_result"] == "Passed" and
              self.best_result["maximum_tps"] <= self.present_result["maximum_kbr"] and
              self.best_result['maximum_kbr'] <= self.present_result['maximum_kbr']):
            self.best_result = self.present_result.copy()
            return 'working'
        elif (self.present_result["overall_result"] == "Passed" and
              self.best_result["maximum_tps"] >= self.present_result["maximum_kbr"] and
              self.best_result['maximum_kbr'] >= self.present_result['maximum_kbr']):
            return 'values_are_low'
        else:
            return "not_working"

    '''  Logic MMAP  '''

    def get_num_jobs_num_cores(self):
        self.cpu_usage_limit = 99
        self.iowait_limit = 99

        self.overall_results_list = []
        # initially run once with the results obtained and
        self.execute_fio_and_grep_result()
        self.best_result = self.present_result.copy()
        while True:
            self.print_key_value_sorted(title="Previous result", dictionary=self.best_result)
            condition = self.num_jobs_condition()

            if condition == "working":
                self.num_jobs = self.num_jobs * 2
                self.num_cores = self.num_cores * 2
                self.limit_number_of_cores()
                self.execute_fio_and_grep_result()
            elif condition == "not_working":
                break

        start = int(self.num_jobs / 2)
        end = self.num_jobs
        self.num_jobs = int((start + end) / 2)
        self.num_cores = self.num_jobs
        self.limit_number_of_cores()

        if start == 0 or start == 1:
            self.num_jobs = 1
            self.num_cores = 1
            fun_test.log("Error iodepth, failed at too low values")
            self.print_the_overall_summary()
            return self.num_jobs, self.iodepth, self.num_cores

        while True:
            self.execute_fio_and_grep_result()
            self.print_key_value_sorted(title="Previous result", dictionary=self.best_result)
            condition = self.num_jobs_condition()

            if condition == 'working':
                start = self.num_jobs
            elif condition == 'not_working':
                end = self.num_jobs
            self.num_jobs = int((start + end) / 2)
            self.num_cores = self.num_jobs
            self.limit_number_of_cores()
            if end == self.num_jobs or start == self.num_jobs:
                self.print_the_overall_summary()
                return self.num_jobs, self.iodepth, self.num_cores

    def num_jobs_condition(self):
        if (self.present_result["overall_result"] == "Passed" and
                self.best_result["maximum_tps"] <= self.present_result["maximum_kbr"] and
                self.best_result['maximum_kbr'] <= self.present_result['maximum_kbr']):
            self.best_result = self.present_result.copy()
            return 'working'
        else:
            return 'not_working'

    def start_iostat_process(self, num_jobs, iodepth, num_cores, fio_rwmode='read',
                             fio_test_runtime=60):
        self.present_result = {}
        self.pid_dictionary = {}
        self.present_result['error_msg'] = ''
        self.iostat_skip_lines = 10

        self.present_result["num_jobs"] = num_jobs
        self.present_result["iodepth"] = iodepth
        self.present_result["num_cores"] = num_cores
        self.present_result["fio_rwmode"] = fio_rwmode
        self.present_result["fio_test_runtime"] = fio_test_runtime

        self.clear_iostat_mpstat_file()
        self.start_iostat_in_background()
        self.start_mpstat_in_background()
        eqm_before = self.get_eqm_number()
        self.present_result["eqm_before_fio"] = eqm_before
        self.fio_start_time = datetime.utcnow()

    def end_iostat_process(self):
        eqm_after = self.get_eqm_number()
        self.present_result["eqm_after_fio"] = eqm_after
        eqm_difference = self.present_result['eqm_before_fio'] - eqm_after

        if eqm_difference >= 0 and eqm_difference <= 5:
            eqm_error = False
        else:
            eqm_error = True
            error_msg = "EQM difference is {}\n".format(eqm_difference)
            self.present_result['error_msg'] = self.present_result['error_msg'] + error_msg
        self.kill_process("iostat")
        self.kill_process("mpstat")
        self.present_result["eqm_error"] = eqm_error
        self.present_result["eqm_difference"] = eqm_difference
        self.parse_iostat_file()
        self.parse_mpstat_file()
        overall_result = "Passed"
        if eqm_error or self.present_result["iowait_error"] or self.present_result["cpu_usage_error"]:
            overall_result = "Failed"
        self.present_result["overall_result"] = overall_result
        # self.overall_results_list.append(self.present_result)
        self.print_key_value_sorted(title="Fio Result", dictionary=self.present_result)
        fun_test.debug("Iostat list : {}".format(self.iostat_list))
        fun_test.debug("Mpstat list : {}".format(self.mpstat_list))
        self.cleanup_everything()
        return self.present_result

    '''Helper functions'''

    def clear_iostat_mpstat_file(self):
        '''
        Clears all the data in iostat and mpstat
        Note: Very important otherwise may result in errors
        '''
        cmd = " > iostat.txt"
        self.handle.command(cmd)
        cmd = " > mpstat.txt"
        self.handle.command(cmd)
        cmd = "rm -r iostat.txt;rm -r mpstat.txt"
        self.handle.command(cmd)
        self.handle.command("ls")
        time.sleep(4)
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
        cmd = "nproc --all"
        output = self.handle.command(cmd)
        number_of_cores_present = int(output)
        if self.num_cores > (number_of_cores_present - 1):
            self.num_cores = number_of_cores_present - 1

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
        use_this = "{:<" + str(spacing) + "}{}"
        for key in order_of_print:
            fun_test.log(use_this.format(key, dictionary[key]))

    def set_iostat_skip_lines(self, skip_lines):
        '''
        Skips the first n lines of the iostat.txt file
        '''
        self.iostat_skip_lines = skip_lines

    def get_the_free_memory(self):
        '''
        Execute the free -m command and grep the free space and return
        '''
        cmd = "free -m"
        output = self.handle.command(cmd)
        split_into_lines = output.split('\n')
        for line in split_into_lines:
            try:
                values_list = re.findall(r'(?<= )[0-9]+', line)
                if len(values_list) == 6:
                    free_space = int(values_list[2])
                    return free_space
            except:
                fun_test.critical("Unable to feth the free space")

    def clear_the_cache(self):
        # get free memory before clearing cache
        free_memory = self.get_the_free_memory()
        fun_test.log("Free memory before clearing cache {}".format(free_memory))
        # clear all the cache
        self.handle.command()

    def cleanup_everything(self):
        self.clear_iostat_mpstat_file()
        self.kill_process("iostat")
        self.kill_process("mpstat")
