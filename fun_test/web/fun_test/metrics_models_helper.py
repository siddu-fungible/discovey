import os
import django
from web.web_global import PRIMARY_SETTINGS_FILE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1
from web.fun_test.site_state import *


class MetricHelper(object):
    def __init__(self, model):
        self.model = model

    def delete(self, key):
        entries = self.model.objects.filter(key=key)
        for entry in entries:
            entry.delete()
            entry.save()

    def clear(self):
        self.model.objects.all().delete()


class Performance1Helper(MetricHelper):
    model = Performance1

    def __init__(self):
        super(Performance1Helper, self).__init__(model=self.model)

    def add_entry(self, key, input1, input2, output1, output2, output3):
        one_entry = Performance1(key=key,
                                 input1=input1,
                                 input2=input2,
                                 output1=output1,
                                 output2=output2,
                                 output3=output3)
        one_entry.save()


if __name__ == "__main__":
    performance1_helper = Performance1Helper()
    performance1_helper.clear()
    performance1_helper.add_entry(key="123", input1="input1", input2=12, output1=34, output2=56, output3="output3_1")
    performance1_helper.add_entry(key="123", input1="input1", input2=12, output1=30, output2=71, output3="output3_2")
    performance1_helper.add_entry(key="123", input1="input1", input2=12, output1=44, output2=5, output3="output3_3")

