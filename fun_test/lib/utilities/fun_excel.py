import xlrd
import logging
import sys
from collections import OrderedDict
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


handler = logging.StreamHandler(sys.stdout)
logger.addHandler(hdlr=handler)
logger.setLevel(logging.DEBUG)

FIELDS = OrderedDict()
FIELDS["Jira-Id"] = {}
FIELDS["Id"] = {}
FIELDS["Module"] = {}
FIELDS["Components"] = {}
FIELDS["Test-type"] = {}
FIELDS["Priority"] = {}
FIELDS["Test-bed"] = {}
FIELDS["Summary"] = {}
FIELDS["Setup"] = {}
FIELDS["Steps"] = {}
FIELDS["Expected-result"] = {}
FIELDS["Variations"] = {}
FIELDS["Automatable"] = {}

TEST_CASES_SHEET_NAME = "Test-cases"

ALLOWED_COMPONENTS = ["bgp", "ikv", "crypto", "erasure-coding"]


class TcmsExcel:
    def __init__(self, workbook_filename):
        # self.wb = None
        self.book = None
        self.workbook_filename = workbook_filename
        self.test_cases_sheet = None

    def _open(self):
        try:
            self.book =  xlrd.open_workbook(self.workbook_filename)
            self.test_cases_sheet = self.book.sheet_by_name(TEST_CASES_SHEET_NAME)
            if not self.test_cases_sheet:
                raise Exception("Could not find Sheet {} in workbook".format(TEST_CASES_SHEET_NAME))
        except Exception as ex:
            raise Exception(str(ex))

    def validate(self):
        if not self.test_cases_sheet:
            self._open()

        # validate column header
        header_columns = self.get_columns_by_row(row_index=0)
        expected_fields = FIELDS.keys()
        if not header_columns == expected_fields:
            raise Exception("We expect the column headers (first row) to be in this order: {}".format(str(expected_fields)))


        # Validate each column:
        num_rows = self.test_cases_sheet.nrows
        for row_index in range(1, num_rows):
            columns = self.get_columns_by_row(row_index=row_index)

            # Validate components
            component_value = columns[FIELDS.keys().index("Components")]
            components = [component.strip() for component in component_value.split(",")]
            if not len(components):
                raise Exception("At least one component is required")
            for component in components:
                if not component in ALLOWED_COMPONENTS:
                    raise Exception("Row: {} Component {} not allowed".format(row_index, component))

    def get_columns_by_row(self, row_index):
        cells = self.test_cases_sheet.row_slice(rowx=row_index, start_colx=0, end_colx=len(FIELDS.keys()))
        return [cell.value for cell in cells]

    def pretty_print_test_case(self, row_index):
        columns = self.get_columns_by_row(row_index=row_index)
        headers = FIELDS.keys()
        for i in range(len(headers)):
            print "{}:\n{}\n\n".format(headers[i], columns[i])


if __name__ == "__main__":
    tcms_excel = TcmsExcel(workbook_filename='/Users/johnabraham/Desktop/tcms_format.xlsx')
    tcms_excel.validate()
    tcms_excel.pretty_print_test_case(row_index=1)

