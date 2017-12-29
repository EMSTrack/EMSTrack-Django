from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import generics
from rest_framework import filters

from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions

from .models import Ambulance, Hospital, Profile, HospitalEquipment

from .serializers import ExtendedProfileSerializer, \
    AmbulanceSerializer, HospitalSerializer, HospitalEquipmentSerializer

# Django REST Framework Viewsets

class IsUserOrAdminOrSuper(permissions.BasePermission):
    """
    Only user or staff can see or modify
    """

    def has_object_permission(self, request, view, obj):
        return (request.user.is_superuser or
                request.user.is_staff or
                obj.user == request.user)


# Profile viewset

class ProfileViewSet(mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):

    queryset = Profile.objects.all()
    serializer_class = ExtendedProfileSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsUserOrAdminOrSuper,)
    lookup_field = 'user__username'

# BasePermissionViewSet

class BasePermissionViewSet(viewsets.GenericViewSet):

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = Ambulance.objects.all()
    
    def get_queryset(self):

        #print('@get_queryset {}({})'.format(self.request.user,
        #                                    self.request.method))
        
        # return all ambulances if superuser
        user = self.request.user
        if user.is_superuser:
            return self.queryset

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        # print('> METHOD = {}'.format(self.request.method))
        # otherwise only return ambulances that the user can read or write to
        if self.request.method == 'GET':
            # ambulances that the user can read
            can_do = getattr(user.profile,
                             self.profile_field).filter(can_read=True).values(self.profile_values)

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # ambulances that the user can write to
            can_do = getattr(user.profile,
                             self.profile_field).filter(can_write=True).values('ambulance_id')
            
        else:
            raise PermissionDenied()

        #print('> user = {}, can_do = {}'.format(user, can_do))
        #print('> ambulances = {}'.format(Ambulance.objects.all()))
        #print('> filtered ambulances = {}'.format(Ambulance.objects.filter(id__in=can_do)))
        filter = {}
        filter[self.filter_field + '__in'] = can_do
        return self.queryset.filter(**filter)
    
# AmbulancePermission

class AmbulancePermissionViewSet(BasePermissionViewSet):

    filter_field = 'id'
    profile_field = 'ambulances'
    profile_values = 'ambulance_id'
    queryset = Ambulance.objects.all()
    
# HospitalPermission

class HospitalPermissionViewSet(BasePermissionViewSet):
    
    filter_field = 'id'
    profile_field = 'hospitals'
    profile_values = 'hospital_id'
    queryset = Hospital.objects.all()

# CreateModelUpdateByMixin

class CreateModelUpdateByMixin(mixins.CreateModelMixin):

    def perform_create(self, serializer):
        
        serializer.save(updated_by=self.request.user)
    
# UpdateModelUpdateByMixin

class UpdateModelUpdateByMixin(mixins.UpdateModelMixin):

    def perform_update(self, serializer):
        
        serializer.save(updated_by=self.request.user)

# Ambulance viewset

class AmbulanceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       CreateModelUpdateByMixin,
                       UpdateModelUpdateByMixin,
                       AmbulancePermissionViewSet):

    serializer_class = AmbulanceSerializer

# Hospital viewset

class HospitalViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      CreateModelUpdateByMixin,
                      UpdateModelUpdateByMixin,
                      HospitalPermissionViewSet):
    
    serializer_class = HospitalSerializer
    
# HospitalEquipment viewset

class HospitalEquipmentViewSet(mixins.ListModelMixin,
                               mixins.RetrieveModelMixin,
                               HospitalPermissionViewSet):
    
    filter_field = 'hospital_id'
    queryset = HospitalEquipment.objects.all()
    
    serializer_class = HospitalEquipmentSerializer
    lookup_field = 'equipment__name'
    lookup_fields = ('hospital_id', 'equipment__name')

    # make sure both fields are looked up
    def get_object(self):

        print('> get_object {}'.format(self.kwargs))
        qset = self.get_queryset()
        #filter = {}
        #for field in self.lookup_fields:
        #    filter[field] = self.kwargs[field]
        #obj = get_object_or_404(qset, **filter)
        obj = get_object_or_404(qset)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):

        print('> get_queryset {}'.format(self.kwargs))
        qset = super().get_queryset()
        filter = {}
        for field in self.lookup_fields:
            filter[field] = self.kwargs[field]

        return qset.filter(**filter)
            
