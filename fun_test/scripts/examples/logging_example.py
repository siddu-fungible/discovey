from lib.system.fun_test import fun_test

fun_test.log("Hi")
fun_test.log_section("Section Heading")

fun_test.critical("peligro")
fun_test.enable_debug()
fun_test.debug("debug statement")
fun_test.disable_debug()

fun_test.log_module_filter("random_module")
fun_test.log("No log")
fun_test.log_module_filter("logging_example")
fun_test.log("Module specific log")
fun_test.log_module_filter_disable()


d = {}
d["Attribute1"] = "Value1"
d[2] = "Value2"
d["Attr3"] = "ValueThree"
fun_test.print_key_value(title="Attribute Value Table", data=d)

fun_test.log_disable_timestamps()
fun_test.log("Without Timestamp")

fun_test.log_enable_timestamps()


def some_func():
    fun_test.enable_debug()
    fun_test.set_log_format(function_name=True)
    fun_test.debug("Inside function")
    fun_test.disable_debug()
    fun_test.set_log_format(function_name=False)


some_func()

fun_test.test_assert(2 > 1, "Expression 1")
fun_test.test_assert_expected(actual=3, expected=3, message="Expected Expression")
fun_test.test_assert_expected(actual=5, expected=1, message="Unexpected Expression")

