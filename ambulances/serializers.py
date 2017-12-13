from rest_framework import serializers

from django.contrib.auth.models import User

from .models import Profile, Hospital, Ambulance, \
    UserLocation, AmbulanceLocation

class UserHospitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hospital
        fields = ('id', 'name')
        read_only_fields = ('id', 'name')

class UserHospitalsSerializer(serializers.ModelSerializer):

    hospitals = UserHospitalSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('hospitals',)
        
class UserAmbulanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ambulance
        fields = ('id', 'identifier')
        read_only_fields = ('id', 'identifier')
        
class UserAmbulancesSerializer(serializers.ModelSerializer):

    ambulances = UserAmbulanceSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('ambulances',)

class UserLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserLocation
        fields = ('location', 'timestamp')
       
class AmbulanceLocationSerializer(serializers.ModelSerializer):

    location = UserLocationSerializer()
    
    class Meta:
        model = AmbulanceLocation
        fields = ('location','status','orientation')
