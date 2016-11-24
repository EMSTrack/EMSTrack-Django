from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^update/(?P<pk>[0-9]+)$',
        views.AmbulanceUpdateView.as_view(),
        name="ambulance_update"),

    url(r'^info/(?P<pk>[0-9]+)$',
        views.AmbulanceInfoView.as_view(),
        name="ambulance_info"),

    url(r'^ambulance_create$',
    	views.AmbulanceCreateView.as_view(),
    	name="ambulance_create"),
]
