from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from web.fun_test.models import SuiteExecution

def index(request):
    return render(request, 'qa_dashboard/regression.html', locals())


def suite_executions(request):
    data = serializers.serialize("json", SuiteExecution.objects.all())
    return HttpResponse(data)