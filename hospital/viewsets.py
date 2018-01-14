from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, mixins, generics, filters, permissions
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from util.mixins import CreateModelUpdateByMixin, UpdateModelUpdateByMixin, \
    BasePermissionMixin

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
    
    filter_field = 'id'
    profile_field = 'hospitals'
    profile_values = 'hospital_id'
    queryset = Hospital.objects.all()
    
    serializer_class = HospitalSerializer

    @detail_route()
    def metadata(self, request, pk=None, **kwargs):

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
        
        # retrieve hospital or 404 if it does not exist
        hospital = get_object_or_404(Hospital.objects.all(), id=id)
        
        # build queryset
        filter = { 'hospital_id': id }
        qset = self.queryset.filter(**filter)

        # return qset if superuser
        if user.is_superuser:
            return qset

        # otherwise check permission
        if self.request.method == 'GET':
            # objects that the user can read
            get_object_or_404(user.profile.hospitals,
                              hospital_id=id, can_read=True)

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # objects that the user can write to
            get_object_or_404(user.profile.hospitals,
                              hospital_id=id, can_write=True)

        # and return qset
        return qset
