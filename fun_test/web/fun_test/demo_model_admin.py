from django.contrib import admin
from web.fun_test.demo1_models import BgExecutionStatus, LastBgExecution

@admin.register(BgExecutionStatus)
class BgExecutionStatusAdmin(admin.ModelAdmin):
    pass


