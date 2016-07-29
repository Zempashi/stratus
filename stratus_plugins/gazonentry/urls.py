
from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^gazon/?$', views.GazonEntryList.as_view(), name='gazon-list'),
    url(r'^gazon/(?P<pk>[a-zA-Z0-9\.-]+)/?$',
        views.GazonEntryDetail.as_view(), name='gazon-detail'),
    url(r'^gazon/(?P<pk>[a-zA-Z0-9\.-]+)/dhcp/?$',
        views.GazonEntryDHCP.as_view(), name='gazon-dhcp'),
    url(r'^gazonworker', views.run_worker, name='gazon-worker'),
]
