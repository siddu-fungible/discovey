import sys
import os
import traceback
import collections
import abc
import pdb
import inspect
from fun_settings import *
import fun_xml
import argparse
import threading
from fun_global import RESULTS, get_current_time, determine_version, get_localized_time
from scheduler.scheduler_helper import *
import signal
from web.fun_test.web_interface import get_homepage_url
import pexpect
from uuid import getnode as get_mac
from uuid import uuid4
import getpass
from threading import Thread
from inspect import getargspec


class TestException(Exception):
    def __str__(self):
        return self.message

    def __add__(self, other):
        return str(self) + str(other)


class FunTestSystemException(Exception):
    pass


class FunTestLibException(Exception):
    pass


class FunTimer:
    def __init__(self, max_time=10000):
        self.max_time = max_time
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def is_expired(self):
        return (self.elapsed_time()) > self.max_time

    def elapsed_time(self):
        current_time = time.time()
        return current_time - self.start_time


class FunTestThread(Thread):
    def __init__(self, func, **kwargs):
        super(FunTestThread, self).__init__()
        self.func = func
        self.kwargs = kwargs

    def run(self):
        i = getargspec(self.func)
        if i.args:
            self.func(**self.kwargs)
        else:
            self.func()


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)

class FunTest:
    PASSED = RESULTS["PASSED"]
    FAILED = RESULTS["FAILED"]
    SKIPPED = RESULTS["SKIPPED"]
    NOT_RUN = RESULTS["NOT_RUN"]
    IN_PROGRESS = RESULTS["IN_PROGRESS"]

    LOG_LEVEL_DEBUG = 0
    LOG_LEVEL_CRITICAL = 1
    LOG_LEVEL_NORMAL = 2
    SETUP_TC_ID = 0
    CLEANUP_TC_ID = 999

    MODE_REAL = 1
    MODE_SIMULATION = 2
    MODE_EMULATION = 3

    LOG_COLORS = {
        LOG_LEVEL_DEBUG: '\033[94m',
        LOG_LEVEL_CRITICAL: '\033[91m',
        LOG_LEVEL_NORMAL: '',
        "RESET": '\033[0m',
        "GREEN": '\033[92m'
    }


    fun_test_thread_id = 0

    def __init__(self):
        if "DISABLE_FUN_TEST" in os.environ:
            def black_hole(*args, **kwargs):
                pass
            self.log = black_hole
            return
        parser = argparse.ArgumentParser(description="FunTest")
        parser.add_argument('--logs_dir',
                            dest="logs_dir",
                            default=None,
                            help="To be used only by the scheduler")
        parser.add_argument('--log_prefix',
                            dest="log_prefix",
                            default=None,
                            help="To be used only by the scheduler")
        parser.add_argument('--suite_execution_id',
                            dest="suite_execution_id",
                            default=None,
                            help="To be used only by the scheduler")
        parser.add_argument('--relative_path',
                            dest="relative_path",
                            default="",
                            help="To be used only by the scheduler")
        parser.add_argument('--test_case_ids',
                            dest="test_case_ids",
                            default=None,
                            help="To be used only by the scheduler")
        parser.add_argument('--build_url',
                            dest="build_url",
                            default=None,
                            help="To be used only by the scheduler")
        parser.add_argument('--disable_fun_test',
                            dest="disable_fun_test",
                            default=None)
        parser.add_argument('--local_settings_file',
                            dest="local_settings_file",
                            default=None)
        parser.add_argument('--environment', dest="environment", default=None)
        parser.add_argument('--inputs', dest="inputs", default=None)
        parser.add_argument('--re_run_info', dest="re_run_info", default=None)
        args = parser.parse_args()
        if args.disable_fun_test:
            self.fun_test_disabled = True
            return
        else:
            self.fun_test_disabled = False
        self.logs_dir = args.logs_dir
        self.log_prefix = args.log_prefix
        self.suite_execution_id = args.suite_execution_id
        self.relative_path = args.relative_path
        self.selected_test_case_ids = None
        self.current_test_case_execution_id = None
        self.build_url = args.build_url
        self.local_settings_file = args.local_settings_file
        self.abort_requested = False
        self.environment = args.environment
        self.inputs = args.inputs
        self.re_run_info = args.re_run_info
        self.local_settings = {}
        if self.suite_execution_id:
            self.suite_execution_id = int(self.suite_execution_id)

        print("Suite Execution Id: {}".format(self.get_suite_execution_id()))

        if args.test_case_ids:
            self.selected_test_case_ids = [int(x) for x in args.test_case_ids.split(",")]
        re_run_info = self.get_re_run_info()
        if re_run_info:
            self.selected_test_case_ids = [int(x) for x in re_run_info.keys()]
            # print("***" + str(self.selected_test_case_ids))
        if not self.logs_dir:
            self.logs_dir = LOGS_DIR
        (frame, file_name, line_number, function_name, lines, index) = \
            inspect.getouterframes(inspect.currentframe())[2]

        self.original_sig_int_handler = None
        if threading.current_thread().__class__.__name__ == '_MainThread':
            self.original_sig_int_handler = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, self.exit_gracefully)

        self.initialized = False
        self.debug_enabled = False
        self.function_tracing_enabled = False
        self.buf = None
        self.current_test_case_id = None
        self.traces = {}

        self.absolute_script_file_name = file_name
        self.script_file_name = os.path.basename(self.absolute_script_file_name)
        script_file_name_without_extension = self.script_file_name.replace(".py", "")

        self.test_metrics = collections.OrderedDict()

        html_log_file = "{}.html".format(script_file_name_without_extension)
        if self.relative_path:
            html_log_file = get_flat_html_log_file_name(self.relative_path, self.log_prefix)
            # if self.log_prefix:
            #    html_log_file = "{}_{}".format(self.log_prefix, html_log_file)
        self.html_log_file = html_log_file

        self.fun_xml_obj = fun_xml.FunXml(script_name=script_file_name_without_extension,
                                          log_directory=self.logs_dir,
                                          log_file=html_log_file,
                                          full_script_path=self.absolute_script_file_name)
        reload(sys)
        sys.setdefaultencoding('UTF8')  # Needed for xml
        self.counter = 0  # Mostly used for testing
        self.logging_selected_modules = []
        self.log_timestamps = True
        self.log_function_name = False
        self.pause_on_failure = False
        self.shared_variables = {}
        if self.local_settings_file:
            self.local_settings = self.parse_file_to_json(file_name=self.local_settings_file)
        self.start_time = get_current_time()
        self.wall_clock_timer = FunTimer()
        self.wall_clock_timer.start()
        self.fun_test_threads = {}
        self.fun_test_timers = []
        self.version = "1"
        self.determine_version()
        self.asset_manager = None
        self.closed = False


    def abort(self):
        self.abort_requested = True

    def get_start_time(self):
        return self.start_time

    def get_job_environment(self):
        result = {}
        if self.environment:
            result = self.parse_string_to_json(self.environment)
        return result

    def get_job_environment_variable(self, variable):
        result = None
        job_environment = self.get_job_environment()
        if variable in job_environment:
            result = job_environment[variable]
        return result

    def is_simulation(self):
        result = True
        test_bed_type = self.get_job_environment_variable(variable="test_bed_type")
        if test_bed_type and test_bed_type != "simulation":
            result = False
        return result

    def get_job_inputs(self):
        result = None
        if self.inputs:
            result = self.parse_string_to_json(self.inputs)
        return result

    def get_re_run_info(self):
        result = None
        if self.re_run_info:
            result = self.parse_string_to_json(self.re_run_info)
        return result

    def get_local_setting(self, setting):
        result = None
        if self.local_settings and setting in self.local_settings:
            result = self.local_settings[setting]
        return result

    def determine_version(self):
        print("Determining version...")
        determined_version = determine_version(build_url=DEFAULT_BUILD_URL)
        if determined_version:
            self.version = determined_version
        else:
            print("Unable to determine the version. Defaulting...")
        print ("Version: {}".format(self.version))

    def set_version(self, version):
        self.version = version

    def get_version(self):
        return self.version

    def _get_next_thread_id(self):
        self.fun_test_thread_id += 1
        return self.fun_test_thread_id

    def execute_after(self, time_in_seconds, func, **kwargs):
        next_id = self._get_next_thread_id()
        timer = threading.Timer(time_in_seconds, self._process_timer, [next_id])
        self.fun_test_timers.append(timer)
        self.fun_test_threads[next_id] = {
            "function": func,
            "kwargs": kwargs,
            "thread": None,
            "as_thread": False,
            "timer": timer
        }
        timer.start()
        return next_id

    def execute_thread_after(self, time_in_seconds, func, **kwargs):
        next_id = self._get_next_thread_id()
        timer = threading.Timer(time_in_seconds, self._process_timer, [next_id])
        self.fun_test_timers.append(timer)
        self.fun_test_threads[next_id] = {
            "function": func,
            "kwargs": kwargs,
            "as_thread": True,
            "thread": None,
            "timer": timer
        }
        timer.start()
        return next_id

    def _process_timer(self, thread_id):
        thread_info = self.fun_test_threads[thread_id]
        func = thread_info["function"]
        kwargs = thread_info["kwargs"]
        as_thread = thread_info["as_thread"]
        if as_thread:
            t = FunTestThread(func, **kwargs)
            thread_info["thread"] = t
            t.start()
        else:
            func(**kwargs)

    def join_thread(self, fun_test_thread_id, sleep_time=5):
        thread_complete = False
        while not thread_complete:
            thread_info = self.fun_test_threads[fun_test_thread_id]
            thread = thread_info["thread"]
            if thread:
                if not thread_complete:
                    try:
                        thread.join()

                    except RuntimeError as r:
                        r_string = str(r)
                        if "cannot join thread before it is started" not in r_string:
                            fun_test.critical("Thread-id: {} Runtime error. {}".format(fun_test_thread_id, r))
                        else:
                            fun_test.sleep(message="Thread-id: {} Waiting for thread to start".format(fun_test_thread_id),
                                           seconds=sleep_time)
                    thread_complete = True
            else:
                fun_test.log("Thread-id: {} has probably not started. Checking if timer should be complete first".format(fun_test_thread_id))
                timer = thread_info["timer"]
                while timer.isAlive():
                    fun_test.sleep(message="Timer is still alive", seconds=sleep_time)
                if not thread_info["as_thread"]:
                    thread_complete = True

        fun_test.log("Join complete for Thread-id: {}".format(fun_test_thread_id))
        return True

    def get_asset_manager(self):
        from asset.asset_manager import AssetManager
        if not self.asset_manager:
            self.asset_manager = AssetManager()
        return self.asset_manager

    def parse_string_to_json(self, string):
        result = None
        try:
            result = json.loads(string)
        except Exception as ex:
            raise Exception("{} has an invalid json format".format(string))
        return result

    def parse_file_to_json(self, file_name):
        result = None
        if os.path.exists(file_name):
            with open(file_name, "r") as infile:
                contents = infile.read()
                result = self.parse_string_to_json(contents)
        else:
            raise Exception("{} path does not exist".format(file_name))
        return result

    def get_wall_clock_time(self):
        return self.wall_clock_timer.elapsed_time()

    def get_absolute_script_path(self):
        return self.absolute_script_file_name

    def get_script_name_without_ext(self):
        return os.path.splitext(self.absolute_script_file_name)[0]

    def get_script_parent_directory(self):
        current_directory = os.path.abspath(os.path.join(self.get_absolute_script_path(), os.pardir))
        return current_directory

    def set_log_format(self, timestamp="UNCHANGED", function_name="UNCHANGED"):
        if timestamp != "UNCHANGED":
            self.log_timestamps = timestamp
        if function_name != "UNCHANGED":
            self.log_function_name = function_name

    def create_test_case_artifact_file(self, contents, post_fix_name=None, artifact_file=None):
        if not artifact_file:
            artifact_file = self.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        with open(artifact_file, "w") as f:
            f.write(contents)
        return os.path.basename(artifact_file)

    def get_test_case_artifact_file_name(self, post_fix_name):
        log_prefix = ""
        if self.log_prefix:
            log_prefix = "_{}".format(self.log_prefix)
        artifact_file = self.logs_dir + "/" + log_prefix + self.script_file_name + "_" + str(self.get_suite_execution_id()) + "_" + str(self.get_test_case_execution_id()) + "_" + post_fix_name
        return artifact_file

    def enable_pause_on_failure(self):
        self.pause_on_failure = True

    def disable_pause_on_failure(self):
        self.pause_on_failure = False

    def set_topology_json_filename(self, filename):
        self.fun_xml_obj.set_topology_json_filename(filename=filename)

    def get_environment_variable(self, variable):
        result = None
        if variable in os.environ:
            result = os.environ[variable]
        return result

    def get_suite_execution_id(self):
        env_sid = self.get_environment_variable("SUITE_EXECUTION_ID")
        if env_sid:
            env_sid = int(env_sid)
        if not env_sid:
            env_sid = int(str(get_mac())[:4])
            env_sid += sum([ord(x) for x in getpass.getuser()])
        sid = self.suite_execution_id if self.suite_execution_id else env_sid
        return sid

    def get_test_case_execution_id(self):
        return self.current_test_case_execution_id if self.current_test_case_execution_id else 100

    def log_enable_timestamps(self):
        self.log_timestamps = True

    def log_disable_timestamps(self):
        self.log_timestamps = False

    def log_module_filter(self, module_name):
        self.logging_selected_modules.append(module_name.strip("*.py"))

    def log_module_filter_disable(self):
        self.logging_selected_modules = []

    def log_module_filters(self, module_names):
        self.logging_selected_modules.extend(module_names)

    def enable_debug(self):
        self.debug_enabled = True

    def disable_debug(self):
        self.debug_enabled = False

    def enable_function_tracing(self):
        self.function_tracing_enabled = True

    def disable_function_tracing(self):
        self.function_tracing_enabled = False

    def debug(self, message):
        if self.debug_enabled:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            calling_module = self._get_calling_module(outer_frames)
            self.log(message=message, level=self.LOG_LEVEL_DEBUG, calling_module=calling_module)

    def critical(self, message):
        message = str(message)
        exc_type, exc_value, exc_traceback = sys.exc_info()

        tb = traceback.format_tb(exc_traceback)
        outer_frames = inspect.getouterframes(inspect.currentframe())
        calling_module = self._get_calling_module(outer_frames)
        self.log(message=message, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module)

        if exc_traceback:
            self.log(message="***** Last Exception At *****", level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module)
            last_exception_s = "".join(tb)
            self.log(message=last_exception_s, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module)
        traceback_stack = traceback.format_stack()
        if traceback_stack:
            asserts_present = None
            s2 = list(traceback_stack)
            s2.reverse()
            for index, l in enumerate(s2):

                one_assert_found = None
                for m in ["in test_assert", "in test_assert_expected", "in simple_assert"]:
                    if m in l:
                        asserts_present = True
                        one_assert_found = True
                        break
                if asserts_present and not one_assert_found:
                    assert_string = l
                    s2 = s2[: len(s2) - index]
                    self.log(message="ASSERT Raised by: {}".format(assert_string), level=self.LOG_LEVEL_CRITICAL)
                    break
            self.log(message="***** Traceback Stack *****", level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module)
            stack_s = "".join(traceback_stack[:-1])
            self.log(message=stack_s, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module)


    def _get_module_name(self, outer_frames):
        module_name = os.path.basename(outer_frames[0][1]).replace(".py", "")
        line_number = outer_frames[0][2]
        return (module_name, line_number)

    def _get_calling_module(self, outer_frames):
        module_info = None
        for f in outer_frames:
            if not f[1].endswith("fun_test.py"):
                function_name = f[0].f_code.co_name
                module_info = (os.path.basename(f[1]).replace(".py", ""), f[2], function_name)
                break
        return module_info

    def _is_selected_module(self, module_name):
        return module_name in self.logging_selected_modules

    def dict_to_json_string(self, d):
        return json.dumps(d, indent=4, cls=DatetimeEncoder)

    def log(self,
            message,
            level=LOG_LEVEL_NORMAL,
            newline=True,
            trace_id=None,
            stdout=True,
            calling_module=None,
            no_timestamp=False):
        current_time = get_current_time()
        if calling_module:
            module_name = calling_module[0]
            line_number = calling_module[1]
            function_name = calling_module[2]
        else:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            module_info = self._get_calling_module(outer_frames=outer_frames)
            module_name = module_info[0]
            line_number = module_info[1]
            function_name = module_info[2]

        message = str(message)
        if trace_id:
            self.trace(id=trace_id, log=message)

        if self.logging_selected_modules:
            if (not module_name == "fun_test") and not self._is_selected_module(module_name=module_name):
                return

        module_line_info = ""
        if level in [self.LOG_LEVEL_DEBUG, self.LOG_LEVEL_CRITICAL]:
            module_line_info = "{}.py:{}".format(module_name, line_number)
        if self.log_function_name:
            module_line_info += ":{}".format(function_name)

        self.fun_xml_obj.log(log=message, newline=newline)

        level_name = ""
        if level == self.LOG_LEVEL_CRITICAL:
            level_name = "CRITICAL: {}".format(module_line_info)
        elif level == self.LOG_LEVEL_DEBUG:
            level_name = "DEBUG: {}".format(module_line_info)
        if level is not self.LOG_LEVEL_NORMAL:
            message = "%s%s: %s%s" % (self.LOG_COLORS[level], level_name, message, self.LOG_COLORS['RESET'])

        if self.log_timestamps and (not no_timestamp):
            message = "[{}] {}".format(current_time, message)

        nl = ""
        if newline:
            nl = "\n"
        if stdout:
            sys.stdout.write(str(message) + nl)
            sys.stdout.flush()

    def print_key_value(self, title, data, max_chars_per_column=50):
        if title:
            self.log_section(title)
        for k, v in data.items():
            k = str(k)
            len_k = len(k)
            start = 0
            end = min(len_k, max_chars_per_column)
            while start < len_k:
                this_format = "{:<" + str(max_chars_per_column) + "} {}"
                this_k = k[start: end]
                if not start:
                    fun_test.log(this_format.format(this_k, v))
                else:
                    fun_test.log(this_format.format(this_k, ""))
                if len_k > max_chars_per_column:
                    start += min(len_k - start, max_chars_per_column)
                    end += min(len_k - end, max_chars_per_column)
                else:
                    break
        self.log("")

    def log_section(self, message):
        calling_module = None
        if self.logging_selected_modules:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            calling_module = self._get_calling_module(outer_frames=outer_frames)
        s = "\n{}\n{}\n".format(message, "=" * len(message))
        self.log(s, calling_module=calling_module)

    def write(self, message):
        self.buf = message

    def flush(self, trace_id=None, stdout=True):
        calling_module = None
        if self.logging_selected_modules:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            calling_module = self._get_calling_module(outer_frames=outer_frames)
        if trace_id:
            self.trace(id=trace_id, log=self.buf)
        self.log(self.buf, newline=False, stdout=stdout, calling_module=calling_module, no_timestamp=True)
        self.buf = ""

    def _print_log_green(self, message, calling_module=None):
        module_info = ""
        if calling_module:
            module_info = "{}.py: {}".format(calling_module[0], calling_module[1])
        message = "\n%s%s: %s %s%s" % (self.LOG_COLORS["GREEN"], "", module_info, message, self.LOG_COLORS['RESET'])

        sys.stdout.write(str(message) + "\n")
        sys.stdout.flush()

    def sleep(self, message, seconds=5):
        outer_frames = inspect.getouterframes(inspect.currentframe())
        calling_module = self._get_calling_module(outer_frames)
        self._print_log_green("zzz...: Sleeping for :" + str(seconds) + "s : " + message,
                              calling_module=calling_module)
        time.sleep(seconds)

    def safe(self, the_function):
        def inner(*args, **kwargs):
            if self.debug_enabled and self.function_tracing_enabled and (not self.fun_test_disabled):
                args_s = "args:" + ",".join([str(x) for x in args])
                args_s += " kwargs:" + ",".join([(k + ":" + str(v)) + " " for k, v in kwargs.items()])
                self.debug(args_s)
                return_value = None
                try:
                    return_value = the_function(*args, **kwargs)
                except Exception as ex:
                    self.critical(str(ex))

                self.debug("Return:" + str(return_value) + "End Return\n")
                return return_value
            else:
                return the_function(*args, **kwargs)
        return inner

    def _print_summary(self):
        self.log_section(message="Summary")
        format = "{:<4} {:<10} {:<100}"
        self.log(format.format("Id", "Result", "Description"), no_timestamp=True)
        for k, v in self.test_metrics.items():
            self.log(format.format(k, v["result"], v["summary"]), no_timestamp=True)

        self.log("{}{}/".format(get_homepage_url(), LOGS_RELATIVE_DIR) + self.script_file_name.replace(".py", ".html"),
                 no_timestamp=True)
        self.log("\nRuntime: {}".format(self.get_wall_clock_time()))

    def print_test_case_summary(self, test_case_id):
        metrics = self.test_metrics[test_case_id]
        assert_list = metrics["asserts"]
        self.log_section("Testcase {} summary".format(test_case_id))
        for assert_result in assert_list:
            self.log(assert_result, no_timestamp=True)

    def _initialize(self):
        if self.initialized:
            raise FunTestSystemException("FunTest obj initialized twice")
        self.initialized = True

    def close(self):
        for timer in self.fun_test_timers:
            fun_test.log("Waiting for active timers to stop")
            while timer.is_alive():
                time.sleep(1)

        threads_to_check = []
        for fun_test_thread_id, thread_info in self.fun_test_threads.iteritems():
            thread = thread_info["thread"]
            if thread and thread.isAlive():
                threads_to_check.append(thread)
        if threads_to_check:
            fun_test.log("Joining pending threads")
            for thread_to_check in threads_to_check:
                thread_to_check.join()
        self._print_summary()
        self.closed = True

    def _get_test_case_text(self,
                            id,
                            summary,
                            steps="None",
                            traffic="None"):

        s = "Id:" + str(id)
        s += " " + summary + "\n"
        s += "------" + "\n"
        if steps:
            s += "Steps:" + "\n"
            s += "==================" + "\n"
            s += steps + "\n"
            s += "\n"

        return s

    def add_table(self, panel_header, table_name, table_data):
        self.fun_xml_obj.add_collapsible_tab_panel_tables(header=panel_header,
                                                          panel_items={table_name: table_data})

    def _add_xml_trace(self):
        if self.current_test_case_id in self.traces:
            trace_items = self.traces[self.current_test_case_id]
            self.fun_xml_obj.add_collapsible_tab_panel(header="Traces", panel_items=trace_items)

    def trace(self, id, log):
        if self.current_test_case_id not in self.traces:
            self.traces[self.current_test_case_id] = {}
        if id not in self.traces[self.current_test_case_id]:
            self.traces[self.current_test_case_id][id] = log
        self.traces[self.current_test_case_id][id] += log

    def set_suite_execution_banner(self, banner):
        if fun_test.suite_execution_id:
            models_helper.set_suite_execution_banner(suite_execution_id=self.suite_execution_id, banner=banner)

    def get_suite_execution_banner(self):
        return models_helper.get_suite_execution_banner(suite_execution_id=self.suite_execution_id)

    def _start_test(self, id, summary, steps):
        self.fun_xml_obj.start_test(id=id, summary=summary, steps=steps)
        self.fun_xml_obj.set_long_summary(long_summary=self._get_test_case_text(id=id,
                                                                                summary=summary,
                                                                                steps=steps))
        self.log_section("Testcase: Id: {} Description: {}".format(id, summary))
        self.test_metrics[id] = {"summary": summary,
                                 "steps": steps,
                                 "result": FunTest.FAILED}
        self.current_test_case_id = id
        self.test_metrics[self.current_test_case_id]["asserts"] = []

    def _end_test(self, result):
        self.fun_xml_obj.end_test(result=result)
        self.test_metrics[self.current_test_case_id]["result"] = result

    def _append_assert_test_metric(self, assert_message):
        if self.current_test_case_id in self.test_metrics:
            self.test_metrics[self.current_test_case_id]["asserts"].append(assert_message)

    def test_assert(self, expression, message, ignore_on_success=False):
        actual = True
        if not expression:
            actual = False
        self.test_assert_expected(expected=True,
                                  actual=actual,
                                  message=message,
                                  ignore_on_success=ignore_on_success)

    def simple_assert(self, expression, message):
        self.test_assert(expression=expression, message=message, ignore_on_success=True)

    def test_assert_expected(self, expected, actual, message, ignore_on_success=False):
        if not ((type(actual) is dict) and (type(expected) is dict)):
            expected = str(expected)
            actual = str(actual)
        assert_message = "ASSERT PASSED: expected={} actual={}, {}".format(expected, actual, message)
        if not expected == actual:
            assert_message = "ASSERT FAILED: expected={} actual={}, {}".format(expected, actual, message)
            self._append_assert_test_metric(assert_message)
            self.fun_xml_obj.add_checkpoint(checkpoint=message,
                                            expected=expected,
                                            actual=actual,
                                            result=FunTest.FAILED)
            self.critical(assert_message)
            if self.pause_on_failure:
                pdb.set_trace()
            raise TestException(assert_message)
        if not ignore_on_success:
            self.log(assert_message)
            self._append_assert_test_metric(assert_message)

            self.fun_xml_obj.add_checkpoint(checkpoint=message,
                                            expected=expected,
                                            actual=actual,
                                            result=FunTest.PASSED)

    def add_checkpoint(self,
                       checkpoint=None,
                       result=PASSED,
                       expected="",
                       actual=""):

        self.fun_xml_obj.add_checkpoint(checkpoint=checkpoint, result=result, expected=expected, actual=actual)

    def exit_gracefully(self, sig, _):
        fun_test.critical("Unexpected Exit")

        if fun_test.suite_execution_id:
            models_helper.update_test_case_execution(test_case_execution_id=fun_test.current_test_case_execution_id,
                                                     suite_execution_id=fun_test.suite_execution_id,
                                                     result=fun_test.FAILED)
            signal.signal(signal.SIGINT, self.original_sig_int_handler)
        sys.exit(-1)

    def _get_flat_file_name(self, path):
        parts = path.split("/")
        flat = path
        if len(parts) > 2:
            flat = "_".join(parts[-2:])
        return flat.lstrip("/")

    def _is_sub_class(self, base_class, mros):
        result = None
        for mro in mros[1:]:
            if base_class in str(mro):
                result = True
                break
        return result

    def inspect(self, module_name):
        def _is_sub_class(base_class, mros):
            result = None
            for mro in mros[1:]:
                if base_class in str(mro):
                    result = True
                    break
            return result
        result = {}
        result["classes"] = []
        sys.argv.append("--disable_fun_test")
        fun_test.absolute_script_file_name = module_name
        test_cases = []

        import imp
        import inspect
        f, filename, description = imp.find_module(os.path.basename(module_name).replace(".py", ""),
                                                   [os.path.dirname(module_name)])
        flat_base_name = os.path.basename(module_name).replace(".", "_")
        loaded_module_name = "dynamic_load" + flat_base_name
        imp.load_module(loaded_module_name, f, filename, description)

        members = inspect.getmembers(sys.modules[loaded_module_name], inspect.isclass)
        for m in members:
            if len(m) > 1:
                klass = m[1]
                mros = inspect.getmro(klass)
                if len(mros) > 1 and _is_sub_class(base_class="lib.system.fun_test.FunTestCase", mros=mros):
                    # print klass
                    try:
                        o = klass()
                        o.describe()
                        result["classes"].append({"name": o.__class__.__name__, "summary": o.summary, "id": o.id})
                        test_cases.append(klass)
                    except Exception as ex:
                        pass
                    # print o.id
                    # print o.summary
                    # print o.steps

                if len(mros) > 1 and _is_sub_class(base_class="lib.system.fun_test.FunTestScript", mros=mros):
                    test_script = klass
        # test_script_obj = test_script()
        # test_case_order = test_script().test_case_order
        '''
        for entry in test_script().test_case_order:
            print entry["tc"]
        '''
        return result

    def add_auxillary_file(self, description, filename):
        base_name = os.path.basename(filename)
        self.fun_xml_obj.add_auxillary_file(description=description, auxillary_file=base_name)

    def scp(self,
            source_file_path,
            target_file_path,
            source_ip=None,
            source_username=None,
            source_password=None,
            source_port=22,
            target_ip=None,
            target_username=None,
            target_password=None,
            target_port=22,
            timeout=60,
            recursive=False):
        transfer_complete = False
        scp_command = ""
        recursive = " -r " if recursive else ""
        # scp_command = "scp -P %d %s %s@%s:%s" % (
        # target_port, source_file_path, target_username, target_ip, target_file_path)
        the_password = source_password
        if target_ip:
            scp_command = "scp {} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P {} {} {}@{}:{}".format(recursive,
                                                                                            target_port,
                                                                                            source_file_path,
                                                                                            target_username,
                                                                                            target_ip,
                                                                                            target_file_path)
            the_password = target_password
        elif source_ip:
            scp_command = "scp {} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P {} {}@{}:{} {}".format(recursive, source_port,
                                                                                            source_username,
                                                                                            source_ip,
                                                                                            source_file_path,
                                                                                            target_file_path)

        if target_ip and source_ip:
            scp_command = "scp {} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P {} {}@{}:{} {}@{}:{}".format(recursive,
                                                                                            source_port,
                                                                                            source_username,
                                                                                            source_ip,
                                                                                            source_file_path,
                                                                                            target_username,
                                                                                            target_ip,
                                                                                            target_file_path)

        handle = pexpect.spawn(scp_command, env={"TERM": "dumb"}, maxread=4096)
        handle.logfile_read = fun_test
        handle.sendline(scp_command)

        expects = collections.OrderedDict()
        expects[0] = '[pP]assword:'
        expects[1] = r'\$ ' + r'$'
        expects[2] = '\(yes/no\)?'

        max_retry_count = 10
        max_loop_count = 10

        attempt = 0
        source_password_sent = False
        try:
            while attempt < max_retry_count and not transfer_complete:
                current_loop_count = 0
                while current_loop_count < max_loop_count:
                    try:
                        i = handle.expect(expects.values(), timeout=timeout)
                        if i == 0:
                            if target_ip and source_ip:  # Remote to remote scp
                                if not source_password_sent:
                                    the_password = source_password
                                    source_password_sent = True
                                else:
                                    the_password = target_password
                            fun_test.debug("Sending: %s" % the_password)
                            handle.sendline(the_password)
                            current_loop_count += 1
                        if i == 2:
                            fun_test.debug("Sending: %s" % "yes")
                            handle.sendline("yes")
                            current_loop_count += 1
                        if i == 1:
                            transfer_complete = True
                            break
                    except pexpect.exceptions.EOF:
                        transfer_complete = True
                        break
        except Exception as ex:
            critical_str = str(ex)
            self.critical(critical_str)

        return transfer_complete

    def get_temp_file_name(self):
        return str(uuid4())

    def get_temp_file_path(self, file_name):
        full_path = SYSTEM_TMP_DIR + "/" + file_name
        return full_path

    def remove_file(self, file_path):
        os.remove(file_path)
        return True

    def get_helper_dir_path(self):
        return self.get_script_parent_directory() + "/helper"

    def get_suite_execution_tags(self):
        tags = []
        suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
        if suite_execution:
            tags = json.loads(suite_execution.tags)
        return tags

fun_test = FunTest()


class FunTestScript(object):
    __metaclass__ = abc.ABCMeta
    test_case_order = None

    def __init__(self):
        fun_test._initialize()
        self.test_cases = []
        self.summary = "Setup"
        self.steps = ""
        self.at_least_one_failed = False

    def set_test_details(self, steps):
        self.id = FunTest.SETUP_TC_ID
        self.steps = steps

    def add_test_case(self, test_case):
        self.test_cases.append(test_case)
        return self

    @abc.abstractmethod
    def describe(self):
        pass

    def _get_test_case_by_name(self, tc_name):
        result = None
        for test_case in self.test_cases:
            s = test_case.__class__.__name__
            if s == tc_name:
                result = test_case
        return result

    @abc.abstractmethod
    def setup(self):
        fun_test._start_test(id=self.id,
                             summary="Script setup",
                             steps=self.steps)
        script_result = FunTest.FAILED

        setup_te = None
        try:
            if fun_test.suite_execution_id:  # This can happen only if it came thru the scheduler
                suite_execution_tags = fun_test.get_suite_execution_tags()
                setup_te = models_helper.add_test_case_execution(test_case_id=FunTest.SETUP_TC_ID,
                                                                 suite_execution_id=fun_test.suite_execution_id,
                                                                 result=fun_test.IN_PROGRESS,
                                                                 path=fun_test.relative_path,
                                                                 log_prefix=fun_test.log_prefix,
                                                                 tags=suite_execution_tags,
                                                                 inputs=fun_test.get_job_inputs())
            fun_test.simple_assert(self.test_cases, "At least one test-case is required. No test-cases found")
            if self.test_case_order:
                new_order = []
                for entry in self.test_case_order:
                    tc_name = entry["tc"]
                    main_test_case = self._get_test_case_by_name(tc_name=tc_name)
                    if not main_test_case:
                        raise Exception(
                            "Unable to find test-case {} in list. Did you forget to append to the script?".format(
                                tc_name))

                    if "dependencies" in entry:
                        dependencies = entry["dependencies"]
                        for dependency in dependencies:
                            t = self._get_test_case_by_name(tc_name=dependency)
                            if not t:
                                raise Exception(
                                    "Unable to find test-case {} in list. Did you forget to append to the script?".format(
                                        dependency))
                            else:
                                new_order.append(t)
                                t._added_to_script = True

                    new_order.append(main_test_case)
                    main_test_case._added_to_script = True

                self.test_cases = new_order

            ids = set()
            for test_case in self.test_cases:
                test_case.describe()
                if test_case.id in ids:
                    fun_test.test_assert(False, "Test-case Id: {} is duplicated".format(test_case.id))
                ids.add(test_case.id)
                if fun_test.selected_test_case_ids:
                    if test_case.id not in fun_test.selected_test_case_ids:
                        continue
                if fun_test.suite_execution_id:
                    suite_execution_tags = fun_test.get_suite_execution_tags()
                    te = models_helper.add_test_case_execution(test_case_id=test_case.id,
                                                               suite_execution_id=fun_test.suite_execution_id,
                                                               result=fun_test.NOT_RUN,
                                                               path=fun_test.relative_path,
                                                               log_prefix=fun_test.log_prefix,
                                                               tags=suite_execution_tags,
                                                               inputs=fun_test.get_job_inputs())
                    test_case.execution_id = te.execution_id

            self.setup()
            if setup_te:
                models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                         suite_execution_id=fun_test.suite_execution_id,
                                                         result=fun_test.PASSED)
            script_result = FunTest.PASSED
        except (TestException) as ex:
            self.at_least_one_failed = True
            if setup_te:
                models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                         suite_execution_id=fun_test.suite_execution_id,
                                                         result=fun_test.FAILED)
        except (Exception) as ex:
            self.at_least_one_failed = True
            fun_test.add_checkpoint(result=FunTest.FAILED, checkpoint="Abnormal test-case termination")
            if setup_te:
                models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                         suite_execution_id=fun_test.suite_execution_id,
                                                         result=fun_test.FAILED)
            fun_test.critical(str(ex))
        fun_test._end_test(result=script_result)
        if fun_test.suite_execution_id:
            models_helper.report_test_case_execution_result(execution_id=setup_te.execution_id,
                                                            result=script_result,
                                                            re_run_info=fun_test.get_re_run_info())

        return script_result == FunTest.PASSED

    @abc.abstractmethod
    def cleanup(self):
        fun_test._start_test(id=FunTest.CLEANUP_TC_ID,
                             summary="Script cleanup",
                             steps=self.steps)
        result = FunTest.FAILED
        try:
            self.cleanup()
            result = FunTest.PASSED
        except Exception as ex:
            fun_test.critical(ex)
        fun_test._end_test(result=result)

    def _close(self):
        fun_test.close()
        fun_test.fun_xml_obj.close()
        exit_code = 0
        if self.at_least_one_failed:
            exit_code = 127
        sys.exit(exit_code)

    def _check_abort(self, test_case):
        if test_case.abort_on_failure:
            fun_test.log("Abort requested for Test-case {}: {}".format(test_case.id, test_case.summary))
            fun_test.abort()

    def run(self):
        self.describe()
        try:
            if super(self.__class__, self).setup():
                for test_case in self.test_cases:
                    if fun_test.abort_requested:
                        break

                    test_case.describe()
                    if fun_test.selected_test_case_ids:
                        if test_case.id not in fun_test.selected_test_case_ids:
                            continue
                    fun_test._start_test(id=test_case.id,
                                         summary=test_case.summary,
                                         steps=test_case.steps)
                    test_result = FunTest.FAILED
                    try:
                        if fun_test.suite_execution_id:
                            models_helper.update_test_case_execution(test_case_execution_id=test_case.execution_id,
                                                                     suite_execution_id=fun_test.suite_execution_id,
                                                                     result=fun_test.IN_PROGRESS)
                        test_case.setup()
                        test_case.run()

                        try:
                            test_case.cleanup()
                            test_result = FunTest.PASSED
                        except Exception as ex:
                            fun_test.critical(str(ex))

                    except TestException:
                        try:
                            test_case.cleanup()
                        except Exception as ex:
                            fun_test.critical(str(ex))
                        if test_case.abort_on_failure:
                            fun_test.log("Abort requested for Test-case {}: {}".format(test_case.id, test_case.summary))
                            fun_test.abort()
                        self._check_abort(test_case)
                    except Exception as ex:
                        fun_test.critical(str(ex))
                        fun_test.add_checkpoint(result=FunTest.FAILED, checkpoint="Abnormal test-case termination")
                        try:
                            test_case.cleanup()
                        except Exception as ex:
                            fun_test.critical(str(ex))
                        self._check_abort(test_case)

                    fun_test._add_xml_trace()
                    fun_test.print_test_case_summary(fun_test.current_test_case_id)
                    fun_test._end_test(result=test_result)
                    if fun_test.suite_execution_id:
                        models_helper.report_test_case_execution_result(execution_id=test_case.execution_id,
                                                                        result=test_result,
                                                                        re_run_info=fun_test.get_re_run_info())

                    if test_result == FunTest.FAILED:
                        self.at_least_one_failed = True

            super(self.__class__, self).cleanup()

        except Exception as ex:
            fun_test.critical(str(ex))
            try:
                super(self.__class__, self).cleanup()
            except Exception as ex:
                fun_test.critical(str(ex))
        self._close()


class FunTestCase:
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        self.id = None
        self.summary = None
        self.steps = None
        self._added_to_script = None
        self.abort_on_failure = kwargs.get("abort_on_failure", False)

    def __str__(self):
        s = "{}: {}".format(self.id, self.summary)
        return s

    def set_test_details(self, id, summary, steps):
        self.id = id
        self.summary = summary
        self.steps = steps

    @abc.abstractmethod
    def describe(self):
        pass

    @abc.abstractmethod
    def setup(self):
        pass

    @abc.abstractmethod
    def cleanup(self):
        pass

    @abc.abstractmethod
    def run(self):
        pass
