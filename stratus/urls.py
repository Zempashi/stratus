"""stratus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^/?$', views.api_root),
    url(r'^vms/?$', views.VMList.as_view(), name='vm-list'),
    url(r'^vms/(?P<pk>[a-zA-Z0-9\.-]+)/?$', views.VMDetail.as_view(), name='vm-detail'),
    url(r'^vms/(?P<pk>[a-zA-Z0-9\.-]+)/full/?$', views.VMDetail.as_view(), {'full': True}, name='vm-full'),
    url(r'^hkvms/?$', views.HKVMList.as_view(), name='hkvm-list'),
    url(r'^hkvms/(?P<pk>[0-9]+)/?$', views.HKVMDetail.as_view(), name='hkvm-detail'),
    url(r'^hkvms/(?P<pk>[0-9]+)/full/?$', views.HKVMDetail.as_view(), {'full': True}, name='hkvm-full'),
]
