from django.core.exceptions import PermissionDenied

from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField

from .models import Ambulance, AmbulanceUpdate


# Ambulance serializers

class AmbulanceSerializer(serializers.ModelSerializer):

    location = PointField(required=False)
    
    class Meta:
        model = Ambulance
        fields = ['id', 'identifier',
                  'capability', 'status',
                  'orientation', 'location',
                  'location_timestamp',
                  'comment', 'updated_by', 'updated_on']
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


class AmbulanceUpdateSerializer(serializers.ModelSerializer):

    location = PointField(required=False)

    class Meta:
        model = AmbulanceUpdate
        fields = ['id',
                  'ambulance__identifier',
                  'status', 'orientation',
                  'location', 'location_timestamp',
                  'comment',
                  'updated_by__username', 'updated_on']
        read_only_fields = ['id',
                            'ambulance__identifier',
                            'status', 'orientation',
                            'location', 'location_timestamp',
                            'comment',
                            'updated_by__username', 'updated_on']