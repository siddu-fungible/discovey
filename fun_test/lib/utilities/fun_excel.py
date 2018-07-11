import xlrd
import logging
import sys
import json
from jira_manager import JiraManager
from collections import OrderedDict
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(hdlr=handler)
logger.setLevel(logging.DEBUG)

FIELDS = OrderedDict()
FIELDS["Jira-Id"] = {}
FIELDS["Test-plan-Id"] = {}
FIELDS["Module"] = {}
FIELDS["Components"] = {}
FIELDS["Test-type"] = {}
FIELDS["Priority"] = {}
FIELDS["Test-bed"] = {}
FIELDS["Summary"] = {}
FIELDS["Setup"] = {}
FIELDS["Description"] = {}
FIELDS["Expected-result"] = {}
FIELDS["Variations"] = {}
FIELDS["Automatable"] = {}

TEST_CASES_SHEET_NAME = "Test-cases"

ALLOWED_COMPONENTS = ["nw-bgp", "nw-isis", "ikv", "crypto", "erasure-coding", "nw-underlay-transit"]


class TcmsExcel:
    def __init__(self, workbook_filename):
        # self.wb = None
        self.book = None
        self.workbook_filename = workbook_filename
        self.test_cases_sheet = None

    def _open(self):
        try:
            self.book = xlrd.open_workbook(self.workbook_filename)
            self.test_cases_sheet = self.book.sheet_by_name(TEST_CASES_SHEET_NAME)
            if not self.test_cases_sheet:
                raise Exception("Could not find Sheet {} in workbook".format(TEST_CASES_SHEET_NAME))
        except Exception as ex:
            raise Exception(str(ex))

    def get_num_rows(self):
        return self.test_cases_sheet.nrows

    def validate(self):
        if not self.test_cases_sheet:
            self._open()

        # validate column header
        header_columns = self.get_columns_by_row(row_index=0)
        expected_fields = FIELDS.keys()
        if not header_columns == expected_fields:
            raise Exception("We expect the column headers (first row) to be in this order: {}".format(str(expected_fields)))


        # fetch allowed components
        jira_manager = JiraManager()
        allowed_components = jira_manager.get_project_component_names()

        # Validate each column:
        num_rows = self.get_num_rows()
        for row_index in range(1, num_rows):
            columns = self.get_columns_by_row(row_index=row_index)

            # Validate components
            component_value = columns[FIELDS.keys().index("Components")]
            components = [component.strip() for component in component_value.split(",")]
            if not len(components):
                raise Exception("At least one component is required")

            for component in components:
                if component not in allowed_components:
                    raise Exception("Row: {} Component {} not allowed. Allowed components: {}".format(row_index, component, allowed_components))

    def get_columns_by_row(self, row_index):
        cells = self.test_cases_sheet.row_slice(rowx=row_index, start_colx=0, end_colx=len(FIELDS.keys()))
        return [cell.value for cell in cells]

    def pretty_print_test_case(self, row_index):
        columns = self.get_columns_by_row(row_index=row_index)
        headers = FIELDS.keys()
        for i in range(len(headers)):
            print "{}:\n{}\n\n".format(headers[i], columns[i])

    def get_value_from_row_by_key(self, row, key):
        result = None
        FIELDS_keys = FIELDS.keys()
        if not key in FIELDS_keys:
            raise Exception("Key: {} not found in FIELDS".format(key))
        index_of_key = FIELDS_keys.index(key)
        if index_of_key < len(row):
            result = row[index_of_key]
        else:
            raise Exception("Index of key exceeds columns on row")
        return result


class PerformanceExcel:
    def __init__(self, workbook_filename):
        self.book = None
        self.workbook_filename = workbook_filename
        self.sheet = None

    def _open(self, sheet_name):
        try:
            self.book = xlrd.open_workbook(self.workbook_filename)
            self.sheet = self.book.sheet_by_name(sheet_name=sheet_name)
            if not self.sheet:
                raise Exception("Could not find Sheet {} in workbook".format(sheet_name))
        except Exception as ex:
            raise Exception(str(ex))

    def get_columns_by_row(self, row_index):
        cells = self.sheet.row_slice(rowx=row_index, start_colx=0, end_colx=len(FIELDS.keys()))
        return [cell.value for cell in cells]

    def get_num_rows(self):
        return self.sheet.nrows

    def parse(self, sheet_name, field_names_row_index=0):
        self._open(sheet_name=sheet_name)
        num_rows = self.get_num_rows()
        fields = self.get_columns_by_row(field_names_row_index)

        records = []

        for row_index in range(field_names_row_index + 1, num_rows):
            columns = self.get_columns_by_row(row_index=row_index)
            one_record = {}
            for index, field in enumerate(fields):
                one_record[field] = columns[index]
            records.append(one_record)

        return (fields, records)

    def pretty_print(self, records):
        print json.dumps(records, indent=4)


if __name__ == "__main__":
    workbook_filename = '/Users/johnabraham/Desktop/zip_example_perf.xlsx'
    sheet_name = "Sheet1"
    generic_excel = PerformanceExcel(workbook_filename=workbook_filename)
    fields, records = generic_excel.parse(sheet_name=sheet_name, field_names_row_index=9)
    generic_excel.pretty_print(records)

'''
if __name__ == "__main2__":
    tcms_excel = TcmsExcel(workbook_filename='/Users/johnabraham/Desktop/tcms_format.xlsx')
    tcms_excel.validate()
    tcms_excel.pretty_print_test_case(row_index=1)

'''