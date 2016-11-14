from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^update/(?P<pk>[0-9]+)$',
        views.AmbulanceUpdateView.as_view(),
        name="ambulance_update"),
]
