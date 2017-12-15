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
from . import tcm_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

regression_urls = [
    url(r'^$', regression_views.index),
    url(r'^completed_jobs$', regression_views.completed_jobs),
    url(r'^pending_jobs$', regression_views.pending_jobs),
    url(r'^jenkins_jobs', regression_views.jenkins_jobs),
    url(r'^suite_executions/(\d+)/(\d+)/(.*)$', regression_views.suite_executions),
    url(r'^suite_detail/(\d+)$', regression_views.suite_detail),
    url(r'^suite_execution/(\d+)$', regression_views.suite_execution),
    url(r'^last_jenkins_hourly_execution_status', regression_views.last_jenkins_hourly_execution_status),
    url(r'^suite_executions_count/(.*)$', regression_views.suite_executions_count),
    url(r'^test_case_execution/(\d+)/(\d+)$', regression_views.test_case_execution),
    url(r'^suite_re_run/(\d+)$', regression_views.suite_re_run),
    url(r'^test_case_re_run$', regression_views.test_case_re_run),
    url(r'^log_path$', regression_views.log_path),
    url(r'^submit_job_page', regression_views.submit_job_page),
    url(r'^submit_job$', regression_views.submit_job),
    url(r'^suites$', regression_views.suites),
    url(r'^static_serve_log_directory/(\d+)$', regression_views.static_serve_log_directory),
    url(r'^kill_job/(\d+)$', regression_views.kill_job),
    url(r'^tags', regression_views.tags),
    url(r'^engineers', regression_views.engineers)
]

tcm_urls = [
    url(r'^$', tcm_views.index),
    url(r'^create_catalog_page', tcm_views.create_catalog_page),
    url(r'^create_catalog', tcm_views.create_catalog),
    url(r'^view_catalog_page/(.*)$', tcm_views.view_catalog_page),
    url(r'^catalog/(.*)$', tcm_views.catalog),
    url(r'^update_catalog', tcm_views.update_catalog),
    url(r'^preview_catalog', tcm_views.preview_catalog),
    url(r'^view_catalogs', tcm_views.view_catalogs),
    url(r'^catalog_categories$', tcm_views.catalog_categories),
    url(r'^catalogs_summary$', tcm_views.catalogs_summary),
    url(r'^remove_catalog/(.*)$', tcm_views.remove_catalog),
    url(r'^execute_catalog/(.*)$', tcm_views.execute_catalog)
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^publish', views.publish, name='publish'),
    url(r'^get_script_content', views.get_script_content, name='get_script_content'),
    url(r'^tools/', include('tools.urls')),
    url(r'^regression/', include(regression_urls)),
    url(r'^tcm/', include(tcm_urls)), # urls related to test-case manangement
    url(r'^$', views.index)

]

urlpatterns += staticfiles_urlpatterns()