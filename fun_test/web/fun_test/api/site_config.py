from web.fun_test.models import SiteConfig

from web.web_global import api_safe_json_response

@api_safe_json_response
def site_configs(request):
    result = None
    if request.method == "GET":
        result = {}
        site_config = SiteConfig.objects.all()[0]
        result["version"] = site_config.version
        result["announcement"] = site_config.announcement
        result["announcement_level"] = site_config.announcement_level
    if request.method == "POST":
        print(1)

    return result
