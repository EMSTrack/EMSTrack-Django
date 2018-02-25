import logging

from rest_framework import serializers

from django.contrib.auth.models import User

from .models import Profile, AmbulancePermission, HospitalPermission, GroupProfile

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

    # all_ambulances = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('ambulances', 'hospitals')


class ExtendedProfileSerializer(serializers.ModelSerializer):
    ambulances = serializers.SerializerMethodField()
    hospitals = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('ambulances', 'hospitals')

    def get_ambulances(self, obj):
        logger.debug('user = {}'.format(obj.user))
        logger.debug('groups= {}'.format(obj.user.groups))
        if obj.user.is_superuser:
            return [{'ambulance_id': p['id'],
                     'ambulance_identifier': p['identifier'],
                     'can_read': True,
                     'can_write': True} for p in Ambulance.objects.all().values('id', 'identifier')]
        else:

            # initialize ambulances permissions
            all_ambulances = {}

            # loop through groups
            for group in obj.user.groups.all():
                all_ambulances.update({e.id: e for e in group.groupprofile.ambulances.all()})
                logger.debug('group = {} , all_ambulances = {}'.format(group.name, all_ambulances))

            # add user permissions
            all_ambulances.update({e.id: e for e in obj.user.profile.ambulances.all()})
            logger.debug('all_ambulances = {}'.format(all_ambulances))

            return AmbulancePermissionSerializer(all_ambulances.values(), many=True).data

    def get_hospitals(self, obj):
        if obj.user.is_superuser:
            return [{'hospital_id': p['id'],
                     'hospital_name': p['name'],
                     'can_read': True,
                     'can_write': True} for p in Hospital.objects.all().values('id', 'name')]
        else:

            # initialize hospitals permissions
            all_hospitals = {}

            # loop through groups
            for group in obj.user.groups.all():
                all_hospitals.update({e.id: e for e in group.groupprofile.hospitals.all()})
                logger.debug('group = {} , all_hospitals = {}'.format(group.name, all_hospitals))

            # add user permissions
            all_hospitals.update({e.id: e for e in obj.user.profile.hospitals.all()})
            logger.debug('all_hospitals = {}'.format(all_hospitals))

            return HospitalPermissionSerializer(all_hospitals.values(), many=True).data
