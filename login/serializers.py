import logging

from rest_framework import serializers

from django.contrib.auth.models import User, Group

from .models import Profile, AmbulancePermission, HospitalPermission, GroupProfile

from .permissions import get_permissions

from ambulance.models import Ambulance

from hospital.models import Hospital


logger = logging.getLogger(__name__)


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

    class Meta:
        model = Profile
        fields = ('ambulances', 'hospitals')


class UserProfileSerializer(serializers.Serializer):
    ambulances = serializers.SerializerMethodField()
    hospitals = serializers.SerializerMethodField()

    class Meta:
        fields = ('ambulances', 'hospitals')

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

        # retrieve permissions
        self._permissions = get_permissions(self.instance)

    def get_ambulances(self, user):

        return AmbulancePermissionSerializer(self._permissions.get_permissions('ambulances').values(), many=True).data

    def get_hospitals(self, user):

        return HospitalPermissionSerializer(self._permissions.get_permissions('hospitals').values(), many=True).data