from django.db import models
from web.fun_test.site_state import site_state



class MetricChart(models.Model):

    data_sets = models.TextField(default="[]")
    chart_name = models.TextField(unique=True)
    metric_model_name = models.TextField(default="Performance1")

class Performance1(models.Model):
    key = models.CharField(max_length=30)
    input1 = models.CharField(max_length=30, choices=[(0, "input1_0"), (1, "input1_1")])
    input2 = models.IntegerField(choices=[(0, 123), (1, 345)])
    output1 = models.IntegerField()
    output2 = models.IntegerField()
    output3 = models.CharField(max_length=30)




site_state.register_metric(Performance1, "Performance1")
