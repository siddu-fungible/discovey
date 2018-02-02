from django.db import models
from web.fun_test.site_state import site_state


class Performance1(models.Model):
    key = models.CharField(max_length=30)
    input1 = models.CharField(max_length=30)
    input2 = models.IntegerField()
    output1 = models.IntegerField()
    output2 = models.IntegerField()
    output3 = models.CharField(max_length=30)


site_state.register_metric(Performance1)
