import os, django, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
from web.tools.models import Session, F1, Tg

f1s = [
    {
        "name": "F1",
        "ip": "10.0.0.1"
    },
    {
        "name": "F2",
        "ip": "10.0.0.2"
    },
    {
        "name": "F3",
        "ip": "10.0.0.3"
    }
]


def deploy_topology(session_id):
    print(session_id)
    for f1 in f1s:
        f1_obj = F1(name=f1["name"], ip=f1["ip"])
        try:
            f1_obj.save()
        except Exception as ex:
            print(str(ex))