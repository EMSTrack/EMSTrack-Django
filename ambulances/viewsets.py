from django.core.exceptions import PermissionDenied

from rest_framework import viewsets
from rest_framework import mixins
from rest_framework import generics
from rest_framework import filters

from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions

from .models import Ambulance, Hospital, Profile

from .serializers import ExtendedProfileSerializer, \
    AmbulanceSerializer, HospitalSerializer

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


# Ambulance viewset

class AmbulanceViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.CreateModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):

    #queryset = Ambulance.objects.all()
    serializer_class = AmbulanceSerializer
    
    def get_queryset(self):

        #print('@get_queryset {}({})'.format(self.request.user,
        #                                    self.request.method))
        
        # return all ambulances if superuser
        user = self.request.user
        if user.is_superuser:
            return Ambulance.objects.all()

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
        return Ambulance.objects.filter(id__in=can_do)

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
                      viewsets.GenericViewSet):
    
    #queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer
    
    def get_queryset(self):

        print('@get_queryset {}({})'.format(self.request.user,
                                            self.request.method))
        
        # return all hospitals if superuser
        user = self.request.user
        if user.is_superuser:
            return Hospital.objects.all()

        # return nothing if anonymous
        if user.is_anonymous:
            raise PermissionDenied()

        print('> METHOD = {}'.format(self.request.method))
        
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

        print('> user = {}, can_do = {}'.format(user, can_do))
        print('> hospitals = {}'.format(Hospital.objects.all()))
        print('> filtered hospitals = {}'.format(Hospital.objects.filter(id__in=can_do)))
        # print('> filtered hospitals query = {}'.format(Hospital.objects.filter(id__in=can_do).query))
        return Hospital.objects.filter(id__in=can_do)

    def perform_create(self, serializer):
        
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):

        serializer.save(updated_by=self.request.user)
