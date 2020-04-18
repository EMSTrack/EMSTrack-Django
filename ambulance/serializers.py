import logging

from django.db import IntegrityError, transaction
from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from drf_extra_fields.geo_fields import PointField

from login.permissions import get_permissions
from emstrack.latlon import calculate_orientation

from .models import Ambulance, AmbulanceUpdate, Call, Location, AmbulanceCall, Patient, CallStatus, Waypoint, \
    LocationType, CallPriorityClassification, CallPriorityCode, CallRadioCode

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
    location_id = serializers.IntegerField(required=False, write_only=True)
    order = serializers.IntegerField(default=-1)

    class Meta:
        model = Waypoint
        fields = ['id', 'ambulance_call_id',
                  'order', 'status',
                  'location', 'location_id',
                  'comment', 'updated_by', 'updated_on']
        read_only_fields = ('id', 'ambulance_call_id', 'updated_by')

    def create(self, validated_data):

        # get current user
        user = validated_data['updated_by']

        # publish?
        publish = validated_data.pop('publish', False)

        # retrieve location
        location = validated_data.pop('location', None)
        location_id = validated_data.pop('location_id', None)
        if not location and not location_id:
            raise serializers.ValidationError('Location or location_id has not been defined')
        elif location and location_id:
            raise serializers.ValidationError('Only one of location or location_id should be set')

        with transaction.atomic():

            if location_id:

                # retrieve existing location
                try:
                    location = Location.objects.get(id=location_id)

                except Location.DoesNotExist:
                    raise serializers.ValidationError("Location with id '{}' could not be found".format(location_id))

            else:

                # create location
                if location['type'] in (LocationType.i.name, LocationType.w.name):
                    location = Location.objects.create(**location, updated_by=user)

                else:
                    raise serializers.ValidationError("Cannot create location of type '{}'".format(location['type']))

            # # retrieve initial location
            # # location id is not present in validated_data
            # initial_location = self.initial_data['location']
            #
            # # retrieve or create?
            # if 'id' not in initial_location or initial_location['id'] is None:
            #     logger.debug('will create waypoint location')
            #     if location['type'] in (LocationType.i.name, LocationType.w.name):
            #         location = Location.objects.create(**location, updated_by=user)
            #     else:
            #         raise serializers.ValidationError('Users can only create incident and waypoint locations')
            # else:
            #     logger.debug('will retrieve waypoint location')
            #     location = Location.objects.get(id=initial_location['id'])

            # create waypoint and publish
            validated_data['location'] = location
            waypoint = super().create(validated_data)
            if publish:
                waypoint.publish()

            return waypoint

    def update(self, instance, validated_data):

        # publish?
        publish = validated_data.pop('publish', False)

        # # retrieve location
        # location = validated_data.pop('location', None)
        # if location is not None:
        #     raise serializers.ValidationError('Waypoint locations cannot be updated.')

        # retrieve location
        location = validated_data.pop('location', None)
        location_id = validated_data.pop('location_id', None)
        if location and location_id:
            raise serializers.ValidationError('Only one of location or location_id should be set')

        with transaction.atomic():

            if location_id:

                # retrieve existing location
                try:
                    instance.location = Location.objects.get(id=location_id)
                    instance.location.save()

                except Location.DoesNotExist:
                    raise serializers.ValidationError("Location with id '{}' could not be found".format(location_id))

            elif location:

                if instance.location.type in (LocationType.i.name, LocationType.w.name):

                    if location['type'] not in (LocationType.i.name, LocationType.w.name):
                        raise serializers.ValidationError("Cannot update location from type "
                                                          "'{}' to type '{}'".format(instance.location.type,
                                                                                     location['type']))

                    # update location
                    for field in location:
                        setattr(instance.location, field, location[field])
                    instance.location.save()

                else:
                    raise serializers.ValidationError("Cannot update location of type '{}'".format(location['type']))

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

    # see https://github.com/encode/django-rest-framework/issues/2320
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Patient
        fields = ['id', 'name', 'age']
        read_only_fields = []


# CallPriorityClassification Serializer

class CallPriorityClassificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = CallPriorityClassification
        fields = ['id', 'label']


# CallPriorityCode Serializer

class CallPriorityCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CallPriorityCode
        fields = ['id', 'prefix', 'priority', 'suffix', 'label']


# CallRadioCode Serializer

class CallRadioCodeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CallRadioCode
        fields = ['id', 'code', 'label']


# Call serializer

class CallSerializer(serializers.ModelSerializer):

    patient_set = PatientSerializer(many=True, required=False)
    ambulancecall_set = AmbulanceCallSerializer(many=True, required=False)
    sms_notifications = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Call
        fields = ['id',
                  'status', 'details', 'priority',
                  'priority_code', 'radio_code',
                  'created_at',
                  'pending_at', 'started_at', 'ended_at',
                  'comment', 'updated_by', 'updated_on',
                  'sms_notifications',
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
        sms_notifications = validated_data.pop('sms_notifications', [])

        # Makes sure database rolls back in case of integrity or other errors
        with transaction.atomic():

            # creates call first, do not publish
            call = Call(**validated_data)
            call.save(publish=False)

            # then patients, do not publish
            for patient in patient_set:
                obj = Patient(call=call, **patient)
                obj.save(publish=False)

            if call.status != CallStatus.P.name and len(ambulancecall_set) == 0:
                raise serializers.ValidationError('Started call and ended call must have ambulancecall_set')

            # then add ambulances, do not publish
            for ambulancecall in ambulancecall_set:
                ambulance = ambulancecall.pop('ambulance_id')

                # check permisssions in case of dispatcher
                if not (user.is_superuser or user.is_staff):
                    # this is the dispatcher_override
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

            # add users to sms notifications
            for user_id in sms_notifications:
                try:
                    user = User.get(id=user_id)
                    if user.userprofile.mobile_number:
                        call.sms_notifications.add(user)
                    else:
                        logger.warning("User %s does not have a mobile phone on file, skipping", user)
                except User.DoesNotExist:
                    raise serializers.ValidationError("Invalid sms_notifications' user id '{}'".format(user_id))

            # publish call to mqtt only after all includes have succeeded
            call.publish()

            # then publish ambulance calls
            for ambulancecall in call.ambulancecall_set.all():
                ambulancecall.publish()

        return call

    def update(self, instance, validated_data):

        # Get current user.
        user = validated_data['updated_by']

        # Make sure ambulancecall_set is not present
        if 'ambulancecall_set' in validated_data:
            raise serializers.ValidationError('Cannot modify ambulancecall_set')

        # Make sure sms_notifications is not present
        if 'sms_notifications' in validated_data:
            raise serializers.ValidationError('Cannot modify sms_notifications')

        # Check permissions
        if not (user.is_superuser or user.is_staff):
            # Get ambulances
            for ambulancecall in instance.ambulancecall_set.all():
                # dispatcher override
                if user.userprofile.is_dispatcher:
                    if not get_permissions(user).check_can_read(ambulance=ambulancecall.ambulance.id):
                        raise PermissionDenied()
                else:
                    if not get_permissions(user).check_can_write(ambulance=ambulancecall.ambulance.id):
                        raise PermissionDenied()

        # Makes sure database rolls back in case of integrity or other errors
        with transaction.atomic():

            # Update patients
            if 'patient_set' in validated_data:

                # Extract patient set
                patient_set = validated_data.pop('patient_set')

                if patient_set:

                    # existing patients
                    logger.debug(patient_set)
                    existing_patients = [patient['id'] for patient in patient_set
                                         if 'id' in patient and patient['id'] is not None]

                    if existing_patients:

                        # delete if not in new patients
                        instance.patient_set.exclude(id__in=existing_patients).delete()

                    # create or update patients
                    for patient in patient_set:
                        pk = patient.pop('id', None)
                        if pk is None:
                            # create patient and do not publish
                            obj = Patient(call=instance, **patient)
                            obj.save(publish=False)
                        else:
                            # update patient, does not call save hence do not publish
                            Patient.objects.filter(id=pk).update(call=instance, **patient)

                else:

                    # delete all patients
                    instance.patient_set.all().delete()

            # call super to update call, which will publish
            super().update(instance, validated_data)

        # call super
        return instance


class CallAmbulanceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = AmbulanceCall
        fields = ['status',
                  'comment', 'updated_by', 'updated_on']


class CallAmbulanceSummarySerializer(serializers.ModelSerializer):

    ambulance_identifier = serializers.CharField(source='ambulance.identifier')
    history = CallAmbulanceHistorySerializer(source='ambulancecallhistory_set', many=True, required=False)
    waypoint_set = WaypointSerializer(many=True, required=False)

    class Meta:
        model = AmbulanceCall
        fields = ['id',
                  'ambulance',
                  'ambulance_identifier',
                  'status',
                  'comment', 'updated_by', 'updated_on',
                  'history',
                  'waypoint_set']
        read_only_fields = ('id', 'updated_by')


class CallSummarySerializer(serializers.ModelSerializer):

    priority_code = CallPriorityCodeSerializer()
    radio_code = CallRadioCodeSerializer()

    patient_set = PatientSerializer(many=True, required=False)
    ambulancecall_set = CallAmbulanceSummarySerializer(many=True, required=False)
    sms_notifications = serializers.PrimaryKeyRelatedField(many=True, read_only=True, required=False)

    class Meta:
        model = Call
        fields = ['id',
                  'status', 'details', 'priority',
                  'priority_code', 'radio_code',
                  'created_at',
                  'pending_at', 'started_at', 'ended_at',
                  'comment', 'updated_by', 'updated_on',
                  'sms_notifications',
                  'ambulancecall_set',
                  'patient_set']
        read_only_fields = ['created_at', 'updated_by']
