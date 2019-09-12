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
    workspaces = [{"id": 1912, "extra_email": ["storage-test@fungible.com", "harinadh.saladi@fungible.com"]},
                     {"id": 2088, "extra_email": ["mohit.saxena@fungible.com"]}]
    regression_email = TEAM_REGRESSION_EMAIL

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
        for workspace in self.workspaces:
            # email = ml._get_email_address(workspace_id=workspace["id"])
            email_list = []
            email_list.append(self.regression_email)
            email_list.extend(workspace["extra_email"])
            reports = ml._generate_report(workspace_id=workspace["id"])
            if len(reports):
                print reports
                status = fun_test.FAILED
                date_time = time.strftime("%m/%d/%Y %H:%M")
                subject = "Performance drop report - " + date_time
                try:
                    data = ml._send_email(email=email_list, subject=subject, reports=reports,
                                          report_name="performance_drop_report.html")
                    if not data["status"]:
                        raise Exception("sending email failed to - {}".format(email_list))
                    else:
                        print "sent email successfully to - {}".format(email_list)
                except Exception as ex:
                    status = fun_test.FAILED
                    fun_test.critical(str(ex))
        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=status, message="No degraded metrics")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(EmailPerformanceDrop())
    myscript.run()
