from django.contrib import admin
from web.tools.models import Session, F1, Tg

class SessionAdmin(admin.ModelAdmin):
    pass

class F1Admin(admin.ModelAdmin):
    pass

class TgAdmin(admin.ModelAdmin):
    pass

admin.site.register(Session, SessionAdmin)
admin.site.register(F1, F1Admin)
admin.site.register(Tg, TgAdmin)