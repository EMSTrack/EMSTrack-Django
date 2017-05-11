from rest_framework import serializers

from .models import Status, TrackableDevice, Ambulances, Region, Call, Hospital, Equipment, EquipmentCount, Base, Route, Capabilities

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
    status = StatusField()
    capability = serializers.SerializerMethodField('get_capability_name')

    class Meta:
        model = Ambulances
        fields = ['id', 'location', 'status', 'priority', 'orientation', 'capability', 'license_plate']
        read_only_fields = ('priority',)

    def get_status_name(self, obj):
        return Status.objects.filter(id=(obj.status).id).first().name

    def get_capability_name(self, obj):
        if(obj.capability != None):
            capability = Capabilities.objects.filter(id=(obj.capability).id).first()
            if(hasattr(capability, 'name')):
                return capability.name

class CallSerializer(serializers.ModelSerializer):

    class Meta:
        model = Call
        fields = '__all__'


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class EquipmentCountSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField('get_equipment_name')
    equipment_type = serializers.SerializerMethodField('get_type')
    toggleable = serializers.SerializerMethodField('get_toggle')

    class Meta:
        model = EquipmentCount
        fields = ['id', 'name', 'hospital_id', 'equipment_id', 'quantity', 'equipment_type', 'toggleable']

    def get_equipment_name(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().name

    def get_type(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().equipment_type

    def get_toggle(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().toggleable

class HospitalSerializer(serializers.ModelSerializer):
    equipment = EquipmentCountSerializer(many=True)

    class Meta:
        model = Hospital
        fields = ['id', 'name', 'equipment']

class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Base
        fields = '__all__'
class RouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Route
        fields = '__all__'
