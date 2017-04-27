from rest_framework import serializers

from .models import Status, TrackableDevice, Ambulances, Region, Call, Hospital, Equipment, EquipmentCount
from drf_extra_fields.geo_fields import PointField


class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = '__all__'


class TrackableDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackableDevice
        fields = '__all__'


# To translate between status id and status name in the returned JSON
class StatusField(serializers.Field):

    def to_representation(self, obj):
        return Status.objects.filter(id=obj.id).first().name

    def to_internal_value(self, data):
        return Status.objects.filter(name=data).first()


class AmbulancesSerializer(serializers.ModelSerializer):

    location = PointField(required=False)
    id = serializers.SerializerMethodField('get_alternate_name')
    status = StatusField()

    class Meta:
        model = Ambulances
        fields = ['id', 'location', 'status', 'priority']
        read_only_fields = ('priority',)

    def get_alternate_name(self, obj):
        return obj.license_plate

    def get_status_name(self, obj):
        return Status.objects.filter(id=(obj.status).id).first().name


class CallSerializer(serializers.ModelSerializer):

    location = PointField(required=False)

    class Meta:
        model = Call
        fields = ['address', 'location', 'priority']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class EquipmentCountSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField('get_equipment_name')

    class Meta:
        model = EquipmentCount
        fields = ['name', 'quantity']

    def get_equipment_name(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().name


class HospitalSerializer(serializers.ModelSerializer):
    equipment = EquipmentCountSerializer(many=True)

    class Meta:
        model = Hospital
        fields = ['name', 'equipment']

class BaseSerializer(serializer.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
