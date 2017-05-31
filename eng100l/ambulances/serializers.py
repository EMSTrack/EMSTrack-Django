from rest_framework import serializers

from .models import Status, Ambulances, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, Route, Capability, LocationPoint

from .fields import StatusField

from drf_extra_fields.geo_fields import PointField

# Serializers: Takes a model and defines how it should be represented as a JSON Object

class StatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = '__all__'


class AmbulancesSerializer(serializers.ModelSerializer):

    # Define functions that will query for these custom fields
    location = serializers.SerializerMethodField('get_amb_loc')
    capability = serializers.SerializerMethodField('get_capability_name')

    # Assign status to a custom field in fields.py
    status = StatusField()

    class Meta:

        # Define model, fields, and access permissions for the serializer
        model = Ambulances
        fields = ['id', 'location', 'status', 'priority', 'orientation', 'capability', 'license_plate']
        read_only_fields = ('priority',)

    # Queries for the capability of the ambulance
    def get_capability_name(self, obj):
        if obj.capability is not None:
            capability = Capability.objects.filter(id=(obj.capability).id).first()
            if hasattr(capability, 'name'):
                return capability.name

    # Obtain serialized location
    def get_amb_loc(self, obj):

        # Obtain latest ambulance location
        loc = LocationPoint.objects.filter(ambulance=obj.id).order_by('timestamp').last()

        # Instantiate a location serializer to serialize location point into fields
        loc_serializer = LocationSerializer(loc)

        # Return the data (JSON format of fields)
        return loc_serializer.data

class CallSerializer(serializers.ModelSerializer):

    latitude = serializers.SerializerMethodField('get_lat')
    longitude = serializers.SerializerMethodField('get_long')

    class Meta:

        # Return all fields of the call in auto serialized format
        model = Call
        exclude = ('location',)

    def get_lat(self, obj):
        return obj.location.y

    def get_long(self, obj):
        return obj.location.x


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'


class EquipmentCountSerializer(serializers.ModelSerializer):

    # Define functions that will query for these custom fields
    name = serializers.SerializerMethodField('get_equipment_name')
    toggleable = serializers.SerializerMethodField('get_toggle')

    class Meta:
        model = EquipmentCount
        fields = ['id', 'name', 'quantity', 'toggleable']

    def get_equipment_name(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().name

    def get_toggle(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().toggleable


class HospitalSerializer(serializers.ModelSerializer):

    # Nest a serializer within a serializer
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


class MQTTLocationSerializer(serializers.ModelSerializer):

    # Define location as a Pointfield (drf-extra-field package auto serializes this)
    location = PointField(required=True)

    # Defines a way to create a model from the JSON data
    def create(self, validated_data):
        return LocationPoint.objects.create(**validated_data)

    class Meta:
        model = LocationPoint
        fields = ['location', 'timestamp', 'ambulance']


class MQTTAmbulanceLocSerializer(serializers.ModelSerializer):

    location = serializers.SerializerMethodField('get_amb_loc')

    class Meta:
        model = Ambulances
        fields = ['location', 'orientation']

    # Obtain serialized location
    def get_amb_loc(self, obj):
        loc = LocationPoint.objects.filter(ambulance=obj.id).order_by('timestamp').last()
        loc_serializer = LocationSerializer(loc)
        return loc_serializer.data


class LocationSerializer(serializers.ModelSerializer):

    # Define functions that will query for these custom fields
    latitude = serializers.SerializerMethodField('get_lat')
    longitude = serializers.SerializerMethodField('get_long')

    class Meta:
        model = LocationPoint
        fields = ['latitude', 'longitude']

    def get_lat(self, obj):
        return obj.location.y

    def get_long(self, obj):
        return obj.location.x

class MQTTHospitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hospital
        fields = ['id', 'name']

class MQTTEquipmentCountSerializer(serializers.ModelSerializer):

    # Define functions that will query for these custom fields
    name = serializers.SerializerMethodField('get_equipment_name')
    toggleable = serializers.SerializerMethodField('get_toggle')

    class Meta:
        model = EquipmentCount
        fields = ['name', 'toggleable']

    def get_equipment_name(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().name

    def get_toggle(self, obj):
        return Equipment.objects.filter(id=(obj.equipment).id).first().toggleable


class MQTTHospitalEquipmentSerializer(serializers.ModelSerializer):

    # Define a serializer within a serializer
    equipment = MQTTEquipmentCountSerializer(many=True)

    class Meta:
        model = Hospital
        fields = ['equipment']
