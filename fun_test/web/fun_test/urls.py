"""web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from . import views, regression_views

regression_urls = [
    url(r'^$', regression_views.index),
    url(r'^suite_executions/(\d+)/(\d+)$', regression_views.suite_executions),
    url(r'^suite_detail/(\d+)$', regression_views.suite_detail),
    url(r'^suite_execution/(\d+)$', regression_views.suite_execution),
    url(r'^suite_executions_count$', regression_views.suite_executions_count),
    url(r'^test_case_execution/(\d+)/(\d+)$', regression_views.test_case_execution),
    url(r'^log_path$', regression_views.log_path),
    url(r'^submit_job_page', regression_views.submit_job_page),
    url(r'^suites$', regression_views.suites)
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^publish', views.publish, name='publish'),
    url(r'^get_script_content', views.get_script_content, name='get_script_content'),
    url(r'^tools/', include('tools.urls')),
    url(r'^regression/', include(regression_urls)),
    url(r'^$', views.index)

]
