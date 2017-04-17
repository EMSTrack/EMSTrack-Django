from rest_framework import serializers
from .models import Status, TrackableDevice, Ambulances
from drf_extra_fields.geo_fields import PointField

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'

class TrackableDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model= TrackableDevice 
        fields = '__all__'

class AmbulancesSerializer(serializers.ModelSerializer):

    location = PointField(required=False)

    class Meta:
        model = Ambulances	
        fields = '__all__'
