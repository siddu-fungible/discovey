from django.conf.urls import url, include

from . import views

f1_urls = [
    url(r'^(\d+)$', views.f1),
    url(r'^workflows$', views.workflows),
    url(r'^traffic_workflows$', views.traffic_workflows),
    url(r'^workflow/(.*)$', views.workflow),
    url(r'^start_workflow_step', views.start_workflow_step),
    url(r'^create_blt_volume/(.*)/(.*)$', views.create_blt_volume),
    url(r'^create_rds_volume/(.*)/(.*)$', views.create_rds_volume),
    url(r'^create_replica_volume/(.*)/(.*)$', views.create_replica_volume),
    url(r'^attach_volume/(.*)/(.*)$', views.attach_volume),
    url(r'^attach_tg/(.*)/(.*)$', views.attach_tg),
    url(r'^set_ip_cfg/(.*)/(.*)$', views.set_ip_cfg),
    url(r'^storage_volumes/(.*)/(.*)$', views.storage_volumes),
    url(r'^storage_stats/(.*)/(.*)$', views.storage_stats),
    url(r'^storage_repvol_stats/(.*)/(.*)$', views.storage_repvol_stats),
    url(r'^(.*)/(.*)$', views.metrics),
    url(r'^detail$', views.f1_details),
    url(r'^upload$', views.upload)
]


tg_urls = [
    url(r'^$', views.tg),
    url(r'^ikv_put/(.*)/(.*)$', views.ikv_put),
    url(r'^ikv_get/(.*)/(.*)/(.*)$', views.ikv_get),
    url(r'^fio/(.*)/(.*)$', views.fio),
    url(r'^traffic_task_status/(.*)$', views.traffic_task_status)
]

topology_urls = [
    url(r'^$', views.topology),
    url(r'^status/(.*)$', views.topology_status),
    url(r'^cleanup$', views.topology_cleanup)
]

urlpatterns = [
    url(r'^f1/', include(f1_urls)),
    url(r'^tg/', include(tg_urls)),
    url(r'^topology/', include(topology_urls)),
    url(r'^$', views.index)
]
