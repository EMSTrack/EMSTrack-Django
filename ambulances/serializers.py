from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField as PointFieldSerializer

from django.contrib.auth.models import User

from .models import Profile, Hospital, Ambulance, \
    AmbulancePermission, HospitalPermission, \
    AmbulanceUpdate

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

    status = serializers.CharField(source='last_update.status', allow_null=True)
    location = PointFieldSerializer(source='last_update.location', allow_null=True)
    timestamp = serializers.DateTimeField(source='last_update.timestamp')
    
    class Meta:
        model = Ambulance
        fields = ('id', 'identifier', 'comment', 'capability',
                  'status', 'location', 'timestamp', 'updated_on')
        
