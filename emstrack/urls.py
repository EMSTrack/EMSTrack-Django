from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

from rest_framework import routers, permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from login.decorator import login_required
from login.viewsets import ProfileViewSet, ClientViewSet
from login.views import PasswordView, SettingsView, VersionView

from ambulance.viewsets import AmbulanceEquipmentItemViewSet, AmbulanceViewSet, \
    LocationViewSet, LocationTypeViewSet, CallViewSet, CallPriorityViewSet, \
    CallRadioViewSet, AmbulanceCallWaypointViewSet, CallNoteViewSet

from hospital.viewsets import HospitalViewSet, HospitalEquipmentItemViewSet
from equipment.viewsets import EquipmentItemViewSet, EquipmentViewSet

from .views import IndexView

# schema_view = get_swagger_view(title='EMSTrack API')
schema_view = get_schema_view(
   openapi.Info(
       title="EMSTrack API",
       default_version='v1',
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()

router.register(r'user',
                ProfileViewSet,
                basename='api-user')

router.register(r'ambulance',
                AmbulanceViewSet,
                basename='api-ambulance')

router.register(r'ambulance/(?P<ambulance_id>[0-9]+)/equipment',
                AmbulanceEquipmentItemViewSet,
                basename='api-ambulance-equipment')

router.register(r'location',
                LocationViewSet,
                basename='api-location')

router.register(r'location/(?P<type>.+)',
                LocationTypeViewSet,
                basename='api-location-type')

router.register(r'hospital',
                HospitalViewSet,
                basename='api-hospital')

router.register(r'hospital/(?P<hospital_id>[0-9]+)/equipment',
                HospitalEquipmentItemViewSet,
                basename='api-hospital-equipment')

router.register(r'equipment/(?P<equipmentholder_id>[0-9]+)/item',
                EquipmentItemViewSet,
                basename='api-equipment')

router.register(r'equipment',
                EquipmentViewSet,
                basename='api-equipment-metadata')

router.register(r'call',
                CallViewSet,
                basename='api-call')

router.register(r'call/(?P<call_id>[0-9]+)/note',
                CallNoteViewSet,
                basename='api-call-note')

router.register(r'call/(?P<call_id>[0-9]+)/ambulance/(?P<ambulance_id>[0-9]+)/waypoint',
                AmbulanceCallWaypointViewSet,
                basename='api-call-waypoint')

router.register(r'priority',
                CallPriorityViewSet,
                basename='api-priority')

router.register(r'radio',
                CallRadioViewSet,
                basename='api-radio')

router.register(r'client',
                ClientViewSet,
                basename='api-client')

urlpatterns = i18n_patterns(*[

    # Router API urls
    url(r'^api/', include(router.urls)),
    url(r'^swagger(?P<format>\.json|\.yaml)$', login_required(schema_view.without_ui(cache_timeout=0)), name='schema-json'),
    url(r'^swagger/$', login_required(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
    # url(r'^redoc/$', login_required(schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc')),

    # Add mqtt_password to api
    url(r'^api/user/(?P<user__username>[\w.@+-]+)/password/$',
        PasswordView.as_view(),
        name='mqtt_password'),

    # Add settings to api
    url(r'^api/settings/$',
        SettingsView.as_view(),
        name='mqtt_settings'),

    # Add version to api
    url(r'^api/version/$',
        VersionView.as_view(),
        name='version'),

])

urlpatterns += i18n_patterns(*[

    # ambulance
    url(r'^ambulance/', include('ambulance.urls')),

    # ambulance
    url(r'^hospital/', include('hospital.urls')),
    
    # login
    url(r'^auth/', include('login.urls')),

    # equipment
    url(r'^equipment/', include('equipment.urls')),

    # report
    url(r'^report/', include('report.urls')),

    # video
    url(r'^video/', include('video.urls')),

    # guest
    url(r'^guest/', include('guest.urls')),

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
])
