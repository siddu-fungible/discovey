from django.db import models


class MetricChart(models.Model):

    data_sets = models.TextField(default="[]")
    chart_name = models.TextField(unique=True)
    metric_model_name = models.TextField(default="Performance1")


class ModelMapping(models.Model):
    module = models.TextField()
    component = models.TextField()
    model_name = models.TextField(default="Performance1", unique=True)

    def __str__(self):
        return "{} {} {}".format(self.model_name, self.module, self.component)


class Performance1(models.Model):
    key = models.CharField(max_length=30, verbose_name="Build no.")
    input1 = models.CharField(max_length=30, choices=[(0, "input1_0"), (1, "input1_1")], verbose_name="Input 1 description")
    input2 = models.IntegerField(choices=[(0, 123), (1, 345)], verbose_name="Input 2 description")
    output1 = models.IntegerField(verbose_name="Output 1 description")
    output2 = models.IntegerField(verbose_name="Output 2 description")
    output3 = models.CharField(max_length=30, verbose_name="Output 3 description")
    module = models.TextField(default="networking")
    component = models.TextField(default="general")


REGISTRANTS = [
    {
        "model": Performance1,
        "model_name": "Performance1",
        "module": "networking",
        "component": "general"
    }

]

