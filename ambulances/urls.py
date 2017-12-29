from django.conf.urls import url, include

from rest_framework_swagger.views import get_swagger_view
from rest_framework import routers

from django.contrib.auth.decorators import login_required, permission_required

from . import views
from . import viewsets

#from .views import AmbulanceStatusViewSet, AmbulanceViewSet, CallViewSet, \
#    HospitalViewSet, EquipmentCountViewSet, AmbulanceRouteViewSet, \
#    AmbulanceUpdateView, AmbulanceStatusUpdateView, AdminView

# Defines the url routing within the website

# Load swagger
schema_view = get_swagger_view(title='Ambulances API')

# Defines a router which groups Django REST Viewsets
router = routers.DefaultRouter()

# Register urls to viewsets
#router.register(r'status', AmbulanceStatusViewSet)
#router.register(r'ambulances', AmbulanceViewSet)
#router.register(r'calls', CallViewSet)
#router.register(r'hospitals', HospitalViewSet)
#router.register(r'equipment', EquipmentCountViewSet)
#router.register(r'routes', AmbulanceRouteViewSet)

router.register(r'profile',
                viewsets.ProfileViewSet)
router.register(r'ambulance',
                viewsets.AmbulanceViewSet,
                base_name='ambulance')
router.register(r'hospital',
                viewsets.HospitalViewSet,
                base_name='hospital')
router.register(r'hospital-equipment/(?P<pk>[0-9]+)',
                viewsets.HospitalEquipmentViewSet)

urlpatterns = [

    # Swagger Documentation
    url(r'^docs/', schema_view),

    # Router API urls
    url(r'^api/', include(router.urls)),

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
