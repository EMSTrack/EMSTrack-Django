from django.core.exceptions import PermissionDenied

from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField

from equipment.serializers import EquipmentItemSerializer
from login.permissions import get_permissions
from .models import Hospital


# Hospital serializer
# TODO: Handle equipment in create and update

class HospitalSerializer(serializers.ModelSerializer):
    # hospitalequipment_set = EquipmentItemSerializer(many=True, read_only=True)
    location = PointField(required=False)

    class Meta:
        model = Hospital
        fields = ['id', 'equipment_holder_id',
                  'number', 'street', 'unit', 'neighborhood',
                  'city', 'state', 'zipcode', 'country',
                  'location',
                  'name',
                  'comment', 'updated_by', 'updated_on',
                  # 'hospitalequipment_set'
                  ]
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
            # if not user.profile.hospitals.filter(can_write=True,
            #                                     hospital=instance.id):
            if not get_permissions(user).check_can_write(hospital=instance.id):
                raise PermissionDenied()

        return super().update(instance, validated_data)

