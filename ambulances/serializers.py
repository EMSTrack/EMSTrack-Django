from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField as PointFieldSerializer

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
import django.db.models as models

from .models import Profile, Hospital, Ambulance, \
    AmbulancePermission, HospitalPermission

# Profile serializers

class AmbulancePermissionSerializer(serializers.ModelSerializer):

    ambulance_id = serializers.IntegerField(source='ambulance.id')
    ambulance_identifier = serializers.CharField(source='ambulance.identifier')
    
    class Meta:
        model = AmbulancePermission
        fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')
        read_only_fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')

class HospitalPermissionSerializer(serializers.ModelSerializer):

    hospital_id = serializers.IntegerField(source='hospital.id')
    hospital_name = serializers.CharField(source='hospital.name')
    
    class Meta:
        model = HospitalPermission
        fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        read_only_fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        
class ProfileSerializer(serializers.ModelSerializer):

    ambulances = AmbulancePermissionSerializer(read_only=True, many=True)
    hospitals = HospitalPermissionSerializer(read_only=True, many=True)

    #all_ambulances = serializers.SerializerMethodField()
    
    class Meta:
        model = Profile
        fields = ('ambulances', 'hospitals')

        
class ExtendedProfileSerializer(serializers.ModelSerializer):

    ambulances = serializers.SerializerMethodField()
    hospitals = HospitalPermissionSerializer(read_only=True, many=True)
    
    class Meta:
        model = Profile
        fields = ('ambulances', 'hospitals')

    def get_ambulances(self, obj):
        if obj.user.is_superuser:
            return [{'ambulance_id': p['id'],
                     'ambulance_identifier': p['identifier'],
                     'can_read': p['can_read'],
                     'can_write': p['can_write']} for p in Ambulance.objects.all().values('id', 'identifier').annotate(can_read=models.Value(True,models.BooleanField()), can_write=models.Value(True,models.BooleanField()))]
        else:
            return [{'ambulance_id': p['ambulance_id'],
                     'ambulance_identifier': p['ambulance__identifier'],
                     'can_read': p['can_read'],
                     'can_write': p['can_write']} for p in obj.ambulances.values('ambulance_id', 'ambulance__identifier', 'can_read', 'can_write')]
        
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
