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
from . import tests_views
from . import upgrade_views
from . import demo_views
from . import triaging
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from fun_global import is_development_mode

regression_urls = [
    url(r'^$', views.angular_home),
    url(r'^completed_jobs$', views.angular_home),
    url(r'^pending_jobs$', views.angular_home),
    url(r'^jenkins_jobs', views.angular_home),
    url(r'^jobs_by_tag/(.*)$', regression_views.jobs_by_tag),
    url(r'^suite_executions/(\d+)/(\d+)/(.*)$', regression_views.suite_executions),
    url(r'^suite_detail/(\d+)$', regression_views.suite_detail),
    url(r'^suite_execution/(\d+)$', regression_views.suite_execution),
    url(r'^suite_execution_attributes/(\d+)$', regression_views.suite_execution_attributes),
    url(r'^suite_executions_count/(.*)$', regression_views.suite_executions_count),
    url(r'^test_case_execution/(\d+)/(\d+)$', regression_views.test_case_execution),
    url(r'^suite_re_run/(\d+)$', regression_views.suite_re_run),
    url(r'^test_case_re_run$', regression_views.test_case_re_run),
    url(r'^log_path$', regression_views.log_path),
    url(r'^submit_job_page', views.angular_home),
    url(r'^submit_job$', regression_views.submit_job),
    url(r'^suites$', regression_views.suites),
    url(r'^static_serve_log_directory/(\d+)$', regression_views.static_serve_log_directory),
    url(r'^kill_job/(\d+)$', regression_views.kill_job),
    url(r'^tags$', regression_views.tags),
    url(r'^engineers', regression_views.engineers),
    url(r'^update_test_case_execution$', regression_views.update_test_case_execution),
    url(r'^catalog_test_case_execution_summary_result/(.*)/(.*)$',
        regression_views.catalog_test_case_execution_summary_result),
    url(r'^catalog_test_case_execution_summary_result_multiple_jiras$',
        regression_views.catalog_test_case_execution_summary_result_multiple_jiras),
    url(r'^modules$', regression_views.modules),
    url(r'^jenkins_job_id_maps$', regression_views.jenkins_job_id_map),
    url(r'^build_to_date_map$', regression_views.build_to_date_map),
    url(r'^sampler$', regression_views.sampler),
    url(r'^sampler2$', regression_views.sampler2),
    url(r'^scripts_by_module/(.*)$', regression_views.scripts_by_module),
    url(r'^get_suite_execution_properties', regression_views.get_suite_execution_properties),
    url(r'^get_all_versions', regression_views.get_all_versions),
    url(r'^get_script_history', regression_views.get_script_history),
    url(r'^scripts$', regression_views.scripts),
    url(r'^unallocated_script$', regression_views.unallocated_script),
    url(r'^script$', regression_views.script),
    url(r'^script_update/(\d+)$', regression_views.script_update),
    url(r'^get_suite_executions_by_time$', regression_views.get_suite_executions_by_time),
    url(r'^get_test_case_executions_by_time$', regression_views.get_test_case_executions_by_time),
    url(r'^all_jiras$', regression_views.all_regression_jiras),
    url(r'^jiras/(\d+)/?(.*)?$', regression_views.jiras),
    url(r'^script_execution/(\d+)$', regression_views.script_execution),
    url(r'^job_spec/(\d+)$', regression_views.job_spec),
    url(r'^re_run_info$', regression_views.re_run_info),
    url(r'^scheduler/admin$', views.angular_home),
    url(r'^scheduler/queue$', regression_views.scheduler_queue),
    url(r'^scheduler/queue_priorities$', regression_views.scheduler_queue_priorities),
    url(r'^scheduler/.*$', views.angular_home),
    url(r'^test_case_execution_info/(\d+)$', regression_views.test_case_execution_info),
    url(r'^git$', regression_views.git),
    url(r'^testbeds$', regression_views.testbeds),
    url(r'^(?:\S+)$', views.angular_home)

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
    url(r'^time_keeper/(.*)$', common_views.time_keeper),
    url(r'^alerts', views.angular_home),
    url(r'^logs$', views.angular_home),
    url(r'^add_session_log$', common_views.add_session_log),
    url(r'^get_session_logs$', common_views.get_session_logs),
    url(r'^home$', common_views.home),
    url(r'^bug_info$', common_views.bug_info)
]

metric_urls = [
    url(r'^$', metrics_views.index),
    url(r'^get_leaves', metrics_views.get_leaves),
    url(r'^metrics_list', metrics_views.metrics_list),
    url(r'^describe_table/(.*)$', metrics_views.describe_table),
    url(r'^chart_list$', metrics_views.chart_list),
    url(r'^charts_info$', metrics_views.charts_info),
    url(r'^chart_info$', metrics_views.chart_info),
    url(r'^data$', metrics_views.data),
    url(r'^past_status$', metrics_views.get_past_build_status),
    url(r'^first_degrade$', metrics_views.get_first_degrade),
    url(r'^data_by_model$', metrics_views.get_data_by_model),
    url(r'^metric_by_id$', metrics_views.metric_by_id),
    url(r'^git_commits$', metrics_views.get_git_commits),
    url(r'^status$', metrics_views.status),
    url(r'^charts_by_module$', metrics_views.charts_by_module),
    url(r'^models_by_module$', metrics_views.models_by_module),
    url(r'^edit_chart/(.*)$', metrics_views.edit_chart),
    url(r'^view_all_storage_charts$', metrics_views.view_all_storage_charts),
    url(r'^view_all_system_charts$', metrics_views.view_all_system_charts),
    url(r'^update_chart$', metrics_views.update_chart),
    url(r'^tables/(.*?)/(\d+)$', metrics_views.tables),
    url(r'^table_data$', metrics_views.table_data),
    # url(r'^summary$', metrics_views.summary_page),
    url(r'^metric_info$', metrics_views.metric_info),
    url(r'^atomic/(.*)/(.*)$', metrics_views.atomic),
    url(r'^score_table/(\d+)$', metrics_views.score_table),
    url(r'^update_child_weight$', metrics_views.update_child_weight),
    url(r'^table_view/(.*)$', metrics_views.table_view),
    url(r'^test$', metrics_views.test),
    url(r'^scores', metrics_views.scores),
    url(r'^dag$', metrics_views.dag),
    url(r'^get_triage_info$', metrics_views.get_triage_info),
    url(r'^get_triage_info_from_commits$', metrics_views.get_triage_info_from_commits),
    url(r'^global_settings', metrics_views.global_settings),
    url(r'^jiras/(\d+)/?(.*)?$', metrics_views.jiras)
]

test_urls = [
    url(r'^datetime$', tests_views.date_test),
    url(r'^bg$', tests_views.bg),
    url(r'^crash$', tests_views.crash)

]

upgrade_urls = [
    url(r'^.*$', upgrade_views.home)
]

triage_urls = [
    url(r'^insert_db$', triaging.insert_triage_db),
    url(r'^fetch_flows$', triaging.fetch_triage_flow),
    url(r'^test$', triaging.update_triage_flow),
    url(r'^update_db$', triaging.update_triage),
    url(r'^kill_db$', triaging.kill_triage),
    url(r'^rerun_flow$', triaging.rerun_triage_flow),
    url(r'^check_db$', triaging.check_triage)
]

demo_urls = [
    url(r'^demo1/.*$', demo_views.home),
    url(r'^schedule_fio_job$', demo_views.schedule_fio_job),
    url(r'^bg_job_status$', demo_views.job_status),
    url(r'^add_controller$', demo_views.add_controller),
    url(r'^set_controller_status$', demo_views.set_controller_status),
    url(r'^get_controllers$', demo_views.get_controllers),
    url(r'^get_container_logs', demo_views.get_container_logs)
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^performance/', views.angular_home),
    url(r'^publish', views.publish, name='publish'),
    url(r'^get_script_content', views.get_script_content, name='get_script_content'),
    # url(r'^tools/', include('tools.urls')),
    url(r'^regression/', include(regression_urls)),
    url(r'^tcm/', include(tcm_urls)),  # related to test-case manangement
    url(r'^metrics/', include(metric_urls)),  # related to metrics, performance statistics
    url(r'^triage/', include(triage_urls)),
    url(r'^triaging/', views.angular_home),
    url(r'^common/', include(common_urls)),
    url(r'^$', views.angular_home),
    url(r'^initialize$', metrics_views.initialize),
    url(r'^test/', include(test_urls)),
    url(r'^upgrade/', include(upgrade_urls)),
    url(r'^demo/', include(demo_urls)),
    url(r'^(?P<path>font.*$)', RedirectView.as_view(url='/static/%(path)s'))

]

urlpatterns += staticfiles_urlpatterns()
