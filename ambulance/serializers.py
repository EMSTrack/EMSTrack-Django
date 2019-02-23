import logging
from django.db import IntegrityError, transaction

from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField
from rest_framework.exceptions import PermissionDenied

from login.permissions import get_permissions
from .models import Ambulance, AmbulanceUpdate, Call, Location, AmbulanceCall, Patient, CallStatus, Waypoint, \
    LocationType
from emstrack.latlon import calculate_orientation

logger = logging.getLogger(__name__)


# Ambulance serializers

class AmbulanceSerializer(serializers.ModelSerializer):

    client_id = serializers.CharField(source='client.client_id', required=False)
    location = PointField(required=False)
    
    class Meta:
        model = Ambulance
        fields = ['id', 'identifier',
                  'capability', 'status',
                  'orientation', 'location',
                  'timestamp', 'client_id',
                  'comment', 'updated_by', 'updated_on']
        read_only_fields = ('updated_by', 'client_id')

    def validate(self, data):

        # timestamp must be defined together with either comment, capability, status or location
        if 'timestamp' in data and not ('comment' in data or 'capability' in data or
                                        'location' in data or 'status' in data):
            raise serializers.ValidationError('timestamp can only be set when either comment, location, ' +
                                              'capability, or status are modified')

        return data

    def create(self, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        # only super can create
        if not user.is_superuser:
            raise PermissionDenied()
    
        return super().create(validated_data)
    
    def update(self, instance, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        if not user.is_superuser:

            # serializer.instance will always exist!
            # if not user.profile.ambulances.filter(can_write=True,
            #                                      ambulance=instance.id):
            if not get_permissions(user).check_can_write(ambulance=instance.id):
                raise PermissionDenied()

        # # update location_client
        # # stored in validated_data as {'location_client': {'client_id': client_id}}
        # if 'location_client' in validated_data:
        #
        #     # retrieve new location_client and remove it from validated_data
        #     location_client = None
        #     client_id = validated_data.pop('location_client')['client_id']
        #     if client_id:
        #         location_client = Client.objects.get(client_id=client_id)
        #
        #     # reset location_client if either new or old is None, otherwise ignore
        #     if instance.location_client is None or location_client is None:
        #
        #         # fine, clear or update location client
        #         validated_data['location_client'] = location_client

        return super().update(instance, validated_data)


class AmbulanceUpdateListSerializer(serializers.ListSerializer):

    def create(self, validated_data):

        def process_update(update, current):

            # calculate orientation?
            if ('orientation' not in update and
                    'location' in update and
                    update['location'] != current['location']):

                    current['orientation'] = calculate_orientation(current['location'], update['location'])

            # clear timestamp
            # if update has no timestamp, save should create one
            current.pop('timestamp', None)

            # update data
            current.update(**update)

            return current

        # process updates inside a transaction
        try:

            with transaction.atomic():

                # loop through updates
                instances = []
                n = len(validated_data)

                # short return
                if n == 0:
                    return

                # get ambulance and create template from first update
                # all ambulances are the same in a bulk update
                ambulance = validated_data[0].get('ambulance')
                data = {k: getattr(ambulance, k) for k in ('capability', 'status',
                                                           'orientation', 'location', 'comment')}

                # loop through
                for k in range(0, n-1):

                    # process update
                    data = process_update(validated_data[k], data)

                    # create update object
                    obj = AmbulanceUpdate(**data)
                    obj.save()

                    # append to objects list
                    instances.append(obj)

                # on last update, update ambulance instead

                # process last update
                data = process_update(validated_data[-1], data)

                # save to ambulance will automatically create update
                for attr, value in data.items():
                    setattr(ambulance, attr, value)
                ambulance.save()

                # append to objects list
                instances.append(ambulance)

            # return created instances
            return instances

        except IntegrityError:
            logger.info('Integrity error in bulk ambulance update')


class AmbulanceUpdateSerializer(serializers.ModelSerializer):

    location = PointField(required=False)
    ambulance_identifier = serializers.CharField(source='ambulance.identifier', required=False)
    updated_by_username = serializers.CharField(source='updated_by.username', required=False)

    class Meta:
        list_serializer_class = AmbulanceUpdateListSerializer
        model = AmbulanceUpdate
        fields = ['id',
                  'ambulance_id',
                  'ambulance_identifier',
                  'capability', 'status', 'orientation',
                  'location', 'timestamp',
                  'comment',
                  'updated_by_username', 'updated_on']
        read_only_fields = ['id',
                            'ambulance_id'
                            'ambulance_identifier',
                            'updated_by_username', 'updated_on']


# Location serializers

class LocationSerializer(serializers.ModelSerializer):
    location = PointField(required=False)

    class Meta:
        model = Location
        fields = ['id',
                  'number', 'street', 'unit', 'neighborhood',
                  'city', 'state', 'zipcode', 'country',
                  'location',
                  'name', 'type',
                  'comment', 'updated_by', 'updated_on']
        read_only_fields = ('id', 'updated_by')

    def create(self, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        # only super can create
        if not user.is_superuser:
            raise PermissionDenied()

        return super().create(validated_data)

    def update(self, instance, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        # only super can update
        if not user.is_superuser:
            raise PermissionDenied()

        return super().update(instance, validated_data)


# Waypoint Serializers

class WaypointSerializer(serializers.ModelSerializer):

    location = LocationSerializer(required=False)

    class Meta:
        model = Waypoint
        fields = ['id', 'ambulance_call_id',
                  'order', 'status',
                  'location',
                  'comment', 'updated_by', 'updated_on']
        read_only_fields = ('id', 'ambulance_call_id', 'location', 'updated_by')

    def create(self, validated_data):

        # get current user
        user = validated_data['updated_by']

        # publish?
        publish = validated_data.pop('publish', False)

        # retrieve location
        location = validated_data.pop('location', None)
        if location is None:
            raise serializers.ValidationError('Waypoint must have a location')

        # retrieve initial location
        # location id is not present in validated_data
        initial_location = self.initial_data['location']

        # retrieve or create?
        if 'id' not in initial_location or initial_location['id'] is None:
            logger.debug('will create waypoint location')
            if location['type'] in (LocationType.i.name, LocationType.w.name):
                location = Location.objects.create(**location, updated_by=user)
            else:
                raise serializers.ValidationError('Users can only create incident and waypoint locations')
        else:
            logger.debug('will retrieve waypoint location')
            location = Location.objects.get(id=initial_location['id'])

        # create waypoint and publish
        validated_data['location'] = location
        waypoint = super().create(validated_data)
        if publish:
            waypoint.publish()

        return waypoint

    def update(self, instance, validated_data):

        # publish?
        publish = validated_data.pop('publish', False)

        # retrieve location
        location = validated_data.pop('location', None)
        if location is not None:
            raise serializers.ValidationError('Waypoint locations cannot be updated.')

        # update waypoint and publish
        waypoint = super().update(instance, validated_data)
        if publish:
            waypoint.publish()

        return waypoint


# AmbulanceCall Serializer

class AmbulanceCallSerializer(serializers.ModelSerializer):

    ambulance_id = serializers.PrimaryKeyRelatedField(queryset=Ambulance.objects.all(), read_only=False)
    waypoint_set = WaypointSerializer(many=True, required=False)

    class Meta:
        model = AmbulanceCall
        fields = ['id',
                  'ambulance_id',
                  'status',
                  'comment', 'updated_by', 'updated_on',
                  'waypoint_set']
        read_only_fields = ('id', 'updated_by')


# Patient Serializer

class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Patient
        fields = ['id', 'name', 'age']
        read_only_fields = []


# Call serializer

class CallSerializer(serializers.ModelSerializer):

    patient_set = PatientSerializer(many=True, required=False)
    ambulancecall_set = AmbulanceCallSerializer(many=True, required=False)

    class Meta:
        model = Call
        fields = ['id',
                  'status', 'details', 'priority',
                  'created_at',
                  'pending_at', 'started_at', 'ended_at',
                  'comment', 'updated_by', 'updated_on',
                  'ambulancecall_set',
                  'patient_set']
        read_only_fields = ['created_at', 'updated_by']

    def create(self, validated_data):

        # Get current user.
        user = validated_data['updated_by']

        # Make sure user is super, staff, or dispatcher.
        if not (user.is_superuser or user.is_staff or user.userprofile.is_dispatcher):
            raise PermissionDenied()
        
        ambulancecall_set = validated_data.pop('ambulancecall_set', [])
        patient_set = validated_data.pop('patient_set', [])

        # Makes sure database rolls back in case of integrity or other errors
        with transaction.atomic():

            # creates call first, do not publish
            call = Call(**validated_data)
            call.save(publish=False)

            # then patients, do not publish
            for patient in patient_set:
                obj = Patient(call=call, **patient)
                obj.save(publish=False)

            # then add ambulances, do not publish
            for ambulancecall in ambulancecall_set:
                ambulance = ambulancecall.pop('ambulance_id')

                # check permisssions in case of dispatcher
                if not (user.is_superuser or user.is_staff):
                    if not get_permissions(user).check_can_read(ambulance=ambulance.id):
                        raise PermissionDenied()

                waypoint_set = ambulancecall.pop('waypoint_set', [])
                ambulance_call = AmbulanceCall(call=call, ambulance=ambulance, **ambulancecall, updated_by=user)
                ambulance_call.save(publish=False)
                # add waypoints
                for waypoint in waypoint_set:
                    location = waypoint.pop('location', {})
                    if not location:
                        raise serializers.ValidationError('Location is not defined')
                    if 'id' in location:
                        # location already exists, retrieve
                        location = Location.objects.get(id=location['id'])
                    else:
                        # location does not exist, create one
                        if 'type' not in location:
                            raise serializers.ValidationError('Location type is not defined')
                        elif location['type'] == LocationType.h.name:
                            raise serializers.ValidationError('Hospitals must be created before using as waypoints')
                        elif location['type'] == LocationType.i.name or location['type'] == LocationType.w.name:
                            # TODO: check to see if a close by waypoint already exists to contain proliferation
                            location = Location.objects.create(**location, updated_by=user)
                        else:
                            raise serializers.ValidationError("Invalid waypoint '{}'".format(location))
                    # add waypoint
                    obj = Waypoint.objects.create(ambulance_call=ambulance_call, **waypoint,
                                                  location=location, updated_by=user)

            # publish call to mqtt only after all includes have succeeded
            call.publish()

            # then publish ambulance calls
            for ambulancecall in call.ambulancecall_set.all():
                ambulancecall.publish()

        return call

    def update(self, instance, data):

        # Get current user.
        user = data['updated_by']

        # Make sure user is Super.
        if not user.is_superuser:
            # Serializer instance will always exist!
            if not user.profile.calls.filter(can_write=True, call=instance.id):
                raise PermissionDenied()

        return super().update(instance, data)

    def validate(self, data):

        if 'status' in data and \
                data['status'] != CallStatus.P.name and \
                (not ('ambulancecall_set' in data) or len(data['ambulancecall_set']) == 0):
            raise serializers.ValidationError('Started call and ended call must have ambulancecall_set')
        return data
