import json
import xlsxwriter

class Field:
    def __init__(self, is_input, field_name, verbose_field_name):
        self.is_input = is_input
        self.field_name = field_name
        self.verbose_field_name = verbose_field_name

    def __eq__(self, other):
        return other == self.field_name

class GenericMetric():

    def __init__(self):
        self.fields = []
        self.records = []
        self.__exported__ = {"records": self.records}

    def describe_field(self, is_input, field_name, verbose_field_name):
        self.fields.append(Field(is_input=is_input, field_name=field_name, verbose_field_name=verbose_field_name))

    def add_record(self, **kwargs):

        input_keys = kwargs.keys()
        expected_keys = [x.field_name for x in self.fields]
        keys_to_remove = []
        for index, input_key in enumerate(input_keys):
            if input_key not in expected_keys:
                raise Exception("{0} is not a valid field. Did you use describe_fields for {0}?".format(input_key))
            keys_to_remove.append(input_key)
        for key_to_remove in keys_to_remove:
            input_keys.remove(key_to_remove)
            expected_keys.remove(key_to_remove)
        for remaining_key in expected_keys:
            raise (Exception("Field: {0} not provided".format(remaining_key)))
        self.records.append(kwargs)

    def to_json(self):
        return self.__exported__

    def to_excel(self, filename="output.xlsx", sheet_name="sheet1"):
        # Header
        workbook = xlsxwriter.Workbook(filename)
        format = workbook.add_format({'text_wrap': True})
        worksheet = workbook.add_worksheet(name=sheet_name)

        for column_index, field in enumerate(self.fields):
            worksheet.write(0, column_index, field.verbose_field_name)

        # rows
        for row_index, row in enumerate(self.records):
            for column_index, field in enumerate(self.fields):
                worksheet.write(row_index + 1, column_index, row[field.field_name])
        workbook.close()

if __name__ == "__main__":
    my_metric = GenericMetric()

    my_metric.describe_field(is_input=True, field_name="key", verbose_field_name="Build number")
    my_metric.describe_field(is_input=True, field_name="input1", verbose_field_name="Input 1")
    my_metric.describe_field(is_input=True, field_name="input2", verbose_field_name="Input 2")
    my_metric.describe_field(is_input=False, field_name="output1", verbose_field_name="Output 1")

    my_metric.add_record(key=543, input1="Some input1", input2="Some input2", output1="Some output")
    my_metric.add_record(key=544, input1="Some input2", input2="Some input232", output1="Some output4224")

    print json.dumps(my_metric.to_json(), indent=4)
    my_metric.to_excel()