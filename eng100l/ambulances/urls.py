from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework_swagger.views import get_swagger_view
from rest_framework import routers

from . import views
from .views import StatusViewSet, AmbulancesViewSet, CallViewSet, HospitalViewSet, EquipmentCountViewSet, RouteViewSet, AmbulanceUpdateView

schema_view = get_swagger_view(title='Ambulances API')

router = routers.DefaultRouter()
router.register(r'status', StatusViewSet)
router.register(r'ambulances', AmbulancesViewSet)
router.register(r'calls', CallViewSet)
router.register(r'hospitals', HospitalViewSet)
router.register(r'equipment', EquipmentCountViewSet)
router.register(r'routes', RouteViewSet)

urlpatterns = [

    # Swagger Documentation
    url(r'^docs/', schema_view),

    # Router API urls
    url(r'^api/', include(router.urls)),

    url(r'^$',
        views.AmbulanceView.as_view(),
        name="ambulance"),

    url(r'^ambulance/(?P<pk>\d+)/update/$', 
        AmbulanceUpdateView.as_view(), 
        name='ambulance_update'),

    url(r'^status$',
        views.StatusCreateView.as_view(),
        name="status"),

    url(r'^ambulance_map$',
        views.AmbulanceMap.as_view(),
        name="ambulance_map"),

    url(r'^call_list$',
        views.CallView.as_view(),
        name="call_list"),

]
