from django.contrib import admin
from web.fun_test.models import SuiteExecution, TestCaseExecution, Tag
from web.fun_test.jira_models import CatalogTestCase, CatalogSuite

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


'''

admin.site.register(SuiteExecution, SuiteExecutionAdmin)
admin.site.register(TestCaseExecution, TestCaseExecutionAdmin)
admin.site.register(Tag, TagAdmin)
'''