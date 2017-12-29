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


# AmbulancePermission

class AmbulancePermissionViewSet(viewsets.GenericViewSet):

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
            can_do = user.profile.ambulances.filter(can_read=True).values('ambulance_id')

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # ambulances that the user can write to
            can_do = user.profile.ambulances.filter(can_write=True).values('ambulance_id')
            
        else:
            raise PermissionDenied()

        #print('> user = {}, can_do = {}'.format(user, can_do))
        #print('> ambulances = {}'.format(Ambulance.objects.all()))
        #print('> filtered ambulances = {}'.format(Ambulance.objects.filter(id__in=can_do)))
        return self.queryset.filter(id__in=can_do)


# HospitalPermission

class HospitalPermissionViewSet(viewsets.GenericViewSet):
    
    filter_field = 'id'
    queryset = Hospital.objects.all()

    def get_queryset(self):

        #print('@get_queryset {}({})'.format(self.request.user,
        #                                    self.request.method))
        
        # return all hospitals if superuser
        user = self.request.user
        if user.is_superuser:
            return self.queryset

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        #print('> METHOD = {}'.format(self.request.method))
        # otherwise only return hospitals that the user can read or write to
        if self.request.method == 'GET':
            # hospitals that the user can read
            can_do = user.profile.hospitals.filter(can_read=True).values('hospital_id')

        elif (self.request.method == 'PUT' or
              self.request.method == 'PATCH' or
              self.request.method == 'DELETE'):
            # hospitals that the user can write to
            can_do = user.profile.hospitals.filter(can_write=True).values('hospital_id')
            
        else:
            raise PermissionDenied()

        #print('> user = {}, can_do = {}'.format(user, can_do))
        #print('> hospitals = {}'.format(Hospital.objects.all()))
        #print('> filtered hospitals = {}'.format(Hospital.objects.filter(id__in=can_do)))
        filter = {}
        filter[self.filter_field + '__in'] = can_do
        return self.queryset.filter(**filter)

    
# Ambulance viewset

class AmbulanceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       AmbulancePermissionViewSet):

    serializer_class = AmbulanceSerializer

    def perform_create(self, serializer):
        
        #print('@perform_create')
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):

        #print('@perform_update')
        serializer.save(updated_by=self.request.user)


# Hospital viewset

class HospitalViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.CreateModelMixin,
                      mixins.UpdateModelMixin,
                      HospitalPermissionViewSet):
    
    serializer_class = HospitalSerializer
    
    def perform_create(self, serializer):
        
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):

        serializer.save(updated_by=self.request.user)

# HospitalEquipment viewset

class HospitalEquipmentViewSet(mixins.RetrieveModelMixin,
                               HospitalPermissionViewSet):
    
    filter_field = 'hospital_id'
    queryset = HospitalEquipment.objects.all()
    serializer_class = HospitalEquipmentSerializer
    lookup_field = 'equipment__name'
    lookup_fields = ('hospital_id', 'equipment__name')

    # make sure both fields are looked up
    def get_object(self):
        queryset = self.get_queryset()
        filter = {}
        for field in self.lookup_fields:
            filter[field] = self.kwargs[field]

        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj
