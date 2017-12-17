from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField as PointFieldSerializer

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from .models import Profile, Hospital, Ambulance, \
    AmbulancePermission, HospitalPermission

# Profile serializers

class AmbulancePermissionSerializer(serializers.ModelSerializer):

    ambulance_id = serializers.IntegerField(source='ambulance.id')
    ambulance_identifier = serializers.CharField(source='ambulance.identifier')
    
    class Meta:
        model = AmbulancePermission
        fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')
        read_only_fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')

class HospitalPermissionSerializer(serializers.ModelSerializer):

    hospital_id = serializers.IntegerField(source='hospital.id')
    hospital_name = serializers.CharField(source='hospital.name')
    
    class Meta:
        model = HospitalPermission
        fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        read_only_fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        
class ProfileSerializer(serializers.ModelSerializer):

    ambulances = AmbulancePermissionSerializer(read_only=True, many=True)
    hospitals = HospitalPermissionSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('ambulances','hospitals')

# Ambulance serializers
class AmbulanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ambulance
        fields = ('id', 'identifier', 'capability',
                  'comment', 'status', 'location',
                  'location_timestamp', 'orientation',
                  'updated_by', 'updated_on')

    def validate(self, data):

        # location and location_timestamp must be defined together
        if data['location'] and not data['location_timestamp']:
            raise serializers.ValidationError('location cannot be set without location_timestamp')

        if not data['location'] and data['location_timestamp']:
            raise serializers.ValidationError('location_timestamp cannot be set without location')

        return data
        
    def update(self, instance, validated_data):

        # can this user update this ambulance?
        user = User.objects.get(id=self.validated_data['updated_by'])

        # if super yes, otherwise
        if not user.is_superuser:
            # check credentials
            if not user.profile.ambulances.filter(can_write=True,
                                                  ambulance=instance.id):
                raise PermissionDenied()

        # calculate orientation

        # save to route
        
        return super().update(instance, validated_data)
