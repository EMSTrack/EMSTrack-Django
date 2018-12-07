from django.http import Http404
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination

from emstrack.mixins import BasePermissionMixin, \
    CreateModelUpdateByMixin, UpdateModelUpdateByMixin
from login.viewsets import IsCreateByAdminOrSuper

from .models import Location, Ambulance, LocationType, Call, AmbulanceUpdate

from .serializers import LocationSerializer, AmbulanceSerializer, AmbulanceUpdateSerializer, CallSerializer

import logging
logger = logging.getLogger(__name__)


# Django REST Framework Viewsets

class AmbulancePageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    # page_size = 25
    max_page_size = 1000


class AmbulanceLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100
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
    queryset = Ambulance.objects.all()

    serializer_class = AmbulanceSerializer

    @detail_route(methods=['get', 'post'], pagination_class=AmbulancePageNumberPagination)
    
    def updates(self, request, pk=None, **kwargs):

        if request.method == 'GET':
            # list updates
            return self.updates_get(request, pk, **kwargs)

        elif request.method == 'POST':
            # put updates
            return self.updates_put(request, pk, updated_by=self.request.user, **kwargs)


    # The function that we are going to filter out the working time of ambulance
    # and extract the unavailable time range for ambulance
    def extract_unavailable_zone(ambulance_history):

        unavailable_zone = []
        unavailable_zone.append(None)
        seenOngoing = False

        for h in ambulance_history:

            # Started timestamp
            if seenOngoing == False and h.status == AmbulanceCallStatus.O.name:
                unavailable_zone.append(h.create_at)
                seenOngoing = True

            # If we already seen ongoing status, seeing another kind of status
            elif seenOngoing == True and h.status != AmbulanceCallStatus.O.name:
                unavailable_zone.append(h.create_at)
                seenOngoing = False

        # If the last status is not ongoing, we should put a None to ensure pair
        if seenOngoing == False:
            unavailable_zone.append(None)

        return unavailable_zone

    def updates_get(self, request, pk=None, **kwargs):
        """
        Retrieve and paginate ambulance updates.
        Use ?page=10&page_size=100 to control pagination.
        Use ?call_id=x to retrieve updates to call x.
        """

        # retrieve updates
        ambulance = self.get_object()
        ambulance_updates = ambulance.ambulanceupdate_set

        # retrieve only call updates
        call_id = self.request.query_params.get('call_id', None)
        if call_id is not None:
            try:
                # TODO: filter call based on active intervals.
                #       go back to AmbulanceCallHistory and select active intervals:
                #       between Ongoing and Suspended or Completed

                ambulance_history = ambulance.ambulancecallhistory_set.filter(call_id = call_id).order_by('create_at')
                
                #  If there is a available history, user the following code:
                if ambulance_history is not None:

                    unavailable_zone = extract_unavailable_zone(ambulance_history)

                    unavailable_zone = list(zip(*[iter(unavailable_zone)] * 2))

                    # Update the info
                    for (t1, t2) in unavailable_zone:
                        if t1 == None:
                            ambulance_updates.exclude(timestamp_lte=t2)
                        elif t2 == None:
                            ambulance_updates.exclude(timestamp__gte=t1)
                        else:
                            ambulance_updates.exclude(timestamp__range=(t1, t2))

                #  If no history is available, use the following code:
                else:

                    call = Call.objects.get(id=call_id)

                    # If the call is ended
                    if call.ended_at is not None:
                        ambulance_updates = ambulance_updates.filter(timestamp__range=(call.started_at, call.ended_at))
                    
                    # If the call is still active
                    elif call.started_at is not None:
                        logger.debug('HERE')
                        ambulance_updates = ambulance_updates.filter(timestamp__gte=call.started_at)

                    # call hasn't started yet, return none
                    else:
                        ambulance_updates = AmbulanceUpdate.objects.none()

            except Call.DoesNotExist as e:
                raise Http404("Call with id '{}' does not exist.".format(call_id))

        # order records
        ambulance_updates = ambulance_updates.order_by('-timestamp')

        # paginate
        page = self.paginate_queryset(ambulance_updates)

        if page is not None:
            serializer = AmbulanceUpdateSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # return all if not paginated
        serializer = AmbulanceUpdateSerializer(ambulance_updates, many=True)
        return Response(serializer.data)

    def updates_put(self, request, pk=None, **kwargs):
        """
        Bulk ambulance updates.
        """

        # retrieve ambulance
        ambulance = self.get_object()

        # retrieve user
        updated_by = kwargs.pop('updated_by')

        # update all serializers
        serializer = AmbulanceUpdateSerializer(data=request.data,
                                               many=True)
        if serializer.is_valid():
            serializer.save(ambulance=ambulance, updated_by=updated_by)
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
    queryset = Location.objects.exclude(type=LocationType.h.name).exclude(type=LocationType.w.name)
    serializer_class = LocationSerializer


class LocationTypeViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """
    API endpoint for manipulating locations.

    list:
    Retrieve list of locations by type.
    """
    serializer_class = LocationSerializer

    def get_queryset(self):
        try:
            type = LocationType(self.kwargs['type']).name
        except ValueError:
            type = ''

        return Location.objects.filter(type=type)


# Call ViewSet

class CallViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  CreateModelUpdateByMixin,
                  BasePermissionMixin,
                  viewsets.GenericViewSet):
    """
    API endpoint for manipulating Calls.

    list:
    Retrieve list of calls.

    create:
    Create new call instance.

    retrieve:
    Retrieve an existing call instance.
    """

    permission_classes = (IsAuthenticated,
                          IsCreateByAdminOrSuper)

    filter_field = 'ambulancecall__ambulance_id'
    profile_field = 'ambulances'
    queryset = Call.objects.all()

    serializer_class = CallSerializer
