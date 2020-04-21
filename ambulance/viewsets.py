import logging
import itertools

from django.http import Http404
from rest_framework import viewsets, mixins, exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.exceptions import APIException, NotFound
from rest_framework.status import HTTP_400_BAD_REQUEST

from emstrack.mixins import BasePermissionMixin, \
    CreateModelUpdateByMixin, UpdateModelUpdateByMixin

from login.permissions import IsCreateByAdminOrSuperOrDispatcher, IsAdminOrSuperOrDispatcher, get_permissions

from equipment.models import EquipmentItem
from equipment.serializers import EquipmentItemSerializer
from equipment.viewsets import EquipmentItemViewSet

from .permissions import CallPermissionMixin

from .models import Location, Ambulance, LocationType, Call, CallNote, AmbulanceUpdate, AmbulanceCall, \
    AmbulanceCallHistory, AmbulanceCallStatus, CallStatus, CallPriorityClassification, \
    CallPriorityCode, CallRadioCode, Waypoint

from .serializers import LocationSerializer, AmbulanceSerializer, AmbulanceUpdateSerializer, CallSerializer, \
    CallPriorityCodeSerializer, CallPriorityClassificationSerializer, CallRadioCodeSerializer, \
    CallAmbulanceSummarySerializer, WaypointSerializer, CallNoteSerializer

logger = logging.getLogger(__name__)
flatten = itertools.chain.from_iterable


# Django REST Framework Viewsets
class AmbulanceEquipmentItemViewSet(EquipmentItemViewSet):
    """
    API endpoint for manipulating ambulance equipment.

    list:
    Retrieve list of equipment.

    retrieve:
    Retrieve an existing equipment instance.

    update:
    Update existing equipment instance.

    partial_update:
    Partially update existing equipment instance.
    """
    queryset = EquipmentItem.objects.all()

    serializer_class = EquipmentItemSerializer
    lookup_field = 'equipment_id'

    def get_queryset(self):

        ambulance_id = int(self.kwargs['ambulance_id'])
        ambulance = Ambulance.objects.get(id=ambulance_id)
        equipmentholder_id = ambulance.equipmentholder.id
        return super().get_queryset(equipmentholder_id)


class AmbulancePageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    # page_size = 25
    max_page_size = 5000


class AmbulanceLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 5000


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

    @action(detail=True, methods=['get'])
    def calls(self, request, pk=None, **kwargs):
        """Retrieve active calls for ambulance instance."""
        calls = Call.objects.filter(ambulancecall__ambulance_id=pk).exclude(status=CallStatus.E.name)

        serializer = CallSerializer(calls, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], pagination_class=AmbulancePageNumberPagination)
    def updates(self, request, pk=None, **kwargs):
        """Bulk retrieve/update ambulance updates."""
        if request.method == 'GET':
            # list updates
            return self.updates_get(request, pk, **kwargs)

        elif request.method == 'POST':
            # put updates
            return self.updates_put(request, pk, updated_by=self.request.user, **kwargs)

    # Filter out the working time of ambulance and extract the unavailable time range for ambulance
    @staticmethod
    def extract_unavailable_zone(ambulance_history):

        unavailable_zone = [None]
        accepted = False

        for h in ambulance_history:

            # Started timestamp
            if accepted is False and h.status == AmbulanceCallStatus.A.name:
                unavailable_zone.append(h.updated_on)
                accepted = True

            # If we already seen accepted status, seeing another kind of status
            elif accepted is True and h.status != AmbulanceCallStatus.A.name:
                unavailable_zone.append(h.updated_on)
                accepted = False

        # If the last status is not accepted, we should put a None to ensure pair
        if accepted is False:
            unavailable_zone.append(None)

        return unavailable_zone

    # Filter out the working time of ambulance and extract the available time range for ambulance
    @staticmethod
    def extract_available_zone(ambulance_history):

        available_zone = []
        accepted = False

        for h in ambulance_history:

            # logger.debug('status = %s, updated_on = %s', h.status, h.updated_on)

            # Started timestamp
            if accepted is False and h.status == AmbulanceCallStatus.A.name:
                available_zone.append(h.updated_on)
                accepted = True

            # If we already seen accepted status, seeing another kind of status
            elif accepted is True and h.status != AmbulanceCallStatus.A.name:
                available_zone.append(h.updated_on)
                accepted = False

        # If the last status is not accepted, we should put a None to ensure pair
        if accepted is True:
            available_zone.append(None)

        return available_zone

    @staticmethod
    def filter_history(history, filter_range, order_by):

        # set filter
        if filter_range:
            # create filter to include only active times
            if len(filter_range) % 2 == 1:
                filter_range.append(None)
            logger.debug(filter_range)
            if filter_range:
                ranges = []
                for (t1, t2) in zip(*[iter(filter_range)] * 2):
                    logger.debug((t1, t2))
                    if t2 is None:
                        ranges.append(history.filter(timestamp__gte=t1))
                    else:
                        ranges.append(history.filter(timestamp__range=(t1, t2)))

                # calculate union of the active intervals
                if len(ranges) == 1:
                    history = ranges[0]
                elif len(ranges) > 1:
                    history = ranges[0].union(*ranges[1:])

            else:
                # no active time yet, return nothing!
                history = history.none()

        # order records in descending order
        history = history.order_by(order_by)
        logger.debug(history)

        return history

    def updates_get(self, request, pk=None, **kwargs):
        """
        Retrieve and paginate ambulance updates.
        Use ?page=10&page_size=100 to control pagination.
        Use ?call_id=x to retrieve updates to call x.
        """

        # retrieve updates
        ambulance = self.get_object()
        ambulance_updates = ambulance.ambulanceupdate_set.all()
        # logger.debug(ambulance_updates)

        # retrieve only call updates
        call_id = self.request.query_params.get('call_id', None)
        if call_id is not None:
            try:

                # retrieve call
                call = Call.objects.get(id=call_id)

                # retrieve ambulance_call
                ambulance_call = AmbulanceCall.objects.get(ambulance=ambulance, call=call)

            except (Call.DoesNotExist, Ambulance.objects.DoesNotExist) as e:
                raise Http404("Call with id '{}' does not exist.".format(call_id))

            ambulance_history = AmbulanceCallHistory.objects\
                .filter(ambulance_call=ambulance_call)\
                .order_by('updated_on')
            # logger.debug(ambulance_history)

            if ambulance_history:

                # If there is available history, filter call based on active intervals

                # parse active times
                filter_range = self.extract_available_zone(ambulance_history)
                # logger.debug(available_times)
                # for entry in ambulance_updates:
                #     logger.debug(entry.timestamp)

                if not filter_range:
                    # no active time yet, return nothing!
                    ambulance_updates = AmbulanceUpdate.objects.none()

            else:

                # If no history is available, go for compatibility

                # if the call is ended
                if call.ended_at is not None:
                    # ambulance_updates = ambulance_updates.filter(timestamp__range=(call.started_at, call.ended_at))
                    filter_range = (call.started_at, call.ended_at)

                # iff the call is still active
                elif call.started_at is not None:
                    # ambulance_updates = ambulance_updates.filter(timestamp__gte=call.started_at)
                    filter_range = (call.started_at, None)

                # call hasn't started yet, return none
                else:
                    ambulance_updates = AmbulanceUpdate.objects.none()
                    filter_range = ()

            # order records in ascending order
            # ambulance_updates = ambulance_updates.order_by('timestamp')
            order_by = 'timestamp'

        else:

            filter_range = request.query_params.get('filter', '')
            if filter_range:
                filter_range = filter_range.split(',')
            logger.debug(filter_range)

            # order records in descending order
            # ambulance_updates = ambulance_updates.order_by('-timestamp')
            order_by = '-timestamp'

        # filter history
        ambulance_updates = self.filter_history(ambulance_updates, filter_range, order_by)

        # for entry in ambulance_updates:
        #     logger.debug(entry.timestamp)

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

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


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
            location_type_name = self.kwargs['type']
            # location_type_name = LocationType(location_type).name
        except ValueError:
            raise APIException("Invalid location type '{}'".format(location_type_name))

        return Location.objects.filter(type=location_type_name)


# Call ViewSet

class CallViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  UpdateModelUpdateByMixin,
                  CreateModelUpdateByMixin,
                  CallPermissionMixin,
                  viewsets.GenericViewSet):
    """
    API endpoint for manipulating Calls.

    list:
    Retrieve list of calls.

    create:
    Create new call instance.

    retrieve:
    Retrieve an existing call instance.

    abort:
    Abort an existing call instance.

    update:
    Full call instance updates are not supported.

    partial_update:
    Partially update existing call instance.
    """

    permission_classes = (IsAuthenticated,
                          IsCreateByAdminOrSuperOrDispatcher)

    filter_field = 'ambulancecall__ambulance_id'
    profile_field = 'ambulances'
    queryset = Call.objects.all()

    serializer_class = CallSerializer

    def get_queryset(self):

        # grab all objects from super, enforces permissions
        queryset = super().get_queryset()

        status = self.request.query_params.get('status', None)
        exclude = self.request.query_params.get('exclude', CallStatus.E.name)

        # filter by status
        if status is not None:
            queryset = queryset.filter(status=status)
        elif exclude is not None:
            queryset = queryset.exclude(status=exclude)

        return queryset

    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrSuperOrDispatcher])
    def abort(self, request, pk=None, **kwargs):
        """Abort call."""

        # get call object
        call = self.get_object()

        # abort call
        call.abort()

        # serialize and return
        serializer = CallSerializer(call)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None, **kwargs):
        """Summarize call."""

        # get call object
        call = self.get_object()

        # serialize and return
        serializer = CallAmbulanceSummarySerializer(call)
        return Response(serializer.data)


class AmbulanceCallWaypointViewSet(mixins.ListModelMixin,
                                   mixins.RetrieveModelMixin,
                                   CreateModelUpdateByMixin,
                                   UpdateModelUpdateByMixin,
                                   BasePermissionMixin,
                                   viewsets.GenericViewSet):
    """
    API endpoint for manipulating waypoints in Calls.

    list:
    Retrieve list of waypoints.

    create:
    Create new waypoint instance.

    retrieve:
    Retrieve an existing waypoint instance.

    update:
    Updates existing waypoint instance in call.

    partial_update:
    Partially update existing waypoint instance in call.
    """

    filter_field = 'ambulance_call__ambulance_id'
    profile_field = 'ambulances'
    queryset = Waypoint.objects.all()
    
    serializer_class = WaypointSerializer
    # permission_classes = (IsAuthenticated, )

    def get_queryset(self):
        """
        Restricts the waypoints to ambulanceCall.
        """
        # retrieve call_id
        call_id = int(self.kwargs['call_id'])

        # retrieve ambulance_id
        ambulance_id = int(self.kwargs['ambulance_id'])

        # does ambulancecall exist?
        try:
            ambulance_call = AmbulanceCall.objects.get(call_id=call_id, ambulance_id=ambulance_id)
            self.queryset = ambulance_call.waypoint_set.all()
        except AmbulanceCall.DoesNotExist:
            raise exceptions.NotFound()

        # call super only after filtering the queryset
        logger.debug(self.queryset)
        return super().get_queryset()

    def perform_create(self, serializer):

        # retrieve call_id
        call_id = int(self.kwargs['call_id'])

        # retrieve ambulance_id
        ambulance_id = int(self.kwargs['ambulance_id'])

        # does ambulancecall exist?
        try:
            ambulance_call = AmbulanceCall.objects.get(call_id=call_id, ambulance_id=ambulance_id)
        except AmbulanceCall.DoesNotExist:
            raise exceptions.NotFound()

        # check permission, create does not invoke queryset
        user = self.request.user
        if not user.is_superuser or user.is_staff:

            # return nothing if anonymous
            if user.is_anonymous:
                raise exceptions.PermissionDenied()

            # get permissions
            permissions = get_permissions(user)
            can_do = set()
            if user.userprofile.is_dispatcher:
                can_do.update(permissions.get_can_read('ambulances'))
            else:
                can_do.update(permissions.get_can_write('ambulances'))

            # query ambulances
            if ambulance_call.ambulance.id not in can_do:

                logger.info("call waypoint create: '%s' is not super, staff, authorized user, or dispatcher", user)
                raise exceptions.PermissionDenied()

        # create
        super().perform_create(serializer, ambulance_call=ambulance_call)

    def perform_update(self, serializer):

        # retrieve call_id
        call_id = int(self.kwargs['call_id'])

        # retrieve ambulance_id
        ambulance_id = int(self.kwargs['ambulance_id'])

        # does ambulancecall exist?
        try:
            ambulanceCall = AmbulanceCall.objects.get(call_id=call_id, ambulance_id=ambulance_id)
        except AmbulanceCall.DoesNotExist:
            raise exceptions.NotFound()

        # create
        super().perform_update(serializer, ambulance_call=ambulanceCall)


# CallNoteViewset

class CallNoteViewSet(mixins.ListModelMixin,
                      CreateModelUpdateByMixin,
                      viewsets.GenericViewSet):
    """
    API endpoint for manipulating notes in Calls.

    list:
    Retrieve list of notes.

    create:
    Create new note instance.
    """

    serializer_class = CallNoteSerializer

    # permission_classes = (IsAuthenticated, )

    def check_permissions(self):

        # retrieve call_id
        call_id = int(self.kwargs['call_id'])

        # does call exist?
        try:
            call = Call.objects.get(call_id=call_id)
        except Call.DoesNotExist:
            raise exceptions.NotFound()

        # get user
        user = self.request.user
        if not user.is_superuser or user.is_staff:

            # return nothing if anonymous
            if user.is_anonymous:
                raise exceptions.PermissionDenied()

            # get permissions
            permissions = get_permissions(user)
            can_do = set()
            if user.userprofile.is_dispatcher:
                can_do.update(permissions.get_can_read('ambulances'))
            else:
                can_do.update(permissions.get_can_write('ambulances'))

            # query ambulances
            ambulance_ids = set(call.ambulancecall_set.values_list('ambulance_id'))

            # fail if disjoints
            if can_do.is_disjoint(ambulance_ids):
                logger.info("call note create: '%s' is not super, staff, authorized user, or dispatcher", user)
                raise exceptions.PermissionDenied()

        return call

    def get_queryset(self):
        """
        Restricts the notes to call.
        """

        # check permissions
        call = self.check_permissions()

        # does ambulancecall exist?
        return CallNote.objects.filter(call=call)

    def perform_create(self, serializer):

        # check permissions
        call = self.check_permissions()

        # create
        super().perform_create(serializer, call=call)


# CallPriorityViewSet

class CallPriorityViewSet(mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    """
    API endpoint for manipulating priority codes.

    list:
    Retrieve list of priority codes.
    """

    queryset = CallPriorityCode.objects.all()
    serializer_class = CallPriorityCodeSerializer

    @action(detail=False, methods=['get'])
    def classification(self, request, **kwargs):
        """Retrieve priority classification labels."""
        classification = CallPriorityClassification.objects.all()

        serializer = CallPriorityClassificationSerializer(classification, many=True)
        return Response(serializer.data)


# CallRadioViewSet

class CallRadioViewSet(mixins.ListModelMixin,
                       viewsets.GenericViewSet):
    """
    API endpoint for manipulating radio codes.

    list:
    Retrieve list of radio codes.
    """

    queryset = CallRadioCode.objects.all()
    serializer_class = CallRadioCodeSerializer
