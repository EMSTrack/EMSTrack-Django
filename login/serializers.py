from rest_framework import serializers

from django.contrib.auth.models import User

from .models import Profile, AmbulancePermission, HospitalPermission, GroupProfile

from ambulance.models import Ambulance

from hospital.models import Hospital


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
        if obj.user.is_superuser:
            return [{'ambulance_id': p['id'],
                     'ambulance_identifier': p['identifier'],
                     'can_read': True,
                     'can_write': True} for p in Ambulance.objects.all().values('id', 'identifier')]
        else:
            # add group permissions to profile permission
            qs = GroupProfile.objects.filter(group__in=obj.user.groups)
            obj.ambulances.union(entry.ambulances for entry in qs)

            return AmbulancePermissionSerializer(obj.ambulances, many=True).data

    def get_hospitals(self, obj):
        if obj.user.is_superuser:
            return [{'hospital_id': p['id'],
                     'hospital_name': p['name'],
                     'can_read': True,
                     'can_write': True} for p in Hospital.objects.all().values('id', 'name')]
        else:
            return HospitalPermissionSerializer(obj.hospitals, many=True).data
