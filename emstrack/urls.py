from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views

from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view

from login.viewsets import ProfileViewSet
from login.views import PasswordView, SettingsView

from ambulance.viewsets import AmbulanceViewSet, LocationViewSet, \
LocationTypeViewSet, CallViewSet

from hospital.viewsets import HospitalViewSet, HospitalEquipmentViewSet

from .views import IndexView

schema_view = get_swagger_view(title='EMSTrack API')

router = routers.DefaultRouter()

router.register(r'user',
                ProfileViewSet,
                base_name='api-user')

router.register(r'ambulance',
                AmbulanceViewSet,
                base_name='api-ambulance')

router.register(r'location',
                LocationViewSet,
                base_name='api-location')

router.register(r'location/(?P<type>.+)',
                LocationTypeViewSet,
                base_name='api-location-type')

router.register(r'hospital',
                HospitalViewSet,
                base_name='api-hospital')

router.register(r'hospital/(?P<hospital_id>[0-9]+)/equipment',
                HospitalEquipmentViewSet,
                base_name='api-hospital-equipment')

router.register(r'call',
                CallViewSet,
                base_name='api-call')

urlpatterns = [

    # Router API urls
    url(r'^api/', include(router.urls)),
    url(r'^docs/', login_required(schema_view)),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    # Add mqtt_password to api
    url(r'^api/user/(?P<user__username>[\w.@+-]+)/password/$',
        PasswordView.as_view(),
        name='mqtt_password'),

    # Add mqtt_settings to api
    url(r'^api/settings/$',
        SettingsView.as_view(),
        name='mqtt_settings'),
    
    # ambulance
    url(r'^ambulance/', include('ambulance.urls')),

    # ambulance
    url(r'^hospital/', include('hospital.urls')),
    
    # login
    url(r'^auth/', include('login.urls')),

    # admin
    url(r'^admin/', admin.site.urls),
    
    # password change
    url(r'^password_change/$',
        auth_views.PasswordChangeView.as_view(),
        name='password_change'),
    url(r'^password_change/done/$',
        auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),

    # password reset
    url(r'^password_reset/$',
        auth_views.PasswordResetView.as_view(),
        name='password_reset'),
    url(r'^password_reset/done/$',
        auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    url(r'^reset/done/$',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),

    url(r'^$',
        IndexView.as_view(),
        name='index'),

]
