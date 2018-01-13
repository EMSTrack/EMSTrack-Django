from django.conf.urls import url, include

from django.contrib.auth.decorators import login_required, permission_required

from . import views

app_name = 'hospital'
urlpatterns = [

    url(r'^list/$',
        login_required(views.HospitalListView.as_view()),
        name="list"),

    url(r'^create/$',
        login_required(views.HospitalCreateView.as_view()),
        name="create"),
    
    url(r'^detail/(?P<pk>[0-9]+)$',
        login_required(views.HospitalDetailView.as_view()),
        name="detail"),

    url(r'^update/(?P<pk>[0-9]+)$',
        login_required(views.HospitalUpdateView.as_view()),
        name="update"),
    
]
