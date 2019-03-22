import json


class SessionLog:
    def __init__(self,
                 method=None,
                 url=None,
                 payload=None,
                 api_data=None):
        self.method = method
        self.url = url
        self.payload = payload
        self.api_data = api_data


def add_session_log(request, data):
    session_log = SessionLog(method=request.method, url=request.build_absolute_uri(), payload=request.body, api_data=data)
    if "logs" not in request.session:
        request.session["logs"] = []
    request.session["logs"].append(json.dumps(session_log.__dict__))
    request.session.save()
