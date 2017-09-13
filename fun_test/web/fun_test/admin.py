from django.contrib import admin
from web.fun_test.models import SuiteExecution, TestCaseExecution

class SuiteExecutionAdmin(admin.ModelAdmin):
    pass

class TestCaseExecutionAdmin(admin.ModelAdmin):
    pass

admin.site.register(SuiteExecution, SuiteExecutionAdmin)
admin.site.register(TestCaseExecution, TestCaseExecutionAdmin)