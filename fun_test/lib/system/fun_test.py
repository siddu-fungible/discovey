import sys, os
import traceback
import collections
import abc
import time, json, pdb
import inspect
from fun_settings import *
import fun_xml
import argparse
from fun_global import RESULTS, get_current_time
from scheduler.scheduler_helper import *
import signal
from web.fun_test.web_interface import get_homepage_url

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
        "RESET": '\033[30m',
        "GREEN": '\033[92m'
    }

    def __init__(self):
        parser = argparse.ArgumentParser(description="FunTest")
        parser.add_argument('--logs_dir',
                            dest="logs_dir",
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
        args = parser.parse_args()
        self.logs_dir = args.logs_dir
        self.suite_execution_id = args.suite_execution_id
        self.relative_path = args.relative_path
        self.selected_test_case_ids = None
        self.current_test_case_execution_id = None
        self.build_url = args.build_url
        if self.suite_execution_id:
            self.suite_execution_id = int(self.suite_execution_id)

        if args.test_case_ids:
            self.selected_test_case_ids = [int(x) for x in args.test_case_ids.split(",")]
            # print("***" + str(self.selected_test_case_ids))
        if not self.logs_dir:
            self.logs_dir = LOGS_DIR

        signal.signal(signal.SIGINT, self.exit_gracefully)
        # signal.signal(signal.SIGTERM, self.exit_gracefully)

        self.initialized = False
        self.debug_enabled = False
        self.function_tracing_enabled = False
        self.buf = None
        self.current_test_case_id = None
        self.traces = {}
        (frame, file_name, line_number, function_name, lines, index) = \
            inspect.getouterframes(inspect.currentframe())[2]
        absolute_script_file_name = file_name
        self.script_file_name = os.path.basename(absolute_script_file_name)
        script_file_name_without_extension = self.script_file_name.replace(".py", "")

        self.test_metrics = collections.OrderedDict()
        self.logging_selected_modules = []

        html_log_file = "{}.html".format(script_file_name_without_extension)
        if self.relative_path:
            html_log_file = get_flat_html_log_file_name(self.relative_path)
        self.fun_xml_obj = fun_xml.FunXml(script_name=script_file_name_without_extension,
                                          log_directory=self.logs_dir,
                                          log_file=html_log_file,
                                          full_script_path=absolute_script_file_name)
        reload(sys)
        sys.setdefaultencoding('UTF8') #Needed for xml
        self.counter = 0  # Mostly used for testing

        self.log_timestamps = True
        self.pause_on_failure = False

    def create_test_case_artifact_file(self, post_fix_name, contents):
        artifact_file = self.logs_dir + "/" + self.script_file_name + "_" + str(self.get_test_case_execution_id()) + "_" + post_fix_name
        with open(artifact_file, "w") as f:
            f.write(contents)
        return os.path.basename(artifact_file)

    def enable_pause_on_failure(self):
        if not is_regression_server():
            self.pause_on_failure = True
        else:
            fun_test.critical("Pause on failure not allowed on a regression server")

    def disable_pause_on_failure(self):
        if not is_regression_server():
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
            env_sid = 100
        sid = self.suite_execution_id if self.suite_execution_id else env_sid
        return sid

    def get_test_case_execution_id(self):
        return self.current_test_case_execution_id if self.current_test_case_execution_id else 100

    def log_enable_timestamps(self):
        self.log_timestamps = True

    def log_disable_timestamps(self):
        self.log_timestamps = False

    def log_selected_module(self, module_name):
        self.logging_selected_modules.append(module_name.strip("*.py"))

    def log_disable_selective(self):
        self.logging_selected_modules = []

    def log_selected_modules(self, module_names):
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
        tb = sys.exc_info()[2]
        s = ""
        stack_found = False
        if hasattr(tb, "tb_next"):
            a = tb.tb_next
            if a:
                traceback.print_tb(a)
                f = traceback.format_tb(a)
                s = "\n".join(f)
                stack_found = True
        if not stack_found:
            s = traceback.format_stack()
            if "format_stack" in s[-1]:
                s = s[: -1]

        asserts_present = None
        s2 = list(s)
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
                s = s[: len(s) - index]
                self.log(message="ASSERT Raised by: {}".format(assert_string), level=self.LOG_LEVEL_CRITICAL)
                break

        stack_s = "".join(s)
        message = "\nTraceback:\n" + message + "\n" + stack_s
        outer_frames = inspect.getouterframes(inspect.currentframe())
        calling_module = self._get_calling_module(outer_frames)
        self.log(message=message, level=self.LOG_LEVEL_CRITICAL, calling_module=calling_module)


    def _get_module_name(self, outer_frames):
        module_name = os.path.basename(outer_frames[0][1]).strip(".py")
        line_number = outer_frames[0][2]
        return (module_name, line_number)

    def _get_calling_module(self, outer_frames):
        module_info = None
        for f in outer_frames:
            if not f[1].endswith("fun_test.py"):
                module_info = (os.path.basename(f[1]).strip(".py"), f[2])
                break
        return module_info

    def _is_selected_module(self, module_name):
        return module_name in self.logging_selected_modules

    def dict_to_json_string(self, d):
        return json.dumps(d, indent=4)

    def log(self,
            message,
            level=LOG_LEVEL_NORMAL,
            newline=True,
            trace_id=None,
            stdout=True,
            calling_module=None,
            no_timestamp=False):
        current_time = get_current_time()
        message = str(message)
        if trace_id:
            self.trace(id=trace_id, log=message)
        module_line_info = ""
        if level in [self.LOG_LEVEL_DEBUG, self.LOG_LEVEL_CRITICAL]:
            if calling_module:
                module_line_info = "{}.py:{} ".format(calling_module[0], calling_module[1])
        if self.logging_selected_modules:
            outer_frames = inspect.getouterframes(inspect.currentframe())
            if not calling_module:
                module_name = self._get_calling_module(outer_frames=outer_frames)
            else:
                module_name = calling_module[0]
            if (not module_name == "fun_test") and not self._is_selected_module(module_name=module_name):
                return
            else:
                message = "{}: {}".format(module_name, message)

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
                format = "{:<" + str(max_chars_per_column) + "} {}"
                this_k = k[start: end]
                if not start:
                    print format.format(this_k, v)
                else:
                    print format.format(this_k, "")
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
        self._print_log_green("zzz...: Sleeeping for :" + str(seconds) + "s : " + message,
                              calling_module=calling_module)
        time.sleep(seconds)

    def safe(self, the_function):
        def inner(*args, **kwargs):
            if self.debug_enabled and self.function_tracing_enabled:
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
        self._print_summary()

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
        if not self.current_test_case_id in self.traces:
            self.traces[self.current_test_case_id] = {}
        if not id in self.traces[self.current_test_case_id]:
            self.traces[self.current_test_case_id][id] = log
        self.traces[self.current_test_case_id][id] += log

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
        if not (type(actual) is dict) and (type(expected) is dict):
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

fun_test = FunTest()

class FunTestScript(object):
    __metaclass__ = abc.ABCMeta
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

    @abc.abstractmethod
    def setup(self):
        fun_test._start_test(id=self.id,
                               summary="Script setup",
                               steps=self.steps)
        script_result = FunTest.FAILED

        setup_te = None
        try:

            if fun_test.suite_execution_id:  # This can happen only if it came thru the scheduler
                setup_te = models_helper.add_test_case_execution(test_case_id=FunTest.SETUP_TC_ID,
                                                           suite_execution_id=fun_test.suite_execution_id,
                                                           result=fun_test.IN_PROGRESS,
                                                           path=fun_test.relative_path)
                for test_case in self.test_cases:
                    test_case.describe()
                    if fun_test.selected_test_case_ids:
                        if not test_case.id in fun_test.selected_test_case_ids:
                            continue
                    te = models_helper.add_test_case_execution(test_case_id=test_case.id,
                                                               suite_execution_id=fun_test.suite_execution_id,
                                                               result=fun_test.NOT_RUN,
                                                               path=fun_test.relative_path)
                    test_case.execution_id = te.execution_id

            self.setup()
            if setup_te:
                models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                           suite_execution_id=fun_test.suite_execution_id,
                                                           result=fun_test.PASSED)
            script_result = FunTest.PASSED
        except (TestException) as ex:
            if setup_te:
                models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                       suite_execution_id=fun_test.suite_execution_id,
                                                       result=fun_test.FAILED)
        except (Exception) as ex:
            if setup_te:
                models_helper.update_test_case_execution(test_case_execution_id=setup_te.execution_id,
                                                       suite_execution_id=fun_test.suite_execution_id,
                                                       result=fun_test.FAILED)
            fun_test.critical(str(ex))
        fun_test._end_test(result=script_result)

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
        except TestException as ex:
            fun_test.critical(ex)
        fun_test._end_test(result=result)

    def _close(self):
        fun_test.close()
        fun_test.fun_xml_obj.close()
        exit_code = 0
        if self.at_least_one_failed:
            exit_code = 127
        sys.exit(exit_code)

    def run(self):
        self.describe()
        try:
            if super(self.__class__, self).setup():
                for test_case in self.test_cases:

                    test_case.describe()
                    if fun_test.selected_test_case_ids:
                        if not test_case.id in fun_test.selected_test_case_ids:
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
                        test_case.cleanup()
                        test_result = FunTest.PASSED
                    except TestException:
                        try:
                            test_case.cleanup()
                        except Exception as ex:
                            fun_test.critical(str(ex))
                    except Exception as ex:
                        fun_test.critical(str(ex))
                        try:
                            test_case.cleanup()
                        except Exception as ex:
                            fun_test.critical(str(ex))
                    fun_test._add_xml_trace()
                    fun_test.print_test_case_summary(fun_test.current_test_case_id)
                    fun_test._end_test(result=test_result)
                    if fun_test.suite_execution_id:
                        models_helper.report_test_case_execution_result(execution_id=test_case.execution_id,
                                                                        result=test_result)

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
    def __init__(self,
                 script_obj):
        self.id = None
        self.summary = None
        self.steps = None
        self.script_obj = script_obj

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