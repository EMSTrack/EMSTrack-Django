from django.core.exceptions import PermissionDenied

from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from emstrack.mixins import UpdateModelUpdateByMixin, BasePermissionMixin
from equipment.models import EquipmentItem, EquipmentHolder, Equipment
from equipment.serializers import EquipmentItemSerializer, EquipmentSerializer
from hospital.viewsets import logger
from login.permissions import get_permissions


class EquipmentItemViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           UpdateModelUpdateByMixin,
                           viewsets.GenericViewSet):
    """
    API endpoint for manipulating hospital equipment.

    list:
    Retrieve list of hospital equipment.

    retrieve:
    Retrieve an existing hospital equipment instance.

    update:
    Update existing hospital equipment instance.

    partial_update:
    Partially update existing hospital equipment instance.
    """

    queryset = EquipmentItem.objects.all()

    serializer_class = EquipmentItemSerializer
    lookup_field = 'equipment_id'

    # make sure both fields are looked up
    def get_queryset(self):

        # retrieve user
        user = self.request.user

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()
        
        # retrieve id
        equipment_holder_id = int(self.kwargs['equipment_holder_id'])
        logger.debug('kwargs = {}'.format(self.kwargs))

        try:
            
            # retrieve equipment_holder
            equipment_holder = EquipmentHolder.objects.get(id=equipment_holder_id)

            # read or write?
            if self.request.method == 'GET':
                is_write = False
            elif (self.request.method == 'PUT' or
                  self.request.method == 'PATCH' or
                  self.request.method == 'DELETE'):
                is_write = True

            # is hospital?
            if equipment_holder.is_hospital():

                # check permission (and also existence)
                if is_write:
                    if not get_permissions(user).check_can_write(hospital=equipment_holder.hospital.id):
                        raise PermissionDenied()
                else:
                    if not get_permissions(user).check_can_read(hospital=equipment_holder.hospital.id):
                        raise PermissionDenied()

            # is ambulance?
            elif equipment_holder.is_ambulance():

                # check permission (and also existence)
                if is_write:
                    if not get_permissions(user).check_can_write(ambulance=equipment_holder.ambulance.id):
                        raise PermissionDenied()
                else:
                    if not get_permissions(user).check_can_read(ambulance=equipment_holder.ambulance.id):
                        raise PermissionDenied()

            else:
                raise PermissionDenied()

        except EquipmentHolder.DoesNotExist as e:
            raise PermissionDenied()

        # build queryset
        filter = {'equipment_holder_id': equipment_holder_id}
        return self.queryset.filter(**filter)


class EquipmentViewSet(BasePermissionMixin,
                       viewsets.GenericViewSet):
    """
    API endpoint for manipulating equipment.

    metadata
    Partially update existing hospital instance.
    """

    filter_field = 'hospital__id'
    profile_field = 'hospitals'
    queryset = EquipmentHolder.objects.all()

    @action(detail=True)
    def metadata(self, request, pk=None, **kwargs):
        """
        Retrive hospital equipment metadata.
        """

        equipment_holder = self.get_object()
        equipment_list = equipment_holder.equipmentitem_set.values('equipment')
        equipment = Equipment.objects.filter(id__in=equipment_list)
        serializer = EquipmentSerializer(equipment, many=True)
        return Response(serializer.data)
