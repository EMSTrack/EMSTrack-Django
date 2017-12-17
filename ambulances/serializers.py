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
class AmbulanceUpdateSerializer(serializers.ModelSerializer):

    ambulance_id = serializers.IntegerField()
    
    class Meta:
        model = AmbulanceUpdate
        fields = ('ambulance_id', 'user', 'status', 'location', 'timestamp')

    def create(self, validated_data):
        
        ambulance_id = validated_data.pop('ambulance_id')
        update = AmbulanceUpdate.objects.create(**validated_data)

        ambulance = Ambulance.objects.get(id=ambulance_id)
        ambulance.last_update = update
        ambulance.save()
        
        return update

class PrivateAmbulanceUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmbulanceUpdate
        fields = ('user', 'status', 'location', 'timestamp')

class AmbulanceSerializer(serializers.ModelSerializer):

    last_update = PrivateAmbulanceUpdateSerializer()
    
    class Meta:
        model = Ambulance
        fields = ('id', 'identifier', 'comment', 'capability',
                  'last_update')
        
