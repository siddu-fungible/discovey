from django.conf.urls import url, include

from . import views

f1_urls = [
    url(r'^$', views.f1),
    url(r'^/workflows$', views.workflows),
    url(r'^/workflow/(.*)$', views.workflow),
    url(r'^/start_workflow_step', views.start_workflow_step),
    url(r'^/(.*)/(.*)$', views.metrics),

]

tg_urls = [
    url(r'^$', views.tg),
]

topology_urls = [
    url(r'^$', views.topology)
]

urlpatterns = [
    url(r'^f1', include(f1_urls)),
    url(r'^tg', include(tg_urls)),
    url(r'^topology', include(topology_urls)),
    url(r'^$', views.index)
]
