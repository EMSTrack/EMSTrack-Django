from rest_framework import serializers
from .models import Status, TrackableDevice, Ambulances

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'

class TrackableDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model= TrackableDevice 
        fields = '__all__'

class AmbulancesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ambulances	
        fields = '__all__'
