import logging

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from .models import UserAmbulancePermission, UserHospitalPermission, Client, TokenLogin

from .permissions import get_permissions

logger = logging.getLogger(__name__)


# Profile serializers

class AmbulancePermissionSerializer(serializers.ModelSerializer):
    ambulance_id = serializers.IntegerField(source='ambulance.id')
    ambulance_identifier = serializers.CharField(source='ambulance.identifier')

    class Meta:
        model = UserAmbulancePermission
        fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')
        read_only_fields = ('ambulance_id', 'ambulance_identifier', 'can_read', 'can_write')


class HospitalPermissionSerializer(serializers.ModelSerializer):
    hospital_id = serializers.IntegerField(source='hospital.id')
    hospital_name = serializers.CharField(source='hospital.name')

    class Meta:
        model = UserHospitalPermission
        fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')
        read_only_fields = ('hospital_id', 'hospital_name', 'can_read', 'can_write')


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


# TokenLogin serializer
class TokenLoginSerializer(serializers.NodelSerializer):

    class Meta:
        model = TokenLogin
        fields = ('token', 'url')

    def get_object(self):

        # get current user
        user = self.context['request'].user

        # make sure current user is the one requesting token or username is guest
        username = self.kwargs['username']
        if user.username != username:
            # override user if guest
            user = get_object_or_404(User, username=username)
            if not user.userprofile.is_guest:
                raise Http404

        # create slug
        obj = TokenLogin.objects.create(user=user)

        return obj


# Client serializers

class ClientSerializer(serializers.ModelSerializer):

    # override validators to prevent uniqueness to invalidate data
    client_id = serializers.CharField(max_length=254, validators=[])
    username = serializers.CharField(source='user.username', required=False)

    class Meta:
        model = Client
        fields = ['client_id', 'username',
                  'status', 'ambulance', 'hospital',
                  'updated_on']
        read_only_fields = ('username', 'updated_on')

    def create(self, validated_data):
        """
        This will create or update a client if existing
        """
        instance, created = Client.objects.update_or_create(
            client_id=validated_data.get('client_id'),
            defaults=validated_data
        )

        return instance
