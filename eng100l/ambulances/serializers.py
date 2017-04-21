from rest_framework import serializers
from .models import Status, TrackableDevice, Ambulances, Call
from drf_extra_fields.geo_fields import PointField


class StatusSerializer(serializers.ModelSerializer):

    status = serializers.SerializerMethodField('get_alternate_name')

    class Meta:
        model = Status
        fields = ['status']

    def get_alternate_name(self, obj):
        return obj.status_string


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

    address = serializers.SerializerMethodField('get_alternate_name')
    location = PointField(required=False)

    class Meta:
        model = Call
        fields = ['address', 'location', 'priority']

    def get_alternate_name(self, obj):
        return obj.address_string
