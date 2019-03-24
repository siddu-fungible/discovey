from lib.system.fun_test import *
from django.utils.dateparse import parse_datetime
import json
import re
from web.fun_test.analytics_models_helper import MetricHelper
from lib.utilities.performance_excel_parser import PerformanceExcel
from web.fun_test.metrics_models import ShaxPerformance
from datetime import datetime

SHAX_PERF_XLSX = LOGS_DIR + "/shax_perf.xlsx"


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        pass

    def cleanup(self):
        pass


def validate():
    pass


class ShaxPerformanceTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="SHAx performance",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        pe = PerformanceExcel(workbook_filename=SHAX_PERF_XLSX)
        sheet_name = "SHAx"
        data_rows = pe.parse(sheet_name=sheet_name)
        fun_test.test_assert(data_rows, "Data is missing from sheet: {}".format(sheet_name))
        for data_row in data_rows:
            d = {}
            for key, value in data_row.iteritems():
                if value:
                    d[key] = value
            MetricHelper(model=ShaxPerformance).add_entry(**d)

        # fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ShaxPerformanceTc())
    myscript.run()
