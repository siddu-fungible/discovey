from django.contrib import admin
from web.fun_test.metrics_models import Performance1


@admin.register(Performance1)
class Performance1Admin(admin.ModelAdmin):
    pass
