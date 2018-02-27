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

    @staticmethod
    def _get_permissions(user):

        # quick return if None
        if user is None:
            return {'ambulances': [], 'hospitals': []}

        # or superuser
        if user.is_superuser:
            return {'ambulances': [{'ambulance_id': p['id'],
                                    'ambulance_identifier': p['identifier'],
                                    'can_read': True,
                                    'can_write': True} for p in Ambulance.objects.all().values('id', 'identifier')],
                    'hospitals': [{'hospital_id': p['id'],
                                   'hospital_name': p['name'],
                                   'can_read': True,
                                   'can_write': True} for p in Hospital.objects.all().values('id', 'name')]}

        # initialize permissions
        permissions = {'ambulances': {}, 'hospitals': {}}

        # loop through groups
        for group in user.groups.all():
            permissions['ambulances'].update({e.id: e for e in group.groupprofile.ambulances.all()})
            permissions['hospitals'].update({e.id: e for e in group.groupprofile.hospitals.all()})
            logger.debug('group = {}, ambulances = {}, hospitals = {}'.format(group.name,
                                                                              permissions['ambulances'],
                                                                              permissions['hospitals']))

        # add user permissions
        permissions['ambulances'].update({e.id: e for e in user.profile.ambulances.all()})
        permissions['hospitals'].update({e.id: e for e in user.profile.hospitals.all()})
        logger.debug('ambulances = {}, hospitals = {}'.format(permissions['ambulances'],
                                                              permissions['hospitals']))

        # serialize
        permissions['ambulances'] = AmbulancePermissionSerializer(permissions['ambulances'].values(), many=True).data
        permissions['hospitals'] = HospitalPermissionSerializer(permissions['hospitals'].values(), many=True).data

        perms = get_permissions(user)

        permissions['ambulances'] = AmbulancePermissionSerializer(perms.get_all_permissions('ambulances').values(), many=True).data
        permissions['hospitals'] = HospitalPermissionSerializer(perms.get_all_permissions('hospitals').values(), many=True).data

        return permissions

    def __init__(self, *args, **kwargs):

        # call super
        super().__init__(*args, **kwargs)

        # cache permissions
        self._permissions = self._get_permissions(self.instance)

    def get_ambulances(self, user):

        return self._permissions['ambulances']

    def get_hospitals(self, user):

        return self._permissions['hospitals']

