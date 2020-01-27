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
from fun_global import RESULTS, get_current_time, determine_version, get_localized_time, get_current_epoch_time
from scheduler.scheduler_helper import *
import signal
from web.fun_test.web_interface import get_homepage_url
import pexpect
from uuid import getnode as get_mac
from uuid import uuid4
import getpass
from threading import Thread
from inspect import getargspec
from lib.utilities.send_mail import send_mail
from fun_global import Codes, TimeSeriesTypes


class TestException(Exception):
    def __str__(self):
        return self.message

    def __add__(self, other):
        return str(self) + str(other)


class FunTestSystemException(Exception):
    pass


class FunTestLibException(Exception):
    pass


class FunTestFatalException(Exception):
    pass


class FunTimer:
    def __init__(self, max_time=10000):
        self.max_time = max_time
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def is_expired(self, print_remaining_time=False):
        result = (self.elapsed_time()) > self.max_time
        if print_remaining_time:
            fun_test.log("Remaining time: {}".format(self.remaining_time()))
        return result

    def elapsed_time(self):
        current_time = time.time()
        return current_time - self.start_time

    def remaining_time(self):
        return self.max_time - self.elapsed_time()


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


class FunContext:
    def __init__(self,
                 description,
                 context_id,
                 output_file_path=None,
                 suite_execution_id=None,
                 test_case_execution_id=None,
                 script_id=None):
        self.description = description
        self.context_id = context_id
        self.fp = None
        self.output_file_path = output_file_path
        self.buf = ""
        self.suite_execution_id = suite_execution_id
        self.test_case_execution_id = test_case_execution_id
        self.script_id = script_id

    def get_id(self):
        return self.context_id

    def open(self):
        if self.output_file_path:
            self.fp = open(self.output_file_path, "w")
        return True

    def close(self):
        if self.fp:
            self.fp.close()
        return True

    def write(self, data):
        if self.fp:
            self.fp.write(data)

    def __str__(self):
        return "Context: {}".format(self.context_id)


class FunAlertLevel:
    LEVEL_FATAL = 0   # Fatal
    LEVEL_WARNING = 1  #


class FunAlert:
    def __init__(self, level, message):
        self.level = level
        self.message = message


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

    BOOT_ARGS_REPLACEMENT_STRING = "rpl_:"

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
        args, unknown = parser.parse_known_args()
        if args.disable_fun_test:
            self.fun_test_disabled = True
            return
        else:
            self.fun_test_disabled = False
        self.unknown_args = unknown
        self.fun_xml_obj = None
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
        if self.environment:
            self.environment = self.environment.decode('utf-8', 'ignore').encode("utf-8")
        self.inputs = args.inputs
        self.re_run_info = args.re_run_info
        self.local_settings = {}
        if self.suite_execution_id:
            self.suite_execution_id = int(self.suite_execution_id)
            self.set_my_process_id()
        print("Suite Execution Id: {}".format(self.get_suite_execution_id()))

        if args.test_case_ids:
            self.selected_test_case_ids = [int(x) for x in args.test_case_ids.split(",")]
        re_run_info = self.get_re_run_info()
        if re_run_info:
            re_run_ids = [int(x) for x in re_run_info]
            if self.selected_test_case_ids:

                ordered_list = []
                for selected_id in self.selected_test_case_ids:
                    for re_run_id in re_run_ids:
                        if int(selected_id) == int(re_run_id):
                            ordered_list.append(re_run_id)
                self.selected_test_case_ids = ordered_list
            else:
                # scheduler never sent test_case_ids
                self.selected_test_case_ids = sorted(re_run_ids)
            # print("***" + str(self.selected_test_case_ids))
        if not self.logs_dir:
            self.logs_dir = LOGS_DIR

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

        # self.initialize_output_files()

        self.counter = 0  # Mostly used for testing
        self.logging_selected_modules = []
        self.log_timestamps = True
        self.log_function_name = False
        self.pause_on_failure = False
        self.shared_variables = {}
        if self.local_settings_file:
            self.local_settings = self.parse_file_to_json(file_name=self.local_settings_file)

        self.wall_clock_timer = FunTimer()
        self.wall_clock_timer.start()
        self.fun_test_threads = {}
        self.fun_test_timers = []
        self.version = "1"
        self.determine_version()
        self.asset_manager = None
        self.statistics_manager = None
        self.time_series_manager = None
        self.build_parameters = {}
        self._prepare_build_parameters()

        self.contexts = {}
        self.last_context_id = 0
        self.profiling = False
        self.profiling_timer = None
        self.topologies = []
        self.hosts = []
        self.current_time_series_checkpoint = 0
        self.fss = []
        self.at_least_one_failed = False
        self.closed = False
        self.time_series_enabled = False

        if self.suite_execution_id:
            print "Testing mongodb"
            if not self.get_mongo_db_manager().test_connection():
                self.enable_time_series(enable=False)
            else:
                self.time_series_enabled = True

        self.script_id = None
        self.enable_profiling()
        self.start_time = get_current_time()
        self.started_epoch_time = get_current_epoch_time()
        self.time_series_buffer = {0: ""}
        self.checkpoints = {}
        self.script_file_name = ""

    def get_current_test_case_execution_id(self):
        return self.current_test_case_execution_id

    def get_custom_arg(self, key):
        value = None
        if self.unknown_args and type(self.unknown_args) is list:
            for unknown_arg_part in self.unknown_args:
                parts = unknown_arg_part.split("=")
                if len(parts) == 2:
                    unknown_arg_key = parts[0].lstrip("--")
                    if key == unknown_arg_key:
                        value = parts[1]
                        break
                if len(parts) == 1:
                    value = True
                    break
        return value

    def enable_time_series(self, enable=True):
        self.time_series_enabled = enable
        if not enable:
            self.log("Disabling time series")

    def get_script_id(self):
        if not self.script_id and self.suite_execution_id and self.current_test_case_execution_id:
            self.script_id = models_helper.get_script_id(self.current_test_case_execution_id)
        return self.script_id

    def report_message(self, message):  # Used only by FunXml only
        if self.fun_xml_obj:
            self.fun_xml_obj.add_message(message=message)

    def is_at_least_one_failed(self):
        return self.at_least_one_failed

    def initialize_output_files(self, absolute_script_file_name):
        # (frame, file_name, line_number, function_name, lines, index) = \
        #    inspect.getouterframes(inspect.currentframe())[2]
        self.absolute_script_file_name = absolute_script_file_name
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

    def enable_profiling(self):
        self.profiling = True
        self.profiling_timer = FunTimer(max_time=10000)

    def add_context(self, description, output_file_path=None):
        self.last_context_id += 1
        self.time_series_buffer[self.last_context_id] = ""
        output_file_path = output_file_path
        suite_execution_id = self.get_suite_execution_id()
        script_id = self.get_script_id()
        fc = FunContext(description=description,
                        context_id=self.last_context_id,
                        output_file_path=output_file_path,
                        suite_execution_id=suite_execution_id,
                        test_case_execution_id=self.get_test_case_execution_id(),
                        script_id=script_id)
        self.contexts[self.last_context_id] = fc
        if self.time_series_enabled:
            self.add_time_series_context(context=fc)
        fc.open()
        return fc

    def get_stored_environment_variable(self, variable_name):
        result = None
        if self.suite_execution_id:
            stored_environment = self.get_stored_environment()
            if stored_environment:
                result = stored_environment[variable_name] if variable_name in stored_environment else None
        return result

    def get_stored_environment(self):
        result = None
        if self.suite_execution_id:
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
            stored_environment_string = suite_execution.environment
            if stored_environment_string is not None:
                stored_environment = self.parse_string_to_json(stored_environment_string)
                result = stored_environment
        return result

    def _prepare_build_parameters(self):
        tftp_image_path = self.get_job_environment_variable("tftp_image_path")
        with_stable_master = self.get_job_environment_variable("with_stable_master")
        bundle_image_parameters = self.get_job_environment_variable("bundle_image_parameters")
        pre_built_artifacts = self.get_job_environment_variable("pre_built_artifacts")

        if tftp_image_path:
            self.build_parameters["tftp_image_path"] = tftp_image_path
        elif bundle_image_parameters:
            self.build_parameters["bundle_image_parameters"] = bundle_image_parameters
        elif with_stable_master:
            self.build_parameters["with_stable_master"] = with_stable_master
        elif pre_built_artifacts:
            self.build_parameters["pre_built_artifacts"] = pre_built_artifacts
        else:
            # Check if it was stored by a previous script
            tftp_image_path = self.get_stored_environment_variable(variable_name="tftp_image_path")
            self.build_parameters["tftp_image_path"] = tftp_image_path
        user_supplied_build_parameters = self.get_job_environment_variable("build_parameters")
        if user_supplied_build_parameters:
            if "BOOTARGS" in user_supplied_build_parameters:
                self.build_parameters["BOOTARGS"] = user_supplied_build_parameters["BOOTARGS"]
                self.build_parameters["BOOTARGS"] = self.build_parameters["BOOTARGS"].replace(self.BOOT_ARGS_REPLACEMENT_STRING, " ")
            if "DISABLE_ASSERTIONS" in user_supplied_build_parameters:
                self.build_parameters["DISABLE_ASSERTIONS"] = user_supplied_build_parameters["DISABLE_ASSERTIONS"]
            if "RELEASE_BUILD" in user_supplied_build_parameters:
                self.build_parameters["RELEASE_BUILD"] = user_supplied_build_parameters["RELEASE_BUILD"]
            if "FUNOS_MAKEFLAGS" in user_supplied_build_parameters:
                self.build_parameters["FUNOS_MAKEFLAGS"] = user_supplied_build_parameters["FUNOS_MAKEFLAGS"]
            if "BRANCH_FunOS" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_FunOS"] = user_supplied_build_parameters["BRANCH_FunOS"]
            if "BRANCH_FunSDK" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_FunSDK"] = user_supplied_build_parameters["BRANCH_FunSDK"]
            if "BRANCH_FunControlPlane" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_FunControlPlane"] = user_supplied_build_parameters["BRANCH_FunControlPlane"]
            if "SKIP_DASM_C" in user_supplied_build_parameters:
                self.build_parameters["SKIP_DASM_C"] = user_supplied_build_parameters["SKIP_DASM_C"]
            if "BRANCH_FunHW" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_FunHW"] = user_supplied_build_parameters["BRANCH_FunHW"]
            if "BRANCH_FunTools" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_FunTools"] = user_supplied_build_parameters["BRANCH_FunTools"]
            if "BRANCH_FunJenkins" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_FunJenkins"] = user_supplied_build_parameters["BRANCH_FunJenkins"]
            if "BRANCH_fungible_host_drivers" in user_supplied_build_parameters:
                self.build_parameters["BRANCH_fungible_host_drivers"] = user_supplied_build_parameters["BRANCH_fungible_host_drivers"]

    def get_build_parameters(self):
        return self.build_parameters

    def get_build_parameter(self, parameter):
        result = None
        build_parameters = self.get_build_parameters()
        if parameter in build_parameters:
            result = build_parameters[parameter]
        return result


    def is_build_done(self):
        suite_execution_id = self.get_suite_execution_id()
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        return suite_execution.build_done

    def abort(self):
        self.abort_requested = True

    def get_start_time(self):
        return self.start_time

    def get_job_environment(self):
        result = {}
        if not self.suite_execution_id:
            if self.environment:
                result = self.parse_string_to_json(self.environment)
        else:
            stored_environment = self.get_stored_environment()
            if stored_environment:
                result = stored_environment
        return result

    def get_rich_inputs(self):
        rich_inputs = None
        if fun_test.suite_execution_id:
            suite_execution = models_helper.get_suite_execution(suite_execution_id=fun_test.suite_execution_id)
            rich_inputs = suite_execution.rich_inputs
        return rich_inputs

    def get_suite_run_time_environment_variable(self, name):
        run_time = models_helper.get_suite_run_time(execution_id=self.suite_execution_id)
        result = run_time.get(name, None)
        return result

    def set_suite_run_time_environment_variable(self, variable, value):
        if self.suite_execution_id:
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
            if suite_execution:
                suite_execution.add_run_time_variable(variable, value)

    def set_my_process_id(self):
        run_time_process_id = self.get_suite_run_time_environment_variable("process_id")
        if not run_time_process_id:
            self.set_suite_run_time_environment_variable("process_id", {self.log_prefix: os.getpid()})
        else:
            run_time_process_id[self.log_prefix] = os.getpid()
            self.set_suite_run_time_environment_variable("process_id", run_time_process_id)

    def get_job_environment_variable(self, variable):
        result = None
        job_environment = self.get_job_environment()
        if variable in job_environment:
            result = job_environment[variable]
        return result

    def update_job_environment_variable(self, variable, value):
        job_environment = self.get_job_environment()
        if job_environment is not None:
            job_environment[variable] = value
        self.environment = json.dumps(job_environment)
        if self.suite_execution_id:
            models_helper.update_suite_execution(suite_execution_id=self.suite_execution_id, environment=job_environment)

    def is_with_jenkins_build(self):
        with_jenkins_build = self.get_job_environment_variable(variable="with_jenkins_build")
        return with_jenkins_build

    def is_simulation(self):
        result = True
        test_bed_type = self.get_job_environment_variable(variable="test_bed_type")
        test_bed = self.get_job_environment_variable(variable="test_bed")

        if test_bed_type:
            if test_bed_type != "simulation":
                result = False
        elif test_bed:
            if test_bed != "simulation":
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
        return determined_version

    def set_version(self, version):
        self.version = version
        if self.suite_execution_id:
            models_helper.update_suite_execution(suite_execution_id=self.suite_execution_id, version=version)

    def get_version(self):
        version = None
        if self.suite_execution_id:
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
            if not suite_execution:
                self.log("Suite execution: {} could not be retrieved from the DB".format(self.suite_execution_id))
            else:
                version = suite_execution.version
                if not version:
                    try:
                        version = self.determine_version()
                    except Exception as ex:
                        print("Error unable to determine the version: {}".format(str(ex)))
        else:
            version = self.version
        return version

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
        while not thread_complete and not fun_test.closed:
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


    def fetch_stable_master(self, parameters):
        from lib.system.build_helper import BuildHelper
        bh = BuildHelper(parameters=self.build_parameters)
        result = bh.fetch_stable_master(debug=parameters["debug"], stripped=parameters["stripped"])
        fun_test.test_assert(result, "Stable master fetched")
        self.build_parameters["tftp_image_path"] = result
        self.update_job_environment_variable("tftp_image_path", result)
        fun_test.log("Updating the tftp-image path: {}".format(self.build_parameters))
        return result

    def position_pre_built_artifacts(self, pre_built_artifacts):
        from lib.system.build_helper import BuildHelper
        bh = BuildHelper(parameters=None, pre_built_artifacts=pre_built_artifacts)
        result = bh.position_pre_built_artifacts(pre_built_artifacts=pre_built_artifacts)
        if result:
            self.update_job_environment_variable("tftp_image_path", result)
        return result


    def build(self):
        from lib.system.build_helper import BuildHelper
        result = False

        build_parameters = self.get_build_parameters()
        boot_args = ""
        if "BOOTARGS" in build_parameters:

            build_parameters["BOOTARGS"] = build_parameters["BOOTARGS"].replace(self.BOOT_ARGS_REPLACEMENT_STRING, " ")

            boot_args = build_parameters["BOOTARGS"]
        # fun_test.test_assert(boot_args, "BOOTARGS: {}".format(boot_args))

        test_bed_type = self.get_job_environment_variable("test_bed_type")
        fun_test.test_assert(test_bed_type, "Test-bed type: {}".format(test_bed_type))

        submitter_email = None
        if fun_test.suite_execution_id:
            suite_execution = models_helper.get_suite_execution(suite_execution_id=fun_test.suite_execution_id)
            submitter_email = suite_execution.submitter_email

        bh = BuildHelper(parameters=build_parameters)
        emulation_image = bh.build_emulation_image(submitter_email=submitter_email)
        fun_test.test_assert(emulation_image, "Build emulation image")
        self.build_parameters["tftp_image_path"] = emulation_image
        self.update_job_environment_variable("tftp_image_path", emulation_image)
        result = True
        return result

    def get_asset_manager(self):
        from asset.asset_manager import AssetManager
        if not self.asset_manager:
            self.asset_manager = AssetManager()
        return self.asset_manager


    def get_statistics_manager(self):
        from lib.utilities.statistics_manager import StatisticsManager
        if not self.statistics_manager:
            self.statistics_manager = StatisticsManager()
        return self.statistics_manager

    def get_mongo_db_manager(self, host=None):
        from lib.utilities.mongo_db_manager import MongoDbManager
        if not self.time_series_manager:
            if host is None:
                self.time_series_manager = MongoDbManager()
            else:
                self.time_series_manager = MongoDbManager(host=host)
        return self.time_series_manager

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

    def read_file(self, file_name):
        result = None
        if os.path.exists(file_name):
            with open(file_name, "r") as infile:
                result = infile.read()
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

    def get_test_case_artifact_file_name(self, post_fix_name, is_large_file=False):
        log_prefix = ""
        if self.log_prefix:
            log_prefix = "_{}".format(self.log_prefix)
        artifact_file = self.get_logs_directory(is_large_file=is_large_file) + "/" + log_prefix + self.script_file_name + "_" + str(self.get_suite_execution_id()) + "_" + str(self.get_test_case_execution_id()) + "_" + post_fix_name
        return artifact_file

    def upload_artifact(self, local_file_name_post_fix,
                        linux_obj,
                        source_file_path,
                        display_name,
                        asset_type,
                        asset_id,
                        artifact_category="general",
                        artifact_sub_category="general",
                        is_large_file=False,
                        timeout=240):
        result = None
        try:
            artifact_file_name = self.get_test_case_artifact_file_name(local_file_name_post_fix,
                                                                       is_large_file=is_large_file)

            if fun_test.scp(source_ip=linux_obj.host_ip,
                            source_file_path=source_file_path,
                            source_username=linux_obj.ssh_username,
                            source_password=linux_obj.ssh_password,
                            target_file_path=artifact_file_name,
                            timeout=timeout):
                if not is_large_file:
                    self.add_auxillary_file(description=display_name,
                                            filename=artifact_file_name,
                                            asset_type=asset_type,
                                            asset_id=asset_id,
                                            artifact_category=artifact_category,
                                            artifact_sub_category=artifact_sub_category)

                result = artifact_file_name
            else:
                fun_test.critical("scp failed")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def enable_pause_on_failure(self):
        self.pause_on_failure = True

    def get_logs_directory(self, is_large_file=False):
        result = self.logs_dir
        if is_large_file and self.suite_execution_id:
            directory_path = "{}/s_{}".format(LARGE_FILE_STORE, self.suite_execution_id)
            os.system("mkdir -p {}".format(directory_path))
            result = directory_path
        return result

    def disable_pause_on_failure(self):
        self.pause_on_failure = False

    def set_topology_json_filename(self, filename):
        if self.fun_xml_obj:
            self.fun_xml_obj.set_topology_json_filename(filename=filename)

    def register_topologies(self, topology):
        self.topologies.append(topology)

    def register_hosts(self, host):
        self.hosts.append(host)

    def register_fs(self, fs):
        self.fss.append(fs)
        asset_name = fs.get_asset_name()
        if asset_name and self.time_series_enabled:
            self.add_time_series_registered_asset(asset_name=asset_name, asset_type=AssetType.DUT)

    def get_topologies(self):
        return self.topologies

    def get_hosts(self):
        return self.hosts

    def get_fss(self):
        return self.fss

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

    def debug(self, message, context=None):
        if self.debug_enabled:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            calling_module = self._get_calling_module(outer_frames)
            self.log(message=message, level=self.LOG_LEVEL_DEBUG, calling_module=calling_module, context=context)

    def critical(self, message, context=None):
        message = str(message)
        exc_type, exc_value, exc_traceback = sys.exc_info()

        tb = traceback.format_tb(exc_traceback)
        outer_frames = inspect.getouterframes(inspect.currentframe())
        calling_module = self._get_calling_module(outer_frames)
        self.log(message=message, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module, context=context)

        if exc_traceback:
            self.log(message="***** Last Exception At *****", level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module, context=context)
            last_exception_s = "".join(tb)
            self.log(message=last_exception_s, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module, context=context)
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
                    self.log(message="ASSERT Raised by: {}".format(assert_string), level=self.LOG_LEVEL_CRITICAL, context=context)
                    break
            self.log(message="***** Traceback Stack *****", level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module, context=context)
            stack_s = "".join(traceback_stack[:-1])
            self.log(message=stack_s, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module, context=context)


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

    def delete_time_series_document(self, collection_name, query):
        try:
            result = self.get_mongo_db_manager().delete_one(collection_name=collection_name, query=query)
            if not result:
                self.critical("Unable to remove_time_series_document: {}".format(query))
            # fun_test.log("Removed document")
        except Exception as ex:
            self.critical(str(ex))


    def add_time_series_document(self, collection_name, epoch_time, type, **kwargs):
        try:
            result = self.get_mongo_db_manager().insert_one(collection_name=collection_name,
                                                            epoch_time=epoch_time,
                                                            type=type,
                                                            **kwargs)
            if not result:
                self.critical("Unable to add_time_series_document: {}".format(kwargs))
        except Exception as ex:
            self.critical(str(ex))
            self.enable_time_series(enable=False)

    def add_time_series_registered_asset(self, asset_name, asset_type=None):
        try:
            epoch_time = get_current_epoch_time()
            data = {"asset_id": asset_name,
                    "asset_type": asset_type}
            self.add_time_series_document(collection_name=self.get_time_series_collection_name(),
                                          epoch_time=epoch_time,
                                          type=TimeSeriesTypes.REGISTERED_ASSET,
                                          te=self.current_test_case_execution_id,
                                          data=data)
        except Exception as ex:
            self.critical(str(ex))
            self.enable_time_series(enable=False)

    def add_time_series_artifact(self,
                                 description,
                                 filename,
                                 asset_type,
                                 asset_id,
                                 category,
                                 sub_category):
        epoch_time = get_current_epoch_time()
        data = {"description": description,
                "filename": filename,
                "asset_type": asset_type,
                "asset_id": asset_id,
                "category": category,
                "sub_category": sub_category
                }
        self.add_time_series_document(collection_name=self.get_time_series_collection_name(),
                                      epoch_time=epoch_time,
                                      type=TimeSeriesTypes.ARTIFACT,
                                      te=self.current_test_case_execution_id,
                                      data=data)

    def add_time_series_log(self, data, epoch_time=None):
        if not epoch_time:
            epoch_time = get_current_epoch_time()
        # data = data.decode('utf-8', 'ignore')
        self.add_time_series_document(collection_name=self.get_time_series_collection_name(),
                                      epoch_time=epoch_time,
                                      type=TimeSeriesTypes.LOG,
                                      te=self.current_test_case_execution_id,
                                      data=data)

    def delete_time_series_checkpoint(self, checkpoint_index):
        query = {"type": TimeSeriesTypes.CHECKPOINT,
                 "data.checkpoint_index": checkpoint_index,
                 "te": self.current_test_case_execution_id}
        self.delete_time_series_document(collection_name=self.get_time_series_collection_name(),
                                         query=query)

    def add_time_series_checkpoint(self, data):
        self.add_time_series_document(collection_name=self.get_time_series_collection_name(),
                                      epoch_time=get_current_epoch_time(),
                                      type=TimeSeriesTypes.CHECKPOINT,
                                      te=self.current_test_case_execution_id,
                                      data=data)

    def add_time_series_test_case_table(self, data):
        self.add_time_series_document(collection_name=self.get_time_series_collection_name(),
                                      epoch_time=get_current_epoch_time(),
                                      type=TimeSeriesTypes.TEST_CASE_TABLE,
                                      te=self.current_test_case_execution_id,
                                      data=data)

    def add_time_series_context(self, context):
        try:
            result = self.get_mongo_db_manager().insert_one(collection_name=self.get_time_series_collection_name(),
                                                            epoch_time=get_current_epoch_time(),
                                                            type=TimeSeriesTypes.CONTEXT_INFO,
                                                            context_id=context.context_id,
                                                            description=context.description,
                                                            suite_execution_id=context.suite_execution_id,
                                                            test_case_execution_id=context.test_case_execution_id,
                                                            script_id=context.script_id)
            if not result:
                self.critical("Unable to add_time_series_context: {}".format(context))
        except Exception as ex:
            self.critical(str(ex))
            self.enable_time_series(enable=False)

    def update_time_series_script_run_time(self, started_epoch_time=None):
        script_id = self.get_script_id()
        update_dict = {"suite_execution_id": self.suite_execution_id,
                       "script_id": script_id,
                       "started_epoch_time": started_epoch_time,
                       "type": TimeSeriesTypes.SCRIPT_RUN_TIME}
        try:

            result = self.get_mongo_db_manager().find_one_and_update(collection_name=self.get_time_series_collection_name(),
                                                            key={"suite_execution_id": self.suite_execution_id,
                                                                 "script_id": script_id},
                                                            **update_dict)

        except Exception as ex:
            self.critical(str(ex))
            self.enable_time_series(enable=False)


    def log(self,
            message,
            level=LOG_LEVEL_NORMAL,
            newline=True,
            trace_id=None,
            stdout=True,
            calling_module=None,
            no_timestamp=False,
            context=None,
            ignore_context_description=None,
            section=False,
            from_flush=False):
        current_time = get_current_time()
        current_epoch_time = get_current_epoch_time()

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

        if self.fun_xml_obj:
            self.fun_xml_obj.log(log=message, newline=newline)

        level_name = ""
        if level == self.LOG_LEVEL_CRITICAL:
            level_name = "CRITICAL: {}".format(module_line_info)
        elif level == self.LOG_LEVEL_DEBUG:
            level_name = "DEBUG: {}".format(module_line_info)
        if level is not self.LOG_LEVEL_NORMAL:
            message = "%s%s: %s%s" % (self.LOG_COLORS[level], level_name, message, self.LOG_COLORS['RESET'])

        nl = ""
        if newline:
            nl = "\n"
        if not ignore_context_description:
            final_message = self._get_context_prefix(context=context, message=str(message) + nl)
        else:
            final_message = str(message) + nl
        final_message_for_time_series = final_message

        if self.log_timestamps and (not no_timestamp) and not section:
            final_message = "[{}] {}".format(current_time, final_message)

        if section:
            final_message = "\n{}\n{}\n".format(final_message, "=" * len(final_message))
        if context:
            context.write(final_message)
        if stdout:
            sys.stdout.write(final_message)
            sys.stdout.flush()

        context_id = 0
        if context:
            context_id = context.get_id()

        if self.time_series_enabled:
            try:
                if from_flush:
                    if not final_message_for_time_series.endswith("\n"):
                        self.time_series_buffer[context_id] += final_message_for_time_series
                    else:
                        final_message_for_time_series = self.time_series_buffer[context_id] + final_message_for_time_series
                        for part in final_message_for_time_series.split("\n"):
                            if not part:
                                continue
                            data = {"checkpoint_index": self.current_time_series_checkpoint,
                                    "log": part.rstrip().lstrip(),
                                    "context_id": context_id}
                            self.add_time_series_log(data=data, epoch_time=current_epoch_time)
                        self.time_series_buffer[context_id] = ""
                else:
                    final_message_for_time_series = final_message_for_time_series.decode('utf-8', 'ignore')
                    data = {"checkpoint_index": self.current_time_series_checkpoint,
                            "log": final_message_for_time_series.rstrip().lstrip(),
                            "context_id": context_id}
                    self.add_time_series_log(data=data, epoch_time=current_epoch_time)
            except Exception as ex:
                print "Timeseries exception: {}".format(str(ex))


    def get_time_series_collection_name(self):
        return models_helper.get_fun_test_time_series_collection_name(self.get_suite_execution_id())

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

    def log_section(self, message, context=None):
        calling_module = None
        if self.logging_selected_modules:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            calling_module = self._get_calling_module(outer_frames=outer_frames)
        # s = "\n{}\n{}\n".format(message, "=" * len(message))
        self.log(message, calling_module=calling_module, context=context, section=True)

    def write(self, message, context=None):
        if context:
            context.buf = message
        else:
            self.buf = message

    def flush(self, trace_id=None, stdout=True, context=None):
        calling_module = None
        if self.logging_selected_modules:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            calling_module = self._get_calling_module(outer_frames=outer_frames)
        buf = self.buf
        if context:
            buf = context.buf
        if trace_id:
            self.trace(id=trace_id, log=buf)
        self.log(buf, newline=False,
                 stdout=stdout,
                 calling_module=calling_module,
                 no_timestamp=True,
                 context=context,
                 ignore_context_description=True,
                 from_flush=True)
        if context:
            context.buf = ""
        else:
            self.buf = ""

    def _print_log_green(self, message, calling_module=None, context=None):
        module_info = ""
        if calling_module:
            module_info = "{}.py: {}".format(calling_module[0], calling_module[1])
        message = "\n%s%s: %s %s%s" % (self.LOG_COLORS["GREEN"], "", module_info, message, self.LOG_COLORS['RESET'])

        sys.stdout.write(str(message) + "\n")
        sys.stdout.flush()
        if context:
            context.write(str(message) + "\n")

    def sleep(self, message, seconds=5, context=None, no_log=False):
        outer_frames = inspect.getouterframes(inspect.currentframe())
        calling_module = self._get_calling_module(outer_frames)
        if not no_log:
            message = "zzz...: Sleeping for :" + str(seconds) + "s : " + message
            self._print_log_green(message=message, calling_module=calling_module, context=context)
            if self.fun_xml_obj:
                self.fun_xml_obj.log(log=message, newline=True)
            context_id = 0
            if context:
                context_id = context.get_id()
            if self.time_series_enabled:
                data = {"checkpoint_index": self.current_time_series_checkpoint,
                        "log": message.rstrip().lstrip(),
                        "context_id": context_id}
                self.add_time_series_log(data=data, epoch_time=get_current_epoch_time())
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

    def _print_summary(self, context=None):
        self.log_section(message="Summary")
        format = "{:<4} {:<10} {:<100}"
        self.log(format.format("Id", "Result", "Description"), no_timestamp=True, context=context)
        for k, v in self.test_metrics.items():
            self.log(format.format(k, v["result"], v["summary"]), no_timestamp=True, context=context)

        self.log("{}{}/".format(get_homepage_url(), LOGS_RELATIVE_DIR) + self.script_file_name.replace(".py", ".html"),
                 no_timestamp=True, context=context)
        self.log("\nRuntime: {}".format(self.get_wall_clock_time()), context=context)

    def print_test_case_summary(self, test_case_id, context=None):
        metrics = self.test_metrics[test_case_id]
        assert_list = metrics["asserts"]
        self.log_section("Testcase {} summary".format(test_case_id), context=context)
        for assert_result in assert_list:
            self.log(assert_result, no_timestamp=True, context=context)

    def _initialize(self, script_file_name):
        self.initialize_output_files(absolute_script_file_name=script_file_name)
        if self.initialized:
            raise FunTestSystemException("FunTest obj initialized twice")
        self.initialized = True

    def close(self):
        for timer in self.fun_test_timers:
            fun_test.log("Waiting for active timers to stop")
            max_wait_time = 5 * 60
            max_timer_wait_timer = FunTimer(max_time=max_wait_time)
            while timer.is_alive() and not max_timer_wait_timer.is_expired():
                time.sleep(1)
            if max_timer_wait_timer.is_expired():
                fun_test.log("Max wait {} for active timers expired".format(max_wait_time))

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
        if self.time_series_enabled:
            data = {"panel_header": panel_header, "table_name": table_name, "table_data": table_data}
            self.add_time_series_test_case_table(data=data)

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
        self.current_time_series_checkpoint = 0

    def _end_test(self, result):
        self.fun_xml_obj.end_test(result=result)
        if result == FunTest.FAILED:
            self.at_least_one_failed = True
        self.test_metrics[self.current_test_case_id]["result"] = result
        self.add_checkpoint("End test-case")

    def _append_assert_test_metric(self, assert_message):
        if self.current_test_case_id in self.test_metrics:
            self.test_metrics[self.current_test_case_id]["asserts"].append(assert_message)

    def test_assert(self, expression, message, ignore_on_success=False, context=None):
        actual = True
        if not expression:
            actual = False
        self.test_assert_expected(expected=True,
                                  actual=actual,
                                  message=message,
                                  ignore_on_success=ignore_on_success, context=context)

    def simple_assert(self, expression, message, context=None):
        self.test_assert(expression=expression, message=message, ignore_on_success=True, context=context)

    def _get_context_prefix(self, context, message):
        s = "{}".format(message)
        if context:
            s = "{}: {}".format(context.description, message.lstrip("\n"))
        return s

    def test_assert_expected(self, expected, actual, message, ignore_on_success=False, context=None):
        if not ((type(actual) is dict) and (type(expected) is dict)):
            expected = str(expected)
            actual = str(actual)
        assert_message = "ASSERT PASSED: expected={} actual={}, {}".format(expected, actual, message)
        if not expected == actual:
            assert_message = "ASSERT FAILED: expected={} actual={}, {}".format(expected, actual, message)
            if self.initialized:
                self._append_assert_test_metric(assert_message)
                this_checkpoint = self._get_context_prefix(context=context, message=message)
                # if self.profiling:
                #    this_checkpoint = "{:.2f}: {}".format(self.profiling_timer.elapsed_time(), this_checkpoint)
                self.add_checkpoint(checkpoint=this_checkpoint, expected=expected, actual=actual, result=FunTest.FAILED, context=context)
            self.critical(assert_message, context=context)
            if self.pause_on_failure and not self.suite_execution_id:
                pdb.set_trace()

            """
            if self.suite_execution_id:
                suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
                if suite_execution.pause_on_failure:
                    fun_test.log("Pause on failure set for {}".format(assert_message))
                    suite_execution.state = JobStatusType.PAUSED
                    suite_execution.save()
                    self.pause_loop()
            """
            self.check_pause_on_failure(assert_message)
            raise TestException(assert_message)
        if not ignore_on_success:
            self.log(assert_message, context=context)
            if self.initialized:
                self._append_assert_test_metric(assert_message)
                this_checkpoint = self._get_context_prefix(context=context, message=message)
                # if self.profiling:
                #    this_checkpoint = "{:.2f}: {}".format(self.profiling_timer.elapsed_time(), this_checkpoint)  #TODO: Duplicate line
                self.add_checkpoint(checkpoint=this_checkpoint, expected=expected, actual=actual, result=FunTest.PASSED, context=context)

    def pause_loop(self):
        max_pause_loop_timer = FunTimer(max_time=24 * 60 * 60)
        if self.suite_execution_id:
            while not max_pause_loop_timer.is_expired():
                self.sleep("Pause loop", seconds=60)
                suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
                if not suite_execution.pause_on_failure:
                    fun_test.log("Exiting pause loop")
                    suite_execution.state = JobStatusType.IN_PROGRESS
                    suite_execution.save()
                    break
        suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
        suite_execution.state = JobStatusType.IN_PROGRESS
        suite_execution.save()

    def add_checkpoint(self,
                       checkpoint=None,
                       result=PASSED,
                       expected="",
                       actual="",
                       context=None):

        checkpoint = self._get_context_prefix(context=context, message=checkpoint)
        checkpoint_for_time_series = checkpoint
        if self.profiling:
            checkpoint = "{:.2f} {}".format(self.profiling_timer.elapsed_time(), checkpoint)
        if self.fun_xml_obj:
            self.fun_xml_obj.add_checkpoint(checkpoint=checkpoint,
                                            result=result,
                                            expected=expected,
                                            actual=actual)


        context_id = 0
        if context:
            context_id = context.get_id()

        data = {"checkpoint": checkpoint_for_time_series,
                "result": result, 
                "expected": expected,
                "actual": actual,
                "checkpoint_index": self.current_time_series_checkpoint,
                "context_id": context_id}

        if self.time_series_enabled:
            if self.current_time_series_checkpoint == 0:
                self.delete_time_series_checkpoint(checkpoint_index=0)
            # self.log("Added checkpoint: {}".format(self.current_time_series_checkpoint))
            self.add_time_series_checkpoint(data=data)
        if self.current_test_case_id not in self.checkpoints:
            self.checkpoints[self.current_test_case_id] = []
        self.checkpoints[self.current_test_case_id].append(checkpoint)
        self.current_time_series_checkpoint += 1

    def add_in_progress_checkpoint(self):
        # only for dummy checkpoint
        if self.time_series_enabled:
            data = {"checkpoint": "In-progress",
                    "result": FunTest.PASSED,
                    "expected": True,
                    "actual": True,
                    "checkpoint_index": 0,
                    "context_id": 0}
            self.add_time_series_checkpoint(data=data)

    def exit_gracefully(self, sig, _):
        self.critical("Unexpected Exit")
        if self.suite_execution_id:
            models_helper.update_test_case_execution(test_case_execution_id=self.current_test_case_execution_id,
                                                     suite_execution_id=self.suite_execution_id,
                                                     result=self.FAILED)
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

    def add_auxillary_file(self, description, filename,
                           asset_type="general",
                           asset_id="Unknown",
                           artifact_category="general",
                           artifact_sub_category="general"):
        base_name = os.path.basename(filename)
        self.fun_xml_obj.add_auxillary_file(description=description, auxillary_file=base_name)

        if self.time_series_enabled:
            self.add_time_series_artifact(description=description,
                                          filename=filename,
                                          asset_type=asset_type,
                                          asset_id=asset_id,
                                          category=artifact_category,
                                          sub_category=artifact_sub_category)

    def send_mail(self, subject, content, to_addresses=["john.abraham@fungible.com"]):
        try:
            if fun_test.suite_execution_id:
                suite_execution = models_helper.get_suite_execution(suite_execution_id=fun_test.suite_execution_id)
                if suite_execution:
                    to_addresses.append(suite_execution.submitter_email)
                    content += '<br><a href="{}/regression/suite_detail/{}">Suite detail link</a>'.format(get_homepage_url(), fun_test.suite_execution_id)
        except Exception as ex:
            self.critical(str(ex))
        send_mail(to_addresses=to_addresses, subject=subject, content=content)

    def add_start_checkpoint(self):

        data = {"checkpoint": "Start",
                "result": FunTest.PASSED,
                "expected": True,
                "actual": True,
                "checkpoint_index": fun_test.current_time_series_checkpoint,
                "context_id": 0}
        if self.time_series_enabled:
            fun_test.add_time_series_checkpoint(data=data)

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

    def check_pause_on_failure(self, message):
        if self.suite_execution_id:
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.suite_execution_id)
            if suite_execution.pause_on_failure:
                self.log("Pause on failure set for {}".format(message))
                suite_execution.state = JobStatusType.PAUSED
                suite_execution.save()
                self.pause_loop()

fun_test = FunTest()


class FunTestScript(object):
    __metaclass__ = abc.ABCMeta
    test_case_order = None

    def __init__(self):
        st = inspect.stack()
        script_file_name = st[1][1]
        fun_test._initialize(script_file_name)
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

                fun_test.current_test_case_execution_id = setup_te.execution_id
                if fun_test.time_series_enabled:
                    fun_test.update_time_series_script_run_time(started_epoch_time=fun_test.started_epoch_time)
                    fun_test.add_in_progress_checkpoint()
                # fun_test.add_start_checkpoint()
            fun_test._start_test(id=self.id,
                                 summary="Script setup",
                                 steps=self.steps)

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
            fun_test.log("Test-case count: {}".format(len(self.test_cases)))


            if fun_test.selected_test_case_ids:
                new_test_cases = []
                for selected_test_case_id in fun_test.selected_test_case_ids:
                    for test_case in self.test_cases:
                        test_case.describe()
                        if test_case.id == selected_test_case_id:
                            new_test_cases.append(test_case)
                self.test_cases = new_test_cases

            for test_case in self.test_cases:
                test_case.describe()
                if test_case.id in ids:
                    fun_test.test_assert(False, "Test-case Id: {} is duplicated".format(test_case.id))
                ids.add(test_case.id)
                if fun_test.selected_test_case_ids:
                    if test_case.id not in fun_test.selected_test_case_ids:
                        fun_test.log("test-case-id: {} not in selected test-cases: {}".format(test_case.id, fun_test.selected_test_case_ids))
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

            if fun_test.build_parameters and "with_stable_master" in fun_test.build_parameters and fun_test.build_parameters["with_stable_master"]:
                fun_test.test_assert(fun_test.fetch_stable_master(fun_test.build_parameters["with_stable_master"]), "Fetch stable master image from dochub")

            elif fun_test.build_parameters and "pre_built_artifacts" in fun_test.build_parameters:
                fun_test.simple_assert(fun_test.position_pre_built_artifacts(pre_built_artifacts=fun_test.build_parameters["pre_built_artifacts"]), "Unable to setup pre-built artifacts")

            tftp_image_path_provided = "tftp_image_path" in fun_test.build_parameters and fun_test.build_parameters["tftp_image_path"]
            if fun_test.is_with_jenkins_build() and fun_test.suite_execution_id and not tftp_image_path_provided:
                if not fun_test.is_build_done():
                    fun_test.test_assert(fun_test.build(), "Jenkins build")
                    suite_execution = models_helper.get_suite_execution(suite_execution_id=fun_test.suite_execution_id)
                    suite_execution.build_done = True
                    suite_execution.save()
                else:
                    fun_test.log("Skipping Jenkins build as it is not the first script")
            self.setup()
            script_result = FunTest.PASSED
        except (TestException) as ex:
            self.at_least_one_failed = True
            script_result = FunTest.FAILED
        except (Exception) as ex:
            self.at_least_one_failed = True
            script_result = FunTest.FAILED
            fun_test.add_checkpoint(result=FunTest.FAILED, checkpoint="Abnormal test-case termination")
            fun_test.critical(str(ex))
        if setup_te:
            models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                     suite_execution_id=fun_test.suite_execution_id,
                                                     result=script_result)
            models_helper.report_re_run_result(execution_id=setup_te.execution_id, re_run_info=fun_test.get_re_run_info())
        fun_test._end_test(result=script_result)

        return script_result == FunTest.PASSED




    def _cleanup_fss(self):
        cleanup_error_found = False

        for fs in fun_test.get_fss():
            if fs and not fs.cleanup_attempted:
                fun_test.log("FS {} was not cleaned up. Attempting ...".format(fs.context))
                try:
                    fs.cleanup()
                except Exception as ex:
                    fun_test.critical(ex)
                    cleanup_error_found = True
            fun_test.simple_assert(not cleanup_error_found, "FS {} cleanup error".format(fs.context))


    def _cleanup_topologies(self):
        topologies = fun_test.get_topologies()
        cleanup_error_found = False

        for topology in topologies:
            if not topology.is_cleaned_up():
                fun_test.log("Topology was not cleaned up. Attempting ...")
                try:
                    topology.cleanup()
                except Exception as ex:
                    fun_test.critical(ex)
                    cleanup_error_found = True
        fun_test.simple_assert(not cleanup_error_found, "Topology cleanup error")

    def _cleanup_hosts(self):
        for host in fun_test.get_hosts():
            try:
                if host.handle:
                    try:
                        host.destroy()
                    except:
                        pass
                fun_test.log("Host: {} properly disconnected".format(host))
            except:
                pass

    @abc.abstractmethod
    def cleanup(self):

        cleanup_te = None
        cleanup_error_found = False
        if fun_test.suite_execution_id:
            cleanup_te = models_helper.add_test_case_execution(test_case_id=FunTest.CLEANUP_TC_ID,
                                                  suite_execution_id=fun_test.suite_execution_id,
                                                  result=fun_test.IN_PROGRESS,
                                                  path=fun_test.relative_path,
                                                  log_prefix=fun_test.log_prefix,
                                                  inputs=fun_test.get_job_inputs())
            fun_test.current_test_case_execution_id = cleanup_te.execution_id
            if fun_test.time_series_enabled:
                fun_test.add_in_progress_checkpoint()

        fun_test._start_test(id=FunTest.CLEANUP_TC_ID,
                             summary="Script cleanup",
                             steps=self.steps)
        result = FunTest.PASSED

        try:
            try:
                self.cleanup()
            except Exception as ex:
                result = FunTest.FAILED
                cleanup_error_found = True
                fun_test.critical(ex)

            try:
                self._cleanup_topologies()
            except Exception as ex:
                result = FunTest.FAILED
                cleanup_error_found = True
                fun_test.critical(ex)

            try:
                self._cleanup_fss()
            except Exception as ex:
                result = FunTest.FAILED
                cleanup_error_found = True
                fun_test.critical(ex)

            try:
                self._cleanup_hosts()
            except Exception as ex:
                fun_test.critical(ex)


        except Exception as ex:
            fun_test.critical(ex)
        fun_test.add_checkpoint(checkpoint="Cleanup error found",
                                expected=False,
                                actual=cleanup_error_found,
                                result=result)
        fun_test._end_test(result=result)
        if cleanup_te:
            models_helper.update_test_case_execution(test_case_execution_id=cleanup_te.execution_id,
                                                     suite_execution_id=fun_test.suite_execution_id,
                                                     result=result)

            models_helper.report_re_run_result(execution_id=cleanup_te.execution_id, re_run_info=fun_test.get_re_run_info())

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
            if FunTestScript.setup(self):
                for test_case in self.test_cases:
                    if fun_test.abort_requested:
                        break

                    test_case.describe()
                    if fun_test.selected_test_case_ids:
                        if test_case.id not in fun_test.selected_test_case_ids:
                            continue

                    test_result = FunTest.FAILED
                    try:
                        if fun_test.suite_execution_id:
                            models_helper.update_test_case_execution(test_case_execution_id=test_case.execution_id,
                                                                     suite_execution_id=fun_test.suite_execution_id,
                                                                     result=fun_test.IN_PROGRESS,
                                                                     started_time=get_current_time())
                            fun_test.current_test_case_execution_id = test_case.execution_id
                            if fun_test.time_series_enabled:
                                fun_test.add_in_progress_checkpoint()
                        # fun_test.add_start_checkpoint()
                        fun_test._start_test(id=test_case.id,
                                             summary=test_case.summary,
                                             steps=test_case.steps)
                        test_case.setup()
                        test_case.run()

                        try:
                            test_case.cleanup()
                            test_result = FunTest.PASSED
                        except Exception as ex:
                            fun_test.critical(str(ex))

                    except TestException as ex:
                        fun_test.check_pause_on_failure(str(ex))
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
                        fun_test.check_pause_on_failure(str(ex))

                        try:
                            test_case.cleanup()
                        except Exception as ex:
                            fun_test.critical(str(ex))
                        self._check_abort(test_case)

                    fun_test._add_xml_trace()
                    fun_test.print_test_case_summary(fun_test.current_test_case_id)
                    fun_test._end_test(result=test_result)
                    if fun_test.suite_execution_id:
                        models_helper.update_test_case_execution(test_case_execution_id=test_case.execution_id,
                                                                 suite_execution_id=fun_test.suite_execution_id,
                                                                 result=test_result)
                        models_helper.report_re_run_result(execution_id=test_case.execution_id,
                                                           re_run_info=fun_test.get_re_run_info())

                    if test_result == FunTest.FAILED:
                        self.at_least_one_failed = True

            FunTestScript.cleanup(self)

        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.check_pause_on_failure(str(ex))

            try:
                FunTestScript.cleanup(self)
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

    def set_test_details(self, id, summary, steps, test_rail_case_ids=None):
        self.id = id
        self.summary = summary
        self.steps = steps
        if fun_test.suite_execution_id:
            script_relative_path = fun_test.absolute_script_file_name.replace(SCRIPTS_DIR, "")
            models_helper.update_test_case_info(test_case_id=self.id, summary=summary, script_path=script_relative_path)

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

