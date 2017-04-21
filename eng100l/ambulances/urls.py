from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework_swagger.views import get_swagger_view
from rest_framework import routers

from . import views
from .views import StatusViewSet, AmbulancesViewSet, RegionViewSet

schema_view = get_swagger_view(title='Ambulances API')

router = routers.DefaultRouter()
router.register(r'status', StatusViewSet)
router.register(r'ambulances', AmbulancesViewSet)
router.register(r'regions', RegionViewSet)

urlpatterns = [

    # Swagger Documentation
    url(r'^docs/', schema_view),

    # Router API urls
    url(r'^api/', include(router.urls)),

    url(r'^$',
        views.AmbulanceView.as_view(),
        name="ambulance_create"),

    url(r'^update_ambulance/(?P<pk>[0-9]+)$',
        views.AmbulanceUpdateView.as_view(),
        name="ambulance_update"),

    url(r'^status$',
        views.StatusCreateView.as_view(),
        name="status_create"),

    url(r'^create_route$',
        csrf_exempt(views.CreateRoute.as_view()),
        name="create_route"),

    url(r'^ambulance_map$',
        views.AmbulanceMap.as_view(),
        name="ambulance_map"),

]
