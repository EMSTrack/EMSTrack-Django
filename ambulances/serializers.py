from rest_framework import serializers

from .models import  AmbulanceStatus, AmbulanceLocation, Ambulance, \
    AmbulanceRoute, Region, Call, Hospital, \
    Equipment, EquipmentCount, Base, AmbulanceCapability, UserLocation, User

from .fields import AmbulanceStatusField, AmbulanceCapabilityField

from drf_extra_fields.geo_fields import PointField

# Serializers: Takes a model and defines how it should be represented as a JSON Object

class AmbulanceStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmbulanceStatus
        fields = '__all__'


class UserLocationSerializer(serializers.ModelSerializer):

    class Meta:

        # Define model, fields, and access permissions for the serializer
        model = UserLocation
        fields = ['user', 'location', 'timestamp']
        
class AmbulanceLocationSerializer(serializers.ModelSerializer):

    # Assign status and capability
    status = AmbulanceStatusField()

    class Meta:

        # Define model, fields, and access permissions for the serializer
        model = AmbulanceLocation
        fields = ['location', 'status', 'orientation']

class AmbulanceSerializer(serializers.ModelSerializer):

    # Define functions that will query for these custom fields
    location = AmbulanceLocationSerializers()
    capability = AmbulanceCapabilityField()

    class Meta:

        # Define model, fields, and access permissions for the serializer
        model = Ambulance
        fields = ['id', 'identifier', 'comment', 'capability', 'updated_at', 'location']


        
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


class AmbulanceRouteSerializer(serializers.ModelSerializer):

    class Meta:
        model = AmbulanceRoute
        fields = '__all__'


class MQTTLocationSerializer(serializers.ModelSerializer):

    # Define location as a Pointfield (drf-extra-field package auto serializes this)
    location = PointField(required=True)

    # Defines a way to create a model from the JSON data
    def create(self, validated_data):
        return UserLocation.objects.create(**validated_data)

    class Meta:
        model = UserLocation
        fields = ['location', 'timestamp', 'ambulance']

class MQTTUserLocationSerializer(serializers.ModelSerializer):

    # Define location as a Pointfield (drf-extra-field package auto serializes this)
    location = PointField(required=True)

    # Defines a way to create a model from the JSON data
    def create(self, validated_data):
        return UserLocation.objects.create(**validated_data)

    class Meta:
        model = UserLocation
        fields = ['location', 'timestamp', 'ambulance', 'user']

class MQTTAmbulanceLocSerializer(serializers.ModelSerializer):

    location = serializers.SerializerMethodField('get_amb_loc')

    class Meta:
        model = Ambulance
        fields = ['location', 'orientation']

    # Obtain serialized location
    def get_amb_loc(self, obj):
        loc = UserLocation.objects.filter(ambulance=obj.id).order_by('timestamp').last()
        loc_serializer = UserLocationSerializer(loc)
        return loc_serializer.data


class UserLocationSerializer(serializers.ModelSerializer):

    # Define functions that will query for these custom fields
    latitude = serializers.SerializerMethodField('get_lat')
    longitude = serializers.SerializerMethodField('get_long')

    class Meta:
        model = UserLocation
        fields = ['latitude', 'longitude']

    def get_lat(self, obj):
        return obj.location.y

    def get_long(self, obj):
        return obj.location.x

class MQTTHospitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hospital
        fields = ['id', 'name']

class MQTTAmbulanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ambulance
        fields = ['id', 'identifier']

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


class MQTTHospitalListSerializer(serializers.ModelSerializer):
    hospitals = MQTTHospitalSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['hospitals']


class MQTTAmbulanceListSerializer(serializers.ModelSerializer):
    ambulances = MQTTAmbulanceSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ['ambulances']
