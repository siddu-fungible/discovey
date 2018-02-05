from django.db import models
from web.fun_test.site_state import site_state



class MetricChart(models.Model):

    data_sets = models.TextField(default="[]")
    chart_name = models.TextField(unique=True)
    metric_model_name = models.TextField(default="Performance1")

class Performance1(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1 = models.CharField(max_length=30, choices=[(0, "input1_0"), (1, "input1_1")], verbose_name="Input 1 description")
    input2 = models.IntegerField(choices=[(0, 123), (1, 345)], verbose_name="Input 2 description")
    output1 = models.IntegerField(verbose_name="Output 1 description")
    output2 = models.IntegerField(verbose_name="Output 2 description")
    output3 = models.CharField(max_length=30, verbose_name="Output 3 description")




site_state.register_metric(Performance1, "Performance1")
