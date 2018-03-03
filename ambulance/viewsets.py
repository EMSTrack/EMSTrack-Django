from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination

from emstrack.mixins import BasePermissionMixin, \
    CreateModelUpdateByMixin, UpdateModelUpdateByMixin

from .models import Location

from .serializers import LocationSerializer, \
    LocationUpdateSerializer


# Django REST Framework Viewsets

class LocationPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    page_size = 25
    max_page_size = 1000


class LocationLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 1000


# Location viewset

class LocationViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       CreateModelUpdateByMixin,
                       UpdateModelUpdateByMixin,
                       BasePermissionMixin,
                       viewsets.GenericViewSet):
    """
    API endpoint for manipulating locations.

    list:
    Retrieve list of locations.

    retrieve:
    Retrieve an existing location instance.

    create:
    Create new location instance.
    
    update:
    Update existing location instance.

    partial_update:
    Partially update existing location instance.
    """

    filter_field = 'id'
    profile_field = 'locations'
    queryset = Location.objects.all()

    serializer_class = LocationSerializer

    @detail_route(methods=['get', 'post'], pagination_class=LocationPageNumberPagination)
    def updates(self, request, pk=None, **kwargs):

        if request.method == 'GET':
            # list updates
            return self.updates_get(request, pk, **kwargs)

        elif request.method == 'POST':
            # put updates
            return self.updates_post(request, pk, updated_by=self.request.user, **kwargs)

    def updates_get(self, request, pk=None, **kwargs):
        """
        Retrieve and paginate location updates.
        Use ?page=10&page_size=100 to control pagination.
        """

        # retrieve updates
        location = self.get_object()
        location_updates = location.locationupdate_set.order_by('-timestamp')

        # paginate
        page = self.paginate_queryset(location_updates)

        if page is not None:
            serializer = LocationUpdateSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # return all if not paginated
        serializer = LocationUpdateSerializer(location_updates, many=True)
        return Response(serializer.data)

    def updates_put(self, request, pk=None, **kwargs):
        """
        Bulk location updates.
        """

        # retrieve location
        location = self.get_object()

        # retrieve user
        updated_by = kwargs.pop('updated_by')

        # update all serializers
        serializer = LocationUpdateSerializer(data=request.data,
                                               many=True)
        if serializer.is_valid():
            serializer.save(location=location, updated_by=updated_by)
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Location viewset

class LocationViewSet(mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """
    API endpoint for manipulating locations.

    list:
    Retrieve list of locations.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
