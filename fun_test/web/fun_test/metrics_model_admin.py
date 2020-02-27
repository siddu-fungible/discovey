from django.contrib import admin
from web.fun_test.metrics_models import Performance1
from web.fun_test.metrics_models import MetricChart
from web.fun_test.metrics_models import ModelMapping, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.metrics_models import LastMetricId
from web.fun_test.metrics_models import WuLatencyUngated, WuLatencyAllocStack
from web.fun_test.metrics_models import UnitTestPerformance, DataPlaneOperationsPerformance
from web.fun_test.metrics_models import EcPerformance, BcopyPerformance, BcopyFloodDmaPerformance
from web.fun_test.metrics_models import LsvZipCryptoPerformance, EcVolPerformance, NuTransitPerformance
from web.fun_test.metrics_models import VoltestPerformance, ShaxPerformance, WuDispatchTestPerformance
from web.fun_test.metrics_models import HuRawVolumePerformance, FunMagentPerformanceTest
from web.fun_test.metrics_models import SoakClassicMallocPerformance, SoakFunMallocPerformance
from web.fun_test.metrics_models import WuStackSpeedTestPerformance, TeraMarkFunTcpThroughputPerformance
from web.fun_test.metrics_models import MetricChartStatus, TeraMarkJuniperNetworkingPerformance
from web.fun_test.metrics_models import WuSendSpeedTestPerformance, BootTimePerformance, FlowTestPerformance, BltVolumePerformance
from web.fun_test.metrics_models import TeraMarkPkeEcdh25519Performance, TeraMarkPkeEcdh256Performance, TeraMarkLookupEnginePerformance
from web.fun_test.metrics_models import TeraMarkPkeRsaPerformance, TeraMarkPkeRsa4kPerformance, TeraMarkCryptoPerformance

@admin.register(Performance1)
class Performance1Admin(admin.ModelAdmin):
    pass


@admin.register(MetricChart)
class MetricChartAdmin(admin.ModelAdmin):
    ordering = ('-metric_id', )


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

@admin.register(WuLatencyAllocStack)
class WuLatencyAllocStackAdmin(admin.ModelAdmin):
    pass

@admin.register(WuLatencyUngated)
class WuLatencyUngatedAdmin(admin.ModelAdmin):
    pass

@admin.register(UnitTestPerformance)
class UnitTestPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(EcPerformance)
class EcPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(BcopyPerformance)
class BcopyPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(BcopyFloodDmaPerformance)
class BcopyFloodDmaPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)


@admin.register(LsvZipCryptoPerformance)
class LsvZipCryptoPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(EcVolPerformance)
class EcVolPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(NuTransitPerformance)
class NuTransitPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)


@admin.register(VoltestPerformance)
class VoltestPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(WuDispatchTestPerformance)
class WuDispatchTestPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(WuSendSpeedTestPerformance)
class WuSendSpeedTestPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(HuRawVolumePerformance)
class HuRawVolumePerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(FunMagentPerformanceTest)
class FunMagentPerformanceTestAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(WuStackSpeedTestPerformance)
class WuStackSpeedTestPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(SoakFunMallocPerformance)
class SoakFunMallocPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(SoakClassicMallocPerformance)
class SoakClassicMallocPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(BootTimePerformance)
class BootTimePerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkPkeEcdh256Performance)
class TeraMarkPkeEcdh256PerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkPkeRsaPerformance)
class TeraMarkPkeRsaPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkPkeRsa4kPerformance)
class TeraMarkPkeRsa4kPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkPkeEcdh25519Performance)
class TeraMarkPkeEcdh25519PerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkCryptoPerformance)
class TeraMarkCryptoPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkLookupEnginePerformance)
class TeraMarkLookupEnginePerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(BltVolumePerformance)
class BltVolumePerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkJuniperNetworkingPerformance)
class TeraMarkJuniperNetworkingPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(TeraMarkFunTcpThroughputPerformance)
class TeraMarkFunTcpThroughputPerformanceeAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(DataPlaneOperationsPerformance)
class DataPlaneOperationsPerformanceAdmin(admin.ModelAdmin):
    ordering = ('-input_date_time',)

@admin.register(ShaxPerformance)
class ShaxPerformanceAdmin(admin.ModelAdmin):
    pass

@admin.register(MetricChartStatus)
class MetricStatusAdmin(admin.ModelAdmin):
    ordering = ('-date_time', '-metric_id')
