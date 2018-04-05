from django.contrib import admin
from web.fun_test.metrics_models import Performance1
from web.fun_test.metrics_models import MetricChart
from web.fun_test.metrics_models import ModelMapping, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.metrics_models import LastMetricId


@admin.register(Performance1)
class Performance1Admin(admin.ModelAdmin):
    pass


@admin.register(MetricChart)
class MetricChartAdmin(admin.ModelAdmin):
    pass


@admin.register(ModelMapping)
class ModelMappingAdmin(admin.ModelAdmin):
    pass


@admin.register(VolumePerformance)
class VolumePerformanceAdmin(admin.ModelAdmin):
    pass


@admin.register(AllocSpeedPerformance)
class AllocSpeedPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(LastMetricId)
class LastMetricIdAdmin(admin.ModelAdmin):
    pass
