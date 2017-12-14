from django.contrib import admin
from web.fun_test.models import SuiteExecution, TestCaseExecution, Tag, Engineer
from web.fun_test.models import CatalogTestCase, CatalogSuite

@admin.register(SuiteExecution)
class SuiteExecutionAdmin(admin.ModelAdmin):
    pass

@admin.register(TestCaseExecution)
class TestCaseExecutionAdmin(admin.ModelAdmin):
    pass

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(CatalogTestCase)
class CatalogTestCaseAdmin(admin.ModelAdmin):
    pass

@admin.register(CatalogSuite)
class CatalogSuiteAdmin(admin.ModelAdmin):
    pass

@admin.register(Engineer)
class EngineerAdmin(admin.ModelAdmin):
    pass