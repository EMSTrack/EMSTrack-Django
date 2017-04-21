from rest_framework import serializers

from .models import Status, TrackableDevice, Ambulances, Region, Call
from drf_extra_fields.geo_fields import PointField


class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = ['__all__']


class TrackableDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackableDevice
        fields = '__all__'


class AmbulancesSerializer(serializers.ModelSerializer):

    location = PointField(required=False)
    id = serializers.SerializerMethodField('get_alternate_name')

    class Meta:
        model = Ambulances
        fields = ['id', 'location', 'status', 'device']

    def get_alternate_name(self, obj):
        return obj.license_plate


class CallSerializer(serializers.ModelSerializer):

    location = PointField(required=False)

    class Meta:
        model = Call
        fields = ['address', 'location', 'priority']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
