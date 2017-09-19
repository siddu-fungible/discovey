from django.contrib import admin
from web.tools.models import Session

class SessionAdmin(admin.ModelAdmin):
    pass

admin.site.register(Session, SessionAdmin)