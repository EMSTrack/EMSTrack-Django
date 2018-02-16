from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.pagination import OffsetLimitPagination

from emstrack.mixins import BasePermissionMixin, \
    CreateModelUpdateByMixin, UpdateModelUpdateByMixin

from .models import Ambulance, AmbulanceUpdate

from .serializers import AmbulanceSerializer, \
    AmbulanceUpdateSerializer


# Django REST Framework Viewsets

class AmbulanceUpdatesPagination(OffsetLimitPagination):
    default_limit = 10
    max_limit = 1000


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
    pagination_class = AmbulanceUpdatesPagination

    @detail_route()
    def updates(self, request, pk=None, **kwargs):
        """
        Retrieve and paginate ambulance updates.
        """

        # retrieve updates
        ambulance = self.get_object()
        ambulance_updates = ambulance.ambulanceupdate_set

        # paginate
        page = self.paginate_queryset(ambulance_updates)

        if page is not None:
            serializer = AmbulanceUpdateSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # return all if not paginated
        serializer = AmbulanceUpdateSerializer(ambulance_updates, many=True)
        return Response(serializer.data)
