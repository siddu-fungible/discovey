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
from . import common_views
from . import metrics_views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

regression_urls = [
    url(r'^$', regression_views.index),
    url(r'^completed_jobs$', regression_views.completed_jobs),
    url(r'^pending_jobs$', regression_views.pending_jobs),
    url(r'^jenkins_jobs', regression_views.jenkins_jobs),
    url(r'^jobs_by_tag/(.*)$', regression_views.jobs_by_tag),
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
    url(r'^engineers', regression_views.engineers),
    url(r'^update_test_case_execution$', regression_views.update_test_case_execution),
    url(r'^catalog_test_case_execution_summary_result/(.*)/(.*)$',
        regression_views.catalog_test_case_execution_summary_result),
    url(r'^catalog_test_case_execution_summary_result_multiple_jiras$',
        regression_views.catalog_test_case_execution_summary_result_multiple_jiras),
    url(r'^modules$', regression_views.modules),
    url(r'^jenkins_job_id_maps$', regression_views.jenkins_job_id_map),
    url(r'^build_to_date_map$', regression_views.build_to_date_map)
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
    url(r'^execute_catalog', tcm_views.execute_catalog),
    url(r'^catalog_executions/(.*)$', tcm_views.catalog_executions),
    url(r'^catalog_suite_execution_summary/(.*)$', tcm_views.catalog_suite_execution_summary),
    url(r'^catalog_suite_execution_details/(.*)$', tcm_views.catalog_suite_execution_details),
    url(r'^catalog_suite_execution_details_with_jira/(.*)$', tcm_views.catalog_suite_execution_details_with_jira),
    url(r'^catalog_suite_execution_details_page/(.*)$', tcm_views.catalog_suite_execution_details_page),
    url(r'^catalog_execution_add_test_cases$', tcm_views.catalog_execution_add_test_cases),
    url(r'^basic_issue_attributes$', tcm_views.basic_issue_attributes),
    url(r'^module_component_mapping$', tcm_views.module_component_mapping),
    url(r'^set_active_release/(.*)/(.*)$', tcm_views.set_active_release),
    url(r'^releases_page$', tcm_views.releases_page),
    url(r'^releases$', tcm_views.releases),
    url(r'^active_releases$', tcm_views.active_releases),
    url(r'^remove_catalog_test_case_execution/(.*)/(.*)$', tcm_views.remove_catalog_test_case_execution)
]

common_urls = [
    url(r'^alerts_page$', common_views.alerts_page),
    url(r'^add_session_log$', common_views.add_session_log),
    url(r'^get_session_logs$', common_views.get_session_logs),
    url(r'^home$', common_views.home)
]

metric_urls = [
    url(r'^$', metrics_views.index),
    url(r'^metrics_list', metrics_views.metrics_list),
    url(r'^describe_table/(.*)$', metrics_views.describe_table),
    url(r'^chart_list$', metrics_views.chart_list),
    url(r'^charts_info$', metrics_views.charts_info),
    url(r'^chart_info$', metrics_views.chart_info),
    url(r'^data$', metrics_views.data),
    url(r'^charts_by_module$', metrics_views.charts_by_module),
    url(r'^models_by_module$', metrics_views.models_by_module),
    url(r'^edit_chart/(.*)$', metrics_views.edit_chart),
    url(r'^view_all_storage_charts$', metrics_views.view_all_storage_charts),
    url(r'^view_all_system_charts$', metrics_views.view_all_system_charts),
    url(r'^update_chart$', metrics_views.update_chart),
    url(r'^tables/(.*?)/(.*)$', metrics_views.tables),
    url(r'^table_data$', metrics_views.table_data),
    url(r'^summary$', metrics_views.summary_page)
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^publish', views.publish, name='publish'),
    url(r'^get_script_content', views.get_script_content, name='get_script_content'),
    url(r'^tools/', include('tools.urls')),
    url(r'^regression/', include(regression_urls)),
    url(r'^tcm/', include(tcm_urls)),  # related to test-case manangement
    url(r'^metrics/', include(metric_urls)),  # related to metrics, performance statistics
    url(r'^common/', include(common_urls)),
    url(r'^$', common_views.home)

]


urlpatterns += staticfiles_urlpatterns()
