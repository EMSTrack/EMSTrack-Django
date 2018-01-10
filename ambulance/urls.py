from django.conf.urls import url, include

from django.contrib.auth.decorators import login_required, permission_required

from . import views

urlpatterns = [

    url(r'^$',
        login_required(views.AmbulanceListView.as_view()),
        name="ambulance"),

    url(r'^ambulance_map$',
        login_required(views.AmbulanceMap.as_view()),
        name="ambulance_map"),
    
    url(r'^ambulance/(?P<pk>\d+)/update/$',
        login_required(views.AmbulanceUpdateView.as_view()),
        name='ambulance_update'),

    # url(r'^status/(?P<pk>\d+)/update/$',
    #     login_required(views.AmbulanceStatusUpdateView.as_view()),
    #     name='status_update'),

    # url(r'^status$',
    #     login_required(views.AmbulanceStatusCreateView.as_view()),
    #     name="status"),

    url(r'^call_list$',
        login_required(views.CallView.as_view()),
        name="call_list"),

    url(r'^admin$',
        login_required(views.AdminView.as_view()),
        name="admin"),
    
]
