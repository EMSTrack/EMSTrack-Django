from django.conf.urls import url
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, permission_required

from . import views

urlpatterns = [

    url(r'^update_ambulance/(?P<pk>[0-9]+)$',
        views.AmbulanceUpdateView.as_view(),
        name="ambulance_update"),

    url(r'^create_ambulance$',
        views.AmbulanceCreateView.as_view(),
        name="ambulance_create"),

    url(r'^create_reporter$', 
        views.ReporterCreateView.as_view(),
        name="reporter_create"),

    url(r'^ambulance_info/(?P<pk>[0-9]+)$',
        views.AmbulanceInfoView.as_view(),
        name="ambulance_info"),

    url(r'^ambulance_view$',
        views.AmbulanceView.as_view(),
        name="ambulance_view"),

    url(r'^all_ambulances',
        views.AllAmbulancesView.as_view(),
        name="all_ambulance")
]
