from rest_framework import serializers

from django.contrib.auth.models import User

from .models import Profile, Hospital, Ambulance

class UserHospitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hospital
        read_only_fields = ('id', 'identifier')

class UserHospitalsSerializer(serializers.ModelSerializer):

    hospitals = UserHospitalSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('hospitals',)
        
class UserAmbulanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ambulance
        read_only_fields = ('id', 'identifier')
        
class UserAmbulancesSerializer(serializers.ModelSerializer):

    ambulances = UserAmbulanceSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('ambulances',)
