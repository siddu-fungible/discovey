from web.fun_test.django_interactive import *
from web.fun_test.models import ReleaseCatalogExecution


rcs = ReleaseCatalogExecution.objects.filter(description="FS1600 Weekly Regression")
for rc in rcs:
    rc.description = "FS1600 Daily regression"
    rc.save()
