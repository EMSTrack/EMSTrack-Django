from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, mixins, generics, filters, permissions
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from emstrack.mixins import BasePermissionMixin, \
    CreateModelUpdateByMixin, UpdateModelUpdateByMixin
from login.permissions import get_permissions

from .models import Hospital, HospitalEquipment, Equipment

from .serializers import HospitalSerializer, \
    HospitalEquipmentSerializer, EquipmentSerializer

# Django REST Framework Viewsets
    
# Hospital viewset

class HospitalViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      CreateModelUpdateByMixin,
                      UpdateModelUpdateByMixin,
                      BasePermissionMixin,
                      viewsets.GenericViewSet):
    
    """
    API endpoint for manipulating hospitals.

    list:
    Retrieve list of hospitals.

    retrieve:
    Retrieve an existing hospital instance.

    create:
    Create new hospital instance.
    
    update:
    Update existing hospital instance.

    partial_update:
    Partially update existing hospital instance.
    """
    
    filter_field = 'id'
    profile_field = 'hospitals'
    queryset = Hospital.objects.all()
    
    serializer_class = HospitalSerializer

    @detail_route()
    def metadata(self, request, pk=None, **kwargs):
        """
        Retrive hospital equipment metadata.
        """
        
        hospital = self.get_object()
        hospital_equipment = hospital.hospitalequipment_set.values('equipment')
        equipment = Equipment.objects.filter(id__in=hospital_equipment)
        serializer = EquipmentSerializer(equipment, many=True)
        return Response(serializer.data)


# HospitalEquipment viewset

class HospitalEquipmentViewSet(mixins.ListModelMixin,
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
    
    queryset = HospitalEquipment.objects.all()
    
    serializer_class = HospitalEquipmentSerializer
    lookup_field = 'equipment__name'

    # make sure both fields are looked up
    def get_queryset(self):

        # retrieve user
        user = self.request.user
        
        # retrieve id
        id = self.kwargs['id']

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        logger.debug('user = {}'.format(user))
        logger.debug('hospital_id = {}'.format(id))
        logger.debug('can_read = {}'.format(get_permissions(user).check_can_read(hospital=id)))
        logger.debug('can_write = {}'.format(get_permissions(user).check_can_write(hospital=id)))

        # check permission (and also existence)
        if self.request.method == 'GET':
            if not get_permissions(user).check_can_read(hospital=id):
                raise PermissionDenied()

        elif (self.request.method == 'PUT' or
               self.request.method == 'PATCH' or
               self.request.method == 'DELETE'):
            if not get_permissions(user).check_can_write(hospital=id):
                raise PermissionDenied()

        # build queryset
        filter = { 'hospital_id': id }
        return self.queryset.filter(**filter)
