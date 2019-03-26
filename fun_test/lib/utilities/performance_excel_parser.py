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
import datetime


class PerformanceExcel:
    def __init__(self, workbook_filename):
        self.book = None
        self.workbook_filename = workbook_filename
        self.sheet = None
        self.num_fields = 20
        self.input_choices = {}

    def _open(self, sheet_name):
        try:
            self.book = xlrd.open_workbook(self.workbook_filename)
            self.sheet = self.book.sheet_by_name(sheet_name=sheet_name)
            if not self.sheet:
                raise Exception("Could not find Sheet {} in workbook".format(sheet_name))
        except Exception as ex:
            raise Exception(str(ex))

    def get_columns_by_row(self, row_index):
        cells = self.sheet.row_slice(rowx=row_index, start_colx=0, end_colx=self.num_fields)
        return [cell.value for cell in cells]

    def get_num_rows(self):
        return self.sheet.nrows

    def _find_block(self, block_name):
        schema_block_start_index = -1
        schema_block_end_index = -1
        num_rows = self.get_num_rows()
        row_index = -1
        for row_index in range(num_rows):
            columns = self.get_columns_by_row(row_index=row_index)
            if columns[0] == block_name:
                schema_block_start_index = row_index
            if columns[0] == "End {}".format(block_name):
                schema_block_end_index = row_index
                break
        return (schema_block_start_index, schema_block_end_index)

    def find_schema_block(self):
        return self._find_block(block_name="Schema")

    def find_data_block(self):
        self.data_block_start_index, self.data_block_end_index = self._find_block(block_name="Data")
        return (self.data_block_start_index, self.data_block_end_index)

    def _get_fields(self, block_start_index, block_end_index):
        fields = []
        current_index = block_start_index
        while current_index < block_end_index:
            current_index += 1
            if block_start_index > -1:
                fields = self.get_columns_by_row(row_index=current_index)
                if not any(fields):
                    continue
                else:
                    break

        return [field for field in fields if field], current_index

    def get_schema_fields(self):
        schema_fields, self.schema_fields_index = self._get_fields(*self.find_schema_block())
        return schema_fields

    def get_data_fields(self):
        data_fields, self.data_fields_index = self._get_fields(*self.find_data_block())
        return data_fields

    def get_data_rows_index(self):
        fields_header_index = self.data_fields_index
        data_rows_index = -1
        current_index = fields_header_index + 1
        while current_index < self.data_block_end_index:
            if any(self.get_columns_by_row(row_index=current_index)):
                data_rows_index = current_index
                break
            current_index += 1
        self.data_rows_start_index = data_rows_index
        return data_rows_index

    def parse_schema(self):
        self.schema = {}
        schema_fields = self.get_schema_fields()
        # print schema_fields
        is_input_column_index = 1
        field_column_index = 0
        units_column_index = 2
        description_column_index = 3
        try:
            field_column_index = schema_fields.index("Field")
        except Exception as ex:
            print (str(ex))
        try:
            is_input_column_index = schema_fields.index("Is_input")
        except Exception as ex:
            print (str(ex))
        try:
            units_column_index = schema_fields.index("Units")
        except Exception as ex:
            print (str(ex))
        try:
            description_column_index = schema_fields.index("Description")
        except Exception as ex:
            print (str(ex))

        schema_block_start_index, schema_block_end_index = self.find_schema_block()
        schema_header_row_index = schema_block_start_index + 1
        for row_index in range(schema_header_row_index + 1, schema_block_end_index):
            columns = self.get_columns_by_row(row_index)
            if (columns and not columns[0]) or not columns:
                continue
            field_name = columns[field_column_index]
            is_input = columns[is_input_column_index]
            is_input = True if is_input == 'Y' else False
            description = columns[description_column_index]
            units = columns[units_column_index]
            self.schema[field_name] = {"is_input": is_input, "units": units, "description": description}

    def parse_data(self):
        data_fields = self.get_data_fields()
        self.get_data_rows_index()
        if self.data_rows_start_index < 0:
            raise Exception("Data rows start index is unknown")
        rows = []
        for row_index in range(self.data_rows_start_index, self.data_block_end_index):
            one_row = {}
            columns = self.get_columns_by_row(row_index=row_index)
            if not any(columns):
                continue
            for schema_field in self.schema.keys():
                try:
                    data_field_index = data_fields.index(schema_field)
                    field_name = "input_" + schema_field if self.schema[schema_field]["is_input"] else "output_" + schema_field
                    one_row[field_name] = columns[data_field_index]
                    if field_name == "input_date_time":
                        # print one_row[field_name]
                        year, month, day, hour, minute, second = xlrd.xldate_as_tuple(one_row[field_name],
                                                                                      self.book.datemode)
                        py_date = datetime.datetime(year, month, day, hour, minute, 1)
                        one_row[field_name] = py_date
                    elif field_name.startswith("input_"):
                        self.input_choices.setdefault(field_name, []).append(one_row[field_name])
                except Exception as ex:
                    print (str(ex))
                    print "Could not find index in data header for: {}".format(schema_field)
                    print ("Available data headers: {}".format(data_fields))
                    raise ex
            rows.append(one_row)
        self.data_rows = rows
        return self.data_rows


    def validate_schema_data(self):
        num_schema_fields = self.schema.keys()
        num_data_fields = self.data.keys()

    def parse(self, sheet_name, field_names_row_index=0):
        data_rows = []
        try:
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
            self.parse_schema()
            data_rows = self.parse_data()
        except Exception as ex:
            print str(ex)
        return data_rows

    def pretty_print(self, records):
        print json.dumps(records, indent=4)

    def schema_to_django_model(self, model_name, interpolation_allowed=False):
        rows = []
        for key in self.schema.keys():
            if key == "date_time":
                rows.append("input_date_time = models.DateTimeField(verbose_name=\"Date\", default=datetime.now)")
            else:
                field_name = "input_" + key if self.schema[key]["is_input"] else "output_" + key
                if field_name.startswith("input_") and field_name != "input_date_time":
                    print self.get_choices(field_name=field_name)
                field_units = self.schema[key]["units"]
                units = field_units.strip().lower()
                choices = self.get_choices(field_name)
                choices_str = ""
                if choices:
                    choices_str = ", choices={}".format(json.dumps(choices))
                else:
                    choices_str = ""
                if units == "string".lower():
                    rows.append("{} = models.TextField(verbose_name=\"{}\", default=\"\"{})".format(field_name, self.schema[key]["description"], choices_str))
                elif units == "Gbps".lower():
                    rows.append("{} = models.FloatField(verbose_name=\"{}\", default=-1{})".format(field_name, self.schema[key]["description"], choices_str))
                elif units in ["number", "cycles/block", "ms", "kbps"] :
                    rows.append("{} = models.IntegerField(verbose_name=\"{}\", default=-1{})".format(field_name, self.schema[key]["description"], choices_str))
                else:
                    raise Exception("Unsupported unit: {}".format(units))
        print "class {}(models.Model):".format(model_name)
        for row in rows:
            print "    " + row
        print "    tag = \"analytics\""
        print "    interpolation_allowed = models.BooleanField(default={})".format(interpolation_allowed)
        print "    interpolated = models.BooleanField(default=False)"

    def get_choices(self, field_name):
        choices_list = []
        if field_name in self.input_choices:
            choices = self.input_choices[field_name]
            for choice_index, choice in enumerate(choices):
                choices_list.append((choice_index, choice))
        return choices_list

if __name__ == "__main__":
    workbook_filename = '/Users/ash/Desktop/Integration/fun_test/web/static/logs/hu_performance.xlsx'
    sheet_name = "hu"
    performance_excel = PerformanceExcel(workbook_filename=workbook_filename)
    records = performance_excel.parse(sheet_name=sheet_name, field_names_row_index=10)
    # generic_excel.pretty_print(records)
    # print performance_excel.get_schema_fields()
    performance_excel.parse_schema()
    # print performance_excel.get_schema_fields()
    # print performance_excel.get_data_fields()
    # print performance_excel.parse_data()
    performance_excel.schema_to_django_model(model_name="HuRawVolumePerformance", interpolation_allowed=True)