from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.authtoken.views import obtain_auth_token

from login import views

app_name = 'login'
urlpatterns = [

    # login/logout
    url(r'^login/$',
        views.LoginView.as_view(),
        name='login'),
    url(r'^logout/$',
        views.LogoutView.as_view(),
        name='logout'),

    # signup
    url(r'^signup/$',
        views.SignupView.as_view(),
        name='signup'),
    
    # User Admin
    
    url(r'^user/$',
        staff_member_required(views.UserAdminListView.as_view()),
        name='list-user'),

    url(r'^user/create/$',
        staff_member_required(views.UserAdminCreateView.as_view()),
        name='create-user'),

    url(r'^user/detail/(?P<pk>[0-9]+)$',
        staff_member_required(views.UserAdminDetailView.as_view()),
        name='detail-user'),

    url(r'^user/update/(?P<pk>[0-9]+)$',
        staff_member_required(views.UserAdminUpdateView.as_view()),
        name='update-user'),

    url(r'^user/export/$',
        staff_member_required(views.user_export),
        name='export-user'),

    # Group Admin

    url(r'^group/$',
        staff_member_required(views.GroupAdminListView.as_view()),
        name='list-group'),

    url(r'^group/create/$',
        staff_member_required(views.GroupAdminCreateView.as_view()),
        name='create-group'),

    url(r'^group/detail/(?P<pk>[0-9]+)$',
        staff_member_required(views.GroupAdminDetailView.as_view()),
        name='detail-group'),

    url(r'^group/update/(?P<pk>[0-9]+)$',
        staff_member_required(views.GroupAdminUpdateView.as_view()),
        name='update-group'),

    # client admin
    url(r'^client/$',
        staff_member_required(views.ClientListView.as_view()),
        name='list-client'),

    url(r'^client/detail/(?P<pk>[0-9]+)$',
        staff_member_required(views.ClientDetailView.as_view()),
        name='detail-client'),

    url(r'^client/logout/(?P<pk>\d+)$',
        staff_member_required(views.ClientLogoutView.as_view()),
        name='logout-client'),

    # restart

    url(r'^restart/$',
        staff_member_required(views.RestartView.as_view()),
        name='restart'),

    # rest token
    url(r'^token/$', obtain_auth_token),

    # mqtt login
    
    url(r'^mqtt/login/$',
        views.MQTTLoginView.as_view(),
        name='login-mqtt'),
    url(r'^mqtt/superuser/$',
        views.MQTTSuperuserView.as_view(),
        name='superuser-mqtt'),
    url(r'^mqtt/acl/$',
        views.MQTTAclView.as_view(),
        name='acl-mqtt'),
    
]
