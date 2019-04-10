from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import TestBed


@csrf_exempt
@api_safe_json_response
def test_beds(request, id):
    result = None
    if request.method == "GET":
        all_test_beds = TestBed.objects.all().order_by('name')
        result = []
        for test_bed in all_test_beds:
            result.append(test_bed.to_dict())
    return result
