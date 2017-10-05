from lib.system.fun_test import fun_test

fun_test.log("Hi")
fun_test.log_section("Hola")
fun_test.critical("peligro")
fun_test.enable_debug()
fun_test.debug("debug statement")
fun_test.disable_debug()

fun_test.log_selected_module("random_module")
fun_test.log("No log")

fun_test.log_selected_module("logging_example")
fun_test.log("Module specific log")
fun_test.log_section("Hola")
fun_test._print_summary()

fun_test.test_assert(2 > 1, "Expression 1")
fun_test.test_assert_expected(actual=3, expected=3, message="Expected Expression")
fun_test.test_assert_expected(actual=5, expected=1, message="Unexpected Expression")

