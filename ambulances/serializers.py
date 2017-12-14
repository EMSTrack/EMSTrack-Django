from rest_framework import serializers

from django.contrib.auth.models import User

from .models import Profile, Hospital, Ambulance, \
    AmbulancePermission, HospitalPermission, \
    UserLocation, AmbulanceLocation

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

    status = serializers.CharField(source='location.status')
    
    class Meta:
        model = Ambulance
        fields = ('id', 'identifier', 'comment', 'capability',
                  'status', 'location', 'updated_on')

        
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
