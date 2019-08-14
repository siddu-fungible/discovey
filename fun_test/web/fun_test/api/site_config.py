from web.fun_test.models import SiteConfig
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
@api_safe_json_response
def site_configs(request):
    result = None
    if request.method == "GET":
        result = {}
        site_config = SiteConfig.objects.all()[0]
        result["version"] = site_config.version
        result["announcement"] = site_config.announcement
        result["announcement_level"] = site_config.announcement_level
    if request.method == "PUT":
        site_config = SiteConfig.objects.all()[0]
        request_json = json.loads(request.body)
        if "announcement" in request_json:
            site_config.announcement = request_json["announcement"]
        if "announcementLevel" in request_json:
            site_config.announcement_level = request_json["announcementLevel"]
        site_config.save()
    return result
