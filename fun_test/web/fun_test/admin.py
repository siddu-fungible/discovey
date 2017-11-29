from django.contrib import admin
from web.fun_test.models import SuiteExecution, TestCaseExecution, Tag

class SuiteExecutionAdmin(admin.ModelAdmin):
    pass

class TestCaseExecutionAdmin(admin.ModelAdmin):
    pass

class TagAdmin(admin.ModelAdmin):
    pass

admin.site.register(SuiteExecution, SuiteExecutionAdmin)
admin.site.register(TestCaseExecution, TestCaseExecutionAdmin)
admin.site.register(Tag, TagAdmin)