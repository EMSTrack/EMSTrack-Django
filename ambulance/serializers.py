import django.db.models as models
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField

from .models import Ambulance

# Ambulance serializers
class AmbulanceSerializer(serializers.ModelSerializer):

    location = PointField(required=False)

    class Meta:
        model = Ambulance
        fields = [ 'id', 'identifier', 
                'capability', 'status',
                'orientation', 'location',
                'location_timestamp',
                'comment', 'updated_by', 'updated_on' ]
        read_only_fields = ('updated_by',)

    def validate(self, data):

        # location and location_timestamp must be defined together
        if 'location' in data or 'location_timestamp' in data:

            if not ('location' in data and 'location_timestamp' in data):
                raise serializers.ValidationError('location and location_timestamp must be set together')

            if data['location'] and not data['location_timestamp']:
                raise serializers.ValidationError('location cannot be set without location_timestamp')

            if not data['location'] and data['location_timestamp']:
                raise serializers.ValidationError('location_timestamp cannot be set without location')

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
            if not user.profile.ambulances.filter(can_write=True,
                    ambulance=instance.id):
                raise PermissionDenied()

        return super().update(instance, validated_data)

# Defined call serializer
class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Call
        fields = ['id', 'active', 'ambulances', 'patients', 'details',
                'priority','comment', 'updated_by', 'updated_on']
        read_only_fields = ('updated_by')

    def create(self, data):
        # Get current user.
        user = data['updated_by']

        # Make sure user is Super.
        if not user.is_superuser:
            raise PermissionDenied()

        return super().create(data)

    def update(self, instance, data):
        # Get current user.
        user = data['update_by']

        # Make sure user is Super.
        if not user.is_superuser:
            # Serializer instance will always exist!
            if not user.profile.calls.filter(can_write=True, call=instance.id):
                raise PermissionDenied()

        return super().update(instance, data)
