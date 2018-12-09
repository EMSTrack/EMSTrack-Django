from django.core.exceptions import PermissionDenied

from rest_framework import viewsets, mixins

from emstrack.mixins import UpdateModelUpdateByMixin
from equipment.models import EquipmentItem
from equipment.serializers import EquipmentItemSerializer
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

        # retrieve id
        equipment_holder_id = int(self.kwargs['equipment_holder_id'])

        logger.debug('kwargs = {}'.format(self.kwargs))

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        # logger.debug('user = {}'.format(user))
        # logger.debug('hospital_id = {}'.format(id))
        # logger.debug('can_read = {}'.format(get_permissions(user).check_can_read(hospital=id)))
        # logger.debug('can_write = {}'.format(get_permissions(user).check_can_write(hospital=id)))

        # check permission (and also existence)
        if self.request.method == 'GET':
            if not get_permissions(user).check_can_read(hospital=equipment_holder_id):
                raise PermissionDenied()

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            if not get_permissions(user).check_can_write(hospital=equipment_holder_id):
                raise PermissionDenied()

        # build queryset
        filter = {'equipment_holder_id': equipment_holder_id}
        return self.queryset.filter(**filter)