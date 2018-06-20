from django.contrib import admin
from web.fun_test.models import SuiteExecution, TestCaseExecution, Tag, Engineer
from web.fun_test.models import CatalogTestCase, CatalogSuite, CatalogSuiteExecution
from web.fun_test.models import CatalogTestCaseExecution
from web.fun_test.models import TestBed
from web.fun_test.models import Module, JenkinsJobIdMap
from web.fun_test.metrics_model_admin import *
from web.fun_test.models import LastSuiteExecution, LastTestCaseExecution

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

@admin.register(CatalogSuiteExecution)
class CatalogSuiteExecutionAdmin(admin.ModelAdmin):
    pass

@admin.register(TestBed)
class TestBedAdmin(admin.ModelAdmin):
    pass

@admin.register(CatalogTestCaseExecution)
class CatalogTestCaseExecutionAdmin(admin.ModelAdmin):
    pass

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    pass

@admin.register(JenkinsJobIdMap)
class JenkinsJobIdMapAdmin(admin.ModelAdmin):
    pass

@admin.register(LastSuiteExecution)
class LastSuiteExecutionAdmin(admin.ModelAdmin):
    pass

@admin.register(LastTestCaseExecution)
class LastTestCaseExecutionAdmin(admin.ModelAdmin):
    pass
