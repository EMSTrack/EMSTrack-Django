from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField as PointFieldSerializer

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import django.db.models as models

from .models import Ambulance, Hospital, Equipment, HospitalEquipment

# Ambulance serializers
class AmbulanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ambulance
        fields = '__all__'
        read_only_fields = ('updated_by',)

    def validate(self, data):

        # location and location_timestamp must be defined together
        if 'location' in data or 'location_timestamp' in data:

            if not ('location' in data and 'location_timestamp' in data):
                raise serializers.ValidationError('location and location_timestamp must be set together')
            
            if data['location'] and not data['location_timestamp']:
                raise serializers.ValidationError('location cannot be set without location_timestamp')
            
            if not data['location'] and data['location_timestamp']:
                raise serializers.ValidationError('location_timestamp cannot be set without location')

        return data

    def create(self, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        # only super can create
        if not user.is_superuser:
            raise PermissionDenied()
    
        return super().create(validated_data)
    
    def update(self, instance, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        if not user.is_superuser:

            # serializer.instance will always exist!
            if not user.profile.ambulances.filter(can_write=True,
                                                  ambulance=instance.id):
                raise PermissionDenied()

        return super().update(instance, validated_data)


# Hospital serializers
class HospitalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hospital
        fields = '__all__'
        read_only_fields = ('updated_by',)

    def create(self, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        # only super can create
        if not user.is_superuser:
            raise PermissionDenied()
    
        return super().create(validated_data)
    
    def update(self, instance, validated_data):

        # get current user
        user = validated_data['updated_by']

        # check credentials
        if not user.is_superuser:
            
            # serializer.instance will always exist!
            if not user.profile.hospitals.filter(can_write=True,
                                                 hospital=instance.id):
                raise PermissionDenied()

        return super().update(instance, validated_data)
    
# HospitalEquipment serializers
class HospitalEquipmentSerializer(serializers.ModelSerializer):

    hospital_name = serializers.CharField(source='hospital.name')
    equipment_name = serializers.CharField(source='equipment.name')
    equipment_etype = serializers.CharField(source='equipment.etype')
    
    class Meta:
        model = HospitalEquipment
        fields = ('hospital_id', 'hospital_name',
                  'equipment_id', 'equipment_name', 'equipment_etype',
                  'value', 'comment',
                  'updated_by', 'updated_on')
        read_only_fields = ('hospital_id', 'hospital_name',
                            'equipment_id', 'equipment_name', 'equipment_etype',
                            'updated_by',)

    def validate(self, data):

        # call super
        validated_data = super().validate(data)

        # TODO: validate equipment value using equipment_etype
        return validated_data
        
# EquipmentMetadata serializer
class EquipmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Equipment
        fields = '__all__'
