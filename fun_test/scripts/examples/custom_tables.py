from lib.system.fun_test import *

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

class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Description 1",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Custom tables")
        table_data_rows1 = []

        table_data_rows1.append([5, 6, 7])
        table_data_rows1.append([8, 9, 10])
        table_data_rows1.append(["8", "8bps", "9bps"])

        table_data_rows2 = []

        table_data_rows2.append([12, 6, 7])
        table_data_rows2.append([8, 34, 10])
        table_data_rows2.append(["8", "8bps", "9bps"])

        table_data_headers = ["IOPS", "Read B/W", "Write B/W"]
        table_data1 = {"headers": table_data_headers, "rows": table_data_rows1}
        table_data2 = {"headers": table_data_headers, "rows": table_data_rows2}
        fun_test.add_table(panel_header="Performance Table",
                           table_name="Block size = 4k", table_data=table_data1)

        fun_test.add_table(panel_header="Performance Table",
                           table_name="Block size = 6k", table_data=table_data2)



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())

    myscript.run()
