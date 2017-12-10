from django.conf.urls import url, include
from rest_framework_swagger.views import get_swagger_view
from rest_framework import routers

from django.contrib.auth.decorators import login_required, permission_required

from . import views
from .views import StatusViewSet, AmbulancesViewSet, CallViewSet, \
    HospitalViewSet, EquipmentCountViewSet, RouteViewSet, \
    AmbulanceUpdateView, StatusUpdateView, AdminView

# Defines the url routing within the website

# Load swagger
schema_view = get_swagger_view(title='Ambulances API')

# Defines a router which groups Django REST Viewsets
router = routers.DefaultRouter()

# Register urls to viewsets
router.register(r'status', StatusViewSet)
router.register(r'ambulances', AmbulancesViewSet)
router.register(r'calls', CallViewSet)
router.register(r'hospitals', HospitalViewSet)
router.register(r'equipment', EquipmentCountViewSet)
router.register(r'routes', RouteViewSet)

urlpatterns = [

    # Swagger Documentation
    @login_required
    url(r'^docs/', schema_view),

    # Router API urls
    @login_required
    url(r'^api/', include(router.urls)),

    @login_required
    url(r'^$',
        views.AmbulanceView.as_view(),
        name="ambulance"),

    @login_required
    url(r'^ambulance_map$',
        views.AmbulanceMap.as_view(),
        name="ambulance_map"),
    
    @login_required
    url(r'^ambulance/(?P<pk>\d+)/update/$',
        AmbulanceUpdateView.as_view(),
        name='ambulance_update'),

    @login_required
    url(r'^status/(?P<pk>\d+)/update/$',
        StatusUpdateView.as_view(),
        name='status_update'),

    @login_required
    url(r'^status$',
        views.StatusCreateView.as_view(),
        name="status"),

    @login_required
    url(r'^call_list$',
        views.CallView.as_view(),
        name="call_list"),

    @login_required
    url(r'^admin$',
        views.AdminView.as_view(),
        name="admin"),
    
]
