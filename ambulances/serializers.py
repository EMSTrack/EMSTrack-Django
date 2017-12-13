from rest_framework import serializers

from django.contrib.auth.models import User

from .models import Profile, Hospital, Ambulance, \
    UserLocation, AmbulanceLocation

# Profile serializers

class AmbulancePermissionSerializer(serializers.ModelSerializer):

    ambulance_id = serializer.CharField(source='ambulance.id')
    ambulance_identifier = serializer.CharField(source='ambulance.identifier')
    
    class Meta:
        model = Ambulance
        fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')
        read_only_fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')

class HospitalPermissionSerializer(serializers.ModelSerializer):

    hospital_id = serializer.CharField(source='hospital.id')
    hospital_name = serializer.CharField(source='hospital.name')
    
    class Meta:
        model = Hospital
        fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        read_only_fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        
class ProfileSerializer(serializers.ModelSerializer):

    ambulances = AmbulancePermissionSerializer(read_only=True, many=True)
    hospitals = HospitalPermissionSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('ambulances','hospitals')

# Ambulance location serializers
        
class UserLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserLocation
        fields = ('location', 'timestamp')
       
class AmbulanceLocationSerializer(serializers.ModelSerializer):

    location = UserLocationSerializer()
    
    class Meta:
        model = AmbulanceLocation
        fields = ('location','status','orientation')
