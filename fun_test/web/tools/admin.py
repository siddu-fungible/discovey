from django.contrib import admin
from web.tools.models import Session, F1, Tg
from web.tools.models import TopologyTask

class SessionAdmin(admin.ModelAdmin):
    pass

class F1Admin(admin.ModelAdmin):
    pass

class TgAdmin(admin.ModelAdmin):
    pass

class TopologyTaskAdmin(admin.ModelAdmin):
    pass

admin.site.register(Session, SessionAdmin)
admin.site.register(F1, F1Admin)
admin.site.register(Tg, TgAdmin)
admin.site.register(TopologyTask, TopologyTaskAdmin)