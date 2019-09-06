from web.fun_test.django_interactive import *
from lib.system.fun_test import *
from web.fun_test.metrics_lib import *

ml = MetricLib()


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""

        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class PerformanceTc(FunTestCase):
    workspace_ids = [1480]

    def setup(self):
        pass

    def cleanup(self):
        pass


class EmailPerformanceDrop(PerformanceTc):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Email performance drops from various/selected workspaces",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def run(self):
        status = fun_test.PASSED
        for workspace_id in self.workspace_ids:
            email = ml._get_email_address(workspace_id=workspace_id)
            reports = ml._generate_report(workspace_id=workspace_id)
            if len(reports):
                print reports
                status = fun_test.FAILED
                subject = "Performance drop report - " + str(get_current_time())
                try:
                    data = ml._send_email(email=email, subject=subject, reports=reports,
                                          report_name="performance_drop_report.html")
                    if not data.status:
                        raise Exception("sending email failed to - {}".format(email))
                    else:
                        print "sent email successfully to - {}".format(email)
                except Exception as ex:
                    status = fun_test.FAILED
                    fun_test.critical(str(ex))
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=status, message="No degraded metrics")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(EmailPerformanceDrop())
    myscript.run()
