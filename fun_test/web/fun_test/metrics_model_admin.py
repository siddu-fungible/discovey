from django.contrib import admin
from web.fun_test.metrics_models import Performance1
from web.fun_test.metrics_models import MetricChart
from web.fun_test.metrics_models import ModelMapping


@admin.register(Performance1)
class Performance1Admin(admin.ModelAdmin):
    pass


@admin.register(MetricChart)
class MetricChartAdmin(admin.ModelAdmin):
    pass


@admin.register(ModelMapping)
class ModelMappingAdmin(admin.ModelAdmin):
    pass
