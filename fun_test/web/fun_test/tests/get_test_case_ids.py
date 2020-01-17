from web.fun_test.django_interactive import *
from web.fun_test.models import Suite

suites = Suite.objects.all()
for s in suites:
    for entry in s.entries:
        if "s1_teramarks" in entry["script_path"]:
            print entry["script_path"]
            if "test_case_ids" in entry:
                print entry["test_case_ids"], s.name