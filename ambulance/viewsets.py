from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from emstrack.mixins import BasePermissionMixin, \
    CreateModelUpdateByMixin, UpdateModelUpdateByMixin

from .models import Ambulance, AmbulanceUpdate

from .serializers import AmbulanceSerializer, \
    AmbulanceUpdateSerializer

# Django REST Framework Viewsets


# Ambulance viewset

class AmbulanceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       CreateModelUpdateByMixin,
                       UpdateModelUpdateByMixin,
                       BasePermissionMixin,
                       viewsets.GenericViewSet):

    """
    API endpoint for manipulating ambulances.

    list:
    Retrieve list of ambulances.

    retrieve:
    Retrieve an existing ambulance instance.

    create:
    Create new ambulance instance.
    
    update:
    Update existing ambulance instance.

    partial_update:
    Partially update existing ambulance instance.
    """

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = Ambulance.objects.all()
    
    serializer_class = AmbulanceSerializer

    @detail_route()
    def updates(self, request, pk=None, **kwargs):
        """
        Retrive ambulance updates.
        """

        ambulance = self.get_object()
        ambulance_updates = ambulance.ambulanceupdate_set
        serializer = AmbulanceUpdateSerializer(ambulance_updates, many=True)
        return Response(serializer.data)
